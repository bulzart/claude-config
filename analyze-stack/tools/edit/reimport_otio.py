"""reimport_otio.py — update edit-plan.json trims / order / speed / transitions from an edited timeline.

    python reimport_otio.py <edited.otio|.xml|.fcpxml|.edl> --plan <edit-plan.json> [--out <edit-plan.json>]
                            [--track V1] [--dry-run] [--json]

The NLE re-edit loop: build_otio.py -> the owner edits in Resolve / Premiere / Final Cut (or Descript ->
export_timeline) -> exports .otio / FCP7 .xml / .fcpxml / .edl -> this script rewrites the plan's clips[] and
transitions[] -> render_ffmpeg.py re-renders (and the builders regenerate the projects).

What is taken from the timeline (first video track, or --track <name>):
  * clip order and trims: source_range start -> `in`; duration -> `out` (times duration x LinearTimeWarp scalar,
    matching build_otio's convention where the OTIO duration is the timeline duration);
  * clip identity: metadata.analyze_stack.plan_clip, else the clip name (plan id or id.N piece), else the media
    file name; media the plan does not know becomes a new clip (id from the file name);
  * consecutive pieces of one plan clip with contiguous source ranges are merged back into one clip with
    speed_ramps; non-contiguous pieces stay separate clips (ids suffixed -2, -3 ...);
  * Transition items -> transitions[] (type from metadata, else xfade; duration = in+out offsets); the
    neighbouring trims are widened by duration/2 so the ffmpeg overlap reproduces the NLE's centred cut;
  * markers whose metadata.analyze_stack.overlay_id (or name) matches an existing overlay re-time that overlay.
Never taken: new text from markers (a marker stream could be a caption track - owner rule: overlays are only
hook/callout/end-card/sticker and only the plan's own), audio tracks (music/sfx stay as planned), effects
other than linear speed. Gaps on the video track are reported and skipped (the plan has no black gaps).

The previous plan is backed up as edit-plan.<YYYYMMDD-HHMMSS>.json next to the output; meta.history gets a
line; the written plan is re-validated with common_edit.load_plan.

Exit codes: 0 ok, 1 usage/input error, 2 timeline unreadable or no video clips.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_edit as ce  # noqa: E402

ADAPTER_BY_EXT = {".otio": "otio_json", ".otioz": "otioz", ".otiod": "otiod", ".xml": "fcp_xml",
                  ".fcpxml": "fcpx_xml", ".edl": "cmx_3600"}


def secs(rt) -> float:
    return float(rt.value) / float(rt.rate) if rt.rate else 0.0


def clip_media_path(clip) -> str | None:
    mr = clip.media_reference
    url = getattr(mr, "target_url", None)
    if url:
        return ce.from_file_uri(url)
    return None


def time_scalar(clip) -> float:
    for e in clip.effects or []:
        if e.schema_name() == "LinearTimeWarp":
            try:
                return float(e.time_scalar)
            except Exception:
                pass
    return 1.0


def match_plan_clip(clip, path: str | None, plan_clips: list[dict], base: str) -> tuple[dict | None, int | None]:
    """Returns (plan clip, piece number) or (None, None)."""
    meta = (clip.metadata or {}).get("analyze_stack") or {}
    pid = meta.get("plan_clip")
    if pid:
        for c in plan_clips:
            if c["id"] == pid:
                return c, meta.get("piece")
    name = clip.name or ""
    m = re.fullmatch(r"(.+?)\.(\d+)", name)
    base_name, piece = (m.group(1), int(m.group(2))) if m else (name, None)
    for c in plan_clips:
        if c["id"] == base_name:
            return c, piece
    if path:
        for c in plan_clips:
            if os.path.basename(ce.resolve_path(c["path"], base) or "").lower() == os.path.basename(path).lower():
                return c, None
    return None, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="edited timeline -> edit-plan.json trims/order")
    ap.add_argument("timeline")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", help="default: overwrite --plan (backup kept)")
    ap.add_argument("--track", help="video track name to read (default: first video track)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        plan, base = ce.load_plan(args.plan)
    except ce.PlanError as e:
        print(f"REFUSED/INVALID: {e}", file=sys.stderr)
        return 3 if "owner rule" in str(e) else 1
    try:
        import opentimelineio as otio
    except Exception as e:
        print(f"opentimelineio import failed: {e}", file=sys.stderr)
        return 2
    tl_path = os.path.abspath(args.timeline)
    if not os.path.isfile(tl_path):
        print(f"timeline not found: {tl_path}", file=sys.stderr)
        return 1
    adapter = ADAPTER_BY_EXT.get(os.path.splitext(tl_path)[1].lower())
    # an EDL carries no frame rate: the cmx_3600 reader defaults to 24 fps and rejects frame numbers >= 24,
    # so read it at the plan's fps (the rate build_otio.py wrote it at)
    read_kw = {"rate": int(plan["project"]["fps"])} if adapter == "cmx_3600" else {}
    try:
        tl = otio.adapters.read_from_file(tl_path, adapter_name=adapter, **read_kw) if adapter else otio.adapters.read_from_file(tl_path)
    except Exception as e:
        print(f"cannot read timeline ({adapter}): {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if tl.schema_name() != "Timeline":
        print(f"expected a Timeline, got {tl.schema_name()}", file=sys.stderr)
        return 2
    vtracks = [t for t in tl.tracks if t.kind == otio.schema.TrackKind.Video]
    if args.track:
        vtracks = [t for t in vtracks if t.name == args.track] or vtracks
    if not vtracks:
        print("no video track in the timeline", file=sys.stderr)
        return 2
    track = vtracks[0]
    plan_clips = plan["clips"]
    probes: dict[str, dict] = {}

    def probe(p: str) -> dict:
        if p not in probes:
            probes[p] = ce.probe_media(p) if os.path.isfile(p) else {"duration": 0.0}
        return probes[p]

    # ---- walk the track
    seq: list[dict] = []        # {kind: clip|transition|gap, ...}
    report = {"timeline": tl_path, "adapter": adapter, "track": track.name, "gaps_skipped": 0, "unmatched_media": [],
              "pieces_merged": [], "transitions": [], "markers_retimed": [], "markers_ignored": []}
    for item in track:
        sn = item.schema_name()
        if sn == "Gap":
            report["gaps_skipped"] += 1
            seq.append({"kind": "gap", "dur": secs(item.duration())})
        elif sn == "Transition":
            d = secs(item.in_offset) + secs(item.out_offset)
            meta = (item.metadata or {}).get("analyze_stack") or {}
            seq.append({"kind": "transition", "duration": round(d, 4), "type": meta.get("type") or "xfade", "xfade": meta.get("xfade")})
        elif sn == "Clip":
            path = clip_media_path(item)
            pc, piece = match_plan_clip(item, path, plan_clips, base)
            sr = item.source_range or item.available_range()
            t_in = secs(sr.start_time)
            dur_tl = secs(sr.duration)
            s = time_scalar(item)
            media_path = ce.resolve_path(pc["path"], base) if pc else path
            if not media_path:
                report["unmatched_media"].append({"clip": item.name, "reason": "no media path and no plan match"})
                continue
            seq.append({"kind": "clip", "plan": pc, "piece": piece, "path": media_path, "in": round(t_in, 4),
                        "out": round(t_in + dur_tl * s, 4), "speed": s, "name": item.name,
                        "volume": ((item.metadata or {}).get("analyze_stack") or {}).get("volume")})
            if pc is None:
                report["unmatched_media"].append({"clip": item.name, "path": media_path, "note": "added as a new clip"})
    clips_seq = [x for x in seq if x["kind"] == "clip"]
    if not clips_seq:
        print("no video clips found on the track", file=sys.stderr)
        return 2
    # ---- merge contiguous pieces of one plan clip back into speed_ramps
    merged: list[dict] = []
    for x in clips_seq:
        prev = merged[-1] if merged else None
        same = prev and prev["plan"] is not None and x["plan"] is prev["plan"] and abs(prev["out"] - x["in"]) <= 1.0 / 24 + 1e-6
        if same:
            if abs(x["speed"] - prev["speed"]) > 1e-6 or prev.get("ramps"):
                prev.setdefault("ramps", []).append({"from": x["in"], "to": x["out"], "speed": x["speed"]})
            prev["out"] = x["out"]
            report["pieces_merged"].append(x["name"])
        else:
            merged.append(dict(x))
    # ---- transitions between merged clips (a transition sits between two clips in seq)
    trans_between: list[tuple[int, dict]] = []  # (index of the following merged clip, transition)
    mi = -1
    pending = None
    for x in seq:
        if x["kind"] == "transition":
            pending = x
        elif x["kind"] == "clip":
            first_of_merged = any(m is x or (m["plan"] is x["plan"] and m["plan"] is not None and m["in"] == x["in"]) for m in merged)
            if first_of_merged:
                mi += 1
                if pending and mi > 0:
                    trans_between.append((mi, pending))
            pending = None
    # ---- build the new clips[] (ids: keep plan ids, suffix repeats, slug new media)
    used: dict[str, int] = {}
    new_clips: list[dict] = []
    for order, m in enumerate(merged, start=1):
        pc = m["plan"]
        if pc:
            base_id = pc["id"]
            c = json.loads(json.dumps(pc))
        else:
            base_id = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(os.path.basename(m["path"]))[0]).strip("-").lower() or f"new{order}"
            c = {"id": base_id, "path": m["path"], "prompt_no": None, "transform": {"fit": "cover", "scale": 1.0, "x": 0, "y": 0},
                 "volume": 1.0, "notes": f"added from {os.path.basename(tl_path)}"}
        n = used.get(base_id, 0) + 1
        used[base_id] = n
        c["id"] = base_id if n == 1 else f"{base_id}-{n}"
        dur_media = probe(m["path"]).get("duration") or 0
        c["in"] = round(max(0.0, m["in"]), 3)
        c["out"] = round(min(m["out"], dur_media) if dur_media else m["out"], 3)
        c["order"] = order
        c["speed"] = round(m["speed"], 6) if m["speed"] != 1.0 else 1.0
        c["speed_ramps"] = [dict(r, **{"from": round(r["from"], 3), "to": round(r["to"], 3)}) for r in m.get("ramps") or []]
        if m.get("volume") is not None:
            c["volume"] = m["volume"]
        new_clips.append(c)
    # widen trims around transitions by d/2 (inverse of build_otio's centred cut)
    new_trans = []
    for i, t in trans_between:
        d = float(t["duration"])
        a, b = new_clips[i - 1], new_clips[i]
        a["out"] = round(min(a["out"] + d / 2 * float(a.get("speed", 1.0) or 1.0), probe(a["path"]).get("duration") or a["out"] + d), 3)
        b["in"] = round(max(0.0, b["in"] - d / 2 * float(b.get("speed", 1.0) or 1.0)), 3)
        rec = {"between": [a["id"], b["id"]], "type": t["type"] if t["type"] in ("xfade", "whip", "zoom") else "xfade", "duration": round(d, 3)}
        if t.get("xfade"):
            rec["xfade"] = t["xfade"]
        new_trans.append(rec)
        report["transitions"].append(rec)
    for a, b in zip(new_clips, new_clips[1:]):
        if not any(tr["between"] == [a["id"], b["id"]] for tr in new_trans):
            new_trans.append({"between": [a["id"], b["id"]], "type": "cut"})
    new_trans.sort(key=lambda tr: [c["id"] for c in new_clips].index(tr["between"][0]))
    # ---- markers -> re-time existing overlays only
    overlays = plan.get("text_overlays") or []
    by_id = {o.get("id"): o for o in overlays}
    by_text = {str(o.get("text", "")).replace("\n", " / ").strip().lower(): o for o in overlays}
    for holder in [track, tl.tracks]:
        for mk in holder.markers:
            meta = (mk.metadata or {}).get("analyze_stack") or {}
            ov = by_id.get(meta.get("overlay_id")) or by_text.get((mk.name or "").strip().lower())
            if ov is None:
                report["markers_ignored"].append(mk.name)
                continue
            t0 = secs(mk.marked_range.start_time)
            t1 = t0 + secs(mk.marked_range.duration)
            if abs(t0 - float(ov.get("t_start", 0))) > 1e-3 or abs(t1 - float(ov.get("t_end", 0))) > 1e-3:
                ov["t_start"], ov["t_end"] = round(t0, 3), round(t1, 3)
                report["markers_retimed"].append({"id": ov.get("id"), "t_start": ov["t_start"], "t_end": ov["t_end"]})
    # ---- overlays vs the new timeline length: an end card is anchored to the END of the timeline (playbook 4.8:
    # "over the last 2 s"), so when the NLE edit shortened or lengthened the cut and no marker re-timed it, it is
    # re-anchored to the new end (same length); any other overlay left beyond the new end is reported (the renderer
    # would skip it). Text is never changed here.
    try:
        _, new_total = ce.compute_timeline({"clips": new_clips, "transitions": new_trans}, probes)
    except Exception:
        new_total = None
    report["timeline_total_s"] = new_total
    report["overlays_reanchored"], report["overlays_beyond_end"] = [], []
    if new_total:
        retimed_ids = {r["id"] for r in report["markers_retimed"]}
        for ov in overlays:
            t0, t1 = float(ov.get("t_start", 0)), float(ov.get("t_end", 0))
            if ov.get("id") in retimed_ids:
                continue
            if ov.get("type") == "end_card" and abs(t1 - new_total) > 1e-3:
                length = max(0.5, t1 - t0)
                ov["t_end"], ov["t_start"] = round(new_total, 3), round(max(0.0, new_total - length), 3)
                report["overlays_reanchored"].append({"id": ov.get("id"), "from": [t0, t1], "to": [ov["t_start"], ov["t_end"]]})
            elif t0 >= new_total - 1e-3:
                report["overlays_beyond_end"].append({"id": ov.get("id"), "t_start": t0, "timeline_end": round(new_total, 3),
                                                      "note": "starts after the new timeline end; the renderer skips it - re-time it in the plan"})
    # ---- diff + write
    before = [(c["id"], c["in"], c["out"]) for c in plan_clips]
    after = [(c["id"], c["in"], c["out"]) for c in new_clips]
    plan["clips"] = new_clips
    plan["transitions"] = new_trans
    meta = plan.setdefault("meta", {})
    meta["source"] = "reimport_otio"
    meta["updated"] = ce.now_iso()
    meta.setdefault("history", []).append(f"{ce.now_iso()} reimport_otio from {os.path.basename(tl_path)} ({adapter})")
    out = os.path.abspath(args.out or args.plan)
    report.update({"clips_before": before, "clips_after": after, "out": out, "dry_run": args.dry_run})
    if not args.dry_run:
        if os.path.isfile(out):
            bak = os.path.join(os.path.dirname(out), f"{os.path.splitext(os.path.basename(out))[0]}.{ce.stamp()}.json")
            shutil.copyfile(out, bak)
            report["backup"] = bak
        ce.save_json(out, plan)
        try:
            ce.load_plan(out)
        except ce.PlanError as e:
            print(f"written plan failed validation: {e}", file=sys.stderr)
            return 1
        ce.history_line(os.path.dirname(out), f"reimport_otio: {len(new_clips)} clips from {os.path.basename(tl_path)}")
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.json else None, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
