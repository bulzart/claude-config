---
name: atg-qc-fixes-option
description: "/analyze-then-generate contract item 27 (user 2026-10-18): the user chooses at the start whether a fix generation after a QC finding is asked first (ask) or done by the QC agents on their own (auto); state.json qc_fixes, qc_fix_permission blocker"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T13:12:03.972Z
---

User, 2026-10-18: "it should have two options: when the first video is generated and the QC agents find issues or anomalies in it it asks for the users
permission if to proceed with the fix generation or not, or leave the QC agents to proceed with the correctness on the new video generation on their own
without asking at all".

What was built (Recreate and Create only; Edit Mode has no automatic regeneration, the user reviews every attempt):
- Asked once at the start in `atg-start` step 5 (AskUserQuestion header "QC fixes": "Ask me first" / "QC agents fix on their own"), or given as the argument
  `qc-fixes ask|auto`; stored with `T state --run RUN set qc_fixes=ask|auto`; a run without it is `auto` (the behaviour before).
- `ask`: the production agent writes its attempt block, prepares the corrected request and the X5 preflight, submits nothing, and stops with
  `result.json` `blocker: qc_fix_permission` + `fix_proposal`; the main session asks (header "QC fix": fix it / keep this take / fix it and stop asking),
  then continues the agent with `approved`, `declined` or `auto` (SendMessage; fallback: a fresh agent resuming at atg-submit X7). Declined = the take ships as
  generated, flagged (`qc` = "declined fix: ..."). Local post-fixes, CapCut fixes and no-output job retries are never asked.
- Written in: router item 27, atg-start, atg-qc, atg-submit, atg-analyze-produce, atg-wrapup, production-agents sections 1-5, README, learning-log, build prompt
  (`Documents/prompts/analyze-then-generate.txt`, backup `.bak-20261018-qc-fixes`); tests: `tests/t14_library.py` checks the wiring.

**Why:** the user wants control over credits spent on fix generations, or full autonomy, per run.

**How to apply:** I decided the choice is made at the start (all questions upfront, autonomy afterwards) and added a third answer "fix it, and stop asking" so the
user can switch to auto at the first finding; if the user wants the question only at the first finding, or an Edit Mode variant, change `atg-start`/`atg-qc`.
Related: [[atg-pipeline]], [[atg-skills-architecture]].
