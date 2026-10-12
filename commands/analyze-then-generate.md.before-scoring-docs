---
description: Analyze a folder of reference material (or take videos to edit), learn what makes it work, then either generate new vertical 9:16 720p videos through Higgsfield MCP (Recreate, virality-backed Create, Edit) or find the next three products to sell with the same viral approach (Viral-Browser, which asks the market and price range and generates nothing).
argument-hint: "analyze <references-folder> assets <asset files/folders…> [examples <folder>] | edit <video files/folders…> [examples <folder>] | viral-browser <references-folder> [baseline <folder>] [market us|eu|global] [price <min>-<max> <currency>] [depth quick|standard|deep] | resume [run-dir]"
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

It contains everything `/analyze-then-pick` does (Edit Mode; Analyze Mode with Recreate and Create) and
adds a third Analyze sub-mode, **Viral-Browser** (§3, steps V1–V9; `ATG/reference/viral-browser.md`): the
references become a **source of ideas**, nothing is generated, and the run returns the **next three
products to sell** with the same viral approach, each with a blueprint. Contract items 3–6, 12–16 and 19
concern video generation and apply to Edit Mode, Recreate and Create. Items 23–25 govern Viral-Browser.

**Scripts gather, the agent decides** (the user's rule, 2026-10-12; it holds in every mode and for every
`T` command). The scripts measure, extract, record, tabulate and calculate. They never hand out a
verdict, status, flag or label derived from content, never apply a threshold that refuses, caps or
changes an answer, never rank, pick or break a tie, and never compare texts or count words to decide
anything. They refuse only a bad argument, a missing file or tool, a damaged ledger, an unsafe web
address or a failed ffmpeg run (the mechanical exceptions: file locks, the submission ledger's
fingerprint bookkeeping, the public-address guard of the page reader, CapCut's "close it first" and the
locked house preset). **You**, the agent that runs the pipeline, read the numbers and tables they return,
decide under the mode's specification, and record every decision with its reason (`--by` / `--reason`, the
caught-error ledger, the bias log in `30-research/ranking.md`, `ledger set --status superseded --note`).
Numbers that older versions of the toolkit enforced (the 0.10 s sync tolerance, the 15 % / 25 % size
bands, the 12 % crop loss, the pool shares, the rating floors, the evidence caps) are **rules of thumb**:
apply them with judgement, depart from them when the evidence says so, and write down what you applied,
what you set aside and why. Independent checks stay fresh AI agents (niche audit, blind scoring, red
team, reference packs), never script gates.

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
   - **Viral-Browser agents** (no production agents, nothing is generated): the analysis agents
     above for the viral cards (≤ 2, disjoint lists); one fresh **niche-audit agent** (before the
     shortlist); up to `viral_browser.max_research_agents` (3) **research agents** (web only,
     background, disjoint candidate lists), one fresh, blind **scoring agent** and one
     **red-team agent**; and, after the picks are recorded, up to 3 **reference-pack agents** (web
     only, one per pick). None calls Higgsfield or CapCut (`reference/viral-browser.md` §5, §7,
     §8.2, §9.1, §13).
   - Agents never overlap, never ask questions (they report blockers and stop), and never spawn
     agents. Edit Mode uses no production agents.
3. **Generation lanes.** Every video is a lane with **one job in flight at a time**:
   plan → preflight → brief → submit → wait → download → post-process → QC.
   - The ledger records every submission and reports what is already in flight; the agents keep to at
     most `production.max_parallel_jobs` (5) jobs in flight per run, across the production agents
     (`T ledger begin` reports the open submissions against that cap; whether to submit is the
     agent's decision, §5 X7).
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
     hooks, captions) afterwards as **CapCut text layers** at the reference text's height and
     timing, always **horizontally centred** (posX 0; when centred text would cover the product, a
     face or an insert, it moves up or down, never sideways; caught error CE-010)
     (`reference/capcut-assembly.md`).
     - The wording keeps the reference's role and format.
     - A generic meme line may stay as written; source-specific wording is rewritten.
     - Usernames, handles, watermarks and source brands are never copied.
     - A reference's short keyword or tag that is its hook, or any text the user keeps, is placed word
       for word at the same height (CE-027); a guardrail rewrite is minimal and keeps the reference's
       subject and meaning (CE-022).
     - A source overlay that carries the joke's context (a notification, a message, a banner) is the
       original element reused as a picture overlay, not re-typed text (CE-017, CE-023).
     - No text layer contains an emoji (the user's rule, strict).
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
      goes through the ledger (`T ledger begin` before, `T ledger set` after; §5 X7: the ledger
      records and reports, the agent decides). There is at most **one job in flight per video lane**, at
      most 5 per run, one generation call per turn per agent, and never parallel calls inside a lane.
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
      - it is there from the first frame and stays on one persistent spot, on a fixed natural
        surface the source frame shows, moved only by a visible, logical action (picked up to
        use, then set down; a parked car driven away; a cut alone is not a motive);
      - it is lit and rendered like the rest of the scene, so it never reads as an edit.
    - **Use only when the action invites it.** The product is used the way it really is (sipped,
      chewed, applied, driven) only when the action has room for it; the story never changes to
      fit the product.
    - **Physically and logically correct for that object.** Its size, weight, states and motion
      follow its own physics (`generation-system.md` §3, §4, §5b, §5d;
      `reference/anomaly-catalog.md`): its counts persist, it is used through its real opening
      after the step that readies it, and it is still there, unchanged, after every exit,
      occlusion and cut. These rules are general; the examples only illustrate them.
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
        menu or a template (`creative-direction.md` §5.0b).
      - The references are **mined like Viral-Browser's** (`viral-browser.md` §14): why they spread
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
      23–25; steps V1–V9).
    - In Recreate and Create, every video ends as a CapCut project (item 16), produced by its own
      agent (item 2).
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
19. **Source fidelity is pushed from the first attempt (Edit Mode and Analyze Mode Recreate).** The
    output is the source with only the planned operations changed: every other movement, action and
    detail stays exactly as it is. The original audio also goes back under the generated picture
    (X8), so every action happens at the same moment, at the same speed and in the same order as in
    the source: mouth movements on their words, contact on its impacts, steps on their footfalls, a
    pickup, sip or door on its sound. The **first** request is built for this, and QC only confirms
    it (`reference/generation-system.md` §5c):
    - the card holds the **source action script**: every beat in order, with who moves what and how
      (body, hands, head, gaze, face, mouth), the props and their contacts, the camera, the
      background action and the small details, each marked keep or change. Its **sync anchors** are
      the beats whose sound is in the original audio (§5c.1);
    - the request uses the most preserving input and parameters the locked model offers: the source
      as the edit input, then as the motion input, then as the video reference, then its own first
      and last frames. The guide's preserving mode is used, and the duration equals the source
      segment's (§5c.2);
    - the prompt carries the **fidelity lock** in the guide's wording: the change scoped with
      "only", the full keep-list, and exclusions against any added, skipped or reordered action.
      For models that rebuild the action (≈, ✗), the action script is also written out in order.
      The timing comes from the source video, never from timestamps in the prompt (§5c.3);
    - X4 checks the request against the action script before any credit is spent (§5c.4);
    - after the merge, `T sync-check` measures the timing and returns numbers, not a verdict (X8 step
      5); you read them and the sheet. A steady offset is fixed in post. Drift or a moved action is a
      regenerate reason in Recreate, or the first QC note in Edit Mode.
    Create is not affected: it makes new scenes, and its sound is built in CapCut on their own
    beats.

20. **The pipeline is also the creative team** (`reference/creative-direction.md`): a social-media
    and product-growth creative specialist, a mass-cognition engineer, a trend analyst, a creative
    director and a performance editor at once. Every run writes its goal, its audience model and
    its trend read; every Create video comes from at least five scored concept seeds and passes
    the sharpness gate, the copy test and the blend test (a Create video takes a reference's style,
    properties, approach, crafting and hook logic, never its subject, scene, joke, lines or ending,
    and blends them with the product's own truths: `creative-direction.md` §5.0, §5.0b); every
    Recreate pick is ranked for its creative potential; every brief says
    why the video will work; and QC judges the hook, the payoff and the share line as notes. The
    creative layer never overrides the hard rules (items 6, 14, 15, 18, 19 and the anomaly
    catalog); it decides which references, mechanisms and concepts win inside them. In
    Viral-Browser the team widens (item 23): an expert social-media growth strategist, a
    direct-response product-selling specialist, a mass-cognition ("masses approach") engineer, a
    trend analyst, a market and competitor researcher, a sourcing and compliance screener, a
    statistician and a red-team sceptic, working for the one outcome that the user is about to put
    money into a product. In Create the same persona block opens every analysis and ideation
    prompt, and the references are mined for why they spread before anything is written
    (`viral-browser.md` §14).
21. **Brand guardrails decide what may be picked and what must be edited**
    (`reference/brand-guardrails.md`). Documents among the supplied assets (and in the references
    folder) that state the client's rules (no gore, two cans per day max, no competitor brands on
    screen, no ambassador likeness, no health claims, required disclaimers, …) are extracted into
    `30-assets/guardrails.md`, one quoted rule per line with its kind and default operation, plus
    the competitor, people, limit, wording and presentation lists they imply. Every reference gets
    a **guardrail audit** on its card: each hit located and classified **core** (the hook, turn,
    payoff, subject or premise depends on it; it is spoken in audio that returns; a hand or the
    action touches it; the edit would change what the video is about) or **peripheral** (set
    dressing, an untouched unit beyond the limit, a brand mark on an object that stays, a person
    who is swapped anyway, a caption line). Verdict: pick-clean, pick-and-edit (count reduced to
    the limit, competitor marks **removed, never blurred**, ambassador faces swapped without
    exception, captions rewritten, props removed) or dismiss (any core hit, with the rule). In
    Recreate the audit is the first filter of the ranking; in Create the rules are plan
    invariants; in Edit Mode the hits and the operations they require are shown and the user
    decides. The user's run instructions outrank the guardrails; the guardrails outrank the house
    approach and the defaults; they never relax a hard rule; none is invented. **The pipeline has
    no content rules of its own:** without a guardrail document only the copyright and ownership
    floor (`generation-system.md` §9b rows 1–6) and the generation service's blocks apply;
    alcohol, weapons, gore, profanity, meme faces, cameos and the like stay as the reference shows
    them, and nothing is blurred, softened or removed for taste.
22. **Caught errors: the pipeline learns from every video the user was not satisfied with**
    (`ATG/caught_errors.md`, written only with `T caught-error`). Whenever the user says a
    delivered video is wrong, in the run or in a later session, an entry is written first, with
    their words verbatim, the diagnosis in pipeline terms, the class (reference and section), the
    cause (prompt, reference, parameter, plan, qc-miss, model-limit), the fix and a general rule,
    **and the video's brief, the final prompt and the QC verdict** so the cause can be read
    against what was planned and asked (with `--run` and `--video` the command attaches the saved
    brief, the newest request's prompt and the plan path itself; `--brief`, `--prompt`, `--qc`
    take text or a file for a video from an earlier session); Edit Mode's "Needs changes" always
    writes one. **Two sources feed it:** the agents record, with `--source agent`, every error
    they caught that cost a regeneration or survived the retry (after fixing it, as always); and
    once every video is delivered, the wrap-up **asks the user for feedback**, and each problem
    they name is recorded with `--source user` and the video's details (CapCut project, final
    file, credits and the run's QC verdict, read from `result.json`). A user entry outranks an
    agent entry on the same point. Every run reads the ledger at the start (A1,
    E1) and writes the entries that apply (same mode, model, product family or class) to
    `20-analysis/caught-errors.md`; every plan names the entries it applies, every prompt carries
    their rules in the model's phrasing, and X9 checks each applied entry by id in the verdict.
    An entry whose rule is general, or that recurs, is promoted into the reference it belongs to
    and marked `promoted` with the pointer; the entry stays as the record. In Viral-Browser the
    same ledger records a pick the user rejects or a research error an agent caught
    (`--mode analyze-viral-browser`, `--video "P<n> <product>"`, causes `research`, `scoring`,
    `bias`, `evidence`), and its rules are promoted into `reference/viral-browser.md`.
23. **Viral-Browser: the references are a source of ideas, and the run generates nothing**
    (`reference/viral-browser.md`).
    - **No generation, no model, no assets.** No model is picked, no Higgsfield generation tool is
      called, no credits are spent, no CapCut project is written, no client assets are asked for,
      and the references folder is never modified (no `split-audio`).
    - **The brief is asked, not assumed:** the **market location** (US, EU, global or a country
      list) and the **price range** (the retail band and its currency) are always asked unless
      `$ARGUMENTS` gives them; the selling model and the research tools are asked with them; exclusions,
      constraints and how they sell (sales channel, ad platform, importer-of-record country, capital
      limit) are taken from the user's chat message (§2.5). Nothing about the user is inferred into an
      exclusion.
    - **The product layer and the mechanism layer are kept apart** in every card. The run learns
      *why* the videos spread (the hook, the visible proof, the emotion, the identity trigger, the
      price perception, the length, the engagement style), then looks for products that the same
      mechanism could carry, across the whole market.
    - **Three products, each data-backed:** researched in parallel by research agents, attacked by
      a red-team agent, rated on a rubric by a fresh blind agent, read by the main session against
      six gates of thumb (the reasoning written down), and delivered with a blueprint (the corpus's
      engagement style combined with what is trending now), the economics
      at the user's price, the compliance and logistics findings, a **reference pack** (the
      product's sourced specification: size, weight, material, texture, usage; and links to photos
      from several angles, none downloaded, `viral-browser.md` §9.1), a validation plan and the evidence that would
      change the call. "No product passes" is a valid result.
    - **Evidence discipline:** no number without a source and a retrieval date or a method; grades
      A–D; "unknown" never scores 3; the run is read-only on the world (no purchase, no login, no
      contact); the compliance, platform and IP screens are viability checks, never taste. The
      pipeline adds no exclusion of its own.
