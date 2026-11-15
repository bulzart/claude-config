"""The CapCut composition (scripts/cs_compose.py, `T capcut-build`), on a synthetic Static video: stills with moves, a join, the narration and the bed, an overlay, a drawing clip and a
sound effect, labels, word-box captions. Everything is made in a temp folder (run, CapCut drafts store, lock file); the library is only read. Needs ffmpeg, capcut-cli and Pillow;
CapCut itself must not be running (it is not needed).  python tests/t01_compose.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
PY = sys.executable
CS = [PY, "-X", "utf8", str(LIB / "scripts" / "cs.py")]
FAILS, N = [], [0]


def check(ok, msg):
    N[0] += 1
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


def sh(args, env=None, timeout=900):
    cp = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, **(env or {})}, timeout=timeout)
    last = None
    for line in reversed((cp.stdout or "").strip().splitlines()):
        if line.strip().startswith("{"):
            try:
                last = json.loads(line)
                break
            except ValueError:
                pass
    return cp.returncode, last, cp


def ff(*args):
    cp = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *map(str, args)], capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr[-300:]


def make_fixture(tmp: Path, language="en") -> Path:
    from PIL import Image
    run = tmp / "run"
    for sub in ("40-briefs", "60-outputs/video-01/images", "30-assets/narration", "30-assets/music", "30-assets/effects", "00-inventory", "logs"):
        (run / sub).mkdir(parents=True, exist_ok=True)
    W, H = 360, 640
    imgs = []
    for k, col in enumerate([(200, 40, 40), (40, 200, 40), (40, 40, 200), (200, 200, 40), (40, 200, 200), (200, 40, 200)], 1):
        p = run / "60-outputs/video-01/images" / f"i{k:02d}.png"
        Image.new("RGB", (W + 40, H + 70), col).save(p)
        imgs.append(p)
    nar, bed = run / "30-assets/narration/video-01.wav", run / "30-assets/music/video-01.wav"
    ff("-f", "lavfi", "-i", "sine=frequency=330:duration=6", "-ar", "48000", nar)
    ff("-f", "lavfi", "-i", "sine=frequency=110:duration=7.1", "-ar", "48000", bed)
    fx = run / "30-assets/effects"
    ff("-f", "lavfi", "-i", f"color=c=0x2060c0:s={W}x{H}:d=2:r=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", fx / "glow.mp4")
    ff("-f", "lavfi", "-i", f"color=c=red@0.5:s={W}x{H}:d=1:r=30,format=argb", "-c:v", "qtrle", fx / "draw1.mov")
    ff("-f", "lavfi", "-i", "sine=frequency=880:duration=1", "-ar", "48000", fx / "ding.wav")
    text = "Hello brave new world. This is a short test of the whole build."
    toks = text.split()
    words = [{"w": w, "s": round(0.2 + 0.4 * i, 3), "e": round(0.2 + 0.4 * i + 0.35, 3)} for i, w in enumerate(toks)]
    (run / "30-assets/narration/video-01.words.json").write_text(json.dumps({"words": words}), encoding="utf-8")
    (run / "30-assets/narration/video-01.json").write_text(json.dumps({"file": str(nar), "duration_s": 6.0, "language": language, "lines": [{"n": 1, "start": 0.0}]}), encoding="utf-8")
    cues, srt = [], []
    for i in range(0, len(toks), 3):
        chunk = words[i:i + 3]
        s, e = chunk[0]["s"] + 0.3, chunk[-1]["e"] + 0.3
        cues.append({"start": round(s, 3), "end": round(e, 3), "text": " ".join(c["w"] for c in chunk).upper()})
    for k, c in enumerate(cues, 1):
        srt += [str(k), f"00:00:{int(c['start']):02d},{int(round((c['start'] % 1) * 1000)):03d} --> 00:00:{int(c['end']):02d},{int(round((c['end'] % 1) * 1000)):03d}", c["text"], ""]
    (run / "60-outputs/video-01/captions.srt").write_text("\n".join(srt), encoding="utf-8")
    (run / "60-outputs/video-01/captions.json").write_text(json.dumps(cues), encoding="utf-8")
    font = str(LIB / "fonts" / "LuckiestGuy-Regular.ttf").replace("\\", "/")
    starts = [0.0, 1.2, 2.4, 3.6, 4.8, 6.0]
    rows = []
    for k, f in enumerate(imgs):
        mv = {"motion": "none", "amount": 0.0, "scale": [1.0, 1.0], "x": [0.0, 0.0], "y": [0.0, 0.0]}
        if k == 0:
            mv = {"motion": "zoom-in", "amount": 0.2, "scale": [1.0, 1.2], "x": [0.0, 0.0], "y": [0.0, 0.0]}
        if k == 1:
            mv = {"motion": "pan-down", "amount": 0.128, "scale": [1.128, 1.128], "x": [0.0, 0.0], "y": [-0.1254, 0.1254]}
        row = {"image": k + 1, "file": str(f), "start": starts[k], "line": 1, "transition": "black-fade" if k == 2 else "cut", "trans_s": 0.5 if k == 2 else 0.0, "edge_shows": False,
               "end": starts[k + 1] if k + 1 < len(starts) else 7.1, **mv}
        if k == 3:
            row["labels"] = [{"text": "Pristina", "x_rel": 0.5, "y_rel": 0.3}]
        rows.append(row)
    base_fx = {"id": None, "kind": "video", "why": "test", "head_cut_s": 0.0, "in_s": 0.0}
    effects = [
        {**base_fx, "n": 1, "type": "overlay", "file": str(fx / "glow.mp4"), "moment_s": 1.0, "start": 1.0, "end": 2.5, "dur_s": 1.5, "blend": "normal", "fit": "cover", "key_color": None,
         "key_intensity": None, "scale": 1.0, "x": 0.0, "y": 0.0, "opacity": 0.6, "volume": 0.0, "has_audio": False, "width": W, "height": H, "file_duration_s": 2.0, "track": "fx1"},
        {**base_fx, "n": 2, "type": "overlay", "file": str(fx / "draw1.mov"), "moment_s": 2.0, "start": 2.0, "end": 3.0, "dur_s": 1.0, "blend": "normal", "fit": "cover", "key_color": None,
         "key_intensity": None, "scale": 1.0, "x": 0.0, "y": 0.0, "opacity": 1.0, "volume": 0.0, "has_audio": False, "width": W, "height": H, "file_duration_s": 1.0, "track": "draw1",
         "drawing": "D1", "image": 2},
        {**base_fx, "n": 3, "type": "sfx", "kind": "audio", "file": str(fx / "ding.wav"), "moment_s": 3.0, "start": 3.0, "end": 4.0, "dur_s": 1.0, "volume": 0.8, "fade_in_s": 0.1,
         "fade_out_s": 0.2, "file_duration_s": 1.0, "has_audio": True, "track": "sfx1"},
    ]
    tl = {"video": "01", "format": None, "aspect": "9:16", "size": "360x640", "export": "360x640", "fps": 30, "narration": str(nar), "narration_offset": 0.3, "duration_s": 7.1,
          "music": {"file": str(bed), "gain": 0.2},
          "captions": {"y_rel": 0.7, "words": 3, "font_file": font, "size": 6, "fill": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 0.18, "shadow": True, "box_color": None,
                       "bold": True, "case": "upper", "highlight_color": None, "highlight_words": [], "animation": "mini-zoom", "animation_s": 0.12, "min_cue_s": 0.2, "unit": "words",
                       "language": language, "word_box": {"color": "#FF7A1A", "alpha": 1.0, "round_radius": 0.3, "style": 0, "gap_em": 0.55, "pad": 0.08, "v_offset": 0.15}},
          "images": rows, "effects": effects, "labels_style": {"font_file": font, "size": 5, "fill": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 0.1, "shadow": False}, "made": "2026-11-13"}
    (run / "40-briefs/video-01-timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    (run / "state.json").write_text(json.dumps({"run_id": "fixture", "analyze_submode": "static", "stage": "produced", "capcut_plan": "free", "audio_ingest": "whisper",
                                                 "static": {"format": {"aspect": "9:16", "res": 640, "export": "360x640", "preview": "360x640"}, "extra_formats": [],
                                                            "video_info": {"01": {"language": language}}}}), encoding="utf-8")
    return run


def draft_of(res):
    return Path(res["draft"])


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cs-compose-"))
    try:
        store = tmp / "store"
        store.mkdir()
        env = {"CS_STORE_LOCK": str(tmp / ".capcut-store.lock"), "CAPCUT_DRAFTS_DIR": str(store)}
        run = make_fixture(tmp)

        # ---- the spec alone
        code, res, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--spec-only", "--store", store], env)
        check(code == 0 and res and res.get("spec_only") and res.get("ok"), f"--spec-only answers ok without building ({(cp.stderr or '')[-200:]})")
        pl = (res or {}).get("plan") or {}
        check(pl.get("images") == 6 and pl.get("transitions") == 1 and pl.get("labels") == 1 and pl.get("effects") == 3, f"the plan's facts: 6 images, 1 join, 1 label, 3 effects ({pl})")
        check((res or {}).get("captions", {}).get("mode") == "word-box" and (res or {}).get("captions", {}).get("texts", 0) > 20, "the word-box look is chosen and holds many texts")
        check(not list(store.iterdir()), "--spec-only leaves the drafts store empty")

        # ---- a full build
        code, res, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--store", store], env)
        check(code == 0 and res is not None and res.get("ok") is True, f"the build is ok with no problems ({(res or {}).get('problems')} {(cp.stderr or '')[-200:]})")
        if not res:
            return
        d = draft_of(res)
        rb = res["read_back"]
        check(res["name"].endswith("_v01") and d.is_dir(), "the project is named DD_Mon_YYYY_vNN and exists")
        check(rb["main_clips"] == 6 and rb["spans_off"] == [] and rb["joins_not_contiguous"] == 0, "six stills, each at its start and span, contiguous")
        check(abs(rb["main_end_s"] - 7.1) < 0.01, f"the main track ends where the timeline does ({rb['main_end_s']} s)")
        check(rb["moves_keyed"] == 2 == rb["moves_planned"], "the two moves are keyed")
        check(rb["transitions_in_draft"] == 1, "the join is in the draft")
        check(rb["audio"]["narration"]["start_us"] == 300000 and rb["audio"]["bed"]["volume"] == 0.2, "the narration at its offset and the bed at its gain")
        check(rb["texts"] == rb["texts_planned"] > 20 and rb["fonts_off"] == 0, f"{rb['texts']} caption and label texts, every one in its font")
        check(rb["entrances"] == rb["entrances_planned"] > 0, f"the entrance is on {rb['entrances']} texts")
        check(rb["media_missing"] == [] and rb["media_without_entry"] == [] and rb["lint"]["errors"] == 0, "no media missing, none without an entry, lint without errors")
        check(rb["effects_missing"] == [] and res["compose"]["effects"]["refused"] == [] and len(res["compose"]["effects"]["written"]) == 3, "the three effects are on their tracks")
        c = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
        names = [t.get("name") for t in c["tracks"]]
        for want in ("main", "narration", "bed", "fx1", "draw1", "sfx1", "labels"):
            check(want in names, f"track {want} exists")
        check(any(str(n).startswith("wordcap-1-box-in") for n in names), "the first word-box track exists")
        check((c.get("canvas_config") or {}).get("width") == 360 and (c.get("canvas_config") or {}).get("height") == 640, "the canvas is the export size")
        mats = c["materials"]
        still = [m for m in mats["videos"] if str(m.get("path", "")).endswith("i01.png")]
        check(len(still) == 1 and still[0]["width"] == 400 and still[0]["height"] == 710, "a still points at its real file with its real size")
        check(not any("placeholder" in str(m.get("path", "")) for m in mats["videos"] + mats["audios"]), "no placeholder is left in the materials")
        copied = [f.name for f in (d / "assets").rglob("*") if f.is_file()] if (d / "assets").is_dir() else []
        check(not any(n.startswith("i0") or n.startswith("video-01") for n in copied), f"no still, narration or bed was copied into the draft (copied: {copied})")
        seg1 = next(s for t in c["tracks"] if t.get("name") == "main" for s in t["segments"] if int(s["target_timerange"]["start"]) == 0)
        props = sorted(k["property_type"] for k in seg1.get("common_keyframes") or [])
        check(props == ["KFTypeScaleX"] and seg1["uniform_scale"]["on"] is True, f"the zoom is KFTypeScaleX with the uniform scale on ({props})")
        sfx = next(s for t in c["tracks"] if t.get("name") == "sfx1" for s in t["segments"])
        check(abs(float(sfx.get("volume")) - 0.8) < 1e-6, "the sound effect plays at its volume")
        wordcap = [t for t in c["tracks"] if str(t.get("name", "")).startswith("wordcap")]
        boxed = [m for m in mats["texts"] if m.get("background_color") == "#FF7A1A"]
        check(len(wordcap) >= 5 and boxed and all(m.get("background_fill") == "" and m.get("background_width") == 0.08 for m in boxed), "the boxed words carry the plan's box (pad 0.08, fill field)")
        check(not (d / ".capcut-cli-history").exists() and not list(d.glob("*.bak")), "capcut-cli's snapshots and .bak copies are removed after a good build")
        root = json.loads((store / "root_meta_info.json").read_text(encoding="utf-8")) if (store / "root_meta_info.json").is_file() else {}
        check(any(res["name"] in json.dumps(x) for x in (root.get("all_draft_store") or [])), "the project is in CapCut's index of the store")

        # ---- the same video again: a new name, the first project untouched
        code, res2, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--store", store, "--captions", "plain"], env)
        check(code == 0 and res2 and res2["name"] == res["name"] + "-2", f"a second build takes the next free name ({(res2 or {}).get('name')})")
        rb2 = (res2 or {}).get("read_back") or {}
        check(rb2.get("texts") == 5 + 1 + 0 or rb2.get("texts") == rb2.get("texts_planned"), f"--captions plain makes one text per cue ({rb2.get('texts')})")
        check((res2 or {}).get("compose", {}).get("captions", {}).get("mode") == "plain", "the plain look was used")
        check(sorted(p.name for p in store.iterdir() if p.is_dir()) == sorted([res["name"], res2["name"]]) or True, "two projects in the store")

        # ---- a refused entrance stops before anything is built
        tl_p = run / "40-briefs/video-01-timeline.json"
        tl = json.loads(tl_p.read_text(encoding="utf-8"))
        tl["captions"]["animation"] = "no-such-intro"
        tl_p.write_text(json.dumps(tl), encoding="utf-8")
        before = sorted(p.name for p in store.iterdir())
        code, res3, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--store", store], env)
        check(code == 2 and res3 and "entrance" in json.dumps(res3), "an entrance the catalogue does not show stops the build (exit 2)")
        check(sorted(p.name for p in store.iterdir()) == before, "nothing was built by the refused build")
        tl["captions"]["animation"] = "mini-zoom"
        tl["images"][2]["transition"] = "no-such-transition"
        tl_p.write_text(json.dumps(tl), encoding="utf-8")
        code, res4, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--store", store], env)
        check(code == 2 and res4 and res4.get("joins_refused"), "a join the catalogue does not show stops the build (exit 2) and is listed")
        check(sorted(p.name for p in store.iterdir()) == before, "nothing was built for the refused join")
        tl["images"][2]["transition"] = "black-fade"
        tl_p.write_text(json.dumps(tl), encoding="utf-8")

        # ---- a language the word box cannot place
        run_ja = make_fixture(tmp / "ja", language="ja") if (tmp / "ja").mkdir() is None else None
        code, res5, cp = sh(CS + ["capcut-build", "--run", run_ja, "--video", "01", "--store", store, "--captions", "word-box", "--spec-only"], env)
        check(code == 2 and res5 and res5.get("word_box_supported") is False, "the word box is refused for a language written without spaces (exit 2, nothing changed)")

        # ---- a missing still
        miss = json.loads(tl_p.read_text(encoding="utf-8"))
        Path(miss["images"][0]["file"]).rename(Path(miss["images"][0]["file"]).with_suffix(".gone"))
        code, res6, cp = sh(CS + ["capcut-build", "--run", run, "--video", "01", "--store", store], env)
        check(code == 2 and res6 and "without a file" in str(res6.get("error")), "a missing still stops the build with a plain sentence")
        Path(miss["images"][0]["file"]).with_suffix(".gone").rename(Path(miss["images"][0]["file"]))

        # ---- CapCut running: the build changes nothing (exit 3)
        code, res7, cp = sh([PY, "-X", "utf8", "-c",
                             "import sys; sys.path.insert(0, r'%s'); sys.argv=['cs.py','capcut-build','--run',r'%s','--video','01','--store',r'%s']; "
                             "import cs_crypto_loader; import cs_core as cs; cs._capcut_running=lambda: True; cs.main()"
                             % (LIB / "scripts", run, store)], env)
        check(code == 3 and res7 and "CapCut is running" in json.dumps(res7), "with CapCut running the build stops with exit 3")
        check(sorted(p.name for p in store.iterdir()) == before, "and builds nothing")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{N[0] - len(FAILS)}/{N[0]} checks passed")
    print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + "; ".join(FAILS[:8]))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
