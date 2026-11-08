## 6 The voice and the bed (A6s, S2)

**The voice** (the run's engine, the user's pick at the start, `state.json → static_tts`: `local` = Qwen3-TTS 1.7B on this PC, bf16,
design then clone; `alibaba` = Alibaba Cloud Model Studio's `qwen-audio-3.1-tts-plus` on the user's key, below): one voice per run, the
same in every video, locked once picked (§10): more videos of the run and a clone that keeps it make no new samples; the toolkit refuses
a new design or pick without `--replace`. The sample line names nothing religious or superstitious (§11). The steps below are the same
for both engines; what differs with Alibaba is in its own paragraph.
- Five samples at the stop of A6s (the user, 2026-11-06: "the agent should suggest 5 versions and also the file path for each of them so
  the user can hear them and pick the one they like to be the voice of the videos"): five voice descriptions written from the spec's
  voice profile (gender, age, tone, pace, accent; the references' register, five different takes on it), all speaking one line in the
  references' style: `T tts design --run RUN --text "<line>" --instruct "<voice 1>" … --instruct "<voice 5>"` (one sample per
  `--instruct`). The stop lists each with the full path of its file (`T tts design` prints them); the user listens and picks.
- The pick becomes the run's voice: `T tts voice --run RUN --sample K`, plus at most two emotion clips when the spec's delivery swings
  (`--emotion tense="<a line that carries it>"`): the same voice speaking that line, used as the reference for lines tagged with it
  (with Alibaba: the delivery in words, below).
- **Strong lines** (§4; the user, 2026-11-05: "make strong lines with the voice-design model instead, though the voice may shift slightly
  from line to line"): `T tts say` makes a line marked `strong` with the VoiceDesign model, from the run's voice description word for word
  plus the line's `delivery`, with the picked sample's seed (`state.json → static.voice.seed`, or the line's own `seed`), so the timbre
  stays as close as the model allows. The sidecar gives every line's pitch against the run's voice (`pitch_st`, semitones) and its timbre
  similarity (`timbre_sim`, 0 to 1), and `voice_match` the cloned lines' spread. A strong line more than a semitone outside the cloned
  lines' pitch range, or under their lowest timbre similarity, is made again with another seed (the line's `seed`, then `--only N`), at
  most twice; still apart, it becomes a cloned line (`strong` false, its emotion clip when the voice has one), noted in the brief.
- A video's narration: `T tts say --run RUN --video NN` (every line, the pauses, the loudness); `T narration-words --run RUN --video NN`
  (the timed words, the cues, the SRT, and per line what was heard against the script). A line that came out wrong (a missing or repeated
  word, the start repeating the reference's words, another speaker) is made again: `T tts say --only N`, at most twice, then noted.
- The narration starts `lead_s` after the first frame and the video ends `tail_s` after it (config `static.narration`).

**The pace** (the user, 2026-11-08: "the narration speed and style should mirror the reference's data patterns, if the data tells that
the best speed is 160 words with pauses and 178-191 while speaking per minute then thats what we should use too ... we have to be very
sure that the workflow really achieves a 178-191 words a minute"; "if qwen 3.1 plus for example has the speed feature or word per minute
then set it up in the model, only do manual tweaks if the model does not provied with what we want to achieve"). The narration JSON's
`pace` (§4: words a minute while speaking and overall, the set's bands, §2) and `pause_default_s` drive `T tts say`:
- every line's silent edges are trimmed, so the pause between lines is exactly the planned one (a line's `pause_after`, else
  `pause_default_s`);
- **the model's own speed setting first**: Alibaba's `rate` (0.5 to 2.0), set from the voice's own speed (learned from its last
  narration, `state.json → static.voice.native_wpm_speech`, else read off its sample); when the measure misses the band, every line is
  made once more at the corrected setting (billed again; the voice's learned speed makes the next video right the first time);
- **a tempo afterwards only for what the model did not reach**, and for every line of a model without a speed setting (Qwen3-TTS on
  this PC has none): one factor for all lines, ffmpeg's rubberband with the pitch and the formants kept; a factor outside 0.85 to 1.35
  is named (`tempo_outside_clean_range`: the voice is far from the set's pace; a voice described nearer it, or picked nearer it, needs
  less);
- the default pause is set so the words a minute overall land in their band (a line's own `pause_after` stays);
- after every pass the joined narration is measured with **the references' own yardstick** (faster-whisper's words and segments, read the
  way A1 read them: words a minute from the first word to the last, and over the spoken segments only), at most four passes. The
  sidecar's `pace` holds the target, every pass, the measure, `within` and the method; `T narration-words` reads the pace again from its
  own transcription. A narration outside its band after the passes is a fact for the brief and the agent's call (another voice nearer
  the set's pace), never shipped as if it matched.
The made lines stay as they came (`video-NN/line-NN.wav`); the paced ones are in `video-NN/paced/`, and the image spans and the captions
follow the paced narration. A narration is never stretched to fit a length: the length comes from the words at the set's pace (§4).

**With Alibaba** (`static_tts=alibaba`; the user, 2026-11-08: "add qwen 3.1 tts plus from the alibaba provider and the user will just
provide with the api key when they pick it over our local model, the workflow will be the same"). The key is the user environment
variable `DASHSCOPE_API_KEY` (§9); nothing runs on this PC's GPU, so no memory guard or GPU wait applies.
- **The five samples**: the same `T tts design` command; each description becomes a voice designed at Alibaba (at most 500 characters)
  that says the sample line (at most 200 characters, English or Chinese); its preview is the sample file and its voice id is kept
  beside it. A run in another language makes the samples on this PC (`T tts design --engine local`), and the pick is cloned at Alibaba
  from its file (cloning works best on 10 to 20 s of speech: write a sample line that long). Voice creation is free; the voices stay on
  the user's account (1,000 per account).
- **The pick**: `T tts voice --run RUN --sample K` makes it the run's voice once Alibaba answers that it is usable (a designed sample as
  it is, a local one cloned). With this engine `--emotion NAME="<the delivery in words>"` is the instruction sent with every line tagged
  NAME, not a line to speak.
- **The lines**: `T tts say` makes each line in that voice, a few at a time. A line's `delivery` (a strong line's), else its emotion's
  instruction, goes with it as Alibaba's instruction, and its `seed` (else the voice's) as the seed. A strong line keeps the same voice
  and only its delivery changes, so it stays close to the others; `voice_match` and the strong-line check above still apply. The same
  pauses, loudness pass, sidecar and `T narration-words` follow.
- **Cost**: per character (`config.json → static.tts.alibaba.price_usd_per_10k_chars`, about US$0.30 per 10,000 in Singapore; a
  9-minute narration of about 6,700 characters is about US$0.20). The sidecar and each answer record the characters and the estimate. A
  line made again is billed again: `--only N` makes only those lines, and a run that stopped part way names the missing ones.

**The bed** (ACE-Step 1.5): an instrumental under every video, also when the references are voice only (the user, 2026-11-06: "make
sure we try to generate instrumentals that fit the video content type and narration based on the data collected from the references, no
need to analyze their instrumentals too"). It is written from what the run already knows, never from analysing the references' music:
- **the content type**: the kind and niche of the references and of this video's subject (a life story, quick facts, a kids' story, a
  true case, a myth …): the palette;
- **the narration**: the spec's register and delivery in words (calm, wry, warm, ominous …), its pace (words per minute, the pauses) and
  the voice's pitch: the music leaves the narrator's band clear (no lead melody or busy part where the voice sits) and has no vocals,
  and nothing sacred or ritual (no hymn, choir singing sacred words, chant or church organ: §11);
- **the story's arc over time**: this video's beats (its script) at the narration's line times (the hook, the rise, the turn, the fall
  or payoff, the close) and each line's emotion: where the bed holds, builds, drops or darkens;
- **the pictures' rhythm**: the seconds per still and the cuts (§2), which a pulse can sit under without fighting;
- **the references' own sound, as the numbers A3 already has** (`T audio-profile`: a bed or none; when one, its tempo, beat strength and
  energy arc): a reference bed's tempo and energy are followed; its instruments and genre are not analysed.
