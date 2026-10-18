---
name: update-from-errors-command
description: "OBSOLETE (user 2026-10-18): /update-from-errors is no longer executed and must not be mentioned in new docs, skills or prompts; a lesson goes straight into the owning section on the user's yes"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T12:37:07.521Z
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
- analyze-then-pick's own files still mention the command; they were not edited because an ATP run may be active. Clean them
  when the user asks.
- The old design (kept only as history): read the whole pipeline first, then the errors, then generalise each miss into a
  kind with a transfer test, never changing the architecture.
