---
name: atp-asset-plan
description: /analyze-then-pick Analyze Mode phase: asset plan and the long-video permission (A7–A7b). Internal to that command.
user-invocable: false
---

# atp-asset-plan — Analyze Mode: asset plan, long videos (A7–A7b)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- assets-and-substitution §3: `ATP/reference/assets-and-substitution/030_3_asset-registry-30-assets-registr.md` (1.5 KB)
- assets-and-substitution §4: `ATP/reference/assets-and-substitution/040_4_substitution-map-per-video.md` (2.4 KB)
- generation-system §4b.0: `ATP/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
- generation-system §4b.1: `ATP/reference/generation-system/130_4b.1_choose-the-anchor-by-the-product.md` (2.4 KB)
- generation-system §3b.1: `ATP/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.3 KB)
- generation-system §3b.2: `ATP/reference/generation-system/060_3b.2_join-methods-by-the-locked-model.md` (3.2 KB)
- *Recreate (a person is swapped for a supplied character: choose the character by comparison, not by turn):*
  - anomaly-catalog §2.17: `ATP/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- the locked model's `continuation` entry: `T model-entry --id <model>`

### A7. Asset plan (autonomous — picks from the supplied assets only)
- For every planned video, choose from the registry (A2b) the assets that fit its direction
  (Create) or its reference (Recreate):
  - which product or object entity, and which variant (with its contents sample when needed);
  - which character(s). Recreate: which character replaces which person;
  - any interface, brand or environment asset.
- **Fit the brand to the scene first** (CE-020): a food, grill, party or sport scene suits a drink; a
  desk, class, meeting, work or commute scene suits a focus product. The plan states the tie in one
  line, and a reference with no tie for one brand goes to the other, whatever free surface it offers.
- **Then the form** (CE-007): where one product comes in several packages, pick the form that fits the
  scene's scale and register: the smallest closed form in a casual handheld scene, a large pack only where
  a large pack belongs (a large stand-up pouch in a phone-and-couch scene read as too much; the small
  carton fits). The forms keep their real size ladder (a pouch is larger than a carton, a carton larger than
  a sachet): a retry changes the anchor or the posture of the same form, and a smaller form is never put in
  for a planned one, because the client reads it as a different product ("Idea is great, the bag is too small
  here. This would be the size of the box packaging. The bag is bigger than the boxes", CE-033: a sachet
  stood in for the pouch and read carton-sized).
- **Then distribute sensibly.** Spread several products or variants across videos unless the user or a
  document says otherwise. Rotate approved characters when no assignment is given. Pair assets that
  belong together (a product with its own label close-up).
- For each product, record its integration form, **swap**, **contents** or **placement**
  (`generation-system.md` §4b.0). The exact anchor is decided in X1.
  - **Recreate:** from the reference card's client-entity fit.
  - **Create:** designed into the new concept, as the product's most natural use and blend in that
    scene.
  - **Contents** needs the chosen variant's contents sample (e.g. the liquid photo of that flavour).
  - **Contents comes first** whenever the scene gives the subject a vessel of the product's category
    (a glass on the café table): the vessel holds the product, and the package stands beside it.
  - Pick a variant that has one. With none supplied, fall back to placement and say so.
- **House approach** (when examples exist): where it is consistent, it decides the anchor style,
  prominence, how often the product is used, and the clip and text habits. Record which of its rules
  each video applies.
- Give every video a **planned length**:
  - **Create:** its direction's typical length, adapted to the concept;
  - **Recreate:** the reference's own length.
  Only the generated or edited part counts toward generations: inserts are cut, never generated.
- Show the plan in one line per video and proceed; the user can change it by replying. Examples:
  - `Video 2 — D3 — ~12 s — product B (variant 2) via placement (in hand) + character "anna"`;
  - `Video 3 — D1 — ~45 s (2 generations) — product A via swap of the source can`;
  - `Video 4 — D2 — ~27 s (25 s generated + 2 s meme) — product A (peach) as contents: cup + open can`;
  - `Video 5 — D4 — ~15 s — product C (the car, red) via placement: parked at the curb behind him`.
- **Never** fill a gap from the references folder. If a planned concept needs something that was not
  supplied, adapt the concept to the supplied assets, e.g. hands-only POV when no character was
  supplied. If no adaptation keeps the direction's mechanism, ask one question: drop the element, or
  let the user add files.
- Do not upload yet. Shared uploads happen once in A9; each video's own inputs come in its X3.

### A7b. Long videos: the only permission question in Analyze Mode
A video **over 30 s** that therefore needs **2 or more generations** with the locked model is never
generated without the user's permission. Nothing else in Analyze Mode asks for permission.
1. **Plan its clips first** (`generation-system.md` §3b):
   - the split points, on the reference's own cuts wherever possible;
   - the method for every seam (cut, native extension, or last-frame chain, from the model's
     `index.json → continuation` entry);
   - the cost. Preflight each distinct clip request with `get_cost`; prompt text does not change
     the price.
2. **Ask with AskUserQuestion** (header "Long video"): one question per long video, up to 4 per
   call. Question: "Video N (~45 s, D3) needs K generations with <model>. Generate it?" Options:
   - "Generate in K clips (≈C credits)" — the description says where the seams fall and how they
     join;
   - "Condense to one generation (≤<max> s, ≈C1 credits)": the same mechanism with tighter pacing;
   - "Skip this video".
   "Other" lets the user give a different length.
3. **Store each answer**, and never re-ask it on resume:
   `T state --run RUN set long_videos.NN='{"planned_s":45,"clips":K,"decision":"clips|condense|skip"}'`.
4. **When it applies, and when it doesn't:**
   - If the X1 plan later pushes a video that wasn't asked about over 30 s, ask then, for that
     video only.
   - A video of **30 s or less never asks**, even when the locked model needs several clips for it
     (a model with a shorter maximum). Its brief states the clip count.
   - Only **generated** content counts: reference inserts (memes) are cut, not generated
     (`generation-system.md` §3c). Example: a 35 s reference with 6 s of memes is one 29 s
     generation, so no question.

## Rules this phase owns (contract items 11, 14, 15)

11. **Client assets come only from paths the user gives.**
    - **Analyze Mode:** the user supplies all asset files and/or folders **once, at the start**. The
      command then understands them and uses them autonomously for every video.
    - **Edit Mode:** the user supplies the assets **for each edit**.
    - Never search for, detect, infer or pick client assets inside the references folder or the
      edit-source folder. Those can hold other products, samples or entirely different executions, so
      everything there is **reference material only**.
    - Never reuse one edit's assets for another edit unless the user says so.
    - The **examples folder** (item 18) is never a source of client assets either.
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
15. **Analyze Mode asks for permission in exactly one case:** a video **over 30 s that needs 2 or
    more generations** (A7b).
    - Everything else runs without confirmation: no "Go" question, no cost pauses, no QC questions.
    - Blockers are reported, not asked: the balance can't cover the next video, or Higgsfield
      itself demands a choice (`unlim_choice`, `recovery_tool`, §5 X7).
    - The planning questions (mode, model, inputs, number of videos, directions) are not
      permissions and stay.
    - Edit Mode keeps its gates (E6, X9-R).

## Never (this phase)

- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Never ask for assets again in Analyze Mode once they were dropped at the start (unless a concept
  cannot be adapted).
- Never re-type a context-bearing source overlay as text (CE-017, CE-023), never drop a keyword the user
  keeps (CE-027), never change a caption's subject to clear a guardrail (CE-022), and never give a brand a
  scene it has no tie to when the other brand fits (CE-020).
- Never leave the client's product out of an Analyze Mode video because the reference had nothing
  to swap. Integrate it instead, as contents or as a natural placement. Never force an unrelated
  source object into a swap.
- Never leave a glass, cup or other vessel of the product's category holding something else (water
  beside the can) when the product's contents fit, and never let a prop from an asset photo carry
  over unplanned.
- Analyze Mode: never ask for permission except for a video over 30 s that needs 2+ generations.
  Never generate any clip of such a video before that permission.

## Hand-off

`T state --run RUN set stage=asset_planned next_skill=atp-analyze-produce`, then invoke Skill `atp-analyze-produce`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
