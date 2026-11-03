---
name: awl-record
description: /analyze-with-loupe per-video step X10: finalize, deliverables, README row, result.json, state. Internal to that command.
user-invocable: false
---

# awl-record — Step X10: record

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- capcut-assembly §6: `AWL/reference/capcut-assembly/070_6_deliverables-analyze-mode.md` (1.8 KB)
- production-agents §4: `AWL/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.6 KB)

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
