"""The SessionStart resume-note hook (hooks/atp_resume_note.py) names a /create-static run that is in progress, with its skill and video, and prints the to-do's `Next:` line.
Temporary folders only: every library's run folder is pointed at an empty temporary one (environment overrides), so no real run is read.  python tests/t03_resume_hook.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "atp_resume_note.py"
OTHERS = ("ATP_HOME", "ATG_HOME", "AWL_HOME", "CC_RUNS_ROOT")        # the other libraries' roots: pointed at empty folders so that nothing real is read
FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


def run_hook(env_extra):
    r = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True, encoding="utf-8", env={**os.environ, **env_extra}, timeout=30)
    out = r.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def make(home, name, state, todo=None):
    d = Path(home) / "runs" / name
    d.mkdir(parents=True)
    (d / "state.json").write_text(json.dumps(state), encoding="utf-8")
    if todo:
        (d / "todo.md").write_text(todo, encoding="utf-8")


with tempfile.TemporaryDirectory(prefix="cs-resume-hook-") as tmp:
    tmp = Path(tmp)
    home = tmp / "cs"
    env = {k: str(tmp / ("none-" + k)) for k in OTHERS}
    env["CS_HOME"] = str(home)

    check(run_hook(env) == "", "no run: the hook prints nothing")
    make(home, "20261114-000001-static-done", {"stage": "done", "next_skill": "", "mode": "analyze"})
    check(run_hook(env) == "", "a finished run (stage done) is not 'in progress'")
    todo = "# Run to-do: 20261114-000002-static-x (kept by the main session; one writer)\nNext: S3 stills for video 02, stretch 2\nUpdated: 2026-11-14\n[x] S2 narration\n"
    make(home, "20261114-000002-static-x", {"stage": "producing", "next_skill": "cs-produce", "mode": "analyze", "video": "02"}, todo=todo)
    note = run_hook(env)
    check("/create-static run `20261114-000002-static-x`" in note and "cs-produce" in note and "video 02" in note, f"a run in progress is named with its skill and video: {note[:120]}")
    check("Next: S3 stills for video 02, stretch 2" in note and "todo.md" in note, "the note points at the run's to-do and prints its Next line")

print("ALL PASSED" if not FAILS else f"FAILED: {len(FAILS)}")
sys.exit(1 if FAILS else 0)
