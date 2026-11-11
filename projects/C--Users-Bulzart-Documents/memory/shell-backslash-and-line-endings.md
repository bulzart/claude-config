---
name: shell-backslash-and-line-endings
description: "Bash tool on this PC: a doubled backslash in a command or heredoc reaches the program as ONE backslash; bash grep for CR gives wrong line-ending answers; check endings and build backslashes in Python"
metadata:
  node_type: memory
  type: project
  originSessionId: 0ff74cb4-bc5e-4c0e-82b7-c94ab48b8c77
  modified: 2026-11-11T11:55:29.812Z
---

Found 2026-11-02 while patching Loupe and /analyze-with-loupe files from Python heredocs:

- A doubled backslash written in a Bash-tool command or `<<'EOF'` heredoc arrived in the written script as a single one, so a Python anchor meant to hold a literal backslash-n held a real newline and matched nothing. In patch scripts build the character as `chr(92)` (and CR LF as `chr(13) + chr(10)`) instead of escaping.
- `grep -c $'\r' file` and `if grep -q $'\r'` in Git Bash reported CRLF for LF files and LF for CRLF files. Count endings in Python on the bytes (`b.count(b"\r\n")` against `b.count(b"\n")`) before editing, and write with `read_bytes`/`write_bytes`: `Path.write_text` on Windows turns every newline into CR LF (it converted the LF memory index once).
- A Windows path or a word with a backslash inside a normal (non-raw) Python string became a control character in notes and logs: `Documents\27.10` turned into chr(23), `\fonts` into a form feed that ate the f (found 2026-11-11 in a memory note, the learning log and awl-user-folders-read-only). Write paths with forward slashes or raw strings, and after writing notes scan them for `[\x00-\x08\x0b\x0c\x0e-\x1f]`.
- Repos differ: `~/.claude/loupe` has `core.autocrlf=true` (working files mostly CRLF, git stores LF, a few files LF on disk), `~/.claude` (claude-config) has it false and its router and skills must stay LF (t01 checks). Preserve each file's own endings.

**How to apply:** before any scripted edit, read the file's endings with Python bytes, keep them, and never put an escaped backslash in a shell-quoted script. Related: [[loupe-web-app]], [[claude-folder-git-versioning]].
