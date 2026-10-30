"""The Loupe coupling of the toolkit against a real Loupe server started in this process on a temp data folder, with the keeper
replaced by a fake (no model call, no credits): loupe ensure (and its bounded wait), qc-brief, qc-consult (saved answer, needs_unmet
rule, --note), plan-hints (saved hints), caught-flag add/set/reconcile and ledger --flagged. Loupe's code is used read-only; its real
data folder is never opened (LOUPE_DATA points at the temp folder)."""
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import HOME, check, finish, make_clip, t, temp_library  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="awl-loupe-"))
DATA = TMP / "loupe-data"
home = temp_library("lp")
os.environ["LOUPE_DATA"] = str(DATA)
os.environ["AWL_HOME"] = str(home)
os.environ["ATG_HOME"] = str(TMP / "atg-empty")
LOUPE = Path(os.environ.get("LOUPE_HOME") or HOME / "loupe")
sys.path.insert(0, str(LOUPE))
from loupe_app import core, misses, qc, server  # noqa: E402

# --- a library of one sample: a miss and its right version from two synthetic clips of a fake run of the temp library
run = home / "runs" / "20261001-000000-07"
a1 = make_clip(run / "60-outputs" / "video-03" / "a1" / "raw.mp4", seconds=3.0, flash=None, audio=False, size="360x640")
a2 = make_clip(run / "60-outputs" / "video-03" / "a2" / "raw.mp4", seconds=3.0, flash=(1.0, 1.2), audio=False, size="360x640")
(run / "50-requests").mkdir(parents=True, exist_ok=True)
(run / "40-briefs").mkdir(exist_ok=True)
(run / "state.json").write_text(json.dumps({"run_id": run.name, "mode": "analyze", "analyze_submode": "recreate", "model": "wan3_0_prime", "stage": "producing",
                                             "submissions": [{"video": "03", "lane": "03", "attempt": 1, "fingerprint": "fp1", "status": "failed", "flagged": True, "job_id": "job-111",
                                                              "request_file": str(run / "50-requests" / "video-03-request.json"), "history": [{"at": "2026-10-14T10:00:00+02:00", "to": "failed", "note": "moderation"}]}]}), encoding="utf-8")
(run / "50-requests" / "video-03-request.json").write_text(json.dumps({"params": {"model": "wan3_0_prime", "prompt": "Show the can on the desk. Keep the camera still."}}), encoding="utf-8")
m = misses.create({"run": run.name, "video": "03", "title": "the can shrinks after the cut", "model": "wan3_0_prime", "kinds": [], "wrong_path": str(a1), "fixed_path": str(a2)}, "test")
mo = misses.add_moment(m["id"], {"frames": [{"src": "wrong", "role": "wrong", "t": 1.0}, {"src": "fixed", "role": "right", "t": 1.0}], "details": "the can is small here"}, "test")
SID = f"S{mo['moment_id']}"
misses.update(m["id"], {"wrong_prompt": "PROMPT-WRONG the can on the desk.", "fixed_prompt": "PROMPT-FIXED the can on the desk, as tall as the mug beside it.", "prompt_note": "the height was stated against the mug"}, "test")

# --- the fake keeper: a boot that can be slow (to test the bounded wait), then JSON answers by question kind
calls = []
SLOW = {"boot_s": 0.0}
PIM = {"tpl_text": "", "tpl": None, "qc": None}     # the judge's product images in a template answer and in a QC answer (none until a test sets them)


def fake_claude(prompt, sid, resume, model, timeout=150):
    calls.append(prompt)
    if "TEMPLATE REQUEST" in prompt:                      # step 1 of a template request: the judge names the samples whose prompts it needs
        return {"result": json.dumps({"read": [SID, "S999"]}), "total_cost_usd": 0.0}
    if "Step 2 of the template request" in prompt and PIM["tpl_text"]:      # a template answer that names the product images
        return {"result": json.dumps({"template": PIM["tpl_text"], "basis": [{"id": SID, "worked": "two views of the carton", "failed": "one view", "where": "shot 1"}],
                                      "notes": "", "changes": [], "not_covered": "", "product_images": PIM["tpl"] or []}), "total_cost_usd": 0.0}
    if "Step 2 of the template request" in prompt:
        return {"result": json.dumps({"template": "TEMPLATE-MARK Shot 1: the slim can stands on the desk, as tall as the mug beside it. [SLOT: the can's upload tag]",
                                      "basis": [{"id": SID, "worked": "the height stated against the mug", "failed": "no size stated", "where": "shot 1"}],
                                      "notes": "keep the mug line", "changes": [{"what": "beat 2's hard cut", "why": "the can shrank after a cut", "id": SID}],
                                      "not_covered": ""}), "total_cost_usd": 0.0}
    if "rests on samples whose prompts" in prompt:    # the round that hands the judge the prompts of the samples it cites: the first answer stays
        return {"result": "ready", "total_cost_usd": 0.0}
    if prompt.startswith("LIBRARY ("):
        time.sleep(SLOW["boot_s"])
        return {"result": "ready", "total_cost_usd": 0.0}
    if "PLANNING question" in prompt:
        ans = {"hints": [{"id": SID, "trigger": "the can is set down after a cut", "right_outcome": "the can keeps its size across the cut",
                          "lever": "restate the size against the laptop at that beat", "caveat": "not for a hand-held can", "confidence": "high", "model_independent": False}],
               "none_reason": ""}
        if "The prompt writer answers" not in prompt:       # the first planning ask: the keeper also asks the writer something only the plan can answer
            ans["needs"] = [{"kind": "ask_agent", "question": "is the can on the same desk after the cut?", "why": "the beats do not say where it stands after the cut"}]
        return {"result": json.dumps(ans), "total_cost_usd": 0.0}
    if "The QC agent adds" in prompt:
        return {"result": json.dumps({"relevant": [{"id": SID, "why": "same mechanism", "check": "the can's height before and after the cut", "wrong_pattern": "the can shrinks"}],
                                        "advice": "compare the can against the laptop", "not_covered": ""}), "total_cost_usd": 0.0}
    if "QC question" in prompt:
        return {"result": json.dumps({"relevant": [{"id": SID, "why": "same mechanism", "check": "the can's height before and after the cut", "wrong_pattern": "the can shrinks"}],
                                        "advice": "compare the can against the laptop", "not_covered": "no sample shows the can carried through a doorway",
                                        "flags": [{"id": SID, "what": "FLAG-MARK the right frame's prompt box holds one text", "effect": "the cause rests on one prompt"},
                                                  {"id": "S999", "what": "a sample that does not exist"}],
                                        "cause": "CAUSE-MARK shot 1 states no size" if "The prompt this video was generated from" in prompt else "",
                                        "template_fix": "the slim can as tall as the mug" if "The prompt this video was generated from" in prompt else "",
                                        "needs": [{"kind": "ask_agent", "question": "does the can leave the frame?", "why": "I cannot see the last second"}],
                                        **({"product_images": PIM["qc"]} if PIM["qc"] else {})}), "total_cost_usd": 0.0}
    return {"result": "ready", "total_cost_usd": 0.0}


