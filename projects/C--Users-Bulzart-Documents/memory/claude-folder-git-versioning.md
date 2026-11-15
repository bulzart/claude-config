---
name: claude-folder-git-versioning
description: "~/.claude is a local git repo with Stop/SessionStart auto-commit hooks; allow-list .gitignore keeps Claude Code's own files out"
metadata:
  node_type: memory
  type: project
  originSessionId: eeae7805-53c0-4ecd-8da6-f148caa3f308
  modified: 2026-11-14T03:48:54.476Z
---

Since 2026-10-05, `C:\Users\Bulzart\.claude` is a local git repo (branch main; since 2026-10-15 it has a GitHub remote, `origin` = bulzart/claude-config, pushed manually with `git -C ~/.claude push`: the auto-commit hook only commits) so the user can revert commands, skills, pipelines, hooks, memory and settings to any earlier point.
**CORRECTION 2026-11-13: that remote is PUBLIC, not private** (GitHub API, no login: visibility public, 156 memory notes under projects/*/memory, settings.json, CLAUDE.md and 3,700 other files readable by anyone; checked with a whole-tree scan: no API keys or tokens in it). The working branch is `pc` (tracks origin/pc; main is old). On 2026-11-13 the user said "git push now"; I found it public, did NOT push (12 commits ahead, a plain fast-forward, dry-run worked) and asked whether to push as is or make the repo private first. Before any push of this repo: say it is public and ask.
**UPDATE 2026-11-14: it is PRIVATE again** (GitHub API without a login answers 404; an anonymous `git ls-remote` asks for a user name; the stored login still reads it: origin/pc = feefbec = my local origin/pc). The user presumably made it private after my 11-13 question, and then said "push to git for the claude config repo on pc branch" (an explicit request, 14 commits ahead): a plain `git push origin pc` from `C:\Users\Bulzart\.claude`. Re-check the visibility before each push (API 404 and the anonymous ls-remote failing = private); if it is public again, say so and ask first.

- Hooks in `~/.claude/settings.json` (Stop, SessionStart) run `hooks/autocommit.py`, which commits tracked changes as `auto(<event>): …`.
- `.gitignore` is an allow-list (`/*` then `!/commands/`, `!/skills/`, `!/analyze-then-pick/`, `!/analyze-stack/`, `!/hooks/`, memory dirs, settings.json…). Claude Code's own files (credentials, sessions, transcripts, plugins, skills/synced, caches) are never tracked; run folders, samples, node_modules, `_backups` are excluded.
- How-to for the user lives in `~/.claude/VERSIONING.md`.
- **`loupe/` left this repo on 2026-10-15**: it is its own git repo (history kept via `git subtree split`), origin = private GitHub `bulzart/loupe`; the parent `.gitignore` no longer allow-lists it and the auto-commit hook does NOT cover it, so Loupe changes must be committed and pushed inside `~/.claude/loupe` (its `CLAUDE.md` says so).

**Why:** the user wants every change to their skills/commands/pipelines committed so they can go back in time, but never Claude Code's engine or files that official releases change.

**How to apply:** after a significant change to a pipeline or skill, also make a descriptive commit (with the attribution trailer) instead of relying only on the generic auto-commit. When creating a new top-level folder of the user's own in `~/.claude`, add `!/<folder>/` to `~/.claude/.gitignore`. To revert, use `git -C ~/.claude restore --source <hash> -- <path>`. Related: [[capcut-text-preset-locked]].
- **Never leave backup or scratch copies inside the tracked folders** (`*.before-*`, `.bak`, temp files next to a command, reference or script): the Stop hook commits them. On 2026-10-12 thirteen `.before-*` copies made by patch helpers were committed into `analyze-then-generate/` and `commands/` and had to be removed; keep backups in the session scratchpad (git history is the backup).

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): local repo + auto-commit hooks; allow-list .gitignore; add new user folders to it; never leave backup copies in tracked folders; origin bulzart/claude-config private again (checked 2026-11-14), push branch pc on the user's say
