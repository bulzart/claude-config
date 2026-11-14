---
name: create-clips-shorts-edit-freedom
description: "user 2026-11-14, streamer shorts: zoom, sound effects and the words per caption are the agents' call; no count or spacing; encouraged where there is room and it fits, never forced where there is none or it feels off"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T04:59:19.679Z
---

User 2026-11-14, after the shorts logic was explained (three of its lines: "Captions show three words at a time in the house look", "Zoom is at most one punch-in every 6 to 8 seconds, on the beat that carries the joke", "Sound effects are at most one per 8 to 10 seconds, never over the joke's word and none on real pain"): "just these need to change ... the agents decide on their own when to zoom, or use a sound effect, and also encourage to do so if there is space to do so but not strictly do them if there's no space at all and it seems off the context to use sound effects or zoom to a specific person for example or a specific object or whatever".

**Why:** fixed counts and spacings (one zoom per 6 to 8 s, one sound per 8 to 10 s, three words) made the edit rule-driven; the user wants it judged from the moment, with effects used when they fit and left out when they would feel forced.

**How to apply:** docs only (the scripts never enforced counts: `edl-check` has no zoom or sound density check, and `merge_captions` lets the EDL's captions block override `max_words`/`max_chars`). Zoom and sound effects in a short: no count, no spacing; use them where there is a beat and room (a gap in the speech for a sound, something worth pushing in on for a zoom), several when the clip has room, nothing where there is none or it would feel off (a push-in on a person or object that is not the point, a meme sound on something heavy). Still fixed (content rules, not frequency): never a sound over the joke's word, none on real pain, nothing with a religious feel, the voice stays on top.
Captions: the house look (Luckiest Guy, the word box, size auto) is unchanged; only the words per caption became the agent's call (about 3 by default, another count set in the EDL when the speech calls for it). The user listed the captions line without saying what to change, so this is my reading of it.
Not asked, left as is: long videos keep "a few zooms, a handful of sounds". Where: `reference/clip-economy.md` (the short section), `reference/edit-craft.md` (zoom, sound effects, lines), skill cc-build-short; checks in `tests/test_docs.py`.

Related: [[create-clips-caption-look]], [[scripts-gather-agents-decide]], [[create-clips-pipeline]].
