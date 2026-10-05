---
guide: gemini-omni-flash
title: Google Gemini Omni Flash (1.0 preview) and Gemini Omni 1.1 Flash
provider: Google DeepMind (Gemini API / Gemini Enterprise Agent Platform)
higgsfield_model_ids: [gemini_omni, gemini_omni_flash_1_1]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# Gemini Omni Flash / Gemini Omni 1.1 Flash — model engineering guide

> Scope: Gemini Omni is Google DeepMind's any-input → video family: text, images and video in; video with
> native audio out; editing by instruction. This file covers `gemini_omni` ("Gemini Omni Flash") and
> `gemini_omni_flash_1_1` ("Gemini Omni Flash 1.1"). On Higgsfield:
> - both ids: text-to-video, image/video-reference generation and video editing (**Edit Mode**);
> - 1.1 only: explicit start/end frames and a required `mode` switch.
>
> Google's multi-turn memory, scene extension, audio references and negative-prompt field are **not
> exposed on Higgsfield**. /analyze-then-pick renders **9:16 at 720p** (§2.6); visible text is
> mode-dependent (§3.11). The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **What it is.** "Gemini Omni Flash is our next step towards models that can create and edit anything from any input—starting with video" [OFFICIAL: model card]. It is a transformer with "native multimodal support for text, vision, video and audio inputs" [OFFICIAL]. It was announced at Google I/O on 2026-05-19 [OFFICIAL: blog.google].
- **Name mapping (evidence-based).**
  - `gemini_omni` = Gemini Omni Flash preview, `gemini-omni-flash-preview`. Released to the Gemini API on 2026-06-30 for "3–10 second videos at 720p". Google states it "only supports '720p'", which matches the Higgsfield entry [OFFICIAL][HF].
  - `gemini_omni_flash_1_1` = Gemini Omni 1.1 Flash, `gemini-omni-1.1-flash` (GA 2026-08-27; Agent Platform `gemini-omni-1.1-flash-preview`). Its resolutions (360p/720p/1080p/4k) and `mode` values (`text_to_video`, `image_to_video`, `reference_to_video`, `edit`) match Google's `task` [OFFICIAL][HF]. The model card "describes Gemini Omni Flash and Gemini Omni 1.1 Flash" [OFFICIAL]. Higgsfield writes the version after "Flash"; same model.
- **Lifecycle warning.** "The existing gemini-omni-flash-preview endpoint will be deprecated on September 30, 2026" (today) on the Gemini API [OFFICIAL]. The Agent Platform lists retirement on 2027-06-30 [OFFICIAL]. Prefer `gemini_omni_flash_1_1`; re-check the catalog before using `gemini_omni` [INFERRED].
- **Best for:**
  - Edit Mode: removing, swapping, restyling or relighting inside a supplied clip [OFFICIAL];
  - reference-driven generation [OFFICIAL];
  - world knowledge and physics [OFFICIAL];
  - short in-scene text that is actually wanted [OFFICIAL, with caveats];
  - 10-second clips [HF].
- **Weaker at:**
  - "maintaining complete consistency throughout edits, generating scenes with complex motion, or rendering perfectly accurate text" [OFFICIAL: model card];
  - multi-element interaction edits [HF];
  - peak photoreal quality compared with Veo 3.1 [HF];
  - it cuts to several shots by default [OFFICIAL].
- **Choose this model when** you need an edit of a supplied clip that keeps its motion, reference-based identity or product placement, or short scene text. **Choose another model when** you need clips over 10 s, edit sources over 10 s, audio references, new dialogue inside an edit (speech editing is restricted [OFFICIAL]), or maximum photoreal fidelity.

