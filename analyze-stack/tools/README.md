# `tools\` — Stage-1 measurement scripts and media helpers for `/analyze-stack`

Python 3.12 scripts, argparse, absolute paths, JSON outputs, non-interactive. Stage 1 turns
`<run>\00-input\source.mp4` into measured evidence (`<run>\10-measure\`); the helpers slice the source
for the Seedance 2.5 edit approach, read/write `state.json`, and handle generated clips afterwards
(download, frames for QA, join). Post-generation editing lives in `tools\edit\` (own README).
The lines below are the authoritative invocations that `SKILL.md` quotes; every line was run on
2026-09-17 against `samples\sample-27s-roofingpov.mp4` (run `runs\20260917-020912-b1f`).

## 0. Conventions (read once)

| Item | Value |
|---|---|
| Python | `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe` (`python` resolves to it in PowerShell after the PATH refresh; in Git Bash the bare `python` is a Store stub, so always use the absolute path) |
| PATH refresh | start every PowerShell 5.1 command with `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`; chain with `;` (no `&&` / `\|\|`) |
| Tool fallback | scripts resolve `ffmpeg` / `ffprobe` from PATH, then the registry PATH, then the absolute paths in `LAYOUT.md` (`common.find_tool`), so a stale PATH never breaks them |
| Run folder | `C:\Users\Bulzart\.claude\analyze-stack\runs\<YYYYMMDD-HHMMSS-slug>\` created by `intake.py` with the full skeleton (`common.RUN_SKELETON`); `TOOLS` below = `C:\Users\Bulzart\.claude\analyze-stack\tools` |
| Common flags | Stage-1 scripts take `--run-dir "<run>"` and `--quiet` (progress lines off; the log file is always written) |
| Logs | Stage-1 scripts append to `<run>\10-measure\measure.log`; `intake.py`, `segment_source.py`, `join_clips.py --run-dir` write `<run>\logs\<script>.log`; helpers without a run write `<out dir>\<script>.log` |
| Exit codes | `0` ok · `1` failure (traceback in the log) · `2` bad arguments / bad plan (`slicer.py`, `segment_source.py`, `download.py`, `state.py`, `join_clips.py`, `measure_all.py` = intake failed) |
| Timestamps | file names use `00m12.40s` (no colons); JSON uses decimal seconds; burned-in labels use `mm:ss.ff` |
| state.json | every Stage-1 script indexes its own outputs under `files["10-measure"]`; `measure_all.py` sets `stage=measured`, `next_step=analysis`, `measure.timings`; `state.py` is the CLI for everything else |
| PowerShell quoting | a JSON value for `state.py set` needs escaped quotes, otherwise PowerShell 5.1 strips them before the exe sees them: `'flags={\"a\":true}'` works, `'flags={"a":true}'` arrives as `{a:true}` (verified) |
| Never | no installs at run time (pip/npm/winget); `transcript.srt` is a sidecar for the owner's external caption tool and for analysis only — it is never rendered into an edit |

Test machine: i7-1355U (10 cores / 12 threads), 16 GB, Windows 11. Wall-clock figures below are from two
runs of the same 27.27 s, 720x1280, 30 fps, 13-shot sample (no speech); the laptop varies by up to 2x
between runs, so treat them as orders of magnitude. Scale roughly with duration x resolution.

## 1. Stage 1 in one command

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\measure_all.py "C:\path\to\video.mp4" --slug <slug>
```

That one line runs `intake.py` (new run folder + normalised `source.mp4`) and then, as separate
processes, `probe.py → cuts.py → keyframes.py → audio.py → transcribe.py (+ audio.py --refine-only) →
ocr.py → visual_stats.py`, writes `10-measure\measure-summary.md`, updates `state.json`
(`stage=measured`, `next_step=analysis`, `measure.timings`) and prints the run dir as the LAST stdout
line. A link (`https://…`) in place of the path is downloaded with yt-dlp.

The two-step form the skill uses (intake first so the run dir is known before measuring):

```powershell
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\intake.py "C:\path\to\video.mp4" --slug <slug>
#  -> last stdout line = <run>
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\measure_all.py --run-dir "<run>"
```

Assert after it: `10-measure\probe.json, cuts.json, shots.json, keyframes.json, keyframes\shots\ (3 per shot),
keyframes\sampled\, contact-sheets\sheet-NN.jpg + index.json, audio.wav, audio-16k.wav, transcript.json/.srt/.txt,
ocr.json, audio-features.json, visual-stats.json, measure-summary.md, measure.log` and `state.json.stage == "measured"`.
Re-running is idempotent: finished steps are skipped (`--redo` repeats them, `--skip a,b` omits them).
Measured totals: 217 s (fresh run, OCR overlapped by other work) and 150 s (earlier clean run); OCR is
the long pole (see §2.8).

Step-by-step timings of the fresh run (`state.json → measure.timings`):
`intake 0.6 s · probe 0.25 s · cuts 17.4 s · keyframes 7.9 s · audio 12.3 s · transcribe 12.2 s · ocr 128 s · visual_stats 38 s`
(earlier clean run: `0.2 · 0.1 · 9.5 · 6.5 · 3.6 · 6.8 · 97 · 26`).

## 2. Scripts

### 2.0 `common.py` (library, no CLI)
Shared by every script: tool resolution with the `LAYOUT.md` fallbacks, `run_cmd` (no shell, UTF-8,
timeout, command + result logged), JSON/text writers (atomic `.tmp` rename), run-folder skeleton and
`new_run_dir`, `state_get / state_set / state_add_files`, timestamp helpers (`ts_name` → `00m12.40s`,
`fmt_hms`, `fmt_mmss`, `fmt_srt`), `ffprobe_json / video_stream / audio_streams / media_duration /
stream_fps`, the contact-sheet builder (PIL, Windows fonts, 270x480 portrait / 480x270 landscape cells,
timestamp + shot id burned into each cell) and the `Log` class. Sets `sys.dont_write_bytecode` so
`tools\` stays free of `__pycache__`.

### 2.1 `intake.py` — Stage 0: run folder + normalised source
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\intake.py "<path-or-url>" [--slug <slug>] [--run-root <runs dir>] [--run-dir <existing run>] [--cookies-from-browser chrome] [--quiet]
```
Arguments: positional local video path or `http(s)` link; `--slug` run-id suffix (default: file stem
or link host); `--run-root` (default `…\analyze-stack\runs`); `--run-dir` reuse an existing folder instead
of creating one; `--cookies-from-browser` passed to yt-dlp for logged-in pages.
Outputs: `<run>\` skeleton; `00-input\source.mp4` — plain copy when the file is already
h264/yuv420p mp4 with aac/mp3/no audio, stream copy when only the container differs, otherwise a
libx264 crf 18 + aac 192k transcode (the original bytes stay next to it as `source-original.mp4` /
`source.<ext>`); links → `00-input\link.txt`, `download.<ext>`, `download.info.json` (title, uploader,
upload date, view/like counts copied into `input.json`); `00-input\input.json` (origin, sha1, conversion,
`quick_probe`); `state.json` (`stage=intake`, `next_step=measure`, `input`); `logs\intake.log`.
Prints the run dir as the last stdout line (also on failure, with `stage=intake-failed`).
Time: 0.6 s for a 7 MB mp4 copy (sha1 + 2 ffprobes); a transcode costs roughly real time x 0.5–1 on
this CPU; a download depends on the site.

### 2.2 `probe.py` — specs
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\probe.py --run-dir "<run>" [--source <file>] [--quiet]
```
Output `10-measure\probe.json`: `duration_s`, `duration_hms`, `width/height`, `rotation`,
`display_width/height` (rotation-corrected), `orientation`, `aspect_ratio` (reduced, e.g. `9:16`),
`aspect_nearest` (closest common ratio within 3 %), `aspect_decimal`, `fps {r_frame_rate, avg_frame_rate,
value}`, `nb_frames` (+ `nb_frames_source` stream|estimated), `video {codec, profile, level, bitrate,
pix_fmt, color_*, sar, dar, start_time}`, `audio[{codec, sample_rate, channels, layout, bitrate}]`,
`has_audio`, `container {format, bitrate, size_bytes, tags}`, `raw` (full ffprobe JSON). Time: 0.1–0.3 s.

### 2.3 `cuts.py` — shot cuts, shots, pacing
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\cuts.py --run-dir "<run>" [--content-threshold 27] [--adaptive-threshold 3] [--min-scene-len 6] [--hard 0.30] [--broad 0.08] [--scdet 10] [--merge-window 0.15] [--no-verify] [--quiet]
```
Five detectors run in parallel threads: PySceneDetect `ContentDetector(27)` and
`AdaptiveDetector(3)`, ffmpeg `select=gt(scene,0.08)` (hits ≥ 0.30 count as strong), ffmpeg
`scdet=threshold=10`, plus `freezedetect` / `blackdetect`. Hits are clustered within
`--merge-window` s; `confidence` = number of strong detectors agreeing (0–4); each cluster is verified
with an OpenCV frame pair (mean abs diff ≥ 18 or HSV-histogram correlation < 0.55 confirms).
`type=hard` when confidence ≥ 2, or 1 + frame-pair confirmation; else `candidate`.
Outputs: `10-measure\cuts.json` (`cuts[{t, hms, score, sources[], confidence, type, why, frame_pair}]`,
`detectors{…n, elapsed_s}`, `raw_hits`, `rule`) and `shots.json` (`shots[{id, start, end, duration,
start_hms, end_hms, cut_in}]`, `pacing{mean/median/min/max_shot_s, cuts_per_10s_avg, cuts_per_10s_windows,
fastest_window, slowest_window, shots_under_1s, shots_over_5s}`, `freeze_spans`, `black_spans`).
Sample result: 12 hard cuts → 13 shots, median 1.33 s. Time: 9.5–17.4 s for 27 s of 720p.

### 2.4 `keyframes.py` — shot frames, sampled frames, contact sheets
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\keyframes.py --run-dir "<run>" [--fps N] [--max-frames 600] [--sample-max-side 1280] [--jobs 4] [--quiet]
```
Needs `shots.json` (without it the whole video is one shot, with a warning). Sampling rate: 2 fps,
3 fps when the median shot is under 1.5 s, 1 fps for videos over 5 min, capped at `--max-frames`
(fps lowered to fit; the reason is recorded); `--fps` forces it.
Outputs: `keyframes\shots\shot-NN-first|mid|last-<00m00.00s>.jpg` (full resolution, q=2, three per
shot, `--jobs` parallel ffmpeg seeks), `keyframes\sampled\t-<00m00.33s>.jpg` (long side ≤
`--sample-max-side`, timestamps are the exact `showinfo` pts), `contact-sheets\sheet-NN.jpg` (4x4 tiles,
270x480 cells for portrait / 480x270 for landscape, aspect kept with padding, timestamp + shot id
burned into every cell, cells read left-to-right then top-to-bottom), `contact-sheets\index.json`
(sheet → cells → `{t, shot, frame}`), `keyframes.json` (everything above + `sample_fps_reason`).
Verified by eye on the sample: sheet-01 cells run 00:00.00 / 00:00.33 / 00:00.67 / 00:01.00 … with
`shot 01`, `shot 02` … labels, and cell 1 matches `index.json`. Sample: 39 shot frames, 82 sampled at
3 fps, 6 sheets. Time: 6.5–7.9 s.

### 2.5 `audio.py` — audio extraction + features
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\audio.py --run-dir "<run>" [--silence-db -35] [--silence-min 0.6] [--no-librosa] [--refine-only] [--quiet]
```
Outputs: `audio.wav` (44.1 kHz stereo PCM, analysis/editing reference), `audio-16k.wav` (16 kHz mono,
the ASR input), `_work\audio-22k.wav` (feature input), `audio-features.json`: `tempo_bpm`,
`beat_times[]`, `onset_times[]` (librosa 1.0; `--no-librosa` = numpy fallback), `rms_per_0.25s[{t, rms,
db}]`, `rms_peak_db`, `spectral_centroid_mean_hz` + per second, `silence_spans` = `dead_air_spans`
(ffmpeg silencedetect, `--silence-db` / `--silence-min`), `dead_air_total_s`, `loudness {integrated_lufs,
lra_lu, true_peak_dbtp, momentary_per_s}` (ffmpeg ebur128; delivery QA target -14 LUFS / -1.5 dBTP),
`segmentation[{start, end, label speech|music-or-ambience|silence, confidence}]`, `cuts_vs_beats`
(hard cuts within 80 ms of a beat, when `shots.json` exists). No audio stream → `{has_audio:false}`,
exit 0. `--refine-only` re-labels the segmentation with `transcript.json` (speech = transcript
segments, authoritative); `measure_all.py` runs it automatically after transcription.
Time: 3–12 s (librosa's first call after a cold numba cache is the slow case; ~40 s worst).

### 2.6 `transcribe.py` — speech with word timestamps
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\transcribe.py --run-dir "<run>" [--model small] [--language auto] [--engine faster-whisper|ffmpeg] [--beam-size 5] [--no-vad] [--audio <wav>] [--quiet]
```
Engines: `faster-whisper` (default; CPU int8, VAD filter, word timestamps + probabilities; models
`small`, `small.en`, `base` are cached in `C:\Users\Bulzart\.cache\huggingface\hub`) or `ffmpeg`
(built-in whisper.cpp filter with `C:\Users\Bulzart\.cache\whisper-cpp\ggml-tiny.en.bin` /
`ggml-base.en.bin`; segment timestamps only — the Python-free fallback).
Outputs: `transcript.json` (`engine, model, language, language_probability, has_speech,
language_uncertain, segments[{id, start, end, text, words[{word, start, end, probability}], avg_logprob,
no_speech_prob}], n_segments, n_words, speech_s, wpm_speech_only, wpm_whole_video`), `transcript.srt`
(SIDECAR only — never rendered), `transcript.txt` (one segment per line; `No speech detected.` when
empty). `has_speech=false` when there are no words or the language probability is < 0.5 with fewer
than 5 words. ASR failure → `transcript.error.txt`, exit 1.
Time: 6.5–12 s for 27 s with no speech (2 s model load); speech runs at roughly 0.3–0.5x real time
with `small` on this CPU.

### 2.7 `ocr.py` — on-screen text
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\ocr.py --run-dir "<run>" [--min-score 0.5] [--similarity 0.8] [--workers 3] [--threads 4] [--quiet]
```
RapidOCR (onnxruntime, CPU; detector limit 960 px on the long side) over every sampled frame plus
the shot first/last frames that do not coincide with a sampled timestamp, in `--workers` processes x
`--threads` intra-op threads. Outputs `ocr.json`: `detections[{t, text, box, score, frame, shot, position,
size_class}]`, `spans[{id, text, start, end, duration, n_frames, position top|middle|bottom-left|centre|right,
size_class small|medium|large, score_max, box_mean, shots[], persists_across_cuts, likely_noise, kind_hint}]`
(near-identical text at a similar position merged over consecutive frames), `frames_text[]`,
`brand_candidates[]` (all-caps tokens, ®/™ marks, brand keywords), `handles[]`, `hashtags[]`, `urls[]`.
OCR text is evidence to verify on the frame, never verbatim truth (`likely_noise` spans are 1–2
characters or weak one-frame hits). Sample: 97 frames → 46 detections, 26 spans (12 noise), 7 brand
candidates, e.g. "POV: This combo had potential" 0.00–2.83 s.
Time: this is the long pole — 92–128 s for 97 frames (≈ 1 s per 720x1280 frame); worker/thread
combinations 3x4, 2x3, 4x2 and 6x1 were all within the run-to-run noise on this 12-thread CPU
(see §4), so the default stays 3x4. A 4-minute video at 2 fps is ~480 frames ≈ 8–10 min.

### 2.8 `visual_stats.py` — colour/light/texture per frame, camera motion per shot, style cues
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\visual_stats.py --run-dir "<run>" [--motion-rate 8] [--motion-width 320] [--no-motion] [--quiet]
```
Needs `keyframes.json` (+ `shots.json`, `probe.json`). Per sampled frame: k-means palette (k=5),
brightness, contrast, saturation, Canny edge density, colourfulness, flat/soft/hard gradient ratios,
noise, colour entropy. Per shot: the same aggregated + `camera_motion` from Farneback optical flow at
`--motion-rate` pairs/s on `--motion-width` px frames (RANSAC similarity fit → translation / scale /
rotation / residual, phase correlation cross-check) labelled `static | pan-left/right | tilt-up/down |
zoom-in/out | handheld-shaky | subject-motion` (labels = camera direction; thresholds heuristic, the
numbers are the reliable part). Global: palette k=5/k=8, edge-density distribution, flat-colour ratio,
noise, `style_hints {real_footage, animation_2d_flat, sketch_or_line_art}` (hints for the visual
analyst, not a verdict), `camera_motion_summary`. Output `visual-stats.json` (`frames[]`, `shots[]`,
`global`, `motion_pairs[]`, `method`). Time: 26–38 s for 27 s at 30 fps (the flow pass reads the whole
video once; `--no-motion` drops it to ~3 s).

### 2.9 `measure_all.py` — Stage-1 driver
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\measure_all.py --run-dir "<run>" [--whisper-model small] [--language auto] [--engine faster-whisper|ffmpeg] [--fps N] [--skip probe,cuts,keyframes,audio,transcribe,ocr,visual_stats] [--skip-transcribe] [--redo] [--quiet]
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\measure_all.py "<video-or-url>" [--run-root <runs>] [--slug <slug>] [--cookies-from-browser chrome] [same options]
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\measure_all.py "<existing run dir>" [same options]
```
Runs each script as its own process (a failing script is logged and the rest continue), skips steps
whose marker output exists unless `--redo`, runs `audio.py --refine-only` after a successful
transcription, writes `10-measure\measure-summary.md` (§1 specs, §2 shot table with camera labels,
§3 keyframes, §4 transcript excerpt, §5 OCR spans, §6 audio profile, §7 camera motion, §8 style cues,
§9 files, §10 timings) and `state.json` (`stage=measured`, `next_step=analysis`,
`measure{timings, failed, total_s, summary}`). Exit 0 all ok · 1 at least one step failed (which ones
is in `state.measure.failed` and the summary) · 2 intake failed. Prints the run dir last.
The measurer agent appends `## 11. Analysis segments` + `## 12. Problems` to the summary itself.

### 2.10 `slicer.py` — clip / edit-segment plan (Stage 4 helper)
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\slicer.py --duration <D> --clip-seconds <S> --min-clip <MIN> --max-clip <MAX> [--uneven --shots "<run>\10-measure\shots.json"] [--snap-window 1.5] [--start 0] [--number-from 1] [--out "<run>\40-plan\plan-slices.json"] [--quiet]
```
Pure arithmetic, no ffmpeg. `MIN`/`MAX` are read from `seedance\SEEDANCE-SPEC.md` (generation) or
`SEEDANCE-EDIT.md` (video-input limit) at run time — the 2026-09-16 notes say 4–30 s for both — and
`S` outside `[MIN, MAX]` is refused with exit 2 (re-ask Q3b). Equal lengths by default: `ceil(D/S)`
clips of `S`, the last one shorter only when unavoidable, rebalanced to equal lengths when the
remainder would fall below `MIN`. `--uneven` snaps every internal boundary to the nearest hard cut
(shot start in `shots.json`) within ±`--snap-window` s as long as every clip stays within the limits.
`--start` offsets the clips (Mode 2 segment, Mode 3 budget), `--number-from` continues numbering across
segments. Output JSON (`--out`, and stdout when `--quiet`): `clips[{number, start, end, duration,
gen_duration_s (integer seconds for the generation call), snapped, cut_t}]`, `boundaries`, `warnings`.
Verified on the sample (27.267 s): equal 15 s → `0–15.00, 15.00–27.27` (gen 15 s + 13 s); `--uneven
--snap-window 4` → boundary snapped to the hard cut 18.533; 10 s clips `--uneven` → boundaries snapped to
10.000 and 19.867; 45 s clips → refused (rc 2). Time: 0.2 s.

### 2.11 `segment_source.py` — cut the source into edit segments (Seedance 2.5 edit approach)
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\segment_source.py --run-dir "<run>" --plan "<run>\40-plan\plan-slices.json" [--reencode | --copy] [--source <file>] [--out-dir <dir>] [--crf 18] [--preset medium] [--quiet]
```
The plan is `slicer.py` output or the Stage-4 `plan.json` (`clips | segments | slices | edit_segments`
list; items need `start`/`end`, aliases `source_start`/`src_start`/`in` and nested `slice`/`source`
objects are accepted). Default `--reencode` is frame-accurate (libx264 crf `--crf`, preset `--preset`,
yuv420p, aac 192k, +faststart). `--copy` (previews only) starts each segment at the source keyframe at
or before the planned start and ends it at the planned end; `copy_start` and `starts_early_s` say how
early — phone footage keeps keyframes seconds apart (this sample: 0, 1, 3.4, 7, 15.3, 18.5, 26.9 s), so
a 15 s boundary starts 8 s early in copy mode. Outputs `00-input\segments\seg-NN.mp4` (or `--out-dir`)
+ `segments.json` (per segment: planned vs actual duration, `delta_s`, `within_tolerance`, size, dims,
fps, audio, sha1; segment-local `t` maps to source `t + start`; upload each `seg-NN.mp4` as `@Video1` of
its edit prompt). Segments are indexed in `state.json` only when they live inside the run folder.
Exit 0 ok · 1 a segment failed · 2 bad plan. Verified: 15.000 s and 12.267 s segments with 0.000 s
delta. Time: 31.5 s for 2 re-encoded 720p segments (27 s of source); `--copy` 0.6 s.

### 2.12 `state.py` — read / write `state.json`
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\state.py "<run>" get [key.path]
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\state.py "<run>" set stage=<stage> next_step=<step> [mode=1|2|3] [approach=replicate|edit] [answers.Q1="<answer>"] …
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\state.py "<run>" add-file <stage-dir> <path> [<path> …]
```
`get` prints the whole state (or one key; a plain string is printed bare, anything else as JSON;
missing state → the default skeleton, not an error). `set` parses each value as JSON when possible
(`1` → number, `true` → boolean, `{…}` → object with the quoting rule in §0) else keeps the string;
dotted keys write nested values (`answers.Q1=…`); always stamps `updated` and `run_id`. `add-file`
appends run-relative paths under `files[<stage-dir>]` without duplicates. Exit 0 · 1 run dir missing ·
2 bad usage (`set` without `=`, unknown command). Time: 0.1 s.

## 3. Post-generation helpers (Stage 7g downloads, Stage 9a clip QA, joins)

### 3.1 `download.py` — stream a URL to disk
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\download.py "<url>" --out "<file>" [--probe] [--retries 3] [--timeout 120] [--min-bytes 1024] [--quiet]
```
requests streaming download (connect timeout 15 s, read timeout `--timeout`), exponential-backoff
retries, `.part` file renamed on success, Content-Length check, `text/html` warning (login page /
error page instead of media); `--probe` runs ffprobe and requires a video stream, recording duration,
dims, fps, codec, audio in the log line. Last stdout line: `<path> <bytes> bytes`. Exit 0 · 1 all
attempts failed · 2 the URL does not start with `http://` or `https://`. Used for Higgsfield result
URLs (`80-generated\clip-NN.mp4`) and reference files. Verified: 788,493-byte public mp4 with
`--probe` in 2.0 s; `ftp://` refused with rc 2.

### 3.2 `join_clips.py` — normalise + concatenate clips in order
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\join_clips.py --run-dir "<run>" --out "<run>\80-generated\joined.mp4" [--width 1080] [--height 1920] [--fps 30] [--crf 18] [--preset medium] [--no-audio] [--work <dir>] [--keep-work] [--quiet]
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\join_clips.py --clips "<a.mp4>" "<b.mp4>" … --out "<joined.mp4>" [same options]
```
`--run-dir` takes `80-generated\clip-*.mp4` in name order (or `manifest.json` `clips[].file` order when
present); `--clips` is an explicit order (edit approach: edited segments and pass-through segments
interleaved). Every clip is normalised once — scale to fit + pad to `--width x --height`, `setsar 1`,
`--fps`, yuv420p, libx264 High 4.1 crf `--crf` with a 2 s GOP, audio resampled to 48 kHz stereo AAC
192k (a silent track is synthesised when a clip has none) — then the normalised files are joined with
the concat demuxer in stream-copy mode. Writes `<out>.json` next to the output (per-clip in/out specs,
offsets, expected vs actual duration). The `_join-work` folder is deleted unless `--keep-work`.
Exit 0 · 1 ffmpeg failure · 2 no/missing clips.
Verified on `samples\generated-clips\` (480x854@24 + 3x 720x1280@30, 15 s each) → `h264 High 1080x1920
yuv420p 30/1 fps, aac 48 kHz stereo, 60.05 s` (expected 60.03 s). Time: 118 s for 4x15 s (the 24 fps
clip took 44 s, the 30 fps ones 21–27 s each; `--preset fast` roughly halves it).

### 3.3 `clip_frames.py` — first/last/1 fps frames + one contact sheet of a generated clip
Usage:
```
C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe C:\Users\Bulzart\.claude\analyze-stack\tools\clip_frames.py "<clip.mp4>" --out "<dir>" [--fps 1] [--max-side 1280] [--quiet]
```
Writes `<dir>\first-00m00.00s.jpg` and `last-<t>.jpg` (full resolution, q=2), `f-<00m01.00s>.jpg` at
`--fps` (long side ≤ `--max-side`), `sheet.jpg` (4 columns, as many rows as needed, first and last
frames included, timestamps burned in) and `frames.json` (probe: duration, fps, dims, codec, audio,
size; the frame index and sheet cells). Old JPEGs in `<dir>` are removed first. This is the input the
clip-QA agent looks at next to the clip's prompt. Verified on `clip-01-higgsfield-15s.mp4` (15.04 s,
480x854, 24 fps): first + last + 15 frames + a 4x4 sheet labelled `first 00:00.00 … last 00:15.00`.
Time: 1.6 s per 15 s clip.

## 4. Test log (2026-09-17, run `runs\20260917-020912-b1f`)

| Test | Result |
|---|---|
| `intake.py … --slug b1f` | rc 0, copy, 0.6 s, run dir printed last |
| `measure_all.py --run-dir <run>` | rc 0, 7/7 steps ok, 217 s; all Stage-1 files present; `state.json` stage `measured` |
| contact sheet look (`sheet-01.jpg`) | 4x4 tiles, timestamps rising left→right, top→bottom, shot ids burned in, cell 1 = index.json |
| `slicer.py` equal / `--uneven` / refused / `--start --number-from --quiet` | 15+12.27 s; snap to 18.533 (window 4) and 10.0 + 19.867 (10 s clips); 45 s → rc 2; JSON on stdout |
| `segment_source.py` (re-encode) | 2 segments, 15.000 s / 12.267 s, delta 0.000, 31.5 s |
| `segment_source.py --copy --out-dir <scratch>` | rc 0; seg-02 starts 8.0 s early at keyframe 7.0 (reported), ends on plan; not indexed in state.json |
| `join_clips.py --clips` (4 clips) | 1080x1920 @ 30 fps, 60.05 s, 118 s |
| `download.py … --probe` | 788,493 bytes, probe ok, 2.0 s; bad scheme → rc 2 |
| `clip_frames.py` | 17 JPEGs + sheet + frames.json in 1.6 s |
| `state.py get / set / add-file / bad usage` | typed values, dotted keys, JSON objects (with `\"`), rc 2 on bad input |
| OCR worker/thread settings (same 97 frames) | 3x4: 97 s (clean) / 128 s (overlapped); 2x3: 92 s; 4x2 and 6x1: see §2.7 — noise-level differences, default unchanged |

Defects fixed in this pass (`segment_source.py`): (1) with `--out-dir` outside the run, absolute
paths were written into `state.json` `files["00-input"]` — now only in-run segments are indexed;
(2) `--copy` seeked to the requested start while ffmpeg actually started at the previous keyframe and
`-t` counted from the requested start, so a segment could be 8 s long instead of 12 s and the
4-decimal seek could even miss an exact keyframe (`18.5333 < 18.533333`) — copy mode now seeks onto the
keyframe at or before the start, cuts `end − keyframe`, and reports `copy_start` / `starts_early_s`.
