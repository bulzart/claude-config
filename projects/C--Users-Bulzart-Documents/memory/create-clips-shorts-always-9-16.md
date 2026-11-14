---
name: create-clips-shorts-always-9-16
description: "user 2026-11-14: shorts are ALWAYS 9:16 (1080x1920), whatever the source; edl-check warns and capcut-build lists a problem when a short's canvas is not 9:16; long videos stay 16:9"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T05:12:27.139Z
---

User 2026-11-14 (mid-turn, while the shorts level was being added): "also shorts should always be 9:16".

**Why:** the canvas of a short was only a default (`capcut.short_canvas` 1080x1920 in config.json) that an EDL's own `canvas` could override, and nothing checked it; a wrong canvas means a wrong CapCut project and a rebuild.

**How to apply:**
- Docs: cc-build-short ("always 9:16 (1080x1920): no other canvas, no 16:9 or square short"; Never: no other canvas, no `native` layout), edit-craft.md Layout section, clip-economy.md ("Always 9:16, with a safe area"), capcut-build.md, router rule 5, README.
- Code (small, the first invariant in code for shorts): `cc_edit.py` `_is_9_16()`; `plan_edl` adds a WARNING when a short's canvas is not 9:16 (so `edl-check` is not ok until the EDL's `canvas` is removed or fixed), and `capcut-build` lists a PROBLEM when a short's resolved canvas is not 9:16. Tests in `tests/test_edit.py` (a 1920x1080 short warns, the default and an explicit 1080x1920 pass, a long 1920x1080 is untouched, capcut-build lists the problem) and `tests/test_docs.py`.
- A whole 16:9 frame in a short = `fit-blur` (the frame in the middle of the 9:16 canvas on a blurred copy); the canvas stays 9:16. Long videos stay 16:9 (`native`). Game mode has no shorts.
- Not enforced by code: the 180 s cap of a short and the layout choice; only the canvas is.

Related: [[create-clips-shorts-level]], [[create-clips-shorts-edit-freedom]], [[scripts-gather-agents-decide]].
