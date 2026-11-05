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
  the animation (pop-up, fade-in, typewriter …). A set that mixes looks gives the most common one.
- **Motion and transitions**: which moves and how strong, which transitions, which effects on top.
- **Voice profile**: the numbers of §1 and the delivery in words; the three sample voices are written from it (§6).
- **Bed**: yes (mood, genre, instruments, tempo, level under the voice) or no, from the references' sound.
- **Devices to reuse**, and **what is left behind**: every reference's subject, its names, its facts and its exact lines.

**The format (A5;** the user, 2026-11-05: the CapCut export is the final, and the images' size and quality are the user's pick, "make sure
to suggest the most correct size first along with options"**).** `T static formats --run RUN` gives the facts: each reference's size and
aspect, the aspects by count and seconds, and per aspect and resolution the export size (the CapCut canvas), the image size that stays
sharp through the stills' moves (`image_size`, each edge times 1 + the move's amount), the smaller one without that margin, and whether
the image API takes each. The question rides in A5's AskUserQuestion call with the count (header "Format"). Its first option is the best
fit, marked (Recommended): the references' main aspect (the most videos, then the most seconds) at 1080 on the short side, the image size
with the margin, quality `high` (prompts mode: no quality). Up to three more, each differing in one thing, from the facts: 720 (smaller
images, less cost and time), `medium` (cheaper, a little less detail), the other main aspect when the references mix them, or the image
size without the margin (slightly soft at the end of a zoom). Each option's description names the export size, the image size and, with
the API, the quality; "Other" takes the rest (another aspect, `xhigh` or `max`, an exact size). The answer is stored with
`T static format --run RUN --aspect A --res R [--quality Q] [--image-size WxH]`, which refuses a size the image API does not take. Every
later step reads `state.json → static.format`: the images' size and quality, the prompts file, the project's canvas, the check render.

