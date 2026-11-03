---
name: awl-qc
description: /analyze-with-loupe per-video step X9: the QC stack (counts, size, blend, solidity, timeline, guardrails). Internal to that command.
user-invocable: false
---

# awl-qc — Step X9: QC

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- anomaly-catalog §4: `AWL/reference/anomaly-catalog/220_4_the-qc-stack-x9-in-order.md` (7.3 KB)
- anomaly-catalog §2.14: `AWL/reference/anomaly-catalog/170_2.14_solidity-collision-and-occlusion.md` (3.4 KB)
- *a product handled, prepared, used, poured or counted on screen:*
  - anomaly-catalog §2.1: `AWL/reference/anomaly-catalog/040_2.1_counts-and-conservation.md` (3.2 KB)
  - anomaly-catalog §2.2: `AWL/reference/anomaly-catalog/050_2.2_openings-and-use-affordances.md` (2.8 KB)
  - anomaly-catalog §2.3: `AWL/reference/anomaly-catalog/060_2.3_preparation-and-causality-cause.md` (1.5 KB)
  - anomaly-catalog §2.4: `AWL/reference/anomaly-catalog/070_2.4_irreversible-and-persistent-stat.md` (1.3 KB)
  - anomaly-catalog §2.5: `AWL/reference/anomaly-catalog/080_2.5_object-permanence-exits-occlusio.md` (1.5 KB)
  - anomaly-catalog §2.6: `AWL/reference/anomaly-catalog/090_2.6_liquids-powders-and-materials.md` (1.8 KB)
  - anomaly-catalog §2.8: `AWL/reference/anomaly-catalog/110_2.8_body-mechanics-at-the-product.md` (1.5 KB)
- *a placed or contents product (size, label, blend, posture checks):*
  - anomaly-catalog §2.7: `AWL/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (12.3 KB)
  - anomaly-catalog §2.9: `AWL/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.4 KB)
  - anomaly-catalog §2.15: `AWL/reference/anomaly-catalog/180_2.15_blend-a-render-not-a-paste.md` (9.6 KB)
  - anomaly-catalog §2.16: `AWL/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (3.9 KB)
- *a person is swapped (skin tone face vs hands):*
  - anomaly-catalog §2.17: `AWL/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- generation-system §9: `AWL/reference/generation-system/340_9_post-generation-qc-after-downloa.md` (8.6 KB)
- generation-system §6: `AWL/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (4.2 KB)
- generation-system §9b: `AWL/reference/generation-system/350_9b_what-must-not-survive-and-what-i.md` (4.7 KB)
- generation-system §5b: `AWL/reference/generation-system/220_5b_physical-motion-follows-physics.md` (2.9 KB)
- generation-system §5d: `AWL/reference/generation-system/300_5d_counts-openings-and-object-perma.md` (1.7 KB)
- *a contents video, or a vessel of the product's category:*
  - generation-system §4b.0: `AWL/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
- *a placed product (posture):*
  - generation-system §4b.1b: `AWL/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (2.6 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2b: `AWL/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.5 KB)
  - generation-system §5c.5: `AWL/reference/generation-system/290_5c.5_measure-it-after-the-merge.md` (2.3 KB)
- *a multi-clip video, or a source with hard cuts (shot structure):*
  - generation-system §3b.1: `AWL/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.7 KB)
  - generation-system §3b.3: `AWL/reference/generation-system/070_3b.3_seam-discipline.md` (2.5 KB)
- creative-direction §8: `AWL/reference/creative-direction/110_8_creative-qc-x9-as-notes-the-narr.md` (0.9 KB)
- brand-guardrails §5: `AWL/reference/brand-guardrails/050_5_qc-x9-and-the-wrap-up.md` (1.3 KB)
- *Analyze Mode (the CapCut project):*
  - capcut-assembly §5: `AWL/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.8 KB)
- *an own voiceover (the plan has a Voiceover block; item 31):*
  - voiceover §8: `AWL/reference/voiceover/080_8_after-the-generation-x8-by-metho.md` (3.3 KB) (the fix routes)
  - voiceover §10: `AWL/reference/voiceover/100_10_qc-of-a-voiceover-x9.md` (1.4 KB)
