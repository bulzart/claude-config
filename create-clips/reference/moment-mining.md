# Moment mining: how a mining agent reads a block of the stream

You get a block of chunks (about 10, 30 minutes), the context brief and the criteria. You bring back what happened, the moments worth cutting,
how rich each chunk is, and what needs blurring. Everything is in rec time (`H:MM:SS.cc` or seconds). You decide; the reports you start from only describe.

## Read in this order (cheap first, expensive only where it pays)
1. `RUN/20-analysis/brief.md` and `clip-criteria.md` (what travels for this streamer and this topic, the lexicon, the touchy list).
2. **The chunk reports**: `RUN/10-media/Cnnnn/report.md` for every chunk of the block, in order (about 2 to 4 KB each). A separate reporter session wrote them while the stream was downloaded: what the sheets show per 22.5 s (the kind of picture, who and what is visible, text on screen quoted as printed),
   what the audio numbers do, what is said, what the chat does, a few neutral sentences about what visibly or audibly happens with their evidence, and what it could not read. **A report is data, not a decision**: it names no moment, no highlight, no round and no keep; its names are as printed or transcribed (unverified);
   its counts are what it counted in the cells. Use it to find where to look. A chunk with no report (or a stale or failed one, see `T status`) is read from the raw data in steps 3 to 7.
3. The block's rows of `RUN/00-inventory/stream.md` (words per minute, loudness, motion, chat per second, ads, gaps, title and game per chunk).
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
 "moments": [ {moment}, ... ],
 "sensitive": [ {"rec_from": 3901.0, "rec_to": 3908.5, "kind": "gore|distress|nudity|personal-data", "what": "...", "region": [0.1,0.1,0.4,0.4] or null, "moment": "B03-M02" or null} ],
 "avoid": [ {"rec_from": 4001.0, "rec_to": 4064.0, "kind": "religion|superstition|hate|tragedy|music", "what": "..."} ],
 "notes": "anything the planner should know (technical trouble, an ad, a gap, a long AFK, the streamer's mood)"}
```
A moment:
```json
{"id": "B03-M02", "rec_from": 3890.0, "rec_to": 3950.5, "setup_from": 3872.0, "payoff_at": 3941.2,
 "type": "reaction-explosion", "title": "short working title", "what_happens": "2 or 3 sentences, plain",
 "hook": "the line or the visual that would open a short", "why_it_travels": "the social reason, in this streamer's terms and the topic's",
 "standalone": 8, "shareability": 9, "short_len_s": [25, 45], "needs_context": "what a viewer must be told, or null",
 "long_form": true, "people": ["..."], "topic_tie": "how it connects to what the internet is talking about, or null",
 "profanity": "none|some|heavy", "music_risk": "none|some", "evidence": ["transcript 3890-3950", "chat 34/s at 3941", "sheet C0022 s3"],
 "confidence": "high|medium|low", "sensitive_refs": [], "avoid_refs": []}
```
`standalone` = how well it works for someone who never saw the stream (1 to 10); `shareability` = how likely this audience sends it on (1 to 10). They are your judgement, with the reason in
`why_it_travels`. `short_len_s` is the span a short of it would run, `setup_from` the earliest second a viewer would need.

Keep the file compact (the planner reads every block's file): at most about 20 KB, plain short sentences, at most 30 moments (the best ones), no pasted transcript, evidence as pointers (a rec time, a sheet), not copies.

## The quality bar
- **Tight bounds**: `rec_from` and `rec_to` are where a clip of it would start and stop, on a pause between words, not a chunk edge. Refine them by reading the words around (`cc.py words`) and the frames.
- **Moments, not minutes**: 3 to 8 per 30 minutes is typical for a lively stream; a quiet block can have 0. Do not pad. Do not skip a quiet moment that is great because the numbers were low.
- **A moment is a whole beat**: setup, turn, payoff. A reaction without what it reacted to is not a moment yet; widen it.
- **Richness is about the stretch, not the peak**: a chunk where the whole 3 minutes is watchable is a 7 or 8 even with no single peak; a chunk of one great joke and 2 minutes of dead air is a 4.
  Use the full scale. The planner reads these to decide how many long videos exist.
- **Say how sure you are**: a moment you only read in the transcript (no frames seen) is "medium" at best; one whose words you could not understand (music, crosstalk) is "low".
- **Touchy things are recorded where they are found** (`sensitive`, `avoid`), with the rec span at full-resolution precision, so the builder does not have to find them again.
- **Speed (the user wants it fast, without losing a check):** batch independent tool calls (several frames, contact sheets or Read calls in ONE message, every sheet you need from ONE PowerShell call, the images read together), aim for about 8 minutes and about 40 tool calls.
- **The picture and the words win** over the brief, the criteria or a report: where they disagree, the moment says what is seen and heard, and `notes` says so.
- **Do not decide the videos.** That is the planner's job; you hand over the best map of the block you can.
