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


def fake_claude(prompt, sid, resume, model, timeout=150):
    calls.append(prompt)
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
                                        "needs": [{"kind": "ask_agent", "question": "does the can leave the frame?", "why": "I cannot see the last second"}]}), "total_cost_usd": 0.0}
    return {"result": "ready", "total_cost_usd": 0.0}


qc._run_claude = fake_claude
read_calls = []


def fake_extract(s, model):            # the picture reader, replaced too: a reading that says it opened the picture
    read_calls.append(s["id"])
    return {"reading": {"the_miss": "READ-MISS the can is smaller after the cut", "qc_check": "READ-CHECK compare its height with the laptop", "mechanism": "m",
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
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--kinds", "scale-size", "--product-details", "slim 355 ml can",
             "--checkpoint", "cut 1.0-1.2", env=ENV)
check(js.get("mode") == "keeper" and js["relevant"][0]["id"] == SID and js["relevant"][0]["composite_path"], "qc-consult reaches the keeper after the boot finished (the lock serialised it) and names the sample's composite")
check(len([c for c in calls if c.startswith("LIBRARY (")]) == 1, "the keeper was booted exactly once (the bounded ensure did not make the consult boot it again)")
check(js.get("needs_unmet") and js["needs_unmet"][0]["kind"] == "ask_agent" and "--note" in js.get("unmet_rule", ""), "what only the QC agent can answer comes back as needs_unmet with the --note rule")
rel0 = js["relevant"][0]
check(rel0.get("reading_path", "").endswith(f"{SID}.json") and (rel0.get("reading") or {}).get("the_miss", "").startswith("READ-MISS") and "reading_rule" in js,
      "a relevant sample carries the keeper's reading of its picture (two short fields and the path of the whole one) with the rule to view the picture first")
check(js.get("library_read", {}).get("understood") == 1 and js["library_read"]["not_read"] == [] and "not_read_rule" not in js, "the answer says the keeper holds the whole library from its pictures")
check(js.get("not_covered", "").startswith("no sample shows") and "keeper_gaps" in js.get("gaps_rule", ""), "what the library does not cover comes with the rule to write it as keeper_gaps for the wrap-up")
saved = run / "60-outputs" / "video-03" / "qc-consult.json"
check(saved.is_file() and json.loads(saved.read_text(encoding="utf-8"))["relevant"][0]["id"] == SID, "the answer is saved as 60-outputs/video-NN/qc-consult.json")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--note", "the can stays in frame to the end", env=ENV)
check(js.get("mode") == "keeper" and not js.get("needs_unmet") and "The QC agent adds" in calls[-1], "a second ask with --note reaches the keeper with the agent's words and nothing stays unmet")
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
check(js2.get("mode") == "keeper" and not js2.get("needs_unmet") and "The prompt writer answers" in calls[-1] and "the same desk" in calls[-1],
      "a second plan-hints with --note reaches the keeper as the writer's answer from its plan, and nothing stays unmet")
check((run / "40-briefs" / "video-03-hints.json").is_file(), "the hints are saved as 40-briefs/video-NN-hints.json")
check(js["hints"][0].get("prompts") == "pair" and js["hints"][0].get("prompt_note", "").startswith("the height") and "wrong_prompt" not in js["hints"][0] and "sample-prompts" in js.get("prompts_rule", ""),
      "a hint whose sample keeps the prompts of both takes carries the marker, the admin's note and the prompts rule, never the prompts")
js, _, _ = t("qc-consult", "--run", run.name, "--video", "03", "--question", "the can looks smaller after the cut", "--note", "the can stays in frame", env=ENV)
check(js["relevant"][0].get("prompts") == "pair" and "wrong_prompt" not in js["relevant"][0] and "sample-prompts" in js.get("prompts_rule", ""), "a relevant sample with saved prompts carries the marker and the prompts rule in the QC answer, never the prompts")
js, _, _ = t("sample-prompts", "--id", SID, "--run", run.name, env=ENV)
pf = run / "40-briefs" / "samples" / f"{SID}-prompts.md"
ptxt = pf.read_text(encoding="utf-8") if pf.is_file() else ""
check(js.get("ok") and js.get("prompts") == "pair" and js["chars"]["wrong"] > 0 and pf.is_file() and "PROMPT-WRONG the can" in ptxt and "PROMPT-FIXED the can" in ptxt and "the height was stated" in ptxt
      and "## Prompt of the wrong take" in ptxt and "## Prompt of the corrected take" in ptxt, "sample-prompts writes both prompts whole and the admin's note to 40-briefs/samples/<id>-prompts.md")
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

# --- the coupling in step with Loupe (2026-10-28): a consult may outlast the old 190 s; reconcile lists the flag captures and only counts the
#     upload answers kept for hf-put; a capture is found at any age; a queued flag stays findable after Loupe's ingest
import re as _re  # noqa: E402
from http.server import BaseHTTPRequestHandler, HTTPServer  # noqa: E402
from loupe_app import flags as lflags  # noqa: E402
src = Path(os.environ.get("AWL_UNDER_TEST") or (HOME / "analyze-with-loupe" / "scripts" / "awl.py")).read_text(encoding="utf-8")
m = _re.search(r'CONSULT_TIMEOUT = float\(os\.environ\.get\("AWL_CONSULT_TIMEOUT"\) or (\d+)\)', src)
check(bool(m) and int(m.group(1)) >= qc.LOCK_WAIT + 3 * 150 and src.count("timeout=CONSULT_TIMEOUT") == 2,
      "qc-consult and plan-hints wait as long as Loupe's own limits allow (its lock wait plus three keeper calls)")
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
check(code == 0 and len(same) == 1 and same[0]["status"] == "cleared" and same[0]["id"] != q,
      f"after Loupe recorded it as {same[0]['id'] if same else '?'}, `caught-flag set --id {q}` still finds it (one flag, now cleared)")

httpd.shutdown()
finish()
