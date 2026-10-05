"""clip_frames.py - post-generation clip QA input: first frame, last frame, 1 fps frames and one contact sheet for a clip.

Usage: python clip_frames.py <clip.mp4> --out <dir> [--fps 1] [--max-side 1280] [--quiet]

Writes <dir>\\first-00m00.00s.jpg, last-<t>.jpg (full resolution, q=2), f-<MMmSS.ffs>.jpg at --fps (long side <= --max-side),
<dir>\\sheet.jpg (4 columns, as many rows as needed, first and last frames included) and <dir>\\frames.json (index + probe).
Exit 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="clip frames + contact sheet")
    ap.add_argument("clip")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=1.0)
    ap.add_argument("--max-side", type=int, default=1280)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    clip = Path(a.clip).expanduser().resolve()
    out = common.ensure_dir(Path(a.out).expanduser().resolve())
    log = common.Log(out / "clip_frames.log", "clip_frames", a.quiet)
    try:
        if not clip.exists():
            raise FileNotFoundError(clip)
        ff = common.ffmpeg()
        pj = common.ffprobe_json(clip, log=log)
        v = common.video_stream(pj) or {}
        if not v:
            raise RuntimeError("no video stream")
        fps = common.stream_fps(v) or 24.0
        dur = common.media_duration(pj)
        w, h = int(v.get("width") or 0), int(v.get("height") or 0)
        portrait = h >= w
        for old in out.glob("*.jpg"):
            old.unlink(missing_ok=True)
        # first + last (full res)
        first = out / f"first-{common.ts_name(0)}.jpg"
        last_t = max(0.0, dur - 1.0 / fps)
        last = out / f"last-{common.ts_name(last_t)}.jpg"
        r1 = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(clip), "-frames:v", "1", "-q:v", "2", str(first)], log=log)
        r2 = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-sseof", f"-{max(0.05, 1.5 / fps):.4f}", "-i", str(clip),
                             "-frames:v", "1", "-q:v", "2", "-update", "1", str(last)], log=log)
        if not r2.ok or not last.exists():
            r2 = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, last_t - 0.4 / fps):.4f}", "-i", str(clip),
                                 "-frames:v", "1", "-q:v", "2", str(last)], log=log)
        # sampled
        ms = a.max_side
        scale = f"scale=-2:'min({ms},ih)'" if portrait else f"scale='min({ms},iw)':-2"
        work = common.ensure_dir(out / "_work")
        for old in work.glob("*.jpg"):
            old.unlink(missing_ok=True)
        res = common.run_cmd([ff, "-hide_banner", "-nostats", "-loglevel", "info", "-y", "-i", str(clip), "-vf",
                              f"fps={a.fps:.6f},{scale},showinfo", "-q:v", "3", str(work / "s-%05d.jpg")], log=log)
        pts = {}
        for line in res.stderr.splitlines():
            m = re.search(r"\bn:\s*(\d+)\s+pts:\s*-?\d+\s+pts_time:(-?[\d.]+)", line)
            if m:
                pts[int(m.group(1))] = float(m.group(2))
        sampled = []
        for k, f in enumerate(sorted(work.glob("s-*.jpg"))):
            t = round(max(0.0, pts.get(k, k / a.fps)), 3)
            dest = out / f"f-{common.ts_name(t)}.jpg"
            f.replace(dest)
            sampled.append({"t": t, "file": dest.name})
        frames = [{"path": first, "t": 0.0, "label": "first 00:00.00"}] + \
                 [{"path": out / s["file"], "t": s["t"]} for s in sampled if s["t"] > 0.01] + \
                 [{"path": last, "t": last_t, "label": f"last {common.fmt_mmss(last_t)}"}]
        rows = max(1, int(math.ceil(len(frames) / 4)))
        index = common.build_contact_sheets(frames, out, portrait=portrait, grid=(4, rows), padding=4, prefix="sheet", quality=88)
        sheet = out / index["sheets"][0]["file"] if index["sheets"] else None
        if sheet and sheet.name != "sheet.jpg":
            sheet.replace(out / "sheet.jpg")
            sheet = out / "sheet.jpg"
        for old in work.glob("*"):
            old.unlink(missing_ok=True)
        work.rmdir()
        info = {"clip": str(clip), "duration_s": round(dur, 3), "fps": round(fps, 3), "width": w, "height": h,
                "codec": v.get("codec_name"), "has_audio": bool(common.audio_streams(pj)), "size_bytes": clip.stat().st_size,
                "first": first.name, "last": last.name, "last_t": round(last_t, 3), "sample_fps": a.fps, "sampled": sampled,
                "sheet": "sheet.jpg", "sheet_cells": index["sheets"][0]["cells"] if index["sheets"] else [],
                "timing_s": round(time.time() - t0, 2)}
        common.write_json(out / "frames.json", info)
        log.info(f"{clip.name}: {dur:.2f}s {w}x{h} @ {fps:.3g} fps -> first, last, {len(sampled)} frames, sheet.jpg in {info['timing_s']}s")
        print(str(out))
        return 0
    except Exception as e:
        import traceback
        log.error(f"clip_frames failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
