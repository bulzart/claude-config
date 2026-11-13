"""create-clips ready alert: a Windows notification when a recording's run is fully processed and /create-clips can start on it.

A run is READY when (facts about files; nothing here judges the footage):
  - the recording has ended (the recorder wrote `ended_at` in session.json: the stream ended, you stopped it, the disk guard or the length limit hit),
    or nothing has arrived for `notify.idle_minutes` (a recorder that died cannot write its end);
  - no chunk file of the session waits in the inbox, and the recorder's own chunk count (session.json `chunks`) is accounted for;
  - no chunk is pending or being processed (a chunk that FAILED is settled: the alert names it);
  - every chunk report (cc_report) is made or has failed for good, when the chunk reporter is on.
The watcher (`cc.py watch`) checks this beside its chunk work and alerts once per state of the run. The alert is a Windows toast that stays on screen until it is
dismissed and carries the exact command to run; a message box is the fallback when toasts are switched off. `cc.py notify --run RUN` does the same by hand.
What a run was alerted about is `state.json -> ready_notified` (a fingerprint of its chunks and reports): a restart never repeats an alert, and a later chunk of
the same run gives a new one. A finished recording that never got an alert (the watcher was not running) is picked up within `notify.catchup_hours`.
Settings: config.json `notify` {enabled, persistent, sound, idle_minutes, catchup_hours}; CC_NOTIFY=0 turns the automatic alerts off. Details: docs/processing.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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

from cc_common import (CC_HOME, NO_WINDOW, cfg_get, fmt_hms, load_chunks, load_state, now_iso, out, read_json, resolve_run, run_cmd, say,
                       update_state)
from cc_report import eligible, find_claude, needs_report, report_cfg, report_state

SCRIPT = CC_HOME / "scripts" / "notify.ps1"
DEFAULTS = {"enabled": True, "persistent": True, "sound": True, "idle_minutes": 15, "catchup_hours": 24}
# the recorder's own end reasons (twitch-chunk-recorder src/view.js): a stop the user asked for or the stream's end is normal, every other one is named in the alert
REASONS = {"user": "stopped by you", "stop": "stopped by you", "stopped": "stopped", "stream-ended": "the stream ended", "size-limit": "the size limit you set was reached",
           "limit": "the size limit you set was reached", "low-disk": "free disk space fell below the limit", "stalled": "no new video for 10 minutes",
           "browser-restarted": "Chrome was restarted", "error": "the recorder hit an error"}
QUIET = ("user", "stop", "stopped", "stream-ended")


def notify_cfg() -> dict:
    c = {**DEFAULTS, **(cfg_get("notify", {}) or {})}
    v = os.environ.get("CC_NOTIFY")
    if v is not None and v.strip() != "":
        c["enabled"] = v.strip().lower() not in ("0", "off", "false", "no")
    if os.environ.get("CC_NOTIFY_IDLE_MIN"):
        c["idle_minutes"] = float(os.environ["CC_NOTIFY_IDLE_MIN"])
    c["idle_minutes"] = max(0.0, float(c["idle_minutes"]))
    c["catchup_hours"] = max(1.0, float(c["catchup_hours"]))
    return c


# --------------------------------------------------------------------------- the facts

def _parse_iso(s) -> float | None:
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return (d if d.tzinfo else d.astimezone()).timestamp()


def _last_activity(run: Path, sess_dir: Path | None) -> float | None:
    """The newest modification time among the chunk table and the files of the recording's inbox folder."""
    cands = [run / "00-inventory" / "chunks.json"]
    if sess_dir is not None and sess_dir.is_dir():
        try:
            cands += [p for p in sess_dir.iterdir() if p.is_file()]
        except OSError:
            pass
    best = None
    for p in cands:
        try:
            t = p.stat().st_mtime
        except OSError:
            continue
        best = t if best is None or t > best else best
    return best


