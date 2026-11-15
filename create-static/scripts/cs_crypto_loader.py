"""cs_crypto_loader.py - the only always-plain, never-encrypted piece of the real logic (with cs.py and cs_source.py): a Python import hook that
decrypts the other cs_*.py modules at the moment something imports them, given the right key, and never writes decrypted plaintext to disk.

The user, 2026-11-15: "use encryption at run ... requires a key for files to be read ... not a .exe file." This is that: cs_core.py (everything
the old, single cs.py used to hold) and cs_compose.py can be stored on disk as ciphertext (`<name>.py.enc`, written by `cs.py source lock`); the
moment anything does `import cs_core` (from this tiny cs.py bootstrap, or from a self-re-invocation of cs.py as a subprocess), Python's import
system asks every finder in `sys.meta_path` in turn, and THIS one, if a plain `<name>.py` is not sitting there already, reads the ciphertext,
decrypts it in memory with the key from the CS_SOURCE_KEY environment variable, and executes the result as the module - no decrypted copy ever
touches disk. If `CS_SOURCE_KEY` is missing or wrong, the import fails with a plain explanation instead of a cryptic traceback.

A module with its plain `.py` present (the normal, editable state while someone is working on it: `cs.py source unlock` makes it so) is loaded
exactly as Python always loads a file - this finder steps aside and lets the default import machinery handle it, so no key is needed at all while
a module is unlocked. The plain `.py` filenames are gitignored (see ~/.claude/.gitignore), so being unlocked never risks being committed by
accident, however this session or an auto-commit hook ends.

This module decides WHICH names it manages by what is actually sitting in this folder (every `cs_*.py` or `cs_*.py.enc` pair, except the names
in ALWAYS_PLAIN below) rather than a hardcoded list.
"""
from __future__ import annotations

import importlib.abc
import importlib.util
import os
import sys
from pathlib import Path

ENV_VAR = "CS_SOURCE_KEY"
SCRIPTS_DIR = Path(__file__).resolve().parent
ALWAYS_PLAIN = {"cs", "cs_crypto_loader", "cs_source"}  # the bootstrap, this loader, and the lock/unlock tool itself: never encrypted


def protected_names() -> list[str]:
    """Every cs_* module name that has a plain .py, an encrypted .py.enc, or both, except the names that are never encrypted."""
    names = set()
    for p in SCRIPTS_DIR.glob("cs_*.py"):
        names.add(p.stem)
    for p in SCRIPTS_DIR.glob("cs_*.py.enc"):
        names.add(p.stem[:-3])            # "cs_core.py.enc".stem is "cs_core.py"; drop the trailing ".py"
    return sorted(names - ALWAYS_PLAIN)


class _EncryptedLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, enc_path: Path):
        self.fullname, self.enc_path = fullname, enc_path

    def create_module(self, spec):
        return None  # the default module object is fine; we only need to fill in its code

    def exec_module(self, module) -> None:
        key = os.environ.get(ENV_VAR)
        if not key:
            raise ImportError(
                f"{self.fullname} is encrypted at rest ({self.enc_path.name}) and {ENV_VAR} is not set: there is no key to decrypt it with. "
                f"Set {ENV_VAR} to the project's key (see docs/processing.md \"Source encryption\"), or run `cs.py source unlock` first if you "
                f"meant to edit it, which needs the same key once.")
        from cryptography.fernet import Fernet, InvalidToken  # imported here, not at module load, so a plain/unlocked run never needs it installed
        try:
            source = Fernet(key.encode("utf-8")).decrypt(self.enc_path.read_bytes())
        except (InvalidToken, ValueError) as e:
            raise ImportError(f"{ENV_VAR} does not decrypt {self.fullname} ({self.enc_path.name}): the key is wrong, or the file is corrupt "
                               f"({type(e).__name__}).") from None
        code = compile(source, str(self.enc_path), "exec")
        exec(code, module.__dict__)  # noqa: S102 - this IS the module's own code, decrypted; equivalent to what a normal import does with a .py file


class _EncryptedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in ALWAYS_PLAIN or not fullname.startswith("cs_"):
            return None
        plain_path = SCRIPTS_DIR / f"{fullname}.py"
        if plain_path.is_file():
            return None  # unlocked: let the default file-based import handle it, no key needed
        enc_path = SCRIPTS_DIR / f"{fullname}.py.enc"
        if not enc_path.is_file():
            return None  # not one of ours (or genuinely missing): let the normal machinery raise its own ModuleNotFoundError
        return importlib.util.spec_from_loader(fullname, _EncryptedLoader(fullname, enc_path), origin=str(enc_path))


if not any(isinstance(f, _EncryptedFinder) for f in sys.meta_path):   # importable from several entry points in one process; install once
    sys.meta_path.insert(0, _EncryptedFinder())
