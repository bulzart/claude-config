---
name: create-clips-music-mode
description: "user 2026-11-22: start question Isolation | Non-Isolation (state music_isolation_mode); only decides whether the copyright-music step runs; never touches selection or editing"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-22T00:15:34.904Z
---

The user, 2026-11-22 ("Add Isolation / Non-Isolation Mode Without Changing the Existing Content Workflow"): `cc-start` asks `Music` in the follow-up
dialog (with Style and Shorts) when long videos are made; no default. Stored as `music_isolation_mode` = `isolation` | `non_isolation`; a run made
before the question has no key and keeps Isolation; `only=shorts` stores `non_isolation` unasked. Non-Isolation bypasses `cc.py music` at its entry
(no detection, fingerprint, risk score, research agent, separation, GPU lease, music folder); `edl-check` never builds a leftover music patch into a
short or a Non-Isolation video. Shorts bypass in both modes ([[create-clips-shorts-never-touch-music]]). Switching = `T state set
music_isolation_mode=...` on the user's word only: patches taken out (copy `edl.music-patched.json`, cache kept), delivered videos left as they are.

**Why:** the user's hard rule for this feature: "This is NOT a content-pipeline improvement assignment" — the same recording must give the same
selected clips, order and edits in both modes; only qualifying songs' audio may differ. The mode must never reach research, mining, the plan or a brief.

**How to apply:** never use the mode as a reason to keep, drop, shorten or move a moment, and never pass it to an editorial agent. Changes to the
music step go through [[create-clips-music-isolation]] as before; the mode only gates whether that step runs. Open (asked 2026-11-22): safety.md §3
still says "cut around [commercial music] or leave the moment out" in both modes, which conflicts with "no clip removed because it contains music".
