"""Structure checks of the library: the router, the phase skills, the section files and the toolkit agree with each other (no model call,
no run needed). The forbidden names (the retired ledger, the obsolete learning command, the other pipeline) are built in pieces so that
this file itself does not carry them."""
import json
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
check(len(names) == 24, f"24 phase skills exist ({len(names)})")
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
for c in ("loupe", "qc-consult", "qc-brief", "plan-hints", "caught-flag", "status", "doctor", "lint-run", "cost-report", "seams", "strip-inserts", "doc-text"):
    check(c in cmds, f"awl.py has the {c} command")

# --- no placement marker (the user, 2026-10-28: "remove the reference placement from the analyze-with-loupe totally ... just let the original
#     video as a reference, i believe prompts,images and instructions suffice"): the original's silent footage is the only video reference, and no
#     command, step, section, guide or the README builds, binds or checks a placement preview; no guide image cut from a source frame either
GS = LIB / "reference" / "generation-system"
flat = lambda p: " ".join(rd(p).split())  # noqa: E731
check("placeholder" not in cmds, "awl.py has no placeholder command any more")
check(not list(GS.glob("*placement-marker*")) and not list(GS.glob("*reckoning-the-marker*")), "the placement-marker sections of the generation system are gone")
gone = re.compile(r"placement marker|placement preview|placement still|T placeholder|awl\.py placeholder|§4b\.[67]\b|removal line|Marker residue|Spot and marker", re.I)
left = [f"{p.relative_to(HOME)}: {m.group(0)}" for p in [ROUTER] + SKILLS + sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "models").rglob("*.md"))
        + [LIB / "README.md", LIB / "pipeline" / "preprocessing.md"] for m in [gone.search(flat(p))] if m]
check(not left, "no step, section, guide or the README speaks of a placement marker or preview any more: " + "; ".join(left[:6]))
four = flat(GS / "190_4b.5_expressing-it-to-the-model-with.md")
check("The original reference" in four and "is never built, uploaded or bound" in four and "the literal first frame" in four,
      "generation-system §4b.5: the original's silent footage is the only video reference, no source-crop guide image, start frames photoreal")
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
check("`original video`" in qc and "circle, arrow or box" in qc, "the QC phase reads a sample's source tags (an original video is never a generated frame) and knows a zoom is drawn only under a marked frame, as Loupe draws them")
check("alone carries that frame's marks" in qc and "the frame above it left clean" in qc and "frame-N-marked.png" in qc, "the QC phase knows a marked frame's zoom alone carries its marks, the frame above it left clean, and where each frame is kept whole with its marks in place, as Loupe draws them (the admin, 2026-11-02)")
wr1 = re.sub(r"\s+", " ", rd(SKD / "awl-write-request" / "SKILL.md"))
pc1 = re.sub(r"\s+", " ", rd(SKD / "awl-precheck" / "SKILL.md"))
check("X4b" in pc1 and "T prompt-template" in pc1 and "T template-apply" in pc1 and "video-NN-judge-brief.md" in pc1 and "T plan-hints" not in wr1
      and "Never rewrite, trim, reorder or improve the judge's prompt" in pc1,
      "after X1-X4 the whole checked brief goes to the judge (X4b: prompt-template), its prompt goes into the request word for word (template-apply), never improved")
check("Must carry" in wr1 and "video-NN-musts.md" in wr1 and "T prompt-template" not in wr1 and "Must carry" in pc1 and "X4 and X4b only" in rd(SKD / "awl-analyze-produce" / "SKILL.md"),
      "X2 writes the checked draft and its must-carry lines and never asks the judge; X4 checks them; A9 runs X4b after X4")
qc1 = re.sub(r"\s+", " ", rd(SKD / "awl-qc" / "SKILL.md"))
check("has caught what it caught" in qc1 and "evidence_sent" in qc1 and "--attempt aK" in qc1 and "result.json → judge" in qc1,
      "QC consults the judge after its first pass; the consult carries the prompt used, the template and the brief, and the cause is kept in result.json judge")
