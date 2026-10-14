## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling_video_edit` | `mode` | `std`, `pro`, `4k` | `pro` | "Output quality: Standard, Pro, or 4K." [HF S3]. Project: `std` (§2.6). |
| `kling_video_edit` | `aspect_ratio` | none (empty list) | — | Output follows the source [HF S3; INFERRED]. |
| `kling_video_edit` | `duration` | none | — | Output follows the source length ("duration matches source range") [HF S4]; API mirrors: duration ignored in base editing [SECONDARY S10]. |
| `kling_video_edit` | audio | none | — | Native audio "Not Supported Yet" with video input [OFFICIAL S1]; Kling's API has a keep-original-sound option and a mirror defaults `keep_audio:true` [SECONDARY S10, S11]; restore the source audio locally (§2.5). |
| `kling_video_edit` | `negative_prompt`, `cfg_scale`, `keep_original_sound`, `refer_type` (base/feature), elements, seed | — | — | **Not exposed on Higgsfield** [HF S3]. Kling's API separates a "base" video to edit from a "feature" video used as style/camera reference [SECONDARY S10]; this id is edit-only. Write preservation and exclusions in the prompt (§3.10). |

Call-level keys: `model`, `prompt`, `medias`, `get_cost` (preflight, submits nothing) [HF S6].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `video_references` | the source clip to edit (`@Video1`) | exactly 1: "You can upload one video with a duration between 3s and 10s, file size ≤ 200MB, and resolution ≤ 2k." [OFFICIAL S1]; June 2026 upgrade: 3–15 s, 4K input [SECONDARY S9] | send it first in `medias` [INFERRED] |
| `image_references` | replacement subject/product, background, style or colour source (`@Image1…4`) | ≤4 with a video; each ≥300 px, ≤10 MB, jpg/jpeg/png [OFFICIAL S1, S2] | in `@Image` order after the video |

`medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S6]. Server-side role coercion applies when unambiguous [HF S6].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** follows the source [HF S4]; keep sources 3–10 s unless a test confirms the upgraded 3–15 s range on Higgsfield [OFFICIAL S1; HF S5; SECONDARY S9]. Split longer sources on hard cuts.
- **Resolution:** `std` / `pro` / `4k` output tiers [HF S3]; Higgsfield's help centre still lists Omni Edit at 1080p max while the catalog offers `4k` [HF S5, S3].
- **Aspect ratio:** follows the source [HF S3].
- **Audio:** treat returned audio as untrusted; strip it and restore the source's own track locally, conformed to the source duration (Higgsfield's own practice for Seedance edits) [OFFICIAL S1; HF S8; INFERRED].
- **Billing basis:** undocumented — preflight with `get_cost:true` [HF S6].

### 2.4 Call recipes

Source reframed to 9:16 before upload (§2.6). Add `"get_cost": true` to preflight.

**Instruction-only edit**
```json
{"model":"kling_video_edit","prompt":"<EDIT INSTRUCTION citing @Video1>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"mode":"std"}
```
**Reference-guided edit (source first, then up to four images)**
```json
{"model":"kling_video_edit","prompt":"<EDIT INSTRUCTION citing @Video1 and @Image1..@Image2>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"}],"mode":"std"}
```
**Two-pass clean-up: text removal first, content edit second** (the second call uses the first call's completed job id as its source) [INFERRED]
```json
{"model":"kling_video_edit","prompt":"<REMOVE-ONLY INSTRUCTION>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"mode":"std"}
```
```json
{"model":"kling_video_edit","prompt":"<CONTENT EDIT citing @Video1 and @Image1>","medias":[{"value":"<JOB_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"}],"mode":"std"}
```

### 2.5 Parameter gotchas

- **Tag binding is undocumented on Higgsfield.** Kling's guide writes `[@Video]`, `[@Image1]`, `[@Element]` [OFFICIAL S2]; API mirrors use `@Video1`/`@Image1`/`@Element1` [SECONDARY S11] or `<<<image_1>>>` [SECONDARY S12]; Higgsfield normalises `@Image` tags server-side for Seedance [HF S8]. Write `@Video1` and `@Image1…@Image4` in `medias` order **and** describe every target in words [INFERRED].
- No `duration` or `aspect_ratio` parameters — do not send them [HF S3]. Four images maximum [OFFICIAL S1].
- Elements are documented for `kling3_0`, not this id [HF S6]; use `image_references`.
- Source ≤200 MB and ≤2K (transcode 4K phone footage) unless 4K input is confirmed [OFFICIAL S1; SECONDARY S9].
- Using a completed job id as the next call's source is supported by the MCP contract [HF S6]; whether Higgsfield accepts a video job id for `video_references` on this id is untested.
- Kling's API caps prompts at 2,500 characters [SECONDARY S13]; keep edit prompts short.

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| step | what to do | expected output | post-processing |
|---|---|---|---|
| before upload | reframe the source to 9:16 at 720×1280 with `atp.py conform` (scale-to-fill + minimal crop; never stretch); keep 3–10 s | — | — |
| edit call | `mode:"std"` (Kling's standard tier ≈ 720p) [SECONDARY S16; INFERRED for the edit model] | follows the source ratio → 720×1280 expected [INFERRED] | ffprobe; if the short edge is not 720 or the ratio drifted, `atp.py conform`; conform duration to the source; restore source audio |

A non-9:16 source whose important content would be cropped away is better re-created in Analyze Mode with a generation model than edited [INFERRED].

