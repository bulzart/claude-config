"""visual_stats.py - Stage 1: per-frame colour/light/texture stats, per-shot camera motion, style cues -> 10-measure\\visual-stats.json

Usage: python visual_stats.py --run-dir <run> [--motion-rate 8] [--motion-width 320] [--no-motion] [--quiet]

Per sampled frame (keyframes.json "sampled"): dominant palette (k-means k=5, hex + share), brightness (mean V, 0-1),
contrast (grey std, 0-1), saturation (mean S, 0-1), edge density (Canny 100/200 non-zero ratio), colourfulness
(Hasler-Suesstrunk), flat_ratio (Sobel magnitude < 6 on 0-255 grey), noise (mean |grey - median3x3|), colour_entropy_bits.
Per shot (shots.json): camera-motion class from OpenCV Farneback optical flow between frames --motion-rate pairs per second
read straight from the video (pairs never straddle a cut) -> estimateAffinePartial2D (RANSAC) gives translation / scale /
rotation / non-rigid residual; phase correlation as a cross-check. Labels: static, pan-left/right, tilt-up/down, zoom-in/out,
handheld-shaky, subject-motion; magnitudes in px/s at --motion-width. Labels are CAMERA direction (content moves the
opposite way). Thresholds are heuristic (calibrated on handheld POV footage only) - the raw numbers are the reliable part.
Global: palette k=8, edge-density distribution, palette size, flat-colour ratio, gradient smoothness, noise level and
style hints (real footage / 2D animation / sketch scores - hints for the visual analyst, not a verdict).
Exit 0 ok, 1 failure.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def hexcol(bgr) -> str:
    return "#%02x%02x%02x" % (int(bgr[2]), int(bgr[1]), int(bgr[0]))


def palette(pixels, k: int):
    import cv2
    import numpy as np
    data = pixels.reshape(-1, 3).astype(np.float32)
    if len(data) < k:
        return []
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    pal = [{"hex": hexcol(c), "share": round(float(n / len(labels)), 3)} for c, n in zip(centers, counts)]
    return sorted(pal, key=lambda d: -d["share"])


def frame_stats(img):
    import cv2
    import numpy as np
    h, w = img.shape[:2]
    scale = 320 / max(w, h)
    small = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA) if scale < 1 else img
    g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(g, 100, 200)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy) / 4.0  # ~0-255 scale
    flat = float(np.mean(mag < 6.0))
    soft = float(np.mean((mag >= 6.0) & (mag < 40.0)))
    hard = float(np.mean(mag >= 40.0))
    med = cv2.medianBlur(g, 3)
    noise = float(np.mean(np.abs(g.astype(np.float32) - med.astype(np.float32))))
    b, gch, r = [small[..., i].astype(np.float32) for i in range(3)]
    rg = r - gch
    yb = 0.5 * (r + gch) - b
    colourful = float(math.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * math.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    q = (small // 16).astype(np.int32)
    keys = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    counts = np.bincount(keys.ravel(), minlength=4096).astype(np.float64)
    p = counts[counts > 0] / counts.sum()
    entropy = float(-(p * np.log2(p)).sum())
    tiny = cv2.resize(small, (96, max(1, int(96 * small.shape[0] / small.shape[1]))), interpolation=cv2.INTER_AREA)
    return {
        "palette": palette(tiny, 5),
        "brightness": round(float(hsv[..., 2].mean()) / 255.0, 3),
        "contrast": round(float(g.std()) / 255.0, 3),
        "saturation": round(float(hsv[..., 1].mean()) / 255.0, 3),
        "edge_density": round(float(np.count_nonzero(edges)) / edges.size, 4),
        "colourfulness": round(colourful, 1),
        "flat_ratio": round(flat, 3), "soft_gradient_ratio": round(soft, 3), "hard_edge_ratio": round(hard, 3),
        "noise": round(noise, 2), "colour_entropy_bits": round(entropy, 2),
    }, tiny


def classify(rows: list[dict], rate: float, tw: int) -> str:
    import numpy as np
    tx = float(np.mean([r["tx"] for r in rows])) * rate
    ty = float(np.mean([r["ty"] for r in rows])) * rate
    sc = (float(np.mean([r["scale"] for r in rows])) - 1.0) * rate
    mf = float(np.mean([r["mean_flow"] for r in rows])) * rate
    res = float(np.mean([r["resid"] for r in rows])) * rate
    jitter = (float(np.std([r["tx"] for r in rows])) + float(np.std([r["ty"] for r in rows]))) * rate
    if mf < 3.0:
        return "static"
    if abs(sc) > 0.04 and abs(sc) * tw / 2 > 0.8 * max(abs(tx), abs(ty)):
        return "zoom-in" if sc > 0 else "zoom-out"
    if jitter > 15.0 and max(abs(tx), abs(ty)) < 10.0:
        return "handheld-shaky"
    if abs(tx) >= abs(ty) and abs(tx) > 5.0:
        return "pan-right" if tx < 0 else "pan-left"
    if abs(ty) > 5.0:
        return "tilt-down" if ty < 0 else "tilt-up"
    if res > 10.0:
        return "subject-motion"
    return "handheld-shaky" if jitter > 8.0 else "static"


def motion_pass(src: Path, shots: list[dict], fps: float, rate: float, tw: int, log) -> dict:
    """One sequential decode; Farneback flow between frames `step` apart; pairs assigned to the shot of their second frame."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError("OpenCV cannot open the video")
    step = max(1, int(round(fps / rate)))
    eff_rate = fps / step
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    th = max(16, int(H * tw / max(W, 1)))
    gx, gy = np.meshgrid(np.arange(8, tw - 8, 16), np.arange(8, th - 8, 16))
    pts = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float32)
    starts = [s["start"] for s in shots]

    def shot_idx(t):
        i = 0
        for k, st in enumerate(starts):
            if t >= st - 1e-6:
                i = k
        return i

    prev, prev_t, prev_shot = None, None, None
    rows = []
    idx = 0
    t0 = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            t = idx / fps
            si = shot_idx(t)
            small = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
            g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            if prev is not None and si == prev_shot:
                flow = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                fl = flow[pts[:, 1].astype(int), pts[:, 0].astype(int)]
                mag = np.linalg.norm(fl, axis=1)
                M, inl = cv2.estimateAffinePartial2D(pts, pts + fl, method=cv2.RANSAC, ransacReprojThreshold=1.0)
                if M is None:
                    M = np.array([[1, 0, 0], [0, 1, 0]], float)
                    inl = np.zeros((len(pts), 1))
                s = float(np.hypot(M[0, 0], M[1, 0]))
                rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
                c = np.array([tw / 2, th / 2])
                c2 = M[:, :2] @ c + M[:, 2]
                pred = (M[:, :2] @ pts.T).T + M[:, 2] - pts
                resid = float(np.mean(np.linalg.norm(fl - pred, axis=1)))
                (dx, dy), resp = cv2.phaseCorrelate(prev.astype(np.float32), g.astype(np.float32))
                rows.append({"t": round(t, 3), "shot": shots[si]["id"], "mean_flow": round(float(mag.mean()), 3),
                             "tx": round(float(c2[0] - c[0]), 3), "ty": round(float(c2[1] - c[1]), 3),
                             "scale": round(s, 4), "rot_deg": round(rot, 3), "resid": round(resid, 3),
                             "pc_dx": round(float(dx), 3), "pc_dy": round(float(dy), 3), "pc_resp": round(float(resp), 3),
                             "inlier_frac": round(float(np.mean(inl)), 3),
                             "frame_diff": round(float(np.mean(cv2.absdiff(prev, g))), 2)})
            prev, prev_t, prev_shot = g, t, si
        idx += 1
    cap.release()
    log.info(f"optical flow: {len(rows)} pairs at {eff_rate:.2f} pairs/s ({tw}px wide) in {time.time() - t0:.1f}s")
    return {"rows": rows, "rate": eff_rate, "tw": tw, "step": step}


