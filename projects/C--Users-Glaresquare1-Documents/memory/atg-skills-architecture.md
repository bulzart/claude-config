---
name: atg-skills-architecture
description: /analyze-then-generate (2026-10-18) = ~20 KB router + 25 atg-* phase skills (6 are atg-vb-*) + sectioned references/guides incl. viral-browser; where to edit what; Loupe and hooks cover both pipelines
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T12:37:35.447Z
---

On 2026-10-18 the user asked to rewrite `/analyze-then-generate` with the same context-rot-avoiding structure as the other pipeline, linked to
Loupe, with ambiguity and double-edged example cleanup, without losing any ATG logic ("split sections into skills").

What exists (full description: `~/.claude/analyze-then-generate/README.md`):
- `~/.claude/commands/analyze-then-generate.md`: router only (~20 KB: loading rules, resume incl. Viral-Browser `next_step` map, 26 one-line contract
  items, phase table, per-video loop, labels, global Never).
- 25 skills `~/.claude/skills/atg-*/SKILL.md` (`user-invocable: false`, LF endings, descriptions <=200 chars): the 19 shared phase skills
  (start, analyze-prepare/-study, create-plan, recreate-plan, asset-plan, analyze-produce, edit, plan-video, write-request, inputs, precheck, submit,
  postprocess, qc, record, wrapup, feedback, model-guide) + 6 Viral-Browser skills: `atg-vb-cards` (V1-V2 incl. the inputs/brief questions and
  the run), `atg-vb-synthesis` (V3-V4b), `atg-vb-research` (V5), `atg-vb-select` (V6), `atg-vb-deliver` (V7), `atg-vb-wrapup` (V8-V9).
  `atg-start` hands a Viral-Browser run to `atg-vb-cards` right after the sub-mode is known. Hand-offs record `state.json -> next_skill`.
- All long docs are index + section folder (`scripts/docs_tool.py split|join|index|check|budget`); `viral-browser` is sectioned too (sections 0-14;
  12 = short trap list; prompts in 13.x cite section files). Edit the section file, then `docs_tool.py index <doc>.md` and `docs_tool.py check`
  (0 errors); `refresh_reads` equivalent: a "Read now" list names exact section files, so after renumbering fix the skills' paths.
- Hooks `hooks/atp_flag_watch.py`, `atp_resume_note.py`, `atp_read_guard.py` serve both pipelines (they scan both `runs/` folders and name the right
  toolkit script); Loupe (`core.LIBS`, `runs.list_runs` with a `lib` tag, pushed to GitHub) lists the runs of both; `atg.py` carries `caught-flag`,
  `loupe`, `qc-consult`, `qc-brief`, `plan-hints`, `model-entry`.
- Build prompt `Documents/prompts/analyze-then-generate.txt` was rebuilt from a 3-way merge (backups `.bak-20261018-*`).

**Why:** same as before: agents never read the command or whole documents, every phase boundary is a safe `/compact` or resume point, the Viral-Browser
procedure (~28 KB) no longer sits in front of Edit and Recreate runs.

**How to apply:** change a step in the owning skill (router labels table says which; a rule two phases act on lives in both), a rule in its section
file; never recreate a monolithic command; never Read a whole reference/guide or `models/index.json` in a run; keep new text free of mentions of the other
pipeline ([[no-cross-pipeline-mentions]]); update the build prompt after any pipeline change ([[atp-build-prompt-sync]]); backups live outside tracked
folders ([[claude-folder-git-versioning]]). Related: [[atg-pipeline]], [[loupe-web-app]].
