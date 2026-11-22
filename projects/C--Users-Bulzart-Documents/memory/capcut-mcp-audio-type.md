---
name: capcut-mcp-audio-type
description: "Found 2026-11-22: the CapCut MCP's capcut_add_audio writes materials.audios type \"audio\"; CapCut 9.8 drops it on open (rewrites to \"none\") and shows every audio track empty; capcut-cli's form is type \"extract_music\""
metadata:
  node_type: memory
  type: reference
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-22T16:09:45.190Z
---

The CapCut MCP (`analyze-stack/tools/mcp/capcut-mcp/src/core.js`, addAudio) saves an audio clip's material with `type: "audio"`,
no `name`, and no `category_name`. This PC's CapCut (9.8) does not know that type. When it opened such a project, it rewrote the type
to `"none"` and showed the narration, music and sound tracks EMPTY, so the export would have had no sound. capcut-cli writes the
form CapCut uses for a local file: `type: "extract_music"`, `name` = the file's name, `category_name: "local"`, `check_flag: 1`.
A rebuilt project with that form opened with every audio track, and its export carried the narration (export-check found it
window by window, lag 0.02 s).

Evidence: Garbo run (static-studio), project 22_Nov_2026_v01 (MCP form, tracks empty in the editor) vs 22_Nov_2026_v01-2 (fixed form,
all tracks present, export OK). The only audio change between them was the material's type, name, category and check_flag.

**How to apply:** any project built with the MCP's add_audio needs the material fixed before CapCut first opens it. /create-video does
this in `capcut_tools.py capcut-repair` (its own `audio-materials` step, with a test). The MCP's core.js itself was NOT changed: it
belongs to another pipeline ([[one-pipeline-per-session]]). Fix it there only when working in that pipeline, on the user's say.
After CapCut has opened a project, an outside fix does not stick: build a fresh project. Related: [[capcut-desktop-automation]],
[[capcut-export-ignores-clip-volume]], [[create-video-command]].
