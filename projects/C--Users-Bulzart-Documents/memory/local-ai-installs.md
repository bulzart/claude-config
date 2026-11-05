---
name: local-ai-installs
description: "Qwen3-TTS 1.7B (3 variants) + ACE-Step 1.5 installed on this PC 2026-11-05 under Documents\\AI; this is the /analyze-with-loupe \"Static PC\"; AI jobs must run under the memory guard (two Windows crashes)"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-05T10:29:44.762Z
---

Installed 2026-11-05 in `C:\Users\Bulzart\Documents\AI\` (user: file generation is all that matters, no web UI needed):
- Qwen3-TTS: models `Qwen3-TTS\models\Qwen3-TTS-12Hz-1.7B-{CustomVoice,VoiceDesign,Base}` (bf16), also hardlinked into the HF cache (`~\.cache\huggingface\hub\models--Qwen--...\snapshots\<commit>`) so repo ids resolve offline. Official env `Qwen3-TTS\.venv` (qwen-tts 0.1.1, torch 2.7.1+cu128, py3.11, sdpa, pip-system-certs). Fast env `Qwen3-TTS\fast\.venv` (faster-qwen3-tts 0.5.4 CUDA graphs, transformers==5.15.1 pinned; ~8x faster: 1.6-2x real time vs ~0.25x).
- ACE-Step 1.5: `ACE-Step-1.5\` (uv sync --locked, py3.11), checkpoints incl. 0.6B LM (RTX 3060 = tier4). `.env` set.
- Pipeline wiring (User env vars): `AWL_TTS_PYTHON` = `AI\tools\qwen_tts_python.cmd` (runs the FAST venv's python), `AWL_MUSIC_PYTHON` = `AI\tools\acestep_python.cmd` (both inside `AI\tools\memguard.py`), `AWL_MUSIC_ROOT` = `AI\ACE-Step-1.5`. `T static check`: tts + music ready (2026-11-05).
- Fast engine in the pipeline (user 2026-11-05, "yes switch ... and verify the seeds"): `scripts/tts_worker.py` `engine_for()` uses faster-qwen3-tts on CUDA bf16 when importable, graphs captured at load before any seed, answers carry `engine`; `AWL_TTS_ENGINE=qwen-tts` forces qwen-tts. Verified: same seed bit-identical in one call and across calls on either engine; the two engines give different takes for one seed. §9 + README carry the guard and engine notes.
- **PENDING on the main PC:** the build prompt `Documents/prompts/analyze-with-loupe.txt` is not on this PC; add there the same two notes (fast engine optional + seeds per engine; keep a guarded .cmd in AWL_TTS_PYTHON / AWL_MUSIC_PYTHON) per its rules (CRLF, no headings, .bak first).
- This PC has no pipeline tooling Python (3.12 + Pillow, NumPy, requests, faster-whisper) and no `python` on PATH: a Static run here needs it first (tests ran in a temporary `uv run --with` env). Qwen web launchers deleted 2026-11-05 (user: not needed).

**Why the guard:** starting ACE-Step's Gradio UI froze Windows twice (forced restarts). Cause: Windows commit limit (RAM + page file) was 24.1 GB with 20.8 GB already used by open apps; any model load commits ~13 GB (measured: Qwen worker 13.2 GB, ACE music worker 13.1 GB, while real free RAM stayed 4.5+ GB). memguard = kernel job cap (16 GB) + watchdog (stop if free RAM < 1 GB or free commit < 3 GB); it never changes output quality.

**How to apply:**
- Never start ACE-Step's `start_gradio_ui.bat` / `uv run acestep` UI unguarded; run any model job via memguard. Don't repoint AWL_*_PYTHON straight at python.exe (that removes the guard).
- Windows Smart App Control is ON: unsigned or brand-new native wheels get blocked ("An Application Control policy has blocked this file": flash-attn, pandas 3.1.1). Keep versions pinned; SDPA, not flash-attn.
- The agent shell has `NoDefaultCurrentDirectoryInExePath=1`: call .bat/.cmd by full path.
- Git Bash forks can fail under memory pressure: prefer PowerShell.

Related: [[avast-https-scanning-breaks-tls]], [[analyze-with-loupe-command]]
