"""Structure checks of the library: router, phase skills, section files and the toolkit agree with each other (no model call, no run needed)."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t11_common import ATG, LIB, PY, check, finish  # noqa: E402

HOME = LIB.parent                                                  # ~/.claude: commands/, skills/ and the library sit side by side
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
    used |= set(re.findall(r"(?<!no )`T ([a-z][a-z-]+)(?= |`)", rd(p)))     # "no `T caught-error`" states a retirement, it is not a use
missing = sorted(c for c in used if c not in cmds)
check(not missing, "every `T <command>` in the router and the skills is a command of atg.py: " + ", ".join(missing))

# --- the QC-fixes option (command item 27) is written wherever it acts, with the same words for the choice and the blocker
PA = LIB / "reference" / "production-agents"
SKD = HOME / "skills"
wired = [("router", ROUTER, "`ask`"), ("atg-start", SKD / "atg-start" / "SKILL.md", "qc_fixes"), ("atg-qc", SKD / "atg-qc" / "SKILL.md", "qc_fix_permission"),
         ("atg-submit", SKD / "atg-submit" / "SKILL.md", "QC fixes `ask`"), ("atg-analyze-produce", SKD / "atg-analyze-produce" / "SKILL.md", "qc_fix_permission"),
         ("production-agents §1", PA / "010_1_prepared-by-this-session-before.md", "qc_fixes"), ("production-agents §2", PA / "020_2_spawning.md", "qc_fix_permission"),
         ("production-agents §3", PA / "030_3_the-agent-s-contract.md", "qc_fix_permission"), ("production-agents §4", PA / "040_4_60-outputs-video-nn-result-json.md", "fix_proposal"),
         ("production-agents §5", PA / "050_5_this-session-as-agents-report.md", "qc_fix_permission")]
check(not [lbl for lbl, p, needle in wired if needle not in rd(p)], "the QC-fixes option is written in every place that acts on it: " + ", ".join(lbl for lbl, p, needle in wired if needle not in rd(p)))
check(all(w in router for w in ("27. **QC fixes**", "qc-fixes ask|auto")), "the router has contract item 27 and the qc-fixes argument")

# --- the ledger is described the same way everywhere: it records and reports, it never refuses
stale = [p.name for p in list((LIB / "higgsfield").rglob("*.md")) + list((LIB / "models").rglob("*.md")) + list((LIB / "reference").rglob("*.md")) + SKILLS
         if re.search(r"ledger (caps|enforces)|Exit 3 means|conform` refuses|refuses to crop", rd(p))]
check(not stale, "no guide, reference or skill says the ledger caps/enforces or that conform refuses: " + ", ".join(stale))

# --- Loupe is started and recorded at run creation, and the same key reaches resume, the agent contract and QC
lw = [("router", ROUTER, "T loupe ensure"), ("atg-start", SKD / "atg-start" / "SKILL.md", "T loupe ensure"), ("atg-analyze-produce", SKD / "atg-analyze-produce" / "SKILL.md", "T loupe ensure"),
      ("atg-qc", SKD / "atg-qc" / "SKILL.md", "T loupe ensure"), ("production-agents §1", PA / "010_1_prepared-by-this-session-before.md", "`loupe`"),
      ("production-agents §2", PA / "020_2_spawning.md", "Loupe: <up|down>")]
check(not [lbl for lbl, p, needle in lw if needle not in rd(p)], "the Loupe start step is written in every place that acts on it: " + ", ".join(lbl for lbl, p, needle in lw if needle not in rd(p)))
check("loupe=up" in rd(SKD / "atg-start" / "SKILL.md") and "loupe" in cmds, "atg-start records state.json loupe and the toolkit has the loupe command")

# --- Loupe is started and recorded at run creation, and the same key reaches resume, the agent contract and QC
lw = [("router", ROUTER, "T loupe ensure"), ("atg-start", SKD / "atg-start" / "SKILL.md", "T loupe ensure"), ("atg-analyze-produce", SKD / "atg-analyze-produce" / "SKILL.md", "T loupe ensure"),
      ("atg-qc", SKD / "atg-qc" / "SKILL.md", "T loupe ensure"), ("production-agents 1", PA / "010_1_prepared-by-this-session-before.md", "`loupe`"),
      ("production-agents 2", PA / "020_2_spawning.md", "Loupe: <up|down>")]
check(not [lbl for lbl, p, needle in lw if needle not in rd(p)], "the Loupe start step is written in every place that acts on it: " + ", ".join(lbl for lbl, p, needle in lw if needle not in rd(p)))
check("loupe=up" in rd(SKD / "atg-start" / "SKILL.md") and "loupe" in cmds, "atg-start records state.json loupe and the toolkit has the loupe command")

# --- what must not come back
text = router + "\n".join(rd(p) for p in SKILLS) + rd(LIB / "README.md")
check("update-from-errors" not in text, "no mention of the obsolete update-from-errors command in the router, skills and README")
OTHER = "analyze-then-" + "pick"      # built in two pieces so that a search for the name finds only real mentions
check(OTHER not in text, "the router, skills and README do not mention the other pipeline")
uses = [ln.strip() for ln in text.splitlines() if re.search(r"caught_errors|caught-error", ln) and not re.search(r"There is no|no `|retired|git history", ln)]
check(not uses and "caught-error" not in cmds, "the retired error ledger is not used by any step (only 'there is no ...' statements mention it): " + " | ".join(uses[:3]))
check(not (LIB / "caught_errors.md").exists(), "caught_errors.md is gone")

finish()
