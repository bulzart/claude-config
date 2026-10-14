---
name: atp-plan-video
description: /analyze-then-pick per-video step X1: the plan (work backward, ledger, integration, size reckoning, QC checkpoints). Internal to that command.
user-invocable: false
---

# atp-plan-video — Step X1: plan the video (work backward)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Per-video loop: `atp-plan-video` (X1) → `atp-write-request` (X2) → `atp-inputs` (X3) → `atp-precheck` (X4–X6) → `atp-submit` (X7) → `atp-postprocess` (X8) → `atp-qc` (X9) → `atp-record` (X10). Analyze Mode: this session runs X1, X2 and X4 for every video, X3 for the shared uploads and X5–X6 (A9); a production agent runs the rest of its own video.

Provenance labels: **[E]** evidence · **[I]** inference · **[U]** user instruction · **[A]** client asset · **[M]** model knowledge · **[G]** generation instruction.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- generation-system §1: `ATP/reference/generation-system/010_1_the-dependency-chain.md` (1.2 KB)
- generation-system §2: `ATP/reference/generation-system/020_2_work-backward-from-the-finished.md` (3.9 KB)
- generation-system §3: `ATP/reference/generation-system/030_3_entity-state-ledger-one-continuo.md` (3.8 KB)
- generation-system §4: `ATP/reference/generation-system/100_4_replacement-and-insertion-integr.md` (3.3 KB)
- generation-system §5: `ATP/reference/generation-system/210_5_logic-continuity-and-anti-slop-g.md` (4.6 KB)
- generation-system §5b: `ATP/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5d: `ATP/reference/generation-system/300_5d_counts-openings-and-object-perma.md` (1.7 KB)
- generation-system §6: `ATP/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (1.5 KB)
- generation-system §9b: `ATP/reference/generation-system/350_9b_what-must-not-survive-and-what-i.md` (4.6 KB)
- *a contents or placement video:*
  - generation-system §4b: `ATP/reference/generation-system/110_4b_natural-placement-and-contents-w.md` (1.2 KB)
  - generation-system §4b.0: `ATP/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
  - generation-system §4b.1: `ATP/reference/generation-system/130_4b.1_choose-the-anchor-by-the-product.md` (2.4 KB)
  - generation-system §4b.1b: `ATP/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (3.1 KB)
  - generation-system §4b.1c: `ATP/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
  - generation-system §4b.2: `ATP/reference/generation-system/160_4b.2_prominence-noticed-not-featured.md` (2.5 KB)
  - generation-system §4b.3: `ATP/reference/generation-system/170_4b.3_one-anchor-persistent-ledger-tra.md` (3.0 KB)
  - generation-system §4b.4: `ATP/reference/generation-system/180_4b.4_ambient-integration-it-must-not.md` (2.7 KB)
- *a size-and-place guide is needed (the model guide lists size or place as a limit, or the spot is near-plane):*
  - generation-system §4b.6: `ATP/reference/generation-system/200_4b.6_the-size-and-place-guide-a-refer.md` (4.1 KB)
- *Edit Mode or Recreate (the source action script):*
  - generation-system §5c.1: `ATP/reference/generation-system/240_5c.1_the-source-action-script-card-th.md` (1.2 KB)
- *a multi-clip video, or a Recreate/Edit source with hard cuts (item 7: separate clips on the source's own cuts):*
  - generation-system §3b: `ATP/reference/generation-system/040_3b_videos-longer-than-one-generatio.md` (0.8 KB)
  - generation-system §3b.1: `ATP/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.3 KB)
- *a video with inserts:*
  - generation-system §3c: `ATP/reference/generation-system/090_3c_reference-inserts-memes-cut-from.md` (3.2 KB)
