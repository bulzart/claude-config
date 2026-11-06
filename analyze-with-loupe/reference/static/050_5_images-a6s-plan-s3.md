## 5 Images (A6s plan, S3)

**The image plan** `40-briefs/video-NN-images.json`: `{"video": "NN", "transition": "fade", "music": true,
"captions": {"y_rel": 0.72, "words": 3, "font_file": "<a file from T capcut-font --list>", "size": 12, "fill": "#FFFFFF",
"stroke_color": "#000000", "stroke_width": 0.08, "shadow": false, "box_color": null, "bold": true, "case": "upper", "highlight_color":
"#FFE14D", "highlight_words": ["…"], "animation": "pop-up"}, "characters": [{"id": "C1", "name": "…", "photo": "<path or null>", "sheet_prompt": "<when no
photo>"}], "images": [{"image": 1, "from_line": 1, "prompt": "…", "characters": ["C1"], "motion": "zoom-in", "transition": "cut",
"line": "<the words over it>"}, …]}`. The size and quality are the run's format (`state.json → static.format`, picked at A5, §2); a
plan's own `"size"` changes it for that video only. `captions` is the spec's text look (§2) with this video's highlighted words: the CapCut
project and the check copy both take it.

- **Count and cuts**: an image starts on a narration line (`from_line`); the spec's seconds per still decide how many lines one image
  covers. A reveal, a new place or a new person starts a new image. After the narration exists, `T slideshow plan` gives every image's
  span; keep each within the spec's range (none under about 2 s).
- **The prompt**: what the image shows at that moment of the story (the subject, the action, the place, the time of day), the framing, the
  style lock of the spec word for word, then the composition for the run's aspect (`static.format.aspect`; vertical: the main subject in
  the upper two thirds; horizontal: the subject on a third with room around it; square: centred), the band where the captions sit (the
  plan's y_rel) free of faces and key detail, no text, letters, numbers, logos or watermarks in the picture unless the
  story needs a sign or a page (then the exact words), no added sticker or emoji (contract item 6).
- **Characters**: a character with a photo is the photo as a reference image of every image that shows them; one with only a description
  first gets an **anchor**: a neutral sheet image (`T image generate --anchor C1`, the look in words), viewed and kept, then used as the
  reference of every image that shows them. The prompt names who is who ("the man in the first image").
- **API mode** (`static_images=api`): `T image generate --run RUN --video NN --image K --prompt-file <file> [--ref <photo or anchor> …]`
  (the size and quality from the run's format); the toolkit sends it through the ledger, saves `60-outputs/video-NN/images/iKK-aM.png` and marks it the one the edit uses. A request
  that already made an image is not sent again (`--again` for a new draw). `moderation_blocked`: change the prompt (or the reference), never
  send it again unchanged.
- **Klein mode** (`static_images=klein`): the same `T image generate` (the size from the run's format; no quality); FLUX 3 Image Klein
  makes it on this PC, one image at a time, ledgered with provider `klein` and no cost. The prompt is written as for the API; Black Forest
  Labs' prompt upsampler turns it into the full scene caption the model takes (the answer's `caption`). A character's photo or anchor
  rides as a reference (at most 10). The seed comes from the request and the attempt and is recorded; `--again` draws with a new one.
- **Prompts mode** (`static_images=prompts`): `T image prompts --run RUN` writes `deliverables/prompts/video-NN-image-prompts.md` (the
  characters' sheets first, then one prompt per image with its file name `vNN-iKK`, the character to attach, and the format's aspect and size); the user makes
  them, puts them in one folder and sends its path; `T image intake --run RUN --folder <path>` copies them in (never moves or changes
  them) and lists what is missing, extra or named twice.

