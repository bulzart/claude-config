---
name: cc-start
description: /create-clips phase 1: take the run folder, check what the recorder and processor produced, set up the analysis folders, size the work. Internal to that command.
user-invocable: false
---

# cc-start: intake

> `CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (every call prints one JSON object on its last line; run through PowerShell) · `RUN` = the run folder.

## Read now
- `CC/README.md` (the contract: the run layout, rec time, the chunk table). Nothing else yet.

## Steps
1. **Arguments** (`$ARGUMENTS`): the run folder (a path, or a session name under `runs_root`), then optional `only=shorts|long`, `notes="..."` (what the user knows: the guest, the topic, what they want), `streamer="Name"`.
   No run given: `T status` lists the runs; with exactly one run that has chunks, take it, otherwise report the list and stop (that is the only time to ask).
2. **The run**: `T status --run <arg>` (stages per chunk, free space, totals). Take what is there: a chunk with stage `failed` or `pending` is listed and skipped; `T chunks --run RUN` is the table.
   The recording may still be growing (a watcher running): the chunk table at this moment is the run for this pass; record it (`T state --run RUN set snapshot_chunks=<n>`) and use only those chunks. No processed chunk at all: stop and say what to run (`T watch`).
3. **Facts to hold**: channel, date, number of chunks and total length, the title and category changes (`00-inventory/stream-meta.json`), the source quality (`probe.json` of a chunk), gaps and skipped ads, free space on the drive.
   Read `RUN/00-inventory/stream.md` once (the table of numbers per chunk).
4. **Tools**: `T doctor` must show ffmpeg and ffprobe working; `T sfx-scan --run RUN` catalogues the sound-effects folder (`30-assets/sfx.md`; it fails plainly when the folder is missing). CapCut running is noted (the build needs it closed), not a blocker yet.
5. **Folders**: `RUN/20-analysis/blocks`, `RUN/40-briefs`, `RUN/60-outputs`, `RUN/deliverables` exist (`New-Item -ItemType Directory -Force`).
6. **Size the work**: the chunk count decides the scan: `T blocks --run RUN --chunks N` with N = 8 to 12 so that at most about 12 blocks result (6 scan agents at a time, two rounds at most); a short stream is one or two blocks.
   The user's `notes`, `streamer` and `only` go into `state.json` (`T state --run RUN set notes="..." only=shorts`).
7. `T state --run RUN set stage=started next_skill=cc-profile`.

## Never
- Never move, rename, delete or rewrite a chunk, a sheet or a transcript. The run's media is read-only for the whole command.
- Never ask the user anything but the missing run (the user: the agents decide).

## Hand-off
Invoke Skill `cc-profile`.