qc._run_claude = fake_claude
read_calls = []


def fake_extract(s, model):            # the picture reader, replaced too: a reading that says it opened the picture
    read_calls.append(s["id"])
    return {"reading": {"marked": "READ-MARKED the arrow points at the can after the cut", "right_version": "READ-RIGHT the can as tall as the laptop's screen", "product_and_scene": "p",
                        "frames_seen": [{"frame": "WRONG 0:01.00", "seen": "a small can"}]}, "cost": 0.0, "turns": 3, "images_read": True}


qc._extract_one = fake_extract

# --- a Loupe server on a free port, with the keys the toolkit reads from LOUPE_DATA/keys
httpd = server.ThreadingHTTPServer((core.HOST, 0), server.Handler)
httpd.daemon_threads = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
core.ensure_dirs()
(DATA / "server.json").write_text(json.dumps({"port": httpd.server_port, "pid": os.getpid()}), encoding="utf-8")
for name, scopes in (("pipeline", ["flags:write", "flags:read", "runs:read"]), ("qc", ["qc:read", "flags:read"])):
    core.key_write_file(name, core.key_create(name, scopes)["key"])
ENV = {"AWL_HOME": str(home), "LOUPE_DATA": str(DATA), "ATG_HOME": str(TMP / "atg-empty")}
print("loupe on port", httpd.server_port, "data", DATA)

# --- loupe ensure: library size and keeper state; a slow boot is bounded and reported as syncing, and the first consult still waits for it
js, _, _ = t("loupe", "status", env=ENV)
check(js.get("running") is True, "loupe status sees the test server")
SLOW["boot_s"] = 4.0
t0 = time.time()
js, _, _ = t("loupe", "ensure", env={**ENV, "AWL_KEEPER_SYNC_WAIT": "1"})
el = time.time() - t0
check(js.get("ok") and js.get("library_size") == 1 and js["keeper"]["state"] == "syncing" and el < 3.5, f"loupe ensure waits at most AWL_KEEPER_SYNC_WAIT and reports keeper.state syncing ({el:.1f} s)")
for _ in range(100):                   # the run start also started reading the unread sample's picture in the background
    if (DATA / "keeper" / "understood" / f"{SID}.json").is_file():
        break
    time.sleep(0.1)
check(read_calls == [SID], f"a run start (loupe ensure) has Loupe read the sample that has no reading of its picture yet, once, in the background ({read_calls})")
js, _, _ = t("qc-brief", "--run", run.name, "--video", "03", "--product", "slim can", env=ENV)
check(js.get("mode") == "brief" and js["library_size"] == 1 and js["samples"][0]["id"] == SID, "qc-brief returns the matching sample with no model call")
vdir3 = run / "60-outputs" / "video-03"
check((vdir3 / "qc-brief.json").is_file() and not (vdir3 / "qc-consult.json").exists() and "prompts_files" not in js
      and ("prompts_rule" not in js or "no keeper read or judged" in js["prompts_rule"])
      and all(k in js["samples"][0] for k in ("run", "video", "t_wrong", "prompt_roles", "prompt_sides", "reading", "reading_path")),
      "qc-brief keeps its answer as qc-brief.json (never as the video's consult), writes no prompts files, says no keeper judged a prompt, "
      "and gives each sample its origin, its prompt boxes and what the collector saw")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--kinds", "scale-size", "--product-details", "slim 355 ml can",
             "--checkpoint", "cut 1.0-1.2", env=ENV)
check(js.get("mode") == "keeper" and js["relevant"][0]["id"] == SID and js["relevant"][0]["composite_path"], "qc-consult reaches the keeper after the boot finished (the lock serialised it) and names the sample's composite")
check(len([c for c in calls if c.startswith("LIBRARY (")]) == 1, "the keeper was booted exactly once (the bounded ensure did not make the consult boot it again)")
check(js.get("needs_unmet") and js["needs_unmet"][0]["kind"] == "ask_agent" and "--note" in js.get("unmet_rule", ""), "what only the QC agent can answer comes back as needs_unmet with the --note rule")
rel0 = js["relevant"][0]
check(rel0.get("reading_path", "").endswith(f"{SID}.json") and (rel0.get("reading") or {}).get("marked", "").startswith("READ-MARKED") and "reading_rule" in js
      and "no verdict" in js["reading_rule"], "a relevant sample carries what the collector saw in its picture (two short fields and the path of the whole collection), "
      "with the rule to view the picture first and that the judgement is not the collector's")
