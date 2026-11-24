"""Tests of scripts/gpu_lease.py, the GPU lease Static Studio's GPU jobs hold (FLUX 3 Klein, ACE-Step, Whisper) in the PC's
shared lease format. Every test uses a temporary lease folder (STATIC_GPU_LEASE_DIR) and a stand-in for the GPU's memory:
nothing here writes the PC's real lease folder, starts a model or uses the GPU.
Run from this folder: python -B -m unittest test_gpu_lease"""
from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
CC_SCRIPTS = HERE.parents[1] / "create-clips" / "scripts"     # the other reader of these lease files on this PC (read-only here)
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import gpu_lease as L  # noqa: E402

CARD = 12288
FIELDS = {"name", "need_mb", "t", "at", "ttl_s", "pid", "note", "by"}

# A second holder in its own process: it takes a lease, says HELD, waits for a line on stdin, then ends as `mode` says
# ("exit": the script ends; "raise": an uncaught error; "with-exit": sys.exit(3) inside the with-block).
HOLDER = r'''
import sys
sys.path.insert(0, sys.argv[1])
import gpu_lease as L
L.vram = lambda max_age_s=3.0: {"total_mb": 12288, "used_mb": 0, "free_mb": 12288, "util_pct": 0}
kind, need, mode = sys.argv[2], int(sys.argv[3]), sys.argv[4]
if mode == "with-exit":
    with L.acquire(kind, need_mb=need):
        print("HELD", flush=True)
        sys.stdin.readline()
        sys.exit(3)
lease = L.acquire(kind, need_mb=need)
print("HELD", flush=True)
sys.stdin.readline()
if mode == "raise":
    raise RuntimeError("the job failed")
'''

