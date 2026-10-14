---
name: atp-create-plan
description: /analyze-then-pick Analyze Mode / Create phase: style groups and scored concept ideation (A6). Internal to that command.
user-invocable: false
---

# atp-create-plan — Create: style groups and concepts (A6)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- creative-direction §5.0: `ATP/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (4.7 KB)
- creative-direction §5.1: `ATP/reference/creative-direction/070_5.1_concept-seeds-scored-create-a6.md` (2.8 KB)
- creative-direction §5.2: `ATP/reference/creative-direction/080_5.2_the-best-approach-both-sub-modes.md` (1.0 KB)
- creative-direction §6: `ATP/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- creative-direction §7: `ATP/reference/creative-direction/100_7_hook-payoff-loop-text-and-sound.md` (1.1 KB)
- brand-guardrails §4: `ATP/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- generation-system §4b.0: `ATP/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)

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
  - **Transfer, not repetition** (`creative-direction.md` §5.0): every concept takes from the
    references only their craft (the style, the properties, the approach, the crafting, the hook
    type, why it works) from `20-analysis/craft-sheet.md`, and brings its own subject from the
    audience model and the product's natural use. A seed that restages a reference's premise,
    setting, characters, action order, joke, lines, first frame, ending or product beat fails the
    **copy test** and is rewritten with a new subject or dropped. That is Recreate's job, not
    Create's.
  - **Ideation, scored** (`creative-direction.md` §5.1): for every video slot write at least five
    concept seeds (situation + turn + where the product lives), score each on stop power,
    relatability, sharpness, product nativeness, trend fit and freshness, feasibility for the
    locked model, and brand safety; take the best, keep the runner-up as the fallback, write the
    winner's share line and job, and run the sharpness gate (§6). Save them to
    `20-analysis/concepts.md` and show one line per video (seed, score, the reason it won). The
    user may swap a pick by replying; nothing is asked.
  - Each one exploits the patterns that made the references go viral: hook type and timing,
    structure, pacing, content type, camera, humour, and payoff.
  - The client's product is blended into the concept (its most suitable use, `generation-system.md`
    §4b.0), the way the house approach does it when examples exist.
  - No two videos repeat the same concept, and none repeats a reference's subject: the copy test
    runs against the family's references and the run's other winners.
  - **Guardrails as invariants** (`brand-guardrails.md` §4): the count limit is a ledger
    invariant, competitor objects never appear, only supplied characters appear, the wording
    rules shape the text plan, the presentation rules shape the anchor and the use beats, and a
    seed that a content or context rule hits scores 0 on brand safety.
- **Create never uses a reference as input.**
  - No reference video, frame or clip is uploaded, edited or passed to a generation.
  - The analysis informs only the concept, structure, pacing, camera, product use and text role.
  - A meme the style calls for may still be placed in CapCut: an insert cut from a reference, or a
    supplied file.

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
    the sharpness gate and the copy test (a Create video takes a reference's style, properties,
    approach, crafting and hook logic, never its subject, scene, joke, lines or ending:
    `creative-direction.md` §5.0); every Recreate pick is ranked for its creative potential; every brief says
    why the video will work; and QC judges the hook, the payoff and the share line as notes. The
    creative layer never overrides the hard rules (items 6, 14, 15, 18, 19 and the anomaly
    catalog); it decides which references, mechanisms and concepts win inside them.

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
  (`creative-direction.md` §5.0).

## Hand-off

`T state --run RUN set stage=planned next_skill=atp-asset-plan`, then invoke Skill `atp-asset-plan`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
