---
name: analyze-with-loupe-new-command
description: "the Fable-prompt agent GENERATES a new command /analyze-with-loupe that carries all the improvements (Loupe first-class, free to design anything, nothing deformed); /analyze-then-pick and /analyze-then-generate stay read-only; user 2026-10-20"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T13:23:47.396Z
---

User, 2026-10-20, in steps: only /analyze-then-pick is edited, not /analyze-then-generate; the agent is free to edit, change, alter, implement or add anything in the pipeline (it improves, it does not only inspect) but must not deform the intended functionality; do not presuppose what it should change: it reads and understands the pipeline and the output we want, Claude Code internals, agents, how agents handle data formats, how separate sessions like the QC keeper process Loupe's samples and whether they understand them or miss something, double-edged cases, ambiguity, context rot, coupling, any other feature, Loupe's miss-processing scripts; and finally "make it so that it generates a new command /analyze-with-loupe with all the changes".

**State:** `Documents/prompts/pipeline-coupling-fable.txt` is written that way: SCOPE (a NEW command /analyze-with-loupe: command file, skills, library, toolkit, README, learning log, tests, build prompt `analyze-with-loupe.txt`, hook and Loupe coverage; self-contained, never mentioning the other pipelines), AUTHORITY, a FUNCTIONALITY CONTRACT (the same rehearsal, Phase A7, runs on /analyze-then-pick and the new command so any difference shows), four phases (understand, decide, build, verify), sections 0A to 0D and 1B, the optional Whisper question as a user requirement, the old defect list reduced to observations and optional ideas, and a SAFETY NET. `pipeline-coupling-fable-addendum-authority.txt` tells an already-running session to re-read it and to stop editing /analyze-then-pick.

**Why:** the user wants every improvement, but isolated in a new command so the stable pipeline (and the live run using it) is never deformed; the user decides later whether the new one replaces the old.

**How to apply:** /analyze-then-pick and /analyze-then-generate are never edited from now on; Loupe, hooks and settings.json may change for the new command only if both old pipelines and the live run keep working and their tests stay green. Still the user's: credits and Higgsfield calls, live run folders, credentials, pushing, the product and brand rules in memory, the start-at-logon refusal. The Whisper work already built in /analyze-then-pick ([[atp-audio-ingest-question]]) is carried into the new command. Related: [[no-cross-pipeline-mentions]], [[atp-skills-architecture]], [[atp-build-prompt-sync]], [[loupe-web-app]].

**Built 2026-10-20** by this session: see [[analyze-with-loupe-command]] for where it lives, what it keeps and what it changes; the report is `Documents/prompts/coupling-report-2026-10-20.md`.
