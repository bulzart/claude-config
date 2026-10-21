---
name: awl-placement-marker-no-guide-image
description: "/analyze-with-loupe rule (user 2026-10-22): the product in a prepared video reference is a labelled placement/size marker at the reckoned size; the separate blurred source-crop size-and-place guide image is never uploaded or used again"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fd23b3ce-bd75-4669-95d5-20d1bbdbcdef
  modified: 2026-10-21T22:17:36.462Z
---

User 2026-10-22 (Celsius run 20261021-224049-21, V09 pilot), on the prepared source with the can composited into it (`10-media/<V>/prepared/source-placeholder.mp4`):
1. Next to the product in that video reference, add a short text label saying it is only a placement/size reference from the client's asset sample, not how the product must look; the generated video must show a real product rendered properly in the scene, not the pasted sample.
2. The product in that video sample must have the right size: calculate proportions, dimensions and distance against the original video's objects of known size (and their distances), with the product's real dimensions from the client assets.
3. The blurred source-crop size-and-place guide image (`30-assets/guides/V09-guide.png`): "never upload or use it ever again".

**Why:** the user saw the placeholder could be read as the product's final look, and rejected the blurred guide image.

**How to apply:** in /analyze-with-loupe, Recreate/Edit sources that carry a placed product get the labelled marker (built with the toolkit, measured with two agreeing estimates, recorded); every request that uses one says the marker and its label are removed and a real product is rendered; no separate guide image built from a source crop. Related: [[analyze-with-loupe-command]], [[no-genjutsu-use-wan-prime]], [[always-full-paths]].
