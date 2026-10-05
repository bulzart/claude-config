import importlib, json, sys
mods = ["opentimelineio","scenedetect","faster_whisper","ctranslate2","moviepy","PIL","numpy","cv2",
        "imageio_ffmpeg","yt_dlp","librosa","soundfile","pydub","rapidocr_onnxruntime","onnxruntime",
        "pyJianYingDraft","requests","av","scipy","sklearn","pymediainfo"]
out = {}
for name in mods:
    try:
        m = importlib.import_module(name)
        v = getattr(m, "__version__", None) or getattr(m, "version", None)
        if callable(v):
            try: v = v()
            except Exception: v = "callable"
        out[name] = {"ok": True, "version": str(v)}
    except Exception as e:
        out[name] = {"ok": False, "error": repr(e)}
print(json.dumps(out, indent=1))
print("python", sys.version.split()[0], sys.executable)
try:
    import imageio_ffmpeg; print("imageio_ffmpeg bundled exe:", imageio_ffmpeg.get_ffmpeg_exe())
except Exception as e: print("imageio_ffmpeg err", e)
try:
    import ctranslate2
    print("ctranslate2 cuda devices:", ctranslate2.get_cuda_device_count(), "| cpu compute types:", sorted(ctranslate2.get_supported_compute_types("cpu")))
except Exception as e: print("ct2 info err", e)
try:
    import onnxruntime; print("onnxruntime providers:", onnxruntime.get_available_providers())
except Exception as e: print("ort err", e)
