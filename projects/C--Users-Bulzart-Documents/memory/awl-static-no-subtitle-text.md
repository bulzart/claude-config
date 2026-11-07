---
name: awl-static-no-subtitle-text
description: "user 2026-11-07: no subtitle/caption-style text in any Static image (text on objects, books, logos, brands, screens is fine); prompts never hold caption words; T image text + the bottom edge viewed"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-07T09:59:50.938Z
---

User 2026-11-07, after nine stills of video 02 (run `20261106-063422-static-klein`) carried made-up subtitle lines: "try to push no captions or subtitles style text in any image generation at all, it can have text over objects,books,logos,brands,inside screens,or whatever, just not subtitles style text whatsoever, redo them again"; "also make sure to avoid this error in the future runs of the static mode".

**Why:** the plan prompts' sentence "the bottom fifth of the frame, where captions sit, holds only floor ..." made FLUX 3 Klein (no reference, no upsampler) draw a line of made-up letters across the bottom; such a still is unusable under the real captions.

**How to apply:** static §5 "No subtitle-like text, ever" and §8: no prompt holds caption, subtitle, lower third, title bar or text overlay (the answer's `prompt_overlay_words` stays empty), every prompt ends on the clean-picture sentence, `T image text` after the stills (one still re-read replaces only its row), and the bottom edge viewed (cut-off letter tops escape the OCR). Prompt words draw what they name: no "split picture" (panels), no place names on a map (written on, one over the wrong continent), the "people placed naturally" sentence only in a scene with people. Related: [[analyze-with-loupe-command]], [[awl-real-things-look-like-themselves]].
