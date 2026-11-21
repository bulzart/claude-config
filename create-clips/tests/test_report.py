"""Test of the chunk reporter (scripts/cc_report.py) with a stand-in for `claude -p` (tests/fake_claude.py): no network, no model, no cost.

    python tests/test_report.py

Checks the flags of the headless session, that the files it really opened are read from its stream (not from what it claims), the whitelist (a verdict field never
survives), the retry when files were not opened or the answer was not JSON, failure and timeout and rate-limit handling, that a failed report never touches the chunk's
own status, stale detection, several sessions at once, `status`, `doctor`, and the watcher making a report after a real ingest (a 12 s chunk, no Whisper).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "scripts" / "cc.py"
PY = sys.executable
FAKE = HERE / "fake_claude.py"


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def cc(*args, env=None, timeout=600):
    e = dict(os.environ)
    e.update(env or {})
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, timeout=timeout)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    j = json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}
    j["_rc"] = cp.returncode
    return j


def make_chunk(run: Path, n: int, dur: float = 180.0, sheets: int = 3, rec_start: float = 0.0) -> str:
    cid = f"C{n:04d}"
    d = run / "10-media" / cid
    (d / "sheets").mkdir(parents=True, exist_ok=True)
    (d / "chunk.mp4").write_bytes(b"x")
    (d / "sheets" / "overview.jpg").write_bytes(b"jpg")
    for i in range(1, sheets + 1):
        (d / "sheets" / f"sheet-{i:02d}.jpg").write_bytes(b"jpg%d" % i)
    (d / "digest.json").write_text('{"chunk": "%s"}' % cid, encoding="utf-8")
    (d / "transcript.txt").write_text("[0:00:01.00-0:00:03.00] (C0001 +1.00) hello chat\n", encoding="utf-8")
    (d / "timeline.md").write_text("| rec | chunk+off | speech |\n", encoding="utf-8")
    (d / "audio-profile.json").write_text("{}", encoding="utf-8")
    (d / "chunk.json").write_text('{"stream": {"title": "t", "game": "g"}}', encoding="utf-8")
    rows_p = run / "00-inventory" / "chunks.json"
    rows = json.loads(rows_p.read_text(encoding="utf-8")) if rows_p.is_file() else []
    rows.append({"id": cid, "index": n, "rec_start_s": rec_start, "duration_s": dur, "status": "done", "frames": 240, "words": 3, "rec_base_s": rec_start, "stale_rec": False,
                 "stages": {s: True for s in ("move", "probe", "audio", "sheets", "transcript", "digest")}})
    rows_p.parent.mkdir(parents=True, exist_ok=True)
    rows_p.write_text(json.dumps(rows), encoding="utf-8")
    return cid


def row(run: Path, cid: str) -> dict:
    return next(r for r in json.loads((run / "00-inventory" / "chunks.json").read_text(encoding="utf-8")) if r["id"] == cid)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-report-test-"))
    try:
        shim = tmp / "fake-claude.cmd"
        shim.write_text(f'@echo off\r\n"{PY}" "{FAKE}" %*\r\n', encoding="utf-8")
        args_file, count_file = tmp / "args.json", tmp / "count.txt"
        base = {"CC_RUNS_ROOT": str(tmp / "runs"), "CC_CLAUDE_BIN": str(shim), "FAKE_CLAUDE_ARGS_FILE": str(args_file), "FAKE_CLAUDE_COUNT_FILE": str(count_file), "CC_NOTIFY": "0"}
        run = tmp / "runs" / "20261113-000000-rtest"
        (run / "00-inventory").mkdir(parents=True)
        (run / "state.json").write_text('{"schema":"cc/1","channel":"rtest","session":"20261113-000000-rtest"}', encoding="utf-8")
        cid = make_chunk(run, 1)
        sheet_n = 3

        r = cc("report", "--run", run, "--dry-run", env={**base, "FAKE_CLAUDE_MODE": "ok"})
        check(r.get("ok") and r["would_report"] == [cid] and r["model"] == "claude-haiku-5-5" and r["parallel"] == json.loads((HERE.parent / "config.json").read_text(encoding="utf-8"))["report"]["parallel"],
              "report --dry-run lists the chunk, the model and the configured number of sessions at once " + json.dumps(r)[:200])

        # ---- a good report
        count_file.unlink(missing_ok=True)
        r = cc("report", "--run", run, env={**base, "FAKE_CLAUDE_MODE": "ok"})
        check(r.get("ok") and r["reported"] == 1 and not r["failed"], "report: one chunk reported " + json.dumps(r)[:200])
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        mb = rep["made_by"]
        check(rep["schema"] == "cc-report/1" and rep["chunk"] == cid and rep["rec_from"] == 0.0 and rep["rec_to"] == 180.0, "report.json carries the schema, the chunk and its rec span")
        check(mb["model"] == "claude-haiku-5-5" and mb["effort"] == "high" and mb["attempts"] == 1 and not mb["not_opened"] and "overview.jpg" in mb["opened"] and f"sheet-0{sheet_n}.jpg" in mb["opened"],
              "made_by: Haiku at high effort, one attempt, every file opened (read from the stream) " + json.dumps(mb)[:240])
        check(len(rep["look"]) == sheet_n and rep["look"][1]["rec_from"] == 22.5 and rep["look"][0]["text"][0]["text"] == "FRAME 0", "one look entry per sheet with rec times and the text read")
        md = (run / "10-media" / cid / "report.md").read_text(encoding="utf-8")
        check("## What the pictures show" in md and "## Unclear" in md and "hello chat" in md and "Opened" in md, "report.md is the readable rendering")
        rw = row(run, cid)
        check(rw["status"] == "done" and rw["report"]["status"] == "done" and rw["report"]["attempts"] == 1, "the chunk row says report done and the chunk stays done")
        a = json.loads(args_file.read_text(encoding="utf-8"))
        av = a["argv"]
        flags_ok = all(f in av for f in ("-p", "--strict-mcp-config", "--no-session-persistence", "--verbose")) and av[av.index("--model") + 1] == "claude-haiku-5-5" \
            and av[av.index("--effort") + 1] == "high" and av[av.index("--tools") + 1] == "Read" and av[av.index("--allowedTools") + 1] == "Read" \
            and av[av.index("--setting-sources") + 1] == "project" and av[av.index("--output-format") + 1] == "stream-json"
        check(flags_ok, "the session runs Haiku at high effort with the Read tool only, no MCP, no saved conversation, the user's settings and hooks left out " + " ".join(av)[:200])
        check(a["has_role"] and a["cc_reporter"] == "1", "with a .cmd shim the brief travels on stdin (the command line stays short)")
        r = cc("report", "--run", run, env={**base, "FAKE_CLAUDE_MODE": "ok"})
        check(r.get("ok") and r["reported"] == 0 and r["already_current"] == [cid], "a current report is not made again")
        s = cc("status", "--run", run, env=base)
        check(s.get("ok") and s["reports"] == {"ok": 1, "missing": 0, "stale": 0, "failed": 0, "running": 0}, "status counts the report " + json.dumps(s.get("reports")))

        # ---- the whitelist: no verdict field survives
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "extra_fields"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and "highlights" not in rep and "rating" not in rep and "score" not in rep["look"][0] and rep["dropped"]["fields"] == ["highlights", "rating"] and rep["dropped"]["entry_fields"] >= 1,
              "fields the brief does not ask for (highlights, rating, a score) are dropped and counted, not stored " + json.dumps(rep["dropped"]))
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "strings"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and rep["look"][0]["text"][0]["text"] == "COUNTER 1" and rep["speech"][0]["lines"][0]["text"] == "a bare line", "bare strings where objects were asked for are kept as their text")

        # ---- retries
        count_file.unlink(missing_ok=True)
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "skip_first"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and rep["made_by"]["attempts"] == 2 and not rep["made_by"]["not_opened"] and abs(rep["made_by"]["cost_usd"] - 0.0246) < 1e-6,
              "files not opened: one retry names them, the second attempt opens everything (cost of both counted) " + json.dumps(rep["made_by"])[:200])
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "never_open"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and len(rep["made_by"]["not_opened"]) >= 2 and any("not opened" in w for w in rep["warnings"]) and "NOT opened" in (run / "10-media" / cid / "report.md").read_text(encoding="utf-8"),
              "a report whose files were still not all opened after the retry is kept and says so (made_by, warnings, report.md)")
        count_file.unlink(missing_ok=True)
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "no_open"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and rep["made_by"]["attempts"] == 2 and not rep["made_by"]["not_opened"], "an answer given without opening anything is asked again")
        count_file.unlink(missing_ok=True)
        r = cc("report", "--run", run, "--force", "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "bad_json_once"})
        check(r.get("ok") and json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))["made_by"]["attempts"] == 2, "an answer that is not JSON is asked again")

        # ---- failures never touch the chunk
        c2 = make_chunk(run, 2, rec_start=180.0)
        for mode, expect in (("bad_json", "not one JSON object"), ("exit1", "no answer"), ("rate_limit", "rate limited")):
            count_file.unlink(missing_ok=True)
            r = cc("report", "--run", run, "--chunk", c2, "--force", env={**base, "FAKE_CLAUDE_MODE": mode})
            rw = row(run, c2)
            check(not r.get("ok") and r["_rc"] == 1 and rw["status"] == "done" and rw["report"]["status"] == "failed" and expect in (rw["report"]["error"] or "")
                  and not (run / "10-media" / c2 / "report.json").is_file(), f"{mode}: the report fails with a reason, the chunk stays done, no report file " + str(rw["report"]["error"])[:120])
        check(count_file.read_text() == "1", "a rate limit stops the attempts at once (one session call, not two)")
        t = time.time()
        r = cc("report", "--run", run, "--chunk", c2, "--force", env={**base, "FAKE_CLAUDE_MODE": "hang", "CC_REPORT_TIMEOUT": "2"})
        rw = row(run, c2)
        check(not r.get("ok") and "ran longer than 2 s" in (rw["report"]["error"] or "") and time.time() - t < 30, f"a session that hangs is ended at the time limit ({round(time.time() - t, 1)} s) " + str(rw["report"]["error"])[:100])
        pl = cc("report", "--run", run, "--dry-run", env=base)
        check(c2 in pl["would_report"], "a failed report is listed again by the command (the watcher's own catch-up stops after max_attempts)")

        # ---- stale: the chunk's rec start moved
        rows_p = run / "00-inventory" / "chunks.json"
        rows = json.loads(rows_p.read_text(encoding="utf-8"))
        rows[0]["rec_start_s"] = 7.0
        rows_p.write_text(json.dumps(rows), encoding="utf-8")
        s = cc("status", "--run", run, env=base)
        check(s["reports"]["stale"] == 1, "a chunk whose rec start moved has a STALE report " + json.dumps(s["reports"]))
        r = cc("report", "--run", run, "--chunk", cid, env={**base, "FAKE_CLAUDE_MODE": "ok"})
        rep = json.loads((run / "10-media" / cid / "report.json").read_text(encoding="utf-8"))
        check(r.get("ok") and rep["rec_from"] == 7.0 and rep["look"][0]["rec_from"] == 7.0, "the stale report is made again from the new rec span")

        # ---- several at once
        run2 = tmp / "runs" / "20261113-000001-rpar"
        (run2 / "00-inventory").mkdir(parents=True)
        (run2 / "state.json").write_text('{"schema":"cc/1","channel":"rpar"}', encoding="utf-8")
        ids = [make_chunk(run2, n, rec_start=180.0 * (n - 1)) for n in (1, 2, 3, 4)]
        t = time.time()
        r = cc("report", "--run", run2, "--parallel", "4", env={**base, "FAKE_CLAUDE_MODE": "slow", "FAKE_CLAUDE_SLEEP": "2.0"})
        el = time.time() - t
        check(r.get("ok") and r["reported"] == 4 and r["parallel"] == 4 and el < 6.5, f"four sessions run at once ({round(el, 1)} s for four 2 s sessions; one after another would take 8 s+)")
        check(all((run2 / "10-media" / i / "report.md").is_file() for i in ids), "every chunk has its report")

        # ---- the watcher makes the report after a real ingest (a 12 s chunk, no Whisper)
        if shutil.which("ffmpeg"):
            inbox = tmp / "inbox"
            ses = "20261113-010000-wtest"
            sd = inbox / "wtest" / ses
            sd.mkdir(parents=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                            "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(sd / "chunk-0001.mp4")], check=True)
            (sd / "chunk-0001.json").write_text(json.dumps({"schema": "tcr/1", "channel": "wtest", "session": ses, "chunk": 1, "file": "chunk-0001.mp4", "t0_utc": "2026-11-13T01:00:00.000Z",
                                                            "t1_utc": "2026-11-13T01:00:12.000Z", "duration_s": 12.0, "segments": 6, "bytes": 1,
                                                            "quality": {"name": "720p60", "width": 1280, "height": 720, "fps": 30}, "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "duration",
                                                            "stream": {"id": "1", "title": "t", "game": "g", "viewers": 1, "uptime_s": 1, "started_at": "2026-11-13T01:00:00.000Z"}}), encoding="utf-8")
            count_file.unlink(missing_ok=True)
            r = cc("watch", "--once", "--skip-whisper", "--inbox", inbox, "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1",
                   env={**base, "FAKE_CLAUDE_MODE": "ok", "CC_INBOX": str(inbox)})
            wrun = tmp / "runs" / ses
            check(r.get("ok") and r.get("reports") and r["reports"]["done"] == 1 and not r["reports"]["failed"], "watch --once: the ingested chunk got its report before the watcher left " + json.dumps(r.get("reports")))
            wrep = json.loads((wrun / "10-media" / "C0001" / "report.json").read_text(encoding="utf-8")) if (wrun / "10-media" / "C0001" / "report.json").is_file() else {}
            check(wrep.get("chunk") == "C0001" and len(wrep.get("look", [])) >= 1 and row(wrun, "C0001")["report"]["status"] == "done" and row(wrun, "C0001")["status"] == "pending",
                  "the watcher's report is in the chunk folder, made without a transcript (--skip-whisper): the chunk's own status is untouched (still pending)")
            r = cc("watch", "--once", "--skip-whisper", "--no-report", "--inbox", inbox, "--interval", "0.5", "--stable", "0.6", env={**base, "FAKE_CLAUDE_MODE": "ok", "CC_INBOX": str(inbox)})
            check(r.get("ok") and r.get("reports") is None, "watch --no-report starts no reporter")
        else:
            print("skip the watcher check (ffmpeg not on PATH)")

        d = cc("doctor", env=base)
        cl = [c for c in d.get("checks", []) if c["name"].startswith("claude CLI")]
        check(cl and cl[0]["ok"] and "claude-haiku-5-5" in cl[0]["detail"] and ".cmd shim" in cl[0]["detail"], "doctor shows the claude CLI and the report settings " + (cl[0]["detail"][:140] if cl else "-"))
        off = cc("report", "--run", run, "--dry-run", env={**base, "CC_CLAUDE_BIN": str(tmp / "nope.exe"), "PATH": str(tmp)})
        check(off.get("claude") is None or Path(off["claude"]).name.lower().startswith("claude"), "without a claude CLI the dry run says which one it found (none, or the user's own)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