check('"judge": {"template"' in rd(LIB / "reference" / "production-agents" / "040_4_60-outputs-video-nn-result-json.md")
      and "T prompt-template" in rd(HOME / "commands" / "analyze-with-loupe.md"), "result.json has the judge field and contract item 23 names prompt-template")
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
check("header \"QC fixes\"" in st and "qc_fixes=ask|auto|off" in st and "No QC, I review at the end" in st,
      "awl-start asks the QC-fixes question with its third option (no QC after the first generation) and stores state.json -> qc_fixes")
check("`off`" in router.split("27. **QC fixes")[1][:900] and "no awl-qc at all" in rd(PA / "020_2_spawning.md") and "QC fixes `off`" in rd(SKD / "awl-postprocess" / "SKILL.md")
      and "QC fixes `off`" in rd(SKD / "awl-wrapup" / "SKILL.md") and "none with `off`" in rd(PA / "030_3_the-agent-s-contract.md"),
      "QC fixes off reaches the router, the contract (no awl-qc at all), X8's hand-off, the wrap-up and the regeneration rule")
check("QC fixes: <ask|auto|off>" in rd(PA / "020_2_spawning.md") and "qc_fix_permission" in rd(PA / "030_3_the-agent-s-contract.md"), "the agent contract carries the QC-fixes line and the blocker")
check("qc_fix_permission" in qc and "fix_proposal" in qc, "the QC phase stops with a fix proposal under ask")
check("qc_fix_permission" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "header \"QC fix\"" in rd(SKD / "awl-analyze-produce" / "SKILL.md"), "the main session asks the fix question and continues the agent")
check("25. **Scripts gather" in router and "26. **Pilot first" in router, "the router has the gather-only and pilot-first items")
# the Free sub-mode (item 17, A6f): asked at the start, the requirement kept verbatim, its own planning skill, the kind per video, QC fixes for every sub-mode
check("awl-free-plan" in names and "`awl-free-plan`" in router and "Four Analyze sub-modes" in router, "the router has the Free sub-mode and its skill")
check("**Free**" in st and "free_references" in st and "requirement.md" in st and "analyze_submode=recreate|create|free" in st, "awl-start asks Free, with or without references, and keeps the requirement verbatim")
fp = rd(SKD / "awl-free-plan" / "SKILL.md")
check("requirement.md" in fp and "videos_kind" in fp and "T qc-brief" in fp and "free_plan_confirmed" in fp and "next_skill=awl-asset-plan" in fp, "the free plan reads the requirement, lists the past misses, is confirmed once, gives each video a kind and hands off to the asset plan")
check("next_skill=awl-free-plan" in rd(SKD / "awl-analyze-prepare" / "SKILL.md") and "next_skill=awl-free-plan" in rd(SKD / "awl-analyze-study" / "SKILL.md"), "prepare (no references) and study (with references) hand off to the free plan")
check("videos_kind" in rd(SKD / "awl-plan-video" / "SKILL.md") and "Video kind" in rd(PA / "020_2_spawning.md") and "Free" in rd(SKD / "awl-asset-plan" / "SKILL.md"), "the kind of a Free video reaches the plan step, the contract and the asset plan")
check("every Analyze sub-mode" in router.split("27. **QC fixes")[1][:120] and "Recreate, Create, Free and Static" in st, "the QC-fixes choice covers every Analyze sub-mode")


# the Static sub-mode (item 36, the user 2026-11-05): narrated still-image videos; no Higgsfield and no Loupe; its own skills, contract and reference
STK = ("awl-static-plan", "awl-static-sound", "awl-static-images", "awl-static-edit")
sp_text = {n: rd(SKD / n / "SKILL.md") for n in STK if (SKD / n / "SKILL.md").is_file()}
item36 = router.split("36. **Static")[1].split(chr(10))[0] if "36. **Static" in router else ""
check(len(sp_text) == 4 and item36 and all(f"`{n}`" in item36 for n in STK + ("awl-start", "awl-analyze-prepare", "awl-analyze-study", "awl-analyze-produce", "awl-record", "awl-wrapup")),
      "the router has item 36 (Static) and names every skill that owns it; the four Static skills exist")
