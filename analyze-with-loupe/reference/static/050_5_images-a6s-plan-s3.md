## 5 Images (A6s plan, S3)

**The image plan** `40-briefs/video-NN-images.json`: `{"video": "NN", "music": true, "music_gain": <the bed's level, kept after its
check, §6>,
"captions": {"y_rel": <from the spec>, "words": <n>, "font_file": "<a file from T capcut-font --list>", "size": <n>, "fill": "#…",
"stroke_color": "#…", "stroke_width": <n>, "shadow": false, "box_color": null, "bold": true, "case": "upper", "highlight_color": "#…",
"highlight_words": ["…"], "animation": "<a text intro slug the catalogue shows drawn>", "animation_s": <seconds>, "word_box": <null, or
the spoken word's box (§7): {"color": "#…", "alpha": <0-1>, "round_radius": <0-1>, "style": 0, "gap_em": <the words' gap>, "pad": <the
box past its word, CapCut's 0.14 by default>, "v_offset": <the box's vertical offset; CapCut boxes the descent too, so it sits low at 0>,
"why": "…"}>, "min_words": <null, or with a word box the fewest words a caption shows: each caption filled to `words` across commas
and short pauses, never across a long pause (0.8 s), a short last group joining the one before it>},
"characters": [{"id":
"C1", "name": "…", "photo": "<path or null>", "sheet_prompt": "<when no photo>"}], "images": [{"image": 1, "from_line": 1, "prompt": "…",
"characters": ["C1"], "motion": "<zoom-in | zoom-out | pan-left | pan-right | pan-up | pan-down | none>", "amount": <the change>,
"transition": "<cut | a transition slug the catalogue shows drawn>", "trans_s": <seconds>, "line": "<the words over it>"}, …],
"effects": [<with an effects folder, below>], "title": "<the video's YouTube title, §12>", "thumbnail": {"prompt": "…", "size":
"<W>x<H>", "text": "<its exact words, or null>", "characters": ["C1"], "why": "…"}}` (the title and the thumbnail: §12). Every value
in `<…>` is decided from the spec (no stock value exists: `T slideshow plan` lists what is undecided). The size and quality are the run's
format (`state.json → static.format`, picked at A5, §2); a plan's own `"size"` changes it for that video only. `captions` is the spec's
text look (§2) with this video's highlighted words: the CapCut project takes it. With more than one format (§2b) the plan is the primary's, and an extra format's own values sit in `"by_format": {"<tag>": {…}}`: the plan's `captions`
(`size`, `y_rel`) and `labels_style`, an image's `labels`, `scale`, `x`, `y` (and, in prompts mode only, a `prompt` the swaps do not fit).

- **Moves and joins** (the spec's measured pattern, §2): each image's `motion` with its `amount` (a zoom's change: 0.2 zooms from 1.0 to
  1.2 or back; a pan travels the margin of a scale of 1 + amount), or its own `scale`, `x` and `y` pairs at its start and end (scale 1 =
  the picture covers the canvas; x and y in half-canvas units, y up, as CapCut keys them) for a pan with a slow zoom or a zoom toward a
  corner. The amount is the reference's pace per second times this still's seconds, and the moves follow the references' order (in and out
  by turns, a pan where they pan). Each join's `transition` and `trans_s` are a cut or the transition whose signature matches the
  references' join; the caption `animation` and `animation_s` are the intro whose curve matches their entrance (data/capcut-catalogue.md;
  only what it shows drawn). `T slideshow plan` gives each image's `moves`, lists an edge that would show (`edges_show`) and every
  decision left out (`undecided`).

