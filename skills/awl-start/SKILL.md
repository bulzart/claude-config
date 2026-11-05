---
name: awl-start
description: /analyze-with-loupe phase 1: mode, Analyze sub-mode, the locked video model, inputs, the audio, voiceover, memes and effort choices, create the run. Internal to that command.
user-invocable: false
---

# awl-start — Start: mode, sub-mode, model, inputs, run

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase 1 of `/analyze-with-loupe`. The router (the command) sent you here and passes the command's arguments (`$ARGUMENTS` below) as this skill's args. Nothing else needs to be loaded for this phase.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- *(nothing else from the library: `T model-menu` and `T model-entry --id` print what is needed)*
- effort §1: `AWL/reference/effort/010_1_the-question-awl-start-step-5d.md` (2.1 KB) (every run, step 5d)
- *Static, when `T static check` reports a part the run needs as not ready:*
  - static §9: `AWL/reference/static/090_9_the-static-pc-setup-once-per-pc.md` (1.4 KB)
- *Create (the voiceover method, step 2b, and the voice, language and style, step 5c, when the user takes a method):*
  - voiceover §1: `AWL/reference/voiceover/010_1_the-state-and-the-files.md` (3.0 KB)
  - voiceover §2: `AWL/reference/voiceover/020_2_the-choice-at-the-start-create-f.md` (5.5 KB)

## 1. Paths and tools

