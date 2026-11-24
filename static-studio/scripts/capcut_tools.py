#!/usr/bin/env python3
"""capcut_tools.py - write and repair the CapCut project of a Static Studio video on this PC.

One command per call; every call prints one JSON object on its last line (exit 0 ok, 1 a step failed, 2 refused, 3 CapCut is running).
Commands: capcut-name | capcut-prep | capcut-build | capcut-repair | capcut-motion | capcut-transitions | capcut-font | capcut-text-anim.
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
    capcut-repair names it, but nothing here turns it on);
  * capcut-repair has two steps of this toolkit's own, added 2026-11-22 and not in the source: `audio-materials` before register
    (_audio_materials: every audio clip in CapCut's own form, type "extract_music"; the MCP writes "audio", which CapCut 9.x drops
    on open, so every audio track showed empty) and `photo-durations` after it (_photo_durations: CapCut's 3-hour duration on a
    still the MCP saved with none). A re-copy must add both back: AudioMaterialTests and PhotoDurationTests fail until it does.
Nothing else was changed; apart from those two steps, the CapCut logic is theirs.

capcut-build (2026-11-24, with scripts/capcut_build.mjs) is this toolkit's own and copies nothing: it writes the whole project of
one video from the run's decided files through the CapCut MCP's own library (config.json -> capcut.mcp_core), then runs
capcut-motion and capcut-transitions on it.
"""

import argparse
from pathlib import Path
import datetime as dt
import hashlib
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


AUDIO_TYPES = {"extract_music", "music", "sound", "record", "text_to_audio", "video_original_sound"}


def _audio_materials(d: Path) -> dict:
    """An audio clip CapCut can show: its material in CapCut's own form for a local file (type "extract_music", named after
    its file, category "local"), as capcut-cli writes it. Found 2026-11-22: the MCP's capcut_add_audio writes type "audio",
    which CapCut 9.x does not know: on open it rewrote the type to "none" and showed every audio track empty (no narration,
    no music). Only audio materials of a type CapCut does not know are changed; everything else stays as it is."""
    files, total = [], 0
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        n = 0
        for m in content.get("materials", {}).get("audios") or []:
            path = m.get("path")
            if not isinstance(path, str) or not path or re.match(r"(?i)^https?://", path):
                continue
            if m.get("type") not in AUDIO_TYPES:
                m["type"] = "extract_music"
                n += 1
            if not m.get("name"):
                m["name"] = Path(path).name
                n += 1
            if not m.get("category_name"):
                m["category_name"] = "local"
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".audio.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "fixed": n})
        total += n
    return {"fixed": total, "files": files}


def cmd_capcut_repair(a):
    """After every capcut_save: the house text style on every text layer (capcut-text-style), then
    `capcut register --apply --materials` (identity from draft_content.json,
    the media list CapCut needs, the store index), CapCut's own form for every audio material (_audio_materials, before
    register), CapCut's duration on every still added without one (_photo_durations), the media
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
        for name, args in (("audio-materials", None),
                           ("register", ["register", str(d), "--apply", "--materials"]),
                           ("photo-durations", None),
                           ("link", None),
                           ("sync-timelines", ["sync-timelines", str(d), "--nested", "--apply"]),
                           ("lint", ["lint", str(d)])):
            if args is None:   # still durations, then the media links CapCut 9.3+ opens a clip by, from the entries register just wrote
                try:
                    fix = {"audio-materials": _audio_materials, "photo-durations": _photo_durations}.get(name, _link_local_materials)
                    steps.append({"step": name, "exit": 0, "result": fix(d)})
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
    ok = (codes.get("audio-materials") == 0 and codes.get("register") == 0 and codes.get("photo-durations") == 0
          and codes.get("link") == 0
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


STORE_WRITERS = ("capcut-prep", "capcut-build", "capcut-repair", "capcut-font", "capcut-motion", "capcut-transitions",
                 "capcut-text-anim")


def _gpu_lease():
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import gpu_lease
    return gpu_lease


def _store_users() -> list:
    """Others using CapCut's shared project store now (another pipeline's builds and GUI exports, in the PC's shared lease
    folder): a project written meanwhile could lose their entry in CapCut's project list, or show CapCut a half-written
    one."""
    try:
        return _gpu_lease().capcut_store_users()
    except Exception:  # noqa: BLE001 - no shared folder, nobody to coordinate with
        return []


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


# --------------------------------------------------------------------------- capcut-build: the whole project in one command
#
# This toolkit's own (2026-11-24), not copied from the other toolkit. It replaces the per-run build scripts of the first
# production (one MCP call per picture and sound, or a script in the run folder that called the MCP's library): the run's
# decided files become one checked build plan, written into the draft in one Node process through the CapCut MCP's own
# library (scripts/capcut_build.mjs), then capcut-motion and capcut-transitions run on the same draft.

CAPCUT_BUILD_VERSION = "1 (2026-11-24)"
BUILD_MJS = Path(__file__).resolve().parent / "capcut_build.mjs"
YOUTUBE_CANVASES = ("1920x1080", "2560x1440", "3840x2160")     # the canvases timeline-check accepts (YouTube 16:9)
BUILD_BED_KINDS = ("music", "ambience", "bed")                  # the kinds timeline-check reads as the bed under a held silence
END_SLACK_S = 0.05                                              # rounding a sound may end after the last picture, or past its file
_SHA = {}


def _sha256_file(p) -> str:
    """A file's sha256, read once per version of it (its size and time)."""
    p = Path(p)
    st = p.stat()
    key = (os.path.normcase(str(p.resolve())), st.st_size, st.st_mtime_ns)
    if key not in _SHA:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _SHA[key] = h.hexdigest()
    return _SHA[key]


def _pkey(path) -> str:
    """One spelling per file, whichever tool wrote the path (as static_core.py keys its media records)."""
    return os.path.normcase(str(Path(str(path)).expanduser().resolve()))


def _true_path(p) -> Path:
    """The file's own spelling on disk (a record may keep a path in lower case): what the project shows."""
    return Path(os.path.realpath(str(p)))


