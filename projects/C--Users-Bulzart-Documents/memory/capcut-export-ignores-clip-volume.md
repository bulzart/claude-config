---
name: capcut-export-ignores-clip-volume
description: "measured 2026-11-22: CapCut 9.8's export plays a video clip's own sound even at volume 0 (UI shows -inf dB); silence the media itself instead"
metadata:
  node_type: memory
  type: reference
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-22T01:25:35.761Z
---

Measured 2026-11-22 (create-clips music isolation, LT2 test exports in `C:\Users\Bulzart\Documents\stream-clips\validation\music-mode-20261122\exports`):
a main-track video clip written with `volume: 0` (our capcut-cli compile) or CapCut's own mute form (`volume: 0.0`, `last_nonzero_volume: 1.0`)
shows "-inf dB" in CapCut's timeline, yet the GUI export still plays that clip's sound at full level (the original under the cleaned song: -28.6 dB
left, the original's own level). An audio-track clip at volume 1.0 plays normally. Not tested: other volume values on video clips.

**How to apply:** never rely on a video clip's volume to mute in a CapCut project; give that clip media whose sound is already silent (create-clips:
a stream-copied silent copy of the chunk in `RUN/30-assets/mute`, same frames, the user's proposal), then verify by measuring the exported MP4,
not by reading the draft. See [[create-clips-music-isolation]] and [[capcut-desktop-automation]].
