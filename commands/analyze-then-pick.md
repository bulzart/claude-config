---
description: Analyze a folder of reference material (or take videos to edit), learn what makes it work, then generate new vertical 9:16 720p videos through Higgsfield MCP with model-specific prompting — one video at a time.
argument-hint: "analyze <references-folder> assets <asset files/folders…> [examples <folder>] | edit <video files/folders…> [examples <folder>] | resume [run-dir]"
disable-model-invocation: true
disallowed-tools:
  - Workflow
allowed-tools:
  - Read
  - Glob
  - Grep
  - ToolSearch
  - AskUserQuestion
  - "Bash(C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe *)"
  - "Bash(python *)"
  - "Bash(ffprobe *)"
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

## 0. Operating contract (read first, obey throughout)

1. **Normal command, never a workflow.** Run everything in this conversation with ordinary tools.
   Never create, call, convert to, or delegate to a Claude Code Workflow (the `Workflow` tool is
   disabled for this command). Higgsfield's server-side "workflow" recipes are only documentation, and
   their content is already copied locally.
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
   - The ledger enforces at most `production.max_parallel_jobs` (5) jobs in flight per run, across
     the production agents.
   - Never use `generate_video_batch`, never submit twice in one lane, and never start an
     uncontrolled batch.
   - A multi-clip video runs **clip by clip** inside its lane: a clip is submitted only after the
     previous clip passed QC (`generation-system.md` §3b).
   - Edit Mode runs one video at a time.
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
5. **Fixed output: vertical 9:16 at 720p (720×1280)** for every generation in both modes. Never ask.
   Map it to each model's own parameters (`index.json → output_9x16_720p`) and conform
   deterministically. Never stretch.
6. **Text policy depends on the mode** (`reference/text-and-format.md`):
   - Edit Mode removes all source text unless the user keeps specific text.
   - **Analyze Mode generates every video clean.** It places all overlay text ("POV: …", "when …",
     hooks, captions) afterwards as **CapCut text layers** at the reference text's position and
     timing (`reference/capcut-assembly.md`).
     - The wording keeps the reference's role and format.
     - A generic meme line may stay as written; source-specific wording is rewritten.
     - Usernames, handles, watermarks and source brands are never copied.
   - **Every CapCut text layer uses the house text style:** font System, size 10, and **the user's
     chosen preset**, learned from their project `03_Oct_2026_v09` on 2026-10-03 and locked in
     `config.json → capcut.text_style.learned` (white text, black outline). `T capcut-repair` applies
     it to every text layer after each save (`reference/capcut-assembly.md` §3). Never re-learn or
     replace it unless the user explicitly asks for a different preset.
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
9. **One interconnected system.** Every generation is planned with `reference/generation-system.md`:
   - work backward from the finished video;
   - keep the entity state ledger;
   - run the integration analysis;
   - pass the anti-slop gate;
   - translate into the model's official pattern;
   - run the pre-generation QC.
10. **Honest reporting.** Never claim a generation, upload or check that did not happen. Report
    failures with the real error.
11. **Client assets come only from paths the user gives.**
    - **Analyze Mode:** the user supplies all asset files and/or folders **once, at the start**. The
      command then understands them and uses them autonomously for every video.
    - **Edit Mode:** the user supplies the assets **for each edit**.
    - Never search for, detect, infer or pick client assets inside the references folder or the
      edit-source folder. Those can hold other products, samples or entirely different executions, so
      everything there is **reference material only**.
    - Never reuse one edit's assets for another edit unless the user says so.
    - The **examples folder** (item 18) is never a source of client assets either.
12. **Generation discipline: no spam, no glitches.**
    - Every paid Higgsfield generation (`generate_video`, and `generate_image` for start frames)
      goes through the ledger (`T ledger begin` before, `T ledger set` after; §5 X7). There is at
      most **one job in flight per video lane**, at most 5 per run, one generation call per turn
      per agent, and never parallel calls inside a lane.
    - Never resubmit after a timeout or an unclear answer until the outcome has been checked, and
      never resubmit because a job is slow.
    - Never repeat an identical finished request.
    - Preflight (`get_cost`) once per distinct request.
    - Never call generation tools to "test" or "retry just in case".
13. **Edit Mode review.** After every edit attempt, the user sees the finished video and approves
    it or asks for changes. Changes are re-applied to the **original** source video. The next video
    starts only after approval (§5 X9-R).
