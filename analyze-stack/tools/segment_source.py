"""segment_source.py - cut 00-input\\source.mp4 into 00-input\\segments\\seg-NN.mp4 per a plan's time slices (Seedance edit approach).

Usage: python segment_source.py --run-dir <run> --plan <plan.json> [--copy | --reencode] [--source <file>] [--out-dir <dir>]
                                [--crf 18] [--preset medium] [--quiet]

The plan may be slicer.py output ({clips:[{number,start,end}]}) or the Stage-4 plan.json ({clips|segments|slices:[...]});
each item needs start/end (aliases: source_start/source_end, src_start/src_end, or a nested "slice"/"source" object).
Default = frame-accurate re-encode (libx264 crf 18 + aac 192k, +faststart); --copy = stream copy: each segment starts
at the source keyframe at or before its planned start (reported as copy_start / starts_early_s - on sparse-keyframe
phone footage this can be several seconds early) and ends at the planned end; previews only. Every segment is verified
with ffprobe (duration delta vs plan, size, dims, fps) -> 00-input\\segments\\segments.json (or --out-dir; segments are
indexed in state.json only when they live inside the run folder). Exit 0 ok, 1 any segment failed, 2 bad plan.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def plan_items(plan) -> list[dict]:
    items = None
    if isinstance(plan, list):
        items = plan
    elif isinstance(plan, dict):
        for key in ("clips", "segments", "slices", "edit_segments"):
            if isinstance(plan.get(key), list):
                items = plan[key]
                break
    if not items:
        raise ValueError("plan has no clips/segments/slices list")
    out = []
    for i, it in enumerate(items, 1):
        src = it
        for k in ("slice", "source", "source_slice", "time_slice"):
            if isinstance(it.get(k), dict):
                src = it[k]
                break
        start = next((src[k] for k in ("start", "source_start", "src_start", "in") if k in src), None)
        end = next((src[k] for k in ("end", "source_end", "src_end", "out") if k in src), None)
        if start is None or end is None:
            raise ValueError(f"item {i} has no start/end: {it}")
        out.append({"number": int(it.get("number", it.get("id", i))), "start": float(start), "end": float(end)})
    return out


def keyframe_times(src: Path, log) -> list[float]:
    """pts of every video keyframe (ffprobe -skip_frame nokey); used by --copy to seek exactly onto a keyframe."""
    res = common.run_cmd([common.ffprobe(), "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
                          "-show_entries", "frame=pts_time", "-of", "csv=p=0", str(src)], log=log, timeout=900)
    out = []
    for line in (res.stdout or "").splitlines():
        line = line.strip().strip(",")
        try:
            out.append(float(line))
        except ValueError:
            continue
    return sorted(set(out))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="cut source segments per plan")
    common.add_std_args(ap)
    ap.add_argument("--plan", required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--reencode", action="store_true", help="frame-accurate re-encode (default)")
    g.add_argument("--copy", action="store_true", help="stream copy (keyframe aligned)")
    ap.add_argument("--source", default=None, help="override the source (default 00-input/source.mp4)")
    ap.add_argument("--out-dir", default=None, help="default <run>/00-input/segments")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.script_log(run_dir, "segment_source", a.quiet)
    try:
        plan = common.read_json(a.plan)
        if plan is None:
            log.error(f"plan not found: {a.plan}")
            return 2
        items = plan_items(plan)
    except Exception as e:
        log.error(f"bad plan: {e}")
        return 2
    try:
        src = Path(a.source).resolve() if a.source else common.source_mp4(run_dir)
        out_dir = common.ensure_dir(Path(a.out_dir).resolve() if a.out_dir else run_dir / "00-input" / "segments")
        ff = common.ffmpeg()
        pj = common.ffprobe_json(src, log=log)
        v = common.video_stream(pj) or {}
        fps = common.stream_fps(v) or 30.0
        src_dur = common.media_duration(pj)
        mode = "copy" if a.copy else "reencode"
        log.info(f"cutting {len(items)} segments from {src.name} ({src_dur:.2f}s) mode={mode} -> {out_dir}")
        kfs = keyframe_times(src, log) if mode == "copy" else []
        if mode == "copy":
            log.info(f"stream copy: {len(kfs)} keyframes in the source; every segment starts at the keyframe at or before its "
                     f"planned start and ends at the planned end (frame-accurate starts need the default re-encode)")
        results, all_ok = [], True
        for it in items:
            n, s, e = it["number"], it["start"], min(it["end"], src_dur)
            d = e - s
            dest = out_dir / f"seg-{n:02d}.mp4"
            if d <= 0:
                results.append({"number": n, "file": None, "ok": False, "error": f"empty slice {s}-{e}"})
                all_ok = False
                continue
            if mode == "copy":
                # seek to the keyframe at/before the planned start (+1 ms so the demuxer does not fall back to the
                # previous keyframe through float truncation) and cut -t from THAT point, so the segment ends on plan
                kf = max([k for k in kfs if k <= s + 1e-3], default=0.0)
                seek_t, cut_d = kf + 0.001, e - kf
                args = [ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{seek_t:.4f}", "-i", str(src), "-t", f"{cut_d:.4f}",
                        "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-avoid_negative_ts", "make_zero"]
            else:
                kf, cut_d = s, d
                args = [ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{s:.4f}", "-i", str(src), "-t", f"{d:.4f}",
                        "-map", "0:v:0", "-map", "0:a:0?",
                        "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k"]
            args += ["-movflags", "+faststart", str(dest)]
            t1 = time.time()
            res = common.run_cmd(args, log=log, timeout=3600)
            row = {"number": n, "file": common.rel(run_dir, dest), "start": round(s, 3), "end": round(e, 3),
                   "planned_duration": round(d, 3), "mode": mode, "elapsed_s": round(time.time() - t1, 2)}
            if mode == "copy":
                row.update({"copy_start": round(kf, 3), "starts_early_s": round(s - kf, 3), "expected_duration": round(cut_d, 3)})
            if not res.ok or not dest.exists():
                row.update({"ok": False, "error": res.tail(6)})
                all_ok = False
                log.warn(f"seg-{n:02d} failed: {res.tail(3)}")
            else:
                pj2 = common.ffprobe_json(dest, log=log)
                v2 = common.video_stream(pj2) or {}
                ad = common.media_duration(pj2)
                delta = round(ad - cut_d, 3)
                # re-encode: frame-accurate; copy: the end lands up to ~3 frames late (packet/B-frame granularity)
                tol = 1.0 / fps + 0.05 if mode == "reencode" else 4.0 / fps + 0.2
                row.update({"actual_duration": round(ad, 3), "delta_s": delta, "within_tolerance": abs(delta) <= tol,
                            "size_bytes": dest.stat().st_size, "width": v2.get("width"), "height": v2.get("height"),
                            "fps": round(common.stream_fps(v2), 3), "has_audio": bool(common.audio_streams(pj2)),
                            "sha1": common.sha1_file(dest), "ok": True})
                if not row["within_tolerance"]:
                    log.warn(f"seg-{n:02d}: duration {ad:.3f}s differs from the expected {cut_d:.3f}s by {delta}s")
                early = f", starts {s - kf:.3f}s early at keyframe {kf:.3f}" if mode == "copy" and s - kf > 0.02 else ""
                log.info(f"seg-{n:02d}: {s:.2f}-{e:.2f} -> {ad:.3f}s {v2.get('width')}x{v2.get('height')} "
                         f"{common.human_size(dest.stat().st_size)} ({row['elapsed_s']}s){early}")
            results.append(row)
        out = {"source": common.rel(run_dir, src), "source_duration_s": round(src_dur, 3), "plan": str(Path(a.plan).resolve()),
               "mode": mode, "encode": None if mode == "copy" else f"libx264 crf {a.crf} preset {a.preset} + aac 192k",
               "n_segments": len(results), "all_ok": all_ok, "segments": results,
               "note": "segment-local time t_local maps to source time t_local + start; upload each seg-NN.mp4 as @Video1 of its edit prompt",
               "timing_s": round(time.time() - t0, 2)}
        sj = out_dir / "segments.json"
        common.write_json(sj, out)
        # index in state.json only when the segments live inside the run folder (an external --out-dir is a
        # preview/test location; recording absolute paths outside the run would pollute the file index)
        if out_dir.resolve().is_relative_to(run_dir.resolve()):
            common.state_add_files(run_dir, "00-input", [sj] + [out_dir / Path(r["file"]).name for r in results if r.get("file") and r.get("ok")])
        else:
            log.info(f"--out-dir is outside the run folder; segments are NOT indexed in state.json ({out_dir})")
        log.info(f"segments.json written ({'all ok' if all_ok else 'with failures'}) in {out['timing_s']}s")
        return 0 if all_ok else 1
    except Exception as e:
        import traceback
        log.error(f"segment_source failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
