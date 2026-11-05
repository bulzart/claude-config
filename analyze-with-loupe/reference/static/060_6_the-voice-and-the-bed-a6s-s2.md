## 6 The voice and the bed (A6s, S2)

**The voice** (Qwen3-TTS 1.7B, bf16, design then clone): one voice per run, the same in every video.
- Three samples at the stop of A6s: three voice descriptions written from the spec's voice profile (gender, age, tone, pace, accent; the
  references' register, three different takes on it), all speaking one line in the references' style:
  `T tts design --run RUN --text "<line>" --instruct "<voice 1>" --instruct "<voice 2>" --instruct "<voice 3>"`. The user listens and picks.
- The pick becomes the run's voice: `T tts voice --run RUN --sample K`, plus at most two emotion clips when the spec's delivery swings
  (`--emotion tense="<a line that carries it>"`): the same voice speaking that line, used as the reference for lines tagged with it.
- A video's narration: `T tts say --run RUN --video NN` (every line, the pauses, the loudness); `T narration-words --run RUN --video NN`
  (the timed words, the cues, the SRT, and per line what was heard against the script). A line that came out wrong (a missing or repeated
  word, the start repeating the reference's words, another speaker) is made again: `T tts say --only N`, at most twice, then noted.
- The narration starts `lead_s` after the first frame and the video ends `tail_s` after it (config `static.narration`).

**The bed** (ACE-Step 1.5), only when the spec says the references use one: `40-briefs/music.json`
`{"tracks": [{"video": "NN", "caption": "<genre, mood, instruments, tempo in words>", "duration": <lead + narration + tail>, "bpm": 80}]}`,
then `T music make --run RUN` (every track in one model load; instrumental). It goes under the voice ducked, at the plan's gain.

