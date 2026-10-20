## 1. At a glance

- **Positioning.** Released 2026-07-31: "a general-purpose multimodal generation model. H3 understands unified context
  across text, images, video, and audio, generating video with native stereo sound, up to 15 seconds at 2K
  resolution" [OFFICIAL]; open weights on Hugging Face (MiniMax H3 Community License) [OFFICIAL]; "excelling at
  instruction following, accurate text and brand rendering, and V2V motion transfer" [OFFICIAL]; 24 fps, 32 kHz
  stereo, stable dialogue in 11 languages [OFFICIAL].
- **H3 Max** (`MiniMax-H3-Max`): "fast generation variant", 480P/768P, "2K is not supported", 5–15 s [OFFICIAL];
  post-trained by fal "with a particular focus on prompt adherence and visual quality", ~3 s wall time per 5 s clip
  [OFFICIAL, fal as co-developer].
- **Best for:** product, packaging and UI visuals; multi-reference fusion (character + prop + scene + voice + motion);
  V2V motion/camera transfer; regenerating a supplied clip (≤15 s); short intentional in-frame text (§3.11).
  Artificial Analysis (2026-09-30): image-to-video with audio #1 (Elo 1181); text-to-video #4 (768p, Elo 1138)
  [SECONDARY].
- **Weaker at:** "Visual detail can still be improved in certain scenarios" [OFFICIAL]; MiniMax's own production
  skill falls back to Seedance 2.0 for "complex shots, elastic Pixar-style performance, and tension-driven action"
  [OFFICIAL]; it renders text readily, so clean plates need explicit suppression (§3.11).
- **Choose H3** for many references, reference audio, motion transfer, in-frame short text or crisp product detail;
  **H3 Max** for fast 768p drafts and batches. **Choose another model when** you need >15 s or a silent switch
  (`wan3_0`), or demanding action performance.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | upstream requires an explicit ratio (not adaptive) [OFFICIAL] |
| First frame → video | `start_image` | ratio follows the image [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` | FL2VA "favors a single shot" [OFFICIAL] |
| Last frame only | `end_image` | documented inconsistently upstream (§2.5) |
| Reference-to-video | `image_references` (≤9), `video_references` (≤3), `audio_references` (≤3); ≤12 files | exclusive with frame roles [OFFICIAL] |
| V2V motion transfer, Edit Mode regeneration | `video_references` + prompt | upstream capability [OFFICIAL]; Higgsfield routing [INFERRED] |
| Context-IR prompt enhancer, 768p→2K regeneration task | — | N/A on Higgsfield as separate calls [HF] |