def run_facts(run, *, inbox=None, reporter=None, reports_on=None, skip_transcript=False, dead=(), now=None, cfg=None) -> dict:
    """What there is to know about whether `run` can be handed to /create-clips. `reports_on`: are chunk reports expected (the watcher passes whether its
    reporter runs; None = the settings say so and the claude CLI exists). `dead`: inbox files the watcher gave up on (they are reported as stuck, they do not
    hold the alert back). `skip_transcript`: the watcher runs with --skip-whisper, so a chunk without its transcript counts as processed."""
    run = Path(run)
    cfg = cfg or notify_cfg()
    now = time.time() if now is None else float(now)
    st = load_state(run)
    rows = load_chunks(run)
    rec = st.get("recording") or {}
    ended = bool(rec.get("ended_at"))
    done, failed, busy = [], [], []
    for r in rows:
        s, stg = r.get("status"), r.get("stages") or {}
        if s == "done" or (skip_transcript and s != "failed" and all(stg.get(k) is True for k in ("move", "probe", "audio", "sheets", "digest"))):
            done.append(r["id"])
        elif s == "failed":
            failed.append(r["id"])
        else:
            busy.append(r["id"])
    rec_total = round(sum(float(r.get("duration_s") or 0) for r in rows if r["id"] in done), 1)

    sess_dir = Path(st["inbox"]) if st.get("inbox") else None
    if sess_dir is None and inbox is not None and st.get("channel") and st.get("session"):
        sess_dir = Path(inbox) / st["channel"] / st["session"]
    dead_set = {Path(p) for p in dead}
    waiting, stuck = [], []
    if sess_dir is not None and sess_dir.is_dir():
        try:
            for p in sorted(sess_dir.iterdir()):
                if p.is_file() and re.match(r"^chunk-\d+\.mp4$", p.name, re.I):
                    (stuck if p in dead_set else waiting).append(p.name)
                elif p.is_file() and p.name.lower().endswith(".crdownload"):
                    waiting.append(p.name)
        except OSError:
            pass

    last = _last_activity(run, sess_dir)
    quiet_s = round(now - last, 1) if last is not None else None
    idle_s = float(cfg["idle_minutes"]) * 60.0
    quiet_long = idle_s > 0 and quiet_s is not None and quiet_s >= idle_s
    if quiet_long and waiting:                       # nothing moves any more: what still lies in the inbox is stuck, not about to be processed
        stuck, waiting = stuck + waiting, []
    finished = ended or quiet_long
    rc = rec.get("chunks")
    accounted = len(rows) + len(waiting) + len(stuck)
    missing = max(0, int(rc) - accounted) if ended and isinstance(rc, int) else 0

    rcfg = report_cfg()
    if reports_on is None:
        reports_on = bool(rcfg["enabled"] and find_claude(rcfg)[0])
    rep_done, rep_failed, rep_pending, rep_eligible = [], [], [], 0
    if reports_on:
        for r in rows:
            if not eligible(r):
                continue
            rep_eligible += 1
            s = report_state(run, r)
            if s == "done":
                rep_done.append(r["id"])
            elif s == "running" or needs_report(run, r, rcfg):
                rep_pending.append(r["id"])
            else:
                rep_failed.append(r["id"])

    why = []
    if not rows and not waiting and not stuck:
        why.append("no chunk has arrived yet")
    if not finished:
        why.append("the recording has not ended (no end marker from the recorder yet)")
    if waiting:
        why.append(f"{len(waiting)} chunk file(s) still in the inbox: {', '.join(waiting[:6])}")
    if busy:
        why.append(f"{len(busy)} chunk(s) not processed yet: {', '.join(busy[:6])}")
    if missing and not quiet_long:
        why.append(f"the recorder saved {rc} chunks, {accounted} have arrived")
    if rep_pending:
        why.append(f"{len(rep_pending)} chunk report(s) still to be made: {', '.join(rep_pending[:6])}")
    alert = not why                                  # everything that can settle has settled (the run may still hold nothing usable)
    fp = hashlib.sha1("|".join([",".join(sorted(done)), ",".join(sorted(failed)), ",".join(sorted(stuck)), ",".join(sorted(rep_done)),
                                ",".join(sorted(rep_failed)), str(rc)]).encode()).hexdigest()[:12]
    return {"run": str(run), "session": st.get("session") or run.name, "channel": st.get("channel"), "chunks": len(rows), "done": sorted(done), "failed": sorted(failed),
            "busy": sorted(busy), "rec_total_s": rec_total, "waiting": waiting, "stuck": stuck, "recorder_chunks": rc, "missing": missing, "ended": ended,
            "ended_at": rec.get("ended_at"), "reason": rec.get("reason"), "quiet_s": quiet_s, "idle_finished": bool(finished and not ended),
            "reports_on": bool(reports_on), "reports_eligible": rep_eligible, "reports_done": sorted(rep_done), "reports_failed": sorted(rep_failed),
            "reports_pending": sorted(rep_pending), "alert": alert, "ready": bool(alert and done), "why_not": why, "fingerprint": fp}


