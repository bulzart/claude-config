---
guide: veo-3
title: Google Veo 3
provider: Google DeepMind (served through the Gemini API and Gemini Enterprise Agent Platform, formerly Vertex AI)
higgsfield_model_ids: [veo3]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Google Veo 3 — model engineering guide

> Scope: Veo 3 is the first Veo generation with natively generated audio (dialogue, SFX, ambience). This file
> covers the single Higgsfield id `veo3`, with variants `veo-3-preview` (best quality) and `veo-3-fast`
> (faster). Operations: text-to-video and start-frame animation. There is no duration, resolution,
> end-frame, reference, negative-prompt or seed control on Higgsfield, and no video editing (Edit-Mode jobs
> route elsewhere). Google has shut down the Veo 3.0 endpoints upstream (§1), so treat `veo3` as a legacy
> model. /analyze-then-pick renders **9:16 at 720p** (§2.6); visible text is mode-dependent (§3.11).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** "Veo 3 is a video generation system capable of synthesizing high-quality, high-resolution video with audio from a text prompt or input image" [OFFICIAL: model card]. It "lets you add sound effects, ambient noise, and even dialogue… generating all audio natively" [OFFICIAL: DeepMind]. Higgsfield: "Reliable cinematic, broad creative range" [HF].
- **Lifecycle warning.** Google shut down `veo-3.0-generate-001` and `veo-3.0-fast-generate-001` on the Gemini API on 2026-06-30 and recommends the Veo 3.1 ids [OFFICIAL: deprecations, changelog]. The Agent Platform also lists 2026-06-30 retirement [OFFICIAL]. The Higgsfield catalog still lists `veo3` [HF], and the backend now answering it is unpublished. **Prefer `veo3_1` for new work**; use `veo3` only when explicitly selected, and verify outputs [INFERRED].
- **Best for:** cinematic realism with synchronized sound; strong prompt adherence ("performed best on overall preference, and for its capability to follow prompts accurately") [OFFICIAL]; cheap variations on `veo-3-fast` [HF].
- **Weaker at:**
  - text ("still poor at generating text", "prone to small hallucinations") [OFFICIAL: tech report];
  - unwanted cuts ("a bias for generating cinematic footage, with frequent camera cuts and dramatic camera angles") [OFFICIAL];
  - consistency in complex scenes or motion [OFFICIAL: model card];
  - garbled subtitles on dialogue [SECONDARY];
  - no controls beyond prompt and start frame [HF].
