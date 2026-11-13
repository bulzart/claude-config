"""Run every test of the create-clips processing toolkit.

    "C:\\Users\\Bulzart\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" tests\\run-all.py [--fast] [--keep]

--fast: the tiny Whisper model for the 3-minute chunk too (about a minute); without it the real medium model is timed (about four minutes).
Exit code 0 when everything passed.
"""
import os
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
code = 0
env = {**os.environ, "CC_NOTIFY": "0"}        # no test may show a real Windows notification (test_notify.py uses stand-ins and sets its own)
for t in sorted(here.glob("test_*.py")):
    print(f"=== {t.name}", flush=True)
    flags = [a for a in sys.argv[1:] if a in ("--fast", "--keep")] if t.name == "test_proc.py" else []
    rc = subprocess.run([sys.executable, str(t), *flags], env=env).returncode
    code = code or rc
print("ALL PASSED" if code == 0 else f"FAILED (exit {code})")
sys.exit(code)
