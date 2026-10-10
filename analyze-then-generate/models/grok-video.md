---
guide: grok-video
title: xAI Grok Imagine Video (Grok Video) and Grok Imagine Video 1.5 (Grok Video 1.5)
provider: xAI (developer docs branded "SpaceXAI (xAI)")
higgsfield_model_ids: [grok_video, grok_video_v15]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: low
---

# Grok Video / Grok Video 1.5 — model engineering guide

> Scope: xAI's Grok Imagine video models generate short clips with native audio from text or a start image.
> This file covers `grok_video` ("Grok Video": text or start image → video) and `grok_video_v15`
> ("Grok Video 1.5": text, start image, image references and an audio/voice reference). xAI-native video
> editing, extension, last-frame and keyframe pins, and the audio switch are **not exposed on Higgsfield**.
> xAI publishes an API with example prompts but **no video prompting guide**, so this file is conservative.
> /analyze-then-generate renders **9:16 at 720p** (§2.6); visible text is mode-dependent (§3.11). There is no
> edit route here, so Edit-Mode jobs go elsewhere. The live `models_explore` catalog always wins over the
> parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Model mapping.**
  - `grok_video` → xAI `grok-imagine-video` ("text, image, video → video"). Inferred from the name and feature set [INFERRED].
  - `grok_video_v15` → `grok-imagine-video-1.5` (aliases `-preview`, `-2026-05-30`; "text, image → video") [OFFICIAL]. Higgsfield's own REST API documents it as "Grok Imagine Video 1.5" at `xai/grok-imagine-video/v1.5/reference-to-video` [HF].
- **Positioning.** "On grok-imagine-video-1.5, text-to-video supports native 1080p" [OFFICIAL]. Higgsfield: the model "holds detail and lighting from the input frame - so the result continues the original rather than reinterpreting it" [HF].
- **Timeline [SECONDARY]:** Grok Imagine 1.0 on 2026-02-02; Imagine Video 1.5 preview (image-to-video) on 2026-06-17; text-to-video, image/voice references and native 1080p added around 2026-07-31/08-01.
- **Best for:**
  - faithful animation of an approved start frame [HF];
  - clips up to 15 s [OFFICIAL];
  - reference casting and product placement ("virtual try-on, product placement, character-consistent storytelling, and voice identity") [OFFICIAL];
  - low cost ($0.05/s classic, $0.08/s 1.5 at xAI list price) [OFFICIAL].
- **Weaker at / unknown:**
  - no official prompting or negative-prompt guidance;
  - text is "hit-or-miss" [SECONDARY];
  - always-on audio [HF + INFERRED];
  - image **stretching** when the aspect ratio is forced [OFFICIAL];
  - reference mode capped at 720p, and on Higgsfield it cannot be combined with a first frame [HF].
- **Choose this model when** you need a 10–15 s shot from an approved 9:16 still, or (1.5) references plus one voice. **Choose another model when** you need end frames, editing, reliable in-frame text, or 9:16 guaranteed in reference mode.