# The other reader of the lease files, imported read-only in a child process through its own decrypt-on-import hook
# (-B: no bytecode written; its lease folder is pointed at this test's folder in memory). Its watcher's own rule then says
# whether an idle Whisper is let go for our lease; the GPU and the transcriber are stand-ins, as in its own tests.
READER = r'''
import json, sys
from pathlib import Path
cc_scripts, folder, free = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, cc_scripts)
try:
    import cc_crypto_loader  # noqa: F401
    import cc_gpu as G
    import cc_audio as A
    import cc_proc as P
except ImportError as e:
    print(json.dumps({"skip": f"{type(e).__name__}: {e}"[:400]}))
    sys.exit(0)
G.GPU_DIR = folder
G.vram = lambda max_age_s=3.0: {"total_mb": 12288, "used_mb": 12288 - free, "free_mb": free, "util_pct": 0}
G.recording_active = lambda inbox, recent_s=600: True
class Whisper:
    model = object()
    used = {"device": "cuda"}
A._TRANSCRIBERS.clear()
A._TRANSCRIBERS["k"] = Whisper()
print(json.dumps({"leases": G.leases(), "unload_reason": P._whisper_unload_reason(folder / "inbox", 5, 600, 120, 700)}))
'''


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GpuLeaseTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="gpu-lease-test-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.dir = self.root / "gpu"
        self.pids = {os.getpid()}
        self.addCleanup(self.real_folder_untouched)
        self.gpu = {"total_mb": CARD, "used_mb": 1000, "free_mb": CARD - 1000, "util_pct": 0}
        for p in (mock.patch.dict(os.environ, {L.LEASE_DIR_ENV: str(self.dir), "PYTHONDONTWRITEBYTECODE": "1"}),
                  mock.patch.object(L, "vram", new=lambda max_age_s=3.0: dict(self.gpu))):
            p.start()
            self.addCleanup(p.stop)
        err = mock.patch.object(sys, "stderr", new_callable=io.StringIO)
        self.err = err.start()
        self.addCleanup(err.stop)
        self.addCleanup(L.release_all)                         # a failed test leaves no lease for the next one

    def real_folder_untouched(self):
        real = L.default_lease_dir()
        if real.is_dir():
            pids = {str(p) for p in self.pids}
            mine = [p.name for p in real.glob("lease-create-video-*.json") if p.stem.rsplit("-", 1)[-1] in pids]
            self.assertEqual(mine, [], "a test wrote into the PC's real lease folder")

    def file_of(self, kind, pid=None):
        return self.dir / f"lease-create-video-{kind}-{pid or os.getpid()}.json"

    def read(self, f):
        for _ in range(20):                                    # a beat may be replacing the file this instant
            d = L._read(f)
            if d is not None:
                return d
            time.sleep(0.05)
        self.fail(f"{f} cannot be read")

    def put(self, name, **kw):
        rec = {"name": name, "need_mb": 9000, "t": time.time(), "at": "2026-11-24T05:00:00+01:00", "ttl_s": 600.0,
               "pid": None, "note": "", "by": "someone", **kw}
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / f"lease-{name}.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")

    def holder(self, kind, need, mode="exit"):
        p = subprocess.Popen([sys.executable, "-B", "-c", HOLDER, str(SCRIPTS), kind, str(need), mode], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ))
        self.addCleanup(self.end, p)
        self.pids.add(p.pid)
        line = p.stdout.readline().strip()
        if line != "HELD":
            p.kill()
            self.fail(f"the second holder did not start: {line!r} {p.communicate(timeout=30)[1]}")
        return p

    @staticmethod
    def end(p):
        if p.poll() is None:
            p.kill()
        try:
            p.communicate(timeout=30)
        except Exception:  # noqa: BLE001 - already read
            pass

    @staticmethod
    def dead_pid():
        p = subprocess.Popen([sys.executable, "-B", "-c", "pass"])
        p.wait(30)
        return p                                               # kept by the caller: its pid is not given to another process

    def test_a_lease_is_written_in_the_shared_format_and_let_go(self):
        self.assertEqual(L.lease_dir(), self.dir)
        lease = L.acquire("flux", need_mb=7168, note="flux3-image-klein-int8: 1 image(s), 1216x2160")
        raw = self.file_of("flux").read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        rec = json.loads(raw.decode("utf-8"))
        self.assertEqual(set(rec), FIELDS)
        self.assertEqual((rec["name"], rec["need_mb"], rec["pid"], rec["by"], rec["note"]),
                         (f"create-video-flux-{os.getpid()}", 7168, os.getpid(), "create-video",
                          "flux3-image-klein-int8: 1 image(s), 1216x2160"))
        self.assertIsInstance(rec["t"], float)
        self.assertIsInstance(rec["ttl_s"], float)
        self.assertLess(abs(dt.datetime.fromisoformat(rec["at"]).timestamp() - rec["t"]), 2)
        self.assertEqual([x["name"] for x in L.leases()], [rec["name"]])
        self.assertEqual((lease.held, lease.info["held"], lease.info["waited_s"], lease.info["why"]), (True, True, 0.0, None))
        lease.release()
        self.assertFalse(self.file_of("flux").exists())
        self.assertEqual((L.leases(), lease.held), ([], False))
        lease.release()                                        # a second release changes nothing
        with L.acquire("music", need_mb=8000) as info:         # the with-form: held inside, gone after
            self.assertTrue(info["held"])
            self.assertTrue(self.file_of("music").is_file())
        self.assertEqual(sorted(self.dir.iterdir()), [])        # no lease and no temporary file left behind
        # A nested hold of the same kind in one process shares the lease (no second wait); it goes with the last release.
        outer = L.acquire("whisper", need_mb=2200)
        self.gpu["free_mb"] = 100
        t0 = time.time()
        inner = L.acquire("whisper", need_mb=2200, wait_s=60)
        self.assertLess(time.time() - t0, 0.5)
        self.assertTrue(inner.info.get("nested"))
        self.assertEqual(len(list(self.dir.glob("lease-*.json"))), 1)
        inner.release()
        self.assertTrue(self.file_of("whisper").is_file())
        outer.release()
        self.assertFalse(self.file_of("whisper").exists())

    def test_a_live_holder_stays_fresh_and_t_stays_when_it_was_taken(self):
        lease = L.acquire("music", need_mb=8000, ttl_s=0.6, beat_s=0.1)
        f = self.file_of("music")
        t = self.read(f)["t"]
        time.sleep(1.5)                                        # well past its first time-to-live
        rec = self.read(f)
        self.assertEqual(rec["t"], t)
        self.assertGreater(rec["ttl_s"], 1.2)
        self.assertEqual([x["name"] for x in L.leases()], [lease.name])
        lease.release()
        time.sleep(0.3)
        self.assertFalse(f.exists())                           # the beat stopped with it: nothing brings the file back

    def test_a_second_holder_sees_the_lease(self):
        p = self.holder("music", 8000)
        self.assertEqual([(x["name"], x["pid"], x["need_mb"]) for x in L.leases()],
                         [(f"create-video-music-{p.pid}", p.pid, 8000)])
        # A job that would not fit beside it (8000 + 7168 MB on a 12288 MB card) waits for it, says so, and goes ahead.
        t0 = time.time()
        flux = L.acquire("flux", need_mb=7168, wait_s=0.6, poll_s=0.05)
        self.addCleanup(flux.release)
        took = time.time() - t0
        self.assertTrue(0.55 <= took < 5, took)
        self.assertIn(f"create-video-music-{p.pid} holds it (8000 MB, by create-video since ", flux.info["why"])
        self.assertIn("waiting for the GPU (up to 1 s)", self.err.getvalue())
        self.assertIn("going ahead on the GPU after", self.err.getvalue())
        self.assertTrue(flux.held)
        self.assertEqual(sorted(x["name"] for x in L.leases()),
                         sorted([f"create-video-music-{p.pid}", f"create-video-flux-{os.getpid()}"]))
        # A job that fits beside both does not wait.
        t0 = time.time()
        whisper = L.acquire("whisper", need_mb=2200, wait_s=5, poll_s=0.05)
        self.addCleanup(whisper.release)
        self.assertLess(time.time() - t0, 0.5)
        self.assertIsNone(whisper.info["why"])
        # The first holder ends: its lease went with it.
        _out, err = p.communicate("go\n", timeout=30)
        self.assertEqual(p.returncode, 0, err)
        self.assertFalse(self.file_of("music", p.pid).exists())

    def test_a_dead_or_expired_holder_is_taken_over(self):
        ended = self.dead_pid()
        self.pids.add(ended.pid)
        self.put(f"create-video-music-{ended.pid}", pid=ended.pid)      # its process has ended
        self.put("create-video-flux-1", t=time.time() - 3600)            # no pid, past its time-to-live
        self.put("music-separation", pid=ended.pid)                     # another holder's stale lease
        self.assertEqual(L.leases(), [])                                # stale leases count for nobody
        self.put("capcut-export", need_mb=0)                            # a lease taken by hand, no pid: lives by its ttl
        self.assertEqual([x["name"] for x in L.leases()], ["capcut-export"])
        t0 = time.time()
        lease = L.acquire("flux", need_mb=7168, wait_s=5, poll_s=0.05)  # each stale one would be in its way if live
        self.addCleanup(lease.release)
        self.assertLess(time.time() - t0, 1.0)
        self.assertIsNone(lease.info["why"])
        self.assertEqual(sorted(p.name for p in self.dir.glob("lease-*.json")),     # ours taken over, others' left alone
                         sorted([self.file_of("flux").name, "lease-music-separation.json", "lease-capcut-export.json"]))
        # An old file under this process's own name (an earlier process had this pid) is written over.
        self.put(f"create-video-whisper-{os.getpid()}", pid=os.getpid(), t=time.time() - 3600, need_mb=1)
        whisper = L.acquire("whisper", need_mb=2200)
        self.addCleanup(whisper.release)
        rec = self.read(self.file_of("whisper"))
        self.assertEqual((rec["need_mb"], rec["by"]), (2200, "create-video"))
        self.assertGreater(rec["t"], time.time() - 5)

    def test_the_lease_is_let_go_on_an_error_and_at_exit(self):
        with self.assertRaises(RuntimeError):
            with L.acquire("music", need_mb=8000):
                self.assertTrue(self.file_of("music").is_file())
                raise RuntimeError("the job failed")
        self.assertFalse(self.file_of("music").exists())
        # Ctrl+C while it waits: nothing is left behind.
        self.gpu["free_mb"] = 1000
        with mock.patch.object(L, "_sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                L.acquire("flux", need_mb=7168, wait_s=60, poll_s=0.05)
        self.assertEqual(list(self.dir.glob("lease-*.json")), [])
        self.gpu["free_mb"] = CARD - 1000
        # A holder process that ends (normally, by an uncaught error, by sys.exit inside the with-block) leaves none.
        for mode, code in (("exit", 0), ("raise", 1), ("with-exit", 3)):
            p = self.holder("music", 8000, mode)
            self.assertTrue(self.file_of("music", p.pid).is_file())
            _out, err = p.communicate("go\n", timeout=30)
            self.assertEqual(p.returncode, code, err)
            self.assertFalse(self.file_of("music", p.pid).exists(), f"{mode}: the lease outlived its process")
        # A killed holder cannot let go: its lease is left with a dead pid, counts for nobody, and is taken over.
        p = self.holder("music", 8000)
        p.kill()
        p.wait(30)
        self.assertTrue(self.file_of("music", p.pid).is_file())
        self.assertEqual(L.leases(), [])
        lease = L.acquire("flux", need_mb=7168, wait_s=5, poll_s=0.05)
        self.addCleanup(lease.release)
        self.assertIsNone(lease.info["why"])
        self.assertFalse(self.file_of("music", p.pid).exists())

    def test_the_wait_is_bounded_and_said_on_stderr(self):
        # Memory short and nothing else in the way: it waits while memory may still come back, then goes ahead on the GPU.
        self.gpu["free_mb"] = 3000
        t0 = time.time()
        lease = L.acquire("flux", need_mb=7168, wait_s=30, poll_s=0.05, settle_s=0.4)
        took = time.time() - t0
        lease.release()
        self.assertTrue(0.35 <= took < 5, took)
        self.assertEqual(lease.info["why"], "only 3000 MB free of the 7168 MB this job needs")
        self.assertIn("waiting for the GPU (up to 0 s): only 3000 MB free", self.err.getvalue())
        self.assertEqual((lease.info["waited_for"], lease.info["card_mb"]), ("outside", CARD))
        self.assertIn("going ahead on the GPU after", self.err.getvalue())
        t0 = time.time()                                       # a wait ends on time, not a whole poll later
        L.acquire("flux", need_mb=7168, wait_s=0.5, poll_s=2.0, settle_s=30).release()
        self.assertLess(time.time() - t0, 1.5)
        # Memory that comes back ends the wait early, with nothing left to report.
        self.err.seek(0)
        self.err.truncate()
        readings = iter([3000, 3000, 6000, 9000])

        def coming_back(max_age_s=3.0):
            self.gpu["free_mb"] = next(readings, 9000)
            return dict(self.gpu)
        with mock.patch.object(L, "vram", new=coming_back):
            lease = L.acquire("flux", need_mb=7168, wait_s=30, poll_s=0.05, settle_s=10)
        lease.release()
        self.assertIsNone(lease.info["why"])
        self.assertLess(lease.info["waited_s"], 5)
        self.assertIn("the GPU is ready after", self.err.getvalue())
        # An earlier holder in the way: at most wait_s, however long it holds (the settle time does not cut it short).
        p = self.holder("music", 8000)
        self.gpu["free_mb"] = CARD - 1000
        t0 = time.time()
        lease = L.acquire("flux", need_mb=7168, wait_s=0.8, poll_s=0.05, settle_s=0.1)
        took = time.time() - t0
        lease.release()
        self.assertTrue(0.75 <= took < 5, took)
        self.assertIn(f"create-video-music-{p.pid} holds it", lease.info["why"])
        p.communicate("go\n", timeout=30)
        # wait_s 0: no wait at all, whatever the memory.
        self.gpu["free_mb"] = 100
        t0 = time.time()
        lease = L.acquire("whisper", need_mb=2200, wait_s=0)
        lease.release()
        self.assertLess(time.time() - t0, 0.3)
        self.assertIsNone(lease.info["why"])
        self.gpu["free_mb"] = CARD - 1000
        # A lease taken after this job's is not waited for (first come, first served) ...
        self.put("create-video-music-77", need_mb=8000, t=time.time() + 60, pid=os.getpid(), by="create-video")
        lease = L.acquire("flux", need_mb=7168, wait_s=5, poll_s=0.05)
        lease.release()
        self.assertIsNone(lease.info["why"])
        # ... nor one that declares no memory, unless the job names it in wait_for.
        self.put("capcut-export", need_mb=0, pid=os.getpid(), by="sess")
        lease = L.acquire("flux", need_mb=7168, wait_s=5, poll_s=0.05)
        lease.release()
        self.assertIsNone(lease.info["why"])
        lease = L.acquire("flux", need_mb=7168, wait_s=0.3, poll_s=0.05, wait_for=("capcut-*",))
        lease.release()
        self.assertIn("capcut-export holds it (0 MB, by sess since ", lease.info["why"])

    def test_the_wait_follows_who_holds_the_card(self):
        # No universal wait (the user, 2026-11-24). An earlier GPU job is waited for until it ends, or until it has run
        # twice the time it said it needs (then it is treated as stuck); create-clips' recorder is given the time it
        # takes to let an idle Whisper go; memory held outside the leases only settle_s.
        # (taken a little earlier: two leases written in one tick of the Windows clock would tie on t)
        self.put("create-video-music-9", need_mb=8000, pid=os.getpid(), expected_s=0.5, by="create-video",
                 t=time.time() - 0.1)
        self.gpu["free_mb"] = CARD - 9000
        t0 = time.time()
        lease = L.acquire("flux", need_mb=7168, poll_s=0.05, expected_s=120)
        took = time.time() - t0
        lease.release()
        self.assertTrue(0.6 <= took < 5, took)                 # 2 x 0.5 s from when that lease was taken
        self.assertEqual(lease.info["waited_for"], "lease")
        self.assertIn("create-video-music-9 holds it", lease.info["why"])
        (self.dir / "lease-create-video-music-9.json").unlink()
        # create-clips' recorder holds its Whisper: the wait is its yield time (capped here by wait_s)
        (self.dir / "whisper.json").write_text(json.dumps({"loaded": True, "pid": os.getpid(), "at": "x"}), encoding="utf-8")
        self.gpu["free_mb"] = 3000
        lease = L.acquire("flux", need_mb=7168, wait_s=0.3, poll_s=0.05)
        lease.release()
        self.assertEqual(lease.info["waited_for"], "recorder")
        self.assertIn("the recorder beside the leases holds its Whisper", lease.info["why"])
        self.assertIn("waiting for the GPU (up to 0 s)", self.err.getvalue())
        (self.dir / "whisper.json").write_text(json.dumps({"loaded": False, "pid": os.getpid(), "at": "x"}), encoding="utf-8")
        lease = L.acquire("flux", need_mb=7168, poll_s=0.05, settle_s=0.2)
        lease.release()
        self.assertEqual(lease.info["waited_for"], "outside")
        # a job's own estimate is published for the others' wait
        lease = L.acquire("whisper", need_mb=2200, wait_s=0, expected_s=42)
        self.assertEqual(self.read(self.file_of("whisper"))["expected_s"], 42.0)
        lease.release()
        # a job that declares more than the card holds is said so
        lease = L.acquire("flux", need_mb=CARD + 1000, wait_s=0)
        lease.release()
        self.assertIn("the card has 12288 MB in all", lease.info["why"])

    def test_capcut_store_is_coordinated_with_the_other_capcut_users(self):
        # create-clips' builds (capcut-build-*) and GUI exports (capcut-export) in the same folder: ours wait for them,
        # and our build holds its own capcut-build lease (their export waits for it), never counted against ourselves.
        self.dir.mkdir(parents=True, exist_ok=True)
        self.assertEqual(L.capcut_store_users(), [])
        lease, busy = L.hold_capcut_build("a test build")
        self.assertEqual(busy, [])
        f = self.dir / f"lease-{L.OWN_BUILD_PREFIX}{os.getpid()}.json"
        self.assertTrue(f.is_file())
        self.assertEqual(L.capcut_store_users(), [])                   # our own build is not in our way
        self.assertFalse((self.dir / L.CAPCUT_DESK_LOCK).exists())     # the desk lock is let go at once
        lease.release()
        self.assertFalse(f.exists())
        self.put("capcut-build-07-4242", need_mb=0, pid=os.getpid(), by="create-clips")
        self.assertEqual([x["name"] for x in L.capcut_store_users()], ["capcut-build-07-4242"])
        lease, busy = L.hold_capcut_build("a test build")
        self.assertIsNone(lease)
        self.assertEqual(busy[0]["name"], "capcut-build-07-4242")
        (self.dir / "lease-capcut-build-07-4242.json").unlink()
        self.put("capcut-export", need_mb=0, pid=os.getpid(), by="caseoh-export")
        self.assertEqual([x["name"] for x in L.capcut_store_users()], ["capcut-export"])

    def test_the_shared_lease_folder_is_used_only_where_it_exists(self):
        # A copy of gpu_lease.py in a temporary layout: create-clips without data/gpu is not written into.
        import shutil
        root = Path(tempfile.mkdtemp(prefix="lease-layout-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "static-studio" / "scripts").mkdir(parents=True)
        (root / "create-clips").mkdir()
        shutil.copy(SCRIPTS / "gpu_lease.py", root / "static-studio" / "scripts" / "gpu_lease.py")
        spec = importlib.util.spec_from_file_location("gpu_lease_layout_t", root / "static-studio" / "scripts" / "gpu_lease.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        self.assertEqual(m.default_lease_dir(), root / "static-studio" / "data" / "gpu")
        (root / "create-clips" / "data" / "gpu").mkdir(parents=True)
        self.assertEqual(m.default_lease_dir(), root / "create-clips" / "data" / "gpu")

    def test_a_lease_that_cannot_be_written_never_stops_the_job(self):
        blocker = self.root / "a-file"
        blocker.write_text("x", encoding="utf-8")
        with mock.patch.dict(os.environ, {L.LEASE_DIR_ENV: str(blocker / "gpu")}):
            lease = L.acquire("flux", need_mb=7168, wait_s=30)
        self.assertFalse(lease.held)
        self.assertIn("could not be written", lease.info["why"])
        self.assertIn("going ahead on the GPU without one", self.err.getvalue())
        lease.release()

    def test_the_shared_reader_sees_our_lease_and_its_recorder_yields_to_it(self):
        if not (CC_SCRIPTS / "cc_crypto_loader.py").is_file():
            self.skipTest(f"no other reader of the lease files on this PC ({CC_SCRIPTS})")
        lease = L.acquire("flux", need_mb=7168, note="flux3-image-klein-int8: 1 image(s), 1216x2160")
        self.addCleanup(lease.release)
        ended = self.dead_pid()
        self.pids.add(ended.pid)
        self.put(f"create-video-music-{ended.pid}", pid=ended.pid, need_mb=8000)    # a holder that has ended
        self.put("create-video-whisper-1", t=time.time() - 3600, need_mb=2200)      # past its time-to-live

        def read(free):
            cp = subprocess.run([sys.executable, "-B", "-c", READER, str(CC_SCRIPTS), str(self.dir), str(free)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                                env=dict(os.environ))
            self.assertEqual(cp.returncode, 0, cp.stderr[-2000:])
            res = json.loads(cp.stdout.strip().splitlines()[-1])
            if "skip" in res:
                self.skipTest("the other reader cannot be imported here: " + res["skip"])
            return res
        res = read(3000)
        self.assertEqual([x["name"] for x in res["leases"]], [lease.name])          # ours is a lease to it, the stale ones not
        self.assertEqual(res["leases"][0], self.read(Path(lease.info["file"])))
        self.assertEqual(res["unload_reason"], f"{lease.name} needs 7168 MB of GPU memory (3000 MB free)")   # its Whisper goes
        self.assertIsNone(read(9000)["unload_reason"])                               # room for both: its Whisper stays

    def test_the_workers_hold_the_lease_for_their_model_work(self):
        iw = load("image_worker_gpu_lease_t", "image_worker.py")

        class Proc:
            returncode = 0

            def poll(self):
                return 0

        class Stuck(Proc):
            def poll(self):
                return None

            def terminate(self):
                raise OSError("access denied")
        fake = types.SimpleNamespace(Popen=lambda *a, **k: Proc(), STDOUT=subprocess.STDOUT, DEVNULL=subprocess.DEVNULL,
                                     CREATE_NO_WINDOW=0, TimeoutExpired=subprocess.TimeoutExpired)
        terms = {"need_mb": None, "reserve_gb": 5, "wait_s": 0, "note": "a test still"}
        with mock.patch.object(iw, "subprocess", fake):
            # start() takes the lease before ComfyUI starts (the card less the 5 GB ComfyUI holds back); stop() lets it go
            proc, log = iw.start(self.root / "ComfyUI", self.root / "w1", 1, ["--reserve-vram", "5"], gpu=terms)
            rec = self.read(self.file_of("flux"))
            self.assertEqual((rec["need_mb"], rec["note"]), (CARD - 5 * 1024, "a test still"))
            iw.stop(proc, log)
            self.assertFalse(self.file_of("flux").exists())
            # ... also when stopping ComfyUI fails
            proc, log = iw.start(self.root / "ComfyUI", self.root / "w2", 1, [], gpu=terms)
            with self.assertRaises(OSError):
                iw.stop(Stuck(), log)
            log.close()
            self.assertFalse(self.file_of("flux").exists())
            # a check job's probe starts ComfyUI without a model: no lease
            proc, log = iw.start(self.root / "ComfyUI", self.root / "w3", 1)
            self.assertEqual(list(self.dir.glob("lease-*.json")), [])
            iw.stop(proc, log)
        # op_generate hands start() the lease's terms (none when ComfyUI runs on the CPU)
        root = self.root / "comfy"
        for sub, name in iw.MODELS.values():
            f = root / "ComfyUI" / "models" / sub / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"0" * 64)
        seen = []

        def fake_start(comfy, work, port, extra=(), gpu=None):
            seen.append(gpu)
            raise RuntimeError("stopped before ComfyUI")
        job = {"op": "generate", "root": str(root), "gpu_wait_s": 7,
               "images": [{"prompt": "a valley at dawn", "out": str(self.root / "x.png"), "width": 1216, "height": 2160}]}
        with mock.patch.object(iw, "start", side_effect=fake_start):
            for args in ([], ["--cpu"]):
                with self.assertRaises(RuntimeError):
                    iw.op_generate({**job, "comfy_args": args})
        self.assertEqual(seen, [{"need_mb": None, "reserve_gb": 5, "wait_s": 7,
                                 "note": "flux3-image-klein-int8: 1 image(s), 1216x2160",
                                 "expected_s": round(iw.flux_expected_s([{"width": 1216, "height": 2160}]), 1)}, None])
        # music_worker: the lease is held while the models load and play, and let go however that ends
        mw = load("music_worker_gpu_lease_t", "music_worker.py")
        inside = []

        def generate(job):
            inside.append(self.file_of("music").is_file())
            return {"ok": True, "made": [], "failed": []}

        def failing(job):
            raise RuntimeError("ACE-Step failed")
        with mock.patch.object(mw, "_generate", side_effect=generate):
            res = mw.op_generate({"tracks": [{}], "gpu_wait_s": 0})
        self.assertEqual(inside, [True])
        self.assertEqual((res["gpu_lease"]["held"], res["gpu_lease"]["need_mb"]), (True, 8000))
        self.assertFalse(self.file_of("music").exists())
        with mock.patch.object(mw, "_generate", side_effect=failing):
            with self.assertRaises(RuntimeError):
                mw.op_generate({"tracks": [], "gpu_wait_s": 0})
        self.assertFalse(self.file_of("music").exists())
        inside.clear()
        with mock.patch.object(mw, "_generate", side_effect=generate):
            res = mw.op_generate({"tracks": [], "device": "cpu"})
        self.assertEqual((inside, res["gpu_lease"]["held"]), ([False], False))      # a job on the CPU holds none


if __name__ == "__main__":
    unittest.main()
