"""Test of encryption-at-rest for the cc_*.py modules (cc_crypto_loader.py, cc_source.py, and cc.py itself): the mechanism, never the real
source.

    python tests/test_source_crypto.py

Everything happens in an isolated temp copy (CC_SCRIPTS_DIR points cc_crypto_loader.py and cc_source.py at it): a dummy module stands in for a
real cc_*.py module, so this never touches, locks or unlocks a single file of the real create-clips/scripts/. Two layers are checked:
1. The mechanism directly (`cc_source.cmd_source`): plain needs no key; locked without a key, or with the wrong key, fails with a plain message
   and nothing runs; locked with the right key behaves exactly like the unlocked original, including an inter-module import; `source status`
   reports plain/locked/both correctly; `unlock` without --force never clobbers a local edit, `--force` does; unlock restores byte-identical source.
2. **The real entry point** (`python cc.py ...` as an actual subprocess) in every lock state, using a dummy module that references `__file__`
   at module level (the exact pattern that broke once: a custom loader that never sets `__file__` makes any such module crash with NameError
   even with the correct key). This is the layer step 1 cannot see: `cc_source.cmd_source()` called directly never goes through cc.py's own
   MODULES loop, so a bug there (as happened 2026-11-15: `from cc_common import fail` at module level meant `cc.py source status` itself was
   unreachable the moment anything was locked, exactly when it is most needed) would pass step 1 and still break the real command.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL_SCRIPTS = HERE.parent / "scripts"
PY = sys.executable
failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failed += 1


DUMMY_A = '"""cc_dummy_a.py - a stand-in for a real cc_*.py module; not part of the real toolkit."""\n\n\ndef value():\n    return "A-OK"\n'
DUMMY_B = ('"""cc_dummy_b.py - imports cc_dummy_a, like cc_notify.py imports cc_report: tests that the hook also covers inter-module imports."""\n\n'
           'from cc_dummy_a import value as _a\n\n\ndef value():\n    return "B:" + _a()\n')

# a dummy for the MODULES loop in cc.py, named like a real entry so cc.py's own `importlib.import_module(name)` picks it up unmodified;
# uses __file__ at module level, which is exactly what broke once a locked module's code ran without the loader setting it.
DUMMY_PROC = '''"""cc_proc.py - dummy stand-in for the real module (only for this test); cc.py's own MODULES tuple names it, so the entry point
exercises its real import path. References __file__ at module level like most real cc_*.py modules do."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _cmd_probe(a):
    sys.stdout.write(json.dumps({"ok": True, "here": HERE.name}) + "\\n")


def register(sub):
    p = sub.add_parser("probe", help="dummy test command")
    p.set_defaults(func=_cmd_probe)
