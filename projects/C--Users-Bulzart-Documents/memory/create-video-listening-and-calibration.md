---
name: create-video-listening-and-calibration
description: "user 2026-11-25, every /create-video run: narrator locked on the user's listening, never on previews, pitch or WPM; first paid recording = smallest representative calibration; planning pace never a target; a length conflict goes to the user"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3cb802e3-203e-41d6-98ff-b19f9a9a5679
  modified: 2026-11-25T14:53:45.019Z
---

The user's brief after tag static-studio-pacing-1 (2026-11-25), for every /create-video run:

- The narrator is never locked from library previews, pitch measurements or an estimated WPM. The shortlist goes to
  the user with its listening files (each preview, plus any real eleven_v4 recording the voice already has, such as
  another film's parts), and `voice-pick` records their listening choice, or their word that the choice is delegated.
- An opening-only first recording is not enough when it has no letters, tags, hard names or pause transitions. The
  first paid recording of a narrator is the smallest representative one. It covers documentary explanation and
  expressive storytelling, the hardest names, tags as written, and a transition into a silence. Part 1 qualifies only
  when it holds all that. Otherwise a `narration-trial` comes first: the voice lock as the one variant
  (`context: neighbours`), questions comparing passages, one take each. It is priced and shown, and runs only on a yes.
- The planning pace (here 163 wpm) is a forecast, never a performance target. When real recordings conflict with the
  locked length, present the evidence and ask for a controlled reapproval. Never force the delivery: no tag or setting
  for pace, no audio edits, no words padded or cut only to fit.
- The plan check also shows what the pacing comparison leaves out: the niche's measured narrators that decision.pacing
  never names, and relevant ones without a measurement. It is advisory: no minimum count, no scoring formula.
- Name density in other languages is deferred until needed. Keep the architecture language-agnostic (a data tuple),
  with no Albanian-specific behaviour for English work.

**Why:** the user wants the voice chosen by ear and tested on what the whole script asks. The old workflow
calibrated on part 1 (the Qin opening has no letters, tags or hard names). Its manual also said "change the words" to
fit the window, which forces the delivery toward the planning pace.

**How to apply:** built 2026-11-25. Code: `pacing_left_out`, `pacing_pool`, and the trial guide for passage-only
questions. Manuals 03/05/07/10 and the command are updated. The Qin run's listening folder is
`C:\Users\Bulzart\.claude\static-studio\runs\20261124-153758-youtube\60-voice\video-01\shortlist-listening\`.
Related: [[create-video-pacing-from-narrators]], [[create-video-narration-direction]],
[[create-video-narration-calibration]], [[create-video-storytelling]].
