---
guide: higgsfield-marketing-studio
title: Higgsfield Marketing Studio (video)
provider: Higgsfield (in-house ad engine)
higgsfield_model_ids: [marketing_studio_video]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Higgsfield Marketing Studio — model engineering guide

> Scope: `marketing_studio_video`, "One-click product ads, TikTok/Reels ready". It is a templated ad
> engine, not a free-form prompt model. **Limited from Claude Code:** its mode slugs and its hook,
> setting, avatar, product and ad-reference ids are listed by tools this connector does not expose
> (only the widget `show_marketing_studio_v2` is present, and it does not render in a terminal).
> Tags: **[HF]** · **[VERIFIED]** · **[INFERRED]**.

## 1. At a glance
- **Positioning [HF]:** paste a product URL or upload images, pick an AI avatar and a creative format,
  and get "publish-ready video with native audio and lip sync in one pass".
- **Formats [HF]** (help center):
  - UGC videos (Faceless, Talking Head, Silent);
  - Product Shots (Studio, Lifestyle, With Model);
  - Motion (Hypermotion, 2D Product Motion, Mixed Media, Motion Design);
  - Ref → Video.
- **Hooks and settings:** hooks are 25+ opening mechanics ("Product Hit, Epic Fail, POV, Pattern
  Interrupt, Cold Open…"); settings are locations or vibes. Both are "supported only for these
  presets: UGC, Tutorial, Unboxing, Product Review, UGC Virtual Try On" [HF].
- **Ad Reference [HF]:** "reads its concept, scene composition, pacing, hook, and narration style,
  then generates a new ad in a similar style built around your own product and avatar". It is
  mutually exclusive with hook/setting.
- **When to choose it:**
  - only when the user explicitly selects it, the project is a product ad, and the user can supply
    the Marketing Studio ids from the Higgsfield web app;
  - or they accept a generic prompt-plus-images generation.
  For controlled recreation of analyzed references, prefer Seedance 2.x reference-to-video.

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

## 3. How the model reads a prompt

### 3.1 Recommended structure
- The prompt is optional in the template path. When used: "write a prompt describing the shot, tone,
  and what the ad needs to show" [HF].
- Keep it to the creative intent; the preset supplies structure, pacing, voice-over and hook.

### 3.2 – 3.10
Not individually controllable: the format preset drives subject handling, action, camera, chronology,
audio and exclusions. Describe only the intent and the order of what must be shown.

### 3.11 Visible text
- (a) Formats may add their own captions or text, and "voiceover and pacing in UGC Videos can vary by
  generation" [HF].
- (b) Request "no on-screen text" in generic mode.
- (c) Add planned text in post (`atg.py captions`).
- (d) Edits: N/A. Run QC with OCR in any case.

### 3.12 Character / identity consistency
Avatars come from the preset or custom library, and supplied character references are not guaranteed
to be used. Approved project characters therefore need other models (Seedance, Kling with Elements).

### 3.13 Product and object fidelity
A product created from a URL or images is the product record. With image-only generic mode, supply
the canonical template image.

### 3.14 Integration and continuity
The engine handles them and they are not controllable. QC the product geometry, hands and object
states carefully on the storyboard.

## 4. Construction
### 4.0 Examples
Higgsfield publishes the format catalogue and the hook names above, but no raw prompt examples for
this model. Treat the preset as the "prompt structure".
### 4.1
Generic mode: `<Format intent: UGC talking-head review | product-only demo | unboxing>. <What the ad must show, in order>. <Tone>. No on-screen text.`
### 4.2 – 4.4
N/A.

## 5. Failure modes
| Failure | Mitigation |
|---|---|
| Landscape output | Always `aspect_ratio:"9:16"` |
| Generic look when `mode` is omitted | Ask the user for a preset slug from the web app, or choose another model |
| Wrong avatar / identity | Use Seedance or Kling with approved character references instead |
| Unwanted captions | OCR QC; regenerate with "no on-screen text" or choose another model |

## 6. Model-specific features and controls
Format presets (`mode`), hooks and settings (UGC-family presets), Ad Reference (scenario
recreation), avatars, products, and native audio with lip sync. All ids come from the Higgsfield web
app when using it from Claude Code.

## 7. Checklist
- [ ] The user explicitly chose Marketing Studio.
- [ ] 9:16 / 720p set.
- [ ] Ids available, or generic mode accepted.
- [ ] 12–15 s duration.
- [ ] `qc` for text, geometry and hands.

## 8. Sources
- [HF] catalog + `get_cost` preflight (2026-09-30); `generate_video` tool description (Marketing Studio notes).
- [HF] https://higgsfield.ai/creator-hub/help-center/tools-and-workflows/how-do-i-use-marketing-studio-to-create-video-ads (accessed 2026-09-30)
- [HF] https://higgsfield.ai/blog/how-to-make-ai-ugc-videos (search summary, 2026-09-30)

## 9. Open questions
- Whether generic mode honours `image` references as the product.
- Whether preset slugs can be discovered from the terminal.
- Caption behaviour per format.