check(js.get("library_read", {}).get("understood") == 1 and js["library_read"]["not_read"] == [] and "not_read_rule" not in js, "the answer says the keeper holds the whole library from its pictures")
check(js.get("not_covered", "").startswith("no sample shows") and "keeper_gaps" in js.get("gaps_rule", ""), "what the library does not cover comes with the rule to write it as keeper_gaps for the wrap-up")
saved = run / "60-outputs" / "video-03" / "qc-consult.json"
check(saved.is_file() and json.loads(saved.read_text(encoding="utf-8"))["relevant"][0]["id"] == SID, "the answer is saved as 60-outputs/video-NN/qc-consult.json")
check(js.get("flags") == [{"id": SID, "what": "FLAG-MARK the right frame's prompt box holds one text", "effect": "the cause rests on one prompt"}]
      and "keeper_gaps" in js.get("flags_rule", ""), "the judge's flags on a sample's record reach the QC agent (a flag on a sample that does not exist is dropped) with the rule to report them")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--note", "the can stays in frame to the end", env=ENV)
asked = lambda: [c for c in calls if "rests on samples whose prompts" not in c][-1]      # noqa: E731  (the last question, not the prompts round)
check(js.get("mode") == "keeper" and not js.get("needs_unmet") and "The QC agent adds" in asked(), "a second ask with --note reaches the keeper with the agent's words and nothing stays unmet")
SLOW["boot_s"] = 0.0
js, _, _ = t("loupe", "ensure", env=ENV)
check(js["keeper"]["state"] == "in_sync", "a current keeper is left alone by loupe ensure (no model call)")
js, _, _ = t("status", "--run", run.name, env=ENV)
lp = js.get("loupe") or {}
check(lp.get("running") is True and "error" not in lp and (lp.get("keeper") or {}).get("in_sync") is True and ((lp.get("keeper") or {}).get("understanding") or {}).get("understood") == 1,
      "status sees Loupe running and reads the keeper's state, with how many samples it holds from their pictures")

# --- plan-hints: the first request's sparse text-only hints, saved beside the plan
js, _, _ = t("plan-hints", "--run", run.name, "--video", "03", "--beats", "Beat 1: he sets the can on the desk.\nBeat 2: a cut; the can is still there.", "--product", "slim can",
             "--product-details", "slim 355 ml can, upright", env=ENV)
check(js.get("mode") == "keeper" and len(js["hints"]) == 1 and js["hints"][0]["id"] == SID and "rules" in js, "plan-hints returns the keeper's hint with the writer's rules")
check(js.get("needs_unmet") and js["needs_unmet"][0]["kind"] == "ask_agent" and "--note" in js.get("unmet_rule", "") and "held_back_why" in js,
      "what only the prompt writer can answer comes back from plan-hints as needs_unmet with the --note rule, and held_back_why is passed on")
check(js["hints"][0].get("reading_path", "").endswith(f"{SID}.json") and "reading_rule" in js, "a hint carries the path of its sample's reading and the rule to read it only when the trigger match is unclear")
js2, _, _ = t("plan-hints", "--run", run.name, "--video", "03", "--beats", "Beat 1: he sets the can on the desk.\nBeat 2: a cut; the can is still there.", "--product", "slim can",
              "--note", "yes, the same desk, the same spot after the cut", env=ENV)
check(js2.get("mode") == "keeper" and not js2.get("needs_unmet") and "The prompt writer answers" in asked() and "the same desk" in asked(),
      "a second plan-hints with --note reaches the keeper as the writer's answer from its plan, and nothing stays unmet")
check((run / "40-briefs" / "video-03-hints.json").is_file(), "the hints are saved as 40-briefs/video-NN-hints.json")
check(js["hints"][0].get("prompts") == "pair" and js["hints"][0].get("prompt_note", "").startswith("the height") and "wrong_prompt" not in js["hints"][0] and "prompts_files" in js.get("prompts_rule", "")
      and js.get("prompts_judged") == [SID] and "PROMPT-WRONG" in (Path(js.get("prompts_files", {}).get(SID, "")).read_text(encoding="utf-8") if js.get("prompts_files", {}).get(SID) else ""),
      "a hint whose sample keeps the prompts of both boxes carries the marker and the note, the judge read both before hinting, and both are written for the agent, never in the line")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--note", "the can stays in frame", env=ENV)
check(js["relevant"][0].get("prompts") == "pair" and "wrong_prompt" not in js["relevant"][0] and "prompts_files" in js.get("prompts_rule", "") and js.get("prompts_judged") == [SID]
      and Path(js.get("prompts_files", {}).get(SID, "-")).is_file(), "a relevant sample with saved prompts: the judge read both before its answer was final and both are written for the QC agent, never in the line")
rounds = [c for c in calls if "rests on samples whose prompts" in c]
check(rounds and "PROMPT-WRONG the can on the desk." in rounds[-1] and "PROMPT-FIXED the can on the desk, as tall as the mug beside it." in rounds[-1]
      and "no other session has read or judged them" in rounds[-1], "the prompts round hands the judge both prompts whole from Loupe's record")

# --- X2: the judge's template, briefed by the agent; then QC carries the prompt used, the template and the brief
(run / "50-requests" / "video-03-pattern.md").write_text("STRUCTURE-MARK Shot 1: subject, action, setting. Shot 2: ...", encoding="utf-8")
(run / "40-briefs" / "video-03-judge-brief.md").write_text("BRIEF-MARK video 03: he sets the slim can on the desk; the goal is the can's true size after the cut. "
                                                            + "The slim can stays upright on the desk in every shot. " * 600 + "BRIEF-END-MARK", encoding="utf-8")
(run / "40-briefs" / "video-03-musts.md").write_text("- Keep the camera still.\n", encoding="utf-8")
n0 = len(calls)
js, _, _ = t("prompt-template", "--run", run.name, "--video", "03", "--brief-file", str(run / "40-briefs" / "video-03-judge-brief.md"),
             "--structure-file", str(run / "50-requests" / "video-03-pattern.md"), "--product", "slim can", "--product-details", "slim 355 ml can, upright", env=ENV)
