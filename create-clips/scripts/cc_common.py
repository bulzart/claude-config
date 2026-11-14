"""Shared helpers of the create-clips toolkit: config, paths, run folders, the chunk table, times, JSON output.

The contract (file names, JSON fields, times) is C:/Users/Bulzart/.claude/create-clips/README.md. This module only
implements what every command shares; the commands live in cc_proc.py (processing) and cc_edit.py (editing).
Scripts gather, agents decide: nothing here judges.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

CC_HOME = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("CC_CONFIG") or (CC_HOME / "config.json"))
SCHEMA = "cc/1"
CHUNK_RE = re.compile(r"^C(\d{4,})$")


def _stdio_utf8() -> None:
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:          # pythonw.exe (the logon task) has no console: write to a log file instead of crashing
            try:
                (CC_HOME / "logs").mkdir(parents=True, exist_ok=True)
                setattr(sys, name, open(CC_HOME / "logs" / "background.log", "a", encoding="utf-8", errors="replace", buffering=1))
            except OSError:
                setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


_stdio_utf8()


# --------------------------------------------------------------------------- output

def out(obj: dict, code: int = 0) -> None:
    """One JSON object on the last line of stdout, then exit."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    sys.exit(code)


def fail(msg: str, code: int = 2, **extra) -> None:
    out({"ok": False, "error": msg, **extra}, code)


def say(msg: str) -> None:
    """A progress line on stderr (stdout stays one JSON object)."""
    sys.stderr.write(msg.rstrip() + "\n")
    sys.stderr.flush()


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- files

def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def write_text(path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.name}.tmp{os.getpid()}")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, p)


def write_json(path, obj, indent: int | None = 1) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=indent))


class FileLock:
    """A lock file (O_EXCL) with a timeout; a lock older than `stale_s` is taken over."""

    def __init__(self, path, timeout: float = 120.0, stale_s: float = 900.0):
        self.path, self.timeout, self.stale_s = Path(path), timeout, stale_s

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        end = time.time() + self.timeout
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale_s:
                        self.path.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.time() > end:
                    raise TimeoutError(f"lock {self.path} is held")
                time.sleep(0.2)

    def __exit__(self, *exc):
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass


# --------------------------------------------------------------------------- config

_CFG = None


def load_config() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = read_json(CONFIG_PATH, {}) or {}
    return _CFG


def cfg_get(path: str, default=None):
    cur = load_config()
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def runs_root() -> Path:
    return Path(os.environ.get("CC_RUNS_ROOT") or cfg_get("runs_root") or (CC_HOME / "runs"))


def inbox_dir() -> Path:
    return Path(os.environ.get("CC_INBOX") or cfg_get("inbox_dir") or (Path.home() / "Downloads" / "twitch-chunks"))


# --------------------------------------------------------------------------- tools

def find_tool(name: str) -> str:
    exe = shutil.which(name)
    if exe:
        return exe
    for base in (Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",):
        if base.is_dir():
            hits = sorted(base.glob(f"**/bin/{name}.exe"))
            if hits:
                return str(hits[-1])
    fail(f"{name} not found on PATH", 1)
    return name


# A console program (ffmpeg, ffprobe, powershell ...) started by a process that has no console of its own, such as the pythonw.exe watcher of the logon task,
# is given a NEW console, and with Windows Terminal as the default terminal that is a visible window per call. Every child this toolkit starts carries this
# flag: the console stays hidden and nothing opens. (0 where the flag does not exist; tests/test_nowindow.py checks that no call site forgets it.)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run_cmd(args: list, timeout: float = 600, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command without a shell; text output, never raises on a non-zero exit. The child's console window stays hidden (NO_WINDOW)."""
    return subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, cwd=cwd, creationflags=NO_WINDOW)


