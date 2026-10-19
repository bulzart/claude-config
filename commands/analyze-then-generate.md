---
description: Analyze a folder of reference material (or take videos to edit), learn what makes it work, then either generate new vertical 9:16 720p videos through Higgsfield MCP (Recreate, virality-backed Create, Edit) or find the next three products to sell with the same viral approach (Viral-Browser, which asks the market and price range and generates nothing).
argument-hint: "analyze <references-folder> assets <asset files/folders…> [examples <folder>] [qc-fixes ask|auto] | edit <video files/folders…> [examples <folder>] | viral-browser <references-folder> [baseline <folder>] [market us|eu|global] [price <min>-<max> <currency>] [depth quick|standard|deep] | resume [run-dir]"
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
  - mcp__higgsfield__tiktok_accounts
  - mcp__higgsfield__tiktok_music_trending
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

# /analyze-then-generate

Arguments: `$ARGUMENTS`

You are running the **/analyze-then-generate** command.

Modes: **Edit Mode**, and **Analyze Mode** with three sub-modes: **Recreate**, **Create** and **Viral-Browser**. In Viral-Browser the references become a **source of ideas**, nothing is
generated, and the run returns the **next three products to sell**, each with a blueprint and a reference pack. Create is virality-backed (the references are mined for why they spread and blended with the
client's product). Items 3–6, 12–16 and 19 concern video generation and apply to Edit Mode, Recreate and Create; item 27 (QC fixes) applies to Recreate and Create; items 24–26 govern Viral-Browser.

This file is only the **router**, and it is small on purpose. The pipeline is split into **phase skills** (`atg-*`, one per mode and per step) and its rules and data into **section files**
(`ATG/reference/<name>/`, `ATG/models/<guide>/`, `ATG/higgsfield/higgsfield-mcp/`), so that every phase loads only what it needs and the context of a run does not rot. The skills are interconnected:
each ends with a hand-off that names the next one.

`ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` ·
`T` = `"$PY" "$ATG/scripts/atg.py"` (one JSON object on its last line; run through Bash) · `RUN` = `ATG/runs/<stamp>-<slug>/`.

**Scripts gather, the agent decides** (the user's rule, 2026-10-12; every mode, every `T` command). `T` measures, extracts, records, tabulates and calculates; it never hands out a verdict, status or label
derived from content, never applies a threshold that refuses, caps or changes an answer, never ranks, picks or breaks a tie, never compares texts or counts words to decide anything, and refuses only a bad argument, a missing file
or tool, a damaged ledger, an unsafe web address or a failed ffmpeg run (the mechanical exceptions: file locks, the submission ledger's fingerprint bookkeeping, the page reader's public-address guard, CapCut's
"close it first" and the locked house preset). **You** read its numbers and tables, decide under the mode's specification, and record every decision with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`,
`ledger set --status superseded --note`). The old thresholds (0.10 s sync tolerance, 15 % / 25 % size bands, 12 % crop loss, pool shares, rating floors, evidence caps) are rules of thumb: apply them with
judgement, depart from them when the evidence says so, and write down what you applied, what you set aside and why. Independent checks stay fresh AI agents (niche audit, blind scoring, red team, reference
packs), never script gates.

## How the pipeline loads (obey throughout)

1. **Start by invoking Skill `atg-start` with `$ARGUMENTS` as its args**, after the resume and feedback checks below. Then follow each skill's **Hand-off**: when a phase ends it records
   `T state --run RUN set stage=… next_skill=…` and names the next skill. Invoke that skill when you reach it, never earlier. (`atg-start` hands a Viral-Browser run to `atg-vb-cards` as soon as the sub-mode is known.)
2. **Load only what the current phase names.** Each skill has a "Read now" list of exact section files (some conditional); read those and nothing else unless a step
   says so. Never Read a whole reference, a whole guide or `models/index.json`; never run `docs_tool.py join` in a run. A section already read in this session is not read again.
3. **Citations.** `file.md §id` is a section of `ATG/reference/<file>/` (a model guide: `ATG/models/<guide>/`; the Higgsfield guide: `ATG/higgsfield/higgsfield-mcp/`).
   `file.md` itself is only an index (a table `§ | section | file | KB`). Resolve a citation that no "Read now" list covers with that table or Glob `ATG/reference/<file>/*_<id>_*.md`;
   an id that is not a row lives in its nearest parent row. Labels such as A7b, X9, E5, V5, "item 19" resolve with the **labels** table below.
4. **A phase boundary is a safe cut.** Everything a later phase needs is in `RUN/state.json` and the run files, not in this conversation. When many phases lie behind you and the context is
   long, tell the user in one line that they may run `/compact` (or open a new session and send `/analyze-then-generate resume <RUN>`); nothing is lost. After a compaction, or on resume,
   **re-invoke the skill named in `state.json → next_skill`**: its text may have been summarised away. Inside the per-video loop a run resumes at the video level
   (`state.json` holds `video` and `next_skill`; the ledger and the files on disk show the step reached).
5. **Agents never receive this file.** A production agent gets a contract that names the skills to invoke (Skill tool; if it is unavailable or the name is not found, Read
   `C:/Users/Glaresquare1/.claude/skills/<name>/SKILL.md` and follow it); it reads the same section lists as the main session and nothing else. An analysis agent is briefed by the prompt
   in `reference/analysis-protocol/` §7 (Create and Viral-Browser: `reference/viral-browser/` §13); Viral-Browser's other agents by the prompts of `reference/viral-browser/` §13.

## Resume, and a video reported as wrong

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done; for Viral-Browser the candidates, the evidence rows and the picks so far);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json` (Viral-Browser stores its brief under `brief.*`).
   Run `T loupe ensure` and update `loupe` in `state.json` (a run without the key counts as `up`; Loupe may have been stopped since).
   Then invoke the skill named by `next_skill` in `state.json`. A run made before this layout has none: take the phase from `stage` / `next_step` with the map below
   (for example `stage=analyzed next_step=count` → A5 in `atg-analyze-study`; videos in `videos[]` but not all done → `atg-analyze-produce`; Edit Mode → `atg-edit`;
   Viral-Browser `next_step` cards → `atg-vb-cards`; synthesis, candidates, cost-basis → `atg-vb-synthesis`; research → `atg-vb-research`; scoring → `atg-vb-select`; blueprints → `atg-vb-deliver`; report-qc, wrap-up → `atg-vb-wrapup`).

If `$ARGUMENTS` or the opening message reports a delivered video, or a Viral-Browser pick, as wrong (it names a video, a CapCut project, a pick or a run and says what was not right), invoke Skill `atg-feedback` first
and handle it before anything else (item 22).

## Core rules (one line each; the full text of each sits in the skill that owns it)

1. **Normal command, never a workflow.** Run everything in this conversation with ordinary tools.
   Never create, call, convert to, or delegate to a Claude Code Workflow (the `Workflow` tool is
   disabled for this command). Higgsfield's server-side "workflow" recipes are only documentation, and
   their content is already copied locally.
2. **Agents.** Analysis agents: 0 by default, 1 for many videos, 2 for a large folder. Production agents: Analyze Mode (Recreate, Create) only, one per video, at most 5 at once; they never overlap, never ask, never spawn agents. Edit Mode uses none. Viral-Browser uses no production agent: at most 2 card agents, one niche-audit agent, up to 3 research agents, one blind scoring agent, one red-team agent and up to 3 reference-pack agents (never alongside the research agents). → `atg-analyze-produce`, `atg-vb-*`
3. **Generation lanes.** One job in flight per video lane, at most 5 per run, always through the ledger (it records and reports; you decide whether to submit); never `generate_video_batch`; a multi-clip video runs clip by clip. → `atg-submit`
4. **One model per run**, picked at the start (a menu of every available model), then locked: never re-ask, switch or suggest switching; read only the locked model's guide, by section. Viral-Browser picks none. → `atg-start`, `atg-model-guide`
5. **Fixed output: vertical 9:16 at 720p (720×1280)** for every generation in both modes. Never ask.
   Map it to each model's own parameters (`index.json → output_9x16_720p`) and conform
   deterministically. Never stretch.
6. **Text.** Edit Mode removes all source text unless the user keeps some. Analyze Mode generates clean plates and places all overlay text afterwards as CapCut layers in the house text style (horizontally centred, no emoji). → `atg-plan-video`, `atg-postprocess`
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
9. **One interconnected system.** Every generation is planned with `reference/generation-system/` (work backward, entity state ledger, integration analysis, anti-slop gate, model translation, pre-generation QC). → `atg-plan-video`
10. **Honest reporting.** Never claim a generation, upload or check that did not happen. Report
    failures with the real error.
11. **Client assets come only from paths the user gives** (Analyze: once at the start; Edit: for each edit); never from the references, edit-source or examples folders. Viral-Browser asks for none. → `atg-start`, `atg-asset-plan`
12. **Generation discipline.** Every paid call through `T ledger begin/set`; never resubmit after a timeout or unclear answer until checked; never repeat an identical finished request; preflight once per distinct request; no test or "just in case" calls. → `atg-submit`
13. **Edit Mode review** after every attempt; changes re-apply to the original source; the next video starts only after approval. → `atg-edit`
14. **Analyze Mode: the client's product is always in the video** (Recreate, Create): swap, contents or natural placement, physically and logically correct. → `atg-asset-plan`, `atg-plan-video`
15. **Analyze Mode asks permission in exactly one case**: a video over 30 s needing 2+ generations (A7b); the one other question is the fix generation after a QC finding, and only when the user chose `ask` (item 27). Blockers are reported, not asked. → `atg-asset-plan`
16. **Analyze Mode: reference inserts are cut, never generated; every video ends as a CapCut project** `DD_Mon_YYYY_vNN`. → `atg-recreate-plan`, `atg-plan-video`, `atg-postprocess`
17. **Three Analyze sub-modes, chosen at the start, never mixed**: Recreate (edit the original references with the client's assets), Create (new virality-backed blends of the analysed mechanisms and the client's product; no reference is ever an input) and Viral-Browser (the references as ideas; products to sell; nothing generated). → `atg-start`
18. **Examples** (the user's own finished videos, optional, both modes) are study material for the house approach; never assets. → `atg-analyze-prepare`, `atg-analyze-study`
19. **Source fidelity** (Edit Mode, Recreate): only the planned operations change; the original audio goes back under the new picture; a sync check (numbers you read) confirms it. → `atg-recreate-plan`, `atg-write-request`, `atg-edit`
20. **The pipeline is also the creative team** (`reference/creative-direction/`): goal, audience, trend read, scored concept seeds, sharpness gate, copy test, and in Create the blend and template-lock tests with a virality rationale. → `atg-analyze-study`, `atg-create-plan`
21. **Brand guardrails** from the client's documents decide what may be picked and what must be edited (core hit → dismiss; peripheral → edit). The pipeline has no content rules of its own. → `atg-analyze-prepare`, `atg-analyze-study`, `atg-plan-video`
22. **No error ledger**: a video or a pick the user reports as wrong is diagnosed in pipeline terms in its brief (or `deliverables/feedback.md`), then fixed; a lesson the references do not hold is written, generalised, into the section that owns it (on the user's yes). → `atg-feedback`
23. **Caught flags**: every prompt/video Higgsfield flags is recorded in Loupe before the request changes (`T caught-flag add`); the record is written, never read during a run, and only QC (`T qc-consult`) and the first request of a video (`T plan-hints`, a few text-only hints, usually none) consult Loupe's separate sample library. → `atg-submit`, `atg-qc`, `atg-write-request`
24. **Viral-Browser: the references are a source of ideas and the run generates nothing**: no model, generation tool, credits, CapCut or assets, the references folder untouched; the brief (market, price range, selling model, tools) is asked, not assumed; three data-backed products, each with a blueprint and a reference pack (sourced specification and photo links, none downloaded); "no product passes" is a valid result. → `atg-vb-cards`
25. **Niche-bias control**: the references' product niche must not decide the answer: a niche vocabulary the agents build from the data (`T niches`) and a fresh niche-audit agent reads, a pool read for balance before research, a fresh blind scorer, a red-team reading for every pick and a written defence for a dominant-niche pick; no script ranks, caps, gates or picks. → `atg-vb-synthesis`, `atg-vb-select`
26. **Viral-Browser is autonomous after the brief**: the only questions are the brief, the picks feedback and the optional "continue to Create", which runs only on the user's yes and then follows every Create rule. → `atg-vb-wrapup`
27. **QC fixes** (Recreate, Create): at the start the user chooses `ask` or `auto` for the fix generation after a QC finding. `ask`: from the first video on, when QC finds issues or anomalies that only a new generation can fix, the production agent prepares the fix and stops with a proposal, the main session asks the user, and no credits are spent until the user says yes. `auto`: the QC agents correct on their own, without asking (one diagnosed regeneration per clip). Stored in `state.json → qc_fixes` (a run without it is `auto`). Local post-fixes, CapCut fixes and the retry of a job that failed with no output are never asked; Edit Mode is not asked (the user reviews every attempt). → `atg-start`, `atg-qc`, `atg-analyze-produce`

## Phases (the skills)

| Phase | Skill | Mode | Next |
|---|---|---|---|
| Start: mode, sub-mode, model, inputs, run | `atg-start` | all | `atg-analyze-prepare` (Recreate, Create) · `atg-vb-cards` (Viral-Browser) · `atg-edit` (Edit) |
| A1–A2b inventory, preprocessing, audio context, documents, guardrails, asset registry, product insights | `atg-analyze-prepare` | Recreate, Create | `atg-analyze-study` |
| A3–A5 video analysis (Create: virality mining), synthesis, count | `atg-analyze-study` | Recreate, Create | `atg-create-plan` (Create) · `atg-recreate-plan` (Recreate) |
| A6 style groups, blends, scored concepts | `atg-create-plan` | Create | `atg-asset-plan` |
| A6r pick the references, plan the edits | `atg-recreate-plan` | Recreate | `atg-asset-plan` |
| A7–A7b asset plan, long-video permission | `atg-asset-plan` | Recreate, Create | `atg-analyze-produce` |
| A8–A10 prepare every video, production agents, reports, QC-fix questions | `atg-analyze-produce` | Recreate, Create | `atg-wrapup` |
| V1–V2 inputs and brief, run, inventory, viral cards | `atg-vb-cards` | Viral-Browser | `atg-vb-synthesis` |
| V3–V4b corpus profile, niche vocabulary, candidates, cost basis | `atg-vb-synthesis` | Viral-Browser | `atg-vb-research` |
| V5 research wave | `atg-vb-research` | Viral-Browser | `atg-vb-select` |
| V6 blind scoring, red team, gates, the three picks | `atg-vb-select` | Viral-Browser | `atg-vb-deliver` |
| V7 blueprints, reference packs, deliverables | `atg-vb-deliver` | Viral-Browser | `atg-vb-wrapup` |
| V8–V9 report QC, wrap-up, picks feedback, continue to Create | `atg-vb-wrapup` | Viral-Browser | (Create flow on the user's yes) |
| E1–E7, X9-R intake, operations, source, review | `atg-edit` | Edit | `atg-wrapup` |
| §6, §6b wrap-up, feedback question, Topaz | `atg-wrapup` | Edit, Recreate, Create | — |
| item 22 a delivered video or a pick reported as wrong | `atg-feedback` | all | — |
| the locked model's guide, by section | `atg-model-guide` | Edit, Recreate, Create | — |

**The per-video loop** (Edit, Recreate, Create): X1 `atg-plan-video` → X2 `atg-write-request` → X3 `atg-inputs` → X4–X6 `atg-precheck` → X7 `atg-submit` (X5 again when the request changed) →
X8 `atg-postprocess` → X9 `atg-qc` → (Edit Mode: X9-R in `atg-edit`) → X10 `atg-record`. Analyze Mode: this session runs X1, X2 and X4 for every video, X3 for the shared uploads, then X5–X6 for every video (A9);
each production agent then runs X3 → X7 → X8 → X9 → X10 for its own video by invoking those skills from its contract (Analyze Mode: the CapCut project of X8 step 6 is built after the picture passes X9, then X9 checks
it). A regeneration or re-edit runs `atg-write-request` → (`atg-inputs` for new inputs) → `atg-submit` → `atg-postprocess` → `atg-qc`. Edit Mode runs the whole loop in this session, one video at a time. Viral-Browser has no per-video loop.

**Labels** (as cited in the skills and the references): §1 paths and §2 Start, items 4 · 11 · 17 → `atg-start` · A1, A2, A2b → `atg-analyze-prepare` · A3, A4, A5 → `atg-analyze-study` · A6 → `atg-create-plan` ·
A6r (the "R-steps" of item 17; E4–E5 as Recreate uses them are repeated in it) → `atg-recreate-plan` · A7, A7b → `atg-asset-plan` · A8, A9, A9b, A10 → `atg-analyze-produce` · V1, V2 → `atg-vb-cards` · V3, V4, V4b → `atg-vb-synthesis` ·
V5 → `atg-vb-research` · V6 → `atg-vb-select` · V7 → `atg-vb-deliver` · V8, V9 → `atg-vb-wrapup` · E1–E7, X9-R → `atg-edit` · X1 → `atg-plan-video` · X2 → `atg-write-request` · X3 → `atg-inputs` ·
X4, X5, X6 → `atg-precheck` (X5 also in `atg-submit`) · X7 → `atg-submit` · X8 → `atg-postprocess` · X9 → `atg-qc` · X10 → `atg-record` · §6, §6b → `atg-wrapup` · item 22 → `atg-feedback` · item 23 → `atg-submit` ·
items 24 → `atg-vb-cards`, 25 → `atg-vb-synthesis`, 26 → `atg-vb-wrapup`, 27 → `atg-start` (the choice), `atg-qc` (the proposal), `atg-analyze-produce` (the question).
A rule that two phases both act on is written in both skills.

## Never (global; each skill carries the rest of the Never list for its own phase)

- Never use or create a Claude Code Workflow.
- Never take a script's output for a decision: read what the `T` commands return, decide under the mode's rules (their numbers are rules of thumb), and record the decision with its reason. Never lower a gate or set a rule of thumb aside silently.
- Never spawn more than 2 analysis agents, more than 5 production agents at once, or a production agent in Edit Mode; in Viral-Browser never more than 3 research agents at once, plus one niche-audit agent, one scoring agent and one red-team agent, and, after the picks, up to 3 reference-pack agents (never alongside the research agents), and no production agent. Never give agents overlapping work.
- Never read model guides other than the locked one.
- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Viral-Browser: never generate anything, never start Create without the user's yes, and never let the references' product niche decide the answer.
- Never claim results you did not verify.
