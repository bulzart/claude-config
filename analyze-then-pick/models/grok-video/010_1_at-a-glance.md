## 1. At a glance

- **Model mapping.**
  - `grok_video` → xAI `grok-imagine-video` ("text, image, video → video"). Inferred from the name and feature set [INFERRED].
  - `grok_video_v15` → `grok-imagine-video-1.5` (aliases `-preview`, `-2026-05-30`; "text, image → video") [OFFICIAL]. Higgsfield's own REST API documents it as "Grok Imagine Video 1.5" at `xai/grok-imagine-video/v1.5/reference-to-video` [HF].
- **Positioning.** "On grok-imagine-video-1.5, text-to-video supports native 1080p" [OFFICIAL]. Higgsfield: the model "holds detail and lighting from the input frame - so the result continues the original rather than reinterpreting it" [HF].
- **Timeline [SECONDARY]:** Grok Imagine 1.0 on 2026-02-02; Imagine Video 1.5 preview (image-to-video) on 2026-06-17; text-to-video, image/voice references and native 1080p added around 2026-07-31/08-01.
- **Best for:**
  - faithful animation of an approved start frame [HF];
  - clips up to 15 s [OFFICIAL];
  - reference casting and product placement ("virtual try-on, product placement, character-consistent storytelling, and voice identity") [OFFICIAL];
  - low cost ($0.05/s classic, $0.08/s 1.5 at xAI list price) [OFFICIAL].
- **Weaker at / unknown:**
  - no official prompting or negative-prompt guidance;
  - text is "hit-or-miss" [SECONDARY];
  - always-on audio [HF + INFERRED];
  - image **stretching** when the aspect ratio is forced [OFFICIAL];
  - reference mode capped at 720p, and on Higgsfield it cannot be combined with a first frame [HF].
- **Choose this model when** you need a 10–15 s shot from an approved 9:16 still, or (1.5) references plus one voice. **Choose another model when** you need end frames, editing, reliable in-frame text, or 9:16 guaranteed in reference mode.

| Operation | `grok_video` | `grok_video_v15` |
|---|---|---|
| Text-to-video | Prompt only (`aspect_ratio: "9:16"` available) | Not usable in the fixed format without a 9:16 frame (§2.6): generate a still, then image-to-video |
| Start frame → video | `start_image` (9:16) | `start_image` (9:16), the recommended route |
| Reference-to-video | N/A on Higgsfield | `image_references` (≤7) and/or `audio_references`, without `start_image` [HF]; 9:16 unguaranteed |
| End frame, keyframes, edit, extension | N/A on Higgsfield | N/A on Higgsfield |