check("**Static**" in st and "analyze_submode=recreate|create|free|static" in st and '"Images": **"Generate with OpenAI"**' in st and "T static check" in st and "static_images=api|prompts" in st,
      "awl-start offers Static, asks Images (OpenAI or prompts) with the QC-fixes question, checks the setup and stores the choice")
check("next_skill=awl-static-plan" in rd(SKD / "awl-analyze-study" / "SKILL.md") and "next_skill=awl-analyze-produce" in sp_text.get("awl-static-plan", "")
      and "--fps 1 --dense-fps 1 --no-extras" in rd(SKD / "awl-analyze-prepare" / "SKILL.md") and "--voice" in rd(SKD / "awl-analyze-study" / "SKILL.md"),
      "Static: 1 fps without extras in prepare, the voice numbers in study, study hands to the static plan and the plan to produce")
check("### A9s. Static" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "awl-static-sound" in rd(SKD / "awl-analyze-produce" / "SKILL.md")
      and "static.waiting=images" in sp_text.get("awl-static-images", "") and "T image intake" in sp_text.get("awl-static-images", ""),
      "produce has A9s (sound for every video, then images, then the agents); prompts mode stops for the user's folder and takes it in by copy")
s2s = rd(PA / "025_2s_spawning-static.md")
check("<api|prompts>" in s2s and "<ask|auto|off>" in s2s and "Loupe: not used in Static" in s2s and "No Higgsfield" in s2s
      and all(n in s2s for n in ("awl-static-images", "awl-static-edit", "awl-record")) and "OPENAI_API_KEY" in s2s,
      "the Static agent contract (production-agents 2s): its own placeholders, no Loupe, no Higgsfield, its three skills, the key only in the environment")
hig = [n for n, tx in sp_text.items() for w in ("mcp__higgsfield", "generate_video", "jobs_wait", "media_upload", "T ledger begin") if w in tx]
check(not hig, "no Static skill calls a Higgsfield tool or the video ledger by hand (image calls go through T image generate): " + ", ".join(hig))
check(all(f"{d}" in rd(LIB / "reference" / "static.md") for d in ("| 1 |", "| 9 |")) and "Nothing in Static calls Higgsfield or Loupe" in rd(LIB / "reference" / "static.md"),
      "the Static reference is indexed in nine sections and says it calls neither Higgsfield nor Loupe")
check("capcut import-srt" in sp_text.get("awl-static-edit", "") and "capcut_add_captions" in sp_text.get("awl-static-edit", "").split("## Never")[1],
      "Static captions reach CapCut by import-srt; CapCut's own caption tools are named only to be never used")

# Recreate: the whole source in one generation when it fits the locked model's maximum (the user, 2026-11-05)
_gs31 = rd(LIB / "reference" / "generation-system" / "050_3b.1_plan-the-clips-in-the-video-plan.md")
check("is sent whole, in ONE generation" in _gs31 and "a 14 or 15 s video is one generation, never two" in _gs31 and "as Higgsfield answers it live, never a number" in _gs31
      and "model_limits" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "the fewest generations its length needs" in _gs31
      and "Edit Mode** keeps the" in _gs31 and "goes whole, in one generation with its cuts" in rd(SKD / "awl-plan-video" / "SKILL.md")
      and "the source stays whole: one generation" in rd(SKD / "awl-recreate-plan" / "SKILL.md"),
      "Recreate sends a source within the model's maximum whole (one generation), splits only where it must, and a longer one into the fewest parts")
# the limits are recorded from the live answer where it is first read: E4 at A6r (before the source is prepared) and A8 again
check("set model_limits='" in rd(SKD / "awl-recreate-plan" / "SKILL.md").split("### E4.")[1].split("### E5.")[0]
      and "set model_limits='" in rd(SKD / "awl-analyze-produce" / "SKILL.md"),
      "the live model limits are recorded at E4 (A6r, before the source is prepared and split) and refreshed at A8")
check("A run with no `state.json → model_limits`" in rd(SKD / "awl-analyze-produce" / "SKILL.md").split("### A9. ")[1].split("### A9s.")[0],
      "a run resumed from before the live limits existed records them at A9's start, before any video is planned")
