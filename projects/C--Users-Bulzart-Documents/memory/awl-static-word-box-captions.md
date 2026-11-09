---
name: awl-static-word-box-captions
description: "user 2026-11-09: Static captions put the word being spoken on a coloured box with slightly rounded corners (CapCut-preset look, the box moving word to word); built by T capcut-word-box from the plan's captions.word_box"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-09T02:27:45.229Z
---

User 2026-11-09, on video 03 of run `20261106-063422-static-klein`, with a CapCut screenshot (white caps line, the spoken word "APPLICATION" on a purple box): "do it like that, for every word that is spoken at the moment the narrator is speaking then use that preset that puts a color behind the word and a round radius ... the radius has to be a bit round too in the corners".

**Why:** the user wants the karaoke-style box that follows the voice word by word, not keyword colouring.

**How to apply:** the plan's `captions.word_box` {color, alpha, round_radius, style, gap_em, why} (static §5, §7); S4 builds the captions with `T capcut-word-box --draft … --run … --video NN [--replace subtitle]` (one CapCut text per word, since CapCut boxes a whole text only; the box on the word whose narration time is now), then `T capcut-font` per `wordcap-*` track and `T capcut-text-anim` only on `-in` tracks. `highlight_words` empty (an orange word on an orange box vanishes). Video 03 used the video's heat orange #FF7A1A, round_radius 0.3, gap 0.7 em (the colour was my pick; the screenshot's box was purple). CapCut sizes a text by its LINE (ascent + descent = CAPCUT_FONT_PER_SIZE x size x canvas width), so each font's em differs (`_capcut_em_px`); my first build used Anton's em for Luckiest Guy and the user saw the words "all over each other". CapCut's box reaches ~0.35 em past its word and covers the descent (sits low). Opening a project in CapCut 9.7 writes a root template-2.tmp that capcut-cli reads first: the toolkit writes all root documents, and repair syncs the nested copies. Videos 01 and 02 still have the old captions unless the user asks. Related: [[awl-static-no-subtitle-text]], [[analyze-with-loupe-command]].
