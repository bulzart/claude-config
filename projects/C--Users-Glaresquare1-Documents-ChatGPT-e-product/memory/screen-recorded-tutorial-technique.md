---
name: screen-recorded-tutorial-technique
description: "How the narrated product tutorial video was recorded and edited from a Chrome MCP session (capture, logging, narration, render) — reusable for 01B/01C/01D"
metadata:
  node_type: memory
  type: reference
  originSessionId: a7551dd1-9530-4a94-a346-55ba54629a27
  modified: 2026-10-03T19:03:23.928Z
---

Proven on 01A (2026-10-03, `assets/video/setup-tutorial/`, D-55):
- Chrome only paints/screenshots the *visible* tab of a *non-occluded* window; MCP tabs are created as background tabs
  in the user's window and MCP cannot switch tabs. Ask the owner once to right-click the tab → "Move tab to new window",
  then park that window mostly off-screen (x≈1872, 48-px strip, topmost via SetWindowPos) — Chrome keeps rendering and
  the user can keep working. After moving/resizing, nudge the window 1 px if `document.visibilityState` stays "hidden".
- Capture with PrintWindow(PW_RENDERFULLCONTENT) (`tools/recorder.py`): no real pointer in frames, only changed frames
  written to an x264 MKV with wall-clock times. Hide the extension overlay (`#claude-agent-glow-border`,
  `#claude-phantom-cursor`) with an injected style.
- Log clicks/keys/wheel in the page (capture-phase listeners, `window.__mosLog`); read it back in small chunks
  (tool output truncates ~1 KB) and never clear it before saving. Navigation/reloads lose it; recover from frame changes.
- Popups (Google OAuth) are separate windows: recorder grabs new Chrome windows to PNG; the OAuth grant is the owner's
  click (ask), e-mails must be pixelated.
- Edit (`tools/render.py` + `tools/edit_spec.py`): narration-driven beats, idle compression + holds on results,
  synthetic pointer/ripples/click sounds from the logged events, camera zooms, highlights, solid wipes, captions.
- ElevenLabs MCP: generate per scene with `generations_count: 1` in one flow; concurrency limits auto-retry; signed MP3
  URLs expire in 2 h — download promptly (write URLs to a file; heredocs with them failed). Commercial use needs a paid plan.
- Sheets gotchas seen: row-1 HYPERLINK cells need two clicks; percent cells auto-add "%" (type 4.4, not 4.4%);
  Print the Invoice Generator with "Selected cells".
Related: [[excel-com-testing-technique]], [[money-os-release-state]], [[browser-tooling-preference]]
