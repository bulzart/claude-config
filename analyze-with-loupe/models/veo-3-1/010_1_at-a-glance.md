## 1. At a glance

- **Positioning.** "Veo 3.1 is a model for generating 8-second videos (720p, 1080p, or 4k) with natively generated audio" [OFFICIAL: Gemini API]. Google Cloud: Veo 3.1 builds on Veo 3 "with stronger prompt adherence and improved audiovisual quality when turning images into videos" [OFFICIAL: Cloud blog]. Veo 3.1 Lite: "Google's most cost-effective video model", at "less than 50% of the cost of Veo 3.1 Fast, but with the same speed" [OFFICIAL: blog.google]. Higgsfield labels: `veo3_1` "Ultra-realistic, top-tier cinematic quality"; `veo3_1_lite` "Fast, affordable, budget batch clips" [HF].
- **Lifecycle warning.** On the Gemini API, `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview` and `veo-3.1-lite-generate-preview` list shutdown **2026-10-22**, replaced by `gemini-omni-1.1-flash` [OFFICIAL: deprecations page, updated 2026-09-30]. The Agent Platform GA ids list "November 17, 2026 or later"; Lite is Preview [OFFICIAL]. Higgsfield does not publish its backend, so re-check `models_explore` before each run [INFERRED].
- **Best for:**
  - photoreal single shots with synchronized dialogue, SFX and ambience [OFFICIAL];
  - direction through film vocabulary; Google calls cinematography "the most powerful tool for conveying tone and emotion" [OFFICIAL];
  - animating a prepared 9:16 start frame;
  - timestamped mini-sequences inside 8 s [OFFICIAL];
  - cheap drafts on Lite.
- **Weaker at:**
  - generated text: Veo 3 is "still poor at generating text" [OFFICIAL: tech report];
  - consistency in complex scenes or motion [OFFICIAL: model card];
  - subtitle artifacts on dialogue [SECONDARY];
  - short speech segments [OFFICIAL];
  - anything over 8 s;
  - reference-based identity (not exposed) [HF].
- **Choose this model when** the shot fits 4–8 s, photoreal quality with native audio matters, and exact products or people arrive via a clean start frame. **Choose another model when** you need reference images, video editing (Edit Mode), clips over 8 s, reliable in-frame text, or several consecutive actions.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | `veo3_1` / `veo3_1_lite`, no `medias` | 4/6/8 s [HF] |
| Start frame → video | `start_image` on either id | The image becomes the first frame [OFFICIAL] |
| First + last frame | `veo3_1_lite` with `start_image` + `end_image` | `veo3_1` has no `end_image` role [HF] |
| Reference images, extension, add/remove object, edit | N/A on Higgsfield | Google-native only [OFFICIAL][HF] |

