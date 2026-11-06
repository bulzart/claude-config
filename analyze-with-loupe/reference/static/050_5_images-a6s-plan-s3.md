## 5 Images (A6s plan, S3)

**The image plan** `40-briefs/video-NN-images.json`: `{"video": "NN", "music": true,
"captions": {"y_rel": <from the spec>, "words": <n>, "font_file": "<a file from T capcut-font --list>", "size": <n>, "fill": "#…",
"stroke_color": "#…", "stroke_width": <n>, "shadow": false, "box_color": null, "bold": true, "case": "upper", "highlight_color": "#…",
"highlight_words": ["…"], "animation": "<a text intro slug the catalogue shows drawn>", "animation_s": <seconds>}, "characters": [{"id":
"C1", "name": "…", "photo": "<path or null>", "sheet_prompt": "<when no photo>"}], "images": [{"image": 1, "from_line": 1, "prompt": "…",
"characters": ["C1"], "motion": "<zoom-in | zoom-out | pan-left | pan-right | pan-up | pan-down | none>", "amount": <the change>,
"transition": "<cut | a transition slug the catalogue shows drawn>", "trans_s": <seconds>, "line": "<the words over it>"}, …]}`. Every value
in `<…>` is decided from the spec (no stock value exists: `T slideshow plan` lists what is undecided). The size and quality are the run's
format (`state.json → static.format`, picked at A5, §2); a plan's own `"size"` changes it for that video only. `captions` is the spec's
text look (§2) with this video's highlighted words: the CapCut project and the check copy both take it.

- **Moves and joins** (the spec's measured pattern, §2): each image's `motion` with its `amount` (a zoom's change: 0.2 zooms from 1.0 to
  1.2 or back; a pan travels the margin of a scale of 1 + amount), or its own `scale`, `x` and `y` pairs at its start and end (scale 1 =
  the picture covers the canvas; x and y in half-canvas units, y up, as CapCut keys them) for a pan with a slow zoom or a zoom toward a
  corner. The amount is the reference's pace per second times this still's seconds, and the moves follow the references' order (in and out
  by turns, a pan where they pan). Each join's `transition` and `trans_s` are a cut or the transition whose signature matches the
  references' join; the caption `animation` and `animation_s` are the intro whose curve matches their entrance (data/capcut-catalogue.md;
  only what it shows drawn). `T slideshow plan` gives each image's `moves`, lists an edge that would show (`edges_show`) and every
  decision left out (`undecided`).

- **Count and cuts**: an image starts on a narration line (`from_line`); the spec's seconds per still decide how many lines one image
  covers. A reveal, a new place or a new person starts a new image. After the narration exists, `T slideshow plan` gives every image's
  span; keep each within the spec's range (none under about 2 s).
- **The prompt**: what the image shows at that moment of the story (the subject, the action, the place, the time of day), the framing, the
  style lock of the spec word for word, then the composition for the run's aspect (`static.format.aspect`; vertical: the main subject in
  the upper two thirds; horizontal: the subject on a third with room around it; square: centred), the band where the captions sit (the
  plan's y_rel) free of faces and key detail, no text, letters, numbers, logos or watermarks in the picture unless the
  story needs a sign or a page (then the exact words), no added sticker or emoji (contract item 6).
- **Scale and depth**, when a character's reference image rides with other people, animals or buildings in the frame: the models tend to
  draw the referenced character larger than the rest (2026-11-06: an emperor three times the size of the pope crowning him, a horse and
  rider towering over the soldiers, a pony-sized horse merging into his coat). Say each one's real size and place in words: life-size, the
  same height as, seated behind him, in the background, a full-sized horse he leads by the reins.
- **Characters**: a character with a photo is the photo as a reference image of every image that shows them; one with only a description
  first gets an **anchor**: a neutral sheet image (`T image generate --anchor C1`, the look in words), viewed and kept, then used as the
  reference of every image that shows them. The prompt names who is who ("the man in the first image"). Every image copies the anchor's
  details, so view it for an ornament that reads as a letter or symbol (braid loops, embroidery, a pattern): it comes back in every image
  (2026-11-06: lapel braid loops read as a repeated "N"). The sheet prompt names the ornament plainly ("plain straight gold braid").
- **API mode** (`static_images=api`): `T image generate --run RUN --video NN --image K --prompt-file <file> [--ref <photo or anchor> …]`
  (the size and quality from the run's format); the toolkit sends it through the ledger, saves `60-outputs/video-NN/images/iKK-aM.png` and marks it the one the edit uses. A request
  that already made an image is not sent again (`--again` for a new draw). `moderation_blocked`: change the prompt (or the reference), never
  send it again unchanged.
- **Klein mode** (`static_images=klein`): the same `T image generate` (the size from the run's format; no quality); FLUX 3 Image Klein
  makes it on this PC, one image at a time, ledgered with provider `klein` and no cost. The prompt is written as for the API; Black Forest
  Labs' prompt upsampler turns it into the full scene caption the model takes (the answer's `caption`). An anchor skips the upsampler
  (it would add props every later image copies), so its sheet prompt is the full description itself. A character's photo or anchor
  rides as a reference (at most 10). The seed comes from the request and the attempt and is recorded; `--again` draws with a new one.
  Every Klein prompt says the picture is one continuous scene from a single camera viewpoint filling the whole frame, above all one with
  no reference image: the upsampler may otherwise lay a tall frame out as stacked panels (2026-11-06: an image with no reference came back
  as two pictures with a hard seam; with that sentence the seven after it were single scenes).
- **Prompts mode** (`static_images=prompts`): `T image prompts --run RUN` writes `deliverables/prompts/video-NN-image-prompts.md` (the
  characters' sheets first, then one prompt per image with its file name `vNN-iKK`, the character to attach, and the format's aspect and size); the user makes
  them, puts them in one folder and sends its path; `T image intake --run RUN --folder <path>` copies them in (never moves or changes
  them) and lists what is missing, extra or named twice.

