# create-clips: the clip-farming toolkit for livestreams

Twitch livestream -> **Twitch Chunk Recorder** (Chrome extension, `C:\Users\Bulzart\Documents\twitch-chunk-recorder`) saves 3-minute MP4 chunks ->
**`cc.py watch`** (this toolkit) turns each chunk into frame sheets, a Whisper transcript and per-second numbers inside a run folder ->
**`/create-clips <run folder>`** (Claude Code command) researches the stream, mines its moments and builds CapCut projects (shorts and long-form).

The command has **two modes, a captions choice and (streamer mode) a videos choice, and you pick them at the very start** (`/create-clips` asks them in one dialog; `mode=streamer|game`, `captions=on|off`, `only=long|both` and `shorts=concentrated|normal` in the command skip the questions), each mode with its own logic:
- **streamer clipping**: a person is the show (jokes, reactions, arguments, chat, lingo): ONE brief research agent on the streamer, their audience and the topic, moments, long videos (whole watches of about 25 minutes to an hour) and, when you pick them, shorts too (the question: long videos only, or long videos + shorts, and with shorts a level: concentrated, the one to three best, or normal, about 5 to 10), with matching sound effects.
- **game clipping**: a broadcast of a match (BLAST Premier CS2, a Dota 2 game, Valorant, League ...): ONE brief research agent on the game, the event and the teams, then **rounds and fights** as the units
  (how much of each to take, which to drop, which small ones to keep because a viewer would lose the detail). **Long condensed-match videos only: no shorts, no sound effects**, one video and one CapCut project per map or game (a recording with several different matches gives each its own, never mixed); sponsorship and the like (sponsor stings, betting segments, ad breaks) is cut out totally.

While a stream is downloaded, a separate headless **Haiku reporter** (`claude -p`, Haiku 5.5, high effort) writes a report of every processed chunk: what its sheets, audio numbers, transcript and chat show. Observations only, never a verdict, a label or a name correction (`reference/reporter.md`).
`/create-clips` then starts from those reports, so nothing has to be spawned to read the raw chunks.

This file is the **contract** between the three parts. Everything that crosses a part (file names, JSON fields, times) is defined here.

## Quick start
1. **Once**: `chrome://extensions` -> Developer mode -> Load unpacked -> `C:\Users\Bulzart\Documents\twitch-chunk-recorder`. Check `T doctor` (ffmpeg, Whisper medium cached, free space).
2. **Let the processor start by itself** (one time, opt-in, removable): double-click `C:\Users\Bulzart\.claude\create-clips\scripts\install-background.cmd` in Explorer (it registers the Chrome helper and a logon task; `uninstall-background.cmd` undoes it).
   Do not use the `!` prefix of the Claude prompt for it: that runs through Git Bash, which cannot start on this PC. The extension then starts `cc.py watch` in the background when you press Record. Or start it by hand in a PowerShell window: `& "C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Bulzart\.claude\create-clips\scripts\cc.py" watch`.
3. **Record**: open a streamer's Twitch page and press the **Record** button the extension puts at the bottom right of the page (or type the login in the extension's popup, or put channels on the auto-record list).
   Chunks land in `Downloads\twitch-chunks\...` every 3 minutes and the processor turns each one into sheets and a transcript inside `C:\Users\Bulzart\Documents\stream-clips\runs\<session>`.
   When the recording has ended and every chunk and its report is done, Windows shows **one notification** (it stays until you dismiss it) with the exact `/create-clips <run folder>` command (`docs/processing.md`, "The ready alert").
   Chrome's "Ask where to save each file before downloading" (Settings > Downloads) must be OFF in the recording profile, or every chunk file waits for a Save As click.
4. **Clip**: in Claude Code, `/create-clips <that run folder>` (optionally `notes="guest was X, topic Y"`, `mode=streamer|game`, `captions=on|off`, `game="Counter-Strike 2"`, `only=long|both|shorts` and `shorts=concentrated|normal` (streamer mode)). It asks you first which mode this is, whether the videos get captions and, in streamer mode, whether to make long videos only or long videos plus shorts, and when shorts are made how many (concentrated or normal), unless you gave `mode=`, `captions=`, `only=` and `shorts=` (captions are on by default; the videos and the shorts level you always pick).
   Read `RUN\deliverables\README.md` at the end (game mode also writes `RUN\deliverables\rounds.md`: every round or fight with what was done with it); open the CapCut projects, check the first frame, export.
   Models: the chunk reports are written by the Haiku reporter (`config.json -> report`); research, analysis, planning, editing and the main session use whatever you picked with `/model`. Nothing asks you which.
