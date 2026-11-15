"""Test of scripts/setup_pc.py: the machine paths of the PC the toolkit was written on become this PC's own, in exactly the files the commands read, and nothing else.

    python tests/test_setup_pc.py

An isolated temp copy: a fake `.claude` that holds the real setup_pc.py and a copy of the real commands, skills and configs (so a path hard-coded anywhere in them fails this test),
a fake user profile and a fake CapCut install. The owner's user name in the copies is swapped for a made-up one (SETUP_PC_OLD_HOME tells the script), so the test also works where the
temp folder itself sits under the owner's profile. Two fake PCs: one with an ordinary home, one whose user name only STARTS like the original's (Olddude / OlddudeX): a second run must
not mangle it. The real toolkit is never touched.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL = HERE.parents[1]                                  # the real .claude folder (only read)
PY = sys.executable
OWNER = "Bulzart"
MADE_UP = "Olddude"                                     # the original PC's user name inside the test copies
OLD_RX = re.compile(r"C:[/\\]Users[/\\]" + MADE_UP + r"(?![\w.\-])")


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def sha(files) -> str:
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()


def scenario(label: str, profile: str | None):
    """One fake PC. `profile` None = a home inside the temp folder; a string = that user profile path (it need not exist)."""
    tmp = Path(tempfile.mkdtemp(prefix="cc-setup-test-"))
    try:
        home = tmp / "friend"
        claude = home / ".claude"
        files = ["commands/create-clips.md", "commands/create-static.md", "create-clips/config.json", "create-static/config.json", "analyze-with-loupe/config.json",
                 "create-clips/scripts/setup_pc.py"]
        for rel in files:
            (claude / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REAL / rel, claude / rel)
        for sk in sorted((REAL / "skills").glob("c[cs]-*")):
            (claude / "skills" / sk.name).mkdir(parents=True, exist_ok=True)
            shutil.copy2(sk / "SKILL.md", claude / "skills" / sk.name / "SKILL.md")
        runtime = [claude / "commands" / "create-clips.md", claude / "commands" / "create-static.md", claude / "create-clips" / "config.json",
                   claude / "create-static" / "config.json", claude / "analyze-with-loupe" / "config.json", *sorted((claude / "skills").glob("c[cs]-*/SKILL.md"))]
        for f in runtime:                                   # the copies come from a made-up original PC
            f.write_text(f.read_text(encoding="utf-8").replace(OWNER, MADE_UP), encoding="utf-8")
        local = home / "AppData" / "Local"
        for ver in ("9.6.0.1", "9.10.0.2"):                  # a fake CapCut install: the newest version (9.10 > 9.6, numerically) must win
            f = local / "CapCut" / "Apps" / ver / "Resources" / "Font" / "SystemFont" / "en.ttf"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"x")
        script = claude / "create-clips" / "scripts" / "setup_pc.py"
        user_home = profile or str(home)
        env = {**{k: v for k, v in os.environ.items() if k not in ("CC_SOURCE_KEY", "CS_SOURCE_KEY")}, "USERPROFILE": user_home, "LOCALAPPDATA": str(local),
               "HF_HOME": str(home / "hf"), "PYTHONIOENCODING": "utf-8", "SETUP_PC_OLD_HOME": f"C:/Users/{MADE_UP}"}

        def run(*args):
            cp = subprocess.run([PY, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(tmp), timeout=120)
            return cp.returncode, cp.stdout + cp.stderr

        had_old = all(any(OLD_RX.search(f.read_text(encoding="utf-8")) for f in runtime[i:i + 1]) for i in (0, 1, 2, 3, 4))
        check(had_old, f"[{label}] the test copies of the commands and the three configs hold paths of the made-up original PC (so the test can see them go)")
        before = sha(runtime)
        rc, out = run("--check")
        check(sha(runtime) == before, f"[{label}] --check changes nothing")
        check("Checklist for this PC" in out and "[!!]" in out and "[!!] " in out and "still name the original PC" in out, f"[{label}] --check prints the checklist and marks the paths still to rewrite")
        check("Whisper medium model is not cached" in out and "download_model('medium')" in out, f"[{label}] the missing Whisper model comes with the exact command that fetches it (the toolkit never downloads it by itself)")
        rc, out = run("--dry-run")
        check(sha(runtime) == before and "would rewrite" in out, f"[{label}] --dry-run lists the files and changes nothing")

        rc, out = run()
        rewritten = len(re.findall(r"^\s+rewrote:", out, re.M))
        check(rewritten >= 10, f"[{label}] the run rewrote {rewritten} files (the commands, the skills and the three configs)")
        left = [str(f.relative_to(claude)) for f in runtime if OLD_RX.search(f.read_text(encoding="utf-8"))]
        check(not left, f"[{label}] no path of the original PC is left in any command, skill or config " + ", ".join(left[:4]))
        new_py, new_claude, new_home = Path(PY).as_posix(), claude.as_posix(), Path(user_home).as_posix()
        router = (claude / "commands" / "create-clips.md").read_text(encoding="utf-8")
        check(f"`CC` = `{new_claude}/create-clips`" in router and f"`PY` = `{new_py}`" in router, f"[{label}] the router's CC and PY name this PC's toolkit folder and the Python that ran the script")
        check(f'"Bash({new_py} *)"' in router, f"[{label}] the router's allow-list names this PC's Python, so its calls need no extra approval")
        cs_cfg = (claude / "create-static" / "config.json").read_text(encoding="utf-8")
        check(f'"home": "{new_claude}/create-static"' in cs_cfg and f'"python": "{new_py}"' in cs_cfg, f"[{label}] create-static's config names its own folder and this PC's Python")
        check(f"{new_claude}/analyze-with-loupe/runs/.capcut-store.lock" in cs_cfg, f"[{label}] create-static's shared CapCut lock sits in the analyze-with-loupe folder of THIS copy (the same lock create-clips uses)")
        cc_cfg = (claude / "create-clips" / "config.json").read_text(encoding="utf-8")
        check(f'"runs_root": "{new_home}/Documents/stream-clips/runs"' in cc_cfg and f'"awl_home": "{new_claude}/analyze-with-loupe"' in cc_cfg,
              f"[{label}] create-clips' config puts the runs under this user's Documents and awl_home at the analyze-with-loupe folder of THIS copy")
        best = (local / "CapCut" / "Apps" / "9.10.0.2" / "Resources" / "Font" / "SystemFont" / "en.ttf").as_posix()
        check(best in cs_cfg and best in (claude / "analyze-with-loupe" / "config.json").read_text(encoding="utf-8"), f"[{label}] the CapCut font path becomes the newest installed CapCut's (9.10 beats 9.6)")

        after = sha(runtime)
        rc, out = run()
        check(sha(runtime) == after and "nothing to rewrite" in out, f"[{label}] a second run rewrites nothing")
        check(MADE_UP + "XX" not in "".join(f.read_text(encoding="utf-8") for f in runtime), f"[{label}] and mangles no folder name that only starts like the original's")
        rc, out = run("--check")
        check("[ok] no path of the original PC is left" in out, f"[{label}] --check agrees: nothing of the original PC is left")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    scenario("ordinary home", None)
    scenario("name starts like the original", rf"C:\Users\{MADE_UP}X")
    print("ALL PASSED" if not check.failed else f"FAILED: {check.failed}")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
