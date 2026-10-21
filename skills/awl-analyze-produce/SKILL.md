---
name: awl-analyze-produce
description: /analyze-with-loupe Analyze Mode phase: prepare every video, spawn the production agents, handle their reports (A8–A10). Internal to that command.
user-invocable: false
---

# awl-analyze-produce — Analyze Mode: prepare, produce in parallel, wrap-up hand-off (A8–A10)

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- production-agents §1: `AWL/reference/production-agents/010_1_prepared-by-this-session-before.md` (1.3 KB)
- production-agents §2: `AWL/reference/production-agents/020_2_spawning.md` (15.4 KB)
- production-agents §3: `AWL/reference/production-agents/030_3_the-agent-s-contract.md` (8.4 KB)
- production-agents §5: `AWL/reference/production-agents/050_5_this-session-as-agents-report.md` (2.3 KB)
- higgsfield-mcp §1: `AWL/higgsfield/higgsfield-mcp/010_1_connection-and-conventions.md` (1.5 KB)
- `models_explore {action:"get", model_id}` once (A8.2)

### A8. Load the locked model's documentation
The model was picked at the start (§2.4) and does not change.
1. **Read no guide or reference wholesale.** Invoke Skill `awl-model-guide` once: it resolves the locked model's guide folder and says which
   sections each step reads. Each per-video skill (`awl-plan-video`, `awl-write-request`, `awl-inputs`, `awl-precheck`, `awl-submit`, `awl-qc`)
   names the exact reference and guide sections it needs; they are read at that step and not before. For a model with no guide, `awl-model-guide`
   points to `AWL/models/_generic-fallback.md`.
2. `models_explore {action:"get", model_id}` once. If the live parameters differ from the guide, the
   live ones win; note the drift.
3. Where a planned concept needs something this model cannot do, adapt the approach within the model
   and state it in the video's brief. Examples:
   - build a 9:16 start frame from the supplied assets when the model has no reference roles;
   - split into clips when the duration exceeds the model's range.
   Overlay text never depends on the model: it goes in CapCut. Never switch models.

### A9. Prepare every video (this session)
At the start of A9: `T state --run RUN set stage=producing next_skill=awl-analyze-produce` (a resume re-enters here; the ledger and `state.json → videos[]` show which videos are done).

