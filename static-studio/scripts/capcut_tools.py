#!/usr/bin/env python3
"""capcut_tools.py - write and repair the CapCut project of a Static Studio video on this PC.

One command per call; every call prints one JSON object on its last line (exit 0 ok, 1 a step failed, 2 refused, 3 CapCut is running).
Commands: capcut-name | capcut-prep | capcut-repair | capcut-motion | capcut-transitions | capcut-font | capcut-text-anim.
How and in what order: reference/09-capcut-toolkit.md.

Provenance: these are the CapCut commands of this PC's analyze-with-loupe toolkit (scripts/awl.py, sha256 9d54c41ce5ff9163, copied 2026-11-19),
copied function by function with their helpers, the source lines unchanged. Changed on purpose, and only this:
  * AWL_HOME / AWL_FONTS_DIR are STUDIO_HOME / STUDIO_FONTS_DIR (this toolkit's own root, config.json and fonts folder);
  * the machine-wide CapCut store lock (one file for every toolkit that writes CapCut's shared project index) is read from
    config.json -> capcut.store_lock instead of the other toolkit's runs folder;
  * a few messages that named the other toolkit's commands, manual or run files were reworded (docstrings and comments keep the
    original wording);
  * the command-line glue at the end is new: the images' starts, moves and joins come from a file (--timeline), there is no run, and
    capcut-repair always keeps every text as it is (--keep-text; the other toolkit's house text style code is copied because
    capcut-repair names it, but nothing here turns it on).
Nothing else was changed; the CapCut logic is theirs.
"""

import argparse
from pathlib import Path
import datetime as dt
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import unicodedata
import uuid

sys.dont_write_bytecode = True
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


STUDIO_HOME = Path(os.environ.get("STUDIO_HOME") or Path(__file__).resolve().parent.parent)   # the library; STUDIO_HOME points tests at a temp copy


CONFIG_PATH = STUDIO_HOME / "config.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def cfg_get(path: str, default=None):
    cur = load_config()
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def out(obj: dict, code: int = 0):
    # one JSON object on the last line: U+2028/2029 are escaped so a line-splitting reader never cuts it in two
    print(json.dumps(obj, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    sys.exit(code)


def fail(msg: str, code: int = 1, **extra):
    out({"ok": False, "error": msg, **extra}, code)


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _replace(tmp: Path, path: Path) -> None:
    """os.replace that waits out a reader: on Windows a file another process holds open without FILE_SHARE_DELETE (a hook, Loupe, an editor
    reading it) refuses to be replaced for as long as it is held; short retries let the write through instead of failing the step."""
    for i in range(60):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 59:
                raise
            time.sleep(0.05)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    _replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    _replace(tmp, path)


def run(cmd: list, cwd=None, timeout=None, check=False) -> subprocess.CompletedProcess:
    cp = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=timeout)
    if check and cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(map(str, cmd))[:300]}\n"
                           f"{cp.stderr[-1500:]}")
    return cp


def runs_root() -> Path:
    """Where the runs live: config `runs_root`, else <library>/runs."""
    return Path(cfg_get("runs_root") or (STUDIO_HOME / "runs")).expanduser()


def resolve_run(run, must_exist: bool = True):
    """The run folder named by --run: a full path, a bare run name (`20261019-235823-19`) or a stamp prefix (`20261019-235823`)
    under the runs root. A prefix that matches several runs is refused with their names (the choice is the agent's). With
    must_exist False, nothing matching gives None instead of an error."""
    s = str(run or "").strip().strip('"')
    if not s:
        return None
    p = Path(s).expanduser()
    if p.is_dir():
        return p.resolve()
    root = runs_root()
    if "/" not in s and "\\" not in s:
        if (root / s).is_dir():
            return (root / s).resolve()
        hits = sorted(d for d in root.glob(s + "*") if d.is_dir()) if root.is_dir() else []
        if len(hits) == 1:
            return hits[0].resolve()
        if len(hits) > 1:
            fail(f"--run {s!r} matches {len(hits)} runs under {root}: " + ", ".join(d.name for d in hits[:8]) + " (name one)", 2)
    if must_exist:
        fail(f"run {s!r} not found: not a folder, and no run under {root} has that name or prefix", 2)
    return None


def _pid_alive(pid: int) -> bool:
    """Whether a process with this id runs now (Windows: OpenProcess and its exit code; never os.kill, which on Windows ends it)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return ctypes.GetLastError() == 5            # access denied: it exists
        try:
            code = ctypes.c_ulong()
            return not k32.GetExitCodeProcess(h, ctypes.byref(code)) or code.value == 259   # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _lock_owner_dead(path: Path) -> bool:
    """A lock file names its owner ("<pid> <time>"): true only when that process is gone (2026-11-07: a call killed under memory
    pressure left the GPU lock behind, and every FLUX 3 Klein call would have waited out the 4-hour stale time). An unreadable or
    still-empty file (its writer has not written yet) counts as alive."""
    try:
        first = path.read_text(encoding="utf-8", errors="replace").split()
        return bool(first) and first[0].isdigit() and int(first[0]) != os.getpid() and not _pid_alive(int(first[0]))
    except (OSError, ValueError):
        return False


class FileLock:
    """Cross-process lock (O_EXCL lock file). Production agents run in parallel (one per video), so every
    read-modify-write of a shared file (state.json, CapCut's store index) holds one of these. A lock whose owner process is gone is
    taken over at once; one whose owner lives waits out `stale` seconds."""

    def __init__(self, path, timeout: float = 120.0, stale: float = 600.0):
        self.path, self.timeout, self.stale, self.fd = Path(path), timeout, stale, None

    def __enter__(self):
        import time
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, f"{os.getpid()} {now_iso()}".encode())
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale or _lock_owner_dead(self.path):
                        self.path.unlink()          # left behind by a killed process
                        continue
                except FileNotFoundError:
                    continue
                if time.time() - t0 > self.timeout:
                    fail(f"lock busy: {self.path} (another agent is writing; retry)", 4)
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            os.close(self.fd)
        finally:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def _state_of(run) -> tuple:
    rd = resolve_run(run)
    p = rd / "state.json"
    if not p.is_file():
        fail(f"state.json not found in {rd}", 2)
    return rd, json.loads(p.read_text(encoding="utf-8"))


_FONT_GLYPHS = {}


def _font_glyphs(font_file) -> set:
    """The code points a TrueType or OpenType font file has a glyph for: its 'cmap' table's Unicode subtables of formats 4 and 12 (the
    rest are skipped), read with no library (fontTools is not installed here). A WOFF (compressed) or a file with no cmap raises ValueError."""
    p = Path(font_file)
    stt = p.stat()
    key = (str(p.resolve()), stt.st_mtime_ns, stt.st_size)
    if key in _FONT_GLYPHS:
        return _FONT_GLYPHS[key]
    d = p.read_bytes()
    base = struct.unpack(">I", d[12:16])[0] if d[:4] == b"ttcf" else 0          # a collection: its first font
    if d[base:base + 4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        raise ValueError("not a TrueType or OpenType font file (a WOFF is compressed)")
    cmap = None
    for k in range(struct.unpack(">H", d[base + 4:base + 6])[0]):
        tag, _cs, off, _ln = struct.unpack(">4sIII", d[base + 12 + 16 * k:base + 28 + 16 * k])
        if tag == b"cmap":
            cmap = off
            break
    if cmap is None:
        raise ValueError("the font file has no cmap table")
    got = set()
    for k in range(struct.unpack(">H", d[cmap + 2:cmap + 4])[0]):
        plat, enc, off = struct.unpack(">HHI", d[cmap + 4 + 8 * k:cmap + 12 + 8 * k])
        if not (plat == 0 or (plat == 3 and enc in (1, 10))):
            continue
        sub = cmap + off
        fmt = struct.unpack(">H", d[sub:sub + 2])[0]
        if fmt == 4:
            seg = struct.unpack(">H", d[sub + 6:sub + 8])[0] // 2
            o = sub + 14
            ends = struct.unpack(f">{seg}H", d[o:o + 2 * seg])
            starts = struct.unpack(f">{seg}H", d[o + 2 * seg + 2:o + 4 * seg + 2])
            deltas = struct.unpack(f">{seg}h", d[o + 4 * seg + 2:o + 6 * seg + 2])
            ro_at = o + 6 * seg + 2
            offs = struct.unpack(f">{seg}H", d[ro_at:ro_at + 2 * seg])
            for i in range(seg):
                if starts[i] == 0xFFFF:
                    continue
                for c in range(starts[i], min(ends[i], 0xFFFE) + 1):
                    if offs[i] == 0:
                        g = (c + deltas[i]) & 0xFFFF
                    else:
                        at = ro_at + 2 * i + offs[i] + 2 * (c - starts[i])
                        g = struct.unpack(">H", d[at:at + 2])[0] if at + 2 <= len(d) else 0
                        g = (g + deltas[i]) & 0xFFFF if g else 0
                    if g:
                        got.add(c)
        elif fmt == 12:
            for j in range(struct.unpack(">I", d[sub + 12:sub + 16])[0]):
                s0, e0, g0 = struct.unpack(">III", d[sub + 16 + 12 * j:sub + 28 + 12 * j])
                if e0 - s0 <= 0x110000:
                    got.update(c for c in range(s0, e0 + 1) if g0 + (c - s0))
    _FONT_GLYPHS[key] = got
    return got


def _font_report(font_file, text) -> dict:
    """Whether a font file has a glyph for every character of a text: {"font_missing_glyphs": [the characters without one, in order of
    their code points], "font_covers": bool}; a space, a control or a format character needs none. {"font_glyphs_error": ...} when the
    font file cannot be read. A fact for the agent (a font that lacks a script draws boxes or the default font's letters)."""
    try:
        have = _font_glyphs(font_file)
    except (OSError, ValueError, struct.error) as e:
        return {"font_missing_glyphs": None, "font_covers": None, "font_glyphs_error": f"{type(e).__name__}: {e}"[:200]}
    miss = sorted({c for c in str(text or "") if not c.isspace() and unicodedata.category(c) not in ("Cc", "Cf", "Cs") and ord(c) not in have})
    return {"font_missing_glyphs": miss, "font_covers": not miss}


def _cf_nn(video) -> str:
    m = re.search(r"(\d{1,3})", str(video or ""))
    return m.group(1).zfill(2) if m else str(video or "")


MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _capcut_store(explicit=None) -> Path:
    return Path(explicit or os.environ.get("CAPCUT_DRAFTS_DIR") or cfg_get("capcut.drafts_dir", "")
                or os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "User Data", "Projects", "com.lveditor.draft"))


