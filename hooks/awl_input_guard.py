#!/usr/bin/env python
"""PreToolUse hook (Bash, PowerShell, Write, Edit, MultiEdit, NotebookEdit) for /analyze-with-loupe, contract item 34: the user's input
folders are read-only (the user, 2026-10-27: agents never remove or move the files of the reference folder; a file they need in the run
folder or anywhere else is copied).  It refuses a command that moves, renames, deletes or writes inside a protected folder (or deletes a
folder that holds one), and a Write or Edit into one; reading it, copying from it and everything outside it pass untouched.

Protected: `source` (the references folder, or Edit Mode's videos) and `examples_paths` of every run of the library whose stage is not done
or abandoned and whose state.json changed in the last 7 days.  The assets folders stay open: the user curates them.

What it reads in a command: delete, move and rename verbs and write targets (a copy's destination, a redirection, an encoder's output) at
command position, through shell variables, `for` loops, nested shells (`bash -c`, `cmd /c`, `powershell -Command`) and line continuations;
in Python (a heredoc, `-c`, or a script it runs) a delete, move or write call aimed at a protected path or at a name that holds one.  It
fails open: any error lets the call through."""
import fnmatch
import json
import os
import posixpath
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
AWL_HOME = Path(os.environ.get("AWL_HOME") or (HOME / ".claude" / "analyze-with-loupe"))
FINAL = {"done", "abandoned"}
STALE_S = 7 * 86400
SCRIPT_EXT = (".py", ".ps1", ".sh", ".bash", ".js", ".mjs", ".cjs")
VERBS = {"rm", "rmdir", "mv", "unlink", "shred", "trash", "trash-put", "srm", "remove-item", "ri", "del", "erase", "rd",
         "move-item", "mi", "move", "rename-item", "rni", "ren", "rename"}
COPIES = {"cp", "copy", "copy-item", "cpi", "xcopy", "robocopy", "install", "rsync"}
WRITES_ALL = {"tee", "mkdir", "md", "touch", "new-item", "ni", "set-content", "add-content", "out-file", "sc", "ac"}
ENCODERS = {"ffmpeg", "ffmpeg.exe", "magick", "convert"}
CD = {"cd", "chdir", "set-location", "sl", "pushd", "push-location"}
PREFIX = {"sudo", "env", "nohup", "time", "command", "exec", "then", "do", "else", "elif", "{", "(", "&", "!", "%", "foreach-object", "call"}
NESTED = {"-c", "-command", "/c", "/k", "-commandwithargs"}
PY_DEL = re.compile(r"\b(?:os\.(?:remove|unlink|rmdir|removedirs|rename|renames|replace)|shutil\.(?:move|rmtree)|send2trash(?:\.send2trash)?)\s*\(|"
                    r"\.(?:unlink|rmdir|rename|replace)\s*\(|\bfs\.(?:unlink|rm|rmdir|rename)(?:sync)?\s*\(", re.I)
NET_DEL = re.compile(r"\[(?:system\.)?io\.(?:file|directory)\]::(?:delete|move)\s*\(|filesystem\]::(?:deletefile|deletedirectory|movefile|movedirectory)\s*\("
                     r"|\.delete\s*\(\s*\)|\.moveto\s*\(|invokeverb\s*\(\s*['\"]delete|\.movehere\s*\(", re.I)
PY_WRITE = re.compile(r"\bopen\s*\(\s*(?P<a>[^,)]+?)\s*,\s*(?:mode\s*=\s*)?['\"][^'\"]*[wax+]|(?P<b>[\w.\[\]\"'/ ()]+?)\.write_(?:text|bytes)\s*\("
                      r"|shutil\.copy(?:file|2|tree)?\s*\(\s*[^,]+,\s*(?P<c>[^)]+)\)|\[(?:system\.)?io\.file\]::(?:writeall\w*|copy)\s*\((?P<d>[^)]*)\)", re.I)
