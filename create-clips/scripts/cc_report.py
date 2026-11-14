"""create-clips chunk reporter: a separate headless `claude -p` session (Haiku) reads what the processor made of one chunk and writes a REPORT.

When a chunk has its sheets, audio numbers, transcript and chat, the reporter opens them and writes down what the data shows: what the pictures show,
what is on screen as text, what is said, what the numbers do, what could not be read. It is a reporter, never a decider: no verdict, no label such as "ace",
no name corrected, nothing ranked (reference/reporter.md is its whole brief). The agents of /create-clips read these reports instead of opening every sheet.

Files per chunk (10-media/Cnnnn/): report.json (checked, whitelisted fields) and report.md (the same as readable text). The chunk's row in 00-inventory/chunks.json
gets a `report` field (status done|failed|running, model, seconds, cost, attempts, error); a report is current while its source signature matches the chunk's files.
The reporter never changes the chunk's own stages: a failed report leaves the chunk `done`.

Commands: `report` (make or redo reports now, several at once). The watcher (`watch`) queues a report after every ingested chunk and catches up on the ones that are missing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from cc_common import (CC_HOME, cfg_get, chunk_dir, fail, fmt_hms, load_chunks, load_state, now_iso, out, read_json, resolve_run, run_paths, say,
                       write_json, write_text)

REPORT_SCHEMA = "cc-report/1"
ROLE_FILE = CC_HOME / "reference" / "reporter.md"
DEFAULTS = {"enabled": True, "model": "claude-haiku-5-5", "effort": "high", "parallel": 2, "timeout_s": 420, "max_turns": 30, "max_attempts": 2,
            "claude_bin": "", "setting_sources": "project"}
EFFORTS = ("high", "xhigh", "max")           # never low or medium (the user's standing rule for Haiku sessions)


# --------------------------------------------------------------------------- settings and the claude CLI

def report_cfg() -> dict:
    c = {**DEFAULTS, **(cfg_get("report", {}) or {})}
    if os.environ.get("CC_REPORT") in ("0", "off", "false"):
        c["enabled"] = False
    if os.environ.get("CC_REPORT_PARALLEL"):
        c["parallel"] = int(os.environ["CC_REPORT_PARALLEL"])
    if os.environ.get("CC_REPORT_TIMEOUT"):
        c["timeout_s"] = float(os.environ["CC_REPORT_TIMEOUT"])
    if str(c.get("effort")).lower() not in EFFORTS:
        c["effort"] = "high"
    c["parallel"] = max(1, int(c["parallel"]))
    return c


def find_claude(cfg: dict | None = None) -> tuple:
    """(path, is_exe): the real claude.exe first. The npm `claude.cmd` shim goes through cmd.exe, which cuts a command at 8191 characters, so with a shim the
    reporter's brief travels on stdin instead of the command line."""
    cfg = cfg or report_cfg()
    cands = [os.environ.get("CC_CLAUDE_BIN"), cfg.get("claude_bin")]
    appdata = os.environ.get("APPDATA")
    if appdata:
        cands.append(str(Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"))
    cands += [shutil.which("claude.exe"), shutil.which("claude"), shutil.which("claude.cmd")]
    for c in cands:
        if c and Path(c).is_file():
            return str(c), str(c).lower().endswith(".exe")
    return None, False


# --------------------------------------------------------------------------- what the reporter reads

def inputs(run: Path, cid: str) -> dict:
    cd = chunk_dir(run, cid)
    sheets = sorted((cd / "sheets").glob("sheet-*.jpg")) if (cd / "sheets").is_dir() else []
    d = {"digest": cd / "digest.json", "transcript": cd / "transcript.txt", "timeline": cd / "timeline.md", "audio": cd / "audio-profile.json",
         "chunk_json": cd / "chunk.json", "chat": cd / "chat.json", "overview": cd / "sheets" / "overview.jpg"}
    present = {k: p for k, p in d.items() if p.is_file()}
    return {"files": present, "sheets": sheets}


def must_open(inp: dict) -> list:
    """Every file the reporter has to open: the pictures first, then the text and numbers (the chat only when the chunk has one)."""
    f = inp["files"]
    order = ["overview"] + [s.name for s in inp["sheets"]] + ["timeline", "transcript", "digest", "audio", "chunk_json", "chat"]
    paths = []
    for k in order:
        if k in f:
            paths.append(f[k])
        else:
            m = next((s for s in inp["sheets"] if s.name == k), None)
            if m:
                paths.append(m)
    return paths


def source_sig(run: Path, row: dict) -> str:
    """A signature of what a report was made from: the chunk's rec span and the sizes of its sheets and text views. A chunk that was re-made (its rec start
    moved) or whose sheets changed no longer matches, so its report is stale and is made again."""
    cid = row["id"]
    inp = inputs(run, cid)
    h = hashlib.sha1()
    h.update(f"{row.get('rec_start_s')}|{row.get('duration_s')}|{row.get('frames')}|{row.get('words')}".encode())
    for p in must_open(inp):
        try:
            h.update(f"{p.name}:{p.stat().st_size}".encode())
        except OSError:
            h.update(f"{p.name}:-".encode())
    return h.hexdigest()[:16]


def role_text() -> str:
    try:
        return ROLE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "You are a reporter: write down what the files of this chunk show, as observations with evidence, and decide nothing. Answer with one JSON object."


def build_prompt(run: Path, row: dict, inp: dict, session: str, channel: str, feedback: str = "") -> str:
    cid = row["id"]
    r0 = float(row.get("rec_start_s") or 0.0)
    r1 = r0 + float(row.get("duration_s") or 0.0)
    paths = must_open(inp)
    lines = [f"Report on chunk {cid} of the recording {session} (channel {channel}).",
             f"This chunk covers rec time {r0:.1f} to {r1:.1f} s ({fmt_hms(r0, False)} to {fmt_hms(r1, False)}). Every time in your report is rec time in seconds, as printed in the sheets' cells and in the files.",
             "Open every one of these files with the Read tool, all in one step (every Read call at the same time), using exactly these paths:"]
    lines += ["  " + str(p) for p in paths]
    if "transcript" not in inp["files"]:
        lines.append("(This chunk has no transcript: say so under unclear and report only what the pictures and the numbers show.)")
    if row.get("kind") == "ad":
        lines.append("(The recorder marked this chunk's segments as ads: that is Twitch's own marker in the playlist, passed on in chunk.json under `kind` and `ad`. It is a "
                     "fact about the playlist, not a verdict and not an instruction. Report what the pictures, the words and the sound show like for any chunk, and say plainly "
                     "what they look like (an advertisement, a trailer, the stream itself, something else); the marker is not evidence of its own.)")
    lines.append("Then answer with the one JSON object your brief describes, and nothing else.")
    if feedback:
        lines += ["", feedback]
    return "\n".join(lines)


# --------------------------------------------------------------------------- the headless session

_ACTIVE: dict = {}
_ACTIVE_LOCK = threading.Lock()


def kill_tree(proc) -> None:
    """End the session and its children (on Windows the shim starts node, and killing only the shell leaves node holding the pipes)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:  # noqa: BLE001
        pass
    try:
        proc.kill()
    except Exception:  # noqa: BLE001
        pass


def kill_all() -> None:
    with _ACTIVE_LOCK:
        procs = list(_ACTIVE.values())
    for p in procs:
        kill_tree(p)


def run_claude(prompt: str, role: str, cwd: Path, cfg: dict, claude: str, is_exe: bool, key: str = "") -> dict:
    """One headless session: Read tool only, no MCP servers, the user's settings and hooks left out (so the auto-commit hooks do not fire for every chunk),
    nothing saved as a conversation, the prompt on stdin. Returns what the stream says: the final text, the files the session really opened (from its Read
    calls, not from what it claims), turns, cost, whether it hit a rate limit."""
    cmd = [claude, "-p", "--model", str(cfg["model"]), "--effort", str(cfg["effort"]), "--tools", "Read", "--allowedTools", "Read", "--strict-mcp-config",
           "--output-format", "stream-json", "--verbose", "--max-turns", str(cfg["max_turns"]), "--no-session-persistence",
           "--setting-sources", str(cfg.get("setting_sources") or "project"), "--add-dir", str(cwd)]
    stdin_text = prompt
    if is_exe:
        cmd += ["--append-system-prompt", role]
    else:
        stdin_text = role + "\n\n---\n\n" + prompt
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    env = {**os.environ, "CC_REPORTER": "1"}
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(cwd), creationflags=flags, env=env)
    with _ACTIVE_LOCK:
        _ACTIVE[key or str(proc.pid)] = proc
    try:
        so, se = proc.communicate(input=stdin_text.encode("utf-8"), timeout=float(cfg["timeout_s"]))
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        raise RuntimeError(f"the reporter session ran longer than {int(float(cfg['timeout_s']))} s and its process tree was ended")
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE.pop(key or str(proc.pid), None)
    res = {"opened": [], "result": None, "num_turns": None, "cost_usd": 0.0, "is_error": False, "subtype": None, "rate_limited": False, "returncode": proc.returncode,
           "seconds": round(time.time() - t0, 1), "stderr": (se or b"").decode("utf-8", "replace").strip()[-400:], "events": 0}
    for raw in (so or b"").decode("utf-8", "replace").splitlines():
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        res["events"] += 1
        kind = ev.get("type")
        if kind == "assistant":
            for blk in (ev.get("message") or {}).get("content") or []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use" and blk.get("name") == "Read":
                    fp = (blk.get("input") or {}).get("file_path")
                    if fp:
                        res["opened"].append(str(fp))
        elif kind == "rate_limit_event":
            info = ev.get("rate_limit_info") or ev
            if str(info.get("status") or "").lower() in ("rejected", "blocked", "exceeded"):
                res["rate_limited"] = True
        elif kind == "result":
            res["result"] = ev.get("result")
            res["num_turns"] = ev.get("num_turns")
            res["cost_usd"] = float(ev.get("total_cost_usd") or 0.0)
            res["is_error"] = bool(ev.get("is_error"))
            res["subtype"] = ev.get("subtype")
    return res


def json_of(text) -> dict | None:
    """The one JSON object in the session's answer (it may be fenced or have a stray line before it)."""
    if not isinstance(text, str):
        return None
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        o = json.loads(s[i:j + 1])
    except ValueError:
        return None
    return o if isinstance(o, dict) else None


# --------------------------------------------------------------------------- what is kept (a whitelist: no verdict fields survive)

def _s(v, n: int = 2000) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:n]


def _t(v):
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def _list(v) -> list:
    return v if isinstance(v, list) else []


def clean_report(obj: dict) -> tuple:
    """(report fields, dropped): only the fields of the schema are kept. A field the brief does not ask for (a score, a highlight list, a keep/skip) is dropped and
    counted, never stored. Nothing is judged here: the whitelist is the format."""
    dropped_fields = sorted(set(obj) - {"look", "sound", "speech", "chat", "seen_and_heard", "unclear"})
    dropped_entries = 0

    def entries(name, keys):
        nonlocal dropped_entries
        res = []
        for e in _list(obj.get(name)):
            if not isinstance(e, dict):
                dropped_entries += 1
                continue
            dropped_entries += len(set(e) - set(keys))
            res.append(e)
        return res
    rep = {"look": [], "sound": [], "speech": [], "chat": [], "seen_and_heard": [], "unclear": []}
    def as_dict(x, key):                    # a bare string where an object was asked for is kept as that object's text
        return x if isinstance(x, dict) else ({key: x} if isinstance(x, str) else None)
    for e in entries("look", ("sheet", "rec_from", "rec_to", "shows", "changes", "text")):
        texts = [d for d in (as_dict(x, "text") for x in _list(e.get("text"))) if d]
        rep["look"].append({"sheet": _s(e.get("sheet"), 40), "rec_from": _t(e.get("rec_from")), "rec_to": _t(e.get("rec_to")), "shows": _s(e.get("shows")),
                            "changes": _s(e.get("changes"), 800),
                            "text": [{"text": _s(x.get("text"), 400), "where": _s(x.get("where"), 100), "cells": _s(x.get("cells"), 40)} for x in texts]})
    for e in entries("sound", ("rec_from", "rec_to", "what")):
        rep["sound"].append({"rec_from": _t(e.get("rec_from")), "rec_to": _t(e.get("rec_to")), "what": _s(e.get("what"), 800)})
    for e in entries("speech", ("rec_from", "rec_to", "about", "lines")):
        lines = [d for d in (as_dict(x, "text") for x in _list(e.get("lines"))) if d]
        rep["speech"].append({"rec_from": _t(e.get("rec_from")), "rec_to": _t(e.get("rec_to")), "about": _s(e.get("about"), 800),
                              "lines": [{"rec": _t(x.get("rec")), "text": _s(x.get("text"), 500)} for x in lines]})
    for e in entries("chat", ("rec_from", "rec_to", "what")):
        rep["chat"].append({"rec_from": _t(e.get("rec_from")), "rec_to": _t(e.get("rec_to")), "what": _s(e.get("what"), 800)})
    for e in entries("seen_and_heard", ("rec", "what", "evidence")):
        rep["seen_and_heard"].append({"rec": _t(e.get("rec")), "what": _s(e.get("what"), 800), "evidence": [_s(x, 120) for x in _list(e.get("evidence"))]})
    rep["unclear"] = [_s(x, 500) for x in _list(obj.get("unclear")) if _s(x)]
    for name, key in (("look", "rec_from"), ("sound", "rec_from"), ("speech", "rec_from"), ("chat", "rec_from"), ("seen_and_heard", "rec")):
        rep[name].sort(key=lambda e: (e.get(key) is None, e.get(key) or 0.0))        # time order, whatever order the session wrote them in
    return rep, {"fields": dropped_fields, "entry_fields": dropped_entries}


def time_warnings(rep: dict, r0: float, r1: float) -> list:
    """Format facts about the times the reporter gave: how many fall outside the chunk's rec span (a chunk offset written instead of a rec time)."""
    bad = 0
    total = 0
    for sec, keys in (("look", ("rec_from", "rec_to")), ("sound", ("rec_from", "rec_to")), ("speech", ("rec_from", "rec_to")), ("chat", ("rec_from", "rec_to")), ("seen_and_heard", ("rec",))):
        for e in rep.get(sec, []):
            for k in keys:
                v = e.get(k)
                if v is None:
                    continue
                total += 1
                if v < r0 - 1.0 or v > r1 + 1.0:
                    bad += 1
    return [f"{bad} of {total} times lie outside the chunk's rec span {r0:.1f} to {r1:.1f} s"] if bad else []


def render_md(rep: dict) -> str:
    mb = rep.get("made_by") or {}
    L = [f"# Report on chunk {rep.get('chunk')} (rec {fmt_hms(rep.get('rec_from'), False)} to {fmt_hms(rep.get('rec_to'), False)})", "",
         f"Written by {mb.get('model')} from the chunk's sheets, audio numbers, transcript and chat. Observations only: it decides nothing, names are as printed or transcribed, "
         f"and what it could not read is listed under Unclear.",
         f"Opened {len(mb.get('opened') or [])} files" + (f"; NOT opened: {', '.join(mb['not_opened'])}" if mb.get("not_opened") else "") + ".", ""]

    def tr(a, b):
        return f"{fmt_hms(a, False)}-{fmt_hms(b, False)}" if a is not None and b is not None else "?"
    L.append("## What the pictures show")
    for e in rep.get("look", []):
        bits = [f"- {e['sheet'] or 'sheet'} ({tr(e['rec_from'], e['rec_to'])}): {e['shows']}"]
        if e.get("changes"):
            bits.append(f"changes: {e['changes']}")
        for x in e.get("text") or []:
            bits.append(f"text \"{x['text']}\"" + (f" ({x['where']}" + (f", cells {x['cells']}" if x.get("cells") else "") + ")" if x.get("where") else ""))
        L.append(" | ".join(bits))
    none = ["- (nothing reported)"]
    L += ["", "## Sound (what the numbers show)"]
    L += [f"- {tr(e['rec_from'], e['rec_to'])}: {e['what']}" for e in rep.get("sound", [])] or none
    L += ["", "## Speech (from the transcript)"]
    for e in rep.get("speech", []):
        L.append(f"- {tr(e['rec_from'], e['rec_to'])}: {e['about']}")
        L += [f"  - {fmt_hms(x['rec'], False) if x.get('rec') is not None else '?'} \"{x['text']}\"" for x in e.get("lines") or []]
    if not rep.get("speech"):
        L += none
    L += ["", "## Chat"]
    L += [f"- {tr(e['rec_from'], e['rec_to'])}: {e['what']}" for e in rep.get("chat", [])] or none
    L += ["", "## Seen and heard (neutral sentences with evidence)"]
    L += [f"- {e['rec']:.1f} s: {e['what']}" + (f" [{'; '.join(e['evidence'])}]" if e.get("evidence") else "") for e in rep.get("seen_and_heard", []) if e.get("rec") is not None] or none
    L += ["", "## Unclear (could not be read or told)"]
    L += [f"- {x}" for x in rep.get("unclear", [])] or none
    if rep.get("warnings"):
        L += ["", "## Format warnings"] + [f"- {w}" for w in rep["warnings"]]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- one chunk

def set_row_report(run: Path, cid: str, info: dict | None) -> None:
    from cc_proc import mutate_rows

    def fn(rows):
        for r in rows:
            if r["id"] == cid:
                if info is None:
                    r.pop("report", None)
                else:
                    r["report"] = {**(r.get("report") or {}), **info}
    mutate_rows(run, fn)


def current_report(run: Path, row: dict) -> dict | None:
    """The chunk's report when it exists and was made from the chunk as it is now."""
    j = read_json(chunk_dir(run, row["id"]) / "report.json")
    if isinstance(j, dict) and j.get("schema") == REPORT_SCHEMA and (j.get("made_by") or {}).get("source_sig") == source_sig(run, row):
        return j
    return None


def eligible(row: dict) -> bool:
    """A chunk can be reported on once it has its pictures (sheets), its audio numbers and its text views (digest). The transcript is not required: a chunk
    made with --skip-whisper (or whose speech-to-text failed) is reported without speech, and its report goes stale, and is made again, when the transcript arrives."""
    st = (row or {}).get("stages") or {}
    return all(st.get(s) is True for s in ("sheets", "audio", "digest"))


def report_state(run: Path, row: dict) -> str:
    """done | stale | running | failed | missing (facts about the files; the watcher and `status` use it)."""
    if not eligible(row):
        return "n/a"
    if current_report(run, row):
        return "done"
    if (chunk_dir(run, row["id"]) / "report.json").is_file():
        return "stale"
    rp = row.get("report") or {}
    if rp.get("status") == "running":
        try:                                              # a `running` note older than the sessions' time limits is a watcher that died: the report is missing again
            import datetime as dt
            age = (dt.datetime.now().astimezone() - dt.datetime.fromisoformat(str(rp.get("started_at")))).total_seconds()
        except (TypeError, ValueError):
            age = 1e9
        limit = float(report_cfg()["timeout_s"]) * int(report_cfg()["max_attempts"]) + 120
        return "running" if age < limit else "missing"
    return "failed" if rp.get("status") == "failed" else "missing"


def needs_report(run: Path, row: dict, cfg: dict, ignore_attempts: bool = False) -> bool:
    st = report_state(run, row)
    if st in ("done", "n/a", "running"):
        return False
    if st == "failed" and not ignore_attempts and int((row.get("report") or {}).get("attempts") or 0) >= int(cfg["max_attempts"]):
        return False
    return True


def make_report(run: Path, cid: str, force: bool = False, cfg: dict | None = None) -> dict:
    """Make (or redo) one chunk's report. Never raises: {ok, chunk, status, ...}. The chunk's own status is never touched."""
    run = Path(run)
    cfg = cfg or report_cfg()
    row = next((r for r in load_chunks(run) if r["id"] == cid), None)
    if not row:
        return {"ok": False, "chunk": cid, "error": "no such chunk"}
    if not eligible(row):
        return {"ok": False, "chunk": cid, "error": "the chunk has no sheets, audio numbers and text views yet (its processing is not finished)"}
    if not force and current_report(run, row):
        return {"ok": True, "chunk": cid, "status": "current", "note": "the report is current"}
    claude, is_exe = find_claude(cfg)
    attempts_before = int((row.get("report") or {}).get("attempts") or 0)
    if not claude:
        err = "the claude CLI was not found (put claude.exe on PATH, or set config report.claude_bin)"
        set_row_report(run, cid, {"status": "failed", "error": err, "attempts": attempts_before + 1, "at": now_iso()})
        return {"ok": False, "chunk": cid, "status": "failed", "error": err}
    st = load_state(run)
    inp = inputs(run, cid)
    if not inp["sheets"] or "overview" not in inp["files"]:
        err = "the chunk has no sheets to report on"
        set_row_report(run, cid, {"status": "failed", "error": err, "attempts": attempts_before + 1, "at": now_iso()})
        return {"ok": False, "chunk": cid, "status": "failed", "error": err}
    sig = source_sig(run, row)
    need = [str(p) for p in must_open(inp)]
    role = role_text()
    set_row_report(run, cid, {"status": "running", "started_at": now_iso(), "model": cfg["model"]})
    feedback, last_err, total_cost, turns, t_all = "", None, 0.0, 0, time.time()
    log_lines = []
    for attempt in range(1, int(cfg["max_attempts"]) + 1):
        prompt = build_prompt(run, row, inp, st.get("session") or run.name, st.get("channel") or "channel", feedback)
        try:
            res = run_claude(prompt, role, chunk_dir(run, cid), cfg, claude, is_exe, key=f"{run.name}/{cid}")
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {str(e)[:240]}"
            log_lines.append(f"attempt {attempt}: {last_err}")
            feedback = ""
            continue
        total_cost += res["cost_usd"]
        turns = int(res["num_turns"] or 0)
        opened = {os.path.normcase(os.path.abspath(p)) for p in res["opened"]}
        not_opened = [Path(p).name for p in need if os.path.normcase(os.path.abspath(p)) not in opened]
        log_lines.append(f"attempt {attempt}: turns {res['num_turns']}, cost {res['cost_usd']:.4f}, {res['seconds']} s, opened {len(opened)}, not opened {not_opened}, "
                         f"rate_limited {res['rate_limited']}, subtype {res['subtype']}, stderr {res['stderr'][:160]!r}")
        if res["result"] is None:
            last_err = ("rate limited: " if res["rate_limited"] else "") + f"the session gave no answer (exit {res['returncode']}): {res['stderr'][:160]}"
            if res["rate_limited"]:
                break
            continue
        if res["is_error"]:
            last_err = ("rate limited: " if res["rate_limited"] else "the session ended in an error: ") + _s(res["result"], 200)
            if res["rate_limited"]:
                break
            continue
        obj = json_of(res["result"])
        if obj is None:
            last_err = "the answer was not one JSON object"
            feedback = "Your last answer was not one JSON object. Answer again with only the JSON object of your brief, nothing before or after it."
            continue
        if not_opened and attempt < int(cfg["max_attempts"]):
            last_err = "files were not opened: " + ", ".join(not_opened[:6])
            feedback = ("You did not open these files: " + ", ".join(not_opened) + ". Open them with the Read tool now (exact paths are listed above), look at every one, then answer with the JSON object.")
            continue
        rep, dropped = clean_report(obj)
        r0 = float(row.get("rec_start_s") or 0.0)
        r1 = r0 + float(row.get("duration_s") or 0.0)
        rep.update({"schema": REPORT_SCHEMA, "chunk": cid, "rec_from": round(r0, 3), "rec_to": round(r1, 3), "channel": st.get("channel"),
                    "made_by": {"model": cfg["model"], "effort": cfg["effort"], "at": now_iso(), "seconds": round(time.time() - t_all, 1), "cost_usd": round(total_cost, 4),
                                "num_turns": turns, "attempts": attempt, "opened": sorted({Path(p).name for p in res["opened"]}), "not_opened": not_opened, "source_sig": sig},
                    "warnings": time_warnings(rep, r0, r1) + ([f"files not opened by the reporter: {', '.join(not_opened)}"] if not_opened else []), "dropped": dropped})
        order = ["schema", "chunk", "channel", "rec_from", "rec_to", "made_by", "warnings", "dropped", "look", "sound", "speech", "chat", "seen_and_heard", "unclear"]
        rep = {k: rep[k] for k in order if k in rep}
        cd = chunk_dir(run, cid)
        write_json(cd / "report.json", rep)
        write_text(cd / "report.md", render_md(rep))
        info = {"status": "done", "model": cfg["model"], "at": rep["made_by"]["at"], "seconds": rep["made_by"]["seconds"], "cost_usd": rep["made_by"]["cost_usd"],
                "attempts": attempts_before + attempt, "error": None, "not_opened": not_opened, "source_sig": sig}
        set_row_report(run, cid, info)
        _log(run, cid, log_lines + ["done"])
        return {"ok": True, "chunk": cid, "status": "done", "seconds": info["seconds"], "cost_usd": info["cost_usd"], "attempts": attempt, "not_opened": not_opened,
                "dropped": dropped}
    set_row_report(run, cid, {"status": "failed", "error": last_err, "attempts": attempts_before + int(cfg["max_attempts"]), "at": now_iso(), "seconds": round(time.time() - t_all, 1),
                              "cost_usd": round(total_cost, 4)})
    _log(run, cid, log_lines + [f"failed: {last_err}"])
    return {"ok": False, "chunk": cid, "status": "failed", "error": last_err, "cost_usd": round(total_cost, 4)}


def _log(run: Path, cid: str, lines: list) -> None:
    try:
        d = run_paths(run)["logs"]
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"report-{cid}.log", "a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}]\n" + "\n".join(lines) + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------- the queue (the watcher's background jobs)

class Reporter:
    """Report jobs that run beside chunk processing: at most `parallel` sessions at once, a job never blocks or fails a chunk. Daemon threads: stopping the
    watcher ends them, and their sessions are ended with kill_all()."""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or report_cfg()
        self.q: queue.Queue = queue.Queue()
        self.queued: set = set()
        self.lock = threading.Lock()
        self.threads: list = []
        self.results: list = []

    def _start(self) -> None:
        while len(self.threads) < self.cfg["parallel"]:
            t = threading.Thread(target=self._worker, daemon=True, name=f"cc-report-{len(self.threads) + 1}")
            t.start()
            self.threads.append(t)

    def enqueue(self, run: Path, cid: str, force: bool = False) -> bool:
        key = (str(run), cid, bool(force))
        with self.lock:
            if any(k[:2] == key[:2] for k in self.queued):
                return False
            self.queued.add(key)
        self.q.put(key)
        self._start()
        return True

    def _worker(self) -> None:
        while True:
            key = self.q.get()
            run, cid, force = Path(key[0]), key[1], key[2]
            try:
                res = make_report(run, cid, force=force, cfg=self.cfg)
            except Exception as e:  # noqa: BLE001
                res = {"ok": False, "chunk": cid, "error": f"{type(e).__name__}: {e}"}
            res["run"] = run.name
            with self.lock:
                self.results.append(res)
                self.queued.discard(key)
            try:
                say(f"[report] {run.name} {cid}: {res.get('status') or ('ok' if res.get('ok') else 'failed')}"
                    + (f" in {res['seconds']} s, ${res.get('cost_usd', 0):.3f}" if res.get("seconds") else "") + (f" ({res['error']})" if res.get("error") else ""))
            except Exception:  # noqa: BLE001
                pass
            self.q.task_done()

    def catch_up(self, runs, ignore_attempts: bool = False) -> int:
        n = 0
        for run in runs:
            for row in load_chunks(run):
                if needs_report(Path(run), row, self.cfg, ignore_attempts) and self.enqueue(Path(run), row["id"]):
                    n += 1
        return n

    def pending(self) -> int:
        return self.q.unfinished_tasks

    def join(self, timeout: float | None = None) -> bool:
        end = None if timeout is None else time.time() + timeout
        while self.q.unfinished_tasks:
            if end is not None and time.time() > end:
                return False
            time.sleep(0.5)
        return True

    def summary(self) -> dict:
        with self.lock:
            done = [r for r in self.results if r.get("ok")]
            bad = [r for r in self.results if not r.get("ok")]
        return {"done": len(done), "failed": [{"run": r.get("run"), "chunk": r.get("chunk"), "error": r.get("error")} for r in bad],
                "cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in self.results), 4), "pending": self.pending()}


# --------------------------------------------------------------------------- the command

def cmd_report(a):
    run = resolve_run(a.run)
    cfg = report_cfg()
    if a.parallel:
        cfg["parallel"] = max(1, int(a.parallel))
    rows = load_chunks(run)
    done_rows = [r for r in rows if eligible(r)]
    wanted = {c.strip().upper() for part in (a.chunk or []) for c in str(part).split(",") if c.strip()}
    unknown = sorted(wanted - {r["id"] for r in rows})
    force = bool(a.force or a.all)
    if wanted:
        targets = [r for r in done_rows if r["id"] in wanted]
    elif a.all:
        targets = done_rows
    else:                                                  # the default: every processed chunk whose report is missing, stale or failed
        targets = [r for r in done_rows if needs_report(run, r, cfg, ignore_attempts=True)]
    states = {r["id"]: report_state(run, r) for r in targets}
    todo = [r for r in targets if force or states[r["id"]] != "done"]
    if a.dry_run:
        out({"ok": True, "run": str(run), "would_report": [r["id"] for r in todo], "states": states, "unknown": unknown,
             "claude": find_claude(cfg)[0], "model": cfg["model"], "parallel": cfg["parallel"]})
    claude, _ = find_claude(cfg)
    if not claude and todo:
        fail("the claude CLI was not found (put claude.exe on PATH, or set config report.claude_bin)", 3)
    t0 = time.time()
    rep = Reporter(cfg)
    for r in todo:
        rep.enqueue(run, r["id"], force=force)
    rep.join()
    s = rep.summary()
    todo_ids = {r["id"] for r in todo}
    current = [r["id"] for r in done_rows if r["id"] not in todo_ids and report_state(run, r) == "done"]
    out({"ok": not s["failed"], "run": str(run), "requested": [r["id"] for r in todo], "reported": s["done"], "failed": s["failed"], "already_current": current,
         "unknown": unknown, "cost_usd": s["cost_usd"], "seconds": round(time.time() - t0, 1), "model": cfg["model"], "parallel": cfg["parallel"]}, 0 if not s["failed"] else 1)


def register(sub) -> None:
    p = sub.add_parser("report", help="make the chunks' reports now (a headless Haiku session per chunk reads its sheets, audio numbers, transcript and chat; observations only)")
    p.add_argument("--run", required=True)
    p.add_argument("--chunk", action="append", help="a chunk id or a comma list (repeatable); default: every chunk without a current report")
    p.add_argument("--all", action="store_true", help="every processed chunk, redoing the ones that have a current report too")
    p.add_argument("--force", action="store_true", help="redo the named chunks even though their report is current")
    p.add_argument("--parallel", type=int, help="sessions at once (default config report.parallel)")
    p.add_argument("--dry-run", action="store_true", help="only list what would be reported")
    p.set_defaults(func=cmd_report)
