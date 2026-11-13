---
description: Make narrated still-image videos (Static) - analyze a folder of reference videos, pick a niche family, a style, a narrator and a new subject per video, make the stills (OpenAI, FLUX 3 Klein on this PC, or yours), the ElevenLabs narration, an ACE-Step bed, drawn annotations and word-box captions, then build each video's CapCut project by ONE composition (T capcut-build) instead of tool by tool.
argument-hint: "<references-folder> assets <asset files/folders…> [examples <folder>] [effects <folder> | no-effects] | resume [run-dir] | more <run> [N] | clone <run>"
disable-model-invocation: true
disallowed-tools:
  - Workflow
allowed-tools:
  - Skill
  - Agent
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - ToolSearch
  - AskUserQuestion
  - SendMessage
  - WebSearch
  - WebFetch
  - "Bash(C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe *)"
  - "Bash(python *)"
  - "Bash(ffprobe *)"
  - "Bash(capcut *)"
  - "PowerShell(& 'C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe' *)"
  - "PowerShell(& C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe *)"
  - "PowerShell(python *)"
  - "PowerShell(capcut *)"
  - "PowerShell(ffmpeg *)"
  - "PowerShell(ffprobe *)"
  - "PowerShell(cd *)"
  - "PowerShell(Get-ChildItem *)"
  - "PowerShell(Get-Process *)"
  - mcp__elevenlabs__search_voices
  - mcp__elevenlabs__search_voice_library
  - mcp__elevenlabs__get_voice
  - mcp__elevenlabs__list_models
  - mcp__elevenlabs__check_subscription
---

# /create-static

Arguments: `$ARGUMENTS`

You are running the **/create-static** command: narrated still-image videos ("Static") in the craft of the references the user gives, on new subjects, each video's CapCut project built by **one composition**.

This file is only the **router**, and it is small on purpose. The pipeline is split into **phase skills** (`cs-*`, one per step) and its rules and data into **section files**
(`CS/reference/<name>/`), so that every phase loads only what it needs and the context of a run does not rot. The skills are interconnected: each ends with a hand-off that names the next one.

`CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` ·
`T` = `"$PY" "$CS/scripts/cs.py"` (one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = `CS/runs/<stamp>-<slug>/`.

## How the pipeline loads (obey throughout)

1. **Start by invoking Skill `cs-start` with `$ARGUMENTS` as its args**, after the resume and feedback checks below. Then follow each skill's **Hand-off**: when a phase ends it records
   `T state --run RUN set stage=… next_skill=…` and names the next skill. Invoke that skill when you reach it, never earlier.
2. **Load only what the current phase names.** Each skill has a "Read now" list of exact section files (some conditional); read those and nothing else unless a step
   says so. Never Read a whole reference; never run `docs_tool.py join` in a run. A section already read in this session is not read again.
3. **Citations.** `file.md §id` is a section of `CS/reference/<file>/`. `file.md` itself is only an index (a table `§ | section | file | KB`). Resolve a citation that no "Read now" list covers with that
   table or Glob `CS/reference/<file>/*_<id>_*.md`; an id that is not a row lives in its nearest parent row. Labels such as A5, S4, X10, "item 36" resolve with the **labels** table below. A section that points at `generation-system.md`, `text-and-format.md` or `voiceover.md` points at documents of modes this command does not have: follow the section's Static rule and ignore the pointer.
4. **A phase boundary is a safe cut.** Everything a later phase needs is in `RUN/state.json` and the run files, not in this conversation. When many phases lie behind you and the context is
   long, tell the user in one line that they may run `/compact` (or open a new session and send `/create-static resume <RUN>`); nothing is lost. After a compaction, or on resume,
   **re-invoke the skill named in `state.json → next_skill`**: its text may have been summarised away. Inside the per-video work a run resumes at the video level
   (`state.json` holds `video` and `next_skill`; the files on disk show the step reached). **Read `RUN/todo.md` first** (item 38): it says where inside the phase the work stood and what is open. A run made before the to-do existed has none: write it now from `state.json` and the files on disk, then go on.
5. **Agents never receive this file.** A production agent gets a contract (`T contract --run RUN` writes it) that names the skills to invoke (Skill tool; if it is unavailable or the name is not found, Read
   `C:/Users/Bulzart/.claude/skills/<name>/SKILL.md` and follow it); it reads the same section lists as the main session and nothing else. An analysis agent is briefed by the prompt
   in `reference/analysis-protocol/` §7.

## Resume, more videos, a clone, and a video reported as wrong

1. **Resume?** If `$ARGUMENTS` starts with `resume`, or names a run folder of this library:
   - read its `state.json` (`T state --run <run> get`);
   - summarise where it stopped (stage, next_step, videos done);
   - continue from `next_step`. Never re-ask a question that is answered in `state.json`.
   Then invoke the skill named by `next_skill` in `state.json` (`stage=analyzed next_step=…` → `cs-plan`; videos in `videos[]` but not all done → `cs-produce`).

2. **More videos of a run?** If `$ARGUMENTS` starts with `more` (`more <run> [N]`), or the user asks for more videos after a wrap-up: `T static lock --run <run>` (the run's locks), then invoke Skill
   `cs-plan` and follow its **More videos** (static §10: subjects of the run's niche only, each with an approach of its own, the same narrator, visual style and text look; nothing is asked
   at the start but the count, the length (standard or the user's own, before any planning) and the language of each new video; only references new to the run are analysed).
   **One run per session** (the user, 2026-11-07: "no need to generate multiple runs for each generation we do inside one session ... a new run session or a clone session is the only thing that creates a new run folder"): once a session has a run, every later request
   in it (more videos, new references in the run's folder) continues that run, never `T new-run`; new references are taken into that run (static §10 "New references"). Only a new `/create-static` start or `clone <run>` makes a run folder.

3. **A clone of a run?** If `$ARGUMENTS` starts with `clone` (`clone <run>`): `T clone-run --from <run>` (a new run with the analysis copied, static §10), then invoke Skill `cs-study` at A5 for the clone
   (its niche, the narrator and the visual style kept or picked again, the count, then the narration model and the language of each video) and follow the hand-offs from there.

If `$ARGUMENTS` or the opening message reports a delivered video as wrong (it names a video, a CapCut project or a run and says what was not right), invoke Skill `cs-feedback` first
and handle it before anything else (item 22).

## Core rules (one line each; the full text of each sits in the skill that owns it)

The item numbers are stable labels that the skills and the references cite; a number that is not listed here does not apply.

1. **Normal command, never a workflow.** Run everything in this conversation with ordinary tools.
   Never create, call, convert to, or delegate to a Claude Code Workflow (the `Workflow` tool is
   disabled for this command).

2. **Agents.** Analysis agents: 0 by default, 1 for many references, 2 for a large folder. Production agents: one per video, at most 5 at once; they never overlap, never ask, never spawn agents. A long video's stills are split across image agents (`cs-produce` A9b). → `cs-produce`

6. **Text.** Static generates clean pictures (no text drawn in them but what a thing carries) and places all overlay text as CapCut text in the references' own text look (item 36), never a house style. **No sticker or emoji added, ever** (the user, 2026-11-03): none is added to a generation as a decoration or placed in an edit (as a graphic or in a text layer), in any mode; one that belongs naturally to the scene (a chat's emojis on a phone someone is texting on, a product's own label) is scene content. A Static **drawn annotation** (item 36: a line, an arrow, a circle, a highlight or a word drawn over a still to explain what the narration says) is not a sticker: it is a drawing the agent specifies and the toolkit renders; an icon, badge, emoji or decorative arrow is still never drawn. → `cs-plan`, `cs-images`, `cs-edit`

7. **Client- and niche-agnostic.**
   - Never assume an industry, a product, a character swap, or a fixed template.
   - Infer the domain, the entities, what to preserve / replace / adapt / ignore, and the objective
     from the files and instructions.
   - Documents are authoritative requirements.

8. **Provenance.** In analysis, plans and briefs, keep separate:
   - **[E]** evidence
   - **[I]** inference
   - **[U]** user instruction
   - **[A]** client asset
   - **[M]** model knowledge
   - **[G]** generation instruction

10. **Honest reporting.** Never claim a generation, upload or check that did not happen. Report
    failures with the real error.

12. **Generation discipline.** Every paid call goes through the toolkit's own ledger (`T image generate`, `T tts say`, `T music`): never resubmit after a timeout or an unclear answer until the ledger is checked; never repeat an identical finished request; no test or "just in case" calls. → `cs-sound`, `cs-images`

14. **The product appears only when the assets hold one** (item 36): the client's product is in a video only when the user's assets hold one; Static's assets are usually the characters. When they hold one, it is swapped, contained or placed naturally, physically and logically correct. → `cs-study`, `cs-plan`, `cs-images`

15. **What this command asks**: at the start the inputs and the four choices (`cs-start`); after the analysis the niche family, the style reference, the narrator, the format(s), the length, the narration model and each video's language (`cs-study`); the subject-and-voice pick at A6s (`cs-plan`: the one stop) and, with images by the user, their folder; the new draw after a QC finding, only when the user chose `ask` (item 27). Blockers are reported, not asked; no reference review or "Go" before a generation. → `cs-start`, `cs-study`, `cs-plan`, `cs-produce`

18. **Examples** (the user's own finished videos, optional) are study material for the craft; never assets. → `cs-prepare`, `cs-study`

20. **The pipeline is also the creative team** (`reference/creative-direction/`): goal, audience, trend read, scored concept seeds, sharpness gate, copy test; in Static the team of static §0. → `cs-study`, `cs-plan`

21. **Brand guardrails** from the client's documents, when the user gives any, decide what may be picked and what must be edited (core hit → dismiss; peripheral → edit). The pipeline has no content rules of its own; Static has two: nothing religious or superstitious (static §11) and nothing indecent, gory or distressing (static §11b). → `cs-prepare`, `cs-study`, `cs-plan`

22. **No error ledger**: a video the user reports as wrong is diagnosed in pipeline terms in its brief, then fixed; a lesson the references do not hold is written, generalised, into the section that owns it (on the user's yes). → `cs-feedback`

24. **Audio ingest** is `whisper` in Static and is never asked: every reference's audio is transcribed locally and `state.json → audio_ingest` is the only source; whatever needs the audio file itself (loudness, the sound profile) runs on it. → `cs-start`, `cs-prepare`

25. **Scripts gather, agents decide.** The toolkit measures, extracts, records and calculates and never judges: no verdict, label, rank or gate comes from a script (`audio-profile`, `edit-profile`, the OCR spans, the ledger, `static forecast`, `tts fit` and the build's read-back return numbers and facts). Every judgement is the agent's, written with its reason where the step records it; the numbers the references give are rules of thumb. → every skill, `pipeline/preprocessing.md`

27. **QC fixes** (Static): at the start the user chooses `ask`, `auto` or `off` (`state.json → qc_fixes`) for QC and the new draw after a QC finding. `ask`: from the first video on, when QC finds issues in a video's images that only a new draw can fix, the production agent prepares the fix and stops with a proposal, the main session asks the user, and nothing is drawn until the user says yes. `auto`: the QC agents draw again once or twice on their own and ship the best take flagged. `off`: no QC agent after a video's first images at all; each image is made once and delivered unchecked, and the user says what to fix after the wrap-up (item 22). Local post-fixes, drawings and edit fixes never ask. → `cs-start` (the question), `cs-images`, `cs-produce`, `cs-record`, `cs-wrapup`

34. **The user's folders are read-only** (the user, 2026-10-27): nothing in the references, assets, examples or effects folders is moved, renamed, deleted or overwritten by this session or any agent; a file needed in the run folder or elsewhere is copied, never moved (only the toolkit adds its own derived folders there). The `awl_input_guard` hook refuses a move, delete, Write or Edit inside the references, examples or effects folders of a run that is not done. → every skill

36. **Static: narrated still-image videos** (the user, 2026-11-05). From its first step every agent of a Static run works as the team of static §0 (a YouTube short- and long-form strategist, storyteller, sociologist and human-behaviour expert, attention psychologist, fact-checker, art director and editor; the user, 2026-11-06), ambitious and disciplined by the references' data. The references are read as one set; when they mix niches, each video's plan is drawn mostly from the references of the run's niche, with the whole set's patterns kept beside them and used where the agent finds they hold (the user, 2026-11-09; static §1, §2, §13). The references (narration and storytelling slideshows) are studied at 2 fps flat with their audio (Whisper, not asked; no effort level, the user, 2026-11-07), with their real YouTube titles from their file names (`<channel>_<title>_<YouTube id>`; or a `context.txt` with thumbnails when the folder has one; static §12); a reference another run already analysed is copied from it, never analysed twice (`T reuse-analysis`); a run is one channel (static §10): one niche, one visual style (a reference the user names) and one narrator, the user's picks, locked for every video the run ever makes (`more <run>` adds videos of that niche; `clone <run>` copies the analysis into a new run for another niche, nothing analysed twice); the niche is a **family of content**, a field and never a title or story form (the user, 2026-11-11: "we lock the niche family", not "N days of X"), and each video has an **approach** of its own inside it (story form, angle, point of view, time frame, scale, title form, pillar), taken from the whole set of references and from the agents' own creativity, varied across the run and recorded with its subject (static §10, §3), and a **language** of its own, asked per video from the live ElevenLabs list: the references may be English or mixed, the content is made natively in the language the user picks, each line with an English gloss (static §4, §6); nothing religious or superstitious in any subject, line, caption, picture or sound (static §11), and nothing indecent, gory or distressing either (no nudity, implied included, no gore or injury, no extreme distress, nothing a family audience is not shown or told; the user, 2026-11-09; static §11b); every video also gets its YouTube title and thumbnail (static §12); real things look like themselves (static §5, the user 2026-11-07): a company or brand the story is about gets its official logo in the stills where it comes in and again later (`T fetch-image`, `T image brand`, never drawn by the model), a known person looks like them (public photos with their anchor); the length is the user's pick, asked at A5 after the niche is locked and before any planning or generation (the user, 2026-11-12): **standard** (the niche's references' length: each video's own the agent's from their lengths and what drives them) or **their own** (a total, or minutes more or less than standard, for the batch or per video), `state.json → static.length_plan`, written as each video's `target_length_s`; a bed over ACE-Step's 600 s is made in sections joined with crossfades, and a long video's stills are split across image agents; the videos keep their craft on a new subject the user picks from a pool (real and sourced in a factual niche; fitted to the assets' characters); the stills come from the OpenAI Images API (`OPENAI_API_KEY`, every call in the ledger through `T image generate`), from FLUX 3 Image Klein in int8 on this PC (the user, 2026-11-06: `AWL_IMAGE_PYTHON` and `AWL_IMAGE_ROOT`, the same ledgered `T image generate`, no cost) or from the user's own generation of the pipeline's prompts (one folder, copied in), the user's pick at the start; one voice per run (five samples, each with its file path, the user picks), made by the ElevenLabs model the user picks at the start from the live list (the ElevenLabs MCP's `list_models`, else `T tts models`; Eleven v4, v4 Turbo or another whose facts the run has recorded: static §6 "The models") on the user's key (`ELEVEN_API_KEY`), its pace, pauses and length set in the request (the voice, its settings, the words, the audio tags and, where the model has one, its speed setting: Eleven v4 has no speed) and the delivered audio not edited (the user, 2026-11-09: "do not edit the delivered generation without any exception": no cut, trim, compressor, fade or added silence) but for the two changes the user then allowed: one gain only when its loudness sits outside the references' measured range, and one capped speed-up with the pitch kept (`T tts tempo`, at most config static.narration.tempo_max) made only on the user's yes after they have seen the delivered project and the pace's numbers, never the agent's call: the pace is reached in the generation first (the user, 2026-11-09: "only speedup on their permission never else"; static §6, §13 J2); an instrumental bed from a local ACE-Step 1.5 under every video, written from the references' data (the content type, the narration, the story's arc), never from analysing their music; the edit is a CapCut project at the format the user picks at A5 (the best fit for the references first; its export is the final), or one per format when the user picks more than one (the user, 2026-11-08: the same plan, narration and edit, the same prompts with only their frame words swapped, and a CapCut project per format, each by `T capcut-build --format <tag>`; static §2b), made in CapCut directly, by one composition (item 39; no local render, the user, 2026-11-07) with the captions from the narration's words in the references' own text look (font, size, colours; no house style); a strong line is a line with its own delivery tags, sparingly. The agents that make a video can also **draw and animate** over a still (the user, 2026-11-11: "the agents editing the video should also to be able to draw, and animate too, like combining flux klein image + drawing or animation"): lines drawn on along a path (dashed or solid, straight or curved), arrows, circles, boxes, coloured highlights wiped or faded in, and words typed or popped in, with a hand-drawn wobble when the references have it, timed to the spoken word and read off a gridded copy of the still (`T draw grid`, `T draw words`); the toolkit renders each drawing as a transparent clip (`T draw render`, with composite previews to look at) that `T slideshow plan` and `T capcut-build` place over the still as an overlay CapCut plays here (static §5 "Drawings", §7), the look from the references' own annotations when they have them and the agent's own inside the style lock when not; the image holds still while a drawing is on it, nothing is generated by a model, no credits. The agents may also **download an extra font** when no listed one is a good match for the video (the user, 2026-11-11: "add a permission for the agents to download extra fonts on capcut if the available ones do not seem a good match for the video"): `T fetch-font`, open licences only (SIL OFL 1.1 or Apache 2.0), copied into the library's `fonts/` with its row (static §7 "Extra fonts"). An optional effects folder (the user, 2026-11-06: "sound effects, and green screen transitions"), read-only like the references, is measured by `T effects scan`; the plan picks from it what plays the part of the references' own devices (an overlay transition, a light leak, a sound on a cut), never a sticker, emoji or badge (item 6), and `T capcut-build` writes each one only by a way the CapCut effects check verified on this PC (static §9). The product appears only when the assets hold one (item 14). → `cs-start`, `cs-prepare`, `cs-study`, `cs-plan`, `cs-produce`, `cs-sound`, `cs-images`, `cs-edit`, `cs-record`, `cs-wrapup`

37. **Static: evaluating the work** (the user, 2026-11-08: "nothing should turn out as unexpected"; then 2026-11-13: "every judge in this static mode should be removed, the pipeline should be intelligent to evaluate and be skeptical in itself and judge while it works, but spawn different judges who have no context on the main agent"). Every value a Static output will carry is chosen on purpose from the references' measured numbers before it is generated, written down with the result it should give, and the measured result is read against that forecast; a miss is explained and corrected, or recorded with its reason. There is no judge agent and no checkpoint: whoever makes a plan, a line, a still, a bed or an edit judges it as it is made, skeptically (static §13: the checks before any generation, after the narration, between image stretches, before the bed and before the edit are the working agent's own), and fresh reviewers with none of the working agent's context are used: one fresh read of the plan before the first generation of each video is a standing step (the user, 2026-11-13: "make one fresh read of the plan before the first generation a standing step, still with no judge"), others only when a second opinion is worth having (a reviewer gets the artifact and the standard, never the reasoning; it reports and never changes a file or generates; the working agent decides and fixes). `T static forecast` calculates what a plan will give and `T tts fit` learns the voice's numbers; nothing leaves a lock, a start choice, the memory guard or the references' data. Records: the video's brief `40-briefs/video-NN-brief.md` and `video-NN-forecast.json` (a run planned before 2026-11-13 keeps its `video-NN-judge.md` as history). → `cs-plan`, `cs-sound`, `cs-produce` (between stretches), `cs-images`, `cs-edit`

38. **Task lists and a to-do file** (the user, 2026-11-13: "add to the pipeline so that we use tasklist and todo lists in order to keep context of whats done and whats about to be done"; every mode). What is done and what comes next never lives only in a conversation. The main session keeps `RUN/todo.md`, a markdown checklist it writes when the run is created and updates at every step boundary and before any long wait (a generation, a recording, an agent): `[ ]` not started, `[~]` in progress, `[x]` done, `[-]` dropped with its reason; a `Next:` line on top that names the very next action; items grouped by phase and, from the production phase on, by video; each item names its files by their full path, and a finished item its result in a few words (a count, a pass or fail, a folder). Each production agent keeps the same for its own video in `RUN/60-outputs/video-NN/todo.md` (a file has one writer, so parallel agents never share one), and its report says what is done, what is not and what comes next. Beside the file the session keeps its task list (the task tools, TaskCreate and TaskUpdate, when the session has them; the file alone when it has not): the same items as tasks, one in progress at a time, each marked done the moment it is done and never in a batch at the end, and new work (a redraw, a re-record, a fix, an agent's blocker) added as soon as it appears. On a resume or after a compaction the to-do is read first: it says where inside a phase the work stood, which `state.json → next_skill` cannot. A fresh reviewer (item 37) never gets it. The to-do is a record and never a gate: no script reads it, nothing waits on it, and a changed or skipped item is marked with its reason, never deleted; a compaction summary keeps its open items. Where the to-do and the run's own files disagree (`state.json`, the ledger, what is in the folders), the files are right: look at them before an item is done again, then correct the to-do. → `cs-start`, `cs-produce`, `cs-plan`, `cs-sound`, `cs-images`, `cs-edit`, `cs-record`, `cs-wrapup`

39. **The CapCut project is one composition** (the user, 2026-11-13: "use capcut composition for everything if possible for faster delivery"). Every video of a Static run, in every format, has its CapCut project built by ONE command, `T capcut-build --run RUN --video NN [--format <tag>]` (`cs-edit`, `CS/reference/capcut-build.md`): the timeline `T slideshow plan` wrote becomes a single `capcut compile` (the stills in place, the narration and the bed, the joins, the effects and the drawings, the caption texts with their styles, the labels), one write pass over the project's files writes what compile has no operation for (the moves, the fonts, the entrance), then the repair and a read-back that answers with a `problems` list. Measured on a 12.7-minute video with 4,413 caption texts: 23 s, against about 3 minutes for the single commands, and the two projects equal segment by segment (the caption times to the microsecond). **Never the CapCut MCP tools, never `capcut import-srt`, never `capcut lint --fix`, never a save with force, never a project built clip by clip, tool by tool or finished by hand**; CapCut must be closed (the build stops with exit 3 and changes nothing otherwise); the build writes the plan's values and never picks one (item 25). → `cs-edit`, `cs-record`, `cs-wrapup`

## Phases (the skills)

| Phase | Skill | Next |
|---|---|---|
| Start: inputs, the four choices, the setup check, the run | `cs-start` | `cs-prepare` |
| A1–A2b inventory, preprocessing (2 fps, Whisper), documents, guardrails, asset registry | `cs-prepare` | `cs-study` |
| A3–A5 analysis, synthesis, the niche family, style, narrator, format, length, narration model, language, count | `cs-study` | `cs-plan` |
| A6s subjects and voice (the one stop), scripts, image plans | `cs-plan` | `cs-produce` |
| A8–A10 prepare every video, S2 for every video, the production agents, their reports | `cs-produce` | `cs-wrapup` |
| S2 each video's narration, timed words, image spans, the bed | `cs-sound` | back in `cs-produce` |
| S3 a video's stills, thumbnail, drawings | `cs-images` | `cs-edit` (the production agent) |
| S4 the timeline and the CapCut project by ONE composition (`T capcut-build`) and its read-back | `cs-edit` | `cs-record` |
| X10 deliverables, README row, result.json | `cs-record` | the agent ends |
| §6, §6b wrap-up and the feedback question | `cs-wrapup` | — |
| item 22 a delivered video reported as wrong | `cs-feedback` | — |

**The flow:** this session runs `cs-start` → `cs-prepare` → `cs-study` → `cs-plan` → `cs-produce`; `cs-produce` runs S2 `cs-sound` for every video (and, with images by the user, `cs-images` for the prompts and the folder), then spawns one production agent per video; each production agent runs
S3 `cs-images` → S4 `cs-edit` → X10 `cs-record`. Then `cs-wrapup`.

**Labels** (as cited in the skills and the references): A1, A2, A2b → `cs-prepare` · A3, A4, A5 → `cs-study` · A6s → `cs-plan` · A8, A9, A9b, A10 → `cs-produce` · S2 → `cs-sound` · S3 → `cs-images` · S4 → `cs-edit` · X10 → `cs-record` · §6, §6b → `cs-wrapup` ·
item 22 → `cs-feedback` · item 24 → `cs-start`, `cs-prepare` · item 25 → every skill · item 27 → `cs-start` (the question), `cs-images`, `cs-produce` · item 34 → every skill and agent (the `awl_input_guard` hook) · item 36 → every skill · item 37 → `cs-plan`, `cs-sound`, `cs-produce`, `cs-images`, `cs-edit` · item 38 → every skill · item 39 → `cs-edit`, `cs-record`, `cs-wrapup`.
A rule that two phases both act on is written in both skills.

## Never (global; each skill carries the rest of the Never list for its own phase)

- Never use or create a Claude Code Workflow.
- Never spawn more than 2 analysis agents or more than 5 production agents at once. Never give agents overlapping work.
- Never build a CapCut project tool by tool or by hand: `T capcut-build` is the only route (item 39). Never use the CapCut MCP tools in this command.
- Never take client assets from the references folder: they are reference material, and may show other products or executions.
- Never claim results you did not verify.
