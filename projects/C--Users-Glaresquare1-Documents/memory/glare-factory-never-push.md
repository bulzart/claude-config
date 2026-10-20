---
name: glare-factory-never-push
description: "Never push to ~/glare-factory (harperdogpound/ai-video-pipelines) — no push, branch push or PR — unless the user explicitly asks in that moment"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ac68e0f5-a378-44e3-aed7-657a1f5d1e41
  modified: 2026-10-20T20:44:14.564Z
---

Never push anything to `~/glare-factory` (team repo `harperdogpound/ai-video-pipelines`) unless the user explicitly asks for it at that moment. That covers a plain push, pushing a branch and opening a pull request, which needs a push. Pulling updates (`git pull --ff-only`) is fine.

**Why:** user, 2026-10-20: "never push into glare-factory ever without explicitly asking, keep that in mind". It is a shared team repo, reviewed by leads.

**How to apply:** this applies even when the team constitution's chores suggest a PR, or after a local edit there. Ask first, every time; an earlier yes does not carry over. Also written into `~/glare-work/CLAUDE.local.md`, so Glare sessions (which do not load this memory) obey it. Related: [[glare-pipelines-scoped-install]].
