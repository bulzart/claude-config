#!/usr/bin/env python
"""PreCompact hook (manual /compact and auto-compact): hands the summarizer the "# Compact Instructions" section of
~/.claude/CLAUDE.md.  Claude Code uses a PreCompact hook's stdout as instructions for the compaction summary
(hooks docs, PreCompact).  CLAUDE.md stays the one place the instructions are written; this only reads it.
If the user typed their own focus after /compact, it is repeated at the end so it is never lost.
It never blocks a compaction: any problem means it prints nothing and exits 0."""
import json
import sys
from pathlib import Path

CLAUDE_MD = Path(__file__).resolve().parent.parent / "CLAUDE.md"
HEADING = "# compact instructions"
CAP = 9500  # Claude Code cuts PreCompact stdout at 10,000 characters


def section():
    lines = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    out, inside = [], False
    for ln in lines:
        if ln.startswith("# "):
            if inside:
                break
            inside = ln.strip().lower() == HEADING
            continue
        if inside:
            out.append(ln)
    return "\n".join(out).strip()


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    text = section()
    if not text:
        return
    focus = (payload.get("custom_instructions") or "").strip()
    if focus:
        text += f"\n\nThe user also gave this focus for this compaction; follow it as well: {focus}"
    sys.stdout.buffer.write(text[:CAP].encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
    sys.exit(0)
