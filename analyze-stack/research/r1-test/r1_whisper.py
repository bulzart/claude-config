import json, sys, time
import r1_dllshim  # process-local msvcp140.dll workaround (see file); remove once VC++ redist is installed
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
size = sys.argv[3] if len(sys.argv) > 3 else "tiny"
lang = sys.argv[4] if len(sys.argv) > 4 else None   # force e.g. "en"; None = auto-detect
t = time.time()
model = WhisperModel(size, device="cpu", compute_type="int8")
load_s = round(time.time() - t, 2)
segments, info = model.transcribe(src, language=lang, word_timestamps=True, vad_filter=True,
                                  vad_parameters={"min_silence_duration_ms": 500}, beam_size=5)
res = {"model": size, "language": info.language, "language_probability": round(info.language_probability, 3),
       "duration": info.duration, "segments": []}
for s in segments:
    res["segments"].append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                            "words": [{"w": w.word, "start": round(w.start, 3), "end": round(w.end, 3),
                                       "p": round(w.probability, 3)} for w in (s.words or [])]})
res["model_load_s"] = load_s
res["elapsed_total_s"] = round(time.time() - t, 2)
json.dump(res, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("model", size, "lang", info.language, res["language_probability"], "dur", info.duration,
      "load", load_s, "s total", res["elapsed_total_s"], "s")
for s in res["segments"]:
    print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}")
if res["segments"]:
    print("first words:", res["segments"][0]["words"][:6])
