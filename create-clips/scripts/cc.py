"""create-clips toolkit entry point: `python cc.py <command> ...` (every command prints one JSON object on its last line).

Commands live in four modules, each exposing register(sub):
  cc_proc.py  chunk processing: new-run, ingest, watch, status, doctor, chunks, locate, window, frame, sheet, stream-table
  cc_edit.py  editing helpers:  config, state, blocks, words, sfx-scan, layout-calc, grid-frame, censor, edl-check, captions, capcut-name, capcut-compose, capcut-finish
  cc_hud.py   on-screen reading for game matches: hud-read, hud-scan (OCR of a region over time), region-series (numbers of a region over time)
  cc_game.py  game-mode tabulation: hud-states (the score's changes as one table), hud-slice (one reader inside a range), units-merge, units-verdict, units-check (facts about round/fight cards), units-table (rounds.json as a table for the user)
(native_host.py is the Chrome native-messaging host that starts and reports on `watch`; install-background.ps1 registers it, opt-in.)
Scripts gather, agents decide: nothing here judges, ranks or decides.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cc_common import fail  # noqa: E402

MODULES = ("cc_proc", "cc_edit", "cc_hud", "cc_game")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cc.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name == name:      # the module itself is not written (yet): the others still work
                continue
            raise
        mod.register(sub)
    return ap


def main(argv=None) -> None:
    ap = build_parser()
    a = ap.parse_args(argv)
    if not getattr(a, "func", None):
        ap.print_help()
        fail("a command is needed", 2)
    a.func(a)


if __name__ == "__main__":
    main()
