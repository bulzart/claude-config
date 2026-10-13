# Chosen processing pipeline (recorded decision)

**Decision (2026-09-30):** all media inspection and processing for /analyze-then-pick runs **locally
and deterministically** through `scripts/atp.py`.

| stage | tool | why this tool |
|---|---|---|
| Metadata | **ffprobe** (FFmpeg 9.0.2 full build, winget Gyan.FFmpeg) | Exact streams, rotation, SAR, fps, audio stream index. Rotation- and SAR-aware display size, following Higgsfield's own media-pipeline normalisation |
| Structure (cuts, shots, pacing, motion activity) | **FFmpeg** `select` scene score on 192 px frames | Deterministic; one decode pass; no ML dependency |
| Frame sampling | **FFmpeg** `fps=5` (one pass) plus targeted `-ss` seeks | Exact timestamps; ~5 frames per second baseline with adaptive density |
| Static thinning | **Pillow + NumPy** (48×48 grey mean absolute difference vs. the last kept frame) | Cheap, deterministic, and never drops below 1 fps |
| Storyboards | **Pillow** | Labelled chronological contact sheets of **30 frames**, sized to Claude's vision limits (≤ 1.15 MP, ≤ 1568 px long side) so they are read at full size and no cell is shrunk |
| Audio | **FFmpeg** (16 kHz mono WAV, `ebur128`, `silencedetect`, `astats` RMS per 0.5 s) | Deterministic loudness, silences and energy curve |
| Speech | **faster-whisper** `small`, int8 CPU, local cache, word timestamps + VAD. Fallback: **FFmpeg's built-in whisper.cpp filter** (`ggml-base.en.bin`) | Word-level timing is a meaningful advantage over FFmpeg-only ASR (the fallback has segment timing only). Runs offline (`local_files_only`) |
| On-screen text sample | **RapidOCR** (onnxruntime CPU) on ~12 frames per video | Detects captions, handles and watermarks precisely (feeds the text policy); caption-track and persistent-overlay heuristics |
| Output format | **FFmpeg** (lanczos scale-to-cover + crop, or blurred pad on request) | Exact 720×1280 without stretching |
| Overlay text | **CapCut text layers** through the capcut MCP (`reference/capcut-assembly.md`), over the clean generated video | Editable in the video's CapCut project; the generation itself never carries overlay text |
| Deterministic text (fallback) | **FFmpeg + libass** (`subtitles` filter, fonts copied beside the `.ass`) | Only when the CapCut MCP is unavailable |
| Multi-clip joins, hand-off frames | **FFmpeg** (`concat` with `cut` / `continuous` seams; `last-frame` as a lossless PNG) | Continuous seams drop the next clip's repeated first frame; the clips' own fps is kept |
| Edit clean-up | **FFmpeg** `delogo` / `crop` | Small static overlays only; large text goes to the edit model |
| Audio split (intake; Edit Mode and Analyze **Recreate**: audio + silent copy; **Create**: audio only, `--audio-only`) | **FFmpeg** stream copy: audio → `<given path>/files_audio/`, video-only copy → `<given path>/videos_without_audio/` | Only silent videos are uploaded to Higgsfield (fewer flags). The untouched original audio is kept for the final |
| Audio restoration | **FFmpeg** (Higgsfield media-pipeline rules: offset-aware `adelay`/`atrim` + `apad`/`atrim`, `-t` exact; AAC 256 kb/s) | The generated picture gets the original audio from `files_audio`. Verified: 0 ms lag; waveform correlation 0.99+ against the original |
| Transfers | **requests** (Python) PUT/GET | Higgsfield presigned upload and public result download, with retries |

Not used: Higgsfield `sandbox_exec` (remote), Higgsfield `video_analysis_*` (remote, paid; optional only
on request), and cloud ASR.

## Video sampling policy

