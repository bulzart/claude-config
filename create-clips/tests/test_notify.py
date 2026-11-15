"""Test of the ready alert (scripts/cc_notify.py, scripts/notify.ps1) with stand-ins for the toast and the message box (tests/fake_notify.py): nothing is shown.

    python tests/test_notify.py

Checks: when a run counts as ready (the recording ended or went quiet, no chunk waiting or unprocessed, reports settled), what the notification says (the exact
command with the full run path, failures named), that it is sent once per state of the run and again when the run changes, the message box fallback when the toast is
refused, `notify --test`, `status`, `doctor`, the catch-up of finished runs the watcher never announced, the watcher alerting by itself after a real ingest (a 12 s chunk,
no Whisper, a stand-in claude for the report), CC_NOTIFY=0 silencing the watcher but not the command, and the real notify.ps1 building a well-formed toast
(dry run: Windows is asked, nothing is shown).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
CC = SCRIPTS / "cc.py"
PY = sys.executable
FAKE_NOTIFY = HERE / "fake_notify.py"
FAKE_CLAUDE = HERE / "fake_claude.py"
sys.path.insert(0, str(SCRIPTS))
import cc_crypto_loader  # noqa: E402,F401


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def lines_of(p: Path) -> list:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []


def wait_for(p: Path, n: int, secs: float = 8.0) -> list:
    end = time.time() + secs
    while time.time() < end:
        got = lines_of(p)
        if len(got) >= n:
            return got
        time.sleep(0.2)
    return lines_of(p)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-notify-test-"))
    toasts, boxes = tmp / "toasts.jsonl", tmp / "boxes.jsonl"
    base = {"CC_RUNS_ROOT": str(tmp / "runs"), "CC_INBOX": str(tmp / "inbox"), "CC_NOTIFY_BIN": str(FAKE_NOTIFY), "CC_NOTIFY_BOX_CMD": str(FAKE_NOTIFY),
            "FAKE_NOTIFY_OUT": str(toasts), "FAKE_BOX_OUT": str(boxes), "CC_REPORT": "0"}
    os.environ.update({k: v for k, v in base.items() if k != "CC_REPORT"})
    os.environ["CC_NOTIFY"] = "0"           # in this process only the facts are tested; the commands below set their own environment

    def cc(*args, env=None, timeout=600):
        e = dict(os.environ)
        e.pop("CC_NOTIFY", None)
        e.update(base)
        e.update(env or {})
        cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, timeout=timeout)
        last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
        j = json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}
        j["_rc"] = cp.returncode
        j["_stderr"] = cp.stderr[-900:]
        return j

    def make_run(name, statuses, recording=None, files=(), channel="ntest", report=None):
        run = tmp / "runs" / name
        sess = tmp / "inbox" / channel / name
        (run / "00-inventory").mkdir(parents=True, exist_ok=True)
        sess.mkdir(parents=True, exist_ok=True)
        st = {"schema": "cc/1", "channel": channel, "session": name, "inbox": str(sess), "chunks": {}}
        if recording is not None:
            st["recording"] = recording
        (run / "state.json").write_text(json.dumps(st), encoding="utf-8")
        rows = []
        for i, s in enumerate(statuses, start=1):
            full = s == "done"
            stages = {k: True for k in ("move", "probe", "audio", "sheets", "transcript", "digest")} if full else \
                {"move": True, "probe": True, "audio": s == "pending", "sheets": False, "transcript": False, "digest": False}
            row = {"id": f"C{i:04d}", "index": i, "rec_start_s": 180.0 * (i - 1), "duration_s": 180.0, "status": s, "stages": stages, "stale_rec": False}
            if report and i in report:
                row["report"] = report[i]
            rows.append(row)
        (run / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")
        for f in files:
            (sess / f).write_bytes(b"x")
        return run

    ended = {"started_at": "2026-11-13T12:00:00.000Z", "ended_at": "2026-11-13T12:10:00.000Z", "reason": "stream-ended", "chunks": 2, "chunk_seconds": 180}
    try:
        import cc_notify as N

        # ---- the facts
        r = make_run("20261113-000001-a", ["done", "done"], recording={**ended, "ended_at": None})
        f = N.run_facts(r, reports_on=False)
        check(not f["alert"] and any("has not ended" in w for w in f["why_not"]), "a recording that has not ended is not ready " + str(f["why_not"]))
        r = make_run("20261113-000002-b", ["done", "done"], recording=ended)
        f = N.run_facts(r, reports_on=False)
        check(f["alert"] and f["ready"] and not f["why_not"] and f["done"] == ["C0001", "C0002"] and f["rec_total_s"] == 360.0, "an ended recording with every chunk done is ready")
        m = N.build_message(f, r)
        check(m["title"] == "Create-clips is ready: ntest" and m["lines"][1] == f"Run: /create-clips {r}" and "All 2 chunks processed (0:06:00 of the stream)" in m["lines"][0],
              "the notification names the channel, counts the chunks and carries the exact command with the full run path " + json.dumps(m)[:230])
        r = make_run("20261113-000003-c", ["done", "processing"], recording=ended)
        f = N.run_facts(r, reports_on=False)
        check(not f["alert"] and any("not processed yet: C0002" in w for w in f["why_not"]), "a chunk still being processed holds the alert back " + str(f["why_not"]))
        r = make_run("20261113-000004-d", ["done", "done"], recording={**ended, "chunks": 3}, files=["chunk-0003.mp4"])
        f = N.run_facts(r, reports_on=False)
        check(not f["alert"] and f["waiting"] == ["chunk-0003.mp4"] and any("still in the inbox" in w for w in f["why_not"]), "a chunk file still in the inbox holds it back")
        f = N.run_facts(r, reports_on=False, dead=[tmp / "inbox" / "ntest" / "20261113-000004-d" / "chunk-0003.mp4"])
        m = N.build_message(f, r)
        check(f["alert"] and f["stuck"] == ["chunk-0003.mp4"] and "(with problems)" in m["title"] and "stuck in the inbox: chunk-0003.mp4" in m["lines"][0],
              "a file the watcher gave up on is named as stuck, it does not hold the alert back forever " + m["lines"][0][:120])
        r = make_run("20261113-000005-e", ["done", "done"], recording={**ended, "chunks": 3})
        f = N.run_facts(r, reports_on=False)
        check(not f["alert"] and f["missing"] == 1 and any("recorder saved 3 chunks, 2 have arrived" in w for w in f["why_not"]), "the recorder's own chunk count must be accounted for " + str(f["why_not"]))
        f = N.run_facts(r, reports_on=False, now=time.time() + 3600)
        m = N.build_message(f, r)
        check(f["alert"] and f["missing"] == 1 and "1 chunk(s) the recorder saved never arrived" in m["lines"][0], "after a quiet hour a missing chunk is reported, not waited for any more")

        # ---- failures
        r = make_run("20261113-000006-f", ["done", "failed", "done"], recording={**ended, "chunks": 3})
        f = N.run_facts(r, reports_on=False)
        m = N.build_message(f, r)
        check(f["alert"] and f["ready"] and f["failed"] == ["C0002"] and m["title"] == "Create-clips is ready (with problems): ntest" and "2 of 3 chunks processed" in m["lines"][0] and "failed: C0002" in m["lines"][0],
              "a failed chunk does not stop the alert: the title says problems and the text names it " + m["lines"][0][:140])
        r = make_run("20261113-000007-g", ["failed", "failed"], recording=ended)
        f = N.run_facts(r, reports_on=False)
        m = N.build_message(f, r)
        check(f["alert"] and not f["ready"] and m["title"].startswith("Create-clips run finished, nothing usable") and "Look at the run folder" in m["lines"][1], "when nothing could be processed the alert says so, and does not offer the command")

        # ---- reports
        r = make_run("20261113-000008-h", ["done", "done"], recording=ended, report={1: {"status": "failed", "attempts": 2}})
        f = N.run_facts(r, reports_on=True)
        check(not f["alert"] and f["reports_pending"] == ["C0002"] and f["reports_failed"] == ["C0001"] and any("report(s) still to be made: C0002" in w for w in f["why_not"]),
              "a report still to be made holds the alert back; one that failed for good does not " + str(f["why_not"]))
        r = make_run("20261113-000009-i", ["done", "done"], recording=ended, report={1: {"status": "failed", "attempts": 2}, 2: {"status": "failed", "attempts": 2}})
        f = N.run_facts(r, reports_on=True)
        m = N.build_message(f, r)
        check(f["alert"] and "(with problems)" in m["title"] and "reports 0 of 2 (failed: C0001, C0002)" in m["lines"][0], "reports that failed for good are named in the alert " + m["lines"][0][:150])
        r = make_run("20261113-000010-j", ["done", "done"], recording=ended)
        check(N.run_facts(r, reports_on=False)["alert"], "with the reporter off the alert does not wait for reports")

        # ---- a recorder that never wrote its end
        r = make_run("20261113-000011-k", ["done"], recording={**ended, "ended_at": None, "chunks": 0})
        f = N.run_facts(r, reports_on=False, now=time.time() + 60 * 60)
        m = N.build_message(f, r)
        check(f["alert"] and f["idle_finished"] and "wrote no end marker; nothing arrived for" in m["lines"][0], "a recording that went quiet for 15 minutes counts as finished, and the text says it had no end marker")
        f = N.run_facts(r, reports_on=False, now=time.time() + 60)
        check(not f["alert"], "a recording that is only quiet for a minute is not finished")
        r = make_run("20261113-000012-l", ["done"], recording={**ended, "chunks": 1, "reason": "low-disk"})
        m = N.build_message(N.run_facts(r, reports_on=False), r)
        check("The recording stopped early: free disk space fell below the limit." in m["lines"][0], "an early stop is named in plain words")
        r = make_run("20261113-000014-n", ["done"], recording={**ended, "chunks": 1, "reason": "user"})
        check("stopped early" not in N.build_message(N.run_facts(r, reports_on=False), r)["lines"][0], "a stop you asked for (reason user) or the stream's end is no 'stopped early'")
        r = make_run("20261113-000015-o", ["done"], recording={**ended, "chunks": 1, "reason": "save-failed: disk full"})
        check("The recording stopped early: save-failed: disk full." in N.build_message(N.run_facts(r, reports_on=False), r)["lines"][0], "a reason the alert has no words for is shown as the recorder wrote it")
        r = make_run("20261113-000013-m", ["pending"], recording={**ended, "chunks": 1})
        row = json.loads((r / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        row[0]["stages"] = {k: True for k in ("move", "probe", "audio", "sheets", "digest")} | {"transcript": False}
        (r / "00-inventory" / "chunks.json").write_text(json.dumps(row), encoding="utf-8")
        check(not N.run_facts(r, reports_on=False)["alert"] and N.run_facts(r, reports_on=False, skip_transcript=True)["alert"], "a watcher that runs without Whisper counts a chunk without its transcript as processed")

        # ---- the command: once per state
        run = make_run("20261113-000020-ready", ["done", "done"], recording=ended)
        v = cc("notify", "--run", run, "--dry-run")
        check(v.get("ok") and v["dry_run"] and not v["sent"] and not toasts.is_file() and "ready_notified" not in json.loads((run / "state.json").read_text(encoding="utf-8")),
              "notify --dry-run says what it would send and records nothing")
        v = cc("notify", "--run", run)
        got = wait_for(toasts, 1)
        st = json.loads((run / "state.json").read_text(encoding="utf-8"))
        check(v.get("ok") and v["sent"] and v["how"] == "toast" and len(got) == 1 and got[0]["title"] == "Create-clips is ready: ntest" and got[0]["lines"][1] == f"Run: /create-clips {run}"
              and got[0]["persistent"] is True and got[0]["sound"] is True, "notify sends one toast with the title, the command, persistent and with sound " + json.dumps(got)[:200])
        check(st["ready_notified"]["how"] == "toast" and st["ready_notified"]["ok"] is True and st["ready_notified"]["chunks"] == 2, "state.json records what was announced " + json.dumps(st["ready_notified"])[:160])
        v = cc("notify", "--run", run)
        check(v.get("ok") and not v["sent"] and v.get("already_notified") and len(lines_of(toasts)) == 1, "the same state is not announced twice (a restart repeats nothing)")
        rows = json.loads((run / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        rows.append({**rows[0], "id": "C0003", "index": 3, "rec_start_s": 360.0})
        (run / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")
        s2 = json.loads((run / "state.json").read_text(encoding="utf-8"))
        s2["recording"]["chunks"] = 3
        (run / "state.json").write_text(json.dumps(s2), encoding="utf-8")
        v = cc("notify", "--run", run)
        got = wait_for(toasts, 2)
        check(v.get("sent") and len(got) == 2 and "All 3 chunks processed" in got[1]["lines"][0], "a later chunk of the same run is a new state and gets a new alert")
        run_nr = make_run("20261113-000021-notready", ["done", "processing"], recording=ended)
        v = cc("notify", "--run", run_nr)
        check(v.get("ok") and not v["sent"] and v["why_not"] and len(lines_of(toasts)) == 2, "a run that is not ready sends nothing and says what it waits for " + str(v.get("why_not"))[:100])
        v = cc("notify", "--run", run_nr, "--force")
        got = wait_for(toasts, 3)
        check(v.get("sent") and got[2]["title"] == "Create-clips run is NOT ready: ntest" and got[2]["lines"][0].startswith("Still waiting for:"), "--force sends a clearly marked 'not ready' note " + got[2]["title"])
        v = cc("notify", "--test")
        got = wait_for(toasts, 4)
        check(v.get("ok") and v["test"] and got[3]["title"] == "Create-clips notifications work", "notify --test sends a test notification without any run")
        v = cc("notify", "--run", make_run("20261113-000022-off", ["done"], recording={**ended, "chunks": 1}), env={"CC_NOTIFY": "0"})
        check(v.get("sent") and v["automatic_alerts"] is False, "CC_NOTIFY=0 silences the watcher only: the command still sends when asked")

        # ---- the toast is refused: the message box takes over
        before = len(lines_of(boxes))
        run_b = make_run("20261113-000023-box", ["done"], recording={**ended, "chunks": 1})
        v = cc("notify", "--run", run_b, env={"FAKE_NOTIFY_MODE": "fail"})
        got = wait_for(boxes, before + 1)
        st = json.loads((run_b / "state.json").read_text(encoding="utf-8"))
        check(v.get("ok") and v["sent"] and v["how"] == "messagebox" and len(got) == before + 1 and got[-1]["title"] == "Create-clips is ready: ntest" and f"/create-clips {run_b}" in got[-1]["text"]
              and st["ready_notified"]["how"] == "messagebox", "toasts switched off: a message box with the same text is shown instead and the record says so")
        orig_send, orig_box = N.send_toast, N.show_box
        N.send_toast = lambda *a, **k: {"ok": False, "error": "no toast", "setting": "DisabledForUser"}
        N.show_box = lambda *a, **k: {"ok": False, "error": "no box"}
        res = N.deliver("t", ["l"], {"persistent": True, "sound": True})
        N.send_toast, N.show_box = orig_send, orig_box
        check(res["ok"] is False and res["error"] == "toast: no toast; message box: no box", "when neither the toast nor the message box can be shown the failure says both reasons")
        check("ready_notified" not in json.loads((run_nr / "state.json").read_text(encoding="utf-8")), "a forced 'not ready' note leaves no announcement record, so the real alert can still come")

        # ---- the catch-up: finished runs that were never announced
        root = tmp / "seedroot"
        now = time.time()
        iso = lambda secs: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - secs))
        for nm, rec, extra in (("recent", {"ended_at": iso(3600)}, {}), ("old", {"ended_at": iso(3 * 86400)}, {}), ("done-already", {"ended_at": iso(600)}, {"ready_notified": {"fingerprint": "x"}}),
                               ("never-ended", {"started_at": iso(600)}, {}), ("no-recording", None, {})):
            d = root / nm
            d.mkdir(parents=True)
            st = {"schema": "cc/1", **extra}
            if rec is not None:
                st["recording"] = rec
            (d / "state.json").write_text(json.dumps(st), encoding="utf-8")
        a = N.Alerts({**N.notify_cfg(), "enabled": True}, background=False)
        n = a.seed(root, now)
        check(n == 1 and {p.name for p in a.active} == {"recent"}, "the catch-up takes a run that ended within a day and was never announced, and only that one " + str(sorted(p.name for p in a.active)))

        # ---- the real notify.ps1 (a dry run: Windows is asked, nothing is shown)
        if sys.platform == "win32" and N._powershell():
            os.environ.pop("CC_NOTIFY_BIN", None)
            res = N.send_toast("Ready & <set> \"quoted\" 'x'", ["Run: /create-clips C:\\Users\\Some One\\runs\\a&b", "second <line>"], persistent=True, sound=True, dry_run=True)
            x = None
            try:
                x = ET.fromstring(res.get("xml") or "")
            except ET.ParseError as e:
                print("   xml:", e, (res.get("xml") or "")[:200])
            texts = [t.text for t in x.iter("text")] if x is not None else []
            check(res.get("ok") and res.get("how") == "dry-run" and res.get("setting") == "Enabled" and x is not None and x.get("scenario") == "reminder" and len(texts) == 3
                  and texts[0] == "Ready & <set> \"quoted\" 'x'" and texts[1].endswith("a&b") and any(a_.get("activationType") == "system" for a_ in x.iter("action")),
                  "notify.ps1 builds a well-formed reminder toast (special characters escaped, three text lines, a Dismiss button) and Windows has toasts enabled " + json.dumps({k: res[k] for k in res if k != "xml"}))
            res = N.send_toast("t", ["l"], persistent=False, sound=False, dry_run=True)
            x = ET.fromstring(res["xml"]) if res.get("xml") else None
            check(x is not None and x.get("duration") == "long" and x.get("scenario") is None and not list(x.iter("action")) and x.find("audio").get("silent") == "true",
                  "persistent off: a toast that goes away by itself; sound off: silent")
            os.environ["CC_NOTIFY_BIN"] = str(FAKE_NOTIFY)
        else:
            print("skip the notify.ps1 check (not Windows PowerShell)")

        d = cc("doctor")
        nd = [c for c in d.get("checks", []) if c["name"].startswith("Windows notification")]
        check(nd and nd[0]["ok"] and "automatic alerts" in nd[0]["detail"], "doctor shows the notification check " + (nd[0]["detail"][:150] if nd else "-"))
        s = cc("status", "--run", run_nr)
        check(s.get("ok") and s["ready"]["ready"] is False and s["ready"]["why_not"] and s["ready"]["announced"] is False, "status says whether /create-clips can start and why not " + json.dumps(s.get("ready"))[:160])
        s = cc("status", "--run", run)
        check(s["ready"]["ready"] is True and s["ready"]["announced"] is True, "status says ready and announced for the run that was announced")

        # ---- the watcher alerts by itself after a real ingest (its own inbox and runs folder: the runs above must not be caught up)
        if shutil.which("ffmpeg"):
            shim = tmp / "fake-claude.cmd"
            shim.write_text(f'@echo off\r\n"{PY}" "{FAKE_CLAUDE}" %*\r\n', encoding="utf-8")
            winbox, wruns = tmp / "winbox", tmp / "wruns"
            wenv = {"CC_CLAUDE_BIN": str(shim), "FAKE_CLAUDE_MODE": "ok", "CC_REPORT": "1", "CC_INBOX": str(winbox), "CC_RUNS_ROOT": str(wruns)}
            ended_now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() - 30))
            started_now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() - 60))

            def make_session(ses: str) -> None:
                sd = winbox / "wtest" / ses
                sd.mkdir(parents=True)
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                                "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(sd / "chunk-0001.mp4")], check=True)
                (sd / "chunk-0001.json").write_text(json.dumps({"schema": "tcr/1", "channel": "wtest", "session": ses, "chunk": 1, "file": "chunk-0001.mp4", "t0_utc": started_now, "t1_utc": ended_now,
                                                                "duration_s": 12.0, "segments": 6, "bytes": 1, "quality": {"name": "720p60", "width": 1280, "height": 720, "fps": 30},
                                                                "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "duration",
                                                                "stream": {"id": "1", "title": "t", "game": "g", "viewers": 1, "uptime_s": 1, "started_at": started_now}}), encoding="utf-8")
                (sd / "session.json").write_text(json.dumps({"schema": "tcr-session/1", "channel": "wtest", "session": ses, "started_at": started_now, "ended_at": ended_now,
                                                              "reason": "user", "chunks": 1, "chunk_seconds": 180}), encoding="utf-8")

            def watch(env):
                return cc("watch", "--once", "--skip-whisper", "--inbox", winbox, "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1", env=env)

            ses, ses2 = "20261113-010000-wtest", "20261113-020000-wtest"
            make_session(ses)
            n0 = len(lines_of(toasts))
            r = watch(wenv)
            got = wait_for(toasts, n0 + 1)
            r["why_not"] = cc("notify", "--run", wruns / ses, "--dry-run", env=wenv).get("why_not")
            wst = json.loads((wruns / ses / "state.json").read_text(encoding="utf-8"))
            r["recording"], r["session_copy"] = wst.get("recording"), (wruns / ses / "00-inventory" / "session.json").is_file()
            check(wst.get("stream_ended") is True and (wst.get("recording") or {}).get("ended_at") == ended_now and wst["recording"]["chunks"] == 1,
                  "a recording that had ended before its first chunk was processed still gets its end into state.json (the ingest's own copy of session.json must not hide it) " + json.dumps(wst.get("recording")))
            check(r.get("ok") and r["notified"] == [ses] and len(got) == n0 + 1 and got[-1]["title"] == "Create-clips is ready: wtest" and "reports 1 of 1" in got[-1]["lines"][0]
                  and got[-1]["lines"][1] == f"Run: /create-clips {wruns / ses}", "watch: after the chunk, the end marker and the report are in, the watcher alerts by itself " + json.dumps(got[-1] if got else {})[:230]
                  + " | watch said: " + json.dumps({k: r.get(k) for k in ("ok", "notified", "why_not", "recording", "session_copy", "stderr", "error")})[:700])
            r = watch(wenv)
            check(r.get("ok") and r["notified"] == [] and len(lines_of(toasts)) == n0 + 1, "a second pass (a watcher restart) does not announce the same run again")
            make_session(ses2)
            r = watch({**wenv, "CC_NOTIFY": "0"})
            check(r.get("ok") and r["notified"] == [] and len(lines_of(toasts)) == n0 + 1 and (wruns / ses2 / "10-media" / "C0001" / "report.md").is_file(),
                  "CC_NOTIFY=0: the watcher processes the run and says nothing")
            r = watch(wenv)
            got = wait_for(toasts, n0 + 2)
            check(r.get("ok") and r["notified"] == [ses2] and len(got) == n0 + 2, "the next watcher (alerts on) catches up on the finished run it was never told about "
                  + json.dumps({k: r.get(k) for k in ("ok", "notified", "reports", "_stderr")})[:900]
                  + " state: " + json.dumps({k: json.loads((wruns / ses2 / "state.json").read_text(encoding="utf-8")).get(k) for k in ("recording", "ready_notified", "stream_ended")}))
        else:
            print("skip the watcher check (ffmpeg not on PATH)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
