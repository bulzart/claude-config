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
   - the rules in one place: only cuts, captions (always), VFX (zoom, a short transition, a blur where safety says) and, in streamer mode, matching sound effects (game mode: no sound effects at all, and sponsor stretches cut out); religion and superstition avoided, gore, distress, nudity and personal data kept and blurred only where seen (`CC/reference/safety.md`, which it reads);
     the chunks are read-only; CapCut closed for every save (if it is open: finish the plan, set `videos.<id>.status=ready-to-build`, stop); never ask the user anything, never spawn agents; every file it names in a report is a full path from the drive letter;
     no emoji in any text; never claim a check that did not run;
   - it returns at most 8 lines: the id, the status (`built`, `ready-to-build` or `failed`), the CapCut project name and path, the length, the blurred spans, the exclamations or touchy items left, blockers.
4. **Collect**: when an agent returns, check `RUN/60-outputs/<id>/report.md` exists and `T state --run RUN get videos.<id>` says what it returned. A `failed` video gets one retry with the failure named; a second failure stays `failed` and goes into the wrap-up.
5. When every video is `built`, `ready-to-build` or `failed`: `T state --run RUN set stage=produced next_skill=cc-wrapup`.

## Never
- Never more than four agents at once, never two on one project, never a production agent that edits another video's folder.
- Never build a video yourself in this session while agents run (the CapCut project index is shared).

## Hand-off
Invoke Skill `cc-wrapup`.