- **Effects** (only with the user's effects folder, as the spec's effects pattern says, §2): the plan's `"effects": [{"id": "<FXnnn of
  00-inventory/effects.md, or "file": a path>", "type": "<overlay | sfx>", "join": <K: the cut into image K> | "line": <N: narration line
  N's start> | "at_s": <seconds on the video>, "anchor_s": <the second of the file that lands on that moment>, "in_s": <optional: where in
  the file it starts>, "dur_s": <optional; an image needs it>, "why": "<the reference's device and the numbers it rests on>", …}]`. An
  **overlay** also has `"blend": "<chroma | screen | normal>"` (chroma: the key colour taken out, `key_color` from the scan's `key green`
  and `key_intensity` from the catalogue's verified one unless given; screen: a black background vanishes, light adds; normal: as it is,
  its own transparency kept), `"fit": "<cover | contain>"` (cover fills the canvas: a 16:9 file on 9:16 shows only the box outlined on its
  sheet; contain shows it whole), `"volume": <0 mutes; required when the file has sound>`, and optional `"scale"`, `"x"`, `"y"` (a
  number, or keys `[[seconds from the overlay's start, value], …]` for a pop or a slide; scale 1 = as fit, x and y in half-canvas units,
  y up) and `"opacity"`. A **sfx** has `"volume"` and optional `"fade_in_s"`, `"fade_out_s"`. The anchor is a fact of the file, not a
  taste: a green-screen transition's cut sits inside its `no green` seconds (their middle, so the box is hidden on both sides of the cut);
  a sound's `starts` or `loudest at` lands on its moment (a click file with half a second of silence before it has `starts` 0.53).
  Effects that overlap go on separate tracks (`fx1`, `fx2`, `sfx1` …); a file used twice is fine. `T slideshow plan` lists every effect
  setting the plan left out in `undecided`, and nothing has a stock value. Never a sticker, emoji, icon or badge as an overlay (a like or
  subscribe button, an arrow), even when the folder holds one (contract item 6): overlays are transitions and treatments of the whole
  picture (a wipe, a flash, a light leak, grain, a glow).

- **Count and cuts**: an image starts on a narration line (`from_line`); the spec's seconds per still decide how many lines one image
  covers. A reveal, a new place or a new person starts a new image. A long video holds many (12 minutes at 5 s a still: about 144); its
  images are then made by several agents, each a stretch of them (`awl-analyze-produce` A9b). After the narration exists, `T slideshow plan` gives every image's
  span; keep each within the spec's range (none under about 2 s). An **insert** the references use (a picture flashed for a few frames
  at a turn, §1) is an image of its own with `"from_line"` of the line it leads into and `"offset_s"`: minus its length (−0.1 for 3
  frames at 30 fps), its own number after the others (the timeline follows the starts), `"motion": "none"` unless the reference's insert
  moves; `T slideshow plan` lists it under `shorter_than_0_5s` as a fact. Its picture is a glimpse in the run's subject (the reference's
  device, never its picture: §3).
- **The prompt**: what the image shows at that moment of the story (the subject, the action, the place, the time of day), the framing, the
  style lock of the spec word for word (the style reference's look, the same in every video of the run: §10), then the composition for
  the run's aspect (`static.format.aspect`; vertical: the main subject in
  the upper two thirds; horizontal: the subject on a third with room around it; square: centred; people placed at different depths only
  in a scene that has people), the band the captions will take (the plan's y_rel) described only by what it shows ("the bottom fifth
  shows only the wooden floor"); these frame words are written the same way in every prompt of the video, so an extra format swaps
  them with the same `--swap` pairs (§2b), no text, letters, numbers, logos or watermarks in the picture unless the
  story needs a sign or a page (then the exact words), no added sticker or emoji (contract item 6), and a secular scene described in
  positive terms with nothing religious or superstitious in it (§11: a palace throne hall, never a cathedral; a "red X" mark, never a
  "red cross"; the prompt names what is there, never what must stay out). Every person is dressed for the scene with the clothes named
  from top to bottom, and the moment shown is never an undressed, injured or agonised one (§11b: "A cool shower." is the shower running
  in the empty bathroom, or the man after it, dressed, his hair wet; a medical moment shows the care, never the harm; a survival pose
  low on the ground shows the person clearly alive in it: head up or turned so the open eyes show, mid-move). One picture,
  never a split picture, a side-by-side or panels
  (§8): two ideas share one place (2026-11-07: "a split picture" of a full hotel and an empty spare room came back as two panels with a
  seam; one street with the hotel and the house next door read as one scene). A map is centred on the region its pins mark and says
  where they stand, not the places' names (2026-11-07: the cities' names were written onto the map, one over the wrong continent, and
  pins "in western Europe" on a whole world map landed on the United States; centred on Europe they landed on Europe); the names go
  onto it as CapCut text (Labels below).