24. **Niche-bias control: the references' product niche must not decide the answer**
    (`viral-browser.md` §5). Candidates come from the mechanism, not from "more of what the videos
    show"; the references' own products are one source among five; niches are compared through a
    **vocabulary the agents build from the data** (`T niches`, a record with its history; no script
    lists, knows or compares any niche), never as free text, and a fresh **niche-audit agent** reads
    it for one niche under several names, synonyms that share no word included (no script flags
    look-alike names: the main session applies the agent's merges with a reason and records the
    audit); the long list should span at least six niches with none above 40 %, and the main session
    reads the **shortlist against the same rules of thumb before research starts**
    (`T candidates summary`, then `T candidates set --status researching --by main --reason "…"`;
    the numbers are guidance, and every exception is written in the bias log with its reason);
    research and rating are **origin-blind** (a fresh scoring agent rates, never this session); evidence rows carry a direction
    and an independence flag, and the scoring agent applies the rule of thumb that a criterion without
    a positive independent grade A/B row is rated 2 at most; the key criteria need a 3 when the main
    session selects; at most two picks should share a niche and none a product type; every pick has a
    red-team reading, and every pick from the dominant niche (a niche that is 40 % or more of the
    references' cards, read from `T viral-stats` by the main session) a written defence against the
    best outside-niche alternative, **before** the picks are recorded; the run reports whether the
    picks change when reference-derived evidence or the fit criterion is removed (the main session's
    own what-if: `T candidates table --exclude-criteria fit`). A data-backed product from the
    references' own niche stays eligible and may win: the evidence rules demand independent proof, not
    a quota. No script ranks, caps, gates or picks: the main session reads the tables, decides, and
    writes the decisions and their reasons in `30-research/ranking.md` (the picks, the runner-ups, why
    each other candidate is not a pick, the what-if and the bias log).
25. **Viral-Browser is autonomous after the brief:** the only questions are the brief (market,
    price range, selling model, research tools), the final feedback question, and the optional
    "continue to Create". Research blockers are reported, not asked. Continuing to Create is
    offered at the end and runs only on the user's yes (`viral-browser.md` §11.4); it then follows
    every Create rule, and none of Viral-Browser's output relaxes one.

## 1. Paths and tools

| name | value |
|---|---|
| `ATG` | `C:/Users/Glaresquare1/.claude/analyze-then-generate` (library root) |
| `PY` | `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (see `ATG/config.json`) |
| `T` | `"$PY" "$ATG/scripts/atg.py"`. Every call prints one JSON object on its last line (numbers, tables and records, never a verdict: the agent decides); run through Bash |
| Model index | `ATG/models/index.json` (model id → guide, capabilities, 9:16/720p params) |
| Higgsfield guide | `ATG/higgsfield/higgsfield-mcp.md` |
| Caught errors | `ATG/caught_errors.md` (item 22): `T caught-error add | list | set`; read at A1 / E1, applied in X1, X2, X9 |
| References | `ATG/reference/analysis-protocol.md`, `generation-system.md`, `anomaly-catalog.md`, `creative-direction.md`, `brand-guardrails.md`, `text-and-format.md`, `assets-and-substitution.md`, `capcut-assembly.md`, `production-agents.md`, `viral-browser.md`; `ATG/pipeline/preprocessing.md` |
| Viral-Browser | `ATG/reference/viral-browser.md` (item 23; steps V1–V9); config `ATG/config.json → viral_browser`; toolkit `T viral-stats`, `T niches`, `T candidates`, `T evidence`, `T econ`, `T spec`, `T photo` |
| CapCut | `capcut` MCP (drafts store and template in `ATG/config.json → capcut`) + capcut-cli `capcut` on PATH. Tool list and steps: `reference/capcut-assembly.md` |
| Run folder | created by `T new-run` under `ATG/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json; Viral-Browser adds `30-research/` for the candidates, evidence, dossiers and ranking, and `deliverables/` for the report, the three product files and their reference packs) |

**Higgsfield tools** are deferred.
- Load them before first use:
  `ToolSearch "select:mcp__higgsfield__models_explore,mcp__higgsfield__balance,mcp__higgsfield__list_workspaces,mcp__higgsfield__create_project,mcp__higgsfield__media_upload,mcp__higgsfield__media_confirm,mcp__higgsfield__media_import_url,mcp__higgsfield__show_reference_elements,mcp__higgsfield__generate_image,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__show_generations,mcp__higgsfield__transactions,mcp__higgsfield__reframe"`.
- If they are missing or only `authenticate` tools exist, ask the user to run `/mcp` → higgsfield →
  Authenticate, then continue.
- Never call widget-only tools (`media_upload_widget`, `show_marketing_studio_v2`).

