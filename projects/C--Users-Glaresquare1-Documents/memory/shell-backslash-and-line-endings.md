---
name: shell-backslash-and-line-endings
description: "Bash tool on this PC: a doubled backslash in a command or heredoc reaches the program as ONE backslash; bash grep for CR gives wrong line-ending answers; check endings and build backslashes in Python"
metadata:
  type: project
---

Found 2026-11-02 while patching Loupe and /analyze-with-loupe files from Python heredocs:

- A doubled backslash written in a Bash-tool command or `<<'EOF'` heredoc arrived in the written script as a single one, so a Python anchor meant to hold a literal backslash-n held a real newline and matched nothing. In patch scripts build the character as `chr(92)` (and CR LF as `chr(13) + chr(10)`) instead of escaping.
- `grep -c $'\r' file` and `if grep -q $'\r'` in Git Bash reported CRLF for LF files and LF for CRLF files. Count endings in Python on the bytes (`b.count(b"\r\n")` against `b.count(b"\n")`) before editing, and write with `read_bytes`/`write_bytes`: `Path.write_text` on Windows turns every newline into CR LF (it converted the LF memory index once).
- Repos differ: `~/.claude/loupe` has `core.autocrlf=true` (working files mostly CRLF, git stores LF, a few files LF on disk), `~/.claude` (claude-config) has it false and its router and skills must stay LF (t01 checks). Preserve each file's own endings.

**How to apply:** before any scripted edit, read the file's endings with Python bytes, keep them, and never put an escaped backslash in a shell-quoted script. Related: [[loupe-web-app]], [[claude-folder-git-versioning]].
