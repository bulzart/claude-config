---
name: create-clips-context-keeping-light
description: "Streamer long videos may keep a bit of a dull part when something kept leans on it; guidance only, no limits, judged from data; miners, planner (cross-block search) and builder; heavy keep-level machinery rejected (user 2026-11-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T02:46:09.339Z
---

User, 2026-11-14, asking to port game mode's "an empty-looking unit can still carry context" idea to streamer mode: "we might include that round or just some part of it, if the agents working on it find it useful but without pushing too much ... (but not imply my sample, I am just telling you to give context of what we're trying to achieve) ... carefully and with a sound and reflective mind", then: "no don't push few seconds, just give instructions but dont push limits, just let our system be judgmental on its own and based on data", then: "no need to spawn a pointer agent though, the data is read -> planned -> delivery, no drama", then (after the cross-block limit was explained): "maybe i was wrong ... add anything that make it work or maybe return the pointer too, but if we find such errors we evaluate and fix them and not just report".

**Why:** the first attempt (a `cc_stretch.py` module, a card for every second of every block, a keep verdict per stretch, many checks, a table for the user) was too heavy and pushed agents; it was fully removed (repo restored, files deleted). The user's own example (a CS2 round) is only context for the goal, never doc text; nothing in the docs may carry a run's names either. "Pointer" was never an agent: it is one line in the miners' instructions.

**How to apply:** the whole feature is `reference/context-keeping.md` plus one-line pointers (moment-mining.md, portfolio.md, cc-scan, cc-plan, cc-build-long, cc-wrapup list, router rule 5, README): guidance for judgement from the words and frames, NO numbers (no seconds, counts, quotas, caps), no new schema field, no new script, no new agent. Flow stays read -> plan -> deliver. Miners (they read every line of their block) say in the existing `needs_context` what a viewer must be told and where the stream tells it if they saw it; if it lies outside their block they say only what. The planner is the one place that sees every block: leads = `needs_context`, block `people` (`first_rec`) and `summary` lines, block-edge moments; it finds the place with a plain text search of all transcripts (also Whisper's variant spellings from lexicon.json), ignoring ad and avoid hits, then checks words and a frame (tried on the ishowspeed run: it finds the block-1 telling for a block-2 moment). Builder keeps context spans to what the context needs; the wrap-up README lists every context span kept. Guards: only what is on tape (no text card), never across a recording hole, ad batch or avoid span, never changing meaning, context goes with what needs it and comes before it. `tests/test_docs.py` checks the doc sets no seconds or counts. Shorts unchanged. Related: [[scripts-gather-agents-decide]], [[create-clips-one-research-agent]], [[create-clips-pipeline]].

Index line before the 2026-11-14 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: long videos MAY keep a bit of a dull part when something kept leans on it; guidance only, no limits, judged from data; planner finds it across blocks by text search; no new agent or tool

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14: long videos MAY keep a bit of a dull part something kept leans on; no limits, judged from data
