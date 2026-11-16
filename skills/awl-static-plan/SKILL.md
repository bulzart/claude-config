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

- static §0: `AWL/reference/static/005_0_the-team-who-works-a-static-run.md` (5.8 KB) (who works the run, and when; skip when already read)
- static §3: `AWL/reference/static/030_3_a-new-subject-a6s.md` (4.7 KB)
- static §4b: `AWL/reference/static/045_4b_engagement-thought-first.md` (5.1 KB) (what the references taught, then what will hold a viewer, thought through before any line)
- static §4: `AWL/reference/static/040_4_the-script-a6s.md` (11.1 KB)
- static §5: `AWL/reference/static/050_5_images-a6s-plan-s3.md` (27.6 KB)
- static §6: `AWL/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (30.5 KB)
- static §10: `AWL/reference/static/100_10_one-channel-per-run.md` (11.0 KB)
- static §11: `AWL/reference/static/110_11_no-religion-and-no-superstition.md` (3.1 KB)
- static §11b: `AWL/reference/static/115_11b_nothing-indecent-gory-or-distres.md` (6.1 KB)
- static §12: `AWL/reference/static/120_12_the-youtube-title-and-thumbnail.md` (8.6 KB)
- static §13: `AWL/reference/static/130_13_evaluating-the-work.md` (17.6 KB) (how you judge your own work, and fresh reviewers)
- creative-direction §5.0: `AWL/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (5.1 KB)
- creative-direction §6: `AWL/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- *the client's documents hold rules (`RUN/30-assets/guardrails.md` exists):*
  - brand-guardrails §4: `AWL/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)

Inputs: `RUN/20-analysis/static-spec.md` and the cards (A3–A4), the asset registry (A2b), `state.json → requested_videos` and `static.length_plan` (A5). A run whose spec has no page "What the references teach" (made before 2026-11-14) gets it first, written from the spec's readings and the niche's cards (static §2), before anything is planned. A run with no `static.length_plan` (made before 2026-11-12, or A5 not answered) asks the length first (`awl-analyze-study` A5 "Then the length"), before the pool is drawn.

### A6s. Static: the plan (main session; the run's one stop)
1. **Characters.** Every character of the asset registry gets an id (C1, C2 …), who they are (a known real person, an ordinary role, a
   cartoon or children's character, an animal …) read from their photos and words [A]/[I], the look in words (face, hair, build, age,
   clothing, style) and its source: photo(s) or description only. Write `RUN/30-assets/characters.md`. No characters: write "none"; the
   subject then comes from the references alone (static §3). A known real person the script brings in (theirs or the subject's people:
   a founder, a leader) gets two or three public photos for their likeness (static §5 "Real things look like themselves": the user's
   assets first, else `T fetch-image --kind photo`, the licence recorded) and is written in `characters.md` with them.
