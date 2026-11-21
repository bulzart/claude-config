"""Voice-preserving music removal for /create-clips. `cc.py music --apply` runs this file with a Python that has torch + torchaudio (config music.python,
else found by `cc.py music-setup`). Kept plain (never encrypted): another interpreter runs it, and it imports nothing from the toolkit.

One job file in, one result file out:
  job = {"device": "cuda"|"cpu", "spans": [{"id", "sig", "wav_in", "wav_out", "words": [[s, e], ...] (seconds in the span), "gap_gate_s" (or
         "gap_before_s" and "gap_after_s"), "gate_db", "crossfade_s"}]}
Each finished span also writes wav_out + ".json" (its numbers and sig) at once, so an interrupted batch resumes where it stopped: a span whose
sidecar carries the same sig is not separated again (`--smoke` runs a 4 s self-test instead).

Per span: torchaudio's Hybrid Demucs (HDEMUCS_HIGH_MUSDB_PLUS: drums, bass, other, vocals; weights in the torch hub cache) splits the audio once. The
drums, bass and other stems (the song's instruments and beat) are dropped. The vocals stem keeps every voice: the streamer, the game's characters, his
laugh, and also a song's singer. Where nobody speaks (no transcript word within gap_gate_s) the vocals stem is lowered by gate_db, so a sung line
between his words goes down while his lines and what follows them stay. A singer UNDER his words stays (measured on a controlled mix 2026-11-21: about
7 dB down there, 25 dB where he is silent), and so does anything voiced in the gaps that the transcript does not hold (a long laugh after his last word
is lowered with the singer): `gap_voice_db` (the voice level in the gaps against his speech) tells the toolkit to ask for a listen. The first and last
crossfade_s blend from and back to the original audio. The model loads once for all spans."""
import json
import os
import sys
import time

import torch
import torchaudio
from torchaudio.transforms import Fade


def separate(model, mix, sr, device, segment=10.0, overlap=0.1):
    batch, channels, length = mix.shape
    chunk_len = int(sr * segment * (1 + overlap))
    start, end = 0, chunk_len
    overlap_frames = int(overlap * sr)
    fade = Fade(fade_in_len=0, fade_out_len=overlap_frames, fade_shape="linear")
    final = torch.zeros(batch, len(model.sources), channels, length, device=device)
    while start < length - overlap_frames:
        chunk = mix[:, :, start:end]
        with torch.no_grad():
            out = model.forward(chunk)
        out = fade(out)
        final[:, :, :, start:start + out.shape[-1]] += out
        if start == 0:
            fade.fade_in_len = overlap_frames
            start += chunk_len - overlap_frames
        else:
            start += chunk_len
        end += chunk_len
        if end >= length:
            fade.fade_out_len = 0
    return final


def rms_db(x):
    if x.numel() == 0:
        return None
    v = float(torch.sqrt(torch.mean(x.float() ** 2)) + 1e-12)
    return round(20.0 * torch.log10(torch.tensor(v)).item(), 2)