| name | value |
|---|---|
| `AWL` | `C:/Users/Glaresquare1/.claude/analyze-with-loupe` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `AWL/config.json`) |
| `T` | `"$PY" "$AWL/scripts/awl.py"`. Every call prints one JSON object on its last line; run through Bash |
| Model index | `AWL/models/index.json` (model id → guide, capabilities, 9:16/720p params). **Never Read it whole** (40 KB): `T model-menu` builds the menu, `T model-entry --id <id>` prints one model's entry and its guide path |
| Model guides | `AWL/models/<guide>.md` is an index; the sections are in `AWL/models/<guide>/`. Which sections each step reads: `awl-model-guide` |
| Higgsfield guide | `AWL/higgsfield/higgsfield-mcp.md` (index) and `AWL/higgsfield/higgsfield-mcp/` (sections) |
| Flag record | Loupe, `http://127.0.0.1:8787` (item 23), started by `T loupe ensure` at run creation and recorded in `state.json → loupe` (`up` or `down`; missing = up): `T caught-flag add, set, reconcile, open` and `T ledger set --flagged`; written in X7 (`awl-submit`), reconciled in A9b and §6, never read during a run. The sample library is read only by `T prompt-template` once per video at X4b (`awl-precheck`), `T qc-consult` at X9 (`awl-qc`) and `T qc-brief` in the free plan (`awl-free-plan`) |
| References | `AWL/reference/<name>/` section files (index: `AWL/reference/<name>.md`): `analysis-protocol`, `generation-system`, `anomaly-catalog`, `creative-direction`, `brand-guardrails`, `text-and-format`, `assets-and-substitution`, `capcut-assembly`, `production-agents`, `voiceover`. Each phase skill lists the sections it needs under "Read now" |
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

   **Analyze Mode → sub-mode.** If `$ARGUMENTS` names `recreate`, `create`, `free` or `static`, use it. Otherwise ask
   with AskUserQuestion (header "Analyze as"):
   - **Recreate**: "Analyze the references, then recreate N of them with your product and
     characters: same scenario, faces and products swapped or blended. Fully autonomous."
   - **Create**: "Analyze the references, then create new videos in suggested style groups (one
     style or a mix), using your product. No reference video is used as input."
   - **Free**: "Say in your own words what the videos must achieve and how. With reference material analysed first, or from your
     requirement alone. The pipeline plans to your requirement, keeps the model's official prompting, the QC stack and Loupe's samples
     and misses, and asks you once to confirm its reading of the plan."
   - **Static**: "Narrated still-image videos in the references' style on a new subject: the images by OpenAI with your key, or by you
     from my prompts; a local Qwen3-TTS voice; CapCut. No Higgsfield."
   **Free → two more things, asked in the same message batch.** (a) Header "Free: references": **"With references"** ("Analyse a
   folder of reference material first; the plan can follow, edit or avoid what they do") or **"Requirement only"** ("No references: the
   plan comes from your requirement and your assets"); `$ARGUMENTS` with `free` and a references folder means with references, `free`
   alone means requirement only. (b) Header "Your requirement": **"I write it now"** (the user writes it in the Other box: what the
   videos must achieve, how many, what happens, the product and how it is used, references to edit or follow, length, text, sound,
   anything they want or forbid) or **"It is in a file"** (the path in the Other box: a .txt, .md or .pdf; `T doc-text` reads it).
   The words are kept verbatim, nothing is paraphrased or trimmed; a one-line requirement is accepted as it is (the free plan shows its
   gaps as visible [I] lines). The requirement is written once the run exists (step 6).
   Store it with `T state --run RUN set analyze_submode=recreate|create|free|static` once the run exists (Free also `free_references=yes|no`).
   **Static → its own path** (item 36): no steps 2b, 2c, 3 or 4 (no voiceover or memes question, no Higgsfield tools, no model menu: the
   images come from the OpenAI model in `config.json → static.images`, or from the user); step 5b is not asked (`audio_ingest=whisper`).
   Its inputs (step 5): the references folder and the assets: the characters as photos and/or descriptions (a text file each, or words in
   the message), usually no product; documents and examples as always. In the same AskUserQuestion call as the QC-fixes question, header
   "Images": **"Generate with OpenAI"** ("I make every image with the OpenAI Images API on your key (OPENAI_API_KEY on this PC), check
   each one and draw again by your QC-fixes choice; it uses your OpenAI credits.") or **"Prompts for me"** ("I write one prompt per image
   and the character sheets; you make the images, put them in one folder and send me its path; I check them."); `$ARGUMENTS` with
   `images api|prompts` answers it. Then `T static check` (add `--offline` with prompts): a part the run needs that is not ready (the key
   with Generate; the TTS environment always) is a blocker: report it with static §9's setup line and stop before any analysis. Music is
   needed only when a bed is planned (A6s): reported, never a blocker here.
2b. **Own voiceover: the method (Create only; item 31), before the model menu.** When the sub-mode is Create, ask with AskUserQuestion
   (header "Voiceover") the method question of `voiceover.md` §2 step 1 (its four options, none recommended); `$ARGUMENTS` with
   `voiceover native|lipsync|overlay` or `no-voiceover` answers it. Free never asks it (`awl-free-plan` step 2b); Recreate and Edit Mode
   never do (item 19). The method shapes the model menu (step 4.4); the voice, the language and the style come after the paths (step 5c).
2c. **Memes (Create only; item 32).** In the same call as step 2b, header "Memes", "Do the videos include memes or other cut-in
   clips?", none recommended: **"Include memes"** ("As the references do: memes, reaction clips or other original clips the style calls
   for, cut from the references with their sound or taken from your files, placed between the generated parts in CapCut.") or **"No
   memes: pure generation"** ("Every second is generated: no meme, reaction clip, screen recording, snippet, still or meme sound is cut
   in; a reference's meme beat is played by the generated scene."). `$ARGUMENTS` with `memes` or `no-memes` answers it. Only Create asks
   it (Free: its requirement; Recreate and Edit Mode keep a reference's own inserts).
3. **Higgsfield tools.** Load them (§1) and check that they are authenticated.
4. **Model — picked now, locked for the run.**
   1. `models_explore {action:"list", type:"video", limit:100}`, then collect the returned ids.
   2. `T model-menu --mode <analyze|edit> --live-ids "<id,id,…>"`. Edit Mode and **Recreate** use
      `--mode edit`, since their fit is the model's edit capability; **Free** uses `--mode edit` when the requirement says a reference is
      to be edited and `--mode analyze` otherwise; **Create** uses
      `--mode analyze`.
      - It prints one numbered table of **every available video model**, with ★ Seedance 2.5 and
        ★ Wan 3.0 Prime pinned at the top and the rest in `index.json → menu.order`.
      - Live models without a guide are appended.
      - The columns show what each can do and its fit for the mode. The Edit column reads: ✓ edits
        video, ↔ motion transfer, ≈ recreates, ✗ frames only.
   3. **Show the whole table in chat, verbatim, every row, however long.** Never shorten it to a
      top-N. The user wants to see all models.
   4. Ask with AskUserQuestion (header "Model"). **You choose the 4 options** from the table (the
      script offers no picks): the pinned models first (`pinned` in the JSON line), then the models
      that fit the mode: for Edit Mode and Recreate the video editors (✓), then motion transfer (↔),
      then recreation (≈); for Create the models that can analyze (the Analyze column). Label =
      model name; description = its "what it can do" and what the mode column says. "Other" = any
      number or name from the table; resolve numbers with the JSON `numbers` map (`unavailable`
      lists any model of the index that is not live).
      **With an own voiceover (step 2b):** the facts line and the option order of `voiceover.md` §2 step 2.
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
     this step: add characters, or keep the people as they are. **Free** asks the same only when the requirement says people are replaced.
     **Free with references** needs the references folder like Recreate and Create; **Free, requirement only** needs no references: the assets (and the optional examples) are its inputs.
     **QC fixes (every Analyze sub-mode: Recreate, Create, Free and Static; a choice, asked once the paths are validated, unless `$ARGUMENTS` has `qc-fixes ask|auto|off`).**
     Ask with AskUserQuestion (header "QC fixes"), "After a video's first generation, how should QC and its fixes run?" (three options, none recommended):
     - **"Ask me first"**: "From the first video on, I show you what QC found, what the fix generation would change and cost, and wait for your yes or no before spending credits on it."
     - **"QC agents fix on their own"**: "The QC agents regenerate a video with one diagnosed fix on their own, without asking, and ship the best take flagged if it still fails."
     - **"No QC, I review at the end"**: "No QC agent runs after a video's first generation: each video is generated once, assembled and delivered unchecked, with no
       regeneration. Once everything is delivered you tell me what to fix."
     Store it once the run exists (step 6). Edit Mode is not asked (the user reviews every attempt, X9-R).
   - **Edit Mode** needs the video file(s) or folder to edit, and offers the optional **examples
     folder** (as above). Per-edit assets are asked later, per operation (E3).
   - Paths may arrive quoted, space-separated, dragged into the terminal, or one per line. If an
     image arrives only as a chat attachment without a file path, ask for its path or folder:
     Higgsfield needs the original file.
   - Validate every path (Glob/ls) and report any that don't exist.
5b. **Audio.** Ask once, with AskUserQuestion (header "Audio ingest"), in the same message batch as the other start questions,
   whether the videos' audio is processed as text for this run (contract item 24). Both modes ask it (not Static: its audio is `whisper`, item 36). Never pick for the user and
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
5c. **Own voiceover: the voice, the language and the style (Create, when step 2b took a method; item 31).** After the QC-fixes and
   audio questions, `voiceover.md` §2 steps 3–5: load the ElevenLabs tools (§2 step 3), read the subscription, the models and the voices,
   print the whole voice list, then one AskUserQuestion call with header "Voice", header "Language" and header "Voice style" (§2 step 4),
   then resolve and verify the answers. Stored in step 6.
5d. **Effort** (both modes; item 33). After the start's question dialogs (QC fixes, audio, and step 5c's voice), in plain chat, never
   with AskUserQuestion (a dialog holds four options and hides the text printed above it): the question of `effort.md` §1, all five
   levels numbered, none recommended, as a message of its own and the last thing in the turn; then stop and wait for the reply.
   `$ARGUMENTS` with `effort low|medium|high|xhigh|max` answers it. Stored in step 6.
6. Create the run:
   - `T new-run --mode <analyze|edit> --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"]` (Free, requirement only: no `--source`);
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5);
   - store the audio choice (step 5b): `T state --run RUN set audio_ingest=whisper` or `audio_ingest=frames-only`;
   - store the effort level (step 5d): `T effort --run RUN --level <level>` plus the user's own numbers as its options (`effort.md` §1;
     `T new-run` leaves it empty, and `T prep-all` stops until it is stored);
   - every Analyze sub-mode: store the QC-fixes choice (`T state --run RUN set qc_fixes=ask|auto|off`);
   - Create: store the voiceover choice (steps 2b, 5c) with the store line of `voiceover.md` §1 (`T state --run RUN set voiceover.enabled=true
     voiceover.method=native|lipsync|overlay …`); "No, the model's own audio": `T state --run RUN set voiceover.enabled=false`;
   - Create: store the memes choice (step 2c): `T state --run RUN set memes=include` or `memes=none`;
   - Static: `T state --run RUN set analyze_submode=static static_images=api|prompts audio_ingest=whisper` (no model is stored; item 36);
   - Free: store `T state --run RUN set analyze_submode=free free_references=yes|no` and write the requirement, verbatim, to `RUN/00-inventory/requirement.md`
     (first line `# Requirement (the user's words)`, then the text; a file the user named is copied, a PDF through `T doc-text`);
   - start Loupe (not in Static: no Loupe call there, item 36): `T loupe ensure` (it starts the web app detached when it is down; the JSON line has `library_size`, the number of QC samples the keeper
     is fed from, and `keeper.state`: the keeper is booted or brought up to date there, so the first consult finds it current (`busy`: another keeper call held
     it, and the first consult brings it up to date; an empty library has no keeper, `keeper: null`); `keeper.understanding` says how many
     samples it holds from their pictures, and `keeper.reading_note` appears when new or changed samples are being read in the background: nothing to do, Loupe
     tells the keeper when they are done), then `T state --run RUN set loupe=up`, or `loupe=down` when it exits 1 (tell the user in one line that
     `python ~/.claude/loupe/loupe.py serve` starts it by hand; the run goes on, QC without samples, flags wait in Loupe's outbox);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`); not in Static (no Higgsfield).

## Rules this phase owns (contract items 4, 11, 17, 24, 27, 31, 32, 33)

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
17. **Analyze Mode has three sub-modes, chosen at the start (§2.2) and never mixed:**
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
    - **Free.** The user's own requirement, written at the start, decides what the videos achieve and how: how many, what happens,
      the product and its use, references edited or re-made or only studied, length, text, sound. With references, the analysis
      (A1–A5) runs first and the plan may follow, edit or avoid what they do; without references, the plan comes from the requirement
      and the assets. The pipeline keeps the hard rules, the locked model's own prompting, the plan discipline, the QC stack, Loupe's
      samples and misses (the judge's prompt template at X4b, the consult at X9, the flags), the CapCut assembly and the deliverables; it asks once to confirm
      its reading of the plan (A6f, `awl-free-plan`), then nothing. Every video carries its own kind, `recreate` or `create`
      (`state.json → videos_kind`), and follows that kind's branch in every per-video step.
    - In every sub-mode, every video ends as a CapCut project (item 16), produced by its own agent
      (item 2).

27. **QC fixes (every Analyze sub-mode: Recreate, Create and Free).** The user chooses at the start; the choice is stored in `state.json → qc_fixes` (a run without it is `auto`):
    - **`ask`**: when QC finds issues or anomalies in a generated video, from the first video on, and only a new generation can fix them, the fix is not generated until the user answers yes:
      the production agent prepares the corrected request and stops with a proposal, and the main session asks (`awl-analyze-produce`);
    - **`auto`**: the QC agents correct on their own, without asking: one diagnosed regeneration per clip, then the best take ships flagged;
    - **`off`**: no QC agent after a video's first generation at all: no QC check, no consult, no regeneration; each video is generated once, assembled
      and delivered unchecked, and the user says what to fix after everything is delivered (the wrap-up's feedback question, item 22).
    Never asked: local post-fixes, CapCut fixes, the retry of a job that failed with no output, and anything in Edit Mode (every attempt is reviewed, X9-R).

Item 17's "§3 R-steps" are step A6r (`awl-recreate-plan`).

24. **Audio ingest is the user's choice, once per run (step 5b).** `state.json → audio_ingest` is `whisper` (speech-to-text of every
    video's audio, written once per video as `10-media/<V>/transcript.json` and `transcript.txt` by `T prep-all`) or `frames-only` (no
    speech-to-text, no transcript file; every speech field of every card, plan and brief says `audio not ingested`, never `no speech`
    or `silent`). No step, script or agent picks a default: `T prep-all` and `T prep-video` refuse without it and `T captions
    --from-speech` refuses in a frames-only run. The choice is about speech-to-text and what is derived from it; whatever needs the
    audio file itself (the original audio restored under the picture, loudness and silences, `T audio-profile`, `T sync-check`)
    runs in both modes.

31. **Own voiceover (ElevenLabs): Create's choice at the start (steps 2b, 5c):** the method (native, lipsync or overlay), then the voice,
    the language and any accent, dialect or delivery preference. `state.json → voiceover` (`voiceover.md` §1) is the only source; a run
    without the key has none. Free takes it only from its requirement; Recreate and Edit Mode keep their original audio (item 19).

32. **Memes in Create: the user's choice (step 2c).** `include`: memes and other cut-in clips as the style calls for (item 16);
    `none`: pure generation, no insert or meme sound of any kind, a reference's meme beat played by the
    generated scene, never by a generated copy. It wins over the house approach. `state.json → memes`; a Create run without the key
    includes them.
33. **Effort level: the user's choice (step 5d), from all five levels.** It sets how densely the references are sampled, the agents
    at once and the pilot threshold (`state.json → effort`; `T prep-all` and the produce phase read it); coverage and the floors never
    change, and QC and Loupe are never part of it (`reference/effort.md`). Asked in plain chat, the five levels numbered (a question
    dialog holds four). A new run's level is empty until stored, and `T prep-all` and `T effort` stop on it; a run made before item 33
    has no key, keeps its old rates and is never asked.

## Never (this phase)

- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never shorten the model menu. Every available model is always shown, with the pinned ones on top.
- Never offer, suggest or ask the own voiceover outside Create's questions (steps 2b, 5c), never mark one of its options as recommended,
  never shorten the voice list, and never pick the method, the voice, the language or the preference for the user.
- Never decide the audio choice for the user, never mark one of its options as recommended, and never write `no speech` for a run that did not ingest audio.
- Never pick the memes choice for the user or mark one of its options as recommended (item 32).
- Never pick the effort level for the user, mark one as recommended, offer fewer than its five levels, or set a rate below its floor
  (item 33).
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.

## Hand-off

- Analyze Mode: `T state --run RUN set stage=started next_skill=awl-analyze-prepare`, then invoke Skill `awl-analyze-prepare`.
- Edit Mode: `T state --run RUN set stage=started next_skill=awl-edit`, then invoke Skill `awl-edit`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
