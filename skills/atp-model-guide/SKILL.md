---
name: atp-model-guide
description: /analyze-then-pick: resolve the locked model's guide folder and which sections each step reads; add or update a model. Internal to that command.
user-invocable: false
---

# atp-model-guide — Load the locked model's guide by section

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## What this skill is for

Only the **locked model's** guide is ever read, and only the sections the current step names. A guide is a folder of section files with an index
(`ATP/models/<guide>.md`), built by `scripts/docs_tool.py split` from the guide written on `ATP/models/_TEMPLATE.md`; the section numbers are the template's.

## Resolve the guide

1. `T model-entry --id <model>` → `guide` (the index file), `sections_dir` (the folder), the entry (capabilities, `edit_kind`, durations, `output_9x16_720p`, `continuation`).
2. The index file holds the guide's identity (front matter, scope, evidence tags) and a table `§ | section | file | KB`. Read the index once for the folder's file names;
   a step then reads `sections_dir/<file>` for each § it names. An id that is not a row lives in its parent row (`§2.4` in a short guide is inside `§2`).
3. No guide for the id (`guide_exists` false, or a live model that is not in the index): read `ATP/models/_generic-fallback.md` (whole, it is small) and say so in the brief.
4. Live parameters win over the guide: `models_explore {action:"get", model_id}` once per run; note any drift in the brief.

## Which sections each step reads

| step (skill) | model guide sections |
|---|---|
| A8 / planning (`atp-analyze-produce`, `atp-plan-video`) | §1 at a glance, §3.14 integration and continuity, §5 failure modes (where the guide lists size or place as a limit), §6 model-specific features |
| E4 Edit Mode, Recreate plan (`atp-edit`, `atp-recreate-plan`) | §1 at a glance, §2.4 call recipes, §4.4 video edit / extension / motion transfer (the preserving mode and settings), §6 features |
| X2 request (`atp-write-request`) | §2.4 call recipes, §2.6 9:16/720p, §3.1 to §3.7 (structure, subject and identity, action, environment and light, chronology, camera, references), §3.10 to §3.14 (negatives, visible text, identity consistency, product fidelity, integration), **§4.0 official examples** (the pattern card), the §4.x of the request kind: 4.1 text-to-video, 4.2 start/end frame, 4.3 reference-to-video, 4.4 edit / extension / motion transfer; §3.8 frames and §3.9 audio only when used; §6 when a feature is planned |
| X3 inputs (`atp-inputs`) | §2.2 media roles, §3.7 references, §3.8 frames |
| X4 pre-generation QC (`atp-precheck`) | §5 strengths, weaknesses and failure modes, §7 pre-generation checklist |
| X5/X7 preflight and submit (`atp-submit`) | §2.1 parameters per model id, §2.3 duration/aspect/audio, §2.5 parameter gotchas |
| X9 QC and retries (`atp-qc`) | §5 failure table; §9 open questions when a retry is planned |

`§8 Sources` is read only when a claim must be checked. Other sections only when a step is in doubt about that feature.

## Rules

- Never read a guide of another model; never Read `ATP/models/index.json` whole (40 KB); never `join` a whole guide (that is for `/update-from-errors`).
- Prompting always follows the guide (contract item 4 and the Never list); where a section is missing in a short guide, the nearest parent row is read.
- A model's skill-like first-party prompt optimiser (for Seedance 2.5: Skill `sd25-pe`) may be used for the prompt text; it never replaces the guide's pattern card.

## Adding or updating a model

1. Research it from official sources; write the guide as one file from `ATP/models/_TEMPLATE.md` (tag every claim [OFFICIAL] / [HF] / [SECONDARY] / [INFERRED]; quote 3–8 official example prompts in §4.0; fill §2.6 and §3.11).
2. `python "$ATP/scripts/docs_tool.py" split ATP/models/<slug>.md` turns it into the index + section folder (lossless; it verifies the rejoin).
3. Add its entry to `ATP/models/index.json` and its id to `menu.order`. Nothing else changes: the command, the skills and the agents find it through `T model-entry`.
4. After editing a section file or adding one: `python "$ATP/scripts/docs_tool.py" index ATP/models/<slug>.md`, then `python "$ATP/scripts/docs_tool.py" check`.
5. Updating: bump `guide_version` and `last_verified` in the index file's front matter; on drift against `models_explore list`, update §2 and the index entry.

## Hand-off

Return to the skill that sent you here.
