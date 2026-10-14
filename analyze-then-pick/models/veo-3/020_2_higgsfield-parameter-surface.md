## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `veo3` | `variant` | `veo-3-preview`, `veo-3-fast` | `veo-3-fast` | "'veo-3-preview' = best quality; 'veo-3-fast' = faster generation" [HF] |
| `veo3` | `aspect_ratio` | `16:9`, `9:16` | not stated | Always `9:16` here |
| `veo3` | `prompt` | string | — | 1,024-token limit [OFFICIAL] |
| `veo3` | duration | not exposed | — | Google docs disagree for Veo 3: the Gemini API says "8 seconds"; the Agent Platform and the 2025-10-15 changelog say 4/6/8 [OFFICIAL]. Expect 8 s [INFERRED] |
| `veo3` | resolution, negative prompt, seed, sample count | not exposed | — | Google has `negativePrompt` and `seed` for Veo 3 [OFFICIAL]; Higgsfield does not [HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | Initial frame of the video [OFFICIAL] | 1 | ≥720p; 16:9/9:16 recommended; other ratios "may be resized or centrally cropped" [OFFICIAL]; JPEG/PNG, ≤20 MB [OFFICIAL] |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced when unambiguous [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** not selectable; plan for 8 s and measure the output [INFERRED].
- **Resolution:** Gemini API: "720p & 1080p (16:9 only)". Agent Platform: 720p/1080p [OFFICIAL]. Portrait is therefore 720p upstream [OFFICIAL + INFERRED].
- **Frame rate:** 24 fps [OFFICIAL].
- **Audio:** "Always on" [OFFICIAL]. There is no flag on Higgsfield; strip locally for silence [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6). Never send `duration`: the catalog defines none for `veo3` [HF].

Text-to-video (draft):
```json
{"model":"veo3","prompt":"<PROMPT>","aspect_ratio":"9:16","variant":"veo-3-fast"}
```
Start frame → video (quality variant; the start frame is already 9:16):
```json
{"model":"veo3","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"aspect_ratio":"9:16","variant":"veo-3-preview"}
```
Start frame from a completed Higgsfield image job:
```json
{"model":"veo3","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"aspect_ratio":"9:16","variant":"veo-3-fast"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Legacy backend.** Upstream endpoints are shut down [OFFICIAL]. If outputs show traits of another model (4k, other lengths, no audio), record it and switch to `veo3_1` [INFERRED].
2. **Start frame must be 9:16.** Google may center-crop other ratios [OFFICIAL]. Conform locally first [INFERRED].
3. **No duration control.** Size the action for about 8 s [INFERRED].
4. **Audio cannot be switched off.** Written dialogue will be voiced [OFFICIAL + INFERRED].
5. **People in start frames.** "allow_adult" only. Child and prominent-person content is rejected [OFFICIAL].
6. **No negative prompt.** Put exclusions in the prompt (§3.10) [HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `veo3` | `"aspect_ratio":"9:16"`, `variant` of choice. There is no resolution parameter | 720×1280 expected. Google lists Veo 3's 1080p as "16:9 only", so portrait is 720p [OFFICIAL + INFERRED]. DeepMind evaluated Veo portrait "at 720x1280 resolution" [OFFICIAL] | None if 720×1280. Otherwise `atp.py conform` (exact downscale, or scale-to-fill plus minimal crop; never stretch) | Native 9:16 request. Any start frame is reframed to 9:16 before upload |

ffprobe the first output of a session. The legacy backend makes this mandatory [INFERRED].

