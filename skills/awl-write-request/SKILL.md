---
name: awl-write-request
description: /analyze-with-loupe per-video step X2: pattern card and Higgsfield request in the model's own structure. Internal to that command.
user-invocable: false
---

# awl-write-request — Step X2: pattern card and request

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

A production agent comes here only to rewrite a request for its one diagnosed regeneration (then `awl-inputs` for new inputs only, `awl-submit` for X5 and X7).

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `awl-model-guide`) — §2.4 (call recipes), §2.6 (9:16/720p), §3.1–§3.7 (structure, subject and identity, action, environment and light, chronology, camera, references), §3.10–§3.14 (negatives, visible text, identity consistency, product fidelity, integration), §4.0 (official examples: the pattern card) and the §4.x of the request kind (4.1 text-to-video, 4.2 frames, 4.3 reference, 4.4 edit/extension); §3.8 when frames are used; §3.9 when audio is used; §6 when a model feature is planned
- generation-system §4: `AWL/reference/generation-system/100_4_replacement-and-insertion-integr.md` (3.3 KB)
- generation-system §6: `AWL/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (4.3 KB)
- generation-system §5b: `AWL/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5c.3: `AWL/reference/generation-system/270_5c.3_the-fidelity-lock-in-the-prompt.md` (3.1 KB)
- generation-system §7: `AWL/reference/generation-system/320_7_translating-the-plan-into-the-se.md` (2.7 KB)
- generation-system §4b.5: `AWL/reference/generation-system/190_4b.5_expressing-it-to-the-model-with.md` (4.3 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2: `AWL/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
  - generation-system §5c.2b: `AWL/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.5 KB)
- *a placed or contents product (the spot):*
  - generation-system §4b.1c: `AWL/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- anomaly-catalog §3: `AWL/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.4 KB)
- *a product in use, prepared or counted:*
  - anomaly-catalog §2.1: `AWL/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.2 KB)
  - anomaly-catalog §2.2: `AWL/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (2.8 KB)
  - anomaly-catalog §2.3: `AWL/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.5 KB)
  - anomaly-catalog §2.5: `AWL/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
- *a placed or contents product (size words):*
  - anomaly-catalog §2.7: `AWL/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (12.3 KB)
- *the video shows a throw/pass (solidity lines):*
  - anomaly-catalog §2.14: `AWL/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.4 KB)
- *a placed or contents product (blend lines):*
  - anomaly-catalog §2.15: `AWL/reference/anomaly-catalog/180_2.15_blend-a-render-not-a-paste.md` (9.6 KB)
- *a person is swapped (the skin-tone sentence):*
  - anomaly-catalog §2.17: `AWL/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- text-and-format §1: `AWL/reference/text-and-format/010_1_text-policy-depends-on-the-mode.md` (5.7 KB)
- *guardrail operations in the plan:*
  - brand-guardrails §4: `AWL/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- *an own voiceover (the plan has a Voiceover block; item 31):*
  - voiceover §6: `AWL/reference/voiceover/060_6_in-the-request-x2-by-what-the-lo.md` (3.3 KB); the locked guide's §2.2, §3.7 and §3.9 with it
- the plan `RUN/40-briefs/video-NN-plan.md` (X1)

## Step X2

**Free runs:** the requirement's intent for this video (its free-plan lines) is translated into the locked model's own prompting structure, recipes and official examples exactly as below; the user's sentences are never pasted as the prompt, and the model guide's structure wins where the two differ in form (the intent stays).


