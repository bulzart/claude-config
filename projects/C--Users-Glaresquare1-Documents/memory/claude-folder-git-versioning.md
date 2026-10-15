---
name: claude-folder-git-versioning
description: "~/.claude is a local git repo with Stop/SessionStart auto-commit hooks; allow-list .gitignore keeps Claude Code's own files out"
metadata:
  node_type: memory
  type: project
  originSessionId: eeae7805-53c0-4ecd-8da6-f148caa3f308
  modified: 2026-10-05T21:13:29.651Z
---

Since 2026-10-05, `C:\Users\Glaresquare1\.claude` is a local git repo (branch main, no remote) so the user can revert commands, skills, pipelines, hooks, memory and settings to any earlier point.

- Hooks in `~/.claude/settings.json` (Stop, SessionStart) run `hooks/autocommit.py`, which commits tracked changes as `auto(<event>): …`.
- `.gitignore` is an allow-list (`/*` then `!/commands/`, `!/skills/`, `!/analyze-then-pick/`, `!/analyze-stack/`, `!/hooks/`, memory dirs, settings.json…). Claude Code's own files (credentials, sessions, transcripts, plugins, skills/synced, caches) are never tracked; run folders, samples, node_modules, `_backups` are excluded.
- How-to for the user lives in `~/.claude/VERSIONING.md`.
- **`loupe/` left this repo on 2026-10-15**: it is its own git repo (history kept via `git subtree split`), origin = private GitHub `bulzart/loupe`; the parent `.gitignore` no longer allow-lists it and the auto-commit hook does NOT cover it, so Loupe changes must be committed and pushed inside `~/.claude/loupe` (its `CLAUDE.md` says so).

**Why:** the user wants every change to their skills/commands/pipelines committed so they can go back in time, but never Claude Code's engine or files that official releases change.

**How to apply:** after a significant change to a pipeline or skill, also make a descriptive commit (with the attribution trailer) instead of relying only on the generic auto-commit. When creating a new top-level folder of the user's own in `~/.claude`, add `!/<folder>/` to `~/.claude/.gitignore`. To revert, use `git -C ~/.claude restore --source <hash> -- <path>`. Related: [[capcut-text-preset-locked]].
- **Never leave backup or scratch copies inside the tracked folders** (`*.before-*`, `.bak`, temp files next to a command, reference or script): the Stop hook commits them. On 2026-10-12 thirteen `.before-*` copies made by patch helpers were committed into `analyze-then-generate/` and `commands/` and had to be removed; keep backups in the session scratchpad (git history is the backup).
