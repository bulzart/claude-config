---
guide: wan-2-7
title: Alibaba Wan 2.7
provider: Alibaba Cloud (Wan / Tongyi Wanxiang team; API via Alibaba Cloud Model Studio, DashScope)
higgsfield_model_ids: [wan2_7]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# Alibaba Wan 2.7 — model engineering guide

> Scope: Wan 2.7-Video is a four-model suite upstream (text-to-video, image-to-video, reference-to-video, video
> editing) [OFFICIAL]. Higgsfield id `wan2_7` exposes only `start_image`, `end_image` and `audio_references`, so
> through Higgsfield it covers text-to-video, first-frame and first+last-frame image-to-video, and audio-driven
> generation — not reference-to-video, video editing or video continuation [HF/INFERRED]. Output format is fixed
> at 9:16, 720p (§2.6). The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** Launched April 2026 as "a comprehensive video generation model" with "director-level control",
  2–15 s at 720p/1080p, 30 fps [OFFICIAL]. Upstream ids `wan2.7-t2v` (snapshots 2026-04-25, 2026-06-12) and
  `wan2.7-i2v` (2026-04-25) [OFFICIAL]. Higgsfield: "Synchronized audio, character-consistent video" [HF].
  Superseded by Wan 3.0 as Alibaba's flagship [OFFICIAL].
- **Best for:** 5–15 s clips with native audio (auto-generated, or driven by your own track for lip sync and action
  timing) [OFFICIAL]; animating an approved 9:16 still; bridging two approved frames; multi-shot storyboards from
  one prompt [OFFICIAL]; expressive faces ("over 50 refined emotional expressions") [OFFICIAL].
- **Weaker at:** readable text ("Text renders approximately") [OFFICIAL]; exact lip sync; long choreography; orbits
  wider than ~45° [OFFICIAL]. No reference images or video input on Higgsfield, so identity comes only from the start
  frame or text, and Edit Mode is not possible.
- **Benchmarks:** Artificial Analysis (2026-09-30): text-to-video #12 (Wan2.7-260612, Elo 1029), image-to-video with
  audio #11 (Elo 1077) [SECONDARY].
