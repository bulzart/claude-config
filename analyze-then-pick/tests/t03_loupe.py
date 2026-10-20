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

TMP = Path(tempfile.mkdtemp(prefix="atp-loupe-"))
DATA = TMP / "loupe-data"
home = temp_library("lp")
os.environ["LOUPE_DATA"] = str(DATA)
os.environ["ATP_HOME"] = str(home)
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

# --- the fake keeper: a boot that can be slow (to test the bounded wait), then JSON answers by question kind
calls = []
SLOW = {"boot_s": 0.0}


def fake_claude(prompt, sid, resume, model, timeout=150):
    calls.append(prompt)
    if prompt.startswith("LIBRARY ("):
        time.sleep(SLOW["boot_s"])
        return {"result": "ready", "total_cost_usd": 0.0}
    if "PLANNING question" in prompt:
        return {"result": json.dumps({"hints": [{"id": SID, "trigger": "the can is set down after a cut", "right_outcome": "the can keeps its size across the cut",
                                                   "lever": "restate the size against the laptop at that beat", "caveat": "not for a hand-held can", "confidence": "high", "model_independent": False}],
                                        "none_reason": ""}), "total_cost_usd": 0.0}
    if "The QC agent adds" in prompt:
        return {"result": json.dumps({"relevant": [{"id": SID, "why": "same mechanism", "check": "the can's height before and after the cut", "wrong_pattern": "the can shrinks"}],
                                        "advice": "compare the can against the laptop", "not_covered": ""}), "total_cost_usd": 0.0}
    if "QC question" in prompt:
        return {"result": json.dumps({"relevant": [{"id": SID, "why": "same mechanism", "check": "the can's height before and after the cut", "wrong_pattern": "the can shrinks"}],
                                        "advice": "compare the can against the laptop", "not_covered": "",
                                        "needs": [{"kind": "ask_agent", "question": "does the can leave the frame?", "why": "I cannot see the last second"}]}), "total_cost_usd": 0.0}
    return {"result": "ready", "total_cost_usd": 0.0}


qc._run_claude = fake_claude

# --- a Loupe server on a free port, with the keys the toolkit reads from LOUPE_DATA/keys
httpd = server.ThreadingHTTPServer((core.HOST, 0), server.Handler)
httpd.daemon_threads = True
threading.Thread(target=httpd.serve_forever, daemon=True).start()
core.ensure_dirs()
(DATA / "server.json").write_text(json.dumps({"port": httpd.server_port, "pid": os.getpid()}), encoding="utf-8")
for name, scopes in (("pipeline", ["flags:write", "flags:read", "runs:read"]), ("qc", ["qc:read", "flags:read"])):
    core.key_write_file(name, core.key_create(name, scopes)["key"])
ENV = {"ATP_HOME": str(home), "LOUPE_DATA": str(DATA), "ATG_HOME": str(TMP / "atg-empty")}
print("loupe on port", httpd.server_port, "data", DATA)

# --- loupe ensure: library size and keeper state; a slow boot is bounded and reported as syncing, and the first consult still waits for it
js, _, _ = t("loupe", "status", env=ENV)
check(js.get("running") is True, "loupe status sees the test server")
SLOW["boot_s"] = 4.0
t0 = time.time()
js, _, _ = t("loupe", "ensure", env={**ENV, "ATP_KEEPER_SYNC_WAIT": "1"})
el = time.time() - t0
check(js.get("ok") and js.get("library_size") == 1 and js["keeper"]["state"] == "syncing" and el < 3.5, f"loupe ensure waits at most ATP_KEEPER_SYNC_WAIT and reports keeper.state syncing ({el:.1f} s)")
js, _, _ = t("qc-brief", "--run", run.name, "--video", "03", "--product", "slim can", env=ENV)
check(js.get("mode") == "brief" and js["library_size"] == 1 and js["samples"][0]["id"] == SID, "qc-brief returns the matching sample with no model call")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--kinds", "scale-size", "--product-details", "slim 355 ml can",
             "--checkpoint", "cut 1.0-1.2", env=ENV)
check(js.get("mode") == "keeper" and js["relevant"][0]["id"] == SID and js["relevant"][0]["composite_path"], "qc-consult reaches the keeper after the boot finished (the lock serialised it) and names the sample's composite")
check(len([c for c in calls if c.startswith("LIBRARY (")]) == 1, "the keeper was booted exactly once (the bounded ensure did not make the consult boot it again)")
check(js.get("needs_unmet") and js["needs_unmet"][0]["kind"] == "ask_agent" and "--note" in js.get("unmet_rule", ""), "what only the QC agent can answer comes back as needs_unmet with the --note rule")
saved = run / "60-outputs" / "video-03" / "qc-consult.json"
check(saved.is_file() and json.loads(saved.read_text(encoding="utf-8"))["relevant"][0]["id"] == SID, "the answer is saved as 60-outputs/video-NN/qc-consult.json")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--note", "the can stays in frame to the end", env=ENV)
check(js.get("mode") == "keeper" and not js.get("needs_unmet") and "The QC agent adds" in calls[-1], "a second ask with --note reaches the keeper with the agent's words and nothing stays unmet")
SLOW["boot_s"] = 0.0
js, _, _ = t("loupe", "ensure", env=ENV)
check(js["keeper"]["state"] == "in_sync", "a current keeper is left alone by loupe ensure (no model call)")

# --- plan-hints: the first request's sparse text-only hints, saved beside the plan
js, _, _ = t("plan-hints", "--run", run.name, "--video", "03", "--beats", "Beat 1: he sets the can on the desk.\nBeat 2: a cut; the can is still there.", "--product", "slim can",
             "--product-details", "slim 355 ml can, upright", env=ENV)
check(js.get("mode") == "keeper" and len(js["hints"]) == 1 and js["hints"][0]["id"] == SID and "rules" in js, "plan-hints returns the keeper's hint with the writer's rules")
check((run / "40-briefs" / "video-03-hints.json").is_file(), "the hints are saved as 40-briefs/video-NN-hints.json")

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

httpd.shutdown()
finish()
