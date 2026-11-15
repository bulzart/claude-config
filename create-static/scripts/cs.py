#!/usr/bin/env python3
"""cs.py - entry point for the /create-static Claude Code command (`python cs.py <cmd> ...`).

This file and cs_crypto_loader.py and cs_source.py are the only always-plain, never-encrypted pieces: the real logic (everything the single
cs.py file used to hold directly) now lives in cs_core.py, and the CapCut composition in cs_compose.py; both can be stored encrypted at rest
(cc_crypto_loader.py's sibling for this pipeline: cs_crypto_loader.py decrypts one at the moment something imports it, given CS_SOURCE_KEY; the
user, 2026-11-15, "use encryption at run ... requires a key for files to be read ... not a .exe file"). `cs.py source generate-key|lock|unlock|
status` manages that. Every subcommand, help text and behaviour is unchanged from before the split; this file only loads cs_core and runs it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cs_crypto_loader  # noqa: E402,F401  (registers the decrypt-on-import hook before anything below can need it)


def _locked_only() -> None:
    # cs_core can't decrypt (CS_SOURCE_KEY missing or wrong): `source` lives inside cs_core.main() normally, so without this fallback,
    # `cs.py source status`/`unlock` - the one thing you'd want to run in exactly this situation - would be unreachable too.
    import argparse
    import json
    import cs_source

    class _Parser(argparse.ArgumentParser):
        def error(self, message):       # a command that lives only inside the locked cs_core: name the reason, in the one-JSON-object form every command answers in
            if "invalid choice" in message:
                sys.stdout.write(json.dumps({"ok": False, "error": f"{message.split(' (choose')[0]}: that command lives in cs_core.py, which is encrypted at rest, and "
                                             f"CS_SOURCE_KEY is missing or does not decrypt it. Set CS_SOURCE_KEY to the project's key in the environment this was started "
                                             f"from (a new terminal after `setx`); `cs.py source status` shows the state."}) + "\n")
                sys.stdout.flush()
                sys.exit(2)
            super().error(message)

    ap = _Parser(prog="cs.py", description="cs_core.py is encrypted at rest and CS_SOURCE_KEY is missing or wrong: only "
                 "`source` is available until it's unlocked (`cs.py source status` for details).")
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")
    cs_source.register(sub)
    a = ap.parse_args()
    if not getattr(a, "fn", None):
        ap.print_help()
        sys.exit(2)
    a.fn(a)


if __name__ == "__main__":
    try:
        import cs_core  # noqa: E402
    except cs_crypto_loader.SourceLocked:
        _locked_only()
    else:
        cs_core.main()
