#!/usr/bin/env python3
"""tts_worker.py - Qwen3-TTS for /analyze-with-loupe Static (contract item 36).

Run ONLY by awl.py (`T tts ...`) with the TTS environment's own Python (AWL_TTS_PYTHON: a venv with `pip install -U qwen-tts` and a CUDA
build of torch), one job file per call, one model load per call. It prints one JSON object on its last stdout line, like every command of
the toolkit. It makes audio and measures nothing else; the agent judges.

Jobs (the "op" of the job file):
  check  : torch, qwen-tts, CUDA, bf16 support, the GPU, and whether the models are in the Hugging Face cache
  design : VoiceDesign model; items [{n, text, instruct, out, seed}] -> one wav each (a voice described in words; the seed, when
           given, set before each item, so a strong line can reuse the picked sample's)
  voice  : Base model; ref_audio + ref_text -> the reusable clone prompt (out_prompt, torch.save of the items, as the official demo);
           emotions [{name, text, out_wav, out_prompt}] -> the same voice speaking each line, and that clip's own prompt
  say    : Base model; prompts {name: file}; lines [{n, text, emotion, out}] -> one wav per line in the run's voice

The API used (QwenLM/Qwen3-TTS, qwen_tts/inference/qwen3_tts_model.py): Qwen3TTSModel.from_pretrained(id, device_map, dtype,
attn_implementation); generate_voice_design(text, instruct, language); create_voice_clone_prompt(ref_audio, ref_text);
generate_voice_clone(text, language, voice_clone_prompt). Each returns (list of numpy waves, sample rate 24000).

The engine: when faster-qwen3-tts is installed in this environment (andimarafioti/faster-qwen3-tts: the same models and qwen_tts
calls, the two decode loops replayed as CUDA graphs, about 8x faster) and the job runs on CUDA in bf16, it makes the audio;
otherwise qwen-tts does. AWL_TTS_ENGINE=qwen-tts forces qwen-tts. Each answer names the engine: a seed reproduces its take only
on the engine that made it (the graphs are captured at load, before any seed is set, so a seed gives the same take again).
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def _dtype(name):
    import torch
    return {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}.get(str(name or "bfloat16"), torch.bfloat16)


def engine_for(dev, dt):
    """faster-qwen3-tts on CUDA in bf16 when it is installed here (unless AWL_TTS_ENGINE=qwen-tts); qwen-tts otherwise."""
    import torch
    if str(os.environ.get("AWL_TTS_ENGINE") or "").strip().lower() in ("qwen-tts", "qwen_tts", "official"):
        return "qwen-tts"
    if not str(dev).startswith("cuda") or dt != torch.bfloat16:
        return "qwen-tts"
    try:
        import faster_qwen3_tts  # noqa: F401
    except ImportError:
        return "qwen-tts"
    return "faster-qwen3-tts"


class FastModel:
    """faster-qwen3-tts behind the three calls the ops make: the same arguments and the same (waves, sample rate) answers."""

    def __init__(self, fast):
        self.fast = fast

    def generate_voice_design(self, text, instruct, language):
        return self.fast.generate_voice_design(text=text, instruct=instruct, language=language or "auto")

    def create_voice_clone_prompt(self, ref_audio, ref_text):
        return self.fast.model.create_voice_clone_prompt(ref_audio=ref_audio, ref_text=ref_text)

    def generate_voice_clone(self, text, language, voice_clone_prompt):
        return self.fast.generate_voice_clone(text=text, language=language or "auto", voice_clone_prompt=voice_clone_prompt)


def load(model_id, job):
    """The model on the job's device. bf16 where the GPU supports it (the model was trained in bf16); float32 otherwise, never float16
    (the maintainers: fp16 breaks the code predictor). CPU when no CUDA device is there (slow, but it runs)."""
    import torch
    dev = str(job.get("device") or "cuda:0")
    notes = []
    if dev.startswith("cuda") and not torch.cuda.is_available():
        notes.append("no CUDA device: running on the CPU (slow)")
        dev = "cpu"
    dt = _dtype(job.get("dtype"))
    if dt == torch.bfloat16 and dev.startswith("cuda") and not torch.cuda.is_bf16_supported():
        notes.append("this GPU has no bf16: float32 instead")
        dt = torch.float32
    if dt == torch.float16:
        notes.append("float16 asked: float32 instead (fp16 breaks this model)")
        dt = torch.float32
    engine = engine_for(dev, dt)
    t0 = time.time()
    if engine == "faster-qwen3-tts":
        from faster_qwen3_tts import FasterQwen3TTS
        fast = FasterQwen3TTS.from_pretrained(model_id, device=dev, dtype=dt, attn_implementation=job.get("attn") or "sdpa")
        fast.warmup()  # capture the CUDA graphs now, before any seed is set: a seed then gives the same take again
        model = FastModel(fast)
    else:
        from qwen_tts import Qwen3TTSModel
        kw = {"device_map": dev, "dtype": dt}
        if job.get("attn"):
            kw["attn_implementation"] = job["attn"]
        model = Qwen3TTSModel.from_pretrained(model_id, **kw)
    return model, {"device": dev, "dtype": str(dt).replace("torch.", ""), "engine": engine, "load_s": round(time.time() - t0, 1),
                   "notes": notes}


def write_wav(path, wav, sr):
    import soundfile as sf
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), wav, sr, subtype="PCM_16")
    return round(len(wav) / float(sr), 3)


def save_prompt(items, path):
    import torch
    from dataclasses import asdict
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"items": [asdict(it) for it in items]}, str(path))


def load_prompt(path):
    import torch
    from qwen_tts import VoiceClonePromptItem
    d = torch.load(str(path), map_location="cpu", weights_only=True)
    return [VoiceClonePromptItem(**it) for it in d["items"]]


def op_check(job):
    res = {"ok": False}
    try:
        import torch
        res.update({"torch": torch.__version__, "cuda": torch.cuda.is_available()})
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            res.update({"gpu": p.name, "vram_gb": round(p.total_memory / 1024 ** 3, 1), "bf16": torch.cuda.is_bf16_supported()})
    except Exception as e:  # noqa: BLE001
        res["error"] = f"torch: {type(e).__name__}: {e}"
        return res
    try:
        import qwen_tts
        res["qwen_tts"] = getattr(qwen_tts, "__version__", "installed")
    except Exception as e:  # noqa: BLE001
        res["error"] = f"qwen_tts: {type(e).__name__}: {e} (pip install -U qwen-tts in this environment)"
        return res
    try:
        import faster_qwen3_tts
        res["faster_qwen3_tts"] = getattr(faster_qwen3_tts, "__version__", "installed")
    except ImportError:
        res["faster_qwen3_tts"] = None
    dev = str(job.get("device") or "cuda:0") if torch.cuda.is_available() else "cpu"
    dt = _dtype(job.get("dtype"))
    if dt != torch.bfloat16 or (dev.startswith("cuda") and not torch.cuda.is_bf16_supported()):
        dt = torch.float32  # what load() would use
    res["engine"] = engine_for(dev, dt)
    cached = {}
    try:
        from huggingface_hub import try_to_load_from_cache
        for m in [x for x in job.get("models") or [] if x]:
            hit = try_to_load_from_cache(m, "config.json")
            cached[m] = bool(hit) and isinstance(hit, str)
    except Exception:  # noqa: BLE001
        pass
    res.update({"ok": True, "models_cached": cached,
                "note": "a model not cached is downloaded on its first use (several GB)" if not all(cached.values() or [True]) else ""})
    return res


def seed_all(seed):
    """The same seed for every random source the generation uses (python, numpy, torch, CUDA)."""
    if seed is None:
        return
    import random
    import numpy as np
    import torch
    s = int(seed)
    random.seed(s)
    np.random.seed(s % (2 ** 32))
    torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def op_design(job):
    model, info = load(job["model"], job)
    items = []
    for it in job["items"]:
        t0 = time.time()
        seed_all(it.get("seed"))
        wavs, sr = model.generate_voice_design(text=it["text"], instruct=it["instruct"], language=job.get("language"))
        it = dict(it, duration_s=write_wav(it["out"], wavs[0], sr), seconds=round(time.time() - t0, 1), sample_rate=sr)
        items.append(it)
    return {"ok": True, "items": items, **info}


def op_voice(job):
    model, info = load(job["model"], job)
    prompt = model.create_voice_clone_prompt(ref_audio=job["ref_audio"], ref_text=job["ref_text"])
    save_prompt(prompt, job["out_prompt"])
    made = []
    for e in job.get("emotions") or []:
        wavs, sr = model.generate_voice_clone(text=e["text"], language=job.get("language"), voice_clone_prompt=prompt)
        dur = write_wav(e["out_wav"], wavs[0], sr)
        p2 = model.create_voice_clone_prompt(ref_audio=e["out_wav"], ref_text=e["text"])
        save_prompt(p2, e["out_prompt"])
        made.append({"name": e["name"], "wav": e["out_wav"], "prompt": e["out_prompt"], "duration_s": dur})
    return {"ok": True, "prompt": job["out_prompt"], "emotions": made, **info}


def op_say(job):
    model, info = load(job["model"], job)
    prompts = {name: load_prompt(p) for name, p in (job.get("prompts") or {}).items() if Path(p).is_file()}
    if "neutral" not in prompts:
        return {"ok": False, "error": "the run's neutral voice prompt is missing (T tts voice)"}
    lines = []
    for ln in job["lines"]:
        t0 = time.time()
        pr = prompts.get(str(ln.get("emotion") or "neutral")) or prompts["neutral"]
        wavs, sr = model.generate_voice_clone(text=ln["text"], language=job.get("language"), voice_clone_prompt=pr)
        lines.append({"n": ln["n"], "out": ln["out"], "duration_s": write_wav(ln["out"], wavs[0], sr), "seconds": round(time.time() - t0, 1),
                      "emotion_used": ln.get("emotion") if str(ln.get("emotion") or "neutral") in prompts else "neutral", "sample_rate": sr})
    return {"ok": True, "lines": lines, **info}


def main():
    if len(sys.argv) != 2:
        out({"ok": False, "error": "usage: tts_worker.py <job.json>"}, 2)
    try:
        job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"job file: {e}"}, 2)
    ops = {"check": op_check, "design": op_design, "voice": op_voice, "say": op_say}
    if job.get("op") not in ops:
        out({"ok": False, "error": f"unknown op {job.get('op')!r}"}, 2)
    try:
        res = ops[job["op"]](job)
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}, 1)
    out(res, 0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
