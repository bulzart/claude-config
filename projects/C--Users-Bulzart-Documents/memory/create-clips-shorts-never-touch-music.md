---
name: create-clips-shorts-never-touch-music
description: "user 2026-11-21: Shorts keep their audio exactly as recorded; no music identification, risk analysis or separation for a short, ever"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T16:10:55.348Z
---

The user, 2026-11-21 (mid-turn): "For Shorts, never isolate, suppress, remove, replace, or otherwise modify music, even when the selected footage contains
known copyright-risk songs. Preserve all original music and audio exactly as recorded; skip music identification, copyright-risk analysis, and separation
processing for Shorts videos entirely."

**Why:** the user's call for short-form; it overrides the long-video music rules ([[create-clips-music-isolation]]) for every short.

**How to apply:** `cc.py music` skips any EDL of kind short (the resolver's default kind) and takes an older run's music patch back out of a short (backup
`edl.pre-music.json`); cc-produce's batch detection gets the LONG videos' spans only; the research step is for long videos; a short's report says
"original audio, shorts are not processed for music". Never propose music removal for a short.
