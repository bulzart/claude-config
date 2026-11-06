---
name: awl-static-edit
description: /analyze-with-loupe Static step S4: the timeline, the local check render, the CapCut project (the final, at the run's format) and the edit checks. Internal to that command.
user-invocable: false
---

# awl-static-edit — Static step S4: the edit

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §7: `AWL/reference/static/070_7_the-edit-s4.md` (4.9 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (2.2 KB)
- capcut-assembly §1: `AWL/reference/capcut-assembly/010_1_tools-and-rules.md` (3.3 KB)
- capcut-assembly §2: `AWL/reference/capcut-assembly/020_2_create-the-project.md` (0.8 KB)
- capcut-assembly §4: `AWL/reference/capcut-assembly/050_4_after-every-save-capcut-cli.md` (3.1 KB)
- capcut-assembly §5: `AWL/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.9 KB)

## Step S4

1. **The timeline:** `T slideshow plan --run RUN --video NN` → `RUN/40-briefs/video-NN-timeline.json` and the captions on the video's
   timeline (`RUN/60-outputs/video-NN/captions.srt`; a word that would flash for under `captions.min_cue_s` shares its cue with the next,
   `captions_over_words`). Read `image_spans` (every cut on the frame grid), `moves`, `undecided`, `edges_show`, `shorter_than_0_5s`
   and `images_without_a_file`: a gap, an undecided move or join, or an edge that shows is fixed in the image plan (static §5: every value
   is decided there from the spec's measured pattern and the CapCut catalogue; there is no stock value) or in the images, then plan again.
2. **The local render** (the check copies, at the format's check size): `T slideshow render --run RUN --video NN` → `RUN/deliverables/video-NN-clean.mp4` and `video-NN-preview.mp4`
   (the complete video with its captions). Its `video_frames` must equal `expected_frames` (`ok` false, exit 1: pictures were lost; the
   files are not used, the fault is reported with the answer). Watch it: `T frames RUN/deliverables/video-NN-preview.mp4 --out RUN/60-outputs/video-NN/check
   --at <each image's start + 0.5 s, and three caption times> --sheet`, view the sheet, check it as static §8 says; measure its moves:
   `T edit-profile RUN/deliverables/video-NN-clean.mp4 --timeline RUN/40-briefs/video-NN-timeline.json` (each image's zoom and pan
   against its `moves`, the jitter at the references' level).
3. **The CapCut project** (static §7; capcut-assembly §1, §2, §4):
   - `T capcut-name --video NN`, `capcut_clone_draft` (the template, empty), `T capcut-prep --draft "<draft>" --canvas <state.json →
     static.format.export>` (the project's canvas is the format's export size), `capcut_read_timeline`;
   - each image of the timeline with `capcut_add_image` (`atSec` its start, `durSec` its span, on the main track);
   - the narration with `capcut_add_audio` (`atSec` = the timeline's `narration_offset`, its own track, volume 1.0); the bed, when there
     is one, with `capcut_add_audio` (`atSec` 0, volume = the timeline's gain) and `capcut_add_audio_fade`;
   - effects the spec names with `capcut add-effect` (capcut-cli) or `capcut_add_filter`;
   - `capcut_validate`, `capcut_save` (never force); this is the last MCP save: the commands below write the project's files, and a later
     MCP save would write its own copy back over them;
   - the moves: `T capcut-motion --draft "<draft>" --run RUN --video NN` (the timeline's values as KFTypeScaleX with uniform scale and
     KFTypePositionX/Y; never `capcut_add_keyframe` for a move: CapCut 9.7 ignores its UNIFORM_SCALE keys);
   - the joins: `T capcut-transitions --draft "<draft>" --run RUN --video NN` (the timeline's transition slugs; never `capcut_add_transition`);
   - the captions in the references' look (static §7; the timeline's `captions` block): `capcut import-srt "<draft>"
     "RUN/60-outputs/video-NN/captions.srt" --font-size <size> --color <fill> --border-width <stroke_width> --border-color <stroke_color>
     --align 1 --y <1 − 2 × y_rel>` (plus `--shadow`, `--bg-color`/`--bg-alpha`, `--highlight-words … --keyword-color … --keyword-size …`
     as the look has them), the font with `T capcut-font --draft "<draft>" --font-file <font_file> --track subtitle` (it also writes the
     outline, box and shadow where CapCut 9.x draws them: `outlines_in_styles`), the entrance with `T capcut-text-anim --draft "<draft>"
     --track subtitle --intro <captions.animation> --intro-duration <captions.animation_s>` (CapCut's own intro on every caption), any
     other text with `capcut add-text` in its own look (its font with
     `T capcut-font --draft "<draft>" --font-file <file> --track text`), then
     `T capcut-repair --draft "<draft>" --keep-text --preview RUN/60-outputs/video-NN/capcut-preview.mp4` (register, the media links, sync,
     lint; the text stays as you set it). capcut-assembly's house text style (§1, §4, §5) does not apply in Static.
   CapCut is open: blocker `capcut_running` (result.json).
4. **Project checks** (capcut-assembly §5): `capcut_read_timeline` (every image at its start and span, the narration and the bed on their
   tracks), every text's look against the timeline's `captions` (font, size, colours, position); the repair's lint with no
   `media-unlinked` and its link step's `media_without_entry` empty.
5. The video's brief, block S4: the render's facts (`RUN/60-outputs/video-NN/slideshow.json`), the project's name and its export size (the
   final: the user exports it from CapCut at that size, 30 fps), anything left to set by hand in CapCut. Then invoke Skill `awl-record`.

## Never (this phase)

- Never use `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`; never the house text style (no `capcut-text-style`;
  `capcut-repair` always with `--keep-text`): the look is the references'; never `capcut_save` with force; never `capcut lint --fix`
  (it copies every media file into the draft, shortens texts over 7 s and trims captions; `capcut-repair` writes the links).
- Never a move, an intro or a transition that `AWL/data/capcut-catalogue.md` does not show drawn by this PC's CapCut, and never a stock
  amount: every move and join is the plan's, decided from the references' measured pattern.
- Never move an image off its line to fill a gap, and never stretch the narration: fix the plan.

## Hand-off

Invoke Skill `awl-record` (X10).
