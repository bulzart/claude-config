## 1. At a glance

- **Positioning.** Launched April 2026 as "a comprehensive video generation model" with "director-level control",
  2–15 s at 720p/1080p, 30 fps [OFFICIAL]. Upstream ids `wan2.7-t2v` (snapshots 2026-04-25, 2026-06-12) and
  `wan2.7-i2v` (2026-04-25) [OFFICIAL]. Higgsfield: "Synchronized audio, character-consistent video" [HF].
  Superseded by Wan 3.0 as Alibaba's flagship [OFFICIAL].
- **Best for:** 5–15 s clips with native audio (auto-generated, or driven by your own track for lip sync and action
  timing) [OFFICIAL]; animating an approved 9:16 still; bridging two approved frames; multi-shot storyboards from
  one prompt [OFFICIAL]; expressive faces ("over 50 refined emotional expressions") [OFFICIAL].
- **Weaker at:** readable text ("Text renders approximately") [OFFICIAL]; exact lip sync; long choreography; orbits
  wider than ~45° [OFFICIAL]. No reference images or video input on Higgsfield, so identity comes only from the start
  frame or text, and Edit Mode is not possible.
- **Benchmarks:** Artificial Analysis (2026-09-30): text-to-video #12 (Wan2.7-260612, Elo 1029), image-to-video with
  audio #11 (Elo 1077) [SECONDARY].
- **Choose `wan2_7` when** a shot starts (and optionally ends) on approved 9:16 frames and needs synced audio or an
  uploaded voice/music track. **Choose another model when** you need reference images (`wan3_0`, `minimax_h3`), a
  supplied clip regenerated (`wan3_0`), >15 s, or a silent render switch (`wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | multi-shot controlled in the prompt [OFFICIAL] |
| Text + audio | `prompt` + one `audio_references` | upstream `audio_url`; audio drives the video [OFFICIAL/INFERRED mapping] |
| First frame → video | `start_image` | output aspect follows the image [OFFICIAL] |
| First frame + audio | `start_image` + `audio_references` | upstream `driving_audio`: "lip-sync and action timing" [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` (+ optional audio) | all three may be combined upstream [OFFICIAL] |
| Reference-to-video, video edit, continuation | — | N/A on Higgsfield (no reference or video roles) [HF] |

