## 12 The YouTube title and thumbnail (A1, A6s, S3, X10)

The user, 2026-11-07: "in the references folder there is also a context.txt file that has all the real youtube title of each video and
their thumbnails image file path too ... if the video name is how_to_drive_a_car.mp4 then in this file it will be like this
how_to_drive_a_car.mp4|How do you drive a car|C:/users.../how_to_drive.png ... because we will also in the end generate the yt thumbnail
for each video using klein or openai api directly or just prompt (image files stand at /thumbnails folder in the references folder) and
the title too".

The user, later the same day: "we will not have the context.txt file no more because the video already have their name, the pattern is
like this every video is named like "Channel_Name_Video_Title_and_somehashtags"". The tail of such a name is the YouTube video's id (11
letters, digits, `_` or `-`, added by the downloader), not hashtags.

**The references' titles (A1, A3).** `T static context --run RUN`. **Usually (no `context.txt`)** it reads the titles from the file names
`<channel>_<title>_<YouTube id>`: per video the name's words (underscores as spaces), the id-like tail, any `#hashtags`, and the words
every name starts with; `00-inventory/context.md` holds the table. Which words are the channel and which the title is your reading (a
channel name is usually the first one to three words, the same for two videos of one channel; the title is what is left, as YouTube
shows it: `$1 Trillion` with its `$`, a `(` … `)` kept); a name without that pattern (`video.mp4`) carries no title. **A thumbnail** is
the image of the same name beside its video (the user, 2026-11-08: the `.jpg` next to the `.mp4`; or of that name in a `thumbnails`
folder): measured, in the table and on the labelled sheets `10-media/thumbnails/sheet-NN.jpg`; an image of that naming pattern that no
video matches is listed as a thumbnail on its own (its title in its name), studied for the pattern like the others. Without any, the
thumbnail below follows the references' hooks and first frames, at YouTube's 1280x720 (16:9; a 9:16 run's Short keeps 1280x720 too, as
YouTube shows a Short's thumbnail in the feed).
**With a `context.txt`** in the references folder, one line per video, `<video file>|<the real YouTube title>|<its thumbnail's path>`,
it matches each line to the inventory's video by its file name, finds each thumbnail (the path as written, else the file of that name in
the references folder's `thumbnails` folder), measures it, and writes `00-inventory/context.md` (the table) and
`10-media/thumbnails/sheet-NN.jpg` (the thumbnails labelled); it lists the videos without a line, the lines no video matches and the
thumbnails not found. Each card (§1) carries its reference's title (and what its thumbnail shows, when there is one); the spec (§2) the
patterns. The thumbnails are reference material like the videos: studied, never an input image of a generation, never copied.

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
reference's title); its words are the narration's promise, never more than the video keeps. **The title form is the video's** (the user,
2026-11-11, §10: the niche is a family, each video an approach): the `title_form` recorded with the subject (`state.json →
static.video_info`: "How …", "Why …", "N days …", a "you" premise, a question, "The ENTIRE history of …") picks the pattern among the
references' title patterns the spec counts (§2), so a run's titles are not all one wording; the length is the references' in the
language's own unit (about the same content: words, or characters for a language written without spaces) and never over YouTube's 100
characters. **In the video's language** (§6): the title, and the thumbnail's `text` when it has words, are written natively in the
language the video is spoken in, not translated from English; the plan keeps `"title_gloss"` (the English reading) and the thumbnail
`text`'s reading in `why`. A thumbnail word is drawn by the image model only in a script it draws reliably (viewed letter by letter,
below); in one it draws badly the thumbnail is made without the words, its picture carrying the hook, and the README names the words
for the user to put on it (a thumbnail is a picture file, not a CapCut project: no label tool reaches it, and a misdrawn word is never
delivered). The thumbnail follows the thumbnails'
pattern, in the run's style lock (§10: the same look as the video's stills), with its subject's most legible moment (the face and the
feeling, the object, the contrast the hook opens); words on it only when the references' thumbnails carry words, as few as they use,
spelled out exactly in `text` and in the prompt; nothing religious or superstitious (§11), nothing indecent, gory or distressing
(§11b: a face's feeling that reads at a glance, never terror or pain), no sticker, emoji, arrow badge or logo
(item 6), no reference's own picture or subject.

**The click and the words around the video** (the user, 2026-11-13: engagement is thought through first, §4b): the title, the thumbnail and
the first line of the narration make one promise, and the video keeps it. Beyond the title and the thumbnail the agent decides what else
this video needs to be published well, as its niche and subject call for (for example title options, a description with chapters and the
sources, a pinned comment), and writes it into the plan's optional `"publish"` block in whatever form serves (`description`, `chapters`:
`[{"label", "image": <K: its first image>}]`, `pinned_comment`, anything else). X10 writes each as a file in `deliverables/`, giving each
chapter its time from the timeline (its first image's start; YouTube's rules: the first at 0:00, at least three, each at least 10 s long).
Nothing in them is promised that the video does not keep (never more than the narration says), nothing religious or superstitious (§11),
nothing indecent, gory or distressing (§11b), and no emoji or sticker (item 6).

**Making it (S3, the production agent)**: with the stills, by the run's images source: API or FLUX 3 Klein, `T image generate --run RUN
--video NN --thumbnail --size <W>x<H> --prompt-file <file> [--ref <anchor or photo> …]` (the attempt is `thumb-aK`; the one in use is
copied to `deliverables/video-NN-thumbnail.png`, with a 320-pixel copy beside the attempt to view it at feed size; `T image use --run RUN
--video NN --thumbnail --attempt K` picks another); prompts mode: `T image prompts` adds the thumbnail as `vNN-thumb`, and `T image intake`
takes the user's `vNN-thumb` file in.

**QC (§8)**: the thumbnail viewed at full size and at feed size: the subject and the feeling read at a glance; its words, when it has
them, letter by letter as `text` says (a misspelt word is a redraw by QC fixes; FLUX 3 Klein draws short words, a long phrase less
reliably: few words, large); the run's style; nothing of §11 or §11b; nothing of item 6. The title: its words against the video's narration
(it promises what the video keeps).

**The record (X10)**: `deliverables/video-NN-title.txt` (the title on its first line, and its English reading on a second line
beginning "English: " when the video is in another language), the thumbnail in `deliverables/`, and whatever else the plan's `publish`
block carries as files beside them (`video-NN-description.txt` with its chapters' times, `video-NN-pinned-comment.txt`, title options …),
and all of them in the video's README row and its result.json. A video in more than one format (§2b) has one title and one thumbnail, made with the primary and
named in every format's row.
