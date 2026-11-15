"""Chat heat: how busy the audience was, in 4-second bins of rec time, against this stream's own normal. Numbers only: nothing here says a moment is good.

The user, 2026-11-15: count the live comments every 4 seconds, find where the chat peaks, let the agents give those parts priority and a little score, but never pick a part only because of its
peak. This module is the first half of that (the facts); `reference/chat-heat.md` is the second half (how the agents weigh them). Scripts gather, agents decide: no row, flag or order here
is a verdict, the burst list is a filter with settings in config.json -> chat that the caller can change, and nothing downstream reads it by itself.

Input: the chunks' `chat.json` (`tcr-chat/1`: messages per second, already shifted by the recorder's `lag_hint_s` so second i of the file is second i of the chunk; the top tokens per 10 s,
counted over all messages; up to 120 sampled messages; no user names). Ad-marked chunks have no chat file.

  heat --run RUN                          build 20-analysis/heat.json and heat.md (the series, the per-chunk table, the bursts) and print a summary
  heat --run RUN --from T --to T [--rows] the numbers for one rec span: messages, the bins, the peak, the bursts inside, what chat said (tokens, sample lines); --rows adds the heat.md rows of the span's chunks and bursts
  heat --run RUN --coverage BLOCK.json    which bursts of a block file no moment, unit, non-play span or heat_review entry mentions (facts for the main session)

Each bin: n (messages in the 4 s), base (the median of the bins within +-half_bins around it, only covered bins), ratio = (n+1)/(base+1), z = (n-base)/sqrt(base+1), pct = where its z stands
among all the run's bins (0-100). A burst = bins with z >= burst_min_z and n >= burst_min_n, merged when close, widened while z stays >= onset_z. z is a size-adjusted excess, not a p-value (chat is burstier than Poisson).
Bins with no data are `null`: before the run's first message (chat not connected yet), inside a stretch of exact zeros of at least dropout_min_s while the stream's median is at least
dropout_min_median (a capture dropout, listed under capture.gaps), and the chunks that have no chat file (ad-marked ones).
"""
from __future__ import annotations

import argparse
import bisect
import math
import statistics
from collections import Counter
from pathlib import Path

from cc_common import cfg_get, chunk_dir, fail, fmt_hms, load_chunks, load_state, now_iso, out, parse_time, read_json, resolve_run, run_paths, write_json, write_text

SCHEMA = "cc-heat/1"
DEFAULTS = {"bin_s": 4, "baseline_half_bins": 37, "burst_min_z": 4.0, "burst_min_n": 5, "burst_merge_bins": 2, "onset_z": 1.5, "max_extend_bins": 6,
            "hot_z": 2.0, "min_cover": 0.875, "dropout_min_s": 30, "dropout_min_median": 3.0, "after_ad_s": 90, "samples_per_burst": 6, "tokens_per_burst": 8,
            "coverage_pad_s": 8}


def params(**over) -> dict:
    """config.json -> chat over the defaults, then the caller's own values (None = not given)."""
    p = dict(DEFAULTS)
    cfg = cfg_get("chat", {}) or {}
    for k in DEFAULTS:
        if k in cfg:
            p[k] = cfg[k]
    for k, v in over.items():
        if v is not None:
            p[k] = v
    return p


def _rows(run: Path) -> list:
    rows = [r for r in load_chunks(run) if r.get("duration_s") and r.get("rec_start_s") is not None]
    rows.sort(key=lambda r: float(r["rec_start_s"]))
    return rows


def _load_chats(run: Path, rows: list) -> tuple:
    """({chunk id: chat dict}, [{chunk, why}] for the chunks with no usable chat)."""
    chats, missing = {}, []
    for r in rows:
        cid = r["id"]
        if r.get("kind") == "ad":
            missing.append({"chunk": cid, "why": "ad-marked chunk (the recorder saves no chat for it)"})
            continue
        chat = read_json(chunk_dir(run, cid) / "chat.json")
        if chat is None:
            missing.append({"chunk": cid, "why": "no chat file"})
        elif not chat.get("per_second"):
            missing.append({"chunk": cid, "why": "empty chat file"})
        else:
            chats[cid] = chat
    return chats, missing


# --------------------------------------------------------------------------- the series

