"""join_clips.py - normalise clips to one canvas and concatenate them in order (re-join edited segments, quick previews).

Usage: python join_clips.py --run-dir <run> --out joined.mp4 [--width 1080 --height 1920 --fps 30] [options]
       python join_clips.py --clips a.mp4 b.mp4 ... --out joined.mp4 [--width 1080 --height 1920 --fps 30] [options]
Options: [--crf 18] [--preset medium] [--no-audio] [--work <dir>] [--keep-work] [--quiet]

--run-dir picks 80-generated\\clip-*.mp4 in name order (or manifest.json "clips" order when present).
Every clip is normalised once (scale to fit + pad to --width x --height, setsar 1, --fps, yuv420p, libx264 crf --crf,
audio resampled to 48 kHz stereo AAC 192k; a silent track is synthesised when a clip has none), then the normalised
files are concatenated with the concat demuxer in stream-copy mode (no second encode). Verified with ffprobe;
writes <out>.json next to the output (per-clip in/out specs, offsets, total duration). Exit 0 ok, 1 failure, 2 bad args.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="normalise + concatenate clips")
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--clips", nargs="*", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--work", default=None, help="folder for normalised intermediates (default <out dir>\\_join-work)")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    out = Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    run_dir = Path(a.run_dir).resolve() if a.run_dir else None
    log = common.script_log(run_dir, "join_clips", a.quiet) if run_dir else common.Log(out.parent / "join_clips.log", "join_clips", a.quiet)
    clips: list[Path] = []
    if a.clips:
        clips = [Path(c).expanduser().resolve() for c in a.clips]
    elif run_dir:
        gen = run_dir / "80-generated"
        man = common.read_json(gen / "manifest.json") or {}
        order = [c.get("file") for c in man.get("clips", []) if isinstance(c, dict) and c.get("file")] if man else []
        if order:
            clips = [(gen / f) if not Path(f).is_absolute() else Path(f) for f in order]
        else:
            clips = sorted(gen.glob("clip-*.mp4"))
    if not clips:
        print("no clips given (--clips ...) or found in <run>/80-generated", file=sys.stderr)
        return 2
    missing = [c for c in clips if not c.exists()]
    if missing:
        print("missing clips: " + ", ".join(str(m) for m in missing), file=sys.stderr)
        return 2
    try:
        ff = common.ffmpeg()
        work = common.ensure_dir(Path(a.work).resolve() if a.work else out.parent / "_join-work")
        W, H, F = a.width, a.height, a.fps
        gop = int(round(F * 2))
        rows, norm_files = [], []
        log.info(f"normalising {len(clips)} clips to {W}x{H} @ {F:g} fps")
        for i, c in enumerate(clips, 1):
            pj = common.ffprobe_json(c, log=log)
            v = common.video_stream(pj) or {}
            has_a = bool(common.audio_streams(pj))
            dur = common.media_duration(pj)
            dest = work / f"norm-{i:02d}.mp4"
            vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                  f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={F:g},format=yuv420p")
            args = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(c)]
            if not a.no_audio and not has_a:
                args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            args += ["-map", "0:v:0"]
            if not a.no_audio:
                args += ["-map", "0:a:0" if has_a else "1:a:0"]
            args += ["-vf", vf, "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-profile:v", "high", "-level", "4.1",
                     "-g", str(gop), "-keyint_min", str(int(round(F))), "-pix_fmt", "yuv420p", "-video_track_timescale", "90000"]
            if a.no_audio:
                args += ["-an"]
            else:
                args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
                if not has_a:
                    args += ["-shortest"]
            args += ["-movflags", "+faststart", str(dest)]
            t1 = time.time()
            res = common.run_cmd(args, log=log, timeout=3600)
            if not res.ok or not dest.exists():
                raise RuntimeError(f"normalising {c.name} failed: {res.tail(6)}")
            pj2 = common.ffprobe_json(dest, log=log)
            v2 = common.video_stream(pj2) or {}
            rows.append({"index": i, "input": str(c), "in": {"width": v.get("width"), "height": v.get("height"),
                                                              "fps": round(common.stream_fps(v), 3), "duration_s": round(dur, 3),
                                                              "codec": v.get("codec_name"), "has_audio": has_a},
                         "normalised": common.rel(out.parent, dest),
                         "out": {"width": v2.get("width"), "height": v2.get("height"), "fps": round(common.stream_fps(v2), 3),
                                 "duration_s": round(common.media_duration(pj2), 3)}, "elapsed_s": round(time.time() - t1, 2)})
            norm_files.append(dest)
            log.info(f"  {i:02d} {c.name}: {v.get('width')}x{v.get('height')}@{common.stream_fps(v):g} {dur:.2f}s -> normalised ({rows[-1]['elapsed_s']}s)")
        lst = work / "concat.txt"
        lines = ["file '" + str(p).replace("\\", "/").replace("'", "'\\''") + "'" for p in norm_files]
        common.write_text(lst, "\n".join(lines) + "\n")
        res = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                              "-c", "copy", "-movflags", "+faststart", str(out)], log=log, timeout=3600)
        if not res.ok or not out.exists():
            raise RuntimeError(f"concat failed: {res.tail(6)}")
        pj3 = common.ffprobe_json(out, log=log)
        v3 = common.video_stream(pj3) or {}
        total = common.media_duration(pj3)
        expected = sum(r["out"]["duration_s"] for r in rows)
        offsets, acc = [], 0.0
        for r in rows:
            offsets.append({"index": r["index"], "start": round(acc, 3), "end": round(acc + r["out"]["duration_s"], 3)})
            acc += r["out"]["duration_s"]
        info = {"output": str(out), "width": v3.get("width"), "height": v3.get("height"), "fps": round(common.stream_fps(v3), 3),
                "codec": v3.get("codec_name"), "has_audio": bool(common.audio_streams(pj3)), "duration_s": round(total, 3),
                "expected_duration_s": round(expected, 3), "duration_delta_s": round(total - expected, 3),
                "size_bytes": out.stat().st_size, "clips": rows, "offsets": offsets,
                "method": f"per-clip normalise (scale+pad {W}x{H}, fps {F:g}, libx264 crf {a.crf} {a.preset}, aac 48k stereo) then concat demuxer -c copy",
                "timing_s": round(time.time() - t0, 2)}
        common.write_json(out.with_suffix(out.suffix + ".json"), info)
        if not a.keep_work:
            shutil.rmtree(work, ignore_errors=True)
        log.info(f"joined {len(rows)} clips -> {out.name}: {v3.get('width')}x{v3.get('height')} @ {common.stream_fps(v3):g} fps, "
                 f"{total:.2f}s (expected {expected:.2f}s), {common.human_size(out.stat().st_size)} in {info['timing_s']}s")
        print(str(out))
        return 0
    except Exception as e:
        import traceback
        log.error(f"join_clips failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
