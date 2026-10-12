# Chosen processing pipeline (recorded decision)

**Decision (2026-09-30):** all media inspection and processing for /analyze-then-generate runs **locally
and deterministically** through `scripts/atg.py`.

**The rule (the user, 2026-10-12), for every mode and every command:** the scripts gather, extract, record,
tabulate and calculate; they never evaluate or decide. They measure (durations, cuts, loudness, spectra), extract
(frames, transcripts, OCR text with its numbers), fetch and probe, record the agents' facts and decisions with who
and why, and calculate pure formulas. They hand out no verdict, status, flag or label derived from content, apply
no threshold that refuses, caps or changes an answer, rank or pick nothing, compare no texts for sameness and
count no words to decide anything; a command refuses only a bad argument, a missing file or tool, a damaged
ledger, an unsafe web address or a failed ffmpeg run, and it keeps the user's own locks (CapCut closed while a
project is written, the locked house text preset). The AI agent that runs the pipeline reads the numbers and
tables, decides from the mode's specification (Recreate, Create, Viral-Browser and Edit alike) and records the
decision with the reason. The numbers that used to be enforced (the 0.10 s sync tolerance, the 15 / 25 % size
bands, the 12 % crop loss, ...) are rules of thumb in the reference documents, applied with judgement.

| stage | tool | why this tool |
|---|---|---|
| Metadata | **ffprobe** (FFmpeg 9.0.2 full build, winget Gyan.FFmpeg) | Exact streams, rotation, SAR, fps, audio stream index. Rotation- and SAR-aware display size, following Higgsfield's own media-pipeline normalisation |
| Structure (cuts, shots, pacing, motion activity) | **FFmpeg** `select` scene score on 192 px frames | Deterministic; one decode pass; no ML dependency |
| Frame sampling | **FFmpeg** `fps=5` (one pass) plus targeted `-ss` seeks | Exact timestamps; ~5 frames per second baseline with adaptive density |
| Static thinning | **Pillow + NumPy** (48×48 grey mean absolute difference vs. the last kept frame) | Cheap, deterministic, and never drops below 1 fps |
| Storyboards | **Pillow** | Labelled chronological contact sheets of **30 frames**, sized to Claude's vision limits (≤ 1.15 MP, ≤ 1568 px long side) so they are read at full size and no cell is shrunk |
| Audio | **FFmpeg** (16 kHz mono WAV, `ebur128`, `silencedetect`, `astats` RMS per 0.5 s) | Deterministic loudness, silences and energy curve |
| Speech | **faster-whisper** `small`, int8 CPU, local cache, word timestamps + VAD. Fallback: **FFmpeg's built-in whisper.cpp filter** (`ggml-base.en.bin`) | Word-level timing is a meaningful advantage over FFmpeg-only ASR (the fallback has segment timing only). Runs offline (`local_files_only`). A transcript only records what the transcriber returned: `has_speech` means at least one word came back, and it cannot tell speech from lyrics (the card agent states the voice type) |
| On-screen text sample | **RapidOCR** (onnxruntime CPU) on ~12 frames per video | Extracts the on-screen text with the numbers that describe it (first and last time, frames it was seen in, share of the frames scanned, row of the frame, confidence, spelling facts such as an @ or a URL pattern); no label is put on any text: the agent decides what is a caption, a fixed overlay, a handle, a watermark or noise (feeds the text policy) |
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
| Densify on demand | `atg.py frames <video> --range a-b --fps 15 --sheet` around fast actions, object interactions, hand contact, gestures, product appearances, swaps, text appearances and transitions |
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
| `video.json`, `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json`, `ocr.json`, `probe.json`, `audio-profile.json` (after `audio-context --profile`) | Machine data: measurements and extractions, no labels |
| `audio/audio-16k.wav` | ASR input |

## Commands

Python: `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` (`config.json → python`).
Script: `C:/Users/Glaresquare1/.claude/analyze-then-generate/scripts/atg.py`. Every command prints one JSON
object as its last stdout line.

