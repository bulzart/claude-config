---
name: create-clips-caption-masks
description: "user 2026-11-14: /create-clips captions ALWAYS type profanity and slurs with one asterisk (f*ck, f*ggot, sh*t, p*do, g*y); the list is create-clips/data/caption-masks.json plus the EDL's captions.mask_terms; audio is never edited"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T03:48:50.006Z
---

User 2026-11-14 (create-clips session): "words such as fuck, faggot, pedo, shit, gay and more always write in captions like f*ck, f*ggot or similarly" (in the same message: push the claude config repo on branch pc). The old rule only masked "the hardest words" as first letter + stars (S***), and only when a platform limit worried the user; ordinary swearing stayed unmasked in captions.

**Why:** the user gave no reason (the old rule's reason was platform limits on a video); do not invent one.

**How to apply:**
- Style: ONE asterisk replaces the first vowel after the first letter (fuck f*ck, shit sh*t, faggot f*ggot, pedo p*do, gay g*y, bitch b*tch); no such vowel: the second letter (ass a*s). Code: `cc_edit._star`, `_mask_word`, `mask_lists`, `_masked_tally`; the case rule (upper) runs after, so the caption shows F*CK.
- The list is the user's own file `~/.claude/create-clips/data/caption-masks.json` (`anywhere` stems, with the `bad[ass]` bracket form for compounds, and `whole_word` forms for short or ambiguous words such as ass, gay, pedo, cunt); the code holds no word ([[no-hardcoded-names-in-scripts]], [[scripts-gather-agents-decide]]) and a missing or broken file is a loud error, never a silent skip. Per video the agent adds words in the EDL's `captions.mask_terms` (exact lower-case forms) after reading the cues once; `T captions` answers `masked` (as typed, with counts), which is what the wrap-up README lists.
- Not masked on purpose: ordinary game talk and mild words (kill, die, hell, damn, crap); the user can add any in the file. Titles, descriptions and chapter names were not covered (not asked). Audio is never edited.
- The house font (Luckiest Guy) draws the asterisk (checked). Tests: `tests/test_masks.py` (plus test_wordbox, test_edit, test_docs). The rule text: reference/safety.md section 3, edit-craft.md, game-edit-craft.md, the README, router rule 6, the three build skills, cc-produce, cc-wrapup.
- Real data (run 20261114-010840-ishowspeed): L01-v3's captions held 7 such words unmasked (sh*t x4, b*tch, f*ck, f*cking) and S03 one; they were built before the rule. A rebuild as a new project was offered to the user, not done unasked.

Related: [[create-clips-caption-look]], [[create-clips-blur-only-gore-distress]]
