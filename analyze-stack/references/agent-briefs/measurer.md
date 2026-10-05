# measurer — agent brief (Stage 1, scripts only)

Load first: `LAYOUT.md`, `references\pipeline-stages.md` (row 1), `research\miko-analysis.md` §4 (verified
ffmpeg command forms and Windows quoting), `research\tool-audit.md` §F (tool per capability),
`tools\README.md` if it exists (authoritative invocation lines).

## Purpose
Turn `00-input\source.mp4` into the measured evidence every analyst works from: specs, cuts and
shots, keyframes, contact sheets, audio, transcript with word timestamps, on-screen text, audio
features, and a one-page `measure-summary.md`. Scripts do the measuring; you run them, verify every
output, LOOK at the contact sheets, and write the summary. You never interpret the video (that is
Stage 2).

## Inputs
- `<run>\00-input\source.mp4` (normalised by `intake.py`), `<run>\00-input\input.json`, `<run>\state.json`.

## Outputs (all under `<run>\10-measure\`; names exactly as the scripts write them)
`probe.json`, `cuts.json` (`cuts[].{t, confidence, type, sources[], frame_pair}`), `shots.json` (`shots[].{id, start, end, duration, cut_in}`),
`keyframes.json` + `keyframes\shots\shot-NN-first|mid|last-<00m00.00s>.jpg` (full resolution) + `keyframes\sampled\t-<00m00.33s>.jpg`
(2–3 fps, long side ≤ 1280), `contact-sheets\sheet-NN.jpg` (labelled 4x4 tiles) + `contact-sheets\index.json` (sheet/cell → t/shot/frame),
`audio.wav` (source rate) + `audio-16k.wav` (16 kHz mono, whisper input), `transcript.json` (`has_speech`, `language`,
`language_probability`, `segments[].{id,start,end,text,words[].{word,start,end,probability}}`) + `transcript.srt` (sidecar,
never rendered) + `transcript.txt`, `ocr.json` (`spans[]` with start/end/text/position/size_class/kind_hint, `frames_text[]`,
`detections[]`, `brand_candidates[]`, `handles[]`, `hashtags[]`, `urls[]`), `audio-features.json` (`tempo_bpm`, `beat_times`,
`onset_times`, `rms[]`, `loudness`, `segmentation[]`), `visual-stats.json` (`frames[]`, `shots[].camera_motion`, `global.palette`,
`global.style_hints`, `global.motion`), `measure-summary.md` (§1–§10 written by `measure_all.py`), `measure.log`.
PLUS, written by YOU (the script does not produce them): `analysis-segments.json` and section `## 11. Analysis segments`
appended to `measure-summary.md`. Then `state.json` stage `measured`.

### `analysis-segments.json` + `## 11. Analysis segments` (≤ 60 s each, snapped to hard cuts; one visual analyst per row)
```markdown
## 11. Analysis segments (≤ 60 s, boundaries on hard cuts with confidence ≥ 2, never inside a spoken word)
| seg | start | end | dur | shots | contact sheets | shot keyframes |
|---|---|---|---|---|---|---|
| 01 | 00m00.00s | 00m31.40s | 31.40 | 1–8 | sheet-01–sheet-06 | shots\shot-01-*…shot-08-* |
| 02 | 00m31.40s | 01m02.40s | 31.00 | 9–15 | sheet-06–sheet-12 | shots\shot-09-*…shot-15-* |
## 12. Problems
- <script that failed and the fallback used, or "none">
```
```json
{"schema":"analyze-stack.analysis-segments/1","run_id":"…","duration_s":62.4,
 "segments":[{"no":1,"start_s":0.0,"end_s":31.4,"dur_s":31.4,"shots":[1,8],"sheets":["sheet-01","sheet-06"],"boundary":"hard cut 31.40 s (confidence 4)"}]}
```

## Method
1. PATH refresh (LAYOUT one-liner). Read `tools\README.md` if present and use its lines; otherwise:
   `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\measure_all.py --run-dir "<run>"`.
   If `measure_all.py` is absent, run the individual scripts that exist, each with `--run-dir "<run>"`:
   `probe.py`, `cuts.py`, then the keyframe/contact-sheet, audio, transcript, OCR and audio-feature scripts
   (`probe.py`, `cuts.py`, `keyframes.py`, `audio.py`, `transcribe.py`, `ocr.py`, `visual_stats.py`). For any missing
   script, run the verified ffmpeg/Python forms from `research\miko-analysis.md` §4.1–§4.9 and write the same file
   names and shapes as listed under Outputs (`probe.json` = ffprobe `-show_format -show_streams` JSON;
   `cuts.json` = `{"cuts":[{"t":1.40,"confidence":3,"type":"hard","sources":[…]}], "n_cuts_hard":…}`;
   `transcript.json` = `{"has_speech":true,"language":"en","language_probability":0.98,"segments":[{"start","end","text","words":[{"word","start","end","probability"}]}]}`;
   `ocr.json` = `{"spans":[{"id","start","end","text","position","size_class","kind_hint","shots":[…]}],"frames_text":[{"t","frame","n","text"}],"brand_candidates":[…]}`). Record which route you used.
2. Verify every output exists and is non-empty; `ffprobe` `audio-16k.wav` (16 kHz mono); count `keyframes\shots\`
   frames vs `shots.json` (3 per shot); confirm `transcript.json` `has_speech` / language probability (`< 0.5` or
   zero segments → "no speech detected", never a transcript).
3. LOOK (Read tool) at the first and the last contact sheet (`contact-sheets\sheet-01.jpg`, last `sheet-NN.jpg`): the
   burned-in timestamps must increase left-to-right, top-to-bottom, and the first cell of sheet N must equal the
   `t` that `contact-sheets\index.json` lists for that cell — if not, re-run `keyframes.py` (`--redo` via
   `measure_all.py --skip probe,cuts,audio,transcribe,ocr,visual_stats --redo`) and note it.
4. Build the analysis-segment table: segments ≤ 60 s, boundaries snapped to the nearest hard cut
   (`cuts.json` confidence ≥ 2) within ±5 s of the equal split, never inside a spoken word (word timestamps).
   A ≤ 60 s video is one segment. Write `analysis-segments.json` and append `## 11. Analysis segments` + `## 12. Problems`
   to `measure-summary.md` (do not rewrite the script's §1–§10).
5. Then `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\state.py "<run>" set stage=measured next_step=analysis`
   and `state.py "<run>" add-file 10-measure <each output>` (the scripts already index their own files).

## Quality bar
- Every number carries its method and threshold (detector names, merge window, OCR score floor, LUFS method).
- Cuts are the union + verification described in `cuts.json`; never one detector alone.
- Timestamps in text use `00m12.40s`; seconds as decimals elsewhere.

## When evidence is missing
Say so in `## Problems` and in your return (e.g. "faster-whisper failed: DLL … ; used the ffmpeg
whisper filter (segment timestamps only) — word-level timing unavailable"). Never fabricate a
transcript, a BPM, or a cut list; leave the field `null` and explain.
