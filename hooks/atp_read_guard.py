#!/usr/bin/env python
"""PreToolUse hook for Read: refuse a WHOLE-file read of the few big files the pipeline's skills tell agents never to read whole
(they rot the context: the script is 245 KB, the model index 40 KB, the catalog snapshot 33 KB, old backups).  A read with an
offset/limit is always allowed, so editing such a file still works.  Everything else passes untouched."""
import json
import re
import sys

BIG = [
    (r"/analyze-(then-pick|then-generate)/models/index\.json$",
     "this is the 40 KB model index: use `atp.py model-entry --id <model>` for one model, or Read it with offset/limit."),
    (r"/higgsfield/catalog-snapshot-[^/]+\.json$",
     "this is a 33 KB catalog snapshot, only compared with `models_explore list` on drift: Grep it for the model, or Read with offset/limit."),
    (r"/(analyze-then-pick|analyze-then-generate|analyze-stack)/scripts/(atp|atg|analyze_stack|stack)\.py$",
     "this script is far too big to read whole: run it with `-h` / `<command> -h`, or Grep for the function and Read that range with offset/limit."),
    (r"/(analyze-then-pick|analyze-then-generate|analyze-stack)/_backups/",
     "backups are never read in a run: they are for `diff` by the person who made them. Read an excerpt with offset/limit if you really need one."),
    (r"/analyze-then-pick/caught_flags\.html$",
     "the old flag page is retired and was never to be read: flags live in Loupe (`atp.py caught-flag list`)."),
]


def main():
    ev = json.loads(sys.stdin.read() or "{}")
    ti = ev.get("tool_input") or {}
    path = str(ti.get("file_path", "")).replace("\\", "/")
    if not path or ti.get("offset") not in (None, 0, "") or ti.get("limit") not in (None, 0, ""):
        return
    for rx, why in BIG:
        if re.search(rx, path):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                              "permissionDecisionReason": f"Whole-file Read of {path.rsplit('/', 1)[-1]} refused (context rot): {why}"}}))
            return


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
