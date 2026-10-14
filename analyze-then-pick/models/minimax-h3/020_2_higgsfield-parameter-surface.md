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

