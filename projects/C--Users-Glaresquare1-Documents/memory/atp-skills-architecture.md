---
name: atp-skills-architecture
description: "/analyze-then-pick is a ~13 KB router + 19 atp-* phase skills + sectioned references/guides (docs_tool.py); where to edit what, and the anti-context-rot rules (user 2026-10-14)"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-14T17:37:54.921Z
---

On 2026-10-14 the user asked to split the 138 KB `/analyze-then-pick` command into Claude skills per section and mode,
because the agents' context was rotting from large prompt chunks and from reading what a step does not need; the phases
must stay interconnected but each agent reads only its mode and step.

What exists now (full description: `~/.claude/analyze-then-pick/README.md`):
- `~/.claude/commands/analyze-then-pick.md` is only a router (loading rules, one-line contract items, phase map, labels table, global Never).
- 19 skills `~/.claude/skills/atp-*/SKILL.md` (`user-invocable: false`): start, analyze-prepare/-study, create-plan, recreate-plan, asset-plan, analyze-produce, edit,
  plan-video, write-request, inputs, precheck, submit, postprocess, qc, record, wrapup, feedback, model-guide. Steps moved verbatim; each has "Read now" + a hand-off
  that records `state.json → next_skill`.
- Every long reference/guide is an index `X.md` + folder `X/` of section files (numbers unchanged); `scripts/docs_tool.py` splits/joins/indexes/checks; `atp.py model-entry --id` prints one model entry.
- Production agents' contract (`reference/production-agents/020_2_spawning.md`) invokes the per-video skills instead of reading the command.

**Why:** run start dropped from 135 KB to 13 KB, agents never read the command or whole documents, and every phase boundary is a safe `/compact` or resume point.

**How to apply:** to change a step or rule, edit the owning skill (the router's labels table says which; a rule two phases act on lives in both) or the section file; then
`python ~/.claude/analyze-then-pick/scripts/docs_tool.py index <doc>.md` (if sections changed) and `... check` (must be 0 errors), update the build prompt ([[atp-build-prompt-sync]]),
and commit. Never recreate a monolithic command, never Read a whole reference/guide or `models/index.json` in a run (a PreToolUse hook `hooks/atp_read_guard.py` now refuses whole-file reads of atp.py, models/index.json, the catalog snapshot and backups; a SessionStart compact|resume hook `hooks/atp_resume_note.py` names the unfinished run and its `next_skill`; [[loupe-web-app]]), never leave backups in tracked folders ([[claude-folder-git-versioning]]).
`/update-from-errors` is the only reader of whole documents (`docs_tool.py join`).
