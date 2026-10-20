---
name: atp-audio-ingest-question
description: "/analyze-then-pick asks once at the start (contract item 24) whether the videos' audio is processed with Whisper speech-to-text or frames only; state.json audio_ingest (whisper | frames-only) is the only source, no default, frames-only = no transcript and 'audio not ingested' never 'no speech'; built 2026-10-20"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T01:49:33.815Z
---

The user asked (2026-10-20, first for the other pipeline, then moved): /analyze-then-pick should implement audio-to-text ingestion with Whisper throughout all its features, and it must be optional: the user chooses at the start whether the videos' audio is processed or only the video image frames. (They wrote "audio to text ttl whisper": read as speech-to-text; the Fable prompt asks the agent to stop and report if the evidence points to another meaning.) The other pipeline, /analyze-then-generate, is NOT edited for this.

**Why:** speech-to-text costs time and shapes what the cards say about hooks, speech and sync anchors; the user wants to choose per run instead of the pipeline deciding.

**How to apply:** the spec lives in item 10 of `Documents/prompts/pipeline-coupling-fable.txt` (understand-first audit of where audio becomes text today and of every feature that touches audio; one state.json key; no silent default; "audio not ingested" is never written as "no speech"; the audio file itself stays usable for the original-audio restore; the wider reading of "frames only" goes to the user). Built 2026-10-20 (commits 87785f2, 9e6d061): `atp-start` step 5b asks (header "Audio ingest", no option recommended; the measured cost is in the option text), step 6 stores `audio_ingest`; router item 24; `T prep-all` reads the key and stops without it, `T prep-video --audio-ingest`, `T captions --from-speech` refuses in a frames-only run; frames-only writes no transcript and `video.md`, `timeline.md`, the cards (analysis-protocol §2.4, §3), the sync anchors (generation-system §5c.1, atp-edit E2) and the sound plan say `audio not ingested`; the contract carries an "Audio ingest" line; tests t01/t02 cover it. Open for the user: the wider reading of "frames only" (no audio measurement at all) and whether the sibling asks the same question. Related: [[atg-qc-fixes-option]] (the pattern for a start option stored in state), [[atp-skills-architecture]], [[scripts-gather-agents-decide]], [[no-cross-pipeline-mentions]].
