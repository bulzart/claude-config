---
name: atg-write-request
description: /analyze-then-generate per-video step X2: pattern card and Higgsfield request in the model's own structure. Internal to that command.
user-invocable: false
---

# atg-write-request — Step X2: pattern card and request

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

A production agent comes here only to rewrite a request for its one diagnosed regeneration (then `atg-inputs` for new inputs only, `atg-submit` for X5 and X7).

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atg-model-guide`) — §2.4 (call recipes), §2.6 (9:16/720p), §3.1–§3.7 (structure, subject and identity, action, environment and light, chronology, camera, references), §3.10–§3.14 (negatives, visible text, identity consistency, product fidelity, integration), §4.0 (official examples: the pattern card) and the §4.x of the request kind (4.1 text-to-video, 4.2 frames, 4.3 reference, 4.4 edit/extension); §3.8 when frames are used; §3.9 when audio is used; §6 when a model feature is planned
- generation-system §4: `ATG/reference/generation-system/100_4_replacement-and-insertion-integr.md` (3.3 KB)
- generation-system §6: `ATG/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (3.7 KB)
- generation-system §5b: `ATG/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5c.3: `ATG/reference/generation-system/270_5c.3_the-fidelity-lock-in-the-prompt.md` (3.1 KB)
- generation-system §7: `ATG/reference/generation-system/320_7_translating-the-plan-into-the-se.md` (2.7 KB)
- generation-system §4b.5: `ATG/reference/generation-system/190_4b.5_expressing-it-to-the-model-with.md` (4.0 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2: `ATG/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
  - generation-system §5c.2b: `ATG/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.2 KB)
- *a placed or contents product (the spot):*
  - generation-system §4b.1c: `ATG/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- *the plan has a size-and-place guide, or a retry adds one:*
  - generation-system §4b.6: `ATG/reference/generation-system/200_4b.6_the-size-and-place-guide-a-refer.md` (4.1 KB)
- anomaly-catalog §3: `ATG/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.1 KB)
- *a product in use, prepared or counted:*
  - anomaly-catalog §2.1: `ATG/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.2 KB)
  - anomaly-catalog §2.2: `ATG/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (2.8 KB)
  - anomaly-catalog §2.3: `ATG/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.5 KB)
  - anomaly-catalog §2.5: `ATG/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
- *a placed or contents product (size words):*
  - anomaly-catalog §2.7: `ATG/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.5 KB)
- *the video shows a throw/pass (solidity lines):*
  - anomaly-catalog §2.14: `ATG/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.3 KB)
- *a placed or contents product (blend lines):*
  - anomaly-catalog §2.15: `ATG/reference/anomaly-catalog/180_2.15_blend-a-render-not-a-paste.md` (8.1 KB)
- *a person is swapped (the skin-tone sentence):*
  - anomaly-catalog §2.17: `ATG/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- text-and-format §1: `ATG/reference/text-and-format/010_1_text-policy-depends-on-the-mode.md` (5.7 KB)
