---
name: cs-prepare
description: /create-static Analyze Mode phase: inventory, preprocessing, documents, guardrails, asset registry (A1–A2b). Internal to that command.
user-invocable: false
---

# cs-prepare — Static: inventory, preprocessing, documents, guardrails, assets (A1–A2b)

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- assets-and-substitution §2: `CS/reference/assets-and-substitution/020_2_understanding-the-supplied-asset.md` (2.9 KB)
- assets-and-substitution §3: `CS/reference/assets-and-substitution/030_3_asset-registry-30-assets-registr.md` (1.5 KB)
- brand-guardrails §1: `CS/reference/brand-guardrails/010_1_finding-and-reading-the-guardrai.md` (1.8 KB)
- brand-guardrails §2: `CS/reference/brand-guardrails/020_2_rule-kinds-and-what-each-does-to.md` (4.9 KB)
- *the assets hold a product or object (item 14; Static's assets are usually characters):*
  - anomaly-catalog §1: `CS/reference/anomaly-catalog/020_1_the-affordance-sheet-asset-regis.md` (7.6 KB)
  - *only when that product has no supplied spec and its size must come from the standard-size table:*
    - anomaly-catalog §2.7: `CS/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.7 KB)
- `CS/pipeline/preprocessing.md` — only when a prep step reports an error

### A1. Inventory and preprocessing (deterministic, local)

The references' storyboards are at 2 fps flat with their audio (item 36; Static has no effort level: `T prep-all` samples every reference at
`config.json → static.analysis.fps`, nothing denser; the user, 2026-11-07: "remove the effort idea completely (on static mode), just do 2fps
when on static mode"), and every video's audio is transcribed by Whisper (`state.json → audio_ingest` is `whisper`: written at the start,
never asked, item 24). No reference is ever an input.

1. `T inventory "<references folder>" --run RUN --as references`: everything in it is **reference material only**.
2. **A reference another run already analysed** (the same file): `T reuse-analysis --run RUN --from <that run>` right after the inventory
   copies its media folder (its frames, transcript, audio numbers and edit profile; and its card) under its id here: `prep-all` skips it as
   already prepared, `edit-profile` is not run for it, and A3 reads its card again instead of writing a new one, adding what the current
   card (static §1) asks that the older card lacks, from the copied media, never by analysing the video again (the user, 2026-11-07: "we
   already have the Sadam Hussein's there whom we've already analyzed, analyze the two new samples").
3. `T inventory "<asset path>" "<asset path>" … --run RUN --as assets` (scope `project`), then `T prep-assets --run RUN`: previews,
   document text, font names and a labelled contact sheet of **exactly the files the user supplied**. The assets are characters (photos
   and/or descriptions), usually no product.
4. **Examples, when given** (contract item 18): `T inventory "<examples folder>" --run RUN --as examples`. An empty folder gives 0
   examples: carry on. An assets path that contains a folder named `examples` (any case) hands that folder over as the examples folder:
   inventory the assets without it (pass its siblings) and say so.
5. **With an effects folder** (`state.json → static.effects_folder` not `none`; read-only like the references, item 34):
   `T effects scan --run RUN` (every sound and overlay measured once and cached: `00-inventory/effects.md` and `.json`, contact sheets in
   `10-media/effects/`; a large folder takes a minute or more, run it with `run_in_background: true` beside the other steps). Facts only:
   the spec and the plan pick from them (static §2, §5).
6. `T split-audio "<references folder>" --run RUN --audio-only` writes `files_audio/` (no silent copies: no reference is ever an input; the
   toolkit's own derived folder beside the originals, item 34) for the sound and voice numbers of A3.
7. Show the counts (references, assets, examples) in one line.
8. `T prep-all --run RUN --jobs 2 --ocr-frames 30` (2 fps flat, no effort level; `--ocr-frames 30` takes more OCR frames for the captions).
   Every video's picture and its sound are fully processed inside the run folder:
   - frames, storyboards and on-screen text;
   - loudness, silences, music and sound cues, from the audio file;
   - the transcript (`10-media/<V>/transcript.json` and `.txt`), by Whisper.

   Spoken hooks, sounds and music are part of what made them work. `prep-all` runs the frame pipeline at the Static rate, storyboards, the
   per-second timeline, the audio measurements, speech-to-text (it reads `state.json → audio_ingest` itself and stops while it is empty;
   Static's is `whisper`) and the OCR sample for every video, plus image previews and document text; it skips every reference already
   prepared; its JSON says which `audio_ingest` it ran.
   - with more than ~3 minutes of total video, run it with `run_in_background: true`, read the documents (A2) meanwhile, and wait for the
     completion notification before the next steps and A3;
   - fix or report any per-item errors listed in its JSON.
9. With examples: `T prep-all --run RUN --set examples --jobs 2` (into `10-media/E01…`, listed in `10-media/examples-index.md`).
10. **The edit layer at the full frame rate**, once `prep-all` has finished: `T edit-profile --run RUN --ref <V>` for every reference that has no
    profile yet (its moves, joins and caption entrances as numbers, `10-media/<V>/edit-profile.json`; 2 fps cannot show them, static §1).
11. **The references' real YouTube titles:** `T static context --run RUN` (usually from the file names, `<channel>_<title>_<YouTube id>`;
    with a `context.txt` in the references folder, its lines `<file>|<title>|<thumbnail path>` and the thumbnails; a thumbnail is also the
    image of the same name beside its video; the table `00-inventory/context.md`; static §12).
12. Pipeline details: `CS/pipeline/preprocessing.md`.

### A2. Documents and instructions (authoritative)
- Read every document:
  - `10-media/docs/<D>.txt` for text and office files, and for PDFs (`prep-all` extracts their text layer with pypdf; the media index
    line gives the page and character counts);
  - a PDF with no text layer (the index line says `no text layer`) is viewed page by page from the images `prep-all` wrote to
    `10-media/docs/<D>-pages/`, or with Read and `pages` (at most 10 pages render on this machine);
  - spreadsheets as extracted text.
- The same goes for documents among the supplied assets (`30-assets/project/docs/`), e.g. dimensions,
  brand rules and usage notes.
- Quote the requirements they define. They override inferences.
- **Brand guardrails** (item 21; `CS/reference/brand-guardrails.md` §1): extract every rule
  into `30-assets/guardrails.md` (`G<n> · quote [E] · source · kind · what it hits · default
  operation`), then the lists they imply: competitors (named, plus every brand in the client's
  category), excluded people, limits, wording and disclaimers, presentation rules. Conflicts
  between documents or with the user's instructions go to the user once, with both quotes.
  Without a guardrail document, write "none supplied": only Static's two content rules apply (static §11, §11b; item 21).

### A2b. Understand the supplied assets (autonomous — no questions by default)
- Load the `assets-and-substitution` sections named in Read now (not the whole reference).
- View `30-assets/project/assets-sheet-*.jpg` and any preview that needs a closer look. Read
  `asset-inventory.md` (the paths grouped by sub-folder, and `duplicate_of` for identical files; file
  names are not interpreted, so you confirm every role by looking at the asset), then build the **asset registry**
  (`30-assets/registry.md` and `state.json → assets`):
  - **Group into entities.** Each distinct product, object, character, interface, brand kit or
    environment is one entity, using sub-folders, names and what the images show. Several products,
    samples or characters are expected.
  - **Characters:** one entry per distinct person, mascot or character, with its best face and full
    views.
  - **Products and objects** (only when the assets hold one, item 14): pick the canonical template (the cleanest, most complete geometry view,
    or the file the user named template/canonical). Mark other views and variants, and take real
    dimensions from any supplied spec. Find and link each **contents sample** to its variant: a
    liquid or texture photo, a pour, a glass of the drink, or a lifestyle shot that shows it. They
    are often among the supplied files without a label. A sample is never a separate product.
    - **Affordance sheet, per product or object** (`CS/reference/anomaly-catalog.md` §1): its parts,
      openings, opening sequence, how it is used and held, the contact point, what it holds and how
      many, its states, real size, the orientation of its mark, and what it cannot do. Every plan
      and prompt quotes it.
    - **Real dimensions, per product:** height, width or diameter and depth in cm, and the volume,
      from the supplied specs; when none exist, the category's standard size from the catalog's
      §2.7 table, marked [I]. Never read a size off the product's own photo. These numbers are the sizes the image plans and prompts
      give the product in a still (static §5).
  - **Other assets:** logos, palettes, UI screenshots, environments, audio. Supplied fonts are
    listed only: the captions take the references' own text look (item 36).
- Ask **one** consolidated question only if a genuinely consequential ambiguity cannot be resolved by
  looking (e.g. two different-looking items presented as the same product). Otherwise proceed.

## Rules this phase owns (contract items 18, 21)

18. **Examples: the user's own finished videos (optional).** They are asked for with the
    other inputs (`cs-start`). The folder may be empty or absent; then nothing changes.
    - They show the user's **house approach**: how their products are placed and used, plus anything else they consistently do (text
      placement, pacing, sound, characters, endings).
    - When present, they are prepared and analysed (A1, A3) into
      `20-analysis/house-approach.md`, and every plan follows it (A4–A6s).
    - **Precedence:** the user's instructions for the run > the house approach > the pipeline's
      defaults. The house approach never overrides the hard rules: the facts sourced and nothing invented (static §3, §4), nothing
      religious or superstitious (static §11), nothing indecent, gory or distressing (static §11b), the permission rule (item 15) and
      no sticker or emoji (item 6).
    - Examples are **study material only**: never uploaded, recreated, cut into a new video, or used
      as client assets. Their own flaws (a physics cheat, a leftover watermark) are never copied.
21. **Brand guardrails come from the client's documents** (`CS/reference/brand-guardrails.md`). Documents among the supplied assets (and in
    the references folder) that state the client's rules (no gore, two cans per day max, no competitor brands on screen, no ambassador
    likeness, no health claims, required disclaimers, …) are extracted into
    `30-assets/guardrails.md`, one quoted rule per line with its kind and default operation, plus
    the competitor, people, limit, wording and presentation lists they imply. In Static no reference is picked or edited: the rules are
    plan invariants for the new videos (`brand-guardrails.md` §4), and each reference's audit against them belongs to its card
    (A3, `cs-study`; `brand-guardrails.md` §3). The user's run instructions outrank the guardrails; the guardrails outrank the house
    approach and the defaults; they never relax a hard rule; none is invented. **The pipeline has no content rules of its own but
    Static's two:** nothing religious or superstitious in a subject, a line, a caption, a picture or a sound (static §11), and nothing
    indecent, gory or distressing (static §11b). Without a guardrail document only those two apply, with the image and speech services'
    own blocks; a brand rule can add a content rule, never remove those two or enable what a service refuses.

## Never (this phase)

- Never take client assets from the references folder: it is reference material, and may show other products or executions.
- Never upload, recreate or cut an example into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never blur, pixelate or cover a competitor's mark (the picture is planned without it, or the object is kept plain and unbranded); never
  let an excluded person's face appear in any still; never plan more units than the limit in any frame; never invent a guardrail, and
  never let one relax a hard rule (`brand-guardrails.md`).
- Never move, rename, delete or overwrite a file in the user's references, assets, examples or effects folders (item 34): what the run
  needs is copied into `RUN`, and the toolkit adds only its own derived folder (`files_audio/`).

## Hand-off

`T state --run RUN set stage=prepared next_skill=cs-study`, tick this phase's items in `RUN/todo.md` and set its `Next:` line (item 38), then invoke Skill `cs-study` once `prep-all`, `edit-profile` and the effects scan have finished.

After a compaction, or on `resume`, read `RUN/todo.md` first (item 38), then re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
