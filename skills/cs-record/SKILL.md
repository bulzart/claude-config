---
name: cs-record
description: /create-static per-video step X10: the video's record: deliverables, YouTube title and thumbnail, README row, result.json, state. Internal to that command.
user-invocable: false
---

# cs-record — Step X10: record

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- production-agents §4: `CS/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.8 KB)

A production agent does not touch `state.json → videos[]` or `next_step`: it writes `result.json` and `readme-row.md`, and the main session appends `videos[]` as the agent reports (`production-agents` §5 item 1). This step records what `cs-images`, `cs-sound` and `cs-edit` made: it builds, changes and repairs nothing (item 39).

## Step X10

- **X10 — Record** (Static, item 36).
  - **The final is the CapCut project and nothing else.** `T capcut-build` (S4, `cs-edit`; item 39) built it at the format's export
    size and read it back; the user opens it in CapCut (the projects are listed by name), looks at the first frame, a move, a join and a
    caption once, and exports it from CapCut at the format's export size, `state.json → static.format.export`, 30 fps. No local copy is
    rendered (the user, 2026-11-07: "no need to generate a ffmpeg video simulation version, just do it in capcut directly"), so
    `deliverables/` has no video file and `state.json → videos[]` names the project (`capcut_project`, `capcut_project_path`: its
    name and its full path, the build's `name` and `draft`). The project's stills, narration and bed are used where they lie in the
    run folder, so the run folder is kept (the README says so).
  - **The build's facts**, from the build's answer as S4 wrote it in the video's brief (block S4; `T capcut-build` also keeps it in
    `RUN/60-outputs/video-NN/composed.json`, an extra format's in its `<tag>/` folder): `ok`, the project's `name`, `draft` and `export`,
    the `seconds`, every entry of `problems` with how it was settled (fixed by a new build under a new `--name`, or named open with its
    reason), its `read_back` counts against the timeline's, and its `note` (what no tool here can see: how CapCut draws the caption
    look, the box, the entrance, the moves, the joins and the drawings). Record them as they are: never a check that was not made.
    A project that could not be built (CapCut running: blocker `capcut_running`, `capcut_pending` true; or a build that failed) is
    recorded for what it is: what is missing, and `status` `blocked` or `failed`, never a half-built project that looks finished
    (`CS/reference/capcut-build.md` "When something goes wrong").
  - **The README row** lists the CapCut project's name and full path, the format (export size, image size, quality), the images
    (`60-outputs/video-NN/images/`, api, klein or user), the narration (`30-assets/narration/video-NN.wav`), the bed or none, the
    drawings (their ids and images, `30-assets/drawings/video-NN/`; none when none) and, with images by the user, the prompts file; the
    YouTube title and thumbnail (static §12): write `RUN/deliverables/video-NN-title.txt` (the plan's `title` on its first line, and for
    a video in another language a second line "English: <the plan's `title_gloss`>") and name it and
    `RUN/deliverables/video-NN-thumbnail.png` (the toolkit keeps the one in use there) in the row; and whatever else the plan's `publish`
    block carries (static §12: for example a description and a pinned comment, written as files in `RUN/deliverables/`, a chapter's time
    taken from the timeline: the start of its first image, the first at 0:00, at least three, each at least 10 s long), named in the row; the
    run's locks it kept (niche, style reference, narrator; static §10) and this video's own approach and language (story form, angle,
    point of view, time frame, title form, pillar; the language's name, code and unit; the narration model: `state.json →
    static.video_info`, `static.tts_model`); the cost (the OpenAI estimate, the narration's characters), the verdict (with QC fixes
    `off`: "not checked (QC off)", and `result.json → qc` = "off: not checked (the user reviews at the end)"), the attempts (the stills
    drawn again, the passages made again) and notes. It also says what the user does in CapCut: open the project by its name, look at
    the first frame, a move, a join and a caption, export at the export size, 30 fps.
  - **`result.json`** (`production-agents` §4 for the fields it names; a Static video has no job, credit or sync fields) adds
    `static`: {format, images (count, source api|klein|user, re-draws), cost_usd_estimate (the sum of
    the image calls), drawings (how many, and per drawing its id, image, start, length and why: static §5 "Drawings"), narration_s, voice (its ElevenLabs id and name), model (the narration's ElevenLabs model id), language {code, name,
    official, unit}, approach {story_form, angle, point_of_view, time_frame, scale, title_form, pillar}, the narration's characters,
    passages made again, partial or whole, bed, title, title_gloss, thumbnail, description and pinned comment (their files), captions (word box placed, or the plain look and why), font
    (any replacement for missing glyphs), pronunciation ("not checked (listen)" when the language is outside the model's list or is the
    first in the run, static §8), capcut_build {ok, seconds, problems (each with how it was settled, or "open: <why>"), read_back (its
    counts against the timeline's, as the answer gives them), note}}. No job, credit or flag fields. A long video split at A9b
    (spawn message `S4 and X10`) sums its `images-K1-K2.json` files into `static.images`.
    More than one format (static §2b): one README row per format (its CapCut project's name and full path, its export size, its stills'
    folder `60-outputs/video-NN/<tag>/images/`; the title and thumbnail named in each), and `result.json → static.formats`: one entry
    per format {aspect, tag (null for the primary), export, capcut_project, capcut_project_path, capcut_build, images (count, re-draws,
    own prompts), swaps, cost_usd_estimate, flags}; `static.cost_usd_estimate` sums them. A run told to make one format of a video later
    (spawn message `format <tag>`) adds that format's entry and row and leaves the others as they are.
  - Append a row to `RUN/deliverables/README.md` (an agent writes it to
    `60-outputs/video-NN/readme-row.md` and the main session appends it as the agent reports, A10).
  - Update `state.json` (`videos[]`, `next_step`): the main session, from `result.json`, as the agent reports (`production-agents`
    §5), then it moves to the next video.

## Never (this phase)

- Never build, change or repair a CapCut project here: the project is built only by `T capcut-build` (item 39); a repair after the
  user's complaint is a new build under a new `--name`, never an edit of the finished project.
- Never render a local copy or put a video file in `deliverables/` (the user, 2026-11-07, above).
- Never record a check that did not happen (item 10): a build `problems` entry is recorded as it is; what only CapCut's playing shows
  is "not seen by any tool here"; the pronunciation is "not checked (listen)".

## Hand-off

- Production agent: write `result.json`, `readme-row.md`, the deliverables (the title file, the thumbnail and the `publish` files), close the video's `todo.md` (item 38: every item `[x]` or `[-]` with its reason, `Next:` saying what the main session does), then send the one-line JSON as the final message and stop. The main session continues at A10 in `cs-produce`.
- The main session, when it records a video itself (a record made again after a complaint, `cs-feedback`): `T state --run RUN set next_skill=cs-produce`, then continue at A10 in `cs-produce`. After a compaction or on `resume`, the command sends the session to `state.json → next_skill`.
