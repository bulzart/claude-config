"""Assemble static-studio's capcut_tools.py from the CapCut commands of awl.py, function by function, byte for byte (the source LINES
of each definition are copied, never retyped). Usage:
    python -I build_capcut_tools.py <awl.py> <out.py> [--report]
--report only prints where the copy still mentions the other toolkit (nothing is written)."""
import ast
import builtins
import datetime
import hashlib
import re
import symtable
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
REPORT = "--report" in sys.argv

STARTS = ["cmd_capcut_name", "cmd_capcut_prep", "cmd_capcut_repair", "cmd_capcut_motion", "cmd_capcut_transitions",
          "cmd_capcut_font", "cmd_capcut_text_anim"]

raw = SRC.read_bytes()
text = raw.decode("utf-8").replace("\r\n", "\n")
lines = text.split("\n")
tree = ast.parse(text)
mod = symtable.symtable(text, str(SRC), "exec")

# ---- module-level definitions and imports
defs, imports = {}, {}
for node in tree.body:
    names = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names = [node.name]
    elif isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                names += [e.id for e in t.elts if isinstance(e, ast.Name)]
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        names = [node.target.id]
    for n in names:
        defs.setdefault(n, []).append(node)
    if isinstance(node, ast.Import):
        for al in node.names:
            imports[(al.asname or al.name).split(".")[0]] = node
    elif isinstance(node, ast.ImportFrom):
        for al in node.names:
            imports[al.asname or al.name] = node

tables = {}
for child in mod.get_children():
    if child.get_type() in ("function", "class"):
        tables.setdefault(child.get_name(), []).append(child)


def table_globals(table):
    out = set()
    for sym in table.get_symbols():
        if sym.is_global() and (sym.is_referenced() or sym.is_declared_global()):
            out.add(sym.get_name())
    for ch in table.get_children():
        out |= table_globals(ch)
    return out


def header_names(node):
    parts = list(getattr(node, "decorator_list", []))
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        parts += list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
        parts += [a.annotation for a in node.args.args + node.args.kwonlyargs + node.args.posonlyargs if a.annotation is not None]
        if node.returns is not None:
            parts.append(node.returns)
    if isinstance(node, ast.ClassDef):
        parts += list(node.bases) + [k.value for k in node.keywords]
    return {n.id for p in parts for n in ast.walk(p) if isinstance(n, ast.Name)}


