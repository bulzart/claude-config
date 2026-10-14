---
name: atp-build-prompt-sync
description: "Documents/prompts/analyze-then-pick.txt is the build prompt for the /analyze-then-pick pipeline; keep it in sync after every pipeline change; since 2026-10-14 it describes the router + phase skills + section files architecture, which is real"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-14T17:37:47.816Z
---

`C:\Users\Glaresquare1\Documents\prompts\analyze-then-pick.txt` is the prompt the user runs to
(re)build the `/analyze-then-pick` pipeline. It is CRLF prose, no headings; a dated `.bak-*` copy of the
previous version sits beside it before each rewrite (the folder is not under git).

On 2026-10-08 it got a "Knowledge packaging" section asking for skills as the packaging ("even though our pipeline is
not like that"). On 2026-10-14 that became real and the section was rewritten to match what exists: the command is a
router, there are 19 phase skills `~/.claude/skills/atp-*`, every long document is an index + section files made by
`scripts/docs_tool.py`, and model guides are sectioned folders read through `atp-model-guide`, **not one skill per model**
(deviation from the 2026-10-08 wish: every skill description sits in every session's skill list; one router skill gives
the same read-only-the-locked-model behaviour at no listing cost) and **not registered in the global CLAUDE.md**
(always-loaded text only adds rot). Offer per-model skill wrappers if the user still wants them. See [[atp-skills-architecture]].

**Why:** the user noticed the prompt had drifted far behind the pipeline; they want it to remain the
single spec from which the pipeline can be rebuilt.

**How to apply:** after any change to the command, a skill or the library, also update the build prompt
(same prose style, no new headings; one paragraph or bullet per rule; keep CRLF; make the `.bak-*` first).
Keep its skills section consistent with how skills really live on this machine. The flag record, the QC samples/keeper and the three hooks are Loupe's: they have their own build prompt `Documents/prompts/loupe.txt` ([[loupe-web-app]]); this prompt only says that flags go to Loupe, that atp-qc calls `qc-consult`, and that the hooks exist. Related: [[atp-anomaly-catalog]],
[[analyze-then-pick-system]].
