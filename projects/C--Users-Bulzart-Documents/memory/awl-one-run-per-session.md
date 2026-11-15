---
name: awl-one-run-per-session
description: "/analyze-with-loupe: a session keeps its run; more videos and new references continue it; only a new start or a clone makes a run folder"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-07T03:23:51.446Z
---

User 2026-11-07: "no need to generate multiple runs for each generation we do inside one session ... we just continue on it ... only
create a new run folder when the user clones a run ... a new run session or a clone session is the only thing that creates a new run
folder in C:\Users\Bulzart\.claude\analyze-with-loupe\runs".

**Why:** the run holds the channel (niche, style, narrator) and everything mined from the references; splitting a session over run
folders scatters that data and re-analyses references.

**How to apply:** once a session has a run, never `T new-run` again for more videos or for references added to its folder: take the
inventory again in that run (ids stay put since 2026-11-07; new files get the next ids), analyse only the new references into its
folders (A1, A3, the spec revised at A4), then make the videos. A clone (`/analyze-with-loupe clone <run>`) or a fresh
`/analyze-with-loupe` start are the only new run folders. Related: [[analyze-with-loupe-command]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-07: more videos and new references continue the session's run (ids kept, analyse only the new ones); only a clone or a new /analyze-with-loupe start makes a run folder
