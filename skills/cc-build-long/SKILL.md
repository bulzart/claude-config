---
name: cc-build-long
description: /create-clips production agent, long-form (one whole watch of about 25 minutes to an hour, 16:9): assemble the planned spans of the stream into a good watch, never cutting a scene in half, with captions (unless the run's captions setting is off), light zoom, matching sounds and blurs where seen, as a CapCut project. Internal to that command.
user-invocable: false
---

# cc-build-long: one long video, one CapCut project

> `CC`, `PY`, `T`, `RUN`, `OUT` as in cc-build-short. You build exactly one video, you never ask, you never spawn agents, the chunks are read-only.

## Read now
- `RUN/40-briefs/<id>-brief.md` and `RUN/20-analysis/brief.md`.
- `CC/reference/clip-economy.md` (the long-form section), `CC/reference/edit-craft.md`, `CC/reference/safety.md`, `CC/reference/capcut-build.md`, `CC/reference/context-keeping.md` (short). Read each once, whole, in ONE message.
- The run's captions setting: `T state --run RUN get captions` (`on` by default, `off` when the user picked no captions; your contract says which). Everything below about captions applies only when it is on.
- Speed: independent tool calls go in ONE message (all the contact sheets and frames you need from ONE PowerShell call, the images read together); every check stays.

## Steps
1. **Read the spans**: the brief lists the spans (runs of chunks and pickups) in order with a line each. A span the brief marks as a context span is there for the context it gives: keep what that context needs (`context-keeping.md`). Where you drop dull parts inside a run, the same judgement applies: a bit of one may stay when what follows is unclear without it. For each, read the transcript (`RUN/10-media/Cnnnn/transcript.txt`, or `T window`) and the overview sheets of its chunks; look at dense sheets and full frames only where a decision needs them (a story's start and end, a touchy span, a layout question).
   You decide the final cut list: where a run starts and ends (on a scene boundary, a pause between words), what inside it to drop (long silences, technical trouble, a long AFK, a chat read nobody needs), whether a cold open of the best 20 to 40 s starts the video.
   The length is whatever the whole watch is: the brief's target, usually 25 minutes to an hour (the user, 2026-11-14). Finish a scene even if the video runs a little over an hour, stop earlier when what follows is weak, never pad. A scene, a story or a bit is never cut in half.
   **Check how the video opens and how it ends**: read the words just before its first span and just after its last (`T window`, and a frame). It does not open in the middle of something and it does not end before its last story lands.
   You may finish a scene with the stretch just after your last span when no other video of the plan uses it (the brief names the next video and where it starts). Where a border is not clean (the video opens with the end of a story that began in the previous video's spans, or ends where one starts that finishes in the next video's),
   cut back to the nearest scene that is whole and put the border in your report (the rec times where that story starts and ends) so the wrap-up can show it. Never take a stretch that another video's brief uses (a context span the brief gives you is the planner's choice, and stays).
2. **Touchy check** (safety.md) over every span, by the transcripts and the sheets: religion and superstition are cut out or the stretch is left out (an incidental exclamation is kept and listed); gore, distress and nudity get a `censor` entry (only that span, only that region; personal data, DMs, usernames, IDs and face cams are never blurred); profanity and slurs masked in captions, always, with one asterisk (f*ck, sh*t: `T captions` does the default list by itself, safety.md §3; with captions OFF a spoken slur is audible and nothing masks it: cut around it or leave the span out, as the brief marks it); commercial music noted.
   A long video has many spans: write them down as you go in `OUT/touchy.md` (rec range, what, action) so the report is complete.
3. **Write the EDL** `OUT/edl.json`: `kind: long`, 1920x1080, `layout: {"mode": "native"}`, one segment per straight run or pickup (a run of 20 chunks in a row is one segment, split across chunks automatically), the cold open first when you use one, zooms only on a real beat (a few in the whole video), plain cuts (a short transition only where the stream changes act), sound effects very sparingly (a handful for the whole video),
   with captions ON the captions block (the lexicon in `replace`, `mask_terms` for a profane or slurring word you hear that the default list lacks; the look is Loupe video 04's, the default: Luckiest Guy ALWAYS (no font in the EDL; the one exception is a character it cannot draw, listed by `T captions` as `font_missing_glyphs`), upper case, the word-box; `size` stays `auto`: small to normal for phones and tablets;
   **pick only the box colour to match this video's appearance** and write why in `captions.why`, edit-craft.md "The look"; a video of more than about 23 minutes of speech (3,000 words) falls back to the plain look, in the same font, by itself, `captions.json` says so), with captions OFF none.
   Where the chunk table shows a recording gap, or an ad batch (the brief's avoid spans list the ones the agents judged to be ads: `kind: "ad"`), between two chunks inside one run, treat it as a jump and place the cut deliberately: a run never goes through an ad batch.
4. **Check**: `T edl-check --run RUN --edl OUT/edl.json --make-censor`; fix every warning and every cut that lands inside a word (a long video has hundreds of cuts: only the cuts between segments are facts you must clear; the chunk joins inside a straight run are seamless);
   with captions ON `T captions --run RUN --resolved OUT/resolved.json` (read `silent_stretches_over_4s` and `masked`, the words it masked; read the cues once for any other profane or slurring word the default list missed, add it to `captions.mask_terms` and run it again; with captions OFF skip it). View each blurred file's preview and the frames around it.
5. **Build** with `CC/reference/capcut-build.md` (canvas 1920x1080): ONE command, `T capcut-build --run RUN --video <id>` composes all the pieces, the sound effects, the transitions and the captions in a single CapCut composition, finishes and reads the project back (CapCut closed: if it is open, stop with `ready-to-build`); keep the sound effects few. Never build clip by clip.
   No proxy preview of the whole video: the build's `read_back` (the clip count against the plan, the total length, the joins, the texts, the media on disk, `capcut lint`) and an empty `problems` list are the check, and three frames from the start, middle and end of a proxy only if a render is cheap.
   `OUT/report.md` and `OUT/posting.md` (title, description, hashtags, chapters with rec-to-output timestamps: the output time of a segment is its `at` in `resolved.json`). The report lists each context span kept and what it gives, and the words masked in the captions (`masked` of `T captions`), how the video opens and how it ends, and any border that was not clean (step 1).
6. `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>" videos.<id>.duration_s=<n>` (or `failed` with the reason). C: free space is small: say in the report the project's size and the chunks it uses.

## Never
- Never pad to reach a length. Never cut a scene in half to reach one, and never open or end the video in the middle of a story. With captions ON never a long video with captions missing anywhere speech is; with captions OFF never add any.
- Never more than cuts, captions, a few zooms, short transitions, a blur where required and matching sound effects: no music, sticker, emoji, text overlay, filter or scene effect.
- Never blur more than the span and region where the content is seen; never avoid a gory or distressing span (blur it); never include religion or superstition. Never cut from a span the brief lists as an ad (`kind: "ad"`: an ad batch the agents judged).
- Never copy a chunk into the draft, never `capcut lint --fix`, never save with force.

## Hand-off
Return your short report to the main session.
