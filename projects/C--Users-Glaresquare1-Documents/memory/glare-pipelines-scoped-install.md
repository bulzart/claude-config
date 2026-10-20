---
name: glare-pipelines-scoped-install
description: "Glare team repo (harperdogpound/ai-video-pipelines) installed 2026-10-20 scoped to ~/glare-work; never run its setup.sh here, it clobbers ~/.claude"
metadata:
  node_type: memory
  type: project
  originSessionId: ac68e0f5-a378-44e3-aed7-657a1f5d1e41
  modified: 2026-10-20T17:32:36.702Z
---

Glare video pipelines: clone at `~/glare-factory`, installed 2026-10-20 **scoped to `~/glare-work`** (user: "do not ruin our current pipelines ... claude memory and structure ... without making anything fail or mix").

- Rules: `~/glare-work/CLAUDE.md` (= repo CONSTITUTION.md) + `~/glare-work/CLAUDE.local.md` (Windows overrides). Skills: `~/glare-work/.claude/skills/` (25 glare-* + 38 vendor). Load only when claude is started in `~/glare-work/<project>` (verified: 25 glare skills there, 0 in Documents).
- Setup/update: `cd ~/glare-factory && git pull --ff-only && bash ~/glare-work/glare-setup.sh`. **Never run the repo's `setup.sh`**.

**Why:** setup.sh overwrites `~/.claude/CLAUDE.md` with the constitution ("never work on non-Glare work", "never use the Higgsfield upscaler") and `rm -rf`s 16 global skills (hyperframes*, media-use, ...) that differ from the vendored copies.

**How to apply:** never put Glare files in `~/.claude`. Repo is macOS-only: doctor's `macOS` + `brew` checks always FAIL on this PC (accepted by the user). Added for it: gh (user scope), whisper-cli at `%LOCALAPPDATA%\Programs\whisper-cpp` (appended to user PATH), model `~/.cache/whisper/ggml-base.en.bin`, `python3.exe` copy in Python312. Doctor needs `PYTHONUTF8=1`. Personal skills win name clashes, so Glare sessions use the user's hyperframes*/media-use versions.
