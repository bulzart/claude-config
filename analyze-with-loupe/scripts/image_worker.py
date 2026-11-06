#!/usr/bin/env python3
"""image_worker.py - FLUX 3 Image Klein (int8) for /analyze-with-loupe Static (contract item 36): a run's stills made on this PC.

Run ONLY by awl.py (`T image ...`, `T static check`) with the Python of a ComfyUI Windows portable install (AWL_IMAGE_PYTHON: a .cmd that
runs its python_embeded\\python.exe inside the memory guard) and that install's folder (AWL_IMAGE_ROOT: the folder that holds
python_embeded and ComfyUI). One job file per call. It starts a private headless ComfyUI on a free 127.0.0.1 port (no browser, no
custom nodes, no partner nodes and no internet for the frontend, nothing pinned in RAM, no metadata in the PNGs), sends every image of
the job as an API workflow, moves the PNGs to their paths, stops ComfyUI and prints one JSON object on its last stdout line.

Jobs:
  check    : the install (ComfyUI and its version, torch, CUDA, the GPU) and the four model files; "probe": true also starts ComfyUI
             and asks it for every node the workflow uses
  generate : images [{prompt, out, width, height, seed, steps, upsample, refs}] -> one PNG each, with the caption the image model got

The workflow is the one of ComfyUI's own FLUX 3 Image Klein templates (comfyui-workflow-templates 0.11.101:
image_flux3_klein_distilled_t2i and image_flux3_klein_distilled_image_edit): UNETLoader (the int8 transformer), CLIPLoader type flux3
(the int8 Qwen3-VL-4B text encoder, and the w4a8 prompt upsampler), VAELoader (flux2-vae), the upsampler as TextGenerateV2 with Black
Forest Labs' own system prompts (flux3_upsampler_prompts.json) and decoding (greedy, presence penalty 1.5 for text-to-image and 0 for
edits, at most 3584 tokens: flux3/pup.py), ReferenceMultiLatent (each reference at 1 MP) for edits, EmptyFlux2LatentImage at the asked
size, KSampler (16 steps, cfg 1, euler, simple). "alpha" sets the timestep shift through ModelSamplingFlux (16 is the reference code's
value since 2026-10-17, flux3/pipeline.py; 6.93 is ComfyUI's built-in launch value); null leaves ComfyUI's own. The upsampler sees
each reference as the reference code prepares it (RGB over white, LANCZOS to its pixel budget, JPEG q92); a transparent reference is
put on white for the image model as well.
"""
import json
import math
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = {"unet": ("diffusion_models", "flux3-image-klein-int8-convrot.safetensors"),
          "text_encoder": ("text_encoders", "qwen3vl_4b_int8_convrot.safetensors"),
          "vae": ("vae", "flux2-vae.safetensors"),
          "upsampler": ("text_encoders", "qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors")}
NODES = ("UNETLoader", "CLIPLoader", "VAELoader", "CLIPTextEncode", "TextGenerateV2", "PreviewAny", "EmptyFlux2LatentImage",
         "ModelSamplingFlux", "KSampler", "VAEDecode", "SaveImage", "LoadImage", "ReferenceMultiLatent", "ConditioningZeroOut")
MAX_REFS = 10
EDGE_MULTIPLE, MIN_EDGE, MAX_EDGE = 16, 64, 4096
STEPS, SAMPLER, SCHEDULER = 16, "euler", "simple"
UPSAMPLER_TOKENS = 3584
PRESENCE = {"t2i": 1.5, "i2i": 0.0}
I2I_SCAFFOLD = "Reference images follow in order (the first image, the second image, ...).\nUser request: {instruction}\nOutput the caption."
REF_MULTIPLE = 32
REF_PIXELS = {1: 1024 * 1024, 2: 724 * 724}          # three or more references: 512 x 512 each (flux3/pup.py)
ASPECTS = ((1, 1), (4, 5), (5, 4), (3, 4), (4, 3), (2, 3), (3, 2), (9, 16), (16, 9), (1, 2), (2, 1), (9, 21), (21, 9))
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # 127.0.0.1 only: never through a proxy


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False), flush=True)
    sys.exit(code)


def locate(job):
    """(portable root, its ComfyUI folder, the models folder)."""
    root = Path(job.get("root") or os.environ.get("AWL_IMAGE_ROOT") or Path(sys.executable).resolve().parent.parent)
    return root, root / "ComfyUI", root / "ComfyUI" / "models"


