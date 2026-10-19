---
name: atg-start
description: /analyze-then-generate phase 1: mode, Analyze sub-mode (Recreate, Create, Viral-Browser), the locked video model, inputs and brief, create the run. Internal to that command.
user-invocable: false
---

# atg-start — Start: mode, sub-mode, model, inputs, run

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase 1 of `/analyze-then-generate`. The router (the command) sent you here and passes the command's arguments (`$ARGUMENTS` below) as this skill's args. Nothing else needs to be loaded for this phase.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- *(nothing from the library: `T model-menu` and `T model-entry --id` print what is needed)*

## 1. Paths and tools

| name | value |
|---|---|
| `ATG` | `C:/Users/Glaresquare1/.claude/analyze-then-generate` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `ATG/config.json`) |
| `T` | `"$PY" "$ATG/scripts/atg.py"`. Every call prints one JSON object on its last line (numbers, tables and records, never a verdict: the agent decides); run through Bash |
| Model index | `ATG/models/index.json` (model id → guide, capabilities, 9:16/720p params). **Never Read it whole** (40 KB): `T model-menu` builds the menu, `T model-entry --id <id>` prints one model's entry and its guide path |
| Model guides | `ATG/models/<guide>.md` is an index; the sections are in `ATG/models/<guide>/`. Which sections each step reads: `atg-model-guide` |
| Higgsfield guide | `ATG/higgsfield/higgsfield-mcp.md` (index) and `ATG/higgsfield/higgsfield-mcp/` (sections) |
| Preprocessing | `ATG/pipeline/preprocessing.md` (the recorded local pipeline, FFmpeg-first, and the sampling policy; `atg-analyze-prepare` reads it only when a prep step reports an error) |
| Flag record | Loupe, `http://127.0.0.1:8787` (item 23), started by `T loupe ensure` at run creation and recorded in `state.json → loupe` (`up` or `down`; missing = up): `T caught-flag add, set, reconcile, open` and `T ledger set --flagged`; written in X7 (`atg-submit`), reconciled in A9b and §6, never read during a run. The sample library is read only by `T qc-consult` (`atg-qc`) and, once per video at its first request, `T plan-hints` (`atg-write-request`) |
| References | `ATG/reference/<name>/` section files (index: `ATG/reference/<name>.md`): `analysis-protocol`, `generation-system`, `anomaly-catalog`, `creative-direction`, `brand-guardrails`, `text-and-format`, `assets-and-substitution`, `capcut-assembly`, `production-agents`, `viral-browser`. Each phase skill lists the sections it needs under "Read now" |
| Viral-Browser | `ATG/reference/viral-browser/` (items 24–26; skills `atg-vb-*`); config `ATG/config.json → viral_browser`; toolkit `T viral-stats`, `T niches`, `T candidates`, `T evidence`, `T econ`, `T landed`, `T spec`, `T photo`, `T pdf-text` |
| CapCut | `capcut` MCP (drafts store and template in `ATG/config.json → capcut`) + capcut-cli `capcut` on PATH. Tool list and steps: `reference/capcut-assembly/` (`atg-postprocess`) |
| Run folder | created by `T new-run` under `ATG/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json; Viral-Browser adds `30-research/` for the candidates, evidence, dossiers and ranking, and `deliverables/` for the report, the three product files and their reference packs) |

### Higgsfield tools

**Higgsfield tools** are deferred. Viral-Browser needs none.
- Load them before first use:
  `ToolSearch "select:mcp__higgsfield__models_explore,mcp__higgsfield__balance,mcp__higgsfield__list_workspaces,mcp__higgsfield__create_project,mcp__higgsfield__media_upload,mcp__higgsfield__media_confirm,mcp__higgsfield__media_import_url,mcp__higgsfield__show_reference_elements,mcp__higgsfield__generate_image,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__show_generations,mcp__higgsfield__transactions,mcp__higgsfield__reframe"`.
- If they are missing or only `authenticate` tools exist, ask the user to run `/mcp` → higgsfield →
  Authenticate, then continue.
- Never call widget-only tools (`media_upload_widget`, `show_marketing_studio_v2`).

## 2. Start (steps 2–6; the router already handled `resume` and reported-video feedback)

2. **Mode.** If `$ARGUMENTS` begins with `analyze`, `edit` or `viral-browser` (the last means Analyze
   Mode, Viral-Browser), use it. Otherwise ask with AskUserQuestion (header "Mode"):
   - **Analyze Mode**: "Analyze a folder of references and instructions, learn what makes them work,
     then create new videos for this client (Recreate, Create) or find the next products to sell
     (Viral-Browser)."
   - **Edit Mode**: "Edit supplied videos one by one: replace, remove, insert, alter, restyle or
     recreate elements."

   **Analyze Mode → sub-mode.** If `$ARGUMENTS` names `recreate`, `create` or `viral-browser`, use
   it. Otherwise ask with AskUserQuestion (header "Analyze as"):
   - **Recreate**: "Analyze the references, then recreate N of them with your product and
     characters: same scenario, faces and products swapped or blended. Autonomous after its planning questions."
   - **Create**: "Analyze the references like a viral-growth team (why they spread: style, hooks,
     engagement, audience mentality, trends), then create new virality-backed videos for your product,
     blending what was learned with your assets, in suggested style groups (one style or a mix) or the
     agents' own blends. No reference video is used as input."
   - **Viral-Browser**: "Use the references only as a source of ideas: learn why they spread,
     research the market, and bring back the next 3 products to sell with the same approach.
     Nothing is generated; no assets needed."
   Store it with `T state --run RUN set analyze_submode=recreate|create` once the run exists
   (`T new-run --submode` already does).
   **Viral-Browser skips steps 3–6** (no Higgsfield tools, no model, no balance, no CapCut): invoke Skill
   `atg-vb-cards` now with `$ARGUMENTS` as its args. It asks the references folder, the optional extras and the
   brief, creates the run and does the first steps. Nothing below applies to it, except when the user later says yes to *continue to Create*
   (`viral-browser.md` §11.4): that run already exists and has `analyze_submode=create`; it re-enters this skill at steps 3–5 for the new inputs only,
   step 6 does not run again, and the model is stored with `T state --run RUN set model=<id> model_locked=true`.
3. **Higgsfield tools.** Load them (§1) and check that they are authenticated.
4. **Model — picked now, locked for the run.**
   1. `models_explore {action:"list", type:"video", limit:100}`, then collect the returned ids.
   2. `T model-menu --mode <analyze|edit> --live-ids "<id,id,…>"`. Edit Mode and **Recreate** use
      `--mode edit`, since their fit is the model's edit capability; **Create** uses
      `--mode analyze`.
      - It prints one numbered table of **every available video model**, with ★ Seedance 2.5 and
        ★ Wan 3.0 Prime pinned at the top and the rest in `index.json → menu.order`.
      - Live models without a guide are appended.
      - The columns show what each model can do and what it offers for each mode (an Analyze and an
        Edit column); the order is the pins, then `menu.order`, not a ranking. The Edit column reads: ✓
        edits video, ↔ motion transfer, ≈ recreates, ✗ frames only.
   3. **Show the whole table in chat, verbatim, every row, however long.** Never shorten it to a
      top-N. The user wants to see all models.
   4. Ask with AskUserQuestion (header "Model"). **You choose the 4 options** from the table (the
      script offers no picks): the pinned models first (`pinned` in the JSON line), then the models
      that fit the mode: for Edit Mode and Recreate the video editors (✓), then motion transfer (↔),
      then recreation (≈); for Create the models that can analyze (the Analyze column). Label =
      model name; description = its "what it can do" and what the mode column says. "Other" = any
      number or name from the table; resolve numbers with the JSON `numbers` map (`unavailable`
      lists any model of the index that is not live).
   5. Store it: after the run exists (step 6), `T state --run RUN set model=<id> model_locked=true`.
      Print its `index.json` entry now with `T model-entry --id <id>` (never Read `index.json` whole: it is 40 KB; capabilities, durations, 9:16/720p params, and
      `continuation`: the maximum per generation and how clips join), but not yet its guide.
   6. If the model's fit for the mode is limited (e.g. Edit Mode with "✗ frames only"), say once how
      the run will work with it, e.g. "edits will be recreated from clean frames of each source
      video with your assets". Then continue. Do not suggest another model.
5. **Inputs.** Take what `$ARGUMENTS` already gives (`analyze <references-folder> assets <paths…>
   [examples <folder>] [qc-fixes ask|auto]` / `edit <video paths…> [examples <folder>]`) and ask in plain chat,
   in **one** message, only for what is missing. Then stop and wait.
   - **Analyze Mode, Recreate and Create** need two things, and offer a third:
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
     needs none. If the user asks what a well-prepared asset set looks like, share the table in `assets-and-substitution.md` §1
     (`ATG/reference/assets-and-substitution/010_1_where-client-assets-come-from-on.md`), and only then.
     **Recreate** also needs the **characters** who replace the people in the references (face
     close-up + full body each). If none are supplied and the references show people, ask once at
     this step: add characters, or keep the people as they are.
     **QC fixes (Recreate and Create; a choice, asked once the paths are validated, unless `$ARGUMENTS` has `qc-fixes ask|auto`).**
     Ask with AskUserQuestion (header "QC fixes"), "If QC finds issues or anomalies in a generated video, how should the fix generation be decided?":
     - **"Ask me first"**: "From the first video on, I show you what QC found, what the fix generation would change and cost, and wait for your yes or no before spending credits on it."
     - **"QC agents fix on their own"**: "The QC agents regenerate a video with one diagnosed fix on their own, without asking, and ship the best take flagged if it still fails."
     Store it once the run exists (step 6). Edit Mode is not asked (the user reviews every attempt, X9-R); Viral-Browser generates nothing.
   - **Viral-Browser** is handled by `atg-vb-cards`, which asks for its own inputs and the brief (market, price range, how the user sells, tools) and creates its run: invoke it as soon as the sub-mode is known (step 2).
   - **Edit Mode** needs the video file(s) or folder to edit, and offers the optional **examples
     folder** (as above). Per-edit assets are asked later, per operation (E3).
   - Paths may arrive quoted, space-separated, dragged into the terminal, or one per line. If an
     image arrives only as a chat attachment without a file path, ask for its path or folder:
     Higgsfield needs the original file.
   - Validate every path (Glob/ls) and report any that don't exist.
6. Create the run:
   - `T new-run --mode <analyze|edit> [--submode recreate|create] --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"]`;
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5);
   - Recreate and Create: store the QC-fixes choice (`T state --run RUN set qc_fixes=ask|auto`);
   - Edit, Recreate and Create (Viral-Browser generates nothing): start Loupe with `T loupe ensure` (it starts the web app detached when it is
     down; the JSON line has `library_size`, the number of QC samples the keeper
     is fed from, and `keeper.state`: the keeper is booted or brought up to date there, so the first consult finds it current), then `T state --run RUN set loupe=up`, or
     `loupe=down` when it exits 1 (tell the user in one line that `python ~/.claude/loupe/loupe.py serve` starts it by hand; the run goes on,
     QC without samples, flags wait in Loupe's outbox);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`).

## Rules this phase owns (contract items 4, 11, 17, 27)

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
   - Viral-Browser picks no model (nothing is generated).
11. **Client assets come only from paths the user gives.**
    - **Analyze Mode:** the user supplies all asset files and/or folders **once, at the start**. The
      command then understands them and uses them autonomously for every video. Viral-Browser asks
      for none.
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
      - The videos are **blends**, not copies of the references' samples: the agents understand the
        references (why they work) and the product (from the supplied assets, the insight sheet), and
        design the most engaging video from both; families are evidence and ingredients, never a
        menu or a template.
      - The references are **mined like Viral-Browser's**: why they spread
        (style, engagement and attention approach, hooks, how the product is used, the audience and
        its mentality, the mass-thinking patterns, length, trends), and every video is
        **virality-backed**: a mined mechanism blended with a truth of the client's own product (the
        assets folder), never a copy of a reference and never fixated on the references' product type.
      - The product is used in the new scenes.
      - **No reference video, frame or clip is ever an input** to a generation; nothing is edited.
    - **Viral-Browser.** The references are a **source of ideas**: the agents mine them for why they
      spread (hooks, style, approach, subject, how the product is used, engagement, audience and its
      mentality, length), then research the market and bring back the **next three products to sell**
      with the same approach, each with a viral blueprint. Nothing is generated or edited (items
      24–26; skills `atg-vb-*`).
    - In Recreate and Create, every video ends as a CapCut project (item 16), produced by its own
      agent (item 2).

