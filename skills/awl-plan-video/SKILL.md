---
name: awl-plan-video
description: /analyze-with-loupe per-video step X1: the plan (work backward, ledger, integration, size reckoning, QC checkpoints). Internal to that command.
user-invocable: false
---

# awl-plan-video — Step X1: plan the video (work backward)

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Per-video loop: `awl-plan-video` (X1) → `awl-write-request` (X2) → `awl-inputs` (X3) → `awl-precheck` (X4–X6) → `awl-submit` (X7) → `awl-postprocess` (X8) → `awl-qc` (X9) → `awl-record` (X10). Analyze Mode: this session runs X1, X2 and X4 for every video, X3 for the shared uploads and X5–X6 (A9); a production agent runs the rest of its own video.

Provenance labels: **[E]** evidence · **[I]** inference · **[U]** user instruction · **[A]** client asset · **[M]** model knowledge · **[G]** generation instruction.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- generation-system §1: `AWL/reference/generation-system/010_1_the-dependency-chain.md` (1.2 KB)
- generation-system §2: `AWL/reference/generation-system/020_2_work-backward-from-the-finished.md` (3.9 KB)
- generation-system §3: `AWL/reference/generation-system/030_3_entity-state-ledger-one-continuo.md` (3.8 KB)
- generation-system §4: `AWL/reference/generation-system/100_4_replacement-and-insertion-integr.md` (3.3 KB)
- generation-system §5: `AWL/reference/generation-system/210_5_logic-continuity-and-anti-slop-g.md` (4.6 KB)
- generation-system §5b: `AWL/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5d: `AWL/reference/generation-system/300_5d_counts-openings-and-object-perma.md` (1.7 KB)
- generation-system §6: `AWL/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (4.3 KB)
- generation-system §9b: `AWL/reference/generation-system/350_9b_what-must-not-survive-and-what-i.md` (4.8 KB)
- *a contents or placement video:*
  - generation-system §4b: `AWL/reference/generation-system/110_4b_natural-placement-and-contents-w.md` (1.2 KB)
  - generation-system §4b.0: `AWL/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
  - generation-system §4b.1: `AWL/reference/generation-system/130_4b.1_choose-the-anchor-by-the-product.md` (2.4 KB)
  - generation-system §4b.1b: `AWL/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (2.6 KB)
  - generation-system §4b.1c: `AWL/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
  - generation-system §4b.2: `AWL/reference/generation-system/160_4b.2_prominence-noticed-not-featured.md` (2.5 KB)
  - generation-system §4b.3: `AWL/reference/generation-system/170_4b.3_one-anchor-persistent-ledger-tra.md` (3.0 KB)
  - generation-system §4b.4: `AWL/reference/generation-system/180_4b.4_ambient-integration-it-must-not.md` (2.7 KB)
- *a placed product (spot and size in the prompt; Recreate and Edit Mode: the original is the only video reference):*
  - generation-system §4b.5: `AWL/reference/generation-system/190_4b.5_expressing-it-to-the-model-with.md` (6.5 KB)
- *Edit Mode or Recreate (the source action script):*
  - generation-system §5c.1: `AWL/reference/generation-system/240_5c.1_the-source-action-script-card-th.md` (1.4 KB)
- *a multi-clip video, or a Recreate/Edit source with hard cuts (item 7: separate clips on the source's own cuts):*
  - generation-system §3b: `AWL/reference/generation-system/040_3b_videos-longer-than-one-generatio.md` (0.8 KB)
  - generation-system §3b.1: `AWL/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.3 KB)
- *a video with inserts:*
  - generation-system §3c: `AWL/reference/generation-system/090_3c_reference-inserts-memes-cut-from.md` (3.6 KB)
- anomaly-catalog §0: `AWL/reference/anomaly-catalog/010_0_four-questions-behind-every-anom.md` (1.5 KB)
- anomaly-catalog §1: `AWL/reference/anomaly-catalog/020_1_the-affordance-sheet-asset-regis.md` (7.6 KB)
- anomaly-catalog §2.7: `AWL/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (12.3 KB)
- anomaly-catalog §2.14: `AWL/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.4 KB)
- anomaly-catalog §2.16: `AWL/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (3.9 KB)
- anomaly-catalog §3: `AWL/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.4 KB)
- *a product that is handled, prepared, used, poured or counted on screen:*
  - anomaly-catalog §2.1: `AWL/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.2 KB)
  - anomaly-catalog §2.2: `AWL/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (2.8 KB)
  - anomaly-catalog §2.3: `AWL/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.5 KB)
  - anomaly-catalog §2.4: `AWL/reference/anomaly-catalog/070_2.4_irreversible-and-persistent-stat.md` (1.3 KB)
  - anomaly-catalog §2.5: `AWL/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
  - anomaly-catalog §2.6: `AWL/reference/anomaly-catalog/090_2.6_liquids-powders-and-materials.md` (1.8 KB)
  - anomaly-catalog §2.8: `AWL/reference/anomaly-catalog/110_2.8_body-mechanics-at-the-product.md` (1.5 KB)
  - anomaly-catalog §2.9: `AWL/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.4 KB)
- *a person is swapped for a supplied character:*
  - anomaly-catalog §2.17: `AWL/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- creative-direction §2: `AWL/reference/creative-direction/020_2_the-goal-model-written-into-20-a.md` (1.4 KB)
