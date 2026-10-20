## 1. At a glance

- **Positioning.** "The new-generation video creation model", built on the "unified multimodal audio-video joint-generation architecture" of Seedance 2.0 [OFFICIAL S1, S10], centred on "foundational generation and reference-based generation" with breakthroughs in "long-form storytelling, multimodal reference, and editing"; launched 2026-07-31 [OFFICIAL S1]. Up to 30 s per generation, up to 50 references (≤30 images, ≤10 videos, ≤10 audio), native audio in 11 languages [OFFICIAL S2, S3]. ByteDance calls it "not a cross-generational leap" over 2.0 but "systematic enhancements for real production scenarios" [OFFICIAL S2].
- **Best for:** scripted single-pass clips up to 30 s with integer-second timeline control; multi-reference casting (identity + product + scene + motion clip + voice); scoped edits of real footage (replace a product or person, remove captions/watermarks/objects, change background, audio edits and dubbing); extension; keyframe, storyboard and clay-model control [OFFICIAL S1, S2, S3].
- **Weaker at:** "the physical plausibility of complex motions and the stability of scenes involving interactions among multiple subjects" [OFFICIAL S1]; exact spelling of rendered text [OFFICIAL S2]; guaranteed subtitle-free and music-free output [OFFICIAL S2]; high-frequency actions under timestamps [OFFICIAL S2]; crowded frames (>4 people, 2.0 guidance) [OFFICIAL S6].
- **Choose this model when** the clip exceeds 15 s, needs many bound references, needs an edit or extension of an existing clip (including source-text removal), dubbing, or keyframe/storyboard/blockout control.
- **Choose another model when** you need Higgsfield Elements (listed for Seedance 2.0 and Kling 3.0, not 2.5), a one-object swap that must pass source audio and untouched pixels through (Genjutsu `hf_mult_replace_object` keeps source audio [HF S15]), or a short simple shot where 2.5's structure adds nothing.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `mode:"t2v"`, no `medias` | ratio and duration free [OFFICIAL S3] |
| First / first + last frame | roles `start_image` (+ `end_image`) | ratio locked to the first frame [OFFICIAL S2]; `mode` for this path undocumented (§2.5) |
| Omni reference, keyframes, storyboard, clay blockout | `mode:"omni_reference"` + `image_references` / `video_references` / `audio_references` | assets cited as `@ImageN` / `@VideoN` / `@AudioN` |
| Video edit | `mode:"video_edit"`, exactly one video (+ images) | length and ratio follow the source; billed by source duration [HF S11] |
| Video extension | `mode:"video_extension"` + `extension_mode` | ratio follows the source; `duration` = new segment [HF S11] |
| Draft → final | `draft:true` (480p) → `draft_job_id` (1080p) | `seedance_2_5` only; not the default path (§2.6) |
| Ad Multiplier recipe | `model:"ad_multiplier"`, `mode:"video_edit"`, silent + local audio restore | Higgsfield's production edit contract [HF S13] |

