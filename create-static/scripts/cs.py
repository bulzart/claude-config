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

import cs_core  # noqa: E402

if __name__ == "__main__":
    cs_core.main()
