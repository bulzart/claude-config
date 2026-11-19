---
name: feedback-elevenlabs-v4-only
description: "ElevenLabs narration uses only eleven_v4 / eleven_v4_turbo; no speed-setting tests; tags chosen by the video's agents from the full tag catalogue"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-19T18:43:14.586Z
---

ElevenLabs narration in every pipeline uses **only `eleven_v4` and `eleven_v4_turbo`** ("only elvenlabs v4 and v4 turbo model strictly", said three times on 2026-11-19). Do not test or propose the `speed` setting on them ("no it has no speed test"), and do not switch to Flash/Turbo v2.5 for their speed setting.

Audio tags: the user wants the full official tag list fetched with each tag's description, and the agents making the video to decide which fit the story (no fixed tag recipe); avoid long pauses except where they really matter. Voices are hand-picked from ElevenLabs tags and descriptions, then calibrated on a real part.

**Why:** the user's other sessions reached their pace with v4; earlier runs drifted to other models and wasted credits. Measured 2026-11-19: v4/v4 Turbo voices converge to ~175-188 WPM on real parts; short samples and previews read fast and mislead.

**How to apply:** in /create-video this is enforced in code (static_core.py `TTS_MODELS`, catalogue `static-studio/data/elevenlabs-audio-tags.json`); in other pipelines (/analyze-with-loupe Static, /create-static) apply the same rule by hand. Related: [[project-analyze-stack]], [[feedback-pipeline-rules]].
