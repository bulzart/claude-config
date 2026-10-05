"""Shared helpers for the post-generation edit module (tools\\edit).

- Tool paths: PATH inside a fresh shell may be stale, so every binary falls back to the absolute
  paths listed in LAYOUT.md. If tools\\common.py (written by agent B1) exists and exposes FFMPEG /
  FFPROBE (strings) or find_ffmpeg()/find_ffprobe() (callables) those win; otherwise the fallback
  logic below is used. Nothing here needs common.py to exist.
- Edit-plan loading + validation (schema analyze-stack.edit-plan/2, see EDIT-PLAN.md).
- Timeline arithmetic shared by the renderer and the project builders (speed pieces, transition
  overlaps, output durations) so every builder agrees on the same placement to the frame.
- Overlay layout (safe-zone anchored geometry) shared by text_overlays.py and the builders.

OWNER RULE: speech captions / subtitles are never produced by this module. load_plan() refuses a
plan that carries a captions/subtitles block or transcript-shaped overlays.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import uuid as _uuid

STACK_HOME = r"C:\Users\Glaresquare1\.claude\analyze-stack"
TOOLS_DIR = os.path.join(STACK_HOME, "tools")
EDIT_DIR = os.path.join(TOOLS_DIR, "edit")
FONTS_DIR = os.path.join(EDIT_DIR, "fonts")
CAPCUT_DRAFTS_DIR = r"C:\Users\Glaresquare1\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft"
CAPCUT_TEMPLATE_DIR = os.path.join(STACK_HOME, "research", "capcut-draft-sample")
CAPCUT_EXE = r"C:\Users\Glaresquare1\AppData\Local\CapCut\Apps\9.4.0.4015\CapCut.exe"

_FF_DIR = (r"C:\Users\Glaresquare1\AppData\Local\Microsoft\WinGet\Packages"
           r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin")
FFMPEG_FALLBACK = os.path.join(_FF_DIR, "ffmpeg.exe")
FFPROBE_FALLBACK = os.path.join(_FF_DIR, "ffprobe.exe")
PYTHON_FALLBACK = r"C:\Users\Glaresquare1\AppData\Local\Programs\Python\Python312\python.exe"
NPM_BIN_DIR = os.path.join(os.environ.get("APPDATA", r"C:\Users\Glaresquare1\AppData\Roaming"), "npm")

PLAN_SCHEMA = "analyze-stack.edit-plan/2"

# Safe boxes at 1080x1920 (references\post-generation-playbook.md section 4.3).
UNIVERSAL_SAFE_BOX = {"x_min": 65, "x_max": 915, "y_min": 270, "y_max": 1248}
PLATFORM_SAFE_BOXES = {
    "universal": UNIVERSAL_SAFE_BOX,
    "all": UNIVERSAL_SAFE_BOX,
    "tiktok": {"x_min": 65, "x_max": 916, "y_min": 270, "y_max": 1596},
    "tiktok-ads": {"x_min": 65, "x_max": 916, "y_min": 270, "y_max": 1550},
    "reels": UNIVERSAL_SAFE_BOX,
    "shorts": {"x_min": 65, "x_max": 915, "y_min": 270, "y_max": 1536},
}

# Words that mark a transcript-shaped object (never allowed: no caption generator can grow here).
_FORBIDDEN_PLAN_KEYS = {"captions", "subtitles", "transcript", "caption_track", "subtitle_track"}
_FORBIDDEN_OVERLAY_KEYS = {"words", "word_timestamps", "transcript", "srt", "segments", "speaker"}
_FORBIDDEN_OVERLAY_TYPES = {"caption", "captions", "subtitle", "subtitles", "speech", "karaoke", "lyrics"}
ALLOWED_OVERLAY_TYPES = ("hook_text", "callout", "end_card", "sticker")


# ----------------------------------------------------------------------------- tool paths
def _try_common_module():
    """Return tools\\common.py as a module if it exists and imports, else None."""
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    try:
        import importlib
        return importlib.import_module("common")
    except Exception:
        return None


_COMMON = _try_common_module()


def _from_common(attr: str, funcs: tuple[str, ...]):
    """tools\\common.py (agent B1) exposes ffmpeg()/ffprobe() callables and FFMPEG_FALLBACK constants;
    older drafts of it may expose FFMPEG strings or find_ffmpeg(). Try all shapes."""
    if _COMMON is None:
        return None
    v = getattr(_COMMON, attr, None)
    if isinstance(v, str) and os.path.isfile(v):
        return v
    for func in funcs:
        f = getattr(_COMMON, func, None)
        if callable(f):
            try:
                r = f()
                if isinstance(r, (str, os.PathLike)) and os.path.isfile(str(r)):
                    return str(r)
            except Exception:
                pass
    return None


def _refresh_path_from_registry() -> None:
    """PATH in a fresh shell can be stale: merge Machine + User PATH from the registry (Windows only)."""
    if os.name != "nt":
        return
    try:
        import winreg
        parts = []
        for hive, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, "Environment")):
            try:
                with winreg.OpenKey(hive, key) as k:
                    val, _ = winreg.QueryValueEx(k, "Path")
                    parts.append(os.path.expandvars(val))
            except OSError:
                pass
        if parts:
            os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + os.pathsep.join(parts)
    except Exception:
        pass


def resolve_tool(name: str, fallback: str, common_attr: str = "", common_funcs: tuple[str, ...] = ()) -> str:
    """tools\\common.py first, then PATH (refreshed from the registry), then the LAYOUT.md fallback, then bare name."""
    c = _from_common(common_attr, common_funcs) if common_attr else None
    if c:
        return c
    w = shutil.which(name)
    if not w:
        _refresh_path_from_registry()
        w = shutil.which(name)
    if w:
        return w
    if os.path.isfile(fallback):
        return fallback
    return name


FFMPEG = resolve_tool("ffmpeg", FFMPEG_FALLBACK, "FFMPEG", ("ffmpeg", "find_ffmpeg"))
FFPROBE = resolve_tool("ffprobe", FFPROBE_FALLBACK, "FFPROBE", ("ffprobe", "find_ffprobe"))
PYTHON = sys.executable or resolve_tool("python", PYTHON_FALLBACK)


def gain_db(obj: dict | None, default: float) -> float:
    """Gain in dB from an audio object: 'gain_db' preferred, 'gain' accepted as an alias (also dB)."""
    if not isinstance(obj, dict):
        return float(default)
    for k in ("gain_db", "gain"):
        if obj.get(k) is not None:
            return float(obj[k])
    return float(default)


def find_capcut_cli() -> list[str] | None:
    """capcut-cli 0.23 (npm global). Returns an argv prefix (node + dist/index.js) or None.
    The npm shim is capcut.ps1/capcut.cmd; calling node directly avoids shell quoting on Windows."""
    for base in (NPM_BIN_DIR, os.path.join(os.environ.get("APPDATA", ""), "npm")):
        js = os.path.join(base, "node_modules", "capcut-cli", "dist", "index.js")
        if os.path.isfile(js):
            node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
            if not os.path.isfile(node):
                _refresh_path_from_registry()
                node = shutil.which("node") or node
            if os.path.isfile(node):
                return [node, js]
    w = shutil.which("capcut.cmd") or shutil.which("capcut")
    if w and w.lower().endswith(".cmd"):
        return [w]
    return None


# ----------------------------------------------------------------------------- misc helpers
def now_iso() -> str:
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def stamp() -> str:
    """File-name-safe timestamp (no colons): 20260916-131500."""
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_json(path: str):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path: str, obj, indent: int | None = 2, compact: bool = False) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if compact:
            f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        else:
            f.write(json.dumps(obj, ensure_ascii=False, indent=indent))
            f.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def append_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run(cmd: list[str], log_path: str | None = None, check: bool = False, cwd: str | None = None,
        timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a command as an argument list (never through a shell). stdout/stderr captured as text."""
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                        cwd=cwd, timeout=timeout)
    if log_path:
        append_text(log_path, "$ " + " ".join(ps_quote(a) for a in cmd) + "\n")
        if cp.stdout:
            append_text(log_path, cp.stdout + ("\n" if not cp.stdout.endswith("\n") else ""))
        if cp.stderr:
            append_text(log_path, cp.stderr + ("\n" if not cp.stderr.endswith("\n") else ""))
        append_text(log_path, f"[exit {cp.returncode}]\n")
    if check and cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stderr[-4000:]}")
    return cp


