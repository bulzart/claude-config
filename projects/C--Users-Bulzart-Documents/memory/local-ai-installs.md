---
name: local-ai-installs
description: "Qwen3-TTS 1.7B (3 variants) + ACE-Step 1.5 (2026-11-05) and FLUX 3 Image Klein int8 in a ComfyUI portable (2026-11-06) on this PC under Documents\\AI; this is the /analyze-with-loupe \"Static PC\"; AI jobs must run under the memory guard (two Windows crashes)"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-06T04:07:57.331Z
---

Installed 2026-11-05 in `C:\Users\Bulzart\Documents\AI\` (user: file generation is all that matters, no web UI needed):
- Qwen3-TTS: models `Qwen3-TTS\models\Qwen3-TTS-12Hz-1.7B-{CustomVoice,VoiceDesign,Base}` (bf16), also hardlinked into the HF cache (`~\.cache\huggingface\hub\models--Qwen--...\snapshots\<commit>`) so repo ids resolve offline. Official env `Qwen3-TTS\.venv` (qwen-tts 0.1.1, torch 2.7.1+cu128, py3.11, sdpa, pip-system-certs). Fast env `Qwen3-TTS\fast\.venv` (faster-qwen3-tts 0.5.4 CUDA graphs, transformers==5.15.1 pinned; ~8x faster: 1.6-2x real time vs ~0.25x).
- ACE-Step 1.5: `ACE-Step-1.5\` (uv sync --locked, py3.11), checkpoints incl. 0.6B LM (RTX 3060 = tier4). `.env` set.
- Pipeline wiring (User env vars): `AWL_TTS_PYTHON` = `AI\tools\qwen_tts_python.cmd` (runs the FAST venv's python), `AWL_MUSIC_PYTHON` = `AI\tools\acestep_python.cmd` (both inside `AI\tools\memguard.py`), `AWL_MUSIC_ROOT` = `AI\ACE-Step-1.5`. `T static check`: tts + music ready (2026-11-05).
- Fast engine in the pipeline (user 2026-11-05, "yes switch ... and verify the seeds"): `scripts/tts_worker.py` `engine_for()` uses faster-qwen3-tts on CUDA bf16 when importable, graphs captured at load before any seed, answers carry `engine`; `AWL_TTS_ENGINE=qwen-tts` forces qwen-tts. Verified: same seed bit-identical in one call and across calls on either engine; the two engines give different takes for one seed. §9 + README carry the guard and engine notes.
- **FLUX 3 Image Klein int8 (2026-11-06, user: "install flux.3 image klein int8 too", then wire it into Static):** ComfyUI 0.44 Windows portable in `AI\ComfyUI_windows_portable\` (Python 3.13, torch 2.14.1+cu130, comfy-kitchen 0.2.40 CUDA backend: int8_tensorwise and asym_w4a8_int8 run natively on the 3060). Models from the gated `black-forest-labs/flux-3-image-klein-comfy` (FLUX Kommunity License accepted by the user; HF login `bulzarti` via `hf auth login` OAuth, token in `~\.cache\huggingface\token`): int8-convrot transformer, int8 Qwen3-VL-4B text encoder, w4a8 prompt upsampler, flux2-vae (17.8 GB in `ComfyUI\models\`). `AWL_IMAGE_PYTHON` = `AI\tools\flux3_python.cmd` (memguard cap 16 GB like the others). **Windows (WDDM) charges GPU memory to the process commit 1:1** (6 GB CUDA tensor = +6.0 GB, measured): that is why every GPU job here commits 13-15 GB while RAM stays free. Klein therefore runs ComfyUI with `--reserve-vram 5` (`config static.klein.reserve_vram_gb`): peak 11.8 GB instead of ~15 GB at 1216x2160, same speed, identical pixels; without it the guard stopped a run when apps were open (free commit 16.8 GB at start), `AWL_IMAGE_ROOT` = the portable folder. Worker `~/.claude/analyze-with-loupe/scripts/image_worker.py`: private ComfyUI per call, BFL's own int8 workflow settings (alpha 16 via ModelSamplingFlux, 16 steps euler/simple, greedy upsampler), caption → POST /free → image. Measured: ~70 s per 1216x2160 still, ~90 s with a reference, 47 s at 1 MP; same seed = identical pixels across processes. Never run ComfyUI's `update_comfyui_and_python_dependencies.bat` untested; never `--disable-dynamic-vram` (fills real RAM; the guard stopped it).
- **PENDING on the main PC:** the build prompt `Documents/prompts/analyze-with-loupe.txt` is not on this PC; add there per its rules (CRLF, no headings, .bak first): the two TTS notes (fast engine optional + seeds per engine; keep a guarded .cmd in AWL_TTS_PYTHON / AWL_MUSIC_PYTHON) and the Static images choice `api|klein|prompts` (FLUX 3 Klein through image_worker.py, AWL_IMAGE_PYTHON + AWL_IMAGE_ROOT, config static.klein).
- The pipeline tooling Python (Python312 with all modules) was installed later the same day: see [[pc-pipeline-tooling]]. Qwen web launchers deleted 2026-11-05 (user: not needed).

**Why the guard:** starting ACE-Step's Gradio UI froze Windows twice (forced restarts). Cause: Windows commit limit (RAM + page file) was 24.1 GB with 20.8 GB already used by open apps; any model load commits ~13 GB (measured: Qwen worker 13.2 GB, ACE music worker 13.1 GB, while real free RAM stayed 4.5+ GB). memguard = kernel job cap (16 GB) + watchdog (stop if free RAM < 1 GB or free commit < 3 GB); it never changes output quality.

**How to apply:**
- Never start ACE-Step's `start_gradio_ui.bat` / `uv run acestep` UI unguarded; run any model job via memguard. Don't repoint AWL_*_PYTHON straight at python.exe (that removes the guard).
- Windows Smart App Control was ON and blocked unsigned or brand-new native wheels ("An Application Control policy has blocked this file": flash-attn, pandas 3.1.1, ctranslate2 4.8.5). The user turned it OFF on 2026-11-05 (it cannot be turned back on without a Windows reset). The pins stay as they are (pandas 2.3.3, SDPA rather than flash-attn) because they are tested.
- The agent shell has `NoDefaultCurrentDirectoryInExePath=1`: call .bat/.cmd by full path.
- Git Bash forks can fail under memory pressure: prefer PowerShell.

Related: [[avast-https-scanning-breaks-tls]], [[analyze-with-loupe-command]]
