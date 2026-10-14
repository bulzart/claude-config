## 1. At a glance

- **Positioning.** "Veo 3 is a video generation system capable of synthesizing high-quality, high-resolution video with audio from a text prompt or input image" [OFFICIAL: model card]. It "lets you add sound effects, ambient noise, and even dialogue… generating all audio natively" [OFFICIAL: DeepMind]. Higgsfield: "Reliable cinematic, broad creative range" [HF].
- **Lifecycle warning.** Google shut down `veo-3.0-generate-001` and `veo-3.0-fast-generate-001` on the Gemini API on 2026-06-30 and recommends the Veo 3.1 ids [OFFICIAL: deprecations, changelog]. The Agent Platform also lists 2026-06-30 retirement [OFFICIAL]. The Higgsfield catalog still lists `veo3` [HF], and the backend now answering it is unpublished. **Prefer `veo3_1` for new work**; use `veo3` only when explicitly selected, and verify outputs [INFERRED].
- **Best for:** cinematic realism with synchronized sound; strong prompt adherence ("performed best on overall preference, and for its capability to follow prompts accurately") [OFFICIAL]; cheap variations on `veo-3-fast` [HF].
- **Weaker at:**
  - text ("still poor at generating text", "prone to small hallucinations") [OFFICIAL: tech report];
  - unwanted cuts ("a bias for generating cinematic footage, with frequent camera cuts and dramatic camera angles") [OFFICIAL];
  - consistency in complex scenes or motion [OFFICIAL: model card];
  - garbled subtitles on dialogue [SECONDARY];
  - no controls beyond prompt and start frame [HF].
- **Choose this model when** Veo 3 is explicitly requested, or a quick cinematic clip with native audio is enough. **Choose another model when** you need end frames, references, editing, legible text, a chosen duration, or long-term availability.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | `veo3`, no `medias` | Length not selectable [HF] |
| Start frame → video | `start_image` | The image is used as the initial frame [OFFICIAL] |
| End frame, references, extension, edit | N/A on Higgsfield | Not exposed [HF] |

