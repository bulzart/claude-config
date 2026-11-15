---
name: protected-build-tool
description: "user 2026-11-15: a separate compiled copy of create-clips/create-static for if they ever leak or get handed to someone outside, never touching the maintained source; driver is Node.js, not PowerShell"
metadata:
  node_type: memory
  type: project
  originSessionId: 7871cc76-de90-4292-a548-53ad612f5f68
  modified: 2026-11-15T09:24:02.325Z
---

User 2026-11-15, after a chat-heat feature push: "analyze the logic this type of pipelines use to build their dependencies and how to make it hard to couple it without knowing the order of files ... so that if someone steals our codebase they don't know how to build it and can't abuse our tool if it leaks or goes public." I explained that scrambling file order is weak security-through-obscurity for Python and would break my own ability to read/edit this exact source every session; asked a clarifying question (AskUserQuestion); the user picked "a separate obfuscated build, only if you ever ship it to someone" — keep the maintained source exactly as is, add a one-time packaging step for a future hand-off. Then, mid-build: "it should not be a .ps1 build but a nodejs possibly and if there are ps1 scripts to be run then include them as scripts and ps1 file to be run inside the obfuscated build."

**Built:** `C:\Users\Bulzart\.claude\scripts\build-protected.js` (Node.js; the retired `.ps1` version was deleted). It shells out to PyInstaller (`python -m PyInstaller --onedir --collect-all ...`) against `cc.py` or `cs.py` (the only real protection mechanism — PyInstaller compiles Python to bytecode-only, Node is only the driver), writes the output to `C:\Users\Bulzart\ProtectedBuilds\<pipeline>\dist\<cc|cs>-tool\` — **outside `~/.claude`, so a build is never part of the git repo** — copies `config.json` as `config.example.json` (the real paths are this PC's, whoever receives the build must edit them), copies any `.ps1` helper scripts the pipeline ships into a `scripts\` subfolder of the build unmodified (create-clips has `install-background.ps1` and `notify.ps1`; create-static has none), and writes a `NOTICE.txt` (proprietary, no reuse without permission; lists what the destination machine still needs: ffmpeg, CapCut 9.7 + capcut-cli, the faster-whisper `medium` model, an API key for create-static).

**Run it:** `node C:\Users\Bulzart\.claude\scripts\build-protected.js --pipeline create-clips --clean` (or `create-static`). `--skip-smoke-test` skips the final `--help` check. No npm install needed (Node 22.13.1, built-ins only: `node:child_process`, `node:fs`, `node:util.parseArgs`).

**Verified (2026-11-15):** both built and passed `--help` with exit 0: create-clips 52 s, 523 MB (numpy, PIL, faster_whisper, ctranslate2, rapidocr_onnxruntime, onnxruntime bundled; a harmless `tbb12.dll` warning from numba, no crash); create-static 94 s, 620 MB (same list plus cv2, librosa, requests, pypdf). PyInstaller 6.22.3 installed into Python312 for this (`pip install pyinstaller`); no C compiler is on this PC, so Nuitka (stronger, actual compiled code) was not an option — PyInstaller only bundles Python bytecode, which existing decompilers can partially recover, so this is a real but not absolute protection.

**What it does NOT solve** (the ask was to hide the source, not to make the tool portable): config.json's absolute paths, the CapCut/capcut-cli/ffmpeg dependency on the destination machine, and the 1.4 GB Whisper model are all unresolved by this build — a receiver still has real setup work. Not committed anywhere by design (build output is outside the repo); the `build-protected.js` script itself is committed and pushed.

Related: [[claude-folder-git-versioning]], [[create-clips-pipeline]], [[create-static-command]].
