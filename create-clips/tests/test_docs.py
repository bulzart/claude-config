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
        for m in re.findall(r"`((?:game-clipping|game-mining|game-edit-craft|game-research-playbook|capcut-build-mcp|capcut-build|edit-craft|clip-economy|moment-mining|portfolio|research-playbook|research-agent|safety|context-keeping)\.md)`", read(d)):
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
    check((CC / "scripts" / "notify.ps1").is_file() and any((CC / "scripts" / n).is_file() for n in ("cc_notify.py", "cc_notify.py.enc")),
          "the ready alert's scripts exist (notify.ps1, cc_notify.py: plain, or locked as cc_notify.py.enc)")
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
    check(all("captions=on|off" in t and "caption_style=luckiest-guy|montserrat-highlight" in t for t in (rt, read(CC / "README.md"))) and "Captions" in sk("cc-start") and "AskUserQuestion" in sk("cc-start"),
          "the router, the README and cc-start offer the captions choice (argument or question): on or off, then the style")
    # the user's choice of 2026-11-20: two caption looks, picked at the start with no default (box = Luckiest Guy on a box, no-box = Montserrat Bold yellow with an outline)
    cs0 = sk("cc-start")
    # the user's spec of 2026-11-20 (later): "Enable captions?" On / Off, then, with captions on, the style: Luckiest Guy - Word Box (Existing) or Montserrat Bold - Word Highlight (New)
    check(all(w in cs0 for w in ("Enable captions?", "**On**", "**Off**", "Which caption style?", "**Luckiest Guy — Word Box (Existing)**", "**Montserrat Bold — Word Highlight (New)**",
                                 "caption_style=luckiest-guy", "caption_style=montserrat-highlight", "Never asked when captions are off", "no default"))
          and "Captions (Recommended)" not in cs0 and "**No-box captions**" not in cs0,
          "cc-start asks captions On/Off and, only when on, the style (Luckiest Guy word box or Montserrat Bold word highlight), no default; the no-box look is no longer offered")
    check("captions=no-box" in cs0 and "keeps that look" in cs0, "cc-start keeps an older run's look (captions on/box/no-box without caption_style) and adds nothing to its state")
    check(all("Montserrat Bold" in t and "#FFFF00" in t and "no-box" in t for t in (rt, read(CC / "README.md"), read(CC / "reference" / "edit-craft.md"), sk("cc-build-short"), sk("cc-build-long"),
                                                                                    sk("cc-build-game"), sk("cc-produce"))),
          "the router, the README, edit-craft.md, the three build skills and the produce contract describe the no-box look (Montserrat Bold, yellow #FFFF00)")
    check(all('captions.style: "no-box"' in sk(n) or "`no-box` for no-box" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game")) and all("never the other look" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game")),
          "every build skill writes the run's look as captions.style and never builds the other look")
    check(all('"word-highlight"' in sk(n) and "montserrat-highlight" in sk(n) and "#FFFF00" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game"))
          and all("word-highlight" in t or "montserrat-highlight" in t for t in (rt, read(CC / "README.md"), read(CC / "reference" / "edit-craft.md"), sk("cc-produce"), sk("cc-wrapup")))
          and "word_highlight.texts" in sk("cc-wrapup"),
          "the build skills, the router, the README, edit-craft.md, the produce contract and the wrap-up describe the Montserrat word-highlight look")
    check(all("lexicon" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game")) and "not_before" in sk("cc-profile") and "review" in sk("cc-profile") and "ONE pass" in read(CC / "reference" / "edit-craft.md"),
          "the lexicon rules (whole words, one pass, punctuation, context guards, review) are in cc-profile and edit-craft.md, and every build skill reads the lexicon record")
    # who speaks (the user, 2026-11-20): the [sub] marks of the game's subtitled lines are facts every reader is told about the same way, and they never decide
    mm, rep, ec2 = read(CC / "reference" / "moment-mining.md"), read(CC / "reference" / "reporter.md"), read(CC / "reference" / "edit-craft.md")
    check("[sub]" in mm and "not attributed" in mm and "never dropped" in mm and "voices.json" in rep and "never from the transcript" in rep,
          "moment-mining.md explains the [sub] marks (facts, an unmarked line is not attributed, a moment is never dropped for them) and the reporter quotes subtitles from voices.json")
    check("T voices" in sk("cc-start") and "T voices" in sk("cc-scan") and "[sub]" in sk("cc-plan") and "[sub]" in sk("cc-build-short") and "[sub]" in sk("cc-build-long"),
          "cc-start makes the speaker facts, cc-scan waits for them, the planner and the builders read the [sub] marks")
    check("captions.skip" in ec2 and "never the streamer's own words" in ec2 and "subtitle_y_median" in ec2 and "voices" in read(CC / "README.md") and "T voices" in rt,
          "edit-craft.md has captions.skip (never the streamer's words) and the caption placement clear of the game's subtitles; the README and the router name the voices facts")
    check(all("word_box_max_words" in sk(n) for n in ("cc-build-long", "cc-build-game", "cc-produce")) and "falls back to the plain look, in the same font, by itself" not in sk("cc-build-long"),
          "the long-form build skills keep every box-look video word-box (the user, 2026-11-18): word_box_max_words raised, no silent plain fallback")
    check("padding 0.05" in read(CC / "README.md") and "padding 0.05" in read(CC / "reference" / "edit-craft.md"), "the README and edit-craft.md give the box padding 0.05 (the user, 2026-11-20: a little smaller, then \"only a tiny bit\" smaller)")
    check(all("captions" in sk(n).lower() and ("off" in sk(n).lower()) for n in ("cc-build-short", "cc-build-long", "cc-build-game", "cc-produce", "cc-wrapup", "cc-plan", "cc-plan-game")),
          "every plan, produce, build and wrap-up skill follows the run's captions setting")
    check("captions OFF" in read(CC / "reference" / "edit-craft.md") and "captions OFF" in read(CC / "reference" / "safety.md"), "edit-craft.md and safety.md say what captions OFF means (and that a spoken slur is cut around)")

    # the user's choices of 2026-11-14: a videos question in streamer mode (long only, or long + shorts, no default), and nothing skipped, ad or not ad
    cs = sk("cc-start")
    check("`Videos`" in cs and "Long videos only" in cs and "Long videos + shorts" in cs and "no default" in cs and "only=both" in cs and "only=long" in cs,
          "cc-start asks the Videos question in the same dialog: long videos only, or long videos + shorts, the user picks (no default)")
    check("only=long|both|shorts" in rt and "only=long|both" in read(CC / "README.md") and "videos choice" in rt, "the router and the README offer the videos choice (argument or question)")
    check("only=long" in sk("cc-plan") and "only=shorts" in sk("cc-plan") and "get only" in sk("cc-plan") and "get only" in sk("cc-produce"),
          "cc-plan and cc-produce read the run's `only` (long = no short is planned or built)")
    check("game mode" in cs.lower() and "only=long" in cs and "never in game mode" in cs, "game mode records only=long and is not asked the Videos question")
    mm, pf = read(CC / "reference" / "moment-mining.md"), read(CC / "reference" / "portfolio.md")
    check("ad_batches" in mm and "verdict" in mm and "Ad-marked chunks" in mm and "ad_batches" in sk("cc-scan") and "ad-batches.json" in pf and '"kind": "ad"' in pf and "ad-batches.json" in sk("cc-plan"),
          "the mining agents judge the ad-marked batches (ad_batches with a verdict) and the planner puts the ones that are ads into avoid.json")
    check("do not skip anything" in rt.lower() and "ad-marked" in rt and "avoid.json" in rt and '"kind": "ad"' in read(CC / "README.md"),
          "the router and the README say: nothing is skipped, ad or not ad; the agents leave the ad batches out")
    check("ad-marked" in read(CC / "reference" / "game-mining.md") and "non_play" in read(CC / "reference" / "game-mining.md"), "game mining judges the ad-marked chunks too (non_play kind ad)")

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
    check("Barlow\", \"font_style" not in ec and '"font_family": "Montserrat' not in ec, "edit-craft.md shows no other font as an EDL example or a fallback (Montserrat Bold is the no-box look's own font, never an EDL key)")
    check((Path("C:/Users/Bulzart/.claude/analyze-with-loupe/fonts") / "Montserrat-Bold.otf").is_file(), "the no-box look's font file exists in the Loupe fonts folder")
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

    # the user's choice of 2026-11-14: context in the cut parts of a streamer long video: guidance only, no limits, judged from the data
    ref = read(CC / "reference" / "context-keeping.md")
    check(all("context-keeping.md" in t for t in (sk("cc-scan"), sk("cc-plan"), sk("cc-build-long"), mm, pf, rt, read(CC / "README.md"))),
          "cc-scan, cc-plan, cc-build-long, moment-mining.md, portfolio.md, the router and the README point to context-keeping.md")
    check(all(w in ref for w in ("on tape", "no text card", "gap_before_s", "needs_context", "context span", "first_rec", "another block", "text search")),
          "context-keeping.md says: only what is on tape (no text card), never across a hole in the recording, needs_context as the hint, the context span in the brief, and how the planner finds it across blocks (people first_rec, a text search of the transcripts)")
    check(re.search(r"\b\d+(?:\.\d+)?\s*(?:s|sec|secs|seconds)\b|few seconds|a handful|at most|at least", ref, re.I) is None and not any(w in ref for w in ("NAVI", "CS2", "Typical Gamer", "Pirate", "Speed")),
          "context-keeping.md sets no number of seconds or count (the agents judge from the data) and carries no example borrowed from a game match or from a run")

    # the user's choice of 2026-11-14: profanity and slurs are ALWAYS typed with one asterisk in captions (f*ck), from the user's own list file plus the EDL's mask_terms
    ml = CC / "data" / "caption-masks.json"
    check(ml.is_file(), "data/caption-masks.json (the user's list of always-masked caption words) exists")
    safety = read(CC / "reference" / "safety.md")
    check("f*ck" in safety and "caption-masks.json" in safety and "mask_terms" in safety and "always masked" in safety and "f*ck" in ec and "caption-masks.json" in ec and "f*ck" in gec,
          "safety.md, edit-craft.md and game-edit-craft.md say profanity and slurs are always typed with one asterisk (f*ck), from data/caption-masks.json plus mask_terms")
    check("f*ck" in rt and "caption-masks.json" in rt and "f*ck" in readme and "caption-masks.json" in readme and "test_masks.py" in readme, "the router and the README carry the caption mask rule")
    check(all("mask_terms" in sk(n) and "f*ck" in sk(n) for n in ("cc-build-short", "cc-build-long", "cc-build-game")) and "masked" in sk("cc-wrapup"),
          "the three build skills and the wrap-up follow the mask rule (the default list by itself, mask_terms for a word it lacks, the `masked` tally in the README)")

    # the user's choice of 2026-11-14 (STREAMER MODE ONLY): a long video is one whole watch of about 25 minutes to an hour, set by the content; borders between acts, never a story left half
    cl = read(CC / "reference" / "clip-economy.md")
    check(all("25 minutes to an hour" in t for t in (pf, cl, sk("cc-start"), sk("cc-build-long"), rt, readme)) and "36, 43 and 27" in pf and "whole watch" in pf and "whole watch" in rt,
          "portfolio.md, clip-economy.md, cc-start, cc-build-long, the router and the README say a long video is one whole watch of about 25 minutes to an hour (the 36, 43 and 27 minute example is in the planner's guide)")
    check(not any("about an hour" in t.lower() for t in (pf, cl, sk("cc-start"), sk("cc-build-long"), sk("cc-plan"), rt, readme, mm)),
          "no streamer-mode file still sets the long video at 'about an hour'")
    check("acts" in mm and "open_end" in mm and "open_start" in mm and "acts" in sk("cc-scan") and "acts.json" in pf and "acts.json" in sk("cc-plan"),
          "the mining agents record the stream's acts (open_start and open_end at a block's edge) and the planner merges them into acts.json")
    check("Check every border" in pf and "between acts" in pf and "ONE long video only" in pf and "between acts" in sk("cc-plan") and "reading the words" in sk("cc-plan"),
          "the planner sets the borders between acts, checks every border by reading the words, and keeps a stretch in one long video only")
    check("how it opens" in pf and "not clean" in sk("cc-build-long") and "not clean" in sk("cc-produce") and "not clean" in sk("cc-wrapup"),
          "the long-video builder checks how its video opens and ends, and a border that was not clean goes through the produce contract into the wrap-up README")
    check("game-clipping.md" in cl and "condensed match" in cl.lower() and "about an hour is only a ceiling" in read(CC / "reference" / "game-clipping.md").lower(),
          "the 25-minutes-to-an-hour rule is streamer mode only: the shared craft sheet points game mode to game-clipping.md, whose own length rule is unchanged")
    check(all("25 minutes" not in read(p) for p in (SKILLS / "cc-plan-game" / "SKILL.md", SKILLS / "cc-build-game" / "SKILL.md", CC / "reference" / "game-clipping.md")),
          "game mode's plan, build skill and clipping guide carry no 25-minute rule")

    # the user's choice of 2026-11-14 (STREAMER MODE): how much of a stream becomes videos is the agents' judgement and never a target (three hours, 32 minutes or none); nothing included to reach a length
    check(all(w in pf for w in ("never a target", "three hours", "32 minutes", "no minimum", "not a length to reach")),
          "portfolio.md: how much of the stream becomes videos is the agents' judgement and never a target (three hours, 32 minutes or none; no minimum, the range is not a length to reach)")
    check(all(w in sk("cc-plan") for w in ("never a target", "32 minutes", "reach a number of minutes")) and all(w in rt for w in ("three hours", "32 minutes", "reach a number of minutes")) and all(w in readme for w in ("never a target", "32 minutes")),
          "cc-plan, the router and the README carry the same: no stretch is included only to fill a video or reach a number of minutes")
    check(all(w in sk("cc-build-long") for w in ("never a number to reach", "only to lengthen it", "only to reach a length")) and all(w in cl for w in ("32-minute video", "three hours of videos", "not a target")),
          "cc-build-long and the craft sheet: the length is never a number to reach, nothing is kept only to lengthen a video, and a video can be much shorter than the plan hoped")
    check("target length" not in pf and "length target" not in pf and "brief's target" not in sk("cc-build-long") and "expected length" in pf and "expected length" in sk("cc-build-long"),
          "the planned length is an 'expected length' (an estimate from the spans), never called a target in the planner's guide or the long-video builder")
    check("not worth a video" in sk("cc-build-long") and "not worth a video:" in sk("cc-produce") and "not retried" in sk("cc-produce") and "dropped" in sk("cc-wrapup"),
          "a long video its builder judges not worth making is set failed with 'not worth a video: <why>', is not retried by cc-produce, and the wrap-up lists it as dropped with its reason")
    # the user's choice of 2026-11-14 (BOTH MODES): the spoken language is found per stream (auto, fallback, a lock per run), the task stays transcribe; the agents read it in that language
    lg = read(CC / "reference" / "language.md")
    check(all(w in lg for w in ("auto", "fallback_language", "language_locked", "never translate", "An ad chunk", "mask_terms", "Posting text", "multilingual")),
          "reference/language.md: auto detection with a fallback, a lock per run (not from or for an ad chunk), transcribe never translate, masks and posting text in the stream's language")
    check(cfg.get("whisper", {}).get("language") == "auto" and cfg.get("whisper", {}).get("fallback_language") == "en" and "language auto" in read(CC / "docs" / "processing.md"),
          "config.json: whisper.language is auto with an English fallback (it was forced to en), and docs/processing.md says so")
    check(all("language.md" in t for t in (sk("cc-start"), sk("cc-scan"), sk("cc-scan-game"), read(CC / "reference" / "safety.md"), cl, readme)) and "Spoken language:" in read(CC / "reference" / "research-agent.md"),
          "cc-start, both scan skills, safety.md, the craft sheet and the README point to language.md, and the research contract carries the spoken language")

    # the user's choice of 2026-11-14 (STREAMER SHORTS): a short is ALWAYS 9:16 (1080x1920); the check warns, the build lists a problem
    check("always 9:16" in sk("cc-build-short") and "Never a short in any shape but 9:16" in sk("cc-build-short") and "A short is always 9:16" in ec and "Always 9:16" in cl and "always 9:16" in rt and "Shorts are always 9:16" in readme,
          "shorts are always 9:16: the short builder, the edit craft, the craft sheet, the router and the README say so")
    check("not 9:16" in read(CC / "reference" / "capcut-build.md") and "edl-check` warns" in ec and "capcut-build` lists it as a problem" in ec,
          "the docs say edl-check warns and capcut-build lists a problem when a short is not 9:16")

    # the user's choice of 2026-11-14 (STREAMER SHORTS LEVEL): when shorts are made the user picks Concentrated (the one, two or three best) or Normal (about 5 to 10), asked as a follow-up; a range, never a quota
    check(all(w in cs for w in ("`Shorts`", "Concentrated", "Normal", "shorts_level", "shorts=concentrated|normal", "no default", "Never ask anything but", "shorts level")) and "follow-up" in cs.lower(),
          "cc-start asks the shorts level (Concentrated or Normal, no default) as a follow-up when shorts are made, takes `shorts=` as an argument, and stores it as shorts_level")
    check(all(w in pf for w in ("shorts_level", "`concentrated`", "`normal`", "never a quota", "Never more than three", "Never more than ten")) and all(w in sk("cc-plan") for w in ("shorts_level", "concentrated", "never a quota")),
          "portfolio.md and cc-plan read the shorts level: concentrated = the one, two or three best (never more than three), normal = about 5 to 10 (never more than ten); a range, never a quota")
    check(all(w in rt for w in ("shorts=concentrated|normal", "shorts level", "shorts_level")) and all(w in readme for w in ("shorts=concentrated|normal", "shorts_level")),
          "the router and the README offer the shorts level (argument or follow-up question) and name the saved setting")

    # the user's choice of 2026-11-14 (STREAMER SHORTS): zoom, sound effects and the words per caption are the agents' call; encouraged where there is room and it fits, never forced
    check("6 to 8 s" not in ec and "8 to 10 s" not in ec and "one per big beat at most" not in cl and "seasoning" not in cl.lower() and "seasoning" not in ec.lower(),
          "no zoom or sound-effect count or spacing is set in the craft sheet or the edit craft any more (the old 6 to 8 s, 8 to 10 s and one-per-beat limits are gone)")
    check("the agent's call" in cl and "the agent's call" in ec and "would feel off" in cl and "would feel off" in ec and "Never force a zoom or a sound effect" in sk("cc-build-short"),
          "shorts: zoom and sound effects are the agent's call, used where there is room and they fit, left out where there is none or one would feel off")
    check("about 3 words" in cl and "about 3 words" in ec and "the agent sets another count" in ec and "about 3 by default" in sk("cc-build-short"),
          "shorts: about 3 words a caption is a default; the agent sets another count in the EDL when the speech or the picture calls for it")
    check("none from a dull one" in sk("cc-start") and "hours of videos" in sk("cc-start"),
          "the Videos question tells the user the agents decide how much of the stream is worth it (hours from a great night, half an hour from a quiet one, none from a dull one)")

    # the user's choice of 2026-11-14 (GAME MODE): a recording with 2, 3 or more different matches gives separate videos, each in its own CapCut project, matches never mixed
    gcl, gmn = read(CC / "reference" / "game-clipping.md"), read(CC / "reference" / "game-mining.md")
    check("Different matches are never mixed" in gcl and "its own CapCut project" in gcl and "teams changing on the scoreboard" in gcl and "never two matches in one video or one project" in gcl.lower(),
          "game-clipping.md: different matches are never mixed, each game is its own CapCut project, and a new match is told by the teams changing on the scoreboard (a score reset alone is the next game)")
    check("match-change" in gmn and "match-change" in sk("cc-scan-game") and "a score reset alone" in gmn and "a score reset alone" in sk("cc-scan-game"),
          "the game miners record a change of match as non_play match-change, and tell it from a new map (a score reset alone)")
    check("more than one match" in sk("cc-profile-game") and "just after each reset" in sk("cc-profile-game") and "second or third match" in sk("cc-profile-game"),
          "the game profile phase finds every match of the recording (a frame just after each score reset; the teams of a second or third match go to the research agent)")
    check("own CapCut project" in sk("cc-plan-game") and "never two matches in one video or one project" in sk("cc-plan-game").lower() and "videos.L01.match" in sk("cc-plan-game") and "videos.L01.game" in sk("cc-plan-game"),
          "cc-plan-game plans the games of each match as videos of their own (each its own CapCut project) and records each video's match and game")
    check("grouped by match" in sk("cc-wrapup") and "different matches" in rt and "own CapCut project" in rt and "different matches" in readme and "match-change" in readme,
          "the wrap-up README groups game videos by match, and the router and the README carry the rule")
    check("25 minutes" not in gcl and "25 minutes" not in gmn and "acts.json" not in sk("cc-plan-game"),
          "game mode got the separate-project rule only: no 25-minute range and no streamer-mode acts file")

    # the user's choice of 2026-11-14 (WHISPER): medium for anything, strictly; no smaller model as a default, a fallback or a speed-up; the router, the README and the processing doc say so
    proc = read(CC / "docs" / "processing.md")
    check(cfg["whisper"]["model"] == "medium" and "Whisper is `medium`, always" in rt and "Whisper is `medium`, always" in readme and "there is NO fallback to a smaller one" in proc and "tests only" in proc
          and "never fall back to one and never translate a transcript" in rt,
          "Whisper is medium, always: the config, the router (rule 15 and the Never list), the README and the processing doc say so, and CC_WHISPER_MODEL is documented as tests only")
    check("transcribe, never translate" in rt and "rule 15" in rt.split("**The edit is only**")[1].split("Safety")[0] and "mask_terms" in rt.split("15. **Whisper")[1],
          "the router carries the spoken-language rule (transcribe, never translate; the masks of another language go to captions.mask_terms) and rule 6 points to it")

    # the user's choice of 2026-11-13 (TO-DO LISTS, every pipeline): RUN/todo.md kept by the main session, one to-do per production agent, read first on a resume; a record, never a gate
    core = rt.split("## Core rules")[1].split("## Never (global)")[0]
    nums = [int(n) for n in re.findall(r"^(\d+)\. \*\*", core, re.M)]
    check(nums == list(range(1, len(nums) + 1)) and len(nums) >= 16, f"the router's core rules are numbered 1 to {len(nums)} with no gap or repeat")
    todo_skills = ("cc-start", "cc-profile", "cc-profile-game", "cc-scan", "cc-scan-game", "cc-plan", "cc-plan-game", "cc-produce", "cc-build-short", "cc-build-long", "cc-build-game", "cc-wrapup")
    check("Task lists and a to-do file" in rt and "RUN/todo.md" in rt and "never a gate" in rt and "the files are right" in rt and all("todo.md" in sk(s) and "rule 16" in sk(s) for s in todo_skills),
          "the router has the to-do rule (16) and every cc-* skill names its part of it (write, tick, the agent's own to-do, the check at the close)")
    check("read `RUN/todo.md` first" in rt and "Write `RUN/todo.md`" in cs and "The to-do is checked at the close" in sk("cc-wrapup") and "its own to-do" in sk("cc-produce")
          and all("Your own to-do" in sk(s) for s in ("cc-build-short", "cc-build-long", "cc-build-game")) and "todo.md" in readme,
          "the to-do is written at the start, read first on a resume, kept by each production agent, checked at the close and described in the README")

    # the user's choice of 2026-11-15 (CHAT HEAT): the chat counted in 4 s bins against the stream's own normal; a clue that corroborates, never picks and never drops; game mode much less but considered
    ch = read(CC / "reference" / "chat-heat.md")
    mm, gm, gc = read(CC / "reference" / "moment-mining.md"), read(CC / "reference" / "game-mining.md"), read(CC / "reference" / "game-clipping.md")
    rs = read(CC / "reference" / "research-agent.md") + read(CC / "reference" / "research-playbook.md")
    check(all(w in ch for w in ("4-second bins", "this stream's own normal", "It corroborates, it never creates", "It never subtracts", "The second look", "heat_review", "one point on `shareability`",
                                "taken into account way less", "A half point at most", "--rows")),
          "chat-heat.md has the method: 4 s bins against the stream's own normal, corroborates and never creates, never subtracts, the second look, the one-point nudge, game mode much less")
    check(all(w in rt for w in ("Chat heat is a clue, never a verdict", "Game mode: much less", "never picks a moment alone and never drops one", "`T heat --run RUN`", "Never pick a moment only because the chat peaked", "one look at every chat burst"))
          and cfg["chat"]["bin_s"] == 4 and cfg["chat"]["burst_min_z"] == 4 and cfg["chat"]["burst_min_n"] == 5,
          "the router has the chat-heat rule (streamer mode, game mode much less, the Never line) and config.json -> chat has the 4 s bin and the burst settings")
    check("`T heat --run RUN`" in cs and "has_chat" in cs and "--coverage" in sk("cc-scan") and "sent back once" in sk("cc-scan") and "one look" in sk("cc-scan") and "--rows" in sk("cc-scan")
          and "no file is sent back" in sk("cc-scan-game") and "light clue" in sk("cc-scan-game") and "chat_peak" in sk("cc-plan-game") and "heat" in sk("cc-plan") and "chat heat" in sk("cc-build-short"),
          "cc-start makes the heat, cc-scan gives every burst one look and sends back what nobody looked at once, cc-scan-game keeps it light, the planners and the builders read it as a clue")
    check('"heat_review"' in mm and '"heat": null' in mm and "Every burst of your block gets one look" in mm and "never picks and never drops a moment" in mm and "--rows" in mm
          and '"heat_review"' in gm and "Chat is a light clue here" in gm and "chat_peak" in gm and "chat_peak" in gc and "half-point clue" in gc,
          "the mining guides: a heat field in a moment, a heat_review list in the block file, one look per burst; in game mode a light clue on the unit card (chat_peak)")
    check("Chat heat" in pf and "heat.md" in pf and "`T heat`" in cl and "chat's vocabulary" in rs and "heat.md" in readme and "tests/test_heat.py" in readme and "## The chat heat" in proc,
          "the planner's guide, the craft sheet, the research brief, the README and the processing doc carry the chat heat")

    # the router names both modes' skills
    r = read(ROUTER)
    for s in ("cc-start", "cc-profile", "cc-profile-game", "cc-scan", "cc-scan-game", "cc-plan", "cc-plan-game", "cc-produce", "cc-build-short", "cc-build-long", "cc-build-game", "cc-wrapup"):
        check(f"`{s}`" in r, f"the router names {s}")
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
