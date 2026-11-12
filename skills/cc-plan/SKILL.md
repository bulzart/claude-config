---
name: cc-plan
description: /create-clips phase 4: merge the scan, read how rich the night was, decide which short and long-form videos get made, write one brief per video. Internal to that command.
user-invocable: false
---

# cc-plan: the portfolio

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/portfolio.md` (merge, long-form richness, shorts selection, the briefs). Read it whole.
- `CC/reference/clip-economy.md` (what travels, the shape of a short and of a long video). Read it whole.
- `RUN/20-analysis/brief.md` and `clip-criteria.md`, and every `RUN/20-analysis/blocks/block-NN.json`.

## Steps
1. **Merge** (portfolio.md §1): write `stream-summary.md`, `moments.json`, `richness.json`, `lexicon.json` (merged with the profile's), `sensitive.json`, `avoid.json`. Where a block is missing or thin, read its transcripts yourself (`T window`).
1b. **The second look** (you, the model the user picked, not the scan model): the scan agents were the fast pass and their `standalone` and `shareability` scores are their own reading. Before a moment becomes a short or a span of a long video,
   read its words yourself (`T window --run RUN --from T --to T`) and look at a dense sheet or a frame of its payoff (`RUN/10-media/Cnnnn/sheets/`, `T frame`): fix the bounds, the hook and the scores where the card is wrong and drop what does not hold.
   The best three shorts, the first and last span of every long video, and every moment with `confidence` low or medium always get it.
2. **Decide the long-form videos** (portfolio.md §2): runs and pickups from the richness line, how many videos the night earns, each one's shape and length (about an hour as a guide, never cut a story in half, past an hour when needed, fewer and shorter when the night was warm). Honour `only=shorts` (none) from the user's start notes.
3. **Decide the shorts** (portfolio.md §3): which moments, how many (as many as are good, up to 3 minutes each, the length follows the moment), what the hook is, what is cut together and what is cut twice. Honour `only=long` (none).
4. **Write the briefs** (portfolio.md §4): `RUN/40-briefs/<id>-brief.md` for every video (`S01`, `S02`, ... and `L01`, `L02`, ...), and `RUN/20-analysis/portfolio.md` (the table, the counts, the building order: best first). Each brief carries its spans, the touchy spans with what to blur, the avoid spans, the lexicon, the people and a title and hashtags idea.
   Every span in a brief is re-checked against `avoid.json` (religion and superstition never in; an incidental one is edited around or the moment is dropped) and `sensitive.json` (kept, blurred where seen).
5. Record the videos with dotted keys (no JSON quoting): `T state --run RUN set videos.S01.kind=short "videos.S01.title=working title" videos.S01.status=planned` for each, and `stage=planned next_skill=cc-produce`.
   (`T state` values are read as JSON when they parse, as a file when written `key=@file.json`, else as text.)
6. Give the user nothing to answer: the plan is theirs to read later in `portfolio.md`. One line in the chat says how many shorts and long videos are planned.

## Never
- Never plan a video to a quota or to hit an hour. Never plan padding. Never plan a moment that is about religion or superstition.
- Never write the cut list: the production agent decides exact cuts, zooms, sounds and captions from the brief.

## Hand-off
Invoke Skill `cc-produce`.