# Static's format and final (the user, 2026-11-05): the CapCut export is the final, at the format the user picks at A5 (the best fit for the
# references first, with options); strong lines by the voice-design model, sparingly and never jumping unannounced
_s2t = rd(LIB / "reference" / "static" / "020_2_the-static-card-and-the-spec-a3.md")
_s4t = rd(LIB / "reference" / "static" / "040_4_the-script-a6s.md")
_s6t = rd(LIB / "reference" / "static" / "060_6_the-voice-and-the-bed-a6s-s2.md")
_s7t = rd(LIB / "reference" / "static" / "070_7_the-edit-s4.md")
_a5t = rd(SKD / "awl-analyze-study" / "SKILL.md")
check("T static formats --run RUN" in _a5t and 'header "Format"' in _a5t and "(Recommended)" in _s2t
      and "T static format --run RUN --aspect A --res R" in _s2t.replace("\n", " ") and "--canvas <state.json" in rd(SKD / "awl-static-edit" / "SKILL.md")
      and "**The CapCut project is the final**" in _s7t and "that export is the final" in rd(SKD / "awl-wrapup" / "SKILL.md")
      and "its export is the final" in rd(HOME / "commands" / "analyze-with-loupe.md"),
      "Static asks the format at A5 (the best fit first), stores it, makes the CapCut project at its export size, and that export is the final")
check('"strong": true' in _s4t and "never two in a row" in _s4t and "**Strong lines**" in _s6t and "timbre_sim" in _s6t
      and "voice_match" in rd(SKD / "awl-static-sound" / "SKILL.md"),
      "strong lines: the voice-design model at the references' peaks only, measured against the run's voice, made again or cloned when apart")
# Static's text look is the references' (the user, 2026-11-05: "everything is data driven (from the references) and nothing is predefined")
_se = rd(SKD / "awl-static-edit" / "SKILL.md")
check("**Text look**" in _s2t and "never the house text style" in _s2t and "--keep-text" in _se and "T capcut-font --draft" in _se
      and "capcut-text-style --draft" not in _se and "**No house text style in Static**" in _s7t
      and "Static: the references' own text look, item 36" in rd(HOME / "commands" / "analyze-with-loupe.md"),
      "Static takes the text look from the references (font, size, colours): capcut-cli's flags, T capcut-font, capcut-repair --keep-text, no house style")
# a source at most 0.4 s over the maximum is one generation of its first <maximum> seconds (the user, run 20261104-225639-04)
check("at most 0.4 s over the maximum" in _gs31 and "At most 0.4 s over the maximum" in rd(SKD / "awl-recreate-plan" / "SKILL.md")
      and "`T trim --end <maximum>`" in rd(SKD / "awl-recreate-plan" / "SKILL.md")
      and "at most 0.4 s over the maximum sends only its first <maximum> seconds" in rd(SKD / "awl-plan-video" / "SKILL.md"),
      "a source at most 0.4 s over the model's maximum is one generation of its first <maximum> seconds, in item 7, A6r, E5 and X1")
# the user's examples (2026-11-05): 15 s on a 15 s maximum is never 7.5 + 7.5; 27 s on a 30 s maximum goes at once; a "works best" note
# never lowers the maximum; a take a little longer than its source is trimmed
check("never lowers it" in _gs31 and "a 27 s video is one generation" in _gs31 and "never 7.5 + 7.5 s" in _gs31 and "16 s for 15 s" in _gs31,
      "item 7 keeps the user's examples: the hard maximum, 15 s never 7.5 + 7.5, 27 s on 30 s at once, a longer take trimmed")

check("Pilot first" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "stalled" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "frozen once its agent is spawned" in rd(SKD / "awl-analyze-produce" / "SKILL.md"),
      "the produce phase has the pilot, the stalled-agent recovery and the request freeze rules")
