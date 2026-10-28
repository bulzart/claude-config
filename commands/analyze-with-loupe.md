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
  - mcp__elevenlabs__search_voices
  - mcp__elevenlabs__search_voice_library
  - mcp__elevenlabs__get_voice
  - mcp__elevenlabs__list_models
  - mcp__elevenlabs__check_subscription
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

# /analyze-with-loupe

Arguments: `$ARGUMENTS`

You are running the **/analyze-with-loupe** command.

This file is only the **router**, and it is small on purpose. The pipeline is split into **phase skills** (`awl-*`, one per mode and per step) and its
rules and data into **section files** (`AWL/reference/<name>/`, `AWL/models/<guide>/`, `AWL/higgsfield/higgsfield-mcp/`), so that every phase loads
only what it needs and the context of a run does not rot. The skills are interconnected: each ends with a hand-off that names the next one.

`AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` ·
`T` = `"$PY" "$AWL/scripts/awl.py"` (one JSON object on its last line; run through Bash) · `RUN` = `AWL/runs/<stamp>-<slug>/`.

## How the pipeline loads (obey throughout)

1. **Start by invoking Skill `awl-start` with `$ARGUMENTS` as its args**, after the resume and feedback checks below. Then follow each skill's **Hand-off**: when a phase ends it records
   `T state --run RUN set stage=… next_skill=…` and names the next skill. Invoke that skill when you reach it, never earlier.
2. **Load only what the current phase names.** Each skill has a "Read now" list of exact section files (some conditional); read those and nothing else unless a step
   says so. Never Read a whole reference, a whole guide or `models/index.json`; never run `docs_tool.py join` in a run. A section already read in this session is not read again.
3. **Citations.** `file.md §id` is a section of `AWL/reference/<file>/` (a model guide: `AWL/models/<guide>/`; the Higgsfield guide: `AWL/higgsfield/higgsfield-mcp/`).
   `file.md` itself is only an index (a table `§ | section | file | KB`). Resolve a citation that no "Read now" list covers with that table or Glob `AWL/reference/<file>/*_<id>_*.md`;
   an id that is not a row lives in its nearest parent row. Labels such as A7b, X9, E5, "item 19" resolve with the **labels** table below.
4. **A phase boundary is a safe cut.** Everything a later phase needs is in `RUN/state.json` and the run files, not in this conversation. When many phases lie behind you and the context is
   long, tell the user in one line that they may run `/compact` (or open a new session and send `/analyze-with-loupe resume <RUN>`); nothing is lost. After a compaction, or on resume,
   **re-invoke the skill named in `state.json → next_skill`**: its text may have been summarised away. Inside the per-video loop a run resumes at the video level
   (`state.json` holds `video` and `next_skill`; the ledger and the files on disk show the step reached).
5. **Agents never receive this file.** A production agent gets a contract that names the skills to invoke (Skill tool; if it is unavailable or the name is not found, Read
   `C:/Users/Glaresquare1/.claude/skills/<name>/SKILL.md` and follow it); it reads the same section lists as the main session and nothing else. An analysis agent is briefed by the prompt
   in `reference/analysis-protocol/` §7.