new = calls[n0:]
step1 = next((c for c in new if "TEMPLATE REQUEST" in c), "")
step2 = next((c for c in new if "Step 2 of the template request" in c), "")
check(js.get("mode") == "keeper" and js.get("template", "").startswith("TEMPLATE-MARK") and [b["id"] for b in js.get("basis", [])] == [SID] and js.get("read") == [SID]
      and js.get("changes") and "rules" in js, "prompt-template returns the judge's template, its basis, the samples it read, its changes and the rules to craft from it")
check("Wan 3.0 Prime" in step1 and js.get("video_model") == "wan3_0_prime", "the template request names the generation video model with its entry of the model index")
check("BRIEF-END-MARK" in step1 and "brief_cut" not in js, "a brief of over 30000 characters reaches the judge whole (no video generation prompt is cut)")
check("Show the can on the desk. Keep the camera still." in step1 and "Lines the prompt must carry, word for word" in step1 and "- Keep the camera still." in step1
      and "5000 characters" in step1 and js.get("musts") == 1, "the judge gets the whole checked brief: the draft request's prompt, its must-carry lines and the service's limit")
check("BRIEF-MARK" in step1 and "STRUCTURE-MARK" in step1 and "PROMPT-WRONG the can on the desk." in step2 and "PROMPT-FIXED" in step2 and "Not sent: S999" in step2
      and not any("rests on samples whose prompts" in c for c in new), "the judge gets the agent's brief and the model's structure, then both prompts of the samples it chose, whole (none sent twice)")
tj, tm = run / "40-briefs" / "video-03-template.json", run / "40-briefs" / "video-03-template.md"
check(tj.is_file() and json.loads(tj.read_text(encoding="utf-8")).get("brief", "").startswith("BRIEF-MARK") and tm.is_file() and tm.read_text(encoding="utf-8").startswith("TEMPLATE-MARK")
      and Path(js.get("prompts_files", {}).get(SID, "-")).is_file(), "the template is saved with the brief, as JSON and as text, and the basis sample's prompts are written for the agent")
_, code, _ = t("prompt-template", "--run", run.name, "--video", "07", env=ENV, ok=False)
check(code == 2, "prompt-template without a brief (no --brief, no judge brief file) stops (code 2)")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--attempt", "a1", "--question", "the can is smaller than the mug after the cut", env=ENV)
q = [c for c in calls if "QC question" in c][-1]
check("Show the can on the desk. Keep the camera still." in q and "TEMPLATE-MARK" in q and "BRIEF-MARK" in q
      and js.get("evidence_sent", {}).get("request_prompt") == "video-03-request.json" and js["evidence_sent"].get("template") == "video-03-template.json"
      and js["evidence_sent"].get("video_model") == "wan3_0_prime" and "The video model and parameters of that request" in q and "Wan 3.0 Prime" in q,
      "after generation the QC consult carries the prompt the video was generated from, the judge's template and the brief, and says which files")
check(js.get("cause", "").startswith("CAUSE-MARK") and js.get("template_fix") and "result.json judge" in js.get("judge_rule", ""),
      "the judge's answer names the cause in the prompt or template and the part rewritten, with the rule to record them for the user's review")
js, code, _ = t("template-apply", "--run", run.name, "--video", "03", "--slot", "the can's upload tag=Image 1", env=ENV)
rq3 = json.loads((run / "50-requests" / "video-03-request.json").read_text(encoding="utf-8"))
check(code == 0 and rq3["params"]["prompt"].startswith("TEMPLATE-MARK") and "[SLOT" not in rq3["params"]["prompt"] and "Image 1" in rq3["params"]["prompt"]
      and js.get("musts_missing") == ["Keep the camera still."], "template-apply puts the judge's prompt in the request word for word and reports the must-carry line it lacks")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can is smaller again", env=ENV)
q = [c for c in calls if "QC question" in c][-1]
check("TEMPLATE-MARK" in q and "(the same as the prompt this video was generated from, its slots filled)" in q and js.get("evidence_sent", {}).get("request_prompt") == "video-03-request.json",
      "the QC consult then sends the judge's prompt as the prompt used (the kept draft is never taken for it) and says the template is the same")
js, _, _ = t("sample-prompts", "--id", SID, "--run", run.name, env=ENV)
pf = run / "40-briefs" / "samples" / f"{SID}-prompts.md"
ptxt = pf.read_text(encoding="utf-8") if pf.is_file() else ""
check(js.get("ok") and js.get("prompts") == "pair" and js["chars"]["wrong"] > 0 and pf.is_file() and "PROMPT-WRONG the can" in ptxt and "PROMPT-FIXED the can" in ptxt and "the height was stated" in ptxt
      and f"--- {SID}-P1 (sample {SID}, generation miss R{m['id']}) · the flawed version's prompt box: the prompts of the generations the frames called WRONG come from, which generated the flawed version ---" in ptxt
      and f"--- {SID}-P2 (sample {SID}, generation miss R{m['id']}) · the correct version's prompt box: the prompts of the generations the frames called RIGHT come from, which generated the correct version ---" in ptxt
      and "the flawed version's prompt and the correct version's prompt" in ptxt
      and f"--- end of {SID}-P1 (sample {SID}) ---" in ptxt and f"  {SID} · Frame 1 WRONG 0:01.00, Video A" in ptxt and f"=== SAMPLE {SID} · generation miss R{m['id']}" in ptxt
      and f"=== END OF SAMPLE {SID} ===" in ptxt and f"made by {SID}-P1" in ptxt and f"made by {SID}-P2" in ptxt
      and "wrong here (what is wrong at the marked place of Frame 1 (WRONG, 0:01.00), called WRONG): the can is small here" in ptxt, "sample-prompts writes both prompts whole and the admin's note to 40-briefs/samples/<id>-prompts.md")
check("wrong_prompt" not in js and "diff" not in js and "prompt_change" not in js, "the JSON line carries sizes and the path, never the prompt texts or a diff (the agent reads the file and judges)")
js, _, _ = t("sample-prompts", "--id", "S999", "--run", run.name, env=ENV)
check(js.get("mode") == "unavailable" and js.get("prompts") == "", "an unknown sample id answers unavailable, no prompts, no failure")