Reason from these to the caption, as these worked examples do, never as a lookup: a brisk, wry life story with a rise and a fall → a
light orchestral underscore with a march pulse that swells to the peak and darkens with low strings at the fall (the run of 2026-11-06:
100 bpm under a 175-words-a-minute narrator); a calm bedtime story → soft celesta, harp and warm strings, slow and even, no drums; a dark
true case → low drones and sparse piano on a slow pulse that tightens at the reveal; quick surprising facts → light plucked and mallet
sounds, curious and bouncy. `40-briefs/music.json` (A6s), one track per video:
`{"tracks": [{"video": "NN", "caption": "<genre, mood and its arc, instruments, tempo in words; no vocals>", "duration": <lead +
narration + tail, set in S2>, "bpm": <n>, "seed": <n>, "why": "<each choice and the data it rests on>"}]}`, then in S2 `T music make
--run RUN` (every track in one model load; instrumental). The file carries its own fades (the track's `fade_in`, `fade_out`) and is
saved as 16-bit PCM WAV, the format the CapCut effects check showed playing (ACE-Step writes 32-bit float; the toolkit converts it).
**A long bed** (the user, 2026-11-07: "if acestep 1.5 max is 10 minutes, then we could do 2x8minutes for a 16minutes video i guess, or
5x5 for a 25 minutes"): ACE-Step makes at most 600 s per piece on this PC (`config.json → static.music.max_s`), so a longer track is made
in sections and joined end to end with crossfades (`crossfade_s`, default 4 s) into the one file the edit uses: either the agent's own
`"sections": [{"caption": "<this part's mood, the same instruments and tempo>", "duration": <s>}, …]` (one per part of the story: the
rise, the turn, the fall; the section lengths add up to the track's duration plus one crossfade per join), or, without them, the fewest
equal sections of at most `max_section_s` (480 s) under the track's caption. The fade-in is on the first section, the fade-out on the
last; the pieces stay in `30-assets/music/parts/`. `T music measure`'s level per second shows each join: no drop or jump around it.

**The bed's check and level** (S2): `T music measure --run RUN --video NN` gives the facts: the words speech-to-text hears in the bed
alone (a voice where none was asked), its loudness, its level per second and over each narration line (does it build and drop where the
beats do), its energy by band, and, as the CapCut project plays it (one constant gain, no ducking), its distance under the narration and
the narration's words heard with it against without it. The level is the agent's: every narration word heard the same with the bed
under it, and the bed still heard in the pauses; another level is tried with `--gain G` and kept as the image plan's `music_gain` (with
`"music": true`; else `config.json → static.music.gain`). A voice in the bed, or an arc that fights the story, is a new take (another
seed or a reworded caption, `T music make --run RUN --video NN`), at most two, by the run's QC fixes (off: none, noted in the brief). The
CapCut project, the only edit (no local render, §7), plays the bed at that gain without ducking (no CapCut ducking was checked), which is
the level the measure judged.

