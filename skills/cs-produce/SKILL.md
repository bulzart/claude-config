---
name: cs-produce
description: /create-static phase: prepare every video (S2 for each), spawn one production agent per video, handle their reports and a long video's split (A9s–A10). Internal to that command.
user-invocable: false
---

# cs-produce — Static: prepare every video, produce in parallel, handle the reports (A9s–A10)

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- production-agents §1: `CS/reference/production-agents/010_1_prepared-by-this-session-before.md` (1.4 KB)
- production-agents §2: `CS/reference/production-agents/020_2_spawning.md` (2.1 KB)
- production-agents §2s: `CS/reference/production-agents/025_2s_spawning-static.md` (14.6 KB) (the contract prompt `T contract` writes)
- production-agents §3: `CS/reference/production-agents/030_3_the-agent-s-contract.md` (7.6 KB)
- production-agents §4: `CS/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.2 KB)
- production-agents §5: `CS/reference/production-agents/050_5_this-session-as-agents-report.md` (2.1 KB)
- static §13: `CS/reference/static/130_13_evaluating-the-work.md` (17.5 KB) (the fresh read before the first generation, and "Between image stretches"; skip when already read)

### A9s. Prepare every video (this session; item 36)
At the start: `T state --run RUN set stage=producing next_skill=cs-produce` (a resume re-enters here; `state.json → videos[]` shows which videos are done), and add the production items to `RUN/todo.md` (item 38): per video S2, S3 (its stretches by image number, naming the
stills to draw and to redraw), the bed, S4 and X10, each with its files by full path; mirror them in the session's tasks when it has task tools, and update both before every long wait (a recording, a
stretch, an agent) and as each agent reports. In order, without asking:
0. **The check and the fresh read of each video's plan, before its first generation** (item 37; static §13): the video's brief
   (`RUN/40-briefs/video-NN-brief.md`) holds your own check of its plan and the one fresh read of it that `cs-plan` makes at A6s step 9. A video whose
   brief does not hold them (a plan made another way, or before the step existed) gets them now, before S2 makes its narration: a new
   agent (`subagent_type: "general-purpose"`, `model: "opus"`) with none of your context reads the finished plan cold, given the narration's
   text, the pictures' plan, the title, the thumbnail and the video's other published words and the standard, never your reasoning and never
   the to-do (item 38); it reports where it would stop watching and what is unclear, flat, repetitive, unearned or untrue, and changes and
   generates nothing; you decide, fix the plan files and write the decision into the brief. In a session without agents you read the plan
   cold yourself, from the artifact alone.
1. **S2 for every video**, one at a time: invoke Skill `cs-sound` (the narration, its words and checks, the image spans; the
   beds after the last narration).
2. **Images by the API or by FLUX 3 Klein** (`static_images=api|klein`): the characters' anchors once (Skill `cs-images`, its
   anchors step). **Images by the user:** Skill `cs-images` for the prompts, then stop for their folder (`static.waiting=images`); when they send it (or on `resume` with
   `static.waiting` set), the intake and the check of every image, then go on.
3. **The agent contract:** `T contract --run RUN [--notes "…"]` writes `RUN/50-requests/agent-contract.md` from production-agents §2s's prompt:
   the toolkit fills the run, the library, the QC fixes (`state.json → qc_fixes`, `auto` when the run has none; item 27), the images'
   source, the CapCut plan and the formats, and lists any placeholder it could not fill: spawn no agent while one remains. It is generated
   for every run and never copied from an earlier run's file; run-specific notes go in its last block.
4. **Spawn** as A9b says: each agent runs S3 `cs-images` (the stills and the YouTube thumbnail; with
   images by the user, only the check of its images), S4 `cs-edit` (the timeline, then `T capcut-build`: the whole CapCut project as one
   composition, item 39) and X10 `cs-record` (the title and the thumbnail into the
   deliverables, static §12). Nothing here asks a question. 5 agents at once.
   More than one format (`state.json → static.extra_formats`, static §2b): the same one agent per video makes every format (the
   contract's Formats line says how); the narration, bed and anchors serve them all.
**More videos** of a run (static §10; `cs-plan`'s More videos): S2, the anchors' check, the contract and the agents for the new
videos only (their numbers from `T static subjects`); the videos already in `state.json → videos[]` are not touched.
**A format added later** (the user asks for the run's videos in one more format: static §2b): `T static format --run RUN --aspect A
--res R --also`, `T contract --run RUN` again, then one agent per video the user names with the spawn message `Video NN, format <tag>`
(its stills, project and record entry only; split as A9b says for a long video); nothing of the first format is touched.

### A9b. Produce in parallel (production agents)

- The contract is production-agents §2s's (`T contract` wrote it at A9s); a QC-fix proposal is about image re-draws, with the cost from
  `cost_usd_estimate`. Each spawn message also names the video's own approach and
  language, read from `state.json → static.video_info` (`T static subjects --run RUN`): the approach's story form, angle, point of view,
  time frame, scale, title form and pillar, and the language's name, ISO code, unit and whether the run's narration model lists it (the
  contract's "One channel" rule refers to them, static §10).
- **A long video** (more than about 40 stills in its plan, e.g. a 12-minute video at 5 s a still holds about 144): its stills are split
  across image agents, each a stretch of about 30–40 in plan order (spawn message `Video NN, images K1-K2: S3 only`; the one with the
  last stretch also makes the thumbnail, `… and the thumbnail`): with the API all at once within the 5 agents at once; with FLUX 3
  Klein one after another, each making its images in the foreground (one GPU; three Klein agents at once ran this PC's commit memory
  short and Claude Code ended their background loops, 2026-11-07: static §5). **Between two stretches, you read what the stretch made** (static §13 "Between image stretches"):
  when a stretch's agent reports, read its report and view the stills it names before the next stretch's agent is spawned; trace what went
  wrong to its prompt words and change the prompts still to come (prevention costs no generation; a re-draw follows the run's QC fixes);
  a fresh reviewer who knows nothing of the work may look at the stretch cold against its lines when a second opinion is worth having; a gap
  between stretches is also where a re-join of the narration and a test suite may run (nothing heavy beside FLUX 3 Klein). When every
  stretch has reported, the bed (`cs-sound` step 5), then one edit agent (`Video NN: S4 and X10`; it reads the plan and the
  brief first) builds the edit and the record from them. The image agents' files are `60-outputs/video-NN/images-K1-K2.json` (their images, attempts, re-draws, costs,
  flags); the edit agent sums them into `result.json`. More than one format (static §2b): each extra format's stretches too
  (`Video NN, format <tag>, images K1-K2: S3 only`; their files `60-outputs/video-NN/<tag>/images-K1-K2.json`), each one after the
  primary's same stretch has reported (it sends the primary's requests); the one edit agent builds every format's project and records them.
- **Spawn one production agent per video** (production-agents §2; `subagent_type: general-purpose`, `model: "opus"` (they run QC and judge: Opus 5.5),
  `run_in_background: true`, description "Produce video NN"):
  - At most 5 run at once, none overlapping; start the next queued video when one finishes.
  - Each agent runs S3 → S4 → X10 for its video (`cs-images`, `cs-edit`, `cs-record`), ending with its CapCut project, and returns one
    JSON line.
  - Each spawn message names the agent's own to-do, `RUN/60-outputs/video-NN/todo.md` (item 38): the agent writes its steps into it when it starts, keeps it current (`[ ]`, `[~]`, `[x]`, `[-]` with
    the reason), and its report says what is done, what is not and what comes next; one file, one writer, so parallel agents never share one.

### A10. Handle every report
- **As each agent reports** (production-agents §5):
  - tick the video's items in `RUN/todo.md` from its report and its own `todo.md`, set `Next:`, and add what the report leaves open (a redraw, a blocker, a flagged image); where the to-do and the
    run's own files disagree, the files are right: look at them before an item is done again, then correct the to-do (item 38);
  - read its `60-outputs/video-NN/result.json`;
  - record it (`T state --run RUN append videos='<json>'`);
  - check the brief: a `qc` that says RESIDUAL FAILURE or regenerated has an attempt block in the
    video's brief with the verdict and what changed, or it is added now from `result.json`;
  - verify, and fix at once what is missing (production-agents §5 item 3): `videos[]` in
    `state.json`; the README table (the agent's `readme-row.md` appended to `deliverables/README.md`, one row per format, static §2b);
    `deliverables/` holding `video-NN-title.txt` and `video-NN-thumbnail.png` and no video file (the CapCut project instead, by its full path, static §7);
    `result.json` complete, each
    check of the agent contract with an evidence path or "not checked: <why>"; the plan and brief files
    with their attempts;
  - print one line: video, status, CapCut project, cost.
- **Blockers come back from agents and are handled here:**
  - `qc_fix_permission` (only with QC fixes `ask`; never with `auto` or `off`) → ask the user the fix question of item 27, then continue that agent with the answer;
  - CapCut was running (`capcut_running`) → its project is pending until the wrap-up (production-agents §5 item 6);
  - credits ran short (the image API's) → launch nothing more, report the shortfall; the run stays resumable;
  - a request failed twice (`failed_twice`) → report it in the wrap-up.
- **QC verdicts are the agent's**; with QC fixes `ask` the fix draws wait for the user's yes (item 27); a video that still fails, or whose fix the user declined, is reported in the wrap-up.
  With QC fixes `off` no agent makes a re-draw: each report's `qc` says off, and the wrap-up's feedback question collects what the user wants fixed.
- **Without the Agent tool**, run S3, S4 and X10 per video in this session, one video at a time (with QC fixes `ask`, ask the fix question of item 27 yourself instead of writing a proposal; with `off`, make no re-draw).
- When every agent has reported and its checks are done, the wrap-up (§6) is `cs-wrapup`: see the hand-off.

## Rules this phase owns (contract items 2, 15, 27)

2. **Agents.**
   - **Analysis agents** are the study phases' (0 by default, 1 for many videos, 2 for a large folder); this phase spawns none.
   - **Production agents:**
     - **one agent per video**, at most 5 at once;
     - after this session has prepared every video (A9s), each agent produces its own video end to end: images → CapCut project → record;
     - the contract and prompt are in `production-agents` §2s;
     - a queued video starts when an agent finishes.
   - Agents never overlap, never ask questions (they report blockers and stop), and never spawn agents.
15. **Static asks for permission nowhere in this phase** but the QC fix (item 27, asked only when the user chose `ask`) and, with images by the user, their folder (item 36).
    - Everything else runs without confirmation: no "Go" question, no cost pauses, no QC questions of its own, and no reference review before an
      upload or a generation (the user, 2026-10-27; an older note asking for one is retired).
    - Blockers are reported, not asked: the account's credits can't cover the next video, CapCut is running.
    - The planning questions (the start's choices, the subject-and-voice pick of A6s) are not permissions and stay.
27. **QC fixes: the question.** With `state.json → qc_fixes = ask`, a production agent that found images only a new draw can fix writes
    `result.json` with `blocker: qc_fix_permission` and a `fix_proposal` and stops (it never asks). When it reports, record it as for any report, then ask with AskUserQuestion
    (header "QC fix"; one question per waiting video, up to four in one call): "Video NN: QC found <the findings in one line>. Fix: <the images to draw again and what their corrected prompts change>,
    about <`cost_usd_estimate`> USD (free with FLUX 3 Klein). Proceed?" with **"Fix it"** (`approved`), **"Keep this take"** (`declined`) and **"Fix it, and stop asking"** (`auto`: also
    `T state --run RUN set qc_fixes=auto`, so no later video asks). Continue the stopped agent with the answer (SendMessage to that agent, its context intact; if it cannot be continued,
    launch a fresh production agent for that video with the contract plus "resume at cs-images with the proposal in result.json, decision <…>"). The other videos keep running meanwhile; the next
    queued video starts when an agent stops. With `auto`, nothing is asked: the agent draws its diagnosed re-draws itself. With `off`, nothing is asked and no
    QC runs: each image is made once and delivered, and the wrap-up's feedback question collects what to fix (item 22).
- **A stalled production agent.** An agent whose `result.json` does not exist and whose `60-outputs/video-NN/` has not changed for 20 minutes while an image call of its video is `submitted`
  or `completed` in the ledger is stalled (a machine pause freezes every background agent at once). Do not relaunch it blindly: read the ledger (`T ledger show --run RUN --video NN`)
  and `T status --run RUN`, then continue the same agent by its id with one line ("continue from the last ledger entry"); only if it cannot be continued launch a fresh agent with the
  contract plus "resume at the ledger's last entry; never send an image request that is submitted or completed". The ledger is what makes a resume safe: a request that already made an
  image is not sent again unless the agent decides on a new draw, and an `unknown` outcome is decided before anything is sent again.

## Never (this phase)

- Never spawn more than 5 production agents at once. Never give agents overlapping work.
- Never close a run with a RESIDUAL FAILURE or a regenerated video that has no attempt block in its
  brief (A10, §6). Never copy an agent contract from an earlier run: it is generated at A9s from
  production-agents §2s.
- Never ask for permission in this phase beyond the QC fix (with `ask`) and, with images by the user, their folder (item 36).
- Never give a fresh reviewer the to-do or your reasoning (items 37, 38).
- Never build a CapCut project here except a pending one, and then only by `T capcut-build` (item 39); never the CapCut MCP tools, `capcut lint --fix` or a save with force.

## Hand-off

When every agent has reported and its checks (A10) are done: `T state --run RUN set stage=produced next_skill=cs-wrapup`, then invoke Skill `cs-wrapup`.

After a compaction, or on `resume`, read `RUN/todo.md` first (item 38), then re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