14. **Analyze Mode: the client's product is always in the video.** This applies when the supplied
    assets include a product or physical object of any size (a drink, a pack of gum, a car), or
    software that can appear on a screen. Unless the user or a document says otherwise, every new
    video shows it, in the most suitable form for what it is and how it is really used
    (`generation-system.md` §4b.0):
    - **Swap**, where the reference shows its analog in the same form (another can, another gum
      pack, another car).
    - **Contents**, wherever the video shows the product's category in another form or vessel,
      whatever its role in the story: from the reference, from the plan, or from a prop in a
      supplied photo. The vessel and the action stay; what is inside becomes the client's product,
      matched to the variant's contents sample, and its opened package stands nearby.
      - Example: a man at a café table holds a glass. It holds the client's orange sparkling drink
        (from the flavour's sample), with the open can beside it. A glass of water next to the can
        is wrong.
      - Example: a "first day as an assassin" poison gag. The cup's drink becomes the client's
        drink, the open can stands beside the cup, and the gag plays out unchanged.
      - Example: someone pops a piece of gum mid-story. It comes from the client's open pack on
        the table, which then holds one piece fewer.
    - **Natural placement** (§4b), where the reference has nothing analogous:
      - the reference's story stays untouched;
      - the anchor fits the product's size and use (§4b.1):
        - a handheld item sits in a free hand when that is logical (a man crossing a street holds
          it through his one-second "respectful jog"), otherwise on a fitting surface;
        - a large one stands where such things really are (a car parked at the curb behind the
          action);
        - software shows on a device in use;
      - it is noticed, not featured;
      - it stays on one persistent spot, moved only by a visible, logical action (picked up to
        use, then set down; a parked car driven away);
      - it is lit and rendered like the rest of the scene, so it never reads as an edit.
    - **Use only when the action invites it.** The product is used the way it really is (sipped,
      chewed, applied, driven) only when the action has room for it; the story never changes to
      fit the product.
    - **Physically and logically correct for that object.** Its size, weight, states and motion
      follow its own physics (`generation-system.md` §3, §4, §5b). These rules are general; the
      examples only illustrate them.
15. **Analyze Mode asks for permission in exactly one case:** a video **over 30 s that needs 2 or
    more generations** (A7b).
    - Everything else runs without confirmation: no "Go" question, no cost pauses, no QC questions.
    - Blockers are reported, not asked: the balance can't cover the next video, or Higgsfield
      itself demands a choice (`unlim_choice`, `recovery_tool`, §5 X7).
    - The planning questions (mode, model, inputs, number of videos, directions) are not
      permissions and stay.
    - Edit Mode keeps its gates (E6, X9-R).
16. **Analyze Mode: reference inserts are cut, never generated, and every video ends in CapCut.**
    - A meme or other insert that interrupts the reference (e.g. 13 s of footage + a 2 s meme with
      its sound + 12 s of footage) is cut from the reference with its sound. A video meme is never
      screenshotted.
    - Only the reference's own content is generated (Create) or edited (Recreate): 25 s in the
      example, with a beat boundary at the split.
    - Every video becomes its own CapCut project `DD_Mon_YYYY_vNN` (e.g. `01_Oct_2026_v03`). The
      project holds the clean video, split at each insert point with the insert placed in the gap,
      plus the overlay text as text layers (`reference/capcut-assembly.md`;
      `generation-system.md` §3c).
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
18. **Examples: the user's own finished videos (optional, both modes).** They are asked for with the
    other inputs (§2.5). The folder may be empty or absent; then nothing changes.
    - They show the user's **house approach**: how their products are placed, used, continued across
      clips and blended, plus anything else they consistently do (text placement, pacing, sound,
      characters, endings).
    - When present, they are prepared and analysed (A1, A3; Edit Mode E1) into
      `20-analysis/house-approach.md`, and every plan follows it (A4–A7, X1, X9).
    - **Precedence:** the user's instructions for the run > the house approach > the pipeline's
      defaults. The house approach never overrides the hard rules: physical and logical correctness
      (`generation-system.md` §3, §4b, §5b), the §9b must-not-survive list, the permission rule
      (item 15) and the house text style (item 6).
    - Examples are **study material only**: never uploaded, recreated, cut into a new video, or used
      as client assets. Their own flaws (a physics cheat, a leftover watermark) are never copied.
19. **Action timing is locked to the original audio (Edit Mode and Analyze Mode Recreate).** Whenever
    the original audio goes back under a generated picture (X8), every action in the output happens
    at the same moment, at the same speed and in the same order as in the source, because the merged
    sound expects it: mouth movements on their words, contact on its impacts, steps on their
    footfalls, a pickup, sip or door on its sound. Plan, prompt, generate and check for it
    (`reference/generation-system.md` §5c):
    - the card lists the **sync anchors**: every sound in the original audio that belongs to a
      visible action, with its time;
    - the source drives the motion whenever the model can take it (true edit, motion transfer or
      video reference), and the request's duration equals the source segment's;
    - the prompt keeps every action's timing and pace, and adds, skips, repeats, reorders, speeds up
      or slows down nothing. The timing comes from the source video, never from timestamps in the
      prompt;
    - after the merge, `T sync-check` measures it (X8 step 5). A steady offset is fixed in post;
      drift or a moved action is a regenerate reason (Recreate) or the first QC note (Edit Mode).
    Create is not affected: its sound is built in CapCut on the new video's own beats.

## 1. Paths and tools

| name | value |
|---|---|
| `ATP` | `C:/Users/Glaresquare1/.claude/analyze-then-pick` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `ATP/config.json`) |
| `T` | `"$PY" "$ATP/scripts/atp.py"`. Every call prints one JSON object on its last line; run through Bash |
| Model index | `ATP/models/index.json` (model id → guide, capabilities, 9:16/720p params) |
| Higgsfield guide | `ATP/higgsfield/higgsfield-mcp.md` |
| References | `ATP/reference/analysis-protocol.md`, `generation-system.md`, `text-and-format.md`, `assets-and-substitution.md`, `capcut-assembly.md`, `production-agents.md`; `ATP/pipeline/preprocessing.md` |
| CapCut | `capcut` MCP (drafts store and template in `ATP/config.json → capcut`) + capcut-cli `capcut` on PATH. Tool list and steps: `reference/capcut-assembly.md` |
| Run folder | created by `T new-run` under `ATP/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json) |

**Higgsfield tools** are deferred.
- Load them before first use:
  `ToolSearch "select:mcp__higgsfield__models_explore,mcp__higgsfield__balance,mcp__higgsfield__list_workspaces,mcp__higgsfield__create_project,mcp__higgsfield__media_upload,mcp__higgsfield__media_confirm,mcp__higgsfield__media_import_url,mcp__higgsfield__show_reference_elements,mcp__higgsfield__generate_image,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__show_generations,mcp__higgsfield__transactions,mcp__higgsfield__reframe"`.
- If they are missing or only `authenticate` tools exist, ask the user to run `/mcp` → higgsfield →
  Authenticate, then continue.
- Never call widget-only tools (`media_upload_widget`, `show_marketing_studio_v2`).

## 2. Start

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json`.
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
      Read its `index.json` entry now (capabilities, durations, 9:16/720p params, and
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
6. Create the run:
   - `T new-run --mode <analyze|edit> --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"]`;
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`).

## 3. Analyze Mode

### A1. Inventory and preprocessing (deterministic, local)
- `T inventory "<references folder>" --run RUN --as references`: everything in it is **reference
  material only**.
- `T inventory "<asset path>" "<asset path>" … --run RUN --as assets` (scope `project`), then
  `T prep-assets --run RUN`: previews, document text, font names and a labelled contact sheet of
  **exactly the files the user supplied**.
- **Examples, when given** (contract item 18): `T inventory "<examples folder>" --run RUN --as
  examples`. An empty folder gives 0 examples: carry on. An assets path that contains a folder named
  `examples` (any case) hands that folder over as the examples folder: inventory the assets without
  it (pass its siblings) and say so.
- **Recreate only:** `T split-audio "<references folder>" --run RUN` writes `files_audio/` and
  `videos_without_audio/` inside the references folder.
  - The references are Recreate's edit sources, so only the **silent copy** is uploaded.
  - The reference's own-content audio is restored onto the edited picture (A6r).
- **Create: audio only, no silent copies.** `T split-audio "<references folder>" --run RUN
  --audio-only` writes `files_audio/` (no `videos_without_audio/`).
  - No reference is ever uploaded or used as a generation input.
  - The extracted audio feeds the **sound design**. Generated clips usually carry only voices,
    action sounds and ambience, while the references' feel often comes from a soundtrack and sound
    effects.
  - So every reference gets a sound profile (A3), and every Create video gets a soundtrack /
    sound-effect layer in its CapCut project (`capcut-assembly.md` §3b). That layer is the
    reference's own sound when it is reusable, or a matching track found and downloaded.
- **Both sub-modes fully process every video's picture and sound** for the analysis, inside the run
  folder (`prep-all` below):
  - frames, storyboards and on-screen text;
  - the transcript, loudness, silences, music and sound cues.
  Spoken hooks, sounds and music are part of what made them work.
- Show the counts (references, assets, examples) in one line.
- `T prep-all --run RUN --jobs 2`:
  - it runs the 5 fps adaptive frame pipeline, storyboards, per-second timeline, audio, speech and
    OCR sample for every video, plus image previews and document text;
  - with more than ~3 minutes of total video, run it with `run_in_background: true`, read the
    documents (A2) meanwhile, and wait for the completion notification before A3;
  - fix or report any per-item errors listed in its JSON.
- With examples: `T prep-all --run RUN --set examples --jobs 2` (into `10-media/E01…`, listed in
  `10-media/examples-index.md`).
- Pipeline details: `ATP/pipeline/preprocessing.md`.

### A2. Documents and instructions (authoritative)
- Read every document:
  - `10-media/docs/<D>.txt` for text and office files;
  - PDFs directly with Read (use `pages` for long ones);
  - spreadsheets as extracted text.
- The same goes for documents among the supplied assets (`30-assets/project/docs/`), e.g. dimensions,
  brand rules and usage notes.
- Quote the requirements they define. They override inferences.

### A2b. Understand the supplied assets (autonomous — no questions by default)
- Load `ATP/reference/assets-and-substitution.md`.
- View `30-assets/project/assets-sheet-*.jpg` and any preview that needs a closer look. Read
  `asset-inventory.md` (sub-folder groups and name hints), then build the **asset registry**
  (`30-assets/registry.md` and `state.json → assets`):
  - **Group into entities.** Each distinct product, object, character, interface, brand kit or
    environment is one entity, using sub-folders, names and what the images show. Several products,
    samples or characters are expected.
  - **Products and objects:** pick the canonical template (the cleanest, most complete geometry view,
    or the file the user named template/canonical). Mark other views and variants, and take real
    dimensions from any supplied spec. Find and link each **contents sample** to its variant: a
    liquid or texture photo, a pour, a glass of the drink, or a lifestyle shot that shows it. They
    are often among the supplied files without a label. A sample is never a separate product.
  - **Characters:** one entry per distinct person, mascot or character, with its best face and full
    views.
  - **Other assets:** logos, palettes, UI screenshots, environments, audio. Supplied fonts are
    listed only: CapCut text always uses the house text style (contract item 6).
- Ask **one** consolidated question only if a genuinely consequential ambiguity cannot be resolved by
  looking (e.g. two different-looking items presented as the same product). Otherwise proceed.

### A3. Video analysis (as continuous sequences)
- Follow `ATP/reference/analysis-protocol.md` exactly. For each video:
  - read `video.md` and `timeline.md`;
  - view **every** storyboard sheet in order, reading the timeline beside it;
  - densify with `T frames … --range a-b --fps 15 --sheet` around fast actions, cuts, interactions,
    gestures, product appearances and text appearances;
  - write `20-analysis/cards/<V>.md`, including (protocol §2.9–§2.11, §3):
    - its **client-entity fit**:
      - **swap**: its analog in the same form exists;
      - **contents**: the product's category sits in another vessel whose action matters;
      - **placement**: nothing analogous.
      For contents and placement, also record the placement opportunities: free or busy hands,
      nearby surfaces, and the light on them.
    - its **inserts**: memes or other clips that interrupt the reference, with their exact in and
      out on cut frames, video or still, and their sound;
    - its **overlay text**: wording, role, centre position, in and out times, and style;
    - its **sound design** (Create):
      `T audio-profile --audio "<files_audio file>" --out 10-media/<V>/audio-profile.json --transcript 10-media/<V>/transcript.json --cuts 10-media/<V>/cuts.json`.
      It measures the music bed, tempo, beat strength, energy arc, and hits (and whether they land
      on cuts), plus whether the sound is speech-free and so reusable whole. From those numbers and
      the visuals, infer its role: dramatic, comic, suspense, hype or sound-effect-driven.
    Videos that have nothing to do with the client's product are kept and analysed like any other.
    Their mechanism is still useful, and the product is integrated into them later.
- Delegate to 1–2 agents only per §7 of the protocol, with disjoint video lists. Give them the
  one-line client-entity summary from the registry.
- Images and other files in the references folder are also **reference material**: other products,
  samples, thumbnails and executions. Analyse them as references and never treat them as client
  assets.
- **Examples** (contract item 18): one card per example, `20-analysis/examples/<E>.md` (protocol §9):
  product integration, continuation, blend, characters, text, structure, sound, what they avoid,
  and flaws not to copy. The same ≤2 agents take them in their lists.

### A4. Synthesis
Write, following the protocol §5–§6:
- `20-analysis/families.md`: dynamic content families with measured profiles;
- `20-analysis/project-profile.md`: domain, objective, authoritative requirements, entities,
  preserve / replace / adapt / **contents / place** / ignore, which references are swap, contents or
  placement, and the fit of the **supplied** assets (registry) to them;
- `20-analysis/directions.md`: numbered directions (subject × structure × execution style). Each
  lists **which supplied assets it would use** (registry entities) and **how the product appears**:
  swap of a named source entity, contents in a named vessel, or placement with its likely anchor.
  - A direction that needs an asset type the user did not supply is either adapted to what exists
    or marked "needs <type> — not supplied".
  - Directions are also shaped for the **locked model** (its durations, references, audio and
    frames, from its `index.json` entry). No direction may depend on a capability the model lacks
    unless it states the adaptation.
  - **Create** presents them as style groups (A6).
- **Recreate:** `20-analysis/recreate-ranking.md`, every reference ranked by recreate fit (protocol
  §5).
- **With examples:** `20-analysis/house-approach.md` (protocol §9.3): the user's consistent approach,
  one rule per line with its evidence and the default it replaces. Directions, picks and plans
  follow it (contract item 18).

Show a **short** chat summary:
- the project profile in about 5 lines;
- the families table;
- the house approach in 2–4 lines, or "no examples";
- then the numbered style groups (Create) or the top of the recreate ranking (Recreate).
Then run `T state --run RUN set stage=analyzed next_step=count`.

### A5. How many videos
- **Create:** ask with AskUserQuestion (header "Videos"), options "1", "3", "5" ("Other" allows
  any number).
- **Recreate:** ask (header "Recreate"), "How many reference videos should be recreated?", options
  "1", "3", "5" ("Other": any number up to the usable references).
- Store the answer in `requested_videos`.

### A6. Create: style groups (Create only)
- From the families and directions (A4), present numbered **style groups**:
  `<content type> × <style> × <subject>`, grouped by content type. Examples: "G1 Organic × POV skit
  × gym", "G2 Organic × story-time × office", "G3 Anime × reaction × school".
  - Each group lists its mechanism, typical length, and how the product appears.
  - They are the agent's suggestions, built from the analysed patterns.
- Ask with AskUserQuestion (header "Styles", `multiSelect: true`), with the up-to-4 best groups.
  The user picks **one style or a mix**. "Other" accepts numbers or quantities ("2×G1, 1×G4").
- Without exact quantities, spread the videos across the chosen groups first, then by fit. Show the
  allocation in one line and store it in `directions`.
- **The N videos are varieties.** Each is its own new concept: a different scenario, hook, setting
  or character beat.
  - Each one exploits the patterns that made the references go viral: hook type and timing,
    structure, pacing, content type, camera, humour, and payoff.
  - The client's product is blended into the concept (its most suitable use, `generation-system.md`
    §4b.0), the way the house approach does it when examples exist.
  - No two videos repeat the same concept.
- **Create never uses a reference as input.**
  - No reference video, frame or clip is uploaded, edited or passed to a generation.
  - The analysis informs only the concept, structure, pacing, camera, product use and text role.
  - A meme the style calls for may still be placed in CapCut: an insert cut from a reference, or a
    supplied file.

### A6r. Recreate: pick the references and plan the edits (Recreate only, autonomous)
- **Use the recreate ranking from A4** (protocol §5). It weighs:
  - the integration form available for the product (swap / contents / placement);
  - the number of people against the supplied characters;
  - the own-content length after stripping inserts, against the locked model's edit range. A longer
    one is split, which may need the A7b permission;
  - the load of text and overlays;
  - the motion complexity for the model's `edit_kind`.
- **Take the top N.** Show one line per pick plus two runners-up, then proceed; the user may swap
  picks by replying. Store `recreate_picks`.
- **Decide each pick's operations autonomously**, with no E3 questions:
  - **Person → character:** each person becomes a supplied character. Rotate characters across
    videos, one per person, using the guide's person-replacement contract.
  - **Product:** swap, contents or placement (item 14; `generation-system.md` §4b), written as edit
    operations ("Replace only …", "Add only … at …"). With examples, the house approach shapes the
    anchor, prominence and use.
  - **Source text:** every overlay text is removed in the edit (`text-and-format.md` §2) and comes
    back as CapCut layers, word for word. Usernames, handles, watermarks and source brands do not
    come back.
  - **Inserts** (memes) stay the reference's own: stripped before the edit, placed back in CapCut.
  - **Audio:** the reference's original audio for its own content is restored onto the edited
    picture (X8 step 1); the inserts keep their own sound.
    - With inserts: `T restore-audio --generated <edit> --source <own.mp4>`.
    - Without: `--audio` from `files_audio`.
  - **Action timing (item 19):** the restored audio fixes when everything happens, so the edit keeps
    the reference's timing. Add the pick's **sync anchors** to its card (`generation-system.md` §5c:
    words with their mouth movements, impacts, steps, pickups, sips, from the transcript, the
    storyboards and the audio profile's hits); the plan and the request keep them.
- **Prepare each pick's source** as in Edit Mode E5, from its own content:
  - **With inserts:**
    `T strip-inserts --video "<original reference>" --inserts "<in-out,…>" --out <RUN>/10-media/<V>/own`
    gives `own-silent.mp4`, and `map.json` with the split points.
  - **Without inserts:** the silent copy from A1.
  - Then 9:16 (`T conform` / `reframe`). Split at cuts into the edit model's range when it is
    longer.

### A7. Asset plan (autonomous — picks from the supplied assets only)
- For every planned video, choose from the registry (A2b) the assets that fit its direction
  (Create) or its reference (Recreate):
  - which product or object entity, and which variant (with its contents sample when needed);
  - which character(s). Recreate: which character replaces which person;
  - any interface, brand or environment asset.
- **Distribute sensibly.** Spread several products or variants across videos unless the user or a
  document says otherwise. Rotate approved characters when no assignment is given. Pair assets that
  belong together (a product with its own label close-up).
- For each product, record its integration form, **swap**, **contents** or **placement**
  (`generation-system.md` §4b.0). The exact anchor is decided in X1.
  - **Recreate:** from the reference card's client-entity fit.
  - **Create:** designed into the new concept, as the product's most natural use and blend in that
    scene.
  - **Contents** needs the chosen variant's contents sample (e.g. the liquid photo of that flavour).
  - **Contents comes first** whenever the scene gives the subject a vessel of the product's category
    (a glass on the café table): the vessel holds the product, and the package stands beside it.
  - Pick a variant that has one. With none supplied, fall back to placement and say so.
- **House approach** (when examples exist): where it is consistent, it decides the anchor style,
  prominence, how often the product is used, and the clip and text habits. Record which of its rules
  each video applies.
- Give every video a **planned length**:
  - **Create:** its direction's typical length, adapted to the concept;
  - **Recreate:** the reference's own length.
  Only the generated or edited part counts toward generations: inserts are cut, never generated.
- Show the plan in one line per video and proceed; the user can change it by replying. Examples:
  - `Video 2 — D3 — ~12 s — product B (variant 2) via placement (in hand) + character "anna"`;
  - `Video 3 — D1 — ~45 s (2 generations) — product A via swap of the source can`;
  - `Video 4 — D2 — ~27 s (25 s generated + 2 s meme) — product A (peach) as contents: cup + open can`;
  - `Video 5 — D4 — ~15 s — product C (the car, red) via placement: parked at the curb behind him`.
- **Never** fill a gap from the references folder. If a planned concept needs something that was not
  supplied, adapt the concept to the supplied assets, e.g. hands-only POV when no character was
  supplied. If no adaptation keeps the direction's mechanism, ask one question: drop the element, or
  let the user add files.
- Do not upload yet. Shared uploads happen once in A9; each video's own inputs come in its X3.

### A7b. Long videos: the only permission question in Analyze Mode
A video **over 30 s** that therefore needs **2 or more generations** with the locked model is never
generated without the user's permission. Nothing else in Analyze Mode asks for permission.
1. **Plan its clips first** (`generation-system.md` §3b):
   - the split points, on the reference's own cuts wherever possible;
   - the method for every seam (cut, native extension, or last-frame chain, from the model's
     `index.json → continuation` entry);
   - the cost. Preflight each distinct clip request with `get_cost`; prompt text does not change
     the price.
2. **Ask with AskUserQuestion** (header "Long video"): one question per long video, up to 4 per
   call. Question: "Video N (~45 s, D3) needs K generations with <model>. Generate it?" Options:
   - "Generate in K clips (≈C credits)" — the description says where the seams fall and how they
     join;
   - "Condense to one generation (≤<max> s, ≈C1 credits)": the same mechanism with tighter pacing;
   - "Skip this video".
   "Other" lets the user give a different length.
3. **Store each answer**, and never re-ask it on resume:
   `T state --run RUN set long_videos.NN='{"planned_s":45,"clips":K,"decision":"clips|condense|skip"}'`.
4. **When it applies, and when it doesn't:**
   - If the X1 plan later pushes a video that wasn't asked about over 30 s, ask then, for that
     video only.
   - A video of **30 s or less never asks**, even when the locked model needs several clips for it
     (a model with a shorter maximum). Its brief states the clip count.
   - Only **generated** content counts: reference inserts (memes) are cut, not generated
     (`generation-system.md` §3c). Example: a 35 s reference with 6 s of memes is one 29 s
     generation, so no question.

### A8. Load the locked model's documentation
The model was picked at the start (§2.4) and does not change.
1. Read **only** `ATP/<guide>` for that model (from `index.json`), `ATP/higgsfield/higgsfield-mcp.md`,
   `ATP/reference/generation-system.md`, `ATP/reference/text-and-format.md`,
   `ATP/reference/capcut-assembly.md` and `ATP/reference/production-agents.md`.
   - For a model with no guide, read `ATP/models/_generic-fallback.md`.
2. `models_explore {action:"get", model_id}` once. If the live parameters differ from the guide, the
   live ones win; note the drift.
3. Where a planned concept needs something this model cannot do, adapt the approach within the model
   and state it in the video's brief. Examples:
   - build a 9:16 start frame from the supplied assets when the model has no reference roles;
   - split into clips when the duration exceeds the model's range.
   Overlay text never depends on the model: it goes in CapCut. Never switch models.

### A9. Prepare every video (this session)
Plan everything before production, in allocation order, **without asking for confirmation**
(contract item 15):
1. **X1–X4 for every video:** plan, pattern card, request(s), pre-generation QC. Recreate plans
   take the approach and source preparation from E4–E5.
2. **Shared inputs, once:**
   - the Higgsfield project folder (X5: `list_workspaces` → `create_project`), stored with
     `T state --run RUN set higgsfield.folder_id=<id>`;
   - every asset the asset plan uses, uploaded (X3), with media ids in `state.json → assets.uploads`;
   - Elements when the model uses them.
3. **X5–X6 per video:** preflight its first request and print its brief. Then print the estimated
   total once, as information, against the balance.
4. **The only question in this phase** is a long video's permission (A7b), when a plan newly pushes
   a video over 30 s.

### A9b. Produce in parallel (production agents)
- **Spawn one production agent per video** (`reference/production-agents.md` §2 prompt;
  `subagent_type: general-purpose`, `run_in_background: true`).
  - At most `production.max_parallel_agents` (5) run at once; start the next queued video when one
    finishes.
  - Each agent runs X3 (its own inputs) → X7 → X8 → X9 → X10 for its video, ending with its CapCut
    project, and returns one JSON line. It runs X5 again for any request it changes.
- **As each agent reports:**
  - read its `60-outputs/video-NN/result.json`;
  - record it (`T state --run RUN append videos='<json>'`);
  - print one line: video, status, CapCut project, credits.
- **Blockers come back from agents and are handled here:**
  - a permission is needed (A7b) → ask, then launch that video again;
  - CapCut was running → its project is pending until the wrap-up;
  - credits ran short → launch nothing more, report the shortfall; the run stays resumable;
  - a request failed twice → report it in the wrap-up.
- **QC verdicts are autonomous** (X9); a video that still fails is reported in the wrap-up.
- **Without the Agent tool**, run X3–X10 per video in this session, one video at a time.

### A10. Wrap-up
See §6.

## 4. Edit Mode

### E1. Intake
- `T inventory "<video path>" … --run RUN --as sources`: only videos are processed. Any other file
  there is ignored and never used as an asset.
- `T split-audio "<video path>" … --run RUN`. For every original video, **inside the given path**
  (sub-folders mirrored), it writes:
  - the audio to `files_audio/<name>.<ext>` (stream copy);
  - a silent copy to `videos_without_audio/<name>`.
  It links both to the inventory (`silent_path`, `audio_path`, `audio_offset`) and is idempotent.
  Report it in one line.
  - Only silent copies are ever uploaded to Higgsfield for replace, swap and other edits: there is
    less chance of flagging.
  - The approved result gets the original audio from `files_audio` (X8), and then goes to a `final`
    folder in the same path (X10).
- Then `T prep-all --run RUN --jobs 2`. The analysis uses the originals, with audio, for transcripts.
- **Examples, when given** (contract item 18): `T inventory "<examples folder>" --run RUN --as
  examples` and `T prep-all --run RUN --set examples`, then one card each and
  `20-analysis/house-approach.md` (protocol §9), once per run, before the first edit. Every edit
  follows it for how a replacement is held, placed and blended.
- Videos are edited **one at a time, in inventory order** (or the user's order).

### E2. For each video — understand it first
- Read `video.md` and `timeline.md` and view every storyboard sheet in order (densify contact
  moments).
- Write a compact card `20-analysis/cards/<V>.md` (protocol §3):
  - the full timeline;
  - actions, subjects and objects in the video (numbered, so E3 can point at them);
  - camera and staging;
  - continuity states;
  - the **sync anchors** (item 19, `generation-system.md` §5c): every moment where a sound in the
    original audio belongs to a visible action (each spoken line and whose mouth says it, impacts,
    steps, pickups, sips, opens), with its time, from the transcript, the storyboards and, when it
    helps, `T audio-profile` hits;
  - the **source-text inventory** (`text-and-format.md` §2.1).
- Show the user a 4–6 line understanding of the video.

### E3. Choose the operations, then drop the files for each
1. **Operations.** Ask with AskUserQuestion (header "Edit", `multiSelect: true`), "What should happen
   in video N?":
   - **Replace an object / product**: swap an item (product, object, interface, logo…) for yours;
   - **Swap a person / face**: replace a person or character with your character;
   - **Remove something**: take an element out;
   - **Insert something**: add a new element.
   "Other" covers alter, restyle, relight, background change or recreate, described in words.
2. **Targets and files, per chosen operation.** Right after, ask in plain chat in **one** message,
   pre-filled with numbered candidates from the E2 understanding. Only include the lines for the
   operations the user chose:
   ```
   In video N I see: 1) <person A, where/when>  2) <object, where/when>  3) <…>
   Replace → which item(s)? Drop the replacement files (product samples: template + other views).
   Swap → which person(s)? Drop the character files for each (face close-up + full body if you have them).
   Insert → what, where, when? Drop its files.
   Remove → which item(s)? (no files needed)
   Reply like:  replace 2: <paths>   swap 1: <paths>   (or "same files as video 1")
   ```
   Then stop and wait.
3. **Register the files for this edit only.**
   - `T inventory <paths…> --run RUN --as assets --scope video-NN`, then
     `T prep-assets --run RUN --scope video-NN`; view the contact sheet.
   - **Bind each file to the operation and target it was given for.** The user's grouping is
     authoritative. If files arrive ungrouped, sort them by what they show (a person vs. an object).
     Ask only if that is still ambiguous.
   - Within each product, pick the canonical template and mark the other views and variants.
   - "Same files as video K" reuses that scope explicitly. Nothing else carries over.
4. Remind the user once that all source text (captions, usernames, watermarks, stickers, overlays…)
   is removed unless they name text to keep.

### E4. Locked model — how it performs this edit
- The model was picked at the start (§2.4) and does not change. Before the first edit, read **only**
  its guide + `higgsfield-mcp.md` + `generation-system.md` + `text-and-format.md`, and call
  `models_explore get` once.
- Map the chosen operations onto the model's edit capability (`index.json → edit_kind`):
  - **✓ edits video** (`video_edit`, `object_replace`): a true edit of the 9:16 source.
  - **↔ motion transfer:** the source drives motion; the supplied files define the subjects and
    scene.
  - **≈ recreate** (`video_refs`): regenerate the clip with the source as a motion, camera and timing
    reference, applying the operations.
  - **✗ frames only:** recreate from clean 9:16 frames of the source, with the operations applied to
    those frames through the supplied files, plus a prompt that rebuilds the source's action.
- **Timing (item 19).** The original audio comes back, so the approach must keep the source's
  timing. ✓ and ↔ keep it by construction. ≈ keeps it only with the source as the video reference
  and the same duration. ✗ cannot guarantee it: rebuild the actions in the source's order and pace
  from the sync anchors, and say in the brief that sync is at risk.
- State the approach in the brief (one line). Never switch models.

### E5. Prepare the source (local, deterministic)
- **Start from the silent copy** (`videos_without_audio/…`), never from the original with audio.
  Every preparation below produces a silent file under `RUN/10-media/<V>/prepared/`. The user's
  folders keep only `files_audio` and `videos_without_audio`.
- **9:16.** If the source is not 9:16, choose (per `text-and-format.md` §4.1):
  - `T conform` with a focus point, when a crop keeps every important subject;
  - Higgsfield `reframe` (9:16, 720p; preflight first);
  - regeneration with the source as a video reference.
- **Length.** If the source exceeds the edit model's input range, split it at cuts with `T trim` into
  segments, edit them in order with identical references and wording, then `T concat` the edited
  pictures. The original audio is restored once over the joined result.
- **Duration (item 19).** Request each segment at its exact source duration, or at the nearest
  allowed duration above it and trim the extra afterwards. Never request a shorter one: the actions
  would be squeezed against the original sound.
- **Text.** Plan the removal per `text-and-format.md` §2.2:
  - local `T clean` for small static overlays;
  - otherwise explicit remove operations in the edit prompt;
  - otherwise clean-frame regeneration.

### E6. Generate
Run **X1–X10** (§5) for this video, as an edit. The source video is the unique master, and the plan
holds:
- the operations;
- the substitution map;
- the integration analysis;
- the text removal;
- the audio:
  - request **no generated audio** whenever the model has a flag for it (`generate_audio:false` /
    `sound:"off"`);
  - the final **always** carries the original audio from `files_audio` (X8), and any audio the
    model returns is discarded.

Before the first submission of the run, show the estimated total against the balance: the
preflight of video 1 × the number of videos. Then ask with AskUserQuestion (header "Go"):
- "Start editing (≈X credits)";
- "Edit video 1 first, then decide";
- "Stop here".

Pause again before an attempt whose preflight exceeds
`config.json → higgsfield.confirm_cost_above_credits`, or when credits run low.
After every attempt, the finished video opens for the user's review (X9-R):
- **"Looks good"** moves on;
- **"Needs changes"** re-edits **the original source video** with the feedback, as a new attempt;
- the loop repeats until the user approves or stops.

### E7. Next video
Only after the user approved the current video (or chose to stop), repeat E2–E6 for the next one. Do
not re-ask for the model. Every video gets its own E3 (operations → files); the user can answer "same
files as video K".

## 5. Per-video execution loop X1–X10 (both modes)

- **X1 — Plan (work backward).**
  - Write `40-briefs/video-NN-plan.md` with `generation-system.md` §2–§6:
    - intent;
    - the per-second time budget from the family profile;
    - roles and assets;
    - the scene;
    - the **entity state ledger**;
    - the **integration analysis** for every substitution or insertion;
    - for a **contents** or **placement** video, the **integration plan** (`generation-system.md`
      §4b):
      - the form (§4b.0);
      - for contents: the vessel or form, the amount over time, and the variant's contents sample;
      - the anchor, chosen by the product's size and use (§4b.1: a handheld item in hand, on a
        surface or elsewhere in the environment; a large one where such things stand; software on
        a device in use);
      - prominence;
      - the anchor row in the ledger, with any motivated move (a pickup and set-down, a car driven
        away);
      - the ambient match;
    - the **props in the asset photos**: what each character or environment photo shows besides the
      person or place (a glass, a cup, a snack). Each one is planned as the product's contents when
      it is of the product's category, or excluded in the prompt. Nothing carries over by accident;
    - the **house approach** (when examples exist, `20-analysis/house-approach.md`): the rules this
      video applies, and how;
    - for a video with **inserts**, the **insert plan** (`generation-system.md` §3c):
      - the generated length (the reference minus its inserts);
      - each split point as a planned beat boundary;
      - each insert's cut (in, out, video or still, sound, overlays to clean);
    - the **text plan** (Analyze Mode, `text-and-format.md` §3): every overlay text event with its
      wording, final-timeline time and position, always in the house text style (item 6). It is
      placed in CapCut later and never generated;
    - the **sound plan** (Create, `capcut-assembly.md` §3b), placed in CapCut:
      - the generation carries only dialogue, action sounds and ambience, with no generated music;
      - the soundtrack's role, mood, tempo and energy arc, from the references' sound profiles;
      - its source: a supplied track, the reference's own speech-free sound, or a matching track
        to download;
      - the sound effects and their hit points on the new video's beats;
    - for a **multi-clip** video, the **clip plan** (`generation-system.md` §3b):
      - the seams, on the reference's cuts first;
      - the join method of each seam (from `index.json → continuation`);
      - the hand-off state of each seam;
      - the clip durations;
    - the logic and anti-slop gate;
    - conflict resolution.
  - Use the provenance labels.
  - Analyze Mode: rotate approved characters across videos when no assignment is given.
- **X2 — Pattern card and request.**
  - From the selected guide's **§4.0 official examples**, write the pattern card
    (`50-requests/video-NN-pattern.md`).
  - Decide the channel for everything: parameters vs. references vs. prompt vs. post-production.
  - Write the prompt in the model's proven structure and syntax.
    - A placed product (or a contents vessel with its package beside it) is described as part of
      the scene from the first frame, at its anchor. Use no edit verbs and no ad vocabulary
      (`generation-system.md` §4b.5).
    - Every vessel's contents are stated from the contents sample ("the glass holds …"); an
      unstated glass comes back as water. A character photo's role is limited to the person ("only
      his face, hair, build and clothing; not the glass, table or background of Image 4") unless
      the plan keeps its props as the product's contents (`generation-system.md` §4b.5).
    - Free physical motion (a spin, toss, roll or pour, or a vehicle's move) is described by its
      physics, never by a schedule of exact times. A required end state gets a visible cause, such
      as a hand stopping the product label-forward or a driver braking into the spot
      (`generation-system.md` §5b). A corrected retry removes timing constraints from free motion;
      it never adds them.
    - Analyze Mode prompts are always **clean plates**: no overlay text. The only lettering is the
      product's own label, logo or badge.
    - With inserts, the prompt covers only the generated content, and puts a natural beat boundary
      at each split point.
    - **Timing lock** (item 19; Edit Mode and Recreate, whenever the original audio comes back): in
      the model's own wording, keep the exact timing, speed and order of every action and mouth
      movement of the source (e.g. "same timing as @Video1 …; add, skip, repeat or reorder
      nothing"). A swapped person keeps the source person's mouth movements, expressions and
      gestures on the same frames; a swapped product moves exactly as the original item did. The
      timing comes from the source video, never from timestamps in the prompt
      (`generation-system.md` §5c), and the duration parameter matches the source segment (E5).
  - Assemble the params from the guide's §2.4 recipe and the index's `output_9x16_720p`, then save
    `50-requests/video-NN-request.json`.
  - Multi-clip: one request per clip, `50-requests/video-NN-cK-request.json`. A continuation clip
    uses the guide's extension or "Across clips" wording and restates the seam's hand-off state.
  - Edit Mode: include the model's no-audio setting when it has one (`generate_audio:false`,
    `sound:"off"`). The original audio is merged in X8.
- **X3 — Inputs.**
  - Take the assets only from this video's registry: scope `project` (Analyze Mode asset plan) or
    scope `video-NN` (Edit Mode files for this edit).
  - Upload the files this video needs, once per run: `media_upload` → `T hf-put` (exact
    content type) → `media_confirm`. Reuse media ids recorded in `state.json`.
  - **Every video sent to Higgsfield is silent:** the `videos_without_audio` copy, or its prepared
    derivative from E5. Never upload an original video with its audio. (A clip this run generated
    may go back with its generated audio, as the input of a native extension.)
  - **Multi-clip continuous seam:** the input comes from the **accepted** previous clip
    (`generation-system.md` §3b.3):
    - last-frame chain: `T last-frame --video <clip> --out <…/cK/handoff.png>`, view it, upload it,
      and pass it as `start_image`;
    - native extension: the accepted clip itself as `@Video1`. Pass its job id directly; if the
      server refuses that for a video role, or the clip was trimmed, upload the file.
  - Create Elements when the model supports them and assets recur.
  - **Contents form:** upload the variant's contents sample with the product views, and bind it to
    the vessel's contents in the prompt ("the drink in the cup has the colour, clarity and bubbles
    of @ImageN", "the gum piece she takes has the shape and colour of @ImageN"). A start frame
    shows the vessel already holding it, and the opened package beside it.
  - For start-frame models, build and check the 9:16 start frame with an image model
    (`assets-and-substitution.md` §5). It must match the canonical geometry before it is used.
    That `generate_image` call is paid, so it follows the same ledger discipline as X7: its own
    request file `50-requests/video-NN[-aK]-frame-request.json`, `ledger begin`, one call, `ledger set`,
    then `jobs_wait`.
- **X4 — Pre-generation QC.**
  - Run the mental render of `generation-system.md` §8 from the first frame to the last.
  - Fix any conflict in the plan and the request before continuing.
- **X5 — Preflight.**
  - `generate_video {params:{…, get_cost:true}}` → cost and `adjustments`. **One** preflight per
    distinct request. Preflight again only after the request changed.
  - Reconcile every adjustment: an unsupported or dropped parameter means rethinking the request,
    not ignoring it.
  - Project folder: create it once per run (`list_workspaces` → `create_project`, keyed by the run
    id) and pass `folder_id`.
- **X6 — Brief.**
  - Print the short brief (`generation-system.md` §10): concept, reference pattern,
    characters/assets, substitutions, main action and states, style/camera, text plan, model /
    operation / duration / 9:16 720p, cost, adaptation logic.
  - Analyze Mode: no gate; the brief is information (item 15). Edit Mode: the E6 gate.
- **X7 — Submit and wait (ledger-guarded; no spam, no glitches).**
  1. `T ledger begin --run RUN --video NN --attempt K --request 50-requests/video-NN[-aK]-request.json`
     (a clip: `--video NN-cK` with its own request file).
     - **Exit 3 means do not submit.** Follow its `action`:
       - an open job exists → resolve it with `jobs_wait`, or for `pending` / `unknown` via
         `show_generations {type:"video", only_completed:false, size:5}` and `transactions`;
       - the request is a duplicate of a finished job → reuse that job;
       - the request failed twice → change it or report the failure.
  2. Exactly **one** `generate_video {params}` call: `count` 1, no `get_cost`, never in parallel with
     anything, never twice in one turn, never inside a retry loop.
  3. Record the outcome at once:
     - a job id came back → `T ledger set --run RUN --fingerprint F --job J --status submitted`;
     - a transport error or timeout with no job id → `--status unknown`. Then find out what happened
       (history and transactions), and set `submitted` with the found job id, or `failed` with the
       note "not created". Only then may a new `begin` happen.
     - Handle `unlim_choice` (ask), `recovery_tool` (call it), and validation errors. A validation
       error means nothing was created: set `failed` with the note "rejected before creation", fix
       only the named field, and begin a new attempt.
  4. Poll `jobs_wait {jobs:[{index:0, job_id}], timeout_seconds:15}`, respecting
     `poll_after_seconds`.
     - Terminal → `T ledger set --job J --status completed|failed`.
     - Still running after ~25 min → tell the user, and keep waiting on that same job. Never
       resubmit because a job is slow.
  5. A failed job is refunded. Diagnose it before any retry; the ledger allows at most one retry of
     an identical request.
- **X8 — Download and post-process.** `T hf-get` into `60-outputs/video-NN/aK/raw.mp4` (K = the
  attempt number; the raw Higgsfield output is always kept), then as needed, in this order:
  1. **Edit Mode and Recreate — original audio back:**
     `T restore-audio --generated <raw or joined> --audio "<files_audio file>" --audio-offset <audio_offset> [--start <segment start>] --out <aK>/with-original-audio.mp4`.
     The picture is Higgsfield's and the sound is the original's. A clip that is slightly shorter
     keeps sync from the start and cuts the audio at its end; the tool reports it. A source that had
     no audio gives a silent final.
  2. `T conform` → exactly 720×1280;
  3. `T trim` (generated dead head or tail);
  4. `T concat` (multi-clip videos):
     - each clip is downloaded to `60-outputs/video-NN/cK/aJ/raw.mp4`, conformed, trimmed and
       QC'd (X9) **before** the next clip is submitted;
     - after the last clip:
       `T concat --clips <c1> <c2> … --seams <cut|continuous,…> --out 60-outputs/video-NN/joined.mp4`.
       Seams are `cut` on planned cuts and `continuous` on chained or extended joins. Edit Mode
       segments (E5) are always `cut`;
  5. **Sync check** (item 19; Edit Mode and Recreate), once the picture is final and the original
     audio is on it:
     `T sync-check --source <the prepared source; own-silent for a Recreate> --output <final> [--start <segment start>] --out <aK>/sync`.
     View `sync-sheet.jpg` and the sync anchors densified (mouths on their words, contact on its
     impacts). Then act on the verdict:
     - `in_sync` (within ±0.1 s everywhere) → continue;
     - `constant_offset` → apply its `fix`, with no new generation: trim the picture's head when the
       output is late, or re-run `restore-audio` with `--start` increased when it is early. Then
       merge and check again;
     - `drift` or `out_of_sync` (faster, slower, or an action added, skipped or moved) → a
       regenerate reason in X9;
     - `inconclusive` (motion too different to measure, e.g. a heavy restyle) → judge it on the
       sheet and the densified anchors.
  6. **Analyze Mode:** the result is the **clean video** `60-outputs/video-NN/clean.mp4`: conformed,
     trimmed, joined, with no overlay text. After it passes X9, assemble its CapCut project
     (`reference/capcut-assembly.md` §2–§5):
     - `T capcut-name --video NN` → `capcut_clone_draft` (empty) → `T capcut-prep`;
     - the inserts cut from the reference (`generation-system.md` §3c);
     - the generation placed, split at each insert point, with each insert in its gap;
     - every overlay text as a text layer;
     - `capcut_validate` → `capcut_save` → the capcut-cli repair lines → the preview.
     If CapCut is running, keep going and assemble all pending projects at the wrap-up.
- **X9 — QC.**
  - `T qc --video <final> --out <dir> --mode <mode> --allowed-text "<planned text>|<printed words of
    every visible client asset>"`, then view the storyboard sheets.
  - Check identity, asset geometry against the canonical template, the ledger states, interactions
    (densify contact moments), lighting and reflections, text, pacing and dead space, and the format.
  - **Motion beats at 30 fps** (`generation-system.md` §5b): every motion beat (spins, tosses,
    pours, landings; a vehicle driving, turning, braking or parking) gets a full-frame-rate sheet
    across the beat. A snap, a pause-and-resume without a cause, a reversal, a slide without a
    cause, or a morphing label, badge or body is a regenerate reason. Product-pun text is timed to
    the measured moment.
  - **Action sync** (item 19; Edit Mode and Recreate): the X8 sync verdict and sheet. Every sync
    anchor lands within ±0.1 s of its sound: words on mouth movements, impacts on contact, steps on
    footfalls. Drift, or an action added, skipped or moved, is a regenerate reason; a steady offset
    is a post-fix.
  - **Leftovers** (`generation-system.md` §9b): only the must-not-survive list counts, and it is
    fixed autonomously.
  - **House approach** (when examples exist): the video follows the rules its plan applied.
  - **Contents** (`generation-system.md` §9): every vessel of the product's category shows the
    product's contents. A glass of water beside the can is a regenerate reason, never a note.
    - Must not survive: the replaced person, the swapped or competitor product, overlay text,
      handles, platform logos and watermarks, featured third-party branding, flaggable content.
    - Background decor and clothing logos are fine. They are not reported, not asked about, and
      never cost a retry. In Analyze Mode no QC question ever goes to the user.
  - For a placement, also check the product's spot across the sheets, densified around cuts and
    pickups. These are regenerate reasons:
    - it is missing or unrecognisable;
    - it is duplicated;
    - it changes spot without a visible action;
    - it is featured like an ad;
    - it looks pasted in.
  - **Multi-clip:**
    - every clip passes QC before the next is chained from it;
    - the joined video is checked ±1 s around each seam (densified): positions, the product's
      anchor, light and colour, and the audio;
    - a bad seam → trim a few frames there and re-join; otherwise regenerate the later clip of
      that seam.
  - **Inserts:** each split point lands on a real beat boundary of the output (within ±0.5 s of the
    plan). Each insert is cut on its exact frames, with its sound, and a video meme is never a
    screenshot.
  - **CapCut project** (Analyze Mode, `capcut-assembly.md` §5):
    - the read-back timeline matches the plan (pieces, inserts, text times and positions);
    - `capcut lint` reports 0 errors;
    - the preview shows the right order, sound and text.
    Fix in the project, not by regenerating.
  - Apply the post-fixes (`trim`, `conform`, `restore-audio`, a sync offset) that need no new generation.
  - **Analyze Mode verdict** (autonomous):
    - accept;
    - or **one** deliberate regeneration with a diagnosed, corrected request (a new ledger attempt;
      the preflight cost is shown in its brief);
    - or report the failure honestly.
