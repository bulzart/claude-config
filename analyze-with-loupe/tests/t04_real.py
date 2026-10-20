"""Real data, read-only on the sources: the user's reference folder, a real guardrails PDF, the real Loupe library (qc-brief, no model call) and
one real clip through faster-whisper (the cached small model). Everything the toolkit writes goes to a temp library copy (AWL_HOME); nothing
under the real runs/ or Loupe's data is written. Opt-in: `python tests/run_all.py --real`, or run this file. With AWL_TEST_LIVE_KEEPER=1 it
also makes ONE real qc-consult and ONE real plan-hints (a few cents): the keeper is asked about a can that shrinks after a cut."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import check, finish, t, temp_library  # noqa: E402

REFS = Path(os.environ.get("AWL_TEST_REFS") or r"C:\Users\Glaresquare1\Documents\19.10")
PDF = Path(os.environ.get("AWL_TEST_PDF") or r"C:\Users\Glaresquare1\Documents\neurogum\assets\Content Guardrails.pdf")
V10 = REFS / "Video-39496.mp4"                       # the live run's V10: its insert out-point 7.52 s sits inside a white flash
if not REFS.is_dir():
    print("SKIP  the reference folder is not on this machine:", REFS)
    sys.exit(0)

home = temp_library("real")
ENV = {"AWL_HOME": str(home)}

# --- a real PDF with a text layer
if PDF.is_file():
    js, _, _ = t("doc-text", str(PDF), env=ENV)
    check(js["pdf"]["extractor"] == "pypdf" and js["pdf"]["pages"] >= 5 and js["pdf"]["chars"] > 5000 and js["pdf"]["image_only"] is False,
          f"a real guardrails PDF yields its text layer ({js['pdf']['pages']} pages, {js['pdf']['chars']} characters)")
    check("Guardrails" in js.get("text", "") or "guardrail" in js.get("text", "").lower(), "the extracted text reads as prose (the word guardrails is in it)")

# --- the seam profile on the real original: the flash the live run's planner found by hand
if V10.is_file():
    js, _, _ = t("seams", "--video", str(V10), "--at", "7.52", env=ENV)
    s = js["seams"][0]
    check(s["luma_max"] > 230 and s["luma_min"] < 110 and s["diff_max"] > 15, f"V10 at 7.52 s: the profile shows the flash (luma {s['luma_min']}-{s['luma_max']}, max frame difference {s['diff_max']})")

# --- one real clip through faster-whisper (the cached small model), both modes
clips = sorted(p for p in REFS.glob("*.mp4") if p.stat().st_size > 0)
clip = V10 if V10.is_file() else (clips[0] if clips else None)
if clip:
    js, _, _ = t("prep-video", str(clip), "--out", str(home.parent / "pv-frames"), "--audio-ingest", "frames-only", "--no-ocr", env=ENV)
    check(js["audio_ingest"] == "frames-only" and js["speech"]["ingested"] is False and not (home.parent / "pv-frames" / "transcript.json").exists(),
          f"real clip, frames only: no transcript written, speech.ingested false ({clip.name})")
    js, _, _ = t("prep-video", str(clip), "--out", str(home.parent / "pv-whisper"), "--audio-ingest", "whisper", "--no-ocr", env=ENV, timeout=900)
    sp = js.get("speech") or {}
    check(js["audio_ingest"] == "whisper" and sp.get("ingested") is True and sp.get("engine") in ("faster-whisper", "ffmpeg-whisper") and (home.parent / "pv-whisper" / "transcript.json").exists(),
          f"real clip, whisper: engine {sp.get('engine')} ({sp.get('model')}), {sp.get('n_words')} words, language {sp.get('language')}; transcript written")

# --- the real Loupe library, read-only: qc-brief makes no model call; the keeper is asked only when the user opted in
js, _, _ = t("loupe", "status", env=ENV)
if js.get("running"):
    js, _, _ = t("new-run", "--mode", "analyze", "--source", str(REFS), "--slug", "real", env=ENV)
    run = Path(js["run_dir"])
    t("state", "--run", str(run), "set", "model=wan3_0_prime", "analyze_submode=recreate", "audio_ingest=frames-only", env=ENV)
    js, _, _ = t("qc-brief", "--run", str(run), "--video", "01", "--product", "slim can", "--product-details", "slim 355 ml aluminium can, upright on a desk", "--kinds", "scale-size", env=ENV)
    check(js.get("mode") == "brief" and js.get("library_size", 0) >= 1 and isinstance(js.get("samples"), list), f"qc-brief reads the real library without a model call ({js.get('library_size')} samples, {len(js.get('samples') or [])} matched)")
    check(all(Path(s["composite_path"]).is_file() for s in js.get("samples") or []), "every matched sample's composite image exists")
    if os.environ.get("AWL_TEST_LIVE_KEEPER") == "1":
        js, _, _ = t("loupe", "ensure", env=ENV)
        check(js.get("ok") and js["keeper"]["state"] in ("in_sync", "booted", "synced", "syncing"), f"loupe ensure against the real keeper: {js['keeper']['state']}")
        js, _, _ = t("qc-consult", "--run", str(run), "--video", "01", "--question", "the slim can on the desk looks smaller after the cut at 3 s than before it; the label reads but the can's height against the laptop changed",
                     "--kinds", "scale-size,continuity", "--product-details", "slim 355 ml aluminium can, upright on a desk beside a laptop", "--checkpoint", "cut 3.0-3.4: the can's height against the laptop", env=ENV, timeout=900)
        check(js.get("mode") in ("keeper", "fallback") and js.get("saved") and Path(js["saved"]).is_file(), f"a real qc-consult answers (mode {js.get('mode')}, {len(js.get('relevant') or js.get('samples') or [])} leads, {js.get('ms')} ms) and is saved")
        js, _, _ = t("plan-hints", "--run", str(run), "--video", "01", "--beats", "Beat 1: he sets the slim can on the desk beside the laptop.\nBeat 2: a cut; the can is still on the desk, same size against the laptop.",
                     "--product", "slim can", "--product-details", "slim 355 ml aluminium can, upright", env=ENV, timeout=900)
        check(js.get("ok") and js.get("mode") in ("keeper", "empty", "unavailable") and isinstance(js.get("hints"), list) and len(js["hints"]) <= 3,
              f"a real plan-hints answers sparsely (mode {js.get('mode')}, {len(js.get('hints') or [])} hint(s), held back {js.get('held_back')})")
else:
    print("SKIP  Loupe is not running: the real-library checks need it (python ~/.claude/loupe/loupe.py serve)")

finish()
