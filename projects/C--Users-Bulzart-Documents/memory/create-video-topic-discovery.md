---
name: create-video-topic-discovery
description: "/create-video topic discovery (briefs of 2026-11-24): subject researched and chosen in the user's scope; no numeric sufficiency threshold, no forced key moment or turning point, a recorded source is not evidence, no word-overlap scope test, each change reaches only what it changes"
metadata:
  node_type: memory
  type: project
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T01:24:57.986Z
---

/create-video picks its subject by research before any approach: `direction.json` → `subject` (manual 02 "Finding the subject", schema in 07, code `subject_issues` and friends in static-studio/scripts/static_core.py). Checkpoints: tags `static-studio-topic-discovery-1` (first build) and `-2` (corrections).

The user's rules from the second brief (2026-11-24), each a correction of my first build:
- **No universal numeric threshold for "enough material".** My first build refused under 90% of the locked length; the user: "Do not replace the percentage with another arbitrary numerical formula." Now: `runtime.progression` (what the viewer newly gets, step by step, on material ids) + the director's `verdict` (sustains/short/uncertain) + why; a short chosen one goes to re-selection or the user's recorded decision (`runtime_decision`, decided_by user). `material_minutes` is a note only.
- **Never force a key moment or turning point.** Key moments only where the video turns or pays off; cumulative value says how it builds (`reward_shape`). The treatment's third sample may be `strongest_moment` instead of `turning_point`.
- **A recorded source is not evidence.** The ledger's `- Access:` (read/indirect/snippet) and claims.json confidence (confirmed/likely/disputed/legend, the scale the Garbo research agent used first) are what the checks read; established material rests on claims with a read source; the choice's `decisive_material` must be confirmed. Credibility itself stays the director's judgement.
- **No word-overlap test for exact topics.** `understood_as` + `boundary` + `how_scope_kept`; for an exact topic/story the blind treatment reader is asked "is it still a video about what was asked" and a partly/no becomes a finding (Q1...).
- **Precise invalidation.** New subject → everything; new angle of the chosen → plan files; a changed value → only the beats carrying it, their lines and shots (`required.parts`); corrected source/claim → re-check where used, recorded with `direction-lock --research-rechecked`; a beat changed after shot-check → only its shots (`shot-check --keep "why"`).

**Why:** the user's priorities are exceptional originality, no boringness, sustained engagement; they want creative judgement carried by reasoning and evidence, "not merely successful validation", and no rebuild when a bounded change is enough.
**How to apply:** when extending topic discovery, add presence/consistency checks only; never a score, quota or threshold; validate with fresh agents researching by the manual alone (exercise outputs kept as test fixtures in static-studio/tests/fixtures/topic-research). Related: [[create-video-significance]], [[create-video-command]], [[scripts-gather-agents-decide]].