def ps_quote(a: str) -> str:
    """Quote an argument for a copy-pasteable PowerShell line (documentation only)."""
    if re.fullmatch(r"[A-Za-z0-9_\-./\\:=+,@\[\]]+", a or ""):
        return a
    return "'" + a.replace("'", "''") + "'"


def db_to_lin(db: float) -> float:
    return float(10 ** (float(db) / 20.0))


def utf16_len(s: str) -> int:
    """Length in UTF-16 code units (CapCut text ranges use these)."""
    return len(s.encode("utf-16-le")) // 2


def capcut_uuid() -> str:
    """CapCut writes upper-case uuids with a lower-case third group; any uuid is accepted."""
    g = str(_uuid.uuid4()).upper().split("-")
    g[2] = g[2].lower()
    return "-".join(g)


def plain_uuid() -> str:
    return str(_uuid.uuid4())


def ffpath(p: str) -> str:
    """Path for use INSIDE a filter graph option (ass=filename=..., fontsdir=...).
    Forward slashes; the drive colon escaped as '\\:'; single quotes escaped."""
    p = os.path.abspath(p).replace("\\", "/")
    p = p.replace(":", "\\:")
    p = p.replace("'", "\\'")
    return p


def to_file_uri(p: str) -> str:
    import pathlib
    return pathlib.Path(os.path.abspath(p)).as_uri()