| Operation | `gemini_omni` | `gemini_omni_flash_1_1` |
|---|---|---|
| Text-to-video | prompt only; the model infers the task [OFFICIAL] | `mode:"text-to-video"` |
| Start (+ end) frame | Only via `image_references` plus "Use this image as the starting frame." [OFFICIAL wording; honouring unverified] | `mode:"image-to-video"` + `start_image` (+ `end_image`) |
| Reference-to-video | `image_references` / `video_references` | `mode:"reference-to-video"` |
| Video edit (Edit Mode) | `video_references` = source + edit instruction | `mode:"edit"` + `video_references` (+ optional `image_references`) |
| Extension, multi-turn, audio references | N/A on Higgsfield | N/A on Higgsfield |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `gemini_omni` | `duration` | 4–10 (s) | 8 | Google allows 3–10 [OFFICIAL] |
| `gemini_omni` | `resolution` | `720p` | `720p` | Only option [HF][OFFICIAL] |
| `gemini_omni` | `aspect_ratio` | `16:9`, `9:16` | not stated | If unset, Google infers it from the prompt [OFFICIAL]. Always `9:16` here |
| `gemini_omni_flash_1_1` | `mode` | `text-to-video`, `image-to-video`, `reference-to-video`, `edit` | **required** | Google: "using the task field adds some constraints" [OFFICIAL] |
| `gemini_omni_flash_1_1` | `duration` | 3–10 (s) | 8 | "Ignored in edit mode, which uses the source video duration capped at 30 seconds" [HF] |
| `gemini_omni_flash_1_1` | `resolution` | `360p`, `720p`, `1080p`, `4k` | `720p` | "1080p and 4K outputs are generated using upscaling" [OFFICIAL]. Always `720p` here |
| `gemini_omni_flash_1_1` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` |
| both | negative prompt, seed, temperature, audio toggle | not exposed | — | Google supports none of the first three for Omni: "put your negatives in the regular prompt: e.g., 'Do not do X'" [OFFICIAL] |

`gemini_omni` supports Higgsfield unlimited generations (`supports_unlim: true`). Send `use_unlim` only on the user's explicit request [HF].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (1.1 only) | First frame, `<FIRST_FRAME>` [OFFICIAL] | 1 | `mode:"image-to-video"` |
| `end_image` (1.1 only) | Last frame, `<LAST_FRAME>`: "Must be used with <FIRST_FRAME>" [OFFICIAL] | 1 | "image_to_video task with up to 2 images" [OFFICIAL] |
| `image_references` (both ids) | Subject, object, style or environment references (`<IMAGE_REF_N>`) [OFFICIAL] | Google up to 10 per prompt [OFFICIAL]; Higgsfield "up to 7" [HF] | Use ≤7. PNG/JPEG/WebP/HEIC/HEIF, ≤20 MB [OFFICIAL] |
| `video_references` (both ids) | Reference clips (`<VIDEO_REF_N>`) in reference mode; the **source clip** in edit mode [OFFICIAL][INFERRED] | Reference: "maximum of 3 clips, up to 3 seconds each"; their audio "is ignored" [OFFICIAL]. Edit source: uploads "must be 10 seconds or less" [OFFICIAL]; Higgsfield caps at 30 s [HF] | Exactly one video in edit mode |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 3–10 s on 1.1, 4–10 s on 1.0 [HF]. Flow offers 4/6/8/10 s [OFFICIAL]. Out-of-range values snap or clamp [HF].
- **Resolution:** 720p is native. 1080p/4k are upscales; 360p is a cheaper draft tier [OFFICIAL]. The fixed format uses 720p only.
- **Aspect ratio:** 16:9 or 9:16 [OFFICIAL][HF].
- **Audio:** always generated; the model "will try to generate an appropriate audio track" [OFFICIAL]. To shape it, describe it. For silence, strip the track locally. Voice editing is unsupported, and speech-changing in edits is restricted [OFFICIAL].

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"text-to-video","prompt":"<PROMPT>","duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Start frame → video (1.1; the start frame is already 9:16):
```json
{"model":"gemini_omni_flash_1_1","mode":"image-to-video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"resolution":"720p","aspect_ratio":"9:16"}
```
First + last frame (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"image-to-video","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Reference-to-video (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"reference-to-video","prompt":"<REFERENCE_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Edit Mode (1.1; the source is pre-conformed to 9:16 and ≤10 s; `duration` is ignored):
```json
{"model":"gemini_omni_flash_1_1","mode":"edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID>","role":"image_references"}],"resolution":"720p","aspect_ratio":"9:16"}
```
Edit Mode or references (`gemini_omni`; the prompt states the job explicitly):
```json
{"model":"gemini_omni","prompt":"<PROMPT WITH EXPLICIT ROLE SENTENCE>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Preflight with the same params plus `get_cost: true` [HF]. A completed job ID can be passed back as `video_references` for a second edit pass [HF][INFERRED].

### 2.5 Parameter gotchas

1. **Edit-source length conflict.** Google: uploaded edit inputs ≤10 s; the Agent Platform model page lists 10 s maximum; Flow edits "Up to 10s" [OFFICIAL]. Higgsfield: capped at 30 s [HF]. Trim to ≤10 s locally, and edit longer clips in ≤10 s segments at cut points [INFERRED].
2. **`mode` constrains the model** [OFFICIAL]. Match it to the media you send [INFERRED].
3. **Multiple videos.** Google lists both "maximum of 3 clips" and "Referencing or reasoning across multiple videos is not supported" [OFFICIAL]. Send one video when possible.
4. **Stateless calls.** There is no `previous_interaction_id` memory on Higgsfield, so drift compounds across chained edits. Keep chains short [INFERRED].
5. **Restrictions.** No "certain recognizable people". Minors and uploaded-video edits are restricted in the EEA, CH and UK [OFFICIAL].
6. **Deprecated 1.0 endpoint** (see §1).

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `gemini_omni` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` | Native 720p [OFFICIAL]. Pixel size 720×1280 expected but undocumented [INFERRED] | None if 720×1280; otherwise `atp.py conform` (downscale, or scale-to-fill plus minimal crop; never stretch) | Edit: reframe the source to 9:16 (720×1280) with `atp.py conform` before upload. References can be any ratio, but keep subjects uncropped |
| `gemini_omni_flash_1_1` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` (never 360p/1080p/4k) | Native 720p; 1080p/4k would only be upscales [OFFICIAL]. 720×1280 expected [INFERRED] | Same rule | `image-to-video`: start and end frames conformed to 9:16. `edit`: source conformed to 9:16 and still send `"9:16"`. The output likely follows the source [INFERRED] |

ffprobe the first output per session and log the dimensions [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Elements** (DeepMind): shot framing and motion, style, lighting, location, action [OFFICIAL]. Gemini API: "Write prompts with details like scene description, camera movement, lighting and mood" [OFFICIAL]. The Agent Platform guide covers "Gemini Omni Flash and Veo" with the same anatomy [OFFICIAL].
- **Less prescriptive than Veo.** "With Veo, you need to share precise instructions… with Gemini Omni, you don't have to be as prescriptive" [OFFICIAL]. State the intent, plus the locks that matter.
- **Meta prompts** such as "Consider micro-detail, expression and timing to create a very rich, detailed but entirely natural scene." [OFFICIAL]
- **Edits:** "Simple prompts work best for video editing. Overly descriptive prompts can lead to unintended changes" [OFFICIAL].
- **Language and length.** English is fully supported [OFFICIAL]. Generation: 40–150 words. Edits: 1–3 sentences plus "Keep everything else the same." [INFERRED from OFFICIAL]

### 3.2 Subject and identity

Bind references by tag and description, e.g. "a woman <IMAGE_REF_0> is walking" [OFFICIAL]. For dense casting: "Be extremely detailed in your descriptions of characters… Apply costume design principles" [OFFICIAL]. Specify apparent age, skin tone and hair for text-only people [INFERRED].

### 3.3 Action, motion and physical interaction

Omni "has an intuitive understanding of forces like gravity, kinetic energy and fluid dynamics" [OFFICIAL]. A complex action can be referenced without frame-by-frame description [OFFICIAL]. Complex motion is still a model-card weakness [OFFICIAL].

Rules [INFERRED]:
- one or two primary actions;
- name contact points and end states;
- give each person a stable handle (tag plus wardrobe) so identities do not swap across its default cuts.

### 3.4 Environment, lighting and style

Name the location without over-describing ("you don't need to describe every single little detail"). Name the light source and its quality. Name styles such as "anime, claymation, or watercolour" [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure

- **Default is multi-shot.** "By default Omni Flash will try to create a video with a few different shots." For one scene, prompt "In a single unbroken scene", "In a single continuous shot" or "No scene cuts" [OFFICIAL]. This is the single most important continuity rule for this model.
- **Timing.** Natural language ("After 3 seconds, a woman enters the scene") or timecodes (`[0-3s] … [3-6s] …`) [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls

No camera controls. Omni follows videography terms [OFFICIAL]:
- continuity: "one continuous shot" or "oner";
- locked camera: "static", "locked off", "fixed";
- movement: "push in", "punch in", "dolly zoom";
- capture look: "natural smartphone zoom", "film camera", "webcam style".

In edits, the camera can be changed: "Change the camera angle to be over the violinist's shoulder" [OFFICIAL].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- **Tags:** `<FIRST_FRAME>`, `<LAST_FRAME>`, `<IMAGE_REF_N>`, `<VIDEO_REF_N>` (zero-based). Declared blocks for complex cases: `[# Sources <FIRST_FRAME>@Image1] [# References <IMAGE_REF_0>@Image2]` [OFFICIAL].
- **Guiding sentences** [OFFICIAL]:
  - "Use this image as the starting frame."
  - "Use the given image(s) as references for video generation. The images should not be used as literal initial frames."
  - "Use the given video(s) as references. Do not use them as a source for video editing."
- **On Higgsfield,** the mapping from `medias` order to tags is undocumented. Pair every tag with a description, and order `medias` as they are mentioned [INFERRED].
- **What video references carry.** They supply likeness and motion; their audio is ignored [OFFICIAL]. From analyzed references, inherit subject, motion and style. Never inherit their words, usernames or watermarks [policy].
- **Audio references:** unsupported ("Uploading audio references is unsupported") [OFFICIAL]; no audio role on Higgsfield [HF].

### 3.8 Start and end frames

1.1 with `mode:"image-to-video"`. "Clearly define what is in your initial frame, specify the exact camera movement or transition path that takes place in between, and state precisely what the final frame should reveal", ending with "One continuous shot, no jump cuts" [OFFICIAL]. The same image as first and last frame makes a loop [OFFICIAL]. A lone image is one "the model will decide how to use", so state its role [OFFICIAL].

### 3.9 Audio, dialogue and sound (if supported)

- **Describe the soundtrack you want,** especially music: "Include calm background music" [OFFICIAL]. Remove unwanted layers with "No dialogue", "No extra sound effects" [OFFICIAL].
- **Dialogue: colon form without quotation marks.** Google's best-practice page, which covers "Gemini Omni and Veo", uses it "to prevent the model from rendering text in the video" [OFFICIAL]. DeepMind's Omni examples use quotes [OFFICIAL]. This library keeps quotes for intended scene text (§3.11c), so the two stay distinguishable.
- **No new or changed speech in `edit` mode** [OFFICIAL].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field anywhere. Google's documented form is short imperative negatives in the prompt: "Do not do X", "No dialogue", "No embellishments" [OFFICIAL]. Higgsfield's VFX example ends with a `FORBIDDEN:` line and "No music. No on-screen text." [HF]. Put negatives after the positive description [INFERRED].

### 3.11 Visible text

Policy recap:
- **Edit Mode:** no source text survives unless the user keeps specific text.
- **Analyze Mode:** new text is allowed, by default added in deterministic post. Omni may render scene-bound text in-frame when that is reliable.

**(a) Reliability, claims vs evidence.**
- **Claims:** "You can prompt to include text in your video and Gemini Omni will render in a way that is correct and readable" [OFFICIAL: Gemini API]. DeepMind: "render text more accurately… create it in sync with your visuals" [OFFICIAL]. A partner reports "crisper on-screen text" [OFFICIAL page, partner quote].
- **Counter-evidence:** the model card still lists "rendering perfectly accurate text" as a challenge [OFFICIAL].
- **Independent evidence:** none found.
- **Verdict:** the most text-capable model in this Google set. In-frame text is acceptable for short (1–4 words), large, scene-bound text such as a sign, a screen or packaging, with spelling QC. Exact hooks, captions and subtitles still go to post [INFERRED].

**(b) Clean plate.**
1. End with Google-style negatives: "No on-screen text. No subtitles. No captions. No logos." [OFFICIAL style]
2. Define background text surfaces as blank ("the shop sign is a plain unlettered panel; the phone screen shows abstract color only"). This applies Google's advice to "define what it should say" for naturally occurring text [OFFICIAL + INFERRED].
3. Use colon dialogue [OFFICIAL].
4. Avoid text-inviting words (label, caption, title, lower third, headline). Google's own meta example "include text to label the thing" shows the model adds labels on request [OFFICIAL].

**(c) Intentional in-frame text.** Use Google's convention: name the surface, then the exact words in double quotes. For example: `There is a street sign that says: "…"`, `a car with the number plate: "…"` [OFFICIAL]. For timed kinetic words: `One word on the screen at a time: "…" Each word appears for 1s…` [OFFICIAL]. Keep it short, early and large. Specify font style and placement only when needed ("Choose your type, placement, animation, and exposure") [OFFICIAL]. Always QC the spelling.

**(d) Edit Mode: removing source text** (`gemini_omni_flash_1_1` `mode:"edit"`; `gemini_omni` with a video reference).
- **Tendency.** Omni applies changes "while preserving elements you did not mention" [OFFICIAL], so source captions, usernames, stickers and watermarks **stay unless named**. Partial removals can leave or re-render garbled glyphs, given the text-accuracy caveat [INFERRED].
- **Most reliable wording.** Make removal its own first pass. Name each element by position and look, and say what is revealed behind it, then close with the keep-same line. No official text-removal example exists. This combines Google's edit pattern [OFFICIAL] with Higgsfield's first-party removal wording ("Remove only [target]… and reconstruct the revealed area consistently with its immediate surroundings") [HF]:
  `Remove the white caption text along the bottom of the frame, the username in the top-left corner and the semi-transparent logo in the lower-right corner, and restore the wall and floor behind them as they naturally appear. No on-screen text. Keep everything else the same.`
- **Content edits come after cleanup.** Run them as a second pass on the cleaned result, so a later pass cannot reintroduce text [INFERRED].
- **Better alternatives** [INFERRED]:
  - **Local clean-up:** small static corner marks on simple backgrounds (FFmpeg `delogo`), and caption bands that the 9:16 reframe crops away anyway.
  - **Another model:** use `flux_3_video_edit` if residue survives one retry.
  - **Regenerate the shot (Analyze Mode):** when text covers faces or products, or moves across most of the clip.

### 3.12 Character / identity consistency

- **References:** approved character images as `image_references` (tag plus description). Optionally add a ≤3 s likeness clip as `video_references`: video references "work best with likenesses" [OFFICIAL].
- **Replacing a source person (Edit Mode):** "Provide an image of a character with your video, and the new character will match your motion and dialogue seamlessly" [OFFICIAL]. Wording: `Replace the man in the grey coat with the person shown in <IMAGE_REF_0>, keeping his exact movements and timing. Keep everything else the same.` [INFERRED from OFFICIAL]
- **Restrictions and drift.** Recognizable-person images are unsupported [OFFICIAL]. Across sessions, consistency "may drift" [HF], so reuse identical references and description blocks.

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

1. **Pixel-exact opening:** 1.1 `start_image` (9:16) with the approved product; prompt the motion.
2. **Placement:** clean multi-view `image_references`, the "not literal initial frames" sentence, and explicit locks. Higgsfield reports that "The product shape does not distort" is treated "as locks rather than suggestions" [HF claim]. Google: "Be very specific about the people, items and objects in the scene" [OFFICIAL].
3. **Swap in footage:** `Replace the <old object> with the <object> from <IMAGE_REF_0>, same size in hand and same motion. Keep everything else the same.` Single-element edits are strongest [HF].
4. **Approved labels:** real product text on the reference is preserved for fidelity. Keep it large and verify it; do not ask Omni to re-letter it [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

**First-party integration wording** (Higgsfield's own Omni VFX prompt) [HF]: "LIGHT-MATCH / INTEGRATION (top priority): The real bird is lit by the room—the bright overhead LED panel light and ambient warm office lights. It must reflect the same exposure, color grade, and grain as the plate… Precise soft contact shadows of the bird and its feet must cast onto the palm."

Phrasing for inserted or replaced assets [INFERRED unless tagged]:
- **Scale:** "same size in hand as the original", "about the height of the cup beside it".
- **Orientation:** "front face toward the camera", "handle pointing right".
- **Contact and grip:** "held in her right hand by the base, fingers clear of the front"; "rests flat on the table with a soft contact shadow".
- **Occlusion:** "her fingers stay behind the object's edges"; "it passes behind the lamp and reappears unchanged".
- **Light inheritance:** "lit by the same warm window light from the left as the rest of the scene; matching exposure, color grade and grain; its shadow falls right; a faint reflection shows in the glossy tabletop" (pattern from [HF] above).
- **Persistent states:** "the lid stays open until the end", "the glass stays half full", "it stays exactly where she places it", "she keeps it in the same hand".

**Known failures:**
- consistency "throughout edits" and complex motion [OFFICIAL: model card];
- multi-element interaction edits [HF];
- drift across stateless chained edits [INFERRED].

**Across clips.** Extension is not exposed [HF]. Chain via the last good frame → 1.1 `start_image`, or edit the previous output. Keep references, description blocks and style phrases identical [INFERRED].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Single scene, Gemini API Omni guide (https://ai.google.dev/gemini-api/docs/omni):
   > Continuous, unbroken handheld shot of a fluffy tabby cat sitting on a sunny windowsill, looking out into a leafy garden. The cat's tail twitches slowly, and its ears rotate slightly toward ambient noises. Sunbeams illuminate dust motes in the air. Sound design: Gentle breeze, distant bird chirps. No dialogue.
2. Timecodes, same source:
   > [0-3s] A person is walking [3-6s] They stop and turn around [6-10s] They start running
3. Simplified edits, same source:
   > Add a cat that jumps onto his lap, he begins to pet it. Keep everything else the same. / Make the phone invisible. Keep everything else the same.
4. Declared sources and references, same source:
   > [# Sources <FIRST_FRAME>@Image1] [# References <IMAGE_REF_0>@Image2] a woman <IMAGE_REF_0> is walking. Use Image1 as the starting frame. Use Image2 as a reference for the video generation.
5. First and last frame, DeepMind Omni prompt guide (https://deepmind.google/models/gemini-omni/prompt-guide/):
   > A close-up low-angle shot of a stylish drummer in a beige suit playing a red drum kit in a grand hall transitions as the camera whip-pans to the side, revealing an older saxophonist playing alongside a ballet dancer spinning in a white outfit under soft purple stage lights. One continuous shot, no jump cuts.
6. Image as a motion guide, Gemini API:
   > turn this into realistic footage, using the drawing only as a guide for movement, do not show the drawing in the final video
7. Intended scene text, Gemini API:
   > There is a street sign that says: "This is an AI generation by Omni", there is a storefront that says: "All you need AI", there's a car with the number plate: "OMNI1.1"
8. First-party Higgsfield VFX edit [HF] (https://higgsfield.ai/blog/gemini-omni-flash-vfx-video-editing):
   > SOURCE LOCK: This is an ADD-ELEMENT VFX pass on video_1, NOT a new generation. Keep 1:1 everything already in the plate […] Only ADD the live bird and animate it. […] ANTI-SLOP: Real feather texture with high detail; lively eyes with a sharp catchlight; convincing flight physics with proper weight, acceleration, and air resistance. No robotic/CGI look, no floating, and no morphing shapes or extra limbs. […] No music. No on-screen text.

Patterns these teach:
- **Order:** continuity phrase first ("Continuous, unbroken … shot"), then subject, micro-actions, ambient detail, a `Sound design:` label, and short negatives last (1).
- **Sentence style:** short declarative sentences. Edits are one imperative sentence plus "Keep everything else the same." (3).
- **Time:** `[0-3s]` timecodes with one action per segment (2).
- **Subject vs camera:** camera path stated as the transition ("transitions as the camera whip-pans…") separate from subject action (5).
- **References:** declared blocks and inline tags, then guiding sentences at the end (4). Intent words for how an image is used ("only as a guide for movement, do not show the drawing") (6).
- **Detail:** 10–70 words; less prescriptive than Veo. Higgsfield's long, block-structured prompt (8) is its own style for complex VFX, and runs against Google's "simple prompts" edit advice.
- **Exclusions:** "No dialogue." / "Do not do X" (1, 8).
- **Scene text:** `says: "<exact words>"` (7).

### 4.1 Text-to-video

Follows patterns 1–2 and 7.
```text
In a single continuous shot, <camera framing and move>. <Subject with appearance> <micro-actions in order, or
[0-3s]/[3-6s]/[6-10s] beats>. <Location, time, light source>. <Style>. Sound design: <ambience/SFX/music>.
<Speaker> says: <line without quotation marks> | No dialogue. <Blank-surface clause>. No on-screen text. No subtitles.
No captions.
```
Example (`mode:"text-to-video"`, 8 s, 9:16):
```text
In a single continuous shot, a slow push-in at table height. An orange tabby cat stalks along a sunlit kitchen
counter, pauses beside a glass of water, taps it once with a paw so the water ripples, then sits beside it while the
glass stays upright. Late-morning light from a side window, soft shadows to the right, natural documentary look, real-
time pace. Sound design: quiet kitchen ambience, a light tap of paw on glass, distant birdsong. No dialogue. Cupboards
and appliances are plain and unlabeled. No on-screen text. No subtitles. No captions.
```

### 4.2 Start frame (and end frame) to video

Follows patterns 1 and 5 (initial frame → path → final reveal).
```text
<Camera movement>. <What moves, general terms, in order>. <What stays fixed>. Sound design: <…>. One continuous
shot, no jump cuts. No on-screen text.
```
Example (`mode:"image-to-video"`, start_image = approved 9:16 still of a person at a desk with a laptop):
```text
Slow push-in from medium to medium close-up. The woman looks up from the laptop, smiles, and closes the lid with both
hands; the laptop stays flat on the desk with its exact shape and proportions. Dust motes drift through the window
light. Sound design: soft room tone and the muted click of the lid. No dialogue. One continuous shot, no jump cuts.
No on-screen text.
```
First + last example: `The first frame shows a closed cardboard box on a workbench; the camera stays locked off while the lid flaps open and a small wind-up toy climbs out, ending exactly on the final frame of the toy standing beside the open box. One continuous shot, no jump cuts. No on-screen text.`

### 4.3 Reference-to-video

Follows pattern 4 (declared blocks, tags plus description, guiding sentences last).
```text
[# References <IMAGE_REF_0>@Image1 <IMAGE_REF_1>@Image2] In a single continuous shot, <scene and camera>. <Person
description> <IMAGE_REF_0> <action> with the <object description> <IMAGE_REF_1>. <Locks: exact shape, proportions,
color, material; identity>. <Light inheritance>. Sound design: <…>. No on-screen text. No subtitles. Use the given
images as references for video generation. The images should not be used as literal initial frames.
```
Example (two image references):
```text
[# References <IMAGE_REF_0>@Image1 <IMAGE_REF_1>@Image2] In a single continuous shot, a slow tracking shot along a
city sidewalk at golden hour. The young man with short curly hair <IMAGE_REF_0> walks toward camera carrying the
compact silver thermos <IMAGE_REF_1> in his left hand and unscrews its cap. The thermos keeps its exact cylindrical
shape, proportions and brushed-metal finish, lit by the same warm low sun as the street. Sound design: footsteps,
light traffic, a soft metallic twist. No dialogue. No on-screen text. No subtitles. Use the given images as references
for video generation. The images should not be used as literal initial frames.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

Follows pattern 3: one operation, short, then "Keep everything else the same." Run text removal as pass 1 (§3.11d).
```text
<One operation, 1–2 sentences, with placement/scale/light details only if the edit needs them>. <Reference binding
if any>. Keep everything else the same.
```
Examples:
- `Remove the white caption text along the bottom of the frame and restore the table surface behind it. No on-screen text. Keep everything else the same.`
- `Replace the red mug in her hand with the ceramic mug from <IMAGE_REF_0>, same size and same motion, lit by the same window light. Keep everything else the same.`
- `Change the lighting to warm late-afternoon sun from the left. Keep everything else the same.`

Motion transfer (Google-documented intent) [OFFICIAL]: `Apply the pose and motion from <VIDEO_REF_0> to the character from <IMAGE_REF_0>. Use the given video as a reference. Do not use it as a source for video editing.` Extension: N/A on Higgsfield.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Unmotivated cuts (slop) | Multi-shot default [OFFICIAL] | "In a single continuous shot / No scene cuts" |
| Unintended changes in edits (untouched regions morph) | Long, descriptive edit prompts [OFFICIAL] | One operation plus "Keep everything else the same."; separate passes |
| Source text survives an edit | Not named (preserved by design) [OFFICIAL] | Dedicated removal pass naming every element (§3.11d) |
| Garbled or unwanted text | Text-inviting words; accuracy caveat [OFFICIAL] | Blank-surface clause, "No on-screen text…", colon dialogue; scene text via `says: "…"` |
| Morphing shapes, floating, extra limbs | Complex motion or insertion [OFFICIAL model card] | Higgsfield ANTI-SLOP line: "No robotic/CGI look, no floating, and no morphing shapes or extra limbs" [HF]; contact shadows |
| Dead space or arbitrary slow motion | Duration longer than the action; unpaced prompt [INFERRED] | Pick duration 3–10 to fit; timecodes; "real-time pace" |
| Sudden speed changes | Several moves or beats without timing [INFERRED] | Timecoded beats; one camera move |
| Identity drift or clothing changes | Default cuts, text-only people, stateless chains [INFERRED] | Single shot; references plus description; short chains |
| Duplicated objects | Object described twice, no count [INFERRED] | "a single …", then "the same …" |
| Reference shown as a literal frame | Ambiguous image role [OFFICIAL] | "should not be used as literal initial frames" |
| Wrong reference bound | Undocumented tag mapping [INFERRED] | Tag plus description; consistent `medias` order |
| Unwanted music or speech | Automatic soundtrack [OFFICIAL] | Describe audio; "No dialogue"; strip in post |
| Rejected request | Recognizable people, minors, region, edit source over 10 s [OFFICIAL] | Approved adult references; trim to ≤10 s |

## 6. Model-specific features and controls

- **Mode switch (1.1)** ↔ Google `task` [HF][OFFICIAL].
- **Resolution ladder:** 360p/720p/1080p/4k; only 720p is used here [OFFICIAL].
- **Instruction editing:** swap, add, remove, restyle, relight, re-camera, retime [OFFICIAL].
- **Prompt tags and declared blocks; meta prompting; world knowledge** [OFFICIAL].
- **Thinking** (the model reasons before generating) [OFFICIAL: Agent Platform]; no parameter.
- **SynthID and C2PA** [OFFICIAL].
- **Not exposed:** extension, multi-turn memory, custom voices [OFFICIAL][HF].

## 7. Model-specific pre-generation checklist

- [ ] `gemini_omni_flash_1_1` preferred; `gemini_omni` availability re-checked (upstream deprecation 2026-09-30).
- [ ] `aspect_ratio: "9:16"`, `resolution: "720p"`; `mode` matches the media.
- [ ] Edit Mode: source conformed to 9:16, ≤10 s, one video; text-removal pass first; "Keep everything else the same."
- [ ] Start/end frames conformed to 9:16; references ≤7, each bound by tag plus description; guiding sentence present.
- [ ] "Single continuous shot / No scene cuts" unless cuts are wanted; duration fits the action.
- [ ] Integration: scale, grip, contact shadow, light inheritance, persistent states; ANTI-SLOP line for inserts.
- [ ] Text: clean-plate negatives; intentional scene text as `says: "…"` (short) or in post; colon dialogue.
- [ ] `get_cost` done; output probed (720×1280) and QC'd (text residue, identity, geometry, cuts).

## 8. Sources

- [OFFICIAL] Generate and edit videos with Gemini Omni Flash, Gemini API (updated 2026-09-23) — https://ai.google.dev/gemini-api/docs/omni — accessed 2026-09-30
- [OFFICIAL] Video generation overview, Gemini API — https://ai.google.dev/gemini-api/docs/video — accessed 2026-09-30
- [OFFICIAL] Gemini API changelog (2026-06-30 preview; 2026-08-27 GA) — https://ai.google.dev/gemini-api/docs/changelog — accessed 2026-09-30
- [OFFICIAL] Gemini API deprecations — https://ai.google.dev/gemini-api/docs/deprecations — accessed 2026-09-30
- [OFFICIAL] Gemini Omni 1.1 Flash Preview model page (Agent Platform) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/omni-1-1-flash — accessed 2026-09-30
- [OFFICIAL] Gemini Omni Flash Preview model page (Agent Platform) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/omni-flash-preview — accessed 2026-09-30
- [OFFICIAL] Video generation prompt guide ("Gemini Omni Flash and Veo") — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide — accessed 2026-09-30
- [OFFICIAL] Best practices for generating videos (Gemini Omni and Veo) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice — accessed 2026-09-30
- [OFFICIAL] Agent Platform video pages (text, references, first/last frames, edit, extend) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/overview — accessed 2026-09-30
- [OFFICIAL] Gemini Omni model page (DeepMind) — https://deepmind.google/models/gemini-omni/ — accessed 2026-09-30
- [OFFICIAL] How to create effective prompts with Gemini Omni (DeepMind) — https://deepmind.google/models/gemini-omni/prompt-guide/ — accessed 2026-09-30
- [OFFICIAL] Gemini Omni Flash model card (covers Omni Flash and Omni 1.1 Flash) — https://deepmind.google/models/model-cards/gemini-omni-flash/ — accessed 2026-09-30
- [OFFICIAL] Introducing Gemini Omni (blog.google, 2026-05-19) — https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-omni/ — accessed 2026-09-30
- [OFFICIAL] Google Flow Help: models & supported features — https://support.google.com/flow/answer/16352836 — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract; first-party edit-prompt contract (removal wording) — higgsfield/first-party/ad-multiplier-prompt-writer.md — accessed 2026-09-30
- [HF] How to Use Gemini Omni Flash for VFX and Video Editing (Higgsfield blog) — https://higgsfield.ai/blog/gemini-omni-flash-vfx-video-editing — accessed 2026-09-30
- [HF] How to Use Gemini Omni Flash for Multi-Shot AI Video Production (Higgsfield blog) — https://higgsfield.ai/blog/how-to-use-gemini-omni-flash-multi-shot-video — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- Whether `gemini_omni` still routes to `gemini-omni-flash-preview` after its Gemini API deprecation (2026-09-30), is served by 1.1, or fails.
- Exact output dimensions at 720p 9:16 (720×1280 expected), and whether edit output follows the source ratio or the sent `aspect_ratio`.
- Whether `gemini_omni` honours image inputs as a first frame. The Agent Platform lists image-to-video and references as unsupported for the 1.0 preview; the Gemini API changelog says it can "animate still images".
- How Higgsfield maps `medias` to `<IMAGE_REF_N>`/`<VIDEO_REF_N>`, and whether Google tag syntax passes through.
- Edit-source limit: Higgsfield says 30 s, Google 10 s. Does Higgsfield segment longer clips?
- Removal quality for burned-in and animated captions, stickers and UI overlays. There is no official text-removal example.
- Real reference ceiling (7 vs 10), and whether `image_references` are accepted with `start_image` in `image-to-video` mode.
