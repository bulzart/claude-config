---
guide: seedance-2-0
title: ByteDance Seedance 2.0
provider: ByteDance Seed (Dreamina Seedance 2.0), served by Higgsfield
higgsfield_model_ids: [seedance_2_0]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# ByteDance Seedance 2.0 — model engineering guide

> Scope: ByteDance Seed's Seedance 2.0 joint audio-video model as served by Higgsfield under
> `seedance_2_0` ("Reference-driven video with image/video/audio reference inputs, consistent identity,
> multi-SKU; optional generate_audio for native audio"). On Higgsfield it covers text-to-video,
> first/last-frame generation and multi-reference generation from images, video and audio, with Higgsfield
> Elements, 4–15 s. Editing and extension exist on ByteDance's API but are **not exposed as modes** here.
> Project output format is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** A "unified multimodal audio-video joint generation architecture" accepting text, image, audio and video; up to 9 images, 3 video clips and 3 audio clips; 15-second multi-shot output with native audio; released 2026-02 [OFFICIAL S1, S2]. ByteDance's guide calls it "essentially a multimodal AI director" that splits a prompt into a "spatial layer (what is in the frame)" and a "temporal layer (how things change over time)" [OFFICIAL S3].
- **Best for:** reference-driven shots with a consistent person or product (Higgsfield tags: identity, consistent, product, multi-SKU) [HF S6]; `Shot 1 / Shot 2 / Shot 3` storyboards within 4–15 s; motion or camera transfer from a reference clip; voice timbre from an audio reference; Higgsfield Elements [HF S8].
- **Weaker at:** precise timing ("The model's support for precise timing (such as 0–3 seconds) is unstable") [OFFICIAL S3]; multi-view character sheets (ID drift, twins) [OFFICIAL S3]; >4 referenced people [OFFICIAL S3]; "detail stability, hyper-realism, and dynamic vitality … multi-subject consistency, text rendering accuracy, and complex editing effects", occasional audio distortion [OFFICIAL S2]; multi-speaker lip sync [OFFICIAL S4].
- **Choose this model when** you need ≤15 s with strong identity/product locking from a few references, Elements, or the 2.0 look (2.5 has "significantly different aesthetic style preferences") [OFFICIAL S5].
- **Choose another model when** you need >15 s, timestamp-exact beats, an edit or extension of a supplied clip, more than 9/3/3 references or multi-view sheets — use Seedance 2.5.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"seedance_2_0"`, no `medias` | |
| First frame / first + last frame | roles `start_image` (+ `end_image`) | ratio may be set or follow the image [OFFICIAL S7] |
| Multi-reference (R2V) | `image_references`, `video_references`, `audio_references` | cited as `@Image1`, `@Video1`, `@Audio1` |
| Elements | `<<<element_id>>>` in the prompt | Seedance 2.0 is Elements-capable on Higgsfield [HF S8] |
| Video edit / extension | N/A on Higgsfield (no mode) | available on ModelArk 2.0 [OFFICIAL S3]; use `seedance_2_5` |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `seedance_2_0` | `duration` | number, 4–15 s | 5 | "Duration in seconds (4-15)." Unsupported values snap or clamp [HF S8]. |
| `seedance_2_0` | `resolution` | `480p`, `720p`, `1080p`, `4k` | `720p` | "Output resolution supported by standard mode." Project: `720p` (§2.6). |
| `seedance_2_0` | `mode` | `std` | `std` | "Standard mode is available for this account." Quality tier, not a task selector. |
| `seedance_2_0` | `bitrate_mode` | `standard`, `high` | `standard` | "'high' = higher bitrate output." Higgsfield-specific. |
| `seedance_2_0` | `genre` | `auto`, `action`, `horror`, `comedy`, `noir`, `drama`, `epic` | `auto` | "Cinematic genre hint." Higgsfield-specific, mechanism undocumented — keep `auto` unless the look is wanted and matches the prompt [INFERRED]. |
| `seedance_2_0` | `generate_audio` | bool | `true` | "Generate native audio for the video. Set false for a silent video. Independent of audio_references." |
| `seedance_2_0` | `aspect_ratio` (call-level) | `auto`, `16:9`, `9:16`, `4:3`, `3:4`, `1:1`, `21:9` | not stated | Project: `9:16`. |
| `seedance_2_0` | flags | `supports_unlim: true` | — | `use_unlim:true` only when the user explicitly asks [HF S6, S10] |
| `seedance_2_0` | `seed`, `negative_prompt`, `camera_fixed`, `watermark`, edit/extension selection, `duration:-1` | — | — | **Not exposed on Higgsfield** [HF S6]; ModelArk lists `seed`/`camera_fixed` for 1.x only [OFFICIAL S7]. Approximations: §3.6, §3.10. |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing), `use_unlim` [HF S8].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame | 1 | ModelArk `first_frame` [OFFICIAL S7] |
| `end_image` | last frame | 1, with `start_image` | same ratio as the first frame [OFFICIAL S7] |
| `image_references` | `@Image1…9`: identity, wardrobe, product, scene, style, logo | ≤9 [OFFICIAL S1, S7]; each <30 MB, 300–6000 px, w/h 0.4–2.5 [OFFICIAL S7] | numbered in `medias` order |
| `video_references` | `@Video1…3`: action, camera movement, rhythm, effects, style | ≤3, each 2–15 s, total ≤15 s [OFFICIAL S7] | |
| `audio_references` | `@Audio1…3`: timbre, music, SFX, beat | ≤3, each 2–15 s, total ≤15 s [OFFICIAL S7] | "Audio-only input is not supported; include at least one reference image or video" [OFFICIAL S7] |

Higgsfield states "up to 12 assets in a single generation" [HF S11] versus ByteDance's 9 + 3 + 3 [OFFICIAL S1]; treat 12 as the cap until tested. ModelArk forbids mixing first/last-frame roles with omni references [OFFICIAL S7]; Higgsfield behaviour undocumented. `medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S8].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration** 4–15 s; 24 fps [OFFICIAL S7, S9].
- **Resolution** 480p/720p/1080p (8-bit), 4K (10-bit HEVC on ModelArk) [OFFICIAL S9]; the model card describes 480p/720p native generation [OFFICIAL S4].
- **Aspect ratio:** six fixed output ratios (2.5 added arbitrary ratios) [OFFICIAL S5]; with a first frame, 2.0 accepts a specified ratio and centre-crops the image if it differs [OFFICIAL S7].
- **Audio:** native voice, SFX and music in one pass; ByteDance describes it as dual-channel [OFFICIAL S1], the ModelArk API returns mono [OFFICIAL S7]. `generate_audio:false` for silence.

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight without submitting [HF S8].