def from_file_uri(u: str) -> str:
    from urllib.parse import unquote, urlparse
    if not u:
        return ""
    if u.lower().startswith("file:"):
        pr = urlparse(u)
        path = unquote(pr.path)
        if pr.netloc and pr.netloc not in ("", "localhost"):
            path = "//" + pr.netloc + path
        if re.match(r"^/[A-Za-z]:", path):
            path = path[1:]
        return os.path.normpath(path)
    return u


def capcut_running() -> bool:
    """True when CapCut.exe is running (never write into the live draft store then)."""
    try:
        cp = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        return "CapCut.exe" in (cp.stdout or "")
    except Exception:
        return False


# ----------------------------------------------------------------------------- probing
def ffprobe_json(path: str) -> dict:
    cp = run([FFPROBE, "-v", "error", "-show_entries",
              "format=filename,duration,size,bit_rate:stream=index,codec_type,codec_name,profile,width,height,"
              "r_frame_rate,avg_frame_rate,pix_fmt,sample_rate,channels,duration,nb_frames",
              "-of", "json", path])
    if cp.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {cp.stderr.strip()[-500:]}")
    return json.loads(cp.stdout or "{}")


def _fps_from(s: str) -> float:
    try:
        n, d = s.split("/")
        d = float(d)
        return float(n) / d if d else 0.0
    except Exception:
        return 0.0