'''


def run(code: str, env_extra: dict, expect_ok: bool | None = None) -> subprocess.CompletedProcess:
    env = {**{k: v for k, v in os.environ.items() if k != "CC_SOURCE_KEY"}, **env_extra}    # the real key, once it is set on this PC, must never leak into a "no key" case
    cp = subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, env=env, timeout=30)
    if expect_ok is not None:
        check((cp.returncode == 0) == expect_ok, f"exit code {cp.returncode} (expected {'0' if expect_ok else 'nonzero'}): {(cp.stderr or '')[-200:]}")
    return cp


def run_cc(scripts: Path, args: list, key: str | None = None, expect_ok: bool | None = None) -> subprocess.CompletedProcess:
    """Runs the real cc.py, copied into the isolated scripts dir, as an actual subprocess: the entry point layer, not the mechanism directly."""
    env = {**os.environ, "CC_SCRIPTS_DIR": str(scripts)}
    if key is not None:
        env["CC_SOURCE_KEY"] = key
    else:
        env.pop("CC_SOURCE_KEY", None)
    cp = subprocess.run([PY, "-I", str(scripts / "cc.py"), *args], capture_output=True, text=True, env=env, timeout=30)
    if expect_ok is not None:
        check((cp.returncode == 0) == expect_ok, f"cc.py {' '.join(args)}: exit code {cp.returncode} (expected {'0' if expect_ok else 'nonzero'}): {(cp.stderr or cp.stdout)[-300:]}")
    return cp


def source_action(scripts: Path, action: str, key: str | None = None, force: bool = False) -> subprocess.CompletedProcess:
    """Runs cc_source.cmd_source(action) directly (it calls sys.exit()), pointed at the temp scripts dir: the mechanism, not the entry point."""
    code = (f"import sys, types; sys.path.insert(0, r'{scripts}'); import cc_crypto_loader; import cc_source; "
            f"cc_source.cmd_source(types.SimpleNamespace(action={action!r}, force={force}))")
    env = {**os.environ, "CC_SCRIPTS_DIR": str(scripts)}
    if key is not None:
        env["CC_SOURCE_KEY"] = key
    else:
        env.pop("CC_SOURCE_KEY", None)
    return subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, env=env, timeout=30)


def last_json(cp: subprocess.CompletedProcess) -> dict:
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else {}


def main():
    with tempfile.TemporaryDirectory(prefix="cc-source-crypto-test-") as tmp:
        scripts = Path(tmp) / "scripts"
        scripts.mkdir()
        for name in ("cc.py", "cc_crypto_loader.py", "cc_source.py"):
            shutil.copy2(REAL_SCRIPTS / name, scripts / name)
        (scripts / "cc_dummy_a.py").write_text(DUMMY_A, encoding="utf-8")
        (scripts / "cc_dummy_b.py").write_text(DUMMY_B, encoding="utf-8")
        (scripts / "cc_proc.py").write_text(DUMMY_PROC, encoding="utf-8")
        base_env = {"CC_SCRIPTS_DIR": str(scripts)}
        import_code = "import sys; sys.path.insert(0, r'%s'); import cc_crypto_loader; import cc_dummy_b; print(cc_dummy_b.value())" % scripts

        print("--- layer 1: the mechanism directly (cc_source.cmd_source) ---")
        cp = run(import_code, base_env, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"plain modules import and run with no CC_SOURCE_KEY set at all: {cp.stdout.strip()!r}")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cc_dummy_a", "").startswith("plain") and names.get("cc_dummy_b", "").startswith("plain") and names.get("cc_proc", "").startswith("plain"),
              f"status: all three dummies report plain: {names}")

        key = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = source_action(scripts, "lock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("locked", [])) == ["cc_dummy_a", "cc_dummy_b", "cc_proc"], f"lock: all three dummies locked: {res}")
        check(not (scripts / "cc_dummy_a.py").exists() and not (scripts / "cc_proc.py").exists(), "lock: the plain .py files are gone")
        check((scripts / "cc_dummy_a.py.enc").is_file() and (scripts / "cc_proc.py.enc").is_file(), "lock: the .py.enc files exist")
        enc_a_bytes = (scripts / "cc_dummy_a.py.enc").read_bytes()

        cp = run(import_code, base_env, expect_ok=False)
        check("CC_SOURCE_KEY is not set" in cp.stderr and "Traceback" not in cp.stdout, f"locked, no key: a plain ImportError, not a crash dump: {cp.stderr.strip()[-160:]}")

        wrong = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = run(import_code, {**base_env, "CC_SOURCE_KEY": wrong}, expect_ok=False)
        check("does not decrypt" in cp.stderr, f"locked, wrong key: a clear decryption-failure message: {cp.stderr.strip()[-160:]}")

        cp = run(import_code, {**base_env, "CC_SOURCE_KEY": key}, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"locked, correct key: decrypts both modules and the inter-module import works: {cp.stdout.strip()!r}")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cc_dummy_a") == "locked" and names.get("cc_proc") == "locked", f"status: dummies report locked: {names}")

        cp = source_action(scripts, "unlock", key=wrong)
        check(cp.returncode != 0 and (scripts / "cc_dummy_a.py.enc").read_bytes() == enc_a_bytes and not (scripts / "cc_dummy_a.py").exists(),
              "unlock with the wrong key fails and leaves the .enc files untouched")

        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("unlocked", [])) == ["cc_dummy_a", "cc_dummy_b", "cc_proc"], f"unlock: all three dummies unlocked: {res}")
        check((scripts / "cc_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A and (scripts / "cc_proc.py").read_text(encoding="utf-8") == DUMMY_PROC,
              "unlock: the restored source is byte-identical to the original")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(all(v.startswith("both") for v in names.values()), f"status: unlocking without re-locking leaves 'both', a reminder to re-lock: {names}")

        (scripts / "cc_dummy_a.py").write_text(DUMMY_A + "# a local edit\n", encoding="utf-8")
        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check("cc_dummy_a" in res.get("already_unlocked", []) and (scripts / "cc_dummy_a.py").read_text(encoding="utf-8").endswith("# a local edit\n"),
              "unlock without --force skips an already-unlocked module and keeps the local edit")

        cp = source_action(scripts, "unlock", key=key, force=True)
        res = last_json(cp)
        check("cc_dummy_a" in res.get("unlocked", []) and (scripts / "cc_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A,
              "unlock --force overwrites the local edit with the committed .enc content")

        print("--- layer 2: the real entry point (python cc.py ...) ---")
        cp = run_cc(scripts, ["--help"], expect_ok=True)
        check("probe" in cp.stdout and "source" in cp.stdout, "plain: cc.py --help lists both the dummy module's command and source")

        cp = run_cc(scripts, ["probe"], expect_ok=True)
        check(last_json(cp).get("here") == "scripts", f"plain: cc.py probe runs the dummy module's real command: {cp.stdout.strip()!r}")

        cp = run_cc(scripts, ["source", "lock"], key=key, expect_ok=True)
        check(sorted(last_json(cp).get("locked", [])) == ["cc_dummy_a", "cc_dummy_b", "cc_proc"], f"cc.py source lock (through the real entry point): {cp.stdout.strip()}")

        cp = run_cc(scripts, ["source", "status"], key=None, expect_ok=True)
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cc_proc") == "locked", f"THE BUG THIS CATCHES: cc.py source status must still work with NO key once cc_proc is locked: {names}")

        cp = run_cc(scripts, ["--help"], key=None, expect_ok=True)
        check("cc_proc" in cp.stdout.lower() or "locked" in cp.stdout.lower(), f"plain --help still works with cc_proc locked and no key, and says something is locked: {cp.stdout[-300:]!r}")
        check("Traceback" not in cp.stdout and "Traceback" not in cp.stderr, "no key, cc_proc locked: --help never shows a raw traceback")

        cp = run_cc(scripts, ["probe"], key=None, expect_ok=False)
        check("Traceback" not in cp.stdout and "Traceback" not in cp.stderr, "no key, cc_proc locked: `cc.py probe` fails cleanly, not a crash dump")
        check(last_json(cp).get("ok") is False and "CC_SOURCE_KEY" in last_json(cp).get("error", "") and last_json(cp).get("locked") == ["cc_proc"],
              f"no key, cc_proc locked: `cc.py probe` names the key and the locked module in one JSON error, not a bare 'invalid choice': {cp.stdout.strip()[:200]!r}")

        cp = run_cc(scripts, ["probe"], key=key, expect_ok=True)
        check(last_json(cp).get("here") == "scripts", f"THE BUG THIS CATCHES: correct key must make __file__ work inside a decrypted module, not raise NameError: {cp.stdout.strip()!r}")

        cp = run_cc(scripts, ["source", "unlock"], key=key, expect_ok=True)
        check(sorted(last_json(cp).get("unlocked", [])) == ["cc_dummy_a", "cc_dummy_b", "cc_proc"], f"cc.py source unlock (through the real entry point): {cp.stdout.strip()}")
        check((scripts / "cc_proc.py").read_text(encoding="utf-8") == DUMMY_PROC, "unlock through the real entry point restores byte-identical source too")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
