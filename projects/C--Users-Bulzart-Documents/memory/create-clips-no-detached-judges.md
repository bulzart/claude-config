---
name: create-clips-no-detached-judges
description: "user 2026-11-21: /create-clips never launches blind, contextless or pairwise judges, second planners or compare-builds"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T00:41:43.739Z
---

The user, 2026-11-21: "Remove the standalone blind-judge mechanism ... Do not make it optional. Do not introduce the same mechanism under a new name."
Router rule 2 and the global Never list of `commands/create-clips.md` now say it. The live workflow never had one; blind judges and pairwise viewers
existed only in the interrupted long-form experiment (`Documents\stream-clips\validation\longform-20261120\evidence\`), kept as evidence only.

**Why:** the 2026-11-20 experiment spent ~2.5 h on judges, baseline-vs-improved builds and a whole-stream second look (415k tokens, 22 min, two weak
finds, no plan change).

**How to apply:** checks are made by the agent that holds the context (planner's check, builder's one paper read, the selective second look) plus
deterministic validators (`edl-check`, read-back, `export-check`). Never propose a judge, a comparison build or an alternative-EDL loop as a fix.
Related: [[create-clips-second-look]], [[create-clips-pipeline]].
