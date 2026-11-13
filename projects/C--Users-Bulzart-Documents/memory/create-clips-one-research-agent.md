---
name: create-clips-one-research-agent
description: "user 2026-11-13: /create-clips spawns ONE brief research agent in both modes (no 4-agent wave), runs anything bulk/parallel, same results faster, and offers captions / no captions picked at the start; DONE 2026-11-13 16:3x except the CapCut compose/finish test with captions off (needs CapCut closed)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-13T15:26:33.908Z
---

User 2026-11-13 (twice, same words): "when we complete the clips, make sure to re-edit the /create-clips pipeline so that it only spawns only one research agent for all the work, no need to collect 100 sources ... one agent suffices to collect everything briefly, not a deep research", "same for streamer mode, and also anything that can be processed and produced in bulk ... in order to save as much time as possible ... we need to deliver as fast as possible, yet without ruining or letting anything aside, we want to achieve the same results as we do right now but faster."
Also: "add the option to pick captions and no captions mode for both streamer and game mode".

**Why:** the BLAST run's 4-agent research wave (15:05 to 15:20 on 2026-11-13) took 14 minutes and about 930k agent tokens (435 tool calls, 93 to 133 per agent) for four notes of 9 to 11 KB; the agents chased single claims (a cousin tie, mirror sites) that no clip decision needed. Same run: mining 19 min (block 1 held four live rounds, 57 tool calls) and the one production agent 23.5 min (104 tool calls); planning 4.5 min.

**What was built (2026-11-13 after the BLAST clips were wrapped):**
- ONE research agent: `cc-start` starts it in the background (`reference/research-agent.md` = contract + budget, `config.json -> agents.research_max` 1, `research_calls` 15), note `20-analysis/research.md`; `cc-profile` / `cc-profile-game` collect it (a "write your note now" nudge by SendMessage after about 6 minutes); never a wave.
- Bulk/parallel: cc-start starts the research agent, missing reports and sfx-scan together; cc-profile-game starts `hud-scan` plus `region-series` replay and feed in the background the moment regions.json exists; `T blocks --min-blocks` (`agents.scan_min_blocks` 2); mining and production contracts say "batch independent tool calls, aim ~8 min / keep every check"; router rule 14.
- Captions option: `captions=on|off` argument or a second question in the SAME AskUserQuestion dialog as the mode; `state.json captions` (default on, also when the key is missing); `cc.py captions` skips and `capcut-finish` adds no caption track/font/entrance when off (`finish.json captions.enabled`); skills, references, wrap-up, README follow it; with captions off a spoken slur is audible, so the plan cuts around it. Tests: test_docs (new checks), test_edit (blocks, captions off, state words false/0/no).
- Lessons written into the skills: live vs replay only from the replay-badge series (the first brief called two live rounds replays); `hud/states.txt` misses banner-hidden round ends (raw `<name>.txt` is truth); "reconcile" step after the scan; captions `y_rel` 0.76 above a CS2 HUD; a subagent's write of `report.md` can be refused by the harness (the main session saves the returned text).

**Not verified yet:** the compose/finish part of `tests/test_edit.py` (captions off at the build, captions on without an srt is refused) SKIPS while CapCut runs (the user opened it 16:24); run `python tests/test_edit.py` once CapCut is closed. A real run with the new start (one dialog, the background research agent) has not happened yet.

Related: [[create-clips-pipeline]], [[scripts-gather-agents-decide]], [[awl-never-ask-decide-autonomously]]
