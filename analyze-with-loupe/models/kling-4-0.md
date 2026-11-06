---
guide: kling-4-0
title: Kuaishou Kling 4.0
provider: Kuaishou — Kling AI, served by Higgsfield
higgsfield_model_ids: [kling4_0]
guide_version: 1.0
last_verified: 2026-11-06
catalog_snapshot: live models_explore get kling4_0, 2026-11-06 (the id is newer than higgsfield/catalog-snapshot-2026-09-30.json)
documentation_depth: high
---

# Kuaishou Kling 4.0 — model engineering guide

> Scope: Kling 4.0 as served by Higgsfield under the single id `kling4_0` ("Generate video from text, ordered keyframes,
> references, or edit an input video"). One id, four modes chosen by the `mode` parameter: `text-to-video`,
> `image-to-video` (start / end frame), `reference-to-video` (Kling's "Omni Reference": image and video references and
> Kling Elements) and `video-edit`. Kling 4.0 Flash (3–20 s, 720p) is not a separate id on Higgsfield as of 2026-11-06,
> and Kling 3.0 / 3.0 Omni Edit have their own guides. The project output is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8. Nothing in this guide has been
> verified by a generation of this library yet (2026-11-06): every behaviour on Higgsfield beyond the live parameters is
> an expectation until the first takes are measured (§9).

## 1. At a glance

- **Positioning.** "Kling 4.0 is a next-generation native multimodal AI model for video creation. It delivers more stable complex motion, stronger consistency across diverse references, and more coherent, precise, and controllable storytelling." [OFFICIAL S1, user guide dated 2026-11-04]. Headline specs: 3–30 s in one generation, "Multi-shot is enabled by default", up to 10 keyframes, Omni Reference with up to 15 assets (10 images, 5 videos ≤30 s total, 7 elements, 3 voice profiles), two-channel stereo audio, nine speech languages with dialects and accents, "clear and stable generation of multilingual text, emojis, and logos", prompts "up to 8,000 tokens" [OFFICIAL S1]. On Higgsfield since 2026-10-20 [HF S4].
- **Best for:** one-pass takes up to 30 s, long continuous shots or auto-cut multi-shot stories; fast and complex motion ("high-speed movement, continuous action, tracking shots, or orbit shots, footage stays stable and seamless") [OFFICIAL S1]; casting people, products and scenes from up to 10 reference images; borrowing a reference video's camera path, action timing or pacing; "Creative Recreation" of a proven video with your own product or character; instruction edits of a supplied clip that keep "the rest of the scene stable"; dialogue with lip sync in nine languages [OFFICIAL S1].
- **Weaker at / watch:** audio is always generated, with no switch [OFFICIAL S1; HF S2]; the model "may add" subtitles and background music by default [OFFICIAL S1]; shots are split automatically by default, so a single take must be asked for [OFFICIAL S1; INFERRED]; no negative-prompt field [HF S2; SECONDARY S6]; voice profiles, middle keyframes, 4K and HDR are not reachable through the Higgsfield roles and parameters [HF S2]; frames and references cannot be combined in one task [OFFICIAL S1]; no independent failure testing was found for a model this new [INFERRED gap].
- **Choose this model when** a take must run 15–30 s in one generation, when several references (people, product, scene, a camera or action video) must work together, when a reference video is recreated with a swapped product or character, or when a supplied clip needs a targeted edit.
- **Choose another model when** the output must be silent with no post step, when a voice or music file must drive the result (no audio role here), or when a pixel-exact start frame and reference images are both needed in one call.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `mode:"text-to-video"`, no `medias` | 3–30 s; the model expands a short prompt [OFFICIAL S1] |
| Start frame to video | `mode:"image-to-video"`, `start_image` | aspect follows the first keyframe [OFFICIAL S1] |
| Start + end frame | `image-to-video`, `start_image` + `end_image` | "Showing transformation processes, craftsmanship, and before-and-after comparisons" [OFFICIAL S1] |
| End frame only | `end_image` alone | supported by Kling ("Use @Image1 as the last frame") [OFFICIAL S1]; unverified on Higgsfield (§9) |
| Middle keyframes (Kling: up to 10) | no media role for them on Higgsfield | the catalog says "ordered keyframes" and tags `keyframes`, but lists only `start_image` / `end_image` [HF S2] (§9) |
| Reference-to-video (Omni Reference) | `mode:"reference-to-video"`, `image_references` (≤10), `video_references` (≤5, ≤30 s total), `kling_element_ids` (≤7) | cite as `@Image1`, `@Video1`, `@Element1` [OFFICIAL S1]; Higgsfield numbering by `medias` order [INFERRED] |
| Creative Recreation (product / character swap in a reference video) | `reference-to-video`, the source in `video_references` + the new item in `image_references` | "Replace the element in @Video1 with @Image1. Keep everything else unchanged." [OFFICIAL S1]; mode choice [INFERRED] |
| Action / camera transfer | `reference-to-video` with `video_references` | "Reference the fighting moves and attack timing in @Video1" [OFFICIAL S1]; no separate motion-control mode |
| Video edit | `mode:"video-edit"`, `video_references` (primary first) + optional `image_references` / elements | the prompt must say "Edit @Video1" [OFFICIAL S1] |
| Voice profile reference | N/A on Higgsfield (no audio role) [HF S2] | Kling: up to 3 voice profiles [OFFICIAL S1] |
| Video extension | N/A | Kling: "Extend videos multiple times, up to 2 minutes" is "(Coming soon)" [OFFICIAL S1] |
| Multi-shot | on by default; shots written in the prompt | no switch or per-shot fields on Higgsfield [HF S2] |

Higgsfield also runs Kling 4.0 behind `hf_mult_replace_object_flash` ("Genjutsu Lite", "Replace objects in a source video using reference images (Kling 4.0)") [HF S2]; that id has its own parameters and is not covered here.

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling4_0` | `mode` | `text-to-video`, `image-to-video`, `reference-to-video`, `video-edit` | `text-to-video` | "Generation mode." [HF S2]. Send it on every call; whether the server infers it from `medias` is unknown (§2.5, §9). `image-to-video` corresponds to Kling's Keyframes entry and `reference-to-video` to its Omni Reference entry [INFERRED from OFFICIAL S1 and HF S2]. |
| `kling4_0` | `resolution` | `720p`, `1080p` | **`1080p`** | "Output resolution." [HF S2]. Project: always `720p` (§2.6); never omit it. Kling's 4K and 10-bit HDR ("coming soon") are not offered here [OFFICIAL S1; HF S2]. |
| `kling4_0` | `duration` | integer 3–30 | 10 | "Duration in whole seconds (3-30). Whole number." [HF S2]; Kling: "adjustable in 1-second increments; default: 10 seconds" [OFFICIAL S1]. Unsupported values are snapped or clamped [HF S3]. |
| `kling4_0` | `kling_element_ids` | string array, at most 7 | — | "Accessible, ready Kling element IDs or reference UUIDs (up to seven)." [HF S2]; Kling: "Up to 7 elements in total, including up to 3 video elements" [OFFICIAL S1]. How the prompt cites them is undocumented (§3.7, §9). |
| `kling4_0` | `aspect_ratio` (call-level) | `21:9`, `16:9`, `9:16`, `1:1`, `auto` | not stated | Kling's Omni default is Auto [OFFICIAL S1]. Project: always `9:16`, never `auto`. |
| `kling4_0` | audio | — | — | No audio parameter is listed [HF S2]. Kling: "Audio-visual synchronization and Smart Storyboard are enabled by default and have no separate toggles." [OFFICIAL S1]; an API aggregator reports that `enable_audio` is not accepted for 4.0 [SECONDARY S6]. |
| `kling4_0` | not exposed | `negative_prompt`, `cfg_scale`, `seed`, a multi-shot switch or per-shot prompt/duration fields, voice profiles, middle keyframes, `keep_original_sound`, 4K, HDR | — | Not in the live answer [HF S2]. An aggregator reports that `negative_prompt` and `cfg_scale` do not apply to Kling 4.0 [SECONDARY S6]; per-shot fields and `keep_original_sound` exist on third-party APIs only [SECONDARY S6, S7]. |
| `kling4_0` | flags | unlim | — | `unlim.available: false` for this account on 2026-11-06 [HF S2]. |

Call-level keys: `model`, `prompt`, `mode` and the other model parameters, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing), `use_unlim` [HF S3].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | the first frame (Kling's Keyframes entry keeps "pixel-level consistency in keyframe images") | 1; image ≤30 MB, aspect 2:5–5:2 [OFFICIAL S1] | "After uploading images, the aspect ratio follows the first keyframe." [OFFICIAL S1] — supply exactly 9:16 |
| `end_image` | the last frame | 1 | Kling supports first + last and last only [OFFICIAL S1]; last only on Higgsfield unverified |
| `image_references` | characters, products, scenes, composition, storyboard, style | ≤10; ≤30 MB each; aspect 2:5–5:2 [OFFICIAL S1] | "Assets are automatically numbered in upload order, such as @Image1, @Image2" [OFFICIAL S1]; on Higgsfield the N-th `image_references` entry is expected to be `@ImageN` [INFERRED, the convention of `AWL/higgsfield/higgsfield-mcp.md` §5] |
| `video_references` | in `reference-to-video`: action, camera path, pacing, composition, or the video recreated; in `video-edit`: the clip(s) to edit, the primary first | ≤5 clips; 3–30 s each; ≤30 s total; ≤300 MB each; aspect 2:5–5:2 [OFFICIAL S1] | "Reference videos, videos for editing, and video elements share the same video quota: up to 5 clips and a maximum combined duration of 30 seconds." [OFFICIAL S1] |
| `kling_element_ids` (a parameter, not a media role) | reusable characters and objects | ≤7, of them ≤3 video elements; a video element's source footage "must be 3–8 seconds long" [OFFICIAL S1] | elements count toward the 15-asset total [OFFICIAL S1]; fal describes an element as a front view plus extra angles, or a video [SECONDARY S5] |

- **Totals:** "Up to 15 reference assets in total across images, videos, voice profiles, and elements" [OFFICIAL S1].
- **Voice profiles:** Kling accepts up to 3 per task, made from 5–30 s of audio [OFFICIAL S1]. Higgsfield has no audio role for this id [HF S2], so voices are described in words (§3.9).
- **Frames vs references:** "The Keyframes entry does not support uploading reference assets." and "The capabilities of the two entry points cannot be combined within a single generation task." [OFFICIAL S1]. Never send `start_image` / `end_image` together with `image_references` / `video_references` [INFERRED for Higgsfield; whether the server rejects or drops the mix is open, §9]. Inside Omni Reference an image can still be named the first frame in words ("@Image1 is the first frame.", §4.0 E6) [OFFICIAL S1]; that is not the Keyframes entry's pixel-level lock [INFERRED].
- `medias[].value` is a media UUID or a completed job id, never a URL; local files go through `media_upload` → HTTP PUT → `media_confirm` [HF S3].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** whole seconds 3–30, default 10 [HF S2; OFFICIAL S1]. One generation holds up to 30 s, so a source or take up to the live maximum is one generation (`reference/generation-system.md` §3b.1 item 7). Plan whole seconds; trim in post.
- **Resolution:** 720p or 1080p on Higgsfield, default 1080p [HF S2]. Credits: the Higgsfield blog prints two tables that disagree (720p, 5 s: 13.75 credits in one, 25 in the FAQ) and says the credit cost may vary with the number of reference inputs [HF S4]; always preflight with `get_cost`.
- **Aspect ratio:** 21:9, 16:9, 9:16, 1:1, auto [HF S2; OFFICIAL S1]. Keyframes: the ratio "follows the first keyframe" [OFFICIAL S1]. A third-party API documents `auto` as following the references [SECONDARY S7].
- **Frame rate:** not documented [gap]; measure the first output.
- **Audio:** always generated, "two-channel stereo" [OFFICIAL S1]; no switch [HF S2]. "Background music and sound effects are generated by the model based on the visuals. Describe your audio requirements in the audio section of the prompt." [OFFICIAL S1]. Audio input: "Audio input currently supports voice profile references only" [OFFICIAL S1], and that is not exposed here [HF S2]. An aggregator measured a 720p output with two-channel AAC audio [SECONDARY S6]. A silent deliverable, an own voiceover or the original's restored audio is made in post (`awl.py restore-audio`, CapCut) [INFERRED].

### 2.4 Call recipes

Every recipe uses the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight. Send `mode` and `resolution` every time.

**Text-to-video**
```json
{"model":"kling4_0","mode":"text-to-video","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","resolution":"720p"}
```
**Start frame** (an exactly-9:16 image, 720×1280)
```json
{"model":"kling4_0","mode":"image-to-video","prompt":"<PROMPT: what happens from the first frame on>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":10,"aspect_ratio":"9:16","resolution":"720p"}
```
**Start + end frame**
```json
{"model":"kling4_0","mode":"image-to-video","prompt":"<PROMPT: the process between the two frames>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p"}
```
**Reference-to-video** (order inside each role = its number, [INFERRED])
```json
{"model":"kling4_0","mode":"reference-to-video","prompt":"<PROMPT citing @Image1, @Image2, @Video1 with a role each>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":15,"aspect_ratio":"9:16","resolution":"720p"}
```
**Reference-to-video with Kling Elements** (the prompt citation of elements is unverified, §3.7)
```json
{"model":"kling4_0","mode":"reference-to-video","prompt":"<PROMPT>","kling_element_ids":["<ELEMENT_ID_1>"],"medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"}],"duration":12,"aspect_ratio":"9:16","resolution":"720p"}
```
**Creative Recreation** (Recreate: the source rides as a video reference, the product as an image reference) — mode choice [INFERRED]
```json
{"model":"kling4_0","mode":"reference-to-video","prompt":"Replace <the source object> in @Video1 with the <product> from @Image1. Keep everything else unchanged, including <keep-list> ...","medias":[{"value":"<VIDEO_MEDIA_ID or JOB_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID>","role":"image_references"}],"duration":<SOURCE_SECONDS>,"aspect_ratio":"9:16","resolution":"720p"}
```
**Video edit** (source already 9:16; a job id also works as value [HF S3]; output length against `duration` unverified, §9)
```json
{"model":"kling4_0","mode":"video-edit","prompt":"Edit @Video1. <ONE CHANGE>. Keep everything else unchanged, including <keep-list>.","medias":[{"value":"<VIDEO_MEDIA_ID or JOB_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID>","role":"image_references"}],"duration":<SOURCE_SECONDS>,"aspect_ratio":"9:16","resolution":"720p"}
```

### 2.5 Parameter gotchas

1. **`resolution` defaults to `1080p`** [HF S2]: an omitted value costs more and needs a downscale. Always send `720p`.
2. **`mode` defaults to `text-to-video`** [HF S2]: send the mode that matches the `medias`. Whether Higgsfield ignores media that do not fit the mode, rejects them, or switches the mode itself is unknown (§9) [INFERRED].
3. **No audio switch.** Every take carries a stereo track [OFFICIAL S1; HF S2; SECONDARY S6]. Control speech and music in the prompt (§3.9); remove or replace the track in post.
4. **Default subtitles and music.** "Only two types of negative instructions are truly necessary: no subtitles and no background music. The model may add these by default, so explicitly exclude them when they are not needed." [OFFICIAL S1].
5. **Multi-shot by default.** "Multi-shot is enabled by default, allowing the model to automatically split shots and organize pacing based on the content." [OFFICIAL S1]. A single take is written as one (§3.5).
6. **Frames and references never in one call** (§2.2) [OFFICIAL S1].
7. **Shared video quota:** reference videos, edit videos and video elements together: at most 5 clips and 30 s [OFFICIAL S1]. A 30 s edit source leaves no room for another video. Each clip must be at least 3 s [OFFICIAL S1].
8. **"Edit @Video1" vs "Reference @Video1".** "Simply writing “Reference @Video1” may be interpreted as reference-based generation instead of editing." [OFFICIAL S1]. Pair the verb with the matching `mode` [INFERRED].
9. **Prompt expansion.** "Kling 4.0 can expand and refine your instructions with a director’s eye" and "When the description is already sufficiently clear, the model follows it faithfully without adding its own interpretation." [OFFICIAL S1]. A thin prompt invites invented beats, cuts and music; write complete prompts [INFERRED].
10. **Prompt length.** Kling: up to 8,000 tokens [OFFICIAL S1] (an aggregator says 8,000 characters [SECONDARY S6]). Higgsfield states no limit for this id [HF S2, S3]; a 5,000-character limit has been seen on Higgsfield for another model in this library [INFERRED]. Until the first request shows the limit, keep a prompt under about 5,000 characters by cutting descriptive wording, never the clean-plate, count or continuity lines (§9).
11. **Whole seconds only** [HF S2]: a 7.5 s beat is planned as 8 s and trimmed.
12. **Numbering stays fixed across clips:** the same references in the same `medias` order in every clip of a video (`reference/generation-system.md` §3b.1 item 6) [INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-with-loupe)

| mode | params to send | expected output | post-processing |
|---|---|---|---|
| `text-to-video`, `reference-to-video` | `"aspect_ratio":"9:16","resolution":"720p"` | 720×1280 expected [INFERRED: an aggregator measured a 16:9 720p output as 1280×720, SECONDARY S6]; fps undocumented | verify (`hf-get` reports the size); `awl.py conform` |
| `image-to-video` | same, plus exactly-9:16 frames at 720×1280 | the ratio "follows the first keyframe" [OFFICIAL S1] → 720×1280 expected [INFERRED] | conform frames to 9:16 before upload; verify |
| `video-edit` | same; the source already 9:16 | presumably the source's ratio [INFERRED]; untested | reframe the source to 9:16 first (`awl.py conform` with focus, or Higgsfield `reframe`); verify |

Always finish with `awl.py conform --video "<in>" --out "<out>"` (scale-to-cover and focus crop to exactly 720×1280, never stretched; a no-op copy when already exact). A `lost_fraction` above about 12 % is a wrong-ratio generation: regenerate from 9:16 inputs instead of forcing the crop [INFERRED]. `1080p` plus a downscale is possible but costs more and is not the project default [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Principle:** "Use descriptive language and minimize abstract terms and negative instructions. Describe visual details as explicitly as possible to reduce the need for the model to infer or guess." [OFFICIAL S1]. Kling's own table replaces "Premium look" with "Side backlighting outlines the object's edges, the background is blurred, and fine matte grain is visible on the surface." and "A middle-class family's kitchen" with "Wood-grain cabinets, a rice cooker and seasoning jars on the countertop, and sticky notes on the refrigerator door." [OFFICIAL S1].
- **Omni Reference structure (official):** `[Asset Roles]` "@Image1 defines ___; preserve its ___." → `[Overall Settings]` "Scene and texture: ___; visual style: ___; camera tone: ___." → `[Sequence of Events]` "0–X s: ___ (visuals + action + emotion) […] Y s–end: ___ (closing shot)" → `[Audio]` "Dialogue/voiceover + ambient sounds + music + sound effects" [OFFICIAL S1].
- **Long-form layout of the official examples:** numbered, upper-case sections — SCENE CONTEXT (opening with "EXACT 1 HUMAN CHARACTER — NO DUPLICATES"), ACTIVE REFERENCES, LOCATION MAP, FIRST FRAME AND SPATIAL BLOCKING, FORMAT MODE, OPTICS, CAMERA, ACTION TIMING, PHYSICS, LIGHTING, AUDIO, CHARACTER ACTING, STYLE, QUALITY, POSITIVE CONSTRAINTS (§4.0 E2, E3) [OFFICIAL S1]. This is the pattern card for the project's requests (§4.1–§4.4); sections a shot does not need are left out [INFERRED].
- **Length:** "Start with one sentence that clearly describes the element, scene, action, and emotion. Then add only the details that meaningfully affect the result, such as camera work, timing, audio, and preservation requirements. This is more effective than piling on adjectives." [OFFICIAL S1]. Official examples run from one line ("An old man ranting about AI.") to several thousand characters [OFFICIAL S1]; Higgsfield's cap is open (§2.5 item 10).
- **Language:** English prompts throughout the official guide; spoken lines are written in the language they are spoken in (§3.9) [OFFICIAL S1].
- **Word sense:** in Kling's English guide "element" often means the main subject ("Describe the element and what you want to happen"; "The element is shown in profile while talking on the phone"), while "@Element1" is a Kling Element asset [OFFICIAL S1; reading INFERRED]. Name subjects concretely ("the woman", "the bottle") rather than "the element" [INFERRED].

### 3.2 Subject and identity

- First mention carries the visible identity: age, hair, build, then wardrobe item by item ("Around 30 years old, with short dark hair, light stubble, and a lean, athletic build. […] A fitted dark charcoal-gray tactical top with a closed neckline; Matching tactical trousers; Black leather ankle boots.") and a consistency line ("The actor's face, hairstyle, and physique must remain consistent throughout.") [OFFICIAL S1].
- Count people in the first words: "EXACT 3 UNIQUE HUMAN CHARACTERS ACROSS THE VIDEO", "EXACT 1 CHARACTER — NO DUPLICATES" [OFFICIAL S1]; give a recurring character a label ("BISCUIT (C1)", "C2") [OFFICIAL S1].
- With a reference: "@Image2 defines the female protagonist. Preserve her facial features, hairstyle, and clothing." [OFFICIAL S1].

### 3.3 Action, motion and physical interaction

- Kling claims large-scale motion and camera moves "remain smooth and stable" [OFFICIAL S1]; the official examples still spell every action out with its hand, contact and weight: "Both hands support it continuously; the forearms tense and the lift accelerates slowly under its weight." / "the bag swings with a delayed motion and thuds heavily against the side of her leg" / "Each person performs a clearly defined action. After removing a garment, the corresponding crew member holds it in their hands." [OFFICIAL S1].
- A PHYSICS section states causes, inertia and what never intersects: "The blade-supporting hand has visible clearance to slide free as the sword settles; the hand never passes through the blade or tabletop." [OFFICIAL S1].
- Speed is stated: "real-time motion", "natural walking speed and no slow motion", "no slow motion, no speed changes" [OFFICIAL S1].
- Keyframe-style controls the guide lists for timing: "Raise a hand at 3 seconds, turn around at 7 seconds"; "Character B enters through the door at 6 seconds, rather than appearing only at the end" [OFFICIAL S1].

### 3.4 Environment, lighting and style

- Scenes are lists of concrete objects, never adjectives (§3.1) [OFFICIAL S1].
- LIGHTING names one motivated key source with its side: "Soft daylight from the large window on frame-right is the single motivated key source." / "Cold storm daylight enters from upper-left." [OFFICIAL S1].
- STYLE names the look and a palette split: "Color balance: 60% black and charcoal, 25% cool white showroom tones, 15% faded blue denim and natural skin." [OFFICIAL S1]. Many official examples add "old-photograph softness, organic film grain […] no digital sharpening"; that is the examples' house look, not a requirement — a phone-shot UGC take describes a phone camera instead [INFERRED].
- "When specifying an animation style, explicitly exclude photorealism to avoid inconsistent results that mix the two styles." and "combining positive descriptions with explicit exclusions produces more consistent results" [OFFICIAL S1].

### 3.5 Chronology, timing and multi-shot structure

- **Default:** "Multi-shot is enabled by default, allowing the model to automatically split shots and organize pacing based on the content." [OFFICIAL S1]; "Smart Storyboard" has no toggle [OFFICIAL S1], and Higgsfield exposes no switch [HF S2].
- **One continuous take** (every Create take, `reference/generation-system.md` §3b.1 item 8) is written in FORMAT MODE, in Kling's own phrasing: "One uninterrupted 15-second vertical 9:16 shot. No cuts, fades, dissolves, speed ramps, wardrobe transformations, location changes, or duplicated poses." / "The entire video must be one continuous lateral side-tracking long take, filmed in a single shot with no cuts, no angle changes, and no scene changes." [OFFICIAL S1]. How reliably this overrides the default is untested (§9) [INFERRED].
- **Planned cuts:** "FORMAT MODE: Six shots with hard cuts: SHOT 1 — 0.0–4.0s: roar and launch.SHOT 2 — 4.0–9.0s: […]" / "Hard cuts at 3.0, 5.0, 8.0, 10.0, and 11.0 seconds." / "Shot 1 (5s): […]" ; motivated transitions ("Cuts are motivated by wing wipes, smoke wipes and close architectural passes. No fades or dissolves.") [OFFICIAL S1]. Third-party APIs have per-shot fields capped at 15 s in total [SECONDARY S6]; Higgsfield has none [HF S2].
- **Time markers:** decimal ranges "0.0–2.0s:", "0–3 seconds:", "00:00–00:03 |" and absolute moments "At 0.0 seconds" [OFFICIAL S1]. No dead opening: "Every shot begins mid-gesture with the teacher already pointing toward the active numeral. No empty establishing beat." [OFFICIAL S1].
- **Keyframes:** "X–Y sec | Keyframe 1: [Describe what happens]" [OFFICIAL S1]; with frames, Higgsfield advises letting the keyframes set the key moments and using the prompt for the action and camera movement between them [HF S4].
- State the duration and format in the prompt too, as the official examples do ("15 seconds total, six shots", "vertical 9:16"), matching `duration` and `aspect_ratio` [OFFICIAL S1 pattern; INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

- No camera-control parameter on Higgsfield [HF S2]; the camera is written in its own CAMERA section, separate from the subject's ACTION TIMING [OFFICIAL S1 pattern].
- Official vocabulary: "Push-ins, pull-outs, pans, tracking shots, and orbit shots" [OFFICIAL S1]; "Natural handheld cinematography with noticeable vertical movement from footsteps, subtle irregular shake, and framing corrections"; "Whip pans follow vehicle and character movements"; "one continuous lateral side-tracking long take"; "strictly vertical top-down overhead shot"; "The camera gradually pulls back" [OFFICIAL S1].
- Operator, distance, height and size of move: "A human operator stands approximately two and a half meters away at chest height and performs one slow handheld clockwise arc of less than one meter." [OFFICIAL S1]. OPTICS gives lens and field of view: "50mm equivalent lens with a 40° horizontal field of view" [OFFICIAL S1].
- Rigs excluded by name when the look matters: "Not a gimbal, slider, tripod lock-off, drone or digitally stabilised camera." / "No mechanical, rail-mounted camera movement." [OFFICIAL S1]. A locked camera: "The opening camera holds its position while the iron block leaves the frame." [OFFICIAL S1].
- From a video: "Reference the camera path and pacing of @Video1." [OFFICIAL S1].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- **Numbering:** "Assets are automatically numbered in upload order, such as @Image1, @Image2, and @Video1." [OFFICIAL S1]. Official examples also write "@Video 1", "@image1", "Image 1" and "Reference Image 1"; this library writes `@Image1`, `@Video1` (the documented form) [INFERRED]. On Higgsfield the N-th entry of a role is expected to be N [INFERRED, `AWL/higgsfield/higgsfield-mcp.md` §5 convention]; check the first take (§9).
- **One role per asset:** "Specify the intended role of each asset, for example, “@Image1: preserve the character's appearance” or “@Video1: reference the action pacing.” If you provide only asset IDs without specifying their roles, the model will infer their intended use, making the results less predictable." [OFFICIAL S1].
- **Scope and exclusion:** "When multiple assets provide different types of information, specify the scope of each asset's role and explicitly exclude elements that should not be carried over." — e.g. "@Image1: visual-world reference only — […] Never inherit its existing characters, numerals or composition." [OFFICIAL S1].
- **Video roles:** action ("Reference the fighting moves and attack timing in @Video1"), camera ("Reference the camera path and pacing of @Video1"), whole structure ("Recreate @Video1 shot-for-shot and cut-for-cut") [OFFICIAL S1]. "The closer the reference clip and target content are in pacing and shot structure, the easier it is to achieve the desired results." [OFFICIAL S1].
- **The original reference** (Recreate, Edit Mode): the original's own silent footage is the only video reference, bound by purpose with its keep-list; spot and size ride in the prompt and the product views (`reference/generation-system.md` §4b.5) [house rule]. Whether a video reference's own sound reaches the output on Higgsfield is unknown (a third-party API keeps it only with `keep_original_sound:true`, default false [SECONDARY S7]); upload the silent copy [INFERRED].
- **Kling Elements:** Kling cites them as `@Element1` ("Edit @Video1. When the box is opened again at the end, add @Element1 lying inside asleep.") [OFFICIAL S1]. Higgsfield passes them in `kling_element_ids` [HF S2]; whether the array order becomes `@Element1…`, whether `<<<element_id>>>` tokens work, and whether Higgsfield reference-element UUIDs behave like Kling elements is undocumented (§9). Until a take shows it, put people and products in `image_references` [INFERRED].
- **Voice:** voice profiles are not on Higgsfield [HF S2]; describe the voice (§3.9).
- **Text in references:** not documented for 4.0 [gap]. Keep reference images free of captions, usernames and watermarks, except the product's own approved label [INFERRED].

### 3.8 Start and end frames

- Kling's formats: "Use @Image1 as the first frame, then describe what happens next." / "Use @Image1 as the first frame and @Image2 as the last frame, then describe the [process] in between." / "Use @Image1 as the last frame, then describe what happens before it." [OFFICIAL S1].
- On Higgsfield the frames ride as `start_image` / `end_image`; whether they are also numbered `@Image1`/`@Image2` there is unknown, so call them "the first frame" and "the last frame" in the prompt [INFERRED] (§9).
- "Without keyframes, the model determines the order and timing of visual changes. With keyframes, you define the visuals at specific timestamps." [OFFICIAL S1]. The official first + last example describes the path into the end frame physically: "The closing camera holds the empty tabletop composition while the sword enters, then settles into the exact final reference." [OFFICIAL S1].
- The ratio follows the first keyframe [OFFICIAL S1]: frames are exactly 9:16 at 720×1280. A start frame is the literal first frame, photoreal and paste-tested (`reference/anomaly-catalog.md` §2.15) [house rule].

### 3.9 Audio, dialogue and sound (if supported)

- **Always on, stereo**, no switch (§2.3) [OFFICIAL S1; HF S2].
- **Speech:** "To generate speech in a specific language, write the dialogue in that language inside quotation marks." Voice: "describe the speaker's age, vocal tone, speaking speed, and emotion" — "She speaks in English with sincerity and emotional engagement: “I honestly love this Kling jacket—the cropped fit feels so confident, and it goes with everything.” Start with warm appreciation, emphasizing “love” and “confident.”" [OFFICIAL S1].
- **Several speakers** (official example rules): "Each person has a distinct voice." / "When one person is speaking, the others remain silent. No interruptions or overlapping dialogue." / "All dialogue must have clear vocals, with lip movements synchronized to the corresponding language." / "Spanish pronunciation must be natural and standard, without English-accented pronunciation." / "The entire line must be delivered while the director is on screen." / "pause for approximately 0.5 seconds" [OFFICIAL S1].
- **Music and effects:** "Do not add background music." / "SFX only, no music, no score, no song, no soundtrack." / "No music for the first 12 seconds." ; a mix line: "Music ducks beneath every spoken line." / "Roar, wings and fire remain louder than the music." [OFFICIAL S1]. Uploading music or effects is not supported: "Background music and sound effects are generated by the model based on the visuals." [OFFICIAL S1].
- **No speech:** "No dialogue, no voice-over, and no background music." [OFFICIAL S1].
- **Own voiceover (item 31) or restored original audio:** the model's track is replaced in post; still write "No dialogue, no voice-over" for people who must not talk, and "no background music", so no lip movement or music-timed motion is baked into the picture [INFERRED].
- **Languages:** Chinese, English, Japanese, Korean, Spanish, Portuguese, German, French, Hindi; dialects Sichuanese, Cantonese; accents Beijing, Northeastern Chinese, Taiwanese Mandarin, American, British, Indian [OFFICIAL S1].
- **Edit:** "Keep the audio exactly identical to the original video. Do not add any new sounds." ; a spoken line can be replaced: "Replace the final line, “Ah, it's all old stuff,” with “Why is there a pig here?”" [OFFICIAL S1].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield [HF S2]; aggregators report none on Kling 4.0 at all [SECONDARY S6].
- Kling: "Negative prompts can increase the likelihood of errors. Only two types of negative instructions are truly necessary: no subtitles and no background music." and "(Describe what you want to see directly) The element is shown in profile while talking on the phone." [OFFICIAL S1].
- The official examples still exclude in three places: carry-over from references ("Never inherit its existing characters"), style mixing ("explicitly exclude photorealism"), and a closing list of the shot's own risks ("Negative Constraints: No cuts, no jump cuts, no white flashes, no dissolves, no slow motion, no speed changes, no subtitles, no watermarks, no UI, and no background music. […] Do not make the travel bag appear weightless.") — usually after POSITIVE CONSTRAINTS that state the wanted counts and states ("Exactly one dragon remains visible throughout the sequence.") [OFFICIAL S1].
- Project form: positive states first (POSITIVE CONSTRAINTS with exact counts), then one short exclusion sentence for subtitles and text, music when unwanted, cuts in a take, reference carry-over, and each product's own wrong use and count (`reference/anomaly-catalog.md` §3) [INFERRED from the official pattern].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (CapCut / `awl.py captions`); reference wording, usernames and watermarks are never copied; no emoji in any text, ever (command item 6).

- **(a) Reliability.** Kling claims "Accurate Text Generation: Supports clear and stable generation of multilingual text, emojis, and logos. Even with dynamic camera movement and scene transitions, text remains clear and stable, keeping key information accurate and readable." and shows burned-in subtitles timed from the prompt [OFFICIAL S1]; Higgsfield repeats it as on-screen text in nine languages plus emoji and logos [HF S4]. No independent spelling test was found [INFERRED gap]. Verdict: promising, unverified; hooks and captions still go to post.
- **(b) Clean plate (default in Analyze Mode).** The model "may add" subtitles by default [OFFICIAL S1], so every prompt carries the exclusion, in Kling's own wording: "No text overlays, subtitles, or music." / "no subtitles, no watermarks, no UI" / "Do not add any characters, change the store structure or camera movement, or introduce subtitles, logos, watermarks, or extra text." / "Background text and map labels must be blurred and unreadable. No real brands, organization names, logos, or watermarks may appear." [OFFICIAL S1]. Closing line used here: "No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear." [INFERRED, built from the official items]. Because the model writes text well, a described sign, screen or package will likely be lettered: describe such surfaces as plain and unmarked, and never quote a non-dialogue string [INFERRED]. With reference media add "do not reproduce any text, captions, usernames or watermarks from @Video1" [INFERRED from the official "Never inherit" pattern]. Never cut these lines to fit a length limit; cut descriptive wording instead [INFERRED].
- **(c) Intentional in-frame text** (scene text only: packaging, a sign, a screen). Kling's pattern: the exact words in backticks or quotes, the surface, the placement and the stability terms — "Fix a clear, stable, readable sign with the exact uppercase text `KLING AI OPEN 24 hours` in the middle of the convenience store's right-side glass window. The text must remain correctly spelled, undistorted, and free of flickering throughout the video. Keep the sign fixed to the inside of the glass window without obstructing any characters." [OFFICIAL S1]. An approved product label comes from the reference image and is held by a QUALITY line: "The white Kling wordmark remains correctly spelled, stable, and attached to the same chest position." [OFFICIAL S1]. Keep it short; QC every frame with `awl.py qc --mode analyze --allowed-text "<text>"` [INFERRED].
- **(d) Edit operations: removing source text (Edit Mode).** Text removal is not documented [gap]; the official removal pattern is "Edit @Video 1 to remove the foreground person. Keep everything else unchanged, including the background, other subjects, camera movement, lighting, composition, and video duration. Seamlessly reconstruct the areas previously obscured by the person, ensuring natural, consistent details with no visible artifacts." [OFFICIAL S1]. Applied to text, as its own first pass (Higgsfield advises changing one element at a time [HF S4]): "Edit @Video1 to remove every caption, subtitle, username, watermark, sticker, timestamp and overlay logo. Keep everything else unchanged, including the people, their movements, camera movement, lighting, composition, audio and video duration. Seamlessly reconstruct the areas previously covered by the text with natural, consistent details and no visible artifacts. No subtitles or on-screen text appear." [INFERRED]. Keep a named source text only on the user's request ("keep only the lettering on the mug"). Small static overlays may first go with `awl.py clean --delogo` in Edit Mode; in Analyze Mode the prompt lines do it, no tool removes a caption. Verify with `awl.py qc --mode edit`.
- **(e) Watermarks.** Kling's free plans watermark outputs [SECONDARY S6]; no Higgsfield watermark is documented [gap]. `awl.py qc` OCR catches invented corner marks.

### 3.12 Character / identity consistency

- One reference image per person, bound by role and kept strictly: "Reference the facial features of the characters in @Image1, @Image2, and @Image3, keeping them strictly consistent." / "The attached character design sheet (Image 2) is the sole authoritative reference for BISCUIT (C1)" / "The same dog, spacesuit, and fork must remain visually consistent in every frame." [OFFICIAL S1].
- Positions and eyelines across cuts: "Maintain consistent character positions, eyelines, and clothing throughout. Do not abruptly replace characters or change their spatial relationships." [OFFICIAL S1].
- Replacing several people: each "@ImageN" with its identity and wardrobe written out ("use the identity, face, dark curly hair, white sun hat, white short-sleeved shirt […] of the man in @Image1") [OFFICIAL S1].
- An identity image whose clothing differs from the kept garment is cropped to the face, and the kept garment is written in positive words (`reference/anomaly-catalog.md` §2.17) [house rule].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Bind the product to its image and list its parts: "Reference the design of the blue motorcycle in @Image4 and keep it strictly consistent." / "@image1 controls the woman’s exact identity, […] black Kling cropped puffer jacket, high collar, silver zipper, white chest logo, quilted panels, elastic cuffs, side pockets […] Preserve every detail exactly." [OFFICIAL S1].
- Hold geometry and size in QUALITY and POSITIVE CONSTRAINTS: "The car's overall shape and lighting design must remain consistent across all shots." / "Keep the Corgi exactly the same size as the original, without scaling it up or down." / "Exactly one woman wears exactly one black Kling jacket throughout the shot." [OFFICIAL S1].
- Rigidity and handling: "The completed sword remains rigid during carrying and placement." / "one hand around the grip and the other supporting the blade flat near its balance point" [OFFICIAL S1].
- Recreation: "matching the original Element's position, scale, movements, and trajectory" [OFFICIAL S1].
- Write count, rigidity, size against the hand or a named neighbour, grip, and which face (label side) is toward the lens [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Integration wording (official):** "Ensure the replacement Element integrates naturally into the original footage, matching the original Element's position, scale, movements, and trajectory." / "The depth to which it sinks into the snow, the snow kicked up by its paws, the snow settling on its body, and its shadow cast onto the snow must all follow the blocky body accurately." / "Maintain consistent hands, gloves, sleeve details, metal geometry, and contact shadows." [OFFICIAL S1].
- **Layout that does not swap sides:** a LOCATION MAP section fixes what is frame-left, frame-right and behind, and the side the camera keeps: "The left rack stays behind frame-left, the second rack remains in the rear-right, and the large window stays on frame-right. The camera remains directly in front of her" / "Camera always stays on the front side of the teaching axis" [OFFICIAL S1].
- **Scale:** the size relation comes from the plan's size reckoning (`reference/anomaly-catalog.md` §2.7): the ratio to a named neighbour at the same depth and the depth in the shot. Whether words control a placed product's size on this model is untested: write the relation as a check, measure the first output with `awl.py scale`, and let the brief carry the size risk [INFERRED].
- **Posture, support and place:** one chronological sentence, positive first (`reference/anomaly-catalog.md` §2.16) [house rule].
- **Contact, grip, occlusion:** each hand's job and the contact point inside ACTION TIMING (§3.3); an occluder is timed: "A yellow taxi or a group of pedestrians quickly passes between the camera and the woman, completely obscuring the frame for approximately half a second to one second. When the obstruction clears, […]" [OFFICIAL S1].
- **Scene light on the asset:** one motivated key source and its travel: "Orange light sweeps across his left shoulder, the side of his face, and the ground." / "Return to the original neutral daylight before the sword enters the final tabletop shot." [OFFICIAL S1]; add the product's reflection on glossy surfaces and its contact shadow [INFERRED].
- **Persistent states and counts** (`reference/anomaly-catalog.md` §3): Kling's own forms — "EXACTLY 1 DRAGON — NO DUPLICATES" in SCENE CONTEXT, "the other four blocks remain resting on the table through the cut", "Whenever it reappears after being covered by snow, it must remain the exact same blocky Corgi with consistent textures", "Every quantity remains stable and readable until its shot ends", "one head, two wings, four legs and one tail" [OFFICIAL S1]. Write each use as the part, the preparation step and the contact point in its ACTION TIMING row; restate counts and states in the first words of the row after an exit, an occlusion or a cut; put each product's own wrong use and count in the exclusion sentence [INFERRED from the official pattern].
- **Across clips:** one generation holds 30 s, so most takes need no seam. Where one must exist: `image-to-video` with `start_image` = the hand-off frame (`awl.py last-frame`, exact, lossless) and, for a keyframe ladder, `end_image` = an approved keyframe of the planned end state (`reference/generation-system.md` §3b.2). A `reference-to-video` clip cannot take a frame role (§2.2): there the hand-off frame rides as `@Image1` with "Use @Image1 as the first frame." — not pixel-exact, unverified [INFERRED from OFFICIAL S1]. Keep the same references in the same order, the same `resolution` and the same wording for identities, wardrobe, setting, light and style; restate positions, hand contents and light at the start of the next prompt [INFERRED]. Kling's own extension is "(Coming soon)" and not on Higgsfield [OFFICIAL S1; HF S2]. No seed [HF S2].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Verbatim from Kling's 4.0 user guide (S1; trimmed with […]).

**E1 — Omni Reference role binding**
> "@Image1 defines the scene. Preserve its spatial layout, furnishings, and lighting.
> @Image2 defines the female protagonist. Preserve her facial features, hairstyle, and clothing.
> The female protagonist walks toward the window, stops, and looks back."

**E2 — one continuous vertical 9:16 take, a presenter, a product with a logo, speech**
> "1. SCENE CONTEXT EXACT 1 HUMAN CHARACTER — NO DUPLICATES. A woman enthusiastically presents the black Kling cropped puffer jacket she is wearing inside a minimalist fashion showroom. […] One continuous 15-second vertical fashion shot.2. ACTIVE REFERENCES@image1 controls the woman’s exact identity, straight brown hair, blue eyes, small earrings, black Kling cropped puffer jacket, high collar, silver zipper, white chest logo, […] Preserve every detail exactly. […] 5. FORMAT MODE: One uninterrupted 15-second vertical 9:16 shot. No cuts, fades, dissolves, speed ramps, wardrobe transformations, location changes, or duplicated poses. […] 7. CAMERA: A human operator stands approximately two and a half meters away at chest height and performs one slow handheld clockwise arc of less than one meter. […] 8. ACTION TIMING 0.0–2.0s: She finds the lens, takes a light anticipatory breath, and forms a genuine welcoming smile.2.0–5.5s: While beginning her sentence, she touches the structured collar and follows the zipper downward with her fingertips, keeping her eyes on the lens. […] 11. AUDIO: Layered showroom ambience: quiet room tone, distant ventilation, soft jacket rustle, zipper contact, jeans movement, and restrained footsteps. In a sincere, emotionally engaged English voice, she says: “I honestly love this Kling jacket—the cropped fit feels so confident, and it goes with everything.” […] SFX only, no music, no score, no song, no soundtrack. […] The white Kling wordmark remains correctly spelled, stable, and attached to the same chest position. […] 15. POSITIVE CONSTRAINTS: Exactly one woman wears exactly one black Kling jacket throughout the shot. […] Add no second person, clothing change, subtitle, price, promotional overlay, mirror reflection, music, or runway movement. A flat, emotionless delivery, wandering eyeline, malformed wordmark, changing jacket length, extra limb, or fabric passing through her body equals a failed shot."

**E3 — first + last frame, counts and hand–object contact**
> "SCENE CONTEXT EXACT 1 CHARACTER — NO DUPLICATES. […] ACTIVE REFERENCES: @Image1: exact first-frame anchor. Preserve all five iron blocks, their arrangement, the tabletop, background tools, perspective, and lighting. […] FORMAT MODE: 15 seconds total, six shots.Hard cuts at 3.0, 5.0, 8.0, 10.0, and 11.0 seconds. […] ACTION TIMING: 0.0–3.0s — TAKE THE IRON. Start on the exact first reference; during 0.0–0.6s, the blacksmith’s matching gloved hands enter from screen-left and grip opposite ends of the largest central block. During 0.6–1.5s, the wrists brace and both hands lift the block clear of the tabletop, exposing the patch of table beneath it. During 1.5–3.0s, the blacksmith carries the supported block out through screen-left; the other four blocks remain resting on the table through the cut. […] the hand never passes through the blade or tabletop. […] POSITIVE CONSTRAINTS: The first frame contains exactly five iron blocks. […] Exactly one finished sword is present.No text overlays, subtitles, or music."

**E4 — one continuous long take with a timed occlusion**
> "Generate a 20-second, horizontal 16:9 realistic cinematic street escape video. The entire video must be one continuous lateral side-tracking long take, filmed in a single shot with no cuts, no angle changes, and no scene changes. […] 12–15s: Occlusion and losing sight of her. A yellow taxi or a group of pedestrians quickly passes between the camera and the woman, completely obscuring the frame for approximately half a second to one second. […] Audio: No dialogue, no voice-over, and no background music. […] Negative Constraints: No cuts, no jump cuts, no white flashes, no dissolves, no slow motion, no speed changes, no subtitles, no watermarks, no UI, and no background music. […] Do not make the travel bag appear weightless."

**E5 — Creative Recreation (swap the subject of a reference video)**
> "Replace the Element in @Video 1 with the Element from @Image 1. Keep everything else unchanged, including the background composition, camera movements, lighting, shadows, audio, and video duration. Ensure the replacement Element integrates naturally into the original footage, matching the original Element's position, scale, movements, and trajectory."

**E6 — a first frame plus a video reference for camera, motion and cuts**
> "@Image1 is the first frame.  @Video1 is the reference for camera, motion, timing and cuts. Recreate @Video1 shot-for-shot and cut-for-cut, but starting from @Image1: the rider is SITTING in a black office swivel chair instead of standing on a bike. […] Wherever the video shows the bike — […] — show the office chair (mesh backrest, padded seat, chrome column, five-spoke base, casters). […] No bicycle, handlebar, tyres or pedals anywhere."

**E7 — edit: remove and reconstruct**
> "Edit @Video 1 to remove the foreground person. Keep everything else unchanged, including the background, other subjects, camera movement, lighting, composition, and video duration. Seamlessly reconstruct the areas previously obscured by the person, ensuring natural, consistent details with no visible artifacts."

**E8 — speech in a chosen language**
> "A Spanish female tourist looks at the interpreter in the middle and raises the map in her hand. She speaks in natural, clear, slightly slow Spanish: “¿Dónde está la estación de metro más cercana?”"

Patterns these teach [derived from E1–E8]:
- **Order:** asset roles first (E1, E2 §2, E3), then the scene and its layout, the format (length, ratio, cuts or none), optics and camera, the timed action, physics, light, audio, style, and last the quality and positive constraints with the failure definition (E2, E3).
- **Sentence style:** numbered upper-case section labels followed by plain declarative present-tense sentences; long examples run the sections together without line breaks (E2, E3).
- **Counts first:** "EXACT 1 HUMAN CHARACTER — NO DUPLICATES" opens the prompt and "Exactly one woman wears exactly one black Kling jacket throughout the shot." closes it (E2, E3).
- **Time markers:** decimal second ranges ("0.0–2.0s:", "12–15s:"), sub-second where contact matters ("0.0–0.6s"), and hard-cut times listed in FORMAT MODE (E2, E3, E4).
- **Subject vs camera:** the camera has its own section with operator distance, height, rig and the size of the move; the subject's beats live in ACTION TIMING (E2, E4).
- **References:** `@ImageN` / `@VideoN` + a verb of role ("defines", "controls", "is the first frame", "is the reference for camera, motion, timing and cuts") + "Preserve …" with a part list; replacements name every place the swapped object appears (E1, E2, E5, E6).
- **Detail level:** every hand's job, the part touched, weights and what is revealed underneath ("exposing the patch of table beneath it"); objects persist through cuts by name (E3).
- **Edits:** "Edit @Video1" + one change + "Keep everything else unchanged, including […]" with a keep-list + "Seamlessly reconstruct […]" (E7); recreation uses "Replace […] Keep everything else unchanged […] matching the original Element's position, scale, movements, and trajectory" (E5).
- **Audio:** ambience as a list of concrete sounds; a voice described by manner and language, the line in quotation marks in the spoken language; music excluded explicitly ("SFX only, no music, no score, no song, no soundtrack") (E2, E4, E8).
- **Exclusions:** subtitles and music always handled; other exclusions name the shot's own risks (cuts, slow motion, weightless props, the replaced object anywhere) after the positive statement (E3, E4, E6).
- **Format words:** the prompt repeats the duration and the ratio ("15-second vertical 9:16") (E2, E4).

### 4.1 Text-to-video

```text
SCENE CONTEXT: EXACTLY <n> <people/objects> — NO DUPLICATES. <One sentence: who, where, the action, the emotion.> One continuous <d>-second vertical 9:16 shot.
LOCATION MAP: <what stays frame-left, frame-right and behind; the side of the scene the camera stays on>.
FIRST FRAME AND SPATIAL BLOCKING: <what is visible at 0.0 s: who, pose, what each hand holds, the product's place, posture and state>.
FORMAT MODE: One uninterrupted <d>-second vertical 9:16 shot. No cuts, fades, dissolves, speed ramps or location changes. Real time.
CAMERA: <operator distance and height, rig, one move with its size and direction, where it ends>.
ACTION TIMING: 0.0–<t1>s: <action: which hand, which part, the contact point>. <t1>–<t2>s: <next beat; counts and states restated>. <tn>–<d>.0s: <ending; hold the final composition>.
PHYSICS: <weight, inertia, contact; what never passes through what>.
LIGHTING: <the one motivated key source and its side; shadow side; reflection and contact shadow of the product>.
AUDIO: <ambience as a list of sounds>. <Speaker, age, tone, speed, emotion: "<line in its language>"> | No dialogue, no voice-over. No background music.
STYLE: <camera look, grain, palette split>.
POSITIVE CONSTRAINTS: Exactly <n> <people> and exactly <k> <objects> throughout; <persistent states>. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```
Worked example (12 s, generic):
```text
SCENE CONTEXT: EXACTLY 1 PERSON — NO DUPLICATES. A man in his thirties sands the lid of a small unfinished wooden box at a workbench in a home garage, calm and focused. One continuous 12-second vertical 9:16 shot.
LOCATION MAP: A pegboard with hand tools stays behind him, a closed roller door stays frame-right, and a desk lamp stands on the bench at frame-left. The camera stays in front of the bench.
FIRST FRAME AND SPATIAL BLOCKING: He stands behind the bench in a grey work apron, the box in front of him with its lid on; his left hand rests on the box, his right hand holds a folded sheet of sandpaper.
FORMAT MODE: One uninterrupted 12-second vertical 9:16 shot. No cuts, fades, dissolves, speed ramps or location changes. Real time.
CAMERA: A handheld operator about one and a half meters away at chest height pushes in slowly by about half a meter and ends on a medium close-up of his hands and the box.
ACTION TIMING: 0.0–4.0s: His left hand steadies the box by its near edge while his right hand sands the lid in short strokes along the grain; fine pale dust lifts from the lid. 4.0–8.0s: He stops, blows the dust off the lid and runs his right fingertips across the sanded surface. 8.0–12.0s: He lifts the lid with his right hand, looks inside the empty box, closes it and sets the sandpaper down beside it; the box stays on the bench under his left hand.
PHYSICS: The lid seats flush with a soft wooden knock; the dust drifts down and settles on the bench; his fingers never pass through the wood.
LIGHTING: Warm light from the desk lamp at frame-left is the single key source; his right side falls into soft shadow; the lid's edge catches a thin highlight and the box casts a short shadow to the right.
AUDIO: Garage room tone, the dry rasp of sandpaper, a short breath as he blows the dust, the knock of the lid. No dialogue, no voice-over. No background music.
STYLE: Natural phone-camera look, true colours, mild handheld sway, warm wood and grey tones.
POSITIVE CONSTRAINTS: Exactly one man, exactly one box and one sheet of sandpaper throughout; the box stays closed except between 8 and 10 seconds. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```

### 4.2 Start frame (and end frame) to video

```text
The first frame is the supplied start image[; the last frame is the supplied end image]. <Same SCENE CONTEXT line, counts first.>
FORMAT MODE: One uninterrupted <d>-second vertical 9:16 shot, no cuts. Real time.
CAMERA: <behaviour from the first frame on; for an end frame, how the camera settles into it>.
ACTION TIMING: 0.0–<t1>s: <the first motion: which hand, from where, the contact point>. … <tn>–<d>.0s: <the physical action that reaches the last frame>.
LIGHTING: <as in the frame: key side, shadow side>. AUDIO: <…>.
POSITIVE CONSTRAINTS: <identity, product shape, proportions and counts exactly as in the frame(s)>. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear. No background music.
```
Calling the frames "the start image" / "the end image" instead of `@Image1` / `@Image2` is a choice made because the Higgsfield numbering of frame roles is unknown [INFERRED] (§3.8, §9).

Worked example (start + end frame, 8 s):
```text
The first frame is the supplied start image; the last frame is the supplied end image. EXACTLY 1 PERSON — NO DUPLICATES: a woman sets a breakfast table.
FORMAT MODE: One uninterrupted 8-second vertical 9:16 shot, no cuts. Real time.
CAMERA: The camera holds its position at table height for the whole shot.
ACTION TIMING: 0.0–3.0s: Her hands enter from frame-left carrying one white plate and set it at the near edge of the empty table. 3.0–6.0s: Her right hand places one glass of orange juice to the upper right of the plate. 6.0–8.0s: Both hands withdraw through frame-left and the table settles into the last frame: one plate, one glass, nothing else.
LIGHTING: Morning light from the window at frame-right, as in both frames; soft shadows fall to the left.
AUDIO: Quiet kitchen ambience, a ceramic touch as the plate lands, a soft glass tap. No dialogue, no voice-over. No background music.
POSITIVE CONSTRAINTS: Exactly one plate and one glass; the table and window exactly as in the frames. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```

### 4.3 Reference-to-video

```text
ACTIVE REFERENCES: @Image1 defines <the person>; preserve <face, hair, build, the kept garment>. @Image2 defines <the product>; preserve <shape, colour, label, proportions> exactly. [@Video1: reference only its <camera path / action timing / pacing>; never inherit its people, products, text, captions or watermarks.]
SCENE CONTEXT: EXACTLY <n> … — NO DUPLICATES. <one sentence>. One continuous <d>-second vertical 9:16 shot.
LOCATION MAP / FIRST FRAME AND SPATIAL BLOCKING / FORMAT MODE / CAMERA / ACTION TIMING / PHYSICS / LIGHTING / AUDIO / STYLE: as in §4.1, naming the person and the product by their reference ("the woman from @Image1", "the bottle from @Image2").
QUALITY: <the product's geometry, label and size stay consistent; the label stays correctly spelled and attached to the same face>.
POSITIVE CONSTRAINTS: Exactly <n> people and exactly <k> <product> throughout; <states>. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```
Worked example (10 s):
```text
ACTIVE REFERENCES: @Image1 defines the woman; preserve her face, shoulder-length dark hair and green knit sweater. @Image2 defines the water bottle; preserve its matte white body, flat grey cap and proportions exactly.
SCENE CONTEXT: EXACTLY 1 PERSON — NO DUPLICATES. The woman from @Image1 takes a drink from the bottle from @Image2 at a park bench after a walk, relaxed. One continuous 10-second vertical 9:16 shot.
LOCATION MAP: The bench stands in the middle ground, a path runs behind it, trees stay on both sides. The camera stays in front of the bench.
FIRST FRAME AND SPATIAL BLOCKING: She sits on the left half of the bench; the bottle stands upright on the bench seat to her right, cap closed.
FORMAT MODE: One uninterrupted 10-second vertical 9:16 shot. No cuts, fades, dissolves or speed ramps. Real time.
CAMERA: A handheld operator about two meters away at seated eye height holds a medium shot with small natural sway.
ACTION TIMING: 0.0–3.0s: She picks up the bottle with her right hand around its middle and twists the cap open with her left hand. 3.0–7.0s: She drinks from the open neck of the bottle, head tilted back slightly, the cap held in her left hand. 7.0–10.0s: She screws the cap back on and sets the bottle upright on the seat to her right; it stays there.
PHYSICS: The bottle keeps its rigid shape in her grip; the cap turns on the thread and seats closed.
LIGHTING: Soft afternoon sun from frame-left is the single key source; the bottle shows a soft highlight on its left side and a short shadow on the seat.
AUDIO: Park ambience, distant birds, the click of the cap, a quiet swallow. No dialogue, no voice-over. No background music.
QUALITY: The bottle's shape, colour and size stay consistent; it is about as tall as her forearm is long.
POSITIVE CONSTRAINTS: Exactly one woman and exactly one bottle throughout; she drinks only from the open neck. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```
**Creative Recreation** (Recreate; the original as `@Video1`, the product as `@Image1`), on the pattern of E5:
```text
Replace <the source object, where and when it appears> in @Video1 with the <product> from @Image1; preserve its <shape, colour, label, proportions> exactly. Keep everything else unchanged, including the people, their movements and timing, the background composition, camera movements, lighting, shadows and video duration. Ensure the <product> integrates naturally into the original footage, matching the original <object>'s position, scale, movements, and trajectory; <the size relation to the named neighbour>. <The source object> does not remain anywhere. Do not reproduce any text, captions, usernames or watermarks from @Video1. No subtitles, captions, on-screen text, watermarks, logos or UI overlays appear.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

