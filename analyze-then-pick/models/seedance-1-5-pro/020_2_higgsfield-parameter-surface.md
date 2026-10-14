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

