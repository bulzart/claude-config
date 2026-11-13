"""Stand-ins for the notification pieces, for tests/test_notify.py: nothing is shown on screen.

fake_notify.py <payload.json> [--dry-run]   replaces scripts/notify.ps1 (CC_NOTIFY_BIN points at this file): it appends the payload to FAKE_NOTIFY_OUT (a JSONL file)
                                            and answers like the real script. FAKE_NOTIFY_MODE=fail answers "notifications are not enabled" (exit 2), as the script does
                                            when the user switched toasts off.
fake_notify.py <title> <text>               replaces the message box fallback (CC_NOTIFY_BOX_CMD points at this file): appends {title, text} to FAKE_BOX_OUT.
"""
import json
import os
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if a != "--dry-run"]
dry = "--dry-run" in sys.argv
if len(args) == 1 and Path(args[0]).is_file():          # the toast stand-in: one argument, the payload file
    payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    out = os.environ.get("FAKE_NOTIFY_OUT")
    if out and not dry:
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    if os.environ.get("FAKE_NOTIFY_MODE") == "fail":
        print(json.dumps({"ok": False, "setting": "DisabledForUser", "error": "notifications are not enabled for this app (DisabledForUser)"}))
        sys.exit(2)
    print(json.dumps({"ok": True, "how": "dry-run" if dry else "toast", "setting": "Enabled"}))
else:                                                    # the message box stand-in: a title and a text
    out = os.environ.get("FAKE_BOX_OUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"title": args[0] if args else "", "text": args[1] if len(args) > 1 else ""}) + "\n")
