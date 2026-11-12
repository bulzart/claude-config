"""Regression test of cc_edit.py on a synthetic two-chunk run (no network, no CapCut store touched).

    python tests/test_edit.py            (Python312; ffmpeg on PATH; takes about a minute: the SFX scan is the slow part and is skipped here)

Builds two 12 s test chunks with ffmpeg, a transcript for each, then checks: layout maths, the EDL resolve across a chunk boundary, the censor split and file,
caption cues (masking, replacement), the cut facts, the MCP plan and finish plan, and capcut-finish against a draft in an isolated store (capcut-cli init --drafts).
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
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=900)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    return json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-edit-test-"))
    try:
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs")}
        run = tmp / "runs" / "20261112-000000-testch"
        for n in (1, 2):
            d = run / "10-media" / f"C000{n}"
            d.mkdir(parents=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=60", "-f", "lavfi", "-i",
                            f"sine=frequency={440 * n}:sample_rate=48000", "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "120", "-c:a", "aac", str(d / "chunk.mp4")],
                           check=True)
        (run / "00-inventory").mkdir(parents=True)
        (run / "00-inventory" / "chunks.json").write_text(json.dumps([
            {"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 12.0, "status": "done"},
            {"id": "C0002", "index": 2, "rec_start_s": 12.0, "duration_s": 12.0, "status": "done", "gap_before_s": 0}]), encoding="utf-8")
        (run / "state.json").write_text('{"schema":"cc/1","channel":"testch"}', encoding="utf-8")
        w = lambda s, e, t: {"w": t, "s": s, "e": e, "p": 1}  # noqa: E731
        (run / "10-media" / "C0001" / "transcript.json").write_text(json.dumps({"segments": [{"words": [
            w(1.0, 1.4, "Hello"), w(1.5, 1.9, "chat,"), w(2.0, 2.2, "this"), w(2.3, 2.4, "is"), w(2.5, 3.0, "wild."), w(3.4, 4.0, "Absolutely"), w(4.1, 4.6, "crazy")]}]}), encoding="utf-8")
        (run / "10-media" / "C0002" / "transcript.json").write_text(json.dumps({"segments": [{"words": [
            w(0.5, 0.9, "Damn"), w(1.0, 1.2, "Kai"), w(1.3, 1.6, "Sinat"), w(1.7, 2.1, "shit.")]}]}), encoding="utf-8")

        r = cc("layout-calc", "--src", "1280x720", "--canvas", "1080x1920", "--mode", "fill", "--focus", "0.3,0.5")
        check(abs(r["scale"] - 3.16049) < 1e-3 and abs(r["posX"] - 1.2642) < 1e-3 and not r["clamped"], "layout-calc fill focus 0.3")
        r = cc("layout-calc", "--src", "1280x720", "--canvas", "1080x1920", "--mode", "fill", "--focus", "0.0,0.5")
        check(r["clamped"], "layout-calc clamps a focus at the edge")

        edl = {"schema": "cc-edl/1", "video": "S01", "kind": "short", "layout": {"mode": "fill", "focus": [0.5, 0.5]},
               "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0, "zoom": [{"at": 1.0, "to": 1.2, "in": 0.2, "hold": 1.0, "out": 0.2}]},
                            {"id": "s2", "rec_from": 10.0, "rec_to": 15.0, "transition_in": {"slug": "flash", "dur": 0.2},
                             "censor": [{"rec_from": 11.0, "rec_to": 12.5, "region": [0.1, 0.1, 0.4, 0.4], "style": "blur", "why": "test"}],
                             "layout": {"mode": "fill", "focus": [0.3, 0.5]}}],
               "captions": {"mask_terms": ["shit"], "highlight_words": ["wild"], "replace": [["Kai Sinat", "Kai Cenat"]]}}
        out = run / "60-outputs" / "S01"
        out.mkdir(parents=True)
        sfx_file = Path("C:/Users/Bulzart/Documents/sound_effects/vine boom.mp3")
        if sfx_file.is_file():                                  # one sound effect on its own lane (skipped on a PC without the folder)
            edl["sfx"] = [{"file": str(sfx_file).replace("\\", "/"), "at": {"seg": "s1", "t": 1.2}, "volume": 0.7, "why": "test"}]
        (out / "edl.json").write_text(json.dumps(edl), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", out / "edl.json", "--make-censor", env=env)
        check(r.get("ok"), "edl-check ok: " + json.dumps(r.get("warnings")))
        check(r["totals"]["pieces"] == 5 and r["totals"]["chunks_used"] == ["C0001", "C0002"], "five pieces over two chunks (the censor span crosses the boundary)")
        check(abs(r["totals"]["duration_s"] - 9.1) < 0.01, "duration 9.1 s")
        res = json.loads((out / "resolved.json").read_text(encoding="utf-8"))
        check(len(list((run / "30-assets" / "censor").glob("C000*-*.mp4"))) == 2, "two blurred files made")
        check(all(abs(p["at"] - sum(q["dur_out"] for q in res["pieces"][:i])) < 1e-6 for i, p in enumerate(res["pieces"])), "pieces are contiguous on the output timeline")
        plan = json.loads((out / "mcp-plan.json").read_text(encoding="utf-8"))
        check(sum(1 for o in plan["ops"] if o["op"] == "add_video") == 5, "mcp plan has 5 add_video ops")
        fin = json.loads((out / "finish.json").read_text(encoding="utf-8"))
        check(len(fin["zoom"]) == 1 and fin["transitions"][0]["refused"] is None, "finish plan: one zoom, the flash transition accepted")
        r = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
        srt = (out / "captions.srt").read_text(encoding="utf-8")
        check(r.get("ok") and "S***" in srt and "KAI CENAT" in srt, "captions: masking and the lexicon replace applied")

        capcut = shutil.which("capcut")
        if capcut:
            store = tmp / "drafts"
            store.mkdir()
            r = cc("capcut-compose", "--run", run, "--video", "S01", "--name", "cctest", "--store", store, env=env)
            check(r.get("ok") and r.get("video_segments_retargeted") == 5, "capcut-compose: one command, 5 video segments pointed at the real chunk files " + json.dumps(r)[:700])
            c = json.loads((store / "cctest" / "draft_content.json").read_text(encoding="utf-8"))
            vids = c["materials"].get("videos", [])
            check(vids and all(m["path"].endswith(("chunk.mp4", ".mp4")) and "placeholder" not in m["path"] for m in vids), "no video material points at the placeholder")
            check(not (store / "cctest" / "assets" / "video").exists(), "no media file was copied into the draft's assets/video")
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest", "--video", "S01", env=env)
            check(r.get("ok"), "capcut-finish ok on the composed draft")
            c = json.loads((store / "cctest" / "draft_content.json").read_text(encoding="utf-8"))
            texts = c["materials"].get("texts", [])
            check(len(texts) == len(json.loads((out / "captions.json").read_text(encoding="utf-8"))["cues"]), "one text per caption cue in the draft")
            seg0 = [t for t in c["tracks"] if t["type"] == "video"][0]["segments"][0]
            check(any(k["property_type"] == "KFTypeScaleX" for k in seg0.get("common_keyframes", [])), "the zoom keyframes are on the first clip")
            lint = subprocess.run([capcut, "lint", str(store / "cctest")], capture_output=True, text=True)
            check('"errors":0' in lint.stdout.replace(" ", ""), "capcut lint: 0 errors")
            if sfx_file.is_file():
                check(any(t["type"] == "audio" and t.get("segments") for t in c["tracks"]), "the sound effect is on an audio track")
            # NOT tested here: compose into the real CapCut store (its `auto` seeding from the newest app-authored project); the first real build is that check
        else:
            print("skip capcut-compose/finish (capcut-cli not on PATH)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
