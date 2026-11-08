## 4 The script (A6s)

`40-briefs/video-NN-script.md` (readable: the beats, the devices used, the sources) and `40-briefs/video-NN-narration.json`, the lines the
voice speaks: `{"video": "NN", "language": "english", "pace": {"wpm_speech": [<low>, <high>], "wpm_overall": [<low>, <high>], "why":
"<the set's numbers>"}, "pause_default_s": <the set's median pause>, "lines": [{"n": 1, "text": "…", "emotion": "neutral",
"pause_after": <only where the set pauses longer, before a reveal>}, …]}`. The pace and the pauses are the spec's (§2, the set's
numbers); `T tts say` brings the narration to them and measures it (§6 "The pace").

- **The length** is the agent's, per video, from the spec's length pattern (§2), never asked of the user: where this subject sits among
  the references (a subject with as much to tell as their longest runs as long; one beat-light subject as short as their shortest), the
  beats the template needs and how long the references let each run. It is written into `video-NN-narration.json` as
  `"target_length_s"` with `"length_why"` (the references' numbers it rests on), and the script is sized to it.
- **The template of the spec**: the hook in the first line (spoken within the first second), every beat in its share, the payoff, the
  closing line or loop; the length: the target, as the words at the plan's overall pace (the middle of `pace.wpm_overall`: words =
  seconds × words a minute / 60; 530 s at 165 words a minute is about 1,460 words), since the narration is brought to that pace whatever
  the voice's own speed (§6). A spelled-out year or number counts as the words it is spoken as ("eighteen twelve" is two). (Before the
  pace was set, 2026-11-06 to 11-08, scripts were sized at the voice's own speed, which ran about 12 % under its sample's: video 02 of
  the run of 2026-11-06 said 1,154 words in 530 s, 131 words a minute against the set's 160–174.)
- **Lines**: one sentence or one breath each, as the references break them; a reveal gets its own line and a longer pause before it
  (`pause_after` of the line before, 0.5–0.9 s); the default pause is the config's.
- **Emotion**: most lines `neutral`, the voice's own delivery, the wording carrying the feeling; a line tagged with an emotion the run's
  voice holds a clip for (§6) takes that clip's tone. A **strong** line (`"strong": true, "delivery": "<the feeling in words, e.g. quiet
  disbelief, slower, a catch in the voice>"`) is made by the voice-design model (§6), for the peaks only (the user, 2026-11-05: "not make
  big strong emotion changes unexpectedly, but yeah make room for it"): where the references' narrator peaks (the hook's turn, the reveal,
  the payoff), at most one line in five and never two in a row unless the references do; its delivery in the references' register (no
  shouting a reference never does); the line before leads into it (its wording, a pause, a tense clip) and the line after comes back down,
  so the feeling never jumps unannounced.
- **Spoken text only**: numbers written as they are said ("nineteen fifty-nine" when the voice must say it so), no stage directions, no
  emoji, no markup.
- **No religion and no superstition** (§11): no line names or alludes to either; a fact that needs one to be told is cut or told without
  it. The subject is the run's niche (§10), told in the references' craft.
- **Fact sheet** (factual niches): `40-briefs/video-NN-facts.md`, every claim of the script with its source URLs.
- The copy test (`creative-direction.md` §5.0) and the sharpness gate pass before the script is final.

