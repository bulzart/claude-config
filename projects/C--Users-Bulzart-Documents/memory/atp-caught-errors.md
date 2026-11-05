---
name: atp-caught-errors
description: "RETIRED 2026-10-13: /analyze-then-pick has no error ledger any more (caught_errors.md and `atp.py caught-error` removed); lessons live generalised in the references; a user's bad-video report is diagnosed in the brief and the rule is written into the owning section on the user's yes"
metadata:
  node_type: memory
  type: project
  originSessionId: 018f5736-eb42-45a5-8337-7d44d473e9a2
  modified: 2026-10-13T16:35:59.351Z
---

History: on 2026-10-08 the user asked for a file of the videos they were not satisfied with
(`~/.claude/analyze-then-pick/caught_errors.md`, `atp.py caught-error add | list | set`, command item
22, read at A1/E1, applied in X1/X2/X9, fed by the agents and by the wrap-up feedback question). It
grew to 94 entries (CE-001..CE-094, 1.3 MB, mostly attached briefs, prompts and QC verdicts).

**Decision (user, 2026-10-13): errors are no longer inserted and saved in a different file.** The user
ran `/update-from-errors analyze-then-pick` and asked to remove the caught_errors files, inserting each
error entry completely into the pipeline, because the separate file was causing AI-agent context memory
rot and "we've had enough cases covered to be generalized for a final pipeline". The pass consumed
CE-029..CE-094 (never processed before), wrote every lesson into its owning section (generation-system
§4b.1c/§4b.6/§5c.2b, anomaly-catalog §2.9/§2.15–§2.17, the Wan and Seedance guides, the command) and
retired the ledger.

**Why:** a growing ledger read at every run start rots the agents' context; the lessons belong in the
owning sections as general rules (what to achieve, what to avoid) with short samples.

**How to apply:**
- Never recreate `caught_errors.md`, `atp.py caught-error`, `20-analysis/caught-errors.md` digests or
  any other error file for analyze-then-pick. Agents write a regenerate reason or a flagged delivery in
  the video's brief (an attempt block) and in `result.json`, nothing else.
- When the user reports a bad video: take their words verbatim, diagnose in pipeline terms (stage that
  made the miss, stage that should have caught it), say which section holds the rule, offer the fix; if
  the miss is a kind the references do not hold, offer to write the rule into the owning section (on the
  user's yes; /update-from-errors is obsolete, [[update-from-errors-command]]).
- `CE-nnn` in the references are case labels: the README explains them, `learning-log.md` maps each to
  its section, the old file is in git history (last commit `aba83d3`).
- Not affected, and not asked about: `caught_flags.html` (the flag record, now an HTML page, [[atp-caught-flags]]) and the
  Loupe flag record. (analyze-then-generate's own ledger was retired on 2026-10-18 in its rebuild, [[atg-pipeline]].)

Related: [[atp-anomaly-catalog]], [[update-from-errors-command]], [[atp-build-prompt-sync]].
