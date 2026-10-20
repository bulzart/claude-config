---
name: awl-start
description: /analyze-with-loupe phase 1: mode, Analyze sub-mode, the locked video model, inputs, the audio choice, create the run. Internal to that command.
user-invocable: false
---

# awl-start — Start: mode, sub-mode, model, inputs, run

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase 1 of `/analyze-with-loupe`. The router (the command) sent you here and passes the command's arguments (`$ARGUMENTS` below) as this skill's args. Nothing else needs to be loaded for this phase.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- *(nothing from the library: `T model-menu` and `T model-entry --id` print what is needed)*

## 1. Paths and tools

| name | value |
|---|---|
| `AWL` | `C:/Users/Glaresquare1/.claude/analyze-with-loupe` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `AWL/config.json`) |
| `T` | `"$PY" "$AWL/scripts/awl.py"`. Every call prints one JSON object on its last line; run through Bash |
| Model index | `AWL/models/index.json` (model id → guide, capabilities, 9:16/720p params). **Never Read it whole** (40 KB): `T model-menu` builds the menu, `T model-entry --id <id>` prints one model's entry and its guide path |
| Model guides | `AWL/models/<guide>.md` is an index; the sections are in `AWL/models/<guide>/`. Which sections each step reads: `awl-model-guide` |
| Higgsfield guide | `AWL/higgsfield/higgsfield-mcp.md` (index) and `AWL/higgsfield/higgsfield-mcp/` (sections) |
| Flag record | Loupe, `http://127.0.0.1:8787` (item 23), started by `T loupe ensure` at run creation and recorded in `state.json → loupe` (`up` or `down`; missing = up): `T caught-flag add, set, reconcile, open` and `T ledger set --flagged`; written in X7 (`awl-submit`), reconciled in A9b and §6, never read during a run. The sample library is read only by `T qc-consult` (`awl-qc`) and, once per video at its first request, `T plan-hints` (`awl-write-request`) |
| References | `AWL/reference/<name>/` section files (index: `AWL/reference/<name>.md`): `analysis-protocol`, `generation-system`, `anomaly-catalog`, `creative-direction`, `brand-guardrails`, `text-and-format`, `assets-and-substitution`, `capcut-assembly`, `production-agents`. Each phase skill lists the sections it needs under "Read now" |
| CapCut | `capcut` MCP (drafts store and template in `AWL/config.json → capcut`) + capcut-cli `capcut` on PATH. Tool list and steps: `reference/capcut-assembly/` (`awl-postprocess`) |
| Run folder | created by `T new-run` under `AWL/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json) |

### Higgsfield tools

**Higgsfield tools** are deferred.
- Load them before first use:
  `ToolSearch "select:mcp__higgsfield__models_explore,mcp__higgsfield__balance,mcp__higgsfield__list_workspaces,mcp__higgsfield__create_project,mcp__higgsfield__media_upload,mcp__higgsfield__media_confirm,mcp__higgsfield__media_import_url,mcp__higgsfield__show_reference_elements,mcp__higgsfield__generate_image,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__show_generations,mcp__higgsfield__transactions,mcp__higgsfield__reframe"`.
- If they are missing or only `authenticate` tools exist, ask the user to run `/mcp` → higgsfield →
  Authenticate, then continue.
- Never call widget-only tools (`media_upload_widget`, `show_marketing_studio_v2`).

## 2. Start (steps 2–6; the router already handled `resume` and reported-video feedback)

2. **Mode.** If `$ARGUMENTS` begins with `analyze` or `edit`, use it. Otherwise ask with
   AskUserQuestion (header "Mode"):
   - **Analyze Mode**: "Analyze a folder of references and instructions, learn what makes them work,
     then create new videos for this client."
   - **Edit Mode**: "Edit supplied videos one by one: replace, remove, insert, alter, restyle or
     recreate elements."

   **Analyze Mode → sub-mode.** If `$ARGUMENTS` names `recreate` or `create`, use it. Otherwise ask
   with AskUserQuestion (header "Analyze as"):
   - **Recreate**: "Analyze the references, then recreate N of them with your product and
     characters: same scenario, faces and products swapped or blended. Fully autonomous."
   - **Create**: "Analyze the references, then create new videos in suggested style groups (one
     style or a mix), using your product. No reference video is used as input."
   Store it with `T state --run RUN set analyze_submode=recreate|create` once the run exists.
3. **Higgsfield tools.** Load them (§1) and check that they are authenticated.
4. **Model — picked now, locked for the run.**
   1. `models_explore {action:"list", type:"video", limit:100}`, then collect the returned ids.
   2. `T model-menu --mode <analyze|edit> --live-ids "<id,id,…>"`. Edit Mode and **Recreate** use
      `--mode edit`, since their fit is the model's edit capability; **Create** uses
      `--mode analyze`.
      - It prints one numbered table of **every available video model**, with ★ Seedance 2.5 and
        ★ Wan 3.0 Prime pinned at the top and the rest in `index.json → menu.order`.
      - Live models without a guide are appended.
      - The columns show what each can do and its fit for the mode. The Edit column reads: ✓ edits
        video, ↔ motion transfer, ≈ recreates, ✗ frames only.
   3. **Show the whole table in chat, verbatim, every row, however long.** Never shorten it to a
      top-N. The user wants to see all models.
   4. Ask with AskUserQuestion (header "Model"). The options are the 4 `quick_picks` from the JSON
      line (label = model name; description = its "what it can do" and mode fit). "Other" = any
      number or name from the table; resolve numbers with the JSON `numbers` map.
   5. Store it: after the run exists (step 6), `T state --run RUN set model=<id> model_locked=true`.
      Print its `index.json` entry now with `T model-entry --id <id>` (never Read `index.json` whole: it is 40 KB; capabilities, durations, 9:16/720p params, and
      `continuation`: the maximum per generation and how clips join), but not yet its guide.
   6. If the model's fit for the mode is limited (e.g. Edit Mode with "✗ frames only"), say once how
      the run will work with it, e.g. "edits will be recreated from clean frames of each source
      video with your assets". Then continue. Do not suggest another model.
5. **Inputs.** Take what `$ARGUMENTS` already gives (`analyze <references-folder> assets <paths…>
   [examples <folder>]` / `edit <video paths…> [examples <folder>]`) and ask in plain chat, in
   **one** message, only for what is missing. Then stop and wait.
   - **Analyze Mode** needs two things, and offers a third:
     1. The references folder to analyze.
     2. **Your assets, dropped once:** product samples, characters, logos, interface
        screenshots, anything the new videos should use. Files and/or folders; one folder per
        product or character is ideal but not required. For products that are poured, eaten or
        applied (a drink, a gum, a food, a cream), add a **contents sample** per flavour or variant
        (the liquid in a clear glass, a gum piece, the cream on a finger). It lets a reference's
        cup, bowl or hand carry your product.
     3. **Your examples folder (optional):** your own finished, AI-edited videos that show how you
        use your products: placement, use, continuation across clips, blend, and anything else you
        always do. It may be empty; "none" skips it (contract item 18).
     Say in the message: *"Drop or paste the paths. I will use only these as your assets and pick
     from them for each video on my own. Examples are optional: I study them for how you use your
     products and never use them as assets."* The user may answer "no assets" for a project that
     needs none.
     **Recreate** also needs the **characters** who replace the people in the references (face
     close-up + full body each). If none are supplied and the references show people, ask once at
     this step: add characters, or keep the people as they are.
   - **Edit Mode** needs the video file(s) or folder to edit, and offers the optional **examples
     folder** (as above). Per-edit assets are asked later, per operation (E3).
   - Paths may arrive quoted, space-separated, dragged into the terminal, or one per line. If an
     image arrives only as a chat attachment without a file path, ask for its path or folder:
     Higgsfield needs the original file.
   - Validate every path (Glob/ls) and report any that don't exist.
5b. **Audio.** Ask once, with AskUserQuestion (header "Audio ingest"), in the same message batch as the other start questions,
   whether the videos' audio is processed as text for this run (contract item 24). Both modes ask it. Never pick for the user and
   never mark one option as recommended; the two options, with these descriptions:
   - **Whisper speech-to-text**: "Every video's audio is transcribed locally (faster-whisper `small`, int8 on the CPU): about real
     time per video plus about 8 s to load the model once per batch (measured 2026-10-20 on this machine: a 15 s clip in 10 s, a 9 s
     clip in 18 s including the load). The transcript feeds the cards (what is said, the spoken hook, the address), the sync anchors
     of spoken lines, the caption timing of the text plan and the speech share of the sound profile."
   - **Frames only**: "No speech-to-text runs and no transcript is written. Every speech field of the cards, plans and briefs reads
     `audio not ingested` (what was said is unknown, not absent); the hook, the address and the sync anchors come from the frames,
     the cuts, the sound numbers and the on-screen text. The audio file itself is still used: the original audio returns under the
     picture, loudness and silences are measured, the sound profile runs without a speech share."
   The answer is stored in step 6 (`state.json → audio_ingest`: `whisper` or `frames-only`) and is the only source of the choice:
   `T prep-all` stops when it is missing. A resume that finds it stored never re-asks; one that finds it missing asks here.
6. Create the run:
   - `T new-run --mode <analyze|edit> --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"]`;
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5);
   - store the audio choice (step 5b): `T state --run RUN set audio_ingest=whisper` or `audio_ingest=frames-only`;
   - start Loupe: `T loupe ensure` (it starts the web app detached when it is down; the JSON line has `library_size`, the number of QC samples the keeper
     is fed from, and `keeper.state`: the keeper is booted or brought up to date there, so the first consult finds it current), then `T state --run RUN set loupe=up`, or `loupe=down` when it exits 1 (tell the user in one line that
     `python ~/.claude/loupe/loupe.py serve` starts it by hand; the run goes on, QC without samples, flags wait in Loupe's outbox);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`).

## Rules this phase owns (contract items 4, 11, 17, 24)

4. **One model per run, picked at the start, then locked.**
   - The user picks the video model right after choosing the mode (§2.4), from a menu that lists
     **every** available model.
   - That model is used for the whole run. Never re-ask for it, never switch it, and never suggest
     switching it. If a later step needs something the model cannot do, adapt the approach within
     the model and say how in one line. Only an explicit user request changes the model.
   - `models/index.json` builds the menu; **never read every model guide**. Read **only the locked
     model's guide** (from the index) plus `higgsfield/higgsfield-mcp.md`, at the step that names
     them.
   - Read reference files at the step that names them.
11. **Client assets come only from paths the user gives.**
    - **Analyze Mode:** the user supplies all asset files and/or folders **once, at the start**. The
      command then understands them and uses them autonomously for every video.
    - **Edit Mode:** the user supplies the assets **for each edit**.
    - Never search for, detect, infer or pick client assets inside the references folder or the
      edit-source folder. Those can hold other products, samples or entirely different executions, so
      everything there is **reference material only**.
    - Never reuse one edit's assets for another edit unless the user says so.
    - The **examples folder** (item 18) is never a source of client assets either.
17. **Analyze Mode has two sub-modes, chosen at the start (§2.2) and never mixed:**
    - **Recreate.** The agents autonomously **edit the original reference videos** with the client's
      assets: the same scenario, with faces swapped to the supplied characters and the product
      swapped, filled into a vessel or placed (item 14).
      - It is Edit Mode's machinery (E4–E5) after a full analysis, run without per-video questions
        or reviews.
      - The user gives how many videos to recreate; the agent picks the best-fitting references
        (§3 R-steps).
    - **Create.** New videos built from the analysed patterns, in one style or a mix of styles
      (style groups such as "Organic × skit × gym", "Anime × reaction × office").
      - The product is used in the new scenes.
      - **No reference video, frame or clip is ever an input** to a generation; nothing is edited.
    - In both sub-modes, every video ends as a CapCut project (item 16), produced by its own agent
      (item 2).

Item 17's "§3 R-steps" are step A6r (`awl-recreate-plan`).

24. **Audio ingest is the user's choice, once per run (step 5b).** `state.json → audio_ingest` is `whisper` (speech-to-text of every
    video's audio, written once per video as `10-media/<V>/transcript.json` and `transcript.txt` by `T prep-all`) or `frames-only` (no
    speech-to-text, no transcript file; every speech field of every card, plan and brief says `audio not ingested`, never `no speech`
    or `silent`). No step, script or agent picks a default: `T prep-all` and `T prep-video` refuse without it and `T captions
    --from-speech` refuses in a frames-only run. The choice is about speech-to-text and what is derived from it; whatever needs the
    audio file itself (the original audio restored under the picture, loudness and silences, `T audio-profile`, `T sync-check`)
    runs in both modes.

## Never (this phase)

- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never shorten the model menu. Every available model is always shown, with the pinned ones on top.
- Never decide the audio choice for the user, never mark one of its options as recommended, and never write `no speech` for a run that did not ingest audio.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.

## Hand-off

- Analyze Mode: `T state --run RUN set stage=started next_skill=awl-analyze-prepare`, then invoke Skill `awl-analyze-prepare`.
- Edit Mode: `T state --run RUN set stage=started next_skill=awl-edit`, then invoke Skill `awl-edit`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
