## 7 The edit (S4)

- `T slideshow plan --run RUN --video NN`: the timeline (`40-briefs/video-NN-timeline.json`: every image with its start, end, motion,
  transition) and the captions on the video's timeline (`60-outputs/video-NN/captions.srt`). Adjust motions, transitions and spans in the
  timeline file when the spec calls for others; `T slideshow render --run RUN --video NN` makes `deliverables/video-NN-clean.mp4` and
  `video-NN-preview.mp4` (the captions burned in the house look): the check copies, at the format's check size (720 on the short side).
- **Motion**: every still moves a little (the config's amount, about 12 %), the moves of the spec in turn; a cut or a fade as the spec has
  them; effects only as the references use them.
- **The CapCut project is the final** (the user, 2026-11-05: "export it as the final"): it mirrors the timeline at the format's export
  size, the images at their full size (`reference/capcut-assembly.md` §1–§2, §4): `T capcut-name`, `capcut_clone_draft`,
  `T capcut-prep --draft "<draft>" --canvas <state.json → static.format.export>`; each image with `capcut_add_image` at its start for its duration on the main
  track; its move with `capcut_add_keyframe` (UNIFORM_SCALE, KFTypePositionX/Y at the image's start and end); transitions with
  `capcut_add_transition` (names from `capcut_list_transitions`); the narration with `capcut_add_audio` at `lead_s`; the bed with
  `capcut_add_audio` at its gain and `capcut_add_audio_fade`; `capcut_validate`, `capcut_save`; then the captions in the references' look (the plan's `captions`, §2, §5):
  `capcut import-srt "<draft>" "<RUN>/60-outputs/video-NN/captions.srt" --font-size <size> --color <fill> --border-width <stroke_width>
  --border-color <stroke_color> --align 1 --y <1 − 2 × y_rel>`, with `--shadow`, `--bg-color`/`--bg-alpha` and `--highlight-words …
  --keyword-color … --keyword-size …` as the look has them; the font with `T capcut-font --draft "<draft>" --font-file <font_file> --track
  subtitle`; an animation with `capcut text-anim "<draft>" <id> --intro <animation>` on each caption; any other text with `capcut add-text`
  in its own look (its font with `T capcut-font ... --track text`, the add-text default); then `T capcut-repair --draft "<draft>" --keep-text` (register, lint). **No house text style in Static** (the user, 2026-11-05: "the agents are free to chose any font preset, size, color and family or whatever they like while editing the video and are not constrained like we do with recreate"; "everything is data driven (from the references) and nothing is predefined"):
  `capcut-text-style` is not used and the size, font and colours are the references'. CapCut's own caption tools stay unused
  (`capcut-assembly.md` §1).
- Loudness: the render brings the whole to the config's target (about −14 LUFS); in CapCut the narration stays at 1.0 and the bed under it.
- **The export** is the user's, in CapCut (no tool exports a CapCut project): each project at the format's export size, 30 fps; the
  wrap-up says so, and that file is the final.

