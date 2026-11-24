---
name: create-video-check-commands-write
description: "2026-11-24 incident - /create-video's *-check CLI commands are NOT read-only (plan-check wrote into the finished Garbo run); on a finished production call the facts functions by import, never the CLI"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T14:29:32.876Z
---

`static_core.py plan-check` (and the other gate commands: shot-check, audio-check, media-check, timeline-check,
release-check...) write their gate record into the run (e.g. 40-plans/video-NN/plan-check.json) and move
state.json's `stage` forward (advance_stage re-saves the whole file). On 2026-11-24 a "read-only" plan-check on the
finished Garbo run (C:\Users\Bulzart\.claude\static-studio\runs\20261121-160057-youtube) changed state.json (stage
planning -> script_checked) and created plan-check.json. Undone byte for byte against the morning baseline (sha256), and
reported to the user.

**Why:** the user's rule: existing/finished productions are read-only ("No completed production is modified").

**How to apply:** to check a finished production, import static_core and call the facts functions (plan_facts,
shot_facts, audio_facts, media_gate, timeline_facts...) or run the command on a COPY of the run. Before touching any
production, take a size+mtime_ns+sha256 baseline of its files and re-check it after (scratchpad recheck script pattern).
Related: [[create-video-verify-real-paths]].
