## 5. Media roles — how the catalog names them

| Role (catalog) | Meaning | Models (2026-09-30) |
|---|---|---|
| `start_image` / `end_image` | First / last frame anchors | Seedance 1.5/2.0/2.5, Kling 3.0 (end too), Kling 3.0 Turbo / 2.6 / Happy Horse / Grok (start only), Veo 3 / 3.1 (start only), Veo 3.1 Lite, Wan 2.7 / 3.0, MiniMax H3 / Hailuo, FLUX 3 Video, Gemini Omni 1.1, Cinema Studio |
| `image` | Generic image input | Cinema Studio (all), Marketing Studio, `higgsfield_preset` |
| `image_references` | Identity, product, prop or scene references | Seedance 2.0/2.5, Wan 2.6 / 3.0, MiniMax H3, FLUX 3 Video, Gemini Omni, Grok 1.5, Kling Omni Edit, Genjutsu |
| `video_references` | Motion, camera or timing reference, or the source video to edit or extend | Seedance 2.0/2.5, Wan 2.6 / 3.0, MiniMax H3, FLUX 3 Video (+ Edit), Gemini Omni, Kling Omni Edit, Genjutsu |
| `audio_references` | Voice, music or sound reference | Seedance 2.0/2.5, Wan 2.6 / 2.7 / 3.0, MiniMax H3, Grok 1.5 |
| `input_video` / `input_audio` | Utility inputs | `sync_so` lipsync, `video_upscale`, `video_deflicker` |

- The server auto-coerces unambiguous roles. Higgsfield's own recipes pass `"video"` / `"image"`, and
  stored params show `"audio"` for an audio reference [VERIFIED]. Prefer the exact catalog role names.
- **Order matters.** Prompt tags such as `@Image1`, `@Video1` and `@Audio1` count per media type in
  `medias` order (Seedance convention; see each model guide for its own tag syntax). In edits, the
  source video goes first and images follow in `@ImageN` order [HF-DOC].
- Hidden stored keys (`multi_shots`, `speedramp`, `reference_elements`, `prompt_language`, …) appear
  in stored params as server defaults. Do not set them unless a model guide says they are honoured.

