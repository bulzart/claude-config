---
name: create-clips-lexicon-scope
description: "/create-clips captions (2026-11-20): lexicon entry \"scope\":\"streamer\" is never applied to words printed in the game's subtitle (voices facts); plain pairs apply to every voice"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-20T17:18:54.140Z
---

`{"from": "Jack,", "to": "Chat,", "scope": "streamer"}` = a fix for how Whisper hears the streamer; cc_wordbox.apply_lexicon skips it on words flagged `screen` (cc_voices.screen_words: label S AND the matched subtitle line prints that word, so a wrong OCR read can never block a fix on a word the screen does not show). Unattributed words still get it (no subtitle is not proof of the streamer). Plain pairs / scope "any" = transcription fixes for every voice (game names). No current voices facts (older runs) = every fix everywhere, as before. Same fix written as pair + streamer object = one rule, streamer scope. Skipped places: captions.json lexicon.kept_on_screen (builders read it).

Verified on caseoh copies: the run's own lexicon (all pairs) gives identical captions with and without facts; a broad streamer-only "Jack"->"chat" keeps "heart of Jack of Hearts" (C0007, rec 1157.75) and still makes "Chat, why" (C0014, 2352.16). The caseoh lexicon.json was NOT changed (marking its streamer entries is the user's call).

Related: [[create-clips-caption-look]], [[create-clips-speaker-facts]], [[create-clips-second-look]]
