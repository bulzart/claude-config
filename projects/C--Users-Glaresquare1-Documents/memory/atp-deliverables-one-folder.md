---
name: atp-deliverables-one-folder
description: Every /analyze-then-pick run puts all finished videos together in the run's deliverables folder
metadata:
  type: feedback
---

Put every finished video of a run in one folder, always `RUN/deliverables/` (`video-NN-clean.mp4` with inserts and original audio, `video-NN-preview.mp4`, plus a README table).

**Why:** the user asked for it at the end of the 2026-10-10 run so they find all videos in one place instead of per-video 60-outputs subfolders.

**How to apply:** at wrap-up, copy each video's final files into `RUN/deliverables/` (never overwrite a with-inserts version with a generated-only clip: build the clean file from pieces + inserts + original audio) and say the path. Related: [[atp-caught-errors]].