# the keeper's answer: the QC phase knows the fields that carry the admin's words and the origin; the writer knows held_back_why and the sentence-safe fields
check("`title`" in qc and "`run`" in qc and "`busy`" in qc, "the QC phase reads the sample's title and origin from the consult answer and knows the busy mode")
wr = rd(SKD / "awl-write-request" / "SKILL.md")
wrn = re.sub(r"\s+", " ", wr)
check("template_fix" in wrn and "every other part word for word" in wrn and "needs_unmet" in pc1 and "--add-must" in pc1 and "--use-draft" in pc1,
      "a regeneration takes the judge's template_fix and keeps the rest word for word; X4b re-asks the judge before it adds a line or keeps the draft")
# the judge decides the product images (the admin, 2026-10-30): X2 records each input's original and puts the product images last, X4b applies the
# judge's choice, X3 prepares an image it added (by the placeholder the toolkit writes), QC sends the inputs and a regeneration takes the QC answer's
tk_src = rd(AWL)
ins = re.sub(r"\s+", " ", rd(SKD / "awl-inputs" / "SKILL.md"))
check("product-images" in cmds and '"<X3: prepare {name} for {lab}>"' in tk_src.replace("f\"<X3", "\"<X3") and "<X3: prepare <file> for Image N>" in ins
      and '"source": {"original"' in wrn and "ride last" in wrn and "T product-images" in wrn and "inputs.without_a_recorded_source" in wrn
      and "product_images" in pc1 and "musts_renumbered" in pc1 and "product_images_problems" in pc1 and "T product-images" in qc1
      and "product_images" in rd(LIB / "reference" / "production-agents" / "040_4_60-outputs-video-nn-result-json.md")
      and "T product-images" in rd(HOME / "commands" / "analyze-with-loupe.md"),
      "X2 records each input's original and puts the product images last, X4b applies the judge's product images, X3 prepares one it added by the "
      "placeholder the toolkit writes, QC and a regeneration take the QC answer's (T product-images), result.json keeps them")
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

# --- the own voiceover (item 31): Create asks the method before the model, then the voice, language and style; Free only from the requirement;
#     every per-video step that acts on it names it; the agent contract carries it; the toolkit has the command
VOD = LIB / "reference" / "voiceover"
vo_files = sorted(p.name for p in VOD.glob("*.md")) if VOD.is_dir() else []
check(len(vo_files) == 11 and (LIB / "reference" / "voiceover.md").is_file(), f"the voiceover reference has its index and 11 sections ({len(vo_files)})")
vo_all = " ".join(rd(p) for p in VOD.glob("*.md"))
check(all(k in vo_all for k in ("**native**", "**lipsync**", "**overlay**", "sync_so", "driving audio", "Scottish accent", "Kosovar Albanian", "Never claim that a take was listened to")),
      "the voiceover reference holds the three methods, the sync pass, the user's accent and dialect examples and the honesty rule")
check("31. **Own voiceover" in router and "mcp__elevenlabs__search_voices" in router and "item 31 →" in router and "mcp__elevenlabs__text_to_speech" not in router.split("---")[1],
      "the router has contract item 31 and its labels, and allows only the read-only ElevenLabs tools without asking (a paid take still asks)")
check('header "Voiceover"' in st and 'header "Voice"' in st and 'header "Language"' in st and 'header "Voice style"' in st and "voiceover.method=native|lipsync|overlay" in st
      and "2b. **Own voiceover" in st and st.index("2b. **Own voiceover") < st.index("4. **Model"), "awl-start asks the method before the model menu, then the voice, the language and the style, and stores state.json -> voiceover")
check("2b. **Own voiceover: only when the requirement asks for it**" in fp and "never offers, recommends or asks it" in fp, "the free plan uses a voiceover only when the requirement asks and never suggests one")
vo_wired = [("awl-plan-video", "T voiceover record"), ("awl-plan-video", "T voiceover outdir"), ("awl-write-request", "**native**"), ("awl-inputs", "`voiceover.md` §7"),
            ("awl-precheck", "Own voiceover"), ("awl-postprocess", "T voiceover align"), ("awl-postprocess", "T voiceover mix"), ("awl-postprocess", "sync_so"),
            ("awl-submit", "--video NN-sync"), ("awl-qc", "Own voiceover"), ("awl-record", "pronunciation: not checked"), ("awl-wrapup", "Voiceover:"),
            ("awl-analyze-produce", "`voiceover` (a take"), ("awl-create-plan", "voiceover.method"), ("awl-asset-plan", "voiceover.method"),
            ("awl-qc", "X8 step 5b has not run yet"), ("awl-analyze-produce", "a fork never voices a"), ("awl-feedback", "**A voiced video (item 31).**"),
            ("awl-postprocess", "never `with-voiceover.mp4`")]
