"""Structure checks of the library: the router, the phase skills, the section files and the toolkit agree with each other (no model call,
no run needed). The forbidden names (the retired ledger, the obsolete learning command, the other pipeline) are built in pieces so that
this file itself does not carry them."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import AWL, HOME, LIB, PY, check, finish  # noqa: E402

ROUTER = HOME / "commands" / "analyze-with-loupe.md"
SKILLS = sorted((HOME / "skills").glob("awl-*/SKILL.md"))
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
check(len(names) == 20, f"20 phase skills exist ({len(names)})")
check(all(f"`{n}`" in router for n in names), "the router names every phase skill: " + ", ".join(n for n in names if f"`{n}`" not in router))
check(all(b"\r" not in p.read_bytes() for p in SKILLS) and b"\r" not in ROUTER.read_bytes(), "the router and the skills use LF line endings (a CRLF frontmatter is not parsed)")
check(all(rd(p).startswith("---\nname: " + p.parent.name + "\ndescription: ") and "\nuser-invocable: false\n---\n" in rd(p)[:600] for p in SKILLS),
      "every skill has name, description and user-invocable: false in its frontmatter")
handoffs = set()
for p in SKILLS:
    handoffs |= set(re.findall(r"next_skill=(awl-[a-z-]+)", rd(p)))
check(handoffs <= set(names), "every next_skill a hand-off records is an existing skill: " + ", ".join(sorted(handoffs - set(names))))
check(all(any(n in rd(q) for q in SKILLS if q.parent.name != n) or n in router for n in names), "every skill is reached from the router or from another skill")
check(all("## Read now" in rd(p) for p in SKILLS if p.parent.name != "awl-model-guide"), "every phase skill has a Read now list (awl-model-guide is the helper that resolves the guide sections)")
# every section file a Read now list names exists
bad_paths = []
for p in SKILLS:
    for m in re.finditer(r"`AWL/([^`\s]+)`", rd(p)):
        ref = m.group(1).rstrip(".,;:)")
        if any(c in ref for c in "*<>{}"):
            continue
        if not (LIB / ref).exists():
            bad_paths.append(f"{p.parent.name}: {ref}")
check(not bad_paths, "every AWL/ path a skill names exists: " + "; ".join(bad_paths[:5]))

# --- README, reference and pipeline files are LF
lf_bad = [str(p.relative_to(LIB)) for p in [LIB / "README.md", LIB / "learning-log.md"] if b"\r" in p.read_bytes()]
check(not lf_bad, "README and learning log are LF: " + ", ".join(lf_bad))
crlf = [p for p in sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "pipeline").glob("*.md")) if b"\r\n" in p.read_bytes()]
mixed = [str(p.relative_to(LIB)) for p in crlf if re.search(rb"(?<!\r)\n", p.read_bytes())]
print(f"NOTE  {len(crlf)} reference/pipeline section files are CRLF (kept as they are: a line-ending change is the user's decision); mixed endings: {mixed[:5]}")

# --- the toolkit commands the text uses exist
h = subprocess.run([PY, "-X", "utf8", AWL, "-h"], capture_output=True, text=True, encoding="utf-8").stdout
cmds = set(re.search(r"\{([^}]+)\}", h).group(1).split(","))
used = set()
for p in [ROUTER] + SKILLS + sorted((LIB / "reference").rglob("*.md")):
    used |= set(re.findall(r"(?<!no )`T ([a-z][a-z-]+)(?= |`)", rd(p)))     # "no `T caught-error`" states a retirement, it is not a use
missing = sorted(c for c in used if c not in cmds)
check(not missing, "every `T <command>` in the router, the skills and the references is a command of awl.py: " + ", ".join(missing))
# every `T <cmd> ... --flag` the texts cite is a flag of that command (from the command's own --help)
flags_of = {}
for c in sorted(cmds):
    hc = subprocess.run([PY, "-X", "utf8", AWL, c, "-h"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    flags_of[c] = set(re.findall(r"(?m)^\s{2}(?:-\w, )?(--[a-z0-9\-]+)", hc)) | set(re.findall(r"\[(--[a-z0-9\-]+)", hc))
bad_flags = set()
for p in [ROUTER] + SKILLS + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "higgsfield").rglob("*.md")):
    for m in re.finditer(r"`T ([a-z][a-z-]+)((?:[^`\n])*)`", rd(p)):
        c, rest = m.group(1), m.group(2)
        if c not in flags_of:
            continue
        for f in re.findall(r"(--[a-z][a-z0-9\-]*)", rest):
            if f not in flags_of[c] and f != "--help":
                bad_flags.add(f"{p.parent.name if p.name == 'SKILL.md' else p.name}: T {c} {f}")
check(not bad_flags, "every `T <command> --flag` the router, the skills and the references cite is a flag of that command: " + "; ".join(sorted(bad_flags)[:6]))
for c in ("loupe", "qc-consult", "qc-brief", "plan-hints", "caught-flag", "status", "doctor", "lint-run", "cost-report", "seams", "strip-inserts", "doc-text", "placeholder"):
    check(c in cmds, f"awl.py has the {c} command")

# --- the placement marker (the user, 2026-10-22): every placement reference is labelled; no guide image cut from a source frame
GS = LIB / "reference" / "generation-system"
flat = lambda p: " ".join(rd(p).split())
m6 = flat(GS / "200_4b.6_the-placement-marker-spot-and-si.md")
m7 = flat(GS / "205_4b.7_reckoning-the-marker-real-size-d.md")
check("is never built, uploaded or bound in Recreate or Edit Mode" in m6 and "Start and end frames are the exception" in m6 and "T placeholder --image" in m6,
      "generation-system §4b.6: no source-crop guide image in Recreate/Edit, the start/end-frame exception, Create's marked texture")
check("completely removes the red outline, the label and every auxiliary mark" in m6 and "not how the <product> looks" in m6 and "actual object in the scene" in m6,
      "generation-system §4b.6 holds the marker sentence and the removal line")
check("at least TWO neighbours" in m7 and "agree within about 25 %" in m7 and "--occlusion-mask" in m7 and "--window" in m7,
      "generation-system §4b.7 reckons the marker from two agreeing estimates, with occlusion and windows")
wired = [("awl-inputs", SKD / "awl-inputs" / "SKILL.md", "T placeholder --video"), ("awl-inputs image", SKD / "awl-inputs" / "SKILL.md", "T placeholder --image"),
         ("awl-recreate-plan", SKD / "awl-recreate-plan" / "SKILL.md", "T placeholder"), ("awl-edit", SKD / "awl-edit" / "SKILL.md", "T placeholder"),
         ("awl-plan-video", SKD / "awl-plan-video" / "SKILL.md", "placement marker"), ("awl-write-request", SKD / "awl-write-request" / "SKILL.md", "removal line"),
         ("awl-precheck", SKD / "awl-precheck" / "SKILL.md", "Spot and marker"), ("awl-qc", SKD / "awl-qc" / "SKILL.md", "Marker residue"),
         ("production-agents §2", PA / "020_2_spawning.md", "Spot and marker")]
check(not [lbl for lbl, p, needle in wired if needle not in rd(p)], "the placement marker is wired into every step that builds, binds or checks it: " + ", ".join(lbl for lbl, p, needle in wired if needle not in rd(p)))
old_way = [str(p.relative_to(HOME)) for p in SKILLS + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "models").rglob("*.md"))
           if re.search(r"(build|built) (it|the guide)? ?(locally )?from\s+the source's bare surface", " ".join(rd(p).split()))]
check(not old_way, "no step builds a guide from the source's bare surface any more: " + ", ".join(old_way[:4]))

# --- Loupe is started and recorded at run creation, and the same key reaches resume, the agent contract and QC
lw = [("router resume", ROUTER, "T loupe ensure"), ("awl-start", SKD / "awl-start" / "SKILL.md", "T loupe ensure"),
      ("awl-start state", SKD / "awl-start" / "SKILL.md", "loupe=up"),
      ("awl-analyze-produce", SKD / "awl-analyze-produce" / "SKILL.md", "T loupe ensure"), ("awl-qc", SKD / "awl-qc" / "SKILL.md", "T loupe ensure"),
      ("production-agents §1", PA / "010_1_prepared-by-this-session-before.md", "`loupe`"), ("production-agents §2", PA / "020_2_spawning.md", "Loupe: <up|down>")]
check(not [lbl for lbl, p, needle in lw if needle not in rd(p)], "the Loupe start step is written in every place that acts on it: " + ", ".join(lbl for lbl, p, needle in lw if needle not in rd(p)))
qc = rd(SKD / "awl-qc" / "SKILL.md")
check("needs_unmet" in qc and "--note" in qc, "the QC phase handles the keeper asking (needs_unmet, qc-consult --note)")
check("once per video" in qc, "the QC phase asks the keeper once per video")
check("T qc-consult" in qc and "composite_path" in qc and "qc-consult.json" in qc, "the QC phase consults the keeper, views every composite and names the saved answer")
check("T plan-hints" in rd(SKD / "awl-write-request" / "SKILL.md"), "the first request asks for sample hints (plan-hints)")
sub = rd(SKD / "awl-submit" / "SKILL.md")
check("T caught-flag add" in sub and "--flagged" in sub, "a flag is recorded in X7 before the request changes")
check("T caught-flag reconcile" in rd(SKD / "awl-wrapup" / "SKILL.md") and "T caught-flag reconcile" in rd(SKD / "awl-analyze-produce" / "SKILL.md"), "the flags are reconciled as agents report and in the wrap-up")
check("T strip-inserts" in rd(SKD / "awl-recreate-plan" / "SKILL.md") and "seams" in rd(SKD / "awl-recreate-plan" / "SKILL.md"), "the Recreate plan strips the inserts and reads the seam profile")

# --- the audio question (contract item 24): asked once at the start, stored, honoured by prep-all, told to the agents
st = rd(SKD / "awl-start" / "SKILL.md")
check("audio_ingest" in st and "Audio ingest" in st, "awl-start asks the audio question and stores state.json -> audio_ingest")
check("24. **Audio" in router and "audio_ingest" in router, "the router has contract item 24 (audio ingest)")
check("audio_ingest" in rd(SKD / "awl-analyze-prepare" / "SKILL.md") and "audio_ingest" in rd(SKD / "awl-edit" / "SKILL.md"), "prepare and Edit Mode read the audio choice")
check("audio not ingested" in rd(LIB / "reference" / "analysis-protocol" / "040_3_per-video-card-20-analysis-cards.md"), "the card template says 'audio not ingested' for the frames-only mode")
check("Audio ingest: <" in rd(PA / "020_2_spawning.md"), "the agent contract carries the audio line")

# --- what must not come back
text = router + "\n".join(rd(p) for p in SKILLS) + rd(LIB / "README.md")
OBSOLETE = "update-from-" + "errors"            # the retired learning command
check(OBSOLETE not in text, "no mention of the obsolete learning command in the router, skills and README")
OTHER = "analyze-then-" + "generate"            # the other pipeline: never named here
check(OTHER not in text, "the router, skills and README do not mention the other pipeline")
check(not [p.name for p in sorted((LIB / "reference").rglob("*.md")) if OTHER in rd(p)], "no reference section mentions the other pipeline")
# the library this command was born from is never named either (its name, its skill prefix, its toolkit, its home variable, its path alias)
OLD = ["analyze-then-" + "pick", "atp" + "-", "atp" + ".py", "ATP" + "_HOME", "ATP" + "/", "`ATP" + "`"]
everything = [ROUTER] + SKILLS + [LIB / "README.md", LIB / "learning-log.md", LIB / "config.json", LIB / "scripts" / "awl.py", LIB / "scripts" / "docs_tool.py"] + \
    sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "models").rglob("*.md")) + sorted((LIB / "higgsfield").rglob("*.md")) + sorted((LIB / "pipeline").glob("*.md")) + \
    sorted((LIB / "tests").glob("*.py")) + sorted((LIB / "scripts").glob("check*"))
leaks = []
for p in everything:
    body = rd(p)
    body = re.sub(r"C:/Users/Glaresquare1/\.claude/" + "analyze-then-" + "pick" + r"(?=[/`\s)])", "<path>", body)      # a file path may name the source library; nothing else may
    for o in OLD:
        if re.search(r"(?<![A-Za-z_])" + re.escape(o), body):
            leaks.append(f"{p.name}: {o}")
            break
check(not leaks, "no file of this command names the library it was born from (only a file path may): " + "; ".join(leaks[:6]))
# the QC-fixes choice (item 27): asked at the start, stored, carried by the contract, acted on in QC and by the main session
check("27. **QC fixes" in router and "qc_fixes" in router, "the router has contract item 27 (QC fixes) and names the state key")
check("header \"QC fixes\"" in st and "qc_fixes=ask|auto" in st, "awl-start asks the QC-fixes question and stores state.json -> qc_fixes")
check("QC fixes: <ask|auto>" in rd(PA / "020_2_spawning.md") and "qc_fix_permission" in rd(PA / "030_3_the-agent-s-contract.md"), "the agent contract carries the QC-fixes line and the blocker")
check("qc_fix_permission" in qc and "fix_proposal" in qc, "the QC phase stops with a fix proposal under ask")
check("qc_fix_permission" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "header \"QC fix\"" in rd(SKD / "awl-analyze-produce" / "SKILL.md"), "the main session asks the fix question and continues the agent")
check("25. **Scripts gather" in router and "26. **Pilot first" in router, "the router has the gather-only and pilot-first items")
# the Free sub-mode (item 17, A6f): asked at the start, the requirement kept verbatim, its own planning skill, the kind per video, QC fixes for every sub-mode
check("awl-free-plan" in names and "`awl-free-plan`" in router and "Three Analyze sub-modes" in router, "the router has the Free sub-mode and its skill")
check("**Free**" in st and "free_references" in st and "requirement.md" in st and "analyze_submode=recreate|create|free" in st, "awl-start asks Free, with or without references, and keeps the requirement verbatim")
fp = rd(SKD / "awl-free-plan" / "SKILL.md")
check("requirement.md" in fp and "videos_kind" in fp and "T qc-brief" in fp and "free_plan_confirmed" in fp and "next_skill=awl-asset-plan" in fp, "the free plan reads the requirement, lists the past misses, is confirmed once, gives each video a kind and hands off to the asset plan")
check("next_skill=awl-free-plan" in rd(SKD / "awl-analyze-prepare" / "SKILL.md") and "next_skill=awl-free-plan" in rd(SKD / "awl-analyze-study" / "SKILL.md"), "prepare (no references) and study (with references) hand off to the free plan")
check("videos_kind" in rd(SKD / "awl-plan-video" / "SKILL.md") and "Video kind" in rd(PA / "020_2_spawning.md") and "Free" in rd(SKD / "awl-asset-plan" / "SKILL.md"), "the kind of a Free video reaches the plan step, the contract and the asset plan")
check("every Analyze sub-mode" in router.split("27. **QC fixes")[1][:120] and "Recreate, Create and Free" in st, "the QC-fixes choice covers every Analyze sub-mode")

check("Pilot first" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "stalled" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "frozen once its agent is spawned" in rd(SKD / "awl-analyze-produce" / "SKILL.md"),
      "the produce phase has the pilot, the stalled-agent recovery and the request freeze rules")
# the keeper's answer: the QC phase knows the fields that carry the admin's words and the origin; the writer knows held_back_why and the sentence-safe fields
check("`title`" in qc and "`run`" in qc and "`busy`" in qc, "the QC phase reads the sample's title and origin from the consult answer and knows the busy mode")
wr = rd(SKD / "awl-write-request" / "SKILL.md")
check("held_back_why" in wr and "in your own\n      words" in wr, "the writer reads held_back_why and applies a hint in its own words")
# the preview is the 720x1280 burn, never the proxy; no product clause teaches a faded product
check("never the 540×960 capcut-cli proxy" in rd(LIB / "reference" / "capcut-assembly" / "070_6_deliverables-analyze-mode.md") and "720×1280" in rd(SKD / "awl-record" / "SKILL.md"), "the preview is documented as the 720x1280 burn, never the proxy")
faded = [str(p.relative_to(LIB)) for p in sorted((LIB / "reference").rglob("*.md")) if re.search(r"colours as muted as|no brighter than the room", rd(p))]
check(not faded, "no reference teaches a faded product clause: " + ", ".join(faded))
# the toolkit labels nothing: no verdict word in the toolkit's output keys of the converted commands (the code itself)
tk = rd(LIB / "scripts" / "awl.py")
check(not re.search(r'"(verdict|provisional|likely_noise|kind_hint|quick_picks|passed_automatic_checks)"\s*:', tk), "the toolkit prints no verdict, provisional, noise or pick key")
LEDGER_A, LEDGER_B = "caught_" + "errors", "caught-" + "error"
uses = [ln.strip() for ln in text.splitlines() if (LEDGER_A in ln or LEDGER_B in ln) and not re.search(r"There is no|no `|retired|git history|no error", ln)]
check(not uses and LEDGER_B not in cmds, "the retired error ledger is not used by any step (only 'there is no ...' statements mention it): " + " | ".join(uses[:3]))
check(not (LIB / (LEDGER_A + ".md")).exists(), "the retired ledger file is gone")
stale = [p.name for p in SKILLS + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "pipeline").glob("*.md")) if "read directly with the Read tool" in rd(p) or "PDFs directly with Read" in rd(p)]
check(not stale, "no skill or section says to read PDFs directly with Read: " + ", ".join(stale))

finish()
