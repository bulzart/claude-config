---
guide: higgsfield-genjutsu
title: Higgsfield Genjutsu (object replacement and motion transfer)
provider: Higgsfield (in-house)
higgsfield_model_ids: [hf_mult_replace_object, hf_mult_motion_control]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Higgsfield Genjutsu — model engineering guide

> Scope: two video-to-video operations built on one source (driving) video and reference images.
> - `hf_mult_replace_object` (**Object Swap**): replaces a character, object, product, garment or
>   location in a source video while keeping motion, camera, lighting and timing.
> - `hf_mult_motion_control` (**Motion Transfer**): applies a driving video's motion, gestures and
>   camera movement to subjects from reference images, rebuilding the scene.
>
> Tags: **[HF]** catalog, MCP contract, first-party recipe (`../higgsfield/first-party/genjutsu.md`) or
> Higgsfield pages · **[VERIFIED]** · **[SECONDARY]** · **[INFERRED]**.

## 1. At a glance
- **Positioning [HF]:** "rebuilds part of a clip without a full reshoot". Object Swap "replaces the
  object or element you specify while preserving the rest of the original footage". Motion Transfer
  "uses the motion from an existing video as a reference, then applies that movement to a new
  character or rebuilt scene".
- **What stays [HF]:** original motion and timing, camera work and framing, shot structure and pacing.
- **Limits [HF]:**
  - one input video of **4–30 s**;
  - up to **30 reference images**;
  - output up to **1080p**;
  - works on AI-generated and filmed footage.
- **Needs full regeneration instead [HF]:**
  - different character actions or performance beats;
  - changes to duration, pacing or shot structure;
  - "object replacements with significantly different sizes/shapes";
  - "new interactions requiring physical contact or movement";
  - "multiple simultaneous changes across the frame".
- **Choose Object Swap** (Edit Mode) when one clearly defined entity must become the client's entity,
  and the replacement has similar size and handling to the original.
- **Choose Motion Transfer** (Analyze or Edit Mode) when the reference's choreography, gesture timing
  or camera move is the valuable mechanism and the subject or scene must be rebuilt with approved
  characters.
- **Choose Seedance 2.5 `video_edit`** instead (see `seedance-2-5.md`) for several simultaneous edits,
  text removal plus a swap in one pass, or a replacement whose geometry differs strongly.

| Operation | Model id | Media |
|---|---|---|
| Object / character / product / garment / location swap | `hf_mult_replace_object` | 1 source video + 1–30 reference images |
| Motion transfer to a new subject or scene | `hf_mult_motion_control` | 1 driving video + reference images (subject, optionally scene) |

## 2. Higgsfield parameter surface
### 2.1 Parameters
| id | parameter | values | default |
|---|---|---|---|
| both | `resolution` | 480p, 720p, 1080p | 720p |

There are no duration, aspect, audio or genre parameters: the output follows the source video
[INFERRED from the empty `aspect_ratios` and the Higgsfield description].

### 2.2 Media roles
- Catalog roles: `image_references`, `video_references`.
- The first-party recipe passes reference images with role **`image`** and **exactly one**
  source/driving video with role **`video`** [HF]. The server auto-coerces.
- Order: the video first, then the images, in `@ImageN` order (Higgsfield edit convention [HF]).

### 2.3 Duration, resolution, audio
- The duration equals the source's (4–30 s).
- 720p is the default.
- Audio: prior research reported that the source audio is kept [INFERRED, unverified]. After
  download, check with `ffprobe` (`atp.py hf-get` reports `has_audio`) and run `atp.py restore-audio`
  if it is missing.

### 2.4 Call recipes
```json
{"model":"hf_mult_replace_object","prompt":"<edit brief — see §4.4>","resolution":"720p",
 "medias":[{"value":"<SOURCE_VIDEO_MEDIA_ID>","role":"video"},{"value":"<ASSET_IMAGE_1_MEDIA_ID>","role":"image"},{"value":"<ASSET_IMAGE_2_MEDIA_ID>","role":"image"}],
 "folder_id":"<FOLDER_ID>"}
```
```json
{"model":"hf_mult_motion_control","prompt":"<transfer brief — see §4.4>","resolution":"720p",
 "medias":[{"value":"<DRIVING_VIDEO_MEDIA_ID>","role":"video"},{"value":"<CHARACTER_IMAGE_MEDIA_ID>","role":"image"},{"value":"<SCENE_IMAGE_MEDIA_ID>","role":"image"}],
 "folder_id":"<FOLDER_ID>"}
```

