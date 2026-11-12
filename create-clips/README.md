# create-clips: the clip-farming toolkit for livestreams

Twitch livestream -> **Twitch Chunk Recorder** (Chrome extension, `C:\Users\Bulzart\Documents\twitch-chunk-recorder`) saves 3-minute MP4 chunks ->
**`cc.py watch`** (this toolkit) turns each chunk into frame sheets, a Whisper transcript and per-second numbers inside a run folder ->
**`/create-clips <run folder>`** (Claude Code command) researches the streamer, mines the stream's moments and builds CapCut projects (shorts and long-form).

This file is the **contract** between the three parts. Everything that crosses a part (file names, JSON fields, times) is defined here.

## Quick start
1. **Once**: `chrome://extensions` -> Developer mode -> Load unpacked -> `C:\Users\Bulzart\Documents\twitch-chunk-recorder`. Check `T doctor` (ffmpeg, Whisper medium cached, free space).
2. **Start the processor** in a PowerShell window and leave it running: `& "C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Bulzart\.claude\create-clips\scripts\cc.py" watch`
3. **Record**: open the extension on a Twitch channel (or type the login), pick the quality, press Record (or put the channels on the auto-record list). Chunks land in `Downloads\twitch-chunks\...` and the processor turns each one into sheets and a transcript inside `C:\Users\Bulzart\Documents\stream-clips\runs\<session>`.
4. **Clip**: in Claude Code, `/create-clips <that run folder>` (optionally `notes="guest was X, topic Y"`). Read `RUN\deliverables\README.md` at the end; open the CapCut projects, check the first frame, export.
C: has only about 8 GB free (2026-11-12): 720p60 is about 1.5 GB per hour of stream, 1080p60 about 3.6 GB per hour; free space before a long stream.

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
this chunk's start (by program date time; ad seconds and reconnects). `stream` is a GQL snapshot taken at the chunk's start, `null` fields when unknown.

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
      sheets\sheet-01.jpg ...   the contact sheets (frames every 0.75 s, 30 per sheet = 22.5 s) and overview.jpg
      frames.json               one row per frame: t (chunk s), rec (rec s), sheet, cell, rms_db, chat_per_s, diff_prev
      audio.json                loudness per 0.5 s; audio-profile.json: its summary
      transcript.json           Whisper medium words; transcript.txt: the same as readable lines
      timeline.md               per-second table (speech, loudness, motion, chat)
      digest.json               the chunk's row of stream.md as data
  20-analysis\                  /create-clips: streamer profile, audience, stream brief, moments, richness, portfolio
  30-assets\                    /create-clips and cc.py: extra frames, dense sheets, censor clips, caption files, sfx.json
  40-briefs\                    /create-clips: one brief per planned video
  60-outputs\<video>\           /create-clips: EDL, captions, build plan, CapCut project name, report
  deliverables\                 README with the CapCut projects made
  logs\                         cc.py logs (watch.log, ingest-<chunk>.log)
```

### Times (read this once)

- **rec time** = seconds since the start of C0001, counting recorded content only (a gap between chunks does NOT add time). Every time an agent
  reads or writes (sheets, transcripts, EDL, moments) is rec time. Display `H:MM:SS.cc` (`0:33:45.75`) or plain seconds (`2025.75`).
- **chunk offset** = seconds since the start of that chunk's mp4 (`+45.75`).
- `rec = chunk.rec_start_s + offset`. `rec_start_s` of a chunk = sum of the real durations (ffprobe) of the chunks before it.
- Chunks are about 180 s but not exactly (they end on a 2 s segment boundary); always map through the chunk table (`cc.py locate`), never `index * 180`.
- `t0_utc` (wall clock) is context only (when it happened, gaps between chunks).

`00-inventory/chunks.json`: list of `{id:"C0001", index:1, file:"10-media/C0001/chunk.mp4", rec_start_s, duration_s, t0_utc, t1_utc, gap_before_s,
ads_skipped_s, ended_by, quality:{...}, stream:{...}, status:"pending|processing|done|failed", stages:{move,probe,audio,sheets,transcript,digest: true|false|"failed: why"},
sheets:N, frames:N, words:N, speech_seconds, language, model, device, seconds:{audio,sheets,transcript}, error, processed_at}`.

`state.json`: `{schema:"cc/1", channel, session, run, created, inbox, settings:{frame_interval_s,frames_per_sheet,...}, chunks:{"C0001":{status,...}},
stage (the /create-clips stage), next_skill, videos:{}}`.

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
Editing and run state (`scripts/cc_edit.py`): `state` (get/set dotted keys), `blocks` (chunk blocks for scan agents), `words` (spoken words with start times), `sfx-scan`, `layout-calc`, `grid-frame`
(a full-resolution frame with a 10% grid), `censor` (a blurred copy of only a span and optionally only a region), `edl-check` (resolve an EDL: pieces, the CapCut MCP plan, the finish plan, facts at every cut),
`captions` (cues from the transcript words of the resolved pieces: masking, spelling replacements), `capcut-name`, `capcut-finish` (zoom keyframes, transitions, captions, font, entrance, repair).
`--run` takes a run folder path or a bare session name under `runs_root`.

The command, its phase skills (`~/.claude/skills/cc-*`) and the references (`reference/*.md`) are described in `~/.claude/commands/create-clips.md`; `tests/test_edit.py` is the edit toolkit's regression test.

## 4. Rules that hold everywhere

- Scripts gather, agents decide: no verdict, label, rank or gate comes from a script (numbers, facts, peaks lists are fine).
- Never move, rename, delete or overwrite a chunk's `chunk.mp4` after `ingest`; the editing side only reads it. Frames are the only media a script deletes (after their sheet is built), plus the 16 kHz wav after transcription.
- Whisper stays on the CPU by default (the GPU is reserved for FLUX Klein and ACE-Step with their memory guard); the GPU is an opt-in (`whisper.device`), measured at ~10x faster.
- C: is nearly full (8 GB free at 2026-11-12): `doctor` and `watch` report free space and refuse to start a chunk below `min_free_gb`.
- No emoji in any file this toolkit or a command writes. Religion and superstition are avoided in what a video says or shows; gore, distress, nudity and personal data are kept but blurred, only where seen.