def build_series(rows: list, chats: dict, P: dict) -> dict:
    """The run-wide series in bins of P['bin_s'] seconds of rec time. A chunk's 1 s counts are spread over the bins they overlap (chunk starts are fractional), so no bin loses or doubles a second."""
    bin_s = float(P["bin_s"])
    total = max(float(r["rec_start_s"]) + float(r["duration_s"]) for r in rows)
    nb = int(math.ceil(total / bin_s - 1e-9))
    cnt, cov = [0.0] * nb, [0.0] * nb
    first_msg = None
    for r in rows:
        chat = chats.get(r["id"])
        if not chat:
            continue
        rec0, dur = float(r["rec_start_s"]), float(r["duration_s"])
        for i, v in enumerate(chat["per_second"]):
            a = rec0 + i
            if a >= rec0 + dur - 1e-9:
                break
            b = min(a + 1.0, rec0 + dur)
            if v and first_msg is None:
                first_msg = a
            k0, k1 = int(a // bin_s), int((b - 1e-9) // bin_s)
            for k in range(k0, min(k1, nb - 1) + 1):
                ov = min(b, (k + 1) * bin_s) - max(a, k * bin_s)
                if ov > 0:
                    cnt[k] += float(v) * ov
                    cov[k] += ov
    n = [(cnt[k] * bin_s / cov[k]) if cov[k] >= float(P["min_cover"]) * bin_s else None for k in range(nb)]
    if first_msg is not None:                 # before the first message the chat was not connected yet: no data, not a quiet chat
        for k in range(nb):
            if (k + 1) * bin_s <= first_msg + 1e-9:
                n[k] = None
    covered = [x for x in n if x is not None]
    gaps = []
    if covered and statistics.median(covered) >= float(P["dropout_min_median"]):
        need = max(2, int(math.ceil(float(P["dropout_min_s"]) / bin_s)))
        k = 0
        while k < nb:
            if n[k] == 0:
                j = k
                while j + 1 < nb and n[j + 1] == 0:
                    j += 1
                if j - k + 1 >= need:
                    gaps.append({"rec_from": round(k * bin_s, 2), "rec_to": round((j + 1) * bin_s, 2), "seconds": round((j - k + 1) * bin_s, 1),
                                 "why": "no message at all for this long while the chat is normally busy: the chat capture stopped, it is not a quiet chat"})
                    for q in range(k, j + 1):
                        n[q] = None
                k = j + 1
            else:
                k += 1
    covered = [x for x in n if x is not None]
    run_median = statistics.median(covered) if covered else 0.0
    half = int(P["baseline_half_bins"])
    base, z, ratio = [None] * nb, [None] * nb, [None] * nb
    for k in range(nb):
        if n[k] is None:
            continue
        w = [x for x in n[max(0, k - half):k + half + 1] if x is not None]
        base[k] = statistics.median(w) if len(w) >= 5 else run_median
        z[k] = (n[k] - base[k]) / math.sqrt(base[k] + 1.0)
        ratio[k] = (n[k] + 1.0) / (base[k] + 1.0)
    zs = sorted(x for x in z if x is not None)
    pct = [None] * nb
    for k in range(nb):
        if z[k] is not None:
            pct[k] = 100.0 * (bisect.bisect_left(zs, z[k]) + bisect.bisect_right(zs, z[k])) / 2.0 / len(zs)
    return {"bin_s": bin_s, "nb": nb, "total_s": total, "n": n, "base": base, "ratio": ratio, "z": z, "pct": pct, "first_msg_rec": first_msg, "gaps": gaps,
            "covered": covered, "run_median": run_median}


# --------------------------------------------------------------------------- bursts

def _ad_ends(rows: list) -> list:
    return sorted(float(r["rec_start_s"]) + float(r["duration_s"]) for r in rows if r.get("kind") == "ad")


def _chunk_of(rows: list, t: float):
    for r in rows:
        a, d = float(r["rec_start_s"]), float(r["duration_s"])
        if a - 1e-6 <= t < a + d - 1e-6:
            return r["id"], round(t - a, 2)
    return None, None


def tokens_in(rows: list, chats: dict, t0: float, t1: float, top: int) -> tuple:
    """(top tokens [[token, count]], messages that start with '!' by token) of the 10 s windows overlapping [t0, t1): counted over ALL messages by the recorder."""
    tk = Counter()
    for r in rows:
        chat = chats.get(r["id"])
        if not chat:
            continue
        rec0 = float(r["rec_start_s"])
        for j, bucket in enumerate(chat.get("tokens_per_10s") or []):
            a = rec0 + 10 * j
            if a < t1 and a + 10 > t0:
                for tok, c in bucket:
                    tk[tok] += int(c)
    commands = Counter({t: c for t, c in tk.items() if str(t).startswith("!")})
    return [[t, c] for t, c in tk.most_common(top)], [[t, c] for t, c in commands.most_common(3)], sum(commands.values())


def samples_in(rows: list, chats: dict, t0: float, t1: float, k: int) -> list:
    """Up to k of the sampled messages typed in [t0, t1), evenly spread (a sample: the recorder keeps at most 120 per chunk)."""
    found = []
    for r in rows:
        chat = chats.get(r["id"])
        if not chat:
            continue
        rec0 = float(r["rec_start_s"])
        for s in chat.get("samples") or []:
            t = rec0 + float(s.get("t", 0))
            if t0 <= t < t1:
                found.append({"rec": round(t, 1), "text": " ".join(str(s.get("text", "")).split())[:160]})
    found.sort(key=lambda x: x["rec"])
    if len(found) <= k:
        return found
    step = len(found) / float(k)
    return [found[int(i * step)] for i in range(k)]


def words_in(rows: list, chats: dict, t0: float, t1: float) -> tuple:
    """(how many sampled messages, mean words per message) of the samples typed in [t0, t1): short messages are people reacting, long ones are people talking about something else."""
    k = w = 0
    for r in rows:
        chat = chats.get(r["id"])
        if not chat:
            continue
        rec0 = float(r["rec_start_s"])
        for s in chat.get("samples") or []:
            if t0 <= rec0 + float(s.get("t", 0)) < t1:
                k += 1
                w += len(str(s.get("text", "")).split())
    return k, (round(w / k, 2) if k else None)


def find_bursts(S: dict, rows: list, chats: dict, P: dict) -> list:
    bin_s, nb, n, z = S["bin_s"], S["nb"], S["n"], S["z"]
    thr, min_n, gap = float(P["burst_min_z"]), float(P["burst_min_n"]), int(P["burst_merge_bins"])
    onz, maxext = float(P["onset_z"]), int(P["max_extend_bins"])
    core = [k for k in range(nb) if z[k] is not None and z[k] >= thr and n[k] >= min_n]
    groups = []
    for k in core:
        if groups and k - groups[-1]["e"] <= gap:
            groups[-1]["e"] = k
            groups[-1]["cores"].append(k)
        else:
            groups.append({"s": k, "e": k, "cores": [k]})
    for g in groups:
        o = g["s"]
        while g["s"] - o < maxext and o - 1 >= 0 and z[o - 1] is not None and z[o - 1] >= onz:
            o -= 1
        f = g["e"]
        while f - g["e"] < maxext and f + 1 < nb and z[f + 1] is not None and z[f + 1] >= onz:
            f += 1
        g["o"], g["f"] = o, f
    merged = []
    for g in groups:                            # two bursts whose widened spans touch are one continuing hot stretch
        if merged and g["o"] <= merged[-1]["f"] + 1:
            merged[-1]["e"], merged[-1]["f"] = g["e"], max(merged[-1]["f"], g["f"])
            merged[-1]["cores"] += g["cores"]
        else:
            merged.append(g)
    ad_ends = _ad_ends(rows)
    bursts = []
    for i, g in enumerate(merged, 1):
        pk = max(g["cores"], key=lambda q: z[q])
        o_rec, e_rec, p_rec = g["o"] * bin_s, (g["f"] + 1) * bin_s, pk * bin_s
        msgs = sum(n[q] for q in range(g["o"], g["f"] + 1) if n[q] is not None)
        tokens, commands, cmd_total = tokens_in(rows, chats, o_rec, e_rec, int(P["tokens_per_burst"]))
        cid, off = _chunk_of(rows, p_rec)
        prev_ad = [t for t in ad_ends if t <= o_rec + 1e-6]
        after_ad = round(o_rec - prev_ad[-1], 1) if prev_ad and o_rec - prev_ad[-1] <= float(P["after_ad_s"]) else None
        top = tokens[0][1] if tokens else 0
        sample_n, avg_words = words_in(rows, chats, o_rec, e_rec)
        bursts.append({"id": f"H{i:03d}", "chunk": cid, "peak_offset_s": off, "onset_rec": round(o_rec, 2), "peak_rec": round(p_rec, 2), "end_rec": round(e_rec, 2),
                       "core_from": round(g["s"] * bin_s, 2), "core_to": round((g["e"] + 1) * bin_s, 2), "span_s": round(e_rec - o_rec, 1), "rise_s": round(p_rec - o_rec, 1),
                       "n_peak": round(n[pk], 1), "base": round(S["base"][pk], 1), "ratio": round(S["ratio"][pk], 2), "z": round(z[pk], 2), "pct": round(S["pct"][pk], 1),
                       "msgs": round(msgs, 0), "tokens": tokens, "command_tokens": cmd_total, "commands": commands,
                       "top_token_per_msg": round(top / msgs, 2) if msgs else None, "sample_n": sample_n, "avg_words": avg_words, "after_ad_s": after_ad,
                       "samples": samples_in(rows, chats, o_rec, e_rec, int(P["samples_per_burst"]))})
    return bursts


# --------------------------------------------------------------------------- the whole build

def _rd(x, nd=2):
    return None if x is None else round(x, nd)


def chunk_table(rows: list, chats: dict, missing: dict, S: dict, bursts: list, P: dict) -> list:
    bin_s = S["bin_s"]
    table = []
    for r in rows:
        cid, rec0, dur = r["id"], float(r["rec_start_s"]), float(r["duration_s"])
        ks = [k for k in range(S["nb"]) if rec0 - 1e-6 <= k * bin_s < rec0 + dur - 1e-6 and S["n"][k] is not None]
        chat = chats.get(cid)
        msgs = int(sum(chat["per_second"])) if chat else None
        row = {"chunk": cid, "rec_from": round(rec0, 2), "rec_to": round(rec0 + dur, 2), "msgs": msgs, "msgs_per_s": round(msgs / dur, 2) if (msgs is not None and dur) else None,
               "note": missing.get(cid), "median_n": None, "max_n": None, "max_n_rec": None, "max_z": None, "max_z_rec": None, "hot_share": None,
               "bursts": sum(1 for b in bursts if b["chunk"] == cid)}
        if ks:
            ns = [S["n"][k] for k in ks]
            kmax = max(ks, key=lambda k: S["n"][k])
            zmax = max(ks, key=lambda k: S["z"][k])
            row.update({"median_n": _rd(statistics.median(ns), 1), "max_n": _rd(S["n"][kmax], 1), "max_n_rec": round(kmax * bin_s, 2), "max_z": _rd(S["z"][zmax]),
                        "max_z_rec": round(zmax * bin_s, 2), "hot_share": round(sum(1 for k in ks if S["z"][k] >= float(P["hot_z"])) / len(ks), 3)})
        table.append(row)
    return table


def build(run: Path, P: dict) -> dict:
    rows = _rows(run)
    if not rows:
        fail("no processed chunk in this run (run the processor first)")
    chats, miss = _load_chats(run, rows)
    base = {"schema": SCHEMA, "created": now_iso(), "run": str(run), "params": P, "lag_hint_s": next((c.get("lag_hint_s") for c in chats.values() if c.get("lag_hint_s") is not None), None),
            "chunks_used": [r["id"] for r in rows]}
    if not chats:
        base.update({"has_chat": False, "why": "no chunk of this run has a chat file with messages (chat capture off, or the stream's chat was empty): there is no heat to read",
                     "capture": {"first_msg_rec": None, "gaps": [], "no_chat_chunks": miss}, "stream": None, "series": None, "chunks": [], "bursts": []})
        return base
    S = build_series(rows, chats, P)
    if S["first_msg_rec"] is None or not S["covered"]:
        base.update({"has_chat": False, "why": "the chat files hold no message at all", "capture": {"first_msg_rec": None, "gaps": [], "no_chat_chunks": miss},
                     "stream": None, "series": None, "chunks": [], "bursts": []})
        return base
    bursts = find_bursts(S, rows, chats, P)
    cov = S["covered"]
    cs = sorted(cov)
    msgs_total = sum(int(sum(c["per_second"])) for c in chats.values())
    stream = {"bins": S["nb"], "bin_s": S["bin_s"], "covered_bins": len(cov), "covered_s": round(len(cov) * S["bin_s"], 1), "msgs": msgs_total,
              "msgs_per_s": round(sum(cov) / (len(cov) * S["bin_s"]), 2), "median_n": round(statistics.median(cov), 1), "p90_n": round(cs[int(0.9 * (len(cs) - 1))], 1),
              "p99_n": round(cs[int(0.99 * (len(cs) - 1))], 1), "max_n": round(cs[-1], 1), "avg_words": words_in(rows, chats, 0.0, float("inf"))[1], "bursts": len(bursts)}
    mdict = {m["chunk"]: m["why"] for m in miss}
    base.update({"has_chat": True, "stream": stream,
                 "capture": {"first_msg_rec": round(S["first_msg_rec"], 2), "gaps": S["gaps"], "no_chat_chunks": miss},
                 "series": {"start_rec": 0.0, "bin_s": S["bin_s"], "n": [_rd(x) for x in S["n"]], "base": [_rd(x) for x in S["base"]], "z": [_rd(x) for x in S["z"]]},
                 "chunks": chunk_table(rows, chats, mdict, S, bursts, P), "bursts": bursts})
    return base


# --------------------------------------------------------------------------- the files

def _cell(x, n=60) -> str:
    return " ".join(str(x).replace("|", "/").split())[:n]


CHUNK_HEAD = ["| chunk | rec range | msgs | msgs/s | median/bin | max/bin (at) | max z (at) | hot share | bursts |", "|---|---|---|---|---|---|---|---|---|"]
BURST_HEAD = ["| id | chunk | onset-end | peak | n vs base | ratio | z | pct | msgs | words/msg | chat says | notes |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]


def chunk_line(c: dict) -> str:
    rng = f"{fmt_hms(c['rec_from'], False)}-{fmt_hms(c['rec_to'], False)}"
    if c["msgs"] is None:
        return f"| {c['chunk']} | {rng} | - | - | - | - | - | - | {c['note'] or 'no chat'} |"
    return (f"| {c['chunk']} | {rng} | {c['msgs']} | {c['msgs_per_s']} | {c['median_n']} | {c['max_n']} ({fmt_hms(c['max_n_rec'], False)}) | "
            f"{c['max_z']} ({fmt_hms(c['max_z_rec'], False)}) | {c['hot_share']} | {c['bursts']} |")


def burst_line(b: dict) -> str:
    notes = []
    if b["after_ad_s"] is not None:
        notes.append(f"{b['after_ad_s']:g} s after an ad-marked chunk")
    if b["command_tokens"]:
        notes.append("commands " + ", ".join(f"{t} x{c}" for t, c in b["commands"]))
    if b["top_token_per_msg"] is not None and b["top_token_per_msg"] >= 0.5:
        notes.append(f"top token x{b['top_token_per_msg']:g} per message")
    says = ", ".join(f"{t} x{c}" for t, c in b["tokens"][:5])
    return (f"| {b['id']} | {b['chunk'] or '-'} | {fmt_hms(b['onset_rec'], False)}-{fmt_hms(b['end_rec'], False)} | {fmt_hms(b['peak_rec'], False)} | {b['n_peak']:g} vs {b['base']:g} | "
            f"{b['ratio']:g} | {b['z']:g} | {b['pct']:g} | {b['msgs']:g} | {'-' if b['avg_words'] is None else b['avg_words']} | {_cell(says, 70)} | {_cell('; '.join(notes), 70)} |")


def heat_md(h: dict, state: dict) -> str:
    P = h["params"]
    L = [f"# Chat heat: {state.get('session')} ({state.get('channel')})", "",
         f"The audience's messages counted in {P['bin_s']}-second bins of rec time, each bin against this stream's own normal (the median of the bins within about "
         f"{int(P['baseline_half_bins']) * int(P['bin_s'])} s around it). Numbers only: no row says a moment is good, and nothing here picks or drops one. "
         "`z` = (n - base) / sqrt(base + 1), a size-adjusted excess (not a p-value); `ratio` = (n + 1) / (base + 1); `pct` = where the bin's z stands among all the run's bins (0 to 100); "
         "`hot share` = the share of a chunk's bins with z of at least " + f"{P['hot_z']:g}" + ". How to read it: `CC/reference/chat-heat.md`. All times are rec time.", ""]
    if not h.get("has_chat"):
        return "\n".join(L + [f"**No heat: {h.get('why')}.**", ""]) + "\n"
    s, cap = h["stream"], h["capture"]
    L += [f"Stream: {s['bins']} bins, {s['covered_s'] / 60:.1f} min covered, {s['msgs']} messages ({s['msgs_per_s']}/s), per bin: median {s['median_n']}, p90 {s['p90_n']}, p99 {s['p99_n']}, max {s['max_n']}; "
          f"{s['avg_words']} words per sampled message over the whole run. "
          f"Chat first seen at {fmt_hms(cap['first_msg_rec'], False)}; the recorder already moved the chat {h.get('lag_hint_s')} s back so that second i of a chunk's chat is second i of the chunk.", ""]
    if cap["gaps"]:
        L.append("Capture gaps (no message at all while the chat is normally busy; left out of every number): " + "; ".join(
            f"{fmt_hms(g['rec_from'], False)}-{fmt_hms(g['rec_to'], False)} ({g['seconds']:g} s)" for g in cap["gaps"]) + ".")
    if cap["no_chat_chunks"]:
        L.append("Chunks with no chat: " + ", ".join(f"{m['chunk']} ({m['why']})" for m in cap["no_chat_chunks"]) + ".")
    L += ["", "## Per chunk", ""] + CHUNK_HEAD
    L += [chunk_line(c) for c in h["chunks"]]
    L += ["", f"## Bursts ({len(h['bursts'])}): n >= {P['burst_min_n']:g} and z >= {P['burst_min_z']:g}, merged when {int(P['burst_merge_bins']) * int(P['bin_s'])} s apart or less, widened while z stays >= {P['onset_z']:g}", "",
          "`onset-end` is the widened span, `peak` its highest bin. `chat says` = the top tokens of the 10 s windows over the span, counted over all messages. The cause is rarely at the peak: "
          "read from about 14 s before the onset (chat reacts after the event, and sometimes the streamer is reacting to chat). `T heat --run RUN --from T --to T` gives the numbers, tokens and sample lines of any span.", "",
          "`words/msg` = mean words per sampled message in the span (at most 120 messages are sampled per chunk): short ones are people reacting, long ones people talking about something else.", "",
          ] + BURST_HEAD
    L += [burst_line(b) for b in h["bursts"]]
    if not h["bursts"]:
        L.append("| (none at these settings) | | | | | | | | | | | |")
    return "\n".join(L) + "\n"


def paths(run: Path) -> tuple:
    a = run_paths(run)["analysis"]
    return a / "heat.json", a / "heat.md"


def _write(run: Path, h: dict) -> None:
    jp, mp = paths(run)
    jp.parent.mkdir(parents=True, exist_ok=True)
    write_json(jp, h, indent=None)
    write_text(mp, heat_md(h, load_state(run)))


def load_heat(run: Path):
    return read_json(paths(run)[0])


def burst_ids_in(run: Path, t0: float, t1: float) -> list:
    """The ids of the bursts whose peak lies in [t0, t1) from the run's heat.json ([] when there is none): for `T blocks`."""
    h = load_heat(run)
    return [b["id"] for b in (h or {}).get("bursts", []) if t0 <= float(b["peak_rec"]) < t1]


# --------------------------------------------------------------------------- one span

def span_view(run: Path, h: dict, rows: list, chats: dict, t0: float, t1: float, P: dict) -> dict:
    s = h["series"]
    bin_s = float(s["bin_s"])
    k0, k1 = int(t0 // bin_s), int((t1 - 1e-9) // bin_s)
    bins = []
    for k in range(max(0, k0), min(k1, len(s["n"]) - 1) + 1):
        bins.append({"rec": round(k * bin_s, 2), "n": s["n"][k], "base": s["base"][k], "z": s["z"][k]})
    have = [b for b in bins if b["n"] is not None]
    tokens, commands, cmd_total = tokens_in(rows, chats, t0, t1, int(P["tokens_per_burst"]))
    res = {"rec_from": round(t0, 2), "rec_to": round(t1, 2), "bins": len(bins), "covered_bins": len(have),
           "msgs": round(sum(b["n"] for b in have), 0) if have else None, "n_mean": round(statistics.mean(b["n"] for b in have), 1) if have else None,
           "stream_median_n": h["stream"]["median_n"], "tokens": tokens, "command_tokens": cmd_total, "samples": samples_in(rows, chats, t0, t1, int(P["samples_per_burst"]))}
    res["sample_n"], res["avg_words"] = words_in(rows, chats, t0, t1)
    res["stream_avg_words"] = h["stream"].get("avg_words")
    if have:
        pk = max(have, key=lambda b: b["z"])
        res.update({"peak_rec": pk["rec"], "n_peak": pk["n"], "base_at_peak": pk["base"], "z_peak": pk["z"], "n_max": max(b["n"] for b in have),
                    "ratio_peak": _rd((pk["n"] + 1) / (pk["base"] + 1)), "pct_peak": None})
        zs = sorted(x for x in s["z"] if x is not None)
        res["pct_peak"] = round(100.0 * (bisect.bisect_left(zs, pk["z"]) + bisect.bisect_right(zs, pk["z"])) / 2.0 / len(zs), 1)
    res["bursts"] = [b["id"] for b in h["bursts"] if float(b["onset_rec"]) < t1 and float(b["end_rec"]) > t0]
    return res


def _span_text(res: dict) -> list:
    L = [f"heat {fmt_hms(res['rec_from'], False)}-{fmt_hms(res['rec_to'], False)}: {res['covered_bins']} of {res['bins']} bins with data, "
         f"{'-' if res['msgs'] is None else int(res['msgs'])} messages, mean {res['n_mean']} per bin (stream median {res['stream_median_n']})"]
    if res.get("peak_rec") is not None:
        L.append(f"peak bin {fmt_hms(res['peak_rec'], False)}: n {res['n_peak']:g} vs base {res['base_at_peak']:g}, ratio {res['ratio_peak']}, z {res['z_peak']}, pct {res['pct_peak']}")
    L.append("bursts inside: " + (", ".join(res["bursts"]) or "none"))
    if res["tokens"]:
        L.append("chat says: " + ", ".join(f"{t} x{c}" for t, c in res["tokens"]))
    if res["command_tokens"]:
        L.append(f"messages that are commands (start with !): {res['command_tokens']}")
    if res["avg_words"] is not None:
        L.append(f"words per sampled message: {res['avg_words']} over {res['sample_n']} sampled messages (the whole run: {res['stream_avg_words']})")
    for smp in res["samples"]:
        L.append(f"sample {fmt_hms(smp['rec'], False)}: {smp['text']}")
    return L


# --------------------------------------------------------------------------- coverage of a block file

def coverage(h: dict, block: dict, P: dict) -> dict:
    t0, t1 = float(block.get("rec_from") or 0), float(block.get("rec_to") or 0)
    pad = float(P["coverage_pad_s"])
    spans = []
    for key in ("moments", "units", "extras", "non_play"):
        for it in block.get(key) or []:
            a = it.get("setup_from", it.get("rec_from")) if key == "moments" else it.get("rec_from")
            b = it.get("rec_to")
            if a is not None and b is not None:
                spans.append((float(a), float(b), key, it.get("id")))
    review_ids, review_recs = set(), []
    for it in block.get("heat_review") or []:
        if it.get("burst"):
            review_ids.add(str(it["burst"]))
        if it.get("rec") is not None:
            review_recs.append(float(it["rec"]))
    for key in ("moments", "units", "extras"):         # a moment or unit that names the burst it was built on
        for it in block.get(key) or []:
            hb = (it.get("heat") or it.get("chat_peak") or {})
            if isinstance(hb, dict) and hb.get("burst"):
                review_ids.add(str(hb["burst"]))
    inside, covered, un = [], [], []
    for b in h["bursts"]:
        if not (t0 <= float(b["peak_rec"]) < t1):
            continue
        inside.append(b["id"])
        by = None
        if b["id"] in review_ids:
            by = "named"
        elif any(float(b["onset_rec"]) <= r <= float(b["end_rec"]) + pad for r in review_recs):
            by = "heat_review rec"
        else:
            for a, e, key, ident in spans:
                if float(b["onset_rec"]) <= e + pad and float(b["peak_rec"]) >= a:
                    by = f"{key} {ident or ''}".strip()
                    break
        if by:
            covered.append({"id": b["id"], "by": by})
        else:
            un.append({"id": b["id"], "peak_rec": b["peak_rec"], "onset_rec": b["onset_rec"], "z": b["z"], "n_peak": b["n_peak"], "base": b["base"]})
    return {"rec_from": t0, "rec_to": t1, "bursts_in_block": inside, "covered": covered, "unmentioned": un}


# --------------------------------------------------------------------------- the command

def cmd_heat(a):
    run = resolve_run(a.run)
    P = params(burst_min_z=a.min_z, burst_min_n=a.min_n)
    if a.coverage:
        h = load_heat(run)
        if not h:
            h = build(run, params())
            _write(run, h)
        if not h.get("has_chat"):
            out({"ok": True, "has_chat": False, "unmentioned": [], "note": h.get("why")})
        block = read_json(a.coverage)
        if block is None:
            fail(f"cannot read the block file {a.coverage}")
        if a.min_z is not None or a.min_n is not None:               # another setting: the same series, other bursts
            rows = _rows(run)
            chats, _ = _load_chats(run, rows)
            S = build_series(rows, chats, P)
            h = dict(h, bursts=find_bursts(S, rows, chats, P))
        res = coverage(h, block, P)
        for u in res["unmentioned"]:
            print(f"unmentioned {u['id']}: peak {fmt_hms(u['peak_rec'], False)} (onset {fmt_hms(u['onset_rec'], False)}), n {u['n_peak']:g} vs base {u['base']:g}, z {u['z']:g}")
        out({"ok": True, "has_chat": True, **res})
    if a.from_ is not None or a.to is not None:
        h = load_heat(run)
        if not h:
            h = build(run, params())
            _write(run, h)
        if not h.get("has_chat"):
            out({"ok": True, "has_chat": False, "note": h.get("why")})
        rows = _rows(run)
        t0 = parse_time(a.from_, rows) if a.from_ is not None else 0.0
        t1 = parse_time(a.to, rows) if a.to is not None else float(h["series"]["bin_s"]) * len(h["series"]["n"])
        if t1 <= t0:
            fail("--to must be after --from")
        chats, _ = _load_chats(run, rows)
        res = span_view(run, h, rows, chats, t0, t1, P)
        for line in _span_text(res):
            print(line)
        if a.rows:                                    # the heat.md rows of the span (a long stream's heat.md is long: an agent reads its own block's rows only)
            cs = [c for c in h["chunks"] if c["rec_from"] < t1 and c["rec_to"] > t0]
            bs = [b for b in h["bursts"] if float(b["onset_rec"]) < t1 and float(b["end_rec"]) > t0]
            print("\nper chunk:")
            print("\n".join(CHUNK_HEAD + [chunk_line(c) for c in cs]))
            print("\nbursts:")
            print("\n".join(BURST_HEAD + [burst_line(b) for b in bs] if bs else ["(none in this span)"]))
        out({"ok": True, "has_chat": True, **res})
    h = build(run, P)
    _write(run, h)
    jp, mp = paths(run)
    if not h["has_chat"]:
        out({"ok": True, "has_chat": False, "why": h["why"], "heat_md": str(mp), "heat_json": str(jp)})
    s = h["stream"]
    out({"ok": True, "has_chat": True, "bins": s["bins"], "covered_min": round(s["covered_s"] / 60, 1), "msgs": s["msgs"], "msgs_per_s": s["msgs_per_s"], "median_n": s["median_n"],
         "p99_n": s["p99_n"], "bursts": s["bursts"], "capture_gaps": len(h["capture"]["gaps"]), "no_chat_chunks": [m["chunk"] for m in h["capture"]["no_chat_chunks"]],
         "heat_md": str(mp), "heat_json": str(jp), "settings": {k: P[k] for k in ("bin_s", "baseline_half_bins", "burst_min_z", "burst_min_n", "burst_merge_bins", "onset_z")}})


def register(sub) -> None:
    p = sub.add_parser("heat", help="the chat counted in 4-second bins of rec time against the stream's own normal: heat.json/heat.md with the bursts; --from/--to for one span; --coverage for a block file (numbers only)")
    p.add_argument("--run", required=True)
    p.add_argument("--from", dest="from_", help="a rec span's start: print the heat numbers, tokens and sample lines of the span")
    p.add_argument("--to", help="the span's end")
    p.add_argument("--rows", action="store_true", help="with --from/--to: also print the heat.md rows of the chunks and bursts in the span (a block's rows without reading the whole heat.md)")
    p.add_argument("--coverage", metavar="BLOCK_JSON", help="a block file: list the bursts of its rec range that no moment, unit, non-play span or heat_review entry mentions")
    p.add_argument("--min-z", type=float, help="list bursts from this z (default config.json chat.burst_min_z, 4)")
    p.add_argument("--min-n", type=float, help="and at least this many messages in the peak bin (default config.json chat.burst_min_n, 5)")
    p.set_defaults(func=cmd_heat)
