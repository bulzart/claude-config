"""common.py - shared helpers for every analyze-stack tool script (Python 3.12, Windows).

Import with:  sys.path.insert(0, str(Path(__file__).resolve().parent)); import common

Provides: tool resolution (ffmpeg / ffprobe / python: PATH first, then the absolute
fallbacks from LAYOUT.md), run_cmd with timeout + logging, JSON helpers, run-folder
skeleton, state.json helpers, timestamp formatting without colons, contact-sheet builder
(PIL text, font-safe on Windows) and a small Log class that prints progress lines unless
--quiet and always appends to the log file.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------------------
# console / environment
# --------------------------------------------------------------------------------------
sys.dont_write_bytecode = True  # never write __pycache__ next to the tools (only the run dir + model caches are written)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - very old consoles
        pass
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

STACK_HOME = Path(r"C:\Users\Glaresquare1\.claude\analyze-stack")
DEFAULT_RUN_ROOT = STACK_HOME / "runs"
TOOLS_DIR = STACK_HOME / "tools"

_FF_DIR = Path(r"C:\Users\Glaresquare1\AppData\Local\Microsoft\WinGet\Packages"
               r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin")
FFMPEG_FALLBACK = _FF_DIR / "ffmpeg.exe"
FFPROBE_FALLBACK = _FF_DIR / "ffprobe.exe"
PYTHON_FALLBACK = Path(r"C:\Users\Glaresquare1\AppData\Local\Programs\Python\Python312\python.exe")
WHISPER_CPP_DIR = Path(r"C:\Users\Glaresquare1\.cache\whisper-cpp")
FONT_CANDIDATES = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf",
                   r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\consola.ttf"]

# Run folder skeleton (LAYOUT.md) - every directory created by new_run_dir / ensure_skeleton
RUN_SKELETON = [
    "00-input", "00-input/product-images", "00-input/segments",
    "10-measure", "10-measure/keyframes", "10-measure/keyframes/shots", "10-measure/keyframes/sampled",
    "10-measure/contact-sheets",
    "20-analysis",
    "30-decisions",
    "40-plan",
    "50-prompts", "50-prompts/references",
    "60-qa",
    "70-deliverables", "70-deliverables/references",
    "75-generation",
    "80-generated",
    "90-postgen", "90-postgen/project", "90-postgen/render",
    "logs",
]


# --------------------------------------------------------------------------------------
# tool resolution
# --------------------------------------------------------------------------------------
def _refresh_path_from_registry() -> None:
    """PATH inside a fresh shell can be stale; merge Machine + User PATH from the registry."""
    if os.name != "nt":
        return
    try:
        import winreg
        parts = []
        for hive, key in ((winreg.HKEY_LOCAL_MACHINE,
                           r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
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


def find_tool(name: str, fallback: Path | None = None) -> str:
    """Resolve an executable: PATH first, then the registry PATH, then the absolute fallback."""
    p = shutil.which(name)
    if p:
        return p
    _refresh_path_from_registry()
    p = shutil.which(name)
    if p:
        return p
    if fallback and Path(fallback).exists():
        return str(fallback)
    raise FileNotFoundError(f"{name} not found on PATH and fallback missing: {fallback}")


def ffmpeg() -> str:
    return find_tool("ffmpeg", FFMPEG_FALLBACK)


def ffprobe() -> str:
    return find_tool("ffprobe", FFPROBE_FALLBACK)


def python_exe() -> str:
    if sys.executable and Path(sys.executable).exists():
        return sys.executable
    return find_tool("python", PYTHON_FALLBACK)


# --------------------------------------------------------------------------------------
# small utilities
# --------------------------------------------------------------------------------------
def now_iso() -> str:
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def ts_name(seconds: float) -> str:
    """File-name-safe timestamp without colons: 12.4 -> '00m12.40s', 3725.5 -> '62m05.50s'."""
    seconds = max(0.0, float(seconds))
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}m{s:05.2f}s"


def fmt_hms(seconds: float) -> str:
    """Human timestamp for text: 12.4 -> '00:00:12.400'."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def fmt_mmss(seconds: float) -> str:
    """Short timestamp for burned-in labels: 12.4 -> '00:12.40'."""
    seconds = max(0.0, float(seconds))
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}:{s:05.2f}"


