# Generation system — one interconnected plan per video

Load this file before planning the first video, and keep it open until the last one ships. It turns
analysis, assets, model knowledge and Higgsfield capabilities into one coherent request per video.
Nothing important is decided in isolation. Every item below must describe **the same intended
video**.

Its companion `anomaly-catalog.md` holds the logical and physical anomaly classes (counts, openings
and use, preparation, persistent states, object permanence, liquids, scale, body mechanics, labels,
hand-offs, environment, timing, stylised rendering), each with its ledger entry, prompt lines and QC
checkpoint. Load it with this file; §3, §5d, §8 and §9 below point into it.

## 1. The dependency chain

```
source analysis ──► content strategy ──► style + subject (selected direction) ──► concept
      │                                                                               │
      │                          client assets needed ◄──────────────────────────────┘
      │                                  │
      │        asset geometry, identity, materials constrain ──► placement, interaction, staging
      │                                  │
      │        environment constrains ──► perspective, lighting, reflections, shadows, motion
      │
      └──► reference mechanics ──► pacing, hook, camera behaviour, engagement structure
                                                   │
official model docs + official examples ──► how the intentions are expressed (prompt structure, syntax)
Higgsfield capabilities ──► how references, parameters and operations are actually passed
final QC ──► every decision checked against every other decision
```

When a decision changes upstream (e.g. a different asset), re-run every downstream step that depends
on it. Do not patch the prompt alone.

## 2. Work backward from the finished video

Write this plan to `<run>/40-briefs/video-NN-plan.md` **before** any prompt. Keep it compact
(tables and short lines). Label provenance on each line where it matters:

- **[E]** direct evidence from source material
- **[I]** analytical inference
- **[U]** user instruction
- **[A]** approved client asset
- **[M]** model engineering knowledge
- **[G]** generation instruction

### 2.1 Intent (answer first)
- **Communicates:** what the viewer must understand or feel by the last frame.
- **Why keep watching:** the curiosity / payoff contract set up in the first second.
- **Mechanism kept from the references [E/I]:** hook type, reveal logic, rhythm, interaction pattern
  and payoff timing, from the selected content family.
- **Subject of its own (Create) [I]:** the premise, setting, characters, action sequence, turn,
  lines, first frame, ending image and product beat are the concept's, none of them a reference's;
  the plan names the family's craft it carries and states that the copy test passed
  (`creative-direction.md` §5.0).
- **Goal and job [I/U]:** the run's goal (`creative-direction.md` §2) and what this video makes the
  viewer do at the end, and what they keep of the product.
- **Audience and the one sharp idea [I]:** who it is for, the situation they have lived, the one
  idea in one sentence, the emotion arc or laugh mechanism, and the share line
  (`creative-direction.md` §3, §6).
- **Adapted:** which identity-specific elements become the client's [A/U]; what is dropped (source
  branding, usernames, watermarks, source wording).

### 2.2 Time budget (every second has a job)

| t (s) | beat | purpose (hook / context / demonstrate / build / payoff / rhythm) | action | camera | audio | text (mode-dependent) |
|---|---|---|---|---|---|---|

Rules:
- Rows must tile the whole duration with no unexplained gaps.
- **Stillness** is allowed only when the content family uses it deliberately (a held reaction, a
  reveal pause). Mark those rows "intentional hold".
- The **duration** comes from the content family's typical length and the concept, and must be one
  the selected model supports. Too long for one generation → plan clips per §3b, with explicit
  hand-off states (§3), assembled with `atp.py concat`. Hard cuts only where the family's editing
  style cuts.
- **Hook density, information density and payoff timing** follow the family profile from the
  analysis, not generic AI editing habits.
- **Reference inserts** (memes, §3c) are not in the generated time budget. Their split points are
  marked as beat boundaries.
- **Overlay text** is never generated: the plate stays clean, and the text is placed as CapCut text
  layers (`capcut-assembly.md`, `text-and-format.md`).

### 2.3 Roles and assets

| entity | role in the video | source-of-truth asset [A] | must stay fixed | may adapt | replaced from source entity |
|---|---|---|---|---|---|

- The canonical template or source-of-truth reference is authoritative for identity and geometry.
- Variants may change appearance (colour, label, flavour, skin) but never the fundamental geometry,
  unless the user says so.

### 2.4 Scene
- **Environment:** layout, surfaces, depth planes, what is in the foreground and background.
- **Lighting:** key-light direction, quality (hard/soft), colour temperature, exposure level, practical
  lights, environmental colour spill.
- **Camera:** shot size, angle, lens feel, height, movement per beat. Every move needs a reason (§5).
- **Audio:** dialogue (who, exact words), ambience, action sounds, music (or none), native vs. post.
  **Create:** the generation carries dialogue, action sounds and ambience only, with no generated
  music. The soundtrack and sound effects come from the sound plan and are placed in CapCut
  (`capcut-assembly.md` §3b).
- **Text:** per `text-and-format.md`. Edit Mode removes source text; Analyze Mode may add planned text,
  by default in post.

## 3. Entity state ledger (one continuous evolving state)

Track every important character, product, object, container, liquid, interface, garment and prop from
the first frame to the last. Earlier states constrain later ones.

| entity | count | t=0 state (spot · opening/lid · level · holder + hand · mark · in frame?) | event (visible cause · hand · contact point) | new state | … | final state |
|---|---|---|---|---|---|---|
| e.g. bottle | 1 | on counter, right of glass, cap on, full, label to camera | 1.2 s right hand lifts it | in right hand, cap on | 2.0 s left hand unscrews the cap and sets it on the counter; 2.5–4.0 s lips on the bottle's mouth, head tilted back: ⅓ drunk | back on counter, cap off beside it, ⅔ full |
| e.g. can (placed, §4b) | 1 | on desk, right of laptop, open (tab up), label ~30° to camera | 6.0 s left hand lifts it; lips on the opening beside the tab, one sip, head tilted back a little | in left hand | 7.5 s set down on the same spot | on desk, right of laptop, open |
| e.g. capsules | 3 | on the desk, right of the lamp, in a row | 4.0–7.5 s he walks past behind the desk and out of frame: untouched | 3 on the desk | 7.5 s right hand takes two, into the mouth, swallows | 1 on the desk, 2 swallowed |
| e.g. car (placed, §4b) | 1 | parked at the curb behind the bench, lights off, wheels straight, badge ~30° to camera | 8.5 s owner walks to it, opens the driver's door, gets in | engine on, lights on | 9.5 s pulls away slowly, wheels turning | leaving frame left |

Invariants to check against the ledger:
- **Placement persists:** an object stays where it was put until a visible action moves it.
- **One holder, one hand:** an object held in the right hand stays in the right hand unless a
  visible hand-off happens.
- **Irreversible states persist:** opened stays open, poured stays poured, broken stays broken,
  consumed stays consumed.
- **Liquids are conserved:** the amount leaving a container equals the amount arriving; nothing
  appears from nowhere.
- **Camera changes preserve layout:** a cut or angle change keeps left/right, near/far and on/under
  relations (respect the 180° line unless the reference deliberately breaks it).
- **Screens and interfaces:** a UI state changes only through a visible interaction and never
  re-randomises.
- **Wardrobe, hair, makeup and accessories** are constant unless a visible change happens.
- **Multi-clip videos:** each clip's end state is the next clip's start state, word for word.
- **Counts persist:** every multiple is counted at t=0 and changes only through a visible cause, by
  the amount it explains; what was taken exists somewhere (`anomaly-catalog.md` §2.1).
- **Use goes through the opening:** an object is used through the part built for it (the spout, the
  opened top, the nozzle, the torn notch, the handle, the screen), after the step that readies it,
  with the contact point named; nothing reacts before its cause (§2.2, §2.3, §2.8).
- **Object permanence:** what leaves the frame, passes behind a hand or sits across a cut comes
  back with the same count, spot, state and size (§2.5).
- **Parts and marks belong to the body:** a cap, strap, straw or label moves with the object, never
  on its own, never mirrored, never duplicated; the variant stays the same (§2.9).
- **Rendered, not pasted:** the product shares the neighbours' light, exposure, focus, grain,
  camera angle, scale and shadow direction, and stands inside its surface among the things around
  it (`anomaly-catalog.md` §2.15, the eleven-sign paste test).
- **Solids exclude each other:** nothing passes through the product or any other solid thing;
  nothing sinks into a surface or a hand; opaque bodies hide what is behind them in depth order; a
  moving thing that meets a solid stops, deflects, bounces or lands, and what it hits reacts
  (§2.14).

## 3b. Videos longer than one generation