# --- the flag record: ledger --flagged, caught-flag add, set, reconcile
js, _, _ = t("ledger", "set", "--run", run.name, "--job", "job-111", "--status", "failed", "--flagged", "--note", "moderation block", env=ENV)
check(js.get("ok") and js["entry"]["flagged"] is True and "caught-flag add" in js.get("reminder", ""), "ledger set --flagged marks the row and reminds the agent to record the flag")
js, _, _ = t("caught-flag", "reconcile", "--run", run.name, env=ENV)
check(js.get("ok") and len(js["flagged_unrecorded"]) == 1, "reconcile lists the flagged row that has no entry yet")
js, _, _ = t("caught-flag", "add", "--run", run.name, "--video", "03", "--attempt", "a1", "--title", "moderation on the desk shot", "--kind", "moderation-block", "--tool", "generate_video",
             "--stage", "submit", "--response", "content policy", "--trigger", "[I] the prompt's wording", "--tags", "prompt-wording", "--no-thumbs", "--no-facts", env=ENV)
cf = js.get("id")
check(js.get("ok") and str(cf).startswith("CF-") and "request" in js.get("attached", []), f"caught-flag add records the flag in Loupe with the request attached ({cf})")
js, _, _ = t("caught-flag", "reconcile", "--run", run.name, env=ENV)
check(js["flagged_unrecorded"] == [] and js["flagged_recorded"][0]["entry"] == cf, "after the entry exists, reconcile reports the row as recorded")
js, _, _ = t("caught-flag", "set", "--id", cf, "--status", "cleared", "--cleared-prompt", str(run / "50-requests" / "video-03-request.json"), "--cleared-job", "job-222", env=ENV)
check(js.get("ok") and js.get("status") == "cleared", "caught-flag set clears the flag once an accepted request is named")
js, _, _ = t("caught-flag", "list", "--run", run.name[:8], env=ENV)
check(js.get("count") == 1, "caught-flag list filters by a run name prefix as text")

# --- a take made of two generations: the prompts file gives the prompt of each generation this sample's frames come from, under the seconds it made
def _two_gens(cut):
    misses.update(m["id"], {"wrong_segments": [{"clip": "c1", "attempt": 1, "request": "video-03-c1-request.json", "t_from": 0, "t_to": cut, "prompt": "SEG-ONE the can on the desk."},
                                               {"clip": "c2", "attempt": 1, "request": "video-03-c2-request.json", "t_from": cut, "t_to": 3.0, "prompt": "SEG-TWO the lights go off."}]}, "test")
    js2, _, _ = t("sample-prompts", "--id", SID, "--run", run.name, env=ENV)
    return js2, (Path(js2.get("saved", "-")).read_text(encoding="utf-8") if js2.get("saved") else "")


js, ptxt2 = _two_gens(1.5)
check(js.get("generations", {}).get("wrong") == 2 and "the flawed version's prompt box holds generations of a take made of 2" in ptxt2
      and f"--- {SID}-P1 (sample {SID}, generation miss R{m['id']}) · the flawed version's prompt box: the prompts of the generations the frames called WRONG come from" in ptxt2
      and ("This is a prompt of the flawed version (the generation the frames called WRONG come from): it generated second 0 to second 1.5 of Video A "
           "(generation 1 of 2 · clip c1 · video-03-c1-request.json), and made Frame 1 (WRONG, 0:01.00) of this sample.") in ptxt2
      and f"made by {SID}-P1 (the flawed version's prompt box)" in ptxt2 and "SEG-ONE" in ptxt2 and "SEG-TWO" not in ptxt2,
      "a take made of two generations: the prompts file gives the prompt of the generation the sample's WRONG frame comes from, under the seconds it made")
js, ptxt3 = _two_gens(0.5)
check("it generated second 0.5 to second 3 of Video A (generation 2 of 2 · clip c2 · video-03-c2-request.json), and made Frame 1 (WRONG, 0:01.00) of this sample." in ptxt3
      and "SEG-TWO" in ptxt3 and "SEG-ONE" not in ptxt3,
      "when that frame comes from the second generation, only the second generation's prompt")
misses.update(m["id"], {"wrong_segments": [], "wrong_prompt": "PROMPT-WRONG the can on the desk."}, "test")

# --- Example frames only (the user, 2026-10-28 and 2026-10-29): an Examples sample takes all its frames from one video and has one prompt box, that
#     video's; the prompts file gives that prompt alone, named an example prompt, never the flawed or the correct one; Loupe refuses Examples from two videos
mo_ex = misses.add_moment(m["id"], {"frames": [{"src": "wrong", "role": "example", "t": 1.0}, {"src": "wrong", "role": "example", "t": 1.5}], "details": "kept as an example"}, "test")
SID_EX = mo_ex["id"] if isinstance(mo_ex, dict) and "id" in mo_ex else f"S{mo_ex['moment_id']}"
js, _, _ = t("sample-prompts", "--id", SID_EX, "--run", run.name, env=ENV)
ptx = Path(js.get("saved", "-")).read_text(encoding="utf-8") if js.get("saved") else ""
check(js.get("prompt_roles") == {"wrong": "example", "fixed": "example"} and js.get("prompt_sides") == ["wrong"]
      and f"--- {SID_EX}-P1 (sample {SID_EX}, generation miss R{m['id']}) · the example prompt box of Video A, this Examples sample's one box: the prompts of the generations of Video A its Example frames come from, an example" in ptx
      and "of Video B" not in ptx and "flawed version's prompt box" not in ptx and "This sample's frames are all Examples" in ptx
      and "the example prompt of Video A (an Examples sample has one prompt box" in ptx,
      "a sample of Example frames only: the prompts file gives the one box of its one video, named an example prompt, never the flawed or the correct version's")
try:
    misses.add_moment(m["id"], {"frames": [{"src": "wrong", "role": "example", "t": 1.0}, {"src": "fixed", "role": "example", "t": 1.0}]}, "test")
    two_refused = False