def _read_json_or_none(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _in_run(rd: Path, f) -> Path:
    """A path a run file gives: absolute as written, else relative to the run folder."""
    p = Path(str(f or "")).expanduser()
    return p if p.is_absolute() else rd / p


def _media_seconds(p):
    """A media file's length as ffprobe reads it (the reading core.js gives a clip its length from), or None."""
    try:
        cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)], timeout=120)
        v = float((cp.stdout or "").strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None
    return v if v == v and v > 0 else None


def _draw_tool():
    """The drawing renderer (draw_tool.py beside this file), for its render records: importing it imports no Pillow."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import draw_tool
    return draw_tool


def _capcut_cli_path():
    """capcut-cli's executable, or None (_capcut_cli fails instead)."""
    exe = shutil.which("capcut")
    if exe:
        return exe
    cand = os.path.join(os.environ.get("APPDATA", ""), "npm", "capcut.cmd")
    return cand if os.path.exists(cand) else None


def _lanes(rows: list, name) -> None:
    """Each clip on the first track of its kind where it overlaps nothing (name(0), name(1), ...): one track never holds two
    clips at once (capcut_validate refuses that). Sorts the rows by their start and writes row["track"]: a mechanical packing."""
    rows.sort(key=lambda x: (x["at_us"], str(x.get("id") or "")))
    ends = []
    for r in rows:
        k = next((i for i, e in enumerate(ends) if r["at_us"] >= e), None)
        if k is None:
            ends.append(0)
            k = len(ends) - 1
        ends[k] = r["at_us"] + r["dur_us"]
        r["track"] = name(k)


def _bed_at_silences(pauses, spans) -> list:
    """What the planned beds do at each held silence, read by timeline-check's own rule (2026-11-24): enters, stops, continues
    (dips and swells need a bed across it), none. A forecast for the agent; timeline-check decides on the built project."""
    rows = []
    for p in pauses or []:
        bed, tm = ((p or {}).get("transition") or {}).get("bed"), (p or {}).get("times_in_edit") or {}
        if not bed or tm.get("silence_from_s") is None or tm.get("silence_to_s") is None:
            continue
        a, b = float(tm["silence_from_s"]), float(tm["silence_to_s"])
        nxt = float(tm.get("next_line_s") or b)
        covers = any(s <= a + 0.05 and e >= b - 0.05 for s, e in spans)
        under = any(s < b - 0.2 and e > a + 0.2 for s, e in spans)
        ok = {"enters": any(a - 0.5 <= s <= nxt + 0.5 for s, _ in spans), "stops": any(a - 0.5 <= e <= nxt + 0.5 for _, e in spans),
              "continues": covers, "none": not under, "dips": covers, "swells": covers}.get(str(bed))
        rows.append({"after_line": p.get("after_line"), "silence_from_s": a, "silence_to_s": b, "bed": bed, "as_decided": ok})
    return rows


def _capcut_build_plan(rd: Path, n: int, a) -> tuple:
    """Everything one video's CapCut project holds, from the run's decided files only (manual 09, "capcut-build"):
    (plan, problems, warnings). A problem is an input missing or unreadable, a file changed since its record was written, or two
    decided files that disagree on a fact (a time, a shot, a beat); any problem refuses the build. A warning is a fact for the
    agent. Nothing here chooses a time, a file, a move, a level or a bed: each comes from the file named beside it."""
    problems, warnings, inputs = [], [], []
    edit, vis = rd / "70-edit" / f"video-{n:02d}", rd / "60-visuals" / f"video-{n:02d}"

    def note_input(role, p, **extra):
        inputs.append({"role": role, "file": str(p), "sha256": _sha256_file(p), **extra})

    ep_path = edit / "edit-plan.json"
    ep = _read_json_or_none(ep_path) if ep_path.is_file() else None
    if not isinstance(ep, dict):
        return None, [f"no readable edit plan at {ep_path} (static_core.py retime-shots writes it)"], warnings
    note_input("edit_plan", ep_path)

    # the shots, as retime-shots timed them to the real narration and its decided holds
    shots = sorted((s for s in ep.get("shots") or [] if isinstance(s, dict)), key=lambda s: float(s.get("start_s") or 0))
    if not shots:
        problems.append("the edit plan has no shots")
    rows, prev = [], None
    for k, s in enumerate(shots, 1):
        sid = str(s.get("id") or "").strip()
        try:
            a0, b0 = float(s["start_s"]), float(s["end_s"])
        except (KeyError, TypeError, ValueError):
            problems.append(f"edit plan shot {sid or k}: no start_s and end_s (run retime-shots)")
            continue
        if not sid:
            problems.append(f"edit plan shot {k}: no id")
        at_us, end_us = round(a0 * 1e6), round(b0 * 1e6)
        if end_us <= at_us:
            problems.append(f"{sid}: it ends at {b0} s, not after its start at {a0} s")
        if prev is not None:
            if at_us < prev[1]:
                problems.append(f"{sid} starts at {a0} s, before {prev[0]} ends at {prev[1] / 1e6} s")
            elif at_us - prev[1] > 17000:
                warnings.append(f"{at_us / 1e6 - prev[1] / 1e6:.3f} s of nothing between {prev[0]} and {sid}: the picture is black there")
        elif at_us > 17000:
            warnings.append(f"the first shot {sid} starts at {a0} s: the picture is black before it")
        prev = (sid, end_us)
        rows.append({"image": k, "shot_id": sid, "beat_id": s.get("beat_id"), "at": a0, "end": b0, "at_us": at_us,
                     "dur_us": end_us - at_us})
    by_shot = {r["shot_id"]: r for r in rows}
    last_end_us = max((r["at_us"] + r["dur_us"] for r in rows), default=0)
    beat_ids = {str(b.get("id")) for b in ep.get("beats") or [] if isinstance(b, dict) and b.get("id")}
    beat_spans = {str(b.get("id")): (float(b.get("start_s") or 0), float(b.get("end_s") or 0))
                  for b in ep.get("beats") or [] if isinstance(b, dict) and b.get("id")}

    # each shot's still: stills/<the shot, or the shot it reuses>.png, the file timeline-write traces it to, as its record has it
    sp_path = vis / "shot-plan.json"
    sp = _read_json_or_none(sp_path) if sp_path.is_file() else None
    if not isinstance(sp, dict):
        problems.append(f"no readable shot plan at {sp_path} (it says which shot a callback reuses)")
        sp = {}
    else:
        note_input("shot_plan", sp_path)
    reuse = {str(s.get("id")): str(s.get("reuses")) for s in sp.get("shots") or [] if isinstance(s, dict) and s.get("reuses")}
    prov_path = vis / "stills-provenance.json"
    prov = (_read_json_or_none(prov_path) or {}).get("images") or {} if prov_path.is_file() else {}
    if prov_path.is_file():
        note_input("stills_record", prov_path)
    else:
        warnings.append(f"no stills record ({prov_path}): no still can be checked against the file the generator made")
    recs = {_pkey(k): v for k, v in prov.items() if isinstance(v, dict)}
    newest = {}
    for k, v in prov.items():
        if isinstance(v, dict) and Path(k).is_file():
            sid0 = str(v.get("shot_id"))
            if str(v.get("made_at") or "") >= newest.get(sid0, ("", ""))[0]:
                newest[sid0] = (str(v.get("made_at") or ""), k)
    images, unrecorded = [], []
    for r in rows:
        sid = r["shot_id"]
        src = reuse.get(sid) or sid
        f = vis / "stills" / f"{src}.png"
        if not f.is_file():
            problems.append(f"{sid}: its still {f} is missing" + (f" (it reuses {src}'s)" if src != sid else ""))
            continue
        f = _true_path(f)
        sha = _sha256_file(f)
        rec = recs.get(_pkey(f))
        if rec is None:
            unrecorded.append(f.name)
        else:
            if str(rec.get("shot_id")) != src:
                problems.append(f"{sid}: {f.name} was made for shot {rec.get('shot_id')}, not {src} (stills-provenance.json)")
            if rec.get("file_sha256") and rec["file_sha256"] != sha:
                problems.append(f"{sid}: {f.name} changed after the generator made it (its sha256 differs from stills-provenance.json)")
        nw = newest.get(src)
        if nw and _pkey(nw[1]) != _pkey(f):
            warnings.append(f"{sid}: the newest still recorded for {src} is {nw[1]}; the project shows {f} (timeline-write traces "
                            "stills/<shot>.png)")
        images.append({**r, "file": f.as_posix(), "sha256": sha, "dur": round(r["dur_us"] / 1e6, 6)})
    if unrecorded:
        warnings.append(f"{len(unrecorded)} still(s) without a stills-provenance record (" + ", ".join(sorted(set(unrecorded))[:8])
                        + "): timeline-check needs a record, or the stills reapproved on record")

    # the narration: the one file the edit plan names, unchanged since retime-shots, at 0 s, speed 1, whole
    narration = None
    nfe = ep.get("narration_for_edit") or {}
    if not nfe.get("file") or not nfe.get("sha256"):
        problems.append("the edit plan names no narration_for_edit file with its sha256 (run retime-shots again)")
    else:
        nf = _in_run(rd, nfe["file"])
        if not nf.is_file():
            problems.append(f"the narration the edit plan names is missing: {nf}")
        else:
            nf = _true_path(nf)
            sha = _sha256_file(nf)
            if sha != nfe["sha256"]:
                problems.append(f"the narration {nf.name} changed since retime-shots: its sha256 differs from edit-plan.json's "
                                "narration_for_edit (run retime-shots again, or bring back the approved file)")
            dur = _media_seconds(nf)
            if dur is None:
                problems.append(f"ffprobe could not read the narration's length: {nf}")
            else:
                narration = {"file": nf.as_posix(), "sha256": sha, "at": 0.0, "at_us": 0, "dur": dur, "dur_us": round(dur * 1e6),
                             "src_start_us": 0, "speed": 1.0, "volume": 1.0}
                if nfe.get("duration_s") and abs(dur - float(nfe["duration_s"])) > 0.02:
                    warnings.append(f"the narration lasts {dur:.3f} s, the edit plan says {float(nfe['duration_s']):.3f} s")
                if rows and abs(last_end_us / 1e6 - dur) > 0.5:
                    warnings.append(f"the pictures end at {last_end_us / 1e6:.3f} s, the narration at {dur:.3f} s")
                inputs.append({"role": "narration", "file": nf.as_posix(), "sha256": sha})

    # the moves and joins: the images file the agent wrote (manual 09, "The images file")
    moves, row_motion = None, {}
    if getattr(a, "no_moves", False):
        if getattr(a, "images", None):
            problems.append("--images and --no-moves contradict each other")
        elif (edit / "capcut-images.json").is_file():
            warnings.append(f"--no-moves: {edit / 'capcut-images.json'} is there and is not used (every still holds, every join a cut)")
    else:
        mp = Path(a.images).expanduser() if getattr(a, "images", None) else edit / "capcut-images.json"
        data = _read_json_or_none(mp) if mp.is_file() else None
        if not mp.is_file():
            problems.append(f"no images file (each still's move and join): {mp}; write it (manual 09, \"The images file\"), or pass "
                            "--no-moves when every still holds and every join is a cut")
        elif not isinstance(data, dict) or not isinstance(data.get("images"), list):
            problems.append(f"the images file is not {{\"fps\": 30, \"images\": [...]}}: {mp}")
        else:
            note_input("images_file", mp)
            fps = int(data.get("fps") or 30)
            half, pro_ok = 0.5 / fps, _capcut_pro_ok(rd)
            joins, moved, last, rws = [], 0, 0, data["images"]
            for j, r in enumerate(rws, 1):
                if not isinstance(r, dict) or any(x not in r for x in ("image", "start", "motion")):
                    problems.append(f"images file row {j}: every row needs image, start and motion")
                    continue
                try:
                    k, t = int(r["image"]), float(r["start"])
                except (TypeError, ValueError):
                    problems.append(f"images file row {j}: image is a whole number and start a number of seconds")
                    continue
                if k <= last:
                    problems.append(f"images file row {j}: image {k} comes after image {last} (the rows go in clip order)")
                last = max(last, k)
                if not 1 <= k <= len(rows):
                    problems.append(f"images file row {j}: image {k}, but the edit plan has {len(rows)} shots")
                    continue
                s = rows[k - 1]
                if abs(t - s["at"]) > half:
                    problems.append(f"images file: image {k} starts at {t} s, its clip ({s['shot_id']}) at {s['at']} s: the file was "
                                    "written for another timing (write it again from the current edit plan)")
                if r.get("shot_id") and str(r["shot_id"]) != s["shot_id"]:
                    problems.append(f"images file: image {k} names {r['shot_id']}, the clip number {k} is {s['shot_id']}")
                slug = str(r.get("transition") or "cut")
                if slug != "cut":
                    before = rws[j - 2] if j > 1 and isinstance(rws[j - 2], dict) else {}
                    if k == 1:
                        problems.append(f"images file: image 1 has a transition ({slug}), but no clip comes before it")
                    elif str(before.get("image")) != str(k - 1):
                        problems.append(f"images file: the transition into image {k} needs the row of image {k - 1} just before it "
                                        "(capcut-transitions puts it on the clip before, found by that row's start)")
                    why = _catalogue_refusal("transition", slug, pro_ok)
                    if why:
                        problems.append(f"images file: image {k}: {why}")
                    joins.append({"into_image": k, "into_shot": s["shot_id"], "at_s": s["at"], "transition": slug,
                                  "trans_s": float(r.get("trans_s") or 0.5)})
                if any(q in r for q in ("scale", "x", "y")) and not all(
                        isinstance(r.get(q), (list, tuple)) and len(r[q]) == 2 for q in ("scale", "x", "y")):
                    problems.append(f"images file: image {k}: scale, x and y go together, each as [at the start, at the end]")
                    continue
                mv = _still_motion(r)
                if mv["edge_shows"]:
                    warnings.append(f"images file: image {k} ({s['shot_id']}): an edge of the picture would show "
                                    f"(scale {mv['scale']}, x {mv['x']}, y {mv['y']})")
                if mv["scale"] != [1.0, 1.0] or mv["x"] != [0.0, 0.0] or mv["y"] != [0.0, 0.0]:
                    moved += 1
                row_motion[s["shot_id"]] = mv
            moves = {"file": str(mp), "sha256": _sha256_file(mp), "fps": fps, "rows": len(rws), "moved": moved, "transitions": joins}

    # the drawn overlays: every rendered DNN.mov in the drawings folder, placed on the shot its spec (DNN.json) names, from
    # that still's start for as long as it lasts (manual 04: the drawing clip starts with its still and lasts as long)
    overlays = []
    ddir = Path(a.drawings).expanduser() if getattr(a, "drawings", None) else vis / "drawings"
    if getattr(a, "no_drawings", False):
        if getattr(a, "drawings", None):
            problems.append("--drawings and --no-drawings contradict each other")
        elif ddir.is_dir() and any(ddir.glob("*.mov")):
            warnings.append(f"--no-drawings: the drawings in {ddir} are not placed")
    elif getattr(a, "drawings", None) and not ddir.is_dir():
        problems.append(f"no drawings folder at {ddir}")
    elif ddir.is_dir():
        unrecorded_drawings = []
        for mov in sorted(ddir.glob("*.mov")):
            spec_p = mov.with_suffix(".json")
            spec = _read_json_or_none(spec_p) if spec_p.is_file() else None
            if not isinstance(spec, dict) or not spec.get("elements"):
                problems.append(f"{mov.name}: no drawing spec beside it ({spec_p.name}), so the shot it is drawn on is unknown "
                                "(a drawing left out of the cut is moved out of the folder)")
                continue
            sid = str(spec.get("shot") or "").strip()
            if not sid:
                problems.append(f"{spec_p.name} names no shot (\"shot\": the shot whose still it is drawn on)")
                continue
            s = by_shot.get(sid)
            if s is None:
                problems.append(f"{spec_p.name} is drawn on shot {sid}, which the edit plan does not have (move it out of "
                                f"{ddir.name}/ or name its shot)")
                continue
            rstatus = _draw_tool().render_status(spec_p, mov, next((im["file"] for im in images if im["shot_id"] == sid),
                                                                   None))
            unvouched = [r for r in rstatus["reasons"] if r["code"] in ("no_record", "still_not_recorded")]
            stale = [r for r in rstatus["reasons"] if r not in unvouched]
            if stale:
                problems.append(f"{mov.name} is not the render of {spec_p.name} and its still as they are now: "
                                + "; ".join(r["detail"] for r in stale) + " (render it again: draw_tool.py render)")
            elif unvouched:
                unrecorded_drawings.append(mov.stem)
            secs = _media_seconds(mov)
            if secs is None:
                problems.append(f"ffprobe could not read {mov}")
                continue
            frame, shot_s = 1.0 / float((moves or {}).get("fps") or 30), s["dur_us"] / 1e6
            if secs < shot_s - frame:
                warnings.append(f"{mov.stem} lasts {secs:.2f} s and its shot {sid} {shot_s:.2f} s: it leaves the still "
                                f"{shot_s - secs:.2f} s before the cut (render it for the shot's length)")
            elif secs > shot_s + frame:
                warnings.append(f"{mov.stem} lasts {secs:.2f} s and its shot {sid} {shot_s:.2f} s: its last "
                                f"{secs - shot_s:.2f} s are cut at the shot's end")
            sm = spec.get("still_motion")
            mv = row_motion.get(sid)
            if isinstance(sm, dict) and sm.get("scale"):
                smd = float(sm.get("dur_s") or spec.get("dur_s") or 0)
                if abs(smd - shot_s) > frame:
                    warnings.append(f"{spec_p.name} follows its still's move over {smd:.2f} s, the shot lasts {shot_s:.2f} s: the "
                                    "drawing drifts off what it marks (render it again for the current timing)")
                if mv is not None:
                    pairs = [[round(float(x), 4) for x in (sm.get(key) or [default, default])] for key, default in
                             (("scale", 1.0), ("x", 0.0), ("y", 0.0))]
                    if any(abs(p - q) > 1e-3 for got, want in zip(pairs, (mv["scale"], mv["x"], mv["y"])) for p, q in zip(got, want)):
                        warnings.append(f"{spec_p.name}'s still_motion differs from the images file's move for {sid}: the drawing "
                                        "would not stay on what it marks")
            elif mv is not None and (mv["scale"][0] != mv["scale"][1] or mv["x"][0] != mv["x"][1] or mv["y"][0] != mv["y"][1]) \
                    and not isinstance(spec.get("still_framing"), dict):
                warnings.append(f"{sid} moves under {mov.stem}, whose spec does not follow the move (no still_motion)")
            f = _true_path(mov)
            overlays.append({"id": mov.stem, "shot_id": sid, "file": f.as_posix(), "sha256": _sha256_file(f), "spec": str(spec_p),
                             "spec_sha256": _sha256_file(spec_p), "at": s["at"], "at_us": s["at_us"], "dur": round(min(shot_s, secs), 6),
                             "dur_us": min(s["dur_us"], round(secs * 1e6))})
        if unrecorded_drawings:
            warnings.append(f"{len(unrecorded_drawings)} drawing(s) without a render record that vouches for their spec "
                            "and still (" + ", ".join(unrecorded_drawings[:8]) + (", ..." if len(unrecorded_drawings) > 8
                                                                                   else "")
                            + "): rendered before render records, so a stale one cannot be told; render them again "
                              "to have them checked")
        _lanes(overlays, lambda k: f"draw{k + 1}")

    # the beds and the sound effects, as decided (the sound placements file: manual 09)
    beds, sfx, sound_names = [], [], {}
    music_prov_path = edit / "music-provenance.json"
    music = (_read_json_or_none(music_prov_path) or {}).get("tracks") or {} if music_prov_path.is_file() else {}
    music = {_pkey(k): v for k, v in music.items() if isinstance(v, dict)}
    if music_prov_path.is_file():
        note_input("music_record", music_prov_path)
    if getattr(a, "no_sounds", False):
        if getattr(a, "sound_placements", None):
            problems.append("--sound-placements and --no-sounds contradict each other")
        elif (edit / "sound-placements.json").is_file():
            warnings.append(f"--no-sounds: {edit / 'sound-placements.json'} is there and is not used")
        if music:
            warnings.append("music was made for this video (music-provenance.json) and --no-sounds places none")
    else:
        spp = Path(a.sound_placements).expanduser() if getattr(a, "sound_placements", None) else edit / "sound-placements.json"
        data = _read_json_or_none(spp) if spp.is_file() else None
        if not spp.is_file():
            problems.append(f"no sound placements file (the beds and sound effects as decided): {spp}; write it (manual 09, \"The "
                            "sound placements file\"), or pass --no-sounds when the edit has no bed and no sound effect")
        elif not isinstance(data, dict) or not any(isinstance(data.get(k2), list) for k2 in ("beds", "sfx")):
            problems.append(f"the sound placements file holds no \"beds\" or \"sfx\" list: {spp}")
        else:
            note_input("sound_placements", spp)
            anchored = any(isinstance(x, dict) and any(str(k2).endswith("_anchor") for k2 in x)
                           for k2 in ("beds", "sfx") for x in data.get(k2) or [])
            try:
                made = dt.datetime.fromisoformat(str(ep.get("made_at") or "").replace("Z", "+00:00")).timestamp()
            except ValueError:
                made = None
            if anchored and made and spp.stat().st_mtime < made:
                warnings.append("the edit plan was retimed after the sound placements were last written: run sound-anchors --resolve "
                                "on them (--list beds, then --list sfx) before the build")
            for key, out_rows in (("beds", beds), ("sfx", sfx)):
                for j, it in enumerate(data.get(key) or [], 1):
                    label = f"{key}[{j}]" + (f" {it.get('id')}" if isinstance(it, dict) and it.get("id") else "")
                    if not isinstance(it, dict):
                        problems.append(f"{label}: not an object")
                        continue
                    f = _in_run(rd, it.get("file"))
                    if not it.get("file") or not f.is_file():
                        problems.append(f"{label}: its file is missing: {f}")
                        continue
                    f = _true_path(f)
                    sha = _sha256_file(f)
                    if it.get("sha256") and it["sha256"] != sha:
                        problems.append(f"{label}: {f.name} changed since the placements recorded it (sha256)")
                    try:
                        at = float(it["at"])
                        src = float(it.get("src_start") or 0.0)
                        vol = float(it["volume"]) if it.get("volume") is not None else 1.0
                        fin, fout = float(it.get("fade_in") or 0.0), float(it.get("fade_out") or 0.0)
                        end = float(it["end"]) if it.get("end") is not None else None
                    except (KeyError, TypeError, ValueError):
                        problems.append(f"{label}: at (seconds on the edit's clock) is needed; src_start, end, volume, fade_in and "
                                        "fade_out are numbers when given")
                        continue
                    secs = _media_seconds(f)
                    if secs is None:
                        problems.append(f"{label}: ffprobe could not read {f}")
                        continue
                    room = secs - src
                    dur = (end - at) if end is not None else room
                    bad = []
                    if at < 0 or src < 0:
                        bad.append("at and src_start are 0 or more")
                    if room <= 0:
                        bad.append(f"src_start {src} s is past the file's end ({secs:.3f} s)")
                    elif dur <= 0:
                        bad.append(f"it ends at {end} s, not after its start at {at} s")
                    elif dur > room + END_SLACK_S:
                        bad.append(f"it lasts {dur:.3f} s from {src} s into its file, which holds {room:.3f} s from there")
                    if vol <= 0:
                        bad.append("volume is more than 0 (a muted clip is no placement)")
                    if fin < 0 or fout < 0 or (dur > 0 and fin + fout > dur + 1e-6):
                        bad.append("fade_in and fade_out are 0 or more and fit inside the clip")
                    beats = [str(x) for x in it.get("beats") or []]
                    if not beats:
                        bad.append("beats names the beats it serves (timeline-check needs them)")
                    elif beat_ids and any(x not in beat_ids for x in beats):
                        bad.append("beats names a beat the edit plan does not have: " + ",".join(x for x in beats if x not in beat_ids))
                    kind = str(it.get("kind") or ("music" if key == "beds" else "sfx"))
                    if key == "beds" and kind not in BUILD_BED_KINDS:
                        bad.append(f"a bed's kind is one of {', '.join(BUILD_BED_KINDS)}")
                    if bad:
                        problems += [f"{label}: {b}" for b in bad]
                        continue
                    dur = min(dur, room)
                    at_us, dur_us = round(at * 1e6), round(dur * 1e6)
                    if rows and at_us + dur_us > last_end_us + END_SLACK_S * 1e6:
                        problems.append(f"{label}: it ends at {(at_us + dur_us) / 1e6:.3f} s, after the last picture ({last_end_us / 1e6:.3f} s): "
                                        "the export would end on black (end it with the picture, or hold the last shot longer)")
                        continue
                    if beat_spans and not any(x in beat_spans and at < beat_spans[x][1] and at + dur > beat_spans[x][0] for x in beats):
                        warnings.append(f"{label} plays at {at:.2f}-{at + dur:.2f} s, outside the beats it names ({','.join(beats)})")
                    if abs(vol - 1.0) > 1e-9:
                        warnings.append(f"{label}: volume {vol:g} on the clip: CapCut's export was measured ignoring a clip's volume "
                                        "(2026-11-22, a video clip); a level baked into the file (bed-levels --bake) plays as made")
                    rec = music.get(_pkey(f))
                    if key == "beds":
                        if rec is None:
                            warnings.append(f"{label}: {f.name} has no music-provenance record (timeline-check needs one, or the music "
                                            "reapproved on record)")
                        elif sorted(rec.get("beats") or []) != sorted(beats):
                            warnings.append(f"{label}: its record names beats {','.join(rec.get('beats') or [])}; timeline-write takes "
                                            "a recorded bed's beats from there")
                    if key == "sfx" or rec is None:
                        nm = f.name
                        if nm.lower() in {x.lower() for x in sound_names} and sound_names.get(nm, {}).get("_file") != str(f):
                            problems.append(f"{label}: another sound file is also named {nm}: timeline-write tells sounds apart by "
                                            "their file names")
                        sound_names[nm] = {"kind": kind, "beats": beats, "purpose": str(it.get("purpose") or it.get("why") or ""),
                                           "_file": str(f)}
                    out_rows.append({"id": str(it.get("id") or f.stem), "kind": kind, "file": f.as_posix(), "sha256": sha,
                                     "at": at, "at_us": at_us, "dur": round(dur, 6), "dur_us": dur_us, "src_start": src,
                                     "src_start_us": round(src * 1e6), "volume": vol, "fade_in_us": round(fin * 1e6),
                                     "fade_out_us": round(fout * 1e6), "beats": beats,
                                     "purpose": str(it.get("purpose") or it.get("why") or ""), "recorded_music": rec is not None})
            _lanes(beds, lambda k: "music" if k == 0 else f"music-{k + 1}")
            _lanes(sfx, lambda k: "sfx" if k == 0 else f"sfx-{k + 1}")
            if music and not beds:
                warnings.append("music was made for this video (music-provenance.json) and the placements place no bed")

    held = _bed_at_silences(ep.get("pauses"), [(b["at"], b["at"] + b["dur"]) for b in beds if b["kind"] in BUILD_BED_KINDS])
    for h in held:
        if h["as_decided"] is False:
            warnings.append(f"the silence after {h['after_line']} ({h['silence_from_s']:.2f}-{h['silence_to_s']:.2f} s) was decided "
                            f"with the bed \"{h['bed']}\"; the placed beds do not do that there (timeline-check reads the same)")
    for role, items in (("overlay", overlays), ("bed", beds), ("sfx", sfx)):
        inputs += [{"role": role, "id": o["id"], "file": o["file"], "sha256": o["sha256"]} for o in items]
    for im in images:
        inputs.append({"role": "still", "shot_id": im["shot_id"], "file": im["file"], "sha256": im["sha256"]})
    plan = {"made_by": "capcut_tools.py capcut-build", "version": CAPCUT_BUILD_VERSION, "made_at": now_iso(), "run": str(rd),
            "video": n, "edit_duration_s": ep.get("edit_duration_s"), "narration": narration, "images": images,
            "overlays": overlays, "beds": beds, "sfx": sfx, "moves": moves, "held_silences": held,
            "sounds_for_timeline_write": {k: {x: y for x, y in v.items() if x != "_file"} for k, v in sound_names.items()},
            "inputs": inputs, "warnings": warnings,
            "note": "Everything the project holds, from the run's decided files; capcut_build.mjs places exactly this. Times in "
                    "seconds on the edit's clock (*_us: the same in microseconds, as CapCut stores them)."}
    return plan, problems, warnings


def _capcut_build_draft_facts(d: Path) -> tuple:
    """Whether a draft is the fresh, prepared clone capcut-build may write: (problems, facts). It refuses the template, a
    project that already holds a clip, a clone capcut-prep has not prepared, one CapCut has opened, and a canvas that is not
    YouTube 16:9."""
    tmpl = str(cfg_get("capcut.template_draft") or "")
    facts = {"draft": str(d), "draft_name": d.name, "drafts_dir": str(d.parent), "template_draft": tmpl}
    cp = d / "draft_content.json"
    if not cp.is_file():
        return [f"not a CapCut draft (no draft_content.json): {d}"], facts
    problems = []
    if not tmpl:
        problems.append("config.json names no capcut.template_draft")
    elif d.name == tmpl or _pkey(d) == _pkey(_capcut_store() / tmpl):
        problems.append(f"{d} is the template draft every project is cloned from: it is never edited")
    elif not (d.parent / tmpl / "draft_content.json").is_file():
        problems.append(f"the template {tmpl!r} is not beside this draft in {d.parent}: core.js takes its clip templates from there "
                        "(build in the drafts folder capcut-name answered)")
    try:
        content = json.loads(cp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return problems + [f"draft_content.json is unreadable: {e}"], facts
    held = sum(len(t.get("segments") or []) for t in content.get("tracks") or [] if isinstance(t, dict))
    if held:
        problems.append(f"the draft already holds {held} clip(s): capcut-build writes only a fresh project (capcut-name, the "
                        "clone, capcut-prep, then capcut-build)")
    if content.get("name") and content.get("name") != d.name:
        problems.append(f"draft_content.json names {content.get('name')!r}, not this folder {d.name!r}: not the fresh clone")
    if (d / "draft_meta_info.json").exists():
        problems.append("capcut-prep has not run on this clone: draft_meta_info.json (the template's identity) is still in place")
    lay = _read_json_or_none(d / "timeline_layout.json") or {}
    ids = [i for it in lay.get("dockItems") or [] if isinstance(it, dict) for i in it.get("timelineIds") or []]
    if content.get("id") not in ids:
        problems.append("capcut-prep has not run on this clone: timeline_layout.json does not point at its timeline")
    if (d / "template-2.tmp").exists():
        problems.append("template-2.tmp is in the draft: it was opened in CapCut or copied, not cloned (capcut_clone_draft leaves "
                        "it out; capcut-cli would read it as the timeline): make a fresh project")
    cc = content.get("canvas_config") or {}
    facts["canvas"] = f"{cc.get('width')}x{cc.get('height')}"
    if facts["canvas"] not in YOUTUBE_CANVASES:
        problems.append(f"the canvas is {facts['canvas']}: run capcut-prep --canvas 1920x1080 on the fresh clone (a YouTube 16:9 "
                        "canvas: " + ", ".join(YOUTUBE_CANVASES) + ")")
    return problems, facts


def _mirror_timeline(d: Path) -> dict:
    """draft_info.json made the same timeline as draft_content.json, the mirror capcut-cli keeps identical when it exists: a fresh
    clone carries the template's, which capcut-motion would key as a stale copy and sync-timelines would find newer than the build."""
    src, dst = d / "draft_content.json", d / "draft_info.json"
    if not dst.is_file():
        return {"mirrored": False, "why": "the draft has no draft_info.json"}
    tmp = dst.with_name(dst.name + ".build-tmp")
    shutil.copyfile(src, tmp)
    _replace(tmp, dst)
    return {"mirrored": True, "file": str(dst)}


def _draft_tracks(d: Path) -> list:
    content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    return [{"index": i, "type": t.get("type"), "name": t.get("name"), "segments": len(t.get("segments") or []),
             "muted": bool(t.get("attribute"))} for i, t in enumerate(content.get("tracks") or [])]


def _build_next(rd: Path, n: int, d, sounds_file: Path) -> list:
    """The documented steps after the build (manual 09, "The order"), with this run's paths."""
    st = _read_json_or_none(rd / "state.json") or {}
    cap = str(st.get("captions") or "").lower()
    core = 'python "$HOME/.claude/static-studio/scripts/static_core.py"'
    tools = 'python "$HOME/.claude/static-studio/scripts/capcut_tools.py"'
    dr = f'"{d}"' if d else '"<project>"'
    steps = []
    if cap == "on":
        steps += [f'{core} captions-plan --run "{rd}" --video {n}   (if captions.json is not timed to this edit plan; the word box adds '
                  '--box-color and --box-color-why)',
                  f'{core} captions-build --run "{rd}" --video {n} --draft {dr}']
    elif cap != "off":
        steps.append(f'{core} captions-choice --run "{rd}" ...   (the user has not chosen the captions yet: ask once)')
    steps += [f"{tools} capcut-repair --draft {dr} --keep-text",
              f'{core} timeline-write --run "{rd}" --video {n} --draft {dr} --sounds "{sounds_file}"',
              f'{core} timeline-check --run "{rd}" --video {n}']
    return steps


def cmd_capcut_build(a):
    """The whole CapCut project of one video in one command (manual 09, "The order", step 4): the run's decided files (the edit
    plan with its shots, holds and narration_for_edit; each shot's still; the images file; the rendered drawings; the sound
    placements) become one checked build plan (RUN/70-edit/video-NN/capcut/build-plan.json); unless --dry-run, it is written
    into the fresh, prepared draft in one Node process through the CapCut MCP's own library (capcut_build.mjs, one save), then
    capcut-motion and capcut-transitions run on the same draft, and RUN/70-edit/video-NN/capcut/build-log.json records the draft,
    every input with its sha256, what each track holds and this toolkit's version. It decides nothing; an input missing or
    changed since its record refuses the build (exit 2, nothing written). CapCut closed; the machine-wide store lock is held while
    the draft is written; the template and every other project are never touched."""
    rd = resolve_run(a.run)
    try:
        n = int(a.video)
    except (TypeError, ValueError):
        fail("--video must be the video's number", 2)
    if not a.draft and not a.dry_run:
        fail("capcut-build needs --draft (the project folder capcut-name answered), or --dry-run", 2)
    d = Path(os.path.abspath(Path(a.draft).expanduser())) if a.draft else None
    if not shutil.which("ffprobe"):
        fail("ffprobe not found on PATH: the build reads each clip's length with it, as core.js does", 2)
    if d is not None and not a.dry_run and ((d / ".locked").exists() or _capcut_running()):
        fail("CapCut is running: close it, then run this again (nothing was changed)", 3)
    edit = rd / "70-edit" / f"video-{n:02d}"
    plan, problems, warnings = _capcut_build_plan(rd, n, a)
    facts = {}
    if d is not None:
        dp, facts = _capcut_build_draft_facts(d)
        problems += dp
        if a.dry_run and (d / ".locked").exists():
            warnings.append("the draft is open in CapCut (.locked): close it before the build")
    core = Path(str(cfg_get("capcut.mcp_core") or "")).expanduser()
    node = shutil.which("node")
    if not a.dry_run:
        if not node:
            problems.append("node not found on PATH: the build runs the CapCut MCP's own library in Node")
        if not cfg_get("capcut.mcp_core") or not core.is_file():
            problems.append(f"the CapCut MCP library is not at {core} (config.json -> capcut.mcp_core)")
        if not BUILD_MJS.is_file():
            problems.append(f"{BUILD_MJS} is missing (it sits next to capcut_tools.py)")
        if plan and plan.get("moves") and plan["moves"]["transitions"] and not _capcut_cli_path():
            problems.append("capcut-cli not found: capcut-transitions writes the joins with it (npm i -g capcut-cli)")
    if problems:
        out({"ok": False, "error": problems[0] + (f" (and {len(problems) - 1} more)" if len(problems) > 1 else ""),
             "problems": problems[:60], "problems_count": len(problems), "warnings": warnings[:20], "warnings_count": len(warnings),
             "note": "refused: nothing was written"}, 2)
    plan.update({k: facts.get(k) for k in ("draft", "draft_name", "drafts_dir", "template_draft", "canvas")})
    plan["dry_run"] = bool(a.dry_run)
    cdir = edit / "capcut"
    plan_path, sounds_file, log_path = cdir / "build-plan.json", cdir / "sounds.json", cdir / "build-log.json"
    write_json(plan_path, plan)
    write_json(sounds_file, plan["sounds_for_timeline_write"])
    counts = {"pictures": len(plan["images"]), "overlays": len(plan["overlays"]), "narration": 1 if plan["narration"] else 0,
              "beds": len(plan["beds"]), "sfx": len(plan["sfx"]),
              "moves": (plan["moves"] or {}).get("moved", 0), "transitions": len((plan["moves"] or {}).get("transitions") or [])}
    nxt = _build_next(rd, n, d, sounds_file)
    if a.dry_run:
        out({"ok": True, "dry_run": True, "build_plan": str(plan_path), "sounds_file": str(sounds_file), "draft": plan["draft"],
             "planned": counts, "warnings": warnings[:30], "warnings_count": len(warnings),
             "next": ([] if d else ["capcut-name, the clone (capcut_clone_draft, empty) and capcut-prep --canvas 1920x1080"])
             + [f'python "$HOME/.claude/static-studio/scripts/capcut_tools.py" capcut-build --run "{rd}" --video {n} --draft '
                + (f'"{d}"' if d else '"<project>"')]})
    tmpl = facts["template_draft"]
    lock = Path(cfg_get("capcut.store_lock", str(STUDIO_HOME / "runs" / ".capcut-store.lock")))
    lock.parent.mkdir(parents=True, exist_ok=True)
    steps, res = [], {}
    with FileLock(lock, timeout=900):
        if (d / ".locked").exists() or _capcut_running():
            fail("CapCut is running: close it, then run this again (the project was not changed)", 3)
        env = {**os.environ, "CAPCUT_MCP_CORE": str(core), "CAPCUT_DRAFTS_DIR": str(d.parent), "CAPCUT_TEMPLATE_DRAFT": tmpl}
        try:
            cp = subprocess.run([node, str(BUILD_MJS), str(plan_path)], capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=1800, env=env)
            res = _last_json(cp.stdout) or {"ok": False, "error": ((cp.stderr or "") + (cp.stdout or "")).strip()[-800:]}
            code = cp.returncode
        except subprocess.TimeoutExpired:
            res, code = {"ok": False, "error": "the Node build did not finish in 30 minutes"}, 1
        steps.append({"step": "build", "exit": code, "result": {k: v for k, v in res.items() if k != "segments"}})
        built = code == 0 and bool(res.get("ok"))
        if built:
            steps.append({"step": "mirror", "exit": 0, "result": _mirror_timeline(d)})
            me = str(Path(__file__).resolve())
            if plan["moves"]:
                for name in ("capcut-motion", "capcut-transitions"):
                    if name == "capcut-transitions" and not plan["moves"]["transitions"]:
                        steps.append({"step": name, "exit": 0, "result": "no join but cuts: nothing to write"})
                        continue
                    cp = run([sys.executable, me, name, "--draft", str(d), "--timeline", plan["moves"]["file"]], timeout=1800)
                    r2 = _last_json(cp.stdout) or {"ok": False, "error": (cp.stderr or cp.stdout or "").strip()[-600:]}
                    steps.append({"step": name, "exit": cp.returncode, "ok": bool(r2.get("ok")), "result": r2})
    tracks = _draft_tracks(d) if built else []
    if built:
        main_n = next((t["segments"] for t in tracks if t["type"] == "video"), 0)
        audio_n = sum(t["segments"] for t in tracks if t["type"] == "audio")
        over_n = sum(t["segments"] for t in tracks if t["type"] == "video") - main_n
        want = (counts["pictures"], counts["overlays"], counts["narration"] + counts["beds"] + counts["sfx"])
        muted = [str(t["name"]) for t in tracks if t["muted"] and t["segments"]]
        if muted:   # a track cloned from a muted template starts muted: its clips would play nothing
            steps.append({"step": "read-back", "exit": 1, "result": "muted track(s) holding clips: " + ", ".join(muted)})
        elif (main_n, over_n, audio_n) != want:
            steps.append({"step": "read-back", "exit": 1, "result": f"the saved project holds {main_n} pictures, {over_n} overlays and "
                                                                    f"{audio_n} audio clips; the plan has {want[0]}, {want[1]} and {want[2]}"})
        else:
            steps.append({"step": "read-back", "exit": 0, "result": "the saved project holds every planned clip"})
    ok = built and all(s["exit"] == 0 and s.get("ok", True) for s in steps)
    if log_path.is_file():
        old = _read_json_or_none(log_path) or {}
        if old.get("draft") and _pkey(old["draft"]) != _pkey(d):
            shutil.copyfile(log_path, log_path.with_name(f"build-log.{Path(str(old['draft'])).name}.json"))
    me_sha = _sha256_file(Path(__file__).resolve())
    nv = run([node, "--version"], timeout=60).stdout.strip() if node else None
    log = {"ok": ok, "draft": str(d), "draft_name": d.name, "made_at": now_iso(),
           "toolkit": {"command": "capcut_tools.py capcut-build", "version": CAPCUT_BUILD_VERSION, "capcut_tools_sha256": me_sha,
                       "capcut_build_mjs_sha256": _sha256_file(BUILD_MJS), "mcp_core": str(core), "mcp_core_sha256": _sha256_file(core),
                       "node": nv},
           "build_plan": str(plan_path), "build_plan_sha256": _sha256_file(plan_path), "inputs": plan["inputs"], "counts": counts,
           "tracks": tracks, "steps": steps, "segments": res.get("segments") or [], "warnings": warnings, "plan": plan}
    write_json(log_path, log)
    summary = []
    for s in steps:
        r = s.get("result")
        if s["step"] == "capcut-motion" and isinstance(r, dict):
            r = {"ok": r.get("ok"), "images_without_a_clip": r.get("images_without_a_clip"), "stale_copies": len(r.get("stale_copies") or [])}
        elif s["step"] == "capcut-transitions" and isinstance(r, dict):
            r = {"ok": r.get("ok"), "written": len(r.get("transitions") or []), "already_there": r.get("already_there"),
                 "failed": r.get("failed")}
        elif s["step"] == "build" and isinstance(r, dict):
            r = {"ok": r.get("ok"), "error": r.get("error"), "validate": r.get("validate"), "saved": r.get("saved")}
        summary.append({"step": s["step"], "exit": s["exit"], "result": r})
    res_out = {"ok": ok, "draft": str(d), "build_plan": str(plan_path), "build_log": str(log_path), "sounds_file": str(sounds_file),
               "counts": counts, "tracks": tracks, "steps": summary, "warnings": warnings[:30], "warnings_count": len(warnings)}
    if ok:
        res_out["next"] = nxt
    elif not built:
        res_out["action"] = ("the draft was not saved (core.js saves once, at the end): fix what the build step names, then run "
                             "capcut-build again on this draft")
    else:
        res_out["action"] = ("the clips are in the project; fix what the failed step names and run that step alone on this draft "
                             "(capcut-motion and capcut-transitions can run again), then go on with: " + " | ".join(nxt))
    out(res_out, 0 if ok else 1)


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

    p = sp.add_parser("capcut-build", help="after capcut-prep: the whole project of one video from the run's decided files, in one "
                                           "Node process through the CapCut MCP's own library, then capcut-motion and capcut-transitions")
    p.add_argument("--run", required=True, help="the run folder (or its name under the runs root)")
    p.add_argument("--video", required=True, help="the video's number")
    p.add_argument("--draft", help="the fresh, prepared project folder (capcut-name's path); optional with --dry-run")
    p.add_argument("--images", help="the images file (moves and joins); default RUN/70-edit/video-NN/capcut-images.json")
    p.add_argument("--no-moves", action="store_true", help="the edit has no move and no join: no images file")
    p.add_argument("--sound-placements", help="the beds and sound effects as decided; default RUN/70-edit/video-NN/sound-placements.json")
    p.add_argument("--no-sounds", action="store_true", help="the edit has no bed and no sound effect")
    p.add_argument("--drawings", help="the rendered drawings (DNN.mov beside its spec DNN.json); default RUN/60-visuals/video-NN/drawings")
    p.add_argument("--no-drawings", action="store_true", help="place no drawing")
    p.add_argument("--dry-run", action="store_true", help="write the build plan only; the draft is not touched")
    p.set_defaults(fn=cmd_capcut_build)

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
    # CapCut's project store is shared with the PC's other CapCut users (their builds and GUI exports hold leases in the shared
    # folder): a command that writes into it refuses while one of theirs is in use, and a build holds its own lease while
    # it writes, so their GUI export waits for it (gpu_lease.capcut_store_users, hold_capcut_build).
    if a.cmd in STORE_WRITERS and not getattr(a, "dry_run", False) and not getattr(a, "list", False):
        busy = _store_users()
        if not busy and a.cmd == "capcut-build":
            try:
                _, busy = _gpu_lease().hold_capcut_build(f"capcut-build: video {getattr(a, 'video', '?')}")
            except Exception:  # noqa: BLE001
                busy = []
        if busy:
            x = busy[0]
            fail(f"another pipeline is using CapCut's project store ({x.get('name')} by {x.get('by') or 'another job'} since "
                 f"{x.get('at')}): wait until it ends, then run this again (nothing was changed)", 3)
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
