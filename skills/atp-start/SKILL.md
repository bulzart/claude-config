---
name: atp-start
description: /analyze-then-pick phase 1: mode, Analyze sub-mode, the locked video model, inputs, create the run. Internal to that command.
user-invocable: false
---

# atp-start — Start: mode, sub-mode, model, inputs, run

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase 1 of `/analyze-then-pick`. The router (the command) sent you here and passes the command's arguments (`$ARGUMENTS` below) as this skill's args. Nothing else needs to be loaded for this phase.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- *(nothing from the library: `T model-menu` and `T model-entry --id` print what is needed)*

## 1. Paths and tools

| name | value |
|---|---|
| `ATP` | `C:/Users/Glaresquare1/.claude/analyze-then-pick` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `ATP/config.json`) |
| `T` | `"$PY" "$ATP/scripts/atp.py"`. Every call prints one JSON object on its last line; run through Bash |
| Model index | `ATP/models/index.json` (model id → guide, capabilities, 9:16/720p params). **Never Read it whole** (40 KB): `T model-menu` builds the menu, `T model-entry --id <id>` prints one model's entry and its guide path |
| Model guides | `ATP/models/<guide>.md` is an index; the sections are in `ATP/models/<guide>/`. Which sections each step reads: `atp-model-guide` |
| Higgsfield guide | `ATP/higgsfield/higgsfield-mcp.md` (index) and `ATP/higgsfield/higgsfield-mcp/` (sections) |
| Flag record | `ATP/caught_flags.html` (item 23): `T caught-flag add, set, reconcile, open` and `T ledger set --flagged`; written in X7 (`atp-submit`), reconciled in A9b and §6, never read during a run |
| References | `ATP/reference/<name>/` section files (index: `ATP/reference/<name>.md`): `analysis-protocol`, `generation-system`, `anomaly-catalog`, `creative-direction`, `brand-guardrails`, `text-and-format`, `assets-and-substitution`, `capcut-assembly`, `production-agents`. Each phase skill lists the sections it needs under "Read now" |
| CapCut | `capcut` MCP (drafts store and template in `ATP/config.json → capcut`) + capcut-cli `capcut` on PATH. Tool list and steps: `reference/capcut-assembly/` (`atp-postprocess`) |
| Run folder | created by `T new-run` under `ATP/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json) |

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
6. Create the run:
   - `T new-run --mode <analyze|edit> --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"]`;
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`).

## Rules this phase owns (contract items 4, 11, 17)

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

Item 17's "§3 R-steps" are step A6r (`atp-recreate-plan`).

## Never (this phase)

- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never shorten the model menu. Every available model is always shown, with the pinned ones on top.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.

## Hand-off

- Analyze Mode: `T state --run RUN set stage=started next_skill=atp-analyze-prepare`, then invoke Skill `atp-analyze-prepare`.
- Edit Mode: `T state --run RUN set stage=started next_skill=atp-edit`, then invoke Skill `atp-edit`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
