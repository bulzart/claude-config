#!/usr/bin/env python
"""SessionStart hook (matcher compact|resume): after a compaction or a resume, tell the agent which pipeline run is in
progress and which skill to load again: the skills' text may have been summarised away, the run's state.json still names it.

It knows no pipeline by name.  It looks at every `runs` folder one level under ~/.claude, plus every `runs_root` that a
`config.json` one level under ~/.claude names (a pipeline that keeps its runs elsewhere).  A run is in progress when its
state.json changed in the last 36 hours, its stage is not a finished one, and it says what comes next (a `next_skill`, a
`next_step` or a `todo.md`).  The newest such run is named by its folder path, or by the `command` field of its state.json
when the pipeline writes one.  With no run in progress it prints nothing.

RESUME_NOTE_ROOTS (folders separated by the system path separator) replaces the search, for tests."""
import json
import os
import time
from datetime import datetime
from pathlib import Path

CLAUDE = Path(__file__).resolve().parent.parent
FINISHED = {"done", "redo_delivered", "delivered", "complete", "completed", "closed", "wrapped", "released"}
WINDOW_S = 36 * 3600


def run_roots():
    override = os.environ.get("RESUME_NOTE_ROOTS")
    if override:
        return {Path(p) for p in override.split(os.pathsep) if p}
    roots = {p for p in CLAUDE.glob("*/runs") if p.is_dir()}
    for cfg in CLAUDE.glob("*/config.json"):
        try:
            root = json.loads(cfg.read_text(encoding="utf-8")).get("runs_root")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(root, str) and root.strip():
            roots.add(Path(root).expanduser())
    return roots


def newest_run_in_progress():
    best = None
    for runs in run_roots():
        for p in runs.glob("*/state.json"):
            try:
                st = json.loads(p.read_text(encoding="utf-8"))
                t = p.stat().st_mtime
            except (OSError, ValueError):
                continue
            if not isinstance(st, dict) or st.get("stage") in FINISHED or time.time() - t > WINDOW_S:
                continue
            if not (st.get("next_skill") or st.get("next_step") or (p.parent / "todo.md").is_file()):
                continue        # nothing says what comes next: not a run someone is working through (e.g. a raw recording)
            if best is None or t > best[0]:
                best = (t, p, st)
    return best


def main():
    best = newest_run_in_progress()
    if not best:
        return
    t, p, st = best
    run = p.parent
    command = st.get("command") if isinstance(st.get("command"), str) and st.get("command").strip() else ""
    facts = [f"{st['mode']} mode" if st.get("mode") else "", f"stage `{st['stage']}`" if st.get("stage") else "",
             f"video {st['video']}" if st.get("video") else "", f"last change {datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')}"]
    head = f"A {command} run is in progress" if command else "A pipeline run is in progress"
    note = f"{head}: `{run}` ({'; '.join(f for f in facts if f)})."
    todo_file = run / "todo.md"
    if todo_file.is_file():
        nxt_line = ""
        try:
            for ln in todo_file.read_text(encoding="utf-8").splitlines()[:15]:
                if ln.startswith("Next:"):
                    nxt_line = " " + ln.strip()[:320]
                    break
        except OSError:
            pass
        note += f" Read the run's to-do `{todo_file}` first (what is done and what is next).{nxt_line}"
    nxt = st.get("next_skill") or ""
    if nxt:
        note += f" Re-invoke the skill `{nxt}` (Skill tool) before doing anything else: its text may have been summarised away."
    else:
        step = f" (next step `{st['next_step']}`)" if st.get("next_step") else ""
        note += (f" This run names no skill to load{step}: take the next step from its state and to-do with the resume section "
                 f"of the command that made it.")
    note += f" Read `{p}` for the exact point reached; if this session is not working on that run, ignore this note."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
