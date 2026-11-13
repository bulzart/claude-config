---
name: cc-plan-game
description: /create-clips game mode, phase 4: merge the mining agents' cards, check what will be used, decide for every round or fight how much to keep (full, trim, flash, skip), decide the condensed-match videos (long-form only, no shorts), write one brief per video. Internal to that command.
user-invocable: false
---

# cc-plan-game: which rounds, how much of each, which videos

> `CC`, `PY`, `T`, `RUN` as in cc-start. You are the planner: the model the user picked. The mining agents wrote the cards; every verdict below is yours.

## Read now
- `CC/reference/game-clipping.md` (whole: impact, the four keep levels, how much of a unit to take, the condensed-match videos) and `CC/reference/clip-economy.md` (the long-form section).
- `CC/reference/portfolio.md` sections 4 and 5 (the briefs and the agents). The rest of that file is for streamers.
- `RUN/20-analysis/brief.md`, `clip-criteria.md`, `match-map.md`, `hud/states.txt` and every `RUN/20-analysis/blocks/block-NN.json`.

## Steps
1. **Merge**: `T units-merge --run RUN` writes `RUN/20-analysis/rounds.json` (every block's units, `non_play` and `extras` in time order, ids kept, a repeated id kept once, the lexicon fixes collected), and `sensitive.json` and `avoid.json` (every span to blur and every span to stay away from).
   `lexicon.json` is yours: the profile's pairs plus `rounds.json -> lexicon_fixes`, conflicts settled by what the broadcast shows. `T units-check --run RUN` then shows the facts: overlapping units, score changes no unit holds, stretches with neither a unit nor a `non_play`, cards with missing fields, the totals.
   Settle every one by reading the words (`T window`), the chunk reports (`RUN/10-media/Cnnnn/report.md`) or the sheets of that stretch; a block marked `scan.failed` is covered here from its reports, transcripts and sheets. When two block agents saw one unit under two ids, keep the card with the honest widest bounds and mark the other `skip` with the reason "the same unit as R12".
   Then write the final `RUN/20-analysis/match-map.md`: every stretch of the broadcast classified (pre-show, each map or game, each half, overtime, breaks, timeouts, pauses, ads, **sponsor stretches**, replays).
2. **Check what will be used** (the cards are the mining agents' reading; the videos are built from your verdicts): look at the frames and read the words yourself for (a) every unit you expect to use at `full` or `trim`, (b) every unit whose `confidence` is not high and whose impact is 6 or more.
   Use the dense sheets of the span (`RUN/10-media/Cnnnn/sheets/`), `T frame`, `T words`, `T window`, `T hud-slice` or `T hud-read` for a clock. Where a card is wrong (the bounds, the kills counted, live or replay, the winner), put the corrected fields in the unit's verdict entry below; write what you saw in `verified`.
3. **The verdict for every unit** (game-clipping.md §5 to §7): `keep` (`full`, `trim`, `flash`, `skip`), `keep_spans` (rec ranges inside the unit's bounds, never over a sponsor stretch), `keep_why` in a line, for all units, the skipped ones with the reason they are noise. The "never skip" list of §6 and the brief's five questions apply.
   Write the decisions in one small file, `RUN/20-analysis/verdicts.json`:
   `{"R14": {"keep": "full", "keep_spans": [[4058.0, 4092.0]], "keep_why": "the 1v3 needs its setup and the defuse", "verified": "frames C0023 s4-s5"}, "R15": {"keep": "skip", "keep_spans": [], "keep_why": "a routine eco round, no stakes"}, ...}`
   and apply it: `T units-verdict --run RUN --file RUN/20-analysis/verdicts.json`. The answer lists the units still without a keep level, unknown ids and refused entries (a bad level, a span that runs backwards): fix and apply again until every unit has its level.
4. **Decide the videos** (game-clipping.md §8): **long-form condensed matches only, never a short** (the user, 2026-11-13): one video per map or game (`L01`, `L02` ...), a brief one for a one-sided map or a quick best-of-one, a map or game that was dull gets a brief video or none.
   `only=shorts` in the user's start notes is refused in one line (game mode has no shorts); `only=long` changes nothing. No quota, no padding. Record which units each video uses: `{"R14": {"used_in": ["L01"]}, ...}` applied with `T units-verdict ... --add-used-in`.
5. **Write the briefs** (`portfolio.md` §4 shape): `RUN/40-briefs/<id>-brief.md` for every video. A game brief carries: the goal and the audience; the units in order, each with its keep level, `keep_spans`, the replay spans to cut (or keep, and why) and a line on why it is in;
   the sponsor and ad stretches inside its range, to cut; the map changes (a `flash` transition each); the touchy spans with what to blur; the avoid spans; the lexicon and the players' spelling; the chapter list; the title idea `<team> vs <team> | Map 2 Mirage | <event>` and hashtags.
   Write `RUN/20-analysis/portfolio.md` (the table: id, kind `long`, working title, length, units, why it exists; the counts; the building order: best first).
   Every span in a brief is re-checked against `avoid.json` (religion and superstition never in; an incidental one is edited around or the unit is dropped) and `sensitive.json` (kept, blurred where seen).
6. Record the videos with dotted keys: `T state --run RUN set videos.L01.kind=long "videos.L01.title=working title" videos.L01.status=planned` for each, then `stage=planned next_skill=cc-produce`.
7. One line in the chat: how many videos are planned, and that `RUN/deliverables/rounds.md` will carry the table of every round with its keep level (the user can overrule a skip there). The plan itself is theirs to read later in `portfolio.md`.

## Never
- Never skip a unit without a reason written next to it; a skipped unit with impact 6 or more is checked first (step 2).
- Never plan a short, a highlight reel, a sound effect or a sponsor stretch. Never plan to a quota or a length. Never plan padding. Never plan a unit that is about religion or superstition.
- Never write the cut list: the production agent decides the exact cuts inside the spans from the brief.

## Hand-off
Invoke Skill `cc-produce`.
