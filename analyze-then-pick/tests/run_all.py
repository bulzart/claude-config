"""Run every test suite of the library and print one line per suite. Usage: python tests/run_all.py   (ATP_UNDER_TEST=<atp.py> tests a working copy)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITES = ["t01_library", "t02_toolkit", "t03_loupe"]
bad = 0
for s in SUITES:
    cp = subprocess.run([sys.executable, "-X", "utf8", str(HERE / f"{s}.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = cp.stdout.count("PASS  ")
    fails = [ln for ln in cp.stdout.splitlines() if ln.startswith("FAIL") or "UNEXPECTED FAILURE" in ln]
    status = "ok" if cp.returncode == 0 and not fails else "FAILED"
    bad += status != "ok"
    print(f"{s:16} {status:7} {ok} checks passed" + ("" if status == "ok" else "\n  " + "\n  ".join(fails[:5] or [cp.stdout[-300:], cp.stderr[-300:]])))
print("\nALL SUITES PASSED" if not bad else f"\n{bad} SUITE(S) FAILED")
sys.exit(1 if bad else 0)
