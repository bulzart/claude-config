---
name: update-from-errors-command
description: "/update-from-errors <command> learns a pipeline from its caught_errors.md ledger; pipeline first, then errors, then rewrite the owning sections"
metadata:
  node_type: memory
  type: project
  originSessionId: 2adb81e3-0d33-4268-9b11-ed9262381e95
  modified: 2026-10-10T04:00:17.114Z
---

`~/.claude/commands/update-from-errors.md` (created 2026-10-10) takes a required command name
(e.g. `analyze-then-pick`; options `dry-run`, `only CE-…`).

The order is fixed by the user:
1. Read and model the FULL pipeline: the command, its references, the guides of the models in the
   ledger, the toolkit, the memory, and `learning-log.md`.
2. Then scan the error record set on EVERY pass: `caught_errors.md` is the entry point of a
   chain (files its entries point to, files that point back at it, siblings under other names
   such as generation errors caught / listed errors / error log, and run-level records that
   never reached the ledger). Not one file. (User clarification, 2026-10-10.)
3. Then cluster the entries, reverse-engineer them, grade the evidence and rewrite the owning
   sections: prompting, use cases, dismissal, craft, examples, error definitions and QC.

After that it promotes the entries through the ledger's tool, backs up and updates the build
prompt, logs the pass in `LIB/learning-log.md`, and commits.

**Why:** the early pipeline lacked real examples, a good/bad sense and error definitions; the
ledger is meant to make that context accurate over time.

**How to apply:**
- Keep the order: pipeline first, then errors.
- A coverage check (§3.4) comes before any edit: when the pipeline already covers every case,
  the command changes nothing, says "looks good", and only suggests optional updates (user
  asked for this explicitly, 2026-10-10).
- The architecture and structural design are never changed (user, 2026-10-10): nothing that
  exists is removed, merged, split, reordered, renamed, moved or re-methoded. NEW parts are
  fine when needed (user clarified twice the same day): a new file, stage, step, instruction,
  tool subcommand, field or entity. The one condition is coupling: each new part is wired in
  the way its neighbours are (caller, consumer, paths, reading lists, QC stack, README, build
  prompt). Anything beyond adding is a design suggestion, never applied.
- Only a prompt that passed QC may be a "good" example.
- A rule that recurs after promotion is replaced, not repeated.
- When the ATP pipeline changes shape, update the command's ATP target map.

Related: [[atp-caught-errors]], [[atp-build-prompt-sync]].