PATH = r"(?<![\w.])(?:[a-zA-Z]:/|/(?:mnt/)?[a-zA-Z]/)"


def read_shared(p) -> str:
    """A file's text, opened with FILE_SHARE_DELETE on Windows, so that it holds a writer's atomic replace as little as possible (the toolkit
    retries a replace a reader blocked; this hook runs on every shell call of every session)."""
    if os.name != "nt":
        return Path(p).read_text(encoding="utf-8")
    import ctypes
    import msvcrt
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    h = k32.CreateFileW(str(p), 0x80000000, 0x1 | 0x2 | 0x4, None, 3, 0x80, None)     # GENERIC_READ, share read|write|delete, OPEN_EXISTING
    if h is None or h == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "cannot open", str(p))
    with os.fdopen(msvcrt.open_osfhandle(h, os.O_RDONLY), "rb") as f:
        return f.read().decode("utf-8")


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
    if s.startswith("//?/"):
        s = s[4:]
    m = re.match(r"^/(?:mnt/)?([a-zA-Z])(/|$)", s)           # Git Bash /c/..., WSL /mnt/c/...
    if m:
        s = m.group(1) + ":/" + s[m.end():]
    s = posixpath.normpath(s) if s else s
    return s.lower().rstrip("/")


HOME_L = _base(str(HOME))
HOME_S = _base(_short(str(HOME)))


def norm(p: str) -> str:
    s = _base(p)
    if HOME_S and HOME_S != HOME_L and (s == HOME_S or s.startswith(HOME_S + "/")):
        s = HOME_L + s[len(HOME_S):]
    return s


def inside(p: str, folder: str) -> bool:
    return bool(p) and bool(folder) and (p == folder or p.startswith(folder + "/"))


def expand_home(text: str) -> str:
    h = str(HOME).replace("\\", "/")
    for rx in (r"\$env:userprofile", r"\$\{(?:home|userprofile)\}", r"\$(?:home|userprofile)(?![a-z0-9_])", r"%userprofile%", r"(?<![\w/~.-])~(?=[/\\])"):
        text = re.sub(rx, lambda _m: h, text, flags=re.I)
    return text


def runs_root() -> Path:
    try:
        rr = json.loads(read_shared(AWL_HOME / "config.json")).get("runs_root")
        if rr:
            return Path(os.path.expanduser(rr))
    except (OSError, ValueError):
        pass
    return AWL_HOME / "runs"


def protected() -> list:
    """[(folder or file, run name, the path as the run stores it)] of the open runs, each in its long and its 8.3 form."""
    lib = norm(str(AWL_HOME))
    res, now = [], time.time()
    try:
        entries = list(os.scandir(runs_root()))
    except OSError:
        return res
    for e in entries:
        sp = Path(e.path) / "state.json"
        try:
            if not e.is_dir() or now - sp.stat().st_mtime > STALE_S:       # a run idle for a week holds nothing
                continue
            st = json.loads(read_shared(sp))
        except (OSError, ValueError):
            continue
        if not isinstance(st, dict) or str(st.get("stage") or "").lower() in FINAL:
            continue
        src = st.get("source")
        for p in (src if isinstance(src, list) else [src]) + list(st.get("examples_paths") or []):
            if not p or not isinstance(p, str):
                continue
            n = norm(p)
            if re.fullmatch(r"[a-z]:", n) or inside(lib, n):          # a drive, or a folder holding the library itself: never guarded
                continue
            res.append((n, e.name, p))
            sh = _short(p)
            if sh and norm(sh) != n:
                res.append((norm(sh), e.name, p))
    return res


def split_outside_quotes(text: str, seps) -> list:
    out, cur, q, i = [], [], None, 0
    while i < len(text):
        ch = text[i]
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur.append(ch)
        else:
            sep = next((s for s in seps if text.startswith(s, i)), None)
            if sep:
                out.append("".join(cur))
                cur = []
                i += len(sep)
                continue
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


