---
name: pc-pipeline-tooling
description: "This PC (branch pc of claude-config) got the full /analyze-with-loupe tooling on 2026-11-05: Python312 modules + whisper, CapCut template, Loupe keeper via the real claude.exe, elevenlabs MCP renamed; Higgsfield still blocked by Avast (user's call)"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-06T07:09:10.084Z
---

Set up 2026-11-05 (user: "install that tooling here too and anything else needed for the pipeline to work correctly as intended"). `awl.py doctor` all green; `awl.py static check` ready except the OpenAI key (the user sets it).
- Tooling Python `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe` 3.12.10: pypdf, Pillow, numpy, requests, librosa, rapidocr-onnxruntime, faster-whisper 1.2.1 with ctranslate2 4.8.5 and **av 18.1.0: keep `av<19`** (PyAV 19 removed `metadata_errors`, which faster-whisper 1.2.1 still passes to `av.open`, so every transcription failed). setuptools 80.10.2 stays from the old ctranslate2. Whisper models small, base, tiny cached in the HF cache.
- **No pip-system-certs in Python312** (removed 2026-11-05): its `.pth` imported pip's network code at every Python start (~2.7 s), which slowed every Claude Code hook (all run on Python312) and failed t03's 3.5 s `loupe ensure` timing check. Replaced by `site-packages\_truststore_lazy.py` + `truststore_lazy.pth`: truststore is injected right after the first import of requests, urllib3, httpx or aiohttp (requests through Avast needs it: SSLCertVerificationError without). A bare start is 0.08 s, `awl.py --help` 0.31 s. pip 25 and huggingface_hub 2.4 need nothing.
- CapCut template `_analyze-stack-template` built here with capcut-cli (`init --ratio 9:16`, which seeded the CapCut 9.7 skeleton from the user's empty draft `1105`; two 2 s clips, a tone and a text in its own `assets\`; registered). Never delete or edit it. A scratch run of the whole CapCut path passed (clone empty, capcut-prep, add video, image, audio and text, save, capcut-repair with preview).
- Loupe's keeper needs a real `claude.exe` first on PATH. The npm `claude.cmd` shim goes through cmd.exe, which caps a command at 8191 characters; the keeper's command is ~21 000 (its role text), so it failed with "The command line is too long" and the picture readings with "The system cannot find the file specified". Fix: the user PATH has `C:\Users\Bulzart\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin` right before `...\AppData\Roaming\npm`. 22/22 samples read, keeper in sync on Opus 5.5. The Loupe admin passphrase is not set yet (the user sets it on the page).
- MCP: `ElevenLabs` re-registered as `elevenlabs` (the name the pipeline's tools use) with `SSLKEYLOGFILE=""`. Its stored API key is refused ("Invalid API key"): the user must put in a valid one.
- FFmpeg: only the Gyan.FFmpeg full build 9.0.1 (Essentials uninstalled; the full build has the whisper filter).
- capcut-cli stays 0.25.0 (global npm). Checked 2026-11-06: 0.32.0 still writes neither the `local_material_id` links nor the caption strokes, so the toolkit writes both itself (`T capcut-repair` link step, `T capcut-font`); 0.31 added `loudness --target -14` (not needed: the narration carries the target). This PC's CapCut is 9.7 (`%LOCALAPPDATA%\CapCut\Apps\9.7.1.4203`): it opens local clips by `local_material_id`. Never `capcut lint --fix` on a pipeline project (it also shortens texts over 7 s, trims captions, copies all media into the draft).
- Remote HTTP MCP servers (higgsfield and the plugin ones) fail because of Avast: see [[avast-https-scanning-breaks-tls]].

**Why:** these were the gaps between this PC and the main PC; each one made a pipeline step fail or silently fall back.

**How to apply:**
- If the keeper fails again with "command line is too long", check that the PATH folder above still holds `claude.exe` (an npm update could move it), then restart Loupe from a shell that has the new PATH (stop the process on port 8787, `awl.py loupe ensure`).
- Never `pip install -U av` past 18 in Python312 until faster-whisper stops passing `metadata_errors`.

Related: [[local-ai-installs]], [[loupe-web-app]], [[analyze-with-loupe-command]]
