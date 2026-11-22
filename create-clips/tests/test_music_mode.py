"""Tests of the music isolation mode (the user, 2026-11-22, "Add Isolation / Non-Isolation Mode Without Changing the Existing Content Workflow").
state.json music_isolation_mode is picked at the start (a run made before the option keeps Isolation). Checked on a generated run (test_music's make_run),
the separation and its check stood in (no GPU, no model):
  - the state key: a typo refused with nothing changed, the forms the user may type stored as isolation / non_isolation, read back by a new process;
  - the editorial outputs (the resolved plan, the CapCut plan, the finish plan, the captions) of the same frozen EDLs are identical in both modes;
  - Non-Isolation bypasses the music step at its entry: no settings read, no detection, fingerprint, index query, risk score, separation, SAM or GPU
    lease, no music folder made; the original sound stays; shorts as always;
  - Isolation still runs the step: a claimed song in a long video is separated and patched, a short in the same call is not;
  - the resolver never builds a leftover music patch into a short or a Non-Isolation video;
  - the switch both ways: to Non-Isolation the patch is taken out (a copy kept, the cleaned audio kept in the cache), a delivered video is left as it is,
    shorts untouched; back to Isolation nothing is processed by the switch, then the music step reuses the caches and applies the patch once (never
    stacked); a switch while a job runs stops it before anything is applied.
Run: python tests/test_music_mode.py"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import cc_crypto_loader  # noqa: E402,F401
import cc_music as M  # noqa: E402
import cc_gpu  # noqa: E402
import test_music as TM  # noqa: E402  (the generated run: two chunks, a bass line and a beat across the join)

PY = sys.executable
CC = HERE.parent / "scripts" / "cc.py"
FAILED = []
N = [0]


def check(ok, what):
    N[0] += 1
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        FAILED.append(what[:90])


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env)
    last = [ln for ln in cp.stdout.splitlines() if ln.startswith("{")]
    return json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}


def rj(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def wj(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj), encoding="utf-8")


def editorial(edl: dict) -> dict:
    """The EDL without what the music step adds (its mute spans, its cleaned-audio lanes, the builder's `music` naming list); an empty `sfx` list reads
    as none (the resolver reads `sfx or []`, and the patch leaves `sfx: []` where the EDL had no list)."""
    e = M.strip_patch(edl)
    e.pop("music", None)
    if not e.get("sfx"):
        e.pop("sfx", None)
    return e


def norm(obj):
    """A file's content without the moment it was written."""
    if isinstance(obj, dict):
        return {k: norm(v) for k, v in obj.items() if k not in ("made", "at", "written", "created")}
    if isinstance(obj, list):
        return [norm(x) for x in obj]
    return obj


def first_diff(a, b, path="") -> str:
    """Where two JSON values first differ (for a failure message)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}/{k}: only in {'the first' if k in a else 'the second'}"
            d = first_diff(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return ""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: {len(a)} items against {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return ""
    return "" if a == b else f"{path}: {str(a)[:80]!r} against {str(b)[:80]!r}"


def song_muted(pieces) -> bool:
    """A piece of the song's stretch (rec 30-80 s) plays muted (the builder's own mute at 90-92 s is not the music patch)."""
    return any(p.get("muted") and p["rec_from"] < 80.0 and p["rec_to"] > 30.0 for p in pieces)


def set_mode_raw(run, mode):
    """The state key written directly (no `cc.py state`, so no switch): for the resolver's own checks."""
    st = rj(Path(run) / "state.json")
    st["music_isolation_mode"] = mode
    wj(Path(run) / "state.json", st)