| Operation | `grok_video` | `grok_video_v15` |
|---|---|---|
| Text-to-video | Prompt only (`aspect_ratio: "9:16"` available) | Not usable in the fixed format without a 9:16 frame (§2.6): generate a still, then image-to-video |
| Start frame → video | `start_image` (9:16) | `start_image` (9:16), the recommended route |
| Reference-to-video | N/A on Higgsfield | `image_references` (≤7) and/or `audio_references`, without `start_image` [HF]; 9:16 unguaranteed |
| End frame, keyframes, edit, extension | N/A on Higgsfield | N/A on Higgsfield |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `grok_video` | `duration` | 1–15 (s) | 5 | xAI range 1–15; xAI default 8 [OFFICIAL] |
| `grok_video` | `aspect_ratio` | `16:9`, `9:16`, `1:1` | not stated | With a start image, a different ratio **stretches** the image [OFFICIAL]. Always `9:16` here, with a 9:16 frame |
| `grok_video` | resolution | not exposed | — | xAI API default is 480p; 720p available [OFFICIAL]. The resolution Higgsfield delivers is unknown |
| `grok_video_v15` | `resolution` | `480p`, `720p`, `1080p` | `720p` | Always `720p` here. "Reference-to-video is capped at 720p" [OFFICIAL]; Higgsfield rejects 1080p in reference mode [HF] |
| `grok_video_v15` | `duration` | 2–15 (s) | 5 | Higgsfield REST: 1–15, default 5 [HF] |
| `grok_video_v15` | `aspect_ratio` | **none in the MCP catalog** | — | Higgsfield's REST schema has `aspect_ratio` (`auto` default; `9:16` allowed) [HF]. MCP pass-through is unverified |
| both | audio switch, negative prompt, seed | not exposed | — | xAI has `generate_audio` (default on) [OFFICIAL] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (both ids) | "the provided image as the starting frame" [OFFICIAL] | 1 | JPEG/PNG/WebP (Higgsfield also lists GIF) [OFFICIAL][HF]. Output "defaults to the input image's aspect ratio" [OFFICIAL] |
| `image_references` (1.5 only) | People, objects, clothing or visual elements "without locking the first frame" [OFFICIAL] | ≤7 [OFFICIAL][HF] | Tags `<IMAGE_0>`… in list order [OFFICIAL]. Higgsfield: "Choose either image_url or reference media (image_urls/audio_url); do not combine these modes" [HF] |
| `audio_references` (1.5 only) | Voice identity (`<AUDIO_0>`) [OFFICIAL] | xAI ≤3; Higgsfield REST takes a single `audio_url` [HF] | Caller clips ≤15 s. xAI GA covers preset voices; own-audio references are for "trusted partners, on request" [OFFICIAL]. Acceptance on Higgsfield is unverified |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 1–15 s (classic) and 2–15 s (1.5) on Higgsfield [HF]. Pick the shortest duration that holds the action (§5).
- **Resolution:** 1.5 offers 480p/720p/1080p, with references capped at 720p [OFFICIAL][HF]. Classic has no control [HF].
- **Aspect ratio:** xAI supports 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 [OFFICIAL]. Image-to-video follows the image unless `aspect_ratio` forces a different ratio, which stretches it [OFFICIAL].
- **Audio:** "Generated videos include an audio track by default" [OFFICIAL]. There is no switch on Higgsfield; strip the track locally for silence [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video (`grok_video`):
```json
{"model":"grok_video","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16"}
```
Start frame → video (`grok_video`; the frame is exactly 9:16):
```json
{"model":"grok_video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":10,"aspect_ratio":"9:16"}
```
Start frame → video (`grok_video_v15`; the 9:16 frame sets the ratio):
```json
{"model":"grok_video_v15","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":10,"resolution":"720p"}
```
"Text-to-video" on 1.5 in the fixed format: first generate a 9:16 still (image job), then animate it:
```json
{"model":"grok_video_v15","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"duration":8,"resolution":"720p"}
```
Reference mode (`grok_video_v15`; **probe first**, since 9:16 is not guaranteed; no `start_image`):
```json
{"model":"grok_video_v15","prompt":"<REFERENCE_PROMPT using <IMAGE_0>, <IMAGE_1>, <AUDIO_0>>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":8,"resolution":"720p"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Stretching.** A requested ratio that differs from the start image deforms products and faces [OFFICIAL]. Conform every start image to exactly 9:16 locally (scale-to-fill plus minimal crop; never stretch) [INFERRED].
2. **No first frame in reference mode** on Higgsfield [HF], so reference jobs cannot inherit 9:16 from a frame.
3. **Reference cap.** Any reference means ≤720p; 1080p is rejected [OFFICIAL][HF].
4. **Tag numbering.** xAI shifts reference tags by one when a first frame is set [OFFICIAL]. On Higgsfield the two modes cannot be combined, so references start at `<IMAGE_0>` [HF + INFERRED].
5. **Audio references.** Custom voice audio is gated at xAI [OFFICIAL]. Test acceptance, and have a described-voice fallback [INFERRED].
6. **Prompt length.** xAI fails "a prompt that is too long" without publishing the limit [OFFICIAL]. Stay under ~150 words [INFERRED].
7. **Always-on audio.** Every written line will be voiced [INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `grok_video` | `"aspect_ratio":"9:16"`; no resolution parameter | Unknown. xAI's API defaults to 480p [OFFICIAL]; the Higgsfield tier is unpublished. 720×1280 or about 480×854 [INFERRED] | 720×1280: none. 480p: `atg.py conform` scale-to-fill up to 720×1280 plus minimal crop; this upscale loses detail, so prefer `grok_video_v15` when quality matters | Start image conformed to exactly 9:16, plus `aspect_ratio: "9:16"`. The two must match, or the image is stretched [OFFICIAL] |
| `grok_video_v15` | `"resolution":"720p"` plus a **mandatory 9:16 `start_image`** (no aspect parameter in the catalog) | Follows the start image's ratio [OFFICIAL]: 720×1280 expected [INFERRED] | Conform only if the dimensions differ | The 9:16 start frame. For "text-to-video", create the 9:16 still first. Reference mode cannot carry a frame [HF], so it is excluded from the fixed format unless a probe (optionally adding the REST-documented `"aspect_ratio":"9:16"` [HF]) returns 720×1280 |

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

xAI publishes examples, not rules (§4.0) [OFFICIAL].
- **Higgsfield advice** [HF]: "Describe what moves and how - the camera move, the pacing, the atmosphere, and the sound you want"; be specific about direction ("slow push-in," "pan left," "embers drifting"). Use short prompts for exploration and detailed prompts for a specific shot.
- **Secondary guidance:** subject + action at the core; timecoded segments like "(0-4s)" for multi-beat shots or dialogue; avoid vague praise like "cinematic masterpiece" [SECONDARY: fal.ai].
- **Library formula** [INFERRED]: `camera move + subject + one directed action + what stays still + setting/light + one audio sentence + continuity/clean-plate line`. 40–120 words, English prose.

### 3.2 Subject and identity

Text-to-video (classic): give explicit appearance [INFERRED]. With a start image, name the subject generically and describe only change [HF + INFERRED]. Secondary advice is to state "what the still is" first [SECONDARY]; keep that to a few words so the frame is not re-imagined [INFERRED].

### 3.3 Action, motion and physical interaction

- **Anchor motion.** "Anchor the prompt to what should move and in what direction. Name the subject's action explicitly… so the model knows what to animate and what to hold steady" [HF].
- **Weight.** Secondary testing says "motion with weight" is its strength [SECONDARY].
- **Further rules** [INFERRED]:
  - state contact, direction, speed and end state;
  - say that states persist;
  - give each person a fixed visual handle (plus `<IMAGE_n>` in reference mode);
  - describe pours by stream, level and settling.

### 3.4 Environment, lighting and style

Undocumented beyond examples. In image-to-video, light comes from the frame, so describe only lighting changes [HF]. In text-to-video, name setting, time, light source and look [INFERRED].

### 3.5 Chronology, timing and multi-shot structure

No official syntax. The xAI reference example sequences with "then" [OFFICIAL]. Secondary practice uses "(0-4s)" timecodes [SECONDARY]. Use ordered sentences, add timecodes only for clips ≥8 s, and write "one continuous shot" [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

No camera controls. Examples use "slowly pan out the camera", "slow zoom in", "The camera dollies from the sunlit doorway to the window" [OFFICIAL]; "slow push-in", "pan left" [HF]. Use one camera move per clip [INFERRED].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

`grok_video_v15` reference mode only (no first frame on Higgsfield) [HF].
- **What references do:** images "incorporate specific people, objects, clothing, or other visual elements without locking the first frame" [OFFICIAL].
- **Binding:** by position, "The person from <IMAGE_0> presents the product from <IMAGE_1>… speaking with the voice from <AUDIO_0>" [OFFICIAL]. Pair each tag with a short description [INFERRED].
- **Inheritance:** inherit identity and objects only; never text, usernames or watermarks from analyzed material [policy].
- **Video references:** none on Higgsfield [HF].

### 3.8 Start and end frames

- **Start frame:** "Upload a frame, describe the motion" [HF]. In the fixed format it is mandatory for 1.5 and strongly recommended for classic (§2.6).
- **End frame:** N/A on Higgsfield. xAI's `last_frame` and `keyframes` (1.5) are not in the catalog [OFFICIAL][HF].

### 3.9 Audio, dialogue and sound (if supported)

- **Native audio is on** [OFFICIAL]. Name the ambient bed and one or two key effects, and say whether you want music [SECONDARY + INFERRED].
- **Dialogue.** Lines in double quotes are spoken with lip sync [SECONDARY]. xAI documents no syntax. Use `The man says: "<line>"` with a visible speaker and keep it short [INFERRED].
- **Voice (1.5 reference mode):** bind with `<AUDIO_0>`, using only approved voice recordings [OFFICIAL + policy].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field, and xAI gives no guidance [OFFICIAL: absent]. Describe the wanted state positively, add one short exclusion line at the end, and verify by QC [INFERRED].

### 3.11 Visible text

Policy: Edit Mode is not available on these ids (route to an edit model). Analyze Mode may add new text, by default in deterministic post.

**(a) Reliability.**
- **Official:** xAI makes no claim about text rendering in video [OFFICIAL: absent].
- **Evidence:** rendered text is "hit-or-miss… more miss than hit at small sizes"; practitioners "keep an empty area in the frame for a logo or a line and add the type during the edit" [SECONDARY: fal.ai].
- **Verdict:** unreliable. All captions and hooks go in post.

**(b) Clean plate.**
1. **Start from a clean 9:16 frame.** Image-to-video from a text-free frame is the most reliable clean plate [INFERRED].
2. **Text-to-video on 1.5.** It first generates an image and then animates it [OFFICIAL], so describe the opening composition with blank, unmarked surfaces.
3. **Closing line:** "No on-screen text, no subtitles, no captions, no logos, no watermarks." [INFERRED]
4. **Dialogue:** short, with a visible speaker [INFERRED].
5. **QC** sampled frames [INFERRED].

**(c) Intentional in-frame text.** Only via the start frame: the real asset, or a text-reliable image model. Keep it large and frontal, with slow camera motion. xAI documents no quoting convention [INFERRED].

**(d) Edit operations:** N/A on Higgsfield. xAI's native edit endpoint (output ≤720p, duration capped at 8.7 s) is not exposed [OFFICIAL][HF].

### 3.12 Character / identity consistency

- **Approved people:** a 9:16 start frame of the person. The model "keeps the look and lighting of your original" [HF], and secondary testing says it "holds the identity of your source frame closely" [SECONDARY].
- **Reference mode (1.5):** front plus three-quarter images bound by tags, when a probe shows acceptable output [INFERRED].
- **Across clips:** reuse the same frame lineage and description text [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

1. The product sits in the 9:16 start frame at final scale; no ratio mismatch, since that stretches [OFFICIAL].
2. Prompt motion and rigidity ("the bottle stays upright and unchanged while the camera pushes in") [HF advice + INFERRED].
3. Avoid spins that reveal unseen sides [INFERRED].
4. In reference mode, bind "the product from <IMAGE_n>" [OFFICIAL] and restate shape, proportions and color [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

**Integration comes from the start-frame composite.** The model continues the frame "rather than reinterpreting it" [HF]. Build the composite with correct scale, perspective, contact shadow and matching light, then protect it in words [INFERRED]:
- **Scale:** "palm-sized, as tall as the cup beside it".
- **Orientation:** "front face toward camera".
- **Contact and grip:** "rests flat on the shelf"; "held in her left hand by the base, fingers clear of the front".
- **Occlusion:** "nothing passes in front of it".
- **Light inheritance:** "lit by the same cool window light from the right; soft shadow falling left; faint reflection in the glossy surface".
- **Persistent states:** "the lid stays open", "the glass stays half full", "it stays where she placed it", "same hand throughout".

**Known failures.** None are documented by xAI [OFFICIAL: absent]. In reference placement, scale and contact are not guaranteed; probe [INFERRED].

**Across clips.** No extension on Higgsfield. Chain via last good frame → next `start_image`. xAI's own tip for pinned frames: "Pins work best when they share a scene… each season is an image edit of it, so the tree, horizon, and camera angle stay identical" [OFFICIAL].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

xAI publishes API examples but no prompting guide, so official material is thin. Items 1–6 are xAI's own examples (https://docs.x.ai/developers/model-capabilities/video/generation, …/reference-to-video, …/extension); items 7–8 are the closest first-party Higgsfield material.

1. Image-to-video [OFFICIAL]:
   > Make the water crash down and slowly pan out the camera
2. Text-to-video [OFFICIAL]:
   > A glowing crystal-powered rocket launching from the red dunes of Mars, ancient alien ruins lighting up in the background as it soars into a sky full of unfamiliar constellations
3. Reference-to-video [OFFICIAL]:
   > slow zoom in on the white fashion runway stage. then, the model from <IMAGE_0> walks in from the back of the shot from the white opening, and gracefully walk out onto the front of the white stage platform. they wear the shirt from <IMAGE_1> and black flared jeans. they look dramatically at the camera. high quality slow motion shot. fun, playful. skin pores. highly detailed faces. perfect shot. […]
4. References with voices [OFFICIAL]:
   > The person from <IMAGE_0> presents the product from <IMAGE_1> on the set from <IMAGE_2>, speaking with the voice from <AUDIO_0>. A second speaker with the voice from <AUDIO_1> replies.
5. First and last frame (not exposed on Higgsfield) [OFFICIAL]:
   > The camera dollies from the sunlit doorway to the window, settling on the closing frame.
6. Extension (not exposed on Higgsfield) [OFFICIAL]:
   > The shot pans to an over the shoulder perspective. Calm controlled scene.
7. Higgsfield Grok 1.5 page [HF] (https://higgsfield.ai/grok-imagine-1.5):
   > Slow cinematic push-in as embers drift across the scene and the fabric stirs in the wind.
8. Higgsfield REST docs example [HF] (https://docs.higgsfield.ai/docs/models/grok-video-1-5/reference-to-video):
   > A cinematic wide shot of ocean waves at sunset, with gentle camera movement.

Patterns these teach:
- **Length:** short, often one sentence (1, 2, 5, 7, 8). Longer only for reference staging (3).
- **Image-to-video:** motion verbs plus camera verb in one imperative line (1, 7), with no re-description of the frame.
- **Order in reference prompts:** camera first ("slow zoom in…"), then "then, <subject from <IMAGE_n>> <action>", then wardrobe/objects "from <IMAGE_n>", then look (3). Voices are bound with "with the voice from <AUDIO_n>" (4).
- **Sentence style:** plain, even lowercase fragments. Quality keywords sit at the end (3).
- **Pacing:** slow motion appears **only when requested** (3). Otherwise imply real time.
- **Tone words:** "Calm controlled scene." sets pacing (6).
- **Exclusions and dialogue:** none shown in official examples. This library adds them per §3.10/§3.11.

### 4.1 Text-to-video

Classic only in the fixed format; follows patterns 2, 7 and 8 (one descriptive sentence plus a camera phrase).
```text
<Camera move> of <subject with appearance> <one directed action with end state> in <setting, time, light>.
<What stays still>. <Audio sentence>. One continuous shot, real-time pace. <Blank-surface clause>. No on-screen
text, no subtitles, no captions, no logos.
```
Example (`grok_video`, 8 s, 9:16):
```text
Low tracking shot moving alongside a grey-muzzled black dog as it runs across a wet beach at sunrise, splashes
through a shallow wave, and slows to a trot with a stick in its mouth. Low golden backlight, spray catching the light.
Audio: waves breaking, paws slapping wet sand, distant gulls. One continuous shot, real-time pace. The beach is empty
of signs and buildings. No on-screen text, no subtitles, no captions, no logos.
```

### 4.2 Start frame (and end frame) to video

Follows patterns 1 and 7 (imperative motion plus camera; no re-description).
```text
<Camera move> as <what moves, general terms, with direction>. <What stays still and unchanged>. <Audio sentence>.
One continuous shot, real-time pace. No on-screen text, no subtitles.
```
Example (either id; start_image = approved 9:16 still of a car parked on a road):
```text
Slow push-in toward the front of the car as its headlights switch on and light mist drifts across the road. The car
stays parked and unchanged in shape and color. Audio: a soft click, a low idle hum, light wind. One continuous shot,
real-time pace. No on-screen text, no subtitles.
```
End frame: N/A on Higgsfield.

### 4.3 Reference-to-video

Follows patterns 3 and 4 (camera first, then "then", subjects "from <IMAGE_n>", voice "with the voice from <AUDIO_0>"). Probe first (§2.6).
```text
<Camera move> in <setting>. then, the <person description> from <IMAGE_0> <action> with the <object description>
from <IMAGE_1>. The <object> keeps its exact shape, proportions and color. <Speaker> speaks with the voice from
<AUDIO_0>: "<short line>". <Audio bed>. One continuous shot, real-time pace. No on-screen text, no subtitles.
```
Example (`grok_video_v15`, references only, 720p):
```text
Slow push-in in a bright minimalist studio. then, the woman with shoulder-length braids from <IMAGE_0> lifts the small
white ceramic speaker from <IMAGE_1> off a wooden table and holds it at chest height. The speaker keeps its exact
rounded shape, proportions and matte finish. She speaks with the voice from <AUDIO_0>: "This one goes everywhere
with me." Soft room tone. One continuous shot, real-time pace. No on-screen text, no subtitles.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield. xAI's `/v1/videos/edits` and `/v1/videos/extensions` are not exposed [OFFICIAL][HF]. Edit-Mode jobs route to `gemini_omni_flash_1_1` or `flux_3_video_edit`.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Stretched or distorted subject | `aspect_ratio` differs from the start image [OFFICIAL] | Conform the frame to 9:16; request exactly 9:16 (classic) or omit it (1.5) |
| Wrong orientation on 1.5 | No aspect parameter; text or reference jobs [HF + INFERRED] | Mandatory 9:16 start frame; probe reference mode |
| 1080p rejected or ignored | References present [OFFICIAL][HF] | 720p always |
| Voice reference rejected | Gated custom audio [OFFICIAL] | Test; fall back to a described voice |
| Pseudo-text or subtitles | Text surfaces, dialogue [SECONDARY + INFERRED] | Clean start frame, blank surfaces, exclusion line, QC |
| Arbitrary slow motion (slop) | "slow motion" or quality-keyword prompts (xAI's own example requests it) [OFFICIAL example] | Leave it out; "real-time pace" |
| Dead space | Long duration (up to 15 s) for a short action [INFERRED] | Shortest duration that holds the action; add a second beat |
| Sudden speed changes | Several moves in one prompt [INFERRED] | One camera move; "steady" |
| Unmotivated cuts | Unspecified continuity [INFERRED] | "One continuous shot" |
| Morphing, duplicated objects, clothing changes, identity drift | Over-long clips, re-described frames, text-only people [INFERRED] | Start frame; motion-only prompt; "a single …"/"the same …"; restate wardrobe as unchanged |
| Unwanted sound | Always-on audio [OFFICIAL + HF] | Strip audio in post |

## 6. Model-specific features and controls

- **Two tiers:** classic (cheaper; 9:16 selectable) vs 1.5 (720p/1080p, references, one voice on Higgsfield) [OFFICIAL][HF].
- **Text-to-video on 1.5 runs text→image→video internally** [OFFICIAL]; the opening frame is decided first.
- **Long clips** up to 15 s [OFFICIAL][HF].
- **Reference-to-video with tags** (1.5) [OFFICIAL]; mutually exclusive with a first frame on Higgsfield [HF].

## 7. Model-specific pre-generation checklist

- [ ] Start frame conformed to exactly 9:16 (never stretched); classic sends `"9:16"`, 1.5 relies on the frame.
- [ ] 1.5 at `resolution: "720p"`; reference mode only after a probe returns 720×1280.
- [ ] No `start_image` together with references on 1.5 [HF].
- [ ] Motion-first prompt: direction, what stays still, one camera move, "real-time pace", shortest fitting duration.
- [ ] Tags from `<IMAGE_0>`, each with a description; voice clip approved and ≤15 s.
- [ ] Clean plate (blank surfaces plus exclusion line); Analyze-Mode text planned for post.
- [ ] Integration phrases (scale, contact, grip, light, shadow, persistent states).
- [ ] `get_cost` done; output probed (dimensions; classic may be 480p) and QC'd.

## 8. Sources

- [OFFICIAL] Imagine Overview (xAI) — https://docs.x.ai/developers/model-capabilities/imagine — accessed 2026-09-30
- [OFFICIAL] Video Generation (xAI) — https://docs.x.ai/developers/model-capabilities/video/generation — accessed 2026-09-30
- [OFFICIAL] Image-to-Video (xAI) — https://docs.x.ai/developers/model-capabilities/video/image-to-video — accessed 2026-09-30
- [OFFICIAL] Reference-to-Video (xAI) — https://docs.x.ai/developers/model-capabilities/video/reference-to-video — accessed 2026-09-30
- [OFFICIAL] Video Editing / Video Extension (xAI) — https://docs.x.ai/developers/model-capabilities/video/editing — accessed 2026-09-30
- [OFFICIAL] Inference API — Videos (REST reference) — https://docs.x.ai/developers/rest-api-reference/inference/videos — accessed 2026-09-30
- [OFFICIAL] Models and pricing; grok-imagine-video(-1.5) model pages — https://docs.x.ai/developers/models — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract — as recorded for /analyze-then-generate — accessed 2026-09-30
- [HF] Higgsfield API: Grok Imagine Video 1.5 — Reference to video (schema, usage notes) — https://docs.higgsfield.ai/docs/models/grok-video-1-5/reference-to-video — accessed 2026-09-30
- [HF] Grok Imagine 1.5 on Higgsfield (FAQ, prompting tips) — https://higgsfield.ai/grok-imagine-1.5 — accessed 2026-09-30
- [SECONDARY] How To Use Grok Imagine: Prompts & Workflows, fal.ai (2026-07-26) — https://fal.ai/learn/tools/how-to-use-grok-imagine — accessed 2026-09-30
- [SECONDARY] Elon Musk shares tips on using Grok Imagine, Storyboard18 (January 2026) — https://www.storyboard18.com/amp/digital/elon-musk-shares-tips-on-using-grok-imagine-for-cinematic-ai-images-and-videos-87005.htm — accessed 2026-09-30
- [SECONDARY] GIGAZINE (2026-02-03) and AI Weekly launch reports (search-result summaries only) — https://gigazine.net/gsc_news/en/20260203-grok-imagine-video-generation-ai — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- Output resolution of `grok_video` on Higgsfield (xAI API default 480p) and its exact 9:16 dimensions.
- Whether `grok_video_v15` honours an `aspect_ratio` sent through MCP (it is absent from the catalog but present in Higgsfield's REST schema), and what `auto` yields in reference mode.
- Whether MCP also forbids `start_image` plus references (the REST docs forbid it), and how many `audio_references` MCP accepts (REST: one `audio_url`).
- Whether uploaded voice clips are accepted as `audio_references`; xAI gates custom voices.
- The mapping of `grok_video` to `grok-imagine-video` (inferred), and the tag order Higgsfield uses.
- Subtitle or pseudo-text behaviour with dialogue; there is no measurement.
