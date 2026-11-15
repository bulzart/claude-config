# Moment mining: how a mining agent reads a block of the stream

You get a block of chunks (about 10, 30 minutes), the context brief and the criteria. You bring back what happened, the moments worth cutting,
how rich each chunk is, and what needs blurring (gore, distress, nudity only: personal data, DMs, usernames and face cams are never recorded). Everything is in rec time (`H:MM:SS.cc` or seconds). You decide; the reports you start from only describe.

## Read in this order (cheap first, expensive only where it pays)
1. `RUN/20-analysis/brief.md` and `clip-criteria.md` (what travels for this streamer and this topic, the lexicon, the touchy list). `CC/reference/context-keeping.md` is short: read it too.
2. **The chunk reports**: `RUN/10-media/Cnnnn/report.md` for every chunk of the block, in order (about 2 to 4 KB each). A separate reporter session wrote them while the stream was downloaded: what the sheets show per 22.5 s (the kind of picture, who and what is visible, text on screen quoted as printed),
   what the audio numbers do, what is said, what the chat does, a few neutral sentences about what visibly or audibly happens with their evidence, and what it could not read. **A report is data, not a decision**: it names no moment, no highlight, no round and no keep; its names are as printed or transcribed (unverified);
   its counts are what it counted in the cells. Use it to find where to look. A chunk with no report (or a stale or failed one, see `T status`) is read from the raw data in steps 3 to 7.
3. The block's rows of `RUN/00-inventory/stream.md` (words per minute, loudness, motion, chat per second, ads, gaps, title and game per chunk; `(ad-marked)` after a chunk id: see "Ad-marked chunks" below), then the chat bursts of your block: `T heat --run RUN --from <your rec_from> --to <your rec_to> --rows` prints your chunks' rows and your bursts' rows (the whole `RUN/20-analysis/heat.md` of a long stream is long: do not read it whole; `T blocks` lists the burst ids as `bursts`); `CC/reference/chat-heat.md`, read whole once, says how to read them.
4. The transcripts of the block: `RUN/10-media/Cnnnn/transcript.txt` for every chunk (about 600 words each). This is where most moments are found; the reports quote only a few lines. Read them all, in order.
5. `RUN/10-media/Cnnnn/sheets/overview.jpg` of a chunk (24 frames per chunk, 7.5 s apart: the visual flow, who is on camera, what is on screen), where its report is thin or you doubt it.
6. Only for a candidate window or a place where the words and the numbers disagree (loud and chat spike but no words; a long silence with a lot of motion): the dense sheets of that window
   (`RUN/10-media/Cnnnn/sheets/sheet-NN.jpg`, 0.75 s per frame, every frame timestamped) or `cc.py window --run RUN --from T --to T` (transcript, per-second table and chat for the span),
   `cc.py frame --run RUN --at T` (one frame at full resolution), `cc.py sheet --run RUN --from T --to T --step 0.25` (a denser sheet of a short window).
7. `RUN/10-media/Cnnnn/timeline.md` only for a span you are measuring (it has a row per second).
The signals are numbers a script measured and the reports are what a reporter saw, not verdicts: a loud second with a chat spike and a short burst of words is a place to look, not a moment. A quiet funny line is a moment with no
numbers at all. You decide.

