---
name: create-clips-gpu-whisper
description: "user 2026-11-21: the recorder's processing (cc.py watch) uses Whisper medium on the GPU too; automatic CPU fallback per chunk"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T00:41:31.572Z
---

The user, 2026-11-21: "the twitch chunk recorder chrome extension processing the audio should use whisper medium on gpu too".
/create-clips config `whisper.device` = `cuda`, `cuda_compute_type` float16 (int8 stays the CPU fallback's), `gpu_retry_s` 600. A GPU error while
transcribing moves that chunk to the CPU, retries the GPU later, and the transcript records `device_fallback`.

**Why:** measured on the RTX 3060: 9.0 s + 4.2 s load per 3-minute chunk vs 131.6 s int8 CPU, same 281 words, drift <= 0.32 s. The caseoh run spent
204.9 min of CPU on transcripts (236 chunks, mean 52 s).

**How to apply:** still `medium` only ([[whisper-strictly-medium]]). The watcher picks the setting up at its next start. The GPU is shared with
FLUX Klein / ACE-Step ([[local-ai-installs]]): Whisper holds about 2 GB VRAM while loaded (unloads after 600 s idle).
