---
name: cc-produce
description: /create-clips phase 5: spawn one production agent per planned video (shorts and long-form at the same time, up to four at once), collect their reports. Internal to that command.
user-invocable: false
---

# cc-produce: build the videos

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `RUN/20-analysis/portfolio.md` (the videos and the building order). Nothing else: the agents read their own briefs.
- `RUN/todo.md` (router rule 16): what is done and what is open; the plan already added one build item per video.
- `T state --run RUN get only`: the user's pick at the start (`long` = long videos only, `both`, `shorts`; none = both). A planned video of a kind the user did not pick (a short in a `long` run) is not built: say so in one line and leave it `planned`.

## Steps
1. **CapCut**: `Get-Process CapCut -ErrorAction SilentlyContinue`. Running is a blocker notice, not a question: the agents still write their edit plans, but cannot save a project. Tell the user once, in a line, to close CapCut; the videos stay `ready-to-build` and a later `/create-clips <run> resume` builds them.
2. **Waves**: first, in the background, `T music --run RUN --spans <every planned span of every video, A-B,C-D,...>` (the music detection of the whole plan at once, on the CPU while the agents work; the builders then find it cached). Claim each video as its agent starts: `T claim --run RUN --video <id> --by <this session's run name> --status building` (refused = another session is building it: skip it and say so). Spawn production agents (general-purpose, no `model` argument: they use the model the user picked; one per video; the first wave holds the long videos (they take longest, so the last video is done sooner) and the best shorts (they finish first), then the best videos first, at most `config.json -> agents.produce_max` = 4 at once; shorts and long-form share the slots; as one finishes, the next starts).
   Never two agents on one video. Spawn each wave in one message so they run together.
3. **The contract** each agent gets (write it in full; the agent never sees this skill or the command file):
   - the run path, the video id and kind, its brief `RUN/40-briefs/<id>-brief.md`, its output folder `RUN/60-outputs/<id>/`;
   - its own to-do `RUN/60-outputs/<id>/todo.md` (router rule 16): it writes its steps into it when it starts, keeps it current (`[ ]` not started, `[~]` in progress, `[x]` done, `[-]` dropped with its reason) and its report says what is done, what is not and what comes next; one file, one writer, so parallel agents never share one;
   - invoke the build skill of the run's mode (`T state --run RUN get mode`): streamer mode `cc-build-short` (kind short) or `cc-build-long` (kind long); game mode `cc-build-game` (long only: game mode has no shorts) and follow it (if the Skill tool or the name is not available, Read `C:/Users/Bulzart/.claude/skills/<name>/SKILL.md`);
   - read `RUN/20-analysis/brief.md` first; the rest only as its skill says;
   - the rules in one place: only cuts, captions, VFX (zoom, a short transition, a blur where safety says) and, in streamer mode, matching sound effects (game mode: no sound effects at all, and sponsor stretches cut out); religion and superstition avoided, gore, distress and nudity kept and blurred only where seen (nothing else is ever blurred: personal data, DMs, usernames, IDs and face cams stay as they are) (`CC/reference/safety.md`, which it reads);
     **captions follow the run's setting, which the contract states in one line: "captions: ON, box look" (Luckiest Guy word box), "captions: ON, highlight look" (Montserrat Bold word highlight) or, on an older run only, "captions: ON, no-box look" (every second of speech, in the style the user picked: `T state --run RUN get captions` is `on` and `get caption_style` is `luckiest-guy` or `montserrat-highlight`; an older run without `caption_style`: `on`, `box` or nothing is the box look, `no-box` the no-box look) or "captions: OFF" (the user picked no captions: no `T captions`, no caption track, no lexicon work; a spoken slur is audible, so the brief's marked spans are cut around)**; with captions ON profanity and slurs are always typed with one asterisk (f*ck, sh*t: `T captions` masks the user's default list by itself, the EDL's `captions.mask_terms` adds a word it lacks; the audio is never edited);
     the chunks are read-only; **the CapCut project is built with ONE command through the CapCut composition, `T capcut-build` (never clip by clip, never the MCP tools unless the build failed with a plain error that a re-run does not fix; its `problems` list must be empty or reported)**; CapCut closed for every save (if it is open: finish the plan, set `videos.<id>.status=ready-to-build`, stop); never ask the user anything, never spawn agents; every file it names in a report is a full path from the drive letter;
     with captions ON the look is the run's, the same in every video: the box look is Loupe video 04's (Luckiest Guy ALWAYS, upper case, the word-box, `captions.style: "word-box"` with `captions.word_box_max_words` 20000 so no video falls back to plain: no font in any EDL; the one exception is a character the font cannot draw, listed by `T captions` as `font_missing_glyphs`), only the box colour picked per video, to match its appearance (the user's `captions_color` from `state.json` fills it when the EDL leaves it open);
     the highlight look is Montserrat Bold ALWAYS, upper case, white words with a black outline and nothing behind them, only the word being spoken yellow #FFFF00 (`captions.style: "word-highlight"` with `captions.word_box_max_words` 20000, one CapCut text per moment holding the whole line), nothing of the look picked per video;
     the no-box look (older runs only) is Montserrat Bold ALWAYS, upper case, yellow #FFFF00 words with a black outline and nothing behind them, one text per caption (`captions.style: "no-box"`), nothing of the look picked per video; in every look the size stays `auto` (small to normal, for phones and tablets);
     no emoji in any text; never claim a check that did not run;
   - speed: it reads its reference files in ONE message, batches independent tool calls (all the contact sheets and frames it needs from ONE PowerShell call, the images read together) and keeps every check (a frame at every cut, `edl-check`, the read-back): batching saves time, skipping a check saves nothing that stays saved;
   - music (router rule 18): its skill's music step; never removes music without a claim on record, never fails or drops a moment over a song;
   - it returns at most 8 lines: the id, the status (`built`, `ready-to-build` or `failed`), the CapCut project name and path, the music lines (removed / listen / left as it is), the length (for a long video also how much of its planned source plays, from its paper edit), the blurred spans, the exclamations or touchy items left, for a streamer-mode long video any border that was not clean, blockers. It writes `report.md` and `posting.md` in its output folder; the harness may refuse a subagent's write of `report.md`: then it returns the full report text after a line `===== REPORT.MD =====` and this session saves it.
4. **Collect**: when an agent returns, check `RUN/60-outputs/<id>/report.md` exists (save the returned report text as that file when the agent could not) and `T state --run RUN get videos.<id>` says what it returned. A `failed` video gets one retry with the failure named, except one whose error starts with `not worth a video:` (its builder judged what is left not worth making, `cc-build-long`): that one is not retried and goes into the wrap-up as dropped, with its reason; a second failure stays `failed` and goes into the wrap-up.
   Tick the video's item in `RUN/todo.md` from its report and its own `todo.md`, set `Next:`, and add what the report leaves open (a retry, a blocker, a project waiting on CapCut); where the to-do and the run's own files disagree, the files are right: look at them before an item is done again, then correct the to-do (rule 16).
5. When every video is `built`, `ready-to-build` or `failed`: `T state --run RUN set stage=produced next_skill=cc-wrapup`, and set the to-do's `Next:` line to the wrap-up.

## Never
- Never more than four agents at once, never two on one project, never a production agent that edits another video's folder.
- Never build a video yourself in this session while agents run (the CapCut project index is shared).

## Hand-off
Invoke Skill `cc-wrapup`.