- **X9-R — Edit Mode review (every edit, every attempt).**
  1. Open the finished video for the user: `T open --file <final.mp4>`. This is the version with the
     **original audio** already merged, so the user judges exactly what will be delivered, lip-sync
     included. Also print:
     - its path and the raw Higgsfield file next to it;
     - the Higgsfield result URL;
     - 1–3 QC notes (e.g. leftover text or a duration difference, or "no issues found").
     - the sync verdict (item 19), always: the measured offset and the sheet's path. A `drift` or
       `out_of_sync` comes first, with the moments that miss their sound.
  2. Ask with AskUserQuestion (header "Review"), "Video N, attempt K — is it okay?":
     - **"Looks good — next video"** → `T ledger set --job J --status accepted`, then X10, which
       places the approved video in the `final` folder.
     - **"Needs changes"** → ask in plain chat what to change, and let them add or replace files.
     - **"Stop here"** → keep the files, go to the wrap-up.
     "Other" lets the user type the changes directly.
  3. **Re-edit from the original.** A new attempt always starts from the **original source video**
     (the same prepared 9:16 source, already uploaded; its media id is reused), never from the
     previous output. It uses the same per-edit files plus any new ones: re-run `inventory` for scope
     `video-NN` with the full path list.
     - Fold the feedback into the plan and the request, and save them as
       `50-requests/video-NN-aK-request.json`.
     - The brief shows what changed versus the previous attempt, plus the preflight cost.
     - Then X5 → X7 → X8 → X9 → X9-R again.
     - Mark the rejected attempt with `T ledger set --job <old> --status rejected`.
     - Loop until the user says it is okay or stops. Every attempt is kept under
       `60-outputs/video-NN/aK/`.
