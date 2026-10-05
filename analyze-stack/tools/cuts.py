"""cuts.py - Stage 1: shot cuts, shots and pacing -> 10-measure\\cuts.json + shots.json.

Usage: python cuts.py --run-dir <run> [--content-threshold 27] [--adaptive-threshold 3] [--min-scene-len 6]
                      [--hard 0.30] [--broad 0.08] [--scdet 10] [--merge-window 0.15] [--no-verify] [--quiet]

Detectors (all run, results merged):
  * PySceneDetect ContentDetector(threshold=27)       source "content"
  * PySceneDetect AdaptiveDetector(adaptive_threshold=3) source "adaptive"
  * ffmpeg select='gt(scene,0.08)' (broad candidates)  source "scene008"; hits with score >= 0.30 -> "scene030" (hard)
  * ffmpeg scdet=threshold=10                          source "scdet"
Hits are clustered within --merge-window (0.15 s). confidence = number of strong detectors agreeing
(content, adaptive, scene030, scdet: 0-4). Every cluster is verified with an OpenCV frame pair
(mean abs diff + HSV histogram correlation of the frame before vs the frame at the cut).
type "hard": confidence >= 2, or confidence == 1 confirmed by the frame pair. Otherwise "candidate".
shots.json = hard cuts + 1 shots, pacing (mean/median/min/max shot length, cuts per 10 s sliding window,
fastest/slowest windows), plus ffmpeg freezedetect / blackdetect spans.
Exit 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

STRONG = ("content", "adaptive", "scene030", "scdet")
PRIORITY = {"content": 0, "adaptive": 1, "scene030": 2, "scdet": 3, "scene008": 4}


# ------------------------------------------------------------------ detectors
def run_pyscenedetect(src: Path, kind: str, threshold: float, min_scene_len: int, log) -> dict:
    from scenedetect import open_video, SceneManager, ContentDetector, AdaptiveDetector
    t0 = time.time()
    video = open_video(str(src))
    sm = SceneManager()
    if kind == "content":
        sm.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))
    else:
        sm.add_detector(AdaptiveDetector(adaptive_threshold=threshold, min_scene_len=min_scene_len))
    sm.detect_scenes(video, show_progress=False)
    scenes = sm.get_scene_list()
    cuts = []
    for s, _e in scenes[1:]:
        try:
            t = float(s.seconds)
        except AttributeError:  # older API
            t = float(s.get_seconds())
        cuts.append(round(t, 3))
    log.info(f"PySceneDetect {kind} (thr={threshold}): {len(cuts)} cuts in {time.time() - t0:.1f}s")
    return {"cuts": cuts, "elapsed_s": round(time.time() - t0, 2), "threshold": threshold,
            "min_scene_len_frames": min_scene_len, "n_scenes": len(scenes)}


def parse_metadata_file(path: Path, key: str) -> list[tuple[float, float]]:
    """Parse ffmpeg metadata=print output: 'frame:N pts:P pts_time:T' then 'lavfi.<key>=S'."""
    out = []
    if not path.exists():
        return out
    t = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"pts_time:\s*(-?[\d.]+)", line)
        if m:
            t = float(m.group(1))
            continue
        m = re.match(rf"\s*{re.escape(key)}=(-?[\d.]+)", line)
        if m and t is not None:
            out.append((round(t, 3), float(m.group(1))))
            t = None
    return out


def run_ffmpeg_scene(src: Path, work: Path, broad: float, log) -> dict:
    t0 = time.time()
    name = "scene-broad.txt"
    (work / name).unlink(missing_ok=True)
    args = [common.ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(src),
            "-vf", f"select='gt(scene,{broad})',metadata=print:file={name}", "-an", "-f", "null", "-"]
    res = common.run_cmd(args, log=log, cwd=work, timeout=3600)
    hits = parse_metadata_file(work / name, "lavfi.scene_score")
    log.info(f"ffmpeg scene>{broad}: {len(hits)} raw hits in {time.time() - t0:.1f}s")
    return {"hits": hits, "elapsed_s": round(time.time() - t0, 2), "ok": res.ok, "threshold": broad}


def run_ffmpeg_scdet(src: Path, work: Path, thr: float, log) -> dict:
    t0 = time.time()
    name = "scdet.txt"
    (work / name).unlink(missing_ok=True)
    args = [common.ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(src),
            "-vf", f"scdet=threshold={thr}:sc_pass=1,metadata=print:file={name}", "-an", "-f", "null", "-"]
    res = common.run_cmd(args, log=log, cwd=work, timeout=3600)
    hits = parse_metadata_file(work / name, "lavfi.scd.score")
    log.info(f"ffmpeg scdet={thr}: {len(hits)} hits in {time.time() - t0:.1f}s")
    return {"hits": hits, "elapsed_s": round(time.time() - t0, 2), "ok": res.ok, "threshold": thr}


def run_freeze_black(src: Path, log) -> dict:
    t0 = time.time()
    args = [common.ffmpeg(), "-hide_banner", "-nostats", "-loglevel", "info", "-i", str(src),
            "-vf", "freezedetect=n=0.003:d=0.5,blackdetect=d=0.3:pix_th=0.10", "-an", "-f", "null", "-"]
    res = common.run_cmd(args, log=log, timeout=3600)
    txt = res.stderr
    freezes, blacks = [], []
    cur = {}
    for line in txt.splitlines():
        m = re.search(r"freeze_start:\s*(-?[\d.]+)", line)
        if m:
            cur = {"start": float(m.group(1))}
        m = re.search(r"freeze_end:\s*(-?[\d.]+)", line)
        if m and cur:
            cur["end"] = float(m.group(1))
            cur["duration"] = round(cur["end"] - cur["start"], 3)
            freezes.append(cur)
            cur = {}
        m = re.search(r"black_start:\s*(-?[\d.]+)\s+black_end:\s*(-?[\d.]+)\s+black_duration:\s*(-?[\d.]+)", line)
        if m:
            blacks.append({"start": float(m.group(1)), "end": float(m.group(2)), "duration": float(m.group(3))})
    log.info(f"freezedetect: {len(freezes)} spans, blackdetect: {len(blacks)} spans ({time.time() - t0:.1f}s)")
    return {"freeze": freezes, "black": blacks, "elapsed_s": round(time.time() - t0, 2),
            "params": "freezedetect=n=0.003:d=0.5, blackdetect=d=0.3:pix_th=0.10"}


# ------------------------------------------------------------------ merging + verification
def cluster_hits(hits: list[dict], window: float) -> list[dict]:
    """hits: [{t, score, source}] -> clusters merged within `window` seconds of the cluster's first hit."""
    hits = sorted(hits, key=lambda h: (h["t"], PRIORITY.get(h["source"], 9)))
    clusters = []
    for h in hits:
        if clusters and h["t"] - clusters[-1]["first_t"] <= window:
            clusters[-1]["hits"].append(h)
        else:
            clusters.append({"first_t": h["t"], "hits": [h]})
    out = []
    for c in clusters:
        by_src = {}
        for h in c["hits"]:
            by_src.setdefault(h["source"], []).append(h)
        best_src = min(by_src.keys(), key=lambda s: PRIORITY.get(s, 9))
        t = min(h["t"] for h in by_src[best_src])
        scores = [h["score"] for h in c["hits"] if h.get("score") is not None and h["source"] in ("scene008", "scene030")]
        strong = sorted({s for s in by_src if s in STRONG}, key=lambda s: PRIORITY[s])
        out.append({"t": round(t, 3), "score": round(max(scores), 3) if scores else None,
                    "sources": sorted(by_src.keys(), key=lambda s: PRIORITY.get(s, 9)),
                    "strong_sources": strong, "confidence": len(strong),
                    "n_hits": len(c["hits"]), "span_s": round(max(h["t"] for h in c["hits"]) - c["first_t"], 3)})
    return out


