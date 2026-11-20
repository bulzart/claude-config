---
name: create-clips-spoken-language
description: "user 2026-11-14: streams may be German or Spanish, not only English; whisper.language was forced to en, now auto (per-chunk detection, unsure guess falls back to en, first sure detection on a stream chunk locked per run); transcribe never translate"
metadata:
  node_type: memory
  type: project
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T19:13:52.733Z
---

User 2026-11-14: "is the whisper processor supposed to know which language is the audio ... not always all of the streams we will process will be in english, some will be in german or spanish too"; then "as far as i know whisper medium can translate german and espanol too".

**Facts found:** the model is `medium` (multilingual, `Systran/faster-whisper-medium`), so German and Spanish are fine. The problem was `config.json -> whisper.language: "en"`: every chunk was decoded as English whatever was spoken (a forced English decode of foreign speech gives an unreliable half-translation: dropped or invented words, bad word timing; I did not test it on a real German clip, none exists on this PC and only English TTS voices are installed).

**What was built (2026-11-14):** `whisper.language` = `auto`, `fallback_language` en, `detect_min_probability` 0.85, `detect_min_words` 40. `cc_audio.Transcriber.transcribe(..., language=None)`: auto = Whisper names the language first; an unsure guess (< 0.85) is not trusted and the chunk is decoded in the fallback language (the guess is kept as `detected_language`); `transcript.json` has `language_source` = detected | fallback | forced. `cc_proc.lock_language`: the first SURE detection (>= 0.85, >= 40 words) on a STREAM chunk is locked in `state.json -> settings.whisper.language_locked` (+ `settings.whisper.language`, `language_locked_from`) and `stream_language` tells it to the later chunks; an AD chunk never locks and never uses it (an ad is in its own language); a language the user set (run override `T new-run --language de` or `T state set settings.whisper_override.language=de`, or a config language) is never replaced. `T status` has `language`; `stream.md` has a `Spoken language` line; `cc_edit.whisper_language` reads the lock, else the most reported chunk language. New `reference/language.md` + pointers (cc-start facts and research contract, both scan skills, safety.md masks, clip-economy posting text, README, docs/processing.md); tests `tests/test_language.py` (stand-in model) and test_docs.

**Agent rules for a non-English stream:** read transcripts as spoken; notes, briefs and reports in English; research the streamer's world in that language too; ADD that language's profanity/slurs to `captions.mask_terms` (the user's `caption-masks.json` is English); posting title/description/hashtags in the stream's language unless the user's notes say otherwise (my default, to be confirmed by the user); the task stays TRANSCRIBE, never Whisper's translate-to-English (captions need the spoken words and exact timing). Open: whether the user also wants an English translation transcript for reading (a second decode pass, about double the Whisper time).

**Verified on real audio (2026-11-14, medium on CPU, the user's own downloads copied to a temp inbox, originals untouched):** a German train-conversation lesson: detected de, probability 0.994, 149 words; a Spanish humour short: es 0.996, 71 words; both locked the run's language; forcing English on the same audio gave a half-translation that mixes the languages (the old behaviour); Whisper's translate task gives consistent English but is not used for captions. The model is medium and ONLY medium: [[whisper-strictly-medium]].

Related: [[create-clips-pipeline]], [[create-clips-caption-masks]], [[scripts-gather-agents-decide]], [[pc-pipeline-tooling]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: streams may be German/Spanish; whisper.language was forced en, now auto (unsure -> en fallback, first sure detection on a stream chunk locked per run, ads never lock); transcribe never translate; agents add that language's profanity to mask_terms

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: German/Spanish streams; whisper.language auto, first sure detection locked per run, ads never lock; transcribe never translate
