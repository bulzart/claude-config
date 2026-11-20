---
name: create-clips-long-videos-whole-watches
description: "user 2026-11-14, STREAMER MODE ONLY: a long video is one whole watch of about 25 min to an hour set by the content (36+43+27 min from a 7 h stream, not 60+46); borders between acts, never a story left half; how much of the stream becomes content (3 h, 32 min or none) is the agents' judgement, never a target"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T04:45:07.030Z
---

User 2026-11-14 (a pasted brief, then "i am talking only about streamer mode"): "make the long content to be in the 25 min - 1 hour ballpark per video based on the content and context, and not one hour, such as for example there could be 3x 36min, 43, 27min videos collected from a 7 hour stream based on whats being spoken and other details and data of the stream, and not try to push for example 1hour video and then 46 minutes the other with if we could've split the stream into more easily watchable entities rather than letting the video not finish and then the user should go and watch 7 first minutes of the other 46 minutes in order to complete what they were watching but were left in half."

**Why:** the old rule ("about an hour as a guide, 8 hour-long videos on a hot night") let the planner fill one video to the hour and spill the rest into the next, which cut a story between two videos: the viewer had to open the next video to see how it ended.

**How to apply:** streamer mode only (the 25-minute-to-an-hour range and the acts do not apply to game mode, which keeps its own lengths in `game-clipping.md` "about an hour is only a ceiling"; its counterpart is [[create-clips-game-one-project-per-match]]; `clip-economy.md`'s long-form section is tagged streamer mode and points game mode to `game-clipping.md`).
- A long video is ONE WHOLE WATCH: ballpark about 25 minutes to an hour when the content is there, set by content and context, never by the clock; shorter or longer is right when the content is whole at that length; the number of videos is what the content earns, not hours divided by one.
- HOW MUCH OF THE STREAM BECOMES CONTENT IS THE AGENTS' JUDGEMENT, NEVER A TARGET (the user's follow-up, same day: "agents should not strictly push or insist on including unnecessary content if they believe it not worth it ... just in order to achieve a certain number of minutes, even if a video is 8 hour the agent decides how much of that should be turned into content ... 3 hours of content ... but it can also only product 32minutes of total content too, the agents should be the ones to freely evaluate, judge and decide on many factors").
  No minimum in total or per video; the 25 to 60 range only says how a night that has plenty is split; nothing is included to fill a video or to reach a length; a streamer doing nothing worth including is left out however long it lasts; the builder may come out far below the plan and sets `failed` with the reason when nothing is worth a video. Reasoning over rules: the docs list factors to weigh, no formula.
- The mining agents add `acts` to their block file (stretches that are one watchable thing from start to end, dull stretches and breaks included, `starts`/`ends`, `open_start`/`open_end` at a block's edge). It is the ONE new schema field: no script, no agent. The planner merges them into `acts.json` (an act open across a block edge is joined), sets the borders between videos BETWEEN acts, groups acts to about 25 to 60 minutes of kept material, regroups when the sums fall badly (60 + 46 where the 46 starts mid-story), and checks every border by reading the words about 2 minutes either side plus a frame. A stretch is in one long video only. An act over an hour stays one video, or is divided only where a part is finished (the next part's setup may be a context span: [[create-clips-context-keeping-light]]).
- The brief says how the video opens and ends and names the neighbouring videos; the builder checks its opening and ending, cuts back to the nearest whole scene when a border is not clean and reports it; the wrap-up README lists how each long video opens and ends and every unclean border.
- Where it lives: `reference/portfolio.md` section 2, `moment-mining.md`, `clip-economy.md`, cc-plan, cc-scan, cc-build-long, cc-start (Videos question text), cc-produce, cc-wrapup, README, router rule 5; checks in `tests/test_docs.py`.

Related: [[create-clips-pipeline]], [[scripts-gather-agents-decide]], [[create-clips-ads-recorded-agents-judge]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14, STREAMER MODE ONLY: ~25 min to 1 h per video set by content (36+43+27 from 7 h, not 60+46); borders between acts (miners' `acts`), every border checked in the words, no story left half; how much becomes content (3 h, 32 min or none) is the agents' call, never a target

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-14, streamer mode: ~25 min-1 h per video set by content, borders between acts, no story left half; total = agents' call, never a target