27. **QC fixes (Recreate and Create).** The user chooses at the start; the choice is stored in `state.json → qc_fixes` (a run without it is `auto`):
    - **`ask`**: when QC finds issues or anomalies in a generated video, from the first video on, and only a new generation can fix them, the fix is not generated until the user answers yes:
      the production agent prepares the corrected request and stops with a proposal, and the main session asks (`atg-analyze-produce`);
    - **`auto`**: the QC agents correct on their own, without asking: one diagnosed regeneration per clip, then the best take ships flagged.
    Never asked: local post-fixes, CapCut fixes, the retry of a job that failed with no output, and anything in Edit Mode (every attempt is reviewed, X9-R).

Item 17's "§3 R-steps" are step A6r (`atg-recreate-plan`).

## Never (this phase)

- Never re-ask for, switch, or suggest switching the model after it was picked at the start. Only an
  explicit user request changes it.
- Never shorten the model menu. Every available model is always shown, with the pinned ones on top.
- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Viral-Browser: never pick a model, call a Higgsfield generation tool, ask for client assets or touch the references folder; never invent an exclusion (the user's exclusions come from the user alone).

## Hand-off

- Analyze Mode, Recreate or Create: `T state --run RUN set stage=started next_skill=atg-analyze-prepare`, then invoke Skill `atg-analyze-prepare`.
- Analyze Mode, Viral-Browser: already handed to `atg-vb-cards` at step 2.
- Edit Mode: `T state --run RUN set stage=started next_skill=atg-edit`, then invoke Skill `atg-edit`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
