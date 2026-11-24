---
name: create-video-niche-discovery
description: "user 2026-11-24 brief (mandatory): /create-video splits reference analysis by reading work (analysis-plan), discovers niches from finished cards (niche-evidence -> niche-map.json -> niche-check), locks the user's pick (niche-lock) before length; batches never imply niches"
metadata:
  node_type: memory
  type: project
  originSessionId: 3cb802e3-203e-41d6-98ff-b19f9a9a5679
  modified: 2026-11-24T18:30:32.564Z
---

User brief 2026-11-24, "Mandatory Implementation - Correct Dynamic Niche Discovery in the Reusable /create-video
Workflow". Cause found: in run 20261124-153758-youtube I made five analysis batches myself from video titles
(history, origins, money, survival+fitness, psychology+fitness); the six niches I then presented followed those batches
(four niches = one batch each, a fifth 6/7, the sixth = the fitness fillers). 17 cards also compared a reference with
"my group"; my brief had asked agents what their group shared. And the code tied the niche to the length cohort
(`length` set selected_niche from a card label or `__cohort__:` id).

**Built (static_core + manuals 01/02/03/07/10 + command + template, tag static-studio-niche-discovery-1):**
- `analysis-plan --run [--agents N] [--ids|--all] [--dry-run] [--replace-why]`: batches by reading work only
  (watch + shot sheets, transcript words, closer-look candidates, per-reference overhead; LPT split), agent count from
  config `analysis_batching` (budget 260, max 5) or --agents; writes 20-analysis/agents/plan-r<n>.json + one brief per
  agent from reference/templates/analysis-agent-brief.md (no group talk, no batch comparisons, no cohort_id) + to-do.
- `niche-evidence`: every reference in ID order, each dimension apart (subject, format, viewer reward, look, narration,
  runtime/pace, content), no batch/cohort shown; pure function of the cards (byte-identical whatever the plans).
- 20-analysis/niche-map.json (director): any number of niches, members core/overlap with why, formats inside a niche,
  comparable_cohorts with why_comparable, timed evidence, outliers, shared_across_niches (a shared format is not a niche).
- `niche-check`: form + traceability only (coverage, reasons, members-only cohorts/formats, evidence current); facts
  incl. cohort Standard + whether length would refuse, batches_per_niche; WARNS (never refuses) when a niche is exactly
  one batch / all from one, a cohort gives no Standard, evidence incomplete.
- `niche-lock --niche --user-words [--decided-by director --why] [--refresh --why]`: one niche per run; length,
  niche_family_refs (direction evidence family = members, any format) and locked_niche_names (subject.scope.niche) read it.
- Runs made by init/clone now carry state `niche_discovery: niche-map-v1` and `length` refuses before niche-lock;
  older runs (no marker) keep the label/cohort path (Garbo verified identical old vs new code, 1,305 files unchanged).

**How to apply:** never group references before analysis; never let the agent count shape niches; when presenting
niches, read niche-check facts and warnings. Scripts gather, the director decides ([[scripts-gather-agents-decide]]).
Verification 2026-11-24: 288 tests; two real collections mapped blind by fresh agents (4 niches + 1 outlier vs 3
niches), replayed as tests/fixtures/niche-discovery; evidence in Documents/create-video-dev/verification/2026-11-24-niche-discovery.
Related: [[create-video-command]], [[create-video-topic-discovery]], [[create-video-adaptive-niche-guardrail]].