def fmt_srt(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - math.floor(seconds)) * 1000))
    if ms == 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def slugify(text: str, maxlen: int = 40) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", str(text)).strip("-").lower()
    text = re.sub(r"-{2,}", "-", text)
    return (text[:maxlen].strip("-")) or "run"


def sha1_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ensure_dir(p: str | Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_json(path: str | Path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data, indent: int = 2) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=_json_default)
    os.replace(tmp, p)
    return p


def _json_default(o):
    try:
        import numpy as np  # noqa
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.ndarray,)):
            return o.tolist()
    except Exception:
        pass
    if isinstance(o, Path):
        return str(o)
    return str(o)


def write_text(path: str | Path, text: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return p


def rel(run_dir: str | Path, path: str | Path) -> str:
    """Path relative to the run dir with forward slashes (for JSON indexes)."""
    try:
        return Path(path).resolve().relative_to(Path(run_dir).resolve()).as_posix()
    except ValueError:
        return str(path)


def parse_fraction(s) -> float:
    """'30000/1001' -> 29.97; '30' -> 30.0; None/'0/0' -> 0.0"""
    if s is None:
        return 0.0
    s = str(s)
    if "/" in s:
        a, b = s.split("/", 1)
        try:
            a, b = float(a), float(b)
            return a / b if b else 0.0
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def human_size(n: int) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} GB"


# --------------------------------------------------------------------------------------
# logging
# --------------------------------------------------------------------------------------
class Log:
    """Progress printer + append-only log file. info() prints unless quiet; everything is logged."""

    def __init__(self, path: str | Path | None, tag: str = "", quiet: bool = False):
        self.path = Path(path) if path else None
        self.tag = tag
        self.quiet = quiet
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, level: str, msg: str) -> None:
        line = f"[{now_iso()}] [{self.tag}] {level}: {msg}"
        if self.path:
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    def info(self, msg: str) -> None:
        self._write("INFO", msg)
        if not self.quiet:
            print(f"[{self.tag}] {msg}", flush=True)

    def warn(self, msg: str) -> None:
        self._write("WARN", msg)
        print(f"[{self.tag}] WARNING: {msg}", flush=True)

    def error(self, msg: str) -> None:
        self._write("ERROR", msg)
        print(f"[{self.tag}] ERROR: {msg}", file=sys.stderr, flush=True)

    def cmd(self, args, cwd=None) -> None:
        line = subprocess.list2cmdline([str(a) for a in args])
        if cwd:
            line = f"(cwd={cwd}) {line}"
        self._write("CMD", line[:4000])


def measure_log(run_dir: str | Path, tag: str, quiet: bool = False) -> Log:
    return Log(Path(run_dir) / "10-measure" / "measure.log", tag, quiet)


def script_log(run_dir: str | Path | None, tag: str, quiet: bool = False) -> Log:
    if run_dir is None:
        return Log(None, tag, quiet)
    return Log(Path(run_dir) / "logs" / f"{tag}.log", tag, quiet)


# --------------------------------------------------------------------------------------
# external commands
# --------------------------------------------------------------------------------------
class CmdResult:
    def __init__(self, args, returncode, stdout, stderr, elapsed, timed_out=False):
        self.args = [str(a) for a in args]
        self.returncode = returncode
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.elapsed = elapsed
        self.timed_out = timed_out

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def tail(self, n: int = 12) -> str:
        lines = (self.stderr or self.stdout).strip().splitlines()
        return "\n".join(lines[-n:])


class CmdError(RuntimeError):
    def __init__(self, res: CmdResult):
        self.res = res
        super().__init__(f"command failed rc={res.returncode}: {subprocess.list2cmdline(res.args)[:300]}\n{res.tail()}")