### 2.5 Gotchas
- Exactly one video per call.
- Trim the source to 4–30 s around the part that matters; the whole clip is billed.
- The web app's 30+ presets are not exposed through MCP. Write a short brief instead.
- The legacy `motion_control` MCP tool (Kling 3.0 Motion Control) is a different engine. The MCP
  instructions say to route motion transfer to `hf_mult_motion_control` [HF].
- Pricing [HF, Sept 2026]:
  - 15 s: 40 / 104 / 144 credits at 480p / 720p / 1080p;
  - 10 s at 1080p: 99.
  Always preflight.

### 2.6 9:16 / 720p mapping
- `resolution:"720p"`; the output aspect follows the source video.
- **Make the source 9:16 before submitting:**
  - `atp.py conform` with a focus point, when a crop keeps every important subject (≤ 12 % loss by
    default);
  - otherwise Higgsfield `reframe` to 9:16 at 720p;
  - otherwise regenerate with a reference-to-video model.
- After download, `conform` to exactly 720×1280 when needed, then `qc`.

## 3. How the model reads a prompt

### 3.1 Structure
a short, operational brief. "Optional, short description" when presets aren't
used [HF]. Say what changes and what stays, not the whole scene.

### 3.2 Identity
Object Swap identifies the target in the source by a unique plain-language anchor
("the white mug in the man's right hand", "the woman in the green jacket"), then binds the
replacement to `@ImageN`.

### 3.3 Action / physics
do not re-direct the action; the source's action is inherited.
- State that the replacement follows the original's position, trajectory, orientation, occlusion
    and contact points.
- If the client asset's size or shape differs, state the real size and grip adaptation.
- Large differences are a documented failure → regenerate instead.

### 3.4 Environment / light
say "matches the scene's lighting direction and colour, casts
consistent shadows and reflections". The source light is inherited.