except ValueError as e:
    two_refused = "one video" in str(e)
check(two_refused, "Loupe refuses an Examples sample whose frames come from two videos")
misses.delete_moment(mo_ex["moment_id"], "test") if hasattr(misses, "delete_moment") else None

# --- the coupling in step with Loupe (2026-10-28): a consult may outlast the old 190 s; reconcile lists the flag captures and only counts the
#     upload answers kept for hf-put; a capture is found at any age; a queued flag stays findable after Loupe's ingest
import re as _re  # noqa: E402
from http.server import BaseHTTPRequestHandler, HTTPServer  # noqa: E402
from loupe_app import flags as lflags  # noqa: E402
src = Path(os.environ.get("AWL_UNDER_TEST") or (HOME / "analyze-with-loupe" / "scripts" / "awl.py")).read_text(encoding="utf-8")
m = _re.search(r'CONSULT_TIMEOUT = float\(os\.environ\.get\("AWL_CONSULT_TIMEOUT"\) or (\d+)\)', src)
check(bool(m) and int(m.group(1)) >= qc.LOCK_WAIT + 6 * qc.KEEPER_CALL_TIMEOUT and src.count("timeout=CONSULT_TIMEOUT") == 3,
      "qc-consult, plan-hints and prompt-template wait as long as Loupe's own limits allow (its lock wait plus six keeper calls)")
old_cap = lflags.capture_add({"tool": "mcp__higgsfield__generate_video", "job": "job-old-777", "run": run.name, "summary": "signals: moderation, blocked | ids: job-old-777",
                              "signals": ["moderation", "blocked"], "response": "{\"status\": \"nsfw\", \"job\": \"job-old-777\"}"})
for k in range(230):
    lflags.capture_add({"tool": "mcp__higgsfield__media_upload", "job": "", "summary": "signals: upload", "signals": ["upload"],
                        "response": json.dumps({"upload_url": f"https://up.example/slot/{k}", "media_id": f"m{k}"})})
js, _, _ = t("caught-flag", "reconcile", "--run", run.name, env=ENV)
check(old_cap in [c["id"] for c in js.get("unclaimed_captures", [])] and js.get("unclaimed_upload_answers", 0) >= 230,
      f"reconcile lists a flag capture behind {js.get('unclaimed_upload_answers')} newer upload answers, which it only counts")
js, _, _ = t("caught-flag", "add", "--run", run.name, "--video", "03", "--attempt", "a2", "--title", "an old capture attached", "--kind", "moderation-block",
             "--tool", "generate_video", "--stage", "job", "--response", "nsfw", "--trigger", "[I] the desk shot", "--tags", "prompt-wording",
             "--capture", str(old_cap), "--no-thumbs", "--no-facts", env=ENV)
cf2 = js.get("id")
check(((lflags.get(cf2) or {}).get("captured") or {}).get("id") == old_cap, f"caught-flag add --capture attaches a capture that has 230 newer ones ({cf2})")


class Stub(BaseHTTPRequestHandler):
    """A Loupe that answers its health and listings but fails every write with a 500."""
    def _send(self, code, d):
        b = json.dumps(d).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(200, {"ok": True, "app": "loupe", "entries": [], "captures": []})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._send(500, {"ok": False, "error": "stub: internal error"})

    def log_message(self, *a):
        pass


stub = HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
sj = DATA / "server.json"
real_sj = sj.read_text(encoding="utf-8")
sj.write_text(json.dumps({"port": stub.server_port, "pid": os.getpid()}), encoding="utf-8")
try:
    js, _, _ = t("caught-flag", "add", "--run", run.name, "--video", "03", "--attempt", "a1", "--title", "queued while Loupe failed", "--kind", "other",
                 "--tool", "generate_video", "--stage", "submit", "--response", "none given", "--trigger", "[I] unknown", "--tags", "unknown-trigger",
                 "--no-thumbs", "--no-facts", env=ENV)
finally:
    sj.write_text(real_sj, encoding="utf-8")
    stub.shutdown()
q = str(js.get("id", ""))
queued = [json.loads(f.read_text(encoding="utf-8"))["doc"] for f in (DATA / "outbox").glob("*.json")]
doc_q = next((d for d in queued if d.get("id") == q), {})
check(q.startswith("CF-Q") and any(q in str(n.get("note")) and "answered 500" in str(n.get("note")) for n in doc_q.get("log") or []),
      f"a flag Loupe answers 500 to is queued as {q}, its log noting the provisional id and what Loupe answered")
lflags.ingest_outbox()
js, code, _ = t("caught-flag", "set", "--id", q, "--status", "cleared", "--cleared-prompt", str(run / "50-requests" / "video-03-request.json"), "--cleared-job", "job-333", env=ENV, ok=False)
same = [e for e in lflags.search("queued while loupe failed")[1] if e.get("title") == "queued while Loupe failed"]
check(code == 0 and len(same) == 1 and same[0]["status"] == "cleared" and same[0]["id"] != q and js.get("id") == same[0]["id"] and js.get("queued_as") == q,
      f"after Loupe recorded it as {same[0]['id'] if same else '?'}, `caught-flag set --id {q}` still finds it (one flag, now cleared)"
      + ("" if code == 0 and len(same) == 1 and same[0]["status"] == "cleared" else f" [code {code}, {len(same)} flag(s), status {[e.get('status') for e in same]}, answer {json.dumps(js)[:300]}]"))

# --- product images (the admin, 2026-10-30): the judge decides which of the client's images of the product a request carries and how many; each input
#     records the client's original it was made from, named by its file name alone (never its folder), on the way to the judge and back
import importlib.util as _ilu  # noqa: E402
from loupe_app import runs as lruns  # noqa: E402
from t00_common import AWL  # noqa: E402
assets = TMP / "client" / "assets"
inv5 = [{"id": "A47", "path": str(assets / "people" / "face-47.jpg")}, {"id": "A82", "path": str(assets / "carton" / "Carton-Front.png")},
        {"id": "A83", "path": str(assets / "carton" / "Carton-Back.png")}, {"id": "A273", "path": str(assets / "photos" / "IMG_6917.jpg")}]