def build_message(f: dict, run) -> dict:
    """The notification's text: a title and two short lines (plain words, ASCII, the exact command)."""
    run = Path(run)
    name = f.get("channel") or run.name
    problems = bool(f["failed"] or f["stuck"] or f["missing"] or f["reports_failed"])
    cmd = f"/create-clips {run}"
    if not f["alert"]:
        return {"title": f"Create-clips run is NOT ready: {name}", "lines": ["Still waiting for: " + "; ".join(f["why_not"]), f"Later: {cmd}"]}
    n, nd = f["chunks"], len(f["done"])
    bits = [f"All {n} chunks processed" if nd == n and n != 1 else (f"{nd} of {n} chunks processed" if n != 1 else f"{nd} of 1 chunk processed")]
    if f["rec_total_s"]:
        bits[0] += f" ({fmt_hms(f['rec_total_s'], cs=False)} of the stream)"
    if f["failed"]:
        bits.append("failed: " + ", ".join(f["failed"]))
    if f["stuck"]:
        bits.append("stuck in the inbox: " + ", ".join(f["stuck"]))
    if f["missing"] and f["ended"]:
        bits.append(f"{f['missing']} chunk(s) the recorder saved never arrived")
    if f["reports_on"]:
        bits.append(f"reports {len(f['reports_done'])} of {f['reports_eligible']}" + (f" (failed: {', '.join(f['reports_failed'])})" if f["reports_failed"] else ""))
    l1 = "; ".join(bits) + "."
    if f["ended"] and f["reason"] and f["reason"] not in QUIET:
        l1 += f" The recording stopped early: {REASONS.get(f['reason'], f['reason'])}."
    elif not f["ended"]:
        l1 += f" The recorder wrote no end marker; nothing arrived for {int((f['quiet_s'] or 0) // 60)} min."
    if not f["done"]:
        return {"title": f"Create-clips run finished, nothing usable: {name}", "lines": [l1, f"Look at the run folder: {run}"]}
    return {"title": f"Create-clips is ready{' (with problems)' if problems else ''}: {name}", "lines": [l1, f"Run: {cmd}"]}


# --------------------------------------------------------------------------- showing it

def _powershell() -> str | None:
    p = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return str(p) if p.is_file() else shutil.which("powershell")


def _last_json(text: str) -> dict | None:
    for ln in reversed((text or "").strip().splitlines()):
        if ln.strip().startswith("{"):
            try:
                return json.loads(ln)
            except ValueError:
                return None
    return None


def send_toast(title: str, lines: list, *, persistent: bool = True, sound: bool = True, dry_run: bool = False, timeout: float = 60.0) -> dict:
    """One Windows toast through scripts/notify.ps1 (Windows PowerShell 5.1, hidden). CC_NOTIFY_BIN runs a stand-in script instead (tests)."""
    payload = {"title": title, "lines": [str(x) for x in lines], "persistent": bool(persistent), "sound": bool(sound)}
    fd, pf = tempfile.mkstemp(prefix="cc-notify-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True)
        override = os.environ.get("CC_NOTIFY_BIN")
        if override:
            cmd = [sys.executable, override, pf] + (["--dry-run"] if dry_run else [])
        else:
            ps = _powershell()
            if not ps or not SCRIPT.is_file():
                return {"ok": False, "error": "powershell.exe (Windows PowerShell 5.1) or notify.ps1 not found"}
            cmd = [ps, "-NoProfile", "-NonInteractive", "-NoLogo", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-PayloadFile", pf] + (["-DryRun"] if dry_run else [])
        try:
            cp = run_cmd(cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"the notification script gave no answer in {timeout:.0f} s"}
        res = _last_json(cp.stdout) or {"ok": False, "error": ((cp.stderr or cp.stdout or "").strip() or f"exit {cp.returncode}")[-300:]}
        res.setdefault("ok", cp.returncode == 0)
        if not dry_run:
            res.pop("xml", None)
        return res
    finally:
        try:
            os.unlink(pf)
        except OSError:
            pass


def show_box(title: str, lines: list) -> dict:
    """The fallback: a topmost message box from a detached pythonw.exe (no console, never blocks the caller). CC_NOTIFY_BOX_CMD runs a stand-in (tests)."""
    text = "\n".join(str(x) for x in lines)
    code = "import ctypes,sys; ctypes.windll.user32.MessageBoxW(0, sys.argv[2], sys.argv[1], 0x40 | 0x40000 | 0x10000)"
    override = os.environ.get("CC_NOTIFY_BOX_CMD")
    if override:
        cmd = [sys.executable, override, title, text]
    elif sys.platform == "win32":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        cmd = [str(pyw) if pyw.is_file() else sys.executable, "-c", code, title, text]
    else:
        return {"ok": False, "error": "no message box on this system"}
    flags = NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, creationflags=flags)
    except OSError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "how": "messagebox"}


