# The second look: one agent, after the scan (streamer mode)

The user, 2026-11-20: "Find broadly. Understand deeply. Recover overlooked opportunities. Select only what deserves to be watched." The mining agents read
every line of their block once. A reader can still miss a quiet line in half an hour of talk, set a smaller beat aside to keep the block file short, or not
see that a setup in one block pays off in another. You are a fresh pair of eyes on what the scan did NOT keep, and you add a moment only when it deserves to
be watched. **Most leads end as nothing, and recovering no moment at all is a normal, good result.** A lead is a place to look, never a reason to keep.

## What you get
- `RUN/20-analysis/recall.md` (made by `cc.py recall`; facts only): the stretches no moment covers, with their numbers, and the **leads**, each with an id:
  `maybe` (a moment a mining agent set aside, with why), `reaction` (a chat burst a mining agent set aside as "no reaction" or as the game's own line or
  scene, without his face seen: on the caseoh run three of three such bursts checked hid a laugh on the face cam, because a laugh is almost never in the
  transcript), `summary` (a line of a block's summary that no moment covers), `thread` (a point of a running bit
  or a story that no moment covers: a lead of its own only with `config.json -> recall.thread_leads`, because 15 such leads on two runs gave no moment, only two context lines; the threads of every block are always listed at the end, with their points no moment covers, so a bit that runs through two blocks is visible as one: read them as context), `sample`
  (a window placed by the clock alone: no number chose it, so it finds what has no numbers: a quiet line, a picture gag).
- The block files `RUN/20-analysis/blocks/block-NN.json` (what the scan found: the moments, the acts, the summaries, the notes), `RUN/20-analysis/brief.md`
  and `clip-criteria.md`, and the data: `RUN/10-media/Cnnnn/report.md`, `transcript.txt` (`[sub]` = words that match the subtitle on screen: in a game, the
  game's own line), the sheets, and the tools (`T window`, `T words`, `T frame`, `T sheet`, `T heat`).

## Read first
1. `CC/reference/moment-mining.md` (the moment card and the quality bar: yours are the same) and `CC/reference/context-keeping.md` (short).
2. `brief.md`, `clip-criteria.md`, then `recall.md` whole.
3. The moments the scan already has: every block file's `moments` (id, span, title), so you never find one again.

## Which leads (the user, 2026-11-21: selective, in proportion to what it can find)
On the caseoh run one agent naming all 102 leads of a 5-hour stream took 22 minutes and about 415k tokens for two weak finds and no change to the plan; the finds that mattered were laughs on the face cam. `recall.md` lists the leads in tiers:
- **Look first** (each gets a line in `checked`): a chat burst set aside without his face seen, a beat its miner set aside as unsure.
- **Sample windows** (each gets a line; a quick look at the words and the face: most hold nothing).
- **The rest** (summary lines no moment covers, beats set aside with a reason, the threads) is context: open one only where it may hold the setup or the payoff of something you are checking, and give it a line when you do.
Reuse what exists: the chunk's dense sheets show the face cam when it is large enough; make a face-cam strip only where they cannot settle it.

## How to look (a second look at the likeliest places, not a second scan)
- **His face is evidence the words do not carry.** Find where the face cam sits once (`T frame --at <rec> --max-width 960`, read its place as fractions of
  the frame, e.g. `0,0.1,0.21,0.3` for a top-left inset) and look at it with a face-cam strip: `T sheet --from <rec_from> --to <rec_to> --step 0.5 --crop
  x,y,w,h` (one image, every cell timestamped). A laugh (doubling over, covering his face, leaning back, a grin), a jump back or a stare is a reaction; the
  game's line plus his laugh is a moment like any other (the game's line the setup, his laugh the payoff), judged by the same bar. A stream with no face cam:
  the picture and the sound numbers only, and say so.
- `reaction`: the face-cam strip over the burst first, then the words around it. Laughing at something touchy (safety.md: hate, religion) stays out; a song
  under it is `music_risk`.
- A `summary` or `sample` lead whose words carry the game's joke, a reveal, a fail or a stunt gets his face too (a face-cam strip), not the words alone: on the caseoh run (2026-11-20) one agent named all 102 leads of a 5-hour stream in 96 tool calls and missed the best find a closer look had made, a laugh on the face cam at a game line with no chat burst.
- `summary`, `thread` and `maybe`: read the words around it (`T window` from about 30 s before to 60 s after, longer when it is a story) and the chunk's
  report lines for that time; look at a dense sheet or a frame when the picture may carry it.
- `sample`: read the window's words (`T window --from <rec_from> --to <rec_to>`), look at its cells on the dense sheet (or `T sheet` of the window) and at
  his face (a face-cam strip of the window at a 1 s step): is
  there anything here this streamer's audience would enjoy (a quiet line that lands, a visual gag, an absurd game event, a reaction, a callback) that no
  moment holds? Most sample windows hold nothing: say so in a few words.
- Threads: a setup in one block and its payoff in another, with no moment holding the pair, is a lead for a moment (or for a moment's context). The same
  bit named in two blocks is one thread.
- Batch: several `T window` lines in ONE PowerShell call, the sheets and frames read together in one message. Never read a whole block's transcripts again.
  Aim for about 8 minutes and about 30 tool calls.

## Decide each lead you looked at (one line in `checked`)
`moment` (you wrote a card: give its id), `covered` (a moment of the scan already holds it: name it), `context` (not a moment, but context a moment needs:
name the moment and the span), `not-a-moment` (why, in a few words: an ordinary drive, a game line with no reaction, a weak joke, no payoff, a song),
`unclear` (the data cannot settle it: say what would, e.g. "listen: his voice or the radio?").
The bar does not drop because a lead exists. A beat that is fine inside a long video but would not make anyone laugh, gasp or care on its own is
`not-a-moment` here: the long video keeps the stretch it lies in anyway.

## A recovered moment
The card of moment-mining.md with every field, id `SL-M01`, `SL-M02`, ..., plus `"found_by": "second-look"`, `"lead": ["L034"]` (the lead or leads it came
from) and `"why_missed"` (one line: quiet, no chat burst; carried by the picture; setup and payoff in different blocks; set aside by its block; ...). Tight
bounds, a whole beat (setup, turn, payoff), `confidence` as moment-mining.md says (a moment you only read in the transcript is "medium" at best). Never
write a card for what a moment already holds, never widen a scan moment (say `context`), never decide the videos.

## Write ONE file: `RUN/20-analysis/second-look.json`
```json
{"moments": [ {card fields..., "found_by": "second-look", "lead": ["L034"], "why_missed": "..."} ],
 "checked": [ {"lead": "L034", "verdict": "moment|covered|context|not-a-moment|unclear", "why": "a few words", "moment": "SL-M01 or B03-M05 or null"} ],
 "threads": [ {"what": "...", "points": [3916.0, 6147.0], "moments": ["B03-M02", "SL-M01"]} ],
 "notes": "anything the planner should know"}
```
Then `T recall --run RUN --check RUN/20-analysis/second-look.json`: every look-first lead and sample window must be named once (one looked at and set aside is fine, one never looked at is not); fix what it lists. Check the file parses. Write nothing else; read media only; never ask, never spawn agents.
Return three lines: the file, how many moments you recovered of how many leads, anything the planner must know.
