---
name: pipeline-context-budget
description: "When changing /analyze-with-loupe, keep the always-loaded text (router, skills, agent contract) lean: no context rot in the pipeline's agents"
metadata:
  node_type: memory
  type: feedback
  originSessionId: c1639feb-dd77-47ca-950d-178277c7920f
  modified: 2026-10-26T01:52:11.000Z
---

When adding a feature to /analyze-with-loupe, put its details in a reference section that a skill's Read-now list loads only under a condition. The router, the always-loaded skills and the agent contract get a pointer of one or two lines. Toolkit commands print a summary and keep long lists in their JSON files.

**Why:** on 2026-10-26 the user asked to "make sure to avoid causing any memory context rot in pipeline agents". The first version of the voiceover feature had added about 11 KB to every production agent, even in runs without a voiceover. After trimming, the addition was about 4.7 KB.

**How to apply:** measure the growth against the commit before the change. `~/.claude` is a git repo with auto-commits, so compare against `git show <base>:<file>`. Report the per-agent and main-session deltas. Never paste the same rule into several always-loaded files. Related: [[awl-voiceover-memes-design]].
