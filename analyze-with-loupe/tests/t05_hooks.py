"""The four hooks and the upload capture, against a Loupe server started in this process (fake data folder, no model, no credits):
the flag-watch hook keeps a media_upload answer as a capture and tells only this toolkit about `hf-put --capture`; a flagged
generation answer is captured with the usual reminder; the resume note names a run of this library and its next skill; the read
guard refuses a whole-file Read of awl.py and allows an offset read; `T hf-put --capture` uploads from the capture without the URL
ever passing through the agent's hands (a PUT server in this process receives it); the input guard (item 34) refuses a move, delete,
Write or Edit inside an open run's references, edit sources or examples, and lets copies, reads and the run folder through."""
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

# --- 7. the input guard (item 34): an open run's references, edit sources and examples are read-only; copies, reads, the run folder,
#        a done run's folders and the toolkit itself pass
G = TMP / "guard"
refs_g = G / "My Refs 27.10"
refs_g.mkdir(parents=True)
(refs_g / "a.mp4").write_bytes(b"x")
ex_g = G / "examples"
ex_g.mkdir()
done_g = G / "old-refs"
done_g.mkdir()
edit_v = G / "edit-src" / "clip.mp4"
edit_v.parent.mkdir()
edit_v.write_bytes(b"x")


def mkrun(name, **st):
    d = home / "runs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({"run_id": name, **st}), encoding="utf-8")
    return d


rg = mkrun("20990101-000001-guard", mode="analyze", stage="producing", source=str(refs_g), examples_paths=[str(ex_g)])
mkrun("20990101-000002-old", mode="analyze", stage="done", source=str(done_g), examples_paths=[])
mkrun("20990101-000003-edit", mode="edit", stage="editing", source=[str(edit_v)], examples_paths=[])
R, RUN = str(refs_g), str(rg)
RF, RUNF, LONG = R.replace("\\", "/"), RUN.replace("\\", "/"), str(refs_g.resolve()).replace("\\", "/")
GB = "/" + LONG[0].lower() + LONG[2:]


def denied(tool, cmd=None, cwd=None, **inp):
    ti = {"command": cmd} if cmd is not None else inp
    r = hook("awl_input_guard.py", {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti, "cwd": str(cwd or RUN)})
    return (r.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"


mover = G / "mover.py"
mover.write_text(f'import shutil\nSRC = r"{R}"\nshutil.move(SRC + "/a.mp4", "x.mp4")\n', encoding="utf-8")
cleaner = G / "cleaner.py"
cleaner.write_text('import os\nos.remove("tmp.txt")\n', encoding="utf-8")
cases = [
    ("Bash", f'rm "{RF}/a.mp4"', True, "rm of a reference"),
    ("Bash", f'mv "{RF}/a.mp4" "{RUNF}/a.mp4"', True, "mv of a reference into the run folder"),
    ("Bash", f'cp "{RF}/a.mp4" "{RUNF}/a.mp4"', False, "cp of a reference into the run folder"),
    ("Bash", f'cp "{RF}/a.mp4" "{RUNF}/" && rm -rf "{RUNF}/tmp"', False, "a copy from the references and a delete in the run folder"),
    ("Bash", f'cd "{RF}" && rm *.mp4', True, "cd into the references, then rm by wildcard"),
    ("Bash", f'rm "{GB}/a.mp4"', True, "rm through the Git Bash /c/ form of the long path"),
    ("Bash", f'rm "{LONG}/a.mp4"', True, "rm through the long path of a folder stored in its 8.3 form"),
    ("Bash", f'find "{RF}" -name "*.mp4" -delete', True, "find -delete"),
    ("Bash", f'rm "{str(done_g)}/o.mp4"', False, "rm in a done run's references"),
    ("Bash", f'rm "{str(ex_g)}/e.mp4"', True, "rm in an open run's examples"),
    ("Bash", f'rm "{str(edit_v)}"', True, "rm of an Edit Mode source video"),
    ("Bash", f'rm "{RF}0/x.mp4"', False, "a folder that only shares the name's start"),
    ("Bash", f'python -c "import shutil; shutil.move(r\'{R}\\a.mp4\', r\'{RUN}\\a.mp4\')"', True, "shutil.move in python -c"),
    ("Bash", f'python -c "import os; print(os.listdir(r\'{R}\'))"', False, "a python -c that only lists the references"),
    ("Bash", f'python - <<\'EOF\'\nimport shutil\nsrc = r"{R}"\nshutil.move(src + "/a.mp4", r"{RUN}/a.mp4")\nEOF', True, "a python heredoc that moves"),
    ("Bash", f'python "{mover}"', True, "a script file that moves from the references"),
    ("Bash", f'python "{cleaner}"', False, "a script file that deletes its own temp file"),
    ("Bash", f'rm "{RUNF}/tmp.txt"', False, "rm in the run folder"),
    ("Bash", f'"$PY" "$AWL/scripts/awl.py" split-audio --run X "{RF}"', False, "the toolkit called with the references folder"),
    ("PowerShell", f'Remove-Item -LiteralPath "{R}\\a.mp4"', True, "Remove-Item"),
    ("PowerShell", f'Get-ChildItem "{R}" -Filter *.mp4 | Move-Item -Destination "{RUN}"', True, "Get-ChildItem piped to Move-Item"),
    ("PowerShell", f'Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("{R}\\a.mp4", \'OnlyErrorDialogs\', \'SendToRecycleBin\')', True, "a delete to the Recycle Bin"),
    ("PowerShell", f'Copy-Item "{R}\\a.mp4" "{RUN}\\a.mp4"', False, "Copy-Item into the run folder"),
    ("PowerShell", f'Rename-Item "{R}\\a.mp4" b.mp4', True, "Rename-Item"),
    ("PowerShell", f'Set-Location "{R}"; Remove-Item *.mp4', True, "Set-Location into the references, then Remove-Item"),
]
for tool, cmd, want, label in cases:
    got = denied(tool, cmd)
    check(got == want, f"input guard: {label} is {'refused' if want else 'let through'}")
check(denied("Bash", "rm *.mp4", cwd=R), "input guard: rm by wildcard with the references as the working folder is refused")
check(denied("Write", file_path=f"{R}\\notes.txt", content="x"), "input guard: a Write into the references is refused")
check(denied("Edit", file_path=f"{RF}/a.mp4", old_string="x", new_string="y"), "input guard: an Edit inside the references is refused")
check(not denied("Write", file_path=f"{RUN}\\notes.txt", content="x"), "input guard: a Write into the run folder passes")
r = hook("awl_input_guard.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": f'rm "{RF}/a.mp4"'}, "cwd": RUN})
why = (r.get("hookSpecificOutput") or {}).get("permissionDecisionReason", "")
check("item 34" in why and "20990101-000001-guard" in why and "copy" in why, f"the refusal names item 34, the run and the copy: {why[:120]}")
cp = subprocess.run([PY, "-X", "utf8", str(HOOKS / "awl_input_guard.py")], input="not json", capture_output=True, text=True, env={**os.environ, **ENV}, timeout=60)
check(cp.returncode == 0 and not cp.stdout.strip(), "input guard: a malformed event lets the call through (fails open)")
st_g = json.loads((rg / "state.json").read_text(encoding="utf-8"))
st_g["stage"] = "done"
(rg / "state.json").write_text(json.dumps(st_g), encoding="utf-8")
check(not denied("Bash", f'rm "{RF}/a.mp4"'), "input guard: once the run is done its references are no longer guarded")

finish()
