---
name: cc-wrapup
description: /create-clips final phase: check the reports, write the deliverables README, say what is built, what is waiting on CapCut being closed, what failed, and what the user does next. Internal to that command.
user-invocable: false
---

# cc-wrapup

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `T state --run RUN get` (the videos and their status) and every `RUN/60-outputs/<id>/report.md`.

## Steps
1. **Verify**, do not trust: for each `built` video the CapCut project folder named in its report exists, `capcut lint "<draft>"` shows 0 errors, `capcut segments "<draft>" --track video` shows the clip count and the total length the report states (within 0.1 s),
   with the run's captions setting ON (`T state --run RUN get captions` is not `off`) `RUN/60-outputs/<id>/captions.srt` exists and `capcut texts "<draft>"` counts its cues (in the word-box look one CapCut text per word and state: the count equals `RUN/60-outputs/<id>/captions.json -> word_box.texts`, about 2.5 texts per spoken word, minus any text cut at the video's end; `capcut lint` then shows many `caption-too-fast` warnings, which are expected: 0 errors is the bar);
   with captions OFF there is no `captions.srt` and the draft has no caption track (`capcut texts` shows 0), which is right; and the report lists the blurred spans.
   A video that fails a check is reported as it is (not fixed silently); a quick fix you can make (a re-run of `T capcut-finish`, or of `T capcut-build` under a new `--name`) you make. The production agent's `capcut-build` answer (`problems`, `read_back`) is in its report: it is what the agent saw, these checks are yours.
   Game mode also: `T units-table --run RUN` writes `RUN/deliverables/rounds.md` (every round or fight with its keep level and why; the skipped ones listed again so the user can overrule one), and `T units-check --run RUN` must show no unit that a video used with a missing field or an overlap.
2. **Write `RUN/deliverables/README.md`**: the stream (channel, date, length, topic, guests; game mode: the game, the event, the teams, the score of each map; the captions setting, on or off, as the user picked it), then one row per video: id, kind, title, length, CapCut project name, source chunks, status (game mode: also its match and game, the rows grouped by match in the order played, and where the recording holds a match only in part, where it begins or ends); then the lists the user may want to read: every blurred span (video, rec range, what, region), every exclamation or touchy item left in, every context span kept in a long video (video, rec range, what it gives and what needs it), how each streamer-mode long video opens and ends (its rec range, and every border its builder reported as not clean, with where that story starts and ends), every word masked in the captions (the `masked` tally in each video's `captions.json`, as typed, with counts; with captions off: every slur still audible), each video's caption look (the box colour, the size and the agent's reason, whether the house font Luckiest Guy was used (`house_font`) and why not if it was not, or "plain look: <why>", or "captions off"), commercial music noted, videos made from a 720p source (soft in a 9:16 crop), what failed and why (a video its builder judged not worth making is listed as dropped, with its reason), what is `ready-to-build` and needs CapCut closed.
   Add each video's `posting.md` text (title, description, hashtags, chapters) under its row.
3. **Space**: the run's size (`T status --run RUN` and the drive's free space), and the sentence: the chunks stay until the user has exported what they want from CapCut (never deleted by this command).
4. **Tell the user** (a few lines, plain): how many shorts and long videos (streamer mode: with the shorts level the user picked, and why there are fewer shorts than its range when there are), where the README is, that CapCut must be opened once and each project's first frame checked (a `fill` layout and a `fit-blur` background are not verified by any tool here), the export size and fps per kind, what is waiting (`/create-clips <run> resume`), what failed.
5. `T state --run RUN set stage=wrapped`.

## Never
- Never claim a project is good because the agent said so; the checks above are the claim.
- Never delete a chunk, a sheet, a transcript or a CapCut project.
- Never ask a question (the user reads the README).
