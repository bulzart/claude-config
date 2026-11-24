#!/usr/bin/env python3
"""music_worker.py - ACE-Step 1.5 for Static Studio: an instrumental bed under a narration, only when a video's plan calls for one.

Run by the /create-video agents (manual 04) with ACE-Step 1.5's own Python (AWL_MUSIC_PYTHON, the .venv of a clone of
https://github.com/ace-step/ACE-Step-1.5 set up with `uv sync`; NOT `pip install ace-step`, which is v1), in that clone's folder
(AWL_MUSIC_ROOT), one job file per call, one model load per call. It prints one JSON object on its last stdout line.

Jobs:
  check    : torch, CUDA, the acestep package, and whether the checkpoints folder holds the configured music model
  generate : run, video and tracks [{video, beats, caption, duration, bpm, seed, fade_in, fade_out, out}] -> one instrumental wav
             each (48 kHz). Refused before any model loads unless Static Studio's production gate passes (static_core.media_gate:
             the direction locked and current, the beat map checked, each track naming the beats it scores); each track made is
             recorded with its beats and direction revision (70-edit/video-NN/music-provenance.json)

The API used (ACE-Step 1.5 docs/en/INFERENCE.md, checked against the code): AceStepHandler().initialize_service(project_root, config_path,
device, ...) -> (message, ok); generate_music(dit, llm=None, GenerationParams(task_type="text2music", caption, lyrics="[Instrumental]",
duration, bpm, inference_steps, seed, fade_in_duration, fade_out_duration), GenerationConfig(batch_size=1, use_random_seed=False,
audio_format="wav"), save_dir) -> result with .success, .error and .audios[i]["path"]. Without the planning language model (llm None)
the music model runs alone. The instrumental flag of GenerationParams is not read by generate_music: "[Instrumental]" lyrics are.

Loading (2026-11-09): the models load through _low_commit_loading (each tensor read when asked, straight onto the GPU), which keeps the
job's commit memory to the models' own size on this PC; job "low_commit": false loads them ACE-Step's own way. The answer's "loading"
says which ran.

The GPU: while the models load and play, a generate job holds the PC's GPU lease (gpu_lease.py, next to this file), so the PC's
other GPU users make room: GPU_NEED_MB (or the job's gpu_need_mb) and how long it expects to hold the card (music_expected_s), a
wait as long as whoever holds the card warrants (gpu_lease.py; the job's gpu_wait_s caps it), said on stderr, then the job goes
ahead with the same models; the lease is let go however the job ends. The answer's gpu_lease says what it waited for and the
card's size. A job on the CPU ("device") holds none.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

GPU_NEED_MB = 8000        # ACE-Step 1.5 held about 8 GB once loaded (2026-11-09; commit memory, which counts its GPU memory)
MUSIC_LOAD_S, MUSIC_S_PER_S = 90.0, 3.0   # how long a job holds the card (gpu_lease expected_s): loading, then per second of music


def music_expected_s(job):
    secs = 0.0
    for t in job.get("tracks") or []:
        try:
            secs += float((t or {}).get("duration") or 0)
        except (TypeError, ValueError):
            pass
    return MUSIC_LOAD_S + MUSIC_S_PER_S * secs


def out(obj, code=0):
    s = json.dumps(obj, ensure_ascii=False)
    try:
        s.encode(sys.stdout.encoding or "utf-8")
    except (UnicodeEncodeError, LookupError):
        s = json.dumps(obj, ensure_ascii=True)      # a code-page pipe cannot hold every character: escaped, never a crash
    print(s, flush=True)
    sys.exit(code)


def music_root(job):
    # PC adapter: the old pipeline wrapper put "root" in every job file; with none, the folder comes from AWL_MUSIC_ROOT (the same way
    # image_worker.py reads AWL_IMAGE_ROOT), so a bare job file never points ACE-Step at the working folder and a ~10 GB model download.
    return job.get("root") or os.environ.get("AWL_MUSIC_ROOT") or "."


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
    root = Path(music_root(job))
    ck = Path(os.environ.get("ACESTEP_CHECKPOINTS_DIR") or root / "checkpoints")
    res.update({"ok": True, "root": str(root), "checkpoints": str(ck), "checkpoints_present": ck.is_dir(),
                "model_present": (ck / str(job.get("config") or "acestep-v15-turbo")).exists(),
                "note": "a missing model downloads on its first use (about 10 GB for the core models)"})
    return res


def _low_commit_loading(torch, device: str) -> None:
    """ACE-Step's models loaded without their files charged in full (the user, 2026-11-09: "find the solution, verify it").

    On this PC (Windows, WDDM) the GPU's memory counts as commit memory, and safetensors' own safe_open maps a whole file copy-on-write,
    which Windows charges at its full size before a byte is read: loading the 4.46 GB music model held the file's 4.66 GB charge and the
    GPU copy's together, a 13-15 GB peak that the memory guard stopped (measured 2026-11-09 with the guard's --log). Here each tensor is
    read with a plain file read when transformers or safetensors.torch asks for it (one tensor's bytes in memory at a time; every tensor of
    the three model files checked identical to safetensors' own, 1,352 of 1,352), and AutoModel.from_pretrained loads straight onto the
    GPU at the working precision ACE-Step converts to anyway (the text encoder's bf16 file never passes through 32-bit floats). The
    models, their precision and the output are ACE-Step's own; only the loading's memory changes."""
    import safetensors.torch as st_torch
    import transformers
    import transformers.modeling_utils as mu

    kinds = {"F64": torch.float64, "F32": torch.float32, "F16": torch.float16, "BF16": torch.bfloat16, "I64": torch.int64,
             "I32": torch.int32, "I16": torch.int16, "I8": torch.int8, "U8": torch.uint8, "BOOL": torch.bool}
    for name, attr in (("F8_E4M3", "float8_e4m3fn"), ("F8_E5M2", "float8_e5m2"), ("U16", "uint16"), ("U32", "uint32"),
                       ("U64", "uint64")):
        if hasattr(torch, attr):
            kinds[name] = getattr(torch, attr)

    class _Slice:
        def __init__(self, src, key):
            self._src, self._key = src, key

        def get_dtype(self):
            return self._src._hdr[self._key]["dtype"]

        def get_shape(self):
            return list(self._src._hdr[self._key]["shape"])

        def __getitem__(self, idx):
            t = self._src.get_tensor(self._key)
            return t if idx is Ellipsis else t[idx]

    class ReadOpen:
        """safe_open's API (metadata, keys, offset_keys, get_slice, get_tensor, the context) over plain file reads."""

        def __init__(self, filename, framework="pt", device="cpu"):
            self._fh = open(filename, "rb")
            n = int.from_bytes(self._fh.read(8), "little")
            hdr = json.loads(self._fh.read(n))
            self._meta = hdr.pop("__metadata__", None)
            self._hdr, self._base, self._device = hdr, 8 + n, device

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._fh.close()
            return False

        def metadata(self):
            return self._meta

        def keys(self):
            return list(self._hdr)

        def offset_keys(self):
            return sorted(self._hdr, key=lambda k: self._hdr[k]["data_offsets"][0])

        def get_slice(self, key):
            return _Slice(self, key)

        def get_tensor(self, key):
            info = self._hdr[key]
            begin, end = info["data_offsets"]
            kind = kinds[info["dtype"]]
            if end > begin:
                buf = bytearray(end - begin)
                self._fh.seek(self._base + begin)
                if self._fh.readinto(buf) != end - begin:
                    raise OSError(f"short read of {key}")
                t = torch.frombuffer(buf, dtype=kind)
            else:
                t = torch.empty(0, dtype=kind)
            t = t.reshape(info["shape"])
            dev = f"cuda:{self._device}" if isinstance(self._device, int) else self._device
            return t if dev is None or str(dev) == "cpu" else t.to(dev)

    mu.safe_open = ReadOpen
    st_torch.safe_open = ReadOpen
    if not (torch.cuda.is_available() and str(device).startswith("cuda")):
        return
    seen = {}
    orig = transformers.AutoModel.from_pretrained

    def from_pretrained(*args, **kw):
        kw.setdefault("device_map", {"": device})
        if "dtype" in kw or "torch_dtype" in kw:
            seen.setdefault("dtype", kw.get("dtype", kw.get("torch_dtype")))
        else:   # ACE-Step converts every model to its working precision after loading: the same weights, loaded at it
            kw["dtype"] = seen.get("dtype") or (torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16)
        return orig(*args, **kw)

    transformers.AutoModel.from_pretrained = from_pretrained


def gpu_take(job):
    """The PC's GPU lease for this job (gpu_lease.py, next to this file): GPU_NEED_MB or the job's gpu_need_mb; none for a job
    on the CPU."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import gpu_lease
    if not str(job.get("device") or "cuda").startswith("cuda"):
        return gpu_lease.unheld("the job runs on the CPU")
    need, wait = job.get("gpu_need_mb"), job.get("gpu_wait_s")
    return gpu_lease.acquire("music", need_mb=GPU_NEED_MB if need is None else int(need),
                             wait_s=None if wait is None else float(wait),
                             note=f"ACE-Step 1.5: {len(job.get('tracks') or [])} track(s)",
                             expected_s=round(music_expected_s(job), 1))


def op_generate(job):
    """The models load and play (_generate) under the GPU lease, which is let go however that ends."""
    with gpu_take(job) as gpu:
        res = _generate(job)
    res["gpu_lease"] = gpu
    return res


def _generate(job):
    loading = "ACE-Step's own"
    if job.get("low_commit", True):
        try:
            import torch
            _low_commit_loading(torch, str(job.get("device") or "cuda"))
            loading = "low-commit: each tensor read from its file when asked, straight onto the GPU at the working precision"
        except Exception as e:  # noqa: BLE001
            loading = f"ACE-Step's own (the low-commit loading could not be set up: {type(e).__name__}: {e})"
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    quant = job.get("quantization") or None   # ACE-Step's own DiT quantization (torchao): int8_weight_only | fp8_weight_only | w8a8_dynamic
    if quant:
        # the user, 2026-11-09: "int8 quantization of the ace step 1.5 model if possible": the music model is loaded, then quantized by
        # ACE-Step itself; the full-size weights it leaves in PyTorch's cache are released at once, before the next model loads (on this
        # PC a cached GPU block is still commit memory)
        orig_q = AceStepHandler._apply_dit_quantization

        def _quantize_then_release(self, quantization):
            orig_q(self, quantization)
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        AceStepHandler._apply_dit_quantization = _quantize_then_release
    dit = AceStepHandler()
    t0 = time.time()
    init = dit.initialize_service(project_root=str(music_root(job)), config_path=str(job.get("config") or "acestep-v15-turbo"),
                                  device=str(job.get("device") or "cuda"), use_flash_attention=False, compile_model=False,
                                  offload_to_cpu=False, offload_dit_to_cpu=False, quantization=quant)
    msg, ok = (init if isinstance(init, tuple) and len(init) == 2 else (str(init), True))
    if not ok:
        return {"ok": False, "error": f"initialize_service: {msg}", "loading": loading, "quantization": quant}
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:  # noqa: BLE001
        pass
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
    return {"ok": bool(made) and not failed, "made": made, "failed": failed, "load_s": load_s, "loading": loading, "quantization": quant}


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
    gate, sc = None, None
    if job.get("op") == "generate":
        # Before any model loads: the job names its run and video, every track the beats it scores (their sound
        # direction is what the caption carries out), and the direction and beat map are current (static_core.media_gate).
        try:
            here = str(Path(__file__).resolve().parent)
            if here not in sys.path:
                sys.path.insert(0, here)
            import static_core as sc
            gate = sc.media_gate(job, "music")
        except Exception as e:  # noqa: BLE001
            out({"ok": False, "error": f"Static Studio gate unavailable: {type(e).__name__}: {e}"}, 2)
        if not gate["ok"]:
            out({"ok": False, "error": "Static Studio: this music cannot be generated yet (fix the plan, not the gate).",
                 "issues": gate["issues"]}, 2)
    try:
        res = ops[job["op"]](job)
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}, 1)
    if gate:   # which beats each track scores, made under which direction revision
        # the direction each track was made to serve (the treatment's sound, its beats' sound direction, experience and
        # pace, a key moment's meaning) and the job's own account of how its caption serves it: shown, and on record
        res["direction"] = gate.get("direction")
        made = {str(Path(m["out"]).resolve()) for m in res.get("made") or [] if m.get("out")}
        # exactly what ACE-Step was given for each track: the caption as sent (its sha256), the model, steps and seed
        entries = [{"out": str(Path(tr["out"]).resolve()), **rec, "engine": "ace-step-1.5",
                    "config": str(job.get("config") or "acestep-v15-turbo"), "steps": int(job.get("steps") or 8),
                    "seed": int(tr.get("seed") or 1234), "duration": tr.get("duration"),
                    "caption_sent_sha256": hashlib.sha256(str(tr.get("caption") or "")[:500].encode("utf-8")).hexdigest()}
                   for tr, rec in zip(job.get("tracks") or [], gate["records"])
                   if str(Path(str(tr.get("out") or "")).resolve()) in made]
        if entries:
            res["provenance"] = sc.record_media(gate["run"], gate["video"], "music", entries)
    out(res, 0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
