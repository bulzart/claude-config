#!/usr/bin/env python
"""PreToolUse hook (Bash, PowerShell, Write, Edit, MultiEdit, NotebookEdit) for /analyze-with-loupe, contract item 34: the user's input
folders are read-only (the user, 2026-10-27: agents never remove or move the files of the reference folder; a file they need in the run
folder or anywhere else is copied).  It refuses a shell command that moves, renames or deletes inside a protected folder, and a Write or
Edit into one; reading it, copying from it and everything outside it pass untouched.  Protected: `source` (the references folder, or Edit
Mode's videos) and `examples_paths` of every run of the library whose stage is not done or abandoned.  The assets folders stay open: the
user curates them.  It fails open: any error lets the call through."""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
AWL_HOME = Path(os.environ.get("AWL_HOME") or (HOME / ".claude" / "analyze-with-loupe"))
FINAL = {"done", "abandoned"}
SCRIPT_EXT = (".py", ".ps1", ".sh", ".bash", ".js", ".mjs", ".cjs")
VERBS = {"rm", "rmdir", "mv", "unlink", "shred", "trash", "trash-put", "srm", "remove-item", "ri", "del", "erase", "rd",
         "move-item", "mi", "move", "rename-item", "rni", "ren", "rename"}
CD = {"cd", "chdir", "set-location", "sl", "pushd", "push-location"}
API = re.compile(r"\[(system\.)?io\.(file|directory)\]::(delete|move)\s*\(|filesystem\]::(deletefile|deletedirectory|movefile|movedirectory)\s*\("
                 r"|\.delete\s*\(\s*\)|\.moveto\s*\(|invokeverb\s*\(\s*['\"]delete|\.movehere\s*\("
                 r"|\b(os\.(remove|unlink|rmdir|removedirs|rename|renames|replace)|shutil\.(move|rmtree)|send2trash)\s*\("
                 r"|\.(unlink|rmdir|rename)\s*\(|\bfs\.(unlink|rm|rmdir|rename)(sync)?\s*\(")
PATH = r"(?<![\w.])(?:[a-zA-Z]:/|/(?:mnt/)?[a-zA-Z]/)"


def _short(p: str) -> str:
    """The 8.3 form of an existing Windows path (C:/Users/GLARES~1/...), or ''."""
    if os.name != "nt":
        return ""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        n = ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 32768)
        return buf.value if 0 < n < 32768 else ""
    except Exception:  # noqa: BLE001
        return ""


def _base(p: str) -> str:
    s = str(p).strip().strip("\"'").replace("\\", "/")
    m = re.match(r"^/(?:mnt/)?([a-zA-Z])(/|$)", s)           # Git Bash /c/..., WSL /mnt/c/...
    if m:
        s = m.group(1) + ":/" + s[m.end():]
    return re.sub(r"(?<=.)/{2,}", "/", s).lower().rstrip("/")


HOME_L = _base(str(HOME))
HOME_S = _base(_short(str(HOME)))


def norm(p: str) -> str:
    s = _base(p)
    if HOME_S and HOME_S != HOME_L and (s == HOME_S or s.startswith(HOME_S + "/")):
        s = HOME_L + s[len(HOME_S):]
    return s


def inside(p: str, folder: str) -> bool:
    return bool(p) and (p == folder or p.startswith(folder + "/"))


def expand(text: str) -> str:
    h = str(HOME).replace("\\", "/")
    for rx in (r"\$env:userprofile", r"\$\{home\}", r"\$home(?![a-z0-9_])", r"%userprofile%", r"(?<![\w/~.-])~(?=[/\\])"):
        text = re.sub(rx, lambda _m: h, text, flags=re.I)
    return text


def runs_root() -> Path:
    try:
        rr = json.loads((AWL_HOME / "config.json").read_text(encoding="utf-8")).get("runs_root")
        if rr:
            return Path(os.path.expanduser(rr))
    except (OSError, ValueError):
        pass
    return AWL_HOME / "runs"


