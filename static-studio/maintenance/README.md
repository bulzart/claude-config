# maintenance (not read by the command)

Tools for whoever looks after `scripts/capcut_tools.py`. Nothing here runs in a video's production.

- `build_capcut_tools.py <awl.py> <out.py>`: copies the CapCut commands (and the helpers they need) out of the analyze-with-loupe toolkit's `scripts/awl.py` into a new `capcut_tools.py`: the source lines unchanged, plus the few deliberate changes listed in the file's header. `--report` only lists where the copy would still name that toolkit.
- `verify_extraction.py <awl.py> <capcut_tools.py>`: line-by-line proof that every copied definition equals the original except those deliberate changes.
- `capcut_e2e.py [--keep]`: the end-to-end check in a scratch CapCut store (the real MCP server and capcut-cli write a small project; the toolkit adds moves, a join, a font and a text entrance, repairs it, and it is read back from its files and through the MCP; every writer must refuse while CapCut has the project open). CapCut must be closed. The real store is never written. Run it after a CapCut update and after re-copying.

- `capcut_autoupdate.py status | block | unblock`: CapCut's automatic updates off or on. `block` sets CapCut's own switches (`enableAutoUpdate`, `totalSilentUpgradeSwitch` in `User Data\Config\globalSetting`) to false and denies creating new files and folders directly in `%LOCALAPPDATA%\CapCut\Apps` (this folder only; the existing versions and everything CapCut does while running are untouched). Blocked on 2026-11-19 at the user's request, so the toolkit keeps meeting the CapCut it was checked on. Run `unblock` before updating CapCut yourself, then `block` again. CapCut must be closed.

After re-copying the code: `python -I maintenance/verify_extraction.py <awl.py> scripts/capcut_tools.py`, then `python tests/test_capcut_tools.py` and `python maintenance/capcut_e2e.py`. `data/capcut-catalogue.*` is a measurement of this PC's CapCut (made on CapCut 9.7.0.4153, 2026-11-06): replace it only from a new measurement.
