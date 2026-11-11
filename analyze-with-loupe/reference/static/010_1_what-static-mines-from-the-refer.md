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

**The run's niche within the set** (the user, 2026-11-09: "references are studied as a whole set and even if i pick a specific niche
but the references are mixed niches, the strategy plan of the next video still is based on leveraging and carefully implementing by the
patterns of the whole references data set but it drived mostly from the niche we chose but without ignoring what it learned from the
whole set patterns and understanding too and leveraging and implementing what it decides to from them too"). When the set mixes
niches, the references of the run's niche (§10; their field read from the cards, the agent's reading with its reason) are the main
source of each video's plan: its hook, telling, devices, retention, emotion, language, engagement, length, pace and pauses come mostly
from them (`T static profile --run RUN --refs <the niche's references>`, within the video's family when the set holds kinds). The
whole set stays the second source and is never ignored: a pattern most of the set shares across its niches is kept unless the niche's
references show otherwise, and where they are too few or silent on a point (one reference, no bed, no call to action), the family's or
the set's pattern decides. Each value of a plan says which it follows, with both numbers ("the niche's 3 references open on a
question, the set's 6 of 9: kept"). A niche no reference is about takes the whole set's craft. The same two sources feed a video's
**approach** (§10, the user, 2026-11-11): the niche's references' approaches first, the whole set's other story families beside them,
and the agent's own where neither fits: the field is the lock, the approach is chosen per video. (The run of 2026-11-06, niche
"Survival scenarios": its survival references V07, V09 and V13 sit in the family F3 of seven; video 03 still took F3's numbers, and
the long pauses show the difference: F3's median 6.3 per 10 minutes, the survival references' 8.8.)
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
- **The pictures**: the seconds each still holds (the median and the range from the edit profile's shots, which read every frame, its
  few-frame shots inside a join left out; A1's `cuts.json` misses many changes of a quiet drawn style: 119 against 259 on one
  reference, 2026-11-08), the style (photoreal, painted, cinematic,
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
- **Drawn annotations** (the user, 2026-11-11: agents that edit a video can draw and animate; his example is a pen sketch of an arm
  with three dashed white curved lines drawn on, frame by frame, from its muscle regions out to the hand-lettered words "Width",
  "Height" and "Depth", and the regions filled red, blue and green): lines, arrows, circles, boxes, coloured highlights and words
  drawn over a still to explain what the voice says, as the frames show them, each with its times: what it points at and says, how
  it is drawn (solid or dashed, straight or curved, its colours, its width against the frame, the lettering of its words), how it
  appears and leaves (drawn on along its path and how fast, wiped, faded, popped, typed), whether it wobbles frame by frame, and how
  long after the spoken word it starts; counted per reference and per minute, read on frames viewed densely (`T frames … --range a-b
  --fps 30 --sheet`). They are not stickers (item 6): a drawing explains the picture, an icon or a badge decorates it.
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
  specificity (dates, sums, names), the humour (deadpan tags, callbacks, irony) and how often it lands, slang, the reading level. The
  language the reference speaks is a fact too (the transcript's detected language, `10-media/<V>/`): the references may be English, or
  a mix, and are all studied the same way, each in its own language (the user, 2026-11-11: "even though all references might be in
  english or mixed, we still analyse them and understand"); their pace numbers count their own unit (words, or characters for a
  language written without spaces) and the set's medians by words leave a reference of the other unit out, with the reason (`T static
  profile`). The patterns are carried to the run's videos in the language each video is made in (§4, §6).
- **Engagement**: each call to action (subscribe, comment, like) with its time and wording, the questions put to the viewer, the ending
  (a loop back to the hook, a teaser of the next video, a question for the comments).
- **Attachment**: what makes a viewer care: a recurring protagonist, the narrator as a persona, the viewer cast as the hero ("POV: you"),
  relatable stakes, aspiration, belonging to an in-group, a character's fall and rise.
- **The social side**: why someone would send it on or comment (a surprising fact to repeat, a usable lesson, identity, nostalgia, a
  harmless argument), the title and thumbnail as a pair (§12), a series or a time-box promise ("in 9 Minutes"), the comment bait.
- **The content style**: a story, an explainer, a list or a scenario; factual or invented; how serious and how playful; the angle on the
  subject (the underdog, the hidden cost, the "what if").
- **The approach** (the user, 2026-11-11, §10): how this reference tells its subject, as the fields a run's video will choose among:
  its story form (counted days, hour by hour, a real case retold, a life path, "what happens if", myth against fact, a guide …), its
  point of view (you, third person, we, an expert), the time frame it counts and the scale it tells at (one person to a species), the
  pillar inside its field (the sub-topic: heat, a book, a battle …) and its title form (§12). One line each, read from the transcript
  and the title; the spec counts them across the set and across the niche's references (§2).
- **Why it holds** [I]: one paragraph per reference, from the facts above: what kept a viewer to the end and what made them come back.
- **The subject**: what each video is about, and what kind of subject it is (a book, a person, an event, a fact list, a story), to be
  left behind (§3), and its field (history, philosophy, psychology …): a candidate for the run's niche, which the user picks at A5 (§10).

