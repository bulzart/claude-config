"""slicer.py - Stage 4 helper: split a duration into Seedance clips (equal by default, cut-snapped with --uneven).

Usage: python slicer.py --duration D --clip-seconds S --min-clip MIN --max-clip MAX [--uneven] [--shots shots.json]
                        [--start 0] [--snap-window 1.5] [--number-from 1] [--out plan-slices.json] [--quiet]

Rules:
  * S must lie within [MIN, MAX] (spec limits from seedance\\SEEDANCE-SPEC.md / SEEDANCE-EDIT.md) -> otherwise exit 2.
  * Equal lengths by default: n = ceil(D / S) clips of S; the last clip is shorter only if unavoidable; when that remainder
    would be below MIN the clips are rebalanced to n equal lengths (never below MIN); when no split satisfies MIN/MAX a
    best-effort plan is written with a warning.
  * --uneven: every internal boundary snaps to the nearest hard cut (shot start in shots.json) within +/- --snap-window s,
    as long as every clip stays within [MIN, MAX]; the remainder is re-balanced after each snap.
  * --start offsets every clip (Mode 2 segment start, Mode 3 budget offsets); --number-from continues numbering across
    several segments.
Output JSON: {duration, start, end, clip_seconds, min_clip, max_clip, uneven, n_clips, clips:[{number, start, end, duration,
  gen_duration_s (integer seconds for the generation call, ceil, clamped), snapped, cut_t}], boundaries, warnings, method}.
Exit 0 ok, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

EPS = 1e-6


def equal_lengths(D: float, S: float, mn: float, mx: float) -> tuple[list[float], list[str]]:
    warnings = []
    if D <= mx + EPS and D <= S + EPS:
        if D < mn - EPS:
            warnings.append(f"duration {D:.2f}s is below the minimum clip length {mn}s: single clip below spec minimum")
        return [D], warnings
    n = int(math.ceil(D / S - EPS))
    last = D - (n - 1) * S
    if last >= mn - EPS:
        lengths = [S] * (n - 1) + [last]
        if last < S - 0.005:
            warnings.append(f"last clip is shorter ({last:.2f}s) - unavoidable with {n - 1} clips of {S}s")
        return lengths, warnings
    L = D / n
    if L >= mn - EPS and L <= mx + EPS:
        warnings.append(f"remainder {last:.2f}s would be below min {mn}s: rebalanced to {n} equal clips of {L:.2f}s")
        return [L] * n, warnings
    if n - 1 >= 1 and D / (n - 1) <= mx + EPS and D / (n - 1) >= mn - EPS:
        L = D / (n - 1)
        warnings.append(f"remainder {last:.2f}s would be below min {mn}s: rebalanced to {n - 1} equal clips of {L:.2f}s")
        return [L] * (n - 1), warnings
    n3 = max(1, int(math.ceil(D / mx - EPS)))
    L = D / n3
    warnings.append(f"no split satisfies min {mn}s / max {mx}s with {S}s clips; best effort {n3} equal clips of {L:.2f}s "
                    f"({'below min' if L < mn else 'ok'}) - consider another clip length or target duration")
    return [L] * n3, warnings


def snap_boundaries(start: float, end: float, lengths: list[float], cuts: list[float], mn: float, mx: float, window: float):
    """Walk the internal boundaries of the planned lengths; snap each to the nearest cut within the window if every
    constraint still holds. After a snap the remaining planned lengths are rescaled proportionally to the time left."""
    n = len(lengths)
    bounds = []  # internal boundaries
    prev = start
    snapped_info = []
    for i in range(n - 1):
        remaining_clips = n - i  # including this one
        planned_rest = sum(lengths[i:])
        scale = (end - prev) / planned_rest if planned_rest > 0 else 1.0
        target = prev + lengths[i] * scale
        cands = sorted((c for c in cuts if abs(c - target) <= window + EPS and prev < c < end), key=lambda c: abs(c - target))
        chosen, cut_t = target, None
        for c in cands:
            this_len = c - prev
            rem = end - c
            k = remaining_clips - 1
            if mn - EPS <= this_len <= mx + EPS and k * mn - EPS <= rem <= k * mx + EPS:
                chosen, cut_t = c, c
                break
        bounds.append(chosen)
        snapped_info.append(cut_t)
        prev = chosen
    return bounds, snapped_info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="clip slicing plan")
    ap.add_argument("--duration", type=float, required=True, help="seconds to split (segment or budget length)")
    ap.add_argument("--clip-seconds", type=float, required=True, help="requested seconds per clip (Q3b)")
    ap.add_argument("--min-clip", type=float, required=True, help="spec minimum clip length")
    ap.add_argument("--max-clip", type=float, required=True, help="spec maximum clip length")
    ap.add_argument("--uneven", action="store_true", help="allow boundaries to snap to shot cuts (Q3c)")
    ap.add_argument("--shots", default=None, help="shots.json (for --uneven)")
    ap.add_argument("--start", type=float, default=0.0, help="source time of the first clip's start")
    ap.add_argument("--snap-window", type=float, default=1.5)
    ap.add_argument("--number-from", type=int, default=1)
    ap.add_argument("--out", default=None, help="output JSON (default: print to stdout only)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    D, S, mn, mx = a.duration, a.clip_seconds, a.min_clip, a.max_clip
    if D <= 0 or mn <= 0 or mx < mn:
        print("bad arguments: duration > 0 and 0 < min-clip <= max-clip required", file=sys.stderr)
        return 2
    if S < mn - EPS or S > mx + EPS:
        print(f"refused: clip length {S}s is outside the spec range {mn}-{mx}s (re-ask Q3b)", file=sys.stderr)
        return 2

    lengths, warnings = equal_lengths(D, S, mn, mx)
    start, end = a.start, a.start + D
    cuts = []
    if a.uneven:
        if a.shots and Path(a.shots).exists():
            sj = common.read_json(a.shots) or {}
            cuts = sorted({float(s["start"]) for s in sj.get("shots", []) if float(s["start"]) > 0})
        else:
            warnings.append("--uneven given without a readable --shots file: no cuts to snap to, equal lengths kept")
    if a.uneven and cuts and len(lengths) > 1:
        bounds, snapped = snap_boundaries(start, end, lengths, cuts, mn, mx, a.snap_window)
    else:
        bounds, snapped = [], []
        acc = start
        for L in lengths[:-1]:
            acc += L
            bounds.append(acc)
        snapped = [None] * len(bounds)
    edges = [start] + bounds + [end]
    clips = []
    for i in range(len(edges) - 1):
        s, e = edges[i], edges[i + 1]
        d = e - s
        gen = int(math.ceil(d - 0.02))
        gen = max(int(math.ceil(mn)), min(int(math.floor(mx)), gen)) if mn <= mx else gen
        clips.append({"number": a.number_from + i, "start": round(s, 3), "end": round(e, 3), "duration": round(d, 3),
                      "gen_duration_s": gen, "snapped": snapped[i] is not None if i < len(snapped) else False,
                      "cut_t": snapped[i] if i < len(snapped) else None})
    n_snapped = sum(1 for c in clips if c["snapped"])
    if n_snapped:
        warnings = [w for w in warnings if not w.startswith("last clip is shorter")]
        warnings.append(f"{n_snapped} boundar{'y' if n_snapped == 1 else 'ies'} snapped to shot cuts: "
                        + ", ".join(f"{c['cut_t']:.3f}" for c in clips if c["snapped"]))
    for c in clips:
        if c["duration"] < mn - 0.005 or c["duration"] > mx + 0.005:
            warnings.append(f"clip {c['number']} duration {c['duration']}s is outside {mn}-{mx}s")
    out = {"duration": round(D, 3), "start": round(start, 3), "end": round(end, 3), "clip_seconds": S, "min_clip": mn, "max_clip": mx,
           "uneven": bool(a.uneven and cuts), "snap_window_s": a.snap_window, "n_clips": len(clips), "clips": clips,
           "boundaries": [round(b, 3) for b in bounds], "n_snapped": n_snapped,
           "cuts_available": len(cuts), "warnings": warnings,
           "method": "equal lengths (ceil(D/S) clips of S, remainder last; rebalanced when the remainder < min)"
                     + ("; boundaries snapped to the nearest hard cut within the window when min/max still hold" if a.uneven else "")}
    if a.out:
        common.write_json(a.out, out)
    if not a.quiet:
        for c in clips:
            print(f"clip {c['number']:02d}: {c['start']:.2f} -> {c['end']:.2f} ({c['duration']:.2f}s, gen {c['gen_duration_s']}s){' snapped to cut ' + str(c['cut_t']) if c['snapped'] else ''}")
        for w in warnings:
            print("WARNING: " + w)
        if a.out:
            print(f"written: {a.out}")
    else:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
