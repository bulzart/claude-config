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

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| case | params to send | expected output | post-processing |
|---|---|---|---|
| `sound:true` | `aspect_ratio:"9:16"`, no resolution parameter | likely the 1080p tier → ~1080×1920: Kling prices native audio at a single rate (silent output has Professional and Standard rates) [OFFICIAL S1], third-party docs say native audio requires Pro/1080p [SECONDARY S12], Higgsfield lists 1080p max [HF S4] | ffprobe; deterministic downscale to 720×1280 with `atp.py conform` |
| `sound:false` | `aspect_ratio:"9:16"` | 720p or 1080p tier — unknown which Higgsfield uses [INFERRED] | ffprobe; downscale or scale-to-fill + minimal crop to 720×1280; never stretch |
| start frame | same + exactly-9:16 image | as above | conform the image to 9:16 before upload |

Native 720×1280 output cannot be guaranteed on this id; conformance is always a post step [INFERRED].