- **X2 — Pattern card and request.**
  - From the selected guide's **§4.0 official examples**, write the pattern card
    (`50-requests/video-NN-pattern.md`).
  - Decide the channel for everything: parameters vs. references vs. prompt vs. post-production.
  - **The judge writes the final prompt after X4 (the first request of a video; the user, 2026-10-28).** X2 writes the pipeline's own request
    by every step below, as always: it is the **checked draft** (X4 checks it next). Write with it the pattern card's **"Must carry"** block and
    the same lines in `RUN/40-briefs/video-NN-musts.md`, one per line, word for word: every sentence the prompt must carry exactly (the fidelity
    lock, the clean-plate lines, the camera lock, the product's targeted exclusion, a guardrail operation, the
    voiceover's dialogue or no-dialogue line). X2 never asks the judge: after X4, `awl-precheck` X4b hands the judge the whole checked brief
    (the plan's beats and goal, this draft, its must-carry lines, the model's structure) and the judge's answer becomes the request's prompt,
    word for word (`T template-apply`).
  - **A regeneration or a re-edit** never asks the judge for a new prompt: the corrected prompt is the request's prompt (the judge's) with the
    judge's `template_fix` from the QC consult in place of the part it names (`awl-qc`), every other part word for word; with no `template_fix`,
    only the part that let the error happen is crafted again by the steps below, every unrelated part kept.
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
      guide's passing list or wrote the size risk in the brief, and a start frame is out of reach
      while the source rides as a video reference. A start frame's product is a photoreal render that
      passed the paste test.
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
    - The **camera lock, the swap grammar, the empty surfaces and the prepared-source sentence**, where the plan
      has them, in the model's phrasing (`generation-system.md` §4, §4b.5, §5c.2b, §5c.3): in Recreate and Edit
      Mode, whatever the model, the original reference is bound by purpose in the model's own reference syntax
      (the guide's §3.7): the silent footage in the model's most preserving input, for the performers, motion,
      camera, framing, timing, scene and light, the full keep-list; it is the only video reference, and an
      exclusion of the original's content ("do not inherit … branded items of Video 1") never covers the product
      the request places; the product's own views ride padded, never a tight packshot; the anchor sentence writes
      the spot (pinned to a fixed neighbour) and the size (against a named neighbour), and asks for a real object
      in the scene (its material, the scene's light and shadows, real contact with its surface); no guide image
      cut from a source frame is bound; the camera lock as its own sentence; a swap written as a
      replacement; an empty surface written empty, per shot; "Video 1 is already in true orientation" after a
      flip; the one hand in frame named with the bare empty area; the clean-plate lines never cut to fit the
      length limit (`text-and-format.md` §1).
    - **Guardrail operations** in the model's own edit syntax (`brand-guardrails.md` §4): remove only the named
      item or mark, reconstruct what is behind it, keep everything else exactly as it is (a mark removed leaves a plain
      product of the same shape, size, position and lighting); the person-replacement contract for an
      excluded person. Never "blur", "pixelate" or "cover".
    - Analyze Mode prompts are always **clean plates**: no overlay text. The only lettering is the
      product's own label, logo or badge.
    - **Own voiceover** (the plan's Voiceover block; item 31): build the request by the run's method (its guide's §2.2, §3.7 and §3.9;
      the table of `voiceover.md` §6): **native** binds the take as the driving audio, **lipsync** writes its words verbatim as dialogue
      (the sync pass is the agent's, in X8), **overlay** writes the no-dialogue line; the duration as §6 says; no music.
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

- Never ask the judge in X2 (it is asked once, after X4: `awl-precheck` X4b), never on a regeneration or a re-edit, and never
  rewrite, trim or reorder its prompt. Never name a past miss's wrong behaviour in a prompt, and never paste another video's
  sentences (a basis sample's prompts file, `T sample-prompts`) into a request: the judge's prompt already carries what
  worked, adapted to this video.
- Never use the flawed take (the clip QC rejected) for its regeneration: not as a video input, a start or end frame
  or a reference, and never fix one frame of it or ask the model to edit it. The regeneration goes out with the
  inputs of the first attempt (the original source video, when the video has one), and a whole request crafted again: the
  diagnosed cause designed out in what the model should do, every part unrelated to the error kept.
- Never apply generic prompting when a model guide exists.
- Never let the video model render overlay text in Analyze Mode. Generate clean and place the text
  in CapCut. Never burn it in with `awl.py captions`, except as the stated fallback.
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
  it (`generation-system.md` §4b.1c); never build, upload or bind a guide image cut from a source frame, or any
  placement image beside the original (§4b.5); never upload a mirrored selfie source un-flipped in Recreate, or leave a baked
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

- Edit Mode: invoke Skill `awl-inputs` (X3).
- Analyze Mode (this session, A9 step 1): continue with X4 → invoke Skill `awl-precheck` (X4 only) for this video.
- A regeneration or a re-edit with a rewritten request: `awl-inputs` only for new or replaced inputs, then Skill `awl-submit` (X5 again, X7).
