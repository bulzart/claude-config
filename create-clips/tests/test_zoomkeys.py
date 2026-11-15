"""Regression test of cc_edit.write_zoom_keys: every copy of the timeline holds the SAME zoom keyframes, ids included (no CapCut, no media).

    python tests/test_zoomkeys.py

A CapCut draft keeps its timeline three times (draft_content.json, the draft_info.json mirror and template-2.tmp). The zoom keyframes used to get fresh random ids in each copy, so the
copies differed (7 ids each for one zoomed clip); on a long video the build's repair step (`capcut sync-timelines`) then refused: the root document looked older than the "drifted"
mirrors, because the repair's own rewrites of the three documents take time on a big draft. The three long builds of the first run all stopped there and needed a manual workaround.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_edit  # noqa: E402


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def timeline() -> dict:
    return {"tracks": [{"type": "video", "segments": [
        {"id": "SEG1", "target_timerange": {"start": 0, "duration": 3000000}, "clip": {}},
        {"id": "SEG2", "target_timerange": {"start": 3000000, "duration": 3000000}, "clip": {}},
        {"id": "SEG3", "target_timerange": {"start": 6000000, "duration": 3000000}, "clip": {}}]}], "materials": {}}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-zoomkeys-test-"))
    try:
        d = tmp / "draft"
        d.mkdir()
        for name in ("draft_content.json", "draft_info.json", "template-2.tmp"):
            (d / name).write_text(json.dumps(timeline()), encoding="utf-8")
        zooms = [{"at_s": 0.0, "piece": 1, "keys": [{"t_us": 0, "scale": 1.0, "x": 0.0, "y": 0.0}, {"t_us": 200000, "scale": 1.1, "x": 0.02, "y": 0.0},
                                                    {"t_us": 1400000, "scale": 1.1, "x": 0.02, "y": 0.0}, {"t_us": 1700000, "scale": 1.0, "x": 0.0, "y": 0.0}]},
                 {"at_s": 6.0, "piece": 3, "keys": [{"t_us": 0, "scale": 1.0, "x": 0.0, "y": 0.0}, {"t_us": 300000, "scale": 1.2, "x": -0.05, "y": 0.04},
                                                    {"t_us": 1500000, "scale": 1.0, "x": 0.0, "y": 0.0}]}]
        r = cc_edit.write_zoom_keys(d, zooms, 30)
        check(r["keyed"] == 2 and not r["pieces_without_a_clip"] and [f["clips_keyed"] for f in r["files"]] == [2, 2, 2], "two clips are keyed in each of the three copies " + json.dumps(r)[:200])
        docs = {n: json.loads((d / n).read_text(encoding="utf-8")) for n in ("draft_content.json", "draft_info.json", "template-2.tmp")}
        kf = {n: [s.get("common_keyframes") for s in doc["tracks"][0]["segments"]] for n, doc in docs.items()}
        check(kf["draft_content.json"][0] and kf["draft_content.json"][1] is None and kf["draft_content.json"][2], "clips 1 and 3 carry keyframes, clip 2 none")
        check(kf["draft_info.json"] == kf["draft_content.json"] and kf["template-2.tmp"] == kf["draft_content.json"],
              "the zoom keyframes are identical in the three copies of the timeline, ids included (so the repair's sync-timelines finds no drift)")
        ids = [x for lst in kf["draft_content.json"] if lst for prop in lst for x in [prop["id"]] + [k["id"] for k in prop["keyframe_list"]]]
        check(len(ids) == len(set(ids)) and len(ids) >= 10, f"the ids inside one copy are all different ({len(ids)} ids)")
        check(docs["draft_content.json"] == docs["draft_info.json"] == docs["template-2.tmp"], "the three whole timelines are equal after the zoom keys were written")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
