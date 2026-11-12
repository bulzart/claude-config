---
name: cc-scan
description: /create-clips phase 3: scan agents read the stream in blocks of chunks and bring back what happened, the moments worth cutting, how rich each chunk is and what needs blurring. Internal to that command.
user-invocable: false
---

# cc-scan: mine the stream

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/moment-mining.md` (the reading order, the block file, the quality bar). Read it whole once; each scan agent reads it too.

## Steps
1. **Blocks**: `T blocks --run RUN --chunks N` with N from `config.json -> agents.scan_chunks_streamer` (6: about 18 minutes per agent). Record the list in `state.json` (`T state --run RUN set scan.blocks=<n>`).
2. **Spawn the scan agents** (general-purpose, **`model: "haiku"`**: `config.json -> agents.scan_model`; the scan is the fast pass, and planning, editing and everything else use the model the user picked, so no other agent gets a `model` argument),
   one per block, at most `config.json -> agents.scan_max` = 6 at once, the next block as one finishes; never two agents on one block. One message per wave. Each agent's contract (it never sees this skill):
   - the run path; its block (the chunk ids, the rec range); its output `RUN/20-analysis/blocks/block-NN.json`;
   - it is the fast pass: complete and factual, evidence as pointers (a rec time, a sheet), "not seen" where it did not see, never a number it did not measure; the planner re-checks what it will use;
   - read, in this order: `CC/reference/moment-mining.md`, `RUN/20-analysis/brief.md`, `RUN/20-analysis/clip-criteria.md`, then the data as the playbook says (stream.md rows, transcripts of every chunk in the block, the overview sheets, dense sheets and `T window` / `T frame` / `T sheet` / `T words` only where a candidate or a mismatch needs them);
   - it judges moments by the brief and the criteria, not by numbers alone; records what must be blurred (`sensitive`) and what must be avoided (`avoid`: religion, superstition, hate, tragedy, commercial music; `CC/reference/safety.md` §1 and §3, which it reads);
   - it reads media only (never moves, renames or writes into `10-media`), writes only its block file, never asks, never spawns agents;
   - it returns three lines: the file, how many moments, anything the planner must know.
3. **Check each block file** when its agent returns: valid JSON (`& $PY -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <file>`), the fields of moment-mining.md present, rec times inside the block, a richness score per chunk, every moment with bounds, a hook and a reason.
   A bad or empty file: one retry with the problem named; a second failure is recorded in `state.json` (`scan.failed`) and the block is covered by the planner reading its transcripts itself.
4. `T state --run RUN set stage=scanned next_skill=cc-plan`.

## Never
- Never give an agent more than one block or the whole stream. Never let a scan agent decide the videos.
- Never give the scan agents' model to any other agent, and never ask the user which model to use.
- Never accept a moment list with no touchy-spans fields: an empty `sensitive` and `avoid` is a statement that the block was checked, so the agent says it did.

## Hand-off
Invoke Skill `cc-plan`.
