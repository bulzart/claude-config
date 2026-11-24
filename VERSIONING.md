# ~/.claude version history

This folder is a git repository that keeps the history of **your**
customizations: commands, skills, pipelines (`analyze-then-pick`, `analyze-stack`), hooks,
memory files and `settings.json`. The Loupe web app (`loupe/`) is no longer tracked here: it is its own git repository with a private GitHub remote (`bulzart/loupe`); see `loupe/CLAUDE.md`.

## What is tracked
Only what `.gitignore` allow-lists. Claude Code's own files are never committed: credentials,
sessions (live-process registries with their keys) and transcripts, history, caches, plugin code and marketplace clones, synced claude.ai skills,
telemetry, update state. Plugin settings are tracked: `plugins/installed_plugins.json`, `known_marketplaces.json` and `plugin-directory-bindings.json`. Run folders, samples, `node_modules` and backups are also left out.
A new top-level folder is reported once and stays untracked until you add `!/<folder>/` to
`.gitignore`.

## When commits happen
Claude Code hooks in `settings.json` run `hooks/autocommit.py`:
- **Stop**: after every Claude turn, whatever changed is committed as `auto(Stop) [area]: …`.
- **SessionStart**: changes made outside Claude (manual edits, installers) are committed as
  `auto(SessionStart) [area]: …`.
Files over 25 MB are left out and reported. The hook only commits; it never pushes.

**One commit per area.** A checkpoint is split into one commit per area, so a commit never mixes two
projects. The area is the top-level folder (`commands`, `hooks`, `skills`, `static-studio`, `create-clips`, …),
memory notes (`projects/*/memory/`) are `memory`, and the files at the top (`settings.json`, `CLAUDE.md`,
`.gitignore`, …) are `config`. The area is in the subject, so one project's commits can be picked out later:
`git -C ~/.claude log --oneline --grep "\[static-studio\]"`.

**Secret scan.** Before committing, each changed text file is checked for things that look like real
credentials: API keys (`sk-…`), GitHub, Hugging Face and AWS keys, private-key blocks, and a long random value
given to a key name such as `ELEVEN_API_KEY` or `CC_SOURCE_KEY`. A file that matches is not committed; the
hook's message names the file and the kind of match (never the value) on every turn until the secret is taken
out of the file, and everything else is committed as usual. Encrypted `.enc` files and binary files are not
checked, and placeholders such as `<your key>` do not count. Tests: `hooks/test_autocommit.py`.

## GitHub copy
The repo has a **private** remote, `origin` = `github.com/bulzart/claude-config` (branch `main`), created 2026-10-15 so the
customizations survive a lost or reinstalled machine. Pushing is manual: `git -C ~/.claude push`. The `.gitignore`
allow-list decides what can ever reach it, so credentials, sessions, transcripts, history and Claude Code's own files cannot.
The Loupe web app (`loupe/`) is a separate repository (`bulzart/loupe`) and is not part of this one.

## Look back in time
```
git -C ~/.claude log --oneline -20
git -C ~/.claude log --oneline -- commands/analyze-then-pick.md
git -C ~/.claude show <hash> --stat
git -C ~/.claude diff <hash> -- analyze-then-pick/
```

## Revert
- One file back to an earlier version:
  `git -C ~/.claude restore --source <hash> -- commands/analyze-then-pick.md`
- Undo one change (keeps everything after it):
  `git -C ~/.claude revert <hash>`
- A whole folder back to a point in time:
  `git -C ~/.claude restore --source <hash> -- analyze-then-pick/`
The restore itself is committed by the next auto-commit, so it can be undone too.
Or just ask Claude: "revert the analyze-then-pick command to how it was yesterday".

## Pause it
Remove the two `autocommit.py` entries under `hooks` in `settings.json`, or open `/hooks`.
