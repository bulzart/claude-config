---
name: references-built-per-generation
description: "AWL runs: every generation builds its own reference image/video files in RUN/55-references/video-NN/aK/ (named by role) and uploads them fresh, so the user can see what goes in; old built references were deleted 2026-10-22"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fd23b3ce-bd75-4669-95d5-20d1bbdbcdef
  modified: 2026-10-21T23:40:10.182Z
---

User 2026-10-22 (Celsius run 20261021-224049-21): "delete all the references that you build till now and for each generation build its references so i might see whats going under the hood (just the image/video reference files not the .md documents or other data collected)".

**Why:** the user wants to inspect exactly which files each generation sent (original video, face crop, can view).

**How to apply:** per generation (attempt aK, clip cK) a folder `RUN/55-references/video-NN/aK/` with `video1-original.mp4`, `image1-character-<C>-head.jpg`, `image2-product-<P>-front-padded.png` (no placement preview since 2026-10-28: [[awl-original-only-reference]]); uploaded fresh, never reusing an earlier generation's media ids. Only image/video reference files are ever deleted, never .md/.json data or analysis frames. Still show the paths before an unapproved upload ([[show-references-before-upload]]). Done for this run only; not yet written into the pipeline (offer it). Related: [[awl-original-only-reference]], [[always-full-paths]].
