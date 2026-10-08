---
guide: seedance-2-5
title: ByteDance Seedance 2.5 (incl. Higgsfield Ad Multiplier)
provider: ByteDance Seed (Dreamina Seedance 2.5), served by Higgsfield
higgsfield_model_ids: [seedance_2_5, ad_multiplier]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# ByteDance Seedance 2.5 — model engineering guide

> Scope: ByteDance Seed's Seedance 2.5 joint audio-video model as served by Higgsfield under two ids:
> `seedance_2_5` (text-to-video, omni-reference, video edit, video extension, draft/finalize) and
> `ad_multiplier` ("Ad Multiplier video generation powered by Seedance 2.5"; same modes, no draft fields;
> used by Higgsfield's own multi-variant edit recipe). Covers text-to-video, first/last-frame generation,
> generation from up to 50 image/video/audio references, keyframes, storyboards, clay-model blockouts,
> editing of a supplied 4–30 s video (replace/add/remove, text removal, audio edits) and forward/backward
> extension. Project output format is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** "The new-generation video creation model", built on the "unified multimodal audio-video joint-generation architecture" of Seedance 2.0 [OFFICIAL S1, S10], centred on "foundational generation and reference-based generation" with breakthroughs in "long-form storytelling, multimodal reference, and editing"; launched 2026-07-31 [OFFICIAL S1]. Up to 30 s per generation, up to 50 references (≤30 images, ≤10 videos, ≤10 audio), native audio in 11 languages [OFFICIAL S2, S3]. ByteDance calls it "not a cross-generational leap" over 2.0 but "systematic enhancements for real production scenarios" [OFFICIAL S2].
- **Best for:** scripted single-pass clips up to 30 s with integer-second timeline control; multi-reference casting (identity + product + scene + motion clip + voice); scoped edits of real footage (replace a product or person, remove captions/watermarks/objects, change background, audio edits and dubbing); extension; keyframe, storyboard and clay-model control [OFFICIAL S1, S2, S3].
- **Weaker at:** "the physical plausibility of complex motions and the stability of scenes involving interactions among multiple subjects" [OFFICIAL S1]; exact spelling of rendered text [OFFICIAL S2]; guaranteed subtitle-free and music-free output [OFFICIAL S2]; high-frequency actions under timestamps [OFFICIAL S2]; crowded frames (>4 people, 2.0 guidance) [OFFICIAL S6].
- **Choose this model when** the clip exceeds 15 s, needs many bound references, needs an edit or extension of an existing clip (including source-text removal), dubbing, or keyframe/storyboard/blockout control.
- **Choose another model when** you need Higgsfield Elements (listed for Seedance 2.0 and Kling 3.0, not 2.5), a one-object swap that must pass source audio and untouched pixels through (Genjutsu `hf_mult_replace_object` keeps source audio [HF S15]), or a short simple shot where 2.5's structure adds nothing.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `mode:"t2v"`, no `medias` | ratio and duration free [OFFICIAL S3] |
| First / first + last frame | roles `start_image` (+ `end_image`) | ratio locked to the first frame [OFFICIAL S2]; `mode` for this path undocumented (§2.5) |
| Omni reference, keyframes, storyboard, clay blockout | `mode:"omni_reference"` + `image_references` / `video_references` / `audio_references` | assets cited as `@ImageN` / `@VideoN` / `@AudioN` |
| Video edit | `mode:"video_edit"`, exactly one video (+ images) | length and ratio follow the source; billed by source duration [HF S11] |
| Video extension | `mode:"video_extension"` + `extension_mode` | ratio follows the source; `duration` = new segment [HF S11] |
| Draft → final | `draft:true` (480p) → `draft_job_id` (1080p) | `seedance_2_5` only; not the default path (§2.6) |
| Ad Multiplier recipe | `model:"ad_multiplier"`, `mode:"video_edit"`, silent + local audio restore | Higgsfield's production edit contract [HF S13] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `seedance_2_5` | `mode` | `t2v`, `omni_reference`, `video_edit`, `video_extension` | `t2v` | Catalog: "'t2v' for prompt-only generation, 'omni_reference' for image, video, or audio references, 'video_edit' to edit one reference video (billed by that video's duration; 'duration' and 'aspect_ratio' are ignored), or 'video_extension' to extend a reference video ('aspect_ratio' is ignored — the output follows the extended video)." [HF S11] |
| `seedance_2_5` | `duration` | number, 4–30 s | 5 | Ignored in `video_edit`; new-segment length in `video_extension`; unsupported values snap or clamp [HF S11, S12]. |
| `seedance_2_5` | `resolution` | `480p`, `720p`, `1080p` | `720p` | Project: always `720p` (§2.6). |
| `seedance_2_5` | `generate_audio` | bool | `true` | "Generate audio for the output video." `false` for edits (§2.5). |
| `seedance_2_5` | `bitrate_mode` | `standard`, `high` | `standard` | "'high' = higher bitrate output." Higgsfield-specific. |
| `seedance_2_5` | `extension_mode` | `backward`, `forward` | null | "required for mode 'video_extension' and not allowed otherwise." |
| `seedance_2_5` | `draft` | bool | `false` | "Generate a 480p draft that can be finalized within seven days." |
| `seedance_2_5` | `draft_job_id` | string | null | "Completed draft job to finalize at 1080p." |
| `seedance_2_5` | `aspect_ratio` (call-level) | `auto`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | not stated | Project: `9:16`, or `auto` where the ratio is locked by an input (§2.6). |
| `ad_multiplier` | `mode` | `t2v`, `omni_reference`, `video_edit`, `video_extension` | `t2v` | "Same as seedance_2_5 mode." |
| `ad_multiplier` | `duration` | number, 4–30 s | 5 | Recipe passes `ceil(SOURCE_DURATION)` [HF S13]. |
| `ad_multiplier` | `resolution` | `480p`, `720p`, `1080p` | `720p` | |
| `ad_multiplier` | `generate_audio` | bool | `true` | Recipe always sends `false` [HF S13]. |
| `ad_multiplier` | `bitrate_mode` | `standard`, `high` | `standard` | |
| `ad_multiplier` | `extension_mode` | `backward`, `forward` | nullable | |
| `ad_multiplier` | `aspect_ratio` (call-level) | `auto`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | not stated | Recipe sends `"auto"` [HF S13]. |
| both | `seed`, `negative_prompt`, `camera_fixed`, `watermark`, `output_format` (`mov`), `return_last_frame`, `omni_reference_task_type`, `duration:-1` | — | — | **Not exposed on Higgsfield** [HF S11]. ModelArk offers `watermark`, `output_format`, `return_last_frame`, `omni_reference_task_type` and `-1` for 2.5; `seed`/`camera_fixed` exist only for 1.x; no Seedance API has a negative-prompt field [OFFICIAL S4]. Approximations: exclusions in prose (§3.10), camera lock in words (§3.6), last frame extracted locally (§3.14), explicit edit/extension trigger words (§2.5). |

`ad_multiplier` lacks `draft`/`draft_job_id`; its recipe also sends the undocumented `duration_policy:"strict"` [HF S11, S13]. Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost:true` (preflight, submits nothing), `use_unlim` (only if the user asks) [HF S12].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | exact first frame; locks output ratio | 1 | ModelArk `first_frame` [OFFICIAL S4] |
| `end_image` | exact last frame | 1, with `start_image` | same ratio as the first frame, else stretched/cropped [OFFICIAL S2, S4] |
| `image_references` | `@Image1…N`: identity, wardrobe, product, scene, lighting/style, storyboard, keyframes, text-as-image | ≤30; each <30 MB, 300–6000 px, w/h 0.4–2.5; best with 1–8 image subjects [OFFICIAL S2, S3] | numbered in `medias` order |
| `video_references` | `@Video1…N`: motion, action, camera, rhythm, effects, clay blockout; or the edit/extension source | ≤10, combined ≤30 s, each 2–30 s (edit source 4–30 s, ≤20 s best), ≤200 MB, 24–60 fps [OFFICIAL S2, S3, S4] | exactly one video for edit/extension [HF S11] |
| `audio_references` | `@Audio1…N`: timbre, dialogue, music, ambience, beat | ≤10, combined ≤30 s, each 2–30 s, wav/mp3 ≤15 MB [OFFICIAL S3, S4] | audio-only accepted on ModelArk [OFFICIAL S4]; untested on Higgsfield |
| `video` / `image` | aliases in Higgsfield's Ad Multiplier recipe | — | "Server may auto-coerce roles when unambiguous" [HF S12] |

≤50 references total; 1–5 subjects per audio/video reference, 5–10 s per reference clip, 1–5 images with an edit [OFFICIAL S2]. "The numbering should correspond to the upload order of the assets, such as Image 1 / Video 1 / Audio 1" — one 1-based counter per media type [OFFICIAL S2]. `medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S12].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 4–30 s integers (t2v, reference, first-frame, extension) [OFFICIAL S4; HF S11]. Edit output is locked to the source and "may differ … by up to about 0.3 seconds" (prompt guide) / "about 0.4 seconds shorter" (API); zero drift when the source was generated by 2.5; official fix: re-time the source to **8n+1 frames** or use Reference mode with an explicit duration [OFFICIAL S2, S4].
- **Resolution / fps:** 480p, 720p (8-bit), 1080p (10-bit on ModelArk); 24 fps [OFFICIAL S5]. Higgsfield returned H.264 MP4 in earlier tests [HF S16]. Higgsfield's marketing page shows "4K" examples; the catalog caps this id at 1080p [HF S14, S11].
- **Aspect ratio:** t2v/reference: any listed ratio or `auto` [OFFICIAL S4]; first/last frame: locked to the first image; edit/extension: locked to the source (any ratio in [0.4, 2.5]) [OFFICIAL S2].
- **Audio:** voice, SFX and music in one pass; ModelArk output is mono [OFFICIAL S4]. Edits render silent and restore the source audio locally [HF S13].
- **Draft:** 480p draft, 1080p-only final, 7-day validity; prompt, references, duration, ratio and audio are reused [OFFICIAL S3].

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight without submitting; never reuse remembered rates [HF S12].