def segments(cmd: str) -> list:
    """The command split at newlines, ';', '&&' and '||' outside quotes (a pipeline stays one segment)."""
    return split_outside_quotes(cmd, ("&&", "||", "\n", ";"))


def tokens(seg: str) -> list:
    return [a or b or c for a, b, c in re.findall(r'"([^"]*)"|\'([^\']*)\'|(\S+)', seg)]


def quoted(seg: str) -> list:
    return [a or b for a, b in re.findall(r'"([^"]*)"|\'([^\']*)\'', seg)]


def abs_paths(text: str) -> list:
    """Every absolute Windows or Git Bash path in a text, normalised: inside quotes a path may hold spaces, outside it ends at one."""
    t = text.replace("\\", "/")
    res = []

    def grab(s, spaces):
        tail = r"[^\"'\n\r`;|&<>]*" if spaces else r"[^\s\"'`;|&<>(),]*"
        for f in re.findall(PATH + tail, s):
            res.append(norm(f.rstrip(" ),")))
    for a, b in re.findall(r'"([^"]*)"|\'([^\']*)\'', t):
        grab(a or b, True)
        grab(a or b, False)
    grab(re.sub(r'"[^"]*"|\'[^\']*\'', " ", t), False)
    return res


def resolve(tok: str, cwd: str) -> str:
    t = tok.strip().strip("\"'")
    if not t or t.startswith(("-", "$", "%", "|", "{", "(")) or "=" in t or re.match(r"^/[a-zA-Z?]{1,3}$", t) or "://" in t:
        return ""
    if re.match(r"^([a-zA-Z]:[\\/]|/)", t):
        return norm(t)
    return norm(cwd.rstrip("/") + "/" + t) if cwd else ""


def command_words(toks: list) -> list:
    """(index, word) of each token at a command position: a pipeline part's first word after prefixes (sudo, xargs and its options, env and
    its assignments, do, then, a brace), and the word after find's -exec or an opening brace."""
    res, i, n = [], 0, len(toks)
    while i < n:
        w = toks[i].lower().strip("({&@")
        if not w:
            i += 1
            continue
        if w in PREFIX or re.fullmatch(r"[a-z_]\w*=\S*", w):
            i += 1
            continue
        if w == "xargs":
            i += 1
            while i < n and toks[i].startswith("-"):
                i += 1
            continue
        if w == "git" and i + 1 < n and toks[i + 1].lower() in ("rm", "mv"):
            res.append((i + 1, toks[i + 1].lower()))
            break
        res.append((i, w))
        break
    for k, t in enumerate(toks):
        if t.lower() in ("-exec", "-execdir", "-ok") and k + 1 < n:
            res.append((k + 1, toks[k + 1].lower().strip("({")))
        if t in ("{", "(") and 0 < k and k + 1 < n:
            res.append((k + 1, toks[k + 1].lower().strip("({")))
        elif k > 0 and t[:1] in ("{", "(") and len(t) > 1:
            res.append((k, t.lower().strip("({")))
    return res


def write_targets(word: str, args: list) -> list:
    """The tokens a command writes to: a copy's destination, an encoder's output, every path of tee/mkdir/Set-Content and the like."""
    low = [a.lower() for a in args]
    for flag in ("-destination", "-path", "-filepath", "-literalpath", "-o", "--output", "-outfile"):
        if flag in low and low.index(flag) + 1 < len(args) and (word in COPIES or word in WRITES_ALL or flag in ("-o", "--output", "-outfile")):
            return [args[low.index(flag) + 1]]
    pos = [a for a in args if not a.startswith("-") and not re.match(r"^/[a-zA-Z?]{1,4}(:\S*)?$", a)]
    if word in COPIES:
        if word == "robocopy":
            return pos[1:2]
        return pos[-1:] if len(pos) >= 2 else []
    if word in ENCODERS:
        return pos[-1:]
    if word in WRITES_ALL:
        return pos
    return []


