---
name: whisper-strictly-medium
description: "user 2026-11-14: Whisper medium for ALL audio processing, strictly, in every pipeline; no smaller model as a default, a fallback or a speed-up suggestion; a medium that cannot load is an error"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T20:06:09.505Z
---

User 2026-11-14: "btw we use whisper medium for all our audio processing right, not whisper small? because we should strictly always use medium model for anything". Earlier, 2026-11-11, for AWL/Static: "always medium for narration checks, extracting and analysing no matter the language".

**What I found and changed (2026-11-14):** /analyze-then-pick and /analyze-then-generate were still on `small` (config `whisper_model`, script defaults), the old analyze-stack tools (`transcribe.py`, `measure_all.py`) defaulted to `small`, and several scripts silently fell back to small/base/tiny when medium could not load (faster-whisper loop, and the whisper.cpp filter looked for `ggml-base.en.bin` / `ggml-tiny.en.bin`). Now: every default is `medium`; the fallback loops try ONLY the model asked for (create-clips `cc_audio.Transcriber`, atp.py, atg.py, awl.py, cs.py, analyze-stack transcribe.py); the whisper.cpp fallback reads `ggml-medium.bin` only; a medium that cannot load raises an error that says "there is no fallback to a smaller model"; the docs no longer suggest `--whisper-model base` to speed a run up. Test in `create-clips/tests/test_language.py` (a model that cannot load: only "medium" is tried).

**Why:** medium hears what small does not: on the same 11.8 s German clip small wrote "Alleranfang" (4.4 s), medium got all 22 words (13.1 s); small/tiny mis-hear brand names and foreign speech, and a silent downgrade hides it from the run's record.

**How to apply:**
- New script, tool or doc that transcribes: default `medium`, no smaller fallback, no "use base/small if it is slow" advice. If medium will not load, stop and report the real error (cache, memory), never another size or engine (same spirit as [[awl-memory-is-a-fact]]).
- Costs the user accepted by saying "strictly": about 0.7 s of work per second of audio (3x small), a hard failure when the medium model is not cached.
- Left on purpose (tell the user, ask): the CLI flags `--whisper-model` / `--model` still accept another name if someone types it; `CC_WHISPER_MODEL` (create-clips) exists for the tests, whose fast suite runs a tiny stand-in so it finishes in minutes; historical research notes (`analyze-stack/research`, learning logs) still describe the old small/base/tiny.

**In the commands (2026-11-14, "update createstatic and createclips commands to be in sync"):** /create-static item 24 (+ a Never line, `cs-start`, `cs-prepare`, `pipeline/preprocessing.md`, static §6 and §9, `config.json` whisper_model_note; the dead `model_fallback` code is gone from cs.py and awl.py) and /create-clips router rule 15 (+ the Never line, README, `docs/processing.md`, `tests/test_docs.py`). Both routers also carry the to-do rule now, see [[task-lists-and-todo-files]]. The user said no Loupe checks are needed (Static mode does not use Loupe): the AWL suite's t01/t02/t03/t05 failures seen the same day (a missing judge doc, a TTS stand-in timeout, Loupe start, hook capture) were not investigated.

Related: [[pc-pipeline-tooling]], [[create-clips-spoken-language]], [[atp-audio-ingest-question]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: medium for ALL audio processing in every pipeline; no smaller default, fallback or speed-up advice; a medium that cannot load is an error (ATP/ATG were on small until today); now in /create-static item 24 and /create-clips rule 15