def music_cmd(run, edl=None, spans=None, apply=False):
    """cc_music.cmd_music in this process (it prints one JSON line and exits)."""
    a = SimpleNamespace(run=str(run), edl=[str(e) for e in edl] if edl else None, spans=spans, apply=apply, force=False, no_analysis=False)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            M.cmd_music(a)
        except SystemExit:
            pass
    return json.loads([ln for ln in buf.getvalue().splitlines() if ln.startswith("{")][-1])


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc_music_mode_test_"))
    M.CLAIMS = tmp / "claims.json"
    S = M.songid
    S.EVIDENCE, S.CACHE = tmp / "music-evidence.json", tmp / "music-ident-cache.json"      # never the real register or cache
    S.LYR_CACHE, S.MB_CACHE = tmp / "lyrics-check-cache.json", tmp / "musicbrainz-cache.json"
    os.environ["CC_ALLOW_FIXTURES"] = "1"                 # labelled fixtures; ordinary runs ignore them
    os.environ["CC_NAFP_INDEX"] = str(tmp / "nafp-none")  # never the real reference index
    real_rec = S.rec_settings
    S.rec_settings = lambda: {**S.REC_DEFAULTS}
    real = {k: getattr(M, k) for k in ("separate_spans", "verify", "sam_spans", "sam_ready")}
    try:
        run = TM.make_run(tmp)
        boom = tmp / "boom.wav"
        subprocess.run([TM.find_tool("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=880:duration=0.5", str(boom)], check=True)
        long_edl = {"schema": "cc-edl/1", "video": "L01", "kind": "long",
                    "segments": [{"id": "s1", "rec_from": 20.0, "rec_to": 100.0, "zoom": [{"at": 30.0, "to": 1.15}],
                                  "mute": [{"rec_from": 90.0, "rec_to": 92.0, "why": "the builder's own (not music)"}]},
                                 {"id": "s2", "rec_from": 105.0, "rec_to": 115.0, "transition_in": {"slug": "flash", "dur": 0.2}}],
                    "sfx": [{"file": str(boom).replace("\\", "/"), "at": {"seg": "s1", "t": 3.0}, "why": "a hit"}],
                    "music": [{"rec_from": 30.0, "rec_to": 80.0, "title": "Test Tone", "artist": "Lab", "confidence": "high", "evidence": "test fixture"}]}
        short_edl = {"schema": "cc-edl/1", "video": "S01", "kind": "short", "segments": [{"id": "s1", "rec_from": 45.0, "rec_to": 70.0}]}

        # ------------------------------------------------------------ the state key
        check(M.music_isolation_mode(run) == "isolation", "a run made before the option (no key) keeps Isolation, the music step as before")
        st0 = (run / "state.json").read_bytes()
        bad = cc("state", "--run", run, "set", "music_isolation_mode=sometimes")
        check(bad.get("ok") is False and "nothing was changed" in bad.get("error", "") and (run / "state.json").read_bytes() == st0,
              "a typo is refused and nothing is changed: " + bad.get("error", "")[:70])
        s1 = cc("state", "--run", run, "set", "music_isolation_mode=Non-Isolation")
        got = cc("state", "--run", run, "get", "music_isolation_mode")
        check(s1.get("ok") and got.get("value") == "non_isolation" and s1.get("music_isolation_mode") == "non_isolation"
              and "nothing to change" in (s1.get("music_switch") or {}).get("note", ""),
              "'Non-Isolation' is stored as non_isolation and read back by a new process (resume); no EDL yet, nothing to change")
        s2 = cc("state", "--run", run, "set", "music_isolation_mode=isolation")
        check(s2.get("ok") and cc("state", "--run", run, "get", "music_isolation_mode").get("value") == "isolation", "and back: isolation")

        # ------------------------------------------------------------ the editorial outputs of the same frozen EDLs: identical in both modes
        outs = {}
        for mode in ("isolation", "non_isolation"):
            cc("state", "--run", run, "set", f"music_isolation_mode={mode}")
            files = {}
            for vid, e in (("L01", long_edl), ("S01", short_edl)):
                d = tmp / f"frozen-{mode}" / vid
                wj(d / "edl.json", e)
                chk = cc("edl-check", "--run", run, "--edl", d / "edl.json")
                cap = cc("captions", "--run", run, "--resolved", d / "resolved.json")
                files[vid] = {"check": {k: chk.get(k) for k in ("ok", "totals", "warnings", "joins", "layout")}, "captions_ok": cap.get("ok"),
                              **{f: norm(rj(d / f)) for f in ("resolved.json", "mcp-plan.json", "finish.json", "captions.json") if (d / f).is_file()},
                              **{f: (d / f).read_text(encoding="utf-8") for f in ("captions.srt",) if (d / f).is_file()}}
            outs[mode] = files
        same = json.dumps(outs["isolation"], sort_keys=True) == json.dumps(outs["non_isolation"], sort_keys=True)
        made = sorted(k for k in outs["isolation"]["L01"] if k.endswith((".json", ".srt")))
        check(same and outs["isolation"]["L01"]["check"]["ok"] and "resolved.json" in made and "captions.json" in made,
              f"the same EDLs give the same resolved plan, CapCut plan, finish plan and captions in both modes ({', '.join(made)}; long and short)"
              + ("" if same else " | differs at " + first_diff(outs["isolation"], outs["non_isolation"]))
              + ("" if outs["isolation"]["L01"]["check"]["ok"] else " | edl-check: " + json.dumps(outs["isolation"]["L01"]["check"].get("warnings"))[:300]))
        cc("state", "--run", run, "set", "music_isolation_mode=non_isolation")

        # ------------------------------------------------------------ Non-Isolation: bypassed at the entry, nothing runs
        out_l, out_s, out_d = run / "60-outputs" / "L01", run / "60-outputs" / "S01", run / "60-outputs" / "L02"
        wj(out_l / "edl.json", long_edl)
        wj(out_s / "edl.json", short_edl)
        calls = []

        def trap(name):
            def f(*a_, **k_):
                calls.append(name)
                raise RuntimeError(f"{name} must not run in a Non-Isolation run")
            return f
        names = ("settings", "Scores", "analyse", "separate_spans", "sam_spans", "sam_ready", "nafp_identify", "nafp_ready", "fp_load", "fp_identify",
                 "load_claims", "span_audio", "learn_recording")
        saved = {n: getattr(M, n) for n in names}
        saved_gpu, saved_id = cc_gpu.lease, S.identify_interval
        for n in names:
            setattr(M, n, trap(n))
        cc_gpu.lease, S.identify_interval = trap("gpu lease"), trap("identify_interval")
        try:
            r_sp = music_cmd(run, spans="0-120")
            r_ed = music_cmd(run, edl=[out_l / "edl.json", out_s / "edl.json"], apply=True)
        finally:
            for n, f in saved.items():
                setattr(M, n, f)
            cc_gpu.lease, S.identify_interval = saved_gpu, saved_id
        vids = {v["video"]: v for v in r_ed.get("videos") or []}
        check(not calls and r_sp.get("bypassed") and r_sp.get("music_intervals") == [] and r_ed.get("bypassed") and r_ed.get("intervals") == 0
              and not (run / "30-assets" / "music").exists(),
              "Non-Isolation: no settings, detection, fingerprint, index, claims, risk score, separation, SAM or GPU lease is touched, no music folder made: "
              + (", ".join(calls) or "nothing called"))
        check(rj(out_l / "edl.json") == long_edl and rj(out_s / "edl.json") == short_edl and vids.get("L01", {}).get("skipped") == M.NON_ISOLATION_RULE
              and vids.get("S01", {}).get("skipped") == M.SHORTS_RULE and rj(out_l / "music.json").get("mode") == "non_isolation",
              "the EDLs are left exactly as they are (original sound); the long video's record says Non-Isolation, the short's the shorts rule")
        leases = sorted(p.name for p in (HERE.parent / "data" / "gpu").glob("*")) if (HERE.parent / "data" / "gpu").is_dir() else []
        t0 = time.time()
        r_cli = cc("music", "--run", run, "--edl", out_l / "edl.json", "--apply")
        r_cli2 = cc("music", "--run", run, "--spans", "0-120")
        dt = time.time() - t0
        leases2 = sorted(p.name for p in (HERE.parent / "data" / "gpu").glob("*")) if (HERE.parent / "data" / "gpu").is_dir() else []
        check(r_cli.get("bypassed") and r_cli2.get("bypassed") and dt < 20 and leases2 == leases and not (run / "30-assets" / "music").exists(),
              f"the command line too (a new process reads the mode): bypassed in {dt:.1f} s for two calls, no GPU lease, no music folder")

        # ------------------------------------------------------------ Isolation: the step runs; a short in the same call is not processed
        cc("state", "--run", run, "set", "music_isolation_mode=isolation")
        M.CLAIMS.write_text(json.dumps({"claims": [{"id": "M001", "title": "Test Tone", "artist": "Lab", "status": "claimed", "evidence": "TEST FIXTURE ONLY"}]}),
                            encoding="utf-8")
        rid = S.ensure_recording({"title": "Test Tone", "artist": "Lab"})
        S.add_id_evidence(rid, "onscreen_title", "the radio display reads Lab - Test Tone (TEST FIXTURE)", "test fixture", run=run.name, rec=[30, 80])
        sep_calls = []

        def fake_sep(jobs, cfg_, work):
            import soundfile as sf
            sep_calls.append([j["id"] for j in jobs])
            for j in jobs:
                d_, sr_ = sf.read(j["wav_in"], dtype="float32", always_2d=True)
                sf.write(j["wav_out"], d_ * 0.1, sr_)
            return {"ok": True, "model": "stand-in demucs", "device": "cpu", "results": [{"id": j["id"], "ok": True, "seconds": 0.1} for j in jobs]}

        def fake_verify(path, orig, sr, words, cfg_, sung=False, method="hdemucs"):
            return {"ok": True, "checks": {"duration": {"ok": True}, "sync": {"ok": True}, "music_left": {"ok": True}}}
        M.separate_spans, M.verify = fake_sep, fake_verify
        M.sam_ready = lambda c: {"ok": False, "why": "not needed in this test"}
        cfg = {**M.settings(), "analysis": False}
        adir = run / "30-assets" / "music"
        adir.mkdir(parents=True, exist_ok=True)
        ri = M._music(run, cfg, adir, TM.args([out_l / "edl.json", out_s / "edl.json"], apply=True))
        vi = {v["video"]: v for v in ri["videos"]}
        patched = rj(out_l / "edl.json")
        mus = [m for s in patched["segments"] for m in s.get("mute") or [] if m.get("music")]
        lanes = [x for x in patched.get("sfx") or [] if x.get("music_clean")]
        check(ri["by_action"]["remove"] == 1 and len(sep_calls) == 1 and len(mus) == 1 and len(lanes) == 1 and Path(lanes[0]["file"]).is_file()
              and vi["S01"].get("skipped") == M.SHORTS_RULE and rj(out_s / "edl.json") == short_edl,
              "Isolation: the claimed song in the long video is recognised, scored (outcome A), separated, checked and patched; the short is not processed")
        check(editorial(patched) == editorial(long_edl), "the patch changes only the audio: every segment, cut, zoom, transition, sound effect and the "
                                                         "builder's own mute are the same")
        wj(out_d / "edl.json", patched | {"video": "L02"})
        state = rj(run / "state.json")
        state["videos"] = {"L01": {"kind": "long", "status": "built", "project": "test"}, "L02": {"kind": "long", "status": "verified", "export": "C:/x/L02.mp4"},
                           "S01": {"kind": "short", "status": "built"}}
        wj(run / "state.json", state)
        delivered_before = (out_d / "edl.json").read_bytes()
        cache_before = sorted(p.name for p in adir.glob("*"))

        # ------------------------------------------------------------ the resolver never builds a leftover patch into a short or a Non-Isolation video
        g = tmp / "guard"
        wj(g / "iso" / "L01" / "edl.json", patched)
        ci = cc("edl-check", "--run", run, "--edl", g / "iso" / "L01" / "edl.json")
        ri_ = rj(g / "iso" / "L01" / "resolved.json")
        sh_p = {**short_edl, "segments": [{**short_edl["segments"][0], "mute": [{"rec_from": 50.0, "rec_to": 60.0, "music": True, "why": "copied"}]}],
                "sfx": [{**lanes[0], "at": {"seg": "s1", "t": 5.0}}]}
        wj(g / "iso" / "S01" / "edl.json", sh_p)
        cs = cc("edl-check", "--run", run, "--edl", g / "iso" / "S01" / "edl.json")
        rs_ = rj(g / "iso" / "S01" / "resolved.json")
        check(song_muted(ri_["pieces"]) and ci["totals"]["sfx"] == 2 and "music_patch_left_out" not in ri_,
              "Isolation, long video: the patch is built (the song's stretch muted, the cleaned audio on a lane beside the sound effect)")
        check(not song_muted(rs_["pieces"]) and cs["totals"]["sfx"] == 0 and (cs.get("music_patch_left_out") or {}).get("music_mute_spans") == 1,
              "a short carrying a patch copied from a long video: left out, its original audio plays: " + str((cs.get("music_patch_left_out") or {}).get("why")))
        set_mode_raw(run, "non_isolation")      # the mode alone, without the switch (tested below): here only the resolver
        wj(g / "non" / "L01" / "edl.json", patched)
        cn = cc("edl-check", "--run", run, "--edl", g / "non" / "L01" / "edl.json")
        rn_ = rj(g / "non" / "L01" / "resolved.json")
        fz = norm(rj(tmp / "frozen-non_isolation" / "L01" / "resolved.json"))
        rn_cmp = norm({k: v for k, v in rn_.items() if k != "music_patch_left_out"})
        check(not song_muted(rn_["pieces"]) and cn["totals"]["sfx"] == 1 and rn_cmp == fz
              and (cn.get("music_patch_left_out") or {}).get("cleaned_audio_lanes") == 1,
              "Non-Isolation, an EDL still carrying the patch: left out, and the plan is the very one of the EDL before the music step"
              + ("" if rn_cmp == fz else " | differs at " + first_diff(rn_cmp, fz) + f" | sfx {cn.get('totals', {}).get('sfx')}"))
        set_mode_raw(run, "isolation")
        check(rj(out_l / "edl.json") == patched, "(the resolver checks did not touch the run's own EDLs)")

        # ------------------------------------------------------------ the switch: Isolation -> Non-Isolation
        sw = cc("state", "--run", run, "set", "music_isolation_mode=non_isolation").get("music_switch") or {}
        now_l = rj(out_l / "edl.json")
        check([x["video"] for x in sw.get("restored", [])] == ["L01"] and [x["video"] for x in sw.get("rebuild", [])] == ["L01"]
              and [x["video"] for x in sw.get("left_as_delivered", [])] == ["L02"],
              "the switch: L01's patch taken out and listed for a rebuild (its project was built), L02 (verified) left as it is, the short not listed")
        check(now_l == M.strip_patch(patched) and editorial(now_l) == editorial(long_edl) and rj(out_l / "edl.music-patched.json") == patched,
              "L01 plays its original soundtrack: only the music mute and the cleaned-audio lane are gone (a copy of the patched EDL kept)")
        check((out_d / "edl.json").read_bytes() == delivered_before and rj(out_s / "edl.json") == short_edl
              and sorted(p.name for p in adir.glob("*")) == cache_before and Path(lanes[0]["file"]).is_file(),
              "the delivered video's EDL is byte for byte the same, the short untouched, every cached file kept (the cleaned audio too)")
        mj = rj(out_l / "music.json")
        cn2 = cc("edl-check", "--run", run, "--edl", out_l / "edl.json")
        check(mj.get("mode") == "non_isolation" and not song_muted(rj(out_l / "resolved.json")["pieces"]) and cn2["totals"]["sfx"] == 1
              and "music_patch_left_out" not in cn2,
              "its record says Non-Isolation; the rebuild's plan has no muted stretch and only the sound effect"
              + ("" if mj.get("mode") == "non_isolation" and cn2.get("ok") else
                 f" | mode {mj.get('mode')}, sfx {(cn2.get('totals') or {}).get('sfx')}, left_out {cn2.get('music_patch_left_out')}, edl-check {cn2.get('ok')}"))
        again = cc("state", "--run", run, "set", "music_isolation_mode=non-isolation")
        check(again.get("ok") and "music_switch" not in again and rj(out_l / "edl.json") == now_l, "the same mode again: no switch, nothing changed")

        # ------------------------------------------------------------ the switch: Non-Isolation -> Isolation, then the music step reuses the caches
        before_switch = (out_l / "edl.json").read_bytes()
        sw2 = cc("state", "--run", run, "set", "music_isolation_mode=isolation").get("music_switch") or {}
        check([x["video"] for x in sw2.get("music_step", [])] == ["L01"] and [x["video"] for x in sw2.get("left_as_delivered", [])] == ["L02"]
              and (out_l / "edl.json").read_bytes() == before_switch,
              "back to Isolation: the switch itself processes nothing; L01 is listed for the music step (then a rebuild), L02 left as it is")
        n_sep = len(sep_calls)
        rb = M._music(run, cfg, adir, TM.args([out_l / "edl.json"], apply=True))
        re1 = rj(out_l / "edl.json")
        rb2 = M._music(run, cfg, adir, TM.args([out_l / "edl.json"], apply=True))
        re2 = rj(out_l / "edl.json")
        check(len(sep_calls) == n_sep and rb["analysed_s"] == 0 and re1 == patched and re2 == patched
              and sum(1 for s in re2["segments"] for m in s.get("mute") or [] if m.get("music")) == 1
              and sum(1 for x in re2.get("sfx") or [] if x.get("music_clean")) == 1 and rb2["analysed_s"] == 0,
              "the music step after the switch: nothing analysed or separated again (the caches), the same patch as before, applied once, never stacked")

        # ------------------------------------------------------------ a switch while a job runs: nothing is applied after it
        wj(out_l / "edl.json", long_edl)
        (adir / "separated.json").unlink(missing_ok=True)

        def sep_then_switch(jobs, cfg_, work):
            r_ = fake_sep(jobs, cfg_, work)
            st_ = rj(run / "state.json")
            st_["music_isolation_mode"] = "non_isolation"
            wj(run / "state.json", st_)
            return r_
        M.separate_spans = sep_then_switch
        rm_ = M._music(run, cfg, adir, TM.args([out_l / "edl.json"], apply=True))
        check(rm_.get("switched_during_job") and rm_.get("bypassed") and rj(out_l / "edl.json") == long_edl and (adir / "separated.json").is_file(),
              "switched to Non-Isolation during a job: its separation stays cached, nothing is applied, the EDL keeps its original sound")

        # ------------------------------------------------------------ a run made before the option: the music step runs as before
        st_ = rj(run / "state.json")
        st_.pop("music_isolation_mode", None)
        wj(run / "state.json", st_)
        leg = cc("music", "--run", run, "--spans", "0-120", "--no-analysis")
        check(leg.get("ok") and not leg.get("bypassed") and leg.get("music_intervals"),
              "no key (an older run): not bypassed, the detection runs as it always did: " + json.dumps(leg.get("music_intervals"))[:60])

        # ------------------------------------------------------------ an UNRESOLVED song never asks for another cut (the modes keep the same cuts)
        wj(out_l / "edl.json", long_edl)
        M.separate_spans = fake_sep
        M.verify = lambda *a_, **k_: {"ok": False, "checks": {"duration": {"ok": True}, "sync": {"ok": True}, "singer_under_speech": {"ok": False}}}
        M.sam_ready = lambda c: {"ok": False, "why": "not needed in this test"}
        M._music(run, cfg, adir, TM.args([out_l / "edl.json"], apply=True, force=True))
        un = rj(out_l / "music.json")["music"][0]
        check(un.get("unresolved") and "the cut stays as planned" in un["status"] and "shorten" not in un["status"] and rj(out_l / "edl.json") == long_edl,
              "Isolation, a song no method cleans: UNRESOLVED, the original audio kept, and the line never asks for a cut: " + un["status"][-70:])
    finally:
        for k, f in real.items():
            setattr(M, k, f)
        S.rec_settings = real_rec
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"test_music_mode: ok {N[0] - len(FAILED)} of {N[0]} | " + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
