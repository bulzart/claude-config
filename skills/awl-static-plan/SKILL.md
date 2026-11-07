---
name: awl-static-plan
description: /analyze-with-loupe Analyze Mode / Static phase: characters, the subject pool, five voice samples, the one stop, scripts and image plans (A6s). Internal to that command.
user-invocable: false
---

# awl-static-plan — Static: subjects, voice, scripts, image plans (A6s)

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §0: `AWL/reference/static/005_0_the-team-who-works-a-static-run.md` (3.6 KB) (who works the run; skip when already read)
- static §3: `AWL/reference/static/030_3_a-new-subject-a6s.md` (2.4 KB)
- static §4: `AWL/reference/static/040_4_the-script-a6s.md` (2.5 KB)
- static §5: `AWL/reference/static/050_5_images-a6s-plan-s3.md` (9.5 KB)
- static §6: `AWL/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (6.4 KB)
- static §10: `AWL/reference/static/100_10_one-channel-per-run.md` (4.3 KB)
- static §11: `AWL/reference/static/110_11_no-religion-and-no-superstition.md` (2.5 KB)
- static §12: `AWL/reference/static/120_12_the-youtube-title-and-thumbnail.md` (4.5 KB)
- creative-direction §5.0: `AWL/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (5.1 KB)
- creative-direction §6: `AWL/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- *the client's documents hold rules (`RUN/30-assets/guardrails.md` exists):*
  - brand-guardrails §4: `AWL/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)

Inputs: `RUN/20-analysis/static-spec.md` and the cards (A3–A4), the asset registry (A2b), `state.json → requested_videos` (A5).

### A6s. Static: the plan (main session; the run's one stop)
1. **Characters.** Every character of the asset registry gets an id (C1, C2 …), who they are (a known real person, an ordinary role, a
   cartoon or children's character, an animal …) read from their photos and words [A]/[I], the look in words (face, hair, build, age,
   clothing, style) and its source: photo(s) or description only. Write `RUN/30-assets/characters.md`. No characters: write "none"; the
   subject then comes from the references alone (static §3).
2. **The subject pool** (static §3, §10): `T static lock --run RUN` first (the locks: the niche, the style reference, the narrator, the
   subjects made). The requested count plus three at least (never under five), all of the run's niche, told in the references' craft,
   never a reference's own subject and never one the run made or one so close it retells it, nothing religious or superstitious
   (static §11), scored as §3 says. A factual niche: research every candidate (WebSearch, then WebFetch on the strongest
   results; at most four searches per candidate) and keep only the candidates two independent sources hold. Write
   `RUN/20-analysis/static-subjects.md` (each candidate: title, hook line, why it fits, the scores, the sources).
