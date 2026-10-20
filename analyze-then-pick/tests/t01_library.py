"""Structure checks of the library: the router, the phase skills, the section files and the toolkit agree with each other (no model call,
no run needed). The forbidden names (the retired ledger, the obsolete learning command, the other pipeline) are built in pieces so that
this file itself does not carry them."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import ATP, HOME, LIB, PY, check, finish  # noqa: E402

ROUTER = HOME / "commands" / "analyze-then-pick.md"
SKILLS = sorted((HOME / "skills").glob("atp-*/SKILL.md"))
SKD = HOME / "skills"
PA = LIB / "reference" / "production-agents"


def rd(p):
    return Path(p).read_bytes().decode("utf-8")


router = rd(ROUTER)
names = [p.parent.name for p in SKILLS]

# --- the section tool's own check: indexes against files, skills, paths, citations
cp = subprocess.run([PY, "-X", "utf8", str(LIB / "scripts" / "docs_tool.py"), "check"], capture_output=True, text=True, encoding="utf-8")
check(cp.returncode == 0 and " 0 errors" in cp.stdout, "docs_tool check reports 0 errors: " + (cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "nothing printed"))

# --- the router and the skills
check(len(names) == 19, f"19 phase skills exist ({len(names)})")
check(all(f"`{n}`" in router for n in names), "the router names every phase skill: " + ", ".join(n for n in names if f"`{n}`" not in router))
check(all(b"\r" not in p.read_bytes() for p in SKILLS) and b"\r" not in ROUTER.read_bytes(), "the router and the skills use LF line endings (a CRLF frontmatter is not parsed)")
check(all(rd(p).startswith("---\nname: " + p.parent.name + "\ndescription: ") and "\nuser-invocable: false\n---\n" in rd(p)[:600] for p in SKILLS),
      "every skill has name, description and user-invocable: false in its frontmatter")
handoffs = set()
for p in SKILLS:
    handoffs |= set(re.findall(r"next_skill=(atp-[a-z-]+)", rd(p)))
check(handoffs <= set(names), "every next_skill a hand-off records is an existing skill: " + ", ".join(sorted(handoffs - set(names))))
check(all(any(n in rd(q) for q in SKILLS if q.parent.name != n) or n in router for n in names), "every skill is reached from the router or from another skill")
check(all("## Read now" in rd(p) for p in SKILLS), "every skill has a Read now list")
# every section file a Read now list names exists
bad_paths = []
for p in SKILLS:
    for m in re.finditer(r"`ATP/([^`\s]+)`", rd(p)):
        ref = m.group(1).rstrip(".,;:)")
        if any(c in ref for c in "*<>{}"):
            continue
        if not (LIB / ref).exists():
            bad_paths.append(f"{p.parent.name}: {ref}")
check(not bad_paths, "every ATP/ path a skill names exists: " + "; ".join(bad_paths[:5]))

# --- README, reference and pipeline files are LF
lf_bad = [str(p.relative_to(LIB)) for p in [LIB / "README.md", LIB / "learning-log.md"] + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "pipeline").glob("*.md"))
          if b"\r" in p.read_bytes()]
check(not lf_bad, "README, learning log, references and pipeline docs are LF: " + ", ".join(lf_bad[:5]))

# --- the toolkit commands the text uses exist
h = subprocess.run([PY, "-X", "utf8", ATP, "-h"], capture_output=True, text=True, encoding="utf-8").stdout
cmds = set(re.search(r"\{([^}]+)\}", h).group(1).split(","))
used = set()
for p in [ROUTER] + SKILLS + sorted((LIB / "reference").rglob("*.md")):
    used |= set(re.findall(r"(?<!no )`T ([a-z][a-z-]+)(?= |`)", rd(p)))     # "no `T caught-error`" states a retirement, it is not a use
missing = sorted(c for c in used if c not in cmds)
check(not missing, "every `T <command>` in the router, the skills and the references is a command of atp.py: " + ", ".join(missing))
for c in ("loupe", "qc-consult", "qc-brief", "plan-hints", "caught-flag", "status", "doctor", "lint-run", "cost-report", "seams", "strip-inserts", "doc-text"):
    check(c in cmds, f"atp.py has the {c} command")

# --- Loupe is started and recorded at run creation, and the same key reaches resume, the agent contract and QC
lw = [("router resume", ROUTER, "T loupe ensure"), ("atp-start", SKD / "atp-start" / "SKILL.md", "T loupe ensure"),
      ("atp-start state", SKD / "atp-start" / "SKILL.md", "loupe=up"),
      ("atp-analyze-produce", SKD / "atp-analyze-produce" / "SKILL.md", "T loupe ensure"), ("atp-qc", SKD / "atp-qc" / "SKILL.md", "T loupe ensure"),
      ("production-agents §1", PA / "010_1_prepared-by-this-session-before.md", "`loupe`"), ("production-agents §2", PA / "020_2_spawning.md", "Loupe: <up|down>")]
check(not [lbl for lbl, p, needle in lw if needle not in rd(p)], "the Loupe start step is written in every place that acts on it: " + ", ".join(lbl for lbl, p, needle in lw if needle not in rd(p)))
qc = rd(SKD / "atp-qc" / "SKILL.md")
check("needs_unmet" in qc and "--note" in qc, "the QC phase handles the keeper asking (needs_unmet, qc-consult --note)")
check("once per video" in qc, "the QC phase asks the keeper once per video")
check("T qc-consult" in qc and "composite_path" in qc and "qc-consult.json" in qc, "the QC phase consults the keeper, views every composite and names the saved answer")
check("T plan-hints" in rd(SKD / "atp-write-request" / "SKILL.md"), "the first request asks for sample hints (plan-hints)")
sub = rd(SKD / "atp-submit" / "SKILL.md")
check("T caught-flag add" in sub and "--flagged" in sub, "a flag is recorded in X7 before the request changes")
check("T caught-flag reconcile" in rd(SKD / "atp-wrapup" / "SKILL.md") and "T caught-flag reconcile" in rd(SKD / "atp-analyze-produce" / "SKILL.md"), "the flags are reconciled as agents report and in the wrap-up")
check("T strip-inserts" in rd(SKD / "atp-recreate-plan" / "SKILL.md") and "seams" in rd(SKD / "atp-recreate-plan" / "SKILL.md"), "the Recreate plan strips the inserts and reads the seam profile")

# --- the audio question (contract item 24): asked once at the start, stored, honoured by prep-all, told to the agents
st = rd(SKD / "atp-start" / "SKILL.md")
check("audio_ingest" in st and "Audio ingest" in st, "atp-start asks the audio question and stores state.json -> audio_ingest")
check("24. **Audio" in router and "audio_ingest" in router, "the router has contract item 24 (audio ingest)")
check("audio_ingest" in rd(SKD / "atp-analyze-prepare" / "SKILL.md") and "audio_ingest" in rd(SKD / "atp-edit" / "SKILL.md"), "prepare and Edit Mode read the audio choice")
check("audio not ingested" in rd(LIB / "reference" / "analysis-protocol" / "040_3_per-video-card-20-analysis-cards.md"), "the card template says 'audio not ingested' for the frames-only mode")
check("Audio ingest: <" in rd(PA / "020_2_spawning.md"), "the agent contract carries the audio line")

# --- what must not come back
text = router + "\n".join(rd(p) for p in SKILLS) + rd(LIB / "README.md")
OBSOLETE = "update-from-" + "errors"            # the retired learning command
check(OBSOLETE not in text, "no mention of the obsolete learning command in the router, skills and README")
OTHER = "analyze-then-" + "generate"            # the other pipeline: never named here
check(OTHER not in text, "the router, skills and README do not mention the other pipeline")
check(not [p.name for p in sorted((LIB / "reference").rglob("*.md")) if OTHER in rd(p)], "no reference section mentions the other pipeline")
LEDGER_A, LEDGER_B = "caught_" + "errors", "caught-" + "error"
uses = [ln.strip() for ln in text.splitlines() if (LEDGER_A in ln or LEDGER_B in ln) and not re.search(r"There is no|no `|retired|git history|no error", ln)]
check(not uses and LEDGER_B not in cmds, "the retired error ledger is not used by any step (only 'there is no ...' statements mention it): " + " | ".join(uses[:3]))
check(not (LIB / (LEDGER_A + ".md")).exists(), "the retired ledger file is gone")
stale = [p.name for p in SKILLS + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "pipeline").glob("*.md")) if "read directly with the Read tool" in rd(p) or "PDFs directly with Read" in rd(p)]
check(not stale, "no skill or section says to read PDFs directly with Read: " + ", ".join(stale))

finish()