- **X10 — Record.**
  - **Edit Mode:** the approved video (generated picture + original audio, already 720×1280) goes to
    the **`final` folder inside the given path**:
    `T finalize --run RUN --video NN --file <aK approved file> --original "<original video path>"`.
    - It is named after the original video (`<given path>/final/<name>.mp4`, sub-folders mirrored).
    - It is checked: picture present, 720×1280, audio present exactly when the original had audio.
    - The folder is marked so later scans skip it. A previously approved final of the same video is
      moved into the run folder, never overwritten silently.
    - Only approved videos are placed there.
  - **Analyze Mode** (`capcut-assembly.md` §6):
    - the **CapCut project** `DD_Mon_YYYY_vNN` is the master; the final is exported from CapCut;
    - `RUN/deliverables/video-NN-clean.mp4`: the same edit with its inserts and without text,
      assembled locally;
    - `RUN/deliverables/video-NN-preview.mp4`: the CapCut proxy with the text.
  - Append a row to `RUN/deliverables/README.md`: direction, model, params, prompt file, assets, job
    id, attempt, credits, verdict, final path, notes. For a multi-clip video, list every clip's
    job id and the seam methods. Analyze Mode adds the CapCut project name, the inserts and the
    text events.
  - Update `state.json` (`videos[]`, `next_step`), then move to the next video. In Edit Mode, only
    after the user said "Looks good".

