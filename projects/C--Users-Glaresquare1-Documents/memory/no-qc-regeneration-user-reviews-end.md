---
name: no-qc-regeneration-user-reviews-end
description: "User 2026-10-28 (both 27.10 recreate runs): each clip generated once, no QC regeneration; later the same day also NO QC inspection at all; the user reviews at the end"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6cbd9032-18a8-4ac2-bf9d-dc68a46bea88
  modified: 2026-10-28T03:16:14.800Z
---

User, 2026-10-28, mid /analyze-with-loupe run 20261027-224009-27 (Celsius) and run 20261027-233328-27 (Neuro): "continue, just don't do any second generation from QC agents if something wrong i will tell in the end". Later the same day, in the Neuro run: "continue, just don't do any second or more generations after the first one and no QC agents inspection, if something wrong i will tell in the end".

**Why:** the user wants to judge the first takes themselves instead of paying (credits and time) for automatic checks and fixes; the pilot spent its retry and still shipped flagged.

**How to apply:** every clip is generated once. With the second rule, production agents skip awl-qc entirely (no qc-consult, no dense sheets, no size/label measurements, no project checks): inputs → submit → postprocess (audio, conform, join) → CapCut project → preview → record, result.json qc = "not inspected (user rule)". Pre-generation planning and the main session's X4 still run, and findings learned before a clip is submitted may still change its request (that is not a regeneration). A submission that produced nothing (refused/flagged job) may be resubmitted once after its flag is recorded. Propose this as the default for later runs unless the user says otherwise; list what was and was not inspected in the wrap-up. Related: [[awl-never-ask-decide-autonomously]], [[atg-qc-fixes-option]].
