## 1. At a glance

- **Positioning.** A "unified multimodal audio-video joint generation architecture" accepting text, image, audio and video; up to 9 images, 3 video clips and 3 audio clips; 15-second multi-shot output with native audio; released 2026-02 [OFFICIAL S1, S2]. ByteDance's guide calls it "essentially a multimodal AI director" that splits a prompt into a "spatial layer (what is in the frame)" and a "temporal layer (how things change over time)" [OFFICIAL S3].
- **Best for:** reference-driven shots with a consistent person or product (Higgsfield tags: identity, consistent, product, multi-SKU) [HF S6]; `Shot 1 / Shot 2 / Shot 3` storyboards within 4–15 s; motion or camera transfer from a reference clip; voice timbre from an audio reference; Higgsfield Elements [HF S8].
- **Weaker at:** precise timing ("The model's support for precise timing (such as 0–3 seconds) is unstable") [OFFICIAL S3]; multi-view character sheets (ID drift, twins) [OFFICIAL S3]; >4 referenced people [OFFICIAL S3]; "detail stability, hyper-realism, and dynamic vitality … multi-subject consistency, text rendering accuracy, and complex editing effects", occasional audio distortion [OFFICIAL S2]; multi-speaker lip sync [OFFICIAL S4].
- **Choose this model when** you need ≤15 s with strong identity/product locking from a few references, Elements, or the 2.0 look (2.5 has "significantly different aesthetic style preferences") [OFFICIAL S5].
- **Choose another model when** you need >15 s, timestamp-exact beats, an edit or extension of a supplied clip, more than 9/3/3 references or multi-view sheets — use Seedance 2.5.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"seedance_2_0"`, no `medias` | |
| First frame / first + last frame | roles `start_image` (+ `end_image`) | ratio may be set or follow the image [OFFICIAL S7] |
| Multi-reference (R2V) | `image_references`, `video_references`, `audio_references` | cited as `@Image1`, `@Video1`, `@Audio1` |
| Elements | `<<<element_id>>>` in the prompt | Seedance 2.0 is Elements-capable on Higgsfield [HF S8] |
| Video edit / extension | N/A on Higgsfield (no mode) | available on ModelArk 2.0 [OFFICIAL S3]; use `seedance_2_5` |

