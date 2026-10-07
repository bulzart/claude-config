---
name: atp-build-prompt-sync
description: "Documents/prompts/analyze-then-pick.txt is the build prompt for the /analyze-then-pick pipeline; keep it in sync after every pipeline change, and it specifies skills-based packaging of model guides and knowledge"
metadata:
  node_type: memory
  type: project
  originSessionId: 2adb81e3-0d33-4268-9b11-ed9262381e95
  modified: 2026-10-07T23:19:27.061Z
---

`C:\Users\Glaresquare1\Documents\prompts\analyze-then-pick.txt` is the prompt the user runs to
(re)build the `/analyze-then-pick` pipeline. On 2026-10-08 it was brought up to date (source
fidelity from the first attempt, the anomaly catalog with affordance sheets and 30 fps QC
checkpoints, the locked CapCut text preset, honest reporting, resume arguments, the Higgsfield
preset-recommendation quirk) and extended with a "Knowledge packaging" section the user asked for:
every generation model's research becomes a Claude Code skill (`~/.claude/skills/<model-slug>/`,
guide as reference files, `sd25-pe` as the precedent), registered in the global `~/.claude/CLAUDE.md`
with its trigger and invoked when that model is about to run; other data, collections, instructions
and QC rules are packaged as a skill when they are a procedure a step invokes, or as a .md reference
when they are data to read. The user said this explicitly "even though our pipeline is not like
that": the live library still keeps guides as `models/<slug>.md`, so the prompt describes the target
packaging, not the current one. A dated `.bak-*` copy of the previous prompt sits beside it.

**Why:** the user noticed the prompt had drifted far behind the pipeline; they want it to remain the
single spec from which the pipeline can be rebuilt.

**How to apply:** after any change to the command or its library, also update the build prompt
(same prose style, no new headings; one paragraph or bullet per rule). Keep the skills section
consistent with how skills really live on this machine. Related: [[atp-anomaly-catalog]],
[[analyze-then-pick-system]].
