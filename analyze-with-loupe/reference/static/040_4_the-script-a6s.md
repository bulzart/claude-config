## 4 The script (A6s)

`40-briefs/video-NN-script.md` (readable: the beats, the devices used, the sources) and `40-briefs/video-NN-narration.json`, the lines the
voice speaks: `{"video": "NN", "language": "english", "lines": [{"n": 1, "text": "…", "emotion": "neutral", "pause_after": 0.35}, …]}`.

- **The template of the spec**: the hook in the first line (spoken within the first second), every beat in its share, the payoff, the
  closing line or loop; the length from the spec's range: the words at the run's voice's pace plus every pause. The picked sample's
  `words_per_s` (`state.json → static.voice`) runs about 12 % faster than its cloned narration (2026-11-06: the sample 2.9 words per
  second, the narration 2.5, so a script sized at the reference narrator's pace came out at 45 s against the spec's 30–40 s); a
  spelled-out year or number counts as the words it is spoken as ("eighteen twelve" is two).
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

