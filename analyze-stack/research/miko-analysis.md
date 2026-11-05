# miko `video-ad-stack` — analysis for `analyze-stack` (agent R1)

Source: `C:\Users\Bulzart\.claude\analyze-stack\research\miko\miko-video-ad-stack-main\` (13 files incl. `.gitignore`).
Tested on: `C:\Users\Bulzart\.claude\analyze-stack\samples\sample-27s-roofingpov.mp4` (720x1280, 30 fps, 27.27 s, H.264 + HE-AACv2 stereo 44.1 kHz).
Test outputs: `C:\Users\Bulzart\.claude\analyze-stack\research\r1-test\` (scripts `r1_*.py`, `*.txt`, `*.json`, `sheet_*.jpg`, `kf_*.jpg`, `cut_*.jpg`).
Date: 2026-09-16. Shell for every command below: Windows PowerShell 5.1 (no `&&`/`||`).

---

## 1. File-by-file summary (what each file does in the SOP)

| File (relative to repo root) | Role in the SOP | Key content |
|---|---|---|
| `README.md` | Marketing/setup page for the kit. | 4-stage stack (brand research → reference breakdown → editable ad plan → Higgsfield generation). Requires: visible in-app browser, ffmpeg/ffprobe, frame inspection, Higgsfield visual/audio analysis. "No separate speech-transcription dependency". Preview release; "real end-to-end pilot still pending". Install = copy `skills/video-ad-stack` into `.agents/skills/`. |
| `RUN-STACK.md` | Legacy pointer. | Says the guided workflow now lives in `SKILL.md`; nothing else. |
| `.gitignore` | Hygiene. | Ignores `outputs/ campaigns/ breakdown/ brand/ production/ run-state.md *.mp4 *.mov *.wav *.mp3 .env*`. Implies the run folders the SOP writes (`brand/`, `breakdown/`, `production/`). |
| `skills/video-ad-stack/SKILL.md` | Skill front-matter + entry behaviour. | Trigger phrases ("start the video ad stack"). Loads `references/guided-workflow.md`, then loads each stage's file only when reached. Rules: never make the user name files; guided mode waits for the word **generate** before any paid call; end-to-end mode only when explicitly requested; disclose missing tools honestly. |
| `references/guided-workflow.md` | The orchestrator (conversation script). | Stage order + the exact intake questions: (1) "Which product… send the website… images, Meta Ad Library links, reviews…"; (2) "Send the reference video(s)… any part you want to keep?"; (3) editable preview: script + timed beat/shot plan + generation prompt + attachment map + duration target, then "say 'generate'"; (4) generate, review, stitch. Persists `run-state.md` (stages done, artifact paths, pending job IDs, next action) so paid jobs are resumed, not duplicated. |
| `references/miko-brand-research/workflow.md` | Stage 1 – brand research. | Visible-browser research of homepage/product/about/FAQ/reviews + Meta Ad Library; record URLs + retrieval dates; never ask for credentials; output `brand/brand-research.md` (facts, price/currency, positioning, voice, visual direction, audience hypotheses, objections, observed ad patterns, gaps). Fragrance-specific notes (notes, concentration, bottle). |
| `references/miko-reference-video-breakdown/workflow.md` | Stage 2 – reference breakdown (the analysis SOP). | Probe duration/dimensions/fps/audio; analyse ≤30 s segments but cover the whole video if asked; two evidence methods (ffmpeg measurement + Higgsfield analyzer "watching and listening") that must both complete on matching coverage or the stage is **blocked**; open every contact sheet; closer sampling around ambiguity; reconcile disagreements; overlays vs physical labels inventory; hand-off of transferable mechanics; optional faithful recreation prompt. |
| `references/miko-reference-video-breakdown/references/evidence-workflow.md` | The concrete ffmpeg recipe + reconciliation rules. | Thresholds 0.30 / 0.08, the four filter fragments, 3 fps vs 2 fps sampling, cell→timestamp formula, motion metric caveats, upload→analyze→poll route for Higgsfield, speech rules (analyzer audio results; label paraphrases; no invented speakers), reconciliation bullets, WPM denominator rule. Full detail in §2. |
| `references/miko-reference-video-breakdown/references/output-template.md` | Breakdown document contract. | 10 sections: Source & coverage; Specs; Transcript/dialogue summary; Shot-by-shot table; People & setups; Setting & image; Text & overlays; Audio; Retention mechanisms; Measurements & disagreements; Handoff. Full detail in §2.8. |
| `references/miko-reference-video-breakdown/references/recreation-prompt.md` | Optional faithful-recreation prompt (targets Seedance 2.5). | 8 rules (exact dialogue when authorised, exclude overlays, named objects with positions, match actual style, camera behaviour per beat, setup blocks, real UI via supplied footage, clean source assets). Returns prompt + attachment list, not a guarantee. Full detail in §2.9. |
| `references/miko-reference-to-video-plan/workflow.md` | Stage 3 – adaptation plan. | `production/video-plan.md`: audience hypothesis, adapted mechanism, exact script + on-screen copy, ordered scene IDs with durations/action/camera/lighting/sound/product visibility; continuity requirements; map shots to production operations (start frame, reference video, native speech, edit/assembly); verify Higgsfield model constraints; does **not** submit paid jobs. |
| `references/miko-reference-to-video-plan/references/prompt-contract.md` | Master-prompt contract for the adapted ad. | `production/master-prompt.md` with 7 sections: (1) duration/aspect/style, (2) product-image attachment map, (3) scene/subject/wardrobe/positions/lighting/camera, (4) ordered timed action beats, (5) audio (exact new dialogue, voice, ambience, music, FX; keep silent formats silent), (6) continuity repeated per clip ("same as before" is insufficient), (7) exclusions. Split into numbered clip prompts only when model limits require; planned durations must sum to target; "do not speed speech to conceal timing errors". |
| `references/miko-higgsfield-video-production/workflow.md` | Stage 4 – generation. | Discover current Higgsfield tools/model IDs; `production/run-manifest.json` (scene IDs, params, asset IDs, job IDs, status); persist IDs before polling; budget rules; inspect clips for product fidelity, label legibility, hands, speech, continuity, unwanted text; assemble (normalise formats, trim without cutting words, stitch, verify); audio-derived caption timings. |

---

## 2. Exactly how miko handles video and image analysis

### 2.1 Probe and segment handling
* "Probe video dimensions, frame rate, duration and audio stream" (ffprobe; no exact command given).
* Segment policy: analyse short segments, "preferably up to 30 seconds", but never silently replace a whole-video request with the first 30 s. Split long coverage into **indexed segments** and reconcile their boundaries. Record **source start/end and segment-local timestamps**; preserve original-time offsets in every output.
* Trimming: "Trim the chosen segment accurately" — no command is given (gap; ours in §4.2).
* Shot count rule: **shot count = confirmed internal cuts + 1** for a continuous segment; do not add duplicate segment-boundary shots when segments are stitched back together.

### 2.2 Cut detection — the two thresholds
Filter fragments verbatim from `evidence-workflow.md`:
```text
select='gt(scene,0.30)',showinfo      # hard-cut candidates
select='gt(scene,0.08)',showinfo      # broader visual-change candidates
```
* `scene` is ffmpeg's `select` filter scene-change score (0..1; normalised frame-difference vs previous frame). `showinfo` prints `pts_time` per passed frame to **stderr**.
* Stated caveats (verbatim in spirit): thresholds are "starting heuristics: flashes overcount, similarly colored cuts can be missed, and small UI changes or slow camera moves may not register". Count **confirmed cuts** separately from **candidate changes** and report the threshold with the count.

### 2.3 Contact sheets (frame sampling)
```text
fps=3,scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,tile=4x4:padding=4
```
* 3 sampled frames/s for short fast-cut footage, 2 fps for longer footage; **increase sampling around ambiguity**; preserve aspect ratio (scale+pad, never stretch).
* Cell→timestamp formula for unlabeled tiles: `t = ((sheet-1)*cells_per_sheet + cell-1)/sample_fps + source_offset`. Reminders: a 3x4 sheet has 12 cells not 16; trailing padding cells are not source frames; "verify actual sampled PTS before claiming precise timing".
* "Open every contact sheet yourself"; use full-resolution frames for text/labels/gestures; "Sampled sheets are not enough to claim frame-accurate timing".

### 2.4 Motion metric (optional)
```text
fps=4,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG
```
* `tblend=all_mode=difference` produces |frame_n − frame_n−1|; `signalstats` YAVG = mean luma of that difference frame (0..255) = a per-sample "motion energy" number at 4 Hz.
* Rules: report preprocessing/settings next to values; "low difference is not automatically a dead or ineffective shot"; confirm motion visually.

### 2.5 "Watching and listening" (Higgsfield analyzer)
* Upload the trimmed segment through the current media-upload route, confirm, `video_analysis_create`, persist the analysis ID, poll — never re-submit. A direct YouTube link route exists but a full-link analysis "must not be misrepresented as the same trimmed segment".
* Audio/speech comes only from the analyzer: speech, delivery, music, ambience, effects. No audio stream ⇒ no transcript. If the analyzer returns paraphrases, label them **summary**, never "verbatim". Replay source audio for important ambiguities; mark uncertain words/speakers; never invent speaker identity. This "supersedes the original PDF's separate transcription step".

### 2.6 Reconciliation rules (evidence hierarchy)
1. **Cut timing**: detector candidate + source-frame confirmation; inspect adjacent source frames for precision.
2. **Camera motion, wardrobe, room/setup, props**: compare consecutive inspected frames.
3. **Spoken words**: analyzer dialogue evidence + source-audio checking; distinguish exact words from summaries.
4. **Music, effects, acoustics**: audio inspection/analyzer with uncertainty stated.
5. **Labels or screen text (OCR by eye)**: full-resolution source frames first; **never invent unreadable text**; separate added overlays (captions, handles, watermarks, emojis, UI) from physical product text.
6. Record material disagreements + evidence + resolution; keep unresolved cases marked. Confirmed source footage/audio is the authority.
7. **Speech rate**: compute WPM only with a sufficiently complete dialogue record; state the denominator (whole segment vs speech-only); 150/175 WPM are descriptive reference points, not targets.
8. Uncertainty labelling everywhere: "Distinguish measured values, estimates and creative interpretation"; "Do not claim attention or conversion performance was measured from the footage alone"; missing tools are "a limitation to report, not evidence that an analysis ran".

### 2.7 Screen text / OCR
No OCR tool. Text is read by the agent from full-resolution frames; legibility gaps are listed in "Text and overlays"; the recreation brief **excludes** added overlays by default and **preserves** intended physical label/screen text (with its source).

### 2.8 Output template (`breakdown.md`, one per reference)
1. **Source and coverage** – file/link, selected segment, source offset, inspection methods completed, missing layers, uncertainty.
2. **Specs** – duration, dimensions, fps, audio presence, confirmed cut timestamps/count, visual-change candidate count **with threshold**, distinct filming setups, WPM with denominator; metadata vs estimates separated.
3. **Transcript or dialogue summary** – time range, speaker label, words; slang/delivery kept; uncertain words/speakers marked; source dialogue kept distinct from adapted script.
4. **Shot-by-shot** table: `| Source time | Framing | Camera move | On screen / props | Action and delivery |` — one row per confirmed shot; gestures, expressions, product contact, timing, not mood labels.
5. **People and setups** – appearance, hair, makeup, wardrobe, jewelry, nails, gestures per setup; hook vs main take changes.
6. **Setting and image** – objects with positions, surfaces, lighting direction/quality, grade, visible camera characteristics; inferred equipment vs observable traits.
7. **Text and overlays** – timestamped captions, titles, watermarks, handles, emojis, UI styling; overlays-to-exclude vs physical-text-to-preserve; legibility gaps.
8. **Audio** – music character/continuity/ducking, effects + timestamps, mic quality, room acoustics, other voices; never invent a soundtrack name.
9. **Retention mechanisms** – observed hooks, open loops, interrupts, show-while-telling, payoffs; hypothesised function, no measured-performance claims.
10. **Measurements and disagreements** – metric, method, value, confidence/limitation; analyzer/transcript/frame conflicts and resolutions.
11. **Handoff** – transferable structure, reference-specific elements to replace, exact product/identity references needed, difficult shots, continuity requirements.

### 2.9 Recreation-prompt contract (Seedance 2.5 target)
1. Preserve authorised source dialogue exactly when faithful dialogue is requested; label speakers + delivery; rewrites in a separate adapted version.
2. Exclude captions/subtitles/handles/watermarks/graphics by default; specify intended physical label/screen text and its source; final captions belong to editing.
3. Named background objects with positions, not aesthetic adjectives.
4. Match the actual visual style; phone-realism language only for phone/UGC references; never strip cinematic lighting/grade from a cinematic reference.
5. Tripod/handheld behaviour and camera moves specified **per dialogue/action beat**, with precise timing where sync matters.
6. Separate setup blocks for wardrobe/room changes plus the beat that connects them.
7. Real UI on screen → supplied/authorised screen footage, not model-invented text; check reference constraints; preserve aspect ratio; mute clips used as visual-only references.
8. Prefer clean authorised source assets so overlays are not reproduced; log reference preprocessing; keep original footage + attribution in evidence.
Return = prompt + attachment list, "not a claim that the generation will perfectly match the source". `prompt-contract.md` adds for multi-clip: numbered clip prompts, planned durations summing to the target, continuity/boundary actions, assembly order; "A generated clip may serve as a continuity reference when supported".

---

## 3. What to adopt, what is weak, how we go beyond

### 3.1 Adopt verbatim (or near-verbatim)
* The **two-threshold cut logic** (0.30 hard cuts / 0.08 broad changes) with the "candidates vs confirmed" vocabulary and the explicit caveat list.
* The **contact-sheet recipe** (`fps=3|2`, 270x480 scale+pad, `tile=4x4:padding=4`), the cell→timestamp formula, and the rule "sampled sheets never justify frame-accurate claims; go to full-res frames around ambiguity".
* **Shot count = confirmed internal cuts + 1**, no double-counting at segment boundaries; source-offset bookkeeping for segments.
* The **evidence hierarchy / reconciliation** list (§2.6) and the uncertainty-labelling rules (measured vs estimate vs interpretation; never invent unreadable text, speaker identity or a soundtrack name; state WPM denominator).
* The **shot-by-shot table columns** and the overlay-vs-physical-text split (both map 1:1 onto our `20-analysis\visual.md` and `50-prompts\references\`).
* The **recreation-prompt rules** 2–8 and the prompt-contract's "continuity repeated in every clip; durations sum to target; never speed speech to hide timing errors; exclusions section".
* Process hygiene: persist job IDs before polling; resume instead of re-submitting paid jobs; "generate" is the only spend approval; never ask for credentials.

### 3.2 Weak / missing (and why it matters for us)
| Weakness | Consequence | Our replacement |
|---|---|---|
| **No local transcription** — speech comes only from the Higgsfield analyzer, which may return paraphrases. | No word timestamps ⇒ cannot place cuts/beats on words, cannot compute WPM reliably, cannot produce `transcript.srt`. | `faster-whisper` (word timestamps, VAD) locally; ffmpeg `whisper` filter as static-binary fallback; ElevenLabs Scribe / Descript as cloud fallbacks (see `tool-audit.md`). |
| **Hard dependence on the Higgsfield analyzer** ("both methods must complete or the stage is blocked"). | A 3–5 min cloud job with unknown cost becomes a hard blocker; accuracy drops with length. | Local measurement is primary; Higgsfield `video_analysis` is an optional **second opinion** on ≤30 s segments. |
| **Cut detection = one ffmpeg heuristic**. On the sample it missed 5 of 12 cuts at 0.30 (see §4.3). | Under-counted shots ⇒ wrong slicing/seconds-per-prompt. | Union of ffmpeg `select(scene)` + `scdet` + PySceneDetect `ContentDetector`/`AdaptiveDetector`, merged within 3 frames, then frame-pair confirmation. |
| **No OCR** (agent eyeballs frames). | Slow, misses small text, no timestamps for caption in/out. | RapidOCR on 1 fps keyframes → `ocr.json` with per-frame text + boxes; caption in/out times by first/last detection. |
| **No audio feature extraction** (no BPM, beat grid, onsets, loudness, dead air). | Cannot align cuts to beats, cannot spec music tempo for Seedance audio, cannot QA loudness of generated clips. | librosa (BPM/beats/onsets/RMS) + ffmpeg `ebur128`/`silencedetect`/`astats` → `audio-features.json`. |
| **No camera-motion or style measurement** (all inferred by eye). | Prompts describe camera moves vaguely; style swap has no measured baseline. | OpenCV optical-flow global-motion model per second (pan/tilt/zoom/handheld/static), edge density, saturation/value, k-means palette, SITI → `style-profile.md` inputs. |
| **No physics / continuity / blending rules** for AI generation. | Prompts that ask for impossible object behaviour or inconsistent identity between clips. | `references\physics-continuity.md` (ours) + `continuity-sheet.md` per run + anomaly checklist stage. |
| **No product-swap logic** (only brand adaptation of the whole concept). | Cannot keep the format and swap only the product. | Product identification → `product-spec.md` + `swap-map.md` (which shots/beats touch the product; hand contact; label legibility; scale). |
| **No compression planning** (target duration = source duration; split only on model limits). | Cannot deliver "clean 30 s from a 62 s reference". | Mode 3 compression plan: beat map → keep/merge/drop with owner approval. |
| **No post-generation phase** beyond "inspect clips, stitch". | No QA loop, no trend boosts, no editable project. | `60-qa` anomaly loop + `90-postgen` (clip QA, trend brief, CapCut/OTIO editable project, render, final check). |
| **No machine-readable outputs** (Markdown only). | Cannot resume from a stage or feed scripts. | `probe.json`, `cuts.json`, `shots.json`, `transcript.json`, `ocr.json`, `audio-features.json`, `state.json`. |
| Windows/PowerShell quoting never addressed; `showinfo` output on stderr is awkward to capture. | Commands fail on Windows. | Verified PowerShell forms in §4 (`metadata=print:file=`, `Start-Process -RedirectStandardError`). |
| "Browser-first" brand research tied to Codex's in-app browser (`iab`/CUA). | Not portable. | Out of scope for measurement; product spec comes from owner-supplied images + `product-library`. |

### 3.3 How we go beyond (mapping to LAYOUT stages)
* **Stage 1 measure** is fully scripted (`tools\*.py`) and writes JSON + Markdown; every number carries its method and threshold; Higgsfield analysis is optional.
* **Stage 2 analysis** adds `audio.md` (BPM/beats/loudness/dead air), `style-profile.md` (measured cues), `beat-map.md` (cuts × beats × words), `entities.json` (people/products/objects with first/last appearance).
* **Stage 3–4** add product swap, mode selection, compression plan, continuity sheet, style bible — none of which exist in miko.
* **Stage 5–6** keep miko's prompt rules but add the anomaly checklist loop across all prompts together.
* **Post-gen** keeps miko's clip-inspection list (product fidelity, label legibility, hands, speech, continuity, unwanted text) and adds trend boosts + editable project + render.

---

## 4. Reusable techniques — tested PowerShell commands (Windows, ffmpeg 9.0.1)

Conventions that were verified to work:
* Put the whole `-vf`/`-af` graph in **double quotes**; use **single quotes inside** for expressions and for any value containing a drive-letter colon, escaping the colon: `fontfile='C\:/Windows/Fonts/arial.ttf'`, `model='C\:/Users/.../ggml-tiny.en.bin'`. An unquoted `C\:` failed to parse in the `whisper` filter ("No option name near …").
* `drawtext` **must** get `fontfile=` — without it ffmpeg prints `Fontconfig error: Cannot load default config file` and writes nothing.
* ffmpeg 9 removed `-vsync`; use `-fps_mode vfr` ("Unrecognized option 'vsync'" otherwise).
* Metadata-style filters (`select`, `scdet`, `signalstats`, `silencedetect`…) can write to a file with `metadata=print:file=<name>` / `ametadata=print:file=<name>`; use a relative name after `Set-Location` to avoid the colon problem.
* Filters that only print a summary to stderr (`showinfo`, `ebur128`, `astats`, `volumedetect`, `silencedetect`, `siti`, `freezedetect`, `blackdetect`) are captured cleanly in PS 5.1 with `Start-Process -RedirectStandardError` (native `2>` wraps lines in ErrorRecords).
* `%03d` output patterns need no escaping in PowerShell; `-f null -` is the null sink.

Prelude used by every command:
```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$ff = "C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
$s  = "C:\Users\Bulzart\.claude\analyze-stack\samples\sample-27s-roofingpov.mp4"
$o  = "C:\Users\Bulzart\.claude\analyze-stack\research\r1-test"; New-Item -ItemType Directory -Force $o | Out-Null; Set-Location $o
```

### 4.1 Probe → `probe.json`
```powershell
ffprobe -v error -print_format json -show_format -show_streams $s | Out-File -Encoding utf8 "$o\probe.json"
```
Result: video `h264` 720x1280 (DAR 9:16) 30/1 fps, 818 frames, 27.266667 s, yuv420p bt709, 2.1 Mb/s; audio `aac` HE-AACv2 44100 Hz stereo 64 kb/s, 27.235 s; format tags include `aigc_info`, `comment: vid:v1204…` (TikTok download).

### 4.2 Segment trim (source offset bookkeeping — miko gives no command)
```powershell
# accurate re-encode trim (frame-exact); record start=10.000 end=25.000 in measure-summary.md
ffmpeg -hide_banner -loglevel error -y -ss 10.000 -to 25.000 -i $s -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 128k -movflags +faststart seg-01_10.000-25.000.mp4
```
Segment-local time `t_local` ⇒ source time `t_src = t_local + 10.000`. (Not run on the sample; standard ffmpeg syntax.)

### 4.3 Cut candidates — three detectors, then reconcile
```powershell
& $ff -hide_banner -loglevel error -i $s -vf "select='gt(scene,0.30)',metadata=print:file=scene030.txt" -an -f null -
& $ff -hide_banner -loglevel error -i $s -vf "select='gt(scene,0.08)',metadata=print:file=scene008.txt" -an -f null -
& $ff -hide_banner -loglevel error -i $s -vf "scdet=threshold=10:sc_pass=1,metadata=print:file=scdet10.txt" -an -f null -
# miko's original showinfo form (stderr) — captured via Start-Process:
Start-Process -FilePath $ff -ArgumentList "-hide_banner -i `"$s`" -vf `"select='gt(scene,0.30)',showinfo`" -an -f null -" -NoNewWindow -Wait -RedirectStandardError "$o\showinfo030.txt"
Select-String -Path "$o\showinfo030.txt" -Pattern "pts_time" | ForEach-Object { $_.Line }
# PySceneDetect (Python API: research\r1-test\r1_scenedetect.py; CLI form below)
scenedetect -i $s detect-adaptive list-scenes -n          # -n = print only, no CSV
scenedetect -i $s detect-content -t 27 list-scenes -n
```
Output format of `metadata=print:file=`: pairs of lines `frame:N pts:P pts_time:T` / `lavfi.scene_score=S` (or `lavfi.scd.score`, `lavfi.scd.mafd`, `lavfi.scd.time`).

**Measured on the sample (source seconds):**

| Detector | Cuts found | Timestamps |
|---|---|---|
| ffmpeg `scene>0.30` | 7 | 1.000 (0.347), 3.400 (0.473), 4.433 (0.405), 7.000 (0.310), 7.500 (0.367), 10.000 (0.458), 18.533 (0.519) |
| ffmpeg `scene>0.08` | 21 raw → 12 after merging "echo" frames | adds 8.433 (0.287), 9.333 (0.247), 19.867 (0.290); every real cut also produced a second hit 1 frame later (score 0.09–0.26) plus 0.033 (first frame) |
| ffmpeg `scdet=10` | 10 | 1.0, 3.4, 4.433, 7.0, 7.5, 7.533 (dup), 8.433, 10.0, 18.533, 19.867 |
| PySceneDetect `ContentDetector(threshold=27, min_scene_len=6)` | 12 cuts / 13 scenes, 5.3 s | 1.0, 3.4, 4.433, 7.0, 7.5, 8.433, 9.333, 10.0, 18.533, 19.867, 21.3, 22.8 |
| PySceneDetect `AdaptiveDetector(adaptive_threshold=3, min_scene_len=6)` | 8 cuts / 9 scenes, 2.3 s (CLI 3.9 s, 210 fps) | 1.0, 3.4, 4.433, 7.0, 9.333, 10.0, 18.533, 19.867 |

Reconciliation on contact sheets (`sheet_02.jpg` = 5.333–10.333 s): 7.0, 7.5, 8.433, 9.333 and 10.0 are all visible framing jumps ⇒ real cuts. So miko's 0.30 alone under-counts (7 vs ≥12), 0.08 over-counts unless merged. **Rule for our `cuts.json`:** union of all detectors → merge hits within 3 frames (0.10 s) → confidence = number of detectors agreeing (ContentDetector-only hits such as 21.3/22.8 need frame-pair confirmation) → shots = confirmed cuts + 1 = 13.

### 4.4 Contact sheets with burned-in timestamps (miko recipe + `drawtext`)
```powershell
& $ff -hide_banner -loglevel error -y -i $s -vf "fps=3,scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,drawtext=fontfile='C\:/Windows/Fonts/arial.ttf':text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x4:padding=4:color=black" -q:v 4 "sheet_%02d.jpg"
```
Result: 6 sheets (1096x1936 px, ~500 KB each) covering 81 sampled frames; the drawn label on sheet 2 cell 1 reads `00:00:05.333`, which equals the miko formula `((2-1)*16 + 0)/3 = 5.333 s` — so cells can be trusted **when the fps filter runs first**. Use `-q:v 6` and `scale=180:320` for cheaper sheets on long videos; use `fps=2` above ~60 s.

### 4.5 Keyframes and cut frames (inputs for OCR, palette, prompt references)
```powershell
& $ff -hide_banner -loglevel error -y -i $s -vf "fps=1,scale=360:-2" -q:v 5 "kf_%03d.jpg"                        # 1 fps keyframes (27 files, ~40 KB each)
& $ff -hide_banner -loglevel error -y -i $s -vf "select='gt(scene,0.30)',scale=540:-2" -fps_mode vfr -q:v 3 "cut_%03d.jpg"   # first frame of each new shot
& $ff -hide_banner -loglevel error -y -ss 12.500 -i $s -frames:v 1 -q:v 2 "frame_12.500.jpg"                      # one full-res frame (for reading labels)
```
Shot-midpoint frames: compute `(start+end)/2` from `cuts.json` and run the third form per shot (scripted in Stage 1).

### 4.6 Motion energy (miko metric) and camera-motion classification
```powershell
& $ff -hide_banner -loglevel error -i $s -vf "fps=4,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=motion_yavg.txt" -an -f null -
```
Sample: YAVG 17–55 at 4 Hz (e.g. 55.2 at t=1.00 = the cut; 17.6 at 1.50 = steady handheld). Treat spikes at cut times as cuts, not motion.
Camera-motion classification (OpenCV, `r1_motion.py`, 21 s for the 27 s clip): Farneback flow at 10 pairs/s on 320-px frames → `estimateAffinePartial2D` (RANSAC) gives translation/scale/rotation + non-rigid residual; per-second labels + `frame_diff`, `edge_density`, `sat`, `val`; k-means (k=5) palette. Sample palette: `#c6ab99 35 %`, `#302122 22 %`, `#6f6865 20 %`, `#d1d0db 18 %`, `#d01642 5 %` (tan roof, black gloves, grey, ice/white, red cooler). Labels on this POV clip were mostly `tilt-*`/`pan-*`/`subject-motion` with residual 1–9 px — thresholds still need calibration on tripod/gimbal references (flagged in `tool-audit.md`).