- *a `result.json` field this phase writes (a fix proposal under QC fixes `ask`, the keeper's gaps, the voiceover verdict):*
  - production-agents §4: `AWL/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.6 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `awl-model-guide`) — §5 (failure table); §9 when a retry is planned
- the plan's QC checkpoints (`RUN/40-briefs/video-NN-plan.md`), the contract's checks (`AWL/reference/production-agents/` §3 item 13, for a production agent)

## Step X9

**Free runs:** besides the stack below, every explicit want and forbid of the requirement for this video (the free plan's lines, the plan's checkpoints) is checked and written in the verdict with what was seen; a miss on one of them is a finding like any other (regenerate reason or note by its weight), under the QC-fixes choice (item 27).


- **X9 — QC.**
  - **Judge by reasoning, not by list** (`generation-system.md` §6). For every possible finding ask what the plan or source needed
    at that beat, what the product's real details allow (shape, size, opening, posture: its registry row) and what the scene offers.
    A finding is a deviation from the first, the second or physics, written as expected, why, seen. A deviation from a default alone is
    a note, never a regenerate reason. Three short evaluations of the same reasoning:
    - A flat sachet stands upright on a surface. Its details (thin, flat) cannot hold that and no support is visible: product details and
      physics, so a finding. The same sachet held upright in a hand is fine, because the hand is the support.
    - The product rests somewhere other than the usual place. Compare with the plan's anchor row, not with a habit: a deviation from the
      plan is a finding; a placement the plan and the source's scene call for is not, whatever the default would have been.
    - Two defaults seem to demand opposite things (a label that must read, a pack that lies flat). Read what this beat needs and judge
      by that need; never fail the video on one default to satisfy another.
  - **Samples first (Loupe, this phase only).** The admin keeps a library of generation misses in Loupe, each
    one image of the frames the admin chose (one to twelve), every frame tagged WRONG (red), RIGHT (green) or EXAMPLE (blue) with its own time and its source (a RIGHT frame can come from the right version or from an earlier part of the same video),
    a zoom under each frame the admin marked with a circle, arrow or box that alone carries that frame's marks, the frame above it left clean (no zoom under an unmarked frame; a frame alone in its row is shown as its clean normal-range shot with its marked close range beside it; a frame without a zoom, marked with a text label alone or over most of it, keeps its marks; `frame-N-marked.png` beside `composite_path` is each frame whole with its marks in place), and the admin's words burned in at the bottom beside the product sample
    the video used. A frame's source on its tag is `as generated`, `correct version` or `original video` (the source clip the generation was made from: what the source held, never a generated frame), with `· video NN` or `· run R video NN` when the admin took it from another video or run; the image's legend says the same. A separate read-only keeper session holds that library and nothing else, with what a data collector saw in every sample's picture (what the marks
    point at and the right frame; the full collection on file; no verdict: the judgement is the keeper's) that Loupe had a session make once by opening it; the picture itself stays
    the evidence you view. The judge (that keeper, on Opus) is consulted once your first pass over the sheets (the `T qc` bullet below)
    has caught what it caught: `T qc-consult --run RUN --video NN --attempt aK --question "<the errors you caught: what, where (time), at
    which beat or checkpoint; or none caught, with the product form, the beat and what the plan's checkpoints watch>" --kinds <counts,openings-use,scale-size,…>
    --product-details "<its shape, size, opening and natural posture, from its registry row>" --checkpoint "<a plan checkpoint>" …`
    (repeat `--checkpoint`). The consult carries by itself what the judge needs to judge an error accurately: the prompt this video was
    generated from (the request of `--attempt`, the newest otherwise) with that request's video model, parameters and inputs (each with
    the client's original it was made from, and its product images) and the model's entry of the model index, and the brief the judge got at X4b (`evidence_sent` says which; the request's prompt is the judge's, word for word). The answer adds `cause` (which part of the prompt or of the template let the error happen) and `template_fix` (that part
    rewritten): both go into the verdict and `result.json → judge`, for the user's review at the end. A regeneration (QC fixes `ask` or
    `auto`) takes `template_fix` in place of the part it names, every other part of the judge's prompt word for word (`awl-write-request`).
    When the error comes from the product images, the answer may add `product_images` (which of the client's images of the product the
    regeneration carries, and how many; `product_images_rule` says how): `T product-images --run RUN --video NN --request <the
    regeneration's request> --apply` puts them in it, and they go into `result.json → judge` too. The JSON line has `relevant` (or `samples`
    when `mode` is `fallback` or `busy`, the brief's own ranking while no keeper answered): each with `composite_path`, `frames` (role, where it comes from, time),
    the admin's words (`title`, and `details`, `correct_note`, `idea`, `better`, `missed` when given), where it came from (`model`, `run`, `video`, `t_wrong`, `kinds`),
    the keeper's `why`, `check` and `wrong_pattern`, `reading` (what a data collector saw in that picture, in two short fields, `marked` and `right_version`,
    no verdict, null when the sample has none yet) with `reading_path` (the whole collection: what each frame shows, the product and scene, the admin's words,
    what was unclear), and `advice`. **View every
    `composite_path`**, add what each says to look for as extra `--dense` checkpoints (a second `T qc` run for them), and write in the verdict
    which sample was compared and what was seen at the same place of this video. Read a `reading_path` only when the picture leaves the marked place
    unclear; it is the collector's description, never a verdict: the judgement is the keeper's and yours. `library_read` says how much of the library the keeper holds from the pictures: a sample in its
    `not_read` list was judged from the admin's words alone, so the picture you view decides for it. `mode: unavailable` or an
    empty list means no sample applies: QC goes on without them. On `mode: unavailable` while the contract's Loupe line (`state.json → loupe`,
    none = up) says `up`, run `T loupe ensure` once and ask again; if it stays unavailable the verdict says "no sample consulted: Loupe unavailable". The answer is also saved as
    `RUN/60-outputs/video-NN/qc-consult.json`. Ask the keeper **once per video**, after its first picture pass: the CapCut project pass and a
    regenerated take read the saved file again; ask again only when the product form, the beat or the plan's checkpoints changed. `T qc-brief` takes the same arguments with no model call; its answer is kept as `qc-brief.json`, never as the consult, and it writes no prompts files.
    A sample has a `sample_kind`: `pair` (a WRONG and a RIGHT frame), `miss-only` (`has_right: false`: no frame of it is called RIGHT, and a lone miss frame carries a grey NO RIGHT VERSION tag), or `scenario` (no frame is called WRONG: the admin's words only, frames the admin called RIGHT only (its record says THE CORRECT VERSION ONLY: how it looks when it is right, with the correct version's prompt alone), or frames the admin called EXAMPLE (blue: a suggestion of what could have changed or how it could have been done another way, neither a bad generation nor a correct one; a sample with Example frames has only Examples, one with WRONG or RIGHT frames has none); it carries `idea`, `better` and `missed`: what was meant to happen, what could have been better, what the AI agents missed or could not understand). A scenario is insight, not a visual pattern: compare the video with the idea and with what was missed, and never look for a match of the image. For a miss-only sample:
    it shows the wrong pattern to look for and nothing about what is right, so never infer a right look from it.
    A sample marked `prompts` (`pair`, `wrong` or `fixed`) keeps, each named by what it is, the flawed version's prompt (the prompt of each generation its frames called WRONG come from) and the correct version's prompt (each generation its frames called RIGHT come from, from either video), only the boxes it has frames for (frames called RIGHT only: the correct version's alone; WRONG only: the flawed version's alone), or, where `prompt_roles` says `example`, an Examples sample's one example box (the generations of its one video its Example frames come from; a suggestion of what could have changed or how it could have been done another way, neither a bad generation nor a correct one: never read it as the flawed or the correct prompt: `prompt_sides`); a box holds no other generation, each prompt under the line that says what it is, which seconds of which video it generated and which frames it made; with `prompt_note` (the admin's one line on what made the
    difference); the keeper read whole, before it answered, those of the samples in `prompts_judged` (up to ten cited samples per answer; any in `prompts_unread` it judged without them), and `qc-consult` writes them whole for you at `prompts_files[<id>]`
    (`RUN/40-briefs/samples/<id>-prompts.md`, from Loupe's record; no prompt is ever cut). For a sample you judged relevant to this video, Read that file and judge yourself what the correct version's
    prompt did differently from the flawed version's (a sample with one box: what that prompt secured, or let happen, at the frames it made; an example
    prompt: what it suggests, never a flawed or a correct prompt; nothing is compared or judged for you; `T sample-prompts` fetches any other sample). It is a lead for the diagnosed
    cause of a regenerate and for the corrected request (the `awl-write-request` rules: the mechanism in the model's own structure and your words, never a sentence pasted, never the
    wrong behaviour named), never a verdict on the video, and never read for a sample you did not judge relevant.
    A sample is a lead, never a verdict: a match is a regenerate reason only by this phase's own rules.
    Always pass `--run`, `--video` and `--attempt`: the keeper may ask Loupe for this video's plan, a frame, or the product's registry row, and Loupe reads them from the run.
    When the answer has `needs_unmet` (a question only you can answer by looking at your own video, or a file that does not exist), answer it in words and ask
    once more with `--note "<what you saw>"`; if it is still unmet, go on and write in the verdict what was not answered.
    **Keeper gaps reach the admin:** write the answer's `not_covered` (what the library does not cover for this video) and every need still unmet after
    the `--note`, and every flag of the judge (`flags`: what is missing, contradictory or ambiguous in a sample's record, as `flag S12: <what>`), into
    `result.json → keeper_gaps`, one line each (`production-agents.md` §4); the main session reports them in the wrap-up so the admin
    can add a sample in Loupe, and Loupe's Keeper page lists them too. A gap is information for the library, never a regenerate reason by itself.
  - `T qc --video <final> --out <dir> --mode <mode> --allowed-text "<planned text>|<printed words of
    every visible client asset>" --dense "<label>:<a>-<b>" …` with every QC checkpoint of the plan,
    then view the storyboard sheets and every dense sheet under `<dir>/dense/`. It returns measurements
    beside the expectations and no verdict: `checks` (`duration_s`, `aspect`, `size`, `has_audio`,
    `black_spans`, `freeze_starts`, `expected`, `size_delta_px`, `duration_delta_s`, `aspect_error_pct`,
    `mode`), `planned_text[]` (from `--allowed-text`), `visible_text[]` (every text the OCR saw, with its
    `first_t`, `last_t`, `hits`, `share_of_frames_scanned`, height `y_rel`, `score_mean`, `chars` and
    `band_distinct_texts`), `frames_scanned_for_text` and `dense_checkpoints`. **You** compare
    `planned_text` with `visible_text`, read the sheets, and write the QC verdict (it goes into
    `result.json` and the brief). Rules of thumb: a duration off by more than max(0.25 s, 5 %) is a duration
    problem; any black span or freeze needs a look; in Edit Mode no source text may remain unless it was
    explicitly kept; in Analyze Mode only the planned text may appear, and anything else is pseudo-text or a
    copied artifact. Whether a visible text is a caption, a fixed overlay, a watermark, a label or noise is
    your reading of those numbers and the picture.
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
    --distance d --distance-basis "<how d was derived from the frame>" --lens f`. It returns numbers and no
    verdict: `estimates[]`, two of them when both can be made, the neighbour ratio (A) and the frame
    fraction at a distance derived from the surface or another object (B), each with its `size_factor` (the
    observed size as a multiple of the expected size) and `deviation_pct`; also `size_vs_neighbour`,
    `size_vs_distance`, `estimates_spread_pct` (when there are two), the expected and observed values and
    `distance_basis` as you gave it. **You** read them under the guidance: within 15 % is fine; 15–25 % is a
    note, only for a static product with a readable label; over 25 % on agreeing estimates, a size that
    changes between shots, or a product larger than the hand that holds it is a regenerate reason with no
    post-fix; two estimates more than 25 % apart are inconclusive, so re-derive the distance and measure
    again on the full-resolution frame. A size read from one assumed number, with no neighbour estimate, is
    PROVISIONAL (your own label, "provisional: distance assumed"): not a regenerate reason or a RESIDUAL
    FAILURE until a second estimate agrees, and viewed on the full-resolution frame by whoever reports it
    before it is flagged, repeated or summarised (CE-028). Write the multiple of the expected size with its
    method and distance in the verdict and compare across cuts. The retry changes the lever the guide names. For a model
    whose guide lists size as a model limit (`wan3_0_prime`) it changes the lever: the integration
    form (`generation-system.md` §4b.0), the spot (§4b.1c) or the anchor class from the guide's
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
  - **Action sync** (item 19; Edit Mode and Recreate): your sync reading from X8 (the numbers and the
    sheet). Every sync anchor should land within ±0.1 s of its sound: words on mouth movements, impacts on
    contact, steps on footfalls. Drift, or an action added, skipped or moved, is a regenerate reason; a
    steady offset is a post-fix.
  - **Own voiceover** (item 31), once X8 step 5b ran: the checks and fix routes of `voiceover.md` §10 (the soundtrack, the lips, the face
    after a sync pass); a take that cannot fit is a `voiceover` blocker, never re-voiced here. The verdict goes to `result.json → voiceover`.
  - **Leftovers** (`generation-system.md` §9b): only the must-not-survive list counts, and it is
    fixed autonomously.
  - **Label legibility** (`anomaly-catalog.md` §2.9, §4 step 5h): on a full-resolution frame at rest the
    wordmark and the variant tag (flavour, size or model) read exactly, word by word against the asset, the frame path in the
    verdict; a wrong letter is a regenerate reason, and upscaling is no fix.
  - **Hand lanes, camera path and orientation** (`anomaly-catalog.md` §2.16; `generation-system.md` §5c.5,
    §5c.2b): no hand covers, wraps or passes through the placed product in any beat; the product stays in
    frame wherever its anchor does; the camera and the performer's pose in the last third match the source;
    every readable thing and handed object reads the right way round. A reference image's artefacts copied into
    the take (a soft label, a thick rim, a lid notch, the source's scene or person) are a regenerate reason.
  - **Clean takes** (Create and Free `create`, item 35): every take, on its storyboard and at full resolution, is one continuous shot
    (`capcut detect-scenes "<take>"` prints the cut points with their scores; you judge each: a real cut, montage, fade, wipe or dissolve
    inside a take is a regenerate reason, a fast in-world motion is not) and carries nothing editorial (a caption, title, label, sticker,
    emoji, arrow, badge, button, overlay logo, interface decoration, border, frame or panel divider, a split screen, picture-in-picture,
    grid or collage, a speed effect or a freeze, a decorative particle, glow, glitch or motion graphic): one found is a regenerate reason,
    never covered in CapCut. The in-world text the plan names reads as planned (`T qc --allowed-text`), and the art direction, the
    in-world effects and the continuity across takes hold as planned.
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
      cost a retry. In Analyze Mode QC asks the user nothing itself; with QC fixes `ask` it hands a fix proposal to the main session (item 27).
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
    screenshot. With `memes=none` (Create, item 32) there is none: only generated pictures, text layers, the soundtrack and ordinary
    sound effects, no meme of any kind (clip, still, screen recording, snippet or sound); one found is removed.
  - **CapCut project** (Analyze Mode, `capcut-assembly.md` §5):
    - the read-back timeline matches the plan (pieces, inserts, text times and positions; with `memes=none`, no insert at all);
    - overlays exist only on their visible frames and fade with the picture; a Recreate's original audio
      is one segment; no sticker or emoji is anywhere in the project, as a graphic or in a text layer (item 6);
    - an own voiceover is audible at 1.0 (native, lipsync: the clip's audio; overlay: its own track), nothing muted by mistake;
    - `capcut lint` reports 0 errors;
    - the preview shows the right order, sound and text;
    - Create (item 35): the read-back timeline matches the edit plan: every piece (its take, in, out, speed and track) in order, every
      keyframe, mask, transition, filter, graphic and text at its time, and what no tool could place listed in the README row (the
      preview flattens the main track only).
    Fix in the project, not by regenerating.
  - Apply the post-fixes (`trim`, `conform`, `restore-audio`, a sync offset) that need no new generation.
  - **Analyze Mode verdict** (the production agent's; item 27):
    - accept;
    - or **one** deliberate regeneration with a diagnosed, corrected request (a new ledger attempt;
      the preflight cost is shown in its brief). With QC fixes `auto` (the contract's "QC fixes" line, or `state.json → qc_fixes`; missing means `auto`) you submit it yourself.
      With `ask` you prepare it the same way (the attempt block in the brief, the corrected request by the `awl-write-request` rewrite, new inputs by `awl-inputs`, the X5 preflight) but
      do **not** submit it and do not call `T ledger begin`: write `result.json` with `"status":"blocked"`, `"blocker":"qc_fix_permission"` and a `fix_proposal`
      (`production-agents` §4), then stop. The main session asks the user and continues you with `approved`, `declined` or `auto`; you never ask the user yourself.
      `approved` or `auto`: go on at `awl-submit` (X7 with the prepared request, the next attempt number), then `awl-postprocess` and `awl-qc` as usual. `declined`: no further generation
      for this video; finish this take as it is, flagged: `awl-postprocess` step 5b first when an own voiceover has not been applied yet (item 31), step 6 if the project is not built yet, the project checks here, then `awl-record`, with `qc` = "declined fix: <the findings>".
      A second miss after an approved fix ships the best take flagged and asks nothing;
    - or report the failure honestly.

## Rules this phase owns (contract items 14, 19, 21, 27, 35)

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
    - after the merge, `T sync-check` measures the timing and returns numbers, not a verdict (X8 step
      5); you read them and the sheet. A steady offset is fixed in post. Drift or a moved action is a
      regenerate reason in Recreate, or the first QC note in Edit Mode.
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
27. **QC fixes (Recreate and Create).** A regenerate reason found here is fixed by a new generation only as the user chose at the start (`state.json → qc_fixes`): `auto`: the agent submits the one
    diagnosed regeneration itself; `ask`: the agent prepares it and stops with a `fix_proposal`, and nothing is submitted until the main session says `approved` or `auto` (the user's yes). Local post-fixes
    (`trim`, `conform`, `restore-audio`, a sync offset, a local regrade) and CapCut fixes need no permission in either case. `off`: this phase does not run at all (the
    production agent goes from X8 to X10; `awl-postprocess` hand-off): no check, no consult, no regeneration, and the user says what to fix after everything is delivered.
    Edit Mode has no automatic regeneration.
35. **Create: clean takes, the edit in CapCut** (item 35, `awl-plan-video`): QC checks every take clean and continuous, then the finished
    edit against the edit plan; a baked-in editorial element or a cut inside a take is a regenerate reason (by the QC-fix choice, item 27),
    never something CapCut covers.

## Never (this phase)

- Never call `T qc-consult` or `T qc-brief` outside X9 (the orchestrator's `T qc-brief` in the free plan, A6f, comes before production), never hand the keeper the video or the run's files
  (it holds the sample library only), never write to Loupe's samples from a run, and never treat a sample
  that "looks like" this video as a finding without the same place viewed in this video's own frames.
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
  nobody viewed on a frame (it is provisional, your own word: the tool prints numbers, CE-028); never accept a product over a quarter larger or
  smaller than reckoned, one that
  changes size across a cut, or one larger than the hand that holds it (`anomaly-catalog.md` §2.7).
- Never plan a product that is handled on screen without its affordance sheet in the registry
  (§1), and never run X9 without the plan's QC checkpoints rendered dense (`T qc --dense`).
- Never deliver a video that carries the original audio without its sync check (X8 step 5), and
  never leave drift or a moved action unreported. Never fix sync by stretching or looping the
  original audio.
- Never accept a Create take with a cut, a transition or an editorial element inside it as fixable by covering it in CapCut (item 35).

## Hand-off

- Edit Mode: the findings become the QC notes of the review. Return to the review (X9-R) in `awl-edit` (re-invoke it if its text is no longer in context); there is no automatic regeneration.
- Analyze Mode, an own voiceover (item 31), the picture passed and X8 step 5b has not run yet: `awl-postprocess` step 5b, then the voice checks here, then step 6 as below.
- Analyze Mode, the picture passed but the CapCut project is not built yet: go back to `awl-postprocess` step 6, then return here for the project checks.
- Analyze Mode, accepted (picture and project): invoke Skill `awl-record` (X10).
- Analyze Mode, one diagnosed regeneration: `awl-write-request` (the rewritten request; the diagnosis is already written in the brief as an attempt block) → `awl-inputs` only for new inputs → `awl-submit` (X5 again, X7, next attempt number) → `awl-postprocess` → `awl-qc`.
