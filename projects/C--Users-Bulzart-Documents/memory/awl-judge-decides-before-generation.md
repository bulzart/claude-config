---
name: awl-judge-decides-before-generation
description: "user 2026-11-08: a judge agent forecasts and decides every generation (speech, image, music) before it runs, from the references' data; every value aimed at a decided point, never 'landed somewhere in the band'"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-08T20:44:16.301Z
---

User 2026-11-08, after video 03's narration landed at 209 words a minute in a 178-212 band by chance: "no need to ask me for my call, just make a smart judge system who can do things on its own who decides what to do when this happens or similar cases, who is given enough brief and information and it evaluates the situation and decides way before generation happens and the generation is done whether image,speech or music is done so we just make the most quality outputs and not unexpected things turn out after the work is done ... all without drifting from the mined and collected data patterns and analysis from the references". Then: "the problem was with this word "We didn't aim for 209.", because every step should be taken carefully and thoroghfully, and nothing should turn out as unexpected".

**Why:** a result that falls anywhere inside a band by chance is an unplanned outcome; the user wants each value aimed at a point the data justifies, and each risk predicted and designed out before a model runs.

**How to apply:** /analyze-with-loupe Static: the judge (contract item 37, static §13: J1 before any generation, J2 after the narration, J3 between image stretches, J4 before the bed, J5 before the edit) runs `T static forecast` and decides on its own; every number gets a target point (the family's medians unless the data gives a reason) and a tolerance; never ask the user these calls, report the decisions afterwards; never explain a result as "not aimed". Its memory forecast is a fact, never a gate (static §13 "Memory is a fact", 2026-11-08): every still, narration and bed is tried, and only a real guard stop makes a job wait or a bed go without, named. Related: [[awl-tts-normal-model-only]], [[awl-never-ask-decide-autonomously]], [[awl-static-whole-set-and-pace]], [[analyze-with-loupe-command]], [[scripts-gather-agents-decide]].
