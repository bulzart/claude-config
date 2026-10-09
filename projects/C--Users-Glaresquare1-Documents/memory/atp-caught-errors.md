---
name: atp-caught-errors
description: "/analyze-then-pick keeps ATP/caught_errors.md, a feedback ledger of videos the user was not satisfied with (verbatim words, diagnosis, class, cause, fix, rule); written only via `atp.py caught-error add`, read at every run start, applied in plans/prompts/QC, promoted into references when general"
metadata:
  type: project
---

On 2026-10-08 the user asked for a file that catches errors from their feedback per video they
were not satisfied with, with the issue and details, that the agents learn from on every run.
Result: `~/.claude/analyze-then-pick/caught_errors.md` (entries `## CE-nnn · date · title` with
video, run, mode, model, product, user said (verbatim), what was wrong, class, cause, fix, rule,
status, promoted to), the toolkit command `atp.py caught-error add | list | set` (locked writes,
auto ids), and wiring: command item 22, paths row, "Feedback first" before the mode question, A1
and E1 read the ledger into `20-analysis/caught-errors.md`, X1 names applied entries, X2 carries
their rules, X9 checks them by id, X9-R "Needs changes" writes an entry, the wrap-up invites
feedback, Never rules; production-agents reading list and hard rule; generation-system §8, §9,
§10 line; analysis-protocol §6; README; preprocessing usage; build prompt. Seeded with CE-001 to
CE-005 (capsules count, bottle spout, paper through bottle, pasted can, oversized can), all
promoted.

**Why:** the user wants every dissatisfaction recorded in their own words and turned into a
rule the next runs apply, not a one-off fix.

**Sources (user, 2026-10-09):** agents ALSO feed the ledger (`--source agent`: errors caught in QC
/ pre-gen / sync that cost a regeneration or survived the retry, recorded after the fix), AND the
wrap-up asks the user for feedback once everything is delivered (AskUserQuestion "Feedback";
each named problem → `--source user`, verbatim, with delivered details from result.json).

**How to apply:** when the user reports a bad video, run `atp.py caught-error add` FIRST (their
words verbatim, diagnosis, class, cause, fix, general rule) WITH the video's brief, final prompt
and QC verdict (user, 2026-10-08: "video brief should come along with the error"): pass `--run`
and `--video` so the saved brief (`40-briefs/video-NN-brief.md`, saved at X6), the newest request
prompt and the plan attach themselves, or `--brief/--prompt/--qc` as text or files; then offer
the fix. When a rule is
general or recurs, promote it into the right reference, `caught-error set --status promoted
--promoted-to …`, and update the build prompt ([[atp-build-prompt-sync]]). Never edit the ledger
by hand. Related: [[atp-anomaly-catalog]], [[atp-brand-guardrails]], [[atp-creative-direction]].
