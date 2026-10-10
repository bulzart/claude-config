---
guide: higgsfield-cinema-studio-video
title: Higgsfield Cinema Studio Video (v1)
provider: Higgsfield (in-house; underlying model not disclosed)
higgsfield_model_ids: [cinematic_studio_video]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: low
---

# Higgsfield Cinema Studio Video (v1) — model engineering guide

> Scope: `cinematic_studio_video`, described in the catalog as "Solid cinematic, dramatic
> compositions". Its only controls are a slow-motion switch and a sound switch. Prefer
> `cinematic_studio_3_0` or `cinematic_studio_video_v2` unless the user selects this model.
> Tags: **[HF]** · **[VERIFIED]** · **[INFERRED]**.

## 1. At a glance
- **Best for:** simple dramatic single shots from a hero frame. It is inexpensive (5 s = 8 credits,
  preflight 2026-09-30 [VERIFIED]).
- **Weaker at:** controllability. It has no resolution, genre, multi-shot, speed or adherence controls.
- Operations: text-to-video; `image` / `start_image` / `end_image` conditioning; Elements are not
  listed for v1.

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
- Always run `atg.py conform` to 720×1280 (scale-to-cover, minimal crop), then `qc`.
- The hero frame must be 9:16.

## 3. How the model reads a prompt (conservative defaults; no official specification)

### 3.1 Recommended structure
Subject → setting → style → action → atmosphere (Higgsfield structure, see
`higgsfield-cinema-studio-3-0.md` §4.0). ≤ 500 characters.

### 3.5 Chronology
Only 5 or 10 s. Plan 1–2 beats for 5 s and 2–3 for 10 s, each with an end state, to avoid dead air.

### 3.6 Camera
One move, in words.

### 3.10 Negative constraints
None as a parameter; use short positive phrasing.

### 3.11 Visible text
- (a) Unreliable.
- (b) For a clean plate, end with "No on-screen text, captions or logos."
- (c) Add planned text in post (`atg.py captions`).
- (d) Edits: N/A.

### 3.12 – 3.13 Identity and product
Control them through the hero frame (correct scale, light and placement baked in). The prompt only
describes motion and states that shape and appearance stay unchanged.

### 3.14 Integration and continuity
Keep the light consistent with the frame, state contact points, and state persistent states (placed
objects stay put, container states hold).

## 4. Templates
### 4.0 Official examples
None published. Use the Higgsfield pattern from the 3.0 guide.
### 4.1 / 4.2
`From the opening frame, <motion> ending <end state>. <Camera>. Real-time speed. <Sound>. No on-screen text.`
### 4.3 / 4.4
N/A.

## 5. Failure modes
| Failure | Trigger | Mitigation |
|---|---|---|
| Dead air | 10 s with a single small action | Use 5 s or add a beat |
| Unwanted slow motion | `slow_motion:true` | Keep false |
| Wrong output size | No resolution control | `conform` |

## 6. Model-specific features and controls
`slow_motion` (bool) and `sound` (bool) only.

## 7. Checklist
- [ ] 9:16 hero frame.
- [ ] Duration 5 or 10.
- [ ] `slow_motion:false` unless intended.
- [ ] `conform` + `qc`.

## 8. Sources
- [HF] catalog and `get_cost` preflight (2026-09-30).

## 9. Open questions
- Output resolution.
- The underlying model.
- Whether Elements work with v1.
