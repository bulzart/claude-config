# Copyright music in the kept footage (`T music`)

The user, 2026-11-21: keep the footage; take a song out only when the evidence is strong, never all music; never call a video copyright-safe;
recognising a song never removes it by itself. Steps kept apart: where music plays, which recording it is (the Song Identification Confidence), how
strong the evidence of YouTube claims on that recording is (the YouTube Copyright-Claim Risk index), the decision, the removal, its check. Long videos
only:

**Shorts are never touched** (the user, 2026-11-21: "For Shorts, never isolate, suppress, remove, replace, or otherwise modify music, even when the selected footage contains known copyright-risk songs. Preserve all original music and audio exactly as recorded; skip music identification, copyright-risk analysis, and separation processing for Shorts videos entirely"): `T music` skips a short's EDL (it writes a `music.json` that says so, and takes an older run's music patch back out of a short), the batch detection gets the long videos' spans only, and a short's report has no music list.


## What the tool does (facts; `cc.py music`)
- **Detection** on the footage an EDL keeps (never the whole stream): every 3 s window gets a music score from a steady beat, held notes and the
  harmonic share of the sound, smoothed and merged into intervals. The windows are cached for the run, and an interval that runs into the edge of the
  kept footage is followed to where the music ends, so a short and a long video that share a song analyse and clean it once.
  Measured on a GTA stream (2026-11-21): a song alone scores about 0.54, talk over a song 0.53, talk alone 0.42, a shootout 0.47 (threshold 0.50). It
  hears music; it does not know whose. A game's own score or a menu theme can show up as music: that only puts a line in the list.
- **Recognition service** (the user, 2026-11-21: no catalogue to build by hand): an interval the local fingerprints do not know is sent to a
  broad-catalogue service, ONLY when the user authorised it: `config.json -> music.recognition` `provider` (`acrcloud` or `audd`) and `allow_upload: true`,
  the keys in environment variables (ACRCLOUD_HOST, ACRCLOUD_ACCESS_KEY, ACRCLOUD_ACCESS_SECRET, or AUDD_API_TOKEN), never in a file. Off by default
  (`T music-evidence` shows the state and why). Two 12 s windows per interval, the ones with the least speech; at most `max_queries_per_run` (60) new
  queries a run; every answer cached by the clip's own samples (`data/music-ident-cache.json`). Confidence: ACRCloud's score (high at 90, or 70 with two
  windows agreeing), AudD's two windows agreeing; two windows naming two recordings stay medium. The recording is kept by its ISRC (else the service's id,
  else artist + title with its version words: live, remix, remaster, cover, ...). A high-confidence recording is LEARNED into the local fingerprints, so it
  is recognised offline and at no cost the next time it plays, in any run. Prices (2026-11): AudD $2-5 per 1,000 requests (300 free), uploads the clip;
  ACRCloud a 14-day trial, then pay per recognition (prices in its console). A local catalogue of commercial songs does not exist: without a service
  only recordings heard before (claims, learned) are recognised.
