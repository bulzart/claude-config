---
name: cs-feedback
description: /create-static: a delivered video reported as wrong: diagnose in pipeline terms and offer the fix (item 22). Internal to that command.
user-invocable: false
---

# cs-feedback — A delivered video reported as wrong (item 22)

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- nothing up front: read the run's brief, plan files, image requests and `result.json` named below, and only the one reference section that owns the rule

## Feedback first

   If `$ARGUMENTS` or the opening message reports a delivered video as wrong
   (it names a video, a CapCut project or a run and says what was not right), handle it before
   anything else (item 22): find the run among the run folders `CS/runs/<stamp>-<slug>/` by the video's CapCut project name or date
   (`DD_Mon_YYYY_vNN`, `-<tag>` for an extra format: it is in the run's `deliverables/README.md` and in
   `60-outputs/video-NN/result.json`) and read its brief, its plan files and its QC verdict
   (`40-briefs/video-NN-brief.md`, `video-NN-script.md`, `video-NN-narration.json`, `video-NN-images.json`, `video-NN-timeline.json`;
   `50-requests/video-NN-iKK-aM-image-request.json`; `60-outputs/video-NN/result.json`); when the run cannot be found, ask the user once for the brief or
   the run folder. Say in two lines which stage made the miss and which reference section holds the
   rule, then offer the fix in one line (the fix paths below, with what it costs: the OpenAI estimate for stills drawn again, the
   ElevenLabs characters for passages made again; nothing for an edit, for FLUX 3 Klein or for a drawing), and
   continue only if the user wants it.

   **A Static video's miss is one of these** (the user's words say which; the stage is the one that made it, the section the one that
   owns the rule, the fix the path through the phases that follows):
   - **A picture** (a face, hands, a count, the style, a made-up subtitle-like line, a logo, a person's likeness, something indecent
     or religious, the frame): S3, `cs-images`; static §5 and §8 (§11, §11b; `anomaly-catalog` §2.17 identity, §2.13 stylised pictures).
     Fix: that image drawn again with its prompt changed by the diagnosis (`cs-images` step 3: `--again` only when nothing but the draw
     changes; with images by the user, they send a corrected file and `T image intake` takes it in), then `cs-edit`, `cs-record`.
   - **The narration** (a word said wrong, a missing or repeated word, the pace, the accent or dialect, the register, a tag spoken): S2,
     `cs-sound`; static §6 and §8. No agent listens, so the pronunciation is the gap the wrap-up named ("not checked, listen"): the
     user's ear is the check. Fix: the passage made again through the request with the user's correction (the word respelled the way
     it is said, a delivery tag or the words changed; `T tts say --only N`, billed in characters; never another voice in this run, static
     §10), never an edit of the delivered audio (the user, 2026-11-09); a speed-up only on the user's yes (static §6); then
     `T narration-words`, the spans, the bed's length, `cs-edit`, `cs-record`.
   - **The bed** (a voice heard in it, a narration word lost under it, a level that fights the story's beats): S2, `cs-sound` step 5;
     static §6 and §8. Fix: a new take (another `seed` or a reworded `caption`) or another level (`--gain`), then `cs-edit`, `cs-record`.
   - **The captions** (a word, a timing, the look, the box's colour, a glyph missing): the words are the narration's (S2,
     `T narration-words`), the look is the plan's and the run's (static §5, §7, §10), the project carries what the plan decided. Fix: the
     words by the passage (above) or the look by the plan's `captions`, then `cs-edit`, `cs-record`.
   - **A move, a join, an effect, a label, a drawing** (its look, its place, its moment): decided in the image plan from the references'
     measured pattern (static §5, §2; no stock value) and built by `T capcut-build` (static §7, §8). Fix: the value decided again in
     the plan, a drawing's spec drawn again (`cs-images` step 5d, `T draw render`), `T slideshow plan` and a new build in `cs-edit`.
   - **The title, the thumbnail, the description or the chapters**: A6s's plan, S3's thumbnail and X10's files; static §12. Fix: the
     thumbnail drawn again (`cs-images` step 6) or the plan's words changed, then `cs-record`; no new project.
   - **The CapCut project itself** (a clip, a gap, a join or a sound that is not the timeline's, a font back at CapCut's default): S4,
     `cs-edit`; the build's `problems` and `read_back` (static §7, §8; `CS/reference/capcut-build.md`). Fix: the cause in the plan or the
     files, then a new `T capcut-build` under a new `--name` (item 39). The delivered project stays untouched and is named in the
     brief as replaced; the user keeps or deletes it. CapCut must be closed for the build (ask once).
   - **What only CapCut's playing shows** (how it draws the box, the entrance, a join, a drawing over its picture, a right-to-left or
     joined script): no tool here saw it (the wrap-up said so). Say what the project's facts show and what they cannot, and offer the
     plan value that would change it.
   With QC fixes `off` (item 27) no check ran: say so in the diagnosis. A user's word outranks the agents' QC on the same point.

## Rules this phase owns (contract items 22)

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
    prevent this video, and offer the fix (a new edit, a redrawn still or a narration passage made again, the paths above); when the
    miss is a kind the references do not hold, say so in one line and offer to write the rule, generalised
    (what to achieve, what to avoid, the miss and its cause, the corrected wording), into the section that
    owns it; write it only on the user's yes. A user's word outranks the agents' QC on the same point: the user saw what QC passed. **The
    agents** write a regenerate reason or a flagged delivery in the video's brief (an attempt block with the
    failed request, the verdict and what changed) and in `result.json` (`production-agents` §3
    item 12); nothing else is written to the library.

## Never (this phase)

- Never create or read an error ledger (item 22): a video the user reports as wrong is diagnosed with their
  words verbatim, in its brief, and fixed only after the diagnosis.
- Never edit, repair or delete a CapCut project the user already has: a repair after a complaint is a new `T capcut-build` under a new
  `--name` (item 39), and never the CapCut MCP tools, `capcut lint --fix` or a save with force.
- Never edit the delivered narration (the user, 2026-11-09): a passage is made again through the request; a speed-up only on the
  user's yes.

## Hand-off

Continue only if the user wants the fix (a new edit, a redrawn still or a narration passage made again): re-enter the video's loop at the owning skill with the diagnosis (`cs-images` for a picture, a drawing or the thumbnail; `cs-sound` for the narration or the bed), then `cs-edit` (a new project under a new `--name`) and `cs-record`; for a plan value or the project alone, `cs-edit`, then `cs-record`; a title, description or the record alone, `cs-record`. The attempt goes in the video's brief (block per attempt: the user's words, the diagnosis, what changed) and in `result.json`, and the new project is reported as a new build with its name and full path. A miss that is a kind the references do not hold: offer to write the rule into the section that owns it (on the user's yes). While a fix is open, `T state --run RUN set next_skill=cs-feedback` (after a compaction or on `resume`, the command sends the session to `state.json → next_skill`); when it is recorded, `T state --run RUN set stage=done`.
