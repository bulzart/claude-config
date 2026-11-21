---
name: sam-audio-base-install
description: "2026-11-21: Meta SAM Audio Base installed in Documents\\AI\\sam-audio (own venv); the loading fixes it needs on this PC; measured vs Demucs"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-21T19:31:47.556Z
---

The user's Hugging Face access to facebook/sam-audio-base (and -small) was approved 2026-11-21 (account bulzarti, token already on this PC; Avast breaks
the venv's `hf` CLI TLS: use huggingface_hub with `truststore.inject_into_ssl()`). Checkpoint 7,725,405,659 bytes, SHA-256 verified, in the HF cache.
Environment: `C:\Users\Bulzart\Documents\AI\sam-audio\.venv` (Python 3.12, torch 2.7.1+cu128, official sam_audio from `...\sam-audio\src`, dacvae and
perception_models@unpin-deps from `...\deps`, xformers 0.0.31.post1, accelerate); ACE-Step's venv untouched. Runner: `create-clips\scripts\sam_separate.py`.

**Why (the loading fixes, all measured):** GPU memory counts as committed memory on Windows: the official torch.load (and an mmap) reached 17.6 GB commit,
so the runner streams the checkpoint one tensor at a time into the GPU model; the rerankers and span predictor are off via official config overrides;
the unused vision encoder (671 M params) is dropped after the strict load (moving it to the CPU cost 2.4 GB); torchcodec has no Windows wheel for torch
2.7: a refusing stand-in in `...\sam-audio\shims`, put on sys.path only AFTER transformers is imported; fp32 20 s at once ran out of GPU memory, 10 s
windows fit; expandable_segments is not supported on Windows. Always under `Documents\AI\tools\memguard.py` ([[local-ai-installs]]); the music step
unloads its own Whisper first, GPU lease 10 GB.

**How to apply:** measured (bench `...\stream-clips\validation\separation-bench-20261121`, listening files in `listen\`): load 9-11 s, peak 8.3 GB, about
34 s per minute of audio. Talk over a sung song: SAM "man speaking" via stereo mask leaves the song 20 dB down (voice band 17) vs Demucs 13 (10), words
kept alike; "music playing" removal eats his words; anchors weaker; Demucs better for laughs, instrumentals and song-only stretches. So: escalation only
([[create-clips-music-isolation]]). Small and Large not installed. bfloat16 (measured 2026-11-21): 5.3 GB peak instead of 8.3 but 4-5 dB less song removed under talk (B: -15.9 vs -20.1 dB): NEVER used: the user, 2026-11-22, "always use the full precision" (the retry was removed; a memory-guard stop leaves the span UNRESOLVED, original kept, with the reason). Free commit on this PC fell to about 12 GB late in the day: fp32 SAM (about 11.7 GB) was stopped twice by the guard. 2026-11-22 (user: "edit any caps if possible and works too"): `music.sam.memguard_limit_gb` 13 -> 16 GB (the guard's Windows floors, 1.0 GB free commit and 0.8 GB free RAM, unchanged); fp32 on a 4.6-min span went past 13.06 GB, then ran with the 16 GB cap (GPU peak 8.3 GB, 35 s per audio minute). DBS-TIGER-DnR (3-stem) tested and NOT adopted (keeps game no better than SAM's music removal while removing less song; real-stream singer left -5 to -9 dB); its venv `Documents\AI\dnr-sep`. MVSep DnR v3 weights are not published.
