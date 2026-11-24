#!/usr/bin/env python3
"""gpu_lease.py - the GPU lease Static Studio's GPU jobs hold while they use the card, so the PC's other GPU users see them
and make room: FLUX 3 Image Klein int8 (image_worker.py: while its private ComfyUI runs), ACE-Step 1.5 (music_worker.py:
while its models load and play) and Whisper medium on cuda float16 (static_core.py: while the model loads, and while it
transcribes a file). A program that keeps an idle model on the GPU lets it go while a lease needs more memory than is free.

The lease files are the PC's shared ones, one file per job: <lease dir>/lease-<name>.json, UTF-8 JSON written whole (a
temporary file beside it, then os.replace):
  {"name", "need_mb", "t", "at", "ttl_s", "pid", "note", "by"}
  name      "create-video-<kind>-<pid>": one file per process, so two jobs never let go of each other's lease;
  need_mb   the GPU memory (MB) the job uses;
  t, at     when it was taken (epoch seconds, and the local time as ISO text); neither changes while it is held;
  ttl_s     the lease is stale once now - t > ttl_s; a live holder extends ttl_s every BEAT_S seconds;
  pid       the holding process: once it has ended the lease is stale, whatever ttl_s says;
  note, by  what the job is, and who holds it ("create-video").
A stale lease counts for nobody: every reader skips it, and a new holder takes its place (acquire removes the stale
create-video-* files it finds and writes over its own name; other holders' stale files are skipped and left alone).

acquire() writes the lease first, so others see the job while it waits. How long it waits follows who holds the card,
never one fixed time for every job (the user, 2026-11-24):
  - a live lease taken earlier that would not fit on the card beside this job (their need_mb together more than the
    card's memory), or one named in wait_for: until it ends, or until it has run STUCK_FACTOR times the time it said it
    needs (expected_s; a holder that names none: its own time-to-live), then it is treated as stuck;
  - less than need_mb free and the recorder beside the leases holds its Whisper (whisper.json: loaded, its process alive): up to
    RECORDER_YIELD_S, the time that recorder takes to let an idle Whisper go (it looks every 10 s, between chunks);
  - less than need_mb free and nobody in the lease system holds it (another program): only settle_s, unless memory is
    coming back, then while it keeps coming back.
A job may cap all of it (wait_s; 0 = no wait). First come, first served: a job waits only for leases taken before its
own, so two jobs never wait for each other. Waiting and going ahead are said on stderr. When the wait ends the job goes
ahead on the GPU and says why: a lease never refuses a job and never changes its device, model or precision. It is let
go when the job ends, on an error, and at exit (atexit); a process that is killed leaves a lease with a dead pid, which
is stale. The card's real size is read (nvidia-smi) and reported (card_mb); a job that declares more than the card has
is said so. The memory guard that runs FLUX and ACE-Step caps their process memory (RAM and page file), not the card.

The lease dir: STATIC_GPU_LEASE_DIR when set (tests point it at a temporary folder), else the PC's shared folder
~/.claude/create-clips/data/gpu when it exists (the PC's other GPU users read leases only there, so every GPU job sees
the others there; nothing is ever created under that path), else static-studio/data/gpu.

CapCut's project store is shared too: the PC's other CapCut builds hold capcut-build-<video>-<pid> and its GUI exports hold
capcut-export in the same folder, a check-and-take under its desk lock file (capcut-desk.lock). capcut_store_users()
lists those in use now; hold_capcut_build() takes the same lock and holds capcut-build-create-video-<pid> while this
pipeline writes a project (those GUI exports wait while a capcut-build-* lease is held).

Standard library only: it runs in Python 3.11 (ACE-Step), 3.12 and 3.13 (ComfyUI's embedded Python).
"""
from __future__ import annotations

import atexit
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

