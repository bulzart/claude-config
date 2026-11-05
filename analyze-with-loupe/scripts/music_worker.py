#!/usr/bin/env python3
"""music_worker.py - ACE-Step 1.5 for /analyze-with-loupe Static (contract item 36): an instrumental bed under a narration, only when a
run's plan calls for one.

Run ONLY by awl.py (`T music ...`) with ACE-Step 1.5's own Python (AWL_MUSIC_PYTHON, the .venv of a clone of
https://github.com/ace-step/ACE-Step-1.5 set up with `uv sync`; NOT `pip install ace-step`, which is v1), in that clone's folder
(AWL_MUSIC_ROOT), one job file per call, one model load per call. It prints one JSON object on its last stdout line.

Jobs:
  check    : torch, CUDA, the acestep package, and whether the checkpoints folder holds the configured music model
  generate : tracks [{video, caption, duration, bpm, seed, fade_in, fade_out, out}] -> one instrumental wav each (48 kHz)

The API used (ACE-Step 1.5 docs/en/INFERENCE.md, checked against the code): AceStepHandler().initialize_service(project_root, config_path,
device, ...) -> (message, ok); generate_music(dit, llm=None, GenerationParams(task_type="text2music", caption, lyrics="[Instrumental]",
duration, bpm, inference_steps, seed, fade_in_duration, fade_out_duration), GenerationConfig(batch_size=1, use_random_seed=False,
audio_format="wav"), save_dir) -> result with .success, .error and .audios[i]["path"]. Without the planning language model (llm None)
the music model runs alone. The instrumental flag of GenerationParams is not read by generate_music: "[Instrumental]" lyrics are.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def op_check(job):
    res = {"ok": False}
    try:
        import torch
        res.update({"torch": torch.__version__, "cuda": torch.cuda.is_available()})
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            res.update({"gpu": p.name, "vram_gb": round(p.total_memory / 1024 ** 3, 1)})
    except Exception as e:  # noqa: BLE001
        res["error"] = f"torch: {type(e).__name__}: {e}"
        return res
    try:
        from acestep.handler import AceStepHandler  # noqa: F401
        from acestep.inference import GenerationConfig, GenerationParams, generate_music  # noqa: F401
    except Exception as e:  # noqa: BLE001
        res["error"] = f"acestep: {type(e).__name__}: {e} (run this with the ACE-Step 1.5 clone's own .venv python, in its folder)"
        return res
    root = Path(job.get("root") or ".")
    ck = Path(os.environ.get("ACESTEP_CHECKPOINTS_DIR") or root / "checkpoints")
    res.update({"ok": True, "root": str(root), "checkpoints": str(ck), "checkpoints_present": ck.is_dir(),
                "model_present": (ck / str(job.get("config") or "acestep-v15-turbo")).exists(),
                "note": "a missing model downloads on its first use (about 10 GB for the core models)"})
    return res


def op_generate(job):
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    dit = AceStepHandler()
    t0 = time.time()
    init = dit.initialize_service(project_root=str(job.get("root") or "."), config_path=str(job.get("config") or "acestep-v15-turbo"),
                                  device=str(job.get("device") or "cuda"), use_flash_attention=False, compile_model=False,
                                  offload_to_cpu=False, offload_dit_to_cpu=False, quantization=None)
    msg, ok = (init if isinstance(init, tuple) and len(init) == 2 else (str(init), True))
    if not ok:
        return {"ok": False, "error": f"initialize_service: {msg}"}
    load_s = round(time.time() - t0, 1)
    made, failed = [], []
    for tr in job["tracks"]:
        t1 = time.time()
        kw = dict(task_type="text2music", caption=str(tr["caption"])[:500], lyrics="[Instrumental]", duration=float(tr["duration"]),
                  inference_steps=int(job.get("steps") or 8), seed=int(tr.get("seed") or 1234),
                  fade_in_duration=float(tr.get("fade_in") or 0.0), fade_out_duration=float(tr.get("fade_out") or 0.0))
        if tr.get("bpm"):
            kw["bpm"] = int(tr["bpm"])
        tmp = Path(tempfile.mkdtemp(prefix="awl-music-"))
        try:
            res = generate_music(dit, None, GenerationParams(**kw), GenerationConfig(batch_size=1, use_random_seed=False, audio_format="wav"),
                                 save_dir=str(tmp))
            if not getattr(res, "success", False) or not getattr(res, "audios", None):
                failed.append({"video": tr["video"], "error": str(getattr(res, "error", "no audio"))[:400]})
                continue
            src = Path(res.audios[0]["path"])
            dest = Path(tr["out"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            made.append({"video": tr["video"], "out": str(dest), "sample_rate": res.audios[0].get("sample_rate"), "seconds": round(time.time() - t1, 1)})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return {"ok": bool(made) and not failed, "made": made, "failed": failed, "load_s": load_s}


def main():
    if len(sys.argv) != 2:
        out({"ok": False, "error": "usage: music_worker.py <job.json>"}, 2)
    try:
        job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"job file: {e}"}, 2)
    ops = {"check": op_check, "generate": op_generate}
    if job.get("op") not in ops:
        out({"ok": False, "error": f"unknown op {job.get('op')!r}"}, 2)
    try:
        res = ops[job["op"]](job)
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}, 1)
    out(res, 0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
