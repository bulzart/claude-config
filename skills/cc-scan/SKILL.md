---
name: cc-scan
description: /create-clips streamer mode, phase 3: mining agents read the chunk reports of a block of chunks (the transcripts, sheets and frames only where a candidate needs them) and bring back what happened, the moments worth cutting, how rich each chunk is and what needs blurring. Internal to that command.
user-invocable: false
---

# cc-scan: mine the stream

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/moment-mining.md` (the reading order, the block file, the quality bar). Read it whole once; each mining agent reads it too.

## Steps
1. **Blocks**: `T blocks --run RUN --chunks N` with N from `config.json -> agents.scan_chunks_streamer` (10: about 30 minutes per agent; the agents start from the chunk reports, so a block can be large). Record the list in `state.json` (`T state --run RUN set scan.blocks=<n>`).
2. **Spawn the mining agents** (general-purpose, **no `model` argument**: they use the model the user picked; one per block, at most `config.json -> agents.scan_max` = 6 at once, the next block as one finishes; never two agents on one block). One message per wave. Each agent's contract (it never sees this skill):
   - the run path; its block (the chunk ids, the rec range); its output `RUN/20-analysis/blocks/block-NN.json`;
   - read, in this order: `CC/reference/moment-mining.md`, `RUN/20-analysis/brief.md`, `RUN/20-analysis/clip-criteria.md`, then the data as moment-mining.md says: the chunks' reports first (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, observations only), the stream.md rows, the transcripts of every chunk in the block,
     and the overview sheets, dense sheets and `T window` / `T frame` / `T sheet` / `T words` only where a candidate or a mismatch needs them (a chunk without a report is read from its raw data);
   - a report decides nothing: what is a moment, what is on brand and what is touchy is the agent's call, by the brief and the criteria, not by numbers alone; names in a report are as printed or transcribed, never verified;
   - it records what must be blurred (`sensitive`) and what must be avoided (`avoid`: religion, superstition, hate, tragedy, commercial music; `CC/reference/safety.md` §1 and §3, which it reads);
   - it reads media only (never moves, renames or writes into `10-media`), writes only its block file, never asks, never spawns agents;
   - it returns three lines: the file, how many moments, anything the planner must know.
3. **Check each block file** when its agent returns: valid JSON (`& $PY -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <file>`), the fields of moment-mining.md present, rec times inside the block, a richness score per chunk, every moment with bounds, a hook and a reason.
   A bad or empty file: one retry with the problem named; a second failure is recorded in `state.json` (`scan.failed`) and the block is covered by the planner reading its reports and transcripts itself.
4. `T state --run RUN set stage=scanned next_skill=cc-plan`.

## Never
- Never give an agent more than one block or the whole stream. Never let a mining agent decide the videos.
- Never accept a moment list with no touchy-spans fields: an empty `sensitive` and `avoid` is a statement that the block was checked, so the agent says it did.
- Never pass a `model` to an agent, and never spawn an agent to read raw chunks that a report already describes.

## Hand-off
Invoke Skill `cc-plan`.