def ffprobe_facts(path) -> dict:
    cp = run_cmd([find_tool("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], timeout=120)
    try:
        j = json.loads(cp.stdout or "{}")
    except ValueError:
        j = {}
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), {})
    fmt = j.get("format", {})

    def frac(x):
        try:
            n, d = str(x).split("/")
            return round(float(n) / float(d), 3) if float(d) else None
        except (ValueError, ZeroDivisionError):
            return None
    dur = fmt.get("duration") or v.get("duration")
    return {
        "path": str(path),
        "duration_s": round(float(dur), 3) if dur else None,
        "size_bytes": int(fmt.get("size") or 0) or None,
        "bit_rate": int(fmt.get("bit_rate") or 0) or None,
        "width": v.get("width"), "height": v.get("height"),
        "fps": frac(v.get("avg_frame_rate")), "video_codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "nb_frames": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
        "audio_codec": a.get("codec_name"), "audio_rate": int(a["sample_rate"]) if a.get("sample_rate") else None,
        "audio_channels": a.get("channels"), "has_video": bool(v), "has_audio": bool(a),
    }


def free_gb(path) -> float:
    p = Path(path)
    while not p.exists() and p.parent != p:
        p = p.parent
    return round(shutil.disk_usage(p).free / 1e9, 2)


# --------------------------------------------------------------------------- times

def fmt_hms(sec: float, cs: bool = True) -> str:
    """0:33:45.75 (rec time). Negative or None -> '-'."""
    if sec is None:
        return "-"
    neg = sec < 0
    sec = abs(sec)
    whole = int(sec)
    frac = sec - whole
    h, rem = divmod(whole, 3600)
    m, s = divmod(rem, 60)
    base = f"{h}:{m:02d}:{s:02d}"
    if cs:
        c = int(round(frac * 100))
        if c == 100:
            c = 0
            s += 1
            if s == 60:
                s, m = 0, m + 1
                if m == 60:
                    m, h = 0, h + 1
            base = f"{h}:{m:02d}:{s:02d}"
        base += f".{c:02d}"
    return ("-" if neg else "") + base


def fmt_off(sec: float) -> str:
    """+45.75 (a chunk offset)."""
    return f"+{sec:.2f}"


def parse_time(text, rows: list | None = None) -> float:
    """Seconds from '2025.75', '33:45.75', '0:33:45.75' (rec time) or 'C0012+45.75' (chunk + offset; needs the chunk table)."""
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text).strip()
    m = re.match(r"^(C\d{4,})\s*\+\s*([0-9.]+)$", s, re.I)
    if m:
        if rows is None:
            fail("a chunk time needs the chunk table")
        return chunk_to_rec(rows, m.group(1).upper(), float(m.group(2)))
    parts = s.split(":")
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        fail(f"cannot read the time {text!r}")
    t = 0.0
    for v in vals:
        t = t * 60 + v
    return t


# --------------------------------------------------------------------------- runs

def chunk_id(n: int) -> str:
    return f"C{int(n):04d}"


def chunk_index(cid: str) -> int:
    m = CHUNK_RE.match(cid)
    if not m:
        raise ValueError(f"not a chunk id: {cid}")
    return int(m.group(1))


def resolve_run(arg) -> Path:
    """A run folder from a path, a bare session name under runs_root, or a unique prefix of one."""
    if not arg:
        fail("--run is needed (a run folder path or a session name)")
    p = Path(str(arg).strip().strip('"'))
    if p.is_dir() and ((p / "state.json").is_file() or (p / "10-media").is_dir()):
        return p.resolve()
    root = runs_root()
    if (root / p.name).is_dir():
        return (root / p.name).resolve()
    hits = sorted(d for d in root.glob("*") if d.is_dir() and arg and str(arg) in d.name) if root.is_dir() else []
    if len(hits) == 1:
        return hits[0].resolve()
    if len(hits) > 1:
        fail(f"{arg!r} matches several runs: {[h.name for h in hits][:8]}")
    fail(f"no run folder for {arg!r} (runs_root = {root})")
    return p


def run_paths(run: Path) -> dict:
    run = Path(run)
    return {k: run / v for k, v in {
        "state": "state.json", "inventory": "00-inventory", "media": "10-media", "analysis": "20-analysis",
        "assets": "30-assets", "briefs": "40-briefs", "outputs": "60-outputs", "deliverables": "deliverables", "logs": "logs",
        "chunks": "00-inventory/chunks.json", "stream_md": "00-inventory/stream.md", "meta": "00-inventory/stream-meta.json"}.items()}


def chunk_dir(run: Path, cid: str) -> Path:
    return Path(run) / "10-media" / cid


def load_state(run: Path) -> dict:
    return read_json(Path(run) / "state.json", {}) or {}


def save_state(run: Path, state: dict) -> None:
    with FileLock(Path(run) / ".state.lock", timeout=60):
        write_json(Path(run) / "state.json", state)


