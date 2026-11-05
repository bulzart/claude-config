## 7 The edit (S4)

- `T slideshow plan --run RUN --video NN`: the timeline (`40-briefs/video-NN-timeline.json`: every image with its start, end, motion,
  transition) and the captions on the video's timeline (`60-outputs/video-NN/captions.srt`). Adjust motions, transitions and spans in the
  timeline file when the spec calls for others; `T slideshow render --run RUN --video NN` makes `deliverables/video-NN-clean.mp4` and
  `video-NN-preview.mp4` (the captions burned in the house look: the complete video, 720×1280).
- **Motion**: every still moves a little (the config's amount, about 12 %), the moves of the spec in turn; a cut or a fade as the spec has
  them; effects only as the references use them.
- **The CapCut project** mirrors the timeline (the editable version for a 1080p export; `reference/capcut-assembly.md` §1–§2, §4):
  `T capcut-name`, `capcut_clone_draft`, `T capcut-prep`; each image with `capcut_add_image` at its start for its duration on the main
  track; its move with `capcut_add_keyframe` (UNIFORM_SCALE, KFTypePositionX/Y at the image's start and end); transitions with
  `capcut_add_transition` (names from `capcut_list_transitions`); the narration with `capcut_add_audio` at `lead_s`; the bed with
  `capcut_add_audio` at its gain and `capcut_add_audio_fade`; `capcut_validate`, `capcut_save`; then the captions with capcut-cli
  `capcut import-srt "<draft>" "<RUN>/60-outputs/video-NN/captions.srt"`, and `T capcut-repair --draft "<draft>"` (the house text style,
  register, lint). CapCut's own caption tools stay unused (`capcut-assembly.md` §1).
- Loudness: the render brings the whole to the config's target (about −14 LUFS); in CapCut the narration stays at 1.0 and the bed under it.

