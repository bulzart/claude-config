---
name: atg-analyze-prepare
description: /analyze-then-generate Analyze Mode phase: inventory, preprocessing, documents, guardrails, asset registry (A1–A2b). Internal to that command.
user-invocable: false
---

# atg-analyze-prepare — Analyze Mode: inventory, preprocessing, documents, guardrails, assets (A1–A2b)

> `ATG` = `C:/Users/Bulzart/.claude/analyze-then-generate` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- assets-and-substitution §2: `ATG/reference/assets-and-substitution/020_2_understanding-the-supplied-asset.md` (5.0 KB)
- assets-and-substitution §3: `ATG/reference/assets-and-substitution/030_3_asset-registry-30-assets-registr.md` (1.5 KB)
- brand-guardrails §1: `ATG/reference/brand-guardrails/010_1_finding-and-reading-the-guardrai.md` (1.8 KB)
- brand-guardrails §2: `ATG/reference/brand-guardrails/020_2_rule-kinds-and-what-each-does-to.md` (4.9 KB)
- anomaly-catalog §1: `ATG/reference/anomaly-catalog/020_1_the-affordance-sheet-asset-regis.md` (7.5 KB)
- *the product insight sheet (Create and Recreate):*
  - creative-direction §5.0b: `ATG/reference/creative-direction/070_5.0b_blend-not-mimic-reference-craft.md` (3.1 KB)
- *only when a product has no supplied spec and its size must come from the standard-size table:*
  - anomaly-catalog §2.7: `ATG/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.5 KB)
- `ATG/pipeline/preprocessing.md` — only when a prep step reports an error

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
- **Audio context, every analysis mode.** Then run
  `T audio-context --run RUN --profile --second-pass`. It writes `20-analysis/audio-context.md` (and the `.json` beside it):
  one digest of what every reference says and how it sounds, as numbers and extractions, never as labels. Per video:
  - the `status` of the transcription run (a fact about the run: ok = the transcriber returned words, no-speech = it
    returned none, no-audio, failed, missing, skipped), the language and its probability;
  - the words and words per minute, the first word (any word, and the first word of probability 0.5 or more), the words
    below probability 0.5, the first sentence, every line with its times, the three-word phrases said twice or more
    (an extraction);
  - the sound numbers: `speech_share`, `non_speech_audible_share`, `harmonic_ratio_non_speech`, `tempo_bpm`,
    `beat_strength`, `spectral_flatness_median` (near 0 tonal, near 1 noise-like), `peak_frequency_hz_median` with
    `peak_frequency_steady_share` (near 1 = one steady tone, such as a beep), and the energy change from the first to
    the last third; `notes` state only facts about the run (missing, skipped, failed).
  `--profile` also measures each video's sound design (`audio-profile.json`); `--second-pass` transcribes every video in
  which no words were found once more without the voice filter, so that sung words are not dropped (shown in the digest
  and kept between runs; nothing prepared is changed). Over pure music or a tone the transcriber can invent words: read
  the second pass as a second look, not as proof of speech.
  - The scripts label nothing. You decide what the numbers mean: whether there is a music bed, whether the voice is on
    camera, a voice-over, sung, rapped or chanted (the transcriber cannot tell speech from lyrics), whether the sound is
    reusable whole, and what it does for the video. Every card agent judges the machine transcript (ASR: it mishears and
    can drop or invent words) against the picture and `timeline.md`.
  - Every analysis agent reads the digest before writing a card (A3), and every card carries the **Audio context:**,
    **Said:** and **Words and sound together:** lines. In Create the speech is read for its craft, never for its lines.
    Sung, rapped or chanted speech is the card agent's judgement, recorded in the Facts key `voice_type` (on-camera /
    voice-over / sung / rap / chant / none / mixed …); `Said:` may be one compact structured line for a long pitch.
  - A video without a usable transcript (status failed, missing or skipped: `without_a_transcript` in the JSON) is
    prepared again before the cards: `T prep-all --run RUN --only <V> --redo [--whisper-model medium]`. When speech
    cannot be recovered, the card says `transcript unavailable: <why>`.
  - **Recreate:** context only. The audio never goes to Higgsfield: only the silent copy is uploaded, and the original
    audio is restored after the result is approved (A6r). What is said tells the plan which beats the restored audio
    must still fit.
  - After the cards are written (A3), run `T audio-context --run RUN --check --cards`: a completeness check only (a
    transcript for every video; a card for every video, each with its `Audio context:` and `Said:` lines). It exits 1
    and lists what is missing, and writes nothing unless `--out` is given; add what it lists.
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
- Load the `assets-and-substitution` sections named in Read now (not the whole reference).
- View `30-assets/project/assets-sheet-*.jpg` and any preview that needs a closer look. Read
  `asset-inventory.md` (the paths grouped by sub-folder, and `duplicate_of` for identical files; file
  names are not interpreted, so you confirm every role by looking at the asset), then build the **asset registry**
  (`30-assets/registry.md` and `state.json → assets`):
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
  - **Product insights, per product** (every Analyze run; `assets-and-substitution.md` §2 step 3b; `creative-direction.md` §5.0b) into
    `30-assets/product-insights.md`: what it is and what it does for someone, who and when, what reads on camera (colour,
    texture, motion, the sound it makes, the reveal), what it can honestly show and how fast, the proof and claims the
    documents allow, the emotion it carries, the objections and limits, the occasions, and **up to six product truths**
    (PT1…) a concept can be built on (as many as the supplied assets and documents support). From the supplied assets and
    documents only; a gap is "not supplied" and is never filled by invention. Create's ideation reads it beside the craft
    sheet (A4, A6); Recreate keeps it for the plan's product details.
  - **Characters:** one entry per distinct person, mascot or character, with its best face and full
    views.
  - **Other assets:** logos, palettes, UI screenshots, environments, audio. Supplied fonts are
    listed only: CapCut text always uses the house text style (contract item 6).
- Ask **one** consolidated question only if a genuinely consequential ambiguity cannot be resolved by
  looking (e.g. two different-looking items presented as the same product). Otherwise proceed.

## Rules this phase owns (contract items 18, 21)

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

- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Never upload, recreate or cut an example into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never pick a reference whose core a guardrail bans, and never dismiss one for a peripheral hit
  that an edit removes without changing what the video is about; never blur, pixelate or cover a
  competitor's mark (remove it and keep the object); never leave an excluded person's face in any
  shot, reflection or placed-back insert; never leave more units than the limit in any frame;
  never invent a guardrail, and never let one relax a hard rule (`brand-guardrails.md`).

## Hand-off

`T state --run RUN set stage=prepared next_skill=atg-analyze-study`, then invoke Skill `atg-analyze-study` once `prep-all` has finished.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