**Edit** (`mode:"video-edit"`; Kling: "Specify which visual elements must be preserved to minimize changes beyond the intended scope." [OFFICIAL S1]):
```text
Edit @Video1. <One change: what, where, from when to when>. [<The new item> from @Image1: <its description>.] Keep everything else unchanged, including <the people, their movements, camera movement, lighting, composition, audio and video duration>. Seamlessly reconstruct <the areas the change uncovers> with natural, consistent details and no visible artifacts. No subtitles, on-screen text, logos or watermarks are added.
```
Worked example:
```text
Edit @Video1. Replace the red mug on the desk with the plain white mug from @Image1, in the same spot and at the same size, for the whole video. Keep everything else unchanged, including the man, his movements, the camera movement, lighting, composition, audio and video duration. The red mug does not remain anywhere. No subtitles, on-screen text, logos or watermarks are added.
```
- One change per pass; a source with text first gets the text-removal pass (§3.11 d) [HF S4; INFERRED].
- Source limits: up to 5 clips, "including 1 primary video", each 3–30 s, 30 s in total [OFFICIAL S1]; reframe to 9:16 first (§2.6).
- **Extension:** N/A on Higgsfield; Kling lists it as "(Coming soon)" [OFFICIAL S1]. Chain clips instead (§3.14).
- **Motion transfer:** no dedicated mode; use `reference-to-video` with the action reference: "Reference the fighting moves and attack timing in @Video1. Use @Image1 and @Image2 as the character appearance references." [OFFICIAL S1].

