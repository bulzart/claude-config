---
name: create-clips-music-isolation
description: "user 2026-11-21: music removed only for a recording with a real claim on record, recognised by its fingerprint; Demucs v3 default; never \"safe\""
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T01:48:05.841Z
---

The user, 2026-11-21 (two specs): never remove all music, never drop a strong highlight over a song, decide risk on evidence only, recognition never
removes by itself, flag unknowns, never call a video copyright-safe, no paid recognition API or sending audio out without approval.

Built: `cc.py music` (detection on the EDL's kept footage, cached per run; recognition: landmark fingerprints of the claimed recordings in
`create-clips/data/music-index/`; risk = the claim's status in `data/music-claims.json`; `--apply` removes only `confirmed`), `music-claim` (from the
claimed video + its YouTube Studio times: `--run --video --at`, or `--file --at`; `--claimant --policy --record`), `music-id`, `music-setup`,
`reference/music.md`. Separation: torchaudio Hybrid Demucs run by `scripts/audio_separate.py` with the ACE-Step venv's Python; speech window 2.0 s.

**Why:** Content ID is not queryable; the register of claims really received is the only substantiated evidence. The user asked "do I need to register
songs?": yes, only claims they actually receive (one command per claim); no song names appear on screen in their streams (no OCR route).

**How to apply (measured 2026-11-21):** recognition at threshold 12: 12 of 18 real 10 s/5 s pieces, 0 false matches (stray max 1); fails when the song
is 6 dB under his talk. A singer under his words stays (~7 dB down). Tried and not adopted: MERL MRX (MIT; 3 dB better under words, 15 dB worse
between, 4x slower), htdemucs_ft (demucs package in `Documents\AI\music-sep\pydeps`; 0.8 GB VRAM peak not 6 GB, 8x slower, no better; option
`music.model`). Licence: Demucs weights trained partly on MUSDB18 (non-commercial dataset), no weight licence: the user's decision. Next candidate
only on the user's say: SAM Audio (gated on Hugging Face, 5.1 GB+). Evidence: `Documents\stream-clips\validation\longform-20261120\evidence\`
(music-eval*, fp-eval.json). Related: [[create-clips-gpu-whisper]].
