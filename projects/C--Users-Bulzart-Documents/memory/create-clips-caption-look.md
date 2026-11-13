---
name: create-clips-caption-look
description: "user 2026-11-13: /create-clips captions = COPY of Loupe video 04's look: Luckiest Guy ALWAYS (never a font per video), upper case, outline 0.18 + shadow, word on a rounded box (0.3/0.08/0.15/gap 0.55); only the box colour is free; size small/normal for phones (auto 4.6%)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-13T16:43:20.518Z
---

User 2026-11-13, first: "use the same background color preset and spoken word highlight style the analyze with loupe uses [frames] but with the possibility to use whichever font family or highlight color it matches the appearance", and "font size neither too small nor too large ... most viewers on phone or tablets ... preferably dont use large fonts, go to the small/normal side".
Then, after opening the demo project in CapCut and screenshotting our frame next to Loupe video 04's (run `20261106-063422-static-klein`): "the highlight is way too off and big in comparison with the fonts, and always use the same font family as they used in that video". This SUPERSEDES the free font family.

**Why (root cause, found by reading the Loupe code and the video-04 timeline):** the box numbers were tuned with the user on Luckiest Guy. CapCut boxes the WHOLE LINE of a text (ascent + descent), so the font's metrics decide the box's size and place. Luckiest Guy: line 1.0 em, ascent 704 / descent 297, capitals as tall as lowercase. Barlow Black: line 1.2 em, x-height 0.52 em, baseline lower in the line, so the same numbers gave a box 2x the word's height, off it (our demo). Our as-is lowercase text and thin outline made it worse.

**The look (video 04's `captions` + `word_box` in `40-briefs/video-04-timeline.json`):** font `LuckiestGuy-Regular.ttf` (Loupe fonts folder), upper case, fill #FFFFFF, black outline 0.18, shadow on, box radius 0.3 / alpha 1 / style 0 / pad 0.08 / v_offset 0.15 / gap 0.55 em (our old default gap 0.7 was an earlier Loupe value), 3 words a caption, entrance mini-zoom 0.12 s (ours: fade-in in shorts only), Loupe size 5.5 on 16:9 / 10 on 9:16 (em about 5.6%).
**How to apply:**
- Never put a font in an EDL; the one exception is a character Luckiest Guy cannot draw (no Slavic/Turkish letters, Cyrillic, Greek: `cc.py captions` lists `font_missing_glyphs`, says `house_font`; `capcut-build` makes it a problem). The user's per-run font option `captions_font` was removed; `captions_color` (box colour) stays, and the agent matches the colour to the video.
- Our size stays `auto` = em 4.6% of the smaller side (CapCut 4.5 on 1080p, 8.0 on 9:16 in this font), about 20% smaller than Loupe's own 5.5/10: a number to change if the user wants Loupe's size.
- Plain fallback (languages without spaces, over `word_box_max_words` 3000 words = about 23 minutes of this broadcast's talk) uses the same font, outline, shadow and case.
- Game mode names come out in capitals (TESES, M0NESY, KARRIGAN); Luckiest Guy draws lowercase as near-capitals anyway.
- Not verified by any tool: CapCut's drawing. A project whose first frame has a boxed word (the demo `13_Nov_2026_blastpremier_L01_loupe_look`) lets me read CapCut's own `draft_cover.jpg` after the user opens it once. The first demo `..._L01_wordbox` (Barlow) is the "before" and still in the store.

Related: [[create-clips-one-research-agent]], [[create-clips-capcut-composition]], [[awl-static-word-box-captions]], [[always-full-paths]]
