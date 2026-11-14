"""Text views of a chunk and of the stream: transcript.txt, timeline.md, digest.json, stream-meta.json, stream.md, and `window`.

Numbers only. Nothing here ranks a moment as a highlight: the footer lists plain percentiles and the largest values with their times.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import Counter
from pathlib import Path

import numpy as np

from cc_common import (ad_batches, chunk_dir, fmt_hms, load_chunks, read_json, write_json, write_text)


# --------------------------------------------------------------------------- loading

def load_data(run: Path, cid: str) -> dict:
    d = chunk_dir(run, cid)
    return {"audio": read_json(d / "audio.json"), "profile": read_json(d / "audio-profile.json"), "frames": read_json(d / "frames.json"),
            "transcript": read_json(d / "transcript.json"), "chat": read_json(d / "chat.json"), "probe": read_json(d / "probe.json"),
            "sidecar": read_json(d / "chunk.json")}


def local_clock(iso: str | None) -> str:
    if not iso:
        return "-"
    try:
        t = dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return t.astimezone().strftime("%H:%M")
    except ValueError:
        return "-"


# --------------------------------------------------------------------------- per second

def _loud_in_second(audio: dict | None, s: int):
    if not audio or audio.get("no_audio") or not audio.get("rms_db"):
        return None
    win = float(audio.get("window_s") or 0.5)
    rms = audio["rms_db"]
    k0, k1 = int(s / win), int((s + 1 - 1e-9) / win)
    seg = rms[min(k0, len(rms) - 1):min(k1, len(rms) - 1) + 1]
    return max(seg) if seg else None


def second_rows(duration: float, data: dict) -> list:
    """One dict per second of the chunk: words starting in it, the loudest 0.5 s window, mean frame difference, chat count."""
    n = int(math.ceil(max(0.0, duration) - 1e-6))
    words = [[] for _ in range(n)]
    tr = data.get("transcript") or {}
    for seg in tr.get("segments") or []:
        ws = seg.get("words") or []
        if ws:
            for w in ws:
                s = int(w["s"])
                if 0 <= s < n:
                    words[s].append(w["w"])
        else:
            s = int(seg.get("start", 0))
            if 0 <= s < n and seg.get("text"):
                words[s].append(seg["text"])
    motion = [[] for _ in range(n)]
    for fr in (data.get("frames") or {}).get("frames") or []:
        s = int(fr["t"])
        if 0 <= s < n and fr.get("diff_prev") is not None:
            motion[s].append(fr["diff_prev"])
    chat = (data.get("chat") or {}).get("per_second")
    rows = []
    for s in range(n):
        rows.append({"s": s, "words": " ".join(words[s]), "loud_db": _loud_in_second(data.get("audio"), s),
                     "motion": round(float(np.mean(motion[s])), 1) if motion[s] else None,
                     "chat": int(chat[s]) if chat is not None and s < len(chat) else None})
    return rows


def render_timeline_md(cid: str, rec0: float, duration: float, rows: list) -> str:
    head = [f"# {cid} per-second timeline (rec {fmt_hms(rec0)} - {fmt_hms(rec0 + duration)})", "",
            "One row per second of the chunk. speech = the words that start in that second; loudness = the largest 0.5 s RMS in dBFS in that "
            "second (-90 = silence); motion = mean absolute difference (0-255) between sheet frames starting in that second, on a 64x36 grey "
            "copy; chat = messages per second, already shifted by the chat lag (blank when no chat was recorded).", "",
            "| rec | chunk+off | speech in this second | loudness max dB | motion | chat msgs/s |", "|---|---|---|---|---|---|"]
    body = []
    for r in rows:
        speech = r["words"].replace("|", "/")
        body.append(f"| {fmt_hms(rec0 + r['s'])} | {cid} +{r['s']} | {speech} | "
                    f"{'' if r['loud_db'] is None else f'{r['loud_db']:.1f}'} | {'' if r['motion'] is None else f'{r['motion']:.1f}'} | "
                    f"{'' if r['chat'] is None else r['chat']} |")
    return "\n".join(head + body) + "\n"


def render_transcript_txt(cid: str, rec0: float, tr: dict | None) -> str:
    if not tr or not tr.get("segments"):
        return f"# {cid}: no speech transcribed" + (f" ({tr.get('note')})" if tr and tr.get("note") else "") + "\n"
    lines = []
    for s in tr["segments"]:
        lines.append(f"[{fmt_hms(rec0 + s['start'])}-{fmt_hms(rec0 + s['end'])}] ({cid} +{s['start']:.2f}) {s['text']}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- digest

def build_digest(row: dict, rec0: float, duration: float, data: dict, srows: list) -> dict:
    tr = data.get("transcript") or {}
    prof = data.get("profile") or {}
    chat = data.get("chat") or {}
    side = data.get("sidecar") or {}
    stream = (side.get("stream") or row.get("stream") or {}) if isinstance(side.get("stream") or row.get("stream") or {}, dict) else {}
    words = int(tr.get("n_words") or 0)
    speech = float(tr.get("speech_seconds") or 0.0)
    all_words = [w["w"] for s in tr.get("segments") or [] for w in s.get("words") or []]
    motions = [fr["diff_prev"] for fr in (data.get("frames") or {}).get("frames") or [] if fr.get("diff_prev") is not None]
    per = chat.get("per_second") or []
    chat_total = int(sum(per)) if per else None
    chat_max = int(max(per)) if per else None
    chat_peak = round(rec0 + int(np.argmax(per)), 2) if per else None
    tokens = Counter()
    for b in chat.get("tokens_per_10s") or []:
        for tok, n in b:
            tokens[tok] += n
    return {"chunk": row["id"], "rec_start_s": round(rec0, 3), "duration_s": round(duration, 3), "words": words,
            "speech_seconds": round(speech, 2), "wpm": round(words / (duration / 60), 1) if duration else None,
            "wpm_speech_only": tr.get("wpm_speech_only"), "speech_share": round(speech / duration, 3) if duration else None,
            "language": tr.get("language"), "rms_mean_db": prof.get("rms_mean_db"), "rms_max_db": prof.get("rms_max_db"),
            "loud_jumps": len(prof.get("loud_jumps") or []) if prof else None,
            "motion_mean": round(float(np.mean(motions)), 2) if motions else None, "motion_max": round(float(max(motions)), 2) if motions else None,
            "chat_total": chat_total, "chat_max_per_s": chat_max, "chat_peak_rec": chat_peak,
            "top_tokens": [[t, n] for t, n in tokens.most_common(8)], "first_words": " ".join(all_words[:25]),
            "last_words": " ".join(all_words[-25:]), "title": stream.get("title"), "game": stream.get("game"), "viewers": stream.get("viewers"),
            "ads_skipped_s": side.get("ads_skipped_s", row.get("ads_skipped_s")), "gap_before_s": side.get("gap_before_s", row.get("gap_before_s"))}


# --------------------------------------------------------------------------- stream-level

def build_stream_meta(run: Path, rows: list, state: dict) -> dict:
    per, changes = [], []
    prev = {}
    for r in sorted(rows, key=lambda x: x["index"]):
        st = r.get("stream") or {}
        per.append({"chunk": r["id"], "rec_start_s": r.get("rec_start_s"), "t0_utc": r.get("t0_utc"), "title": st.get("title"),
                    "game": st.get("game"), "viewers": st.get("viewers"), "uptime_s": st.get("uptime_s"), "stream_id": st.get("id")})
        for field in ("title", "game"):
            v = st.get(field)
            if v is not None and field in prev and prev[field] != v:
                changes.append({"chunk": r["id"], "rec_start_s": r.get("rec_start_s"), "field": field, "from": prev[field], "to": v})
            if v is not None:
                prev[field] = v
    meta = {"schema": "cc/1", "channel": state.get("channel"), "session": state.get("session"),
            "session_json": read_json(Path(run) / "00-inventory" / "session.json"), "per_chunk": per, "changes": changes}
    write_json(Path(run) / "00-inventory" / "stream-meta.json", meta)
    return meta


def _pcts(vals: list) -> dict | None:
    v = [x for x in vals if x is not None]
    if not v:
        return None
    a = np.asarray(v, dtype=np.float64)
    return {"n": len(v), "p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90)),
            "max": float(a.max())}


def _top_seconds(cands: list, k: int = 10, radius: float = 5.0) -> list:
    """The k largest (rec, value, chunk, offset) with at least `radius` s between listed seconds (one long event is not ten entries)."""
    picked = []
    for c in sorted(cands, key=lambda x: -x[1]):
        if all(abs(c[0] - p[0]) >= radius for p in picked):
            picked.append(c)
            if len(picked) >= k:
                break
    return picked


def build_stream_md(run: Path, rows: list, state: dict) -> str:
    run = Path(run)
    rows = sorted(rows, key=lambda x: x["index"])
    digests, cand = {}, {"chat": [], "loud": [], "motion": []}
    for r in rows:
        cid = r["id"]
        d = read_json(chunk_dir(run, cid) / "digest.json")
        if d:
            digests[cid] = d
        rec0 = float(r.get("rec_start_s") or 0.0)
        data = load_data(run, cid)
        if not d and not data["audio"]:
            continue
        chat = (data["chat"] or {}).get("per_second") or []
        for i, v in enumerate(chat):
            cand["chat"].append((rec0 + i, float(v), cid, i))
        dur = float(r.get("duration_s") or 0)
        for s in range(int(math.ceil(dur - 1e-6))):
            lv = _loud_in_second(data["audio"], s)
            if lv is not None:
                cand["loud"].append((rec0 + s, float(lv), cid, s))
        mo = {}
        for fr in (data["frames"] or {}).get("frames") or []:
            if fr.get("diff_prev") is not None:
                mo.setdefault(int(fr["t"]), []).append(fr["diff_prev"])
        for s, v in mo.items():
            cand["motion"].append((rec0 + s, float(np.mean(v)), cid, s))
    total = sum(float(r.get("duration_s") or 0) for r in rows)
    done = sum(1 for r in rows if r.get("status") == "done")
    ad_ids = {r["id"] for r in rows if r.get("kind") == "ad"}
    head = [f"# Stream {state.get('session')} ({state.get('channel')})", "",
            f"{len(rows)} chunks ({done} done), {fmt_hms(total)} recorded. All times are rec time h:mm:ss.cc (seconds since the start of C0001, "
            "every recorded chunk counts, an ad-marked one too); `(ad-marked)` after a chunk id = the recorder passed on Twitch's own marker for its segments "
            "(a fact, not a verdict: see the section below the table); `clock` is the local wall clock of the chunk's first segment. wpm = words per minute over the whole chunk; "
            "speech % = Whisper speech seconds over the chunk's length; rms = loudness in dBFS over 0.5 s windows; loud jumps = windows 10 dB "
            "above the previous 5 s median (audio-profile.json); motion = mean frame difference 0-255; chat = messages per second (chunks "
            "without chat show -). Numbers only: no row here says a moment is good.", "",
            "| chunk | rec range | clock | title / game | words | wpm | speech % | rms mean/max dB | loud jumps | motion mean | chat total/max | ads s | gap s | first words |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    langs = {}
    for r in rows:                      # the spoken language as Whisper reported it: stream chunks only (an advertisement is in its own language)
        if r.get("language") and r.get("kind") != "ad":
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    if langs:
        w = (state.get("settings") or {}).get("whisper") or {}
        head[4:4] = ["Spoken language (Whisper's detection, a fact): " + ", ".join(f"{k} in {v} chunks" for k, v in sorted(langs.items(), key=lambda kv: -kv[1]))
                     + (f"; the run's language is {w['language_locked']} (locked from {w.get('language_locked_from')})" if w.get("language_locked") else "")
                     + ". A chunk Whisper was not sure about was transcribed in the fallback language (`language_source` in its transcript.json). Advertisements are not counted.", ""]

    def f1(x, nd=1):
        return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))
    body = []
    for r in rows:
        cid = r["id"]
        label = f"{cid} (ad-marked)" if cid in ad_ids else cid
        d = digests.get(cid)
        rng = f"{fmt_hms(r.get('rec_start_s'), cs=False)}-{fmt_hms((r.get('rec_start_s') or 0) + (r.get('duration_s') or 0), cs=False)}"
        clock = local_clock(r.get("t0_utc"))
        if not d:
            body.append(f"| {label} | {rng} | {clock} | status: {r.get('status')} {r.get('error') or ''} | | | | | | | | | | |".replace("\n", " "))
            continue
        tg = " / ".join(x for x in (str(d.get("title") or "")[:40], str(d.get("game") or "")) if x) or "-"
        sp = "-" if d.get("speech_share") is None else f"{100 * d['speech_share']:.0f}"
        chat = "-" if d.get("chat_total") is None else f"{d['chat_total']}/{d['chat_max_per_s']}"
        first = " ".join(str(d.get("first_words") or "").split()[:10]).replace("|", "/")
        body.append(f"| {label} | {rng} | {clock} | {tg.replace('|', '/')} | {d.get('words')} | {f1(d.get('wpm'), 0)} | {sp} | "
                    f"{f1(d.get('rms_mean_db'))}/{f1(d.get('rms_max_db'))} | {d.get('loud_jumps')} | {f1(d.get('motion_mean'))} | {chat} | "
                    f"{f1(d.get('ads_skipped_s'), 0)} | {f1(d.get('gap_before_s'), 0)} | {first} |")
    out = head + body
    batches = ad_batches(rows)
    if batches:
        out += ["", "## Chunks the recorder marked as ads", "",
                "Twitch's own marker for the segments of these chunks (a stitched-ad range or a title that is not `live`), passed on by the recorder: a fact, not a "
                "verdict. Nothing was skipped; the agents look at each batch (its reports, sheets and words) and decide whether it really is an ad; the batches that are "
                "are left out of every video. Consecutive chunk numbers are one batch (one ad break).", "",
                "| batch | chunks | rec range | seconds | titles |", "|---|---|---|---|---|"]
        for b in batches:
            rr = f"{fmt_hms(b['rec_from'], cs=False)}-{fmt_hms(b['rec_to'], cs=False)}" if b.get("rec_from") is not None and b.get("rec_to") is not None else "-"
            out.append(f"| {b['batch']} | {', '.join(b['chunks'])} | {rr} | {b['seconds']:.1f} | {'; '.join(b['titles']).replace('|', '/') or '-'} |")
    out += ["", "## Plain percentiles across chunks (every chunk, ad-marked ones included)", "", "| column | n | p10 | p50 | p90 | max |", "|---|---|---|---|---|---|"]
    for key, label in (("words", "words"), ("wpm", "wpm"), ("speech_share", "speech share"), ("rms_mean_db", "rms mean dB"),
                       ("rms_max_db", "rms max dB"), ("loud_jumps", "loud jumps"), ("motion_mean", "motion mean"),
                       ("chat_total", "chat total"), ("chat_max_per_s", "chat max per s")):
        p = _pcts([d.get(key) for d in digests.values()])
        out.append(f"| {label} | {p['n']} | {p['p10']:.2f} | {p['p50']:.2f} | {p['p90']:.2f} | {p['max']:.2f} |" if p else f"| {label} | 0 | | | | |")
    unit = {"chat": "msgs/s", "loud": "dB (max 0.5 s RMS)", "motion": "mean frame diff"}
    for kind, title in (("chat", "chat rate"), ("loud", "loudness"), ("motion", "motion")):
        out += ["", f"## Ten largest seconds by {title}", "(seconds within 5 s of an already listed one are skipped, so one long event is one entry)", ""]
        top = _top_seconds(cand[kind])
        if not top:
            out.append("(no data)")
        for i, (rec, v, cid, off) in enumerate(top, 1):
            out.append(f"{i}. {fmt_hms(rec)} ({cid} +{off}{', ad-marked chunk' if cid in ad_ids else ''}) {v:.1f} {unit[kind]}")
    text = "\n".join(out) + "\n"
    write_text(run / "00-inventory" / "stream.md", text)
    return text


# --------------------------------------------------------------------------- window

def window_text(run: Path, rows: list, t0: float, t1: float, what: set) -> tuple:
    """(lines, summary) for the rec span [t0, t1) across chunks: transcript, timeline, chat, audio."""
    lines, summary = [], {"chunks": [], "transcript_lines": 0, "words": 0, "seconds": 0}
    for r in sorted(rows, key=lambda x: x["index"]):
        if not r.get("duration_s"):
            continue
        rec0, dur = float(r["rec_start_s"]), float(r["duration_s"])
        if rec0 >= t1 or rec0 + dur <= t0:
            continue
        cid = r["id"]
        data = load_data(run, cid)
        summary["chunks"].append(cid)
        lines.append(f"== {cid} (rec {fmt_hms(rec0)}-{fmt_hms(rec0 + dur)}) ==")
        a, b = max(t0, rec0) - rec0, min(t1, rec0 + dur) - rec0
        if "transcript" in what:
            tr = data["transcript"]
            if tr is None:
                lines.append("(no transcript.json for this chunk)")
            else:
                n = 0
                for s in tr.get("segments") or []:
                    if s["end"] > a and s["start"] < b:
                        lines.append(f"[{fmt_hms(rec0 + s['start'])}-{fmt_hms(rec0 + s['end'])}] ({cid} +{s['start']:.2f}) {s['text']}")
                        n += 1
                        summary["words"] += len(s.get("words") or [])
                summary["transcript_lines"] += n
                if not n:
                    lines.append("(no speech in this span)")
        if "timeline" in what:
            lines.append("timeline: rec | speech | loudness max dB | motion | chat/s")
            for sr in second_rows(dur, data):
                if sr["s"] + 1 > a and sr["s"] < b:
                    lines.append(f"{fmt_hms(rec0 + sr['s'])} {cid}+{sr['s']} | {sr['words']} | "
                                 f"{'' if sr['loud_db'] is None else sr['loud_db']} | {'' if sr['motion'] is None else sr['motion']} | "
                                 f"{'' if sr['chat'] is None else sr['chat']}")
                    summary["seconds"] += 1
        if "chat" in what:
            ch = data["chat"]
            if not ch:
                lines.append("(no chat recorded for this chunk)")
            else:
                per = ch.get("per_second") or []
                lo, hi = int(a), int(math.ceil(b))
                lines.append(f"chat msgs/s from +{lo}: " + " ".join(str(v) for v in per[lo:hi]))
                for j, bucket in enumerate(ch.get("tokens_per_10s") or []):
                    if j * 10 < b and j * 10 + 10 > a:
                        lines.append(f"chat tokens +{j * 10}-{j * 10 + 10}: " + ", ".join(f"{t} {n}" for t, n in bucket))
                for smp in ch.get("samples") or []:
                    if a <= smp["t"] < b:
                        lines.append(f"chat sample +{smp['t']:.1f}: {smp['text']}")
        if "audio" in what:
            au = data["audio"]
            if not au or au.get("no_audio"):
                lines.append("(no audio in this chunk)")
            else:
                win = float(au["window_s"])
                k0, k1 = int(a / win), int(math.ceil(b / win))
                lines.append(f"audio rms dB per {win:g} s from +{k0 * win:g}: " + " ".join(f"{v:.0f}" for v in au["rms_db"][k0:k1]))
    return lines, summary