## What to write: `RUN/20-analysis/blocks/block-NN.json`
```json
{"block": 3, "chunks": ["C0021","C0022"], "rec_from": 3780.0, "rec_to": 4860.0,
 "summary": "what happens in this block, 6 to 12 lines in time order, each with its rec time (who is on, what they do, the topic, the turns)",
 "people": [{"name": "...", "role": "guest|co-streamer|mentioned", "first_rec": 3790.5, "notes": "spelling, how Whisper wrote it"}],
 "lexicon_fixes": [["Whisper wrote", "right spelling"]],
 "richness": [{"chunk": "C0021", "score": 7, "why": "one line: how good this chunk's content is for this streamer's audience, as a stretch to watch"}],
 "acts": [ {"rec_from": 3780.0, "rec_to": 4150.5, "kind": "game|guest|story|challenge|topic|chat|break|dull|other", "what": "one line: what this stretch is, as a watch", "starts": "how it opens: what a viewer sees and hears", "ends": "how it ends: the result, the guest leaving, the topic closing, or 'continues in the next block'", "open_start": false, "open_end": false} ],
 "moments": [ {moment}, ... ],
 "sensitive": [ {"rec_from": 3901.0, "rec_to": 3908.5, "kind": "gore|distress|nudity", "what": "...", "region": [0.1,0.1,0.4,0.4] or null, "moment": "B03-M02" or null} ],
 "avoid": [ {"rec_from": 4001.0, "rec_to": 4064.0, "kind": "religion|superstition|hate|tragedy|music", "what": "..."} ],
 "ad_batches": [ {"chunks": ["C0024"], "rec_from": 4320.0, "rec_to": 4372.1, "verdict": "ad|stream|mixed", "what": "what the sheets, the words and the sound show", "evidence": ["report C0024", "sheet C0024 s2"]} ],
 "heat_review": [ {"burst": "H013", "peak_rec": 4010.0, "kind": "commands", "why": "one line: what you named it (chat-heat.md) and why it is not a moment"} ],
 "notes": "anything the planner should know (technical trouble, an ad, a gap, a long AFK, the streamer's mood)"}
```
`ad_batches` is `[]` when no chunk of the block is ad-marked and you saw no advertisement (see "Ad-marked chunks"). `heat_review` is `[]` when your block has no chat burst or every burst lies inside a moment you wrote (see "Chat heat" below).
`acts` (the user, 2026-11-14: a long video is one whole watch, so the planner sets the borders between long videos between the stream's acts and never inside a story): the stretches of your block that are each one watchable thing from its start to its end
(a game or a match from the lobby to the result, a guest segment, a story from its setup to its end, a challenge or a bet to its verdict, a topic the stream stayed on, a break, a dull stretch), in time order and covering the whole block, usually 2 to 8 of them. A dull stretch or a break is an act of its own (kind `dull` or `break`), so the planner can see where a border may fall.
`starts` and `ends` say what a viewer would see and hear at the two edges (the result lands, the guest leaves, the streamer changes the game), so the planner can tell a clean border from a story cut in half. An act that begins before your block or goes on after it is marked `open_start` or `open_end`, with the edge you can see: the planner joins it to the neighbouring block's act.
You do not decide the videos: you say where the stream's own acts begin and end, from the words and the frames.
A moment:
```json
{"id": "B03-M02", "rec_from": 3890.0, "rec_to": 3950.5, "setup_from": 3872.0, "payoff_at": 3941.2,
 "type": "reaction-explosion", "title": "short working title", "what_happens": "2 or 3 sentences, plain",
 "hook": "the line or the visual that would open a short", "why_it_travels": "the social reason, in this streamer's terms and the topic's",
 "standalone": 8, "shareability": 9, "short_len_s": [25, 45], "needs_context": "what a viewer must be told, and where the stream tells it if you saw (a rec span), or null",
 "long_form": true, "people": ["..."], "topic_tie": "how it connects to what the internet is talking about, or null",
 "profanity": "none|some|heavy", "music_risk": "none|some", "evidence": ["transcript 3890-3950", "chat 34/s at 3941", "sheet C0022 s3"],
 "heat": null, "confidence": "high|medium|low", "sensitive_refs": [], "avoid_refs": []}
```
`standalone` = how well it works for someone who never saw the stream (1 to 10); `shareability` = how likely this audience sends it on (1 to 10). They are your judgement, with the reason in
`why_it_travels`. `short_len_s` is the span a short of it would run, `setup_from` the earliest second a viewer would need. `needs_context` is what a viewer must be told to follow the moment: when the stream itself tells it somewhere in your block, add where (a rec span); when you cannot see where (it may lie before your block, or in another one), say only what is needed, because the planner sees every block and finds it. `CC/reference/context-keeping.md` says how that is judged; anything not tied to a moment goes in `notes`.
`heat` is `null` when no chat burst lies in the moment, else the burst's numbers as `chat-heat.md` shows them (`burst`, `peak_rec`, `z`, `pct`, `n`, `base`, `says`, `kind`, `nudge`): heat adds at most one point to `shareability`, only when at least two other kinds of evidence already rate the moment, and never decides it.

Keep the file compact (the planner reads every block's file): at most about 20 KB, plain short sentences, at most 30 moments (the best ones), no pasted transcript, evidence as pointers (a rec time, a sheet), not copies.

## Ad-marked chunks: you judge them, and the ad batches are left out
The recorder skips nothing, ad or not ad (the user, 2026-11-14). Every segment Twitch marks as an ad (a stitched-ad range, or a title that is not `live`) is saved as chunks of its own and the marker is passed on: `(ad-marked)` after the chunk id in `stream.md`, `ad_chunks` per block and `ad_batches` (consecutive marked chunks = one ad break) in `T blocks`, `kind: "ad"` in the chunk's `chunk.json`. The marker is Twitch's word, not a verdict.
- Look at every marked chunk of your block like any other (its report, its overview sheet, a few words) and write ONE entry per batch in `ad_batches` with your `verdict`: **`ad`** (an advertisement: a commercial, a trailer, a house ad, a countdown), **`stream`** (the marker was wrong: it is the stream), **`mixed`** (say in `what` which seconds are which).
- **A batch you judge `ad` is left out of the analysis**: no moments in it, no hook, richness 0 for its chunks with the reason `ad`, nothing in `summary` beyond one line ("ad break, 52 s, rec ..."). The planner puts it into `avoid.json`, so no video cuts from it.
- A batch you judge `stream`, or a `mixed` part, is mined like any other stretch, and `notes` says the marker was wrong there.
- An advertisement the marker missed (an unmarked pre-roll or house ad you see in the frames) goes in `ad_batches` the same way (`verdict: "ad"`, the chunks and the span). The streamer's own sponsor read is NOT an ad batch: it is the stream, and the criteria say what to do with it.
- The stream's second after an ad: the chunk after an ad batch usually has a `gap_before_s` (the stream seconds the ad session never received): it is the join, not a fault of the chunk.

## Chat heat: a clue, never a verdict
The user, 2026-11-15: the chat's messages are counted in 4-second bins against this stream's own normal and the bursts are listed (`RUN/20-analysis/heat.md`; the ids of your block are in `T blocks`; the method is `CC/reference/chat-heat.md`). The numbers are facts; what a burst means is yours to judge.
- **Every burst of your block gets one look** (about 30 seconds): its row, what chat says, the words from 14 s before its onset to 4 s after its peak, a frame when the words do not explain it. It ends as a moment (its numbers go in the moment's `heat`), as covered (it lies inside a moment you wrote), or as a `heat_review` line saying what it was and why it is not a moment
  (commands or a giveaway, spam on request, a raid or a gifted-sub flood, the surge after an ad, a technical complaint, talk during a break, nothing on screen explains it). The main session checks that none was skipped (`T heat --coverage`).
- Heat **corroborates and never creates**: up to one point on `shareability`, only when at least two other kinds of evidence (the words, the picture and sound, the streamer's reaction, standalone and hook, the topic) already rate the moment. It never drops a moment: a quiet chat, a chat with no capture and a quiet funny line say nothing.
- It also tells where the cause starts (`setup_from`) and how long the reaction lasts (`rec_to`).

## The quality bar
- **Chat heat never picks and never drops a moment** (`chat-heat.md`): a loud burst nobody can explain is a `heat_review` line, and a great quiet moment with no burst is still a moment.
- **Tight bounds**: `rec_from` and `rec_to` are where a clip of it would start and stop, on a pause between words, not a chunk edge. Refine them by reading the words around (`cc.py words`) and the frames.
- **Moments, not minutes**: 3 to 8 per 30 minutes is typical for a lively stream; a quiet block can have 0. Do not pad. Do not skip a quiet moment that is great because the numbers were low.
- **A moment is a whole beat**: setup, turn, payoff. A reaction without what it reacted to is not a moment yet; widen it.
- **Richness is about the stretch, not the peak**: a chunk where the whole 3 minutes is watchable is a 7 or 8 even with no single peak; a chunk of one great joke and 2 minutes of dead air is a 4.
  Use the full scale. The planner reads these to decide how many long videos exist.
- **Say how sure you are**: a moment you only read in the transcript (no frames seen) is "medium" at best; one whose words you could not understand (music, crosstalk) is "low".
- **Touchy things are recorded where they are found** (`sensitive`, `avoid`), with the rec span at full-resolution precision, so the builder does not have to find them again.
- **Speed (the user wants it fast, without losing a check):** batch independent tool calls (several frames, contact sheets or Read calls in ONE message, every sheet you need from ONE PowerShell call, the images read together), aim for about 8 minutes and about 40 tool calls.
- **The picture and the words win** over the brief, the criteria or a report: where they disagree, the moment says what is seen and heard, and `notes` says so.
- **Acts end where the stream ends them**: an act's bounds are where its story, game or conversation really starts and finishes (read the words around each edge), never a chunk edge; one still going at the end of your block is `open_end`, never closed by you.
- **Do not decide the videos.** That is the planner's job; you hand over the best map of the block you can (the moments and the acts).
