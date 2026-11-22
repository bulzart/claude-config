# Copyright music in the kept footage (`T music`)

The user, 2026-11-21: keep the footage; take a song out only when the evidence is strong, never all music; never call a video copyright-safe;
recognising a song never removes it by itself. Steps kept apart: where music plays, which recording it is (the Song Identification Confidence), how
strong the evidence of YouTube claims on that recording is (the YouTube Copyright-Claim Risk index), the decision, the removal, its check. Long videos
only:

**Shorts are never touched** (the user, 2026-11-21: "For Shorts, never isolate, suppress, remove, replace, or otherwise modify music, even when the selected footage contains known copyright-risk songs. Preserve all original music and audio exactly as recorded; skip music identification, copyright-risk analysis, and separation processing for Shorts videos entirely"): `T music` skips a short's EDL (it writes a `music.json` that says so, and takes an older run's music patch back out of a short), the batch detection gets the long videos' spans only, and a short's report has no music list.


**Isolation or Non-Isolation** (the user, 2026-11-22, "Add Isolation / Non-Isolation Mode Without Changing the Existing Content Workflow"): `cc-start` asks it with the other start questions and stores `state.json -> music_isolation_mode` (`isolation` or `non_isolation`; a run made before the question has none and keeps Isolation, the step as it was). **Isolation** runs everything in this file for the long videos. **Non-Isolation** bypasses it at the entry: `T music` reads the mode before anything else and answers `bypassed` (no settings, detection, fingerprint, index query, lyrics, risk score, research line, separation, SAM, GPU lease or music folder); each EDL keeps its original soundtrack and its `music.json` says so; `cc-produce` starts no `T music --spans` and no music research agent. Shorts are bypassed in both modes. The mode is read only by this step and by `edl-check`, which never builds a music patch into a short or a Non-Isolation video (a leftover one is left out and listed as `music_patch_left_out`); it never reaches the research, the mining, the plan or a brief, and never changes what is collected, picked, cut or ordered: the same recording gives the same videos in both modes, only the qualifying songs' audio differs.
**Changing the mode of a run** (only on the user's word): `T state --run RUN set music_isolation_mode=non_isolation` (or `isolation`) prints `music_switch`. To Non-Isolation: every long video's EDL carrying a music patch has it taken out (`restored`; the patched EDL kept as `edl.music-patched.json`, the cleaned audio and every analysis kept in `30-assets/music`); one whose CapCut project was built with it is listed in `rebuild` (edl-check, captions, capcut-build); a video already exported or verified is left exactly as it is (`left_as_delivered`) until the user asks for a rebuild. To Isolation: the switch processes nothing; a long video not built yet gets the step at its build, one built or waiting for CapCut is listed in `music_step` (`T music --edl ... --apply`: the caches reused, the patch applied once, never stacked; then a rebuild), a delivered one is left as it is. A music job running during a switch stops before anything is applied (its finished work stays cached). Shorts, cuts, captions, zooms, sound effects and blurs are never touched.

## What the tool does (facts; `cc.py music`)
- **Detection** on the footage an EDL keeps (never the whole stream): every 3 s window gets a music score from a steady beat, held notes and the
  harmonic share of the sound, smoothed and merged into intervals. The windows are cached for the run, and an interval that runs into the edge of the
  kept footage is followed to where the music ends, so a short and a long video that share a song analyse and clean it once.
  Measured on a GTA stream (2026-11-21): a song alone scores about 0.54, talk over a song 0.53, talk alone 0.42, a shootout 0.47 (threshold 0.50). It
  hears music; it does not know whose. A game's own score or a menu theme can show up as music: that only puts a line in the list.
- **No hosted recognition** (the user, 2026-11-21: "Do not use ShazamIO, Shazam's recognition service, AudD, ACRCloud, hosted AcoustID lookup,
  hosted MVSep inference, commercial music-recognition APIs"): identification is local and open-weight. The ACRCloud / AudD adapters stay in the code,
  unreachable whatever the config says (`cc_songid.service_state` is always off). No audio, fingerprint or embedding leaves this PC.

- **Recognition** (local, always): every interval is matched against the fingerprints of the claimed and the learned recordings (landmark fingerprints,
  the method of Shazam and audfprint, kept in `data/music-index/`). A match is the same recording, at the same place in it; no title is needed.
  Measured on the caseoh stream (10 s pieces of a radio song with a singer): recognised clean 3 of 3, under his talk with the song 6 dB louder 3 of 3,
  as loud as his talk 2 of 3, 6 dB quieter 0 of 3 (a whole song occurrence has quieter moments, and one recognised window is enough); 5 s pieces
  3 of 3 clean; no false match on another song, his talk, a shootout or his laugh (highest stray score 1 against a threshold of 12). It only knows
  recordings someone registered: an unknown song stays "not identified". Part of a song that was not in the claimed audio is not recognised either
  (the claim's reference is taken from the whole song occurrence around the claimed part, up to 8 minutes, to cover as much of it as there is).
- **Neural fingerprint** (local, open weights; `scripts/nafp.py` in `C:\Users\Bulzart\Documents\AI\audio-fp\.venv`): LAION's
  `laion/neural-audio-fingerprint` (Apache-2.0, 80.3 M parameters, checkpoint 321,329,282 bytes, SHA-256 checked) turns every 1 s of 16 kHz audio into a
  128-number fingerprint. A music interval the landmark fingerprints did not name is queried against the LOCAL REFERENCE INDEX (`data/nafp-index/`,
  `cc.py music-index`) in excerpts of 2 minutes (up to 10: another excerpt is tried wherever one fails), and where his words overlap the music and
  nothing was named, again on the analysis step's separated accompaniment (temporary audio, never the output). **It names a song only when that song's
  reference recording is in the index; otherwise UNKNOWN.** The production index starts empty: no commercial song can be named until a reference is
  added (the user's own files, a stream stretch where an identified song plays alone, openly licensed music; never downloaded commercial recordings).
  A match = two consecutive 1 s windows at one offset. Levels: strong 0.90 (identity 90, 95 with four windows), fair 0.67 (80: alone below 85, a
  second independent method is needed). A song matched in two or more excerpts must line up as one continuous playback (within 1 s), otherwise it
  stays at the fair level; two references in one excerpt = AMBIGUOUS (nothing named); other songs matched elsewhere in the interval are listed. A
  reference is never surer than its own label: `--id-score` (required for a stretch of a run) caps every match against it. The
  same method group as the landmark fingerprints (one reference audio: never counted twice). Cached per interval, source and index version
  (`30-assets/music/neural-fp.json`); `music.json` names the matching reference (`index_id`), the level, the source and the consistency.
  Measured 2026-11-21 (`C:\Users\Bulzart\Documents\stream-clips\validation\fingerprint-bench-20261121`: 8 references (5 ACE-Step tracks made on this
  PC, 3 stream songs), 110 queries, never the indexed files themselves, 10,057 null windows): clean 5 s, 2-3 s, MP3 64 kbps, -20 dB, 3 % and 6 %
  faster: all found; not-indexed songs, his talk, game sound, TTS and sound effects: all UNKNOWN; no false or wrong match at any level down to 0.54
  (the two-window rule does the work; highest single wrong score 0.70). At the fair level 0.67 (0.1 % of null windows above it; it was 0.80: song as
  loud as his talk 1/8): the song as loud as his talk 7/8, 6 dB under it 1/8, the -6 dB mixes separated first by Demucs 3/9 and by SAM 5/9. A song
  buried under his talk stays mostly unrecognised. Load 0.7-0.8 s, 0.4-0.7 GB of GPU memory, about 2 ms per window. The real stream: the stretch
  inside an indexed stream reference was named (171 windows, identity 95, outcome C: no claim evidence); the stretch before it under his talk (not in
  the reference) stayed UNKNOWN on the stream audio and on the separated accompaniment. The levels come from one small set: provisional.

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
  fault, never escalated. Neither passes: `UNRESOLVED`, the original audio stays, both attempts recorded. SAM ALWAYS runs in full precision (the
  user, 2026-11-22: "always use the full precision"; the code ignores any other `dtype`): GPU memory counts as committed memory on Windows, about
  12 GB for a short span and more than 13 GB for a 4.6-minute one, so the guard's per-job cap `music.sam.memguard_limit_gb` is 16 GB (raised from
  13 on the user's word; its Windows floors, 1.0 GB free commit and 0.8 GB free RAM, unchanged). Stopped by the guard, there is no lighter retry: the
  span is `UNRESOLVED`, the original audio stays, and the line says to close other programs and run the music step again. (The lighter bfloat16
  mode, measured 2026-11-21 at 5.3 GB of GPU memory instead of 8.3, removed 4-5 dB less of the song under his talk and is never used.) Where nobody
  speaks the gate makes the span quiet, game sound and reactions far from his words included: no method tested removed the song
  there while keeping them (the trade-off is written in each removed line).
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
  +0.2 dB, the song slightly less removed, 8x slower; config `music.model` `htdemucs_ft`); **DBS-TIGER-DnR** (JusperLee, Apache-2.0, 1.0 M parameters,
  4.1 MB, speech / music / effects; installed in `C:\Users\Bulzart\Documents\AI\dnr-sep\.venv`, 1.2 GB of GPU memory, about 14 s per minute):
  talk over a sung song: the song -22.9 dB (voice band -19.5) run per channel, his words 0.59; a laugh kept (-6.9 dB lost against Demucs -8.2, SAM's
  "man speaking" loses the laugh: -0.3); BUT game sound under a song kept no better than SAM's "music playing" removal while removing LESS song (-12.8
  against -15.9 dB), and on the real stream the singer stayed audible before his words (-4.8 to -9 dB against SAM's -65): not adopted. MVSep's DnR v3
  Mel-Band RoFormer: its weights are not published (mvsep.com/algorithms/64 offers it hosted only); not used. SAM Audio Small and Large are not
  installed. The second fingerprint model, **nmfp-triplet** (raraz15/neural-music-fp, ISMIR 2025; installed for the test only in
  `C:\Users\Bulzart\Documents\AI\nmfp`, never called by the toolkit): its readme says AGPLv3 for code and weights, its LICENSE file GPL-3.0, Zenodo
  GPL-3.0-or-later (read as AGPLv3). TensorFlow 2.13 has no GPU on Windows and its spectrogram library (Essentia) no Windows build: run on the CPU
  with Essentia's spectrogram replicated from its source (all 832 weight tensors restored; clean excerpts 0.97). At the same false-alarm rate as
  LAION (`fp_compare.py`, `compare-matched-false-alarm.json`): 6 dB under his talk 6/8 against 2/8 (1 %) and 3/8 against 1/8 (0.1 %), Demucs-separated
  7/9 against 6/9; but SAM-separated 5/9 against 7/9 and sped-up versions 0/6 against 6/6; equal elsewhere; about 40 times slower (64 ms per window
  on the CPU). Not adopted: better only for a song well under his talk, and adding it would bind the toolkit to its licence (the user's decision).


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
   recording: soundtrack_listing). A candidate the evidence contradicts gets its items too: the scores record the contradiction. Once a song is identified at 85+ and a stretch of the stream plays it WITHOUT his talk, add that stretch to the local index (`T music-index
   --from-run RUN --rec A-B --id <short id> --title "..." --artist "..." --id-score <its identity score> --license "the user's stream
   recording"`): from then on it is recognised
   acoustically wherever that recording plays again.
2. *Risk* (only for a recording identified at 85+): reports of YouTube Content ID claims, blocks or restrictions that NAME THIS RECORDING and version,
   the rights holder's own statements, a licence or clearance for YouTube: `T music-evidence --add-risk --rid <rid> --kind <kind> --summary "..."
   --source <URL> --quality verified|credible|unverified [--specific] [--origin <the original source when sites copy one another>] [--date]
   [--region]`. Fame, a release, streaming, a major label or "copyrighted" are not evidence; nothing found is recorded as nothing_found.
3. `T music --edl ... [--apply]` again; the scores are recomputed. Stop when more searching is unlikely to change the decision; never invent a title
   to avoid "unknown".
`T music-evidence --rid <rid>` shows a recording's intervals and scores; `--pending` lists recordings identified at 85+ without risk research.

## The builder's step (long videos; after the EDL is final, before the build; in a Non-Isolation run `T music` answers `bypassed` and there is nothing to do)
1. `T music --run RUN --edl OUT/edl.json` writes `OUT/music.json`: every interval with where it plays in the video, its candidates, both scores, the
   outcome (A-F) and why, the analysis, what research it needs, its status.
2. Name an interval's recording in the EDL's `music` list only where the evidence shows it (`{"rec_from", "rec_to", "title", "artist",
   "confidence": "high|medium|low", "evidence"}`): a weak item (50 at most); never a guessed title. Research is the main session's.
3. `T music --run RUN --edl OUT/edl.json --apply` when a line says `remove` (outcome A): Demucs, and SAM Audio Base for a span Demucs cannot clean;
   when it changed the EDL (`patched`), `T edl-check ... --make-censor` and `T captions` again before the build: `capcut-build` refuses a music patch
   newer than the resolved plan (built without it, the song would stay in). In the plan, the song's stretch plays a SILENT COPY of its chunk
   (`RUN/30-assets/mute`: the picture stream-copied, the same frames at the same times; the sound silent), because CapCut's export plays a clip's
   own sound even at volume 0 (measured 2026-11-22 on LT2: the original stayed under the cleaned audio; the user's fix: mute that part of the
   original before CapCut uses it); the cleaned audio plays on its own lane over it.
   an EDL changed after `--apply` gets `--apply` again (cached: seconds); the patch is replaced, never stacked.
4. The report lists every interval: its output time, removed (with SAM: listen before publishing) / UNRESOLVED / left as it is with its outcome, and
   why. A music line never fails a video and never drops a moment.

## Never
- Never remove or mute music on a guess, because a song sounds famous, because it was recognised, or because the game is known for licensed radio: only
  outcome A changes the audio.
- Never use the analysis audio (the temporary separation) as the output. Never say a video or a song is safe, cleared or claim-free; never call the
  risk index a probability.
- Never use a hosted or paid recognition service, never send audio, fingerprints or embeddings anywhere (the user, 2026-11-21). The lyrics check and
  MusicBrainz send text only. Never fill the index with downloaded commercial recordings; never name a song the index does not hold.
- Never let test evidence count: items and claims labelled FIXTURE (or added by validation / test) are ignored outside a test that sets
  CC_ALLOW_FIXTURES=1; validation runs use their own register file (CC_MUSIC_EVIDENCE), never `data/music-evidence.json`.
- Never run `T music` for a short, never add a music mute or a cleaned lane to a short: shorts keep their audio exactly as recorded.
- Never replace a whole clip's sound when a span is the problem; never hand over cleaned audio that failed its check; never install SAM Audio Large or
  download model weights during a run.

`T music --run RUN --spans "A-B,..."` detects and analyses ahead of the EDLs (`cc-produce` runs it once for every planned span of the LONG videos; it
lists `research`; `--no-analysis` for detection only). `T music-id --run RUN --rec A-B` shows a recognition by hand. `T music-setup` checks the
Demucs separation's Python, weights and a 4 s self-test.
