---
name: cc-build-long
description: /create-clips production agent, long-form (about an hour, 16:9): assemble the planned spans of the stream into a good watch, never cutting a scene in half, with captions (unless the run's captions setting is off), light zoom, matching sounds and blurs where seen, as a CapCut project. Internal to that command.
user-invocable: false
---

# cc-build-long: one long video, one CapCut project

> `CC`, `PY`, `T`, `RUN`, `OUT` as in cc-build-short. You build exactly one video, you never ask, you never spawn agents, the chunks are read-only.

## Read now
- `RUN/40-briefs/<id>-brief.md` and `RUN/20-analysis/brief.md`.
- `CC/reference/clip-economy.md` (the long-form section), `CC/reference/edit-craft.md`, `CC/reference/safety.md`, `CC/reference/capcut-build.md`. Read each once, whole, in ONE message.
- The run's captions setting: `T state --run RUN get captions` (`on` by default, `off` when the user picked no captions; your contract says which). Everything below about captions applies only when it is on.
- Speed: independent tool calls go in ONE message (all the contact sheets and frames you need from ONE PowerShell call, the images read together); every check stays.

## Steps
1. **Read the spans**: the brief lists the spans (runs of chunks and pickups) in order with a line each. For each, read the transcript (`RUN/10-media/Cnnnn/transcript.txt`, or `T window`) and the overview sheets of its chunks; look at dense sheets and full frames only where a decision needs them (a story's start and end, a touchy span, a layout question).
   You decide the final cut list: where a run starts and ends (on a scene boundary, a pause between words), what inside it to drop (long silences, technical trouble, a long AFK, a chat read nobody needs), whether a cold open of the best 20 to 40 s starts the video.
   About an hour is a guide: finish a scene even if the video runs past an hour; stop earlier when what follows is weak. A scene, a story or a bit is never cut in half.
2. **Touchy check** (safety.md) over every span, by the transcripts and the sheets: religion and superstition are cut out or the stretch is left out (an incidental exclamation is kept and listed); gore, distress, nudity and personal data get a `censor` entry (only that span, only that region); slurs masked in captions (with captions OFF a spoken slur is audible and nothing masks it: cut around it or leave the span out, as the brief marks it); commercial music noted.
   A long video has many spans: write them down as you go in `OUT/touchy.md` (rec range, what, action) so the report is complete.
3. **Write the EDL** `OUT/edl.json`: `kind: long`, 1920x1080, `layout: {"mode": "native"}`, one segment per straight run or pickup (a run of 20 chunks in a row is one segment, split across chunks automatically), the cold open first when you use one, zooms only on a real beat (a few in the whole video), plain cuts (a short transition only where the stream changes act), sound effects very sparingly (a handful for the whole hour),
   with captions ON the captions block (the lexicon in `replace`; the look is the default word-box one, `size` stays `auto`: small to normal for phones and tablets; **pick the font family and the box colour to match this video's appearance** and write why in `captions.why`, edit-craft.md "The look"; a video of more than about 17 minutes of speech falls back to the plain look by itself, `captions.json` says so), with captions OFF none.
   Where the chunk table shows a recording gap or skipped ads between two chunks inside one run, treat it as a jump and place the cut deliberately.
4. **Check**: `T edl-check --run RUN --edl OUT/edl.json --make-censor`; fix every warning and every cut that lands inside a word (an hour has hundreds of cuts: only the cuts between segments are facts you must clear; the chunk joins inside a straight run are seamless);
   with captions ON `T captions --run RUN --resolved OUT/resolved.json` (read `silent_stretches_over_4s`; with captions OFF skip it). View each blurred file's preview and the frames around it.
5. **Build** with `CC/reference/capcut-build.md` (canvas 1920x1080): ONE command, `T capcut-build --run RUN --video <id>` composes all the pieces, the sound effects, the transitions and the captions in a single CapCut composition, finishes and reads the project back (CapCut closed: if it is open, stop with `ready-to-build`); keep the sound effects few. Never build clip by clip.
   No proxy preview of the whole hour: the build's `read_back` (the clip count against the plan, the total length, the joins, the texts, the media on disk, `capcut lint`) and an empty `problems` list are the check, and three frames from the start, middle and end of a proxy only if a render is cheap.
   `OUT/report.md` and `OUT/posting.md` (title, description, hashtags, chapters with rec-to-output timestamps: the output time of a segment is its `at` in `resolved.json`).
6. `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>" videos.<id>.duration_s=<n>` (or `failed` with the reason). C: free space is small: say in the report the project's size and the chunks it uses.

## Never
- Never pad to reach an hour. Never cut a scene in half to reach one. With captions ON never a long video with captions missing anywhere speech is; with captions OFF never add any.
- Never more than cuts, captions, a few zooms, short transitions, a blur where required and matching sound effects: no music, sticker, emoji, text overlay, filter or scene effect.
- Never blur more than the span and region where the content is seen; never avoid a gory or distressing span (blur it); never include religion or superstition.
- Never copy a chunk into the draft, never `capcut lint --fix`, never save with force.

## Hand-off
Return your short report to the main session.