## 2. Start

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done; for Viral-Browser the candidates,
     the evidence rows and the picks so far);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json`
     (Viral-Browser stores its brief under `brief.*`).
2. **Mode.** If `$ARGUMENTS` begins with `analyze`, `edit` or `viral-browser` (the last means Analyze
   Mode, Viral-Browser), use it. Otherwise ask with AskUserQuestion (header "Mode"):
   - **Analyze Mode**: "Analyze a folder of references and instructions, learn what makes them work,
     then create new videos for this client (Recreate, Create) or find the next products to sell
     (Viral-Browser)."
   - **Edit Mode**: "Edit supplied videos one by one: replace, remove, insert, alter, restyle or
     recreate elements."

   **Feedback first.** If `$ARGUMENTS` or the opening message reports a delivered video as wrong
   (it names a video, a CapCut project or a run and says what was not right), record it before
   anything else: `T caught-error add` with the user's words verbatim, the diagnosis, the class,
   the cause, the fix if known and the rule, plus the video's brief and prompt (item 22): find
   the run under `ATG/runs/` by the video's CapCut project name or date and pass `--run` and
   `--video` so they attach themselves; when the run cannot be found, ask the user once for the
   brief or the prompt they used, or record it with "not recorded" and say so. Then offer the fix
   (a re-edit or a regeneration of that video in its mode) in one line, and continue only if the
   user wants it. The same goes for a message that rejects a Viral-Browser pick: record it with
   `--mode analyze-viral-browser --video "P<n> <product>"` (V9; `viral-browser.md` §11.2), then offer
   the adjustment.
   **Analyze Mode → sub-mode.** If `$ARGUMENTS` names `recreate`, `create` or `viral-browser`, use
   it. Otherwise ask with AskUserQuestion (header "Analyze as"):
   - **Recreate**: "Analyze the references, then recreate N of them with your product and
     characters: same scenario, faces and products swapped or blended. Fully autonomous."
   - **Create**: "Analyze the references like a viral-growth team (why they spread: style, hooks,
     engagement, audience mentality, trends), then create new virality-backed videos for your product,
     blending what was learned with your assets, in suggested style groups (one style or a mix) or the
     agents' own blends. No reference video is used as input."
   - **Viral-Browser**: "Use the references only as a source of ideas: learn why they spread,
     research the market, and bring back the next 3 products to sell with the same approach.
     Nothing is generated; no assets needed."
   Store it with `T state --run RUN set analyze_submode=recreate|create|viral-browser` once the run
   exists (`T new-run --submode` already does).
   **Viral-Browser skips steps 3 and 4:** no Higgsfield tools, no model, no balance, no CapCut. Go
   to step 5.
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
      Read its `index.json` entry now (capabilities, durations, 9:16/720p params, and
      `continuation`: the maximum per generation and how clips join), but not yet its guide.
   6. If the model's fit for the mode is limited (e.g. Edit Mode with "✗ frames only"), say once how
      the run will work with it, e.g. "edits will be recreated from clean frames of each source
      video with your assets". Then continue. Do not suggest another model.
5. **Inputs.** Take what `$ARGUMENTS` already gives (`analyze <references-folder> assets <paths…>
   [examples <folder>]` / `edit <video paths…> [examples <folder>]` / `viral-browser
   <references-folder> [baseline <folder>] [market …] [price …] [depth …]`) and ask in plain chat,
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
     needs none.
     **Recreate** also needs the **characters** who replace the people in the references (face
     close-up + full body each). If none are supplied and the references show people, ask once at
     this step: add characters, or keep the people as they are.
   - **Viral-Browser** needs the references folder, offers three optional extras, and then asks the
     brief. In **one** plain-chat message:
     1. The **references folder** (videos are the primary content; a notes, links or metrics file
        in it is read: views, likes, comments, shares, saves, dates, links).
     2. *(Optional)* a **baseline folder**: comparable videos that did **not** spread (same niche
        and platform). It lets the run separate what the viral videos share from what all videos
        share (`viral-browser.md` §3.4).
     3. *(Optional)* **anything to exclude or respect**: categories you will not sell, regulated
        goods, size or weight limits, no batteries or liquids, a supplier or shipping limit, a
        product you already sell. Taken from the user only; never inferred.
     4. *(Optional)* **how you sell**: the sales channel(s) (own store, TikTok Shop, Amazon, …), the ad
        platform(s), the country of your selling company (the importer of record), the capital you
        can put into a first order and the shipping policy of the store (free to the customer / the
        customer pays a flat amount / free above a threshold). They decide the fee schedules, the
        restricted lists, the VAT and duty regime, the fulfilment cost in the cost basis and the MOQ
        capital figure (`T econ --moq` prints the capital at risk; you compare it with the limit);
        without them the defaults are an own store with paid social, the seller's own company as
        importer, an unknown capital limit and shipping free to the customer (the conservative
        reading, said in the cost basis).
     5. *(Optional)* `depth quick|standard|deep` (default standard) and `price` / `market` if not
        already in `$ARGUMENTS`.
     Say in the message: *"I will use the references only as ideas and generate nothing. I will
     ask four quick questions next: market, price range, how you sell, and whether I may use your
     Chrome for live pages."*
     Then, after the paths are validated, ask the **brief** with one AskUserQuestion call holding
     only the questions `$ARGUMENTS` did not answer (`viral-browser.md` §2):
     - header "Market": "Where will you sell?" **US** / **EU** (then ask which countries in the
       next chat message, or say "all, lead countries chosen by the data") / **Global** ("Other":
       UK or a country list).
     - header "Price": "What retail price range (in the market's currency: USD for the US, EUR
       for the EU; type another currency under Other)?" **Impulse: up to 25** / **Core: 25 to 60**
       / **Premium: 60 to 150** ("Other": any range and currency).
     - header "Sell model": **Owned inventory** (bulk order, your own warehouse) /
       **Dropshipping** / **Print-on-demand** / **Digital product**.
     - header "Tools": **Web search and fetch only** (Recommended) / **Web plus my Chrome**
       (read-only pages: trend charts, marketplace pages, ad libraries).
     Hold the answers, and store them right after step 6 creates the run: `T state --run RUN set
     brief.market=… brief.price_min=… brief.price_max=… brief.currency=… brief.model=…
     brief.tools=web|chrome brief.depth=… brief.exclusions='…' brief.channel='…' brief.importer_country='…'
     brief.capital_limit=… brief.shipping='…'`.
   - **Edit Mode** needs the video file(s) or folder to edit, and offers the optional **examples
     folder** (as above). Per-edit assets are asked later, per operation (E3).
   - Paths may arrive quoted, space-separated, dragged into the terminal, or one per line. If an
     image arrives only as a chat attachment without a file path, ask for its path or folder:
     Higgsfield needs the original file.
   - Validate every path (Glob/ls) and report any that don't exist.
6. Create the run:
   - `T new-run --mode <analyze|edit> [--submode recreate|create|viral-browser] --source "<refs folder | video paths…>" [--assets "<path>" "<path>" …] [--examples "<folder>"] [--baseline "<folder>"]`
     (Viral-Browser: `--mode analyze --submode viral-browser --source "<refs folder>" [--baseline "<folder>"]`;
     it adds `30-research/` and `deliverables/`);
   - keep `RUN` from the JSON;
   - store the locked model (step 4.5; not in Viral-Browser);
   - call `balance` and note the credits in `state.json` (`T state --run RUN set credits_start=<n>`;
     not in Viral-Browser, which spends none).

## 3. Analyze Mode

### A1. Inventory and preprocessing (deterministic, local)
- **Caught errors first** (item 22): `T caught-error list --digest` and read every entry (the
  compact view: product and assets, model and params, class, evidence, errors, rule, and the
  verified prompt change where one exists). A verified prompt change is reused in the locked
  model's phrasing; an unverified entry tells only what to avoid. Write
  `20-analysis/caught-errors.md`: the entries that apply to this run (same mode, the locked model,
  the client's product family, or a class any video may hit) with their rules, one line each, and
  which step applies each (plan, prompt, QC, ideation). Promoted entries are listed by their
  pointer; open ones in full.
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
  - The reference's own-content audio is restored onto the edited picture (A6r). Its transcript and sound
    profile are still read for context (below): the audio is analysed and never uploaded.
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
- **Audio context, every analysis mode** (`analysis-protocol.md` §2 item 4, §3): then run
  `T audio-context --run RUN --profile --second-pass`. It writes `20-analysis/audio-context.md` (and the
  `.json` beside it), one digest of what every reference says and how it sounds, as numbers and
  extractions and never as labels. Per video: the `status` of the transcription run (a fact about the
  run: ok = the transcriber returned words, no-speech = it returned none, no-audio, failed, missing,
  skipped), the language and its probability, the words and words per minute, the first word (any word,
  and the first word of probability 0.5 or more), the words below probability 0.5, the first sentence,
  every line with its times, the three-word phrases said twice or more (an extraction), and the sound
  numbers (`speech_share`, `non_speech_audible_share`, `harmonic_ratio_non_speech`, `tempo_bpm`,
  `beat_strength`, `spectral_flatness_median` (near 0 tonal, near 1 noise-like), `peak_frequency_hz_median`
  with `peak_frequency_steady_share` (near 1 = one steady tone, such as a beep), and the energy change from
  the first to the last third); `notes` state only facts about the run (missing, skipped, failed).
  `--profile` also measures each video's sound design (`audio-profile.json`); `--second-pass` transcribes
  every video in which no words were found once more without the voice filter, so that sung words are
  not dropped (shown in the digest and kept between runs; nothing prepared is changed; over pure music or a
  tone the transcriber can invent words, so read the second pass as a second look, not as proof of speech).
  - The scripts label nothing. You decide what the numbers mean: whether there is a music bed, whether
    the voice is on camera, a voice-over, sung, rapped or chanted (the transcriber cannot tell speech
    from lyrics), whether the sound is reusable whole, and what it does for the video. Every card agent
    judges the machine transcript (ASR: it mishears and can drop or invent words) against the picture and
    `timeline.md`.
  - Every analysis agent reads the digest before writing a card, and every card carries the **Audio context:**,
    **Said:** and **Words and sound together:** lines. In Create the speech is read for its craft, never for its lines.
    Sung, rapped or chanted speech is the card agent's judgement, recorded in the Facts key `voice_type`
    (on-camera / voice-over / sung / rap / chant / none / mixed …); `Said:` may be one compact structured
    line for a long pitch.
  - A video without a usable transcript (status failed, missing or skipped: `without_a_transcript` in the
    JSON) is prepared again before the cards: `T prep-all --run RUN --only <V> --redo [--whisper-model medium]`.
    When speech cannot be recovered, the card says `transcript unavailable: <why>`.
  - **Recreate:** context only. The audio never goes to Higgsfield: only the silent copy is uploaded, and the
    original audio is restored after the result is approved (A6r). What is said tells the plan which beats the
    restored audio must still fit.
  - After the cards are written, run `T audio-context --run RUN --check --cards`: a completeness check only (a
    transcript for every video; a card for every video, each with its `Audio context:` and `Said:` lines). It
    exits 1 and lists what is missing, and writes nothing unless `--out` is given; add what it lists.
- With examples: `T prep-all --run RUN --set examples --jobs 2` (into `10-media/E01…`, listed in
  `10-media/examples-index.md`).
- Pipeline details: `ATG/pipeline/preprocessing.md`.

### A2. Documents and instructions (authoritative)
- Read every document:
  - `10-media/docs/<D>.txt` for text and office files;
  - PDFs directly with Read (use `pages` for long ones);
  - spreadsheets as extracted text.
- The same goes for documents among the supplied assets (`30-assets/project/docs/`), e.g. dimensions,
  brand rules and usage notes.
- Quote the requirements they define. They override inferences.
- **Brand guardrails** (item 21; `ATG/reference/brand-guardrails.md` §1): extract every rule
  into `30-assets/guardrails.md` (`G<n> · quote [E] · source · kind · what it hits · default
  operation`), then the lists they imply: competitors (named, plus every brand in the client's
  category), excluded people, limits, wording and disclaimers, presentation rules. Conflicts
  between documents or with the user's instructions go to the user once, with both quotes.
  Without a guardrail document, write "none supplied" and apply `generation-system.md` §9b alone.

### A2b. Understand the supplied assets (autonomous — no questions by default)
- Load `ATG/reference/assets-and-substitution.md`.
- View `30-assets/project/assets-sheet-*.jpg` and any preview that needs a closer look. Read
  `asset-inventory.md` (the paths grouped by sub-folder, and `duplicate_of` for identical files; file
  names are not interpreted, so you confirm every role by looking at the asset), then build the
  **asset registry** (`30-assets/registry.md` and `state.json → assets`):
  - **Group into entities.** Each distinct product, object, character, interface, brand kit or
    environment is one entity, using sub-folders, names and what the images show. Several products,
    samples or characters are expected.
  - **Products and objects:** pick the canonical template (the cleanest, most complete geometry view,
    or the file the user named template/canonical). Mark other views and variants, and take real
    dimensions from any supplied spec. Find and link each **contents sample** to its variant: a
    liquid or texture photo, a pour, a glass of the drink, or a lifestyle shot that shows it. They
    are often among the supplied files without a label. A sample is never a separate product.
  - **Affordance sheet, per product or object** (`ATG/reference/anomaly-catalog.md` §1): its parts,
    openings, opening sequence, how it is used and held, the contact point, what it holds and how
    many, its states, real size, the orientation of its mark, and what it cannot do. Every plan,
    prompt and QC pass quotes it.
  - **Real dimensions, per product:** height, width or diameter and depth in cm, and the volume,
    from the supplied specs; when none exist, the category's standard size from the catalog's
    §2.7 table, marked [I]. Never read a size off the product's own photo. These numbers feed
    the size reckoning of every shot (X1).
  - **Product insights, per product** (`assets-and-substitution.md` §2 step 3b;
    `creative-direction.md` §5.0b) into `30-assets/product-insights.md`: what it is and what it does
    for someone, who and when, what reads on camera (colour, texture, motion, the sound it makes, the
    reveal), what it can honestly show and how fast, the proof and claims the documents allow,
    the emotion it carries, the objections and limits, the occasions, and **up to six product
    truths** a concept can be built on (as many as the supplied assets and documents support). From
    the supplied assets and documents only; a gap is "not supplied" and is never filled by
    invention. Create's ideation reads it beside the craft sheet (A4, A6).
  - **Characters:** one entry per distinct person, mascot or character, with its best face and full
    views.
  - **Other assets:** logos, palettes, UI screenshots, environments, audio. Supplied fonts are
    listed only: CapCut text always uses the house text style (contract item 6).
- Ask **one** consolidated question only if a genuinely consequential ambiguity cannot be resolved by
  looking (e.g. two different-looking items presented as the same product). Otherwise proceed.

### A3. Video analysis (as continuous sequences)
- **Create: virality mining** (`viral-browser.md` §14). Each card is also a **viral card** (§3.2), so a
  reference is read once: the product layer kept apart from the mechanism layer (the product layer
  is recorded and then discarded), the ranked drivers of spread (craft / product / creator / trend /
  paid / bait / timing) and attention-only versus commerce-proven, the one-sentence product-agnostic
  mechanism with its product dependence and transplant needs, the audience (awareness stage, the pain
  or desire) and its mentality (the mental shortcuts, the emotion at the hook, the middle and the
  payoff, what got them hooked), the engagement mechanics, commerce signals when a metrics file is
  supplied, and the one-line `Facts:` JSON (its `category` optional; `voice_type` and `shots_seen` as in
  V2). The agents open with the persona block (`viral-browser.md` §1). Recreate keeps the plain
  protocol card.
- Follow `ATG/reference/analysis-protocol.md` exactly. For each video:
  - read `video.md` and `timeline.md`;
  - view **every** storyboard sheet in order, reading the timeline beside it, and state in the card
    "sheets seen n of n" (a sheet that did not display is read again before the card is written);
  - densify with `T frames … --range a-b --fps 15 --sheet` around fast actions, cuts, interactions,
    gestures, product appearances and text appearances;
  - write `20-analysis/cards/<V>.md`, including (protocol §2.9–§2.11, §3):
    - its **client-entity fit**:
      - **swap**: its analog in the same form exists;
      - **contents**: the product's category sits in another vessel whose action matters;
      - **placement**: nothing analogous.
      For contents and placement, also record the placement opportunities: free or busy hands,
      nearby surfaces, and the light on them.
    - its **object use and counts** (protocol §2.8; `anomaly-catalog.md` §2): for every handled
      object, the part used, the preparation step, the contact point, the hand and the head angle;
      the count of every multiple over time; the path of every thrown, dropped or passing thing
      relative to the objects it passes (§2.14);
    - its **trend elements and cognitive triggers** (protocol §2.12; `creative-direction.md` §3–§4):
      the format name and caption grammar, the structural mechanism, the surface elements with
      their freshness, the emotion arc, the laugh mechanism, the share line;
    - its **transferable craft** (protocol §3; `creative-direction.md` §5.0), as kinds, not
      instances: style, properties, approach, crafting and why it works, kept apart from the
      subject lines (premise, setting, characters, actions, joke, lines, props, ending) that a
      Create video must not reuse;
    - its **guardrail audit** (protocol §2.13; `brand-guardrails.md` §3): every hit against
      `30-assets/guardrails.md` with its time, element, prominence and place (picture, caption,
      speech, insert, reflection), classified core or peripheral by the meaning test, and the
      verdict: pick-clean, pick-and-edit with the operations, or dismiss with the rule;
    - its **inserts**: memes or other clips that interrupt the reference, with their exact in and
      out on cut frames, video or still, and their sound;
    - its **overlay text**: wording, role, centre position, in and out times, and style. The OCR spans
      (`ocr.json`, `video.json`, `video.md`, `timeline.md`) carry numbers and spelling facts only: `text`,
      `first_t`, `last_t`, `hits`, `share_of_frames_scanned`, `y_rel`, `band`, `band_distinct_texts`,
      `band_frames`, `score_mean`, `chars`, `words`, `has_at_handle`, `has_hashtag`, `has_url_pattern`,
      and `bands[]` per row of the frame. No script says whether a text is a caption, a fixed overlay, a
      watermark, a handle, a label or noise: you decide that from the numbers and the storyboard;
    - its **audio context** (every mode; `analysis-protocol.md` §2 item 4): the `Audio context:`, `Said:` and
      `Words and sound together:` lines, from `20-analysis/audio-context.md` and the transcript (context only in Recreate);
    - its **sound design** (every mode; Create builds its sound layer from it):
      `T audio-profile --audio "<files_audio file>" --out 10-media/<V>/audio-profile.json --transcript 10-media/<V>/transcript.json --cuts 10-media/<V>/cuts.json`.
      It returns numbers only: the speech share and the audible non-speech share, the harmonic share
      outside speech, the tempo and beat strength, the spectral flatness (near 0 tonal, near 1
      noise-like), the strongest frequency and how steady it is (near 1 = one steady tone, such as a
      beep), the energy per second and from the first to the last third, and the hits (each with
      whether it lands on a cut). From those numbers, the transcript and the visuals, you decide
      whether there is a music bed, whether the sound is speech-free and so reusable whole, how its
      energy moves, and its role: dramatic, comic, suspense, hype or sound-effect-driven. The card
      records that judgement.
    Videos that have nothing to do with the client's product are kept and analysed like any other.
    Their mechanism is still useful, and the product is integrated into them later.
- Delegate to 1–2 agents only per §7 of the protocol, with disjoint video lists. Give them the
  one-line client-entity summary from the registry. In Create use the prompt of `viral-browser.md` §13.6
  (the persona block, the goal, the viral-card rules).
- Images and other files in the references folder are also **reference material**: other products,
  samples, thumbnails and executions. Analyse them as references and never treat them as client
  assets.
- **Examples** (contract item 18): one card per example, `20-analysis/examples/<E>.md` (protocol §9):
  product integration, continuation, blend, characters, text, structure, sound, what they avoid,
  and flaws not to copy. The same ≤2 agents take them in their lists.

### A4. Synthesis
Write, following the protocol §5–§6:
- `20-analysis/families.md`: dynamic content families with measured profiles;
- **Create:** `20-analysis/craft-sheet.md` (protocol §5 step 3b): per family, what is
  **collected** (style, properties, approach, crafting, why it works) and what is **left behind**
  (the subject). Ideation reads only the collected column, together with the mechanism map, the blend matrix and the product insight sheet
  (`30-assets/product-insights.md`, A2b; `creative-direction.md` §5.0b, §5.0c);
- **Create: the virality synthesis** (`viral-browser.md` §14.1–§14.5), from the cards, product-free:
  `T viral-stats --run RUN --no-niche` (the measured length, hook, pacing, speech, text, music and
  loop profile, in `20-analysis/corpus-profile.md`); `20-analysis/mechanism-map.md` (mechanisms M#,
  k of n, driver, strength, independence of the product, transplant needs, confounds, graded
  hypotheses); the hook, length and pacing ranges; the engagement style; the audience and mentality
  model with the mass-thinking patterns the material uses; `20-analysis/viral-essence.md`; the trend
  read with the Create trend pass (up to `analysis.create_trend_checks` dated searches: the
  references' formats, and the client's product niche and market); and the **blend matrix**
  `20-analysis/blend-matrix.md` (the mechanisms that pass the driver test, set against the product
  truths PT# and affordances of `30-assets/product-insights.md`, with an audience-fit judgement per cell). Only available cells reach ideation;
- in `20-analysis/project-profile.md`, the **goal**, the **audience model** and the **trend read**
  (`creative-direction.md` §2–§4; protocol §6);
- `20-analysis/project-profile.md`: domain, objective, authoritative requirements, entities,
  preserve / replace / adapt / **contents / place** / ignore, which references are swap, contents or
  placement, and the fit of the **supplied** assets (registry) to them;
- `20-analysis/directions.md`: numbered directions (subject × structure × execution style). Each
  says **why it will work** for the goal and the audience (`creative-direction.md` §5), lists
  **which supplied assets it would use** (registry entities) and **how the product appears**:
  swap of a named source entity, contents in a named vessel, or placement with its likely anchor.
  - A direction that needs an asset type the user did not supply is either adapted to what exists
    or marked "needs <type> — not supplied".
  - Directions are also shaped for the **locked model** (its durations, references, audio and
    frames, from its `index.json` entry). No direction may depend on a capability the model lacks
    unless it states the adaptation.
  - **Create** presents them as style groups, plus hybrid groups that blend several families with
    the product's strengths (A6).
- **Recreate:** `20-analysis/recreate-ranking.md`, every reference ranked by recreate fit (protocol
  §5). The guardrail audit is its first filter: dismissed references are out of the ranking and
  listed under it with their rule; pick-and-edit references rank with their guardrail operations
  counted in the edit load (`brand-guardrails.md` §4).
- **With examples:** `20-analysis/house-approach.md` (protocol §9.3): the user's consistent approach,
  one rule per line with its evidence and the default it replaces. Directions, picks and plans
  follow it (contract item 18).

Show a **short** chat summary:
- the project profile in about 5 lines;
- the families table;
- Create: the essence in 3 lines and the mechanisms the product can carry (k of n);
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
  - Each group lists its mechanisms (M#, k of n references, graded), the typical length range, and how the product appears (its blend-matrix cell).
  - They are the agent's suggestions, built from the analysed patterns **and the product's
    strengths** (the insight sheet), never a menu or a template. Include **hybrid groups** that blend
    mechanisms from several families with what the product uniquely brings, and a format the
    references never showed when the mechanism logic and the product support it
    (`creative-direction.md` §5.0b).
- Ask with AskUserQuestion (header "Styles", `multiSelect: true`). The first option is **Agent's
  choice (Recommended)**: the agents design the blends with the highest engagement potential for this
  product and audience, from any family, hybrid or new format (`creative-direction.md` §5.0b); the
  other options are up to 3 of the best groups. The user picks **Agent's choice, one style or a
  mix**. "Other" accepts numbers or quantities ("2×G1, 1×G4").
- Without exact quantities, spread the videos across the chosen groups first, then by fit; under
  Agent's choice every video is its own best blend. A mixed answer (Agent's choice together with
  named groups) and no quantities gives the named groups half of the videos (rounded up, spread
  across them first) and Agent's choice the rest; quantities, when given ("2×G1, the rest Agent's
  choice"), always win. Show the allocation in one line and store it in `directions`.
- **The N videos are varieties.** Each is its own new concept: a different scenario, hook, setting
  or character beat.
  - **Transfer, not repetition** (`creative-direction.md` §5.0): every concept takes from the
    references only their craft (the style, the properties, the approach, the crafting, the hook
    type, why it works) from `20-analysis/craft-sheet.md`, and brings its own subject from the
    product's audience (the audience model's product half) and the product's natural use. A seed that restages a reference's premise,
    setting, characters, action order, joke, lines, first frame, ending or product beat fails the
    **copy test** and is rewritten with a new subject or dropped. That is Recreate's job, not
    Create's.
  - **Blend, not mimic** (`creative-direction.md` §5.0b): Create designs the most engaging video
    for *this* product from two inputs of equal weight, the references understood
    (`craft-sheet.md`, the audience model, the trend read) and the product understood
    (`30-assets/product-insights.md`). Every seed names its blend (the borrowed mechanism, the
    product truth, the audience situation) and passes the **blend test** (without the product the
    idea is generic; without the mechanism it is only an ad) and the **template-lock test** (it is
    not one family's structure and tone with the product swapped in). Families are evidence and
    ingredients, never a menu: the winner is chosen for engagement, not for resemblance to a
    reference.
  - **Virality-backed** (`creative-direction.md` §5.0c; `viral-browser.md` §14.2–§14.4): seeds come
    from the available cells of `20-analysis/blend-matrix.md` (a seed outside it is a new format and names
    "M#: none (new format), speculative"); only the craft is borrowed (never a
    reference's creator reach, paid reach, brand, bait, season or product); the blend line also
    names the audience trigger, the hook and its timing inside the measured range, the current
    trend element and the share line; and the winner carries its **virality rationale** (why it
    should spread, and what could make it fail).
  - **Ideation, scored** (`creative-direction.md` §5.1): for every video slot write at least five
    concept seeds (situation + turn + where the product lives + its blend line: M#, PT#, the hook and its timing, the trend element, the share line), score each on stop
    power, relatability, sharpness, product nativeness, blend, trend fit and freshness, feasibility
    for the locked model, and brand safety; take the best, keep the runner-up as the fallback, write the
    winner's share line, job and virality rationale (`viral-browser.md` §14.4), and run the sharpness gate (§6). Save them to
    `20-analysis/concepts.md` and show one line per video (seed, score, the reason it won). The
    user may swap a pick by replying; nothing is asked.
  - Each one borrows the mechanisms that made the references go viral (hook logic and timing, a
    structure move, a pacing device, a humour or payoff device) from whichever families show them,
    in whatever mix the product's strengths and the audience call for; its structure, pacing and
    payoff are designed for the blend, never copied from one family's profile or re-run from one
    family's format.
  - The client's product is blended into the concept from the first idea, not added at the end (its
    most suitable use, `generation-system.md` §4b.0), the way the house approach does it when
    examples exist.
  - No two videos repeat the same concept, and none repeats a reference's subject: the copy test
    runs against every reference the blend borrows from and the run's other winners.
  - **Guardrails as invariants** (`brand-guardrails.md` §4): the count limit is a ledger
    invariant, competitor objects never appear, only supplied characters appear, the wording
    rules shape the text plan, the presentation rules shape the anchor and the use beats, and a
    seed that a content or context rule hits scores 0 on brand safety.
- **Create never uses a reference as input.**
  - No reference video, frame or clip is uploaded, edited or passed to a generation.
  - The analysis informs only the borrowed mechanisms and the craft (hook logic, structure moves,
    pacing devices, camera behaviour, text role); the concept and the product's use come from the
    blend with the product insight sheet.
  - A meme the style calls for may still be placed in CapCut: an insert cut from a reference, or a
    supplied file.

### A6r. Recreate: pick the references and plan the edits (Recreate only, autonomous)
- **Use the recreate ranking from A4** (protocol §5). It weighs:
  - the integration form available for the product (swap / contents / placement);
  - for a placement, the anchor class the locked model renders at size: where its guide lists size
    as a model limit (`wan3_0_prime`, `wan-3-0.md` §5), an in-hand, swap or large same-plane
    neighbour anchor ranks above a surface anchor that only paper, a notebook or a head can size;
  - the number of people against the supplied characters;
  - the own-content length after stripping inserts, against the locked model's edit range. A longer
    one is split, which may need the A7b permission;
  - the load of text and overlays;
  - the motion complexity for the model's `edit_kind`;
  - its creative potential (`creative-direction.md` §5.2): mechanism strength, fit to the goal and
    the audience, how natural the product's integration can be, the freshness of its surface
    elements, and the risk of reading as a copy;
  - and, before all of these, the **guardrail audit** (item 21; `brand-guardrails.md` §3–§4): a
    reference with a core hit is dismissed and never picked; a pick-and-edit reference carries
    its guardrail operations into the edit load.
- **Take the top N.** Show one line per pick plus two runners-up, then proceed; the user may swap
  picks by replying. Store `recreate_picks`. Name the dismissed references with their rule in one
  line each.
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
    An insert that shows an excluded person or a competitor's mark is cut and not placed back. Each
    insert is cut on frames that hold only its own content (edges past any dissolve or frame of the
    replaced performer), and the reference timeline and its original audio stay whole
    (`generation-system.md` §3c; CE-016, CE-024, CE-025).
  - **Guardrail edits** (`brand-guardrails.md` §2, §4), as change marks in the source action
    script and as operations in the first request: an untouched unit beyond the count limit is
    removed and the ledger holds the limit at every checkpoint; a competitor's name, logo and
    identifying mark are removed from its object, which stays as a plain unbranded one of the
    same shape, size, spot and light (never blurred, pixelated or covered); an excluded person is
    swapped completely (face, hair, marks, reflections), their name dropped from the text and
    their voice named in the brief; a caption that breaks a wording rule is rewritten minimally
    in CapCut, and a required disclaimer is added as a text layer in the house style; a peripheral
    banned prop is removed with its surface reconstructed.
  - **Audio:** the reference's original audio for its own content is restored onto the edited
    picture (X8 step 1); the inserts keep their own sound.
    - With inserts: `T restore-audio --generated <edit> --source <own.mp4>`.
    - Without: `--audio` from `files_audio`.
  - **Source fidelity (item 19):** the edit keeps the reference's movements, actions, details and
    timing, and only the operations above change. Add the pick's **source action script** with its
    keep / change marks and **sync anchors** to its card (`generation-system.md` §5c.1); the plan
    and the first request carry them.
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
- **Fit the brand to the scene first** (CE-020): a food, grill, party or sport scene suits a drink; a
  desk, class, meeting, work or commute scene suits a focus product. The plan states the tie in one
  line, and a reference with no tie for one brand goes to the other, whatever free surface it offers.
- **Then the form** (CE-007): where one product comes in several packages, pick the form that fits the
  scene's scale and register: the smallest closed form in a casual handheld scene, a large pack only where
  a large pack belongs (a large stand-up pouch in a phone-and-couch scene read as too much; the small
  carton fits).
- **Then distribute sensibly.** Spread several products or variants across videos unless the user or a
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
1. Read **only** `ATG/<guide>` for that model (from `index.json`), `ATG/higgsfield/higgsfield-mcp.md`,
   `ATG/reference/generation-system.md`, `ATG/reference/anomaly-catalog.md`,
   `ATG/reference/creative-direction.md`, `ATG/reference/text-and-format.md`,
   `ATG/reference/capcut-assembly.md` and `ATG/reference/production-agents.md`.
   - For a model with no guide, read `ATG/models/_generic-fallback.md`.
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
5. **The agent contract:** write `<RUN>/50-requests/agent-contract.md` from the prompt in
   `reference/production-agents.md` §2 (the canonical text: the recording rule, the checks, the size
   method, the deliverables), filling its paths; run-specific notes go in its last block. It is generated
   for every run and never copied from an earlier run's file.

### A9b. Produce in parallel (production agents)
- **Spawn one production agent per video** (`reference/production-agents.md` §2 prompt, as written to
  the run's contract file at A9; `subagent_type: general-purpose`, `run_in_background: true`).
  - At most `production.max_parallel_agents` (5) run at once; start the next queued video when one
    finishes.
  - Each agent runs X3 (its own inputs) → X7 → X8 → X9 → X10 for its video, ending with its CapCut
    project, and returns one JSON line. It runs X5 again for any request it changes.
- **As each agent reports:**
  - read its `60-outputs/video-NN/result.json`;
  - record it (`T state --run RUN append videos='<json>'`);
  - reconcile the ledger: a `qc` that says RESIDUAL FAILURE or regenerated, with no entry in
    `T caught-error list --grep <RUN>` for that video, is recorded now (`--source agent`, one entry
    per class and anchor, the videos listed);
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
  - CapCut was running → its project is pending until the wrap-up;
  - credits ran short → launch nothing more, report the shortfall; the run stays resumable;
  - a request failed twice → report it in the wrap-up.
- **QC verdicts are autonomous** (X9); a video that still fails is reported in the wrap-up.
- **Without the Agent tool**, run X3–X10 per video in this session, one video at a time.

### A10. Wrap-up
See §6.

### Viral-Browser (V1–V9)

Run these steps, **instead of A1–A10**, when `analyze_submode=viral-browser` (V1 does its own
inventory and preprocessing; A2's rule that documents are authoritative requirements applies). Read
`ATG/reference/viral-browser.md` once at V1 and follow it. Nothing is generated: no Higgsfield tool,
no model, no credits, no CapCut, no assets, no change to the references folder. At the end of each
step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>` (the
`next_step` values below make the run resumable). The market, price range, selling model, sales
channel, tools, depth and exclusions live in `state.json → brief.*`.

