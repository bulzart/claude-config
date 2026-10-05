---
name: analyze-then-pick-system
description: "Where the /analyze-then-pick video system lives and the user's fixed requirements for it (9:16 720p, 5 fps analysis, mode-dependent text)"
metadata:
  node_type: memory
  type: reference
  originSessionId: 35f8a02c-f911-4a16-92ee-15e5442237e2
  modified: 2026-09-30T23:59:40.871Z
---

**Location.** The command is `~/.claude/commands/analyze-then-pick.md`; its library is
`~/.claude/analyze-then-pick/`, containing:
- `models/index.json` + one guide per model;
- `higgsfield/higgsfield-mcp.md`;
- `reference/`, `pipeline/`;
- `scripts/atp.py` (local FFmpeg toolkit).

It was built 2026-09-30. It succeeds the older `~/.claude/analyze-stack` (a Seedance-only product-swap
pipeline).

**User-set requirements, not negotiable:**
- Every Higgsfield output is vertical 9:16 at 720p (720×1280) and is never asked.
- Video analysis samples ~5 fps, densified around cuts and actions and thinned in static stretches.
  "Approximately five passes" was a misreading.
- Text depends on the mode:
  - Edit Mode strips all source text;
  - Analyze Mode may add new, intentional text, rendered in post by default;
  - reference wording is never copied.
- Prompts must actively use the selected model's official examples (§4.0 pattern card).
- **Model selection** (clarified 2026-10-01):
  - The video model is picked right after the Edit/Analyze choice and is locked for the run: never
    re-asked or switched.
  - The menu always lists every available model, even if long, with Seedance 2.5 and Wan 3.0 Prime
    pinned on top (`index.json → menu`).
- **Edit Mode review loop** (2026-10-01):
  - After each edit, open the video for the user and ask whether it is okay.
  - "Needs changes" re-edits the original source (never the previous output); the next video starts
    only after approval.
- **Audio split** (2026-10-01):
  - At intake, every original video's audio goes to `<given path>/files_audio/` and a silent copy to
    `<given path>/videos_without_audio/`.
  - Only silent copies are uploaded to Higgsfield (fewer flags).
  - Edit Mode finals always get the original audio merged back (`atp.py restore-audio --audio`).
  - Once approved, they go to `<given path>/final/<original name>.mp4` (`atp.py finalize`; that
    folder carries a hidden `.atp-final` marker so re-scans skip it).
- **Generation discipline:** every paid generation goes through `atp.py ledger`, with one job in
  flight, no parallel or blind resubmits and no duplicates. The user explicitly asked that Higgsfield
  generation calls never spam or glitch.
- **Assets come only from the user** (clarified 2026-10-01):
  - **Analyze Mode:** they drop all product samples, characters and other assets at the start, and
    the command picks from them autonomously for each video.
  - **Edit Mode:** they choose the operations per video (e.g. Replace + Swap), then drop the files
    for each operation.
  - Never detect or pick assets inside the references or source folders. They may hold other
    products or executions.

**Higgsfield MCP quirks seen 2026-09-30:**
- `show_medias` fails with an output-schema error in Claude Code.
- `cinematic_studio_video_v2` ignores `multi_prompt`.
- Always read `adjustments` from `get_cost` preflights.

Related: [[no-workflows-agent-cap]]
