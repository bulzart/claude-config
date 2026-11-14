---
name: cc-scan-game
description: /create-clips game mode, phase 3: read the score and clock off the screen over the whole match (started in the profile phase), then mining agents read the chunk reports of their block, card every round or fight, mark what is not play (sponsor stretches included), and bring back the extra moments and what needs blurring. Internal to that command.
user-invocable: false
---

# cc-scan-game: card every round

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/game-clipping.md` (the units, the card, impact, keep levels). Read it whole once; every mining agent reads it too.
- `CC/reference/game-mining.md` (the reading order, the block file, the quality bar), and the game's profile the brief names.
- `RUN/20-analysis/brief.md`, `clip-criteria.md` and `hud/regions.json`.

## Steps
1. **The score over the whole match** (the facts the cards are built on). `cc-profile-game` started the scan in the background the moment `regions.json` existed: every number box of `hud/regions.json -> readers` (the two team scores, the clock; Dota 2 and League: the two kill counts and the game clock) is read in ONE pass, because decoding the video is most of the cost,
   and the replay-badge and kill-feed series (`hud/replay-series.txt`, `hud/feed-series.txt`) ran beside it. Check that `hud/score_a.json`, `score_b.json`, `clock.json`, `states.txt` and the two series files exist; run only what is missing, in the background and together:
   `T hud-scan --run RUN --spec RUN/20-analysis/hud/regions.json --step 1` (measure first on one chunk with `--from C0001+0 --to C0001+180` when the match is long: its `seconds` times the number of chunks is the wait, about 12 minutes for a two-hour match),
   then `T hud-states --run RUN --series score_a,score_b --stable 3`.
   Each reader writes `hud/<name>.json` and `<name>.txt` (one line per change of its text); `T hud-slice --run RUN --name clock --from T --to T` prints the readings of one reader inside a range (the agents use it for the clock near a unit).
   `hud/states.txt` lists every change of the score with its time, but a value only counts when it holds for 3 samples, so it MISSES a round end that the ROUND WIN banner hides after one or two readings and it lists OCR slips as changes: the raw `<name>.txt` files hold the first time a value was seen. The agents are told so.
   Look at the answer: `not_plus_one` lists the changes that did not add exactly one (a reset to 0 at a new map is right; a fall or a jump inside a map is a bad read), and `empty_reads` counts the samples where the box read as nothing (a hidden scoreboard during a replay is normal; most of the match is not).
   Where the read is wrong: `T hud-read` at that time, adjust (`--scale`, `--threshold`, `--invert`) and re-scan only that stretch (`--from`/`--to`) under another `--name`, then merge by hand into your reading. `hud=none` in the state: skip this step; the agents work from the reports, the words and the sheets.
2. **A skeleton of the match** (this session, from text only; `cc-profile-game` writes it while the research note is still coming, finish it here): `RUN/20-analysis/match-map.md`, a table of the stretches with rec times: the score resets (a new map or game), the long stretches with no score change (a break, a desk, an ad, a timeout), the words per minute and loudness of those stretches from `stream.md`,
   and what the chunk reports say about them (a desk, an advertisement-looking picture, a menu). Live or replay comes from the replay-badge series, not from a report. It is a skeleton; the mining agents refine it in their `non_play`, the planner writes the final one.
3. **Blocks**: `T blocks --run RUN --chunks N --min-blocks M` with N from `config.json -> agents.scan_chunks_game` (8: about 24 minutes, 12 to 16 rounds; the agents start from the chunk reports) and M from `config.json -> agents.scan_min_blocks` (2: a short recording still gets at least two blocks, so two agents read it side by side; the block size becomes min(N, ceil(chunks / M))). `T state --run RUN set scan.blocks=<n>`.
   When the live play is concentrated in a few chunks (the answer's `words` and the replay series show it), a smaller N gives each agent a lighter block; the number of agents is still at most `agents.scan_max`.
4. **Spawn the mining agents**: general-purpose, **no `model` argument** (they use the model the user picked), one per block, at most `agents.scan_max` (6) at once, the next block as one finishes; never two agents on one block. ALL the blocks of a wave in ONE message. Each agent's contract (it never sees this skill):
   - the run path; its block (the chunk ids, the rec range); its output `RUN/20-analysis/blocks/block-NN.json`;
   - the tools: PowerShell only (Git Bash forks fail on this PC), `T` with the full paths of `PY` and `CC`, and the commands it needs (`grid-frame`, `frame`, `window`, `sheet`, `region-series`, `hud-slice`, `locate`); `region-series` names must start with `b<block>_` so that agents never overwrite each other's files; tool outputs under `RUN/30-assets` and `RUN/20-analysis/hud` are fine, nothing else is written but its block file;
   - read, in this order: `CC/reference/game-clipping.md`, `CC/reference/game-mining.md`, `RUN/20-analysis/brief.md`, `clip-criteria.md`, the game's profile (name the path), `hud/regions.json`, the raw `hud/score_a.txt`, `score_b.txt`, `clock.txt` and the rows of `hud/states.txt` inside its range (with the warning of step 1: states.txt misses banner-hidden round ends and lists slips), `hud/replay-series.txt`, `match-map.md`,
     then the data as game-mining.md says: the chunks' reports first (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, observations only, nothing decided), then the transcripts, and sheets and frames only where a card needs them;
   - **the picture wins**: where the brief, the criteria, the match-map or a report says "replay" or "live", a score or a name and the frames show otherwise, the card says what the frames show and says so in `notes`;
   - **speed**: it batches independent tool calls (several frames, sheets or Read calls in ONE message, all the contact sheets it needs from ONE PowerShell call) and aims for about 8 minutes and about 40 tool calls; a one-image-per-turn agent is the slowest;
   - **the units that end inside its block are its units**; it may read the chunk before the block to see where the first one started; a unit still running at the block's end is the next agent's;
   - a card for every unit (the dull ones with a short reason), evidence as pointers, "not seen" where it did not see, never a count it did not make; `keep_hint` is advice, the planner decides what is kept and which videos exist;
   - sponsorship and the like (sponsor stings and bumpers, "presented by" cards, betting segments, promos, ad breaks, giveaways) goes into `non_play` with kind `sponsor`;
   - it records what must be blurred (`sensitive`: gore, distress, nudity only; never personal data) and what must be avoided (`avoid`: religion, superstition, hate, tragedy, commercial music; `CC/reference/safety.md`, which it reads);
   - it reads media only (never moves, renames or writes into `10-media`), writes only its block file, never asks, never spawns agents, no emoji, every file it names is a full path;
   - it returns three lines: the file, how many units and extras, anything the planner must know.
5. **Check each block file** when its agent returns: `T units-check --run RUN --file RUN/20-analysis/blocks/block-NN.json` (valid JSON; every card has its fields; no overlap; the score changes of the range and the units that end at them; the gaps with no unit and no `non_play`).
   Facts only: you decide what they mean. A bad or thin file (no evidence, an impact with no reason, missing units): one retry with the unit ids and the problem named; a second failure goes into `state.json` (`scan.failed`) and the planner covers that block itself.
   **Reconcile**: where the cards contradict the brief, `clip-criteria.md`, `recon.md` or the match-map skeleton (a live round called a replay, a wrong score, a wrong name), correct those files now, with a line saying so at the top: the planner and the builders read them.
6. `T state --run RUN set stage=scanned next_skill=cc-plan-game`.

## Never
- Never give an agent more than one block or the whole match. Never let a mining agent decide the videos or the final keep levels.
- Never accept a block with no `sensitive` and `avoid` statement: an empty list is a statement that the block was checked, and the agent says so in `notes`.
- Never trust a HUD series you did not look at: the changes list is read against the frames at three places before it is used.

## Hand-off
Invoke Skill `cc-plan-game`.
