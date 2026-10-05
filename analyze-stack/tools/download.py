"""download.py - stream a URL to disk (generated clips from Higgsfield result URLs, reference files).

Usage: python download.py <url> --out <file> [--retries 3] [--timeout 120] [--min-bytes 1024] [--probe] [--quiet]

requests streaming download with connect/read timeouts, exponential-backoff retries, Content-Length check, content-type note;
--probe runs ffprobe and requires a video stream (for clips). Prints the final path and size as the last stdout line:
"<path> <bytes> bytes". Exit 0 ok, 1 failure, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="download a URL to a file")
    ap.add_argument("url")
    ap.add_argument("--out", required=True)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=120.0, help="read timeout in seconds (connect timeout 15 s)")
    ap.add_argument("--min-bytes", type=int, default=1024)
    ap.add_argument("--probe", action="store_true", help="verify with ffprobe that the file has a video stream")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if not a.url.lower().startswith(("http://", "https://")):
        print("url must start with http:// or https://", file=sys.stderr)
        return 2
    import requests
    out = Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    log = common.Log(out.parent / "download.log", "download", a.quiet)
    last_err = None
    for attempt in range(1, max(1, a.retries) + 1):
        t0 = time.time()
        tmp = out.with_suffix(out.suffix + ".part")
        try:
            log.info(f"GET {a.url} (attempt {attempt}/{a.retries})")
            with requests.get(a.url, stream=True, timeout=(15, a.timeout), headers={"User-Agent": "analyze-stack/1.0"}) as r:
                r.raise_for_status()
                ctype = r.headers.get("Content-Type", "")
                expected = int(r.headers.get("Content-Length") or 0)
                n = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        if chunk:
                            f.write(chunk)
                            n += len(chunk)
            if expected and n != expected:
                raise IOError(f"short read {n}/{expected} bytes")
            if n < a.min_bytes:
                raise IOError(f"only {n} bytes received (min {a.min_bytes})")
            if out.exists():
                out.unlink()
            tmp.replace(out)
            el = round(time.time() - t0, 2)
            info = {"url": a.url, "file": str(out), "bytes": n, "content_type": ctype, "content_length_header": expected or None,
                    "elapsed_s": el, "mbps": round(n * 8 / 1e6 / el, 1) if el > 0 else None, "attempt": attempt}
            if "text/html" in ctype.lower():
                log.warn("content-type is text/html - this is probably an error page or a login interstitial, not a media file")
            if a.probe:
                pj = common.ffprobe_json(out, log=log)
                v = common.video_stream(pj)
                if not v:
                    raise RuntimeError("downloaded file has no video stream")
                info["probe"] = {"duration_s": round(common.media_duration(pj), 3), "width": v.get("width"), "height": v.get("height"),
                                 "fps": round(common.stream_fps(v), 3), "codec": v.get("codec_name"), "has_audio": bool(common.audio_streams(pj))}
            log.info(json.dumps(info))
            print(f"{out} {n} bytes")
            return 0
        except Exception as e:
            last_err = e
            log.warn(f"attempt {attempt} failed: {e}")
            tmp.unlink(missing_ok=True)
            if attempt < a.retries:
                time.sleep(min(30, 2 ** attempt))
    log.error(f"download failed after {a.retries} attempts: {last_err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
