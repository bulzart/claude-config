---
name: create-clips-blur-only-gore-distress
description: "/create-clips blurs ONLY gore, real distress and nudity; never personal data, DMs, usernames, IDs, lobby tags, face cams or names (user 2026-11-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: e465a765-7e76-4c82-9cac-7fd4d55a8b6c
  modified: 2026-11-14T01:57:09.243Z
---

User, 2026-11-14, after the ishowspeed run's L01 blurred viewer DMs and a Social panel: "no need to do blurring on any of them whether dm, face cams, names, or whatever, the only reason we blur is when there's gore, distressful content and similar, as for other types no need to blur at all, update the create clips to avoid that too".

**Why:** the personal-data blurs (23 spans in L01) covered almost the whole picture at times (a Social panel plus DM popups: one band over the frame) and hid the face cams and gameplay for no gain the user wanted.

**How to apply:** `sensitive` kinds are gore | distress | nudity only. Personal data (phone numbers, addresses, emails, viewer DMs and chat, usernames, in-game IDs, lobby tags, party/Social panels, face cams, faces, donor alerts) is left as it is: no `sensitive` entry, no `censor` entry, nothing in a brief or report. Written into `reference/safety.md` §2 ("Not blurred, ever"), the router rule 7, README, the mining/planning/build skills and the game references. Gossip/crime jokes about named real people and the religion/superstition rule are unchanged (avoid, not blur). The `censor` tool stays, for gore/distress/nudity. See [[create-clips-pipeline]].
