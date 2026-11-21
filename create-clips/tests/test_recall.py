"""Tests of the second look's gathering (cc_recall.py, `cc.py recall`): what no moment covers, the miners' unused leads, the sample windows placed by the
clock alone, the threads of older and newer block files, the check of a second-look file, and that nothing in the run is changed. Facts only: the tests
also check that no signal (a chat burst, a loud chunk) moves a sample window. Run: python tests/test_recall.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_recall as R  # noqa: E402

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


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env)
    last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}), cp.stdout


def make_run(tmp: Path, with_heat: bool) -> Path:
    run = tmp / "runs" / "20261120-000000-recalltest"
    (run / "00-inventory").mkdir(parents=True)
    (run / "20-analysis" / "blocks").mkdir(parents=True)
    chunks = []
    for i in range(6):   # six chunks of 300 s: 0-1800, with an ad batch of 60 s inside chunk 4
        cid = f"C{i + 1:04d}"
        chunks.append({"id": cid, "index": i + 1, "rec_start_s": 300.0 * i, "duration_s": 300.0, "status": "done", "stages": {"transcript": True}})
        d = run / "10-media" / cid
        d.mkdir(parents=True)
        (d / "digest.json").write_text(json.dumps({"wpm": 100 + i, "loud_jumps": 50 if (with_heat and i == 2) else 3, "chat_total": 900}), encoding="utf-8")
    (run / "00-inventory" / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    (run / "state.json").write_text('{"schema":"cc/1","channel":"recalltest","mode":"streamer"}', encoding="utf-8")
    if with_heat:
        (run / "20-analysis" / "heat.json").write_text(json.dumps({"bursts": [{"id": "H001", "peak_rec": 700.0}, {"id": "H002", "peak_rec": 1500.0},
                                                                               {"id": "H003", "peak_rec": 610.0, "onset_rec": 604.0},
                                                                               {"id": "H004", "peak_rec": 1320.0}, {"id": "H005", "peak_rec": 1700.0}]}),
                                                         encoding="utf-8")
    b1 = {"block": 1, "chunks": ["C0001", "C0002", "C0003"], "rec_from": 0.0, "rec_to": 900.0,
          "summary": "0:00:10 he starts the mission\n0:02:00-0:03:00 a long drive with the radio\n400: the crash and his scream\n0:12:30 he reads chat a poll",
          "moments": [{"id": "B01-M01", "rec_from": 390.0, "rec_to": 440.0, "setup_from": 380.0, "title": "the crash"}],
          "acts": [{"rec_from": 0.0, "rec_to": 900.0, "kind": "game", "what": "the first mission"}],
          "richness": [{"chunk": "C0001", "score": 5}, {"chunk": "C0002", "score": 7}, {"chunk": "C0003", "score": 4}],
          "heat_review": [{"burst": "H001", "why": "dance emotes to a song"}, {"burst": "H003", "why": "chat laughs at the game's line in the cutscene, no reaction from him"}],
          "notes": "No ad. Running bits: the hat (150, 610, 820); the shower (395, 420). Exclamations at 500 are not religion.",
          "ad_batches": []}
    b2 = {"block": 2, "chunks": ["C0004", "C0005", "C0006"], "rec_from": 900.0, "rec_to": 1800.0,
          "summary": ["0:15:00 back home", "1:00:00 an hour mark nobody reached"],
          "moments": [{"id": "B02-M01", "rec_from": 1400.0, "rec_to": 1450.0, "title": "the payoff"}],
          "maybes": [{"rec_from": 1600.0, "rec_to": 1630.0, "what": "a quiet line about the hat", "why_not": "unsure it lands", "kind": "uncertain"},
                     {"rec_from": 1410.0, "rec_to": 1420.0, "what": "a second angle on the payoff", "why_not": "inside B02-M01", "kind": "rejected"}],
          "threads": [{"what": "the hat", "points": [{"rec": 1425.0, "role": "payoff"}, {"rec": 1700.0, "role": "reference"}], "open": "before"}],
          "heat_review": [{"burst": "H004", "why": "the game's joke", "face": "still"}, {"burst": "H005", "why": "chat spams a word", "face": "not looked"},
                          {"burst": "H003", "why": "the same burst seen from this block, no reaction from him"}],
          "ad_batches": [{"chunks": ["C0004"], "rec_from": 1000.0, "rec_to": 1060.0, "verdict": "ad"}]}
    for n, b in ((1, b1), (2, b2)):
        (run / "20-analysis" / "blocks" / f"block-{n:02d}.json").write_text(json.dumps(b), encoding="utf-8")
    return run


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-recall-test-"))
    try:
        run = make_run(tmp, with_heat=True)
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs"), "CC_NOTIFY": "0", "PYTHONIOENCODING": "utf-8"}
        before = {p: p.read_bytes() for p in (run / "20-analysis" / "blocks").glob("*.json")}
        cfg = {"sample_every_s": 300.0, "sample_len_s": 90.0, "min_stretch_s": 45.0, "margin_s": 15.0}
        g = R.gather(run, cfg)
        # coverage: 1800 s, 60 s of ad, moments 380-440 and 1400-1450 = 110 s
        check(g["total_s"] == 1800.0 and g["ads_s"] == 60.0 and g["covered_s"] == 110.0 and abs(g["uncovered_s"] - 1630.0) < 0.01,
              f"coverage: the ad batch is left out and the moments count from their setup: {g['total_s']} {g['ads_s']} {g['covered_s']} {g['uncovered_s']}")
        kinds = {}
        for ld in g["leads"]:
            kinds.setdefault(ld["kind"], []).append(ld)
        sums = sorted(round(x["rec_from"]) for x in kinds.get("summary", []))
        check(sums == [10, 120, 750, 900], "summary lines no moment covers are leads (10, 120-180, 750, 900), the line inside a moment (400) and a time outside "
                                            "the block (1:00:00) are not: " + str(sums))
        thr = sorted(round(x["rec_from"]) for x in kinds.get("thread", []))
        check(thr == [], "thread points are not leads of their own by default (2026-11-20: 15 thread leads gave no moment): " + str(thr))
        gt = R.gather(run, {**cfg, "thread_leads": True})
        thr = sorted(round(x["rec_from"]) for x in gt["leads"] if x["kind"] == "thread")
        check(thr == [150, 610, 820, 1700], "with recall.thread_leads, thread points from older notes ('Running bits: the hat (150, 610, 820)') and from "
                                            "structured threads are leads, those inside a moment left out (395, 420, 1425): " + str(thr))
        mays = kinds.get("maybe", [])
        check(len(mays) == 2 and any(m.get("inside") == "B02-M01" for m in mays) and all("set aside" in m["text"] for m in mays),
              "every set-aside moment is a lead, with its reason, even one inside a moment (named): " + json.dumps(mays)[:240])
        reac = sorted((round(x["rec_from"]), x.get("burst")) for x in kinds.get("reaction", []))
        check(reac == [(598, "H003"), (1694, "H005")], "reaction checks: a burst set aside as 'no reaction' or as the game's line (an older file) and one whose face "
                                                       "was not looked at; never a face seen 'still', never a song, never the same burst twice: " + str(reac))
        samples = [(x["rec_from"], x["rec_to"]) for x in kinds.get("sample", [])]
        check(len(samples) == 5 and all(b - a <= 90.0 for a, b in samples), "sample windows: one per 300 s of uncovered time, 90 s each: " + str(samples))
        check([ld["id"] for ld in g["leads"]] == [f"L{i + 1:03d}" for i in range(len(g["leads"]))] and
              [ld["rec_from"] for ld in g["leads"]] == sorted(ld["rec_from"] for ld in g["leads"]), "leads are numbered in time order")
        check(len(g["threads"]) == 3 and g["threads"][0]["uncovered_points"] == [150.0, 610.0, 820.0], "the threads are listed with their uncovered points")
        # no signal moves a sample: the same run without bursts and loud chunks gives the same windows
        run2 = make_run(tmp / "b", with_heat=False)
        g2 = R.gather(run2, cfg)
        check([(x["rec_from"], x["rec_to"]) for x in g2["leads"] if x["kind"] == "sample"] == samples,
              "the sample windows are placed by the clock alone: chat bursts and loud chunks do not move them")
        check(json.dumps({k: v for k, v in R.gather(run, cfg).items() if k != "made_at"}, sort_keys=True) ==
              json.dumps({k: v for k, v in g.items() if k != "made_at"}, sort_keys=True), "the gathering is deterministic")
        # the command, the page, the check
        r, _ = cc("recall", "--run", run, "--sample-every-s", 300, env=env)
        md = (run / "20-analysis" / "recall.md").read_text(encoding="utf-8")
        check(r.get("ok") and r["lead_counts"]["sample"] == 5 and "## U" in md and "L001" in md and "## Threads" in md and "H001 (reviewed)" in md,
              "`recall` writes recall.md/json: stretches with their numbers, the leads, the threads, a reviewed burst marked: " + json.dumps(r)[:200])
        check({p: p.read_bytes() for p in (run / "20-analysis" / "blocks").glob("*.json")} == before, "the block files are never changed")
        sl = {"moments": [{"id": "SL-M01", "rec_from": 1600.0, "rec_to": 1640.0, "lead": ["L999"]}],
              "checked": [{"lead": ld["id"], "verdict": "not-a-moment", "why": "x"} for ld in g["leads"][:3]]}
        (run / "20-analysis" / "second-look.json").write_text(json.dumps(sl), encoding="utf-8")
        r, _ = cc("recall", "--run", run, "--check", run / "20-analysis" / "second-look.json", env=env)
        must = [ld for ld in g["leads"] if ld["tier"] in ("look", "sample")]
        named = {ld["id"] for ld in g["leads"][:3]}
        check(r.get("ok") is False and len(r["unmentioned"]) == len([ld for ld in must if ld["id"] not in named]) and r["recovered"] == 1
              and r["read_tier_not_mentioned"] == len([ld for ld in g["leads"] if ld["tier"] == "read" and ld["id"] not in named]),
              "`--check` lists every look-first lead and sample window the second look never mentioned, and only counts the read-tier ones: " + json.dumps(r)[:200])
        tiers = {ld["kind"]: ld["tier"] for ld in g["leads"]}
        check(tiers.get("reaction") == "look" and tiers.get("sample") == "sample" and tiers.get("summary") == "read" and g["tier_counts"]["look"] >= 2,
              "the tiers: a burst set aside without the face seen is look-first, a sample window is a sample, a summary line is context: " + json.dumps(tiers))
        md0 = R.render_md(g)
        check(md0.index("## Look first") < md0.index("## Sample windows") < md0.index("## The rest, by stretch"), "recall.md lists the look-first leads, then the samples, then the rest")
        sl["checked"] = [{"lead": ld["id"], "verdict": "not-a-moment", "why": "x"} for ld in must]
        (run / "20-analysis" / "second-look.json").write_text(json.dumps(sl), encoding="utf-8")
        r, _ = cc("recall", "--run", run, "--check", run / "20-analysis" / "second-look.json", env=env)
        check(r.get("ok") is True and r["unmentioned"] == [], "every look-first lead and sample window named (the read tier left as context): the check passes")
        sl["checked"] = [{"lead": ld["id"], "verdict": "not-a-moment", "why": "x"} for ld in g["leads"]]
        (run / "20-analysis" / "second-look.json").write_text(json.dumps(sl), encoding="utf-8")
        r, _ = cc("recall", "--run", run, "--check", run / "20-analysis" / "second-look.json", env=env)
        check(r.get("ok") is True and r["unmentioned"] == [], "every lead named: the check passes")
        g3 = R.gather(run, cfg, extra_moments=sl["moments"])
        check(g3["covered_s"] == 150.0 and not any(ld["kind"] == "maybe" and ld["rec_from"] == 1600.0 and not ld.get("inside") for ld in g3["leads"]),
              "--include: the second look's own moments count as covered in a later gathering")
        check(R.times_in("the shower bit (178, 191-198, 1570); $45,000, 1,200, 45% in 2024; 1:05:26 and 5602-5716:", 0, 6000)
              == [178.0, 191.0, 198.0, 1570.0, 2024.0, 3926.0, 5602.0, 5716.0], "times in free text: lists and ranges, never money, thousands or percents")
        empty = tmp / "runs" / "20261120-000001-empty"
        (empty / "00-inventory").mkdir(parents=True)
        (empty / "00-inventory" / "chunks.json").write_text("[]", encoding="utf-8")
        (empty / "state.json").write_text("{}", encoding="utf-8")
        r, _ = cc("recall", "--run", empty, env=env)
        check(r.get("ok") is False, "a run with no block files fails cleanly (the second look comes after the scan)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL PASSED" if not check.failed else f"FAILED: {check.failed}")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
