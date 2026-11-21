---
name: create-clips-shorts-always-9-16
description: "user 2026-11-14: shorts are ALWAYS 9:16 (1080x1920), whatever the source; edl-check warns and capcut-build lists a problem when a short's canvas is not 9:16; long videos stay 16:9"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-21T16:11:09.451Z
---

User 2026-11-14 (mid-turn, while the shorts level was being added): "also shorts should always be 9:16".

**Why:** the canvas of a short was only a default (`capcut.short_canvas` 1080x1920 in config.json) that an EDL's own `canvas` could override, and nothing checked it; a wrong canvas means a wrong CapCut project and a rebuild.

**How to apply:**
- Docs: cc-build-short ("always 9:16 (1080x1920): no other canvas, no 16:9 or square short"; Never: no other canvas, no `native` layout), edit-craft.md Layout section, clip-economy.md ("Always 9:16, with a safe area"), capcut-build.md, router rule 5, README.
- Code (small, the first invariant in code for shorts): `cc_edit.py` `_is_9_16()`; `plan_edl` adds a WARNING when a short's canvas is not 9:16 (so `edl-check` is not ok until the EDL's `canvas` is removed or fixed), and `capcut-build` lists a PROBLEM when a short's resolved canvas is not 9:16. Tests in `tests/test_edit.py` (a 1920x1080 short warns, the default and an explicit 1080x1920 pass, a long 1920x1080 is untouched, capcut-build lists the problem) and `tests/test_docs.py`.
- THE FRAME (user 2026-11-21, "Fix Shorts Framing"): by default a short shows the WHOLE source picture fitted inside the 9:16 canvas, centred, solid BLACK above and below (`fit`: 1920x1080 -> 1080x608 at y 656-1264); never crop, zoom-to-fill, stretch, split or detach the face cam. `fill` / `fit-blur` only when the user picks it for the run (`state.json shorts_layout`). The old default `fill` around the face cam at zoom 1.5 showed 21% of the width (S01, 2026-11-21). Enforced in code: `plan_edl` refuses another layout or a resting zoom (warning), a punch-in keeps its focus and never grows below the picture's bottom edge, captions are placed in the black band under the picture (`captions.placement`), `capcut-build` reads the frame back (`read_back.framing`), `export-check` compares exported frames with the source (`checks.framing`, framing-sheet.jpg).
- Long videos stay 16:9 (`native`). Game mode has no shorts.
- Not enforced by code: the 180 s cap of a short.

Related: [[create-clips-shorts-level]], [[create-clips-shorts-edit-freedom]], [[scripts-gather-agents-decide]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: a short is ALWAYS 9:16 (1080x1920); edl-check warns and capcut-build lists a problem otherwise (small code guard in cc_edit.py); long videos stay 16:9

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: a short is ALWAYS 9:16 (1080x1920); edl-check warns, capcut-build lists a problem; long videos stay 16:9
