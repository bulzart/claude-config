## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `flux_3_video_edit` | `prompt` | 1–4,096 characters | — | Whitespace is trimmed [OFFICIAL] |
| `flux_3_video_edit` | `folder_id` | string (nullable) | — | "Optional folder to place the generated output in" [HF] |
| `flux_3_video_edit` | `aspect_ratio` | none listed | — | Output follows the source [OFFICIAL][HF] |
| `flux_3_video_edit` | duration, resolution, seed, audio flag, mode | not exposed | — | BFL returns HTTP 422 for "`mode`, `version`, `seed`, `duration`, `resolution`, `aspect_ratio` and `generate_audio`" [OFFICIAL]. Do not send them |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `video_references` | The source clip to edit | Exactly 1 [OFFICIAL] | MP4, ≤15 s, ≤50 MiB, each side ≥160 px, ≥17 frames at 24 fps (about 0.7 s) [OFFICIAL]. Higgsfield uses "the first 15 seconds at most" [HF] |

Values are Higgsfield media UUIDs or completed job IDs (for example a previous pass), never URLs [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** equal to the trimmed source. BFL rejects sources over 15 s ("rejected, not trimmed"); Higgsfield uses the first 15 s [OFFICIAL][HF]. Trim locally so you choose the window.
- **Resolution:** "Sources larger than 720p are downscaled to 720p: the 1920 × 1088 harbor clip came back at 1248 × 704" [OFFICIAL].
- **Frame rate:** 24 fps output [OFFICIAL]. 30/60 fps sources come back at 24 fps; account for this when remuxing [INFERRED].
- **Audio:** "Source audio is carried through unless the prompt asks for a dialogue or sound change. A silent source returns a silent result" [OFFICIAL].
- **Billing:** 1 credit per processed second [HF]. BFL: $0.03 per output second, "a ten second clip costs the same whatever the edit" [OFFICIAL]. Stacked edits in one prompt cost no more [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6): the source is conformed to 9:16 720×1280 and trimmed to ≤15 s before upload.

Single edit or text-removal pass:
```json
{"model":"flux_3_video_edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}]}
```
Second pass on the previous result (dependent edits):
```json
{"model":"flux_3_video_edit","prompt":"<NEXT_EDIT_PROMPT>","medias":[{"value":"<JOB_ID>","role":"video_references"}]}
```
With an output folder:
```json
{"model":"flux_3_video_edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"folder_id":"<FOLDER_ID>"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; collect via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Pre-trim and pre-reframe** the source (≤15 s, ≥0.7 s, ≥160 px, ≤50 MiB, 9:16) [OFFICIAL + policy].
2. **720p ceiling and 24 fps** [OFFICIAL]. Re-time source audio against the 24 fps output if the pipeline restores it [INFERRED].
3. **One video only.** "image input, audio-only input, masks and extending a clip are not supported" [OFFICIAL].
4. **Untargeted content persists, including text** [OFFICIAL behaviour]. Every overlay to remove must be named (§3.11).
5. **Speech cannot grow** [OFFICIAL].
6. **Moderation.** `Request Moderated` / `Content Moderated` are terminal; reword rather than resubmit verbatim [OFFICIAL].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `flux_3_video_edit` | None. There is no aspect or resolution parameter, and sending one is a 422 upstream [OFFICIAL] | Follows the source ratio, length and 24 fps, at ≤720p [OFFICIAL]. For a 720×1280 source, expect 720×1280 or a 704-wide variant such as 704×1248 (BFL's 16:9 720p class is 1248×704) [INFERRED] | `atp.py conform` the output to exactly 720×1280 (scale-to-fill plus minimal crop; never stretch) | **Reframe the source to 9:16 (720×1280) with `atp.py conform` before upload.** The reframe may already crop away edge captions, which leaves less text to remove |

