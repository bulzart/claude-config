#!/usr/bin/env python
"""SessionStart hook (matcher compact|resume): after a compaction or a resume, tell the agent which /analyze-then-pick run is in
progress and which skill to re-invoke.  The skills' text may have been summarised away; the run's state.json still names the next one.
It reads one small file and prints one short note; with no run in progress it prints nothing."""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

CLAUDE = Path(__file__).resolve().parent.parent
FINISHED = {"done", "redo_delivered", "delivered", "complete", "completed", "closed"}


def main():
    home = Path(os.environ.get("ATP_HOME") or CLAUDE / "analyze-then-pick")
    best = None
    for p in (home / "runs").glob("*/state.json"):
        if p.parent.name.startswith("client-fixes"):
            continue
        try:
            st = json.loads(p.read_text(encoding="utf-8"))
            t = p.stat().st_mtime
        except (OSError, ValueError):
            continue
        if st.get("stage") in FINISHED or time.time() - t > 36 * 3600:
            continue
        if best is None or t > best[0]:
            best = (t, p, st)
    if not best:
        return
    t, p, st = best
    nxt = st.get("next_skill") or ""
    where = f"stage `{st.get('stage', '?')}`" + (f", video {st['video']}" if st.get("video") else "")
    if nxt:
        todo = f"Re-invoke the skill `{nxt}` (Skill tool) before doing anything else: its text may have been summarised away."
    else:
        todo = (f"This run has no `next_skill` (it predates the skills layout): take the phase from `stage` / `next_step` "
                f"(`{st.get('next_step', '?')}`) with the map in the command's resume section.")
    note = (f"/analyze-then-pick run `{p.parent.name}` is in progress ({st.get('mode', '?')} mode, {where}; last change "
            f"{datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')}). {todo} Read `{p}` and the ledger for the exact point reached; "
            f"if this session is not working on that run, ignore this note.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
