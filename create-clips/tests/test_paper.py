"""Tests of the paper edit (cc_paper.py, `cc.py paper`): a video's segments in output order with what is said in each (word for word, `[sub]` where the game
prints the line), the stretches the cut list leaves out inside the planned spans, the moments kept whole, in part or left out (moments.json and
second-look.json), the totals, the spans as seconds or H:MM:SS, the fallback without resolved.json, the short cuts summed in one line, and that nothing in
the run is changed. Facts only. Run: python tests/test_paper.py"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_voices as V  # noqa: E402

PY = sys.executable
CC = HERE.parent / "scripts" / "cc.py"


class Check:
    def __init__(self):
        self.failed = []

    def __call__(self, ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            self.failed.append(what[:80])


check = Check()


def cc(*args):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}), cp.stdout


def words(start: float, text: str, step: float = 0.5) -> list:
    return [{"s": start + i * step, "e": start + i * step + step * 0.8, "w": w} for i, w in enumerate(text.split())]


def make_run(tmp: Path) -> Path:
    run = tmp / "runs" / "20261120-000000-papertest"
    (run / "00-inventory").mkdir(parents=True)
    (run / "20-analysis").mkdir(parents=True)
    chunks = [{"id": f"C{i + 1:04d}", "index": i + 1, "rec_start_s": 100.0 * i, "duration_s": 100.0, "status": "done"} for i in range(3)]
    (run / "00-inventory" / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    (run / "state.json").write_text('{"schema":"cc/1","channel":"papertest","mode":"streamer"}', encoding="utf-8")
    trs = {"C0001": [words(1.0, "hello chat welcome back"), words(40.0, "the quiet line lands here"), words(70.0, "nothing to see on this drive")],
           "C0002": [words(10.0, "big crash now"), words(62.0, "radio song plays")],
           "C0003": [words(50.0, "and the end payoff")]}
    for cid, segs in trs.items():
        d = run / "10-media" / cid
        d.mkdir(parents=True)
        tr = {"segments": [{"start": ws[0]["s"], "end": ws[-1]["e"], "text": " ".join(w["w"] for w in ws), "words": ws} for ws in segs]}
        (d / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
    # C0002: "big crash" is the game's subtitle, "now" is not (voices.json current for the transcript)
    tr2 = json.loads((run / "10-media" / "C0002" / "transcript.json").read_text(encoding="utf-8"))
    tw = V.transcript_words(tr2)
    (run / "10-media" / "C0002" / "voices.json").write_text(json.dumps({"schema": V.SCHEMA, "version": V.VERSION, "transcript_sig": V.transcript_sig(tw),
                                                                         "labels": "SS" + "U" * (len(tw) - 2)}), encoding="utf-8")
    a = run / "20-analysis"
    (a / "moments.json").write_text(json.dumps({"moments": [
        {"id": "M1", "rec_from": 105.0, "rec_to": 125.0, "setup_from": 95.0, "title": "the crash"},
        {"id": "M2", "rec_from": 245.0, "rec_to": 260.0, "title": "the payoff"},
        {"id": "M3", "rec_from": 160.0, "rec_to": 170.0, "title": "a beat the cut leaves out"},
        {"id": "M4", "rec_from": 55.0, "rec_to": 75.0, "title": "half kept"}]}), encoding="utf-8")
    (a / "second-look.json").write_text(json.dumps({"moments": [{"id": "SL-M01", "rec_from": 38.0, "rec_to": 50.0, "title": "the quiet line"}]}), encoding="utf-8")
    (a / "acts.json").write_text(json.dumps([{"id": "A1", "rec_from": 0, "rec_to": 100, "kind": "game", "what": "start"},
                                             {"id": "A2", "rec_from": 130, "rec_to": 200, "kind": "dull", "what": "a long drive"}]), encoding="utf-8")
    (a / "avoid.json").write_text(json.dumps([{"rec_from": 140, "rec_to": 150, "kind": "music", "what": "radio song"}]), encoding="utf-8")
    out = run / "60-outputs" / "L01"
    out.mkdir(parents=True)
    edl = {"schema": "cc-edl/1", "video": "L01", "kind": "long", "segments": [
        {"id": "s0", "rec_from": 245.0, "rec_to": 250.0, "note": "cold open"},
        {"id": "s1", "rec_from": 0.0, "rec_to": 60.0, "note": "the start"},
        {"id": "s1b", "rec_from": 61.0, "rec_to": 64.5, "note": "a line after a breath"},
        {"id": "s2", "rec_from": 95.0, "rec_to": 130.0, "note": "the crash with its setup"},
        {"id": "s3", "rec_from": 240.0, "rec_to": 262.0, "note": "the payoff"},
        {"id": "s4", "rec_from": 263.0, "rec_to": 270.0, "note": "the outro after a breath"}]}
    (out / "edl.json").write_text(json.dumps(edl), encoding="utf-8")
    return run


def snapshot(run: Path, skip: Path) -> dict:
    return {str(p): hashlib.sha1(p.read_bytes()).hexdigest() for p in run.rglob("*") if p.is_file() and skip not in p.parents}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc_paper_test_"))
    try:
        run = make_run(tmp)
        out = run / "60-outputs" / "L01"
        side = tmp / "side"
        before = snapshot(run, out)

        # 1. no resolved.json: times summed from the EDL; spans given in seconds
        res, _ = cc("paper", "--run", run, "--edl", out / "edl.json", "--spans", "0-300", "--lines")
        check(res.get("ok") is True and not res.get("resolved_used"), "paper runs without resolved.json (times summed from the EDL) and says so")
        p = json.loads((out / "paper-edit.json").read_text(encoding="utf-8"))
        t = p["totals"]
        check(abs(t["duration_s"] - 132.5) < 0.01 and t["segments"] == 6, f"the video's length is the sum of the segments (132.5 s, 6 segments): {t['duration_s']}")
        check([s["at"] for s in p["segments"]] == [0.0, 5.0, 65.0, 68.5, 103.5, 125.5], f"each segment's output time follows the EDL order: {[s['at'] for s in p['segments']]}")
        check(abs(t["span_s"] - 300) < 0.01 and abs(t["kept_in_spans_s"] - 127.5) < 0.01 and abs(t["kept_share"] - 0.425) < 0.001,
              f"planned 300 s, plays 127.5 s of it (the cold open counted once): {t['kept_in_spans_s']} / {t['kept_share']}")
        lo = [(c["rec_from"], c["rec_to"]) for c in p["left_out"]]
        check(lo == [(60.0, 61.0), (64.5, 95.0), (130.0, 240.0), (262.0, 263.0), (270.0, 300.0)], f"the left-out stretches are the gaps of the kept union inside the span: {lo}")
        big = next(c for c in p["left_out"] if c["rec_from"] == 130.0)
        check(any("M3" in m for m in big["moments"]) and any("dull" in m for m in big["marks"]) and any("music" in m for m in big["marks"]),
              "a left-out stretch names the moment, the dull act and the avoid span inside it")
        check(big["words"] == 3 and big["first"].endswith("radio song plays") and big["longest_no_word_s"] > 60,
              f"a left-out stretch carries its words, its first line and its longest no-word stretch: {big['words']} / {big['first']} / {big['longest_no_word_s']}")
        mo = p["moments"]
        check(sorted(m["id"] for m in mo["whole"]) == ["M1", "M2", "SL-M01"] and [m["id"] for m in mo["left_out"]] == ["M3"]
              and [m["id"] for m in mo["in_part"]] == ["M4"], f"moments whole / in part / left out (second look included): {[(k, [m['id'] for m in v]) for k, v in mo.items()]}")
        m4 = mo["in_part"][0]
        check(abs(m4["share"] - 0.42) < 0.01, f"a moment kept in part gives the share of its span that plays: {m4['share']}")
        m1 = next(m for m in mo["whole"] if m["id"] == "M1")
        check(m1["setup_share"] == 1.0, "a kept moment says how much of its setup plays")
        md = (out / "paper-edit.md").read_text(encoding="utf-8")
        check("[sub] big crash" in md and "0:01:51 now" in md, "--lines prints the kept words line by line, the game's subtitled words marked [sub] on a line of their own")
        check("nothing to see on this drive" not in md.split("## Left out")[0], "a line that is not in a kept segment is not printed under any segment")
        check("hello chat welcome back" in md and "the quiet line lands here" in md, "the words of the kept footage are printed under their segments")
        check("and 1 shorter cut" in md and "0:04:22-0:04:23" not in md, "a short cut with no moment in it is summed in one line, not listed")
        check("0:01:00-0:01:01" in md, "a short cut that holds part of a moment is listed")
        check("0:01:04-0:01:35" in md, "a long left-out stretch is listed with its rec span")

        # 2. resolved.json beside the EDL gives the output times; spans as H:MM:SS
        (out / "resolved.json").write_text(json.dumps({"segments": [{"seg": "s0", "at": 0.0, "dur_out": 5.0}, {"seg": "s1", "at": 5.2, "dur_out": 60.0},
                                                                    {"seg": "s1b", "at": 65.2, "dur_out": 3.5}, {"seg": "s2", "at": 68.7, "dur_out": 35.0},
                                                                    {"seg": "s3", "at": 103.7, "dur_out": 22.0},
                                                                    {"seg": "s4", "at": 125.7, "dur_out": 7.0}],
                                                       "totals": {"duration_s": 132.7}}), encoding="utf-8")
        res, _ = cc("paper", "--run", run, "--edl", out / "edl.json", "--spans", "0:00:00-0:05:00", "--out", side)
        p2 = json.loads((side / "paper-edit.json").read_text(encoding="utf-8"))
        check(res.get("ok") and res.get("resolved_used") and p2["segments"][1]["at"] == 5.2 and abs(p2["totals"]["duration_s"] - 132.7) < 0.01,
              "with resolved.json the output times and the length are edl-check's")
        check(abs(p2["totals"]["span_s"] - 300) < 0.01 and (side / "paper-edit.md").is_file() and not (side / "edl.json").exists(),
              "spans as H:MM:SS read the same; --out writes the paper edit elsewhere")
        check(chr(10) + "    0:01:50" not in (side / "paper-edit.md").read_text(encoding="utf-8"), "without --lines no spoken line is printed under the segments")

        # 3. no spans: the EDL's own first-to-last rec time
        res, _ = cc("paper", "--run", run, "--edl", out / "edl.json", "--out", side / "own")
        p3 = json.loads((side / "own" / "paper-edit.json").read_text(encoding="utf-8"))
        check(res.get("ok") and p3["totals"]["spans_are_the_edl_extent"] and p3["totals"]["spans"] == [[0.0, 270.0]],
              "without --spans the planned source is the EDL's own first-to-last rec time, and the paper edit says so")

        # 4. refusals
        res, _ = cc("paper", "--run", run, "--edl", out / "edl.json", "--spans", "300-100")
        check(res.get("ok") is False or "error" in json.dumps(res), "a span that ends before it starts is refused")
        (tmp / "empty.json").write_text(json.dumps({"segments": []}), encoding="utf-8")
        res, _ = cc("paper", "--run", run, "--edl", tmp / "empty.json")
        check(res.get("ok") is False or "error" in json.dumps(res), "an EDL with no segments is refused")

        # 5. nothing in the run changed but the paper edit's own files (and the resolved.json this test wrote)
        after = snapshot(run, out)
        check(before == after, "the run's own files are unchanged (the paper edit only reads them)")
        check(sorted(p.name for p in out.iterdir()) == ["edl.json", "paper-edit.json", "paper-edit.md", "resolved.json"],
              "the paper edit writes only paper-edit.md and paper-edit.json beside the EDL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = 24
    print(f"test_paper: ok {n - len(check.failed)} | " + ("ALL PASSED" if not check.failed else f"FAILED: {check.failed}"))
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
