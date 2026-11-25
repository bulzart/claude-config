"""The SessionStart resume-note hook (hooks/atp_resume_note.py) names a run of this command that is in progress (by its folder), with its skill, its mode and the to-do's `Next:` line.

    python tests/test_resume_hook.py

Temporary folders only: RESUME_NOTE_ROOTS points the hook at one temporary runs folder, so no real run is read.
A recording the processor made and the command has not started (no `next_skill`) and a wrapped run are not "in progress"; a started run is; the note does not send the agent to a ledger (this command has none).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "atp_resume_note.py"
failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    failed += 0 if cond else 1


def run_hook(env_extra: dict) -> str:
    r = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True, encoding="utf-8", env={**os.environ, **env_extra}, timeout=30)
    out = r.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def make(root: Path, name: str, state: dict, todo: str | None = None) -> None:
    d = root / name
    d.mkdir(parents=True)
    (d / "state.json").write_text(json.dumps(state), encoding="utf-8")
    if todo:
        (d / "todo.md").write_text(todo, encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory(prefix="cc-resume-hook-") as tmp:
        tmp = Path(tmp)
        runs = tmp / "runs"
        env = {"RESUME_NOTE_ROOTS": str(runs)}

        check(run_hook(env) == "", "no run: the hook prints nothing")

        make(runs, "20261114-000001-rec", {"schema": "cc/1", "channel": "x"})
        make(runs, "20261114-000002-done", {"schema": "cc/1", "channel": "x", "stage": "wrapped", "next_skill": "", "mode": "streamer"})
        check(run_hook(env) == "", "a recording the command has not started (no next_skill) and a wrapped run are not 'in progress'")

        todo = "# Run to-do: 20261114-000003-cc (kept by the main session; one writer)\nNext: spawn the production agents for L01 and S01\nUpdated: 2026-11-14\n[x] intake\n"
        make(runs, "20261114-000003-cc", {"stage": "planned", "next_skill": "cc-produce", "mode": "streamer"}, todo=todo)
        note = run_hook(env)
        check("`" + str(runs / "20261114-000003-cc") + "`" in note and "cc-produce" in note and "streamer mode" in note, f"a started run is named with its skill and mode: {note[:110]}")
        check("Next: spawn the production agents for L01 and S01" in note and "todo.md" in note, "the note points at the run's to-do and prints its Next line")
        check("the ledger" not in note, "the note does not send the agent to a ledger (this command has none)")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