A video longer than the locked model's maximum per generation (`models/index.json →
continuation.max_s`) is made of clips. **Analyze Mode:** a video over 30 s needs the user's
permission before any of its clips is generated (command A7b). Only the generated content counts:
reference inserts such as memes are cut from the reference (§3c), never generated.

**Fill one generation first.** Seedance 2.5 is built for "coherent videos up to 30 seconds long…
without multi-segment stitching" [OFFICIAL]. Every provider's guidance agrees: split at cuts and
scene turns, and continue only a single continuous take. Higgsfield's own advice is: "To build a
longer sequence, use the last frame of one clip as the starting image for the next, then join them
in an editor" [HF].

### 3b.1 Plan the clips (in the video plan, before any request)
1. **Put seams on the reference's own cuts first.** Where the content family cuts anyway, a clip
   boundary on that cut is invisible:
   - each clip holds whole shots, and the join is the planned hard cut (`concat --seams cut`);
   - across a cut only the world must carry over, not the pixels: identities, wardrobe, layout,
     light, props, the placed product's anchor and state (§4b), and the ambience.
2. **Use a continuous seam only where no usable cut exists** (one take longer than the maximum).
   Put it on a calm moment: low motion and no speech, such as between sentences or on a held beat.
   Never mid-action, mid-word, on the hook or on the payoff.
3. **Use as few clips as the length allows**, each within the model's range. Every seam is a risk.
4. **Write a hand-off state for every seam**, as a ledger row (§3) at the seam time:
   - positions and poses, and who holds what in which hand;
   - object and liquid states, and the placed product's anchor;
   - camera position and framing, and the light;
   - the audio state (who speaks next, the ambience).
   The next clip's prompt restates it word for word.
5. **Speech never crosses a seam.** Each clip's lines are complete sentences.
6. **Keep everything else identical:** the same references in the same order, the same parameters
   (resolution, audio flag, mode), and the same wording for identities, wardrobe, setting, light and
   style in every clip.

### 3b.2 Join methods, by the locked model's capability (`continuation` in the index)
| seam | method (`continuous` value) | models on Higgsfield | how |
|---|---|---|---|
| cut | Independent clips | all | Each clip comes from the same references. Start-frame models get each clip's start frame built from the same assets and setting |
| continuous | Native extension (`extension`) | `seedance_2_5`, `ad_multiplier` | See **Native extension** below |
| continuous | Video continuation (`video_continuation`) | `flux_3_video` | `video_references` = the accepted clip; the prompt opens "Continue this video from its final frames: <what they show>", then the next action; "do not recap completed action" [OFFICIAL BFL]. `duration` = the new segment, ≤ 15 s. One media field only, so no other references in that call. Unverified whether Higgsfield maps the role to continuation: check that the first result opens on the clip's last frame |
| continuous | Keyframe ladder (`keyframe_ladder`) | models with `start_image` + `end_image` | `start_image` = the hand-off frame. `end_image` = an approved keyframe of the planned end state, built and checked like a start frame. Pinning both ends stops drift building up across hops |
| continuous | Last-frame chain (`last_frame`) | every model with a `start_image` role | `atp.py last-frame` on the accepted previous clip → upload the PNG → `start_image` of the next clip. Its prompt opens with the guide's continuation wording ("continue forward from this moment; do not replay what happened before it") and the hand-off state |
| continuous | none (`cut_only`) | models without `start_image` (`wan2_6`, `gemini_omni`, `marketing_studio_video`) | Seams go on cuts only. With no cut in the reference, the boundary becomes a motivated cut the family uses (e.g. a punch-in), stated in the brief |
| either | Driver segments (`segments`) | Genjutsu (`hf_mult_motion_control`, `hf_mult_replace_object`), edit ids | Split the driving or source video at its own cuts into 4–30 s segments (no remainder under 4 s). Every segment gets identical image references and wording. QC segment 1 before running the rest |

**Native extension (Seedance 2.5)** [OFFICIAL BytePlus; HF catalog]:
- **Request:** `mode:"video_extension"`, `extension_mode:"forward"`.
  - `video_references` = the accepted clip A, passed **by job id**: that keeps A's audio and avoids
    a re-upload.
  - `duration` = the new part (4–30 s); the prompt is the guide's extension template.
- **Input limit:** the extended video must be 2–30 s. For a 45 s take:
  1. generate A at 25–30 s;
  2. extend A forward by 15–20 s;
  3. join locally.
  A further hop extends the newest segment, never the stitched master.
- **Output:** ByteDance's example returns **only the new part**, and its first frame repeats A's
  last frame, which the `continuous` seam drops. Measure the first result: if it holds A plus the
  new part, keep only the part after A.
- **Watch the join:** the volume may differ slightly from A's, so match the level. Colour can also
  step slightly, because Higgsfield has no MOV output.
- **Hops:** at most 2 extension hops per take. "Multiple continuations will compound the
  degradation", with mottled faces [OFFICIAL, Seedance 2.0 guide].

### 3b.3 Seam discipline
- **QC each clip before the next one exists.** Chain only from an accepted clip.
  - A clip that fails QC is regenerated (once, autonomously) before its successor.
  - Regenerating an earlier clip invalidates every clip chained from it.
- **The hand-off frame is the accepted clip's real last good frame:**
  `atp.py last-frame --video <clip> --out <…/cK/handoff.png>`.
  - If the final frames freeze, fade or morph, add `--back <s>` and trim the clip with the reported
    `trim_end_s`, so it ends on that frame.
  - View the PNG before uploading it. Identity, product geometry, label and the anchor must be
    right: errors in it propagate to every later clip.
- **Join:** `atp.py concat --clips c1 c2 … --seams <cut|continuous,…>`. A continuous seam drops the
  next clip's first frame (it repeats the hand-off frame) and smooths the audio. If a continuous
  join still jumps, apply these in order:
  1. Trim per ByteDance: "trim 6 frames from the end of the previous video segment… trim 1 frame
     from the beginning of the following video segment" [OFFICIAL].
  2. Use Higgsfield's bridge fix: generate the transition between the two boundary frames with a
     first-and-last-frame call [HF].
  3. As the last resort, move the seam onto a planned cut.
- **Drift budget:** each hop re-renders the world, so colour, exposure, sharpness and identity can
  drift, and the errors compound.
  - Prefer cut seams.
  - Keep continuous chains to at most 3 hops (2 for native extension). After that, re-anchor on
    the original approved assets with a keyframe.
  - Re-assert identity in every clip from the original references, never from the previous clip
    alone.
- **Audio:**
  - Dialogue is generated per clip, in complete sentences, with the same voice. Where the model
    takes `audio_references`, a clean cut of the voice from clip 1 keeps the timbre.
  - Keep the same ambience description in every clip.
  - No generated music across seams: it would restart at every seam. Write "No BGM; generate only
    environmental sounds and action sounds" [OFFICIAL Seedance]. Native extension is the exception,
    because it continues the audio.
  - Match loudness across joins. Fade a clip tail that ends with a click or cut-off noise.
- **Final QC on the joined video:** densify ±1 s around every seam
  (`atp.py frames --range a-b --fps 15 --sheet`). Check the continuity of positions, the product's
  anchor, light and colour, and the audio.

### 3b.4 Files and ledger
- One request per clip: `50-requests/video-NN-cK-request.json`, with regenerations as
  `-cK-aJ`. The ledger uses `--video NN-cK`.
- Outputs:
  - each clip: `60-outputs/video-NN/cK/aJ/raw.mp4`;
  - its hand-off frame: `60-outputs/video-NN/cK/handoff.png`;
  - the joined video: `60-outputs/video-NN/joined.mp4`.
- A clip the run generated may go back to Higgsfield **with its generated audio** (extension
  input). The silent-upload rule protects the user's source and reference videos.

## 3c. Reference inserts (memes): cut from the reference, never generated

An **insert** is footage that interrupts the reference's own scene: a meme clip, a film or TV
snippet, a reaction image, usually with its own sound (analysis card → "Inserts"). Example: a 27 s
reference has 13 s of its own footage, a 2 s meme with a meme sound, then 12 s more footage.

1. **Generate only the reference's own content.** In the example that is one 25 s generation; the
   time budget (§2.2) covers those 25 s.
2. **Split points.** Each insert k gets a split point in the generated timeline:
   `split_k = t_in_k − (sum of the earlier inserts' durations)`. In the example, 13.0 s.
   - Plan a natural beat boundary there. The line or action before the insert ends on it (the
     setup), and the content after it resumes as the reference does after the insert.
   - A sentence never runs across a split point.
3. **Measure the real split on the output.** After generation, put each split on the generated
   clip's actual boundary within ±0.5 s of the plan: the pause after the line, or a planned cut.
   Measure it with the transcript and cuts from `atp.py prep-video`, or a dense frame sheet.
4. **Cut each insert from the original reference video, with its sound:**
   `atp.py trim --video "<reference original>" --start <t_in> --end <t_out> --out <run>/30-assets/inserts/<V>-iK.mp4`,
   with `t_in` / `t_out` on the cut frames from `cuts.json`. Then `atp.py conform` to 720×1280.
   - **A video meme is always cut, never screenshotted.**
   - A still image held for the insert's duration is cut the same way, which keeps its sound. Or
     take a lossless screenshot (`atp.py last-frame` on the cut) and place it with the insert's
     sound under it.
   - Overlays the reference added on top of the insert (its caption, username or watermark) are
     removed with `atp.py clean`. The meme's own built-in text stays. If removal isn't clean, say
     so in the brief.
5. **The 30 s permission counts only the generated content.** In the example, 25 s means one
   generation, so no question.
6. **Assembly happens in CapCut** (`capcut-assembly.md`): the generated video split at each point,
   with each insert in its gap.
7. **The product stays put across inserts.** The placed product keeps its anchor on both sides of
   an insert (§4b); inserts never show it.

## 4. Replacement and insertion integration analysis

For every product placement, product swap, character swap, object insertion, interface replacement or
other entity substitution, fill this block (only the rows that matter for the shot, but consider all
of them):

| factor | source entity (what it was) [E] | client entity (what it is) [A] | resolved staging [G] |
|---|---|---|---|
| real size and scale | | | |
| proportions, silhouette, curves, geometry | | | **never inherited from the source entity** |
| orientation, perspective, depth, camera distance and angle | | | |
| location in frame; relation to character and surrounding objects | | | |
| supporting surface; contact points | | | |
| hand placement, grip, finger wrap, occlusion | | | adapt the grip to the client's real geometry |
| motion path, apparent weight, gravity, inertia | | | |
| materials (gloss, matte, transparent, metal, fabric) | | | |
| reflections, highlights, shadows (softness, direction) | | | |
| light direction, intensity, colour temperature, exposure, colour spill | | | inherit the scene's light |
| why it is here; how it arrived; where it was before; where it goes next | | | |
| what the character does with it; its state at each ledger checkpoint | | | |

Resolution rules:
- **Geometry follows the client's real asset.** If the source's grip, placement or container does
  not fit it (a different size, shape or opening), change the staging (grip, surface, framing,
  camera distance), never the asset.
- **Lighting is continuous.** The asset takes the scene's key direction, colour temperature and
  shadow softness in every shot and follows the light as the subject or camera moves. Reflective
  materials reflect the actual environment.
- **Context is logical.** The entity's presence, entrance and use must make sense in that
  environment. If the analogy is weak (e.g. the client's service replacing a physical prop), choose
  the most natural analogous staging (a screen, a document, a gesture) instead of forcing a literal
  swap.
- **One frame is never optimised at the expense of the timeline.** Check the whole ledger.

For a natural placement (§4b), the "source entity" column holds the **anchor** instead: the hand
or surface it sits on [E], the light on that spot [E], and what surrounds it [E].

## 4b. Natural placement and contents — when nothing in the reference is the same kind of item

**When it applies (Analyze Mode):**
- The client has a placeable entity: a physical product of any size (a drink, a pack of gum, a
  cosmetic, a phone, a car, a piece of furniture), or software shown on a device screen in the
  scene.
- The reference the new video follows contains **no** entity of the same form. For example:
  - a drink client, and a reference with no drink in it, or with the drink in a cup;
  - a gum client, and a reference where nobody eats anything;
  - a car client, and a reference filmed indoors with no vehicle.

In that case the client entity is **not** dropped, and it is **not** forced into a swap with an
unrelated object: a phone never becomes a can, and a bicycle never becomes a car. The new video
keeps the reference's story and mechanism unchanged. The client entity becomes part of the scene as
if it had always been there, through the most suitable form (§4b.0).

The analysis card records which integration form a reference allows (`analysis-protocol.md` §3),
and the plan decides the anchor. A client with no placeable entity (a personality, a pure service)
keeps the analogous-staging rule of §4.

### 4b.0 Choose the integration form: the most suitable use and blend
Ask how this product would naturally be part of *this* scene, given what it is, its size and how it
is really used. Pick the first form the action allows:

| form | when | what happens |
|---|---|---|
| **Swap** (§4) | The reference shows the product's analog in the **same form**: another can for a canned drink, another gum pack for a gum, another car for a car, another app on a phone | The client's product takes its place, with the same action and timing, at its own real size |
| **Contents** | The video shows the product's **category in another form or vessel**, whatever its role in the story: a glass on the subject's café table, a drink in a cup, food in a bowl, a cream on a finger, gum pieces in a hand. It may come from the reference, from the plan, or from a prop in a supplied photo | The vessel and the action stay. What is inside **becomes the product**, matched to the supplied contents sample of the chosen variant (colour, clarity, bubbles, texture, shape). The product's **package is placed nearby, opened,** as the visible source (§4b.1–§4b.4) |
| **Placement** | Nothing analogous | §4b.1, chosen by the product's size and use |

- **Contents is the default for the subject's own consumable.** When the subject has a drink, snack
  or other consumable of the product's category in hand or in front of them, it holds the product,
  even when nothing in the story is about it. Contents and placement then go together: the vessel
  holds the product, and its opened package stands beside it as the source.
  - Example: a man at a café table holds a glass. The client sells an orange sparkling drink, so the
    glass holds that drink (bright orange, sparkling, from the flavour's sample), and the open can
    stands beside it. A glass of water next to the can reads as wrong.
  - **When not to:** the switch must keep the scene logical. Keep the vessel's own contents when
    the joke or story depends on that exact thing ("when you order water at a bar"), when its
    serving contradicts the product (a steaming coffee for a cold drink, a baby bottle, medicine),
    or when it belongs to a background stranger. A branded competitor product is a §9b leftover
    anyway.
  - **Details follow the variant:** ice may stay; a garnish that clashes with the flavour becomes
    the variant's fruit or goes (a lemon slice in an orange drink becomes an orange slice).
  - **The drink comes from the package:** the package is open, and the amounts add up (a full glass
    from one can leaves the can nearly empty). The sip comes from the glass, or from the can only
    when enough is plausibly left.
- **Contents examples:**
  - A "first day as an assassin" clip pours a powder into a cup of drink, stirs it with a finger,
    forgets, drinks it and dies. The cup now holds the client's drink, in its flavour sample's
    colour and texture. The open can stands beside the cup the whole time. The gag plays out
    unchanged.
  - Someone pops a piece of gum mid-story. The piece comes from the client's open pack on the
    table.
- **Contents ledger rules:**
  - Amounts stay consistent with the package: a cup's level fits what one can holds, and a pack
    of ten has nine left once a piece is taken.
  - Amounts change only through a visible action: drinking, eating, applying.
  - The package stays open and in place unless something moves it.
- **Contents sample needed:** this form needs a contents sample of the chosen variant
  (`assets-and-substitution.md` §1). Samples are often among the supplied files without a label: a
  pour, a glass of the drink, a lifestyle shot. Without one, pick a variant that has a sample. With
  none at all, a vessel that plays no part in the action is left out, and one that does keeps its
  own contents beside the placed package; say so in the brief.
- **Use only when the action invites it.** The product is used the way it is really used only when
  the reference's action has room for it: a drink held or sipped, gum unwrapped and chewed, a cream
  applied, a phone used, a car driven, parked or leaned on. Otherwise it is simply present. The
  story never changes to make room for the product.

### 4b.1 Choose the anchor by the product's size and use (first logical option wins)
**Handheld products** (a can, a gum pack, a cosmetic, a phone):
1. **In the character's hand**, when a hand is free or moving casually (talking, gesturing,
   walking, sitting relaxed) and holding the item is natural to the activity.
   - Example: a man crossing a street does a one-second "respectful jog" to thank the driver. He
     holds the drink, or the gum pack, the whole way, through the jog and back to walking.
   - Use **one hand, the same hand throughout**. The other hand makes the gestures the reference
     needs.
   - An item in a gesturing hand moves less and is held the way it naturally would be: an open
     drink stays upright, an open pack does not spill its pieces.
   - Not when both hands are needed by the action (typing, cooking, playing, carrying, heavy
     two-handed gesturing), when the hands are mostly out of frame, or when holding it would look
     staged.
2. **On a surface the character plausibly owns, within reach**: a desk, table, counter, nightstand,
   shelf beside them, the arm of a sofa, a car's cup holder or dashboard. It sits in the subject's
   depth plane or slightly behind it, inside the main framing.
3. **Elsewhere in the environment, where such an item naturally lives** (a shelf, a gym bench, an
   open bag, a fridge door), still inside the main framing.

**Large products** (a car, a motorbike, furniture, an appliance):
- They stand where such things really are: a car parked at the curb, in the driveway, or passing
  behind the action; a chair or a fridge in the room.
- They are used only when the action invites it: getting in, leaning on it, driving off.
- They obey their own physics (§5b).

**Software:** a phone, laptop or monitor in the scene, showing the client's **real** interface and
used the way the action allows.

If none of these is logical, add the smallest element native to the setting (a side table at the
frame edge, a car parked across the street) and say so in the brief. If even that would look forced,
write "placement weak: …" in the brief and use the least forced option. Never place it floating, out
of context, or somewhere it could not really be.

### 4b.1b Posture, support and place (every anchor)
Caught errors CE-006, CE-007, CE-012 and CE-013 (2026-10): a flat sachet standing on its edge against a
writer's forearm, a carton that "leaned" on a prop the model never drew, a pack resting on an exam sheet
whose corner warped, a pouch that took over the source's bottle pick-up. The anchor row of the ledger
therefore carries four more facts, and the prompt and QC quote them (`anomaly-catalog.md` §2.16):
- **Posture its shape allows:** a flat sachet or pouch lies flat, label up; a carton lies flat or stands on
  its base; a can stands on its base. Never on its edge against a person or an object.
- **A support that is in the frame:** bare surface, or a large solid object the source frame already shows.
  Never a lean against a prop the model has to invent, and never on or overlapping paper, cloth or any thin
  sheet that hands move or write on.
- **A place where a person would leave it:** out of the way of a working hand or arm, at the table's near or
  far edge, never touching the person. The ledger row gives the story reason in one clause ("set down at the
  near edge, out of the writing hand's way").
- **Never the source's beat:** a placed product does not take over a pick-up, use or hand-off that belongs
  to another object; the prompt names the object that is picked up and says the product stays.
- **The anchor class the locked model renders at size.** When the model guide lists size as a model limit
  (`wan3_0_prime`: `wan-3-0.md` §5), the anchor comes from its passing list: in the hand that holds it or
  swapped for the source's own handheld object; on a bare surface beside a large rigid object of the source
  in the same plane; one sachet lying flat on bare near-side surface. Sizing words do not carry the plan.

### 4b.2 Prominence: noticed, not featured
- **Scale:** real scale at its depth, from the plan's **size reckoning** (`anomaly-catalog.md`
  §2.7: real dimensions, distance, lens, the expected fraction of the frame, the ratio to a named
  neighbour, the size ladder across products, constancy). Never enlarged so it gets seen: a
  background product is a small object, and the prompt says so. On a model whose guide lists size as a
  model limit (`wan3_0_prime`, `wan-3-0.md` §5) the reckoning is the check and the anchor class (§4b.1b)
  is the control.
- **Position:** off-centre (a side third), in the mid-ground near the subject. A large product sits
  in the mid-ground or background where it naturally stands. It never blocks the subject or the
  action, and never takes the foreground closest to the lens unless the reference's scene puts such
  an object there.
- **Visible most of the runtime:** in frame in every shot where its anchor is in frame. Choose the
  anchor so that this is most of the video.
- **Brand mark** (label, logo, badge or screen): turned roughly toward the camera (about 15–40°
  off-axis), recognisable at a glance but not squared to the lens like a packshot. Brief, natural
  occlusion is fine; permanent occlusion is not.
- **Same image as everything around it:** same focus, exposure, grain and motion blur.
- **No hero treatment:**
  - no light, glow or rim light of its own;
  - no push-in, cutaway or insert shot of it;
  - nobody looks at it or presents it to the camera;
  - no mention in dialogue or captions, unless the user asks for it.
- **The story is untouched.** The hook, beats, dialogue, timing and payoff are the reference
  mechanism's own. The placement adds nothing to them and takes nothing away.

### 4b.3 One anchor, persistent (ledger-tracked)
- **One location at any time,** recorded in the ledger at t=0 with relational words: "on the desk,
  right of the laptop", "parked at the curb behind the bench".
- **It stays there through everything:** every cut, angle change, reframe and camera move. Its
  relation to the neighbouring objects is identical in every shot where that area is visible. It
  never jumps from desk to table to chair, and a parked car never moves along the street.
- **It moves only through a visible, motivated action:** picked up to use it (drink, unwrap,
  apply, read), moved out of the way, handed to someone, taken along when leaving. A vehicle is
  driven or pushed; it never slides.
  - A handheld item is picked up from its anchor, by the nearest hand. While held, it stays in that
    hand. The set-down is visible, and the new spot (usually the same one) becomes the anchor.
- **Few interactions, timed to the rhythm:** at most one or two, at natural pauses (after a
  punchline, while listening, between sentences). Never on the hook or the key beat.
- **States stay coherent:**
  - if it is ever used, it is ready for that use from the start or made ready on screen: a can
    that is drunk from is open from the start or opened on screen, and a car that drives off has
    its driver get in first;
  - it is used through its own opening or control, with the contact point of its affordance sheet
    (`anomaly-catalog.md` §1, §2.2): a straw bottle through its spout with the cap flipped open, a
    can from the opening beside its lifted tab, a pack from its opened end;
  - a state that changes, stays changed:
    - an opened can stays open;
    - a pack missing a piece stays missing it;
    - a car's lights, engine, doors and windows keep their state until a visible action changes
      it;
  - a held item stays held from frame one until a visible set-down.
- **Exactly one instance.** No duplicates, and no change in size, label, colour, variant or state
  without a cause.

### 4b.4 Ambient integration: it must not read as an edit
- **Lighting:** the scene's key direction, softness, colour temperature and exposure.
  - Specular highlights appear where the key light would put them.
  - Metal, glass, paint and screens reflect the actual surroundings; a car's body and windows
    mirror the street.
  - Nearby surfaces and screens spill their colour onto it.
- **Contact:**
  - a contact shadow, consistent with the other objects' shadows (under a car, the dark contact
    patches of its tyres);
  - it sits on its surface, never floating or intersecting it, and never sinking into it;
  - its perspective is correct for the camera height and lens;
  - things in front of it occlude it;
  - in hand: a grip that fits the canonical geometry (§4), with fingers wrapping it and none
    passing through it.
- **Plate match:** the same depth of field (soft if its plane is soft), noise or grain, motion blur,
  colour grade and white balance as the scene.
- **Lived-in pose:**
  - slightly angled, not perfectly centred or aligned;
  - it may sit among everyday items without being crowded out;
  - its state fits the scene (opened beside a laptop mid-work, a car parked with its wheels
    straight);
  - never a pristine product-shot pose.
- **No sticker or edit artifacts:** no flat look, no halo or cut-out edges, no sharpness or colour
  mismatch.
- **The paste test** (`anomaly-catalog.md` §2.15) names the eleven signs of an edit and their
  causes, and the prompt scopes the product reference to shape, colours and label only ("do not
  use its lighting, exposure, background or camera angle") while describing the room's light on
  the product, its size against a neighbour, its mark angle and its contact shadow like the
  neighbour's. Prefer an anchor that forces integration: touching or partly behind another object,
  inside the lamp's falloff, never alone on an empty edge.

### 4b.5 Expressing it to the model (with §7)
- Describe the item as **part of the scene from the first frame**, inside the environment
  description the official examples use: "<canonical description> <anchor>", e.g. "an open <drink>
  stands on the desk to the right of the laptop", "a <car> is parked at the curb behind the bench".
- Avoid edit verbs ("add", "insert", "place a product") and advertising words ("product shot",
  "hero", "showcase", "brand", "advertisement"). They pull models toward entrances and ad framing.
- Say that it persists ("stays on the desk throughout", "stays parked"). Write any interaction as a
  chronological event with the hand or the driver named. Add a duplicate exclusion in the model's
  syntax ("only one <product> in the scene").
- **Keep its brand mark.** The clean-plate line carves out the item's own printed label, logo or
  badge (`text-and-format.md` §1): never a bare "no logos", which blanks the product. Its words go
  into QC `--allowed-text`.
- **Start-frame models:** the 9:16 start frame already contains the item at its anchor, with a
  contact shadow and the scene's light. Check it against the canonical template before animating.
- **Reference models:** the product views are bound to their role. The prompt states the anchor and
  that the item keeps the scene's lighting.
- **When a reference video drives the motion** (Recreate only; Create never passes a reference),
  it shows no such item, and the model may treat the item as foreign:
  - say explicitly that the item is part of this scene although the reference has none;
  - keep the reference's actions;
  - for an in-hand anchor, name the hand that holds it while the other hand performs the
    referenced gestures.
- **Multi-clip videos (§3b):** the anchor and the item's state are part of every hand-off state,
  restated word for word in the next clip.
- **State what every vessel holds.** Bind the contents to the sample: "the glass on the table holds
  <product> poured from the open can beside it: a bright orange, sparkling drink with fine rising
  bubbles and ice, as in @ImageN". A glass, cup or bowl whose contents are not stated comes back as
  water, or as whatever the model guesses.
- **Asset photos bring their props.** A character or environment photo that shows a glass, a cup or
  a snack makes the model reproduce it. Plan each such prop as the product's contents when it is of
  the product's category, or limit that image's role in the prompt ("Image 4 is only the man's
  identity: face, hair, build and clothing; not its glass, table or background").

## 5. Logic, continuity and anti-slop gate

Evaluate before writing the prompt, and again in the pre-generation QC pass (§8):

| dimension | pass condition |
|---|---|
| physical | Plausible mass, gravity, contact, grip, liquids and material behaviour. No floating, unsupported or intersecting objects. No fingers through objects, no malformed hands |
| spatial | A stable layout, with consistent left/right, near/far and supporting surfaces |
| temporal | Cause precedes effect; every state change has a visible cause; no reversals |
| narrative | Every beat serves the intent (§2.1); the payoff pays off the hook |
| environmental | The background, props and weather stay consistent; no morphing |
| asset fidelity | Canonical geometry, identity, materials and label/interface fidelity (label text only when real and approved) |
| camera continuity | Moves are motivated; axis respected; framing keeps the important interaction readable |
| lighting continuity | Direction, colour and exposure are stable unless a visible cause changes them; reflections and shadows agree |
| motion continuity | Natural speed; no arbitrary slow motion, sudden speed-ups or jump-speed changes |
| interaction realism | Believable body mechanics, weight shifts and follow-through |
| composition | The subject and asset are readable in 9:16; key action kept out of platform UI zones |
| pacing | Matches the family profile; no dead space, filler or unexplained pauses; no repeated actions |
| transitions | Every cut, zoom, reframe, speed ramp or scene change has a reason (the action, the family's editing style, the narrative). None are added "for cinematic feel" |
| identity | No drift in face, hair, body or wardrobe; no duplicated people or objects |
| placement (§4b) | The placed client entity is present and recognisable, on one anchor that persists through every shot. It moves only by a visible action, matches the plate, and is noticed but not featured |
| counts | Every multiple keeps its number except through a visible cause; nothing appears, vanishes or doubles across exits, occlusions and cuts (`anomaly-catalog.md` §2.1, §2.5) |
| affordance | Every use goes through the object's real opening or control, after its preparation step, with a real contact point and the body mechanics of that use (§2.2, §2.3, §2.8) |
| solidity | Nothing passes through, sinks into or shows through a solid; occlusion follows depth; every contact has its consequence (§2.14) |
| sharpness | One clear idea, a hook in the first second, a real turn, a payoff on the family's beat, a share line, and the product native to the scene (`creative-direction.md` §6) |
| size | Every product's size in every shot is reckoned from its real dimensions, its distance, the lens and a named neighbour, written into the prompt and the start frame, and kept across motion and cuts (§2.7) |
| guardrails | Every hit of the client's rules is edited as planned (count at the limit, competitor marks removed, excluded faces swapped, captions rewritten, props removed) and nothing the rules ban is in the concept (`brand-guardrails.md`) |
| transfer (Create) | The video carries the references' craft (style, properties, approach, crafting) and none of their subject: the copy test passes against every reference of the family and the run's other videos (`creative-direction.md` §5.0) |

The AI-slop blacklist must never appear in a plan or a prompt:
- unexplained dead space, filler or pauses, and unnecessary static stretches;
- arbitrary slow motion, abrupt fast-forwarding and sudden speed changes;
- out-of-nowhere transitions, unjustified cuts and random scene changes;
- teleporting, disappearing or duplicated objects;
- a count that changes without a cause (three capsules that are one after a walk-past);
- a product used through a part that has no opening or through a closed one (a straw bottle drunk
  from the side without the spout, a sealed can sipped), or used before it was made ready;
- anything passing through the product or another solid (a tossed paper through a plastic bottle),
  sinking into a surface, showing through an opaque body, or hitting something without a
  consequence;
- a generic concept: a "person enjoys product" beat, an explained joke, a stock situation nobody
  lives in, a dated meme;
- a placed product that changes spot between shots, enters or leaves without a cause, or looks
  pasted in (its own light, a halo, mismatched sharpness, no contact shadow, a packshot pose);
- identity drift, clothing changes and asset deformation;
- inconsistent backgrounds, unexplained lighting changes and broken reflections;
- impossible physics, inconsistent scale and nonsensical motion;
- repeated actions and environmental morphing.

### 5b. Physical motion follows physics, above all when it has to land
Every moving thing obeys momentum, friction, gravity and contact. Write and check each motion with
the physics of the object that moves:
- **A spun object** (a can, a bottle, a phone on a table) slows down and wobbles, and its speed only
  ever drops.
- **A tossed or flipped object** (a gum pack, a coin, keys) rises, arcs, tumbles at a steady rate,
  falls and lands on whichever face its spin brings down. It bounces or settles, and is never
  frozen in mid-air.
- **A vehicle** (a car, a bike) accelerates and brakes gradually.
  - Its body pitches under braking and rolls in a turn.
  - Its wheels turn at the speed it travels and steer along the path it takes.
  - It never slides sideways without a cause, and it stops with its wheels still.
  - Its doors swing on their hinges.
- **Liquids, powders and pieces** fall in an arc, fill, spill and are conserved (§3).
- **People** shift their weight, follow through and react to what they touch.

When a motion can't physically reach a required state in time, models fake it:
- the object **snaps** to a new position or angle in a single frame;
- it **pauses on the pose and then resumes** with no new push;
- it **reverses**;
- its label, badge or body **morphs**.
This was seen on a spinning can that had to land its logo between two caption words. The same cheat
appears with a toss that must land face-up, or a car that must stop on an exact mark.

- **Describe the physics, never a schedule.** Give the cause (a flick, a toss, a push on the
  pedal), the direction, how it speeds up or slows down, roughly how far or how many turns, and the
  end state. Never list exact times at which a face, logo or badge must point at the camera, or a
  vehicle must reach a mark.
- **Give a required end state a visible cause:**
  - a hand stops the spinning item or turns it label-forward;
  - the character catches the toss;
  - the driver brakes and steers into the spot.
  A free motion that "happens" to end exactly where the plan needs it invites a cheat.
- **Recreate:** when the reference's payoff depends on its own object's geometry (where its label
  sat, its size, its wheelbase), remember the client's product is different. Keep the reference's
  beat; only the product-specific landing may differ (which face shows, where the label ends up).
  The original audio comes back in a Recreate, so the moment the motion starts and lands stays
  the source's (§5c).
- **Text that plays on the product** (a pun on its logo, a reveal caption) follows the product. It
  is timed and placed in CapCut on the moment the product really shows it in the clean video,
  measured at the full frame rate, never on the plan's timestamp.
- **A corrected regeneration removes timing constraints from free motion. It never adds them.**
  The §5c fidelity lock is not such a constraint: it comes from the source video, not from
  timestamps in the prompt.

### 5c. Source fidelity: the original's movements, actions, details and timing
In Edit Mode and in Analyze Mode Recreate, the output is the source with only the planned
operations changed. Everything else keeps the source's movements, actions and details exactly:
who moves, how and in what order, gestures, expressions, gaze, mouth movements, how props are
handled, the camera path and framing, the light and the background action. The final also carries
the source's own audio (`restore-audio`). That audio is fixed, so every action must happen at the
same moment and speed as in the source: words need their mouth movements, impacts their contact,
steps their footfalls, a can its opening, a door its slam. A late hand or an early sip reads as a
dubbing error, even when every frame looks right.

Fidelity is built into the **first** request. QC (§5c.5) confirms it; it is not where it is
achieved. Create is not affected: it makes new scenes, and its sound is built in CapCut on their
own beats.

#### 5c.1 The source action script (card, then plan)
Write the source as numbered beats, in order, from the storyboards, densified at 15–30 fps around
fast moments and contacts:
- the time range, for planning and QC only; it never goes into a prompt as a schedule;
- each person: body and weight, hands (which hand, what it holds, how), head and gaze, facial
  expression, mouth (the line they speak, or silent);
- each prop: who handles it, its path, grip and contacts, and where it ends;
- the camera: framing, angle, moves, shake, cuts;
- the environment: background people and action, light changes;
- the small details that make it this video: a hair touch, a nod, a pause before a line, the
  rhythm of quick and slow moves.

Mark each beat **keep** (unchanged) or **change** (an operation changes it). A change of identity
keeps the motion: a swapped person keeps the source person's movements, and a swapped product keeps
the original item's path, grip and contacts. Mark the **sync anchors**, the beats whose sound is in
the original audio:
- each spoken line and whose mouth says it (transcript);
- impacts and hits (`audio-profile` hits, densified frames);
- footsteps, pickups, set-downs, sips, opens and closes.

#### 5c.2 The most preserving input and parameters
Use the strongest preservation the locked model offers, in this order:
1. **The source video as the edit input** (✓, a pixel-preserving edit): the model changes only the
   targets and keeps the rest of the picture's motion and timing.
2. **The source video as the motion input** (↔, motion transfer).
3. **The source video as the video reference** (≈): the model regenerates the clip and follows the
   source's motion, camera and timing as far as its reference allows.
4. **The source's own frames** (✗, frames only): its first frame with the operations applied as
   the start frame, and its last frame with the same operations as the end frame when the model
   takes one. Say in the brief that fidelity and sync are at risk.

Take the guide's preserving mode and settings, for example Seedance 2.5's `video_edit` mode with the
duration rounded up from the source. Where the guide offers a choice, never take a creative or
loose setting. A parameter the guide marks as not exposed on Higgsfield is not a lever.

**Same duration.** Request the source segment's exact duration, or the nearest allowed duration
above it and trim the extra afterwards. A shorter or longer generation squeezes or stretches the
actions against the sound.

#### 5c.3 The fidelity lock in the prompt
Write it in the model's own structure and wording (its §4.0 examples and keep-lists). The edit kind
decides how much is described:
- **Always:**
  - the change, scoped with "only" ("Replace only the white mug in his right hand …");
  - the full keep-list in the guide's words: the performers, their motion, gestures, expressions
    and mouth movements, the props and how they are handled, the camera path and framing, the
    light, the background and the timing ("Keep the man, his motion, the camera path and the timing
    of @Video1 unchanged");
  - for a swapped item: it follows the original's exact position, path, tilt and grip in every
    frame;
  - for a swapped person: they keep the source person's movements, expressions and mouth movements
    on the same frames.
- **✓ and ↔, where the source carries the action:** no re-description of the scene. The guides warn
  that re-describing invites the model to regenerate instead of edit; the keep-list does the work.
- **≈ and ✗, where the model rebuilds the action:** also write the action script out in order as
  plain sentences: who does what, with which hand, how fast, where they look, where they pause
  ("she lifts the can with her right hand to chest height, glances down at it, looks up into the
  lens and speaks, then lowers it"). When the guide limits length, the sync-anchor beats and the
  most visible actions come first.
- **Exclusions:** no added, skipped, repeated or reordered action; no new gesture; no extra camera
  move; no re-staging; no new people or background action; no change of pace.
- **Not a schedule.** The timing comes from the source video, never from timestamps in the prompt.
  Free physical motion still follows §5b. What must match is when a motion starts and lands, and
  the source already shows it.

#### 5c.4 Check before spending (X4)
Walk the action script beat by beat against the request:
- every keep beat is carried by the source input or named in the prompt;
- nothing in the prompt invites new motion ("dynamic", "cinematic camera move", a gesture the
  source does not have);
- the duration matches the source segment;
- no change operation forces a motion change. A bigger or differently shaped product gets a
  planned grip that keeps the same hand path.
Fix the request before the preflight.

#### 5c.5 Measure it after the merge
`atp.py sync-check --source <source> --output <final>` compares the output's motion with the
source's at 30 fps. It reports the offset, any drift and the duration difference, and writes a
side-by-side sheet (source | output at the same timestamps) at the strongest moments. Also view the
sync anchors densified, and compare the keep beats on the sheet.
- **in_sync**, within ±0.1 s everywhere: accept.
- **constant_offset**, the same offset everywhere (e.g. a generated dead head): post-fix. Trim the
  picture's head when the output is late, or start the audio later (`restore-audio --start`) when
  it is early. Then merge and check again.
- **drift** (the output runs faster or slower) or **out_of_sync** (an action added, skipped or
  moved): no post-fix can repair it. It is a **regenerate** reason, and the corrected request names
  what went wrong (duration, speed, the action that moved) and tightens the fidelity lock.
- **inconclusive**, when the motion is too different to measure (e.g. a heavy restyle): judge it on
  the sheet and the densified anchors.

### 5d. Counts, openings and object permanence
Two anomalies from anime Create videos (2026-10) define this rule set: three capsules on a desk
became one after the character walked past them and came back, and a boy drank from the side of a
flip-top straw bottle that has no opening there, after his mother had filled it with milk. A ledger
that tracks only "where the product is" lets both through. `anomaly-catalog.md` is the full
catalog; what every plan, prompt and QC pass must do:
- **The affordance sheet first** (`anomaly-catalog.md` §1): parts, openings, the opening sequence,
  how the product is used and held, the contact point, what it holds and how many, its states, its
  real size, the orientation of its mark, and what it cannot do, written into the registry before
  the plan.
- **The ledger counts and names the part** (§3 above): a count per multiple, the opening or lid
  state, the level, the holder and hand, the contact point, and whether the anchor is in frame.
- **The prompt** writes every use beat as initial state → operation on the named part → observable
  result with the contact point, carries every count with its number, restates counts and states
  after each exit, occlusion, cut, hand-off and seam, and adds one targeted exclusion per product
  for its own wrong use (`anomaly-catalog.md` §3).
- **QC** renders the plan's checkpoints dense (`atp.py qc --dense`), counts at each, checks the part
  and the contact on every use beat, and compares count, spot, state and size across every exit,
  occlusion, cut and seam (`anomaly-catalog.md` §4). A count or state that changes without a cause,
  a use through the wrong or a closed part, and an effect before its cause are regenerate reasons.

## 6. Conflict resolution (resolve before sending)

| conflict | resolution |
|---|---|
| A camera move would hide the key interaction | Change the camera: a slower move, a different angle, or locked-off |
| The reference grip or placement does not fit the client asset | Adapt the interaction to the asset's real geometry |
| The replacement would produce wrong reflections or shadows | Restage it (angle, distance, surface) or specify the lighting explicitly |
| The sequence is too complex for the model's reliability | Simplify or split it into clips and keep the core mechanism. Fewer simultaneous movers, one camera move, real-time processes |
| The duration exceeds the model's range | Split per §3b (on the reference's cuts first, continuations only where the take is continuous). The model stays locked. Analyze Mode: a video over 30 s needs the user's permission first (command A7b) |
| Overlay text is needed | Always a clean plate plus CapCut text layers (Analyze Mode; `capcut-assembly.md`). Never model-rendered |
| The reference is wrong or weak for the need | Replace or improve the reference (new start frame, better asset view). Do not compensate with prompt text |
| A dedicated parameter exists (duration, aspect, audio, genre, mode, frames) | Use the parameter. Do not describe it only in prose |
| The house approach (the user's examples) differs from a default here | Follow the house approach (`20-analysis/house-approach.md`) and note it in the brief. It never overrides physics and logic, §9b, the permission rule or the house text style |

## 7. Translating the plan into the selected model's language

1. Open the selected model guide at **§4.0 (official examples and patterns)** and write a
   **pattern card** into `<run>/50-requests/video-NN-pattern.md`:
   - information order;
   - sentence style and length;
   - temporal notation (chronological sentences, stages, timecodes, shots);
   - subject motion vs. camera motion;
   - camera vocabulary;
   - reference syntax (`@Image1`, `<<<element>>>`, "image one");
   - frame-anchor wording;
   - audio and dialogue syntax;
   - how exclusions are phrased;
   - prompt length limits.
   These patterns are engineering principles to adapt, not text to copy.
2. **Decide the channel for each element of the plan:**
   - **parameters**: duration, aspect, resolution, audio, genre, mode, extension direction;
   - **references**: identity, product geometry, scene plate, motion or camera driver, first/last
     frame. By sub-mode:
     - **Create:** only client assets and generated frames, never a reference video, frame or clip;
     - **Recreate:** the reference's prepared own-content source is the edit master, and the
       client's assets replace and add;
   - **prompt**: action, chronology, relationships, light, camera behaviour, states, exclusions;
   - **post-production, local** (`atp.py`): conform to 720×1280, source-audio restoration, trims,
     multi-clip joins, cutting the reference inserts;
   - **post-production, CapCut** (Analyze Mode, `capcut-assembly.md`): every overlay text as a text
     layer, the inserts in their gaps, the final edit.
   Nothing is expressed twice in conflicting ways.
3. Write the prompt in the model's pattern:
   - chronological if the official examples are chronological;
   - concise if they are concise;
   - subject motion separated from camera motion if the examples separate them;
   - the documented syntax for references and frames.
   Include the ledger's state anchors (start state, key state changes, end state) and the
   integration facts from §4 in the model's own phrasing. Express a natural placement as §4b.5
   says. Write every use beat as initial state → operation on the named part → observable result
   with its contact point, carry every count with its number and restate it after exits,
   occlusions, cuts and hand-offs, and add one targeted exclusion per product for its own wrong use
   (`anomaly-catalog.md` §3). Do not dump the analysis into the prompt.
4. Check the prompt against the pattern card and the model guide's §7 checklist, then save it to
   `<run>/50-requests/video-NN-request.json`: model, params, medias with their role and meaning, the
   prompt, the post-processing plan, and the preflight cost.

## 8. Pre-generation QC pass (mental render, first frame → last frame)

Walk through the planned video in 0.5–1 s steps and confirm each of these, or fix it before sending:

- [ ] Subject identity and wardrobe are stable; the approved character is used and the source
      person is excluded.
- [ ] Client asset fidelity: canonical geometry, materials, labels and interface; correct scale
      relative to hands and body.
- [ ] Size reckoning: for every product in every shot, the real dimensions, the depth, the lens,
      the expected fraction of the frame and the ratio to a named neighbour are in the plan and in
      the prompt; a start frame was measured with `atp.py scale` before animating; the size ladder
      holds when several products show (`anomaly-catalog.md` §2.7).
- [ ] Anchor class (§4b.1b): the posture, the visible support, the place and its story reason are in the plan
      and the prompt; no lean on a prop the model has to invent; nothing on a thin sheet; no source beat
      taken over. Where the guide lists size as a model limit, the anchor is from its passing list and no
      sizing words are relied on.
- [ ] Source surfaces: every printed surface of the source that a guardrail or §9b names (a poster, a
      livery, a gate board, a monitor page, a shirt print) is an explicit "replace / remove only … and
      reconstruct it as <named concrete content>" sentence in the model's grammar, never a description of
      blankness, and the original item is in the exclusion line (`brand-guardrails.md` §4).
- [ ] Scene layout, perspective and camera logic are consistent across every beat and cut.
- [ ] Placement, contact, grip and occlusion are physically possible at every step.
- [ ] Surroundings are consistent (surfaces, props, background people) with nothing morphing.
- [ ] Lighting, reflections and shadows agree with the scene for the inserted asset in every beat.
- [ ] Natural placement (§4b), if used:
      - the anchor is logical, and the item is visible most of the runtime;
      - the same spot holds in every shot, and every move has a visible action;
      - it is noticed, not featured, and it does not read as an edit.
- [ ] Contents (§4b.0): every glass, cup or other vessel of the product's category in the subject's
      scene holds the product (from its contents sample), with the package open beside it, unless
      the plan says why not. Every vessel's contents are stated in the prompt.
- [ ] Props in the asset photos (a glass, a cup, a snack) are planned as contents or excluded in the
      prompt.
- [ ] Counts: every multiple has its number at t=0, at every event and at the end, and nothing
      appears, vanishes or doubles without a cause (`anomaly-catalog.md` §2.1, §2.5).
- [ ] Openings and use: every use beat goes through the product's real opening or control after its
      preparation step, with the contact point, orientation and body mechanics of its affordance
      sheet; no effect precedes its cause; no reference image shows a later state than t=0
      (§2.2, §2.3, §2.8).
- [ ] Permanence and parts: the count and state of every tracked item are restated after each exit,
      occlusion, cut, hand-off and seam; caps, straps, straws and labels stay with their body
      (§2.4, §2.5, §2.9). The plan lists its QC checkpoints (`anomaly-catalog.md` §3 step 8).
- [ ] Blend: the product reference is scoped to shape, colours and label; the prompt states the
      room's light on the product, its size against a neighbour, its mark angle, its contact shadow
      and its camera angle; the anchor touches or is partly occluded by something; a start frame
      passed the paste test (`anomaly-catalog.md` §2.15).
- [ ] Solidity: every thrown, dropped, swung or passing thing has its path written relative to the
      product (past it on a named side, or onto it with the consequence), the solidity exclusion
      is in the prompt, and no placed object sinks into its surface or a hand (§2.14).
- [ ] Sharpness: the plan's intent names the goal, the job, the one idea, the emotion arc or laugh
      mechanism and the share line, and the concept passed the gate (`creative-direction.md` §6).
- [ ] Transfer (Create): the plan takes only craft from the references and the copy test passed;
      no premise, setting, character, turn, line, first frame, ending or product beat is a
      reference's (`creative-direction.md` §5.0).
- [ ] Motion is natural in speed and weight, with no unmotivated speed changes.
- [ ] Every object state matches the ledger at every checkpoint.
- [ ] Caught errors: every entry of `20-analysis/caught-errors.md` that applies to this video is
      named in the plan, its rule is in the prompt, and its check is a QC checkpoint
      (`ATP/caught_errors.md`, command item 22).
- [ ] Pacing matches the family profile: no dead space, every second has a job.
- [ ] Transitions are all motivated, and multi-clip hand-offs are identical.
- [ ] No free physical motion is pinned to exact timestamps; a required end state has a visible
      cause (§5b).
- [ ] The text plan follows the mode policy. The generated plate is clean (only the product's real
      label). Analyze Mode overlay text is planned as CapCut layers. No accidental text.
- [ ] Inserts (§3c): the generation covers only the reference's own content, and every split point
      is a planned beat boundary.
- [ ] House approach (when examples exist): the plan applies its consistent rules, and none of them
      breaks a hard rule.
- [ ] Beginning, intermediate and end states are all readable and correct.
- [ ] Params, references, prompt and post plan describe the same video (the dependency chain holds).
- [ ] Format: 9:16 and 720p through the model's own parameters (`models/index.json` →
      `output_9x16_720p`), with a conform step if needed.
- [ ] Preflight done: cost known, `adjustments` read and reconciled.

## 9. Post-generation QC (after download)

1. `atp.py qc --video <final> --out <dir> --mode <analyze|edit> --allowed-text "<planned text>"
   --dense "<label>:<a>-<b>" …` with every QC checkpoint of the plan (`anomaly-catalog.md` §3
   step 8), then **view the 5 fps storyboard** sheets in order and every dense sheet under
   `<dir>/dense/`.
2. Check against the plan: identity, asset geometry (compare with the canonical template), the ledger
   states, interactions (densify contact moments with `atp.py frames --range a-b --fps 15 --sheet`),
   lighting, text (unexpected text or pseudo-text = fail), pacing (dead head/tail → `atp.py trim`),
   and format (720×1280).
   - **Placement (§4b):** compare the item's spot and state across the sheets, and densify around
     cuts, pickups, set-downs and any move (a car driven in or away).
   - These count as a **regenerate** reason: the item missing, unrecognisable, duplicated, changing
     spot without a visible action, featured like an ad, or looking pasted in. "Pasted in" is
     measured, not felt: the eleven-sign paste test on one full-resolution frame at rest and one in
     use, against the nearest neighbour at the same depth (`anomaly-catalog.md` §2.15), with the
     result written in the verdict.
   - **Contents (§4b.0):** every vessel of the product's category in the subject's scene shows the
     product's contents (colour, clarity, bubbles, garnish), whether it was planned or came from an
     asset photo. A glass of water beside the can, or any other consumable of the category that is
     not the product, is a **regenerate** reason, never a note. The corrected attempt states the
     vessel's contents from the sample, or excludes the vessel when contents would be illogical.
   - **Motion beats at the full frame rate.** Every motion beat gets
     `atp.py frames --range a-b --fps 30 --sheet` across the whole beat: spins, tosses, catches,
     pours and landings; a vehicle driving, turning, braking or parking; a door or lid opening. The
     5 fps sheets hide single-frame cheats. The motion must stay continuous and follow its own
     physics (§5b): a spin keeps its direction and slows, a toss keeps its arc, a vehicle speeds up
     and slows gradually with its wheels turning at its speed. A snap, a pause-and-resume without a
     cause, a reversal, a slide without a cause, or a morphing label, badge or body is a
     **regenerate** reason (§5b).
   - **Action sync (§5c),** whenever the original audio comes back: `atp.py sync-check` and its
     sheet, plus the sync anchors densified. Drift or a moved action is a **regenerate** reason;
     a steady offset is a post-fix.
   - **Leftovers:** check against §9b. Only its **must-not-survive** list counts as a finding.
     Everything on its **fine** list is ignored: not reported, not asked about, not regenerated.
   - **Size** (`anomaly-catalog.md` §2.7): on a full-resolution frame at rest, one in use and the
     last, `atp.py scale --product-cm <H> --product-px <y0-y1> --ref-cm <h> --ref-px <y0-y1>`
     against the named neighbour (and `--distance --lens` for the shot); the observed multiple of
     the expected size goes in the verdict. Over 25 %, a size that changes between shots, or a
     product larger than the hand that holds it is a **regenerate** reason with no post-fix;
     15–25 % is a note only for a static product with a readable label. On a model whose guide lists
     size as a model limit, the retry changes the form or the anchor class from the guide's passing list,
     never the sizing words; a second miss ships the best take flagged, and the miss is recorded.
   - **Posture, support and place** (`anomaly-catalog.md` §2.16): at 30 fps on every rest and every pass
     of a hand or sheet. A lean against nothing, a posture the shape cannot take, a pack touching a
     working hand or arm, a doubled or warped sheet, or a source beat taken over is a **regenerate**
     reason with no post-fix; the story reason is its own line of the verdict.
   - **Source surfaces** (§8): each printed surface that a guardrail or §9b names, at full resolution and
     by `atp.py qc` OCR. A reproduced poster, livery, board or screen is a **regenerate** reason, and the
     retry replaces it with a named concrete thing instead of describing blankness.
   - **Caught errors** (`ATP/caught_errors.md`, command item 22): each entry the plan applies is
     checked by id and written in the verdict; a failed check is a regenerate reason when the
     entry's class says so.
   - **Counts, openings and permanence** (`anomaly-catalog.md` §4): count every multiple at every
     checkpoint and write the numbers in the verdict; on every use beat check the preparation step,
     the part used and the contact point on the 30 fps sheet; before and after every exit,
     occlusion, cut and seam compare count, spot, state, size and label orientation. A count or
     state that changes without a cause, a use through a part with no opening or a closed one, and
     an effect before its cause are **regenerate** reasons. The catalog names the only post-fixes:
     a pixel hold on an untouched static anchor in a locked shot, a one-frame trim, a recolour or a
     punch-in in a locked shot.
3. **Verdict** (record it in the run log with the reason):
   - **accept**;
   - **post-fix**: trim, conform, restore-audio or a sync offset (text and inserts are fixed in the
     CapCut project);
   - **regenerate**: once, with a corrected request, after diagnosing whether the prompt, a
     reference or a parameter caused the problem. The model stays locked. Report the failure
     honestly if the retry also fails.
   These rules apply autonomously in Analyze Mode.
4. **Edit Mode review:** the user decides. After every attempt the finished video is opened for them
   (`atp.py open`) and they choose:
   - **Looks good** → next video;
   - **Needs changes** → re-edit, always from the **original source video**, with their feedback
     folded into a new request (new attempt, new ledger fingerprint);
   - **Stop**.
   Repeat until approved. Automated QC findings are shown with the video, not acted on silently.

## 9b. What must not survive, and what is fine (all modes)

UGC is full of everyday branded stuff. A Kirby poster, a Hello Kitty ornament or an AYBL hoodie in
a reference's room is normal, and so is a sign across the street. By default only two things have
to go: what makes the video **someone else's** or a **platform repost** (the copyright and
ownership floor, rows 1–6), and what the generation service **refuses to render** (row 7, a
block, not a rule). The pipeline has **no content rules of its own**: alcohol, weapons, gore,
profanity, meme faces and everything else a brand might dislike stay exactly as the reference
shows them unless the client's guardrails name them (`brand-guardrails.md`), and nothing is ever
blurred, pixelated, softened or removed on the pipeline's initiative.

| Must not survive: fix it | Fine: leave it, never flag it |
|---|---|
| The **original person or character** being replaced, in any shot, reflection or mirror | **Background decor:** posters, plushies, figurines, ornaments, wall art, toys, even of famous characters (Kirby, Hello Kitty) |
| The **original product** being swapped, and any **competitor product of the client's category** anywhere in frame (another energy drink for a drink client, another gum brand for a gum client, a rival car that is featured or has a readable badge for a car client; anonymous passing traffic is fine) | **Clothing and footwear** logos, stripes and prints on anyone (AYBL, three stripes, a swoosh) |
| **Overlay text:** captions, subtitles, hook text, stickers, usernames and handles, timestamps. The planned text comes back as CapCut layers | **Environmental text:** shop and street signs ("PHARMACY", "SALON"), generic labels, everyday packaging in the background |
| **Platform logos and watermarks:** TikTok, Instagram / Reels, YouTube Shorts, CapCut, Snapchat, creator watermarks | **Brands seen in passing:** furniture, appliances, cars, phones, laptops, unless they compete with the client's product (left) |
| **Featured third-party branding:** a readable brand name or logo that is held, used, centred or in close-up (a branded coffee cup in hand, a sneaker box shown to camera) | Anything the reference shows that is not featured, not an overlay, not a watermark, not refused by the service and not named by a guardrail |
| **A copyrighted character as the subject** (a costume, a toy presented to camera) and studio / film / character names in prompts. Higgsfield blocks those as "ip_detected" | **Meme inserts and the faces in them,** cut from the reference as they are (`generation-system.md` §3c): never blurred, never cropped, never replaced unless a guardrail names the person |
| **Service blocks (a block, not a rule):** what the generation service refuses or moderates (`Request Moderated`, `ip_detected`, a model's own real-face refusal where its guide says so): sexual content and nudity, graphic self-harm, hate symbols. The job fails, so the plan avoids them and a reference built on them is dismissed; a brand rule cannot enable them | **Brand-dependent content, nothing by default:** weapons, alcohol, tobacco and vapes, gambling, drugs, gore and fake blood, dangerous stunts, profanity, political or religious content, celebrity cameos in memes, and anything else a brand may dislike. It stays as the reference shows it unless a guardrail in the client's documents names it (`brand-guardrails.md` §2); then it is a hit, handled by the audit |

**The client's guardrails are the only content rules** (`brand-guardrails.md`): the content bans,
the competitor list they name or imply, the people whose likeness is excluded, the count limits,
the context rules, the banned wording and the required disclaimers. A competitor's mark is
**de-branded**, never blurred: the name, the logo and the identifying trade dress are removed and
the object stays as a plain one of the same shape, size, spot and light. Without a guardrail
document, only the floor (rows 1–6) and the service blocks apply, and the right column is left
alone in full.

**Fixes are autonomous and cost-aware:**
- **Small static leftovers** (a watermark, a corner logo, a sticker remnant): fix them locally and
  for free with `atp.py clean --delogo` on the clean video before CapCut. A Recreate / Edit source
  is cleaned before upload (`text-and-format.md` §2.2).
- **Everything else on the left:** one corrected regeneration that names the item explicitly
  ("Replace only…", "Remove only…").
- **Still failing:** report it in the wrap-up. In Analyze Mode, never ask about it mid-run.
- **The right column never costs a retry.**

Keep it short: 8–12 lines.

```
Video N of M — <direction / content family>
Concept: <one line>
Why it works: <goal and job; the one idea; the emotion arc or laugh mechanism; the share line> (creative-direction.md)
Reference pattern: <which analyzed videos/mechanism, e.g. "V03/V07 hook-then-demo, payoff at ~5 s">
Taken / left (Create): <craft carried: style, pacing, hook type, payoff timing, text role, product read | subject invented: premise, setting, characters, turn, ending; copy test passed against V…> (creative-direction.md §5.0)
Characters/assets: <approved assets used; element/media ids not shown>
House approach: <the rules applied from 20-analysis/house-approach.md | none (no examples)>
Substitutions: <source entity → client entity, per entity> | Placement: <client entity → anchor, e.g. "can on desk right of laptop; one sip at ~6 s, set back", "car parked at the curb behind the bench; stays parked">
Main action & states: <start → key change → end>
Counts & use: <every multiple with its number over time; each use beat's part and contact ("spout, cap flipped open, head level"); the QC checkpoints>
Size: <per product and shot: real H cm; depth d m; lens f mm → ~N % of frame height (~px); neighbour and ratio ("2/3 of the bottle beside it"); size ladder across products; constancy> (anomaly-catalog.md §2.7)
Guardrails: <none supplied | G<n> (rule) → operation and time, per hit, e.g. "G2 (two cans max) → third can removed, count 2 at every checkpoint; G3 (no competitors) → Monster can de-branded on the shelf; G4 (ambassador) → face swapped, voice remains in the original audio" | Create: the invariants applied> (brand-guardrails.md)
Caught errors applied: <none apply | CE-004 (blend: reference scoped, room light stated, paste test in QC); CE-005 (size: reckoning in the prompt, T scale in QC); …> (ATP/caught_errors.md)
Style & camera: <look, lighting, camera behaviour>
Text: <none | CapCut text layers in the house style: "…" (where, when) | real label, logo or badge text on the product>
Inserts: <none | "<meme>" cut from <V> at <t_in–t_out>, placed at <split> s>
Sound: <generated: dialogue + ambience | soundtrack: <source>, <role / mood / ~BPM>, <license> | SFX: <name @ t, …>>
CapCut project: <DD_Mon_YYYY_vNN>
Model & operation: <model id, operation, duration, 9:16 720p, audio on/off> · est. <credits> credits
Adaptation logic: <what was changed from the reference and why (geometry, grip, lighting, pacing fixes)>
```

For a multi-clip video, add one line: `Clips: K — <seam times and methods (cut / extension /
last-frame chain)>`.

The brief is also saved as `40-briefs/video-NN-brief.md` (command X6): a caught-error entry
(`ATP/caught_errors.md`, item 22) carries it with the final prompt and the QC verdict, so a
reported problem can be read against what was planned and what was asked.

In Analyze Mode, proceed after showing the brief. The only pause is the permission for a video over
30 s that needs 2+ generations (command A7b). Uncertainties are resolved by the plan's own rules and
stated in the brief's adaptation line, not asked. In Edit Mode, the gates of command E6 and X9-R
apply.
