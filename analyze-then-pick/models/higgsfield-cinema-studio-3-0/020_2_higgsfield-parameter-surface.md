## 2. Higgsfield parameter surface

### 2.1 Parameters
| id | parameter | values | default | notes |
|---|---|---|---|---|
| cinematic_studio_3_0 | `resolution` | 480p, 720p, 1080p, 4k | 720p | Higher costs more [HF] |
| | `genre` | auto, action, horror, comedy, noir, drama, epic | auto | Cinematic genre hint that shapes camera and colour language |
| | `generate_audio` | bool | **false** | Audio is **off** by default [VERIFIED adjustments]. Set `true` when the concept needs sound; the price did not change in preflight (8 s 720p = 40 credits both ways) |
| | `duration` | 4–15 s | — | Unsupported values are clamped |
| | `aspect_ratio` | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | — | |
| | `speedramp` | — | — | **Not supported over MCP**: the preflight reported "Cinema Studio Video 3.0 does not support this parameter" [VERIFIED], although the web UI has 8 speed-ramp presets |

Camera body, lens, focal length, aperture, speed ramp and the Director Panel movement stack are
web-app controls; the MCP does not expose them. Describe camera behaviour in the prompt instead.

### 2.2 Media roles
| role | controls | notes |
|---|---|---|
| `image` | Generic image conditioning | One or more? Not documented; start with one |
| `start_image` | First frame composition | The output follows its framing |
| `end_image` | Last frame composition | Use with `start_image` |

### 2.3 Duration, resolution, aspect, audio
4–15 s; 480p–4k; audio optional and off by default.

### 2.4 Call recipes (fixed 9:16 / 720p)
```json
{"model":"cinematic_studio_3_0","prompt":"<prompt>","duration":8,"aspect_ratio":"9:16","resolution":"720p","genre":"auto","generate_audio":true,"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_3_0","prompt":"<motion-and-story prompt that continues from the first frame>","duration":6,"aspect_ratio":"9:16","resolution":"720p","generate_audio":false,
 "medias":[{"value":"<START_FRAME_MEDIA_ID>","role":"start_image"},{"value":"<END_FRAME_MEDIA_ID>","role":"end_image"}],"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_3_0","prompt":"<<<CHARACTER_ELEMENT_ID>>> <action> while holding <<<PRODUCT_ELEMENT_ID>>> …","duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true,"folder_id":"<FOLDER_ID>"}
```

### 2.5 Gotchas
- `generate_audio` defaults to false, unlike most models.
- `speedramp` is silently dropped over MCP. Always read `adjustments` from the `get_cost` preflight.
- **Prompt length.** A third-party skill reports a hard **512-character** prompt limit in Cinema
  Studio's web UI, with ~350–400 visible characters recommended when references are attached
  [SECONDARY]. The MCP limit is unknown. Keep prompts **≤ 500 characters**, and shorter with Elements.

### 2.6 9:16 / 720p mapping
`aspect_ratio:"9:16"`, `resolution:"720p"` → expected 720×1280 [INFERRED from the resolution tier;
confirm with `atp.py qc`]. With `start_image` / `end_image`, supply frames that are already 9:16
(720×1280 or larger at the same ratio). Run `atp.py conform` if the output differs.