## 6. Wrap-up (both modes)

Report in a short table: video → direction/edit → model → duration → credits → verdict → file path.
In Edit Mode the file paths point into `<given path>/final/`; state that folder once.
In Analyze Mode the table also names each video's **CapCut project**:
- First assemble any projects still pending. If CapCut is running, ask the user once to close it
  (a blocker, not a permission), then assemble them.
- Then say: "open CapCut → the projects are listed by name → review → Export".
Then give:
- the total credits used (`transactions` / `balance`);
- the run folder (keep it: the CapCut projects use its files);
- the examples used ("6 examples → house approach applied") or "no examples";
- only if `config.json → capcut.text_style.learned` is ever empty (it holds the user's locked
  preset): "To copy CapCut's exact text preset, add a text in any CapCut project, pick the preset,
  close CapCut, and run `T capcut-text-style --learn --draft "<store>/<that project>"`";
- any open issues.

Offer, in one line, the next useful step (more videos, a different direction, regenerate a flagged
video).

## 7. Never

- Never use or create a Claude Code Workflow.
- Never spawn more than 2 analysis agents, more than 5 production agents at once, or a production
  agent in Edit Mode. Never give agents overlapping work.
- Never read model guides other than the locked one.
- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never shorten the model menu. Every available model is always shown, with the pinned ones on top.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Never upload, recreate or cut an example into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never ask for assets again in Analyze Mode once they were dropped at the start (unless a concept
  cannot be adapted).