(run / "30-assets" / "project").mkdir(parents=True, exist_ok=True)
(run / "30-assets" / "project" / "asset-inventory.json").write_text(json.dumps({"items": inv5}), encoding="utf-8")
(run / "30-assets" / "registry.md").write_text("| id | what | assets |\n|---|---|---|\n| P-CARTON | the product, a carton | A82, A83, A273 |\n", encoding="utf-8")
req5 = {"params": {"model": "wan3_0_prime", "prompt": "DRAFT-5 the man of Image 1 holds the carton. The printed label exactly as in Image 2. Keep the camera still.",
                   "medias": [{"role": "image_references", "value": "<X3: image1-character-face.jpg>", "label": "Image 1 = image1-character-face",
                               "source": {"original": inv5[0]["path"], "asset_id": "A47", "prepared": "cropped to the face", "kind": "character"}},
                              {"role": "image_references", "value": "<X3: image2-product-front.png>", "label": "Image 2 = image2-product-front",
                               "source": {"original": inv5[1]["path"], "asset_id": "A82", "prepared": "padded to 9:16 on white", "kind": "product"}}]}}
(run / "50-requests" / "video-05-request.json").write_text(json.dumps(req5), encoding="utf-8")
(run / "40-briefs" / "video-05-judge-brief.md").write_text("BRIEF-5 video 05: he holds the carton to the camera; the goal is the label read true.", encoding="utf-8")
(run / "40-briefs" / "video-05-musts.md").write_text("- The printed label exactly as in Image 2.\n- Keep the camera still.\n", encoding="utf-8")
PIM.update(tpl_text="TPL-5 the man of Image 1 holds the carton. The printed label exactly as in Image 2. Image 3 shows the back of the carton. Keep the camera still.",
           tpl=[{"asset": "A82", "file": "client/assets/carton/Carton-Front.png", "prepare": "", "why": f"{SID}: one view left the thinness wrong"},
                {"file": "carton\\Carton-Back.png", "prepare": "padded to 9:16 on white like the front", "why": f"{SID}: a second view held it"}])
n0 = len(calls)
js, _, _ = t("prompt-template", "--run", run.name, "--video", "05", "--product", "carton", env=ENV)
step1 = next((c for c in calls[n0:] if "TEMPLATE REQUEST" in c), "")
check("- Image 1 (image_references; character; made from A47 · face-47.jpg, prepared: cropped to the face)" in step1
      and "- Image 2 (image_references; a product image; made from A82 · Carton-Front.png, prepared: padded to 9:16 on white)" in step1
      and "Product images (yours to decide, see PRODUCT IMAGES): Image 2 (A82 · Carton-Front.png); they are the last image inputs" in step1
      and "The client's images of P-CARTON (the run's registry row and asset inventory): A82 Carton-Front.png, A83 Carton-Back.png, A273 IMG_6917.jpg" in step1
      and str(assets) not in step1 and "carton/Carton-Front.png" not in step1,
      "the template request lists each input with the client's original it was made from, by its file name alone (never a folder), the draft's product "
      "images and the client's images of that product")
pim5 = js.get("product_images") or []
check([(x.get("asset"), x.get("file"), x.get("prepare")) for x in pim5] == [("A82", "Carton-Front.png", ""), ("", "Carton-Back.png", "padded to 9:16 on white like the front")]
      and "template-apply" in js.get("product_images_rule", "") and "upload it at X3 before X5" in js.get("product_images_rule", ""),
      f"the judge's product images come back from Loupe in its order, named by file name alone (the folders it wrote are cut), with the rule to apply them ({pim5})")
t5 = json.loads((run / "40-briefs" / "video-05-template.json").read_text(encoding="utf-8"))
check(t5.get("product_images") == pim5, "the judge's product images are kept in the saved template")
js, code, _ = t("template-apply", "--run", run.name, "--video", "05", env=ENV)
rq5 = json.loads((run / "50-requests" / "video-05-request.json").read_text(encoding="utf-8"))
med5 = [x for x in rq5["params"]["medias"] if x.get("role") == "image_references"]
check(code == 0 and rq5["params"]["prompt"].startswith("TPL-5") and len(med5) == 3 and med5[:2] == req5["params"]["medias"]
      and med5[2].get("value") == "<X3: prepare Carton-Back.png for Image 3>"
      and med5[2].get("source") == {"original": inv5[2]["path"], "asset_id": "A83", "prepared": "padded to 9:16 on white like the front", "kind": "product"}
      and [a["asset"] for a in (js.get("product_images") or {}).get("added", [])] == ["A83"] and js.get("musts_missing") == []
      and js.get("prompt_names_images_beyond_the_inputs") == [] and (rq5.get("product_images") or {}).get("by") == "the judge (X4b)",
      "template-apply carries them into the request: the character and the front view keep Image 1 and 2; the back view, named by its file name alone, "
      "is found in the inventory (A83) and added as Image 3 with the source to prepare it from")
PIM.update(qc=[{"asset": "A82", "file": "Carton-Front.png", "prepare": "", "why": "kept"}, {"asset": "A83", "file": "Carton-Back.png", "prepare": "", "why": "kept"},
               {"asset": "A273", "file": "photos/IMG_6917.jpg", "prepare": "cropped to the carton", "why": f"{SID}: a real photo held the label"}])
js, _, _ = t("qc-consult", "--run", run.name, "--video", "05", "--question", "the label reads wrong in shot 2", env=ENV)
q5 = [c for c in calls if "QC question" in c][-1]
check("The inputs of that request (what each is and the client's original file it was made from) and its product images" in q5
      and "- Image 3 (image_references; a product image; made from A83 · Carton-Back.png, prepared: padded to 9:16 on white like the front)" in q5
      and "Product images (yours to decide, see PRODUCT IMAGES): Image 2 (A82 · Carton-Front.png), Image 3 (A83 · Carton-Back.png)" in q5
      and str(assets) not in q5 and js.get("evidence_sent", {}).get("request_inputs") == "video-05-request.json",
      "the QC judge is told which inputs the video was given, each with the client's original by its file name alone, and its product images")
