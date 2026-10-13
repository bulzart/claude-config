---
name: update-from-errors-command
description: "/update-from-errors <command> learns a pipeline from its error records (a ledger where the pipeline has one, else run-level records and the user's words); pipeline first, then errors, then rewrite the owning sections"
metadata:
  node_type: memory
  type: project
  originSessionId: 2adb81e3-0d33-4268-9b11-ed9262381e95
  modified: 2026-10-10T07:48:25.168Z
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

**Main idea (user, 2026-10-10): GENERALISATION.** The command turns each miss into a kind the
pipeline can apply to products and scenes the ledger never saw: what to achieve, what to avoid,
the miss and its cause, the prompt correction (failed wording to corrected wording) and what
worked, so the pipeline understands what is good and what is bad. The user's model example: "a
Neuro sachet forcedly placed leaning on the bbq grill lid" becomes "name a fixed, natural surface
the source frame shows; never a prop that moves or a leaning support; the pack sits where a person
would really leave it". Implemented as §3.3b (lesson cards + transfer test), contract item 6b, a
fourth coverage element ("gap of form"), a General rule change kind and the sample format. The
feedback is "stacked" inside the owning sections as general rules plus short samples, never as a
dump.

**Why:** the early pipeline lacked real examples, a good/bad sense and error definitions; the
ledger is meant to make that context accurate over time.

**How to apply:**
- Keep the order: pipeline first, then errors.
- Generalise across products and scenes, never across models; "what worked" and any good side only
  from a take that passed QC or was approved, otherwise write "not verified".
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
- The command's own build prompt is `Documents/prompts/update-from-errors.txt` (created 2026-10-10 at
  the user's request, CRLF, same prose style as `analyze-then-pick.txt`). After any change to the
  command, update it in the same style with a dated `.bak-YYYYMMDD-HHMMSS` copy beside it
  (see [[atp-build-prompt-sync]]).

**analyze-then-pick has no ledger since 2026-10-13** ([[atp-caught-errors]]): its record set is the user's words given as the argument plus the run-level records (briefs, requests, result.json); nothing is marked or promoted through a tool, and `learning-log.md` keeps the map from each CE label to the section that holds its lesson. The 2026-10-13 pass over all 94 entries was the first to consume CE-029..CE-094. The skill's ledger steps still apply to pipelines that keep one (analyze-then-generate).

Related: [[atp-caught-errors]], [[atp-build-prompt-sync]].
