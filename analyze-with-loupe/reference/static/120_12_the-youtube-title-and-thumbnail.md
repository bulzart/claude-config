## 12 The YouTube title and thumbnail (A1, A6s, S3, X10)

The user, 2026-11-07: "in the references folder there is also a context.txt file that has all the real youtube title of each video and
their thumbnails image file path too ... if the video name is how_to_drive_a_car.mp4 then in this file it will be like this
how_to_drive_a_car.mp4|How do you drive a car|C:/users.../how_to_drive.png ... because we will also in the end generate the yt thumbnail
for each video using klein or openai api directly or just prompt (image files stand at /thumbnails folder in the references folder) and
the title too".

**The references' titles and thumbnails (A1, A3).** `T static context --run RUN` reads `context.txt` in the references folder, one line
per video, `<video file>|<the real YouTube title>|<its thumbnail's path>`, matches each line to the inventory's video by its file name,
finds each thumbnail (the path as written, else the file of that name in the references folder's `thumbnails` folder), measures it, and
writes `00-inventory/context.md` (the table) and `10-media/thumbnails/sheet-NN.jpg` (the thumbnails labelled). It lists the videos
without a line, the lines no video matches and the thumbnails not found. Without the file there are no real titles or thumbnails, and the
title and the thumbnail below follow the references' hooks and first frames. Each card (§1) carries its reference's title and what its
thumbnail shows; the spec (§2) the patterns. The thumbnails are reference material like the videos: studied, never an input image of a
generation, never copied.

**The patterns** (the spec, A4), as facts from the titles and the thumbnails viewed one by one (and the sheets):
- **Titles**: the length in words and characters, the hook form (a question, a number, a bold claim, a "how", a name, a time promise),
  the case and the punctuation, the words that recur, how the title and the video's first line relate.
- **Thumbnails**: their size and aspect (`T static context` gives them: the run's thumbnails are made at the size most of them have;
  without them, YouTube's own 1280x720), the layout (one subject or several, its size and place, a face and its expression, the
  background), the text on them (none, or how many words, their size against the frame, colours, outline, where), the colours and the
  contrast, how they read at phone-feed size, and how each relates to its title (the same promise, or the half the title leaves open).

**The plan (A6s)**: each video's image plan carries `"title": "<the video's YouTube title>"` and
`"thumbnail": {"prompt": "<the picture>", "size": "<W>x<H>", "text": "<its exact words, or null>", "characters": ["C1"], "why": "<the
pattern each choice follows>"}`. The title follows the titles' pattern for this video's subject and hook, written fresh (never a
reference's title); its words are the narration's promise, never more than the video keeps. The thumbnail follows the thumbnails'
pattern, in the run's style lock (§10: the same look as the video's stills), with its subject's most legible moment (the face and the
feeling, the object, the contrast the hook opens); words on it only when the references' thumbnails carry words, as few as they use,
spelled out exactly in `text` and in the prompt; nothing religious or superstitious (§11), no sticker, emoji, arrow badge or logo
(item 6), no reference's own picture or subject.

**Making it (S3, the production agent)**: with the stills, by the run's images source: API or FLUX 3 Klein, `T image generate --run RUN
--video NN --thumbnail --size <W>x<H> --prompt-file <file> [--ref <anchor or photo> …]` (the attempt is `thumb-aK`; the one in use is
copied to `deliverables/video-NN-thumbnail.png`, with a 320-pixel copy beside the attempt to view it at feed size; `T image use --run RUN
--video NN --thumbnail --attempt K` picks another); prompts mode: `T image prompts` adds the thumbnail as `vNN-thumb`, and `T image intake`
takes the user's `vNN-thumb` file in.

**QC (§8)**: the thumbnail viewed at full size and at feed size: the subject and the feeling read at a glance; its words, when it has
them, letter by letter as `text` says (a misspelt word is a redraw by QC fixes; FLUX 3 Klein draws short words, a long phrase less
reliably: few words, large); the run's style; nothing of §11; nothing of item 6. The title: its words against the video's narration
(it promises what the video keeps).

**The record (X10)**: `deliverables/video-NN-title.txt` (the title on its first line), the thumbnail in `deliverables/`, and both in the
video's README row and its result.json.
