"""Test of scripts/native_host.py: the native-messaging protocol, the detached watcher start, the status answer.

    python tests/test_native_host.py

Uses temporary runs/inbox folders (CC_RUNS_ROOT, CC_INBOX); the watcher it starts is a real `cc.py watch` and is stopped at the end.
"""
from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = HERE.parent / "scripts" / "native_host.py"
PY = sys.executable


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


class Host:
    def __init__(self, env):
        self.p = subprocess.Popen([PY, str(HOST), "chrome-extension://abc/"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    def ask(self, obj):
        data = json.dumps(obj).encode()
        self.p.stdin.write(struct.pack("<I", len(data)) + data)
        self.p.stdin.flush()
        head = self.p.stdout.read(4)
        (n,) = struct.unpack("<I", head)
        return json.loads(self.p.stdout.read(n).decode())

    def close(self):
        self.p.stdin.close()
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-host-test-"))
    pid = 0
    try:
        runs, inbox = tmp / "runs", tmp / "inbox"
        session = "20261112-111200-testch"
        (runs / session / "00-inventory").mkdir(parents=True)
        (inbox / "testch" / session).mkdir(parents=True)
        (runs / session / "00-inventory" / "chunks.json").write_text(json.dumps([
            {"id": "C0001", "index": 1, "status": "done", "processed_at": "2026-11-12T11:20:00", "seconds": {"audio": 1, "sheets": 4, "transcript": 100}},
            {"id": "C0002", "index": 2, "status": "processing"}]), encoding="utf-8")
        (inbox / "testch" / session / "chunk-0003.mp4").write_bytes(b"x")
        env = {**os.environ, "CC_RUNS_ROOT": str(runs), "CC_INBOX": str(inbox), "CC_REPORT": "0"}      # no real report sessions from the watcher this test starts
        h = Host(env)
        r = h.ask({"id": "1", "type": "hello"})
        check(r.get("ok") and r["id"] == "1" and r["host"] == "create-clips", "hello answered with the host name and the id echoed")
        check(r.get("watcher") in ("started", "running") and r.get("pid", 0) > 0, f"watcher {r.get('watcher')} pid {r.get('pid')}")
        pid = r.get("pid", 0)
        check(r.get("free_gb", 0) > 0 and r.get("inbox_free_gb", 0) > 0, "hello carries the free space of the runs drive and of the inbox drive")
        r2 = h.ask({"id": "2", "type": "ensure"})
        check(r2.get("watcher") == "running" and r2.get("pid") == pid, "ensure again finds the same watcher running (single instance)")
        st = h.ask({"id": "3", "type": "status", "session": session})
        check(st.get("ok") and st["chunks"] == {"total": 3, "done": 1, "processing": 1, "failed": 0, "pending": 1}, "status counts: " + json.dumps(st.get("chunks")))
        check(st["last"]["id"] == "C0001" and st["last"]["seconds"] == 105.0 and st["run"] and st["free_gb"] > 0, "status last chunk, run path, free space")
        check(h.ask({"id": "4", "type": "status", "session": "../x"}).get("ok") is False, "a session id with .. is refused")
        check(h.ask({"id": "5", "type": "nope"}).get("ok") is False, "an unknown type is an error answer, not a crash")
        h.close()
        check(h.p.returncode == 0, "the host exits cleanly when Chrome closes the port")
        time.sleep(0.5)
        check(pid and subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout.count(str(pid)) > 0, "the watcher outlives the host")
    finally:
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        time.sleep(0.5)
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
