---
guide: minimax-h3
title: MiniMax H3 / H3 Max
provider: MiniMax (H3); H3 Max post-trained by fal on MiniMax H3, jointly released with MiniMax
higgsfield_model_ids: [minimax_h3, minimax_h3_max]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# MiniMax H3 / H3 Max — model engineering guide

> Scope: MiniMax H3 is an open-weight, omni-modal audio-video model: text, first/last-frame images, and up to 12
> reference images/videos/audio clips in one request, with native stereo sound, 4–15 s [OFFICIAL]. H3 Max is "a video
> generation model post-trained by fal.ai on MiniMax H3 and optimized for high-speed generation", 480p/768p only
> [OFFICIAL]. Higgsfield ids: `minimax_h3` (2K only) and `minimax_h3_max` (480p/768p) [HF]. MiniMax's V2 OpenAPI file
> is titled "MiniMax video generation V2 (Hailuo-03) API" [OFFICIAL], hence the nickname "Hailuo 3" [SECONDARY]; the
> older Hailuo 02/2.3 models are covered in `minimax-hailuo.md`. Output format is fixed at 9:16, 720p — both ids
> need a deterministic downscale (§2.6). The live `models_explore` catalog always wins over this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** Released 2026-07-31: "a general-purpose multimodal generation model. H3 understands unified context
  across text, images, video, and audio, generating video with native stereo sound, up to 15 seconds at 2K
  resolution" [OFFICIAL]; open weights on Hugging Face (MiniMax H3 Community License) [OFFICIAL]; "excelling at
  instruction following, accurate text and brand rendering, and V2V motion transfer" [OFFICIAL]; 24 fps, 32 kHz
  stereo, stable dialogue in 11 languages [OFFICIAL].
- **H3 Max** (`MiniMax-H3-Max`): "fast generation variant", 480P/768P, "2K is not supported", 5–15 s [OFFICIAL];
  post-trained by fal "with a particular focus on prompt adherence and visual quality", ~3 s wall time per 5 s clip
  [OFFICIAL, fal as co-developer].
- **Best for:** product, packaging and UI visuals; multi-reference fusion (character + prop + scene + voice + motion);
  V2V motion/camera transfer; regenerating a supplied clip (≤15 s); short intentional in-frame text (§3.11).
  Artificial Analysis (2026-09-30): image-to-video with audio #1 (Elo 1181); text-to-video #4 (768p, Elo 1138)
  [SECONDARY].
- **Weaker at:** "Visual detail can still be improved in certain scenarios" [OFFICIAL]; MiniMax's own production
  skill falls back to Seedance 2.0 for "complex shots, elastic Pixar-style performance, and tension-driven action"
  [OFFICIAL]; it renders text readily, so clean plates need explicit suppression (§3.11).
- **Choose H3** for many references, reference audio, motion transfer, in-frame short text or crisp product detail;
  **H3 Max** for fast 768p drafts and batches. **Choose another model when** you need >15 s or a silent switch
  (`wan3_0`), or demanding action performance.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | upstream requires an explicit ratio (not adaptive) [OFFICIAL] |
