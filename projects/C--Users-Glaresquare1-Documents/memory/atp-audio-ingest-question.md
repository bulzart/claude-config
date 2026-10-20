---
name: atp-audio-ingest-question
description: "/analyze-then-pick must offer optional Whisper speech-to-text ingestion of the videos' audio throughout all its features; the user chooses at the start whether audio is processed or only frames; requested 2026-10-20, spec in the Fable prompt item 10, not yet implemented"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T01:49:33.815Z
---

The user asked (2026-10-20, first for the other pipeline, then moved): /analyze-then-pick should implement audio-to-text ingestion with Whisper throughout all its features, and it must be optional: the user chooses at the start whether the videos' audio is processed or only the video image frames. (They wrote "audio to text ttl whisper": read as speech-to-text; the Fable prompt asks the agent to stop and report if the evidence points to another meaning.) The other pipeline, /analyze-then-generate, is NOT edited for this.

**Why:** speech-to-text costs time and shapes what the cards say about hooks, speech and sync anchors; the user wants to choose per run instead of the pipeline deciding.

**How to apply:** the spec lives in item 10 of `Documents/prompts/pipeline-coupling-fable.txt` (understand-first audit of where audio becomes text today and of every feature that touches audio; one state.json key; no silent default; "audio not ingested" is never written as "no speech"; the audio file itself stays usable for the original-audio restore; the wider reading of "frames only" goes to the user). Not built yet: when it is, update this note. Related: [[atg-qc-fixes-option]] (the pattern for a start option stored in state), [[atp-skills-architecture]], [[scripts-gather-agents-decide]], [[no-cross-pipeline-mentions]].
