---
name: excel-web-chrome-testing-technique
description: "How to drive Excel for the web (OneDrive) reliably through the Chrome MCP for product tests — Name Box navigation, list cells, dialogs, stuck tabs"
metadata:
  type: reference
---

Proven on 01A v1.1.1 (2026-10-04), Excel for the web in Chrome (bulzarti's OneDrive):
- Navigate with the **Name Box** (click it at ~(67,138) in a 1536-wide frame, ctrl+a, type, Return): a defined name
  such as `inc_Date`, `tax_GR`, `set_TaxYear` switches sheets; then a plain ref (`G8`) on the same sheet selects one
  cell. Jumping to a whole-column name selects the range — typing then goes to the first cell and Tab/Enter move
  INSIDE the selection, so jump to a single cell before typing rows. The Go To dialog (ctrl+g) only opens when the
  grid has keyboard focus and drops keystrokes otherwise; avoid it.
- List-validated cells: typed text is sometimes refused or replaced by the first list item (AutoComplete accepts the
  highlighted suggestion). Type, wait ≥1 s, check the suggestion, or pick from the dropdown arrow (click the cell,
  then the arrow at its right edge, then the item ~21 px below). Client/invoice lists built with an INDEX-range name
  (`dv_ClientNames`) refuse typed names entirely in Excel web — picking works.
- Validation error dialogs are modal: later keystrokes are lost; Cancel is at the dialog's bottom right (0.6-scale
  screenshot → ×1/0.6). Date cells pop a date picker — press Escape after committing.
- A "Saving…" tab can freeze (clicks ignored, stale values): reload the Doc.aspx URL; autosave had kept the edits.
- The screenshot frame size changes with the window; always compute coordinates from the latest frame.
- Evidence: the Chrome screenshot/zoom files land in the session's tool-results folder; copy the ones you cite into
  tests/.../evidence/ with descriptive names right away (they are gone after the session).
Related: [[excel-com-testing-technique]], [[apps-script-editor-paste-technique]], [[money-os-release-state]]
