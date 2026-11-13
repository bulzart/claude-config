---
name: cc-start
description: /create-clips phase 1: ask the user which mode this run is (streamer clipping or game clipping) and whether the videos get captions, take the run folder, check what the recorder, the processor and the chunk reporter produced, start the ONE research agent in the background, set up the analysis folders, size the work. Internal to that command.
user-invocable: false
---

# cc-start: intake

> `CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (every call prints one JSON object on its last line; run through PowerShell) · `RUN` = the run folder.

## Read now
- `CC/README.md` (the contract: the run layout, rec time, the chunk table, the chunk reports). Nothing else yet.

## Steps
1. **The mode and the captions choice come first, and the user picks them** (nothing here guesses the mode). `$ARGUMENTS` may carry `mode=streamer` or `mode=game` and `captions=on` or `captions=off`: what is given is not asked. A run whose `state.json` already holds a `mode` (a resume) keeps it, and keeps its `captions` (a run made before the option existed has none: that means `on`).
   Otherwise, before anything else, ask with AskUserQuestion, **both questions in ONE call** when both are missing (one dialog, headers `Mode` and `Captions`):
   - `Mode`: "Which kind of clipping is this run?" with two options:
     - **Streamer clipping**: "A person is the show (jokes, hype, arguments, chat, lingo). Research of the streamer, their audience and the topic; short-form videos (up to 3 minutes) and long-form videos, with zooms and sound effects (and captions if you pick them)."
     - **Game clipping**: "A match is the show (BLAST Premier CS2, a Dota 2 game, Valorant, League). Research of the game, the event and the teams; every round or fight decided (full, trimmed, a flash or skipped); long condensed-match videos only, no shorts, no sound effects; sponsor stretches are cut."
   - `Captions`: "Should the videos have captions?" with two options:
     - **Captions (Recommended)**: "Every second of speech is captioned in every video (names fixed from the research). The standing default."
     - **No captions**: "The same cuts, zooms and blurs, nothing typed on the picture: no caption track is made. A slur spoken aloud stays audible, so the plan cuts around such lines."
   The answer is the mode and the captions setting; "Other" text that names one of the options is taken as that one, anything else: ask once more. If the questions cannot be asked (a non-interactive run), the mode must come as `mode=streamer` or `mode=game` (stop and say so otherwise) and `captions` is `on` unless `captions=off` was passed.
   `T state --run RUN set mode=streamer captions=on` (or `game`, `off`) once the run is known (step 3), and `game="..."` when the user gave it.
2. **Arguments** (`$ARGUMENTS`): the run folder (a path, or a session name under `runs_root`), then optional `only=shorts|long` (streamer mode; game mode makes long videos only and `only=shorts` is refused in one line), `notes="..."` (what the user knows: the guest, the topic, what they want), `streamer="Name"`, `game="Counter-Strike 2"`.
   No run given: `T status` lists the runs; with exactly one run that has chunks, take it, otherwise report the list and stop (the only other time to ask).
3. **The run**: `T status --run <arg>` (stages per chunk, the report column, free space, totals). Take what is there: a chunk with stage `failed` or `pending` is listed and skipped; `T chunks --run RUN` is the table.
   The recording may still be growing (a watcher running): `T state --run RUN get recording` and `get stream_ended` say whether the recorder has ended it (the stream ended, it was stopped, a limit was reached: `reason`); when it has not ended, the chunk table at this moment is the run for this pass.
   `T status` also prints `ready` (the recording ended, every chunk processed, every report settled: the watcher then showed the user a Windows notification) and, when it is false, `why_not`: say in one line what is still running; it is information, not a stop, the rule above stands.
   Record the chunks used (`T state --run RUN set snapshot_chunks=<n>`) and use only those chunks. No processed chunk at all: stop and say what to run (`T watch`).
4. **Facts to hold**: channel, date, number of chunks and total length, the title and category changes (`00-inventory/stream-meta.json`), the source quality (`probe.json` of a chunk), gaps and skipped ads, free space on the drive.
   Read `RUN/00-inventory/stream.md` once (the table of numbers per chunk).
5. **Folders**: `RUN/20-analysis/blocks`, `RUN/40-briefs`, `RUN/60-outputs`, `RUN/deliverables` exist (`New-Item -ItemType Directory -Force`); game mode also `RUN/20-analysis/hud`.
6. **Start everything that does not wait for anything else, together, in ONE message** (speed: nothing below needs another's result):
   - **The one research agent**, in the background (Agent tool, general-purpose, no `model` argument, web only), briefed from `CC/reference/research-agent.md`: its contract for this mode, the run, the channel, the date, the stream's title and category from `stream-meta.json`, the user's `notes`, `streamer` or `game`, its output `RUN/20-analysis/research.md`, its budget (`config.json -> agents.research_calls` tool calls, a short note, not a deep research). It is the only research agent of the command (`config.json -> agents.research_max`). `T state --run RUN set research.status=running`.
     The recon, the HUD map and the scan of the next phases run while it works; `cc-profile` / `cc-profile-game` collect its note.
   - **The chunk reports** (made while the chunks were downloaded: a headless Haiku session per chunk reads its sheets, audio numbers, transcript and chat and writes `RUN/10-media/Cnnnn/report.md`; observations only, `CC/reference/reporter.md`): the `reports` counts of `T status` say how many are `ok`, `missing`, `stale`, `failed`, `running`.
     Complete what is not there: `T report --run RUN --parallel 4` (every chunk without a current report; the sessions run side by side, about a minute each; it prints the count, the cost and anything that failed). A chunk whose report cannot be made (no claude CLI, a failure twice) is listed: the analysis reads its raw data instead.
   - **Streamer mode:** `T sfx-scan --run RUN` catalogues the sound-effects folder (`30-assets/sfx.md`; it fails plainly when the folder is missing); game mode has no sound effects and skips it.
   - `T doctor` must show ffmpeg and ffprobe working; game mode also needs the screen reader (it shows whether `rapidocr_onnxruntime` loads; when it does not, say so: the analysis then works from the casters' words, the reports and the sheets).
   CapCut running is noted (the build needs it closed), not a blocker yet.
7. **Size the work**: `T config get agents` shows `scan_chunks_streamer` (10) and `scan_chunks_game` (8): the analysis makes one block per that many chunks (the agents read the reports, so a block is large), at least `scan_min_blocks` (2) blocks so that even a short recording is read by agents side by side, at most `scan_max` (6) agents at a time. A 4-hour stream is about 8 blocks; a short stream is two.
   The user's `notes`, `streamer` and `only` go into `state.json` (`T state --run RUN set notes="..." only=shorts`).
8. `T state --run RUN set stage=started next_skill=cc-profile` (streamer) or `next_skill=cc-profile-game` (game).

## Never
- Never move, rename, delete or rewrite a chunk, a sheet, a transcript or a report. The run's media is read-only for the whole command.
- Never guess the mode and never change it later: the user picked it. Never ask anything but the mode, the captions choice and, when it is missing, the run.
- Never start a second research agent, never a research wave.

## Hand-off
Invoke Skill `cc-profile` (streamer mode) or `cc-profile-game` (game mode).