- anomaly-catalog §0: `ATP/reference/anomaly-catalog/010_0_four-questions-behind-every-anom.md` (1.5 KB)
- anomaly-catalog §1: `ATP/reference/anomaly-catalog/020_1_the-affordance-sheet-asset-regis.md` (7.6 KB)
- anomaly-catalog §2.7: `ATP/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.1 KB)
- anomaly-catalog §2.14: `ATP/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.9 KB)
- anomaly-catalog §2.16: `ATP/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (4.3 KB)
- anomaly-catalog §3: `ATP/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.1 KB)
- *a product that is handled, prepared, used, poured or counted on screen:*
  - anomaly-catalog §2.1: `ATP/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.5 KB)
  - anomaly-catalog §2.2: `ATP/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (3.0 KB)
  - anomaly-catalog §2.3: `ATP/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.7 KB)
  - anomaly-catalog §2.4: `ATP/reference/anomaly-catalog/070_2.4_irreversible-and-persistent-stat.md` (1.4 KB)
  - anomaly-catalog §2.5: `ATP/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
  - anomaly-catalog §2.6: `ATP/reference/anomaly-catalog/090_2.6_liquids-powders-and-materials.md` (1.9 KB)
  - anomaly-catalog §2.8: `ATP/reference/anomaly-catalog/110_2.8_body-mechanics-at-the-product.md` (1.5 KB)
  - anomaly-catalog §2.9: `ATP/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.3 KB)
- *a person is swapped for a supplied character:*
  - anomaly-catalog §2.17: `ATP/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- creative-direction §2: `ATP/reference/creative-direction/020_2_the-goal-model-written-into-20-a.md` (1.4 KB)
- creative-direction §3: `ATP/reference/creative-direction/030_3_the-audience-model-mass-cognitio.md` (3.0 KB)
- creative-direction §4: `ATP/reference/creative-direction/040_4_the-trend-read-written-into-20-a.md` (1.9 KB)
- creative-direction §6: `ATP/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- *Create (the craft carried, the copy test):*
  - creative-direction §5.0: `ATP/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (4.7 KB)
- *Edit Mode:*
  - creative-direction §9: `ATP/reference/creative-direction/120_9_edit-mode.md` (0.3 KB)
- text-and-format §1: `ATP/reference/text-and-format/010_1_text-policy-depends-on-the-mode.md` (5.7 KB)
- text-and-format §3: `ATP/reference/text-and-format/030_3_analyze-mode-planning-text-and-p.md` (3.5 KB)
- *Edit Mode (the substitution map):*
  - assets-and-substitution §4: `ATP/reference/assets-and-substitution/040_4_substitution-map-per-video.md` (2.4 KB)
