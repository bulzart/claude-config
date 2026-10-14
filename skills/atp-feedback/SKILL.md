---
name: atp-feedback
description: /analyze-then-pick: a delivered video reported as wrong — diagnose in pipeline terms and offer the fix (item 22). Internal to that command.
user-invocable: false
---

# atp-feedback — A delivered video reported as wrong (item 22)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- nothing up front: read the run's brief, final prompt and QC verdict named below, and only the one reference section that owns the rule

## Feedback first

   If `$ARGUMENTS` or the opening message reports a delivered video as wrong
   (it names a video, a CapCut project or a run and says what was not right), handle it before
   anything else (item 22): find the run under `ATP/runs/` by the video's CapCut project name or date
   and read its brief, its final prompt and its QC verdict (`40-briefs/`, `50-requests/`,
   `60-outputs/video-NN/result.json`); when the run cannot be found, ask the user once for the brief or
   the prompt they used. Say in two lines which stage made the miss and which reference section holds the
   rule, then offer the fix (a re-edit or a regeneration of that video in its mode) in one line, and
   continue only if the user wants it.

## Rules this phase owns (contract items 22)

22. **No error ledger: the rules live in the pipeline.** Every lesson learned from a video that went wrong
    (the user's reports, the agents' regenerate reasons) is written, generalised, in the section that owns
    it (`reference/`, the model guides): as a kind (what to achieve, what to avoid) with the miss, its
    cause, the corrected wording and what worked as the sample beside it. There is no `caught_errors.md`,
    no `T caught-error`, no per-run digest of past errors, and nothing in a run reads an error file: the
    plan, the prompt and QC follow the references. The only error text a run writes is a video's own
    attempt block in its brief, `result.json`, and the Higgsfield flag record of item 23; no later run
    reads any of it. `CE-nnn` in the references are case labels of
    those lessons (`README.md`). **When a delivered video is wrong**, in the run or in a later session:
    take the user's words verbatim, diagnose them in pipeline terms (the stage that made the miss and the
    stage that should have caught it), say which section already holds the rule and why it did not
    prevent this video, and offer the fix (a re-edit or a regeneration of that video in its mode); when the
    miss is a kind the references do not hold, say so in one line and name `/update-from-errors
    analyze-then-pick` with the user's words as its argument, which generalises them into the owning
    sections. A user's word outranks the agents' QC on the same point: the user saw what QC passed. **The
    agents** write a regenerate reason or a flagged delivery in the video's brief (an attempt block with the
    failed request, the verdict and what changed) and in `result.json` (`reference/production-agents.md` §3
    item 12); nothing else is written to the library but the Higgsfield flag record of item 23.

## Never (this phase)

- Never create or read an error ledger (item 22): a video the user reports as wrong is diagnosed with their
  words verbatim, in its brief, and fixed only after the diagnosis.

## Hand-off

Continue only if the user wants the fix (a re-edit or a regeneration of that video in its mode): re-enter the per-video loop at `atp-write-request` with the diagnosis. A miss that is a kind the references do not hold: say `/update-from-errors analyze-then-pick "<their words>"`.
