## 2. Higgsfield parameter surface
| parameter | values | default | notes |
|---|---|---|---|
| `slow_motion` | bool | false | Keep false unless the reference structure uses slow motion deliberately |
| `sound` | bool | true | A bool here, unlike v2's string |
| `duration` | 5 or 10 s | — | Discrete values |
| `aspect_ratio` | 1:1, 4:3, 3:4, 16:9, 9:16 | — | |
| `resolution` | — | — | **Not supported**: the preflight dropped it [VERIFIED] |

Roles: `image`, `start_image`, `end_image`.

### 2.4 Call recipe
```json
{"model":"cinematic_studio_video","prompt":"<prompt>","duration":5,"aspect_ratio":"9:16","slow_motion":false,"sound":true,
 "medias":[{"value":"<HERO_FRAME_MEDIA_ID>","role":"start_image"}],"folder_id":"<FOLDER_ID>"}
```

### 2.6 9:16 / 720p mapping
- Send `aspect_ratio:"9:16"`. There is no resolution control and the output size is unknown.
- Always run `atp.py conform` to 720×1280 (scale-to-cover, minimal crop), then `qc`.
- The hero frame must be 9:16.