- *guardrail operations in the plan:*
  - brand-guardrails §4: `ATG/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- the plan `RUN/40-briefs/video-NN-plan.md` (X1)

## Step X2

- **X2 — Pattern card and request.**
  - From the selected guide's **§4.0 official examples**, write the pattern card
    (`50-requests/video-NN-pattern.md`).
  - Decide the channel for everything: parameters vs. references vs. prompt vs. post-production.
  - **Sample hints (the first request of a video only).** The admin keeps past misses in Loupe; one separate
    keeper session holds them. Ask it once, before the prompt is written, in text only: `T plan-hints --run RUN
    --video NN --beats "<one line per beat of the plan: what happens, the product's form and state, the camera>"
    --product "<form>" --product-details "<its shape, size, opening and natural posture, from its registry row>"`. A regeneration never asks: it works from its own diagnosed cause (`atg-qc`). The answer
    has 0 to 3 hints, and 0 is the normal answer (`mode: empty` or `unavailable` also mean none: write the
    request as always). Each hint has a `trigger` (the plan situation where that miss arises), a `right_outcome`,
    a `lever` and a `caveat`.
    - A hint is a risk to check this plan against, never prompt text. Do not copy its words, do not name the wrong
      behaviour anywhere in the prompt or the reference notes (a thing that is named, even in a negative, is what
      comes back: `generation-system.md` §4, §5c.2b), and add no negative list beyond the product's one targeted
      exclusion.
    - Apply a hint only if its `trigger` matches a beat of this plan and its `caveat` does not exclude it;
      otherwise change nothing. Apply it by the smallest change inside the prompting stack
      (`anomaly-catalog.md` §3): the restatement at that beat, the product's targeted exclusion, the reference
      view, the beat written as start state, operation, result, or the anchor, written positively as the hint's
      `right_outcome`. Touch only the matching beat: no new element, camera move or sentence elsewhere, nothing of
      the source's story, timing or the locked model changes, and any rule of this phase wins a conflict.
    - A hint that comes from a scenario (`sample_kind: scenario`: the admin's idea, what could be better, what the agents missed) states a situation to check the plan against; it carries no right outcome of its own beyond the admin's words, so apply it only as a plain restatement at the matching beat. A hint that comes from a miss example (the admin never had a right version for it) may carry no `right_outcome` of its own:
      apply it only when its lever is a plain restatement at the matching beat (the count, the state or the orientation the plan
      already intends, said once positively); otherwise leave it out. Never invent what a right version would look like.
    - At most two hints are applied per video. A hint whose application would reshape more than one clause of
      the prompt is over-applied: drop it. When the video is already planned correctly, applying nothing is right.
    - Write the decisions as a short "Sample hints" block at the end of the pattern card: per hint, its id,
      applied to which beat with the change in one line, or not applied and why. X4 checks it and X6 copies it
      into the brief. The hints themselves are in `40-briefs/video-NN-hints.json`; never paste them into the
      brief or the prompt.
  - **Reason first** (`generation-system.md` §6). For every beat that places, moves or uses the product, derive what the plan or source
    needs there, what the product's own details allow (its registry row, affordance sheet and `product_properties.txt`) and what the
    source scene offers, then write the one state all three allow, once, in positive words. The rules below are checks on that result,
    never lines to paste: no "never" or "always" in the prompt, at most one targeted exclusion per product, and no two sentences that
    ask opposite things of a beat (the higher authority in §6 wins, the other line is dropped, one line of reason goes in the pattern card).
    An example sentence in a reference or a guide shows a mechanism for another case: write this video's own nouns.
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
      (against a named neighbour at the same depth), the depth (its distance from the camera), the fraction of the
      frame when the model takes it, the size ladder when several products show, and the constancy line. The
      reference image is padded so the product does not fill it, and a start frame is built at
      the reckoned pixel height and measured with `T scale --frame … --product-px … --ref-cm …
      --ref-px …` before it is animated. Where the guide lists size as a model limit
      (`wan3_0_prime`), these words are a check, not a control: X1 chose the anchor class from the
      guide's passing list or planned a size-and-place guide (§4b.6), and a start frame is out of reach
      while the source rides as a video reference.
    - Every vessel's contents are stated from the contents sample; an unstated vessel comes back as
      water. A character photo's role is limited to the person (face, hair, build and clothing, not its
      props or background) unless the plan keeps its props as the product's contents
      (`generation-system.md` §4b.5).
    - Free physical motion (a spin, toss, roll or pour, or a vehicle's move) is described by its
      physics, never by a schedule of exact times. A required end state gets a visible cause, such
      as a hand stopping the product label-forward or a driver braking into the spot
      (`generation-system.md` §5b). A corrected retry removes timing constraints from free motion;
      it never adds them.
    - Every **use beat** is written as initial state → operation on the named part → observable
      result, with the contact point, orientation and body mechanics of the product's affordance
      sheet. Every **multiple** carries its number at t=0, at each event and at
      the end, restated after exits, occlusions, cuts, hand-offs and seams. Each product gets **one
      targeted exclusion**: the one wrong use or count that this product's own details make possible
      (its other end, a second copy, a count that changes). No reference image shows a
      later state than t=0 (`anomaly-catalog.md` §3). Every thrown, dropped, swung or passing thing
      has its path written relative to the product, past it on a named side or onto it with the
      consequence, plus the solidity exclusion (`anomaly-catalog.md` §2.14).
    - The **guide, the camera lock, the swap grammar, the empty surfaces and the prepared-source sentence**,
      where the plan has them, in the model's phrasing (`generation-system.md` §4, §4b.5, §4b.6, §5c.2b,
      §5c.3): the guide bound as spot and size only; the camera lock as its own sentence; a swap written as a
      replacement; an empty surface written empty, per shot; "Video 1 is already in true orientation" after a
      flip; the one hand in frame named with the bare empty area; the clean-plate lines never cut to fit the
      length limit (`text-and-format.md` §1).
    - **Guardrail operations** in the model's own edit syntax (`brand-guardrails.md` §4): remove only the named
      item or mark, reconstruct what is behind it, keep everything else exactly as it is (a mark removed leaves a plain
      product of the same shape, size, position and lighting); the person-replacement contract for an
      excluded person. Never "blur", "pixelate" or "cover".
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

## Rules this phase owns (contract items 5, 19)

5. **Fixed output: vertical 9:16 at 720p (720×1280)** for every generation in both modes. Never ask.
   Map it to each model's own parameters (`index.json → output_9x16_720p`) and conform
   deterministically. Never stretch.
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

## Never (this phase)

- Never ask for sample hints on a regeneration or a re-edit, never copy a hint's words into a prompt, never name a past
  miss's wrong behaviour in a prompt, never apply a hint to a beat its trigger does not match, and never apply more
  than two per video.
- Never apply generic prompting when a model guide exists.
- Never let the video model render overlay text in Analyze Mode. Generate clean and place the text
  in CapCut. Never burn it in with `atg.py captions`, except as the stated fallback.
- Never keep source text in Edit Mode unless the user kept that specific text.
- Never let source identities or competitor branding survive when approved replacements exist.
- Never pin free physical motion (spins, tosses, rolls, pours, a vehicle's moves) to exact
  timestamps. Never accept a snap, a pause-and-resume, a slide without a cause, or a morphing
  label or badge (`generation-system.md` §5b).
- Never deform a client asset's canonical geometry or identity to fit a reference object.
- Never sacrifice temporal or physical continuity to imitate an individual source frame.
- Never accept a product that fails the paste test: brighter, cooler, sharper or cleaner than its
  neighbours, lit from the front in a room lit from elsewhere, without a contact shadow, squared to
  the lens, at the wrong size or perspective, or alone on an empty edge (`anomaly-catalog.md`
  §2.15). Never bind a product reference without scoping out its lighting, exposure, background
  and camera angle.
- Never let anything pass through the product or any other solid thing, sink into a surface or a
  hand, show through an opaque body, or hit something without a consequence
  (`anomaly-catalog.md` §2.14).
- Never place a product at a spot that is hidden at the source's frame 0, leaves the frame along the camera
  path, lies in a hand's lane, is narrower than the product or is the nearest plane unless the user marked
  it, and then only with a guide (`generation-system.md` §4b.1c); never build a size-and-place guide from an
  unscrubbed source frame (performer, clothing or lettering still in it), a flat packshot paste or a
  soft-labelled image (§4b.6); never upload a mirrored selfie source un-flipped in Recreate, or leave a baked
  face effect, a burned-in caption or an identifying name without its prompt sentence (§5c.2b); never try to
  remove a caption, a name or a patch from a source with a tool in Analyze Mode (inpaint, delogo, crop): the
  clean-plate lines and the character-swap script carry it.
- Never let a multiple change its number without a visible cause: three capsules on a desk are
  still three after the character walks past and comes back, unless they are seen being taken
  (`anomaly-catalog.md` §2.1, §2.5).
- Never let a product be used through a part that has no opening, through a closed one, or before
  the step that readies it: a straw bottle is drunk through its spout with the cap flipped open, a
  can from its opened top after the tab is lifted (§2.2, §2.3).
- Never stretch to reach 9:16, never ask for aspect ratio or resolution, and never deliver anything
  other than 720×1280.
- Never send an Edit Mode or Recreate request, the first one included, without the fidelity lock
  (item 19): the change scoped with "only", the full keep-list, the exclusions and, for models that
  rebuild the action, the source action script written out in order.

## Hand-off

- Edit Mode: invoke Skill `atg-inputs` (X3).
- Analyze Mode (this session, A9 step 1): continue with X4 → invoke Skill `atg-precheck` (X4 only) for this video.
- A regeneration or a re-edit with a rewritten request: `atg-inputs` only for new or replaced inputs, then Skill `atg-submit` (X5 again, X7).
