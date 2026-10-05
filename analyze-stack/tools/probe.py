"""probe.py - Stage 1: ffprobe the source into 10-measure\\probe.json.

Usage: python probe.py --run-dir <run> [--source <file>] [--quiet]

probe.json fields: duration_s, width, height, rotation, display_width/height (rotation corrected),
aspect_ratio (reduced, e.g. "9:16"), aspect_nearest ("9:16"/"16:9"/"1:1"/"4:5"/...), aspect_decimal,
fps {r_frame_rate, avg_frame_rate, value}, nb_frames (+ source: "stream"|"estimated"), video {codec, profile,
level, bitrate, pix_fmt, color_space/primaries/transfer/range, sar/dar}, audio [{index, codec, profile,
sample_rate, channels, channel_layout, bitrate, duration}], container {format_name, format_long_name,
bitrate, size_bytes, tags}, has_audio, orientation, raw (full ffprobe output).
Exit: 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

COMMON_RATIOS = {"9:16": 9 / 16, "16:9": 16 / 9, "1:1": 1.0, "4:5": 0.8, "5:4": 1.25, "4:3": 4 / 3, "3:4": 0.75,
                 "21:9": 21 / 9, "9:21": 9 / 21, "2:3": 2 / 3, "3:2": 1.5, "2:1": 2.0, "1:2": 0.5}


def rotation_of(v: dict) -> int:
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                rot = int(round(float(sd["rotation"])))
            except (TypeError, ValueError):
                pass
    if not rot:
        try:
            rot = int(round(float((v.get("tags") or {}).get("rotate", 0))))
        except (TypeError, ValueError):
            rot = 0
    return rot % 360


def reduce_ratio(w: int, h: int) -> str:
    if not w or not h:
        return "?"
    g = math.gcd(int(w), int(h))
    return f"{int(w) // g}:{int(h) // g}"


def nearest_ratio(w: int, h: int, tol: float = 0.03) -> str | None:
    if not w or not h:
        return None
    r = w / h
    best = min(COMMON_RATIOS.items(), key=lambda kv: abs(kv[1] - r))
    return best[0] if abs(best[1] - r) / best[1] <= tol else None


def build(probe: dict, src: Path) -> dict:
    v = common.video_stream(probe) or {}
    auds = common.audio_streams(probe)
    fmt = probe.get("format", {})
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    rot = rotation_of(v)
    dw, dh = (h, w) if rot in (90, 270) else (w, h)
    r_fps = common.parse_fraction(v.get("r_frame_rate"))
    a_fps = common.parse_fraction(v.get("avg_frame_rate"))
    fps = a_fps if 0 < a_fps <= 240 else r_fps
    duration = common.media_duration(probe)
    nb = v.get("nb_frames")
    nb_src = "stream"
    try:
        nb = int(nb)
    except (TypeError, ValueError):
        nb = int(round(duration * fps)) if fps else None
        nb_src = "estimated"
    vbr = v.get("bit_rate") or fmt.get("bit_rate")
    out = {
        "source": str(src),
        "duration_s": round(duration, 3),
        "duration_hms": common.fmt_hms(duration),
        "width": w, "height": h, "rotation": rot,
        "display_width": dw, "display_height": dh,
        "orientation": "portrait" if dh > dw else ("landscape" if dw > dh else "square"),
        "aspect_ratio": reduce_ratio(dw, dh),
        "aspect_nearest": nearest_ratio(dw, dh),
        "aspect_decimal": round(dw / dh, 4) if dh else None,
        "fps": {"r_frame_rate": round(r_fps, 4), "avg_frame_rate": round(a_fps, 4), "value": round(fps, 4),
                "r_frame_rate_raw": v.get("r_frame_rate"), "avg_frame_rate_raw": v.get("avg_frame_rate")},
        "nb_frames": nb, "nb_frames_source": nb_src,
        "video": {"codec": v.get("codec_name"), "codec_long": v.get("codec_long_name"), "profile": v.get("profile"),
                  "level": v.get("level"), "bitrate": int(vbr) if str(vbr).isdigit() else None,
                  "pix_fmt": v.get("pix_fmt"), "color_space": v.get("color_space"),
                  "color_primaries": v.get("color_primaries"), "color_transfer": v.get("color_transfer"),
                  "color_range": v.get("color_range"), "sar": v.get("sample_aspect_ratio"),
                  "dar": v.get("display_aspect_ratio"), "time_base": v.get("time_base"),
                  "start_time": common.parse_fraction(v.get("start_time")), "stream_index": v.get("index")},
        "audio": [{"index": s.get("index"), "codec": s.get("codec_name"), "profile": s.get("profile"),
                   "sample_rate": int(s.get("sample_rate") or 0), "channels": s.get("channels"),
                   "channel_layout": s.get("channel_layout"),
                   "bitrate": int(s["bit_rate"]) if str(s.get("bit_rate", "")).isdigit() else None,
                   "duration": round(common.parse_fraction(s.get("duration")), 3)} for s in auds],
        "has_audio": bool(auds),
        "container": {"format_name": fmt.get("format_name"), "format_long_name": fmt.get("format_long_name"),
                      "bitrate": int(fmt["bit_rate"]) if str(fmt.get("bit_rate", "")).isdigit() else None,
                      "size_bytes": int(fmt.get("size") or src.stat().st_size), "nb_streams": fmt.get("nb_streams"),
                      "tags": fmt.get("tags", {})},
        "probed_at": common.now_iso(),
        "raw": probe,
    }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ffprobe -> 10-measure/probe.json")
    common.add_std_args(ap)
    ap.add_argument("--source", default=None, help="override the video (default 00-input/source.mp4)")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "probe", a.quiet)
    try:
        src = Path(a.source).resolve() if a.source else common.source_mp4(run_dir)
        probe = common.ffprobe_json(src, log=log)
        out = build(probe, src)
        out["timing_s"] = round(time.time() - t0, 2)
        dst = common.measure_dir(run_dir) / "probe.json"
        common.write_json(dst, out)
        common.state_add_file(run_dir, "10-measure", dst)
        log.info(f"{out['duration_s']}s {out['display_width']}x{out['display_height']} {out['aspect_ratio']} "
                 f"{out['fps']['value']} fps {out['video']['codec']} audio={out['has_audio']} -> probe.json "
                 f"({out['timing_s']}s)")
        return 0
    except Exception as e:
        log.error(f"probe failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