LEASE_DIR_ENV = "STATIC_GPU_LEASE_DIR"
PREFIX, BY = "create-video-", "create-video"
TTL_S = 600.0        # time-to-live after the last beat: a holder that stops beating (hung, or its pid reused) goes stale
BEAT_S = 60.0        # how often a live holder extends its ttl_s (t stays the time it was taken)
POLL_S = 2.0         # how often a waiting job looks again
SETTLE_S = 15.0      # memory held outside the lease system: how long to look for it coming back (then while it keeps coming)
RECORDER_YIELD_S = 75.0   # the recorder beside the leases lets an idle Whisper go: it looks every 10 s, between chunks
STUCK_FACTOR = 2.0   # a lease holder still running at this many times the time it said it needs is treated as stuck
CAPCUT_DESK_LOCK = "capcut-desk.lock"           # the shared lock file for a check-and-take on CapCut's project store
OWN_BUILD_PREFIX = "capcut-build-create-video-"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_VRAM = {"t": 0.0, "v": None}
_HELD = {}                       # lease name -> _Held: the leases this process holds
_LOCK = threading.Lock()
_sleep = time.sleep


def default_lease_dir() -> Path:
    """The PC's shared GPU lease folder (~/.claude/create-clips/data/gpu) when it exists: the PC's other GPU users read
    leases only there. Otherwise static-studio/data/gpu, where the jobs here still see each other; nothing is ever
    created under the shared path."""
    studio = Path(__file__).resolve().parent.parent
    shared = studio.parent / "create-clips" / "data" / "gpu"
    return shared if shared.is_dir() else studio / "data" / "gpu"


def lease_dir() -> Path:
    return Path(os.environ[LEASE_DIR_ENV]) if os.environ.get(LEASE_DIR_ENV) else default_lease_dir()


def _say(text: str) -> None:
    try:
        print(f"[gpu-lease] {text}", file=sys.stderr, flush=True)
    except Exception:  # noqa: BLE001 - a closed or odd stderr never stops a job
        pass


def _now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def vram(max_age_s: float = 3.0):
    """The GPU's memory from nvidia-smi, {"total_mb", "used_mb", "free_mb", "util_pct"}, or None without an answer."""
    if time.time() - _VRAM["t"] < max_age_s:
        return _VRAM["v"]
    v, exe = None, shutil.which("nvidia-smi")
    if exe:
        try:
            cp = subprocess.run([exe, "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
                                 "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10,
                                creationflags=NO_WINDOW)
            total, used, free, util = [x.strip() for x in (cp.stdout or "").splitlines()[0].split(",")]
            v = {"total_mb": int(total), "used_mb": int(used), "free_mb": int(free),
                 "util_pct": int(util) if util.isdigit() else None}
        except Exception:  # noqa: BLE001 - no answer is no reading, never an error
            v = None
    _VRAM.update(t=time.time(), v=v)
    return v


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _K32 = ctypes.WinDLL("kernel32", use_last_error=True)      # a private handle: nobody else's kernel32 setup changes
    _K32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _K32.OpenProcess.restype = wintypes.HANDLE
    _K32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    _K32.GetExitCodeProcess.restype = wintypes.BOOL
    _K32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _K32.CloseHandle.restype = wintypes.BOOL


def pid_alive(pid) -> bool:
    """The readers' rule: a lease without a pid lives by its time-to-live; a pid that cannot be opened, or whose process
    has an exit code, has ended (STILL_ACTIVE, 259, means it runs); when in doubt the holder is alive."""
    if not pid:
        return True
    try:
        pid = int(pid)
        if os.name == "nt":
            h = _K32.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            try:
                code = wintypes.DWORD()
                _K32.GetExitCodeProcess(h, ctypes.byref(code))
                return code.value == 259
            finally:
                _K32.CloseHandle(h)
        os.kill(pid, 0)                                         # POSIX only: on Windows os.kill would end the process
        return True
    except ProcessLookupError:
        return False
    except Exception:  # noqa: BLE001
        return True


def _read(path: Path):
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def live(d: dict, now: float | None = None) -> bool:
    """The readers' rule for one lease: fresh (now - t at most ttl_s, 1800 s when it has none) and its process alive."""
    now = time.time() if now is None else now
    try:
        fresh = now - float(d.get("t") or 0) <= float(d.get("ttl_s") or 1800)
    except (TypeError, ValueError):
        return False
    return fresh and pid_alive(d.get("pid"))


def leases(exclude: str | None = None) -> list:
    """Every live lease in the lease dir, whoever holds it, as its readers see them (stale ones are skipped)."""
    folder, found, now = lease_dir(), [], time.time()
    if not folder.is_dir():
        return found
    for p in sorted(folder.glob("lease-*.json")):
        d = _read(p)
        if d and d.get("name") != exclude and live(d, now):
            found.append(d)
    return found


def _write(path: Path, record: dict) -> bool:
    """The lease written whole: a temporary file beside it, then os.replace, so a reader sees the old file or the new one.
    On Windows a replace fails while a reader has the file open: it is tried again a few times."""
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    data = json.dumps(record, ensure_ascii=False, indent=1).encode("utf-8")
    try:
        for i in range(10):
            try:
                tmp.write_bytes(data)
                os.replace(tmp, path)
                return True
            except PermissionError:
                _sleep(0.05 * (i + 1))
        return False
    except OSError:
        return False
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _unlink(path: Path) -> bool:
    for i in range(10):
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return True
        except PermissionError:                                # a reader has it open this instant
            _sleep(0.05 * (i + 1))
        except OSError:
            return False
    return False


class _Held:
    """The lease file this process holds under one name, shared by nested holds of that name. A beat thread extends its
    ttl_s while the process lives; close() stops the beat and removes the file if it is still this holder's."""

    def __init__(self, path: Path, record: dict, ttl_s: float, beat_s: float):
        self.path, self.record, self.ttl_s, self.beat_s = path, record, float(ttl_s), float(beat_s)
        self.refs, self.info = 1, {}
        self._lock, self._stop, self._thread = threading.Lock(), threading.Event(), None

    def start_beat(self) -> None:
        if self.beat_s > 0:
            self._thread = threading.Thread(target=self._beat, name="gpu-lease-beat", daemon=True)
            self._thread.start()

    def _beat(self) -> None:
        while not self._stop.wait(self.beat_s):
            with self._lock:
                if self._stop.is_set():
                    return
                rec = dict(self.record, ttl_s=round(time.time() - float(self.record["t"]) + self.ttl_s, 1))
                if _write(self.path, rec):
                    self.record = rec

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)
        with self._lock:
            cur = _read(self.path)
            if cur is None or (cur.get("pid") == self.record["pid"] and cur.get("t") == self.record["t"]):
                _unlink(self.path)                             # never another holder's lease
        with _LOCK:
            if _HELD.get(self.record["name"]) is self:
                del _HELD[self.record["name"]]


