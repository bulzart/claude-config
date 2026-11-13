---
name: cs-wrapup
description: /create-static final phase: wrap-up report, the finished CapCut projects, the narration's cost and honesty lines, the feedback question (§6–6b). Internal to that command.
user-invocable: false
---

# cs-wrapup — Wrap-up (§6) and what a Static wrap-up reports (§6b)

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- the run folder, `state.json`, the deliverables and the briefs are the sources
- *CapCut projects still pending (a video whose `result.json` says `capcut_pending` true or blocker `capcut_running`):*
  - production-agents §5: `CS/reference/production-agents/050_5_this-session-as-agents-report.md` (2.3 KB)

## 6. Wrap-up

Report in a short table: video → approach → language → duration → cost → verdict → **CapCut project** (name and full path).
The table names each video's CapCut project:
- First build any projects still pending. If CapCut is running, ask the user once to close it
  (a blocker, not a permission), then build them: by relaunching their agents for the build and the record only (`cs-edit`,
  `cs-record`; `production-agents` §5), or in this session; always by `T capcut-build` (item 39), never clip by clip.
- Then say: "open CapCut → the projects are listed by name → review → Export". Each at its format's export size
  (`state.json → static.format.export`, 30 fps; an extra format's project, named `…-<tag>`, at its own, `static.extra_formats`, one
  table row per format, static §2b); that export is the final. A vertical version longer than 3 minutes is a vertical long video on
  YouTube, not a Short: say so in one line when the run has one.
- What `T capcut-build` read back for each project (the video's brief block S4, `result.json → static.capcut_build`, an extra format's
  in `static.formats`): `ok`, or its `problems` and how each was settled, the seconds; and what no tool here saw (the build's `note`):
  nothing here renders a project, so how CapCut draws the caption look, the box, the entrance, the moves, the joins and the drawings
  is the user's first look. Tell the user what to do in CapCut: open the project, look at the first frame, a move, a join and a
  caption, then export.
Then give:
- the cost and the narration's facts (§6b below): the OpenAI estimate, the narration's ElevenLabs characters and the account's
  characters left;
- the run folder (keep it: the CapCut projects use its files);
- the examples used ("6 examples → house approach applied") or "no examples";
- the guardrails applied ("G1–G5 from brand-rules.pdf; 2 references dismissed: V04 (G1, the gore
  is the prank), V09 (G3, a taste test); 3 picks edited: counts, de-branding, face swaps") or
  "no guardrails supplied";
- the QC fixes (item 27): "N videos fixed after QC, M fixes you declined (kept as generated, flagged: V03 …)", or "no QC finding needed a fix";
  with QC fixes `off`: "QC was off: every video was generated once and delivered unchecked; tell me what to fix" (the feedback question below collects it);
- any open issues.

Check the briefs before the feedback question. Every `result.json` whose `qc` says
RESIDUAL FAILURE or regenerated has an attempt block in its video's brief, so no flagged delivery leaves
the run unexplained.

Before the table, check the run's deliverables and text. Every video in `state.json` →
`videos[]` has its CapCut project, by name and full path (`capcut_project`, `capcut_project_path`), its title and thumbnail in
`<RUN>/deliverables/` (all videos in that one folder), and no video file there (static §7), and a row in `deliverables/README.md`;
the plan and brief files carry every attempt; and no CapCut text layer of any project contains an emoji (the user's rule, strict).
What is missing is fixed before the table is shown.

Offer, in one line, the next useful step (more videos, a different direction, redraw the stills of a flagged video).
Static (static §10, §12): the table also names each video's YouTube title and its thumbnail (full paths:
`deliverables/video-NN-title.txt`, `deliverables/video-NN-thumbnail.png`), each with its approach (story form, point of view, time frame,
title form) and its language, and the offer names the two ways on: more videos of this channel's niche (`/create-static more <RUN>`:
the language of each new video is asked, and the subjects come with their approaches) or a clone of the analysis for another niche
(`/create-static clone <RUN>`: the niche, the narration model and the language are asked again). With QC fixes `off` (item 27) the feedback question is the review: say first, in one line, that no video was checked. Then, once every video is delivered, **ask for feedback** with AskUserQuestion (header
"Feedback"), "Watch the videos: is any of them not right?": **"All good"**; **"I'll watch them
later"** (any later message about them is handled as item 22 says); **"Some need fixes"** → ask in plain
chat which video and what is wrong, disliked or illogical. "Other" lets the user type it
directly. Each problem named, now or in a later session, is handled as item 22 says: their words verbatim
and the diagnosis go into the video's brief before the fix is offered. When a problem is a kind the
references do not hold, add one line offering to write the rule into the section that owns it.

### 6b. What a Static wrap-up reports (item 36)

