## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `minimax_hailuo` | `variant` | `minimax`, `minimax-fast`, `minimax-2.3`, `minimax-2.3-fast` | `minimax-2.3` | "Minimax Hailuo model variant." [HF]; mapping in §1 |
| `minimax_hailuo` | `duration` | `6`, `10` | 6 | "Duration in seconds." [HF] |
| `minimax_hailuo` | `resolution` | `"512"`, `"768"`, `"1080"` | `"768"` | "'512' is incompatible with end_image, and is not supported by the 'minimax-2.3' / 'minimax-2.3-fast' variants." [HF] |
| `minimax_hailuo` | `aspect_ratio` | none (empty list) | — | no ratio control; see §2.6 [HF] |
| `minimax_hailuo` | prompt_optimizer, fast_pretreatment, audio | — | — | not exposed on Higgsfield [HF]; upstream schemas contain no audio, negative-prompt or seed fields [OFFICIAL, by absence] |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame (upstream `first_frame_image`) | 1; JPG/JPEG/PNG/WebP, <20 MB, short edge >300 px, aspect 2:5–5:2 [OFFICIAL] | "Video resolution follows the first frame image" [OFFICIAL]; must be 9:16 |
| `end_image` | last frame (upstream `last_frame_image`) | 1; same limits; Hailuo 02 only; not with 512 [OFFICIAL/HF] | "If first and last frames differ in size, the last frame will be cropped to match the first" [OFFICIAL] |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
Upstream duration × resolution matrix [OFFICIAL]:

| model | 512P | 768P | 1080P |
|---|---|---|---|
| Hailuo 2.3 / 2.3 Fast | — | 6 or 10 s | 6 s only |
| Hailuo 02 | 6 or 10 s (image-to-video only) | 6 or 10 s | 6 s only |
| Hailuo 02 first+last frame | — | 6 or 10 s | 6 s only |

- **1080 + 10 s is not a valid upstream combination** [OFFICIAL]; the server snaps/clamps or rejects [HF contract].
- **Aspect ratio:** not selectable [HF]; image-to-video follows the start frame [OFFICIAL/HF]; text-to-video is 16:9
  (§2.6).
- **Audio:** none documented; treat output as silent [INFERRED from OFFICIAL API with no audio fields].

### 2.4 Call recipes
Start frame → video (9:16 frame; the deliverable path):
```json
{"model":"minimax_hailuo","prompt":"<MOTION PROMPT with [camera commands]>","variant":"minimax-2.3","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":6,"resolution":"768"}
```
Fast iteration (9:16 frame):
```json
{"model":"minimax_hailuo","prompt":"<MOTION PROMPT>","variant":"minimax-2.3-fast","medias":[{"value":"<IMAGE_MEDIA_ID or JOB_ID>","role":"start_image"}],"duration":10,"resolution":"768"}
```
First + last frame (Hailuo 02 only; both frames 9:16, identical size):
```json
{"model":"minimax_hailuo","prompt":"<PATH PROMPT>","variant":"minimax","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"resolution":"768"}
```
Text-to-video: no recipe in the fixed format — the output is landscape (§2.6). For a text-only concept, generate a 9:16
still first and use the start-frame recipe. Preflight any call with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. **Resolution values are bare strings** `"512"`, `"768"`, `"1080"` (no "p") [HF].
2. **`end_image` works only with variant `minimax`** (Hailuo 02) upstream [OFFICIAL]; with 2.3 variants expect rejection
   or silent omission [INFERRED]. Never combine `end_image` with `"512"` [HF].
3. **Fast variants need a start frame:** `MiniMax-Hailuo-2.3-Fast` is absent from the upstream text-to-video list
   [OFFICIAL]; `minimax-fast` presumably too [INFERRED].
4. **`"512"`** needs variant `minimax` (or possibly `minimax-fast`) and a start image upstream; never for deliverables
   (§2.6) [OFFICIAL/HF/INFERRED].
5. **Prompt optimizer:** upstream `prompt_optimizer` defaults to `true` ("Set to false for more precise control") and
   is not exposed [OFFICIAL/HF] → prompts may be rewritten; keep camera commands explicit [INFERRED].
6. **Prompt limit 2,000 characters** [OFFICIAL]. **No negative prompt, seed or audio** [OFFICIAL/HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
How aspect is set: there is no ratio parameter [HF]. Image-to-video output follows the start frame ("Video resolution
follows the first frame image" [OFFICIAL]; Higgsfield: "Aspect Ratio: Matches input image dimensions" [HF]).
Text-to-video has no documented ratio [OFFICIAL silence]; third-party specs list 16:9 only (768p = 1366×768, 1080p =
1920×1080) [SECONDARY] — cutting 9:16 out of that would discard ~68% of the width, so text-to-video is not a 9:16 path.

| path | params | expected output | action |
|---|---|---|---|
| Start frame (± end frame) | 9:16 `start_image` (and identical `end_image`); `"resolution":"768"` (6 or 10 s) or `"1080"` (6 s); no `aspect_ratio` | portrait at the tier; exact pixels undocumented — a 768-px short edge (≈768×1366) is likely [INFERRED] | measure, downscale |
| `"512"` / `minimax-fast` | — | short edge below 720 would need upscaling | drafts only |
| Text-to-video | — | 16:9 [SECONDARY] | do not use for deliverables |

Make the 9:16 still first (e.g. 1080×1920), then generate. If the output's short edge is below 720, regenerate at
`"1080"` (6 s) rather than upscale [INFERRED]. Otherwise finish with `atp.py conform --video "<in>" --out "<out>"`
(scale-to-cover + focus crop to exactly 720×1280, never stretched). If `conform` refuses (>12% loss), the frame ratio
was wrong — fix the frame and regenerate; never force a landscape text-to-video clip into 9:16 [INFERRED].