#### V1. Brief, inventory and preprocessing
- Store the held answers now that the run exists (`T state --run RUN set brief.market=… …`, Start
  step 5).
- **Caught errors first** (item 22): `T caught-error list --mode analyze-viral-browser --digest`,
  plus the entries of class selection, evidence or bias. Write `20-analysis/caught-errors.md`
  with the ones that apply and the step each changes.
- Write `20-analysis/brief.md` from the answers (`viral-browser.md` §2): market and lead
  countries, currency and tax convention (US prices exclude sales tax, EU prices include VAT; fees
  are charged on the amount paid), the price band and the landed-cost ceiling, the selling model,
  the sales channel, ad platform, importer-of-record country and capital limit when given,
  exclusions, depth and tools, today's date, the selling windows of the next 120 days with the lead
  time, the Global per-market convention, and the production route.
- `T inventory "<refs folder>" --run RUN --as references`; with a baseline folder
  `T inventory "<baseline>" --run RUN --as baseline`.
- `T prep-all --run RUN --jobs 2` (and `T prep-all --run RUN --set baseline --jobs 2`); with more
  than about 3 minutes of video run it in the background and read the documents meanwhile
  (documents are authoritative requirements and are quoted, "we already sell X" included).
  **No `split-audio`:** the references folder is not touched.
- `T audio-context --run RUN --profile --second-pass` (and `--set baseline` with a baseline): the digest of every transcript and the sound
  numbers of every video, with no labels (A1 lists them; `--second-pass` runs for every video in which no
  words were found; `viral-browser.md` §3.1, `analysis-protocol.md` §2 item 4). A video whose status is
  failed, missing or skipped (`without_a_transcript` in the JSON) is prepared again before the cards
  (`T prep-all --run RUN --only <V> --redo --whisper-model medium`).
- A metrics or links file becomes `20-analysis/metrics.md`: one row per video (views, likes,
  comments, shares, saves, followers, date, link, source), matched to the video ids by file name or
  link, and "not provided" where there is nothing. Never estimate a metric. **Reference pages**
  (only with a links file and "web plus my Chrome"): read each post page, read-only, up to
  `reference_pages_max[depth]` pages, for the counters, the caption, the creator's size, the date
  and the top comments in aggregate, and add them to `metrics.md` (`viral-browser.md` §3.6).
- Show the counts in one line. `next_step=cards`.

