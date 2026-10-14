## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `grok_video` | `duration` | 1–15 (s) | 5 | xAI range 1–15; xAI default 8 [OFFICIAL] |
| `grok_video` | `aspect_ratio` | `16:9`, `9:16`, `1:1` | not stated | With a start image, a different ratio **stretches** the image [OFFICIAL]. Always `9:16` here, with a 9:16 frame |
| `grok_video` | resolution | not exposed | — | xAI API default is 480p; 720p available [OFFICIAL]. The resolution Higgsfield delivers is unknown |
| `grok_video_v15` | `resolution` | `480p`, `720p`, `1080p` | `720p` | Always `720p` here. "Reference-to-video is capped at 720p" [OFFICIAL]; Higgsfield rejects 1080p in reference mode [HF] |
| `grok_video_v15` | `duration` | 2–15 (s) | 5 | Higgsfield REST: 1–15, default 5 [HF] |
| `grok_video_v15` | `aspect_ratio` | **none in the MCP catalog** | — | Higgsfield's REST schema has `aspect_ratio` (`auto` default; `9:16` allowed) [HF]. MCP pass-through is unverified |
| both | audio switch, negative prompt, seed | not exposed | — | xAI has `generate_audio` (default on) [OFFICIAL] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (both ids) | "the provided image as the starting frame" [OFFICIAL] | 1 | JPEG/PNG/WebP (Higgsfield also lists GIF) [OFFICIAL][HF]. Output "defaults to the input image's aspect ratio" [OFFICIAL] |
| `image_references` (1.5 only) | People, objects, clothing or visual elements "without locking the first frame" [OFFICIAL] | ≤7 [OFFICIAL][HF] | Tags `<IMAGE_0>`… in list order [OFFICIAL]. Higgsfield: "Choose either image_url or reference media (image_urls/audio_url); do not combine these modes" [HF] |
| `audio_references` (1.5 only) | Voice identity (`<AUDIO_0>`) [OFFICIAL] | xAI ≤3; Higgsfield REST takes a single `audio_url` [HF] | Caller clips ≤15 s. xAI GA covers preset voices; own-audio references are for "trusted partners, on request" [OFFICIAL]. Acceptance on Higgsfield is unverified |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 1–15 s (classic) and 2–15 s (1.5) on Higgsfield [HF]. Pick the shortest duration that holds the action (§5).
- **Resolution:** 1.5 offers 480p/720p/1080p, with references capped at 720p [OFFICIAL][HF]. Classic has no control [HF].
- **Aspect ratio:** xAI supports 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 [OFFICIAL]. Image-to-video follows the image unless `aspect_ratio` forces a different ratio, which stretches it [OFFICIAL].
- **Audio:** "Generated videos include an audio track by default" [OFFICIAL]. There is no switch on Higgsfield; strip the track locally for silence [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video (`grok_video`):
```json
{"model":"grok_video","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16"}
```
Start frame → video (`grok_video`; the frame is exactly 9:16):
```json
{"model":"grok_video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":10,"aspect_ratio":"9:16"}
```
Start frame → video (`grok_video_v15`; the 9:16 frame sets the ratio):
```json
{"model":"grok_video_v15","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":10,"resolution":"720p"}
```
"Text-to-video" on 1.5 in the fixed format: first generate a 9:16 still (image job), then animate it:
```json
{"model":"grok_video_v15","prompt":"<MOTION_PROMPT>","medias":[{"value":"<JOB_ID>","role":"start_image"}],"duration":8,"resolution":"720p"}
```
Reference mode (`grok_video_v15`; **probe first**, since 9:16 is not guaranteed; no `start_image`):
```json
{"model":"grok_video_v15","prompt":"<REFERENCE_PROMPT using <IMAGE_0>, <IMAGE_1>, <AUDIO_0>>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":8,"resolution":"720p"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Stretching.** A requested ratio that differs from the start image deforms products and faces [OFFICIAL]. Conform every start image to exactly 9:16 locally (scale-to-fill plus minimal crop; never stretch) [INFERRED].
2. **No first frame in reference mode** on Higgsfield [HF], so reference jobs cannot inherit 9:16 from a frame.
3. **Reference cap.** Any reference means ≤720p; 1080p is rejected [OFFICIAL][HF].
4. **Tag numbering.** xAI shifts reference tags by one when a first frame is set [OFFICIAL]. On Higgsfield the two modes cannot be combined, so references start at `<IMAGE_0>` [HF + INFERRED].
5. **Audio references.** Custom voice audio is gated at xAI [OFFICIAL]. Test acceptance, and have a described-voice fallback [INFERRED].
6. **Prompt length.** xAI fails "a prompt that is too long" without publishing the limit [OFFICIAL]. Stay under ~150 words [INFERRED].
7. **Always-on audio.** Every written line will be voiced [INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `grok_video` | `"aspect_ratio":"9:16"`; no resolution parameter | Unknown. xAI's API defaults to 480p [OFFICIAL]; the Higgsfield tier is unpublished. 720×1280 or about 480×854 [INFERRED] | 720×1280: none. 480p: `atp.py conform` scale-to-fill up to 720×1280 plus minimal crop; this upscale loses detail, so prefer `grok_video_v15` when quality matters | Start image conformed to exactly 9:16, plus `aspect_ratio: "9:16"`. The two must match, or the image is stretched [OFFICIAL] |
| `grok_video_v15` | `"resolution":"720p"` plus a **mandatory 9:16 `start_image`** (no aspect parameter in the catalog) | Follows the start image's ratio [OFFICIAL]: 720×1280 expected [INFERRED] | Conform only if the dimensions differ | The 9:16 start frame. For "text-to-video", create the 9:16 still first. Reference mode cannot carry a frame [HF], so it is excluded from the fixed format unless a probe (optionally adding the REST-documented `"aspect_ratio":"9:16"` [HF]) returns 720×1280 |

