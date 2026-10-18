"""Structure checks of the library: router, phase skills, section files and the toolkit agree with each other (no model call, no run needed)."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t11_common import ATG, LIB, PY, check, finish  # noqa: E402

HOME = LIB.parent.parent if (LIB.parent / "skills").is_dir() is False else LIB.parent
ROUTER = HOME / "commands" / "analyze-then-generate.md"
SKILLS = sorted((HOME / "skills").glob("atg-*/SKILL.md"))


def rd(p):
    return Path(p).read_bytes().decode("utf-8")


router = rd(ROUTER)
names = [p.parent.name for p in SKILLS]

# --- the section tool's own check: indexes against files, skills, paths, citations
cp = subprocess.run([PY, "-X", "utf8", str(LIB / "scripts" / "docs_tool.py"), "check"], capture_output=True, text=True, encoding="utf-8")
check(cp.returncode == 0 and " 0 errors" in cp.stdout, "docs_tool check reports 0 errors: " + cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "docs_tool check printed nothing")

# --- the router and the skills
check(len(names) == 25, f"25 phase skills exist ({len(names)})")
check(all(f"`{n}`" in router for n in names), "the router names every phase skill: " + ", ".join(n for n in names if f"`{n}`" not in router))
check(all(b"\r" not in p.read_bytes() for p in SKILLS) and b"\r" not in ROUTER.read_bytes(), "the router and the skills use LF line endings (a CRLF frontmatter is not parsed)")
check(all(rd(p).startswith("---\nname: " + p.parent.name + "\ndescription: ") and "\nuser-invocable: false\n---\n" in rd(p)[:600] for p in SKILLS), "every skill has name, description and user-invocable: false in its frontmatter")
handoffs = set()
for p in SKILLS:
    handoffs |= set(re.findall(r"next_skill=(atg-[a-z-]+)", rd(p)))
check(handoffs <= set(names), "every next_skill a hand-off records is an existing skill: " + ", ".join(sorted(handoffs - set(names))))
check(all(any(n in rd(q) for q in SKILLS if q.parent.name != n) or n in router for n in names), "every skill is reached from the router or from another skill")

# --- the toolkit commands the text uses exist
h = subprocess.run([PY, "-X", "utf8", ATG, "-h"], capture_output=True, text=True, encoding="utf-8").stdout
cmds = set(re.search(r"\{([^}]+)\}", h).group(1).split(","))
used = set()
for p in [ROUTER] + SKILLS:
    used |= set(re.findall(r"`T ([a-z][a-z-]+)(?= |`)", rd(p)))
missing = sorted(c for c in used if c not in cmds and c != "caught-error")
check(not missing, "every `T <command>` in the router and the skills is a command of atg.py: " + ", ".join(missing))

# --- what must not come back
text = router + "\n".join(rd(p) for p in SKILLS) + rd(LIB / "README.md")
check("update-from-errors" not in text, "no mention of the obsolete update-from-errors command in the router, skills and README")
check("analyze-then-pick" not in text, "the router, skills and README do not mention the other pipeline")
check("T caught-error" not in re.sub(r"no `T caught-error`", "", text) and "caught_errors.md" not in re.sub(r"There is no `caught_errors.md`", "", re.sub(r"`caught_errors.md` and", "", text)), "the retired error ledger is not used by any step")
check(not (LIB / "caught_errors.md").exists(), "caught_errors.md is gone")

finish()
