---
name: create-video-gpu-whisper
description: "user 2026-11-21: /create-video's Whisper medium MUST run on the GPU (cuda float16); no silent CPU fallback; CPU only with --cpu-approved \"<user's words>\"; the script finds the pip CUDA runtime itself"
metadata:
  node_type: memory
  type: project
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T23:04:39.003Z
---

User 2026-11-21 (brief "2 FPS Analysis, Content Restrictions, and GPU Whisper Integration", Part 5): Whisper medium must use the GPU in the real /create-video path; never fall back to the CPU silently; never switch to CPU to make a test pass; don't reinstall or upgrade the CUDA setup another agent made.

**The environment (checked 2026-11-21):**
- `/create-video` runs `python` = `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe`, the same in Git Bash, PowerShell and a fresh terminal.
- Packages: faster-whisper 1.2.1, ctranslate2 4.8.5 (CUDA build: float16, int8_float16 and so on), nvidia-cublas-cu12 12.9.2.10, nvidia-cudnn-cu12 9.28.1.4, nvidia-cuda-nvrtc-cu12 12.9.86.
- DLL folders: `Lib\site-packages\nvidia\{cublas,cudnn,cuda_nvrtc}\bin`, all three on the user PATH (HKCU).
- GPU: RTX 3060 12 GB, driver 610.88.
- Weights: `Systran/faster-whisper-medium` in the HF cache.
- Before this change, static_core defaulted to CPU int8: when the CUDA runtime was missing, cublas64_12.dll failed to load.

**What static_core does now:**
- Every Whisper command (`add_whisper_args`) defaults to `--device cuda`, float16, with `--whisper-model` restricted to `medium`.
- `whisper_settings()` runs in main() before any work. `--device cpu` is refused unless `--cpu-approved "<what the user said>"`, which is then recorded in the transcript's engine facts.
- `whisper_model()` loads the model once per process. It then:
  - calls `cuda_runtime_setup()`, which puts the pip NVIDIA bin folders first on THIS process's PATH and in `os.add_dll_directory`. It never touches the user's PATH, so it also works from an agent session that started before the PATH change;
  - checks `ctranslate2.get_cuda_device_count()`;
  - runs 1 s of silence through the model, so a missing DLL fails there, by name;
  - reads the device from the engine (`model.model.device`), not from the request.
- `transcript.json` gets `engine` (device, compute_type, gpu, versions, python), `elapsed_s` and `realtime_x`.
- `doctor --whisper [--file F]` is the smoke test.
- The transcript cache key leaves the device out, so older CPU transcripts stay valid and are never re-heard.

**Verified 2026-11-21:**
- `doctor --whisper` worked from this session's stale-PATH process and from a fresh-terminal PATH (registry Machine + User).
- Windows SAPI speech: all 17 words exact; engine reported cuda, float16, RTX 3060.
- Tests (in test_static_core.py `WhisperGpuTests`):
  - with `CUDA_VISIBLE_DEVICES=-1`, both doctor and prepare stop with "sees no CUDA device", and no transcript is written;
  - `--whisper-model small` is refused by argparse.

**How to apply:**
- Never set the device to auto or CPU in /create-video code or docs.
- If the GPU fails, report the error's cause; don't reinstall anything without establishing the cause and getting the user's yes.
- Other pipelines are not covered by this rule (each has its own); don't change them from a create-video session ([[one-pipeline-per-session]]).

Related: [[whisper-strictly-medium]], [[pc-pipeline-tooling]], [[create-video-command]].