- **Labels** (the user, 2026-11-07: a map's place names "as CapCut text"): a picture whose places the line names (a map with pins, a
  route) carries the names as CapCut texts over it, never drawn by the model. Once the image is made and viewed, its plan entry gets
  `"labels": [{"text": "London", "x_rel": 0.47, "y_rel": 0.33}, …]`: each label's centre read off the picture as shares of its width
  and height from the top left, beside the pin or place it names (not on it), inside the frame and above the caption band, spelled as
  the narration says it (an extra format's places are read off its own still into `by_format.<tag>.labels`, §2b). The plan gets one
  `labels_style` for the video: `font_file`, `size`, `fill`, `stroke_color`, `stroke_width`,
  `shadow` (the run's text look's font and colours unless the plan says why not; `T slideshow plan` lists any left out as undecided). A
  label stays where it is put and does not follow a move, so an image with labels has the motion `none` (`T slideshow plan` lists any
  that moves in `labels_on_moving_images`). A label on a pin that sits in the wrong place makes the error plain: the pins are checked
  against the places first (§8), and a wrong pin is a redraw reason by QC fixes.
- **No subtitle-like text, ever** (the user, 2026-11-07: "try to push no captions or subtitles style text in any image generation at
  all, it can have text over objects, books, logos, brands, inside screens, or whatever, just not subtitles style text whatsoever"):
  a prompt never holds the words caption, subtitle, lower third, title bar or text overlay, not even to keep a band clear: the model
  reads them as a request and draws a line of made-up letters across the bottom (2026-11-07: eleven stills whose prompts said "where
  captions sit"); `T image generate` lists any such word it finds in its answer (`prompt_overlay_words`), and a prompt that has one is
  rewritten before it is sent again. Every prompt ends on one clean-picture sentence in the style lock's medium: "Nothing is laid over
  the picture: it is one clean illustration from edge to edge." (a photoreal lock: "one clean photograph"; a painted one: "one clean
  painting"). Words appear only on the things that carry them in the scene (a sign, a page, a screen, a
  logo, a package), and a name stays out of the prompt unless it is meant to be written (a cast's names in a prompt got written onto
  a cheque).
- **Scale and depth**, when a character's reference image rides with other people, animals or buildings in the frame: the models tend to
  draw the referenced character larger than the rest (2026-11-06: an emperor three times the size of the courtier seated behind him, a
  horse and rider towering over the soldiers, a pony-sized horse merging into his coat). Say each one's real size and place in words: life-size, the
  same height as, seated behind him, in the background, a full-sized horse he leads by the reins.
- **Characters**: a character with a photo is the photo as a reference image of every image that shows them; one with only a description
  first gets an **anchor**: a neutral sheet image (`T image generate --anchor C1`, the look in words), viewed and kept, then used as the
  reference of every image that shows them. The prompt names who is who ("the man in the first image"). Every character rides with
  their own anchor where the memory fits them (the user, 2026-11-07: "Separate where it fits"): FLUX 3 Klein takes every reference at
  1 MP, so before a still with three or more characters `T image fit --run RUN --n-refs N` gives the free commit memory against what N
  references need on this PC (their measured peak plus the memory guard's floor). A negative headroom means the guard would stop it
  (on this PC it stopped every still with 3-4 references, 2026-11-07), and the still then rides with one **cast sheet** (`T image cast
  --run RUN --ids C2,C3,C4`: their anchors cropped side by side), the prompt describing each by look from left to right, never by name.
  A cast sheet costs composition (the same day: the people kept its front-facing lineup in 13 stills, and 4 came back as the sheet
  itself instead of the scene), so every still made with one is viewed for that. Every image copies the anchor's
  details, so view it for an ornament that reads as a letter or symbol (braid loops, embroidery, a pattern): it comes back in every image
  (2026-11-06: lapel braid loops read as a repeated "N"). The sheet prompt names the ornament plainly ("plain straight gold braid").
- **Real things look like themselves** (the user, 2026-11-07: "if there's a company, or a brand being talked about, their logo should
  appear somewhere, or if talking about famous person whos appeareance is known it should really look like them, and so on"; "we need
  to let the viewer watching the video have more context about who we're talking about"):
  - **A company, brand or product** the story is about or names at length gets its official logo in the stills: where the story first
    brings it in (its founding, its first mention) and at least once more later (a later chapter, the payoff), so the viewer knows whom
    the video is about. The file comes from an official source (the company's brand or press page, or Wikimedia Commons: `T fetch-image
    --run RUN --kind logo --name <brand>-logo --commons "File:…"` records its licence and author; `--url` for a direct PNG), and the
    image model never draws it (it redraws a logo wrong): the plan's image gets `"logo": {"brand": "<name>", "file":
    "<30-assets/brand/…>", "surface": "<what carries it: a banner, a sign, a screen, a box>"}` and its prompt describes that surface
    plain and blank ("a large plain white banner across the tent's front edge, completely blank"). Once the image is made and viewed,
    `T image brand --run RUN --video NN --image K --logo <file> --box x0,y0,x1,y1 [--card]` places the file on that surface (the box read
    off the picture, outside the caption band; `--card` paints a flat card first when something there must be hidden) as the next attempt,
    the generated one kept; an extra format's still gets its own (`--format <tag>`, the box read off that still). The present logo tells the viewer who even in an earlier year; a dated logo, when the official archive holds
    it, tells when: the agent's call, written in the plan. Another brand's mark the model drew on its own (a fruit on a laptop, a label)
    is painted over with `--cover x0,y0,x1,y1`.
  - **A known person** (whose appearance is public: a founder, a leader, an artist) is drawn to look like them, in the run's style lock:
    two or three public photos (the user's assets first; else ones whose licence allows reuse, from Wikimedia Commons or an official press
    page: `T fetch-image --kind photo`) ride with their anchor (`T image generate --anchor C1 --ref <photo> …`; the sheet prompt names
    their real look at the story's time: face shape, hair, build, glasses, signature clothes), and the anchor is checked against the
    photos (§8). They appear only in what the fact sheet sources, never in a degrading, sexual or violent scene they were not part of.
  - **A known place or thing** (a landmark, a product, a vehicle, a building) looks like itself: its real features in words, and a photo
    as a reference where the model would guess; nothing of §11 (a religious landmark is left out of the pictures).
- **API mode** (`static_images=api`): `T image generate --run RUN --video NN --image K --prompt-file <file> [--ref <photo or anchor> …]`
  (the size and quality from the run's format); the toolkit sends it through the ledger, saves `60-outputs/video-NN/images/iKK-aM.png` and marks it the one the edit uses. A request
  that already made an image is not sent again (`--again` for a new draw). `moderation_blocked`: change the prompt (or the reference), never
  send it again unchanged. An extra format's still (§2b): `T image generate --run RUN --video NN --image K --format <tag>
  --same-as-primary [--swap "<frame words>" "<this frame's words>" …]`, saved in `60-outputs/video-NN/<tag>/images/`.
- **Klein mode** (`static_images=klein`): the same `T image generate` (the size from the run's format; no quality); FLUX 3 Image Klein
  makes it on this PC, one image at a time, ledgered with provider `klein` and no cost. The prompt is written as for the API; Black Forest
  Labs' prompt upsampler turns it into the full scene caption the model takes (the answer's `caption`). An anchor skips the upsampler
  (it would add props every later image copies), so its sheet prompt is the full description itself. A character's photo or anchor
  rides as a reference (at most 10). The seed comes from the request and the attempt and is recorded; `--again` draws with a new one.
  The model's peak sits a few hundred MB from the memory guard's floor on this PC: a job the guard stops is run once more by the
  toolkit once the commit memory is back (`memory_retry` in the answer). When the free commit memory is short, `--reserve-vram GB`
  holds more of the GPU back for that call (config `static.klein.reserve_vram_gb`, 5, otherwise): the job commits less, the picture is
  the same, the call is slower (2026-11-09 at 10.6 GB free: 9 GB let a still with no reference through in 452 s instead of about 90 s;
  a still with one reference was still stopped at 7.7 GB); the agent's call from the free memory, recorded in each attempt; image calls run in the foreground (Claude Code ends background
  commands when memory runs low, and their GPU lock with them), and one image agent works at a time (three at once stopped a third of
  the stills, 2026-11-07). While it makes images nothing else heavy runs on this PC, the main session included: no test suite, no second
  image call, no model load (2026-11-07: the toolkit's tests run beside the images were one cause of six guard stops).
  Every Klein prompt says the picture is one continuous scene from a single camera viewpoint filling the whole frame, above all one with
  no reference image: the upsampler may otherwise lay a tall frame out as stacked panels (2026-11-06: an image with no reference came back
  as two pictures with a hard seam; with that sentence the seven after it were single scenes).
- **Prompts mode** (`static_images=prompts`): `T image prompts --run RUN` writes `deliverables/prompts/video-NN-image-prompts.md` (the
  characters' sheets first, then one prompt per image with its file name `vNN-iKK`, the character to attach, and the format's aspect and size); the user makes
  them, puts them in one folder and sends its path; `T image intake --run RUN --folder <path>` copies them in (never moves or changes
  them) and lists what is missing, extra or named twice. An extra format (§2b): `T image prompts --run RUN --format <tag> [--swap … …]`
  (the same prompts, its frame words swapped, named `vNN-<tag>-iKK`) and `T image intake --run RUN --folder <path> --format <tag>`.

