---
name: atg-create-plan
description: /analyze-then-generate Analyze Mode / Create phase: style groups, virality-backed blends and scored concept ideation (A6). Internal to that command.
user-invocable: false
---

# atg-create-plan — Create: style groups, blends and concepts (A6)

> `ATG` = `C:/Users/Bulzart/.claude/analyze-then-generate` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- creative-direction §5.0: `ATG/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (5.1 KB)
- creative-direction §5.0b: `ATG/reference/creative-direction/070_5.0b_blend-not-mimic-reference-craft.md` (3.1 KB)
- creative-direction §5.0c: `ATG/reference/creative-direction/080_5.0c_virality-backed-blend-create-min.md` (2.2 KB)
- creative-direction §5.1: `ATG/reference/creative-direction/090_5.1_concept-seeds-scored-create-a6.md` (3.5 KB)
- creative-direction §5.2: `ATG/reference/creative-direction/100_5.2_the-best-approach-both-sub-modes.md` (1.3 KB)
- creative-direction §6: `ATG/reference/creative-direction/110_6_the-sharpness-gate-before-a-conc.md` (1.2 KB)
- creative-direction §7: `ATG/reference/creative-direction/120_7_hook-payoff-loop-text-and-sound.md` (1.2 KB)
- viral-browser §14.2: `ATG/reference/viral-browser/560_14.2_only-what-the-craft-carried-is-b.md` (1.0 KB)
- viral-browser §14.4: `ATG/reference/viral-browser/580_14.4_the-virality-rationale.md` (1.5 KB)
- viral-browser §14.6: `ATG/reference/viral-browser/600_14.6_what-the-mining-never-does-in-cr.md` (0.4 KB)
- brand-guardrails §4: `ATG/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- generation-system §4b.0: `ATG/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)

### A6. Create: style groups and blends (Create only)
- From the families and the directions (A4), the mechanism map, the blend matrix and the product insight sheet (A2b) present numbered **style
  groups**: `<content type> × <style> × <subject>`, grouped by content type. The values come from the analysed patterns and
  the product, not from a stock list.
  - Each group lists its mechanisms (M#, k of n references, graded), the typical length range, and how the product appears
    (its blend-matrix cell).
  - They are the agent's suggestions, built from the analysed patterns **and the product's strengths** (the insight
    sheet), never a menu or a template. Include **hybrid groups** that blend mechanisms from several families with what
    the product uniquely brings, and a format the references never showed when the mechanism logic and the product
    support it (`creative-direction.md` §5.0b).
- Ask with AskUserQuestion (header "Styles", `multiSelect: true`). The first option is **Agent's choice (Recommended)**:
  the agents design the blends with the highest engagement potential for this product and audience, from any family,
  hybrid or new format (`creative-direction.md` §5.0b); the other options are up to 3 of the best groups. The user picks
  **Agent's choice, one style or a mix**. "Other" accepts numbers or quantities ("2×G1, 1×G4").
- Without exact quantities, spread the videos across the chosen groups first, then by fit; under Agent's choice every
  video is its own best blend. A mixed answer (Agent's choice together with named groups) and no quantities gives the
  named groups half of the videos (rounded up, spread across them first) and Agent's choice the rest; quantities, when
  given ("2×G1, the rest Agent's choice"), always win. Show the allocation in one line and store it in `directions`.
- **The N videos are varieties.** Each is its own new concept: a different scenario, hook, setting or character beat.
  - **Transfer, not repetition** (`creative-direction.md` §5.0): every concept takes from the references only their craft
    (the style, the properties, the approach, the crafting, the hook type, why it works) from `20-analysis/craft-sheet.md`,
    and brings its own subject from the product's audience (the audience model's product half) and the product's natural
    use. A seed that restages a reference's premise, setting, characters, action order, joke, lines, first frame, ending
    or product beat fails the **copy test** and is rewritten with a new subject or dropped. That is Recreate's job, not
    Create's.
  - **Blend, not mimic** (`creative-direction.md` §5.0b): Create designs the most engaging video for *this* product from
    two inputs of equal weight, the references understood (`craft-sheet.md`, the audience model, the trend read) and the
    product understood (`30-assets/product-insights.md`). Every seed names its blend (the borrowed mechanism, the product
    truth, the audience situation) and passes the **blend test** (without the product the idea is generic; without the
    mechanism it is only an ad) and the **template-lock test** (it is not one family's structure and tone with the product
    swapped in). Families are evidence and ingredients, never a menu: the winner is chosen for engagement, not for
    resemblance to a reference.
  - **Virality-backed** (`creative-direction.md` §5.0c; `viral-browser.md` §14.2–§14.4): seeds come from the available
    cells of `20-analysis/blend-matrix.md` (a seed outside it is a new format and names "M#: none (new format),
    speculative"); only the craft is borrowed (never a reference's creator reach, paid reach, brand, bait, season or
    product); the blend line also names the audience trigger, the hook and its timing inside the measured range, the
    current trend element and the share line; and the winner carries its **virality rationale** (why it should spread,
    and what could make it fail).
  - **Ideation, scored** (`creative-direction.md` §5.1): for every video slot write at least five concept seeds (situation
    + turn + where the product lives + its blend line: M#, PT#, the hook and its timing, the trend element, the share
    line), score each on stop power, relatability, sharpness, product nativeness, blend, trend fit and freshness,
    feasibility for the locked model, and brand safety; take the best, keep the runner-up as the fallback, write the
    winner's share line, job and virality rationale (`viral-browser.md` §14.4), and run the sharpness gate (§6). Save
    them to `20-analysis/concepts.md` and show one line per video (seed, score, the reason it won). The user may swap a
    pick by replying; nothing is asked.
  - Each one borrows the mechanisms that made the references go viral (hook logic and timing, a structure move, a pacing
    device, a humour or payoff device) from whichever families show them, in whatever mix the product's strengths and the
    audience call for; its structure, pacing and payoff are designed for the blend, never copied from one family's profile
    or re-run from one family's format.
  - The client's product is blended into the concept from the first idea, not added at the end (its most suitable use,
    `generation-system.md` §4b.0), the way the house approach does it when examples exist.
  - No two videos repeat the same concept, and none repeats a reference's subject: the copy test runs against every
    reference the blend borrows from and the run's other winners.
  - **Guardrails as invariants** (`brand-guardrails.md` §4): the count limit is a ledger invariant, competitor objects
    never appear, only supplied characters appear, the wording rules shape the text plan, the presentation rules shape the
    anchor and the use beats, and a seed that a content or context rule hits scores 0 on brand safety.
- **Create never uses a reference as input.**
  - No reference video, frame or clip is uploaded, edited or passed to a generation.
  - The analysis informs only the borrowed mechanisms and the craft (hook logic, structure moves, pacing devices, camera
    behaviour, text role); the concept and the product's use come from the blend with the product insight sheet.
  - A meme the style calls for may still be placed in CapCut: an insert cut from a reference, or a supplied file.

## Rules this phase owns (contract items 16, 20)

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

## Never (this phase)

- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
- Never plan a Create video from a single unscored idea, a generic "person enjoys product" beat,
  an explained joke or a dated surface element; never let two videos of a run share a situation or
  a joke; never let the creative layer override a hard rule (`creative-direction.md`).
- Never restage a reference in Create: its premise, setting, characters, action order, joke,
  lines, caption wording, props, first frame, ending or product beat. Create collects a
  reference's style, properties, approach, crafting and hook logic, and makes another video with a
  new subject and a new idea; a seed that fails the copy test is rewritten or dropped
  (`creative-direction.md` §5.0). Never plan a Create video that is one family's template with the product
  swapped in, or one that ignores the product's own strengths: every seed names its blend and passes the blend and
  template-lock tests (§5.0b).
- Never let the references' product category, forms or names decide a Create concept (a corpus of pet tools does not
  make a pet video); never borrow a mechanism whose driver is not the craft (a creator's reach, paid reach, a known
  brand, bait, a season); never state that a video will go viral or quote a reach or sales figure that no source gave
  (`viral-browser.md` §14.2, §14.6).

## Hand-off

`T state --run RUN set stage=planned next_skill=atg-asset-plan`, then invoke Skill `atg-asset-plan`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
