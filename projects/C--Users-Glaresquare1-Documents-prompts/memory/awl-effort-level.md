---
name: awl-effort-level
description: "/analyze-with-loupe item 33: the user picks one of five effort levels (low, medium, high, xhigh, max = the old rates) that lowers redundant sampling, never coverage or frame-exact checks"
metadata:
  type: project
---

On 2026-10-26 the user said the pipeline burned too many tokens on frames and samples. They asked for an effort level at the start of
every run (or their own fps numbers): on 2026-10-27 they fixed it at five, low, medium, high, xhigh and max, that saves frames without "making it dumb": never skip a second of the
source, never lose data a check needs.

It is item 33 of /analyze-with-loupe. `T effort` stores the level in `state.json → effort`, and `T prep-all` and `T qc --run` read it
themselves. Max equals the rates the pipeline used before (5 fps references, 10 around motion, 30 fps checkpoints, no budgets); a run without the key keeps them. The start question shows all five as a table with four buttons; XHigh goes through Other. The floors and the never-changed list are
in `reference/effort.md` §2: every second is sampled at ≥ 2 fps, cut frames are always kept, and the first second plus every insert, seam
and cut edge are checked on every frame (`@full`).

**Why:** the measured run (`20261021-224049-21`) spent most of its frames on 30 fps QC checkpoint sheets and on 30–49 single
full-resolution frames per QC pass.

**How to apply:** when tuning cost, lower the level's numbers, never the coverage or the `@full` checks. Keep the rules in the sections their
readers already load ([[pipeline-context-budget]]). Related: [[awl-voiceover-memes-design]].
