"""Tests of the GPU sharing (cc_gpu.py and the watcher's Whisper policy in cc_proc.py): Whisper is kept while a recording runs, let go when the recording
stopped and nothing came, when a GPU job asks for more memory than is free, when another program has taken the memory, or after the long idle; never
while it transcribes (the watcher asks only when no processor is busy). A lease waits for free memory or for a named job, and falls back to the CPU
when the memory never comes. A second holder of a lease is refused while the first is fresh. The recording is active only with no end and a recent
change. The GPU itself is never touched here (vram and the transcribers are stand-ins). Run: python tests/test_gpu.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_gpu as G  # noqa: E402
import cc_audio as A  # noqa: E402
import cc_proc as P  # noqa: E402

PY = sys.executable
CC = HERE.parent / "scripts" / "cc.py"
FAILED, N = [], [0]


def check(ok, what):
    N[0] += 1
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILED.append(what[:90])


class FakeT:
    def __init__(self, device):
        self.model = object()
        self.used = {"device": device}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc_gpu_test_"))
    real = (G.GPU_DIR, G.vram, G.recording_active, A._TRANSCRIBERS.copy())
    try:
        G.GPU_DIR = tmp / "gpu"
        inbox = tmp / "inbox"
        free = {"mb": 9000}
        G.vram = lambda max_age_s=3.0: {"total_mb": 12288, "used_mb": 12288 - free["mb"], "free_mb": free["mb"], "util_pct": 0}
        rec = {"on": True}
        G.recording_active = lambda inbox, recent_s=600: rec["on"]
        A._TRANSCRIBERS.clear()
        A._TRANSCRIBERS["k"] = FakeT("cuda")
        why = lambda idle: P._whisper_unload_reason(inbox, idle, 600, 120, 700)  # noqa: E731
        check(why(200) is None, "a recording runs and a chunk came 200 s ago: Whisper stays loaded (a reload would cost seconds every chunk)")
        rec["on"] = False
        check("no recording" in (why(130) or ""), "the recording stopped and nothing came for 130 s: let go")
        check(why(60) is None, "the recording stopped a minute ago: kept a little longer (a late chunk may still come)")
        rec["on"] = True
        free["mb"] = 500
        check("another program" in (why(30) or ""), "another program took the GPU's memory (500 MB free): let go")
        free["mb"] = 3000
        G.take("music-separation", need_mb=6000, ttl_s=60, pid=os.getpid())
        check("music-separation needs 6000 MB" in (why(5) or ""), "a GPU job asks for more than is free: let go")
        G.release("music-separation")
        G.take("music-separation", need_mb=1500, ttl_s=60, pid=os.getpid())
        check(why(5) is None, "a GPU job that fits beside Whisper: Whisper stays")
        G.release("music-separation")
        check("idle" in (why(700) or ""), "idle past idle_unload_s even while recording: let go")
        A._TRANSCRIBERS["k"] = FakeT("cpu")
        check(why(300) is None, "a model on the CPU is not the GPU's business: only the long idle frees it")
        A._TRANSCRIBERS.clear()
        check(why(10_000) is None, "nothing loaded: nothing to do")

        # leases
        free["mb"] = 500
        t0 = time.time()
        with G.lease("music-separation", need_mb=1500, wait_s=0) as g:
            check(g["device"] == "cpu" and "only 500 MB" in (g["why"] or "") and (G.GPU_DIR / "lease-music-separation.json").is_file(),
                  "a lease whose memory never comes falls back to the CPU and says why: " + json.dumps(g))
        check(not (G.GPU_DIR / "lease-music-separation.json").exists(), "the lease file is gone when the job ends")
        free["mb"] = 9000
        G.take("capcut-export", ttl_s=60, pid=None, by="exporter")
        with G.lease("music-separation", need_mb=1500, wait_s=0, wait_for=("capcut-export",)) as g:
            check("capcut-export still running" in (g["why"] or "") and g["device"] == "cuda", "separation waits for an export (here: no wait allowed, so it says so)")
        G.release("capcut-export")
        with G.lease("music-separation", need_mb=1500, wait_s=5, wait_for=("capcut-export",)) as g:
            check(g["device"] == "cuda" and not g["why"] and time.time() - t0 < 10, "nothing in the way: the GPU at once")
        stale = G.take("old", ttl_s=0.01, pid=None)
        time.sleep(0.05)
        check(all(x["name"] != "old" for x in G.leases()), "a lease past its time-to-live is ignored")
        G.take("dead", ttl_s=60, pid=999_999)
        check(all(x["name"] != "dead" for x in G.leases()), "a lease of a process that has ended is ignored")
        stale.unlink(missing_ok=True)

        # recording_active (the real function)
        G.recording_active = real[2]
        sd = inbox / "chan" / "20261121-000000-chan"
        sd.mkdir(parents=True)
        (sd / "session.json").write_text(json.dumps({"started_at": "x", "ended_at": None}), encoding="utf-8")
        check(G.recording_active(inbox), "a session with no end and a recent change: active")
        (sd / "session.json").write_text(json.dumps({"started_at": "x", "ended_at": "y"}), encoding="utf-8")
        check(not G.recording_active(inbox), "a session with its end written: not active")
        (sd / "session.json").write_text(json.dumps({"started_at": "x", "ended_at": None}), encoding="utf-8")
        old = time.time() - 3600
        os.utime(sd / "session.json", (old, old))
        check(not G.recording_active(inbox, recent_s=600), "no end but nothing changed for an hour (a recorder that died): not active")
    finally:
        G.GPU_DIR, G.vram, G.recording_active = real[0], real[1], real[2]
        A._TRANSCRIBERS.clear()
        A._TRANSCRIBERS.update(real[3])
        shutil.rmtree(tmp, ignore_errors=True)
    # the command line: a second holder is refused (the live data/gpu folder, cleaned after)
    cp = subprocess.run([PY, str(CC), "gpu", "--take", "test-lease", "--by", "one", "--ttl-s", "60"], capture_output=True, text=True)
    cp2 = subprocess.run([PY, str(CC), "gpu", "--take", "test-lease", "--by", "two"], capture_output=True, text=True)
    subprocess.run([PY, str(CC), "gpu", "--release", "test-lease"], capture_output=True, text=True)
    r2 = json.loads([ln for ln in cp2.stdout.splitlines() if ln.startswith("{")][-1])
    check(cp.returncode == 0 and cp2.returncode == 3 and "held by one" in r2.get("error", ""), "gpu --take: a second holder is refused while the first is fresh")
    print(f"test_gpu: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
