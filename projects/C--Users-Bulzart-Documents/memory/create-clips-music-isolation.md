---
name: create-clips-music-isolation
description: "user 2026-11-21: long videos only; music removed only on established risk (claims or the evidence register); recognition service needs the user's yes"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T16:11:02.699Z
---

The user, 2026-11-21 (three specs): never remove all music, never drop a strong highlight over a song, decide risk on evidence only, recognition never
removes by itself, never call a video copyright-safe, no paid service or sending audio out without approval, no manual catalogue. Shorts: never touched
([[create-clips-shorts-never-touch-music]]).

Built: `cc.py music` (detection on kept footage; recognition = local landmark fingerprints of claimed + LEARNED recordings, then `cc_songid` ACRCloud/AudD
only with `config music.recognition.provider` + `allow_upload: true` + env keys; cached in `data/music-ident-cache.json`); risk = claims register, then
`data/music-evidence.json` decisions (`cc.py music-evidence`: verified needs own claim / Studio check / rights-holder notice; strong needs 2 recording-specific
reports from 2 sites; cleared needs a licence); identified but undecided = `pending` -> ONE research agent per run (music.md "The research step").
Removal: verified + strong (`remove_strong` true). Separation: Hybrid Demucs, 2.0 s speech window, gate -18 dB.

**Why:** Content ID is not queryable; evidence must name the recording. A level drop is not removal: the `recording_left` check fingerprints the removed
part against the cleaned audio over a -50 dBFS floor (caseoh Cheap Thrills: original 20-254, cleaned 0-5; without the floor even -60 dB matched).

**How to apply:** service off until the user authorises (AudD $2-5/1000, 300 free, uploads clips; ACRCloud 14-day trial). Singer under his words stays
~7 dB down (audible). Not adopted: MRX, htdemucs_ft. Next model only on the user's say (SAM Audio gated, 5.1 GB+). Demucs weights: MUSDB18 grey area,
the user's decision. Evidence: `Documents\stream-clips\validation\music-demo\` (residual-eval.json) and `longform-20261120\evidence\`. Related:
[[create-clips-gpu-whisper]].