- **Recognition** (local, always): every interval is matched against the fingerprints of the claimed and the learned recordings (landmark fingerprints,
  the method of Shazam and audfprint, kept in `data/music-index/`). A match is the same recording, at the same place in it; no title is needed.
  Measured on the caseoh stream (10 s pieces of a radio song with a singer): recognised clean 3 of 3, under his talk with the song 6 dB louder 3 of 3,
  as loud as his talk 2 of 3, 6 dB quieter 0 of 3 (a whole song occurrence has quieter moments, and one recognised window is enough); 5 s pieces
  3 of 3 clean; no false match on another song, his talk, a shootout or his laugh (highest stray score 1 against a threshold of 12). It only knows
  recordings someone registered: an unknown song stays "not identified". Part of a song that was not in the claimed audio is not recognised either
  (the claim's reference is taken from the whole song occurrence around the claimed part, up to 8 minutes, to cover as much of it as there is).
- **Analysis** (temporary audio, never the output): an interval no fingerprint knows is split once into voices and accompaniment by Demucs
  (`30-assets/music/analysis/`, cached); the accompaniment is matched against the local fingerprints (the song without his voice over it); Whisper
  medium hears the voices for LYRIC FRAGMENTS (no voice-activity filter and no no-speech threshold: they drop singing; the voices brought to -20 dBFS;
  the prompt "Song lyrics, a pop song playing on the radio:"; the prompt's own echo dropped); a fragment that is mostly his own words (the stream
  transcript at that time) is left out; at most 3 fragments of up to 10 words: what to search, never the lyrics. The voices' level where nobody speaks
  says whether the song is SUNG (`sung`). Measured 2026-11-21 on the caseoh copy: with the default settings Whisper wrote nothing on a radio song; with
  these it wrote "focus, fireguns, what do you need so on to lean" (Lean On's chorus), three times over the stretch. The batch detection
  (`T music --spans`) runs it ahead and lists `research`. Removal spans are analysed too (the singer check needs `sung`).
- **Evidence for a person** for each interval: the miners' avoid entries, the chunk reports' sound lines, the stream's words about a song near it, three
  times to look at, the lyric fragments.
- **The two scores** (`cc_songid`), computed from recorded evidence items, never typed in:
  - *Song Identification Confidence* (0-100, about the EXACT recording in THIS interval): every identity item belongs to its interval (run + rec span;
    only a soundtrack listing and metadata facts are about the recording everywhere). Items of one method count once (the strongest); methods
    combine as independent: 100 x (1 - product(1 - s/100)). Kinds and upper strengths: a claim's fingerprint 95 (88 with one window), a learned
    fingerprint 90 (never above what it was learned at), a recognition service 92 / 75, the title on screen 85, a lyrics match 75 / 60 / 45 (the
    lyrics check sets it), his words naming the song 55, a soundtrack listing 40, a builder's naming 50 / 35 / 15. Without a version-specific item
    (fingerprint, service, screen title, a listing of that very recording) the score stops at 80: the song is known, not the recording (covers, live,
    remixes and radio edits share the words). Two candidates for one stretch that are both supported (the runner-up 50 or more and within 25
    points of the best) cap it at 60: a contradiction.
  - *YouTube Copyright-Claim Risk* (0-100): an evidence-based INDEX, not a probability (no verified outcomes exist yet to calibrate it on; the
    thresholds are provisional). Only items that name this very recording count (supporting facts aside); copies of one origin count once; origins
    combine as independent. Per item: a claim on the user's own channel 98, YouTube Studio's copyright check 95, the rights holder's own notice 90
    (credible 80), documented enforcement naming this recording 80 verified / 62 credible / 30 unverified, how its rights are administered 25 / 20 /
    10 (supporting only), and 0 for fame, a release, streaming, a major label, being copyrighted or a model's guess. Older than 5 years x0.6;
    limited to another region x0.5. Supporting facts alone stop at 40, unverified reports alone at 45, contradicting reports cap at 50, a licence or
    clearance for this use puts it at 5. The user's claims register (`data/music-claims.json`) counts as own-claim items.
  - *Outcome* (config `music.thresholds`: id 85, risk 85, concern 50): F two recordings supported for one stretch (left as it is, recorded); D
    identity under 85 (left as it is); E licensed or cleared (respected); **A identity 85+, risk 85+ and recording-specific enforcement evidence
    (credible or better): removal attempted**; F contradictory risk evidence; B risk 50+ (a possible concern, left as it is, flagged); C no adequate
    evidence (left as it is). Only A changes the audio. Unknown risk is not zero risk: C and D say so.
- **Removal** (only A, with `--apply`): **Hybrid Demucs first** (torchaudio, on the GPU, about 2 s per minute): the instruments dropped, the voices
  kept, -40 dB where no transcript word is within 2.0 s (`music.gate_db`; -18 before 2026-11-21, which left a sung song only 21 dB down). A span whose
  Demucs result fails a check another separation could fix (a sung song under his talk; music left where nobody speaks; his words) goes to **SAM
  Audio Base** (Meta, `scripts/sam_separate.py` in its own environment, one model load for all such spans, a GPU lease of 10 GB that waits for a
  CapCut export, the memory guard): "man speaking" kept through a stereo mask (SAM's keep/drop ratio applied to the ORIGINAL stereo audio: its phase
  and stereo picture stay, nothing generated is heard directly), the same gate, verified again; only a pass is used. A wrong length or offset is a
  fault, never escalated. Neither passes: `UNRESOLVED`, the original audio stays, both attempts recorded.
- **Measured 2026-11-21** (`C:\Users\Bulzart\Documents\stream-clips\validation\separation-bench-20261121`, controlled mixes of real stream audio,
  the song 6 dB under him; "music left" = the song's energy left beyond the wanted sound, lower is better; listening files in `listen\`):
  talk over a SUNG song: Demucs -13 dB (the voice band, where the singer sits: -10), his words 0.64 (Whisper recall; the mix 0.77); SAM "man
  speaking" kept -20 dB (voice band -17), words 0.64-0.73. Talk over an instrumental: Demucs -11.5, words 0.82; SAM -17.6, words 0.59. Laugh over a
  song: Demucs kept the laugh best (lost -11.5 dB against -6.0). Game sound under a song without talk: Demucs and SAM's speech both silence it; SAM
  "music playing" removed kept the game but left the song 16 dB down (fails the 35 dB check). Song alone: Demucs -48.6. "music playing" removed
  under talk lost his words (0.14); time anchors made the removal weaker (-4 dB). Whisper's word scores vary about 0.1 between runs.
  SAM Base on the RTX 3060 (fp32, 10 s windows): load 9-11 s, 5.6 GB after load, peak 8.3 GB, about 34 s per minute of audio. End to end on the
  caseoh copy (validation fixtures forcing outcome A): Demucs failed the singer check, SAM passed every check, the EDL used SAM's audio; the music
  step took 59 s.
- **SAM Audio Base install** (2026-11-21): the user's approved Hugging Face access (facebook/sam-audio-base, SAM License: royalty-free, use and
  modification allowed, laws and trade controls apply); checkpoint 7,725,405,659 bytes (SHA-256 b5f3e29e...6839) in the Hugging Face cache; the
  official code (github.com/facebookresearch/sam-audio) with dacvae, perception_models (unpin-deps), xformers 0.0.31.post1 and accelerate in
  `C:\Users\Bulzart\Documents\AI\sam-audio\.venv` (torch 2.7.1+cu128), never in another environment. The runner: the rerankers and the span
  predictor switched off through the official config overrides (nothing of theirs downloaded); the checkpoint streamed into the GPU one tensor at a
  time (GPU memory counts as committed memory on Windows: the official loader needed 17.6 GB); the unused vision encoder's 671 M parameters dropped
  after the strict load (no video prompts); torchcodec, imported but never used with audio passed in decoded, is a stand-in that refuses any use
  (`...\sam-audio\shims`). The music step lets go of its own Whisper before SAM starts.
- **Check** before anything changes: the same length, the edges match the original, his words still there (Whisper on the cleaned and on the original
  span against the transcript), no longer reads as music, **the music down 35 dB or more where nobody speaks** (1 s windows away from his words and
  the span's edges, or under -60 dBFS: a song turned down 20 dB is still plainly audible), and **no singer under his words**: a sung song under his
  talk removed by a method that keeps every voice (Demucs) fails ("A vocal stem containing both streamer speech and the song's singer is not
  successful separation", the user). The fingerprint of the removed part against the cleaned audio is recorded as information only, with and without
  the -50 dBFS floor: the floor hides residue below it, and a song a fingerprint no longer matches is not proof that it is gone. A SAM result passes
  the singer check by its method (measured above, not per span), so its line always asks for a listen.
- **Models** (2026-11-21): Hybrid Demucs (in use, first), SAM Audio Base (in use, the escalation). Tried, not adopted: MERL MRX (MIT, 122 MB: about
  3 dB more song removed under his words, 15 dB less between them, 4x slower); Demucs v4 htdemucs_ft (MIT code, about 0.8 GB of GPU memory: speech
  +0.2 dB, the song slightly less removed, 8x slower; config `music.model` `htdemucs_ft`). SAM Audio Small and Large are not installed (Base fits).
- **Licence:** Demucs's code is MIT; its weights were trained partly on MUSDB18, a non-commercial dataset, and carry no licence of their own (the user
  decides about a monetized channel). SAM Audio's weights: the SAM License, accepted by the user with their Hugging Face access.

## Registering a claim (the user, when YouTube claims a video)
YouTube Studio > Content > the video > Copyright shows the song, who claimed it and the claimed part's times in the video. One command keeps it all:
`T music-claim --add "Artist - Title" --evidence "YouTube Studio claim, <date>" --claimant "<who>" --policy monetize|block|track|restrict
 --record "<screenshot path or URL>" --run RUN --video <id> --at M:SS-M:SS` (the claim's times in that video: the toolkit maps them to the stream and
fingerprints that song where it plays). Without the run: `--file "<the exported MP4>" --at M:SS-M:SS`. From then on, that recording is recognised in
every run. `--remove M001` takes a claim and its fingerprint out. Never register a claim that was not received.

## The research step (the main session's ONE research agent; long videos only)
`T music` and the batch detection list `research`: per interval, what it needs (`identity` or `risk`), its candidates with their scores, the lyric
fragments, the stream's words about a song, the times to look at. The agent, for each:
1. *Identity*: search the web for the lyric fragments (garbled: try a few spellings) and the named songs; for each candidate `T music-evidence --new
   "Artist - Title"`, then `T music-evidence --lyrics "Artist - Title" --run RUN --rec A-B --rid <rid>` (LRCLIB, free and open: the interval's own
   fragments matched against the candidate's lyrics, only numbers kept; the lyrics_match item is added at the strength it earns: two different lines
   at 0.65+ 75, one 60, 0.58+ 45; measured on one real case, provisional), `T music-evidence --meta "Artist - Title"` (MusicBrainz, free, text only:
   versions, ISRCs, lengths, remixes, DJ mixes), and items it finds with `--add-id --rid <rid> --kind <kind> --run RUN --rec A-B --detail "..."
   --source <where>` (his words naming it: spoken_mention; a title on screen: onscreen_title with the frame time; a soundtrack listing of that very
   recording: soundtrack_listing). A candidate the evidence contradicts gets its items too: the scores record the contradiction.
2. *Risk* (only for a recording identified at 85+): reports of YouTube Content ID claims, blocks or restrictions that NAME THIS RECORDING and version,
   the rights holder's own statements, a licence or clearance for YouTube: `T music-evidence --add-risk --rid <rid> --kind <kind> --summary "..."
   --source <URL> --quality verified|credible|unverified [--specific] [--origin <the original source when sites copy one another>] [--date]
   [--region]`. Fame, a release, streaming, a major label or "copyrighted" are not evidence; nothing found is recorded as nothing_found.
3. `T music --edl ... [--apply]` again; the scores are recomputed. Stop when more searching is unlikely to change the decision; never invent a title
   to avoid "unknown".
`T music-evidence --rid <rid>` shows a recording's intervals and scores; `--pending` lists recordings identified at 85+ without risk research.

## The builder's step (long videos; after the EDL is final, before the build)
1. `T music --run RUN --edl OUT/edl.json` writes `OUT/music.json`: every interval with where it plays in the video, its candidates, both scores, the
   outcome (A-F) and why, the analysis, what research it needs, its status.
2. Name an interval's recording in the EDL's `music` list only where the evidence shows it (`{"rec_from", "rec_to", "title", "artist",
   "confidence": "high|medium|low", "evidence"}`): a weak item (50 at most); never a guessed title. Research is the main session's.
3. `T music --run RUN --edl OUT/edl.json --apply` when a line says `remove` (outcome A): Demucs, and SAM Audio Base for a span Demucs cannot clean;
   an EDL changed after `--apply` gets `--apply` again (cached: seconds); the patch is replaced, never stacked.
4. The report lists every interval: its output time, removed (with SAM: listen before publishing) / UNRESOLVED / left as it is with its outcome, and
   why. A music line never fails a video and never drops a moment.

## Never
- Never remove or mute music on a guess, because a song sounds famous, because it was recognised, or because the game is known for licensed radio: only
  outcome A changes the audio.
- Never use the analysis audio (the temporary separation) as the output. Never say a video or a song is safe, cleared or claim-free; never call the
  risk index a probability.
- Never use a paid recognition service or send audio anywhere without the user's yes (`music.recognition.allow_upload` is that yes). The lyrics
  check and MusicBrainz send text only.
- Never run `T music` for a short, never add a music mute or a cleaned lane to a short: shorts keep their audio exactly as recorded.
- Never replace a whole clip's sound when a span is the problem; never hand over cleaned audio that failed its check; never install SAM Audio Large or
  download model weights during a run.

`T music --run RUN --spans "A-B,..."` detects and analyses ahead of the EDLs (`cc-produce` runs it once for every planned span of the LONG videos; it
lists `research`; `--no-analysis` for detection only). `T music-id --run RUN --rec A-B` shows a recognition by hand. `T music-setup` checks the
Demucs separation's Python, weights and a 4 s self-test.