def model_files(job, models_dir):
    names = {k: v[1] for k, v in MODELS.items()}
    names.update({k: v for k, v in (job.get("models") or {}).items() if k in MODELS and v})
    return names, {k: models_dir / MODELS[k][0] / names[k] for k in MODELS}


def comfy_version(comfy):
    try:
        m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)", (comfy / "comfyui_version.py").read_text(encoding="utf-8"))
        return m.group(1) if m else None
    except OSError:
        return None


# ---- the private ComfyUI

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start(comfy, work, port):
    for d in ("in", "out", "tmp", "user"):
        (work / d).mkdir(parents=True, exist_ok=True)
    log = open(work / "comfyui.log", "w", encoding="utf-8", errors="replace")
    env = {**os.environ, "SSLKEYLOGFILE": "", "HF_HUB_OFFLINE": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    cmd = [sys.executable, "-s", str(comfy / "main.py"), "--listen", "127.0.0.1", "--port", str(port), "--disable-auto-launch",
           "--disable-all-custom-nodes", "--offline", "--disable-pinned-memory", "--disable-metadata",
           "--output-directory", str(work / "out"), "--input-directory", str(work / "in"), "--temp-directory", str(work / "tmp"),
           "--user-directory", str(work / "user"), "--database-url", "sqlite:///:memory:"]
    proc = subprocess.Popen(cmd, cwd=str(comfy), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return proc, log


def http(port, method, path, body=None, timeout=30):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with OPENER.open(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode("utf-8", "replace")
    try:
        return status, json.loads(raw) if raw else None
    except ValueError:
        return status, {"raw": raw[:2000]}


def wait_ready(proc, port, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return None, f"ComfyUI stopped while starting (exit {proc.returncode})"
        try:
            status, js = http(port, "GET", "/system_stats", timeout=5)
            if status == 200:
                return js, None
        except OSError:
            pass
        time.sleep(0.5)
    return None, f"ComfyUI gave no answer within {int(timeout)} s"


def stop(proc, log):
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=20)
    if log is not None:
        log.close()


def tail(work, n=2500):
    try:
        return (work / "comfyui.log").read_text(encoding="utf-8", errors="replace")[-n:]
    except OSError:
        return ""


# ---- the references

def _on_white(im):
    from PIL import Image
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", rgba.size, (255, 255, 255, 255)), rgba)
    return im.convert("RGB")


def _ref_size(width, height, n_refs):
    """The upsampler's pixel budget for one reference (flux3/pup.py reference_size)."""
    floor = lambda v: max(REF_MULTIPLE, int(math.floor(v / REF_MULTIPLE)) * REF_MULTIPLE)  # noqa: E731
    cap = REF_PIXELS.get(n_refs, 512 * 512)
    w = max(REF_MULTIPLE, round(width / REF_MULTIPLE) * REF_MULTIPLE)
    h = max(REF_MULTIPLE, round(height / REF_MULTIPLE) * REF_MULTIPLE)
    if w * h > cap:
        beta = math.sqrt(width * height / cap)
        w, h = floor(width / beta), floor(height / beta)
    if w * h > cap:
        if w == REF_MULTIPLE:
            h = floor(cap / w)
        else:
            w = floor(cap / h)
    return w, h


def stage_refs(refs, work, tag):
    """Copy each reference into ComfyUI's input folder twice: for the image model (on white when transparent) and as the upsampler
    sees it. Returns [(model file name, upsampler file name)]."""
    from PIL import Image, ImageOps
    staged = []
    for i, src in enumerate(refs):
        with Image.open(src) as im0:
            im = _on_white(ImageOps.exif_transpose(im0))
        model_name = f"{tag}-ref{i}.png"
        im.save(work / "in" / model_name, format="PNG")
        size = _ref_size(im.width, im.height, len(refs))
        pim = im if im.size == size else im.resize(size, Image.Resampling.LANCZOS)
        pup_name = f"{tag}-ref{i}-pup.jpg"
        pim.save(work / "in" / pup_name, format="JPEG", quality=92)
        staged.append((model_name, pup_name))
    return staged


# ---- the workflow (API format)

def canvas_line(w, h):
    """The t2i upsampler's optional first line: the nearest plain aspect of a non-square canvas."""
    if w == h:
        return ""
    r = w / h
    a, b = min(ASPECTS, key=lambda ab: abs(math.log(r / (ab[0] / ab[1]))))
    return f"TARGET CANVAS: {a}:{b}\n"


def build(img, names, prompts, staged, tag):
    """The API graph of one image; returns (graph, the SaveImage node id, the caption node id or None)."""
    w, h, steps, seed = img["width"], img["height"], img["steps"], img["seed"]
    g = {"unet": {"class_type": "UNETLoader", "inputs": {"unet_name": names["unet"], "weight_dtype": "default"}},
         "te": {"class_type": "CLIPLoader", "inputs": {"clip_name": names["text_encoder"], "type": "flux3", "device": "default"}},
         "vae": {"class_type": "VAELoader", "inputs": {"vae_name": names["vae"]}}}
    model = ["unet", 0]
    if img.get("alpha"):
        shift = math.log(float(img["alpha"]))
        g["shift"] = {"class_type": "ModelSamplingFlux", "inputs": {"model": ["unet", 0], "max_shift": shift, "base_shift": shift,
                                                                    "width": w, "height": h}}
        model = ["shift", 0]
    task = "i2i" if staged else "t2i"
    caption_node = None
    if img["upsample"]:
        g["up"] = {"class_type": "CLIPLoader", "inputs": {"clip_name": names["upsampler"], "type": "flux3", "device": "default"}}
        request = I2I_SCAFFOLD.format(instruction=img["prompt"]) if staged else canvas_line(w, h) + img["prompt"]
        tg = {"clip": ["up", 0], "prompt": request, "max_length": UPSAMPLER_TOKENS, "sampling_mode": "on",
              "sampling_mode.temperature": 1.0, "sampling_mode.top_k": 1, "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0.0,
              "sampling_mode.repetition_penalty": 1.0, "sampling_mode.presence_penalty": PRESENCE[task], "sampling_mode.seed": 0,
              "thinking": False, "use_default_template": True, "mtp": img.get("mtp") or "off", "system_prompt": prompts[task]}
        for i, (_m, pup_name) in enumerate(staged):
            g[f"pupref{i}"] = {"class_type": "LoadImage", "inputs": {"image": pup_name}}
            tg[f"images.image{i + 1}"] = [f"pupref{i}", 0]
        g["upsample"] = {"class_type": "TextGenerateV2", "inputs": tg}
        g["caption"] = {"class_type": "PreviewAny", "inputs": {"source": ["upsample", 0]}}
        caption_node, text = "caption", ["upsample", 0]
    else:
        text = img["prompt"]
    g["pos"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["te", 0], "text": text}}
    g["latent"] = {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}}
    if staged:
        g["neg"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}}
        rm = {"positive": ["pos", 0], "negative": ["neg", 0], "vae": ["vae", 0], "resolution": "resize", "resolution.megapixels": 1.0}
        for i, (model_name, _p) in enumerate(staged):
            g[f"ref{i}"] = {"class_type": "LoadImage", "inputs": {"image": model_name}}
            rm[f"images.image{i}"] = [f"ref{i}", 0]
        g["refs"] = {"class_type": "ReferenceMultiLatent", "inputs": rm}
        positive, negative = ["refs", 0], ["refs", 1]
    else:
        g["neg"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["te", 0], "text": ""}}
        positive, negative = ["pos", 0], ["neg", 0]
    g["sample"] = {"class_type": "KSampler", "inputs": {"model": model, "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": SAMPLER,
                                                         "scheduler": SCHEDULER, "positive": positive, "negative": negative,
                                                         "latent_image": ["latent", 0], "denoise": 1.0}}
    g["decode"] = {"class_type": "VAEDecode", "inputs": {"samples": ["sample", 0], "vae": ["vae", 0]}}
    g["save"] = {"class_type": "SaveImage", "inputs": {"images": ["decode", 0], "filename_prefix": tag}}
    return g, "save", caption_node