def one_span(model, sr, srcs, device, sp):
    wav, in_sr = torchaudio.load(sp["wav_in"])
    if in_sr != sr:
        wav = torchaudio.functional.resample(wav, in_sr, sr)
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    wav = wav[:2].to(device)
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    stems = separate(model, ((wav - mean) / std)[None], sr, device)[0] * std + mean
    voc = stems[srcs.index("vocals")]
    rest = sum(stems[i] for i, s in enumerate(srcs) if s != "vocals")
    n = voc.shape[-1]
    gap = float(sp.get("gap_gate_s", 1.5))
    pre = float(sp["gap_before_s"]) if sp.get("gap_before_s") is not None else gap      # before a word: a breath at most
    post = float(sp["gap_after_s"]) if sp.get("gap_after_s") is not None else gap      # after a word: the laugh or reaction that follows a line
    speech = torch.zeros(n, dtype=torch.bool, device=device)
    for s, e in sorted(sp.get("words") or []):
        a, b = max(0, int((s - pre) * sr)), min(n, int((e + post) * sr))
        if b > a:
            speech[a:b] = True
    gate = torch.ones(n, device=device)
    gate[~speech] = 10 ** (float(sp.get("gate_db", -18.0)) / 20.0)
    k = max(1, int(0.05 * sr))                       # 50 ms ramps, never a click
    gate = torch.nn.functional.avg_pool1d(gate[None, None], kernel_size=2 * k + 1, stride=1, padding=k, count_include_pad=False)[0, 0][:n]
    clean = voc * gate
    xf = min(int(float(sp.get("crossfade_s", 0.15)) * sr), n // 4)
    if xf > 0:
        ramp = torch.linspace(0.0, 1.0, xf, device=device)
        clean[:, :xf] = wav[:, :xf] * (1 - ramp) + clean[:, :xf] * ramp
        clean[:, -xf:] = clean[:, -xf:] * (1 - ramp) + wav[:, -xf:] * ramp
    peak = float(clean.abs().max())
    if peak > 0.99:                                   # never clip
        clean = clean * (0.99 / peak)
    torchaudio.save(sp["wav_out"], clean.cpu(), sr)
    v_gap, v_sp = rms_db(voc[:, ~speech]), rms_db(voc[:, speech])
    return {"duration_s": round(n / sr, 3), "in_duration_s": round(wav.shape[-1] / sr, 3),
            "rms_db": {"mix": rms_db(wav), "vocals": rms_db(voc), "music": rms_db(rest), "clean": rms_db(clean)},
            "gated_share": round(float((~speech).float().mean()), 3), "gap_voice_db": round(v_gap - v_sp, 2) if v_gap is not None and v_sp is not None else None,
            "peak_scaled": peak > 0.99}


def load_model(device):
    bundle = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
    return bundle.get_model().to(device).eval(), bundle.sample_rate


def main():
    if sys.argv[1] == "--smoke":
        device = "cuda" if torch.cuda.is_available() else "cpu"
        t0 = time.time()
        model, sr = load_model(device)
        t = torch.arange(int(4 * sr)) / sr
        x = (0.3 * torch.sin(2 * 3.14159 * 220 * t) + 0.1 * torch.randn_like(t)).repeat(2, 1)[None].to(device)
        with torch.no_grad():
            y = model.forward(x)
        print(json.dumps({"ok": tuple(y.shape) == (1, 4, 2, x.shape[-1]), "device": device, "torch": torch.__version__, "torchaudio": torchaudio.__version__,
                          "sources": list(model.sources), "seconds": round(time.time() - t0, 1),
                          "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None}))
        return
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    device = job.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"
    model, sr, load_s = None, None, 0.0
    results = []
    for sp in job["spans"]:
        side = sp["wav_out"] + ".json"
        try:
            prev = json.load(open(side, encoding="utf-8")) if os.path.isfile(side) and os.path.isfile(sp["wav_out"]) else None
        except ValueError:
            prev = None
        if prev and prev.get("sig") == sp.get("sig") and prev.get("ok"):
            results.append({**prev, "reused": True})
            continue
        if model is None:
            t0 = time.time()
            model, sr = load_model(device)
            load_s = round(time.time() - t0, 1)
        t1 = time.time()
        try:
            res = {"id": sp["id"], "sig": sp.get("sig"), "ok": True, **one_span(model, sr, list(model.sources), device, sp), "seconds": round(time.time() - t1, 2)}
        except Exception as e:  # noqa: BLE001
            res = {"id": sp.get("id"), "sig": sp.get("sig"), "ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"}
        if res["ok"]:
            json.dump(res, open(side, "w", encoding="utf-8"))
        results.append(res)
    json.dump({"ok": True, "device": device, "model": "torchaudio HDEMUCS_HIGH_MUSDB_PLUS", "load_s": load_s, "torch": torch.__version__,
               "peak_vram_mb": round(torch.cuda.max_memory_allocated() / 2 ** 20) if device == "cuda" else None,
               "results": results}, open(sys.argv[2], "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
