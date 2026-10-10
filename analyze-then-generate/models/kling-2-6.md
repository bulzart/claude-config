---
guide: kling-2-6
title: Kuaishou Kling 2.6
provider: Kuaishou — Kling AI, served by Higgsfield
higgsfield_model_ids: [kling2_6]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Kuaishou Kling 2.6 — model engineering guide

> Scope: Kling VIDEO 2.6, Kling's first model with native audio, as served by Higgsfield under `kling2_6`
> ("Kling 2.6 Video — Cinematic motion, advanced physics"). On Higgsfield: text-to-video and start-frame
> animation at 5 or 10 s with optional native audio (dialogue, narration, singing/rap, ambience, sound
> effects). No end frame, references, Elements, multi-shot controls or editing on Higgsfield.
> Project output format is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** "With the VIDEO 2.6 Model, we are introducing the 'Native Audio' feature for the first time" — one generation produces the visuals together with voice, sound effects and ambience, and "Voice rhythm, ambient sounds, and visual actions are closely aligned" [OFFICIAL S1]. Higgsfield: "Cinematic motion, advanced physics" and "Cinematic clips with audio", up to 1080p [HF S2, S4].
- **Best for:** single continuous 5–10 s shots with convincing motion; talking, narrating, singing or rapping characters in Chinese or English; ambience and action sound in the same pass; animating an approved still with sound [OFFICIAL S1; HF S2].
- **Weaker at:** voice output only in Chinese and English ("If you input other languages, the model will automatically translate them to English") [OFFICIAL S1]; multi-voice scenes beyond two characters ("performance may degrade in scenes with three or more characters") [OFFICIAL S1; SECONDARY S11]; no shot planning [HF S3]; no end frame, references or Elements on Higgsfield [HF S2]; no text-rendering claim (native text output arrived with 3.0) [OFFICIAL S5]; no resolution control on Higgsfield (§2.6).
- **Choose this model when** a single shot or start-frame animation with native Chinese/English speech, singing or rap fits 5 or 10 s.
- **Choose another model when** you need flexible 3–15 s, multi-shot, Elements, an end frame, Japanese/Korean/Spanish speech or text preservation (Kling 3.0), references (Seedance 2.0/2.5), editing (Kling 3.0 Omni Edit, Seedance 2.5), or guaranteed native 720p output.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"kling2_6"`, no `medias` | 5 or 10 s |
| Start frame to video | role `start_image` | the only media role |
| End frame, references, Elements, multi-shot, edit, extension | N/A on Higgsfield | [HF S2] |
| Motion control | N/A for this id | Kling 2.6 Motion Control exists in Kling's app [OFFICIAL S6]; Higgsfield's legacy `motion_control` tool is the 3.0 version |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling2_6` | `duration` | `5`, `10` (s) | `5` | "Video duration in seconds." Other values snap [HF S7]. Kling: "For singing or dialogue scenes, using the 10s parameter is recommended for more complete and stable results." [OFFICIAL S1] |
| `kling2_6` | `sound` | bool | `true` | "Generate the video with native audio." (boolean here; `kling3_0` uses `"on"`/`"off"`) [HF S2] |
| `kling2_6` | `aspect_ratio` (call-level) | `16:9`, `9:16`, `1:1` | not stated | matches Kling's "Aspect Ratio: 16:9, 1:1, 9:16" [OFFICIAL S1]; project: `9:16` |
| `kling2_6` | resolution / mode | none | — | not selectable on Higgsfield; up to 1080p [HF S4] (§2.6) |
| `kling2_6` | `negative_prompt`, `cfg_scale`, `camera_control`, end frame, voice control (`@VoiceName`), seed | — | — | **Not exposed on Higgsfield** [HF S2]. Kling's API offers `negative_prompt`, `cfg_scale` (0–1) and `sound` on/off for 2.6 [SECONDARY S8]; custom voices exist only in Kling's app for image-to-audio-visual [OFFICIAL S1]. Approximations: exclusions in prose (§3.10), precise wording instead of cfg, camera moves in words (§3.6), voices described in words (§3.9). |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing) [HF S7].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame: identity, product, scene, composition | 1; "it's recommended to upload higher-resolution images" [OFFICIAL S1]; Kling image rules: jpg/jpeg/png, ≥300 px, ≤10 MB [OFFICIAL S9] | "ensure image content matches the text description" [OFFICIAL S1] |

`medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF S7].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 5 or 10 s; one continuous shot per generation [HF S2, S3; OFFICIAL S1].
- **Resolution:** not selectable; up to 1080p [HF S4].
- **Aspect ratio:** 16:9, 9:16, 1:1 [HF S2; OFFICIAL S1].
- **Audio:** `sound:true` gives voice, SFX and ambience in one pass; `sound:false` for silence [OFFICIAL S1; HF S2]. Voice output: Chinese and English [OFFICIAL S1].

### 2.4 Call recipes

All recipes use `aspect_ratio:"9:16"`; the output is conformed to 720×1280 afterwards (§2.6). Add `"get_cost": true` to preflight.

**Text-to-video with native audio**
```json
{"model":"kling2_6","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","sound":true}
```
**Text-to-video, silent**
```json
{"model":"kling2_6","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","sound":false}
```
**Start frame to video** (exactly-9:16 image)
```json
{"model":"kling2_6","prompt":"<PROMPT describing change from the frame>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":5,"aspect_ratio":"9:16","sound":true}
```
**Chained continuation** (last frame of the previous clip, extracted locally and uploaded) [INFERRED]
```json
{"model":"kling2_6","prompt":"<PROMPT: continue from this exact moment ...>","medias":[{"value":"<IMAGE_MEDIA_ID_LAST_FRAME>","role":"start_image"}],"duration":5,"aspect_ratio":"9:16","sound":true}
```

### 2.5 Parameter gotchas

- `sound` is a **boolean** here but a string on `kling3_0` [HF S2].
- Only 5 or 10 s; request one of them exactly [HF S2, S7].
- No `end_image` on Higgsfield although Kling's comparison lists start & end frames for 2.6 [OFFICIAL S5; HF S2].
- Dialogue in languages other than Chinese/English is translated into English [OFFICIAL S1].
- Kling's API prompt limit is 2,500 characters [SECONDARY S8]; 2.6 prompts rarely need more than ~120 words.
- Elements are documented only for `kling3_0`, Seedance 2.0 and Cinema Studio Video [HF S7].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| case | params to send | expected output | post-processing |
|---|---|---|---|
| `sound:true` | `aspect_ratio:"9:16"`, no resolution parameter | likely the 1080p tier → ~1080×1920: Kling prices native audio at a single rate (silent output has Professional and Standard rates) [OFFICIAL S1], third-party docs say native audio requires Pro/1080p [SECONDARY S12], Higgsfield lists 1080p max [HF S4] | ffprobe; deterministic downscale to 720×1280 with `atg.py conform` |
| `sound:false` | `aspect_ratio:"9:16"` | 720p or 1080p tier — unknown which Higgsfield uses [INFERRED] | ffprobe; downscale or scale-to-fill + minimal crop to 720×1280; never stretch |
| start frame | same + exactly-9:16 image | as above | conform the image to 9:16 before upload |

Native 720×1280 output cannot be guaranteed on this id; conformance is always a post step [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Official general formula:** "Scene (Scene Description) + Element (Subject Description) + Movement (Movement Description) + Audio (Dialogue/Singing/Sound Effects/Pure Music) + Other (Style/Emotion/Camera)" [OFFICIAL S1].
- Official examples label blocks `Visual:` and `Dialog:` and put subjects in square brackets (`[Narrator, soft female voice]`, `[ginger cat]`) (§4.0) [OFFICIAL S1].
- "Use quotation marks to clarify sound content"; "Avoid stacking too many elements (e.g., multiple ambient sounds + complex speech)"; "ensure image content matches the text description" [OFFICIAL S1].
- Kling's cross-model blog formula (Subject, Action, Scene, Camera, Lighting & Mood) is compatible [OFFICIAL S5b].
- **Length:** 2–5 sentences for 5 s, up to ~120 words for 10 s dialogue/singing [INFERRED]; ≤2,500 characters [SECONDARY S8]. English or Chinese prompts [OFFICIAL S1].

### 3.2 Subject and identity

- Describe each subject concretely once and reuse the same bracketed label; "Character labels must be unique and consistent" [OFFICIAL S1].
- With a start frame, identity comes from the image; keep text consistent with it [OFFICIAL S1].
- Prefer two speaking characters per clip [OFFICIAL S1; SECONDARY S11].

### 3.3 Action, motion and physical interaction

- One main action with direction, speed and end state; one clip = one continuous shot [HF S3].
- Sounds tied to actions: "[Object: Wooden Door] suddenly [Action: Slams] + [Sound Effect: Bang]" [OFFICIAL S1].
- Hands, grip, final placement and liquids per §3.14 [INFERRED].

### 3.4 Environment, lighting and style

- Scene first, with light direction and time of day ("In an afternoon room, sunlight filters through the blinds, creating striped light spots on the floor") [OFFICIAL S1].
- Ambience: "Scene + Sound Elements + Spatial Reverb" (e.g. "Echo in an Open Hall (Reverb)") [OFFICIAL S1]. Style, emotion and camera go last ("Other") [OFFICIAL S1].

### 3.5 Chronology, timing and multi-shot structure

- One continuous shot, no shot planning [HF S3]; order beats with "first … then … finally"; "First describe the action, then follow with the dialogue" [OFFICIAL S1].
- Numeric timestamps are undocumented for 2.6 [OFFICIAL S1 silent]. 10 s for dialogue or singing; 5 s for one action [OFFICIAL S1]. Multi-shot sequences = one clip per shot, chained by frames [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

- Explicit directional terms (push in, pull back, pan left, tilt up, tracking shot, static shot), one move per clip [OFFICIAL S5b vocabulary; INFERRED one-move rule].
- API `camera_control` presets are not exposed [HF S2; SECONDARY S10]; describe start framing, move and end framing. Static: "static tripod shot; the camera does not move" [INFERRED].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

N/A beyond the start frame: no reference roles or Elements [HF S2, S7]. Kling's custom voices (`[Character Name] @VoiceName: 'Dialogue'`) are app-only [OFFICIAL S1].

### 3.8 Start and end frames

- Start frame only; describe what changes; keep text and image consistent; use high-resolution, clean frames [OFFICIAL S1; INFERRED].
- End frame: N/A on Higgsfield [HF S2]; describe the ending pose explicitly or use `kling3_0` with `end_image`.

### 3.9 Audio, dialogue and sound (if supported)

Official formats [OFFICIAL S1]:
- **Single speaker:** "[Man speaking], "Sentence" + Deep + Fast".
- **Multiple speakers:** "[Character A, angrily] says, "Sentence" [Character B, calmly] replies, "Sentence"" — labels unique and consistent; action first: "The black-suited agent slams his hand on the table. [Black-suited Agent, angrily shouting]: "Where is the truth?""
- **Narration:** `Visual: … Dialog: [Narrator, <voice>] …`.
- **SFX:** "Sound Source (Action/Object) + State + Professional Sound Effects". **Ambience:** "Scene + Sound Elements + Spatial Reverb".
- **Singing:** ""Lyrics" + Singing Style + Accompaniment + Emotion". **Rap:** ""Sentence (Rhyming)" + Rhythm Style + Emotion".
- **English casing:** "please use lowercase letters for English words whenever possible. When referring to acronyms or proper nouns, please use uppercase letters".
- **Silence:** `sound:false` [HF S2].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield [HF S2] (Kling's API has one [SECONDARY S8]).
- Positive description first; one short exclusion sentence targeting this clip's risks; for audio say what the soundtrack contains ("only rain and footsteps; no music, no voice") [INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

- **(a) Reliability:** no official 2.6 text-rendering claim; Kling introduced "native-level text output" with 3.0 [OFFICIAL S5]. Treat any 2.6 in-frame text as pseudo-text [INFERRED].
- **(b) Clean plate:** clean start frames of captions, handles, watermarks and signage; describe carriers as blank (plain signs, unlabelled packaging, screens with abstract colour); frame text-bearing surfaces out or defocus them; quoted strings only for spoken or sung lines (Kling uses quotes to mark sound content) [OFFICIAL S1]; end with "No captions, subtitles, signage text, logos or watermarks appear." [INFERRED].
- **(c) Intentional text:** not on this model — add in post, or use Kling 3.0 / Seedance 2.5 for scene text [INFERRED]. An approved label already in the start frame may stay; keep motion slow and verify it [INFERRED].
- **(d) Source text in edits:** N/A — no edit mode [HF S2].

### 3.12 Character / identity consistency

- Within a clip: one bracketed label and description per character; prefer two speakers [OFFICIAL S1; SECONDARY S11].
- Across clips: same approved still or previous last frame as `start_image`, identical identity wording [INFERRED]. No Elements on this id [HF S7]. Approved references replace source people by becoming the start frame [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Put the product in the start frame; "the <product> keeps its exact shape, proportions and colours from the first frame; one <product> only" [INFERRED].
- Gentle motion; no rotations to unseen sides; hand, grip, orientation and final placement described [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale / orientation / grip:** "[Barista] lifts the small glass jar with the right hand, fingers around its body, lid toward the camera; it is palm-sized" [INFERRED; bracket pattern OFFICIAL S1].
- **Scene light:** official examples describe light as scene elements ("sunlight filters through the blinds, creating striped light spots on the floor") [OFFICIAL S1]; make inserted objects receive it ("the stripes of light fall across the jar; its shadow lies to the right") [INFERRED].
- **Persistent states:** "the jar stays where it is set down; the lid stays on"; same hand until release [INFERRED].
- **Known failures:** voice attribution with 3+ speakers [OFFICIAL S1; SECONDARY S11]; otherwise undocumented.
- **Across clips:** last frame extracted locally → next `start_image`; "continuing from this exact moment" plus restated positions, hand contents and light; identical ratio, duration and `sound` [INFERRED]. No seed [HF S2].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

All from the KLING VIDEO 2.6 User Guide (S1):

- **E1 — single speaker:** "[Man speaking], "Sentence" + Deep + Fast"
- **E2 — two speakers:** "[Character A, angrily] says, "Sentence" [Character B, calmly] replies, "Sentence""
- **E3 — action first:** "The black-suited agent slams his hand on the table. [Black-suited Agent, angrily shouting]: "Where is the truth?""
- **E4 — sound effect:** "[Object: Wooden Door] suddenly [Action: Slams] + [Sound Effect: Bang]"
- **E5 — narration:** "Visual: In a tidy living room, a white robotic vacuum sits in the center, with no clutter around it. Dialog: [Narrator, soft female voice] accompanied by the gentle sound of vacuuming. […]"
- **E6 — ambience:** "In an afternoon room, sunlight filters through the blinds, creating striped light spots on the floor. A [ginger cat] lies on the windowsill. The [ginger cat] breathes slowly, with background sounds of distant birds and rustling leaves."

Patterns these teach [derived from E1–E6]:
- **Order:** scene and light → bracketed subject → action → audio (E5, E6).
- **Labels:** square-bracket tags for speakers and even subjects (`[ginger cat]`), reused verbatim; delivery inside the tag ("[Character A, angrily]") (E2, E6).
- **Blocks:** `Visual:` and `Dialog:` separate picture from sound (E5).
- **Speech:** double quotes around spoken words; voice qualities appended ("+ Deep + Fast") (E1, E2).
- **Causality:** the physical action sentence precedes the line or sound it motivates (E3, E4).
- **Detail level:** short concrete scene sentences; one subject, one action (E6).
- **Exclusions:** expressed positively ("with no clutter around it") (E5).
- **Time:** no timestamps or shots — single continuous moments.

### 4.1 Text-to-video

```text
Visual: <scene: place, time, light direction>. <[Subject label] with concrete features> <one continuous action: first …, then …>. <Camera: one move or static>. <Style/emotion>.
Dialog: [<Speaker>, <tone>] says, "<line>" / <SFX: [Object] <state> + [Sound Effect: …]> / <ambience: scene + sound elements + reverb>.
No captions, subtitles, signage text, logos or watermarks appear.
```
Worked example (10 s, `sound:true`):
```text
Visual: A quiet bakery kitchen before sunrise, warm light from a single pendant lamp above the counter. A [young baker] with a flour-dusted apron and rolled sleeves lifts a tray of bread rolls from the oven with both gloved hands, then sets it on the steel counter. Slow push in from a medium shot to a close-up of the rolls. Cosy documentary mood.
Dialog: The tray lands with a light metallic clatter. [young baker, cheerful and soft] says, "first batch, right on time." Oven hum with a faint echo off the tiled walls.
No captions, subtitles, signage text, logos or watermarks appear; the walls and tray are plain.
```

### 4.2 Start frame (and end frame) to video

```text
Visual: Starting from the first frame, <[subject] action: first …, then …>. <Camera: one move or static>. The <light> keeps falling <direction>; <shadow side>. Keep <identity, product shape and colours, layout> exactly as in the first frame.
Dialog: <audio as in 4.1>.
No captions, subtitles, logos or watermarks appear.
```
Worked example (5 s, `sound:true`):
```text
Visual: Starting from the first frame, the [brown dog] on the porch lifts its head, stands up, stretches its front legs, then trots down the two wooden steps toward the camera and sits on the lawn. Static camera at knee height. Morning sun from the left keeps its shadow on the right. Keep the dog's markings and size, the porch and the lawn exactly as in the first frame; one dog only.
Dialog: Morning birdsong, soft paws on wood, one short happy bark.
No captions, subtitles, logos or watermarks appear.
```
End frame: N/A on Higgsfield [HF S2].

### 4.3 Reference-to-video

N/A on Higgsfield — no reference roles or Elements [HF S2, S7]. Use `kling3_0` (Elements) or Seedance 2.0/2.5.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield for `kling2_6` [HF S2]. Extension ≈ chaining the last frame into a new start-frame clip (§3.14); edits → `kling_video_edit` or `seedance_2_5`; motion transfer → legacy `motion_control` (Kling 3.0 Motion Control) or Genjutsu `hf_mult_motion_control` [HF S7]. Two-person dialogue within one 10 s clip (E2/E3 pattern):
```text
Visual: <scene with light>. [<Character A>: description] and [<Character B>: description] <positions relative to an object>.
Dialog: <Character A action>. [<Character A>, <tone>] says, "<line>". <Character B reaction action>. [<Character B>, <tone>] replies, "<line>".
<Camera>. No captions, subtitles, signage text, logos or watermarks appear.
```
Worked example:
```text
Visual: A small repair shop at noon, daylight through the front window on the left. A [grey-haired technician] in a navy work shirt stands behind the counter; a [young customer] in a yellow raincoat stands in front of it holding a folded umbrella.
Dialog: The technician slides a small repaired radio across the counter. [grey-haired technician, calm and friendly] says, "good as new." The customer picks up the radio with both hands and smiles. [young customer, relieved] replies, "thank you, really." Faint street traffic outside.
Static medium shot from the side of the counter. No captions, subtitles, signage text, logos or watermarks appear; the radio and shop walls are unmarked.
```

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Line spoken by the wrong character | 3+ speakers; dialogue not tied to action | two speakers; action before each line; unique labels [OFFICIAL S1; SECONDARY S11] |
| Wrong language | Japanese/Korean/Spanish lines | only Chinese or English are voiced [OFFICIAL S1] |
| English words spelled out | capitals in English lines | lowercase English [OFFICIAL S1] |
| Audio doesn't match the image | prompt contradicts the start frame | keep text consistent with the image [OFFICIAL S1] |
| Busy, unstable result | "stacking too many elements" | one subject, one action, one camera move [OFFICIAL S1] |
| **Dead space** | 10 s with one small action | 5 s for one action; 10 s for dialogue or two beats [OFFICIAL S1; INFERRED] |
| **Arbitrary slow motion / speed changes** | no pacing words | "at natural real-time speed" [INFERRED] |
| **Unmotivated cuts** | multi-shot wording | one continuous shot per clip [HF S3] |
| **Morphing / identity drift / clothing change** | rotations to unseen sides; long motion | gentle motion; start frame; repeat the bracketed label and wardrobe [INFERRED] |
| **Duplicated objects** | object not counted | "one <object> only" [INFERRED] |
| Pseudo-text on signs/screens | visible text carriers | blank or out-of-frame carriers; exclusion line [INFERRED] |
| Caption/watermark from the start frame persists | uncleaned input | clean frames before upload [INFERRED] |
| Output not 720p | no resolution parameter | ffprobe + `atg.py conform` [INFERRED] |

## 6. Model-specific features and controls

- Native audio types: narration, dialogue, singing/rap, ambience, object/action SFX, mixed [OFFICIAL S1].
- Boolean `sound`; 5/10 s; 16:9, 9:16, 1:1 [HF S2].
- Not on Higgsfield: std/pro tier choice, custom voices, end frame, negative prompt, cfg, camera-control presets [HF S2; OFFICIAL S1; SECONDARY S8].
- Kling 2.6 Motion Control exists in Kling's app (orientation matches video/image; 3–30 s motion clips) [OFFICIAL S6]; not reachable through this id.

## 7. Model-specific pre-generation checklist

- [ ] `aspect_ratio:"9:16"`; duration 5 or 10 (10 for dialogue/singing); plan the 720×1280 conform step.
- [ ] `sound` boolean set deliberately.
- [ ] `Visual:` / `Dialog:` blocks; Scene → Element → Movement → Audio → Other; quotes only for spoken/sung content.
- [ ] Speakers ≤2 with unique bracketed labels, action before each line, lowercase English.
- [ ] Start frame exactly 9:16, high-resolution, text-free, consistent with the prompt.
- [ ] One action and one camera move; integration (grip, size, light, shadow) stated; no stacked elements.
- [ ] Exclusion sentence for captions, signage text, logos, watermarks.
- [ ] `get_cost:true` preflight done.

## 8. Sources

- S1 [OFFICIAL] Kling AI — KLING VIDEO 2.6 User Guide (native audio, audio types, dialogue/SFX/ambience/singing/rap formulas, examples E1–E6, language and casing rules, multi-voice two-character guidance, 10 s recommendation, pricing tiers) — https://kling.ai/quickstart/klingai-video-26-audio-user-guide (accessed 2026-09-30)
- S2 [HF] Higgsfield live catalog snapshot — `higgsfield/catalog-snapshot-2026-09-30.json` (`kling2_6`)
- S3 [HF] Higgsfield blog — "Kling 3.0 is on Higgsfield: User Guide" ("Kling 2.6 generated one continuous clip per prompt, without shot planning" — its "without built-in sound" clause conflicts with Kling's guide and the catalog and is not used) — https://higgsfield.ai/blog/Kling-3.0-is-on-Higgsfield-User-Guide-AI-Video-Generation (accessed 2026-09-30)
- S4 [HF] Higgsfield help centre — "How do I use Kling" (Kling 2.6: clips with audio, 1080p, 5–10 s) — https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-kling (accessed 2026-09-30)
- S5 [OFFICIAL] Kling AI — Kling VIDEO 3.0 Model User Guide (2.6 vs 3.0 comparison; native-level text output introduced in 3.0) — https://kling.ai/quickstart/klingai-video-3-model-user-guide (accessed 2026-09-30)
- S5b [OFFICIAL] Kling AI blog — "Kling AI Prompt Guide: The Secret to Cinematic Video Prompts" (2026-08-07) — https://kling.ai/blog/kling-ai-prompt-guide (accessed 2026-09-30)
- S6 [OFFICIAL] Kling AI — Motion Control User Guide (2.6 motion control inputs and orientation options) — https://kling.ai/quickstart/motion-control-user-guide (accessed 2026-09-30)
- S7 [HF] Higgsfield MCP tool contract (`generate_video` call shape, `get_cost`, duration snapping, media intake, `jobs_wait`, Elements scope, legacy `motion_control`, Genjutsu routing) as verified for /analyze-then-generate, 2026-09-30
- S8 [SECONDARY] Kling 2.6 API parameters via mirrors (prompt/negative_prompt ≤2,500 characters, `cfg_scale` 0–1, `sound` on/off, std/pro) — search-index excerpts (e.g. https://picsart.com/api-platform/models/kling-v2-6/advanced) and Krea's Kling 2.6 reference https://www.krea.ai/docs/api-reference/video/kling-26.md (accessed 2026-09-30); Kling's own API reference was not retrievable
- S9 [OFFICIAL] Kling AI — KLING VIDEO O1 User Guide (image input rules) — https://kling.ai/quickstart/klingai-video-o1-user-guide (accessed 2026-09-30)
- S10 [SECONDARY] Comfy docs — Kling Camera Controls node (API `camera_control` presets) — https://docs.comfy.org/built-in-nodes/partner-node/video/kwai_vgi/kling-camera-controls (accessed 2026-09-30)
- S11 [SECONDARY] Atlas Cloud — "Kling 2.6 Review and Prompt Guide for Perfect Native Audio Sync" (3+-speaker attribution issues) — https://www.atlascloud.ai/blog/guides/kling-2-6-review (search-index content, 2026-09-30)
- S12 [SECONDARY] Unifically / Morphic Kling 2.6 model pages ("Pro mode unlocks native AI audio", Pro up to 1080p) — https://unifically.com/models/kling-2.6 (search-index content, 2026-09-30)

## 9. Open questions / unverified behaviour

- Which Kling 2.6 tier and pixel size Higgsfield returns for `9:16` with `sound:true` and with `sound:false` (1080×1920 vs 720×1280).
- Whether the start frame's ratio must equal `aspect_ratio` or is cropped/padded.
- Whether square-bracket labels are ever rendered as on-screen text (not reported; untested).
- Spurious-caption and pseudo-text rates at 9:16.
- Whether any end-frame support exists behind Higgsfield's `kling2_6`.
