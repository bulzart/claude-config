---
name: awl-original-only-reference
description: "/analyze-with-loupe (user 2026-10-28): NO placement marker or placement preview at all; the original video (silent) is the only video reference and prompts, images and instructions carry spot and size; the blurred source-crop guide image stays banned (2026-10-22)"
metadata:
  type: feedback
---

User 2026-10-28, after video-02 of the Neuro run (20261027-233328-27) had to be split at 6.10 s. The original span plus its placement preview (about 25 s) exceeded Wan 3.0 Prime's 15 s reference-video limit per request: "remove the reference placement from the analyze-with-loupe totally ... just let the original video as a reference, i believe prompts,images and instructions suffice".

Still standing from 2026-10-22: the blurred source-crop size-and-place guide image, "never upload or use it ever again".

**Why:** the marked preview doubled the reference length and forced splits. The user trusts the prompt, the product images and the instructions to say where the product goes and how big it is.

**How to apply:**
- In Recreate and Edit Mode, the request's only video reference is the original's silent footage of the planned span: `videos_without_audio`, else `own/own-silent.mp4` or `prepared/source.mp4` for inserts, a flip or padding.
- It goes in the model's most preserving input and must fit the model's OWN limit (no halving for a pair). A longer source splits on its own cuts.
- In any mode: no composited copy, no marked stills, no layout image, no Create texture, no guide crop.
- Pin the spot to a fixed neighbour, state the size against a named neighbour, and pad the product views.
- Where the guide lists size as a model limit, the anchor class is the lever; otherwise write the size risk in the brief. QC measures with `T scale`.
- The `placeholder` command and generation-system §4b.6/§4b.7 were removed on 2026-10-28, and t01 guards against their return. Never reintroduce them.

Related: [[analyze-with-loupe-command]], [[no-genjutsu-use-wan-prime]], [[references-built-per-generation]], [[always-full-paths]].
