"""Prove the copy is the original: for every module-level definition of the copy (except the glue main), compare its source with the
same-named definition in awl.py, line by line. Usage: python -I verify_extraction.py <awl.py> <capcut_tools.py>"""
import ast
import difflib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def segments(path):
    text = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")
    lines = text.split("\n")
    out = {}
    for node in ast.parse(text).body:
        names = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names = [node.name]
        elif isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        for n in names:
            start = node.lineno
            if getattr(node, "decorator_list", None):
                start = min(d.lineno for d in node.decorator_list)
            out.setdefault(n, []).append("\n".join(lines[start - 1:node.end_lineno]))
    return out


orig, copy = segments(sys.argv[1]), segments(sys.argv[2])
same = changed = 0
changed_rows = []
for name, segs in copy.items():
    if name == "main":
        continue
    o = orig.get(name)
    if o is None:
        print("NOT IN THE ORIGINAL:", name)
        continue
    if segs == o:
        same += 1
        continue
    changed += 1
    for a, b in zip(o, segs):
        for line in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=0):
            if line.startswith(("---", "+++", "@@")):
                continue
            changed_rows.append((name, line[:230]))
print(f"definitions identical to the original: {same}; with deliberate changes: {changed}")
cur = None
for name, line in changed_rows:
    if name != cur:
        print(f"\n[{name}]")
        cur = name
    print("   ", line)
