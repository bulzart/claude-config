---
name: create-static-command
description: "/create-static (2026-11-13): Static-only command built from /analyze-with-loupe's Static mode, CapCut project by ONE composition (T capcut-build); library ~/.claude/create-static, 11 cs-* skills, tests, what was verified"
metadata:
  node_type: memory
  type: project
  originSessionId: 6677b194-11f2-4714-bc04-4ee75bf9e834
  modified: 2026-11-13T18:57:22.701Z
---

`/create-static` is the Static mode of /analyze-with-loupe made into a command of its own, identical in behaviour and rules except step S4: each video's CapCut project is built by `T capcut-build --run RUN --video NN [--format TAG]` (one `capcut compile` + one write pass + repair + read-back with `problems`), never the CapCut MCP or one command per feature. Asked by the user 2026-11-13 after the create-clips composition ([[create-clips-capcut-composition]]).

**Where:** router `~/.claude/commands/create-static.md`; library `~/.claude/create-static` (own `cs.py` clone of awl.py + `cs_compose.py`, `reference/` = static + analysis-protocol + creative-direction + brand-guardrails + assets-and-substitution + anomaly-catalog + production-agents + `capcut-build.md`, `data/compose-template`, own `runs/`); skills `~/.claude/skills/cs-{start,prepare,study,plan,produce,sound,images,edit,record,wrapup,feedback}`. Contract item numbers kept from the original router (so citations resolve) plus new item 39 (the composition). Tests: `python ~/.claude/create-static/scripts/check_all.py` (t01_compose 44 checks on a synthetic video, t02_library consistency, docs_tool check).

**Verified 2026-11-13:** real video 03 of run 20261106-063422-static-klein (12.7 min, 128 stills, 4,413 caption texts, 17 labels, 6 joins): build 23-27 s vs ~3 min for the old commands; compared segment by segment (4,560): identical but caption times (exact µs vs the SRT route's ms). NOT verified: how CapCut draws it (nobody opened it), a real run through the new skills end to end, overlays/drawings on real data (only a synthetic test).

**Decisions:** stills + narration + bed stay in place (350 KB placeholder, retargeted); effects/drawing/sfx files are copied by compile as before; the machine-wide CapCut store lock is shared with the other toolkits (`config.json capcut.store_lock` -> the awl runs folder lock); refused joins/entrances/effects stop the build with exit 2 before anything is made; a compile refusal falls back to bare compose + the older single commands (kept in cs.py as pieces: capcut-motion/-transitions/-effects/-word-box/-text-anim/-labels/-prep/-repair/-check, never cited by skills); `awl_input_guard.py` now guards both libraries' runs. Non-Static commands dropped from cs.py's CLI.

**How to apply:** change the owning skill/section and run `check_all.py` + `docs_tool.py index`; keep the two toolkits' behaviour separate (no cross-pipeline mentions); a new Static fix in /analyze-with-loupe is not carried over automatically.

Index line before the 2026-11-14 compaction of MEMORY.md (kept here so nothing is lost): 2026-11-13: Static mode of /analyze-with-loupe as its own command, CapCut project by ONE composition `T capcut-build` (23 s vs 3 min, identical output); library ~/.claude/create-static, cs-* skills, check_all.py; not yet opened in CapCut or run end to end

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): 2026-11-13: Static mode of /analyze-with-loupe as its own command, CapCut project by ONE `T capcut-build`; library ~/.claude/create-static, cs-* skills; not yet run end to end