### 3.5 Chronology
the source timeline governs. For a partial-time swap, name the window ("from
the moment she picks it up").

### 3.6 Camera
inherited. Never ask for new camera moves.

### 3.7 References
several views of the same asset jointly define it; say so ("@Image1 and
@Image2 are the front and side of the same bottle").
- Motion Transfer: `@Image1` = subject identity, optional `@Image2` = scene. Exclude the driving
    video's identity, clothing and background explicitly.

### 3.8 Frames
N/A.

### 3.9 Audio
inherited or none; verify it and restore it locally.

### 3.10 Negatives
there is no field. Use scoped exclusion sentences ("the original object must not
appear in any frame").

### 3.11 Visible text
- (a) Genjutsu preserves untargeted content, so the source's captions, usernames and watermarks
    survive by default [INFERRED from "preserving the rest"].
- (b) **Edit Mode policy removes them.**
    - Remove small static overlays locally first (`atp.py clean --delogo …`).
    - For large captions, add an explicit removal clause to the brief ("Remove all on-screen caption
      text and usernames and reconstruct the background behind them"). Its effectiveness is
      **unverified**: QC with OCR afterwards.
    - If text survives, run the whole edit with Seedance 2.5 `video_edit`, where removal is a
      documented operation.
- (c) N/A.
- (d) See (b).

### 3.12 Identity
a replaced person gets their complete look (face, hair, outfit) from the
reference image. State it, and state that the original person must not appear in any frame
(Higgsfield's exclusion pattern, see `first-party/ad-multiplier-prompt-writer.md`).

### 3.13 Product fidelity
the canonical template image is authoritative for shape, proportions,
silhouette, cap/closure and label.
- "Keep the product's exact shape and proportions from @Image1; do not adopt the original object's
    shape."
- Scale: "the same real-world size as in @Image1: a palm-sized bottle about the length of the hand".

### 3.14 Integration and continuity
say "tracks perspective and shadows across the shot" [SECONDARY
phrasing, see §4.0] and "occluded by fingers exactly where the original was".
- State the persistent states (label faces the camera when the original's front did, the lid state
    matches).

## 4. Prompt construction
### 4.0 Examples and patterns
1. "Replace [the object in the source video] with [the object in the reference image]. Keep the rest
   of the shot the same." — The Rundown, Genjutsu Object Swap guide [SECONDARY].
2. "Replace one clearly defined object with the object shown in @Image 2, while leaving the performer,
   background, lighting direction, and camera path stable. The swap should track perspective and
   shadows across the shot." — practitioner template reported alongside that guide [SECONDARY].
3. Higgsfield's own edit contract (`first-party/ad-multiplier-prompt-writer.md`, Seedance-2.5-based,
   first-party): "Replace only [target] in @Video1 with [replacement] from [@ImageN]" and "Remove only
   [target] from @Video1 and reconstruct the revealed area consistently with its immediate
   surroundings" [HF].

Patterns:
- one imperative operation per sentence;
- the target identified uniquely;
- the replacement bound to its image tag;
- the explicit keep-list (performer, background, light, camera path);
- a tracking clause for perspective and shadows;
- no scene re-description.

### 4.4 Object Swap template
```text
Replace only <unique target description> in @Video1 with <replacement name> from @Image1<, @Image2 (other views of the same item)>. Keep its exact shape, proportions, colours and markings from the reference images at <real-world size relative to hand/body>; do not take on the original object's shape. It follows the original's exact position, path, orientation, grip and occlusion in every frame, matches the scene's light direction and colour, and casts consistent shadows and reflections. The original <target> must not appear in any frame. Remove <source captions / usernames / watermark>, reconstructing the background behind them. Keep the performer, motion, camera path, framing, lighting and timing of @Video1 unchanged.
```
Example: "Replace only the white ceramic mug held in the man's right hand in @Video1 with the matte
black insulated tumbler from @Image1 and @Image2 (front and side of the same tumbler). Keep its exact
tall cylindrical shape, lid and proportions from the references, about the height of his hand; do not
take on the mug's shape or handle. It follows the mug's exact position, path, tilt and grip in every
frame, matches the warm window light from the left and casts a consistent soft shadow. The mug must
not appear in any frame. Keep the man, his motion, the camera path and the timing of @Video1
unchanged."

### 4.4 Motion Transfer template
```text
Transfer the full-body motion, gesture timing and camera movement of @Video1 to <subject> from @Image1. <Subject> keeps the face, hair, body proportions and complete outfit shown in @Image1<; the scene is the <location> from @Image2 | described scene>. Do not use the person, clothing, props or background of @Video1. Real-time speed; the same cuts and camera path as @Video1.
```

## 5. Failure modes
| Failure | Trigger | Mitigation |
|---|---|---|
| Original object still visible | Fast motion, small target, weak target description [SECONDARY test] | Unique anchor; exclusion sentence; 720p+; shorter clip; else Seedance 2.5 edit |
| Replacement ignores trajectory at contact | Hand interactions [SECONDARY] | Inspect contact frames in QC (`frames --range` at 15 fps); regenerate if broken |
| Geometry deformation | Replacement shape differs a lot from the original [HF] | Regenerate with a reference-to-video model instead of swapping |
| Captions survive | Untargeted text is preserved | Local `clean`, removal clause, or Seedance edit |
| Wrong aspect | Non-9:16 source | Reframe the source first |
| Identity bleed | Motion Transfer copies the driver's look | Explicit "do not use the person/clothing of @Video1" + a strong identity image |

## 6. Features
Two operations; up to 30 references; 480/720/1080p.

## 7. Checklist
- [ ] Source trimmed to 4–30 s and already 9:16.
- [ ] Exactly one video, first in `medias`; images follow in `@ImageN` order.
- [ ] The target uniquely identified; the canonical template image supplied.
- [ ] The size or shape difference is small enough, else choose regeneration.
- [ ] A text-removal plan exists for source overlays (Edit Mode).
- [ ] After download: audio check / `restore-audio`, `conform`, `qc --mode edit`.

## 8. Sources
- [HF] catalog (2026-09-30); `first-party/genjutsu.md` (get_preset_instructions `/genjutsu`, 2026-09-30).
- [HF] https://higgsfield.ai/blog/higgsfield-genjutsu (accessed 2026-09-30)
- [HF] https://higgsfield.ai/genjutsu (accessed 2026-09-30)
- [HF] https://higgsfield.ai/blog/edit-ai-video-without-regenerating (accessed 2026-09-30)
- [SECONDARY] The Rundown, "Swap the product and keep the performance with Higgsfield" — https://app.therundown.ai/guides/swap-the-product-and-keep-the-performance-with-higgsfield (accessed 2026-09-30)

## 9. Open questions
- Whether the source audio is always preserved.
- Whether text-removal clauses are honoured.
- The exact tag syntax Genjutsu parses (`@Image1` vs `@Image 1`).
- Maximum useful number of references per swap.
