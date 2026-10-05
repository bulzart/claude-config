"""ocr.py - Stage 1: on-screen text with RapidOCR over the sampled keyframes + shot first/last frames -> 10-measure\\ocr.json

Usage: python ocr.py --run-dir <run> [--min-score 0.5] [--similarity 0.8] [--workers 3] [--threads 4] [--quiet]

Speed: RapidOCR's detector is configured with det_limit_side_len=960 / limit_type=max (the default resizes the SHORT side
to 736, so a 720x1280 frame costs ~1 s regardless of input size) and intra_op_num_threads=--threads; frames are OCR'd in
--workers parallel processes (each loads its own engine, ~1 s). Shot first/last frames that coincide with a sampled
frame (within 0.05 s) are skipped.

ocr.json:
  detections: [{t, text, box:[[x,y]x4], score, frame, shot, position, size_class}]      (score < --min-score dropped)
  spans:      identical / near-identical text merged over consecutive frames
              [{id, text, start, end, duration, n_frames, position (top|middle|bottom-left|centre|right), size_class,
                score_max, box_mean, shots, persists_across_cuts, kind_hint (overlay|physical?)}]
  brand_candidates: all-caps short tokens, (R)/TM marks, brand keywords; handles (@...), hashtags (#...), urls
Positions are thirds of the frame; size_class from box height / frame height: small < 3 %, medium 3-7 %, large > 7 %.
Exit 0 ok (also when no text), 1 failure.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

STOP_CAPS = {"POV", "OMG", "LOL", "DIY", "WTF", "TBH", "ASAP", "FYI", "AND", "THE", "FOR", "YOU", "NOT", "BUT", "ALL", "NEW",
             "NOW", "HOW", "WHY", "WHAT", "WHEN", "THIS", "THAT", "WITH", "FROM", "YOUR", "HAVE", "JUST", "LIKE", "MORE",
             "BEST", "FREE", "SALE", "ONLY", "TODAY", "OFF", "GET", "ONE", "TWO", "DAY", "PART", "MY", "ME", "WE", "US",
             "IT", "IS", "IN", "ON", "TO", "OF", "OR", "AT", "BY", "SO", "NO", "OK", "AI", "TV", "USA", "UK", "EU", "PM", "AM",
             "IF", "AN", "AS", "BE", "DO", "GO", "UP", "VS", "ARE", "WAS", "CAN", "HAS", "HAD", "DID", "SEE", "TIP", "TIPS"}
BRAND_WORDS = {"official", "brand", "inc", "inc.", "llc", "ltd", "co.", "corp", "shop", "store", "sponsored", "paid partnership",
               "ad", "promo", "code", "discount", "link in bio", "available at", "order now", "buy now", "made in"}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def pos_class(box, w: int, h: int) -> str:
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    cx, cy = sum(xs) / 4 / max(w, 1), sum(ys) / 4 / max(h, 1)
    v = "top" if cy < 1 / 3 else ("middle" if cy < 2 / 3 else "bottom")
    hz = "left" if cx < 1 / 3 else ("centre" if cx < 2 / 3 else "right")
    return f"{v}-{hz}"


def size_class(box, h: int) -> str:
    ys = [p[1] for p in box]
    bh = (max(ys) - min(ys)) / max(h, 1)
    return "small" if bh < 0.03 else ("medium" if bh <= 0.07 else "large")


def box_centre(box):
    return sum(p[0] for p in box) / 4, sum(p[1] for p in box) / 4


_OCR = None


def _init_worker(threads: int) -> None:
    global _OCR
    from rapidocr_onnxruntime import RapidOCR
    _OCR = RapidOCR(det_limit_side_len=960, det_limit_type="max", intra_op_num_threads=threads)


def _ocr_frame(job):
    """job = (path, t, shot, kind, min_score, threads) -> (job, w, h, items | None)"""
    import cv2
    global _OCR
    path, t, shot, kind, min_score, threads = job
    if _OCR is None:
        _init_worker(threads)
    img = cv2.imread(path)
    if img is None:
        return job, None, None, None
    h, w = img.shape[:2]
    result, _elapse = _OCR(img)
    items = []
    for box, text, score in (result or []):
        score = float(score)
        if score < min_score or not str(text).strip():
            continue
        box = [[int(round(p[0])), int(round(p[1]))] for p in box]
        items.append({"t": t, "text": str(text).strip(), "box": box, "score": round(score, 3), "shot": shot,
                      "frame_kind": kind, "position": pos_class(box, w, h), "size_class": size_class(box, h), "frame_size": [w, h]})
    return job, w, h, items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="RapidOCR over keyframes")
    common.add_std_args(ap)
    ap.add_argument("--min-score", type=float, default=0.5)
    ap.add_argument("--similarity", type=float, default=0.8, help="SequenceMatcher ratio to merge texts into one span")
    ap.add_argument("--workers", type=int, default=3, help="parallel OCR processes (default 3; 1 = in-process)")
    ap.add_argument("--threads", type=int, default=4, help="onnxruntime intra-op threads per process (default 4)")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "ocr", a.quiet)
    mdir = common.measure_dir(run_dir)
    try:
        kf = common.read_json(mdir / "keyframes.json")
        if not kf:
            raise RuntimeError("keyframes.json missing - run keyframes.py first")
        shots = (common.read_json(mdir / "shots.json") or {}).get("shots", [])
        duration = float(kf.get("duration_s") or 0.0)
        sample_fps = float(kf.get("sample_fps") or 2.0)
        frames = [{"t": s["t"], "shot": s["shot"], "file": s["file"], "kind": "sampled"} for s in kf.get("sampled", [])]
        sampled_ts = sorted(f["t"] for f in frames)
        skipped_dup = 0
        for s in kf.get("shot_frames", []):
            if s["kind"] in ("first", "last"):
                if any(abs(s["t"] - st) <= 0.05 for st in sampled_ts):
                    skipped_dup += 1
                    continue
                frames.append({"t": s["t"], "shot": s["shot"], "file": s["file"], "kind": s["kind"]})
        frames.sort(key=lambda f: (f["t"], f["kind"] != "sampled"))
        log.info(f"OCR over {len(frames)} frames ({len(kf.get('sampled', []))} sampled + shot first/last; "
                 f"{skipped_dup} shot frames skipped as duplicates of sampled timestamps)")

        jobs = [(str(run_dir / fr["file"]), fr["t"], fr["shot"], fr["kind"], a.min_score, a.threads) for fr in frames]
        detections, per_frame = [], []
        t1 = time.time()
        workers = max(1, a.workers)
        if workers == 1 or len(jobs) < 4:
            _init_worker(a.threads)
            log.info(f"RapidOCR engine ready (in-process) in {time.time() - t1:.2f}s")
            results = [_ocr_frame(j) for j in jobs]
        else:
            from concurrent.futures import ProcessPoolExecutor
            log.info(f"RapidOCR in {workers} worker processes x {a.threads} threads")
            with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(a.threads,)) as ex:
                results = list(ex.map(_ocr_frame, jobs, chunksize=2))
        for fr, (job, w, h, items) in zip(frames, results):
            if items is None:
                log.warn(f"cannot read {fr['file']}")
                continue
            for d in items:
                d["frame"] = fr["file"]
                detections.append(d)
            per_frame.append({"t": fr["t"], "frame": fr["file"], "n": len(items), "text": " | ".join(i["text"] for i in items)})
        log.info(f"{len(detections)} detections (score >= {a.min_score}) on {len(frames)} frames in {time.time() - t1:.1f}s "
                 f"({(time.time() - t1) / max(1, len(frames)):.2f} s/frame)")

        # ---------------------------------------------------------------- spans
        gap_max = max(1.0, 2.5 / sample_fps)
        open_spans, spans = [], []
        by_t = {}
        for d in detections:
            by_t.setdefault(d["t"], []).append(d)
        for t in sorted(by_t):
            fw, fh = by_t[t][0]["frame_size"]
            for d in by_t[t]:
                n = norm(d["text"])
                cx, cy = box_centre(d["box"])
                best, best_r = None, 0.0
                for sp in open_spans:
                    if sp["_last_t"] == t:  # one detection per span per frame
                        continue
                    r = SequenceMatcher(None, n, sp["_norm"]).ratio() if n and sp["_norm"] else 0.0
                    dx = abs(cx - sp["_cx"]) / max(fw, 1)
                    dy = abs(cy - sp["_cy"]) / max(fh, 1)
                    if r >= a.similarity and dx < 0.2 and dy < 0.15 and r > best_r:
                        best, best_r = sp, r
                if best is not None:
                    best["end"] = t
                    best["_last_t"] = t
                    best["n_frames"] += 1
                    best["_scores"].append(d["score"])
                    best["_boxes"].append(d["box"])
                    if d["score"] > best["score_max"]:
                        best["score_max"], best["text"], best["_norm"] = d["score"], d["text"], n
                    if d["shot"] not in best["shots"]:
                        best["shots"].append(d["shot"])
                    best["_cx"], best["_cy"] = cx, cy
                else:
                    open_spans.append({"text": d["text"], "_norm": n, "start": t, "end": t, "_last_t": t, "n_frames": 1,
                                       "_scores": [d["score"]], "_boxes": [d["box"]], "score_max": d["score"],
                                       "position": d["position"], "size_class": d["size_class"], "shots": [d["shot"]],
                                       "_cx": cx, "_cy": cy, "_fw": fw, "_fh": fh})
            still = []
            for sp in open_spans:
                if t - sp["_last_t"] > gap_max:
                    spans.append(sp)
                else:
                    still.append(sp)
            open_spans = still
        spans.extend(open_spans)
        spans.sort(key=lambda s: (s["start"], s["end"]))
        out_spans = []
        for i, sp in enumerate(spans, 1):
            bx = sp["_boxes"]
            mean_box = [[int(sum(b[k][0] for b in bx) / len(bx)), int(sum(b[k][1] for b in bx) / len(bx))] for k in range(4)]
            end = min(duration or sp["end"] + 0.5 / sample_fps, sp["end"] + 0.5 / sample_fps)
            shots_here = [s for s in sp["shots"] if s is not None]
            across = len(set(shots_here)) > 1
            alnum = re.sub(r"[^A-Za-z0-9]", "", sp["text"])
            # likely OCR noise: 1-2 alphanumerics, or a one-frame hit of <= 3 characters with a weak score
            noise = len(alnum) <= 2 or (sp["n_frames"] == 1 and len(alnum) <= 3 and sp["score_max"] < 0.8)
            out_spans.append({
                "id": i, "text": sp["text"], "start": round(sp["start"], 3), "end": round(end, 3),
                "duration": round(end - sp["start"], 3), "n_frames": sp["n_frames"],
                "position": sp["position"], "size_class": sp["size_class"],
                "score_max": round(sp["score_max"], 3), "score_mean": round(sum(sp["_scores"]) / len(sp["_scores"]), 3),
                "box_mean": mean_box, "frame_size": [sp["_fw"], sp["_fh"]], "shots": sorted(set(shots_here)),
                "persists_across_cuts": across, "likely_noise": noise,
                "kind_hint": "overlay? (same place across a cut or held at the top/bottom - a physical label can do this too)"
                if (across or sp["n_frames"] >= 2 and sp["position"].startswith(("top", "bottom")))
                else "unknown (single shot: overlay or physical text - check the frame)",
            })

        # ---------------------------------------------------------------- brand / handle / hashtag candidates
        cands, handles, hashtags, urls = {}, {}, {}, {}
        for sp in out_spans:
            txt = sp["text"]
            if sp["likely_noise"]:
                continue
            for h in re.findall(r"@[A-Za-z0-9_.]{2,}", txt):
                handles.setdefault(h, []).append(sp["id"])
            for h in re.findall(r"#[A-Za-z0-9_]{2,}", txt):
                hashtags.setdefault(h, []).append(sp["id"])
            for u in re.findall(r"(?:https?://|www\.)\S+|\b[a-z0-9-]+\.(?:com|net|org|io|co|shop|store|app)\b", txt, re.I):
                urls.setdefault(u, []).append(sp["id"])
            reasons = []
            if re.search(r"[®™©]|\(R\)|\(TM\)", txt):
                reasons.append("trademark/registered mark")
            low = txt.lower()
            for kw in BRAND_WORDS:
                if re.search(rf"\b{re.escape(kw)}\b", low):
                    reasons.append(f"brand keyword '{kw}'")
            for tok in re.findall(r"\b[A-Z][A-Z0-9&'\-.]{2,14}\b", txt):
                if tok.rstrip(".") not in STOP_CAPS and len(tok.rstrip(".")) >= 3 and not tok.rstrip(".").isdigit():
                    reasons.append(f"all-caps token '{tok}'")
            if reasons:
                key = txt
                c = cands.setdefault(key, {"text": txt, "reasons": [], "spans": [], "first_t": sp["start"], "last_t": sp["end"]})
                for r in reasons:
                    if r not in c["reasons"]:
                        c["reasons"].append(r)
                c["spans"].append(sp["id"])
                c["last_t"] = max(c["last_t"], sp["end"])

        out = {
            "engine": "rapidocr_onnxruntime (CPU; det_limit_side_len=960 max, %d workers x %d threads)" % (workers, a.threads),
            "min_score": a.min_score, "similarity": a.similarity,
            "n_frames": len(frames), "n_detections": len(detections), "n_spans": len(out_spans),
            "n_spans_likely_noise": sum(1 for sp in out_spans if sp["likely_noise"]),
            "sample_fps": sample_fps, "span_gap_max_s": round(gap_max, 3),
            "frames_text": [f for f in per_frame if f["n"]],
            "detections": detections, "spans": out_spans,
            "brand_candidates": sorted(cands.values(), key=lambda c: c["first_t"]),
            "handles": [{"handle": k, "spans": v} for k, v in handles.items()],
            "hashtags": [{"hashtag": k, "spans": v} for k, v in hashtags.items()],
            "urls": [{"url": k, "spans": v} for k, v in urls.items()],
            "rules": "score < min_score dropped; spans merge texts with SequenceMatcher ratio >= similarity at a similar position over "
                     "consecutive frames (gap <= span_gap_max_s); likely_noise = 1-2 alphanumerics or a weak one-frame hit of <= 3 chars "
                     "(kept for completeness, excluded from brand candidates); never treat OCR output as verbatim without checking the "
                     "frame; overlays (captions, handles, watermarks, UI) are separated from physical text by the analyst",
            "timing_s": round(time.time() - t0, 2),
        }
        common.write_json(mdir / "ocr.json", out)
        common.state_add_file(run_dir, "10-measure", mdir / "ocr.json")
        for sp in [s for s in out_spans if not s["likely_noise"]][:12]:
            log.info(f"  span {sp['id']}: [{sp['start']:.2f}-{sp['end']:.2f}s] {sp['position']} {sp['size_class']}: \"{sp['text']}\"")
        log.info(f"{len(out_spans)} text spans ({out['n_spans_likely_noise']} likely noise), {len(out['brand_candidates'])} brand "
                 f"candidates; done in {out['timing_s']}s")
        return 0
    except Exception as e:
        import traceback
        log.error(f"ocr failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
