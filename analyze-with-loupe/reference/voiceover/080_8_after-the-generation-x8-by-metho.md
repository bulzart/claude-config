## 8. After the generation (X8), by method

`conform`, `trim` and `concat` keep the generation's own sound, so every step below runs on the clean picture
(`60-outputs/video-NN/clean.mp4`). `T voiceover align --generated <a file> --voiceover <the take> --out <aK>/vo` measures where the take lies in
the file's sound: `global_offset_s` and `global_corr`, the per-window offsets (only in `vo-align.json`: read them when the summary is unclear), `window_spread_s`, `drift_s_per_10s`,
`windows_off_global` (listed against `--tol`), the speech span of both, and `vo-align.png`. A file whose soundtrack **is** the take reads as a
correlation near 1 at an offset near 0. Numbers only: you read them and decide.

- **native.** Align the clean picture against the take. Its sound is the take (near 1 at near 0): keep it, nothing is mixed. The model altered
  it (another voice, added sound, a shift): lay the exact take back with `T voiceover mix --picture <clean> --voiceover <the take> --offset
  <global_offset_s> --bed mute --out 60-outputs/video-NN/with-voiceover.mp4` (the same take, so the driven lips stay on it). Lips that do not
  follow the words (X9) are a finding: the fix is a sync pass on the same clip (as in lipsync), under the QC-fixes choice (item 27), or one
  regeneration.
- **lipsync.** The first generation passes its picture checks (X9) first. Then the sync pass: write `50-requests/video-NN-sync-request.json`
  (`{"model":"sync_so","medias":[{"role":"input_video","value":"<the accepted clip's job id>"},{"role":"input_audio","value":"<the take's media id>"}],"sync_mode":"silence"}`),
  run `awl-submit` (X5 preflight, then X7 with `T ledger begin --video NN-sync`: the same lane, one job in flight), download it to
  `60-outputs/video-NN/aK/synced.mp4`, `T conform` it (a no-op at 720×1280), and align it against the take: near 1 at near 0 means its
  soundtrack is the take; anything else gets the exact take laid back on it as in native (`--bed mute` at the measured offset). The synced
  file is the clean picture from here on. A video in the overlay form (no visible speaker) gets no sync
  pass: it is mixed as in overlay.
- **overlay.** `T voiceover mix --picture <clean> --voiceover <the take> --offset <the voice's planned start, usually 0> --bed keep --bed-gain 0.3 --out 60-outputs/video-NN/with-voiceover.mp4`
  (`--tempo` for a take a little long, §4 step 4). It also writes `with-voiceover.vo-track.wav` (the take as placed, the picture's length)
  for the CapCut track, and reports `vo_speech_end_on_picture_s` and `vo_speech_cut_s` (above 0 is cut speech).
- **The fallback**, only when a sync pass is refused, flagged or failed twice: align the take to the model's own speech, read the offset as
  for `T sync-check` (one steady offset is usable, drift is not), and mix it with `--bed mute` at that offset; the lips are then only as close
  as the model's own speech was. Say so in the brief, in `result.json → voiceover` and in the wrap-up.
- **Multi-clip:** each clip with its own take, by the same method (a clip's sync pass: `50-requests/video-NN-cK-sync-request.json`,
  `--video NN-cK-sync`, the same lane); the results joined with `T concat` on the same seams.
- What the deliverables carry: the file whose sound is the take (the clean native picture, the synced file, or `with-voiceover.mp4`);
  `result.json → clean` names that file.