vo_miss = [f"{s}: {n}" for s, n in vo_wired if n not in rd(SKD / s / "SKILL.md")]
check(not vo_miss, "the own voiceover is wired into every step that acts on it: " + "; ".join(vo_miss))
check("Voiceover: <voiceover>" in rd(PA / "020_2_spawning.md") and "`voiceover`" in rd(PA / "030_3_the-agent-s-contract.md") and '"voiceover"' in rd(PA / "040_4_60-outputs-video-nn-result-json.md"),
      "the agent contract carries the Voiceover line, the voiceover blocker and the result field")
check("voiceover" in cmds, "awl.py has the voiceover command")

# --- memes in Create (item 32): asked at the start beside the voiceover method, stored, honoured wherever an insert is planned, placed or
#     checked; the contract carries it; Free takes it from the requirement
check("32. **Memes in Create" in router and "item 32 →" in router, "the router has contract item 32 and its labels")
check('header "Memes"' in st and "memes=include" in st and "memes=none" in st and "2c. **Memes" in st and st.index("2c. **Memes") < st.index("4. **Model"),
      "awl-start asks the memes choice in Create, before the model menu, and stores state.json -> memes")
mm_wired = [("awl-create-plan", "`memes=include`"), ("awl-plan-video", "`memes=include`"), ("awl-postprocess", "`memes=include`"), ("awl-qc", "`memes=none`"),
            ("awl-precheck", "`memes=none`"), ("awl-asset-plan", "`memes=none`"), ("awl-free-plan", "`memes=include`"), ("awl-analyze-produce", "\"Memes\" line")]
mm_miss = [f"{s_}: {n}" for s_, n in mm_wired if n not in rd(SKD / s_ / "SKILL.md")]
check(not mm_miss, "the memes choice is wired into every step that plans, places or checks an insert: " + "; ".join(mm_miss))
check("Memes: <memes>" in rd(PA / "020_2_spawning.md") and "**Memes**" in rd(PA / "030_3_the-agent-s-contract.md")
      and "memes = include" in rd(GS / "090_3c_reference-inserts-memes-cut-from.md"), "the contract carries the Memes line and its check; generation-system §3c states the Create condition")


# --- effort level (item 33): asked at the start in both modes, stored by T effort, read by prep-all (the reference sampling) and the produce
#     phase (agents at once, the pilot); the analysts' close-up budget lives in the protocol section they read. QC and Loupe are never part of it
EF = LIB / "reference" / "effort"
ef_all = " ".join(rd(p_) for p_ in EF.glob("*.md")) if EF.is_dir() else ""
check((LIB / "reference" / "effort.md").is_file() and len(list(EF.glob("*.md"))) == 2 and all(k in ef_all for k in ("never with AskUserQuestion",
      "1. **Low**", "2. **Medium**", "3. **High**", "4. **XHigh**", "5. **Max**", "| setting | Low | Medium | High | XHigh | Max |", "motion peaks densified",
      "production agents at once", "pilot video first", "your own numbers", "`T new-run` writes", "no frame or video is made smaller", "**The judges.**",
      "Coverage", "never skips what a card needs")) and "four options (" not in ef_all and "through Other" not in ef_all,
      "the effort reference offers all five levels, numbered, in plain chat (never a four-option dialog), with the table, the judges rule, the floors, "
      "the never-skip rule and the level empty until stored")
