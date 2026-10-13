---
name: atp-caught-flags
description: "ATP/caught_flags.md — whenever a Higgsfield generation flag occurs in /analyze-then-pick, SAVE it there with `atp.py caught-flag add`; it is write-only: no agent, step or plan reads it (user 2026-10-13, context rot)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 018f5736-eb42-45a5-8337-7d44d473e9a2
  modified: 2026-10-13T17:32:39.324Z
---

The file `~/.claude/analyze-then-pick/caught_flags.md` records every prompt and video Higgsfield flagged, refused, withheld or rerouted during `/analyze-then-pick` (a moderation block, a job failing in seconds with no reason, an `nsfw` / `ip_checking` upload, a withheld output, a `preset_recommendation` notice instead of a job). The user asked for it on 2026-10-12.

**Rule (user, 2026-10-13): the file stays where it is, but nobody reads it.** Never instruct an agent, a plan, a pre-generation check or a run start to read it, to digest it or to copy it into a run (growing files read at every run start rot the agents' context; the same reason the caught-errors ledger was retired, [[atp-caught-errors]]). The name lives here, in memory, so that whenever a generation flag occurs I save it in that file. What a flag teaches goes into the references as a general rule (`generation-system.md` §5c.2, the model guides' failure tables, `higgsfield/higgsfield-mcp.md` §9) through `/update-from-errors`, not through reading entries.

**How to apply:**
- On any generation flag, in a run or in a chat: save it with `T caught-flag add` (never by hand) BEFORE changing the request: verbatim response, kind, tool/stage, jobs and credits, flagged video (reference + clip paths), full prompt, params, media ids, the suspected trigger [E]/[I]. Mark the submission with `T ledger set --flagged`. `cleared` only once a changed request was accepted; else `persistent`.
- Still in the command: the writing (item 23, X7 step 6, production-agents contract item 15) and the main session's `T caught-flag reconcile --run RUN` at each agent's report and the wrap-up (it only lists flagged calls with no entry yet). Removed 2026-10-13: the A1/E1 digest read, `20-analysis/caught-flags.md`, the X4 check against it, the agents' reading-list entry and the "never start a run without reading it" rule; X4 now tests the plan against the references' service-block rules.
- Three entries so far: CF-001 (celebrity face in the video reference, two refunded failures; rule in `generation-system.md` §5c.2), CF-002 and CF-003 (preset notice; rule in the Higgsfield guide §9). Scripts only record; the agent diagnoses ([[scripts-gather-agents-decide]]). Related: [[atp-build-prompt-sync]].
