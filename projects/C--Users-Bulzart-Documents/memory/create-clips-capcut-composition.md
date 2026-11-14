---
name: create-clips-capcut-composition
description: "user 2026-11-13: /create-clips builds every CapCut project through the composition for faster delivery: ONE `cc.py capcut-build` (compose + finish + read-back); transitions and word-box caption texts go into the single capcut compile; verified identical to the old route"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-13T16:43:26.287Z
---

User 2026-11-13 (mid-turn): "but also make sure to use capcut composition for everything if possible for faster delivery".

**What was built:** `cc.py capcut-build --run RUN --video ID` = `capcut-compose` (one `capcut compile`: clips on their real chunk files, sfx lanes, the transitions as `transition` operations, the word-box caption texts as text tracks plus `text-style` operations) + `capcut-finish` (only what compile cannot carry: zoom keys, bg-blur written in-process, caption font and entrance via awl, repair, cleanup) + a read-back (clips vs plan, length, joins, texts, media on disk, `capcut lint`) with a `problems` list. `capcut-compose --bare` keeps the old split; `OUT/composed.json` tells finish what is already in the draft (fingerprint of the planned texts; a changed plan or an MCP-built draft is finished the old way).
**Why it is safe:** `import-srt` and `transition` call the same capcut-cli functions (addText, setTextStyle, addTransition) that compile's operations call; checked text by text on the BLAST test video (1,909 texts, 15 tracks): 0 differing rows, same track order and materials. If compile refuses an operation (unknown transition name) compose removes its own half-made folder and composes bare, finish does the rest the old way.
**Measured (BLAST L01w, 4.5 min):** old compose + finish 25 s, `capcut-build` 8 s (compose 2, finish 5, read-back 1); the font-family lookup (3 s per call, three calls) is cached in `create-clips/data/font-cache.json` (git-ignored; since the font is fixed to Luckiest Guy by file name the build looks nothing up unless an EDL names a family); clip probes run side by side. Scale: a 10-minute test (3,355 texts) built in 9 s, 26 MB.
**Safety additions:** `capcut compile` rewrites CapCut's shared `root_meta_info.json`, so compose holds the machine-wide store lock (`<awl runs_root>/.capcut-store.lock`, the lock file the Loupe repair uses); a 4-parallel compose test keeps all four projects in the index; `capcut-build` refuses a captions.json older than the last edl-check.
**How to apply:** every build skill, the produce contract, router rule 9 and `capcut-build.md` say ONE command, never clip by clip; the MCP route stays a fallback only after a plain error a re-run does not fix.
Not verified: how CapCut draws the result (no tool can); the scratch store of the timing test was `jobs/efec77d7/tmp/store` (not the user's CapCut store).

Related: [[create-clips-caption-look]], [[create-clips-one-research-agent]], [[create-clips-pipeline]], [[loupe-web-app]]

Index line before the 2026-11-14 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-13: every build through `cc.py capcut-build` (compose + finish + read-back, transitions and word-box texts inside the single capcut compile), 25 s -> 8 s on the BLAST test video, identical to the old route; store lock + font cache; MCP route fallback only