class Lease:
    """A job's hold on the GPU. A context manager whose value is `info` ({"name", "held", "need_mb", "waited_s", "free_mb",
    "why", "file"}: "why" says what the job went ahead despite); release() lets it go and is safe to call twice."""

    def __init__(self, held: _Held | None, info: dict):
        self._held, self.info, self._done = held, info, held is None

    @property
    def name(self):
        return self.info.get("name")

    @property
    def held(self) -> bool:
        return not self._done

    def release(self) -> None:
        if self._done:
            return
        self._done = True
        with _LOCK:
            self._held.refs -= 1
            last = self._held.refs <= 0
        if last:
            self._held.close()

    def __enter__(self):
        return self.info

    def __exit__(self, *exc):
        self.release()
        return False


def unheld(why: str) -> Lease:
    """A Lease that holds nothing (a job that does not use the GPU), with the same interface."""
    return Lease(None, {"name": None, "held": False, "need_mb": 0, "waited_s": 0.0, "free_mb": None, "why": why, "file": None})


def _clear_stale(folder: Path, own: str) -> None:
    """Take over from stale holders: the create-video lease files of a process that has ended, or past their time-to-live,
    are removed. A file that cannot be read is left (it may be another holder's, being written)."""
    now = time.time()
    for p in list(folder.glob(f"lease-{PREFIX}*.json")) + list(folder.glob(f"lease-{OWN_BUILD_PREFIX}*.json")):
        if p.name == f"lease-{own}.json":
            continue                                           # this job's own name: written over just after
        d = _read(p)
        if d is not None and not live(d, now):
            _unlink(p)


def recorder_whisper():
    """The recorder's Whisper state beside the leases (whisper.json: loaded, pid, at) while it holds the model
    and its process lives, else None."""
    d = _read(lease_dir() / "whisper.json")
    if not d or not d.get("loaded") or not pid_alive(d.get("pid")):
        return None
    return d


def _holder_deadline(x: dict) -> float:
    """Until when a lease in the way is waited for: STUCK_FACTOR times the time its holder said it needs (expected_s), or
    its own time-to-live when it names none."""
    try:
        t = float(x.get("t") or 0)
        exp = float(x.get("expected_s") or 0)
        ttl = float(x.get("ttl_s") or 1800)
    except (TypeError, ValueError):
        return 0.0
    return t + (STUCK_FACTOR * exp if exp > 0 else ttl)


