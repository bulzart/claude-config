"""SAM Audio (Meta, facebook/sam-audio-base) separation for create-clips: long videos only, the music step's alternative to Hybrid Demucs where
measurements show it is better. Runs in its own environment (config music.sam_python, made 2026-11-21 at C:\\Users\\Bulzart\\Documents\\AI\\sam-audio\\.venv:
torch 2.7.1+cu128, the official sam_audio package, dacvae, perception_models, xformers 0.0.31.post1), never in the toolkit's Python:
    python sam_separate.py JOB.json REPORT.json
job = {"device": "cuda", "model": "facebook/sam-audio-base", "dtype": "float32" | "bfloat16", "shims": "<folder holding the torchcodec stand-in>",
       "ode_step": 0.0625 (the official default, 2/32: 16 midpoint steps), "keep_loaded_s": 0,
       "spans": [{"id", "wav_in", "description": "music playing", "keep": "residual" | "target", "anchors": [["+", s, e], ...] or null,
                  "out": {"target": wav, "residual": wav, "clean_mono": wav, "clean_mask": wav}, "chunk_s": 30.0, "sig": "..."}]}
Per span: SAM gets the span in mono at 48 kHz (its processor's own rule) with the text prompt (and time anchors when the span has real ones); it returns
`target` (the prompted sound) and `residual` (everything else). `keep` says which one is wanted: "residual" when the prompt names the music to take out,
"target" when it names the voice to keep. Two results are written: `clean_mono` (SAM's own output, at the input's rate, the same on both channels) and
`clean_mask` (the original stereo audio with SAM's keep / drop ratio applied per channel and frequency: the original's phase and stereo picture stay, the
generated audio is never heard directly). Long spans go in chunk_s windows with a 2 s overlap.
Loading (measured 2026-11-21, see the report): the model is built directly on the GPU and the 7.7 GB checkpoint is memory-mapped (the official loader
would hold it in RAM twice); the optional rerankers and the span predictor are switched off through the official config overrides (nothing of theirs is
downloaded); the vision encoder (unused without video prompts) goes back to the CPU; the T5 text encoder comes from Hugging Face (t5-base) once.
A finished span writes REPORT-like `<clean_mask>.json` beside it, so an interrupted batch resumes where it stopped (same sig: not separated again)."""
import collections
import io
import json
import os
import pickle
import re
import sys
import time


def stream_load(model, ckpt: str, torch) -> dict:
    """The checkpoint into the model's parameters (already on the GPU) ONE storage at a time, straight from its zip records: never the whole 7.7 GB in
    memory. Measured 2026-11-21 on this PC: GPU memory counts as committed memory on Windows (8 GB of weights = 8.8 GB commit), and the official
    torch.load (or a memory-mapped one) adds the whole file on top (17.6 GB, more than this PC has free). The index (data.pkl) is read with a
    restricted unpickler (tensors, storages, OrderedDict only), and the keys are checked as strictly as Meta's own loader (only the parts it loads
    from Hugging Face itself, or that are switched off, may be missing)."""
    reader = torch._C.PyTorchFileReader(ckpt)
    names = reader.get_all_records()
    prefix = next((n[:-len("data.pkl")] for n in names if n.endswith("data.pkl")), "")

    def rebuild(storage, offset, size, stride, *rest):
        return ("tensor", storage, int(offset), tuple(size), tuple(stride))

    class Index(pickle.Unpickler):
        def find_class(self, mod, name):
            if mod == "torch._utils" and name in ("_rebuild_tensor_v2", "_rebuild_tensor"):
                return rebuild
            if mod == "collections" and name == "OrderedDict":
                return collections.OrderedDict
            if mod == "torch" and name.endswith("Storage"):
                return getattr(torch, name)
            if mod == "torch" and isinstance(getattr(torch, name, None), torch.dtype):
                return getattr(torch, name)
            raise pickle.UnpicklingError(f"not allowed in a weights file: {mod}.{name}")

        def persistent_load(self, pid):
            _typename, stype, key, _location, numel = pid
            dtype = stype if isinstance(stype, torch.dtype) else stype.dtype
            return (str(key), dtype, int(numel))

    index = Index(io.BytesIO(reader.get_record(prefix + "data.pkl"))).load()
    params = model.state_dict(keep_vars=True)          # what a checkpoint holds: parameters and SAVED buffers (computed ones are made at init)
    skip = re.compile("(^text_encoder|^visual_ranker|^text_ranker|^span_predictor)")
    missing = [k for k in params if k not in index and not skip.search(k)]
    unexpected = [k for k in index if k not in params]
    if missing or unexpected:
        raise RuntimeError(f"checkpoint keys do not match the model: missing {missing[:5]}, unexpected {unexpected[:5]}")
    by_storage = collections.defaultdict(list)
    for k, (_tag, (skey, dtype, numel), off, size, stride) in index.items():
        by_storage[(skey, dtype, numel)].append((k, off, size, stride))
    n_bytes = 0
    with torch.no_grad():
        for (skey, dtype, numel), uses in by_storage.items():
            nbytes = numel * torch.empty((), dtype=dtype).element_size()
            # exactly as torch.serialization's own load_tensor: the record as an untyped storage of nbytes, viewed with the storage's dtype
            us = reader.get_storage_from_record(prefix + "data/" + skey, nbytes, torch.UntypedStorage)._typed_storage()._untyped_storage
            st = torch.empty(0, dtype=dtype).set_(us, 0, (numel,), (1,))
            for k, off, size, stride in uses:
                params[k].copy_(st.as_strided(size, stride, off))
            n_bytes += nbytes
            del st, us
    return {"tensors": len(index), "storages": len(by_storage), "gb": round(n_bytes / 2 ** 30, 2), "how": "streamed, one storage at a time"}


