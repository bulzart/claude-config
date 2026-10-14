---
description: Analyze a folder of reference material (or take videos to edit), learn what makes it work, then generate new vertical 9:16 720p videos through Higgsfield MCP with model-specific prompting — one video at a time.
argument-hint: "analyze <references-folder> assets <asset files/folders…> [examples <folder>] | edit <video files/folders…> [examples <folder>] | resume [run-dir]"
disable-model-invocation: true
disallowed-tools:
  - Workflow
allowed-tools:
  - Skill
  - Read
  - Glob
  - Grep
  - ToolSearch
  - AskUserQuestion
  - "Bash(C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe *)"
  - "Bash(python *)"
  - "Bash(ffprobe *)"
  - "PowerShell(cd *)"
  - "PowerShell(Get-ChildItem *)"
  - mcp__higgsfield__models_explore
  - mcp__higgsfield__balance
  - mcp__higgsfield__transactions
  - mcp__higgsfield__jobs_wait
  - mcp__higgsfield__show_generations
  - mcp__higgsfield__list_workspaces
  - mcp__higgsfield__list_projects
  - mcp__higgsfield__show_reference_elements
  - WebSearch
  - WebFetch
  - "Bash(capcut *)"
  - mcp__capcut__capcut_list_drafts
  - mcp__capcut__capcut_clone_draft
  - mcp__capcut__capcut_read_timeline
  - mcp__capcut__capcut_add_video
  - mcp__capcut__capcut_add_image
  - mcp__capcut__capcut_add_audio
  - mcp__capcut__capcut_add_text
  - mcp__capcut__capcut_add_track
  - mcp__capcut__capcut_split_segment
  - mcp__capcut__capcut_move_segment
  - mcp__capcut__capcut_trim_segment
  - mcp__capcut__capcut_set_props
  - mcp__capcut__capcut_set_track_mute
  - mcp__capcut__capcut_add_audio_fade
  - mcp__capcut__capcut_add_transition
  - mcp__capcut__capcut_validate
  - mcp__capcut__capcut_save
  - mcp__capcut__capcut_discard
  - mcp__capcut__capcut_undo
---

# /analyze-then-pick

Arguments: `$ARGUMENTS`

You are running the **/analyze-then-pick** command.

This file is only the **router**, and it is small on purpose. The pipeline is split into **phase skills** (`atp-*`, one per mode and per step) and its
rules and data into **section files** (`ATP/reference/<name>/`, `ATP/models/<guide>/`, `ATP/higgsfield/higgsfield-mcp/`), so that every phase loads
only what it needs and the context of a run does not rot. The skills are interconnected: each ends with a hand-off that names the next one.

`ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` ·
`T` = `"$PY" "$ATP/scripts/atp.py"` (one JSON object on its last line; run through Bash) · `RUN` = `ATP/runs/<stamp>-<slug>/`.

## How the pipeline loads (obey throughout)

1. **Start by invoking Skill `atp-start` with `$ARGUMENTS` as its args**, after the resume and feedback checks below. Then follow each skill's **Hand-off**: when a phase ends it records
   `T state --run RUN set stage=… next_skill=…` and names the next skill. Invoke that skill when you reach it, never earlier.
2. **Load only what the current phase names.** Each skill has a "Read now" list of exact section files (some conditional); read those and nothing else unless a step
   says so. Never Read a whole reference, a whole guide or `models/index.json`; never run `docs_tool.py join` in a run. A section already read in this session is not read again.
3. **Citations.** `file.md §id` is a section of `ATP/reference/<file>/` (a model guide: `ATP/models/<guide>/`; the Higgsfield guide: `ATP/higgsfield/higgsfield-mcp/`).
   `file.md` itself is only an index (a table `§ | section | file | KB`). Resolve a citation that no "Read now" list covers with that table or Glob `ATP/reference/<file>/*_<id>_*.md`;
   an id that is not a row lives in its nearest parent row. Labels such as A7b, X9, E5, "item 19" resolve with the **labels** table below.
4. **A phase boundary is a safe cut.** Everything a later phase needs is in `RUN/state.json` and the run files, not in this conversation. When many phases lie behind you and the context is
   long, tell the user in one line that they may run `/compact` (or open a new session and send `/analyze-then-pick resume <RUN>`); nothing is lost. After a compaction, or on resume,
   **re-invoke the skill named in `state.json → next_skill`**: its text may have been summarised away. Inside the per-video loop a run resumes at the video level
   (`state.json` holds `video` and `next_skill`; the ledger and the files on disk show the step reached).
