## 6 The voice and the bed (A6s, S2)

**The voice** (Qwen3-TTS 1.7B, bf16, design then clone): one voice per run, the same in every video.
- Three samples at the stop of A6s: three voice descriptions written from the spec's voice profile (gender, age, tone, pace, accent; the
  references' register, three different takes on it), all speaking one line in the references' style:
  `T tts design --run RUN --text "<line>" --instruct "<voice 1>" --instruct "<voice 2>" --instruct "<voice 3>"`. The user listens and picks.
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

**The bed** (ACE-Step 1.5), only when the spec says the references use one, or the user asks for one (their word outranks the spec; the
user, 2026-11-06, on a voice-only reference: "lets also generate some instrumental over the capcut project ... with acestep 1.5"):
`40-briefs/music.json`
`{"tracks": [{"video": "NN", "caption": "<genre, mood, instruments, tempo in words>", "duration": <lead + narration + tail>, "bpm": 80}]}`,
then `T music make --run RUN` (every track in one model load; instrumental). The file carries its own fades (the track's `fade_in`,
`fade_out`) and is saved as 16-bit PCM WAV, the format the CapCut effects check showed playing (ACE-Step writes 32-bit float; the toolkit
converts it). The image plan takes it with `"music": true` and `music_gain` (else `config.json → static.music.gain`). The check render
ducks it under the voice; the CapCut project plays it at that gain without ducking (no CapCut ducking was checked).