- **Choose this model when** Veo 3 is explicitly requested, or a quick cinematic clip with native audio is enough. **Choose another model when** you need end frames, references, editing, legible text, a chosen duration, or long-term availability.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | `veo3`, no `medias` | Length not selectable [HF] |
| Start frame → video | `start_image` | The image is used as the initial frame [OFFICIAL] |
| End frame, references, extension, edit | N/A on Higgsfield | Not exposed [HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `veo3` | `variant` | `veo-3-preview`, `veo-3-fast` | `veo-3-fast` | "'veo-3-preview' = best quality; 'veo-3-fast' = faster generation" [HF] |
| `veo3` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` here |
| `veo3` | `prompt` | string | — | 1,024-token limit [OFFICIAL] |
| `veo3` | duration | not exposed | — | Google docs disagree for Veo 3: the Gemini API says "8 seconds"; the Agent Platform and the 2025-10-15 changelog say 4/6/8 [OFFICIAL]. Expect 8 s [INFERRED] |
| `veo3` | resolution, negative prompt, seed, sample count | not exposed | — | Google has `negativePrompt` and `seed` for Veo 3 [OFFICIAL]; Higgsfield does not [HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | Initial frame of the video [OFFICIAL] | 1 | ≥720p; 16:9/9:16 recommended; other ratios "may be resized or centrally cropped" [OFFICIAL]; JPEG/PNG, ≤20 MB [OFFICIAL] |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced when unambiguous [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** not selectable; plan for 8 s and measure the output [INFERRED].
- **Resolution:** Gemini API: "720p & 1080p (16:9 only)". Agent Platform: 720p/1080p [OFFICIAL]. Portrait is therefore 720p upstream [OFFICIAL + INFERRED].
- **Frame rate:** 24 fps [OFFICIAL].
- **Audio:** "Always on" [OFFICIAL]. There is no flag on Higgsfield; strip locally for silence [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6). Never send `duration`: the catalog defines none for `veo3` [HF].

Text-to-video (draft):
```json
{"model":"veo3","prompt":"<PROMPT>","aspect_ratio":"9:16","variant":"veo-3-fast"}
```
Start frame → video (quality variant; the start frame is already 9:16):
```json
{"model":"veo3","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"aspect_ratio":"9:16","variant":"veo-3-preview"}
```
Start frame from a completed Higgsfield image job:
```json
{"model":"veo3","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"aspect_ratio":"9:16","variant":"veo-3-fast"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Legacy backend.** Upstream endpoints are shut down [OFFICIAL]. If outputs show traits of another model (4k, other lengths, no audio), record it and switch to `veo3_1` [INFERRED].
2. **Start frame must be 9:16.** Google may center-crop other ratios [OFFICIAL]. Conform locally first [INFERRED].
3. **No duration control.** Size the action for about 8 s [INFERRED].
4. **Audio cannot be switched off.** Written dialogue will be voiced [OFFICIAL + INFERRED].
5. **People in start frames.** "allow_adult" only. Child and prominent-person content is rejected [OFFICIAL].
6. **No negative prompt.** Put exclusions in the prompt (§3.10) [HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `veo3` | `"aspect_ratio":"9:16"`, `variant` of choice. There is no resolution parameter | 720×1280 expected. Google lists Veo 3's 1080p as "16:9 only", so portrait is 720p [OFFICIAL + INFERRED]. DeepMind evaluated Veo portrait "at 720x1280 resolution" [OFFICIAL] | None if 720×1280. Otherwise `atp.py conform` (exact downscale, or scale-to-fill plus minimal crop; never stretch) | Native 9:16 request. Any start frame is reframed to 9:16 before upload |

ffprobe the first output of a session. The legacy backend makes this mandatory [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **DeepMind's Veo 3 elements:** shot framing and motion, style, lighting, character descriptions, location, action, dialogue. "The more detail you add, the more control you'll have over the final output" [OFFICIAL].
- **Gemini API/Agent Platform elements:** Subject, Action, Style, Camera, Composition, Focus/lens, Ambiance [OFFICIAL].
- **Writing rules:** prose with adjectives and adverbs; English; audio in "separate sentences" [OFFICIAL].
- **One focused moment per short clip** [OFFICIAL]. Length: 60–140 words for text-to-video, 25–60 for start-frame prompts [INFERRED].
- **Order:** style/format → shot and camera → subject → one action → place → light → audio sentences → continuity and clean plate. This follows DeepMind's advice to "Start your prompt by defining the sort of video you want to create" [OFFICIAL].

### 3.2 Subject and identity

"A woman in her twenties with wavy brown hair and light freckles" beats "a brown-haired woman" [OFFICIAL]. Veo 3 "appears to skew towards lighter skin tones when race is not specified" [OFFICIAL], so specify appearance. With a start frame, use "the subject", "the man", "she" [OFFICIAL].

### 3.3 Action, motion and physical interaction

For complex action, DeepMind suggests "highly-detailed prompts" with "exact play-by-plays" [OFFICIAL]. For products or people [INFERRED]:
- one action;
- name the hand and grip, what moves and what stays still, and the end state;
- liquids: stream, level, settling.

### 3.4 Environment, lighting and style

- **Style:** "Is it a cartoon? Claymation? Film noir shot on 35mm?" [OFFICIAL].
- **Lighting:** "warm lighting that's even across the frame" vs "a spotlight in one area" [OFFICIAL].
- **Location:** "A smoky jazz club at night" beats "a jazz club" [OFFICIAL].
- **World-building:** "evocative, sensory language" [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure

Given the cut bias [OFFICIAL], write "One continuous shot, no cuts" and name one camera move [INFERRED]. Timestamp prompting (`[00:00-00:02] …`) is documented for Veo 3.1, not Veo 3 [OFFICIAL]. On `veo3`, use two or three ordered beats ("first… then… finally…") and verify [INFERRED]. DeepMind advises "a clear beginning, middle, and end" [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls

Prompt-only camera. Recognized terms [OFFICIAL]:
- **Framing:** wide, medium, close-up, over-the-shoulder, POV.
- **Angles:** eye-level, low, high, bird's-eye, Dutch.
- **Movement:** static, pan, tilt, dolly, truck, pedestal, zoom, crane, drone, handheld, arc.
- **Lens:** shallow/deep focus, telephoto, rack focus, dolly zoom.

In image-to-video, camera-only motion is "the simplest and most reliable" [OFFICIAL].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

**N/A on Higgsfield.** Veo 3 itself has no reference images ("Use reference images: Not supported") [OFFICIAL]. Composite approved subjects into a 9:16 start frame instead. Inherit composition and light from analyzed references, never their text or watermarks.

### 3.8 Start and end frames

- **Start frame:** "the basis for everything that follows, including character detail, lighting, and overall artistic style". Prompt motion only; re-describing confuses the model [OFFICIAL].
- **End frame:** N/A. First/last-frame is "available for Veo 3.1 models only" [OFFICIAL].

### 3.9 Audio, dialogue and sound (if supported)

- **Official forms:** characters can discuss a topic or say exact lines. DeepMind uses quoted lines, `Speaker: "line"` scripts and `Audio:` blocks [OFFICIAL].
- **Library default: colon without quotation marks,** e.g. `The detective says: Your story has holes.` This is Google's documented text-safe form [OFFICIAL], used verbatim in the Agent Platform's Veo dialogue example.
- **SFX and ambience** as separate sentences [OFFICIAL].
- **Keep lines short and few.** Short speech segments are a weakness [OFFICIAL]. Aim for 2–2.5 words per second [INFERRED].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field [HF]. Google: "describe what you wish to exclude", e.g. "a desolate landscape with no buildings or roads" [OFFICIAL]. Negative-field lists ("wall, frame") do not transfer to the main prompt. State the positive first, then one short descriptive exclusion at the end [INFERRED].

### 3.11 Visible text

Policy: Edit Mode (removing source text) is not possible on `veo3`; route to an edit model. Analyze Mode may add new text, by default in deterministic post.

**(a) Reliability:** poor. "Veo 3 is still poor at generating text (a necessary skill for many misuse scenarios)" [OFFICIAL: tech report]. Garbled subtitles on dialogue clips were widely reported in 2025. Google Labs support attributed them to speech; Google said it had developed fixes [SECONDARY: MIT Technology Review]. **Never rely on `veo3` for exact text.**

**(b) Clean plate:**
1. Minimize dialogue. Write it in colon form with a visible speaker [OFFICIAL].
2. Describe surfaces as blank or unbranded. DeepMind's own example uses "entirely unidentifiable, and unbranded… no discernible badging" [OFFICIAL].
3. Close with "Clean picture throughout, with no captions, subtitles, logos, watermarks or written words." [INFERRED]
4. QC each clip for glyphs; re-roll on any text [INFERRED].

**(c) Intentional in-frame text.** Only through the start frame (the real asset or a text-reliable image model): large, frontal, slow. Analyze-Mode hooks, captions and labels go in post [INFERRED].

**(d) Edit operations:** N/A on Higgsfield.

### 3.12 Character / identity consistency

Name the character and paste an identical description block (build, age, hair, face, eyes, marks, wardrobe, voice) into every prompt [OFFICIAL]. Seed matching is unavailable. For approved people, use a clear, well-lit start frame; avoid big head turns and occlusion [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

1. The exact product goes in a 9:16 start frame at final scale, unoccluded, on its real surface.
2. Prompt motion only, naming the product generically.
3. Prefer a slow push-in or small arc to rotation; complex motion is where consistency breaks [OFFICIAL].
4. State the grip and the end state.
5. Labels stay large and still, or blank [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

Integration quality is set in the start-frame composite (scale, perspective, contact shadow, matching light). The prompt protects it over time [INFERRED]:
- **Scale:** "palm-sized, the same height as the cup beside it".
- **Orientation:** "front face toward the camera".
- **Contact and grip:** "rests flat on the counter"; "held in his left hand by the base, fingers clear of the front".
- **Occlusion:** "nothing passes in front of it"; if it does, "it reappears unchanged".
- **Light inheritance:** name source, direction and color temperature, plus the resulting shadow and reflection, e.g. "cool overcast daylight from above; a soft shadow directly beneath it; a faint reflection in the glossy counter". DeepMind's own lighting questions ask where light comes from and how even it is [OFFICIAL].
- **Persistent states:** "the drawer stays open", "the cup stays half full", "it stays exactly where he set it", "he keeps it in the same hand".
- **Multiple people:** give each a fixed visual handle; avoid ambiguous pronouns [INFERRED].

**Known failures.** "Maintaining complete consistency throughout complex scenes or those with complex motion remains a challenge" [OFFICIAL]. Small hallucinations [OFFICIAL]. No insertion or edit feature on Higgsfield [HF].

**Across clips.** Keep identical description, lighting and format phrases. Chain approved last frame → next `start_image` [INFERRED]. Do not intercut `veo3` and `veo3_1` shots without a look check [INFERRED].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Character with dialogue, DeepMind Veo 3 prompt guide (https://deepmind.google/models/veo/prompt-guide/):
   > A medium shot frames an old sailor, his knitted blue sailor hat casting a shadow over his eyes, a thick grey beard obscuring his chin. He holds his pipe in one hand, gesturing with it towards the churning, grey sea beyond the ship's railing. "This ocean, it's a force, a wild, untamed might. And she commands your awe, with every breaking light"
2. Sound design, same source:
   > A keyboard whose keys are made of different types of candy. Typing makes sweet, crunchy sounds. Audio: Crunchy, sugary typing sounds, delighted giggles.
3. Style-first script, same source:
   > Camping (Stop Motion): Camper: "I'm one with nature now!" Bear: "Nature would prefer some personal space."
4. Text-safe dialogue with ambience, Agent Platform prompt guide (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide):
   > A medium shot in a dimly lit interrogation room. The seasoned detective says: Your story has holes. The nervous informant, sweating under a single bare bulb, replies: I'm telling you everything I know. The only other sounds are the slow, rhythmic ticking of a wall clock and the faint sound of rain against the window
5. Audio detail, Gemini API ("prompting Veo 3's audio generation") (https://ai.google.dev/gemini-api/docs/veo):
   > A wide shot of a misty Pacific Northwest forest. Two exhausted hikers, a man and a woman, push through ferns when the man stops abruptly, staring at a tree. Close-up: Fresh, deep claw marks are gouged into the tree's bark. Man: (Hand on his hunting knife) "That's no ordinary bear." […] A rough bark, snapping twigs, footsteps on the damp earth. A lone bird chirps.
6. Unbranded detail and play-by-play, DeepMind Veo 3 prompt guide:
   > […] Several heavily modified, entirely unidentifiable, and unbranded off-road vehicles are engaged in a frenetic, no-holds-barred race. […] a hulking, high-clearance beast with a heavily reinforced external roll cage and no discernible badging […]
7. Image-to-video motion, Agent Platform best practices (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice):
   > "Slow dolly in on the subject." / "The character's hair and clothes flutter gently in the wind." / "Fog rolls in slowly across the landscape."

Patterns these teach:
- **Order:** shot framing first (1, 4, 5), or style first ("Camping (Stop Motion):"), then subject, action, setting, sound.
- **Sentence style:** vivid prose. A shot change can be written inline ("Close-up: …") (5).
- **Dialogue:** quoted after the description (1), a `Speaker:` script (3, 5), or colon without quotes (4, the text-safe form used here). Stage directions go in parentheses (5).
- **Audio:** `Audio:` label (2) or plain closing sound sentences (4, 5).
- **Exclusions:** stated as descriptive absence ("unidentifiable, and unbranded", "no discernible badging") (6).
- **Detail:** 20–120 words. Play-by-play only for complex action (6).
- **Image-to-video:** camera, subject and environment motion as separate short sentences (7).

### 4.1 Text-to-video

Follows patterns 1, 4 and 6: style → shot → subject → action → place/light → colon dialogue → sound sentences → continuity/clean plate.
```text
<Style/format>. <Shot size>, <angle>, <camera move>. <Subject with explicit appearance and wardrobe>. <One action,
cause → effect, with end state>. <Place and time>. <Light direction and temperature>. <Speaker> says: <short line>.
<Sound sentence(s)>. One continuous shot, no cuts, real-time pace. Clean picture with unbranded, unmarked surfaces
and no captions, subtitles, logos or written words.
```
Example (`veo3`, 9:16):
```text
Photorealistic, shot on 35mm film. Wide shot, low angle, slow tracking left. A brown-and-white dog with a plain red
collar trots along a shallow stream bed, splashing through the water, then stops on a flat stone and shakes itself
dry. Early morning in a pine forest, mist between the trunks. Soft warm backlight rims the wet fur. Water splashing,
the rattle of the dog shaking, birdsong in the distance. One continuous shot, no cuts, real-time pace. Clean picture
with no captions, subtitles, logos or written words.
```

### 4.2 Start frame (and end frame) to video

Follows pattern 7: separate camera, subject and environment sentences; general subject terms.
```text
<Camera motion>. <Subject animation, general terms, in order>. <Environmental motion>. <What stays fixed>.
<Sound sentence>. One continuous shot. <Clean-plate sentence>.
```
Example (start_image = approved 9:16 still of a person holding a handheld object):
```text
Slow push-in toward her hands. She raises the handheld object to chest height and holds it steady in her right
hand. Curtains stir in a light breeze behind her. The object keeps its exact shape and details from the first frame.
Fabric rustle and quiet room tone. One continuous shot. No captions or written words appear.
```
End frame: N/A on Higgsfield.

### 4.3 Reference-to-video

N/A on Higgsfield; use §4.2 with a composited start frame.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield (extension is a Veo 3.1 feature upstream) [OFFICIAL][HF].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Garbled subtitles | Dialogue, quoted lines [SECONDARY][OFFICIAL] | Colon form, fewer lines, clean-plate sentence, QC |
| Pseudo-text on props | Text-bearing surfaces [OFFICIAL] | Unbranded or blank surfaces; real text only via start frame |
| Unmotivated cuts or dramatic angles (slop) | Documented bias [OFFICIAL] | "One continuous shot, no cuts"; one camera move |
| Dead space | Short action in a fixed ~8 s clip [INFERRED] | Give the action a beginning, middle and end spanning the clip |
| Arbitrary slow motion or speed jumps | Pace unspecified, mixed moves [INFERRED] | "real-time pace", one steady camera move |
| Morphing or geometry drift | Complex motion, rotation [OFFICIAL] | Camera moves instead of spins; clear silhouette |
| Identity drift or clothing changes | Cuts, occlusion, text-only characters [INFERRED] | Start frame; identical description block [OFFICIAL] |
| Duplicated objects | Object named inconsistently [INFERRED] | "a single …", then "the same …" |
| Muddled multi-event clip | A→B→C chains [OFFICIAL] | One moment per clip |
| Re-imagined start frame | Prompt re-describes the image [OFFICIAL] | Motion-only prompt |
| Unexpected backend behaviour | Upstream shutdown [INFERRED] | Probe output; prefer `veo3_1` |

## 6. Model-specific features and controls

- **Variants:** `veo-3-fast` (default) for exploration, `veo-3-preview` for quality [HF].
- **Native, always-on audio** [OFFICIAL]. Gemini prompt enhancement [OFFICIAL]. SynthID watermark [OFFICIAL].

## 7. Model-specific pre-generation checklist

- [ ] `veo3` explicitly requested; `veo3_1` considered.
- [ ] `aspect_ratio: "9:16"`; no `duration` sent; action sized to about 8 s with no dead space.
- [ ] Start frame conformed to 9:16 (≥720×1280), adults only, no prominent people.
- [ ] Motion-only prompt for start frames; "one continuous shot, no cuts, real-time pace".
- [ ] Dialogue minimized, colon form; clean plate; Analyze-Mode text planned for post.
- [ ] Integration phrases (scale, contact, grip, light, shadow, persistent states).
- [ ] `get_cost` done; output probed (duration, 720×1280, audio) and QC'd.

## 8. Sources

- [OFFICIAL] Generate videos with Veo 3.1 in Gemini API (Veo 3 columns; audio examples) — https://ai.google.dev/gemini-api/docs/veo — accessed 2026-09-30
- [OFFICIAL] Veo 3 model page, Agent Platform (retirement 2026-06-30) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/veo/3-0-generate — accessed 2026-09-30
- [OFFICIAL] Gemini API deprecations — https://ai.google.dev/gemini-api/docs/deprecations — accessed 2026-09-30
- [OFFICIAL] Gemini API changelog — https://ai.google.dev/gemini-api/docs/changelog — accessed 2026-09-30
- [OFFICIAL] How to create effective prompts with Veo 3 (DeepMind) — https://deepmind.google/models/veo/prompt-guide/ — accessed 2026-09-30
- [OFFICIAL] Veo model page (DeepMind; evaluation resolutions) — https://deepmind.google/models/veo/ — accessed 2026-09-30
- [OFFICIAL] Veo 3 Model Card — https://storage.googleapis.com/deepmind-media/Model-Cards/Veo-3-Model-Card.pdf — accessed 2026-09-30
- [OFFICIAL] Veo 3 Tech Report — https://storage.googleapis.com/deepmind-media/veo/Veo-3-Tech-Report.pdf — accessed 2026-09-30
- [OFFICIAL] Video generation prompt guide (Agent Platform) — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide — accessed 2026-09-30
- [OFFICIAL] Best practices for generating videos — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice — accessed 2026-09-30
- [OFFICIAL] Generate videos from an image — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-an-image — accessed 2026-09-30
- [OFFICIAL] Responsible AI for Veo — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/responsible-ai-and-usage-guidelines — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract — as recorded for /analyze-then-pick — accessed 2026-09-30
- [SECONDARY] "Google's generative video model Veo 3 has a subtitles problem", MIT Technology Review (2025-07-15) — https://www.technologyreview.com/2025/07/15/1120156/googles-generative-video-model-veo-3-has-a-subtitles-problem/ — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- Which model serves `veo3` after the 2026-06-30 upstream shutdown, and whether the two variants still differ.
- Actual output for `aspect_ratio: "9:16"`: 720×1280 expected, unconfirmed. Also actual duration (8 s expected).
- Whether a `duration` field sent to `veo3` is ignored, snapped or rejected.
- Current subtitle-artifact rate after Google's 2025 fixes; there is no official figure.
- Whether `[00:00-00:02]` timestamps work on Veo 3 (documented for 3.1 only).
