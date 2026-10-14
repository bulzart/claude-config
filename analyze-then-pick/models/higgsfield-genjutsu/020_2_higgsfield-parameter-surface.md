## 2. Higgsfield parameter surface
### 2.1 Parameters
| id | parameter | values | default |
|---|---|---|---|
| both | `resolution` | 480p, 720p, 1080p | 720p |

There are no duration, aspect, audio or genre parameters: the output follows the source video
[INFERRED from the empty `aspect_ratios` and the Higgsfield description].

### 2.2 Media roles
- Catalog roles: `image_references`, `video_references`.
- The first-party recipe passes reference images with role **`image`** and **exactly one**
  source/driving video with role **`video`** [HF]. The server auto-coerces.
- Order: the video first, then the images, in `@ImageN` order (Higgsfield edit convention [HF]).

### 2.3 Duration, resolution, audio
- The duration equals the source's (4–30 s).
- 720p is the default.
- Audio: prior research reported that the source audio is kept [INFERRED, unverified]. After
  download, check with `ffprobe` (`atp.py hf-get` reports `has_audio`) and run `atp.py restore-audio`
  if it is missing.

### 2.4 Call recipes
```json
{"model":"hf_mult_replace_object","prompt":"<edit brief — see §4.4>","resolution":"720p",
 "medias":[{"value":"<SOURCE_VIDEO_MEDIA_ID>","role":"video"},{"value":"<ASSET_IMAGE_1_MEDIA_ID>","role":"image"},{"value":"<ASSET_IMAGE_2_MEDIA_ID>","role":"image"}],
 "folder_id":"<FOLDER_ID>"}
```
```json
{"model":"hf_mult_motion_control","prompt":"<transfer brief — see §4.4>","resolution":"720p",
 "medias":[{"value":"<DRIVING_VIDEO_MEDIA_ID>","role":"video"},{"value":"<CHARACTER_IMAGE_MEDIA_ID>","role":"image"},{"value":"<SCENE_IMAGE_MEDIA_ID>","role":"image"}],
 "folder_id":"<FOLDER_ID>"}
```

### 2.5 Gotchas
- Exactly one video per call.
- Trim the source to 4–30 s around the part that matters; the whole clip is billed.
- The web app's 30+ presets are not exposed through MCP. Write a short brief instead.
- The legacy `motion_control` MCP tool (Kling 3.0 Motion Control) is a different engine. The MCP
  instructions say to route motion transfer to `hf_mult_motion_control` [HF].
- Pricing [HF, Sept 2026]:
  - 15 s: 40 / 104 / 144 credits at 480p / 720p / 1080p;
  - 10 s at 1080p: 99.
  Always preflight.

### 2.6 9:16 / 720p mapping
- `resolution:"720p"`; the output aspect follows the source video.
- **Make the source 9:16 before submitting:**
  - `atp.py conform` with a focus point, when a crop keeps every important subject (≤ 12 % loss by
    default);
  - otherwise Higgsfield `reframe` to 9:16 at 720p;
  - otherwise regenerate with a reference-to-video model.
- After download, `conform` to exactly 720×1280 when needed, then `qc`.