- creative-direction §3: `AWL/reference/creative-direction/030_3_the-audience-model-mass-cognitio.md` (3.0 KB)
- creative-direction §4: `AWL/reference/creative-direction/040_4_the-trend-read-written-into-20-a.md` (2.1 KB)
- creative-direction §6: `AWL/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- *Create (the craft carried, the copy test):*
  - creative-direction §5.0: `AWL/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (4.7 KB)
- *Edit Mode:*
  - creative-direction §9: `AWL/reference/creative-direction/120_9_edit-mode.md` (0.3 KB)
- text-and-format §1: `AWL/reference/text-and-format/010_1_text-policy-depends-on-the-mode.md` (5.7 KB)
- text-and-format §3: `AWL/reference/text-and-format/030_3_analyze-mode-planning-text-and-p.md` (3.8 KB)
- *Edit Mode (the substitution map):*
  - assets-and-substitution §4: `AWL/reference/assets-and-substitution/040_4_substitution-map-per-video.md` (2.4 KB)
- *guardrails supplied:*
  - brand-guardrails §4: `AWL/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- *Create (the sound plan):*
  - capcut-assembly §3b: `AWL/reference/capcut-assembly/040_3b_sound-layer-create.md` (5.1 KB)
- *an own voiceover (`state.json → voiceover.enabled` true and, in Free, this video in `voiceover.videos` when that key exists; item 31):*
  - voiceover §3: `AWL/reference/voiceover/030_3_writing-the-lines-x1.md` (2.3 KB)
  - voiceover §4: `AWL/reference/voiceover/040_4_generating-and-recording-a-take.md` (3.4 KB)
  - voiceover §5: `AWL/reference/voiceover/050_5_on-camera-or-off-screen-and-whic.md` (1.1 KB)
  - voiceover §6: `AWL/reference/voiceover/060_6_in-the-request-x2-by-what-the-lo.md` (3.3 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `awl-model-guide`) — §1 at a glance, §3.14 integration and continuity, §5 failure modes (where the guide lists size or place as a limit), §6 features
- the registry `RUN/30-assets/registry.md`, the card `RUN/20-analysis/cards/<V>.md`, `RUN/20-analysis/house-approach.md` when it exists

### ElevenLabs tools (an own voiceover only, item 31)

Load before the first take: `ToolSearch "select:mcp__elevenlabs__text_to_speech,mcp__elevenlabs__get_voice,mcp__elevenlabs__check_subscription"`.
Only this session voices takes (never a planner fork, `awl-analyze-produce` item 30, or a production agent); none found, or a failed call:
a blocker with the real error (`voiceover.md` §4 step 8).

## Step X1

**Free runs:** this video's kind (`state.json → videos_kind[NN]`; the plan header carries `Kind: recreate | create`) selects the Recreate or the Create branch of every step below and of X2–X10; its direction is its lines in `RUN/20-analysis/free-plan.md` (the user's requirement, [U]), which win over the family profile and the house approach wherever they speak, and its explicit wants and forbids become QC checkpoints.


- **X1 — Plan (work backward).**
  - Write `40-briefs/video-NN-plan.md` with `generation-system.md` §2–§6:
    - intent (`generation-system.md` §2.1): the goal and the video's job, the audience, the one
      sharp idea, the emotion arc or laugh mechanism, the share line (`creative-direction.md` §2–§6);
      Create: the craft carried from the family and the subject the concept brings, with the copy
      test passed (`creative-direction.md` §5.0);
    - the **spot** (`generation-system.md` §4b.1c; from the source in Recreate and Edit Mode, from the
      blocking the plan asks for in Create): the hand-lane map, the region that is bare and in frame at 0,
      1, 2.5, 4 and 6 s, the strip's width against the product, the plane, the camera path and any spot the
      user marked; in Recreate and Edit Mode the **original reference** is the only video reference and the prompt
      carries the spot (pinned to a fixed neighbour) and the size (against a named neighbour, §4b.5), with the
      product's padded views; where the model guide lists size or place as a limit and no passing-list anchor fits
      (always for a near-plane spot the user marked), the size risk goes in the brief; plan the source span so that
      the original fits the model's own limits (its guide §2.2, §2.5); a longer source is split into clips on its
      own cuts (the clip plan below);
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
    - for a video with **inserts** (Create: only with `memes=include`, item 32; with `none` its own beats carry a reference's meme beat),
      the **insert plan** (`generation-system.md` §3c):
      - the generated length (the reference minus its inserts);
      - each split point as a planned beat boundary;
      - each insert's cut (in, out, video or still, sound, overlays to clean);
    - the **text plan** (Analyze Mode, `text-and-format.md` §3): every overlay text event with its
      wording, final-timeline time and position, always in the house text style (item 6). It is
      placed in CapCut later and never generated;
    - the **sound plan** (Create, `capcut-assembly.md` §3b), placed in CapCut:
      - the generation carries only dialogue, action sounds and ambience, with no generated music;
      - the soundtrack's role, mood, tempo and how its energy moves, read from the references' sound-profile numbers;
      - its source: a supplied track, the reference's own speech-free sound (only when its profile measured the speech share: in a
        frames-only run `speech_share` is null and the reference's sound is not reused whole), or a matching track to download;
      - the sound effects and their hit points on the new video's beats (no meme sound with `memes=none`);
      - with an own voiceover, the soundtrack sits under the voice (about 0.25) and no effect lands on a word;
    - the **voiceover** (an own voiceover, item 31; `voiceover.md` §3–§6), a "Voiceover" block written before the beats are final: the
      method and the form with the voice and its reason (§5); the lines (§3), the text as sent alone in `40-briefs/video-NN[-cK]-voiceover.txt`;
      the take (§4 steps 1–3: `T voiceover outdir`, one `text_to_speech` call, `T voiceover record`; a recorded take is never voiced again);
      its fit and the plan re-timed to it (§4 steps 4–6: the beats on its phrases, the duration by the method, three phrase starts and one
      pause as QC checkpoints); lipsync names its sync pass, native on Wan 2.7 its start frame; the user's own files: §4 step 7;
    - for a **multi-clip** video, the **clip plan** (`generation-system.md` §3b):
      - the seams, on the reference's cuts first;
      - the join method of each seam (from `index.json → continuation`);
      - the hand-off state of each seam;
      - the clip durations; in Recreate and Edit Mode each clip's original reference (of that clip's span) fits the
        locked model's limits (its guide §2.2, §2.5);
    - the logic and anti-slop gate;
    - the **QC checkpoints** (`anomaly-catalog.md` §3 step 8): every use beat, exit and re-entry,
      occlusion, cut, hand-off, pour and seam, plus the first second (the product in frame at 0.0 s) and
      the last, the product's position against a fixed neighbour at least every 0.25 s, and every
      transition, insert start and end and overlay start and end of the CapCut timeline, each with its time
      range and the counts and states expected there. X9 renders them with `T qc --dense`;
    - conflict resolution.
  - Use the provenance labels.
  - Analyze Mode: rotate approved characters across videos when no assignment is given.

## Rules this phase owns (contract items 6, 9, 14, 16, 18, 21, 31)

31. **Own voiceover: the take is the timing master** (`voiceover.md`): this session writes, voices and records each voiced video's take
    and plans the video to it; production agents upload, carry, check and record it, and never voice anything.

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
     - **Size 11 when the video has only a little text** (the user, 2026-10-29): at no moment more
       than 5 words on screen at once, and every line within 82% of the frame width at 11. One size
       for the whole video; `T capcut-repair` counts, measures and sets it.
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
    - Create uses inserts only when the user chose memes (`state.json → memes`, item 32).
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
  (font System, size 10 or 11 when the video has only a little text, the user's locked preset in
  `capcut.text_style.learned`), unless the user asks for it in the run. Never re-learn or replace that preset (`--learn --replace`) unless the
  user explicitly asks for a new one. Never place a text layer off-centre horizontally (posX ≠ 0):
  only its height follows the reference.
- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
- Never plan an insert or a meme sound in a Create video when `memes=none` (item 32), and never imitate the meme in the scene.
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
  it (`generation-system.md` §4b.1c); never build, upload or bind a guide image cut from a source frame, or any
  placement image beside the original (§4b.5); never upload a mirrored selfie source un-flipped in Recreate, or leave a baked
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
  nobody viewed on a frame (it is provisional, your own word: the tool prints numbers, CE-028); never accept a product over a quarter larger or
  smaller than reckoned, one that
  changes size across a cut, or one larger than the hand that holds it (`anomaly-catalog.md` §2.7).
- Never plan a product that is handled on screen without its affordance sheet in the registry
  (§1), and never run X9 without the plan's QC checkpoints rendered dense (`T qc --dense`).
- Never write a voiceover line a reference spoke, never voice a script twice or a recorded take again, never leave a take unrecorded,
  and never let the model's own voice stand in for a take (item 31).

## Hand-off

Invoke Skill `awl-write-request` for this video's X2.