def refs_of(name, node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        out = header_names(node)
        for t in tables.get(name, []):
            if len(tables.get(name, [])) == 1 or t.get_lineno() == node.lineno:
                out |= table_globals(t)
        return out
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


closure, queue, needed_imports, unresolved = {}, list(STARTS), set(), []
while queue:
    name = queue.pop()
    if name in closure or name not in defs:
        continue
    closure[name] = defs[name]
    for node in defs[name]:
        for r in refs_of(name, node):
            if r in defs and r not in closure:
                queue.append(r)
            elif r not in defs and r in imports:
                needed_imports.add(r)
            elif r not in defs and not hasattr(builtins, r) and r not in ("__file__", "__doc__", "__name__"):
                unresolved.append((r, name))
if unresolved:
    print("UNRESOLVED globals:", unresolved, file=sys.stderr)
    sys.exit(4)


def block_of(node):
    start = node.lineno
    if getattr(node, "decorator_list", None):
        start = min(d.lineno for d in node.decorator_list)
    while start - 2 >= 0 and lines[start - 2].lstrip().startswith("#"):   # comment lines directly above
        start -= 1
    return start, node.end_lineno


members = []
for name, nodes in closure.items():
    for node in nodes:
        s, e = block_of(node)
        members.append((s, e, name))
members.sort()
blocks = [(s, e, name, "\n".join(lines[s - 1:e])) for s, e, name in members]

import_lines = []
for r in sorted(needed_imports):
    seg = ast.get_source_segment(text, imports[r])
    if seg not in import_lines:
        import_lines.append(seg)

body = "\n\n\n".join(b[3] for b in blocks)

# ---- the deliberate changes to the copied text (each must match exactly the stated number of times)
SUBS = [
    # this toolkit's own root, config and fonts folder: never another toolkit's environment variables
    (r"\bAWL_HOME\b", "STUDIO_HOME", None),
    (r"\bAWL_FONTS_DIR\b", "STUDIO_FONTS_DIR", None),
    # the machine-wide CapCut store lock that every toolkit of this PC takes: one file, named in config.json
    ('lock = Path(cfg_get("runs_root", str(Path(__file__).resolve().parent.parent / "runs"))) / ".capcut-store.lock"',
     'lock = Path(cfg_get("capcut.store_lock", str(STUDIO_HOME / "runs" / ".capcut-store.lock")))', 1),
    # messages the agent reads, reworded where they named the other toolkit's commands, manual or run files
    ('capcut_save, then: awl.py capcut-repair "', 'capcut_save, then: capcut_tools.py capcut-repair "', 1),
    ('"--draft \\"<draft>\\" --preview \\"<run>/60-outputs/video-NN/capcut-preview.mp4\\""})', '"--draft \\"<draft>\\""})', 1),
    ("`T capcut-repair", "`capcut_tools.py capcut-repair", 4),
    ("(static §7), so the project keeps it", "so the project keeps it", 1),
    ('"capcut-motion needs --run and --video (the run\'s timeline; --format for an extra format\'s) or --timeline <file>"',
     '"capcut-motion needs --timeline <file> (the images\' starts, moves and joins)"', 1),
    ('"capcut-transitions needs --run and --video (the run\'s timeline; --format for an extra format\'s) or --timeline <file>"',
     '"capcut-transitions needs --timeline <file> (the images\' starts, moves and joins)"', 1),
    ("is CapCut Pro and the run's CapCut plan is free (state.json -> capcut_plan): the export would be blocked",
     "is CapCut Pro and this PC's CapCut is free (config.json -> capcut.pro): the export would be blocked", 1),
    ("once it has fetched the effect (the plan's captions.animation)", "once it has fetched the effect", 2),
]
for pat, rep, count in SUBS:
    if count is None:
        body = re.sub(pat, rep, body)
    else:
        assert body.count(pat) == count, (pat, body.count(pat), "expected", count)
        body = body.replace(pat, rep)

MENTION = re.compile(r"awl\.py|`T |\bT capcut|\bT static|\bT draw|\bT slideshow|\bT fetch|static §|capcut-assembly|contract item|"
                     r"analyze-with-loupe|Analyze Mode|\bAWL\b|Loupe", re.I)
if REPORT:
    print(f"closure: {len(closure)} names, {sum(b[1] - b[0] + 1 for b in blocks)} lines; imports: {import_lines}")
    for i, ln in enumerate(body.split("\n"), 1):
        if MENTION.search(ln):
            print(f"{i:>5}  {ln.strip()[:200]}")
    sys.exit(0)

sha = hashlib.sha256(raw).hexdigest()[:16]
today = datetime.date.today().isoformat()
HEADER = f'''#!/usr/bin/env python3
"""capcut_tools.py - write and repair the CapCut project of a Static Studio video on this PC.

One command per call; every call prints one JSON object on its last line (exit 0 ok, 1 a step failed, 2 refused, 3 CapCut is running).
Commands: capcut-name | capcut-prep | capcut-repair | capcut-motion | capcut-transitions | capcut-font | capcut-text-anim.
How and in what order: reference/09-capcut-toolkit.md.

Provenance: these are the CapCut commands of this PC's analyze-with-loupe toolkit (scripts/awl.py, sha256 {sha}, copied {today}),
copied function by function with their helpers, the source lines unchanged. Changed on purpose, and only this:
  * AWL_HOME / AWL_FONTS_DIR are STUDIO_HOME / STUDIO_FONTS_DIR (this toolkit's own root, config.json and fonts folder);
  * the machine-wide CapCut store lock (one file for every toolkit that writes CapCut's shared project index) is read from
    config.json -> capcut.store_lock instead of the other toolkit's runs folder;
  * a few messages that named the other toolkit's commands, manual or run files were reworded (docstrings and comments keep the
    original wording);
  * the command-line glue at the end is new: the images' starts, moves and joins come from a file (--timeline), there is no run, and
    capcut-repair always keeps every text as it is (--keep-text; the other toolkit's house text style code is copied because
    capcut-repair names it, but nothing here turns it on).
Nothing else was changed; the CapCut logic is theirs.
"""
'''

GLUE = '''


# --------------------------------------------------------------------------- command line

def main():
    ap = argparse.ArgumentParser(prog="capcut_tools.py", description=__doc__.split("\\n\\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("capcut-name", help="a free CapCut project name: DD_Mon_YYYY_vNN (-2, -3 when the folder exists)")
    p.add_argument("--video", required=True, help="the video's number")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)"); p.add_argument("--store", help="CapCut drafts dir")
    p.set_defaults(fn=cmd_capcut_name)

    p = sp.add_parser("capcut-prep", help="right after capcut_clone_draft (empty:true) and before any other call on the draft: "
                                          "set the template's identity aside, set the canvas")
    p.add_argument("--draft", required=True, help="the freshly cloned draft folder")
    p.add_argument("--canvas", help="WxH: the project's canvas (default: the template's)")
    p.set_defaults(fn=cmd_capcut_prep)

    p = sp.add_parser("capcut-repair", help="after the last capcut_save: register, the media links CapCut 9.7 opens clips by, "
                                            "sync-timelines, lint (under the machine-wide store lock); every text stays as it is")
    p.add_argument("--draft", required=True)
    p.add_argument("--keep-text", action="store_true", default=True, help="always on")
    p.add_argument("--preview", help="also render capcut-cli's low-resolution proxy to this .mp4 (a proxy, never an export)")
    p.set_defaults(fn=cmd_capcut_repair)

    p = sp.add_parser("capcut-font", help="--list the fonts on this PC (CapCut's own first) | set one font file on a draft's texts "
                                          "(and list font_missing_glyphs)")
    p.add_argument("--list", action="store_true", help="list the font files (family, style, file, source)")
    p.add_argument("--family", help="list: only families containing this")
    p.add_argument("--draft", help="the CapCut draft folder"); p.add_argument("--font-file", help="the font file (from --list)")
    p.add_argument("--track", help="only the texts on the track with this name")
    p.set_defaults(fn=cmd_capcut_font)

    p = sp.add_parser("capcut-motion", help="each image's move as keyframes CapCut 9.x plays (KFTypeScaleX with uniform scale, "
                                            "KFTypePositionX/Y), after the last capcut_save")
    p.add_argument("--draft", required=True)
    p.add_argument("--timeline", required=True, help="the images file: {'fps': 30, 'images': [{'image': 1, 'start': 0.0, 'motion': 'zoom-in'}]}")
    p.set_defaults(fn=cmd_capcut_motion, run=None)

    p = sp.add_parser("capcut-transitions", help="the images file's joins as CapCut's own transitions (capcut-cli, verified catalogue)")
    p.add_argument("--draft", required=True)
    p.add_argument("--timeline", required=True, help="the images file (a row's transition and trans_s)")
    p.set_defaults(fn=cmd_capcut_transitions, run=None)

    p = sp.add_parser("capcut-text-anim", help="one CapCut text animation (capcut-cli's catalogue) on every text of a track")
    p.add_argument("--draft", required=True); p.add_argument("--track", help="a text track's name; default: every text track")
    p.add_argument("--intro", help="a slug from `capcut enums --text-intros`, e.g. pop-up"); p.add_argument("--outro")
    p.add_argument("--intro-duration", type=float, default=0.5, help="seconds, capped at each text's own length")
    p.add_argument("--outro-duration", type=float, default=0.5)
    p.set_defaults(fn=cmd_capcut_text_anim, run=None)

    a = ap.parse_args()
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
'''
PRELUDE = ("\nimport argparse\n" + "\n".join(import_lines) + "\n\nsys.dont_write_bytecode = True\ntry:\n"
           "    sys.stdout.reconfigure(encoding=\"utf-8\", errors=\"replace\")\nexcept Exception:\n    pass\n\n\n")
final = HEADER + PRELUDE + body + GLUE
OUT.write_bytes(final.encode("utf-8"))
print("written:", OUT, len(final.splitlines()), "lines; source sha256", sha)