- *guardrails supplied:*
  - brand-guardrails §4: `ATP/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- *Create (the sound plan):*
  - capcut-assembly §3b: `ATP/reference/capcut-assembly/040_3b_sound-layer-create.md` (3.9 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §1 at a glance, §3.14 integration and continuity, §5 failure modes (where the guide lists size or place as a limit), §6 features
- the registry `RUN/30-assets/registry.md`, the card `RUN/20-analysis/cards/<V>.md`, `RUN/20-analysis/house-approach.md` when it exists

## Step X1

- **X1 — Plan (work backward).**
  - Write `40-briefs/video-NN-plan.md` with `generation-system.md` §2–§6:
    - intent (`generation-system.md` §2.1): the goal and the video's job, the audience, the one
      sharp idea, the emotion arc or laugh mechanism, the share line (`creative-direction.md` §2–§6);
      Create: the craft carried from the family and the subject the concept brings, with the copy
      test passed (`creative-direction.md` §5.0);
    - the **spot** (`generation-system.md` §4b.1c; from the source in Recreate and Edit Mode, from the
      blocking the plan asks for in Create): the hand-lane map, the region that is bare and in frame at 0,
      1, 2.5, 4 and 6 s, the strip's width against the product, the plane, the camera path and any spot the
      user marked; and, where the model guide lists size or place as a limit and no passing-list anchor
      fits (always for a near-plane spot the user marked), the **size-and-place guide** (§4b.6) with what it
      is built from;
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
    - the per-second time budget from the family profile;
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
    - the **QC checkpoints** (`anomaly-catalog.md` §3 step 8): every use beat, exit and re-entry,
      occlusion, cut, hand-off, pour and seam, plus the first second (the product in frame at 0.0 s) and
      the last, the product's position against a fixed neighbour at least every 0.25 s, and every
      transition, insert start and end and overlay start and end of the CapCut timeline, each with its time
      range and the counts and states expected there. X9 renders them with `T qc --dense`;
    - conflict resolution.
  - Use the provenance labels.
  - Analyze Mode: rotate approved characters across videos when no assignment is given.

## Rules this phase owns (contract items 6, 9, 14, 16, 18, 21)

6. **Text policy depends on the mode** (`reference/text-and-format.md`):
   - Edit Mode removes all source text unless the user keeps specific text.
   - **Analyze Mode generates every video clean.** It places all overlay text ("POV: …", "when …",
     hooks, captions) afterwards as **CapCut text layers** at the reference text's height and
     timing, always **horizontally centred** (posX 0; when centred text would cover the product, a
     face or an insert, it moves up or down, never sideways; CE-010)
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
9. **One interconnected system.** Every generation is planned with `reference/generation-system.md`:
   - work backward from the finished video;
   - keep the entity state ledger;
   - run the integration analysis;
   - pass the anti-slop gate;
   - translate into the model's official pattern;
   - run the pre-generation QC.
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

- Never copy usernames, handles, watermarks or source brand names. Reuse reference caption wording
  only as a generic meme line (`text-and-format.md` §1).
- Never re-type a context-bearing source overlay as text (CE-017, CE-023), never drop a keyword the user
  keeps (CE-027), never change a caption's subject to clear a guardrail (CE-022), and never give a brand a
  scene it has no tie to when the other brand fits (CE-020).
- Never give a CapCut text layer another font, size, colour or preset than the house text style
  (font System, size 10, the user's locked preset in `capcut.text_style.learned`), unless the user
  asks for it in the run. Never re-learn or replace that preset (`--learn --replace`) unless the
  user explicitly asks for a new one. Never place a text layer off-centre horizontally (posX ≠ 0):
  only its height follows the reference.
- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
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
- Never place a product at a spot that is hidden at the source's frame 0, leaves the frame along the camera
  path, lies in a hand's lane, is narrower than the product or is the nearest plane unless the user marked
  it, and then only with a guide (`generation-system.md` §4b.1c); never build a size-and-place guide from an
  unscrubbed source frame (performer, clothing or lettering still in it), a flat packshot paste or a
  soft-labelled image (§4b.6); never upload a mirrored selfie source un-flipped in Recreate, or leave a baked
  face effect, a burned-in caption or an identifying name without its prompt sentence (§5c.2b); never try to
  remove a caption, a name or a patch from a source with a tool in Analyze Mode (inpaint, delogo, crop): the
  clean-plate lines and the character-swap script carry it.
- Never blur, soften, crop out, remove or avoid content that no client guardrail and no copyright
  floor names (meme faces, alcohol, weapons, fake blood, profanity, cameos, …); the floor (the
  replaced person, the swapped or competitor product, overlay text and handles, platform logos
  and watermarks, featured third-party branding, copyrighted characters as the subject) and the
  generation service's blocks always stand, and a brand rule never removes them
  (`generation-system.md` §9b).
- Never render a product without its size reckoning (real dimensions, depth, lens, a named
  neighbour's ratio, the size ladder) in the plan and the prompt; never read a product's size off
  its own photo; never take the distance from an assumption (derive it from the frame, with two estimates
  that agree), and never flag, repeat or summarise a size verdict that rests on one assumed number or that
  nobody viewed on a frame (it is provisional, CE-028); never accept a product over a quarter larger or
  smaller than reckoned, one that
  changes size across a cut, or one larger than the hand that holds it (`anomaly-catalog.md` §2.7).
- Never plan a product that is handled on screen without its affordance sheet in the registry
  (§1), and never run X9 without the plan's QC checkpoints rendered dense (`T qc --dense`).

## Hand-off

Invoke Skill `atp-write-request` for this video's X2.
