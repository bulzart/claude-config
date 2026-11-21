# Copyright music in the kept footage (`T music`)

The user, 2026-11-21: keep the footage; remove a song only when its risk is established, never all music, and never call a video copyright-safe.
Five steps, kept apart: where music plays, which recording it is, whether that recording has a claim on record, the removal, and its check.

## What the tool does (facts; `cc.py music`)
- **Detection** on the footage an EDL keeps (never the whole stream): every 3 s window gets a music score from a steady beat, held notes and the
  harmonic share of the sound, smoothed and merged into intervals. The windows are cached for the run, and an interval that runs into the edge of the
  kept footage is followed to where the music ends, so a short and a long video that share a song analyse and clean it once.
  Measured on a GTA stream (2026-11-21): a song alone scores about 0.54, talk over a song 0.53, talk alone 0.42, a shootout 0.47 (threshold 0.50). It
  hears music; it does not know whose. A game's own score or a menu theme can show up as music: that only puts a line in the list.
- **Evidence to name it**: for each interval nobody identified, the miners' avoid entries, the chunk reports' sound lines and the stream's words about a
  song near it, and three times to look at (`look_at`: a game's radio wheel or a music app prints the station and the song).
- **Risk** is a lookup in `data/music-claims.json`, the claims the user has really received (`T music-claim --add "Artist - Title" --evidence "..."`):
  `confirmed` (a claim, block or restriction on record) -> removed; `none` (identified, nothing on record) -> left as it is (not "safe": nothing here
  can see YouTube's Content ID); `unknown` (not identified, or a guess written with confidence `low`) -> left as it is and listed for a listen.
- **Removal** (only `confirmed`, with `--apply`): Hybrid Demucs (torchaudio, on the GPU) splits the padded span; the instruments are dropped, the voices
  stay, and where nobody speaks (no transcript word within 1.5 s) the voice stem is lowered 18 dB, so a sung line between his words goes down. Measured on
  a controlled mix (60 s of his talk plus a song with a singer): talk alone comes through at 14.5 dB SI-SDR (level -0.2 dB); with the song 6 dB under his
  voice the result moves from 7.0 to 10.9 dB and Whisper's word match from 0.76 to 0.87; the song alone drops 25 dB where he is silent but only 7 dB
  under his words. **A singer under his words stays audible**, and a long laugh with no word near it is lowered with the singer.
- **Check** before anything changes: the same length, in sync (cross-correlation, within 10 ms), his words still there (Whisper on the cleaned and on the
  original span against the transcript), no longer music by the same detector. Pass: the EDL's segment gets a `mute` span (its own sound off there, the
  zoom untouched) and the cleaned audio goes on an audio lane (`sfx` entry with `music_clean: true`). Fail: the original sound stays and the line says
  `attention`. A song with voices in the gaps always says "listen before publishing".

## The builder's step (after the EDL is final, before the build)
1. `T music --run RUN --edl OUT/edl.json` writes `OUT/music.json` and lists every interval with where it plays in the video, its evidence and status.
2. Only when `claims_on_record` is above 0 is identification worth your time: name an interval's recording where the evidence shows it (the words, a
   report line, a frame at its `look_at`), in the EDL's `music` list: `{"rec_from", "rec_to", "title", "artist", "confidence": "high|medium|low",
   "evidence": "what showed it"}`. Never guess a title: a guess is `low` and is treated as unknown. Then `T music --run RUN --edl OUT/edl.json --apply`.
   With no claims on record, skip this: nothing is removed whatever the song is, and the list goes to the user as it is.
3. An EDL changed after `--apply` gets `--apply` again (cached: seconds); the patch is replaced, never stacked.
4. The report lists every interval: its output time, removed / listen before publishing / left as it is, and why. A music line never fails a video and
   never drops a moment: a strong moment with a song under it stays a candidate, and the user decides.

## Never
- Never remove or mute music on a guess, because a song sounds famous, or because the game is known for licensed radio.
- Never say a video or a song is safe, cleared or claim-free. Never use a paid recognition service or upload audio anywhere.
- Never replace a whole clip's sound when a span is the problem; never hand over cleaned audio that failed its check.

`T music --run RUN --spans "A-B,..."` detects ahead of the EDLs (`cc-produce` runs it once for every planned span). `T music-setup` checks the separation's
Python (the ACE-Step venv's torch 2.7.1 + torchaudio, CUDA), the weights (319 MiB, in the torch cache) and runs a 4 s self-test.
