---
name: atp-tests-and-inspection
description: "/analyze-then-pick has a test suite (tests/run_all.py, scripts/check_all.py + wrappers) and gather-only inspection commands (status, doctor, lint-run, cost-report, seams); every --run takes a bare run name or a stamp prefix; loupe ensure waits 25 s then reports syncing; built 2026-10-20"
metadata:
  type: project
---

Since 2026-10-20 the `/analyze-then-pick` library carries `tests/` (t01 structure, t02 toolkit on scratch fixtures under a temp `ATP_HOME`, t03 the Loupe coupling against a Loupe server in the test process with a fake keeper, t04 real data opt-in with `--real`; `ATP_TEST_LIVE_KEEPER=1` makes one real consult) and `scripts/check_all.py` (`check-all.cmd` / `.ps1` / `.sh`: the suites, `docs_tool.py check`, Loupe's selftest and keeper_sync in one table, exit 1 on a failure). The toolkit gained gather-only commands: `status --run`, `doctor [--run]`, `lint-run --run`, `cost-report --run [--balance]`, `seams --video --at|--map` (also printed by `strip-inserts`); every `--run` resolves a full path, a bare run name or a unique stamp prefix (`resolve_run`); `ATP_HOME` can point the toolkit at a temp library copy; `loupe ensure` waits at most 25 s (`ATP_KEEPER_SYNC_WAIT`) for the keeper sync and reports `keeper.state: syncing`; `doc-text` / `prep-all` / `prep-assets` extract PDFs with pypdf and flag image-only ones; `inventory` has no file-name hints.

**Why:** the live Recreate run of 2026-10-19/20 showed the failures these remove (a bare run name refused, PDF stubs, a cut inside a flash found by hand, an hour lost behind the keeper lock, prompts a few characters under the cap that nothing measured) and the library had no tests at all.

**How to apply:** run `scripts/check_all.py` (or `tests/run_all.py`) after every change to the library, the skills or the router; a new toolkit command comes with a check in t02 that it returns facts and no verdict; the Loupe coupling of the toolkit is tested in t03 without the real keeper. Related: [[atp-skills-architecture]], [[loupe-web-app]], [[scripts-gather-agents-decide]], [[atp-audio-ingest-question]], [[engineering-pass-edits-atp-only]].
