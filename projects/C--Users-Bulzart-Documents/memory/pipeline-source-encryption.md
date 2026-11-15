---
name: pipeline-source-encryption
description: create-clips and create-static source is encrypted at rest with a key only the user holds; supersedes the abandoned PyInstaller build-protected.js approach
metadata:
  node_type: memory
  type: project
  originSessionId: 7871cc76-de90-4292-a548-53ad612f5f68
  modified: 2026-11-15T12:10:35.206Z
---

User 2026-11-15, after rejecting two earlier approaches in the same session (file-order obfuscation: "weak security... would break my own ability to read/edit"; then a PyInstaller `.exe` build, [[protected-build-tool]]-superseded: "it should not be a .exe file ... use encryption at run and remove any .exe, i just need to have encryption in the runtime while the command executes it requires a key for files to be read"). Final, explicit requirement: "i encrypt once all the priority files in both pipelines with my keys ... its only my keys who decrypt them ... they should never change once i lock them."

**What's built, in both pipelines:** a Python import hook (`cc_crypto_loader.py` / `cs_crypto_loader.py`) decrypts a module (Fernet/AES) in memory at the moment something imports it, reading the key from an environment variable (`CC_SOURCE_KEY` / `CS_SOURCE_KEY`) — no plaintext ever touches disk during a decrypted run. A sibling tool (`cc_source.py` / `cs_source.py`, self-contained, never depends on anything that could itself be encrypted) does `generate-key | lock | unlock | status`. Three files per pipeline are always plain and never encrypted: the entry script (`cc.py` / `cs.py`), the loader, and this tool itself. Every other `cc_*.py` / `cs_core.py`+`cs_compose.py` can be locked. The plain `.py` filenames are explicitly gitignored (not wildcarded) so an unlocked working copy can never be committed by accident.

Validated end to end in both pipelines (`tests/test_source_crypto.py`, 13/13 checks each, run against an isolated temp copy with disposable dummy modules and throwaway keys — the real source was never touched or locked by me): plain needs no key; locked+no key and locked+wrong key both fail with a plain message, nothing runs; locked+correct key behaves exactly like plain, including an import chain between two protected modules; `status` correctly reports plain/locked/both; `unlock` restores byte-identical source; `unlock` without `--force` never clobbers a local edit, `--force` does.

Doc for the user: `create-clips/docs/processing.md` "Source encryption" section; `create-static/README.md` "Source encryption" section (written self-contained, not cross-linked, per [[no-cross-pipeline-mentions]]).

**The user generates and holds the real key themselves** — I never generate it for real use and I'm never given it to store. `cc.py source generate-key` / `cs.py source generate-key` prints a fresh key once to stdout and writes it nowhere; `setx CC_SOURCE_KEY "<key>"` / `setx CS_SOURCE_KEY "<key>"` (new shell needed after) makes it ambient so neither the user nor any tool has to supply it again on this PC. The SAME key must be reused for every future lock/unlock — there's no rotation — and a clone of the repo elsewhere needs that identical key to ever unlock anything; losing it means anything locked with it is unrecoverable (nothing here escrows it).

**Known gap, not yet resolved (found 2026-11-15 while preparing to push):** the plaintext of these exact files already sits in many historical commits on `origin/pc` (confirmed via `git ls-tree -r origin/pc` and `git log --follow`) from before this feature existed. Locking the current tree and pushing does not scrub old commits — a full clone still exposes the old plaintext through history regardless of what HEAD looks like. Scrubbing it needs a history rewrite + force-push, which is destructive and wasn't requested yet; left for the user to decide. Separately, `git fetch`/`push` to `origin` (`bulzart/claude-config`) currently fails ("could not read Password ... terminal prompts disabled") — `gh auth status` shows not logged in at all; the user needs to re-auth in an interactive terminal before any push can succeed.

Related: [[claude-folder-git-versioning]], [[create-clips-pipeline]], [[create-static-command]], [[whisper-strictly-medium]].
