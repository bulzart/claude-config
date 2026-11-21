---
name: create-clips-gpu-whisper
description: "user 2026-11-21: the recorder's processing uses Whisper medium on the GPU; the watcher shares the GPU (keep while recording, yield)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T01:48:11.781Z
---

The user, 2026-11-21: "the twitch chunk recorder chrome extension processing the audio should use whisper medium on gpu too", then: share the GPU
smartly, no needless reloads (a chunk every ~3 min), free it when not needed, never fight over memory, time to finished videos over GPU percentages.
Config `whisper.device` cuda, float16; CPU int8 fallback per chunk (`device_fallback` recorded).

**Why:** measured on the RTX 3060: a 3-min chunk in 7-9 s vs ~130 s on the CPU; Whisper holds ~2.0 GB when loaded, unload frees all but ~110 MB
(CUDA context), reload 2.0 s in-process (5.1 s cold).

**How to apply:** the watcher (cc_proc `_whisper_unload_reason`) keeps Whisper while a recording runs (session.json without `ended_at`, changed in the
last 10 min), lets it go 120 s after the recording stopped, when a GPU lease (`cc.py gpu`, data/gpu/lease-*.json) needs more than is free, or when free
VRAM < 700 MB; a load waits 30 s for 2.2 GB free, else CPU. Music separation takes a lease and waits for `capcut-export`. Still `medium` only
([[whisper-strictly-medium]]); the GPU is shared with FLUX Klein / ACE-Step ([[local-ai-installs]]), which do not take leases (a lease from them
would be their pipeline's change).
