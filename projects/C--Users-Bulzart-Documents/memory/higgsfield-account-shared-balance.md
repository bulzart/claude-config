---
name: higgsfield-account-shared-balance
description: "The Higgsfield balance drops from spending by other Claude sessions on the same account (e.g. the Viral-browser / ATG session), so unexplained charges are not necessarily this session's agents"
metadata:
  node_type: memory
  type: reference
  originSessionId: 6dd98a9f-a746-44c3-8a2d-23c71b636269
  modified: 2026-10-12T20:47:44.302Z
---

On 2026-10-12 the Higgsfield balance fell far more than this session's agents and upscales explained (4063 -> 1568 credits while the 4 fix agents spent 354 and Topaz 13). `transactions` showed Wan 3.0 Prime / Object Swap / Kling charges landing after every agent of this session had finished. `ListAgents` showed a peer session "Viral-browser mode for analyze-then-generate" busy in the background on the same account.

**Why:** two earlier "unexplained" drops (about 220 credits, then about 2100) had the same cause: another session using the same account.
**How to apply:** before calling a balance drop unexplained, run `transactions` and `ListAgents`; compare timestamps with this session's own ledger (`T ledger`) and report only the difference as "other sessions on the account". Do not stop or message the other session without the user asking. See [[atg-pipeline]].
