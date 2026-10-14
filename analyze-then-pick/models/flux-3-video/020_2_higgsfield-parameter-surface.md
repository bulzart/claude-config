## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `flux_3_video` | `duration` | 5–20 (whole seconds) | 5 | BFL: 5–20; continuation 5–15 [OFFICIAL]. Out-of-range values snap or clamp [HF] |
| `flux_3_video` | `resolution` | `720p`, `1080p` | `720p` | BFL `hd` comes straight off the generation; `fhd` is the "same generation" upsampled [OFFICIAL]. Always `720p` here |
| `flux_3_video` | `generate_audio` | bool | true | "Generate synchronized speech, effects, and ambience" [HF] |
| `flux_3_video` | `aspect_ratio` | `auto`, `21:9`, `2:1`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | not stated | Always `9:16` (not `auto`: "`auto` lets the harness choose from the prompt and any references") [OFFICIAL] |
| `flux_3_video` | draft, safety tolerance, qhd/uhd, version, negative prompt, seed | not exposed | — | BFL has no negative field either [OFFICIAL][HF] |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | Opening frame, on screen "pixel for pixel" [OFFICIAL] | 1 | ≥256×256; PNG/JPEG/WebP [OFFICIAL] |
| `end_image` | Closing frame; the model fills the motion between [OFFICIAL] | 1 | "experimental: expect more variance… re-roll a miss" [OFFICIAL] |
| `image_references` | Either BFL `reference_images` (1–10 identity images that "never appear on screen") or interior storyboard keyframes (on screen) [OFFICIAL semantics; mapping unknown] | Higgsfield: "up to 10 reference frames" [HF] | Probe first |
| `video_references` | BFL `start_video` (continue from the final frames) and/or `reference_video` (carry the cast into a new shot) [OFFICIAL semantics; Higgsfield says continuation] | 1 video, ≤15 s, ≤50 MB [OFFICIAL] | Output ≤15 s with a video at 720p [OFFICIAL] |

Values are Higgsfield media UUIDs or completed job IDs, never URLs; roles may be auto-coerced [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** 5–20 s, default 5 [HF]. For speech, "`duration` is a tempo control, not a length estimate… at 18s it does not pad with silence, it drags." Unhurried delivery runs about 2.1–2.5 words per second [OFFICIAL: BFL product-ads skill].
- **Resolution:** 720p here. 1080p is an upsampled finish of the same shot [OFFICIAL].
- **Frame rate:** 24 fps [OFFICIAL].
- **Aspect ratio:** explicit ratios are predictable. Mismatched input ratios "force the model to either crop or pad" [OFFICIAL: FLUX technical guide].
- **Audio:** on by default. For silence set `generate_audio: false`; do not prompt for "quiet room tone", which "may collapse into static or dead air" [OFFICIAL]. Audio off lowers cost during tests [HF].
- **Cost reference** (Higgsfield blog, approximate): 5 s 720p ≈ 27.5 credits; 20 s 720p ≈ 110 [HF]. Always run `get_cost`.

### 2.4 Call recipes

All in the fixed output format (§2.6).

Text-to-video with audio:
```json
{"model":"flux_3_video","prompt":"<PROMPT>","duration":10,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Start frame → video (silent; the frame is 9:16):
```json
{"model":"flux_3_video","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":false}
```
Start + end frame:
```json
{"model":"flux_3_video","prompt":"<TRANSITION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_2>","role":"end_image"}],"duration":10,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Image references (do not mix with start/end frames until verified):
```json
{"model":"flux_3_video","prompt":"<REFERENCE_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
Continuation (source already 9:16; `duration` ≤15):
```json
{"model":"flux_3_video","prompt":"<CONTINUATION_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"duration":8,"resolution":"720p","aspect_ratio":"9:16","generate_audio":true}
```
A previous job can be chained as `{"value":"<JOB_ID>","role":"video_references"}` [HF]. Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas

1. **Role semantics are unverified on Higgsfield** [INFERRED]. BFL documents two behaviours each:
   - images: identity references never shown on screen, or keyframes shown pixel-exact;
   - video: continue from the final frames (`start_video`), or keep the cast in a new shot (`reference_video`).

   Run one 5 s / 720p / silent probe per role with a distinctive test object. Record whether the reference pixels appear verbatim, and whether a video input continues or recasts.
2. **One input type per request.** BFL: "keyframes and reference_images together return a 422" and "One video input per request" [OFFICIAL]. Do not mix until verified.
3. **Video input caps duration at 15 s** at 720p [OFFICIAL]. Continuation `duration` counts only the new segment [OFFICIAL].
4. **End-frame variance.** Re-roll misses [OFFICIAL].
5. **Early access.** Behaviour tracks `version: latest` [OFFICIAL]; re-verify after updates.

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `flux_3_video` | `"aspect_ratio":"9:16"`, `"resolution":"720p"` | **704×1280**: BFL `hd` at 9:16. Dimensions are multiples of 32 [OFFICIAL]. The 720p ↔ `hd` mapping is [INFERRED] | **Required.** `atp.py conform`: scale-to-fill ×1.0227 to 720×1309, then center-crop 29 px of height → 720×1280 (≈2.2% crop; never stretch). BFL: "Crop the delivered frame if you need an exact standard size" [OFFICIAL] | Explicit `"9:16"` (not `auto`). Start/end frames conformed to 9:16 (≥704×1280 ideal, ≥256 px minimum). Continuation sources conformed to 9:16 first, since continuation follows the source frame [OFFICIAL] |

