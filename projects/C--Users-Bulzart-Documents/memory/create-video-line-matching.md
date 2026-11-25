---
name: create-video-line-matching
description: "user brief 2026-11-25: /create-video compares script versions by their words, not line numbers; revise freely (add, cut, move), never edit in place to keep ids"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3cb802e3-203e-41d6-98ff-b19f9a9a5679
  modified: 2026-11-25T02:11:22.397Z
---

Since 2026-11-25 (`align_script_lines`, LINE_MATCHING 2 in static_core.py; tests "a line added renumbers..." and
siblings), a script read's lines are matched to the current script by their words as well as their numbers: the
reading with fewer changed lines wins, the numbers on a tie. A line added or removed no longer makes every later line
count as revised; a moved line still counts (order is what the reader followed); a removed line counts beside what
its neighbours carry. Holds follow their lines. A beat's or shot's line numbers are its place, not its content
(`part_sha` leaves out id, line_start, line_end; `part_sha_v1` reads older records as made), so later beats, their
shots and a waiting scoped re-check are not touched by a renumbering.

**Why:** the Qin letters run (draft 10) was edited in place only to keep the line numbers, because one inserted line
flagged ~100 later lines and every later hold; the user asked that legitimate insertions not invalidate unrelated work
while real revisions still get reviewed.

**How to apply:** revise in whatever shape the story needs. `revision_notes` name lines by their numbers in the
script as it now stands; a `revised` answer may use those or the reader's numbers; a cut line is named by the number
the reader saw. Re-key notes after any later renumbering. A record made before LINE_MATCHING 2 keeps the
number-by-number check for its own answers. Still positional: claims.json `line_refs` (the builder rewrites them;
plan-check names a stray one) and recorded narration parts (a line count change after recording still means
`--rechunk`, every part re-billed: offered to the user as a fix, not built). Related: [[create-video-storytelling]],
[[create-video-cold-reader-blind]].
