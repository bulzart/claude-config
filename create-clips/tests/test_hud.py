"""Regression test of cc_hud.py (hud-read, hud-scan, region-series) on synthetic game-HUD runs (no network, nothing outside a temp folder).

    python tests/test_hud.py            (Python312 with rapidocr-onnxruntime, numpy, Pillow; ffmpeg on PATH; about a minute)
    python tests/test_hud.py --long     also times a 3-minute 1080p60 chunk (adds about two minutes; the numbers in docs/hud.md come from it)

Run A: two 20 s 1280x720 chunks, a HUD drawn with Pillow: a clock counting down (1:55 at rec 0, one chunk boundary at rec 20), a left score that goes
7 -> 8 at rec 15, a right score that stays 5, a bright banner at rec 8-10 and 24-26, a moving square and a quiet corner.
Run B: one 30 s 1920x1080 chunk of the same HUD for the speed numbers. Then the error cases (bad region, empty range, missing OCR library, bad spec).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "scripts" / "cc.py"
PY = sys.executable

R_CLOCK = (0.44, 0.03, 0.12, 0.07)
R_LEFT = (0.30, 0.03, 0.05, 0.07)
R_RIGHT = (0.65, 0.03, 0.05, 0.07)
R_BANNER = (0.30, 0.80, 0.40, 0.10)
R_QUIET = (0.85, 0.30, 0.10, 0.10)
BANNERS = [(8, 10), (24, 26)]
CLOCK_START = 115


def reg(r):
    return ",".join(str(v) for v in r)


def cc(*args, env=None, timeout=900):
    t = time.time()
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=timeout)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    res = json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}
    res["_rc"], res["_wall"] = cp.returncode, round(time.time() - t, 2)
    return res


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


# --------------------------------------------------------------------------- synthetic video

def font(size):
    from PIL import ImageFont
    for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def clock_text(rec):
    s = CLOCK_START - int(rec)
    return f"{s // 60}:{s % 60:02d}"


def frame_bytes(W, H, rec, cache):
    """The HUD at rec time `rec` as raw rgb24 bytes (frames that look the same are made once)."""
    from PIL import Image, ImageDraw
    banner = any(a <= rec < b for a, b in BANNERS)
    key = (int(rec), 7 if rec < 15 else 8, banner, int(rec * 2) % 4)
    if key in cache:
        return cache[key]
    im = Image.new("RGB", (W, H), (24, 28, 34))
    d = ImageDraw.Draw(im)

    def rect(r):
        return r[0] * W, r[1] * H, (r[0] + r[2]) * W, (r[1] + r[3]) * H

    def centre(r, text, f):
        x0, y0, x1, y1 = rect(r)
        l, t, rr, b = d.textbbox((0, 0), text, font=f)
        d.text(((x0 + x1 - (rr - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), text, font=f, fill=(238, 238, 238))
    centre(R_CLOCK, clock_text(rec), font(int(0.045 * H)))
    centre(R_LEFT, str(key[1]), font(int(0.05 * H)))
    centre(R_RIGHT, "5", font(int(0.05 * H)))
    if banner:
        d.rectangle(rect(R_BANNER), fill=(240, 240, 240))
    x0 = int(0.02 * W) + key[3] * int(0.02 * W)
    d.rectangle((x0, int(0.82 * H), x0 + int(0.05 * W), int(0.92 * H)), fill=(200, 60, 40))
    cache[key] = im.tobytes()
    return cache[key]


def make_chunk(path, W, H, fps, seconds, rec_offset):
    path.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-g", str(fps * 2), "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    cache = {}
    for i in range(int(seconds * fps)):
        p.stdin.write(frame_bytes(W, H, rec_offset + i / fps, cache))
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg could not make the test chunk")


def make_run(root, name, W, H, fps, chunks, probe=False):
    run = root / "runs" / name
    rows, t = [], 0.0
    for n, dur in enumerate(chunks, 1):
        make_chunk(run / "10-media" / f"C{n:04d}" / "chunk.mp4", W, H, fps, dur, t)
        if probe:
            (run / "10-media" / f"C{n:04d}" / "probe.json").write_text(json.dumps({"width": W, "height": H}), encoding="utf-8")
        rows.append({"id": f"C{n:04d}", "index": n, "rec_start_s": t, "duration_s": float(dur), "status": "done"})
        t += dur
    (run / "00-inventory").mkdir(parents=True, exist_ok=True)
    (run / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")
    (run / "state.json").write_text('{"schema":"cc/1","channel":"hudtest"}', encoding="utf-8")
    return run


def rows_of(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["rows"]


# --------------------------------------------------------------------------- the tests

def main():
    from PIL import Image
    import numpy as np
    long_run = "--long" in sys.argv
    tmp = Path(tempfile.mkdtemp(prefix="cc-hud-test-"))
    try:
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs")}
        t = time.time()
        run = make_run(tmp, "20261112-000000-hudA", 1280, 720, 10, [20, 20])
        print(f"built run A in {time.time() - t:.1f} s")

        # ---- hud-read
        r = cc("hud-read", "--run", run, "--at", 5, "--region", reg(R_CLOCK), "--numeric", env=env)
        check(r.get("ok") and r["text"] == clock_text(5) and r.get("value") == CLOCK_START - 5, f"hud-read: clock at rec 5 reads {r.get('text')!r} value {r.get('value')} (want {clock_text(5)})")
        check(r.get("ok") and r["chunk"] == "C0001" and Path(r["image"]).is_file() and r["confidence"] > 0.5, "hud-read: names the chunk, keeps the cropped image, gives a confidence")
        if r.get("ok"):
            with Image.open(r["image"]) as im:          # closed again: an open file would stop the temp folder from being deleted on Windows
                check(im.size[0] > 2 * im.size[1] > 100, f"hud-read: the image is the enlarged crop {im.size}")
        r2 = cc("hud-read", "--run", run, "--at", "C0002+0.5", "--region", reg(R_CLOCK), "--threshold", 128, "--invert", "--numeric", env=env)
        check(r2.get("ok") and r2["chunk"] == "C0002" and r2["text"] == clock_text(20.5) and r2.get("value") == CLOCK_START - 20,
              f"hud-read: chunk time C0002+0.5 with --threshold --invert reads {r2.get('text')!r}")
        if r2.get("ok"):
            with Image.open(r2["image"]) as im2:
                check(float(np.asarray(im2).mean()) > 128, "hud-read: --invert gives dark text on a light crop")
        r3 = cc("hud-read", "--run", run, "--at", 16, "--region", reg(R_LEFT), "--regex", r"^\d{1,2}$", env=env)
        check(r3.get("ok") and r3["text"] == "8", f"hud-read: left score at rec 16 = {r3.get('text')!r} (regex kept)")
        r4 = cc("hud-read", "--run", run, "--at", 5, "--region", reg(R_CLOCK), "--kind", "text", env=env)
        check(r4.get("ok") and r4["text"] == clock_text(5) and r4["boxes"], f"hud-read: kind text (detect + recognise) reads {r4.get('text')!r} with a box")
        check(r.get("method") == "rec" and r4.get("method") == "det+rec", f"hud-read: says how it read (digits {r.get('method')}, text {r4.get('method')})")

        r5 = cc("hud-read", "--run", run, "--at", 5, "--region", reg(R_QUIET), "--numeric", env=env)
        check(r5.get("ok") and r5["text"] == "" and r5["confidence"] == 0 and r5.get("value") is None, "hud-read: a blank region reads as empty text, no invented digit")
        r6 = cc("hud-read", "--run", run, "--at", 5, "--region", reg(R_CLOCK), "--threshold", 128, "--scale", 2, env=env)
        check(r6.get("ok") and r6["image"] != r["image"] and r6["image"].endswith("-t128-s2.png"), "hud-read: the image name carries the options, so two tries keep two images")

        # ---- hud-scan, one region
        r = cc("hud-scan", "--run", run, "--region", reg(R_CLOCK), "--name", "clock", "--step", 1, "--numeric", "--regex", r"\d{1,2}:\d{2}", env=env)
        check(r.get("ok") and r["samples"] == 40 and r["recorded_s"] == 40 and r["holes_s"] == 0, "hud-scan: 40 samples over two chunks")
        rd = r["readers"][0] if r.get("ok") else {}
        rows = rows_of(rd["files"][0]) if rd else []
        check([x["rec"] for x in rows] == [float(k) for k in range(40)], "hud-scan: the sample grid runs on across the chunk boundary (rec 0..39)")
        check(all(x["chunk"] == ("C0001" if x["rec"] < 20 else "C0002") for x in rows) and rows[20]["t_chunk"] == 0 and rows[19]["t_chunk"] == 19, "hud-scan: chunk and chunk time of each sample")
        right = sum(1 for x in rows if x["text"] == clock_text(x["rec"]) and x.get("value") == CLOCK_START - int(x["rec"]))
        check(right >= 38, f"hud-scan: the clock is read right in {right} of 40 samples" + ("" if right >= 38 else " " + json.dumps([(x['rec'], x['text']) for x in rows if x['text'] != clock_text(x['rec'])][:6])))
        txt = Path(rd["files"][1]).read_text(encoding="utf-8").splitlines() if rd else []
        check(len(txt) >= 38 and txt[0].endswith("  " + clock_text(0)), f"hud-scan: the .txt lists the text changes ({len(txt)} lines)")
        summary = json.loads(Path(rd["files"][0]).read_text(encoding="utf-8"))["summary"] if rd else {}
        check(summary.get("samples") == 40 and summary.get("ocr_calls", 99) <= 40, "hud-scan: summary at the end of the json")

        # ---- hud-scan, several regions in one pass (the spec), score regions
        spec = tmp / "spec.json"
        spec.write_text(json.dumps([{"name": "banner", "region": list(R_BANNER), "kind": "text"},      # taller than the others: the crops are padded to it
                                    {"name": "left", "region": list(R_LEFT), "regex": r"^\d{1,2}$", "numeric": True},
                                    {"name": "right", "region": list(R_RIGHT), "regex": r"^\d{1,2}$", "numeric": True},
                                    {"name": "clock2", "region": list(R_CLOCK), "regex": r"\d{1,2}:\d{2}", "numeric": True}]), encoding="utf-8")
        r = cc("hud-scan", "--run", run, "--spec", spec, "--step", 1, env=env)
        check(r.get("ok") and [x["name"] for x in r["readers"]] == ["banner", "left", "right", "clock2"], "hud-scan --spec: four regions of different heights read in one pass")
        if r.get("ok"):
            banner, left, right_, clock2 = r["readers"]
            check(banner["changes"] == 0 and all(x["text"] == "" for x in rows_of(banner["files"][0])), "a plain bright or dark box reads as empty text")
            lrows = rows_of(left["files"][0])
            check(sum(1 for x in lrows if x["text"] == ("7" if x["rec"] < 15 else "8")) >= 39, "left score reads 7, then 8 from rec 15")
            check(left["changes"] == 1 and left["changes_first"] and left["changes_first"][0][0] == 15.0 and left["changes_first"][0][1:] == ["7", "8"], f"left score: one change at rec 15.0 ({left['changes_first']})")
            check(left["reused"] >= 30 and left["ocr_calls"] <= 10, f"left score: a still region is not read again (ocr_calls {left['ocr_calls']}, reused {left['reused']})")
            check(right_["changes"] == 0 and all(x["text"] == "5" and x["value"] == 5 for x in rows_of(right_["files"][0])), "right score stays 5 (value 5)")
            same = [(x["rec"], x["text"]) for x in rows_of(clock2["files"][0])] == [(x["rec"], x["text"]) for x in rows]
            check(same, "the clock read in the three-region pass equals the clock read alone")

        # ---- --from / --to: a grid that starts off the chunk boundary
        r = cc("hud-scan", "--run", run, "--region", reg(R_CLOCK), "--name", "clockslice", "--from", 18.5, "--to", 22, "--step", 1, "--numeric", env=env)
        sl = rows_of(r["readers"][0]["files"][0]) if r.get("ok") else []
        check([x["rec"] for x in sl] == [18.5, 19.5, 20.5, 21.5] and [x["chunk"] for x in sl] == ["C0001", "C0001", "C0002", "C0002"] and [x["t_chunk"] for x in sl] == [18.5, 19.5, 0.5, 1.5],
              f"--from 18.5 --to 22: samples {[(x['rec'], x['chunk'], x['t_chunk']) for x in sl]}")
        check([x["value"] for x in sl] == [CLOCK_START - 18, CLOCK_START - 19, CLOCK_START - 20, CLOCK_START - 21], f"--from 18.5 --to 22: the clock values {[x['value'] for x in sl]}")

        # ---- region-series
        r = cc("region-series", "--run", run, "--region", reg(R_BANNER), "--region", reg(R_QUIET), "--name", "bn", "--step", 0.5, env=env)
        check(r.get("ok") and r["samples"] == 80 and r["regions"] == 2, "region-series: 80 samples of two regions")
        if r.get("ok"):
            top = sorted(r["per_region"][0]["top30_by_diff_in_time_order"], key=lambda x: -x[1])[:4]
            check(sorted(x[0] for x in top) == [8.0, 10.0, 24.0, 26.0] and all(x[1] > 150 for x in top), f"banner region: the four biggest changes are the banner edges {[(x[0], x[1]) for x in top]}")
            quiet = max(x[1] for x in r["per_region"][1]["top30_by_diff_in_time_order"])
            check(quiet < 3, f"quiet region: the biggest change is {quiet}")
            srows = rows_of(r["files"][0])
            check(srows[0]["v"][0][4] is None and srows[17]["v"][0][3] > 200 and srows[15]["v"][0][3] < 60, "region-series: luma of the banner is high at rec 8.5 and low at rec 7.5, the first diff is null")
            check(Path(r["files"][1]).read_text(encoding="utf-8").count("diff") >= 8, "region-series: the .txt lists the biggest changes")
            check(abs(r["per_region"][0]["percentiles"]["p50"]) < 3, "region-series: percentiles of the diff are given")

        # ---- run B: 1080p, speed
        t = time.time()
        runb = make_run(tmp, "20261112-000001-hudB", 1920, 1080, 5, [30], probe=True)
        print(f"built run B in {time.time() - t:.1f} s")
        one = cc("hud-scan", "--run", runb, "--region", reg(R_CLOCK), "--name", "clock", "--step", 0.5, "--numeric", env=env)
        check(one.get("ok") and one["samples"] == 60, "1080p: 60 samples read")
        if one.get("ok"):
            rd = one["readers"][0]
            check(rd["reused"] >= 25, f"1080p: half of the samples are the same second, not read again (ocr_calls {rd['ocr_calls']}, reused {rd['reused']})")
            print(f"     1080p hud-scan one region, 60 samples at 0.5 s: {one['seconds']} s total, OCR {rd['ocr_seconds']} s ({rd['ocr_calls']} reads)")
            check(one["seconds"] < 40, "1080p: one region over 30 s of video in under 40 s")
        every = cc("hud-scan", "--run", runb, "--region", reg(R_CLOCK), "--name", "clockall", "--step", 0.5, "--idle-frac", 0, env=env)
        if every.get("ok"):
            print(f"     1080p hud-scan, --idle-frac 0 (every sample read): {every['seconds']} s, {every['readers'][0]['ocr_calls']} reads")
            check(every["readers"][0]["ocr_calls"] == 60 and every["readers"][0]["reused"] == 0, "--idle-frac 0 reads every sample")
        multi = cc("hud-scan", "--run", runb, "--spec", spec, "--step", 0.5, env=env)
        if multi.get("ok") and one.get("ok"):
            print(f"     1080p hud-scan four regions in one pass: {multi['seconds']} s (one region: {one['seconds']} s)")
            check(multi["seconds"] < 3 * one["seconds"], "four regions in one pass cost less than three single passes")
        rs = cc("region-series", "--run", runb, "--region", reg(R_BANNER), "--region", reg(R_QUIET), "--region", reg(R_CLOCK), "--name", "b", "--step", 0.25, env=env)
        if rs.get("ok"):
            print(f"     1080p region-series, 3 regions, 120 samples at 0.25 s: {rs['seconds']} s")
            check(rs["samples"] == 120 and rs["seconds"] < 40, "1080p: region-series, 3 regions, 120 samples in under 40 s")

        # ---- error cases
        r = cc("hud-read", "--run", run, "--at", 5, "--region", "0.9,0.9,0.3,0.3", env=env)
        check(not r["ok"] and "outside the frame" in r["error"], "error: a region outside the frame is refused with the reason")
        r = cc("hud-scan", "--run", run, "--region", "0.1,0.1,0.2", "--name", "x", env=env)
        check(not r["ok"] and "four numbers" in r["error"], "error: a region with three numbers")
        r = cc("hud-scan", "--run", run, "--region", reg(R_CLOCK), "--name", "x", "--from", 100000, "--to", 100010, env=env)
        check(not r["ok"] and "no recorded content" in r["error"], "error: a range outside the recording")
        r = cc("hud-read", "--run", run, "--at", 9999, "--region", reg(R_CLOCK), env=env)
        check(not r["ok"] and "not inside a recorded chunk" in r["error"], "error: a time outside the recording")
        r = cc("hud-scan", "--run", run, "--spec", tmp / "nope.json", env=env)
        check(not r["ok"] and "must be a JSON list" in r["error"], "error: a missing spec file")
        dup = tmp / "dup.json"
        dup.write_text(json.dumps([{"name": "a", "region": list(R_LEFT)}, {"name": "a", "region": list(R_RIGHT)}]), encoding="utf-8")
        r = cc("hud-scan", "--run", run, "--spec", dup, env=env)
        check(not r["ok"] and "used twice" in r["error"], "error: the same name twice in a spec")
        r = cc("hud-scan", "--run", run, "--region", reg(R_CLOCK), env=env)
        check(not r["ok"] and "--name" in r["error"], "error: no --name")
        r = cc("region-series", "--run", run, "--region", reg(R_BANNER), "--name", "x", "--size", "1x1", env=env)
        check(not r["ok"] and "--size" in r["error"], "error: a silly --size")
        left_parts = list((run / "20-analysis" / "hud").glob("*.part"))
        check(not left_parts, f"no .part files are left behind ({[p.name for p in left_parts]})")

        # the OCR library missing: the message says what to install, and a scan stopped by it leaves no half file
        def hooked(*args):
            code = "import sys; sys.modules['rapidocr_onnxruntime'] = None; sys.path.insert(0, r'%s'); import cc; cc.main(%r)" % (CC.parent, [str(x) for x in args])
            cp = subprocess.run([PY, "-c", code], capture_output=True, text=True, encoding="utf-8", env=env)
            last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
            return cp.returncode, (json.loads(last[-1]) if last else {})
        rc, j = hooked("hud-read", "--run", run, "--at", 5, "--region", reg(R_CLOCK))
        check(rc == 3 and not j.get("ok", True) and "pip install rapidocr-onnxruntime" in j.get("error", ""), "error: a missing rapidocr library gives the pip install line (exit 3)")
        rc, j = hooked("hud-scan", "--run", run, "--region", reg(R_CLOCK), "--name", "nolib", "--step", 1)
        hud = run / "20-analysis" / "hud"
        check(rc == 3 and "pip install" in j.get("error", "") and not list(hud.glob("*.part")) and not (hud / "nolib.json").exists(), "error: a scan stopped by the missing library leaves no file behind")

        if long_run:
            t = time.time()
            runc = tmp / "runs" / "20261112-000002-hudC"
            cdir = runc / "10-media" / "C0001"
            cdir.mkdir(parents=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=60", "-t", "180", "-c:v", "libx264",
                            "-preset", "veryfast", "-b:v", "6M", "-g", "120", "-pix_fmt", "yuv420p", str(cdir / "chunk.mp4")], check=True)
            (runc / "00-inventory").mkdir(parents=True)
            (runc / "00-inventory" / "chunks.json").write_text(json.dumps([{"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 180.0, "status": "done"}]), encoding="utf-8")
            (runc / "state.json").write_text("{}", encoding="utf-8")
            print(f"built the 3-minute 1080p60 chunk in {time.time() - t:.1f} s")
            a = cc("hud-scan", "--run", runc, "--region", "0.4,0.03,0.2,0.07", "--name", "c1", "--step", 1, env=env)
            print(f"     3 min 1080p60, hud-scan one region step 1 s: {a.get('seconds')} s ({a['readers'][0]['ocr_calls']} reads of {a['samples']})" if a.get("ok") else a)
            b = cc("hud-scan", "--run", runc, "--spec", spec, "--step", 1, env=env)
            print(f"     3 min 1080p60, hud-scan four regions step 1 s: {b.get('seconds')} s" if b.get("ok") else b)
            f = cc("hud-scan", "--run", runc, "--region", "0.4,0.03,0.2,0.07", "--name", "c1f", "--step", 1, "--fallback", env=env)
            print(f"     3 min 1080p60, the same with --fallback (detect + recognise on every unreadable sample): {f.get('seconds')} s" if f.get("ok") else f)
            c = cc("region-series", "--run", runc, "--region", "0.3,0.8,0.4,0.1", "--region", "0.85,0.3,0.1,0.1", "--name", "c", "--step", 0.5, env=env)
            print(f"     3 min 1080p60, region-series two regions step 0.5 s: {c.get('seconds')} s" if c.get("ok") else c)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
