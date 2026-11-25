"""The resume-note hook (atp_resume_note.py) finds runs without knowing any pipeline by name.

    python hooks/test_resume_note.py

A copy of the hook runs inside a temporary stand-in for ~/.claude, so no real run is read:
- a run in `<any folder>/runs` is found, and so is one under a `runs_root` that a `<any folder>/config.json` names;
- the newest run in progress wins; a finished stage, a run older than 36 hours and a run that says nothing about what comes next are skipped;
- a run is named by its folder path, or by its state's `command` field when it has one;
- a run with no skill to load gets the generic instruction with its next step; no run means no output."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "atp_resume_note.py"
failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    failed += 0 if cond else 1


def make(runs: Path, name: str, state: dict, todo: str | None = None, age_h: float = 0) -> Path:
    d = runs / name
    d.mkdir(parents=True)
    f = d / "state.json"
    f.write_text(json.dumps(state), encoding="utf-8")
    if todo:
        (d / "todo.md").write_text(todo, encoding="utf-8")
    t = time.time() - age_h * 3600
    os.utime(f, (t, t))
    return d


def note(hook: Path) -> str:
    env = {k: v for k, v in os.environ.items() if k != "RESUME_NOTE_ROOTS"}
    r = subprocess.run([sys.executable, str(hook)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
    out = r.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


with tempfile.TemporaryDirectory(prefix="resume-note-") as tmp:
    tmp = Path(tmp)
    claude = tmp / "claude"
    (claude / "hooks").mkdir(parents=True)
    hook = claude / "hooks" / HOOK.name
    shutil.copy(HOOK, hook)

    check(note(hook) == "", "no runs folder anywhere: the hook prints nothing")

    a = claude / "pipe-a" / "runs"
    a.mkdir(parents=True)
    outside = tmp / "elsewhere" / "runs"
    outside.mkdir(parents=True)
    (claude / "pipe-b").mkdir()
    (claude / "pipe-b" / "config.json").write_text(json.dumps({"runs_root": str(outside).replace("\\", "/")}), encoding="utf-8")

    make(a, "r-finished", {"stage": "released", "next_skill": "x"}, age_h=0.1)
    make(a, "r-old", {"stage": "producing", "next_skill": "x"}, age_h=40)
    make(outside, "r-recording", {"schema": "rec/1"}, age_h=0.1)
    check(note(hook) == "", "a finished run, a run older than 36 h and a run that says nothing about what comes next are skipped")

    r1 = make(a, "r-1", {"stage": "producing", "next_skill": "skill-a", "mode": "analyze", "video": "03"}, age_h=2)
    n = note(hook)
    check(f"`{r1}`" in n and "skill-a" in n and "video 03" in n and "analyze mode" in n and n.startswith("A pipeline run is in progress"),
          f"a run in <folder>/runs is found and named by its path: {n[:120]}")

    r2 = make(outside, "r-2", {"stage": "planning", "command": "/some-command"}, todo="# to-do\nNext: write the script\n", age_h=1)
    n = note(hook)
    check(f"`{r2}`" in n and n.startswith("A /some-command run is in progress"), f"a run under a config's runs_root is found, is newer, and its command field names it: {n[:120]}")
    check("Next: write the script" in n and "names no skill to load" in n, "a run with no skill to load gets its to-do's Next line and the generic instruction")

    r3 = make(a, "r-3", {"stage": "planned", "next_step": "A6"}, age_h=0.5)
    n = note(hook)
    check(f"`{r3}`" in n and "next step `A6`" in n, f"a run with only a next_step counts and shows it: {n[:120]}")

print("ALL PASSED" if not failed else f"FAILED: {failed}")
sys.exit(1 if failed else 0)