saved5 = run / "60-outputs" / "video-05" / "qc-consult.json"
check([(x["asset"], x["file"]) for x in js.get("product_images") or []] == [("A82", "Carton-Front.png"), ("A83", "Carton-Back.png"), ("A273", "IMG_6917.jpg")]
      and "T product-images" in js.get("product_images_rule", "")
      and saved5.is_file() and json.loads(saved5.read_text(encoding="utf-8")).get("product_images") == js.get("product_images"),
      "a QC answer's product images for the regeneration reach the QC agent with the rule to apply them, and are saved with the answer")
r2p = run / "50-requests" / "video-05-a2-request.json"
r2p.write_text(json.dumps({**rq5, "params": {**rq5["params"], "prompt": rq5["params"]["prompt"] + " REGEN-MARK"}}), encoding="utf-8")
js, _, _ = t("product-images", "--run", run.name, "--video", "05", "--request", str(r2p), "--apply", env=ENV)
img2 = [x for x in json.loads(r2p.read_text(encoding="utf-8"))["params"]["medias"] if x.get("role") == "image_references"]
check(js.get("applied") and [a["image"] for a in js.get("added", [])] == ["Image 4"] and len(img2) == 4 and img2[:3] == med5
      and img2[3]["source"]["asset_id"] == "A273" and img2[3]["source"]["original"] == inv5[3]["path"] and img2[3]["value"] == "<X3: prepare IMG_6917.jpg for Image 4>"
      and r2p.with_name("video-05-a2-request.pre-product-images.json").is_file(),
      "product-images puts the QC judge's choice in the regeneration's request: the images its prompt names keep their numbers and the photo is added as Image 4")

reg_text = ("| id | type | role | files |\n|---|---|---|---|\n| NG-EF6-SPE | product | the carton | A44, A45 front-angled |\n"
            "| CH12 | character | the employee | A16 |\n| P-CARTON | the product, a carton | A82, A83, A273 |\n")
reg_keep = (run / "30-assets" / "registry.md").read_text(encoding="utf-8")
(run / "30-assets" / "registry.md").write_text(reg_text, encoding="utf-8")
_spec_r = _ilu.spec_from_file_location("awl_rows", AWL)
_awl_r = _ilu.module_from_spec(_spec_r)
_spec_r.loader.exec_module(_awl_r)
rows_l, rows_a = lruns._registry_product_rows(run), [(rid, ids) for rid, _row, ids in _awl_r._pi_registry_rows(run)]
(run / "30-assets" / "registry.md").write_text(reg_keep, encoding="utf-8")
rows_ok = rows_l == rows_a == [("NG-EF6-SPE", ["A44", "A45"]), ("P-CARTON", ["A82", "A83", "A273"])]
check(rows_ok, "Loupe and the toolkit find the same product rows in a registry of either form (an id starting with P-, a type cell that says product)"
      + ("" if rows_ok else f" {rows_l} {rows_a}"))
# Loupe (its records, the samples' PRODUCT IMAGES) and the toolkit (the judge's inputs, the plan) read an input's source by the same rules
_spec = _ilu.spec_from_file_location("awl_under_test", AWL)
_awl = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_awl)
l_inv, l_names = lruns._inventory(run)
a_inv, a_names = _awl._pi_inventory(run)
cases = [{"source": {"original": inv5[1]["path"], "asset_id": "A82", "prepared": "padded", "kind": "product"}},
         {"build": f"from {inv5[2]['path']} (A83): padded to 9:16 on white"},
         {"build": f"byte copy of {inv5[0]['path']} (A47) (the original bytes)"},
         {"meaning": "the carton's back view, A83"},
         {"label": "Image 2 = IMG_6917.jpg as given"},
         {"meaning": "A82 or A83"},
         {"meaning": "the man"},
         {"source": {"original": inv5[3]["path"]}},
         {"source": inv5[1]["path"], "prepare": "padded to 9:16 on white"},
         {"source_file": inv5[2]["path"], "prepare": "same preparation as Image 2"},
         {"from": inv5[3]["path"]},
         {"build": f"from {inv5[1]['path']} (A82, closed carton, flap shut): the carton upright, padded"},
         {"from": "A83", "label": "Image 3 = the back view"}]
pairs = [(lruns._source_of(c, "", {}, l_inv, l_names), _awl._pi_source(c, "", a_inv, a_names, set())) for c in cases]
check(lruns.BUILD_NOTE.pattern == _awl.PI_BUILD_NOTE.pattern and lruns.A_ID.pattern == _awl.PI_A_ID.pattern and all(lo == aw for lo, aw in pairs)
      and [lo.get("recorded", "") for lo, _aw in pairs] == ["source", "build", "build", "named", "named", "", "", "source", "source", "source", "source", "build", "named"]
      and [lo.get("asset_id") for lo, _aw in pairs[8:]] == ["A82", "A83", "A273", "A82", "A83"]
      and (pairs[8][0].get("prepared"), pairs[11][0].get("prepared")) == ("padded to 9:16 on white", "the carton upright, padded")
      and pairs[7][0].get("asset_id") == "A273" and pairs[2][0].get("prepared") == "a byte copy (the original bytes)",
      "Loupe and the toolkit read an input's source the same way: the source record, the client's file in source, source_file or from (the forms runs "
      "wrote before it), a build note (its asset id in its parenthetical), one asset id or one original file name named; "
      "two ids or none named is no record (never a guess)" + ("" if all(lo == aw for lo, aw in pairs) else f" {[p for p in pairs if p[0] != p[1]]}"))

httpd.shutdown()
finish()
