## 2b More than one format (A5, S3, S4, X10)

The user, 2026-11-08: "if they pick both options then we should use the same plan we have for 16:9 such as narration, story, hooks,
and literally everything that the pipeline decides to do but also in a 9:16 image version too (same image prompts too, but just 9:16)
so we end up generating 2 video formats for the same content (2 capcut projects too, each one of them in their format)".

The user picks one format or more at A5 (§2). The first picked is the **primary** (`state.json → static.format`); each other one is an
**extra format** (`static.extra_formats`, each with its `tag`: 9:16 is `9x16`), and every image, slideshow and capcut-* command works
on it with `--format <tag>`. Every format is the same video: the subject, the script, the narration, the bed, the image plan (its
lines, prompts, moves, joins and effects), the cuts on the same lines, the captions' words and look, the title and the thumbnail are
made once, for the primary, and every format uses them. An extra format has of its own only what its frame changes:
- **Its stills** (S3): each the primary's still made again at its size from the same request: `T image generate --run RUN --video NN
  --image K --format <tag> --same-as-primary` sends the prompt and the reference images the primary's still in use was made with
  (followed back past a placed logo), with `--swap "<words>" "<words>"` for each phrase that names the primary's frame: its shape
  ("Wide 16:9 frame" → "Tall 9:16 frame"), the main subject's place across it, the band kept for the captions (at that format's
  `y_rel`). The same pairs serve every still whose prompt words its frame the same way (§5); every other word stays, and a phrase the
  prompt lacks stops the call before anything is sent. A still the swaps do not fit (its scene laid out across a wide frame) gets a
  prompt of its own (`--prompt-file`, the same `--ref`s): the same scene, only its layout changed, and why in the brief. Its files are
  in `60-outputs/video-NN/<tag>/` (`images/`, `images.json`). Its checks are the primary's (§8): each still viewed, `T image text
  --format <tag>`, the plan's logos placed again on its own picture (`T image brand --format <tag>`, the box read off it), redraws by
  QC fixes. Prompts mode: `T image prompts --run RUN --format <tag> [--swap … …]` writes the same prompts at its size
  (`video-NN-<tag>-image-prompts.md`, names `vNN-<tag>-iKK`; an image's `by_format.<tag>.prompt` where the swaps do not fit), and
  `T image intake --run RUN --folder <path> --format <tag>` takes only those names in.
- **What sits at a point of its picture** (S4), in the image's `by_format.<tag>` in the plan, read off its own still: the labels'
  places (`"labels"`, §5) and a zoom aimed at a spot (`"scale"`, `"x"`, `"y"`). Without them `T slideshow plan --format <tag>` lists a
  labelled image as undecided, and an aimed zoom plays its plain `motion` and `amount` (listed in `moves_aimed_in_the_first_format`:
  view it and aim it there when the spot matters).
- **Its captions' size and band** (the plan's `by_format.<tag>.captions`: `size` and `y_rel`, both required; the rest of the text look
  stays the run's): from the references in that aspect when the set has them, else the same text height against the frame's shorter
  side as the primary's (a phone shows each format with that side across it), in a band clear of that frame's subjects (a vertical
  frame's bottom fifth sits under the apps' own titles and buttons).
- **Its timeline, CapCut project and record**: `T slideshow plan --run RUN --video NN --format <tag>`
  (`40-briefs/video-NN-timeline-<tag>.json`; its captions in `60-outputs/video-NN/<tag>/`), `T capcut-name --video NN --format <tag>`
  (`DD_Mon_YYYY_vNN-<tag>`), the canvas at its export size, `--format <tag>` on `T capcut-motion`, `capcut-transitions`,
  `capcut-effects` and `capcut-labels` (§7); in the record (X10) its own row in the deliverables README and its entry in result.json's
  `static.formats`.

**Who makes it.** The video's production agent makes every format, the primary first: the primary's stills, then each extra
format's (S3); the primary's project, then each extra format's (S4); one record of them all (X10; `awl-analyze-produce` A9s, A9b).
A format added to a run later (`T static format --also`) is made for the videos the user names, from their plans and narration as
they are. A vertical version longer than YouTube's Shorts limit (3 minutes) is published as a vertical long video, not a Short: the
wrap-up says so.
