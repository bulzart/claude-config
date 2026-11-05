## 4 The script (A6s)

`40-briefs/video-NN-script.md` (readable: the beats, the devices used, the sources) and `40-briefs/video-NN-narration.json`, the lines the
voice speaks: `{"video": "NN", "language": "english", "lines": [{"n": 1, "text": "…", "emotion": "neutral", "pause_after": 0.35}, …]}`.

- **The template of the spec**: the hook in the first line (spoken within the first second), every beat in its share, the payoff, the
  closing line or loop; the length from the spec's range at its words per minute (about 2.3–2.8 words per second of speech).
- **Lines**: one sentence or one breath each, as the references break them; a reveal gets its own line and a longer pause before it
  (`pause_after` of the line before, 0.5–0.9 s); the default pause is the config's.
- **Emotion**: `neutral` unless the run's voice holds a clip for that emotion (§6); the wording carries the feeling, since the clone voice
  takes no instruction.
- **Spoken text only**: numbers written as they are said ("nineteen fifty-nine" when the voice must say it so), no stage directions, no
  emoji, no markup.
- **Fact sheet** (factual niches): `40-briefs/video-NN-facts.md`, every claim of the script with its source URLs.
- The copy test (`creative-direction.md` §5.0) and the sharpness gate pass before the script is final.