## 5. Strengths, weaknesses and failure modes

Kling 4.0 has no failure record in this library yet; the rows below come from Kling's own warnings and the general model risks this command checks, and each is to be confirmed or struck by QC of the first takes.

| failure mode | typical trigger | mitigation |
|---|---|---|
| Burned-in subtitles appear | default behaviour; dialogue in the prompt | "no subtitles" line in every prompt (§3.11 b) [OFFICIAL S1] |
| Background music added | default behaviour | "No background music." / "SFX only, no music, no score, no song, no soundtrack." [OFFICIAL S1] |
| **Unmotivated cuts** in a take meant to be continuous | multi-shot on by default | FORMAT MODE continuous-take sentence (§3.5) [OFFICIAL S1 wording; effect unverified] |
| Invented beats, extra characters or story | short prompt + prompt expansion | complete prompt with counts and every beat [OFFICIAL S1] |
| A reference used for the wrong job | bare `@Image1` without a role | one role and a preserve-list per asset [OFFICIAL S1] |
| Characters, composition or text carried over from a style or video reference | no scope stated | "reference only its …; never inherit …" [OFFICIAL S1] |
| An edit regenerates instead of editing | "Reference @Video1" wording; wrong `mode` | "Edit @Video1" + `mode:"video-edit"` [OFFICIAL S1; INFERRED] |
| Unrequested changes in an edit | no keep-list | "Keep everything else unchanged, including […]" plus the keep-list [OFFICIAL S1] |
| Photoreal and animated looks mixed | animation style without exclusion | exclude photorealism [OFFICIAL S1] |
| Vague look | abstract adjectives ("premium", "cinematic feel") | concrete light, material and composition [OFFICIAL S1] |
| **Duplicated objects / extra people / miscounts** | counts left implicit | "EXACTLY <n> — NO DUPLICATES" first, "Exactly <n> … throughout" last [OFFICIAL S1 pattern] |
| **Identity drift, clothing changes, left-right swaps** | long multi-beat takes, cuts | references per person, LOCATION MAP, "Maintain consistent character positions, eyelines, and clothing", "No cuts, fades, dissolves, speed ramps, wardrobe transformations" [OFFICIAL S1] |
| Overlapping or misassigned dialogue; wrong accent | several speakers | one speaker at a time, line while on screen, "without English-accented pronunciation" [OFFICIAL S1] |
| **Arbitrary slow motion / sudden speed changes** | mood words, no pacing | "Real time", "no slow motion, no speed changes" [OFFICIAL S1] |
| **Dead space** at the start or end | nothing happens at 0.0 s; long holds | the first frame written mid-action ("Every shot begins mid-gesture […] No empty establishing beat."); a beat per row to the end [OFFICIAL S1] |
| **Morphing** between object states | transformation without a physical path | "No fades, dissolves, or object-morph transitions"; the state change shown as a hand action [OFFICIAL S1] |
| Hands through objects; weightless props | no physics stated | PHYSICS line: weight, inertia, "never passes through" [OFFICIAL S1] |
| A count changes after an exit, occlusion or cut; a product used through a part with no opening; a later state leaking from a reference (`reference/anomaly-catalog.md` §3) | counts and parts written once | counts restated in the first words after each exit or cut; part, preparation step and contact point per use; references show t=0 states only [INFERRED] |
| Placed product too large or too small (`reference/anomaly-catalog.md` §2.7) | untested on this model | size relation written as a check; first output measured with `awl.py scale`; risk in the brief [INFERRED] |
| Landscape or cropped result | `auto` ratio; a start frame not 9:16 | `aspect_ratio:"9:16"`; 9:16 frames and sources (§2.6) [OFFICIAL S1] |
| 1080p output and a higher bill | `resolution` omitted | send `720p` [HF S2] |
| Lip movement or music-timed motion under an own voiceover or restored audio | audio cannot be switched off | "No dialogue, no voice-over, and no background music."; track replaced in post [INFERRED] |
| Garbled or extra in-frame text | described signs or screens; quoted strings | plain, unmarked surfaces; quotes only for dialogue and intended text (§3.11) [INFERRED] |

