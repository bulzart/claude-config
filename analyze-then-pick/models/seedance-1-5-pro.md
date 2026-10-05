---
guide: seedance-1-5-pro
title: ByteDance Seedance 1.5 Pro
provider: ByteDance Seed (Seedance 1.5 pro), served by Higgsfield
higgsfield_model_ids: [seedance1_5]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# ByteDance Seedance 1.5 Pro — model engineering guide

> Scope: ByteDance Seed's Seedance 1.5 pro, the first Seedance model with native joint audio-video
> generation, as served by Higgsfield under `seedance1_5` ("Seedance 1.5 Pro — Reliable motion, improved
> quality"). On Higgsfield: text-to-video and first-frame / first-and-last-frame animation with native
> audio at 4, 8 or 12 s. No reference inputs, no edit, no extension. BytePlus ModelArk now lists
> `seedance-1-5-pro-251215` as **Retired** (replacement `dreamina-seedance-2-0-mini-260615`) [OFFICIAL S4];
> Higgsfield still serves `seedance1_5` [HF S5]. Project output format is fixed: 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** "A foundational model purpose-built for native, joint audio-video generation. It adopts a dual-branch Diffusion Transformer architecture, combining a cross-modal fusion module with a specialized multi-stage data pipeline" [OFFICIAL S1]; the report adds SFT + RLHF, >10× faster inference, "precise multilingual and dialect lip-syncing", "dynamic cinematic camera control" and "enhanced narrative coherence" [OFFICIAL S2].
- **Highlights claimed:** "monologues and multi-speaker conversations with millisecond-level lip-sync precision"; Mandarin plus Cantonese, Shaanxi and Sichuan dialects, English, Japanese, Korean, Spanish, Indonesian; "film- and television-grade narrative tension" [OFFICIAL S1].
- **Best for:** short 4/8/12 s dialogue or voice-over clips from text or one start frame; shot/reverse-shot conversations inside one clip; animating an approved still with sound [OFFICIAL S1].
- **Weaker at / absent:** no reference images, video or audio [OFFICIAL S3; HF S5]; no documented timestamp control [OFFICIAL S8]; only 4/8/12 s on Higgsfield [HF S5]; no text-rendering claims; retired upstream [OFFICIAL S4].
- **Choose this model when** a quick, reliable start-frame or text shot with native dialogue fits 4, 8 or 12 s and needs no references.
- **Choose another model when** you need references (Seedance 2.0/2.5), >12 s or precise beats (Seedance 2.5), edits/extensions (Seedance 2.5), or in-frame text (Seedance 2.5 with a text image, or Kling 3.0).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"seedance1_5"`, no `medias` | 4, 8 or 12 s |
| First frame to video | role `start_image` | ratio may be set or follow the image [OFFICIAL S3] |
| First + last frame | `start_image` + `end_image` | same ratio for both |
| Reference, edit, extension | N/A on Higgsfield | not supported by the model [OFFICIAL S3] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `seedance1_5` | `duration` | `4`, `8`, `12` (s) | `4` | "Duration of the output video in seconds." Other values snap [HF S6]; ModelArk allowed any integer 4–12 [OFFICIAL S3]. |
| `seedance1_5` | `resolution` | `480p`, `720p`, `1080p` | `720p` | "Output resolution of the video." Project: `720p`. |
| `seedance1_5` | `generate_audio` | bool | `true` | "Generate native audio for the video. Set false for a silent video." |
| `seedance1_5` | `aspect_ratio` (call-level) | `auto`, `16:9`, `9:16`, `4:3`, `3:4`, `1:1`, `21:9` | not stated | Project: `9:16`. ModelArk default `adaptive` [OFFICIAL S3]. |
| `seedance1_5` | `seed`, `camera_fixed`, `draft`, `return_last_frame`, `watermark`, `negative_prompt`, `-1` auto duration | — | — | **Not exposed on Higgsfield** [HF S5]. ModelArk had `seed` ("similar results, but complete consistency is not guaranteed"), `camera_fixed` ("the actual result is not guaranteed"), draft mode and last-frame return [OFFICIAL S3]. Approximations: camera lock in words (§3.6), last frame extracted locally (§3.14), exclusions in prose (§3.10). |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight without submitting) [HF S6].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame: identity, product, scene, composition | 1; ModelArk: 300–6000 px, w/h 0.4–2.5, <30 MB; jpeg/png/webp/bmp/tiff/gif/heic/heif [OFFICIAL S3] | the only identity/product input |
| `end_image` | last frame | 1, only with `start_image` | same ratio as the first frame [OFFICIAL S3] |

No `image_references`, `video_references` or `audio_references` [HF S5]. `medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S6].

