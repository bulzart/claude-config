---
guide: higgsfield-cinema-studio-video-2
title: Higgsfield Cinema Studio Video (v2)
provider: Higgsfield (in-house; underlying model not disclosed)
higgsfield_model_ids: [cinematic_studio_video_v2]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: low
---

# Higgsfield Cinema Studio Video (v2) — model engineering guide

> Scope: `cinematic_studio_video_v2`, described in the catalog as "Refined cinematic camera and color,
> genre control". It covers text-to-video and image / start / end-frame video, with genre, speed-ramp,
> multi-shot and prompt-adherence controls. Tags: **[HF]** · **[VERIFIED]** (preflight on 2026-09-30)
> · **[SECONDARY]** · **[INFERRED]**. No official prompt specification is published.

## 1. At a glance
- **Positioning [HF]:** the Cinema Studio 2.x video engine.
  - The web app pairs Cinema Studio 2.0 with a "Hero Frame First" workflow: build the perfect still,
    then animate it, with up to three stacked camera moves.
  - Cinema Studio 2.5 adds colour grading, Soul Cast characters, Single / Multi-Shot Auto /
    Multi-Shot Manual modes, and speed ramps.
- **Underlying model:** not disclosed. Its parameter style (`cfg_scale`, std/pro modes, multi-shot)
  resembles Kling's [INFERRED].
- **Best for:** fast, cheap cinematic clips from a strong hero frame, with genre look, speed ramps and
  automatic multi-shot planning. Preflight: 6 s std = 9 credits [VERIFIED].
- **Weaker at:** exact multi-shot scripting over MCP (see §2.5), references beyond Elements, and exact
  text.

| Operation | How | Notes |
|---|---|---|
| Text-to-video | prompt | |
| Hero frame → video | `start_image` (+ `end_image`) | Recommended use |
| Image conditioning | `image` | Weighting undocumented |
| Reusable assets | `<<<element_id>>>` | Elements support "Cinema Studio Video 2" [HF] |
| Multi-shot | `multi_shots:true`, `multi_shot_mode:"auto"` | The model plans the shots; custom per-shot prompts are not available (§2.5) |

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
- The output may not be exactly 720×1280, so always run `atg.py conform` (scale-to-cover, minimal
  crop) and `qc --expect-size 720x1280`.
- Hero frames must be 9:16.

## 3. How the model reads a prompt

### 3.1 Structure
use the Higgsfield order (see §4.0): subject → setting → style → action →
atmosphere. Compact prose. A third-party skill reports a 512-character web limit [SECONDARY]; keep
prompts ≤ 500 characters.

### 3.2 Subject
bind the subject to the hero frame or an Element.

### 3.3 Action
one clear action per beat, with cause → contact → result.

### 3.4 Style
`genre` carries the look; describe the light direction in words.

### 3.5 Chronology
order the beats explicitly. With `multi_shots` in auto mode, write the beats as
"Shot one…, then…" in prose; the model decides the cuts [INFERRED].

### 3.6 Camera
describe one move per shot, or none for locked-off shots. The web Director Panel
stack is not exposed.

### 3.7 References
use Elements or start/end frames. There is no `image_references` role.

### 3.8 Frames
the Hero Frame First approach is the recommended way to control composition, asset
geometry and lighting.

### 3.9 Audio
with `sound:"on"`, state the ambience and action sounds and whether anyone speaks.

### 3.10 Negatives
there is no field. Use short positive phrasing plus one exclusion sentence.

### 3.11 Visible text
- (a) Reliability is unknown, so treat it as unreliable.
- (b) For a clean plate, end with "No on-screen text, captions or logos."
- (c) Add planned text in post with `atg.py captions`.
- (d) Edits: N/A.

### 3.12 Identity
keep the same Element id and wardrobe wording across clips.

### 3.13 Product
put the canonical product into the hero frame at the correct scale; state its size
relative to the hands and that its shape and label stay unchanged.

### 3.14 Integration
state the light direction and shadows on the inserted asset, the contact
points, and persistent states.

## 4. Prompt construction
### 4.0 First-party material
No official prompt set. See the Higgsfield example and structure in
`higgsfield-cinema-studio-3-0.md` §4.0 [HF]:
- a style cue first;
- subject bound to a reference;
- one continuous action;
- environment;
- optical and physical cues.

### 4.1 Text-to-video
`<Style>. <Subject> <action + end state> in <setting>. <Light>. <Camera>. <Sound>. No on-screen text.`

### 4.2 Hero frame → video
`From the opening frame, <first motion>, then <second>, ending <end state>. <Camera>. Real-time speed. No on-screen text.`

### 4.3 Multi-shot (auto)
`<Scene>. Beat one: <…>. Then: <…>. Finally: <…>. Same characters, wardrobe and location throughout. Real-time speed. No on-screen text.`

### 4.4 Edit
N/A.

## 5. Failure modes
| Failure | Trigger | Mitigation |
|---|---|---|
| Unmotivated speed changes | `speedramp:"auto"` | `linear` by default |
| Shot plan ignores intent | `multi_shot_mode:"auto"` with vague beats | Explicit ordered beats, or separate clips |
| Output not 720×1280 | No resolution parameter | `conform` + `qc` |
| Character drift between clips | No shared reference | The same Element / hero frame source |

## 6. Features
Genre, speed ramp, multi-shot (auto), `cfg_scale`, Elements.

## 7. Checklist
- [ ] `aspect_ratio:"9:16"`, `mode:"std"`, `speedramp:"linear"` unless a ramp is motivated.
- [ ] `sound` string set deliberately.
- [ ] Prompt ≤ 500 characters, beats ordered, end state stated.
- [ ] 9:16 hero frame / Elements for assets.
- [ ] `conform` + `qc` after download.

## 8. Sources
- [HF] catalog + `get_cost` preflight adjustments (2026-09-30).
- [HF] https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-cinema-studio (accessed 2026-09-30)
- [SECONDARY] https://openskillindex.com/skills/osidemedia-higgsfield-ai-prompt-skill-higgsfield-cinema (accessed 2026-09-30)

## 9. Open questions
- Output pixel size for std vs pro.
- Whether the prompt order drives auto multi-shot boundaries.
- How the `image` role is weighted.
