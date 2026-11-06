## 7 The edit (S4)

- `T slideshow plan --run RUN --video NN`: the timeline (`40-briefs/video-NN-timeline.json`: every image with its start, end, motion,
  transition) and the captions on the video's timeline (`60-outputs/video-NN/captions.srt`). Every cut sits on the frame grid, on the
  frame at or just before its line's start, so the render and CapCut cut on the same frame. A caption that would be on screen for less
  than `captions.min_cue_s` (0.2 s, a quick "he" or "of") takes the next word with it, never across a sentence end (`captions_over_words`
  counts them). Its `undecided` lists a move, an amount or a join the plan left out (nothing has a stock value: decide it in the plan, §5),
  `edges_show` an image whose move would show its edge. `T slideshow render --run RUN --video NN` makes `deliverables/video-NN-clean.mp4`
  and `video-NN-preview.mp4` (the captions burned in the references' look): the check copies, at the format's check size (720 on the short
  side). Each still is drawn with an exact sub-pixel resample per frame (ffmpeg's zoompan stepped on whole pixels and the picture shook:
  2026-11-06), with the same values CapCut keys. It counts the frames each file really holds (`video_frames` against `expected_frames`): a
  file's length is its sound's, so only the frames show a lost picture; short of frames it answers `ok` false and exits 1, and those files
  are not used. A join's check copy is the nearest ffmpeg transition; CapCut carries the real one. The plan's effects (§5) are on the
  timeline too (`effects`: each one's start, in point, length and track) and in the check copies: overlays keyed (ffmpeg's chromakey,
  the nearest of CapCut's), blended or overlaid, sized and keyed as planned, and the sounds in the mix before its loudness pass
  (`effects` in the answer counts them).
- **Motion**: the plan's moves and joins (§5), as the references make them; effects only as the references use them (§2).
- **The CapCut project is the final** (the user, 2026-11-05: "export it as the final"): it mirrors the timeline at the format's export
  size, the images at their full size (`reference/capcut-assembly.md` §1–§2, §4): `T capcut-name`, `capcut_clone_draft`,
  `T capcut-prep --draft "<draft>" --canvas <state.json → static.format.export>`; each image with `capcut_add_image` at its start for its duration on the main
  track; the narration with `capcut_add_audio` at `lead_s`; the bed with `capcut_add_audio` at its gain and `capcut_add_audio_fade`;
  `capcut_validate`, `capcut_save` (the last MCP save: the commands after it write the project's files, and a later MCP save would write its
  own copy back over them); then the moves with `T capcut-motion --draft "<draft>" --run RUN --video NN` (KFTypeScaleX with the clip's
  uniform scale on and KFTypePositionX/Y, the timeline's values: CapCut 9.7 ignores UNIFORM_SCALE keyframes, so never
  `capcut_add_keyframe` for a move) and the joins with `T capcut-transitions --draft "<draft>" --run RUN --video NN` (the timeline's
  transition slugs, never `capcut_add_transition`); the effects, when the plan has any, with `T capcut-effects --draft "<draft>" --run
  RUN --video NN` (each overlay on its own video track above the stills, its file copied into the draft, sized, placed and keyed or
  blended by the way the CapCut effects check verified: on this PC an alpha file ffmpeg makes, since CapCut 9.7 ignored capcut-cli's
  chroma key and screen blend; the overlay silent and its sound, when wanted, on an audio track of its own, since CapCut played an
  overlay's sound at volume 0; each sound effect on an audio track at its volume with its fades; it refuses an effect that needs
  something the check did not verify, listed in `refused`: plan that moment again without it, and never write an effect with the
  CapCut MCP); these three and `T capcut-text-anim` take `--run` and refuse an option the catalogue shows CapCut not drawing, or a Pro
  one while the run's CapCut plan is free (`state.json → capcut_plan`); then the captions in the references' look (the plan's `captions`, §2, §5):
  `capcut import-srt "<draft>" "<RUN>/60-outputs/video-NN/captions.srt" --font-size <size> --color <fill> --border-width <stroke_width>
  --border-color <stroke_color> --align 1 --y <1 − 2 × y_rel>`, with `--shadow`, `--bg-color`/`--bg-alpha` and `--highlight-words …
  --keyword-color … --keyword-size …` as the look has them; the font with `T capcut-font --draft "<draft>" --font-file <font_file> --track
  subtitle` (it also writes the outline, box and shadow import-srt set on each caption where CapCut 9.x draws them: the outline into each
  style's strokes, their check_flag bits; without it CapCut shows the words with no outline); the entrance with `T capcut-text-anim --draft
  "<draft>" --track subtitle --intro <captions.animation> --intro-duration <captions.animation_s> --run RUN` (CapCut's own intro on every caption,
  capped at each caption's length); any other text with `capcut add-text`
  in its own look (its font with `T capcut-font ... --track text`, the add-text default); then `T capcut-repair --draft "<draft>" --keep-text`
  (register, the media links CapCut 9.3+ opens a clip by, sync, lint). Never `capcut lint --fix` on a project: besides the links it copies
  every media file into the draft, shortens any text over 7 s and trims captions. **No house text style in Static** (the user, 2026-11-05: "the agents are free to chose any font preset, size, color and family or whatever they like while editing the video and are not constrained like we do with recreate"; "everything is data driven (from the references) and nothing is predefined"):
  `capcut-text-style` is not used and the size, font and colours are the references'. CapCut's own caption tools stay unused
  (`capcut-assembly.md` §1).
- Loudness: the narration file itself is at the config's target (about −14 LUFS; `T tts say`: a gentle voice compressor, then two
  loudnorm passes), because the CapCut project plays it at 1.0 with the bed under it; the render brings its mix to the same target.
- **The export** is the user's, in CapCut (no tool exports a CapCut project): each project at the format's export size, 30 fps; the
  wrap-up says so, and that file is the final.