**Text-to-video**
```json
{"model":"seedance_2_0","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","resolution":"720p","mode":"std","genre":"auto","generate_audio":true}
```
**First frame (+ last frame)** — exactly-9:16 images
```json
{"model":"seedance_2_0","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**Multi-reference (headshot + full body + product + camera clip + voice)**
```json
{"model":"seedance_2_0","prompt":"<PROMPT citing @Image1 @Image2 @Image3 @Video1 @Audio1>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_3>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID_1>","role":"video_references"},{"value":"<AUDIO_MEDIA_ID_1>","role":"audio_references"}],"duration":12,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**Elements** (Higgsfield injects the Element image and rewrites the token to `@element_name`) [HF S8]
```json
{"model":"seedance_2_0","prompt":"<<<ELEMENT_ID_PERSON>>> lifts <<<ELEMENT_ID_PRODUCT>>> from the table ...","duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```

### 2.5 Parameter gotchas

- No task `mode` for edit/extension; `mode:"std"` is a quality tier [HF S6]. ModelArk 2.0 infers edit/extension from prompt intent when a reference video is present [OFFICIAL S3, S7]; whether an "Edit @Video1…" prompt behaves as an edit through Higgsfield is untested — use `seedance_2_5`.
- `genre` is not a ByteDance parameter [HF S6]; don't let it contradict the prompt's look.
- `generate_audio` is independent of `audio_references` [HF S6]; audio references need an image or video in the same call [OFFICIAL S7].
- Real-face references are restricted on ModelArk's Dreamina Seedance models [OFFICIAL S12]; Higgsfield's treatment is undocumented.
- Keep ratio, duration, resolution and the sound toggle out of the prompt [OFFICIAL S7].
- Elements vs `@ImageN`: numbering of injected Element images relative to attached references is undocumented; use one mechanism per call until tested [INFERRED].
- Prompt length: ≤1,000 English words ("Lengthy text will lead to scattered information") [OFFICIAL S7]; Dreamina suggests 30–100 words for simple clips [OFFICIAL S13].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| operation | params to send | expected output | post-processing |
|---|---|---|---|
| t2v / multi-reference / Elements | `aspect_ratio:"9:16"`, `resolution:"720p"`, `mode:"std"` | 720×1280 (official 2.0 grid) [OFFICIAL S7] | none; verify with ffprobe |
| first / last frame | `aspect_ratio:"9:16"`, `resolution:"720p"`, exactly-9:16 image(s) (720×1280 or 1080×1920) | 720×1280; a non-9:16 image would be centre-cropped by the model [OFFICIAL S7] | conform images to 9:16 **before** upload (`atg.py conform`: scale-to-fill + minimal crop) so framing is chosen deliberately |

