## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling3_0` | `duration` | number, 3–15 s | 5 | "Duration in seconds (3-15)." Unsupported values snap or clamp [HF S8]. |
| `kling3_0` | `mode` | `std`, `pro`, `4k` | `std` | "'std' (standard), 'pro' (higher quality), or '4k' (4K resolution)." Tiers ≈ 720p / 1080p / 4K [HF S9; SECONDARY S20]. Project: `std` (§2.6). |
| `kling3_0` | `sound` | `"on"`, `"off"` (string) | `"on"` | "Generate audio. Use 'off' for silent video and lower credits." |
| `kling3_0` | `aspect_ratio` (call-level) | `16:9`, `9:16`, `1:1` | not stated | no `auto`; project: `9:16` |
| `kling3_0` | flags | `supports_unlim: true` | — | `use_unlim:true` only on explicit user request [HF S8, S14] |
| `kling3_0_turbo` | `resolution` | `720p`, `1080p` | `720p` | "Output resolution." Project: `720p`. |
| `kling3_0_turbo` | `duration` | number, 3–15 s | 5 | "Duration in seconds (3-15)." |
| `kling3_0_turbo` | `aspect_ratio` (call-level) | `16:9`, `9:16`, `1:1` | not stated | project: `9:16` |
| `kling3_0_turbo` | audio toggle | none | — | No `sound` parameter; Kling describes Turbo as audio-included [SECONDARY S12]; ffprobe the result and strip audio locally if silence is needed. |
| both | `negative_prompt`, `cfg_scale`, `camera_control`, `multi_shot` / `shot_type` / `multi_prompt`, `element_list` / `voice_list`, watermark, seed | — | — | **Not exposed on Higgsfield** [HF S8]. Kling's API has `negative_prompt`, `cfg_scale` (0–1, default 0.5), multi-shot (up to 6 shots with per-shot durations), elements and first/end-frame `image_list` [SECONDARY S10, S11]. Approximations: exclusions in prose (§3.10), explicit wording instead of cfg, camera moves in words (§3.6), one clip per shot (§3.5), Elements tokens (§3.7). |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing), `use_unlim` [HF S8].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (both ids) | first frame: composition, identity, product, scene, and any text in it | 1; jpg/jpeg/png, ≥300 px, ≤10 MB [OFFICIAL S3]; aspect 1:2.5–2.5:1 [SECONDARY S10] | text in the frame is preserved (§3.11) |
| `end_image` (`kling3_0`) | last frame | 1, with `start_image` | "Generation with only an end frame is not supported" (O1) [OFFICIAL S3]; Higgsfield copy suggests end-frame-only use [HF S17] — don't rely on it |
| Elements `<<<element_id>>>` (prompt token, `kling3_0`) | reusable identity or product reference | Kling builds elements from 2–4 reference images or a short video [OFFICIAL S1] | "the backend injects the image and rewrites it to @element_name" [HF S8] |

`medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF S8].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration** 3–15 s on both ids [HF S8; OFFICIAL S1].
- **Resolution** `kling3_0`: std / pro / 4k ≈ 720p / 1080p / 4K [HF S9]; Kling's 3.0 guide prices 720p and 1080p tiers and its blog a separate 4K mode [OFFICIAL S1, S6]. Turbo: 720p or 1080p [HF S8].
- **Aspect ratio** 16:9, 9:16, 1:1 [HF S8].
- **Audio** `kling3_0`: `sound:"on"` gives dialogue, SFX and ambience in the same pass — "micro-sounds, environmental textures, and timing cues that match physical interaction on screen" [HF S9]. Dialogue languages: Chinese, English, Japanese, Korean, Spanish; other languages are translated into English [OFFICIAL S1].

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight.

**Text-to-video (silent)**
```json
{"model":"kling3_0","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","mode":"std","sound":"off"}
```
**Text-to-video with native audio**
```json
{"model":"kling3_0","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Start frame** (exactly-9:16 image)
```json
{"model":"kling3_0","prompt":"<PROMPT describing change from the frame>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Start + end frame**
```json
{"model":"kling3_0","prompt":"<PROMPT describing the transition>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"aspect_ratio":"9:16","mode":"std","sound":"off"}
```
**Elements (identity + product), optionally with a start frame** — Kling supports "Start Frame + Element Reference" [OFFICIAL S1]; the combination through Higgsfield is unverified [INFERRED].
```json
{"model":"kling3_0","prompt":"<<<ELEMENT_ID_PERSON>>> picks up <<<ELEMENT_ID_PRODUCT>>> from the counter ...","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Turbo (text or start frame)**
```json
{"model":"kling3_0_turbo","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":5,"aspect_ratio":"9:16","resolution":"720p"}
```
**Legacy Kling 3.0 Motion Control** — separate MCP tool, not `generate_video`; no prompt; 9:16 character image and 9:16 motion clip. Confirm argument names against the live schema (`ToolSearch select:mcp__higgsfield__motion_control`) [HF S8].
```json
{"image_id":"<IMAGE_MEDIA_ID>","motion_video_id":"<VIDEO_MEDIA_ID>","resolution":"720p","scene_control":"video"}
```

### 2.5 Parameter gotchas

- `sound` is a **string** on `kling3_0`, a boolean on `kling2_6`, `generate_audio` on Seedance; Turbo has no audio toggle [HF S8].
- `mode` is a quality/resolution tier, not a task selector; drafting in `4k` is listed as a common mistake [HF S9].
- No `auto` ratio [HF S8]; supply start/end frames at exactly 9:16.
- Multi-shot keys are not in the MCP catalog, and Kling states "When 'Multi-Shot' is disabled, the model will default to generating a single-shot video" [OFFICIAL S1]. Don't send undocumented multi-shot keys unless `models_explore` lists them.
- Elements are documented for `kling3_0`, not Turbo [HF S8].
- Motion transfer: Higgsfield routes Genjutsu motion transfer to `hf_mult_motion_control` and says never to use legacy `motion_control` for a Genjutsu edit [HF S8]; use `motion_control` only when the user picks Kling 3.0 Motion Control.
- Prompt length: Kling's API caps prompts at 2,500 characters [SECONDARY S10, S11].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id / operation | params to send | expected output | post-processing |
|---|---|---|---|
| `kling3_0` t2v / Elements | `aspect_ratio:"9:16"`, `mode:"std"` | 720p tier [HF S9; SECONDARY S20] → 720×1280 expected [INFERRED] | ffprobe; if not 720×1280, `atp.py conform` (downscale, or scale-to-fill + minimal crop); never stretch |
| `kling3_0` start / end frame | same + exactly-9:16 frame(s) | 720×1280 expected [INFERRED] | conform frames to 9:16 before upload; verify output |
| `kling3_0_turbo` | `aspect_ratio:"9:16"`, `resolution:"720p"` | 720×1280 expected [INFERRED] | ffprobe; conform if needed |
| `motion_control` | `resolution:"720p"`, 9:16 image and 9:16 motion clip | aspect follows the image or the motion clip depending on `scene_control`/orientation [HF S15; OFFICIAL S18] | reframe both inputs to 9:16 first; verify output |

`pro` (≈1080p) followed by a deterministic downscale is possible but is not the project default [INFERRED].

