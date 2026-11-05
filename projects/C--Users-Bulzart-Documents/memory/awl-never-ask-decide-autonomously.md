---
name: awl-never-ask-decide-autonomously
description: "During pipeline runs the user wants no questions — decide every choice (re-runs, spots, fallbacks) yourself and report it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6cbd9032-18a8-4ac2-bf9d-dc68a46bea88
  modified: 2026-10-27T23:26:09.502Z
---

User, 2026-10-28, mid /analyze-with-loupe run (Celsius Recreate), when asked whether to re-run a flagged pilot video: "you decide for every turn, dont ask me anything keep it on your own".

**Why:** the user wants the run to proceed autonomously; questions stall it while they are away.

**How to apply:** once a run is under way, make every decision yourself (re-runs of flagged videos, anchor/spot choices, fallbacks, planner conflicts, cost-bounded retries) by the pipeline's own rules and the order of authority, write the reason in the brief/plan, and tell the user afterwards in one line. Only the start-of-run setup questions the command itself requires (mode, model, inputs, counts) were answered before this; do not add new mid-run questions. Related: [[show-references-before-upload]] (no upload approval stop), [[analyze-with-loupe-command]].
