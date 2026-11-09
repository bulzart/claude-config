---
name: awl-memory-is-a-fact
description: "user 2026-11-07/08: a local model's memory headroom (ACE-Step, FLUX 3 Klein) is a fact, never a gate: the job is tried; after a real guard stop report the guard's line and ask the user to close programs; never a lighter engine instead"
metadata:
  type: feedback
---

User 2026-11-07, after I built the run's new voice (sample 2) with `AWL_TTS_ENGINE=qwen-tts` because free commit memory (13.9 GB) looked short of the normal model's measured 12.68 GB peak plus the memory guard's 3 GB floor: "we've already generated prior voices such as the first one used in the video02 with the same memory we have now btw, and possibly without even using a lighter qwen3 tts but the normal model"; "also do not try to use the lighter model in the future".

**Why:** the normal model ran this PC's narrations at about the same free memory (the morning narration of video 02; the evening one, 107 lines in 322 s at 13.9 GB free); my "peak + floor" margin was stricter than the PC needs. The one real failure (17:15) had only 12.6 GB free with WPS Office, Chrome, Teams and Media Player open.

**How to apply:** never set `AWL_TTS_ENGINE` to qwen-tts / official for `T tts voice` or `T tts say`; run the normal model, and if the memory guard really stops it, report the guard's line and ask the user to close programs. The same holds for treating `T image fit`'s headroom as a hard gate: it is a fact, the job is tried. Same for the ACE-Step bed and for the judge's forecasts (static §13 "Memory is a fact", 2026-11-08): never tell an agent "a negative headroom means you wait" (I did in video 03's stretch-3 spawn message); after a real stop wait for >= 1 GB more free commit than the stopped start. 2026-11-08 the bed really was stopped: 15.4 GB free, ACE-Step 13.07 GB, guard at 2.3 GB. Related: [[analyze-with-loupe-command]], [[local-ai-installs]].

**2026-11-09:** the TTS part above is history (Qwen3-TTS uninstalled, the narration is ElevenLabs: [[awl-elevenlabs-v4-no-edit]]); the rule stands for ACE-Step and FLUX 3 Klein.
