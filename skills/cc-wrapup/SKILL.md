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
   `RUN/60-outputs/<id>/captions.srt` exists (captions are non-negotiable), and the report lists the blurred spans.
   A video that fails a check is reported as it is (not fixed silently); a quick fix you can make (a re-run of `T capcut-finish`) you make.
   Game mode also: `T units-table --run RUN` writes `RUN/deliverables/rounds.md` (every round or fight with its keep level and why; the skipped ones listed again so the user can overrule one), and `T units-check --run RUN` must show no unit that a video used with a missing field or an overlap.
2. **Write `RUN/deliverables/README.md`**: the stream (channel, date, length, topic, guests; game mode: the game, the event, the teams, the score of each map), then one row per video: id, kind, title, length, CapCut project name, source chunks, status; then the lists the user may want to read: every blurred span (video, rec range, what, region), every exclamation or touchy item left in, every slur masked, commercial music noted, videos made from a 720p source (soft in a 9:16 crop), what failed and why, what is `ready-to-build` and needs CapCut closed.
   Add each video's `posting.md` text (title, description, hashtags, chapters) under its row.
3. **Space**: the run's size (`T status --run RUN` and the drive's free space), and the sentence: the chunks stay until the user has exported what they want from CapCut (never deleted by this command).
4. **Tell the user** (a few lines, plain): how many shorts and long videos, where the README is, that CapCut must be opened once and each project's first frame checked (a `fill` layout and a `fit-blur` background are not verified by any tool here), the export size and fps per kind, what is waiting (`/create-clips <run> resume`), what failed.
5. `T state --run RUN set stage=wrapped`.

## Never
- Never claim a project is good because the agent said so; the checks above are the claim.
- Never delete a chunk, a sheet, a transcript or a CapCut project.
- Never ask a question (the user reads the README).
