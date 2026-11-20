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
1. **Blocks**: `T blocks --run RUN --chunks N --min-blocks M` with N from `config.json -> agents.scan_chunks_streamer` (10: about 30 minutes per agent; the agents start from the chunk reports, so a block can be large) and M from `config.json -> agents.scan_min_blocks` (2: a short stream still gets at least two blocks, so two agents read it side by side; the block size becomes min(N, ceil(chunks / M))). Record the list in `state.json` (`T state --run RUN set scan.blocks=<n>`) and add one item per block to `RUN/todo.md` (rule 16), ticked as each block's file passes the check in step 3.
   The sound-effect catalogue (`T sfx-scan`) was started in `cc-start`; the mining agents do not need it. The speaker facts (`T voices`, started in `cc-start`) are finished before the agents are spawned (run `T voices --run RUN` again: it only reads what is still missing), so every transcript carries its `[sub]` marks.
2. **Spawn the mining agents** (general-purpose, **no `model` argument**: they use the model the user picked; one per block, at most `config.json -> agents.scan_max` = 6 at once, the next block as one finishes; never two agents on one block). ALL the blocks of a wave in ONE message. Each agent's contract (it never sees this skill):
   - the run path; its block (the chunk ids, the rec range); its output `RUN/20-analysis/blocks/block-NN.json`;
   - read, in this order: `CC/reference/moment-mining.md`, `CC/reference/context-keeping.md` (short), `RUN/20-analysis/brief.md`, `RUN/20-analysis/clip-criteria.md`, then the data as moment-mining.md says: the chunks' reports first (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, observations only), the stream.md rows, the transcripts of every chunk in the block,
     and the overview sheets, dense sheets and `T window` / `T frame` / `T sheet` / `T words` only where a candidate or a mismatch needs them (a chunk without a report is read from its raw data);
   - a report decides nothing: what is a moment, what is on brand and what is touchy is the agent's call, by the brief and the criteria, not by numbers alone; names in a report are as printed or transcribed, never verified;
   - the picture wins: where the brief, the criteria or a report says something the frames or the words show otherwise, the moment says what is seen and the agent says so in `notes`;
   - `[sub]` in a transcript marks words that match the subtitle on screen (in a game: the game's own line, not the streamer); an unmarked line is not attributed; the marks never drop a moment (moment-mining.md "Who speaks");
   - speed: it batches independent tool calls (several frames, sheets or Read calls in ONE message, all the contact sheets it needs from ONE PowerShell call) and aims for about 8 minutes and about 40 tool calls;
   - it records what must be blurred (`sensitive`: gore, distress, nudity only; never personal data, DMs, usernames or face cams) and what must be avoided (`avoid`: religion, superstition, hate, tragedy, commercial music; `CC/reference/safety.md` §1, §2 and §3, which it reads);
   - **the ad batches** (moment-mining.md "Ad-marked chunks"): the recorder skips nothing, ad or not ad, and passes Twitch's own marker on (`(ad-marked)` in stream.md, `ad_chunks` of its block in `T blocks`). The agent looks at every marked chunk of its block (report, overview sheet, a few words), writes one `ad_batches` entry per batch with its verdict (`ad`, `stream` or `mixed`), and leaves a batch it judges `ad` out of its analysis (no moments, richness 0, reason `ad`); it also records an advertisement the marker missed. Tell each agent which chunks of its block are marked (from `T blocks`);
   - **the acts** (moment-mining.md "acts"): the stretches of its block that are each one watchable thing from its start to its end, in time order across the whole block (dull stretches and breaks included), with how each starts and ends and whether it is open at the block's edge (`open_start`, `open_end`). The planner sets the borders between the long videos between acts, so that no story is split between two videos; the agent does not decide the videos;
   - **the spoken language** (the `Spoken language` line of `stream.md`; `CC/reference/language.md`): when it is not English the agent reads the transcripts as spoken, quotes lines as spoken and writes its block file in English;
   - **the chat heat** (the user, 2026-11-15; `CC/reference/chat-heat.md`, read whole once, and `RUN/20-analysis/heat.md`): tell it the burst ids of its block (`T blocks` lists them as `bursts`) and how to read their rows without reading the whole file: `T heat --run RUN --from <its rec_from> --to <its rec_to> --rows`. Every burst gets one look and ends as a moment (its numbers in the moment's `heat`), as covered (inside a moment it wrote) or as a `heat_review` line saying what it was and why it is not a moment, with what his face did (`face`, from a face-cam strip: a laugh is almost never in the transcript; moment-mining.md); heat adds at most one point to a moment that at least two other kinds of evidence already rate, never picks a moment and never drops one; a run with no chat (`has_chat: false` in heat.json): skip it;
   - it reads media only (never moves, renames or writes into `10-media`), writes only its block file, never asks, never spawns agents;
   - `maybes` and `threads` (moment-mining.md): what it noticed and set aside, one line each with why (never to fill them), and the running bits and stories with their points;
   - it returns three lines: the file, how many moments, anything the planner must know.
3. **Check each block file** when its agent returns: valid JSON (`& $PY -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" <file>`), the fields of moment-mining.md present, rec times inside the block, a richness score per chunk, every moment with bounds, a hook and a reason.
   Every ad-marked chunk of the block is covered by an `ad_batches` entry (or the agent says in `notes` why not); a file with an ad-marked chunk the agent never mentions is sent back once with that named.
   `acts` are in time order, inside the block and cover it (a gap between two acts is named); a file without them is sent back once with that named (if it is still missing, the planner reads that block's summary lines and transcripts for the borders instead).
   `T heat --run RUN --coverage RUN/20-analysis/blocks/block-NN.json` lists the bursts of the block that no moment spans, no moment names in its `heat.burst` and no `heat_review` line names or places (`unmentioned`): a file with any is sent back once with them named, like an ad batch (a burst looked at and rejected is fine, one never looked at is not). A run with no chat: nothing to check.
   A bad or empty file: one retry with the problem named; a second failure is recorded in `state.json` (`scan.failed`) and the block is covered by the planner reading its reports and transcripts itself.
   **Reconcile**: where the moments contradict the brief, `clip-criteria.md` or `recon.md` (a wrong name, a wrong topic, a guest who is someone else), correct those files now, with a line saying so at the top: the planner and the builders read them.
3b. **The second look** (the user, 2026-11-20: "Find broadly. Understand deeply. Recover overlooked opportunities. Select only what deserves to be watched."; `CC/reference/second-look.md`; on unless `config.json -> recall.second_look` is false): when every block file has passed, `T recall --run RUN` (facts only: the stretches no moment covers, the miners' `maybes`, their summary lines and thread points no moment covers, and sample windows placed by the clock alone; `RUN/20-analysis/recall.md`). Then spawn ONE second-look agent (general-purpose, no `model` argument). Its contract: the run path; read `CC/reference/second-look.md` whole and follow it; its output `RUN/20-analysis/second-look.json`; read media only, write only that file, never ask, never spawn agents; return three lines. Add one item to `RUN/todo.md` for it.
   Check its file when it returns: valid JSON, `T recall --run RUN --check RUN/20-analysis/second-look.json` passes (an unmentioned lead sends the file back once, with the leads named), every recovered moment has the card's fields and `found_by: "second-look"`. A second failure is recorded in `state.json` (`scan.second_look=failed`) and the plan goes on with the scan's moments. Recovering nothing is a normal result, never a failure.
4. `T state --run RUN set stage=scanned next_skill=cc-plan`, then tick the scan in `RUN/todo.md` and set its `Next:` line (rule 16).

## Never
- Never give an agent more than one block or the whole stream. Never let a mining agent decide the videos.
- Never accept a moment list with no touchy-spans fields: an empty `sensitive` and `avoid` is a statement that the block was checked, so the agent says it did.
- Never pass a `model` to an agent, and never spawn an agent to read raw chunks that a report already describes.
- Never let a chat burst alone make a moment, and never let a quiet chat drop one (`chat-heat.md`).

## Hand-off
Invoke Skill `cc-plan`.