- Never reuse one edit's files for another edit unless told to.
- Never apply generic prompting when a model guide exists.
- Never copy usernames, handles, watermarks or source brand names. Reuse reference caption wording
  only as a generic meme line (`text-and-format.md` §1).
- Never let the video model render overlay text in Analyze Mode. Generate clean and place the text
  in CapCut. Never burn it in with `atp.py captions`, except as the stated fallback.
- Never give a CapCut text layer another font, size, colour or preset than the house text style
  (font System, size 10, the user's locked preset in `capcut.text_style.learned`), unless the user
  asks for it in the run. Never re-learn or replace that preset (`--learn --replace`) unless the
  user explicitly asks for a new one.
- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
- Never `capcut_save` with `force:true` or run capcut-cli with `--force-write` on the live CapCut
  store, and never write a project while CapCut is open.
- Never keep source text in Edit Mode unless the user kept that specific text.
- Never let source identities or competitor branding survive when approved replacements exist.
- Never pin free physical motion (spins, tosses, rolls, pours, a vehicle's moves) to exact
  timestamps. Never accept a snap, a pause-and-resume, a slide without a cause, or a morphing
  label or badge (`generation-system.md` §5b).
- Never flag, ask about or spend a retry on incidental background items: posters, toys,
  ornaments, signs, and clothing or footwear logos (`generation-system.md` §9b). Only the §9b
  must-not-survive list counts.
- Never deform a client asset's canonical geometry or identity to fit a reference object.
- Never leave the client's product out of an Analyze Mode video because the reference had nothing
  to swap. Integrate it instead, as contents or as a natural placement. Never force an unrelated
  source object into a swap.
- Never let a placed product jump between spots (desk → table → chair), appear or vanish without a
  visible action, become the hero of the shot, or look composited.
- Never leave a glass, cup or other vessel of the product's category holding something else (water
  beside the can) when the product's contents fit, and never let a prop from an asset photo carry
  over unplanned.
- Never sacrifice temporal or physical continuity to imitate an individual source frame.
- Never stretch to reach 9:16, never ask for aspect ratio or resolution, and never deliver anything
  other than 720×1280.
- Never upload an original video with its audio to Higgsfield: use the `videos_without_audio` copy
  (or its prepared derivative).
- Never deliver an Edit Mode result with generated audio. It always carries the original audio from
  `files_audio`, or no audio if the original had none.
- Never deliver a video that carries the original audio without its sync check (X8 step 5), and
  never leave drift or a moved action unreported. Never fix sync by stretching or looping the
  original audio.
- Never call a generation tool outside the ledger (`T ledger begin` / `set`).
- Never submit in parallel, never resubmit after an unknown outcome or a slow job, never repeat a
  finished request, never pass URLs or paths as media values, and never set `use_unlim` unasked.
- Never move to the next Edit Mode video before the user approved the current one.
- Never re-edit an Edit Mode video from a previous output: re-edits always start from the original
  source.
- Edit Mode: never spend credits before the "Go" gate of the run.
- Analyze Mode: never ask for permission except for a video over 30 s that needs 2+ generations.
  Never generate any clip of such a video before that permission.
- Never claim results you did not verify.
