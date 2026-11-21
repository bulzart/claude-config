"""Tests of the selective music step (cc_music.py: `cc.py music`, `music-claim`, `music-setup`) and the resolver's `mute` (cc_edit.py).
A generated run of two chunks: a quiet noise bed, then a bass line over a 120 BPM kick and hi-hat across the chunk join, then the bed again. Checked: the claims
lookup, the two scores (identity: one method counts once, 80 without version-specific evidence, a close competitor caps at 60; risk: only items naming
this recording, copies of one source once, caps for supporting-only / unverified-only / contradictory evidence, a licence), outcomes A-F, identity evidence
bound to its interval, the lyrics and MusicBrainz lookups (stand-ins: nothing is sent), the residual checks (the music level where nobody speaks, a singer
under his words), the detection on the kept footage only, the same interval found by a
long and a short video (the second analyses nothing: the windows are cached), the EDL patch (a mute span plus the cleaned audio on a lane, replaced and
never stacked, taken back when the claim is gone, a segment at another speed left alone), the failure branch (no separation: the original sound stays,
`attention`) and, when the separation's Python is on this PC, the real model on the GPU: separated, checked, patched, resolved by `edl-check` with the
muted piece at volume 0, then reused without a second separation. Mocked claims only test the branches; they say nothing about a real song.
Run: python tests/test_music.py"""
import json

import numpy as np
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_music as M  # noqa: E402
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
    return json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}


MUSIC = ("0.35*sin(2*PI*(55+27.5*mod(floor(t/2),2))*t)+0.15*sin(2*PI*(110+55*mod(floor(t/2),2))*t)+0.7*sin(2*PI*60*t)*exp(-30*mod(t,0.5))"
         "+0.08*sin(2*PI*5000*t)*exp(-80*mod(t+0.25,0.5))")      # a bass line, a kick on every beat and a hi-hat between: instruments, no voice


def make_chunk(path: Path, parts: list) -> None:
    """parts: [("bed"|"music", seconds)]; a 320x180 black picture."""
    ins, labels = [], []
    for i, (kind, d) in enumerate(parts):
        src = f"aevalsrc='{MUSIC}':s=44100:d={d}" if kind == "music" else f"anoisesrc=color=brown:amplitude=0.02:sample_rate=44100:duration={d}"
        ins += ["-f", "lavfi", "-i", src]
        labels.append(f"[{i}:a]")
    total = sum(d for _, d in parts)
    ins += ["-f", "lavfi", "-i", f"color=c=black:s=320x180:r=30:d={total}"]
    fc = "".join(labels) + f"concat=n={len(parts)}:v=0:a=1,aformat=channel_layouts=stereo[a]"
    subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", f"{len(parts)}:v", "-map", "[a]", "-c:v", "libx264",
                    "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(path)], check=True, capture_output=True)


