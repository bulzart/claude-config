---
name: atp-run-19oct-can-realism-regen
description: "Run 20261019-235823-19 (Celsius, Wan 3.0 Prime, 20 videos): user said the cans of videos 01-04, 07, 08 look pasted; fixed 2026-10-20 with photoreal guide plates; videos 05, 06, 09-20 still on the old flat guides until the user decides; the lesson is not yet in the references"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T21:05:38.321Z
---

User report 2026-10-20 on the run `20261019-235823-19`: the can in video-01/02/03/04/07/08 previews "looks fake / like a picture placement / extremely ai slop". Cause: Image 3 (the size-and-place guide) was a flat packshot can pasted on the scrubbed frame; Wan copies it literally; the earlier QC passed "mild" paste signs.

Fix that worked (all six regenerated, previews rebuilt): the guide is a photoreal plate made with gpt_image_2_5 (source frame + flat placeholder can at the planned size/spot + packshot -> "empty scene, real can at that spot, contact shadow, reflection"), the video request is the old one with only the Image-3 sentence and the lighting sentence rewritten ("a photograph of ... take everything else only from Video 1"); locked camera = full plate, handheld = crop around the can. Scripts and method are in `RUN/50-requests/regen-2026-10-20/`. Video 03 needed a collar-free identity crop (C05-face.png) because the identity photo's collar leaked onto the sweatshirt.

**Why:** the user judges the can's realism first; a pasted guide is the root cause, not the prompt wording.
**How to apply:** for the remaining 14 videos (05, 06, 09-20) ask before regenerating (my read: 06, 15, 20 look most pasted); never write the lesson into the references or Loupe without the user's yes ([[fix-regeneration-original-plus-recrafted-prompt]]); a deliverable preview of video 03 must include the ghost composite (`60-outputs/video-03/preview-work/ghost-filter.txt`), the other previews are plain clean + text ([[atp-product-colours-and-preview]]).
