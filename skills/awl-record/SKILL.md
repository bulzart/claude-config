---
name: awl-record
description: /analyze-with-loupe per-video step X10: finalize, deliverables, README row, result.json, state. Internal to that command.
user-invocable: false
---

# awl-record — Step X10: record

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- capcut-assembly §6: `AWL/reference/capcut-assembly/070_6_deliverables-analyze-mode.md` (1.8 KB)
- production-agents §4: `AWL/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.8 KB)

A production agent does not touch `state.json → videos[]` or `next_step`: it writes `result.json` and `readme-row.md`, and the main session appends `videos[]` as the agent reports (`production-agents` §5 item 1).

## Step X10

- **X10 — Record.**
  - **Edit Mode:** the approved video (generated picture + original audio, already 720×1280) goes to
    the **`final` folder inside the given path**:
    `T finalize --run RUN --video NN --file <aK approved file> --original "<original video path>"`.
    - It is named after the original video (`<given path>/final/<name>.mp4`, sub-folders mirrored).
    - It never refuses the user's approval. It returns `facts` (`has_video`, `size`, `expected_size`,
      `has_audio`, `original_has_audio`): read them (picture present, 720×1280, audio present exactly
      when the original had audio) and report any mismatch to the user.
    - The folder is marked so later scans skip it. A previously approved final of the same video is
      moved into the run folder, never overwritten silently.
    - Only approved videos are placed there.
  - **Analyze Mode** (`capcut-assembly.md` §6):
    - the **CapCut project** `DD_Mon_YYYY_vNN` is the master; the final is exported from CapCut;
    - `RUN/deliverables/video-NN-clean.mp4`: the same edit with its inserts and without text,
      assembled locally from the pieces, the inserts and (Recreate) the original audio, and never
      replaced by the generated-only `60-outputs/video-NN/clean.mp4` when the video has inserts;
    - `RUN/deliverables/video-NN-preview.mp4`: a 720×1280 ffmpeg burn of the CapCut text layer over the clean video
      (never the 540×960 capcut-cli proxy; `capcut-assembly.md` §6);
    - Create and Free `create` (item 35): `RUN/deliverables/video-NN-take-K.mp4`, every take conformed and untouched by the edit (the
      clean originals); the clean deliverable is the edit's main track cut together without text (`capcut-assembly.md` §6), and the
      README row lists what is to be applied in CapCut by hand (reverse playback, an effect from CapCut's library) when no tool placed it.
  - **Static** (item 36): the CapCut project is the final and the only edit (the user exports it from CapCut at the format's export
    size, `state.json → static.format.export`, 30 fps); no local copy is rendered (the user, 2026-11-07: "no need to generate a ffmpeg
    video simulation version, just do it in capcut directly"), so `deliverables/` has no video file and `state.json → videos[]` names the
    project (`capcut_project`, `capcut_project_path`) instead of `clean` and `preview`. The README row lists the CapCut project's name and
    full path, the format (export size, image size, quality), the images
    (`60-outputs/video-NN/images/`, api, klein or user), the narration (`30-assets/narration/video-NN.wav`), the bed or none, the drawings (their ids and images, `30-assets/drawings/video-NN/`; none when none) and, with images by
    the user, the prompts file; the YouTube title and thumbnail (static §12): write `RUN/deliverables/video-NN-title.txt` (the plan's `title`
    on its first line, and for a video in another language a second line "English: <the plan's `title_gloss`>") and name it and
    `RUN/deliverables/video-NN-thumbnail.png` (the toolkit keeps the one in use there) in the row (the other title options follow the
    title after a blank line); and the publishing kit planned at A6s (static §12; the plan's `publish` block): `RUN/deliverables/video-NN-description.txt`
    (the description, its chapters each given its time from the timeline: the start of its image, the first at 0:00, at least three,
    each at least 10 s long) and `RUN/deliverables/video-NN-pinned-comment.txt`, both named in the row; the
    run's locks it kept (niche, style reference, narrator; static §10) and this video's own approach and language (story form, angle,
    point of view, time frame, title form, pillar; the language's name, code and unit; the narration model: `state.json →
    static.video_info`, `static.tts_model`); `result.json` adds `static`: {format, images (count, source api|klein|user, re-draws), cost_usd_estimate (the sum of
    the image calls), drawings (how many, and per drawing its id, image, start, length and why: static §5 "Drawings"), narration_s, voice (its ElevenLabs id and name), model (the narration's ElevenLabs model id), language {code, name,
    official, unit}, approach {story_form, angle, point_of_view, time_frame, scale, title_form, pillar}, the narration's characters,
    passages made again, partial or whole, bed, title, title_gloss, thumbnail, description and pinned comment (their files), captions (word box placed, or the plain look and why), font
    (any replacement for missing glyphs), pronunciation ("not checked (listen)" when the language is outside the model's list or is the
    first in the run, static §8)}. No Higgsfield job, credit or flag fields.
    More than one format (static §2b): one README row per format (its CapCut project's name and full path, its export size, its stills'
    folder `60-outputs/video-NN/<tag>/images/`; the title and thumbnail named in each), and `result.json → static.formats`: one entry
    per format {aspect, tag (null for the primary), export, capcut_project, capcut_project_path, images (count, re-draws, own prompts),
    swaps, cost_usd_estimate, flags}; `static.cost_usd_estimate` sums them. A run told to make one format of a video later (spawn
    message `format <tag>`) adds that format's entry and row and leaves the others as they are.
  - Append a row to `RUN/deliverables/README.md` (an agent writes it to
    `60-outputs/video-NN/readme-row.md` and the main session appends it as the agent reports, A9b): direction, model, params, prompt file, assets, job
    id, attempt, credits, verdict (with QC fixes `off`: "not checked (QC off)", and `result.json → qc` = "off: not checked (the user reviews at the end)"), final path, notes. For a multi-clip video, list every clip's
    job id and the seam methods. Analyze Mode adds the CapCut project name, the inserts and the
    text events. With an own voiceover (item 31): its `result.json → voiceover` line ("pronunciation: not checked (listen)" included);
    `video-NN-clean.mp4` carries the voice.
  - Update `state.json` (`videos[]`, `next_step`), then move to the next video. In Edit Mode, only
    after the user said "Looks good".

## Hand-off

- Production agent: write `result.json`, `readme-row.md`, the deliverables, then send the one-line JSON as the final message and stop.
- Edit Mode: more videos: `T state --run RUN set video=<NN+1> next_skill=awl-edit` and continue with E7 in `awl-edit`. No more videos, or the user stops: `T state --run RUN set stage=edited next_skill=awl-wrapup`, then invoke Skill `awl-wrapup`.
- Analyze Mode main session: continue A9b in `awl-analyze-produce`.
