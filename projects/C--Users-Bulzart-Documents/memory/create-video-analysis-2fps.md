---
name: create-video-analysis-2fps
description: "user 2026-11-21: /create-video reference analysis samples 2 fps (supersedes 1 fps and 5 fps), each frame at its own source timestamp; a run keeps its rate; inspect-window for brief stretches; output fps untouched"
metadata:
  node_type: memory
  type: project
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T23:04:52.254Z
---

**History:** user 2026-11-20 asked for 1 fps instead of 5 fps. That work was done (rate-aware thresholds) but never reported as finished. On 2026-11-21 the brief "2 FPS Analysis..." superseded it: "2 frames per second ... supersedes previous preferences for 1 FPS and 5 FPS". It applies only to reference analysis: generated footage, the CapCut timeline, exports (30 fps), narration and audio are unchanged.

**What static_core and av_tools do:**
- **Defaults:**
  - `ANALYSIS_FPS = 2.0`, `ANALYSIS_SAMPLER = 'pts-v1'`.
  - A run records `analysis_fps` and `analysis_sampler` in state.json at init, and keeps them.
  - A run without them (made before) stays at 5 fps with nominal slots, so the existing run `20261119-045532-youtube` keeps its 6.7 GB of frames and its profiles.
  - `prepare --fps X` that differs from the run is refused ("clone the run").
  - A clone re-prepares at the current rate. It copies cards, content reviews and closer-look index.json files, never frames.
- **Sampling** (`av_tools.sample_frames`):
  - ffmpeg `select` takes the first real frame of each 0.5 s slot, with `-copyts` and `showinfo`.
  - Each frame keeps its own timestamp: `t_s` = pts minus the audio stream's start (`clock_origin`, the transcript's clock), plus `pts_s` and `slot_s`.
  - So VFR, start offsets and dropped frames never shift later frames.
  - `frame-index.json` has `mode: source_pts`; `approx_s` repeats `t_s` for older readers.
  - Tested: VFR 10/24/7 fps with the video 0.37 s after the audio. Every sample's colour and time were exact.
- **Caches:**
  - Separate keys for frames (`frames_signature`: fingerprint, fps, width, sampler) and the transcript (`transcript_signature`: fingerprint, model).
  - New frames never re-run Whisper.
  - An older single-key manifest's nominal frames are re-made in a 2 fps run, but reused in a legacy run.
  - `--full-fps` has its own key and `all-frames-index.json`.
- **Picture method** (`METHOD_VERSION av-profile-3`):
  - Thresholds are in seconds: `transition_pairs` = 1.6 s / interval (3 at 2 fps).
  - `motion_diff` = 0.6 × (interval/0.2)^0.75, i.e. 1.19 at 2 fps. Calibrated on seven moving references: about 86% agreement with the 5 fps reading.
  - A quick cut series is counted as cuts.
  - Profiles carry `sampled_fps`, `sampler`, `inspect_candidates` (flashes, cut series, transitions, short shots) and `sheet_tiles` (each watch-sheet tile's step and the frame time it shows).
  - Watch-sheet tiles label the frame's own time.
- **`inspect-window --run --ref V### | --file F --from --to [--fps 10 | --native] [--why] [--remove]`:**
  - Writes `20-analysis/inspect/<label>/<a>-<b>@<rate>/` (frames, sheet.jpg, index.json with the words said).
  - At most 400 frames, so it is for a brief stretch only.
  - `--remove` deletes the frames and keeps index.json as the record.

**Real data:** the 1 fps vs 5 fps comparison of 2026-11-20 is in the session transcript only. The 2 fps motion calibration used frames 0.4 and 0.6 s apart (best thresholds 1.2 and 1.4; the formula gives 1.01 and 1.37).

Related: [[create-video-command]], [[create-video-content-review]], [[create-video-gpu-whisper]].
