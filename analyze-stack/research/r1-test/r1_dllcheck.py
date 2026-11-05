import ctypes, os, glob
base = r"C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\Lib\site-packages"
for sub in ["ctranslate2", "ctranslate2.libs", r"onnxruntime\capi", "onnxruntime.libs", "opentimelineio", "opentimelineio.libs"]:
    d = os.path.join(base, sub)
    if not os.path.isdir(d):
        print("no dir:", sub); continue
    files = sorted(glob.glob(os.path.join(d, "*.dll")) + glob.glob(os.path.join(d, "*.pyd")))
    for f in files:
        try:
            ctypes.WinDLL(f); print("OK  ", sub, os.path.basename(f))
        except OSError as e:
            print("FAIL", sub, os.path.basename(f), "->", str(e)[:120])
for dll in ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "vcomp140.dll", "concrt140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll"]:
    try:
        ctypes.WinDLL(dll); print("system OK  ", dll)
    except OSError as e:
        print("system FAIL", dll, "->", str(e)[:100])
