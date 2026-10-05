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

**Why:** the user wants every change to their skills/commands/pipelines committed so they can go back in time, but never Claude Code's engine or files that official releases change.

**How to apply:** after a significant change to a pipeline or skill, also make a descriptive commit (with the attribution trailer) instead of relying only on the generic auto-commit. When creating a new top-level folder of the user's own in `~/.claude`, add `!/<folder>/` to `~/.claude/.gitignore`. To revert, use `git -C ~/.claude restore --source <hash> -- <path>`. Related: [[capcut-text-preset-locked]].
