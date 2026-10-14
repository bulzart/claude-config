---
name: atp-qc
description: /analyze-then-pick per-video step X9: the QC stack (counts, size, blend, solidity, timeline, guardrails). Internal to that command.
user-invocable: false
---

# atp-qc — Step X9: QC

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- anomaly-catalog §4: `ATP/reference/anomaly-catalog/220_4_the-qc-stack-x9-in-order.md` (6.2 KB)
- anomaly-catalog §2.14: `ATP/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.9 KB)
- *a product handled, prepared, used, poured or counted on screen:*
  - anomaly-catalog §2.1: `ATP/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.5 KB)
  - anomaly-catalog §2.2: `ATP/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (3.0 KB)
  - anomaly-catalog §2.3: `ATP/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.7 KB)
  - anomaly-catalog §2.4: `ATP/reference/anomaly-catalog/070_2.4_irreversible-and-persistent-stat.md` (1.4 KB)
  - anomaly-catalog §2.5: `ATP/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
  - anomaly-catalog §2.6: `ATP/reference/anomaly-catalog/090_2.6_liquids-powders-and-materials.md` (1.9 KB)
  - anomaly-catalog §2.8: `ATP/reference/anomaly-catalog/110_2.8_body-mechanics-at-the-product.md` (1.5 KB)
- *a placed or contents product (size, label, blend, posture checks):*
  - anomaly-catalog §2.7: `ATP/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.1 KB)
  - anomaly-catalog §2.9: `ATP/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.3 KB)
  - anomaly-catalog §2.15: `ATP/reference/anomaly-catalog/180_2.15_blend-a-render-not-a-paste.md` (8.3 KB)
  - anomaly-catalog §2.16: `ATP/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (4.3 KB)
- *a person is swapped (skin tone face vs hands):*
  - anomaly-catalog §2.17: `ATP/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- generation-system §9: `ATP/reference/generation-system/340_9_post-generation-qc-after-downloa.md` (8.0 KB)
- generation-system §9b: `ATP/reference/generation-system/350_9b_what-must-not-survive-and-what-i.md` (4.6 KB)
- generation-system §5b: `ATP/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5d: `ATP/reference/generation-system/300_5d_counts-openings-and-object-perma.md` (1.7 KB)
- *a contents video, or a vessel of the product's category:*
  - generation-system §4b.0: `ATP/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
- *a placed product (posture):*
  - generation-system §4b.1b: `ATP/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (3.1 KB)
- *the plan has a size-and-place guide, or a size retry adds one:*
  - generation-system §4b.6: `ATP/reference/generation-system/200_4b.6_the-size-and-place-guide-a-refer.md` (4.1 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2b: `ATP/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.2 KB)
  - generation-system §5c.5: `ATP/reference/generation-system/290_5c.5_measure-it-after-the-merge.md` (1.3 KB)
- *a multi-clip video, or a source with hard cuts (shot structure):*
  - generation-system §3b.1: `ATP/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.3 KB)
  - generation-system §3b.3: `ATP/reference/generation-system/070_3b.3_seam-discipline.md` (2.4 KB)
