---
guide: veo-3-1
title: Google Veo 3.1 and Veo 3.1 Lite
provider: Google DeepMind (served through the Gemini API and Gemini Enterprise Agent Platform, formerly Vertex AI)
higgsfield_model_ids: [veo3_1, veo3_1_lite]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# Google Veo 3.1 / Veo 3.1 Lite — model engineering guide

> Scope: Veo 3.1 is Google DeepMind's video model with natively generated, synchronized audio. This file
> covers `veo3_1` (Veo 3.1; "preview" = best quality, "fast" = faster) and `veo3_1_lite` (Veo 3.1 Lite,
> the budget tier). On Higgsfield both ids do text-to-video and start-frame animation; `veo3_1_lite` also
> does first-and-last-frame interpolation. Google-native reference images ("ingredients"), extension,
> negative prompt, seed, explicit resolution and object add/remove are **not exposed on Higgsfield**.
> /analyze-then-generate always renders **9:16 at 720p** (§2.6). Visible text is mode-dependent (§3.11).
> Neither id can edit video, so Edit-Mode jobs route to an edit-capable model.
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** "Veo 3.1 is a model for generating 8-second videos (720p, 1080p, or 4k) with natively generated audio" [OFFICIAL: Gemini API]. Google Cloud: Veo 3.1 builds on Veo 3 "with stronger prompt adherence and improved audiovisual quality when turning images into videos" [OFFICIAL: Cloud blog]. Veo 3.1 Lite: "Google's most cost-effective video model", at "less than 50% of the cost of Veo 3.1 Fast, but with the same speed" [OFFICIAL: blog.google]. Higgsfield labels: `veo3_1` "Ultra-realistic, top-tier cinematic quality"; `veo3_1_lite` "Fast, affordable, budget batch clips" [HF].
- **Lifecycle warning.** On the Gemini API, `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview` and `veo-3.1-lite-generate-preview` list shutdown **2026-10-22**, replaced by `gemini-omni-1.1-flash` [OFFICIAL: deprecations page, updated 2026-09-30]. The Agent Platform GA ids list "November 17, 2026 or later"; Lite is Preview [OFFICIAL]. Higgsfield does not publish its backend, so re-check `models_explore` before each run [INFERRED].
- **Best for:**
  - photoreal single shots with synchronized dialogue, SFX and ambience [OFFICIAL];
  - direction through film vocabulary; Google calls cinematography "the most powerful tool for conveying tone and emotion" [OFFICIAL];
  - animating a prepared 9:16 start frame;
  - timestamped mini-sequences inside 8 s [OFFICIAL];
  - cheap drafts on Lite.
- **Weaker at:**
  - generated text: Veo 3 is "still poor at generating text" [OFFICIAL: tech report];
  - consistency in complex scenes or motion [OFFICIAL: model card];
  - subtitle artifacts on dialogue [SECONDARY];
  - short speech segments [OFFICIAL];
  - anything over 8 s;
  - reference-based identity (not exposed) [HF].
