---
name: atg-vb-wrapup
description: /analyze-then-generate Viral-Browser phase: report QC, wrap-up, picks feedback and the optional continue to Create (V8–V9). Internal to that command.
user-invocable: false
---

# atg-vb-wrapup — Viral-Browser: report QC, wrap-up, feedback, continue to Create (V8–V9)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase of `/analyze-then-generate` (Viral-Browser). Nothing is generated. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §10: `ATG/reference/viral-browser/430_10_deliverables-v7-v8.md` (5.4 KB) (deliverables, the chat summary and the report QC checklist)
- viral-browser §11: `ATG/reference/viral-browser/440_11_wrap-up-feedback-and-continuatio.md` (4.5 KB) (wrap-up, feedback, adjust, continue to Create)
- viral-browser §12: `ATG/reference/viral-browser/450_12_easy-to-miss-traps.md` (4.3 KB) (pitfalls)

## Steps

### V8. Report QC
- The checklist of `viral-browser.md` §10.4, run by you (no script runs it): every number sourced or
  recomputed with `T econ`, the gate reading per pick quoted from `ranking.md`, origin-blind dossiers,
  defence notes present, one currency and tax convention, region-matched evidence, up to 12 key claims
  fetched again, no unsupported hook or claim, each pick's reference pack (spec judgements and the photo
  coverage table, nothing read off a photo, no image downloaded, angles shown as the source's labels,
  rights stated), and each research error that reached this step fixed and noted in the bias log. Fix before anything is shown. `next_step=wrap-up`.

### V9. Wrap-up
- Show the summary (`viral-browser.md` §10.3): the table of the three picks (with each pick's reference unit, size,
  weight, material and photo-link coverage), the method in three
  lines, the open questions, the deliverables path and the run folder. No credits, no CapCut.
- Ask for feedback (`viral-browser.md` §11.2, header "Picks"). Every problem named, now or later, is handled as item 22 says (`atg-feedback`): their words verbatim and the
  diagnosis in `deliverables/feedback.md` before the fix is offered. "Adjust" follows §11.3.
- Offer in one line the next step: **continue to Create for a pick** (§11.4: the run enters the
  Create flow at its start, for the new inputs only; it needs the product's assets and a model and
  starts only on the user's yes), more depth on one candidate, or nothing. When a problem is a kind the references do not hold, add one line offering
  to write the rule into the section that owns it.

## Rules this phase owns (contract item 26)

26. **Viral-Browser is autonomous after the brief:** the only questions are the brief (market,
    price range, selling model, research tools), the final feedback question, and the optional
    "continue to Create". Research blockers are reported, not asked. Continuing to Create is
    offered at the end and runs only on the user's yes (`viral-browser.md` §11.4); it then follows
    every Create rule, and none of Viral-Browser's output relaxes one.

## Never (this phase)

- Viral-Browser: never generate anything. No model pick, no Higgsfield generation tool, no credits, no
  CapCut project, no request for client assets, no `split-audio` or any other change to the
  references folder; never start Create without the user's yes (item 26, `viral-browser.md` §11.4).
- Viral-Browser: never lower a gate silently to fill the table (fewer than 3 candidates meeting the gates
  is a valid result; any gate you relax is named in the report with its reason), and never show a pick
  without its confidence and what would change the call.

## Hand-off

Nothing follows unless the user says yes to a next step. **Continue to Create** (`viral-browser.md` §11.4) runs only on the user's yes and re-enters the Create flow for the new inputs only: `atg-start` (steps 3–5, new inputs only), then `atg-analyze-prepare` (what is new), `atg-analyze-study` (the additions and the product side of A4), `atg-create-plan`, and on as in Create. Record `T state --run RUN set stage=done` when the user wants nothing more.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