A Static wrap-up reports the OpenAI cost estimate (the sum of
the videos' `result.json → static.cost_usd_estimate`; 0 when FLUX 3 Klein made them on this PC), the images' source and re-draws, the
narration's ElevenLabs characters (each `30-assets/narration/video-NN.json → characters`, at the run's model's credits per character, one
on Eleven v4, and the account's characters left by `T tts check`), a partial narration with the line it stops at, and every narration
passage made again. For each video in another language, or the first in a language of the run: its language, unit and narration model,
and **"pronunciation: not checked, listen"** whenever the language is outside the model's own list (`official` false) or is the run's
first video in it (static §8: nothing here hears the voice); the captions' look (the word box placed, or the plain look and why, static
§7), any font replaced for missing glyphs, and that how CapCut shapes a right-to-left or joined script was not seen. Each video's drawings
(how many, which images, what each elaborates) and that how CapCut plays their clips was read back from the project but not seen
rendered (nothing here renders a project).
It also gives each narration's pace against its point (static §6, §13 "After the narration": the measured words a minute while speaking and overall, the
point, the niche's and the family's numbers beside it) and, when the request levers left it off the point, the speed-up that would close
it (at most `config static.narration.tempo_max`, 1.05). The user looks at the project in CapCut first; the speed-up is asked with
AskUserQuestion (header "Speed-up") and made only on their yes (the user, 2026-11-09: "only speedup on their permission never else"):
`T tts tempo … --user-ok "<their words>"`, then `T narration-words`, `T slideshow plan`, the bed's length (`music.json`, `T music make`
again when it no longer covers the narration) and a new CapCut project (`T capcut-build` under a new `--name`, item 39: the delivered
project stays as it is), reported as a new build.

**The narration's credits, licence and honesty** (the lines of the narration's own credits rules that apply here):
- Every ElevenLabs call spends the user's credits: about one credit per character of the text as sent, tags included, on Eleven v4
  (measured 2026-10-26: 242 credits for a 240-character script), the run's model's credits per character otherwise. The wrap-up
  states the voice, the language, the narration model, the passages made again, the characters used and the characters left (`T tts
  check` now).
- The free plan carries no commercial licence: a video voiced on it is not posted until the account is on a paid plan; the wrap-up says
  so when the account's plan (`T tts check` → `subscription.tier`) is `free`.
- Never claim that a narration was listened to, or that its pronunciation, accent or dialect is right.

## Rules this phase owns (contract items 22, 38)

22. **No error ledger: the rules live in the pipeline.** Every lesson learned from a video that went wrong
    (the user's reports, the agents' regenerate reasons) is written, generalised, in the section that owns
    it (`reference/`): as a kind (what to achieve, what to avoid) with the miss, its
    cause, the corrected wording and what worked as the sample beside it. There is no `caught_errors.md`,
    no `T caught-error`, no per-run digest of past errors, and nothing in a run reads an error file: the
    plan, the prompt and QC follow the references. The only error text a run writes is a video's own
    attempt block in its brief and `result.json`; no later run
    reads any of it. `CE-nnn` in the references are case labels of
    those lessons. **When a delivered video is wrong**, in the run or in a later session:
    take the user's words verbatim, diagnose them in pipeline terms (the stage that made the miss and the
    stage that should have caught it), say which section already holds the rule and why it did not
    prevent this video, and offer the fix (a new edit, a redrawn still or a narration passage made again: `cs-feedback`); when the
    miss is a kind the references do not hold, say so in one line and offer to write the rule, generalised
    (what to achieve, what to avoid, the miss and its cause, the corrected wording), into the section that
    owns it; write it only on the user's yes. A user's word outranks the agents' QC on the same point: the user saw what QC passed. **The
    agents** write a regenerate reason or a flagged delivery in the video's brief (an attempt block with the
    failed request, the verdict and what changed) and in `result.json` (`production-agents` §3
    item 12); nothing else is written to the library.
38. **The to-do is checked at the close** (the user, 2026-11-13): before the report, read `RUN/todo.md` and every video's `todo.md` (item 38): each item is `[x]`, or `[-]` with its reason, or named in the
    report as open, so nothing that was planned is silently missing; then set the run's `Next:` line to what the user decides (the feedback question, an open choice) or to "done".

## Never (this phase)

- Never make the speed-up without the user's yes after they have looked at the project (the user, 2026-11-09: "only speedup on their
  permission never else"), and never edit a finished CapCut project: a change after the user looked is a new build under a new
  `--name` (item 39).
- Never create or read an error ledger (item 22): a video the user reports as wrong is diagnosed with their
  words verbatim, in its brief, and fixed only after the diagnosis.
- Never close a run with a RESIDUAL FAILURE or a regenerated video that has no attempt block in its
  brief (A10, §6). Never copy an agent contract from an earlier run: it is generated at A9s by `T contract`
  from `production-agents` §2s.

## Hand-off

`T state --run RUN set stage=done`. A video the user later reports as wrong: invoke Skill `cs-feedback`.
