## 2 The Static card and the spec (A3–A4)

**The card** (`20-analysis/cards/<V>.md`, one per reference): the fields of §1 in this order: title and thumbnail · hook · telling
(structure as a beat list with times) · devices · retention · emotion over time · language · pictures (seconds per still, style,
framing, motion, transitions, effects) · captions · sound · engagement · attachment · the social side · content style · approach ·
subject, its kind and its field · why it holds (one paragraph, [I]). Every speech field reads from the transcript.

**The Static spec** (`20-analysis/static-spec.md`, one per run; Static's craft sheet) is the **whole set's** (§1 "The set as a whole"):
after the cards, `T static profile --run RUN` (`20-analysis/set-profile.md`), then every field below written from all the references
together: what recurs (with its count), the numbers as the set's median and range, the differences and what they follow. When the set
holds different kinds (Shorts and long videos, a story and a list), each kind is a family read by its own numbers (`T static profile
--run RUN --refs …`), and a video takes its family's. A value from one reference only is named as that, with the reason no other
reference speaks to it; "V02's template" or "V01's moves" is never the reason for a value of the run. **The niche's references**
(written after A5; §1 "The run's niche within the set"): the spec names the references of the run's niche and, for every field below,
gives their pattern beside the set's and the family's: the niche's numbers are what a video aims at, the others the context they are
read in; a spec written before 2026-11-09 gets this block before the run's next videos are planned.
- **Narration template**: the beats in order with their share of the length (hook 0–5 %, setup, escalation 1…n, the reveal, the payoff,
  the closing line), as the set builds them; the line length; the pace and the pauses (below).
- **The pace** (the user, 2026-11-08: "the narration speed and style should mirror the reference's data patterns ... we have to be very
  sure that the workflow really achieves" it): per family and, within it, for the niche's references, by the fair measure (§6 "The
  pace", §13): the words a minute while articulating (`wpm_articulation`) and overall (`wpm_overall`) as the niche's references' median
  (the point a video aims at; weighed with the family's by the agent when they are too few to carry it alone, §13) beside the family's
  median and range, and the pause pattern (pauses a minute, their median and 90th percentile, the long ones of 0.8 s or more per 10 minutes, their share), all from
  `T static profile --refs <family>`; `wpm_speech` (the older segment reading) only as a fact. Each video's narration JSON carries them
  (§4), the agent checks its plan against them before anything is made (§13), and the narration is aimed at the point by the voice, its tags and the words chosen before it is made, then
  measured (§6).
- **Retention, emotion, language, engagement, attachment, the social side, content style** (§1): each as the set's pattern with its
  counts and numbers (a re-hook every N s, the emotion peaks as shares of the length, "you" and questions a minute, the calls to action
  and where they fall), so the scripts (§4), the pictures (§5) and the edit (§7) follow the set, not one video.
- **Length**: the references' lengths (each, the shortest, the median, the longest: `T static lock --run RUN` lists them) and what their
  length follows, read from the cards: the kind of subject and how much it holds, the number of beats and how long each runs, how deep
  each beat goes, the format (a Short under a minute, a long video of many minutes). The user picks it once, at A5 and before any
  planning, after the niche is locked (the user, 2026-11-12; it replaced 2026-11-07's "the user will not pick any length"): the
  **standard** (the niche's references' median and range from this pattern, each video's own length the agent's from it) or **their
  own** (a total, or a few minutes more or less than the standard, for the batch or per video); `state.json → static.length_plan`.
  Each video's length is then decided at A6s (§4) from the user's pick and this pattern.
- **Seconds per still**: the median and the range the references use; when a still changes (on a new line, on a reveal, mid-line).
- **Niche candidates**: the fields the references are about (§1) and the fields their craft would carry, for the user's pick at A5; a
  candidate is a **field and the kind of stories in it** ("Survival scenarios and how-tos"), never a title wording or one story form
  ("N days of X": that is an approach, below); the pick is the run's niche (`state.json → static.niche`, §10) and every subject comes
  from it.
- **Approaches seen** (the user, 2026-11-11, §10): per story family and for the niche's references, the approaches the cards record,
  counted: the story forms, the points of view, the time frames and scales, the pillars and the title forms ("story form: counted
  days 2 of 3 survival references, hour by hour 1; point of view: you 3 of 3; title forms: 'How …' 2, a time box 1"), so that a
  video's approach is chosen from data (the niche's references' first, the whole set's other story families beside them) and the
  agents can see which approaches the set never shows, where their own may go (§10 "room of their own").
- **Visual styles**: each reference's picture style in a few words and its text look, grouped into the families the set holds, with one
  storyboard sheet per family (its full path), for the user's pick of one reference at A5 (§10).
- **Style lock** (written once the user has picked, A5): one sentence every image prompt of the run carries (the medium, the light, the
  palette, the grain, the era), from the reference the user picked (`state.json → static.style_ref`); a set of one reference: that one.
- **Text look** (the user, 2026-11-05: "the agents are free to chose any font preset, size, color and family or whatever they like while editing the video and are not constrained like we do with recreate"; "everything is data driven (from the references) and nothing is predefined"; never the house text style of the video modes): for the captions and any other text the
  references show, the font (the family seen, or the closest from `T capcut-font --list`, CapCut's own fonts first; when none of the
  listed fonts is a good match for the video, an extra open-licence font may be downloaded: `T fetch-font`, §7 "Extra fonts"), the weight, the
  size in CapCut's units for the export canvas (from the text's height on the frames), the fill, the outline (colour, width), the
  shadow, the box, the case, the words at once, the lines, the position (y_rel, alignment), the highlight (colour, size, which words),
  the entrance (from the edit profile's caption entrances, below). The run's text look is the style reference's when it shows captions
  (§10), else the most common look of the references that have them; every video of the run keeps it.
- **Motion, joins and the caption entrance** (the user, 2026-11-06: "dont set fixed numbers let the agent decide how much to zoom in or
  out, how fast, decide the font popup style and do other edits based on ... what the analyzed data tells"): from the edit profiles, never
  guessed and never a stock value: the moves as the references make them (each kind with its amount and its pace per second, steady or
  eased, how they follow each other), the joins by their signatures and the short shots, the caption entrance by its curve. Then, for each,
  the closest option this PC's CapCut verifiably plays (`AWL/data/capcut-catalogue.md`, §9): the moves CapCut plays, the text intro and
  its seconds whose measured curve is nearest the references' entrance (an intro's curve at another length runs faster or slower), the
  transition (or a cut) whose signature is nearest each kind of join. With the run's CapCut plan free (`state.json → capcut_plan`, the
  user's pick at the start) only options marked free; with pro, the Pro ones too. Name the numbers each choice rests on.
- **Effects** (the user, 2026-11-06: "a folder of effects (optional) that can have: sound effects, and green screen transitions"): the
  references' overlays and sound effects as a pattern (which joins carry an overlay transition and for how long it hides the picture,
  which moments carry a sound and of what kind, their level under the voice, how often), never guessed. With the user's effects folder
  (`state.json → static.effects_folder`, its facts in `00-inventory/effects.md` and its sheets in `10-media/effects/`), the closest files
  for each device by their numbers (a transition's seconds with no green in the canvas's box and its colour, a sound's start, loudest
  moment, length, colour and loudness; view the sheet row of each candidate) and the way CapCut plays each kind that the CapCut effects
  check verified (`AWL/data/capcut-catalogue.md`, Effects). An effect the references never show is used only where it plays the part of a
  device they do show (a green-screen wipe for their quick slide at a turn, a whoosh where their slide carries one); without a folder,
  CapCut's own transitions and no sound effects. Name the numbers each choice rests on.
- **Drawn annotations** (§1; the user, 2026-11-11): the references' drawn layers as a pattern: how often (per minute, and in which
  kinds of moment: a measurement, a mechanism, a comparison, a count, a route), the kinds they use (dashed leaders, arrows, circles,
  highlights, words), their looks as numbers read off the frames (the line width and the dash against the frame's short side, the
  colours, the lettering), how they appear and how fast (the draw-on seconds, the wipe or pop), whether they wobble, their hold, and
  their lead on the spoken word in seconds. The niche's references first, the whole set's beside them (§1 "The run's niche within the
  set"). Where the references draw nothing, the pattern is empty and the video's drawings are the agent's own: allowed wherever the
  narration elaborates something a drawn layer shows better than the still does, inside the run's style lock (§10), each with its
  written reason (§5 "Drawings"); never a sticker, icon or badge.
- **Voice profile**: the numbers of §1 and the delivery in words; the five sample voices are written from it (§6).
- **Bed brief** (§6; a bed goes under every video, also when the references are voice only): the content type and its register, the
  narration's pace, pitch and delivery, the arc the beats make, the pictures' rhythm, and the references' own sound as the audio profile's
  numbers (a bed or none; when one, its tempo, beat strength and energy arc; its instruments and genre are not analysed).
- **Titles and thumbnails** (§12): the titles' pattern (from the file names, or `context.txt`) and, when `context.txt` gives
  thumbnails, the thumbnails' pattern with their size and aspect from `T static context`; without reference thumbnails the thumbnail
  follows the references' hooks and first frames.
- **Devices to reuse**, and **what is left behind**: every reference's subject, its names, its facts, its exact lines, its title and its
  thumbnail.

**The format (A5;** the user, 2026-11-05: the CapCut export is the final, and the images' size and quality are the user's pick, "make sure
to suggest the most correct size first along with options"**).** `T static formats --run RUN` gives the facts: each reference's size and
aspect, the aspects by count and seconds, and per aspect and resolution the export size (the CapCut canvas), the image size that stays
sharp through the stills' moves (`image_size`, each edge times 1 + the move's amount), the smaller one without that margin, and whether
the image API (`image`) and FLUX 3 Klein (`klein`) take each. The question rides in A5's AskUserQuestion call with the count (header
"Formats", multiSelect; the user, 2026-11-08: "the user can chose how much image formats video versions they want to do"): "Which
formats should every video be made in? Each one more is the same video with its own pictures and CapCut project." Its options are
aspects, the best fit first, marked (Recommended): the references' main aspect (the most videos, then the most seconds); then the
other main aspect when the references mix them, else the other of 9:16 and 16:9; then up to two more the facts allow (1:1, 4:5). Each
is offered at 1080 on the short side with the image size with the margin and quality `high` (prompts and Klein mode: no quality); each
description names the export size, the image size and, with the API, the quality, and for a format beyond the first what it adds: its
own stills (with the API their cost again, with Klein their hours again) and its own CapCut project. "Other" takes the rest: another
resolution (720: smaller images, less cost and time; 1440: sharper, slower), `medium` (the API: cheaper, a little less detail), `xhigh`
or `max`, the image size without the margin (slightly soft at the end of a zoom; with Klein also quicker per image), an exact size.
The first picked format in the options' order is the **primary**, stored with
`T static format --run RUN --aspect A --res R [--quality Q] [--image-size WxH]`, which refuses a size the run's image source does not
take (the API's rules; Klein's: edges of a multiple of 16 from 64 to 4096); each other picked format with the same command and
`--also` (`state.json → static.extra_formats`, each with its `tag`: 9:16 is `9x16`). Every later step reads `static.format` for the
primary (the images' size and quality, the prompts file, the project's canvas) and the extra formats' own sizes for theirs
(§2b).
