"""create-clips game-mode helpers (used by /create-clips agents in game mode). Gather-only: they tabulate and check facts; they never judge.

Commands (times are rec times; see reference/game-clipping.md and reference/game-mining.md):
  hud-states   the changes of the score (or any counter) read by `hud-scan`, as one time-ordered table with the state after each change
  hud-slice    the readings of one hud-scan series inside a rec range, one line per change (the clock or a score near a unit)
  units-merge  the scan agents' block files as one time-ordered rounds.json (+ sensitive.json, avoid.json)
  units-verdict the planner's decisions (keep level, spans, reason, videos) written next to the cards in rounds.json
  units-check  facts about a unit file (a scan agent's block file, or rounds.json): missing fields, overlaps, spans outside their unit,
               score changes no unit holds, stretches no unit and no non_play covers, totals
  units-table  rounds.json written as a table for the user (deliverables/rounds.md): every round or fight with its keep level and why
No command here says a round started, a play was good or a unit should be kept: the agent reads the facts and decides.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from cc_common import fail, fmt_hms, load_chunks, out, parse_time, read_json, resolve_run, run_paths, write_json, write_text

UNIT_FIELDS = ("id", "kind", "rec_from", "rec_to", "impact", "impact_why", "confidence", "evidence")
SHOW = 40                       # at most this many entries of one list are printed (the file or the counts hold the rest)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _int(text):
    t = str(text).strip()
    return int(t) if re.fullmatch(r"-?\d+", t) else None


# --------------------------------------------------------------------------- hud-states

def stable_changes(rows: list, stable: int) -> list:
    """[(rec, text)]: a text counts as the series' value once `stable` samples in a row read it (the change is dated at the first of them).
    An empty read (the box hidden, an OCR miss) is skipped: it is neither a change nor a break in the run. A text that flickers for fewer
    than `stable` samples never becomes a value. The first value is the initial state."""
    found, cur, cand, n, cand_rec = [], None, None, 0, None
    for r in rows:
        t = (r.get("text") or "").strip()
        if not t:
            continue
        if t == cur:
            cand, n = None, 0
            continue
        if t == cand:
            n += 1
        else:
            cand, n, cand_rec = t, 1, r.get("rec")
        if n >= stable:
            found.append((cand_rec, cand))
            cur, cand, n = cand, None, 0
    return found


def cmd_hud_states(a):
    run = resolve_run(a.run)
    hud = run_paths(run)["analysis"] / "hud"
    names = [s.strip() for s in str(a.series).split(",") if s.strip()]
    if not names:
        fail("--series needs at least one name (the --name of a hud-scan, e.g. score_a,score_b)")
    stable = max(1, int(a.stable))
    events, per_series, odd, steps = [], {}, [], {}
    for nm in names:
        j = read_json(hud / f"{nm}.json")
        if not j or "rows" not in j:
            fail(f"no hud-scan result {hud / (nm + '.json')}: run `cc.py hud-scan --run RUN --region ... --name {nm}` first")
        steps[nm] = j.get("step")
        ch = stable_changes(j["rows"], stable)
        per_series[nm] = {"samples": len(j["rows"]), "empty_reads": sum(1 for r in j["rows"] if not (r.get("text") or "").strip()), "changes": max(0, len(ch) - 1)}
        prev = None
        for rec, text in ch:
            ev = {"rec": rec, "series": nm, "from": prev, "to": text, "initial": prev is None}
            d_from, d_to = (_int(prev) if prev is not None else None), _int(text)
            if d_from is not None and d_to is not None:
                ev["delta"] = d_to - d_from
                if ev["delta"] != 1:
                    odd.append([rec, nm, prev, text, ev["delta"]])
            events.append(ev)
            prev = text
    events.sort(key=lambda e: (e["rec"], names.index(e["series"])))
    state, rows = {}, []
    for ev in events:
        state[ev["series"]] = ev["to"]
        rows.append({**ev, "hms": fmt_hms(ev["rec"]), "state": dict(state)})
    lines = []
    for r in rows:
        s = "-".join(str(r["state"].get(n, "?")) for n in names)
        what = f"{r['series']} starts at {r['to']}" if r["initial"] else f"{r['series']} {r['from']} -> {r['to']}" + (f" ({r['delta']:+d})" if "delta" in r else "")
        lines.append(f"{r['hms']}  {what}   [{s}]")
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", a.name)
    write_json(hud / f"{name}.json", {"series": names, "stable_samples": stable, "steps_s": steps, "rows": rows}, indent=None)
    write_text(hud / f"{name}.txt", "\n".join(lines) + "\n")
    t0, t1 = _num(a.from_), _num(a.to)
    shown = [l for r, l in zip(rows, lines) if (t0 is None or r["rec"] >= t0) and (t1 is None or r["rec"] <= t1)]
    out({"ok": True, "files": [str(hud / f"{name}.json"), str(hud / f"{name}.txt")], "series": per_series, "rows": len(rows), "stable_samples": stable,
         "not_plus_one": odd[:SHOW], "not_plus_one_count": len(odd), "shown": shown[:SHOW],
         "note": "a change is dated at the first sample of the run that held for `stable` samples; empty reads are skipped. not_plus_one lists the changes that did not add exactly one "
                 "(a reset to 0 at a new map, an OCR slip, a jump): look at the frames there before trusting the series"})


# --------------------------------------------------------------------------- hud-slice

def cmd_hud_slice(a):
    run = resolve_run(a.run)
    hud = run_paths(run)["analysis"] / "hud"
    j = read_json(hud / f"{a.name}.json")
    if not j or "rows" not in j:
        fail(f"no hud-scan result {hud / (a.name + '.json')}: run `cc.py hud-scan --run RUN --spec {hud / 'regions.json'}` first")
    rows_all = j["rows"]
    chunks = load_chunks(run)
    t0 = parse_time(a.from_, chunks) if a.from_ is not None else float("-inf")
    t1 = parse_time(a.to, chunks) if a.to is not None else float("inf")
    sel = [r for r in rows_all if t0 <= float(r["rec"]) <= t1]
    shown, prev = [], object()
    for r in sel:
        t = (r.get("text") or "").strip()
        if a.all or t != prev:
            shown.append(f"{fmt_hms(float(r['rec']))}  {t if t else '(none)'}" + (f"  conf {r['conf']}" if r.get("conf") is not None and a.all else ""))
        prev = t
    cap = max(1, int(a.max))
    out({"ok": True, "name": a.name, "from": None if t0 == float("-inf") else t0, "to": None if t1 == float("inf") else t1, "samples_in_range": len(sel), "lines": len(shown),
         "truncated": len(shown) > cap, "rows": shown[:cap],
         "note": "one line per change of the text (every sample with --all); an empty read is shown as (none): the box was hidden or the OCR read nothing"})


# --------------------------------------------------------------------------- units-check

def _present(v) -> bool:
    return v is not None and v != "" and v != [] and v != {}


def _sources(run: Path, file) -> tuple:
    an = run_paths(run)["analysis"]
    if file:
        return [Path(file)], Path(file).name
    if (an / "rounds.json").is_file():
        return [an / "rounds.json"], "rounds.json"
    blocks = sorted((an / "blocks").glob("block-*.json"))
    return blocks, f"{len(blocks)} block files"


def cmd_units_check(a):
    run = resolve_run(a.run)
    srcs, label = _sources(run, a.file)
    if not srcs:
        fail("no unit file: give --file, or write rounds.json / the blocks' block-NN.json first")
    units, non_play, extras, rng, bad_files = [], [], [], None, []
    for p in srcs:
        j = read_json(p)
        if not isinstance(j, dict):
            bad_files.append(str(p))
            continue
        for u in j.get("units") or []:
            units.append({**u, "_src": p.name})
        non_play += j.get("non_play") or []
        extras += j.get("extras") or []
        if len(srcs) == 1 and _num(j.get("rec_from")) is not None and _num(j.get("rec_to")) is not None:
            rng = (float(j["rec_from"]), float(j["rec_to"]))
    chunks = [c for c in load_chunks(run) if c.get("duration_s")]
    if rng is None and chunks:
        rng = (min(c["rec_start_s"] for c in chunks), max(c["rec_start_s"] + c["duration_s"] for c in chunks))
    tol, gap = float(a.tol), float(a.gap)
    look = []
    # per-unit facts
    missing, bad_bounds, outside, ids, dups = {}, [], [], {}, []
    for u in units:
        uid = str(u.get("id") or "?")
        if uid in ids:
            dups.append(uid)
        ids[uid] = ids.get(uid, 0) + 1
        miss = [f for f in UNIT_FIELDS if not _present(u.get(f))]
        if not (_present(u.get("keep")) or _present(u.get("keep_hint"))):
            miss.append("keep|keep_hint")
        if miss:
            missing[uid] = miss
        s, e = _num(u.get("rec_from")), _num(u.get("rec_to"))
        if s is None or e is None or e <= s:
            bad_bounds.append(uid)
        for sp in u.get("keep_spans") or []:
            if s is not None and e is not None and isinstance(sp, (list, tuple)) and len(sp) == 2 and (sp[0] < s - 0.5 or sp[1] > e + 0.5):
                outside.append([uid, sp])
    good = sorted((u for u in units if _num(u.get("rec_from")) is not None and _num(u.get("rec_to")) is not None and u["rec_to"] > u["rec_from"]),
                  key=lambda u: float(u["rec_from"]))
    overlaps = []
    for x, y in zip(good, good[1:]):
        ov = float(x["rec_to"]) - float(y["rec_from"])
        if ov > 0.5:
            overlaps.append({"a": x.get("id"), "b": y.get("id"), "overlap_s": round(ov, 2)})
    # the score changes (hud-states) against the units
    uncovered, no_change, several = [], [], []
    st = read_json(run_paths(run)["analysis"] / "hud" / "states.json")
    n_changes = 0
    if st and st.get("rows"):
        ch = [r for r in st["rows"] if not r.get("initial") and (rng is None or rng[0] <= r["rec"] <= rng[1])]       # a block file is checked on its own range only
        n_changes = len(ch)
        for r in ch:                    # a change belongs to the unit it falls in, or that ended up to `tol` s before it (the scoreboard updates after the result)
            if not any(float(u["rec_from"]) <= r["rec"] <= float(u["rec_to"]) + tol for u in good):
                uncovered.append([r["rec"], fmt_hms(r["rec"], False), r["series"], r["from"], r["to"]])
        for u in good:
            k = sum(1 for r in ch if float(u["rec_from"]) <= r["rec"] <= float(u["rec_to"]) + tol)
            if k == 0:
                no_change.append(u.get("id"))
            elif k > 1:
                several.append([u.get("id"), k])
    # stretches covered by no unit and no non_play
    spans = [(float(u["rec_from"]), float(u["rec_to"])) for u in good]
    spans += [(float(n["rec_from"]), float(n["rec_to"])) for n in non_play if _num(n.get("rec_from")) is not None and _num(n.get("rec_to")) is not None]
    spans.sort()
    stretches = []
    if rng:
        cur = rng[0]
        for s, e in spans:
            if s - cur >= gap:
                stretches.append([round(cur, 2), round(s, 2), round(s - cur, 1)])
            cur = max(cur, e)
        if rng[1] - cur >= gap:
            stretches.append([round(cur, 2), round(rng[1], 2), round(rng[1] - cur, 1)])
    # totals
    by_kind, by_keep, kept_s = {}, {}, {}
    for u in units:
        by_kind[str(u.get("kind"))] = by_kind.get(str(u.get("kind")), 0) + 1
        k = u.get("keep") if _present(u.get("keep")) else u.get("keep_hint")
        by_keep[str(k)] = by_keep.get(str(k), 0) + 1
        if _present(u.get("keep")):
            kept_s[str(u["keep"])] = round(kept_s.get(str(u["keep"]), 0) + sum(max(0.0, sp[1] - sp[0]) for sp in (u.get("keep_spans") or []) if isinstance(sp, (list, tuple)) and len(sp) == 2), 1)
    if bad_files:
        look.append(f"{len(bad_files)} file(s) are not valid JSON objects: {bad_files[:3]}")
    for text, n in (("units with missing fields", len(missing)), ("units with bounds that do not run forward", len(bad_bounds)), ("duplicate unit ids", len(set(dups))),
                    ("overlapping units", len(overlaps)), ("keep spans outside their unit", len(outside)), ("score changes no unit holds", len(uncovered)),
                    ("stretches of at least %d s with no unit and no non_play" % gap, len(stretches))):
        if n:
            look.append(f"{n} {text}")
    out({"ok": True, "source": label, "range": list(rng) if rng else None, "units": len(units), "non_play": len(non_play), "extras": len(extras),
         "by_kind": by_kind, "by_keep": by_keep, "kept_seconds_by_keep": kept_s, "score_changes_in_range": n_changes,
         "look_at": look or ["nothing flagged by these checks (they do not say the cards are right: the second look does)"],
         "missing_fields": dict(list(missing.items())[:SHOW]), "bad_bounds": bad_bounds[:SHOW], "duplicate_ids": sorted(set(dups))[:SHOW], "overlaps": overlaps[:SHOW],
         "keep_spans_outside_unit": outside[:SHOW], "uncovered_score_changes": uncovered[:SHOW], "units_holding_no_score_change": no_change[:SHOW],
         "units_holding_several_score_changes": several[:SHOW], "uncovered_stretches": stretches[:SHOW],
         "note": f"a score change belongs to a unit when it falls inside it or up to {tol} s after its end (the scoreboard updates after the result); these are facts, not verdicts"})


# --------------------------------------------------------------------------- units-merge / units-verdict

KEEP_LEVELS = ("full", "trim", "flash", "skip")


def _block_files(run: Path) -> list:
    return sorted((run_paths(run)["analysis"] / "blocks").glob("block-*.json"))


def cmd_units_merge(a):
    run = resolve_run(a.run)
    an = run_paths(run)["analysis"]
    files = _block_files(run)
    if not files:
        fail("no block files in 20-analysis/blocks: the scan has not written any")
    dest = an / "rounds.json"
    if dest.is_file() and not a.force:
        fail(f"{dest} exists (it may hold verdicts): add --force to rebuild it from the block files, or change it with `cc.py units-verdict`", 2)
    units, seen, dups, non_play, extras, people, fixes, sens, avoid, bad = [], {}, [], [], [], [], [], [], [], []
    for f in files:
        j = read_json(f)
        if not isinstance(j, dict):
            bad.append(f.name)
            continue
        for u in j.get("units") or []:
            uid = str(u.get("id"))
            if uid in seen:
                dups.append([uid, seen[uid], f.name])
                continue
            seen[uid] = f.name
            units.append({**u, "block": j.get("block")})
        non_play += [{**n, "block": j.get("block")} for n in j.get("non_play") or []]
        extras += [{**e, "block": j.get("block")} for e in j.get("extras") or []]
        people += j.get("people") or []
        fixes += [tuple(x) for x in j.get("lexicon_fixes") or [] if isinstance(x, (list, tuple)) and len(x) == 2]
        sens += j.get("sensitive") or []
        avoid += j.get("avoid") or []
    def start(x):
        return float(x.get("rec_from") or 0)
    units.sort(key=start)
    non_play.sort(key=start)
    extras.sort(key=start)
    st = read_json(run_paths(run)["state"], {}) or {}
    game = a.game or st.get("game")
    write_json(dest, {"game": game, "merged_from": [f.name for f in files], "units": units, "non_play": non_play, "extras": extras, "people": people,
                      "lexicon_fixes": [list(x) for x in dict.fromkeys(fixes)]})
    write_json(an / "sensitive.json", sorted(sens, key=start))
    write_json(an / "avoid.json", sorted(avoid, key=start))
    out({"ok": True, "file": str(dest), "blocks": len(files), "units": len(units), "non_play": len(non_play), "extras": len(extras), "sensitive": len(sens), "avoid": len(avoid),
         "duplicate_ids_dropped": dups[:SHOW], "unreadable_files": bad, "also_wrote": [str(an / "sensitive.json"), str(an / "avoid.json")],
         "note": "units sorted by start time; a unit id seen twice keeps its first card (the planner decides about overlapping units: `cc.py units-check` lists them); no verdict is made here"})


def cmd_units_verdict(a):
    run = resolve_run(a.run)
    dest = run_paths(run)["analysis"] / "rounds.json"
    j = read_json(dest)
    if not isinstance(j, dict) or not j.get("units"):
        fail(f"no units in {dest}: run `cc.py units-merge` first")
    src = read_json(a.file)
    if not isinstance(src, dict) or not src:
        fail(f"{a.file} must be a JSON object {{unit id: {{keep, keep_spans, keep_why, ...}}}}")
    by_id = {str(u.get("id")): u for u in j["units"]}
    applied, unknown, invalid = [], [], []
    for uid, v in src.items():
        if uid.startswith("_"):
            continue
        u = by_id.get(str(uid))
        if u is None:
            unknown.append(uid)
            continue
        if not isinstance(v, dict):
            invalid.append([uid, "the verdict must be an object"])
            continue
        if "keep" in v and v["keep"] not in KEEP_LEVELS:
            invalid.append([uid, f"keep must be one of {list(KEEP_LEVELS)}, got {v['keep']!r}"])
            continue
        if "keep_spans" in v and not (isinstance(v["keep_spans"], list) and all(isinstance(s, (list, tuple)) and len(s) == 2 and _num(s[0]) is not None and _num(s[1]) is not None and s[1] > s[0] for s in v["keep_spans"])):
            invalid.append([uid, "keep_spans must be a list of [from, to] rec times, each running forward"])
            continue
        if "used_in" in v and a.add_used_in:
            v = {**v, "used_in": sorted(set(map(str, u.get("used_in") or [])) | set(map(str, v["used_in"])))}
        u.update(v)
        applied.append(uid)
    if applied:
        shutil_copy = dest.with_name("rounds.json.bak")
        shutil_copy.write_bytes(dest.read_bytes())
        write_json(dest, j)
    no_verdict = [str(u.get("id")) for u in j["units"] if not u.get("keep")]
    by_keep = {}
    for u in j["units"]:
        by_keep[str(u.get("keep") or "none yet")] = by_keep.get(str(u.get("keep") or "none yet"), 0) + 1
    out({"ok": True, "file": str(dest), "applied": len(applied), "unknown_ids": unknown[:SHOW], "invalid": invalid[:SHOW], "units_without_a_keep_level": no_verdict[:SHOW],
         "units_without_a_keep_level_count": len(no_verdict), "by_keep": by_keep,
         "note": "the verdicts are the planner's; this only writes them next to the cards (a .bak of the previous rounds.json is kept)"})


# --------------------------------------------------------------------------- units-table

def _cell(x, n: int = 120) -> str:
    s = re.sub(r"\s+", " ", str(x if x is not None else "")).replace("|", "/").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "..."


def cmd_units_table(a):
    run = resolve_run(a.run)
    paths = run_paths(run)
    src = Path(a.file) if a.file else paths["analysis"] / "rounds.json"
    j = read_json(src)
    if not isinstance(j, dict) or not j.get("units"):
        fail(f"no units in {src}: write rounds.json first (cc-plan-game)")
    units = sorted(j["units"], key=lambda u: float(u.get("rec_from") or 0))
    dest = Path(a.out) if a.out else paths["deliverables"] / "rounds.md"
    by_keep, kept_s, per_video = {}, {}, {}
    for u in units:
        k = str(u.get("keep") or u.get("keep_hint") or "?")
        by_keep[k] = by_keep.get(k, 0) + 1
        kept_s[k] = kept_s.get(k, 0.0) + sum(max(0.0, sp[1] - sp[0]) for sp in (u.get("keep_spans") or []) if isinstance(sp, (list, tuple)) and len(sp) == 2)
        for v in u.get("used_in") or []:
            per_video.setdefault(str(v), []).append(str(u.get("id")))
    L = [f"# Every round or fight and what was done with it ({j.get('game') or 'game'})", "",
         "The planner's verdict for each unit. Skipped units are listed again below with the reason, so you can overrule one: tell the agent the unit id and it is added to a video.", "",
         "Keep levels: **full** the whole play, **trim** the part that carries it, **flash** a few seconds that keep the fact, **skip** left out.", "",
         "| Keep | Units | Seconds kept |", "|---|---|---|"]
    for k in ("full", "trim", "flash", "skip"):
        if k in by_keep:
            L.append(f"| {k} | {by_keep[k]} | {round(kept_s.get(k, 0.0))} |")
    L += ["", "## All units", "", "| # | Unit | Rec time | Score | Winner | What happened | Impact | Keep | Why | In videos |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i, u in enumerate(units, 1):
        sc = f"{u.get('score_before', '')} to {u.get('score_after', '')}" if u.get("score_before") or u.get("score_after") else ""
        L.append(f"| {i} | {_cell(u.get('id'), 12)} | {fmt_hms(float(u.get('rec_from') or 0), False)} to {fmt_hms(float(u.get('rec_to') or 0), False)} | {_cell(sc, 16)} | {_cell(u.get('winner'), 24)} | "
                 f"{_cell(u.get('story') or u.get('impact_why'))} | {_cell(u.get('impact'), 4)} | {_cell(u.get('keep') or u.get('keep_hint'), 6)} | {_cell(u.get('keep_why') or u.get('keep_hint_why'))} | {_cell(', '.join(map(str, u.get('used_in') or [])), 30)} |")
    skipped = [u for u in units if str(u.get("keep")) == "skip"]
    if skipped:
        L += ["", "## Skipped units (the reason each was left out)", "", "| Unit | Rec time | Impact | Why it was skipped |", "|---|---|---|---|"]
        for u in skipped:
            L.append(f"| {_cell(u.get('id'), 12)} | {fmt_hms(float(u.get('rec_from') or 0), False)} | {_cell(u.get('impact'), 4)} | {_cell(u.get('keep_why') or u.get('impact_why'))} |")
    if per_video:
        L += ["", "## Units per video", ""] + [f"- **{v}**: {', '.join(ids)}" for v, ids in sorted(per_video.items())]
    if j.get("non_play"):
        L += ["", "## Not play (cut from every video)", "", "| Rec time | Kind | Note |", "|---|---|---|"]
        for n in sorted(j["non_play"], key=lambda n: float(n.get("rec_from") or 0)):
            L.append(f"| {fmt_hms(float(n.get('rec_from') or 0), False)} to {fmt_hms(float(n.get('rec_to') or 0), False)} | {_cell(n.get('kind'), 20)} | {_cell(n.get('note'))} |")
    write_text(dest, "\n".join(L) + "\n")
    out({"ok": True, "file": str(dest), "units": len(units), "by_keep": by_keep, "skipped": len(skipped), "videos": sorted(per_video)})


# --------------------------------------------------------------------------- register

def register(sub) -> None:
    p = sub.add_parser("hud-states", help="the changes of the score (or any counter) read by hud-scan, as one time-ordered table with the state after each change")
    p.add_argument("--run", required=True)
    p.add_argument("--series", required=True, help="comma-separated --name values of earlier hud-scan runs, e.g. score_a,score_b")
    p.add_argument("--stable", type=int, default=3, help="a value counts once this many samples in a row read it (default 3: drops one-sample OCR noise)")
    p.add_argument("--name", default="states", help="the output name: 20-analysis/hud/<name>.json and .txt (default states)")
    p.add_argument("--from", dest="from_", help="print only the changes from this rec time")
    p.add_argument("--to", help="print only the changes up to this rec time")
    p.set_defaults(func=cmd_hud_states)

    p = sub.add_parser("hud-slice", help="the readings of one hud-scan series inside a rec range, one line per change (the clock or a score near a unit)")
    p.add_argument("--run", required=True)
    p.add_argument("--name", required=True, help="the name of the hud-scan reader, e.g. clock or score_a")
    p.add_argument("--from", dest="from_", help="rec time to start at (default: the start)")
    p.add_argument("--to", help="rec time to stop at (default: the end)")
    p.add_argument("--all", action="store_true", help="every sample, not only the changes")
    p.add_argument("--max", type=int, default=200, help="at most this many lines are printed (default 200)")
    p.set_defaults(func=cmd_hud_slice)

    p = sub.add_parser("units-merge", help="the block files' units, non_play and extras as one time-ordered rounds.json (+ sensitive.json, avoid.json); no verdict is made")
    p.add_argument("--run", required=True)
    p.add_argument("--game", help="the game's name for rounds.json (default: state.json's game)")
    p.add_argument("--force", action="store_true", help="rebuild rounds.json even though it exists (the verdicts in it are lost)")
    p.set_defaults(func=cmd_units_merge)

    p = sub.add_parser("units-verdict", help="write the planner's decisions (keep, keep_spans, keep_why, verified, used_in) next to the cards in rounds.json")
    p.add_argument("--run", required=True)
    p.add_argument("--file", required=True, help="a JSON object {unit id: {keep, keep_spans, keep_why, verified, used_in, ...}}")
    p.add_argument("--add-used-in", dest="add_used_in", action="store_true", help="add the given used_in video ids to the ones already there instead of replacing them")
    p.set_defaults(func=cmd_units_verdict)

    p = sub.add_parser("units-check", help="facts about a unit file (a block file or rounds.json): missing fields, overlaps, score changes no unit holds, uncovered stretches, totals")
    p.add_argument("--run", required=True)
    p.add_argument("--file", help="a block-NN.json or rounds.json (default: rounds.json, else every block file)")
    p.add_argument("--tol", type=float, default=6.0, help="seconds after a unit's end inside which a score change still counts as its own (default 6)")
    p.add_argument("--gap", type=float, default=60.0, help="a stretch at least this long with no unit and no non_play is listed (default 60)")
    p.set_defaults(func=cmd_units_check)

    p = sub.add_parser("units-table", help="rounds.json as a table for the user: every round or fight with its keep level and why (deliverables/rounds.md)")
    p.add_argument("--run", required=True)
    p.add_argument("--file", help="default: 20-analysis/rounds.json")
    p.add_argument("--out", help="default: deliverables/rounds.md")
    p.set_defaults(func=cmd_units_table)