```text
atg.py new-run --mode analyze --source "<refs folder>" --assets "<asset path>" … [--examples "<folder>"]   → run_dir
atg.py new-run --mode edit --source "<video path>" …                   (edit: per-edit assets come later)
atg.py state --run "<run>" get [key] | set k=v … | append k=v …
atg.py inventory "<refs folder>" --run "<run>" --as references         → 00-inventory/ (reference material only)
atg.py inventory "<video paths>" --run "<run>" --as sources            → 00-inventory/ (edit: videos only, other files ignored)
atg.py inventory "<asset paths>" --run "<run>" --as assets [--scope video-01]  → 30-assets/<scope>/asset-inventory.{json,md} (paths, kinds, sizes, sub-folder, duplicate_of: facts only; no role is guessed from a file name, the agent confirms each by looking)
atg.py inventory "<examples folder>" --run "<run>" --as examples     → 00-inventory/examples-inventory.{json,md} (study only; may be empty)
atg.py prep-assets --run "<run>" [--scope video-01]                    → previews, docs, font names, assets-sheet-NN.jpg
atg.py prep-all --run "<run>" [--jobs 2] [--only V01,V03] [--redo]     → 10-media/<V>/…, images/, docs/, index.md (each video's length, and apart from it how long its preparation took)
atg.py prep-all --run "<run>" --set examples [--jobs 2]               → 10-media/E01…, examples-index.md
atg.py inventory "<baseline folder>" --run "<run>" --as baseline       → 00-inventory/baseline-inventory.{json,md} (Viral-Browser contrast set: videos that did not spread)
atg.py prep-all --run "<run>" --set baseline [--jobs 2]               → 10-media/B01…, baseline-index.md
atg.py new-run --mode analyze --submode viral-browser --source "<refs folder>" [--baseline "<folder>"]   → adds 30-research/ and deliverables/
atg.py viral-stats --run "<run>" [--set references|baseline|both]     → 20-analysis/corpus-stats.{json,md}: the measured profile (length, hook, pacing, speech, text, sound, loop) as distributions and shares, and one table per Facts key of what the cards' Facts lines say (the category table through the niche vocabulary the agents recorded); tables only, nothing is flagged or ranked
atg.py viral-stats --run "<run>" --no-niche                           → 20-analysis/corpus-profile.{json,md} (Create): the same measured profile without the niche vocabulary, the Facts tables or the references' product layer
atg.py spec add|list|table|judge|gaps|render|reject --run "<run>" --cand C## …   → 30-research/specs.json: each fact with its source, grade, scope and variant (side by side in table); judge records the agent's judgement per field; gaps counts facts and judgements for the core fields; render → deliverables/reference-C##-<name>/spec.{md,json} (viral-browser.md §9.1)
atg.py photo find|add|set|list|check --run "<run>" --cand C## …                    → 30-research/photos.json; LINKS ONLY, no image is downloaded: find lists the image addresses a page declares (in the page's own order), add probes a link with a header request (HEAD) and records the facts, set records the agent's flags (the visual ones only after looking at the image), list / check make the coverage table; photos.md + photos.html in deliverables/reference-C##-<name>/ (public http(s) pages, read-only)
atg.py niches add|map|merge|audit|list|propose --run "<run>" [--by … --reason …] …   → 20-analysis/niche-vocabulary.json: the niche vocabulary the AGENTS decide from the labels in the data and record with who and why (no script lists any niche or compares names; list / propose tabulate the labels in use with their counts)
atg.py candidates add|list|show|set|rate|summary|table --run "<run>" …   → 30-research/candidates.json (viral-browser.md §6, §8): the ledger of the agents' decisions; set records any status with --by and --reason (and --pick-rank), rate records the agent's 1-5 ratings, table sets the recorded values side by side and marks no winner; ranking.md is written by the main session
atg.py evidence add|retract|list --run "<run>" --cand C03 --lane demand …      → 30-research/evidence.json (claim, source, date, grade, independence, signal, as the researching agent stated them; list --counts tabulates the rows and weighs nothing)
atg.py econ --retail 39.9 --vat-pct 21 --landed 6.5 --fulfil 4.2 …    → contribution, break-even CPA and ROAS, MOQ capital (arithmetic only; with --cand and --market the result is stored per market, side by side)
atg.py prep-video "<video>" --out "<dir>" --id V01                     (one video)
atg.py frames "<video>" --out "<dir>" --range 3.0-4.2 --fps 15 --sheet [--label x] | --at 1.2,3.4
atg.py prep-image "<image>" --out "<preview.jpg>"
atg.py doc-text "<file>" --out "<txt>"                                 (docx/pptx/xlsx/txt/md/csv/json/srt/vtt/html)
atg.py hf-put --file "<local>" --url "<upload_url>" --content-type "<exact type>"
atg.py hf-get --url "<result_url>" --out "<file.mp4>"
atg.py split-audio "<given video path>" --run "<run>" [--audio-only]   → <path>/files_audio/ (+ <path>/videos_without_audio/ unless --audio-only)
atg.py audio-profile --audio "<files_audio file>" --out "<json>" [--transcript …] [--cuts …]   → the sound design as numbers: speech share, harmonic ratio outside speech, tempo, beat strength, spectral flatness, steady-tone share, energy per second and its change, hits (with on_cut); no label
atg.py audio-context --run "<run>" [--set references|baseline|examples] [--profile] [--second-pass] [--check [--cards]] [--out FILE]   → 20-analysis/audio-context.{md,json}: every transcript with its times, the language, the speech facts and the sound numbers, and notes about the run (missing / skipped / failed); --second-pass transcribes a video with no words found once more without the voice filter; --check writes nothing (unless --out) and exits 1 when a transcript is missing, failed or skipped or a card lacks its Audio context / Said lines
atg.py fetch-audio --url "<direct audio url>" --page "<page>" --license "<license>" --out "<file>"   → download + <file>.source.json
atg.py restore-audio --generated "<edit>" --audio "<path>/files_audio/<name>.m4a" --audio-offset <s> [--start <s>] --out "<file>"   → the generated picture + the ORIGINAL audio; reports the facts of the result and how much shorter the generated clip was
atg.py sync-check --source "<prepared source / own-silent.mp4>" --output "<final>" [--start <s>] --out "<dir>" [--tol 0.10] [--min-corr 0.5] [--min-motion 0.25]   → <dir>/sync-check.json + sync-sheet.jpg: global and per-window offsets, drift, duration difference, side-by-side sheet; numbers only, no verdict and no fix
atg.py finalize --run "<run>" --video V01 --file "<approved.mp4>" --original "<original video>"   → <path>/final/<name>.mp4 (reports facts, refuses nothing)
atg.py conform --video "<in>" --out "<out>" [--focus-x 0.5 --focus-y 0.5] [--mode fill|pad] [--dry-run]   → exact 720×1280; reports lost_fraction (the share of the picture a crop removes) and never refuses a crop; --dry-run writes nothing
atg.py trim --video "<in>" --out "<out>" --start 0.4 [--end 7.6]
atg.py concat --clips a.mp4 b.mp4 --out joined.mp4 [--seams cut|continuous,…]
atg.py last-frame --video "<clip>" --out "<handoff.png>" [--back 0.3]    → exact last frame, lossless
atg.py capcut-name --video 3                                              → 01_Oct_2026_v03 (free name)
atg.py capcut-prep --draft "<store>/<name>"                               → right after capcut_clone_draft
atg.py capcut-repair --draft "<store>/<name>" --preview "<preview.mp4>"  → after every capcut_save (house text style + register + sync + lint, locked)
atg.py capcut-text-style --draft "<store>/<name>" [--check | --learn [--text N] [--replace]]   → font System, size 10, the user's locked preset (config capcut.text_style.learned)
atg.py strip-inserts --video "<reference>" --inserts 13.0-15.0 --out "<dir>"  → own.mp4, own-silent.mp4, map.json (split points)
atg.py captions --video "<in>" --out "<out>" --spec captions.json | --from-speech [--script "…"]   (fallback only)
atg.py clean --video "<in>" --out "<out>" --delogo "x,y,w,h@t0-t1" [--crop "x,y,w,h"]
atg.py qc --video "<final>" --out "<dir>" --mode analyze|edit [--allowed-text "a|b"] [--expect-duration s] [--expect-aspect 9:16] [--expect-size WxH] [--dense "label:a-b" …] [--dense-fps 30]   → storyboard + measurements beside the expected values (size, duration, aspect, audio, black and frozen spans, the on-screen text its OCR saw beside the planned text), dense checkpoint sheets; no pass or fail
atg.py scale --product-cm H [--distance d --distance-basis "<how d was derived>" --lens f] [--frame img.png --product-px y0-y1 --ref-cm h --ref-px y0-y1 [--depth-ratio r]] [--out scale.json]   # size reckoning, arithmetic only: expected size per shot; observed size as a multiple of the expected one, per estimate; no verdict
atg.py caught-error add --title "…" --video … --run … --mode … --model … --product … --user "<verbatim>" --wrong "…" --class "…" --cause … --fix "…" --rule "…"   # the feedback ledger (caught_errors.md); list [--mode --model --class --status --grep --rules]; set --id CE-nnn --status … --promoted-to …
atg.py model-menu --mode analyze|edit --live-ids "<ids from models_explore>"   (the numbered table of every model, pinned first; it picks nothing)
atg.py ledger begin --run "<run>" --video NN --attempt K --request "<request.json>"   (records a pending entry and reports conflicts[]: an open submission in the lane, jobs in flight against the cap, a request that failed before or already finished; it refuses nothing, the agent decides whether to submit)
atg.py ledger set --run "<run>" --fingerprint F --job J --status submitted|unknown|completed|failed|accepted|rejected|superseded   (superseded = the agent decided not to submit; it frees the lane)
atg.py open --file "<final.mp4>"                                       (Edit Mode review in the default player)
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
  missed, and a cut time can sit a frame or two late. Confirm cuts on the storyboard (red bars): the `c<` cell is
  the frame before the one the score peaks on, `c>` the first frame of the new shot.
- OCR misses stylised or animated text and stickers; always read overlays by eye as well.
- ASR can mis-hear names and brand words; verify them against the lips and the context. Captions use
  `--script` to force the intended wording.
- `delogo` smears textured backgrounds; use it only for small overlays on simple backgrounds.
- Every number the toolkit prints is a measurement or an extraction. Whether a text is a caption, a sound is a
  music bed, a voice is speech or a song, or an output is in sync is the agent's reading of the numbers and the
  pictures.
