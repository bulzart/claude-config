---
name: create-clips-caption-look
description: "user 2026-11-13: /create-clips captions = the Loupe word-box preset (spoken word on a rounded colour box, white words black outline), free font family + highlight colour matched to each video, size small/normal for phone and tablet viewers (auto 4.6% of the smaller side), never large"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-13T16:20:14.237Z
---

User 2026-11-13, after seeing a BLAST frame with plain outlined captions next to a Loupe frame (white words, black outline, the spoken word "TEN" on an orange rounded box): "for captions we should use the same background color preset and spoken word highlight style the analyze with loupe uses but with the possibility to use whichever font family or highlight color it matches the appearance".
Then: "use the font size that is neither too small nor too large but also take in mind that most of the viewers may be watching from the phone or tablets, go with whats best but preferable dont use large fonts, go to the most optimal in the small/normal side".

**Why:** the Loupe look is the one the user already likes; CapCut draws a box behind a whole text only, so the word being spoken is its own text (one CapCut text per word and state, about 2.5 per spoken word); phones and tablets make a large font cover the picture.

**How to apply:**
- Default `captions.style: "word-box"` (scripts `cc_wordbox.py`, preset box radius 0.3, pad 0.08, v_offset 0.15, gap 0.7 em); the production agent picks `font_family` (+ `font_style`/`font_file`) and `highlight_color` per video to match its look and writes why in `captions.why`; the user's own pick = `captions_font` / `captions_color` arguments stored in `state.json`. Orange #FF7A1A and Montserrat Bold are only the fallback.
- Size = `"auto"`: the font's em at `size_em_pct` 4.6 percent of the picture's smaller side (guide 4.0 to 5.0, never above): CapCut size about 5.5 on 1080p and 10 on 1080x1920. Never a big fixed size; `cc.py captions` reports `vs_guide`.
- Plain look (one text per caption) is the fallback for languages without spaces or right to left and above `word_box_max_words` 3000 spoken words (about 17 minutes of speech), with the reason in `resolved.json -> captions.style_reason`.
- Not verified by any tool: how CapCut 9.7 draws the look (the structure was checked: boxed fields, lint 0 errors). The user opens the demo project `13_Nov_2026_blastpremier_L01_wordbox` in CapCut to judge it.

Related: [[create-clips-one-research-agent]], [[create-clips-capcut-composition]], [[awl-static-word-box-captions]], [[atp-product-colours-and-preview]]