#### V2. Viral cards
- One card per reference in `20-analysis/cards/<V>.md` and a light card per baseline video, as
  `viral-browser.md` §3: the product layer and the mechanism layer kept apart, the one-line `Facts:`
  JSON with `category` set to a short label for the niche of the product's main use (taken from the
  material; no script lists niches), `voice_type` (on-camera / voice-over / sung / rap / chant / none /
  mixed …: the card agent's judgement, since the transcriber cannot tell speech from lyrics),
  `shots_seen` (the agent's own shot count from the storyboard, beside the measured one) and
  `price_tier` only when the video shows or says a price, commerce signal versus attention-only,
  the ranked drivers of spread, the one-sentence mechanism, the transplant needs. Every card states
  "sheets seen n of n", and a sheet that did not display is read again before the card is written.
- Sound: for each reference run `T audio-profile --audio "<the original video>" --out
  10-media/<V>/audio-profile.json --transcript 10-media/<V>/transcript.json --cuts
  10-media/<V>/cuts.json` (the original video is the input here; nothing is written to the references
  folder). `T viral-stats` tabulates the numbers (tempo, beat strength, harmonic share, spectral
  flatness, audible non-speech share) and labels nothing; what each sound is, is the card agent's call.
  Every card carries the `Audio context:`, `Said:` and
  `Words and sound together:` lines (`viral-browser.md` §3.2); when the cards are written, run
  `T audio-context --run RUN --check --cards` (and with `--set baseline`): a completeness check only, which
  writes nothing; add what it lists before V3.
- Scale and delegation as protocol §7: up to 6 videos in this session; more, 1 analysis agent (2 over
  about 15 videos) with disjoint lists and the prompt of `viral-browser.md` §13.1.
- Merge the labels into `20-analysis/labels.md` and rewrite the Facts lines so one meaning has one
  label; set `creator_group` in them yourself (the main session), from the creator handle each card
  carries, in the format `g01`. Then build the **niche vocabulary** yourself from the data:
  `T niches propose --run RUN` tabulates the category labels in use with their counts, the niche each
  is recorded under and the `unmapped_labels`; you decide which labels are the same niche (no script
  compares labels or words) and record each decision with its reason:
  `T niches add --name "<niche>" --members "<label>,<label>" --by main --reason "…"` and
  `T niches map --label … --to … --by main --reason "…"` (a label that another niche held moves, and
  the move is noted; `viral-browser.md` §3.2, §5 item 3). `next_step=synthesis`.

#### V3. Corpus profile and synthesis
- `T viral-stats --run RUN` (`--set both` with a baseline): tables only. Per set it prints the
  distributions (length, median shot, cuts per 10 s, first cut, when speech starts (any word, and the
  first word of probability 0.5 or more), words per second, loudness, loop similarity, text spans,
  tempo, beat strength, harmonic share, spectral flatness, audible non-speech share), the shares (a cut in the first 3 s, no cut at all, words found, a word or
  a text in the first second, vertical 9:16, attention-only) and one `labels` table per Facts key
  (label, count, share, videos). The `category` table is read through the niche vocabulary you
  recorded, with the raw labels written on the cards folded in, and marks each label
  `recorded_in_vocabulary` true or false: place every label that is not in the vocabulary
  (`T niches add` / `map`, with `--by main --reason "…"`), then run it again. It also lists
  `cards_without_facts` and `cards_with_unreadable_facts`: fix those cards (every reference card needs a
  `category`, `non-product` when no product category shows). Nothing is flagged, labelled or ranked: no
  script says which niche dominates or whether two names are one niche.
  **You read the category table** and apply the rule of thumb (`viral_browser.rules_of_thumb`): a niche
  that is 40 % or more of the references' cards is a **dominant niche**; with fewer than 10 videos read
  every share as an indication, not a rate. Write your reading, with any exception and its reason, in
  the bias log.
- Write, as `viral-browser.md` §4: `mechanism-map.md` (mechanisms `M1…`, k of n, niche
  independence, confounds), the hook, length and pacing profile, the engagement style (one template
  per family plus the composite), the audience and mentality model, `viral-essence.md` (the essence,
  the fit profile, what is not inferred), the trend read (at most `trend_checks[depth]` bounded
  searches; if a TikTok account is connected in Higgsfield, `tiktok_music_trending` for the market's
  country code, loaded with ToolSearch, else skipped silently), your niche-dominance reading with its
  bias plan, and the standard `families.md`, `craft-sheet.md` and `project-profile.md` for a later
  Create. Start the bias log, the "Bias log" section of `30-research/ranking.md` (written by the main
  session, not by a script).
- Show the short summary (§4.11): the essence in 5 lines, the fit profile, the niche shares (your
  dominance reading) and the controls it triggers, the mechanisms, the typical length and hook profile.
  `next_step=candidates`.

#### V4. Candidates
- Build the long list of 12–20 specific candidates from the five sources (`viral-browser.md` §6),
  with `T candidates add` (or `--from-json`). A candidate is a product a supplier search returns, not a
  category; its name, definition, **niche** (as `--category`: a label from the vocabulary, or a new
  niche you decide and record with `T niches add`), type and origin are all required, and the name and
  definition never mention the references. `add` stores the niche under the one the agents recorded for
  that label (as written otherwise) and reports `niche_not_recorded_in_the_vocabulary`: record those.
  Screen with stated reasons.
- Read the balance of the long list yourself: `T candidates summary --run RUN` counts the candidates by
  niche, type, origin and status (`--exclude-eliminated` leaves the eliminated out). The rules of thumb
  (`viral_browser.rules_of_thumb`): at least 6 niches, none above 40 % of the list, at most half from
  the references' own products. Repair the list where the numbers show it departs from them, or keep
  it and write the exception and its reason in the bias log; no script flags or refuses anything. Then
  spawn the **niche-audit agent** (`viral-browser.md` §13.5; fresh context, it changes nothing and
  writes `30-research/niche-audit.md`): it reads the vocabulary for one niche under several names,
  synonyms that share no word included. Apply its merges (`T niches merge --from … --to … --reason "…"
  --by main`, which folds the members and renames the niche on the candidates), run `T viral-stats` again
  when a merge touched a card label, and record the audit (`T niches audit --by main --result "<what it
  found and what was applied>" --report 30-research/niche-audit.md`). Then choose the shortlist (6 / 9 /
  12 by depth), read `T candidates summary --run RUN --ids C01,C02,…` for exactly that set against the
  same rules of thumb, and start research with
  `T candidates set --run RUN --ids C01,C02,… --status researching --by main --reason "<the balance reading and any exception>"`.
  Statuses are a vocabulary you use and record (long, shortlisted, researching, researched, eliminated,
  picked, runner-up, watch): `set` changes any field and any status from any status, logs `--by` and
  `--reason` in the candidate's history, and the toolkit sets none on its own. Change a researched
  candidate's name, type, definition or niche only with a stated reason.
- Show one table: candidate, niche, origin, why it is in the pool. `next_step=research`.

#### V4b. Cost basis and shared inputs (before the wave)
- Decide, once, the inputs that do not depend on the product and write them with their sources in
  `30-research/cost-basis.md` (`viral-browser.md` §7.0): the postage per order by weight class from a
  carrier's own price list (US and the lead country) plus pick, pack and materials = the fulfilment per
  order, and what the store's shipping policy does to it; the return rate and the cost of a returned order
  per market; the card and platform fees of the channel's real fee schedule; the exchange rate with its
  source and date; the tariff regime for the origin with the guess it rests on; the freight tables and the
  calendar. Register the sourced ones once as evidence rows (`T evidence add --from-json`), under one
  candidate, so that the research agents copy them (`T evidence copy`) instead of searching again. Use the
  cost basis for the economics screen of V4: `T econ … --target-pct 25` per market on a rough landed cost
  (`T landed`) says which retail price a candidate needs; a price above the band's top, or far above what
  the market shows, removes the candidate with that reason.

#### V5. Research (agents)
- Spawn up to 3 research agents (Agent tool, `subagent_type: general-purpose`,
  `run_in_background: true`) with disjoint candidate lists and the prompt of `viral-browser.md`
  §13.2 filled in (market, currency, band, VAT convention, selling model, sales channel, importer
  country, capital limit, exclusions, depth, today's date). They register evidence (`T evidence add`
  with `--signal positive|negative|mixed|neutral`, `--independent yes` and `--by`; the toolkit checks the
  form only: the required fields, and a URL on an independent grade A or B row; each sourced economics
  input is its own grade A or B row with a URL), run `T econ … --cand C## --run RUN --market <M>`
  (arithmetic only; once per market for a global or multi-country market: the results are kept per market
  in `economics_by_market`, side by side, each with its inputs, and an evidence row with signal
  `calculation` is written; the contribution per order, `break_even_cpa` (it can be negative),
  `break_even_roas_*` (null when the contribution is not positive) and `inputs_left_at_zero` are numbers
  for you to read, not judgements), write `30-research/<C>.md`, origin-blind, and queue unreadable pages
  in their own `queue-<C>.md`. The prompt carries the cost basis and the shared rows to copy; the agents
  use `T landed`, `T econ … --target-pct 25` (the retail price a 25 % contribution needs, set against the
  prices the market shows), `T evidence add --from-json` and `--opened yes|no`. A background wave stops when
  you interrupt the turn: the ledger keeps what was registered, so restart each agent with only its
  unfinished candidates and a STATE AT RESTART note (`viral-browser.md` §13.2).
- Before you read the results side by side, read the stored economics inputs of every candidate (each
  candidate's `economics_by_market` has them) for different assumptions on the same cost lines; reconcile them
  on the cost basis: re-run `T econ` for each candidate and market, withdraw the superseded calculation rows
  with `T evidence retract` and the reason, and note it in the bias log.
- When they have reported, check that every shortlisted candidate has a dossier, evidence rows, an
  economics row and a sourced input row behind it (`T evidence list --counts` tabulates the rows by lane,
  signal, grade, independence and distinct sites; it weighs nothing); a missing one is researched once by
  a new agent. A candidate an agent reports as settled by a gate is eliminated here by you
  (`T candidates set --id C## --status eliminated --by main --reason "<the gate and the evidence>"`; the
  reason stays on the candidate). A wrong evidence row is withdrawn with
  `T evidence retract --id EV### --reason "…"` (kept on record, left out of the counts).
  If an agent reports a denied tool (`WebSearch`, `WebFetch`, `Bash`), research that candidate in this
  session within the same budget instead of retrying the agent.
- With "web plus my Chrome": load the browser tools in one call (`ToolSearch "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__tabs_close_mcp"`),
  call `tabs_context_mcp` first and process the `30-research/queue-<C>.md` files in this session, up
  to `browser_pages_per_candidate[depth]` pages per candidate, read-only (`viral-browser.md` §7.5),
  registering the evidence. Without it, queued pages stay "unreachable". Read a marketplace search page
  with a short read-only script (title, price, rating count and sold badge of each result), a trend chart
  from a screenshot, an official rules page as text; then re-run `T econ --cand` at the retail price the
  pages support (the market's stored result is replaced; withdraw the superseded calculation row with the
  reason). A page that informs several candidates counts for each; call `tabs_context_mcp` with
  `createIfEmpty` again before each batch, and stop after two failed attempts to connect.
- Blockers (a tool failure, rate limits) are reported, not asked. If `WebSearch` and `WebFetch`
  are both unavailable, stop here: V1–V3 are delivered (the mechanism map and the fit profile are
  useful alone) and the summary says research could not run. `next_step=scoring`.
- **Backfill:** if your selection in V6 leaves fewer than 3 candidates that meet the gates of thumb, come
  back here **once**: shortlist the next `backfill_researched[depth]` candidates from the long list (read
  the balance rules of thumb on that set again and record `researching` with `--by main --reason`),
  research them the same way, then rate and select again (`viral-browser.md` §7.1).

#### V6. Scoring, red team and selection
- Spawn the **scoring agent** (`viral-browser.md` §13.4): a fresh, blind context that never sees the
  cards, the mechanism map or any origin. It rates every researched candidate
  (`T candidates rate --id C## --ratings demand=4,commercial=3,… --refs "demand=EV001+EV002 …"
  --confidence low|medium|high --by …`; a form check only: an integer 1-5, a known criterion, evidence rows
  that exist for the candidate) and records its readings of price fit, compliance and exclusion with
  `T candidates set --price-fit … --compliance … --excluded …`. It applies the rules of thumb for evidence
  and says so in its note: a rating on demand, commercial, competition, economics or compliance with no
  positive independent grade A or B row is 2 at most (for economics the calculated estimate also needs a
  sourced input row); negative rows that match the positive ones hold a 4 or a 5 at 3. No script caps or
  changes a rating. **This session does not score**: it built the pool and has seen the origins.
- Read the table yourself: `T candidates table --run RUN --sort weighted --desc` sets the candidates
  side by side (ratings per criterion, `weighted_sum_of_rated` = a plain weighted sum of the ratings where
  an unrated criterion adds nothing, confidence, red team, price fit, compliance, economics per market, an
  evidence cell "rows (grade A/B; distinct sites)", pick rank; `--blind` hides the origin). It marks no
  winner and applies no gate. Choose the **red-team targets** yourself: the candidates you would pick under
  the gates of thumb below, plus the next two. Spawn the red-team agent (§13.3) on them and record each
  reading (`T candidates set --id C## --redteam survives|weakened|fails --note "…" --by red-team`),
  eliminate the ones that fail (`--status eliminated --by main --reason "…"`), have a fresh scoring agent
  revisit only the criteria the red team names, and read the table again until every target has a reading
  (two rounds at most).
- **Select** (this session, by your own reading). Apply the six gates of thumb to each candidate: the price
  band; a contribution margin of at least 25 % of net revenue from `T econ` with a sourced input row
  (read per market in `economics_by_market`, side by side: you decide which market governs for this
  brief and write down why); compliance clear or resolved, backed by a positive independent official or
  reputable row; not excluded by
  the brief; positive independent evidence from at least two distinct sources across demand, commercial and
  competition, one of them commercial; ratings of at least 3 on demand, commercial, economics, compliance
  and fit, and confidence of at least medium. Choose the three picks and the runner-ups (at most two picks
  in a niche, none sharing a product type) and break any tie by your own reading, written down. Write the
  defence of every pick from the dominant niche against the best outside-niche alternative
  (`T candidates set --id C## --defence "…"`); a pick with no honest defence is eliminated and the selection
  redone. Run the what-if yourself: the same selection without the reference-derived evidence and without the
  fit criterion (`T candidates table --exclude-criteria fit`), and say whether the picks change. Write
  `30-research/ranking.md`: the picks, the runner-ups, every other candidate with the reason it is not a
  pick, the what-if and the bias log (your dominance reading, and every gate of thumb you applied or set
  aside, each with its reason). Then record the result for each pick: `T candidates set --id C##
  --status picked --pick-rank N --by main --reason "…"` (`--status runner-up` for the runner-ups;
  `--pick-rank` records your pick order).
- Show the ranking table in chat: the picks, the runner-ups, the gate each other candidate did not meet
  (your reading), any exception. If fewer than 3 meet the gates, run the backfill (V5) first; if still
  fewer, report the shortfall and say which gate removed each and what could be relaxed (§8.6): a gate is
  never lowered silently to fill the table. `next_step=blueprints`.

#### V7. Blueprints, reference packs and deliverables
- Per pick, a **trend pass** (up to `pick_trend_checks[depth]` bounded searches or pages for the
  formats, hooks and sounds now used in that product's niche and market, dated; `tiktok_music_trending`
  once when an account is connected), then `deliverables/product-NN.md` (its dossier and its
  blueprint, `viral-browser.md` §9–§10).
- **Reference packs** (`viral-browser.md` §9.1): right after the picks are recorded, spawn up to 3
  reference-pack agents, one per pick, in the background with the prompt of §13.7 filled in (run,
  toolkit, date, market, the pick, the depth and its `reference_pack_budget`), and write the blueprints
  meanwhile.
  - Each agent records the facts it finds (`T spec add`, with source, kind, grade, scope and variant),
    the photo links (`T photo find` / `add`) and its judgement of each core field with
    `T spec judge --cand C## --field … --fact SP### --status "<its own label, for example verified, official, reported, unverified, conflict>" --reason "…" --by …`
    (the latest judgement wins and nothing is computed). A fact found to be wrong is withdrawn with
    `T spec reject --id SP### --reason "…"`, a link with `T photo set --id PH### --reject --reason "…"`
    (both stay on record, off the sheet; `--restore` brings a link back).
  - When they report, read each pack yourself: `T spec gaps --run RUN --cand C##` counts the facts and
    judgements for the core fields, `T spec table --run RUN --cand C##` sets the facts side by side with
    the plain spread of the numbers, and `T photo list --run RUN --cand C##` / `T photo check` produce the
    photo coverage table (links, confirmed, https and looked-at per view label as the agents wrote it,
    and for the core views). Whether a pack is enough is your reading, guided by the pack rules of thumb
    in `viral_browser.rules_of_thumb` (photo links per pick, attempts, thumbnail size, minimum angles,
    spec tolerance): no script suggests a set or calls a pack covered. A pack you judge not enough gets
    one more reference-pack agent for that pick alone,
    told what is missing, with the same budget again (one extra round only), and what is still missing is
    reported, never invented.
  - **No image is downloaded: the packs hold links.** Process `30-research/queue-<C>-pack.md` with the
    user's Chrome only when they allowed it (read-only: the image links of a gallery, a specification
    table; register them with `T spec add` / `T photo add`; an image you open in the browser may get its
    flags with `T photo set --looked-at yes`, which the four visual flags require), then `T spec render`
    and `T photo check` for each pick (`spec.md`, `photos.md` and `photos.html` are written into the pack:
    the judged value with its status and reason, or "no judgement recorded" with the facts side by side).
    The packs go in `deliverables/reference-C##-<name>/` (named after the candidate; the first
    `T spec render` or `T photo add` creates the folder).
- Then `viral-browser-report.md` (with each pick's specification table and photo links with their link
  status and the flags recorded),
  `evidence.md` (`T evidence list --run RUN --out <RUN>/deliverables/evidence.md`),
  `create-handoff.md` and `README.md`. `next_step=report-qc`.

#### V8. Report QC
- The checklist of `viral-browser.md` §10.4, run by you (no script runs it): every number sourced or
  recomputed with `T econ`, the gate reading per pick quoted from `ranking.md`, origin-blind dossiers,
  defence notes present, one currency and tax convention, region-matched evidence, up to 12 key claims
  fetched again, no unsupported hook or claim, each pick's reference pack (spec judgements and the photo
  coverage table, nothing read off a photo, no image downloaded, angles shown as the source's labels,
  rights stated), and each research error that reached this step recorded as an agent entry
  (`--source agent`, with `--title`). Fix before anything is shown. `next_step=wrap-up`.

#### V9. Wrap-up
- Show the summary (`viral-browser.md` §10.3): the table of the three picks (with each pick's reference unit, size,
  weight, material and photo-link coverage), the method in three
  lines, the open questions, the deliverables path and the run folder. No credits, no CapCut.
- Ask for feedback (`viral-browser.md` §11.2, header "Picks") and record every problem named
  (item 22, with `--title`) before offering the fix. "Adjust" follows §11.3.
- Offer in one line the next step: **continue to Create for a pick** (§11.4: the run enters the
  Create flow at its start, for the new inputs only; it needs the product's assets and a model and
  starts only on the user's yes), more depth on one candidate, or nothing. When the ledger holds two
  or more open entries of one class, add: "Run `/update-from-errors analyze-then-generate` to
  generalise these."

## 4. Edit Mode

### E1. Intake
- **Caught errors first** (item 22): `T caught-error list --mode edit` plus the class entries;
  write `20-analysis/caught-errors.md` with the entries that apply to this model and the edit
  kinds, and apply them in X1, X2 and X9 like any plan rule.
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
  - the **source action script** (item 19, `generation-system.md` §5c.1): every beat in order, with
    who moves what and how (body, hands, head, gaze, face, mouth), the props and their contacts, the
    camera, the background action and the small details. Each beat gets its time range, and is
    marked keep or change once E3 has the operations;
  - its **sync anchors**: the beats whose sound is in the original audio (each spoken line and
    whose mouth says it, impacts, steps, pickups, sips, opens), with their times, from the
    transcript, the storyboards and, when it helps, `T audio-profile` hits;
  - the **source-text inventory** (`text-and-format.md` §2.1);
  - when guardrails were supplied with the assets (`30-assets/guardrails.md`), the **guardrail
    audit** (`brand-guardrails.md` §3): every hit, core or peripheral, and the operation the rule
    requires.
- Show the user a 4–6 line understanding of the video. With guardrails, add one line per hit:
  the required operation ("G4 requires a face swap for the man on the left"), or, for a core hit,
  that editing it would change the video ("this video's point is the taste test, which G3 bans").
  The user decides the operations in E3.

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
   - Write the replacement product's affordance sheet (`anomaly-catalog.md` §1) whenever the edit
     has it handled or used on screen (drunk, opened, applied, carried).
   - "Same files as video K" reuses that scope explicitly. Nothing else carries over.
4. Remind the user once that all source text (captions, usernames, watermarks, stickers, overlays…)
   is removed unless they name text to keep.

### E4. Locked model — how it performs this edit
- The model was picked at the start (§2.4) and does not change. Before the first edit, read **only**
  its guide + `higgsfield-mcp.md` + `generation-system.md` + `anomaly-catalog.md` +
  `text-and-format.md`, and call `models_explore get` once.
- Map the chosen operations onto the model's edit capability (`index.json → edit_kind`):
  - **✓ edits video** (`video_edit`, `object_replace`): a true edit of the 9:16 source.
  - **↔ motion transfer:** the source drives motion; the supplied files define the subjects and
    scene.
  - **≈ recreate** (`video_refs`): regenerate the clip with the source as a motion, camera and timing
    reference, applying the operations.
  - **✗ frames only:** recreate from clean 9:16 frames of the source, with the operations applied to
    those frames through the supplied files, plus a prompt that rebuilds the source's action.
- **Fidelity (item 19).** Take the most preserving way the locked model can perform this edit,
  with the guide's preserving mode and settings (`generation-system.md` §5c.2). ✓ and ↔ keep the
  source's movements and timing by construction. ≈ keeps them only with the source as the video
  reference, the same duration and the action script written out. ✗ cannot guarantee them: use
  the source's own first frame, and its last frame when the model takes one, with the operations
  applied; write the action script out; and say in the brief that fidelity and sync are at risk.
- State the approach in the brief (one line). Never switch models.

### E5. Prepare the source (local, deterministic)
- **Start from the silent copy** (`videos_without_audio/…`), never from the original with audio.
  Every preparation below produces a silent file under `RUN/10-media/<V>/prepared/`. The user's
  folders keep only `files_audio` and `videos_without_audio`.
- **9:16.** If the source is not 9:16, choose (per `text-and-format.md` §4.1):
  - `T conform` with a focus point, when a crop keeps every important subject: run it with `--dry-run`
    first; it writes nothing and reports `lost_fraction`, the share of the picture the crop removes. It
    never refuses a crop; the decision is yours, and the rule of thumb is that a loss above about 12 % is
    a reason to use `reframe` or to regenerate from a 9:16 start frame (say what you chose and why);
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
    - intent (`generation-system.md` §2.1): the goal and the video's job, the audience, the one
      sharp idea, the emotion arc or laugh mechanism, the share line (`creative-direction.md` §2–§6);
      Create: the blend (the borrowed mechanisms and the product truth) and the subject the concept brings,
      with the copy and template-lock tests passed (`creative-direction.md` §5.0, §5.0b), and its virality
      rationale (`viral-browser.md` §14.4);
    - the **caught errors applied** (item 22): the ids from `20-analysis/caught-errors.md` that
      apply to this video and what each adds to the plan, the ledger, the prompt and the QC
      checkpoints; an entry about creative quality goes into the ideation and the sharpness gate;
    - the **guardrail hits** of the source (Recreate, Edit Mode) with their operations and times,
      or the guardrail invariants of the concept (Create): the count limit in the ledger, no
      competitor objects, supplied characters only, the wording rules in the text plan
      (`brand-guardrails.md` §4);
    - the **size reckoning** for every product in every shot (`anomaly-catalog.md` §2.7): its real
      dimensions from the registry, its distance from the camera, derived from the frame and
      never assumed (Recreate: the source frame; Create: the blocking asked for), from the surface it
      stands on and a same-plane neighbour of known size, the basis written beside the number (a product
      on a dresser behind the subject is farther than the subject), the lens
      the look implies, the expected fraction of the frame height (`T scale --product-cm H
      --distance d --lens f` prints it and a table over the usual shot distances), the one named
      neighbour at the same depth with the ratio in words, the size ladder when several products
      show, and the size it keeps across motion, exits and cuts;
    - the per-second time budget (Recreate: from the source's timeline; Create: from the beats of
      the planned blend and the locked model's duration range);
    - roles and assets;
    - the scene;
    - Edit Mode and Recreate: the **source action script** with its keep / change marks and sync
      anchors (item 19, `generation-system.md` §5c.1), taken from the card and densified around
      fast moments and contacts;
    - the **entity state ledger**, with a count for every multiple and, per row, the opening or lid
      state, the level, the holder and hand, the contact point and whether the anchor is in frame
      (`generation-system.md` §3, §5d; `anomaly-catalog.md` §2), plus a path row for every thrown,
      dropped, swung or passing thing (where it passes the product, or what it hits and the
      consequence) and an occlusion note for every moment something passes in front of or behind
      a tracked object (`anomaly-catalog.md` §2.14);
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
      - the anchor's posture, support and place, with the story reason in one clause
        (`generation-system.md` §4b.1b; `anomaly-catalog.md` §2.16);
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
      - the soundtrack's role, mood, tempo and how its energy moves, read from the references' sound-profile numbers;
      - its source: a supplied track, the reference's own speech-free sound, or a matching track
        to download;
      - the sound effects and their hit points on the new video's beats;
    - for a **multi-clip** video, the **clip plan** (`generation-system.md` §3b):
      - the seams, on the reference's cuts first;
      - the join method of each seam (from `index.json → continuation`);
      - the hand-off state of each seam;
      - the clip durations;
    - the logic and anti-slop gate;
    - the **QC checkpoints** (`anomaly-catalog.md` §3 step 8): every use beat, exit and re-entry,
      occlusion, cut, hand-off, pour and seam, plus the first second (the product in frame at 0.0 s) and
      the last, the product's position against a fixed neighbour at least every 0.25 s, and every
      transition, insert start and end and overlay start and end of the CapCut timeline, each with its time
      range and the counts and states expected there. X9 renders them with `T qc --dense`;
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
    - The product reference is scoped to shape, proportions, colours and label ("do not use its
      lighting, exposure, background or camera angle"), and the prompt states the room's light on
      the product, its size against a named neighbour, its mark angle, its contact shadow like the
      neighbour's and the scene's camera angle; the anchor touches or is partly occluded by
      something rather than standing alone on an empty edge (`anomaly-catalog.md` §2.15).
    - The **size** comes from the plan's size reckoning (`anomaly-catalog.md` §2.7), in the model's
      own phrasing (its guide §3.14): the ratio to the named neighbour at the same depth in words
      ("two thirds the height of the water bottle beside it"), the depth ("on the dresser about
      two and a half metres from the camera, behind him"), the fraction of the frame when the
      model takes it ("a small object in the background, about one twentieth of the frame
      height"), the size ladder when several products show, and the constancy line. The
      reference image is padded so the product does not fill it, and a start frame is built at
      the reckoned pixel height and measured with `T scale --frame … --product-px … --ref-cm …
      --ref-px …` before it is animated. Where the guide lists size as a model limit
      (`wan3_0_prime`), these words are a check, not a control: X1 chose the anchor class from the
      guide's passing list, and a start frame is out of reach while the source rides as a video
      reference.
    - Every vessel's contents are stated from the contents sample ("the glass holds …"); an
      unstated glass comes back as water. A character photo's role is limited to the person ("only
      his face, hair, build and clothing; not the glass, table or background of Image 4") unless
      the plan keeps its props as the product's contents (`generation-system.md` §4b.5).
    - Free physical motion (a spin, toss, roll or pour, or a vehicle's move) is described by its
      physics, never by a schedule of exact times. A required end state gets a visible cause, such
      as a hand stopping the product label-forward or a driver braking into the spot
      (`generation-system.md` §5b). A corrected retry removes timing constraints from free motion;
      it never adds them.
    - Every **use beat** is written as initial state → operation on the named part → observable
      result, with the contact point, orientation and body mechanics of the product's affordance
      sheet ("he flips the cap open with his thumb, puts his lips on the spout and drinks through
      it with his head level"). Every **multiple** carries its number at t=0, at each event and at
      the end, restated after exits, occlusions, cuts, hand-offs and seams. Each product gets **one
      targeted exclusion** for its own wrong use and count ("only through the spout; no other
      opening", "exactly three capsules; none appears or disappears"). No reference image shows a
      later state than t=0 (`anomaly-catalog.md` §3). Every thrown, dropped, swung or passing thing
      has its path written relative to the product, past it on a named side or onto it with the
      consequence, plus the solidity exclusion ("nothing passes through the bottle";
      `anomaly-catalog.md` §2.14).
    - Every **applied caught-error rule** (item 22) is in the prompt in the model's phrasing: a
      positive line plus the model's exclusion syntax, like an anomaly-catalog prompt line.
    - **Guardrail operations** in the model's own edit syntax (`brand-guardrails.md` §4): "Remove
      only the third can at the left end of the desk and reconstruct the desk and wall behind it;
      keep the two other cans exactly as they are"; "Remove only the brand name and logo from the
      green can on the shelf; keep its shape, size, position and lighting; it becomes a plain
      unbranded can of the same colour"; the person-replacement contract for an excluded person.
      Never "blur", "pixelate" or "cover".
    - Analyze Mode prompts are always **clean plates**: no overlay text. The only lettering is the
      product's own label, logo or badge.
    - With inserts, the prompt covers only the generated content, and puts a natural beat boundary
      at each split point.
    - **Fidelity lock** (item 19; Edit Mode and Recreate), in the **first** request and every
      re-edit, in the model's own structure and wording (`generation-system.md` §5c.3):
      - the change scoped with "only", then the full keep-list: the performers, their motion,
        gestures, expressions and mouth movements, the props and how they are handled, the camera
        path and framing, the light, the background and the timing. A swapped item follows the
        original's exact position, path, tilt and grip in every frame. A swapped person keeps the
        source person's movements, expressions and mouth movements on the same frames;
      - ✓ and ↔: no scene re-description, because the source carries the action and the guides
        warn that re-describing invites a regeneration. ≈ and ✗: the source action script is also
        written out in order as plain sentences (who does what, with which hand, how fast, where
        they look, where they pause), sync-anchor beats first when the guide limits length;
      - exclusions: nothing added, skipped, repeated or reordered, no new gesture or camera move,
        no re-staging, no new background action, no change of pace;
      - the guide's most preserving mode and settings (§5c.2) and the source segment's duration
        (E5). The timing comes from the source video, never from timestamps in the prompt.
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
  - **Edit Mode and Recreate with a frames-only model (item 19):** the start frame is the source's
    own first frame with the operations applied, and the end frame, when the model takes one, is
    its last frame with the same operations. The model then interpolates the source's own action.
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
  - **Fidelity check** (item 19; Edit Mode and Recreate; `generation-system.md` §5c.4): walk the
    source action script beat by beat. Every keep beat is carried by the source input or named in
    the prompt. Nothing in the prompt invites new motion. The duration matches the source segment.
    No change operation forces a motion change: a bigger product gets a planned grip that keeps the
    same hand path.
  - **Counts, openings and permanence** (`anomaly-catalog.md` §3): walk every use beat (the
    preparation step, the part, the contact point, the head and hands), every multiple's number at
    every event, every effect's cause, every restatement after an exit, occlusion, cut, hand-off or
    seam, and the path of every thrown, dropped or passing thing relative to the product (§2.14).
  - **Size** (`anomaly-catalog.md` §2.7): every product's reckoning, its distance derived from the
    frame and not assumed, is in the plan and in the prompt for every shot; a start frame was measured
    with `T scale` and its size factors read (X9 gives the bands); the size ladder holds between
    products; nothing in the prompt or the references invites a bigger product (a tight crop, "hero",
    "prominent", a packshot pose).
  - **Posture, support and place** (`generation-system.md` §4b.1b; `anomaly-catalog.md` §2.16): every
    anchor is a posture its shape allows, on a visible support, where a person would leave it, with
    its story reason; no lean on a prop the model has to invent, nothing on a thin sheet, no source
    beat taken over. Where the guide lists size as a model limit, the anchor is from its passing list.
  - **Source surfaces:** each printed surface a guardrail or §9b names is a "replace / remove only …
    reconstruct as <named content>" sentence, never a description of blankness, with the original in
    the exclusion line.
  - Fix any conflict in the plan and the request before continuing.
- **X5 — Preflight.**
  - `generate_video {params:{…, get_cost:true}}` → cost and `adjustments`. **One** preflight per
    distinct request. Preflight again only after the request changed.
  - Reconcile every adjustment: an unsupported or dropped parameter means rethinking the request,
    not ignoring it.
  - Project folder: create it once per run (`list_workspaces` → `create_project`, keyed by the run
    id) and pass `folder_id`.
- **X6 — Brief.**
  - Print the short brief (`generation-system.md` §10): concept, why it works, reference pattern,
    characters/assets, substitutions, main action and states, style/camera, text plan, model /
    operation / duration / 9:16 720p, cost, adaptation logic. In Edit Mode and Recreate it also names
    the fidelity approach (input, mode, written-out script or not) and any risk to fidelity or sync.
  - Save it as `40-briefs/video-NN-brief.md` (an attempt or clip appends its own block under the
    first), so a later caught-error entry can carry it (item 22): `T caught-error add --run RUN
    --video NN` attaches the brief, the newest request's prompt and the plan path by itself.
  - Analyze Mode: no gate; the brief is information (item 15). Edit Mode: the E6 gate.
- **X7 — Submit and wait (ledger-recorded; no spam, no glitches).**
  1. `T ledger begin --run RUN --video NN --attempt K --request 50-requests/video-NN[-aK]-request.json`
     (a clip: `--video NN-cK` with its own request file).
     - It **records a `pending` entry every time** and exits 0; it never refuses. It reports `conflicts[]`
       as facts, with the entries involved: an open submission (pending / submitted / unknown) in this
       video's lane; the submissions in flight in the run against the cap (`open_in_run`, `cap`); this
       exact request failed before; this exact request already produced a finished job. **You decide
       whether to submit**, under the production rules: one job in flight per video, none past
       `production.max_parallel_jobs`, never the same request again once it produced a finished job, and a
       diagnosis before another attempt. Act on what it shows:
       - an open job exists → resolve it with `jobs_wait`, or for `pending` / `unknown` via
         `show_generations {type:"video", only_completed:false, size:5}` and `transactions`;
       - the request is a duplicate of a finished job → reuse that job;
       - the request failed before → diagnose it first; one retry of the identical request is allowed,
         and after a second failure change it or report the failure;
       - if you decide **not** to submit, record that: `T ledger set --run RUN --fingerprint F --status
         superseded --note "<why>"`, which frees the lane.
  2. Exactly **one** `generate_video {params}` call: `count` 1, no `get_cost`, never in parallel with
     anything, never twice in one turn, never inside a retry loop.
  3. Record the outcome at once:
     - a job id came back → `T ledger set --run RUN --fingerprint F --job J --status submitted`;
     - a transport error or timeout with no job id → `--status unknown`. Then find out what happened
       (history and transactions), and set `submitted` with the found job id, or `failed` with the
       note "not created". Only then begin a new attempt (an `unknown` entry counts as an open
       submission in the lane).
     - Handle `unlim_choice` (ask), `recovery_tool` (call it), and validation errors. A validation
       error means nothing was created: set `failed` with the note "rejected before creation", fix
       only the named field, and begin a new attempt.
  4. Poll `jobs_wait {jobs:[{index:0, job_id}], timeout_seconds:15}`, respecting
     `poll_after_seconds`.
     - Terminal → `T ledger set --job J --status completed|failed`.
     - Still running after ~25 min → tell the user, and keep waiting on that same job. Never
       resubmit because a job is slow.
  5. A failed job is refunded. Diagnose it before any retry; retry an identical request at most once
     (`begin` reports a request that failed before, and the decision is yours).
- **X8 — Download and post-process.** `T hf-get` into `60-outputs/video-NN/aK/raw.mp4` (K = the
  attempt number; the raw Higgsfield output is always kept), then as needed, in this order:
  1. **Edit Mode and Recreate — original audio back:**
     `T restore-audio --generated <raw or joined> --audio "<files_audio file>" --audio-offset <audio_offset> [--start <segment start>] --out <aK>/with-original-audio.mp4`.
     The picture is Higgsfield's and the sound is the original's. A clip that is slightly shorter
     keeps sync from the start and cuts the audio at its end; the tool reports `generated_shorter_by_s`
     (a plain difference) and a note. It returns `facts` (`has_video`, `has_audio`, `audio_was_available`,
     `duration_s`, `requested_duration_s`, `size`, `source_size`): read them; `ok` only means ffmpeg
     produced the file. A source that had no audio gives a silent final.
  2. `T conform` → exactly 720×1280 (it reports `lost_fraction`; the crop rule of thumb is in E5);
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
     It measures and returns numbers; it gives no verdict and no fix, and exits 0 whenever it measured:
     `global_offset_s` and `global_corr`, `windows[]` (`t`, `offset_s`, `corr`, `motion_ratio`),
     `windows_used` / `windows_total`, `median_window_offset_s`, `window_spread_s`, `drift_s_per_10s`,
     `windows_beyond_tolerance` (listed against `--tol`, default 0.10 s), `duration_diff_s`, and the
     side-by-side `sheet` (`--min-corr`, default 0.5, and `--min-motion`, default 0.25, only select the
     windows the summary uses; every window stays listed). A positive offset means the output's action
     happens later than the source's sound. View `sync-sheet.jpg` and the sync anchors densified (mouths on
     their words, contact on its impacts), then **decide** with these rules of thumb and write the decision
     and why in the verdict:
     - in sync: the global offset and every used window within the tolerance (±0.10 s) → continue;
     - a steady offset (the spread of the used windows at most twice the tolerance) is fixed in post, with
       no new generation: when the output is late (positive), trim the picture's head by that much, then
       run `restore-audio` again; when it is early (negative), run `restore-audio` again with `--start`
       increased by that much. Then merge and check again;
     - a drift (|`drift_s_per_10s`| × the compared span / 10 above the tolerance) or scattered offsets
       cannot be fixed in post: diagnose (duration, speed, an action added, skipped or reordered) and
       regenerate with the timing lock, a regenerate reason in X9;
     - a global correlation below 0.3, or no used window, is inconclusive (motion too different to
       measure, e.g. a heavy restyle) → judge it on the sheet and the densified anchors.
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
    every visible client asset>" --dense "<label>:<a>-<b>" …` with every QC checkpoint of the plan,
    then view the storyboard sheets and every dense sheet under `<dir>/dense/`. It returns measurements
    beside the expectations and no verdict: `checks` (`duration_s`, `aspect`, `size`, `has_audio`,
    `black_spans`, `freeze_starts`, `expected`, `size_delta_px`, `duration_delta_s`, `aspect_error_pct`,
    `mode`), `planned_text[]` (from `--allowed-text`), `visible_text[]` (every text the OCR saw, with its
    `first_t`, `last_t`, `hits`, `share_of_frames_scanned`, height `y_rel`, `score_mean`, `chars` and
    `band_distinct_texts`), `frames_scanned_for_text` and `dense_checkpoints`. **You** compare
    `planned_text` with `visible_text`, read the sheets, and write the QC verdict (it goes into
    `result.json` and, when an error is caught, into `T caught-error add --qc`). Rules of thumb: a
    duration off by more than max(0.25 s, 5 %) is a duration problem; any black span or freeze needs a
    look; in Edit Mode no source text may remain unless it was explicitly kept; in Analyze Mode only the
    planned text may appear, and anything else is pseudo-text or a copied artifact. Whether a visible text
    is a caption, a fixed overlay, a watermark, a label or noise is your reading of those numbers and the
    picture.
  - Check identity, asset geometry against the canonical template, the ledger states, interactions
    (densify contact moments), lighting and reflections, text, pacing and dead space, and the format.
  - **Motion beats at 30 fps** (`generation-system.md` §5b): every motion beat (spins, tosses,
    pours, landings; a vehicle driving, turning, braking or parking) gets a full-frame-rate sheet
    across the beat. A snap, a pause-and-resume without a cause, a reversal, a slide without a
    cause, or a morphing label, badge or body is a regenerate reason. Product-pun text is timed to
    the measured moment.
  - **Counts, openings and permanence** (`anomaly-catalog.md` §4): count every multiple at every
    checkpoint and write the numbers in the verdict; on every use beat check, at 30 fps, the
    preparation step, the part used (spout, opened top, nozzle, torn end) and the contact point;
    before and after every exit, occlusion, cut and seam compare count, spot, state, size and label
    orientation. A count or state that changes without a cause, a use through a part with no
    opening or a closed one, and an effect before its cause are regenerate reasons. The only
    post-fixes are the catalog's: a pixel hold on an untouched static anchor in a locked shot, a
    one-frame trim, a recolour or punch-in in a locked shot.
  - **Size** (`anomaly-catalog.md` §2.7): on a full-resolution frame at rest, one in use and the
    last, measure the product's pixel height and the named neighbour's at the product's own depth (`--depth-ratio`
    from the frame when the product stands in front of or behind it, never 1 by default) and run
    `T scale --product-cm <H> --product-px <y0-y1> --ref-cm <h> --ref-px <y0-y1> [--depth-ratio r]
    --distance d --distance-basis "<how d was derived from the frame>" --lens f`. It returns numbers and no
    verdict: `estimates[]`, two of them when both can be made, the neighbour ratio (A) and the frame
    fraction at a distance derived from the surface or another object (B), each with its `size_factor` (the
    observed size as a multiple of the expected size) and `deviation_pct`; also `size_vs_neighbour`,
    `size_vs_distance`, `estimates_spread_pct` (when there are two), the expected and observed values and
    `distance_basis` as you gave it. **You** read them under the guidance: within 15 % is fine; 15–25 % is a
    note, only for a static product with a readable label; over 25 % on agreeing estimates, a size that
    changes between shots, or a product larger than the hand that holds it is a regenerate reason with no
    post-fix; two estimates more than 25 % apart are inconclusive, so re-derive the distance and measure
    again on the full-resolution frame. A size read from one assumed number, with no neighbour estimate, is
    PROVISIONAL (your own label, "provisional: distance assumed"): not a regenerate reason or a RESIDUAL
    FAILURE until a second estimate agrees, and viewed on the full-resolution frame by whoever reports it
    before it is flagged, repeated or summarised (CE-028). Write the multiple of the expected size with its
    method and distance in the verdict and compare across cuts. The retry changes the lever the guide
    names. For a model whose guide lists size as a model limit (`wan3_0_prime`) it changes the form or the
    anchor class from the guide's passing list, never the sizing words (12 of 12 wording retries were
    re-rolled); otherwise it names the neighbour and the ratio, the depth and the fraction of the frame,
    pads the reference and rebuilds any start frame. A second miss ships the best take flagged and is
    recorded.
  - **Blend** (`anomaly-catalog.md` §2.15): on one full-resolution frame at rest and one in use,
    the eleven-sign paste test against the nearest neighbour at the same depth (whites against the
    nearest white object, light direction, contact shadow, sharpness and grain, packshot pose,
    perspective, scale, edges, footprint, depth of field, prominence), written in the verdict. Any
    sign is the "looks pasted in" regenerate reason; the retry fixes the named cause. A local
    regrade is the only post-fix, for a static untouched product failing on exposure alone.
  - **Solidity** (`anomaly-catalog.md` §2.14): at 30 fps wherever anything passes near, in front
    of or behind the product, lands on it or hits it. A pass-through, a sinking, a see-through, a
    wrong occlusion order or a hit without a consequence is a regenerate reason with no post-fix.
  - **Posture, support and place** (`anomaly-catalog.md` §2.16): at 30 fps on every rest and every
    pass of a hand or sheet: the posture, the whole underside on a visible support, the clearance to
    a working hand or arm, the sheet region when paper is near; the story reason is its own line of
    the verdict. A lean against nothing, an impossible posture, a pack touching a working hand or
    arm, a warped sheet or a taken source beat is a regenerate reason with no post-fix.
  - **Anchor from frame 0** (`anomaly-catalog.md` §4 step 5f): the placed or contents product is in the
    dense sheet of the first second and in every second after it, and its position is read against a
    fixed neighbour at least every 0.25 s across the whole clip and every cut. Absent in the opening
    seconds, or moving with no action and no motivating cut, is a regenerate reason and never a flagged
    note (CE-018, CE-019). Verdict line: "anchor: in frame from 0.0 s; drift vs <neighbour> <px>".
  - **Assembled timeline** (`anomaly-catalog.md` §4 step 5g; fixed in the CapCut project): dense sheets
    of every transition, insert start and end, overlay start and end, and the first second of the final:
    no frame of the replaced performer, no frozen or held frame, no stray rectangle, halo or brightness
    step; every context-bearing source overlay present as the original element; a Recreate's original
    audio one whole untouched segment (hash or null test); no emoji in a text layer (CE-016, CE-017,
    CE-023, CE-024, CE-025, CE-026).
  - **Source surfaces:** each printed surface a guardrail or §9b names, at full resolution and by
    `T qc` OCR; a reproduced one is a regenerate reason, and the retry replaces it with a named
    concrete thing.
  - **Creative check** (`creative-direction.md` §8), as notes: the hook within the first second,
    the payoff where planned, the product recognisable at the moments of attention without reading
    as an ad, the planned emotion arc, the loop; Create: the copy test against the references
    the blend borrowed from and the run's other videos (craft shared, subject not). A missing hook or payoff that
    the plan required is a narrative-gate failure and a regenerate reason; everything else is a
    note, never a question.
  - **Action sync** (item 19; Edit Mode and Recreate): your sync reading from X8 (the numbers and the
    sheet). Every sync anchor should land within ±0.1 s of its sound: words on mouth movements, impacts on
    contact, steps on footfalls. Drift, or an action added, skipped or moved, is a regenerate reason; a
    steady offset is a post-fix.
  - **Leftovers** (`generation-system.md` §9b): only the must-not-survive list counts, and it is
    fixed autonomously.
  - **Caught errors** (item 22): each applied entry checked by id and written in the verdict
    ("CE-004: paste test 0 signs"; "CE-005: can at 1.05× expected vs the bottle"); a failed check
    is a regenerate reason when the entry's class says so. Every regenerate reason found here is
    recorded at once, compact and complete for the next run's agents: `T caught-error add
    --source agent --title "<short title>" --run RUN --video NN --mode … --model … --product "…" --assets "<asset paths +
    key specs>" --prompt <the failed request.json> --errors "<execution errors, adjustments,
    moderation>" --evidence "<checkpoint, t range, sheet path>" --title "…" --wrong "<the
    verdict>" --class "<reference §>" --cause <…> --rule "<general rule>"`. The working prompt is
    inserted **only after the new generation passes QC**: `T caught-error set --id CE-nnn
    --verified-prompt <the passing request.json> --qc-pass "<the passing verdict>"` (the tool needs that
    verdict as `--qc-pass`; it checks only that you gave one). If the retry fails too, the entry stays
    open with no fix. A new failure the user later reports becomes a user entry, never a silent fix.
  - **Guardrails** (`brand-guardrails.md` §5): the count limit at every checkpoint; `T qc` OCR
    with no competitor name and a full-resolution look at every de-branded object (no logo,
    claw, crest or livery, no blur, no patch); the identity check over every shot, reflection and
    placed-back insert; the rewritten lines and disclaimers on the CapCut preview. A leftover hit
    in the picture is a regenerate reason with the operation named; in a text layer, a CapCut
    fix. A removed element that turns out to have been handled is reported and the pick is
    replaced by the next runner-up when the run allows it.
  - **House approach** (when examples exist): the video follows the rules its plan applied.
  - **Contents** (`generation-system.md` §9): every vessel of the product's category shows the
    product's contents. A glass of water beside the can is a regenerate reason, never a note.
    - Must not survive: the copyright and ownership floor only (the replaced person, the swapped
      or competitor product, overlay text, handles, platform logos and watermarks, featured
      third-party branding, a copyrighted character as the subject), what the generation service
      refuses, and the hits a client guardrail names.
    - Background decor, clothing logos, meme faces and all brand-dependent content that no
      guardrail names are fine. They are not reported, not asked about, never softened and never
      cost a retry. In Analyze Mode no QC question ever goes to the user.
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
    - overlays exist only on their visible frames and fade with the picture; a Recreate's original audio
      is one segment; no text layer contains an emoji;
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
     - the sync reading (item 19), always: the measured offsets (global, and the spread and drift of the
       windows) and the sheet's path. A drift or scattered offsets come first, with the moments that
       miss their sound.
  2. Ask with AskUserQuestion (header "Review"), "Video N, attempt K — is it okay?":
     - **"Looks good — next video"** → `T ledger set --job J --status accepted`, then X10, which
       places the approved video in the `final` folder.
     - **"Needs changes"** → ask in plain chat what to change, and let them add or replace files.
       Record it before re-editing: `T caught-error add --title "<short title>" --mode edit --video <N> --run <RUN>
       --model <id> --user "<their words>" --wrong "<diagnosis>" --class "<reference §>"
       --cause <…> --rule "<general rule>" --qc "<the X9 verdict and its reasons>"` (item 22;
       the brief, the attempt's prompt and the plan attach themselves from the run); the fix is
       set on the entry once the next attempt is approved (`T caught-error set --id CE-nnn
       --status fixed --fix "<what changed>"`).
     - **"Stop here"** → keep the files, go to the wrap-up.
     "Other" lets the user type the changes directly.
  3. **Re-edit from the original.** A new attempt always starts from the **original source video**
     (the same prepared 9:16 source, already uploaded; its media id is reused), never from the
     previous output. It uses the same per-edit files plus any new ones: re-run `inventory` for scope
     `video-NN` with the full path list.
     - Fold the feedback into the plan and the request (the item 19 fidelity lock stays), and save them as
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
    - It never refuses the user's approval. It returns `facts` (`has_video`, `size`, `expected_size`,
      `has_audio`, `original_has_audio`): read them (picture present, 720×1280, audio present exactly
      when the original had audio) and report any mismatch to the user.
    - The folder is marked so later scans skip it. A previously approved final of the same video is
      moved into the run folder, never overwritten silently.
    - Only approved videos are placed there.
  - **Analyze Mode** (`capcut-assembly.md` §6):
    - the **CapCut project** `DD_Mon_YYYY_vNN` is the master; the final is exported from CapCut;
    - `RUN/deliverables/video-NN-clean.mp4`: the same edit with its inserts and without text,
      assembled locally from the pieces, the inserts and (Recreate) the original audio, and never
      replaced by the generated-only `60-outputs/video-NN/clean.mp4` when the video has inserts;
    - `RUN/deliverables/video-NN-preview.mp4`: the CapCut proxy with the text.
  - Append a row to `RUN/deliverables/README.md` (an agent writes it to
    `60-outputs/video-NN/readme-row.md` and the main session appends it as the agent reports, A9b): direction, model, params, prompt file, assets, job
    id, attempt, credits, verdict, final path, notes. For a multi-clip video, list every clip's
    job id and the seam methods. Analyze Mode adds the CapCut project name, the inserts and the
    text events.
  - Update `state.json` (`videos[]`, `next_step`), then move to the next video. In Edit Mode, only
    after the user said "Looks good".

## 6. Wrap-up (both modes)

Viral-Browser has its own wrap-up (V9); this section and §6b are for Edit Mode, Recreate and Create.

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
- the guardrails applied ("G1–G5 from brand-rules.pdf; 2 references dismissed: V04 (G1, the gore
  is the prank), V09 (G3, a taste test); 3 picks edited: counts, de-branding, face swaps") or
  "no guardrails supplied";
- only if `config.json → capcut.text_style.learned` is ever empty (it holds the user's locked
  preset): "To copy CapCut's exact text preset, add a text in any CapCut project, pick the preset,
  close CapCut, and run `T capcut-text-style --learn --draft "<store>/<that project>"`";
- any open issues.

Analyze Mode: reconcile the ledger before the feedback question. Every `result.json` whose `qc`
says RESIDUAL FAILURE or regenerated, and that has no entry in `T caught-error list --grep <RUN>`, is
recorded now with `--source agent` (compact; one entry per class and anchor, the videos listed), so no
flagged delivery leaves the run unrecorded.

Analyze Mode: before the table, check the run's deliverables and text. Every video in `state.json` →
`videos[]` has `video-NN-clean.mp4` and `video-NN-preview.mp4` in `<RUN>/deliverables/` (all videos in that
one folder; a with-inserts clean built from the pieces, the inserts and the original audio, never
overwritten by a generated-only clip) and a row in `deliverables/README.md`; the plan and brief files carry
every attempt; no CapCut text layer of any project contains an emoji (the user's rule, strict); and every
size figure in the table was viewed on a frame with its method (two estimates, a derived distance), never
repeated from an agent's provisional number. What is missing is fixed before the table is shown.

Create: write `RUN/deliverables/blends.md` from `concepts.md` and the plans, one row per video: the mechanism(s) M#
(k of n, grade), the product truth PT#, the audience trigger, the hook type and its timing, the trend element, the share
line and the honest risk. It shows what each video tests, so that results can be attributed to a mechanism, a hook or a
truth; the chat table gets a "blend" column from it.

Offer, in one line, the next useful step (more videos, a different direction, regenerate a flagged
video). Then, once every video is delivered, **ask for feedback** with AskUserQuestion (header
"Feedback"), "Watch the videos: is any of them not right?": **"All good"**; **"I'll watch them
later"** (any later message about them is still recorded); **"Some need fixes"** → ask in plain
chat which video and what is wrong, disliked or illogical. "Other" lets the user type it
directly. Each problem named, now or in a later session, is recorded with `T caught-error add
--source user --title "<short title>" --run RUN --video NN --user "<their words>" …` (one entry per problem, the brief,
prompt and delivered details attach themselves) before the fix is offered (item 22). When the
ledger now holds two or more open or fixed entries of one class, model or product family, add one
line: "Run `/update-from-errors analyze-then-generate` to generalise these into the prompting and QC."

### 6b. Upscale the finals with Topaz (after the user's approval, both modes)

Once the generated videos and the editing are done, and after the feedback question, offer the
upscale. It runs only on the user's yes, never on its own, and never before the finals exist.
- **The folder.** Edit Mode: `<given path>/final/`. Analyze Mode: the folder the user exported
  the CapCut projects to; the pipeline does not know it, so the question asks for it (the clean
  videos in `60-outputs` are not the finals and are never upscaled unless the user names that
  folder).
- **Ask** with AskUserQuestion (header "Upscale"), "Upscale the final videos 1.5x with Topaz?":
  **"Yes, <folder>"** (Edit Mode: the final folder; Analyze Mode: "Yes, after I export: here is
  the folder" and the user types the path under "Other"); **"Not now"** (say the two commands so
  the user can run them later). Never run on "Not now".
- **Run**, in one PowerShell call, exactly these two commands with the folder filled in (the
  `-notmatch` filter skips files already upscaled, `…_1.5x.mp4`, so a rerun is safe; the script
  writes `<name>_1.5x.mp4` beside each source and `-Yes` skips its cost prompt):
  ```powershell
  cd "$env:USERPROFILE\Scripts"
  Get-ChildItem -Path "<folder>" -Filter *.mp4 | Where-Object { $_.Name -notmatch '_[\d.]+x\.mp4$' } | ForEach-Object { .\topaz-upscale.ps1 -InputFile $_.FullName -Scale 1.5 -Yes }
  ```
  The script needs `ffprobe` on PATH and `TOPAZ_API_KEY` set; if it stops on either, report the
  real error and the fix (`winget install Gyan.FFmpeg`; `setx TOPAZ_API_KEY "<key>"`, then a new
  window). It polls Topaz itself; run it in the foreground with a long timeout (10 minutes), and
  if the call times out, check the folder for `_1.5x.mp4` files before anything is rerun.
- **Report** the upscaled files (name → size → path) and any file that failed, with its error.
  Never retry a failed upscale on its own: say what failed and ask.

## 7. Never

- Never use or create a Claude Code Workflow.
- Never take a script's output for a decision. The `T` scripts gather, extract, record, tabulate and
  calculate; you read what they return, decide under the mode's rules (their numbers are rules of thumb),
  and record the decision with its reason (`--by` / `--reason`, the bias log, the caught-error ledger,
  `ledger set --status superseded --note`). Never lower a gate or set a rule of thumb aside silently.
- Never spawn more than 2 analysis agents, more than 5 production agents at once, or a production
  agent in Edit Mode; in Viral-Browser never more than 3 research agents at once, plus one niche-audit
  agent, one scoring agent and one red-team agent, and, after the picks, up to 3 reference-pack
  agents (never alongside the research agents), and no production agent. Never give agents
  overlapping work.
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
- Never re-type a context-bearing source overlay as text (CE-017, CE-023), never drop a keyword the user
  keeps (CE-027), never change a caption's subject to clear a guardrail (CE-022), and never give a brand a
  scene it has no tie to when the other brand fits (CE-020).
- Never let the video model render overlay text in Analyze Mode. Generate clean and place the text
  in CapCut. Never burn it in with `atg.py captions`, except as the stated fallback.
- Never give a CapCut text layer another font, size, colour or preset than the house text style
  (font System, size 10, the user's locked preset in `capcut.text_style.learned`), unless the user
  asks for it in the run. Never re-learn or replace that preset (`--learn --replace`) unless the
  user explicitly asks for a new one. Never place a text layer off-centre horizontally (posX ≠ 0):
  only its height follows the reference.
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
  visible action, be missing from frame 0 (CE-018), drift along its surface with no cause (CE-019),
  become the hero of the shot, or look composited.
- Never leave a glass, cup or other vessel of the product's category holding something else (water
  beside the can) when the product's contents fit, and never let a prop from an asset photo carry
  over unplanned.
- Never sacrifice temporal or physical continuity to imitate an individual source frame.
- Never deliver a with-inserts video whose timeline or original audio was shortened, spliced or held on a
  frozen frame (CE-024, CE-025), whose insert edges show the replaced performer (CE-016), whose overlay
  outlives its element or its fade (CE-026), or whose text layer holds an emoji.
- Never accept a product that fails the paste test: brighter, cooler, sharper or cleaner than its
  neighbours, lit from the front in a room lit from elsewhere, without a contact shadow, squared to
  the lens, at the wrong size or perspective, or alone on an empty edge (`anomaly-catalog.md`
  §2.15). Never bind a product reference without scoping out its lighting, exposure, background
  and camera angle.
- Never let anything pass through the product or any other solid thing, sink into a surface or a
  hand, show through an opaque body, or hit something without a consequence
  (`anomaly-catalog.md` §2.14).
- Never plan a Create video from a single unscored idea, a generic "person enjoys product" beat,
  an explained joke or a dated surface element; never let two videos of a run share a situation or
  a joke; never let the creative layer override a hard rule (`creative-direction.md`).
- Never run the Topaz upscale without the user's explicit yes in the wrap-up, never run it on
  the clean generations instead of the finals, and never rerun or retry it on your own (§6b).
- Never start a run without reading `ATG/caught_errors.md` (A1 / E1), never leave a video the
  user reported as wrong unrecorded, never write an entry by hand or without the user's words
  verbatim and a general rule, and never silently fix a reported problem without its entry
  (item 22).
- Never tell an agent not to record: the shared contract carries the recording rule, and a run is
  never closed with a RESIDUAL FAILURE or a regenerated video that has no ledger entry (A9b, §6).
  Never copy an agent contract from an earlier run: it is generated at A9 from
  `reference/production-agents.md` §2.
- Never retry a size miss with the sizing words on a model whose guide lists size as a model limit,
  never plan a pack that leans on a prop the model has to invent, stands on its edge against a
  person or rests on a thin sheet that hands move, and never let a placed product take a beat of the
  source (`generation-system.md` §4b.1b).
- Never blur, soften, crop out, remove or avoid content that no client guardrail and no copyright
  floor names (meme faces, alcohol, weapons, fake blood, profanity, cameos, …); the floor (the
  replaced person, the swapped or competitor product, overlay text and handles, platform logos
  and watermarks, featured third-party branding, copyrighted characters as the subject) and the
  generation service's blocks always stand, and a brand rule never removes them
  (`generation-system.md` §9b).
- Never pick a reference whose core a guardrail bans, and never dismiss one for a peripheral hit
  that an edit removes without changing what the video is about; never blur, pixelate or cover a
  competitor's mark (remove it and keep the object); never leave an excluded person's face in any
  shot, reflection or placed-back insert; never leave more units than the limit in any frame;
  never invent a guardrail, and never let one relax a hard rule (`brand-guardrails.md`).
- Never restage a reference in Create: its premise, setting, characters, action order, joke,
  lines, caption wording, props, first frame, ending or product beat. Create collects a
  reference's style, properties, approach, crafting and hook logic, and makes another video with a
  new subject and a new idea; a seed that fails the copy test is rewritten or dropped
  (`creative-direction.md` §5.0). Never plan a Create video that is one family's template with the
  product swapped in, or one that ignores the product's own strengths: every seed names its blend
  and passes the blend and template-lock tests (§5.0b).
- Never let the references' product category, forms or names decide a Create concept (a corpus of pet tools does
  not make a pet video); never borrow a mechanism whose driver is not the craft (a creator's reach, paid reach, a
  known brand, bait, a season); never state that a video will go viral or quote a reach or sales figure that no
  source gave (`viral-browser.md` §14.2, §14.6).
- Never let a multiple change its number without a visible cause: three capsules on a desk are
  still three after the character walks past and comes back, unless they are seen being taken
  (`anomaly-catalog.md` §2.1, §2.5).
- Never let a product be used through a part that has no opening, through a closed one, or before
  the step that readies it: a straw bottle is drunk through its spout with the cap flipped open, a
  can from its opened top after the tab is lifted (§2.2, §2.3).
- Never render a product without its size reckoning (real dimensions, depth, lens, a named
  neighbour's ratio, the size ladder) in the plan and the prompt; never read a product's size off
  its own photo; never take the distance from an assumption (derive it from the frame, with two estimates
  that agree), and never flag, repeat or summarise a size verdict that rests on one assumed number or that
  nobody viewed on a frame (it is provisional, CE-028); never accept a product over a quarter larger or
  smaller than reckoned, one that
  changes size across a cut, or one larger than the hand that holds it (`anomaly-catalog.md` §2.7).
- Never plan a product that is handled on screen without its affordance sheet in the registry
  (§1), and never run X9 without the plan's QC checkpoints rendered dense (`T qc --dense`).
- Never stretch to reach 9:16, never ask for aspect ratio or resolution, and never deliver anything
  other than 720×1280.
- Never upload an original video with its audio to Higgsfield: use the `videos_without_audio` copy
  (or its prepared derivative).
- Never deliver an Edit Mode result with generated audio. It always carries the original audio from
  `files_audio`, or no audio if the original had none.
- Never send an Edit Mode or Recreate request, the first one included, without the fidelity lock
  (item 19): the change scoped with "only", the full keep-list, the exclusions and, for models that
  rebuild the action, the source action script written out in order.
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
- Viral-Browser: never generate anything. No model pick, no Higgsfield generation tool, no credits, no
  CapCut project, no request for client assets, no `split-audio` or any other change to the
  references folder; never start Create without the user's yes (item 25, `viral-browser.md` §11.4).
- Viral-Browser: never let the references' product niche decide the answer (item 24, `viral-browser.md`
  §5). Never build the pool from "more of what the videos show"; never start research on a pool you have
  not read for balance (fewer than 6 niches, one niche above 40 %, or more than half the candidates from
  the references' own products is a departure to repair, or an exception to write down with its reason in
  the bias log); never put a candidate's origin in a research dossier, a research prompt or
  a scoring pass; never count reference-derived evidence as independent; never skip the defence note
  of a dominant-niche pick; and never exclude the dominant niche for being dominant.
- Viral-Browser: never type a niche, category, product or brand name into a script or a config (the
  agents decide them from the data and record them with `T niches`); never start research on a niche
  vocabulary that no fresh agent has audited (`T niches audit` records it; no script flags look-alike
  names); never leave a possibly split niche without a merge (`T niches merge --reason`) or a written
  reason in the bias log for keeping it apart; never record an audit that no fresh agent made; never
  rate in this session (the fresh scoring agent rates); never change a candidate's status, ratings or
  pick order without `--by` and `--reason` (the toolkit sets none by itself), never type an economics
  figure by hand (`T econ --cand` records it), and never change a researched candidate's name, type,
  definition or niche without a stated reason; never record the picks before the red-team readings and the
  defence notes exist, or from `T viral-stats` tables older than the niche vocabulary (run it again after
  a merge or a new mapping).
- Viral-Browser: never state a number without its source and retrieval date or its method; never score
  "unknown" as 3; never count a grade D row; never invent a URL, a quote or a figure; never present an
  estimate as a measurement; never credit a product with what the creator, a trend or paid reach
  carried; never take attention for buying evidence; never claim EU or global demand from US-only
  evidence without the market-gap flag (`viral-browser.md` §0, §2, §3.2).
- Viral-Browser: never lower a gate silently to fill the table (fewer than 3 candidates meeting the gates
  is a valid result; any gate you relax is named in the report with its reason), and never show a pick
  without its confidence and what would change the call.
- Viral-Browser: never buy, sign up, log in, message a seller or submit a form; never collect personal
  data; never use a browser tool unless the user chose "web plus my Chrome", and then only to read
  pages (`viral-browser.md` §0 rule 6, §7.5).
- Viral-Browser: never read a size or weight off a photo; never give a specification fact without its
  source, kind, grade and date, and never call a single listing verified; never download an image (the
  packs hold links); never read a page or probe a link behind a login or past a block (401, 403, 429),
  or by another route after one; never call an angle verified when nobody looked at the image; and
  never present a web image as rights-cleared or as the user's own asset (`viral-browser.md` §9.1).
- Viral-Browser: never invent an exclusion. The user's exclusions come from the user alone, and the
  compliance, platform and IP screens are viability checks, never taste (`viral-browser.md` §0 rule 5).
  Never recommend fake scarcity, fake or undisclosed incentivised reviews, unprovable claims or any
  deceptive tactic in a blueprint (§0 rule 7).
- Never claim results you did not verify.
