---
name: no-hardcoded-names-in-scripts
description: "Never hardcode niche, category, product or brand names in pipeline scripts or configs; names are data the AI agents collect and decide, and a script that needs one takes it as a parameter"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ff6a4b04-16a6-4927-889e-830c4c6779e4
  modified: 2026-10-11T00:05:49.684Z
---

No niche, category, product or brand names are written into pipeline scripts (Python toolkits, config defaults). The user spotted a hardcoded department list (with "pets", aliases and generic-word rules) in the `/analyze-then-generate` toolkit on 2026-10-11 and rejected it: "the names should not be hardcoded but rather data collected; if python does so at least let it take them as parameters from AI agents, but AI agents doing it would be better".

**Why:** the pipelines are client- and niche-agnostic; the folder and the data decide what a niche is, and judging which labels mean the same thing is the agents' job, not a script's. A hardcoded taxonomy makes the pipeline wrong for every project outside it and hides a judgement inside code.

**How to apply:** when a control needs to compare names (niches, categories, product types), let the AI agents decide the equivalences from the data and record them as run data (the `T niches` vocabulary in `/analyze-then-generate`); the script only enforces consistency with what an agent recorded, refuses an unknown label, and warns about look-alikes. Heuristics in scripts may use only language-level function words, never domain words. Check any new script or config for domain words before finishing. Related: [[atg-pipeline]].
