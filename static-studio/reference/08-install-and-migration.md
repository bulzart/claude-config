# 08 — Install and migrate without damaging the existing Claude Code setup

## What has changed

This is a **separate static-only release** extracted from the user-supplied multi-mode `claude-config-pc.zip`. It preserves the same **command name** `/analyze-with-loupe` but intentionally does **not** preserve its old mode router, non-static phase agents, site/browser inspection code, video-to-video generators, model-menu prompts, legacy automated workflows, old aspect assumptions, or other commands. The command reads only the new `static-studio` directory; it does not route to the old `analyze-with-loupe` directory. The old configuration is left untouched so unrelated work is not erased. Prior run directories are **not automatically rewritten**; they may be read using the old setup if needed. New runs use a new explicit state schema.

## Safe install on Windows

1. Back up `C:\Users\<you>\.claude\commands\analyze-with-loupe.md` and any custom local modifications to that command. No need to move or delete existing media, runs or presets.
2. Extract this ZIP's `.claude/commands/analyze-with-loupe.md` to `%USERPROFILE%\.claude\commands\analyze-with-loupe.md` (replace only that command after backing it up). Extract the whole `.claude/static-studio/` directory to `%USERPROFILE%\.claude\static-studio\`.
3. Check that `python`, `ffmpeg` and `ffprobe` are discoverable in the shell where Claude Code runs. For local Whisper, install or reuse `faster-whisper` in that **same Python environment**; select model, device and compute type appropriate to GPU/RAM. Use `python ...\static_core.py doctor` to see what's installed. `av-profile` (watch sheets and the narration/picture measurements) and `narration-measure`'s delivery measurement also need `numpy`, `opencv-python`, `librosa`, `soundfile` and `Pillow` in the same environment; `doctor` reports `av_profile_ready`.
4. If your Claude Code shell is PowerShell rather than Git Bash, replace the command's one `python "$HOME/..."` convention with the correct `python "$env:USERPROFILE\\.claude\\static-studio\\scripts\\static_core.py"` path in the command. Python accepts Windows paths; quote spaces.
5. Confirm `ELEVENLABS_API_KEY` only via terminal environment/secret manager, not an on-disk script. OpenAI Images, CapCut MCP/CLI and local generators are optional and must be configured on the PC; this ZIP does not impersonate an available service or ship models.
6. Run `/analyze-with-loupe C:\path\to\references` in Claude Code. A new run is stored under `.claude/static-studio/runs/`, separate from every prior project.

**Nothing is silently deleted.** Once you've run the new command successfully, old mode-specific resources can be archived separately if desired. Don't delete old `~/.claude/skills/awl-*`, legacy scripts or run folders until you confirm no *other* command uses them; this release doesn't require them but they may be shared by unrelated projects. Avoid merging this directory into the old one: use **static-studio** as the single active root for the new command.

## Assets carried forward

`static_core.py` and `openai_images_worker.py` are new, designed specifically for reference mining, Whisper, niche cohorts, duration lock, script/beat coverage, credit-conscious ElevenLabs, audio integrity and export gates. `image_worker.py`, `music_worker.py` and `flux3_upsampler_prompts.json` are the *static-specific* advanced local image/music helpers from the user-supplied configuration, kept separate so they only run when their native environments are actually installed. Large model weights, fonts, user keys and unrelated phase/config files are intentionally excluded. Use valid licensed local fonts already installed; never distribute proprietary font files as part of the migration.

## What the CLI does not claim to do

The Python utility is **not an AI editorial agent**, an online content crawler, an image API key manager or CapCut itself. Claude Code provides reasoning, browsing for independent research, concept writing and connected generation/editing tools. Native Whisper requires `faster-whisper` installed and processing time. `--full-fps` may require many gigabytes. The command does not auto-download or use reference clips as final footage. It cannot guarantee virality, objectively measure a viewer's emotion from a file, or assess facts without source research. Provider balance, supported model IDs and prices can change; confirm before paid generation.

## Troubleshooting

- `scan` returns no videos: check the folder path, file extensions, nested folders, and FFmpeg installation.
- `prepare` fails: check actual error; if Whisper isn't installed, install it, then rerun. Do not pass `--skip-whisper` silently in an audio-driven analysis; it is only for debugging or genuinely silent sources.
- `cohorts` complains about missing cards: analyze the sources and create `20-analysis/cards/V###.json`; don't invent classifications to satisfy the checker.
- `length` rejects Standard: choose at least two same-niche/form **long-form** videos with comparable durations, or use a user-selected custom long-form runtime.
- `plan-check` rejects short narration: research and add substantive beats; don't dilute the audio pace to force the length.
- `tts` returns partial: stop. Preserve chunks and resolve credits/errors before returning to production.
- `audio-check` fails on duration: do not proceed to pictures or edit; recalibrate planned WPM or rewrite/record affected passages.
- `timeline-check` fails: fix missing visual/audio coverage in the real CapCut project; a planning JSON cannot substitute for clips in the draft.
- `export-check` fails or MP4 missing: export properly, inspect last frame, silence, resolution and actual duration. Report `project-only` until real export is available.