Never stretch. `1080p`/`4k` are not used by this project.

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Basic formulas** [OFFICIAL S3]: image reference "Reference `<Subject_N>` in `<Image_N>` to generate…"; video reference "Reference `<Action/Camera_movement/Style/Sound_effect>` in `<Video_N>` to generate…"; audio reference "Reference the timbre in `<Audio_N>` to generate…".
- **Advanced formula:** "precise subject + action details + scene/environment + lighting & color tone + camera movement + visual style + image quality + constraints" — "first lock in 'who' is 'doing what', then explain 'where' and 'what atmosphere', then tell the model 'how to shoot', and finally tighten the result with style, image quality, and constraints." [OFFICIAL S3]
- **Complex videos:** "a timeline-based storyboard … who + where + doing what + how the camera moves"; per shot: camera movement or transition → subject actions and expressions → position/spatial changes → audio [OFFICIAL S3].
- **Length:** simple shots 30–100 words [OFFICIAL S13]; storyboards as needed, ≤1,000 words [OFFICIAL S7]. "Do not directly use the complete script as the prompt" [OFFICIAL S3].
- **Language:** English; also Spanish, Indonesian, Portuguese and Japanese prompts [OFFICIAL S7]. Dialogue in one language, no Chinese–English mixing except proper nouns [OFFICIAL S3].

### 3.2 Subject and identity

- "Define `[Core_Subject_Features]` in `<Image/Video_N>` as `<Subject_N>`" with "2–3 clear and stable static features" [OFFICIAL S3]; bind multi-asset subjects "Define `[…]` in Image 1 and `[…]` in Image 2 as `<Subject_N>`" [OFFICIAL S3].
- "Each time a subject is involved, it must be explicitly referred to": `Name@Image 1` on every mention, or the defined label every time [OFFICIAL S3]. Asset IDs are never names [OFFICIAL S3]. "Express spatial relationships through reference images first" [OFFICIAL S3].

### 3.3 Action, motion and physical interaction

- "Body-movement refinement + degree quantification" — body part plus range, speed, force [OFFICIAL S3].
- "Prioritize slow, gentle, continuous small movements … avoid high-burst, large-dynamic actions such as sprinting, big jumps, and violent rolls" [OFFICIAL S3]; "Supplement transitions between actions" [OFFICIAL S3].
- Emotions as visible behaviour (official table: nervousness → "frequently checking the watch, fingers constantly tapping the tabletop…") [OFFICIAL S3]. Motion plausibility in edge cases and minor deformation are acknowledged gaps [OFFICIAL S4].

### 3.4 Environment, lighting and style

- Quality words "HD, rich details, cinematic texture, natural colors, soft lighting"; style words such as "retro film" [OFFICIAL S3].
- Style drift: realistic references pull animated prompts to live action — state the style ("2D Japanese anime style") or pre-convert references [OFFICIAL S3].
- Scene images: "use @Image 2 as the dormitory scene style reference" [OFFICIAL S3]; exclude people in scene images [INFERRED].

### 3.5 Chronology, timing and multi-shot structure

- `Shot 1 / Shot 2 / Shot 3` "in the order events occur … Do not impose strict limits on the duration of each segment" [OFFICIAL S3]; numeric timestamps are unstable on 2.0 and "forcibly limiting duration may lead to abnormal generation results" [OFFICIAL S3]. Use relative words ("then", "immediately", "after a brief pause") [INFERRED].
- One main event per shot with a clear ending; end on a held composition ("freezes on a wide shot") [OFFICIAL S3]. Native multi-shot is part of the Seedance line since 1.0 [OFFICIAL S14].

### 3.6 Camera language and dedicated camera / motion controls

