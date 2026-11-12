# On-screen reading (`cc.py hud-read`, `hud-scan`, `region-series`)

For game matches (CS2, Dota 2, any broadcast with a HUD). The scripts crop a screen region of the recorded chunks and either read its text (OCR) or measure it.
They gather numbers only: what a text or a change means (a round began, a score really moved, a replay wipe) is the agent's call. Code `scripts\cc_hud.py`, test `tests\test_hud.py` (`--long` adds a 3-minute 1080p60 timing).

```
$PY = "C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe"
$CC = "C:\Users\Bulzart\.claude\create-clips\scripts\cc.py"
```
Needs `rapidocr-onnxruntime`, numpy, Pillow and ffmpeg (the tooling of this PC; a missing OCR library stops with the pip line to run). Frames are never kept: ffmpeg crops and scales, the samples go through a pipe.

## Regions
A region is `x,y,w,h` as FRACTIONS of the frame (0..1 from the top-left), e.g. `0.44,0.03,0.12,0.07`: it holds at any resolution. Find it on `cc.py grid-frame --run RUN --at T --region x,y,w,h`
(a 10% grid and the red box), then check it with `hud-read`. Crop tight: only the digits and a little margin. Every broadcast has its own overlay; measure it, do not assume it.

## hud-read: one region at one time (calibrate)
`& $PY $CC hud-read --run RUN --at 0:12:30 --region 0.44,0.03,0.12,0.07 --numeric` (`--at`: rec seconds, `H:MM:SS` or `C0012+45.75`). It gives `text`, `confidence`, `boxes`, `value` and `image`:
the PNG of what the OCR saw (`RUN\30-assets\frames\hud-*.png`, the options are in the name). Look at it, then tune:
- `--kind digits` (default): a line of digits, quick recognition only (about 12 ms); letters that look like digits (O, I, S, B) become digits. `text`: detect + recognise (about 0.5 s) for names, words, kill feed. `auto`: text, digits when it looks numeric.
  `hud-read` also tries detect + recognise when the quick read is empty or unsure and says which worked in `method` (`rec` or `det+rec`); if only `det+rec` works, scan with `--kind text` or `--fallback`.
- `--scale` (default 3) enlarges the crop; `--threshold 0-255` turns pixels at or above it white and the rest black (text over a busy picture); `--invert` flips the crop; `--regex` keeps the first match (no match = empty text);
  `--numeric` adds `value` (`1:55` = 115, `-0:45` = -45, `$4,750` = 4750, `7` = 7). A crop with no contrast (the box is hidden) reads as empty text, never as an invented digit.

## hud-scan: a region over a range, in one pass
One region: `hud-scan --run RUN --region 0.44,0.03,0.12,0.07 --name round_clock --step 1 --numeric --regex "\d:\d{2}"`. Several regions in ONE pass over the video: `--spec FILE`, a JSON list
`[{"name":"clock","region":[0.46,0.02,0.08,0.05],"regex":"\\d:\\d{2}","numeric":true},{"name":"score_a","region":[0.40,0.02,0.05,0.05],"regex":"^\\d{1,2}$"}]`
(each entry may carry kind, scale, threshold, invert, regex, numeric; the command line options are the defaults). Decoding the video is most of the time, so read every region you need in the same pass.
`--from` / `--to` (default the whole recording, `--to` exclusive), `--step` seconds (default 1). The sample grid is `from + k*step` and runs on across chunk boundaries; a hole in the recording is skipped and reported as `holes_s`.
- Output per region, `RUN\20-analysis\hud\NAME.json`: a header (name, region, options, step, from, to), `rows` one per sample `{"rec","chunk","t_chunk","text","conf","reused","value"?,"raw"?}` (`raw` only when cleaning changed it) and a `summary`;
  `NAME.txt`: one line `H:MM:SS.cc  text` per CHANGE of the text. The command prints the first 20 changes of each region. `cc.py hud-states` tabulates score series from these files.
- Idle skip: a sample is read again only when at least `--idle-frac` (default 0.002) of its pixels moved by more than 40 of 255 against the last read one; otherwise the last text is reused (`reused: true`). `--idle-frac 0` reads every sample.
- `--fallback` (off): in digits mode also try detect + recognise when the quick read is empty or unsure. Off because it costs about 0.5 s at EVERY sample while the box is hidden behind moving footage.
- Slips happen (a 1 read as 7, a hidden box): look at `conf`, compare neighbours, and look at the frames where a value jumps by more than expected.

## region-series: numbers of a region over a range (no OCR)
`region-series --run RUN --region 0.3,0.8,0.4,0.1 --region 0.85,0.3,0.1,0.1 --name banners --step 0.5` (repeat `--region`). Each region is reduced to `--size` (default 64x36) per sample. `RUN\20-analysis\hud\NAME-series.json` has
`rows` `{"rec","chunk","t","v":[[r,g,b,luma,diff],...]}` (one entry per region; `diff` = mean absolute change 0..255 against the previous sample, null at the first) and, per region, the percentiles of the diff and the 30 samples with the largest diff
(also listed in `NAME-series.txt`). A banner sliding in, a replay wipe or a flash shows as a peak; the numbers do not say which, the agent looks at the frames at those times.

## Speed (this PC, synthetic video, 2026-11-12)
30 s of clean 1080p HUD: one region at 0.5 s (60 samples) about 2 s including the 0.6 s model load; four regions in one pass 2.5 s; `region-series` 3 regions at 0.25 s 0.4 s.
A 3-minute 1080p60 chunk (a 6 Mbps test pattern, harder to read than a real HUD): `hud-scan` one region at 1 s 12 s, three regions in one pass 16 s, `region-series` two regions at 0.5 s 10 s, the same one-region scan with `--fallback` 96 s.
Decoding (about 9 s per such chunk) is most of it: a 2-hour match of 40 chunks is about 8 minutes for one pass, so read all the regions you need in the same pass (`--spec`).

## Errors
A region outside 0..1, a range outside the recording, a time not inside a chunk, a bad `--spec`, a repeated name, a missing OCR library: each prints `{"ok": false, "error": ...}` with the reason (the missing library exits 3).
Output files are written as `.part` and renamed at the end, so a stopped scan leaves no half file.
