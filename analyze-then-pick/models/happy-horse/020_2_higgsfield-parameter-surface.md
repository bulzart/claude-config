## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `happy_horse_video` | `resolution` | `720p`, `1080p` | `720p` | "Output resolution." [HF]; always `720p` (§2.6); upstream default 1080P [OFFICIAL] |
| `happy_horse_video` | `duration` | number, min 3, max 15 | 5 | "Duration in seconds (3-15)." [HF]; upstream integer 3–15 [OFFICIAL] |
| `happy_horse_video` | `aspect_ratio` | `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | — | always `9:16`; upstream image-to-video has no ratio parameter (follows image) [OFFICIAL] |
| `happy_horse_video` | seed, watermark, audio switch, negative prompt | — | — | not exposed on Higgsfield [HF]; negative prompt and prompt rewriting do not exist upstream [OFFICIAL, by absence] |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame (upstream `first_frame`) | exactly 1; JPEG/JPG/PNG/WEBP, each side ≥300 px, aspect 1:2.5–2.5:1, ≤20 MB [OFFICIAL] | "Output pixel count approximates the selected tier while preserving the input image's aspect ratio" [OFFICIAL]; must be 9:16 |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- 3–15 s, 24 fps [OFFICIAL]; unsupported values are snapped/clamped [HF contract].
- Fixed 720p, 9:16 (§2.6); with a start frame the frame's aspect ratio wins [OFFICIAL].
- **Audio:** a listed feature with no on/off parameter upstream [OFFICIAL] → expect speech, ambience or effects; strip
  locally for silent deliverables [INFERRED].
- **Watermark:** upstream default `true`, "HappyHorse"/"Happy Horse" text bottom-right [OFFICIAL]; see §3.11e.

### 2.4 Call recipes
Text-to-video:
```json
{"model":"happy_horse_video","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","resolution":"720p"}
```
Start frame → video (9:16 frame):
```json
{"model":"happy_horse_video","prompt":"<MOTION + CAMERA PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID or JOB_ID>","role":"start_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. `aspect_ratio` is probably ignored when `start_image` is present (upstream image-to-video has no ratio control)
   [OFFICIAL/INFERRED] — the frame must already be 9:16.
2. Only one media role; no end frame [HF].
3. Prompt limit upstream: 5,000 non-Chinese or 2,500 Chinese characters; "Supports any language" [OFFICIAL].
4. Possible provider watermark — check the first output of every session before batch runs (§3.11e) [INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| path | params | expected output | action |
|---|---|---|---|
| Text-to-video | `"aspect_ratio":"9:16","resolution":"720p"` | 9:16 at the 720P tier, 24 fps; no official pixel table (third-party docs list 720P as 1280×720 for 16:9) [SECONDARY] → 720×1280 expected [INFERRED] | verify |
| Start frame | same params + a 9:16 `start_image` | pixel count ≈ 720P tier, image ratio kept [OFFICIAL] → ≈720×1280 | verify |

Finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to exactly 720×1280, never
stretched; a no-op when already exact). If `conform` refuses (>12% loss), the frame ratio was wrong — fix the frame
and regenerate [INFERRED]. Never crop to hide a watermark (§3.11e).

