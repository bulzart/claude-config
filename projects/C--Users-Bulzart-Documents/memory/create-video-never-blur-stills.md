---
name: create-video-never-blur-stills
description: "user 2026-11-23 (Garbo run): never blur, erase or cover anything in a /create-video still; prompt the thing out and remake the still"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-23T00:43:27.772Z
---

Nothing in a /create-video still is ever blurred, erased or covered. Whatever would need hiding (made-up lettering on papers,
books, signs or banknotes; place names on maps; cross-like badges; a seal emblem; a doubled clock numeral) is kept out by
the frame prompt, which describes what is there instead, and the still is generated again.

**Why:** the user, 2026-11-23, after seeing blurred patches on stills in the v3 cut: "remove all the blurrings above some
stills that are blurred and never blurr anything, if there's something to be blurred then instruct in the image generation
so that it avoids that thing". still_touchup.py's `erase` was a 15-35 px median filter, so it counted as a blur too: all 14
touched stills (8 soften, 6 erase) were remade.

**How to apply:** prompt patterns that worked with Klein: the plain blank back of a sheet; a closed book in a plain cloth
cover; print painted as soft grey stripes "with no letters at all" ("too small to read" still produced legible nonsense);
outline maps of coast, rivers and hills; money in a tied leather wallet; a smooth plain wax seal (one came out with a
star emblem); bareheaded veterans with plain ribbon bars; a clock with dots and no numerals, hands described by direction
("the hour hand level, pointing right at the three o'clock dot"); close with "There is no writing, lettering or numbers
anywhere in the picture." Remake from the people's references, never as an edit of the flawed still (its last job may be a
self-edit: check the job's refs). Zoom on pages, spines, seals and banknotes before accepting. After a remake, re-check the
shot's camera move and every drawing placed on it, and every shot that `reuses` that still (S084/S085 reused S059), and
re-decide any held silence decided with the old picture (timeline-check: hold_Lnnn_decided_with_another_picture).
Pipeline since 2026-11-23: still_touchup.py refuses erase/soften (only crisp text/paint marks, never over a fault);
record_media stores each still's file_sha256; stills_facts (timeline-check, release-check) refuses a still changed after
generation or carrying an active blur/erase in stills-postprocess.json, and no reapproval accepts either. Manual 04 and
commands/create-video.md Non-negotiables carry the rule. Related: [[create-video-stills-one-at-a-time]],
[[create-video-advanced-drawings]], [[awl-static-no-subtitle-text]].