def make_run(tmp: Path) -> Path:
    run = tmp / "runs" / "20261121-000000-musictest"
    (run / "00-inventory").mkdir(parents=True)
    (run / "20-analysis").mkdir(parents=True)
    chunks = [{"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 60.0, "status": "done"},
              {"id": "C0002", "index": 2, "rec_start_s": 60.0, "duration_s": 60.0, "status": "done"}]
    (run / "00-inventory" / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    (run / "state.json").write_text('{"schema":"cc/1","channel":"musictest","mode":"streamer"}', encoding="utf-8")
    for cid, parts in (("C0001", [("bed", 30), ("music", 30)]), ("C0002", [("music", 20), ("bed", 40)])):
        d = run / "10-media" / cid
        d.mkdir(parents=True)
        make_chunk(d / "chunk.mp4", parts)
        (d / "transcript.json").write_text(json.dumps({"segments": []}), encoding="utf-8")
    (run / "20-analysis" / "avoid.json").write_text(json.dumps([{"rec_from": 30, "rec_to": 80, "kind": "music", "what": "a test tone on the radio"}]),
                                                    encoding="utf-8")
    return run


def args(edl, apply=False, force=False, spans=None):
    return SimpleNamespace(edl=[str(e) for e in edl] if edl else None, apply=apply, force=force, spans=spans)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc_music_test_"))
    M.CLAIMS = tmp / "claims.json"
    S = M.songid
    S.EVIDENCE, S.CACHE = tmp / "music-evidence.json", tmp / "music-ident-cache.json"      # never the real register or cache
    S.LYR_CACHE, S.MB_CACHE = tmp / "lyrics-check-cache.json", tmp / "musicbrainz-cache.json"
    os.environ["CC_ALLOW_FIXTURES"] = "1"                 # these tests use labelled fixtures; ordinary runs ignore them
    os.environ["CC_NAFP_INDEX"] = str(tmp / "nafp-none")      # never the real reference index
    real_rec = S.rec_settings
    S.rec_settings = lambda: {**S.REC_DEFAULTS}                                           # no service unless a test sets one
    try:
        # ---------------------------------------------------------------- the risk lookup (no audio)
        claims = [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "test"},
                  {"id": "M002", "title": "Free Song", "artist": "Lab", "status": "cleared", "evidence": "test"}]
        check(M.risk_of(None, claims)["status"] == "unknown", "not identified: unknown")
        check(M.risk_of({"title": "Test Tone", "artist": "Lab", "confidence": "low"}, claims)["status"] == "unknown", "a low-confidence guess: unknown, never removed")
        check(M.risk_of({"title": "test tone!", "artist": "LAB", "confidence": "high"}, claims)["status"] == "confirmed", "a claim on record (names normalised): confirmed")
        check(M.risk_of({"title": "Free Song", "artist": "Lab", "confidence": "high"}, claims)["status"] == "none", "cleared on record: none (still not a guarantee)")
        check(M.risk_of({"title": "Other", "artist": "X", "confidence": "high"}, claims)["status"] == "none", "identified, nothing on record: none, left as it is")
        check(M.parse_spans("0:01:00-0:02:00, 30-40") == [[60.0, 120.0], [30.0, 40.0]], "spans in H:MM:SS and seconds")
        e = {"segments": [{"id": "a", "rec_from": 10, "rec_to": 20}, {"id": "b", "rec_from": 100, "rec_to": 130, "speed": 2.0}]}
        check(M.out_times(e, 15, 120) == [[5.0, 10.0, "a"], [10.0, 20.0, "b"]], "where rec time plays in the video, speeds included")

        # ---------------------------------------------------------------- the patch (no audio)
        base = {"segments": [{"id": "s1", "rec_from": 20.0, "rec_to": 100.0, "zoom": [{"at": 5.0, "to": 1.2}], "volume": 0.8,
                              "mute": [{"rec_from": 90.0, "rec_to": 95.0, "why": "the builder's own"}]},
                             {"id": "s2", "rec_from": 100.0, "rec_to": 110.0, "speed": 1.5}],
                "sfx": [{"name": "boom", "at": {"seg": "s1", "t": 2.0}}]}
        cl = [{"rec_from": 29.0, "rec_to": 81.0, "label": "Test Tone", "sub_file": lambda a, b: f"clean@{a:.2f}-{b:.2f}.wav"},
              {"rec_from": 99.0, "rec_to": 105.0, "label": "Test Tone", "sub_file": lambda a, b: f"clean@{a:.2f}-{b:.2f}.wav"}]
        p1, sk = M.patch_edl(base, cl)
        s1 = p1["segments"][0]
        mus = [m for m in s1["mute"] if m.get("music")]
        lane = [x for x in p1["sfx"] if x.get("music_clean")]
        check(len(p1["segments"]) == 2 and s1["zoom"] == base["segments"][0]["zoom"], "the patch never splits a segment, so its zoom stays one envelope")
        check(len(mus) == 2 and (mus[0]["rec_from"], mus[0]["rec_to"]) == (29.0, 81.0) and any(not m.get("music") for m in s1["mute"]),
              "a mute span per cleaned span inside the segment, the builder's own mute kept: " + json.dumps(s1["mute"]))
        check(len(lane) == 2 and lane[0]["at"] == {"seg": "s1", "t": 9.0} and lane[0]["dur"] == 52.0 and lane[0]["volume"] == 0.8,
              "the cleaned audio sits where the span plays, at the segment's volume: " + json.dumps(lane[0]))
        check(sk and sk[0]["seg"] == "s2" and "mute" not in p1["segments"][1], "a segment at another speed keeps its sound and is reported")
        p2, _ = M.patch_edl(p1, cl)
        check(json.dumps(p2, sort_keys=True) == json.dumps(p1, sort_keys=True), "patching again replaces the patch, never stacks it")
        p3 = M.strip_patch(p2)
        check(json.dumps(p3, sort_keys=True) == json.dumps(base, sort_keys=True), "strip_patch gives back the EDL without the music patch")

        # ---------------------------------------------------------------- a generated run: detection, sharing, failure branch
        run = make_run(tmp)
        out_l, out_s = run / "60-outputs" / "L01", run / "60-outputs" / "S01"
        out_l.mkdir(parents=True)
        out_s.mkdir(parents=True)
        long_edl = {"schema": "cc-edl/1", "video": "L01", "kind": "long", "segments": [{"id": "s1", "rec_from": 20.0, "rec_to": 100.0, "zoom": [{"at": 30.0, "to": 1.15}]}],
                    "music": [{"rec_from": 30.0, "rec_to": 80.0, "title": "Test Tone", "artist": "Lab", "confidence": "high", "evidence": "test fixture"}]}
        short_edl = {"schema": "cc-edl/1", "video": "L02", "kind": "long", "segments": [{"id": "s1", "rec_from": 45.0, "rec_to": 70.0}]}     # a second video inside the song
        (out_l / "edl.json").write_text(json.dumps(long_edl), encoding="utf-8")
        (out_s / "edl.json").write_text(json.dumps(short_edl), encoding="utf-8")
        cfg = {**M.settings(), "analysis": False}       # the analysis (a temporary separation + Whisper) is tested with the real model below
        adir = run / "30-assets" / "music"
        adir.mkdir(parents=True)
        M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
        r0 = M._music(run, cfg, adir, args([out_s / "edl.json"]))
        iv0 = [m for v in r0["videos"] for m in v["music"]]
        sj = json.loads((out_s / "music.json").read_text(encoding="utf-8"))
        check(len(iv0) == 1 and 26 <= iv0[0]["rec"][0] <= 34 and 76 <= iv0[0]["rec"][1] <= 84,
              "a video inside the song: the interval is followed past its edges to where the music ends: " + json.dumps([m["rec"] for m in iv0]))
        check(iv0 and iv0[0]["risk"] == "unknown" and iv0[0]["action"] == "review" and sj["review"] == 1, "not identified: listed for review, its sound left as it is")
        check(any("test tone" in e_["text"] for e_ in sj["music"][0]["evidence"]) and len(sj["music"][0]["look_at"]) == 3,
              "the evidence to name it comes along (a miner's avoid line) and three times to look at")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        iv = [m for v in r["videos"] for m in v["music"]]
        check(len(iv) == 1 and iv[0]["rec"] == iv0[0]["rec"], "the bass and beat are found across the chunk join, the bed is not, the same interval as the other video's: "
              + json.dumps([m["rec"] for m in iv]))
        check(iv and iv[0]["risk"] == "unknown" and iv[0]["action"] == "review" and "research: identity" in iv[0]["status"],
              "named by a builder only (a weak item, 50): identity below 85 (D), left as it is, listed for research: " + iv[0]["status"][:100])
        check(any(x["rec"] == iv[0]["rec"] and (x.get("candidate") or {}).get("title") == "Test Tone" and x["needs"] == "identity" for x in r.get("research") or []),
              "the answer lists the interval for the research step, with its candidate")
        check(r["analysed_s"] < 140, f"only the kept footage (and a little past its edges) is analysed: {r['analysed_s']} s")
        rs = M._music(run, cfg, adir, args([out_s / "edl.json"]))
        sj = json.loads((out_s / "music.json").read_text(encoding="utf-8"))
        check(rs["analysed_s"] == 0 and sj["music"][0]["identified"] and sj["music"][0]["identified"]["by"] == "L01" and sj["music"][0]["action"] == "review",
              f"the other video again: nothing analysed (cached), and it knows the song L01's builder named: {rs['analysed_s']} s, {sj['music'][0]['identified']}")
        M.CLAIMS.write_text(json.dumps({"claims": claims}), encoding="utf-8")
        rid_tt = S.ensure_recording({"title": "Test Tone", "artist": "Lab"})
        S.add_id_evidence(rid_tt, "onscreen_title", "the radio display reads Lab - Test Tone (TEST FIXTURE)", "test fixture", run=run.name, rec=[30, 80])
        rb = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        mb = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        check(mb["outcome"] == "A" and mb["action"] == "remove" and mb["id_score"] >= 85 and mb["risk_score"] >= 85,
              f"a claim on record (98) and the title on screen with the builder's naming (identity {mb['id_score']}): outcome A, removal attempted")
        real_python = M.music_python
        M.music_python = lambda c: None
        rf = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
        vl = rf["videos"][0]
        check(vl["attention"] == 1 and "separation failed" in vl["music"][0]["status"] and not rf["videos"][0]["patched"],
              "no separation possible: attention, and the EDL is not touched: " + vl["music"][0]["status"][:100])
        check(json.loads((out_l / "edl.json").read_text(encoding="utf-8")) == long_edl, "the EDL on disk is unchanged after a failed separation")
        M.music_python = real_python
        (adir / "separated.json").unlink(missing_ok=True)

        # ---------------------------------------------------------------- the real model, when this PC has it
        py = M.music_python(cfg)
        probe = M._probe(py) if py else {}
        if not probe.get("hdemucs"):
            print("skip the real-model part: no Python with torch + torchaudio here (`cc.py music-setup`)")
        else:
            ra = M._music(run, cfg, adir, args([out_l / "edl.json", out_s / "edl.json"], apply=True))
            st = {v["video"]: v for v in ra["videos"]}
            check(ra["separation"] and ra["separation"]["ok"] and ra["by_action"]["remove"] == 2,
                  "a claim on record: the shared span is separated once for both videos: " + json.dumps(ra["separation"])[:160])
            check("removed (verified" in st["L01"]["music"][0]["status"] and "removed (verified" in st["L02"]["music"][0]["status"],
                  "the cleaned audio passed its check, and the other video uses the song L01's builder named (shared): " + st["L02"]["music"][0]["status"][:120])
            pl = json.loads((out_l / "edl.json").read_text(encoding="utf-8"))
            mu = [m for m in pl["segments"][0].get("mute", []) if m.get("music")]
            ln = [x for x in pl.get("sfx", []) if x.get("music_clean")]
            check(len(mu) == 1 and len(ln) == 1 and Path(ln[0]["file"]).is_file() and (out_l / "edl.pre-music.json").is_file(),
                  "the long video's EDL: one mute span, the cleaned audio file on a lane, a backup of the EDL")
            sep = json.loads((adir / "separated.json").read_text(encoding="utf-8"))
            k = next(iter(sep))
            ch = sep[k]["verify"]["checks"]
            check(ch["duration"]["ok"] and ch["sync"]["ok"] and max(ch["sync"]["edge_corr"]) > 0.95 and ch["music_left"]["ok"],
                  "checked: same length, in sync, no longer reads as music: " + json.dumps(ch)[:200])
            chk = cc("edl-check", "--run", run, "--edl", out_l / "edl.json")
            res = json.loads((out_l / "resolved.json").read_text(encoding="utf-8")) if (out_l / "resolved.json").is_file() else {}
            vols = [(round(p["rec_from"], 1), p["volume"]) for p in res.get("pieces", [])]
            check(chk.get("ok") and chk["totals"]["segments"] == 1 and any(v == 0.0 for _, v in vols) and any(v == 1.0 for _, v in vols) and chk["totals"]["sfx"] == 1,
                  "edl-check resolves it: one segment, its muted piece at volume 0, the rest at 1, the cleaned audio on a lane: " + json.dumps(vols))
            again = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
            pl2 = json.loads((out_l / "edl.json").read_text(encoding="utf-8"))
            check(again["separation"] is None and again["analysed_s"] == 0 and pl2 == pl, "run again: nothing analysed or separated, the EDL the same (resume)")
            an = M.analyse(run, M.load_chunks(run), [(30.0, 80.0)], {**cfg, "analysis": True}, adir)
            ent = an.get("30.00-80.00") or {}
            an2 = M.analyse(run, M.load_chunks(run), [(30.0, 80.0)], {**cfg, "analysis": True}, adir)
            check(ent.get("ok") and ent.get("sung") is False and (ent.get("vocal_presence_db") or 0) < -20 and (adir / "analysis" / "accompaniment-30.00-80.00.wav").is_file()
                  and an2["30.00-80.00"]["sig"] == ent["sig"],
                  f"the analysis of an instrumental: voices and accompaniment apart, not sung (voices {ent.get('vocal_presence_db')} dB under the music), cached")
            M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
            back = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
            pl3 = json.loads((out_l / "edl.json").read_text(encoding="utf-8"))
            check(not any(m.get("music") for m in pl3["segments"][0].get("mute", [])) and not any(x.get("music_clean") for x in pl3.get("sfx", []))
                  and back["videos"][0]["music"][0]["action"] in ("keep", "review"), "the claim taken off the register: the original sound comes back")
        # ---------------------------------------------------------------- the SAM escalation (stand-ins: nothing loaded, no GPU)
        M.CLAIMS.write_text(json.dumps({"claims": [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "TEST FIXTURE ONLY"}]}),
                            encoding="utf-8")
        real_fns = (M.separate_spans, M.verify, M.sam_spans, M.sam_ready)
        sam_calls = []

        def fake_sep(jobs, cfg_, work):
            import soundfile as sf
            for j in jobs:
                d_, sr_ = sf.read(j["wav_in"], dtype="float32", always_2d=True)
                sf.write(j["wav_out"], d_ * 0.5, sr_)
            return {"ok": True, "model": "stand-in demucs", "device": "cpu", "results": [{"id": j["id"], "ok": True, "seconds": 0.1} for j in jobs]}

        def fake_sam(jobs, cfg_, work):
            sam_calls.append([j["id"] for j in jobs])
            import soundfile as sf
            for j in jobs:
                d_, sr_ = sf.read(j["wav_in"], dtype="float32", always_2d=True)
                sf.write(j["wav_out"], d_ * 0.25, sr_)
            return {"ok": True, "model": "facebook/sam-audio-base", "load_s": 0.1, "peak_vram_mb": 1,
                    "results": [{"id": j["id"], "ok": True, "seconds": 0.1} for j in jobs]}

        def verify_sam_only(path, orig, sr, words, cfg_, sung=False, method="hdemucs"):
            ok = method == "sam-audio-base"
            return {"ok": ok, "checks": {"duration": {"ok": True}, "sync": {"ok": True}, "singer_under_speech": {"ok": ok}}}
        M.separate_spans, M.verify, M.sam_spans, M.sam_ready = fake_sep, verify_sam_only, fake_sam, (lambda c: {"ok": True, "why": None})
        try:
            (adir / "separated.json").unlink(missing_ok=True)
            (out_l / "edl.json").write_text(json.dumps(long_edl), encoding="utf-8")
            r1 = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
            mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
            ent = next(iter(json.loads((adir / "separated.json").read_text(encoding="utf-8")).values()))
            lane = [x for x in json.loads((out_l / "edl.json").read_text(encoding="utf-8")).get("sfx", []) if x.get("music_clean")]
            check(sam_calls and r1["escalated"] == 1 and ent.get("method") == "sam-audio-base" and ent["first_try"]["verify"]["ok"] is False
                  and "removed with SAM Audio Base" in mj["status"] and mj["attention"] and lane and ".sam" in lane[0]["file"],
                  "Demucs fails the singer check: the span goes to SAM, passes, and the EDL uses SAM's audio (listed for a listen): " + mj["status"][:90])
            M.verify = lambda *a_, **k_: {"ok": False, "checks": {"duration": {"ok": True}, "sync": {"ok": True}, "singer_under_speech": {"ok": False}}}
            M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True, force=True))
            mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
            pl = json.loads((out_l / "edl.json").read_text(encoding="utf-8"))
            check(mj.get("unresolved") and "SAM Audio Base was tried too and failed" in mj["status"] and mj["escalation"].get("ok") is False
                  and not any(x.get("music_clean") for x in pl.get("sfx", [])),
                  "SAM fails its checks too: UNRESOLVED, both attempts recorded, the original sound back in the EDL: " + mj["status"][:100])
            M.sam_ready = lambda c: {"ok": False, "why": "SAM Audio's environment is not set up (test)"}
            M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True, force=True))
            mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
            check(mj.get("unresolved") and "SAM Audio was not tried: SAM Audio's environment is not set up (test)" in mj["status"],
                  "SAM not available: UNRESOLVED with the reason it was not tried")
        finally:
            M.separate_spans, M.verify, M.sam_spans, M.sam_ready = real_fns
        check(M.escalation_targets({"k": {"verify": {"ok": False, "checks": {"sync": {"ok": False}, "singer_under_speech": {"ok": False}}}}}, ["k"]) == []
              and M.escalation_targets({"k": {"verify": {"ok": False, "checks": {"music_only": {"ok": False}}}}}, ["k"]) == [("k", ["music_only"])]
              and M.escalation_targets({"k": {"error": "x", "verify": {"ok": False}}}, ["k"]) == [],
              "a wrong length or offset is a fault, never escalated; music left where nobody speaks is; a failed separation is not")
        s_off = M.sam_ready({**M.settings(), "escalate": []})
        s_nopy = M.sam_ready({**M.settings(), "sam": {**M.sam_settings(M.settings()), "python": "C:/nowhere/python.exe"}})
        check(not s_off["ok"] and "switched off" in s_off["why"] and not s_nopy["ok"] and "environment" in s_nopy["why"],
              "SAM's readiness says why not: " + s_off["why"][:50] + " | " + s_nopy["why"][:60])
        (out_l / "edl.json").write_text(json.dumps(long_edl), encoding="utf-8")
        for f in out_l.glob("edl.pre-music.json"):
            f.unlink()
        (adir / "separated.json").unlink(missing_ok=True)
        # the real SAM Audio Base, when this PC has it (about 25 s and 8.3 GB of GPU memory): one span, the gate, the same length back
        if M.sam_ready(M.settings())["ok"]:
            import soundfile as sf
            mixw = tmp / "sam-mix.wav"
            sf.write(str(mixw), M.span_audio(run, M.load_chunks(run), 40, 48, 44100, 2).T, 44100)
            rs_ = M.sam_spans([{"id": "t1", "sig": "test", "wav_in": str(mixw), "wav_out": str(tmp / "sam-out.wav"), "words": [[1.0, 2.0]],
                                "gap_gate_s": 2.0, "gate_db": -40.0, "crossfade_s": 0.15, "description": "man speaking", "keep": "target", "chunk_s": 10.0}],
                              M.settings(), tmp)
            x_ = (rs_.get("results") or [{}])[0]
            err_ = str(rs_.get("error"))
            if not rs_.get("ok") and ("GPU" in err_ or "[memguard]" in err_):
                # the PC's state, not the code: the GPU busy, or the memory guard stopped SAM (always full precision; GPU memory counts as committed
                # memory on Windows: other open programs can leave too little)
                print("SKIP the real SAM run (this PC's memory or GPU, not the code): " + err_[-220:].replace(chr(10), " | "))
            else:
                d_o, _ = sf.read(str(tmp / "sam-out.wav"), dtype="float32", always_2d=True) if (tmp / "sam-out.wav").is_file() else (np.zeros((0, 2)), 0)
                check(rs_.get("ok") and x_.get("ok") and len(d_o) == 8 * 44100 and d_o.shape[1] == 2 and rs_.get("peak_vram_mb"),
                      f"the real SAM Audio Base: loaded in {rs_.get('load_s')} s, 8 s separated in {x_.get('seconds')} s, stereo, same length, "
                      f"GPU peak {rs_.get('peak_vram_mb')} MB, {rs_.get('dtype')}")
            check(rs_.get("dtype") in (None, "float32") and "dtype_fallback" not in rs_ and M.sam_settings({"sam": {"dtype": "bfloat16"}})["dtype"] == "float32",
                  "SAM always runs in full precision: no lighter retry, and a config asking for bfloat16 is ignored")
        else:
            print("skip the real SAM run: " + M.sam_ready(M.settings())["why"])
        # a memory-guard stop (stand-ins: the guard's messages, a GPU lease): one full-precision try, no lighter retry, the reason in plain words
        import contextlib
        import subprocess as sp_
        import cc_gpu
        real_run_, real_lease_ = M.subprocess.run, cc_gpu.lease
        sam_calls = []

        def fake_run_(cmd, **kw):
            if any("sam_separate.py" in str(c_) for c_ in cmd):
                sam_calls.append(cmd)
                return sp_.CompletedProcess(cmd, 1, "", "[memguard] STOPPED: free commit 0.9 GB (floor 1.0 GB)\n[memguard] Close some programs (browser "
                                                         "tabs, chat apps) and start it again.\n[memguard] peak memory used by the app: 12.40 GB (cap 16.0 GB)\n")
            return real_run_(cmd, **kw)

        @contextlib.contextmanager
        def fake_lease_(*a_, **k_):
            yield {"device": "cuda", "why": None}
        M.subprocess.run, cc_gpu.lease = fake_run_, fake_lease_
        try:
            rs_m = M.sam_spans([{"id": "m1", "sig": "m", "wav_in": str(tmp / "none.wav"), "wav_out": str(tmp / "never.wav")}], M.settings(), tmp)
        finally:
            M.subprocess.run, cc_gpu.lease = real_run_, real_lease_
        job_m = json.loads((tmp / "sam-job.json").read_text(encoding="utf-8"))
        check(not rs_m["ok"] and rs_m.get("memory_stop") and "close other programs" in rs_m["error"] and len(sam_calls) == 1 and job_m["dtype"] == "float32"
              and "16" in " ".join(str(c_) for c_ in sam_calls[0]),
              "a memory-guard stop: one full-precision try only (cap 16 GB), no lighter retry, the reason in plain words: " + rs_m["error"][:110])
        r = cc("music-claim", "--add", "Someone - Something")
        check(r.get("ok") is False, "a claim without its evidence is refused")

        # ---------------------------------------------------------------- recognition by fingerprint, and the gate: only a claimed recording on record
        M.INDEX_DIR = tmp / "music-index"
        M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
        for f in (adir / "fingerprint-matches.json", adir / "separated.json"):
            f.unlink(missing_ok=True)
        plain = {**long_edl}
        plain.pop("music", None)
        (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")
        for f in out_l.glob("edl.pre-music.json"):
            f.unlink()
        y, src = M._claim_audio(SimpleNamespace(file=None, run=str(run), rec="40-60", video=None, at=None))
        check(26 <= len(y) / M.FP_SR - 0 and "rec" in src, f"a claim's audio from a run reaches out to the whole music interval around it: {src}")
        ref = M.fp_add(y, {"claim": "M001", "title": "Test Tone", "artist": "Lab", "source": src})
        rng = __import__("numpy").random.default_rng(1)
        noise = rng.normal(0, 0.05, M.FP_SR * 10).astype("float32")
        m_noise = M.fp_match(M.fp_load(), noise) or {}
        m_song = M.fp_match(M.fp_load(), M.span_audio(run, M.load_chunks(run), 50, 60, M.FP_SR, 1)[0]) or {}
        check(m_song.get("score", 0) >= M.settings()["fp_high"] and m_noise.get("score", 0) < M.settings()["fp_high"],
              f"the recording matches its own fingerprint, noise does not: song {m_song.get('score')}, noise {m_noise.get('score')}")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        row = r["videos"][0]["music"][0]
        check(row["risk"] != "confirmed" and row["action"] in ("keep", "review"), "a fingerprint whose claim is not on record never makes music risky: left as it is ("
              + row["risk"] + ")")
        M.CLAIMS.write_text(json.dumps({"claims": [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "TEST FIXTURE ONLY",
                                                    "reference": ref}]}), encoding="utf-8")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        check(mj["outcome"] == "A" and mj["identified"]["by"] == "fingerprint" and mj["identified"]["claim"] == "M001" and mj["action"] == "remove",
              "the claimed recording is recognised by its fingerprint, no title needed, and only then becomes eligible for removal: " + mj["risk"]["why"])
        check(r["seconds"]["recognise"] is not None and r["claimed_recordings_fingerprinted"] == 1, "the recognition step is timed and counted")
        M.CLAIMS.write_text(json.dumps({"claims": [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "cleared", "evidence": "TEST", "reference": ref}]}),
                            encoding="utf-8")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        check(r["videos"][0]["music"][0]["action"] == "keep", "the same recording marked cleared on record: left as it is (and still not called safe)")
        M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
        named = {**plain, "music": [{"rec_from": 30.0, "rec_to": 80.0, "title": "A Famous Song", "artist": "Big Star", "confidence": "high", "evidence": "test"}]}
        (out_l / "edl.json").write_text(json.dumps(named), encoding="utf-8")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
        mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        check(r["videos"][0]["music"][0]["action"] in ("keep", "review") and r["separation"] is None and not r["videos"][0]["patched"],
              "a famous song named with high confidence but no claim on record: nothing separated, the EDL untouched")
        check(mj["identified"]["title"] == "Test Tone" and mj["outcome"] != "F" and any(c["title"] == "A Famous Song" for c in mj["candidates"]),
              "a builder's guess (50) against a fingerprint match: the fingerprint's recording, no contradiction (the guess is listed): "
              + json.dumps([(c["title"], c["id_score"]) for c in mj["candidates"]]))
        wav = tmp / "claimed.wav"
        import soundfile as sf
        sf.write(str(wav), M.span_audio(run, M.load_chunks(run), 30, 80, 44100, 1)[0], 44100)
        env = {**os.environ, "CC_MUSIC_CLAIMS": str(tmp / "cli" / "music-claims.json")}
        cp = subprocess.run([PY, str(CC), "music-claim", "--add", "Lab - Test Tone", "--evidence", "TEST FIXTURE ONLY", "--claimant", "Test Claimant",
                             "--policy", "monetize", "--record", "C:/nowhere/notice.png", "--file", str(wav), "--at", "0:05-0:25"], capture_output=True, text=True,
                            encoding="utf-8", env=env)
        rr = json.loads([ln for ln in cp.stdout.splitlines() if ln.startswith("{")][-1])
        ent = rr.get("added") or {}
        check(rr.get("ok") and ent.get("claimant") == "Test Claimant" and ent.get("records") == ["C:/nowhere/notice.png"] and (ent.get("reference") or {}).get("hashes", 0) > 50,
              "music-claim --file --at keeps the claim's details and a fingerprint of the claimed part: " + json.dumps(ent)[:200])
        cp = subprocess.run([PY, str(CC), "music-claim", "--remove", ent.get("id", "M001")], capture_output=True, text=True, encoding="utf-8", env=env)
        rr = json.loads([ln for ln in cp.stdout.splitlines() if ln.startswith("{")][-1])
        check(rr.get("removed") == 1 and rr.get("fingerprints_removed") == 1, "removing a claim removes its fingerprint too")

        # ---------------------------------------------------------------- SHORTS ARE NEVER TOUCHED (the user, 2026-11-21)
        out_sh = run / "60-outputs" / "S01"
        out_sh.mkdir(parents=True, exist_ok=True)
        sh_edl = {"schema": "cc-edl/1", "video": "S01", "kind": "short", "segments": [{"id": "s1", "rec_from": 45.0, "rec_to": 70.0}],
                  "music": [{"rec_from": 30.0, "rec_to": 80.0, "title": "Test Tone", "artist": "Lab", "confidence": "high", "evidence": "test fixture"}]}
        (out_sh / "edl.json").write_text(json.dumps(sh_edl), encoding="utf-8")
        M.CLAIMS.write_text(json.dumps({"claims": [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "TEST FIXTURE ONLY"}]}),
                            encoding="utf-8")
        for f in (adir / "scores.json", adir / "separated.json"):
            f.unlink(missing_ok=True)
        rsh = M._music(run, cfg, adir, args([out_sh / "edl.json"], apply=True))
        msh = json.loads((out_sh / "music.json").read_text(encoding="utf-8"))
        check(rsh["skipped_shorts"] == 1 and rsh["videos"][0]["skipped"] and msh["music"] == [] and "skipped" in msh and not (adir / "scores.json").is_file()
              and json.loads((out_sh / "edl.json").read_text(encoding="utf-8")) == sh_edl,
              "a short with a claimed song in it: nothing detected, identified, judged or separated, its EDL untouched: " + msh["skipped"][:90])
        patched_short = {**sh_edl, "segments": [{**sh_edl["segments"][0], "mute": [{"rec_from": 45.0, "rec_to": 70.0, "music": True, "why": "an older run"}]}],
                         "sfx": [{"file": "C:/x/clean.wav", "at": {"seg": "s1", "t": 0.0}, "music_clean": True}]}
        (out_sh / "edl.json").write_text(json.dumps(patched_short), encoding="utf-8")
        rsh = M._music(run, cfg, adir, args([out_sh / "edl.json"], apply=True))
        back_sh = json.loads((out_sh / "edl.json").read_text(encoding="utf-8"))
        check(rsh["videos"][0]["restored"] and not any(m.get("music") for s in back_sh["segments"] for m in s.get("mute") or [])
              and not any(x.get("music_clean") for x in back_sh.get("sfx") or []) and (out_sh / "edl.pre-music.json").is_file(),
              "a short an older run had cleaned: the music patch is taken out (backed up), so it plays its original audio")
        (out_l / "edl.json").write_text(json.dumps(long_edl), encoding="utf-8")
        (out_sh / "edl.json").write_text(json.dumps(sh_edl), encoding="utf-8")
        both = M._music(run, cfg, adir, args([out_l / "edl.json", out_sh / "edl.json"]))
        vb = {v["video"]: v for v in both["videos"]}
        check(vb["S01"].get("skipped") and vb["L01"]["music"] and vb["L01"]["music"][0]["action"] == "remove" and both["skipped_shorts"] == 1,
              "a long video and a short sharing the claimed song in one call: the long one's song is up for removal, the short is skipped")
        M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
        (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")

        S.EVIDENCE.unlink(missing_ok=True)                 # the service part starts from an empty register
        # ---------------------------------------------------------------- hosted recognition is never used (the user, 2026-11-21: local open weights only)
        calls = []
        real_q = dict(S.QUERY)
        S.QUERY["audd"] = S.QUERY["acrcloud"] = lambda wav, cfg_: calls.append(len(wav)) or {"found": True, "title": "X", "artist": "Y"}
        old_tok = os.environ.get("AUDD_API_TOKEN")
        os.environ["AUDD_API_TOKEN"] = "test-token-not-real"
        st = [S.service_state({**S.REC_DEFAULTS, "provider": p_, "allow_upload": True}) for p_ in ("audd", "acrcloud", "none")]
        S.rec_settings = lambda: {**S.REC_DEFAULTS, "provider": "audd", "allow_upload": True}
        for f in (adir / "fingerprint-matches.json", adir / "recognition.json", adir / "separated.json", adir / "neural-fp.json"):
            f.unlink(missing_ok=True)
        (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        check(not any(x["active"] for x in st) and "not used" in st[0]["why"] and not calls and not r["recognition"]["service"]["active"],
              "a recognition service is never asked, even when the config names one, allows uploads and its key is set: " + st[0]["why"][:80])
        S.QUERY.update(real_q)
        S.rec_settings = lambda: {**S.REC_DEFAULTS}
        if old_tok is None:
            os.environ.pop("AUDD_API_TOKEN", None)
        else:
            os.environ["AUDD_API_TOKEN"] = old_tok

        # ---------------------------------------------------------------- labelled fixtures never count outside a test that allows them
        rid_f = S.ensure_recording({"title": "Fixture Song", "artist": "Lab"})
        S.add_risk_evidence(rid_f, "documented_enforcement", "VALIDATION FIXTURE (not real evidence)", "https://fixture.invalid/a", "credible", True, by="validation")
        S.add_id_evidence(rid_f, "onscreen_title", "VALIDATION FIXTURE: display", "fixture", run=run.name, rec=[30, 80], by="validation")
        rec_f = S.record_of(rid_f)
        os.environ.pop("CC_ALLOW_FIXTURES", None)
        guarded = (S.risk_items(rec_f), S.interval_items(rec_f, run.name, 30, 80),
                   M.claim_items({"title": "Test Tone", "artist": "Lab", "confidence": "high"},
                                 [{"id": "M009", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "TEST FIXTURE ONLY"}]))
        os.environ["CC_ALLOW_FIXTURES"] = "1"
        allowed = (S.risk_items(rec_f), S.interval_items(rec_f, run.name, 30, 80))
        check(guarded == ([], [], []) and len(allowed[0]) == 1 and len(allowed[1]) == 1 and rec_f["risk_evidence"][0].get("fixture"),
              "fixture evidence and fixture claims are ignored in ordinary runs (and marked as fixtures when added); a test can allow them")
        S.EVIDENCE.unlink(missing_ok=True)                 # the fixture recording above must not compete with the next checks

        # ---------------------------------------------------------------- the local neural fingerprint index (LAION open weights), when installed
        nfp_ready = M.nafp_ready({**M.settings(), "nafp": {**M.nafp_settings(M.settings()), "index": str(tmp / "nafp-empty")}})
        check(not nfp_ready["ok"] and ("empty" in nfp_ready["why"] or "not" in nfp_ready["why"]),
              "an empty reference index names nothing: " + nfp_ready["why"][:80])
        ns = M.nafp_settings(M.settings())
        if Path(ns["python"] or "x").is_file() and (Path(ns["model_dir"] or "x") / "model.pt").is_file():
            os.environ["CC_NAFP_INDEX"] = str(tmp / "nafp-index")
            env3 = {**os.environ}
            add = subprocess.run([PY, str(CC), "music-index", "--from-run", str(run), "--rec", "28-84", "--id", "test-song", "--title", "Test Tone",
                                  "--artist", "Lab", "--license", "generated by this test", "--provenance", "the test run", "--id-score", "88"],
                                 capture_output=True, text=True,
                                 encoding="utf-8", env=env3)
            ra = json.loads([ln for ln in add.stdout.splitlines() if ln.startswith("{")][-1])
            nolab = subprocess.run([PY, str(CC), "music-index", "--from-run", str(run), "--rec", "28-84", "--id", "test-song-3", "--title", "Unsure"],
                                   capture_output=True, text=True, encoding="utf-8", env=env3)
            check(nolab.returncode != 0 and "--id-score" in nolab.stdout, "a stretch of a run is never added without how sure its title is (--id-score)")
            again = subprocess.run([PY, str(CC), "music-index", "--from-run", str(run), "--rec", "28-84", "--id", "test-song-2", "--title", "Same",
                                    "--id-score", "90"],
                                   capture_output=True, text=True, encoding="utf-8", env=env3)
            rb = json.loads([ln for ln in again.stdout.splitlines() if ln.startswith("{")][-1])
            check(ra.get("ok") and ra.get("recordings") == 1 and any(x_.get("skipped") for x_ in rb.get("results") or []),
                  "music-index adds a stretch of a run as a reference; the same audio again is not fingerprinted twice")
            for f in (adir / "fingerprint-matches.json", adir / "neural-fp.json", adir / "separated.json"):
                f.unlink(missing_ok=True)
            M.INDEX_DIR = tmp / "music-index-nfp"                  # no landmark fingerprints: the neural index is the only acoustic method here
            (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")
            r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
            mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
            check(mj["identified"] and mj["identified"]["by"] == "neural-fp" and mj["identified"]["title"] == "Test Tone" and mj["id_score"] == 88.0
                  and mj["identified"].get("label_score") == 88.0
                  and r["neural_fingerprint"]["named"] == 1,
                  f"the music interval is named by the local neural fingerprint, capped at its reference's own label (identity {mj['id_score']}, a "
                  "strong match alone would be 95): " + str(mj["identified"].get("evidence"))[:110])
            r2 = M._music(run, cfg, adir, args([out_l / "edl.json"]))
            check((r2["neural_fingerprint"].get("query") is None), "asked again with the same index: from the cache, the model is not loaded")
            subprocess.run([PY, str(CC), "music-index", "--remove", "test-song"], capture_output=True, text=True, encoding="utf-8", env=env3)
            (adir / "neural-fp.json").unlink(missing_ok=True)
            r3 = M._music(run, cfg, adir, args([out_l / "edl.json"]))
            mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
            check(not mj["identified"] or mj["identified"].get("by") != "neural-fp",
                  "the reference taken out of the index: the same music is no longer named (UNKNOWN), nothing invented")
            os.environ.pop("CC_NAFP_INDEX", None)
        else:
            print("skip the real neural fingerprint: not installed")
        S.EVIDENCE.unlink(missing_ok=True)

        # ---------------------------------------------------------------- the excerpts merged (no model): consistency, another excerpt, ambiguity
        man_ = {"r1": {"title": "Song One", "artist": "A", "provenance": "test"}, "r2": {"title": "Song Two", "artist": "B", "provenance": "test"}}

        def ans(dec, rid=None, chain=3, off=0.0, cos=0.8):
            return {"ok": True, "decision": dec, "candidates": [{"id": "r1"}, {"id": "r2"}],
                    "best": {"id": rid, "chain_windows": chain, "offset_s": off, "max_cos": cos} if rid else None}
        unk = {"ok": True, "decision": "UNKNOWN"}
        m1 = M.nafp_merge([(0.0, ans("MATCH", "r1", 3, 10.0, 0.95), ans("MATCH", "r1", 3, 10.0, 0.95)),
                           (120.0, ans("MATCH", "r1", 4, 130.4, 0.93), ans("MATCH", "r1", 4, 130.4, 0.93))], man_, 0.67)
        m2 = M.nafp_merge([(0.0, ans("MATCH", "r1", 3, 10.0, 0.95), ans("MATCH", "r1", 3, 10.0, 0.95)),
                           (120.0, ans("MATCH", "r1", 3, 190.0, 0.95), ans("MATCH", "r1", 3, 190.0, 0.95))], man_, 0.67)
        check(m1["level"] == "strong" and m1["consistent"] is True and "one continuous playback" in m1["evidence"]
              and m2["level"] == "fair" and m2["consistent"] is False and "DIFFERENT alignments" in m2["evidence"],
              "a song matched in two excerpts must line up as one playback; at two alignments it stays at the fair level")
        m3 = M.nafp_merge([(0.0, unk, unk), (120.0, ans("MATCH", "r2", 2, 5.0, 0.7), unk)], man_, 0.67)
        check(m3 and m3["index_id"] == "r2" and m3["level"] == "fair" and m3["title"] == "Song Two",
              "the first excerpt names nothing, another excerpt does: named at the fair level")
        m4 = M.nafp_merge([(0.0, ans("AMBIGUOUS"), unk)], man_, 0.67)
        m5 = M.nafp_merge([(0.0, ans("MATCH", "r1", 5, 1.0, 0.96), ans("MATCH", "r1", 5, 1.0, 0.96)), (120.0, ans("MATCH", "r2", 2, 3.0, 0.7), unk)],
                          man_, 0.67)
        check(m4.get("ambiguous") and M.nafp_merge([(0.0, unk, unk)], man_, 0.67) is None and m5["index_id"] == "r1" and m5["also_in_interval"] == ["r2"],
              "two references in one excerpt: ambiguous (nothing named); nothing: UNKNOWN; two songs in two excerpts: the best one named, the other listed")

        # ---------------------------------------------------------------- the retry on the separated accompaniment where his words overlap (stand-ins)
        real_ready, real_run, real_words = M.nafp_ready, M.nafp_run, M.words_in
        idx_stub = tmp / "nafp-stub"
        idx_stub.mkdir(exist_ok=True)
        (idx_stub / "manifest.json").write_text(json.dumps({"recordings": {"stub-song": {"title": "Stub Song", "artist": "Lab", "provenance": "test"}}}),
                                                encoding="utf-8")
        os.environ["CC_NAFP_INDEX"] = str(idx_stub)
        sent = []

        def stub_run(ops, cfg_, work):
            sent.extend(str(o.get("file")) for o in ops)
            res_ = []
            for o in ops:
                hit = "accompaniment-" in str(o.get("file"))
                res_.append({"op": "query", "qid": o["qid"], "ok": True, "decision": "MATCH" if hit else "UNKNOWN",
                             "best": {"id": "stub-song", "chain_windows": 3, "offset_s": 12.0 + float(o.get("start_s") or 0), "max_cos": 0.81} if hit else None})
            return {"ok": True, "results": res_, "device": "stub"}
        M.nafp_ready = lambda cfg_: {"ok": True, "why": None, "recordings": 1, "index_version": "stub-1"}
        M.nafp_run = stub_run
        M.INDEX_DIR = tmp / "music-index-retry"
        for f in (adir / "fingerprint-matches.json", adir / "neural-fp.json", adir / "separated.json"):
            f.unlink(missing_ok=True)
        (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")
        M.words_in = lambda run_, rows_, a_, b_: []
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        ivs = [m_["rec"] for v_ in r["videos"] for m_ in v_["music"]]
        for x0_, x1_ in ivs:
            ap = adir / "analysis" / f"accompaniment-{x0_:.2f}-{x1_:.2f}.wav"
            ap.parent.mkdir(parents=True, exist_ok=True)
            import soundfile as sf_
            sf_.write(str(ap), np.zeros((44100, 2), np.float32), 44100)
        (adir / "neural-fp.json").unlink(missing_ok=True)
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        no_words = r["neural_fingerprint"]
        M.words_in = lambda run_, rows_, a_, b_: [(a_ + 1.0, a_ + 1.4, "hello")]
        (adir / "neural-fp.json").unlink(missing_ok=True)
        sent.clear()
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        nf = r["neural_fingerprint"]
        check(no_words["retried_on_separated"] == 0 and nf["retried_on_separated"] == len(ivs) and nf["named_on_separated"] == len(ivs)
              and any("accompaniment-" in x for x in sent) and any("nfp-" in x for x in sent)
              and mj["identified"] and mj["identified"]["by"] == "neural-fp" and mj["identified"]["source"] == "accompaniment"
              and "separated accompaniment" in mj["identified"]["evidence"],
              "the stream audio names nothing; where his words overlap, the separated accompaniment is tried and names the song (without words: no "
              "retry): " + str(mj["identified"].get("evidence") if mj["identified"] else None)[:120])
        M.nafp_ready, M.nafp_run, M.words_in = real_ready, real_run, real_words
        os.environ["CC_NAFP_INDEX"] = str(tmp / "nafp-none")
        for f in (adir / "neural-fp.json", adir / "fingerprint-matches.json"):
            f.unlink(missing_ok=True)
        import shutil as sh_
        sh_.rmtree(adir / "analysis", ignore_errors=True)
        S.EVIDENCE.unlink(missing_ok=True)

        # ---------------------------------------------------------------- the two scores (no audio)
        I = lambda kind, s, g, vs=False: {"kind": kind, "strength": s, "group": g, "version_specific": vs}     # noqa: E731
        a1 = S.id_score([I("fingerprint_claim", 95, "fingerprint", True), I("fingerprint_learned", 88, "fingerprint", True)])
        check(a1["score"] == 95.0, f"two items of one method (both fingerprints) count once, the stronger: {a1['score']}")
        a2 = S.id_score([I("lyrics_match", 75, "lyrics"), I("spoken_mention", 55, "mention")])
        check(a2["score"] == 80.0 and a2["caps"] and not a2["version_specific"],
              f"lyrics and his words agree (88.8 combined) but nothing names the exact recording: 80 at most: {a2['score']} {a2['caps']}")
        a3 = S.id_score([I("lyrics_match", 75, "lyrics"), I("spoken_mention", 55, "mention"), I("onscreen_title", 85, "screen", True)])
        check(a3["score"] == 98.3 and a3["version_specific"], f"with the title on screen (version-specific), independent methods combine: {a3['score']}")
        a4 = S.id_score([I("onscreen_title", 85, "screen", True), I("service", 92, "service", True), I("conflicting_candidate", 70, "conflict")])
        check(a4["score"] == 60.0 and a4["conflict"], f"a supported competitor for the same stretch caps it at 60: {a4['score']}")
        R = lambda kind, q, o, spec=True, **kw: {"id": o, "kind": kind, "quality": q, "names_this_recording": spec, "origin": o, **kw}     # noqa: E731
        b1 = S.risk_score([R("documented_enforcement", "credible", "a.example"), R("documented_enforcement", "credible", "b.example")])
        check(b1["score"] == 85.6 and b1["adequate"], f"two credible reports naming this recording from two origins: {b1['score']}, adequate")
        b2 = S.risk_score([R("documented_enforcement", "credible", "a.example"), {**R("documented_enforcement", "credible", "a.example"), "id": "R2"}])
        check(b2["score"] == 62.0, f"two copies of one origin count once: {b2['score']}")
        b3 = S.risk_score([R("documented_enforcement", "credible", "a.example", spec=False), R("catalog_fact", "verified", "c.example")])
        check(b3["score"] == 0.0 and not b3["adequate"], f"a report that does not name this recording, and fame / a release / a major label: nothing ({b3['score']})")
        b4 = S.risk_score([R("rights_admin", "verified", "d.example", spec=False), R("rights_admin", "credible", "e.example", spec=False)])
        check(b4["score"] <= 40 and not b4["adequate"], f"supporting facts only (how the rights are administered): {b4['score']}, never adequate")
        b5 = S.risk_score([R("documented_enforcement", "unverified", "f.example"), R("documented_enforcement", "unverified", "g.example"),
                           R("rightsholder_notice", "unverified", "h.example")])
        check(b5["score"] <= 45 and not b5["adequate"], f"unverified reports only (a forum post): {b5['score']} at most 45, not adequate")
        b6 = S.risk_score([R("own_claim", "verified", "own"), R("conflicting_report", "credible", "i.example")])
        check(b6["score"] == 50.0 and b6["conflict"], f"a claim and a contradicting report: capped at 50, the conflict recorded: {b6['score']}")
        b7 = S.risk_score([R("own_claim", "verified", "own"), R("license_cleared", "verified", "j.example")])
        check(b7["score"] == 5.0 and b7["license"], "a licence or clearance for this use: 5 at most")
        b8 = S.risk_score([R("documented_enforcement", "credible", "k.example", date="2015-01-01"), R("documented_enforcement", "credible", "l.example",
                                                                                                      region="DE")], user_region="XK")
        check(b8["score"] == 56.7 and b8["score"] < b1["score"],
              f"a report older than five years (x0.6) and one limited to another region (x0.5) weigh less: {b8['score']} against {b1['score']} for two full ones")
        hi = {"score": 92.0, "conflict": False}
        oc = {k: S.outcome(i_, r_)["code"] for k, (i_, r_) in {"A": (hi, b1), "B": (hi, b2), "C": (hi, b4), "D": ({"score": 60.0}, b1),
                                                                 "E": (hi, b7), "F1": (a4, b1), "F2": (hi, {**b6, "license": False, "adequate": True})}.items()}
        check(oc == {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F1": "F", "F2": "F"}, "outcomes A-F: " + json.dumps(oc))
        check(S.outcome(hi, b1)["action"] == "remove" and all(S.outcome(i_, r_)["action"] != "remove" for i_, r_ in ((hi, b2), (hi, b4), ({"score": 60.0}, b1),
                                                                                                                     (hi, b7), (a4, b1))),
              "only A changes the audio")
        check("not a probability" in S.outcome(hi, b1)["why"], "the risk is called an index, never a probability")
        # ---------------------------------------------------------------- identity evidence belongs to its interval
        rid_x = S.ensure_recording({"title": "Interval Song", "artist": "Lab"})
        try:
            S.add_id_evidence(rid_x, "lyrics_match", "a fragment fits", "test", 60.0)
            check(False, "an identity item without its interval is refused")
        except ValueError as ex:
            check("--run" in str(ex), "an identity item without its interval is refused: " + str(ex)[:80])
        S.add_id_evidence(rid_x, "lyrics_match", "a fragment fits", "test", 60.0, run="runA", rec="100-160")
        S.add_id_evidence(rid_x, "soundtrack_listing", "the game's station lists this recording", "https://example.org/station")
        rx = S.record_of(rid_x)
        check(S.id_score(S.interval_items(rx, "runA", 120, 150))["score"] == 76.0 and S.id_score(S.interval_items(rx, "runA", 300, 360))["score"] == 40.0
              and S.id_score(S.interval_items(rx, "runB", 120, 150))["score"] == 40.0,
              "an item counts only for its own interval (another stretch or another run gets the global listing only)")
        check(rid_x in S.candidates_for("runA", 90, 110) and rid_x not in S.candidates_for("runA", 300, 360),
              "the register's candidates of a stretch: only recordings with items there (a listing alone puts no song anywhere)")
        S.add_id_evidence(rid_x, "onscreen_title", "the display reads it", "frame at 130 s", run="runA", rec=[100, 160])
        check(any(p_["rid"] == rid_x for p_ in S.pending()), "identified at 85+ in one interval and no risk research yet: listed (needs risk)")
        # the contradiction rule in a run: two register candidates close together -> F; far apart -> the stronger one, no F
        rid_c1 = S.ensure_recording({"title": "Close One", "artist": "Lab"})
        rid_c2 = S.ensure_recording({"title": "Close Two", "artist": "Lab"})
        S.add_id_evidence(rid_c1, "lyrics_match", "fits", "test", 60.0, run=run.name, rec=[30, 80])
        S.add_id_evidence(rid_c2, "spoken_mention", "he names it", "test", 55.0, run=run.name, rec=[30, 80])
        (out_l / "edl.json").write_text(json.dumps(plain), encoding="utf-8")
        M.INDEX_DIR = tmp / "music-index-3"
        (adir / "fingerprint-matches.json").unlink(missing_ok=True)
        M._music(run, cfg, adir, args([out_l / "edl.json"]))
        mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        check(mj["outcome"] == "F" and mj["identified"]["title"] == "Close One" and mj["action"] == "review",
              "lyrics (60) against his naming of another song (55) for one stretch: contradictory (F), left as it is: " + mj["status"][:110])
        S.add_id_evidence(rid_c1, "onscreen_title", "the display reads Close One", "test", run=run.name, rec=[30, 80])
        M._music(run, cfg, adir, args([out_l / "edl.json"]))
        mj = json.loads((out_l / "music.json").read_text(encoding="utf-8"))["music"][0]
        check(mj["outcome"] != "F" and mj["identified"]["title"] == "Close One" and mj["id_score"] >= 85,
              f"the title on screen settles it: the runner-up (55) is far behind ({mj['id_score']}), no contradiction")
        # ---------------------------------------------------------------- the lyrics check and MusicBrainz (stand-ins: nothing is sent)
        lyr_calls = []
        FIX_LYRICS = ("Paper boats along the river\nCarry all the words I never said\nPaper boats along the river\nSailing to the morning light ahead\n"
                      "Hold the lantern, hold it higher\nEvery window burning red")              # written for this test, no real song

        def fake_lrclib(url):
            lyr_calls.append(url)
            if "Nobody" in url:
                import urllib.error
                raise urllib.error.HTTPError(url, 404, "not found", {}, None)
            return {"id": 7, "trackName": "Paper Boats", "artistName": "Lab", "duration": 200, "plainLyrics": FIX_LYRICS}
        S.LRCLIB_GET = fake_lrclib
        lc = S.lyrics_check("Paper Boats", "Lab", ["paper boats along the liver carry all the words", "paper boats along the river carry all the word",
                                                   "hold the lantern hold it high or every window", "the end"])
        check(lc["found"] and len(lc["fragments"]) == 2 and lc["strength"] == 75.0,
              "two different lines fit (the repeated line once, a 2-word fragment not matched): 75: " + json.dumps([f_["ratio"] for f_ in lc["fragments"]]))
        lc2 = S.lyrics_check("Paper Boats", "Lab", ["I was about to rob this store right now"])
        check(lc2["strength"] == 0.0, f"his own words against the lyrics: no fit ({lc2['fragments'][0]['ratio']})")
        n_ = len(lyr_calls)
        lc3 = S.lyrics_check("Paper Boats", "Lab", ["paper boats along the liver carry all the words", "paper boats along the river carry all the word",
                                                    "hold the lantern hold it high or every window", "the end"])
        check(lc3["cached"] and len(lyr_calls) == n_ and "Paper" not in json.dumps(json.loads(S.LYR_CACHE.read_text(encoding="utf-8"))["entries"]).replace("Paper Boats", ""),
              "asked again: from the cache, and the cache keeps numbers, never the lyrics")
        check(S.lyrics_check("Song", "Nobody", ["paper boats along the river carry all the words"])["found"] is False, "a song LRCLIB does not have: not found, nothing invented")
        mb_calls = []

        def fake_mb(url):
            mb_calls.append(url)
            return {"count": 2, "recordings": [{"id": "mb1", "score": 100, "title": "Paper Boats", "length": 200000, "artist-credit": [{"name": "Lab"}],
                                                "isrcs": ["TEST00000002"], "first-release-date": "2020-01-01", "releases": []},
                                               {"id": "mb2", "score": 90, "title": "Paper Boats", "disambiguation": "live", "length": 260000,
                                                "artist-credit": [{"name": "Lab"}], "first-release-date": "2021"}]}
        S.MB_GET = fake_mb
        mbr = S.mb_search("Paper Boats", "Lab")
        mbr2 = S.mb_search("Paper Boats", "Lab")
        check(mbr["versions"] == ["live", "original/unspecified"] and mbr["recordings"][0]["isrcs"] == ["TEST00000002"] and mbr2["cached"] and len(mb_calls) == 1,
              "MusicBrainz: the versions (live / original), ISRCs and lengths to tell them apart; asked again, from the cache: " + json.dumps(mbr["versions"]))
        env2 = {**os.environ, "CC_MUSIC_EVIDENCE": str(tmp / "cli-evidence.json")}
        cp = subprocess.run([PY, str(CC), "music-evidence", "--new", "Lab - Paper Boats"], capture_output=True, text=True, encoding="utf-8", env=env2)
        rid_pb = json.loads([ln for ln in cp.stdout.splitlines() if ln.startswith("{")][-1])["rid"]
        cp = subprocess.run([PY, str(CC), "music-evidence", "--add-id", "--rid", rid_pb, "--kind", "spoken_mention", "--detail", "he names it",
                             "--source", "transcript"], capture_output=True, text=True, encoding="utf-8", env=env2)
        r1 = json.loads([ln for ln in cp.stdout.splitlines() if ln.startswith("{")][-1])
        cp = subprocess.run([PY, str(CC), "music-evidence", "--add-risk", "--rid", rid_pb, "--kind", "documented_enforcement", "--summary", "a claim report",
                             "--source", "https://x.example/1", "--quality", "credible", "--specific"], capture_output=True, text=True, encoding="utf-8", env=env2)
        r2 = json.loads([ln for ln in cp.stdout.splitlines() if ln.startswith("{")][-1])
        check(r1.get("ok") is False and "--run" in r1.get("error", "") and r2.get("ok") and r2["added"]["origin"] == "x.example",
              "the command refuses an identity item without its interval and keeps a risk item with its origin (the site): " + r1.get("error", "")[:60])

        # ---------------------------------------------------------------- the residual check: a song only made quieter is still recognisable
        song = M.span_audio(run, M.load_chunks(run), 30, 80, 44100, 2)
        rng2 = np.random.default_rng(3)
        talk = (rng2.standard_normal(song.shape).astype("float32") * 0.05) * (np.sin(np.linspace(0, 60, song.shape[1])) > 0)
        orig = song + talk
        quieter = M.recording_left(song * 0.3 + talk, 44100, orig, 44100, cfg)
        gone = M.recording_left(talk, 44100, orig, 44100, cfg)
        check(not quieter["ok"] and quieter["recognisable_at_s"] and gone["ok"],
              f"a song only turned down is still recognisable (max {quieter['max_clean_score']} vs threshold {quieter['threshold']}); removed, it is not "
              f"(max {gone['max_clean_score']})")
        lvl20 = M.music_only_level(song * 0.1, 44100, song, 44100, [], cfg)
        lvl40 = M.music_only_level(song * 0.01, 44100, song, 44100, [], cfg)
        lvl_t = M.music_only_level(song * 0.1, 44100, song, 44100, [(0.0, 50.0, "words")], cfg)
        check(not lvl20["ok"] and lvl20["worst_change_db"] == -20.0 and lvl40["ok"] and lvl_t.get("skipped"),
              f"where nobody speaks the music must be down 35 dB: 20 dB down fails ({lvl20['worst_change_db']}), 40 dB passes; under talk this check has "
              f"nothing to say ({lvl_t.get('skipped')})")
        sc1 = M.singer_check([(10.0, 12.0, "hi")], 50.0, True, "hdemucs", cfg)
        sc2 = M.singer_check([(10.0, 12.0, "hi")], 50.0, False, "hdemucs", cfg)
        sc3 = M.singer_check([], 50.0, True, "hdemucs", cfg)
        sc4 = M.singer_check([(10.0, 12.0, "hi")], 50.0, True, "sam-audio-base", cfg)
        check(not sc1["ok"] and sc2["ok"] and sc3["ok"] and sc4["ok"],
              "a sung song under his words fails with Demucs (it keeps every voice); an instrumental, or no words over it, or a method that can tell the "
              "singer from him, does not fail on this")
    finally:
        S.rec_settings = real_rec
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"test_music: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
