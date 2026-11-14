---
name: create-clips-shorts-level
description: "user 2026-11-14, streamer mode: when shorts are made a follow-up question asks Concentrated (the one, two or three best shorts) or Normal (about 5 to 10); stored as state.shorts_level; a range, never a quota"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T05:07:51.025Z
---

User 2026-11-14: "also add another feature to the pipeline, if the user picks long content + shorts on streamer mode, they should be prompted to pick one of the two levels for shorts too: Concentrated (i.e do only one,two or three shorts based on the most highlighted and potential pieces of the content) or Normal (5-10 shorts)".

**Why:** the user wants to control how many shorts a run makes (a few top highlights, or a normal batch) instead of the planner's free count.

**How to apply:**
- `cc-start` asks a SECOND, follow-up AskUserQuestion (header `Shorts`, options Concentrated / Normal, no default, no "Recommended" mark) right after the first dialog, only when shorts will be made (`only` is `both` or `shorts`) and `shorts=concentrated|normal` was not given. It cannot be in the first call because it depends on the Videos answer. Stored as `state.json -> shorts_level`; a run made before it has none and the planner judges the count as before. Non-interactive runs must pass `shorts=` (stop and say so otherwise). Game mode has no shorts: not asked.
- `cc-plan` and `reference/portfolio.md` section 3 read it: concentrated = only the 1 to 3 best, the most highlighted pieces with the most potential, each with the most care (never more than 3); normal = about 5 to 10, spread over the night (never more than 10).
- It is a RANGE the user chose, NEVER A QUOTA: fewer when fewer are worth making, none when none is, nothing added to reach the number (the same principle as for long videos: [[create-clips-long-videos-whole-watches]]). The planner's chat line and the wrap-up say why when the count is below the range.
- No script changed. Open: there is no "as many as are good" level any more (a hot night is capped at 10 under Normal) unless the user asks for a third one.
- Where: skills cc-start, cc-plan, cc-wrapup, portfolio.md section 3, router (argument-hint, rules 5 and 10), README; checks in `tests/test_docs.py`.

Related: [[create-clips-pipeline]], [[create-clips-shorts-edit-freedom]], [[create-clips-ads-recorded-agents-judge]] (the Videos question).
