"""Test of encryption-at-rest for the cc_*.py modules (cc_crypto_loader.py, cc_source.py): the mechanism, never the real source.

    python tests/test_source_crypto.py

Everything happens in an isolated temp copy (CC_SCRIPTS_DIR points cc_crypto_loader.py and cc_source.py at it): two small dummy modules stand
in for real cc_*.py modules, so this never touches, locks or unlocks a single file of the real create-clips/scripts/. Checks: unlocked needs no
key at all; locked without a key, or with the wrong key, fails with a plain message and nothing runs; locked with the right key behaves exactly
like the unlocked original; unlock restores byte-identical source; `source status` reports plain/locked/both correctly; `unlock` without --force
never clobbers a local edit, `--force` does.
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


def run(code: str, env_extra: dict, expect_ok: bool | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_extra}
    cp = subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, env=env, timeout=30)
    if expect_ok is not None:
        check((cp.returncode == 0) == expect_ok, f"exit code {cp.returncode} (expected {'0' if expect_ok else 'nonzero'}): {(cp.stderr or '')[-200:]}")
    return cp


def source_action(scripts: Path, action: str, key: str | None = None, force: bool = False) -> subprocess.CompletedProcess:
    """Runs cc_source.cmd_source(action) in its own process (it calls sys.exit()), pointed at the temp scripts dir."""
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
        shutil.copy2(REAL_SCRIPTS / "cc_crypto_loader.py", scripts / "cc_crypto_loader.py")
        shutil.copy2(REAL_SCRIPTS / "cc_source.py", scripts / "cc_source.py")
        (scripts / "cc_dummy_a.py").write_text(DUMMY_A, encoding="utf-8")
        (scripts / "cc_dummy_b.py").write_text(DUMMY_B, encoding="utf-8")
        base_env = {"CC_SCRIPTS_DIR": str(scripts)}
        import_code = "import sys; sys.path.insert(0, r'%s'); import cc_crypto_loader; import cc_dummy_b; print(cc_dummy_b.value())" % scripts

        # 1. plain: no key needed at all, works like a normal import
        cp = run(import_code, base_env, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"plain modules import and run with no CC_SOURCE_KEY set at all: {cp.stdout.strip()!r}")

        # 2. status: both plain
        cp = source_action(scripts, "status")
        st = last_json(cp)
        names = {m["name"]: m["state"] for m in st["modules"]}
        check(names.get("cc_dummy_a", "").startswith("plain") and names.get("cc_dummy_b", "").startswith("plain"), f"status: both dummies report plain: {names}")

        # 3. lock with a real key; the plain files must be gone, the .enc present
        key = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = source_action(scripts, "lock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("locked", [])) == ["cc_dummy_a", "cc_dummy_b"], f"lock: both dummies locked: {res}")
        check(not (scripts / "cc_dummy_a.py").exists() and not (scripts / "cc_dummy_b.py").exists(), "lock: the plain .py files are gone")
        check((scripts / "cc_dummy_a.py.enc").is_file() and (scripts / "cc_dummy_b.py.enc").is_file(), "lock: the .py.enc files exist")
        enc_a_bytes = (scripts / "cc_dummy_a.py.enc").read_bytes()

        # 4. locked, no key: a clear failure, nothing runs
        cp = run(import_code, base_env, expect_ok=False)
        check("CC_SOURCE_KEY is not set" in cp.stderr and "Traceback" not in cp.stdout, f"locked, no key: a plain ImportError, not a crash dump: {cp.stderr.strip()[-160:]}")

        # 5. locked, wrong key: a clear failure naming the problem, not a silent wrong answer
        wrong = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = run(import_code, {**base_env, "CC_SOURCE_KEY": wrong}, expect_ok=False)
        check("does not decrypt" in cp.stderr, f"locked, wrong key: a clear decryption-failure message: {cp.stderr.strip()[-160:]}")

        # 6. locked, correct key: behaves exactly like the plain original, including an import chain between two protected modules
        cp = run(import_code, {**base_env, "CC_SOURCE_KEY": key}, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"locked, correct key: decrypts both modules and the inter-module import works: {cp.stdout.strip()!r}")

        # 7. status: both locked
        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cc_dummy_a") == "locked" and names.get("cc_dummy_b") == "locked", f"status: both dummies report locked: {names}")

        # 8. unlock with the wrong key: fails, touches nothing
        cp = source_action(scripts, "unlock", key=wrong)
        check(cp.returncode != 0 and (scripts / "cc_dummy_a.py.enc").read_bytes() == enc_a_bytes and not (scripts / "cc_dummy_a.py").exists(),
              "unlock with the wrong key fails and leaves the .enc files untouched")

        # 9. unlock with the correct key: byte-identical to the original source
        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("unlocked", [])) == ["cc_dummy_a", "cc_dummy_b"], f"unlock: both dummies unlocked: {res}")
        check((scripts / "cc_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A and (scripts / "cc_dummy_b.py").read_text(encoding="utf-8") == DUMMY_B,
              "unlock: the restored source is byte-identical to the original")
        check((scripts / "cc_dummy_a.py.enc").is_file(), "unlock leaves the .py.enc in place too (status can tell 'both' apart from 'plain')")

        # 10. status: both (plain and .enc both present) until the next lock
        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(all(v.startswith("both") for v in names.values()), f"status: unlocking without re-locking leaves 'both', a reminder to re-lock: {names}")

        # 11. unlock again without --force: does not clobber a local edit
        (scripts / "cc_dummy_a.py").write_text(DUMMY_A + "# a local edit\n", encoding="utf-8")
        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check("cc_dummy_a" in res.get("already_unlocked", []) and (scripts / "cc_dummy_a.py").read_text(encoding="utf-8").endswith("# a local edit\n"),
              "unlock without --force skips an already-unlocked module and keeps the local edit")

        # 12. unlock --force: overwrites the local edit with what the .enc holds
        cp = source_action(scripts, "unlock", key=key, force=True)
        res = last_json(cp)
        check("cc_dummy_a" in res.get("unlocked", []) and (scripts / "cc_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A,
              "unlock --force overwrites the local edit with the committed .enc content")

        # 13. a run that never sets CC_SOURCE_KEY at all still works once unlocked (no residual dependency on the key)
        cp = run(import_code, base_env, expect_ok=True)
        check("B:A-OK" in cp.stdout, "fully unlocked again: no key needed, exactly like step 1")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
