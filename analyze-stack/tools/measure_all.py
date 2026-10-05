"""measure_all.py - Stage 1 driver: intake (when given a video) then probe -> cuts -> keyframes -> audio -> transcribe -> ocr -> visual_stats.

Usage:
  python measure_all.py <video-or-url> --run-root C:\\...\\runs [--slug s] [options]
  python measure_all.py <existing-run-dir> [options]
  python measure_all.py --run-dir <existing-run-dir> [options]
Options: [--skip-transcribe] [--whisper-model small] [--language auto] [--fps N] [--skip step,step] [--redo] [--quiet]

Each script runs as its own process; a failing script is logged and the driver continues (exit code 0 when every
script succeeded, 1 when at least one failed, 2 when intake failed). Steps whose output already exists are skipped
unless --redo. Writes 10-measure\\measure-summary.md and state.json (stage "measured", next_step "analysis",
files index, measure.timings). Prints the run dir as the last stdout line.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

TOOLS = Path(__file__).resolve().parent
STEPS = [  # (name, script, output that marks it done)
    ("probe", "probe.py", "10-measure/probe.json"),
    ("cuts", "cuts.py", "10-measure/shots.json"),
    ("keyframes", "keyframes.py", "10-measure/keyframes.json"),
    ("audio", "audio.py", "10-measure/audio-features.json"),
    ("transcribe", "transcribe.py", "10-measure/transcript.json"),
    ("ocr", "ocr.py", "10-measure/ocr.json"),
    ("visual_stats", "visual_stats.py", "10-measure/visual-stats.json"),
]


def run_step(name: str, script: str, args: list[str], log: common.Log, quiet: bool) -> dict:
    cmd = [common.python_exe(), str(TOOLS / script)] + args + (["--quiet"] if quiet else [])
    log.cmd(cmd)
    log.info(f"=== {name}: {script} {' '.join(args)}")
    t0 = time.time()
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, timeout=7200)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        rc = -1
    el = round(time.time() - t0, 2)
    log._write("RESULT", f"{name} rc={rc} in {el}s")
    if rc != 0:
        log.warn(f"{name} failed (rc={rc}) after {el}s - continuing")
    else:
        log.info(f"{name} ok in {el}s")
    return {"step": name, "script": script, "rc": rc, "ok": rc == 0, "elapsed_s": el}


def looks_like_run_dir(p: Path) -> bool:
    return p.is_dir() and ((p / "00-input" / "source.mp4").exists() or (p / "state.json").exists())


def md_table(rows: list[list], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) if c is not None else "" for c in r) + " |")
    return "\n".join(out)


def build_summary(run_dir: Path, results: list[dict], total_s: float) -> str:
    m = run_dir / "10-measure"
    probe = common.read_json(m / "probe.json") or {}
    shots = common.read_json(m / "shots.json") or {}
    cuts = common.read_json(m / "cuts.json") or {}
    kf = common.read_json(m / "keyframes.json") or {}
    af = common.read_json(m / "audio-features.json") or {}
    tr = common.read_json(m / "transcript.json") or {}
    ocr = common.read_json(m / "ocr.json") or {}
    vs = common.read_json(m / "visual-stats.json") or {}
    inp = common.read_json(run_dir / "00-input" / "input.json") or {}
    L = []
    L.append(f"# Measurement summary - {run_dir.name}\n")
    L.append(f"Source: `{inp.get('original_name') or probe.get('source', '?')}` ({inp.get('origin', 'file')}"
             f"{', ' + inp['original_url'] if inp.get('original_url') else ''}); run folder `{run_dir}`; measured {common.now_iso()}.\n")
    L.append("Every number below is measured by a script; the method and threshold sit next to it in the JSON files. "
             "Treat them as measurements, not interpretations; go to the frames before claiming anything frame-accurate.\n")

    # specs
    L.append("## 1. Specs (probe.json)\n")
    if probe:
        v, aud = probe.get("video", {}), probe.get("audio", [])
        a0 = aud[0] if aud else {}
        L.append(md_table([
            ["duration", f"{probe.get('duration_s')} s ({probe.get('duration_hms')})"],
            ["display size", f"{probe.get('display_width')}x{probe.get('display_height')} ({probe.get('orientation')}, rotation {probe.get('rotation')})"],
            ["aspect ratio", f"{probe.get('aspect_ratio')} (nearest {probe.get('aspect_nearest')}, {probe.get('aspect_decimal')})"],
            ["fps", f"{(probe.get('fps') or {}).get('value')} (r_frame_rate {(probe.get('fps') or {}).get('r_frame_rate')}, avg {(probe.get('fps') or {}).get('avg_frame_rate')})"],
            ["frames", f"{probe.get('nb_frames')} ({probe.get('nb_frames_source')})"],
            ["video", f"{v.get('codec')} {v.get('profile')} {v.get('pix_fmt')} {v.get('color_space')} {v.get('bitrate') and str(round(v['bitrate'] / 1000)) + ' kb/s'}"],
            ["audio", (f"{a0.get('codec')} {a0.get('profile') or ''} {a0.get('sample_rate')} Hz {a0.get('channels')} ch "
                       f"{a0.get('bitrate') and str(round(a0['bitrate'] / 1000)) + ' kb/s'}") if aud else "none"],
            ["container", f"{(probe.get('container') or {}).get('format_name')} {common.human_size((probe.get('container') or {}).get('size_bytes') or 0)}"],
        ], ["field", "value"]))
    else:
        L.append("_probe.json missing_")
    L.append("")

    # shots + pacing
    L.append("## 2. Shots and pacing (cuts.json, shots.json)\n")
    if shots:
        p = shots.get("pacing", {})
        det = cuts.get("detectors", {})
        L.append(f"- **{shots.get('n_shots')} shots** from {cuts.get('n_cuts_hard')} hard cuts (+{cuts.get('n_candidates')} unconfirmed candidates), "
                 f"rule: {cuts.get('rule')}.")
        L.append(f"- Detectors: ContentDetector(27) {det.get('content', {}).get('n')} cuts, AdaptiveDetector(3) {det.get('adaptive', {}).get('n')}, "
                 f"ffmpeg scene>0.30 {det.get('scene030', {}).get('n')}, scene>0.08 {det.get('scene008', {}).get('n_raw')} raw, "
                 f"scdet(10) {det.get('scdet', {}).get('n')}; merged within {cuts.get('merge_window_s')} s.")
        L.append(f"- Shot length: mean {p.get('mean_shot_s')} s, median {p.get('median_shot_s')} s, min {p.get('min_shot_s')} s, max {p.get('max_shot_s')} s; "
                 f"{p.get('cuts_per_10s_avg')} cuts per 10 s on average; fastest window {p.get('fastest_window')}, slowest {p.get('slowest_window')}; "
                 f"{p.get('shots_under_1s')} shots under 1 s, {p.get('shots_over_5s')} over 5 s.")
        L.append(f"- Freeze spans: {len(shots.get('freeze_spans', []))}, black spans: {len(shots.get('black_spans', []))} ({shots.get('freeze_black_params')}).\n")
        rows = []
        cam = {s["id"]: s.get("camera_motion", {}) for s in vs.get("shots", [])} if vs else {}
        for s in shots.get("shots", []):
            ci = s.get("cut_in") or {}
            c = cam.get(s["id"], {})
            rows.append([s["id"], f"{s['start']:.2f}", f"{s['end']:.2f}", f"{s['duration']:.2f}",
                         f"{ci.get('confidence', '')}{'/' + str(ci.get('score')) if ci.get('score') is not None else ''}" if ci else "start",
                         c.get("label", ""), c.get("magnitude_px_s", "")])
        L.append(md_table(rows, ["shot", "start s", "end s", "dur s", "cut-in conf/score", "camera", "flow px/s"]))
    else:
        L.append("_shots.json missing_")
    L.append("")

    # keyframes
    L.append("## 3. Keyframes and contact sheets (keyframes.json, contact-sheets\\index.json)\n")
    if kf:
        L.append(f"- Sampled {kf.get('n_sampled')} frames at {kf.get('sample_fps')} fps ({kf.get('sample_fps_reason')}); "
                 f"{kf.get('n_shot_frames')} shot frames (first/mid/last, full resolution) in `10-measure\\keyframes\\shots\\`.")
        L.append(f"- Contact sheets ({len(kf.get('contact_sheets', []))}): " + ", ".join(f"`{s}`" for s in kf.get("contact_sheets", [])) +
                 " - each cell carries its timestamp and shot id; `contact-sheets\\index.json` maps sheet/cell -> t/shot/frame.")
    else:
        L.append("_keyframes.json missing_")
    L.append("")

    # transcript
    L.append("## 4. Transcript excerpt (transcript.json / .srt / .txt)\n")
    if tr:
        if tr.get("has_speech"):
            L.append(f"- {tr.get('engine')} {tr.get('model')}: language {tr.get('language')} (p={tr.get('language_probability')}), "
                     f"{tr.get('n_segments')} segments, {tr.get('n_words')} words, speech {tr.get('speech_s')} s, "
                     f"{tr.get('wpm_speech_only')} WPM (speech-only) / {tr.get('wpm_whole_video')} WPM (whole video).")
            L.append("- `transcript.srt` is a sidecar for the external caption tool and for analysis only - never rendered into an edit.\n")
            for s in tr.get("segments", [])[:12]:
                L.append(f"  - [{common.fmt_mmss(s['start'])} - {common.fmt_mmss(s['end'])}] {s['text']}")
            if tr.get("n_segments", 0) > 12:
                L.append(f"  - ... {tr['n_segments'] - 12} more segments in transcript.json")
        else:
            L.append(f"- **No speech detected** ({tr.get('engine')} {tr.get('model')}; language guess {tr.get('language')} p={tr.get('language_probability')}).")
    elif (m / "transcript.error.txt").exists():
        L.append(f"- transcription FAILED: see `10-measure\\transcript.error.txt`")
    else:
        L.append("_transcription skipped_")
    L.append("")

    # OCR
    L.append("## 5. On-screen text spans (ocr.json)\n")
    if ocr:
        if ocr.get("spans"):
            rows = [[sp["id"], f"{sp['start']:.2f}", f"{sp['end']:.2f}", sp["position"], sp["size_class"], sp["n_frames"],
                     "noise?" if sp.get("likely_noise") else sp["kind_hint"].split(" ")[0], sp["text"].replace("|", "/")]
                    for sp in ocr["spans"]]
            L.append(md_table(rows, ["#", "start", "end", "position", "size", "frames", "hint", "text (OCR - verify on the frame)"]))
            if ocr.get("n_spans_likely_noise"):
                L.append(f"\n{ocr['n_spans_likely_noise']} of {len(ocr['spans'])} spans are flagged `noise?` (1-2 characters or a weak "
                         "one-frame hit) - usually fragments of physical labels; check the frame before quoting any of them.")
        else:
            L.append("- no on-screen text detected (score >= %s)" % ocr.get("min_score"))
        if ocr.get("brand_candidates"):
            L.append("\nBrand / logo candidates: " + "; ".join(f"\"{c['text']}\" ({', '.join(c['reasons'][:2])})" for c in ocr["brand_candidates"][:10]))
        if ocr.get("handles") or ocr.get("hashtags") or ocr.get("urls"):
            L.append("Handles: " + ", ".join(h["handle"] for h in ocr.get("handles", [])) + "; hashtags: " +
                     ", ".join(h["hashtag"] for h in ocr.get("hashtags", [])) + "; urls: " + ", ".join(u["url"] for u in ocr.get("urls", [])))
    else:
        L.append("_ocr.json missing_")
    L.append("")

    # audio
    L.append("## 6. Audio profile (audio-features.json)\n")
    if af:
        if af.get("has_audio"):
            lo = af.get("loudness", {})
            L.append(f"- Tempo {af.get('tempo_bpm')} BPM ({af.get('n_beats')} beats, {af.get('n_onsets')} onsets; {af.get('feature_method', '').split(' (')[0]}); "
                     f"spectral centroid mean {af.get('spectral_centroid_mean_hz')} Hz; RMS peak {af.get('rms_peak_db')} dBFS.")
            L.append(f"- Loudness: integrated {lo.get('integrated_lufs')} LUFS, LRA {lo.get('lra_lu')} LU, true peak {lo.get('true_peak_dbtp')} dBTP "
                     f"(delivery QA target -14 LUFS / -1.5 dBTP).")
            sil = af.get("silence_spans", [])
            L.append(f"- Dead air (silencedetect {af.get('silence_params', {}).get('noise_db')} dB, >= {af.get('silence_params', {}).get('min_s')} s): "
                     f"{len(sil)} spans, {af.get('dead_air_total_s')} s total" + (": " + ", ".join(f"{s['start']:.2f}-{s['end']:.2f}" for s in sil[:10]) if sil else "") + ".")
            L.append(f"- Segmentation ({af.get('segmentation_method')}): {af.get('segmentation_summary')}.")
            segs = af.get("segmentation", [])
            if segs:
                L.append("  " + "; ".join(f"{s['label']} {s['start']:.1f}-{s['end']:.1f}" for s in segs[:20]) + (" ..." if len(segs) > 20 else ""))
            cb = af.get("cuts_vs_beats")
            if cb:
                L.append(f"- Cuts on the beat (within {cb['window_s']} s): {cb['n_on_beat']}/{cb['n_cuts']} (ratio {cb['ratio']}).")
        else:
            L.append("- **No audio stream** in the source.")
    else:
        L.append("_audio-features.json missing_")
    L.append("")

    # camera motion + style
    L.append("## 7. Camera motion summary (visual-stats.json)\n")
    if vs:
        cm = vs.get("global", {}).get("camera_motion_summary")
        if cm:
            L.append(f"- Dominant: **{cm.get('dominant')}**; by screen time {cm.get('by_screen_time_s')}; handheld fraction {cm.get('handheld_fraction')}, "
                     f"static fraction {cm.get('static_fraction')}; mean flow {cm.get('mean_magnitude_px_s')} px/s at {a_w(vs)} px. "
                     f"Labels are heuristic (see method in the JSON); the per-shot table in section 2 lists them.")
        else:
            L.append("- motion pass skipped")
        L.append("")
        L.append("## 8. Style cues (visual-stats.json global)\n")
        g = vs.get("global", {})
        L.append(f"- Palette (k=5, whole video): " + ", ".join(f"{p['hex']} {int(p['share'] * 100)}%" for p in g.get("palette_k5", [])) +
                 f"; distinct colours >= 3 % in k=8: {g.get('palette_size_over_3pct')}.")
        L.append(f"- Brightness {g.get('brightness_mean')} (range {g.get('brightness_range')}), contrast {g.get('contrast_mean')}, saturation {g.get('saturation_mean')}, "
                 f"colourfulness {g.get('colourfulness_mean')}.")
        L.append(f"- Edge density mean {g.get('edge_density', {}).get('mean')} (p10 {g.get('edge_density', {}).get('p10')}, p50 {g.get('edge_density', {}).get('p50')}, "
                 f"p90 {g.get('edge_density', {}).get('p90')}); flat-colour ratio {g.get('flat_colour_ratio')}; gradient smoothness {g.get('gradient_smoothness')}; "
                 f"hard-edge ratio {g.get('hard_edge_ratio_mean')}; noise {g.get('noise_mean')}; colour entropy {g.get('colour_entropy_bits_mean')} bits.")
        sh = g.get("style_hints", {})
        L.append(f"- Style hints (0-1, hints only): real footage {sh.get('real_footage')}, 2D flat animation {sh.get('animation_2d_flat')}, "
                 f"sketch/line art {sh.get('sketch_or_line_art')}; 3D animation not separable from real footage by these cues - decide from the sheets.")
    else:
        L.append("_visual-stats.json missing_")
    L.append("")

    # files + timings
    L.append("## 9. Files\n")
    files = sorted(p for p in m.rglob("*") if p.is_file() and "_work" not in p.parts)
    big = [p for p in files if p.suffix.lower() in (".json", ".srt", ".txt", ".wav", ".md")]
    L.append("\n".join(f"- `{common.rel(run_dir, p)}` ({common.human_size(p.stat().st_size)})" for p in big))
    n_jpg = sum(1 for p in files if p.suffix.lower() == ".jpg")
    L.append(f"- {n_jpg} JPEG frames/sheets under `10-measure\\keyframes\\` and `10-measure\\contact-sheets\\`")
    L.append("")
    L.append("## 10. Script timings\n")
    L.append(md_table([[r["step"], r["script"],
                        ("skipped: " + r.get("note", "")) if r.get("skipped") else ("ok" if r["ok"] else f"FAILED rc={r['rc']}"),
                        r["elapsed_s"]] for r in results] +
                      [["total", "measure_all.py", "this invocation", round(total_s, 2)]], ["step", "script", "status", "seconds"]))
    fails = [r for r in results if not r["ok"]]
    if fails:
        L.append("\n**Failed steps:** " + ", ".join(r["step"] for r in fails) + " - see `10-measure\\measure.log`.")
    return "\n".join(L) + "\n"


def a_w(vs: dict) -> str:
    mm = (vs.get("method") or {}).get("motion") or ""
    m = re.search(r"on (\d+) px", mm)
    return m.group(1) if m else "?"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Stage 1 measurement driver")
    ap.add_argument("source", nargs="?", default=None, help="video file, http(s) link, or an existing run dir")
    ap.add_argument("--run-dir", default=None, help="existing run dir (alternative to the positional run dir)")
    ap.add_argument("--run-root", default=str(common.DEFAULT_RUN_ROOT))
    ap.add_argument("--slug", default=None)
    ap.add_argument("--skip-transcribe", action="store_true")
    ap.add_argument("--whisper-model", default="small")
    ap.add_argument("--language", default="auto")
    ap.add_argument("--engine", default="faster-whisper", choices=["faster-whisper", "ffmpeg"], help="transcription engine")
    ap.add_argument("--fps", type=float, default=None, help="force the keyframe sampling rate")
    ap.add_argument("--skip", default="", help="comma list of steps to skip (probe,cuts,keyframes,audio,transcribe,ocr,visual_stats)")
    ap.add_argument("--redo", action="store_true", help="re-run steps even when their output exists")
    ap.add_argument("--cookies-from-browser", default=None, help="passed to intake.py for links that need a login")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()

    run_dir = None
    intake_result = None
    if a.run_dir:
        run_dir = common.resolve_run_dir(a.run_dir)
    elif a.source and looks_like_run_dir(Path(a.source).expanduser().resolve()):
        run_dir = Path(a.source).expanduser().resolve()
    elif a.source:
        cmd = [common.python_exe(), str(TOOLS / "intake.py"), a.source, "--run-root", a.run_root]
        if a.slug:
            cmd += ["--slug", a.slug]
        if a.cookies_from_browser:
            cmd += ["--cookies-from-browser", a.cookies_from_browser]
        if a.quiet:
            cmd.append("--quiet")
        ti = time.time()
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        lines = [ln for ln in (p.stdout or "").splitlines() if ln.strip()]
        if not a.quiet:
            for ln in lines[:-1]:
                print(ln)
        if p.returncode != 0 or not lines:
            print(f"intake failed (rc={p.returncode})", file=sys.stderr)
            if lines:
                print(lines[-1])
            return 2
        run_dir = Path(lines[-1].strip())
        intake_result = {"step": "intake", "script": "intake.py", "rc": 0, "ok": True, "elapsed_s": round(time.time() - ti, 2)}
    else:
        ap.error("give a video path / link / run dir, or --run-dir")

    log = common.measure_log(run_dir, "measure_all", a.quiet)
    log.info(f"run dir: {run_dir}")
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    if a.skip_transcribe:
        skip.add("transcribe")
    prev_timings = ((common.state_get(run_dir).get("measure") or {}).get("timings") or {})
    results = [intake_result] if intake_result else []
    if not intake_result and "intake" in prev_timings:
        results.append({"step": "intake", "script": "intake.py", "rc": 0, "ok": True, "elapsed_s": prev_timings["intake"],
                        "skipped": True, "note": "earlier run"})
    for name, script, marker in STEPS:
        if name in skip:
            log.info(f"=== {name}: skipped (--skip)")
            results.append({"step": name, "script": script, "rc": 0, "ok": True, "elapsed_s": 0.0, "skipped": True, "note": "--skip"})
            continue
        if not a.redo and (run_dir / marker).exists():
            log.info(f"=== {name}: output exists ({marker}); skipped (use --redo to re-run)")
            results.append({"step": name, "script": script, "rc": 0, "ok": True, "elapsed_s": prev_timings.get(name, 0.0),
                            "skipped": True, "note": "output existed (timing from the earlier run)"})
            continue
        args = ["--run-dir", str(run_dir)]
        if name == "keyframes" and a.fps:
            args += ["--fps", str(a.fps)]
        if name == "transcribe":
            args += ["--model", a.whisper_model, "--language", a.language, "--engine", a.engine]
        results.append(run_step(name, script, args, log, a.quiet))
        if name == "transcribe" and results[-1]["ok"] and (run_dir / "10-measure" / "audio-features.json").exists():
            run_step("audio-refine", "audio.py", ["--run-dir", str(run_dir), "--refine-only"], log, a.quiet)

    total = round(time.time() - t0, 2)
    summary = build_summary(run_dir, results, total)
    sp = run_dir / "10-measure" / "measure-summary.md"
    common.write_text(sp, summary)
    m = run_dir / "10-measure"
    common.state_add_files(run_dir, "10-measure", [p for p in m.iterdir() if p.is_file() and p.suffix in (".json", ".srt", ".txt", ".md", ".wav")])
    fails = [r["step"] for r in results if not r["ok"]]
    common.state_set(run_dir, stage="measured", next_step="analysis",
                     measure={"timings": {r["step"]: r["elapsed_s"] for r in results}, "failed": fails, "total_s": total,
                              "summary": common.rel(run_dir, sp), "updated": common.now_iso()})
    log.info(f"measure-summary.md written; failed steps: {fails or 'none'}; total {total}s")
    print(str(run_dir))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