Space: source quality (1080p60, about 8 Mbps) is about 3.6 GB per hour of stream, 720p60 about 1.5 GB. C: has only about 8 GB free until the new 1 TB M.2 SSD the user is buying (2026-11-12) is installed; then set Chrome's
download folder (chrome://settings/downloads) to the SSD and tell the toolkit once: `T config set inbox_dir=<ssd>/twitch-chunks runs_root=<ssd>/stream-clips/runs` (`T config` shows both and their free space; existing runs stay where they are).

## Paths and names

| What | Value |
|---|---|
| `CC` (this toolkit) | `C:\Users\Bulzart\.claude\create-clips` |
| `PY` | `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe` (faster-whisper, Pillow, numpy, opencv, librosa; `av<19`) |
| `T` | `"$PY" "$CC\scripts\cc.py"` (every command prints one JSON object on its last line) |
| Extension | `C:\Users\Bulzart\Documents\twitch-chunk-recorder` |
| Inbox (where Chrome saves the chunks) | `C:\Users\Bulzart\Downloads\twitch-chunks` (`config.json -> inbox_dir`) |
| Runs | `C:\Users\Bulzart\Documents\stream-clips\runs\<session>` (`config.json -> runs_root`) |
| SFX library | `C:\Users\Bulzart\Documents\sound_effects` (read-only, user's) |

A **session** is one continuous recording of one channel. Its id is `<YYYYMMDD-HHMMSS>-<channel>` (local time of the start; channel lowercase `[a-z0-9_]`).
One session = one run folder, with the same name. Shell: use PowerShell (Git Bash forks fail on this PC).

## 1. What the extension saves (inbox)

```
Downloads\twitch-chunks\<channel>\<session>\
  session.json         written at the start, overwritten at the stop (adds ended_at, chunks, reason)
  chunk-0001.json      sidecar, saved BEFORE its mp4 (so the mp4's arrival means the sidecar is there)
  chat-0001.json       optional (chat capture on), saved before the mp4
  chunk-0001.mp4       one regular MP4 (moov first), H.264 + AAC, samples copied unchanged, ~180 s
  chunk-0002.* ...
```
A file still downloading is `*.crdownload`: never read it. Chunk numbers start at 1 and never repeat inside a session.

`chunk-NNNN.json` (`schema: "tcr/1"`):
```json
{"schema":"tcr/1","channel":"kaicenat","session":"20261112-111200-kaicenat","chunk":1,"file":"chunk-0001.mp4",
 "t0_utc":"2026-11-12T11:12:08.877Z","t1_utc":"2026-11-12T11:15:08.877Z",
 "duration_s":180.0,"segments":90,"bytes":123456789,
 "quality":{"name":"720p60","width":1280,"height":720,"fps":60,"bandwidth":3322199,"codecs":"avc1.4D401F,mp4a.40.2"},
 "gap_before_s":0,"ads_skipped_s":0,"ended_by":"duration",
 "stream":{"id":"317213325397","title":"...","game":"Just Chatting","viewers":12345,"uptime_s":34006,"started_at":"2026-11-12T01:45:00Z"},
 "tool":{"name":"Twitch Chunk Recorder","version":"1.0.0"}}
```
`t0_utc`/`t1_utc` = the playlist's PROGRAM-DATE-TIME of the chunk's first segment and its end (null when the playlist gave none). `ended_by` is
`duration` | `init-change` | `gap` | `stop` | `stream-ended`. `gap_before_s` = seconds of the stream that are missing between the previous chunk's end and
this chunk's start (by program date time; the stream an ad session never received, lost segments and reconnects). `stream` is a GQL snapshot taken at the chunk's start, `null` fields when unknown.

**Ad chunks** (the user, 2026-11-14: "just do not skip anything, whether ad or not ad, and the agents then exclude batches of ads when they analyse"): the recorder saves the segments Twitch marks as ads (a stitched-ad range or a title that is not `live`) as
chunks of their own, numbered in sequence between the stream's chunks, and their sidecar carries two more fields after `ended_by`: `"kind": "ad"` and `"ad": {"segments_by_range": n, "segments_by_title": n, "titles": [...]}`. A stream chunk has neither field. An ad chunk has no chat file and is never dropped, however short.
`ads_skipped_s` is then only the ad seconds that could not be recorded (a segment that would not download): normally 0. The marker is **Twitch's word, a fact the processor copies into the chunk table (`kind`, `ad`) and shows (`(ad-marked)` in `stream.md`, `AD-MARKED` in `T status` and `T chunks`, `ad_chunks` per block and `ad_batches` in `T blocks`), never a verdict:**
an ad chunk is processed like any chunk (sheets, audio numbers, transcript, digest, report; the report says what it shows), rec time runs through it, and the agents decide, when they analyse, which batches (consecutive marked chunks = one ad break) really are ads and leave those out of every video
(mining agents: `ad_batches` with a verdict `ad|stream|mixed` in their block file; the planner: `ad-batches.json` and `avoid.json` kind `ad`). → `reference/moment-mining.md`, `reference/portfolio.md`.

`chat-NNNN.json` (`schema: "tcr-chat/1"`), no user names, ever:
```json
{"schema":"tcr-chat/1","chunk":1,"t0_utc":"...","duration_s":180.0,"bin_s":1,"lag_hint_s":8,
 "per_second":[0,3,5,...],
 "tokens_per_10s":[[["KEKW",34],["LMAO",20]], ...],
 "samples":[{"t":12.5,"text":"..."}]}
```
`per_second[i]` = messages whose wall-clock arrival fell in `[t0_utc + lag_hint_s + i, +1 s)`: the recorder already shifts chat by `lag_hint_s` (viewers react
about that long after the moment, because of the stream's delay), so index i is the chunk offset i and a reader uses it as it is. `tokens_per_10s[j]` covers offsets
`[10j, 10j+10)` and `samples[].t` is the chunk offset the message is aligned to. The chat file is therefore saved about `lag_hint_s` after the chunk ends (still before its mp4).

`session.json`: `{"schema":"tcr-session/1","channel","session","started_at","ended_at","reason","quality_pref","chunk_seconds","chat":true,"stream":{...},"chunks":N}`.
`reason` is set when the recording ends: `stream-ended` (the extension stops by itself when the stream ends), `user` (you pressed Stop), `size-limit` (the optional GB cap), `low-disk`, `stalled` (no new video for 10 minutes),
`browser-restarted`, `stopped`, `save-failed...`, `offline...`. `cc.py watch` copies a changed session.json into the run (`00-inventory/session.json`) and records `recording` and `stream_ended` in `state.json` (compared with the file's content, so a recording that ended before its
first chunk was processed gets its end recorded too), which `/create-clips` and the ready alert read to know whether the recording is complete.

## 2. The run folder (made by `cc.py`, numbered like an analyze-with-loupe run)

```
RUN\
  state.json                    run facts + per-chunk status (cc.py writes; commands read)
  00-inventory\
    chunks.json                 the chunk table (below)
    stream.md                   one row per chunk: the numbers an agent scans first (gather-only)
    stream-meta.json            channel, session, title/game timeline from the sidecars
  10-media\
    C0001\                      one folder per chunk (like AWL's V03)
      chunk.mp4                 the chunk (moved from the inbox: same drive, no copy)
      chunk.json  chat.json     the sidecars, copied
      probe.json                ffprobe facts
      report.json  report.md    the Haiku reporter's report of the chunk (observations only, below); report.md is what the agents read
      sheets\sheet-01.jpg ...   the contact sheets (frames every 0.75 s, 30 per sheet = 22.5 s) and overview.jpg
      frames.json               one row per frame: t (chunk s), rec (rec s), sheet, cell, rms_db, chat_per_s, diff_prev
      audio.json                loudness per 0.5 s; audio-profile.json: its summary
      transcript.json           Whisper medium words; transcript.txt: the same as readable lines
      timeline.md               per-second table (speech, loudness, motion, chat)
      digest.json               the chunk's row of stream.md as data
  20-analysis\                  /create-clips: recon, the context brief, clip criteria, lexicon, the block files, moments, richness, portfolio
                                game mode adds: hud\ (regions.json, the score and clock readings, states.txt), match-map.md, game-profile.md (a game the library lacks), rounds.json (every round or fight with its keep verdict)
  30-assets\                    /create-clips and cc.py: extra frames, dense sheets, censor clips, caption files, sfx.json
  40-briefs\                    /create-clips: one brief per planned video
  60-outputs\<video>\           /create-clips: EDL, captions, build plan, CapCut project name, report
  deliverables\                 README with the CapCut projects made
  logs\                         cc.py logs (watch.log, ingest-<chunk>.log)
```

### Times (read this once)

- **rec time** = seconds since the start of C0001, counting every recorded chunk, an ad-marked one too (a gap between chunks does NOT add time). Every time an agent
  reads or writes (sheets, transcripts, EDL, moments) is rec time. Display `H:MM:SS.cc` (`0:33:45.75`) or plain seconds (`2025.75`).
- **chunk offset** = seconds since the start of that chunk's mp4 (`+45.75`).
- `rec = chunk.rec_start_s + offset`. `rec_start_s` of a chunk = sum of the real durations (ffprobe) of the chunks before it.
- Chunks are about 180 s but not exactly (they end on a 2 s segment boundary); always map through the chunk table (`cc.py locate`), never `index * 180`.
- `t0_utc` (wall clock) is context only (when it happened, gaps between chunks).

`00-inventory/chunks.json`: list of `{id:"C0001", index:1, file:"10-media/C0001/chunk.mp4", rec_start_s, duration_s, t0_utc, t1_utc, gap_before_s,
ads_skipped_s, ended_by, kind:"ad" (only on a chunk the recorder marked as an ad), ad:{...} (the same), quality:{...}, stream:{...}, status:"pending|processing|done|failed", stages:{move,probe,audio,sheets,transcript,digest: true|false|"failed: why"},
sheets:N, frames:N, words:N, speech_seconds, language, model, device, seconds:{audio,sheets,transcript}, error, processed_at}`.

`state.json`: `{schema:"cc/1", channel, session, run, created, inbox, settings:{frame_interval_s,frames_per_sheet,...}, chunks:{"C0001":{status,...}},
stage (the /create-clips stage), next_skill, videos:{}, recording:{started_at,ended_at,reason,chunks,chunk_seconds,quality_pref}, stream_ended,
ready_notified:{at,fingerprint,chunks,done,failed,how,ok,error}}` (`recording` and `stream_ended` come from the recorder's session.json; `ready_notified` is what the ready alert announced: once per state of the run).

### Per-chunk file formats

- `frames.json`: `{"interval_s":0.75,"cols":5,"rows":6,"per_sheet":30,"frames":[{"i":0,"t":0.0,"rec":0.0,"sheet":1,"cell":0,"rms_db":-31.2,"chat_per_s":4,"diff_prev":null}, ...],"frames_deleted":true}`.
  Frame i is at chunk offset `i * 0.75`. `diff_prev` = mean absolute difference (0-255) of a 64x36 grey copy against the previous frame.
- sheet header: `kaicenat | C0012 | rec 0:33:00.00-0:33:22.50 | sheet 1/8 | 0.75 s per frame`; second line: legend. Each cell has under it its own timestamp
  `0:33:45.75  +45.75` (rec time and chunk offset), and a 3-px loudness bar (and a chat bar when chat exists) at the bottom of the label strip.
- `audio.json`: `{"window_s":0.5,"rec_start_s":...,"rms_db":[...],"peak_db":[...],"clip_seconds":N}` (dBFS, floor -90).
- `audio-profile.json`: mean/median/p90/max RMS dB, loud-jump events (rise of >= 10 dB over the previous 5 s median: `{t,rec,db,jump_db}`), silence share (< -50 dB).
- `transcript.json`: `{"engine":"faster-whisper","model":"medium","device":"cpu","language":"en","language_probability":0.99,"rec_start_s":...,"duration_s":...,
  "segments":[{"start":1.2,"end":4.8,"text":"...","avg_logprob":-0.3,"no_speech_prob":0.01,"compression_ratio":1.4,"words":[{"w":"hello","s":1.2,"e":1.5,"p":0.98}]}],
  "n_words":N,"speech_seconds":S,"wpm_speech_only":W}` (chunk-relative seconds).
- `transcript.txt`: `[0:33:45.75-0:33:50.10] (C0012 +45.75) text` per segment.
- `timeline.md`: `| rec | chunk+off | speech in this second | loudness max dB | motion | chat msgs/s |` one row per second.
- `digest.json`: `{chunk, rec_start_s, duration_s, words, speech_seconds, wpm, speech_share, rms_mean_db, rms_max_db, loud_jumps, motion_mean, motion_max, chat_total, chat_max_per_s,
  chat_peak_rec, top_tokens:[[tok,n]...], first_words, last_words, title, game, viewers, ads_skipped_s, gap_before_s}`.

## 3. cc.py commands (gather-only: they measure, extract and record; they never judge, rank or decide)

Processing (`scripts/cc_proc.py`): `new-run`, `ingest`, `watch`, `status`, `doctor`, `chunks`, `locate`, `window`, `frame`, `sheet`, `stream-table`.
Editing and run state (`scripts/cc_edit.py`): `config` (show, `get <dotted key>`, `set`), `state` (get/set dotted keys), `blocks` (chunk blocks for the mining agents; `--min-blocks M` gives a short recording at least M blocks), `words` (spoken words with start times), `sfx-scan`, `layout-calc`, `grid-frame`
(a full-resolution frame with a 10% grid), `censor` (a blurred copy of only a span and optionally only a region), `edl-check` (resolve an EDL: pieces, the CapCut plan, the finish plan, facts at every cut),
`captions` (cues from the transcript words of the resolved pieces: profanity and slurs masked with one asterisk (`data/caption-masks.json` plus the EDL's `mask_terms`; the `masked` tally), spelling replacements; writes nothing when the run's captions setting is off; the word-box look's plan of texts as facts), `fonts` (the font files the captions can use: family, style, file; `--family` filters), `capcut-name`,
`capcut-build` (**the way every video is built**: ONE command for the whole CapCut project, `capcut-compose` + `capcut-finish` + a read-back with a `problems` list), `capcut-compose` (the whole project in a single `capcut compile` from the resolved EDL, on `data/compose-template`, the chunks used in place: the clips, the sound-effect lanes, the transitions and the word-box caption texts; `--bare` leaves the last two to finish),
`capcut-finish` (what compile has no operation for: zoom keyframes, the background blur, the caption font and entrance (not when the run's captions setting is off), the repair and the clean-up; transitions and captions only on a draft compose did not put them in).
The chunk reporter (`scripts/cc_report.py`, `docs/processing.md`): `report` (make, redo or list the chunks' reports; the watcher queues one after every ingested chunk). `status` shows the `report:` column and the `reports` counts.
The ready alert (`scripts/cc_notify.py`, `scripts/notify.ps1`, `docs/processing.md`): `notify` (check whether a run is fully processed and send the Windows notification once per state of the run; `--test`, `--dry-run`, `--force`); the watcher sends it by itself.
`status` shows the line `ready for /create-clips: yes` or `not ready yet: <why>` and `ready` in its JSON.
On-screen reading for game matches (`scripts/cc_hud.py`, `docs/hud.md`): `hud-read` (OCR of one region at one time), `hud-scan` (OCR of a region over a range: the score, the clock), `region-series` (numbers of regions over time: a kill-feed burst, a replay badge).
Game tabulation (`scripts/cc_game.py`): `hud-states` (the changes of the score as one time-ordered table), `hud-slice` (one reader's readings inside a rec range), `units-merge` (the block files as one `rounds.json`),
`units-verdict` (the planner's keep decisions written next to the cards), `units-check` (facts about round and fight cards: missing fields, overlaps, score changes no unit holds, uncovered stretches),
`units-table` (rounds.json as `deliverables/rounds.md` for the user).
`--run` takes a run folder path or a bare session name under `runs_root`.

The command, its phase skills (`~/.claude/skills/cc-*`: profile, scan, plan and build skills for each mode, plus the shared start, produce and wrap-up) and the references (`reference/*.md`, `reference/games/*.md`) are described in `~/.claude/commands/create-clips.md`;
`tests/run-all.py` runs every test (`test_edit.py` the edit toolkit, `test_game.py` the game tabulation, `test_hud.py` the screen reading, `test_proc.py` the processor, `test_report.py` the chunk reporter (with a stand-in claude, no model call), `test_workers.py` the two processors, `test_notify.py` the ready alert (stand-ins, nothing is shown), `test_nowindow.py` that no script opens a console window, `test_native_host.py` the Chrome helper, `test_masks.py` the caption masks, `test_zoomkeys.py` the zoom keyframes of a draft's timeline copies, `test_docs.py` that every file and skill the docs name exists).

## 4. Rules that hold everywhere

- Scripts gather, agents decide: no verdict, label, rank or gate comes from a script (numbers, facts, peaks lists are fine). In game mode the screen readers and `units-check` report values, changes and gaps; whether a round was a clutch or should be kept is an agent's call.
- Models: the only Haiku is the chunk reporter (`config.json -> report`: Haiku 5.5, effort high, a headless `claude -p` session per chunk, Read tool only); research, analysis, planning, production and the main session use the model the user picked with `/model` (no `model` argument to any agent, never a question about it).
  **The reporter reports, it never decides**: no verdict, no label ("ace", "highlight"), no name corrected, nothing ranked, kept or skipped; every decision is a working agent's. The analysis batch sizes are `scan_chunks_streamer` 10 and `scan_chunks_game` 8 (the agents start from the reports), and a recording always gets at least `scan_min_blocks` 2 blocks so that two agents read it side by side.
- The mode, the captions setting and (streamer mode) the videos choice (`only=long`: long videos only, `only=both`: long plus shorts; with shorts, `shorts=concentrated` or `shorts=normal`) are the user's picks, asked once at the start (one dialog and, when shorts are made, one follow-up) and kept for the run. Game mode makes long-form condensed matches only: no shorts, no sound effects, sponsor stretches cut.
- **Captions** (the user, 2026-11-13): `state.json -> captions` is `on` (the default, also for a run made before the option existed) or `off`. With captions on every second of speech is captioned in every video; with captions off `cc.py captions` writes nothing, `capcut-finish` adds no caption track, font or entrance (`finish.json` carries `captions.enabled: false`), the lexicon work is skipped,
  and a spoken slur, which nothing masks (no audio is edited), is cut around by the plan. Skills, references and the wrap-up follow the setting.
- **Caption masks** (the user, 2026-11-14: "words such as fuck, faggot, pedo, shit, gay and more always write in captions like f*ck, f*ggot or similarly"): profanity and slurs are ALWAYS typed with one asterisk in place of the first vowel after the first letter, in every video of both modes. `cc.py captions` does it by itself for the user's own list `data/caption-masks.json` (the code holds no word) and for the EDL's `captions.mask_terms`; its answer and `captions.json` carry a `masked` tally (as typed, with counts) for the report and the wrap-up. Only the typed caption changes: the audio is never edited. `tests/test_masks.py`; the rule: `reference/safety.md` §3.
- **The caption look** (the user, 2026-11-13, after comparing a frame of ours with one of Loupe video 04 in run `20261106-063422-static-klein`: "the highlight is way too off and big in comparison with the fonts, and always use the same font family as they used in that video"): COPIED from that video, not approximated.
  **Luckiest Guy, always** (`LuckiestGuy-Regular.ttf` in the Loupe fonts folder), upper case, white words with a thick black outline (0.18) and a shadow, the spoken word on a rounded colour box that moves word to word (radius 0.3, padding 0.08, 0.15 lower, words 0.55 em apart; `captions.style: "word-box"`, `scripts/cc_wordbox.py`).
  The box numbers were tuned with the user for that font (CapCut boxes the whole line, ascent plus descent, so the font's metrics decide how big the box looks and where it sits): another font made the box more than twice the height of its word and off it. So the font is never picked per video; the only exception is a character it cannot draw
  (no Slavic or Turkish letters, no Cyrillic or Greek), which `cc.py captions` lists as `font_missing_glyphs` (it also says `house_font`) and `capcut-build` lists as a problem. CapCut draws a box behind a whole text only, so it is one CapCut text per word and state, about 2.5 texts per spoken word.
  The box colour is the one free choice: matched to each video's appearance by the production agent (`captions.highlight_color`, the reason in `captions.why`), or the user's own pick for the run (`captions_color` in `state.json`, given as an argument).
  **Size: small to normal, for phones and tablets** (`size: "auto"`: the font's em at `size_em_pct` 4.6 percent of the picture's smaller side: CapCut size 4.5 on 1080p and 8.0 on 1080x1920 in this font; the Loupe videos use 5.5 and 10, about 20 percent larger; the guide is 4.0 to 5.0 percent, `cc.py captions` reports `vs_guide`).
  The plain look (one text per caption, key words in a colour, the same font, outline and shadow) is the fallback: by itself for a language written without spaces or right to left and for a video with more than `captions.word_box_max_words` (3000, about 23 minutes of continuous speech) spoken words, with the reason in `resolved.json -> captions.style_reason`; `style: "plain"` asks for it.
  `data/font-cache.json` (git-ignored) keeps the answer of a font-family lookup, which only an EDL that names a family needs.
- **One composition for everything** (the user, 2026-11-13: "use capcut composition for everything if possible for faster delivery"): `capcut-build` puts the clips, the sound-effect lanes, the transitions and the word-box caption texts into ONE `capcut compile` (the same capcut-cli functions the single commands call, so the project is the same: checked text by text against the older compose-then-finish route on the BLAST test video, 1,909 texts, 0 differences),
  finishes what compile cannot carry and reads the project back. The BLAST test video (4.5 minutes, 1,909 texts): 8 s for the whole build against 25 s for the separate steps, and the agent runs one command instead of five. Production agents build side by side, so `capcut compile`, which adds the project to CapCut's shared index, holds the machine-wide store lock (the Loupe repair's lock file); the clips' probes run side by side; a captions.json older than the last edl-check is refused.
- **One research agent** (the user, 2026-11-13: "one agent suffices to collect everything briefly, not a deep research"): `cc-start` starts ONE web-only research agent in the background (`config.json -> agents.research_max` 1, `agents.research_calls` 15 tool calls, `reference/research-agent.md`) that writes `20-analysis/research.md` while the recon, the HUD map and the screen scan run; never a wave of agents.
  The first game run's four agents took 14 minutes and about 930k tokens (435 tool calls) for four 9 to 11 KB notes that chased single claims.
- **Speed without losing anything** (the user, 2026-11-13): whatever does not depend on another step starts together, in ONE message: the research agent, the missing reports and `sfx-scan` in `cc-start`; the screen scan and the replay and kill-feed series in `cc-profile-game` the moment `regions.json` exists; every mining and production wave; the independent tool calls inside an agent.
  The CapCut project is ONE composition and one command (`capcut-build`). No check is dropped to save time (frames at the cuts, `units-check`, `edl-check`, the read-back).
- No console windows: every program a script starts (ffmpeg, ffprobe, PowerShell, taskkill, claude) is started with `creationflags=NO_WINDOW` (`cc_common.run_cmd` does it). The watcher runs under `pythonw.exe` without a console, and a console program started without the flag gets a NEW one that Windows Terminal shows as a window per call (one popup per ffmpeg call, seen 2026-11-13). `tests/test_nowindow.py` fails when a script forgets it.
- Never move, rename, delete or overwrite a chunk's `chunk.mp4` after `ingest`; the editing side only reads it. Frames are the only media a script deletes (after their sheet is built), plus the 16 kHz wav after transcription.
- Whisper stays on the CPU by default (the GPU is reserved for FLUX Klein and ACE-Step with their memory guard); the GPU is an opt-in (`whisper.device`), measured at ~10x faster.
- Two processors (`config.json -> watch.workers`, `watch --workers N`): `cc.py watch` works on two chunks at the same time, one processor on the NEWEST ready chunk (live), the other on the OLDEST (backlog), sharing one Whisper model. Every ready chunk's real duration is probed and entered in the chunk table first, so rec starts, sheets and text views are right whatever the processing order and nothing is made twice (`docs/processing.md`, `tests/test_workers.py`).
- Free space is checked per drive: `doctor` and `watch` report it and refuse to start a chunk below `min_free_gb` (3 GB) on the runs drive (C: has about 8 GB until the new SSD is in).
- **Context in cut parts, streamer long videos** (the user, 2026-11-14): the dull parts of a long video are left out; where something that is kept leans on a bit of one, the agents may keep that bit, judged from what the stream shows, with no limits or quotas (`reference/context-keeping.md`).
- **Long videos are whole watches, streamer mode only** (the user, 2026-11-14): each long video runs about 25 minutes to an hour, set by the content and its context and not by the clock (a 7-hour stream might give 36, 43 and 27 minutes, not an hour and a leftover of 46 minutes that begins in the middle of a story), and whatever a viewer starts in it ends in it.
  The mining agents record the stream's acts (`acts` in their block file), the planner sets the borders between the videos between acts and checks each border by reading the words (`reference/portfolio.md` section 2, `reference/moment-mining.md`), and each builder checks how its video opens and ends and reports a border that was not clean (`skills/cc-build-long`). How much of the stream becomes videos is the agents' judgement and never a target (the user, 2026-11-14): three hours from an eight-hour stream if the analysis says so, or 32 minutes, or none; nothing is included just to reach a number of minutes. Game mode has its own counterpart, next.
- **Game mode: one video and one CapCut project per game, different matches never mixed** (the user, 2026-11-14: "if the stream has 2, 3 different matches or more being played throughout the whole stream, do the video for each of the game in a separate capcut project"): the profile phase finds every match in the recording (the teams on the scoreboard changing, read in a frame after each score reset), the match map has a level for matches, the mining agents record a change of match as `non_play` kind `match-change`,
  and the planner makes the games of each match videos of their own, each its own CapCut project: never two matches in one video, never a game split between two videos; a match the recording holds only in part is a video of what is there when that is worth watching, and its brief and the README say where it begins or ends (`reference/game-clipping.md` sections 2 and 8, `skills/cc-plan-game`). The lengths stay what the kept rounds or fights add up to.
- **Shorts level, streamer mode** (the user, 2026-11-14): when the run makes shorts, `cc-start` asks a follow-up question, **Concentrated** (only the one, two or three best shorts: the most highlighted, highest-potential pieces of the content) or **Normal** (about 5 to 10 shorts), stored as `state.json -> shorts_level` (`shorts=concentrated|normal` skips the question; a run made before it has none and the planner judges the count as before).
  The level is a range the user chose, never a quota: the planner makes fewer shorts when fewer are worth making, and none when none is (`reference/portfolio.md` section 3, `skills/cc-plan`).
- **Shorts are always 9:16** (the user, 2026-11-14): a short's canvas is 1080x1920 whatever the source. `edl-check` warns when a short's EDL names another canvas (the check is then not ok) and `capcut-build` lists it as a problem (`tests/test_edit.py`); a whole 16:9 frame goes in the middle of the 9:16 canvas on a blurred copy (`fit-blur`). Long videos stay 16:9.
- **Spoken language** (the user, 2026-11-14: "not always all of the streams we will process will be in english, some will be in german or spanish too"): `whisper.language` is `auto` (it was forced to `en`, so every chunk was decoded as English). Whisper, the multilingual `medium` model, names the language per chunk; an unsure guess falls back to English; the first sure detection on a stream chunk is locked as the run's language (`state.json -> settings.whisper.language_locked`; an ad chunk never sets or uses it; a language the user set for the run is never replaced).
  The task stays transcribe, never translate. The agents read the stream in its language and write their notes in English, add that language's profanity to `captions.mask_terms`, and write the posting text in the stream's language (`reference/language.md`, `tests/test_language.py`).
- No emoji in any file this toolkit or a command writes. Religion and superstition are avoided in what a video says or shows; gore, distress and nudity are kept but blurred, only where seen; nothing else is ever blurred (the user, 2026-11-14: no blur for personal data, DMs, usernames, IDs or face cams).
