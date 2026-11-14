# The portfolio: which videos get made (planner's guide)

You have the block files (`20-analysis/blocks/block-NN.json`), the brief and the criteria. You decide what gets built, then write one brief per video.
Two kinds are made at the same time: shorts and long-form. The agents decide how many of each; nothing here is a quota.

## 1. Merge what the scan found
- `RUN/20-analysis/stream-summary.md`: the stream in time order, from the block summaries (what the stream was, the acts it fell into, the guests and when they came and left,
  the turns, the technical trouble). A reader should get the night in two minutes.
- `RUN/20-analysis/moments.json`: all moments, ids kept, duplicates and overlaps merged (when two block agents saw one moment from two sides, keep the widest honest bounds and the better title).
- `RUN/20-analysis/richness.json`: one score per chunk (the scan's), smoothed by you where a block agent was harsher or kinder than its neighbours, with the reason.
- `RUN/20-analysis/lexicon.json`: the merged Whisper-spelling fixes, `[["Whisper wrote","right"], ...]`, which every EDL's `captions.replace` takes.
- `RUN/20-analysis/sensitive.json` and `avoid.json`: every span to blur (gore, distress, nudity only) and every span to stay away from, merged, as the builders will need them.
- **The ad batches** (the user, 2026-11-14: the recorder skips nothing, and the agents leave the ad batches out when they analyse): the mining agents' `ad_batches` (each with a verdict `ad|stream|mixed`) merged by rec time into `RUN/20-analysis/ad-batches.json`
  (`T blocks` also lists the recorder's marker as `ad_batches`; compare: a marked batch no agent judged is yours to judge now, from its report and a sheet). Every span with verdict `ad` goes into `avoid.json` as `{"rec_from", "rec_to", "kind": "ad", "what": "..."}`, so
  every brief carries it as a span to stay away from. A `stream` verdict is not left out; a `mixed` one is left out only for the seconds that are the ad.

## 2. Long-form: how rich was the night?
Read the richness line across the whole stream (a score per chunk), not just the peaks.
- Find **runs**: stretches of chunks that are good to watch as a whole (the stream on fire, a long guest segment, a challenge from start to end). Runs can be short or 20 chunks long.
- Find **pickups**: good moments between the runs (2 minutes from one chunk, 30 s from another) that belong in the best hour but do not make a run.
- Decide **how many videos**: if the content is consistently hot for this creator's audience (they would watch it all), there can be many (8 videos of about an hour is possible for a streamer like that on a big night);
  if it is warm, make fewer and shorter videos that are all good; if only a few pockets are good, one video or none. A video is made when its content earns the length. Padding is a failure.
- Decide **each video's shape**: chronological is the default (the night as it went); a theme video ("every guest moment") or a best-of order is fine when it is the better watch. A cold open of the best 20 to 40 s may start it.
  Length is about an hour as a guide; a segment is never cut in half to hit it, so a video may run past an hour to end a scene, or stop short when the next stretch is weak.
  Where the recording has a gap (a chunk with `gap_before_s` or `ads_skipped_s` in the table), the join is part of the plan. An ad batch (verdict `ad`) is never part of a run, a span or a pickup: the stream on either side of it is a cut, not a continuation.
- **Dull parts and the context a bit of one may carry** (`CC/reference/context-keeping.md`): the parts with nothing to show are left out, as before. Where something that is kept leans on a bit of one, the planner may keep that bit as a **context span**; a moment's `needs_context`, the people and summary lines of the block files and the agents' `notes` are leads; where the stream says it, even in another block, is found with a plain text search of the transcripts (the file says how); it is checked in the words and a frame, and the data decides.
- List for each: `L01`, working title, the ordered source spans (`rec_from`, `rec_to`, a line on why each is in), the target length, the chapter list, the sensitive and avoid spans inside, the guests it features.

## 3. Shorts: which moments, how many
- Start from the moments with the highest shareability and standalone scores that fit this streamer's criteria, then read them again as a clip editor: does the first 2 seconds hook? is the payoff clean?
- One moment can make one short; two or three small beats about one thing can make one short together (a "3 times chat was right" cut); a strong moment can also be cut twice with different hooks when both are good.
- Do not make five shorts that are the same joke. Do not make a short of a moment that needs 40 s of setup to deserve 15 s of payoff.
- Spread: variety across the night and across the kinds of moment that travel for this streamer; the best 3 get the most care.
- Count: as many as are good. A hot night can give dozens; a quiet one a handful. There is no minimum.
- A moment can be in a short and in a long video; that is normal.
- List for each: `S01`, working title, the source spans, the target length (up to 3 min; the length follows the content), the hook idea (what the first 2 s are), the payoff, what to blur (spans from `sensitive.json`),
  what to stay away from, the SFX or zoom ideas if any (optional), the posting title and hashtags idea.

## 4. Write the briefs (one file per video) and the plan
`RUN/40-briefs/<id>-brief.md` (about a page): the goal in a sentence; who it is for; the sources (spans with rec times and a line each; a context span is marked as one, with what it gives and what needs it); constraints (length, the sensitive spans with what to blur, the avoid spans, the lexicon,
the people and their spelling); what the editor should try (a hook, an order, a cold open, a callback); the title and hashtags for `posting.md`.
`RUN/20-analysis/portfolio.md`: the table of videos (id, kind, working title, length target, spans, why it exists), the count of each kind, and the plan for the order of building (best first). Record the ids in
`state.json -> videos` (`cc.py state --run RUN set videos.S01={...}`).
The planner does not cut. A production agent gets a brief and decides the exact cuts, zooms, sounds and captions itself.

## 5. Agents for the build
One production agent per video, at most 4 at the same time (`config.json -> agents.produce_max`), the best videos first. Each is a different CapCut project, a different folder under `60-outputs`, and shares nothing but the read-only chunks.
