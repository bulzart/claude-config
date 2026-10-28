---
name: no-qc-regeneration-user-reviews-end
description: "User 2026-10-28 (Celsius recreate run): QC agents never generate a second time; each clip once, findings shipped flagged, the user reviews at the end"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6cbd9032-18a8-4ac2-bf9d-dc68a46bea88
  modified: 2026-10-28T01:24:50.886Z
---

User, 2026-10-28, mid /analyze-with-loupe run 20261027-224009-27: "continue, just don't do any second generation from QC agents if something wrong i will tell in the end".

**Why:** the user wants to judge the first takes themselves instead of paying for automatic fixes (the pilot spent its retry and still shipped flagged).

**How to apply:** in that run (and as the default to propose for later runs unless the user says otherwise): every clip is generated once; a QC regenerate reason is written as an attempt block and as "FLAGGED (no regeneration, user rule)" in result.json, and the take ships; main-session follow-up re-runs are not started either; local post-fixes the anomaly catalog allows still run; a submission that produced nothing (validation error, refused/flagged job) may be resubmitted. List every flagged finding in the wrap-up for the user's decision. Related: [[awl-never-ask-decide-autonomously]], [[atg-qc-fixes-option]].
