"""Regression test of cc_game.py (hud-states, units-check, units-table) and `config get` on a synthetic run (no network, no media).

    python tests/test_game.py

Builds hud-scan-shaped series files by hand (the real hud-scan is tested in test_hud.py), then checks the table of score changes (a one-sample flicker is dropped,
empty reads are skipped, a reset is flagged), the facts units-check reports for a block file with planted problems, and the table written for the user.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "scripts" / "cc.py"
PY = sys.executable


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=300)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    return json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def series(name, text_at, t_end=400):
    return {"name": name, "region": [0, 0, 1, 1], "step": 1.0, "kind": "digits",
            "rows": [{"rec": float(t), "chunk": "C0001", "t_chunk": float(t), "text": text_at(t), "conf": 0.9, "reused": False} for t in range(t_end)],
            "summary": {}}


def score_a(t):
    if t == 20:
        return "8"                       # a one-sample flicker: never a value
    if 70 <= t <= 72:
        return ""                        # an empty read: skipped, not a change
    return "0" if t < 60 else "1" if t < 150 else "2" if t < 300 else "0"      # the last step is a reset


def score_b(t):
    return "0" if t < 100 else "1"


def unit(uid, a, b, **kw):
    u = {"id": uid, "kind": "round", "rec_from": a, "rec_to": b, "impact": 5, "impact_why": "x", "confidence": "high", "evidence": ["sheet"], "keep_hint": "trim"}
    u.update(kw)
    return u


def integration(env, tmp):
    """The real hud-scan on a synthetic scoreboard video (a score that changes at 10 s and 25 s, another at 18 s), then hud-states on the files it wrote:
    the two modules meet on hud-scan's JSON, which the hand-made series above only imitate. Skipped when the OCR or a font is not there."""
    try:
        import rapidocr_onnxruntime  # noqa: F401
    except Exception:  # noqa: BLE001
        print("skip integration (rapidocr-onnxruntime is not installed)")
        return
    font = Path("C:/Windows/Fonts/arial.ttf")
    if not font.is_file():
        print("skip integration (no arial.ttf)")
        return
    run = tmp / "runs" / "20261112-000001-hudint"
    d = run / "10-media" / "C0001"
    d.mkdir(parents=True)
    (run / "00-inventory").mkdir(parents=True)
    f = "C\\:/Windows/Fonts/arial.ttf"

    def txt(x, text, cond):
        return f"drawtext=fontfile='{f}':text='{text}':fontsize=64:fontcolor=white:x={x}:y=30:enable='{cond}'"
    vf = ",".join([txt(500, "0", "lt(t,10)"), txt(500, "1", "between(t,10,24.99)"), txt(500, "2", "gte(t,25)"), txt(740, "3", "lt(t,18)"), txt(740, "4", "gte(t,18)")])
    cp = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=10", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                         "-t", "40", "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(d / "chunk.mp4")], capture_output=True, text=True)
    if cp.returncode != 0:
        print("skip integration (ffmpeg could not draw text: " + cp.stderr[-120:].strip() + ")")
        return
    (run / "00-inventory" / "chunks.json").write_text(json.dumps([{"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 40.0, "status": "done"}]), encoding="utf-8")
    (run / "state.json").write_text('{"schema":"cc/1","channel":"hudint"}', encoding="utf-8")
    hud = run / "20-analysis" / "hud"
    hud.mkdir(parents=True)
    regions = {"frame": [1280, 720], "tested_at": [5.0, 30.0],         # the shape cc-profile-game writes: hud-scan --spec reads `readers`, the rest is the agents' map
               "readers": [{"name": "score_a", "region": [0.37, 0.02, 0.08, 0.14], "kind": "digits", "regex": r"^\d{1,2}$", "numeric": True, "note": "left team"},
                           {"name": "score_b", "region": [0.56, 0.02, 0.08, 0.14], "kind": "digits", "regex": r"^\d{1,2}$", "numeric": True, "note": "right team"}],
               "series": {"feed": [0.7, 0.1, 0.3, 0.3]}}
    (hud / "regions.json").write_text(json.dumps(regions), encoding="utf-8")
    r = cc("hud-scan", "--run", run, "--spec", hud / "regions.json", "--step", "1", env=env)
    check(r.get("ok") and (hud / "score_a.json").is_file() and (hud / "score_b.json").is_file(),
          "one hud-scan --spec pass wrote both readers' files from the regions.json shape the profile phase writes " + json.dumps({k: r.get(k) for k in ("error", "stderr")}))
    r = cc("hud-states", "--run", run, "--series", "score_a,score_b", env=env)
    got = [(x.split("  ", 1)[0], x.split("  ", 1)[1].split("   ")[0]) for x in r.get("shown", [])]
    check(("0:00:10.00", "score_a 0 -> 1 (+1)") in got and ("0:00:25.00", "score_a 1 -> 2 (+1)") in got and ("0:00:18.00", "score_b 3 -> 4 (+1)") in got,
          "hud-states on the real hud-scan files finds the three changes at 10, 18 and 25 s " + json.dumps(got))
    check(r.get("not_plus_one_count") == 0, "no change is flagged as not +1")
    r = cc("hud-slice", "--run", run, "--name", "score_a", "--from", "8", "--to", "12", env=env)
    check(r.get("ok") and r["samples_in_range"] == 5 and r["rows"] == ["0:00:08.00  0", "0:00:10.00  1"], "hud-slice gives the readings of score_a between 8 and 12 s, one line per change " + json.dumps(r.get("rows")))
    r = cc("hud-slice", "--run", run, "--name", "nope", env=env)
    check(r.get("ok") is False, "hud-slice of a reader that was never scanned is refused")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-game-test-"))
    try:
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs")}
        run = tmp / "runs" / "20261112-000000-testmatch"
        hud, blocks = run / "20-analysis" / "hud", run / "20-analysis" / "blocks"
        for d in (hud, blocks, run / "00-inventory", run / "deliverables"):
            d.mkdir(parents=True)
        (run / "state.json").write_text('{"schema":"cc/1","channel":"testmatch"}', encoding="utf-8")
        (run / "00-inventory" / "chunks.json").write_text(json.dumps([
            {"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 200.0, "status": "done"},
            {"id": "C0002", "index": 2, "rec_start_s": 200.0, "duration_s": 200.0, "status": "done"}]), encoding="utf-8")
        (hud / "score_a.json").write_text(json.dumps(series("score_a", score_a)), encoding="utf-8")
        (hud / "score_b.json").write_text(json.dumps(series("score_b", score_b)), encoding="utf-8")

        r = cc("hud-states", "--run", run, "--series", "score_a,score_b", env=env)
        check(r.get("ok") and r["rows"] == 6, "hud-states: 2 initial values + 4 changes (the flicker at 20 and the empty reads are not changes) " + json.dumps(r)[:300])
        check(r["series"]["score_a"]["changes"] == 3 and r["series"]["score_b"]["changes"] == 1, "three changes of score_a, one of score_b")
        check(r["not_plus_one_count"] == 1 and r["not_plus_one"][0][:2] == [300.0, "score_a"], "the reset to 0 at 300 s is listed as not +1")
        st = json.loads((hud / "states.json").read_text(encoding="utf-8"))
        at150 = next(x for x in st["rows"] if x["rec"] == 150.0)
        check(at150["state"] == {"score_a": "2", "score_b": "1"} and at150["delta"] == 1, "the state after the change at 150 s is 2-1")
        check("0:02:30.00  score_a 1 -> 2 (+1)   [2-1]" in (hud / "states.txt").read_text(encoding="utf-8"), "states.txt reads like a table")
        r = cc("hud-states", "--run", run, "--series", "score_a,nope", env=env)
        check(r.get("ok") is False and "hud-scan" in r.get("error", ""), "a missing series is refused with the command to run first")

        block = {"block": 1, "chunks": ["C0001", "C0002"], "rec_from": 0.0, "rec_to": 400.0, "summary": "s",
                 "units": [unit("R1", 0.0, 65.0), unit("R2", 65.0, 155.0), unit("R3", 150.0, 210.0, evidence=[]), unit("R4", 210.0, 250.0, keep_spans=[[200.0, 250.0]])],
                 "non_play": [{"kind": "timeout", "rec_from": 250.0, "rec_to": 290.0, "note": "t"}], "extras": [], "sensitive": [], "avoid": []}
        bf = blocks / "block-01.json"
        bf.write_text(json.dumps(block), encoding="utf-8")
        r = cc("units-check", "--run", run, "--file", bf, env=env)
        check(r.get("ok") and r["units"] == 4 and r["non_play"] == 1, "units-check counts 4 units and 1 non_play " + json.dumps(r)[:200])
        check(list(r["missing_fields"]) == ["R3"] and r["missing_fields"]["R3"] == ["evidence"], "R3 has no evidence: listed")
        check(len(r["overlaps"]) == 1 and r["overlaps"][0]["overlap_s"] == 5.0, "R2 and R3 overlap by 5 s")
        check(r["keep_spans_outside_unit"] and r["keep_spans_outside_unit"][0][0] == "R4", "R4's keep span starts before R4")
        check([x[0] for x in r["uncovered_score_changes"]] == [300.0], "the reset at 300 s lies in no unit (and none of the other changes is listed)")
        check(r["units_holding_no_score_change"] == ["R4"] and r["units_holding_several_score_changes"] == [["R2", 2]], "R4 holds no change, R2 holds two")
        check(r["uncovered_stretches"] == [[290.0, 400.0, 110.0]], "290 to 400 s is covered by no unit and no non_play")
        check(any("overlapping" in x for x in r["look_at"]), "look_at names the overlap")

        # a second block repeats R4 (kept once) and adds R5; sensitive/avoid entries travel to their own files
        block["units"][0]["winner"], block["units"][0]["score_before"], block["units"][0]["score_after"] = "Team | A", "0-0", "1-0"
        block["sensitive"] = [{"rec_from": 30.0, "rec_to": 33.0, "kind": "distress", "what": "x", "region": None, "unit": "R1"}]
        bf.write_text(json.dumps(block), encoding="utf-8")
        (blocks / "block-02.json").write_text(json.dumps({"block": 2, "chunks": [], "rec_from": 400.0, "rec_to": 800.0, "units": [unit("R4", 210.0, 250.0), unit("R5", 400.0, 460.0)],
                                                         "non_play": [], "extras": [{"id": "B02-X01", "rec_from": 410.0, "rec_to": 415.0}], "lexicon_fixes": [["Kai Sinat", "Kai Cenat"]],
                                                         "sensitive": [], "avoid": [{"rec_from": 420.0, "rec_to": 430.0, "kind": "religion", "what": "x"}]}), encoding="utf-8")
        r = cc("units-merge", "--run", run, env=env)
        check(r.get("ok") and r["units"] == 5 and r["blocks"] == 2 and r["extras"] == 1 and r["sensitive"] == 1 and r["avoid"] == 1 and r["duplicate_ids_dropped"] == [["R4", "block-01.json", "block-02.json"]],
              "units-merge: 5 units over 2 blocks, the repeated R4 kept once " + json.dumps(r)[:300])
        rj = json.loads((run / "20-analysis" / "rounds.json").read_text(encoding="utf-8"))
        check([u["id"] for u in rj["units"]] == ["R1", "R2", "R3", "R4", "R5"] and rj["lexicon_fixes"] == [["Kai Sinat", "Kai Cenat"]], "rounds.json is time-ordered and carries the lexicon fixes")
        check(json.loads((run / "20-analysis" / "avoid.json").read_text(encoding="utf-8"))[0]["kind"] == "religion", "avoid.json is written next to rounds.json")
        r = cc("units-merge", "--run", run, env=env)
        check(r.get("ok") is False and "--force" in r.get("error", ""), "units-merge refuses to overwrite rounds.json (it may hold verdicts)")

        verdicts = {"R1": {"keep": "trim", "keep_spans": [[2.0, 63.0]], "keep_why": "because R1"}, "R3": {"keep": "trim", "keep_spans": [[152.0, 208.0]], "keep_why": "because R3"},
                    "R4": {"keep": "skip", "keep_spans": [], "keep_why": "because R4"}, "R5": {"keep": "flash", "keep_spans": [[402.0, 410.0]], "keep_why": "because R5"},
                    "R2": {"keep": "maybe"}, "R99": {"keep": "skip"}}
        vf = tmp / "verdicts.json"
        vf.write_text(json.dumps(verdicts), encoding="utf-8")
        r = cc("units-verdict", "--run", run, "--file", vf, env=env)
        check(r.get("ok") and r["applied"] == 4 and r["unknown_ids"] == ["R99"] and [x[0] for x in r["invalid"]] == ["R2"] and r["units_without_a_keep_level"] == ["R2"],
              "units-verdict applies 4, reports the unknown id and the invalid keep level, and says R2 still has none " + json.dumps(r)[:300])
        vf.write_text(json.dumps({"R2": {"keep": "trim", "keep_spans": [[67.0, 153.0]], "keep_why": "because R2", "used_in": ["S01"]}, "R1": {"used_in": ["S01"]}, "R3": {"used_in": ["S01"]},
                                  "R5": {"used_in": ["S02"], "keep_spans": [[409.0, 400.0]]}}), encoding="utf-8")
        r = cc("units-verdict", "--run", run, "--file", vf, "--add-used-in", env=env)
        check(r.get("ok") and r["applied"] == 3 and [x[0] for x in r["invalid"]] == ["R5"] and r["units_without_a_keep_level_count"] == 0, "a keep span that runs backwards is refused; R2 now has its verdict " + json.dumps(r)[:300])
        vf.write_text(json.dumps({"R5": {"used_in": ["S02"]}}), encoding="utf-8")
        r = cc("units-verdict", "--run", run, "--file", vf, "--add-used-in", env=env)
        check(r.get("ok") and r["applied"] == 1 and r["by_keep"] == {"trim": 3, "skip": 1, "flash": 1}, "the verdicts are in rounds.json: " + json.dumps(r.get("by_keep")))
        check((run / "20-analysis" / "rounds.json.bak").is_file(), "a .bak of the previous rounds.json is kept")
        r = cc("units-check", "--run", run, env=env)
        check(r.get("ok") and r["source"] == "rounds.json" and r["by_keep"] == {"trim": 3, "skip": 1, "flash": 1}, "units-check on rounds.json reads the verdicts " + json.dumps(r)[:200])
        check(r["kept_seconds_by_keep"] == {"trim": 61.0 + 86.0 + 56.0, "skip": 0, "flash": 8.0}, "kept seconds are the sum of the keep spans (61 + 86 + 56, flash 8) " + json.dumps(r["kept_seconds_by_keep"]))
        r = cc("units-table", "--run", run, env=env)
        md = (run / "deliverables" / "rounds.md").read_text(encoding="utf-8")
        check(r.get("ok") and r["units"] == 5 and r["skipped"] == 1 and r["videos"] == ["S01", "S02"], "units-table: 5 units, 1 skipped, 2 videos " + json.dumps(r)[:200])
        check("## Skipped units" in md and "because R4" in md and "- **S01**: R1, R2, R3" in md and "- **S02**: R5" in md and "Team / A" in md,
              "the table lists the skipped unit with its reason, the units per video, and escapes a pipe")
        r = cc("config", "get", "agents.scan_model", env=env)
        check(r.get("ok") and r.get("value") == "haiku", "config get agents.scan_model is haiku (the scan agents' model)")
        integration(env, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
