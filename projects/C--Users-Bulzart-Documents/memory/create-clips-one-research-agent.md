---
name: create-clips-one-research-agent
description: "user 2026-11-13: /create-clips must spawn ONE brief research agent in both modes (no 4-agent wave, no deep research) and run anything bulk/parallel, same results but faster; re-edit due after the BLAST run's clips are complete (status inside)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-13T14:25:12.570Z
---

User 2026-11-13 (twice, same words): "when we complete the clips, make sure to re-edit the /create-clips pipeline so that it only spawns only one research agent for all the work, no need to collect 100 sources ... one agent suffices to collect everything briefly, not a deep research", "same for streamer mode, and also anything that can be processed and produced in bulk ... in order to save as much time as possible ... we need to deliver as fast as possible, yet without ruining or letting anything aside, we want to achieve the same results as we do right now but faster."

**Why:** the BLAST run's 4-agent research wave (15:05 to 15:20 on 2026-11-13) took 14 minutes and about 930k agent tokens (435 tool calls, 93 to 133 per agent) for four notes of 9 to 11 KB; the agents chased single claims (a cousin tie, mirror sites) that no clip decision needed. The brief that came out of it was about 6.5 KB.

**How to apply:** the re-edit starts only after the BLAST clips are complete (the user's wording), and not while mining/production agents of the current run still read the skills. Target shape: ONE general-purpose web-only research agent started at the end of cc-start (from stream-meta title/category/channel/notes), a hard budget (about 10 to 15 tool calls, one note research.md with four short sections, "not found" is fine, three-line reply), overlapping recon, HUD map and hud-scan; the main session sends it a one-line follow-up if the recon finds something it did not cover. Everything else that can run at once does: background gather scripts as soon as their inputs exist, independent tool calls in one message, mining blocks sized for at least 2 agents (a 10-minute recording was split 3+2 chunks), production batched. Keep every quality gate (frame checks, tags, units-check) so the results stay the same. Files: commands/create-clips.md rule 2, cc-profile, cc-profile-game, research playbooks, config agents.research_max, README, tests/test_docs.py. Report it in the CLAUDE.md change format. Status: PENDING (written 2026-11-13 15:27).

Related: [[create-clips-pipeline]], [[scripts-gather-agents-decide]], [[awl-never-ask-decide-autonomously]]
