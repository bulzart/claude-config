---
name: create-video-narration-direction
description: "/create-video narration rules from the user's 2026-11-20 brief: per-video narrator lock, v4 has no speed, selective tags, no silence padding, paid trials only after approval"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T13:12:55.039Z
---

User 2026-11-20 (master narration brief, implemented as tag static-studio-narration-1): the narrator is an editorial choice per video for its locked treatment (a series may share a voice on purpose); every TTS request takes voice, model and settings from `60-voice/video-NN/voice-lock.json` (no command-line override, no global `--delivery` prefix; a change is `voice-pick --replace --reason`). Stability is chosen for the narrator, never to move pace: Eleven v4 applies no speed setting (official docs), so pace is measured and the script sized to it. Tags only where the writing can't carry a change, each explained under "Delivery and tags". Every hold over 1 s has a `pause_purpose` and the cold reader is shown the holds: silence never pads an underwritten script, but there is no universal maximum. Parts follow the beats (about 3,500 characters, a guideline). Every line must be heard (number-normalised alignment, a Whisper medium re-hearing of a missed line) and no tag read aloud. In CapCut the narration is the edit plan's file at 0 s, speed 1, untrimmed. Credits: ElevenLabs' model rate plus the live balance, every billed request in the run's ledger; Voice Design priced first.

**Why:** the user wants a narrator that feels human ("expressive but not theatrical", "faster isn't necessarily better"); the audit found controls that did nothing or could slip (speed, the global tag prefix, 8,000-character parts split mid-beat, silence padding, an unchecked CapCut narration track).

**How to apply:** keep these when editing static-studio. Never add a speed control, a global tag or a fixed stability. Paid narration tests are designed and priced first (`narration-trial` dry run with `--check-balance`) and run only after the user's explicit yes; the 2026-11-20 plan budgeted about 3,000-4,000 credits. Related: [[create-video-adaptive-niche-guardrail]], [[awl-elevenlabs-v4-no-edit]], [[scripts-gather-agents-decide]], [[wpm-calibrate-from-transcripts]].