check("33. **Effort level" in router and "all five offered in plain chat" in router and "item 33 →" in router and "5d. **Effort**" in st and "plain chat" in st
      and "from all five levels" in st and "four options and Other" not in st and "T effort --run RUN --level" in st and "effort §1" in st and "fewer than its five levels" in st,
      "the router has item 33; awl-start asks the effort question in plain chat with all five levels (step 5d), reads effort section 1 and stores it with T effort")
settings = json.loads((HOME / "settings.json").read_text(encoding="utf-8"))
guards = [e for e in (settings.get("hooks") or {}).get("PreToolUse", []) if any("awl_input_guard.py" in h.get("command", "") for h in e.get("hooks", []))]
check("34. **The user's folders are read-only**" in router and "item 34 →" in router and "(item 34)" in rd(PA / "020_2_spawning.md")
      and "references or examples folders (they are read-only)" in rd(LIB / "reference" / "analysis-protocol" / "080_7_scale-and-delegation-2-analysis.md")
      and (HOME / "hooks" / "awl_input_guard.py").is_file() and len(guards) == 1 and all(x in guards[0].get("matcher", "") for x in ("Bash", "PowerShell", "Write", "Edit")),
      "item 34 (the user's folders are read-only) is in the router, the production agents' contract and the analysis agents' prompt, and its hook is registered for Bash, PowerShell, Write and Edit")
check("effort.max_agents" in rd(SKD / "awl-analyze-produce" / "SKILL.md") and "effort.pilot_from" in rd(SKD / "awl-analyze-produce" / "SKILL.md")
      and "Upload without asking" in rd(SKD / "awl-inputs" / "SKILL.md") and "no reference review" in router,
      "the produce phase takes the agents at once and the pilot threshold from the level; no approval stop before uploads or generations")
check("densify_ranges" in rd(LIB / "reference" / "analysis-protocol" / "020_1_inputs-per-video-produced-by-awl.md")
      and "<densify_ranges>" in rd(LIB / "reference" / "analysis-protocol" / "080_7_scale-and-delegation-2-analysis.md") and "effort" in cmds,
      "the analysts get the close-up budget, and awl.py has the effort command")
# the judges stay stable (the user, 2026-10-27): no effort setting reaches QC, its Loupe consult or the production agents' contract
judge_texts = {"awl-qc": qc, "anomaly-catalog §4": rd(LIB / "reference" / "anomaly-catalog" / "220_4_the-qc-stack-x9-in-order.md"),
               "generation-system §9": rd(LIB / "reference" / "generation-system" / "340_9_post-generation-qc-after-downloa.md"),
               "capcut-assembly §5": rd(LIB / "reference" / "capcut-assembly" / "060_5_qc-of-the-project.md"),
               "the contract prompt": rd(PA / "020_2_spawning.md")}
leak = [k for k, v in judge_texts.items() if re.search(r"(?i)effort|@full|qc --run", v)]
check(not leak, "no effort setting reaches QC, its Loupe consult or the agent contract: " + ", ".join(leak))

# --- orientation (the user, 2026-10-27): the output keeps the original's perspective; no text tells a step to flip a source
sp = " ".join(rd(GS / "260_5c.2b_prepare-the-source-before-it-rid.md").split())
flip_texts = [p_.name for p_ in sorted((LIB / "reference").rglob("*.md")) + sorted((LIB / "models").rglob("*.md")) + SKILLS
              if re.search(r"(?i)(source|copy|video 1)[^.\n]{0,40}(is |are )?flipped (horizontally )?(in|before) (the )?(preparation|upload)|the prepared (copy|source) flipped", rd(p_))]
check("**Orientation: never flipped.**" in sp and "original perspective" in sp and not flip_texts,
      "the source is never flipped (generation-system §5c.2b) and no text tells a step to flip one: " + ", ".join(flip_texts))

# --- item 35 (the user, 2026-11-03): Create and Free `create` videos are clean continuous takes, as few as the length allows, and the whole edit
#     is made in CapCut with the tools found live; no sticker or emoji, ever (item 6)
CA = LIB / "reference" / "capcut-assembly"
owners35 = ["awl-analyze-study", "awl-create-plan", "awl-free-plan", "awl-plan-video", "awl-write-request", "awl-precheck", "awl-postprocess",
            "awl-qc", "awl-record"]
