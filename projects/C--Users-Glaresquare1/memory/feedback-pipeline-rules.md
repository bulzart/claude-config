---
name: feedback-pipeline-rules
description: "Owner rules for the analyze-stack pipeline — no speech captions in edits, generate directly on Higgsfield via MCP, Seedance 2.5 edit as an alternative approach, edit only if asked, editing lives in CapCut (MCP first, direct draft path otherwise), never a Workflow"
metadata:
  type: feedback
  originSessionId: acdfb2b2-895b-46bd-9c4d-4b5775066aec
  modified: 2026-09-18T23:30:44.721Z
---

Given 2026-09-16 while building analyze-stack:
1. Speech captions/subtitles must NEVER be planted into an edited video (not burned in, not as a
   caption track). The owner adds them afterwards with a separate caption tool. Non-speech text
   (hook overlays, callouts, end cards, stickers) is fine.
2. Videos are generated directly on Higgsfield through its MCP from the pipeline's prompts;
   editing/rendering happens afterwards only if the owner says so (ask, don't assume).
3. A "Seedance 2.5 edit" approach must exist next to replication: ask the edit intention (which
   product to edit into the video, plus other changes), build the edit prompt with the same
   blending/physics/continuity logic, upload the source to Higgsfield via MCP, run the edit.

Given 2026-09-19:
4. Video editing lives in **CapCut** — through the `capcut` MCP server when it is present, otherwise
   through the direct path (the stack's draft builder + capcut-cli). Other formats (OTIO/FCPXML,
   Descript) are optional extras on top, never a replacement. The draft must stay editable in CapCut
   and be read back for the next render.
5. `/analyze-stack` is the only command and must never execute as a Workflow, generate a Workflow
   script, or get a second command.
6. The Seedance notes (`seedance\SEEDANCE-SPEC.md`, `SEEDANCE-EDIT.md`, and the owner-supplied
   `seedance\director\` bundle) are gathered once and loaded read-only; never refreshed by a run.

**Why:** their caption workflow is external; generation and editing are separate paid decisions;
CapCut is the editor they actually use; one command keeps the process simple.
**How to apply:** keep `references\questions.md` (Q2 approach, Q2e, G1, P0, P2 = CapCut always,
P3) and rule 9/10 in `references\pipeline-stages.md` intact; never add transcript-driven captions to
render scripts, editable projects or through the MCP's caption tools (`capcut_transcribe`,
`capcut_add_captions`, …); never `capcut_save force:true` / capcut-cli `--force-write` on the live
CapCut store. See [[project-analyze-stack]].
