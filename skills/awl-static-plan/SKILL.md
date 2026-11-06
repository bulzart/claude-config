---
name: awl-static-plan
description: /analyze-with-loupe Analyze Mode / Static phase: characters, the subject pool, three voice samples, the one stop, scripts and image plans (A6s). Internal to that command.
user-invocable: false
---

# awl-static-plan — Static: subjects, voice, scripts, image plans (A6s)

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §3: `AWL/reference/static/030_3_a-new-subject-a6s.md` (2.1 KB)
- static §4: `AWL/reference/static/040_4_the-script-a6s.md` (2.3 KB)
- static §5: `AWL/reference/static/050_5_images-a6s-plan-s3.md` (6.3 KB)
- static §6: `AWL/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (2.6 KB)
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
2. **The subject pool** (static §3): the requested count plus three at least (never under five), in the references' niche, never a
   reference's own subject, scored as §3 says. A factual niche: research every candidate (WebSearch, then WebFetch on the strongest
   results; at most four searches per candidate) and keep only the candidates two independent sources hold. Write
   `RUN/20-analysis/static-subjects.md` (each candidate: title, hook line, why it fits, the scores, the sources).
3. **Three voice samples** (static §6): three voice descriptions from the spec's voice profile and one line in the references' style that
   names no subject, then `T tts design --run RUN --text "<line>" --instruct "<voice 1>" --instruct "<voice 2>" --instruct "<voice 3>"`.
   A worker error is a blocker of the run: report its real text with `T static check` and stop.
4. **The one stop**, in plain chat (never AskUserQuestion: the pool is longer than four options), the last thing in the turn: the
   subjects numbered (title — hook line — why it fits — for facts the number of sources), the three voices (number, the voice in a few
   words, the file to play), and "Reply with N subject numbers and one voice number, or 'you pick'." Then stop and wait. Fewer subjects
   than the count: ask once more. "You pick": the top-scored subjects and the voice that best fits the profile [I].
5. **Store the picks:** `T state --run RUN set static.subjects='["<title 1>","<title 2>"]'` (video order), then
   `T tts voice --run RUN --sample K`, plus `--emotion NAME="<a line that carries it>"` (at most two) when the spec's delivery swings
   (static §6).
6. **Scripts** (static §4), per video: `RUN/40-briefs/video-NN-script.md`, `RUN/40-briefs/video-NN-narration.json`, and for a factual
   niche `RUN/40-briefs/video-NN-facts.md`. The copy test and the sharpness gate (creative-direction §5.0, §6) pass before a script is
   final.
7. **Image plans** (static §5), per video: `RUN/40-briefs/video-NN-images.json`: the characters (photo, or the sheet prompt of one with
   none), one image per stretch of lines (`from_line`), every prompt with the spec's style lock word for word and §5's composition, each
   image's move and amount and each join decided from the spec's measured pattern (static §5 "Moves and joins": the reference's pace times
   this still's seconds, the references' order of moves; a join and the caption entrance from `AWL/data/capcut-catalogue.md`, only what it
   shows drawn), the `captions` block: the spec's text look (static §2: font file, size, colours, outline, box, case, highlight, the
   entrance as `animation` and `animation_s`) with this video's highlighted words. Nothing is left to a stock value: `T slideshow plan`
   lists what is undecided. The count follows the spec's seconds per still at the script's length; the narration's real timing settles it in S2.
8. **The bed:** only when the spec says the references use one: `RUN/40-briefs/music.json`, one track per video (static §6; the duration
   is set in S2 once the narration exists).
9. Show one line per video (number, subject, length, images, bed or none) and go on without waiting.

## Rules this phase owns (contract item 36)

- Static keeps the references' delivery and changes their subject; a factual niche stays factual and sourced; the user picks the
  subjects and the voice at one stop. The run's other stops are a QC-fix proposal (`ask`) and, with images by the user, their folder.
- No Higgsfield and no Loupe in Static: no model menu, `T prompt-template`, `T qc-brief` or `T qc-consult`.

## Never (this phase)

- Never take a reference's subject, names, facts or lines; never invent a fact, a quote, a date or a number; never put a claim in a script
  that its fact sheet does not source.
- Never pick the subjects or the voice for the user unless they said "you pick".
- Never ask for anything but the subjects and the voice at the stop (the paths and choices were asked at the start).
- Never put text, a sticker or an emoji into an image prompt unless the story needs that text (item 6).

## Hand-off

`T state --run RUN set stage=planned next_skill=awl-analyze-produce`, then invoke Skill `awl-analyze-produce`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
