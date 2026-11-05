---
name: awl-static-edit
description: /analyze-with-loupe Static step S4: the timeline, the local render (clean and captioned preview), the CapCut project and the edit checks. Internal to that command.
user-invocable: false
---

# awl-static-edit — Static step S4: the edit

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §7: `AWL/reference/static/070_7_the-edit-s4.md` (1.7 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (1.3 KB)
- capcut-assembly §1: `AWL/reference/capcut-assembly/010_1_tools-and-rules.md` (3.3 KB)
- capcut-assembly §2: `AWL/reference/capcut-assembly/020_2_create-the-project.md` (0.8 KB)
- capcut-assembly §4: `AWL/reference/capcut-assembly/050_4_after-every-save-capcut-cli.md` (2.5 KB)
- capcut-assembly §5: `AWL/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.9 KB)

## Step S4

1. **The timeline:** `T slideshow plan --run RUN --video NN` → `RUN/40-briefs/video-NN-timeline.json` and the captions on the video's
   timeline (`RUN/60-outputs/video-NN/captions.srt`). Read `image_spans`, `shorter_than_0_5s` and `images_without_a_file`: a gap is
   fixed in the image plan or the images first. Where the spec's moves or transitions differ from the timeline's, edit the timeline file
   (motion: zoom-in, zoom-out, pan-left, pan-right, pan-up, pan-down, none; transition: cut, fade, dissolve, fadeblack …).
2. **The local render:** `T slideshow render --run RUN --video NN` → `RUN/deliverables/video-NN-clean.mp4` and `video-NN-preview.mp4`
   (the complete video with its captions). Watch it: `T frames RUN/deliverables/video-NN-preview.mp4 --out RUN/60-outputs/video-NN/check
   --at <each image's start + 0.5 s, and three caption times> --sheet`, view the sheet, check it as static §8 says.
3. **The CapCut project** (static §7; capcut-assembly §1, §2, §4):
   - `T capcut-name --video NN`, `capcut_clone_draft` (the template, empty), `T capcut-prep --draft "<draft>"`, `capcut_read_timeline`;
   - each image of the timeline with `capcut_add_image` (`atSec` its start, `durSec` its span, on the main track);
   - its move with `capcut_add_keyframe` at the image's start and end (UNIFORM_SCALE 1.0 to 1 + the amount for zoom-in, the reverse
     for zoom-out; KFTypePositionX or KFTypePositionY for a pan);
   - every transition that is not a cut with `capcut_add_transition` (the closest name `capcut_list_transitions` gives);
   - the narration with `capcut_add_audio` (`atSec` = the timeline's `narration_offset`, its own track, volume 1.0); the bed, when there
     is one, with `capcut_add_audio` (`atSec` 0, volume = the timeline's gain) and `capcut_add_audio_fade`;
   - effects the spec names with `capcut add-effect` (capcut-cli) or `capcut_add_filter`;
   - `capcut_validate`, `capcut_save` (never force);
   - the captions: `capcut import-srt "<draft>" "RUN/60-outputs/video-NN/captions.srt" --y <1 − 2 × the timeline's captions y_rel>`
     (plus `--highlight-words` when the spec's captions highlight words), then
     `T capcut-repair --draft "<draft>" --preview RUN/60-outputs/video-NN/capcut-preview.mp4` (house text style, register, lint).
   CapCut is open: blocker `capcut_running` (result.json).
4. **Project checks** (capcut-assembly §5): `capcut_read_timeline` (every image at its start and span, the narration and the bed on their
   tracks), `T capcut-text-style --draft "<draft>" --check` at 0.
5. The video's brief, block S4: the render's facts (`RUN/60-outputs/video-NN/slideshow.json`), the project's name, anything left to set by
   hand in CapCut. Then invoke Skill `awl-record`.

## Never (this phase)

- Never use `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`; never restyle or resize text by hand; never
  `capcut_save` with force.
- Never move an image off its line to fill a gap, and never stretch the narration: fix the plan.

## Hand-off

Invoke Skill `awl-record` (X10).
