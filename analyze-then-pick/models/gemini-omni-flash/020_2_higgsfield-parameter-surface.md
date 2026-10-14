## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `gemini_omni` | `duration` | 4–10 (s) | 8 | Google allows 3–10 [OFFICIAL] |
| `gemini_omni` | `resolution` | `720p` | `720p` | Only option [HF][OFFICIAL] |
| `gemini_omni` | `aspect_ratio` | `16:9`, `9:16` | not stated | If unset, Google infers it from the prompt [OFFICIAL]. Always `9:16` here |
| `gemini_omni_flash_1_1` | `mode` | `text-to-video`, `image-to-video`, `reference-to-video`, `edit` | **required** | Google: "using the task field adds some constraints" [OFFICIAL] |
| `gemini_omni_flash_1_1` | `duration` | 3–10 (s) | 8 | "Ignored in edit mode, which uses the source video duration capped at 30 seconds" [HF] |
| `gemini_omni_flash_1_1` | `resolution` | `360p`, `720p`, `1080p`, `4k` | `720p` | "1080p and 4K outputs are generated using upscaling" [OFFICIAL]. Always `720p` here |
| `gemini_omni_flash_1_1` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` |
| both | negative prompt, seed, temperature, audio toggle | not exposed | — | Google supports none of the first three for Omni: "put your negatives in the regular prompt: e.g., 'Do not do X'" [OFFICIAL] |

`gemini_omni` supports Higgsfield unlimited generations (`supports_unlim: true`). Send `use_unlim` only on the user's explicit request [HF].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (1.1 only) | First frame, `<FIRST_FRAME>` [OFFICIAL] | 1 | `mode:"image-to-video"` |
| `end_image` (1.1 only) | Last frame, `<LAST_FRAME>`: "Must be used with <FIRST_FRAME>" [OFFICIAL] | 1 | "image_to_video task with up to 2 images" [OFFICIAL] |
| `image_references` (both ids) | Subject, object, style or environment references (`<IMAGE_REF_N>`) [OFFICIAL] | Google up to 10 per prompt [OFFICIAL]; Higgsfield "up to 7" [HF] | Use ≤7. PNG/JPEG/WebP/HEIC/HEIF, ≤20 MB [OFFICIAL] |
| `video_references` (both ids) | Reference clips (`<VIDEO_REF_N>`) in reference mode; the **source clip** in edit mode [OFFICIAL][INFERRED] | Reference: "maximum of 3 clips, up to 3 seconds each"; their audio "is ignored" [OFFICIAL]. Edit source: uploads "must be 10 seconds or less" [OFFICIAL]; Higgsfield caps at 30 s [HF] | Exactly one video in edit mode |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 3–10 s on 1.1, 4–10 s on 1.0 [HF]. Flow offers 4/6/8/10 s [OFFICIAL]. Out-of-range values snap or clamp [HF].
- **Resolution:** 720p is native. 1080p/4k are upscales; 360p is a cheaper draft tier [OFFICIAL]. The fixed format uses 720p only.
- **Aspect ratio:** 16:9 or 9:16 [OFFICIAL][HF].
- **Audio:** always generated; the model "will try to generate an appropriate audio track" [OFFICIAL]. To shape it, describe it. For silence, strip the track locally. Voice editing is unsupported, and speech-changing in edits is restricted [OFFICIAL].

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"text-to-video","prompt":"<PROMPT>","duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Start frame → video (1.1; the start frame is already 9:16):
```json
{"model":"gemini_omni_flash_1_1","mode":"image-to-video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"resolution":"720p","aspect_ratio":"9:16"}
```
First + last frame (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"image-to-video","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Reference-to-video (1.1):
```json
{"model":"gemini_omni_flash_1_1","mode":"reference-to-video","prompt":"<REFERENCE_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Edit Mode (1.1; the source is pre-conformed to 9:16 and ≤10 s; `duration` is ignored):
```json
{"model":"gemini_omni_flash_1_1","mode":"edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID>","role":"image_references"}],"resolution":"720p","aspect_ratio":"9:16"}
```
Edit Mode or references (`gemini_omni`; the prompt states the job explicitly):
```json
{"model":"gemini_omni","prompt":"<PROMPT WITH EXPLICIT ROLE SENTENCE>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16"}
```
Preflight with the same params plus `get_cost: true` [HF]. A completed job ID can be passed back as `video_references` for a second edit pass [HF][INFERRED].

### 2.5 Parameter gotchas

1. **Edit-source length conflict.** Google: uploaded edit inputs ≤10 s; the Agent Platform model page lists 10 s maximum; Flow edits "Up to 10s" [OFFICIAL]. Higgsfield: capped at 30 s [HF]. Trim to ≤10 s locally, and edit longer clips in ≤10 s segments at cut points [INFERRED].
2. **`mode` constrains the model** [OFFICIAL]. Match it to the media you send [INFERRED].
3. **Multiple videos.** Google lists both "maximum of 3 clips" and "Referencing or reasoning across multiple videos is not supported" [OFFICIAL]. Send one video when possible.
4. **Stateless calls.** There is no `previous_interaction_id` memory on Higgsfield, so drift compounds across chained edits. Keep chains short [INFERRED].
5. **Restrictions.** No "certain recognizable people". Minors and uploaded-video edits are restricted in the EEA, CH and UK [OFFICIAL].
6. **Deprecated 1.0 endpoint** (see §1).

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `gemini_omni` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` | Native 720p [OFFICIAL]. Pixel size 720×1280 expected but undocumented [INFERRED] | None if 720×1280; otherwise `atp.py conform` (downscale, or scale-to-fill plus minimal crop; never stretch) | Edit: reframe the source to 9:16 (720×1280) with `atp.py conform` before upload. References can be any ratio, but keep subjects uncropped |
| `gemini_omni_flash_1_1` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` (never 360p/1080p/4k) | Native 720p; 1080p/4k would only be upscales [OFFICIAL]. 720×1280 expected [INFERRED] | Same rule | `image-to-video`: start and end frames conformed to 9:16. `edit`: source conformed to 9:16 and still send `"9:16"`. The output likely follows the source [INFERRED] |

ffprobe the first output per session and log the dimensions [INFERRED].