check("35. **Create: clean source takes, the whole edit in CapCut**" in router and "item 35 →" in router
      and all(f"`{n}`" in router.split("35. **Create: clean source takes")[1].split(chr(10))[0] for n in owners35)
      and all("item 35" in rd(SKD / n / "SKILL.md") for n in owners35) and "(command item 35)" in rd(PA / "020_2_spawning.md"),
      "item 35 is in the router with its owners and labels, in every skill that acts on it and in the production agents' contract")
full35 = [n for n in ("awl-plan-video",) if "As few generations as the video needs, decided per video" in rd(SKD / n / "SKILL.md")
          and "Clean means nothing added on top of the scene; it never limits the genre" in rd(SKD / n / "SKILL.md")
          and "edit the additions that label, decorate," + chr(10) + "      arrange or repackage it" in rd(SKD / n / "SKILL.md")]
check(full35 == ["awl-plan-video"] and "the whole rule is `awl-plan-video`'s item 35" in rd(SKD / "awl-create-plan" / "SKILL.md"),
      "the whole item 35 (clean means no editorial addition, never a limit on the genre; as few generations as the video needs, decided per "
      "video, never one per shot; the non-exhaustive test) is in awl-plan-video, and awl-create-plan carries what A6 acts on and points there: " + ", ".join(full35))
sec3c = CA / "045_3c_the-create-edit-from-clean-takes.md"
check(sec3c.is_file() and "| 3c | The Create edit from clean takes (command item 35) |" in rd(LIB / "reference" / "capcut-assembly.md")
      and "045_3c_the-create-edit-from-clean-takes.md" in rd(SKD / "awl-plan-video" / "SKILL.md")
      and "045_3c_the-create-edit-from-clean-takes.md" in rd(SKD / "awl-postprocess" / "SKILL.md")
      and "Edit layer | scene layer" in rd(LIB / "reference" / "analysis-protocol" / "040_3_per-video-card-20-analysis-cards.md")
      and "capcut detect-scenes" in rd(SKD / "awl-qc" / "SKILL.md") and "video-NN-take-K.mp4" in rd(SKD / "awl-record" / "SKILL.md"),
      "the Create edit has its CapCut section (read at X1 and X8), the cards an edit layer apart from the scene layer, QC the continuity check of "
      "every take and X10 the takes as the clean originals")
tools = rd(CA / "010_1_tools-and-rules.md")
check("`+capcut`" in tools and "suggestions for the usual operations" in tools and "`capcut --help`" in tools
      and "suggestions for the usual operations" in rd(sec3c) and "search for one first (§1)" in rd(sec3c) and "loading only what the project needs" in tools
      and all(f"mcp__capcut__capcut_{x}" in router for x in ("add_keyframe", "add_mask", "add_filter", "list_transitions", "delete_segment"))
      and not any(f"mcp__capcut__capcut_{x}" in router for x in ("add_captions", "transcribe", "clear_captions", "raw_patch")),
      "the agents find the CapCut tools live (ToolSearch +capcut, the catalog tools, capcut --help) and treat the named ones as suggestions; the "
      "router allows the edit's tools and never the caption, transcript or raw-patch tools")
check("**No sticker or emoji added, ever**" in router and "capcut_add_sticker" not in router and "capcut_add_sticker" not in tools
      and "capcut_add_sticker" not in rd(sec3c) and "Never a sticker or an emoji, as a graphic or in a text layer" in rd(sec3c)
      and all("**No sticker or emoji added, ever**" in rd(SKD / n / "SKILL.md") for n in ("awl-plan-video", "awl-postprocess"))
      and "no sticker or emoji is placed in the project" in rd(SKD / "awl-qc" / "SKILL.md")
      and "**No sticker or emoji added, ever**" in rd(LIB / "reference" / "text-and-format" / "010_1_text-policy-depends-on-the-mode.md"),
      "no sticker or emoji, ever (the user, 2026-11-03): in the router's item 6, the text policy, the plan, X8, the CapCut sections and QC; the sticker "
      "tool is neither allowed nor named")

finish()
