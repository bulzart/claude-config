---
name: feedback-fix-limits-dont-just-report
description: "When I find a limitation or gap in something I built or proposed, evaluate it and fix it (test on real data); do not just list it for the user to decide (user 2026-11-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T02:46:12.766Z
---

User, 2026-11-14, after I had reported a cross-block limit of the context idea as "one limit to this" and offered a fix to choose: "if we find such errors ... we evaluate and fix them and not just report them".

**Why:** the user wants the system to work, not a list of known weak spots handed back to them; reporting a gap I could close costs them a round trip.

**How to apply:** when I notice a gap while explaining or reviewing my own work, test it against real data (as I did on the ishowspeed run), fix it in the lightest way that works, and say what I fixed; keep a question for the user only when the choice is genuinely theirs (a preference, not a bug). Keep fixes proportionate: no new machinery for a small gap, no limits or quotas where they asked for none ([[create-clips-context-keeping-light]]).