## 6. Model-specific features and controls

- **Multi-shot / Smart Storyboard:** on by default, no switch; planned cuts are written in FORMAT MODE (§3.5) [OFFICIAL S1; HF S2].
- **Omni Reference:** up to 15 assets (10 images, 5 videos ≤30 s, 7 elements incl. 3 video elements, 3 voice profiles) [OFFICIAL S1]; on Higgsfield: images, videos and `kling_element_ids`, no voice profiles [HF S2].
- **Keyframes:** Kling takes up to 10 and middle frames "at any position in the timeline" [OFFICIAL S1]; Higgsfield exposes `start_image` and `end_image` only [HF S2].
- **Creative Recreation** and **precise video editing** ("character expressions, body movements, camera positions, camera movements, overall style, video backgrounds") [OFFICIAL S1].
- **Audio:** stereo, nine languages, dialects and accents, lip sync; always on [OFFICIAL S1].
- **Text:** multilingual text, emojis and logos [OFFICIAL S1] (this command never uses emojis).
- **Prompt expansion** of short prompts; prompts up to 8,000 tokens [OFFICIAL S1].
- **Styles:** "cinematic, retro DV, animation, felt, fantasy, and cyberpunk" [OFFICIAL S1].
- **Not on Higgsfield:** 4K, 10-bit HDR (coming soon), video extension to 2 minutes (coming soon), voice profiles, Kling 4.0 Flash as its own id [OFFICIAL S1; HF S2].

