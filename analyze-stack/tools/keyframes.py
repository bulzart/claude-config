"""keyframes.py - Stage 1: per-shot first/middle/last frames, uniformly sampled frames and contact sheets.

Usage: python keyframes.py --run-dir <run> [--fps N] [--max-frames 600] [--sample-max-side 1280] [--jobs 4] [--quiet]

Outputs (10-measure\\):
  keyframes\\shots\\shot-03-first-00m03.40s.jpg / -mid- / -last-   full resolution, JPEG q=2, one triple per shot
  keyframes\\sampled\\t-00m12.50s.jpg                               uniform sampling, long side <= --sample-max-side, q=3
  contact-sheets\\sheet-01.jpg ...                                   4x4 tiles, 270x480 cells (portrait) / 480x270 (landscape),
                                                                     aspect preserved with padding, timestamp + shot id burned in
  contact-sheets\\index.json                                         sheet/cell -> timestamp, shot id, frame file
  keyframes.json                                                     index of everything above + the sampling decision

Sampling rate: 2 fps by default; 3 fps when the median shot is under 1.5 s; 1 fps for videos over 5 min;
--fps forces a value; the total is capped at --max-frames (fps is lowered to fit and the summary says so).
Exit 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def pick_sample_fps(duration: float, median_shot: float | None, forced: float | None, max_frames: int):
    if forced:
        fps, reason = float(forced), f"forced by --fps {forced}"
    elif duration > 300:
        fps, reason = 1.0, "video over 5 min -> 1 fps"
    elif median_shot is not None and median_shot < 1.5:
        fps, reason = 3.0, f"median shot {median_shot:.2f}s under 1.5 s -> 3 fps"
    else:
        fps, reason = 2.0, "default 2 fps"
    n = int(math.ceil(duration * fps))
    if n > max_frames:
        fps = max_frames / duration
        reason += f"; capped at {max_frames} frames -> {fps:.3f} fps"
    return fps, reason


def shot_for(t: float, shots: list[dict]) -> int | None:
    for s in shots:
        if s["start"] <= t < s["end"]:
            return s["id"]
    if shots and t >= shots[-1]["end"] - 1e-6:
        return shots[-1]["id"]
    return None


def extract_one(ff: str, src: Path, t: float, out: Path, log, q: int = 2, vf: str | None = None) -> bool:
    args = [ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, t):.4f}", "-i", str(src),
            "-frames:v", "1", "-q:v", str(q)]
    if vf:
        args += ["-vf", vf]
    args.append(str(out))
    res = common.run_cmd(args, log=log, timeout=120)
    return res.ok and out.exists() and out.stat().st_size > 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="shot keyframes + sampled frames + contact sheets")
    common.add_std_args(ap)
    ap.add_argument("--fps", type=float, default=None, help="force the sampling rate (frames per second)")
    ap.add_argument("--max-frames", type=int, default=600, help="cap on sampled frames (default 600)")
    ap.add_argument("--sample-max-side", type=int, default=1280, help="long side of sampled frames (default 1280)")
    ap.add_argument("--jobs", type=int, default=4, help="parallel ffmpeg processes for shot frames")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "keyframes", a.quiet)
    try:
        src = common.source_mp4(run_dir)
        mdir = common.measure_dir(run_dir)
        ff = common.ffmpeg()
        probe = common.read_json(mdir / "probe.json")
        if not probe:
            pj = common.ffprobe_json(src, log=log)
            v = common.video_stream(pj) or {}
            duration, fps = common.media_duration(pj), common.stream_fps(v)
            w, h = int(v.get("width") or 0), int(v.get("height") or 0)
        else:
            duration, fps = float(probe["duration_s"]), float(probe["fps"]["value"])
            w, h = int(probe["display_width"]), int(probe["display_height"])
        fps = fps or 30.0
        portrait = h >= w
        shots_json = common.read_json(mdir / "shots.json")
        if shots_json and shots_json.get("shots"):
            shots = shots_json["shots"]
            median_shot = (shots_json.get("pacing") or {}).get("median_shot_s")
        else:
            log.warn("shots.json missing - treating the whole video as one shot (run cuts.py first for real shots)")
            shots = [{"id": 1, "start": 0.0, "end": round(duration, 3), "duration": round(duration, 3)}]
            median_shot = duration

        shots_dir = common.ensure_dir(mdir / "keyframes" / "shots")
        sampled_dir = common.ensure_dir(mdir / "keyframes" / "sampled")
        sheets_dir = common.ensure_dir(mdir / "contact-sheets")
        work = common.ensure_dir(mdir / "_work" / "sampled")
        for old in list(shots_dir.glob("*.jpg")) + list(sampled_dir.glob("*.jpg")) + list(sheets_dir.glob("*.jpg")) + list(work.glob("*.jpg")):
            old.unlink(missing_ok=True)

        # ---------------------------------------------------------------- shot frames (first / mid / last)
        half = 0.4 / fps  # seek a little before the target so '-ss' lands on that frame, not the next one
        jobs = []
        for s in shots:
            sid = int(s["id"])
            first_t = float(s["start"])
            last_t = max(first_t, float(s["end"]) - 1.0 / fps)
            mid_t = (first_t + float(s["end"])) / 2.0
            for kind, t in (("first", first_t), ("mid", mid_t), ("last", last_t)):
                name = f"shot-{sid:02d}-{kind}-{common.ts_name(t)}.jpg"
                jobs.append((sid, kind, round(t, 3), shots_dir / name, max(0.0, t - half)))
        log.info(f"extracting {len(jobs)} shot frames ({len(shots)} shots) with {a.jobs} parallel ffmpeg processes")
        t1 = time.time()
        with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
            results = list(ex.map(lambda j: extract_one(ff, src, j[4], j[3], log, q=2), jobs))
        shot_frames = []
        for (sid, kind, t, out, _seek), ok in zip(jobs, results):
            if ok:
                shot_frames.append({"shot": sid, "kind": kind, "t": t, "file": common.rel(run_dir, out)})
            else:
                log.warn(f"shot frame failed: shot {sid} {kind} @ {t}s")
        log.info(f"shot frames: {len(shot_frames)} ok in {time.time() - t1:.1f}s")

        # ---------------------------------------------------------------- uniform sampling
        sample_fps, reason = pick_sample_fps(duration, median_shot, a.fps, a.max_frames)
        log.info(f"sampling at {sample_fps:.3f} fps ({reason})")
        ms = int(a.sample_max_side)
        scale = f"scale=-2:'min({ms},ih)'" if portrait else f"scale='min({ms},iw)':-2"
        vf = f"fps={sample_fps:.6f},{scale},showinfo"
        t1 = time.time()
        res = common.run_cmd([ff, "-hide_banner", "-nostats", "-loglevel", "info", "-y", "-i", str(src), "-vf", vf,
                              "-q:v", "3", str(work / "s-%05d.jpg")], log=log, timeout=3600)
        if not res.ok:
            raise RuntimeError(f"sampling ffmpeg failed rc={res.returncode}: {res.tail(10)}")
        pts = {}
        for line in res.stderr.splitlines():
            m = re.search(r"\bn:\s*(\d+)\s+pts:\s*-?\d+\s+pts_time:(-?[\d.]+)", line)
            if m:
                pts[int(m.group(1))] = float(m.group(2))
        files = sorted(work.glob("s-*.jpg"))
        sampled = []
        for k, f in enumerate(files):
            t = pts.get(k, k / sample_fps)
            t = round(max(0.0, t), 3)
            dest = sampled_dir / f"t-{common.ts_name(t)}.jpg"
            if dest.exists():
                dest.unlink()
            f.replace(dest)
            sampled.append({"t": t, "shot": shot_for(t, shots), "file": common.rel(run_dir, dest)})
        log.info(f"sampled frames: {len(sampled)} in {time.time() - t1:.1f}s "
                 f"(timestamps from showinfo pts: {len(pts)} parsed)")

        # ---------------------------------------------------------------- contact sheets
        t1 = time.time()
        frames = [{"path": run_dir / s["file"], "t": s["t"], "shot": s["shot"]} for s in sampled]
        index = common.build_contact_sheets(frames, sheets_dir, portrait=portrait, grid=(4, 4), padding=4,
                                            prefix="sheet", quality=88)
        index.update({
            "source": common.rel(run_dir, src), "duration_s": round(duration, 3), "sample_fps": round(sample_fps, 4),
            "sample_fps_reason": reason, "orientation": "portrait" if portrait else "landscape",
            "how_to_read": "cells run left-to-right, top-to-bottom; every cell shows its timestamp (mm:ss.ff) and shot id; "
                           "cell timestamps are exact sampled pts (not a formula); go to keyframes\\shots\\ or extract a "
                           "full-resolution frame before claiming frame-accurate timing",
        })
        for sh in index["sheets"]:
            sh["file"] = common.rel(run_dir, sheets_dir / sh["file"])
        common.write_json(sheets_dir / "index.json", index)
        log.info(f"contact sheets: {len(index['sheets'])} sheets ({index['cell'][0]}x{index['cell'][1]} cells) in {time.time() - t1:.1f}s")

        out = {
            "source": common.rel(run_dir, src), "duration_s": round(duration, 3), "fps": round(fps, 4),
            "display": [w, h], "orientation": "portrait" if portrait else "landscape",
            "n_shots": len(shots), "median_shot_s": median_shot,
            "sample_fps": round(sample_fps, 4), "sample_fps_reason": reason, "sample_max_side": ms,
            "n_sampled": len(sampled), "n_shot_frames": len(shot_frames),
            "shot_frames": shot_frames, "sampled": sampled,
            "contact_sheets": [sh["file"] for sh in index["sheets"]],
            "contact_sheet_index": common.rel(run_dir, sheets_dir / "index.json"),
            "naming": {"shots": "shot-<id>-<first|mid|last>-<MMmSS.ffs>.jpg (full resolution, q=2)",
                       "sampled": "t-<MMmSS.ffs>.jpg (long side <= sample_max_side, q=3)"},
            "timing_s": round(time.time() - t0, 2),
        }
        common.write_json(mdir / "keyframes.json", out)
        common.state_add_files(run_dir, "10-measure", [mdir / "keyframes.json", sheets_dir / "index.json"])
        log.info(f"done: {len(shot_frames)} shot frames, {len(sampled)} sampled frames, {len(index['sheets'])} sheets in {out['timing_s']}s")
        return 0
    except Exception as e:
        import traceback
        log.error(f"keyframes failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
