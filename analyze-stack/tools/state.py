"""state.py - read / write <run>\\state.json from the command line.

Usage:
  python state.py <run-dir> get                 -> prints the whole state as JSON
  python state.py <run-dir> get stage           -> prints one key (JSON-encoded unless a plain string)
  python state.py <run-dir> set stage=analysis next_step=questions mode=1
        values are parsed as JSON when possible ("1" -> 1, "true" -> true, '{"a":1}' -> object), else strings;
        dotted keys write nested values: answers.Q1="Keep the video as it is"
  python state.py <run-dir> add-file <stage> <path> [<path> ...]
Always stamps "updated". Exit 0 ok, 1 error, 2 bad usage.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        return raw


def set_nested(d: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    cur = d
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    run_dir = Path(argv[0]).resolve()
    if not run_dir.exists():
        print(f"run dir not found: {run_dir}", file=sys.stderr)
        return 1
    cmd = argv[1]
    if cmd == "get":
        st = common.state_get(run_dir)
        if len(argv) >= 3:
            cur = st
            for p in argv[2].split("."):
                cur = cur.get(p) if isinstance(cur, dict) else None
            print(cur if isinstance(cur, str) else json.dumps(cur, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0
    if cmd == "set":
        st = common.state_get(run_dir)
        for kv in argv[2:]:
            if "=" not in kv:
                print(f"bad assignment: {kv}", file=sys.stderr)
                return 2
            k, v = kv.split("=", 1)
            set_nested(st, k.strip(), parse_value(v))
        st["run_id"] = run_dir.name
        st["updated"] = common.now_iso()
        common.write_json(common.state_path(run_dir), st)
        print(json.dumps({k: st.get(k) for k in ("run_id", "stage", "next_step", "updated")}, ensure_ascii=False))
        return 0
    if cmd == "add-file":
        if len(argv) < 4:
            print("usage: state.py <run-dir> add-file <stage> <path> [...]", file=sys.stderr)
            return 2
        st = common.state_add_files(run_dir, argv[2], argv[3:])
        print(json.dumps(st["files"].get(argv[2], []), ensure_ascii=False))
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
