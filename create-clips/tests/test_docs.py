"""Consistency test of the /create-clips documents: every file, skill, command and config key the docs name exists.

    python tests/test_docs.py

The command is a router + phase skills + references; a rename or a deleted file would leave an agent reading a path that is not there.
This test reads no media and starts no process but the argument parser. It checks:
  - every cc-* skill folder has a SKILL.md whose `name:` is the folder name and which is not user-invocable;
  - every `Skill cc-...` the router and the skills name exists;
  - every `CC/reference/...` path named in the router, the skills, the references and the README exists (paths with a <placeholder> are checked for their folder);
  - every `T <command>` named in backticks is a registered cc.py command;
  - every `config.json -> a.b` key exists in config.json;
  - every phase's `next_skill=` names an existing skill.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent
CLAUDE = CC.parent
SKILLS = CLAUDE / "skills"
ROUTER = CLAUDE / "commands" / "create-clips.md"
sys.path.insert(0, str(CC / "scripts"))


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main():
    skill_dirs = sorted(p for p in SKILLS.glob("cc-*") if p.is_dir())
    names = {p.name for p in skill_dirs}
    check(len(skill_dirs) >= 12, f"{len(skill_dirs)} cc-* skills found")
    for d in skill_dirs:
        f = d / "SKILL.md"
        if not f.is_file():
            check(False, f"{d.name}: SKILL.md missing")
            continue
        head = read(f).split("---")[1] if read(f).startswith("---") else ""
        nm = re.search(r"^name:\s*(\S+)", head, re.M)
        check(bool(nm) and nm.group(1) == d.name and "user-invocable: false" in head and re.search(r"^description:\s*\S", head, re.M),
              f"{d.name}: frontmatter has its name, a description and user-invocable: false")

    docs = [ROUTER, CC / "README.md", *sorted(SKILLS.glob("cc-*/SKILL.md")), *sorted((CC / "reference").rglob("*.md")), *sorted((CC / "docs").glob("*.md"))]
    docs = [d for d in docs if d.is_file()]
    check(ROUTER.is_file(), "the router command file exists")

    # skills named
    missing = []
    for d in docs:
        for s in re.findall(r"Skill `(cc-[a-z-]+)`", read(d)) + re.findall(r"next_skill=(cc-[a-z-]+)", read(d)) + re.findall(r"`(cc-[a-z-]+)`", read(d)):
            if s not in names:
                missing.append((d.name, s))
    check(not missing, "every skill the docs name exists " + str(sorted(set(missing))[:6]))

    # reference paths named
    miss_ref = []
    for d in docs:
        for m in re.findall(r"CC/reference/([A-Za-z0-9_<>./-]+\.md)", read(d)):
            rel = m.rstrip(".")
            if "<" in rel:
                folder = CC / "reference" / rel.split("<")[0].rstrip("/")
                ok = folder.is_dir()
            else:
                ok = (CC / "reference" / rel).is_file()
            if not ok:
                miss_ref.append((d.name, rel))
    check(not miss_ref, "every CC/reference/... path the docs name exists " + str(sorted(set(miss_ref))[:6]))
    miss_bare = []
    for d in docs:
        for m in re.findall(r"`((?:game-clipping|game-mining|game-edit-craft|game-research-playbook|capcut-build-mcp|capcut-build|edit-craft|clip-economy|moment-mining|portfolio|research-playbook|safety)\.md)`", read(d)):
            if not (CC / "reference" / m).is_file():
                miss_bare.append((d.name, m))
    check(not miss_bare, "every reference named by its file name exists " + str(sorted(set(miss_bare))[:6]))

    # cc.py commands named
    import importlib
    import cc as ccmod
    parser = ccmod.build_parser()
    sub = next(a for a in parser._actions if getattr(a, "choices", None))
    cmds = set(sub.choices)
    check({"report", "hud-read", "hud-scan", "region-series", "hud-states", "hud-slice", "units-merge", "units-verdict", "units-check", "units-table", "capcut-compose", "capcut-finish", "edl-check", "captions"} <= cmds,
          "the game and compose commands are registered in cc.py (" + str(len(cmds)) + " commands)")
    bad_cmd = []
    for d in docs:
        for c in re.findall(r"`T ([a-z][a-z-]+)(?=[ `])", read(d)):
            if c not in cmds:
                bad_cmd.append((d.name, c))
    check(not bad_cmd, "every `T <command>` the docs name is a cc.py command " + str(sorted(set(bad_cmd))[:6]))

    # config keys
    cfg = json.loads(read(CC / "config.json"))
    bad_key = []
    for d in docs:
        for k in re.findall(r"config\.json -> ((?:[a-z_]+\.)*[a-z_]+)", read(d)):
            cur = cfg
            for part in k.split("."):
                cur = cur.get(part) if isinstance(cur, dict) else None
            if cur is None:
                bad_key.append((d.name, k))
    check(not bad_key, "every config.json key the docs name exists " + str(sorted(set(bad_key))[:6]))
    rc = cfg.get("report") or {}
    check(rc.get("model") == "claude-haiku-5-5" and rc.get("effort") in ("high", "xhigh", "max") and rc.get("enabled") is True, "the chunk reporter is Haiku 5.5 at high effort or above (never low or medium) in config.json")
    check("scan_model" not in cfg["agents"] and cfg["agents"].get("scan_chunks_game") and cfg["agents"].get("scan_chunks_streamer"), "no agent has a model of its own any more (the analysis batch sizes remain)")
    check((CC / "reference" / "reporter.md").is_file() and "decide nothing" in read(CC / "reference" / "reporter.md").lower().replace("**", ""), "the reporter's brief exists and says it decides nothing")
    gm = [read(p).lower() for p in (SKILLS / "cc-build-game" / "SKILL.md", SKILLS / "cc-plan-game" / "SKILL.md", CC / "reference" / "game-edit-craft.md")]
    check(all("never a short" in t or "no shorts" in t for t in gm) and all("sound effect" in t for t in gm), "game mode's plan, build skill and edit craft all say: no shorts and no sound effects")
    check("askuserquestion" in read(ROUTER).lower() and "askuserquestion" in read(SKILLS / "cc-start" / "SKILL.md").lower(), "the router allows AskUserQuestion and cc-start asks the mode")

    # the empty compose template
    tm = CC / "data" / "compose-template"
    check((tm / "draft_content.json").is_file() and (tm / "draft_meta_info.json").is_file(), "data/compose-template holds the empty CapCut 9.7 draft that capcut-compose starts from")
    try:
        c = json.loads(read(tm / "draft_content.json"))
        check(not any(t.get("segments") for t in c.get("tracks", [])), "the compose template has no clips of its own")
    except ValueError:
        check(False, "the compose template's draft_content.json is valid JSON")

    # the router names both modes' skills
    r = read(ROUTER)
    for s in ("cc-start", "cc-profile", "cc-profile-game", "cc-scan", "cc-scan-game", "cc-plan", "cc-plan-game", "cc-produce", "cc-build-short", "cc-build-long", "cc-build-game", "cc-wrapup"):
        check(f"`{s}`" in r, f"the router names {s}")
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
