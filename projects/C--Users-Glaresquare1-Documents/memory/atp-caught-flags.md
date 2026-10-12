---
name: atp-caught-flags
description: ATP/caught_flags.md ledger of prompts and videos Higgsfield flagged or refused; written only with `atp.py caught-flag`; part of the /analyze-then-pick pipeline since 2026-10-12
metadata:
  type: feedback
---

The user asked (2026-10-12) for a `caught_flags` ledger that marks the prompts and videos that caused flags in Higgsfield during `/analyze-then-pick`, and for it to be an instruction in the command pipeline.

**Why:** a refused or flagged generation (a moderation block, a job failing in seconds with no reason, an `nsfw` / `ip_checking` upload, a withheld output, a `preset_recommendation` notice instead of a job) was only visible in one run's submission ledger; the next run could send the same trigger again.

**How to apply:**
- File `~/.claude/analyze-then-pick/caught_flags.md`, written only with `T caught-flag add | set | list | reconcile`; mark the submission with `T ledger set --flagged`. Record BEFORE the request changes: verbatim response, kind, tool/stage, jobs and credits, flagged video (reference + clip paths), full prompt, params, media ids, the agent's own suspected trigger [E]/[I]. `cleared` only after a changed request was accepted; else `persistent`.
- Wired into the command (item 23, A1/E1 read + `20-analysis/caught-flags.md`, X4 check, X7 step 6, A9b and wrap-up reconcile, Never list), `reference/production-agents.md` (contract item 15, §5 step 0), the Higgsfield notes, `generation-system.md` §5c.2, and `Documents/prompts/analyze-then-pick.txt`.
- Backfilled CF-001 (celebrity face in the video reference, two refunded failures) and CF-002 (IN THE DARK preset notice). Scripts only record; the agent diagnoses ([[scripts-gather-agents-decide]]). Related: [[atp-caught-errors]], [[atp-build-prompt-sync]].
