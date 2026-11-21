"""Local neural audio fingerprint index (create-clips, 2026-11-21): LAION's open-weight neural audio fingerprint model (laion/neural-audio-fingerprint,
Apache-2.0, 80.3 M parameters: every 1 s window of 16 kHz mono audio -> a 128-d embedding), a LOCAL index of reference recordings, and matching.
Runs in its own environment (config music.nafp.python, made 2026-11-21: C:\\Users\\Bulzart\\Documents\\AI\\audio-fp\\.venv, torch 2.7.1+cu128):
    python nafp.py JOB.json REPORT.json
job = {"device": "cuda"|"cpu", "model_dir": "<the model's Hugging Face snapshot folder: model.py + model.pt>", "index": "<index folder>",
       "ops": [{"op": "add", "id": "<recording id>", "file": wav/mp3, "start_s": 0, "end_s": null,
                "meta": {"title", "artist", "version", "isrc", "provenance", "license", ...}},
               {"op": "remove", "id": "..."}, {"op": "list"},
               {"op": "query", "qid": "...", "file": ..., "start_s": ..., "end_s": ..., "tau": 0.90}]}
The model only turns audio into embeddings: a song is NAMED only when its reference recording is in this index. A query with no reference above the
threshold is UNKNOWN. Matching is the model card's rule: query windows at a 0.5 s hop, reference windows at 0.25 s, a match is two consecutive query
windows with cosine >= tau against the same reference at a consistent offset (within 0.25 s); every candidate's longest consistent chain, its offset
and its best cosine are reported, and the decision is the scripts' facts for the music step, which scores the identity.
Index: <index>/manifest.json (recording id -> metadata, provenance, licence, the audio's hash (an already indexed audio is never fingerprinted twice),
windows, the model's SHA-256: another model makes the index stale) and <index>/emb/<id>.npy (float16 embeddings) + <id>.t.npy (window times)."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HOP_REF, HOP_Q = 0.25, 0.5


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def write_json(p: Path, obj) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    rep_p = Path(sys.argv[2])
    md = Path(job["model_dir"])
    sys.path.insert(0, str(md))
    import soundfile as sf
    import soxr
    import torch
    from model import SR, WIN, load   # the model's own code, from its snapshot

    dev = job.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    model = load(str(md / "model.pt"), dev)
    load_s = round(time.time() - t0, 2)
    model_sha = hashlib.sha256(open(md / "model.pt", "rb").read()).hexdigest()
    if dev == "cuda":
        torch.cuda.reset_peak_memory_stats()
    idx = Path(job["index"])
    (idx / "emb").mkdir(parents=True, exist_ok=True)
    man_p = idx / "manifest.json"
    man = json.load(open(man_p, encoding="utf-8")) if man_p.is_file() else {}
    if not man or man.get("model", {}).get("sha256") != model_sha:
        stale = bool(man.get("recordings"))
        man = {"schema": "cc-nafp-index/1", "model": {"repo": "laion/neural-audio-fingerprint", "sha256": model_sha, "hop_s": HOP_REF},
               "recordings": {} if stale or not man else man.get("recordings", {}), "made": now_iso(),
               "note": "local reference recordings for song identification; a song is named only when its reference is here"}
        if stale:
            for f in (idx / "emb").glob("*.npy"):
                f.unlink()
    rep = {"ok": True, "device": dev, "load_s": load_s, "model_sha256": model_sha[:16], "results": []}

    def read16(path, a=None, b=None):
        info = sf.info(path)
        start = int((a or 0) * info.samplerate)
        stop = int(b * info.samplerate) if b else None
        x, sr = sf.read(path, start=start, stop=stop, dtype="float32", always_2d=True)
        x = x.mean(1)
        return soxr.resample(x, sr, SR, quality="VHQ").astype(np.float32) if sr != SR else x

    @torch.inference_mode()
    def embed(x, hop):
        starts = np.arange(0, max(len(x) - WIN, 0) + 1, int(hop * SR))
        if len(x) - WIN - starts[-1] >= 800:
            starts = np.append(starts, len(x) - WIN)
        xp = np.pad(x, (0, max(WIN - len(x), 0)))
        w = torch.from_numpy(np.stack([xp[s:s + WIN] for s in starts]))
        dbs = 10 * torch.log10(w.square().mean(1) + 1e-20)
        keep = (dbs >= max(-90.0, float(dbs.max()) - 60.0)).numpy()
        e = torch.cat([model(w[keep][i:i + 256].to(dev)).float().cpu() for i in range(0, int(keep.sum()), 256)])
        return starts[keep] / SR, e.numpy()

    def refs():
        ids = list(man["recordings"])
        es, ts, owner = [], [], []
        for k, rid in enumerate(ids):
            e = np.load(idx / "emb" / f"{rid}.npy").astype(np.float32)
            es.append(e)
            ts.append(np.load(idx / "emb" / f"{rid}.t.npy"))
            owner.append(np.full(len(e), k))
        if not es:
            return ids, np.zeros((0, 128), np.float32), np.zeros(0), np.zeros(0, int)
        return ids, np.concatenate(es), np.concatenate(ts), np.concatenate(owner)

    for op in job.get("ops") or []:
        t1 = time.time()
        try:
            if op["op"] == "add":
                x = read16(op["file"], op.get("start_s"), op.get("end_s"))
                h = hashlib.sha1((np.round(x * 32767).astype(np.int16)).tobytes()).hexdigest()
                dup = next((k for k, v in man["recordings"].items() if v.get("audio_sha1") == h), None)
                if dup:
                    rep["results"].append({"op": "add", "id": op["id"], "ok": True, "skipped": f"this audio is already indexed as {dup}"})
                    continue
                t, e = embed(x, HOP_REF)
                np.save(idx / "emb" / f"{op['id']}.npy", e.astype(np.float16))
                np.save(idx / "emb" / f"{op['id']}.t.npy", t.astype(np.float32))
                man["recordings"][op["id"]] = {**(op.get("meta") or {}), "audio_sha1": h, "duration_s": round(len(x) / SR, 2), "windows": len(e),
                                               "source_file": str(op["file"]), "source_span_s": [op.get("start_s"), op.get("end_s")], "added": now_iso()}
                write_json(man_p, man)
                rep["results"].append({"op": "add", "id": op["id"], "ok": True, "windows": len(e), "seconds": round(time.time() - t1, 2)})
            elif op["op"] == "remove":
                v = man["recordings"].pop(op["id"], None)
                for f in (idx / "emb" / f"{op['id']}.npy", idx / "emb" / f"{op['id']}.t.npy"):
                    f.unlink(missing_ok=True)
                write_json(man_p, man)
                rep["results"].append({"op": "remove", "id": op["id"], "ok": bool(v)})
            elif op["op"] == "list":
                rep["results"].append({"op": "list", "ok": True, "recordings": {k: {kk: v.get(kk) for kk in ("title", "artist", "version", "duration_s", "provenance",
                                                                                                           "license")} for k, v in man["recordings"].items()}})
            elif op["op"] == "query":
                tau = float(op.get("tau") or 0.90)
                x = read16(op["file"], op.get("start_s"), op.get("end_s"))
                tq, eq = embed(x, HOP_Q)
                ids, er, tr, owner = refs()
                cands = []
                if len(er):
                    S = eq @ er.T                                          # (query windows, all reference windows)
                    for k, rid in enumerate(ids):
                        cols = np.where(owner == k)[0]
                        sub = S[:, cols]
                        j = sub.argmax(1)
                        best = sub[np.arange(len(tq)), j]
                        off = tr[cols][j] - tq
                        hit = best >= tau
                        run, longest, end_at = 0, 0, -1
                        for i in range(len(tq)):
                            ok_ = hit[i] and (i == 0 or not hit[i - 1] or abs(off[i] - off[i - 1]) <= 0.25 and (tq[i] - tq[i - 1]) <= HOP_Q + 1e-6)
                            run = run + 1 if hit[i] and (run == 0 or ok_) else (1 if hit[i] else 0)
                            if run > longest:
                                longest, end_at = run, i
                        need = int(op.get("min_chain") or 2)
                        match = longest >= need or (longest >= 1 and man["recordings"][rid].get("duration_s", 99) <= 1.5)
                        cands.append({"id": rid, "match": bool(match), "chain_windows": int(longest), "hits": int(hit.sum()), "windows": len(tq),
                                      "max_cos": round(float(best.max()), 3), "mean_cos_top5": round(float(np.sort(best)[-5:].mean()), 3),
                                      "offset_s": round(float(np.median(off[hit])), 2) if hit.any() else None,
                                      "title": man["recordings"][rid].get("title"), "artist": man["recordings"][rid].get("artist"),
                                      "version": man["recordings"][rid].get("version")})
                cands.sort(key=lambda c: (c["match"], c["chain_windows"], c["hits"], c["max_cos"]), reverse=True)
                top = cands[0] if cands else None
                second = cands[1] if len(cands) > 1 else None
                ambiguous = bool(top and top["match"] and second and second["match"] and second["chain_windows"] >= top["chain_windows"] - 1)
                rep["results"].append({"op": "query", "qid": op.get("qid"), "ok": True, "seconds": round(time.time() - t1, 3), "query_s": round(len(x) / SR, 2),
                                       "decision": ("UNKNOWN" if not (top and top["match"]) else "AMBIGUOUS" if ambiguous else "MATCH"),
                                       "best": top, "runner_up": second, "candidates": cands[:5], "tau": tau, "min_chain": int(op.get("min_chain") or 2)})
        except Exception as e:  # noqa: BLE001
            rep["results"].append({"op": op.get("op"), "id": op.get("id") or op.get("qid"), "ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
    rep["recordings"] = len(man["recordings"])
    rep["peak_vram_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20) if dev == "cuda" else None
    rep["wall_s"] = round(time.time() - t0, 2)
    write_json(rep_p, rep)
    print(json.dumps({k: rep[k] for k in ("ok", "device", "load_s", "recordings", "peak_vram_mb", "wall_s")}))


if __name__ == "__main__":
    main()
