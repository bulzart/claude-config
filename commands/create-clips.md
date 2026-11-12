---
description: Take a processed livestream run folder (3-minute chunks, frame sheets, transcripts), research the streamer, their audience and the topic of the stream, find the moments, and build short-form (Shorts, TikTok, Reels) and long-form videos as CapCut projects with cuts, captions, VFX and sound effects.
argument-hint: "<run folder or session name> [only=shorts|long] [notes=\"guest, topic, what you want\"] [streamer=\"Name\"] | resume [run]"
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

You are running the **/create-clips** command: the clip-farming editor for livestreams. This file is only the **router**; the work is split into **phase skills** (`cc-*`) and **reference files** (`CC/reference/`), so every phase loads only what it needs and a long run does not rot.

`CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder the user names.
The run folder is what `cc.py watch` made from the Twitch Chunk Recorder's chunks: `CC/README.md` is the contract (layout, rec time, files).

## How it loads (obey throughout)
1. **Resume?** If `$ARGUMENTS` starts with `resume` or the run's `state.json` already has a `stage`: `T state --run RUN get`, say in one line where it stopped, and invoke the skill in `next_skill` (a `produced` run with videos `ready-to-build` goes back to `cc-produce`). Never re-ask what `state.json` answers.
2. Otherwise **start by invoking Skill `cc-start`** with `$ARGUMENTS`, then follow each skill's **Hand-off**: it records `T state --run RUN set stage=... next_skill=...` and names the next skill. Invoke it when you reach it, never earlier.
3. **Load only what a phase names.** Each skill has a "Read now" list; read those and nothing else unless a step says so. A phase boundary is a safe cut: everything a later phase needs is in `RUN/state.json` and the run files. When many phases lie behind you, tell the user in one line that `/compact` is safe (or `/create-clips resume <RUN>` in a new session).
   After a compaction re-invoke the skill in `next_skill`: its text may have been summarised away.
4. **Agents never receive this file.** An agent gets a contract that names the skill to invoke (Skill tool; if it is unavailable, Read `C:/Users/Bulzart/.claude/skills/<name>/SKILL.md`) and the reference files that skill lists.

## Phases
| Phase | Skill | Does | Next |
|---|---|---|---|
| 1 intake | `cc-start` | the run, the chunk table, folders, the size of the work | `cc-profile` |
| 2 profile | `cc-profile` | recon of the stream, a research wave (the streamer and their audience, the topic or game or event and what the internet says about it, the people, what works as a clip), the context brief | `cc-scan` |
| 3 scan | `cc-scan` | scan agents read the stream in blocks: summary, moments, richness per chunk, what to blur or avoid | `cc-plan` |
| 4 plan | `cc-plan` | merge, decide the long-form and short-form videos, one brief per video | `cc-produce` |
| 5 produce | `cc-produce` | one production agent per video, up to 4 at once, shorts and long-form together | `cc-wrapup` |
| per video | `cc-build-short` / `cc-build-long` | study, EDL, captions, CapCut project, report | (returns) |
| 6 wrap-up | `cc-wrapup` | verify, deliverables README, what to do next | none |

## Core rules (the full text sits in the skill or reference that owns each)
1. **Normal command, never a workflow.** Everything runs in this conversation with ordinary tools and the Agent tool; the `Workflow` tool is disabled.
2. **Agents**: research agents at most 4 (web only), scan agents at most 6 at once, production agents at most 4 at once, one per video, never overlapping, never asking, never spawning agents. → `cc-profile`, `cc-scan`, `cc-produce`
3. **Scripts gather, agents decide.** `cc.py` measures, extracts, converts and writes what an agent decided; no verdict, rank or gate comes from a script. Every judgement is an agent's, with its reason written where the step records it.
4. **Think like a clip farmer who lives on the internet.** Before deciding anything, the agents are in touch with the streamer and their audience, the topic of the stream (a game, a release, an event, a trend: what everyone is saying, joking about, hyping and clipping about it), the people on it, and what works as a clip right now. The research is social, not scientific
   (the user, 2026-11-12). Every claim is tagged [W] web, [S] this stream, [M] model memory, [I] inference; nothing is invented. → `cc-profile`, `CC/reference/research-playbook.md`
5. **Two kinds of video at once.** Short-form (Shorts, TikTok, Reels): up to 3 minutes each, the length follows the content, as many as are good. Long-form: about an hour as a guide, never cutting a story in half (so it may run past an hour), the number decided by how rich the night was for this creator (8 hour-long videos on a night that is hot all through, fewer and shorter on a warm one, none on a dull one), made of straight runs of chunks and pickups, the agent's call. → `cc-plan`, `CC/reference/portfolio.md`
6. **The edit is only**: cuts, captions, VFX (a zoom, a short transition, a blur where rule 7 says) and sound effects that match the situation. No music, no stickers, no emoji, no text overlay but captions, no filters, no drawings. **Captions are non-negotiable**: every second of speech, in every video. → `CC/reference/edit-craft.md`
7. **Safety** (the user, 2026-11-12): religion and superstition are **avoided** (a moment about them is not picked; an incidental one is cut around). Distressing, gory, nudity and personal data are **kept, never avoided, and blurred only in the section (and the part of the frame) where they are seen**; the rest of the clip is never blurred. → `CC/reference/safety.md`
8. **The run's media is read-only**: chunks, sheets and transcripts are never moved, renamed, deleted or rewritten by this command. A chunk is used in place in CapCut (never copied into a draft: C: has little free space).
9. **CapCut** (9.7, Free, no Pro): closed for every save; only the measured transitions; the MCP builds the main track and the sound effects, `cc.py capcut-finish` does the zoom keys, transitions, captions and the repair; never `capcut lint --fix`, never `--force-write`, never save with force. → `CC/reference/capcut-build.md`
10. **No questions mid-run.** The agents decide; blockers (CapCut running, a missing run, a failed chunk) are reported, not asked. The user reads `RUN/deliverables/README.md` at the end.
11. **Honest reporting.** Never claim a check, a project or a render that did not happen; report failures with the real error. Every file named to the user is a full path from the drive letter.
12. **Chunks arrive in rec time**: all times in plans, EDLs and reports are rec time (seconds since the start of C0001, content only); map to chunks with `T locate`, never `index * 180`.

## Never (global)
- Never use or create a Workflow. Never more than 4 production agents at once. Never two agents on one video.
- Never delete or overwrite a chunk, a sheet, a transcript or a CapCut project. Never push or commit anything.
- Never include religion or superstition; never skip a gory or distressing moment because it is one; never blur more than where it is seen; never build a video without captions.
- Never invent a fact about the streamer, the topic or a person.
