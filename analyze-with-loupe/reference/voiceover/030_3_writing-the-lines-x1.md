## 3. Writing the lines (X1)

- The lines belong to the concept (an A6 seed, or the free plan's lines): who says them (an on-camera character, or an off-screen voice), the
  job each does (hook, turn, product beat, call to action), in the run's language. **overlay** lines are always narration: nobody on screen
  says them. The copy test and the guardrails apply to the words as to the picture: no reference's lines, no claim a guardrail forbids, no
  result or health promise the client's documents do not allow.
- **Length budget.** About 2.3 to 2.8 spoken words per second for an energetic social read (fewer for a slow, warm one), counted on the
  spoken words; keep the first 0.3 s and the last 0.5 s of the planned length free of speech. Too many words come back rushed or long: cut
  words, never squeeze the read. **native** keeps a take within 15 s per generation (the driving models' audio limit).
- **Dialect and accent.** A dialect is written into the words themselves (Kosovar Albanian: the Gheg forms a Prishtina speaker uses: *me ju
  tregu*, *tash*, *veç*, *krejt*, *e lodhun*, *osht*); an accent goes in an accent tag at the start of the take (`[Scottish accent]`), and a
  voice whose accent label matches was offered at the start. A tag moves an accent only part of the way: say so in the brief.
- **Emotion tags** (Eleven v3 and v4): one bracketed tag before the words it colours, from the delivery the beat needs (`[excited]`,
  `[curious]`, `[warmly]`, `[softly]`, `[whispers]`, `[sighs]`, `[laughs softly]`, `[confident]`), at most one per sentence, never inside a
  word. Punctuation shapes the pauses: an ellipsis (…) holds a beat, a dash turns quickly.
- Numbers, prices and units are written as words in the run's language; the product name is spelled the way it is said (in the script
  only, never on screen).
- The take's script is `40-briefs/video-NN[-cK]-voiceover.txt`: exactly the text sent to ElevenLabs, tags included, nothing else. The plan's
  Voiceover block quotes it with one English line when the language is another.
- **Source `file`:** the words are the file's: the user's script when given ([U]), else `T voiceover record --transcribe` writes them
  (faster-whisper, local; the file is a client asset, so the audio-ingest choice of item 24 does not apply to it), marked [I] in the plan.

