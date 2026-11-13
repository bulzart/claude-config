# Building the CapCut project (production agent's recipe): one compose command

`CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (run through PowerShell; each prints one JSON object on its last line) · `RUN` = the run folder · `OUT` = `RUN/60-outputs/<id>`.
The project is built by two commands, not by one tool call per clip: `T capcut-compose` writes the whole draft in about a second or two, `T capcut-finish` adds what compose does not (zoom keys, transitions, captions when on, the font, the repair).
The older per-tool route is `capcut-build-mcp.md`: a fallback, used only when compose has failed with a plain error that a re-run does not fix.

## Facts about this PC's CapCut that shape the build
- CapCut 9.7 Free (no Pro: a project that uses a Pro option will not export). CapCut and capcut-cli write refuse while CapCut runs: **CapCut must be closed** for compose and finish. If it is open that is a blocker notice to the user, not a question: compose changes nothing and says so.
- The chunk files are used **in place**: compose builds the draft on a 350 KB placeholder and then points every clip at its real chunk file (or blurred file). Never `capcut add-video` (it copies the media into the draft; C: has little free space).
- The draft starts from `CC/data/compose-template`, an empty draft with this PC's CapCut 9.7 version markers. capcut-cli's own `auto` would use its bundled CapCut 6.5.0 (mac) skeleton here; do not pass `--template auto`.
- Never `capcut lint --fix`, `--force-write`, `capcut_transcribe`, `capcut_add_captions`, `capcut_clear_captions`, or a save with force.
- CapCut 9.7 ignores `UNIFORM_SCALE` keyframes: zoom keys are written by `capcut-finish` as KFTypeScaleX with the uniform scale on. Never `capcut_add_keyframe` for a zoom.
- Chroma key and screen blend do not play; scene effects and `bg-blur` are not verified here (edit-craft.md).
- Several production agents build at once: each its own draft; `capcut-repair` takes a machine-wide lock for CapCut's shared project index. They share nothing else.

## Steps
1. **Facts**: read your brief; write the EDL (edit-craft.md); `T edl-check --run RUN --edl OUT/edl.json --make-censor`; fix until it has no warnings and every cut is clean; with the run's captions setting ON (the default; `T state --run RUN get captions`) `T captions --run RUN --resolved OUT/resolved.json`; with captions OFF skip it (it would only answer "skipped").
2. **Compose**: `T capcut-compose --run RUN --video <id>` (the project name is made for you: `12_Nov_2026_kaicenat_S03`; `--name` to choose one). It reads `resolved.json` and `mcp-plan.json`, builds the main track (one clip per piece, in order, contiguous from 0), one audio track per sound-effect lane, and returns:
   `ok`, `draft` (the full path), `name`, `pieces`, `video_segments_retargeted` (equal to `pieces`), `sfx_lanes`, `big_media_copied_into_the_draft` (must be `[]`), `media_pool_entries_dropped` (the placeholder and any media the template listed: dropped so CapCut does not show "Media lost / Link media" when the project opens),
   `cover_from_first_clip` (the project's thumbnail on CapCut's home screen is a frame of the first clip, not the template's "Template text" tile), `seconds`. `ok` must be true. CapCut running: it refuses and changes nothing (set `videos.<id>.status=ready-to-build` and stop).
3. **Finish**: `T capcut-finish --run RUN --draft "<draft>" --video <id>` (the `draft` of step 2): zoom keyframes, transitions, background blur (fit-blur only), the captions (`capcut import-srt` from `OUT/captions.srt` in the EDL's caption look; skipped when the run's captions setting is off), the font, the entrance,
   and `capcut-repair --keep-text` (registers the project, writes the media links, syncs the nested timeline, lints). Its answer must be `ok`; a `failed` step is yours to fix (re-run it) or to report.
4. **Checks** (read, do not assume):
   - `capcut segments "<draft>" --track video`: the main track's clips in the plan's order, `start_us` contiguous from 0, the last one's `start_us + duration_us` equal to `resolved.json -> totals.duration_s` (within 0.1 s). `capcut segments "<draft>" --track audio`: the sound effects at their times.
   - `capcut texts "<draft>"`: the caption count equals the cues in `captions.json` (0 when captions are off).
   - `capcut lint "<draft>"`: 0 errors, no `media-unlinked`. One `media-outside-draft` info per clip is expected (the chunks are used in place); an `info` about source ranges is read, not ignored: it can mean a clip points past the end of its file.
   - The media pool (`draft_meta_info.json -> draft_materials`) lists only files that exist: a missing one makes CapCut open the project with a "Media lost / Link media" window. A project built from capcut-cli's or the MCP's clone of a template can carry the template's media there; compose does not.
   - For a short under 90 s, a proxy preview: `capcut render "<draft>" --out "OUT/preview.mp4" --burn-captions`, then look at 3 frames with ffmpeg `-ss` on the preview. The proxy shows order, timing and captions only: not layouts, keyframes or blur
     (those are checked on the segment read-back and, for blur, with `cc.py censor --preview-only` and the frames around each blurred span).
   - A long video has many pieces: the read-back is the check; no proxy of the whole hour.
5. **Report**: `OUT/report.md` (a few lines each): what the video is, source spans, length, the project name and path, layouts and why, zooms, transitions, sfx (name, time, why), the blurred spans (rec range, what, region, style),
   exclamations or touchy items left in (safety.md), captions (cues, look, lexicon fixes applied; or "captions: off"), the source quality, what the user must do in CapCut (open it, check the first frame of a `fill` layout once, export at 1080x1920 or 1920x1080, 30 fps), anything not verified;
   and `OUT/posting.md` (title, description, hashtags, chapters for a long video). Then `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>" videos.<id>.duration_s=<n>`.

## When something goes wrong
- `capcut-compose` says CapCut is running: close it, run it again. It failed with a plain error (a missing media file, a refused spec): the error text says which; fix the cause (a wrong path in the EDL, a chunk that is not there) and run it again; the half-made draft folder it names is yours to remove only by exact path.
- `video_segments_retargeted` is less than `pieces`, or `big_media_copied_into_the_draft` is not empty: the draft is wrong; delete that one draft folder by its exact path and compose again under a new `--name`.
- `capcut-finish` says a piece has no clip: the main track's clips do not start where the plan says; compose again.
- A scale or position that looks wrong in CapCut: re-run `T layout-calc` for that source and canvas, put the numbers in the EDL's layout, re-run `edl-check`, compose and finish again under a new name; note it in the report.
- Never leave a half-built project that looks finished: if the build cannot be completed, the report says what is missing and `videos.<id>.status=failed`.