def deliver(title: str, lines: list, cfg: dict | None = None, dry_run: bool = False) -> dict:
    cfg = cfg or notify_cfg()
    res = send_toast(title, lines, persistent=cfg["persistent"], sound=cfg["sound"], dry_run=dry_run)
    if res.get("ok") or dry_run:
        return res
    box = show_box(title, lines)                     # toasts are off for this app (or failed): a message box still reaches the user
    if box.get("ok"):
        return {"ok": True, "how": "messagebox", "toast_error": res.get("error"), "setting": res.get("setting")}
    return {"ok": False, "how": None, "error": f"toast: {res.get('error')}; message box: {box.get('error')}", "setting": res.get("setting")}


# --------------------------------------------------------------------------- once per state of a run

def notify_run(run, *, inbox=None, reporter=None, reports_on=None, skip_transcript=False, dead=(), force=False, dry_run=False, background=False,
               cfg=None, now=None) -> dict:
    """Check `run` and alert when it is ready and was not yet announced in this state. Never raises for a run that is simply not ready.
    background=True sends from a daemon thread (the watcher's loop never waits for a toast); the record in state.json is made first so the next check does not repeat it."""
    run = Path(run)
    cfg = cfg or notify_cfg()
    f = run_facts(run, inbox=inbox, reporter=reporter, reports_on=reports_on, skip_transcript=skip_transcript, dead=dead, now=now, cfg=cfg)
    res = {"ok": True, "run": str(run), "ready": f["ready"], "alert": f["alert"], "why_not": f["why_not"], "sent": False, "chunks": f["chunks"], "done": len(f["done"]),
           "failed": f["failed"], "quiet_s": f["quiet_s"], "fingerprint": f["fingerprint"]}
    prev = load_state(run).get("ready_notified") or {}
    if not (f["alert"] or force):
        return res
    if prev.get("fingerprint") == f["fingerprint"] and not force:
        res["already_notified"] = {"at": prev.get("at"), "how": prev.get("how")}
        return res
    msg = build_message(f, run)
    res["message"] = msg
    if dry_run:
        res["dry_run"] = True
        return res
    record = bool(f["alert"])                        # a forced "not ready" note is no announcement: it must not hide the real one that comes later
    if record:
        update_state(run, ready_notified={"at": now_iso(), "fingerprint": f["fingerprint"], "chunks": f["chunks"], "done": len(f["done"]), "failed": f["failed"], "how": "sending"})

    def work() -> dict:
        r = deliver(msg["title"], msg["lines"], cfg)
        try:
            if record:
                update_state(run, **{"ready_notified.how": r.get("how") or "failed", "ready_notified.ok": bool(r.get("ok")), "ready_notified.error": r.get("error")})
        except Exception as e:  # noqa: BLE001
            say(f"[notify] {run.name}: could not record the result: {e}")
        say(f"[notify] {run.name}: {msg['title']} -> " + (str(r.get("how")) if r.get("ok") else f"FAILED ({r.get('error')})"))
        return r

    if background:
        threading.Thread(target=work, daemon=True, name="cc-notify").start()
        res.update(sent=True, how="sending")
    else:
        r = work()
        res.update(sent=bool(r.get("ok")), how=r.get("how"), ok=bool(r.get("ok")))
        if not r.get("ok"):
            res["error"] = r.get("error")
    return res