| First frame → video | `start_image` | ratio follows the image [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` | FL2VA "favors a single shot" [OFFICIAL] |
| Last frame only | `end_image` | documented inconsistently upstream (§2.5) |
| Reference-to-video | `image_references` (≤9), `video_references` (≤3), `audio_references` (≤3); ≤12 files | exclusive with frame roles [OFFICIAL] |
| V2V motion transfer, Edit Mode regeneration | `video_references` + prompt | upstream capability [OFFICIAL]; Higgsfield routing [INFERRED] |
| Context-IR prompt enhancer, 768p→2K regeneration task | — | N/A on Higgsfield as separate calls [HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `minimax_h3` | `duration` | number, min 4, max 15 | 5 | "Duration in seconds (4-15)." [HF] |
| `minimax_h3` | `resolution` | `2K` | `2K` | only option on Higgsfield; upstream also offers 768P [OFFICIAL/HF] |
| `minimax_h3` | `batch_size` | number, min 1, max 4 | 1 | "Number of videos to generate (1-4)." [HF] |
| `minimax_h3` | `folder_id` | string, nullable | — | output folder [HF] |
| `minimax_h3_max` | `duration` | number, min 5, max 15 | 5 | "Duration in seconds (5-15)." [HF]; 4 s not supported upstream [OFFICIAL] |
| `minimax_h3_max` | `resolution` | `480p`, `768p` | `768p` | always `768p` under the fixed format (§2.6); "2K is not supported" [OFFICIAL] |
| `minimax_h3_max` | `batch_size` | number, min 1, max 4 | 1 | [HF] |
| `minimax_h3_max` | `folder_id` | string, nullable | — | [HF] |
| both | `aspect_ratio` | `auto`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | — | always `9:16` (§2.6) [HF] |
| both | negative_prompt, seed, audio switch, `prompt_expansion_mode` (Max), callback | — | — | not exposed on Higgsfield [HF]; H3 has no negative-prompt field even upstream [OFFICIAL] |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | exact opening frame (`first_frame`) | 1; JPG/PNG/WEBP/HEIC/HEIF, ≤30 MB, 256–5760 px, aspect 0.4–2.5 [OFFICIAL] | excludes all references [OFFICIAL]; 9:16 |
| `end_image` | exact closing frame (`last_frame`) | 1 [OFFICIAL] | pair with `start_image` unless tested (§2.5) |
| `image_references` | character, prop, scene, style, storyboard | ≤9 [OFFICIAL] | reference image 1, 2… [OFFICIAL] |
| `video_references` | motion, camera, rhythm, identity, or the source clip to regenerate | ≤3 clips, 2–15 s each, ≤15 s total, MP4/MOV (H.264/H.265), ≤50 MB, 23.976–60 fps [OFFICIAL] | reference video 1, 2… |
| `audio_references` | voice timbre, music, beat, dialogue source | ≤3 clips, 2–15 s each, ≤15 s total, WAV/MP3, ≤15 MB [OFFICIAL] | reference audio 1, 2… |
| (all references) | — | ≤12 files total [OFFICIAL] | — |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- **Duration:** integers, H3 4–15, Max 5–15 [OFFICIAL/HF]. "Always match the total duration of the description to the
  requested video length" [OFFICIAL skill].
- **Resolution:** `minimax_h3` is always 2K on Higgsfield (upstream: base generation at a 768-pixel short edge, then
  H3-Regenerate-2K re-renders in context) [OFFICIAL architecture/HF]; `minimax_h3_max` 768p for deliverables (§2.6).
- **Aspect ratio upstream:** text-to-video — `ratio` "is required and cannot be adaptive"; image-to-video — "the
  aspect ratio is determined by the input image and ratio is always adaptive"; reference-to-video — optional
  [OFFICIAL]. Always send `9:16` and 9:16 frames.
- **Audio:** always generated — voice, SFX and music "jointly modeled", native stereo [OFFICIAL]; no switch upstream
  or on Higgsfield [OFFICIAL/HF]. For silence, prompt no music/dialogue and strip the track locally [INFERRED].
- **Batch:** `batch_size` 2–4 returns several candidates from one call; credits likely scale [INFERRED].

### 2.4 Call recipes
Text-to-video:
```json
{"model":"minimax_h3","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","resolution":"2K","batch_size":1}
```
First frame → video (9:16 frame):
```json
{"model":"minimax_h3","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID or JOB_ID>","role":"start_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"2K"}
```
First + last frame → video (both 9:16, identical size):
```json
{"model":"minimax_h3","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"2K"}
```
Reference-to-video (order inside each role = its number):
```json
{"model":"minimax_h3","prompt":"<PROMPT citing reference image 1, reference image 2, reference video 1, reference audio 1>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":10,"aspect_ratio":"9:16","resolution":"2K"}
```
Edit Mode — regenerate a supplied 9:16 clip (set `duration` to the source length in whole seconds, ≤15; 10 shown; verify routing first):
```json
{"model":"minimax_h3","prompt":"<EDIT PROMPT, §4.4>","medias":[{"value":"<VIDEO_MEDIA_ID or JOB_ID>","role":"video_references"}],"duration":10,"aspect_ratio":"9:16","resolution":"2K"}
```
Fast draft / batch on Max:
```json
{"model":"minimax_h3_max","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","resolution":"768p","batch_size":4}
```
Preflight any call with `get_cost: true` (no submission) [HF].

### 2.5 Parameter gotchas
1. **Frames and references are mutually exclusive:** "if any reference_image / reference_video / reference_audio role
   appears in content, then first_frame / last_frame must not appear (and vice versa)" [OFFICIAL]. For a strict first
   frame plus a character, pre-compose a start frame containing the approved character [INFERRED].
2. **`end_image` alone** is listed as valid ("Image-to-video, last frame") and also as "must be paired with
   first_frame" in the same reference [OFFICIAL, contradictory] — test before relying on it.
3. **T2V needs a concrete ratio;** never send `auto` [OFFICIAL/INFERRED].
4. **A prompt is mandatory in every mode** ("content must include a non-empty text item") [OFFICIAL]; limit 7,000
   characters [OFFICIAL].
5. **2K only on `minimax_h3`**; H3 Max drafts are a different (post-trained) model — they preview composition, not
   the exact final [INFERRED].
6. **Hidden upstream processing:** H3-Context-IR (prompt enrichment) is a separate endpoint and Max's
   `prompt_expansion_mode` defaults to `balanced` [OFFICIAL]; whether Higgsfield enriches your prompt is undocumented
   [INFERRED] — write explicit prompts.
7. **No seed:** use `batch_size` for choices [HF/INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| id / mode | params | expected output | action |
|---|---|---|---|
| `minimax_h3`, any mode | `"aspect_ratio":"9:16","resolution":"2K"` (no 720p option); frames 9:16 | 2K portrait; exact pixels undocumented. H3-Base uses "a 768-pixel short edge and dimensions aligned to a multiple of 32; 1344 × 768 is the native 16:9 canvas" [OFFICIAL] → base 9:16 ≈ 768×1344 (0.571, slightly wider than 9:16), 2K regenerated from it [INFERRED] | always downscale |
| `minimax_h3_max`, any mode | `"aspect_ratio":"9:16","resolution":"768p"` | ≈768×1344 [INFERRED from the same canvas rule] | downscale: scale to ≈732×1280, crop ≈12 px of width |
| `minimax_h3_max` 480p | — | would need upscaling to 720×1280 | drafts only, never deliverables |

Always post-process with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to exactly
720×1280, never stretched). For a 768×1344 source it scales to 732×1280 and crops 12 px of width (~1.6% loss); use
`--focus-x` if the subject is off-centre. `conform` refuses losses above 12% — that means a non-9:16 output:
regenerate with 9:16 inputs [INFERRED]. Keep faces, products and any intentional text away from the extreme left/right
edges [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
MiniMax documents two registers [OFFICIAL]:
1. **Hosted API prompts** are free-form: "Just describe the relationship between the context and the target video in
   words" [OFFICIAL]; first-party examples read like briefs (format → "Image N: role" list → core story → tone).
2. **The structured representation H3-Base consumes** (produced by H3-Context-IR, "critical to the quality of the
   final output"; MiniMax recommends using it "or following the 'Prompting Guidance' to build your own") [OFFICIAL]:
   `integrated_multimodal_description` (shots on a timeline), `overall_soundscape` (1–4 sentences), and
   `non_diegetic_music` (1–3 sentences or `N/A`); reference mode adds `subject_definitions`, `summary`,
   `retention_analysis` and a `detailed_description` of "normally 350–500 English words" [OFFICIAL].

**Recommended for Higgsfield [INFERRED]:** a hybrid — one brief line assigning each reference its role, a shot body in
the IR conventions (`[Shot 1] …`, `[Shot 2] At 00:04.000, the camera cuts to …`), then one `Sound:` and one `Music:`
sentence. It reads naturally if Context-IR runs and mirrors H3-Base's format if it does not. English; dialogue in its
own language [OFFICIAL]. 80–250 words for 4–8 s, up to ~450 for 12–15 s [INFERRED]. "Prefer concrete visual and audio
details over abstract words like 'cinematic' or 'beautiful'" [OFFICIAL skill]. Worked patterns: §4.0.

### 3.2 Subject and identity
At first appearance give identity-carrying traits (age range, hair, clothing, distinctive items) and frame position;
then refer back consistently ("the woman from Shot 1") [OFFICIAL IR examples]. Subject definition pattern: "<Subject
1> is the young woman in <Picture 1>, with long dark hair, a blue cardigan, and a thin silver necklace." [OFFICIAL]

### 3.3 Action, motion and physical interaction
Write observable steps with results: the official FL2VA example has the subject release the handle, raise the
umbrella, press the runner "until the canopy opens" [OFFICIAL]; debris and liquids "slide outward… lose momentum and
settle" [OFFICIAL]. Keep action density moderate (demanding action goes to another model in MiniMax's own skill)
[OFFICIAL]. Contact, grip and states: §3.14.

### 3.4 Environment, lighting and style
Open `[Shot 1]` with style and composition: "Live-action, cinematic, a medium-wide shot frames…"; guide styles:
cinematic, live-action, 2D-animated, 3D CG, claymation, watercolor, vintage film [OFFICIAL]. In reference mode, state
the style before `[Shot 1]` [OFFICIAL]. Light matching: §3.14.

### 3.5 Chronology, timing and multi-shot structure
- "Native multi-shot modeling" [OFFICIAL]. "Do not add a timestamp to the first shot… begin each [later shot] with a
  strictly increasing cut time that falls within the video duration: `[Shot 2] At 00:03.500, the camera cuts to…`"
  [OFFICIAL].
- "A cut should introduce new information about the subject, space, state, viewpoint, or time. If only the distance or
  a slight angle needs to change, prefer camera motion." [OFFICIAL] Dissolves, fades and wipes only when explicitly
  requested [OFFICIAL].
- Dialogue crossing a cut "continues seamlessly across the cut" [OFFICIAL]; the timeline must fit the duration
  [OFFICIAL].

### 3.6 Camera language and dedicated camera / motion controls
Prompt-only on Higgsfield [HF]. Vocabulary: Zoom In/Out, Push In/Pull Out, Pan, Truck, Tilt, Pedestal, Arc Shot,
Tracking Shot, Static Shot, Shake Slightly/Strongly, POV, Roll; amplitude "with small/large amplitude"; speed "at
slow/fast speed" [OFFICIAL]. "Camera motion should be written as a natural English action within the shot, rather
than stacked as separate labels" [OFFICIAL]; the platform guide also mentions bracket hints (`[pan]`, `[zoom]`,
`[static]`) [OFFICIAL] — prefer the sentence form.

### 3.7 References (image / video / audio)
- **Numbering:** hosted-API examples number per modality ("reference images 1 and 2", "reference video 1",
  "reference audio 1"); the launch blog labels "Video 1, Image 2, Audio 3"; self-hosted R2V uses `<Picture 1>`,
  `<Video 1>`, `<Audio 1>` "in connection order" [OFFICIAL, inconsistent]. Use per-modality numbers in `medias`
  order plus a descriptor ("reference image 1, the man in the navy jacket") [INFERRED].
- **Declare roles:** "state which reference controls identity, style, motion, camera, or voice" [OFFICIAL]; one subject
  may combine sources ("appearance comes from <Picture 1> and walking motion comes from <Video 1>") [OFFICIAL].
- **Audio:** "Voice timbre follows reference audio 1." [OFFICIAL]; with timbre-only references the original words
  are not carried over [OFFICIAL IR rule].
- **Grids:** anchor sheets are avoided "because video models may reproduce the panel layout" — use standalone photos
  [OFFICIAL skill].
- **Analyze Mode:** take only the declared attribute from a reference clip — never its captions, usernames,
  watermarks or wording (§3.11).

### 3.8 Start and end frames
- I2VA: "first-frame anchor → action onset → continuous development → result or reaction"; keep identity, clothing,
  colors, key objects and spatial relationships [OFFICIAL].
- FL2VA: "first-frame state → observable intermediate changes → progressively narrowing differences → last-frame
  state"; "FL2VA generally favors a single shot"; the last frame "must be reached by the final [Shot N] at the end of
  the video" [OFFICIAL].
- L2VA (last frame only): infer a plausible earlier state and converge [OFFICIAL] (§2.5 item 2).
- Frames 9:16 and identical in size (§2.6).

### 3.9 Audio, dialogue and sound
- Speakers get stable IDs `(S1)`, `(S2)`; lines go in `<d>[English] …</d>`, "Preserve every original word and
  punctuation mark verbatim" [OFFICIAL]. The hosted-API example writes "Character speaks: Follow the wind, live
  free." [OFFICIAL]
- Voiceover: "says in an off-screen voiceover" and state that the on-screen character's lips "remain completely
  closed" [OFFICIAL].
- Soundscape (ambience, action sounds) and non-diegetic music are separate sentences; "Use N/A when there is no
  non-diegetic music" [OFFICIAL]. 11 stable dialogue languages [OFFICIAL].

### 3.10 Negative constraints
No negative-prompt field upstream or on Higgsfield, and the official IR format has no negative section
[OFFICIAL/HF]. MiniMax's skills write constraints as plain sentences ("no labels, no subtitles unless requested, no
watermarks") [OFFICIAL]. One short constraint sentence at the end plus positive statements of the wanted state
("the product keeps its original matte black finish") [INFERRED].

### 3.11 Visible text
**(a) Reliability.** MiniMax claims "accurate text and brand rendering" and designed the 2K regeneration to recover
"small text and fine detail" [OFFICIAL]. Its own production skills render short in-frame copy ("3-5 English words",
one line) and lyric typography with "only one main typography event" per shot, while advising "If the video model
tends to make typography mistakes, reduce copy frequency proactively" [OFFICIAL]. No independent measurement was
found. Verdict: the most text-capable model in this set for short, scene-bound text, provided every frame is QC'd;
captions, subtitles and anything long or exact still go to post [INFERRED].

**(b) Clean plate — default in Analyze Mode.** Exact captions, hooks and labels go on in post (`atp.py captions`,
libass). Because H3 adds text readily, suppress it explicitly with MiniMax's own phrasing — "no labels, no subtitles unless requested, no watermarks"; "Do not add subtitles or text unless the user
explicitly asks" [OFFICIAL skills] — as the closing sentence, e.g. "No subtitles, captions, titles, labels, logos,
watermarks or any letters or numbers appear anywhere in the frame; screens and packaging show only plain color and
shapes." [INFERRED wording]. Also:
- In H3's representation, visible text is written in double quotes ('A red neon sign reading "…" glows') [OFFICIAL];
  so never put non-dialogue strings in quotes; write dialogue after "says:" (optionally `<d>[English] …</d>`)
  [INFERRED].
- "Do not write arrows, slashes, plus signs, or separators, because the model may render them as in-frame copy";
  strip storyboard labels — they "must NOT appear in the final clip" [OFFICIAL skills].
- Avoid text-cueing framings ("title card", "tagline", "end card", "logo reveal", "lower third", "UI motion demo",
  "kinetic typography"); first-party examples in those genres include typography [INFERRED from OFFICIAL examples].

**(c) Intentional in-frame text (exploit).** When a sign, package or screen in the scene should carry text: write it
once, in double quotes, bound to its surface and position (official form: "A red neon sign reading "…" glows above
the doorway.") [OFFICIAL]; 1–5 words, one line, one text event per shot, not in a lower subtitle position ("Text must
stay on one line"; "Do not place text in a lower subtitle position") [OFFICIAL skill]; generic font descriptors
("bold clean sans-serif"); use `minimax_h3` 2K rather than Max for small text [INFERRED]; keep it away from the
cropped edges (§2.6); verify spelling with `atp.py qc --mode analyze --allowed-text "<text>"` and fall back to a clean
plate + post if wrong. Approved real product text comes from the reference or start image: "the label stays exactly as
in reference image 2" [INFERRED].

**(d) Edit operations — removing source text (Edit Mode).** H3 can take the source as `video_references` and
regenerate it; the official IR frames this as "The target video is an edited version of <Video 1>." with each
element's retention stated [OFFICIAL]. Text removal is not specifically documented [INFERRED]. Small static overlays
can first be removed locally with `atp.py clean --delogo`; captions over the subject belong to the model. Wording:
"The target video is an edited version of reference video 1 with every caption, subtitle, username, watermark,
sticker, timestamp, meme text, UI overlay and overlay logo removed and the scene behind them reconstructed. The
people, their performance, the camera, cuts, lighting, timing and audio are fully preserved. No letters, numbers or
graphics appear anywhere in the frame." Keep specific source text only when the user asked, naming it. Limits: source
2–15 s [OFFICIAL]; `duration` = source length. Risk: 2K regeneration reuses the original context, which still
contains the overlays [OFFICIAL mechanism → INFERRED risk] — verify with `atp.py qc --mode edit` for reappearing or
ghosted text.

**(e) Watermarks and logos.** The H3 API has no watermark parameter [OFFICIAL, by absence]. "Add a logo only when the
user provides one. Do not generate a fake logo." [OFFICIAL skill] — do not attach logo images unless the logo must
appear. `atp.py qc` OCR flags invented marks on corners and surfaces; regenerate.

### 3.12 Character / identity consistency
One clear image per person (face, hair, full outfit), bound explicitly, with the same visible traits restated at first
appearance [OFFICIAL patterns]. Replacing a performer from a clip: "the character's appearance follows reference image
1; the motion follows reference video 1" and state that the person in the video does not appear [INFERRED]. Keep
speaker IDs and descriptors identical across shots and clips; several views may define one subject if you say so
[OFFICIAL].

### 3.13 Product and object fidelity
First-party product prompts describe the design next to the image: "Image 3: eyewear design — wrap-around curves,
sharp cat-eye/goggle hybrid silhouettes, mirror reflections, streamlined temples." [OFFICIAL] Product-skill rules:
standalone single-product photos, "Never recolor the product body unless the user explicitly asks", real product
actions (opening, rotating, lifting, snapping, folding) [OFFICIAL]. Add a geometry lock: "the product keeps its exact
silhouette, proportions, part layout and size relative to the hand in every shot" [INFERRED]. For a mandatory hero
composition use the packshot as `start_image`/`end_image` [INFERRED].

### 3.14 Integration and continuity
**Across clips.** Reuse identical references, labels, descriptors and speaker IDs [OFFICIAL skill: "keep reference
labels consistent"]. Chain clips: last frame of clip A (`atp.py last-frame --video <clip> --out <handoff.png>`) → `start_image` of clip B
(`media_upload` → PUT → `media_confirm`) [HF contract]. Split continuing dialogue at sentence boundaries [INFERRED]. MiniMax's prompt format also defines a "`video continuation` | New content continues, extends, resumes, or transitions from an existing source video" task with `<Video N>` as the "continuation starting point" [OFFICIAL, https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md]; untested on Higgsfield. MiniMax's own recipe for long videos: "if Shot B continues the same scene, use Shot A's tail frame as Shot B's head frame", with cut points on pauses or beats [OFFICIAL]. Never mix H3 and H3 Max inside one take [INFERRED].

**Inserted or replaced assets.** Official anchoring phrases: "preserving her appearance, clothing, seat position, and
the carriage layout"; "settles into the pose, spacing, and composition established by Picture 2"; "the exact broken
arrangement, hand position, camera angle, lighting, and final composition" [OFFICIAL]. Build asset sentences as: size
relative to a hand/face → orientation → grip and contact points → occlusion → final placement ("the bottle from
reference image 2, palm-sized, label facing the camera, held in her left hand with fingers wrapped around its lower
half; her thumb overlaps its edge; she sets it upright at the right of the table") [INFERRED structure].

**Scene light on the asset.** Official IR examples tie light to surfaces ("casting harsh, overexposed illumination
across her face"; light that "reflects vividly in her dark eyes") [OFFICIAL]. State key-light direction, color
temperature, contact shadows and reflections for the asset [INFERRED]. MiniMax's product skill warns against "reflective
floors, glass tables, or cheap studio mirror surfaces" [OFFICIAL] — avoid invented mirror reflections.

**Persistent states.** Official examples keep physical states ("She folds the letter along its existing crease")
[OFFICIAL]. End each beat with the state: placed objects stay put, containers open/closed, liquid level, same hand
[INFERRED].

**Known failures.** "Visual detail can still be improved in certain scenarios"; demanding action is routed elsewhere;
grids get reproduced; typography mistakes happen [OFFICIAL]. Slop prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. T2VA in the IR format — Video Prompt Writing Guide, https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md
   > "integrated_multimodal_description: [Shot 1] Live-action, cinematic, a medium-wide shot frames a baker opening
   > the shutters of a small street bakery before sunrise. The camera pushes in with small amplitude at slow speed as
   > the middle-aged baker with a calm, slightly raspy voice (S1) places a fresh loaf on the wooden counter and says:
   > <d>[English] First batch of the morning.</d> [Shot 2] At 00:05.000, the camera cuts to a close-up of steam rising
   > from the sliced bread while the baker's final words carry over from the previous shot. overall_soundscape: […]
   > non_diegetic_music: A soft acoustic-guitar pattern at a moderate tempo, joined by sparse upright-bass notes and a
   > gentle fade at the end."
2. I2VA — same guide
   > "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
   > integrated_multimodal_description: [Shot 1] Live-action, cinematic, the young woman shown in <Picture 1> remains
   > beside the rain-covered train window, preserving her appearance, clothing, seat position, and the carriage
   > layout. The camera trucks right with small amplitude at slow speed as she lifts her gaze […] She folds the letter
   > along its existing crease."
3. FL2VA — same guide
   > "[…] a rain-soaked cyclist begins in the position and framing established by Picture 1, holding a closed black
   > umbrella beside a silver bicycle. The camera pulls out with small amplitude at slow speed as she releases the
   > bicycle handle, raises the umbrella above her shoulder, and presses the runner upward until the canopy opens. […]
   > settles into the pose, spacing, and composition established by Picture 2 at the end of the shot."
4. Hosted-API prompts — Create Video Generation Task and Video Generation guide, https://platform.minimax.io/docs/api-reference/video-generation-v2-create ; https://platform.minimax.io/docs/guides/video-generation
   > "Pull focus to the people in the background and add more steam to the ramen bowl." · "Character speaks: Follow the
   > wind, live free. Leave worries behind, enjoy the moment. Voice timbre follows reference audio 1." · "The character
   > performs street dance, following the motion in reference video 1; the character's appearance follows reference
   > images 1 and 2."
5. Brief with a role list — H3 Feature Highlights, https://platform.minimax.io/docs/guides/video-prompt
   > "A 16:9 high-fashion brand campaign. Image 1: mood, setting, film grain. Image 2: character. Image 3: bag. Image
   > 4: ending logo. Core story: on a desert highway beside a vintage car, the woman takes a black bag from the trunk,
   > shares a brief quiet moment with the man, then leaves. Tone premium and cool; edit agile and fashion-forward."
6. Visible text convention — Video Prompt Writing Guide
   > "A red neon sign reading "营业中" glows above the doorway."

Patterns they teach:
- **Two registers:** short hosted briefs (4, 5) and the structured IR (1–3). The hybrid template uses the IR shot body
  with a brief role list on top.
- **Order (IR):** keyframe-alignment line (frames only) → `[Shot 1]` style + composition → subject with traits and
  speaker ID → action chain → camera sentence → dialogue → later shots "At MM:SS.mmm" → soundscape → music (1–3).
- **Camera vs subject:** camera is its own clause with type + amplitude + speed, linked with "as" to the subject's
  action (1–3).
- **Temporal markers:** none on Shot 1; cut times as "At 00:05.000"; dialogue can "carry over" a cut (1).
- **Frame anchoring:** "preserving her appearance, clothing, seat position…", "settles into the pose, spacing, and
  composition established by Picture 2" (2, 3).
- **States and physics:** actions end in visible results ("until the canopy opens", "along its existing crease") (2, 3).
- **References:** role list ("Image 2: character") or "follows reference image N / video N / audio N" (4, 5).
- **Audio:** speaker ID + voice description + `<d>[Language] line</d>`; soundscape and music separate, music by
  instrumentation, tempo, dynamics (1).
- **Text:** visible text = a quoted string bound to an object (6) — the lever to exploit or avoid.
- **Exclusions:** no negative section in any official format; constraints are plain sentences.
- **Length:** hosted prompts 10–60 words; IR bodies roughly 100–500 words.

### 4.1 Text-to-video
Follows patterns: IR order, camera clause with amplitude/speed, cut times, separate sound/music, clean-plate close.
```text
[Shot 1] <Style>, <shot size> frames <subject with visible traits> in <setting>, <key light direction + color temperature>. The camera <motion type> with <small|large> amplitude at <slow|fast> speed as <subject> <action onset → development → result at real-time speed>.
[Shot 2] At 00:0X.000, the camera cuts to <new information>. <Action and end state>. <The <speaker> (S1) says: <d>[English] line</d> | no dialogue>.
Sound: <ambience, action sounds, non-verbal sounds>.
Music: <instrumentation, tempo, dynamics | no background music>.
No subtitles, captions, titles, labels, logos, watermarks or any letters or numbers appear anywhere in the frame.
```
Worked example (8 s, 9:16): "[Shot 1] Live-action, cinematic, a vertical medium shot frames a young man in a dark
green raincoat at a bus stop at dusk, cool rain under a warm sodium streetlight from the left. The camera pushes in with
small amplitude at slow speed as he checks the sky, then opens a plain black umbrella; water beads roll off the canopy.
[Shot 2] At 00:05.000, the camera cuts to a close-up of his face as headlights sweep across it; he smiles slightly and
keeps the umbrella in his right hand. Sound: steady rain on the shelter roof, the snap of the umbrella, a distant bus
engine. Music: no background music. No subtitles, captions, titles, labels, logos, watermarks or any letters or numbers
appear anywhere in the frame."

### 4.2 Start frame (and end frame) to video
Follows patterns: frame anchoring phrases, path structure, end state.
```text
Starting exactly from the first frame, <subject as shown>, preserving <appearance, clothing, position, layout>, <action onset>, <intermediate changes>, <result>.
(FLF) The motion settles into the pose, spacing and composition of the last frame at the end of the shot.
The camera <motion type + amplitude + speed>. Light, shadows and colors stay as in the first frame.
Sound: <…>. Music: <… | no background music>. <Clean-plate sentence>.
```
Worked example (6 s, 9:16 frames: a cat on a windowsill → the cat curled asleep): "Starting exactly from the first
frame, the grey cat, preserving its fur pattern and the sill layout, yawns, stretches its front legs along the
windowsill, turns once and curls into the sleeping position of the last frame, its tail wrapping around its paws. The
camera holds a static shot. Light, shadows and colors stay as in the first frame. Sound: a soft purr and faint street
ambience. Music: no background music. No subtitles, captions, logos or watermarks appear anywhere in the frame."

### 4.3 Reference-to-video
Follows patterns: role list, "follows reference …", IR shot body, retention statements.
```text
<Format and style sentence>. Reference image 1: <the character, 3–5 visible traits>. Reference image 2: <the product/prop, geometry description>. Reference video 1: <motion/camera only>. Reference audio 1: <voice timbre of the character>.
[Shot 1] <…> [Shot 2] At 00:0X.000, the camera cuts to <…>
The character keeps the face, hair and outfit from reference image 1 and the product keeps its exact shape, proportions and color from reference image 2 in every shot; take only motion and camera from reference video 1, not its people or any text.
Sound: <…>. Music: <…>. <Clean-plate sentence>.
```
Worked example (10 s, 9:16; image 1 = approved person, image 2 = plain white sneaker, video 1 = a walking clip):
"Clean, bright live-action street style. Reference image 1: the woman, short curly hair, olive jacket, white T-shirt.
Reference image 2: the sneaker, low-top, white leather, thick gum sole. Reference video 1: walking rhythm and tracking
camera only. [Shot 1] A tracking shot follows the woman walking along a sunny sidewalk at real-time speed wearing the
sneakers from reference image 2, matching the pace of reference video 1, soft shadows falling to her right. [Shot 2]
At 00:06.000, the camera cuts to a low close-up of the sneakers stepping over a puddle; the sole flexes naturally.
Take only motion and camera from reference video 1, not its people or any text. Sound: footsteps, light traffic.
Music: no background music. No subtitles, captions, logos, labels or watermarks appear anywhere in the frame."

### 4.4 Video edit / extension / motion transfer
Upstream H3 supports "precise multimodal editing" and V2V motion transfer through reference videos [OFFICIAL]; routing
on Higgsfield is unverified [INFERRED]. Follows the IR edit framing ("The target video is an edited version of …").
```text
Clean regeneration (Edit Mode): The target video is an edited version of reference video 1 with every caption, subtitle, username, watermark, sticker, timestamp, meme text, UI overlay and overlay logo removed and the scene behind them reconstructed. The people, their performance, the camera, cuts, lighting, timing and audio are fully preserved. No letters, numbers or graphics appear anywhere in the frame.
Edit: The target video is an edited version of reference video 1: <one change, with asset size/grip/light>. Everything else — people, camera, cuts, lighting, timing and audio — is fully preserved. <Clean-plate sentence>.
Motion transfer: The character from reference image 1 performs <the moves> of reference video 1 <where>; take only the motion from reference video 1, not its performer, background or any text.
```
Worked example (motion transfer, 8 s, 9:16): "The character from reference image 1 performs the exact dance moves, pace
and pauses of reference video 1 in a plain white studio; the camera stays static. Take only the motion from reference
video 1, not its performer, background or any text. Keep the character's face, hair and outfit from reference image 1.
No subtitles, captions, logos or watermarks appear anywhere in the frame."

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Unwanted typography, titles, labels | genre words, quoted strings, symbols, logo images | §3.11b |
| Intentional text misspelled | long or small text, several text events | 1–5 words, one per shot, 2K, QC; else post |
| Request rejected | frames mixed with references; T2V with `auto` [OFFICIAL] | one mode per call; `9:16` always |
| Panel layout reproduced | grid references [OFFICIAL] | standalone photos; declare storyboards |
| Wrong reference used for a role | ambiguous numbering (§3.7) | number + descriptor + explicit role |
| Source performer or overlays leak | motion clip without exclusion; Edit Mode context | "take only motion…"; QC after regeneration |
| Product recolored or reshaped | style words overriding product | "Never recolor"; geometry lock [OFFICIAL/INFERRED] |
| Timeline overrun/compression | beats exceed duration [OFFICIAL] | fit beats to 4–15 s |
| Stiff complex action | demanding performance [OFFICIAL] | simplify; consider another model |
| Unwanted music/voice | audio always on [OFFICIAL] | "Music: no background music"; strip locally |
| Draft ≠ final look | Max vs H3 are different models [INFERRED] | final check on `minimax_h3` |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space, empty openings | "Avoid fake tech decoration, mirrored white stages, and empty openings"; match the timeline to the duration [OFFICIAL] |
| Random flashes, particles, light effects | "Do not use meaningless white flashes, abstract particles, random light effects, or random cuts to fake premium motion" [OFFICIAL] |
| Unmotivated cuts / transitions | cut only for new information; transitions only when requested [OFFICIAL] |
| Arbitrary slow motion, speed jumps | "at normal real-time speed" for action; camera speed stated explicitly ("at slow speed") [OFFICIAL vocabulary / INFERRED] |
| Morphing, recoloring | geometry lock; "Never recolor the product body" [OFFICIAL/INFERRED] |
| Identity drift | stable subject labels and speaker IDs; "retains identity, hair, outfit" statements [OFFICIAL IR] |
| Duplicated objects | "only one <object> in the scene" [INFERRED] |
| Clothing changes | "keeps the same outfit in every shot" [INFERRED] |

## 6. Model-specific features and controls
- Omni-reference (≤12 files), native stereo audio, 2K via in-context regeneration, H3 Max fast 768p, `batch_size` 1–4,
  V2V motion transfer and editing (routing unverified) [OFFICIAL/HF].
- Upstream-only: Context-IR enhancer, 768p→2K regeneration task, Max `prompt_expansion_mode`, callbacks; official skill
  `h3-prompt-writing`; open weights (H3-Base only) [OFFICIAL].

## 7. Model-specific pre-generation checklist
- [ ] One mode (never frames + references); Analyze vs Edit Mode known.
- [ ] `aspect_ratio:"9:16"`; `minimax_h3` `2K` or `minimax_h3_max` `768p`; frames 9:16; `atp.py conform` to
      720×1280 afterwards (§2.6).
- [ ] Reference limits (≤9 images, ≤3 videos ≤15 s, ≤3 audio ≤15 s, ≤12 total); every reference's role stated.
- [ ] Timeline fits `duration`; `[Shot 1]` untimed, later shots "At 00:0X.XXX"; camera as a sentence.
- [ ] Sound and music sentences present.
- [ ] Clean plate: no quoted non-dialogue strings, no symbols, no text-cueing genre words, closing sentence — or one
      deliberate short text event (§3.11c).
- [ ] Product: standalone refs, "never recolor", geometry lock; identity: one person per image.
- [ ] Asset size/grip, light and end states written (§3.14); slop guards (§5); `batch_size`; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze|edit` (size, freezes, marks, text spelling), plus identity and product shape.

## 8. Sources
- [OFFICIAL] MiniMax API Docs — Video Generation (H3 / H3 Max specs, input limits) — https://platform.minimax.io/docs/guides/video-generation (accessed 2026-09-30)
- [OFFICIAL] Create Video Generation Task (V2 API reference) — https://platform.minimax.io/docs/api-reference/video-generation-v2-create (accessed 2026-09-30)
- [OFFICIAL] H3 Feature Highlights (first-party example prompts) — https://platform.minimax.io/docs/guides/video-prompt (accessed 2026-09-30)
- [OFFICIAL] Create H3-Context-IR Task — https://platform.minimax.io/docs/api-reference/video-generation-v2-h3-context-ir (accessed 2026-09-30)
- [OFFICIAL] Run and self-host MiniMax H3 (768-px short edge, 1344 × 768 canvas) — https://platform.minimax.io/docs/guides/local-deploy-h3 (accessed 2026-09-30)
- [OFFICIAL] MiniMax release notes (H3, 2026-07-31) — https://platform.minimax.io/docs/release-notes/models (accessed 2026-09-30)
- [OFFICIAL] MiniMax H3: An Open Model Breaking the Boundaries Between Tasks and Modalities (blog) — https://www.minimax.io/blog/minimax-h3 (accessed 2026-09-30)
- [OFFICIAL] MiniMaxAI/MiniMax-H3 model card — https://huggingface.co/MiniMaxAI/MiniMax-H3 (accessed 2026-09-30)
- [OFFICIAL] Video Prompt Writing Guide (T2VA / I2VA / FL2VA / L2VA) — https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md (accessed 2026-09-30)
- [OFFICIAL] Full-Reference Mode Rewrite Output Format Guide — https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md (accessed 2026-09-30)
- [OFFICIAL] MiniMax-H3 GitHub skills (h3-prompt-writing, minimalist-product-ad-generator, music-video-subtitle-generator, 3d-animation-short-generator) — https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills (accessed 2026-09-30)
- [OFFICIAL] fal (H3 Max co-developer): Introducing H3 Max by fal — https://blog.fal.ai/introducing-h3-max-by-fal/ (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json; MCP tool contract facts supplied with this task
- [SECONDARY] Artificial Analysis text-to-video / image-to-video leaderboards — https://artificialanalysis.ai/video/leaderboard/text-to-video ; https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Exact pixel sizes of 9:16 output at 2K (`minimax_h3`) and 768p (`minimax_h3_max`); 768×1344 is inferred from the
  H3-Base canvas rule.
- Whether Higgsfield's route applies H3-Context-IR or Max's prompt expansion.
- Whether Edit Mode regeneration removes overlays cleanly, and whether 2K regeneration reintroduces them.
- Reference numbering (per modality vs global); how `medias` order is forwarded; last-frame-only support.
- Credit scaling of `batch_size`; billing for reference videos.
- In-frame text accuracy beyond MiniMax's own claims (no independent measurement found).
- Quality gap between H3 Max 768p and H3 2K for identity and product detail.