def main():
    job_p, rep_p = sys.argv[1], sys.argv[2]
    job = json.load(open(job_p, encoding="utf-8"))
    if job.get("alloc_conf"):
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", str(job["alloc_conf"]))     # before torch is imported
    shims = job.get("shims")
    try:
        import truststore
        truststore.inject_into_ssl()                       # this PC's HTTPS scanning (the T5 download)
    except Exception:  # noqa: BLE001
        pass
    # transformers decides once, at its first import, whether torchcodec is installed: it must see the real answer (no) BEFORE the stand-in is on
    # the path, or it asks the stand-in for its version and fails (measured 2026-11-21: "Could not import module 'T5EncoderModel'")
    import transformers  # noqa: F401
    from transformers import AutoTokenizer, T5EncoderModel  # noqa: F401
    try:
        import torchcodec  # noqa: F401
    except Exception:  # noqa: BLE001
        if shims and shims not in sys.path:
            sys.path.insert(0, shims)
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio

    device = job.get("device") or "cuda"
    model_id = job.get("model") or "facebook/sam-audio-base"
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}.get(str(job.get("dtype") or "float32"), torch.float32)
    t0 = time.time()
    rep = {"ok": False, "model": model_id, "device": device, "dtype": str(dtype).replace("torch.", ""), "torch": torch.__version__, "results": []}
    try:
        from huggingface_hub import snapshot_download
        from sam_audio import SAMAudio, SAMAudioProcessor
        mdir = model_id if os.path.isdir(model_id) else snapshot_download(model_id, allow_patterns=["config.json", "checkpoint.pt"])
        cfg = json.load(open(os.path.join(mdir, "config.json"), encoding="utf-8"))
        cfg.update({"visual_ranker": None, "text_ranker": None, "span_predictor": None})   # the official overrides: no rerankers, no span predictor
        with torch.device(device):
            model = SAMAudio(SAMAudio.config_cls(**cfg))
        rep["loader"] = stream_load(model, os.path.join(mdir, "checkpoint.pt"), torch)
        model = model.eval()
        # no video prompts here: the vision encoder (PE-Core-L14-336, a whole CLIP model) is never run; only its width is read
        # (model.vision_encoder.dim, for the zero visual features of an audio-only prompt). Its weights are dropped after the strict load:
        # moving them to the CPU instead copied 2.4 GB while the GPU copy still counted (measured 2026-11-21: 13 GB commit, over the cap)
        rep["vision_encoder_dropped_params_m"] = round(sum(p.numel() for p in model.vision_encoder.parameters()) / 1e6, 1)
        model.vision_encoder.model = torch.nn.Identity()
        if dtype != torch.float32:
            model.transformer.to(dtype)
        if device == "cuda":
            torch.cuda.empty_cache()
        processor = SAMAudioProcessor.from_pretrained(model_id)
        sr_m = int(processor.audio_sampling_rate)
        rep["load_s"] = round(time.time() - t0, 1)
        rep["vram_after_load_mb"] = round(torch.cuda.memory_allocated() / 2 ** 20) if device == "cuda" else None
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        ode = {"method": "midpoint", "options": {"step_size": float(job.get("ode_step") or 2 / 32)}}
    except Exception as e:  # noqa: BLE001
        rep["error"] = f"load: {type(e).__name__}: {str(e)[:600]}"
        json.dump(rep, open(rep_p, "w", encoding="utf-8"), indent=1)
        print(json.dumps(rep))
        return

    def run_sam(mono48, desc, anchors):
        batch = processor(audios=[mono48[None]], descriptions=[desc], anchors=[anchors] if anchors else None).to(device)
        with torch.inference_mode():
            if dtype != torch.float32:
                with torch.autocast(device_type="cuda", dtype=dtype):
                    res = model.separate(batch, ode_opt=ode, predict_spans=False, reranking_candidates=1)
            else:
                res = model.separate(batch, ode_opt=ode, predict_spans=False, reranking_candidates=1)
        n = mono48.shape[-1]
        return res.target[0].float().reshape(-1)[:n].cpu(), res.residual[0].float().reshape(-1)[:n].cpu()

    def windows(n, sr, chunk_s, ov_s=2.0):
        w, ov = int(chunk_s * sr), int(ov_s * sr)
        if n <= w:
            return [(0, n)]
        out, s = [], 0
        while True:
            e = min(n, s + w)
            out.append((s, e))
            if e >= n:
                return out
            s = e - ov

    def stft(x):
        return torch.stft(x, 2048, 512, window=torch.hann_window(2048), return_complex=True)

    for sp in job.get("spans") or []:
        side = (sp.get("out") or {}).get("clean_mask")
        side = side + ".json" if side else None
        try:
            if side and os.path.isfile(side):
                prev = json.load(open(side, encoding="utf-8"))
                if prev.get("sig") == sp.get("sig") and prev.get("ok"):
                    rep["results"].append({**prev, "reused": True})
                    continue
            t1 = time.time()
            wav, sr_in = torchaudio.load(sp["wav_in"])                     # (channels, n) at the input's rate
            n_in = wav.shape[-1]
            mono48 = torchaudio.functional.resample(wav.mean(0), sr_in, sr_m)
            n48 = mono48.shape[-1]
            tg, rs = torch.zeros(n48), torch.zeros(n48)
            wts = torch.zeros(n48)
            for a, b in windows(n48, sr_m, float(sp.get("chunk_s") or 30.0)):
                anc = None
                if sp.get("anchors"):
                    anc = [[tok, max(0.0, s - a / sr_m), min((b - a) / sr_m, e - a / sr_m)] for tok, s, e in sp["anchors"]
                           if e > a / sr_m and s < b / sr_m] or None
                t_, r_ = run_sam(mono48[a:b], sp.get("description") or "music playing", anc)
                ramp = torch.ones(b - a)
                ov = int(2.0 * sr_m)
                if a > 0:
                    ramp[:ov] = torch.linspace(0, 1, ov)
                if b < n48:
                    ramp[-ov:] = torch.minimum(ramp[-ov:], torch.linspace(1, 0, ov))
                tg[a:b] += t_[:b - a] * ramp
                rs[a:b] += r_[:b - a] * ramp
                wts[a:b] += ramp
            tg, rs = tg / wts.clamp_min(1e-6), rs / wts.clamp_min(1e-6)
            keep, drop = (rs, tg) if (sp.get("keep") or "residual") == "residual" else (tg, rs)
            out = sp.get("out") or {}
            if out.get("target"):
                sf.write(out["target"], tg.numpy(), sr_m)
            if out.get("residual"):
                sf.write(out["residual"], rs.numpy(), sr_m)
            k_in = torchaudio.functional.resample(keep, sr_m, sr_in)[:n_in]
            d_in = torchaudio.functional.resample(drop, sr_m, sr_in)[:n_in]
            if k_in.shape[-1] < n_in:
                k_in = torch.nn.functional.pad(k_in, (0, n_in - k_in.shape[-1]))
                d_in = torch.nn.functional.pad(d_in, (0, n_in - d_in.shape[-1]))
            if out.get("clean_mono"):
                sf.write(out["clean_mono"], k_in[None].repeat(wav.shape[0], 1).T.numpy(), sr_in)
            if out.get("clean_mask"):
                K, D = stft(k_in).abs() ** 2, stft(d_in).abs() ** 2
                M = K / (K + D + 1e-10)
                chans = [torch.istft(stft(wav[c]) * M, 2048, 512, window=torch.hann_window(2048), length=n_in) for c in range(wav.shape[0])]
                y = torch.stack(chans)
                pk = float(y.abs().max())
                if pk > 0.99:
                    y = y * (0.99 / pk)
                sf.write(out["clean_mask"], y.T.numpy(), sr_in)
            res = {"id": sp.get("id"), "sig": sp.get("sig"), "ok": True, "seconds": round(time.time() - t1, 2), "audio_s": round(n_in / sr_in, 2),
                   "description": sp.get("description"), "keep": sp.get("keep") or "residual", "anchors": sp.get("anchors"),
                   "peak_vram_mb": round(torch.cuda.max_memory_allocated() / 2 ** 20) if device == "cuda" else None}
            if side:
                json.dump(res, open(side, "w", encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            res = {"id": sp.get("id"), "sig": sp.get("sig"), "ok": False, "error": f"{type(e).__name__}: {str(e)[:400]}"}
            if device == "cuda":
                torch.cuda.empty_cache()
        rep["results"].append(res)
    rep["ok"] = True
    rep["wall_s"] = round(time.time() - t0, 1)
    rep["peak_vram_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20) if device == "cuda" else None
    rep["peak_reserved_mb"] = round(torch.cuda.max_memory_reserved() / 2 ** 20) if device == "cuda" else None
    json.dump(rep, open(rep_p, "w", encoding="utf-8"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