def protected() -> list:
    """[(folder or file, run name)] of the open runs, each in its long and its 8.3 form."""
    lib = norm(str(AWL_HOME))
    res = []
    for sp in runs_root().glob("*/state.json"):
        try:
            st = json.loads(sp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(st, dict) or str(st.get("stage") or "").lower() in FINAL:
            continue
        src = st.get("source")
        items = (src if isinstance(src, list) else [src]) + list(st.get("examples_paths") or [])
        for p in items:
            if not p or not isinstance(p, str):
                continue
            n = norm(p)
            if n.count("/") < 2 or inside(lib, n):         # a drive, a top folder or a folder holding the library itself: never guarded
                continue
            res.append((n, sp.parent.name))
            sh = _short(p)
            if sh and norm(sh) != n:
                res.append((norm(sh), sp.parent.name))
    return res


def segments(cmd: str) -> list:
    """The command split at newlines, ';', '&&' and '||' outside quotes (a pipeline stays one segment)."""
    segs, cur, q, i = [], [], None, 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur.append(ch)
        elif ch in "\n;" or cmd.startswith("&&", i) or cmd.startswith("||", i):
            segs.append("".join(cur))
            cur = []
            if ch in "&|":
                i += 1
        else:
            cur.append(ch)
        i += 1
    segs.append("".join(cur))
    return [s.strip() for s in segs if s.strip()]


def tokens(seg: str) -> list:
    return [a or b or c for a, b, c in re.findall(r'"([^"]*)"|\'([^\']*)\'|(\S+)', seg)]


def abs_paths(text: str) -> list:
    """Every absolute Windows or Git Bash path in a text, normalised: inside quotes a path may hold spaces, outside it ends at one."""
    t = text.replace("\\", "/")
    res = []

    def grab(s, spaces):
        tail = r"[^\"'\n\r`;|&<>]*" if spaces else r"[^\s\"'`;|&<>()]*"
        for f in re.findall(PATH + tail, s):
            res.append(norm(f.rstrip(" ),")))
    for a, b in re.findall(r'"([^"]*)"|\'([^\']*)\'', t):
        grab(a or b, True)
        grab(a or b, False)
    grab(re.sub(r'"[^"]*"|\'[^\']*\'', " ", t), False)
    return res


def verb_of(toks: list):
    for i, t in enumerate(toks):
        w = t.lower().strip("(){}&@;,")
        if w in VERBS:
            return i
        if w == "find" and any(x.lower() == "-delete" for x in toks[i + 1:]):
            return i
        if w == "robocopy" and any(x.lower() in ("/mov", "/move") for x in toks[i + 1:]):
            return i
        if w == "rsync" and any(x.lower() == "--remove-source-files" for x in toks[i + 1:]):
            return i
    return None


def resolve(tok: str, cwd: str) -> str:
    t = tok.strip().strip("\"'")
    if not t or t.startswith(("-", "$", "%", "|")) or "=" in t or re.match(r"^/[a-zA-Z?]{1,3}$", t):
        return ""
    if re.match(r"^([a-zA-Z]:[\\/]|/)", t):
        return norm(t)
    return norm(cwd.rstrip("/") + "/" + t) if cwd else ""


def script_text(toks: list, cwd: str) -> str:
    own = [norm(str(HOME / ".claude" / d)) for d in ("analyze-with-loupe/scripts", "loupe", "hooks")]
    out = []
    for t in toks:
        if not t.lower().endswith(SCRIPT_EXT):
            continue
        p = resolve(t, cwd)
        if not p or any(inside(p, o) for o in own):
            continue
        try:
            f = Path(p)
            if f.is_file() and f.stat().st_size < 1_000_000:
                out.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(out)


def hit(paths, prot):
    for p in paths:
        for folder, run in prot:
            if inside(p, folder):
                return folder, run
    return None


def check_command(cmd: str, cwd: str, prot: list):
    text = expand(cmd)
    cwd = norm(cwd) if cwd else ""
    # a delete or move written as a call (a Python heredoc or -c, .NET, Node): anywhere in the command, with a guarded path anywhere in it
    if API.search(text.lower()):
        h = hit(abs_paths(text), prot) or (hit([cwd], prot) if cwd else None)
        if h:
            return h, "a delete or move call"
    for seg in segments(text):
        toks = tokens(seg)
        if not toks:
            continue
        if toks[0].lower().strip("(){}&@;,") in CD:
            cwd = next((r for r in (resolve(x, cwd) for x in toks[1:]) if r), cwd)
            continue
        scr = script_text(toks, cwd)
        if scr and (API.search(scr.lower()) or any(verb_of(tokens(line)) is not None for line in segments(scr))):
            h = hit(abs_paths(expand(scr)) + abs_paths(seg), prot)
            if h:
                return h, "a script that deletes or moves files"
        i = verb_of(toks)
        if i is None:
            continue
        cands = abs_paths(seg) + [r for r in (resolve(t, cwd) for t in toks[i + 1:]) if r]
        h = hit(cands or [cwd], prot)
        if h:
            return h, f"`{toks[i]}`"
    return None


def main():
    ev = json.loads(sys.stdin.read() or "{}")
    tool, ti = ev.get("tool_name") or "", ev.get("tool_input") or {}
    prot = protected()
    if not prot:
        return
    found = None
    if tool in ("Bash", "PowerShell"):
        found = check_command(str(ti.get("command") or ""), str(ev.get("cwd") or ""), prot)
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        p = norm(str(ti.get("file_path") or ti.get("notebook_path") or ""))
        h = hit([p], prot) if p else None
        found = (h, f"a {tool}") if h else None
    if not found:
        return
    (folder, run), what = found
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": (
        f"Refused by /analyze-with-loupe item 34: {what} would move, rename, delete or write inside {folder}, an input folder of the open run "
        f"{run}. The user's folders are read-only: copy what you need into the run folder (cp, Copy-Item, shutil.copy2) and leave the "
        "original where it is; a step that cleans up its own files does so in a command that names only the run folder. If the user "
        "explicitly asked for this change, tell them it is refused while that run is open: they can make it themselves.")}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