3. **Five voice samples** (static §6; the user, 2026-11-06: "the agent should suggest 5 versions and also the file path for each of them
   so the user can hear them and pick the one they like to be the voice of the videos"), only when the run has no narrator yet (the
   locks' `voice` empty) or a clone picks a new one (`state.json → static.new_voice` true): five voice descriptions from the spec's voice
   profile, five different takes on it, and one line in the references' style that names no subject and nothing of static §11, then
   `T tts design --run RUN --text "<line>" --instruct "<voice 1>" --instruct "<voice 2>" --instruct "<voice 3>" --instruct "<voice 4>"
   --instruct "<voice 5>"` (a clone's new narrator adds `--replace`). A locked narrator makes no samples (static §10).
   A worker error is a blocker of the run: report its real text with `T static check` and stop.
4. **The one stop**, in plain chat (never AskUserQuestion: the pool is longer than four options), the last thing in the turn: the
   subjects numbered (title — hook line — why it fits — for facts the number of sources), the five voices when step 3 made them (number,
   the voice in a few words, and the full path of its file, as `T tts design` prints it, so the user can play it), and "Reply with N
   subject numbers and one voice number, or 'you pick'." (no voice number when the narrator is locked). Then stop and wait. Fewer
   subjects than the count: ask once more. "You pick": the top-scored subjects and the voice that best fits the profile [I].
5. **Store the picks:** `T static subjects --run RUN --add "<title 1>" --add "<title 2>"` (in video order; each gets the next video
   number), then, when step 3 made samples, `T tts voice --run RUN --sample K` (a clone's new narrator: `--replace`, then
   `T state --run RUN set static.new_voice=false`), plus `--emotion NAME="<a line that carries it>"` (at most two) when the spec's
   delivery swings (static §6).
6. **Scripts** (static §4), per video: `RUN/40-briefs/video-NN-script.md`, `RUN/40-briefs/video-NN-narration.json`, and for a factual
   niche `RUN/40-briefs/video-NN-facts.md`; nothing religious or superstitious in any line (static §11). The copy test and the sharpness
   gate (creative-direction §5.0, §6) pass before a script is final.
7. **Image plans** (static §5), per video: `RUN/40-briefs/video-NN-images.json`: the characters (photo, or the sheet prompt of one with
   none), one image per stretch of lines (`from_line`), every prompt with the spec's style lock word for word (the style reference's
   look, the same in every video of the run: static §10) and §5's composition, a secular scene with nothing of static §11 in it, the
   video's `title` and `thumbnail` (static §12: the references' title and thumbnail patterns, the thumbnails' size, the run's style
   lock), each
   image's move and amount and each join decided from the spec's measured pattern (static §5 "Moves and joins": the reference's pace times
   this still's seconds, the references' order of moves; a join and the caption entrance from `AWL/data/capcut-catalogue.md`, only what it
   shows drawn, and only options marked free while the run's CapCut plan is free, `state.json → capcut_plan`), the `captions` block: the spec's text look (static §2: font file, size, colours, outline, box, case, highlight, the
   entrance as `animation` and `animation_s`) with this video's highlighted words; with an effects folder, the `effects` the spec's effects
   pattern calls for (static §2, §5 "Effects": each overlay or sound from `00-inventory/effects.md`, its moment and anchor second, how it
   is blended, its fit and volume, and why; only the ways the catalogue's Effects part shows playing). Nothing is left to a stock value:
   `T slideshow plan` lists what is undecided. The count follows the spec's seconds per still at the script's length; the narration's
   real timing settles it in S2 (and the effects' moments with it: a `join` or a `line` follows the timing, an `at_s` does not).
8. **The bed** (every video, also when the references are voice only; static §6): `RUN/40-briefs/music.json`, one track per video,
   its `caption`, `bpm` and `why` reasoned from the spec's bed brief and this video's script (its beats and their emotions), never from
   analysing the references' music (the user, 2026-11-06: "make sure we try to generate instrumentals that fit the video content type and
   narration based on the data collected from the references, no need to analyze their instrumentals too"); the image plan gets
   `"music": true`. The duration is set in S2 once the narration exists, and the level after the bed's check.
9. Show one line per video (number, subject, title, length, images, bed or none) and go on without waiting.

**More videos** (static §10; `/analyze-with-loupe more <run> [N]`, or the user asking for more after a wrap-up): no start question is
asked and nothing is analysed again. `T static lock --run RUN` (the locks; a run made before the locks existed is asked its niche once,
with its subjects as context, and locks it with its style reference: the reference its style lock came from), the count when it is not
given (AskUserQuestion, header "Videos"), then steps 2 and 4–9 for the new videos only: no voice samples (the narrator is locked), the
stop asks only for the subjects, `T static subjects --add` gives them the next numbers, and their scripts, image plans, titles and
thumbnails keep the run's style lock and text look. Then `awl-analyze-produce` A9s for the new videos only.

## Rules this phase owns (contract item 36)

- Static keeps the references' delivery and changes their subject; a factual niche stays factual and sourced; the user picks the
  subjects (and, the first time, the voice) at one stop. The run's other stops are a QC-fix proposal (`ask`) and, with images by the
  user, their folder.
- One channel per run (static §10): the niche, the visual style and the narrator are the user's picks, locked; another niche is a clone.
- Nothing religious or superstitious in a subject, a line, a prompt, a title or a thumbnail (static §11).
- No Higgsfield and no Loupe in Static: no model menu, `T prompt-template`, `T qc-brief` or `T qc-consult`.

## Never (this phase)

- Never take a reference's subject, names, facts or lines; never invent a fact, a quote, a date or a number; never put a claim in a script
  that its fact sheet does not source.
- Never pick the subjects or the voice for the user unless they said "you pick".
- Never ask for anything but the subjects and the voice at the stop (the paths and choices were asked at the start).
- Never put text, a sticker or an emoji into an image prompt unless the story needs that text (item 6; a thumbnail's words only as the
  references' thumbnails carry them, static §12).
- Never offer a subject outside the run's niche or one the run made; never a new narrator or visual style inside a run (a clone changes
  them, static §10); never anything religious or superstitious (static §11).

## Hand-off

`T state --run RUN set stage=planned next_skill=awl-analyze-produce`, then invoke Skill `awl-analyze-produce`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
