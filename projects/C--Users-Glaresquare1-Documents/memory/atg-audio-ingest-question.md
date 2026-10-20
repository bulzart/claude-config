---
name: atg-audio-ingest-question
description: "/analyze-then-generate must ask the user once at the start whether the videos' audio is ingested by Whisper speech-to-text or only the image frames are processed; requested 2026-10-20, spec in the Fable prompt item 10, not yet implemented"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T00:38:06.087Z
---

The user asked (2026-10-20): the whole /analyze-then-generate pipeline has to ask the user whether they want the videos' audio to be ingested by audio/voice-to-text with Whisper, or not (then only the video image frames are processed).

**Why:** speech-to-text costs time and shapes what the analysis cards say about hooks, speech and sync; the user wants to choose per run instead of the pipeline deciding. For /analyze-then-generate only; whether /analyze-then-pick gets the same question is the user's call.

**How to apply:** the spec (understand-first audit of where audio becomes text, one state.json key following the QC-fixes precedent [[atg-qc-fixes-option]], no silent default, "audio not ingested" is never written as "no speech", the audio file itself stays usable for restoring the original audio, the wider reading of "frames only" put to the user) is item 10 of `Documents/prompts/pipeline-coupling-fable.txt`. It is not built yet: when it is, the start skill asks it with AskUserQuestion, docs and build prompt follow [[atp-build-prompt-sync]] style rules, and this note should be updated to say it is done. Related: [[atg-skills-architecture]], [[scripts-gather-agents-decide]].