def shot_motion(shot: dict, rows: list[dict], rate: float, tw: int) -> dict:
    import numpy as np
    mine = [r for r in rows if r["shot"] == shot["id"]]
    if not mine:
        return {"label": "unknown", "note": "shot shorter than the flow interval or no pairs", "n_pairs": 0}
    per_sec = {}
    for r in mine:
        per_sec.setdefault(int(r["t"]), []).append(r)
    sec_labels = [{"sec": s, "label": classify(w, rate, tw),
                   "mean_flow_px_s": round(float(np.mean([r["mean_flow"] for r in w])) * rate, 1)} for s, w in sorted(per_sec.items())]
    votes = Counter(l["label"] for l in sec_labels)
    label = classify(mine, rate, tw) if len(mine) < 2 * rate else votes.most_common(1)[0][0]
    tx = float(np.mean([r["tx"] for r in mine])) * rate
    ty = float(np.mean([r["ty"] for r in mine])) * rate
    return {
        "label": label, "n_pairs": len(mine),
        "magnitude_px_s": round(float(np.mean([r["mean_flow"] for r in mine])) * rate, 1),
        "translation_px_s": [round(tx, 1), round(ty, 1)],
        "scale_per_s": round((float(np.mean([r["scale"] for r in mine])) - 1.0) * rate, 4),
        "rotation_deg_per_s": round(float(np.mean([r["rot_deg"] for r in mine])) * rate, 2),
        "residual_px_s": round(float(np.mean([r["resid"] for r in mine])) * rate, 1),
        "jitter_px_s": round((float(np.std([r["tx"] for r in mine])) + float(np.std([r["ty"] for r in mine]))) * rate, 1),
        "inlier_frac": round(float(np.mean([r["inlier_frac"] for r in mine])), 3),
        "per_second": sec_labels, "label_votes": dict(votes),
    }


