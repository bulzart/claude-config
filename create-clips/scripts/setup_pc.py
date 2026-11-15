#!/usr/bin/env python3
"""setup_pc.py - make a copy of the create-clips / create-static toolkit work on THIS PC. Run it once after cloning or copying the toolkit, and again whenever
you want to see what is still missing; it is safe to run twice.

    python setup_pc.py              rewrite the paths of the PC the toolkit was written on to this PC's own, then print the checklist
    python setup_pc.py --check      only print the checklist (changes nothing)
    python setup_pc.py --dry-run    list the files that would be rewritten (changes nothing)

What it rewrites (only these files, only the three machine paths below): the two commands (`commands/create-clips.md`, `commands/create-static.md`), every
`skills/cc-*` and `skills/cs-*` skill, and the three config files that carry paths (`create-clips`, `create-static`, `analyze-with-loupe`). The three paths are the
Python interpreter, the `.claude` folder and the home folder of the PC they were written on. Each becomes this PC's own: the Python that runs this script, the
`.claude` folder this script sits in, and the user profile folder. It also points `capcut.text_style.learned.font_path` at CapCut's newest installed font when the stored one is
missing. It never touches the encrypted modules, a key, a run folder or anything outside those files.

Plain Python (standard library only, no `cc_` prefix: it is not one of the modules that get encrypted), so it works before anything else is installed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# the PC the toolkit was written on (SETUP_PC_OLD_HOME: only the test sets it, to a made-up one): its python.exe, its .claude folder and its home folder are replaced by this PC's own
OLD_HOME = (os.environ.get("SETUP_PC_OLD_HOME") or "C:/Users/Bulzart").replace("\\", "/")
_PARTS = OLD_HOME.split("/")                                     # ["C:", "Users", "<name>"]
_NAME_END = r"(?![\w.\-])"                                       # the next character must not continue a folder name: C:/Users/Bulzart is not C:/Users/BulzartX
# ONE pass over the text (an inserted path is never looked at again, so a new path that starts like the old one stays as it is), either slash style
OLD_RX = re.compile(re.escape(_PARTS[0]) + r"([/\\])" + r"\1".join(re.escape(p) for p in _PARTS[1:]) + _NAME_END
                    + r"(?:(?P<py>\1AppData\1Local\1Programs\1Python\1Python312\1python\.exe)|(?P<claude>\1\.claude" + _NAME_END + r"))?")

NO_WINDOW = 0x08000000 if os.name == "nt" else 0               # CREATE_NO_WINDOW
SCRIPT = Path(os.path.abspath(__file__))
CLAUDE = SCRIPT.parents[2]                                  # <...>/.claude  (scripts -> create-clips -> .claude)
HOME = Path(os.environ.get("USERPROFILE") or Path.home())
PY = Path(sys.executable)
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA") or (HOME / "AppData" / "Local"))

PACKAGES = [("faster_whisper", "faster-whisper"), ("numpy", "numpy"), ("PIL", "Pillow"), ("cv2", "opencv-python"), ("librosa", "librosa"), ("av", "av<19"),
            ("rapidocr_onnxruntime", "rapidocr-onnxruntime"), ("cryptography", "cryptography"), ("requests", "requests"), ("pypdf", "pypdf")]


def fwd(p) -> str:
    return str(p).replace("\\", "/")


def runtime_files() -> list:
    files = [CLAUDE / "commands" / "create-clips.md", CLAUDE / "commands" / "create-static.md",
             CLAUDE / "create-clips" / "config.json", CLAUDE / "create-static" / "config.json", CLAUDE / "analyze-with-loupe" / "config.json"]
    files += [d / "SKILL.md" for d in sorted((CLAUDE / "skills").glob("c[cs]-*")) if d.is_dir()]
    return [f for f in files if f.is_file()]


def _new_path(m) -> str:
    new = fwd(PY) if m.group("py") else fwd(CLAUDE) if m.group("claude") else fwd(HOME)
    return new.replace("/", m.group(1))


def rewrite(text: str) -> str:
    return OLD_RX.sub(_new_path, text)


def newest_capcut_font() -> str | None:
    found = []
    for p in (LOCALAPPDATA / "CapCut" / "Apps").glob("*/Resources/Font/SystemFont/en.ttf"):
        ver = tuple(int(x) if x.isdigit() else 0 for x in p.parts[-5].split("."))
        found.append((ver, p))
    return fwd(max(found)[1]) if found else None


def fix_font_path(text: str) -> str:
    def sub(m):
        if Path(m.group(2)).is_file():
            return m.group(0)
        best = newest_capcut_font()
        return m.group(1) + best + m.group(3) if best else m.group(0)
    return re.sub(r'("font_path"\s*:\s*")([^"]*)(")', sub, text)


def is_original_pc() -> bool:
    """True on the PC the toolkit was written on (same user profile, same .claude folder): its paths are already right, whatever Python happens to run this script."""
    return fwd(HOME).lower() == OLD_HOME.lower() and fwd(CLAUDE).lower() == (OLD_HOME + "/.claude").lower()


def plan() -> list:
    """[(path, new text)] for every runtime file the rewrite would change."""
    changes = []
    if is_original_pc():
        return changes
    for f in runtime_files():
        raw = f.read_bytes()
        try:
            old = raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"  skipped (not UTF-8): {f}")
            continue
        new = rewrite(old)
        if f.name == "config.json":
            new = fix_font_path(new)
        if new != old:
            changes.append((f, new))
    return changes


def leftovers() -> list:
    """The lines that still hold a path of the original PC that the rewrite would change (on the original PC itself nothing would change: no leftovers)."""
    out = []
    if is_original_pc():
        return out
    for f in runtime_files():
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if rewrite(line) != line:
                out.append(f"{f}:{n}")
    return out


def have(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def tool_version(name: str, *args) -> tuple:
    exe = shutil.which(name)
    if not exe:
        return None, ""
    try:
        cp = subprocess.run([exe, *args], capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)     # the toolkit's rule: no child process opens a console window
        return exe, ((cp.stdout or cp.stderr).strip().splitlines() or [""])[0]
    except (OSError, subprocess.SubprocessError):
        return exe, ""


def key_state(pipe: str, var: str) -> tuple:
    """(ok, text): is the key set and does it decrypt this tool's smallest encrypted module. The key itself is never printed."""
    enc = sorted((CLAUDE / pipe / "scripts").glob("*.py.enc"), key=lambda p: p.stat().st_size)
    if not enc:
        return True, "no encrypted modules here (plain source): no key needed"
    key = os.environ.get(var)
    if not key:
        return False, f"{var} is not set in this window (setx {var} \"<the key you were given>\", then open a NEW terminal)"
    try:
        from cryptography.fernet import Fernet
        Fernet(key.encode("utf-8")).decrypt(enc[0].read_bytes())
        return True, f"{var} is set and decrypts {len(enc)} modules"
    except ImportError:
        return False, "the `cryptography` package is not installed (python -m pip install -r requirements.txt)"
    except Exception:  # noqa: BLE001  (a wrong key and a malformed key are the same answer here)
        return False, f"{var} is set but does NOT decrypt the modules: it is not the key these files were locked with"


