"""Test that the toolkit never opens a console window.

    python tests/test_nowindow.py

The watcher of the logon task runs under pythonw.exe, which has no console. A console program it starts (ffmpeg, ffprobe, powershell ...) is then given a NEW console,
and with Windows Terminal as the default terminal that is a visible window for every call (seen 2026-11-13: one popup per ffmpeg call while a recording was processed).
Every child process must therefore be started with creationflags=NO_WINDOW. This test
  1. reads every script and fails on a subprocess call without `creationflags`, and on os.system / os.popen / os.startfile (they always open a console);
  2. starts a console child through cc_common.run_cmd from a pythonw.exe parent (no console) and checks that the child has no console window (GetConsoleWindow() == 0).
     (Checked once by hand without the flag: the child got a window handle and Windows Terminal started a new OpenConsole process.)
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
SUBPROCESS_CALLS = {"run", "Popen", "check_output", "check_call", "call", "getoutput", "getstatusoutput"}
ALWAYS_BAD = {("os", "system"), ("os", "popen"), ("os", "startfile"), ("subprocess", "getoutput"), ("subprocess", "getstatusoutput")}


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def scan(src: str, name: str) -> tuple:
    """(number of subprocess calls, list of problems) in one source text."""
    calls, bad = 0, []
    for node in ast.walk(ast.parse(src, filename=name)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)):
            continue
        owner, fn = node.func.value.id, node.func.attr
        if (owner, fn) in ALWAYS_BAD:
            bad.append(f"{name}:{node.lineno} {owner}.{fn} always opens a console (use cc_common.run_cmd)")
        elif owner == "subprocess" and fn in SUBPROCESS_CALLS:
            calls += 1
            if not any(k.arg == "creationflags" for k in node.keywords):
                bad.append(f"{name}:{node.lineno} subprocess.{fn} without creationflags (a console window opens under pythonw)")
    return calls, bad


def read_scripts(unreadable: list):
    """(name, text) of every script of the toolkit: the plain .py files, and the locked ones (`<name>.py.enc`) decrypted in memory with CC_SOURCE_KEY (nothing
    is written to disk). A locked script that cannot be decrypted goes into `unreadable` and fails the test: the scan must never pass by looking at nothing."""
    names = {p.name for p in SCRIPTS.glob("*.py")}
    for p in sorted(SCRIPTS.glob("*.py")):
        yield p.name, p.read_text(encoding="utf-8-sig")
    for p in sorted(SCRIPTS.glob("*.py.enc")):
        if p.name[:-4] in names:
            continue                                  # the plain copy is there (unlocked for editing): it was read above
        key = os.environ.get("CC_SOURCE_KEY")
        try:
            from cryptography.fernet import Fernet
            yield p.name[:-4], Fernet(key.encode("utf-8")).decrypt(p.read_bytes()).decode("utf-8-sig")
        except Exception as e:  # noqa: BLE001  (no key, a wrong key, no cryptography package: all the same here)
            unreadable.append(f"{p.name} ({type(e).__name__})")


def main():
    # the scan itself: it must flag the old way and accept the new one
    c1, b1 = scan("import subprocess\nsubprocess.run(['ffprobe'], capture_output=True)\n", "old.py")
    c2, b2 = scan("import subprocess\nsubprocess.Popen(['ffmpeg'], creationflags=0x08000000)\nsubprocess.run(['x'], creationflags=F)\n", "new.py")
    c3, b3 = scan("import os\nos.system('dir')\n", "sys.py")
    check(c1 == 1 and len(b1) == 1 and c2 == 2 and not b2 and len(b3) == 1, "the scan flags a call without creationflags and an os.system, and accepts calls that pass it")

    scanned, calls, bad, unreadable = 0, 0, [], []
    for name, text in read_scripts(unreadable):
        scanned += 1
        c, b = scan(text, name)
        calls += c
        bad += b
    check(not unreadable, "every locked script was decrypted in memory to be scanned (CC_SOURCE_KEY must be set for this test) " + ("; ".join(unreadable) if unreadable else "-"))
    check(scanned >= 8 and calls >= 4, f"read {scanned} scripts, {calls} subprocess calls found (the scan sees them)")
    check(not bad, "every subprocess call hides its console window, and no os.system/os.popen/os.startfile " + ("; ".join(bad) if bad else "-"))

    if sys.platform != "win32":
        print("skip the pythonw check (not Windows)")
    else:
        pyw = Path(sys.executable).with_name("pythonw.exe")
        if not pyw.is_file():
            print("skip the pythonw check (pythonw.exe not next to python.exe)")
        else:
            tmp = Path(tempfile.mkdtemp(prefix="cc-nowin-test-"))
            probe, res = tmp / "probe.py", tmp / "result.txt"
            probe.write_text(
                "import sys\n"
                f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
                "import cc_crypto_loader\n"
                "import cc_common\n"
                f"cp = cc_common.run_cmd([{sys.executable!r}, '-c', 'import ctypes; print(ctypes.windll.kernel32.GetConsoleWindow())'])\n"
                f"open({str(res)!r}, 'w').write(cp.stdout.strip() + '|' + str(cc_common.NO_WINDOW))\n", encoding="utf-8")
            rc = subprocess.run([str(pyw), str(probe)], timeout=60).returncode
            got = res.read_text(encoding="utf-8") if res.is_file() else ""
            check(rc == 0 and got == "0|134217728", f"under pythonw, run_cmd's child has no console window (GetConsoleWindow|NO_WINDOW = {got!r})")
            for f in tmp.iterdir():
                f.unlink()
            tmp.rmdir()
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
