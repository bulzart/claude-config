"""Test of encryption-at-rest for cs_core.py/cs_compose.py (cs_crypto_loader.py, cs_source.py, and cs.py itself): the mechanism, never the
real source.

    python tests/t04_source_crypto.py

Everything happens in an isolated temp copy (CS_SCRIPTS_DIR points cs_crypto_loader.py and cs_source.py at it): a dummy module stands in for
cs_core.py, so this never touches, locks or unlocks a single file of the real create-static/scripts/. Two layers are checked:
1. The mechanism directly (`cs_source.cmd_source`): plain needs no key; locked without a key, or with the wrong key, fails with a plain
   message and nothing runs; locked with the right key behaves exactly like the unlocked original; `source status` reports plain/locked/both
   correctly; `unlock` without --force never clobbers a local edit, `--force` does; unlock restores byte-identical source.
2. **The real entry point** (`python cs.py ...` as an actual subprocess) in every lock state, using a dummy that references `__file__` at
   module level AND nests `cs_source.register(...)` inside its own `main()`, exactly like the real cs_core.py does. This is the layer step 1
   cannot see: calling `cs_source.cmd_source()` directly never goes through cs.py's own `import cs_core`, so a bug there (as happened
   2026-11-15: cs_crypto_loader never set `__file__` on a decrypted module, and `cs.py source status` was unreachable once cs_core was locked,
   exactly when it is most needed) would pass step 1 and still break the real command.
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
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        failed += 1


DUMMY_A = '"""cs_dummy_a.py - a stand-in for cs_compose.py; not part of the real toolkit."""\n\n\ndef value():\n    return "A-OK"\n'
DUMMY_B = ('"""cs_dummy_b.py - imports cs_dummy_a, like cs_compose.py calls back into cs_core.py (HOST): tests inter-module imports through the hook."""\n\n'
           'from cs_dummy_a import value as _a\n\n\ndef value():\n    return "B:" + _a()\n')

# a dummy for cs_core.py (the real one is a 17000+ line monolith): cs.py's own `import cs_core` names it, so the entry point exercises its
# real import path. References __file__ at module level, and nests cs_source.register() inside main(), exactly like the real file does.
DUMMY_CORE = '''"""cs_core.py - dummy stand-in for the real module (only for this test); cs.py imports it by this exact name."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    import argparse
    import cs_source                # the real cs_core.py nests this registration inside main() too, not at module level
    ap = argparse.ArgumentParser(prog="cs.py")
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")
    cs_source.register(sub)
    p = sub.add_parser("probe")
    p.set_defaults(fn=lambda a: _probe())
    a = ap.parse_args()
    if not getattr(a, "fn", None):
        ap.print_help()
        sys.exit(2)
    a.fn(a)


def _probe():
    sys.stdout.write(json.dumps({"ok": True, "here": HERE.name}) + "\\n")