def verify_frame_pairs(src: Path, clusters: list[dict], fps: float, log, max_checks: int = 600) -> None:
    """Add frame_pair {mad, hist_corr, confirms} to each cluster by comparing the frame before the cut with the cut frame."""
    try:
        import cv2
        import numpy as np
    except Exception as e:  # pragma: no cover
        log.warn(f"OpenCV unavailable, skipping frame-pair verification: {e}")
        return
    if not clusters:
        return
    if len(clusters) > max_checks:
        log.warn(f"{len(clusters)} clusters > {max_checks}; verifying only single-source ones")
        todo = [c for c in clusters if c["confidence"] <= 1][:max_checks]
    else:
        todo = clusters
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        log.warn("OpenCV could not open the video; skipping frame-pair verification")
        return
    t0 = time.time()

    def grab(idx: int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, idx))
        ok, fr = cap.read()
        if not ok:
            return None
        small = cv2.resize(fr, (160, int(160 * fr.shape[0] / fr.shape[1]) or 1), interpolation=cv2.INTER_AREA)
        return small

    def hsv_hist(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [18, 8], [0, 180, 0, 256])
        cv2.normalize(h, h)
        return h

    for c in todo:
        idx = int(round(c["t"] * fps))
        a = grab(idx - 1)
        b = grab(idx)
        if a is None or b is None or a.shape != b.shape:
            c["frame_pair"] = {"mad": None, "hist_corr": None, "confirms": None, "note": "frame read failed"}
            continue
        ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
        mad = float(np.mean(cv2.absdiff(ga, gb)))
        corr = float(cv2.compareHist(hsv_hist(a), hsv_hist(b), cv2.HISTCMP_CORREL))
        confirms = bool(mad >= 18.0 or corr < 0.55)
        c["frame_pair"] = {"mad": round(mad, 2), "hist_corr": round(corr, 3), "confirms": confirms,
                           "frames": [idx - 1, idx]}
    cap.release()
    log.info(f"frame-pair verification on {len(todo)} clusters in {time.time() - t0:.1f}s "
             f"(rule: mean-abs-diff >= 18 or HSV hist corr < 0.55)")


