"""The three hooks and the upload capture, against a Loupe server started in this process (fake data folder, no model, no credits):
the flag-watch hook keeps a media_upload answer as a capture and tells only this toolkit about `hf-put --capture`; a flagged
generation answer is captured with the usual reminder; the resume note names a run of this library and its next skill; the read
guard refuses a whole-file Read of awl.py and allows an offset read; `T hf-put --capture` uploads from the capture without the URL
ever passing through the agent's hands (a PUT server in this process receives it)."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import HOME, PY, check, finish, t, temp_library  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="awl-hooks-"))
DATA = TMP / "loupe-data"
home = temp_library("hooks")
for k, v in (("LOUPE_DATA", DATA), ("AWL_HOME", home), ("ATP" + "_HOME", TMP / "lib-a-empty"), ("ATG" + "_HOME", TMP / "lib-b-empty")):
    os.environ[k] = str(v)
    Path(v).mkdir(parents=True, exist_ok=True)
LOUPE = Path(os.environ.get("LOUPE_HOME") or HOME / "loupe")
sys.path.insert(0, str(LOUPE))
from loupe_app import core, server  # noqa: E402

httpd = server.ThreadingHTTPServer((core.HOST, 0), server.Handler)
httpd.daemon_threads = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
core.ensure_dirs()
(DATA / "server.json").write_text(json.dumps({"port": httpd.server_port, "pid": os.getpid()}), encoding="utf-8")
for name, scopes in (("pipeline", ["flags:write", "flags:read", "runs:read"]), ("qc", ["qc:read", "flags:read"])):
    core.key_write_file(name, core.key_create(name, scopes)["key"])
ENV = {k: os.environ[k] for k in ("LOUPE_DATA", "AWL_HOME", "ATP" + "_HOME", "ATG" + "_HOME")}
HOOKS = HOME / "hooks"


def hook(name, event, env=None):
    cp = subprocess.run([PY, "-X", "utf8", str(HOOKS / name)], input=json.dumps(event), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        env={**os.environ, **ENV, **(env or {})}, timeout=60)
    try:
        return json.loads(cp.stdout.strip().splitlines()[-1]) if cp.stdout.strip() else {}
    except ValueError:
        return {"raw": cp.stdout[-300:]}


def captures():
    import loupe_client as lc
    s, d = lc.call("GET", "/api/captures?full=1&limit=50", key_name="pipeline")
    return d.get("captures", []) if s == 200 else []


# --- a run of this library, the newest state.json on this machine's temp roots
run = home / "runs" / "20261001-000000-05"
run.mkdir(parents=True)
(run / "state.json").write_text(json.dumps({"run_id": run.name, "mode": "analyze", "stage": "producing", "next_skill": "awl-analyze-produce", "video": "02"}), encoding="utf-8")

# --- 1. a media_upload answer is captured and this toolkit is told about --capture
up = {"uploads": [{"filename": "can.png", "upload_url": "http://127.0.0.1:1/put/one?X-Amz-Signature=abc", "media_id": "11111111-2222-3333-4444-555555555555",
                   "url": "https://cdn.example/one.png", "content_type": "image/png"}]}
r = hook("atp_flag_watch.py", {"hook_event_name": "PostToolUse", "tool_name": "mcp__higgsfield__media_upload", "tool_input": {"files": [{"filename": "can.png", "content_type": "image/png"}]},
                               "tool_response": up})
note = (r.get("hookSpecificOutput") or {}).get("additionalContext", "")
caps = captures()
check(caps and "upload" in str(caps[0].get("summary")) and "upload" in json.dumps((caps[0].get("payload") or {}).get("signals")), f"a media_upload answer is kept as a capture with the signal upload ({len(caps)} capture(s))")
check("awl.py hf-put --capture" in note and str(caps[0]["id"]) in note, f"the reminder names hf-put --capture with the capture id: {note[:120]}")
cid = caps[0]["id"]

# --- 2. the same answer when the newest run belongs to another library: captured, but no reminder (that toolkit has no --capture)
other = TMP / "lib-a-empty" / "runs" / "20261001-000000-09"
other.mkdir(parents=True)
time.sleep(0.05)
(other / "state.json").write_text(json.dumps({"run_id": other.name, "mode": "analyze", "stage": "producing"}), encoding="utf-8")
up2 = {"uploads": [{"filename": "two.png", "upload_url": "http://127.0.0.1:1/put/two", "media_id": "22222222-2222-3333-4444-555555555555", "url": "x", "content_type": "image/png"}]}
r = hook("atp_flag_watch.py", {"hook_event_name": "PostToolUse", "tool_name": "mcp__higgsfield__media_upload", "tool_input": {}, "tool_response": up2})
check(not r and len(captures()) == 2, "with another library's run newest, the upload is still captured and no reminder is printed")
(other / "state.json").unlink()
other.rmdir()

# --- 3. a flagged generation answer: captured with the usual reminder naming this toolkit
r = hook("atp_flag_watch.py", {"hook_event_name": "PostToolUse", "tool_name": "mcp__higgsfield__generate_video", "tool_input": {"prompt": "the can on the desk"},
                               "tool_response": {"status": "failed", "error": "content moderation blocked this request", "job_id": "33333333-2222-3333-4444-555555555555"}})
note = (r.get("hookSpecificOutput") or {}).get("additionalContext", "")
check("awl.py caught-flag add --run " + run.name in note and "moderation" in note, f"a flagged answer is captured and the reminder names caught-flag add for this run: {note[:100]}")

# --- 4. the resume note names this library's run and the skill to re-invoke
r = hook("atp_resume_note.py", {"hook_event_name": "SessionStart", "source": "compact"})
note = (r.get("hookSpecificOutput") or {}).get("additionalContext", "")
check("/analyze-with-loupe run `" + run.name in note and "awl-analyze-produce" in note and "video 02" in note, f"the resume note names the run, the video and next_skill: {note[:110]}")

# --- 5. the read guard: a whole-file Read of awl.py is refused, an offset read passes
p = str(HOME / "analyze-with-loupe" / "scripts" / "awl.py")
r = hook("atp_read_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": p}})
check((r.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny", "a whole-file Read of awl.py is refused")
r = hook("atp_read_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": p, "offset": 100, "limit": 40}})
check(not r, "a Read of awl.py with offset and limit passes")
r = hook("atp_read_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": str(HOME / "analyze-with-loupe" / "models" / "index.json")}})
check((r.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny", "a whole-file Read of models/index.json is refused")

# --- 6. hf-put --capture: the URL comes from the capture; a PUT server in this process receives the bytes with the content type
got = {}


class Put(BaseHTTPRequestHandler):
    def do_PUT(self):
        n = int(self.headers.get("Content-Length") or 0)
        got["path"], got["ctype"], got["n"] = self.path, self.headers.get("Content-Type"), len(self.rfile.read(n))
        self.send_response(200)
        self.send_header("ETag", '"abc"')
        self.end_headers()

    def log_message(self, *a):
        pass


puts = HTTPServer(("127.0.0.1", 0), Put)
threading.Thread(target=puts.serve_forever, daemon=True).start()
up3 = {"uploads": [{"filename": "three.png", "upload_url": f"http://127.0.0.1:{puts.server_port}/slot/three?X-Amz-Signature=def", "media_id": "44444444-2222-3333-4444-555555555555",
                    "url": "x", "content_type": "image/png"},
                   {"filename": "four.mp4", "upload_url": f"http://127.0.0.1:{puts.server_port}/slot/four", "media_id": "55555555-2222-3333-4444-555555555555", "url": "y", "content_type": "video/mp4"}]}
r = hook("atp_flag_watch.py", {"hook_event_name": "PostToolUse", "tool_name": "mcp__higgsfield__media_upload", "tool_input": {"files": [{"filename": "three.png"}, {"filename": "four.mp4"}]}, "tool_response": up3})
cid3 = max(c["id"] for c in captures())
png = TMP / "three.png"
png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 500)
js, code, _ = t("hf-put", "--capture", str(cid3), "--file", str(png), env=ENV)
check(js.get("ok") and js.get("status") == 200 and got.get("path", "").startswith("/slot/three") and got.get("ctype") == "image/png" and got.get("n") == 508 and js.get("media_id", "").startswith("4444"),
      f"hf-put --capture uploads the file to the slot whose filename matches, with the capture's content type, and reports the media id ({js.get('status')}, {got})")
js, code, _ = t("hf-put", "--capture", str(cid3), "--file", str(png), "--slot", "1", env=ENV)
check(js.get("ok") and got.get("path", "").startswith("/slot/four") and got.get("ctype") == "video/mp4", "--slot picks another upload slot of the same capture")
js, code, _ = t("hf-put", "--capture", "999999", "--file", str(png), env=ENV, ok=False)
check(code == 2 and "capture" in js.get("error", ""), "an unknown capture id fails loudly")
finish()
