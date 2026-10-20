## 6. Deliverables (Analyze Mode)
- **CapCut project `<name>`**: the editable master, with the text. Export the final from CapCut
  (Export → 1080×1920 or 720×1280).
- **`RUN/deliverables/video-NN-clean.mp4`**: the same edit without text, assembled locally.
  - Cut the clean video at the split points with `awl.py trim`.
  - Join the pieces and inserts with `awl.py concat --seams cut,…`.
  - A Recreate's clean carries the original audio whole (`restore-audio` over the joined result), and a
    with-inserts clean is never replaced by the generated-only `60-outputs/video-NN/clean.mp4`.
  - Every video of the run has both deliverable files in this one folder and a row in `README.md`.
- **`RUN/deliverables/video-NN-preview.mp4`**: a 720×1280 burn of the CapCut text layer over the clean video (CapCut's
  font, crf 16–18, the original audio stream-copied), for review; never the 540×960 capcut-cli proxy. An optional
  `video-NN-preview_1.5x.mp4` (the same at 1.5× speed) may sit beside it when the user wants a faster review.
- The project uses files from the run folder: keep the run folder.
