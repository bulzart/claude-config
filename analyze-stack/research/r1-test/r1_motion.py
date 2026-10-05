"""Camera-motion + style-cue extractor (OpenCV). Labels are CAMERA direction (content moves opposite)."""
import sys, json, time, cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
t0 = time.time()
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W, H = int(cap.get(3)), int(cap.get(4))
step = max(1, int(round(fps / 10)))          # ~10 analysed pairs per second
tw = 320; th = int(H * tw / W)
gx, gy = np.meshgrid(np.arange(8, tw - 8, 16), np.arange(8, th - 8, 16))
pts = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float32)
prev = None; rows = []; idx = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    if idx % step == 0:
        t = idx / fps
        small = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            flow = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            fl = flow[pts[:, 1].astype(int), pts[:, 0].astype(int)]
            mag = np.linalg.norm(fl, axis=1)
            M, inl = cv2.estimateAffinePartial2D(pts, pts + fl, method=cv2.RANSAC, ransacReprojThreshold=1.0)
            if M is None:
                M = np.array([[1, 0, 0], [0, 1, 0]], float); inl = np.zeros((len(pts), 1))
            s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
            c = np.array([tw / 2, th / 2]); c2 = M[:, :2] @ c + M[:, 2]
            tx, ty = float(c2[0] - c[0]), float(c2[1] - c[1])
            pred = (M[:, :2] @ pts.T).T + M[:, 2] - pts
            resid = float(np.mean(np.linalg.norm(fl - pred, axis=1)))
            (dx, dy), resp = cv2.phaseCorrelate(prev.astype(np.float32), g.astype(np.float32))
            diff = float(np.mean(cv2.absdiff(prev, g)))
            edges = cv2.Canny(g, 100, 200); ed = float(np.count_nonzero(edges)) / edges.size
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            rows.append({"t": round(t, 3), "mean_flow": round(float(mag.mean()), 3), "tx": round(tx, 3), "ty": round(ty, 3),
                         "scale": round(s, 4), "rot_deg": round(rot, 3), "resid": round(resid, 3),
                         "pc_dx": round(float(dx), 3), "pc_dy": round(float(dy), 3), "pc_resp": round(float(resp), 3),
                         "frame_diff": round(diff, 3), "edge_density": round(ed, 4),
                         "sat_mean": round(float(hsv[..., 1].mean()), 1), "val_mean": round(float(hsv[..., 2].mean()), 1),
                         "inlier_frac": round(float(np.mean(inl)), 3)})
        prev = g
    idx += 1

def classify(w):
    tx = np.mean([r["tx"] for r in w]); ty = np.mean([r["ty"] for r in w]); sc = np.mean([r["scale"] for r in w]) - 1
    mf = np.mean([r["mean_flow"] for r in w]); res = np.mean([r["resid"] for r in w])
    jitter = np.std([r["tx"] for r in w]) + np.std([r["ty"] for r in w])
    if mf < 0.3: return "static"
    if abs(sc) > 0.004 and abs(sc) * tw / 2 > 0.8 * max(abs(tx), abs(ty)):
        return "zoom-in" if sc > 0 else "zoom-out"
    if jitter > 1.5 and max(abs(tx), abs(ty)) < 1.0: return "handheld"
    if abs(tx) >= abs(ty) and abs(tx) > 0.5: return "pan-right" if tx < 0 else "pan-left"
    if abs(ty) > 0.5: return "tilt-down" if ty < 0 else "tilt-up"
    if res > 1.0: return "subject-motion"
    return "handheld" if jitter > 0.8 else "static"

secs = {}
for r in rows: secs.setdefault(int(r["t"]), []).append(r)
summary = [{"sec": s, "label": classify(w),
            "mean_flow": round(float(np.mean([r["mean_flow"] for r in w])), 3),
            "resid": round(float(np.mean([r["resid"] for r in w])), 3),
            "frame_diff": round(float(np.mean([r["frame_diff"] for r in w])), 3),
            "edge_density": round(float(np.mean([r["edge_density"] for r in w])), 4),
            "sat": round(float(np.mean([r["sat_mean"] for r in w])), 1),
            "val": round(float(np.mean([r["val_mean"] for r in w])), 1)} for s, w in sorted(secs.items())]
# palette: k-means (k=5) over one 96px-wide frame per second
cap.set(cv2.CAP_PROP_POS_FRAMES, 0); samples = []; i = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    if i % int(round(fps)) == 0:
        samples.append(cv2.resize(frame, (96, int(96 * H / W))).reshape(-1, 3))
    i += 1
data = np.concatenate(samples).astype(np.float32)
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
_, labels, centers = cv2.kmeans(data, 5, None, crit, 3, cv2.KMEANS_PP_CENTERS)
counts = np.bincount(labels.ravel(), minlength=5)
palette = sorted([{"hex": "#%02x%02x%02x" % (int(c[2]), int(c[1]), int(c[0])), "share": round(float(k / len(labels)), 3)}
                  for c, k in zip(centers, counts)], key=lambda d: -d["share"])
res = {"fps": fps, "frames": n, "size": [W, H], "sample_step": step, "elapsed_s": round(time.time() - t0, 2),
       "per_second": summary, "palette_k5": palette, "per_sample": rows}
json.dump(res, open(out, "w"), indent=1)
print("fps", fps, "frames", n, "size", W, H, "pairs", len(rows), "elapsed", res["elapsed_s"], "s")
for s in summary: print(s)
print("palette", palette)
