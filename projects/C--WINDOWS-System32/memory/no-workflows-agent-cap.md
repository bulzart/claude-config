---
name: no-workflows-agent-cap
description: "User's video-tooling commands must stay normal slash commands — never Claude Code Workflows — and use at most 3 agents"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 35f8a02c-f911-4a16-92ee-15e5442237e2
  modified: 2026-09-30T22:02:35.242Z
---

Build and run the user's video tooling (e.g. /analyze-then-pick, /analyze-stack) as normal Claude Code slash commands. Never create, trigger, convert to, or delegate to a Claude Code Workflow. Keep agent usage minimal: prefer 0–1, use 2 when useful, and never exceed 3 per run, with no overlapping responsibilities.

**Why:** the user stated this explicitly and repeatedly (analyze-stack "owner decision" 2026-09-17/19; /analyze-then-pick request 2026-09-30).

**How to apply:**
- Command files use `disallowed-tools: [Workflow]`.
- Parallel work goes through at most 3 Agent-tool agents, each with a disjoint scope.
- Higgsfield's server-side "workflow" recipes are only documentation, not Claude Code Workflows.

Related: [[analyze-then-pick-system]]
