---
name: awl-static-images
description: /analyze-with-loupe Static step S3: a video's stills and YouTube thumbnail, made by OpenAI or FLUX 3 Klein and checked, or the user's taken in. Internal to that command.
user-invocable: false
---

# awl-static-images — Static step S3: the stills

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §5: `AWL/reference/static/050_5_images-a6s-plan-s3.md` (18.5 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (5.4 KB)
- static §11: `AWL/reference/static/110_11_no-religion-and-no-superstition.md` (3.1 KB)
- static §12: `AWL/reference/static/120_12_the-youtube-title-and-thumbnail.md` (6.0 KB)
- *the plan has characters:*
  - anomaly-catalog §2.17: `AWL/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- *the style lock is illustrated, painted or cartoon:*
  - anomaly-catalog §2.13: `AWL/reference/anomaly-catalog/160_2.13_stylised-and-anime-rendering.md` (1.3 KB)
- *the run has more than one format (`state.json → static.extra_formats`):*
  - static §2b: `AWL/reference/static/025_2b_more-than-one-format.md` (4.5 KB)

`state.json → static_images` says which half applies: `api` or `klein` (the first), `prompts` (the second). With more than one format,
the primary's stills come first (the steps below), then each extra format's ("Another format", below).

## Images made for you (`static_images=api`: the OpenAI Images API; `klein`: FLUX 3 Klein on this PC)

A long video's stills are split across agents (`awl-analyze-produce` A9b): when your spawn message names `images K1-K2`, steps 2–5
apply to those images only (step 6, the thumbnail, only when it says so); write `RUN/60-outputs/video-NN/images-K1-K2.json` (each
image's attempts, re-draws, cost, flags) and end with its one JSON line; the edit agent does S4 and X10.

**The judge's decisions come first** (static §13, `RUN/40-briefs/video-NN-judge.md`): the prompts you send are the plan's as the judge
left them (J1, and J3 between stretches); read the judge's record of your images before the first call, and name in your report every
still whose outcome differs from what the record forecast for it (the caption the upsampler wrote, in each attempt, is the first place
to look), so the next J3 prevents it in the stretches still to come.

The same commands for both; `T image generate` takes the source from `static_images`. With **FLUX 3 Klein** the toolkit runs the model
on this PC's GPU, one image at a time (it waits for the GPU; a minute or more per image): your prompt goes through Black Forest Labs'
prompt upsampler first, and the answer's `caption` is the full text the image model received (read it first when an image is wrong: a
lost or changed detail there is the cause). A character's **anchor** is drawn from its sheet prompt as written, without the
upsampler (it adds props such as a hat or a tool, and every later image copies the anchor): write the sheet as the full description
itself (the medium, the framing, every visible trait, the clothing, the pose, the plain background, the light) and nothing more.
At most 10 references per image; the seed is in each answer (`--again` draws with a new seed; `--again --seed N` makes a recorded draw
again); `--no-upsample` only when a plan image's prompt file already is a full scene caption. No moderation, no cost. Every Klein prompt
says the picture is one continuous scene from a single camera viewpoint filling the whole frame (static §5: without it the upsampler may
stack a tall frame into panels, above all with no reference image).

1. **Anchors** (the main session, once per run, before any agent; a character with no photo): its sheet prompt in
   `RUN/30-assets/characters/C1-sheet.txt` (the look in words, a neutral pose on a plain background, the style lock), then
   `T image generate --run RUN --anchor C1 --prompt-file RUN/30-assets/characters/C1-sheet.txt`. View it (static §8: the look, and no
   ornament that reads as a letter or symbol, since every image copies it); a wrong look is drawn again by QC fixes; the one kept is the
   reference of every image that shows them.
2. **Every image of the plan** (the agent, in order): its prompt file `RUN/40-briefs/video-NN-iKK-prompt.txt` (the plan's prompt, the
   style lock, §5's composition, who is who when a reference image rides along), then
   `T image generate --run RUN --video NN --image K --prompt-file RUN/40-briefs/video-NN-iKK-prompt.txt [--ref <photo or anchor> …]` (the
   photo or anchor of each character it shows; at most 16, with FLUX 3 Klein 10; three or more characters with FLUX 3 Klein: their own
   anchors when `T image fit --run RUN --n-refs N`, read right before the call, shows headroom for them, else their one cast sheet,
   `T image cast --run RUN --ids C2,C3,C4`). The size and quality (the API's) are the run's format (`state.json → static.format`); never another
   size. The prompt never holds the words caption, subtitle, lower third or text overlay (static §5: the model then draws a made-up
   subtitle) and ends on the clean-picture sentence; the answer's `prompt_overlay_words` must be empty, else rewrite the prompt. Every
   image call runs in the foreground (never a background loop: Claude Code ends background commands when memory runs low).
3. **View the image** (Read the file) and check it (static §8); after the stills, `T image text --run RUN --video NN` lists every line
   of letters in them (a long line across the bottom third that no sign, page or screen carries is a made-up subtitle: a failure). A
   failure, by QC fixes: `auto` change the prompt or the references by the
   diagnosis and draw again (`--again` only when nothing but the draw changes), at most two re-draws per image, then the best one,
   flagged; `ask` the proposal and stop (the contract's QC fixes rule, blocker `qc_fix_permission`); `off` keep it, noted.
4. `moderation_blocked` (the API): rewrite the prompt (or drop the reference that sets it off) before any new call; refused again: show
   that moment of the line another way, noted. A timeout leaves the ledger `unknown`: decide before sending again. FLUX 3 Klein's
   failure answer carries the error and the end of ComfyUI's log: a memory stop the toolkit already ran once more after the memory came
   back (`memory_retry`); one that still fails means other programs hold the memory (say so, go on with the next image, and make it
   again once at the end; never retry in a loop).
5. An earlier attempt is the better one: `T image use --run RUN --video NN --image K --attempt M`.
5b. **Logos** (static §5 "Real things look like themselves"): an image whose plan has a `logo`, once made and viewed: read the box of its
   blank surface off the picture, `T image brand --run RUN --video NN --image K --logo <the plan's file> --box x0,y0,x1,y1 [--card]`, and
   view the result (static §8). Another brand's mark the model drew in any image: `T image brand … --cover x0,y0,x1,y1`. A known person's
   anchor (step 1) rides with their photos (`--ref <photo>`), and every still that shows them with the anchor.
5c. **Labels** (static §5 "Labels"): a map or route whose line names places, once made and viewed (its pins where the places are,
   else a redraw reason by QC fixes): read each label's centre off the picture beside its pin and write it into the image's plan entry
   (`"labels": [{"text", "x_rel", "y_rel"}]`, the motion `none`) and the plan's `labels_style`; the edit places them (`T capcut-labels`).
6. **The YouTube thumbnail** (static §12), after the stills: its prompt file `RUN/40-briefs/video-NN-thumb-prompt.txt` (the plan's
   `thumbnail.prompt`, the style lock, its exact words when it has any), then `T image generate --run RUN --video NN --thumbnail --size
   <the plan's thumbnail.size> --prompt-file RUN/40-briefs/video-NN-thumb-prompt.txt [--ref <photo or anchor> …]`; view it at full size
   and its `-small.png` (the feed size) and check it as static §8 says; re-draws by QC fixes as in step 3; another attempt:
   `T image use --run RUN --video NN --thumbnail --attempt M`. The one in use is in `RUN/deliverables/video-NN-thumbnail.png`.
7. Each answer carries `cost_usd_estimate` (0 with FLUX 3 Klein): write their sum in `result.json` and the brief.

## Another format (`static.extra_formats`; static §2b)

After the primary's stills, each extra format's, in plan order; no anchor and no thumbnail (made once, for every format). A split
video's spawn message `format <tag>, images K1-K2` means that format's stills K1-K2 only (write
`RUN/60-outputs/video-NN/<tag>/images-K1-K2.json`).
1. **Its caption band and the swap pairs**, once per video and format: the plan's `"by_format": {"<tag>": {"captions": {"size",
   "y_rel"}}}` (static §2b), written now when the plan lacks it, since the stills keep that band clear; then read the requests of two
   or three of the primary's stills in use (`RUN/50-requests/video-NN-iKK-aM-image-request.json`, `params.prompt`) and pick the exact
   phrases that name the primary's frame (its shape and aspect, the main subject's place across it, the band kept at the plan's
   `y_rel`) and what each says for this format (its shape, §5's composition for its aspect, its band at its own `y_rel`). Write them in
   the brief.
2. **Every still**: `T image generate --run RUN --video NN --image K --format <tag> --same-as-primary --swap "<old>" "<new>" …` (the
   primary's prompt and references, sent at this format's size). It stops before sending when a phrase is not in that still's prompt:
   pick that still's own words, or, for a scene the swaps do not fit (laid out across the other frame), write
   `RUN/40-briefs/video-NN-<tag>-iKK-prompt.txt` (the same scene, only its layout changed) and send it with `--prompt-file` and the same
   `--ref`s, why in the brief. In the foreground, one at a time with FLUX 3 Klein, as for the primary.
3. **View and check** each one (static §8) and against the primary's still (the same scene, people and things); after the stills,
   `T image text --run RUN --video NN --format <tag>`; re-draws by QC fixes as step 3 says; another attempt: `T image use … --format <tag>`.
4. **Logos and labels** on its own picture: `T image brand --run RUN --video NN --image K --format <tag> --logo <file> --box …`
   (the box read off this still); a labelled image's places read off this still into the plan entry's `"by_format": {"<tag>":
   {"labels": […]}}`.
5. Its costs as in step 7, per format in `result.json`.

## Images by the user (`static_images=prompts`; main session)

1. **The prompts**, after S2 for every video: the plans' prompts written as step 2 says (the characters' sheet prompts first), then
   `T image prompts --run RUN` → `RUN/deliverables/prompts/video-NN-image-prompts.md` (each video's thumbnail too, as `vNN-thumb`, at
   its own size). Tell the user in one message: the files, the names `vNN-iKK` and `vNN-thumb` (and `C1-sheet` for a character sheet they
   make first), the format's aspect and size (the thumbnail's own), one folder for everything, and "send me the folder's
   path". More than one format (static §2b): also `T image prompts --run RUN --format <tag> [--swap "<old>" "<new>" …]` per extra
   format (the same prompts, their frame words swapped; names `vNN-<tag>-iKK`), named in the same message.
   `T state --run RUN set static.waiting=images`, then stop and wait.
2. **The folder** (their reply, or `resume` with a path): `T image intake --run RUN --folder "<path>"` (and once more with `--format
   <tag>` per extra format: it takes only `vNN-<tag>-iKK`). Missing images: tell the user which
   and wait (the same intake again later). Files it cannot match by name: show them and ask how they map; never guess.
   Then `T state --run RUN set static.waiting=null`.
3. **View every image** (static §8) and list the failures per video for the user; nothing is made by the API in this mode (the user may
   send a corrected file: intake again).

## Never (this phase)

- Never make an image any other way than `T image generate` (no other tool, no direct call, no ComfyUI started by hand); never print,
  echo or write the key.
- Never move, rename or change the user's files (intake copies them).
- Never send a refused request again unchanged; never draw an image again when nothing in it was wrong.
- Never put text, a logo, a sticker or an emoji into an image the story does not need (item 6; a thumbnail's words only as static §12
  says).
- Never anything religious or superstitious in a still or a thumbnail (static §11): a prompt describes a secular scene and never names
  what must stay out.

## Hand-off

A production agent: invoke Skill `awl-static-edit` once every format's stills are made (a split video's image agent: end with its
JSON line). The main session (anchors, prompts, intake): return to A9s in `awl-analyze-produce`.
