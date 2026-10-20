## 1. At a glance

- **Positioning.** "Wan2.6-R2V enables users to upload a character reference video with both appearance and
  voice, utilizing text prompts to generate vivid new scenes starring that same character… a person, animal or
  object, or even multiple subjects together" [OFFICIAL]. The series added "intelligent multi-shot storytelling",
  better audio-visual sync and "video outputs of up to 15 seconds" [OFFICIAL]. Higgsfield describes `wan2_6` as
  "Open-weight, stylized, experimental creative" [HF] — no Wan 2.6 open-weight release was found; Alibaba's
  Wan-Video GitHub publishes Wan2.1 and Wan2.2 base models (plus Wan-Animate-2, Wan-Dancer), nothing from 2.5 onward
  [OFFICIAL] (§9).
- **Best for:** putting one to three referenced characters/objects (appearance + voice from a reference video) into a
  new short scene; stylized looks; 5–10 s clips with auto-generated sound [OFFICIAL/HF].
- **Weaker at:** two generations behind (Artificial Analysis image-to-video with audio, 2026-09-30: #33, Elo 889, vs
  Wan 2.7 #11 and Wan 3.0 #5) [SECONDARY]; readable text [OFFICIAL]; no strict first frame; 1,500-character prompts
  [OFFICIAL]; multi-shot may be locked off (§2.5); cannot regenerate a supplied clip (§3.11).
- **Choose `wan2_6` when** you want its look, a cheap reference-driven draft, or a reference video to supply both
  appearance and voice. **Choose another model when** you need an exact first/last frame (`wan2_7`, `wan3_0`),
  multi-reference precision, Edit Mode or >10 s with references (`wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | upstream `wan2.6-t2v`, 2–15 s [OFFICIAL/INFERRED mapping] |
| Text + audio | `prompt` + `audio_references` | upstream `audio_url` drives the video [OFFICIAL/INFERRED mapping] |
| Reference-to-video | `video_references` and/or `image_references` | upstream `wan2.6-r2v`: character1…N, ≤5 refs, 2–10 s [OFFICIAL/INFERRED mapping] |
| Image as first frame | — | no `start_image` role [HF]; an `image_references` item *might* reach `wan2.6-i2v` as first frame — unverified |
| First/last frame, edit, extension | — | N/A on Higgsfield |

