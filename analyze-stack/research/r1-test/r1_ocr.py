import sys, json, time, cv2
import r1_dllshim  # process-local msvcp140.dll workaround (see file); remove once VC++ redist is installed
from rapidocr_onnxruntime import RapidOCR
src, out = sys.argv[1], sys.argv[2]
times = [float(x) for x in sys.argv[3].split(",")]
cap = cv2.VideoCapture(src)
t0 = time.time(); ocr = RapidOCR(); init_s = round(time.time() - t0, 2)
res = []
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, frame = cap.read()
    if not ok:
        res.append({"t": t, "error": "no frame"}); continue
    r, elapse = ocr(frame)
    items = [{"text": text, "score": round(float(score), 3),
              "box": [[int(p[0]), int(p[1])] for p in box]} for box, text, score in (r or [])]
    res.append({"t": t, "n": len(items), "items": items, "elapse": elapse})
    print(f"t={t}s n={len(items)}", [(i["text"], i["score"]) for i in items])
json.dump({"init_s": init_s, "frames": res}, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("ocr init", init_s, "s")