def cmd_capcut_name(a):
    """Free CapCut project name for one Analyze Mode video: DD_Mon_YYYY_vNN (e.g. 01_Oct_2026_v03), with
    -2, -3 … appended when that folder already exists in the drafts store. English month names, any locale."""
    try:
        d = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
        nn = int(a.video)
    except ValueError:
        fail("--video must be a number and --date YYYY-MM-DD", 2)
    store = _capcut_store(a.store)
    if not store.is_dir():
        fail(f"CapCut drafts store not found: {store}", 2)
    base = f"{d.day:02d}_{MONTHS_EN[d.month - 1]}_{d.year}_v{nn:02d}" + _fmt_sfx(_fmt_tag_norm(getattr(a, "format", None)))
    name, k = base, 1
    while (store / name).exists():
        k += 1
        name = f"{base}-{k}"
    out({"ok": True, "name": name, "path": str(store / name), "store": str(store)})


def cmd_capcut_prep(a):
    """Run right after capcut_clone_draft (empty:true) and before any other CapCut call on the new draft.
    The clone copies the template's identity sidecar (draft_meta_info.json: the TEMPLATE's draft id, name
    and folder) and its timeline_layout.json (the template's timeline id). Set both aside (*.awlbak), drop
    the template's build artefacts, and point the layout at the new timeline id, so that
    `capcut register --apply --materials` (after capcut_save) recreates a correct identity.
    --canvas WxH sets the project's canvas (Static: the format's export size), labelled as capcut-cli labels its presets."""
    d = Path(a.draft)
    cp = d / "draft_content.json"
    if not cp.is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if (d / ".locked").exists():
        fail("the draft is open in CapCut (.locked present): close CapCut first", 2)
    content = json.loads(cp.read_text(encoding="utf-8"))
    tid, name = content.get("id"), content.get("name")
    if not tid:
        fail("draft_content.json has no timeline id", 2)
    if name and name != d.name:
        fail(f"draft_content.json name {name!r} differs from the folder {d.name!r}: is this the fresh clone?", 2)
    canvas = None
    if getattr(a, "canvas", None):
        cw, ch = _parse_size(a.canvas)
        if cw % 2 or ch % 2:
            fail(f"the canvas needs even edges, got {a.canvas}", 2)
        cc = dict(content.get("canvas_config") or {})
        cc.update({"width": cw, "height": ch,
                   "ratio": next((k for k in CAPCUT_RATIO_LABELS if STATIC_ASPECTS[k][0] * ch == STATIC_ASPECTS[k][1] * cw), "original")})
        content["canvas_config"] = cc
        cp.write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        canvas = cc
    moved = []
    for fn in ("draft_meta_info.json", "timeline_layout.json", "build-report.json", "build.log", "lint.json"):
        f = d / fn
        if f.exists():
            os.replace(f, d / (fn + ".awlbak"))
            moved.append(fn)
    write_json(d / "timeline_layout.json", {"dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [tid],
                                                           "timelineNames": ["Timeline 01"]}], "layoutOrientation": 1})
    out({"ok": True, "draft": str(d), "timeline_id": tid, "name": name, "set_aside": moved, "canvas": canvas,
         "next": "capcut_read_timeline → edits → capcut_validate → capcut_save, then: capcut_tools.py capcut-repair "
                 "--draft \"<draft>\""})


def _capcut_cli() -> str:
    exe = shutil.which("capcut")
    if exe:
        return exe
    for cand in (os.path.join(os.environ.get("APPDATA", ""), "npm", "capcut.cmd"),):
        if os.path.exists(cand):
            return cand
    fail("capcut-cli not found on PATH (npm i -g capcut-cli)", 1)


def _last_json(text: str):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                continue
    return None


def _link_local_materials(d: Path) -> dict:
    """CapCut 9.3+ (and JianYing 5.9+) open a local clip through its material's `local_material_id`, the id of the clip's entry in
    draft_meta_info.json -> draft_materials; blank, the clip shows as missing and CapCut's own Link-media dialog cannot repair it.
    `capcut register --materials` writes the entries but never the timeline; this writes the link on every video, photo and audio material
    whose file has an entry (as capcut-cli's `lint --fix` does, without that command's other repairs: it would also shorten texts over 7 s,
    trim overlapping captions, close main-track gaps and copy every external media file into the draft)."""
    side = json.loads((d / "draft_meta_info.json").read_text(encoding="utf-8-sig"))

    def key(p: str) -> str:
        return os.path.normcase(os.path.normpath(p if os.path.isabs(p) else str(d / p)))
    groups, entries = side.get("draft_materials"), []
    for g in (groups if isinstance(groups, list) else list((groups or {}).values()) if isinstance(groups, dict) else []):
        vals = g.get("value") if isinstance(g, dict) else g
        entries += [e for e in (vals if isinstance(vals, list) else []) if isinstance(e, dict)]
    by = {}
    for e in entries:
        if isinstance(e.get("file_Path"), str) and e.get("file_Path") and isinstance(e.get("id"), str) and e["id"]:
            by.setdefault(key(e["file_Path"]), e["id"])
    files, total, no_entry = [], 0, set()
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        n = 0
        for kind in ("videos", "audios"):
            for m in content.get("materials", {}).get(kind) or []:
                path = m.get("path")
                if not isinstance(path, str) or not path or re.match(r"(?i)^https?://", path) or not isinstance(m.get("id"), str):
                    continue
                eid, cur = by.get(key(path)), str(m.get("local_material_id") or "")
                if eid is None:
                    if not cur:
                        no_entry.add(path)
                    continue
                if cur != eid:
                    m["local_material_id"] = eid
                    n += 1
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".link.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "linked": n})
        total += n
    return {"linked": total, "files": files, "media_without_entry": sorted(no_entry)}