### 4.7 Audio measurements
```powershell
& $ff -hide_banner -loglevel error -y -i $s -vn -ac 1 -ar 16000 -c:a pcm_s16le audio16k.wav      # whisper input
Start-Process -FilePath $ff -ArgumentList "-hide_banner -nostats -i `"$s`" -af `"silencedetect=n=-30dB:d=0.5`" -vn -f null -" -NoNewWindow -Wait -RedirectStandardError "$o\silence.txt"
Start-Process -FilePath $ff -ArgumentList "-hide_banner -nostats -i `"$s`" -af `"ebur128=peak=true`" -vn -f null -" -NoNewWindow -Wait -RedirectStandardError "$o\ebur128.txt"
Start-Process -FilePath $ff -ArgumentList "-hide_banner -nostats -i `"$s`" -af `"astats=measure_overall=all:measure_perchannel=none`" -vn -f null -" -NoNewWindow -Wait -RedirectStandardError "$o\astats.txt"
Start-Process -FilePath $ff -ArgumentList "-hide_banner -nostats -i `"$s`" -vf `"freezedetect=n=0.003:d=0.5,blackdetect=d=0.3:pix_th=0.10`" -an -f null -" -NoNewWindow -Wait -RedirectStandardError "$o\freeze_black.txt"
```
Sample: 8 silences ≥0.5 s below −30 dB (largest 9.34–14.01 s and 14.01–19.95 s); integrated loudness **−38.0 LUFS**, LRA 14.2 LU, true peak −5.9 dBFS; RMS −42.9 dB, peak −6.4 dB (a very quiet ambient/music bed, no speech); no freeze or black intervals. Loudness target for delivery QA: −14 LUFS (TikTok/IG) via `loudnorm=I=-14:TP=-1.5:LRA=11`.

### 4.8 Transcription (three routes, all verified)
```powershell
# 1) faster-whisper (word timestamps + VAD) — research\r1-test\r1_whisper.py <video> <out.json> <model> [lang]
python "$o\r1_whisper.py" $s "$o\transcript-tiny.json" tiny en
# 2) ffmpeg's built-in whisper.cpp filter (static build, no Python) — segment timestamps only
& $ff -hide_banner -loglevel warning -y -i audio16k.wav -af "whisper=model='C\:/Users/Bulzart/.cache/whisper-cpp/ggml-tiny.en.bin':language=en:queue=10:use_gpu=false:format=srt:destination=whisper_ffmpeg.srt" -f null -
```
Sample-27s: **no speech** → faster-whisper returned 0 segments and auto-detected language `cy` at p=0.245 (rule: if `language_probability < 0.5` or zero segments ⇒ record "no speech detected"; always pass `language="en"` for US content); ffmpeg whisper wrote an empty SRT in 3.9 s. On `sample-40s-sophiesnowscents.mp4` (speech): faster-whisper `tiny` int8 CPU = 7.95 s total for 40 s (1.65 s model load), 16 segments with per-word `start/end/probability`; ffmpeg whisper `tiny.en` = 11.5 s, 21 SRT blocks. `tiny` mis-hears brand words ("Create a Vectus" for a perfume name) — use `small` or `base` in production and keep `tiny` for smoke tests.

### 4.9 On-screen text (RapidOCR on frames) — `r1_ocr.py <video> <out.json> <t1,t2,…>`
Sample: t=0.5 s → `POV: This combo had potential` (score 0.999); t=2.0 s → same (0.978); t=10.5/20/26 s → nothing. Caption window ≈ 0.0–3.0 s (matches sheet 1). Engine init 0.96 s; per-frame < 0.3 s at 720x1280.

### 4.10 Measure-summary block we will emit (miko "Specs" section, extended)
```text
duration 27.267 s | 720x1280 9:16 | 30 fps | audio: yes (HE-AACv2 stereo, -38.0 LUFS, no speech)
cuts: 12 confirmed (union of scene>0.30 [7], scdet10 [9], ContentDetector27 [12]; merged @3 frames; 2 unconfirmed by frame pair) → 13 shots, mean 2.1 s, min 0.5 s, max 8.5 s
visual-change candidates: 21 raw @0.08 (12 after echo merge)
on-screen text: "POV: This combo had potential" 0.0–3.0 s (OCR 0.98–0.999)
motion: handheld POV throughout; mean_flow 0.6–11.6 px/frame @320px; palette #c6ab99 #302122 #6f6865 #d1d0db #d01642
music: ~99 BPM (librosa beat_track 99.4; autocorr fallback 99.4), 44 beats, 77 onsets
```
