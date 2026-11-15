"""create-clips toolkit entry point: `python cc.py <command> ...` (every command prints one JSON object on its last line).

Commands live in seven modules, each exposing register(sub):
  cc_proc.py  chunk processing: new-run, ingest, watch, status, doctor, chunks, locate, window, frame, sheet, stream-table
  cc_report.py the chunk reporter: report (a headless Haiku session per chunk writes a report of what its sheets, audio numbers, transcript and chat show; observations only)
  cc_notify.py the ready alert: notify (a Windows notification when a run is fully processed and /create-clips can start on it; the watcher sends it by itself)
  cc_edit.py  editing helpers:  config, state, blocks, words, sfx-scan, layout-calc, grid-frame, censor, edl-check, captions, capcut-name, capcut-compose, capcut-finish
  cc_hud.py   on-screen reading for game matches: hud-read, hud-scan (OCR of a region over time), region-series (numbers of a region over time)
  cc_game.py  game-mode tabulation: hud-states (the score's changes as one table), hud-slice (one reader inside a range), units-merge, units-verdict, units-check (facts about round/fight cards), units-table (rounds.json as a table for the user)
  cc_heat.py  the chat counted in 4-second bins against the stream's own normal: heat (heat.json/heat.md with the bursts, one span's numbers, a block file's unmentioned bursts; numbers only)
(native_host.py is the Chrome native-messaging host that starts and reports on `watch`; install-background.ps1 registers it, opt-in.)
Scripts gather, agents decide: nothing here judges, ranks or decides.

Every module above except this file can be stored encrypted at rest (cc_crypto_loader.py decrypts one at the moment something imports it, given
CC_SOURCE_KEY; cc_source.py is `source generate-key|lock|unlock|status`; the user, 2026-11-15). Neither of those two is ever encrypted itself.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_crypto_loader  # noqa: E402,F401  (registers the decrypt-on-import hook before anything below can need it: the user, 2026-11-15)

from cc_common import fail  # noqa: E402

MODULES = ("cc_proc", "cc_report", "cc_notify", "cc_edit", "cc_hud", "cc_game", "cc_heat")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cc.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")
    import cc_source                # always present (never encrypted): lock/unlock/status for the other modules
    cc_source.register(sub)
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