def run_prompt(proc, port, graph, timeout):
    """Queue one graph and wait for it; (history entry, error text)."""
    status, js = http(port, "POST", "/prompt", {"prompt": graph, "client_id": uuid.uuid4().hex}, timeout=60)
    if status != 200 or not isinstance(js, dict) or not js.get("prompt_id"):
        return None, "ComfyUI refused the workflow: " + json.dumps(js, ensure_ascii=False)[:1500]
    pid, t0 = js["prompt_id"], time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return None, f"ComfyUI stopped while making the image (exit {proc.returncode})"
        try:
            _s, hist = http(port, "GET", f"/history/{pid}", timeout=30)
        except OSError:
            hist = None
        entry = (hist or {}).get(pid) if isinstance(hist, dict) else None
        st = (entry or {}).get("status") or {}
        if entry and (st.get("completed") or st.get("status_str") in ("success", "error")):
            if st.get("status_str") == "error":
                msgs = [m[1] for m in st.get("messages") or [] if isinstance(m, list) and len(m) == 2 and m[0] == "execution_error"]
                e = msgs[0] if msgs else {}
                return None, (f"{e.get('node_type')}: {e.get('exception_type')}: {e.get('exception_message')}".strip()
                              if e else "ComfyUI reported an error")[:1500]
            return entry, None
        time.sleep(1.0)
    return None, f"no image after {int(timeout)} s"


