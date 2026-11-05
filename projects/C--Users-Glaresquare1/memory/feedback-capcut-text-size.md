---
name: feedback-capcut-text-size
description: "CapCut overlay text size — standard 10, but 11 when a video has only a little text (≤5 words on screen at once); one size per video"
metadata:
  node_type: memory
  type: feedback
  originSessionId: c1639feb-dd77-47ca-950d-178277c7920f
  modified: 2026-11-05T08:14:22.661Z
---

Given 2026-10-29: "our standard text size is 10 but when there's only few text to be placed then use font size 11" (CapCut edits).

Implemented in /analyze-with-loupe as part of the house text style: `awl.py capcut-text-style` (run by `capcut-repair`)
sets one size per video — 11 when at no moment more than 5 words are on screen (texts shown together counted together)
and every line fits within 82% of the frame width at 11, else 10. Thresholds in `config.json → capcut.text_style.short_text`.
Calibration: CapCut draws size s with a font of ~0.00575·s × frame width (System font), measured on CapCut's own covers.

**Why:** at size 10 a short line looks small on a 9:16 frame; long multi-line hooks need 10 to fit.
**How to apply:** any CapCut text placement for this user (any pipeline or a manual edit): 10 by default, 11 for a video
whose text is only a few words; keep one size across a video's texts. Related: [[feedback-pipeline-rules]].

**Exception, /analyze-with-loupe Static (user, 2026-11-05):** "the agents are free to chose any font preset, size, color and
family or whatever they like while editing the video and are not constrained like we do with recreate ... everything is data
driven (from the references) and nothing is predefined". In Static the text look (font, size, colours, outline, box, case,
highlight, animation) comes from the references' spec; no house size or preset (`capcut-repair --keep-text`, `T capcut-font`).
Recreate, Create, Free and Edit keep 10/11 and the locked preset.
