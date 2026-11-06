## 2 The Static card and the spec (A3–A4)

**The card** (`20-analysis/cards/<V>.md`, one per reference): the fields of §1 in this order: hook · telling (structure as a beat list with
times) · devices · pictures (seconds per still, style, framing, motion, transitions, effects) · captions · sound · subject and its kind ·
what makes it work (one paragraph, [I]). Every speech field reads from the transcript.

**The Static spec** (`20-analysis/static-spec.md`, one per run, the synthesis of all cards; Static's craft sheet):
- **Narration template**: the beats in order with their share of the length (hook 0–5 %, setup, escalation 1…n, the reveal, the payoff,
  the closing line), the length range in seconds, the words per minute, the line length, the pause pattern.
- **Seconds per still**: the median and the range the references use; when a still changes (on a new line, on a reveal, mid-line).
- **Style lock**: one sentence every image prompt of the run carries (the medium, the light, the palette, the grain, the era), from what
  the references share; a reference set that mixes styles gives the most common one, or the user's choice when the plan asks.
- **Text look** (the user, 2026-11-05: "the agents are free to chose any font preset, size, color and family or whatever they like while editing the video and are not constrained like we do with recreate"; "everything is data driven (from the references) and nothing is predefined"; never the house text style of the video modes): for the captions and any other text the
  references show, the font (the family seen, or the closest from `T capcut-font --list`, CapCut's own fonts first), the weight, the
  size in CapCut's units for the export canvas (from the text's height on the frames), the fill, the outline (colour, width), the
  shadow, the box, the case, the words at once, the lines, the position (y_rel, alignment), the highlight (colour, size, which words),
  the entrance (from the edit profile's caption entrances, below). A set that mixes looks gives the most common one.
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
- **Voice profile**: the numbers of §1 and the delivery in words; the three sample voices are written from it (§6).
- **Bed brief** (§6; a bed goes under every video, also when the references are voice only): the content type and its register, the
  narration's pace, pitch and delivery, the arc the beats make, the pictures' rhythm, and the references' own sound as the audio profile's
  numbers (a bed or none; when one, its tempo, beat strength and energy arc; its instruments and genre are not analysed).
- **Devices to reuse**, and **what is left behind**: every reference's subject, its names, its facts and its exact lines.

**The format (A5;** the user, 2026-11-05: the CapCut export is the final, and the images' size and quality are the user's pick, "make sure
to suggest the most correct size first along with options"**).** `T static formats --run RUN` gives the facts: each reference's size and
aspect, the aspects by count and seconds, and per aspect and resolution the export size (the CapCut canvas), the image size that stays
sharp through the stills' moves (`image_size`, each edge times 1 + the move's amount), the smaller one without that margin, and whether
the image API (`image`) and FLUX 3 Klein (`klein`) take each. The question rides in A5's AskUserQuestion call with the count (header
"Format"). Its first option is the best fit, marked (Recommended): the references' main aspect (the most videos, then the most seconds)
at 1080 on the short side, the image size with the margin, quality `high` (prompts and Klein mode: no quality). Up to three more, each
differing in one thing, from the facts: 720 (smaller images, less cost and time), `medium` (the API: cheaper, a little less detail), the
other main aspect when the references mix them, or the image size without the margin (slightly soft at the end of a zoom; with Klein
also quicker per image). Each option's description names the export size, the image size and, with the API, the quality; "Other" takes
the rest (another aspect, `xhigh` or `max`, an exact size). The answer is stored with
`T static format --run RUN --aspect A --res R [--quality Q] [--image-size WxH]`, which refuses a size the run's image source does not
take (the API's rules; Klein's: edges of a multiple of 16 from 64 to 4096). Every
later step reads `state.json → static.format`: the images' size and quality, the prompts file, the project's canvas, the check render.

