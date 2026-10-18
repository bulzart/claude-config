---
name: update-from-errors-command
description: "OBSOLETE (user 2026-10-18): /update-from-errors is no longer executed and must not be mentioned in new docs, skills or prompts; a lesson goes straight into the owning section on the user's yes"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T13:37:22.570Z
---

User, 2026-10-18: "update-from-errors will no longer be executed, it is obsolete now on". The command file
`~/.claude/commands/update-from-errors.md` and its build prompt `Documents/prompts/update-from-errors.txt` still exist on disk
but are dead. Every mention was removed from analyze-then-generate's router, skills, references, README, learning log and
build prompt, and from the Loupe build prompt, on that day.

**Why:** the pipelines keep no error ledger any more ([[atp-caught-errors]]), so the command's job (generalising a ledger of
entries) is gone; lessons are generalised where they land.

**How to apply:**
- Never run it, never suggest running it, never write it into a skill, a doc or a prompt.
- When the user reports a bad video or a bad pick: take their words verbatim, diagnose in pipeline terms, and if the references
  do not hold the rule, offer to write it into the owning section as a general kind (what to achieve, what to avoid, the miss
  and its cause, the corrected wording, what worked; a Trigger and a Counter-case; at most one short example); write it only
  on the user's yes ([[atp-reasoning-over-rule-lists]]).
- analyze-then-pick was cleaned too on 2026-10-18 at the user's request ("remove it from analyze-then-pick too"): its command (item 22),
  skills (atp-feedback, atp-wrapup, atp-submit, atp-analyze-produce, atp-model-guide), README, learning-log title and introduction (plus a
  closing "learning command retired" section) and build prompt (backup `.bak-20261018-no-ufe`) no longer mention it. Left as history: the
  dated sections of the ATP learning log (the four passes, the user's verbatim quote) and old run folders' briefs. The command file
  `commands/update-from-errors.md` and `Documents/prompts/update-from-errors.txt` still sit on disk, unused; not deleted because the user has
  not asked for that.
- The old design (kept only as history): read the whole pipeline first, then the errors, then generalise each miss into a
  kind with a transfer test, never changing the architecture.