def probe_media(path: str) -> dict:
    """Compact media summary: duration, width, height, fps, has_video, has_audio, sample_rate, channels."""
    j = ffprobe_json(path)
    fmt = j.get("format", {})
    out = {"path": os.path.abspath(path), "duration": float(fmt.get("duration") or 0.0),
           "size": int(fmt.get("size") or 0), "has_video": False, "has_audio": False,
           "width": 0, "height": 0, "fps": 0.0, "sample_rate": 0, "channels": 0, "vcodec": "", "acodec": ""}
    for s in j.get("streams", []):
        if s.get("codec_type") == "video" and not out["has_video"]:
            out["has_video"] = True
            out["width"] = int(s.get("width") or 0)
            out["height"] = int(s.get("height") or 0)
            out["fps"] = _fps_from(s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1") or \
                _fps_from(s.get("r_frame_rate") or "0/1")
            out["vcodec"] = s.get("codec_name", "")
            if not out["duration"] and s.get("duration"):
                out["duration"] = float(s["duration"])
        elif s.get("codec_type") == "audio" and not out["has_audio"]:
            out["has_audio"] = True
            out["sample_rate"] = int(s.get("sample_rate") or 0)
            out["channels"] = int(s.get("channels") or 0)
            out["acodec"] = s.get("codec_name", "")
            if not out["duration"] and s.get("duration"):
                out["duration"] = float(s["duration"])
    return out


# ----------------------------------------------------------------------------- plan loading
class PlanError(ValueError):
    pass


def plan_base_dir(plan: dict, plan_path: str) -> str:
    rd = (plan.get("project") or {}).get("run_dir")
    if rd and os.path.isdir(rd):
        return os.path.abspath(rd)
    return os.path.dirname(os.path.abspath(plan_path))


def resolve_path(p: str | None, base: str) -> str | None:
    if not p:
        return None
    p = os.path.expandvars(str(p))
    if os.path.isabs(p):
        return os.path.normpath(p)
    # relative paths resolve against the run dir first, then the plan dir's parent chain
    cand = os.path.normpath(os.path.join(base, p))
    return cand


def safe_box_for(plan: dict) -> dict:
    proj = plan.get("project") or {}
    sz = proj.get("safe_zones")
    if isinstance(sz, dict) and all(k in sz for k in ("x_min", "x_max", "y_min", "y_max")):
        return {k: int(sz[k]) for k in ("x_min", "x_max", "y_min", "y_max")}
    return dict(PLATFORM_SAFE_BOXES.get(str(proj.get("platform", "universal")).lower(), UNIVERSAL_SAFE_BOX))


def refuse_captions(plan: dict) -> None:
    """Raise PlanError when the plan smells like a caption/subtitle job (owner rule)."""
    low = {str(k).lower() for k in plan.keys()}
    bad = sorted(low & _FORBIDDEN_PLAN_KEYS)
    if bad:
        raise PlanError(f"plan carries {bad}: speech captions/subtitles are never added in the edit "
                        f"(owner rule). Remove the block; the owner captions afterwards with a separate tool.")
    txt = plan.get("text") or {}
    if isinstance(txt, dict) and ({str(k).lower() for k in txt} & _FORBIDDEN_PLAN_KEYS):
        raise PlanError("plan.text carries a captions/subtitles entry: refused (owner rule).")
    for ov in plan.get("text_overlays") or []:
        if not isinstance(ov, dict):
            raise PlanError("text_overlays entries must be objects")
        t = str(ov.get("type", "")).lower()
        if t in _FORBIDDEN_OVERLAY_TYPES:
            raise PlanError(f"overlay type '{t}' is a caption type: refused (owner rule).")
        if t not in ALLOWED_OVERLAY_TYPES:
            raise PlanError(f"overlay type '{t}' unknown; allowed: {ALLOWED_OVERLAY_TYPES}")
        keys = {str(k).lower() for k in ov.keys()}
        if keys & _FORBIDDEN_OVERLAY_KEYS:
            raise PlanError(f"overlay {ov.get('id')} carries transcript-shaped keys {sorted(keys & _FORBIDDEN_OVERLAY_KEYS)}: refused.")
        src = str(ov.get("source", "")).lower()
        if any(w in src for w in ("transcript", "whisper", "srt", "subtitle", "caption", "speech")):
            raise PlanError(f"overlay {ov.get('id')} cites a transcript source: refused (owner rule).")


def load_plan(plan_path: str) -> tuple[dict, str]:
    """Load + validate an edit plan. Returns (plan, base_dir)."""
    plan = load_json(plan_path)
    if not isinstance(plan, dict):
        raise PlanError("edit plan must be a JSON object")
    if plan.get("schema") not in (PLAN_SCHEMA,):
        raise PlanError(f"schema must be '{PLAN_SCHEMA}' (got {plan.get('schema')!r}); see EDIT-PLAN.md")
    refuse_captions(plan)
    proj = plan.get("project") or {}
    for k in ("fps", "width", "height"):
        if k not in proj:
            raise PlanError(f"project.{k} missing")
    if not plan.get("clips"):
        raise PlanError("clips[] is empty")
    ids = [c.get("id") for c in plan["clips"]]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise PlanError("every clip needs a unique id")
    base = plan_base_dir(plan, plan_path)
    for c in plan["clips"]:
        if "path" not in c:
            raise PlanError(f"clip {c['id']} has no path")
        for k in ("in", "out"):
            if k not in c:
                raise PlanError(f"clip {c['id']} needs '{k}' (seconds)")
        if float(c["out"]) <= float(c["in"]):
            raise PlanError(f"clip {c['id']}: out must be > in")
    for t in plan.get("transitions") or []:
        b = t.get("between")
        if not (isinstance(b, list) and len(b) == 2 and all(x in ids for x in b)):
            raise PlanError(f"transition {t} must name two existing clip ids in 'between'")
        if t.get("type", "cut") not in ("cut", "xfade", "whip", "zoom"):
            raise PlanError(f"transition type {t.get('type')} unknown (cut|xfade|whip|zoom)")
    return plan, base


# ----------------------------------------------------------------------------- timeline maths
def speed_pieces(clip: dict) -> list[tuple[float, float, float]]:
    """Split [in,out] of a clip into (src_a, src_b, speed) pieces from speed_ramps (source seconds)."""
    a0, b0 = float(clip["in"]), float(clip["out"])
    base_speed = float(clip.get("speed", 1.0) or 1.0)
    ramps = sorted([r for r in (clip.get("speed_ramps") or []) if r], key=lambda r: float(r["from"]))
    pieces: list[tuple[float, float, float]] = []
    cur = a0
    for r in ramps:
        ra, rb, rs = float(r["from"]), float(r["to"]), float(r.get("speed", 1.0) or 1.0)
        ra, rb = max(ra, a0), min(rb, b0)
        if rb <= ra:
            continue
        if ra < cur - 1e-6:
            raise PlanError(f"clip {clip['id']}: overlapping speed_ramps")
        if ra > cur + 1e-6:
            pieces.append((cur, ra, base_speed))
        pieces.append((ra, rb, rs))
        cur = rb
    if cur < b0 - 1e-6:
        pieces.append((cur, b0, base_speed))
    return [(a, b, s) for a, b, s in pieces if b - a > 1e-6 and s > 0]


def transition_lookup(plan: dict) -> dict:
    return {tuple(t["between"]): t for t in (plan.get("transitions") or [])}


def compute_timeline(plan: dict, probes: dict | None = None) -> tuple[list[dict], float]:
    """Place every clip on the output timeline.
    Returns (placed, total_seconds). Each placed item: clip, pieces, start, duration, end,
    transition_in (dict or None; overlap already applied so start = previous end - duration).
    probes (path -> probe_media dict) clamps 'out' to the real media duration when given."""
    clips = sorted(plan["clips"], key=lambda c: (float(c.get("order", 0)), c["id"]))
    trans = transition_lookup(plan)
    placed = []
    t = 0.0
    prev = None
    for c in clips:
        c = dict(c)
        if probes:
            pr = probes.get(c["path"]) or probes.get(os.path.abspath(c["path"]))
            if pr and pr.get("duration") and float(c["out"]) > pr["duration"] + 1e-3:
                c["_clamped_out_from"] = float(c["out"])
                c["out"] = round(float(pr["duration"]), 3)
        pieces = speed_pieces(c)
        dur = sum((b - a) / s for a, b, s in pieces)
        tr = None
        if prev is not None:
            tr = trans.get((prev["id"], c["id"]))
            if tr and tr.get("type", "cut") != "cut":
                d = float(tr.get("duration", 0.3) or 0.3)
                d = min(d, dur * 0.8, placed[-1]["duration"] * 0.8)
                tr = dict(tr, duration=round(d, 4))
                t -= d
        placed.append({"clip": c, "pieces": pieces, "start": round(t, 6), "duration": round(dur, 6),
                       "end": round(t + dur, 6), "transition_in": tr})
        t += dur
        prev = c
    return placed, round(t, 6)


XFADE_MAP = {  # plan transition type -> ffmpeg xfade transition name + default duration
    "xfade": ("fade", 0.4),
    "whip": ("slideleft", 0.2),
    "zoom": ("zoomin", 0.25),
}


# ----------------------------------------------------------------------------- overlay layout
STYLE_PRESETS = {
    # sizes in px at 1080x1920; char_w = average glyph width as a fraction of font size (upper/lower mix)
    "hook-v1": {"font": "Montserrat ExtraBold", "size": 88, "fill": "#FFFFFF", "outline": 6, "shadow": 2,
                "outline_colour": "#000000", "bold": True, "anchor": "top", "char_w": 0.66, "fade": (80, 80),
                "line_h": 1.18},
    "callout-v1": {"font": "Anton", "size": 72, "fill": "#FFE600", "outline": 5, "shadow": 2,
                   "outline_colour": "#000000", "bold": False, "anchor": "bottom", "char_w": 0.46,
                   "fade": (60, 60), "line_h": 1.15},
    "endcard-v1": {"font": "Bebas Neue", "size": 120, "fill": "#FFFFFF", "outline": 6, "shadow": 3,
                   "outline_colour": "#000000", "bold": False, "anchor": "middle", "char_w": 0.44,
                   "fade": (120, 200), "line_h": 1.1, "sub_font": "Montserrat Bold", "sub_size": 60},
    "sticker-text-v1": {"font": "Montserrat Black", "size": 96, "fill": "#FFFFFF", "outline": 4, "shadow": 0,
                        "outline_colour": "#000000", "bold": True, "anchor": "middle", "char_w": 0.7,
                        "fade": (0, 0), "line_h": 1.1},
}
DEFAULT_STYLE_FOR_TYPE = {"hook_text": "hook-v1", "callout": "callout-v1", "end_card": "endcard-v1",
                          "sticker": "sticker-text-v1"}
FONT_FILES = {  # family name -> file in FONTS_DIR
    "Montserrat ExtraBold": "Montserrat-ExtraBold.ttf",
    "Montserrat Black": "Montserrat-Black.ttf",
    "Montserrat Bold": "Montserrat-Bold.ttf",
    "Anton": "Anton-Regular.ttf",
    "Bebas Neue": "BebasNeue-Regular.ttf",
}
SYSTEM_FALLBACK_FONTS = ["Arial Black", "Impact", "Bahnschrift"]
SYSTEM_FONT_FILES = {"Arial Black": r"C:\Windows\Fonts\ariblk.ttf", "Impact": r"C:\Windows\Fonts\impact.ttf",
                     "Bahnschrift": r"C:\Windows\Fonts\bahnschrift.ttf"}
FONT_CHAR_W = {"Arial Black": 0.72, "Impact": 0.5, "Bahnschrift": 0.55}


def resolve_font(family: str, fonts_dir: str = FONTS_DIR) -> tuple[str, str | None]:
    """Return (family_to_use, ttf_path_or_None). Falls back to Arial Black / Impact when the TTF is missing.
    For system fallbacks the path is the Windows font file when present (used for measuring only; libass
    finds installed fonts itself)."""
    f = FONT_FILES.get(family)
    if f and os.path.isfile(os.path.join(fonts_dir, f)):
        return family, os.path.join(fonts_dir, f)
    if family in SYSTEM_FALLBACK_FONTS:
        p = SYSTEM_FONT_FILES.get(family)
        return family, (p if p and os.path.isfile(p) else None)
    for fam in SYSTEM_FALLBACK_FONTS:
        p = SYSTEM_FONT_FILES.get(fam)
        if p and os.path.isfile(p):
            return fam, p
    return SYSTEM_FALLBACK_FONTS[0], None


class _Measurer:
    """Real glyph-run widths with Pillow when the TTF is on disk; per-character heuristic otherwise."""

    def __init__(self, font_path: str | None, size: int, char_w: float):
        self.size = size
        self.char_w = char_w
        self.font = None
        if font_path and os.path.isfile(font_path):
            try:
                from PIL import ImageFont
                self.font = ImageFont.truetype(font_path, size)
            except Exception:
                self.font = None

    def width(self, s: str) -> float:
        if self.font is not None:
            try:
                return float(self.font.getlength(s))
            except Exception:
                pass
        return len(s) * self.size * self.char_w


def wrap_words(text: str, max_chars: int) -> list[str]:
    """Greedy wrap by character count (heuristic path)."""
    lines: list[str] = []
    for para in str(text).replace("\r", "").split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= max_chars:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def wrap_measured(text: str, max_width: float, m: "_Measurer") -> list[str]:
    """Greedy wrap by measured pixel width (explicit newlines are kept)."""
    lines: list[str] = []
    for para in str(text).replace("\r", "").split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if m.width(cur + " " + w) <= max_width:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def layout_overlays(plan: dict, fonts_dir: str = FONTS_DIR, total_duration: float | None = None) -> list[dict]:
    """Resolve every text overlay to concrete geometry inside the safe box.
    Output items: id, type, text, lines, t_start, t_end, style (preset name), preset (dict), font, font_path,
    size, x, y (centre of the block, px), width_est, height_est, in_safe_box (bool), warnings[]."""
    box = safe_box_for(plan)
    W = int(plan["project"]["width"])
    out = []
    for i, ov in enumerate(plan.get("text_overlays") or []):
        typ = ov.get("type")
        if typ == "sticker" and ov.get("image") and not ov.get("text"):
            continue  # PNG stickers are the renderer's job (overlay filter); nothing to typeset
        text = str(ov.get("text", "")).strip()
        if not text:
            continue
        style_name = ov.get("style") or DEFAULT_STYLE_FOR_TYPE.get(typ, "hook-v1")
        preset = dict(STYLE_PRESETS.get(style_name, STYLE_PRESETS["hook-v1"]))
        preset.update({k: v for k, v in (ov.get("style_overrides") or {}).items()})
        family_req = ov.get("font") or preset["font"]
        family, ttf = resolve_font(family_req, fonts_dir)
        size = int(ov.get("size_px") or preset["size"])
        char_w = FONT_CHAR_W.get(family, preset.get("char_w", 0.6)) if family != family_req else preset.get("char_w", 0.6)
        box_w = box["x_max"] - box["x_min"]
        outline = float(preset.get("outline", 0))
        measurer = _Measurer(ttf, size, char_w)
        if measurer.font is not None:
            lines = wrap_measured(text, box_w - 2 * outline, measurer)
            measured = True
        else:
            lines = wrap_words(text, max(6, int(box_w / (size * char_w))))
            measured = False
        n = len(lines)
        line_h = size * preset.get("line_h", 1.15)
        height = n * line_h + 2 * outline
        # end cards: lines after the first use the sub-font/size (see text_overlays.event_text)
        if typ == "end_card" and preset.get("sub_font") and n > 1:
            sub_fam, sub_ttf = resolve_font(preset["sub_font"], fonts_dir)
            sub_size = int(preset.get("sub_size", 60))
            sub_m = _Measurer(sub_ttf, sub_size, FONT_CHAR_W.get(sub_fam, 0.6))
            widths = [measurer.width(lines[0])] + [sub_m.width(l) for l in lines[1:]]
            height = line_h + (n - 1) * sub_size * preset.get("line_h", 1.15) + 2 * outline
        else:
            widths = [measurer.width(l) for l in lines]
        width = max(widths) + 2 * outline
        pos = ov.get("position") or {}
        anchor = (pos.get("anchor") or preset["anchor"]).lower()
        if pos.get("y_px") is not None:
            y = float(pos["y_px"])
        elif anchor == "top":
            y = box["y_min"] + 130 + height / 2 - line_h / 2   # hook band y ~ 300-450
        elif anchor == "bottom":
            y = box["y_max"] - 120 - height / 2 + line_h / 2
        else:
            y = (box["y_min"] + box["y_max"]) / 2
        warnings = []
        # clamp so the block stays inside the safe box
        if y - height / 2 < box["y_min"]:
            y = box["y_min"] + height / 2
            warnings.append("shifted down into the safe box")
        if y + height / 2 > box["y_max"]:
            y = box["y_max"] - height / 2
            warnings.append("shifted up into the safe box")
        if pos.get("x_px") is not None:
            x = float(pos["x_px"])
        else:
            half = width / 2
            x = W / 2 if (W / 2 - half >= box["x_min"] and W / 2 + half <= box["x_max"]) else (box["x_min"] + box["x_max"]) / 2
        if width > box_w:
            warnings.append(f"estimated width {width:.0f}px exceeds safe width {box_w}px; shorten the text or reduce size_px")
        t0 = float(ov.get("t_start", 0.0))
        t1 = float(ov.get("t_end", t0 + 2.0))
        if total_duration is not None:
            if t1 > total_duration + 1e-3:
                warnings.append(f"t_end {t1} beyond timeline end {total_duration:.2f}; clamped")
                t1 = total_duration
            if t0 >= t1:
                warnings.append("overlay starts after the timeline end; skipped")
                continue
        out.append({
            "id": ov.get("id") or f"ov{i + 1:02d}", "type": typ, "text": text, "lines": lines,
            "t_start": round(t0, 3), "t_end": round(t1, 3), "style": style_name, "preset": preset,
            "font": family, "font_requested": family_req, "font_path": ttf, "size": size,
            "x": round(x, 1), "y": round(y, 1), "width_est": round(width, 1), "height_est": round(height, 1),
            "measured_with_font": measured,
            "highlight_words": [str(w) for w in (ov.get("highlight_words") or [])],
            "highlight_colour": ov.get("highlight_colour") or "#FFE600",
            "in_safe_box": (x - width / 2 >= box["x_min"] - 1 and x + width / 2 <= box["x_max"] + 1
                            and y - height / 2 >= box["y_min"] - 1 and y + height / 2 <= box["y_max"] + 1),
            "safe_box": box, "warnings": warnings,
        })
    return out


def caption_density_guard(overlays: list[dict], max_overlays: int = 12) -> str | None:
    """Heuristic guard: a stream of short, back-to-back overlays is a caption track in disguise."""
    if len(overlays) > max_overlays:
        return f"{len(overlays)} text overlays > {max_overlays}: that is caption density, refused (owner rule)."
    evs = sorted(overlays, key=lambda o: o["t_start"])
    run_len = 0
    for a, b in zip(evs, evs[1:]):
        short = (a["t_end"] - a["t_start"]) <= 2.5 and (b["t_end"] - b["t_start"]) <= 2.5
        tight = abs(b["t_start"] - a["t_end"]) <= 0.3
        run_len = run_len + 1 if (short and tight) else 0
        if run_len >= 5:
            return "six or more back-to-back short overlays look like word/phrase captions: refused (owner rule)."
    return None


def default_overlays_path(plan_path: str) -> str:
    """edit-plan.json -> overlays.ass (LAYOUT.md name); any other plan file -> <stem>.overlays.ass so variants
    and auto-generated plans never overwrite each other's ASS."""
    d = os.path.dirname(os.path.abspath(plan_path))
    stem = os.path.splitext(os.path.basename(plan_path))[0]
    return os.path.join(d, "overlays.ass" if stem == "edit-plan" else f"{stem}.overlays.ass")


def history_line(dir_path: str, what: str) -> None:
    append_text(os.path.join(dir_path, "history.md"), f"- {now_iso()} — {what}\n")
