## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `seedance_2_0` | `duration` | number, 4–15 s | 5 | "Duration in seconds (4-15)." Unsupported values snap or clamp [HF S8]. |
| `seedance_2_0` | `resolution` | `480p`, `720p`, `1080p`, `4k` | `720p` | "Output resolution supported by standard mode." Project: `720p` (§2.6). |
| `seedance_2_0` | `mode` | `std` | `std` | "Standard mode is available for this account." Quality tier, not a task selector. |
| `seedance_2_0` | `bitrate_mode` | `standard`, `high` | `standard` | "'high' = higher bitrate output." Higgsfield-specific. |
| `seedance_2_0` | `genre` | `auto`, `action`, `horror`, `comedy`, `noir`, `drama`, `epic` | `auto` | "Cinematic genre hint." Higgsfield-specific, mechanism undocumented — keep `auto` unless the look is wanted and matches the prompt [INFERRED]. |
| `seedance_2_0` | `generate_audio` | bool | `true` | "Generate native audio for the video. Set false for a silent video. Independent of audio_references." |
| `seedance_2_0` | `aspect_ratio` (call-level) | `auto`, `16:9`, `9:16`, `4:3`, `3:4`, `1:1`, `21:9` | not stated | Project: `9:16`. |
| `seedance_2_0` | flags | `supports_unlim: true` | — | `use_unlim:true` only when the user explicitly asks [HF S6, S10] |
| `seedance_2_0` | `seed`, `negative_prompt`, `camera_fixed`, `watermark`, edit/extension selection, `duration:-1` | — | — | **Not exposed on Higgsfield** [HF S6]; ModelArk lists `seed`/`camera_fixed` for 1.x only [OFFICIAL S7]. Approximations: §3.6, §3.10. |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing), `use_unlim` [HF S8].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame | 1 | ModelArk `first_frame` [OFFICIAL S7] |
| `end_image` | last frame | 1, with `start_image` | same ratio as the first frame [OFFICIAL S7] |
| `image_references` | `@Image1…9`: identity, wardrobe, product, scene, style, logo | ≤9 [OFFICIAL S1, S7]; each <30 MB, 300–6000 px, w/h 0.4–2.5 [OFFICIAL S7] | numbered in `medias` order |
| `video_references` | `@Video1…3`: action, camera movement, rhythm, effects, style | ≤3, each 2–15 s, total ≤15 s [OFFICIAL S7] | |
| `audio_references` | `@Audio1…3`: timbre, music, SFX, beat | ≤3, each 2–15 s, total ≤15 s [OFFICIAL S7] | "Audio-only input is not supported; include at least one reference image or video" [OFFICIAL S7] |

Higgsfield states "up to 12 assets in a single generation" [HF S11] versus ByteDance's 9 + 3 + 3 [OFFICIAL S1]; treat 12 as the cap until tested. ModelArk forbids mixing first/last-frame roles with omni references [OFFICIAL S7]; Higgsfield behaviour undocumented. `medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S8].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration** 4–15 s; 24 fps [OFFICIAL S7, S9].
- **Resolution** 480p/720p/1080p (8-bit), 4K (10-bit HEVC on ModelArk) [OFFICIAL S9]; the model card describes 480p/720p native generation [OFFICIAL S4].
- **Aspect ratio:** six fixed output ratios (2.5 added arbitrary ratios) [OFFICIAL S5]; with a first frame, 2.0 accepts a specified ratio and centre-crops the image if it differs [OFFICIAL S7].
- **Audio:** native voice, SFX and music in one pass; ByteDance describes it as dual-channel [OFFICIAL S1], the ModelArk API returns mono [OFFICIAL S7]. `generate_audio:false` for silence.

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight without submitting [HF S8].

**Text-to-video**
```json
{"model":"seedance_2_0","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","resolution":"720p","mode":"std","genre":"auto","generate_audio":true}
```
**First frame (+ last frame)** — exactly-9:16 images
```json
{"model":"seedance_2_0","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**Multi-reference (headshot + full body + product + camera clip + voice)**
```json
{"model":"seedance_2_0","prompt":"<PROMPT citing @Image1 @Image2 @Image3 @Video1 @Audio1>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_3>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID_1>","role":"video_references"},{"value":"<AUDIO_MEDIA_ID_1>","role":"audio_references"}],"duration":12,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
**Elements** (Higgsfield injects the Element image and rewrites the token to `@element_name`) [HF S8]
```json
{"model":"seedance_2_0","prompt":"<<<ELEMENT_ID_PERSON>>> lifts <<<ELEMENT_ID_PRODUCT>>> from the table ...","duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```

### 2.5 Parameter gotchas

- No task `mode` for edit/extension; `mode:"std"` is a quality tier [HF S6]. ModelArk 2.0 infers edit/extension from prompt intent when a reference video is present [OFFICIAL S3, S7]; whether an "Edit @Video1…" prompt behaves as an edit through Higgsfield is untested — use `seedance_2_5`.
- `genre` is not a ByteDance parameter [HF S6]; don't let it contradict the prompt's look.
- `generate_audio` is independent of `audio_references` [HF S6]; audio references need an image or video in the same call [OFFICIAL S7].
- Real-face references are restricted on ModelArk's Dreamina Seedance models [OFFICIAL S12]; Higgsfield's treatment is undocumented.
- Keep ratio, duration, resolution and the sound toggle out of the prompt [OFFICIAL S7].
- Elements vs `@ImageN`: numbering of injected Element images relative to attached references is undocumented; use one mechanism per call until tested [INFERRED].
- Prompt length: ≤1,000 English words ("Lengthy text will lead to scattered information") [OFFICIAL S7]; Dreamina suggests 30–100 words for simple clips [OFFICIAL S13].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| operation | params to send | expected output | post-processing |
|---|---|---|---|
| t2v / multi-reference / Elements | `aspect_ratio:"9:16"`, `resolution:"720p"`, `mode:"std"` | 720×1280 (official 2.0 grid) [OFFICIAL S7] | none; verify with ffprobe |
| first / last frame | `aspect_ratio:"9:16"`, `resolution:"720p"`, exactly-9:16 image(s) (720×1280 or 1080×1920) | 720×1280; a non-9:16 image would be centre-cropped by the model [OFFICIAL S7] | conform images to 9:16 **before** upload (`atp.py conform`: scale-to-fill + minimal crop) so framing is chosen deliberately |

Never stretch. `1080p`/`4k` are not used by this project.