def update_state(run: Path, **changes) -> dict:
    """Read-modify-write under the lock; dotted keys set nested values ('chunks.C0001.status')."""
    with FileLock(Path(run) / ".state.lock", timeout=60):
        st = read_json(Path(run) / "state.json", {}) or {}
        for k, v in changes.items():
            cur = st
            parts = k.split(".")
            for p in parts[:-1]:
                cur = cur.setdefault(p, {})
            cur[parts[-1]] = v
        write_json(Path(run) / "state.json", st)
        return st


def load_chunks(run: Path) -> list:
    return read_json(Path(run) / "00-inventory" / "chunks.json", []) or []


def save_chunks(run: Path, rows: list) -> None:
    with FileLock(Path(run) / ".chunks.lock", timeout=60):
        write_json(Path(run) / "00-inventory" / "chunks.json", rows)


def chunk_to_rec(rows: list, cid: str, off: float) -> float:
    r = next((x for x in rows if x["id"] == cid.upper()), None)
    if r is None:
        fail(f"no chunk {cid} in the chunk table")
    return round(float(r["rec_start_s"]) + float(off), 3)


def rec_to_chunk(rows: list, t: float):
    """(chunk id, offset) holding rec time t, or (None, None) past the recorded end / before the start."""
    done = [r for r in rows if r.get("rec_start_s") is not None and r.get("duration_s")]
    for r in done:
        if r["rec_start_s"] - 1e-6 <= t < r["rec_start_s"] + r["duration_s"] - 1e-6:
            return r["id"], round(t - r["rec_start_s"], 3)
    if done and abs(t - (done[-1]["rec_start_s"] + done[-1]["duration_s"])) < 1e-3:
        r = done[-1]
        return r["id"], round(r["duration_s"], 3)
    return None, None


def ad_batches(rows: list) -> list:
    """The chunks the recorder marked as ads (`kind == "ad"`: Twitch's own marker for the segments, passed on in the sidecar), consecutive chunk numbers merged
    into batches (one ad break = one batch). Facts only, for the agents: `[{batch, chunks, rec_from, rec_to, seconds, t0_utc, t1_utc, titles}]` in order. Whether
    a batch really is an ad, and so is left out of every video, is the agents' call (the user, 2026-11-14), never this function's."""
    batches, cur = [], None
    for r in sorted((x for x in rows if x.get("kind") == "ad"), key=lambda x: x["index"]):
        dur = float(r.get("duration_s") or 0)
        start = r.get("rec_start_s")
        if cur is not None and r["index"] == cur["_last"] + 1:
            cur["chunks"].append(r["id"])
            cur["seconds"] += dur
            cur["t1_utc"] = r.get("t1_utc") or cur["t1_utc"]
        else:
            cur = {"batch": len(batches) + 1, "chunks": [r["id"]], "rec_from": start, "seconds": dur, "t0_utc": r.get("t0_utc"), "t1_utc": r.get("t1_utc"),
                   "titles": [], "_last": r["index"]}
            batches.append(cur)
        cur["_last"] = r["index"]
        cur["rec_to"] = round(float(start) + dur, 3) if start is not None else None
        for t in ((r.get("ad") or {}).get("titles") or []):
            if t not in cur["titles"] and len(cur["titles"]) < 5:
                cur["titles"].append(t)
    for b in batches:
        b.pop("_last", None)
        b["seconds"] = round(b["seconds"], 3)
    return batches


def split_across_chunks(rows: list, t0: float, t1: float) -> list:
    """The pieces of rec span [t0, t1) per chunk: [{chunk, offset_from, offset_to, rec_from, rec_to}] in order (a span over a chunk
    boundary gives two pieces; a hole between chunks, a gap in the recording, is skipped and reported by the caller)."""
    pieces = []
    for r in sorted((x for x in rows if x.get("duration_s")), key=lambda x: x["rec_start_s"]):
        a, b = r["rec_start_s"], r["rec_start_s"] + r["duration_s"]
        lo, hi = max(t0, a), min(t1, b)
        if hi - lo > 1e-6:
            pieces.append({"chunk": r["id"], "offset_from": round(lo - a, 3), "offset_to": round(hi - a, 3),
                           "rec_from": round(lo, 3), "rec_to": round(hi, 3)})
    return pieces


def sanitize_channel(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(name or "").lower())[:40] or "channel"
