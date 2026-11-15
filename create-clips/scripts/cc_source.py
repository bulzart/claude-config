"""cc_source.py - lock, unlock, and check the encrypted-at-rest state of the other cc_*.py modules (see cc_crypto_loader.py for how the
encrypted ones actually get read at runtime). Always plain, never encrypted itself, like cc.py and cc_crypto_loader.py.

  cc.py source generate-key    print a brand-new key ONCE (save it; nothing here writes it to any file)
  cc.py source lock            encrypt every currently-plain protected module with CC_SOURCE_KEY, then delete the plain copy
  cc.py source unlock          decrypt every protected module's .py.enc with CC_SOURCE_KEY into a plain, editable, gitignored .py
  cc.py source status          which protected modules are plain (editable, not tracked), locked (only .enc, what git has), both, or missing

`both` (a module has its plain .py AND its .py.enc on disk at once) means someone edited the unlocked copy and has not re-run `source lock`
since: the .py.enc that git would commit is stale. This command never reads or writes the key anywhere but the CC_SOURCE_KEY environment
variable for the run; it is never written to a file, logged, or sent anywhere.
"""
from __future__ import annotations

import os
import sys

from cc_common import fail, out
from cc_crypto_loader import ENV_VAR, SCRIPTS_DIR, protected_names


def _key() -> str:
    key = os.environ.get(ENV_VAR)
    if not key:
        fail(f"{ENV_VAR} is not set. `cc.py source generate-key` makes one if you do not have one yet; otherwise set it to the project's "
             f"existing key before locking or unlocking anything.")
    return key


def _fernet(key: str):
    from cryptography.fernet import Fernet
    return Fernet(key.encode("utf-8"))


def cmd_source(a) -> None:
    if a.action == "generate-key":
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode("utf-8")
        print(f"\n{key}\n")
        print("Save this now (a password manager, written down - somewhere that is not this repo): it is shown only this once, nothing here "
              "writes it to a file. Set it as the CC_SOURCE_KEY environment variable before `source lock` or `source unlock`, and keep using "
              "the SAME key every time: a new key cannot decrypt files an earlier key encrypted.", file=sys.stderr)
        out({"ok": True, "action": "generate-key", "note": "the key is printed above, once; nothing here persists it"})

    names = protected_names()
    if a.action == "status":
        rows = []
        for name in names:
            plain = (SCRIPTS_DIR / f"{name}.py").is_file()
            enc = (SCRIPTS_DIR / f"{name}.py.enc").is_file()
            state = "both (re-lock: the committed .enc may be stale)" if plain and enc else ("plain (editable, not tracked)" if plain else ("locked" if enc else "missing"))
            rows.append({"name": name, "state": state})
        for r in rows:
            print(f"{r['name']:20s} {r['state']}")
        out({"ok": True, "action": "status", "modules": rows})

    if a.action == "lock":
        f = _fernet(_key())
        locked, skipped = [], []
        for name in names:
            plain_p = SCRIPTS_DIR / f"{name}.py"
            if not plain_p.is_file():
                skipped.append(name)
                continue
            enc_p = SCRIPTS_DIR / f"{name}.py.enc"
            enc_p.write_bytes(f.encrypt(plain_p.read_bytes()))
            plain_p.unlink()
            locked.append(name)
        out({"ok": True, "action": "lock", "locked": locked, "already_locked_or_missing": skipped})

    if a.action == "unlock":
        f = _fernet(_key())
        unlocked, skipped, failed = [], [], []
        for name in names:
            enc_p = SCRIPTS_DIR / f"{name}.py.enc"
            plain_p = SCRIPTS_DIR / f"{name}.py"
            if not enc_p.is_file():
                continue
            if plain_p.is_file() and not a.force:
                skipped.append(name)      # already unlocked: do not clobber a local edit without --force
                continue
            from cryptography.fernet import InvalidToken
            try:
                plain_p.write_bytes(f.decrypt(enc_p.read_bytes()))
            except (InvalidToken, ValueError):
                failed.append(name)
                continue
            unlocked.append(name)
        if failed:
            fail(f"the key does not decrypt: {', '.join(failed)} (wrong key, or the file is corrupt)", 1, unlocked=unlocked, skipped=skipped)
        out({"ok": True, "action": "unlock", "unlocked": unlocked, "already_unlocked": skipped})
    fail(f"unknown action {a.action!r}")


def register(sub) -> None:
    p = sub.add_parser("source", help="lock/unlock the encrypted-at-rest cc_*.py modules, or check their state (see cc_crypto_loader.py)")
    p.add_argument("action", choices=["generate-key", "lock", "unlock", "status"])
    p.add_argument("--force", action="store_true", help="unlock: overwrite an already-unlocked plain .py with what is in the .py.enc")
    p.set_defaults(func=cmd_source)
