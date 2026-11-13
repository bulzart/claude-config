## 7 The edit (S4)

- `T slideshow plan --run RUN --video NN`: the timeline (`40-briefs/video-NN-timeline.json`: every image with its start, end, motion,
  transition) and the captions on the video's timeline (`60-outputs/video-NN/captions.srt`). Every cut sits on the frame grid, on the
  frame at or just before its line's start, so CapCut cuts on that frame. A caption that would be on screen for less
  than `captions.min_cue_s` (0.2 s, a quick "he" or "of") takes the next word with it, never across a sentence end (`captions_over_words`
  counts them). Its `undecided` lists a move, an amount or a join the plan left out (nothing has a stock value: decide it in the plan, §5),
  `edges_show` an image whose move would show its edge. The plan's effects (§5) are on the timeline too (`effects`: each one's start, in
  point, length and track). So are the plan's **drawings** (§5 "Drawings"): each clip `T draw render --run RUN --video NN` made and
  left current is an overlay entry on a track of its own (`draw1`, `draw2` …; `drawings` in the timeline file), and the answer lists
  `drawings_not_rendered` (no clip, or one older than its spec), `drawings_on_moving_images`, `drawings_past_their_image`,
  `drawings_in_caption_band` and `drawings_undecided`: facts to fix in the plan, never changed here.
- **No local render** (the user, 2026-11-07: "no need to generate a ffmpeg video simulation version, just do it in capcut directly"):
  the timeline goes straight into the CapCut project; no check copies and no capcut-cli proxy preview are made, and the edit's checks
  read the project back (§8). (`T slideshow render` still exists for a local copy the user asks for: at the format's check size, each
  still drawn with an exact sub-pixel resample per frame, the captions burned in, the frames counted.)
- **Motion**: the plan's moves and joins (§5), as the references make them; effects only as the references use them (§2). They sit on
  the blueprint's beats (§4b: the push-ins at dread, scale and a reveal's first still, the dips at the chapters, a story sound where
  the story names one, from the user's sounds folder and never a meme or a death sound, the silence or dip before a reveal) and were
  decided when the plan was written (§5, §6): the edit builds what the plan decided, and J5 confirms it; nothing is invented here to
  liven a stretch the plan left plain.
