"""intake.py - Stage 0: create the run folder and normalise the input video.

Usage:
  python intake.py <path-or-url> --run-root C:\\...\\runs [--slug s] [--run-dir existing] [--cookies-from-browser chrome] [--quiet]

- creates runs\\<YYYYMMDD-HHMMSS-slug>\\ with the full skeleton (or reuses --run-dir)
- local file  -> copied to 00-input\\source.<ext>; 00-input\\source.mp4 is guaranteed
                 (plain copy when already h264/yuv420p mp4, stream copy when the codecs allow it,
                 else transcode libx264 crf 18 + aac)
- http(s) link -> downloaded with yt-dlp (best mp4 up to 1080p, merged) into 00-input\\, link.txt written
- writes 00-input\\input.json and state.json (stage "intake", next_step "measure")
- prints the run dir as the LAST stdout line (measure_all.py reads it)
Exit codes: 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mpg", ".mpeg", ".ts", ".m2ts", ".wmv", ".flv", ".3gp", ".gif"}


def is_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s.strip(), re.I))


def default_slug(source: str) -> str:
    if is_url(source):
        host = urlparse(source).netloc.lower()
        host = re.sub(r"^(www|m|vm|vt)\.", "", host)
        return common.slugify(host.split(".")[0] or "link", 24)
    return common.slugify(Path(source).stem, 32)


def download_link(url: str, input_dir: Path, log: common.Log, cookies_from_browser: str | None) -> Path:
    ffdir = str(Path(common.ffmpeg()).parent)
    out_tpl = str(input_dir / "download.%(ext)s")
    fmt = "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4][height<=1080]/bv*[height<=1080]+ba/b"
    args = [common.python_exe(), "-m", "yt_dlp", "--no-playlist", "--no-progress", "-f", fmt,
            "--merge-output-format", "mp4", "--write-info-json", "--ffmpeg-location", ffdir,
            "-o", out_tpl, url]
    if cookies_from_browser:
        args[3:3] = ["--cookies-from-browser", cookies_from_browser]
    log.info(f"downloading with yt-dlp: {url}")
    res = common.run_cmd(args, log=log, timeout=1800)
    if not res.ok:
        raise RuntimeError(f"yt-dlp failed (rc={res.returncode}):\n{res.tail(15)}")
    cands = [p for p in input_dir.glob("download.*") if p.suffix.lower() in VIDEO_EXTS]
    if not cands:
        raise RuntimeError("yt-dlp reported success but no video file named download.* was found in " + str(input_dir))
    cands.sort(key=lambda p: p.stat().st_size, reverse=True)
    return cands[0]


def ensure_source_mp4(input_dir: Path, local: Path, log: common.Log) -> tuple[Path, Path, str]:
    """Returns (source_copy, source_mp4, conversion). local may already live inside input_dir."""
    ext = local.suffix.lower() or ".bin"
    probe = common.ffprobe_json(local, log=log)
    v = common.video_stream(probe)
    if not v:
        raise RuntimeError(f"no video stream in {local}")
    auds = common.audio_streams(probe)
    vcodec = v.get("codec_name")
    pix = v.get("pix_fmt")
    acodec = auds[0].get("codec_name") if auds else None
    copyable_codecs = vcodec == "h264" and pix == "yuv420p" and (acodec in (None, "aac", "mp3"))
    target = input_dir / "source.mp4"

    if ext == ".mp4" and copyable_codecs:
        if local.resolve() != target.resolve():
            shutil.copy2(local, target)
            if local.parent.resolve() == input_dir.resolve() and local.name.startswith("download."):
                local.unlink(missing_ok=True)
        return target, target, "copy"

    # keep the original bytes next to the normalised mp4
    if ext == ".mp4":
        original = input_dir / "source-original.mp4"
    else:
        original = input_dir / f"source{ext}"
    if local.resolve() != original.resolve():
        if local.parent.resolve() == input_dir.resolve() and local.name.startswith("download."):
            local.replace(original)
        else:
            shutil.copy2(local, original)

    ff = common.ffmpeg()
    if copyable_codecs:
        log.info(f"stream-copying {original.name} -> source.mp4")
        res = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(original),
                              "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-movflags", "+faststart", str(target)],
                             log=log, timeout=1800)
        if res.ok and target.exists() and target.stat().st_size > 0:
            try:
                common.ffprobe_json(target, log=log)
                return original, target, "stream-copy"
            except Exception:
                pass
        log.warn("stream copy failed, transcoding instead")
    log.info(f"transcoding {original.name} -> source.mp4 (libx264 crf 18, aac 192k)")
    args = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(original), "-map", "0:v:0", "-map", "0:a:0?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(target)]
    res = common.run_cmd(args, log=log, timeout=3600)
    if not res.ok or not target.exists():
        raise RuntimeError(f"transcode failed rc={res.returncode}:\n{res.tail(15)}")
    return original, target, "transcode"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="analyze-stack intake: run folder + normalised source.mp4")
    ap.add_argument("source", help="local video path or http(s) link")
    ap.add_argument("--run-root", default=str(common.DEFAULT_RUN_ROOT))
    ap.add_argument("--slug", default=None, help="run-id suffix (default: file stem / link host)")
    ap.add_argument("--run-dir", default=None, help="reuse an existing run folder instead of creating one")
    ap.add_argument("--cookies-from-browser", default=None, help="yt-dlp --cookies-from-browser value (e.g. chrome)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    t0 = time.time()
    source = a.source.strip().strip('"')
    if a.run_dir:
        run_dir = common.ensure_skeleton(Path(a.run_dir).resolve())
    else:
        run_dir = common.new_run_dir(a.run_root, a.slug or default_slug(source))
    log = common.script_log(run_dir, "intake", a.quiet)
    log.info(f"run dir: {run_dir}")
    input_dir = run_dir / "00-input"

    try:
        info = {"origin": None, "original_name": None, "original_url": None, "ingested_at": common.now_iso()}
        if is_url(source):
            info["origin"] = "url"
            info["original_url"] = source
            common.write_text(input_dir / "link.txt", source + "\n")
            local = download_link(source, input_dir, log, a.cookies_from_browser)
            info["original_name"] = local.name
            ij = list(input_dir.glob("download.info.json"))
            if ij:
                meta = common.read_json(ij[0], default={}) or {}
                info["yt_dlp_info"] = common.rel(run_dir, ij[0])
                info["title"] = meta.get("title")
                info["uploader"] = meta.get("uploader") or meta.get("channel")
                info["upload_date"] = meta.get("upload_date")
                info["view_count"] = meta.get("view_count")
                info["like_count"] = meta.get("like_count")
                info["webpage_url"] = meta.get("webpage_url")
        else:
            local = Path(source).expanduser().resolve()
            if not local.exists():
                raise FileNotFoundError(f"input file not found: {local}")
            info["origin"] = "file"
            info["original_name"] = local.name
            info["original_path"] = str(local)
        info["original_size_bytes"] = local.stat().st_size
        log.info(f"hashing {local.name} ({common.human_size(local.stat().st_size)})")
        info["original_sha1"] = common.sha1_file(local)

        source_copy, source_mp4, conversion = ensure_source_mp4(input_dir, local, log)
        info["source_copy"] = common.rel(run_dir, source_copy)
        info["source_mp4"] = common.rel(run_dir, source_mp4)
        info["conversion"] = conversion
        info["source_mp4_size_bytes"] = source_mp4.stat().st_size
        info["source_mp4_sha1"] = info["original_sha1"] if conversion == "copy" else common.sha1_file(source_mp4)
        probe = common.ffprobe_json(source_mp4, log=log)
        v = common.video_stream(probe) or {}
        info["quick_probe"] = {"duration_s": round(common.media_duration(probe), 3), "width": v.get("width"),
                               "height": v.get("height"), "fps": round(common.stream_fps(v), 3),
                               "video_codec": v.get("codec_name"), "has_audio": bool(common.audio_streams(probe))}
        info["elapsed_s"] = round(time.time() - t0, 2)
        common.write_json(input_dir / "input.json", info)

        files = [p for p in input_dir.iterdir() if p.is_file()]
        common.state_set(run_dir, stage="intake", next_step="measure", source=info["source_mp4"], input=info["quick_probe"])
        common.state_add_files(run_dir, "00-input", files)
        log.info(f"intake done ({conversion}) in {info['elapsed_s']}s: {info['quick_probe']}")
    except Exception as e:
        log.error(str(e))
        common.state_set(run_dir, stage="intake-failed", next_step="intake", error=str(e))
        print(str(run_dir))
        return 1
    print(str(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
