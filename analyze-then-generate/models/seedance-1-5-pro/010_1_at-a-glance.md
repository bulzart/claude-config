## 1. At a glance

- **Positioning.** "A foundational model purpose-built for native, joint audio-video generation. It adopts a dual-branch Diffusion Transformer architecture, combining a cross-modal fusion module with a specialized multi-stage data pipeline" [OFFICIAL S1]; the report adds SFT + RLHF, >10× faster inference, "precise multilingual and dialect lip-syncing", "dynamic cinematic camera control" and "enhanced narrative coherence" [OFFICIAL S2].
- **Highlights claimed:** "monologues and multi-speaker conversations with millisecond-level lip-sync precision"; Mandarin plus Cantonese, Shaanxi and Sichuan dialects, English, Japanese, Korean, Spanish, Indonesian; "film- and television-grade narrative tension" [OFFICIAL S1].
- **Best for:** short 4/8/12 s dialogue or voice-over clips from text or one start frame; shot/reverse-shot conversations inside one clip; animating an approved still with sound [OFFICIAL S1].
- **Weaker at / absent:** no reference images, video or audio [OFFICIAL S3; HF S5]; no documented timestamp control [OFFICIAL S8]; only 4/8/12 s on Higgsfield [HF S5]; no text-rendering claims; retired upstream [OFFICIAL S4].
- **Choose this model when** a quick, reliable start-frame or text shot with native dialogue fits 4, 8 or 12 s and needs no references.
- **Choose another model when** you need references (Seedance 2.0/2.5), >12 s or precise beats (Seedance 2.5), edits/extensions (Seedance 2.5), or in-frame text (Seedance 2.5 with a text image, or Kling 3.0).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"seedance1_5"`, no `medias` | 4, 8 or 12 s |
| First frame to video | role `start_image` | ratio may be set or follow the image [OFFICIAL S3] |
| First + last frame | `start_image` + `end_image` | same ratio for both |
| Reference, edit, extension | N/A on Higgsfield | not supported by the model [OFFICIAL S3] |