def classify(clusters: list[dict]) -> None:
    for c in clusters:
        fp = c.get("frame_pair", {}) or {}
        conf = c["confidence"]
        if conf >= 2:
            c["type"] = "hard"
            c["why"] = f"{conf} detectors agree"
        elif conf == 1 and fp.get("confirms") is True:
            c["type"] = "hard"
            c["why"] = f"{c['strong_sources'][0]} + frame pair confirms"
        elif conf == 1 and fp.get("confirms") is None:
            c["type"] = "hard" if c["strong_sources"][0] in ("content", "scene030") else "candidate"
            c["why"] = f"{c['strong_sources'][0]} only, frame pair unavailable"
        else:
            c["type"] = "candidate"
            c["why"] = "single weak source" if conf == 1 else "broad-threshold hit only"


def build_shots(cuts: list[dict], duration: float, fps: float) -> dict:
    hard = [c["t"] for c in cuts if c["type"] == "hard" and 0.05 < c["t"] < duration - 0.05]
    bounds = [0.0] + sorted(hard) + [round(duration, 3)]
    shots = []
    cut_by_t = {c["t"]: c for c in cuts}
    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        cut_in = cut_by_t.get(s) if i > 0 else None
        shots.append({"id": i + 1, "start": round(s, 3), "end": round(e, 3), "duration": round(e - s, 3),
                      "start_hms": common.fmt_hms(s), "end_hms": common.fmt_hms(e),
                      "cut_in": None if cut_in is None else {"t": cut_in["t"], "score": cut_in["score"],
                                                              "confidence": cut_in["confidence"],
                                                              "sources": cut_in["sources"]}})
    durs = [s["duration"] for s in shots]
    n_cuts = len(hard)
    windows = []
    if duration > 0:
        win = 10.0
        step = 1.0
        starts = [i * step for i in range(int(max(0, duration - win)) + 1)] if duration >= win else [0.0]
        for ws in starts:
            we = min(duration, ws + win)
            n = sum(1 for t in hard if ws <= t < we)
            windows.append({"start": round(ws, 1), "end": round(we, 1), "cuts": n})
    fastest = max(windows, key=lambda w: w["cuts"]) if windows else None
    slowest = min(windows, key=lambda w: w["cuts"]) if windows else None
    pacing = {
        "shot_count": len(shots), "cut_count": n_cuts,
        "mean_shot_s": round(statistics.mean(durs), 3) if durs else None,
        "median_shot_s": round(statistics.median(durs), 3) if durs else None,
        "min_shot_s": round(min(durs), 3) if durs else None,
        "max_shot_s": round(max(durs), 3) if durs else None,
        "cuts_per_10s_avg": round(n_cuts / duration * 10, 2) if duration else None,
        "cuts_per_10s_windows": windows,
        "fastest_window": fastest, "slowest_window": slowest,
        "longest_shot": max(shots, key=lambda s: s["duration"])["id"] if shots else None,
        "shortest_shot": min(shots, key=lambda s: s["duration"])["id"] if shots else None,
        "shots_under_1s": sum(1 for d in durs if d < 1.0),
        "shots_over_5s": sum(1 for d in durs if d > 5.0),
    }
    return {"shots": shots, "pacing": pacing}


