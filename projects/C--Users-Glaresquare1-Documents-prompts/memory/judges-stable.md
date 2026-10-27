---
name: judges-stable
description: "Never change Loupe or the judge agents (QC agents, the Loupe keeper, the QC consult) when changing /analyze-with-loupe; they must stay stable"
metadata:
  type: feedback
---

When changing /analyze-with-loupe, do not touch Loupe (`~/.claude/loupe`) or the judge side: the QC phase (`awl-qc`, anomaly-catalog §4,
generation-system §9, capcut-assembly §5), the Loupe consult and keeper, the `qc` and `qc-consult` commands, and the agent contract's QC
checks. No setting such as the effort level may vary them.

**Why:** on 2026-10-27 the user said: "no change should be made on the loupe or its agents whether on qc agents or others because the judge
agents should always be stable". An effort level that lowered QC rates and Loupe sample images was rolled back because of it.

**How to apply:** if a change truly needs a QC text (for example the 2026-10-27 orientation fix, whose old QC example told QC to flip a
source), keep it to the minimal correction and tell the user. t01 guards that no effort setting reaches QC. Related: [[awl-effort-level]], [[original-perspective]].
