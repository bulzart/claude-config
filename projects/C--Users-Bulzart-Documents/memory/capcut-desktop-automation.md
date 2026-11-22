---
name: capcut-desktop-automation
description: "Driving CapCut 9.8 on this PC (2026-11-20/22): create-clips `cc.py desk` + `capcut-app`; /create-video its own capcut_desk.py (standing yes 2026-11-22); export folder in the registry, project file copies"
metadata:
  node_type: memory
  type: reference
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T16:11:13.236Z
---

Only with the user's yes (it takes the mouse and keyboard); the user gave it for the /create-clips export test 2026-11-21. No computer-use tools in this
Claude Code CLI (they exist only in the Claude desktop app with Computer use on). Since 2026-11-21 the toolkit has the steps: `cc.py desk shot|windows|
focus|click|key|type` (user32 SendInput, Pillow screenshots, read back with Read) and `cc.py capcut-app start|quit|status|export-path --set/--restore`;
the procedure is cc-wrapup 1b; one export at a time under `cc.py gpu --take capcut-export`. Screen 1920x1080 at 100 %.
- Launch `%LOCALAPPDATA%\CapCut\Apps\CapCut.exe`; home window 1440x960 at 240,37; a project tile click opens the editor (maximised 1920x1032); Export button ~(1769,17); dialog folder icon ~(1288,322) opens a Windows folder picker; dialog Export ~(1188,820), done dialog Close ~(1267,805); Menu (113,17) -> Back to home page (147,214); quit = WM_CLOSE to CapCut.exe's own windows.
- Find CapCut's windows by its process, never by title: a terminal tab can be titled "CapCut clips ..." (`capcut_windows()`).
- The export folder is remembered in `HKCU\Software\Bytedance\CapCut\Modules\Export` `ExportPath` (the user's: `C:/Users/Bulzart/Documents/stream-clips/output`): set before start, restore after CapCut has exited (`capcut-app export-path`).
- A project CapCut has opened once is restored from its own backup on the next open: editing its draft files from outside does NOT stick. A fresh capcut-build project loads as written, and its timeline lives in EIGHT copies (root and `Timelines/<id>/`: draft_content.json, .bak, draft_info.json, template-2.tmp): an outside fix before the first open must change all of them alike. `capcut trim` and the MCP trim cannot move a text clip (null source_timerange).
- A 21 s 1080x1920 export takes ~8 s (a 51 s short 6-7 s, a 32 min long 2 min 15 s). CapCut re-saves an opened draft in its own format. A "CapCut Pro" advert can pop up at start: close it with its X (~1120,296), never Purchase.
- Probed 2026-11-21: a project added to the store while CapCut is open shows on its home page (after Home) and stays in root_meta_info.json after CapCut exits; capcut-cli refuses writes while CapCut runs ("refused [editor-open]", after copying the template and registering). Builds and the GUI export are serialised by the desk hand-off (`cc.py gpu --take capcut-export` waits for a build writing its project; a build waits during an export), not by stopping builders. root_meta_info.json's `draft_ids` is CapCut's own counter: the CLI never changes it.
- /create-video (static-studio) has its OWN tool since 2026-11-22: `static-studio/scripts/capcut_desk.py` (shot, click, key, type, windows, focus, app start|quit|status, export-path --set|--restore|--show; tests/test_capcut_desk.py) and manual 09 "Export and look". Standing yes for that pipeline: the user 2026-11-22, "thats how you can export the projects and inspect them yourself too ... also make sure to implement it into the pipeline too"; it exports after timeline-check, then export-check, final watch review, release-check. Its safety: a click only when CapCut is in front AND the window under the point is CapCut's; `app start` refuses a CapCut it did not start (the user's or another session's) and `app quit` closes only one it started (pids in runs/.desk/started.json). Seen 2026-11-22: the export dialog's "Remove watermark" toggle shows a white pill while loading and settles to off a moment later; the saved dialog's Close moved between exports (~(1267,805) then (1267,852)): read it off a shot. Two 10:28 exports took ~10 s and ~35 s.
Related: [[create-clips-caption-look]], [[capcut-autoupdate-blocked]], [[capcut-mcp-audio-type]]
