---
name: no-blur-no-censor-ever
description: "/analyze-with-loupe contract item 37 — the pipeline never blurs, pixelates, smears, covers or censors anything in a video, before or after generation, whatever a guardrail says"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 502ff4d9-6b7e-4186-a9dc-8c2735ff1ac9
  modified: 2026-11-12T18:59:58.308Z
---

User 2026-11-12: "remove any blurrings that the video do, no matter the guardrails or some other restrictions the pipeline should never blur anything in the video, before or after the generation", then "no bluring or censoring whatsoever".

**Why:** the user does not want any blur, pixelation, cover or censor in the videos the pipeline makes. Earlier rules already said "removed, never blurred" for competitor marks, but real blurring still lived in the tools (blurred pad fill, `delogo` smear) and in one model guide's prompt wording (Kling: "background text … blurred and unreadable"); the user wants it gone completely, guardrails included.

**How to apply:** it is contract item 37 in `commands/analyze-with-loupe.md` (every skill, `reference/generation-system/` §9b). `conform --mode pad` is plain black bars; `clean --delogo` was removed (refuses with a message), `clean --crop` stays; CapCut filters/effects/transitions/masks/canvas fills never blur or hide (a mask only shapes a layout panel); prompts never say blur/defocus/pixelate/cover/censor; a banned element is dismissed with its reference or removed by a named clause ("Remove only …", "plain unbranded … of the same colour"); QC step 5j treats a blur/mosaic/censor bar as a defect. The camera's own focus, depth of field and motion blur are the scene's, not a finding. Tests t01/t02 guard it. Any new tool, model guide or CapCut step must respect it; update `Documents/prompts/analyze-with-loupe.txt` with any change ([[atp-build-prompt-sync]]). Related: [[atp-brand-guardrails]], [[atp-no-tool-caption-removal]], [[awl-user-folders-read-only]].
