---
guide: flux-3-video
title: Black Forest Labs FLUX 3 Video
provider: Black Forest Labs (BFL)
higgsfield_model_ids: [flux_3_video]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# FLUX 3 Video — model engineering guide

> Scope: FLUX 3 is BFL's multimodal flow model, trained jointly on images, video and audio. FLUX 3 Video
> generates 5–20 s clips with optional synchronized speech, effects and ambience. This file covers
> `flux_3_video`. Operations on Higgsfield:
> - text-to-video;
> - start frame, start + end frame, and possibly multi-frame "storyboard" image-to-video;
> - image references;
> - a video input that Higgsfield describes as continuation.
>
> Editing a supplied clip (Edit Mode) is the separate tool in `flux-3-video-edit.md`. BFL's draft/enhance
> loop, safety tolerance, 2K/4K and timestamped keyframes are **not exposed on Higgsfield**. FLUX 3 is in
> early access/preview. /analyze-then-generate renders **9:16 at 720p** (§2.6); visible text is mode-dependent
> (§3.11). The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** FLUX 3 "jointly learns from images, videos, and audio within a unified architecture" [OFFICIAL: BFL blog, 2026-07-23]. The video API launched in preview on 2026-08-04 with "Up to 20 seconds at FHD… 24 fps", "multilingual speech with strong lipsync, plus effects and ambience", and "Multiple scenes and camera angles in one generation, with accurate in-scene text and typography" [OFFICIAL]. Higgsfield: "Text-to-video, multi-frame image-to-video, and video continuation with synchronized audio" [HF].
- **Best for:**
  - the longest single generations here (20 s);
  - hard-cut multi-shot sequences in one clip;
  - pixel-exact first frames;
  - multilingual lip-sync;
  - motivated physical inserts (light in fog, liquids, contact);
  - short in-scene typography [OFFICIAL].
