# Chunk processing (`cc.py watch`, `cc.py ingest`)

Contract: `../README.md`. This is the how-to. Every command prints one JSON object on its last line; PowerShell only (Git Bash forks fail on this PC).

```
$PY = "C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe"
$CC = "C:\Users\Bulzart\.claude\create-clips\scripts\cc.py"
```

## Start it

```
& $PY $CC doctor                 # ffmpeg, modules, the Whisper model, free space (needs ok: true)
& $PY $CC watch                  # leave it open while the extension records; Ctrl+C stops, the next start resumes
& $PY $CC watch --once           # process what is in the inbox now, then exit
```
`watch` polls `Downloads\twitch-chunks\<channel>\<session>\` (config `inbox_dir`). A chunk counts as landed when its `chunk-NNNN.mp4` has no
`.crdownload` sibling, its size has been stable for 1.5 s and its `chunk-NNNN.json` sidecar is there (it waits up to 20 s for it, then goes on without).
It creates the run `Documents\stream-clips\runs\<session>` from the folder name and prints one line per chunk to stderr, with the processor that did it.
One watcher at a time (`runs\.watch.lock`, a dead pid's lock is taken over).

### Two processors (config `watch.workers`, default 2; `watch --workers N`, env `CC_WORKERS`)
One processor was slower than the stream (a 3-minute chunk took 4 to 7 minutes on a busy PC), so the recording was never caught up with. The watcher now runs two processors at the same time, each on its own chunk:
- **live** takes the NEWEST chunk that is ready (the one just recorded), so the end of a recording is never left behind;
- **backlog** takes the OLDEST (the ones left behind), so nothing waits for ever. Both work inwards until they meet. With one chunk ready the first free processor takes it; `--workers 1` is the old one-at-a-time, in number order.
- **Rec times stay right in any order.** A chunk's rec start is the sum of the durations before it, and its sheets and text views carry that time. So before a processor starts, the watcher probes the real duration of every ready chunk (one ffprobe of the file in the inbox) and enters it in the chunk table;
  the live processor can then start on the newest chunk with the older ones still waiting, and nothing has to be made twice. A chunk that arrives late (a lower number after higher ones) is still caught by the stale mechanism: a free processor re-makes the sheets and text views of the chunks whose rec start moved.
- **One Whisper model serves both** (loaded once, thread-safe; faster-whisper's `num_workers` = `whisper.parallel`, default the number of processors), and the two transcriptions really run side by side. `whisper.cpu_threads` is per transcription (default 4 each). A gate keeps the number of simultaneous transcriptions at `whisper.parallel`: set it to 1 and the second processor waits its turn for Whisper while it can still do the other steps.
- `status` shows `pending` for a chunk that is queued (its duration is already in the table) and `processing` for one a processor is working on; the `processed` list of `watch --once` names the processor and the start and end of every chunk.
- Tested by `tests\test_workers.py` (the assignment rule, one model load, six real chunks processed by both processors with rec starts and sheets right, `--workers 1` in order, a late lower chunk).

## Starting it by itself (opt-in, one-time, removable): `scripts\install-background.ps1`

Without this, `watch` is started by hand as above. The installer (PowerShell, no admin rights; `-DryRun` shows what it would write; `-Mode status` changes nothing):
- `-Mode native`: registers the Chrome native-messaging host `com.createclips.processor` (a registry key under HKCU plus `native-host\*.json` and a `.bat`). When you press Record on Twitch the extension
  connects to `scripts\native_host.py`, which starts `cc.py watch` detached if it is not running (it outlives Chrome and finishes the backlog) and answers status requests, so the Twitch page can show
  "processed 3 of 4". Needs the extension loaded once (its id is in `twitch-chunk-recorder\native-host\extension-id.txt`).
- `-Mode task`: a Scheduled Task `CreateClipsWatcher` that starts the watcher hidden at every logon (always on, even without Chrome).
- `-Mode remove`: deletes the key, the manifest, the launcher and the task. `tests\test_native_host.py` tests the host's protocol without Chrome.
An idle watcher drops the Whisper model after `whisper.idle_unload_s` (600 s) so it does not hold about 1.5 GB of memory while nothing arrives; the next chunk loads it again (about 3 s).
The host's log is `logs\native-host.log`, the background watcher's `logs\watch.log`.

## What appears where (per chunk `RUN\10-media\C0012\`)

| File | What |
|---|---|
| `chunk.mp4` | the chunk, moved from the inbox (a rename on one drive: no copy, no extra space) |
| `sheets\sheet-01.jpg` ... | contact sheets: a frame every 0.75 s (4 per 3 s), 30 per sheet = 22.5 s, 5 x 6 cells of 240 x 135 |
| `sheets\overview.jpg` | every 10th frame (7.5 s apart), 24 cells: the chunk at a glance |
| `frames.json` | one row per frame: `i, t, rec, sheet, cell, rms_db, chat_per_s, diff_prev, t_pts, label` |
| `transcript.json` / `.txt` | Whisper words with times (`.txt`: one readable line per segment, rec times) |
| `audio.json`, `audio-profile.json` | loudness per 0.5 s, its summary and the loud-jump events |
| `timeline.md` | one row per second: speech, loudest 0.5 s, motion, chat msgs/s |
| `digest.json` | the chunk's row of `00-inventory\stream.md` as data |
| `probe.json`, `chunk.json`, `chat.json` | ffprobe facts, the extension's sidecar and chat file |
| `report.json` / `report.md` | the chunk reporter's observations of the chunk (below); `report.md` is the readable one the agents read |

Run level: `00-inventory\chunks.json` (the chunk table with the stages of every chunk), `stream.md` (one row per chunk, plain percentiles, the ten
largest seconds by chat rate / loudness / motion), `stream-meta.json` (title and game per chunk, the changes), `state.json`, `logs\ingest-C0012.log`.

**Frames are never kept.** They are written one sheet at a time (30), the sheet is drawn, and those frames are deleted the moment the sheet is saved
(`frames.json -> frames_deleted: true, leftover_frames: 0`). The 16 kHz wav is deleted after the transcript (`audio.keep_wav` keeps it).

## The chunk reporter (a headless Haiku session per chunk, while the stream is downloaded)

When a chunk has its sheets, audio numbers and text views, the watcher queues a **report**: a separate `claude -p` session (config `report`: Haiku 5.5, effort high, the Read tool only, no MCP servers, the user's settings and hooks left out, nothing saved as a conversation, at most `parallel` = 2 at once)
opens the chunk's overview and dense sheets, `timeline.md`, `transcript.txt`, `digest.json`, `audio-profile.json`, `chunk.json` and `chat.json`, and writes what they show. The brief it works from is `reference\reporter.md`:
**observations only, never a decision**: no verdict, no label such as "ace" or "highlight", no name corrected or guessed, nothing ranked, kept or skipped. The command's agents read `report.md` instead of opening every sheet, so by the time `/create-clips` runs the reading is already done.
- **Files:** `report.json` (whitelisted fields only: `look` per sheet, `sound`, `speech`, `chat`, `seen_and_heard`, `unclear`; a field the brief does not ask for is dropped and counted in `dropped`) and `report.md` (the same, readable). `made_by` records the model, effort, seconds, cost, turns, attempts and which files the session **really opened** (read from its Read calls in the stream, not from what it claims).
  A file it did not open after the one retry is listed in `made_by.not_opened`, in `warnings` and in `report.md`. The chunk's row in `chunks.json` has a `report` field (`status` done|failed|running, model, at, seconds, cost_usd, attempts, error).
- **Never in the way:** a report runs beside the chunk processing and never changes a chunk's own status; a failed report leaves the chunk `done`. A report is current while its source signature (rec span, sheets, text views) matches: a chunk re-made because its rec start moved, or whose transcript arrived later, has a STALE report and gets a new one.
- **Commands:** `status` shows `report:ok|--|STALE|FAIL|run` per chunk and the `reports` counts; `report --run RUN` makes every missing, stale or failed report now, `--parallel N` sessions at once (about a minute each; cost about half a cent to a few cents per chunk), `--chunk C0007`, `--force`, `--all`, `--dry-run`.
  The watcher retries a failed report once more (`max_attempts` 2) and then leaves it to `report`. `watch --no-report` (or `report.enabled: false`, or env `CC_REPORT=0`) starts no reporter.
- **The claude CLI:** the real `claude.exe` must come first on PATH (the npm `claude.cmd` shim cuts a command at 8191 characters; with a shim the brief travels on stdin instead). `doctor` shows which one it found; config `report.claude_bin` or env `CC_CLAUDE_BIN` names it. A rate limit stops a chunk's attempts at once and is reported as `rate limited`.
- **Restart the watcher after an update:** a running watcher keeps the code it started with (stop it and start `watch`, or restart the `CreateClipsWatcher` task, to pick up the reporter).

## The ready alert (a Windows notification when a run can go to /create-clips)

When a recording has ended and every chunk of it is processed and reported, the watcher shows **one Windows notification**: "Create-clips is ready: <channel>", how many chunks were processed (and which failed), how much stream that is,
whether the reports are in, and the exact command, `Run: /create-clips <the full run folder path>`. It is a reminder toast: it stays on screen until you dismiss it (Dismiss button) and plays the reminder sound.
- **Ready means (facts only, nothing judges the footage):** the recorder wrote its end into `session.json` (you stopped it, the stream ended, the size limit or the disk guard hit ...) or nothing has arrived for `notify.idle_minutes` (15: a recorder that died cannot write its end);
  no chunk file of the session waits in the inbox and the recorder's own chunk count (`session.json -> chunks`) is accounted for; no chunk is pending or being processed; every chunk report is made or has failed for good (when the reporter is on).
  A chunk that failed does not hold the alert back: the alert names it and its title says "with problems"; when nothing could be processed it says "nothing usable" and does not offer the command. An end the user did not ask for (low disk, size limit, stalled, Chrome restarted) is named in the text.
- **Once per state:** `state.json -> ready_notified` holds a fingerprint of the chunks and reports that were announced. A watcher restart repeats nothing; a later chunk of the same run is a new state and gets a new alert.
  At start, and once a minute, the watcher also takes up a run whose recording ended within `notify.catchup_hours` (24) and that nobody was told about (the watcher was off, or was restarted in between).
- **How it is shown:** `scripts\notify.ps1` (Windows PowerShell 5.1, started hidden) sends a toast under the registered app id of Windows PowerShell, so nothing is registered or changed on this PC; the banner reads "Windows PowerShell".
  If notifications are switched off for that app or for Windows, a topmost message box with the same text appears instead (`doctor` says which applies). The toast is sent from a background thread: a slow notification never holds up a chunk.
  Focus assist / Do Not Disturb keep a toast in the notification centre without the banner and the sound.
- **Commands:** `notify --run RUN` (check; send when ready and not yet announced; `--dry-run` says what it would send and records nothing; `--force` sends anyway: a run that is not ready gets a clearly marked "NOT ready" note that is not recorded as an announcement), `notify --test` (a test notification),
  `status --run RUN` (the line `ready for /create-clips: yes` or `not ready yet: <why>`, and `ready` in the JSON), `doctor` (the "Windows notification" line).
- **Settings:** `config.json -> notify` (`enabled`, `persistent` = stays until dismissed, `sound`, `idle_minutes`, `catchup_hours`); `watch --no-notify` or env `CC_NOTIFY=0` turns the automatic alerts off (the `notify` command still sends when asked).
  Tests set `CC_NOTIFY_BIN` / `CC_NOTIFY_BOX_CMD` to the stand-ins in `tests\fake_notify.py`, so no test shows anything. Like the reporter, the alert needs a restarted watcher after an update.

## Reading a sheet

Header: `channel | C0012 | rec 0:33:00.00-0:33:22.50 | sheet 1/8 | 0.75 s per frame`. Left to right, top to bottom. Under every frame its OWN time:
`0:33:45.75  +45.75` = rec time (seconds since the start of C0001, recorded content only) and the offset in this chunk. Under that, a green bar
(loudness, -60..0 dB) and an orange bar (chat messages per second, 0..20; absent without chat). A portrait source gets 6 x 5 cells of 138 x 245.
Rec time is the time every agent uses; `cc.py locate` converts to chunk + offset.

## Looking closer (what the agents use)

```
& $PY $CC locate --run RUN --at 0:33:45.75             # chunk, offset, file      (--chunk C0012 --offset 45.75 for the other way)
& $PY $CC window --run RUN --from 2025 --to 2045 --what transcript,timeline,chat,audio
& $PY $CC frame  --run RUN --at 2025.5 [--max-width 1280] [--crop 0.6,0.5,0.4,0.5]   # one frame, full size, into 30-assets\frames\
& $PY $CC sheet  --run RUN --from 2020 --to 2030 --step 0.25 [--cell-w 360 --cols 4 --rows 4]   # a dense sheet into 30-assets\sheets\
& $PY $CC status [--run RUN]    &  chunks --run RUN    &  stream-table --run RUN
```
All of them cross chunk boundaries. `sheet` also deletes its frames right after drawing.

## Settings (`config.json`; env overrides for tests)

`frames` (interval 0.75, 5 x 6, 240 x 135, jpeg 86), `audio` (window 0.5, `keep_wav`, loud jump 10 dB), `whisper` (model medium, device cpu, compute int8,
language en, beam 5, VAD on, `initial_prompt`), `min_free_gb` (3). Optional keys read with defaults: `audio.loud_jump_floor_db` (-45), `frames.chat_bar_ref` (20),
`whisper.cuda_compute_type` (float16), `whisper.cpu_threads` (per transcription, default 4), `whisper.parallel` (transcriptions at the same time, default = the processors). `report` (enabled, model `claude-haiku-5-5`, effort high, parallel 2, timeout_s 420, max_turns 30, max_attempts 2, claude_bin, setting_sources project).
`notify` (enabled, persistent, sound, idle_minutes 15, catchup_hours 24). `watch` (workers 2: the processors working on chunks at the same time).
Env: `CC_RUNS_ROOT`, `CC_INBOX`, `CC_WHISPER_MODEL`, `CC_WHISPER_DEVICE`, `CC_MIN_FREE_GB`, `CC_REPORT` (0 = no reports), `CC_CLAUDE_BIN`, `CC_REPORT_PARALLEL`, `CC_REPORT_TIMEOUT`, `CC_NOTIFY` (0 = no automatic alerts), `CC_NOTIFY_IDLE_MIN`, `CC_WORKERS`, `CC_CONFIG` (another config file; tests).
Per run: `new-run --language auto --prompt "names, terms"` (kept in `state.json -> settings.whisper_override`).

## Speed with one and with two processors (measured 2026-11-13, BLAST Premier run, 1080p60 source chunks, a busy PC)

- **One processor** (the live test): a 180 s chunk took 4 to 7 minutes (probe 1-91 s, audio 1.5-30 s, sheets 25-104 s, transcript 120-383 s), so a recording was still being worked on about 10 minutes after it stopped.
- **Whisper medium on this 6-core CPU is the limit for the transcript step, not the number of processors.** Two 60 s excerpts: 52 s one after the other (4 threads each), 48 s at the same time (4 threads each, each one about 1.7 x slower), 62-73 s with 3 or 6 threads (the PC was busier then, so these runs are only roughly comparable). The words were identical every time.
  So `whisper.parallel` (how many transcriptions may run at once, default = the number of processors) and `whisper.cpu_threads` (default 4) stay at their defaults; a processor that has to wait for its turn says so in its transcript (`waited_for_turn_s`).
- **What the second processor does win:** the other steps of one chunk (probe, audio, sheets, digest: 30 to 200 s on a busy PC) run beside the other processor's transcription, and the newest chunk never waits behind the backlog. How much that is end to end depends on the PC's load; the per-chunk seconds in `chunks.json` and the log lines `(live)` / `(backlog)` show it on every recording.
- **The one big transcription speedup is the GPU** (`whisper.device: "cuda"`, below), left off because the GPU belongs to FLUX Klein and ACE-Step.

## Speed of one processor on an idle PC (a 180 s 1280x720 60 fps chunk)

Sheets about 4-5 s; audio 0.3 s; **Whisper medium on the CPU (int8) about 125-130 s** (0.7 x real time, so one live stream is kept up with; two streams at once are not);
whole chunk about 134 s. Opt-in GPU: `whisper.device: "cuda"` (it borrows the CUDA 12 DLLs of ACE-Step's torch folder, `whisper.cuda_dll_dir`): about 4 s for a
24 s clip, roughly 10 x faster; the CPU stays the default because the GPU belongs to FLUX Klein and ACE-Step (memory guard). `device: "auto"` tries CUDA and falls back.

## Troubleshooting

- **Nothing happens**: `watch` prints the inbox it looks at; chunks need `chunk-NNNN.mp4` (not `Unconfirmed ... .crdownload`). `status` lists `inbox_waiting`.
- **`refused: free space`**: below `min_free_gb` on the runs drive; free space (chunks are big), the watcher retries every 30 s.
- **A chunk shows `failed`**: `status --run RUN` shows which stage; the reason is in `logs\ingest-Cnnnn.log`. Fix it, then `ingest --run RUN --chunk RUN\10-media\Cnnnn\chunk.mp4`
  (finished stages are skipped; `--force` redoes all). A corrupt file fails at `probe` and is moved into its chunk folder, never retried by the watcher.
- **Whisper cannot load**: `doctor` says whether the model is cached (`Systran/faster-whisper-medium`); it falls back to small/base/tiny and records `model_fallback`.
  Keep `av<19` (PyAV 19 breaks faster-whisper 1.2.1).
- **Chunk numbers arrive out of order**: rec starts are recomputed; chunks made with an old rec start are flagged `stale_rec` and re-made (sheets and text views, no Whisper) automatically by a free processor.
- **Chunks are not finished in number order**: with two processors that is normal (the live one starts on the newest chunk, the backlog one on the oldest); `status` and the rec times are right at every moment. `watch --workers 1` goes back to one at a time.
- **Another watcher is running**: one at a time; stop it, or a dead one's lock is replaced at the next start.
- **Stop the transcript for now**: `--skip-whisper` (status `pending`); a later `ingest` without it makes the transcript.
- **Chunks on another drive than the runs**: moved by copy through a `.part` file (needs the room).
- **Terminal windows pop up while chunks are processed**: a program started without `creationflags=NO_WINDOW` from the `pythonw.exe` watcher gets its own console, which Windows Terminal shows as a window per call (seen 2026-11-13: one per ffmpeg call).
  Every script starts its programs through `cc_common.run_cmd` (or with the flag); `tests\test_nowindow.py` fails when one does not. A running watcher keeps the code it started with: restart it after an update.
- **No notification appears when a run is done**: `doctor` shows the "Windows notification" line (Settings > System > Notifications: "Windows PowerShell" must not be off); `notify --test` sends one; `status --run RUN` says whether the run is ready and why not;
  `state.json -> ready_notified` says whether and how it was announced (`toast`, `messagebox`, `failed`); `logs\background.log` has the `[notify]` lines. A run is announced once per state: `notify --run RUN --force` shows it again.
- **Chunk files do not appear in the inbox although the recording runs**: Chrome's "Ask where to save each file before downloading" (Settings > Downloads) is on in that profile: every file waits for a Save As click. Turn it off.
- **No reports appear**: `doctor` shows the claude CLI line (found or not); `status` shows the `report:` column and `logs\report-Cnnnn.log` the last attempts (turns, cost, files opened, errors). `report --run RUN` makes the missing ones now.
