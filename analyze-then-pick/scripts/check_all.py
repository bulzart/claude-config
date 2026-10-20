"""check-all: every check of the /analyze-then-pick library in one call, one compact table, exit 1 on any failure.
  python scripts/check_all.py [--real] [--no-loupe] [--live]
    the library's suites (tests/run_all.py; --real adds the real-data suite), docs_tool check, and Loupe's own tests
    (tests/selftest.py and tests/keeper_sync.py offline; --live adds keeper_sync --live, read-only on the real library; --no-loupe skips them).
Nothing here decides anything about a run; it only runs the checks and reports their last lines."""
import argparse
import subprocess
import sys
import time
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
LOUPE = LIB.parent / "loupe"
PY = sys.executable


def run(name, cmd, cwd=None, timeout=1800):
    t0 = time.time()
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, timeout=timeout)
        out = (cp.stdout or "").strip().splitlines()
        last = next((ln for ln in reversed(out) if ln.strip()), "")
        if cp.returncode != 0 and not last:
            last = (cp.stderr or "").strip().splitlines()[-1:] or [""]
            last = last[0]
        return {"name": name, "ok": cp.returncode == 0, "seconds": round(time.time() - t0, 1), "last": last[:110]}
    except subprocess.TimeoutExpired:
        return {"name": name, "ok": False, "seconds": round(time.time() - t0, 1), "last": "timed out"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--real", action="store_true", help="also the real-data suite (tests/t04_real.py)")
    ap.add_argument("--no-loupe", action="store_true", help="skip Loupe's own tests")
    ap.add_argument("--live", action="store_true", help="also keeper_sync --live (read-only on the real Loupe library)")
    a = ap.parse_args()
    rows = [run("atp tests", [PY, "-X", "utf8", str(LIB / "tests" / "run_all.py")] + (["--real"] if a.real else [])),
            run("atp docs check", [PY, "-X", "utf8", str(LIB / "scripts" / "docs_tool.py"), "check"])]
    if not a.no_loupe and LOUPE.is_dir():
        rows.append(run("loupe selftest", [PY, "-X", "utf8", str(LOUPE / "tests" / "selftest.py")], cwd=str(LOUPE)))
        rows.append(run("loupe keeper_sync", [PY, "-X", "utf8", str(LOUPE / "tests" / "keeper_sync.py")], cwd=str(LOUPE)))
        if a.live:
            rows.append(run("loupe keeper_sync --live", [PY, "-X", "utf8", str(LOUPE / "tests" / "keeper_sync.py"), "--live"], cwd=str(LOUPE)))
    w = max(len(r["name"]) for r in rows)
    for r in rows:
        print(f"{r['name']:{w}}  {'ok ' if r['ok'] else 'FAIL'}  {r['seconds']:7.1f} s  {r['last']}")
    bad = [r["name"] for r in rows if not r["ok"]]
    print("\nALL CHECKS PASSED" if not bad else "\nFAILED: " + ", ".join(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
