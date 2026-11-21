"""Tests of the delivery and speed commands (cc_ops.py): `deliver-name` (only characters Windows cannot take are replaced), `claim` (one session per
video under the state lock: a fresh claim of another session is refused, a stale one taken over, released), `export-check` (a generated MP4: plays,
length against resolved.json, the kind's canvas, a sound stream that is not silent; a wrong canvas or a missing file is not `verified`), `timings` (the
commands' log, the ingest stages and the reports with the time each was ready after its chunk) and that every cc.py command is timed.
Run: python tests/test_ops.py"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_ops as O  # noqa: E402
from cc_common import find_tool  # noqa: E402

PY = sys.executable
CC = HERE.parent / "scripts" / "cc.py"
FAILED = []
N = [0]


def check(ok, what):
    N[0] += 1
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILED.append(what[:90])


def cc(*args):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}), cp.returncode


def mp4(path: Path, w: int, h: int, d: float, audio: bool = True):
    a = ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={d}"] if audio else []
    subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=30:d={d}", *a, "-c:v", "libx264", "-preset",
                    "ultrafast", "-pix_fmt", "yuv420p", *(["-c:a", "aac"] if audio else []), "-shortest", str(path)], check=True, capture_output=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc_ops_test_"))
    try:
        # deliver-name
        check(O.safe_name('He Is NOT "Medium Build"? | Part 2/3') == "He Is NOT Medium Build Part 2 3", "the Windows-invalid characters are replaced, the words kept")
        check(O.safe_name("CON") == "_CON" and O.safe_name("  ...  ") == "video" and O.safe_name("Ends with a dot.") == "Ends with a dot",
              "reserved names, empty names and a trailing dot are made valid")
        check(O.safe_name("Él dijo ¡qué! 😂 #shorts") == "Él dijo ¡qué! 😂 #shorts" and O.safe_name("why?") == "why",
              "letters of any language, emoji, ! and # stay (Windows takes them); a ? does not")
        check(len(O.safe_name("x" * 400)) == 180, "a very long title is cut to 180 characters")
        r, _ = cc("deliver-name", "--title", "A: B")
        check(r.get("filename") == "A B.mp4" and r.get("title") == "A: B" and r.get("changed") is True, "deliver-name keeps the title as written beside the file name")

        # claim
        run = tmp / "runs" / "20261121-000000-opstest"
        (run / "00-inventory").mkdir(parents=True)
        (run / "00-inventory" / "chunks.json").write_text("[]", encoding="utf-8")
        (run / "state.json").write_text(json.dumps({"schema": "cc/1", "videos": {"S01": {"kind": "short", "status": "planned"}}}), encoding="utf-8")
        r, code = cc("claim", "--run", run, "--video", "S01", "--by", "one", "--status", "building")
        check(r.get("ok") and r.get("status") == "building", "a free video is claimed and set building")
        r, code = cc("claim", "--run", run, "--video", "S01", "--by", "two")
        check(r.get("ok") is False and code == 3 and r.get("claimed_by") == "one", "a fresh claim of another session is refused (exit 3)")
        r, code = cc("claim", "--run", run, "--video", "S01", "--by", "two", "--stale-min", "0")
        check(r.get("ok") and r.get("took_over") == "one", "a stale claim is taken over and says from whom")
        r, code = cc("claim", "--run", run, "--video", "S01", "--by", "two", "--status", "nonsense")
        check(r.get("ok") is False, "an unknown status is refused")
        r, code = cc("claim", "--run", run, "--video", "S01", "--release")
        st = json.loads((run / "state.json").read_text(encoding="utf-8"))
        check(r.get("ok") and "claimed_by" not in st["videos"]["S01"] and st["videos"]["S01"]["status"] == "building", "release frees the video and keeps its status")

        # export-check
        out = run / "60-outputs" / "S01"
        out.mkdir(parents=True)
        (out / "resolved.json").write_text(json.dumps({"kind": "short", "totals": {"duration_s": 4.0}}), encoding="utf-8")
        good, wide, mute = tmp / "good.mp4", tmp / "wide.mp4", tmp / "mute.mp4"
        mp4(good, 1080, 1920, 4.0)
        mp4(wide, 1920, 1080, 4.0)
        mp4(mute, 1080, 1920, 4.0, audio=False)
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", good, "--title", "A: B", "--set-state")
        st = json.loads((run / "state.json").read_text(encoding="utf-8"))
        check(r.get("ok") and all(c["ok"] for c in r["checks"].values()) and st["videos"]["S01"]["status"] == "verified"
              and st["videos"]["S01"]["youtube_title"] == "A: B" and (out / "export-check.json").is_file(),
              "a good short export: every check passes, the state says verified with the file and the title: " + json.dumps(r.get("checks"))[:200])
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", wide, "--set-state")
        st = json.loads((run / "state.json").read_text(encoding="utf-8"))
        check(r.get("ok") is False and not r["checks"]["canvas"]["ok"] and st["videos"]["S01"]["status"] == "attention", "a short exported wide fails the canvas: attention")
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", mute)
        check(r.get("ok") is False and not r["checks"]["audio_stream"]["ok"], "an export with no sound stream fails")
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", good, "--expect-s", "9")
        check(r.get("ok") is False and not r["checks"]["duration"]["ok"], "an export of the wrong length fails")
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", tmp / "missing.mp4")
        check(r.get("ok") is False and code == 1, "a missing file is a failure, never verified")
        # the frame rate, and the sound against its source: an export made of one 7 s piece of a source with noise for sound
        src = tmp / "src.mp4"
        subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=7", "-f", "lavfi", "-i",
                        "anoisesrc=d=7:c=pink:r=48000:a=0.3", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        str(src)], check=True, capture_output=True)
        (out / "resolved.json").write_text(json.dumps({"kind": "short", "totals": {"duration_s": 7.0}, "pieces": [
            {"kind": "plain", "file": str(src), "src_from": 0.0, "at": 0.0, "dur_out": 7.0, "speed": 1.0, "volume": 1.0}]}), encoding="utf-8")
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", src)
        ch = r.get("checks") or {}
        check(r.get("ok") and ch.get("frame_rate", {}).get("fps") == 30.0 and ch.get("sync", {}).get("ok") and abs(ch["sync"].get("lag_ms", 99)) <= 2,
              "the frame rate is read (30) and the sound lines up with its source (lag about 0): " + json.dumps({k: ch.get(k) for k in ("frame_rate", "sync")}))
        late = tmp / "late.mp4"
        subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-i", str(src), "-itsoffset", "0.2", "-i", str(src), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", str(late)], check=True, capture_output=True)
        r, code = cc("export-check", "--run", run, "--video", "S01", "--file", late)
        ch = r.get("checks") or {}
        check(not ch.get("sync", {}).get("ok", True) and 150 <= abs(ch["sync"].get("lag_ms", 0)) <= 250,
              "sound 200 ms late is caught by the sync check: " + json.dumps(ch.get("sync")))

        # timings: every command above was timed; the ingest and report logs are read
        logs = run / "logs"
        lines = [json.loads(x) for x in (logs / "cc-timings.jsonl").read_text(encoding="utf-8").splitlines()]
        check(any(x["cmd"] == "claim" for x in lines) and any(x["cmd"] == "export-check" and x["code"] == 1 for x in lines),
              "every cc.py command with a run is timed in RUN/logs/cc-timings.jsonl, a failure with its exit code")
        (logs / "ingest-C0001.log").write_text("[2026-11-20 04:06:58] ingest end: done {'move': 0.0, 'sheets': 15.7, 'transcript': 9.1}\n", encoding="utf-8")
        (logs / "report-C0001.log").write_text("[2026-11-20T04:09:33+01:00]\nattempt 1: turns 2, cost 0.0100, 40.5 s, opened 9, not opened []\ndone\n", encoding="utf-8")
        r, code = cc("timings", "--run", run)
        check(r.get("ok") and r["ingest_stages_min"]["transcript"]["median_s"] == 9.1 and r["reports"]["median_turns"] == 2
              and r["reports"]["ready_after_chunk_min"]["median"] == 2.6 and "claim" in r["commands"],
              "timings: the stages, the reports and how long after its chunk each report was ready: " + json.dumps(r.get("reports"))[:200])
        # THE FRAME OF AN EXPORT (the user, 2026-11-21: "a 1080x1920 export can still be badly cropped"): the export's picture against the source laid where the
        # plan puts it. The whole picture in the band with black above and below passes; a crop that fills the canvas, a stretch to 9:16 and a zoom inside the band fail.
        fsrc = tmp / "frame-src.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30", "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-g", "30", str(fsrc)], check=True)
        fres = {"kind": "short", "canvas": {"width": 1080, "height": 1920, "fps": 30},
                "pieces": [{"piece": 1, "kind": "plain", "file": str(fsrc), "src_from": 0.0, "src_to": 6.0, "at": 0.0, "dur_out": 6.0, "speed": 1.0,
                            "src_size": [1280, 720], "layout": {"mode": "fit", "scale": 1.0, "posX": 0.0, "posY": 0.0}}],
                "captions": {"placement": {"band": [1263.8, 1920], "caption_reach_px": [1302.0, 1375.0]}}}
        outs = {}
        for name, vf in (("fit", "scale=1080:608,pad=1080:1920:0:656:black"), ("crop", "crop=405:720:437:0,scale=1080:1920"), ("stretch", "scale=1080:1920"),
                         ("zoomed", "scale=1404:790,crop=1080:608:162:91,pad=1080:1920:0:656:black"),
                         ("fit-caption", "scale=1080:608,pad=1080:1920:0:656:black,drawbox=x=300:y=1310:w=480:h=60:color=yellow:t=fill"),
                         ("fit-blur", "split[a][b];[a]scale=1080:1920,boxblur=20[bg];[b]scale=1080:608[fg];[bg][fg]overlay=0:656")):
            p_ = tmp / f"frame-{name}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(fsrc), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(p_)], check=True)
            outs[name] = O._framing_check(p_, fres, "short", "fit", tmp)
        s_fit = outs["fit"]["samples"]
        check(outs["fit"]["ok"] and s_fit and all(s["whole_source_visible"] and s["bands_black"] and s["picture"] >= 0.95 for s in s_fit) and Path(outs["fit"]["sheet"]).is_file(),
              "framing: the whole picture in the band, black above and below: ok, the picture matches the source " + json.dumps([(s["t"], s["picture"], s["strips"]) for s in s_fit])[:220])
        check(outs["fit-caption"]["ok"] and all(s.get("caption_rows_px") for s in outs["fit-caption"]["samples"]),
              "framing: a caption in the band under the picture is allowed and its rows are found " + json.dumps([s.get("caption_rows_px") for s in outs["fit-caption"]["samples"]]))
        for name in ("crop", "stretch", "zoomed", "fit-blur"):
            ss = outs[name]["samples"]
            check(not outs[name]["ok"], f"framing: a {name} export of a whole-picture plan is caught " + json.dumps([(s["t"], s.get("picture"), s.get("strips"), s.get("bands_black")) for s in ss])[:260])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"test_ops: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
