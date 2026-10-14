## 1. At a glance

- **What it is.** "Gemini Omni Flash is our next step towards models that can create and edit anything from any input—starting with video" [OFFICIAL: model card]. It is a transformer with "native multimodal support for text, vision, video and audio inputs" [OFFICIAL]. It was announced at Google I/O on 2026-05-19 [OFFICIAL: blog.google].
- **Name mapping (evidence-based).**
  - `gemini_omni` = Gemini Omni Flash preview, `gemini-omni-flash-preview`. Released to the Gemini API on 2026-06-30 for "3–10 second videos at 720p". Google states it "only supports '720p'", which matches the Higgsfield entry [OFFICIAL][HF].
  - `gemini_omni_flash_1_1` = Gemini Omni 1.1 Flash, `gemini-omni-1.1-flash` (GA 2026-08-27; Agent Platform `gemini-omni-1.1-flash-preview`). Its resolutions (360p/720p/1080p/4k) and `mode` values (`text_to_video`, `image_to_video`, `reference_to_video`, `edit`) match Google's `task` [OFFICIAL][HF]. The model card "describes Gemini Omni Flash and Gemini Omni 1.1 Flash" [OFFICIAL]. Higgsfield writes the version after "Flash"; same model.
- **Lifecycle warning.** "The existing gemini-omni-flash-preview endpoint will be deprecated on September 30, 2026" (today) on the Gemini API [OFFICIAL]. The Agent Platform lists retirement on 2027-06-30 [OFFICIAL]. Prefer `gemini_omni_flash_1_1`; re-check the catalog before using `gemini_omni` [INFERRED].
- **Best for:**
  - Edit Mode: removing, swapping, restyling or relighting inside a supplied clip [OFFICIAL];
  - reference-driven generation [OFFICIAL];
  - world knowledge and physics [OFFICIAL];
  - short in-scene text that is actually wanted [OFFICIAL, with caveats];
  - 10-second clips [HF].
- **Weaker at:**
  - "maintaining complete consistency throughout edits, generating scenes with complex motion, or rendering perfectly accurate text" [OFFICIAL: model card];
  - multi-element interaction edits [HF];
  - peak photoreal quality compared with Veo 3.1 [HF];
  - it cuts to several shots by default [OFFICIAL].
- **Choose this model when** you need an edit of a supplied clip that keeps its motion, reference-based identity or product placement, or short scene text. **Choose another model when** you need clips over 10 s, edit sources over 10 s, audio references, new dialogue inside an edit (speech editing is restricted [OFFICIAL]), or maximum photoreal fidelity.

| Operation | `gemini_omni` | `gemini_omni_flash_1_1` |
|---|---|---|
| Text-to-video | prompt only; the model infers the task [OFFICIAL] | `mode:"text-to-video"` |
| Start (+ end) frame | Only via `image_references` plus "Use this image as the starting frame." [OFFICIAL wording; honouring unverified] | `mode:"image-to-video"` + `start_image` (+ `end_image`) |
| Reference-to-video | `image_references` / `video_references` | `mode:"reference-to-video"` |
| Video edit (Edit Mode) | `video_references` = source + edit instruction | `mode:"edit"` + `video_references` (+ optional `image_references`) |
| Extension, multi-turn, audio references | N/A on Higgsfield | N/A on Higgsfield |

