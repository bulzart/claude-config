---
guide: minimax-hailuo
title: MiniMax Hailuo 02 / Hailuo 2.3 (incl. Fast variants)
provider: MiniMax (Hailuo AI)
higgsfield_model_ids: [minimax_hailuo]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# MiniMax Hailuo 02 / Hailuo 2.3 — model engineering guide

> Scope: Higgsfield id `minimax_hailuo` (provider label "Hailuo") wraps MiniMax's pre-H3 video models behind one
> `variant` parameter: `minimax`, `minimax-fast`, `minimax-2.3`, `minimax-2.3-fast` [HF]. These are silent,
> text/image-to-video models with a first-party bracket camera-command syntax. Output format is fixed at 9:16, 720p:
> on this id that requires a 9:16 start frame and a deterministic downscale (§2.6). MiniMax's current flagship, H3,
> is covered in `minimax-h3.md`. The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

**Which public versions are these?** MiniMax's API lists `MiniMax-Hailuo-02`, `MiniMax-Hailuo-2.3` and
`MiniMax-Hailuo-2.3-Fast` [OFFICIAL]. Evidence for the mapping:

| Higgsfield variant | most likely public model | evidence | confidence |
|---|---|---|---|
| `minimax` | MiniMax Hailuo 02 (2025-06-18) | Higgsfield says 512 is unsupported by the 2.3 variants and incompatible with `end_image` [HF]; upstream, 512P exists only for `MiniMax-Hailuo-02`, and first+last-frame exists only for `MiniMax-Hailuo-02` and "does not support 512P" [OFFICIAL] | high [INFERRED] |
| `minimax-2.3` (default) | MiniMax Hailuo 2.3 (2025-10-28) | name match; 768/1080 only [OFFICIAL/HF] | high [INFERRED] |
| `minimax-2.3-fast` | MiniMax Hailuo 2.3 Fast | name match; image-to-video only upstream [OFFICIAL] | high [INFERRED] |
| `minimax-fast` | a speed tier of Hailuo 02 ("Hailuo 02 Fast", 512p image-to-video, 6/10 s, sold by third-party hosts) | no such model in MiniMax's own API [OFFICIAL]; third-party listings [SECONDARY] | low [INFERRED] |

- **Positioning.** Hailuo 02: "Native 1080p, SOTA Instruction Following, Extreme Physics Mastery" — "currently the
  only model globally capable" of intricate scenarios such as gymnastics; offered as 768p-6s, 768p-10s, 1080p-6s
  [OFFICIAL]. Hailuo 2.3: "Building upon the Hailuo 02 model, it further enhances dynamic expression… physical
  actions, stylization, and character micro-expressions, while further optimizing its response to motion commands";
  better anime/illustration/ink-wash/game-CG styles; "enhanced response to motion commands for objects" [OFFICIAL].
  2.3 Fast "generates videos faster at a lower price, reducing costs for batch creation by up to 50%" [OFFICIAL].
  Higgsfield: "Natural physics, facial emotion, multiple variants" [HF].
- **Best for:** short (6/10 s) physical-motion shots from a 9:16 still — bodies, sports, falls, fluids; facial
  emotion; stylized looks (2.3); cheap iterations (2.3 Fast).
- **Weaker at:** no audio; no references; no aspect-ratio control (text-to-video is landscape → unusable for 9:16);
  ≤10 s; 1080p only at 6 s; no Edit Mode; no first-party prose prompt guide. Not in the current Artificial Analysis
  top-25 image-to-video board [SECONDARY] — a 2025 generation.
