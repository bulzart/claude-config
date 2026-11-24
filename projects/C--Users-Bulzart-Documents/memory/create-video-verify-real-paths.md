---
name: create-video-verify-real-paths
description: "user 2026-11-24 - a /create-video change is done only when the real path ran: FLUX generation, CapCut desktop open+export, ElevenLabs (paid only on an explicit yes); report real vs mocked"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T11:58:12.085Z
---

A change to the /create-video pipeline is not complete because code exists or tests pass. Verify it on the actual path,
proportionate to what changed, on isolated test assets (never a finished production):
- FLUX Klein int8: a real, new, bounded generation through image_worker.py (see [[create-video-flux-klein-primary]]).
- CapCut: build an isolated project through the reusable path, open it in the real CapCut desktop app, look at the
  timeline and preview, make a bounded test export and check its frames and sound. If the GUI cannot be used, say GUI
  verification is incomplete; project JSON is not the app.
- ElevenLabs v4: verify request construction and handling free (mocks, recorded payloads, dry runs); a real post-change
  generation is billable: prepare the exact test with its credit estimate and ask first, unless an approved test budget
  explicitly covers it.
2026-11-24 results: FLUX new stills incl. a reference-image still; ACE-Step bed through music_worker; CapCut desktop
build+open+preview+export WITH captions (deep export check ready); ElevenLabs v4 live test on the user's yes (cap 205
credits): one 205-character part, 82 credits billed
(character-cost header), all 34 words heard, no tag read aloud.
Report each change in a matrix: verified by real execution / automated tests only / static inspection / not verified.
Never call a mock a live integration, never weaken a check to pass a test, never substitute a model or provider.

**Why:** the user's verification briefs of 2026-11-24 ("No modification is complete merely because the code was changed
or tests passed").

**How to apply:** plan the real-path checks when planning a change; budget GPU time and the user's screen (CapCut runs
only when the PC is idle, through capcut_desk.py).
