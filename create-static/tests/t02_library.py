"""The library's own consistency: the command, its skills and the references agree with each other and with the toolkit.
Every skill of the chain exists with a matching frontmatter; the hand-offs name skills that exist; every `T <command>` a skill or a section cites is a command of cs.py; none of the older
per-feature CapCut commands, MCP tools or names of other pipelines appear where a run reads; the docs tool's check has no error.  python tests/t02_library.py"""
import re
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
HOME = LIB.parent
SKILLS = HOME / "skills"
CHAIN = ["cs-start", "cs-prepare", "cs-study", "cs-plan", "cs-produce", "cs-sound", "cs-images", "cs-edit", "cs-record", "cs-wrapup", "cs-feedback"]
FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


def rd(p):
    return Path(p).read_text(encoding="utf-8")


cp = subprocess.run([sys.executable, "-X", "utf8", str(LIB / "scripts" / "cs.py"), "--help"], capture_output=True, text=True, encoding="utf-8")
cmds = set(re.findall(r"\{([a-z0-9,-]+)\}", cp.stdout)[0].split(","))
check("capcut-build" in cmds and "static" in cmds and "tts" in cmds, f"cs.py lists its commands ({len(cmds)})")
for gone in ("model-menu", "hf-put", "caught-flag", "loupe", "qc", "conform", "voiceover", "effort"):
    check(gone not in cmds, f"the command {gone} of other pipelines is not in cs.py")

router = rd(HOME / "commands" / "create-static.md")
check(router.startswith("---") and "disable-model-invocation: true" in router and "- Workflow" in router, "the router is a command that disallows Workflow")
for s in CHAIN:
    p = SKILLS / s / "SKILL.md"
    ok = p.is_file()
    check(ok, f"skill {s} exists")
    if not ok:
        continue
    t = rd(p)
    fm = re.match(r"^---\n(.*?)\n---", t, re.S)
    check(bool(fm) and f"name: {s}" in fm.group(1) and "user-invocable: false" in fm.group(1), f"{s}: frontmatter name and user-invocable")
    desc = re.search(r"^description:\s*(.+)$", fm.group(1), re.M).group(1) if fm else ""
    check(desc.startswith("/create-static") and len(desc) <= 230 and desc.endswith("Internal to that command."), f"{s}: a short internal description ({len(desc)} chars)")
    check("\r" not in t, f"{s}: LF line endings")

HAND = re.compile(r"next_skill=(cs-[a-z]+)|invoke Skill `(cs-[a-z]+)`|Skill `(cs-[a-z]+)`", re.I)
for s in CHAIN:
    t = rd(SKILLS / s / "SKILL.md")
    names = {m for g in HAND.findall(t) for m in g if m}
    check(all(n in CHAIN for n in names), f"{s}: its hand-offs name skills of the chain ({sorted(names)})")

# commands cited in what a run reads
LEGACY = {"capcut-prep", "capcut-motion", "capcut-transitions", "capcut-effects", "capcut-word-box", "capcut-text-anim", "capcut-labels", "capcut-repair", "capcut-text-style"}
files = [SKILLS / s / "SKILL.md" for s in CHAIN] + [HOME / "commands" / "create-static.md"] + [p for p in (LIB / "reference").rglob("*.md")]
uncited, legacy, foreign, bad_names = [], [], [], []
for p in files:
    t = rd(p)
    rel = str(p.relative_to(HOME))
    for m in re.finditer(r"\bT ([a-z][a-z0-9-]+)", t):
        c = m.group(1)
        if c in LEGACY and "090_9" not in p.name:
            legacy.append((rel, c))
        elif c not in cmds and c not in LEGACY and c not in ("capcut-check",) and not re.fullmatch(r"(is|and|the|a|in|or|to|for|at|of|from|per|as|on|one|two|text|never|measures|caught-error)", c):
            uncited.append((rel, c))
    for m in re.finditer(r"mcp__higgsfield|capcut_(?:clone_draft|add_image|add_audio|save|read_timeline|validate|add_text|add_keyframe|add_transition)|\bawl-[a-z]+|T caught-flag|T qc-consult|T prompt-template", t):
        if "capcut_add_keyframe" in m.group(0) or "capcut_add_transition" in m.group(0):
            continue                                           # named only to forbid them
        if "090_9" in p.name and m.group(0).startswith("capcut_"):
            continue                                           # the once-per-PC catalogue check is the one place the CapCut MCP is used
        foreign.append((rel, m.group(0)))
check(not legacy, f"no older per-feature CapCut command is cited where a run reads ({legacy[:4]})")
check(not uncited, f"every `T <command>` that is cited exists ({uncited[:6]})")
check(not foreign, f"no Higgsfield tool, no CapCut MCP tool, no skill or command of another pipeline is cited ({foreign[:6]})")

# the plan's S4 pieces are named once and consistently
edit = rd(SKILLS / "cs-edit" / "SKILL.md")
check("T capcut-build" in edit and "item 39" in edit, "cs-edit names the one build command and item 39")
check((LIB / "reference" / "capcut-build.md").is_file() and (LIB / "data" / "compose-template" / "draft_content.json").is_file(), "the build's recipe and the empty template exist")
contract = rd(LIB / "reference" / "production-agents" / "025_2s_spawning-static.md")
check(all(f"{n}" in contract for n in ("cs-images", "cs-edit", "cs-record")) and "<CS>" in contract and "<memes>" not in contract and "<model id>" not in contract,
      "the production agent's contract names cs-images, cs-edit, cs-record and only placeholders the toolkit fills")

dt = subprocess.run([sys.executable, "-X", "utf8", str(LIB / "scripts" / "docs_tool.py"), "check"], capture_output=True, text=True, encoding="utf-8")
check(dt.returncode == 0 and " 0 errors" in dt.stdout, "docs_tool check has no errors: " + (dt.stdout.strip().splitlines() or [""])[-1])

print(f"\n{N[0] - len(FAILS)}/{N[0]} checks passed")
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + "; ".join(FAILS[:8]))
sys.exit(1 if FAILS else 0)
