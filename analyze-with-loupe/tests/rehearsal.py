"""Golden-path rehearsal of a pipeline (the functionality baseline, Phase A7): the same script runs on a temp copy of any library of this
shape, so a difference between two pipelines shows. Fake references, fake assets, a stubbed speech-to-text, a Loupe server in this
process with a fake keeper, no Higgsfield call, nothing written under the real library.

Usage: python tests/rehearsal.py --library <lib dir> [--library <lib dir> --home-env AWL_HOME --skill-prefix awl- --command <router.md>] [--out <snapshot.json>] [--loupe <loupe dir>]
(the defaults are this library; a library of the same shape under other names is rehearsed with the same script, so a difference between two shows)
Exit 1 when a step the contract needs fails. The snapshot holds, per step, the command, the exit code and the JSON keys of the last line."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--library", default=str(Path(__file__).resolve().parent.parent))
ap.add_argument("--home-env", default="AWL_HOME")
ap.add_argument("--skill-prefix", default="awl-")
ap.add_argument("--command", default=str(Path.home() / ".claude" / "commands" / "analyze-with-loupe.md"))
ap.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "rehearsal-snapshot.json"))
ap.add_argument("--loupe", default=str(Path.home() / ".claude" / "loupe"))
ap.add_argument("--keep", action="store_true")
A = ap.parse_args()
LIB = Path(A.library).resolve()
TK = next(p for p in (LIB / "scripts").glob("*.py") if p.name not in ("docs_tool.py", "check_all.py"))
PY = sys.executable
SKILLS = Path.home() / ".claude" / "skills"
TMP = Path(tempfile.mkdtemp(prefix="rehearsal-"))
HOME = TMP / "home"
RESULTS, FAILS = [], []


def ffm(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, capture_output=True)


def clip(path: Path, seconds=3.0, size="720x1280", flash=None, audio=True, colour="0x2b4c7e"):
    path.parent.mkdir(parents=True, exist_ok=True)
    vf = "drawbox=x=iw*0.55:y=ih*0.55:w=iw*0.12:h=ih*0.3:color=white@1:t=fill,drawbox=x=iw*0.2:y=ih*0.6:w=iw*0.3:h=ih*0.2:color=gray@1:t=fill"
    if flash:
        vf += f",drawbox=x=0:y=0:w=iw:h=ih:color=white@1:t=fill:enable='between(t,{flash[0]},{flash[1]})'"
    src = ["-f", "lavfi", "-i", f"color=c={colour}:s={size}:r=30:d={seconds}"]
    if audio:
        src += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={seconds}", "-c:a", "aac", "-shortest"]
    ffm(*src, "-vf", vf, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", str(path))
    return path


def step(name, *args, env=None, ok=True, timeout=600, must=True):
    """Run one toolkit command; record (name, exit code, JSON keys of the last line); a failed must-step is a contract failure."""
    e = {**os.environ, A.home_env: str(HOME), "PYTHONIOENCODING": "utf-8", "LOUPE_DATA": str(TMP / "loupe-data"), "ATG" + "_HOME": str(TMP / "lib-b-empty"),
         "ATP" + "_TRANSCRIBE_STUB": "1", "AWL_TRANSCRIBE_STUB": "1", "ATP" + "_KEEPER_SYNC_WAIT": "2", "AWL_KEEPER_SYNC_WAIT": "2", **(env or {})}
    for other in ("ATP" + "_HOME", "ATG" + "_HOME"):        # the other libraries of the same shape see an empty folder
        if other != A.home_env:
            e[other] = str(TMP / ("empty-" + other[:3].lower()))
    e[A.home_env] = str(HOME)
    cmd = [PY, "-X", "utf8", str(TK), *[str(a) for a in args]]
    t0 = time.time()
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, timeout=timeout)
    last = (cp.stdout.strip().splitlines() or [""])[-1]
    try:
        js = json.loads(last)
    except ValueError:
        js = None
    good = (ok is None or (cp.returncode == 0) == ok) and js is not None
    RESULTS.append({"step": name, "cmd": " ".join(str(a) for a in args)[:300], "code": cp.returncode, "keys": sorted(js) if isinstance(js, dict) else None,
                    "ok_field": js.get("ok") if isinstance(js, dict) else None, "ms": int((time.time() - t0) * 1000), "passed": good})
    print(("PASS  " if good else "FAIL  ") + f"{name:34} code {cp.returncode} {int((time.time() - t0) * 1000):6} ms keys={len(js) if isinstance(js, dict) else '-'}")
    if not good:
        FAILS.append(name + (" (must)" if must else ""))
        print("      " + (cp.stderr.strip().splitlines() or [last])[-1][:300])
    return js if isinstance(js, dict) else {}


# ---- the temp library copy: everything but runs, backups and tests; runs_root inside the copy
HOME.mkdir(parents=True)
for item in LIB.iterdir():
    if item.name in ("runs", "_backups", "tests", "__pycache__"):
        continue
    (shutil.copytree if item.is_dir() else shutil.copy2)(item, HOME / item.name)
cfg = json.loads((HOME / "config.json").read_text(encoding="utf-8"))
cfg["runs_root"] = str(HOME / "runs")
(HOME / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
(HOME / "runs").mkdir()
TK = HOME / "scripts" / TK.name           # the copy's own toolkit, so a home-relative path inside it resolves inside the copy

# ---- fixtures
refs = TMP / "refs"
clip(refs / "ref-a.mp4", 3.0, flash=(1.0, 1.2))
clip(refs / "ref-b.mp4", 4.0, colour="0x7e2b4c")
examples = TMP / "examples"
clip(examples / "mine.mp4", 2.0, colour="0x4c7e2b")
assets = TMP / "assets"
assets.mkdir()
ffm("-f", "lavfi", "-i", "color=c=0x1aa0a0:s=400x900:d=0.1", "-frames:v", "1", str(assets / "can-front.png"))
(assets / "product_properties.txt").write_text("slim can, 355 ml, 15.5 cm tall, 5.3 cm wide\n", encoding="utf-8")
(assets / "brand-rules.txt").write_text("No competitor brands. The can is always sealed on screen.\n", encoding="utf-8")
sources = TMP / "sources"
clip(sources / "edit-me.mp4", 3.0, colour="0x404040")
gen = TMP / "gen"
clip(gen / "a1.mp4", 3.0, size="544x960", audio=False)
clip(gen / "a2.mp4", 2.0, size="544x960", audio=False, colour="0x224422")
ffm("-f", "lavfi", "-i", "color=c=0xc8beaf:s=720x1280:d=0.1", "-frames:v", "1", str(TMP / "texture.png"))
HAS_PH = '"placeholder"' in TK.read_text(encoding="utf-8")      # the placement marker; a library without it skips these steps

# ---- the skills: every hand-off transition and every "Read now" path
skills = sorted(d for d in SKILLS.glob(A.skill_prefix + "*") if d.is_dir())
cmd_text = Path(A.command).read_text(encoding="utf-8")
transitions, readnow_missing, next_missing = [], [], []
for d in skills:
    txt = (d / "SKILL.md").read_text(encoding="utf-8")
    for m in re.finditer(r"set ((?:stage|video|next_skill|next_step)=[^`\n]+)", txt):
        pairs = dict(p.split("=", 1) for p in m.group(1).split() if "=" in p)
        if "next_skill" in pairs and not (SKILLS / pairs["next_skill"]).is_dir():
            next_missing.append((d.name, pairs["next_skill"]))
        transitions.append((d.name, pairs))
    for m in re.finditer(r"`([A-Z]{3}/[^`\s]+)`", txt):
        rel = m.group(1).split("/", 1)[1]
        if m.group(1).startswith("RUN/"):
            continue
        if not (LIB / rel).exists() and "<" not in rel and "NN" not in rel:
            readnow_missing.append((d.name, m.group(1)))
print(f"skills {len(skills)}; transitions {len(transitions)}; next_skill unresolved {next_missing}; paths unresolved {len(readnow_missing)}")
for x in readnow_missing[:10]:
    print("   unresolved", x)
if next_missing or readnow_missing:
    FAILS.append("skills-resolve")

# ---- Loupe in this process with a fake keeper
sys.path.insert(0, A.loupe)
os.environ["LOUPE_DATA"] = str(TMP / "loupe-data")
os.environ["ATG" + "_HOME"] = str(TMP / "lib-b-empty")
os.environ[A.home_env] = str(HOME)
from loupe_app import core, misses, qc, server  # noqa: E402


def fake_claude(prompt, sid, resume, model, timeout=150):
    if prompt.startswith("LIBRARY ("):
        return {"result": "ready", "total_cost_usd": 0.0}
    if "PLANNING question" in prompt:
        return {"result": json.dumps({"hints": [], "none_reason": "nothing in the library matches a beat"}), "total_cost_usd": 0.0}
    return {"result": json.dumps({"relevant": [{"id": "S1", "why": "same mechanism", "check": "the can's height across the cut", "wrong_pattern": "the can shrinks"}],
                                  "advice": "compare the can against the laptop", "not_covered": ""}), "total_cost_usd": 0.0}


qc._run_claude = fake_claude
httpd = server.ThreadingHTTPServer((core.HOST, 0), server.Handler)
httpd.daemon_threads = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
core.ensure_dirs()
(TMP / "loupe-data" / "server.json").write_text(json.dumps({"port": httpd.server_port, "pid": os.getpid()}), encoding="utf-8")
for name, scopes in (("pipeline", ["flags:write", "flags:read", "runs:read"]), ("qc", ["qc:read", "flags:read"])):
    core.key_write_file(name, core.key_create(name, scopes)["key"])

# ======================================================================= Analyze Mode, Recreate then Create
for submode in ("recreate", "create", "free-refs", "free-none"):
    sub = "free" if submode.startswith("free") else submode
    print(f"\n--- Analyze / {submode} ---")
    nr = ["new-run", "--mode", "analyze", "--assets", assets, "--examples", examples, "--slug", submode]
    if submode != "free-none":
        nr[3:3] = ["--source", refs]
    js = step(f"{submode}:new-run", *nr)
    run = Path(js.get("run_dir") or js.get("run") or "")
    if not run.is_dir():
        FAILS.append(f"{submode}:new-run (no run_dir)")
        continue
    step(f"{submode}:state-start", "state", "--run", run.name, "set", "model=wan3_0_prime", "model_locked=true", f"analyze_submode={sub}", *(["free_references=" + ("no" if submode == "free-none" else "yes")] if sub == "free" else []), "audio_ingest=frames-only",
         "qc_fixes=ask", "stage=started", f"next_skill={A.skill_prefix}analyze-prepare")
    step(f"{submode}:effort", "effort", "--run", run.name, "--level", {"recreate": "medium", "create": "high", "free-refs": "xhigh", "free-none": "low"}[submode])
    step(f"{submode}:model-entry", "model-entry", "--id", "wan3_0_prime")
    step(f"{submode}:model-menu", "model-menu", "--mode", "analyze")
    step(f"{submode}:loupe-status", "loupe", "status")
    step(f"{submode}:loupe-ensure", "loupe", "ensure")
    if sub == "free":
        (run / "00-inventory").mkdir(exist_ok=True)
        (run / "00-inventory" / "requirement.md").write_text("# Requirement (the user's words)\n\nOne 8 s video: the can stands on the desk, a hand picks it up, the label faces the lens.\n", encoding="utf-8")
    if submode != "free-none":
        step(f"{submode}:inventory-refs", "inventory", "--run", run.name, "--as", "references", refs)
    step(f"{submode}:inventory-examples", "inventory", "--run", run.name, "--as", "examples", examples)
    step(f"{submode}:inventory-assets", "inventory", "--run", run.name, "--as", "assets", assets)
    step(f"{submode}:prep-assets", "prep-assets", "--run", run.name)
    if submode != "free-none":
        step(f"{submode}:prep-all-refs", "prep-all", "--run", run.name, "--no-ocr", "--jobs", "1")
    step(f"{submode}:prep-all-examples", "prep-all", "--run", run.name, "--set", "examples", "--no-ocr", "--jobs", "1")
    step(f"{submode}:doc-text", "doc-text", assets / "brand-rules.txt")
    step(f"{submode}:state-prepared", "state", "--run", run.name, "set", "stage=prepared", f"next_skill={A.skill_prefix}" + ("free-plan" if submode == "free-none" else "analyze-study"))
    st = step(f"{submode}:status-prepared", "status", "--run", run.name, "--no-loupe")
    (run / "20-analysis" / "cards").mkdir(parents=True, exist_ok=True)
    (run / "20-analysis" / "cards" / "V01.md").write_text("# V01\n- hook: [E] a can on a desk\n", encoding="utf-8")
    nxt = A.skill_prefix + {"recreate": "recreate-plan", "create": "create-plan"}.get(submode, "free-plan")
    if submode != "free-none":
        step(f"{submode}:state-analyzed", "state", "--run", run.name, "set", "stage=analyzed", "next_step=count")
        step(f"{submode}:state-counted", "state", "--run", run.name, "set", "stage=counted", "requested_videos=1", f"next_skill={nxt}")
    if submode == "recreate":
        m = step(f"{submode}:strip-inserts", "strip-inserts", "--video", refs / "ref-a.mp4", "--inserts", "1.0-1.2", "--out", run / "10-media" / "V01" / "own")
        step(f"{submode}:seams", "seams", "--video", refs / "ref-a.mp4", "--at", "1.0,1.2")
        step(f"{submode}:frames", "frames", refs / "ref-a.mp4", "--at", "0.5,1.5", "--out", run / "10-media" / "V01" / "targeted")
        if HAS_PH:
            step(f"{submode}:placeholder", "placeholder", "--render", assets / "can-front.png", "--video", refs / "ref-a.mp4", "--out", run / "10-media" / "V01" / "prepared" / "source-marked.mp4",
                 "--product-h-cm", "15.5", "--product-w-cm", "5.3", "--window", "0-1.5:400,1000,160", "--window", "1.5-3:420,1010,180", "--luma-ref", "40,40,120,120",
                 "--basis", "the box: 30 = 380 px at depth ratio 1", "--basis", "the panel: 25 = 320 px at depth ratio 1")
    elif submode == "create" and HAS_PH:
        step(f"{submode}:placeholder-image", "placeholder", "--render", assets / "can-front.png", "--image", TMP / "texture.png", "--out", run / "30-assets" / "guides" / "V01-marker.png",
             "--product-h-cm", "15.5", "--product-w-cm", "5.3", "--base-x", "360", "--base-y", "900", "--height", "150")
    step(f"{submode}:state-planned", "state", "--run", run.name, "set", "stage=planned", f"next_skill={A.skill_prefix}asset-plan", *(['videos_kind={"01":"create"}', "free_plan_confirmed=true", 'directions=["one 8 s video: the can picked up"]'] if sub == "free" else []))
    (run / "30-assets").mkdir(exist_ok=True)
    (run / "30-assets" / "asset-plan.md").write_text("| video 01 | V01 | A1 slim can | placement |\n", encoding="utf-8")
    step(f"{submode}:state-asset-planned", "state", "--run", run.name, "set", "stage=asset_planned", f"next_skill={A.skill_prefix}analyze-produce",
         'asset_plan=[{"video":"01","ref":"V01","asset":"A1"}]')
    # per-video scaffolding the main session writes before spawning
    (run / "40-briefs").mkdir(exist_ok=True)
    (run / "50-requests").mkdir(exist_ok=True)
    (run / "40-briefs" / "video-01-plan.md").write_text("# plan video 01 (V01)\nBeat 1: the can stands on the desk.\nBeat 2: a cut; the can is still there.\n", encoding="utf-8")
    (run / "50-requests" / "video-01-pattern.md").write_text("# pattern card video 01\nShot 1: subject, action, setting.\nJudge's template: no template: Loupe unavailable.\n", encoding="utf-8")
    (run / "40-briefs" / "video-01-judge-brief.md").write_text("Video 01 of a rehearsal: the slim can stands on the desk; the goal is its true size.\n", encoding="utf-8")
    (run / "40-briefs" / "video-01-musts.md").write_text("- Keep the camera still.\n", encoding="utf-8")
    (run / "50-requests" / "video-01-request.json").write_text(json.dumps({"params": {"model": "wan3_0_prime", "prompt": "The can stands on the desk. Keep the camera still.", "aspect_ratio": "9:16", "resolution": "720p"}}), encoding="utf-8")
    (run / "40-briefs" / "video-01-brief.md").write_text("# brief video 01\n- request: 50-requests/video-01-request.json\n- credits: 20\n", encoding="utf-8")
    (run / "50-requests" / "agent-contract.md").write_text(f"# contract {run.name}\nRun: {run.name}\nLoupe: up\nAudio ingest: frames-only\nQC fixes: ask\n", encoding="utf-8")
    step(f"{submode}:prompt-template", "prompt-template", "--run", run.name, "--video", "01", "--structure-file", run / "50-requests" / "video-01-pattern.md",
         "--product", "slim can")
    step(f"{submode}:template-apply-draft", "template-apply", "--run", run.name, "--video", "01", "--use-draft")
    step(f"{submode}:plan-hints", "plan-hints", "--run", run.name, "--video", "01", "--beats", "Beat 1: the can stands on the desk.\nBeat 2: a cut.", "--product", "slim can")
    step(f"{submode}:scale", "scale", "--product-cm", "15.5", "--product-px", "100-300", "--ref-cm", "30", "--ref-px", "50-450")
    step(f"{submode}:lint-run", "lint-run", "--run", run.name)
    step(f"{submode}:state-producing", "state", "--run", run.name, "set", "stage=producing", f"next_skill={A.skill_prefix}analyze-produce", "loupe=up",
         'higgsfield={"folder_id":"f1","project_id":"p1"}', 'assets.uploads={"A1":"media-1"}', "credits_start=1000")
    step(f"{submode}:status-producing", "status", "--run", run.name, "--no-loupe")
    # the production agent's steps: ledger, post-processing, qc, consult, record
    lg = step(f"{submode}:ledger-begin", "ledger", "begin", "--run", run.name, "--video", "01", "--attempt", "1", "--request", run / "50-requests" / "video-01-request.json")
    fp = lg.get("fingerprint") or (lg.get("entry") or {}).get("fingerprint") or ""
    step(f"{submode}:ledger-submitted", "ledger", "set", "--run", run.name, "--fingerprint", fp, "--status", "submitted", "--job", "job-1")
    step(f"{submode}:ledger-completed", "ledger", "set", "--run", run.name, "--fingerprint", fp, "--status", "completed", "--job", "job-1")
    step(f"{submode}:ledger-show", "ledger", "show", "--run", run.name)
    out = run / "60-outputs" / "video-01" / "a1"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gen / "a1.mp4", out / "raw.mp4")
    step(f"{submode}:conform", "conform", "--video", out / "raw.mp4", "--out", out / "conformed.mp4")
    step(f"{submode}:trim", "trim", "--video", out / "conformed.mp4", "--start", "0.1", "--end", "2.9", "--out", out / "trimmed.mp4")
    step(f"{submode}:restore-audio", "restore-audio", "--generated", out / "trimmed.mp4", "--source", refs / "ref-a.mp4", "--out", out / "final.mp4")
    step(f"{submode}:sync-check", "sync-check", "--source", refs / "ref-a.mp4", "--output", out / "final.mp4", "--out", out / "sync", ok=None, must=False)
    step(f"{submode}:last-frame", "last-frame", "--video", out / "final.mp4", "--out", out / "last.png")
    step(f"{submode}:concat", "concat", "--clips", out / "trimmed.mp4", gen / "a2.mp4", "--seams", "cut", "--out", out / "joined.mp4")
    step(f"{submode}:qc", "qc", "--video", out / "final.mp4", "--out", out / "qc", "--mode", "analyze", "--allowed-text", "SLIM CAN", "--dense", "cut:0.9-1.3", "--no-ocr")
    step(f"{submode}:qc-brief", "qc-brief", "--run", run.name, "--video", "01", "--product", "slim can", "--kinds", "scale-size")
    step(f"{submode}:qc-consult", "qc-consult", "--run", run.name, "--video", "01", "--attempt", "a1", "--question", "the can looks smaller after the cut", "--kinds", "scale-size", "--product-details", "slim 355 ml can", "--checkpoint", "cut 0.9-1.3")
    step(f"{submode}:caught-flag-add", "caught-flag", "add", "--run", run.name, "--video", "01", "--attempt", "a1", "--title", "rehearsal flag", "--kind", "other", "--model", "wan3_0_prime", "--mode", "analyze", "--no-thumbs", "--no-facts", "--response", "none given", "--trigger", "rehearsal", "--tags", "unknown-trigger")
    step(f"{submode}:caught-flag-list", "caught-flag", "list", "--run", run.name)
    (out / "spec.json").write_text(json.dumps({"events": [{"start": 0.2, "end": 1.0, "text": "SLIM CAN"}]}), encoding="utf-8")
    step(f"{submode}:captions", "captions", "--video", out / "final.mp4", "--out", out / "captioned.mp4", "--spec", out / "spec.json")
    step(f"{submode}:capcut-name", "capcut-name", "--video", "01")
    (run / "60-outputs" / "video-01" / "result.json").write_text(json.dumps({"video": "01", "status": "done", "final": str(out / "final.mp4")}), encoding="utf-8")
    (run / "deliverables").mkdir(exist_ok=True)
    (run / "deliverables" / "README.md").write_text("| 01 | wan3_0_prime | done |\n", encoding="utf-8")
    step(f"{submode}:state-produced", "state", "--run", run.name, "set", "stage=produced", f"next_skill={A.skill_prefix}wrapup", 'videos=[{"video":"01","status":"done"}]')
    step(f"{submode}:cost-report", "cost-report", "--run", run.name)
    step(f"{submode}:status-produced", "status", "--run", run.name, "--no-loupe")
    step(f"{submode}:caught-flag-reconcile", "caught-flag", "reconcile", "--run", run.name)
    step(f"{submode}:state-done", "state", "--run", run.name, "set", "stage=done")
    step(f"{submode}:doctor", "doctor", "--run", run.name, "--no-loupe", "--no-docs")

# ======================================================================= Edit Mode
print("\n--- Edit ---")
js = step("edit:new-run", "new-run", "--mode", "edit", "--source", sources / "edit-me.mp4", "--slug", "edit")
run = Path(js.get("run_dir") or "")
if run.is_dir():
    step("edit:state-start", "state", "--run", run.name, "set", "model=wan3_0_prime", "model_locked=true", "audio_ingest=frames-only", "stage=started", f"next_skill={A.skill_prefix}edit", "loupe=up")
    step("edit:effort", "effort", "--run", run.name, "--level", "max")
    step("edit:inventory-sources", "inventory", "--run", run.name, "--as", "sources", sources / "edit-me.mp4")
    step("edit:inventory-assets", "inventory", "--run", run.name, "--as", "assets", "--scope", "video-01", assets)
    step("edit:prep-assets", "prep-assets", "--run", run.name, "--scope", "video-01")
    step("edit:prep-all", "prep-all", "--run", run.name, "--no-ocr", "--jobs", "1")
    step("edit:split-audio", "split-audio", "--run", run.name, sources / "edit-me.mp4")
    if HAS_PH:
        step("edit:placeholder", "placeholder", "--render", assets / "can-front.png", "--video", sources / "edit-me.mp4", "--out", run / "10-media" / "V01" / "prepared" / "source-marked.mp4",
             "--product-h-cm", "15.5", "--product-w-cm", "5.3", "--base-x", "360", "--base-y", "1000", "--height", "160", "--sample", "300,1100,400,1200")
    step("edit:audio-profile", "audio-profile", "--audio", sources / "edit-me.mp4", "--out", run / "10-media" / "audio-profile")
    step("edit:state-editing", "state", "--run", run.name, "set", "stage=editing", "video=01", f"next_skill={A.skill_prefix}edit")
    (run / "50-requests").mkdir(exist_ok=True)
    (run / "50-requests" / "video-01-request.json").write_text(json.dumps({"params": {"model": "wan3_0_prime", "prompt": "Replace the tub with the can."}}), encoding="utf-8")
    lg = step("edit:ledger-begin", "ledger", "begin", "--run", run.name, "--video", "01", "--attempt", "1", "--request", run / "50-requests" / "video-01-request.json")
    fp = lg.get("fingerprint") or ""
    step("edit:ledger-completed", "ledger", "set", "--run", run.name, "--fingerprint", fp, "--status", "completed", "--job", "job-9")
    out = run / "60-outputs" / "video-01" / "a1"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gen / "a1.mp4", out / "raw.mp4")
    step("edit:conform", "conform", "--video", out / "raw.mp4", "--out", out / "conformed.mp4")
    step("edit:restore-audio", "restore-audio", "--generated", out / "conformed.mp4", "--source", sources / "edit-me.mp4", "--out", out / "final.mp4")
    step("edit:sync-check", "sync-check", "--source", sources / "edit-me.mp4", "--output", out / "final.mp4", "--out", out / "sync", ok=None, must=False)
    step("edit:qc", "qc", "--video", out / "final.mp4", "--out", out / "qc", "--mode", "edit", "--no-ocr")
    step("edit:finalize", "finalize", "--run", run.name, "--video", "01", "--file", out / "final.mp4", "--original", sources / "edit-me.mp4")
    step("edit:state-edited", "state", "--run", run.name, "set", "stage=edited", f"next_skill={A.skill_prefix}wrapup", 'videos=[{"video":"01","status":"done"}]')
    step("edit:status", "status", "--run", run.name, "--no-loupe")
else:
    FAILS.append("edit:new-run (no run_dir)")

# ---- utilities both modes cite
step("util:prep-image", "prep-image", assets / "can-front.png", "--out", TMP / "prep-image" / "can.png")
step("util:clean", "clean", "--video", gen / "a1.mp4", "--out", TMP / "clean.mp4", "--crop", "0,0,1,0.9")
step("util:state-get-missing", "state", "--run", "20260101-000000-none", "get", ok=False, must=False)

snap = {"library": str(LIB), "toolkit": TK.name, "skills": [d.name for d in skills], "transitions": transitions, "readnow_missing": readnow_missing,
        "next_missing": next_missing, "steps": RESULTS, "fails": FAILS}
Path(A.out).write_text(json.dumps(snap, indent=1, default=str), encoding="utf-8")
passed = sum(1 for r in RESULTS if r["passed"])
print(f"\n{passed}/{len(RESULTS)} steps passed; contract failures: {FAILS or 'none'}; snapshot {A.out}; temp {TMP}")
if not A.keep:
    shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
