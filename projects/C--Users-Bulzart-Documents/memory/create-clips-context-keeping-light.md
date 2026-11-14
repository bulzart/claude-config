---
name: create-clips-context-keeping-light
description: "Streamer long videos may keep a bit of a dull part when something kept leans on it; guidance only, no limits, judged from data, planner and builder only; heavy keep-level machinery and any mining-agent change were rejected (user 2026-11-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T02:41:06.441Z
---

User, 2026-11-14, asking to port game mode's "an empty-looking unit can still carry context" idea to streamer mode: "we might include that round or just some part of it, if the agents working on it find it useful but without pushing too much ... (but not imply my sample, I am just telling you to give context of what we're trying to achieve) ... carefully and with a sound and reflective mind", then: "no don't push few seconds, just give instructions but dont push limits, just let our system be judgmental on its own and based on data", then, about a pointer for the mining agents: "no need to spawn a pointer agent though, the data is read -> planned -> delivery, no drama".

**Why:** the first attempt (a `cc_stretch.py` module, a card for every second of every block, a keep verdict per stretch, checks that flagged dependencies and runs of flashes, a table for the user) was too heavy and pushed agents; it was fully removed (repo restored, files deleted). The user's own example (a CS2 round) is only context for the goal, never text to copy into the docs, and nothing in the docs may carry a run's names either. The mining agents were also left exactly as they were: the flow stays read (miners) -> plan (planner) -> deliver (builders), and the idea lives only in the last two.

**How to apply:** the whole feature is `reference/context-keeping.md` plus one-line pointers in portfolio.md, cc-plan, cc-build-long, router rule 5 and the README: guidance for the planner's and the builder's own judgement from the words and frames, NO numbers (no seconds, counts, quotas, caps), no new schema field, no new script, nothing new asked of the mining agents (moment-mining.md and cc-scan are untouched). The planner's leads are the existing `needs_context`, the block notes and the words around the spans it keeps. Guards that stay: only what is on tape (no text card, no narration), never across a recording hole, ad batch or avoid span, never changing meaning, context goes with what needs it. `tests/test_docs.py` checks the doc sets no seconds or counts. Shorts unchanged. Related: [[scripts-gather-agents-decide]], [[create-clips-one-research-agent]], [[create-clips-pipeline]].
