---
name: cs-edit
description: /create-static Static step S4: the timeline, the whole CapCut project in ONE composition (T capcut-build; the final, at the run's format; no local render) and its read-back. Internal to that command.
user-invocable: false
---

# cs-edit — Static step S4: the edit

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §7: `CS/reference/static/070_7_the-edit-s4.md` (15.3 KB)
- static §8: `CS/reference/static/080_8_static-qc-s2-s4.md` (10.6 KB)
- the build's recipe: `CS/reference/capcut-build.md` (9 KB)
- *the run has more than one format (`state.json → static.extra_formats`):*
  - static §2b: `CS/reference/static/025_2b_more-than-one-format.md` (4.5 KB)

## Step S4

0. **The decisions first, and your own check** (static §13 "Before the edit"): read `RUN/40-briefs/video-NN-brief.md` and the plan files:
   the moves, joins, labels and the bed's level decided for this video are what the project carries; a value the timeline gives that
   differs from them is traced to its cause and named in the brief before the project is built (nothing lands by accident). Settle the
   caption word box's colour from the finished stills and check the plan's moves, joins, drawings and sounds against the spec's numbers,
   skeptically, as §13 says.
1. **The timeline:** with drawings in the plan (static §5 "Drawings"), first `T draw render --run RUN --video NN` (every clip made and
   current, its previews viewed: `T draw list --run RUN --video NN` shows which are not), then `T slideshow plan --run RUN --video NN` →
   `RUN/40-briefs/video-NN-timeline.json` and the captions on the video's
   timeline (`RUN/60-outputs/video-NN/captions.srt`; a word that would flash for under `captions.min_cue_s` shares its cue with the next,
   `captions_over_words`). Read `image_spans` (every cut on the frame grid), `moves`, `effects`, `drawings` (each clip as an overlay on
   its track `draw1`, `draw2` …) with `drawings_not_rendered`, `drawings_on_moving_images`, `drawings_past_their_image`,
   `drawings_in_caption_band` and `drawings_undecided`, `undecided`, `edges_show`,
   `shorter_than_0_5s` and `images_without_a_file`: a gap, an undecided move, join or effect setting, or an edge that shows is fixed in the
   image plan (static §5: every value is decided there from the spec's measured pattern, the CapCut catalogue and, for effects, the effects
   folder's facts; there is no stock value) or in the images, then plan again.
2. **No local render** (the user, 2026-11-07: "no need to generate a ffmpeg video simulation version, just do it in capcut directly"):
   the edit is made in CapCut straight from the timeline; no `T slideshow render`, no check copies in `deliverables/` and no capcut-cli
   proxy preview. The checks read the project itself (step 4).
3. **The CapCut project: one composition** (item 39; static §7, `CS/reference/capcut-build.md`). CapCut must be closed (otherwise the build
   stops with exit 3 and changes nothing: blocker `capcut_running`, result.json). Before it:
   - **a font that is not a good match** (the captions', the labels' or a drawing's: none of `T capcut-font --list` suits the video's
     tone, the references' lettering or its script): download another, open licence only: `T fetch-font --family "<Family>" [--weight
     W] --text <the texts' file> --why "<reason>"` (static §7 "Extra fonts": the user, 2026-11-11), view a specimen of it first, name it in
     the plan's `captions.font_file` / `labels_style.font_file` and in the brief with the reason, then `T slideshow plan` again;
   - **a video in another language** (`state.json → static.video_info[NN].language`, static §7 "Captions in another language"):
     `T static language --run RUN --language <code> --font <the look's font_file> --text RUN/60-outputs/video-NN/captions.srt` (and again
     with the labels' texts): `font_missing_glyphs` must be empty, else another file of `T capcut-font --list` that holds them replaces the
     font for those texts (the reason in the plan and the brief), then `T slideshow plan` again; a language written without spaces
     (`spaced: false`) or from right to left (`direction: rtl`) takes no word box: the build stops with exit 2 and `word_box_supported:
     false` (nothing is changed) and you build again with `--captions plain`, named in the brief;
   - **look first**: `T capcut-build --run RUN --video NN --spec-only` (free; CapCut may be open): the plan's facts (images, tracks, items,
     joins, the caption look and whether the language takes the word box, the labels, the effects and what it refuses). A join or an
     entrance the catalogue does not show drawn, an effect that needs something the CapCut check did not verify, a missing still or a
     caption line wider than the frame stops the build with exit 2 and a sentence: plan that moment again without it (static §5),
     `T slideshow plan` again, then go on. The build makes nothing of its own: every look, move, join, effect, label, font and colour is
     the plan's (item 25).
   - **build**: `T capcut-build --run RUN --video NN` (`--captions plain` where step 3 says, `--name N` to choose the project's name, else
     `DD_Mon_YYYY_vNN`). ONE command writes the whole project: the stills (in place), the narration and the bed, the joins, the effects and
     the drawings, the captions in the references' look, the labels, the moves, the fonts and the entrance, the repair and the read-back.
     Never the CapCut MCP tools, `capcut import-srt`, `capcut lint --fix` or a save with force, never a project built clip by clip
     or finished by hand, never one command per feature (item 39).
4. **Project checks** (static §8 "The edit"), the build's own read-back: its answer's `problems` is empty, or each entry is fixed (in
   the plan or the stills, `T slideshow plan` again, a new build under a new `--name`) or named in the brief with its reason. Read
   `read_back` against the timeline: every image at its start and span, contiguous from 0 to `duration_s`; the narration at its offset and
   the bed at 0 at its gain; every move keyed (`moves_keyed` = `moves_planned`) with the timeline's `moves`; every join; each effect on its
   `fx`/`sfx` track and each drawing on its `draw` track at its start (`compose.effects.refused` empty); the captions' count and look, the
   labels, the fonts and the entrances; the lint with no errors and `media_without_entry` empty; `caption_font.font_missing_glyphs` empty.
   Then **look at what the read-back cannot see** (it is the user's first look, named in the brief): how CapCut draws the box, the entrance,
   a join, a keyed overlay's edges and a drawing over its picture, and for a right-to-left or joined script how CapCut shapes it.
5. The video's brief, block S4: the timeline's facts (`T slideshow plan`'s answer: images, spans, moves, joins, captions, effects, drawings),
   the build's answer (`compose`, `read_back`, `problems` and how each was settled, the seconds), the project's name, full path and export
   size (the final: the user exports it from CapCut at that size, 30 fps), and anything left to set by hand in CapCut. For a video in another
   language also its language and unit, the font the captions and labels use and why (any `font_missing_glyphs` and the replacement),
   whether the word box was placed or the plain caption look took its place and why, and that how CapCut shapes the script (a right-to-left
   or joined one) was not seen: nothing here renders it.
6. **Each extra format** (static §2b), after the primary's project: steps 1, 3, 4 and 5 again with `--format <tag>` on every command
   that takes it. First its own values in the plan, read off its stills: `by_format.<tag>.captions` (`size`, `y_rel`; set at S3), the
   labels' places, and an aim of its own for each image `T slideshow plan --format <tag>` lists in `moves_aimed_in_the_first_format`
   whose spot matters (`"by_format": {"<tag>": {"scale": […], "x": […], "y": […]}}`; else its plain move plays). Then `T slideshow plan
   --run RUN --video NN --format <tag>` (`undecided` empty), `T capcut-build --run RUN --video NN --format <tag>` (its project's name
   ends `-<tag>`, its canvas that format's export size, its stills from `60-outputs/video-NN/<tag>/images/`, the same narration and bed, its
   captions from `60-outputs/video-NN/<tag>/captions.srt` at its timeline's `size` and `y_rel`, the run's font, colours, outline and
   entrance), the checks, and its own S4 block in the brief.
Then invoke Skill `cs-record`.

## Never (this phase)

- Never the CapCut MCP tools, never `capcut import-srt`, never `capcut lint --fix` (it copies every media file into the draft, shortens
  texts over 7 s and trims captions) and never a save with force; never `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`;
  never the house text style: the look is the references'. One composition builds the project (item 39).
- Never a move, an intro, a transition or a way of writing an effect that `CS/data/capcut-catalogue.md` does not show drawn by this PC's
  CapCut (nor one marked Pro while the run's CapCut plan, `state.json → capcut_plan`, is free), and never a stock amount: every move,
  join and effect is the plan's, decided from the references' measured pattern. The build refuses what the catalogue does not allow; it
  never decides one.
- Never move, rename or change a file of the user's effects folder (it is read-only, like the references): the build copies what it
  uses into the draft.
- Never place a drawing by hand, never draw one with the image model, and never let one cover the captions' band or sit on a moving
  image: drawings go through `T draw render`, `T slideshow plan` and the build (static §5 "Drawings"); a drawing is never a sticker,
  emoji, icon, badge or decorative arrow (item 6).
- Never move an image off its line to fill a gap, and never stretch the narration: fix the plan.
- Never delete or change a CapCut project the user already has; a repair or a change after a complaint is a new build under a new name.

## Hand-off

Tick the edit's items in the video's `todo.md` (item 38), then invoke Skill `cs-record` (X10).