- **Choose `wan2_7` when** a shot starts (and optionally ends) on approved 9:16 frames and needs synced audio or an
  uploaded voice/music track. **Choose another model when** you need reference images (`wan3_0`, `minimax_h3`), a
  supplied clip regenerated (`wan3_0`), >15 s, or a silent render switch (`wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | multi-shot controlled in the prompt [OFFICIAL] |
| Text + audio | `prompt` + one `audio_references` | upstream `audio_url`; audio drives the video [OFFICIAL/INFERRED mapping] |
| First frame → video | `start_image` | output aspect follows the image [OFFICIAL] |
| First frame + audio | `start_image` + `audio_references` | upstream `driving_audio`: "lip-sync and action timing" [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` (+ optional audio) | all three may be combined upstream [OFFICIAL] |
| Reference-to-video, video edit, continuation | — | N/A on Higgsfield (no reference or video roles) [HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `wan2_7` | `duration` | number, min 2, max 15 | 5 | "Duration in seconds (2-15)." [HF]; upstream integers 2–15, billed per second [OFFICIAL] |
| `wan2_7` | `resolution` | `720p`, `1080p` | `720p` | always `720p` under the fixed format (§2.6); upstream default 1080P [OFFICIAL] |
| `wan2_7` | `aspect_ratio` | `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | — | always `9:16`; honoured for text-only calls, ignored with a start frame (output follows the image) [OFFICIAL/INFERRED] |
| `wan2_7` | catalog flag | `supports_unlim: true` | — | unlimited-plan eligibility; not available on the capture account (`unlim.available:false`) [HF] |
| `wan2_7` | negative_prompt, seed, prompt_extend, watermark, generate_audio | — | — | not exposed on Higgsfield [HF]; see §2.5, §3.10, §3.11 |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | exact first frame (upstream `first_frame`) | 1; JPEG/PNG (no alpha)/BMP/WEBP, 240–8000 px, aspect 1:8–8:1, ≤20 MB [OFFICIAL] | required for every image-to-video combination [OFFICIAL]; must be 9:16 (§2.6) |
| `end_image` | exact last frame (upstream `last_frame`) | 1; only with `start_image` [OFFICIAL] | same limits; same size as the start frame [INFERRED] |
| `audio_references` | soundtrack that drives lip sync and action timing (upstream `driving_audio` / `audio_url`) | 1 file ("a maximum of one audio file"); wav/mp3, 2–30 s, ≤15 MB [OFFICIAL] | truncated to `duration`; if shorter, the rest of the video is silent [OFFICIAL] |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- **Duration** 2–15 s, 30 fps [OFFICIAL]; unsupported values are snapped/clamped [HF contract].
- **Resolution/aspect:** fixed 720p, 9:16 (§2.6). Text-to-video uses the requested ratio (720P 9:16 = 720×1280)
  [OFFICIAL]. Image-to-video: "The API does not currently support setting the aspect ratio directly… The model
  preserves the approximate original aspect ratio of the input first frame", scaling to the tier's pixel count with
  sides in multiples of 16 [OFFICIAL].
- **Audio is always produced:** without an audio input "the model automatically generates matching background
  music or sound effects" [OFFICIAL]; with one, it drives the video [OFFICIAL]. No silent switch on Higgsfield [HF];
  strip audio locally if a silent file is required [INFERRED].

### 2.4 Call recipes
Text-to-video:
```json
{"model":"wan2_7","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","resolution":"720p"}
```
Text + driving audio (duration ≈ audio length):
```json
{"model":"wan2_7","prompt":"<PROMPT describing who speaks/sings or moves to the audio>","medias":[{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":10,"aspect_ratio":"9:16","resolution":"720p"}
```
First frame → video (9:16 start image):
```json
{"model":"wan2_7","prompt":"<MOTION + CAMERA PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
First frame + driving audio (lip sync / action timing):
```json
{"model":"wan2_7","prompt":"<WHO SPEAKS, GESTURES, CAMERA>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
First + last frame → video (both 9:16, identical size):
```json
{"model":"wan2_7","prompt":"<PATH PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
A `<JOB_ID>` of a completed Higgsfield image job can be the `value` [HF]. Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. **`end_image` needs `start_image`.** Valid upstream combinations: first frame; first frame + audio; first + last
   frame; first + last frame + audio (plus two continuation combos not exposed here) [OFFICIAL].
2. **`aspect_ratio` does nothing with a start frame** [OFFICIAL FAQ] — a non-9:16 start frame yields a non-9:16 video.
3. **One audio file maximum;** longer audio is cut at `duration`, shorter audio leaves silence [OFFICIAL].
4. **No silent mode, negative prompt or seed** on Higgsfield [HF]. Upstream `prompt_extend` (LLM rewriting, default
   `true`) is not exposed → assume your prompt may be rewritten [OFFICIAL/INFERRED].
5. **`shot_type` no longer exists:** "Control shot structure with natural language in the prompt. The shot_type
   parameter has no effect." [OFFICIAL]
6. **Snapshot ambiguity:** which dated snapshot Higgsfield calls is undocumented [HF silent].
7. **Prompt limit** 5,000 characters, auto-truncated [OFFICIAL].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| mode | params | expected output | action |
|---|---|---|---|
| Text-to-video (± audio) | `"aspect_ratio":"9:16","resolution":"720p"` | 720×1280, 30 fps [OFFICIAL size table] | verify |
| Start frame (± end frame, ± audio) | same params (ratio ignored upstream) + a **9:16 start frame**, end frame of identical size | follows the frame's aspect at ≈720P pixel count with sides in multiples of 16 → 720×1280 for an exact 9:16 frame [OFFICIAL rules → INFERRED] | verify |

Require 9:16 frames (e.g. 1080×1920 or 720×1280) — crop or regenerate the still before upload; never rely on
`aspect_ratio` in frame mode. Finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to
exactly 720×1280, never stretched; a no-op when already exact). Expected loss ~0%; `conform` refuses losses above
12% — that means the frame ratio was wrong: fix the frame and regenerate [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
Official Wan formulas [OFFICIAL]:
- **Advanced (text-to-video):** Entity (description) + Scene (description) + Motion (description) + Aesthetic control +
  Stylization — "Most weak prompts cover entity and motion but skip aesthetic control and stylization — producing a
  static camera in an undefined void. Cover all five dimensions."
- **Image-to-video:** Motion + Camera movement — "The image defines the entity, scene, and style. Your prompt should
  focus on motion and camera movements."
- **Sound (Wan 3.0/2.7/2.6/2.5):** Entity + Scene + Motion + Sound description (voice / sound effect / BGM).
- **Multi-shot (Wan 3.0/2.7/2.6):** Overall description + Shot number + Timestamp + Shot content.

Wan 2.7 API examples open with a one-line overall description, then timed shots or a prose scene; the shared prompt
dictionary (generated with Wan 2.2/2.5) opens with shot-size/lighting/tone tags [OFFICIAL]. "The more accurate and
rich the description, the higher the quality" [OFFICIAL, Chinese guide]; 60–150 words per single shot, ≤5,000
characters [INFERRED/OFFICIAL]. Chinese and English [OFFICIAL]. Worked patterns: §4.0.

### 3.2 Subject and identity
Describe appearance with adjectives and short phrases ("a young woman with wavy auburn hair in a vintage floral
dress") [OFFICIAL]. In image-to-video the subject already exists — describe only what changes, never contradict the
frame [OFFICIAL formula]. Do not name real people [OFFICIAL].

### 3.3 Action, motion and physical interaction
Specify amplitude, speed and effect ("swaying violently", "moving slowly", "shattering the glass"); in
image-to-video use "quickly"/"slowly" [OFFICIAL]. Avoid "very long or complex action sequences" [OFFICIAL]. Official
physics examples narrate cause and effect with quantities ("bounces back up to a height lower than its starting
point… each bounce has slightly less force"; "rolling a short distance of about 20 cm before finally stopping")
[OFFICIAL] — copy this for hands, liquids and handled objects (§3.14).

### 3.4 Environment, lighting and style
Scene = background + foreground [OFFICIAL]. Official dictionary: light source (daylight, firelight, overcast,
clear-sky light), light type (soft, hard, side, rim/backlight), time of day, shot size, composition, lens, tone,
and styles (felt, 3D cartoon, pixel, claymation, puppet, black-and-white animation, tilt-shift, time-lapse)
[OFFICIAL]. In image-to-video the frame fixes the light; say it stays as in the first frame [INFERRED].

### 3.5 Chronology, timing and multi-shot structure
- Single shot: "Generate a single-shot video" (or "Generate single shot.") [OFFICIAL]. "If unspecified, the model
  interprets the prompt content" [OFFICIAL] — it may cut on its own.
- Multi-shot: "Generate a multi-shot video" or timed shots ("Shot 1 [0–3 seconds] wide shot: …") [OFFICIAL]; the
  official 15 s example uses five 3-second shots, each opening with the shot size [OFFICIAL].
- Start with a one-sentence overall description; mark transitions ("Hard cut transition, fixed camera position")
  [OFFICIAL]. In image-to-video, "maintaining subject consistency between shots" is advertised [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls
No camera parameters on Higgsfield [HF]. Prompt phrases: "camera pushes in", "camera moves left", "fixed camera",
"camera pulls out", "orbiting camera movement", aerial, over-the-shoulder, high-angle [OFFICIAL]. Intent: push-in =
intimacy/tension, pull-out = scale/isolation, tracking = alongside, orbit = importance, fixed = stillness [OFFICIAL].
"Keep the arc under 45 degrees — wider orbits risk spatial distortion" [OFFICIAL]. Official image-to-video camera
sentences state start and end ("The camera angle gradually rises from eye level, finally capturing its curious gaze
from a top-down view.") [OFFICIAL]. Marketing cites FPV dives and 360° orbits [OFFICIAL] — test before relying on
them.

### 3.7 References (image / video / audio)
Reference images and videos are N/A on Higgsfield for this id (upstream `wan2.7-r2v` is not exposed) [HF]. The only
reference-like input is `audio_references`, which **drives** the result: "The model uses it as a driving source for
lip-sync and action timing" [OFFICIAL]. Say who voices the audio and what else may be heard: "The audio of the video
consists entirely of the rap, with no other dialogue or noise." [OFFICIAL]

### 3.8 Start and end frames
The start frame is the first frame; describe motion and camera only [OFFICIAL]. First + last frame: describe the
transition that connects them [OFFICIAL example]; keep camera position, lighting and subject count compatible and
both frames 9:16 at identical size [INFERRED]. Upstream continuation to a specified end frame exists "eliminating
abrupt 'braking' effects" [OFFICIAL] but is not exposed; approximate with first+last frames [INFERRED].

### 3.9 Audio, dialogue and sound
- Voice = lines + emotion + tone + speed + timbre + accent; e.g. `He says, "…," in a relaxed tone, at a moderate
  speed, with a clear voice, in American English.` [OFFICIAL]. SFX = source material + action + ambient sound; BGM =
  score + style [OFFICIAL].
- Multi-speaker: unique labels, action before speech, distinct voice labels, linking words [OFFICIAL]. Exact-word
  lip sync "does not work reliably" [OFFICIAL]; with an uploaded voice track, describe mouth and gestures and let the
  audio carry the words [INFERRED].
- "No dialogue." / "No background music." are documented for Wan 3.0/2.7 reference mode [OFFICIAL]; their effect in
  t2v/i2v is [INFERRED].

### 3.10 Negative constraints
No `negative_prompt` field on Higgsfield [HF] (upstream: ≤500 characters [OFFICIAL]). Official Wan 2.7 examples
express exclusions as one short imperative sentence ("Do not add text.") [OFFICIAL]. Use one final sentence and
prefer positive descriptions of the wanted state — the upstream rewriter (`prompt_extend`, on by default) may reword
a trailing list [INFERRED].

### 3.11 Visible text
**(a) Reliability.** "Exact text legibility — Text renders approximately — specific words will not be precise"
[OFFICIAL]; Wan 2.7's text-rendering improvements were announced for the separate Wan2.7-Image model, not video
[OFFICIAL]. Treat in-frame text as unreliable.

**(b) Clean plate — default in Analyze Mode.** Generate without text and add hooks, captions and labels in post
(`atp.py captions`, libass). Official Wan 2.7 phrasing: "Do not add text." [OFFICIAL, wan2.7 reference example]; Alibaba's longer
Wan 3.0 form "Do not show any text, subtitles, numbers, interface elements, or watermarks on screen." works as the
same provider's wording [OFFICIAL for Wan 3.0 / INFERRED transfer]. Add positive text-free surfaces; never describe
signage, captions or screens with words, or quote non-dialogue strings (official example prompts that request a neon
sign reading "WAN" or bottom-of-screen subtitles treat them as content) [OFFICIAL examples]. The start frame must be
text-free: the model preserves what is in the frame.

**(c) Intentional in-frame text.** Not recommended. If scene-bound text must appear (a sign, packaging, a screen),
put it already rendered in the 9:16 start frame and write "the lettering on the <object> stays exactly as in the
first frame; no new text appears"; verify with `atp.py qc --mode analyze --allowed-text "<text>"` [INFERRED].
Everything else goes to post.

**(d) Edit operations — removing source text.** N/A on Higgsfield: `wan2_7` takes no video input [HF], so it cannot
regenerate a supplied clip. It can only re-animate a still; a frame taken from a supplied video must have its overlays
removed with an image tool first, and the result is new footage, not an edit [INFERRED]. Use `wan3_0` (or local
`atp.py clean --delogo` for small static overlays) for Edit Mode.

**(e) Watermark risk.** Upstream `watermark` defaults to `false` ("AI Generated", lower-right when true) and is not
exposed [OFFICIAL/HF]; invented corner marks remain possible [INFERRED]. `atp.py qc` OCR flags them — regenerate.

### 3.12 Character / identity consistency
Identity comes from the start frame (strongest) or from text. Use a 9:16 frame with the approved face clearly visible
and well lit; keep motion moderate and avoid long turns away from camera [INFERRED]. Reuse the same approved frame
family and identical appearance wording across clips [INFERRED]. Multi-character identity/voice locking lives in the
unexposed `wan2.7-r2v` [OFFICIAL/HF].

### 3.13 Product and object fidelity
Put the approved product in the start frame (and in the end frame if the clip must land on a packshot) [INFERRED].
State geometry: "the bottle keeps its exact shape, proportions, cap and label placement from the first frame; it does
not bend, stretch or change size" [INFERRED]. Keep handling simple (lift, rotate slowly, set down); avoid fast spins
that force the model to invent unseen sides [INFERRED].

### 3.14 Integration and continuity
**Across clips.** Extract the last frame of clip A (`atp.py last-frame --video <clip> --out <handoff.png>`), upload it as `start_image` of clip B
(`media_upload` → PUT → `media_confirm`) [HF contract/INFERRED]; last-frame→first-frame stitching is Alibaba's
recommended method for its first/last-frame models [OFFICIAL]. Keep lighting, time of day and wardrobe wording
identical [INFERRED].

**Inserted or replaced assets.** No reference roles: an asset must already be in the start (or end) frame. Describe
it with size relative to a hand or known object, orientation (which face to camera), contact and grip (which hand,
which fingers), occlusion ("her thumb covers the lower edge of the label") and end position [INFERRED structure].
Quantify like the official physics examples ("about 20 cm") [OFFICIAL style].

**Scene light on the asset.** The frame fixes the light; write "lighting, shadow direction and color temperature stay
as in the first frame" and name reflections or contact shadows on moving objects [INFERRED]. Official examples name
direction explicitly ("Light comes from the right side of the frame, creating a soft rim light on the characters'
silhouettes") [OFFICIAL].

**Persistent states.** Write end states per beat: placed objects stay put, containers stay open/closed, liquid level,
same hand ("she sets the glass down on the right corner of the table, where it stays, still half full") [INFERRED].
First+last frame mode locks the final state [OFFICIAL capability].

**Known failures.** Long or complex action, rapid scene changes within a clip, exact-word lip sync, text, orbits
>45° [OFFICIAL]; abrupt "braking" at clip ends was the stated motivation for end-frame continuation [OFFICIAL]. Slop
prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. Timed multi-shot — Wan2.7 text-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
   > "A tense detective story with cinematic storytelling. Shot 1 [0–3 seconds] wide shot: Rainy New York street at
   > night, neon lights flicker, a detective in a black trench coat walks briskly. Shot 2 [3–6 seconds] medium shot:
   > The detective enters an old building, rain wets his coat, the door closes slowly behind him. Shot 3 [6–9
   > seconds] close-up: The detective's focused eyes, distant sirens sound, he frowns slightly. […]"
2. First frame + driving audio — Wan 2.7 image-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
   > "A scene of urban fantasy art. A dynamic graffiti art character. A boy made of spray paint comes to life on a
   > concrete wall. He sings an English rap song at high speed while striking a classic, energetic rapper pose. […]
   > The light comes from a single street lamp, creating a cinematic atmosphere full of high energy and amazing
   > detail. The audio of the video consists entirely of the rap, with no other dialogue or noise."
3. First + last frame — same page
   > "Realistic style, a small black cat looks up at the sky curiously. The camera angle gradually rises from eye
   > level, finally capturing its curious gaze from a top-down view."
4. Clip + last frame — Image-to-video 2.7 guide, https://www.alibabacloud.com/help/en/model-studio/wan-image-to-video-guide
   > "The man looks down at the wooden box on the ground. He bends over, carefully opens the lid, and stares at the
   > contents. His lips tremble and part slightly, his brow furrows, and his eyes widen with a horrified expression."
5. Sound and voice formulas — prompt guide, https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt
   > "A small glass ball falls from a table onto a wooden floor, making a "thud" sound in a quiet indoor
   > environment." · "A man is doing a stand-up comedy routine. He says, "Study hard and make progress every day," in
   > a relaxed tone, at a moderate speed, with a clear voice, in American English."
6. Exclusion — wan2.7 reference-to-video example, https://www.alibabacloud.com/help/en/model-studio/wan-video-to-video-api-reference
   > "Keep the characters and the forest scene consistent. Do not add text."

Patterns they teach:
- **Order:** one-line overall description → shots or scene → sound → one short exclusion (1, 2, 6).
- **Timed shots:** `Shot N [a–b seconds] <shot size>:` then content; contiguous 3-second shots (1).
- **Image-to-video = motion + camera:** the camera gets its own sentence with a start and end state (3); the subject
  is not re-described (3, 4).
- **Sentence style:** short sequential sentences, visible micro-expressions and physical consequences (4, 5).
- **Audio:** sound = source + action + ambience (5); voice = line + tone + speed + timbre + accent (5); with a driving
  track, state what the audio consists of (2).
- **Exclusions:** a short imperative sentence, not a list (6). **Length:** 20–90 words.

### 4.1 Text-to-video
Follows patterns: overall line, timed shots with shot size first, audio formula, one exclusion sentence.
```text
<One-line overall description>. Generate a single-shot video. <shot size>, <angle>, <light source + direction>, <tone>.
<Subject with 3–6 visual descriptors> <action with speed/amplitude, at real-time speed> in <scene: background + foreground>, <end state>.
The camera <move, from … to …>. <Sound: source + action + ambience | voice line + delivery | No dialogue. No background music.>
Do not show any text, subtitles, numbers, interface elements, or watermarks on screen.
```
Multi-shot variant: replace "Generate a single-shot video." with "Shot 1 [0–3 seconds] <shot size>: … Shot 2 [3–6
seconds] <shot size>: …".

Worked example (8 s, 9:16, 720p): "A quiet street moment. Generate a single-shot video. Eye-level medium shot, overcast
daylight, soft light, cool tones. A red vintage bicycle leans against a pale stone wall; a grey cat walks along the
top of the wall at real-time speed, pauses beside the handlebar, then hops down and trots out of frame to the right.
The camera holds a fixed position. Sound: soft paw steps, a distant bird, light wind. No dialogue. No background
music. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen."

### 4.2 Start frame (and end frame) to video
Follows patterns: motion + camera only, camera sentence with start and end, driving-audio statement.
```text
Generate a single-shot video. <What moves first, speed>, <then>, <end state>. The camera <from … to …>.
(FLF) The motion ends on the composition of the final frame: <pose/position>.
(Audio) <Who speaks/sings to the uploaded audio>; the audio consists only of <voice/music>, with no other dialogue.
Lighting, clothing and the scene stay as in the first frame. Do not add text.
```
Worked example (6 s, 9:16 `start_image` = a person at a desk holding a phone; `audio_references` = a 6 s spoken line):
"Generate a single-shot video. The person looks up from the phone toward the camera and speaks the line in the audio
with natural lip movement and a small nod, then sets the phone face-down on the right side of the desk, where it
stays. The camera pushes in slowly from a medium shot to a medium close-up. The audio consists only of their voice,
with no music. Lighting, clothing and the room stay as in the first frame. Do not add text."

### 4.3 Reference-to-video
N/A on Higgsfield — `wan2_7` exposes no image or video reference roles [HF]. Use `wan3_0` or `minimax_h3`.

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield — upstream `wan2.7-videoedit` and continuation are not exposed [HF]. Approximate an extension by
using a clean last frame as `start_image` [INFERRED].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Wrong output ratio | non-9:16 start frame [OFFICIAL] | 9:16 frames only (§2.6) |
| Unwanted music or voices | audio always generated [OFFICIAL] | describe the soundscape; "No background music."; strip locally |
| Audio cut off / silent tail | audio length ≠ `duration` [OFFICIAL] | match duration to audio |
| Gibberish text or subtitles | signage, screens, quoted non-dialogue text, text in the frame | §3.11 |
| Product warping | spins, extreme close moves | slow rotations, geometry sentence |
| Spatial distortion | wide orbits [OFFICIAL] | arcs ≤45°, slower camera |
| Muddled actions | too many actions per shot [OFFICIAL] | one or two actions per 3–5 s |
| Implausible FLF path | first/last frames too different [INFERRED] | compatible frames; describe the path |
| Lip-sync mismatch | exact-word expectations [OFFICIAL] | short lines; driving audio |
| Request rejected | `end_image` without `start_image` [OFFICIAL] | always pair |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | shortest `duration` that fits the beats; one visible change every 2–3 s [INFERRED] |
| Arbitrary slow motion | "at real-time speed"; Alibaba's Wan 3.0 wording "No slow motion" [OFFICIAL Wan 3.0 / INFERRED transfer] |
| Sudden speed changes / abrupt stops | state pacing; "slows and comes to rest naturally"; or pin the end with `end_image` [INFERRED] |
| Unmotivated cuts | "Generate a single-shot video" [OFFICIAL] |
| Morphing | "keeps its exact shape throughout"; end frame as anchor [INFERRED] |
| Identity drift | clear start frame, moderate motion, shorter shots [INFERRED] |
| Duplicated objects | "only one <object> in the scene" [INFERRED] |
| Clothing changes | "clothing unchanged throughout" [INFERRED] |

## 6. Model-specific features and controls
- **Prompt-controlled multi-shot** (no `shot_type`) [OFFICIAL].
- **Audio-driven generation** from one uploaded track (lip sync, action timing) in t2v and i2v [OFFICIAL];
  **auto-dubbing** otherwise [OFFICIAL].
- **First + last frame (+ audio)** in one call [OFFICIAL].
- Not exposed: reference-to-video, video editing, continuation, negative prompt, seed, prompt rewriting switch,
  watermark [HF]. `supports_unlim` catalog flag [HF].

## 7. Model-specific pre-generation checklist
- [ ] Mode: text / text+audio / start frame / start+end frame (+audio); `end_image` only with `start_image`.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; frames exactly 9:16, identical size, text-free; `atp.py conform`
      afterwards (§2.6).
- [ ] "Generate a single-shot video" or explicit timed shots with shot sizes.
- [ ] t2v covers entity, scene, motion, aesthetic control, style; i2v covers motion + camera only.
- [ ] Sound described or suppressed; audio length matches `duration`.
- [ ] Clean-plate sentence (§3.11b); captions/hooks planned for post (`atp.py captions`); no Edit Mode on this id.
- [ ] Asset size/grip, light continuity and end states written (§3.14); slop guards (§5).
- [ ] Prompt ≤5,000 characters; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze`: size, freezes, pseudo-text, corner marks, identity, product shape.

## 8. Sources
- [OFFICIAL] Wan2.7 – Text-to-Video API reference (incl. legacy 2.6 section, 720P size table) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] Wan 2.7 – image-to-video API reference — https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference (accessed 2026-09-30)
- [OFFICIAL] Image-to-video 2.7 user guide (FAQ on aspect ratio, multi-shot) — https://www.alibabacloud.com/help/en/model-studio/wan-image-to-video-guide (accessed 2026-09-30)
- [OFFICIAL] Video generation prompt guide (formulas, dictionary, what not to prompt) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt (accessed 2026-09-30)
- [OFFICIAL] 通义万相视频生成提示词指南 (Chinese edition) — https://help.aliyun.com/zh/model-studio/text-to-video-prompt (accessed 2026-09-30)
- [OFFICIAL] Video generation and editing (model list) — https://www.alibabacloud.com/help/en/model-studio/use-video-generation (accessed 2026-09-30)
- [OFFICIAL] Wan – reference-to-video API reference (wan2.7-r2v; "Do not add text." example) — https://www.alibabacloud.com/help/en/model-studio/wan-video-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] wan3.0 Video Generation Prompt Guide (Alibaba clean-plate and anti-slop phrasings) — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-prompt-guide (accessed 2026-09-30)
- [OFFICIAL] Alibaba Unveils Wan2.7-Video to Elevate Creators from Executors to Directors (2026-04-07) — https://www.alibabacloud.com/blog/alibaba-unveils-wan2-7-video-to-elevate-creators-from-executors-to-directors_603009 (accessed 2026-09-30)
- [OFFICIAL] Wan3.0 API reference FAQ (Wan 2.7 driving_audio vs Wan 3.0) — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json; Higgsfield MCP tool contract facts supplied with this task
- [SECONDARY] Artificial Analysis text-to-video / image-to-video leaderboards — https://artificialanalysis.ai/video/leaderboard/text-to-video ; https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Exact image-to-video output size for a 9:16 frame at 720P (720×1280 expected from the pixel-count rule).
- Exact upstream mapping of `audio_references` (t2v `audio_url` vs i2v `driving_audio`) and handling of a second
  audio item.
- Which dated `wan2.7-t2v` / `wan2.7-i2v` snapshots Higgsfield calls; whether `prompt_extend` stays on and
  `watermark` off.
- Whether `aspect_ratio` is ignored or rejected when `start_image` is present.
- Whether "No dialogue." / "No background music." are honoured in t2v/i2v as documented for reference mode.
- `supports_unlim` eligibility on the user's plan.
