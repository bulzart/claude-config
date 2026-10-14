## 2. Higgsfield parameter surface
### 2.1 Parameters
| parameter | values | default | notes |
|---|---|---|---|
| `genre` | auto, action, horror, comedy, western, suspense, intimate, spectacle | auto | A different list from 3.0 |
| `mode` | std, pro | std | Quality tier |
| `sound` | "on", "off" | on | A **string**, not a bool |
| `speedramp` | auto, custom, linear, slowmo, speedup, impact | auto | Use `linear` for real-time motion (§5) |
| `multi_shots` | bool | false | Split into shots |
| `multi_shot_mode` | auto, custom | custom | Use `auto`; see §2.5 |
| `cfg_scale` | 0–1 | 0.5 | Prompt adherence |
| `preset_id` | legacy id | — | Not used |
| `duration` | 3–12 s | — | |
| `aspect_ratio` | 1:1, 4:3, 3:4, 16:9, 9:16 | — | |

### 2.2 Media roles
`image`, `start_image`, `end_image` [HF].

### 2.3 Duration, resolution, audio
- 3–12 s. There is no resolution parameter; `mode` sets the quality tier.
- Audio is on by default.

### 2.4 Call recipes
```json
{"model":"cinematic_studio_video_v2","prompt":"<prompt>","duration":6,"aspect_ratio":"9:16","mode":"std","genre":"auto","speedramp":"linear","sound":"on","cfg_scale":0.6,"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_video_v2","prompt":"<motion from the hero frame>","duration":5,"aspect_ratio":"9:16","mode":"std","speedramp":"linear","sound":"off",
 "medias":[{"value":"<HERO_FRAME_MEDIA_ID>","role":"start_image"}],"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_video_v2","prompt":"<scene with 2–3 natural beats>","duration":10,"aspect_ratio":"9:16","mode":"std","multi_shots":true,"multi_shot_mode":"auto","speedramp":"linear","folder_id":"<FOLDER_ID>"}
```

### 2.5 Gotchas
- **`multi_prompt` is not supported over MCP.** The preflight answered "Cinema Studio Video does not
  support this parameter" and omitted it, for both string and object arrays [VERIFIED]. So
  `multi_shot_mode:"custom"` has no per-shot input. Use `"auto"` and describe the beats in order, or
  generate the shots as separate clips.
- The `speedramp` default `auto` may inject speed changes. Set `linear` unless a ramp is motivated by
  the reference's editing style.
- `sound` takes the strings "on" / "off".

### 2.6 9:16 / 720p mapping
- Send `aspect_ratio:"9:16"` and `mode:"std"`. `std` is the lower tier, assumed ≈720p
  [INFERRED — confirm pixel size on the first run].
- The output may not be exactly 720×1280, so always run `atp.py conform` (scale-to-cover, minimal
  crop) and `qc --expect-size 720x1280`.
- Hero frames must be 9:16.