- **Choose `minimax_hailuo` when** you need a silent, physics-heavy or emotive 6–10 s shot animated from an approved
  9:16 frame. **Choose another model when** you need text-to-video, audio, references, >10 s, multi-shot or Edit Mode
  (`minimax_h3`, `wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Start frame → video | `start_image` (9:16) | any variant; output ratio follows the image [OFFICIAL/HF] |
| First + last frame → video | `start_image` + `end_image`, variant `minimax` | upstream only on Hailuo 02, 768/1080 [OFFICIAL] |
| Text-to-video | `prompt` only; variant `minimax` or `minimax-2.3` | landscape output — not for 9:16 deliverables (§2.6) |
| Camera control | `[command]` brackets in the prompt | 15 official commands [OFFICIAL] |
| References, audio, edit, extension | — | N/A on Higgsfield |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `minimax_hailuo` | `variant` | `minimax`, `minimax-fast`, `minimax-2.3`, `minimax-2.3-fast` | `minimax-2.3` | "Minimax Hailuo model variant." [HF]; mapping in §1 |
| `minimax_hailuo` | `duration` | `6`, `10` | 6 | "Duration in seconds." [HF] |
| `minimax_hailuo` | `resolution` | `"512"`, `"768"`, `"1080"` | `"768"` | "'512' is incompatible with end_image, and is not supported by the 'minimax-2.3' / 'minimax-2.3-fast' variants." [HF] |
| `minimax_hailuo` | `aspect_ratio` | none (empty list) | — | no ratio control; see §2.6 [HF] |
| `minimax_hailuo` | prompt_optimizer, fast_pretreatment, audio | — | — | not exposed on Higgsfield [HF]; upstream schemas contain no audio, negative-prompt or seed fields [OFFICIAL, by absence] |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame (upstream `first_frame_image`) | 1; JPG/JPEG/PNG/WebP, <20 MB, short edge >300 px, aspect 2:5–5:2 [OFFICIAL] | "Video resolution follows the first frame image" [OFFICIAL]; must be 9:16 |
| `end_image` | last frame (upstream `last_frame_image`) | 1; same limits; Hailuo 02 only; not with 512 [OFFICIAL/HF] | "If first and last frames differ in size, the last frame will be cropped to match the first" [OFFICIAL] |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
Upstream duration × resolution matrix [OFFICIAL]:

| model | 512P | 768P | 1080P |
|---|---|---|---|
| Hailuo 2.3 / 2.3 Fast | — | 6 or 10 s | 6 s only |
| Hailuo 02 | 6 or 10 s (image-to-video only) | 6 or 10 s | 6 s only |
| Hailuo 02 first+last frame | — | 6 or 10 s | 6 s only |

- **1080 + 10 s is not a valid upstream combination** [OFFICIAL]; the server snaps/clamps or rejects [HF contract].
- **Aspect ratio:** not selectable [HF]; image-to-video follows the start frame [OFFICIAL/HF]; text-to-video is 16:9
  (§2.6).
- **Audio:** none documented; treat output as silent [INFERRED from OFFICIAL API with no audio fields].

### 2.4 Call recipes
Start frame → video (9:16 frame; the deliverable path):
```json
{"model":"minimax_hailuo","prompt":"<MOTION PROMPT with [camera commands]>","variant":"minimax-2.3","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"resolution":"768"}
```
Fast iteration (9:16 frame):
```json
{"model":"minimax_hailuo","prompt":"<MOTION PROMPT>","variant":"minimax-2.3-fast","medias":[{"value":"<IMAGE_MEDIA_ID or JOB_ID>","role":"start_image"}],"duration":10,"resolution":"768"}
```
First + last frame (Hailuo 02 only; both frames 9:16, identical size):
```json
{"model":"minimax_hailuo","prompt":"<PATH PROMPT>","variant":"minimax","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"resolution":"768"}
```
Text-to-video: no recipe in the fixed format — the output is landscape (§2.6). For a text-only concept, generate a 9:16
still first and use the start-frame recipe. Preflight any call with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. **Resolution values are bare strings** `"512"`, `"768"`, `"1080"` (no "p") [HF].
2. **`end_image` works only with variant `minimax`** (Hailuo 02) upstream [OFFICIAL]; with 2.3 variants expect rejection
   or silent omission [INFERRED]. Never combine `end_image` with `"512"` [HF].
3. **Fast variants need a start frame:** `MiniMax-Hailuo-2.3-Fast` is absent from the upstream text-to-video list
   [OFFICIAL]; `minimax-fast` presumably too [INFERRED].
4. **`"512"`** needs variant `minimax` (or possibly `minimax-fast`) and a start image upstream; never for deliverables
   (§2.6) [OFFICIAL/HF/INFERRED].
5. **Prompt optimizer:** upstream `prompt_optimizer` defaults to `true` ("Set to false for more precise control") and
   is not exposed [OFFICIAL/HF] → prompts may be rewritten; keep camera commands explicit [INFERRED].
6. **Prompt limit 2,000 characters** [OFFICIAL]. **No negative prompt, seed or audio** [OFFICIAL/HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)
How aspect is set: there is no ratio parameter [HF]. Image-to-video output follows the start frame ("Video resolution
follows the first frame image" [OFFICIAL]; Higgsfield: "Aspect Ratio: Matches input image dimensions" [HF]).
Text-to-video has no documented ratio [OFFICIAL silence]; third-party specs list 16:9 only (768p = 1366×768, 1080p =
1920×1080) [SECONDARY] — cutting 9:16 out of that would discard ~68% of the width, so text-to-video is not a 9:16 path.

| path | params | expected output | action |
|---|---|---|---|
| Start frame (± end frame) | 9:16 `start_image` (and identical `end_image`); `"resolution":"768"` (6 or 10 s) or `"1080"` (6 s); no `aspect_ratio` | portrait at the tier; exact pixels undocumented — a 768-px short edge (≈768×1366) is likely [INFERRED] | measure, downscale |
| `"512"` / `minimax-fast` | — | short edge below 720 would need upscaling | drafts only |
| Text-to-video | — | 16:9 [SECONDARY] | do not use for deliverables |

Make the 9:16 still first (e.g. 1080×1920), then generate. If the output's short edge is below 720, regenerate at
`"1080"` (6 s) rather than upscale [INFERRED]. Otherwise finish with `atg.py conform --video "<in>" --out "<out>"`
(scale-to-cover + focus crop to exactly 720×1280, never stretched). If `conform` refuses (>12% loss), the frame ratio
was wrong — fix the frame and regenerate; never force a landscape text-to-video clip into 9:16 [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
MiniMax publishes no prose prompt formula for Hailuo; first-party examples are very short and physical (§4.0)
[OFFICIAL]. Higgsfield's Hailuo 2.3 guide: "Keep prompts simple and visual"; "Keep prompts short and physical"
[HF]. MiniMax also claims Hailuo 02 "accurately interprets and executes highly detailed prompts" [OFFICIAL].
Recommended order [INFERRED synthesis of the examples]: **subject → physical action chain → camera command right after
the clause it accompanies → setting and light → end state**. 1–4 sentences, about 20–70 words; English is safest;
≤2,000 characters [OFFICIAL limit].

### 3.2 Subject and identity
Image-to-video: the frame defines the subject; describe only motion and expression, never contradictory traits
[INFERRED]. Hailuo 2.3 improves "live-action facial performances and micro-expression changes" [OFFICIAL] — describe
emotion as visible behaviour ("her smile fades, eyes drop to the floor") [INFERRED].

### 3.3 Action, motion and physical interaction
Physics is this family's selling point: extreme body motion (gymnastics) and, in 2.3, "more complex character body
movements with greater fluidity, naturalness, precision, and control" plus better object motion commands
[OFFICIAL]. Write strong physical verbs in time order with consequences ("the glass tips, hits the floor and
shatters, water spreading across the tiles") [INFERRED]; one main action per 6 s, two for 10 s [INFERRED]. Grip and
states: §3.14.

### 3.4 Environment, lighting and style
One sentence of setting and light. Hailuo 2.3 supports "anime, illustration, as well as special art styles like ink
wash painting and game CG" [OFFICIAL]; MiniMax notes near-photorealistic "lighting direction, shadow transitions, and
color tones" even with dynamic camera moves in 2.3 [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure
No documented multi-shot or timestamp syntax [OFFICIAL silence]. Each generation is one continuous shot; sequence
actions with "then" and camera moves by order ("…[Push in], then…") [OFFICIAL usage rule]. Build multi-shot pieces by
chaining clips (§3.14).

### 3.6 Camera language and dedicated camera / motion controls
First-party bracket syntax for `MiniMax-Hailuo-2.3`, `-2.3-Fast` and `-02` (text, image, first+last frame)
[OFFICIAL]:

| movement | commands |
|---|---|
| Truck | `[Truck left]`, `[Truck right]` |
| Pan | `[Pan left]`, `[Pan right]` |
| Push | `[Push in]`, `[Pull out]` |
| Pedestal | `[Pedestal up]`, `[Pedestal down]` |
| Tilt | `[Tilt up]`, `[Tilt down]` |
| Zoom | `[Zoom in]`, `[Zoom out]` |
| Shake | `[Shake]` |
| Follow | `[Tracking shot]` |
| Static | `[Static shot]` |

Rules [OFFICIAL]: "Multiple commands inside one `[]` take effect simultaneously (e.g., `[Pan left,Pedestal up]`).
Recommended max: 3."; sequential commands "appear in order"; "Free-form descriptions also work, but explicit commands
yield more accurate results." (The docs' sequential example uses `[Push out]`, which is not in the list — use `[Pull
out]`.) Whether `minimax-fast` honours commands is unverified [INFERRED].

### 3.7 References (image / video / audio)
N/A on Higgsfield — no reference roles [HF]. (MiniMax's separate subject-reference model is not wrapped by this id.)

### 3.8 Start and end frames
- `start_image` is the first frame and fixes resolution and ratio [OFFICIAL]; describe motion from that exact state.
- First + last frame (variant `minimax`): describe the transformation or movement connecting the two [OFFICIAL
  example]; the last frame is cropped to the first frame's size if they differ [OFFICIAL] → both 9:16, identical size.

### 3.9 Audio, dialogue and sound
N/A on Higgsfield — no audio generation documented [OFFICIAL silence/INFERRED]. If a character must appear to speak,
describe mouth movement only and add audio in post [INFERRED].

### 3.10 Negative constraints
No negative-prompt field upstream or on Higgsfield [OFFICIAL/HF]; official examples contain no exclusions [OFFICIAL].
In short prompts a long exclusion list dominates the text — use at most one short sentence and describe the wanted
state positively [INFERRED].

### 3.11 Visible text
**(a) Reliability.** MiniMax publishes nothing about Hailuo text rendering and does not market it for text [OFFICIAL
silence]. Treat in-frame text as unreliable [INFERRED].

**(b) Clean plate — default in Analyze Mode.** Generate without text and add hooks, captions and labels in post
(`atg.py captions`, libass). No provider phrasing exists; use one plain closing sentence, "No text, captions, logos or
watermarks.", plus positive text-free surfaces [INFERRED]. The start frame must be text-free — the model animates what
is in it. Upstream `prompt_optimizer` may expand the prompt [OFFICIAL], so positive clean descriptions are more robust
than the exclusion alone [INFERRED].

**(c) Intentional in-frame text.** Only if it is already rendered in the 9:16 start frame, scene-bound (sign,
packaging, screen) and should stay static: "the lettering on the <object> stays unchanged"; keep camera moves small and
verify with `atg.py qc --mode analyze --allowed-text "<text>"` [INFERRED]. Otherwise post.

**(d) Edit operations — removing source text.** N/A on Higgsfield: no video input on this id [HF], so it cannot
regenerate a supplied clip. A frame taken from a supplied clip must have its overlays removed with an image tool before
use, and the result is new footage, not an edit [INFERRED]. Use `wan3_0` or `minimax_h3` (or local `atg.py clean
--delogo` for small static overlays).

**(e) Watermark risk.** The MiniMax Hailuo API has no watermark parameter [OFFICIAL, by absence]; invented marks are
still possible [INFERRED]. `atg.py qc` OCR flags them — regenerate.

### 3.12 Character / identity consistency
Identity comes only from the 9:16 start frame. Use a high-quality frame with the approved face clearly visible; limit
fast head turns and occlusions; prefer 6 s for close-ups [INFERRED]. For multiple clips, start each from frames of the
same approved character set [INFERRED].

### 3.13 Product and object fidelity
Put the approved product in the start frame; to land on an exact packshot use variant `minimax` with it as `end_image`
[OFFICIAL capability/INFERRED use]. Add "the <object> keeps its exact shape, proportions and color; it does not bend or
change size" and prefer `[Static shot]`, slow `[Push in]` or `[Truck left]` over fast orbits [INFERRED]. 2.3 improved
"response to motion commands for objects" per MiniMax's e-commerce beta testers [OFFICIAL].

### 3.14 Integration and continuity
**Across clips.** Last frame of clip A (`atg.py last-frame --video <clip> --out <handoff.png>`) → `start_image` of clip B via `media_upload` →
PUT → `media_confirm` [HF contract]; for a planned hand-off use first+last frame on variant `minimax`
[OFFICIAL/INFERRED]. Keep variant, resolution and lighting words identical across a sequence [INFERRED].

**Inserted or replaced assets.** No reference roles: the asset must already be composited into the 9:16 start frame
(and end frame). In the prompt, describe only how it moves: size relative to the hand, orientation, grip ("fingers
wrapped around the neck of the bottle"), occlusion, and where it ends [INFERRED structure].

**Scene light on the asset.** Write "light direction, shadows and color stay as in the first frame"; name the key light
once if the object moves through it ("it catches the warm window light from the left as it turns") [INFERRED]. 2.3
claims good "lighting direction, shadow transitions, and color tones" under camera motion [OFFICIAL].

**Persistent states.** End each clip with a state ("the lid stays on the table, jar open, honey level unchanged"); use
first+last frame (variant `minimax`) when the end state must be exact [OFFICIAL capability/INFERRED].

**Known failures.** No official failure list. Documented constraints that cause failures: 1080 limited to 6 s, cropped
mismatched end frames, optimizer rewriting [OFFICIAL]. Physics is a documented strength [OFFICIAL]; others [INFERRED].
Slop prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples:

1. Text-to-video with camera commands — MiniMax API, Create Text-to-Video Generation Task, https://platform.minimax.io/docs/api-reference/video-generation-t2v
   > "A man picks up a book [Pedestal up], then reads [Static shot]."
2. Image-to-video — MiniMax API, Image-to-Video Task, https://platform.minimax.io/docs/api-reference/video-generation-i2v
   > "A mouse runs toward the camera, smiling and blinking."
3. First + last frame — MiniMax API, Create First & Last Frame Video Generation Task, https://platform.minimax.io/docs/api-reference/video-generation-fl2v
   > "A little girl grow up."
4. Camera-command rules — same API pages
   > "Multiple commands inside one `[]` take effect simultaneously (e.g., `[Pan left,Pedestal up]`). Recommended max: 3."
   > · "Commands appear in order, e.g., "...[Push in], then...[Push out]"." · "Free-form descriptions also work, but
   > explicit commands yield more accurate results."
5. Higgsfield first-party examples [HF] — Minimax Hailuo 2.3: A Creative Guide, https://higgsfield.ai/blog/Minimax-Hailuo-2.3-A-Creative-Guide
   > "Human transforming into werewolf under moonlight" · "Perfume bottle melting into gold" · "Keep prompts short and
   > physical ('melt,' 'ignite,' 'morph')"

Patterns they teach:
- **Length:** 4–12 words; one subject, one or two actions (1–3).
- **Camera placement:** the bracket follows the clause it applies to; sequences joined with ", then" (1, 4).
- **Subject vs camera:** subject motion is plain prose, camera motion is only the bracket (1).
- **Image-to-video:** motion and expression only — no re-description of the frame (2).
- **First+last frame:** one phrase naming the change between the frames (3).
- **Exclusions:** none in any official example; transformation verbs are Higgsfield's stylistic lever (5) and a
  morphing risk for products.

### 4.1 Text-to-video
Follows patterns: short physical clause + bracket after it. Landscape output — not for 9:16 deliverables (§2.6).
```text
<Subject with 2–4 visual traits> <physical action 1> [<camera command>], then <action 2> [<camera command>]. <Setting>, <light>. No text, captions, logos or watermarks.
```
Worked example (variant `minimax-2.3`, 6 s, preview only): "A young gymnast in a plain navy leotard sprints down the
mat and launches into a round-off back handspring [Tracking shot], then lands cleanly and raises both arms [Static
shot]. Empty training hall, soft morning light. No text, captions, logos or watermarks."

### 4.2 Start frame (and end frame) to video
Follows patterns: motion only, bracket after each clause, ", then", end state.
```text
<What moves first, from the frame's exact state> [<camera command>], then <next movement> [<camera command>], <end state>. <Subject> keeps the same appearance, clothing and proportions; light and shadows stay as in the first frame. No text, captions or watermarks.
(FLF, variant minimax) <Change connecting the first frame to the last frame>, ending exactly on the last frame.
```
Worked example (variant `minimax-2.3-fast`, 10 s, 9:16 `start_image` = a hand holding a closed glass jar of honey on a
table): "The hand unscrews the lid slowly and sets it on the table, then a spoon dips in and lifts a thick ribbon of
honey that folds back into the jar [Push in], then the spoon rests on the rim [Static shot]. The jar keeps its exact
shape and size; light and shadows stay as in the first frame. No text, labels, captions or watermarks."

### 4.3 Reference-to-video
N/A on Higgsfield — `minimax_hailuo` accepts only `start_image` and `end_image` [HF]. Use `minimax_h3`.

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield. Approximate an extension by using a clean last frame as the next `start_image` [INFERRED].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Landscape output | text-to-video, or non-9:16 start frame [SECONDARY/OFFICIAL] | 9:16 start frame always (§2.6) |
| Request rejected / snapped | `"1080"` with 10 s; `"512"` with 2.3 variants or `end_image` [OFFICIAL/HF] | 1080 → 6 s; 512 drafts only |
| End frame ignored or error | `end_image` on 2.3 variants [OFFICIAL] | variant `minimax` |
| Fast variant fails on text-only | image-to-video only upstream [OFFICIAL] | attach `start_image` |
| Camera ignores intent | vague prose camera | bracket commands (≤3 per bracket) [OFFICIAL] |
| Last frame cropped | first/last sizes differ [OFFICIAL] | identical dimensions |
| Text/gibberish | text in frames or prompt | §3.11 |
| Expecting sound | silent model [INFERRED] | audio in post, or `minimax_h3` |
| Look differs between variants | mixing variants | one variant per sequence |

**AI-slop tendencies and prevention.** `atg.py qc` flags black and frozen spans; `atg.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | 6 s unless two actions need 10 s; the action should fill the clip [INFERRED] |
| Arbitrary slow motion / speed jumps | "at real-time speed", "one steady pace" [INFERRED] |
| Unmotivated cuts | none documented (single-shot model); keep one continuous action [INFERRED] |
| Camera drift | explicit `[Static shot]` or one command per clause [OFFICIAL syntax] |
| Morphing | avoid transformation verbs ("melt", "morph" — which Higgsfield's own examples promote) unless wanted [HF]; FLF anchors |
| Identity drift | clear start frame, moderate motion, 6 s close-ups [INFERRED] |
| Duplicated objects / clothing changes | "only one <object>"; "clothing unchanged" [INFERRED] |

## 6. Model-specific features and controls
- **Variants:** Hailuo 02 (`minimax`: 512/768/1080, first+last frame), Hailuo 2.3 (`minimax-2.3`: default, better
  motion, faces, styles), 2.3 Fast (`minimax-2.3-fast`: cheaper/faster, image-to-video), `minimax-fast` (unverified)
  [OFFICIAL/HF/INFERRED]. Higgsfield: 2.3 Fast "optimized for speed and iteration", standard 2.3 "ideal for final
  production" [HF].
- **Bracket camera commands** — 15 official commands, combinable and sequenceable [OFFICIAL].
- Upstream-only: `prompt_optimizer`, `fast_pretreatment` [OFFICIAL]; Higgsfield web-app motion presets for 2.3 are not
  part of this MCP id [HF].

## 7. Model-specific pre-generation checklist
- [ ] 9:16 start frame ready (text-free, ≥300 px short edge); no text-to-video for deliverables.
- [ ] Variant chosen (2.3 quality, 2.3-fast drafts, `minimax` for first+last); `"768"` or `"1080"` (6 s); never
      `"512"` for deliverables.
- [ ] First/last frames identical size; `end_image` only on `minimax`.
- [ ] Prompt 20–70 words, physical verbs, bracket after each clause, end state.
- [ ] One short no-text sentence; captions/hooks planned for post (`atg.py captions`); no Edit Mode on this id.
- [ ] Grip, light and end states written (§3.14); slop guards (§5); silence accepted; `get_cost: true`.
- [ ] After generation: `atg.py conform` to 720×1280, then `atg.py qc --mode analyze` (size, freezes, pseudo-text,
      corner marks), identity and product shape.

## 8. Sources
- [OFFICIAL] MiniMax API — Create Text-to-Video Generation Task (models, 15 camera commands, duration/resolution) — https://platform.minimax.io/docs/api-reference/video-generation-t2v (accessed 2026-09-30)
- [OFFICIAL] MiniMax API — Image-to-Video Task (2.3, 2.3-Fast, 02; 512P matrix; image limits) — https://platform.minimax.io/docs/api-reference/video-generation-i2v (accessed 2026-09-30)
- [OFFICIAL] MiniMax API — Create First & Last Frame Video Generation Task (Hailuo 02 only, no 512P, resolution follows first frame) — https://platform.minimax.io/docs/api-reference/video-generation-fl2v (accessed 2026-09-30)
- [OFFICIAL] MiniMax Hailuo 02, World-Class Quality, Record-Breaking Cost Efficiency (2025-06-18) — https://www.minimax.io/news/minimax-hailuo-02 (accessed 2026-09-30)
- [OFFICIAL] MiniMax Hailuo 2.3: A New Level of Complex Video Performance & Media Agent (2025-10-28) — https://www.minimax.io/news/minimax-hailuo-23 (accessed 2026-09-30)
- [OFFICIAL] MiniMax release notes (Hailuo 02, Hailuo 2.3 & 2.3-Fast) — https://platform.minimax.io/docs/release-notes/models (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json; MCP tool contract facts supplied with this task
- [HF] Minimax Hailuo 2.3: A Creative Guide (Higgsfield blog; aspect ratio matches input image) — https://higgsfield.ai/blog/Minimax-Hailuo-2.3-A-Creative-Guide (accessed 2026-09-30)
- [SECONDARY] Hedra model page, MiniMax Hailuo-02 (16:9; 768p/1080p) — https://www.hedra.com/models/video/minimax/hailuo-02-standard (accessed 2026-09-30)
- [SECONDARY] WaveSpeedAI, "Introducing MiniMax Hailuo 02 Fast" (512p image-to-video tier) — https://wavespeed.ai/blog/id/posts/introducing-minimax-hailuo-02-fast-on-wavespeedai/ (accessed 2026-09-30)
- [SECONDARY] Artificial Analysis image-to-video leaderboard — https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Exact output size for a 9:16 start frame at `"768"` and `"1080"` (768-px short edge inferred); whether any portrait
  output falls below a 720-px short edge.
- Text-to-video aspect ratio (only third-party sources say 16:9).
- Identity of `minimax-fast` and whether it supports 768/1080, camera commands or `end_image`.
- Whether Higgsfield rejects, ignores or re-routes `end_image` on 2.3 variants, and `"1080"` with 10 s.
- Whether Higgsfield leaves `prompt_optimizer` on; whether any variant returns audio.
