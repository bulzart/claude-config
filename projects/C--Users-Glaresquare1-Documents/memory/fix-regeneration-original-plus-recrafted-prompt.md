---
name: fix-regeneration-original-plus-recrafted-prompt
description: "A fix/correction regeneration sends the ORIGINAL sample video back to Higgsfield with a fully re-crafted prompt; never the flawed take, never a one-frame fix, never an \"edit this / don't do X\" prompt"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ac68e0f5-a378-44e3-aed7-657a1f5d1e41
  modified: 2026-10-20T20:32:25.145Z
---

When a generated video is wrong, the regeneration goes to Higgsfield with **the original sample video** (same input as attempt 1) plus a **newly crafted full prompt**. Never the flawed generated video as input, never a single-frame fix, never an "edit this video" prompt.

The pipeline entities (QC agent, Loupe keeper, request writer) identify what went wrong and craft the prompt so the mistake can't recur. They describe the correct physical action positively, never "do not let the person go through the can". Every prompt piece unrelated to the error stays as it was. Flow: first generation → QC → right: continue; wrong: diagnose → re-crafted request + original → QC again.

**Why:** user correction 2026-10-20, after I wrongly said the original reference never goes back in (I had answered from the Glare recipes, which redo a shot from its stills).

**How to apply:** ATP/AWL already do this: `awl-qc` attempt block → `awl-write-request` full rewrite ("never name a past miss's wrong behaviour") → `awl-inputs` reuses recorded media ids. That the retry reuses the original and not the flawed take is only implied; it is not stated anywhere in the skills (an explicit line was offered 2026-10-20, pending the user's yes). See [[atp-reasoning-over-rule-lists]], [[atp-sample-hints-delicate]].
