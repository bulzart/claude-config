---
name: awl-static-edit
description: /analyze-with-loupe Static step S4: the timeline, the CapCut project made directly (the final, at the run's format; no local render) and the edit checks. Internal to that command.
user-invocable: false
---

# awl-static-edit — Static step S4: the edit

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §7: `AWL/reference/static/070_7_the-edit-s4.md` (10.6 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (8.6 KB)
- capcut-assembly §1: `AWL/reference/capcut-assembly/010_1_tools-and-rules.md` (3.3 KB)
- capcut-assembly §2: `AWL/reference/capcut-assembly/020_2_create-the-project.md` (0.8 KB)
- capcut-assembly §4: `AWL/reference/capcut-assembly/050_4_after-every-save-capcut-cli.md` (3.2 KB)
- capcut-assembly §5: `AWL/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.9 KB)
- *the run has more than one format (`state.json → static.extra_formats`):*
  - static §2b: `AWL/reference/static/025_2b_more-than-one-format.md` (4.5 KB)

## Step S4

0. **The judge's record first** (static §13, J5): read `RUN/40-briefs/video-NN-judge.md`: the moves, joins, labels and the bed's level
   decided and forecast for this video are what the project carries; a value the timeline gives that differs from the record is traced
   to its cause and named in the brief before the project is built (nothing lands by accident).
1. **The timeline:** `T slideshow plan --run RUN --video NN` → `RUN/40-briefs/video-NN-timeline.json` and the captions on the video's
   timeline (`RUN/60-outputs/video-NN/captions.srt`; a word that would flash for under `captions.min_cue_s` shares its cue with the next,
   `captions_over_words`). Read `image_spans` (every cut on the frame grid), `moves`, `effects`, `undecided`, `edges_show`,
   `shorter_than_0_5s` and `images_without_a_file`: a gap, an undecided move, join or effect setting, or an edge that shows is fixed in the
   image plan (static §5: every value is decided there from the spec's measured pattern, the CapCut catalogue and, for effects, the effects
   folder's facts; there is no stock value) or in the images, then plan again.
2. **No local render** (the user, 2026-11-07: "no need to generate a ffmpeg video simulation version, just do it in capcut directly"):
   the edit is made in CapCut straight from the timeline; no `T slideshow render`, no check copies in `deliverables/` and no capcut-cli
   proxy preview. The checks read the project itself (step 4).
3. **The CapCut project** (static §7; capcut-assembly §1, §2, §4):
   - `T capcut-name --video NN`, `capcut_clone_draft` (the template, empty), `T capcut-prep --draft "<draft>" --canvas <state.json →
     static.format.export>` (the project's canvas is the format's export size), `capcut_read_timeline`;
   - each image of the timeline with `capcut_add_image` (`atSec` its start, `durSec` its span, on the main track);
   - the narration with `capcut_add_audio` (`atSec` = the timeline's `narration_offset`, its own track, volume 1.0); the bed, when there
     is one, with `capcut_add_audio` (`atSec` 0, volume = the timeline's gain; its fades are in the file, so no `capcut_add_audio_fade`,
     which would fade it twice) on an audio track of its own: `capcut_add_track` (type audio) first and its `trackIndex` (left out, the
     tool put the bed on the narration's track and `capcut_validate` refused the overlap, 2026-11-09);
   - no CapCut scene effect or filter (`capcut add-effect`, `capcut_add_filter`): the CapCut check has verified none; grain, a vignette or
     light leaks come from the effects folder as overlays (static §5) or are named in the brief as left out;
   - `capcut_validate`, `capcut_save` (never force); this is the last MCP save: the commands below write the project's files, and a later
     MCP save would write its own copy back over them;
   - the moves: `T capcut-motion --draft "<draft>" --run RUN --video NN` (the timeline's values as KFTypeScaleX with uniform scale and
     KFTypePositionX/Y; never `capcut_add_keyframe` for a move: CapCut 9.7 ignores its UNIFORM_SCALE keys);
   - the joins: `T capcut-transitions --draft "<draft>" --run RUN --video NN` (the timeline's transition slugs; never `capcut_add_transition`);
   - the effects, when the timeline has any: `T capcut-effects --draft "<draft>" --run RUN --video NN` (each overlay on its own video
     track above the stills, each sound on an audio track, by the ways the CapCut effects check verified). Its `refused` must be empty: a
     refused effect needs something this PC's CapCut was not shown to play; plan that moment without it (static §5), `T slideshow plan`
     again, and run this again on a fresh clone (never write an effect by hand with the MCP or capcut-cli);
   - **a video in another language** (`state.json → static.video_info[NN].language`, static §7 "Captions in another language"), before
     the captions and the labels: `T static language --run RUN --language <code> --font <the look's font_file> --text
     RUN/60-outputs/video-NN/captions.srt` (and again with the labels' texts): `font_missing_glyphs` must be empty, else another file of
     `T capcut-font --list` that holds them replaces the font for those texts (the reason in the plan and the brief); a language
     written without spaces (`spaced: false`) or from right to left (`direction: rtl`) takes no `word_box` (`T capcut-word-box` stops
     with `word_box_supported: false`): its captions are the plain `capcut import-srt` look below with `highlight_words` left empty,
     named in the brief;
   - the captions in the references' look (static §7; the timeline's `captions` block): `capcut import-srt "<draft>"
     "RUN/60-outputs/video-NN/captions.srt" --font-size <size> --color <fill> --border-width <stroke_width> --border-color <stroke_color>
     --align 1 --y <1 − 2 × y_rel>` (plus `--shadow`, `--bg-color`/`--bg-alpha`, `--highlight-words … --keyword-color … --keyword-size …`
     as the look has them), the font with `T capcut-font --draft "<draft>" --font-file <font_file> --track subtitle` (it also writes the
     outline, box and shadow where CapCut 9.x draws them: `outlines_in_styles`), the entrance with `T capcut-text-anim --draft "<draft>"
     --track subtitle --intro <captions.animation> --intro-duration <captions.animation_s> --run RUN` (CapCut's own intro on every caption);
     with a `captions.word_box` (the spoken word on a rounded colour box, static §7) instead `T capcut-word-box --draft "<draft>" --run RUN
     --video NN [--replace subtitle]`, then `T capcut-font` on each `wordcap-*` track of its answer and `T capcut-text-anim` only on
     those ending in `-in`,
     the labels when the timeline has any (a map's place names, static §5 "Labels") with `T capcut-labels --draft "<draft>" --run RUN
     --video NN` (once per build), any other text with `capcut add-text` in its own look (its font with
     `T capcut-font --draft "<draft>" --font-file <file> --track text`), then
     `T capcut-repair --draft "<draft>" --keep-text` (register, the media links, sync, lint; the text stays as you set it; no `--preview`:
     no proxy video). capcut-assembly's house text style (§1, §4, §5) does not apply in Static.
   CapCut is open: blocker `capcut_running` (result.json).
4. **Project checks** (capcut-assembly §5, static §8), on the project itself: `capcut_read_timeline`: every image at the timeline's start
   and span, contiguous from 0 to the timeline's `duration_s` with no gap or overlap; the narration at `narration_offset` and the bed at
   0 at its gain on their tracks; each effect on its `fx`/`sfx` track at its start. `T capcut-motion`'s answer: every image keyed, its
   values the timeline's `moves`; `T capcut-transitions`': every join the timeline's. The captions: the project's caption count and words
   against `captions.srt` (the narration's words), every text's look against the timeline's `captions` (font, size, colours, outline,
   position, intro). The repair's lint with no `media-unlinked` and its link step's `media_without_entry` empty.
5. The video's brief, block S4: the timeline's facts (`T slideshow plan`'s answer: images, spans, moves, joins, captions, effects), the
   project's name, path and export size (the final: the user exports it from CapCut at that size, 30 fps), what the checks read back,
   and anything left to set by hand in CapCut. For a video in another language also its language and unit, the font the captions and
   labels use and why (any `font_missing_glyphs` and the replacement), whether the word box was placed or the plain caption look
   took its place and why, and that how CapCut shapes the script (a right-to-left or joined one) was not seen: nothing here renders it.
6. **Each extra format** (static §2b), after the primary's project: steps 1, 3, 4 and 5 again with `--format <tag>` on every command
   that takes it. First its own values in the plan, read off its stills: `by_format.<tag>.captions` (`size`, `y_rel`; set at S3), the
   labels' places, and an aim of its own for each image `T slideshow plan --format <tag>` lists in `moves_aimed_in_the_first_format`
   whose spot matters (`"by_format": {"<tag>": {"scale": […], "x": […], "y": […]}}`; else its plain move plays). Then `T slideshow plan
   --run RUN --video NN --format <tag>` (`undecided` empty), `T capcut-name --video NN --format <tag>`, `capcut_clone_draft`,
   `T capcut-prep --draft "<draft>" --canvas <that format's export, state.json → static.extra_formats>`, its stills from its timeline,
   the same narration and bed, `T capcut-motion`, `capcut-transitions`, `capcut-effects` and `capcut-labels` with `--format <tag>`,
   the captions from `RUN/60-outputs/video-NN/<tag>/captions.srt` at its timeline's `size` and `y_rel` (font, colours, outline and
   entrance the run's), `T capcut-repair`, the checks, and its own S4 block in the brief.
Then invoke Skill `awl-record`.

## Never (this phase)

- Never use `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`; never the house text style (no `capcut-text-style`;
  `capcut-repair` always with `--keep-text`): the look is the references'; never `capcut_save` with force; never `capcut lint --fix`
  (it copies every media file into the draft, shortens texts over 7 s and trims captions; `capcut-repair` writes the links).
- Never a move, an intro, a transition or a way of writing an effect that `AWL/data/capcut-catalogue.md` does not show drawn by this PC's
  CapCut (nor one marked Pro while the run's CapCut plan, `state.json → capcut_plan`, is free), and never a stock amount: every move,
  join and effect is the plan's, decided from the references' measured pattern.
- Never move, rename or change a file of the user's effects folder (it is read-only, like the references): `T capcut-effects` copies what
  it uses into the draft.
- Never move an image off its line to fill a gap, and never stretch the narration: fix the plan.

## Hand-off

Invoke Skill `awl-record` (X10).
