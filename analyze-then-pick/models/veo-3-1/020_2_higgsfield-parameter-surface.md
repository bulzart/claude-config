## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `veo3_1` | `duration` | 4, 6, 8 | 8 | Seconds. An unsupported value snaps to the nearest allowed value or is clamped [HF] |
| `veo3_1` | `quality` | `basic`, `high`, `ultra` | `basic` | "Output quality tier" [HF]; resolution mapping unpublished (§2.6) |
| `veo3_1` | `variant` | `veo-3-1-preview`, `veo-3-1-fast` | `veo-3-1-fast` | "preview = best quality, fast = faster generation" [HF] |
| `veo3_1` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` here |
| `veo3_1_lite` | `duration` | 4, 6, 8 | 8 | Same snapping rule [HF] |
| `veo3_1_lite` | `generate_audio` | bool | **false** | Silent unless set to true [HF] |
| `veo3_1_lite` | `aspect_ratio` | `16:9`, `9:16`, `auto` | not stated | Always `9:16` here (not `auto`) |
| both | `prompt` | string | — | Google text limit: 1,024 tokens [OFFICIAL] |
| both | negative prompt, seed, resolution, sample count, person-generation, resize mode | not exposed | — | [HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (`veo3_1`, `veo3_1_lite`) | "Veo uses the input image as the initial frame" [OFFICIAL] | 1 | Google recommends ≥720p at 16:9 or 9:16. Other ratios "may be resized or centrally cropped" [OFFICIAL]. JPEG/PNG, ≤20 MB [OFFICIAL] |
| `end_image` (`veo3_1_lite` only) | Final frame (Google `lastFrame`, "must be used in combination with the image parameter") [OFFICIAL] | 1 | Always pair with `start_image` |

Values are Higgsfield media UUIDs or completed job IDs, never URLs. The server may auto-coerce unambiguous roles [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 4, 6 or 8 s [HF][OFFICIAL]. Google requires 8 s for 1080p, 4k and reference images [OFFICIAL]; that does not constrain 720p work.
- **Resolution:** Veo 3.1 offers 720p/1080p/4k. Lite has no 4k [OFFICIAL]. The Agent Platform lists Fast at 720p/1080p, while the Gemini API lists 4k for "Veo 3.1 & Veo 3.1 Fast" [OFFICIAL, conflicting]. On Higgsfield, resolution is reachable only via `quality` (`veo3_1`); Lite has no control [HF].
- **Frame rate:** 24 fps [OFFICIAL].
- **Aspect ratio:** 16:9 or 9:16; portrait is native [OFFICIAL].
- **Audio:** "Always on" for all Veo 3.x on the Gemini API [OFFICIAL]. `veo3_1` has no flag, so expect sound every time [INFERRED]. Lite: `generate_audio` (default false) [HF].

### 2.4 Call recipes

All recipes use the fixed output format (§2.6).

Text-to-video (`veo3_1`, draft):
```json
{"model":"veo3_1","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","quality":"basic","variant":"veo-3-1-fast"}
```
Start frame → video (`veo3_1`, final pass; the start frame is already 9:16):
```json
{"model":"veo3_1","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","quality":"basic","variant":"veo-3-1-preview"}
```
Text-to-video with sound (`veo3_1_lite`):
```json
{"model":"veo3_1_lite","prompt":"<PROMPT>","duration":6,"aspect_ratio":"9:16","generate_audio":true}
```
Start frame → video, silent (`veo3_1_lite`; a completed image job can be the frame):
```json
{"model":"veo3_1_lite","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","generate_audio":false}
```
First + last frame (`veo3_1_lite`):
```json
{"model":"veo3_1_lite","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","generate_audio":false}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`. `jobs_wait` returns public MP4 URLs [HF].

### 2.5 Parameter gotchas

1. **Pre-shape start and end frames** to exactly 9:16 (at least 720×1280) with `atp.py conform` before upload. Google may center-crop or resize other ratios [OFFICIAL]. Keep the subject inside the central safe area [INFERRED].
2. **Never send `high` or `ultra` in the fixed format.** They likely map to higher resolutions, which cost more and may force 8 s [OFFICIAL coupling + INFERRED].
3. **`veo3_1` always has audio.** For silence, strip it locally (`ffmpeg -an`) [INFERRED]. Lite is silent unless `generate_audio: true` [HF].
4. **No negative prompt.** Put exclusions in the prompt (§3.10) [HF].
5. **People in frames.** Image-to-video and interpolation are "allow_adult" only. Child and prominent-person content is rejected [OFFICIAL]. Use adult, non-famous approved references only.
6. **Audio-triggered blocks.** "Veo 3.1 will sometimes block a video from generating because of safety filters or other processing issues with the audio" [OFFICIAL]. Higgsfield billing for blocked jobs is undocumented.
7. **Web app ≠ MCP.** Higgsfield's web app advertises Veo 3.1 references, start/end frames and multi-shot [HF blog]. The MCP catalog exposes only §2.2 [HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `veo3_1` | `"aspect_ratio":"9:16"`, `"quality":"basic"`. `variant`: `veo-3-1-fast` for drafts, `veo-3-1-preview` for finals | 720×1280 expected [INFERRED]. `basic` is the lowest tier and 720p is Google's default. DeepMind ran its Veo evaluations "at 720x1280 resolution" [OFFICIAL] | None if 720×1280. If larger (e.g. 1080×1920), exact downscale with `atp.py conform` | Native 9:16 request. Any start frame is reframed to 9:16 first (scale-to-fill plus minimal crop; never stretch) |
| `veo3_1_lite` | `"aspect_ratio":"9:16"` (never `auto`). No resolution parameter | 720×1280 expected: Lite supports 720p/1080p, and 720p is the default [OFFICIAL + INFERRED] | Same rule | 9:16 start and end frames, both from the same source |

Always ffprobe the first output of a session. Record the dimensions in run notes and conform if they are not 720×1280 [INFERRED].

