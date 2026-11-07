---
name: awl-tts-normal-model-only
description: "user 2026-11-07: never use the lighter Qwen3-TTS engine (AWL_TTS_ENGINE=qwen-tts, the official engine without CUDA graphs) in the future; always the normal model (faster-qwen3-tts), even when the memory looks short"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-07T18:03:09.742Z
---

User 2026-11-07, after I built the run's new voice (sample 2) with `AWL_TTS_ENGINE=qwen-tts` because free commit memory (13.9 GB) looked short of the normal model's measured 12.68 GB peak plus the memory guard's 3 GB floor: "we've already generated prior voices such as the first one used in the video02 with the same memory we have now btw, and possibly without even using a lighter qwen3 tts but the normal model"; "also do not try to use the lighter model in the future".

**Why:** the normal model ran this PC's narrations at about the same free memory (the morning narration of video 02; the evening one, 107 lines in 322 s at 13.9 GB free); my "peak + floor" margin was stricter than the PC needs. The one real failure (17:15) had only 12.6 GB free with WPS Office, Chrome, Teams and Media Player open.

**How to apply:** never set `AWL_TTS_ENGINE` to qwen-tts / official for `T tts voice` or `T tts say`; run the normal model, and if the memory guard really stops it, report the guard's line and ask the user to close programs. The same holds for treating `T image fit`'s headroom as a hard gate: it is a fact, the job is tried. Related: [[analyze-with-loupe-command]], [[local-ai-installs]].