- creative-direction §8: `ATP/reference/creative-direction/110_8_creative-qc-x9-as-notes-the-narr.md` (0.9 KB)
- brand-guardrails §5: `ATP/reference/brand-guardrails/050_5_qc-x9-and-the-wrap-up.md` (1.2 KB)
- *Analyze Mode (the CapCut project):*
  - capcut-assembly §5: `ATP/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.2 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §5 (failure table); §9 when a retry is planned
- the plan's QC checkpoints (`RUN/40-briefs/video-NN-plan.md`), the contract's checks (`ATP/reference/production-agents/` §3 item 13, for a production agent)

## Step X9

- **X9 — QC.**
  - `T qc --video <final> --out <dir> --mode <mode> --allowed-text "<planned text>|<printed words of
    every visible client asset>" --dense "<label>:<a>-<b>" …` with every QC checkpoint of the plan,
    then view the storyboard sheets and every dense sheet under `<dir>/dense/`.
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
    --distance d --distance-basis "<how d was derived from the frame>" --lens f`: two estimates, the
    neighbour ratio (A) and the frame fraction at a distance derived from the surface or another object
    (B), which must agree before an oversize verdict (`inconclusive` means re-derive). A verdict from one
    assumed number is PROVISIONAL ("provisional: distance assumed"): never a regenerate reason or a
    RESIDUAL FAILURE, and viewed on the full-resolution frame by whoever reports it before it is flagged,
    repeated or summarised (CE-028). Write the multiple of the expected size with its method and distance
    in the verdict and compare across cuts. Over 25 % on agreeing estimates, a size that changes between
    shots, or a product larger than
    the hand that holds it is a regenerate reason with no post-fix; 15–25 % is a note only for a
    static product with a readable label. The retry changes the lever the guide names. For a model
    whose guide lists size as a model limit (`wan3_0_prime`) it changes the lever: the size-and-place
    guide (`generation-system.md` §4b.6), the integration form (§4b.0) or the anchor class from the guide's
    passing list, never the sizing words (12 of 12 wording retries were re-rolls);
    otherwise it names the neighbour and the ratio, the depth and the fraction of the frame, pads the
    reference and rebuilds any start frame. A second miss ships the best take flagged, both attempts written as blocks in the brief.
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
    as an ad, the planned emotion arc, the loop; Create: the copy test against the family's
    references and the run's other videos (craft shared, subject not). A missing hook or payoff that
    the plan required is a narrative-gate failure and a regenerate reason; everything else is a
    note, never a question.
  - **Action sync** (item 19; Edit Mode and Recreate): the X8 sync verdict and sheet. Every sync
    anchor lands within ±0.1 s of its sound: words on mouth movements, impacts on contact, steps on
    footfalls. Drift, or an action added, skipped or moved, is a regenerate reason; a steady offset
    is a post-fix.
  - **Leftovers** (`generation-system.md` §9b): only the must-not-survive list counts, and it is
    fixed autonomously.
  - **Label legibility** (`anomaly-catalog.md` §2.9, §4 step 5h): on a full-resolution frame at rest the
    wordmark and the variant tag (flavour, size or model) read exactly, word by word against the asset, the frame path in the
    verdict; a wrong letter is a regenerate reason, and upscaling is no fix.
  - **Hand lanes, camera path and orientation** (`anomaly-catalog.md` §2.16; `generation-system.md` §5c.5,
    §5c.2b): no hand covers, wraps or passes through the placed product in any beat; the product stays in
    frame wherever its anchor does; the camera and the performer's pose in the last third match the source;
    every readable thing and handed object reads the right way round. A guide's artefacts copied into the
    take (a soft label, a thick rim, a lid notch, the source's scene or person) are a regenerate reason.
  - **Shot structure** (`anomaly-catalog.md` §4 step 5i; `generation-system.md` §3b.1 item 7; Recreate and
    Edit Mode with hard cuts): the output's cuts against the source's shot list: the same count at the same
    times, person-free cutaways still person-free, the placed product in every shot where its anchor is in
    frame, the closing emotion beat present; a merged, dropped or dissolved shot is a regenerate reason.
  - **Every regenerate reason found here is written at once** in the video's brief as an attempt block (the
    failed request.json, the verdict with its numbers and frame paths, what the retry changes) and, in
    Analyze Mode, in `result.json`; the retry changes the lever the diagnosis names (item 22).
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

## Rules this phase owns (contract items 14, 19, 21)

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
    - after the merge, `T sync-check` measures the timing (X8 step 5). A steady offset is fixed in
      post. Drift or a moved action is a regenerate reason in Recreate, or the first QC note in
      Edit Mode.
    Create is not affected: it makes new scenes, and its sound is built in CapCut on their own
    beats.
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

- Never let source identities or competitor branding survive when approved replacements exist.
- Never pin free physical motion (spins, tosses, rolls, pours, a vehicle's moves) to exact
  timestamps. Never accept a snap, a pause-and-resume, a slide without a cause, or a morphing
  label or badge (`generation-system.md` §5b).
- Never flag, ask about or spend a retry on incidental background items: posters, toys,
  ornaments, signs, and clothing or footwear logos (`generation-system.md` §9b). Only the §9b
  must-not-survive list counts.
- Never let a placed product jump between spots (desk → table → chair), appear or vanish without a
  visible action, be missing from frame 0 (CE-018), drift along its surface with no cause (CE-019),
  become the hero of the shot, or look composited.
- Never leave a glass, cup or other vessel of the product's category holding something else (water
  beside the can) when the product's contents fit, and never let a prop from an asset photo carry
  over unplanned.
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
- Never accept a placed product's wordmark or variant tag (flavour, size or model) that reads as wrong letters, a paste sign written as
  a note, or "it is close to the camera" as a reason without the numbers (`anomaly-catalog.md` §2.7, §2.9,
  §2.15).
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
- Never deliver a video that carries the original audio without its sync check (X8 step 5), and
  never leave drift or a moved action unreported. Never fix sync by stretching or looping the
  original audio.

## Hand-off

- Edit Mode: the findings become the QC notes of the review. Return to the review (X9-R) in `atp-edit` (re-invoke it if its text is no longer in context); there is no automatic regeneration.
- Analyze Mode, the picture passed but the CapCut project is not built yet: go back to `atp-postprocess` step 6, then return here for the project checks.
- Analyze Mode, accepted (picture and project): invoke Skill `atp-record` (X10).
- Analyze Mode, one diagnosed regeneration: `atp-write-request` (the rewritten request; the diagnosis is already written in the brief as an attempt block) → `atp-inputs` only for new inputs → `atp-submit` (X5 again, X7, next attempt number) → `atp-postprocess` → `atp-qc`.
