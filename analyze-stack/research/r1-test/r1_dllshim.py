"""Process-local workaround for a missing system-wide MSVC C++ runtime (msvcp140.dll).
Proper fix: install 'Microsoft Visual C++ 2015-2022 Redistributable (x64)'.
This shim only adds a directory that already contains msvcp140.dll to THIS process's
DLL search path (os.add_dll_directory). It changes nothing on the system.
Import it before ctranslate2 / onnxruntime / opentimelineio / librosa (soxr)."""
import os, ctypes, glob

def _runtime_ok():
    try:
        ctypes.WinDLL("msvcp140.dll"); return True
    except OSError:
        return False

SHIM_DIR = None
if os.name == "nt" and not _runtime_ok():
    cands = []
    for pat in [r"C:\Users\Bulzart\AppData\Local\CapCut\Apps\*\msvcp140.dll",
                r"C:\Program Files\*\msvcp140.dll", r"C:\Program Files\*\*\msvcp140.dll",
                r"C:\Program Files (x86)\*\msvcp140.dll", r"C:\Program Files (x86)\*\*\msvcp140.dll",
                r"C:\Windows\System32\*\msvcp140.dll", r"C:\Windows\System32\*\*\msvcp140.dll"]:
        cands += glob.glob(pat)
    cands = sorted(set(cands), key=lambda p: os.path.getsize(p), reverse=True)  # largest ~ newest
    for p in cands:
        d = os.path.dirname(p)
        try:
            h = os.add_dll_directory(d)
        except OSError:
            continue
        if _runtime_ok():
            SHIM_DIR = d; os.environ["R1_DLL_SHIM_DIR"] = d; break
        h.close()
    if SHIM_DIR is None:
        print("[r1_dllshim] WARNING: no usable msvcp140.dll found; C++ extension imports will fail")
    else:
        print("[r1_dllshim] using runtime DLLs from", SHIM_DIR)