def _in_the_way(x: dict, own: dict, v, wait_for: tuple) -> bool:
    """A live lease this job waits for: one named in wait_for (a name, or a prefix ending in *), or a GPU job that took
    its lease first and would not fit beside this one (their need_mb together more than the card's memory)."""
    name = str(x.get("name") or "")
    if any(name == w or (w.endswith("*") and name.startswith(w[:-1])) for w in wait_for):
        return True
    if not v or own["need_mb"] <= 0:
        return False
    try:
        theirs, t = int(x.get("need_mb") or 0), float(x.get("t") or 0)
    except (TypeError, ValueError):
        return False
    first = (t, name) < (float(own["t"]), own["name"])
    return first and theirs > 0 and theirs + own["need_mb"] > int(v["total_mb"])


def _why(ahead: list, free, need: int, kind=None) -> str:
    parts = [f"{x.get('name')} holds it ({int(x.get('need_mb') or 0)} MB, by {x.get('by') or 'another job'} since {x.get('at')})"
             for x in ahead]
    if free is not None and need > 0 and free < need:
        parts.append(f"only {free} MB free of the {need} MB this job needs")
        if kind == "recorder":
            parts.append("the recorder beside the leases holds its Whisper (it lets an idle one go between chunks)")
    return "; ".join(parts)


def _wait(record: dict, wait_s, wait_for: tuple, settle_s: float, poll_s: float) -> dict:
    name, need, t0 = record["name"], record["need_mb"], time.time()
    v = vram(0)
    info = {"name": name, "held": True, "need_mb": need, "waited_s": 0.0, "free_mb": v["free_mb"] if v else None,
            "card_mb": v["total_mb"] if v else None, "why": None, "waited_for": None}
    if v and need > int(v["total_mb"]):
        info["why"] = f"this job declares {need} MB and the card has {v['total_mb']} MB in all"
        _say(f"{name}: {info['why']}: it cannot fit even on an empty card")
    if wait_s is not None and float(wait_s) <= 0:
        return info
    said, prev, gained, kind = False, None, None, None
    while True:
        free = v["free_mb"] if v else None
        ahead = [x for x in leases(exclude=name) if _in_the_way(x, record, v, wait_for)]
        short = free is not None and need > 0 and free < need
        now = time.time()
        if not ahead and not short:
            if said:
                _say(f"{name}: the GPU is ready after {now - t0:.0f} s")
            break
        if free is not None and prev is not None and free > prev + 64:
            gained = now                                       # memory is coming back
        prev = free
        if ahead:     # a GPU job that took the card first: until it ends, or has run STUCK_FACTOR times its own estimate
            kind, deadline = "lease", max(_holder_deadline(x) for x in ahead)
        else:         # the recorder gives an idle Whisper back; memory held outside the leases is not waited for
            kind = "recorder" if recorder_whisper() else "outside"
            deadline = t0 + (RECORDER_YIELD_S if kind == "recorder" else settle_s)
            if gained is not None:
                deadline = max(deadline, gained + settle_s)    # while memory keeps coming back
        if wait_s is not None:
            deadline = min(deadline, t0 + float(wait_s))
        why = _why(ahead, free, need, kind)
        if now >= deadline:
            _say(f"{name}: going ahead on the GPU after {now - t0:.0f} s: {why}")
            info["why"] = why
            break
        if not said:
            _say(f"{name}: waiting for the GPU (up to {max(0.0, deadline - t0):.0f} s): {why}")
            said = True
        _sleep(max(0.01, min(poll_s, deadline - now)))         # never past the end of the wait
        v = vram(0)
    info.update(waited_s=round(time.time() - t0, 1), free_mb=free, waited_for=kind if said else None)
    return info