## 7. Model-specific pre-generation checklist

- [ ] `mode` matches the `medias` (`text-to-video` | `image-to-video` | `reference-to-video` | `video-edit`); frames never ride with references.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"` (the default is 1080p); frames exactly 9:16 at 720×1280; an edit source already 9:16; `awl.py conform` afterwards (§2.6).
- [ ] `duration` a whole number 3–30, matching the prompt's stated length; a source up to the live maximum is one generation.
- [ ] Video quota: video references + edit clips + video elements ≤5 clips and ≤30 s, each clip ≥3 s; ≤10 images; ≤15 assets in total.
- [ ] Every reference has a role and a preserve-list (`@Image1 defines …; preserve …`), and a "never inherit" scope where it carries more than its job; the same order in every clip.
- [ ] FORMAT MODE: the continuous-take sentence for a take, or the planned shots with their cut times.
- [ ] SCENE CONTEXT opens with "EXACTLY <n> … — NO DUPLICATES"; POSITIVE CONSTRAINTS restate the counts.
- [ ] ACTION TIMING in decimal-second rows: each hand's job, the part and contact point of every use, counts and states restated after exits, occlusions and cuts; one exclusion per product for its own wrong use and count (`reference/anomaly-catalog.md` §3).
- [ ] LOCATION MAP fixes sides; CAMERA gives distance, height, rig and one move; LIGHTING one key source with the product's highlight, reflection and contact shadow.
- [ ] Size relation from the reckoning written as a check; the size risk in the brief (§3.14).
- [ ] AUDIO: dialogue in quotes in its language with the voice described, or "No dialogue, no voice-over"; "No background music" unless music is wanted.
- [ ] Clean-plate line (§3.11 b); surfaces described plain; reference text excluded; edits: "Edit @Video1" + keep-list, text removal as its own first pass.
- [ ] Prompt length within the limit the first request shows (§2.5 item 10), with no clean-plate, count or continuity line cut.
- [ ] `get_cost: true` preflight done.

