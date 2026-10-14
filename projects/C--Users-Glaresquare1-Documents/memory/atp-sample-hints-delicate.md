---
name: atp-sample-hints-delicate
description: "Loupe's miss samples also guide the FIRST request of each video (atp.py plan-hints at X2), but delicately: sparse text-only hints, positive levers, never prompt text, max two applied (user 2026-10-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-14T22:30:00.000Z
---

On 2026-10-14 the user asked that the agent crafting a video's FIRST prompt can see the miss/right samples, so it knows what could go wrong, but "in a smart way, a bit delicate": agents sometimes focus on avoiding or implying patterns from wrong/right samples and cause unnecessary distortions and inaccurate logic in the video about to be generated, and context rot must be avoided as everywhere else.

**What was built:** `atp.py plan-hints --run RUN --video NN --beats "<one line per beat>" --product …` (called once at X2 in `atp-write-request`, first request only; a regeneration works from its diagnosed cause). The same Loupe keeper ([[loupe-web-app]]) answers in a planning mode: default no hints, at most 3, a hint needs a beat of the plan that matches the sample's trigger + a compatible model (code drops other model families unless model-independent, low confidence, unknown ids), text only (no images), each hint = trigger, right_outcome (positive), lever (which of the writer's own tools at which beat), caveat. Keeper unavailable or library empty = no hints (a raw match list would over-steer). Real-keeper test: sparse and correct (capsule plan → the count hint; unrelated plan → none; other-model sample held back).

**Writer rules (atp-write-request, checked at X4, recorded in the brief):** a hint is a risk to check the plan against, never prompt text; never copy its words or name the wrong behaviour in the prompt (a named thing, even in a negative, comes back: generation-system §4, §5c.2b); apply only to the matching beat, smallest change inside the existing prompting stack (anomaly-catalog §3), positive wording; at most two per video; a hint that would reshape more than one clause is dropped; applying nothing is right when the plan already holds; the decisions go in a "Sample hints" block of the pattern card → the brief.

**Why / how to apply:** over-correction from old misses is itself a failure mode. Keep any change to this feature sparse, positive and text-only; never let agents read the library or sample images at planning time; update `Documents/prompts/loupe.txt` and the ATP build prompt with any change.
