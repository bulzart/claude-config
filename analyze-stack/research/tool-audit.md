# Local tool audit for `analyze-stack` (agent R1) — 2026-09-16

Machine: Windows 11 Pro 10.0.26200, Windows PowerShell 5.1. All tests run from a fresh shell after
`$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`.
Test artefacts: `C:\Users\Bulzart\.claude\analyze-stack\research\r1-test\`.

> Important event during the audit: at the start, `ctranslate2`, `onnxruntime`, `opentimelineio` and `soxr` failed with
> `DLL load failed … The specified module could not be found` because no system-wide MSVC C++ runtime was installed
> (`C:\Windows\System32\msvcp140.dll` absent, no `HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64` key).
> Later in the session **"Microsoft Visual C++ 2022 X64 Minimum/Additional Runtime 14.51.36247" appeared with InstallDate 20260916**
> (installed by the main session), after which every package imports cleanly with no workaround. `r1_dllshim.py` in the test
> folder was a process-local `os.add_dll_directory` workaround used before that; it is now a no-op (`SHIM_DIR = None`) and can be deleted.

## A. Summary table

| Tool | Status | Version | Absolute path | Role in our pipeline |
|---|---|---|---|---|
| ffmpeg | OK | 9.0.1-full_build-www.gyan.dev (gcc 16.1.0) | `C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe` | Stage 1 measurement (cuts, sheets, keyframes, motion, audio metrics, wav extraction), post-gen render/normalise/concat/loudness, captions burn-in, built-in whisper fallback |
| ffprobe | OK | 9.0.1 | same folder, `ffprobe.exe` | `probe.json`, duration/fps checks of generated clips |
| Python | OK | 3.12.10 (64-bit) | `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe` (`py.exe` launcher also present) | runs `tools\*.py` |
| pip | OK | 26.2.1 | `python -m pip` | package verification only |
| PySceneDetect | OK | 0.7.1 (lib + CLI) | `…\Python312\Scripts\scenedetect.exe` | cut detection (ContentDetector/AdaptiveDetector) |
| faster-whisper / ctranslate2 | OK (after VC++ runtime) | 1.2.1 / 4.8.2 (CPU int8; no CUDA device) | site-packages; models cached in `C:\Users\Bulzart\.cache\huggingface\hub\models--Systran--faster-whisper-*` (`tiny` downloaded) | transcript with word timestamps |
| RapidOCR / onnxruntime | OK (after VC++ runtime) | rapidocr-onnxruntime 1.4.4 / onnxruntime 1.30.0 (CPU provider) | site-packages | on-screen text OCR on keyframes |
| librosa / soundfile / soxr | OK (after VC++ runtime) | 1.0.0 / 0.14.0 / 1.1.0 | site-packages | BPM, beat grid, onsets, RMS, dead air |
| OpenCV | OK | opencv-python 5.0.0.93 **and** opencv-python-headless 5.0.0.93 (both installed; `cv2.__version__` 5.0.0) | site-packages | optical flow, phase correlation, edge density, palette, histogram |
| numpy / scipy / scikit-learn | OK | 2.5.3 / 1.18.1 / 1.9.1 | site-packages | numerics, k-means fallback |
| Pillow | OK | 11.3.0 | site-packages | image I/O, reference crops |
| moviepy | OK | 2.2.1 (pip) — module reports `__version__` 2.1.2 | site-packages | optional simple assembly; prefer ffmpeg |
| imageio-ffmpeg | OK | 0.6.0 (bundles its own `ffmpeg-win-x86_64-v7.1.exe`) | `…\site-packages\imageio_ffmpeg\binaries\` | fallback ffmpeg binary for Python libs only; do **not** use for our commands (v7.1, not 9.0.1) |
| yt-dlp | OK (lib + CLI; YouTube metadata fetch verified) | 2026.08.19 | `…\Python312\Scripts\yt-dlp.exe` | link download to `00-input\` |
| pydub | OK | 0.25.1 (uses ffmpeg on PATH) | site-packages | optional audio slicing |
| OpenTimelineIO | OK (after VC++ runtime) | 0.18.1 | site-packages | editable timeline interchange (post-gen) |
| pyJianYingDraft | OK | 0.3.0 (import name `pyJianYingDraft`) | site-packages | CapCut draft generation (post-gen) |
| requests / httpx | OK | 2.34.2 / 0.28.1 | site-packages | HTTP (uploads to MCP presigned URLs can also use `Invoke-WebRequest`) |
| PyAV | OK | av 18.1.0 | site-packages | faster-whisper decodes mp4 directly (no wav needed) |
| pymediainfo | OK | 7.0.1 | site-packages | optional metadata |
| huggingface_hub | OK | 1.31.0 (warns: no HF_TOKEN; symlinks unsupported without Developer Mode — harmless) | — | whisper model downloads |
| Node.js / npm | OK | v24.21.0 / 11.19.0 | `C:\Program Files\nodejs\node.exe` | HyperFrames CLI (not installed yet), any JS helpers |
| Git | OK | 2.55.0.windows.3 | `C:\Program Files\Git\cmd\git.exe` | versioning of the stack |
| CapCut | OK (present) | 9.4.0.4015 | `C:\Users\Bulzart\AppData\Local\CapCut\Apps\9.4.0.4015\CapCut.exe`; drafts `C:\Users\Bulzart\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<name>\draft_content.json` | editable project target (post-gen) |
| HyperFrames local skills | OK (installed) | 8 `hyperframes*` skills + 12 workflow skills | `C:\Users\Bulzart\.claude\skills\hyperframes*` etc. | HTML-composition editing/captions route (post-gen); needs CLI |
| HyperFrames CLI | **NOT installed** | would be `hyperframes@0.8.43` via npx (npx refused in non-interactive mode: "missing packages and no YES option") | — | `init/lint/check/preview/render/transcribe/tts` |
| whisper.cpp model for ffmpeg `whisper` filter | downloaded (tiny.en, 77.7 MB) | ggml-tiny.en.bin | `C:\Users\Bulzart\.cache\whisper-cpp\ggml-tiny.en.bin` | Python-free transcription fallback |
| MSVC C++ 2022 x64 runtime | OK (installed 2026-09-16 during this session) | 14.51.36247 | `C:\Windows\System32\msvcp140*.dll` | prerequisite for ctranslate2/onnxruntime/otio/soxr |

## B. ffmpeg / ffprobe 9.0.1 details

Version line: `ffmpeg version 9.0.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers`, `built with gcc 16.1.0 (Rev2, Built by MSYS2 project)`; libavfilter 12.1.101.

Requested build flags — all present: `--enable-libass`, `--enable-libfreetype`, `--enable-libx264`, `--enable-libopus`, `--enable-libvpx`, `--enable-libwebp`.
Also relevant: `--enable-whisper` (whisper.cpp audio filter), `--enable-libvmaf`, `--enable-libvidstab`, `--enable-fontconfig --enable-libfribidi --enable-libharfbuzz`, `--enable-libx265 --enable-libsvtav1 --enable-libaom --enable-librav1e`, `--enable-librubberband --enable-libsoxr`, `--enable-libmp3lame`, HW: `--enable-nvenc --enable-amf --enable-libvpl --enable-d3d11va/d3d12va --enable-vulkan --enable-libplacebo`, `--enable-chromaprint`, `--enable-libzimg`.

Filter availability (`ffmpeg -hide_banner -filters`):

| Filter | Present | Notes |
|---|---|---|
| `select` (scene expr) | yes | `select='gt(scene,0.30)'` → `lavfi.scene_score` metadata |
| `scdet` | yes | options `threshold` 0–100 (default 10), `sc_pass` (pass only scene-change frames); metadata `lavfi.scd.score`, `lavfi.scd.mafd`, `lavfi.scd.time` |
| `showinfo` | yes | stderr per-frame info |
| `tile` | yes | `tile=4x4:padding=4:color=black` |
| `tblend` | yes | `tblend=all_mode=difference` |
| `signalstats` | yes | `lavfi.signalstats.YAVG` etc. |
| `freezedetect` | yes | `freezedetect=n=0.003:d=0.5` |
| `blackdetect` | yes | `blackdetect=d=0.3:pix_th=0.10` |
| `silencedetect` | yes | `silencedetect=n=-30dB:d=0.5` |
| `ebur128` | yes | `ebur128=peak=true` (I, LRA, true peak) |
| `astats` | yes | `astats=measure_overall=all:measure_perchannel=none` |
| `loudnorm` | yes | `loudnorm=I=-14:TP=-1.5:LRA=11` |
| `xfade` | yes | crossfades for assembly |
| `drawtext` | yes (libfreetype) | **needs `fontfile=`**; fontconfig default config missing on this machine |
| `subtitles` | yes (libass) | burn-in SRT/ASS |
| `ass` | yes (libass) | |
| `ocr` | **no** | no libtesseract in the gyan build → use RapidOCR |
| `cropdetect` | yes | |
| `thumbnail` | yes | representative frame per N |
| `minterpolate` | yes | slow-mo / fps conversion |
| `palettegen` / `paletteuse` | yes | GIF/palette |
| `whisper` | **yes** | options: `model` (ggml path), `language` (default auto), `translate`, `queue` (default 3 s), `use_gpu` (default true), `gpu_device`, `destination`, `format` text\|srt\|json, `max_len`, `vad_model`, `vad_threshold` 0.5, `vad_min_speech_duration` 0.1, `vad_min_silence_duration` 0.5 |
| extra useful | yes | `siti` (SI/TI, slow: 58 s for 27 s), `blurdetect`, `entropy`, `edgedetect`, `deshake`, `vidstabdetect/transform`, `libvmaf`, `photosensitivity`, `mpdecimate`, `zoompan`, `showwavespic`, `showspectrumpic`, `volumedetect`, `silenceremove`, `dynaudnorm`, `sidechaincompress`, `rubberband`, `atempo`, `concat`, `overlay`, `lut3d`, `curves`, `eq`, `unsharp`, `gblur`, `chromakey`, `colorkey`, `scale2ref` |

Windows/ffmpeg-9 gotchas verified: `-vsync` removed → `-fps_mode vfr`; values containing `C:` must be single-quoted with `\:`; `drawtext` without `fontfile` fails; capture stderr-only filters with `Start-Process … -RedirectStandardError` (see `miko-analysis.md` §4).

## C. Python 3.12 packages (`python -m pip list`, all imports smoke-tested with `r1_imports.py`)

| Package | Version | Import | Smoke test |
|---|---|---|---|
| opentimelineio | 0.18.1 | OK | `otio.schema.Timeline(name='t')` OK |
| scenedetect | 0.7.1 | OK | ContentDetector 13 scenes / 5.3 s, AdaptiveDetector 9 scenes / 2.3 s on 27 s clip; CLI 210 fps. Deprecation: use `FrameTimecode.seconds` / `.frame_num` (not `get_seconds()/get_frames()`) |
| faster-whisper | 1.2.1 | OK | `tiny` int8 CPU: 40 s speech clip in 7.95 s incl. 1.65 s load; word timestamps + probabilities; first-run model download 85 s |
| ctranslate2 | 4.8.2 | OK | CUDA devices 0; CPU compute types float32/int16/int8/int8_float32 |
| moviepy | 2.2.1 | OK | import only |
| pillow | 11.3.0 | OK | import only |
| numpy | 2.5.3 | OK | |
| opencv-python-headless (+ opencv-python) | 5.0.0.93 | OK | Farneback flow + `estimateAffinePartial2D` + `phaseCorrelate` + `kmeans` ran (21 s / 27 s clip) |
| imageio-ffmpeg | 0.6.0 | OK | bundled ffmpeg 7.1 binary |
| yt-dlp | 2026.08.19 | OK | `yt-dlp --simulate --print "%(title)s | %(duration)s s | %(width)sx%(height)s" <YouTube URL>` returned `Big Buck Bunny … | 635 s | 3840x2160` |
| librosa | 1.0.0 | OK | `beat_track` 99.38 BPM, 44 beats, 77 onsets; **first run 40 s** (numba JIT) — warm the cache once or use the numpy fallback (`r1_audio_basic.py`, 0.15 s, same 99.4 BPM) |
| soundfile | 0.14.0 | OK | wav read |
| pydub | 0.25.1 | OK | import only |
| rapidocr-onnxruntime | 1.4.4 | OK | engine init 0.96 s; read `POV: This combo had potential` @0.999 |
| onnxruntime | 1.30.0 | OK | providers: CPU (`AzureExecutionProvider`, `CPUExecutionProvider` typical) |
| pyJianYingDraft | 0.3.0 | OK | import only (draft writing is R3/R4 scope) |
| requests | 2.34.2 | OK | |
| also present | av 18.1.0, scipy 1.18.1, scikit-learn 1.9.1, numba 0.67.0, pymediainfo 7.0.1, huggingface_hub 1.31.0, tokenizers 0.23.2, httpx 0.28.1, PyYAML 6.0.3, tqdm 4.70.1, uiautomation 2.0.29, comtypes 1.4.16 | | |

Notes: `opencv-python` and `opencv-python-headless` are both installed (same version) — works now, but two providers of `cv2` can break on upgrade; keep only headless (low priority). `HF_HUB_DISABLE_SYMLINKS_WARNING=1` silences the HF warning.

## D. Node / Git / CapCut / HyperFrames

* Node v24.21.0, npm 11.19.0 (`C:\Program Files\nodejs\`); global npm packages: only `@anthropic-ai/claude-code@2.1.273`.
* Git 2.55.0.windows.3.
* CapCut 9.4.0.4015 present. Draft store `C:\Users\Bulzart\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\`: index `root_meta_info.json` (`all_draft_store[]` with `draft_id`, `draft_fold_path`, `draft_json_file`, `tm_draft_create/modified` µs epoch, `tm_duration` µs); draft `0915\draft_content.json` (12,657 B plaintext JSON): top-level keys `id, version (360000), new_version ("185.0.0"), name, duration (5133333 µs), fps (30.0), canvas_config {ratio:"original", width:1920, height:1014}, tracks [video(1 segment), effect(1)], materials, keyframes, config, platform, …`; sibling files `draft_meta_info.json`, `draft_cover.jpg`, `draft_virtual_store.json`, `key_value.json`, `timeline_layout.json`, `template-2.tmp`, dirs `Resources\ subdraft\ Timelines\ matting\ smart_crop\ adjust_mask\ qr_upload\ common_attachment\`. A copy of this draft (JSON files only) already sits in `research\capcut-draft-sample\`.
* HyperFrames local skills (`C:\Users\Bulzart\.claude\skills\`): `hyperframes` (entry/router), `hyperframes-core` (composition contract: `data-start/duration/media-start`, tracks/clips), `hyperframes-animation` (blueprints, transitions registry), `hyperframes-audio` (carve/duck/fx), `hyperframes-cli`, `hyperframes-creative` (frame presets, palettes, typography, beat direction), `hyperframes-keyframes`, `hyperframes-registry`; workflow skills `embedded-captions`, `talking-head-recut`, `general-video`, `music-to-video`, `motion-graphics`, `faceless-explainer`, `product-launch-video`, `pr-to-video`, `slideshow`, `remotion-to-hyperframes`, `figma`, `media-use` (media OS: resolve bgm/sfx/image/icon/logo/voice/grade/lut; `transcribe` defaults to Parakeet with whisper.cpp fallback, word-level).
* `hyperframes-cli` offers (run as `npx hyperframes …`): `init, add, catalog, capture, lint, check (--snapshots, --strict), snapshot --at, compare, grade-compare, preview (--background/--port/--context --json), play, present, beats, keyframes, render (--quality draft|looks|delivery, --batch rows.json, --docker), publish, cloud render, cloudrun, lambda, doctor (--json), browser ensure|path|clear, info, upgrade, skills update <workflow>, compositions, docs, benchmark, telemetry, transcribe, tts, remove-background, media-treatment, figma, feedback`. **Render dependencies**: Node ≥ 22 (OK), FFmpeg/FFprobe (OK), a pinned bundled Chrome (`npx hyperframes browser ensure` downloads it), optional Docker for `--docker`; `transcribe`/`tts` download their own models on first run; cloud render needs HeyGen auth. Studio preview = `http://localhost:<port>/#project/<name>`.
* HyperFrames MCP (`mcp__claude_ai_HyperFrames_by_HeyGen__*`): from Claude Code only `list_projects, get_project, get_project_status, get_render_status` work; `compose`/`render_video` are rejected for CLI clients.

