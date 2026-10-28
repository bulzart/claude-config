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

**How to apply:** every clip is generated once. With the second rule, production agents skip awl-qc entirely (no qc-consult, no dense sheets, no size/label measurements, no project checks): inputs → submit → postprocess (audio, conform, join) → CapCut project → preview → record, result.json qc = "not inspected (user rule)". Pre-generation planning and the main session's X4 still run, and findings learned before a clip is submitted may still change its request (that is not a regeneration). A submission that produced nothing (refused/flagged job) may be resubmitted once after its flag is recorded. List what was and was not inspected in the wrap-up. **Formalised the same day (user: "add a 3rd option no qc agent after first generation at all and if there are somethings to fix i will instruct in the end after all the work is delivered"):** contract item 27 now offers three choices at the start, `ask` | `auto` | `off` ("No QC, I review at the end"; none recommended); `off` = no awl-qc at all, X8 builds the CapCut project at once, result.json qc "off: not checked (the user reviews at the end)", the pilot shows only its technical outcome, and the wrap-up's feedback question is the review. A run's stored choice decides; never impose `off` on a run that chose otherwise. Related: [[awl-never-ask-decide-autonomously]], [[atg-qc-fixes-option]].
