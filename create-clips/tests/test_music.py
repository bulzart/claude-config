"""Tests of the selective music step (cc_music.py: `cc.py music`, `music-claim`, `music-setup`) and the resolver's `mute` (cc_edit.py).
A generated run of two chunks: a quiet noise bed, then a bass line over a 120 BPM kick and hi-hat across the chunk join, then the bed again. Checked: the risk lookup
(confirmed / none / unknown; a low-confidence guess is unknown; cleared on record), the detection on the kept footage only, the same interval found by a
long and a short video (the second analyses nothing: the windows are cached), the EDL patch (a mute span plus the cleaned audio on a lane, replaced and
never stacked, taken back when the claim is gone, a segment at another speed left alone), the failure branch (no separation: the original sound stays,
`attention`) and, when the separation's Python is on this PC, the real model on the GPU: separated, checked, patched, resolved by `edl-check` with the
muted piece at volume 0, then reused without a second separation. Mocked claims only test the branches; they say nothing about a real song.
Run: python tests/test_music.py"""
import json
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
        short_edl = {"schema": "cc-edl/1", "video": "S01", "kind": "short", "segments": [{"id": "s1", "rec_from": 45.0, "rec_to": 70.0}]}
        (out_l / "edl.json").write_text(json.dumps(long_edl), encoding="utf-8")
        (out_s / "edl.json").write_text(json.dumps(short_edl), encoding="utf-8")
        cfg = M.settings()
        adir = run / "30-assets" / "music"
        adir.mkdir(parents=True)
        M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
        r0 = M._music(run, cfg, adir, args([out_s / "edl.json"]))
        iv0 = [m for v in r0["videos"] for m in v["music"]]
        sj = json.loads((out_s / "music.json").read_text(encoding="utf-8"))
        check(len(iv0) == 1 and 26 <= iv0[0]["rec"][0] <= 34 and 76 <= iv0[0]["rec"][1] <= 84,
              "a short inside the song: the interval is followed past its edges to where the music ends: " + json.dumps([m["rec"] for m in iv0]))
        check(iv0 and iv0[0]["risk"] == "unknown" and iv0[0]["action"] == "review" and sj["review"] == 1, "not identified: listed for review, its sound left as it is")
        check(any("test tone" in e_["text"] for e_ in sj["music"][0]["evidence"]) and len(sj["music"][0]["look_at"]) == 3,
              "the evidence to name it comes along (a miner's avoid line) and three times to look at")
        r = M._music(run, cfg, adir, args([out_l / "edl.json"]))
        iv = [m for v in r["videos"] for m in v["music"]]
        check(len(iv) == 1 and iv[0]["rec"] == iv0[0]["rec"], "the bass and beat are found across the chunk join, the bed is not, the same interval as the short's: "
              + json.dumps([m["rec"] for m in iv]))
        check(iv and iv[0]["risk"] == "none" and iv[0]["action"] == "keep", "identified with no claim on record: left as it is")
        check(r["analysed_s"] < 140, f"only the kept footage (and a little past its edges) is analysed: {r['analysed_s']} s")
        rs = M._music(run, cfg, adir, args([out_s / "edl.json"]))
        sj = json.loads((out_s / "music.json").read_text(encoding="utf-8"))
        check(rs["analysed_s"] == 0 and sj["music"][0]["identified"] and sj["music"][0]["identified"]["by"] == "L01" and sj["music"][0]["action"] == "keep",
              f"the short again: nothing analysed (cached), and it knows the song the long's builder named: {rs['analysed_s']} s, {sj['music'][0]['identified']}")
        M.CLAIMS.write_text(json.dumps({"claims": claims}), encoding="utf-8")
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
            check("removed (verified" in st["L01"]["music"][0]["status"] and "removed (verified" in st["S01"]["music"][0]["status"],
                  "the cleaned audio passed its check, and the short uses the song the long's builder named (shared): " + st["S01"]["music"][0]["status"][:120])
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
            M.CLAIMS.write_text(json.dumps({"claims": []}), encoding="utf-8")
            back = M._music(run, cfg, adir, args([out_l / "edl.json"], apply=True))
            pl3 = json.loads((out_l / "edl.json").read_text(encoding="utf-8"))
            check(not any(m.get("music") for m in pl3["segments"][0].get("mute", [])) and not any(x.get("music_clean") for x in pl3.get("sfx", []))
                  and back["videos"][0]["music"][0]["action"] == "keep", "the claim taken off the register: the original sound comes back")
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
        check(mj["risk"]["status"] == "confirmed" and mj["identified"]["by"] == "fingerprint" and mj["identified"]["claim"] == "M001" and mj["action"] == "remove",
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
        check(r["videos"][0]["music"][0]["action"] == "keep" and r["separation"] is None and not r["videos"][0]["patched"],
              "a famous song named with high confidence but no claim on record: nothing separated, the EDL untouched")
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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"test_music: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
