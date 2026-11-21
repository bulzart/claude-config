---
name: create-clips-music-isolation
description: "user 2026-11-21: copyright music removed only for a recording with a claim on record; T music, Demucs in the ACE-Step venv, never \"safe\""
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T00:41:40.246Z
---

The user, 2026-11-21 (spec "Automatic Music-Isolation Setup"): never remove all music, never drop a strong highlight over a song, decide risk on
evidence only, flag unknowns, never call a video copyright-safe, no paid recognition APIs without approval.

Built: `cc.py music` (detection on the EDL's kept footage, cached on one grid per run; evidence lines; risk = lookup in
`create-clips/data/music-claims.json`, which the user fills with `music-claim --add "Artist - Title" --evidence ...`; `--apply` removes only
`confirmed`), `music-setup`, `reference/music.md`. Separation = torchaudio Hybrid Demucs (HDEMUCS_HIGH_MUSDB_PLUS) run by
`scripts/audio_separate.py` with the ACE-Step venv's Python (torch 2.7.1+cu128); weights 319 MiB in `~/.cache/torch/hub/torchaudio/models/`,
downloaded on the user's yes 2026-11-21. Nothing installed into ACE-Step.

**Why:** Content ID is not queryable; the register of claims really received is the only substantiated evidence.

**How to apply:** measured limits to repeat honestly: a singer UNDER his words stays (only ~7 dB down; 25 dB where he is silent); a long laugh with no
word near it is lowered with the singer, so a span with voices in the gaps says "listen before publishing". Speech kept: SI-SDR 14.5 dB on talk alone.
