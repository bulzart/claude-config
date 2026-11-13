"""A stand-in for `claude -p ... --output-format stream-json` for tests/test_report.py: no network, no model, no cost.

It reads the prompt on stdin, "opens" the files the prompt lists (as Read tool calls in the stream), and answers with a report object. FAKE_CLAUDE_MODE picks what it does:
  ok              opens every listed file, answers with a valid report
  extra_fields    like ok, plus fields the brief does not ask for (highlights, rating, a score inside an entry): the checker must drop them
  strings         like ok, but text and lines are bare strings
  skip_first      the first call opens only half of the files, the next calls open all (a retry after "You did not open these files")
  never_open      always opens only the first two files
  no_open         answers without any tool call (num_turns 1) on the first call, opens everything afterwards
  bad_json        the answer is not a JSON object
  bad_json_once   the first answer is not JSON, the next is fine
  exit1           prints nothing, exits 1
  hang            sleeps FAKE_CLAUDE_SLEEP seconds (default 60) before answering
  slow            sleeps FAKE_CLAUDE_SLEEP seconds (default 1.5), then like ok
  rate_limit      a rate-limit event with status rejected and an error result
FAKE_CLAUDE_COUNT_FILE counts calls; FAKE_CLAUDE_ARGS_FILE gets the arguments and the head of the prompt (so a test can check the flags).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
prompt = sys.stdin.read()
n = 1
cf = os.environ.get("FAKE_CLAUDE_COUNT_FILE")
if cf:
    p = Path(cf)
    n = (int(p.read_text() or 0) + 1) if p.is_file() else 1
    p.write_text(str(n))
af = os.environ.get("FAKE_CLAUDE_ARGS_FILE")
if af:
    Path(af).write_text(json.dumps({"argv": sys.argv[1:], "prompt_head": prompt[:400], "has_role": "reporter" in prompt.lower(), "call": n, "cc_reporter": os.environ.get("CC_REPORTER")}))


def ev(o):
    print(json.dumps(o), flush=True)


paths = [ln.strip() for ln in prompt.splitlines() if ln.startswith("  ") and re.match(r"^[A-Za-z]:[\\/]", ln.strip())]
m = re.search(r"covers rec time ([0-9.]+) to ([0-9.]+) s", prompt)
r0 = float(m.group(1)) if m else 0.0
retry = "You did not open these files" in prompt or "not one JSON object" in prompt

ev({"type": "system", "subtype": "init"})
if mode == "exit1":
    sys.stderr.write("fake claude: exit 1\n")
    sys.exit(1)
if mode in ("hang", "slow"):
    time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "60" if mode == "hang" else "1.5")))
if mode == "rate_limit":
    ev({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}})
    ev({"type": "result", "subtype": "success", "is_error": True, "result": "You've hit your limit", "num_turns": 1, "total_cost_usd": 0.0})
    sys.exit(0)

if mode == "skip_first" and n == 1 and not retry:
    opens = paths[: max(1, len(paths) // 2)]
elif mode == "never_open":
    opens = paths[:2]
elif mode == "no_open" and n == 1 and not retry:
    opens = []
else:
    opens = paths
if opens:
    ev({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": x}} for x in opens]}})
    ev({"type": "user", "message": {"content": [{"type": "tool_result"} for _ in opens]}})

sheets = [x for x in paths if re.search(r"sheet-\d+\.jpg$", x)]
look = []
for i, s in enumerate(sheets):
    e = {"sheet": Path(s).stem, "rec_from": r0 + 22.5 * i, "rec_to": r0 + 22.5 * (i + 1), "shows": "full-screen picture with a counter at the top left", "changes": "no change",
         "text": [{"text": "FRAME %d" % i, "where": "top left", "cells": "1-30"}]}
    look.append(e)
rep = {"look": look, "sound": [{"rec_from": r0, "rec_to": r0 + 30, "what": "loudness steady around -30 dB"}],
       "speech": [{"rec_from": r0 + 1, "rec_to": r0 + 9, "about": "someone talks about a game", "lines": [{"rec": r0 + 2.5, "text": "hello chat"}]}],
       "chat": [], "seen_and_heard": [{"rec": r0 + 3, "what": "a counter reads 90", "evidence": ["sheet-01 cell 5"]}], "unclear": ["text in the corner too small to read"]}
if mode == "extra_fields":
    rep["highlights"] = [{"rec": r0 + 3, "why": "the best moment"}]
    rep["rating"] = 9
    rep["look"][0]["score"] = 10
if mode == "strings":
    rep["look"][0]["text"] = ["COUNTER 1"]
    rep["speech"][0]["lines"] = ["a bare line"]
result = json.dumps(rep)
if mode == "bad_json" or (mode == "bad_json_once" and n == 1 and not retry):
    result = "I looked at everything and it was a calm chunk."
text = result
ev({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
ev({"type": "result", "subtype": "success", "is_error": False, "result": result, "num_turns": 2 if opens else 1, "total_cost_usd": 0.0123, "duration_ms": 100})