class Alerts:
    """The watcher's side: the runs to look after, and one check every few seconds. A run enters when one of its chunks is ingested, or (at start and once a
    minute) when its recording ended within `catchup_hours` and nobody was told yet; it leaves when it was announced, or has been idle for that long."""

    def __init__(self, cfg: dict | None = None, background: bool = True, every: float = 10.0):
        self.cfg, self.background, self.every = cfg or notify_cfg(), background, every
        self.active: set = set()
        self.last_check = 0.0
        self.last_seed = 0.0

    def add(self, run) -> None:
        self.active.add(Path(run))

    def seed(self, root, now: float | None = None) -> int:
        now = time.time() if now is None else now
        n = 0
        try:
            dirs = [d for d in Path(root).iterdir() if d.is_dir()]
        except OSError:
            return 0
        for d in dirs:
            if d in self.active:
                continue
            st = read_json(d / "state.json", None)
            if not isinstance(st, dict) or st.get("ready_notified"):
                continue
            ended = _parse_iso((st.get("recording") or {}).get("ended_at"))
            if ended is None or now - ended > float(self.cfg["catchup_hours"]) * 3600:
                continue
            self.active.add(d)
            n += 1
        return n

    def tick(self, inbox, root, *, reporter=None, reports_on=None, skip_transcript=False, dead=(), force=False) -> list:
        now = time.time()
        if not force and now - self.last_check < self.every:
            return []
        self.last_check = now
        if force or now - self.last_seed >= 60:
            self.last_seed = now
            self.seed(root, now)
        sent = []
        for run in sorted(self.active):
            try:
                r = notify_run(run, inbox=inbox, reporter=reporter, reports_on=reports_on, skip_transcript=skip_transcript, dead=dead, background=self.background, cfg=self.cfg)
            except Exception as e:  # noqa: BLE001
                say(f"[notify] {run.name}: check failed: {type(e).__name__}: {e}")
                continue
            if r.get("sent") or r.get("already_notified"):
                self.active.discard(run)
                if r.get("sent"):
                    sent.append(r)
            elif not r.get("alert") and r.get("quiet_s") is not None and r["quiet_s"] > float(self.cfg["catchup_hours"]) * 3600:
                self.active.discard(run)                 # idle for the whole catch-up window and still not settled: no alert will come, stop looking
        return sent


# --------------------------------------------------------------------------- the command

def probe() -> dict:
    """Whether a toast could be shown (nothing is shown)."""
    return send_toast("probe", [], dry_run=True)


def cmd_notify(a):
    cfg = notify_cfg()
    if a.test:
        title, lines = "Create-clips notifications work", ["This is a test from: cc.py notify --test", "A real alert names the run and the exact /create-clips command."]
        res = deliver(title, lines, cfg, dry_run=a.dry_run)
        out({"ok": bool(res.get("ok")), "test": True, "dry_run": bool(a.dry_run), "automatic_alerts": cfg["enabled"], **{k: v for k, v in res.items() if k != "ok"}},
            0 if res.get("ok") else 1)
    if not a.run:
        out({"ok": False, "error": "--run RUN (or --test) is needed"}, 2)
    run = resolve_run(a.run)
    r = notify_run(run, force=a.force, dry_run=a.dry_run, background=False, cfg=cfg)
    r["automatic_alerts"] = cfg["enabled"]
    out(r, 0 if r.get("ok") else 1)


def register(sub) -> None:
    p = sub.add_parser("notify", help="the ready alert: check whether a run is fully processed and send the Windows notification (once per state of the run); --test sends a test one")
    p.add_argument("--run", help="run folder or session name")
    p.add_argument("--test", action="store_true", help="send a test notification (nothing about a run)")
    p.add_argument("--force", action="store_true", help="send even when the run is not ready or was already announced in this state (the text says what is missing)")
    p.add_argument("--dry-run", action="store_true", help="only say what would be sent: nothing is shown, nothing is recorded")
    p.set_defaults(func=cmd_notify)
