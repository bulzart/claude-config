---
name: show-references-before-upload
description: "Before uploading new references to Higgsfield after a pipeline/approach change, show the user what changed and the full path of every file that will be used as a reference, and wait for their go"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fd23b3ce-bd75-4669-95d5-20d1bbdbcdef
  modified: 2026-10-21T22:56:13.971Z
---

User 2026-10-22 (Celsius run 20261021-224049-21, after the placement-marker change): "when you're just about to upload references on higgsfield with the new updates let me see first what changed and give the paths for each file that will be used as a reference".

**Why:** the user wants to inspect the new reference material (marked sources, crops, can views) before it reaches the generation service.

**How to apply:** before any new `media_upload` of a reference (main session or production agent): list each file with its full absolute path ([[always-full-paths]]), its role in the request (Video 1, Image N), and what changed versus the previous upload or approach; then wait for the user's go. Production agents stop with a blocker ("upload approval") instead of uploading; the main session relays. Already-uploaded media ids can be submitted as planned.
