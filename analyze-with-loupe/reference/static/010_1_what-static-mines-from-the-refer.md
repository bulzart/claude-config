## 1 What Static mines from the references (A3)

The references' storyboards are at **1 fps** with their audio (`awl-analyze-prepare`): the frames show the stills, the transcript shows the
telling. **The edit layer is measured at the full frame rate** by `T edit-profile --run RUN --ref <V>` (`10-media/<V>/edit-profile.json`):
at 1 fps a pop-in of a few frames is invisible and a zoom between two samples reads as nothing (2026-11-06: a reference read at 1 fps as
"a slight push-in, no caption animation" zoomed its stills by about 20 %, in and out by turns, and popped every word in). View one caption
entrance and one cut densely (`T frames <file> --out <dir> --range a-b --fps 30 --sheet`) to see what the numbers describe. For every
reference, collect as facts with times:

- **The hook**: the first line word for word, its time to the first word, what the first still shows, and the promise or the gap it opens
  ("most people never notice…", a number, a question, a shocking claim).
- **The telling**: its structure (setup, escalations, reveals, the payoff, the closing line or loop), the line length, the words per minute,
  the pauses before reveals, the address (you, we, a story in the third person), the register (calm, ominous, playful, urgent).
- **The devices that hold attention**: open loops ("but that was not the strangest part"), numbered lists, cliffhangers, rhetorical
  questions, contrasts, the punchline's form and where punchlines fall, the call to action or the loop back to the hook.
- **The pictures**: the seconds each still holds (the median and the range from `cuts.json`), the style (photoreal, painted, cinematic,
  illustrated, archival, cartoon), the framing (faces, wide scenes, objects, text cards), how each still moves (the edit profile's shots:
  the zoom from start to end and per second, the pan in % of the width or height, the pace in the first and the last quarter, steady or
  eased, the jitter; and the order of the moves across the video, in and out by turns, a pan after two zooms …), the joins (the cut
  signatures: a hard cut changes in one frame; a dissolve over many frames with no move; a slide or a push with a large shift; a zoom with
  a scale step; a flash with a brightness peak; a blur with a sharpness dip; and the short shots, a flash or a slide of a few frames), and
  the effects on top (grain, vignette, light leaks, glitches) as the frames show them.
- **The text on screen** (the captions and any other text): on screen or not; words at once; where it sits (`ocr.json` rows); its look,
  read on the frames: the font (the family as seen, the weight), the size against the frame, the fill, the outline, the shadow, a box,
  upper case or not, the highlighted words and their colour, how it appears (the edit profile's caption entrances: each word's height,
  width, rise, sideways shift and fill over its first ten frames against where it settles, and the frames it takes); as facts.
- **The sound**: the voice as numbers (`T audio-profile --voice`: pitch, its spread, words per minute, pauses) and as heard words in the
  transcript (gender and age as the voice suggests them are [I]); a music bed or none (the harmonic share outside speech, tempo, the
  energy arc); sound effects on cuts (hits on cuts).
- **The subject**: what each video is about, and what kind of subject it is (a book, a person, an event, a fact list, a story), to be
  left behind (§3).