2. **The subject pool** (static §3, §10): `T static lock --run RUN` first (the locks: the niche, the style reference, the narrator, the
   subjects made). The requested count plus three at least (never under five), all of the run's niche, told in the references' craft,
   never a reference's own subject and never one the run made or one so close it retells it, nothing religious or superstitious
   (static §11) and nothing indecent, gory or distressing (static §11b), scored as §3 says. A factual niche: research every candidate (WebSearch, then WebFetch on the strongest
   results; at most four searches per candidate) and keep only the candidates two independent sources hold. **Each candidate comes
   with its approach** (static §3, §10; the user, 2026-11-11: the niche is a family, each video an approach): story form, angle, point
   of view, time frame, scale, title form and pillar, drawn from the spec's "approaches seen", from the whole set's other story
   families, or the agent's own inside the niche (its reason written); the pool is varied on purpose, none repeats the last video's
   approach without a written reason (`T static subjects --run RUN` lists the approaches made), and a pool is never "N days of X"
   alone. **The research looks for what gives a subject life beside the claims** (static §3, §4b; the user, 2026-11-13: "not just
   facts"): whatever this niche and subject offer that a viewer would care about, wonder at or remember, each with its source; each
   candidate is scored on how well it can hold and attach a viewer, and the agent works out what that means for it. Write
   `RUN/20-analysis/static-subjects.md` (each candidate: title, approach, hook line, why it fits, the scores, the sources).
3. **Five voice samples** (static §6; the user, 2026-11-06: "the agent should suggest 5 versions and also the file path for each of them
   so the user can hear them and pick the one they like to be the voice of the videos"), only when the run has no narrator yet (the
   locks' `voice` empty) or a clone picks a new one (`state.json → static.new_voice` true): five candidates from the spec's voice
   profile, five different takes on it: voices the account has, `T tts voices --run RUN --measure` (filtered by `--gender`, `--accent`,
   `--age`, `--use-case`; each voice's own ElevenLabs preview read with the references' yardstick; free), and, when they do not cover
   the profile, Voice Design samples: `T tts design --run RUN --text "<a line of 100 to 1,000 characters in the references' style that
   names no subject and nothing of static §11, in the language of the batch's first video (`state.json → static.language_plan`; its
   English reading goes to the stop)>" --instruct "<voice 1>" …` (each description 20 to 1,000 characters, naming the set's pace
   in words, "a quick, measured pace"; billed per character of the line, once per design; a clone's new narrator adds `--replace`). A
   locked narrator makes no samples (static §10). An ElevenLabs error is a blocker of the run: report its real text with `T tts check`
   and stop.
4. **The one stop**, in plain chat (never AskUserQuestion: the pool is longer than four options), the last thing in the turn: the
   subjects numbered (title, in English for the user to read: the video's own title is written in its language at step 7 — approach
   in one line, with the last video's beside it — hook line — why it fits — for facts the number of sources), the five voices when step 3 made them (number,
   the voice in a few words, its pace while articulating in words a minute (its preview's or sample's, as `T tts voices` or `T tts
   design` print it) next to the set's, said plainly: nothing is sped afterwards, and the run's model may have no speed setting (Eleven v4
   has none), so a voice near the set's pace is the one that reaches it, and the full path of its file, so the user can play it), and "Reply with N
   subject numbers and one voice number, or 'you pick'; you may also rewrite a subject's approach." (no voice number when the narrator
   is locked). Then stop and wait. Fewer subjects than the count: ask once more. "You pick": the top-scored subjects and the voice
   that best fits the profile [I].
5. **Store the picks:** `T static subjects --run RUN --add "<title 1>" --story-form "…" --angle "…" --pov "…" --time-frame "…"
   --scale "…" --title-form "…" --pillar "…" --approach-why "…" [--language <L>]` once per subject, in video order (each gets the
   next video number; the language is the batch's plan, `T static language --run RUN --plan`, unless `--language` names another for
   that video; `T static subjects --set NN …` edits a made-up approach before its narration exists), then, when step 3 made samples, `T tts voice --run RUN --voice-id ID` (an account voice) or `--sample K` (a design) (a
   clone's new narrator: `--replace`, then `T state --run RUN set static.new_voice=false`), plus `--emotion NAME="[tags]"` (at most two:
   the audio tags sent where a line of that emotion begins) when the spec's delivery swings (static §6).
6. **The design, then the scripts**, per video (the user, 2026-11-13: "this has to be in early stages of planning and video
   development, and not just check and edit and do double effort after the whole video story is already crafted and finished", and "just
   give general suggestions ... and then the pipeline evaluates on its own and find out whats best while it executes").
   **6a. Learn from the references, then think it through** (static §4b), before any line, prompt or caption exists: first write down
   what the references taught for this subject's niche (the spec's page "What the references teach" and its readings, and the niche's cards: their patterns,
   approach and how their stories are built, with their sources) as the first part of the blueprint; then, with that and what your
   research found as the context, work out what will make a stranger click, stay, feel something, finish and pass this video on, for this
   subject in this niche (alone, or with fresh agents given all the same context and left free to think: how many and with what focus
   is your decision; each niche has its own logic, static §4b); keep a short note of what you decided and why
   (`RUN/40-briefs/video-NN-blueprint.md`, any form), be skeptical of it, and, if a second opinion is worth having, have a fresh reviewer
   read it cold (static §13: no context of yours, no conclusions).
   **6b. Research again** wherever the design found a gap, sourced as static §3 says and written into the fact sheet.
   **6c. Scripts** (static §4, written to the design), per video: `RUN/40-briefs/video-NN-script.md`, `RUN/40-briefs/video-NN-narration.json`, and for a factual
   niche `RUN/40-briefs/video-NN-facts.md`; nothing religious or superstitious in any line (static §11), and no graphic detail,
   suffering or swearing, and no intimate part of the body named, even as a first-aid fact (static §11b: a hard fact told plainly and
   briefly; the tip told by its other places). The length follows the user's pick, asked at A5 before this phase
   (`state.json → static.length_plan`; the user, 2026-11-12; static §4 "The length": standard = yours per video from the spec's
   length pattern, the niche's references' lengths in `T static lock`'s `reference_lengths`; own = the user's number or offset),
   written as `target_length_s` and `length_why` in the narration JSON, the script sized to it
   at the planned overall pace (static §4: words = seconds × words a minute / 60; the units of the video's language, `T static units`).
   **The video's language and approach** (static §4, §6, §10): the script is written natively in the video's language (the recorded one,
   `state.json → static.video_info`), every line with its English `gloss`, and follows the recorded approach (its story form, point of
   view, time frame and scale decide the beats and who "you" is); the narration JSON's `language` is that language's ISO code. The
   narration JSON also carries the spec's `pace`
   (`wpm_articulation` and `wpm_overall` as the family's bands from `T static profile`, the point from the niche's references within
   it, with `why`; static §1, §4) and the long pauses the niche's references hold as a line's `tags_after` where they pause longer
   (before a reveal); its `delivery`, `voice_settings` and the pace point are settled by your check at step 9. The beats, the hooks, the emotions, the
   language and the calls to action follow the spec's patterns: mostly the niche's references', the whole set's kept where they hold
   across niches or where the niche's references are silent (static §1 "The run's niche within the set", §2), never one reference's. The copy test and the
   sharpness gate (creative-direction §5.0, §6) pass before a script is final.
7. **Image plans** (static §5), per video: `RUN/40-briefs/video-NN-images.json`: the characters (photo, or the sheet prompt of one with
   none), one image per stretch of lines (`from_line`), each written for a purpose in the story (static §5 "A purpose for each picture": the plan may
   note it as `job` and `shot`, free text; vary what the eye sees), every prompt with the spec's style lock word for word (the style reference's
   look, the same in every video of the run: static §10) and §5's composition, each company or brand the story is about with its
   official logo where the story brings it in and once more later (static §5 "Real things look like themselves": `T fetch-image --kind
   logo`, the image's `logo` field, its surface plain and blank in the prompt), a secular scene with nothing of static §11 in it, every
   person an adult (static §11b, 2026-11-14: no child or child-faced figure; each character's sheet states an age and adult features)
   dressed for the scene with the clothes named from top to bottom and no undressed, injured or agonised moment, nobody as if
   dead, and a survival pose low on the ground kept and drawn with the person clearly alive: head up or turned so the open eyes show,
   mid-move (static §11b), the
   video's `title` (in the video's language, in the recorded title form, with `title_gloss`) and `thumbnail` (static §12: the
   references' title and thumbnail patterns, the thumbnails' size, the run's style lock; its words in the video's language; one promise
   with the title and the first line) and, when the video needs it, the `publish` block (what else it needs to be published well: static
   §12), the labels
   in the video's language (static §5 "Labels": CapCut text whose font covers every character: `T static language --language L --font
   <file> --text <file>`), the places where a drawn annotation will elaborate the narration (encouraged, static §5 "Drawings and explanation animations are
   encouraged": one where a beat of the script gains from a drawn layer that shows or points at what is said, of any family and not only
   numbers (a quantity, steps, a cause, a contrast, a place, a time, a list, a thing to notice), what feels right and never overdone, and that still's
   prompt describes a calm area of the scene, a plain wall, an empty table top or an open floor, for the drawing (scenery only: the
   drawing itself is a CapCut overlay made later and is never in the prompt); static §5 "Drawings": the drawings
   themselves, with their positions, are written at S3 by the video's own agent once the stills exist, so an image it will draw on is
   kept still here, `"motion": "none"`, with the reason in the video's brief), each
   image's move and amount and each join decided from the spec's measured pattern (static §5 "Moves and joins": the reference's pace times
   this still's seconds, the references' order of moves; a join and the caption entrance from `AWL/data/capcut-catalogue.md`, only what it
   shows drawn, and only options marked free while the run's CapCut plan is free, `state.json → capcut_plan`), the `captions` block: the spec's text look (static §2: font file (an extra open-licence font may be downloaded when no listed font is a good match: `T fetch-font`, static §7 "Extra fonts"), size, colours, outline, box, case, highlight, the
   entrance as `animation` and `animation_s`) with this video's highlighted words (a `word_box`'s colour is the video's own, a first pick from its style lock's palette, never the last video's by default: static §7; settled from the finished stills before the edit, static §13); with an effects folder, the `effects` the spec's effects
   pattern calls for (static §2, §5 "Effects": each overlay or sound from `00-inventory/effects.md`, its moment and anchor second, how it
   is blended, its fit and volume, and why; only the ways the catalogue's Effects part shows playing). Nothing is left to a stock value:
   `T slideshow plan` lists what is undecided. The count follows the spec's seconds per still at the script's length; the narration's
   real timing settles it in S2 (and the effects' moments with it: a `join` or a `line` follows the timing, an `at_s` does not).
   More than one format (`state.json → static.extra_formats`): the plan is the primary's and serves every format; each prompt words
   its frame (shape, the subject's place, the caption band) the same way, so an extra format swaps those words only (static §5); the
   extra formats' own values (`by_format`) are read off their stills later, at S3 and S4.
8. **The bed** (every video, also when the references are voice only; static §6): `RUN/40-briefs/music.json`, one track per video,
   its `caption`, `bpm` and `why` reasoned from the spec's bed brief and this video's script and the story's feeling as you thought it through
   (the sections follow it, static §6), never from
   analysing the references' music (the user, 2026-11-06: "make sure we try to generate instrumentals that fit the video content type and
   narration based on the data collected from the references, no need to analyze their instrumentals too"); the image plan gets
   `"music": true`. The duration is set in S2 once the narration exists, and the level after the bed's check. A video longer than
   ACE-Step's 600 s may carry `sections` (one caption per part of the story, the same instruments and tempo; static §6); without them the
   toolkit makes equal sections.
9. **Check your own plan, skeptically, before anything is generated** (static §13 "Before any generation"; the user, 2026-11-08: "nothing
   should turn out as unexpected", and 2026-11-13: no judge checkpoints, you judge while you work), per video, before any speech, image or
   bed is made: for a video in another language run `T static units --run RUN --video NN` first (the references' English points
   converted by the script's ratio, static §4); read `T static forecast` and the family's numbers; settle the pace point, the narration's
   levers (its delivery and pace tags, the settings, the wording), the pause tags, the strong lines, every prompt the forecast marks and
   the bed's caption, sections and timing, editing those plan files yourself; run `T tts probe --run RUN --video NN` with the plan's
   levers (passage 1, billed, used by `say` as passage 1) and one more probe for each lever set you want to compare, as few as the
   account's characters allow (the forecast's `credits`); write each decision, its numbers and the result you expect into
   `RUN/40-briefs/video-NN-brief.md`. Ask what could be wrong with it. Then **one fresh reviewer reads the plan cold, a standing step** (static
   §13: a new agent with none of your context, given the narration's text, the pictures' plan, the title, thumbnail and the video's other
   published words, and the standard, never your reasoning; it reports where it would stop watching and what is unclear, flat, repetitive,
   unearned or untrue); you decide and fix before anything is generated, and more reviewers only if you want them. A decision that would
   break a lock or a rule of this phase is undone.
10. Show one line per video (number, subject, title, length, images, bed or none, the forecast pace) and go on without waiting.

**More videos** (static §10; `/analyze-with-loupe more <run> [N]`, or the user asking for more after a wrap-up; always in the session's
run, never a new one): no start question is asked; references new to the run's folder are taken in first (static §10 "New
references": the inventory again, A1–A4 for them only), and nothing else is analysed again; a spec that does not yet name the
niche's references gets them first (static §2 "The niche's references": the references whose field is the run's niche, read from
their cards, and their patterns and numbers beside the set's). `T static lock --run RUN` (the locks; a run made before the locks existed is asked its niche once,
with its subjects as context, and locks it with its style reference: the reference its style lock came from), the count when it is not
given (AskUserQuestion, header "Videos"), the length (AskUserQuestion, header "Length": standard or the user's own, as A5 says; the niche is already locked, so it is asked straight after the count and before anything is planned; stored again in `static.length_plan` for these videos), the language of each new video (AskUserQuestion, header "Language", as A5 says: `T static
language --run RUN --plan "<L1>[,<L2>…]"`; the narration model stays the run's), then steps 2 and 4–9 for the new videos only: no
voice samples (the narrator is locked), the pool's candidates carry their approaches beside the last video's (step 2), the stop asks
only for the subjects, `T static subjects --add … --story-form …` gives them the next numbers, their approaches and their
languages, and their scripts, image plans, titles and thumbnails keep the run's style lock and text look. Then `awl-analyze-produce` A9s for the new videos only.

## Rules this phase owns (contract item 36)

- Static keeps the references' delivery and changes their subject; a factual niche stays factual and sourced; the user picks the
  subjects (and, the first time, the voice) at one stop. The run's other stops are a QC-fix proposal (`ask`) and, with images by the
  user, their folder.
- One channel per run (static §10): the niche (a field, never a title or story form), the visual style and the narrator are the user's
  picks, locked; another niche is a clone. Each video has an approach and a language of its own, recorded with its subject (static
  §10, §6; the user, 2026-11-11); the agents keep room for their own creativity inside the niche.
- Engagement is thought through first (static §4b; the user, 2026-11-13), before the first line, prompt or caption; you judge your own
  work as you go and are skeptical of it, and fresh reviewers with none of your context are only for when you want a second opinion
  (static §13); nothing is made larger than its source, and a stand-in is framed as one (the truth rule).
- The plan's steps are items in `RUN/todo.md` (item 38; the user, 2026-11-13: tasks and to-dos to keep what is done and what is next): when A6s starts, add its steps and, per video, the design,
  the research it needs, the script, the image plan, the bed, the check before any generation and the standing fresh read; mark each as you work (`[~]` while at it, `[x]` and its result when done,
  `[-]` and the reason when dropped), set the `Next:` line before a long step, and mirror the items in the session's task list when it has task tools. A fresh reviewer is never given the to-do.
- Nothing religious or superstitious in a subject, a line, a prompt, a title or a thumbnail (static §11).
- Nothing indecent, gory or distressing in a subject, a line, a prompt, a title or a thumbnail (static §11b; the user, 2026-11-09).
- No Higgsfield and no Loupe in Static: no model menu, `T prompt-template`, `T qc-brief` or `T qc-consult`.

## Never (this phase)

- Never take a reference's subject, names, facts or lines; never invent a fact, a quote, a date or a number told as real; never put a
  claim told as real in a script that its fact sheet does not source (a niche whose story is invented makes it up by design and holds it
  to its own consistency, static §4b).
- Never write a script before the engagement is thought through, and never add it afterwards as a pass over a finished story (static §4b).
- Never pick the subjects or the voice for the user unless they said "you pick".
- Never ask for anything but the subjects and the voice at the stop (the paths and choices were asked at the start).
- Never put text, a sticker or an emoji into an image prompt unless the story needs that text (item 6; a thumbnail's words only as the
  references' thumbnails carry them, static §12).
- Never offer a subject outside the run's niche or one the run made; never a new narrator or visual style inside a run (a clone changes
  them, static §10); never anything religious or superstitious (static §11), indecent, gory or distressing (static §11b).
- Never lock or write a title form or a story form into the niche (a niche is a field, static §10), never give every video of a run the
  same approach without the written reason, and never write a video's script by translating an English one: it is written natively in
  the video's language with an English gloss per line (static §4).

## Hand-off

`T state --run RUN set stage=planned next_skill=awl-analyze-produce`, tick the plan in `RUN/todo.md` and set its `Next:` line (item 38), then invoke Skill `awl-analyze-produce`.

After a compaction, or on `resume`, read `RUN/todo.md` first (item 38), then re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
