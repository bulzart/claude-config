---
name: show-references-before-upload
description: "REVOKED 2026-10-27: do not ask the user to approve reference files before Higgsfield uploads, or anything else mid-run; continue autonomously (was: show paths and wait for the go, 2026-10-22)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 5082ead0-b81c-4ac6-a9bb-d1526fddf08a
  modified: 2026-10-26T23:50:56.767Z
---

User 2026-10-27 (Celsius Recreate run 20261026-222352-celsius-recreate, while the nine non-pilot plans were being reviewed): "no need to ask approvals from me on references just continue straight away no need for asks on my side at all".

This replaces the 2026-10-22 rule (Celsius run 20261021-224049-21: "when you're just about to upload references on higgsfield with the new updates let me see first what changed and give the paths for each file that will be used as a reference").

**Why:** the user wants the runs to proceed without stopping for their sign-off.

**How to apply:** build, upload and submit references without an approval step; production agents upload their own inputs (no "upload approval" blocker). Make the judgement calls yourself (a weak spot, a pick swap, a fix generation within the QC-fixes rule) and report them in the wrap-up with the reason. The pipeline's own fixed questions at a run's start (mode, model, inputs, count, QC fixes, audio) are not covered by this; mid-run asks are. Still name every file by its full path when reporting ([[always-full-paths]]). Related: [[references-built-per-generation]].
