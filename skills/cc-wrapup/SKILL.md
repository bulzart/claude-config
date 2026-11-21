---
name: cc-wrapup
description: /create-clips final phase: check the reports, write the deliverables README, say what is built, what is waiting on CapCut being closed, what failed, and what the user does next. Internal to that command.
user-invocable: false
---

# cc-wrapup

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `T state --run RUN get` (the videos and their status) and every `RUN/60-outputs/<id>/report.md`; for the close also `RUN/todo.md` and every `RUN/60-outputs/<id>/todo.md` (router rule 16).

## Steps
1. **Verify**, do not trust: for each `built` video the CapCut project folder named in its report exists, `capcut lint "<draft>"` shows 0 errors, `capcut segments "<draft>" --track video` shows the clip count and the total length the report states (within 0.1 s),
   with the run's captions setting ON (`T state --run RUN get captions` is not `off`: `on` with `caption_style` `luckiest-guy` (the box look) or `montserrat-highlight` (the highlight look), or on an older run `on`/`box` (the box look) or `no-box`) `RUN/60-outputs/<id>/captions.srt` exists, `captions.json -> look` is the run's look in every video, and `capcut texts "<draft>"` counts its cues (in the box look one CapCut text per word and state: the count equals `RUN/60-outputs/<id>/captions.json -> word_box.texts`, about 2.5 texts per spoken word, minus any text cut at the video's end; `capcut lint` then shows many `caption-too-fast` warnings, which are expected: 0 errors is the bar; in the highlight look one CapCut text per moment: the count equals `captions.json -> word_highlight.texts`, and the build's `read_back.caption_highlight` shows every text Montserrat Bold, outlined, white with at most one yellow word (`bad` empty); in the no-box look one text per caption: the count equals `captions.json -> lines.texts`);
   with captions OFF there is no `captions.srt` and the draft has no caption track (`capcut texts` shows 0), which is right; and the report lists the blurred spans.
   A video that fails a check is reported as it is (not fixed silently); a quick fix you can make (a re-run of `T capcut-finish`, or of `T capcut-build` under a new `--name`) you make. The production agent's `capcut-build` answer (`problems`, `read_back`) is in its report: it is what the agent saw, these checks are yours.
   Game mode also: `T units-table --run RUN` writes `RUN/deliverables/rounds.md` (every round or fight with its keep level and why; the skipped ones listed again so the user can overrule one), and `T units-check --run RUN` must show no unit that a video used with a missing field or an overlap.
1b. **Export** (router rule 19; the user, 2026-11-21: finished means an exported, verified MP4). It takes the screen, so only with the user's yes in
   this run (asked once at the start of the export, never per video). One export at a time: `T gpu --take capcut-export --by <this session> --ttl-s 3600`
   first (refused = another session exports: wait for it; music separation waits for this lease). Agents still building other videos are fine, but a
   `capcut-build` needs CapCut closed: export when the builds that are running have saved.
   - Desktop control: the computer-use tools when this session has them (`mcp__computer-use__*`, through their access flow); otherwise the toolkit's
     own commands, as on 2026-11-20: `T desk shot --out <png> [--region x,y,w,h] [--scale 0.5]` (then Read the picture), `T desk click --x --y
     [--double]`, `T desk key --keys ctrl+a`, `T desk type --text "..."`, `T desk windows`. Look at a screenshot after every action before the next;
     never click from memory.
   - `T capcut-app export-path --set "RUN\deliverables"` (the user's own folder is kept and put back), `T capcut-app start`.
   - For each `built` video, in the run's order: click its project tile (the name in its report) on the home page; in the editor check the timeline
     length against the report; Export (the button at the top right) opens the dialog: the name field gets `T deliver-name --title "<the YouTube title
     from posting.md>"`'s file name (select it all, type), the resolution its canvas (shorts 1080x1920, long videos 1920x1080), 30 fps; Export;
     wait, with a screenshot every 10-30 s, until the done dialog; close it; Menu > Back to home page. Then
     `T export-check --run RUN --video <id> --file "<RUN\deliverables\name.mp4>" --title "<the title>" --set-state` and look at the frames it lists
     (captions, blur, removed music). A failed check is `attention`, never silently `verified`.
   - `T capcut-app quit` (CapCut's own close, never a kill), `T capcut-app export-path --restore`, `T gpu --release capcut-export`.
   - A dialog that is not in this procedure (an update offer, a sign-in, a crash notice): close it when that is safe, else stop, leave the video
     `built` and say what the screen showed. Without the user's yes or without any desktop control: say so in one line; the projects are ready, the
     export is the user's step, and `T export-check` checks a file they export. Never upload anything.
2. **Write `RUN/deliverables/README.md`**: the stream (channel, date, length, topic, guests; game mode: the game, the event, the teams, the score of each map; the captions setting as the user picked it: Luckiest Guy word box, Montserrat Bold word highlight, no-box (an older run) or off), then one row per video: id, kind, title, length (a streamer-mode long video also its planned source time and how much of it plays, from its report's paper-edit totals), CapCut project name, source chunks, status (game mode: also its match and game, the rows grouped by match in the order played, and where the recording holds a match only in part, where it begins or ends); then the lists the user may want to read: every blurred span (video, rec range, what, region), every exclamation or touchy item left in, every context span kept in a long video (video, rec range, what it gives and what needs it), how each streamer-mode long video opens and ends (its rec range, and every border its builder reported as not clean, with where that story starts and ends), every word masked in the captions (the `masked` tally in each video's `captions.json`, as typed, with counts; with captions off: every slur still audible), each video's caption look (box look: the box colour, the size and the agent's reason, whether its font Luckiest Guy was used (`house_font`) and why not if it was not, or "plain look: <why>"; highlight look: the size and whether its font Montserrat Bold was used (`house_font`); no-box look: the size and whether its font Montserrat Bold was used (`house_font`) and why not; or "captions off"; and the spelling fixes held for review or refused, from each video's `captions.json -> lexicon`), commercial music noted, videos made from a 720p source (soft in a 9:16 crop), what failed and why (a video its builder judged not worth making is listed as dropped, with its reason), what is `ready-to-build` and needs CapCut closed.
   Add each video's `posting.md` text (title, description, hashtags, chapters) under its row, and its music lines from `RUN/60-outputs/<id>/music.json` (removed, listen before publishing, or not identified and left as it is: never "safe"), and its export (the MP4's full path and its check) or "not exported yet".
3. **Space**: the run's size (`T status --run RUN` and the drive's free space), and the sentence: the chunks stay until the user has exported what they want from CapCut (never deleted by this command).
4. **The to-do is checked at the close** (router rule 16, the user, 2026-11-13): before the report, read `RUN/todo.md` and every video's `todo.md`: each item is `[x]`, or `[-]` with its reason, or named in the report as open, so nothing that was planned is silently missing; then set the run's `Next:` line to what the user does next (`/create-clips <run> resume` when a project waits on CapCut) or to "done".
5. **Tell the user** (a few lines, plain; `T timings --run RUN` gives where the run's time went and when the first and last videos were built): how many shorts and long videos (streamer mode: with the shorts level the user picked, and why there are fewer shorts than its range when there are), where the README is, that CapCut must be opened once and each project's first frame checked (a `fill` layout and a `fit-blur` background are not verified by any tool here), the export size and fps per kind, what is waiting (`/create-clips <run> resume`), what failed.
6. `T state --run RUN set stage=wrapped`.

## Never
- Never claim a project is good because the agent said so; the checks above are the claim.
- Never delete a chunk, a sheet, a transcript or a CapCut project.
- Never ask a question (the user reads the README).