## 8. Sources

- S1 [OFFICIAL] Kling AI — "Kling 4.0 User Guide" (dated 2026-11-04; release overview, specifications, Flash, entry points, prompt principles, Omni Reference limits and prompt structure, multimodal reference examples, long-form and multi-shot, video editing, Creative Recreation, audio and languages, text generation, stylized generation, keyframes, FAQ) — https://kling.ai/quickstart/kling-4-model-user-guide (accessed 2026-11-06; read in full from the page HTML)
- S2 [HF] Higgsfield live catalog — `models_explore {action:"get", model_id:"kling4_0"}` (modes, `resolution` 720p/1080p default 1080p, `duration` 3–30 whole seconds default 10, `kling_element_ids` up to seven, roles `start_image` / `end_image` / `image_references` / `video_references`, ratios 21:9 / 16:9 / 9:16 / 1:1 / auto, tags incl. `keyframes`, no audio parameter, unlim not available) and `models_explore {action:"search", query:"kling 4"}` (no separate Flash id; `hf_mult_replace_object_flash` "(Kling 4.0)"), 2026-11-06
- S3 [HF] Higgsfield MCP `generate_video` tool contract (call keys, integer `duration` snapped or clamped, `medias[].value` = media id or job id, `get_cost`, no prompt length stated), read 2026-11-06; the library's record of the Higgsfield contract, `AWL/higgsfield/higgsfield-mcp.md` §5–§7
- S4 [HF] Higgsfield blog — "Kling 4.0 on Higgsfield" (2026-10-20; References / Frames / Edit video tabs, 3–30 s, 720p/1080p, ratios incl. 21:9, references and keyframe counts, stereo, text in nine languages, edit limits, prompting tips, two conflicting credit tables) — https://higgsfield.ai/blog/kling-4-0-on-higgsfield (accessed 2026-11-06)
- S5 [SECONDARY] fal.ai — Kling 4 page (endpoints, `@Image1` / `@Video1` / `@Element1`, keyframe mode with up to 10 images in order, elements, voice elements, edit examples) — https://fal.ai/kling-4 (accessed 2026-11-06)
- S6 [SECONDARY] useapi.net — "How to Generate Kling 4.0 Video via the Kling API" (2026-10-18, updated 2026-11-05; audio always on and `enable_audio` not accepted, a 16:9 720p output measured 1280×720 with two-channel AAC, `negative_prompt` / `cfg_scale` not applicable, per-shot fields capped at 15 s, free-plan watermark) — https://useapi.net/docs/articles/kling-4-api (accessed 2026-11-06)
- S7 [SECONDARY] WaveSpeed — Kling 4.0 reference-to-video API page (`@Image1` / `@Video1` / `@Audio1` by type and position, `keep_original_sound` default false, `auto` follows references) — https://wavespeed.ai/models/kwaivgi/kling-v4.0/reference-to-video (accessed 2026-11-06)