| rule | value |
|---|---|
| Baseline | **~5 frames per second** across the whole video (`--fps 5`). Frame *n* shows the source frame nearest to *n*/5 s |
| Densify automatically | The last frame before and the first frame after every cut; **10 fps** within ±0.5 s of each motion peak (non-cut visual change; up to 8 peaks, ≥ 1 s apart); **10 fps** over the first second (hook onset) |
| Densify on demand | `atp.py frames <video> --range a-b --fps 15 --sheet` around fast actions, object interactions, hand contact, gestures, product appearances, swaps, text appearances and transitions |
| Thin | Static stretches: ≥ 3 consecutive near-duplicate baseline frames (mean absolute difference < 2.5/255 on 48×48 grey vs. the last kept frame) are dropped, with ≥ 1 frame per second kept. Reported as static runs, shown as grey cells on the storyboard |
| Cap | 1,800 baseline frames per video (6 min at 5 fps). Beyond that the baseline rate is lowered and the note says so; densify the segments of interest |
| Never | Five repeated analyses of the same frames. The rule is a sampling rate, not repeated passes |

Audio, speech, on-screen text, cuts and motion are aligned on the same clock in
`timeline.md` (one row per second), so the storyboard and the timeline are read together as one
continuous sequence.

## Outputs per video (`<run>/10-media/<V>/`)

| file | content |
|---|---|
| `video.md` | Human summary: specs, sampling counts, pacing, speech, audio, loop similarity, motion peaks, static runs, sheet list, shot table, transcript, OCR spans |
| `timeline.md` | Per-second table: shot, events (CUT, motion peak, static, silence), words spoken, max loudness, OCR text |
| `sheets/storyboard-NN.jpg` | Chronological storyboard, **30 frames per sheet** (6 s at 5 fps; about one second of a 30 fps QC checkpoint). A span that overflows is split into balanced pages of whole rows (31 frames → 18 + 13), never 30 + 1. Portrait: 6 columns × 5 rows, 138 × 245 px cells, 1.2 s per row at 5 fps (828 × 1351 px). Landscape: 5 × 6, 240 × 135 cells (1200 × 952). Square: 5 × 6, 184 px cells (920 × 1246). Every sheet stays under 1.15 MP, the point past which Claude's vision downscales an image, so the cells are read at their real size |
| `frames/base/`, `frames/extra/` | Baseline and densified JPEGs (≤ 720 px long side) |
| `video.json`, `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json`, `ocr.json`, `probe.json` | Machine data |
| `audio/audio-16k.wav` | ASR input |

## Commands

