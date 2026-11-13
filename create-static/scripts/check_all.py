"""check-all: every check of the /create-static library in one call, one compact table, exit 1 on any failure.
  python scripts/check_all.py
    the library's suites (tests/run_all.py: the CapCut composition on a synthetic video, the library's consistency) and docs_tool check.
Nothing here decides anything about a run; it only runs the checks and reports their last lines."""
import subprocess
import sys
import time
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(name, cmd, cwd=None, timeout=1800):
    t0 = time.time()
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, timeout=timeout)
        out = (cp.stdout or "").strip().splitlines()
        last = next((ln for ln in reversed(out) if ln.strip()), "")
        if cp.returncode != 0 and not last:
            last = ((cp.stderr or "").strip().splitlines() or [""])[-1]
        return {"name": name, "ok": cp.returncode == 0, "seconds": round(time.time() - t0, 1), "last": last[:110]}
    except subprocess.TimeoutExpired:
        return {"name": name, "ok": False, "seconds": round(time.time() - t0, 1), "last": "timed out"}


def main():
    rows = [run("create-static tests", [PY, "-X", "utf8", str(LIB / "tests" / "run_all.py")]),
            run("create-static docs check", [PY, "-X", "utf8", str(LIB / "scripts" / "docs_tool.py"), "check"])]
    w = max(len(r["name"]) for r in rows)
    for r in rows:
        print(f"{r['name']:{w}}  {'ok ' if r['ok'] else 'FAIL'}  {r['seconds']:7.1f} s  {r['last']}")
    bad = [r["name"] for r in rows if not r["ok"]]
    print("\nALL CHECKS PASSED" if not bad else "\nFAILED: " + ", ".join(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()