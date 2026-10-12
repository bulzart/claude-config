"""Shared helpers of the new test files (the toolkit RECORDS and TABULATES; it never decides)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE.parent
PY = sys.executable
ATG = os.environ.get("ATG_UNDER_TEST") or str(LIB / "scripts" / "atg.py")        # set ATG_UNDER_TEST to test a working copy of the toolkit
SYN_RUN = Path(os.environ.get("ATG_TEST_FIXTURE") or HERE / "fixture" / "run")          # a synthetic run: four reference videos and two baseline videos prepared, with their cards (no images or audio)

fails = []


def t(*args, ok=True):
    cp = subprocess.run([PY, "-X", "utf8", ATG, *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    last = [l for l in cp.stdout.strip().splitlines() if l.strip()]
    js = {}
    if last:
        try:
            js = json.loads(last[-1])
        except ValueError:
            js = {"raw": last[-1]}
    if ok and cp.returncode != 0:
        print("UNEXPECTED FAILURE:", args, cp.stdout[-600:], cp.stderr[-600:])
        sys.exit(1)
    return js, cp.returncode, cp.stdout


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def fresh_run(name="t11"):
    """A private copy of the synthetic run with empty ledgers."""
    dst = Path(tempfile.mkdtemp(prefix=f"atg-{name}-")) / "run"
    shutil.copytree(SYN_RUN, dst)
    for sub, files in (("30-research", ("candidates.json", "evidence.json", "specs.json", "photos.json", "ranking.json", "ranking.md", "niche-audit.md")),
                       ("20-analysis", ("niche-vocabulary.json", "corpus-stats.json", "corpus-stats.md", "corpus-profile.json", "corpus-profile.md"))):
        for f in files:
            (dst / sub / f).unlink(missing_ok=True)
            (dst / sub / (f + ".lock")).unlink(missing_ok=True)
    shutil.rmtree(dst / "deliverables", ignore_errors=True)
    (dst / "deliverables").mkdir(exist_ok=True)
    return str(dst)


def finish():
    print("\nFAILED:" if fails else "\nALL CHECKS PASSED", fails if fails else "")
    sys.exit(1 if fails else 0)