- **Weaker at / risky (per BFL's field guide):**
  - "close human performance";
  - "identity-critical products without conditioning";
  - "exact audiovisual synchronization";
  - "graphic sans-serif overlays and late-shot text";
  - "long multi-step narratives with exact timing" [OFFICIAL].
  - End-frame pinning is "experimental" [OFFICIAL].
- **Choose this model when** you need 10–20 s, planned cuts, an exact opening frame, multilingual speech, or a short physical text element. **Choose another model when** you need editing (use `flux_3_video_edit`), identity or product fidelity from references alone, or exact captions (post).
- **Role-ambiguity warning:** `image_references` and `video_references` each map to two different documented BFL behaviours (§2.5 #1). Probe before production use.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | no `medias` | BFL `t2v` [OFFICIAL] |
| Start frame / start + end | `start_image` (+ `end_image`) | Pixel-exact frames [OFFICIAL] |
| Multi-frame storyboard | Tagged "storyboard" [HF]; role mapping undocumented | §2.5 #1 |
| Image references | `image_references` | Semantics unverified (§2.5 #1) |
| Video input | `video_references` | Higgsfield: "video continuation" [HF] |
| Edit a supplied clip | N/A here → `flux_3_video_edit` | [OFFICIAL][HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `flux_3_video` | `duration` | 5–20 (whole seconds) | 5 | BFL: 5–20; continuation 5–15 [OFFICIAL]. Out-of-range values snap or clamp [HF] |
| `flux_3_video` | `resolution` | `720p`, `1080p` | `720p` | BFL `hd` comes straight off the generation; `fhd` is the "same generation" upsampled [OFFICIAL]. Always `720p` here |
| `flux_3_video` | `generate_audio` | bool | true | "Generate synchronized speech, effects, and ambience" [HF] |
| `flux_3_video` | `aspect_ratio` | `auto`, `21:9`, `2:1`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | not stated | Always `9:16` (not `auto`: "`auto` lets the harness choose from the prompt and any references") [OFFICIAL] |
| `flux_3_video` | draft, safety tolerance, qhd/uhd, version, negative prompt, seed | not exposed | — | BFL has no negative field either [OFFICIAL][HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | Opening frame, on screen "pixel for pixel" [OFFICIAL] | 1 | ≥256×256; PNG/JPEG/WebP [OFFICIAL] |
| `end_image` | Closing frame; the model fills the motion between [OFFICIAL] | 1 | "experimental: expect more variance… re-roll a miss" [OFFICIAL] |
| `image_references` | Either BFL `reference_images` (1–10 identity images that "never appear on screen") or interior storyboard keyframes (on screen) [OFFICIAL semantics; mapping unknown] | Higgsfield: "up to 10 reference frames" [HF] | Probe first |
| `video_references` | BFL `start_video` (continue from the final frames) and/or `reference_video` (carry the cast into a new shot) [OFFICIAL semantics; Higgsfield says continuation] | 1 video, ≤15 s, ≤50 MB [OFFICIAL] | Output ≤15 s with a video at 720p [OFFICIAL] |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 5–20 s, default 5 [HF]. For speech, "`duration` is a tempo control, not a length estimate… at 18s it does not pad with silence, it drags." Unhurried delivery runs about 2.1–2.5 words per second [OFFICIAL: BFL product-ads skill].
- **Resolution:** 720p here. 1080p is an upsampled finish of the same shot [OFFICIAL].
- **Frame rate:** 24 fps [OFFICIAL].
- **Aspect ratio:** explicit ratios are predictable. Mismatched input ratios "force the model to either crop or pad" [OFFICIAL: FLUX technical guide].
- **Audio:** on by default. For silence set `generate_audio: false`; do not prompt for "quiet room tone", which "may collapse into static or dead air" [OFFICIAL]. Audio off lowers cost during tests [HF].
- **Cost reference** (Higgsfield blog, approximate): 5 s 720p ≈ 27.5 credits; 20 s 720p ≈ 110 [HF]. Always run `get_cost`.

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video with audio:
```json
{"model":"flux_3_video","prompt":"<PROMPT>","duration":10,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Start frame → video (silent; the frame is 9:16):
```json
{"model":"flux_3_video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":false}
```
Start + end frame:
```json
{"model":"flux_3_video","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":10,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Image references (do not mix with start/end frames until verified):
```json
{"model":"flux_3_video","prompt":"<REFERENCE_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Continuation (source already 9:16; `duration` ≤15):
```json
{"model":"flux_3_video","prompt":"<CONTINUATION_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
A previous job can be chained as `{"value":"<JOB_ID>","role":"video_references"}` [HF]. Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas

1. **Role semantics are unverified on Higgsfield** [INFERRED]. BFL documents two behaviours each:
   - images: identity references never shown on screen, or keyframes shown pixel-exact;
   - video: continue from the final frames (`start_video`), or keep the cast in a new shot (`reference_video`).

   Run one 5 s / 720p / silent probe per role with a distinctive test object. Record whether the reference pixels appear verbatim, and whether a video input continues or recasts.
2. **One input type per request.** BFL: "keyframes and reference_images together return a 422" and "One video input per request" [OFFICIAL]. Do not mix until verified.
3. **Video input caps duration at 15 s** at 720p [OFFICIAL]. Continuation `duration` counts only the new segment [OFFICIAL].
4. **End-frame variance.** Re-roll misses [OFFICIAL].
5. **Early access.** Behaviour tracks `version: latest` [OFFICIAL]; re-verify after updates.

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `flux_3_video` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` | **704×1280**: BFL `hd` at 9:16. Dimensions are multiples of 32 [OFFICIAL]. The 720p ↔ `hd` mapping is [INFERRED] | **Required.** `atg.py conform`: scale-to-fill ×1.0227 to 720×1309, then center-crop 29 px of height → 720×1280 (≈2.2% crop; never stretch). BFL: "Crop the delivered frame if you need an exact standard size" [OFFICIAL] | Explicit `"9:16"` (not `auto`). Start/end frames conformed to 9:16 (≥704×1280 ideal, ≥256 px minimum). Continuation sources conformed to 9:16 first, since continuation follows the source frame [OFFICIAL] |

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Formats.** FLUX 3 accepts "a short phrase, long natural language, timestep prompting, and much more". Short prompts give fresh results; long prompts give precision, but "Over-stuffing can make motion less coherent" and "Length alone is not the goal" [OFFICIAL].
- **Directing.** "Think of your prompt as directing a scene, not describing a collection of objects" [OFFICIAL].
- **One-liner (default):** `[camera] shot of [subject] [action] in [environment]. [supporting visual and motion details]` [OFFICIAL].
- **Schema for long or multi-shot clips:**
  - Core summary;
  - Scene (per shot);
  - Subject description ("a fixed description held identically across shots");
  - Dynamic narrative (per shot, timecoded);
  - Audio (per shot);
  - Style & color (global) [OFFICIAL].
- **Checklist:** subject and action; camera direction; scene and atmosphere; motion qualities; continuity constraints [OFFICIAL].
- **Action budget:** "one subject action and one camera move per short clip" [OFFICIAL].
- **Beat budget:** 5 s = one beat; 10 s = 2–3 beats; 20 s = schema or explicit shots [INFERRED from OFFICIAL beat guidance]. Examples are English.

### 3.2 Subject and identity

- **Concrete nouns and verbs:** "vague adjectives leave the result to chance" [OFFICIAL]. Hold a fixed subject description verbatim across shots [OFFICIAL].
- **Several people:** identify each "by a visible role or stable description" (BFL: "orange-suited astronaut", "blue-suited astronaut") [OFFICIAL].
- **Visible style:** "tense" becomes "rigid posture, shallow breathing, and a slow push-in" [OFFICIAL].
- **Performance:** strong on facial expressions [OFFICIAL: blog], yet close human performance is a "park or reroute" lane [OFFICIAL]. Test first.

### 3.3 Action, motion and physical interaction

**Shot-craft order** [OFFICIAL]:
1. opening frame;
2. visible cause (contact in the same frame as the response);
3. physical response;
4. payoff (one final state usable as an edit point);
5. continuity contract;
6. audio intent.

**Motion rules** [OFFICIAL]:
- **Endpoints.** "A generated clip is trustworthy at its first and last frame and inventive in between." "The predictor is… whether the model must invent geometry it has never seen."
- **Machines.** Mechanical subjects need written imperfection ("stiff even steps, a faint mechanical tremor"), or they move human-smooth.
- **Pours.** They work with the spout "already centered above a wide visible opening", a short path, a visible level rise and a clean stop.
- **Collapses.** Sequence them ("flames, then wine, then plates, then chair").

### 3.4 Environment, lighting and style

- **Reliable lanes:** "atmospheric light in a medium", wet reflections, viscous macro, tactile contact and ignition, restrained noir [OFFICIAL].
- **Medium:** state it explicitly, and exclude the other when needed ("rendered anime cel animation only, NOT live action") [OFFICIAL].
- **Controls.** Cinema Studio genre/lens/lighting controls do not apply; describe them in the prompt [HF].

### 3.5 Chronology, timing and multi-shot structure

- **Continuous take:** "One continuous unbroken real-time shot, constant motion, no freezing" [OFFICIAL example].
- **Timesteps:** `0.0–1.5s — …`, keeping beats achievable ("two or three for a 5-second clip") [OFFICIAL].
- **Hard cuts:** `SHOT ONE: … HARD CUT. SHOT TWO: …`. "Consecutive shots must contrast hard (scale, location, color) or the cut blends into a continuous take" [OFFICIAL].
- **Don't mix structures.** "one continuous shot plus hard cuts" is a listed contradiction [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls

- **One contract.** "Camera is one physical contract: framing, angle, movement, focus. A locked-off camera cannot track; an extreme close-up cannot establish. Locked and deliberate by default" [OFFICIAL].
- **Locks are advisory.** "'Locked camera, no push-in, no pan, no zoom' still permits parallax and drift" [OFFICIAL].
- **Vocabulary:** BFL publishes a camera-term cheatsheet [OFFICIAL].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

**BFL semantics** [OFFICIAL]:
- **Reference images:** "1 to 10 images that define identity… the references never appear on screen". A multi-view sheet pins identity "harder than a single angle". "point at the references explicitly… and re-list the anchors that must survive".
- **Reference video:** "keep the cast, build a new shot". Re-describe the staging to recast it; write a new scene to move the cast.
- **Continuation:** "Continue this video from its final frames: <what those frames show>…"; carry the sounds across the seam.
- **Audio references:** none.

**Availability caveat.** On 2026-08-04 BFL said "Omni Reference with images and videos will be available soon". Its agent skills say the public endpoint has "no field that carries a subject's identity without putting the source on screen" [OFFICIAL]. Hence the probe in §2.5.

**Inheritance from analyzed or source clips.** Continuation inherits the final frames, **including any burned-in text**. Clean such a source (Edit Mode or locally) before continuing it [INFERRED].

### 3.8 Start and end frames

- **Start frame:** "Prompt the motion, not the scene… Re-describing what's in the frame… invites the model to re-imagine it" [OFFICIAL].
- **Start + end:** keep the frames related. "The wider the gap… the more… unpredictability". Stage the change in order and hold the camera still. Make the end frame as an image edit of the start frame [OFFICIAL].
- **Storyboard:** "Keep identity, palette, and viewpoint coherent". "a mid-clip pin is a deadline; say what the remaining seconds are for, or they trail off" [OFFICIAL].

### 3.9 Audio, dialogue and sound (if supported)

- **Layers:** speech, ambience, effects, music. Template: `[Shot and action]. Dialogue or voiceover: [speaker and exact words]. Ambience: […]. Effects: […]. Music: [style and role].` [OFFICIAL]
- **Speech:** "Put the exact spoken words in quotation marks and say who delivers them". Off-screen lines need a `voiceover` or `narration` cue [OFFICIAL].
- **Voice and effects.** Direct the voice with person, register, recording, delivery and a guardrail ("no announcer delivery"). "Effects are causal" [OFFICIAL].
- **Fit the clip.** Short lines in longer clips. Multi-speaker attribution is "review-heavy". The same voice across clips is "not guaranteed" [OFFICIAL].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field [OFFICIAL][HF]. General FLUX doctrine: negation can backfire ("a person without glasses" draws glasses), so write the positive: "no text" → "clean surfaces, unmarked, blank" [OFFICIAL]. BFL's **video** examples still end with explicit tails ("No on-screen text, no logos, no subtitles, no credits."; "No people anywhere… no human voices.") [OFFICIAL]. Use the positive description first, plus a short explicit tail [OFFICIAL pattern].

### 3.11 Visible text

Policy recap:
- **Edit Mode:** not this id; use `flux_3_video_edit`.
- **Analyze Mode:** new text is allowed, by default in deterministic post. FLUX 3 may render short scene-bound text in-frame.

**(a) Reliability, claims vs evidence.**
- **Claims:** "accurate in-scene text and typography" [OFFICIAL]; "Legible, well-placed text rendered as part of the scene — titles, signage, and lower-thirds that stay stable through motion" [OFFICIAL]; Higgsfield: text "stays readable even while it's moving" [HF].
- **BFL's own limits:**
  - "simple physical text: one handwritten or inked phrase can work; sequential character creation does not" (experimental lane);
  - park "CJK text as featured legible copy", "graphic sans-serif overlays and late-shot text", "sequential typewriter or stamp mechanics";
  - reserve "typography, subtitles, logos" for deterministic post "when exactness is a success condition" [OFFICIAL].
- **Verdict:** the most text-capable model in this library set for **one short physical phrase** in Latin script, shown early. Captions, subtitles, hooks and exact copy go to post.

**(b) Clean plate.**
1. Describe clean, unmarked surfaces [OFFICIAL doctrine].
2. Attach every quoted line to a visible speaker or a `voiceover` cue: "A quoted line without a visible speaker or a voiceover cue may be treated as text that belongs in the frame" [OFFICIAL].
3. End with "No on-screen text, no subtitles, no logos, no credits." [OFFICIAL tail]
4. Regenerate any start frame with "stray text on a prop"; the video stage amplifies it [OFFICIAL].
5. QC for "no garbled or duplicated text" [OFFICIAL].

**(c) Intentional in-frame text.** Quote the exact words and name the surface, following BFL's example 'the word "FLUX" assembling from light streaks' [OFFICIAL]. Example: `a hand-painted wooden sign reading "OPEN"`. Rules: one phrase; early in the shot; large; physical (sign, packaging, screen); no late overlays [OFFICIAL]. Keep scene text and dialogue distinct: dialogue always has a speaker [INFERRED].

**(d) Edit operations:** N/A on this id. A continuation source carrying captions must be cleaned first (`flux_3_video_edit` or local), because continuation inherits its final frames [INFERRED].

### 3.12 Character / identity consistency

- **Strongest documented lever:** a start frame of the approved person. Keyframes are the only inputs guaranteed on screen [OFFICIAL].
- **References:** a single-render multi-view sheet. Separate generations "drift apart in the details". Re-list anchors every prompt [OFFICIAL].
- **Voice:** identical voice direction; the performer is not guaranteed [OFFICIAL].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

1. **Real photos.** Derive stills from the real photo. Write invariants as named, falsifiable features ("base: shallow domed profile… vs a flat cylindrical puck") [OFFICIAL].
2. **Put the product in the keyframe.** "Prompt detail did not fix invention. Removing the invention did": with the object in the keyframe, "scale cannot drift" [OFFICIAL].
3. **Entrances.** "generate it leaving and reverse the clip", then re-derive timing [OFFICIAL].
4. **Rotation.** Avoid multi-revolution spins and two bodies rotating. Replace failed rotations with "light moving across a static object" [OFFICIAL].
5. **Approved labels:** keep them as in the keyframe (large, frontal). Never ask FLUX to re-letter them [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

**First-party rules:**
- **Grounding:** "Name the grounding in every prompt. Say the product's contact shadow and its reflection explicitly. A product can hold identity and motion perfectly and still look pasted onto the frame" [OFFICIAL].
- **Scale:** "If the object is in the keyframe, the model only has to move something it can already see, and scale cannot drift" [OFFICIAL]. Without it, the "phone" became "a featureless slab as wide as the pad" [OFFICIAL].
- **Occlusion:** a crank "deformed and vanished as the arm occluded itself" [OFFICIAL]. Keep hands and arms from crossing the asset.
- **Light:** "light moving across a static object" is "the most reliable motion in the system" [OFFICIAL]. Author light changes in the direction that reads correctly after any reversal [OFFICIAL].
- **Camera:** locks are advisory; design for slight drift [OFFICIAL].
- **Persistence:** the "Continuity contract: same set and geometry; no cuts, transitions, frozen or repeated frames, or resets" [OFFICIAL]. Higgsfield's FLUX example adds "SUBJECT LOCK… ENVIRONMENT LOCK: the architecture is rigid and static… no morphing walls… Color grade locked throughout… no color shift first frame to last" [HF].

**Phrasing for an asset** [INFERRED unless tagged]:
- "the matte-green ceramic bottle, the height of her hand, stands upright on the oak table";
- "her right hand grips its neck, fingers behind the label";
- "lit by the warm window light from the left like the rest of the room; its contact shadow falls right; a soft reflection sits in the varnish";
- "it stays exactly where she sets it, and the cap stays off, until the end".

**Known failures.** Invented geometry, self-occlusion, multi-revolution rotation [OFFICIAL]. "Geometry decays in the middle", so sample interior frames [OFFICIAL].

**Across clips.** Preserve a clean ending. Continue from the actual ending artifact, restate only invariants, and "do not recap completed action". Carry audio across the seam; never feed a stale file forward [OFFICIAL]. **Continuation on Higgsfield:** Higgsfield describes `video_references` here as video continuation that "extends an existing clip forward from its final seconds of picture and sound, keeping motion, camera, and audio consistent across the seam" [HF, https://higgsfield.ai/blog/flux-3-higgsfield]. BFL: the continuation "Continues your clip from its final frames"; "`duration` here is the length of the new segment, not source plus new"; input clip ≤ 15 s; "The maximum duration for video continuation (v2v) requests is now 15 seconds"; a continuation call takes one media field only [OFFICIAL, https://docs.bfl.ai/cookbook/video_edit_recast_continue and release notes 2026-08-17]. Prompt: "Continue this video from its final frames: <what they show>. <next action>". Unverified: whether Higgsfield maps the role to continuation or to a cast reference. Check that the first result opens on the source's last frame and that its length ≈ `duration`; drop the repeated opening frame at the join (`atg.py concat --seams continuous`).

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Sources: BFL Text-to-Video guide (https://docs.bfl.ai/guides/prompting_video_text_to_video), Audio and speech guide (https://docs.bfl.ai/guides/prompting_video_audio), cookbooks (https://docs.bfl.ai/cookbook/video_start_from_images, https://docs.bfl.ai/cookbook/video_edit_recast_continue).

1. Short:
   > A red fox leaping through fresh snow, telephoto.
2. Long natural language:
   > A red fox stalks across a wide snowfield at dawn, low winter light, a dark treeline fading into mist behind it. It slows, crouches, then leaps high and pounces into the fresh snow. Telephoto lens, shallow depth of field, locked-off camera panning gently to follow. Muffled paw steps and a soft breeze.
3. Multi-shot:
   > SHOT ONE: wide aerial of a desert highway at dawn, a single red car speeding through. HARD CUT. SHOT TWO: interior close-up, the driver's hands drumming the wheel. HARD CUT. SHOT THREE: from the roadside, the car shrinks into the heat haze. One music bed across all three shots.
4. Timesteps:
   > 0.0–1.5s — locked wide of a still harbor at dawn, boats motionless on glassy water / 1.5–3.0s — a slow push-in begins as gulls lift off the water / 3.0–5.0s — the sun breaks the horizon, warm light spreads and the camera settles
5. Dialogue:
   > A weather presenter on camera in front of a stylized storm map, speaking to the lens: "Storm season is here — and this time, we're ready." Confident delivery, clean studio lighting. No on-screen text, no subtitles.
6. Start frame (cookbook):
   > The video begins exactly on the provided image, the fully set dinner table holding still for a beat. Then the entire room begins to rotate slowly clockwise, ninety degrees over the length of the clip, so the right-hand wall becomes the new floor. […] The camera is locked rigidly to the room so the world itself appears to tip. Audio: […] No on-screen text.
7. Reference images (cookbook):
   > The stop-motion claymation badger from the reference images, same striped face, same brass spectacles, same mustard tweed waistcoat and clay fingerprints, stands in a wind-bent meadow at dusk holding a tiny clay clipboard. […] Handheld camera eases in to a chest-up framing. Audio: wind through dry grass, the creak of stiff clay as he turns, a single distant crow. No on-screen text, no subtitles.
8. Continuation (cookbook):
   > Continue this video from its final frames: the brass wind-up robot reaches the very edge of the workbench, its front foot steps out over nothing, and it keeps marching forward on the empty air, […] Audio: the clockwork ticking continues unbroken, […] One continuous shot. No on-screen text.

Patterns these teach:
- **Order:** subject + action + environment, then lens/camera, then audio, then the exclusion tail (2, 5, 7). One-liners compress to subject, action, lens (1).
- **Sentence style:** directorial prose. Mode-specific openers: "The video begins exactly on the provided image" (6); "Continue this video from its final frames: <what they show>" (8); "The <subject> from the reference images, same <anchor>, same <anchor>" (7).
- **Time:** `SHOT ONE … HARD CUT` (3); `0.0–1.5s —` timesteps (4); beats ordered with "then" (2, 6).
- **Subject vs camera:** the camera gets its own clause ("locked-off camera panning gently to follow"; "The camera is locked rigidly to the room") (2, 6).
- **References:** re-list identity anchors with "same …" (7).
- **Detail:** 7–110 words; one event per shot.
- **Exclusions:** explicit tails "No on-screen text, no subtitles." in nearly every official video example (5–8).
- **Audio:** an `Audio:` label with concrete sources. Speech is quoted with a named on-camera speaker (5). "One music bed across all three shots" (3).

### 4.1 Text-to-video

Follows patterns 2, 3 and 5.
```text
One continuous unbroken real-time shot. <Subject, fixed description> <one action: cause → response → payoff> in
<environment, time>. <Camera clause: framing, angle, one movement>. <Light source/direction, depth of field, look>.
<Speaker> says: "<short line>" | Audio: <ambience>, <effects tied to actions>. The set and every object keep the same
geometry throughout. Clean, unmarked surfaces. No on-screen text, no subtitles, no logos.
```
Example (10 s, 9:16, audio on):
```text
One continuous unbroken real-time shot. A small brass wind-up toy robot marches in a straight line across a
cluttered wooden workbench at night, stiff even steps with a faint mechanical tremor, and stops at the edge of the
bench. Low tracking shot level with the bench, moving slowly right. A single desk lamp rakes light from the left,
shallow depth of field, warm amber palette. Audio: low lamp hum, clockwork ticking locked to each step. The bench and
every object keep the same geometry throughout. Clean, unmarked surfaces. No on-screen text, no subtitles, no logos.
```
Multi-shot variant (pattern 3): `SHOT ONE: <wide>. HARD CUT. SHOT TWO: <contrasting close-up>. HARD CUT. SHOT THREE: <payoff>. One music bed across all shots. No on-screen text, no subtitles.`

### 4.2 Start frame (and end frame) to video

Follows pattern 6.
```text
The video begins exactly on the provided image. <What moves, in order, with direction>. <What stays fixed: shape,
set, light, contact shadow>. <Camera clause>. <Audio layers or none>. No on-screen text.
```
Example (start_image = approved 9:16 still of a product on a table; audio off):
```text
The video begins exactly on the provided image. Morning light slides slowly across the table from left to right,
passing over the ceramic bottle and its shadow; a thin curl of steam rises from the cup behind it. The bottle stays
perfectly still, with the same shape, proportions and contact shadow. Locked-off camera. No on-screen text.
```
Start + end: `The video begins exactly on the first provided image and ends exactly on the second: <stages of the change in order>. The camera stays locked off; the light and set never change. <Audio>. No on-screen text.`

### 4.3 Reference-to-video

Follows pattern 7 (use only after the §2.5 probe confirms reference behaviour).
```text
The <subject> from the reference images, same <anchor 1>, same <anchor 2>, same <anchor 3>, <action> in <new
setting>. <Camera clause>. <Light> with <grounding: contact shadow, reflection>. Audio: <…>. No on-screen text, no
subtitles.
```
Example (image_references = a two-view sheet of a handheld device):
```text
The handheld device from the reference images, same rounded-rectangle body, same matte sage-green shell, same single
circular button on the front, rests in the open palm of a person's hand on a sunlit balcony, then the hand tilts it
slowly toward the camera. Handheld close shot. Warm afternoon sun from the left, the device casting a soft shadow
across the palm. Audio: distant city hum, leaves rustling. No on-screen text, no subtitles.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

Continuation via `video_references` (if the probe confirms continuation), following pattern 8:
```text
Continue this video from its final frames: <what the last frames show>. <One next action>. <Camera continues its
current move>. <Established sounds continue unbroken>, then <new sound tied to the new action>. One continuous
shot. No on-screen text.
```
Example: `Continue this video from its final frames: the cyclist reaches the crest of the hill. She freewheels down the far side as the road curves left, the camera keeping the same low trailing angle. Wind and tyre hiss continue unbroken; a bell rings once as she passes a gate. One continuous shot. No on-screen text.`

Editing a supplied clip: `flux_3_video_edit`. Motion transfer: N/A.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Spoken line rendered as on-screen text | Quote with no speaker or voiceover cue [OFFICIAL] | Name the speaker or add "voiceover"; add "No on-screen text, no subtitles" |
| Frozen or repeated frames, stutter (slop) | Long single takes; "simple events can still stutter or jump scenes" [OFFICIAL] | "constant motion, no freezing", "real-time" [OFFICIAL examples]; shorter clips |
| Late scene switch or unexplained cut (slop) | No structure stated [OFFICIAL scorecard] | "One continuous unbroken shot", or explicit SHOT/HARD CUT, never both |
| Cut blends into a continuous take | Similar consecutive shots [OFFICIAL] | Contrast scale, location and color per shot |
| Dead space or trailing seconds | Pins without purpose; speech stretched by long duration [OFFICIAL] | "say what the remaining seconds are for"; duration = words ÷ 2.1–2.5 |
| Arbitrary slow motion | Unpaced prompts [INFERRED] | "real-time", "constant motion" [OFFICIAL phrasing] |
| Sudden speed changes or jerky pacing | Too many beats for the duration; pins too close ("extra anchors stiffen motion") [OFFICIAL] | "two or three [beats] for a 5-second clip"; pin only what matters; one camera move per beat [OFFICIAL] |
| Human-smooth machines | Default motion prior [OFFICIAL] | Write mechanical imperfection |
| Morphing walls or props; geometry decay | Complex travel, rotation; mid-clip invention [OFFICIAL][HF] | ENVIRONMENT/SUBJECT LOCK lines [HF]; keyframes; sample interior frames |
| Duplicate geometry, subject drift | No count, weak anchors [OFFICIAL scorecard] | "a single …"; keyframe the subject; re-list anchors |
| Identity or clothing drift | Unfixed descriptions [OFFICIAL] | Verbatim subject block; reference sheet |
| Floating or pasted product | No grounding [OFFICIAL] | Name the contact shadow and reflection |
| Invented object (wrong scale) | Object absent from keyframe [OFFICIAL] | Put it in the keyframe; generate it leaving and reverse |
| Unmotivated sparks, bells, effects | Decorative prompting [OFFICIAL] | Tie every effect to a visible cause |
| Camera drift despite lock | Locks are advisory [OFFICIAL] | Design for slight movement |
| 422 or rejection | Mixed inputs; duration over 15 s with a video [OFFICIAL] | One input type; duration ≤15 |

## 6. Model-specific features and controls

- **20 s generations; hard-cut multi-shot** [OFFICIAL].
- **Pixel-exact keyframes** (start, start+end; storyboard at BFL) [OFFICIAL]; Higgsfield mapping per §2.5.
- **Continuation and reference video** [OFFICIAL].
- **Multilingual lip-sync; native-script lines** [OFFICIAL].
- **Upsampled 1080p** (unused here) [OFFICIAL].
- **Iteration discipline:** one consequential change per re-roll; "After two structurally similar misses, change the concept or the production method, not the adjectives" [OFFICIAL].

## 7. Model-specific pre-generation checklist

- [ ] `aspect_ratio: "9:16"`, `resolution: "720p"`; plan `atg.py conform` 704×1280 → 720×1280.
- [ ] Role semantics probed, or `image_references`/`video_references` avoided; one input type per request.
- [ ] Start/end frames and continuation sources conformed to 9:16; the source is text-free before continuation.
- [ ] One continuous take **or** SHOT/HARD CUT; one action plus one camera move per beat; the remaining seconds have a purpose.
- [ ] Grounding named (contact shadow, reflection); locks for subject, environment and color; persistent states stated.
- [ ] Quoted lines have speakers or a voiceover cue; tail "No on-screen text, no subtitles, no logos"; Analyze-Mode text in post.
- [ ] Line length fits duration (about 2.1–2.5 words/s); silent clips use `generate_audio: false`.
- [ ] `get_cost` done; interior frames QC'd for geometry, text and identity.

## 8. Sources

- [OFFICIAL] FLUX 3 — Real World Models (BFL blog, 2026-07-23) — https://bfl.ai/blog/flux-3 — accessed 2026-09-30
- [OFFICIAL] BFL release notes (2026-08-04 launch; 2026-08-17 v2v limit; 2026-09-10 qhd/uhd) — https://docs.bfl.ai/release-notes — accessed 2026-09-30
- [OFFICIAL] FLUX 3 — Video (modes, parameters, resolution table, examples) — https://docs.bfl.ai/flux_3/flux3_video — accessed 2026-09-30
- [OFFICIAL] API reference: Generate a video with FLUX 3 — https://docs.bfl.ai/api-reference/utility/generate-a-video-with-flux-3 — accessed 2026-09-30
- [OFFICIAL] Prompting guides: overview, Text-to-Video, Audio and speech, Image-to-Video, Examples & Cheatsheet — https://docs.bfl.ai/guides/prompting_video_overview — accessed 2026-09-30
- [OFFICIAL] Technical Parameters: working without negative prompts — https://docs.bfl.ai/guides/prompting_unified_technical — accessed 2026-09-30
- [OFFICIAL] Cookbooks: Start a video from images; Recast and continue video; Multi-shot films — https://docs.bfl.ai/cookbook/video_start_from_images — accessed 2026-09-30
- [OFFICIAL] BFL Agent Skills (prompt-doctor, cinematic-inserts + field guide + scorecard, keyframes-continuation, audio-dialogue, generate, product-ads) — https://github.com/black-forest-labs/skills — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract — as recorded for /analyze-then-generate — accessed 2026-09-30
- [HF] Meet Flux 3 on Higgsfield (blog; references/frames, lock-style example prompt, pricing) — https://higgsfield.ai/blog/flux-3-higgsfield — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- **Role mapping (highest priority).** What `image_references` and `video_references` do on Higgsfield (identity reference vs keyframe; continuation vs recast), and how many images are forwarded.
- Whether `start_image`/`end_image` can be combined with `image_references` (BFL returns 422 for keyframes plus references).
- Whether more than two keyframes (storyboard) can be sent, and how they are timed.
- That Higgsfield `720p` equals BFL `hd` (704×1280 at 9:16). Confirm by ffprobe.
- Behaviour when `duration` exceeds 15 with a video input (snap, clamp or error).
- Credit effect of `generate_audio`; drift during early access (`version: latest`).