- "The model has a strong understanding of camera movement terms" — "medium shot, close-up, wide shot, slow push-in, smooth lateral tracking, fixed shot" [OFFICIAL S3].
- "Try to specify only 1 type of camera movement in a single shot. Do not require push, pull, pan, and move at the same time, as this will increase image instability." [OFFICIAL S3]
- Movement formula from the 1.5 pro guide: "Starting frame composition description + Shot movement + Shot movement amplitude + Ending frame composition description" [OFFICIAL S15].
- No camera parameter; lock in words ("fixed camera position; the camera never moves") [INFERRED]; exact moves via a camera-reference clip ("refer to the camera movement in @Video 1") [OFFICIAL S3].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- Recommended: "4-5 assets in total: 1-2 character images (facial close-up / full body) + 1 scene image + 1 camera movement video + 1 audio clip"; "It is not recommended to use the full asset limit" (style conflicts, blurry identification) [OFFICIAL S3].
- "The more an asset requires precise reference, the earlier it should be placed in the prompt" [OFFICIAL S3]. Video references carry "subject, camera movement, action performance, and overall style" [OFFICIAL S16] — name the dimension to take and exclude identity/clothing/location when only motion is wanted [INFERRED].
- Audio: timbre, melody, dialogue content; add voice descriptors ("low, thick, warm … middle-aged male voice of @Audio 1") [OFFICIAL S3]. Effects are better defined by a reference clip than by text [OFFICIAL S3].
- Text inside references propagates — clean them first (§3.11).

### 3.8 Start and end frames

- `start_image`/`end_image` give first/last-frame generation; the ratio may be set or follow the image [OFFICIAL S7]. Supply both frames at exactly 9:16.
- Describe the change between frames (who moves, what changes state); restate the end composition in words for strict endings [INFERRED]. In reference mode, frames can be named in prose ("Image 1 is the first frame") at the cost of exact match [OFFICIAL S7].

### 3.9 Audio, dialogue and sound (if supported)

- Symbols: music `（）`, sound effects `<>`, dialogue `{}`, subtitles `【】`; "If the dialogue is in a less common language (neither Chinese nor English), the language must be marked, such as: says in Japanese {こんにちは}" [OFFICIAL S3].
- Voice from audio: "'Character' says: 'lines', voice timbre references 'Audio n'" plus timbre words [OFFICIAL S3]; keep lines' tone close to the reference [OFFICIAL S3].
- Narration can end with a click; regenerate or fade out [OFFICIAL S3]. Music policy: "No BGM; generate only environmental sounds and action sounds" (2.5 wording, compatible) [OFFICIAL S5; INFERRED for 2.0].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field [HF S6; OFFICIAL S7]. Official constraint words at the end: "keep it subtitle-free", "avoid generating any text or subtitles", "do not generate a logo", "do not generate a watermark"; stability line "The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker" [OFFICIAL S3].
- Twins: "Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited. Do not generate duplicate avatars or a twin effect. Keep only a single corresponding character in the same frame" [OFFICIAL S3].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

**(a) Reliability.** 2.0 "supports generating common text" (slogans, subtitles, speech bubbles) with prompt control of "color, style, appearance method, appearance timing, and appearance position"; "prioritize common characters and avoid rare characters and special symbols" [OFFICIAL S3]. ByteDance lists "text rendering accuracy" as an open issue [OFFICIAL S2]. Verdict: short scene text may render, exactness is not guaranteed — default to post [INFERRED].

**(b) Clean plate.** Official FAQ: "it is not possible to directly avoid generating subtitles 100%"; add "Keep it subtitle-free" and "Avoid generating any text or subtitles"; remove non-essential text from reference images/videos first; landscape produces spurious subtitles "significantly" less often than portrait (not usable under the fixed 9:16 format — QA every frame instead); foreign logos/watermarks: "Do not generate watermarks" and "Do not generate Logos" [OFFICIAL S3]. Never write `【】` or quoted words other than dialogue in a clean plate; describe signs, packaging and screens as blank [INFERRED].

**(c) Intentional in-frame text (scene text only).** Official slogan template: "[Text Content] + [Timing] + [Positioning] + [Entrance/Appearance Style], [Visual Attributes (Color, Font Style)]", e.g. "the text "Bite", "Laugh", and "Seedance" in order appears in the center of the screen"; strict presentation → supply the mark as a reference image ("The logo from image 5 remains in the bottom right corner throughout") [OFFICIAL S3]. Subtitles would use `【】` or "Display subtitles at the bottom-center…" [OFFICIAL S3] — this project adds captions in post instead.

**(d) Removing source text.** N/A on Higgsfield — `seedance_2_0` has no edit mode [HF S6]. Remove source text with `seedance_2_5` `video_edit` or `kling_video_edit`, then use the clean clip as a reference.

### 3.12 Character / identity consistency

