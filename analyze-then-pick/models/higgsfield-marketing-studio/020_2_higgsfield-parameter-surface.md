## 2. Higgsfield parameter surface
| parameter | values | default | notes |
|---|---|---|---|
| `resolution` | 480p, 720p, 1080p | 720p | |
| `generate_audio` | bool | true | |
| `mode` | preset slug | — | "Choose it deliberately rather than letting it default… Omit only when the user explicitly wants a generic video" [HF] |
| `avatar_ids` | [uuid] (max 1) | — | Preset or custom avatar |
| `product_ids` | [uuid] | — | Plural field name only |
| `hook_id` / `setting_id` | id | — | UGC-family presets only; exclusive with `ad_reference_id` |
| `ad_reference_id` | id | — | Recreates a reference ad's scenario. Avatar and product must still be passed explicitly |
| `assets` | [id] | — | Optional backend asset ids |
| `width` / `height` | number | — | Optional explicit size |
| `duration` | 12–15 s | — | |
| `aspect_ratio` | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | **landscape (16:9) when omitted** | Always pass `9:16` [HF-TOOL] |

Media: `avatars` (image), `medias` with roles `image` / `start_image` / `end_image`.
Preflight: 15 s at 720p = 75 credits; audio defaulted on [VERIFIED].

### 2.4 Call recipes
The first recipe is generic (no ids available from the terminal); the second uses ids the user copied
from the web app.
```json
{"model":"marketing_studio_video","prompt":"<shot, tone and what the ad must show>","duration":15,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true,
 "medias":[{"value":"<PRODUCT_IMAGE_MEDIA_ID>","role":"image"}],"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"marketing_studio_video","mode":"<preset slug>","product_ids":["<PRODUCT_ID>"],"avatar_ids":["<AVATAR_ID>"],"hook_id":"<HOOK_ID>","setting_id":"<SETTING_ID>",
 "duration":15,"aspect_ratio":"9:16","resolution":"720p","folder_id":"<FOLDER_ID>"}
```

### 2.6 9:16 / 720p mapping
`aspect_ratio:"9:16"` (never rely on the landscape default) and `resolution:"720p"`. Or pass
`width:720, height:1280` [HF-TOOL: "the backend derives the aspect ratio"]. Then `qc`.