def acquire(kind: str, need_mb: int = 0, wait_s=None, note: str = "", wait_for=(), ttl_s: float = TTL_S,
            beat_s: float = BEAT_S, settle_s: float = SETTLE_S, poll_s: float = POLL_S, expected_s=None) -> Lease:
    """Take the GPU lease "create-video-<kind>-<pid>" for a job: written at once (with expected_s, how long the job
    thinks it holds the card, for the others' wait), then the wait described at the top (wait_s caps it when given);
    the job always goes ahead on the GPU. A nested hold of the same kind in this process shares the lease (no second
    wait). A lease that cannot be written is said on stderr and the job goes ahead without one."""
    pid = os.getpid()
    name = f"{PREFIX}{kind}-{pid}"
    need = max(0, int(need_mb or 0))
    folder = lease_dir()
    path = folder / f"lease-{name}.json"
    with _LOCK:
        h = _HELD.get(name)
        if h is not None:
            h.refs += 1
            return Lease(h, dict(h.info, nested=True))
        record = {"name": name, "need_mb": need, "t": time.time(), "at": _now_iso(), "ttl_s": float(ttl_s), "pid": pid,
                  "note": str(note or ""), "by": BY,
                  **({"expected_s": round(float(expected_s), 1)} if expected_s else {})}
        try:
            folder.mkdir(parents=True, exist_ok=True)
            _clear_stale(folder, name)
            ok = _write(path, record)
        except OSError:
            ok = False
        if not ok:
            _say(f"{name}: the lease could not be written in {folder}; going ahead on the GPU without one")
            return Lease(None, {"name": name, "held": False, "need_mb": need, "waited_s": 0.0, "free_mb": None,
                                "why": f"the lease could not be written in {folder}", "file": None})
        h = _Held(path, record, ttl_s, beat_s)
        _HELD[name] = h
    h.start_beat()
    try:
        h.info = dict(_wait(record, None if wait_s is None else float(wait_s), tuple(wait_for or ()), float(settle_s),
                            float(poll_s)), file=str(path))
    except BaseException:
        h.close()                                              # an interrupted wait (Ctrl+C) leaves no lease behind
        raise
    return Lease(h, h.info)


def capcut_store_users() -> list:
    """Others' live leases on CapCut's shared project store, in the shared folder's own protocol: a build
    writing a project (capcut-build-*) or a GUI export (capcut-export). This pipeline's own builds are not counted."""
    return [x for x in leases()
            if (str(x.get("name") or "").startswith("capcut-build-") and not str(x.get("name")).startswith(OWN_BUILD_PREFIX))
            or x.get("name") == "capcut-export"]


def _desk_lock(folder: Path, timeout: float = 60.0, stale_s: float = 300.0):
    """The shared desk lock: the same file and rule (O_EXCL; one older than stale_s is taken over). The lock path
    when held, else None (then the check goes ahead without it)."""
    p = folder / CAPCUT_DESK_LOCK
    end = time.time() + timeout
    while True:
        try:
            fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return p
        except FileExistsError:
            try:
                if time.time() - p.stat().st_mtime > stale_s:
                    p.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            if time.time() > end:
                return None
            _sleep(0.2)
        except OSError:
            return None


def hold_capcut_build(note: str = "", ttl_s: float = 900.0):
    """While this process writes a project into CapCut's shared store: under the shared desk lock, check that nobody
    else uses the store, then hold capcut-build-create-video-<pid> (the other GUI exports wait while a capcut-build-*
    lease is held), let go at exit. Returns (Lease or None, the others in the way). Without the shared folder nobody
    coordinates through it: (None, [])."""
    folder = lease_dir()
    if not folder.is_dir():
        return None, []
    lock = _desk_lock(folder)
    try:
        busy = capcut_store_users()
        if busy:
            return None, busy
        name = f"{OWN_BUILD_PREFIX}{os.getpid()}"
        path = folder / f"lease-{name}.json"
        record = {"name": name, "need_mb": 0, "t": time.time(), "at": _now_iso(), "ttl_s": float(ttl_s),
                  "pid": os.getpid(), "note": str(note or "writing a CapCut project"), "by": BY}
        if not _write(path, record):
            return None, []
        h = _Held(path, record, ttl_s, BEAT_S)
        with _LOCK:
            _HELD[name] = h
        h.start_beat()
        h.info = {"name": name, "held": True, "file": str(path)}
        return Lease(h, h.info), []
    finally:
        if lock is not None:
            try:
                lock.unlink(missing_ok=True)
            except OSError:
                pass


def release_all() -> None:
    """Let go of every lease this process still holds: registered with atexit, so a job that ends any way but a kill
    leaves none behind."""
    with _LOCK:
        held = list(_HELD.values())
    for h in held:
        h.close()


atexit.register(release_all)
