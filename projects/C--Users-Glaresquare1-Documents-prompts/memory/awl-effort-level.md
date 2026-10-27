---
name: awl-effort-level
description: "/analyze-with-loupe item 33: five effort levels (low…max = the old settings) scale reference analysis and pacing only; QC and Loupe never change"
metadata:
  type: project
---

On 2026-10-26 and 27 the user asked for a start-of-run effort level to cut token use. It has five steps, low, medium, high, xhigh and max,
where max equals the pipeline's earlier settings. The level adjusts only the reference analysis (fps, the dense rate, motion peaks, close-ups),
the production agents running at once, and the pilot threshold. `T effort` stores it in `state.json → effort`; `T prep-all` and the produce
phase read it. Coverage never drops (every second sampled, cut frames kept), and no frame or video is made smaller.

**Why:** the user first wanted QC scaled too, then ruled that the judges must stay stable ([[judges-stable]]). The QC frame rates, the sample
images and the agent contract were therefore restored exactly. In run `20261021-224049-21`, QC was where most frames were spent, so the
savings come from analysis and pacing.

On 2026-10-28 the user saw only four levels in the start question ("they need to be 5: low,medium,high,xhigh and max"): AskUserQuestion holds
at most four options and its dialog hid XHigh behind Other. The question is now asked in plain chat with all five numbered (effort.md §1,
awl-start 5d), and `T new-run` writes `effort: null` so `T effort` and `T prep-all` stop until the answer is stored (a run without the key
is pre-item-33 and keeps max). The run that "never asked" was an /analyze-then-pick run (that pipeline has no effort level; only
/analyze-with-loupe matters to the user).

**How to apply:** tune cost through the level's analysis and pacing numbers, never through QC. Never offer the levels in a question dialog. Related: [[pipeline-context-budget]], [[awl-voiceover-memes-design]].
