---
name: local-neural-fingerprint
description: "2026-11-21: LAION neural audio fingerprint + local reference index (cc.py music-index); names a song only if its reference is indexed; measured limits"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T21:52:51.999Z
---

The user, 2026-11-21: song identification must be local and open-weight only ("Do not use ShazamIO, Shazam's recognition service, AudD, ACRCloud,
hosted AcoustID lookup, hosted MVSep inference"); never send audio, fingerprints or embeddings out; never fill the catalog with downloaded commercial
recordings. Hosted recognition is switched off in code (`cc_songid.service_state` always inactive).

Built: `laion/neural-audio-fingerprint` (Apache-2.0, 321,329,282-byte checkpoint, SHA-256 checked) in `C:\Users\Bulzart\Documents\AI\audio-fp\.venv`
(torch 2.7.1+cu128, soundfile, soxr); runner `create-clips\scripts\nafp.py`; production index `create-clips\data\nafp-index\` (starts EMPTY);
`cc.py music-index --add FILE | --from-run RUN --rec A-B --id --title [--artist --license --provenance]`, `--remove`, `--query`. Levels: 0.90 + 2
consistent windows = strong (identity 90, 95 with 4+), fair 0.67 (80; was 0.80, lowered on the measured 0.1 % null-window point). Intervals queried in
2-min excerpts (up to 10), merged with a one-playback consistency check; retry on the analysis step's separated accompaniment where his words overlap.
A reference's `--id-score` (required with --from-run) caps every match against it: a guessed title never becomes a 95.
Same method group as the landmark fingerprints (never counted twice).

**Why:** a fingerprint model is not a catalog: it names a song only when the reference recording is in the local index. Measured (validation
`fingerprint-bench-20261121`, 8 refs: 5 ACE-Step tracks + 3 stream songs, 110 queries): clean/2-3 s/MP3 64k/-20 dB/3 % speed all found; song 6 dB
over his talk 8/8 at 0.80; as loud 1/8; 6 dB under 0/8; Demucs- or SAM-separated first did NOT rescue it (0/9, 2/9 at 0.75); 13/13 unknowns UNKNOWN; no
false or wrong match (wrong-recording max 0.70). Thresholds provisional (one small set).

**How to apply:** coverage grows only by adding references the user may use (their files, a stream stretch where an identified song plays without his
talk, openly licensed music). nmfp-triplet TESTED 2026-11-21 (`Documents\AI\nmfp`, TF 2.13 CPU, Essentia spectrogram replicated): at matched
false-alarm better 6 dB under talk (6/8 vs 2/8) but worse SAM-separated and 0/6 on sped-up; 40x slower; readme AGPLv3 / LICENSE GPL-3.0: NOT
integrated, the user's licence decision asked. Related: [[create-clips-music-isolation]], [[sam-audio-base-install]].
