## 5. QC of the project
- Read the project back with `capcut_read_timeline`:
  - the generated pieces are contiguous, and each insert sits exactly at its split;
  - the total = generated length + the inserts;
  - every text event is at its planned time and position;
  - `T capcut-text-style --draft "<store>/<name>" --check` reports 0 texts off the house style;
  - no text layer contains an emoji.
- On the preview (`atp.py qc --video <capcut-preview.mp4> --out <dir> --expect-size 540x960`, plus
  its storyboard), check:
  - the cut into and out of every insert, and the sound;
  - text presence and timing;
  - dense sheets (15 to 30 fps) of every transition, insert start and end, overlay start and end and the
    first second: no frame of the replaced performer, no held frame, no stray rectangle, halo or
    brightness step (CE-016, CE-025, CE-026);
  - audio (Recreate): the original track is one segment, the duration equals the reference's, and its
    hash or a null test against the source audio matches (CE-024).
- Fix through the MCP: read → edit → `capcut_validate` → `capcut_save` → §4 again. A save refused
  because the draft changed on disk → `capcut_discard`, then rebuild the edits.

