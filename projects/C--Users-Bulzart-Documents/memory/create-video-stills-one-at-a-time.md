---
name: create-video-stills-one-at-a-time
description: "user 2026-11-22 (Garbo run): stills strictly one per worker run, each reviewed as it lands; never batches of several"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-22T15:32:51.343Z
---

Generate stills strictly one at a time: one image per image-worker job (jobs/one/SNNN-*.json run in order by run_chain.sh), and
look at each still as soon as it lands before trusting the next. Never queue chunks of 5-6 stills in one job again.

**Why:** the user, 2026-11-22, after a batch lost to a memory-guard stop and a still with a man melting into a map ("try to
execute stills one by one to avoid problems" / "yes strictly do one-at-a-time runs for stills"). A guard stop then costs one
picture, not a batch, and a fault is caught before more of the same.

**How to apply:** split any multi-image job into single-image jobs (same settings, own log_out), keep the STOP file check between
them, review each still (full size for lettering, edges, hands, insignia) when its done-line arrives. Model reload per still is
the accepted cost. A guard stop mid-run is usually another heavy app opening (CapCut ~2 GB): the next still waits until it
closes (jobs/resume_when_free.sh in the Garbo run). A fault in what a still SHOWS is remade (reworded frame_prompt, new seed,
or a "keep ... exactly; change only ..." edit); made-up LETTERING on an otherwise right still is fixed locally with
static-studio/scripts/still_touchup.py (preview, look, then --apply; original kept). Related: [[local-ai-installs]],
[[awl-memory-is-a-fact]], [[capcut-export-ignores-clip-volume]].