**How A9 invokes the per-video skills.** Step 1 (X1–X4 for every video, in allocation order): invoke Skill `awl-plan-video` (X1), `awl-write-request` (X2) and `awl-precheck` for **X4 only**; their text stays loaded for the next video. Step 2 (shared inputs, X3 for the shared uploads and X5's folder): invoke Skill `awl-inputs`, then return here. Step 3 (X5–X6 per video): invoke `awl-precheck` again for X5 and X6 of every video and print the total once. Steps 4 and 5 follow here.
Plan everything before production, in allocation order, **without asking for confirmation**
(contract item 15):
1. **X1–X4 for every video:** plan, pattern card, request(s), pre-generation QC. Recreate plans
   take the approach and source preparation from E4–E5.
2. **Shared inputs, once:**
   - the Higgsfield project folder (X5: `list_workspaces` → `create_project`), stored with
     `T state --run RUN set higgsfield.folder_id=<id>`;
   - every asset the asset plan uses, uploaded (X3), with media ids in `state.json → assets.uploads` (every upload is recorded
     with `T uploads set --run RUN --video NN --label "<as the request names it>" --media-id <id> --file <path>` and merged with
     `T uploads merge --run RUN`: one schema, never a hand-written uploads file and never a hand edit of state.json; `T lint-run`
     lists a file outside the schema);
   - Elements when the model uses them.
3. **X5–X6 per video:** preflight its first request and print its brief. Then print the estimated
   total once, as information, against the balance.
4. **The only question in this phase** is a long video's permission (A7b), when a plan newly pushes
   a video over 30 s.
5. **The agent contract:** generate `<RUN>/50-requests/agent-contract.md` with `T contract --run RUN [--notes "<run-specific notes>"]` from the prompt in
   `reference/production-agents.md` §2 (the canonical text: the recording rule, the checks, the size
   method, the deliverables), filling its paths; run-specific notes go in its last block. It is generated
   for every run and never copied from an earlier run's file. Before the first agent is spawned run `T loupe ensure` and update
   `state.json → loupe` (five agents must not race to start it); fill the contract's "Loupe" line from it (`up` when the run has none)
   and its "Audio ingest" line from `state.json → audio_ingest` (item 24). Fill its "QC fixes" line from `state.json → qc_fixes` (`auto` when the run has none; item 27).

### A9b. Produce in parallel (production agents)

- **Free runs:** each agent's spawn message names its video's kind (`Video NN, kind recreate|create`, from `state.json → videos_kind`), and the contract's "Video kind" line says that the kind selects the Recreate or the Create branch of every per-video step.
- **Spawn one production agent per video** (`reference/production-agents.md` §2 prompt, as written to
  the run's contract file at A9; `subagent_type: general-purpose`, `run_in_background: true`).
  - At most `production.max_parallel_agents` (5) run at once; start the next queued video when one
    finishes.
  - Each agent runs X3 (its own inputs) → X7 → X8 → X9 → X10 for its video, ending with its CapCut
    project, and returns one JSON line. It runs X5 again for any request it changes.
- **As each agent reports:**
  - read its `60-outputs/video-NN/result.json`;
  - record it (`T state --run RUN append videos='<json>'`);
  - check the brief: a `qc` that says RESIDUAL FAILURE or regenerated has an attempt block in the
    video's brief with the verdict and what changed, or it is added now from `result.json`;
  - reconcile the flags (item 23): `T caught-flag reconcile --run RUN`. Every row in
    `flagged_unrecorded` gets `T caught-flag add` now (from the agent's `result.json` notes, the
    ledger history and the request file); each `failed_to_judge` row is read and either marked
    (`ledger set --flagged`, then added) or left as the validation or credit error it was; a
    video whose flag is `open` or `persistent` is named in the wrap-up; `unclaimed_captures` (raw answers the
    Higgsfield hook saved) that belong to this run get `T caught-flag add … --capture <id>`, the rest are left
    for the admin;
  - verify, and fix at once what is missing (`production-agents.md` §5 item 3): `videos[]` in
    `state.json`; the README table (the agent's `readme-row.md` appended to `deliverables/README.md`);
    `video-NN-clean.mp4` and `video-NN-preview.mp4` in `deliverables/`; `result.json` complete, each
    check of the agent contract with an evidence path or "not checked: <why>"; the plan and brief files
    with their attempts. A size reading is never repeated or summarised before its frame was viewed
    and its method (two estimates, a derived distance) is in the verdict; a size from one assumed
    number is provisional, the agent's own label (CE-028);
  - print one line: video, status, CapCut project, credits.
- **Blockers come back from agents and are handled here:**
  - a permission is needed (A7b) → ask, then launch that video again;
  - `qc_fix_permission` (only with QC fixes `ask`) → ask the user the fix question of item 27, then continue that agent with the answer;
  - CapCut was running → its project is pending until the wrap-up;
  - credits ran short → launch nothing more, report the shortfall; the run stays resumable;
  - a request failed twice → report it in the wrap-up.
- **QC verdicts are the agent's** (X9); with QC fixes `ask` the fix generation waits for the user's yes (item 27); a video that still fails, or whose fix the user declined, is reported in the wrap-up.
- **Without the Agent tool**, run X3–X10 per video in this session, one video at a time (with QC fixes `ask`, ask the fix question of item 27 yourself instead of writing a proposal).

### A10. Wrap-up
See §6.

## Rules this phase owns (contract items 2, 3, 15, 23)

2. **Agents.**
   - **Analysis agents:** 0 by default; **1** when there are many videos, **2** only when the folder
     is large (`reference/analysis-protocol.md` §7). They never call Higgsfield or CapCut.
   - **Production agents** (Analyze Mode, Recreate and Create):
     - **one agent per video**, at most **5 at once** (`config.json → production`);
     - after this session has planned and prepared every video, each agent produces its own video
       end to end: Higgsfield generation → QC → CapCut project;
     - the contract and prompt are in `reference/production-agents.md`;
     - a queued video starts when an agent finishes.
   - Agents never overlap, never ask questions (they report blockers and stop), and never spawn
     agents. Edit Mode uses no production agents.
3. **Generation lanes.** Every video is a lane with **one job in flight at a time**:
   plan → preflight → brief → submit → wait → download → post-process → QC.
   - The ledger records every submission and reports what is already in flight; the agents keep to at
     most `production.max_parallel_jobs` (5) jobs in flight per run, across the production agents
     (`T ledger begin` reports the open submissions against that cap; whether to submit is the
     agent's decision, X7).
   - Never use `generate_video_batch`, never submit twice in one lane, and never start an
     uncontrolled batch.
   - A multi-clip video runs **clip by clip** inside its lane: a clip is submitted only after the
     previous clip passed QC (`generation-system.md` §3b).
   - Edit Mode runs one video at a time.
15. **Analyze Mode asks for permission in exactly one case:** a video **over 30 s that needs 2 or
    more generations** (A7b).
    - Everything else runs without confirmation: no "Go" question, no cost pauses, no QC questions of its own
      (the one fix question of item 27, asked only when the user chose `ask`, is the exception).
    - Blockers are reported, not asked: the balance can't cover the next video, or Higgsfield
      itself demands a choice (`unlim_choice`, `recovery_tool`, X7 in `awl-submit`).
    - The planning questions (mode, model, inputs, number of videos, directions) are not
      permissions and stay.
    - Edit Mode keeps its gates (E6, X9-R).
23. **Caught flags: every prompt and video that Higgsfield flagged is recorded**
    (in Loupe, the pipeline's web app at `http://127.0.0.1:8787`: a database with a viewer that searches,
    filters and groups, written only with `T caught-flag`; `T loupe open --path /#/flags` shows it to the user).
    A flag is any time Higgsfield refuses, blocks, withholds or reroutes something during the run: a
    moderation or policy block, a job that fails within seconds with no reason (refunded), an upload,
    video or Element marked `nsfw`, `ip_checking` or `failed`, an output withheld, or a notice returned
    instead of a job (`preset_recommendation`). Validation errors (a prompt over 5000
    characters, out of credits) are not flags. **Whoever made the call records it at once,
    before changing the request** (agents and this session alike, in both modes): mark the
    submission with `T ledger set … --flagged`, then `T caught-flag add --run RUN --video NN --attempt aK`.
    **The script gathers** what the run already knows: the request's prompt and parameters, every input
    with its file, type, V or A id and a thumbnail, the reference video and the source segment it covered,
    the plan and the brief, and the job and fingerprint of the ledger row marked flagged. **The agent
    supplies the judgement:** Higgsfield's response verbatim (or "none given"), the kind, the tool and
    stage, the credits, its **suspected trigger** labelled [E] or [I], and what Loupe searches and
    groups by: `--tags` (1 to 4 labels for the trigger, for example `real-person-face`, `celebrity-name`,
    `brand-name`, `protected-ip`, `nsfw-image`, `video-reference`, `element`, `prompt-wording`,
    `preset-notice`, `output-withheld`, `unknown-trigger`), `--asset` (which input: `"Image 2"`,
    `"Video 1"`, a media id, a file name or an A or V id; a file path for an upload flag),
    `--prompt-span` (the exact words of the prompt) and `--part-of` / `--part-from` / `--part-to` (which
    video, which seconds). Name what can be told and leave the rest out: the script lists what was not
    given and never guesses. After the changed request is accepted:
    `T caught-flag set --id CF-nnn --status cleared --cleared-prompt <the accepted request.json>
    --cleared-job J` (never `cleared` before a request went through; a flag that stays is
    `persistent` and the video is planned another way or reported). **The record is written, never
    read during a run:** no step of a run (A1, E1, a plan, X4) and no agent contract lists, searches or opens it,
    and no digest or copy of it is made, because a growing record read at every run start rots the agents'
    context. (Only the sample library is read: by QC through `T qc-consult`, by the first request of a video through `T plan-hints`, and the saved prompts of one sample
    an agent judged relevant through `T sample-prompts`; never the flags.) What a flag
    teaches is held as a general rule in the references (`generation-system.md` §5c.2, the model guides'
    failure tables, `higgsfield/higgsfield-mcp.md` §9), and X4 tests the plan against those rules. The
    main session runs `T caught-flag reconcile --run RUN` as each agent reports and in the wrap-up; it
    only lists the calls marked flagged that have no entry yet, so no flagged call leaves the run
    unrecorded. A flag whose rule is general or recurs is written into those references as a rule when the user asks for it; the entry stays as the record.
    The user opens Loupe to see the flags grouped by trigger, asset, video, kind, run or model and searched
    by field, with the evidence Loupe gathered next to each.
26. **Pilot first.** With more than four videos to produce, spawn the first video's agent as soon as its plan, request, inputs and brief exist and let it run X7–X10 to its QC
    before the remaining plans are finished and their agents are spawned (the planners go on meanwhile). What its QC finds (a recipe fault, a marker, a size, a seam) is written
    into the other plans before they cost a generation; the user is told in one line when the pilot has passed. The user may say "no pilot" at the start.
27. **QC fixes (Recreate and Create): the question.** With `state.json → qc_fixes = ask`, a production agent that found issues or anomalies only a new generation can fix writes
    `result.json` with `blocker: qc_fix_permission` and a `fix_proposal` and stops (it never asks). When it reports, record it as for any report, then ask with AskUserQuestion
    (header "QC fix"; one question per waiting video, up to four in one call): "Video NN: QC found <the findings in one line>. Fix generation: <what the corrected request changes>,
    about <preflight credits> credits (<balance> left). Proceed?" with **"Fix it"** (`approved`), **"Keep this take"** (`declined`) and **"Fix it, and stop asking"** (`auto`: also
    `T state --run RUN set qc_fixes=auto`, so no later video asks). Continue the stopped agent with the answer (SendMessage to that agent, its context intact; if it cannot be continued,
    launch a fresh production agent for that video with the contract plus "resume at awl-submit X7 with <request file>, decision <…>"). The other videos keep running meanwhile; the next
    queued video starts when an agent stops. With `auto`, nothing is asked: the agent submits its one diagnosed regeneration itself.
28. **A stalled production agent.** An agent whose `result.json` does not exist and whose `60-outputs/video-NN/` has not changed for 20 minutes while a job of its lane is `submitted`
    or `completed` in the ledger is stalled (a machine pause freezes every background agent at once). Do not relaunch it blindly: read the ledger (`T ledger show --run RUN --video NN`)
    and `T status --run RUN`, then continue the same agent by its id with one line ("continue from the last ledger entry"); only if it cannot be continued launch a fresh agent with the
    contract plus "resume at the ledger's last entry; never resubmit a job that is submitted or completed". The ledger's fingerprint is what makes a resume safe: a request already
    submitted is found by `begin` as a conflict and is never paid twice.
29. **A request is frozen once its agent is spawned.** After the spawn, `50-requests/video-NN*-request.json` and the uploads file are the agent's: the main session and the planners
    never rewrite them (an identity, a prompt line or an input that must change goes to the agent as a message, and the agent makes the change through its own regeneration path,
    `awl-write-request` → `awl-submit`). `T lint-run` lists a request file whose content no longer matches the fingerprint of its open ledger entry.
30. **Planner forks (optional; X1–X2 of several videos in parallel).** A fork plans one video and writes only that video's files: `40-briefs/video-NN-plan.md`,
    `video-NN-pattern.md`, `video-NN-brief.md`, `50-requests/video-NN-request.json`, its uploads through `T uploads set`, and a status note `40-briefs/video-NN-planner.md`
    with three fixed headings (Done, Open, Risks: what it measured, what it could not settle, what the agent must check). It calls no generation tool, never touches
    another video's files, writes state.json only through `T state … append`, and stops after `T lint-run --run RUN` shows its files clean. The main session reads the
    status note and the files, not the fork's final message, and spawns the production agent only after that.

## Never (this phase)

- Never spawn more than 2 analysis agents, more than 5 production agents at once, or a production
  agent in Edit Mode. Never give agents overlapping work.
- Never list, search or read the flag record or hand it to an agent during a run (item 23: it is written, not read), never
  change or resend a request that Higgsfield flagged before its `T caught-flag add` entry exists (the verbatim
  response, the prompt, the media, the flagged video, the suspected trigger), never write an
  entry by hand, never mark one `cleared` before a changed request was accepted, never send a
  third identical request after two refunded flagged failures, and never re-upload a flagged
  asset or video unchanged (item 23).
- Never close a run with a RESIDUAL FAILURE or a regenerated video that has no attempt block in its
  brief (A9b, §6). Never copy an agent contract from an earlier run: it is generated at A9 from
  `reference/production-agents.md` §2.
- Analyze Mode: never ask for permission except for a video over 30 s that needs 2+ generations.
  Never generate any clip of such a video before that permission.

## Hand-off

When every agent has reported and its checks (A9b) are done: `T state --run RUN set stage=produced next_skill=awl-wrapup`, then invoke Skill `awl-wrapup`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
