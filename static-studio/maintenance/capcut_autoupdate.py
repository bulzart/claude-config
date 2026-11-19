#!/usr/bin/env python3
"""Keep this PC's CapCut on the version it is on: switch its automatic updates off, and back on.

    python capcut_autoupdate.py status      what is set now (never changes anything)
    python capcut_autoupdate.py block       CapCut's own switches off + a safety net on its Apps folder
    python capcut_autoupdate.py unblock     both undone (run this before updating CapCut yourself)

Two layers, both reversible, nothing else touched:
  1. CapCut's own settings, User Data\\Config\\globalSetting: enableAutoUpdate and totalSilentUpgradeSwitch become false (only those two
     lines change; the file's encoding and line endings stay; the first original is kept beside it as globalSetting.before-autoupdate-block).
  2. A deny entry for the current user on %LOCALAPPDATA%\\CapCut\\Apps, THIS FOLDER ONLY, for creating files and sub-folders there. Starting
     and running CapCut never creates anything directly in Apps (the folder's own timestamp did not change on any launch since the last
     update); installing a new version does (a new Apps\\<version> folder). Existing files and folders are untouched and still work.
CapCut must be closed to change its settings (it rewrites the file when it exits). Every call prints one JSON object on its last line
(exit 0 ok, 1 failed, 3 CapCut is running).
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LA = Path(os.environ.get("LOCALAPPDATA", ""))
APPS = LA / "CapCut" / "Apps"
CONFIG = LA / "CapCut" / "User Data" / "Config" / "globalSetting"
UPDATE_INFO = LA / "CapCut" / "User Data" / "Config" / "updateInfo"
BACKUP = CONFIG.with_name("globalSetting.before-autoupdate-block")
KEYS = ("enableAutoUpdate", "totalSilentUpgradeSwitch")
USER = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}"


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def capcut_running():
    try:
        cp = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], capture_output=True, text=True, timeout=30)
        return "capcut.exe" in (cp.stdout or "").lower()
    except Exception:  # noqa: BLE001
        return False


def values(data: bytes) -> dict:
    text = data.decode("utf-8", "replace")
    return {k: (re.search(rf"(?m)^{k}=([^\r\n]*)", text) or [None, None])[1] for k in KEYS}


def with_values(data: bytes, new: dict) -> bytes:
    for key, val in new.items():
        pat = re.compile(rb"(?m)^" + key.encode() + rb"=[^\r\n]*")
        if len(pat.findall(data)) != 1:
            raise RuntimeError(f"{key} is not exactly once in {CONFIG.name}: CapCut's settings file has changed shape; nothing was changed")
        data = pat.sub((key + "=" + val).encode(), data)
    return data


def deny_entry() -> str | None:
    """The deny entry this script put on Apps for the current user (e.g. '(WD,AD)'), else None."""
    cp = subprocess.run(["icacls", str(APPS)], capture_output=True, text=True, timeout=60)
    for line in (cp.stdout or "").splitlines():
        if USER.lower() in line.lower() and "(DENY)" in line:
            m = re.search(r"\(DENY\)\(([^)]*)\)", line)
            return f"({m.group(1)})" if m else "(DENY)"
    return None


def state() -> dict:
    cur = values(CONFIG.read_bytes())
    versions = sorted(p.name for p in APPS.iterdir() if p.is_dir())
    info = UPDATE_INFO.read_text(encoding="utf-8", errors="replace") if UPDATE_INFO.is_file() else ""
    active = re.search(r'full_appver value="([^"]+)"', (APPS / "ProductInfo.xml").read_text(encoding="utf-8", errors="replace"))
    deny = deny_entry()
    blocked = all(v == "false" for v in cur.values()) and deny is not None
    return {"settings": cur, "apps_folder_deny": deny, "blocked": blocked, "active_version": active.group(1) if active else None,
            "versions_installed": versions, "join_beta": (re.search(r"(?m)^joinBeta=(\S+)", info) or [None, None])[1],
            "capcut_running": capcut_running(), "backup_of_original": str(BACKUP) if BACKUP.is_file() else None}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd not in ("status", "block", "unblock"):
        out({"ok": False, "error": "usage: capcut_autoupdate.py status | block | unblock"}, 1)
    if not APPS.is_dir() or not CONFIG.is_file():
        out({"ok": False, "error": f"CapCut's Apps folder or settings file not found under {LA / 'CapCut'}"}, 1)
    before = state()
    if cmd == "status":
        out({"ok": True, **before})
    if before["capcut_running"]:
        out({"ok": False, "error": "CapCut is running: close it first (it rewrites its settings when it exits); nothing was changed",
             "capcut_running": True}, 3)
    data = CONFIG.read_bytes()
    if cmd == "block":
        if not BACKUP.exists():
            shutil.copyfile(CONFIG, BACKUP)
        new = with_values(data, {k: "false" for k in KEYS})
        if new != data:
            CONFIG.write_bytes(new)
        if before["apps_folder_deny"] is None:
            cp = subprocess.run(["icacls", str(APPS), "/deny", f"{USER}:(WD,AD)"], capture_output=True, text=True, timeout=60)
            if cp.returncode != 0:
                out({"ok": False, "error": "icacls refused: " + (cp.stdout + cp.stderr)[-300:], "before": before}, 1)
    else:   # unblock: the values the backup holds (the originals), else true
        original = values(BACKUP.read_bytes()) if BACKUP.is_file() else {}
        new = with_values(data, {k: ("true" if original.get(k) in (None, "false") else original[k]) for k in KEYS})
        if new != data:
            CONFIG.write_bytes(new)
        if before["apps_folder_deny"] is not None:
            cp = subprocess.run(["icacls", str(APPS), "/remove:d", USER], capture_output=True, text=True, timeout=60)
            if cp.returncode != 0:
                out({"ok": False, "error": "icacls refused: " + (cp.stdout + cp.stderr)[-300:], "before": before}, 1)
    after = state()
    ok = after["blocked"] if cmd == "block" else (not after["blocked"] and after["apps_folder_deny"] is None
                                                  and all(v == "true" for v in after["settings"].values()))
    out({"ok": ok, "did": cmd, "before": {k: before[k] for k in ("settings", "apps_folder_deny", "blocked")}, "after": after},
        0 if ok else 1)


if __name__ == "__main__":
    main()
