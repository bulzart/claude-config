---
name: one-generation-up-to-15s
description: "Recreate videos with generated length up to ~15.4 s are always ONE generation (send the first 15 s); over that, smart 2+ generations with hand-offs, never side-by-side re-renders"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2f6ce97f-7243-4a3f-85ec-91fadec42799
  modified: 2026-11-05T03:56:06.144Z
---

User 2026-11-05 (run 20261104-225639-04, /analyze-with-loupe, Wan 3.0 Prime), strict: "videos 15s and under never do two generations but rather direct one, even if its 15.2s or 15.4s just send the 15s, but if its over that than we can do a smart 2+ generations, keep this strictly in mind".

**Why:** video-30 (one unbroken 15.0 s take) was split into two generations joined side by side; each re-render placed the Celsius can and the desk differently, so the can jumped at the seam "without any means". The earlier pilot rule (one generation per hard cut) also split short videos.

**How to apply:**
- Generated length (inserts excluded) up to 15.4 s: one generation, hard cuts ride inside Video 1 (named by order, never by time). 15.0–15.4 s: send the first 15.000 s, the video ends there (audio cut with a short fade).
- Over 15.4 s: as few clips as possible, split on the source's own hard cuts first; a seam inside one unbroken shot only with a hand-off (next clip starts from the previous clip's last frame / keyframe ladder), never a plain side-by-side join.
- This overrides the pilot lesson in that run's planner brief. Related: [[analyze-with-loupe-command]], [[awl-never-ask-decide-autonomously]].
