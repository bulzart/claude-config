---
name: cc-produce
description: /create-clips phase 5: spawn one production agent per planned video (shorts and long-form at the same time, up to four at once), collect their reports. Internal to that command.
user-invocable: false
---

# cc-produce: build the videos

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `RUN/20-analysis/portfolio.md` (the videos and the building order). Nothing else: the agents read their own briefs.

## Steps
1. **CapCut**: `Get-Process CapCut -ErrorAction SilentlyContinue`. Running is a blocker notice, not a question: the agents still write their edit plans, but cannot save a project. Tell the user once, in a line, to close CapCut; the videos stay `ready-to-build` and a later `/create-clips <run> resume` builds them.
2. **Waves**: spawn production agents (general-purpose, no `model` argument: they use the model the user picked; one per video, the best videos first, at most `config.json -> agents.produce_max` = 4 at once; shorts and long-form share the slots; as one finishes, the next starts).
   Never two agents on one video. Spawn each wave in one message so they run together.
3. **The contract** each agent gets (write it in full; the agent never sees this skill or the command file):
   - the run path, the video id and kind, its brief `RUN/40-briefs/<id>-brief.md`, its output folder `RUN/60-outputs/<id>/`;
   - invoke the build skill of the run's mode (`T state --run RUN get mode`): streamer mode `cc-build-short` (kind short) or `cc-build-long` (kind long); game mode `cc-build-game` (long only: game mode has no shorts) and follow it (if the Skill tool or the name is not available, Read `C:/Users/Bulzart/.claude/skills/<name>/SKILL.md`);
   - read `RUN/20-analysis/brief.md` first; the rest only as its skill says;
   - the rules in one place: only cuts, captions, VFX (zoom, a short transition, a blur where safety says) and, in streamer mode, matching sound effects (game mode: no sound effects at all, and sponsor stretches cut out); religion and superstition avoided, gore, distress, nudity and personal data kept and blurred only where seen (`CC/reference/safety.md`, which it reads);
     **captions follow the run's setting, which the contract states in one line: "captions: ON" (every second of speech, the default) or "captions: OFF" (the user picked no captions: no `T captions`, no caption track, no lexicon work; a spoken slur is audible, so the brief's marked spans are cut around)**;
     the chunks are read-only; **the CapCut project is built with ONE command through the CapCut composition, `T capcut-build` (never clip by clip, never the MCP tools unless the build failed with a plain error that a re-run does not fix; its `problems` list must be empty or reported)**; CapCut closed for every save (if it is open: finish the plan, set `videos.<id>.status=ready-to-build`, stop); never ask the user anything, never spawn agents; every file it names in a report is a full path from the drive letter;
     with captions ON the caption font and the box colour are picked per video to match its appearance (the user's `captions_font` / `captions_color` from `state.json` fill what the EDL leaves open) and the size stays `auto` (small to normal, for phones and tablets);
     no emoji in any text; never claim a check that did not run;
   - speed: it reads its reference files in ONE message, batches independent tool calls (all the contact sheets and frames it needs from ONE PowerShell call, the images read together) and keeps every check (a frame at every cut, `edl-check`, the read-back): batching saves time, skipping a check saves nothing that stays saved;
   - it returns at most 8 lines: the id, the status (`built`, `ready-to-build` or `failed`), the CapCut project name and path, the length, the blurred spans, the exclamations or touchy items left, blockers. It writes `report.md` and `posting.md` in its output folder; the harness may refuse a subagent's write of `report.md`: then it returns the full report text after a line `===== REPORT.MD =====` and this session saves it.
4. **Collect**: when an agent returns, check `RUN/60-outputs/<id>/report.md` exists (save the returned report text as that file when the agent could not) and `T state --run RUN get videos.<id>` says what it returned. A `failed` video gets one retry with the failure named; a second failure stays `failed` and goes into the wrap-up.
5. When every video is `built`, `ready-to-build` or `failed`: `T state --run RUN set stage=produced next_skill=cc-wrapup`.

## Never
- Never more than four agents at once, never two on one project, never a production agent that edits another video's folder.
- Never build a video yourself in this session while agents run (the CapCut project index is shared).

## Hand-off
Invoke Skill `cc-wrapup`.
