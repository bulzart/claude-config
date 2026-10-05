"""build_otio.py — edit-plan.json -> OpenTimelineIO timeline + NLE interchange files.

    python build_otio.py <edit-plan.json> --out-dir <dir> [--name timeline] [--no-audio] [--json]

Writes (OpenTimelineIO 0.18.1 + adapters otio-fcp-adapter / otio-fcpx-xml-adapter / otio-cmx3600-adapter):
  <name>.otio     native OTIO JSON        -> DaVinci Resolve 18.5+ (File > Import > Timeline), Kdenlive 25.04+,
                                              Premiere Pro 25.6+ (File > Import; OTIO import is recent - also use the .xml)
  <name>.xml      FCP7 XML (fcp_xml)      -> Premiere Pro (File > Import, "Final Cut Pro XML"), DaVinci Resolve
                                              (File > Import > Timeline), Avid via conversion
  <name>.fcpxml   FCPXML (fcpx_xml)       -> Final Cut Pro 10.x
  <name>.edl      CMX 3600 EDL (cmx_3600) -> every NLE (video track only; dissolves carried; media relinked by name)
  <name>.otio-export.json                 what was written, re-parse results, caveats
  README-otio.md                          which NLE opens each file + relink notes

Timeline content: video track V1 = one Clip per clip piece (source_range starts at the trim-in; its duration is
the piece's TIMELINE duration because OTIO core and the XML adapters ignore time effects; a speed piece carries
a LinearTimeWarp effect and its src_in/src_out in metadata for consumers that honour or need a manual retime),
Transition objects (SMPTE_Dissolve, in/out offsets = duration/2, the cut point centred so the timeline length
equals the render's), track markers for every text overlay (name = the text, metadata = type/style/geometry;
markers are the OTIO convention for titles - OTIO has no title schema), audio tracks A1 (the clips' own audio),
A2 music bed (gap + clip), A3 sfx (gaps + clips). Never speech captions: markers are written only for the
plan's hook/callout/end-card/sticker overlays (the plan loader refuses caption-shaped content).

Exit codes: 0 ok, 1 plan/usage error, 2 write/re-parse failure, 3 refused (caption-shaped plan).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_edit as ce  # noqa: E402

NLE_TABLE = [
    ("<name>.otio", "otio_json", "DaVinci Resolve 18.5+ (File > Import > Timeline), Kdenlive 25.04+, Premiere Pro 25.6+ (File > Import)"),
    ("<name>.xml", "fcp_xml", "Premiere Pro (File > Import - Final Cut Pro XML), DaVinci Resolve (File > Import > Timeline), Avid Media Composer via XML import"),
    ("<name>.fcpxml", "fcpx_xml", "Final Cut Pro 10.x (File > Import > XML)"),
    ("<name>.edl", "cmx_3600", "any NLE (CMX 3600) - video track only, dissolves kept, clips relinked by reel/clip name"),
]


def rt(frames: int, fps: int):
    import opentimelineio as otio
    return otio.opentime.RationalTime(int(frames), fps)


def tr(start_f: int, dur_f: int, fps: int):
    import opentimelineio as otio
    return otio.opentime.TimeRange(rt(start_f, fps), rt(dur_f, fps))


def frames(seconds: float, fps: int) -> int:
    return int(round(float(seconds) * fps))


def media_ref(path: str, dur_s: float, fps: int):
    import opentimelineio as otio
    return otio.schema.ExternalReference(target_url=ce.to_file_uri(path),
                                         available_range=tr(0, max(1, frames(dur_s, fps)), fps))


def build_timeline(plan: dict, base: str, probes: dict, placed: list[dict], name: str, with_audio: bool = True):
    import opentimelineio as otio
    fps = int(plan["project"]["fps"])
    tl = otio.schema.Timeline(name=name, global_start_time=rt(0, fps))
    tl.metadata["analyze_stack"] = {"schema": ce.PLAN_SCHEMA, "run_id": (plan.get("meta") or {}).get("run_id"),
                                    "canvas": {"width": plan["project"]["width"], "height": plan["project"]["height"], "fps": fps},
                                    "safe_box": ce.safe_box_for(plan), "no_captions": "speech captions are never part of this timeline (owner rule)"}
    v1 = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    a1 = otio.schema.Track(name="A1 clip audio", kind=otio.schema.TrackKind.Audio)
    trans = ce.transition_lookup(plan)
    order = [p["clip"] for p in placed]
    # per-clip trims adjusted so a transition is centred on the cut: previous clip loses d/2 at its tail,
    # the next clip starts d/2 later; the transition then uses that handle media (NLE convention).
    adj = []
    for i, p in enumerate(placed):
        c = p["clip"]
        pieces = [list(x) for x in p["pieces"]]
        t_in = p["transition_in"]
        if t_in and t_in.get("type", "cut") != "cut":
            d = float(t_in["duration"]) / 2.0
            a, b, s = pieces[0]
            pieces[0][0] = min(a + d * s, b - 1.0 / fps)
        if i + 1 < len(placed):
            t_out = placed[i + 1]["transition_in"]
            if t_out and t_out.get("type", "cut") != "cut":
                d = float(t_out["duration"]) / 2.0
                a, b, s = pieces[-1]
                pieces[-1][1] = max(b - d * s, a + 1.0 / fps)
        adj.append((c, pieces, t_in))
    for i, (c, pieces, t_in) in enumerate(adj):
        path = ce.resolve_path(c["path"], base)
        pr = probes[path]
        if t_in and t_in.get("type", "cut") != "cut":
            d_f = max(2, frames(float(t_in["duration"]), fps))
            half = d_f // 2
            t = otio.schema.Transition(name=f"{t_in['type']} {order[i - 1]['id']}->{c['id']}",
                                       transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                                       in_offset=rt(half, fps), out_offset=rt(d_f - half, fps))
            t.metadata["analyze_stack"] = {"type": t_in["type"], "duration_s": float(t_in["duration"]), "xfade": t_in.get("xfade")}
            v1.append(t)
            a1.append(otio.schema.Transition(name=t.name, transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                                             in_offset=rt(half, fps), out_offset=rt(d_f - half, fps)))
        for j, (a, b, s) in enumerate(pieces):
            src_f = frames(a, fps)
            # OTIO core (and the fcp/fcpx adapters) ignore LinearTimeWarp when computing durations, so the
            # source_range duration is the TIMELINE duration of the piece ((b-a)/speed): the timeline length is
            # right in every NLE; consumers that honour the warp play src_in..src_out at `speed`, the others
            # play the first (b-a)/speed seconds at 1x (src_in/src_out kept in metadata for a manual retime).
            dur_src_f = max(1, frames((b - a) / s, fps))
            cname = c["id"] if len(pieces) == 1 else f"{c['id']}.{j + 1}"
            clip = otio.schema.Clip(name=cname, media_reference=media_ref(path, pr["duration"], fps),
                                    source_range=tr(src_f, dur_src_f, fps))
            clip.metadata["analyze_stack"] = {"plan_clip": c["id"], "piece": j + 1, "speed": float(s), "src_in": a, "src_out": b,
                                              "timeline_duration_s": (b - a) / s, "prompt_no": c.get("prompt_no"),
                                              "transform": c.get("transform"), "notes": c.get("notes")}
            if abs(s - 1.0) > 1e-6:
                clip.effects.append(otio.schema.LinearTimeWarp(name=f"speed {s:g}x", time_scalar=float(s)))
            v1.append(clip)
            if pr.get("has_audio"):
                aclip = otio.schema.Clip(name=cname, media_reference=media_ref(path, pr["duration"], fps),
                                         source_range=tr(src_f, dur_src_f, fps))
                aclip.metadata["analyze_stack"] = {"plan_clip": c["id"], "volume": c.get("volume", 1.0)}
                if abs(s - 1.0) > 1e-6:
                    aclip.effects.append(otio.schema.LinearTimeWarp(name=f"speed {s:g}x", time_scalar=float(s)))
                a1.append(aclip)
            else:
                a1.append(otio.schema.Gap(source_range=tr(0, max(1, frames((b - a) / s, fps)), fps)))
    tl.tracks.append(v1)
    total_f = frames(sum(p["duration"] for p in placed) - sum(float(p["transition_in"]["duration"]) for p in placed
                                                                if p["transition_in"] and p["transition_in"].get("type", "cut") != "cut"), fps)
    # markers = text overlays (hook / callout / end card / sticker) - never captions
    items = ce.layout_overlays(plan, total_duration=total_f / fps)
    for it in items:
        m = otio.schema.Marker(name=it["text"].replace("\n", " / "), color=otio.schema.MarkerColor.YELLOW,
                               marked_range=tr(frames(it["t_start"], fps), max(1, frames(it["t_end"] - it["t_start"], fps)), fps))
        m.metadata["analyze_stack"] = {"overlay_id": it["id"], "type": it["type"], "style": it["style"], "font": it["font"],
                                       "size_px": it["size"], "x": it["x"], "y": it["y"], "safe_box": it["safe_box"]}
        v1.markers.append(m)
        tl.tracks.markers.append(m.clone())  # sequence-level copy: FCP7 XML carries sequence markers, not track markers
    for ov in plan.get("text_overlays") or []:
        if ov.get("type") == "sticker" and ov.get("image"):
            m = otio.schema.Marker(name=f"sticker {os.path.basename(ov['image'])}", color=otio.schema.MarkerColor.CYAN,
                                   marked_range=tr(frames(float(ov.get("t_start", 0)), fps),
                                                   max(1, frames(float(ov.get("t_end", 0)) - float(ov.get("t_start", 0)), fps)), fps))
            m.metadata["analyze_stack"] = {"overlay_id": ov.get("id"), "type": "sticker", "image": ce.resolve_path(ov["image"], base),
                                           "position": ov.get("position"), "width_px": ov.get("width_px")}
            v1.markers.append(m)
            tl.tracks.markers.append(m.clone())
    if with_audio:
        tl.tracks.append(a1)
        audio = plan.get("audio") or {}
        music = audio.get("music") or {}
        mp = ce.resolve_path(music.get("path"), base) if music.get("path") else None
        if mp and os.path.isfile(mp):
            pr = ce.probe_media(mp)
            a2 = otio.schema.Track(name="A2 music", kind=otio.schema.TrackKind.Audio)
            start_f = frames(float(music.get("start", 0.0) or 0.0), fps)
            if start_f > 0:
                a2.append(otio.schema.Gap(source_range=tr(0, start_f, fps)))
            length_f = max(1, min(frames(pr["duration"], fps), total_f - start_f))
            mc = otio.schema.Clip(name=os.path.basename(mp), media_reference=media_ref(mp, pr["duration"], fps),
                                  source_range=tr(0, length_f, fps))
            mc.metadata["analyze_stack"] = {"gain_db": ce.gain_db(music, -18.0), "ducking": music.get("ducking"),
                                            "license": music.get("license")}
            a2.append(mc)
            tl.tracks.append(a2)
        sfx = [s for s in (audio.get("sfx") or []) if s.get("path") and os.path.isfile(ce.resolve_path(s["path"], base))]
        if sfx:
            a3 = otio.schema.Track(name="A3 sfx", kind=otio.schema.TrackKind.Audio)
            cursor = 0
            for s in sorted(sfx, key=lambda s: float(s.get("at", 0))):
                sp = ce.resolve_path(s["path"], base)
                pr = ce.probe_media(sp)
                at_f = frames(float(s.get("at", 0)), fps)
                if at_f < cursor:
                    continue  # overlapping SFX: skip (documented; the render mixes them all)
                if at_f > cursor:
                    a3.append(otio.schema.Gap(source_range=tr(0, at_f - cursor, fps)))
                dur_f = max(1, frames(pr["duration"], fps))
                sc = otio.schema.Clip(name=os.path.basename(sp), media_reference=media_ref(sp, pr["duration"], fps),
                                      source_range=tr(0, dur_f, fps))
                sc.metadata["analyze_stack"] = {"gain_db": ce.gain_db(s, -12.0), "label": s.get("label")}
                a3.append(sc)
                cursor = at_f + dur_f
            tl.tracks.append(a3)
    return tl, total_f


def strip_transitions(tl):
    import opentimelineio as otio
    tl2 = otio.adapters.read_from_string(otio.adapters.write_to_string(tl, "otio_json"), "otio_json")
    for track in tl2.tracks:
        for item in list(track):
            if isinstance(item, otio.schema.Transition):
                track.remove(item)
    return tl2


def video_only(tl):
    import opentimelineio as otio
    tl2 = otio.adapters.read_from_string(otio.adapters.write_to_string(tl, "otio_json"), "otio_json")
    for track in list(tl2.tracks):
        if track.kind != otio.schema.TrackKind.Video:
            tl2.tracks.remove(track)
    return tl2


def reparse(path: str, adapter: str, fps: int | None = None) -> dict:
    import opentimelineio as otio
    # A CMX 3600 EDL carries no frame rate; the adapter reads at 24 fps unless told otherwise and then rejects
    # any timecode with a frame number >= 24 ("Frame rate mismatch"). Always read it at the project fps.
    kw = {"rate": int(fps)} if (adapter == "cmx_3600" and fps) else {}
    t = otio.adapters.read_from_file(path, adapter_name=adapter, **kw)
    clips = list(t.find_clips()) if hasattr(t, "find_clips") else list(t.each_clip())
    n_tr = sum(1 for tr_ in t.tracks for it in tr_ if isinstance(it, otio.schema.Transition))
    n_mk = sum(len(tr_.markers) for tr_ in t.tracks) + len(t.tracks.markers)
    dur = t.duration()
    return {"clips": len(clips), "tracks": len(t.tracks), "transitions": n_tr, "markers": n_mk,
            "duration_s": round(dur.value / dur.rate, 3) if dur.rate else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="edit-plan.json -> OTIO + FCP7 XML + FCPXML + EDL")
    ap.add_argument("plan")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", default="timeline")
    ap.add_argument("--no-audio", action="store_true")
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
        print(f"opentimelineio import failed: {e}\nfix: winget install --id Microsoft.VCRedist.2015+.x64 -e ; "
              f"python -m pip install opentimelineio==0.18.1 otio-fcp-adapter otio-fcpx-xml-adapter otio-cmx3600-adapter", file=sys.stderr)
        return 2
    probes = {}
    for c in plan["clips"]:
        p = ce.resolve_path(c["path"], base)
        if not os.path.isfile(p):
            print(f"clip {c['id']}: file not found {p}", file=sys.stderr)
            return 1
        probes[p] = ce.probe_media(p)
    plan_tl = json.loads(json.dumps(plan))
    for c in plan_tl["clips"]:
        c["path"] = ce.resolve_path(c["path"], base)
    placed, total = ce.compute_timeline(plan_tl, probes)
    tl, total_f = build_timeline(plan, base, probes, placed, args.name, with_audio=not args.no_audio)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    fps = int(plan["project"]["fps"])
    results = {}
    targets = [("otio_json", ".otio", tl), ("fcp_xml", ".xml", tl), ("fcpx_xml", ".fcpxml", tl), ("cmx_3600", ".edl", video_only(tl))]
    available = set(otio.adapters.available_adapter_names())
    for adapter, ext, timeline in targets:
        path = os.path.join(out_dir, args.name + ext)
        rec = {"adapter": adapter, "path": path}
        if adapter not in available:
            rec["error"] = f"adapter {adapter} not installed (pip install otio-fcp-adapter otio-fcpx-xml-adapter otio-cmx3600-adapter)"
            results[ext] = rec
            continue
        wrote = False
        for attempt, t_ in ((1, timeline), (2, strip_transitions(timeline))):
            try:
                otio.adapters.write_to_file(t_, path, adapter_name=adapter)
                rec["transitions_stripped"] = attempt == 2
                wrote = True
                break
            except Exception as e:  # e.g. an adapter that cannot serialise Transition/LinearTimeWarp
                rec[f"attempt{attempt}_error"] = f"{type(e).__name__}: {str(e)[:300]}"
        if wrote:
            try:
                rec["reparse"] = reparse(path, adapter, fps)
            except Exception as e:
                rec["reparse_error"] = f"{type(e).__name__}: {str(e)[:300]}"
        results[ext] = rec
    caveats = [
        "OTIO carries clips, trims, order, dissolves, markers and speed (LinearTimeWarp); it has no title schema: "
        "hook/callout/end-card overlays are MARKERS on V1 (name = text, metadata = geometry) - recreate them as titles in the NLE "
        "or render them with render_ffmpeg.py. Speech captions are never included (owner rule).",
        "fcp_xml / fcpx_xml adapters (1.0.0) do not write transitions or speed effects: if the first write failed the file was "
        "re-written without transitions (see transitions_stripped); cuts stay centred on the transition midpoint.",
        "Media is referenced by absolute file:// URL; NLEs on another machine need a relink (File > Relink / Reconnect).",
        "EDL is the video track only (CMX 3600); audio tracks live in .otio / .xml / .fcpxml. An EDL carries no frame "
        f"rate: import it at {fps} fps in the NLE (reimport_otio.py reads it at the plan fps; the OTIO cmx_3600 reader "
        "defaults to 24 fps and rejects frame numbers >= 24 otherwise).",
        "Colour preset, grain and music ducking are not expressible - re-apply in the NLE; the plan keeps them for the ffmpeg render.",
    ]
    summary = {"plan": os.path.abspath(args.plan), "out_dir": out_dir, "fps": fps, "planned_duration_s": total,
               "timeline_frames": total_f, "tracks": [{"name": t.name, "kind": str(t.kind), "items": len(t)} for t in tl.tracks],
               "markers": [{"name": m.name, "start_s": m.marked_range.start_time.value / fps} for m in tl.tracks[0].markers],
               "exports": results, "caveats": caveats, "generated": ce.now_iso()}
    ce.save_json(os.path.join(out_dir, args.name + ".otio-export.json"), summary)
    readme = ["# OTIO exports — " + args.name, "", "| File | Adapter | Opens in |", "|---|---|---|"]
    for f, a, nle in NLE_TABLE:
        readme.append(f"| `{f.replace('<name>', args.name)}` | {a} | {nle} |")
    readme += ["", "Re-parse check (opentimelineio.adapters.read_from_file):", ""]
    for ext, rec in results.items():
        readme.append(f"- `{os.path.basename(rec['path'])}`: " + (json.dumps(rec.get("reparse")) if rec.get("reparse") else rec.get("error") or rec.get("reparse_error") or "not written")
                      + (" (transitions stripped for this adapter)" if rec.get("transitions_stripped") else ""))
    readme += ["", "Caveats:", ""] + [f"- {c}" for c in caveats]
    readme += ["", "Re-edit loop: edit in the NLE, export .otio / FCP7 .xml / .fcpxml, then",
               f"`python tools\\edit\\reimport_otio.py <edited file> --plan {os.path.abspath(args.plan)}` and re-render with render_ffmpeg.py.", ""]
    ce.write_text(os.path.join(out_dir, "README-otio.md"), "\n".join(readme))
    ce.history_line(os.path.dirname(os.path.abspath(args.plan)), f"otio exports written to {out_dir}: " +
                    ", ".join(f"{k} {'ok' if v.get('reparse') else 'FAILED'}" for k, v in results.items()))
    failed = [k for k, v in results.items() if not v.get("reparse")]
    print(json.dumps(summary if args.json else {"out_dir": out_dir, "planned_duration_s": total,
                                                "exports": {k: (v.get("reparse") or v.get("error") or v.get("reparse_error")) for k, v in results.items()},
                                                "failed": failed}, ensure_ascii=False, indent=2 if args.json else None))
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