## 9. Open questions / unverified behaviour

- **Mode routing:** does Higgsfield infer `mode` from the `medias`, reject media that do not fit the mode, or drop them silently? Is `start_image` + `image_references` in one call rejected (Kling: the entry points cannot combine)?
- **Reference numbering:** does `@ImageN` / `@VideoN` follow the `medias` order within each role on Higgsfield, also when roles are interleaved?
- **Frame naming:** in `image-to-video`, are `start_image` / `end_image` addressable as `@Image1` / `@Image2`, or only as "the first frame" / "the last frame"? Is `end_image` alone accepted (Kling supports a last frame only)?
- **Middle keyframes:** the catalog says "ordered keyframes" and tags `keyframes`, but lists no role for frames between the first and the last. Can several ordered images reach Kling's keyframes (for example as `image_references` in `image-to-video`)?
- **Elements:** how does a prompt cite `kling_element_ids` (`@Element1` by array order, `<<<element_id>>>`, a name)? Do Higgsfield reference-element UUIDs work like Kling elements, and can a voice-bound element carry a voice?
- **Audio:** confirm on the first output that a stereo track is always present and cannot be suppressed; does a video reference's own sound leak into the output?
- **Output:** exact pixel size and frame rate at 9:16 / 720p (720×1280 expected); behaviour of `aspect_ratio:"9:16"` with a non-9:16 start frame or edit source.
- **Edit length and billing:** in `video-edit`, does the output follow the source length or `duration`? How is a 5-clip edit billed? Is the source's audio kept by default?
- **Prompt limit:** Higgsfield's character cap for this id (Kling: 8,000 tokens); truncation or rejection when exceeded.
- **Continuous takes:** does the FORMAT MODE continuous-take sentence reliably suppress the default multi-shot? Do written shot lists cut at the written times?
- **Text:** spelling accuracy of new in-frame text, and whether "no subtitles" fully suppresses default subtitles.
- **Size:** does a placed product follow written size relations on this model (§3.14)?
- **Cost:** which of Higgsfield's two credit tables holds, and how much each added reference costs (`get_cost` per request).
- **Prompt expansion:** does Higgsfield leave Kling's expansion on, and does it ever override a complete prompt?
