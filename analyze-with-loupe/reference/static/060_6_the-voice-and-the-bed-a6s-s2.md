## 6 The voice and the bed (A6s, S2)

**The voice** (Qwen3-TTS 1.7B, bf16, design then clone): one voice per run, the same in every video, locked once picked (§10): more
videos of the run and a clone that keeps it make no new samples; the toolkit refuses a new design or pick without `--replace`. The
sample line names nothing religious or superstitious (§11).
- Five samples at the stop of A6s (the user, 2026-11-06: "the agent should suggest 5 versions and also the file path for each of them so
  the user can hear them and pick the one they like to be the voice of the videos"): five voice descriptions written from the spec's
  voice profile (gender, age, tone, pace, accent; the references' register, five different takes on it), all speaking one line in the
  references' style: `T tts design --run RUN --text "<line>" --instruct "<voice 1>" … --instruct "<voice 5>"` (one sample per
  `--instruct`). The stop lists each with the full path of its file (`T tts design` prints them); the user listens and picks.
- The pick becomes the run's voice: `T tts voice --run RUN --sample K`, plus at most two emotion clips when the spec's delivery swings
  (`--emotion tense="<a line that carries it>"`): the same voice speaking that line, used as the reference for lines tagged with it.
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

**The bed's check and level** (S2): `T music measure --run RUN --video NN` gives the facts: the words speech-to-text hears in the bed
alone (a voice where none was asked), its loudness, its level per second and over each narration line (does it build and drop where the
beats do), its energy by band, and, as the CapCut project plays it (one constant gain, no ducking), its distance under the narration and
the narration's words heard with it against without it. The level is the agent's: every narration word heard the same with the bed
under it, and the bed still heard in the pauses; another level is tried with `--gain G` and kept as the image plan's `music_gain` (with
`"music": true`; else `config.json → static.music.gain`). A voice in the bed, or an arc that fights the story, is a new take (another
seed or a reworded caption, `T music make --run RUN --video NN`), at most two, by the run's QC fixes (off: none, noted in the brief). The
check render ducks the bed under the voice; the CapCut project plays it at the gain without ducking (no CapCut ducking was checked).