'''


def run(code: str, env_extra: dict, expect_ok: bool | None = None) -> subprocess.CompletedProcess:
    env = {**{k: v for k, v in os.environ.items() if k != "CS_SOURCE_KEY"}, **env_extra}    # the real key, once it is set on this PC, must never leak into a "no key" case
    cp = subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, env=env, timeout=30)
    if expect_ok is not None:
        check((cp.returncode == 0) == expect_ok, f"exit code {cp.returncode} (expected {'0' if expect_ok else 'nonzero'}): {(cp.stderr or '')[-200:]}")
    return cp


def run_cs(scripts: Path, args: list, key: str | None = None, expect_ok: bool | None = None) -> subprocess.CompletedProcess:
    """Runs the real cs.py, copied into the isolated scripts dir, as an actual subprocess: the entry point layer, not the mechanism directly."""
    env = {**os.environ, "CS_SCRIPTS_DIR": str(scripts)}
    if key is not None:
        env["CS_SOURCE_KEY"] = key
    else:
        env.pop("CS_SOURCE_KEY", None)
    cp = subprocess.run([PY, "-I", str(scripts / "cs.py"), *args], capture_output=True, text=True, env=env, timeout=30)
    if expect_ok is not None:
        check((cp.returncode == 0) == expect_ok, f"cs.py {' '.join(args)}: exit code {cp.returncode} (expected {'0' if expect_ok else 'nonzero'}): {(cp.stderr or cp.stdout)[-300:]}")
    return cp


def source_action(scripts: Path, action: str, key: str | None = None, force: bool = False) -> subprocess.CompletedProcess:
    """Runs cs_source.cmd_source(action) directly (it calls sys.exit()), pointed at the temp scripts dir: the mechanism, not the entry point."""
    code = (f"import sys, types; sys.path.insert(0, r'{scripts}'); import cs_crypto_loader; import cs_source; "
            f"cs_source.cmd_source(types.SimpleNamespace(action={action!r}, force={force}))")
    env = {**os.environ, "CS_SCRIPTS_DIR": str(scripts)}
    if key is not None:
        env["CS_SOURCE_KEY"] = key
    else:
        env.pop("CS_SOURCE_KEY", None)
    return subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, env=env, timeout=30)


def last_json(cp: subprocess.CompletedProcess) -> dict:
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else {}


def main():
    with tempfile.TemporaryDirectory(prefix="cs-source-crypto-test-") as tmp:
        scripts = Path(tmp) / "scripts"
        scripts.mkdir()
        for name in ("cs.py", "cs_crypto_loader.py", "cs_source.py"):
            shutil.copy2(REAL_SCRIPTS / name, scripts / name)
        (scripts / "cs_dummy_a.py").write_text(DUMMY_A, encoding="utf-8")
        (scripts / "cs_dummy_b.py").write_text(DUMMY_B, encoding="utf-8")
        (scripts / "cs_core.py").write_text(DUMMY_CORE, encoding="utf-8")
        base_env = {"CS_SCRIPTS_DIR": str(scripts)}
        import_code = "import sys; sys.path.insert(0, r'%s'); import cs_crypto_loader; import cs_dummy_b; print(cs_dummy_b.value())" % scripts

        print("--- layer 1: the mechanism directly (cs_source.cmd_source) ---")
        cp = run(import_code, base_env, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"plain modules import and run with no CS_SOURCE_KEY set at all: {cp.stdout.strip()!r}")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cs_dummy_a", "").startswith("plain") and names.get("cs_core", "").startswith("plain"), f"status: dummies report plain: {names}")

        key = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = source_action(scripts, "lock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("locked", [])) == ["cs_core", "cs_dummy_a", "cs_dummy_b"], f"lock: all three dummies locked: {res}")
        check(not (scripts / "cs_dummy_a.py").exists() and not (scripts / "cs_core.py").exists(), "lock: the plain .py files are gone")
        enc_a_bytes = (scripts / "cs_dummy_a.py.enc").read_bytes()

        cp = run(import_code, base_env, expect_ok=False)
        check("CS_SOURCE_KEY is not set" in cp.stderr and "Traceback" not in cp.stdout, f"locked, no key: a plain ImportError, not a crash dump: {cp.stderr.strip()[-160:]}")

        wrong = run("from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())", {}, expect_ok=True).stdout.strip()
        cp = run(import_code, {**base_env, "CS_SOURCE_KEY": wrong}, expect_ok=False)
        check("does not decrypt" in cp.stderr, f"locked, wrong key: a clear decryption-failure message: {cp.stderr.strip()[-160:]}")

        cp = run(import_code, {**base_env, "CS_SOURCE_KEY": key}, expect_ok=True)
        check("B:A-OK" in cp.stdout, f"locked, correct key: decrypts both modules and the inter-module import works: {cp.stdout.strip()!r}")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cs_dummy_a") == "locked" and names.get("cs_core") == "locked", f"status: dummies report locked: {names}")

        cp = source_action(scripts, "unlock", key=wrong)
        check(cp.returncode != 0 and (scripts / "cs_dummy_a.py.enc").read_bytes() == enc_a_bytes and not (scripts / "cs_dummy_a.py").exists(),
              "unlock with the wrong key fails and leaves the .enc files untouched")

        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check(cp.returncode == 0 and sorted(res.get("unlocked", [])) == ["cs_core", "cs_dummy_a", "cs_dummy_b"], f"unlock: all three dummies unlocked: {res}")
        check((scripts / "cs_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A and (scripts / "cs_core.py").read_text(encoding="utf-8") == DUMMY_CORE,
              "unlock: the restored source is byte-identical to the original")

        cp = source_action(scripts, "status")
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(all(v.startswith("both") for v in names.values()), f"status: unlocking without re-locking leaves 'both', a reminder to re-lock: {names}")

        (scripts / "cs_dummy_a.py").write_text(DUMMY_A + "# a local edit\n", encoding="utf-8")
        cp = source_action(scripts, "unlock", key=key)
        res = last_json(cp)
        check("cs_dummy_a" in res.get("already_unlocked", []) and (scripts / "cs_dummy_a.py").read_text(encoding="utf-8").endswith("# a local edit\n"),
              "unlock without --force skips an already-unlocked module and keeps the local edit")

        cp = source_action(scripts, "unlock", key=key, force=True)
        res = last_json(cp)
        check("cs_dummy_a" in res.get("unlocked", []) and (scripts / "cs_dummy_a.py").read_text(encoding="utf-8") == DUMMY_A,
              "unlock --force overwrites the local edit with the committed .enc content")

        print("--- layer 2: the real entry point (python cs.py ...) ---")
        cp = run_cs(scripts, ["probe"], expect_ok=True)
        check(last_json(cp).get("here") == "scripts", f"plain: cs.py probe runs the dummy module's real command: {cp.stdout.strip()!r}")

        cp = run_cs(scripts, ["source", "lock"], key=key, expect_ok=True)
        check(sorted(last_json(cp).get("locked", [])) == ["cs_core", "cs_dummy_a", "cs_dummy_b"], f"cs.py source lock (through the real entry point): {cp.stdout.strip()}")

        cp = run_cs(scripts, ["source", "status"], key=None, expect_ok=True)
        names = {m["name"]: m["state"] for m in last_json(cp)["modules"]}
        check(names.get("cs_core") == "locked", f"THE BUG THIS CATCHES: cs.py source status must still work with NO key once cs_core is locked: {names}")

        cp = run_cs(scripts, ["probe"], key=None, expect_ok=False)
        check("Traceback" not in cp.stdout and "Traceback" not in cp.stderr, "no key, cs_core locked: `cs.py probe` fails cleanly (the locked-only fallback parser), not a crash dump")
        last = [ln for ln in cp.stdout.splitlines() if ln.strip()]
        check(bool(last) and '"ok": false' in last[-1] and "CS_SOURCE_KEY" in last[-1], f"no key, cs_core locked: `cs.py probe` names the key in one JSON error, not a bare 'invalid choice': {cp.stdout.strip()[:160]!r}")

        cp = run_cs(scripts, ["probe"], key=key, expect_ok=True)
        check(last_json(cp).get("here") == "scripts", f"THE BUG THIS CATCHES: correct key must make __file__ work inside a decrypted module, not raise NameError: {cp.stdout.strip()!r}")

        cp = run_cs(scripts, ["source", "unlock"], key=key, expect_ok=True)
        check(sorted(last_json(cp).get("unlocked", [])) == ["cs_core", "cs_dummy_a", "cs_dummy_b"], f"cs.py source unlock (through the real entry point): {cp.stdout.strip()}")
        check((scripts / "cs_core.py").read_text(encoding="utf-8") == DUMMY_CORE, "unlock through the real entry point restores byte-identical source too")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