PHOTO_DURATION_US = 10800000000   # what CapCut writes on a still it imports itself (3 hours)


def _photo_durations(d: Path) -> dict:
    """A still added through the MCP has no duration of its own (ffprobe answers N/A for a PNG, so the material's duration is saved
    as null): CapCut's own still materials carry PHOTO_DURATION_US. Found 2026-11-22; this writes that value on every photo material
    whose duration is missing, zero or not a number, in every timeline document of the draft, and leaves everything else as it is."""
    files, total = [], 0
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        n = 0
        for m in content.get("materials", {}).get("videos") or []:
            if m.get("type") == "photo":
                v = m.get("duration")
                if not isinstance(v, (int, float)) or isinstance(v, bool) or v != v or v <= 0:
                    m["duration"] = PHOTO_DURATION_US
                    n += 1
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".photo.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "fixed": n})
        total += n
    return {"fixed": total, "files": files}


def cmd_capcut_repair(a):
    """After every capcut_save: the house text style on every text layer (capcut-text-style), then
    `capcut register --apply --materials` (identity from draft_content.json,
    the media list CapCut needs, the store index), CapCut's duration on every still added without one (_photo_durations), the media
    links CapCut 9.3+ opens clips by (_link_local_materials),
    `capcut sync-timelines --nested --apply` (the nested
    timeline copy CapCut 9.x reads first) and `capcut lint`. register rewrites the store's SHARED
    root_meta_info.json, so all three run under one machine-wide lock: production agents assemble their
    projects in parallel. --preview then renders capcut-cli's low-res proxy (outside the lock). --keep-text leaves every text as it is
    (Static: the text look is the references', never the house style)."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    cli = _capcut_cli()
    if (d / ".locked").exists() or _capcut_running():
        out({"ok": False, "draft": str(d), "steps": [],
             "action": "CapCut is running: close it and run this again (nothing was changed)"}, 1)
    lock = Path(cfg_get("capcut.store_lock", str(STUDIO_HOME / "runs" / ".capcut-store.lock")))
    lock.parent.mkdir(parents=True, exist_ok=True)
    steps = ([{"step": "text-style", "exit": 0, "result": "kept: the draft's own text look (--keep-text)"}] if getattr(a, "keep_text", False)
             else [{"step": "text-style", "exit": 0, "result": _text_style_pass(d, write=True)}])   # before sync-timelines
    with FileLock(lock, timeout=900):
        for name, args in (("register", ["register", str(d), "--apply", "--materials"]),
                           ("photo-durations", None),
                           ("link", None),
                           ("sync-timelines", ["sync-timelines", str(d), "--nested", "--apply"]),
                           ("lint", ["lint", str(d)])):
            if args is None:   # still durations, then the media links CapCut 9.3+ opens a clip by, from the entries register just wrote
                try:
                    steps.append({"step": name, "exit": 0,
                                  "result": _photo_durations(d) if name == "photo-durations" else _link_local_materials(d)})
                except (OSError, ValueError) as e:
                    steps.append({"step": name, "exit": 1, "result": f"{type(e).__name__}: {e}"})
                    break
                continue
            cp = run([cli, *args], timeout=900)
            steps.append({"step": name, "exit": cp.returncode,
                          "result": _last_json(cp.stdout) or (cp.stdout or "").strip()[-800:],
                          "stderr": (cp.stderr or "").strip()[-400:]})
            if name != "lint" and cp.returncode != 0:
                break
    codes = {s["step"]: s["exit"] for s in steps}
    ok = (codes.get("register") == 0 and codes.get("photo-durations") == 0 and codes.get("link") == 0
          and codes.get("sync-timelines") == 0 and codes.get("lint") in (0, 1))
    res = {"ok": ok, "draft": str(d), "steps": steps}
    if not ok:
        res["action"] = ("a step refused or lint found errors: CapCut running → close it and run this again; "
                         "lint errors → fix the timeline through the MCP, capcut_save, then run this again")
    elif a.preview:
        Path(a.preview).parent.mkdir(parents=True, exist_ok=True)
        cp = run([cli, "render", str(d), "--out", a.preview, "--burn-captions"], timeout=1800)
        res["preview"] = {"exit": cp.returncode, "file": a.preview if cp.returncode == 0 else None,
                          "result": _last_json(cp.stdout), "stderr": (cp.stderr or "").strip()[-400:]}
    out(res, 0 if ok else 1)


# the library's fonts folder; STUDIO_FONTS_DIR points the tests at a temp copy (T fetch-font writes there, capcut-font --list reads it)
FONTS_DIR = Path(os.environ.get("STUDIO_FONTS_DIR") or (Path(__file__).resolve().parent.parent / "fonts"))


# where a font file lives decides whether a project keeps finding it (2026-11-07: CapCut's own fonts sit in its version folder, which an
# update replaces, and the fonts it downloads sit in its cache, which it may clear: a project then shows its texts in the default font)
FONT_KEPT_BY = {"library": "this library's fonts folder: kept across CapCut updates and cache clears",
                "capcut": "CapCut's version folder: an update replaces it",
                "capcut-downloaded": "CapCut's cache: CapCut may clear it",
                "windows": "Windows' fonts folder", "user": "the user's Windows fonts folder"}


def _font_roots() -> list:
    la = Path(os.environ.get("LOCALAPPDATA", ""))
    apps = []
    for p in (la / "CapCut" / "Apps").glob("*"):
        try:
            apps.append((tuple(int(x) for x in p.name.split(".")), p))
        except ValueError:
            continue
    return [("library", FONTS_DIR)] + ([("capcut", max(apps)[1] / "Resources" / "Font")] if apps else []) + [
        ("capcut-downloaded", la / "CapCut" / "User Data" / "Cache"),
        ("windows", Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"),
        ("user", la / "Microsoft" / "Windows" / "Fonts")]


def _font_kept_by(f: Path) -> str:
    """How the folder of a font file is kept (FONT_KEPT_BY), or 'elsewhere'."""
    la = Path(os.environ.get("LOCALAPPDATA", ""))
    rf = str(Path(f).resolve()).lower()
    for src, root in [*_font_roots(), ("capcut", la / "CapCut" / "Apps")]:
        if rf.startswith(str(Path(root).resolve()).lower() + os.sep):
            return FONT_KEPT_BY[src]
    return "elsewhere"


def _font_files() -> list:
    """Font files on this PC the edit can use, as facts: this library's fonts folder first, then CapCut's own (bundled with the newest
    app, then the ones it downloaded), then Windows' and the user's, each with how its folder is kept. One row per family and style
    (the first file found), never a judgement of which fits."""
    roots = _font_roots()
    try:
        from PIL import ImageFont
    except ImportError:
        return []
    seen, rows = set(), []
    for src, root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if f.suffix.lower() not in (".ttf", ".otf", ".ttc") or "__MACOSX" in f.parts or f.name.startswith("._"):
                continue
            try:
                fam, sty = ImageFont.truetype(str(f), 20).getname()
            except Exception:  # noqa: BLE001
                continue
            key = (str(fam).lower(), str(sty).lower())
            if key not in seen:
                seen.add(key)
                rows.append({"family": fam, "style": sty, "file": str(f).replace("\\", "/"), "source": src, "kept_by": FONT_KEPT_BY[src]})
    return rows


def _text_outline_into_styles(m: dict, c: dict) -> bool:
    """capcut-cli's import-srt and add-text write a text's outline, box and shadow on the material only (border_*, background_*,
    has_shadow, check_flag 7). CapCut 9.x draws the outline from each style's `strokes` and shows each layer by its check_flag bit (8
    outline, 16 box, 32 shadow), as a text CapCut styled itself carries them (check_flag 15 with strokes). Writes those from the material's
    own values; True when the text has an outline."""
    flag = int(m.get("check_flag") or 7)
    width = float(m.get("border_width") or 0)
    outline = bool(m.get("border_color")) and width > 0 and m.get("has_border") is not False
    if outline:
        alpha = float(m.get("border_alpha", 1.0) if m.get("border_alpha") is not None else 1.0)
        stroke = {"alpha": alpha, "content": {"render_type": "solid", "solid": {"alpha": alpha, "color": _hex_rgb(str(m["border_color"]))}},
                  "width": width}
        for s in c.get("styles") or []:
            if not s.get("strokes"):
                s["strokes"] = [json.loads(json.dumps(stroke))]
        m.setdefault("border_mode", 0)
        flag |= 8
    if m.get("background_color") and float(m.get("background_alpha") or 0) > 0:
        flag |= 16
    if m.get("has_shadow"):
        flag |= 32
    m["check_flag"] = flag
    return outline


def cmd_capcut_font(a):
    """Static (contract item 36): --list the fonts on this PC (CapCut's own first), or set one font file on every text of a draft (or of
    one track), the text's own size, colours, outline, box and ranges kept: the font family capcut-cli's text flags cannot set. The
    outline, box and shadow capcut-cli set on the material are also written where CapCut 9.x draws them from (_text_outline_into_styles).
    The answer lists `font_missing_glyphs`: the characters of the texts it set that the font file has no glyph for (_font_glyphs reads the
    font's cmap), since a video in another language needs a font that has its script."""
    if a.list:
        rows = _font_files()
        if a.family:
            rows = [r for r in rows if a.family.lower() in str(r["family"]).lower()]
        out({"ok": True, "count": len(rows), "fonts": rows, "library": str(FONTS_DIR),
             "note": "CapCut draws its own fonts (capcut, capcut-downloaded) for sure; a Windows font is used when CapCut finds it; a "
                     "project keeps a font only while its file stays where it points (kept_by): use the library's copy"})
    if not a.draft or not a.font_file:
        fail("capcut-font needs --list, or --draft and --font-file", 2)
    d, ff = Path(a.draft), Path(a.font_file)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if not ff.is_file():
        fail(f"font file not found: {ff}", 2)
    if (d / ".locked").exists() or _capcut_running():
        fail("CapCut is running: close it, then run this again", 3)
    try:
        from PIL import ImageFont
        family = ImageFont.truetype(str(ff), 20).getname()[0]
    except Exception:  # noqa: BLE001
        family = ff.stem
    font = str(ff).replace("\\", "/")
    files, names, seen_text = [], set(), []
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        tracks = content.get("tracks", [])
        names.update(str(tr.get("name") or "") for tr in tracks if tr.get("type") == "text")
        ids = None
        if a.track:
            ids = {seg.get("material_id") for tr in tracks if str(tr.get("name") or "") == a.track for seg in tr.get("segments", [])}
        n = n_out = 0
        for m in content.get("materials", {}).get("texts", []):
            if ids is not None and m.get("id") not in ids:
                continue
            m.update({"font_name": "", "font_title": "none", "font_id": "", "font_resource_id": "", "font_category_id": "",
                      "font_category_name": "", "font_source_platform": 0, "font_team_id": "", "font_url": "", "fonts": [],
                      "font_path": font})
            try:
                c = json.loads(m.get("content") or "{}")
            except Exception:  # noqa: BLE001
                c = {}
            seen_text.append(str(c.get("text") or "") if isinstance(c, dict) else "")
            out_line = _text_outline_into_styles(m, c)
            for s in c.get("styles") or []:
                s["font"] = {"id": "", "path": font}
            if c:
                m["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
            n += 1
            n_out += bool(out_line)
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".font.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "texts_set": n, "outlines_in_styles": n_out})
    if a.track and not any(f["texts_set"] for f in files):
        fail(f"no text on a track named {a.track!r}; the draft's text tracks: {sorted(names)}", 2)
    out({"ok": True, "draft": str(d), "font": font, "family": family, "track": a.track, "files": files, "font_kept_by": _font_kept_by(ff),
         **_font_report(ff, "".join(seen_text)),
         "note": "then capcut_save is not needed (the file is written); run `capcut_tools.py capcut-repair --draft ... --keep-text` after the last save; "
                 "a font CapCut downloaded or bundled is copied into the library's fonts folder first so the project keeps it; "
                 "font_missing_glyphs lists the characters of those texts the font file has no glyph for (a font that lacks a script draws "
                 "boxes or another font's letters: the language's font is the agent's pick)"})


CAPCUT_MOVE_PROPS = ("UNIFORM_SCALE", "KFTypeScaleX", "KFTypeScaleY", "KFTypePositionX", "KFTypePositionY")


def _kf_list(prop: str, dur_us: int, v0: float, v1: float) -> dict:
    import uuid

    def one(t, v):
        return {"id": str(uuid.uuid4()).upper(), "curveType": "Line", "time_offset": int(t), "left_control": {"x": 0.0, "y": 0.0},
                "right_control": {"x": 0.0, "y": 0.0}, "values": [float(v)], "string_value": "", "graphID": ""}
    return {"id": str(uuid.uuid4()).upper(), "material_id": "", "property_type": prop, "keyframe_list": [one(0, v0), one(dur_us, v1)]}


def cmd_capcut_motion(a):
    """Static (contract item 36): each image's move from the run's timeline written into its CapCut clip as keyframes CapCut 9.x plays:
    the scale as KFTypeScaleX with the clip's uniform scale on, the position as KFTypePositionX / KFTypePositionY (half-canvas units, y
    up), at the clip's first and last moment, linear, the same values the check render draws. CapCut 9.7 ignores UNIFORM_SCALE
    keyframes (2026-11-06: a project keyed that way exported with every still static), so any scale or position keyframes already on
    those clips are replaced. Clips are matched to the timeline's images by their start (within half a frame). Run it after the last
    capcut_save (the MCP would write its own copy of the timeline back over it)."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if (d / ".locked").exists() or _capcut_running():
        fail("CapCut is running: close it, then run this again", 3)
    tlp = _run_timeline_path(a)
    if not tlp or not tlp.is_file():
        fail("capcut-motion needs --timeline <file> (the images' starts, moves and joins)", 2)
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    fps = int(tl.get("fps") or 30)
    rows = [{**r, **({} if "scale" in r else _still_motion(r))} for r in tl.get("images") or []]
    half = 500000 / fps
    files, unmatched, made, stale = [], set(), {}, []

    def keys(prop, image, dur, v0, v1):   # one set of keyframes per clip, the same ids in every copy of the timeline
        if (prop, image, dur) not in made:
            made[(prop, image, dur)] = _kf_list(prop, dur, v0, v1)
        return json.loads(json.dumps(made[(prop, image, dur)]))
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
        segs = (main or {}).get("segments") or []
        keyed, found = 0, set()
        main_file = p == d / "draft_content.json"   # the timeline itself; the other copies are mirrors of it
        for r in rows:
            want = float(r["start"]) * 1e6
            seg = next((s for s in segs if abs(int((s.get("target_timerange") or {}).get("start") or 0) - want) <= half), None)
            if seg is None:
                if main_file:
                    unmatched.add(int(r["image"]))
                continue
            found.add(int(r["image"]))
            dur = int(seg["target_timerange"]["duration"])
            (s0, s1), (x0, x1), (y0, y1) = r["scale"], r["x"], r["y"]
            kfs = [k for k in seg.get("common_keyframes") or [] if k.get("property_type") not in CAPCUT_MOVE_PROPS]
            if (s0, s1) != (1.0, 1.0):
                kfs.append(keys("KFTypeScaleX", r["image"], dur, s0, s1))
            if (x0, x1) != (0.0, 0.0):
                kfs.append(keys("KFTypePositionX", r["image"], dur, x0, x1))
            if (y0, y1) != (0.0, 0.0):
                kfs.append(keys("KFTypePositionY", r["image"], dur, y0, y1))
            seg["common_keyframes"] = kfs
            seg["uniform_scale"] = {"on": True, "value": 1.0}
            clip = seg.setdefault("clip", {})
            clip["scale"] = {"x": float(s0), "y": float(s0)}
            clip["transform"] = {"x": float(x0), "y": float(y0)}
            keyed += 1
        if not main_file and len(found) < len(rows):
            # a mirror still holding another timeline (the template's draft_info.json after an empty clone and an MCP save, 2026-11-06):
            # capcut-cli's next write and capcut-repair's sync-timelines rewrite it from draft_content.json, keyframes included
            stale.append({"file": str(p), "clips_on_main_track": len(segs), "images_not_there": len(rows) - len(found)})
        if keyed:
            shutil.copyfile(p, p.with_name(p.name + ".motion.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "clips_keyed": keyed, "clips_on_main_track": len(segs)})
    main_keyed = next((f["clips_keyed"] for f in files if f["file"] == str(d / "draft_content.json")), 0)
    out({"ok": not unmatched and main_keyed > 0, "draft": str(d), "timeline": str(tlp), "files": files,
         "images_without_a_clip": sorted(unmatched), "stale_copies": stale,
         "moves": [[r["image"], r["motion"], r["scale"], r["x"], r["y"]] for r in rows],
         "note": "scale = KFTypeScaleX with uniform scale on; position in half-canvas units (x right, y up); run `capcut_tools.py capcut-repair` after "
                 "(its sync-timelines rewrites a copy listed in stale_copies from draft_content.json)"})


def _capcut_pro_ok(rd: Path = None) -> bool:
    """Whether a CapCut Pro option may go into a project: the run's CapCut plan (state.json -> capcut_plan, free | pro, asked at the start
    of a Static run: the user, 2026-11-06, "make him pick, if he picks pro then be free to pick any edit feature that pro has"), else
    config.json -> capcut.pro (this PC's default)."""
    if rd is not None:
        try:
            plan = str(json.loads((Path(rd) / "state.json").read_text(encoding="utf-8")).get("capcut_plan") or "").lower()
            if plan in ("free", "pro"):
                return plan == "pro"
        except (OSError, ValueError):
            pass
    return bool(cfg_get("capcut.pro", False))


def _catalogue_refusal(kind: str, slug: str, pro_ok: bool) -> str | None:
    """Why a text intro or a transition may not go into a project, from the measured catalogue (data/capcut-catalogue.json): CapCut drew
    nothing for it in the check, or it is Pro and the run's plan is free. None when it may (or when no catalogue was measured yet)."""
    try:
        cat = json.loads((STUDIO_HOME / "data" / "capcut-catalogue.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = {str(x.get("slug")): x for x in cat.get("text_intros" if kind == "intro" else "transitions") or []}
    x = rows.get(slug)
    if x is None:
        return f"{slug!r} is not in the measured catalogue (data/capcut-catalogue.md): not verified on this PC's CapCut"
    if not x.get("visible_animation" if kind == "intro" else "visible_transition"):
        return f"{slug!r}: CapCut drew nothing for it in the CapCut check (data/capcut-catalogue.md)"
    if x.get("pro") and not pro_ok:
        return f"{slug!r} is CapCut Pro and this PC's CapCut is free (config.json -> capcut.pro): the export would be blocked"
    return None


def _anim_slug(name) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")


def _text_anim_template(content: dict, slug: str, kind: str):
    """An animation of `kind` (in|out) named as `slug` that capcut-cli already wrote into this draft, to copy."""
    for m in content.get("materials", {}).get("material_animations", []):
        for an in m.get("animations") or []:
            if an.get("type") == kind and _anim_slug(an.get("name")) == slug:
                return m, an
    return None, None


def _seg_has_anim(content: dict, seg: dict, kind: str) -> bool:
    refs = set(seg.get("extra_material_refs") or [])
    return any(m.get("id") in refs and any(an.get("type") == kind for an in m.get("animations") or [])
               for m in content.get("materials", {}).get("material_animations", []))


def cmd_capcut_text_anim(a):
    """Static: one of CapCut's own text animations on every text of a track (an intro, an outro or both), through capcut-cli's
    `text-anim` and its catalogue (`capcut enums --text-intros`; CapCut fetches the effect by its id when it opens the project), each
    one's duration capped at its text's own. A text that already has one of that kind is left as it is. An intro the measured catalogue
    shows CapCut not drawing, or a Pro one on a run whose CapCut plan is free, is refused."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if not a.intro and not a.outro:
        fail("capcut-text-anim needs --intro and/or --outro (a slug from `capcut enums --text-intros` / `--text-outros`)", 2)
    if a.intro:
        why = _catalogue_refusal("intro", a.intro, _capcut_pro_ok(_state_of(a.run)[0] if a.run else None))
        if why:
            fail(why, 2)
    if (d / ".locked").exists() or _capcut_running():
        fail("CapCut is running: close it, then run this again", 3)
    cli = _capcut_cli()
    content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    segs = [s for tr in content.get("tracks", []) if tr.get("type") == "text" and (not a.track or str(tr.get("name") or "") == a.track)
            for s in tr.get("segments", [])]
    if not segs:
        fail(f"no text on {'a track named ' + repr(a.track) if a.track else 'any text track'}", 2)
    done, kept, failed = 0, 0, []
    cloned = 0
    if a.intro and not a.outro:
        # many texts (one per caption word): capcut-cli writes the intro once, every other text gets a copy of that animation in one
        # pass (the same material, its own id, its duration capped at its text's), in every copy of the timeline
        _m, tmpl = _text_anim_template(content, a.intro, "in")
        if tmpl is None:
            first = next((s for s in segs if not _seg_has_anim(content, s, "in")), None)
            if first is not None:
                dur_s = int((first.get("target_timerange") or {}).get("duration") or 0) / 1e6
                cp = run([cli, "text-anim", str(d), str(first["id"]), "--intro", a.intro, "--intro-duration",
                          f"{max(0.001, min(float(a.intro_duration), dur_s)):.3f}s"], timeout=120)
                if cp.returncode != 0:
                    fail("capcut-cli text-anim: " + str((_last_json(cp.stdout) or {}).get("error") or cp.stderr or cp.stdout)[-300:], 1)
                done += 1
                content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
                _m, tmpl = _text_anim_template(content, a.intro, "in")
        if tmpl is not None:
            want = {str(s["id"]) for s in segs}
            new_ids = {}
            for p in _draft_contents(d):
                c2 = json.loads(p.read_text(encoding="utf-8"))
                mats2 = c2.setdefault("materials", {}).setdefault("material_animations", [])
                n_here, k_here = 0, 0
                for tr in c2.get("tracks", []):
                    for s in tr.get("segments", []):
                        if str(s.get("id")) not in want:
                            continue
                        if _seg_has_anim(c2, s, "in"):
                            k_here += 1
                            continue
                        mid = new_ids.setdefault(str(s["id"]), str(uuid.uuid4()))
                        an = json.loads(json.dumps(tmpl))
                        seg_us = int((s.get("target_timerange") or {}).get("duration") or 0)
                        an["duration"] = max(1000, min(int(round(float(a.intro_duration) * 1e6)), seg_us))
                        an["start"] = 0
                        mats2.append({**json.loads(json.dumps(_m)), "id": mid, "animations": [an]})
                        s.setdefault("extra_material_refs", []).append(mid)
                        n_here += 1
                p.write_text(json.dumps(c2, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                if p == d / "draft_content.json":  # the counts are the main timeline's; its mirrors get the same copies
                    cloned, kept = n_here, k_here - (1 if done else 0)
            out({"ok": True, "draft": str(d), "track": a.track, "intro": a.intro, "intro_duration_s": float(a.intro_duration),
                 "texts": len(segs), "animated": done + cloned, "by_capcut_cli": done, "copied": cloned, "already_animated": kept,
                 "failed": [], "note": "CapCut shows the entrance once it has fetched the effect"})
    for s in segs:
        dur_s = int((s.get("target_timerange") or {}).get("duration") or 0) / 1e6
        args = [cli, "text-anim", str(d), str(s["id"])]
        if a.intro:
            args += ["--intro", a.intro, "--intro-duration", f"{max(0.001, min(float(a.intro_duration), dur_s)):.3f}s"]
        if a.outro:
            args += ["--outro", a.outro, "--outro-duration", f"{max(0.001, min(float(a.outro_duration), dur_s)):.3f}s"]
        cp = run(args, timeout=120)
        msg = (_last_json(cp.stdout) or {}).get("error") or (cp.stderr or cp.stdout or "").strip()[-300:]
        if cp.returncode == 0:
            done += 1
        elif "already has" in str(msg):
            kept += 1
        else:
            failed.append({"segment": s["id"], "error": msg})
    out({"ok": not failed, "draft": str(d), "track": a.track, "intro": a.intro, "intro_duration_s": float(a.intro_duration) if a.intro else None,
         "outro": a.outro, "texts": len(segs), "animated": done, "already_animated": kept, "failed": failed[:5],
         "note": "CapCut shows the entrance once it has fetched the effect"},
        0 if not failed else 1)


def _run_timeline_path(a):
    """--timeline FILE, else the run's timeline of the video: 40-briefs/video-NN-timeline.json, or an extra format's
    40-briefs/video-NN-timeline-<tag>.json (--format)."""
    if getattr(a, "timeline", None):
        return Path(a.timeline)
    if not (getattr(a, "run", None) and getattr(a, "video", None)):
        return None
    rd, st = _state_of(a.run)
    return rd / "40-briefs" / f"video-{_cf_nn(a.video)}-timeline{_fmt_sfx(_fmt_tag(st, getattr(a, 'format', None)))}.json"


def _capcut_enum(cli: str, flag: str) -> list:
    cp = run([cli, "enums", flag], timeout=120)
    try:
        return json.loads(cp.stdout)
    except ValueError:
        fail(f"capcut enums {flag} gave no list: {(cp.stdout or cp.stderr)[-300:]}", 1)


def _main_clips(d: Path) -> list:
    content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
    return sorted((main or {}).get("segments") or [], key=lambda s: int(s["target_timerange"]["start"]))


def cmd_capcut_transitions(a):
    """Static: the timeline's joins as CapCut's own transitions (capcut-cli `transition`, a slug from `capcut enums --transitions`; the
    measured catalogue says which play and how, data/capcut-catalogue.md): for every image whose join in is not a cut, the transition
    on the clip before it, for the timeline's seconds. Clips are matched by their start. A clip that already has one keeps it."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if (d / ".locked").exists() or _capcut_running():
        fail("CapCut is running: close it, then run this again", 3)
    tlp = _run_timeline_path(a)
    if not tlp or not tlp.is_file():
        fail("capcut-transitions needs --timeline <file> (the images' starts, moves and joins)", 2)
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    rows, fps, cli = tl.get("images") or [], int(tl.get("fps") or 30), _capcut_cli()
    known = {x.get("slug") for x in _capcut_enum(cli, "--transitions")}
    clips = _main_clips(d)
    half = 500000 / fps
    pro_ok = _capcut_pro_ok(_state_of(a.run)[0] if a.run else None)
    done, kept, failed = [], 0, []
    for k in range(1, len(rows)):
        slug = str(rows[k].get("transition") or "cut")
        if slug == "cut":
            continue
        if slug not in known:
            failed.append({"image": rows[k]["image"], "error": f"{slug!r} is not a CapCut transition (capcut enums --transitions)"})
            continue
        why = _catalogue_refusal("transition", slug, pro_ok)
        if why:
            failed.append({"image": rows[k]["image"], "error": why})
            continue
        want = float(rows[k - 1]["start"]) * 1e6
        seg = next((s for s in clips if abs(int(s["target_timerange"]["start"]) - want) <= half), None)
        if seg is None:
            failed.append({"image": rows[k]["image"], "error": "no clip starts where the image before it starts"})
            continue
        cp = run([cli, "transition", str(d), str(seg["id"]), slug, "--duration", f"{float(rows[k].get('trans_s') or 0.5):.3f}s"], timeout=120)
        msg = (_last_json(cp.stdout) or {}).get("error") or (cp.stderr or "").strip()[-300:]
        if cp.returncode == 0:
            done.append({"into_image": rows[k]["image"], "transition": slug, "s": rows[k].get("trans_s")})
        elif "already has" in str(msg):
            kept += 1
        else:
            failed.append({"image": rows[k]["image"], "error": msg})
    out({"ok": not failed, "draft": str(d), "transitions": done, "already_there": kept, "failed": failed,
         "note": "only transitions the CapCut check verified (data/capcut-catalogue.md); run `capcut_tools.py capcut-repair` after"}, 0 if not failed else 1)


HOUSE_TEXT_DEFAULT = {"font": "System", "size": 10, "fill": "#FFFFFF",
                      "stroke": {"color": "#000000", "width": 0.08},
                      # the user, 2026-10-29: "our standard text size is 10 but when there's only few text to be placed then use
                      # font size 11" (one size per video; config capcut.text_style.short_text, null turns it off)
                      "short_text": {"size": 11, "max_words_at_once": 5, "max_line_width": 0.82}}


# CapCut draws a size-s text with a font of CAPCUT_FONT_PER_SIZE * s * (canvas width) px. Measured on the covers CapCut itself
# rendered with its System font: 03_Oct_2026_v09 (size 10, lines 956 and 942 px wide on 1080) and 06_Oct_2026_v14 (size 9, 954 px).
CAPCUT_FONT_PER_SIZE = 0.00575


def _house_text_style() -> dict:
    cfg = cfg_get("capcut.text_style") or {}
    st = {**HOUSE_TEXT_DEFAULT, **cfg}
    st["stroke"] = {**HOUSE_TEXT_DEFAULT["stroke"], **(st.get("stroke") or {})}
    off = "short_text" in cfg and not cfg["short_text"]
    st["short_text"] = None if off else {**HOUSE_TEXT_DEFAULT["short_text"], **(cfg.get("short_text") or {})}
    return st


def _capcut_system_font() -> str:
    """CapCut's 'System' font, the one a fresh text gets: <CapCut>/Apps/<newest version>/Resources/Font/SystemFont/en.ttf."""
    found = []
    for d in (Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "Apps").glob("*"):
        f = d / "Resources" / "Font" / "SystemFont" / "en.ttf"
        if f.is_file():
            try:
                found.append((tuple(int(x) for x in d.name.split(".")), f))
            except ValueError:
                continue
    return str(max(found)[1]).replace("\\", "/") if found else ""


def _capcut_running() -> bool:
    if os.name != "nt":
        return False
    try:
        return "capcut.exe" in (run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], timeout=30).stdout or "").lower()
    except Exception:
        return False


def _hex_rgb(h: str) -> list:
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 6) for i in (0, 2, 4)]


