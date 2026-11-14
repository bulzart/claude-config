#!/usr/bin/env python
"""SessionStart hook (matcher compact|resume): after a compaction or a resume, tell the agent which pipeline run is in
progress (of /analyze-then-pick, /analyze-then-generate, /analyze-with-loupe, /create-static or /create-clips, whichever changed last) and which skill to re-invoke.  The skills' text may have been summarised away; the run's state.json still names the next one.
It reads one small file and prints one short note; with no run in progress it prints nothing."""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

CLAUDE = Path(__file__).resolve().parent.parent
FINISHED = {"done", "redo_delivered", "delivered", "complete", "completed", "closed", "wrapped"}
# (library folder, environment override, slash command)
LIBS = [("analyze-then-pick", "ATP_HOME", "/analyze-then-pick"), ("analyze-then-generate", "ATG_HOME", "/analyze-then-generate"), ("analyze-with-loupe", "AWL_HOME", "/analyze-with-loupe"),
        ("create-static", "CS_HOME", "/create-static")]


def run_folders():
    """(the folder that holds the runs, the slash command, whether a run counts only once the command has started it)."""
    for folder, env, command in LIBS:
        yield Path(os.environ.get(env) or CLAUDE / folder) / "runs", command, False
    # /create-clips: its runs are made by the stream processor in the runs_root of its config (CC_RUNS_ROOT in the tests). A run the processor made and the command has not
    # started has no next_skill: it is a recording, not a run in progress.
    root = os.environ.get("CC_RUNS_ROOT")
    if not root:
        try:
            root = json.loads((CLAUDE / "create-clips" / "config.json").read_text(encoding="utf-8")).get("runs_root")
        except (OSError, ValueError):
            root = None
    if root:
        yield Path(root).expanduser(), "/create-clips", True


def main():
    best = None
    for runs, command, needs_next in run_folders():
        for p in runs.glob("*/state.json"):
            if p.parent.name.startswith("client-fixes"):
                continue
            try:
                st = json.loads(p.read_text(encoding="utf-8"))
                t = p.stat().st_mtime
            except (OSError, ValueError):
                continue
            if st.get("stage") in FINISHED or time.time() - t > 36 * 3600:
                continue
            if needs_next and not st.get("next_skill"):
                continue
            if best is None or t > best[0]:
                best = (t, p, st, command)
    if not best:
        return
    t, p, st, command = best
    nxt = st.get("next_skill") or ""
    where = f"stage `{st.get('stage', '?')}`" + (f", video {st['video']}" if st.get("video") else "")
    if nxt:
        todo = f"Re-invoke the skill `{nxt}` (Skill tool) before doing anything else: its text may have been summarised away."
    else:
        todo = (f"This run has no `next_skill` (it predates the skills layout): take the phase from `stage` / `next_step` "
                f"(`{st.get('next_step', '?')}`) with the map in the command's resume section.")
    todo_note = ""
    todo_file = p.parent / "todo.md"        # the run's to-do (command item 38): what is done and what is next
    if todo_file.is_file():
        nxt_line = ""
        try:
            for ln in todo_file.read_text(encoding="utf-8").splitlines()[:15]:
                if ln.startswith("Next:"):
                    nxt_line = " " + ln.strip()[:320]
                    break
        except OSError:
            pass
        todo_note = f" Read the run's to-do `{todo_file}` first (what is done and what is next).{nxt_line}"
    note = (f"{command} run `{p.parent.name}` is in progress ({st.get('mode', '?')} mode, {where}; last change "
            f"{datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')}).{todo_note} {todo} Read `{p}`{'' if command == '/create-clips' else ' and the ledger'} for the exact point reached; "
            f"if this session is not working on that run, ignore this note.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
