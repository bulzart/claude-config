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


fx_g = G / "fx"
fx_g.mkdir()
(fx_g / "wipe.mp4").write_bytes(b"x")
rg = mkrun("20990101-000001-guard", mode="analyze", stage="producing", source=str(refs_g), examples_paths=[str(ex_g)])
mkrun("20990101-000002-old", mode="analyze", stage="done", source=str(done_g), examples_paths=[])
mkrun("20990101-000003-edit", mode="edit", stage="editing", source=[str(edit_v)], examples_paths=[])
mkrun("20990101-000004-static", mode="analyze", stage="producing", source=str(G / "static-refs"), examples_paths=[],
      static={"effects_folder": str(fx_g)})
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
    ("Bash", f'rm "{str(fx_g)}/wipe.mp4"', True, "rm in an open Static run's effects folder"),
    ("PowerShell", f'Copy-Item "{fx_g}\\wipe.mp4" "{RUN}\\wipe.mp4"', False, "Copy-Item from the effects folder into the run folder"),
]
for tool, cmd, want, label in cases:
    got = denied(tool, cmd)
    check(got == want, f"input guard: {label} is {'refused' if want else 'let through'}")
# the review of 2026-10-28: ways around the guard it must close, and everyday commands it must not refuse
EX, EXF = str(ex_g), str(ex_g).replace("\\", "/")
GF = str(G).replace("\\", "/")
rel_home = str(ex_g.resolve()).replace("\\", "/")[len(str(Path.home().resolve()).replace("\\", "/")):]
cleaner2 = G / "cleaner2.py"
cleaner2.write_text('import os, shutil, sys\nsrc = sys.argv[1]\ntmp = os.path.join(os.environ.get("TEMP", "."), "x-awl")\nos.makedirs(tmp, exist_ok=True)\n'
                    'shutil.copy2(os.path.join(src, "a.mp4"), tmp)\nshutil.rmtree(tmp, ignore_errors=True)\n', encoding="utf-8")
cases2 = [
    ("Bash", f'SRC="{RF}"; rm "$SRC"/a.mp4', True, "rm through a shell variable"),
    ("Bash", f'for f in "{RF}"/*; do mv "$f" "{RUNF}/"; done', True, "mv in a for loop over the references"),
    ("PowerShell", f'$refs = "{R}"; Get-ChildItem $refs | ForEach-Object {{ Remove-Item $_.FullName }}', True, "Remove-Item through a PowerShell variable and ForEach-Object"),
    ("Bash", f"bash -c \"rm '{RF}/a.mp4'\"", True, "rm inside bash -c"),
    ("Bash", f'cmd /c "del {EX}\\e.mp4"', True, "del inside cmd /c"),
    ("Bash", f"powershell -Command \"Remove-Item '{R}\\a.mp4'\"", True, "Remove-Item inside powershell -Command"),
    ("Bash", f"python -c \"import os; os.system('rm {EXF}/e.mp4')\"", True, "rm inside os.system in python -c"),
    ("Bash", f'rm \\\n  "{RF}/a.mp4"', True, "rm across a line continuation"),
    ("Bash", f'rm "{GF}/x/../My Refs 27.10/a.mp4"', True, "rm through a path with .."),
    ("Bash", f'rm "$USERPROFILE{rel_home}/e.mp4"', True, "rm through $USERPROFILE"),
    ("Bash", f'rm -rf "{GF}"', True, "rm -rf of the folder that holds the references"),
    ("Bash", f'cd "{GF}" && rm -rf *', True, "rm -rf * in the folder that holds the references"),
    ("Bash", f'cd "{GF}" && rm -f *.tmp', False, "rm *.tmp beside the references (the pattern cannot match them)"),
    ("Bash", f'cp -f "{RUNF}/x.mp4" "{RF}/a.mp4"', True, "cp over a reference"),
    ("Bash", f'echo hi > "{RF}/notes.txt"', True, "a redirection into the references"),
    ("PowerShell", f'Set-Content -Path "{R}\\notes.txt" -Value x', True, "Set-Content into the references"),
    ("Bash", f'ffmpeg -y -i "{RUNF}/x.mp4" "{RF}/out.mp4"', True, "ffmpeg writing into the references"),
    ("PowerShell", f'Copy-Item "{RUN}\\x.mp4" -Destination "{R}"', True, "Copy-Item into the references"),
    ("Bash", f'python - <<\'EOF\'\nimport shutil\nsrc = r"{R}"\nshutil.move(src + "/a.mp4", r"{RUN}/a.mp4")\nEOF', True, "a python heredoc that moves through a variable"),
    ("Bash", f'python - <<\'EOF\'\nimport shutil\nsrc = r"{R}"\ntmp = r"{RUN}\\tmp"\nshutil.copy2(src + "/a.mp4", r"{RUN}/a.mp4")\nshutil.rmtree(tmp)\nEOF', False,
     "a python heredoc that copies a reference and removes its own temp folder"),
    ("Bash", f'cat > "{RUNF}/note.md" <<\'EOF\'\n{RF}/a.mp4: the hands move fast\nrm {RF}/a.mp4 is never done\nEOF', False, "a note that names a reference and says move and rm"),
    ("Bash", f'"$PY" "$AWL/scripts/awl.py" caught-flag add --run X --tags rename --flagged-video "{RF}/a.mp4"', False, "the toolkit with --tags rename and a reference path"),
    ("Bash", f'ffmpeg -y -i "{RF}/a.mp4" -t 1 "{RUNF}/clip.mp4"', False, "ffmpeg reading a reference into the run folder"),
    ("PowerShell", f'Copy-Item "{R}\\a.mp4" -Destination "{RUN}"', False, "Copy-Item from the references into the run folder"),
    ("Bash", f'ls "{RF}" | head; find "{RF}" -name "*.mp4"', False, "listing and finding in the references"),
    ("Bash", f"python -c \"import pandas as pd; df = pd.read_csv(r'{RUN}\\x.csv'); df.rename(columns={{'a': 'b'}})\"", False, "a pandas rename on a run file"),
    ("Bash", f'python "{cleaner2}" "{RF}"', False, "a script given the references that removes its own temp folder"),
    ("Bash", f'cd "{RF}" && python -c "import os; os.remove(r\'{RUN}\\tmp.txt\')"', False, "os.remove of a run file while the references are the working folder"),
    ("Bash", f'mv "$TMPFILE" "$OUT"', False, "a mv whose targets are unset variables"),
    ("Bash", f'rm -rf "{RUNF}/10-media/V01/_work" 2>&1 | tail -2', False, "an rm in the run folder with a redirection of its errors"),
]
for tool, cmd, want, label in cases2:
    got = denied(tool, cmd, cwd=str(Path.home() / "Documents"))
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
