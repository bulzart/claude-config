---
name: capcut-desktop-automation
description: How CapCut 9.8 was driven on this PC for a visual check (2026-11-20): PowerShell user32 clicks/screenshots, export to a scratch folder, ExportPath in the registry to restore, opened projects restore from CapCut's own backup
metadata:
  type: reference
---

Only with the user's yes for that check (it takes the mouse and keyboard). No computer-use tool in Claude Code CLI here: PowerShell P/Invoke (SetCursorPos, mouse_event, keybd_event ALT tap + SetForegroundWindow, Graphics.CopyFromScreen), screenshots read back with Read. Screen 1920x1080 at 100 %.
- Launch `%LOCALAPPDATA%\CapCut\Apps\CapCut.exe`; home window 1440x960 at 240,37; a project tile click opens the editor (maximised 1920x1032); Export button ~(1769,17); dialog folder icon ~(1288,322) opens a Windows folder picker (type the path in Folder:, Enter, Select Folder); dialog Export ~(1188,820), done dialog Close ~(1267,805); Menu (113,17) -> Back to home page (147,214); quit = Process.CloseMainWindow() from the home page.
- The export folder is remembered in `HKCU\Software\Bytedance\CapCut\Modules\Export` `ExportPath` (the user's: `C:/Users/Bulzart/Documents/stream-clips/output`): restore it after CapCut has exited.
- A project CapCut has opened once is restored from its own backup on the next open: editing its draft files from outside does NOT stick. Build a fresh project (new name) instead. Fresh capcut-build projects load exactly as written.
- A 21 s 1080x1920 export takes ~8 s. CapCut re-saves an opened draft in its own format (draft_content.json, template-2.tmp, a .bak).
Related: [[create-clips-caption-look]], [[capcut-autoupdate-blocked]]