5. **Agents never receive this file.** A production agent gets a contract that names the skills to invoke (Skill tool; if it is unavailable or the name is not found, Read
   `C:/Users/Glaresquare1/.claude/skills/<name>/SKILL.md` and follow it); it reads the same section lists as the main session and nothing else. An analysis agent is briefed by the prompt
   in `reference/analysis-protocol/` §7.

## Resume, and a video reported as wrong

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json`.
   Then invoke the skill named by `next_skill` in `state.json`. A run made before this layout has none: take the phase from `stage` / `next_step` with the map below
   (for example `stage=analyzed next_step=count` → A5 in `atp-analyze-study`; videos in `videos[]` but not all done → `atp-analyze-produce`; Edit Mode → `atp-edit`).

If `$ARGUMENTS` or the opening message reports a delivered video as wrong (it names a video, a CapCut project or a run and says what was not right), invoke Skill `atp-feedback` first
and handle it before anything else (item 22).

## Core rules (one line each; the full text of each sits in the skill that owns it)

1. **Normal command, never a workflow.** Run everything in this conversation with ordinary tools.
   Never create, call, convert to, or delegate to a Claude Code Workflow (the `Workflow` tool is
   disabled for this command). Higgsfield's server-side "workflow" recipes are only documentation, and
   their content is already copied locally.
2. **Agents.** Analysis agents: 0 by default, 1 for many videos, 2 for a large folder. Production agents: Analyze Mode only, one per video, at most 5 at once; they never overlap, never ask, never spawn agents. Edit Mode uses none. → `atp-analyze-produce`
3. **Generation lanes.** One job in flight per video lane, at most 5 per run, always through the ledger; never `generate_video_batch`; a multi-clip video runs clip by clip. → `atp-submit`
4. **One model per run**, picked at the start (a menu of every available model), then locked: never re-ask, switch or suggest switching; read only the locked model's guide, by section. → `atp-start`, `atp-model-guide`
5. **Fixed output: vertical 9:16 at 720p (720×1280)** for every generation in both modes. Never ask.
   Map it to each model's own parameters (`index.json → output_9x16_720p`) and conform
   deterministically. Never stretch.
6. **Text.** Edit Mode removes all source text unless the user keeps some. Analyze Mode generates clean plates and places all overlay text afterwards as CapCut layers in the house text style (horizontally centred, no emoji). → `atp-plan-video`, `atp-postprocess`
7. **Client- and niche-agnostic.**
   - Never assume an industry, a product, a character swap, or a fixed template.
   - Infer the domain, the entities, what to preserve / replace / adapt / ignore, and the objective
     from the files and instructions.
   - Documents are authoritative requirements.
8. **Provenance.** In analysis, plans and briefs, keep separate:
   - **[E]** evidence
   - **[I]** inference
   - **[U]** user instruction
   - **[A]** client asset
   - **[M]** model knowledge
   - **[G]** generation instruction
9. **One interconnected system.** Every generation is planned with `reference/generation-system/` (work backward, entity state ledger, integration analysis, anti-slop gate, model translation, pre-generation QC). → `atp-plan-video`
10. **Honest reporting.** Never claim a generation, upload or check that did not happen. Report
    failures with the real error.
11. **Client assets come only from paths the user gives** (Analyze: once at the start; Edit: for each edit); never from the references, edit-source or examples folders. → `atp-start`, `atp-asset-plan`
12. **Generation discipline.** Every paid call through `T ledger begin/set`; never resubmit after a timeout or unclear answer until checked; never repeat an identical finished request; preflight once per distinct request; no test or "just in case" calls. → `atp-submit`
13. **Edit Mode review** after every attempt; changes re-apply to the original source; the next video starts only after approval. → `atp-edit`
14. **Analyze Mode: the client's product is always in the video**: swap, contents or natural placement, physically and logically correct. → `atp-asset-plan`, `atp-plan-video`
15. **Analyze Mode asks permission in exactly one case**: a video over 30 s needing 2+ generations (A7b). Blockers are reported, not asked. → `atp-asset-plan`
16. **Analyze Mode: reference inserts are cut, never generated; every video ends as a CapCut project** `DD_Mon_YYYY_vNN`. → `atp-recreate-plan`, `atp-plan-video`, `atp-postprocess`
17. **Two Analyze sub-modes, chosen at the start, never mixed**: Recreate (edit the original references with the client's assets) and Create (new videos from the analysed patterns; no reference is ever an input). → `atp-start`
18. **Examples** (the user's own finished videos, optional, both modes) are study material for the house approach; never assets. → `atp-analyze-prepare`, `atp-analyze-study`
19. **Source fidelity** (Edit Mode, Recreate): only the planned operations change; the original audio goes back under the new picture; a sync check confirms it. → `atp-recreate-plan`, `atp-write-request`, `atp-edit`
20. **The pipeline is also the creative team** (`reference/creative-direction/`): goal, audience, trend read, scored concept seeds, sharpness gate, copy test. → `atp-analyze-study`, `atp-create-plan`
21. **Brand guardrails** from the client's documents decide what may be picked and what must be edited (core hit → dismiss; peripheral → edit). The pipeline has no content rules of its own. → `atp-analyze-prepare`, `atp-analyze-study`, `atp-plan-video`
22. **No error ledger**: a video the user reports as wrong is diagnosed in pipeline terms in its brief, then fixed; lessons are generalised by `/update-from-errors`. → `atp-feedback`
23. **Caught flags**: every prompt/video Higgsfield flags is recorded before the request changes (`T caught-flag add`); the page is written, never read. → `atp-submit`

## Phases (the skills)

| Phase | Skill | Mode | Next |
|---|---|---|---|
| Start: mode, sub-mode, model, inputs, run | `atp-start` | both | `atp-analyze-prepare` (Analyze) · `atp-edit` (Edit) |
| A1–A2b inventory, preprocessing, documents, guardrails, asset registry | `atp-analyze-prepare` | Analyze | `atp-analyze-study` |
| A3–A5 video analysis, synthesis, count | `atp-analyze-study` | Analyze | `atp-create-plan` (Create) · `atp-recreate-plan` (Recreate) |
| A6 style groups, scored concepts | `atp-create-plan` | Create | `atp-asset-plan` |
| A6r pick the references, plan the edits | `atp-recreate-plan` | Recreate | `atp-asset-plan` |
| A7–A7b asset plan, long-video permission | `atp-asset-plan` | Analyze | `atp-analyze-produce` |
| A8–A10 prepare every video, production agents, reports | `atp-analyze-produce` | Analyze | `atp-wrapup` |
| E1–E7, X9-R intake, operations, source, review | `atp-edit` | Edit | `atp-wrapup` |
| §6, §6b wrap-up, feedback question, Topaz | `atp-wrapup` | both | — |
| item 22 a delivered video reported as wrong | `atp-feedback` | both | — |
| the locked model's guide, by section | `atp-model-guide` | both | — |

**The per-video loop** (both modes): X1 `atp-plan-video` → X2 `atp-write-request` → X3 `atp-inputs` → X4–X6 `atp-precheck` → X7 `atp-submit` (X5 again when the request changed) →
X8 `atp-postprocess` → X9 `atp-qc` → (Edit Mode: X9-R in `atp-edit`) → X10 `atp-record`. Analyze Mode: this session runs X1, X2 and X4 for every video, X3 for the shared uploads, then X5–X6 for every video (A9);
each production agent then runs X3 → X7 → X8 → X9 → X10 for its own video by invoking those skills from its contract (Analyze Mode: the CapCut project of X8 step 6 is built after the picture passes X9, then X9 checks
it). A regeneration or re-edit runs `atp-write-request` → (`atp-inputs` for new inputs) → `atp-submit` → `atp-postprocess` → `atp-qc`. Edit Mode runs the whole loop in this session, one video at a time.

**Labels** (as cited in the skills and the references): §1 paths and §2 Start, items 4 · 11 · 17 → `atp-start` · A1, A2, A2b → `atp-analyze-prepare` · A3, A4, A5 → `atp-analyze-study` · A6 → `atp-create-plan` ·
A6r (the "R-steps" of item 17; E4–E5 as Recreate uses them are repeated in it) → `atp-recreate-plan` · A7, A7b → `atp-asset-plan` · A8, A9, A9b, A10 → `atp-analyze-produce` · E1–E7, X9-R → `atp-edit` · X1 → `atp-plan-video` · X2 → `atp-write-request` · X3 → `atp-inputs` ·
X4, X5, X6 → `atp-precheck` (X5 also in `atp-submit`) · X7 → `atp-submit` · X8 → `atp-postprocess` · X9 → `atp-qc` · X10 → `atp-record` · §6, §6b → `atp-wrapup` · item 22 → `atp-feedback` · item 23 → `atp-submit`.
A rule that two phases both act on is written in both skills.

## Never (global; each skill carries the rest of the Never list for its own phase)

- Never use or create a Claude Code Workflow.
- Never spawn more than 2 analysis agents, more than 5 production agents at once, or a production
  agent in Edit Mode. Never give agents overlapping work.
- Never read model guides other than the locked one.
- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Never claim results you did not verify.
