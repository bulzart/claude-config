---
name: create-clips-pipeline
description: "Clip-farming system built 2026-11-12: Twitch Chunk Recorder extension -> cc.py watch (sheets + Whisper) -> /create-clips (research, scan, plan, CapCut builds); locations, rules, and what was not verified"
metadata:
  node_type: memory
  type: project
  originSessionId: e45fa635-1cdc-405a-830c-5be655ad54a5
  modified: 2026-11-12T11:39:03.801Z
---

Built 2026-11-12 on the user's brief (clip farming for Kai Cenat, cQx, Ninja, Speed, Fanum, Adin Ross and similar).
- **Extension** `C:\Users\Bulzart\Documents\twitch-chunk-recorder` (MV3, offscreen engine, own GQL token flow, fMP4 segments joined with the YouTube extension's mp4mux.js, 3-minute MP4 chunks into `Downloads\twitch-chunks\<channel>\<session>\`, chat counts without user names, ad segments skipped, auto-record when live, size cap default 5 GB).
- **Toolkit** `~/.claude/create-clips` (README.md is the contract: paths, rec time, chunk table, file formats). `cc.py watch` makes runs under `C:\Users\Bulzart\Documents\stream-clips\runs\<session>`: sheets every 0.75 s (30 per sheet, frames deleted after each sheet), Whisper medium on CPU int8 (GPU is opt-in: the user's note says the GPU is reserved for FLUX Klein and ACE-Step), per-second timeline, stream.md.
- **Command** `/create-clips <run>` (`~/.claude/commands/create-clips.md`, skills `cc-start`, `cc-profile`, `cc-scan`, `cc-plan`, `cc-produce`, `cc-build-short`, `cc-build-long`, `cc-wrapup`, references in `create-clips/reference/`). Research is SOCIAL not scientific (the user, 2026-11-12): what people say, joke about, hype and clip, about the streamer, the topic (game/release/event) and the people.
- Rules from the user: edit = cuts, captions (non-negotiable), VFX, matching sound effects; religion and superstition avoided; gore/distress/nudity (and personal data) kept and blurred only in the section and region where seen (`cc.py censor`, ffmpeg-made blurred span replaces the span); shorts up to 3 min, long-form about 1 h but never cutting a story in half, count by richness; shorts and long-form built at the same time (up to 4 production agents).
- Findings that shaped it: Twitch segments are fMP4 with EXT-X-MAP (not TS); the playback token lasts about 20 min; anonymous viewers get stitched ads (`Amazon|id` segments with their own init); C: has only ~8 GB free; `capcut add-video` copies media into the draft (never use it, use the MCP); git bash forks fail (PowerShell).
- Not verified: no live Twitch download was run (the permission classifier denied polling a third party's stream); CapCut layouts (`fill` scale/pos, `bg-blur`) not opened in CapCut; the MCP clone/add_video path not run against the real store.

**Why:** the user wants streams turned into posted-ready CapCut projects with agents that understand the streamer and the topic.
**How to apply:** use `cc.py doctor` first; keep processing on CPU unless the user says otherwise; keep chunks read-only; never push to a remote; the Twitch extension and the toolkit are not in git (the toolkit is under `~/.claude/create-clips`, tracked by the auto-commit hook).

Related: [[pc-pipeline-tooling]], [[awl-sound-effects-folder]], [[analyze-with-loupe-command]], [[claude-folder-git-versioning]]
