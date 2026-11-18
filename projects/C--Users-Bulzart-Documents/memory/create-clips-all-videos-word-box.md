---
name: create-clips-all-videos-word-box
description: "user 2026-11-18 - every /create-clips video, long ones too, must use the word-on-a-box caption look; never accept the plain-look fallback"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fdd08f84-168e-4132-9267-e792bc679631
  modified: 2026-11-18T22:05:26.942Z
---

User 2026-11-18 (after run 20261118-161031-kaicenat, where L02 fell back to the plain look because it had about 3,300 spoken words, over `captions.word_box_max_words` 3000): "all videos strictly should have word on a box, keep that in mind".

**Why:** the word-box is the user's chosen look (copied from Loupe video 04); a silent fallback to plain breaks it. The 3000-word limit is only a default in the EDL, not a real tool limit (L01 3,718 and L03 6,093 texts built fine).

**How to apply:** in every build (cc-build-short / cc-build-long / cc-build-game) set `captions.style: "word-box"` and a high `captions.word_box_max_words` (e.g. 20000) in the EDL, and check `resolved.json -> captions.style` is word-box before reporting built; a build that resolved to plain is not done. Only a language the box cannot draw (no spaces, right to left) may use plain, and the user is told. Related: [[capcut-text-preset-locked]], [[create-clips-caption-look]].
