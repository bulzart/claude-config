---
name: loupe-web-app
description: "Loupe = the pipeline's local web app (~/.claude/loupe, 127.0.0.1:8787): Higgsfield flag record + generation-miss samples (wrong vs correct image) + QC keeper; STANDING RULE: after every edit to Loupe update Documents/prompts/loupe.txt (user 2026-10-14)"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-14T19:01:33.587Z
---

On 2026-10-14 the user asked for a web app that (1) saves every Higgsfield generation flag (replacing the `caught_flags.html` page, with smarter data about what may have caused the flag), (2) has a "Generation misses" section where they, as admin, pick a pipeline run and a video, describe the miss, mark a second of it with an arrow or circle, pick the fixed version (QC-agent fix, their feedback or a client update), and the app finds the same moment in the correct video and saves ONE image holding the wrong and the correct frame, and (3) lets the QC phase (and only it) read those samples through ONE separate agent that holds the library in its own context and never edits it. Agents reach it with an API key. I named it **Loupe**.

**Where / what:** code `~/.claude/loupe/` (tracked in the ~/.claude git repo via `!/loupe/`; `/loupe/data/` is ignored), `python loupe.py serve` (or `atp.py loupe ensure`, started detached) at `http://127.0.0.1:8787`, localhost only. Python stdlib + SQLite + Pillow + ffmpeg, vanilla-JS UI. The **user sets the admin passphrase themself** at the first open (I must never choose or know it). Keys: `data/keys/pipeline.key` (flags:write, flags:read, runs:read; used by `atp.py caught-flag` and the hooks) and `data/keys/qc.key` (qc:read, flags:read; used by `atp.py qc-consult` / `qc-brief` and the MCP server). The keeper is a separate headless `claude -p` Haiku session (Read tool only, `--strict-mcp-config`, resumed by session id, replaced after 30 turns, deterministic fallback brief); a subagent cannot be the keeper because a sibling's reply goes to the parent session. MCP tools exist (`mcp_server.py`) but are NOT registered (the CLI path is primary); the registration command is in `loupe/README.md`.

**Hooks (settings.json):** `hooks/atp_flag_watch.py` (PostToolUse + PostToolUseFailure on the Higgsfield generation/job/media tools: saves a flag-like raw answer to Loupe as a capture, prints a one-line reminder), `hooks/atp_resume_note.py` (SessionStart compact|resume: names the unfinished run and its `next_skill`), `hooks/atp_read_guard.py` (PreToolUse Read: denies whole-file reads of atp.py, models/index.json, the catalog snapshot, backups). A ledger-guard hook was deliberately NOT added (a false block would stop a paid generation).

**Why:** flags and QC lessons were scattered (an HTML page nobody could use at QC time) and the QC agents had no memory of the admin's own corrected examples; keeping that memory in a separate read-only keeper avoids mixing it into the working agents' context ([[atp-skills-architecture]], context rot).

**How to apply:**
- **Standing instruction (user, 2026-10-14): after EVERY edit to Loupe (code, routes, UI, hooks, keys, the atp.py commands that call it), update `C:\Users\Glaresquare1\Documents\prompts\loupe.txt` in the same sitting** — copy to `loupe.txt.bak-<date>-<why>` first, keep CRLF prose with no headings, keep it true to the code; also keep `loupe/README.md` in step. Same discipline as [[atp-build-prompt-sync]].
- Scripts only gather; the agents decide ([[scripts-gather-agents-decide]]); no niche/brand names in Loupe code ([[no-hardcoded-names-in-scripts]]).
- Keep `loupe/data` out of git; run `python loupe/tests/selftest.py` (36 checks, `--keeper` adds 3) after changes.
- Flags are recorded here now, see [[atp-caught-flags]].
- The keeper also gives sparse planning hints for the first request of a video (`atp.py plan-hints`), see [[atp-sample-hints-delicate]].
