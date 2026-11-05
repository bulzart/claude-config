---
name: awl-static-images
description: /analyze-with-loupe Static step S3: a video's stills made by the OpenAI Images API and checked, or the prompts for the user and their folder taken in. Internal to that command.
user-invocable: false
---

# awl-static-images — Static step S3: the stills

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §5: `AWL/reference/static/050_5_images-a6s-plan-s3.md` (2.8 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (1.5 KB)
- *the plan has characters:*
  - anomaly-catalog §2.17: `AWL/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- *the style lock is illustrated, painted or cartoon:*
  - anomaly-catalog §2.13: `AWL/reference/anomaly-catalog/160_2.13_stylised-and-anime-rendering.md` (1.3 KB)

`state.json → static_images` says which half applies: `api` or `prompts`.

## Images by the API (`static_images=api`)

1. **Anchors** (the main session, once per run, before any agent; a character with no photo): its sheet prompt in
   `RUN/30-assets/characters/C1-sheet.txt` (the look in words, a neutral pose on a plain background, the style lock), then
   `T image generate --run RUN --anchor C1 --prompt-file RUN/30-assets/characters/C1-sheet.txt`. View it; a wrong look is drawn again by QC
   fixes; the one kept is the reference of every image that shows them.
2. **Every image of the plan** (the agent, in order): its prompt file `RUN/40-briefs/video-NN-iKK-prompt.txt` (the plan's prompt, the
   style lock, §5's composition, who is who when a reference image rides along), then
   `T image generate --run RUN --video NN --image K --prompt-file RUN/40-briefs/video-NN-iKK-prompt.txt [--ref <photo or anchor> …]` (the
   photo or anchor of each character it shows; at most 16). The size and quality are the run's format (`state.json → static.format`);
   never another size.
3. **View the image** (Read the file) and check it (static §8). A failure, by QC fixes: `auto` change the prompt or the references by the
   diagnosis and draw again (`--again` only when nothing but the draw changes), at most two re-draws per image, then the best one,
   flagged; `ask` the proposal and stop (the contract's QC fixes rule, blocker `qc_fix_permission`); `off` keep it, noted.
4. `moderation_blocked`: rewrite the prompt (or drop the reference that sets it off) before any new call; refused again: show that moment
   of the line another way, noted. A timeout leaves the ledger `unknown`: decide before sending again.
5. An earlier attempt is the better one: `T image use --run RUN --video NN --image K --attempt M`.
6. Each answer carries `cost_usd_estimate`: write their sum in `result.json` and the brief.

## Images by the user (`static_images=prompts`; main session)

1. **The prompts**, after S2 for every video: the plans' prompts written as step 2 says (the characters' sheet prompts first), then
   `T image prompts --run RUN` → `RUN/deliverables/prompts/video-NN-image-prompts.md`. Tell the user in one message: the files, the
   names `vNN-iKK` (and `C1-sheet` for a character sheet they make first), the format's aspect and size, one folder for everything, and "send me the folder's
   path". `T state --run RUN set static.waiting=images`, then stop and wait.
2. **The folder** (their reply, or `resume` with a path): `T image intake --run RUN --folder "<path>"`. Missing images: tell the user which
   and wait (the same intake again later). Files it cannot match by name: show them and ask how they map; never guess.
   Then `T state --run RUN set static.waiting=null`.
3. **View every image** (static §8) and list the failures per video for the user; nothing is made by the API in this mode (the user may
   send a corrected file: intake again).

## Never (this phase)

- Never make an image any other way than `T image generate` (no other tool, no direct call); never print, echo or write the key.
- Never move, rename or change the user's files (intake copies them).
- Never send a refused request again unchanged; never draw an image again when nothing in it was wrong.
- Never put text, a logo, a sticker or an emoji into an image the story does not need (item 6).

## Hand-off

A production agent: invoke Skill `awl-static-edit`. The main session (anchors, prompts, intake): return to A9s in `awl-analyze-produce`.
