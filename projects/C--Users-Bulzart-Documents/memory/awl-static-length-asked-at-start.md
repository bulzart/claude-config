---
name: awl-static-length-asked-at-start
description: "user 2026-11-12: Static asks the video length at A5, after the niche family is locked and before any planning/generation: standard (niche references) or the user's own (total or +/- minutes, per batch or per video)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0ff74cb4-bc5e-4c0e-82b7-c94ab48b8c77
  modified: 2026-11-12T14:58:31.810Z
---

User 2026-11-12: in Static mode the user is asked for the videos' length way before generation and planning. If no niche is locked, lock the niche family first, then ask the length. Two choices: **standard** (based on the niche's references) and **user specific** (they may want 2-3 minutes more or less than the niche's preference). Planning and everything after continue from that answer.

**Why:** it replaces the 2026-11-07 rule "the user will not pick any length"; the user wants control of length per run (video 05 had to be redone to 15+ minutes after the agents chose a shorter one).

**How to apply:** `awl-analyze-study` A5 "Then the length" (AskUserQuestion header "Length", after `T static lock --niche`, before the language call; `more <run>` asks it right after the count); stored in `state.json → static.length_plan`; static §2/§4/§10 and J1 read it; `target_length_s` = the user's number or standard. Docs only, no toolkit change. Related: [[awl-niche-family-and-approach]], [[awl-static-whole-set-and-pace]].
