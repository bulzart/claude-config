---
description: Take a processed livestream run folder (3-minute chunks, frame sheets, transcripts, chunk reports) and turn it into CapCut projects with cuts, captions and VFX. Two modes, a captions choice (captions or no captions) and, in streamer mode, a videos choice (long videos only, or long videos plus shorts), all picked by the user at the start - streamer clipping (a person's stream - one brief research agent on the streamer, their audience and the topic, then the moments; long-form videos, and short-form ones when the user picked them, with matching sound effects) and game clipping (a match broadcast such as BLAST Premier CS2 or a Dota 2 game - research of the game, the event and the teams, then rounds and fights, how much of each to keep; long condensed-match videos only, no shorts, no sound effects, sponsor stretches cut).
argument-hint: "<run folder or session name> [mode=streamer|game] [captions=on|off] [captions_color=\"#E02B3A\"] [game=\"Counter-Strike 2\"] [only=long|both|shorts] [notes=\"guest, topic, what you want\"] [streamer=\"Name\"] | resume [run]"
disable-model-invocation: true
disallowed-tools:
  - Workflow
allowed-tools:
  - Skill
  - Agent
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - ToolSearch
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
  - "PowerShell(Get-ChildItem *)"
  - "PowerShell(Get-Process *)"
  - "PowerShell(New-Item *)"
  - mcp__capcut__capcut_list_drafts
  - mcp__capcut__capcut_clone_draft
  - mcp__capcut__capcut_read_timeline
  - mcp__capcut__capcut_add_video
  - mcp__capcut__capcut_add_audio
  - mcp__capcut__capcut_add_track
  - mcp__capcut__capcut_trim_segment
  - mcp__capcut__capcut_split_segment
  - mcp__capcut__capcut_move_segment
  - mcp__capcut__capcut_set_props
  - mcp__capcut__capcut_set_track_mute
  - mcp__capcut__capcut_delete_segment
  - mcp__capcut__capcut_validate
  - mcp__capcut__capcut_save
  - mcp__capcut__capcut_discard
  - mcp__capcut__capcut_undo
---

# /create-clips

Arguments: `$ARGUMENTS`

You are running the **/create-clips** command: the clip-farming editor for livestreams and matches. It has **two modes**, each with its own logic: **streamer clipping** (a person is the show: jokes, hype, arguments, clips, memes, lingo) and **game clipping** (a match is the show: the clips are built on rounds and fights).
**The user picks the mode, the captions setting and, in streamer mode, which videos get made, from the very start:** `cc-start` asks them in ONE dialog (each skipped when the arguments carry `mode=`, `captions=` or `only=`), stores the answers as `mode`, `captions` (`on` by default) and `only` (`long` = long videos only, `both` = long videos plus shorts; game mode is long only and is not asked) in `state.json`, and every later phase follows them; nothing guesses the mode or the videos. This file is only the **router**; the work is split into **phase skills** (`cc-*`) and **reference files** (`CC/reference/`), so every phase loads only what it needs and a long run does not rot.

`CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder the user names.
The run folder is what `cc.py watch` made from the Twitch Chunk Recorder's chunks: `CC/README.md` is the contract (layout, rec time, files).

## How it loads (obey throughout)
1. **Resume?** If `$ARGUMENTS` starts with `resume` or the run's `state.json` already has a `stage`: `T state --run RUN get`, say in one line where it stopped, and invoke the skill in `next_skill` (a `produced` run with videos `ready-to-build` goes back to `cc-produce`). Never re-ask what `state.json` answers.
2. Otherwise **start by invoking Skill `cc-start`** with `$ARGUMENTS`, then follow each skill's **Hand-off**: it records `T state --run RUN set stage=... next_skill=...` and names the next skill. Invoke it when you reach it, never earlier.
3. **Load only what a phase names.** Each skill has a "Read now" list; read those and nothing else unless a step says so. A phase boundary is a safe cut: everything a later phase needs is in `RUN/state.json` and the run files. When many phases lie behind you, tell the user in one line that `/compact` is safe (or `/create-clips resume <RUN>` in a new session).
   After a compaction re-invoke the skill in `next_skill`: its text may have been summarised away.
4. **Agents never receive this file.** An agent gets a contract that names the skill to invoke (Skill tool; if it is unavailable, Read `C:/Users/Bulzart/.claude/skills/<name>/SKILL.md`) and the reference files that skill lists.

## Phases (the user picks the mode in phase 1; `T state --run RUN get mode` says which column a run follows)
Before the command runs, while the chunks are downloaded, the processor makes each chunk's sheets, audio numbers and transcript, and a separate headless **Haiku reporter session** (`claude -p`, Haiku 5.5, high effort) writes a **report** of what the chunk shows: observations only, never a verdict (`CC/reference/reporter.md`).
The command's agents read those reports; nothing is spawned to read the raw chunks.
| Phase | Streamer mode | Game mode | Does (streamer / game) | Next |
|---|---|---|---|---|
| 1 intake | `cc-start` | `cc-start` | **asks the mode, the captions choice and (streamer mode) long only or long plus shorts**, the run, the chunk table, any missing reports, folders, **starts the ONE research agent in the background**, the size of the work | `cc-profile` / `cc-profile-game` |
| 2 profile | `cc-profile` | `cc-profile-game` | the recon (while the research agent works), its note and the context brief. Streamer: the streamer and their audience, the topic or game or event and what the internet says about it, the people, what works as a clip. Game: the game, the event and its storylines, the teams and players, esports clip trends; and where the score and the clock sit on screen, with the screen scan started in the background as soon as they are known | `cc-scan` / `cc-scan-game` |
| 3 scan | `cc-scan` | `cc-scan-game` | mining agents (the user's model) read the chunk reports in blocks (at least two, side by side) and decide. Streamer: summary, moments, richness per chunk. Game: the score read off the screen over the whole match, then a card per round or fight, what is not play (sponsor stretches included), extras. Both: what to blur (gore, distress, nudity only) or avoid | `cc-plan` / `cc-plan-game` |
| 4 plan | `cc-plan` | `cc-plan-game` | merge and a check of what will be used. Streamer: the long-form and short-form videos. Game: a keep verdict for every round or fight (full, trim, flash, skip) and the long condensed-match videos (no shorts). One brief per video | `cc-produce` |
| 5 produce | `cc-produce` | `cc-produce` | one production agent per video, up to 4 at once (streamer: shorts and long-form together) | `cc-wrapup` |
| per video | `cc-build-short` / `cc-build-long` | `cc-build-game` | study, EDL, captions (when on), `capcut-build` (one composition, the finishing and the read-back), report | (returns) |
| 6 wrap-up | `cc-wrapup` | `cc-wrapup` | verify, deliverables README (game mode also `rounds.md`), what to do next | none |

## Core rules (the full text sits in the skill or reference that owns each)
1. **Normal command, never a workflow.** Everything runs in this conversation with ordinary tools and the Agent tool; the `Workflow` tool is disabled.
2. **Agents**: ONE research agent (web only, brief, a budget of tool calls, started in `cc-start` so it overlaps the rest: the user, 2026-11-13: not four agents, not a deep research), mining agents at most 6 at once (at least two blocks), production agents at most 4 at once, one per video, never overlapping, never asking, never spawning agents. → `cc-start`, `CC/reference/research-agent.md`, `cc-scan`, `cc-produce` (and their game-mode twins)
   **Models** (the user, 2026-11-12/13): every agent and the main session use the model the user picked with `/model`: never a `model` argument, never a question about it. The only Haiku is the **chunk reporter**, a separate headless `claude -p` session per chunk made by the processor while the stream is downloaded (config `report`):
   it reads the chunk's sheets, audio numbers, transcript and chat and writes what they show. It is a reporter and never a decider: no verdict, no label such as "ace", no name corrected, nothing ranked or kept. Every decision is a working agent's.
3. **Scripts gather, agents decide.** `cc.py` measures, extracts, converts, reads numbers off the screen and writes what an agent decided; no verdict, rank or gate comes from a script. Every judgement is a working agent's, with its reason written where the step records it. A report is data about a chunk, not a decision about it.
4. **Think like a clip farmer who lives on the internet.** Before deciding anything, the agents are in touch with the streamer and their audience, the topic of the stream (a game, a release, an event, a trend: what everyone is saying, joking about, hyping and clipping about it), the people on it, and what works as a clip right now. The research is social, not scientific
   (the user, 2026-11-12), and brief (one note, `research.md`). Every claim is tagged [W] web, [S] this stream, [M] model memory, [I] inference; nothing is invented. → `cc-profile`, `CC/reference/research-playbook.md`, `CC/reference/research-agent.md`. In game mode the same spirit covers the game, the event, the teams and players and the esports clip trends. → `cc-profile-game`, `CC/reference/game-research-playbook.md`
5. **Two kinds of video at once, when the user picked both** (streamer mode asks at the start: long videos only, or long videos plus shorts; `only` in `state.json`: `long`, `both`, or `shorts` from an argument; a run made before the question has none and makes both). Short-form (Shorts, TikTok, Reels): up to 3 minutes each, the length follows the content, as many as are good. Long-form: each video one whole watch of about 25 minutes to an hour, set by the content and its context and not by the clock (the user, 2026-11-14: a 7-hour stream might give 36, 43 and 27 minutes, not an hour and a leftover that starts in the middle of a story): the mining agents record the stream's acts, the planner sets the borders between the videos between acts, checks each border by reading the words and never leaves a story half in one video and finished in the next, and the number of videos, and how much of the stream is used in all, is what the content earns (the user, 2026-11-14: from an 8-hour stream the agents may make three hours of videos if the analysis says so, or only 32 minutes, or none, and nothing is included just to reach a number of minutes), made of straight runs of chunks and pickups, the agent's call; the dull parts are left out, and where something kept leans on a bit of one the agents may keep that bit as context, judging from what the stream shows (the user, 2026-11-14). → `cc-plan`, `CC/reference/portfolio.md`, `CC/reference/context-keeping.md`
   **Game mode makes long-form only, never a short** (the user, 2026-11-13): the units are rounds (CS2, Valorant) or fights and objectives (Dota 2, League); every unit gets a keep level (full, trim, flash, skip) with its reason: a round with no impact is dropped, a quiet one that a viewer would lose a detail of is kept short, a big one is kept whole. The videos are condensed matches, one per map or game; **when the recording holds 2, 3 or more different matches, every game of every match is a video of its own in its own CapCut project, never two matches in one video** (the user, 2026-11-14), found from the teams changing on the scoreboard. Sponsorship and the like (sponsor stings, betting segments, ad breaks, promos) is skipped totally. → `cc-plan-game`, `CC/reference/game-clipping.md`
6. **The edit is only**: cuts, captions (when on), VFX (a zoom, a short transition, a blur where rule 7 says) and, in streamer mode, sound effects that match the situation. No music, no stickers, no emoji, no text overlay but captions, no filters, no drawings. **Game mode has no sound effects at all.**
   **Captions follow the user's choice at the start** (`captions` in `state.json`, `on` by default, a run made before the option has none: that means on): with captions ON every second of speech is captioned, in every video; with captions OFF no caption track is made, no lexicon work is done, and a spoken slur (which nothing masks, no audio is edited) is cut around by the plan. **Profanity and slurs are always masked in the captions** (the user, 2026-11-14: "words such as fuck, faggot, pedo, shit, gay and more always write in captions like f*ck, f*ggot or similarly"): one asterisk in place of the first vowel (f*ck, sh*t, f*ggot, p*do, g*y), from the user's own list `CC/data/caption-masks.json` plus the agent's `captions.mask_terms`; the audio is never edited. → `CC/reference/safety.md` §3
   **The caption look** (the user, 2026-11-13, after comparing our frame with Loupe video 04's: "always use the same font family as they used in that video"): COPIED from that video: Luckiest Guy ALWAYS (never a font picked per video: the box numbers are tuned for it, and another font made the box too big and off its word), upper case,
   white words with a thick black outline and a shadow, the spoken word on a rounded colour box that moves word to word; only the box colour is matched to each video's appearance by the production agent (or the user's `captions_color`);
   the size is small to normal because most viewers are on a phone or a tablet (`size: "auto"`: the font's em at 4.6 percent of the picture's smaller side, never large). → `CC/reference/edit-craft.md`; a match: `CC/reference/game-edit-craft.md`
7. **Safety** (the user, 2026-11-12): religion and superstition are **avoided** (a moment about them is not picked; an incidental one is cut around). Distressing, gory and indecent content (gore, real distress, nudity) is **kept, never avoided, and blurred only in the section (and the part of the frame) where it is seen**; the rest of the clip is never blurred. **Nothing else is ever blurred** (the user, 2026-11-14: "the only reason we blur is when there's gore, distressful content and similar, as for other types no need to blur at all"): personal data, viewer DMs, usernames, IDs, lobby tags, face cams and names stay as they are on screen. → `CC/reference/safety.md`
8. **The run's media is read-only**: chunks, sheets and transcripts are never moved, renamed, deleted or rewritten by this command. A chunk is used in place in CapCut (never copied into a draft: C: has little free space).
9. **CapCut** (9.7, Free, no Pro): closed for every save; only the measured transitions; **ONE build command per video, through the CapCut composition, for every video of both modes** (the user, 2026-11-13: "use capcut composition for everything if possible for faster delivery"):
   `cc.py capcut-build` composes the whole project in a single `capcut compile` (the clips on their real chunk files, the sound-effect lanes, the transitions and, in the word-box look, every caption text with its style), writes what compile has no operation for (zoom keys, background blur, the caption font and entrance, the repair, the clean-up)
   and reads the project back (clips, length, joins, texts, media on disk, `capcut lint`) into one answer with a `problems` list; a 4-minute video with 1,900 caption texts takes about 8 s (the same build as separate compose, finish and check commands took 25 s and four agent turns). `capcut-compose` and `capcut-finish` remain for re-running one part;
   never `capcut lint --fix`, never `--force-write`, never save with force, never a project built clip by clip. The per-tool MCP route is a fallback only. → `CC/reference/capcut-build.md`
10. **One dialog at the start, none mid-run.** `cc-start` asks which mode this is, whether the videos get captions and, in streamer mode, whether to make long videos only or long videos plus shorts (each skipped when `mode=`, `captions=` or `only=` was given); after that the agents decide, and blockers (CapCut running, a missing run, a failed chunk) are reported, not asked. The user reads `RUN/deliverables/README.md` at the end.
11. **Honest reporting.** Never claim a check, a project or a render that did not happen; report failures with the real error. Every file named to the user is a full path from the drive letter.
12. **Chunks arrive in rec time**: all times in plans, EDLs and reports are rec time (seconds since the start of C0001, every recorded chunk counts, an ad-marked one too); map to chunks with `T locate`, never `index * 180`.
    **Nothing is skipped, ad or not ad; the agents leave the ad batches out** (the user, 2026-11-14: "just do not skip anything, whether ad or not ad, and the agents then exclude batches of ads when they analyse"): the recorder saves the segments Twitch marks as ads as chunks of their own (`kind: "ad"` in the chunk's `chunk.json`; `(ad-marked)` in `stream.md`; `T blocks` lists them as `ad_chunks` and `ad_batches`), the processor makes their sheets, transcript and report like any chunk, and the marker is a fact, never a verdict:
    the mining agents look at each marked batch and record a verdict (`ad`, `stream`, `mixed`), leave the ones that are ads out of their analysis, and the planner puts them into `avoid.json` (kind `ad`) so no video cuts from them. → `CC/reference/moment-mining.md`, `CC/reference/portfolio.md`
13. **One mode per run, picked by the user at the start** (`cc-start` asks; `mode=` in the arguments skips the question; a resumed run keeps its mode and its captions setting). A phase of one mode reads only its own mode's skills and references (the shared ones: safety, edit-craft, clip-economy, capcut-build). A streamer co-streaming a match is a streamer run with the game as the topic: the user decides which mode to pick.
14. **Speed without losing anything** (the user, 2026-11-13: "deliver as fast as possible, yet without ruining or letting anything aside, the same results but faster"): whatever does not depend on another step starts together, in ONE message. `cc-start` starts the research agent, the missing chunk reports and `sfx-scan` together;
    `cc-profile-game` starts the screen scan (scores and clock) and the replay-badge and kill-feed series in the background the moment `regions.json` exists; every mining wave and every production wave is spawned in ONE message; the blocks are sized so that a short recording still gets two agents side by side (`T blocks --min-blocks`);
    inside an agent the independent tool calls (frames, contact sheets, Read calls) go in ONE message; the CapCut project is ONE composition and one command (rule 9); the files a command reads once (the clips' probes, the caption font) are read side by side or kept (`font-cache.json`). No check is dropped to save time (frames at the cuts, `units-check`, `edl-check`, the read-back): the speed comes from running things at once, not from looking less. → `cc-start`, `cc-profile-game`, `cc-scan`, `cc-scan-game`, `cc-produce`

## Never (global)
- Never use or create a Workflow. Never more than 4 production agents at once. Never two agents on one video.
- Never more than ONE research agent, never a research wave. Never give a `model` to any agent (the user's `/model` rules). Never guess or change the mode or the captions setting. Never let a report (or the reporter) decide a keep level, a moment, a name or a video.
- Never delete or overwrite a chunk, a sheet, a transcript or a CapCut project. Never push or commit anything.
- Never include religion or superstition; never skip a gory or distressing moment because it is one; never blur more than where it is seen, and never blur personal data, DMs, names, IDs or face cams (only gore, distress, nudity); never build a video without captions when the setting is on, and never add captions when it is off.
- Never invent a fact about the streamer, the topic or a person.
