#!/usr/bin/env python
"""PostToolUse / PostToolUseFailure hook for the Higgsfield generation tools.

When a Higgsfield answer looks like a flag (a moderation or policy block, a job refused or refunded, an upload or video marked nsfw /
ip_checking / failed, a preset notice, a tool error) the raw answer is saved in Loupe as a *capture*, the moment it came back.  The flag
record (`atp.py caught-flag add`) later attaches that capture, so the flag keeps Higgsfield's exact words even when the agent paraphrases.
The hook only gathers: it decides nothing about the flag, never blocks a call, and prints at most one short reminder for the agent.
Loupe unreachable -> the capture waits in loupe/data/outbox/ and is ingested on its next start.
"""
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CLAUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CLAUDE / "loupe"))

HARD = [("nsfw", r"\bnsfw\b"), ("ip_checking", r"ip_checking"), ("moderation", r"moderat"),
        ("policy", r"content[ _-]?polic|policy[ _-]?violat|violates? (our|the) "), ("blocked", r"\bblocked\b|\brefus(ed|al)\b|\bwithheld\b|\brejected\b"),
        ("preset_notice", r"preset_recommendation")]
SOFT = [("refunded", r"\brefund"), ("failed", r'"status"\s*:\s*"(failed|error|canceled|cancelled)"|\bstatus[:=]\s*(failed|error)\b|\bjob failed\b|\bgeneration failed\b|\bfailed (after|within|in) \d')]
VALIDATION = re.compile(r"insufficient|not enough credits|out of credits|too long|exceeds? .{0,40}(characters|limit|maximum)|must be (between|at least|one of)|"
                        r"invalid (parameter|argument|value)|unknown model|schema|required (field|parameter)|not authenticated|authentication|unauthori[sz]ed|rate limit", re.I)
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


# (library folder, environment override, toolkit script)
LIBS = [("analyze-then-pick", "ATP_HOME", "atp.py"), ("analyze-then-generate", "ATG_HOME", "atg.py")]


def active_run() -> tuple[str, str]:
    """(run name, toolkit script) of the run whose state.json changed most recently (within 36 h, in either library), as a hint only;
    the agent names the run when it records the flag."""
    best, best_t, script = "", 0.0, ""
    for folder, env, tool in LIBS:
        home = Path(os.environ.get(env) or CLAUDE / folder)
        for p in (home / "runs").glob("*/state.json"):
            if p.parent.name.startswith("client-fixes"):
                continue
            try:
                t = p.stat().st_mtime
            except OSError:
                continue
            if t > best_t:
                best, best_t, script = p.parent.name, t, tool
    return (best, script) if best and time.time() - best_t < 36 * 3600 else ("", "")


def flat(o) -> str:
    if isinstance(o, str):
        return o
    try:
        return json.dumps(o, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(o)


def strings_of(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            strings_of(v, out)
    elif isinstance(o, list):
        for v in o:
            strings_of(v, out)
    return out


def main():
    try:
        ev = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    tool = ev.get("tool_name", "")
    is_fail = ev.get("hook_event_name") == "PostToolUseFailure" or "error" in ev
    resp = ev.get("error") if is_fail and "tool_response" not in ev else ev.get("tool_response")
    text = flat(resp)
    # the prompt/inputs are echoed back by some answers: do not let words of our own prompt look like a refusal
    scan = text
    for s in strings_of(ev.get("tool_input"), []):
        if len(s) > 24:
            scan = scan.replace(s, " ").replace(json.dumps(s, ensure_ascii=False)[1:-1], " ")
    low = scan.lower()
    sig = [n for n, rx in HARD if re.search(rx, low)]
    soft = [n for n, rx in SOFT if re.search(rx, low)]
    if is_fail:
        if VALIDATION.search(low) and not sig:
            return
        sig = (sig + soft) or ["tool-error"]
    else:
        sig = sig + soft
        if not sig:
            return
    key = hashlib.sha1((tool + "|" + text[:6000]).encode("utf-8", "replace")).hexdigest()

    import loupe_client as lc
    state = lc.DATA / "hook-state.json"
    try:
        seen = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = []
    if key in seen:
        return
    run, script = active_run()
    ids = list(dict.fromkeys(UUID.findall(text)))[:6]
    doc = {"ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "tool": tool.replace("mcp__higgsfield__", ""), "run": run,
           "agent": str(ev.get("agent_id") or ev.get("agent_type") or "")[:60] or "main", "session": str(ev.get("session_id", ""))[:12],
           "job": ids[0] if ids else "", "signals": sig,
           "summary": ("signals: " + ", ".join(sig) + (" | ids: " + ", ".join(ids) if ids else ""))[:400],
           "tool_input": flat(ev.get("tool_input"))[:6000], "response": text[:12000], "failure": bool(is_fail)}
    st, _d = lc.call("POST", "/api/captures", doc, key_name="pipeline", timeout=3)
    cid = _d.get("id") if st == 200 and isinstance(_d, dict) else None
    if st == 0:
        lc.queue("capture", doc)
    elif st != 200:
        return
    try:
        state.write_text(json.dumps((seen + [key])[-300:]), encoding="utf-8")
    except OSError:
        pass
    if run:
        where = f"capture {cid}" if cid else "queued capture"
        note = (f"Loupe saved Higgsfield's raw answer ({where}; signals: {', '.join(sig)}). If this is a flag of run {run}, record it with "
                f"`{script} caught-flag add --run {run} --video NN --attempt aK` before changing the request (the capture attaches itself by job id"
                f"{', or --capture ' + str(cid) if cid else ''}).")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": ev.get("hook_event_name") or "PostToolUse", "additionalContext": note}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001  a hook must never get in the way of a generation
        pass
