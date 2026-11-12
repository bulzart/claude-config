---
name: cc-start
description: /create-clips phase 1: take the run folder, check what the recorder and processor produced, decide the mode (streamer clipping or game clipping), set up the analysis folders, size the work. Internal to that command.
user-invocable: false
---

# cc-start: intake

> `CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (every call prints one JSON object on its last line; run through PowerShell) · `RUN` = the run folder.

## Read now
- `CC/README.md` (the contract: the run layout, rec time, the chunk table). Nothing else yet.

## Steps
1. **Arguments** (`$ARGUMENTS`): the run folder (a path, or a session name under `runs_root`), then optional `only=shorts|long`, `notes="..."` (what the user knows: the guest, the topic, what they want), `streamer="Name"`, `mode=streamer|game`, `game="Counter-Strike 2"`.
   No run given: `T status` lists the runs; with exactly one run that has chunks, take it, otherwise report the list and stop (that is the only time to ask).
2. **The run**: `T status --run <arg>` (stages per chunk, free space, totals). Take what is there: a chunk with stage `failed` or `pending` is listed and skipped; `T chunks --run RUN` is the table.
   The recording may still be growing (a watcher running): `T state --run RUN get recording` and `get stream_ended` say whether the recorder has ended it (the stream ended, it was stopped, a limit was reached: `reason`); when it has not ended, the chunk table at this moment is the run for this pass.
   Record the chunks used (`T state --run RUN set snapshot_chunks=<n>`) and use only those chunks. No processed chunk at all: stop and say what to run (`T watch`).
3. **Facts to hold**: channel, date, number of chunks and total length, the title and category changes (`00-inventory/stream-meta.json`), the source quality (`probe.json` of a chunk), gaps and skipped ads, free space on the drive.
   Read `RUN/00-inventory/stream.md` once (the table of numbers per chunk).
4. **Mode** (the user's `mode=` wins; otherwise you decide from the facts, without asking):
   - **game**: what is on screen is a match played by teams or players with casters or commentators, an esports tournament or league broadcast or a showmatch (BLAST Premier, ESL, PGL, IEM, The International, VCT, LCS ...).
     The signs: the title names a tournament, a stage or two teams ("A vs B"), the channel belongs to an event, a league or an organiser, the picture carries a scoreboard overlay, the voices are casters and not one person talking to their chat. The things to clip are **rounds and fights**.
   - **streamer**: a person is the show (their reactions, their chat, their jokes), also when they play CS2, Dota 2 or Valorant themselves, or watch a tournament with their chat (a watch-along or a co-stream). The match is then the topic the research covers and the moments are the person's.
   - Both fit (a streamer co-streaming a tournament with the match overlay): choose by who the audience came for, the match (game) or the person (streamer), and say the choice and the reason in one line. The two modes never run together on one run.
   `T state --run RUN set mode=game` (or `mode=streamer`), and `game="..."` when the user gave it.
5. **Tools**: `T doctor` must show ffmpeg and ffprobe working; `T sfx-scan --run RUN` catalogues the sound-effects folder (`30-assets/sfx.md`; it fails plainly when the folder is missing). CapCut running is noted (the build needs it closed), not a blocker yet.
   Game mode also needs the screen reader: `T doctor` shows whether `rapidocr-onnxruntime` loads; when it does not, say so (the scan then works from the casters' words and the sheets).
6. **Folders**: `RUN/20-analysis/blocks`, `RUN/40-briefs`, `RUN/60-outputs`, `RUN/deliverables` exist (`New-Item -ItemType Directory -Force`); game mode also `RUN/20-analysis/hud`.
7. **Size the work**: `T config get agents` shows `scan_chunks_streamer` (6) and `scan_chunks_game` (5): the scan makes one block per that many chunks (the scan agents are fast Haiku agents, 6 at a time), so a 4-hour stream is about 14 blocks in 3 waves; a short stream is one or two blocks.
   The user's `notes`, `streamer` and `only` go into `state.json` (`T state --run RUN set notes="..." only=shorts`).
8. `T state --run RUN set stage=started next_skill=cc-profile` (streamer) or `next_skill=cc-profile-game` (game).

## Never
- Never move, rename, delete or rewrite a chunk, a sheet or a transcript. The run's media is read-only for the whole command.
- Never ask the user anything but the missing run (the user: the agents decide). The mode is decided here, and never asked.

## Hand-off
Invoke Skill `cc-profile` (streamer mode) or `cc-profile-game` (game mode).
