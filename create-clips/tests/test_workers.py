"""Test of the two processors of `cc.py watch` (a live one on the newest chunk, a backlog one on the oldest).

    python tests/test_workers.py

Checks the assignment rule (live = the newest ready chunk, backlog = the oldest, one chunk goes to the first free processor), then runs the real watcher on
six short chunks (ffmpeg test pictures, the tiny Whisper model with its voice filter off so the decoder really runs): both processors must work at the same time
(never more than two), the live one must start on the NEWEST chunk and the backlog one on the OLDEST, every chunk's rec start must be the sum of the durations before
it with nothing made twice (no chunk flagged stale, no "rec start moved" line), and with `--workers 1` the chunks must come in number order. One Whisper model must
be loaded once however many threads ask for it.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
CC = SCRIPTS / "cc.py"
PY = sys.executable
sys.path.insert(0, str(SCRIPTS))


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def max_overlap(procs: list) -> int:
    ev = sorted([(p["started"], 1) for p in procs] + [(p["ended"], -1) for p in procs], key=lambda e: (e[0], e[1]))
    cur = best = 0
    for _, d in ev:
        cur += d
        best = max(best, cur)
    return best


def main():
    import cc_proc as P

    # ---- the assignment rule
    r = [{"index": i} for i in range(1, 7)]
    got = P._assign(list(r), ["live", "backlog"])
    check([c["index"] for c in got] == [6, 1], "two free processors, six ready chunks: the live one takes the newest (6), the backlog one the oldest (1)")
    rest = list(r)
    P._assign(rest, ["live", "backlog"])
    check([c["index"] for c in rest] == [2, 3, 4, 5], "the chunks taken leave the list, the others stay in order")
    check([c["index"] for c in P._assign([{"index": 7}], ["live", "backlog"])] == [7] and [c["index"] for c in P._assign([{"index": 7}], ["backlog", "live"])] == [7], "one ready chunk: the first free processor takes it")
    check([c["index"] for c in P._assign(list(r), ["backlog"])] == [1], "a lone backlog processor (--workers 1) takes the oldest: chunks in number order")
    check([c["index"] for c in P._assign(list(r), ["live"])] == [6] and P._assign([], ["live", "backlog"]) == [], "a lone live processor takes the newest; nothing ready, nothing taken")
    check(P._roles(1) == ["backlog"] and P._roles(2) == ["live", "backlog"] and P._roles(3) == ["live", "backlog", "backlog"], "the roles: 1 = backlog only, 2 = live + backlog, 3 = live + two backlog")

    class A:
        workers = None
    os.environ.pop("CC_WORKERS", None)
    check(P._worker_count(A) == 2, "the default is two processors (config watch.workers)")
    a = A()
    a.workers = 9
    check(P._worker_count(a) == 4, "never more than four")
    a.workers = 1
    check(P._worker_count(a) == 1, "--workers 1 gives one")

    # ---- one Whisper model, loaded once however many threads ask
    os.environ["CC_WHISPER_MODEL"] = "tiny"
    import cc_audio
    import faster_whisper
    calls = []
    orig = faster_whisper.WhisperModel

    def counting(*a_, **k):
        calls.append(k.get("num_workers"))
        time.sleep(0.3)                                  # a slow load: the second thread arrives while the first is still loading
        return orig(*a_, **k)
    faster_whisper.WhisperModel = counting
    try:
        cc_audio.configure_workers(2)
        cc_audio._TRANSCRIBERS.clear()
        t = cc_audio.get_transcriber({})
        th = [threading.Thread(target=t.load) for _ in range(4)]
        [x.start() for x in th]
        [x.join() for x in th]
        check(len(calls) == 1 and calls[0] == 2 and t.model is not None and t.used.get("num_workers") == 2, f"four threads, one model load, asked to run two transcriptions at once {calls}")
        check(cc_audio.get_transcriber({}) is t and cc_audio.get_transcriber({"language": "de"}) is not t, "the same run settings share one transcriber, other settings get their own")
        check(cc_audio.unload_transcriber() is True and t.model is None and cc_audio.unload_transcriber() is False, "an idle unload frees the model once")
    finally:
        faster_whisper.WhisperModel = orig
        cc_audio.configure_workers(1)
        cc_audio._TRANSCRIBERS.clear()

    # ---- the real watcher on six chunks
    if not shutil.which("ffmpeg"):
        print("skip the watcher check (ffmpeg not on PATH)")
        print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
        sys.exit(1 if check.failed else 0)
    tmp = Path(tempfile.mkdtemp(prefix="cc-workers-test-"))
    try:
        cfg = json.loads((HERE.parent / "config.json").read_text(encoding="utf-8"))
        cfg["whisper"].update({"model": "tiny", "vad_filter": False, "idle_unload_s": 0, "language": "en"})
        cfg["notify"]["enabled"] = False
        (tmp / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        inbox, runs = tmp / "inbox", tmp / "runs"
        env = {**os.environ, "CC_CONFIG": str(tmp / "config.json"), "CC_RUNS_ROOT": str(runs), "CC_INBOX": str(inbox), "CC_REPORT": "0", "CC_NOTIFY": "0", "CC_WHISPER_MODEL": "tiny"}
        env.pop("CC_WORKERS", None)

        def make_session(ses: str, durs: list) -> Path:
            sd = inbox / "wk" / ses
            sd.mkdir(parents=True)
            for i, d in enumerate(durs, start=1):
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=15", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                                "-t", str(d), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", str(sd / f"chunk-{i:04d}.mp4")], check=True)
                (sd / f"chunk-{i:04d}.json").write_text(json.dumps({"schema": "tcr/1", "channel": "wk", "session": ses, "chunk": i, "file": f"chunk-{i:04d}.mp4", "t0_utc": "2026-11-13T01:00:00.000Z",
                                                                    "t1_utc": "2026-11-13T01:00:05.000Z", "duration_s": float(d), "segments": 2, "bytes": 1, "quality": {"name": "360p", "width": 640, "height": 360, "fps": 15},
                                                                    "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "duration", "stream": {"id": "1", "title": "t", "game": "g", "viewers": 1,
                                                                                                                                         "uptime_s": 1, "started_at": "2026-11-13T01:00:00.000Z"}}), encoding="utf-8")
            return sd

        def watch(*extra):
            cp = subprocess.run([PY, str(CC), "watch", "--once", "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1", *extra], capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env, timeout=900)
            last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
            return (json.loads(last[-1]) if last else {"ok": False}), cp.stderr

        durs = [3.0, 3.5, 4.0, 3.2, 3.8, 3.4]
        ses = "20261113-030000-wk"
        make_session(ses, durs)
        j, err = watch()
        procs = j.get("processed", [])
        run = runs / ses
        rows = json.loads((run / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        check(j.get("ok") and j.get("processors") == ["live", "backlog"] and len(procs) == 6 and all(p["status"] == "done" for p in procs), "six chunks, two processors, all done " + json.dumps({k: j.get(k) for k in ("ok", "processors")}) + " " + str([(p["chunk"], p["status"], p["processor"]) for p in procs]))
        by_start = sorted(procs, key=lambda p: p["started"])
        first_two = {p["processor"]: p["chunk"] for p in by_start[:2]}
        check(first_two == {"live": "C0006", "backlog": "C0001"} and abs(by_start[0]["started"] - by_start[1]["started"]) < 2.0,
              f"at the start the live processor took the newest chunk (C0006) and the backlog processor the oldest (C0001), both at once {first_two}")
        check(max_overlap(procs) == 2, f"two chunks were processed at the same time, never more than two (overlap {max_overlap(procs)})")
        starts = []
        t = 0.0
        for d in durs:
            starts.append(round(t, 3))
            t += d
        real = [r["duration_s"] for r in rows]
        t, exp = 0.0, []
        for d in real:
            exp.append(round(t, 3))
            t += d
        check([r["rec_start_s"] for r in rows] == exp and all(abs(r["rec_start_s"] - s) < 0.5 for r, s in zip(rows, starts)), "every chunk's rec start is the sum of the real durations before it " + str([r["rec_start_s"] for r in rows]))
        check(not any(r["stale_rec"] for r in rows) and "rec start moved" not in err, "nothing was flagged stale and nothing was made twice (the durations were known before the newest chunk started)")
        fj_ok = all(abs(json.loads((run / "10-media" / r["id"] / "frames.json").read_text(encoding="utf-8"))["rec_start_s"] - r["rec_start_s"]) < 1e-3 for r in rows)
        check(fj_ok and all(r["status"] == "done" and all(v is True for v in r["stages"].values()) for r in rows), "every chunk's sheets carry the table's rec start and every stage is done")
        check(all(len(list((run / "10-media" / r["id"] / "sheets").glob("sheet-*.jpg"))) >= 1 and (run / "10-media" / r["id"] / "transcript.json").is_file() for r in rows), "every chunk has its sheets and its transcript (the model transcribed on both processors)")
        check(not list((inbox / "wk" / ses).glob("chunk-*.mp4")), "the inbox is empty of chunk files afterwards")

        # ---- one processor: in number order
        ses1 = "20261113-040000-wk"
        make_session(ses1, [3.0, 3.0, 3.0, 3.0])
        j, err = watch("--workers", "1")
        procs = [p for p in j.get("processed", []) if p["session"] == ses1]
        check(j.get("processors") == ["backlog"] and [p["chunk"] for p in procs] == ["C0001", "C0002", "C0003", "C0004"] and max_overlap(procs) == 1,
              "--workers 1: one at a time, in number order " + str([(p["chunk"], p["processor"]) for p in procs]))
        rows1 = json.loads((runs / ses1 / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        check(not any(r["stale_rec"] for r in rows1) and [r["status"] for r in rows1] == ["done"] * 4, "and nothing stale")

        # ---- a late lower chunk: the other processor re-makes the stale one while the first works on the late one
        ses2 = "20261113-050000-wk"
        sd2 = make_session(ses2, [3.0, 3.0, 3.0])
        for f in sd2.glob("chunk-0001.*"):
            f.rename(f.with_name(f.name + ".held"))
        j, err = watch()
        rows2 = json.loads((runs / ses2 / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        check([r["id"] for r in rows2] == ["C0002", "C0003"] and rows2[0]["rec_start_s"] == 0.0, "chunk 1 not there yet: chunks 2 and 3 were made from rec 0")
        for f in sd2.glob("chunk-0001.*.held"):
            f.rename(f.with_name(f.name[:-5]))
        j, err = watch()
        rows2 = json.loads((runs / ses2 / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
        d1 = rows2[0]["duration_s"]
        check([r["id"] for r in rows2] == ["C0001", "C0002", "C0003"] and abs(rows2[1]["rec_start_s"] - d1) < 1e-3 and not any(r["stale_rec"] for r in rows2)
              and all(abs(json.loads((runs / ses2 / "10-media" / r["id"] / "frames.json").read_text(encoding="utf-8"))["rec_start_s"] - r["rec_start_s"]) < 1e-3 for r in rows2),
              "chunk 1 arrived late: chunks 2 and 3 were re-made with their new rec starts, nothing is left stale " + str([(r["id"], r["rec_start_s"], r["stale_rec"]) for r in rows2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
