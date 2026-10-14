## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `wan2_7` | `duration` | number, min 2, max 15 | 5 | "Duration in seconds (2-15)." [HF]; upstream integers 2–15, billed per second [OFFICIAL] |
| `wan2_7` | `resolution` | `720p`, `1080p` | `720p` | always `720p` under the fixed format (§2.6); upstream default 1080P [OFFICIAL] |
| `wan2_7` | `aspect_ratio` | `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | — | always `9:16`; honoured for text-only calls, ignored with a start frame (output follows the image) [OFFICIAL/INFERRED] |
| `wan2_7` | catalog flag | `supports_unlim: true` | — | unlimited-plan eligibility; not available on the capture account (`unlim.available:false`) [HF] |
| `wan2_7` | negative_prompt, seed, prompt_extend, watermark, generate_audio | — | — | not exposed on Higgsfield [HF]; see §2.5, §3.10, §3.11 |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | exact first frame (upstream `first_frame`) | 1; JPEG/PNG (no alpha)/BMP/WEBP, 240–8000 px, aspect 1:8–8:1, ≤20 MB [OFFICIAL] | required for every image-to-video combination [OFFICIAL]; must be 9:16 (§2.6) |
| `end_image` | exact last frame (upstream `last_frame`) | 1; only with `start_image` [OFFICIAL] | same limits; same size as the start frame [INFERRED] |
| `audio_references` | soundtrack that drives lip sync and action timing (upstream `driving_audio` / `audio_url`) | 1 file ("a maximum of one audio file"); wav/mp3, 2–30 s, ≤15 MB [OFFICIAL] | truncated to `duration`; if shorter, the rest of the video is silent [OFFICIAL] |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- **Duration** 2–15 s, 30 fps [OFFICIAL]; unsupported values are snapped/clamped [HF contract].
- **Resolution/aspect:** fixed 720p, 9:16 (§2.6). Text-to-video uses the requested ratio (720P 9:16 = 720×1280)
  [OFFICIAL]. Image-to-video: "The API does not currently support setting the aspect ratio directly… The model
  preserves the approximate original aspect ratio of the input first frame", scaling to the tier's pixel count with
  sides in multiples of 16 [OFFICIAL].
- **Audio is always produced:** without an audio input "the model automatically generates matching background
  music or sound effects" [OFFICIAL]; with one, it drives the video [OFFICIAL]. No silent switch on Higgsfield [HF];
  strip audio locally if a silent file is required [INFERRED].

### 2.4 Call recipes
Text-to-video:
```json
{"model":"wan2_7","prompt":"<PROMPT>","duration":8,"aspect_ratio":"9:16","resolution":"720p"}
```
Text + driving audio (duration ≈ audio length):
```json
{"model":"wan2_7","prompt":"<PROMPT describing who speaks/sings or moves to the audio>","medias":[{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":10,"aspect_ratio":"9:16","resolution":"720p"}
```
First frame → video (9:16 start image):
```json
{"model":"wan2_7","prompt":"<MOTION + CAMERA PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
First frame + driving audio (lip sync / action timing):
```json
{"model":"wan2_7","prompt":"<WHO SPEAKS, GESTURES, CAMERA>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
First + last frame → video (both 9:16, identical size):
```json
{"model":"wan2_7","prompt":"<PATH PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
A `<JOB_ID>` of a completed Higgsfield image job can be the `value` [HF]. Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. **`end_image` needs `start_image`.** Valid upstream combinations: first frame; first frame + audio; first + last
   frame; first + last frame + audio (plus two continuation combos not exposed here) [OFFICIAL].
2. **`aspect_ratio` does nothing with a start frame** [OFFICIAL FAQ] — a non-9:16 start frame yields a non-9:16 video.
3. **One audio file maximum;** longer audio is cut at `duration`, shorter audio leaves silence [OFFICIAL].
4. **No silent mode, negative prompt or seed** on Higgsfield [HF]. Upstream `prompt_extend` (LLM rewriting, default
   `true`) is not exposed → assume your prompt may be rewritten [OFFICIAL/INFERRED].
5. **`shot_type` no longer exists:** "Control shot structure with natural language in the prompt. The shot_type
   parameter has no effect." [OFFICIAL]
6. **Snapshot ambiguity:** which dated snapshot Higgsfield calls is undocumented [HF silent].
7. **Prompt limit** 5,000 characters, auto-truncated [OFFICIAL].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| mode | params | expected output | action |
|---|---|---|---|
| Text-to-video (± audio) | `"aspect_ratio":"9:16","resolution":"720p"` | 720×1280, 30 fps [OFFICIAL size table] | verify |
| Start frame (± end frame, ± audio) | same params (ratio ignored upstream) + a **9:16 start frame**, end frame of identical size | follows the frame's aspect at ≈720P pixel count with sides in multiples of 16 → 720×1280 for an exact 9:16 frame [OFFICIAL rules → INFERRED] | verify |

Require 9:16 frames (e.g. 1080×1920 or 720×1280) — crop or regenerate the still before upload; never rely on
`aspect_ratio` in frame mode. Finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to
exactly 720×1280, never stretched; a no-op when already exact). Expected loss ~0%; `conform` refuses losses above
12% — that means the frame ratio was wrong: fix the frame and regenerate [INFERRED].

