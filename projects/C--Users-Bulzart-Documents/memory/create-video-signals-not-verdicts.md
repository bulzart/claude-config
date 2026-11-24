---
name: create-video-signals-not-verdicts
description: "user 2026-11-24 - /create-video: numbers and word lists are evidence for reasoning, never verdicts (style identity, people in context, semantic re-reads, pace vs natural variation, grouped comprehension, no blanket exclusions)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T11:57:55.957Z
---

In /create-video, no fixed number or keyword list decides a creative or content question on its own. Measured values
and word matches are signals that trigger reasoning (the agent's, recorded) and the existing review mechanisms:
- Style: the locked look is an identity, not identical wording. Shot-specific light, framing, atmosphere, rendering
  are allowed with a reason; only what the director named as another look (departs_when) needs a relock or a stated
  departure. Never a fixed limit like "one extra phrase".
- People in pictures: never refused or allowed by an ambiguous word alone (a lighthouse silhouette is not a person);
  real human figures must not slip through euphemisms. Decide by looking at the still (people question in its look)
  and by accepting a specific caption with a reason; an added child is never accepted.
- Cold-reader re-reads: by what a revision touches (key moment, its setup/hedge, researched value, claim,
  comprehension gap), not by a percentage of words. Majors always get renewed scrutiny; unchanged material no re-read.
- Pace: compare against the narrator's own norm and natural variation, the beat's intent, density, references.
  Crossing a threshold means "examine", never "wrong". Intentional fast/slow passages stay.
- Comprehension: related signals (shared name or beat) may share one answer; never a blanket line over unrelated ones.
- Content: no new blanket exclusions because a keyword category exists (drug words were NOT added); keep the
  established rules and tell genuine concerns from harmless wording.
- GPU waits: no universal timeout; follow who holds the card, the operation and recovery.

**Why:** the user's brief of 2026-11-24 ("Do not replace one rigid keyword rule with another"; "The 8% and 12% ... are
implementation choices, not universal creative rules"). Extends [[reasoning-over-rule-lists]] (ATP) and
[[scripts-gather-agents-decide]] to /create-video; code enforces process, never quality ([[create-video-adaptive-niche-guardrail]]).

**How to apply:** when adding a check, make the code gather evidence and require an accountable answer (note, look,
acceptance with reason) instead of a hard threshold; keep safety, money, asset-integrity and release checks strict.
