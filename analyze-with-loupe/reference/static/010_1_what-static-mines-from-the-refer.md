## 1 What Static mines from the references (A3)

The references' storyboards are at **2 fps** flat with their audio (`awl-analyze-prepare`; Static has no effort level, the user,
2026-11-07: "remove the effort idea completely (on static mode), just do 2fps when on static mode"): the frames show the stills, the
transcript shows the telling. **The edit layer is measured at the full frame rate** by `T edit-profile --run RUN --ref <V>`
(`10-media/<V>/edit-profile.json`): at 2 fps a pop-in of a few frames is invisible and a zoom between two samples reads as almost nothing
(2026-11-06: a reference read at 1 fps as
"a slight push-in, no caption animation" zoomed its stills by about 20 %, in and out by turns, and popped every word in). View one caption
entrance and one cut densely (`T frames <file> --out <dir> --range a-b --fps 30 --sheet`) to see what the numbers describe.

**The set as a whole** (the user, 2026-11-08: "the reference datas should be studied as a whole not just pick one of them to "copy" ...
we should try to understand them as a whole, what worked, hooks, emotions, patterns, length, voice speed, visuals, editing, engagement,
mental attachment, social strategy, why it got the viewer hooked, content style, and everything ... the data is what should drive the
video generation not fixated or constrained terms or prefixed values"). Every reference is read with the same fields below, and the
spec (§2) reads them together: what recurs across the set (counted: "5 of 8 hooks open with a question"), what the numbers say as the
set's median and range, what differs and why (a 45 s Short and a 9-minute history are two families, each read by its own numbers), and
what a viewer gets from it. No single reference is the template of a video; the one the user names at A5 sets only the look (§10).
`T static profile --run RUN` gives the measured numbers of every analysed reference side by side with the set's median, lowest and
highest (`--refs V01,V04` for a family): the voice's pace while speaking and overall, the pauses, the pitch, the loudness, the words a
sentence, the questions, "you" and numbers a minute, the first word and the first cut, the seconds a shot, the cuts, the moving shots
and their amounts, the captions a minute, the bed. For every reference, collect as facts with times:

- **The title and the thumbnail** (when the references folder has `context.txt`, §12): the reference's real YouTube title word for word
  and what its thumbnail shows (viewed: the subject, the face and its feeling, the words on it and their look, the colours, the
  layout), from `00-inventory/context.md` and the thumbnail file; how the title, the thumbnail and the first line work together.
- **The hook**: the first line word for word, its time to the first word, what the first still shows, and the promise or the gap it opens
  ("most people never notice…", a number, a question, a shocking claim).
- **The telling**: its structure (setup, escalations, reveals, the payoff, the closing line or loop), the line length, the words per minute,
  the pauses before reveals, the address (you, we, a story in the third person), the register (calm, ominous, playful, urgent).
- **The devices that hold attention**: open loops ("but that was not the strangest part"), numbered lists, cliffhangers, rhetorical
  questions, contrasts, the punchline's form and where punchlines fall, the call to action or the loop back to the hook.
- **The pictures**: the seconds each still holds (the median and the range from `cuts.json`), the style (photoreal, painted, cinematic,
  illustrated, archival, cartoon, anime, vintage …: in words the user can recognise, since one reference's style becomes the run's at A5,
  §10), the framing (faces, wide scenes, objects, text cards), how each still moves (the edit profile's shots:
  the zoom from start to end and per second, the pan in % of the width or height, the pace in the first and the last quarter, steady or
  eased, the jitter; and the order of the moves across the video, in and out by turns, a pan after two zooms …), the joins (the cut
  signatures: a hard cut changes in one frame; a dissolve over many frames with no move; a slide or a push with a large shift; a zoom with
  a scale step; a flash with a brightness peak; a blur with a sharpness dip; and the short shots of a few frames), each join with a
  signature other than a one-frame cut viewed frame by frame (`T frames <file> --out <dir> --range <t-0.1>-<t+0.2> --fps 30 --sheet`)
  before it is named: the numbers cannot tell a slide from an **insert**, another picture flashed for a few frames (2026-11-06: two
  "slides" of 7.4 % per frame with a flash and a dip were a statue and a face in hands shown for 3 frames each, a glimpse at each turn
  of the story; the optical flow read the change of picture as a shift), and
  the effects on top as the frames show them, each with its times: an overlay transition over a cut (a wipe, a paint or ink splash, a
  flash; the cut signature's frames that change and its brightness), light leaks, grain, a vignette, glitches, read densely where a
  signature shows one (`T frames … --range a-b --fps 30 --sheet`); stickers, emojis and badges (a like or subscribe button) are noted and
  never re-made (contract item 6).
- **The text on screen** (the captions and any other text): on screen or not; words at once; where it sits (`ocr.json` rows); its look,
  read on the frames: the font (the family as seen, the weight), the size against the frame, the fill, the outline, the shadow, a box,
  upper case or not, the highlighted words and their colour, how it appears (the edit profile's caption entrances: each word's height,
  width, rise, sideways shift and fill over its first ten frames against where it settles, and the frames it takes); as facts.
- **The sound**: the voice as numbers (`T audio-profile --voice`: pitch, its spread, words per minute, pauses) and as heard words in the
  transcript (gender and age as the voice suggests them are [I]); a music bed or none (the harmonic share outside speech, tempo, the
  energy arc); the sound effects: each hit of the audio profile with its time, whether it lands on a cut, its level against the voice
  and its colour (a whoosh with a slide, a hit on a reveal, a click on a list item, a riser before a payoff), and the moments that carry
  none.
- **Retention**: where curiosity is raised again (a re-hook every so many seconds: its times), the open loops planted and when each is
  paid off, the pattern breaks (an insert, a tonal flip, a joke, a sudden quiet), how the stakes rise, the longest stretch with no new
  question or turn.
- **Emotion over time**: the arc (curiosity, tension, awe, laughter, relief, sympathy, a wince), where each peak falls as a share of the
  length, and how the words, the voice (pace, pitch, pauses), the pictures and the bed carry it; how often the mood turns.
- **The language**: the person and the tense, the words a sentence, the questions, "you" and numbers a minute (`T static profile`), the
  specificity (dates, sums, names), the humour (deadpan tags, callbacks, irony) and how often it lands, slang, the reading level.
- **Engagement**: each call to action (subscribe, comment, like) with its time and wording, the questions put to the viewer, the ending
  (a loop back to the hook, a teaser of the next video, a question for the comments).
- **Attachment**: what makes a viewer care: a recurring protagonist, the narrator as a persona, the viewer cast as the hero ("POV: you"),
  relatable stakes, aspiration, belonging to an in-group, a character's fall and rise.
- **The social side**: why someone would send it on or comment (a surprising fact to repeat, a usable lesson, identity, nostalgia, a
  harmless argument), the title and thumbnail as a pair (§12), a series or a time-box promise ("in 9 Minutes"), the comment bait.
- **The content style**: a story, an explainer, a list or a scenario; factual or invented; how serious and how playful; the angle on the
  subject (the underdog, the hidden cost, the "what if").
- **Why it holds** [I]: one paragraph per reference, from the facts above: what kept a viewer to the end and what made them come back.
- **The subject**: what each video is about, and what kind of subject it is (a book, a person, an event, a fact list, a story), to be
  left behind (§3), and its field (history, philosophy, psychology …): a candidate for the run's niche, which the user picks at A5 (§10).

