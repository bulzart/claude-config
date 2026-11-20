---
name: one-pipeline-per-session
description: "User 2026-11-20: a session works on ONE pipeline; a brief naming another pipeline's feature means that feature in this session's pipeline; other pipelines are read-only references"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T14:34:45.003Z
---

User 2026-11-20, in a /create-video session, after a pasted brief's Part B said "/create-clips" and I started treating it as create-clips work: "we're working on create-video not on create-clips", then "no we're doing the same captions feature in create-videos too, another session is working on create-clips we're just talking about create-videos strictly in this session!!!!!!", then "we can look at create-clips as a reference for captions but make strictly sure we're executing and referring to only on create-videos in this session no matter the task".

**Why:** the user runs one session per pipeline in parallel (another session was editing create-clips at the same time); a brief written for one pipeline is often meant to be carried into another.

**How to apply:** find out which pipeline the session is on (the conversation, the run, the files touched) and do every part of a brief there, translated to that pipeline's own files and words. Another pipeline's code may be read as a reference, never run, edited, tested or committed from this session, and the docs of this session's pipeline never mention it ([[no-cross-pipeline-mentions]]). If a brief's pipeline is truly unclear, ask before touching anything. Related: [[no-cross-session-messages]].
