#!/usr/bin/env python3
"""Auto-commit for the ~/.claude customizations repo.

Run by Claude Code hooks (Stop = after every turn, SessionStart = changes made outside Claude).
Commits whatever changed in the tracked (allow-listed) folders: commands, skills, pipelines,
hooks, memory, settings. What is tracked is decided by ~/.claude/.gitignore only.

Never blocks Claude: every failure is swallowed and the script always exits 0.
  - nothing changed            -> silent
  - committed                  -> ONE COMMIT PER AREA, then a one-line systemMessage with the short hashes.
                                  An area is the top-level folder (commands, hooks, static-studio, ...);
                                  projects/*/memory/... is "memory" and files at the root are "config".
                                  Subject: auto(<Event>) [<area>]: file, file, file +N more
  - a file over MAX_MB         -> left out (added to .git/info/exclude) and reported once
  - a text file holding a credential shape (secret scan; *.enc ciphertext and binary files are skipped)
                               -> left out of the commit (unstaged, NOT excluded) and reported by path and
                                  pattern name, never the value, on every run until the file is fixed
  - a new top-level folder that is neither tracked nor a known Claude Code folder -> reported once
  - a merge, rebase, cherry-pick, revert or bisect in progress -> nothing is done until it is finished
  - another run of this hook busy (.git/autocommit.lock)        -> this run skips; the next one commits
Each area's commit is built in a private index from HEAD plus exactly the staged blobs that were scanned,
and it moves HEAD only if nothing else moved it meanwhile, so commits never mix areas or sessions' timing.
Usage: python autocommit.py [EventName]   (reads the hook JSON on stdin when present)
Tests: CLAUDE_AUTOCOMMIT_ROOT=<a throwaway repo> points the hook at another repository (test_autocommit.py).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_AUTOCOMMIT_ROOT") or os.environ.get("CLAUDE_CONFIG_DIR")
            or Path.home() / ".claude")
MAX_MB = 25
SHOWN = 6
LOCK_STALE_S = 120          # the hook's own timeout is 60 s

# Folders/files Claude Code itself creates and updates: never tracked, never reported.
CLAUDE_MANAGED = {
    ".git", ".claude.json", ".credentials.json", ".last-cleanup", ".last-update-result.json",
    "backups", "cache", "chrome", "daemon", "daemon.log", "debug", "downloads", "file-history",
    "history.jsonl", "ide", "jobs", "local", "logs", "mcp-needs-auth-cache.json", "paste-cache",
    "plans", "plugins", "session-env", "sessions", "shell-snapshots", "state", "stats-cache.json",
    "statsig", "telemetry", "todos", "tasks", "teams", "settings.local.json", "projects",
}
# A git operation the user is in the middle of: committing now would get in its way.
IN_PROGRESS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG", "rebase-merge", "rebase-apply")

# ---- secret scan: real credential shapes only --------------------------------------------------
# (name shown to the user, quick substring test, pattern whose first non-empty group is the random part).
# A match counts only when that part looks random (_looks_random): placeholders and prose never block.
SECRET_SHAPES = [
    ("private key", ("-----BEGIN",), re.compile(
        r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY(?: BLOCK)?-----(?:\s|\\[rn])+"
        r"(?:[A-Za-z][\w-]*:[^\r\n\\]*(?:\s|\\[rn])+){0,6}([A-Za-z0-9+/]{40,})")),
    ("sk- key", ("sk-",), re.compile(r"\bsk-([A-Za-z0-9_-]{32,})")),
    ("sk_ key", ("sk_",), re.compile(r"\bsk_([0-9a-f]{32,})\b")),
    ("AWS key", ("AKIA",), re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("GitHub token", ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"),
     re.compile(r"\b(?:gh[pousr]_([A-Za-z0-9]{36,})|github_pat_([A-Za-z0-9_]{40,}))\b")),
    ("Hugging Face token", ("hf_",), re.compile(r"\bhf_([A-Za-z0-9]{34,})\b")),
]
# A key name: any *API_KEY / *API_TOKEN / *_TOKEN / *_SECRET / *SOURCE_KEY / *PASSWORD written in capitals,
# plus the header and the names below in any case. Its value counts when it is a long literal right after it
# (NAME = "value", "NAME": "value", NAME: value) or alone on one of the next 3 lines (a value noted in a code block).
SECRET_NAME = re.compile(
    r"(?<![A-Za-z0-9])((?i:xi-api-key|eleven(?:labs)?_api_key|openai_api_key|anthropic_api_key)"
    r"|[A-Z][A-Z0-9_]*(?:API_KEY|API_TOKEN|_TOKEN|_SECRET|SOURCE_KEY|PASSWORD))")
SECRET_ASSIGN = re.compile(SECRET_NAME.pattern + r"[\"']?\]?\s*[:=,]\s*[\"']?([A-Za-z0-9_-]{20,})(?![\w(\[-])")
_BARE = re.compile(r"(?:[\s`'\">*]|-(?=\s))*([A-Za-z0-9_+/=-]{32,})[\s`'\",;]*")   # a line of one long token
ASSIGN_HINTS = ("api-key", "api_key", "api_token", "_token", "_secret", "source_key", "password")
PUBLIC_KEYS = ("phc_", "pk_live_", "pk_test_")   # client keys meant to be public (PostHog, Stripe publishable)
_PLACEHOLDER = re.compile(r"example|xxxx|your|placeholder|dummy|changeme|redacted", re.I)
_WORDS = re.compile(r"[a-z0-9]{1,15}(?:[-_/][a-z0-9]{1,15})+")    # task-lists-and-todo: a slug or path, not a key


def git(*args, check=False, input=None, env=None):
    cp = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=ROOT, capture_output=True,
                        input=None if input is None else input.encode("utf-8"), env=env, timeout=60)
    cp = subprocess.CompletedProcess(cp.args, cp.returncode, cp.stdout.decode("utf-8", "replace"),
                                     cp.stderr.decode("utf-8", "replace"))
    if check and cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip()[:300])
    return cp


def load_state(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def area_of(rel: str) -> str:
    """The area a path is committed under: its top-level folder; memory notes = "memory"; root files = "config"."""
    parts = rel.split("/")
    if len(parts) == 1:
        return "config"
    if parts[0] == "projects" and len(parts) > 3 and parts[2] == "memory":
        return "memory"
    return parts[0]


def staged_changes() -> list:
    """[(status, path, mode, blob)] of what the index holds over HEAD; a rename counts as D + A."""
    out = git("diff", "--cached", "--raw", "--no-renames", "--no-abbrev", "-z", check=True).stdout.split("\0")
    changes = []
    for meta, path in zip(out[0::2], out[1::2]):
        f = meta.lstrip(":").split()
        if len(f) == 5 and f[4][0] in "AMTD":
            changes.append((f[4][0], path, f[1], f[3]))
    return changes


def unstage(paths) -> None:
    """Take paths out of the next commit (index back to HEAD); the files on disk are not touched."""
    if paths:
        git("--literal-pathspecs", "reset", "-q", "--pathspec-from-file=-", "--pathspec-file-nul",
            input="".join(p + "\0" for p in paths), check=True)


def _looks_random(v: str, literal: bool = False) -> bool:
    """A real key is random: many distinct characters, no placeholder words, not words joined by - or _.
    An assigned value must also mix letters and digits and not be another NAME_LIKE_THIS."""
    if len(set(v)) < 8 or _PLACEHOLDER.search(v) or _WORDS.fullmatch(v):
        return False
    if literal:
        return (bool(re.search(r"[0-9]", v) and re.search(r"[A-Za-z]", v))
                and not re.fullmatch(r"[A-Z0-9]*_[A-Z0-9_]*", v) and not v.startswith(PUBLIC_KEYS))
    return True


def find_secrets(text: str) -> list:
    """Names of the credential shapes in text, never the values themselves."""
    found = []
    for name, hints, rx in SECRET_SHAPES:
        if any(h in text for h in hints) and any(
                _looks_random(next(g for g in m.groups() if g)) for m in rx.finditer(text)):
            found.append(name)

    def named(key: str, value: str) -> None:
        label = ("xi-api-key" if key.lower() == "xi-api-key" else key.upper()) + " value"
        if label not in found and _looks_random(value, literal=True):
            found.append(label)

    if any(h in text.lower() for h in ASSIGN_HINTS):
        for m in SECRET_ASSIGN.finditer(text):
            named(m.group(1), m.group(2))
        for m in SECRET_NAME.finditer(text):           # the value alone on one of the next 3 lines
            pos = text.find("\n", m.end())
            for _ in range(3):
                if pos < 0:
                    break
                nxt = text.find("\n", pos + 1)
                bare = _BARE.fullmatch(text, pos + 1, nxt if nxt >= 0 else len(text))
                if bare:
                    named(m.group(1), bare.group(1))
                pos = nxt
    return found


def _as_text(blob: bytes):
    """The blob as text, or None for a binary file (a NUL in the first 8000 bytes, as git decides)."""
    if blob[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return blob.decode("utf-16", "replace")
    if b"\0" in blob[:8000]:
        return None
    return blob.decode("utf-8", "replace")


def scan_staged(entries) -> dict:
    """{path: [shape names]} for the staged blobs that hold a credential shape. Reads exactly the blobs that
    would be committed. *.enc files (encrypted-at-rest ciphertext, random text) and binary files are skipped."""
    todo = [(p, blob) for _, p, _, blob in entries if not p.lower().endswith(".enc")]
    found = {}
    if not todo:
        return found
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for path, blob in todo:
            proc.stdin.write(blob.encode("ascii") + b"\n")
            proc.stdin.flush()
            head = proc.stdout.readline().split()
            if not head:
                raise RuntimeError("git cat-file stopped")
            if len(head) != 3:                  # "<id> missing": a submodule's commit, nothing to read
                continue
            size = int(head[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)
            if len(data) != size:
                raise RuntimeError("git cat-file stopped")
            text = _as_text(data) if head[1] == b"blob" else None
            names = find_secrets(text) if text else []
            if names:
                found[path] = names
    finally:
        try:
            proc.stdin.close()
            proc.wait(timeout=30)
        except Exception:
            proc.kill()
    return found


def commit_by_area(changes, event: str, sid: str, gitdir: Path) -> list:
    """One commit per area, in name order: [(area, commit, files)] for the ones made. Each is built in a private
    index from HEAD plus exactly these (already scanned) blobs, and HEAD moves only if nothing else moved it."""
    groups = {}
    for ch in changes:
        groups.setdefault(area_of(ch[1]), []).append(ch)
    for old in gitdir.glob("autocommit-index.*"):          # left behind by a run that was killed
        try:
            if time.time() - old.stat().st_mtime > 3600:
                old.unlink()
        except OSError:
            pass
    tmp = gitdir / f"autocommit-index.{os.getpid()}"
    env = {**os.environ, "GIT_INDEX_FILE": str(tmp)}
    made, built_on = [], None
    try:
        for area in sorted(groups):
            entries = groups[area]
            files = [p for _, p, _, _ in entries]
            head = ", ".join(files[:3]) + (f" +{len(files) - 3} more" if len(files) > 3 else "")
            lines = [f"{st}\t{p}" for st, p, _, _ in entries]
            body = "\n".join(lines[:200]) + ("\n…" if len(lines) > 200 else "")
            msg = f"auto({event}) [{area}]: {head}\n\n{body}\n" + (f"\nsession: {sid}\n" if sid else "")
            info = "".join(f"{mode} {blob}\t{p}\0" for _, p, mode, blob in entries)   # mode 000000 = deleted
            try:
                for _attempt in range(3):                   # a retry only when HEAD moved under us
                    cp = git("rev-parse", "HEAD", "HEAD^{tree}")
                    parent, parent_tree = cp.stdout.split()[:2] if cp.returncode == 0 else ("", "")
                    if parent != built_on:                  # the private index must start from HEAD itself
                        git("read-tree", parent or "--empty", env=env, check=True)
                    built_on = None
                    git("update-index", "-z", "--index-info", input=info, env=env, check=True)
                    tree = git("write-tree", env=env, check=True).stdout.strip()
                    if tree == parent_tree:                 # already in HEAD (another run committed it)
                        built_on = parent
                        break
                    new = git("commit-tree", tree, *(["-p", parent] if parent else []), input=msg,
                              check=True).stdout.strip()
                    if git("update-ref", "-m", "commit: " + msg.split("\n", 1)[0], "HEAD", new,
                           parent).returncode == 0:
                        made.append((area, new, files))
                        built_on = new
                        break
            except Exception:
                break                                       # the rest stays staged for the next run
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return made


def take_lock(gitdir: Path):
    """One run at a time, so two sessions' checkpoints never interleave. Busy -> None (this run skips, the
    next one commits); a lock older than LOCK_STALE_S was left by a killed run and is taken over."""
    lock = gitdir / "autocommit.lock"
    for _ in range(2):
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return lock
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime < LOCK_STALE_S:
                    return None
                lock.unlink()
            except OSError:
                return None
        except OSError:
            return None
    return None


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
    if any((gitdir / m).exists() for m in IN_PROGRESS):
        return
    lock = take_lock(gitdir)
    if not lock:
        return
    try:
        checkpoint(event, payload, gitdir)
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def checkpoint(event: str, payload: dict, gitdir: Path) -> None:
    state_p = gitdir / "autocommit-state.json"
    state = load_state(state_p)
    notes = []

    git("add", "-A", check=True)

    try:
        changes = staged_changes()

        # keep oversized files out of history (local exclude, reported once)
        big = []
        for st, rel, _, _ in changes:
            f = ROOT / rel
            try:
                if st != "D" and f.is_file() and f.stat().st_size > MAX_MB * 1024 * 1024:
                    big.append(rel)
            except OSError:
                pass
        if big:
            unstage(big)
            excl = gitdir / "info" / "exclude"
            excl.parent.mkdir(parents=True, exist_ok=True)
            with excl.open("a", encoding="utf-8") as fh:
                for rel in big:
                    fh.write("/" + rel.replace("\\", "/") + "\n")
            notes.append(f"left out {len(big)} file(s) over {MAX_MB} MB: " + ", ".join(big[:3]))

        # secret scan: a file holding a credential stays out of every commit (not excluded) and is
        # reported on every run, by path and pattern name only, until the file is fixed
        secrets = scan_staged([c for c in changes if c[0] != "D" and c[1] not in big])
        if secrets:
            unstage(list(secrets))
            items = [f"{p} ({', '.join(names)})" for p, names in sorted(secrets.items())]
            notes.append("NOT committed, looks like a secret (only the path and kind are shown; remove it from "
                         "the file, it is checked again every turn): " + ", ".join(items[:5])
                         + (f" +{len(items) - 5} more" if len(items) > 5 else ""))
    except Exception:
        git("reset", "-q")              # fail closed: nothing unchecked stays staged or gets committed
        notes.append("secret scan failed, nothing committed this turn")
        changes, big, secrets = [], [], {}

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

    sid = (payload.get("session_id") or "")[:8]
    skip = set(big) | set(secrets)
    made = commit_by_area([c for c in changes if c[1] not in skip], event, sid, gitdir)
    msg_line = None
    if made:
        shorts = git("rev-parse", "--short", *[c for _, c, _ in made]).stdout.split()
        if len(shorts) != len(made):
            shorts = [c[:7] for _, c, _ in made]
        files = [f for _, _, fs in made for f in fs]
        shown = ", ".join(files[:SHOWN]) + (f" +{len(files) - SHOWN} more" if len(files) > SHOWN else "")
        msg_line = ("~/.claude versioned: " + ", ".join(f"{s} [{a}]" for s, (a, _, _) in zip(shorts, made))
                    + f" ({len(files)} file(s): {shown})")

    try:
        state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
    except Exception:
        pass
    parts = [p for p in [msg_line, *notes] if p]
    if parts:
        print(json.dumps({"systemMessage": " | ".join(parts), "suppressOutput": True}), flush=True)
    if made:
        git("maintenance", "run", "--auto", "--quiet")    # what `git commit` runs after committing


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