def _house_text_material(m: dict, st: dict, font_path: str, size: float) -> bool:
    """Rewrite one text material to the house style at `size` (the video's, _house_text_size); True when it changed. The text,
    its ranges, position and timing stay; font, size, fill, outline, shadow, background and preset fields become the house ones."""
    before = json.dumps(m, sort_keys=True)
    size = float(size)
    learned = st.get("learned") or {}
    lmat, lsty = learned.get("material") or {}, learned.get("style")
    if lmat:
        for k, v in lmat.items():
            m[k] = json.loads(json.dumps(v))
    else:
        m.update({"font_name": "", "font_title": "none", "font_id": "", "font_resource_id": "",
                  "font_category_id": "", "font_category_name": "", "font_source_platform": 0,
                  "font_team_id": "", "font_url": "", "fonts": [],
                  "text_color": st["fill"], "text_alpha": 1.0, "has_border": True,
                  "border_color": st["stroke"]["color"], "border_width": st["stroke"]["width"], "border_alpha": 1.0,
                  "has_shadow": False, "background_alpha": 0.0, "background_style": 0})
    m["font_path"] = font_path
    m["font_size"] = size
    try:
        content = json.loads(m.get("content") or "{}")
    except Exception:
        content = {}
    text = content.get("text", "")
    styles = []
    for old in (content.get("styles") or [{"range": [0, len(text)]}]):
        if lsty is not None:
            ns = json.loads(json.dumps(lsty))
        else:
            ns = {"fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                                     "solid": {"alpha": 1.0, "color": _hex_rgb(st["fill"])}}},
                  "strokes": [{"content": {"render_type": "solid",
                                           "solid": {"alpha": 1.0, "color": _hex_rgb(st["stroke"]["color"])}},
                               "width": st["stroke"]["width"]}],
                  "useLetterColor": True}
        ns["range"] = old.get("range", [0, len(text)])
        ns["size"] = size
        ns["font"] = {"id": "", "path": font_path}
        styles.append(ns)
    content["styles"] = styles
    m["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(m, sort_keys=True) != before


def _draft_contents(d: Path) -> list:
    """The project root's timeline documents, every copy a text, font, link or caption fix is written into: draft_content.json, its
    draft_info.json mirror (the macOS name, which capcut-cli keeps identical when it exists) and the template-2.tmp CapCut 9.7 writes
    when the user opens the project (capcut-cli reads it as the timeline when it is there: 2026-11-09 a caption rebuild that changed
    only the first two read the old captions back from it). CapCut 9.x's nested copies (Timelines/<id>/) are never written here:
    `capcut_tools.py capcut-repair` copies the root into them (capcut-cli sync-timelines --nested), which refuses when a nested copy is newer and
    different, i.e. edited in CapCut since (2026-11-09: these commands also wrote the nested draft_content.json, which then looked
    newer than the root and blocked that copy)."""
    return [p for p in [d / "draft_content.json", d / "draft_info.json", d / "template-2.tmp"] if p.is_file()]


def _timeline_texts(content: dict) -> list:
    """The text events a timeline shows: every segment that uses a text material, with its text, in and out (s) and scale."""
    mats = {m.get("id"): m for m in content.get("materials", {}).get("texts", [])}
    out = []
    for tr in content.get("tracks", []):
        for seg in tr.get("segments", []):
            m = mats.get(seg.get("material_id"))
            r = seg.get("target_timerange") or {}
            start, dur = int(r.get("start") or 0), int(r.get("duration") or 0)
            if m is None or dur <= 0:
                continue
            try:
                text = json.loads(m.get("content") or "{}").get("text", "")
            except Exception:
                text = ""
            scale = ((seg.get("clip") or {}).get("scale") or {}).get("x")
            out.append({"text": text, "start": start / 1e6, "end": (start + dur) / 1e6, "scale": float(scale or 1.0)})
    return out


_FONT100 = {}


def _line_width_frac(text: str, size: float, font_path: str, scale: float = 1.0) -> float:
    """The widest line of `text` at CapCut `size`, as a fraction of the canvas width (the font's ink extent, CAPCUT_FONT_PER_SIZE)."""
    if font_path not in _FONT100:
        from PIL import ImageFont
        _FONT100[font_path] = ImageFont.truetype(font_path, 100)
    f, widest = _FONT100[font_path], 0
    for line in text.split("\n"):
        if line.strip():
            left, _, right, _ = f.getbbox(line)
            widest = max(widest, right - left)
    return widest / 100 * CAPCUT_FONT_PER_SIZE * float(size) * float(scale or 1.0)


def _house_text_size(events: list, st: dict, font_path: str) -> dict:
    """One size for every text of a video: the house size (10), or short_text.size (11) when the video has only a little text,
    that is at no moment more than short_text.max_words_at_once words on screen (every text shown at that moment counted, so a
    caption split into two layers counts whole) and, at that size, every line within short_text.max_line_width of the frame
    width. Counted and measured from the timeline (the user, 2026-10-29)."""
    base = float(st["size"])
    rule = st.get("short_text")
    res = {"size": base, "base_size": base, "texts_on_timeline": len(events)}
    if not rule:
        res["short_text"] = "off (config capcut.text_style.short_text is null)"
        return res
    short, max_words, max_width = float(rule["size"]), int(rule["max_words_at_once"]), float(rule["max_line_width"])
    res["short_text"] = {"size": short, "max_words_at_once": max_words, "max_line_width": max_width}
    if not events:
        return res
    peak, at = 0, 0.0
    for e in events:
        n = sum(len(x["text"].split()) for x in events if x["start"] <= e["start"] < x["end"])
        if n > peak:
            peak, at = n, e["start"]
    try:
        widest = max(((_line_width_frac(e["text"], short, font_path, e["scale"]), e["text"]) for e in events), key=lambda w: w[0])
    except Exception as ex:   # the font cannot be measured: the house size stays
        res.update({"words_at_once_max": peak, "measure_error": str(ex)[:200]})
        return res
    little, fits = peak <= max_words, widest[0] <= max_width
    res.update({"size": short if little and fits else base, "words_at_once_max": peak, "words_at_once_max_at_s": round(at, 2),
                "widest_line_at_short_size": round(widest[0], 3), "widest_text": widest[1],
                "why": (f"{peak} word(s) at most on screen at once ({'<=' if little else '>'} {max_words}); widest line "
                        f"{widest[0]:.0%} of the frame width at size {short:g} ({'<=' if fits else '>'} {max_width:.0%})")})
    return res


def _text_style_pass(d: Path, write: bool) -> dict:
    st = _house_text_style()
    font = _capcut_system_font() or (st.get("learned") or {}).get("font_path") or ""
    if not font:
        fail("CapCut's System font was not found (<LOCALAPPDATA>/CapCut/Apps/<version>/Resources/Font/SystemFont/en.ttf)", 1)
    paths = _draft_contents(d)
    contents = {p: json.loads(p.read_text(encoding="utf-8")) for p in paths}
    newest = max(paths, key=lambda p: p.stat().st_mtime)   # the copy written last (the save, or CapCut) holds the timeline
    sizing = _house_text_size(_timeline_texts(contents[newest]), st, font)
    files, changed_ids = [], set()
    for p in paths:
        content = contents[p]
        changed = [m.get("id") for m in content.get("materials", {}).get("texts", [])
                   if _house_text_material(m, st, font, sizing["size"])]
        changed_ids.update(changed)
        if changed and write:
            shutil.copyfile(p, p.with_name(p.name + ".textstyle.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "texts_off_style": len(changed)})
    return {"font": font, "size": sizing["size"], "sizing": sizing,
            "preset": "learned" if st.get("learned") else "default (not calibrated)",
            "files": files, "texts_off_style": len(changed_ids), "written": bool(write and changed_ids)}


STATIC_ASPECTS = {"9:16": (9, 16), "16:9": (16, 9), "1:1": (1, 1), "4:5": (4, 5), "3:4": (3, 4), "4:3": (4, 3)}


CAPCUT_RATIO_LABELS = ("16:9", "9:16", "1:1", "4:3", "3:4")     # capcut-cli's canvas presets; any other canvas is labelled "original"


def _parse_size(s) -> tuple:
    m = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", str(s or ""))
    if not m:
        fail(f"a size is WIDTHxHEIGHT, got {s!r}", 2)
    return int(m.group(1)), int(m.group(2))


def _static_fmt(st: dict) -> dict:
    return ((st or {}).get("static") or {}).get("format") or {}


def _fmt_tag_norm(v) -> str:
    """'9:16', '9x16' or '9×16' -> '9x16'; '' for none."""
    return re.sub(r"[^0-9x]", "", str(v or "").strip().lower().replace(":", "x").replace("×", "x"))


def _extra_formats(st: dict) -> list:
    return list(((st or {}).get("static") or {}).get("extra_formats") or [])


def _fmt_tag(st: dict, v) -> str:
    """The format a command works on: '' for the run's primary format, else the tag of an extra format the run holds. A value naming
    the primary's aspect is the primary; one the run does not hold is refused, with the run's formats."""
    t = _fmt_tag_norm(v)
    if not t or t == _fmt_tag_norm(_static_fmt(st).get("aspect")):
        return ""
    tags = [f.get("tag") for f in _extra_formats(st)]
    if t not in tags:
        fail(f"the run has no format {v!r}: its formats are " + ", ".join([_static_fmt(st).get("aspect") or "none (T static format)"]
             + [x.replace("x", ":") for x in tags]) + " (`T static format --also` adds one)", 2)
    return t


def _fmt_sfx(tag: str) -> str:
    return f"-{tag}" if tag else ""


def _still_motion(r: dict) -> dict:
    """An image's move as the values CapCut keys and the render draws: the scale (1 = the image covers the canvas) and the position of
    its centre in half-canvas units (x to the right, y up, as CapCut stores a clip's position), at the image's start and at its end,
    linear in between. A named motion with its amount (the zoom's change, or for a pan the scale it travels at), or the row's own
    `scale`, `x`, `y` pairs (a pan with a slow zoom, a zoom toward a corner). `edge_shows` is a fact: an edge of the picture would show."""
    a = max(0.0, float(r.get("amount") or 0.0))      # no stock amount: the plan decides it from the references (static §5)
    m = str(r.get("motion") or "none").lower()
    s0 = s1 = 1.0 + (a if m.startswith("pan") else 0.0)
    x0 = x1 = y0 = y1 = 0.0
    e = round(0.98 * a, 4)   # a pan travels the margin its scale gives, a hair inside the picture's edges
    if m == "zoom-in":
        s0, s1 = 1.0, 1.0 + a
    elif m == "zoom-out":
        s0, s1 = 1.0 + a, 1.0
    elif m == "pan-right":           # the view travels right: the picture slides left
        x0, x1 = e, -e
    elif m == "pan-left":
        x0, x1 = -e, e
    elif m == "pan-up":              # the view travels up: the picture slides down (CapCut's y points up)
        y0, y1 = e, -e
    elif m == "pan-down":
        y0, y1 = -e, e
    mv = {"scale": [round(s0, 4), round(s1, 4)], "x": [x0, x1], "y": [y0, y1]}
    for k in ("scale", "x", "y"):
        if isinstance(r.get(k), (list, tuple)) and len(r[k]) == 2:
            mv[k] = [round(float(r[k][0]), 4), round(float(r[k][1]), 4)]
    mv["edge_shows"] = any(abs(mv["x"][i]) > mv["scale"][i] - 1 + 1e-6 or abs(mv["y"][i]) > mv["scale"][i] - 1 + 1e-6 for i in (0, 1))
    return mv


# --------------------------------------------------------------------------- command line

def main():
    ap = argparse.ArgumentParser(prog="capcut_tools.py", description=__doc__.split("\n\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("capcut-name", help="a free CapCut project name: DD_Mon_YYYY_vNN (-2, -3 when the folder exists)")
    p.add_argument("--video", required=True, help="the video's number")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)"); p.add_argument("--store", help="CapCut drafts dir")
    p.set_defaults(fn=cmd_capcut_name)

    p = sp.add_parser("capcut-prep", help="right after capcut_clone_draft (empty:true) and before any other call on the draft: "
                                          "set the template's identity aside, set the canvas")
    p.add_argument("--draft", required=True, help="the freshly cloned draft folder")
    p.add_argument("--canvas", help="WxH: the project's canvas (default: the template's)")
    p.set_defaults(fn=cmd_capcut_prep)

    p = sp.add_parser("capcut-repair", help="after the last capcut_save: register, the media links CapCut 9.7 opens clips by, "
                                            "sync-timelines, lint (under the machine-wide store lock); every text stays as it is")
    p.add_argument("--draft", required=True)
    p.add_argument("--keep-text", action="store_true", default=True, help="always on")
    p.add_argument("--preview", help="also render capcut-cli's low-resolution proxy to this .mp4 (a proxy, never an export)")
    p.set_defaults(fn=cmd_capcut_repair)

    p = sp.add_parser("capcut-font", help="--list the fonts on this PC (CapCut's own first) | set one font file on a draft's texts "
                                          "(and list font_missing_glyphs)")
    p.add_argument("--list", action="store_true", help="list the font files (family, style, file, source)")
    p.add_argument("--family", help="list: only families containing this")
    p.add_argument("--draft", help="the CapCut draft folder"); p.add_argument("--font-file", help="the font file (from --list)")
    p.add_argument("--track", help="only the texts on the track with this name")
    p.set_defaults(fn=cmd_capcut_font)

    p = sp.add_parser("capcut-motion", help="each image's move as keyframes CapCut 9.x plays (KFTypeScaleX with uniform scale, "
                                            "KFTypePositionX/Y), after the last capcut_save")
    p.add_argument("--draft", required=True)
    p.add_argument("--timeline", required=True, help="the images file: {'fps': 30, 'images': [{'image': 1, 'start': 0.0, 'motion': 'zoom-in'}]}")
    p.set_defaults(fn=cmd_capcut_motion, run=None)

    p = sp.add_parser("capcut-transitions", help="the images file's joins as CapCut's own transitions (capcut-cli, verified catalogue)")
    p.add_argument("--draft", required=True)
    p.add_argument("--timeline", required=True, help="the images file (a row's transition and trans_s)")
    p.set_defaults(fn=cmd_capcut_transitions, run=None)

    p = sp.add_parser("capcut-text-anim", help="one CapCut text animation (capcut-cli's catalogue) on every text of a track")
    p.add_argument("--draft", required=True); p.add_argument("--track", help="a text track's name; default: every text track")
    p.add_argument("--intro", help="a slug from `capcut enums --text-intros`, e.g. pop-up"); p.add_argument("--outro")
    p.add_argument("--intro-duration", type=float, default=0.5, help="seconds, capped at each text's own length")
    p.add_argument("--outro-duration", type=float, default=0.5)
    p.set_defaults(fn=cmd_capcut_text_anim, run=None)

    a = ap.parse_args()
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
