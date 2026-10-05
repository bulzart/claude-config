#!/usr/bin/env python3
"""Auto-commit for the ~/.claude customizations repo.

Run by Claude Code hooks (Stop = after every turn, SessionStart = changes made outside Claude).
Commits whatever changed in the tracked (allow-listed) folders: commands, skills, pipelines,
hooks, memory, settings. What is tracked is decided by ~/.claude/.gitignore only.

Never blocks Claude: every failure is swallowed and the script always exits 0.
  - nothing changed            -> silent
  - committed                  -> one-line systemMessage with the short hash
  - a file over MAX_MB         -> left out (added to .git/info/exclude) and reported once
  - a new top-level folder that is neither tracked nor a known Claude Code folder -> reported once
Usage: python autocommit.py [EventName]   (reads the hook JSON on stdin when present)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
MAX_MB = 25
SHOWN = 6

# Folders/files Claude Code itself creates and updates: never tracked, never reported.
CLAUDE_MANAGED = {
    ".git", ".claude.json", ".credentials.json", ".last-cleanup", ".last-update-result.json",
    "backups", "cache", "chrome", "daemon", "daemon.log", "debug", "downloads", "file-history",
    "history.jsonl", "ide", "jobs", "local", "logs", "mcp-needs-auth-cache.json", "paste-cache",
    "plans", "plugins", "session-env", "sessions", "shell-snapshots", "state", "stats-cache.json",
    "statsig", "telemetry", "todos", "tasks", "teams", "settings.local.json", "projects",
}


def git(*args, check=False):
    cp = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=ROOT, capture_output=True,
                        text=True, encoding="utf-8", errors="replace", timeout=60)
    if check and cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip()[:300])
    return cp


def load_state(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    event = sys.argv[1] if len(sys.argv) > 1 else "manual"
    payload = {}
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    event = payload.get("hook_event_name") or event
    gitdir = ROOT / ".git"
    if not gitdir.is_dir() or (gitdir / "index.lock").exists():
        return
    state_p = gitdir / "autocommit-state.json"
    state = load_state(state_p)
    notes = []

    git("add", "-A", check=True)

    # keep oversized files out of history (local exclude, reported once)
    big = []
    staged = git("diff", "--cached", "--name-only", "--diff-filter=AM", "-z").stdout.split("\0")
    for rel in filter(None, staged):
        f = ROOT / rel
        try:
            if f.is_file() and f.stat().st_size > MAX_MB * 1024 * 1024:
                big.append(rel)
        except OSError:
            pass
    if big:
        git("reset", "-q", "--", *big)
        excl = gitdir / "info" / "exclude"
        excl.parent.mkdir(parents=True, exist_ok=True)
        with excl.open("a", encoding="utf-8") as fh:
            for rel in big:
                fh.write("/" + rel.replace("\\", "/") + "\n")
        notes.append(f"left out {len(big)} file(s) over {MAX_MB} MB: " + ", ".join(big[:3]))

    # new top-level folders that nobody decided about yet
    seen = set(state.get("reported_untracked", []))
    fresh = []
    for entry in sorted(os.listdir(ROOT)):
        if entry in CLAUDE_MANAGED or entry in seen or entry.startswith(".git"):
            continue
        if git("check-ignore", "-q", entry).returncode == 0:   # ignored = not allow-listed
            fresh.append(entry)
    if fresh:
        state["reported_untracked"] = sorted(seen | set(fresh))
        notes.append("not tracked (add  !/<name>/  to ~/.claude/.gitignore if it is yours): "
                     + ", ".join(fresh[:5]))

    status = git("diff", "--cached", "--name-status").stdout.strip().splitlines()
    msg_line = None
    if status:
        files = [ln.split("\t")[-1] for ln in status]
        head = ", ".join(files[:3]) + (f" +{len(files) - 3} more" if len(files) > 3 else "")
        sid = (payload.get("session_id") or "")[:8]
        body = "\n".join(status[:200]) + ("\n…" if len(status) > 200 else "")
        msg = f"auto({event}): {head}\n\n{body}\n" + (f"\nsession: {sid}\n" if sid else "")
        cp = git("commit", "-q", "--no-verify", "-m", msg)
        if cp.returncode == 0:
            short = git("rev-parse", "--short", "HEAD").stdout.strip()
            shown = ", ".join(files[:SHOWN]) + (f" +{len(files) - SHOWN} more" if len(files) > SHOWN else "")
            msg_line = f"~/.claude versioned: {short} ({len(files)} file(s): {shown})"

    try:
        state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
    except Exception:
        pass
    parts = [p for p in [msg_line, *notes] if p]
    if parts:
        print(json.dumps({"systemMessage": " | ".join(parts), "suppressOutput": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
