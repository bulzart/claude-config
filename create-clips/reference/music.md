# Copyright music in the kept footage (`T music`)

The user, 2026-11-21: keep the footage; remove a song only when that exact recording has a real claim or restriction on record; never all music; never
call a video copyright-safe; recognising a song never removes it by itself. Five steps, kept apart: where music plays, which recording it is, whether that
recording has a claim on record, the removal, and its check.

## What the tool does (facts; `cc.py music`)
- **Detection** on the footage an EDL keeps (never the whole stream): every 3 s window gets a music score from a steady beat, held notes and the
  harmonic share of the sound, smoothed and merged into intervals. The windows are cached for the run, and an interval that runs into the edge of the
  kept footage is followed to where the music ends, so a short and a long video that share a song analyse and clean it once.
  Measured on a GTA stream (2026-11-21): a song alone scores about 0.54, talk over a song 0.53, talk alone 0.42, a shootout 0.47 (threshold 0.50). It
  hears music; it does not know whose. A game's own score or a menu theme can show up as music: that only puts a line in the list.
- **Recognition** (automatic): every interval is matched against the fingerprints of the recordings in the claims register (landmark fingerprints,
  the method of Shazam and audfprint, kept in `data/music-index/`). A match is the same recording, at the same place in it; no title is needed.
  Measured on the caseoh stream (10 s pieces of a radio song with a singer): recognised clean 3 of 3, under his talk with the song 6 dB louder 3 of 3,
  as loud as his talk 2 of 3, 6 dB quieter 0 of 3 (a whole song occurrence has quieter moments, and one recognised window is enough); 5 s pieces
  3 of 3 clean; no false match on another song, his talk, a shootout or his laugh (highest stray score 1 against a threshold of 12). It only knows
  recordings someone registered: an unknown song stays "not identified". Part of a song that was not in the claimed audio is not recognised either
  (the claim's reference is taken from the whole song occurrence around the claimed part, up to 8 minutes, to cover as much of it as there is).
- **Evidence for a person** for each interval nobody identified: the miners' avoid entries, the chunk reports' sound lines and the stream's words about
  a song near it, and three times to look at (`look_at`).
- **Risk** is a lookup in `data/music-claims.json`, the claims the user has really received: `confirmed` (a claim, block or restriction on record,
  matched by fingerprint, or by a builder's high-confidence title when the claim has no audio) -> removed; `none` (identified, nothing on record, or
  cleared) -> left as it is, never "safe"; `unknown` (not identified, or a low-confidence guess) -> left as it is and listed for a listen.
- **Removal** (only `confirmed`, with `--apply`): Hybrid Demucs (torchaudio, on the GPU) splits the padded span; the instruments are dropped, the voices
  stay, and where nobody speaks (no transcript word within 2.0 s) the voice stem is lowered 18 dB, so a sung line between his words goes down.
  Measured on a controlled mix (60 s of his talk plus a song with a singer): talk alone comes through at 14.5 dB SI-SDR; with the song 6 dB under his
  voice 7.0 -> 11.0 dB and Whisper's word match 0.76 -> 0.89; the song drops 25 dB where he is silent but only about 7 dB under his words. **A singer
  under his words stays audible.** The 2.0 s window (1.5 s before 2026-11-21) keeps his laugh far better (15.6 against 11.5 dB SI-SDR on a
  face-verified laugh) and leaves the song open 38% of a sparse-talk song span instead of 33%.
- **Check** before anything changes: the same length, the edges match the original exactly, his words still there (Whisper on the cleaned and on the
  original span against the transcript), no longer music (or 20 dB or more down). Pass: the EDL's segment gets a `mute` span (its own sound off there, the
  zoom untouched) and the cleaned audio goes on an audio lane (`sfx` entry with `music_clean: true`). Fail: the original sound stays and the line says
  `attention`. A song with voices in the gaps always says "listen before publishing".
- **Models tried (2026-11-21), not adopted:** MERL MRX (MIT, dialogue/music/effects, 122 MB): about 3 dB more song removed under his words, 15 dB
  less between them, 4x slower. Demucs v4 htdemucs_ft (MIT code, 4 x 84 MB, about 0.8 GB of GPU memory at our settings): speech +0.2 dB, the song
  slightly less removed (-5.8 against -6.6 dB under his words), 8x slower. It stays available: config `music.model` `htdemucs_ft` (the demucs package
  in `music.pydeps`, outside every other environment). A model that tells speech from singing (Meta's SAM Audio: gated on Hugging Face, 5.1 GB and
  more) would be the next try, on the user's say.
- **Licence:** the code of Demucs is MIT; its weights (torchaudio's and the demucs package's) were trained partly on MUSDB18, a dataset for
  non-commercial use, and carry no licence of their own. The user decides about using them for a monetized channel.

## Registering a claim (the user, when YouTube claims a video)
YouTube Studio > Content > the video > Copyright shows the song, who claimed it and the claimed part's times in the video. One command keeps it all:
`T music-claim --add "Artist - Title" --evidence "YouTube Studio claim, <date>" --claimant "<who>" --policy monetize|block|track|restrict
 --record "<screenshot path or URL>" --run RUN --video <id> --at M:SS-M:SS` (the claim's times in that video: the toolkit maps them to the stream and
fingerprints that song where it plays). Without the run: `--file "<the exported MP4>" --at M:SS-M:SS`. From then on, that recording is recognised in
every run. `--remove M001` takes a claim and its fingerprint out. Never register a claim that was not received.

## The builder's step (after the EDL is final, before the build)
1. `T music --run RUN --edl OUT/edl.json` writes `OUT/music.json`: every interval with where it plays in the video, the recognition, its evidence
   and status. With claims on record that carry a fingerprint, recognition is automatic: nothing to do but `--apply` when a line says `remove`.
2. A claim registered by title only (no audio): name an interval's recording where the evidence shows it, in the EDL's `music` list
   (`{"rec_from", "rec_to", "title", "artist", "confidence": "high|medium|low", "evidence"}`); never guess a title (a guess is `low`). With no claims on
   record at all, skip this: nothing is removed whatever the song is.
3. `T music --run RUN --edl OUT/edl.json --apply` when a line says `remove`; an EDL changed after `--apply` gets `--apply` again (cached: seconds); the
   patch is replaced, never stacked. The separation waits while a CapCut export holds the GPU (`T gpu`).
4. The report lists every interval: its output time, removed / listen before publishing / left as it is, and why. A music line never fails a video and
   never drops a moment: a strong moment with a song under it stays a candidate, and the user decides.

## Never
- Never remove or mute music on a guess, because a song sounds famous, because it was recognised, or because the game is known for licensed radio.
- Never separate unknown music to identify it. Never say a video or a song is safe, cleared or claim-free.
- Never use a paid recognition service or send audio anywhere without the user's yes.
- Never replace a whole clip's sound when a span is the problem; never hand over cleaned audio that failed its check.

`T music --run RUN --spans "A-B,..."` detects ahead of the EDLs (`cc-produce` runs it once for every planned span). `T music-id --run RUN --rec A-B`
shows a recognition by hand. `T music-setup` checks the separation's Python (the ACE-Step venv's torch 2.7.1 + torchaudio, CUDA), the weights
(319 MiB, in the torch cache) and runs a 4 s self-test.