def chrome_download_prompt() -> bool | None:
    p = LOCALAPPDATA / "Google" / "Chrome" / "User Data" / "Default" / "Preferences"
    try:
        return bool((json.loads(p.read_text(encoding="utf-8")).get("download") or {}).get("prompt_for_download"))
    except (OSError, ValueError):
        return None


def checklist() -> int:
    rows = []

    def row(ok, label, detail="", fix=""):
        rows.append((ok, label, detail, fix))

    v = sys.version_info
    row(v[:2] == (3, 12), f"Python {v[0]}.{v[1]}.{v[2]} at {PY}", "" if v[:2] == (3, 12) else "the toolkit was built and tested on Python 3.12", "install Python 3.12 and run this script with it")
    missing = [pip for mod, pip in PACKAGES if not have(mod)]
    row(not missing, "Python packages" + (": missing " + ", ".join(missing) if missing else ": all present"), "",
        f"cd {CLAUDE / 'create-clips'} ; python -m pip install -r requirements.txt ; cd {CLAUDE / 'create-static'} ; python -m pip install -r requirements.txt")
    for name, args, hint in (("ffmpeg", ("-version",), "winget install --id Gyan.FFmpeg --source winget   (the full build)"), ("ffprobe", ("-version",), "comes with ffmpeg"),
                             ("node", ("--version",), "winget install --id OpenJS.NodeJS.LTS --source winget")):
        exe, ver = tool_version(name, *args)
        row(bool(exe), f"{name}: {ver[:60] if exe else 'not on PATH'}", "", hint)
    exe, ver = tool_version("capcut", "--version")
    row(bool(exe) and ver.startswith("0.25"), f"capcut-cli: {ver if exe else 'not on PATH'}", "" if (exe and ver.startswith('0.25')) else "version 0.25.0 is the tested one", "npm install -g capcut-cli@0.25.0")
    drafts = LOCALAPPDATA / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    row(drafts.is_dir(), f"CapCut projects folder: {drafts}", "", "install CapCut (the toolkit's template was made with 9.7), open it once, close it")
    awl = CLAUDE / "analyze-with-loupe"
    need = [awl / "scripts" / "awl.py", awl / "data" / "capcut-catalogue.json", awl / "fonts"]
    row(all(p.exists() for p in need), f"analyze-with-loupe folder (create-clips builds its CapCut projects with its helper, fonts and catalogue): {awl}", "",
        "copy the analyze-with-loupe folder of the repo next to create-clips")
    for pipe, var in (("create-clips", "CC_SOURCE_KEY"), ("create-static", "CS_SOURCE_KEY")):
        ok, text = key_state(pipe, var)
        row(ok, f"{pipe} key: {text}")
    hf = Path(os.environ.get("HF_HOME") or (HOME / ".cache" / "huggingface")) / "hub"
    cached = sorted(hf.glob("models--*faster-whisper-medium*/snapshots/*/model.bin"))
    row(bool(cached), "Whisper medium model " + ("is cached" if cached else f"is not cached in {hf}"), "",
        "python -c \"from faster_whisper.utils import download_model; download_model('medium')\"   (about 1.4 GB, once; the toolkit never downloads it by itself)")
    row(bool(os.environ.get("ELEVEN_API_KEY")), "ELEVEN_API_KEY (create-static narration)" + (" is set" if os.environ.get("ELEVEN_API_KEY") else " is not set"), "",
        "setx ELEVEN_API_KEY \"<your ElevenLabs key>\" and open a new terminal (only needed for create-static)")
    prompt = chrome_download_prompt()
    if prompt is None:
        row(True, "Chrome download setting: not found (Chrome not installed, or another profile)")
    else:
        row(not prompt, "Chrome 'Ask where to save each file before downloading' is " + ("ON" if prompt else "off"), "",
            "Chrome > Settings > Downloads: turn it OFF, or every recorded chunk waits for a Save As dialog")
    left = leftovers()
    row(not left, "no path of the original PC is left in the commands, skills and configs" if not left else f"{len(left)} lines still name the original PC, e.g. {left[0]}", "",
        "run: python setup_pc.py")

    bad = 0
    print(f"\nChecklist for this PC (user profile {HOME}, toolkit in {CLAUDE}):\n")
    for ok, label, detail, fix in rows:
        print(f"  [{'ok' if ok else '!!'}] {label}")
        if not ok:
            bad += 1
            if detail:
                print(f"        {detail}")
            if fix:
                print(f"        fix: {fix}")
    print(f"\n{'Everything is in place.' if not bad else f'{bad} thing(s) to fix before the first run (the lines marked !! above).'}")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only print the checklist; change nothing")
    ap.add_argument("--dry-run", action="store_true", help="list the files that would be rewritten; change nothing")
    a = ap.parse_args()
    if not (CLAUDE / "create-clips").is_dir():
        sys.exit(f"this script expects to sit in <your .claude folder>\\create-clips\\scripts, but its .claude folder would be {CLAUDE}")
    if not a.check:
        changes = plan()
        if is_original_pc():
            print("Paths: this is the PC the toolkit was written on; its paths are already right (nothing is rewritten here).")
        elif not changes:
            print(f"Paths: nothing to rewrite (already set for {HOME}).")
        for f, new in changes:
            print(f"  {'would rewrite' if a.dry_run else 'rewrote'}: {f}")
            if not a.dry_run:
                f.write_bytes(new.encode("utf-8"))
        if changes and not a.dry_run:
            print(f"Paths: {len(changes)} file(s) rewritten for Python {fwd(PY)}, toolkit {fwd(CLAUDE)}, home {fwd(HOME)}.")
    if a.dry_run:
        return
    sys.exit(1 if checklist() else 0)


if __name__ == "__main__":
    main()
