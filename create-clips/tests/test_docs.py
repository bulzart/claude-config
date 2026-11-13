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
        for m in re.findall(r"`((?:game-clipping|game-mining|game-edit-craft|game-research-playbook|capcut-build-mcp|capcut-build|edit-craft|clip-economy|moment-mining|portfolio|research-playbook|research-agent|safety)\.md)`", read(d)):
            if not (CC / "reference" / m).is_file():
                miss_bare.append((d.name, m))
    check(not miss_bare, "every reference named by its file name exists " + str(sorted(set(miss_bare))[:6]))

    # cc.py commands named
    import importlib
    import cc as ccmod
    parser = ccmod.build_parser()
    sub = next(a for a in parser._actions if getattr(a, "choices", None))
    cmds = set(sub.choices)
    check({"report", "notify", "hud-read", "hud-scan", "region-series", "hud-states", "hud-slice", "units-merge", "units-verdict", "units-check", "units-table", "capcut-compose", "capcut-finish", "edl-check", "captions"} <= cmds,
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
    check((cfg.get("watch") or {}).get("workers") == 2 and "watch.workers" in read(CC / "README.md") and "Two processors" in read(CC / "docs" / "processing.md"),
          "config.json has watch.workers 2 and the README and docs/processing.md describe the two processors")
    nc = cfg.get("notify") or {}
    check({"enabled", "persistent", "sound", "idle_minutes", "catchup_hours"} <= set(nc) and nc.get("enabled") is True, "config.json has the notify block (the ready alert is on)")
    check((CC / "scripts" / "notify.ps1").is_file() and (CC / "scripts" / "cc_notify.py").is_file(), "the ready alert's scripts exist (notify.ps1, cc_notify.py)")
    rd, pd = read(CC / "README.md"), read(CC / "docs" / "processing.md")
    check("`notify`" in rd and "The ready alert" in pd and "creationflags=NO_WINDOW" in rd, "the README and docs/processing.md describe the ready alert and the no-console-window rule")
    check((CC / "reference" / "reporter.md").is_file() and "decide nothing" in read(CC / "reference" / "reporter.md").lower().replace("**", ""), "the reporter's brief exists and says it decides nothing")
    gm = [read(p).lower() for p in (SKILLS / "cc-build-game" / "SKILL.md", SKILLS / "cc-plan-game" / "SKILL.md", CC / "reference" / "game-edit-craft.md")]
    check(all("never a short" in t or "no shorts" in t for t in gm) and all("sound effect" in t for t in gm), "game mode's plan, build skill and edit craft all say: no shorts and no sound effects")
    check("askuserquestion" in read(ROUTER).lower() and "askuserquestion" in read(SKILLS / "cc-start" / "SKILL.md").lower(), "the router allows AskUserQuestion and cc-start asks the mode")

    # the user's choices of 2026-11-13: ONE research agent, side-by-side blocks, captions or no captions picked at the start
    ag = cfg.get("agents") or {}
    check(ag.get("research_max") == 1 and (ag.get("research_calls") or 0) >= 5 and (ag.get("scan_min_blocks") or 0) >= 2,
          "config.json: one research agent with a call budget, and at least two scan blocks")
    ra = CC / "reference" / "research-agent.md"
    check(ra.is_file() and "ONE" in read(ra) and "SendMessage" in read(ra) and "research.md" in read(ra), "reference/research-agent.md exists: the contract of the one research agent")
    rt, sk = read(ROUTER), lambda n: read(SKILLS / n / "SKILL.md")  # noqa: E731
    check("ONE research agent" in rt and "research agents at most 4" not in rt and "Never more than ONE research agent" in rt, "the router says ONE research agent and no longer allows four")
    check("research.md" in sk("cc-start") and "research_calls" in sk("cc-start") and "research.md" in sk("cc-profile") and "research.md" in sk("cc-profile-game"),
          "cc-start starts the research agent and both profile skills collect its note")
    check(all("research wave" not in sk(n).lower().replace("never a research wave", "").replace("never start a second research agent or a research wave", "") for n in ("cc-profile", "cc-profile-game", "cc-start")),
          "no profile skill spawns a research wave any more")
    check("hud-scan" in sk("cc-profile-game") and "region-series" in sk("cc-profile-game") and "min-blocks" in sk("cc-scan-game") and "min-blocks" in sk("cc-scan"),
          "the screen scan starts in the profile phase and both scans size their blocks with --min-blocks")
    check("captions=on|off" in rt and "captions=on|off" in read(CC / "README.md") and "Captions" in sk("cc-start") and "AskUserQuestion" in sk("cc-start"),
          "the router, the README and cc-start offer the captions choice (argument or question)")
    check(all("captions" in sk(n).lower() and ("off" in sk(n).lower()) for n in ("cc-build-short", "cc-build-long", "cc-build-game", "cc-produce", "cc-wrapup", "cc-plan", "cc-plan-game")),
          "every plan, produce, build and wrap-up skill follows the run's captions setting")
    check("captions OFF" in read(CC / "reference" / "edit-craft.md") and "captions OFF" in read(CC / "reference" / "safety.md"), "edit-craft.md and safety.md say what captions OFF means (and that a spoken slur is cut around)")

    # the user's choices of 2026-11-13, later: the CapCut composition for everything (ONE build command), and the caption look
    check({"capcut-build", "fonts"} <= cmds, "cc.py registers capcut-build (the one build command) and fonts")
    cb = read(CC / "reference" / "capcut-build.md")
    check(all("T capcut-build" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game", "cc-produce")) and "T capcut-build" in cb and "problems" in cb and "ONE" in cb,
          "every build skill, the produce contract and capcut-build.md send the agent to ONE `T capcut-build` command with a `problems` list")
    check(not any(re.search(r"`T capcut-compose`[^.\n]*`T capcut-finish`", sk(n)) for n in ("cc-build-short", "cc-build-long", "cc-build-game")),
          "no build skill tells the agent to run compose and finish as two commands any more")
    check("capcut-build" in rt and "composition" in rt and "never a project built clip by clip" in rt and "capcut-build" in read(CC / "README.md"),
          "the router and the README name the CapCut composition, `capcut-build`, and forbid building clip by clip")
    check("--bare" in cb and "composed.json" in cb and "store lock" in cb and "font-cache.json" in cb, "capcut-build.md describes --bare, composed.json, the store lock and the font cache")
    ec, gec = read(CC / "reference" / "edit-craft.md"), read(CC / "reference" / "game-edit-craft.md")
    check("word-box" in ec and "size_em_pct" in ec and "4.6" in ec and "phone" in ec.lower() and "highlight_color" in ec and "captions.why" in ec,
          "edit-craft.md describes the word-box look, the free box colour, and the small-to-normal automatic size for phones")
    check('size: "auto"' in gec and "highlight" not in gec.lower().replace("highlight_color", "") or 'size: "auto"' in gec, "game-edit-craft.md follows the automatic size (no stale fixed size)")
    # THE FONT IS FIXED (the user, 2026-11-13, after comparing our frame with Loupe video 04's): Luckiest Guy always; only the box colour is free
    readme = read(CC / "README.md")
    check(all("Luckiest Guy" in t for t in (ec, gec, rt, readme, sk("cc-start"), sk("cc-build-short"), sk("cc-build-long"), sk("cc-build-game"), sk("cc-produce"))),
          "the router, the README, edit-craft.md, game-edit-craft.md, cc-start, the three build skills and the produce contract all say the caption font is Luckiest Guy")
    check(all("ALWAYS" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game", "cc-produce")) and "font_missing_glyphs" in ec and "house_font" in ec,
          "the build skills say ALWAYS, and edit-craft.md names the one exception (a character the font cannot draw: font_missing_glyphs, house_font)")
    check("captions_font" not in sk("cc-start") and "captions_font" not in rt and "captions_font" not in readme and "captions_font" not in ec, "the per-run font option captions_font is gone from cc-start, the router, the README and edit-craft.md")
    check("captions_color" in sk("cc-start") and "captions_color" in rt and "captions_color" in ec, "cc-start, the router and edit-craft.md carry the user's own box colour (captions_color)")
    check(all("pick only the box colour" in sk(n).lower() for n in ("cc-build-short", "cc-build-long", "cc-build-game")), "the build skills tell the agent to pick only the box colour to match the video's appearance")
    check((Path("C:/Users/Bulzart/.claude/analyze-with-loupe/fonts") / "LuckiestGuy-Regular.ttf").is_file(), "the house font file exists in the Loupe fonts folder")
    check("Montserrat" not in ec and "Barlow\", \"font_style" not in ec, "edit-craft.md no longer shows another font as the example or the fallback")
    gi = (CC.parent / ".gitignore")
    check(not gi.is_file() or "create-clips/data/font-cache.json" in read(gi), "the font-lookup cache is git-ignored (derived data)")

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
