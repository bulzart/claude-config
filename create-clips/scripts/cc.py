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
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_crypto_loader  # noqa: E402,F401  (registers the decrypt-on-import hook before anything below can need it: the user, 2026-11-15)

MODULES = ("cc_proc", "cc_report", "cc_notify", "cc_edit", "cc_hud", "cc_game", "cc_heat")


def fail(msg: str, code: int = 2, **extra) -> None:
    # a local copy, not `from cc_common import fail`: cc_common is itself encryptable, and this file must still be able to report an error
    # (including "a module is locked") when cc_common, or anything else, can't decrypt.
    sys.stdout.write(json.dumps({"ok": False, "error": msg, **extra}, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    sys.exit(code)


class _Parser(argparse.ArgumentParser):
    """When a command is unknown because its module is locked (CC_SOURCE_KEY missing or wrong), say that, in the one-JSON-object form every command answers in,
    instead of a bare "invalid choice" that never mentions the key (the user, 2026-11-15: no key or a wrong key must fail with a plain message)."""
    locked: list = []

    def error(self, message):
        if self.locked and "invalid choice" in message:
            fail(f"{message.split(' (choose')[0]}: that command lives in a module that is encrypted at rest, and CC_SOURCE_KEY is missing or does not decrypt it "
                 f"(locked: {', '.join(self.locked)}). Set CC_SOURCE_KEY to the project's key in the environment this was started from (a new terminal after "
                 f"`setx`); `cc.py source status` shows the state.", 2, locked=list(self.locked))
        super().error(message)


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(prog="cc.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")
    import cc_source                # always present (never encrypted): lock/unlock/status for the other modules
    cc_source.register(sub)
    locked = ap.locked = []
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name == name:      # the module itself is not written (yet): the others still work
                continue
            raise
        except cc_crypto_loader.SourceLocked:
            locked.append(name)     # encrypted and CC_SOURCE_KEY missing/wrong: that module's commands are unavailable, others still work
            continue
        mod.register(sub)
    if locked:
        ap.epilog = (f"{ap.epilog}\n\n" if ap.epilog else "") + f"Locked, no usable key: {', '.join(locked)} (and anything that imports them). `cc.py source status` for details."
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
