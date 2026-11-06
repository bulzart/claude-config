## 1. At a glance

- **Positioning.** "Kling 4.0 is a next-generation native multimodal AI model for video creation. It delivers more stable complex motion, stronger consistency across diverse references, and more coherent, precise, and controllable storytelling." [OFFICIAL S1, user guide dated 2026-11-04]. Headline specs: 3–30 s in one generation, "Multi-shot is enabled by default", up to 10 keyframes, Omni Reference with up to 15 assets (10 images, 5 videos ≤30 s total, 7 elements, 3 voice profiles), two-channel stereo audio, nine speech languages with dialects and accents, "clear and stable generation of multilingual text, emojis, and logos", prompts "up to 8,000 tokens" [OFFICIAL S1]. On Higgsfield since 2026-10-20 [HF S4].
- **Best for:** one-pass takes up to 30 s, long continuous shots or auto-cut multi-shot stories; fast and complex motion ("high-speed movement, continuous action, tracking shots, or orbit shots, footage stays stable and seamless") [OFFICIAL S1]; casting people, products and scenes from up to 10 reference images; borrowing a reference video's camera path, action timing or pacing; "Creative Recreation" of a proven video with your own product or character; instruction edits of a supplied clip that keep "the rest of the scene stable"; dialogue with lip sync in nine languages [OFFICIAL S1].
- **Weaker at / watch:** audio is always generated, with no switch [OFFICIAL S1; HF S2]; the model "may add" subtitles and background music by default [OFFICIAL S1]; shots are split automatically by default, so a single take must be asked for [OFFICIAL S1; INFERRED]; no negative-prompt field [HF S2; SECONDARY S6]; voice profiles, middle keyframes, 4K and HDR are not reachable through the Higgsfield roles and parameters [HF S2]; frames and references cannot be combined in one task [OFFICIAL S1]; no independent failure testing was found for a model this new [INFERRED gap].
- **Choose this model when** a take must run 15–30 s in one generation, when several references (people, product, scene, a camera or action video) must work together, when a reference video is recreated with a swapped product or character, or when a supplied clip needs a targeted edit.
- **Choose another model when** the output must be silent with no post step, when a voice or music file must drive the result (no audio role here), or when a pixel-exact start frame and reference images are both needed in one call.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `mode:"text-to-video"`, no `medias` | 3–30 s; the model expands a short prompt [OFFICIAL S1] |
| Start frame to video | `mode:"image-to-video"`, `start_image` | aspect follows the first keyframe [OFFICIAL S1] |
| Start + end frame | `image-to-video`, `start_image` + `end_image` | "Showing transformation processes, craftsmanship, and before-and-after comparisons" [OFFICIAL S1] |
| End frame only | `end_image` alone | supported by Kling ("Use @Image1 as the last frame") [OFFICIAL S1]; unverified on Higgsfield (§9) |
| Middle keyframes (Kling: up to 10) | no media role for them on Higgsfield | the catalog says "ordered keyframes" and tags `keyframes`, but lists only `start_image` / `end_image` [HF S2] (§9) |
| Reference-to-video (Omni Reference) | `mode:"reference-to-video"`, `image_references` (≤10), `video_references` (≤5, ≤30 s total), `kling_element_ids` (≤7) | cite as `@Image1`, `@Video1`, `@Element1` [OFFICIAL S1]; Higgsfield numbering by `medias` order [INFERRED] |
| Creative Recreation (product / character swap in a reference video) | `reference-to-video`, the source in `video_references` + the new item in `image_references` | "Replace the element in @Video1 with @Image1. Keep everything else unchanged." [OFFICIAL S1]; mode choice [INFERRED] |
| Action / camera transfer | `reference-to-video` with `video_references` | "Reference the fighting moves and attack timing in @Video1" [OFFICIAL S1]; no separate motion-control mode |
| Video edit | `mode:"video-edit"`, `video_references` (primary first) + optional `image_references` / elements | the prompt must say "Edit @Video1" [OFFICIAL S1] |
| Voice profile reference | N/A on Higgsfield (no audio role) [HF S2] | Kling: up to 3 voice profiles [OFFICIAL S1] |
| Video extension | N/A | Kling: "Extend videos multiple times, up to 2 minutes" is "(Coming soon)" [OFFICIAL S1] |
| Multi-shot | on by default; shots written in the prompt | no switch or per-shot fields on Higgsfield [HF S2] |

Higgsfield also runs Kling 4.0 behind `hf_mult_replace_object_flash` ("Genjutsu Lite", "Replace objects in a source video using reference images (Kling 4.0)") [HF S2]; that id has its own parameters and is not covered here.