Python: `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (`config.json → python`).
Script: `C:/Users/Glaresquare1/.claude/analyze-then-pick/scripts/atp.py`. Every command prints one JSON
object as its last stdout line.

```text
atp.py new-run --mode analyze --source "<refs folder>" --assets "<asset path>" … [--examples "<folder>"]   → run_dir
atp.py new-run --mode edit --source "<video path>" …                   (edit: per-edit assets come later)
atp.py state --run "<run>" get [key] | set k=v … | append k=v …
atp.py inventory "<refs folder>" --run "<run>" --as references         → 00-inventory/ (reference material only)
atp.py inventory "<video paths>" --run "<run>" --as sources            → 00-inventory/ (edit: videos only, other files ignored)
atp.py inventory "<asset paths>" --run "<run>" --as assets [--scope video-01]  → 30-assets/<scope>/asset-inventory.{json,md}
atp.py inventory "<examples folder>" --run "<run>" --as examples     → 00-inventory/examples-inventory.{json,md} (study only; may be empty)
atp.py prep-assets --run "<run>" [--scope video-01]                    → previews, docs, font names, assets-sheet-NN.jpg
atp.py prep-all --run "<run>" [--jobs 2] [--only V01,V03] [--redo]     → 10-media/<V>/…, images/, docs/, index.md
atp.py prep-all --run "<run>" --set examples [--jobs 2]               → 10-media/E01…, examples-index.md
atp.py prep-video "<video>" --out "<dir>" --id V01                     (one video)
atp.py frames "<video>" --out "<dir>" --range 3.0-4.2 --fps 15 --sheet [--label x] | --at 1.2,3.4
atp.py prep-image "<image>" --out "<preview.jpg>"
atp.py doc-text "<file>" --out "<txt>"                                 (docx/pptx/xlsx/txt/md/csv/json/srt/vtt/html)
atp.py hf-put --file "<local>" --url "<upload_url>" --content-type "<exact type>"
atp.py hf-get --url "<result_url>" --out "<file.mp4>"
atp.py split-audio "<given video path>" --run "<run>" [--audio-only]   → <path>/files_audio/ (+ <path>/videos_without_audio/ unless --audio-only)
atp.py audio-profile --audio "<files_audio file>" --out "<json>" [--transcript …] [--cuts …]   → music bed, BPM, energy arc, hits on cuts
atp.py fetch-audio --url "<direct audio url>" --page "<page>" --license "<license>" --out "<file>"   → download + <file>.source.json
atp.py restore-audio --generated "<edit>" --audio "<path>/files_audio/<name>.m4a" --audio-offset <s> [--start <s>] --out "<file>"
atp.py finalize --run "<run>" --video V01 --file "<approved.mp4>" --original "<original video>"   → <path>/final/<name>.mp4
atp.py conform --video "<in>" --out "<out>" [--focus-x 0.5 --focus-y 0.5] [--mode fill|pad]
atp.py trim --video "<in>" --out "<out>" --start 0.4 [--end 7.6]
atp.py concat --clips a.mp4 b.mp4 --out joined.mp4 [--seams cut|continuous,…]
atp.py last-frame --video "<clip>" --out "<handoff.png>" [--back 0.3]    → exact last frame, lossless
atp.py capcut-name --video 3                                              → 01_Oct_2026_v03 (free name)
atp.py capcut-prep --draft "<store>/<name>"                               → right after capcut_clone_draft
atp.py capcut-repair --draft "<store>/<name>" --preview "<preview.mp4>"  → after every capcut_save (house text style + register + sync + lint, locked)
atp.py capcut-text-style --draft "<store>/<name>" [--check | --learn [--text N] [--replace]]   → font System, size 10, the user's locked preset (config capcut.text_style.learned)
atp.py strip-inserts --video "<reference>" --inserts 13.0-15.0 --out "<dir>"  → own.mp4, own-silent.mp4, map.json (split points)
atp.py captions --video "<in>" --out "<out>" --spec captions.json | --from-speech [--script "…"]   (fallback only)
atp.py clean --video "<in>" --out "<out>" --delogo "x,y,w,h@t0-t1" [--crop "x,y,w,h"]
atp.py qc --video "<final>" --out "<dir>" --mode analyze|edit [--allowed-text "a|b"] [--expect-duration s] [--dense "label:a-b" …] [--dense-fps 30]
atp.py scale --product-cm H [--distance d --lens f] [--frame img.png --product-px y0-y1 --ref-cm h --ref-px y0-y1 [--depth-ratio r]] [--out scale.json]   # size reckoning: expected size per shot; observed vs expected on a frame
atp.py model-menu --mode analyze|edit --live-ids "<ids from models_explore>"   (every model, pinned first)
atp.py ledger begin --run "<run>" --video NN --attempt K --request "<request.json>"   (exit 3 = do not submit)
atp.py ledger set --run "<run>" --fingerprint F --job J --status submitted|unknown|completed|failed|accepted|rejected
atp.py open --file "<final.mp4>"                                       (Edit Mode review in the default player)
```

PDFs are read directly with Claude's Read tool (`pages` for long files).

## Measured performance (this machine, 2026-09-30, `prep-all --jobs 2`)

| input | wall time | storyboard cells |
|---|---|---|
| 15 s AI clip, 480×854, no speech | ~54 s | 94 |
| 27 s POV clip, 720×1280, 11 shots, no speech | ~60–90 s | 202 |
| 40 s talking head, 720×1280, 183 words | ~75–110 s | ~260 |

The long poles are OCR (~2–5 s per frame) and ASR (~real-time with `small`). For large folders use
`--jobs 2`, `--whisper-model base`, or `--no-ocr` for videos without overlays.

## Known limits
- The cut detector is a heuristic: very fast motion can create false cuts and soft dissolves can be
  missed. Confirm cuts on the storyboard (red bars).
- OCR misses stylised or animated text and stickers; always read overlays by eye as well.
- ASR can mis-hear names and brand words; verify them against the lips and the context. Captions use
  `--script` to force the intended wording.
- `delogo` smears textured backgrounds; use it only for small overlays on simple backgrounds.