def redirections(seg: str) -> list:
    body = re.sub(r'"[^"]*"|\'[^\']*\'', lambda m: m.group(0)[0] + " " * (len(m.group(0)) - 2) + m.group(0)[-1], seg)     # a > inside quotes is no redirection
    return [seg[m.start(1):m.end(1)] for m in re.finditer(r"(?<![<>&\d-])\d?>>?\s*(\"[^\"]+\"|'[^']+'|[^\s;|&()]+)", body)
            if not re.fullmatch(r"&\d|/dev/null|nul|\$null", seg[m.start(1):m.end(1)].strip("\"'").lower())]


def hit(paths, prot, ancestors=False, globs=False):
    """The protected entry a path falls into; with ancestors, also one that falls inside the path (a folder that holds it); with globs, a
    wildcard whose pattern matches the protected folder's name under the path's folder."""
    for p in paths:
        if not p:
            continue
        name = posixpath.basename(p)
        pat = name if globs and any(c in name for c in "*?[") else ""
        base = posixpath.dirname(p) if pat else p
        for folder, run, shown in prot:
            if inside(p, folder) or (pat and inside(base, folder)):
                return shown, run
            if ancestors and not pat and inside(folder, p):
                return shown, run
            if pat and inside(folder, base) and folder != base:
                child = folder[len(base) + 1:].split("/")[0]
                if fnmatch.fnmatch(child, pat.lower()):
                    return shown, run
    return None


def python_check(code: str, prot: list, cwd: str):
    """A delete, move or write call in Python aimed at a protected path, or at a name that holds one (names are followed through assignments
    and for loops in order)."""
    tainted = set()

    def bad(expr: str) -> bool:
        return bool(hit(abs_paths(expr), prot)) or any(re.search(r"(?<![\w.])" + re.escape(n) + r"(?![\w])", expr) for n in tainted)
    lines = []
    for ln in code.splitlines():
        lines += split_outside_quotes(ln, (";",))
    for ln in lines:
        m = re.match(r"^\s*for\s+([A-Za-z_][\w, ]*?)\s+in\s+(.+?):?\s*$", ln)
        if m and bad(m.group(2)):
            tainted.update(x.strip() for x in m.group(1).split(",") if x.strip())
        m = re.match(r"^\s*(?:with\s+.+\s+as\s+)?([A-Za-z_][\w, ]*?)\s*(?::[^=]+)?=(?!=)\s*(.+)$", ln)
        if m and bad(m.group(2)):
            tainted.update(x.strip() for x in m.group(1).split(",") if x.strip())
        if PY_DEL.search(ln) or NET_DEL.search(ln):
            if bad(ln) or (not abs_paths(ln) and not tainted and cwd and hit([cwd], prot) and re.search(r"['\"][^'\"]+['\"]", ln)):
                return "a delete or move call"
        for m in PY_WRITE.finditer(ln):
            target = next((g for g in m.groups() if g), "")
            if target and bad(target):
                return "a write call"
    return None


def _own_code() -> list:
    return [norm(str(HOME / ".claude" / d)) for d in ("analyze-with-loupe/scripts", "loupe", "hooks")]


