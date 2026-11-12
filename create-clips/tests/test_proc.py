"""Tests of the chunk processing (cc_proc.py and its helpers). Plain python, no pytest:

    "C:\\Users\\Bulzart\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" tests\\test_proc.py [--fast] [--keep]

Builds its own test media with ffmpeg from a reference video (read-only) and a synthetic clip, runs the real commands in a temporary
runs root / inbox (CC_RUNS_ROOT, CC_INBOX) and checks what they write. --fast uses the tiny Whisper model for the big chunk too (the
default measures the real model: medium on the CPU, about two minutes). --keep leaves the temp folder.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
CC = SCRIPTS / "cc.py"
PY = sys.executable

FAST = "--fast" in sys.argv
KEEP = "--keep" in sys.argv
RESULTS = []
TIMINGS = {}


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail and not ok else (f"  ({detail})" if detail else "")), flush=True)
    return bool(ok)


def run_cc(args, env=None, timeout=1800):
    e = dict(os.environ)
    e.update(env or {})
    cp = subprocess.run([PY, str(CC), *[str(a) for a in args]], capture_output=True, text=True, encoding="utf-8", errors="replace", env=e,
                        timeout=timeout)
    last = None
    for line in reversed((cp.stdout or "").strip().splitlines()):
        if line.strip().startswith("{"):
            try:
                last = json.loads(line)
                break
            except ValueError:
                continue
    return cp.returncode, cp.stdout, cp.stderr, last


def ff(*args, timeout=600):
    cp = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *[str(a) for a in args]], capture_output=True, text=True,
                        timeout=timeout)
    if cp.returncode:
        raise RuntimeError(cp.stderr[-400:])


def probe_dur(p) -> float:
    cp = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    return float(cp.stdout.strip())


def find_reference() -> Path | None:
    env = os.environ.get("CC_TEST_VIDEO")
    if env and Path(env).is_file():
        return Path(env)
    root = Path(r"C:\Users\Bulzart\Documents\references")
    for p in sorted(root.glob("*.mp4")) if root.is_dir() else []:
        try:
            if probe_dur(p) >= 500:
                return p
        except Exception:  # noqa: BLE001
            continue
    return None


def make_sidecar(path: Path, channel: str, session: str, n: int, dur: float, t0: str, game="Just Chatting", gap=0, ads=0):
    side = {"schema": "tcr/1", "channel": channel, "session": session, "chunk": n, "file": f"chunk-{n:04d}.mp4", "t0_utc": t0, "t1_utc": t0,
            "duration_s": dur, "segments": int(dur / 2), "bytes": 1, "quality": {"name": "720p60", "width": 1280, "height": 720, "fps": 60,
                                                                                   "bandwidth": 3322199, "codecs": "avc1.4D401F,mp4a.40.2"},
            "gap_before_s": gap, "ads_skipped_s": ads, "ended_by": "duration",
            "stream": {"id": "1", "title": f"title of chunk {n}", "game": game, "viewers": 1000 + n, "uptime_s": 600 * n, "started_at": t0},
            "tool": {"name": "Twitch Chunk Recorder", "version": "1.0.0"}}
    path.write_text(json.dumps(side), encoding="utf-8")


def make_chat(path: Path, n: int, dur: int, peak_at: int):
    per = [(i * 7 + n) % 5 for i in range(dur)]
    for i in range(peak_at, min(dur, peak_at + 5)):
        per[i] = 45
    chat = {"schema": "tcr-chat/1", "chunk": n, "t0_utc": "2026-11-12T11:00:00.000Z", "duration_s": float(dur), "bin_s": 1, "lag_hint_s": 8,
            "per_second": per, "tokens_per_10s": [[["KEKW", 10 + b], ["LMAO", 5]] for b in range(math.ceil(dur / 10))],
            "samples": [{"t": float(peak_at), "text": "WTF LMAOOO"}]}
    path.write_text(json.dumps(chat), encoding="utf-8")


def expected_frames(dur: float, interval=0.75) -> int:
    return int(math.floor((dur - 0.01) / interval)) + 1


def label_distance(sheet_img, x0, y0, cw, ch, text) -> float:
    """Mean abs difference between the label strip text row under a cell and the same text drawn fresh (same font and place)."""
    from PIL import Image, ImageDraw
    import numpy as np
    from cc_sheets import TEXT_H, label_font
    crop = sheet_img.crop((x0, y0 + ch, x0 + cw, y0 + ch + TEXT_H)).convert("L")
    ref = Image.new("RGB", (cw, TEXT_H), (0, 0, 0))
    ImageDraw.Draw(ref).text((5, 0), text, fill=(245, 245, 245), font=label_font(cw))
    return float(np.abs(np.asarray(crop, dtype=np.int16) - np.asarray(ref.convert("L"), dtype=np.int16)).mean())


def check_sheet_labels(chunk_dir: Path, frames_json: dict, name: str):
    """Every cell's drawn label equals its frame's own timestamp (compared with the neighbour's label as a control)."""
    from PIL import Image
    from cc_sheets import HEAD_H, LABEL_H, cell_label
    cols, (cw, ch) = frames_json["cols"], frames_json["cell"]
    rec0 = frames_json["rec_start_s"]
    by_sheet = {}
    for fr in frames_json["frames"]:
        by_sheet.setdefault(fr["sheet"], []).append(fr)
    bad = []
    for sh, frs in by_sheet.items():
        img = Image.open(chunk_dir / "sheets" / f"sheet-{sh:02d}.jpg").convert("RGB")
        for j, fr in enumerate(frs):
            r, c = divmod(j, cols)
            x0, y0 = c * cw, HEAD_H + r * (ch + LABEL_H)
            own = label_distance(img, x0, y0, cw, ch, cell_label(rec0 + fr["t"], fr["t"]))
            other_t = frs[(j + 1) % len(frs)]["t"] if len(frs) > 1 else fr["t"] + 99
            other = label_distance(img, x0, y0, cw, ch, cell_label(rec0 + other_t, other_t))
            if not (own < 12 and own + 2 < other):
                bad.append((sh, j, round(own, 1), round(other, 1)))
    check(f"{name}: every cell label equals its frame's own time", not bad, f"{len(bad)} off, first {bad[:3]}")


def data_rows(md: Path) -> int:
    n = 0
    for ln in md.read_text(encoding="utf-8").splitlines():
        if ln.startswith("| ") and not ln.startswith("| rec") and not ln.startswith("|---"):
            n += 1
    return n


def main():
    ref = find_reference()
    tmp = Path(tempfile.mkdtemp(prefix="cc-proc-test-"))
    runs, inbox, data = tmp / "runs", tmp / "inbox", tmp / "data"
    for d in (runs, inbox, data):
        d.mkdir(parents=True)
    env = {"CC_RUNS_ROOT": str(runs), "CC_INBOX": str(inbox)}
    tiny = {**env, "CC_WHISPER_MODEL": "tiny"}
    print(f"test folder {tmp}; reference video: {ref}")
    t_all = time.time()
    try:
        # ---------------------------------------------------------------- media
        if ref:
            ff("-ss", 60, "-t", 179.95, "-i", ref, "-vf", "scale=1280:720,fps=60", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-g", 120,
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", 48000, "-ac", 2, "-movflags", "+faststart", data / "A.mp4")
            ff("-ss", 300, "-t", 20, "-i", ref, "-vf", "scale=1280:720,fps=60", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-g", 120,
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", 48000, "-ac", 2, data / "P1.mp4")
            ff("-ss", 330, "-t", 20, "-i", ref, "-vf", "scale=1280:720,fps=60", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-g", 120,
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", 48000, "-ac", 2, data / "P2.mp4")
            ff("-ss", 500, "-t", 10, "-i", ref, "-vf", "scale=1280:720,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-c:a", "aac", data / "short10.mp4")
            ff("-ss", 100, "-t", 20, "-i", ref, "-an", "-vf", "scale=1280:720,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               data / "noaudio.mp4")
            ff("-ss", 200, "-t", 10, "-i", ref, "-vf", "scale=720:1280,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-c:a", "aac", data / "portrait.mp4")
        # a synthetic 30 s clip whose brightness encodes its time (ramp 0..255 every 2 s), 60 fps, for the time-accuracy check
        ff("-f", "lavfi", "-i", "color=c=black:size=640x360:rate=60:duration=30,geq=lum='255*mod(T,2)/2':cb=128:cr=128",
           "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=48000:duration=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "6",
           "-pix_fmt", "yuv420p", "-g", 120, "-c:a", "aac", data / "ramp.mp4")
        corrupt = data / "corrupt.mp4"
        corrupt.write_bytes(os.urandom(20000))
        check("test media made", True)

        # ---------------------------------------------------------------- doctor
        rc, so, se, j = run_cc(["doctor"], env)
        check("doctor ok", j and j.get("ok"), json.dumps([c for c in (j or {}).get("checks", []) if not c["ok"] and c["hard"]]))

        # ---------------------------------------------------------------- new-run
        rc, so, se, j = run_cc(["new-run", "--channel", "Test_Chan", "--session", "20261112-120000-test_chan"], env)
        run_a = Path(j["run"]) if j else None
        check("new-run makes the folders", j and j["ok"] and all((run_a / d).is_dir() for d in
              ("00-inventory", "10-media", "20-analysis", "30-assets", "40-briefs", "60-outputs", "deliverables", "logs")) and (run_a / "state.json").is_file())

        # ---------------------------------------------------------------- chunk A (3 min) end to end
        if ref:
            sess_dir = inbox / "test_chan" / "20261112-120000-test_chan"
            sess_dir.mkdir(parents=True)
            shutil.copyfile(data / "A.mp4", sess_dir / "chunk-0001.mp4")
            make_sidecar(sess_dir / "chunk-0001.json", "test_chan", "20261112-120000-test_chan", 1, 180.0, "2026-11-12T11:00:00.000Z")
            make_chat(sess_dir / "chat-0001.json", 1, 180, 100)
            (sess_dir / "session.json").write_text(json.dumps({"schema": "tcr-session/1", "channel": "test_chan"}), encoding="utf-8")
            t0 = time.time()
            rc, so, se, j = run_cc(["ingest", "--chunk", sess_dir / "chunk-0001.mp4"], env if not FAST else tiny)
            wall = time.time() - t0
            check("ingest A: ok and every stage true", j and j["ok"] and all(v is True for v in j["stages"].values()), json.dumps(j)[:300])
            TIMINGS["A (180 s chunk, %s)" % ("tiny" if FAST else "medium")] = {**(j or {}).get("seconds", {}), "wall": round(wall, 1)}
            cdir = run_a / "10-media" / "C0001"
            dur = probe_dur(cdir / "chunk.mp4")
            n = expected_frames(dur)
            sheets = sorted((cdir / "sheets").glob("sheet-*.jpg"))
            check("chunk moved out of the inbox", not (sess_dir / "chunk-0001.mp4").exists() and (cdir / "chunk.mp4").is_file())
            check(f"A: {n} frames -> {math.ceil(n / 30)} sheets of 30 and an overview", len(sheets) == math.ceil(n / 30) and (cdir / "sheets" / "overview.jpg").is_file(),
                  f"{len(sheets)} sheets")
            fj = json.loads((cdir / "frames.json").read_text(encoding="utf-8"))
            check("A: frames.json has every frame, frames deleted, none left", len(fj["frames"]) == n and fj["frames_deleted"] and fj["leftover_frames"] == 0
                  and not (cdir / "frames").exists() and not list(cdir.glob("*.jpg")), f"{len(fj['frames'])} frames")
            check("A: frame times are i * 0.75", all(abs(f["t"] - f["i"] * 0.75) < 1e-6 for f in fj["frames"]))
            check("A: actual frame times match the intended ones (within one 60 fps frame)", all(f["t_pts"] is None or abs(f["t_pts"] - f["t"]) < 0.0175 for f in fj["frames"]),
                  str([f for f in fj["frames"] if f["t_pts"] is not None and abs(f["t_pts"] - f["t"]) >= 0.0175][:2]))
            check("A: cells carry loudness and chat numbers", all(f["rms_db"] is not None and f["chat_per_s"] is not None for f in fj["frames"]))
            check("A: diff_prev is null only for frame 0", fj["frames"][0]["diff_prev"] is None and all(f["diff_prev"] is not None for f in fj["frames"][1:]))
            check_sheet_labels(cdir, fj, "A")
            tr = json.loads((cdir / "transcript.json").read_text(encoding="utf-8"))
            words = [w for s in tr["segments"] for w in s["words"]]
            mono = all(words[i]["s"] <= words[i + 1]["s"] + 0.05 for i in range(len(words) - 1))
            check("A: transcript has words with sane, ordered times", len(words) > 100 and mono and all(0 <= w["s"] <= w["e"] <= dur + 1 for w in words),
                  f"{len(words)} words")
            check("A: transcript model/device recorded", tr["model"] == ("tiny" if FAST else "medium") and tr["device"] == "cpu" and tr["language"] == "en",
                  f"{tr.get('model')} {tr.get('device')} {tr.get('language')}")
            check("A: segments carry avg_logprob / no_speech_prob / compression_ratio", all(k in tr["segments"][0] for k in ("avg_logprob", "no_speech_prob", "compression_ratio")))
            check("A: timeline.md has one row per second", data_rows(cdir / "timeline.md") == math.ceil(dur), f"{data_rows(cdir / 'timeline.md')} rows")
            au = json.loads((cdir / "audio.json").read_text(encoding="utf-8"))
            check("A: audio.json windows", len(au["rms_db"]) == math.ceil(dur / 0.5) and au["window_s"] == 0.5)
            ap = json.loads((cdir / "audio-profile.json").read_text(encoding="utf-8"))
            check("A: audio-profile fields", all(k in ap for k in ("rms_mean_db", "rms_median_db", "rms_p90_db", "rms_max_db", "silence_share", "loud_jumps")))
            dg = json.loads((cdir / "digest.json").read_text(encoding="utf-8"))
            chat = json.loads((cdir / "chat.json").read_text(encoding="utf-8"))
            check("A: digest matches the chat file and the transcript", dg["chat_total"] == sum(chat["per_second"]) and dg["words"] == tr["n_words"]
                  and dg["game"] == "Just Chatting" and dg["title"] == "title of chunk 1", json.dumps(dg)[:200])
            check("A: wav deleted after the transcript", not (cdir / "audio-16k.wav").exists())
            rows = json.loads((run_a / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
            check("A: chunk table row", len(rows) == 1 and rows[0]["status"] == "done" and rows[0]["rec_start_s"] == 0 and rows[0]["quality"]["name"] == "720p60"
                  and rows[0]["frames"] == n and rows[0]["seconds"].get("transcript") is not None)
            st = json.loads((run_a / "state.json").read_text(encoding="utf-8"))
            check("A: state.json and stream files", st["chunks"]["C0001"]["status"] == "done" and (run_a / "00-inventory" / "stream.md").is_file()
                  and json.loads((run_a / "00-inventory" / "stream-meta.json").read_text(encoding="utf-8"))["per_chunk"][0]["game"] == "Just Chatting")
            # idempotent
            m0 = {p.name: p.stat().st_mtime_ns for p in (cdir / "sheets").glob("*.jpg")}
            rc, so, se, j2 = run_cc(["ingest", "--run", run_a, "--chunk", cdir / "chunk.mp4"], env if not FAST else tiny)
            m1 = {p.name: p.stat().st_mtime_ns for p in (cdir / "sheets").glob("*.jpg")}
            check("A: a second ingest does nothing", j2 and j2.get("already_done") and m0 == m1, json.dumps(j2)[:200])
            # a transcript-less run, then the later ingest makes it
            rc, so, se, j3 = run_cc(["status", "--run", run_a], env)
            check("status of a run", j3 and j3["ok"] and j3["by_status"] == {"done": 1} and j3["chunks"] == 1)
        else:
            check("reference video found (A tests skipped)", False, "set CC_TEST_VIDEO to a video longer than 500 s")

        # ---------------------------------------------------------------- the time-accuracy check: brightness encodes the frame's time
        rc, so, se, j = run_cc(["new-run", "--channel", "ramp", "--session", "20261112-130000-ramp"], env)
        run_r = Path(j["run"])
        sd = inbox / "ramp" / "20261112-130000-ramp"
        sd.mkdir(parents=True)
        shutil.copyfile(data / "ramp.mp4", sd / "chunk-0001.mp4")
        rc, so, se, j = run_cc(["ingest", "--run", run_r, "--chunk", sd / "chunk-0001.mp4", "--skip-whisper"], tiny)
        check("ramp: sheets made (transcript skipped on request)", j and j["stages"]["sheets"] is True and j["stages"]["transcript"] is False and j["status"] == "pending", json.dumps(j)[:240])
        cdir = run_r / "10-media" / "C0001"
        fj = json.loads((cdir / "frames.json").read_text(encoding="utf-8"))
        from PIL import Image
        import numpy as np
        from cc_sheets import HEAD_H, LABEL_H
        cols, (cw, ch) = fj["cols"], fj["cell"]
        worst = 0.0
        bad = []
        checked = 0
        for sh in sorted({f["sheet"] for f in fj["frames"]}):
            img = Image.open(cdir / "sheets" / f"sheet-{sh:02d}.jpg").convert("L")
            for j2, fr in enumerate([f for f in fj["frames"] if f["sheet"] == sh]):
                r, c = divmod(j2, cols)
                x0, y0 = c * cw, HEAD_H + r * (ch + LABEL_H)
                patch = np.asarray(img.crop((x0 + cw // 4, y0 + ch // 4, x0 + 3 * cw // 4, y0 + 3 * ch // 4)), dtype=np.float64).mean()
                y_code = 255 * ((fr["t"]) % 2) / 2                 # the luma code the generator wrote (limited range on decode: 16..235 -> 0..255)
                if y_code < 20 or y_code > 230:                    # clipped ends of the ramp say nothing about the time
                    continue
                want = (y_code - 16) * 255 / 219
                d = abs(patch - want)
                worst = max(worst, d)
                checked += 1
                if d > 7:
                    bad.append((fr["i"], round(float(patch), 1), round(want, 1)))
        check("ramp: every sheet cell shows the frame at its labelled time (within 7 levels = 0.05 s of the ramp)", not bad and checked > 25, f"checked {checked}, worst {worst:.1f}, bad {bad[:4]}")
        rc, so, se, j = run_cc(["ingest", "--run", run_r, "--chunk", cdir / "chunk.mp4"], tiny)
        check("ramp: a later ingest makes the skipped transcript and the chunk is done", j and j["status"] == "done" and j["stages"]["transcript"] is True, json.dumps(j)[:200])
        tj = json.loads((cdir / "transcript.json").read_text(encoding="utf-8"))
        check("ramp: a tone has no speech: empty transcript, still a valid file", tj["engine"] == "faster-whisper" and isinstance(tj["segments"], list))

        # ---------------------------------------------------------------- short chunk, chunk without audio, corrupt chunk
        for idx, (name, src, dur, with_audio) in enumerate((("short", data / "short10.mp4", 10, True), ("noaudio", data / "noaudio.mp4", 20, False),
                                                           ("portrait", data / "portrait.mp4", 10, True))):
            if not src.exists():
                continue
            ses = f"20261112-1400{idx:02d}-{name}"
            sd = inbox / name / ses
            sd.mkdir(parents=True)
            shutil.copyfile(src, sd / "chunk-0001.mp4")
            make_sidecar(sd / "chunk-0001.json", name, ses, 1, float(dur), "2026-11-12T12:00:00.000Z")
            rc, so, se, j = run_cc(["ingest", "--chunk", sd / "chunk-0001.mp4"], tiny)
            run_x = runs / ses
            cdir = run_x / "10-media" / "C0001"
            check(f"{name}: ingest ok", j and j["ok"], json.dumps(j)[:260])
            d = probe_dur(cdir / "chunk.mp4")
            n = expected_frames(d)
            fj = json.loads((cdir / "frames.json").read_text(encoding="utf-8"))
            check(f"{name}: {n} frames, {math.ceil(n / 30)} sheet(s), overview", len(fj["frames"]) == n and len(list((cdir / "sheets").glob("sheet-*.jpg"))) == math.ceil(n / 30)
                  and (cdir / "sheets" / "overview.jpg").is_file())
            check(f"{name}: timeline rows = {math.ceil(d)}", data_rows(cdir / "timeline.md") == math.ceil(d))
            check_sheet_labels(cdir, fj, name)
            if name == "portrait":
                check("portrait: the 6 x 5 grid of 138 x 245 cells is used", fj["cols"] == 6 and fj["cell"] == [138, 245] and fj["per_sheet"] == 30, json.dumps(fj["cell"]))
            au = json.loads((cdir / "audio.json").read_text(encoding="utf-8"))
            if not with_audio:
                tj = json.loads((cdir / "transcript.json").read_text(encoding="utf-8"))
                check("noaudio: audio.json says no audio, transcript is an empty note, stages all true", au["no_audio"] and tj["segments"] == [] and tj.get("note")
                      and all(v is True for v in j["stages"].values()))
                check("noaudio: no loudness numbers on the frames", all(f["rms_db"] is None for f in fj["frames"]))
        sd = inbox / "bad" / "20261112-150000-bad"
        sd.mkdir(parents=True)
        shutil.copyfile(corrupt, sd / "chunk-0001.mp4")
        rc, so, se, j = run_cc(["ingest", "--chunk", sd / "chunk-0001.mp4"], tiny)
        run_b = runs / "20261112-150000-bad"
        check("corrupt: reported as failed, no crash", rc == 1 and j and j["status"] == "failed" and str(j["stages"]["probe"]).startswith("failed"), json.dumps(j)[:240])
        rc, so, se, j = run_cc(["status", "--run", run_b], env)
        check("corrupt: the run stays consistent and status works", j and j["ok"] and j["by_status"] == {"failed": 1} and j["failed"][0]["chunk"] == "C0001")

        # ---------------------------------------------------------------- free-space refusal
        sd = inbox / "poor" / "20261112-160000-poor"
        sd.mkdir(parents=True)
        shutil.copyfile(data / "short10.mp4", sd / "chunk-0001.mp4") if (data / "short10.mp4").exists() else shutil.copyfile(data / "ramp.mp4", sd / "chunk-0001.mp4")
        rc, so, se, j = run_cc(["ingest", "--chunk", sd / "chunk-0001.mp4"], {**tiny, "CC_MIN_FREE_GB": "100000000"})
        check("low free space: the chunk is refused (exit 3), not moved", rc == 3 and j and j.get("refused") and (sd / "chunk-0001.mp4").exists(), json.dumps(j)[:200])

        # ---------------------------------------------------------------- watch --once: ordering, .crdownload, sidecar wait
        if ref:
            ses = "20261112-170000-wtest"
            sd = inbox / "wtest" / ses
            sd.mkdir(parents=True)
            for n_, src in ((2, data / "P2.mp4"), (1, data / "P1.mp4")):          # written in the "wrong" order
                shutil.copyfile(src, sd / f"chunk-{n_:04d}.mp4")
                make_sidecar(sd / f"chunk-{n_:04d}.json", "wtest", ses, n_, 20.0, f"2026-11-12T11:0{n_}:00.000Z", game="Just Chatting" if n_ == 1 else "Fortnite")
            make_chat(sd / "chat-0002.json", 2, 20, 5)
            (sd / "chunk-0003.mp4.crdownload").write_bytes(b"partial")
            (sd / "Unconfirmed 99.crdownload").write_bytes(b"partial")
            shutil.copyfile(data / "short10.mp4", sd / "chunk-0004.mp4")
            (sd / "chunk-0004.mp4.crdownload").write_bytes(b"still downloading")
            rc, so, se, j = run_cc(["watch", "--once", "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1"], tiny)
            run_w = runs / ses
            rows = json.loads((run_w / "00-inventory" / "chunks.json").read_text(encoding="utf-8")) if (run_w / "00-inventory" / "chunks.json").exists() else []
            mine = [p for p in (j or {}).get("processed", []) if p["session"] == ses]     # the inbox also holds the refused chunk of another session
            check("watch: chunks 1 and 2 ingested in number order", [p["chunk"] for p in mine] == ["C0001", "C0002"] and all(p["status"] == "done" for p in mine),
                  json.dumps(j)[:300])
            check("watch: the .crdownload chunk is left alone and reported", (sd / "chunk-0004.mp4").exists() and any("chunk-0004" in x for x in j["skipped_incomplete"])
                  and not (run_w / "10-media" / "C0004").exists(), json.dumps(j)[:300])
            d1 = probe_dur(run_w / "10-media" / "C0001" / "chunk.mp4")
            check("watch: C0002 starts where C0001 ends in rec time", len(rows) == 2 and abs(rows[1]["rec_start_s"] - d1) < 1e-3 and not rows[1]["stale_rec"],
                  json.dumps([(r["id"], r["rec_start_s"]) for r in rows]))
            check("watch: the stream meta follows the sidecars (game change recorded)", any(c["field"] == "game" and c["to"] == "Fortnite" for c in
                  json.loads((run_w / "00-inventory" / "stream-meta.json").read_text(encoding="utf-8"))["changes"]))
            # ---- cross-boundary commands on this run
            rc, so, se, j = run_cc(["locate", "--run", run_w, "--at", d1 - 0.5], env)
            check("locate before the boundary", j and j["chunk"] == "C0001" and abs(j["offset"] - (d1 - 0.5)) < 1e-3)
            rc, so, se, j = run_cc(["locate", "--run", run_w, "--at", d1 + 0.5], env)
            check("locate after the boundary", j and j["chunk"] == "C0002" and abs(j["offset"] - 0.5) < 1e-3)
            rc, so, se, j = run_cc(["locate", "--run", run_w, "--chunk", "C0002", "--offset", 3.25], env)
            check("locate chunk + offset -> rec", j and abs(j["rec"] - (d1 + 3.25)) < 1e-3)
            rc, so, se, j = run_cc(["locate", "--run", run_w, "--at", "999999"], env)
            check("locate past the end fails cleanly", rc == 1 and j and not j["ok"])
            rc, so, se, j = run_cc(["window", "--run", run_w, "--from", d1 - 3, "--to", d1 + 3, "--what", "transcript,timeline,chat,audio"], env)
            check("window across the boundary reads both chunks", j and j["chunks"] == ["C0001", "C0002"] and j["seconds"] >= 6 and "== C0002" in so and "== C0001" in so,
                  json.dumps(j)[:200])
            rc, so, se, j = run_cc(["frame", "--run", run_w, "--at", d1 + 0.0], env)
            check("frame at the boundary is C0002 +0", j and j["ok"] and j["chunk"] == "C0002" and abs(j["offset"]) < 1e-6 and Path(j["path"]).is_file() and j["width"] == 1280)
            rc, so, se, j = run_cc(["frame", "--run", run_w, "--at", d1 + 2, "--max-width", 320, "--crop", "0.5,0,0.5,0.5"], env)
            check("frame with --max-width and --crop", j and j["ok"] and j["width"] <= 320 and j["height"] > 0, json.dumps(j))
            rc, so, se, j = run_cc(["sheet", "--run", run_w, "--from", d1 - 2, "--to", d1 + 2, "--step", 0.5], env)
            sheets_out = j["sheets"] if j else []
            check("sheet across the boundary: 8 frames, one sheet, no frame files left", j and j["ok"] and j["frames"] == 8 and len(sheets_out) == 1 and Path(sheets_out[0]).is_file()
                  and j["leftover_frames"] == 0 and not [p for p in (run_w / "30-assets" / "sheets").glob(".tmp-*")], json.dumps(j)[:240])
            rc, so, se, j = run_cc(["sheet", "--run", run_w, "--from", 0, "--to", 100000, "--step", 5], env)
            total_rec = d1 + probe_dur(run_w / "10-media" / "C0002" / "chunk.mp4")
            check("sheet clamps to the recording", j and j["ok"] and j["frames"] == math.ceil(total_rec / 5 - 1e-9) and abs(j["rec_to"] - (j["frames"] * 5)) < 1e-6,
                  json.dumps(j)[:200])
            rc, so, se, j = run_cc(["stream-table", "--run", run_w], env)
            md = (run_w / "00-inventory" / "stream.md").read_text(encoding="utf-8")
            check("stream-table: a row per chunk, percentiles, top-10 lists", "| C0001 |" in md and "| C0002 |" in md and "Plain percentiles" in md and "Ten largest seconds by chat rate" in md)
            # ---- out-of-order arrival: chunk 2 first, chunk 1 later
            ses2 = "20261112-180000-ooo"
            sd2 = inbox / "ooo" / ses2
            sd2.mkdir(parents=True)
            shutil.copyfile(data / "P2.mp4", sd2 / "chunk-0002.mp4")
            make_sidecar(sd2 / "chunk-0002.json", "ooo", ses2, 2, 20.0, "2026-11-12T11:03:00.000Z")
            rc, so, se, j = run_cc(["watch", "--once", "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1"], tiny)
            run_o = runs / ses2
            rows = json.loads((run_o / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
            check("out of order: chunk 2 alone starts at rec 0", len(rows) == 1 and rows[0]["rec_start_s"] == 0)
            shutil.copyfile(data / "P1.mp4", sd2 / "chunk-0001.mp4")
            make_sidecar(sd2 / "chunk-0001.json", "ooo", ses2, 1, 20.0, "2026-11-12T11:00:00.000Z")
            rc, so, se, j = run_cc(["watch", "--once", "--interval", "0.5", "--stable", "0.6", "--sidecar-wait", "1"], tiny)
            rows = json.loads((run_o / "00-inventory" / "chunks.json").read_text(encoding="utf-8"))
            d1 = probe_dur(run_o / "10-media" / "C0001" / "chunk.mp4")
            check("out of order: chunk 2's rec start moved to chunk 1's end and was refreshed", len(rows) == 2 and abs(rows[1]["rec_start_s"] - d1) < 1e-3 and rows[1]["stale_rec"] is False
                  and abs(rows[1]["rec_base_s"] - d1) < 1e-3, json.dumps([(r["id"], r["rec_start_s"], r.get("rec_base_s"), r["stale_rec"]) for r in rows]))
            fj2 = json.loads((run_o / "10-media" / "C0002" / "frames.json").read_text(encoding="utf-8"))
            check("out of order: C0002's frames and sheets carry the new rec times", abs(fj2["frames"][0]["rec"] - d1) < 1e-3 and fj2["rec_start_s"] == rows[1]["rec_start_s"])
            check_sheet_labels(run_o / "10-media" / "C0002", fj2, "out-of-order refreshed C0002")
            first_row = [ln for ln in (run_o / "10-media" / "C0002" / "timeline.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| 0:")][0]
            check("out of order: timeline.md of C0002 starts at the new rec time", first_row.startswith(f"| {__import__('cc_common').fmt_hms(d1)} "), first_row[:40])
    finally:
        TIMINGS["suite wall"] = round(time.time() - t_all, 1)
        if not KEEP:
            shutil.rmtree(tmp, ignore_errors=True)
    failed = [r for r in RESULTS if not r[1]]
    print("\nTIMINGS (seconds):")
    for k, v in TIMINGS.items():
        print(f"  {k}: {v}")
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed" + (f"; FAILED: {[r[0] for r in failed]}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