## E. MCP tools reachable from this session for analysis (schemas loaded via ToolSearch; no paid calls made)

### Higgsfield (`mcp__claude_ai_Higssfield__*`) — balance checked: **1379.06 credits, plan `ultra`**; `video_analysis_jobs` → 0 past analyses
* `media_upload` `{filename, content_type?}` or `{files:[{filename,content_type}]}` (1–20, `method:"upload_url"`) → presigned `upload_url` + `media_id`; PUT the bytes yourself (`Invoke-WebRequest -Method Put -InFile <mp4> -ContentType video/mp4 -Uri <upload_url>`), then `media_confirm {type:"video", media_id}` (or `media_ids[]`). `media_upload_widget` is only for Apps-UI clients (not Claude Code). `media_import_url {url, type:"auto|video|…"}` imports an HTTPS media URL ≤ 50 MB → confirmed `media_id`.
* `video_analysis_create` — exactly one of `video_input_id` (confirmed media UUID) or `youtube_url` (youtube.com/youtu.be only). Returns `status:"queued"`; typical 3–5 min; **accuracy degrades with length → send ≤30 s segments** (miko's rule). Poll `video_analysis_status {video_analyze_id}` every 30–60 s until `status:"completed"` (`scenes` populated) or `failed` (`fail_reason`). Output field names beyond `scenes[]` are not documented in the schema — unverified (no run was made; cost unknown).
* `virality_predictor {action:"create", params:{model:"virality_predictor", medias:[{role:"video", id:<media_id or completed generation job_id>}]}}` → interactive dashboard (virality potential, engagement, attention, hook strength, retention risk); `action:"preview"` with `params.job_id` re-opens it. Cost unknown.
* Others for later stages: `tiktok_music_trending {connector_id (from tiktok_accounts), country_code, date_range 1DAY|7DAY|30DAY|90DAY, genre, limit}` (read-only trending commercial tracks), `models_explore`, `generate_video`, `upscale_video`, `shorts_studio_*`.

### ElevenLabs (`mcp__claude_ai_ElevenLabs__*`)
* Local file upload: `creative_create_asset_upload {name, mime_type, file_size (exact bytes), context}` → `upload_url` + `asset_id`; single HTTP PUT with **Content-Type exactly `mime_type`** (e.g. `Invoke-WebRequest -Method Put -InFile audio16k.wav -ContentType audio/wav -Uri <upload_url>`); then `creative_finalize_asset_upload {asset_id, flow_id?, context}` → `node_id`. (Create the flow first with `creative_create_flow` when several steps must share it.) For a public HTTPS file use `creative_attach_reference_file {url, flow_id}` instead.
* `creative_transcribe_audio {model_id:"eleven_scribe_v1", connect_from:[node_id], flow_id, context, estimate_only?}` → `flow_id, node_id, session_ids, url`; poll `creative_get_flow_run_status {flow_id, session_ids, context}` until `all_completed`; transcript in `transcripts`. `estimate_only:true` returns the cost first. Charged per call — never retry blindly. Whether the MCP result includes word-level timestamps is **unverified** (Scribe v1 supports them in the API).

### Adobe (`mcp__claude_ai_Adobe_for_creativity__*`) — call `adobe_mandatory_init` before every Adobe tool
* Upload: `asset_initialize_file_upload {path:"analyze-stack/<file>.mp4", file_size, media_type:"video/mp4", block_size?}` → block upload URLs; PUT chunks; `asset_finalize_file_upload {filename, transfer_document}` → asset (Walnut `assetId`). `asset_add_file` opens a picker (UI clients only).
* `video_metadata {assetId}` → width, height, fps, duration.
* `media_summarize {assetId}` → text summary of spoken content only ("only suitable for content with significant dialogue"); no timestamps → low value for measurement, useful as a third-opinion narrative summary.
* `video_create_quick_cut {assetIds[], user_prompt, target_duration}` → AI highlight reel by visual engagement (not speech-aware). Post-gen only.

### Descript (`mcp__claude_ai_Descript__*`)
* `import_media {project_name, add_media:{"clip.mp4":{content_type:"video/mp4", file_size:<bytes>, language:"en"}}, add_compositions:[{name, clips:[{media:"clip.mp4"}], width:1080, height:1920, fps:30}]}` → `job_id, project_id, project_url, upload_urls{key→{upload_url, asset_id}}`; PUT file with `Content-Type: application/octet-stream`; `wait_for_job {job_id}` (up to 840 s per call). Transcription happens automatically on import.
* `export_transcript {project_id, format:"srt"|"txt"|"markdown"|"html"|"rtf", include_speaker_labels:"changes", timecodes:{on_paragraphs:true, frequency_seconds:5}}` → content inline. Speaker labels yes; word-level JSON no (SRT blocks only).
* `export_timeline` (EDL/AAF/SESX/FCPXML/Premiere XML/Resolve XML) and `prompt_project_agent` (Underlord edits, model selectable) are post-gen tools.

## F. Part C — tool discovery per capability (what it gives, cost, install status, exact call)

| Capability | Tool (status) | What it gives | Cost | Exact command / call |
|---|---|---|---|---|
| Link download | **yt-dlp 2026.08.19** (installed; YouTube metadata verified; TikTok/Instagram not tested this session) | mp4 + JSON metadata (title, uploader, duration, upload date, view/like counts when exposed) | free | `yt-dlp -f "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b" --merge-output-format mp4 --write-info-json -o "runs\<run-id>\00-input\source.%(ext)s" "<url>"` — add `--cookies-from-browser chrome` if a platform demands login; `--ffmpeg-location <ffmpeg bin dir>` if PATH is stale |
| Scene cuts | **ffmpeg `select(scene)`** + **`scdet`** + **PySceneDetect 0.7.1** (all installed) | timestamps + scores; PySceneDetect adds `min_scene_len`, HSV-based ContentDetector (fast cuts), AdaptiveDetector (robust to camera motion), HashDetector/HistogramDetector, ThresholdDetector (fades) | free; 27 s clip: ffmpeg <1 s, Content 5.3 s, Adaptive 2.3 s | see `miko-analysis.md` §4.3; Python: `from scenedetect import open_video, SceneManager, ContentDetector, AdaptiveDetector` → `sm.detect_scenes(open_video(path)); sm.get_scene_list()`; defaults `ContentDetector(threshold=27.0, min_scene_len=15, weights=(hue 1, sat 1, lum 1, edges 0))`, `AdaptiveDetector(adaptive_threshold=3.0, window_width=2, min_content_val=15.0)`. Recommendation: union of the three + 3-frame merge + agreement count |
| Keyframes / contact sheets | **ffmpeg** (`fps`, `select`, `thumbnail`, `tile`, `drawtext`) | 1 fps keyframes, shot-start frames, shot-midpoint frames, labelled 4x4 sheets | free, seconds | `miko-analysis.md` §4.4–4.5 |
| Transcription + word timestamps | **faster-whisper 1.2.1** (installed; `tiny` cached; `base`/`small` download on first use ~150/480 MB) | segments + words `{word,start,end,probability}`, language id, VAD | free; CPU int8 ≈ 5x realtime with `tiny`, expect ≈1–2x with `small` | `WhisperModel("small", device="cpu", compute_type="int8").transcribe(path, language="en", word_timestamps=True, vad_filter=True, vad_parameters={"min_silence_duration_ms":500}, beam_size=5)` (script: `r1-test\r1_whisper.py`) |
| Transcription fallback 1 | **ffmpeg `whisper` filter** (built in; `ggml-tiny.en.bin` downloaded; `ggml-base.en.bin` ~148 MB optional) | SRT/JSON/text segments (no word timestamps) without Python | free; 40 s in 11.5 s (tiny.en, CPU) | `ffmpeg -i audio16k.wav -af "whisper=model='C\:/Users/Bulzart/.cache/whisper-cpp/ggml-tiny.en.bin':language=en:queue=10:use_gpu=false:format=srt:destination=out.srt" -f null -` |
| Transcription fallback 2 | **ElevenLabs Scribe v1** via MCP (reachable; untested) | cloud ASR, likely word timestamps (unverified in MCP output) | paid per call (`estimate_only:true` first) | upload → finalize → `creative_transcribe_audio` → poll (§E) |
| Transcription fallback 3 | **Descript** via MCP (reachable; untested) | auto transcript with speaker labels; SRT/TXT export; also an NLE-grade timeline export | Descript plan | `import_media` (direct upload) → `wait_for_job` → `export_transcript format:"srt"` (§E) |
| On-screen text OCR | **RapidOCR 1.4.4 (onnxruntime CPU)** (installed, verified) | text + 4-point boxes + confidence per frame; caption in/out times from consecutive keyframes | free; ~1 s init, <0.3 s/frame | `from rapidocr_onnxruntime import RapidOCR; r, _ = RapidOCR()(frame_bgr)` → `[box, text, score]` (script `r1-test\r1_ocr.py`); newer package name `rapidocr` exists but is not needed |
| Audio features | **librosa 1.0.0** (installed, verified) + **ffmpeg `ebur128`/`silencedetect`/`astats`** | BPM (`beat_track`), beat times, onsets, RMS/s, spectral centroid; integrated LUFS/LRA/true-peak; silence intervals | free; librosa first call 40 s (JIT), then fast; ffmpeg <1 s | `r1-test\r1_audio.py` (librosa) / `r1_audio_basic.py` (numpy fallback: RMS, silence, spectral-flux onsets, autocorrelation tempo — matched librosa's 99.4 BPM) + `miko-analysis.md` §4.7 |
| Colour palette | **OpenCV `cv2.kmeans`** (installed, verified) | k=5 dominant colours + shares over 1 frame/s | free, <1 s | in `r1-test\r1_motion.py` (`palette_k5`) |
| Camera-motion classification | **OpenCV Farneback + `estimateAffinePartial2D` + `phaseCorrelate`** (installed, verified) | per-second label static/pan-L/R/tilt-U/D/zoom-in/out/handheld/subject-motion + mean flow, residual, inlier fraction | free; 21 s per 27 s clip at 10 pairs/s @320 px | `r1-test\r1_motion.py <video> <out.json>`; **thresholds uncalibrated** (tested only on a handheld POV clip) — calibrate on a tripod/gimbal reference before trusting labels; the raw metrics are reliable |
| Style-detection cues | **OpenCV** (edge density via Canny, HSV saturation/value means, frame-diff mean) + **ffmpeg `siti`** (SI/TI) + `signalstats` | numeric cues per second feeding the analyst agent (contrast, busyness, motion pacing, colourfulness) | free; siti is slow (0.47x realtime) — optional | in `r1_motion.py` (`edge_density`, `sat`, `val`, `frame_diff`); `ffmpeg -i in.mp4 -vf "siti=print_summary=1" -an -f null -` (stderr) |
| Second-opinion analysis | **Higgsfield `video_analysis_create/status`** (reachable; not run) | scene-by-scene description incl. actions, dialogue, delivery, sound | Higgsfield credits (amount unknown; 1379 available) | `media_upload` → PUT → `media_confirm` → `video_analysis_create {video_input_id}` → poll `video_analysis_status` (≤30 s segments) |
| Virality signal | **Higgsfield `virality_predictor`** (reachable; not run) | hook strength, retention risk, engagement dashboard | credits (unknown) | `{action:"create", params:{model:"virality_predictor", medias:[{role:"video", id:<media_id>}]}}` |
| Spoken-content summary | **Adobe `media_summarize`** (reachable; not run) | narrative summary (no timestamps) | Adobe plan | `adobe_mandatory_init` → upload → `media_summarize {assetId}` |

## G. Install plan (only what is missing; every item needs main-session approval)

| # | Item | Command | Priority | Reason |
|---|---|---|---|---|
| 1 | HyperFrames CLI (global) + pinned Chrome | `npm install -g hyperframes` then `npx hyperframes doctor --json` and `npx hyperframes browser ensure` | medium (post-gen only; skip if CapCut/OTIO route is chosen) | local skills are installed but every `npx hyperframes …` command currently aborts ("missing packages and no YES option"); render needs the bundled Chrome download |
| 2 | faster-whisper production model | `python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"` (downloads ≈480 MB to `~\.cache\huggingface\hub`; use `'base'` ≈150 MB if disk/time matters) | high | `tiny` mis-hears brand names; only `tiny` is cached now |
| 3 | whisper.cpp base model for the ffmpeg fallback (optional) | `Invoke-WebRequest -Uri https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin -OutFile C:\Users\Bulzart\.cache\whisper-cpp\ggml-base.en.bin` | low | better fallback quality than tiny.en (148 MB) |
| 4 | Remove the duplicate OpenCV wheel (optional hygiene) | `python -m pip uninstall -y opencv-python` | low | two providers of `cv2`; keep `opencv-python-headless` |
| ~~5~~ | ~~MSVC C++ 2022 x64 runtime~~ | ~~`winget install --id Microsoft.VCRedist.2015+.x64 -e`~~ | done | installed 2026-09-16 during the session (14.51.36247); no action |

No pip packages from LAYOUT are missing.

## H. Uncertainties / not verified
* Higgsfield `video_analysis` and `virality_predictor` were not executed: cost per call and the exact result JSON (beyond `status`, `scenes`, `fail_reason`) are unknown.
* ElevenLabs Scribe word-level timestamps through the MCP result (`transcripts`) — unverified; Descript and Adobe upload flows — schema-documented only, not exercised.
* Camera-motion labels need calibration; only handheld footage was tested.
* yt-dlp was verified against YouTube only; TikTok/Instagram/Facebook extraction may need cookies and changes often.
* librosa 1.0.0 first-call JIT cost (40 s) will recur whenever the numba cache is cold; the numpy fallback script covers RMS/silence/onsets/tempo if speed matters.
* ffmpeg `siti` runs at ~0.47x realtime — fine for ≤60 s references, too slow for long ones.