# ------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="shot cuts + shots + pacing")
    common.add_std_args(ap)
    ap.add_argument("--content-threshold", type=float, default=27.0)
    ap.add_argument("--adaptive-threshold", type=float, default=3.0)
    ap.add_argument("--min-scene-len", type=int, default=6, help="frames (PySceneDetect)")
    ap.add_argument("--hard", type=float, default=0.30, help="ffmpeg scene score for a hard cut")
    ap.add_argument("--broad", type=float, default=0.08, help="ffmpeg scene score for broad candidates")
    ap.add_argument("--scdet", type=float, default=10.0, help="ffmpeg scdet threshold")
    ap.add_argument("--merge-window", type=float, default=0.15, help="seconds; hits closer than this are one cut")
    ap.add_argument("--no-verify", action="store_true", help="skip OpenCV frame-pair verification")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "cuts", a.quiet)
    try:
        src = common.source_mp4(run_dir)
        mdir = common.measure_dir(run_dir)
        work = common.ensure_dir(mdir / "_work")
        probe = common.read_json(mdir / "probe.json")
        if not probe:
            pj = common.ffprobe_json(src, log=log)
            v = common.video_stream(pj) or {}
            duration, fps = common.media_duration(pj), common.stream_fps(v)
        else:
            duration, fps = float(probe["duration_s"]), float(probe["fps"]["value"])
        fps = fps or 30.0
        log.info(f"detecting cuts in {src.name} ({duration:.2f}s @ {fps:.3f} fps)")

        with ThreadPoolExecutor(max_workers=5) as ex:
            f_content = ex.submit(run_pyscenedetect, src, "content", a.content_threshold, a.min_scene_len, log)
            f_adaptive = ex.submit(run_pyscenedetect, src, "adaptive", a.adaptive_threshold, a.min_scene_len, log)
            f_scene = ex.submit(run_ffmpeg_scene, src, work, a.broad, log)
            f_scdet = ex.submit(run_ffmpeg_scdet, src, work, a.scdet, log)
            f_fb = ex.submit(run_freeze_black, src, log)
            content, adaptive = f_content.result(), f_adaptive.result()
            scene, scdet, fb = f_scene.result(), f_scdet.result(), f_fb.result()

        hits = []
        for t in content["cuts"]:
            hits.append({"t": t, "score": None, "source": "content"})
        for t in adaptive["cuts"]:
            hits.append({"t": t, "score": None, "source": "adaptive"})
        for t, s in scene["hits"]:
            if t < 0.05:
                continue
            hits.append({"t": t, "score": s, "source": "scene030" if s >= a.hard else "scene008"})
        for t, s in scdet["hits"]:
            if t < 0.05:
                continue
            hits.append({"t": t, "score": None, "source": "scdet"})
        clusters = cluster_hits(hits, a.merge_window)
        if not a.no_verify:
            verify_frame_pairs(src, clusters, fps, log)
        classify(clusters)
        n_hard = sum(1 for c in clusters if c["type"] == "hard")
        n_cand = len(clusters) - n_hard

        cuts_json = {
            "source": common.rel(run_dir, src), "duration_s": round(duration, 3), "fps": round(fps, 4),
            "merge_window_s": a.merge_window,
            "detectors": {
                "content": {"threshold": a.content_threshold, "min_scene_len_frames": a.min_scene_len,
                            "n": len(content["cuts"]), "elapsed_s": content["elapsed_s"]},
                "adaptive": {"threshold": a.adaptive_threshold, "min_scene_len_frames": a.min_scene_len,
                             "n": len(adaptive["cuts"]), "elapsed_s": adaptive["elapsed_s"]},
                "scene030": {"threshold": a.hard, "n": sum(1 for _t, s in scene["hits"] if s >= a.hard)},
                "scene008": {"threshold": a.broad, "n_raw": len(scene["hits"]), "elapsed_s": scene["elapsed_s"]},
                "scdet": {"threshold": a.scdet, "n": len(scdet["hits"]), "elapsed_s": scdet["elapsed_s"]},
            },
            "rule": "cluster hits within merge_window; confidence = strong detectors agreeing (content, adaptive, "
                    "scene>=hard, scdet); hard = confidence>=2 or (confidence==1 and frame-pair confirms)",
            "n_cuts_hard": n_hard, "n_candidates": n_cand,
            "cuts": [{"t": c["t"], "hms": common.fmt_hms(c["t"]), "score": c["score"], "source": "+".join(c["sources"]),
                      "sources": c["sources"], "confidence": c["confidence"], "type": c["type"], "why": c["why"],
                      "frame_pair": c.get("frame_pair")} for c in clusters],
            "raw_hits": {"content": content["cuts"], "adaptive": adaptive["cuts"],
                         "scene_broad": [[t, s] for t, s in scene["hits"]], "scdet": [[t, s] for t, s in scdet["hits"]]},
        }
        shots = build_shots(cuts_json["cuts"], duration, fps)
        shots_json = {
            "source": cuts_json["source"], "duration_s": round(duration, 3), "fps": round(fps, 4),
            "n_shots": len(shots["shots"]), "method": "shots = hard cuts + 1 (see cuts.json rule)",
            "shots": shots["shots"], "pacing": shots["pacing"],
            "freeze_spans": fb["freeze"], "black_spans": fb["black"], "freeze_black_params": fb["params"],
        }
        elapsed = round(time.time() - t0, 2)
        cuts_json["timing_s"] = elapsed
        shots_json["timing_s"] = elapsed
        common.write_json(mdir / "cuts.json", cuts_json)
        common.write_json(mdir / "shots.json", shots_json)
        common.state_add_files(run_dir, "10-measure", [mdir / "cuts.json", mdir / "shots.json"])
        p = shots["pacing"]
        log.info(f"{n_hard} hard cuts (+{n_cand} candidates) -> {p['shot_count']} shots, mean {p['mean_shot_s']}s, "
                 f"median {p['median_shot_s']}s, {p['cuts_per_10s_avg']} cuts/10s; done in {elapsed}s")
        return 0
    except Exception as e:
        import traceback
        log.error(f"cuts failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
