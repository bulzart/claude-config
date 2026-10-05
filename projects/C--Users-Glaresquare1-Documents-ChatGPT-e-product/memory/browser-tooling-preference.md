---
name: browser-tooling-preference
description: "User wants browser/Google work done through the connected Claude-in-Chrome extension, signed in as bulzarti@gmail.com"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a7551dd1-9530-4a94-a346-55ba54629a27
  modified: 2026-10-03T04:18:33.640Z
---

Use the Claude-in-Chrome tools for Google Sheets/Drive/Apps Script work; the user's Chrome is signed in as
bulzarti@gmail.com (Google /u/4 index). Computer use is read-only for browsers, so never script clicks into Chrome
another way. The app's browser pane is also signed in and is useful for phone-viewport checks.

**Why:** the user said "just use the chrome, i already connected it to the claude" and "use computer use to do anything
on your own" after rejecting a PowerShell COM approach.

**How to apply:** do browser tasks yourself with the Chrome MCP tools instead of asking the user; verify the active
account in the UI before changing files. See [[apps-script-editor-paste-technique]].