- **Choose this model when** the shot fits 4–8 s, photoreal quality with native audio matters, and exact products or people arrive via a clean start frame. **Choose another model when** you need reference images, video editing (Edit Mode), clips over 8 s, reliable in-frame text, or several consecutive actions.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | `veo3_1` / `veo3_1_lite`, no `medias` | 4/6/8 s [HF] |
| Start frame → video | `start_image` on either id | The image becomes the first frame [OFFICIAL] |
| First + last frame | `veo3_1_lite` with `start_image` + `end_image` | `veo3_1` has no `end_image` role [HF] |
| Reference images, extension, add/remove object, edit | N/A on Higgsfield | Google-native only [OFFICIAL][HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `veo3_1` | `duration` | 4, 6, 8 | 8 | Seconds. An unsupported value snaps to the nearest allowed value or is clamped [HF] |
| `veo3_1` | `quality` | `basic`, `high`, `ultra` | `basic` | "Output quality tier" [HF]; resolution mapping unpublished (§2.6) |
| `veo3_1` | `variant` | `veo-3-1-preview`, `veo-3-1-fast` | `veo-3-1-fast` | "preview = best quality, fast = faster generation" [HF] |
| `veo3_1` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` here |
| `veo3_1_lite` | `duration` | 4, 6, 8 | 8 | Same snapping rule [HF] |
| `veo3_1_lite` | `generate_audio` | bool | **false** | Silent unless set to true [HF] |
| `veo3_1_lite` | `aspect_ratio` | `16:9`, `9:16`, `auto` | not stated | Always `9:16` here (not `auto`) |
| both | `prompt` | string | — | Google text limit: 1,024 tokens [OFFICIAL] |
| both | negative prompt, seed, resolution, sample count, person-generation, resize mode | not exposed | — | [HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (`veo3_1`, `veo3_1_lite`) | "Veo uses the input image as the initial frame" [OFFICIAL] | 1 | Google recommends ≥720p at 16:9 or 9:16. Other ratios "may be resized or centrally cropped" [OFFICIAL]. JPEG/PNG, ≤20 MB [OFFICIAL] |
| `end_image` (`veo3_1_lite` only) | Final frame (Google `lastFrame`, "must be used in combination with the image parameter") [OFFICIAL] | 1 | Always pair with `start_image` |

Values are Higgsfield media UUIDs or completed job IDs, never URLs. The server may auto-coerce unambiguous roles [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 4, 6 or 8 s [HF][OFFICIAL]. Google requires 8 s for 1080p, 4k and reference images [OFFICIAL]; that does not constrain 720p work.
- **Resolution:** Veo 3.1 offers 720p/1080p/4k. Lite has no 4k [OFFICIAL]. The Agent Platform lists Fast at 720p/1080p, while the Gemini API lists 4k for "Veo 3.1 & Veo 3.1 Fast" [OFFICIAL, conflicting]. On Higgsfield, resolution is reachable only via `quality` (`veo3_1`); Lite has no control [HF].
- **Frame rate:** 24 fps [OFFICIAL].
- **Aspect ratio:** 16:9 or 9:16; portrait is native [OFFICIAL].
- **Audio:** "Always on" for all Veo 3.x on the Gemini API [OFFICIAL]. `veo3_1` has no flag, so expect sound every time [INFERRED]. Lite: `generate_audio` (default false) [HF].

### 2.4 Call recipes

All recipes use the fixed output format (§2.6).

Text-to-video (`veo3_1`, draft):
```json
{"model":"veo3_1","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","quality":"basic","variant":"veo-3-1-fast"}
```
Start frame → video (`veo3_1`, final pass; the start frame is already 9:16):
```json
{"model":"veo3_1","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","quality":"basic","variant":"veo-3-1-preview"}
```
Text-to-video with sound (`veo3_1_lite`):
```json
{"model":"veo3_1_lite","prompt":"<PROMPT>","duration":6,"aspect_ratio":"9:16","generate_audio":true}
```
Start frame → video, silent (`veo3_1_lite`; a completed image job can be the frame):
```json
{"model":"veo3_1_lite","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","generate_audio":false}
```
First + last frame (`veo3_1_lite`):
```json
{"model":"veo3_1_lite","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","generate_audio":false}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`. `jobs_wait` returns public MP4 URLs [HF].

### 2.5 Parameter gotchas

1. **Pre-shape start and end frames** to exactly 9:16 (at least 720×1280) with `atg.py conform` before upload. Google may center-crop or resize other ratios [OFFICIAL]. Keep the subject inside the central safe area [INFERRED].
2. **Never send `high` or `ultra` in the fixed format.** They likely map to higher resolutions, which cost more and may force 8 s [OFFICIAL coupling + INFERRED].
3. **`veo3_1` always has audio.** For silence, strip it locally (`ffmpeg -an`) [INFERRED]. Lite is silent unless `generate_audio: true` [HF].
4. **No negative prompt.** Put exclusions in the prompt (§3.10) [HF].
5. **People in frames.** Image-to-video and interpolation are "allow_adult" only. Child and prominent-person content is rejected [OFFICIAL]. Use adult, non-famous approved references only.
6. **Audio-triggered blocks.** "Veo 3.1 will sometimes block a video from generating because of safety filters or other processing issues with the audio" [OFFICIAL]. Higgsfield billing for blocked jobs is undocumented.
7. **Web app ≠ MCP.** Higgsfield's web app advertises Veo 3.1 references, start/end frames and multi-shot [HF blog]. The MCP catalog exposes only §2.2 [HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `veo3_1` | `"aspect_ratio":"9:16"`, `"quality":"basic"`. `variant`: `veo-3-1-fast` for drafts, `veo-3-1-preview` for finals | 720×1280 expected [INFERRED]. `basic` is the lowest tier and 720p is Google's default. DeepMind ran its Veo evaluations "at 720x1280 resolution" [OFFICIAL] | None if 720×1280. If larger (e.g. 1080×1920), exact downscale with `atg.py conform` | Native 9:16 request. Any start frame is reframed to 9:16 first (scale-to-fill plus minimal crop; never stretch) |
| `veo3_1_lite` | `"aspect_ratio":"9:16"` (never `auto`). No resolution parameter | 720×1280 expected: Lite supports 720p/1080p, and 720p is the default [OFFICIAL + INFERRED] | Same rule | 9:16 start and end frames, both from the same source |

Always ffprobe the first output of a session. Record the dimensions in run notes and conform if they are not 720×1280 [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Formula:** `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]` [OFFICIAL: Cloud blog]. The Gemini API lists Subject, Action, Style, plus optional Camera, Composition, Focus/lens and Ambiance [OFFICIAL].
- **Prose.** "Use descriptive language: Use adjectives and adverbs to paint a clear picture" [OFFICIAL]. Audio goes in "separate sentences" [OFFICIAL].
- **Length.** "The more detail you add, the more control you'll have" [OFFICIAL], up to 1,024 tokens [OFFICIAL]. But chaining "multiple distinct events (A then B then C)… often leads to muddled or incomplete videos" [OFFICIAL]. Targets: 60–150 words for text-to-video, 25–70 for start-frame prompts [INFERRED].
- **Language.** English is fully supported; others "may work but results can vary" [OFFICIAL]. Spoken lines may be in another language; keep the directions in English [INFERRED].
- **Assembly order:**
  1. shot and camera;
  2. subject (general terms when a start frame exists [OFFICIAL]);
  3. one action (cause → effect);
  4. context;
  5. style and light;
  6. audio sentences (colon dialogue, §3.9);
  7. continuity and clean-plate clause.

### 3.2 Subject and identity

Be specific: "A woman in her twenties with wavy brown hair and light freckles" beats "a brown-haired woman" [OFFICIAL]. Veo 3 "appears to skew towards lighter skin tones when race is not specified" [OFFICIAL: model card, which covers later versions]. State age range, skin tone, hair and wardrobe explicitly. With a start frame, use "the subject", "the woman", "he", "she" [OFFICIAL].

### 3.3 Action, motion and physical interaction

- **Official vocabulary** covers basic movements, interactions, expressions, subtle actions and transformations. Keep "clip length in mind" for processes [OFFICIAL]. Ordered verbs work inside one shot ("A gloved hand carefully slices… The hand then delicately extracts…") [OFFICIAL].
- **Plausibility rules** [INFERRED]:
  - name the hand, the grip point and the object's response;
  - keep interactions in frame;
  - one primary action per clip;
  - describe liquids as stream, level and settling.

### 3.4 Environment, lighting and style

Google provides vocabularies [OFFICIAL]:
- setting, time, weather and period;
- lighting: natural, artificial, Rembrandt, high/low-key, volumetric, backlight, "golden hour glow", "dramatic side lighting";
- mood;
- style: photoreal, "shot on 35mm film", animation;
- ambiance: palettes, atmosphere, textures, "reflections on wet pavement".

A leading style keyword sets the medium ("Film noir style…", "A whimsical stop-motion animation of…") [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure

- **Timestamp prompting** gives "a complete, multi-shot sequence with precise cinematic pacing, all within a single generation" [OFFICIAL], formatted `[00:00-00:02] …`. The official example uses four 2-second segments. Use at most four, each at least 2 s [INFERRED].
- **Pacing and edit words.** "slow-motion", "time-lapse" and "fast-paced action" change pacing. "match cut", "jump cut" and "montage" create cuts [OFFICIAL].
- **Cut bias.** Veo 3 has "a bias for generating cinematic footage, with frequent camera cuts and dramatic camera angles" [OFFICIAL]. Write "one continuous shot, no cuts" unless cuts are wanted [INFERRED].
- **Split stories across clips** [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls

Camera direction is prompt-only on Higgsfield. Recognized terms [OFFICIAL]:
- **Angles:** eye-level, low, high, bird's-eye, worm's-eye, Dutch.
- **Framing:** close-up to wide, over-the-shoulder, POV.
- **Movement:** static, pan, tilt, dolly, truck, pedestal, zoom, crane, drone, handheld, whip pan, arc.
- **Lens:** wide, telephoto, shallow/deep focus, lens flare, rack focus, fisheye, dolly zoom.

"Some advanced camera angles are not officially supported" [OFFICIAL]. In image-to-video, camera-only motion is "the simplest and most reliable way to add dynamism" [OFFICIAL].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

**N/A on Higgsfield.** Google's up-to-three "asset" reference images (8 s only; not Lite) are not in the catalog; there are no video or audio references either [OFFICIAL][HF]. Approximation:
1. Composite the approved subject into a 9:16 start frame with an image model.
2. Animate that frame.
3. Carry a fixed verbal description forward to later prompts.

When deriving a start frame from an analyzed reference video, inherit composition and lighting only. Never inherit its text, usernames or watermarks.

### 3.8 Start and end frames

- **Start frame:** "the stronger the start, the better the finish". Prompt motion only, because re-describing the image makes "Redundant prompts [that] confuse the model". Direct camera motion, subject animation and environmental animation [OFFICIAL].
- **First + last (Lite):** describe the transition, e.g. "The camera performs a smooth 180-degree arc shot, starting with… to seamlessly end on…" [OFFICIAL]. Make the end frame as an edit of the start frame so geometry, light and background match [INFERRED].

### 3.9 Audio, dialogue and sound (if supported)

- **Official syntax** [OFFICIAL]: dialogue "Use quotes for specific speech"; "SFX: …"; "Ambient noise: …". DeepMind examples also use `Audio: …` and `Speaker: "line"`.
- **Library default: colon dialogue without quotation marks.** Google's best-practice page: "To prevent the model from rendering text in the video, use a colon (:) after the speaker's action to denote speech and avoid using quotation marks" [OFFICIAL].
- **Voice consistency:** give the character a name and a fixed voice description; repeat it verbatim [OFFICIAL]. The seed half of Google's tip is unavailable.
- **Line length.** Short speech is a known weakness [OFFICIAL]. Size lines to about 2–2.5 words per second (≤16 words for 8 s) and leave a beat at the end [INFERRED].
- **Silence:** Lite with `generate_audio: false`, or strip audio from `veo3_1`.

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field on Higgsfield [HF]. Google's negative-field rule: no "no"/"don't", just list the items ("wall, frame"). For the main prompt: "describe what you wish to exclude", e.g. "a desolate landscape with no buildings or roads" [OFFICIAL].

Rules [INFERRED]:
1. State the wanted state positively.
2. Add one short descriptive exclusion clause at the end.
3. Avoid long "no X, no Y" lists.

### 3.11 Visible text

Policy recap: Edit Mode removes all source text (not possible on these ids; route to an edit model). Analyze Mode may add intentional new text, by default in deterministic post (FFmpeg/libass).

**(a) Reliability.** No Google document claims reliable text rendering for Veo 3.1. The tech report says Veo 3 "is still poor at generating text" and "prone to small hallucinations" [OFFICIAL]. Google's own best practice is written to *prevent* text rendering [OFFICIAL]. Secondary reporting documents garbled subtitles on dialogue clips [SECONDARY]. **Verdict: not reliable.** Render every caption, hook or label in post.

**(b) Clean plate, the default for every Veo generation.**
1. **Dialogue.** Use colon form without quotation marks, with a visible speaker [OFFICIAL]. MIT Technology Review reported that Veo adds garbled subtitles to dialogue clips even when prompts ask for none. Google Labs support attributed this to speech [SECONDARY]. Write only the lines the concept needs. On Lite, prefer `generate_audio: false` when the shot needs no sound [INFERRED].
2. **Surfaces.** Describe text-bearing surfaces positively as blank or unbranded, as DeepMind does ("entirely unidentifiable, and unbranded… no discernible badging") [OFFICIAL example].
3. **Closing sentence** in Google's descriptive pattern: "Clean picture throughout, with no captions, subtitles, logos, watermarks or written words anywhere." [INFERRED]
4. **QC.** Check frames every 0.5 s for glyphs and re-roll on any text [INFERRED].

**(c) Intentional in-frame text.** Only when the text belongs to the scene and must appear in-frame (packaging, a sign, screen UI). It must arrive through the **start frame**: the approved real asset, or a still from an image model that renders text reliably. Keep it large, frontal and slow-moving; small or moving text warps first [INFERRED]. There is no Google quoting convention for text. Quotation marks are what Google says triggers text, so they are uncontrolled [OFFICIAL + INFERRED]. Never ask Veo to write new words.

**(d) Edit operations.** N/A on Higgsfield. If a Veo clip replaces a segment of an edited video, generate it as a clean plate per (b).

### 3.12 Character / identity consistency

- **Text-to-video.** Name the character, write "unchangeable features" plus a voice, and "Copy and paste the entire, unchanged character description" into every prompt [OFFICIAL].
- **Approved people.** Use a start frame that is sharp, front-lit and face-visible. Avoid head turns beyond about 90° and hands over the face [INFERRED].
- **Across clips.** Reuse the approved still, or the previous approved clip's last frame, as the next `start_image` [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

Start-frame strategy:
1. The approved product sits in a 9:16 start frame at correct scale, unoccluded, sharp and on its real contact surface.
2. Prompt motion only, naming the product generically [OFFICIAL].
3. Prefer camera moves (slow push-in, small arc, rack focus) to product rotation. Rotation invents unseen sides [INFERRED], and complex motion is where consistency breaks [OFFICIAL].
4. State the grip and keep the silhouette clear [INFERRED].
5. Labels stay large, frontal and slow, or blank [INFERRED].
6. On Lite, pin the end pose with an end frame of the same product [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

Integration is decided mostly in the start frame. Build the composite so the asset already sits at the right scale and perspective, with a contact shadow and the scene's light. Then the prompt only has to keep it that way [INFERRED].

**Phrasing** [INFERRED unless tagged]:
- **Scale and proportion:** relate the asset to known objects ("palm-sized, about the height of the mug beside it").
- **Orientation:** "front face toward the camera", "handle on the right".
- **Contact:** "rests flat on the table".
- **Grip:** "held in her right hand by its sides, fingers clear of the front face".
- **Occlusion:** "nothing passes in front of it". If occlusion is unavoidable, keep it brief and say the asset reappears unchanged.
- **Scene-light inheritance:** use Google's lighting vocabulary [OFFICIAL] plus direction and temperature. Example: "warm late-afternoon sun from camera left; its soft shadow falls to the right across the table; a thin highlight runs along its glossy edge; its reflection shows faintly in the polished surface".
- **Persistent states:**
  - "the lid stays open until the end";
  - "the glass stays half full";
  - "it remains exactly where she set it";
  - "she keeps it in her right hand throughout".

**Known failures.**
- "maintaining complete consistency throughout complex scenes or those with complex motion remains a challenge" [OFFICIAL: model card].
- "small hallucinations" [OFFICIAL: tech report].
- Google's own object-insertion feature ("Veo considers scale, interactions, and shadows") is Veo-2-based and not exposed [OFFICIAL][HF]. Nothing in Veo 3.1 guarantees prompt-driven insertion quality.

**Across clips.** Keep description text, palette, lighting and lens phrases identical. Chain by final frame → next `start_image` (Lite: plus `end_image`). Google's extension "finalizes the final second or 24 frames" [OFFICIAL]; the last frames are the continuity anchor [INFERRED].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Formula example, Google Cloud Blog (https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1):
   > Medium shot, a tired corporate worker, rubbing his temples in exhaustion, in front of a bulky 1980s computer in a cluttered office late at night. The scene is lit by the harsh fluorescent overhead lights and the green glow of the monochrome monitor. Retro aesthetic, shot as if on 1980s color film, slightly grainy.
2. Timestamp prompting, same source:
   > [00:00-00:02] Medium shot from behind a young female explorer with a leather satchel and messy brown hair in a ponytail, as she pushes aside a large jungle vine to reveal a hidden path. [00:02-00:04] Reverse shot of the explorer's freckled face, her expression filled with awe as she gazes upon ancient, moss-covered ruins in the background. SFX: The rustle of dense leaves, distant exotic bird calls. […] [00:06-00:08] Wide, high-angle crane shot, revealing the lone explorer standing small in the center of the vast, forgotten temple complex, half-swallowed by the jungle. SFX: A swelling, gentle orchestral score begins to play.
3. Dialogue and SFX, Gemini API (https://ai.google.dev/gemini-api/docs/veo):
   > A close up of two people staring at a cryptic drawing on a wall, torchlight flickering. A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'
4. Text-safe dialogue, Agent Platform best practices (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice):
   > A woman says: My name is Clara.
5. Image-to-video motion only, same source:
   > "Slow dolly in on the subject." / "The character's hair and clothes flutter gently in the wind." / "Fog rolls in slowly across the landscape."
6. Image-to-video prompt, Gemini API:
   > A surreal, cinematic macro video. Tiny surfers ride perpetual, rolling waves inside a stone bathroom sink. A running vintage brass faucet generates the endless surf. The camera slowly pans across the whimsical, sunlit scene as the miniature figures expertly carve the turquoise water.
7. First and last frame, Google Cloud Blog:
   > The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her to seamlessly end on the POV shot from behind her on stage. […]

Patterns these teach:
- **Order:** shot size or camera first, then subject, action, place/time, light, and style last (1, 6).
- **Sentence style:** declarative prose. Light and style may be terse fragments ("Retro aesthetic, … slightly grainy.").
- **Time:** `[mm:ss-mm:ss]` blocks, each holding one shot, one action and its own `SFX:` (2).
- **Subject vs camera motion:** Google separates camera motion, subject animation and environmental animation into distinct sentences (5). Transitions are described as a camera path (7).
- **Camera vocabulary:** standard film terms ("Reverse shot", "Tracking shot", "crane shot", "arc shot").
- **Audio:** separate sentences with `SFX:` or `Ambient noise:` labels. Dialogue in quotes is Google's generic syntax (3); the colon form (4) is Google's text-safe variant and this library's default.
- **Detail and length:** 30–110 words; concrete nouns and adjectives rather than adjective stacks.
- **Exclusions:** written as descriptions of what is there, not "no …" lists.

### 4.1 Text-to-video

Follows patterns 1–4: camera → subject → action → place → light/style → audio sentences → continuity/clean plate.
```text
<Shot size>, <angle>, <camera move>, <lens>. <Subject: age range, appearance, wardrobe>. <One action, cause →
effect>. <Place, time, weather>. <Light direction and temperature>, <style/format>. <Speaker> says: <short line,
no quotation marks>. SFX: <sound tied to the action>. Ambient noise: <place sound>. One continuous shot, no cuts,
real-time pace. Clean picture with plain unmarked surfaces and no captions, subtitles, logos or written words.
```
Example (`veo3_1`, 8 s, 9:16):
```text
Medium close-up, eye level, slow push-in, shallow depth of field. A man in his forties with close-cropped grey hair,
deep brown skin and a navy work jacket sits at a pale wooden workbench. He lifts a small matte-black handheld device
with his right hand, turns it once toward the window light, and sets it down beside a coil of cable, where it stays.
Quiet workshop at dusk, rain on the window. Warm lamp light from the left against cool blue window light, natural
film grain. He says: That should hold. SFX: a soft click as the device touches the bench. Ambient noise: steady
rain. One continuous shot, no cuts, real-time pace. Clean picture with plain unmarked surfaces and no captions,
subtitles, logos or written words.
```
Timestamped variant (pattern 2): at most four `[00:00-00:02]` blocks, each with one shot, one action and one SFX.

### 4.2 Start frame (and end frame) to video

Follows patterns 5–7: separate camera, subject and environment sentences; motion only.
```text
<Camera motion sentence>. <Subject animation sentence, general terms, in order>. <Environmental animation sentence>.
<Persistence: what stays fixed>. <Audio sentences>. One continuous shot. <Clean-plate sentence>.
```
Example (`veo3_1`, start_image = approved 9:16 product-in-scene still):
```text
Very slow dolly in toward the table. The woman slides the bottle two centimetres toward the camera with her right
hand and releases it. Steam drifts from the cup behind it. The bottle stays upright where she left it, keeping its
exact shape, proportions, label and soft shadow to the right. SFX: glass gliding on wood. One continuous shot. Clean
picture with no added captions or written words.
```
First + last (`veo3_1_lite`), pattern 7: `The camera arcs slowly a quarter-turn left around the desk as the small robot lamp raises its head and switches on, ending on the side view of the lit lamp. One continuous shot, no cuts. No captions or written words.`

### 4.3 Reference-to-video

N/A on Higgsfield. Use §4.2 with a start frame composited from the approved references.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield. Edit Mode jobs go to `gemini_omni_flash_1_1` (edit) or `flux_3_video_edit`. Chain clips via last frame → `start_image`.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Garbled subtitles or captions | Dialogue, especially in quotation marks [SECONDARY][OFFICIAL] | Colon dialogue, fewer lines, clean-plate sentence, QC; Lite silent mode |
| Pseudo-text on props | Text-bearing surfaces [OFFICIAL] | Blank/unbranded surfaces; real text only via start frame |
| Unmotivated cuts or dramatic angles (slop) | Documented cinematic bias [OFFICIAL] | "One continuous shot, no cuts"; one named camera move; no editing vocabulary |
| Dead space (action ends early, clip idles) | 8 s default with a short action [INFERRED] | Pick 4/6 s, or give the action a beginning, middle and end across the duration ("keep clip length in mind" [OFFICIAL]) |
| Arbitrary slow motion | "Cinematic/epic" wording without a pace [INFERRED] | "real-time pace"; avoid "slow-motion" unless wanted [OFFICIAL vocabulary] |
| Sudden speed changes | Mixed pace words, several moves [INFERRED] | One camera move at one speed; "steady pace" |
| Morphing or geometry drift | Complex motion, rotation, occlusion [OFFICIAL model card] | Camera moves over object spins; Lite end frame; clear silhouette |
| Identity drift or clothing changes | Cuts, occlusion, text-only people [INFERRED] | Start frame; single shot; identical description block [OFFICIAL] |
| Duplicated objects | Object mentioned several ways, or no count [INFERRED] | "a single …", then "the same …" consistently |
| Muddled multi-event clip | A→B→C chains [OFFICIAL] | One action per clip; at most 4 × 2 s timestamps |
| Re-imagined start frame | Prompt re-describes the image [OFFICIAL] | Motion-only prompt |
| Cropped subject | Start frame not 9:16 [OFFICIAL] | `atg.py conform` before upload |
| Garbled short speech | Crammed or very short lines [OFFICIAL] | Size lines to duration; visible speaker |
| Blocked generation | Audio/safety filters, minors, prominent people [OFFICIAL] | Rephrase audio; approved adult references only |

## 6. Model-specific features and controls

- **Variants (`veo3_1`):** `veo-3-1-fast` (default) for iteration, `veo-3-1-preview` for finals [HF]. Google positions Fast for ads, rapid A/B testing and social content [OFFICIAL].
- **Quality tiers (`veo3_1`):** always `basic` in the fixed format (§2.6).
- **Lite as the draft tier:** less than half the cost of Fast [OFFICIAL]. The only id here with an end frame and an audio switch [HF]. Lock the prompt on Lite, then render the final on `veo3_1` from the same start frame [INFERRED].
- **Timestamp prompting and native audio** [OFFICIAL].
- **Prompt enhancement via Gemini** [OFFICIAL]. Keep the result under 1,024 tokens.
- **SynthID** invisible watermark [OFFICIAL].

## 7. Model-specific pre-generation checklist

- [ ] Catalog re-checked; upstream preview shutdown (2026-10-22) considered.
- [ ] `aspect_ratio: "9:16"`; `veo3_1` uses `quality: "basic"`; Lite never `auto`.
- [ ] Start and end frames conformed to 9:16 (≥720×1280), adults only, no famous people, subject centered.
- [ ] Shot fits 4/6/8 s with one action spanning the duration (no dead space); "real-time pace".
- [ ] Start-frame prompt is motion-only, with separate camera, subject and environment sentences.
- [ ] Dialogue in colon form with a visible speaker, sized to duration, or none.
- [ ] Clean plate: blank surfaces plus closing sentence. Analyze-Mode text planned for post, not in-frame.
- [ ] Integration phrases: scale, contact, grip, light direction and temperature, shadow, persistent states.
- [ ] `get_cost` done. Output ffprobed (720×1280? audio as intended?) and QC'd for text, identity, geometry and cuts.

## 8. Sources

- [OFFICIAL] Generate videos with Veo 3.1 in Gemini API (updated 2026-09-17) — https://ai.google.dev/gemini-api/docs/veo — accessed 2026-09-30
- [OFFICIAL] Video generation overview, Gemini API — https://ai.google.dev/gemini-api/docs/video — accessed 2026-09-30
- [OFFICIAL] Video generation prompt guide, Agent Platform (updated 2026-09-28) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide — accessed 2026-09-30
- [OFFICIAL] Best practices for generating videos — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice — accessed 2026-09-30
- [OFFICIAL] Veo 3.1 model page (Agent Platform) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/veo/3-1-generate — accessed 2026-09-30
- [OFFICIAL] Generate videos from an image / first and last frames / references / text — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-an-image — accessed 2026-09-30
- [OFFICIAL] Responsible AI for Veo — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/responsible-ai-and-usage-guidelines — accessed 2026-09-30
- [OFFICIAL] The ultimate prompting guide for Veo 3.1 (Google Cloud Blog, 2025-10-16) — https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 — accessed 2026-09-30
- [OFFICIAL] Veo model page (DeepMind; evaluation resolutions) — https://deepmind.google/models/veo/ — accessed 2026-09-30
- [OFFICIAL] How to create effective prompts with Veo 3 (DeepMind) — https://deepmind.google/models/veo/prompt-guide/ — accessed 2026-09-30
- [OFFICIAL] Veo 3 Model Card (covers subsequent versions; updated 2026-01-13) — https://storage.googleapis.com/deepmind-media/Model-Cards/Veo-3-Model-Card.pdf — accessed 2026-09-30
- [OFFICIAL] Veo 3 Tech Report — https://storage.googleapis.com/deepmind-media/veo/Veo-3-Tech-Report.pdf — accessed 2026-09-30
- [OFFICIAL] Build with Veo 3.1 Lite (blog.google, 2026-03-31) — https://blog.google/innovation-and-ai/technology/ai/veo-3-1-lite/ — accessed 2026-09-30
- [OFFICIAL] Gemini API changelog / deprecations — https://ai.google.dev/gemini-api/docs/deprecations — accessed 2026-09-30
- [OFFICIAL] Google Flow Help: models & supported features — https://support.google.com/flow/answer/16352836 — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract (call shape, roles, `get_cost`, snapping, upload) — as recorded for /analyze-then-generate — accessed 2026-09-30
- [HF] How to Use Google Veo 3.1 (Higgsfield blog) — https://higgsfield.ai/blog/How-to-Use-Google-Veo-3.1-Complete-Guide-for-the-New-Model — accessed 2026-09-30
- [HF] Veo 3.1 on Higgsfield — https://higgsfield.ai/veo3.1 — accessed 2026-09-30
- [SECONDARY] "Google's generative video model Veo 3 has a subtitles problem", MIT Technology Review (2025-07-15) — https://www.technologyreview.com/2025/07/15/1120156/googles-generative-video-model-veo-3-has-a-subtitles-problem/ — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- **Output dimensions.** What `veo3_1` `quality` `basic`/`high`/`ultra` deliver (720p/1080p/4k expected, unconfirmed), and whether `variant` changes resolution. Whether `basic` + 9:16 yields exactly 720×1280, and what Lite delivers (720×1280 expected). No Higgsfield source states these.
- **Backend.** Which backend Higgsfield calls: Gemini API preview ids (shutdown 2026-10-22) or Agent Platform GA ids.
- **4k on Fast.** Whether `ultra` works with `veo-3-1-fast`; Google's two doc sets conflict.
- **Lite audio switch.** How `generate_audio: false` is implemented on Lite, and whether lips still move when dialogue is written with audio off.
- **Blocked jobs.** Whether Higgsfield bills Google-side safety or audio blocks.
- **Colon dialogue.** How much it reduces subtitle artifacts on Veo 3.1; no rates are published.
- **Timestamps.** Reliability beyond four segments or with segments under 2 s.
