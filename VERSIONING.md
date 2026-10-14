# ~/.claude version history

This folder is a local git repository (no remote) that keeps the history of **your**
customizations: commands, skills, pipelines (`analyze-then-pick`, `analyze-stack`), the Loupe web app (`loupe/`, code only: its `data/` is not tracked), hooks,
memory files and `settings.json`.

## What is tracked
Only what `.gitignore` allow-lists. Claude Code's own files are never committed: credentials,
sessions and transcripts, history, caches, plugins and marketplaces, synced claude.ai skills,
telemetry, update state. Run folders, samples, `node_modules` and backups are also left out.
A new top-level folder is reported once and stays untracked until you add `!/<folder>/` to
`.gitignore`.

## When commits happen
Claude Code hooks in `settings.json` run `hooks/autocommit.py`:
- **Stop**: after every Claude turn, whatever changed is committed as `auto(Stop): …`.
- **SessionStart**: changes made outside Claude (manual edits, installers) are committed as
  `auto(SessionStart): …`.
Files over 25 MB are left out and reported. Nothing is ever pushed anywhere.

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
