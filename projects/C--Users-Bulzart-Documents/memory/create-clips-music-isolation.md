---
name: create-clips-music-isolation
description: "user 2026-11-21: long videos only; two scores (identity, claim-risk index) from interval-bound evidence; only outcome A removes: Demucs first, SAM Audio Base escalation"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T19:31:39.509Z
---

The user, 2026-11-21 (four specs): never remove all music, never drop a strong highlight over a song, decide on evidence only, recognition never
removes by itself, never call a video copyright-safe, the risk score is an index (never "a 90% chance"), no paid service or sending audio out without
approval, no manual catalogue, never invent a title to avoid "unknown". Shorts: never touched ([[create-clips-shorts-never-touch-music]]). Since 2026-11-22 the whole step runs only in an Isolation run ([[create-clips-music-mode]]).

Built (round 4, tag `create-clips-music-scores-20261121` + the SAM commit): `cc_songid` scores per interval: Song Identification Confidence (items of one
method count once; independent methods combine; 80 cap without version-specific evidence; a close supported competitor caps at 60) and YouTube
Copyright-Claim Risk (only items naming the recording; copies of one origin once; caps 40 supporting-only / 45 unverified / 50 contradiction; licence 5).
Outcome A (id 85 + risk 85 + credible recording-specific enforcement) is the only removal; B-F leave the audio. Identity items are BOUND TO THEIR
INTERVAL (run + rec): a design flaw found on the caseoh test (evidence from one stretch would have raised another). Research = ONE agent: `music-evidence
--lyrics` (LRCLIB, numbers only; thresholds 0.65/0.58 from one real case, provisional), `--meta` (MusicBrainz, retry on 503), `--add-id/--add-risk`.
The analysis (temporary Demucs split + Whisper medium on the voices, no VAD, lyrics prompt) gives fragments and `sung`.

**Why:** the caseoh "Cheap Thrills" demo was most likely Lean On (his words named Cheap Thrills; the sung chorus fits Lean On at 0.60-0.67, other songs
0.39-0.53): a spoken mention is weak evidence. Demucs keeps every voice, so a sung song under his talk fails the singer check ("A vocal stem containing
both streamer speech and the song's singer is not successful separation"); the fingerprint after removal is information only (the -50 dBFS floor hid
residue). Gate now -40 dB (-18 left a sung song 21 dB down).

**How to apply:** removal = Demucs first, then SAM Audio Base ([[sam-audio-base-install]]) for spans Demucs fails (not duration/sync faults); neither
passes = UNRESOLVED, original kept. A SAM removal always asks for a listen. Thresholds provisional (no verified outcomes). Hosted recognition is OFF in code for good (the user, 2026-11-21); identification adds the local neural fingerprint ([[local-neural-fingerprint]]). Labelled fixtures never count unless CC_ALLOW_FIXTURES=1 (tests only). Validation register with labelled fixtures:
`...\validation\longform-20261120\caseoh\30-assets\music\validation-evidence.json` (never the real `data/music-evidence.json`).