- **The CapCut project is the final** (the user, 2026-11-05: "export it as the final"): it mirrors the timeline at the format's export
  size, the images at their full size (`reference/capcut-assembly.md` §1–§2, §4): `T capcut-name`, `capcut_clone_draft`,
  `T capcut-prep --draft "<draft>" --canvas <state.json → static.format.export>`; each image with `capcut_add_image` at its start for its duration on the main
  track; the narration with `capcut_add_audio` at `lead_s`; the bed with `capcut_add_audio` at its gain (its fades are in the file: no
  `capcut_add_audio_fade`, which would fade it twice);
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
  CapCut MCP); the **drawings** are in the same timeline list and go in by the same command, each clip on its track `draw1`, `draw2` …
  as an overlay with its own transparency (the QuickTime Animation, PNG-in-MOV or ProRes 4444 file the catalogue lists as playing
  here), covering the canvas, silent, above the stills and below the captions (§5 "Drawings"); these three and `T capcut-text-anim` take `--run` and refuse an option the catalogue shows CapCut not drawing, or a Pro
  one while the run's CapCut plan is free (`state.json → capcut_plan`); then the captions in the run's text look, the same in every video
  of the run (the plan's `captions`, §2, §5, §10):
  `capcut import-srt "<draft>" "<RUN>/60-outputs/video-NN/captions.srt" --font-size <size> --color <fill> --border-width <stroke_width>
  --border-color <stroke_color> --align 1 --y <1 − 2 × y_rel>`, with `--shadow`, `--bg-color`/`--bg-alpha` and `--highlight-words …
  --keyword-color … --keyword-size …` as the look has them; the font with `T capcut-font --draft "<draft>" --font-file <font_file> --track
  subtitle` (it also writes the outline, box and shadow import-srt set on each caption where CapCut 9.x draws them: the outline into each
  style's strokes, their check_flag bits; without it CapCut shows the words with no outline); the entrance with `T capcut-text-anim --draft
  "<draft>" --track subtitle --intro <captions.animation> --intro-duration <captions.animation_s> --run RUN` (CapCut's own intro on every caption,
  capped at each caption's length). **With a `word_box`** (the user, 2026-11-09: "for every word that is spoken at the moment the narrator
  is speaking ... a color behind the word and a round radius"): CapCut draws a box behind a whole text only, so the captions are built
  instead by `T capcut-word-box --draft "<draft>" --run RUN --video NN [--replace subtitle]`: one text per word at its place on the
  centred line (the font's advances at CapCut's em, measured on its own 16:9 render), the box on the word the narration's word times say
  is spoken, the others plain, no keyword colour (`highlight_words` empty: a coloured word on its box would vanish). **The box's colour is the
  video's own** (the user, 2026-11-12: "make it so that it is dynamic and in accordance with the video's colors and not fixed"): `word_box.color`
  is chosen for each video from that video's own palette, never copied from the last video's plan. A first pick is written at A6s from the
  style lock's palette; J5 settles it once the stills exist, from their dominant and accent colours (a few viewed stills or a scratch colour
  reading: facts for the judge's call): a colour of the video's palette that still stands out from the pictures behind the caption band (white
  word, black outline and box all legible; a box near the picture's own colour would vanish), its reason and the colours it was read from in
  `word_box.why`. The shape (radius, pad, gap, v_offset), the font and the size stay the run's text look; then `T capcut-font`
  on every `wordcap-*` track and `T capcut-text-anim` only on the tracks ending in `-in` (a cue's entrance: a word that takes or hands
  on the box never pops again). The labels, when the timeline has any (a map's place names, §5 "Labels"), with `T capcut-labels
  --draft "<draft>" --run RUN --video NN` (each on the track "labels" over its image's span, labels shown at once on tracks of their own: labels-2, …; its centre where the plan put it, in the
  plan's `labels_style`, its font with them; once per build); any other text with `capcut add-text`
  in its own look (its font with `T capcut-font ... --track text`, the add-text default); then `T capcut-repair --draft "<draft>" --keep-text`
  (register, the media links CapCut 9.3+ opens a clip by, sync, lint). Never `capcut lint --fix` on a project: besides the links it copies
  every media file into the draft, shortens any text over 7 s and trims captions. **No house text style in Static** (the user, 2026-11-05: "the agents are free to chose any font preset, size, color and family or whatever they like while editing the video and are not constrained like we do with recreate"; "everything is data driven (from the references) and nothing is predefined"):
  `capcut-text-style` is not used and the size, font and colours are the references'. CapCut's own caption tools stay unused
  (`capcut-assembly.md` §1).
- **Fonts** (the user, 2026-11-07: "the capcut looks like returned the font back to default one ... fix this"): a project shows a text
  in its font only while the font file stays where the project points, and CapCut keeps neither of its own folders still: its version
  folder (the fonts it bundles) is replaced by an update, its cache (the fonts it downloads for templates) may be cleared, and a text
  whose file is gone shows in CapCut's default font. So the captions' and labels' `font_file` is a copy in the library's `fonts/`
  folder: `T capcut-font --list` lists it first and gives every font's `kept_by`; a font from CapCut's cache under an open licence
  (SIL Open Font License) is copied there first with its row in `fonts/README.md`, one whose licence is not known is not used.
- **Extra fonts** (the user, 2026-11-11: "add a permission for the agents to download extra fonts on capcut if the available ones do
  not seem a good match for the video"): when no font of `T capcut-font --list` is a good match for the video, the agent may
  download another, whenever it needs one (the plan's text look at A6s, a drawing's lettering at S3, a script the listed fonts lack at
  S4). What it may fetch is a font file under an open licence, the SIL Open Font License 1.1 or the Apache License 2.0 (the library's
  rule, `fonts/README.md`); one whose licence is not confirmed is not used. CapCut's own cloud fonts can be downloaded only by CapCut's
  app, which no tool here drives, so the files come from the open font source: `T fetch-font --family "<Family>" [--weight 700]
  [--subset latin] [--text <the video's texts>] --why "<which video and why the listed fonts do not fit>"` reads the family's
  licence, subsets and weights from Fontsource, takes the subset whose file holds every character of `--text`, refuses any other
  licence, never overwrites a file, copies the font into the library's `fonts/` folder with its row in `fonts/README.md` (file,
  family, licence, source, subset, the run) and answers with its full path and `font_missing_glyphs`; a font from another open
  source is added with `--url … --licence … --licence-source …`. The font is then used as any library font (`T capcut-font
  --font-file <it>`) and named in the brief with the reason; the choice of the family is the agent's: it views a specimen against the
  references' lettering and the video's tone before it takes one.
- **Captions in another language** (the user, 2026-11-11: the video's language, §6; the captions are the narration's own words, never
  the glosses): the SRT is made from the heard words of the narration in the video's language. A language written with spaces is
  grouped by `captions.words` as before; one written without them (Japanese, Chinese, Thai, Lao, Khmer, Burmese; `T static language
  --language <code>` says `spaced: false` and its unit) is grouped by `captions.chars`, the characters a caption holds (config
  `static.captions.chars_unspaced` when the plan has none), at the characters' times, and its `highlight_words` is left empty (a word is
  not a separate token there). `case: "upper"` changes only letters that have a case (the Turkish and Azerbaijani dotted i first); a script
  without case stays as it is. The font holds a glyph for every character of the captions and the labels: `T capcut-font`, `T
  capcut-labels` and `T capcut-word-box` list `font_missing_glyphs` (the characters the file lacks; a font whose character table is in a format the reader does
  not know, only cmap formats 4 and 12 are read, gives `font_glyphs_error` instead: look at the text in that font or pick another),
  and a font that lacks some is replaced for that video's texts by another file of `T capcut-font --list` (kept under `fonts/` first, as Fonts says), the reason in the
  plan. **The word box** places a row of words one by one from left to right, so for a language written without spaces or from right to
  left `T capcut-word-box` stops with `word_box_supported: false` and its reason, and the video takes the plain caption look by
  `capcut import-srt` as above (the run's font, size, outline, colours and entrance), named in the brief and the record; the box comes
  back on the next video in a language it can place. Nothing here renders a project (no local render), so how CapCut shapes a right-to-left
  or joined script is the user's first look at it, which the wrap-up names.
- **An extra format** (§2b): its own CapCut project by the same steps, each command with `--format <tag>`:
  `T slideshow plan` (its timeline `40-briefs/video-NN-timeline-<tag>.json`: the same cuts, moves, joins and effects, its own stills,
  labels, aimed zooms and caption size and band; its `undecided` lists what its `by_format` still lacks), `T capcut-name` (the name
  ends `-<tag>`), `T capcut-prep --canvas <that format's export>`, its stills from `60-outputs/video-NN/<tag>/images/`, the same
  narration and bed, `T capcut-motion`, `capcut-transitions`, `capcut-effects` and `capcut-labels` with `--format <tag>`, and its
  captions from `60-outputs/video-NN/<tag>/captions.srt` at the timeline's `size` and `y_rel`, in the run's font, outline, colours and
  entrance.
- Loudness: the narration is ElevenLabs' delivered audio (the user, 2026-11-09: "do not edit the delivered generation without any
  exception": no compressor, loudness pass or fade), but for the level rule (§6: one constant gain only when it sits outside the
  references' measured loudness, never past -1 dBTP) and a capped speed-up the user said yes to after delivery (§6, §13 J2); its loudness is recorded
  (`loudness_lufs`, `true_peak_db` and `level` in the narration's sidecar), the CapCut project plays it at 1.0, and the bed sits under it at the plan's gain, judged
  against the narration as it is (§6 "The bed's check and level").
- **The export** is the user's, in CapCut (no tool exports a CapCut project): each project at its format's export size, 30 fps; the
  wrap-up says so, and that file is the final.

