# Building the CapCut project through the MCP tools (FALLBACK ONLY)

The normal build is ONE command (`cc.py capcut-compose`, then `cc.py capcut-finish`): see `capcut-build.md`. This older recipe makes the same project with one MCP tool call per clip. It is slower (a short is dozens of calls, an hour-long video hundreds),
so it is used only when `capcut-compose` has failed with a plain error that the report names and a re-run does not fix it. Nothing else changes: the EDL, `edl-check`, the captions, `capcut-finish`, the checks and the report are the same.

`CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (run through PowerShell; each prints one JSON object on its last line) ·
`TA` = `"$PY" "C:/Users/Bulzart/.claude/analyze-with-loupe/scripts/awl.py"` (the proven CapCut helpers: `capcut-prep`, `capcut-font`, `capcut-text-anim`, `capcut-repair`) · `RUN` = the run folder · `OUT` = `RUN/60-outputs/<id>`.

## Facts about this route
- The chunk files are used **in place**: `capcut_add_video` (MCP) references the file; capcut-cli's `add-video` COPIES the media into the draft (C: has little free space): never use it.
- Never `capcut_transcribe`, `capcut_add_captions`, `capcut_clear_captions`, `capcut_add_keyframe` for a zoom, or `capcut_save` with force.

## Steps (after the EDL, `edl-check` and, when captions are on, `captions` of `capcut-build.md` step 1)
1. **Name**: `T capcut-name --channel <channel> --video <id>` gives a free project name (`12_Nov_2026_kaicenat_S03`) and its path.
2. **Tools**: `ToolSearch "select:mcp__capcut__capcut_clone_draft,mcp__capcut__capcut_read_timeline,mcp__capcut__capcut_add_video,mcp__capcut__capcut_add_audio,mcp__capcut__capcut_add_track,mcp__capcut__capcut_trim_segment,mcp__capcut__capcut_delete_segment,mcp__capcut__capcut_validate,mcp__capcut__capcut_save,mcp__capcut__capcut_discard"`.
3. **Project**: `capcut_clone_draft {base:"_analyze-stack-template", newName:"<name>", empty:true}`, then at once `TA capcut-prep --draft "<store>/<name>" --canvas <W>x<H>` (shorts 1080x1920, long 1920x1080).
4. **Tracks**: `capcut_read_timeline` (the template's tracks are empty; note the video track index = `main`). For each sfx lane in the plan (`sfx1`, `sfx2` ...) `capcut_add_track {type:"audio"}` and note its index.
5. **Execute `OUT/mcp-plan.json -> ops` in order**: `add_video` on `main`: `capcut_add_video {draft, file, srcStartSec, durSec, scale, posX, posY, speed, volume, trackIndex:<main>}` and **no `atSec`** (it appends right after the last clip: no gap, no overlap);
   `add_audio`: `capcut_add_audio {draft, file, atSec, durSec, volume, trackIndex:<its lane>}`. A long video has many pieces: do them in order and read the timeline back after the first five and at the end.
6. `capcut_validate`, `capcut_save` (never force). This is the **last MCP save**: `capcut-finish` writes the project's files itself, and a later MCP save would write its own copy back over them.
7. Then `T capcut-finish`, the checks and the report as in `capcut-build.md` steps 4 to 6.

## When something goes wrong
- `capcut_save` refused (CapCut open, or the draft changed on disk): close CapCut / `capcut_discard` and rebuild the edits; CapCut running is a blocker notice.
- `capcut-finish` says a piece has no clip: the main track's pieces do not start where the plan says (a gap or an overlap from an `atSec` on main): delete the draft's clips and rebuild without `atSec`.
- A scale or position that looks wrong in CapCut: re-run `T layout-calc` for that source and canvas and set it with `capcut_set_props`, then re-run `capcut-finish`; note it in the report.
