"""Tests of the desktop control for the CapCut export (cc_desk.py), without touching the mouse, the keyboard or the registry: the window list, the
CapCut windows found by its process only (a terminal titled "CapCut ..." is never one of them), a screenshot of a region at a scale, key names, and the
commands' refusals. Run: python tests/test_desk.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_desk as K  # noqa: E402

PY = sys.executable
CC = HERE.parent / "scripts" / "cc.py"
FAILED, N = [], [0]


def check(ok, what):
    N[0] += 1
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILED.append(what[:90])


def cc(*args):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False}), cp.returncode


ws = K.windows()
check(isinstance(ws, list) and all({"hwnd", "title", "pid", "rect", "foreground"} <= set(w) for w in ws), f"the visible windows are listed ({len(ws)})")
pids = set(K._capcut_pids())
check(all(w["pid"] in pids for w in K.capcut_windows()), "CapCut's windows are found by its process, never by a title")
tmp = Path(tempfile.mkdtemp(prefix="cc_desk_test_"))
s = K.shot(tmp / "s.jpg", [0, 0, 400, 300], 0.5)
check(Path(s["file"]).is_file() and s["size"] == [200, 150], "a screenshot of a region at half scale: " + json.dumps(s["size"]))
check(K.VK["ctrl"] == 0x11 and K.VK["enter"] == 0x0D and K.VK["f5"] == 0x74, "key names map to their virtual keys")
r, code = cc("desk", "click")
check(r.get("ok") is False, "a click without coordinates is refused")
r, code = cc("capcut-app", "status")
check(r.get("ok") and "export_path" in r, "capcut-app status reports whether CapCut runs and the export folder it remembers")
print(f"test_desk: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
sys.exit(1 if FAILED else 0)
