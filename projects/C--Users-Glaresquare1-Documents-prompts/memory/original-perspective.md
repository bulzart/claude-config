---
name: original-perspective
description: "Generated videos must keep the original reference's perspective: never flip/mirror a source (CE-030's selfie flip retired 2026-10-27)"
metadata:
  type: feedback
---

The user, 2026-10-27: "video should be in the original perspective not reverted/mirrored". /analyze-with-loupe never flips a source, in any
mode. A front-camera selfie keeps its own reversed print as the original shows it, while the client's product label reads correctly. Only a
mirrored identity photo, which is a face reference and not the video, is turned to the person's true face.

**Why:** generation-system §5c.2b used to flip mirrored selfie sources before upload. That rule came from CE-030 ("maybe flip video, then add
bag"), and those outputs came out mirrored against the original.

**How to apply:** never propose flipping a source or an output to fix reversed text. The prompt line is "Video 1's orientation stays exactly
as it is; nothing is flipped". Related: [[judges-stable]].