def check_command(cmd: str, cwd: str, prot: list, depth: int = 0):
    if depth > 3:
        return None
    text = expand_home(re.sub(r"(?:\\|`)\r?\n", " ", cmd))       # line continuations
    cwd = norm(cwd) if cwd else ""
    env, loopvars = {}, set()

    def subst(seg: str) -> str:
        def rep(m):
            name = m.group(1) or m.group(2) or m.group(3)
            return env.get(name, env.get(name.lower(), m.group(0)))
        return re.sub(r"\$\{(\w+)\}|\$(?:env:)?(\w+)|%(\w+)%", rep, seg)
    what = python_check(text, prot, cwd)
    if what:
        return (hit(abs_paths(text), prot) or hit([cwd], prot) or (prot[0][2], prot[0][1])), what
    for raw in segments(text):
        seg = subst(raw)
        toks = tokens(seg)
        if not toks:
            continue
        m = re.match(r"^(?:export\s+|set\s+)?([A-Za-z_]\w*)=(.*)$", seg) or re.match(r"^\$([A-Za-z_]\w*)\s*=\s*(.+)$", seg)
        if m:
            val = m.group(2).strip().strip("\"'")
            env[m.group(1)] = val
            env[m.group(1).lower()] = val
            continue
        m = re.match(r"^for\s+(\w+)\s+in\s+(.+)$", seg) or re.match(r"^foreach\s*\(\s*\$(\w+)\s+in\s+(.+?)\)", seg, re.I)
        if m and (hit(abs_paths(m.group(2)), prot) or (cwd and hit([cwd], prot))):
            loopvars.update((m.group(1), m.group(1).lower()))
        if toks[0].lower().strip("({&") in CD:
            cwd = next((r for r in (resolve(x, cwd) for x in toks[1:]) if r), cwd)
            continue
        for k, t in enumerate(toks[:-1]):                     # a nested shell: bash -c "...", cmd /c "...", powershell -Command "..."
            if t.lower() in NESTED:
                inner = check_command(toks[k + 1], cwd, prot, depth + 1)
                if inner:
                    return inner
        for q in quoted(seg):                                  # a command inside quotes (os.system('rm ...'), a -c body)
            if " " in q.strip() and q.strip() != seg.strip():
                inner = check_command(q, cwd, prot, depth + 1)
                if inner:
                    return inner
        for t in toks:                                         # a script it runs (the pipeline's own code is never read)
            if not t.lower().endswith(SCRIPT_EXT):
                continue
            p = resolve(t, cwd)
            if not p or any(inside(p, o) for o in _own_code()):
                continue
            try:
                f = Path(p)
                scr = f.read_text(encoding="utf-8", errors="replace") if f.is_file() and f.stat().st_size < 1_000_000 else ""
            except OSError:
                scr = ""
            if not scr:
                continue
            what = python_check(expand_home(scr), prot, cwd) if p.endswith(".py") else None
            if what:
                return (hit(abs_paths(expand_home(scr)) + abs_paths(seg), prot) or hit([cwd], prot) or (prot[0][2], prot[0][1])), "a script with " + what
            if not p.endswith(".py"):
                inner = check_command(scr, cwd, prot, depth + 1)
                if inner:
                    return inner
        for part in split_outside_quotes(seg, ("|",)):
            ptoks = tokens(part)
            for i, w in command_words(ptoks):
                args = ptoks[i + 1:]
                low = [a.lower() for a in args]
                deleting = w in VERBS or (w == "find" and "-delete" in low) or (w == "robocopy" and ("/mov" in low or "/move" in low)) \
                    or (w == "rsync" and "--remove-source-files" in low)
                if deleting:
                    if loopvars and any(re.search(r"\$\{?(?:" + "|".join(map(re.escape, loopvars)) + r")\b", a) for a in args):
                        h = hit([r for r in abs_paths(text)], prot) or (prot[0][2], prot[0][1])
                        return h, f"`{w}` on the files of a loop over a protected folder"
                    cands = [r for r in (resolve(a, cwd) for a in args) if r] + abs_paths(part)
                    if i == 0 or not cands:
                        cands += abs_paths(seg)                # a pipeline: the files come from the part before
                    h = hit(cands or [cwd], prot, ancestors=True, globs=True)
                    if h:
                        return h, f"`{w}`"
                h = hit([r for r in (resolve(a, cwd) for a in write_targets(w, args)) if r], prot, globs=True)
                if h:
                    return h, f"`{w}` writing"
        h = hit([r for r in (resolve(x, cwd) for x in redirections(seg)) if r], prot)
        if h:
            return h, "a redirection writing"
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
