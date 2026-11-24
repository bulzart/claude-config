# 08 — Install and migrate without damaging the existing Claude Code setup

## What has changed

This is a **separate static-only release** extracted from the user-supplied multi-mode `claude-config-pc.zip`. It preserves the same **command name** `/analyze-with-loupe` but intentionally does **not** preserve its old mode router, non-static phase agents, site/browser inspection code, video-to-video generators, model-menu prompts, legacy automated workflows, old aspect assumptions, or other commands. The command reads only the new `static-studio` directory; it does not route to the old `analyze-with-loupe` directory. The old configuration is left untouched so unrelated work is not erased. Prior run directories are **not automatically rewritten**; they may be read using the old setup if needed. New runs use a new explicit state schema.

## Safe install on Windows

1. Back up `C:\Users\<you>\.claude\commands\analyze-with-loupe.md` and any custom local modifications to that command. No need to move or delete existing media, runs or presets.
2. Extract this ZIP's `.claude/commands/analyze-with-loupe.md` to `%USERPROFILE%\.claude\commands\analyze-with-loupe.md` (replace only that command after backing it up). Extract the whole `.claude/static-studio/` directory to `%USERPROFILE%\.claude\static-studio\`.
3. Check that `python`, `ffmpeg` and `ffprobe` are discoverable in the shell where Claude Code runs. For local Whisper, install or reuse `faster-whisper` in that **same Python environment**; Whisper runs as medium on the GPU (cuda, float16), always; the CPU only with `--cpu-approved` (`static_core.py doctor --whisper` checks it). Use `python ...\static_core.py doctor` to see what's installed. `av-profile` (watch sheets and the narration/picture measurements) and `narration-measure`'s delivery measurement also need `numpy`, `opencv-python`, `librosa`, `soundfile` and `Pillow` in the same environment; `doctor` reports `av_profile_ready`.
4. If your Claude Code shell is PowerShell rather than Git Bash, replace the command's one `python "$HOME/..."` convention with the correct `python "$env:USERPROFILE\\.claude\\static-studio\\scripts\\static_core.py"` path in the command. Python accepts Windows paths; quote spaces.
5. Confirm `ELEVENLABS_API_KEY` only via terminal environment/secret manager, not an on-disk script. The stills are made with FLUX 3 Image Klein int8 on this PC, the default and primary image engine (`image_worker.py`, run with `C:\Users\Bulzart\Documents\AI\tools\flux3_python.cmd`: ComfyUI's embedded Python inside the memory guard, its model files in that ComfyUI install); OpenAI Images only on the user's explicit choice, recorded with `static_core.py image-engine`, and never as a fallback when FLUX fails. The CapCut MCP/CLI and ACE-Step (music) must be configured on the PC too; this ZIP does not impersonate an available service or ship models.
6. Run `/analyze-with-loupe C:\path\to\references` in Claude Code. A new run is stored under `.claude/static-studio/runs/`, separate from every prior project.

**Nothing is silently deleted.** Once you've run the new command successfully, old mode-specific resources can be archived separately if desired. Don't delete old `~/.claude/skills/awl-*`, legacy scripts or run folders until you confirm no *other* command uses them; this release doesn't require them but they may be shared by unrelated projects. Avoid merging this directory into the old one: use **static-studio** as the single active root for the new command.

## Assets carried forward

`static_core.py` and `openai_images_worker.py` are new, designed specifically for reference mining, Whisper, niche cohorts, duration lock, script/beat coverage, credit-conscious ElevenLabs, audio integrity and export gates. `image_worker.py` (FLUX 3 Image Klein int8: the default and primary image engine, not an optional extra), `music_worker.py` (ACE-Step) and `flux3_upsampler_prompts.json` are the *static-specific* local image and music workers from the user-supplied configuration; each runs in its own native environment (ComfyUI's embedded Python for FLUX, ACE-Step's own for music), which must be installed. When FLUX cannot run, report its error and stop: `openai_images_worker.py` is used only on the user's explicit choice (`image-engine`), never as a fallback. Large model weights, fonts, user keys and unrelated phase/config files are intentionally excluded. Use valid licensed local fonts already installed; never distribute proprietary font files as part of the migration.

## What the CLI does not claim to do

The Python utility is **not an AI editorial agent**, an online content crawler, an image API key manager or CapCut itself. Claude Code provides reasoning, browsing for independent research, concept writing and connected generation/editing tools. Native Whisper requires `faster-whisper` installed and processing time. `--full-fps` may require many gigabytes. The command does not auto-download or use reference clips as final footage. It cannot guarantee virality, objectively measure a viewer's emotion from a file, or assess facts without source research. Provider balance, supported model IDs and prices can change; confirm before paid generation.

## Sharing the GPU

FLUX 3 Image Klein, ACE-Step and Whisper jobs each take a GPU lease while they need the card, so the PC's other GPU users see them, and a program that keeps an idle model on the GPU lets it go while they need the memory. The lease is a file named `create-video-<kind>-<pid>` that says how long the job expects to hold the card (`expected_s`: FLUX 60 s plus 45 s per 1280x720 image, longer for a larger canvas; ACE-Step 90 s plus 3 s per second of music; Whisper 60 s plus its file's length divided by 6). Its folder is the PC's shared one (`~/.claude/create-clips/data/gpu`) only when that folder already exists, and nothing is created there; otherwise `static-studio/data/gpu`. `STATIC_GPU_LEASE_DIR` overrides it.

How long a job waits follows who holds the card, never one fixed time for every job: an earlier GPU job until it ends, or until it has run twice the time it declared (it is then treated as stuck; a holder that declares none, until its lease's time to live runs out); a program that keeps a Whisper model loaded on the card (it says so in `whisper.json` beside the leases) up to 75 s, since it looks every 10 s; memory held outside the leases only 15 s, unless it keeps coming back. Whisper waits only before its model loads. A job's `gpu_wait_s` only caps the wait; there is no default. First come, first served: a job waits only for leases taken before its own, so two jobs never wait for each other. Then the job goes ahead: a lease never changes the device, the model or the precision. The card's real size is read (nvidia-smi; this PC: an RTX 3060, 12,288 MB) and reported as `card_mb`; the memory guard's 16 GB caps the process memory of FLUX and ACE-Step (RAM and page file), not the card.

## Troubleshooting

- `scan` returns no videos: check the folder path, file extensions, nested folders, and FFmpeg installation.
- `prepare` fails: check actual error; if Whisper isn't installed, install it, then rerun. Do not pass `--skip-whisper` silently in an audio-driven analysis; it is only for debugging or genuinely silent sources, and needs `--reason`.
- `cohorts` complains about missing cards: analyze the sources and create `20-analysis/cards/V###.json`; don't invent classifications to satisfy the checker.
- `length` rejects Standard: choose at least two same-niche/form **long-form** videos with comparable durations, or use a user-selected custom long-form runtime.
- `plan-check` rejects short narration: research and add substantive beats; don't dilute the audio pace to force the length.
- `tts` returns partial: stop. Preserve chunks and resolve credits/errors before returning to production.
- `audio-check` fails on duration: do not proceed to pictures or edit; recalibrate planned WPM or rewrite/record affected passages.
- `timeline-check` fails: fix missing visual/audio coverage in the real CapCut project; a planning JSON cannot substitute for clips in the draft.
- `export-check` fails or MP4 missing: export properly, inspect last frame, silence, resolution and actual duration. Report `project-only` until real export is available.