- ID-drift fix: a "close-up face image containing only the character's head (headshot … no expression is best)" plus a full-body photo; "`<Subject 1>` facial features reference image 1 (headshot), makeup and styling reference image 2 (full-body photo)"; precise assets first [OFFICIAL S3].
- "Using multi-view character images is not recommended … the model may easily identify them as multiple different subjects" [OFFICIAL S3]. Label each character with its image every time ("Zhang San (corresponding to image 1) …") [OFFICIAL S3]. >4 people: group images of ≤4 first [OFFICIAL S3].
- Elements: one Element per approved person, cited at every mention [HF S8; INFERRED usage]. Approved references replace source people: source clips supply motion only ("do not use the people or clothing in @Video1") [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Official product patterns: several views as separate images of one product ("Use the cameras featured in Image 1, Image 2 and Image 3…") and a single-reference showcase with a controlled hand ("a hand naturally enters the frame off-screen, gently grips the thermos body and picks it up") [OFFICIAL S3].
- Define the product with 2–3 static features and reuse the label; state rigidity, proportions, part counts, scale versus the hand, grip and orientation; slow rotations [INFERRED]. Multi-SKU: one line per product with count and position [INFERRED]. Label text accuracy is weaker than 2.5 [OFFICIAL S2].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale / orientation / contact:** size relative to the hand or body, the gripping hand, contact point and facing ("held upright in the left hand, label toward the camera, about forearm length") [INFERRED]; official examples specify the entering hand and grip (thermos) [OFFICIAL S3].
- **Scene light:** name key-light direction and colour temperature and require the product/person to take it ("warm yellow sunlight spills into the hallway from the window" is the official scene-light style) [OFFICIAL S3]; add shadow and reflection behaviour for inserted objects; exclude studio lighting of product photos [INFERRED].
- **Persistent states:** end each shot with a held state and restate it at the next shot's start (object positions, open/closed, liquid level, which hand) [INFERRED]; official shots end on frozen compositions [OFFICIAL S3].
- **Known failures:** multi-subject consistency and complex interactions [OFFICIAL S2]; twins with multi-view sheets [OFFICIAL S3].
- **Across clips:** ByteDance recommends extension for continuous dialogue scenes and stitching for turns [OFFICIAL S3] — extension is only on `seedance_2_5` here, and mixing 2.0/2.5 changes the look [OFFICIAL S5]. Chain clips by extracting the last frame locally and using it as the next `start_image`; keep references and order identical; at a jumpy join, ByteDance: "trim 6 frames from the end of the previous video segment… trim 1 frame from the beginning of the following video segment… Repeat… for all stitching points", and better still "end the video … at the moment of a transition cut" [OFFICIAL S3]. "Multiple continuations will compound the degradation, and mottled color blocks are especially likely to appear in character face regions": keep chains short [OFFICIAL S3]. No seed [HF S6].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

**E1 — shot sequencing** (BytePlus 2.0 prompt guide, S3): "Shot 1: Side shot of a street alley; the man slowly starts running, with a sense of rapid breathing. Shot 2: The man knocks over a fruit stand; the camera shakes quickly and gives a close-up of the man's frightened face. Shot 3: The man climbs over a low wall and disappears; the camera slowly pulls back and freezes on the empty street."

**E2 — subject definition** (S3): "Define the tall man in Video 1 as police officer, and define the other short man as thief. The scene is set in a crowded daytime market, with bright sunlight, many fruit stalls, and dense pedestrian traffic […] Thief runs forward in panic through the crowded market, while police officer follows closely behind at full speed. […] A handheld camera rapidly tracks forward, with slight realistic camera shake, creating a tense chase atmosphere."

**E3 — multi-reference short drama** (S3): "Use the girl in @Image 1 as the main character, use @Image 2 as the dormitory scene style reference, and refer to the camera movement in @Video 1. Shot 1: At dusk, girl @Image 1 walks briskly to the dormitory entrance @Image 2. The camera follows steadily in a medium shot. Warm yellow sunlight spills into the hallway from the window. […] The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker. The ambient sound blends naturally with @Audio 1."

**E4 — product views** (S3): "Use the cameras featured in Image 1, Image 2 and Image 3. Replace the original background with a white one, and place the cameras on a white table. The camera first focuses on the cameras in close-up, then slowly rotates 360° with the cameras as the main subject, clearly displaying the front, sides and back of each camera."

**E5 — product handling** (S3): "In a warm-toned home setting, present the thermos shown in the reference image in a medium shot. Then smoothly push the camera into a close-up of the thermos. Next, a hand naturally enters the frame off-screen, gently grips the thermos body and picks it up. The camera follows the slight rotating motion of the hand to showcase the thermos."

**E6 — constraint line** (S3): "Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited. Do not generate duplicate avatars or a twin effect. Keep only a single corresponding character in the same frame, and do not reproduce repeated copies of characters."

Patterns these teach [derived from E1–E6]:
- **Order:** reference roles first ("Use … as …, refer to … in @Video 1"), then shots, then one closing line for style, stability and audio (E3).
- **Sentence style:** short clauses joined by semicolons; subject action, then camera reaction in the same shot line (E1).
- **Time:** `Shot N:` only — no numeric timestamps (E1, E3).
- **Subject vs camera motion:** separated but adjacent ("the man knocks over a fruit stand; the camera shakes quickly…") (E1).
- **Camera vocabulary:** plain moves (follows steadily, pulls back and freezes, rotates 360°, push into a close-up) (E1, E3, E4, E5).
- **References:** `@Image 1` attached to the subject at each mention ("girl @Image 1"), or a defined label ("police officer") (E2, E3).
- **Length:** 40–120 words; shots of 1–3 sentences.
- **Exclusions:** positive stability sentence plus a single targeted constraint sentence (E3, E6).
- **Products:** views as separate images; the hand's entry, grip and rotation spelled out (E4, E5).

### 4.1 Text-to-video

```text
Shot 1: <camera movement or "fixed camera position">, <shot size>. <Subject with 2–3 features> <action with body part and speed> in <location, time, light direction>. <sound>.
Shot 2: Cut to <shot size>; <subject> <next action>; <spatial change>. <sound>.
Shot 3: <camera>; <final action>; the camera <settles / freezes> on <final composition>.
<Style>, <lighting and colour>, HD, rich details, real-time speed. The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo; do not generate a watermark.
```
Worked example (10 s):
```text
Shot 1: Fixed camera position, wide shot. A person in a yellow raincoat walks slowly along a wet harbour pier at dawn, pulling a small wheeled cart with a covered crate; cool light from the left. <gulls in the distance> <cart wheels on wet planks>
Shot 2: Cut to a medium shot from the side. The person stops at the end of the pier, lifts the cover off the crate with both hands and folds it over the cart handle.
Shot 3: Slow push-in to a close-up. The person looks out at the water and exhales; the camera freezes on the calm face with the pale sky behind.
Documentary realism, cool morning light, soft colours, HD, rich details, real-time speed. Movements are natural and smooth, with no stutter or flicker. No BGM; generate only environmental sounds and action sounds. Keep it subtitle-free; avoid generating any text or subtitles; the crate is unmarked; do not generate a logo or watermark.
```

### 4.2 Start frame (and end frame) to video

```text
The video starts from the provided first frame<, and ends on the provided last frame>. <Subject> <continuous action from the first state to the final state>; <which hand, what is held, where it ends>. <Camera: fixed position | one move>. <Sound>. Maintain <identity, object count, layout, light direction>. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo or watermark.
```
Worked example (6 s):
```text
The video starts from the provided first frame. The grey cat on the windowsill stretches its front legs, stands up slowly, turns toward the room and hops down onto the carpet, then sits and looks at the camera. Fixed camera position, eye-level medium shot. <soft thump on the carpet>, quiet room tone. The same single grey cat throughout; the window and plant stay where they are; afternoon light keeps coming from the window on the left. Keep it subtitle-free; avoid generating any text or subtitles.
```

### 4.3 Reference-to-video

```text
Define the <2–3 features> person in @Image1 as <Name> (facial features, headshot) and use @Image2 for <Name>'s hairstyle and clothing (full body). Use the <product> in @Image3 as the only product; use only its shape, proportions, colours and materials, not its background or lighting. Refer to the camera movement in @Video1; do not use its people, location or text. <Name>'s voice timbre references @Audio1.
Shot 1: <camera>; <Name> <action with the product: hand, grip, orientation>; <position>; lit by <scene light>. <sound>.
Shot 2: <camera>; <Name> says in <language>: {<exact words>}; <reaction>.
Shot 3: <camera>; <final state; product placement and orientation>; the frame holds.
<Style, light, quality>, real-time speed. <Name>'s face remains stable without deformation. Exactly one <product>; it keeps its proportions. Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo; do not generate a watermark.
```
Worked example (8 s):
```text
Define the person with short black hair and round glasses in @Image1 as the host (facial features, headshot) and use @Image2 for the host's green overshirt and build (full body). Use the handheld blender in @Image3 as the only product; use only its shape, proportions, colours and materials, not its background or lighting. Refer to the slow push-in in @Video1; do not use its people or location.
Shot 1: Fixed camera position, medium shot in a bright kitchen with daylight from the right. The host picks up the blender with the right hand and turns it so the control button faces the camera.
Shot 2: Slow push-in to a medium close-up. The host presses the button once; the blender hums; the host says in English: {Ten seconds, done.}
Shot 3: Fixed camera. The host sets the blender upright on the counter to the left of a glass and steps back; the frame holds.
Clean daylight, natural colours, HD, rich details, real-time speed. The host's face remains stable without deformation. Exactly one blender; it keeps its proportions and single button. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo; do not generate a watermark.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield as a mode: `seedance_2_0` exposes no edit or extension task [HF S6] — use `seedance_2_5` or `kling_video_edit`. Motion transfer is approximated in §4.3 with `@Video1` as the action or camera reference ("refer to the overall camera movement and action rhythm in @Video 1") [OFFICIAL S3]. ByteDance's 2.0 edit/extension patterns, for reference only: "Add: At [timing] and [location] of [Video N], add […]" · "Remove […] from [Video N], keeping the rest of the video content unchanged" · "Replace […] in [Video N] with […]" · "Extend `<Video_N>` forward/backward to generate…" — "Do not use 'reference `<Video_N>`'" [OFFICIAL S3]; untested through Higgsfield's `seedance_2_0`.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Identity drift / face swap mid-clip | mixed reference sheet; small face area | headshot + full body, headshot first [OFFICIAL S3] |
| Twins / duplicated characters or objects | multi-view sheets; undefined subjects; pasted script | single-person images, labels at every mention, no-twin sentence, counts [OFFICIAL S3] |
| Wrong head count | >4 referenced people | group stills of ≤4 first [OFFICIAL S3] |
| Timing ignored / abnormal pacing | numeric timestamps | `Shot N`, natural pacing [OFFICIAL S3] |
| Jitter / instability | several camera moves in one shot | one move per shot [OFFICIAL S3] |
| **Dead space** | one sparse shot stretched over 15 s | 2–3 shots with one event each; shorter duration [INFERRED] |
| **Arbitrary slow motion / sudden speed changes** | vague "cinematic" wording; bursts | "real-time speed"; slow continuous actions with transitions [OFFICIAL S3; INFERRED] |
| **Unmotivated cuts** | long shot lists for a short clip | fewer shots; "fixed camera position" when continuous [OFFICIAL S3; INFERRED] |
| **Morphing** | fast rotations; single weak product view | multiple product views; slow rotation [OFFICIAL S3; INFERRED] |
| **Clothing changes** | wardrobe not tied to a reference | full-body reference + label reused per shot [OFFICIAL S3] |
| Unwanted subtitles / text | portrait frame; text in references | subtitle constraints, clean references, QA [OFFICIAL S3] |
| Foreign logo / watermark | references from other platforms | "Do not generate watermarks / Logos" [OFFICIAL S3] |
| Style drift toward live action | realistic references + stylised prompt | explicit style; pre-convert references [OFFICIAL S3] |
| Effect behaves wrongly | effect described only in text | effect reference clip [OFFICIAL S3] |
| Voice ≠ reference | vague timbre | describe timbre; keep lines' tone close [OFFICIAL S3] |
| Asset overload | all 9/3/3 slots used | 4–5 assets [OFFICIAL S3] |
| Element/image numbering confusion | Elements + `@ImageN` | one mechanism per call [INFERRED] |

## 6. Model-specific features and controls

- Multi-reference up to 9/3/3 with timbre transfer; `Shot N` multi-shot storyboards; common-text generation when requested [OFFICIAL S1, S3].
- `genre` hint and `bitrate_mode` (Higgsfield-specific); `4k` exists but is outside this project's format [HF S6].
- Higgsfield Elements (`<<<element_id>>>`) [HF S8]; unlim-eligible on explicit request [HF S6, S10].
- Not on Higgsfield: edit/extension selection, seed, negative prompt, camera_fixed, watermark toggle [HF S6].

## 7. Model-specific pre-generation checklist

- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`, `mode:"std"`; start/end frames exactly 9:16; duration 4–15.
- [ ] `Shot 1/2/3` structure, no numeric timestamps; ≤1,000 words; no parameters in the text.
- [ ] 4–5 references where possible; ≤9 images, ≤3 videos (≤15 s), ≤3 audio (≤15 s, never audio-only); Higgsfield 12-asset cap.
- [ ] Each subject defined once (2–3 static features) and referenced by the same label or `Name@Image N`; headshot + full body; no multi-view sheets.
- [ ] One camera move per shot; slow continuous actions with transitions; "real-time speed".
- [ ] Integration: size, hand/grip, orientation, scene light and shadow for products; states restated at each shot start.
- [ ] Clean plate: subtitle/text/logo/watermark constraint line; references text-free; no `【】`; captions planned for post.
- [ ] Elements used at every mention or not at all; `genre:"auto"` unless intentional.
- [ ] `get_cost:true` preflight done.

## 8. Sources

- S1 [OFFICIAL] ByteDance Seed — "Official Launch of Seedance 2.0" (2026-02-12) — https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0 (accessed 2026-09-30)
- S2 [OFFICIAL] Same page — acknowledged limitations (detail stability, audio distortion, multi-subject consistency, text rendering accuracy, complex editing effects) (accessed 2026-09-30)
- S3 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.0 series prompt guide (formulas, subject definition, shot sequencing, actions, camera, constraint words, text generation, asset strategy, symbols, FAQ, examples E1–E6) — https://docs.byteplus.com/en/docs/ModelArk/2222480 (accessed 2026-09-30)
- S4 [OFFICIAL] Team Seedance — "Seedance 2.0: Advancing Video Generation for World Complexity", arXiv:2604.14148 (4–15 s, 480p/720p; evaluation weaknesses incl. multi-speaker lip sync per local notes of the PDF) — https://arxiv.org/abs/2604.14148 (accessed 2026-09-30; PDF findings via `analyze-stack/seedance/SEEDANCE-SPEC.md`, 2026-09-16)
- S5 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.5 prompt guide ("Differences from Seedance 2.0", "Aesthetic style drift between versions", no-BGM wording) — https://docs.byteplus.com/en/docs/ModelArk/2607689 (accessed 2026-09-30)
- S6 [HF] Higgsfield live catalog snapshot — `higgsfield/catalog-snapshot-2026-09-30.json` (`seedance_2_0`)
- S7 [OFFICIAL] BytePlus ModelArk — Create a video generation task (API reference: limits, roles, ratio rules incl. centre-crop of mismatched first frames, pixel table 9:16 720p = 720×1280, audio-only rule, mono audio, prompt length, seed/camera_fixed scope) — https://docs.byteplus.com/en/docs/ModelArk/1520757 (accessed 2026-09-30)
- S8 [HF] Higgsfield MCP tool contract (`generate_video` call shape, `get_cost`, duration snapping, media intake, `jobs_wait`, Elements `<<<element_id>>>` for Seedance 2.0) as verified for /analyze-then-generate, 2026-09-30
- S9 [OFFICIAL] BytePlus ModelArk — Model list (2.0: 480p/720p/1080p 8-bit, 4K 10-bit, 24 fps, 4–15 s) — https://docs.byteplus.com/en/docs/ModelArk/1330310 (accessed 2026-09-30)
- S10 [HF] Higgsfield Ad Multiplier workflow v1.4, "Unlimited generations (use_unlim)" — `higgsfield/first-party/ad-multiplier-recipe.md` (retrieved 2026-09-30)
- S11 [HF] Higgsfield — Seedance 2.0 page (9 images, 3 videos ≤15 s, 3 audio ≤15 s, "up to 12 assets") — https://higgsfield.ai/seedance/2.0 (accessed 2026-09-30)
- S12 [OFFICIAL] BytePlus ModelArk — Create portrait videos with Dreamina Seedance models — https://docs.byteplus.com/en/docs/ModelArk/2608626 (via local notes 2026-09-16; not re-fetched)
- S13 [OFFICIAL] Dreamina — "18 Powerful Seedance 2.0 Prompts" (30–100 words) — https://dreamina.capcut.com/resource/seedance-2-0-prompt (via local notes 2026-09-16; not re-fetched)
- S14 [OFFICIAL] ByteDance Seed — Seedance 1.0 technical report, arXiv:2506.09113 ("natively supporting multi-shot generation") — https://arxiv.org/abs/2506.09113 (accessed 2026-09-30)
- S15 [OFFICIAL] BytePlus ModelArk — Seedance 1.5 pro prompt guide (camera-movement formula) — https://docs.byteplus.com/en/docs/ModelArk/2168087 (accessed 2026-09-30)
- S16 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.0 series tutorial (video references carry "subject, camera movement, action performance, and overall style") — https://docs.byteplus.com/en/docs/ModelArk/2291680 (via local notes 2026-09-16; not re-fetched)

## 9. Open questions / unverified behaviour

- What `genre` changes and whether it overrides prompt style.
- Whether an edit/extension-intent prompt with `video_references` triggers ByteDance's 2.0 edit/extension subtasks through Higgsfield.
- Actual Higgsfield reference cap (12 vs 9 + 3 + 3) and whether `start_image` can be mixed with `*_references`.
- Numbering of Element images relative to `@ImageN` in the same call.
- Whether Higgsfield returns exactly 720×1280 for `9:16` + `720p` (official grid says yes) and how a non-9:16 start frame is handled there.
- Real-face reference handling on Higgsfield for this id; spurious-subtitle rate at 9:16.
