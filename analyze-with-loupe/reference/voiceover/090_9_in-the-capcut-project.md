## 9. In the CapCut project

- **native** and **lipsync:** the clip carries the voice: the clip placed is the file whose sound is the take (§8: the kept clean picture,
  `with-voiceover.mp4` after a lay-back, or the synced file); keep its audio at 1.0, never re-timed, cut or duplicated on another track.
- **overlay:** the take on its own audio track, `capcut_add_audio {file:"<…/with-voiceover.vo-track.wav>", atSec:0, trackIndex:<voice track>, volume:1.0}`
  (already placed, the picture's length; multi-clip: each clip's track at its clip's start), and the clip's own sound at the planned bed
  volume (about 0.3). The clip placed is the clean picture, never `with-voiceover.mp4`, which already carries the voice (it would double).
- **Inserts** (`generation-system.md` §3c): an overlay voice track is split at the same points as the clip, so each phrase stays on its
  picture while the insert plays its own sound; X1 puts every insert split point in a pause of the take (§4 step 5). A native or lipsync
  clip's voice splits with the clip.
- The soundtrack of `capcut-assembly.md` §3b at about 0.25 under the voice; the sound effects on their hits, never on a word.
- Spoken captions, when the text plan has them: the take's spoken words timed to its phrases (plus the mix offset), as text layers in the
  house style (centred, no emoji).
- `capcut_read_timeline`: the voice audible at 1.0 (the clip's audio for native and lipsync, the voice track for overlay), nothing muted
  by mistake.
- `deliverables/video-NN-clean.mp4` carries the voice exactly as the project places it (overlay: the voice track mixed over the clean edit);
  the preview burns the text over it.