**Text-to-video**
```json
{"model":"seedance_2_5","mode":"t2v","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**First frame (+ optional last frame)** — images must be exactly 9:16; `mode` for this path is undocumented, `omni_reference` is the best-supported guess [INFERRED]. Drop `end_image` for first-frame-only.
```json
{"model":"seedance_2_5","mode":"omni_reference","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":8,"aspect_ratio":"auto","resolution":"720p","generate_audio":true}
```
**Omni reference (identity + product + motion clip + voice)**
```json
{"model":"seedance_2_5","mode":"omni_reference","prompt":"<PROMPT citing @Image1 @Image2 @Image3 @Video1 @Audio1>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_3>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID_1>","role":"video_references"},{"value":"<AUDIO_MEDIA_ID_1>","role":"audio_references"}],"duration":15,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**Video edit** — source already reframed to 9:16 (§2.6); `duration` = ceil(measured source seconds).
```json
{"model":"seedance_2_5","mode":"video_edit","prompt":"<EDIT PROMPT, ≤3,900 characters>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"}],"duration":12,"aspect_ratio":"auto","resolution":"720p","generate_audio":false,"bitrate_mode":"high"}
```
**Video edit via Higgsfield's Ad Multiplier contract** (source first, then images in `@Image` order; an approved generated image may be passed by job id) [HF S13]
```json
{"model":"ad_multiplier","mode":"video_edit","prompt":"<VALIDATED EDIT PROMPT>","count":1,"duration":8,"duration_policy":"strict","aspect_ratio":"auto","resolution":"720p","generate_audio":false,"medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image"},{"value":"<JOB_ID>","role":"image"}]}
```
**Video extension** (forward = after the source ends, backward = before it starts [OFFICIAL S7]; enum mapping assumed [INFERRED])
```json
{"model":"seedance_2_5","mode":"video_extension","extension_mode":"forward","prompt":"<PROMPT citing @Video1>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":6,"resolution":"720p","generate_audio":true}
```
**Draft, then finalize** (optional; the final is 1080p and must be downscaled, §2.6)
```json
{"model":"seedance_2_5","mode":"omni_reference","draft":true,"prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"}],"duration":12,"aspect_ratio":"9:16","resolution":"480p","generate_audio":true}
```
```json
{"model":"seedance_2_5","draft_job_id":"<JOB_ID>","resolution":"1080p"}
```
If the finalize call is rejected, resend the identical draft params with `draft:false`, `draft_job_id` and `resolution:"1080p"` [INFERRED; ModelArk reuses the draft's inputs, OFFICIAL S3].

### 2.5 Parameter gotchas

- `mode` defaults to `t2v`; references without `omni_reference` (or an edit/extension mode) risk being ignored or coerced [INFERRED].
- The prompt also routes the task: edits need a trigger ("edit video, add, insert, remove, delete, modify, replace, change to"), extensions an extension trigger ("extend forward, extend backward, continue, continue from, extend the story"); mismatches fail as `TaskTypeMismatch` [OFFICIAL S2, S3]. Name the video directly ("Edit @Video1…"); never write "reference Video 1" in edit/extension prompts [OFFICIAL S6].
- `video_edit` ignores `duration`/`aspect_ratio` and bills by source length; still send `duration: ceil(source)` and `aspect_ratio:"auto"` as Higgsfield does [HF S11, S13].
- ModelArk forbids mixing first/last-frame roles with omni references; in omni mode write "Use @ImageN as the first frame." instead (ratio not locked, not pixel-exact) [OFFICIAL S2, S4, S7]. Mixing on Higgsfield is untested.
- **Parameter separation:** never write aspect ratio, total duration, resolution, frame rate or the sound toggle into the prompt [OFFICIAL S7] (Dreamina's consumer formula does [OFFICIAL S9] — not on Higgsfield).
- **Tags:** official docs accept `@Image 1`, `@Image1`, `Image 1`, `[Image 1]` [OFFICIAL S2, S3]; Higgsfield's contract mandates exact-case `@Video1` / `@ImageN` [HF S13] and normalises tags server-side (`<<<image_1>>>` observed) [HF S16]. Use `@Image1`, `@Video1`, `@Audio1`.
- **Length:** ≤3,900 characters (Higgsfield edit contract) [HF S13]; ModelArk recommends ≤1,000 English words [OFFICIAL S4]. Keep all 2.5 prompts ≤3,900 characters [INFERRED].
- ModelArk refuses real-face references [OFFICIAL S3, S8]; Higgsfield's Ad Multiplier recipe edits footage with people [HF S13] — moderation elsewhere unverified.
- Non-standard JPG chroma subsampling fails; re-encode (`ffmpeg -i in.jpg -pix_fmt yuvj420p out.jpg`) or use PNG [OFFICIAL S2].
- Higgsfield Elements (`<<<element_id>>>`) are not documented for this id [HF S12]; attach approved assets as `image_references`.

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id / operation | params to send | expected output | post-processing |
|---|---|---|---|
| `seedance_2_5` t2v / omni reference | `aspect_ratio:"9:16"`, `resolution:"720p"` | 720×1280 (official 2.5 grid) [OFFICIAL S4]; Higgsfield stored `width:720,height:1280` for this setting [HF S16] | none; verify with ffprobe |
| `seedance_2_5` first / last frame | `aspect_ratio:"auto"`, `resolution:"720p"`, exactly-9:16 start (and end) image, e.g. 720×1280 or 1080×1920 | ratio locked to the image → 720×1280 [OFFICIAL S2, S4; dims INFERRED] | if the image is not exactly 9:16, conform it **before** upload (`atp.py conform`: scale-to-fill + minimal crop) |
| `seedance_2_5` / `ad_multiplier` video_edit | `aspect_ratio:"auto"`, `resolution:"720p"`, source reframed to 9:16 (720×1280) **before** upload | follows the source → 720×1280; Higgsfield's QC expects the short edge within 8 px of 720 [HF S13] | reframe non-9:16 sources with `atp.py conform` first; after the edit, conform duration and restore audio |
| `seedance_2_5` video_extension | `resolution:"720p"`, 9:16 source | follows the source → 720×1280 | same reframing rule as edit |
| draft → finalize | final is `1080p` only [OFFICIAL S3] | 1080×1920 | deterministic downscale to 720×1280 (`atp.py conform`); not the default path |

Never stretch. A non-9:16 source can alternatively be re-created in Reference mode at `9:16` with a shot-by-shot timeline (the official aspect-change workaround) — an Analyze-style re-creation, not an edit [OFFICIAL S2].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Official formula:** "subject + action/event + scene and environment + visual style + camera movement/shot cuts + sound" [OFFICIAL S3].
- **Official layout:** (1) asset referencing by upload order and purpose; (2) one-sentence summary "Subject + Location + Event + Genre/Style + Camera movement"; (3) detailed plot with "timestamps or 'Shot N'"; (4) additional notes for invariants. "Treat Seedance 2.5 as a visual content producer, and write structured prompts with a visual storytelling mindset." [OFFICIAL S2]
- **sd25-pe rules:** one primary task per prompt; reorganise into the task template; one role per used asset; parameters out of the prompt; no analysis text; one best version [OFFICIAL S7].
- **Length:** ≤1,000 English words ("Lengthy text will lead to scattered information") [OFFICIAL S4]; ≤3,900 characters on Higgsfield; official examples run ~50–600 words (§4.0). Non-negotiable facts first, then motion/timing, then audio and constraints [OFFICIAL S9]; precise references earliest [OFFICIAL S6].
- **Language:** English plus Chinese, Spanish, Indonesian, Portuguese, Japanese, Malay, Thai, Arabic, Vietnamese, Korean [OFFICIAL S4]; one prompt language.
- **Labels:** official FAQ prompts use ASCII labels (`[Video constraints]`, `[Exclusions]`) [OFFICIAL S2]; prefer them over sd25-pe's `【Label】` headers because `【】` also marks on-screen text [OFFICIAL S3] (precaution [INFERRED]).

### 3.2 Subject and identity

- Define each subject once with 2–3 stable visible features and a unique label; reuse the label exactly [OFFICIAL S6]. One line per subject; never range-map two subjects [OFFICIAL S7]. Several views of one subject = one entity with its count [OFFICIAL S7].
- Don't put the mapping only inside an image (a name written on it) [OFFICIAL S2]. Upload subject references **in order of first appearance** [OFFICIAL S2].
- Keep neutral terms ("a person"); identity, age, relationships come from the brief, only visible attributes from references [OFFICIAL S7].

### 3.3 Action, motion and physical interaction

- "Give priority to general descriptions … Only write specific details for a few memorable actions, and avoid repeating the same actions"; expressions as descriptive sentences [OFFICIAL S2]; emotions as visible body cues [OFFICIAL S6].
- Products: "initial state → specific operation → observable result", one operation per stage [OFFICIAL S7]. Handoffs: after handing over, "the original holder no longer has it" [OFFICIAL S7]. Causal reveals: trigger before reaction [OFFICIAL S7].
- Slow continuous movement is safer than bursts [OFFICIAL S6]; complex-motion physics is a stated weakness [OFFICIAL S1]. Integration details: §3.14.

### 3.4 Environment, lighting and style

- Anchor positions to stable objects (inside/outside the counter), not only screen sides [OFFICIAL S7]; name the key light's source and direction.
- "Refer to Image 1 for lighting and filters" [OFFICIAL S2]; blocking diagrams: use positions, ignore arrows and annotations [OFFICIAL S7].
- 2.5 and 2.0 have "significantly different aesthetic style preferences" [OFFICIAL S2]; realistic references pull stylised prompts toward live action — state the style [OFFICIAL S6]. Describe looks rather than naming real films or artists (IP rejections reported) [SECONDARY S18].

### 3.5 Chronology, timing and multi-shot structure

- **Integer-second timestamps** (new in 2.5): 1-second units, contiguous ranges ("avoid gaps such as '0-3s... 5-6s...'"), time points ("at the 5-second mark"), relative time ("after 3 seconds") [OFFICIAL S2].
- Too little per range → improvisation; too much → "excessive cuts or omit parts of the plot"; never timestamp high-frequency actions [OFFICIAL S2]. `Shot N | 4-5s` combines shots and time [OFFICIAL S2].
- Only an API duration known → stages without numbers, each with one change and an end state [OFFICIAL S7]; measured beats from an analysed reference may be timestamps [INFERRED].
- Transitions: give trigger point and method ("At the 5-second mark, the camera quickly transitions leftward using a left wipe combined with a natural dissolve") [OFFICIAL S2]; "Hard cut." after shots [OFFICIAL S3].

### 3.6 Camera language and dedicated camera / motion controls

- Standard terms work directly: shot sizes, push in / pull out / pan / track / follow / orbit / dive / tilt up / handheld shake, low angle / overhead / first-person, one-shot, dolly zoom, aerial, FPV, bullet time, speed ramp [OFFICIAL S2]. Niche terms as "[term + descriptive explanation]" [OFFICIAL S2].
- "camera movement + target subject + starting position + direction + arrival" when several subjects share the frame [OFFICIAL S7]; one dominant behaviour per shot [OFFICIAL S6, S9].
- No camera parameter; lock in words ("Locked-off camera, fixed camera position, eye-level medium shot; the camera never moves.") [INFERRED from S2 wording]. Exact moves: supply a motion or clay clip as `@Video1` [OFFICIAL S2].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- State the purpose and, if partial, **which part**: "Refer to the action of casting the spell in Video 1 and the wrap-around camera movement in Video 2"; add what not to take ("do not use the image background") [OFFICIAL S2, S7].
- Exact reference → don't re-describe: "Strictly refer to the actions and camera movements in Video 1, and keep the sequence consistent with the video" [OFFICIAL S2].
- A reference video passes no identity, clothing or scene unless declared [OFFICIAL S7]; audio supplies timbre/accent/rate/emotion, written dialogue wins [OFFICIAL S7]. Mapping priority: user > prompt > asset content > filename > upload order [OFFICIAL S7].
- Storyboards ≤15 panels, line-art, no text on panels, not frame-exact [OFFICIAL S2]; clay videos: coarse primitives, say which elements to take, map each primitive [OFFICIAL S2]. Oversized references can print "fingerprint- or shoeprint-like patterns" — resize to ≤ output resolution [OFFICIAL S2].
- Text inside references propagates (§3.11).

### 3.8 Start and end frames

- `start_image`/`end_image` lock the ratio and match most strictly [OFFICIAL S2, S4]. In omni mode write "Use @Image1 as the first frame." / "Use @Image2 as the last frame." as standalone sentences, then a separate sentence describing composition, positions, poses, prop states and camera [OFFICIAL S7].
- Other references must not change the frame composition ("…without changing the first-frame composition defined by @Image1") [OFFICIAL S7]. Keyframes: "Use Images 1 to 7 in order as keyframes." then one line per key state — semantic anchors, not holds [OFFICIAL S2, S7].

### 3.9 Audio, dialogue and sound (if supported)

- Brackets: `()` music, `<>` sound effects, `{}` dialogue, `【】` subtitles; language before non-Chinese dialogue [OFFICIAL S3]. Don't put names in `<>` [OFFICIAL S7].
- Dialogue: "language + optional regional variety or accent + delivery + speaker + {dialogue}", per speaker; "Use English." if needed; no invented lines [OFFICIAL S7]. Listeners keep mouths closed; no-dialogue clips: "characters keep their mouths naturally closed, there is no narration, only the specified ambience remains" [OFFICIAL S7].
- "No BGM; generate only environmental sounds and action sounds." / "No audio." [OFFICIAL S2]; if music leaks, enumerate banned terms and repeat the policy at start and end, or strip in post [OFFICIAL S2]. Remove water/wave/echo wording to avoid bubbling artifacts [OFFICIAL S2]. Hard mute: `generate_audio:false` [HF S11].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield or in the API [HF S11; OFFICIAL S4]. "Use positive descriptions whenever possible. Negative constraints are supported for subtitles and audio control" [OFFICIAL S2]; official FAQ prompts still end with short `[Exclusions]` lines (twins, hand defects, lip-sync errors, flicker, subtitles, logos) [OFFICIAL S2].
- Keep exclusions short and grouped at the end [OFFICIAL S9], each paired with the positive state it protects. Glowing-eye over-reaction: "normal human eyes; no glowing eyes" [OFFICIAL S2].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

**(a) Reliability.** 2.5 renders text but "Letters in English words may be substituted, added, or omitted" [OFFICIAL S2]; "detailed typography is unstable during motion" [OFFICIAL S9]. Subtitles can appear even when forbidden ("cannot currently be eliminated completely"), less often than on 2.0 [OFFICIAL S2]. Verdict: in-frame text is reliable only for short scene text whose exact wording is supplied as an image reference, on a steady surface, verified by frame QA; everything else goes to post [INFERRED from S2].

**(b) Clean plate (default for Analyze Mode).** Official phrasings: "No subtitles." / "Do not add subtitles." [OFFICIAL S2]; "No subtitles, text, or signs appear on screen." [OFFICIAL S2]; "No subtitles, watermarks, logos, garbled text, irrelevant text" [OFFICIAL S2]; sd25-pe's no-dialogue pattern ("no subtitles or signs appear on screen") [OFFICIAL S7]. Also: don't repeat dialogue words or attach tone notes to specific words — write "Character's line (emotion): content" [OFFICIAL S2]; strip text from reference videos/images ("Subtitles in a reference video may override the no-subtitle instruction") [OFFICIAL S2]; describe signs, packaging and screens as blank [INFERRED]; never use `【】` in a clean plate [OFFICIAL S3]. Portrait frames produced spurious subtitles more often on 2.0 — QA every 9:16 output [OFFICIAL S6].

**(c) Intentional in-frame text (scene text only: a sign, screen UI, packaging).** Official notation puts the words in `【】` with style, position and timing and binds an image of the exact text: "Bold black text appears at the bottom center: 【…】, referring to <Image 2>" [OFFICIAL S2]; for spelling-critical words "Split the word into individual letters and require them to appear one by one in sequence" or "Prepare the text that must be rendered accurately as an image and provide it as a reference asset" [OFFICIAL S2]. Keep it short and front-facing in a locked shot [OFFICIAL S9]. Hooks, captions and subtitles are added in post instead.

**(d) Removing source text in edits.** Removal of "subtitles, watermarks, and more" is an official edit capability [OFFICIAL S2]; the official FAQ edit reads "Editing instruction: Remove the red lines, red numbers, and red arrows from the video." [OFFICIAL S2]. Use Higgsfield's remove sentence "Remove only [target] from @Video1 and reconstruct the revealed area consistently with its immediate surroundings" [HF S13], naming every element with position and time: captions, subtitles, usernames/handles, watermarks, title cards, meme text, stickers, social overlays, UI elements, timestamps, overlay logos, random lettering. **Do not include** Higgsfield's "Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1…" block — this project's policy overrides it [HF S13 differs]. Tendency: untargeted content "remain[s] unchanged by default" [OFFICIAL S6], so any text you don't name survives; text on a replaced object "follows that replacement" in Higgsfield's contract [HF S13] — state that the replacement carries only its approved label. Prefer a removal-only pass before content edits when text is large; trim full-screen title cards locally; when text covers faces, hands or the product, or dominates the frame, re-create in Analyze Mode instead [INFERRED; split-pass advice OFFICIAL S2].

### 3.12 Character / identity consistency

- Per character: headshot (face only, neutral) + full-body image; "facial features reference @Image1 (headshot), styling reference @Image2 (full body)" [OFFICIAL S6]. Multi-view images OK for ≤5 subjects; above 5, separate single views [OFFICIAL S2].
- One image per named character; "Do not swap the two characters' appearances, clothing, actions, positions, or dialogue." [OFFICIAL S7]. Twins: "Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited. Do not generate duplicate avatars or a twin effect." [OFFICIAL S6]. >4 people: group stills of ≤4 first [OFFICIAL S6].
- Approved references replace source people: in generation, the approved image is the only identity source and source clips get motion/camera roles only; in edits use the person-replacement exclusion (§4.4.2) [HF S13]. Aging edits: "facial features should gradually age without drifting or changing identity" [OFFICIAL S2].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- 2–4 single-view images (front, side/¾, top, label close-up) declared as **one** entity: "@Image1 (front), @Image2 (side) and @Image3 (label close-up) jointly define one single <object>; do not generate multiple copies." [OFFICIAL S7 pattern]
- Scope each image ("use only structure, material and color"; "do not use the image background or hands") [OFFICIAL S7]; state rigidity, unchanged silhouette and part count, and name drift-prone parts (cap shape, button count, handle side, screen ratio) [INFERRED]. Dreamina tail: "preserve its logo, bezel, button placement, proportions … No warped logo, extra buttons" [OFFICIAL S9].
- Hero frames: locked camera, product front-facing for the final 2–4 s; slow orbits only [OFFICIAL S9].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale and orientation:** relate size to body and set ("fits in one palm", "same height as the original can"); give orientation relative to camera and set ("label faces the camera", "spout points toward the sink") [INFERRED]. Take the numbers from the plan's size reckoning (`reference/anomaly-catalog.md` §2.7) and write them as relations Seedance keeps: the ratio to a named neighbour at the same depth ("two thirds the height of the water bottle beside it"), the depth in the blocking ("on the dresser behind him, about two and a half metres from the camera"), the fraction of the frame as a plain description ("a small object in the background") and a constancy clause ("it keeps that size as the camera moves"); pad the product reference so it does not fill its image [INFERRED]. In edits, inherit the source slot: "same grip, motion path and real-world size"; for moving subjects "exactly the same appearance timing, movement path, speed, and occlusion positions" [OFFICIAL S7].
- **Contact, grip, occlusion:** name the hand, finger placement, contact point and what passes in front ("the right thumb covers the lower label edge; the cup passes in front of the bottle at 3s"); keep method-critical contact visible [INFERRED S17].
- **Scene-light inheritance:** for inserted assets state the key direction and colour temperature they take ("lit by the warm window light from frame left; soft shadow falls right on the table; the glossy cap reflects the window") and forbid product-photo lighting ("do not use the lighting of @Image2") [INFERRED]; "Refer to Image 1 for lighting" governs overall look [OFFICIAL S2]; the official edit example lists physical consequences explicitly ("a small amount of dust at contact points, cool metallic reflections") [OFFICIAL S2].
- **Persistent states:** carry each stage's end state into the next ("At the end: the lid rests right of the jar" → "Continuing from the previous stage: the lid still rests right of the jar") [OFFICIAL S7 template]; ownership after handoffs [OFFICIAL S7]; liquids: source → stream → level rises → settles; placed objects stay put; the same hand holds until it releases [INFERRED S17].
- **Known failures:** complex motion physics and multi-subject interaction [OFFICIAL S1]; states reset or objects duplicate after cuts/occlusions when not restated [INFERRED S17].
- **Across clips:** fill one 30 s generation first ("coherent videos up to 30 seconds long… without multi-segment stitching" [OFFICIAL S3]); stitch at cuts for scene turns, extend for one continuous take [OFFICIAL S1, S6]. **Extension (`mode:"video_extension"`, `extension_mode:"forward"`):** the input video must be 2–30 s [OFFICIAL S4], so extend the newest accepted clip (pass its **job id**: it keeps its audio and skips a re-upload), never a stitched master; `duration` = the new part; ByteDance's own example returned **only the new part** (a 15.05 s source + "Extend @Video 1 by 5 seconds" → a 5.000 s file; the stitched version is shown separately) and its first frame repeats the source's last frame (drop it: `atp.py concat --seams continuous`) [OFFICIAL S2, measured 2026-10-01]; "the volume of the generated video may differ slightly from the input video" [OFFICIAL S2]; ≤ 2 extension hops per take. Frame chain instead: `atp.py last-frame` → next first frame with "continue forward from this moment; do not replay what happened before it" [OFFICIAL S4; SECONDARY S19]. Upstream, first/last-frame roles cannot mix with omni references, so with references write "Use @ImageN as the first frame." [OFFICIAL S4]. Identical references in identical order; at a jumpy join trim 6 frames from the end of the earlier clip and 1 from the start of the later [OFFICIAL S6]. No seed on Higgsfield [HF S11].
- **Use, counts and permanence** (`reference/anomaly-catalog.md`): write each use in the official product form "initial state → specific operation → observable result" [OFFICIAL S7] with the named part and the contact point ("She flips the spout cap open with her thumb, puts her lips on the spout and drinks through it with her head level; the milk level sinks a little"); carry counts with numbers in every stage's end state and the next stage's opening ("At the end, three capsules still lie on the desk right of the lamp" → "Continuing from the previous stage: the same three capsules lie on the desk"), including after an exit or occlusion ("when he steps back into frame, the same three capsules are on the desk"); write the t=0 state of every part in [Start state] ("sealed, tab flat") and never attach an image that shows a later state (an open-tab photo put a raised tab into frame 0, 2026-10); put one item per product in [Exclusions] for its own wrong use and count ("drunk only through the spout; no other opening", "exactly three capsules; none appears or disappears") [INFERRED; observed 2026-10].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

**E1 — text-to-video** (BytePlus 2.5 prompt guide, S2): "Realistic nature documentary style, natural lighting and shadows. On a warm afternoon, on a grassy slope in the forest, a chubby panda cub rolls down the hill. […] The camera is a low-angle medium-wide shot with a slight handheld feel. […] 0s-3s: A panda cub lies on a green grassy slope, its body round and chubby. It begins to slowly roll sideways down the slope with clumsy movements, gently bending the grass beneath its body. […] Natural environmental audio only, including wind, rustling grass, and the soft plop of the panda rolling."

**E2 — basic generation** (sd25-pe, S7): "A young ceramicist shapes clay on a pottery wheel in a studio at dawn, holding the spinning clay steady with both hands until it forms a narrow-necked vase. Soft morning light enters through the window on the left, keeping the wooden table and clay in natural warm tones. The camera begins in a medium shot observing the hand movements, then slowly pushes in toward the mouth of the vase. The sound preserves the low hum of the wheel, palms rubbing against wet clay, and distant birdsong outside the window."

**E3 — storyboard + bindings** (S2): "Asset Bindings: Storyboard @Image1, bedroom @Image2, Li Tian @Image3, Li Qian @Image4, book *Happy Times* @Image5. Shot 1: [Wide shot, locked-off camera, eye-level, rule-of-thirds composition] Room on a snowy winter night. In front of floor-to-ceiling windows, a man stands sideways with both hands in his pockets, gazing out at falling snow. […] Shot 3: [Medium close-up, diagonal composition] The man holds the book *Happy Times* and extends it slowly. The young girl raises her hands to receive the book."

**E4 — keyframes** (S2): "Use Images 1 to 7 in order as keyframes. In a sea of clouds and mountains, blue-and-pink long-tailed spirit fish soar through the air. The camera slowly moves toward an ancient town built into the mountainside, focusing on the ancient pagoda at the top of the mountain. […]"

**E5 — edits** (S2): "Change the man's action from drinking coffee to mopping the floor from 4-6 seconds in Video 1, and leave the rest of the content unchanged." · "This is a video editing task. Edit the video and modify only the content explicitly requested by the instructions; keep all other subjects, composition, timing, and style unchanged. Editing instruction: Remove the red lines, red numbers, and red arrows from the video."

**E6 — moving-subject replacement** (sd25-pe, S7): "Edit @Video1, replacing only the red bicycle and its rider passing in front of the bench with the dark-gray electric patrol vehicle from @Image1. […] The electric patrol vehicle fills the original rider's motion slot with exactly the same appearance timing, movement path, speed, and occlusion positions. The red bicycle and rider must no longer appear in the final video."

**E7 — extension** (S2): "Extend @Video 1 by 5 seconds. A bee flies in and lands on the flower. Then, in a macro close-up, its legs and abdomen are covered with golden pollen particles. The bee flaps its wings and takes off, and the camera follows it as it flies toward another flower of the same species. […]"

**E8 — audio and text policy** (S2 FAQ): "Audio policy (applies to all shots): The soundtrack contains only the specified spoken dialogue plus faint natural night ambience at a low, constant level. Absolute silence otherwise. No music, BGM, score, instrumental, melody, soundtrack, synth, ambient pad, drone, swelling tone, crescendo, musical build, or stinger at any moment […]" · "No narration. No subtitles, text, or signs appear on screen."

Patterns these teach [derived from E1–E8]:
- **Order:** style/genre → setting and time → subject and action → camera → timeline → look → audio; bindings first when assets exist (E3, E6).
- **Sentence style:** present tense, concrete observable detail (textures, light source and direction), one event per sentence; routine motion general, key actions specific (E1, E2).
- **Time:** `0s-3s:` ranges, `Shot N:` with bracketed camera notes, edit scopes "from 4-6 seconds" (E1, E3, E5).
- **Subject vs camera motion:** separate sentences; the camera sentence follows the subject action it serves (E2).
- **Camera vocabulary:** standard shot sizes and moves; composition terms in brackets (E3).
- **References:** asset + number declared once, then used as names; ordered keyframe declaration as the first sentence (E3, E4).
- **Length:** 50–120 words for simple shots; longer only with a timeline.
- **Exclusions:** few and specific; edit scope closure ("leave the rest of the content unchanged"); explicit subtitle/sign and music bans (E5, E8).
- **Audio:** "Natural environmental audio only, including…" with concrete sources tied to actions (E1, E2).
- **Edits:** A → B with a time scope; replacements inherit timing, path, speed and occlusion; the original "must no longer appear" (E5, E6).
- E7 states the extension length in prose; on Higgsfield `duration` carries it, so templates omit it [OFFICIAL S7 parameter rule].

### 4.1 Text-to-video

```text
[Summary] <style>. <Setting and time>: <subject with 2–3 stable features> <main action>.
[Start state] <positions, facing, what each hand holds, object states; camera shot size and angle; key light source, direction, colour temperature; ambient bed>.
[Timeline]
0-<t1>s: <one main action, body part and speed>; <SFX>. At the end, <state>.
<t1>-<t2>s: Continuing from <state>, <one change>; the camera <one behaviour>. At the end, <state>.
<t2>-<end>s: <concluding action>; the frame holds on <final composition>.
[Look] <light quality, palette, texture, realism>; real-time speed.
[Audio] <"No dialogue; mouths stay naturally closed" or "Name's line (language, delivery): {words}">; natural environmental audio only, including <sources>. No BGM.
[Consistency] <counts, positions, ownership, clothing that must not change>.
[Exclusions] No subtitles, text, or signs appear on screen; no logos or watermarks; no duplicated <subjects>; no slow motion; no extra fingers.
```
Worked example (10 s):
```text
[Summary] Realistic home footage. A wooden desk by a window in the morning: a person in a grey knit sweater unboxes a small matte-white handheld speaker.
[Start state] The closed plain cardboard box sits centred on the desk; both hands rest beside it; soft neutral daylight from the window on the left; medium shot, eye level; quiet room tone.
[Timeline]
0-3s: The person lifts the lid with both hands and sets it right of the box; <cardboard sliding>. At the end, the lid rests right of the box.
3-7s: Continuing from that state, the right hand lifts the speaker out and turns it once so the round grille faces the camera; the camera stays locked. At the end, the speaker rests in the right palm.
7-10s: The speaker is set upright in front of the box and both hands move away; <soft tap>; the frame holds.
[Look] Natural daylight, neutral colours, gentle shadows falling to the right; real-time speed.
[Audio] No dialogue; mouths stay naturally closed. Natural environmental audio only, including cardboard, the tap and faint room tone. No BGM.
[Consistency] Exactly one box, one lid, one speaker; the lid stays where it was placed; the speaker keeps its rounded-cube shape and single grille.
[Exclusions] No subtitles, text, or signs appear on screen; the box and speaker are plain and unmarked; no logos, no watermarks, no extra hands, no slow motion.
```

### 4.2 Start frame (and end frame) to video

```text
Use @Image1 as the first frame.
This first frame defines <composition, positions, poses, prop states, scene, camera direction>.
[Use @Image2 as the last frame.
This last frame defines <ending composition, positions, poses, prop states>.]
The shot begins naturally from the first frame<, and after a continuous action arrives at the last frame>: <action with ownership and state changes>.
Camera: <locked-off | one move with start and end framing>. Real-time speed.
Audio: <…>. No subtitles, text, or signs appear on screen.
Maintain continuity from first to last in <identities, object count and structure, layout, light direction, camera axis>.
```
With `start_image`/`end_image` roles the frame sentences may instead read "The video starts on the provided first frame…" [INFERRED]; keep them when the images are passed as references [OFFICIAL S7].
Worked example (8 s):
```text
Use @Image1 as the first frame.
This first frame defines a medium shot of a person seated at a café table, a closed laptop in front of them, a ceramic cup on the right, window light from the left.
Use @Image2 as the last frame.
This last frame defines the same framing with the laptop open, the screen showing soft abstract colour, and the cup moved to the left of the laptop.
The shot begins naturally from the first frame: the person opens the laptop with both hands, then moves the cup with the right hand to the left side and settles back, arriving at the last frame.
Camera: locked-off, eye level, the camera never moves. Real-time speed.
Audio: café room tone, <laptop hinge>, <cup set down>. No dialogue. No subtitles, text, or signs appear on screen.
Maintain continuity in the person's face and clothing, one laptop, one cup, and the window light from the left.
```

### 4.3 Reference-to-video

```text
[Reference roles]
@Image1 defines <Character A>'s face (headshot); use only facial features.
@Image2 defines <Character A>'s hair, clothing and build; do not use its background.
@Image3 (front) and @Image4 (side) jointly define one single <product>: use only shape, proportions, materials and colours; do not use backgrounds, hands or studio lighting.
@Video1 is used only for <motion path | camera movement | rhythm>; do not use its people, clothing, location, text or audio.
@Audio1 is used only for <Character A>'s voice timbre.
[Summary] <style>. <Setting>: <Character A> <main event with the product>.
[Start state] … [Timeline] … (end state per interval)
[Integration] <product> is <size vs hand>, held in <hand> with <grip>; lit by <scene key light, direction, colour temperature>; its shadow falls <direction>.
[Audio] <Character A>'s line (<language>, <delivery>): {<exact words>}. Listeners keep mouths closed. <ambience/SFX>. <music policy>.
[Consistency] One <Character A>, one <product>; <ownership, positions>. Do not swap identities.
[Exclusions] No subtitles, text, or signs appear on screen; the only lettering is the printed label, logo or badge on <product>, exactly as in @Image3; no other logos or watermarks; no duplicate people; no slow motion.
```
A client product keeps its real label (`text-and-format.md` §1); a bare "no logos" would blank it.
Worked example (12 s):
```text
[Reference roles]
@Image1 defines the courier's face; use only facial features.
@Image2 defines the courier's short curly hair, olive jacket and build; do not use its background.
@Image3 (front) and @Image4 (side) jointly define one single compact grey drone with four folded arms; use only shape, proportions and materials; do not use the studio lighting.
@Video1 is used only for the slow lateral tracking move; do not use its people, location or audio.
[Summary] Cinematic realism. A rooftop at dusk: the courier unfolds the drone and sends it into the air.
[Start state] The folded drone lies on a flat concrete ledge; the courier stands behind it facing camera; warm low sun from frame right; light wind.
[Timeline]
0-4s: The courier unfolds the four arms one by one with both hands; each arm clicks into place. At the end, all four arms are extended.
4-8s: The courier steps back two paces; the drone lifts straight up to head height, level and stable.
8-12s: The drone climbs out of frame top; the frame holds on the courier and the empty ledge.
[Integration] The drone is the size of a dinner plate; warm sunlight from frame right lights its right side; its shadow falls left on the ledge until take-off.
[Audio] No dialogue. <arm clicks> <rotor hum rising> <wind>. No BGM.
[Consistency] Exactly one drone with four arms throughout; it is rigid and keeps its proportions.
[Exclusions] No subtitles, text, or signs appear on screen; no logos; no second drone; no slow motion.
```
Re-creating an analysed reference with a new cast. **Recreate mode only.** Use it when a true edit
(§4.4, `mode:"video_edit"` on the reference's prepared own-content source) is not the chosen
approach. **Create mode never passes a reference video.** Add the routing sentence only when ratio
or duration differs from the reference [OFFICIAL S2, S7]:
```text
Generate a video using @Video1 as the reference for shot order, timing, camera movement and actions; do not use its people, clothing, text, captions, watermarks or audio. Please note that this is not video editing.
[Visual timeline] 00:00-00:02: <shot 1 as seen> … (one line per source shot)
Replace every person with <Character A> from @Image1. <ONE of the three product lines below> No subtitles, text, or signs appear on screen; the only lettering is the printed label, logo or badge on <product>, exactly as in @Image2.
```
Product line, chosen by the reference card's client-entity fit (`generation-system.md` §4, §4b):
- **Swap** (the reference has an analogous item): "The <analogous item as seen> becomes <product> from @Image2, with the same <grip or position>, motion path and real-world size, lit by the scene's light."
- **Contents** (the product's category in another form or vessel): "The <vessel or hand as seen> holds <product>'s <drink / gum pieces / cream>, with the <colour, clarity and bubbles / shape and texture> of @Image3, in the same amount and through the same actions. The opened <product package> from @Image2 stands beside it on the <surface>, its label turned slightly toward the camera, and stays there in every shot."
- **Placement** (nothing analogous; never "replace every product", which would turn an unrelated object into the product): "<Product> from @Image2 is part of this scene from the first frame although @Video1 has none: <anchor, e.g. "it stands on the desk to the right of the laptop, label turned slightly toward the camera", "it is parked at the curb behind the bench, wheels straight, badge turned slightly toward the camera">, and it stays there in every shot<, except: at <t>s the left hand lifts it, <uses it once, e.g. takes one sip> and sets it back on the same spot>. It is lit by the scene's <key light> like everything around it; only one appears." For an in-hand anchor: "<Character A> holds <product> from @Image2 in the <left> hand throughout, while the <right> hand performs the gestures of @Video1."

### 4.4 Video edit / extension / motion transfer (only if supported)

**Edit rules** [OFFICIAL S2, S7; HF S13]: `@Video1` is the sole master; start with a trigger ("Video edit.", "Replace only…", "Remove only…"); describe A → B; list every visible subject category as replace/remove/keep; include one scope-closure sentence; replacements come from `@ImageN`, never `@Video1`; ≤3,900 characters; source ≤20 s and 1–5 images for stability; one or two operations per call — split complex edits into passes [OFFICIAL S2]. Render silent (`generate_audio:false`), then conform to the exact source duration and restore the source audio locally; fail outputs shorter than max(1/fps, 0.10) s rather than freezing frames [HF S13]. Source text is removed per §3.11(d); the Higgsfield preservation block is never used.

#### 4.4.1 COMPACT (no person identity replacement)
```text
TASK - VIDEO EDIT:
<start>-<end>s: Replace only <target, with a unique anchor> in @Video1 with <replacement> from @Image1, keeping the same grip, motion path, real-world size and scene lighting; remove only <each text element, with position> from @Video1 and reconstruct the revealed area consistently with its immediate surroundings. Keep every unrequested element, camera motion, lighting treatment, and overall color grading from @Video1 exactly the same.
No new text, subtitles, logos or watermarks appear anywhere<; the printed label from @Image2 stays exactly as in the reference>.
Except for the objects explicitly modified above, all other visible characters, props, and background elements in @Video1 remain unchanged and are not to be replaced or removed.
```
Segments tile the full measured duration; a whole-clip edit has one change line; other verbs: "Modify only <target> in @Video1 so that <change>", "Add only <element> at <placement> in @Video1" [HF S13]. The last sentence is sd25-pe's scope closure [OFFICIAL S7].
Worked example (12.0 s source, 9:16):
```text
TASK - VIDEO EDIT:
0-12s: Replace only the clear plastic bottle held in the woman's right hand in @Video1 with the matte white insulated bottle from @Image1, keeping the same grip, motion path, real-world size and the warm window light from frame left; remove only the burned-in captions along the bottom, the username in the lower-left corner, the sticker at the top right and the watermark from @Video1 and reconstruct the revealed areas consistently with their immediate surroundings. Keep every unrequested element, camera motion, lighting treatment, and overall color grading from @Video1 exactly the same.
No new text, subtitles, logos or watermarks appear anywhere. The bottle is one rigid object with an unchanged silhouette and cap shape; its reflection in the window glass matches it.
Except for the objects explicitly modified above, all other visible characters, props, and background elements in @Video1 remain unchanged and are not to be replaced or removed.
```

#### 4.4.2 DETAILED (person identity replacement, multi-shot targets, or ≥3 change categories)
```text
@Image1 — <ALIAS>, the complete replacement look for <target person as seen>: <face, hair, skin tone, build, outfit, footwear, accessories>. Transfer this entire look from @Image1, including the full outfit and all worn accessories.
@Image2 — <PRODUCT ALIAS>, the replacement for <product target>: <shape, proportions, colours, materials, part count>. @Image3 — a close-up of the same product's label; it is not a second product.
Video edit. Keep this @Video1 clip exactly as it is — the same shots and cuts, camera moves, framing, composition, unmapped performers, setting, untargeted held and environmental props, lighting, pacing, and timing. Change only <complete scope>, keeping source blocking, poses, motion, position, screen placement, and timing while rendering each replacement person's complete image-defined look.
1. REPLACE — The original source person identified as <target> in @Video1 must never appear in any frame of the output. Replace that person completely with <ALIAS> from @Image1 in every appearance, transferring the complete reference-defined look and retaining only the original performance, pose, blocking, interactions, and timing. This holds through cuts, entrances, exits, occlusions, motion blur, transitions, reflections, and shadows.
2. REPLACE — <product target> in @Video1 becomes <PRODUCT ALIAS> from @Image2 for its whole visible range, same grip, path, size and scene lighting.
3. REMOVE — <every source text element, with positions and times>; reconstruct each revealed area consistently with its immediate surroundings; add no text.
IDENTITY lock: <ALIAS> comes only from @Image1; identities never cross, merge, exchange or duplicate; the product keeps the geometry of @Image2; no other person, object, untargeted wardrobe, environment, action, cut, camera move, lighting treatment, or timing changes.
Render <ALIAS>'s complete look from @Image1 and the product from @Image2 while inheriting only the source performance and timing.
Everything else — <untouched people>, <untouched objects>, the environment, lighting, the camera moves and all timing — stays exactly the same.
```
Operation 1 is Higgsfield's exclusion sentence verbatim (plus its extension list); the block order is Higgsfield's DETAILED template with the preservation block replaced by operation 3 [HF S13]. The replaced person's source clothing does not survive unless a separate garment image or instruction says so [HF S13]. Avoid replacing a speaking face unless re-synthesised lips are acceptable [INFERRED].

#### 4.4.3 Audio-only edit and dubbing [OFFICIAL S2, S7]
```text
Edit @Video1, changing only <speaker or sound category> in <whole video | 4-6s>: <change>. @Video1 is the sole editing master for visuals, actions, lip-sync timing, shots and all other audio. Keep <other dialogue, ambience, SFX> unchanged. Do not add subtitles.
```
Dubbing: give the full target-language dialogue with a per-speaker timeline, demand word-level lip sync and state acceptance criteria (no source-language speech left, no subtitles) [OFFICIAL S2]. Audio edits need `generate_audio:true`.

#### 4.4.4 Extension [OFFICIAL S7]
```text
Extend @Video1 forward. The first frame of the extended segment directly continues from the final frame of @Video1: maintain continuity in <pose and orientation>, <prop positions>, <background>, <camera position and composition>, <lighting>, <audio state>, <motion trajectory>.
Then, <new action>; at the end, <observable state>.
Throughout the extension, maintain continuity in <identity and clothing>, <key props>, <layout>, <camera axis>, <audio environment>.
The same subject must remain the same continuous object throughout, without duplication or splitting; its appearance and number of parts stay stable. No subtitles, text, or signs appear on screen.
```
Backward: describe what happens first, then "The final frame of the extended segment connects naturally to the first frame of @Video1: keep …", plus "Characters, props, or effects that belong only to later parts of the source video must not appear early." [OFFICIAL S7] The source must already be text-free (remove text in an edit pass first).
Worked example (forward, 6 s):
```text
Extend @Video1 forward. The first frame of the extended segment directly continues from the final frame of @Video1: the cyclist keeps riding left to right along the same riverside path at the same speed, same tracking camera height and afternoon side light from frame left.
Then, the cyclist brakes gently, stops beside a wooden bench, and puts the left foot down; at the end, the bicycle stands still with both wheels on the path.
Throughout the extension, maintain continuity in the cyclist's face, blue jacket and helmet, one bicycle, the river on the right, and the camera axis.
The cyclist and the bicycle each remain the same continuous object, without duplication or splitting. No subtitles, text, or signs appear on screen.
```
Motion transfer is not a Seedance 2.5 mode on Higgsfield; approximate it in omni mode (`@Video1` as motion reference + identity images) or use Genjutsu `hf_mult_motion_control` [HF S15].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Subtitles / captions appear | repeated dialogue words with tone notes; captions in a reference video; portrait frame | "Character's line (emotion): content"; clean references; explicit subtitle line; QA; removal pass [OFFICIAL S2, S6] |
| Misspelled or pseudo-text | any in-frame words | clean plate + post text; if required, text as image reference or letters one by one [OFFICIAL S2] |
| Source text survives an edit | text element not named | name every element with the remove sentence; removal-only pass first [OFFICIAL S2, S6; HF S13] |
| Music despite "No BGM" | SFX rendered as score | enumerate music terms, repeat policy start and end, or strip in post [OFFICIAL S2] |
| Edit routed as reference/extension | no trigger word; "reference Video 1" | trigger first; name `@Video1` directly [OFFICIAL S2, S6] |
| Edit output ~0.3–0.4 s short | model frame processing | 8n+1-frame source or reference mode; conform + QA [OFFICIAL S2; HF S13] |
| Complex multi-requirement edit unstable | several references + edits in one call | split into passes [OFFICIAL S2] |
| Wrong character ↔ reference mapping | upload order ≠ order of first appearance | reorder; one line per subject [OFFICIAL S2] |
| **Dead space / filler** | too little plot per time range; long take without timeline | one real change per range; shorter duration; hold only at the end [OFFICIAL S2; SECONDARY S19] |
| **Arbitrary slow motion** | long ranges, "cinematic" wording | "real-time speed; no slow motion" unless wanted [INFERRED; SECONDARY S19] |
| **Sudden speed changes** | overloaded ranges, speed-ramp words | even event density; "constant natural speed" [OFFICIAL S2; INFERRED] |
| **Unmotivated cuts / transitions** | packed ranges; vague multi-shot wording | "continuous one-shot, with no jump cuts" or explicit `Shot N` + "Hard cut." [OFFICIAL S2] |
| **Morphing** (objects bend, parts change) | fast orbit, weak references | 2–4 single-view images as one rigid entity; slow moves [OFFICIAL S7, S9; INFERRED] |
| **Identity drift** | mixed reference sheets, small face area | headshot + full body; "without drifting or changing identity" [OFFICIAL S2, S6] |
| **Duplicated objects / twins** | multi-view sheets, unlabeled subjects, >4 people | single-person images, counts, no-twin sentence [OFFICIAL S2, S6] |
| **Clothing / age changes** | unanchored wardrobe | clothing named as an invariant; official exclusion "Exclude face swaps, changes in age or clothing, sudden height shifts, added or missing characters, spatial jumps" [OFFICIAL S2] |
| Objects teleport or reset after cuts | no restated state | end state per stage, restated at next use [OFFICIAL S7; INFERRED S17] |
| Count of multiples changes after an exit, occlusion or cut (three capsules become one after a walk-past) | items not counted per stage; a walk-past or cut with no restatement | counts with numbers in every end state and after re-entry; "exactly N …; none appears or disappears" (`reference/anomaly-catalog.md` §2.1, §2.5) [INFERRED; observed 2026-10] |
| Product used through the wrong part (a straw bottle drunk from the side without the spout; a sealed can sipped) | the use written as a result only ("drinks"), without the part or the preparation step | initial state → operation on the named part → result, with the contact point; the preparation step first; one [Exclusions] item naming the wrong use (`reference/anomaly-catalog.md` §2.2, §2.3) [INFERRED; observed 2026-10] |
| A later state leaks into frame 0 (a raised tab on a can cracked later) | a reference image that shows the later state | attach only the t=0 state; write it in [Start state] (`reference/anomaly-catalog.md` §2.3) [observed 2026-10] |
| A thrown or passing thing goes through the product; the product sinks into a surface or shows through an arm | the path written without the product ("he tosses the paper"); complex multi-subject interaction is a stated weakness [OFFICIAL S1] | write the path relative to the product with the side and the landing spot, or the hit and its consequence; "[Exclusions] nothing passes through the bottle; it is solid and opaque"; move the anchor out of the path when the story does not need the contact (`reference/anomaly-catalog.md` §2.14) [observed 2026-10] |
| Object snaps, or pauses on a pose then resumes | free physical motion (a spin, toss or roll, or a vehicle's move) given exact times or a required end state ("never timestamp high-frequency actions" [OFFICIAL S2]) | describe the physics only; give the end state a visible cause; time product-pun text to the real moment (`generation-system.md` §5b) [INFERRED] |
| Inserted asset looks pasted on (a can on a dresser at 2–3× real size, squared to the lens, flat cool light in a warm dim room, no contact shadow, straight-on in a low-angle room) | product-photo lighting, exposure, background and camera angle inherited; a tight product crop; an anchor alone on an empty edge | "@ImageN defines only shape, proportions, colours and label; do not use its lighting, exposure, background, shadow or camera angle"; the room's light on the product, its size against a named neighbour, its mark angle, its contact shadow like the neighbour's, the scene's camera angle; an anchor touching or partly behind something; padded crops; the eleven-sign paste test in QC (`reference/anomaly-catalog.md` §2.15) [INFERRED; observed 2026-10] |
| Glowing eyes / fingerprint textures / bubbling audio | intense emotion words; oversized AI references; water wording | neutral emotion + "normal human eyes"; resize references; drop water/echo words [OFFICIAL S2] |
| Person swap leaves original in reflections | partial scope | DETAILED exclusion sentence [HF S13] |

## 6. Model-specific features and controls

- 30 s single pass, integer-second timestamps, multi-view subject images, locked vs unlocked tasks (edit/first-frame/extension lock the ratio) [OFFICIAL S2].
- Draft → final (`draft`, `draft_job_id`, `seedance_2_5` only): 480p preview, 1080p final within 7 days — needs a downscale for this project [OFFICIAL S3; HF S11].
- Clay-model rendering, storyboard grids (≤15 panels), multi-keyframe order, seamless transition between two videos ("Do not alter the two uploaded videos themselves"), one-click video [OFFICIAL S2].
- Editing: add/modify/remove incl. subtitles and watermarks, reference-image edits, audio edits and translation with lip re-sync, timestamp-scoped edits [OFFICIAL S2]; marketed as green-screen and camera-perspective editing [OFFICIAL S1].
- `bitrate_mode:"high"` for finals; `ad_multiplier` for Higgsfield's multi-variant edit workflow ("multiple edits of one clip") [HF S11, S12, S13].
- Official prompt optimizer `sd25-pe` (templates in §4) [OFFICIAL S2, S7]. Not on Higgsfield: seed, negative prompt, camera_fixed, MOV, last-frame return, Elements, watermark toggle [HF S11, S12].

## 7. Model-specific pre-generation checklist

- [ ] One primary task; `mode` matches; edit prompts start with a trigger and name `@Video1`; extensions say "Extend @Video1 forward/backward" and set `extension_mode`.
- [ ] Fixed format: `aspect_ratio:"9:16"` + `resolution:"720p"` (or `auto` with a 9:16 start frame / 9:16-reframed source); no draft unless a 480p preview is wanted.
- [ ] No duration, ratio, resolution, fps or sound toggle in the prompt text.
- [ ] One role line per asset ("use only / do not use"); `medias` order = `@ImageN/@VideoN/@AudioN`; subjects in order of first appearance; references resized to ≤ output resolution; standard JPGs.
- [ ] Limits: ≤30 images, ≤10 videos (≤30 s), ≤10 audio (≤30 s), ≤50 total; edit source 4–30 s (ideally ≤20 s), 1–5 images.
- [ ] Timestamps contiguous, one change per range, end states stated and carried forward; "real-time speed" unless slow motion is intended.
- [ ] One camera behaviour per shot; lock phrase if static.
- [ ] Dialogue: speaker + language + delivery + `{exact words}`; listeners silent; music policy stated.
- [ ] Visible text: Analyze Mode → clean-plate line, blank carriers, no `【】`, text-free references; Edit Mode → every source text element named in a remove sentence; no Higgsfield preservation block.
- [ ] Integration line for inserted assets: size, hand/grip, orientation, scene light direction/colour temperature, shadow, reflection.
- [ ] Size from the reckoning: ratio to a named neighbour, depth, "small object in the background" where it is one, constancy; the reference padded; a start frame measured with `atp.py scale` (`reference/anomaly-catalog.md` §2.7).
- [ ] Counts with numbers in every stage; every use beat names the part, the preparation step and the contact point; one [Exclusions] item per product for its own wrong use and count; no reference shows a later state than t=0 (`reference/anomaly-catalog.md` §3).
- [ ] Identity: headshot + full body; no-twin sentence; DETAILED exclusion for person swaps.
- [ ] Edits: `generate_audio:false`, `duration: ceil(source)`, `aspect_ratio:"auto"`, `bitrate_mode:"high"`; audio restored and duration conformed locally.
- [ ] Prompt ≤3,900 characters; no ids or URLs in the prompt; `get_cost:true` preflight done.

## 8. Sources

- S1 [OFFICIAL] ByteDance Seed — "One-take Creation, Flexible Referencing: Introducing Seedance 2.5" (2026-07-31) — https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5 (accessed 2026-09-30)
- S2 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.5 prompt guide (formula, timestamps, negative control, camera, storyboards, keyframes, edits, extension, FAQ incl. subtitles, text spelling, no-BGM, glowing eyes, fingerprint textures, edit duration, aspect-ratio edits, mapping order; examples E1, E3–E5, E7, E8) — https://docs.byteplus.com/en/docs/ModelArk/2607689 (accessed 2026-09-30)
- S3 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.5 tutorial (task types, draft mode, prompt rules and bracket notation, usage limits, languages) — https://docs.byteplus.com/en/docs/ModelArk/2607688 (accessed 2026-09-30)
- S4 [OFFICIAL] BytePlus ModelArk — Create a video generation task (API reference incl. the resolution × ratio pixel table: 9:16 at 720p = 720×1280) — https://docs.byteplus.com/en/docs/ModelArk/1520757 (accessed 2026-09-30)
- S5 [OFFICIAL] BytePlus ModelArk — Model list (bit depth, 24 fps, durations) — https://docs.byteplus.com/en/docs/ModelArk/1330310 (accessed 2026-09-30)
- S6 [OFFICIAL] BytePlus ModelArk — Dreamina Seedance 2.0 series prompt guide (predecessor FAQ used where 2.5 docs are silent) — https://docs.byteplus.com/en/docs/ModelArk/2222480 (accessed 2026-09-30)
- S7 [OFFICIAL] Seedance team — `sd25-pe` "Seedance 2.5 Prompt Optimizer" skill v0.1.1 (owner: seedance), distributed from https://arkdocs-en.tos-ap-southeast-1.volces.com/skills/ as published in S2/S3; local copy `C:\Users\Glaresquare1\.claude\skills\sd25-pe\SKILL.md` (read 2026-09-30; examples E2, E6)
- S8 [OFFICIAL] BytePlus ModelArk — Create portrait videos with Dreamina Seedance models — https://docs.byteplus.com/en/docs/ModelArk/2608626 (via local notes 2026-09-16; not re-fetched)
- S9 [OFFICIAL] Dreamina (CapCut) — Seedance 2.5 Prompt Guide: Formula & Examples — https://dreamina.capcut.com/seedance/seedance-2-5-prompt (accessed 2026-09-30)
- S10 [OFFICIAL] Team Seedance — Seedance 2.0 model card, arXiv:2604.14148 (lineage) — https://arxiv.org/abs/2604.14148 (accessed 2026-09-30)
- S11 [HF] Higgsfield live catalog snapshot — `higgsfield/catalog-snapshot-2026-09-30.json` (`seedance_2_5`, `ad_multiplier`)
- S12 [HF] Higgsfield MCP tool contract (`generate_video` call shape, `get_cost`, role coercion, duration snapping, media intake, `jobs_wait`, Elements scope) as verified for /analyze-then-pick, 2026-09-30
- S13 [HF] Higgsfield Ad Multiplier workflow v1.4 + `references/prompt-writer.md` + `references/media-pipeline.md` — local copies in `higgsfield/first-party/` (retrieved 2026-09-30); this project overrides its text-preservation rule
- S14 [HF] Higgsfield — Seedance 2.5 page — https://higgsfield.ai/seedance/2.5 (accessed 2026-09-30)
- S15 [HF] Higgsfield Genjutsu preset instructions — `higgsfield/first-party/genjutsu.md` (retrieved 2026-09-30); `analyze-stack/seedance/SEEDANCE-EDIT.md` §9 (2026-09-16)
- S16 [HF] Local research `analyze-stack/research/higgsfield-mcp.md` (2026-09-16): observed role aliases, `<<<image_1>>>` normalisation, `width:720,height:1280` stored for 9:16 720p, H.264 outputs, `_trim.mp4` re-encoding; its credit figures are stale
- S17 [INFERRED] Seedance 2.5 Director bundle rev 2.1.0 (`analyze-stack/seedance/director/`) — authored continuity/causality method; its own `references/sources.md` says its external citations were not re-verified
- S18 [SECONDARY] Krea — Seedance 2.5 API guide (IP-name rejections) — https://www.krea.ai/blog/seedance-2-5-api-access-guide-features-code-examples-for-long-form-video (via local notes 2026-09-16)
- S19 [SECONDARY] fal.ai — "Seedance 2.5 Prompting Guide" (long-take timelines, "no slow motion", continuation phrasing) — https://fal.ai/learn/devs/seedance-2-5-prompting-guide (via local notes 2026-09-16; not re-fetched)

## 9. Open questions / unverified behaviour

- Which `mode` Higgsfield expects for `start_image`/`end_image`; whether `start_image` may be combined with `*_references`.
- Whether `draft_job_id` finalize calls must resend prompt/medias; whether draft works with edit/extension.
- Confirm on Higgsfield that `video_extension` returns only the new segment, as ByteDance's own example does (ffprobe the first result: length ≈ `duration`), and which direction each `extension_mode` value maps to.
- Actual output dimensions for 9:16 first-frame and edit tasks on Higgsfield (720×1280 expected); behaviour when a start frame or source is not exactly 9:16.
- Whether Higgsfield's `_trim.mp4` re-encode changes frame counts (defeating the 8n+1 fix); what `duration_policy:"strict"` does.
- Whether audio-only reference calls are accepted on Higgsfield.
- Real-face moderation outside the Ad Multiplier recipe.
- Prompt ceiling for non-edit calls (only the 3,900-character edit contract is documented).
- Removal quality for large or moving overlays (full-screen title cards, animated stickers) and spurious-subtitle rates at 9:16 on 2.5.