def run_cmd(args, log: Log | None = None, timeout: float = 1800, cwd=None, check: bool = False,
            env=None, capture: bool = True) -> CmdResult:
    """Run an external command (no shell), capture stdout/stderr as UTF-8, log command + result."""
    args = [str(a) for a in args]
    if log:
        log.cmd(args, cwd)
    t0 = time.time()
    try:
        p = subprocess.run(args, cwd=str(cwd) if cwd else None, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.PIPE if capture else None,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
        res = CmdResult(args, p.returncode, p.stdout, p.stderr, round(time.time() - t0, 3))
    except subprocess.TimeoutExpired as e:
        res = CmdResult(args, -1, e.stdout if isinstance(e.stdout, str) else "",
                        e.stderr if isinstance(e.stderr, str) else "", round(time.time() - t0, 3), timed_out=True)
    if log:
        status = "TIMEOUT" if res.timed_out else f"rc={res.returncode}"
        log._write("RESULT", f"{status} in {res.elapsed}s :: {Path(args[0]).name} {' '.join(args[1:3])}")
        if not res.ok:
            log._write("STDERR", res.tail(20))
    if check and not res.ok:
        raise CmdError(res)
    return res


def ffprobe_json(path: str | Path, log: Log | None = None) -> dict:
    res = run_cmd([ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                   "-show_chapters", str(path)], log=log, timeout=300)
    if not res.ok:
        raise CmdError(res)
    return json.loads(res.stdout or "{}")


def video_stream(probe: dict) -> dict | None:
    for s in probe.get("streams", []):
        if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic", 0) != 1:
            return s
    return None


def audio_streams(probe: dict) -> list:
    return [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]


def media_duration(probe: dict) -> float:
    fmt = probe.get("format", {})
    d = parse_fraction(fmt.get("duration"))
    if d <= 0:
        v = video_stream(probe)
        if v:
            d = parse_fraction(v.get("duration"))
    return float(d or 0.0)


def stream_fps(v: dict | None) -> float:
    if not v:
        return 0.0
    f = parse_fraction(v.get("avg_frame_rate"))
    if f <= 0 or f > 240:
        f = parse_fraction(v.get("r_frame_rate"))
    return f


# --------------------------------------------------------------------------------------
# run folder + state.json
# --------------------------------------------------------------------------------------
def ensure_skeleton(run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    for d in RUN_SKELETON:
        (run_dir / d).mkdir(parents=True, exist_ok=True)
    return run_dir


def new_run_dir(run_root: str | Path = DEFAULT_RUN_ROOT, slug: str = "run") -> Path:
    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(slug)
    run_dir = run_root / f"{stamp}-{slug}"
    n = 1
    while run_dir.exists():
        n += 1
        run_dir = run_root / f"{stamp}-{slug}-{n}"
    ensure_skeleton(run_dir)
    return run_dir


def state_path(run_dir: str | Path) -> Path:
    return Path(run_dir) / "state.json"


def state_get(run_dir: str | Path) -> dict:
    st = read_json(state_path(run_dir), default=None)
    if not isinstance(st, dict):
        st = {"run_id": Path(run_dir).name, "stage": None, "mode": None, "approach": None,
              "answers": {}, "files": {}, "next_step": None, "created": now_iso(), "updated": now_iso()}
    st.setdefault("files", {})
    st.setdefault("answers", {})
    return st


def state_set(run_dir: str | Path, **kv) -> dict:
    st = state_get(run_dir)
    st.update(kv)
    st["run_id"] = Path(run_dir).name
    st["updated"] = now_iso()
    write_json(state_path(run_dir), st)
    return st


def state_add_file(run_dir: str | Path, stage: str, path: str | Path) -> dict:
    st = state_get(run_dir)
    files = st.setdefault("files", {})
    lst = files.setdefault(stage, [])
    r = rel(run_dir, path)
    if r not in lst:
        lst.append(r)
    st["run_id"] = Path(run_dir).name
    st["updated"] = now_iso()
    write_json(state_path(run_dir), st)
    return st


def state_add_files(run_dir: str | Path, stage: str, paths) -> dict:
    st = state_get(run_dir)
    files = st.setdefault("files", {})
    lst = files.setdefault(stage, [])
    for p in paths:
        r = rel(run_dir, p)
        if r not in lst:
            lst.append(r)
    st["run_id"] = Path(run_dir).name
    st["updated"] = now_iso()
    write_json(state_path(run_dir), st)
    return st


def source_mp4(run_dir: str | Path) -> Path:
    p = Path(run_dir) / "00-input" / "source.mp4"
    if not p.exists():
        raise FileNotFoundError(f"missing {p} - run intake.py first")
    return p


def measure_dir(run_dir: str | Path) -> Path:
    return ensure_dir(Path(run_dir) / "10-measure")


def resolve_run_dir(arg: str) -> Path:
    p = Path(arg).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"run dir does not exist: {p}")
    return p


# --------------------------------------------------------------------------------------
# contact sheets (PIL, font-safe on Windows)
# --------------------------------------------------------------------------------------
def pick_font(size: int):
    from PIL import ImageFont
    for cand in FONT_CANDIDATES:
        try:
            if Path(cand).exists():
                return ImageFont.truetype(cand, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def build_contact_sheets(frames: list, out_dir: str | Path, portrait: bool = True, grid=(4, 4), padding: int = 4,
                         prefix: str = "sheet", quality: int = 88, cell=None, font_size: int | None = None) -> dict:
    """frames: list of {path, t, shot?, label?}; cells 270x480 (portrait) / 480x270 (landscape) unless cell given.

    Returns an index dict {sheets:[{sheet, file, cells:[{cell,row,col,t,shot,frame}]}], ...}. Each cell gets the
    timestamp and shot id burned into the top-left corner with a black box behind the text."""
    from PIL import Image, ImageDraw, ImageOps
    out_dir = ensure_dir(out_dir)
    if cell is None:
        cell = (270, 480) if portrait else (480, 270)
    cw, ch = cell
    cols, rows = grid
    per_sheet = cols * rows
    font = pick_font(font_size or max(14, int(cw * 0.06)))
    sheet_w = cols * cw + (cols + 1) * padding
    sheet_h = rows * ch + (rows + 1) * padding
    index = {"grid": [cols, rows], "cell": [cw, ch], "padding": padding, "cells_per_sheet": per_sheet,
             "n_frames": len(frames), "sheets": []}
    for si in range(0, len(frames), per_sheet):
        chunk = frames[si:si + per_sheet]
        sheet_no = si // per_sheet + 1
        canvas = Image.new("RGB", (sheet_w, sheet_h), (16, 16, 16))
        cells = []
        for ci, fr in enumerate(chunk):
            r, c = divmod(ci, cols)
            x = padding + c * (cw + padding)
            y = padding + r * (ch + padding)
            try:
                img = Image.open(fr["path"]).convert("RGB")
                img = ImageOps.pad(img, (cw, ch), color=(0, 0, 0), method=Image.Resampling.BILINEAR)
            except Exception:
                img = Image.new("RGB", (cw, ch), (40, 0, 0))
            canvas.paste(img, (x, y))
            d = ImageDraw.Draw(canvas)
            t = float(fr.get("t", 0.0))
            label = fr.get("label") or fmt_mmss(t)
            shot = fr.get("shot")
            lines = [label] + ([f"shot {int(shot):02d}"] if shot is not None else [])
            ty = y + 4
            for ln in lines:
                bbox = d.textbbox((x + 5, ty), ln, font=font)
                d.rectangle((bbox[0] - 3, bbox[1] - 2, bbox[2] + 3, bbox[3] + 2), fill=(0, 0, 0))
                d.text((x + 5, ty), ln, fill=(255, 255, 255), font=font)
                ty = bbox[3] + 5
            cells.append({"cell": ci + 1, "row": r + 1, "col": c + 1, "t": round(t, 3),
                          "shot": shot, "frame": Path(fr["path"]).name})
        fname = f"{prefix}-{sheet_no:02d}.jpg"
        canvas.save(out_dir / fname, "JPEG", quality=quality, optimize=True)
        index["sheets"].append({"sheet": sheet_no, "file": fname, "t_start": cells[0]["t"] if cells else None,
                                "t_end": cells[-1]["t"] if cells else None, "cells": cells})
    return index


# --------------------------------------------------------------------------------------
# argparse helpers
# --------------------------------------------------------------------------------------
def add_std_args(parser, run_dir: bool = True):
    if run_dir:
        parser.add_argument("--run-dir", required=True, help="run folder runs\\<YYYYMMDD-HHMMSS-slug>")
    parser.add_argument("--quiet", action="store_true", help="suppress progress lines (log file still written)")
    return parser


def timed(fn):
    """Decorator: returns (result, elapsed_seconds)."""
    def wrap(*a, **k):
        t0 = time.time()
        r = fn(*a, **k)
        return r, round(time.time() - t0, 2)
    return wrap