def _int(v, name):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a whole number, got {v!r}") from None


def normalise(img, i):
    if not str(img.get("prompt") or "").strip():
        raise ValueError(f"image {i + 1}: no prompt")
    if not img.get("out"):
        raise ValueError(f"image {i + 1}: no out path")
    w, h = _int(img.get("width") or 1024, "width"), _int(img.get("height") or 1024, "height")
    for name, v in (("width", w), ("height", h)):
        if v % EDGE_MULTIPLE or not MIN_EDGE <= v <= MAX_EDGE:
            raise ValueError(f"image {i + 1}: {name} {v} must be a multiple of {EDGE_MULTIPLE} between {MIN_EDGE} and {MAX_EDGE}")
    refs = [Path(r) for r in img.get("refs") or []]
    if len(refs) > MAX_REFS:
        raise ValueError(f"image {i + 1}: at most {MAX_REFS} reference images, got {len(refs)}")
    missing = [str(r) for r in refs if not r.is_file()]
    if missing:
        raise ValueError(f"image {i + 1}: reference image(s) not found: " + "; ".join(missing))
    seed = img.get("seed")
    seed = random.randint(0, 2 ** 32 - 1) if seed is None else _int(seed, "seed")
    return {"prompt": str(img["prompt"]).strip(), "out": str(img["out"]), "width": w, "height": h, "seed": seed,
            "steps": _int(img.get("steps") or STEPS, "steps"), "upsample": img.get("upsample", True) is not False,
            "refs": [str(r) for r in refs], "alpha": img.get("alpha"), "mtp": img.get("mtp")}


# ---- the jobs

def op_check(job):
    root, comfy, models_dir = locate(job)
    res = {"ok": False, "root": str(root), "python": sys.executable, "comfyui": comfy_version(comfy)}
    if not (comfy / "main.py").is_file():
        res["error"] = f"no ComfyUI\\main.py under {root} (AWL_IMAGE_ROOT is the portable folder that holds python_embeded and ComfyUI)"
        return res
    try:
        import torch
        res.update({"torch": torch.__version__, "cuda": torch.cuda.is_available()})
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            res.update({"gpu": p.name, "vram_gb": round(p.total_memory / 1024 ** 3, 1), "compute": f"{p.major}.{p.minor}"})
    except Exception as e:  # noqa: BLE001
        res["error"] = f"torch: {type(e).__name__}: {e} (run this with the portable's python_embeded\\python.exe)"
        return res
    _names, files = model_files(job, models_dir)
    res["models"] = {k: {"file": str(f), "present": f.is_file(), "gb": round(f.stat().st_size / 1e9, 2) if f.is_file() else None}
                     for k, f in files.items()}
    missing = [k for k, v in res["models"].items() if not v["present"]]
    if not res.get("cuda"):
        res["error"] = "CUDA is not available to this torch"
        return res
    res["ok"] = not missing
    if missing:
        res["error"] = "model files missing: " + ", ".join(f"{k} ({res['models'][k]['file']})" for k in missing)
    if job.get("probe"):
        work = Path(tempfile.mkdtemp(prefix="awl-image-"))
        proc = log = None
        try:
            port, t0 = free_port(), time.time()
            proc, log = start(comfy, work, port)
            stats, err = wait_ready(proc, port, float(job.get("start_timeout") or 300))
            t_start = time.time() - t0
            if err:
                res.update({"ok": False, "error": err, "log_tail": tail(work)})
                return res
            res["system"] = {"comfyui": (stats.get("system") or {}).get("comfyui_version"),
                             "devices": [{k: d.get(k) for k in ("name", "vram_total", "vram_free")} for d in stats.get("devices") or []]}
            absent = []
            for n in NODES:
                status, js = http(port, "GET", f"/object_info/{n}", timeout=30)
                if status != 200 or not isinstance(js, dict) or n not in js:
                    absent.append(n)
            res["nodes_missing"] = absent
            _s, cl = http(port, "GET", "/object_info/CLIPLoader", timeout=30)
            spec = ((((cl or {}).get("CLIPLoader") or {}).get("input") or {}).get("required") or {}).get("type") or [[]]
            types = spec[0] if isinstance(spec[0], list) else ((spec[1] or {}).get("options") if len(spec) > 1 and isinstance(spec[1], dict) else [])
            res["clip_type_flux3"] = "flux3" in (types or [])
            if absent or not res["clip_type_flux3"]:
                res.update({"ok": False, "error": "this ComfyUI lacks a node the FLUX 3 Klein workflow needs: update it (0.41.0 or later)"})
            res["start_s"] = round(t_start, 1)
        finally:
            stop(proc, log)
            shutil.rmtree(work, ignore_errors=True)
    return res


