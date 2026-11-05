---
name: atg-analyze-study
description: /analyze-then-generate Analyze Mode phase: video analysis, synthesis, house approach, video count (A3–A5). Internal to that command.
user-invocable: false
---

# atg-analyze-study — Analyze Mode: analysis, synthesis, count (A3–A5)

> `ATG` = `C:/Users/Bulzart/.claude/analyze-then-generate` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- analysis-protocol §0: `ATG/reference/analysis-protocol/010_0_provenance-labels-use-everywhere.md` (0.6 KB)
- analysis-protocol §1: `ATG/reference/analysis-protocol/020_1_inputs-per-video-produced-by-atg.md` (1.9 KB)
- analysis-protocol §2: `ATG/reference/analysis-protocol/030_2_reading-a-video-as-one-continuou.md` (6.5 KB)
- analysis-protocol §3: `ATG/reference/analysis-protocol/040_3_per-video-card-20-analysis-cards.md` (9.0 KB)
- analysis-protocol §4: `ATG/reference/analysis-protocol/050_4_effectiveness-lenses-apply-those.md` (2.1 KB)
- analysis-protocol §5: `ATG/reference/analysis-protocol/060_5_cross-video-synthesis.md` (6.5 KB)
- analysis-protocol §6: `ATG/reference/analysis-protocol/070_6_project-inference-20-analysis-pr.md` (2.6 KB)
- analysis-protocol §7: `ATG/reference/analysis-protocol/080_7_scale-and-delegation-2-analysis.md` (2.7 KB)
- analysis-protocol §8: `ATG/reference/analysis-protocol/090_8_presenting-results-to-the-user.md` (0.2 KB)
- analysis-protocol §9: `ATG/reference/analysis-protocol/100_9_examples-the-user-s-own-videos-t.md` (3.1 KB)
- creative-direction §1: `ATG/reference/creative-direction/010_1_the-roles.md` (2.3 KB)
- creative-direction §2: `ATG/reference/creative-direction/020_2_the-goal-model-written-into-20-a.md` (1.4 KB)
- creative-direction §3: `ATG/reference/creative-direction/030_3_the-audience-model-mass-cognitio.md` (3.7 KB)
- creative-direction §4: `ATG/reference/creative-direction/040_4_the-trend-read-written-into-20-a.md` (2.0 KB)
- *Create only (the craft sheet):*
  - creative-direction §5.0: `ATG/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (5.1 KB)
- *Create only (the virality mining: the same mining as Viral-Browser's, without its market work):*
  - viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB)
  - viral-browser §3.1: `ATG/reference/viral-browser/050_3.1_how-to-read.md` (1.6 KB)
  - viral-browser §3.2: `ATG/reference/viral-browser/060_3.2_the-card.md` (13.3 KB)
  - viral-browser §4.1: `ATG/reference/viral-browser/120_4.1_measure-first.md` (2.5 KB)
  - viral-browser §4.2: `ATG/reference/viral-browser/130_4.2_mechanism-map-20-analysis-mechan.md` (1.1 KB)
  - viral-browser §4.3: `ATG/reference/viral-browser/140_4.3_hooks-length-and-pacing.md` (1.0 KB)
  - viral-browser §4.4: `ATG/reference/viral-browser/150_4.4_engagement-style-the-approach.md` (0.6 KB)
  - viral-browser §4.5: `ATG/reference/viral-browser/160_4.5_audience-and-mentality.md` (1.3 KB)
  - viral-browser §4.6: `ATG/reference/viral-browser/170_4.6_what-hooked-them-the-essence-20.md` (1.1 KB)
  - viral-browser §4.7: `ATG/reference/viral-browser/180_4.7_confounds-survivorship-and-small.md` (0.6 KB)
  - viral-browser §4.8: `ATG/reference/viral-browser/190_4.8_trend-read.md` (0.7 KB)
  - viral-browser §4.10: `ATG/reference/viral-browser/210_4.10_files-for-a-later-create.md` (0.4 KB)
  - viral-browser §13.6: `ATG/reference/viral-browser/520_13.6_create-card-agent-subagent-type.md` (2.8 KB)
  - viral-browser §14.1: `ATG/reference/viral-browser/550_14.1_what-create-takes-what-it-skips.md` (1.8 KB)
  - viral-browser §14.2: `ATG/reference/viral-browser/560_14.2_only-what-the-craft-carried-is-b.md` (1.0 KB)
  - viral-browser §14.3: `ATG/reference/viral-browser/570_14.3_the-blend-matrix-20-analysis-ble.md` (1.6 KB)
  - viral-browser §14.5: `ATG/reference/viral-browser/590_14.5_the-create-trend-pass.md` (0.9 KB)
  - viral-browser §14.6: `ATG/reference/viral-browser/600_14.6_what-the-mining-never-does-in-cr.md` (0.4 KB)
  - creative-direction §5.0b: `ATG/reference/creative-direction/070_5.0b_blend-not-mimic-reference-craft.md` (3.1 KB) *(read in `atg-analyze-prepare` when the product insights were written; not read again)*
- brand-guardrails §3: `ATG/reference/brand-guardrails/030_3_the-guardrail-audit-per-referenc.md` (3.2 KB)
- generation-system §4b.1c: `ATG/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- generation-system §5c.1: `ATG/reference/generation-system/240_5c.1_the-source-action-script-card-th.md` (1.2 KB)
- generation-system §5c.2b: `ATG/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.2 KB)
- anomaly-catalog §2.1: `ATG/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.2 KB)
- anomaly-catalog §2.2: `ATG/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (2.8 KB)
- anomaly-catalog §2.5: `ATG/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
- anomaly-catalog §2.14: `ATG/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.3 KB)

### A3. Video analysis (as continuous sequences)
- **Create: virality mining** (`viral-browser.md` §14). Each card is also a **viral card** (§3.2), so a reference is read
  once: the product layer kept apart from the mechanism layer (the product layer is recorded and then discarded), the
  ranked drivers of spread (craft / product / creator / trend / paid / bait / timing) and attention-only versus
  commerce-proven, the one-sentence product-agnostic mechanism with its product dependence and transplant needs, the
  audience (awareness stage, the pain or desire) and its mentality (the mental shortcuts, the emotion at the hook, the
  middle and the payoff, what got them hooked), the engagement mechanics, commerce signals when a metrics file is
  supplied, and the one-line `Facts:` JSON (its `category` optional; `voice_type` and `shots_seen` as in the card
  spec). The agents open with the persona block (`viral-browser.md` §1). Recreate keeps the plain protocol card.
- Follow `ATG/reference/analysis-protocol/` (the sections named in Read now) exactly. For each video:
  - read `video.md` and `timeline.md`;
  - view **every** storyboard sheet in order, reading the timeline beside it, and state in the card "sheets seen n of n"
    (a sheet that did not display is read again before the card is written);
  - densify with `T frames … --range a-b --fps 15 --sheet` around fast actions, cuts, interactions,
    gestures, product appearances and text appearances;
  - write `20-analysis/cards/<V>.md`, including (protocol §2.9–§2.11, §3):
    - its **client-entity fit**:
      - **swap**: its analog in the same form exists;
      - **contents**: the product's category sits in another vessel whose action matters;
      - **placement**: nothing analogous.
      For contents and placement, also record the placement opportunities: free or busy hands and
      each hand's lane over the whole clip, nearby surfaces, the region that stays bare and in frame along
      the whole camera path, and the light on them (`generation-system.md` §4b.1c).
    - its **source preparation flags** (`generation-system.md` §5c.2b; protocol §3): a mirrored selfie, burned-in
      text on a flat surface, a real person's name or a patch on screen, a baked face effect, the cut
      structure (many hard cuts, a person alternating with person-free shots), the camera path;
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
    - its **overlay text**: wording, role, centre position, in and out times, and style. The OCR spans (`ocr.json`,
      `video.json`, `video.md`, `timeline.md`) carry numbers and spelling facts only: `text`, `first_t`, `last_t`,
      `hits`, `share_of_frames_scanned`, `y_rel`, `band`, `band_distinct_texts`, `band_frames`, `score_mean`, `chars`,
      `words`, `has_at_handle`, `has_hashtag`, `has_url_pattern`, and `bands[]` per row of the frame. No script says
      whether a text is a caption, a fixed overlay, a watermark, a handle, a label or noise: you decide that from the
      numbers and the storyboard;
    - its **audio context** (every mode; `analysis-protocol.md` §2 item 4): the `Audio context:`, `Said:` and
      `Words and sound together:` lines, from `20-analysis/audio-context.md` and the transcript (context only in
      Recreate);
    - its **sound design** (every mode; Create builds its sound layer from it):
      `T audio-profile --audio "<files_audio file>" --out 10-media/<V>/audio-profile.json --transcript 10-media/<V>/transcript.json --cuts 10-media/<V>/cuts.json`.
      It returns numbers only: the speech share and the audible non-speech share, the harmonic share outside speech,
      the tempo and beat strength, the spectral flatness (near 0 tonal, near 1 noise-like), the strongest frequency and
      how steady it is (near 1 = one steady tone, such as a beep), the energy per second and from the first to the last
      third, and the hits (each with whether it lands on a cut). From those numbers, the transcript and the visuals,
      you decide whether there is a music bed, whether the sound is speech-free and so reusable whole, how its energy
      moves, and its role: dramatic, comic, suspense, hype or sound-effect-driven. The card records that judgement.
    Videos that have nothing to do with the client's product are kept and analysed like any other.
    Their mechanism is still useful, and the product is integrated into them later.
- Delegate to 1–2 agents only per §7 of the protocol, with disjoint video lists. Give them the
  one-line client-entity summary from the registry. In Create use the prompt of `viral-browser.md` §13.6 (the persona
  block, the goal, the viral-card rules). When the cards are written, run
  `T audio-context --run RUN --check --cards` (A1) and add what it lists.
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
  (the subject). Ideation reads only the collected column, together with the mechanism map, the blend matrix and the
  product insight sheet (`30-assets/product-insights.md`, A2b; `creative-direction.md` §5.0b, §5.0c);
- **Create: the virality synthesis** (`viral-browser.md` §14.1–§14.5), from the cards, product-free:
  `T viral-stats --run RUN --no-niche` (the measured length, hook, pacing, speech, text, music and loop profile, in
  `20-analysis/corpus-profile.md`); `20-analysis/mechanism-map.md` (mechanisms M#, k of n, driver, strength,
  independence of the product, transplant needs, confounds, graded hypotheses); the hook, length and pacing ranges; the
  engagement style; the audience and mentality model with the mass-thinking patterns the material uses;
  `20-analysis/viral-essence.md`; the trend read with the Create trend pass (up to `analysis.create_trend_checks` dated
  searches: the references' formats, and the client's product niche and market); and the **blend matrix**
  `20-analysis/blend-matrix.md` (the mechanisms that pass the driver test, set against the product truths PT# and
  affordances of `30-assets/product-insights.md`, with an audience-fit judgement per cell). Only available cells reach
  ideation;
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
  - **Create** presents them as style groups, plus hybrid groups that blend several families with the product's
    strengths (A6).
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

## Rules this phase owns (contract items 18, 20, 21)

18. **Examples: the user's own finished videos (optional, both modes).** They are asked for with the
    other inputs (`atg-start`, step 5). The folder may be empty or absent; then nothing changes.
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
    catalog); it decides which references, mechanisms and concepts win inside them. In Create the same persona block
    opens every analysis and ideation prompt (a growth strategist, a direct-response specialist, a mass-cognition
    engineer, a trend analyst), and the references are mined for why they spread before anything is written
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

## Never (this phase)

- Never upload, recreate or cut an example into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never pick a reference whose core a guardrail bans, and never dismiss one for a peripheral hit
  that an edit removes without changing what the video is about; never blur, pixelate or cover a
  competitor's mark (remove it and keep the object); never leave an excluded person's face in any
  shot, reflection or placed-back insert; never leave more units than the limit in any frame;
  never invent a guardrail, and never let one relax a hard rule (`brand-guardrails.md`).

## Hand-off

After A5 is answered and stored (`requested_videos`):
- Create: `T state --run RUN set stage=counted next_skill=atg-create-plan`, then invoke Skill `atg-create-plan`.
- Recreate: `T state --run RUN set stage=counted next_skill=atg-recreate-plan`, then invoke Skill `atg-recreate-plan`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
