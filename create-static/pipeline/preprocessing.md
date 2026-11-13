# Chosen processing pipeline (recorded decision)

**Decision (2026-09-30):** all media inspection and processing for /create-static runs **locally and deterministically** through `scripts/cs.py`.

**The rule (the user, 2026-10-12), for every command:** the scripts gather, extract, record, tabulate and calculate; they never evaluate or decide. They measure (durations, cuts, loudness, spectra), extract
(frames, transcripts, OCR text with its numbers), fetch and probe, record the agents' facts and decisions with who and why, and calculate pure formulas. They hand out no verdict, status, flag or label derived
from content, apply no threshold that refuses, caps or changes an answer, rank or pick nothing, compare no texts for sameness and count no words to decide anything; a command refuses only a bad argument, a
missing file or tool, a damaged ledger, an unsafe web address or a failed ffmpeg run, and it keeps the user's own locks (CapCut closed while a project is written). The AI agent that runs the pipeline reads the
numbers and tables, decides from the Static specification (`reference/static/`) and records the decision with the reason. The numbers that used to be enforced are rules of thumb in the reference documents,
applied with judgement.

| stage | tool | why this tool |
|---|---|---|
| Metadata | **ffprobe** (FFmpeg full build, winget Gyan.FFmpeg) | Exact streams, rotation, SAR, fps, audio stream index. Rotation- and SAR-aware display size |
| Structure (cuts, shots, pacing, motion activity) | **FFmpeg** `select` scene score on 192 px frames | Deterministic; one decode pass; no ML dependency |
| Frame sampling | **FFmpeg** `fps=2` flat for a Static run's references (config `static.analysis.fps`, no effort level) plus targeted `-ss` seeks | Exact timestamps |
| Static thinning | **Pillow + NumPy** (48×48 grey mean absolute difference vs. the last kept frame) | Cheap, deterministic, and never drops below 1 fps |
| Storyboards | **Pillow** | Labelled chronological contact sheets of **30 frames**, sized to Claude's vision limits (≤ 1.15 MP, ≤ 1568 px long side) so they are read at full size and no cell is shrunk |
| Audio | **FFmpeg** (16 kHz mono WAV, `ebur128`, `silencedetect`, `astats` RMS per 0.5 s) | Deterministic loudness, silences and energy curve |
| Speech | **faster-whisper** (the config's `whisper_model`), int8 CPU, local cache, word timestamps + VAD. Fallback: **FFmpeg's built-in whisper.cpp filter** | Word-level timing; runs offline (`local_files_only`) |
| On-screen text sample | **RapidOCR** (onnxruntime CPU) on ~12 frames per video | Extracts the on-screen text with the numbers that describe it (first and last time, frames it was seen in, share of the frames scanned, row of the frame, confidence, spelling facts); no label is put on any text: the agent decides what is a caption, a fixed overlay, a handle, a watermark or noise |
| Captions and moves of the references | `T edit-profile` | The references' edit layer as numbers at their full frame rate (static §1) |
| The CapCut project | **capcut-cli** `compile` + the toolkit's one write pass (`T capcut-build`) | One composition per video (item 39, `reference/capcut-build.md`) |

## Video sampling policy (a Static run's references)

| rule | value |
|---|---|
| Baseline | **2 frames per second** across the whole video, flat (the user, 2026-11-07: "just do 2fps when on static mode"). Frame *n* shows the source frame nearest to *n*/2 s |
| Densify on demand | `cs.py frames <video> --range a-b --fps 15 --sheet` around a caption entrance, a cut, a move or a drawn annotation the analysis needs to see closely |
| Thin | Static stretches: ≥ 3 consecutive near-duplicate baseline frames (mean absolute difference < 2.5/255 on 48×48 grey vs. the last kept frame) are dropped, with ≥ 1 frame per second kept. Reported as static runs, shown as grey cells on the storyboard |
| Never | Five repeated analyses of the same frames. The rule is a sampling rate, not repeated passes |

Audio, speech, on-screen text, cuts and motion are aligned on the same clock in `timeline.md` (one row per second), so the storyboard and the timeline are read together as one continuous sequence.

## Outputs per video (`<run>/10-media/<V>/`)

| file | content |
|---|---|
| `video.md` | Human summary: specs, sampling counts, pacing, speech, audio, motion peaks, static runs, sheet list, shot table, transcript, OCR spans |
| `timeline.md` | Per-second table: shot, events (CUT, motion peak, static, silence), words spoken, max loudness, OCR text |
| `sheets/storyboard-NN.jpg` | Chronological storyboard, **30 frames per sheet**. A span that overflows is split into balanced pages of whole rows (31 frames → 18 + 13), never 30 + 1. Every sheet stays under 1.15 MP, the point past which Claude's vision downscales an image, so the cells are read at their real size |
| `frames/base/`, `frames/extra/` | Baseline and densified JPEGs (≤ 720 px long side) |
| `video.json`, `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json`, `ocr.json`, `probe.json` | Machine data |
| `audio/audio-16k.wav` | ASR input |

## Commands

Python: `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` (`config.json → python`).
Script: `C:/Users/Bulzart/.claude/create-static/scripts/cs.py`. Every command prints one JSON object on its last line; `cs.py <command> -h` lists a command's options. The commands a Static run uses:

```
cs.py new-run --source "<refs folder>" [--assets "<path>" …] [--examples "<folder>"]   → run_dir
cs.py state --run "<run>" get [key] | set k=v … | append k=v …
cs.py inventory "<refs folder>" --run "<run>" --as references     → 00-inventory/ (reference material only)
cs.py inventory "<asset paths>" --run "<run>" --as assets          → 30-assets/asset-inventory.{json,md} (paths, kinds, sizes, duplicate_of: facts only; no role is guessed from a file name)
cs.py inventory "<examples folder>" --run "<run>" --as examples    → 00-inventory/examples-inventory.{json,md} (study only; may be empty)
cs.py prep-assets --run "<run>"                                    → previews, docs, font names, assets-sheet-NN.jpg
cs.py prep-all --run "<run>" [--jobs 2] [--only V01,V03] [--redo]  → 10-media/<V>/…, images/, docs/, index.md
cs.py prep-video "<video>" --out "<dir>" --id V01                  (one video)
cs.py frames "<video>" --out "<dir>" --range 3.0-4.2 --fps 15 --sheet [--label x] | --at 1.2,3.4
cs.py doc-text "<file>" --out "<txt>"                              (docx/pptx/xlsx/txt/md/csv/json/srt/vtt/html)
cs.py split-audio "<given video path>" --run "<run>" --audio-only  → <path>/files_audio/
cs.py audio-profile --audio "<file>" --out "<json>"               → the sound design as numbers: speech share, harmonic ratio outside speech, tempo, beat strength, spectral flatness, energy per second; no label
cs.py edit-profile --run "<run>" --ref V01                        → the reference's edit layer as numbers (zoom, pan, pace, caption entrances; gather only)
cs.py effects scan --run "<run>" --folder "<effects folder>"       → 00-inventory/effects.json and .md
cs.py reuse-analysis … | clone-run --from <run>                   (an analysis another run made; static §10)
cs.py static check | formats | format | lock | subjects | language | units | context | profile | forecast
cs.py image … | fetch-image … | fetch-font … | tts … | narration-words … | music … | draw … | slideshow plan …   (static §5, §6, §7)
cs.py capcut-font --list                                           (the fonts the captions can use)
cs.py capcut-build --run "<run>" --video NN [--format <tag>]       → the video's CapCut project (item 39)
cs.py ledger begin|set|show … | contract --run "<run>" | status | doctor | lint-run
```

PDFs: `prep-all`, `prep-assets` and `doc-text` extract the text layer with pypdf (layout mode) into `docs/<D>.txt`, and report `pages`, `chars` and `image_only`. A PDF with no text layer gets its embedded page images
written to `docs/<D>-pages/` (at most 40), to be viewed one by one; the Read tool renders at most 10 pages of a PDF on this machine (no poppler).

## Measured performance (this machine, 2026-09-30, `prep-all --jobs 2`)

| input | wall time | storyboard cells |
|---|---|---|
| 15 s clip, 480×854, no speech | ~54 s | 94 |
| 27 s clip, 720×1280, 11 shots, no speech | ~60–90 s | 202 |
| 40 s talking head, 720×1280, 183 words | ~75–110 s | ~260 |

These were measured at 5 fps; a Static run's 2 fps takes less. The long poles are OCR (~2–5 s per frame) and ASR (~real-time with `small`). For large folders use `--jobs 2`, `--whisper-model base`, or `--no-ocr`
for videos without overlays.

## Known limits
- The cut detector is a heuristic: very fast motion can create false cuts and soft dissolves can be missed. Confirm cuts on the storyboard (red bars).
- OCR misses stylised or animated text and stickers; always read overlays by eye as well.
- ASR can mis-hear names and brand words; verify them against the lips and the context.