## Resume, and a video reported as wrong

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json`. A run whose `state.json` has no `audio_ingest` is asked the audio question (`awl-start` step 5b, item 24) before any `prep-all`.
     No `voiceover` key: no own voiceover, never asked (item 31); `voiceover.enabled` true: the ElevenLabs tools are loaded again before the next take. A Create run without `memes` includes them, never asked (item 32). Without the `effort` key it keeps its old rates, never asked; an empty `effort` (`null`) is asked (`awl-start` step 5d) before any `prep-all` or spawn (item 33).
   Run `T loupe ensure` and update `loupe` in `state.json` (a run without the key counts as `up`; Loupe may have been stopped since).
   Then invoke the skill named by `next_skill` in `state.json`. A run made before this layout has none: take the phase from `stage` / `next_step` with the map below
   (for example `stage=analyzed next_step=count` → A5 in `awl-analyze-study`; videos in `videos[]` but not all done → `awl-analyze-produce`; Edit Mode → `awl-edit`).

If `$ARGUMENTS` or the opening message reports a delivered video as wrong (it names a video, a CapCut project or a run and says what was not right), invoke Skill `awl-feedback` first
and handle it before anything else (item 22).

## Core rules (one line each; the full text of each sits in the skill that owns it)

1. **Normal command, never a workflow.** Run everything in this conversation with ordinary tools.
   Never create, call, convert to, or delegate to a Claude Code Workflow (the `Workflow` tool is
   disabled for this command). Higgsfield's server-side "workflow" recipes are only documentation, and
   their content is already copied locally.
2. **Agents.** Analysis agents: 0 by default, 1 for many videos, 2 for a large folder. Production agents: Analyze Mode only, one per video, at most the effort level's count at once (5 for a run made before item 33); they never overlap, never ask, never spawn agents. Edit Mode uses none. → `awl-analyze-produce`
3. **Generation lanes.** One job in flight per video lane, at most 5 per run, always through the ledger; never `generate_video_batch`; a multi-clip video runs clip by clip. → `awl-submit`
4. **One model per run**, picked at the start (a menu of every available model), then locked: never re-ask, switch or suggest switching; read only the locked model's guide, by section. → `awl-start`, `awl-model-guide`
5. **Fixed output: vertical 9:16 at 720p (720×1280)** for every generation in both modes. Never ask.
   Map it to each model's own parameters (`index.json → output_9x16_720p`) and conform
   deterministically. Never stretch.
6. **Text.** Edit Mode removes all source text unless the user keeps some. Analyze Mode generates clean plates and places all overlay text afterwards as CapCut layers in the house text style (horizontally centred, no emoji). → `awl-plan-video`, `awl-postprocess`
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
9. **One interconnected system.** Every generation is planned with `reference/generation-system/` (work backward, entity state ledger, integration analysis, anti-slop gate, model translation, pre-generation QC). → `awl-plan-video`
10. **Honest reporting.** Never claim a generation, upload or check that did not happen. Report
    failures with the real error.
11. **Client assets come only from paths the user gives** (Analyze: once at the start; Edit: for each edit); never from the references, edit-source or examples folders. → `awl-start`, `awl-asset-plan`
12. **Generation discipline.** Every paid call through `T ledger begin/set`; never resubmit after a timeout or unclear answer until checked; never repeat an identical finished request; preflight once per distinct request; no test or "just in case" calls. → `awl-submit`
13. **Edit Mode review** after every attempt; changes re-apply to the original source; the next video starts only after approval. → `awl-edit`
14. **Analyze Mode: the client's product is always in the video**: swap, contents or natural placement, physically and logically correct. → `awl-asset-plan`, `awl-plan-video`
15. **Analyze Mode asks permission in exactly one case**: a video over 30 s needing 2+ generations (A7b); the other questions are the fix generation after a QC finding, only when the user chose `ask` (item 27), and in Free the one confirmation of the plan (A6f). Blockers are reported, not asked; no reference review or "Go" before an upload or a generation (the user, 2026-10-27). → `awl-asset-plan`, `awl-free-plan`
16. **Analyze Mode: reference inserts are cut, never generated; every video ends as a CapCut project** `DD_Mon_YYYY_vNN`. Create cuts them in only when the user chose memes (item 32). → `awl-recreate-plan`, `awl-plan-video`, `awl-postprocess`
17. **Three Analyze sub-modes, chosen at the start, never mixed**: Recreate (edit the original references with the client's assets), Create (new videos from the analysed patterns; no reference is ever an input) and Free (the user's own requirement decides what the videos achieve and how, with references analysed first or from the requirement alone; every video carries its own kind, `recreate` or `create`, and the pipeline keeps the hard rules, the locked model's own prompting, the QC stack and Loupe's samples; one confirmation of the plan, then no questions). → `awl-start`, `awl-free-plan`
18. **Examples** (the user's own finished videos, optional, both modes) are study material for the house approach; never assets. → `awl-analyze-prepare`, `awl-analyze-study`
19. **Source fidelity** (Edit Mode, Recreate): only the planned operations change; the original audio goes back under the new picture; a sync check confirms it. → `awl-recreate-plan`, `awl-write-request`, `awl-edit`
20. **The pipeline is also the creative team** (`reference/creative-direction/`): goal, audience, trend read, scored concept seeds, sharpness gate, copy test. → `awl-analyze-study`, `awl-create-plan`
21. **Brand guardrails** from the client's documents decide what may be picked and what must be edited (core hit → dismiss; peripheral → edit). The pipeline has no content rules of its own. → `awl-analyze-prepare`, `awl-analyze-study`, `awl-plan-video`
22. **No error ledger**: a video the user reports as wrong is diagnosed in pipeline terms in its brief, then fixed; a lesson the references do not hold is written, generalised, into the section that owns it (on the user's yes). → `awl-feedback`
23. **Caught flags**: every prompt/video Higgsfield flags is recorded in Loupe before the request changes (`T caught-flag add`); the record is written, never read during a run, and only the first request of a video (`T prompt-template`: the agent briefs the judge, Loupe's Opus keeper, which reads the saved prompts of the samples it chooses and answers the prompt template the request is crafted from; not asked again before generation) and QC after generation (`T qc-consult`, carrying the prompt used, the template and the brief) consult Loupe's separate sample library; the prompts of a sample's two takes reach the judge whole from Loupe's record and an agent as files (`prompts_files`, `T sample-prompts`), never compared by a script. → `awl-submit`, `awl-qc`, `awl-write-request`
24. **Audio ingest is the user's choice, once per run**: at the start the user picks Whisper speech-to-text of every video's audio or frames only; `state.json → audio_ingest` (`whisper` | `frames-only`) is the only source, no step picks a default (`T prep-all` stops without it), a frames-only run writes no transcript and every speech field says `audio not ingested`, never `no speech`; whatever needs the audio file itself (the original audio restored, loudness, the sound profile, the sync check) runs in both modes. → `awl-start`, `awl-analyze-prepare`, `awl-edit`
25. **Scripts gather, agents decide.** The toolkit measures, extracts, records and calculates and never judges: no verdict, label, rank or gate comes from a script (`sync-check`, `scale`, `qc`, `conform`, `audio-profile`, the OCR spans and the ledger return numbers and facts; the model menu picks nothing). Every judgement is the agent's, written with its reason where the step records it; the numbers the references give are rules of thumb. → every skill, `pipeline/preprocessing.md`
26. **Pilot first.** From the effort level's count (5 videos for a run made before item 33), the first video goes through X7–X10 and its QC (with QC fixes `off`: X7–X10 without QC, its technical outcome only) before the other plans are finished and the other agents are spawned: a recipe fault costs one generation, not twenty. → `awl-analyze-produce`
27. **QC fixes** (every Analyze sub-mode: Recreate, Create, Free): at the start the user chooses `ask`, `auto` or `off` (`state.json → qc_fixes`) for QC and the fix generation after a QC finding. `ask`: from the first video on, when QC finds issues or anomalies that only a new generation can fix, the production agent prepares the fix and stops with a proposal, the main session asks the user, and no credits are spent until the user says yes. `auto`: the QC agents regenerate once on their own and ship the best take flagged. `off`: no QC agent after a video's first generation at all; each video is generated once and delivered unchecked, and the user says what to fix after the wrap-up (item 22). Local post-fixes and CapCut fixes never ask. → `awl-start` (the question), `awl-qc`, `awl-analyze-produce`, `awl-postprocess`, `awl-record`, `awl-wrapup`
31. **Own voiceover (ElevenLabs).** Create asks before the model menu how the spoken words are made: **native** (the take drives the generation: Wan 3.0, Wan 3.0 Prime, Wan 2.7), **lipsync** (any model, then a `sync_so` pass with the take), **overlay** (no dialogue, the take over the video) or the model's own audio; then the voice, the language and any accent or dialect. Free only from its requirement; never Recreate or Edit Mode. `state.json → voiceover`, `reference/voiceover.md`. → `awl-start`, `awl-free-plan`, `awl-plan-video`, `awl-postprocess`, `awl-qc`
32. **Memes in Create (the user's choice).** Create asks beside the voiceover method: **include** (memes and other cut-in clips as the style calls for, item 16) or **none** (pure generation: no insert or meme sound of any kind; a reference's meme beat is played by the generated scene). It wins over the house approach; `state.json → memes`, none set = include. → `awl-start`, `awl-create-plan`, `awl-plan-video`, `awl-postprocess`, `awl-qc`
33. **Effort level (the user's choice, both modes).** Low, Medium, High, XHigh or Max (the settings before this choice), all five offered in plain chat, sets how densely the references are sampled, the agents at once and the pilot threshold (`state.json → effort`, read by `T prep-all` and the produce phase; a new run's is empty until stored, and `T prep-all` stops on it); coverage and the floors never change, and QC and Loupe are never part of it (`reference/effort.md`). → `awl-start`, `awl-analyze-prepare`, `awl-analyze-produce`
34. **The user's folders are read-only** (the user, 2026-10-27): nothing in the references, assets, examples or edit-source folders is moved, renamed, deleted or overwritten by this session or any agent; a file needed in the run folder or elsewhere is copied, never moved (only the toolkit adds its own derived folders there: `files_audio/`, `videos_without_audio/`, Edit Mode's `final/`). The `awl_input_guard` hook refuses a move, delete, Write or Edit inside the references, edit-source or examples folders of a run that is not done. → every skill

## Phases (the skills)

| Phase | Skill | Mode | Next |
|---|---|---|---|
| Start: mode, sub-mode, model, inputs, run | `awl-start` | both | `awl-analyze-prepare` (Analyze) · `awl-edit` (Edit) |
| A1–A2b inventory, preprocessing, documents, guardrails, asset registry | `awl-analyze-prepare` | Analyze | `awl-analyze-study` (`awl-free-plan` for Free without references) |
| A3–A5 video analysis, synthesis, count | `awl-analyze-study` | Analyze | `awl-create-plan` (Create) · `awl-recreate-plan` (Recreate) · `awl-free-plan` (Free with references) |
| A6 style groups, scored concepts | `awl-create-plan` | Create | `awl-asset-plan` |
| A6r pick the references, plan the edits | `awl-recreate-plan` | Recreate | `awl-asset-plan` |
| A6f the user's requirement becomes the plan, confirmed once | `awl-free-plan` | Free | `awl-asset-plan` |
| A7–A7b asset plan, long-video permission | `awl-asset-plan` | Analyze | `awl-analyze-produce` |
| A8–A10 prepare every video, production agents, reports | `awl-analyze-produce` | Analyze | `awl-wrapup` |
| E1–E7, X9-R intake, operations, source, review | `awl-edit` | Edit | `awl-wrapup` |
| §6, §6b wrap-up, feedback question, Topaz | `awl-wrapup` | both | — |
| item 22 a delivered video reported as wrong | `awl-feedback` | both | — |
| the locked model's guide, by section | `awl-model-guide` | both | — |

**The per-video loop** (both modes): X1 `awl-plan-video` → X2 `awl-write-request` → X3 `awl-inputs` → X4–X6 `awl-precheck` → X7 `awl-submit` (X5 again when the request changed) →
X8 `awl-postprocess` → X9 `awl-qc` → (Edit Mode: X9-R in `awl-edit`) → X10 `awl-record`. Analyze Mode: this session runs X1, X2 and X4 for every video, X3 for the shared uploads, then X5–X6 for every video (A9);
each production agent then runs X3 → X7 → X8 → X9 → X10 for its own video by invoking those skills from its contract (Analyze Mode: the CapCut project of X8 step 6 is built after the picture passes X9, then X9 checks
it). A regeneration or re-edit runs `awl-write-request` → (`awl-inputs` for new inputs) → `awl-submit` → `awl-postprocess` → `awl-qc`. Edit Mode runs the whole loop in this session, one video at a time.

**Labels** (as cited in the skills and the references): §1 paths and §2 Start, items 4 · 11 · 17 → `awl-start` · A1, A2, A2b → `awl-analyze-prepare` · A3, A4, A5 → `awl-analyze-study` · A6 → `awl-create-plan` ·
A6r (the "R-steps" of item 17; E4–E5 as Recreate uses them are repeated in it) → `awl-recreate-plan` · A6f → `awl-free-plan` · A7, A7b → `awl-asset-plan` · A8, A9, A9b, A10 → `awl-analyze-produce` · E1–E7, X9-R → `awl-edit` · X1 → `awl-plan-video` · X2 → `awl-write-request` · X3 → `awl-inputs` ·
X4, X5, X6 → `awl-precheck` (X5 also in `awl-submit`) · X7 → `awl-submit` · X8 → `awl-postprocess` · X9 → `awl-qc` · X10 → `awl-record` · §6, §6b → `awl-wrapup` · item 22 → `awl-feedback` · item 23 → `awl-submit` · item 24 → `awl-start` (the question), `awl-analyze-prepare` and `awl-edit` (`prep-all`) · item 25 → every skill · item 26 → `awl-analyze-produce` · item 27 → `awl-start` (the question), `awl-qc` (the proposal), `awl-analyze-produce` (the fix question) · item 31 → `awl-start`, the plan skills, every per-video skill, `awl-analyze-produce`, `awl-wrapup`, `awl-feedback` · item 32 → `awl-start`, `awl-free-plan`, `awl-create-plan`, `awl-asset-plan`, `awl-plan-video`, `awl-precheck`, `awl-postprocess`, `awl-qc`, `awl-analyze-produce` · item 33 → `awl-start`, `awl-analyze-prepare`, `awl-edit`, `awl-analyze-study`, `awl-analyze-produce`, `awl-wrapup` · item 34 → every skill and agent (the `awl_input_guard` hook).
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
