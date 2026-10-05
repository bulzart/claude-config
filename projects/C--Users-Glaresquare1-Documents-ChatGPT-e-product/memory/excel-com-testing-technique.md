---
name: excel-com-testing-technique
description: "How spreadsheet products were proven identical in real Excel on this PC (COM automation, baking results, metadata scrub, Protected View, captures)"
metadata:
  node_type: memory
  type: reference
  originSessionId: a7551dd1-9530-4a94-a346-55ba54629a27
  modified: 2026-10-03T07:59:56.391Z
---

Proven on 01A (2026-10-03), reusable for 01B/01C/01D:
- Values: openpyxl writes each fixture workbook → PowerShell `Excel.Application` COM: Open, CalculateFull, SaveAs →
  openpyxl `data_only=True` reads Excel's stored values → compare with the oracle (tests/excel_check_all.py). Negative
  control: an uncalculated file must fail. ~3 s per workbook.
- Ship Excel-saved files (source/build/bake_xlsx.py): openpyxl output has no stored results, so Protected View and
  previews show formula cells blank. Excel's save writes `cp:lastModifiedBy` (Windows user) and `x15ac:absPath` (local
  folder) — strip both in the zip; never change Office's user-name setting.
- Protected View test: add Zone.Identifier ZoneId=3, open with EXCEL.EXE explicitly (this PC has no default .xlsx app →
  a double-click shows Windows' chooser), use a fresh folder each run (Excel trusts a path after Enable Editing).
- Desktop screenshots: COM-opened visible window + PrintWindow(PW_RENDERFULLCONTENT), DPI-aware, trim the maximised
  frame (source/tools/capture_excel_desktop.ps1). Set values via `.Formula = [string]` (Value2 with doubles failed).
- Data validation: Excel's "Ignore blank" skips a CUSTOM rule whenever ANY referenced cell is empty (e.g. miles accepted
  while the category is blank) — Sheets always evaluates. Write custom rules with allow_blank=False (01A D-67); list
  rules can keep it. Always type one cross-column case by hand in Excel, not only fixture values.
- Merged cells never overflow: a status message in a merged range gets cut off in both Excel and Sheets — leave it
  unmerged with empty cells to the right (01A D-68). Review long dynamic texts with real captures.
- Background regressions run as child processes: if the session restarts, a PowerShell/Excel recalc can keep running
  orphaned while the follow-up check never runs — check the logs/processes and re-run the check yourself.
- PDF page review without poppler: Windows.Data.Pdf via PowerShell (source/tools/render_pdf_pages.ps1).
Related: [[money-os-release-state]]