def style_hints(g: dict) -> dict:
    def ramp(x, lo, hi):
        if x is None:
            return 0.5
        return max(0.0, min(1.0, (x - lo) / (hi - lo))) if hi > lo else max(0.0, min(1.0, (lo - x) / (lo - hi)))
    real = (ramp(g["noise_mean"], 0.5, 1.6) + ramp(g["flat_colour_ratio"], 0.78, 0.45) + ramp(g["colour_entropy_bits_mean"], 7.5, 10.0)) / 3
    anim2d = (ramp(g["flat_colour_ratio"], 0.55, 0.85) + ramp(g["noise_mean"], 1.2, 0.3) + ramp(g["colour_entropy_bits_mean"], 10.0, 6.5)
              + ramp(g["hard_edge_ratio_mean"], 0.02, 0.08)) / 4
    sketch = (ramp(g["saturation_mean"], 0.25, 0.05) + ramp(g["brightness_mean"], 0.55, 0.85) + ramp(g["edge_density"]["mean"], 0.04, 0.15)) / 3
    return {
        "real_footage": round(real, 2), "animation_2d_flat": round(anim2d, 2), "sketch_or_line_art": round(sketch, 2),
        "animation_3d": None,
        "note": "hints only: 3D/CGI and stylised live action share the cues of real footage; the visual analyst decides from the "
                "contact sheets (references\\style-taxonomy.md). Cues: noise (sensor grain) high + few flat areas + high colour "
                "entropy -> real footage; many flat areas + clean hard edges + low noise + low entropy -> 2D animation; "
                "low saturation + bright + edge-heavy -> sketch/line art.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="visual stats + camera motion + style cues")
    common.add_std_args(ap)
    ap.add_argument("--motion-rate", type=float, default=8.0, help="flow pairs per second (default 8)")
    ap.add_argument("--motion-width", type=int, default=320, help="analysis width in px for optical flow (default 320)")
    ap.add_argument("--no-motion", action="store_true", help="skip the optical-flow pass")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "visual_stats", a.quiet)
    mdir = common.measure_dir(run_dir)
    try:
        import cv2
        import numpy as np
        src = common.source_mp4(run_dir)
        kf = common.read_json(mdir / "keyframes.json")
        if not kf:
            raise RuntimeError("keyframes.json missing - run keyframes.py first")
        probe = common.read_json(mdir / "probe.json") or {}
        fps = float((probe.get("fps") or {}).get("value") or kf.get("fps") or 30.0)
        duration = float(probe.get("duration_s") or kf.get("duration_s") or 0.0)
        shots = (common.read_json(mdir / "shots.json") or {}).get("shots") or [{"id": 1, "start": 0.0, "end": duration, "duration": duration}]

        # ------------------------------------------------------------ per-frame stats
        t1 = time.time()
        frames_out, tinies = [], []
        for s in kf.get("sampled", []):
            img = cv2.imread(str(run_dir / s["file"]))
            if img is None:
                continue
            st, tiny = frame_stats(img)
            tinies.append(tiny.reshape(-1, 3))
            frames_out.append({"t": s["t"], "shot": s["shot"], "frame": s["file"], **st})
        log.info(f"frame stats on {len(frames_out)} sampled frames in {time.time() - t1:.1f}s")
        if not frames_out:
            raise RuntimeError("no sampled frames found (keyframes.json sampled list empty)")

        # ------------------------------------------------------------ camera motion
        motion = None
        if not a.no_motion:
            motion = motion_pass(src, shots, fps, a.motion_rate, a.motion_width, log)
        shots_out = []
        for sh in shots:
            mine = [f for f in frames_out if f["shot"] == sh["id"]]
            entry = {"id": sh["id"], "start": sh["start"], "end": sh["end"], "duration": sh.get("duration", round(sh["end"] - sh["start"], 3)),
                     "n_sampled_frames": len(mine)}
            if mine:
                for key in ("brightness", "contrast", "saturation", "edge_density", "colourfulness", "flat_ratio", "noise"):
                    entry[key + "_mean"] = round(float(np.mean([f[key] for f in mine])), 4)
                shot_pix = np.concatenate([tinies[frames_out.index(f)] for f in mine])
                entry["palette"] = palette(shot_pix, 5)
            if motion:
                entry["camera_motion"] = shot_motion(sh, motion["rows"], motion["rate"], motion["tw"])
            shots_out.append(entry)

        # ------------------------------------------------------------ global aggregates
        ed = np.array([f["edge_density"] for f in frames_out])
        allpix = np.concatenate(tinies)
        pal8 = palette(allpix, 8)
        g = {
            "n_frames": len(frames_out),
            "palette_k5": palette(allpix, 5), "palette_k8": pal8,
            "palette_size_over_3pct": sum(1 for p in pal8 if p["share"] >= 0.03),
            "edge_density": {"mean": round(float(ed.mean()), 4), "p10": round(float(np.percentile(ed, 10)), 4),
                             "p50": round(float(np.percentile(ed, 50)), 4), "p90": round(float(np.percentile(ed, 90)), 4)},
            "flat_colour_ratio": round(float(np.mean([f["flat_ratio"] for f in frames_out])), 3),
            "gradient_smoothness": round(float(np.mean([f["soft_gradient_ratio"] for f in frames_out])), 3),
            "hard_edge_ratio_mean": round(float(np.mean([f["hard_edge_ratio"] for f in frames_out])), 3),
            "noise_mean": round(float(np.mean([f["noise"] for f in frames_out])), 2),
            "colour_entropy_bits_mean": round(float(np.mean([f["colour_entropy_bits"] for f in frames_out])), 2),
            "brightness_mean": round(float(np.mean([f["brightness"] for f in frames_out])), 3),
            "brightness_range": [round(float(min(f["brightness"] for f in frames_out)), 3), round(float(max(f["brightness"] for f in frames_out)), 3)],
            "contrast_mean": round(float(np.mean([f["contrast"] for f in frames_out])), 3),
            "saturation_mean": round(float(np.mean([f["saturation"] for f in frames_out])), 3),
            "colourfulness_mean": round(float(np.mean([f["colourfulness"] for f in frames_out])), 1),
        }
        g["style_hints"] = style_hints(g)
        if motion:
            labels = [s["camera_motion"]["label"] for s in shots_out if "camera_motion" in s]
            weighted = Counter()
            for s in shots_out:
                if "camera_motion" in s:
                    weighted[s["camera_motion"]["label"]] += float(s["duration"])
            tot = sum(weighted.values()) or 1.0
            g["camera_motion_summary"] = {
                "by_shot_count": dict(Counter(labels)),
                "by_screen_time_s": {k: round(v, 2) for k, v in weighted.items()},
                "dominant": weighted.most_common(1)[0][0] if weighted else None,
                "handheld_fraction": round((weighted.get("handheld-shaky", 0.0)) / tot, 2),
                "static_fraction": round((weighted.get("static", 0.0)) / tot, 2),
                "mean_magnitude_px_s": round(float(np.mean([r["mean_flow"] for r in motion["rows"]])) * motion["rate"], 1) if motion["rows"] else None,
            }

        out = {
            "source": common.rel(run_dir, src), "duration_s": round(duration, 3), "fps": fps,
            "method": {
                "frames": "OpenCV on the sampled keyframes downscaled to 320 px: k-means palette (k=5 on a 96 px thumbnail), HSV brightness/saturation, "
                          "grey std contrast, Canny 100/200 edge density, Hasler-Suesstrunk colourfulness, Sobel flat/soft/hard gradient ratios, "
                          "median-residual noise, 4-bit RGB colour entropy",
                "motion": None if not motion else f"Farneback flow at {motion['rate']:.2f} pairs/s on {motion['tw']} px frames, "
                          "estimateAffinePartial2D RANSAC (translation/scale/rotation + residual), phaseCorrelate cross-check; labels are camera "
                          "direction; thresholds heuristic (static < 3 px/s; pan/tilt > 5 px/s; zoom |scale| > 0.04/s; shaky jitter > 15 px/s)",
            },
            "frames": frames_out, "shots": shots_out, "global": g,
            "motion_pairs": motion["rows"] if motion else [],
            "timing_s": round(time.time() - t0, 2),
        }
        common.write_json(mdir / "visual-stats.json", out)
        common.state_add_file(run_dir, "10-measure", mdir / "visual-stats.json")
        cm = g.get("camera_motion_summary", {})
        log.info(f"global: palette {[p['hex'] for p in g['palette_k5']]}, edge density {g['edge_density']['mean']}, "
                 f"flat {g['flat_colour_ratio']}, noise {g['noise_mean']}, hints {g['style_hints']['real_footage']}/{g['style_hints']['animation_2d_flat']}/{g['style_hints']['sketch_or_line_art']} (real/2d/sketch); "
                 f"camera dominant {cm.get('dominant')}; done in {out['timing_s']}s")
        return 0
    except Exception as e:
        import traceback
        log.error(f"visual_stats failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
