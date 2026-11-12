"""Chrome native-messaging host `com.createclips.processor`: the Twitch Chunk Recorder's link to this toolkit.

Chrome starts this process when the extension calls chrome.runtime.connectNative('com.createclips.processor') and talks to it over stdin/stdout
(4-byte little-endian length + UTF-8 JSON). It never prints anything else to stdout.

Messages (each carries a string `id` that the answer repeats):
  {"type":"hello"}                     -> {"ok":true,"type":"hello","host":"create-clips","version":"1","watcher":"running|started|failed","pid":N,"runs_root":..,"inbox":..,
                                           "free_gb":N (runs drive),"inbox_free_gb":N (the drive Chrome saves the chunks to)}
  {"type":"ensure"}                    -> the same as hello (starts the watcher detached when it is not running)
  {"type":"status","session":"<id>"}   -> {"ok":true,"type":"status","session":..,"run":path|null,"chunks":{"total","done","processing","failed","pending"},
                                           "last":{"id","status","seconds"}|null,"free_gb":N,"inbox_free_gb":N}
The watcher (`cc.py watch`) is started detached (it survives this host and Chrome) and is single-instance (its own lock file), so `ensure` is safe to repeat.
Registration and the opt-in autostart: scripts/install-background.ps1.
"""
from __future__ import annotations

import ctypes
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cc_common import CC_HOME, free_gb, inbox_dir, read_json, runs_root  # noqa: E402

VERSION = "1"
LOG = CC_HOME / "logs" / "native-host.log"


def log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg.rstrip() + "\n")
        if LOG.stat().st_size > 512_000:                      # keep the log small
            LOG.write_text(LOG.read_text(encoding="utf-8")[-200_000:], encoding="utf-8")
    except OSError:
        pass


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def watcher_pid() -> int:
    lock = runs_root() / ".watch.lock"
    try:
        pid = int(lock.read_text().strip() or 0)
    except (OSError, ValueError):
        return 0
    return pid if pid_alive(pid) else 0


def ensure_watcher() -> dict:
    pid = watcher_pid()
    if pid:
        return {"watcher": "running", "pid": pid}
    try:
        out = (CC_HOME / "logs" / "watch.log").open("ab")
        flags = 0
        if os.name == "nt":
            flags = 0x00000008 | 0x00000200 | 0x08000000       # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        p = subprocess.Popen([sys.executable, str(CC_HOME / "scripts" / "cc.py"), "watch"], stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                             creationflags=flags, close_fds=True, cwd=str(CC_HOME))
        for _ in range(30):                                     # the watcher writes its lock file a moment after it starts
            time.sleep(0.2)
            pid = watcher_pid()
            if pid:
                break
            if p.poll() is not None:
                break
        if pid:
            log(f"watcher started (pid {pid})")
            return {"watcher": "started", "pid": pid}
        log(f"watcher did not start (exit {p.poll()})")
        return {"watcher": "failed", "pid": 0}
    except OSError as e:
        log(f"watcher start failed: {e}")
        return {"watcher": "failed", "pid": 0, "error": str(e)[:200]}


def session_status(session: str) -> dict:
    root = runs_root()
    run = root / session
    rows = read_json(run / "00-inventory" / "chunks.json", []) or []
    channel = session.split("-", 2)[2] if session.count("-") >= 2 else ""
    sess_in = inbox_dir() / channel / session
    waiting = 0
    if sess_in.is_dir():
        waiting = sum(1 for f in sess_in.glob("chunk-*.mp4"))
    counts = {"done": 0, "processing": 0, "failed": 0}
    for r in rows:
        st = r.get("status")
        if st in counts:
            counts[st] += 1
    last = None
    done_rows = [r for r in rows if r.get("status") in ("done", "failed")]
    if done_rows:
        r = max(done_rows, key=lambda x: (x.get("processed_at") or "", x.get("index") or 0))
        secs = r.get("seconds") or {}
        last = {"id": r.get("id"), "status": r.get("status"), "seconds": round(sum(v for v in secs.values() if isinstance(v, (int, float))), 1) if secs else None}
    return {"session": session, "run": str(run) if run.is_dir() else None,
            "chunks": {"total": len(rows) + waiting, **counts, "pending": waiting}, "last": last, "free_gb": free_gb(root),
            "inbox_free_gb": free_gb(inbox_dir())}


def handle(msg: dict) -> dict:
    mid, typ = msg.get("id"), msg.get("type")
    base = {"id": mid, "ok": True, "type": typ}
    if typ in ("hello", "ensure"):
        w = ensure_watcher()
        return {**base, "host": "create-clips", "version": VERSION, **w, "runs_root": str(runs_root()), "inbox": str(inbox_dir()),
                "free_gb": free_gb(runs_root()), "inbox_free_gb": free_gb(inbox_dir())}
    if typ == "status":
        sess = str(msg.get("session") or "")
        if not sess or "/" in sess or "\\" in sess or ".." in sess:
            return {"id": mid, "ok": False, "error": "a session id is needed"}
        return {**base, **session_status(sess)}
    return {"id": mid, "ok": False, "error": f"unknown message type {typ!r}"}


def read_message(stream):
    head = stream.read(4)
    if len(head) < 4:
        return None
    (n,) = struct.unpack("<I", head)
    if n <= 0 or n > 1_000_000:
        return None
    body = stream.read(n)
    if len(body) < n:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stream, obj: dict) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(struct.pack("<I", len(data)) + data)
    stream.flush()


def main() -> None:
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
    log(f"host started (pid {os.getpid()}, args {sys.argv[1:]})")
    while True:
        try:
            msg = read_message(stdin)
        except (ValueError, OSError) as e:
            log(f"bad message: {e}")
            break
        if msg is None:
            break
        try:
            reply = handle(msg)
        except Exception as e:  # noqa: BLE001
            log(f"handler error: {type(e).__name__}: {e}")
            reply = {"id": msg.get("id"), "ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
        try:
            write_message(stdout, reply)
        except OSError:
            break
    log("host stopped")


if __name__ == "__main__":
    main()