### 2.3 Duration, resolution, aspect ratio, audio

- Duration 4 / 8 / 12 s [HF S5]; 24 fps [OFFICIAL S4]. Beat budget: 4 s ≈ one action, 8 s ≈ two beats or a short exchange, 12 s ≈ three to five shots [INFERRED].
- Resolution 480p / 720p / 1080p [OFFICIAL S3; HF S5].
- Aspect ratio: t2v takes a listed ratio or `auto`; first-frame tasks take a ratio or follow the image, centre-cropping a mismatched image [OFFICIAL S3].
- Audio: voice, SFX and BGM with the picture; "By default, Seedance 1.5 Pro automatically generates background music that matches the prompt" [OFFICIAL S1]; mono on ModelArk [OFFICIAL S3].

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight.

**Text-to-video**
```json
{"model":"seedance1_5","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**First frame to video** (exactly-9:16 image)
```json
{"model":"seedance1_5","prompt":"<PROMPT describing change from the frame>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**First + last frame**
```json
{"model":"seedance1_5","prompt":"<PROMPT describing the transition>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":4,"aspect_ratio":"9:16","resolution":"720p","generate_audio":false}
```
**Chained continuation** (last frame of the previous clip, extracted locally and uploaded) [INFERRED]
```json
{"model":"seedance1_5","prompt":"<PROMPT: continue forward from this moment ...>","medias":[{"value":"<IMAGE_MEDIA_ID_LAST_FRAME_OF_PREVIOUS>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```

### 2.5 Parameter gotchas

- Durations other than 4/8/12 are snapped or clamped — request exactly 4, 8 or 12 [HF S6].
- Don't append ModelArk's legacy inline commands (`--rs 720p --rt 16:9 --dur 5 --seed 11 --cf false`); request-body fields were "Strongly recommended" even on ModelArk [OFFICIAL S1].
- `end_image` requires `start_image`; one ratio for both [OFFICIAL S3].
- Retired on ModelArk; check `models_explore` before planning a run [OFFICIAL S4; HF S5].
- Prompt languages: Chinese and English [OFFICIAL S1]; ≤500 Chinese characters / 1,000 English words, as "lengthy text will lead to scattered information" [OFFICIAL S3].
- No Higgsfield Elements for this id (Elements are documented for Cinema Studio Video 2/3.0, Seedance 2.0 and Kling 3.0) [HF S6].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| operation | params to send | expected output | post-processing |
|---|---|---|---|
| t2v | `aspect_ratio:"9:16"`, `resolution:"720p"` | 720×1280 (official 1.5 pro grid) [OFFICIAL S3] | none; verify with ffprobe |
| first / first + last frame | `aspect_ratio:"9:16"`, `resolution:"720p"`, exactly-9:16 image(s) | 720×1280; a mismatched image would be centre-cropped by the model [OFFICIAL S3] | conform images to 9:16 before upload (`atp.py conform`: scale-to-fill + minimal crop); never stretch |

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Official formula:** "Subject + Movement + Environment (optional) + Camera movement (optional) + Aesthetic description (optional) + Sound (optional)" [OFFICIAL S1].
- "By detailing elements such as dialogue content, language choices, emotional progression, camera movement, and narrative structure, the model can generate audio and visuals that are more closely aligned" [OFFICIAL S1].
- Principles: clear, constrained subject and motion; the key visual cues; degree adverbs; prompt aligned with both picture and audio; one feature-based subject description reused throughout [OFFICIAL S1].
- **Form:** natural prose; multi-shot clips as "The shot begins with… The shot cuts to… Finally, the shot cuts back to…" or "Shot 1: … Shot 2: …"; dialogue on labelled lines after the scene [OFFICIAL S1] (§4.0).
- **Length:** official examples run from one sentence to ~150 words [OFFICIAL S1].

### 3.2 Subject and identity

- Define the subject with concrete visible features and reuse the description ("Use feature-based descriptions to define the subject consistently across the prompt") [OFFICIAL S1].
- In dialogue scenes "Accurately specify each character's personalized attributes (gender, age, clothing, actions)" so lips map to the right person [OFFICIAL S1].
- With a start frame, identity comes from the frame; describe the person by what the frame shows [INFERRED].

### 3.3 Action, motion and physical interaction

- Degree adverbs and explicit phases: "The doll first rotates slowly, then she stops rotating…" [OFFICIAL S1]; causal chains in order [OFFICIAL S1].
- One interaction per beat with hand, grip, contact and end state (§3.14) [INFERRED].

### 3.4 Environment, lighting and style

- Environment carries mood and sound ("On a rainy night, in a dim and rundown underground parking garage…") [OFFICIAL S1].
- "Consider specifying a clear aesthetic or stylistic reference in the prompt" [OFFICIAL S1] — describe it neutrally (palette, light, texture, animation technique) rather than naming real studios or works [INFERRED].
- Style stays consistent across cuts within one clip (official claim, shown with 2D-animated, 3D-animated and realistic examples) [OFFICIAL S1].

### 3.5 Chronology, timing and multi-shot structure

- Native multi-shot is part of the Seedance line since 1.0 [OFFICIAL S9]; 1.5 pro "Supports responding to shot switching timing" and "reverse-shot editing for dialogue scenes" [OFFICIAL S1].
- Numeric timestamps are undocumented for 1.5 pro; 2.0 still called precise timing unstable and 2.5 introduced it [OFFICIAL S8, S7]. Use shot order and relative words [INFERRED].
- End on a settled or frozen frame ("the room falls silent again, and the frame freezes") so the last frame chains cleanly [OFFICIAL S1].

### 3.6 Camera language and dedicated camera / motion controls

Official lens vocabulary [OFFICIAL S1]:
- **Angle:** high angle, low angle, bird view, eye-level. **Narrative perspective:** over-the-shoulder, "xx subjective view", surveillance, telescope, ant, peeping. **Subject angle:** front, profile, half-profile, back, top, bottom.
- **Shot size** with "Subject + Shot Size (e.g., Close-up of the man on the left, A bust of the woman in red)".
- **Movement:** dolly-in/out, pan, track, follow, rise, fall, whirl, rotate, surround, zoom; formula "Starting frame composition description + Shot movement + Shot movement amplitude + Ending frame composition description"; "Hitchcock shot = dolly-in/out + zoom-out/in; Bullet time shot = time slowdown + surround".
- `camera_fixed` is not exposed [HF S5]; write "static shot, fixed camera position; the camera does not move" [INFERRED from the official "a static shot" usage, S1].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

N/A on Higgsfield: no reference roles [HF S5]; ModelArk 1.5 pro supports only text, first frame, and first + last frames [OFFICIAL S3]. The start frame is the sole visual reference (§3.8); describe voices in words (§3.9).

### 3.8 Start and end frames

- The start frame anchors composition, identity, product and scene; write what changes from it [INFERRED].
- Official product-keyframe phrasing: "keeping the appearance, proportions, and materials of both the [product] and the model accurate and consistent, with no unnecessary elements added" [OFFICIAL S1].
- First + last: same ratio; describe the continuous action connecting them [INFERRED]. Remove unwanted text and watermarks from frames before upload (§3.11).

### 3.9 Audio, dialogue and sound (if supported)

- **Voice via wording:** emotion + tone + pace + `say:` + quoted line — "In a gentle emotional state, with a soft tone and a slow speaking pace, say: "…"" [OFFICIAL S1].
- **Language/dialect:** name it before the line ("He said in Cantonese, …"; "Korean dialogue: A: "…" B: "…"") [OFFICIAL S1]. Double quotes for dialogue [OFFICIAL S3].
- **Multi-speaker:** a scene sentence, a language header, then one labelled line per speaker, each speaker described in the scene [OFFICIAL S1].
- **Voice-over:** "Generate a video with voiceover: A deep, calm male voice says, "…"" [OFFICIAL S1].
- **SFX** tied to visible causes; **BGM** auto by default, style/pacing controllable ("accompanied by a heart-stirring symphony"; "clap hands in time with the drumbeats") [OFFICIAL S1]. For no music: "No background music; only ambient and action sounds" (2.5 wording; untested on 1.5) [INFERRED]. Silence: `generate_audio:false` [HF S5].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field [HF S5; OFFICIAL S3]; the 1.5 guide gives no negative-phrasing advice [OFFICIAL S1 silent].
- Positive constrained description first ("with no unnecessary elements added" is the official phrasing) [OFFICIAL S1], then one short exclusion sentence using Seedance 2.x wording [OFFICIAL S8 wording; applicability INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

- **(a) Reliability:** no official 1.5 statement or example of text rendering [OFFICIAL S1 silent]; ByteDance only made text claims from 2.0 on, and still lists text accuracy as a gap there [OFFICIAL S8]. Treat 1.5 in-frame text as unreliable [INFERRED].
- **(b) Clean plate:** clean the start/end frames of captions, handles, watermarks and signage first; describe text carriers as blank (plain walls, unlabelled boxes, a phone screen with soft abstract colour); keep quoted strings for dialogue only; end with the Seedance 2.x wording "keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo; do not generate a watermark" [OFFICIAL S8 wording; INFERRED for 1.5]; QA every 9:16 frame (portrait produced more spurious subtitles on 2.0) [OFFICIAL S8].
- **(c) Intentional text:** not recommended on this model — add text in post, or use Seedance 2.5 / Kling 3.0 for scene text [INFERRED]. An approved product label already visible in the start frame may stay; keep camera motion around it slow and verify legibility [INFERRED].
- **(d) Source text in edits:** N/A — no edit mode [HF S5].

### 3.12 Character / identity consistency

- Within a clip: gender, age, clothing and action per person, identical wording when referring back [OFFICIAL S1].
- Across clips: the start frame (approved still or previous last frame) plus the verbatim identity description are the only carriers [INFERRED]. Approved references replace source people by becoming the start frame [INFERRED].
- Official multi-person dialogue examples stop at four speakers [OFFICIAL S1]; keep ≤2–3 speakers for reliable lip mapping [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Show the product in the start frame; add the official fidelity sentence (§3.8) [OFFICIAL S1].
- Slow moves around it ("an extremely slow and smooth push-in to showcase … overall appearance and design details") [OFFICIAL S1]; avoid rotations to sides the frame never showed; use an end frame for the final product pose [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale, orientation, contact:** "held in the right hand, about palm-sized, label turned toward the camera; the thumb rests on the cap" [INFERRED]. Name what passes in front of what.
- **Scene light:** keep the frame's light direction and colour temperature explicit ("warm light from the window on the left keeps falling on the cup; its shadow stays on the right") [INFERRED]; official examples describe light on faces and props ("The light falls across the pages and their faces") [OFFICIAL S1].
- **Persistent states:** state positions and conditions at the start and end of each shot (lid on/off, liquid level, which hand holds); "the cup stays where it was set down" [INFERRED].
- **Known failures:** undocumented for 1.5 beyond general claims; 2.0 lists motion plausibility and multi-subject consistency as gaps [OFFICIAL S8]. Expect drift on unseen object sides [INFERRED].
- **Across clips:** extract the last frame locally (no `return_last_frame`), use it as the next `start_image`, begin with "continue forward from this moment; do not replay what happened before it", restate positions, hand contents and light; keep ratio, resolution and audio setting identical [INFERRED]. No seed [HF S5].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

All from the BytePlus Seedance 1.5 pro prompt guide (S1):

**E1 — motion with degree adverbs:** "The doll first rotates slowly, then she stops rotating and shows her cuteness in front of the camera."

**E2 — voice control:** "In a gentle emotional state, with a soft tone and a slow speaking pace, say: "You can take your time. I'm not rushing you.""

**E3 — two-person dialogue:** "In a warm, softly lit independent bookstore, two Americans—a man and a woman—stand shoulder to shoulder, flipping through the same book. The light falls across the pages and their faces. The camera makes an extremely subtle dolly-in, creating a quiet and intimate atmosphere. English dialogue: Man: "Did you ever read this one before?" Woman: "No, but… I think I want to, with you.""

**E4 — voice-over:** "Generate a video with voiceover: A deep, calm male voice says, "In the vast silence of the universe, our world is but a fleeting moment. Yet, within it, life thrives against all odds." The scene should slowly transition from night to dawn, with the stars gradually disappearing and the sun rising from behind the mountains."

**E5 — product keyframe:** "Generate a video based on the input lipstick product keyframe image, keeping the appearance, proportions, and materials of both the lipstick and the model accurate and consistent, with no unnecessary elements added. The overall style is a high-end e-commerce beauty commercial, clean, refined, and premium in tone. The video consists of three continuous shots: in the first shot, the camera performs an extremely slow and smooth push-in […]"

**E6 — shot timing:** "Shot 1: Medium shot. The character raises her hand and looks at her palm. Shot 2: Cut to a close-up of the hand. Faint glowing particles begin to appear around the palm, slowly drifting in the air. Shot 3: Cut to a close-up of the character's neck. The glowing particles spread upward. […] Shot 5: Cut to a close-up of her face. […] she smiles with satisfaction and says, "Merry Christmas.""

Patterns these teach [derived from E1–E6]:
- **Order:** scene and light → subjects with attributes → action → camera → dialogue block last (E3); image tasks open with the fidelity sentence (E5).
- **Sentence style:** plain declarative sentences; degree adverbs ("slowly", "extremely subtle") set speed and amplitude (E1, E3).
- **Time:** no timestamps — "first … then", "Shot N: … Cut to …", "slowly transition from … to …" (E1, E4, E6).
- **Subject vs camera:** separate sentences ("The camera makes an extremely subtle dolly-in…") (E3).
- **Dialogue syntax:** language header ("English dialogue:"), `Speaker: "line"`; delivery as "In a <emotion> state, with a <tone> and a <pace>, say:" (E2, E3).
- **Length:** 15–100 words; 12 s allows up to five short shots (E6).
- **Exclusions:** expressed positively ("with no unnecessary elements added") (E5).

### 4.1 Text-to-video

```text
<Scene: place, time, light direction>. <Subject with concrete features> <movement with degree adverbs: first …, then …>. <Camera: shot size + movement formula, or "static shot, fixed camera position">. <Aesthetic: palette, texture>. <Sound: ambience, action sounds, music or "no background music">. <Dialogue: In a <emotion> state, with a <tone> and a <pace>, <speaker> says: "<line>"> <Constraint sentence>.
```
Worked example (8 s):
```text
At dusk, at a quiet bus stop, cool blue street light reflects on the wet pavement. A young woman with short silver hair and a navy windbreaker checks the empty road, then slowly lowers her hood as light rain begins. The camera starts in a medium shot and performs a slow dolly-in to a close-up of her face. Realistic texture, soft reflections. Soft rain on the shelter roof, distant traffic, no background music. In a calm emotional state, with a low tone and a slow speaking pace, she says: "It's always late on Fridays." Keep it subtitle-free; avoid generating any text or subtitles; the shelter and signs are blank; do not generate a logo or watermark.
```

### 4.2 Start frame (and end frame) to video

```text
Based on the first frame, <what changes: subject action with degree adverbs, object state, camera move>. Keep <identity details>, <product appearance, proportions and materials> accurate and consistent, with no unnecessary elements added. <Camera>. <Light: direction and shadows stay as in the frame>. <Sound>. <Constraint sentence>.
[With an end frame:] The shot moves continuously from the first frame to the last frame: <connecting action>.
```
Worked example (4 s):
```text
Based on the first frame, a hand enters from the right, picks up the small round alarm clock by its base, turns it slowly so the face points at the camera, then sets it back in the same spot. Keep the clock's shape, proportions and colours accurate and consistent, with no unnecessary elements added. Static shot, fixed camera position. The desk lamp keeps lighting the clock from the left; its shadow stays on the right. Soft desk ambience, a light tap as the clock is set down, no background music. Keep it subtitle-free; the clock face shows plain hands without numbers or text; do not generate a logo or watermark.
```

### 4.3 Reference-to-video

N/A on Higgsfield — no reference inputs [HF S5]. Use `seedance_2_0` or `seedance_2_5`.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield [HF S5; OFFICIAL S3]. "Extension" = chaining the last frame into a new first-frame clip (§3.14). Multi-shot dialogue inside one 12 s clip follows E3/E6:
```text
<Scene with light; each character's gender, age, clothing>. The shot begins with a <shot size> of <both>. <Character A>, <emotion/tone>, says: "<line>". The shot cuts to a close-up of <Character B>, who <reaction> and replies <tone>: "<line>". Finally, the shot cuts back to <shot size>; <final action>; the frame holds. <Sound>. <Constraint sentence>.
```
Worked example:
```text
In a small workshop under warm lamp light from above, a bearded man in a denim apron and a young woman in a grey hoodie stand at a workbench over a half-built wooden stool. The shot begins with a medium shot of both. The man, calm and encouraging, says: "Sand it once more, then we glue." The shot cuts to a close-up of the woman, who nods and replies with a small smile: "Once more. Got it." Finally, the shot cuts back to the medium shot; she picks up a sanding block with her right hand and starts on the seat edge; the frame holds. Soft workshop hum, sanding sound, no background music. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo or watermark.
```

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Lines on the wrong speaker | speakers not described distinctly | gender, age, clothing and an action per speaker before the line [OFFICIAL S1] |
| Flat or wrong delivery | line without delivery cues | "In a <emotion> state, with a <tone> and a <pace>, say: …" [OFFICIAL S1] |
| Unwanted music | BGM on by default | explicit music policy or `generate_audio:false` + post audio [OFFICIAL S1; INFERRED] |
| Spurious subtitles / pseudo-text | quoted strings, text in the start frame, portrait framing | clean frames, blank carriers, constraint sentence, QA [INFERRED; OFFICIAL S8] |
| **Dead space** | 12 s with one small action | 12 s only for 3–5 beats; otherwise 4 or 8 s [INFERRED] |
| **Arbitrary slow motion / speed jumps** | vague pacing | degree adverbs for every movement; "real-time speed" [OFFICIAL S1 pattern; INFERRED] |
| **Unmotivated cuts** | multi-sentence scene read as shots | "a single continuous shot" when no cuts are wanted; explicit "The shot cuts to…" when they are [OFFICIAL S1; INFERRED] |
| **Morphing / invented product sides** | fast rotation from one frontal frame | slow moves; end frame for the final pose [INFERRED] |
| **Identity drift / clothing change across clips** | new clip without a frame | chain last frame → `start_image`; identical description [INFERRED] |
| **Duplicated objects** | object not counted | "one <object> only" with its position [INFERRED] |
| Wrong duration | value other than 4/8/12 | request 4, 8 or 12 [HF S6] |
| Model unavailable | retired upstream | check `models_explore`; fall back to Seedance 2.0 [OFFICIAL S4] |

## 6. Model-specific features and controls

- Native joint audio-video with multilingual and dialect lip sync [OFFICIAL S1].
- Shot/reverse-shot and shot-timing response inside one clip [OFFICIAL S1].
- Effects: "Accurately describe the trigger timing … the transformation process … the details after transformation … Audio design" [OFFICIAL S1].
- ModelArk-only (not on Higgsfield): seed, `camera_fixed`, draft mode, last-frame return, inline `--` commands [OFFICIAL S3]. No Elements [HF S6].

## 7. Model-specific pre-generation checklist

- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; duration exactly 4, 8 or 12 with a matching beat count.
- [ ] Start/end frames exactly 9:16, clean of captions, handles, watermarks and signage text.
- [ ] Subject + Movement + Environment + Camera + Aesthetic + Sound; no parameters or `--` commands in the text.
- [ ] Each speaker described; delivery phrase per line; language named; double quotes.
- [ ] Music policy stated (or `generate_audio:false`).
- [ ] One camera movement per shot or the static phrase; degree adverbs for pacing.
- [ ] Integration: grip, size, orientation, light direction and shadow for products; states restated per shot.
- [ ] Clean-plate constraint sentence; captions planned for post.
- [ ] `models_explore` still lists `seedance1_5`; `get_cost:true` preflight done.

## 8. Sources

- S1 [OFFICIAL] BytePlus ModelArk — Seedance 1.5 pro prompt guide (introduction, highlights, formula, dialogue, SFX, BGM, shot transitions, lens control, effects; examples E1–E6) — https://docs.byteplus.com/en/docs/ModelArk/2168087 (accessed 2026-09-30)
- S2 [OFFICIAL] Team Seedance — "Seedance 1.5 pro: A Native Audio-Visual Joint Generation Foundation Model", arXiv:2512.13507 — https://arxiv.org/abs/2512.13507 (accessed 2026-09-30)
- S3 [OFFICIAL] BytePlus ModelArk — Create a video generation task (API reference: 1.5 pro tasks, ratio/duration rules, centre-crop of mismatched first frames, pixel table 9:16 720p = 720×1280, `seed`, `camera_fixed`, draft, `generate_audio`, prompt length) — https://docs.byteplus.com/en/docs/ModelArk/1520757 (accessed 2026-09-30)
- S4 [OFFICIAL] BytePlus ModelArk — Model list (`seedance-1-5-pro-251215` Retired; replacement `dreamina-seedance-2-0-mini-260615`; 24 fps, 4–12 s) — https://docs.byteplus.com/en/docs/ModelArk/1330310 (accessed 2026-09-30)
- S5 [HF] Higgsfield live catalog snapshot — `higgsfield/catalog-snapshot-2026-09-30.json` (`seedance1_5`)
- S6 [HF] Higgsfield MCP tool contract (`generate_video` call shape, `get_cost`, duration snapping, media intake, `jobs_wait`, Elements scope) as verified for /analyze-then-pick, 2026-09-30
- S7 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.5 prompt guide ("Seedance 2.0 does not respond to timestamps … Seedance 2.5 supports integer-second timestamps") — https://docs.byteplus.com/en/docs/ModelArk/2607689 (accessed 2026-09-30)
- S8 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.0 series prompt guide (constraint wording, text-generation scope, "precise timing … is unstable", landscape vs portrait subtitle finding) — https://docs.byteplus.com/en/docs/ModelArk/2222480 (accessed 2026-09-30)
- S9 [OFFICIAL] ByteDance Seed — Seedance 1.0 technical report, arXiv:2506.09113 (native multi-shot, precise captioning) — https://arxiv.org/abs/2506.09113 (accessed 2026-09-30)

## 9. Open questions / unverified behaviour

- Whether Higgsfield's `seedance1_5` routes to the retired ModelArk endpoint or another deployment, and how long it stays listed.
- Whether Higgsfield returns exactly 720×1280 for `9:16` + `720p` and how it treats a non-9:16 start frame (ModelArk centre-crops).
- Whether "No background music" wording is honoured on 1.5 (documented only for 2.5).
- Spurious-subtitle and pseudo-text rates on 1.5 at 9:16 (no official data).
- Whether numeric timestamps have any effect on 1.5.
