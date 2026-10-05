---
name: apps-script-editor-paste-technique
description: "Monaco API edits in the Apps Script IDE are not saved; edit via real clipboard paste, and cache-bust Sheets mobile htmlview"
metadata:
  node_type: memory
  type: reference
  originSessionId: a7551dd1-9530-4a94-a346-55ba54629a27
  modified: 2026-10-03T04:18:38.705Z
---

- Apps Script IDE: `monaco` model edits (setValue/executeEdits) are NOT registered or saved. Working method: PowerShell
  `Set-Clipboard` with the new text → JS `getSelection().removeAllRanges(); ed.setSelection(range); ed.focus()` → real
  ctrl+v → ctrl+s → check "Saved to Drive" → Run button. Read the run log from `document.body.innerText`; the Chrome
  extension redacts `=`, `&`, `?` in results, so replace them in JS first. Past runs and their logs are on the project's
  /executions page (click a row to expand).
- Google Sheets mobile web (`/htmlview`) is browser-cached; after a rebuild add a cache-busting query
  (`/htmlview?cb=<n>#gid=…`) or you will test the old layout.
- Full-screen captures: arm `requestFullscreen` on pointerdown, click, then zoom tiles (0,0,756,795)/(756,0,1512,795)
  at scale 1 with save_to_disk → 960×1010 PNGs.

- Several editor tabs of the same project hold their OWN copy of every file: an old tab showing "Unsaved changes" would
  overwrite newer saved code if Save/Run were pressed there. Reload stale tabs before relying on them; verify the saved
  state by length + djb2 hash of each model in a freshly loaded tab.
- Runs keep going server-side while the tab is hidden: start them with a synthetic click on the button whose
  aria-label is "Run the selected function", and poll the Execution log with single short JS reads (hidden tabs throttle
  timers — long JS wait loops hit the 45 s CDP timeout).
- One function per Run that advances a step counter kept in Script Properties (e.g. opDrive) avoids the fragile function
  dropdown: put it first in the open file so it is the default selection.
- The same spreadsheet open in two tabs shows a collaborator cursor with the account's NAME — close the second session
  or mask the label before saving any capture.
Related: [[browser-tooling-preference]]

- 2026-10-05 additions: load the clipboard with `Get-Content -Raw -Encoding UTF8 <file> | Set-Clipboard` and verify with
  `Get-Clipboard` (line count) — `Set-Clipboard -Value $text` from the tool's PowerShell reported 0 chars once. After the
  paste, `monaco.editor.getModels()` lengths confirm the saved model (LF line ends: file bytes − line count). Google Drive
  tabs often freeze `Page.captureScreenshot` after a navigation: read them with `get_page_text` / `find` / JS on `[data-id]`
  rows (selection = `aria-selected`), select rows by `ref` with ctrl-click, press Delete to trash, verify via the Trash page.
  A step runner that returns a message containing "ALL DONE" from a sub-step ends the outer runner early — match a unique token.
