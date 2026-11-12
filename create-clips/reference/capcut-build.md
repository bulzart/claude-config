# Building the CapCut project (production agent's recipe)

`CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (run through PowerShell; each prints one JSON object on its last line) ·
`TA` = `"$PY" "C:/Users/Bulzart/.claude/analyze-with-loupe/scripts/awl.py"` (the proven CapCut helpers: `capcut-prep`, `capcut-font`, `capcut-text-anim`, `capcut-repair`) · `RUN` = the run folder · `OUT` = `RUN/60-outputs/<id>`.

## Facts about this PC's CapCut that shape the build
- CapCut 9.7 Free (no Pro: a project that uses a Pro option will not export). CapCut and capcut-cli write refuse while CapCut runs: **CapCut must be closed** for every save and every capcut-cli write. If it is open that is a blocker notice to the user, not a question.
- The chunk files are used **in place**: `capcut_add_video` (MCP) references the file; capcut-cli's `add-video` COPIES the media into the draft (C: has about 8 GB free): never use it.
- Never `capcut lint --fix`, `capcut_transcribe`, `capcut_add_captions`, `capcut_clear_captions`, `--force-write`, or `capcut_save` with force.
- CapCut 9.7 ignores `UNIFORM_SCALE` keyframes: zoom keys are written by `cc.py capcut-finish` as KFTypeScaleX with the uniform scale on (same as the AWL motion code). Never `capcut_add_keyframe` for a zoom.
- Chroma key and screen blend do not play; scene effects and `bg-blur` are not verified here (edit-craft.md).
- Several production agents build at once: each its own draft; `capcut-repair` takes a machine-wide lock for CapCut's shared project index. They share nothing else.

## Steps
1. **Facts**: read your brief; write the EDL (edit-craft.md); `T edl-check --run RUN --edl OUT/edl.json --make-censor`; fix until it has no warnings and every cut is clean; `T captions --run RUN --resolved OUT/resolved.json` (captions are not optional).
2. **Name**: `T capcut-name --channel <channel> --video <id>` gives a free project name (`12_Nov_2026_kaicenat_S03`).
3. **Tools**: `ToolSearch "select:mcp__capcut__capcut_clone_draft,mcp__capcut__capcut_read_timeline,mcp__capcut__capcut_add_video,mcp__capcut__capcut_add_audio,mcp__capcut__capcut_add_track,mcp__capcut__capcut_trim_segment,mcp__capcut__capcut_delete_segment,mcp__capcut__capcut_validate,mcp__capcut__capcut_save,mcp__capcut__capcut_discard"`. A name that is not found was renamed: search `+capcut` and the operation.
4. **Project**: `capcut_clone_draft {base:"_analyze-stack-template", newName:"<name>", empty:true}`, then at once `TA capcut-prep --draft "<store>/<name>" --canvas <W>x<H>` (shorts 1080x1920, long 1920x1080). The drafts store is in `mcp-plan.json -> ` the name's `path` from `capcut-name`.
5. **Tracks**: `capcut_read_timeline` (the template's tracks are empty; note the video track index = `main`). For each sfx lane in the plan (`sfx1`, `sfx2` ...) `capcut_add_track {type:"audio"}` and note its index.
6. **Execute `OUT/mcp-plan.json -> ops` in order**:
   - `add_video` on `main`: `capcut_add_video {draft, file, srcStartSec, durSec, scale, posX, posY, speed, volume, trackIndex:<main>}` and **no `atSec`** (it appends right after the last clip, so there is no gap or overlap).
   - `add_audio`: `capcut_add_audio {draft, file, atSec, durSec, volume, trackIndex:<its lane>}`.
   A long video has many pieces: do them in order and read the timeline back after the first five and at the end.
7. `capcut_validate` (no overlaps, no missing media), `capcut_save` (never force). This is the **last MCP save**: `capcut-finish` writes the project's files itself, and a later MCP save would write its own copy back over them.
8. **Finish**: `T capcut-finish --run RUN --draft "<store>/<name>" --video <id>`: zoom keyframes, transitions, background blur (fit-blur only), the captions (`capcut import-srt` from `OUT/captions.srt` in the EDL's caption look), the font, the entrance, and `capcut-repair --keep-text` (registers the project, writes the media links, syncs the nested timeline, lints). Its answer must be `ok`; any `failed` step is yours to fix (re-run it) or to report.
9. **Checks** (read, do not assume):
   - `capcut_read_timeline`: the main track's pieces in the plan's order, each `srcStartSec`/duration as planned, contiguous from 0, the total equal to `resolved.json -> totals.duration_s` (within 0.1 s); the sfx on their lanes at their times; the caption track's count equal to the cues in `captions.json`.
   - `capcut lint "<draft>"`: 0 errors, no `media-unlinked`.
   - For a short under 90 s, a proxy preview: `capcut render "<draft>" --out "OUT/preview.mp4" --burn-captions`, then look at 3 frames (`T frame` is for the chunks; use ffmpeg `-ss` on the preview). The proxy shows order, timing and captions only: not layouts, keyframes or blur (those are checked on the timeline read-back and, for blur, with `cc.py censor --preview-only` and the frames around each blurred span).
10. **Report**: `OUT/report.md` (a few lines each): what the video is, source spans, length, the project name and path, layouts and why, zooms, transitions, sfx (name, time, why), the blurred spans (rec range, what, region, style), exclamations or touchy items left in (safety.md), captions (cues, look, lexicon fixes applied), the source quality, what the user must do in CapCut (open it, check the first frame of a `fill` layout once, export at 1080x1920 or 1920x1080, 30 fps), anything not verified. And `OUT/posting.md` (title, description, hashtags, chapters for a long video).
    Then `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>"`.

## When something goes wrong
- `capcut_save` refused (CapCut open, or the draft changed on disk): close CapCut / `capcut_discard` and rebuild the edits; report CapCut-running as a blocker.
- `capcut-finish` says a piece has no clip: the main track's pieces do not start where the plan says (a gap or an overlap from an `atSec` on main): delete the draft's clips and rebuild without `atSec`.
- A scale/position that looks wrong in CapCut: re-run `T layout-calc` for that source and canvas and set it with `capcut_set_props`, then re-run `capcut-finish`; note it in the report.
- Never leave a half-built project that looks finished: if the build cannot be completed, the report says what is missing and `videos.<id>.status=failed`.
