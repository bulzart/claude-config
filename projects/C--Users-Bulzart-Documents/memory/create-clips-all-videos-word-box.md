---
name: create-clips-all-videos-word-box
description: "user 2026-11-18 - every /create-clips video in the BOX look, long ones too, must use word-on-a-box, never the plain fallback; since 2026-11-20 a run can be the no-box look instead (user's pick at the start), then every video is no-box"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fdd08f84-168e-4132-9267-e792bc679631
  modified: 2026-11-20T03:42:51.471Z
---

User 2026-11-18 (after run 20261118-161031-kaicenat, where L02 fell back to the plain look because it had about 3,300 spoken words, over `captions.word_box_max_words` 3000): "all videos strictly should have word on a box, keep that in mind".

**Why:** the word-box is the user's chosen look (copied from Loupe video 04); a silent fallback to plain breaks it. The 3000-word limit is only a default in the EDL, not a real tool limit (L01 3,718 and L03 6,093 texts built fine).

**How to apply:** in every box-look build (cc-build-short / cc-build-long / cc-build-game) set `captions.style: "word-box"` and a high `captions.word_box_max_words` (e.g. 20000) in the EDL, and check `resolved.json -> captions.style` is word-box before reporting built; a build that resolved to plain is not done. Only a language the box cannot take (no spaces, right to left) may use plain, and the user is told. Related: [[capcut-text-preset-locked]], [[create-clips-caption-look]].

**2026-11-20:** until then this rule lived only in the README and memory: cc-build-long still said a long video "falls back to the plain look ... by itself". Fixed that day while adding the no-box look: cc-build-long, cc-build-game and cc-produce now say `word_box_max_words` 20000 and check the style; test_docs guards it. The code default stays 3000 (not raised). Since 2026-11-20 the user picks box or no-box at the start ([[create-clips-caption-look]]): in a no-box run every video is `style: "no-box"` (one text per caption, no word limit), and this rule applies to box runs.