def op_generate(job):
    root, comfy, models_dir = locate(job)
    names, files = model_files(job, models_dir)
    missing = [str(f) for f in files.values() if not f.is_file()]
    if missing:
        return {"ok": False, "error": "model files missing: " + "; ".join(missing)}
    try:
        prompts = json.loads((HERE / "flux3_upsampler_prompts.json").read_text(encoding="utf-8"))
        imgs = [normalise({"alpha": job.get("alpha"), **im}, i) for i, im in enumerate(job.get("images") or [])]
    except (OSError, ValueError) as e:
        return {"ok": False, "error": str(e)}
    if not imgs:
        return {"ok": False, "error": "the job has no images"}
    work = Path(tempfile.mkdtemp(prefix="awl-image-"))
    proc = log = None
    results, t_all = [], time.time()
    try:
        port = free_port()
        proc, log = start(comfy, work, port)
        stats, err = wait_ready(proc, port, float(job.get("start_timeout") or 300))
        if err:
            return {"ok": False, "error": err, "log_tail": tail(work), "images": results}
        version = (stats.get("system") or {}).get("comfyui_version")
        for i, img in enumerate(imgs):
            tag, t0 = f"img{i:03d}", time.time()
            res = {k: img[k] for k in ("out", "seed", "width", "height", "steps", "upsample", "refs", "alpha")}
            res["request"] = img["prompt"]
            try:
                staged = stage_refs(img["refs"], work, tag)
                graph, save_id, cap_id = build(img, names, prompts, staged, tag)
                entry, err = run_prompt(proc, port, graph, float(job.get("timeout_per_image") or 1800))
            except Exception as e:  # noqa: BLE001
                entry, err = None, f"{type(e).__name__}: {e}"
            if err:
                res.update({"ok": False, "error": err, "seconds": round(time.time() - t0, 1)})
                results.append(res)
                if proc.poll() is not None:
                    break
                continue
            outs = entry.get("outputs") or {}
            files_ = (outs.get(save_id) or {}).get("images") or []
            src = work / "out" / (files_[0].get("subfolder") or "") / files_[0]["filename"] if files_ else None
            if src is None or not src.is_file():
                res.update({"ok": False, "error": "ComfyUI finished without an image file", "seconds": round(time.time() - t0, 1)})
                results.append(res)
                continue
            dest = Path(img["out"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            caption = ((outs.get(cap_id) or {}).get("text") or [None])[0] if cap_id else img["prompt"]
            res.update({"ok": True, "caption": caption, "seconds": round(time.time() - t0, 1)})
            results.append(res)
        ok = bool(results) and all(r.get("ok") for r in results) and len(results) == len(imgs)
        ans = {"ok": ok, "engine": "flux3-image-klein-int8", "comfyui": version, "models": names, "images": results,
               "seconds": round(time.time() - t_all, 1)}
        if not ok:
            ans["error"] = next((r.get("error") for r in results if not r.get("ok")), "not every image was made")
            ans["log_tail"] = tail(work)
        return ans
    finally:
        stop(proc, log)
        shutil.rmtree(work, ignore_errors=True)


def main():
    if len(sys.argv) != 2:
        out({"ok": False, "error": "usage: image_worker.py <job.json>"}, 2)
    try:
        job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        out({"ok": False, "error": f"job file: {e}"}, 2)
    op = {"check": op_check, "generate": op_generate}.get(job.get("op"))
    if op is None:
        out({"ok": False, "error": f"unknown op {job.get('op')!r} (check | generate)"}, 2)
    try:
        res = op(job)
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}, 1)
    out(res, 0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
