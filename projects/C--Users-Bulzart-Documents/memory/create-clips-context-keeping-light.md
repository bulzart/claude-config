---
name: create-clips-context-keeping-light
description: "Streamer long videos may keep a bit of a dull part when something kept leans on it; guidance only, no limits, judged from data; heavy keep-level machinery was tried and rejected (user 2026-11-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T02:33:02.919Z
---

User, 2026-11-14, asking to port game mode's "an empty-looking unit can still carry context" idea to streamer mode: "we might include that round or just some part of it, if the agents working on it find it useful but without pushing too much ... (but not imply my sample, I am just telling you to give context of what we're trying to achieve) ... carefully and with a sound and reflective mind", then: "no don't push few seconds, just give instructions but dont push limits, just let our system be judgmental on its own and based on data".

**Why:** the first attempt (a `cc_stretch.py` module, a card for every second of every block, a keep verdict per stretch, checks that flagged dependencies and runs of flashes, a table for the user) was too heavy and pushed agents; it was fully removed (repo restored, files deleted). The user's own example (a CS2 round) is only context for the goal, never text to copy into the docs, and nothing in the docs may carry a run's names either.

**How to apply:** the whole feature is `reference/context-keeping.md` plus one-line pointers (moment-mining.md, portfolio.md, cc-scan/cc-plan/cc-build-long, router rule 5, README): guidance for the agents' own judgement from the words and frames, NO numbers (no seconds, counts, quotas, caps), no new schema field (a moment's `needs_context` says where the stream gives the context, `notes` for the rest), no new script. Guards that stay: only what is on tape (no text card, no narration), never across a recording hole, ad batch or avoid span, never changing meaning, context goes with what needs it. `tests/test_docs.py` checks the doc sets no seconds or counts. Shorts unchanged. Related: [[scripts-gather-agents-decide]], [[create-clips-one-research-agent]], [[create-clips-pipeline]].
