"""audio.py - Stage 1: audio extraction + audio features -> 10-measure\\audio.wav, audio-16k.wav, audio-features.json

Usage: python audio.py --run-dir <run> [--silence-db -35] [--silence-min 0.6] [--no-librosa] [--refine-only] [--quiet]

  audio.wav       44.1 kHz stereo PCM (analysis / editing reference)
  audio-16k.wav   16 kHz mono PCM (ASR input for transcribe.py)
  audio-features.json:
    tempo_bpm + beat_times (librosa beat_track), onset_times, rms_per_0.25s [{t, rms, db}], spectral_centroid (mean + per second),
    silence_spans (ffmpeg silencedetect, default -35 dB / 0.6 s = dead air), loudness (ffmpeg ebur128: integrated LUFS, LRA, true peak,
    momentary per second), segmentation [{start, end, label speech|music-or-ambience|silence, confidence}] from a simple
    energy-modulation heuristic (the transcript is authoritative for speech: --refine-only re-labels with transcript.json),
    cuts_vs_beats (how many hard cuts land within 80 ms of a beat, when shots.json exists).
No audio stream -> audio-features.json {has_audio:false} and exit 0. Exit 1 on failure.
librosa's first call after a cold numba cache can take ~40 s; --no-librosa uses the numpy fallback (RMS, onsets, autocorrelation tempo).
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


# ----------------------------------------------------------------------------- ffmpeg measurements
def extract_wavs(src: Path, mdir: Path, work: Path, log) -> dict:
    ff = common.ffmpeg()
    outs = {}
    for key, ac, ar, dest in (("audio_wav", 2, 44100, mdir / "audio.wav"),
                              ("audio_16k", 1, 16000, mdir / "audio-16k.wav"),
                              ("audio_22k", 1, 22050, work / "audio-22k.wav")):
        res = common.run_cmd([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-ac", str(ac),
                              "-ar", str(ar), "-c:a", "pcm_s16le", str(dest)], log=log, timeout=1800)
        if not res.ok or not dest.exists():
            raise RuntimeError(f"wav extraction failed ({dest.name}) rc={res.returncode}: {res.tail(8)}")
        outs[key] = dest
    return outs


def silencedetect(src: Path, db: float, min_s: float, duration: float, log) -> list[dict]:
    res = common.run_cmd([common.ffmpeg(), "-hide_banner", "-nostats", "-loglevel", "info", "-i", str(src),
                          "-af", f"silencedetect=n={db}dB:d={min_s}", "-vn", "-f", "null", "-"], log=log, timeout=1800)
    spans, start = [], None
    for line in res.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*(-?[\d.]+)\s*\|\s*silence_duration:\s*(-?[\d.]+)", line)
        if m and start is not None:
            spans.append({"start": round(start, 3), "end": round(float(m.group(1)), 3),
                          "duration": round(float(m.group(2)), 3)})
            start = None
    if start is not None:
        spans.append({"start": round(start, 3), "end": round(duration, 3), "duration": round(duration - start, 3),
                      "note": "silence runs to the end"})
    return spans


def ebur128(src: Path, log) -> dict:
    res = common.run_cmd([common.ffmpeg(), "-hide_banner", "-nostats", "-loglevel", "info", "-i", str(src),
                          "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], log=log, timeout=1800)
    txt = res.stderr
    out = {"integrated_lufs": None, "lra_lu": None, "true_peak_dbtp": None, "momentary_per_s": []}
    # momentary loudness timeline: "t:   0.4  TARGET:-23 LUFS    M: -30.1 S: -33.2  I: -32.0 LUFS ..."
    last_sec = -1
    for line in txt.splitlines():
        m = re.search(r"\bt:\s*([\d.]+)\s+TARGET:.*?\bM:\s*(-?[\d.]+)", line)
        if m:
            t = float(m.group(1))
            sec = int(t)
            if sec != last_sec:
                mval = float(m.group(2))
                out["momentary_per_s"].append({"t": sec, "lufs": None if mval < -100 else round(mval, 1)})
                last_sec = sec
    if "Summary:" in txt:
        summ = txt[txt.rfind("Summary:"):]
        m = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ)
        if m:
            out["integrated_lufs"] = float(m.group(1))
        m = re.search(r"LRA:\s+(-?[\d.]+)\s+LU", summ)
        if m:
            out["lra_lu"] = float(m.group(1))
        m = re.search(r"True peak:\s*(?:\n|\r\n)?\s*Peak:\s+(-?[\d.]+)\s+dBFS", summ)
        if m:
            out["true_peak_dbtp"] = float(m.group(1))
    out["method"] = "ffmpeg ebur128=peak=true (EBU R128); delivery target for TikTok/IG QA: -14 LUFS, TP -1.5 dBTP"
    return out


# ----------------------------------------------------------------------------- frame features
def features_librosa(wav22: Path):
    import numpy as np
    import librosa
    y, sr = librosa.load(str(wav22), sr=None, mono=True)
    hop, fl = 512, 2048
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop, units="time")
    tempo = float(np.atleast_1d(tempo)[0]) if tempo is not None else None
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, onset_envelope=oenv, hop_length=hop, units="time")
    rms = librosa.feature.rms(y=y, frame_length=fl, hop_length=hop)[0]
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=fl, hop_length=hop)[0]
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=fl, hop_length=hop)[0]
    flat = librosa.feature.spectral_flatness(y=y, n_fft=fl, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    return {"sr": sr, "duration": len(y) / sr, "tempo": tempo, "beats": [float(b) for b in beats],
            "onsets": [float(o) for o in onsets], "rms": rms, "cent": cent, "zcr": zcr, "flat": flat,
            "times": times, "method": "librosa 1.0 (beat_track, onset_detect, rms, spectral_centroid, zcr, flatness)"}


def features_numpy(wav22: Path):
    """librosa-free fallback (soundfile + numpy + scipy): RMS, spectral-flux onsets, autocorrelation tempo, centroid, zcr, flatness."""
    import numpy as np
    import soundfile as sf
    try:
        from scipy.signal import find_peaks
    except Exception:  # scipy binaries blocked by Windows Smart App Control (2026-09-19) -> numpy peak picker
        def find_peaks(x, height=None, distance=1):
            x = np.asarray(x, dtype=float)
            cand = np.where((x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:]))[0] + 1
            if height is not None:
                cand = cand[x[cand] >= height]
            keep = []
            for i in cand[np.argsort(-x[cand])]:
                if all(abs(i - k) >= max(1, int(distance)) for k in keep):
                    keep.append(int(i))
            return np.array(sorted(keep), dtype=int), {}
    y, sr = sf.read(str(wav22), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    win, hop = 2048, 512
    n = max(0, (len(y) - win) // hop + 1)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = y[idx] * np.hanning(win)[None, :]
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    times = hop * np.arange(n) / sr
    S = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(win, 1 / sr)
    cent = np.sum(S * freqs[None, :], axis=1) / (np.sum(S, axis=1) + 1e-9)
    logS = np.log1p(S)
    flux = np.concatenate([[0.0], np.sum(np.maximum(0.0, np.diff(logS, axis=0)), axis=1)])
    flux_n = (flux - flux.mean()) / (flux.std() + 1e-9)
    peaks, _ = find_peaks(flux_n, height=1.0, distance=int(0.1 * sr / hop))
    onsets = [float(times[p]) for p in peaks]
    fr = sr / hop
    ac = np.correlate(flux_n, flux_n, mode="full")[len(flux_n) - 1:]
    lag_min, lag_max = int(fr * 60 / 200), int(fr * 60 / 30)
    tempo, beats = None, []
    if lag_max < len(ac):
        lag = lag_min + int(np.argmax(ac[lag_min:lag_max]))
        if lag:
            tempo = 60.0 * fr / lag
            period = 60.0 / tempo
            # beat grid anchored on the strongest onset
            anchor = onsets[int(np.argmax(flux_n[peaks]))] if len(peaks) else 0.0
            t = anchor - period * math.floor(anchor / period)
            while t < len(y) / sr:
                beats.append(float(t))
                t += period
    zcr = np.mean(np.abs(np.diff(np.sign(frames), axis=1)) > 0, axis=1)
    gm = np.exp(np.mean(np.log(S + 1e-9), axis=1))
    am = np.mean(S, axis=1) + 1e-9
    flat = gm / am
    return {"sr": sr, "duration": len(y) / sr, "tempo": tempo, "beats": beats, "onsets": onsets, "rms": rms,
            "cent": cent, "zcr": zcr, "flat": flat, "times": times,
            "method": "numpy fallback (spectral-flux onsets, autocorrelation tempo, beat grid anchored on the strongest onset)"}


def db(x: float) -> float:
    return round(20.0 * math.log10(max(float(x), 1e-9)), 1)


def bin_mean(values, times, step: float, duration: float):
    import numpy as np
    out = []
    n = int(math.ceil(duration / step))
    for i in range(n):
        m = (times >= i * step) & (times < (i + 1) * step)
        out.append(float(np.mean(values[m])) if np.any(m) else 0.0)
    return out


def segment(feat: dict, silence_spans: list[dict], duration: float, floor_db: float = -50.0, win: float = 0.5) -> list[dict]:
    """Simple heuristic: silence by energy / silencedetect; speech vs music by RMS modulation depth + zero-crossing rate."""
    import numpy as np
    times, rms, zcr = feat["times"], feat["rms"], feat["zcr"]
    n = int(math.ceil(duration / win))
    labels = []
    for i in range(n):
        ws, we = i * win, min(duration, (i + 1) * win)
        m = (times >= ws) & (times < we)
        ctx = (times >= ws - 0.5) & (times < we + 0.5)
        if not np.any(m):
            labels.append(("silence", 1.0, {}))
            continue
        level = db(np.mean(rms[m]))
        mid = (ws + we) / 2
        in_sd = any(s["start"] <= mid < s["end"] for s in silence_spans)
        if level < floor_db or in_sd:
            labels.append(("silence", 1.0, {"db": level}))
            continue
        r = rms[ctx]
        cv = float(np.std(r) / (np.mean(r) + 1e-9))
        z = float(np.mean(zcr[ctx]))
        cv_term = min(1.0, max(0.0, (cv - 0.35) / 0.45))
        z_term = min(1.0, max(0.0, (z - 0.03) / 0.12))
        score = 0.65 * cv_term + 0.35 * z_term
        lab = "speech" if score >= 0.5 else "music-or-ambience"
        labels.append((lab, round(abs(score - 0.5) * 2, 2), {"db": level, "cv": round(cv, 3), "zcr": round(z, 4)}))
    # 3-window median smoothing on the label
    sm = []
    for i in range(n):
        trio = [labels[j][0] for j in (i - 1, i, i + 1) if 0 <= j < n]
        lab = max(set(trio), key=trio.count) if trio.count(labels[i][0]) < 2 and len(trio) == 3 else labels[i][0]
        sm.append((lab, labels[i][1]))
    spans = []
    for i, (lab, conf) in enumerate(sm):
        ws, we = round(i * win, 3), round(min(duration, (i + 1) * win), 3)
        if spans and spans[-1]["label"] == lab:
            spans[-1]["end"] = we
            spans[-1]["_c"].append(conf)
        else:
            spans.append({"start": ws, "end": we, "label": lab, "_c": [conf]})
    for s in spans:
        s["duration"] = round(s["end"] - s["start"], 3)
        s["confidence"] = round(sum(s["_c"]) / len(s["_c"]), 2)
        del s["_c"]
    return spans


def refine_with_transcript(segmentation: list[dict], transcript: dict, duration: float) -> list[dict]:
    """Speech = transcript segments (authoritative); everything else keeps silence / music-or-ambience."""
    segs = [(float(s["start"]) - 0.1, float(s["end"]) + 0.1) for s in transcript.get("segments", [])]
    if not segs:
        out = []
        for s in segmentation:
            s = dict(s)
            if s["label"] == "speech":
                s["label"] = "music-or-ambience"
                s["note"] = "heuristic said speech but the transcript found none"
            out.append(s)
        return out
    step = 0.25
    n = int(math.ceil(duration / step))
    labels = []
    for i in range(n):
        mid = (i + 0.5) * step
        base = next((s["label"] for s in segmentation if s["start"] <= mid < s["end"]), "silence")
        if any(a <= mid < b for a, b in segs):
            labels.append("speech")
        elif base == "speech":
            labels.append("music-or-ambience")
        else:
            labels.append(base)
    spans = []
    for i, lab in enumerate(labels):
        ws, we = round(i * step, 3), round(min(duration, (i + 1) * step), 3)
        if spans and spans[-1]["label"] == lab:
            spans[-1]["end"] = we
        else:
            spans.append({"start": ws, "end": we, "label": lab})
    for s in spans:
        s["duration"] = round(s["end"] - s["start"], 3)
        s["confidence"] = 0.95 if s["label"] == "speech" else 0.6
    return spans


def summarise(spans: list[dict]) -> dict:
    tot = {"speech_s": 0.0, "music_or_ambience_s": 0.0, "silence_s": 0.0}
    for s in spans:
        key = {"speech": "speech_s", "music-or-ambience": "music_or_ambience_s", "silence": "silence_s"}[s["label"]]
        tot[key] += s["duration"]
    return {k: round(v, 2) for k, v in tot.items()}


# ----------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="audio extraction + features")
    common.add_std_args(ap)
    ap.add_argument("--silence-db", type=float, default=-35.0, help="silencedetect noise threshold in dB (default -35)")
    ap.add_argument("--silence-min", type=float, default=0.6, help="silencedetect minimum duration in s (default 0.6)")
    ap.add_argument("--no-librosa", action="store_true", help="use the numpy fallback instead of librosa")
    ap.add_argument("--refine-only", action="store_true",
                    help="only re-label the segmentation in audio-features.json with transcript.json (no extraction)")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "audio", a.quiet)
    mdir = common.measure_dir(run_dir)
    out_path = mdir / "audio-features.json"
    try:
        if a.refine_only:
            feats = common.read_json(out_path)
            tr = common.read_json(mdir / "transcript.json")
            if not feats or not feats.get("has_audio"):
                log.info("refine-only: no audio features to refine")
                return 0
            if not tr:
                log.info("refine-only: transcript.json missing, segmentation left as heuristic")
                return 0
            feats["segmentation"] = refine_with_transcript(feats["segmentation"], tr, float(feats["duration_s"]))
            feats["segmentation_method"] = "speech from transcript.json (faster-whisper VAD segments); other labels heuristic"
            feats["segmentation_summary"] = summarise(feats["segmentation"])
            feats["refined_at"] = common.now_iso()
            common.write_json(out_path, feats)
            log.info(f"segmentation refined with transcript: {feats['segmentation_summary']}")
            return 0

        src = common.source_mp4(run_dir)
        probe = common.read_json(mdir / "probe.json")
        if probe is None:
            pj = common.ffprobe_json(src, log=log)
            has_audio = bool(common.audio_streams(pj))
            duration = common.media_duration(pj)
        else:
            has_audio = bool(probe.get("has_audio"))
            duration = float(probe["duration_s"])
        if not has_audio:
            common.write_json(out_path, {"has_audio": False, "source": common.rel(run_dir, src),
                                         "note": "no audio stream in the source; nothing extracted", "timing_s": 0.0})
            common.state_add_file(run_dir, "10-measure", out_path)
            log.info("no audio stream -> audio-features.json {has_audio:false}")
            return 0

        work = common.ensure_dir(mdir / "_work")
        t1 = time.time()
        wavs = extract_wavs(src, mdir, work, log)
        log.info(f"wav extraction done in {time.time() - t1:.1f}s")
        t1 = time.time()
        sil = silencedetect(wavs["audio_wav"], a.silence_db, a.silence_min, duration, log)
        loud = ebur128(wavs["audio_wav"], log)
        log.info(f"silencedetect: {len(sil)} spans >= {a.silence_min}s below {a.silence_db} dB; "
                 f"loudness I={loud['integrated_lufs']} LUFS LRA={loud['lra_lu']} TP={loud['true_peak_dbtp']} dBTP ({time.time() - t1:.1f}s)")

        t1 = time.time()
        feat = None
        if not a.no_librosa:
            try:
                feat = features_librosa(wavs["audio_22k"])
            except Exception as e:  # pragma: no cover
                log.warn(f"librosa failed ({e}); using the numpy fallback")
        if feat is None:
            feat = features_numpy(wavs["audio_22k"])
        log.info(f"features ({feat['method'].split(' ')[0]}): tempo {feat['tempo'] and round(feat['tempo'], 1)} BPM, "
                 f"{len(feat['beats'])} beats, {len(feat['onsets'])} onsets in {time.time() - t1:.1f}s")

        import numpy as np
        rms_q = bin_mean(feat["rms"], feat["times"], 0.25, duration)
        rms_list = [{"t": round(i * 0.25, 2), "rms": round(v, 5), "db": db(v)} for i, v in enumerate(rms_q)]
        cent_s = bin_mean(feat["cent"], feat["times"], 1.0, duration)
        segmentation = segment(feat, sil, duration)
        tr = common.read_json(mdir / "transcript.json")
        seg_method = "heuristic: silence by energy (< -50 dBFS) or silencedetect; speech vs music by RMS modulation depth + ZCR"
        if tr:
            segmentation = refine_with_transcript(segmentation, tr, duration)
            seg_method = "speech from transcript.json (faster-whisper VAD segments); other labels heuristic"

        cuts_vs_beats = None
        shots = common.read_json(mdir / "shots.json")
        if shots and feat["beats"]:
            beats = np.array(feat["beats"])
            cut_ts = [s["start"] for s in shots.get("shots", [])[1:]]
            rows = []
            for t in cut_ts:
                d = float(np.min(np.abs(beats - t)))
                rows.append({"cut_t": t, "nearest_beat_gap_s": round(d, 3), "on_beat": d <= 0.08})
            cuts_vs_beats = {"window_s": 0.08, "n_cuts": len(rows), "n_on_beat": sum(1 for r in rows if r["on_beat"]),
                             "ratio": round(sum(1 for r in rows if r["on_beat"]) / len(rows), 2) if rows else None,
                             "cuts": rows}

        peak_rms = max((r["rms"] for r in rms_list), default=0.0)
        out = {
            "has_audio": True, "source": common.rel(run_dir, src), "duration_s": round(duration, 3),
            "files": {"audio_wav": common.rel(run_dir, wavs["audio_wav"]), "audio_16k": common.rel(run_dir, wavs["audio_16k"])},
            "analysis_sr": feat["sr"], "feature_method": feat["method"],
            "tempo_bpm": round(feat["tempo"], 2) if feat["tempo"] else None,
            "n_beats": len(feat["beats"]), "beat_times": [round(b, 3) for b in feat["beats"]],
            "n_onsets": len(feat["onsets"]), "onset_times": [round(o, 3) for o in feat["onsets"]],
            "rms_per_0.25s": rms_list, "rms_peak": round(peak_rms, 5), "rms_peak_db": db(peak_rms),
            "spectral_centroid_mean_hz": round(float(np.mean(feat["cent"])), 1) if len(feat["cent"]) else None,
            "spectral_centroid_per_s_hz": [round(c, 1) for c in cent_s],
            "silence_spans": sil, "dead_air_spans": sil, "silence_params": {"noise_db": a.silence_db, "min_s": a.silence_min},
            "dead_air_total_s": round(sum(s["duration"] for s in sil), 2),
            "loudness": loud,
            "segmentation": segmentation, "segmentation_method": seg_method,
            "segmentation_summary": summarise(segmentation),
            "cuts_vs_beats": cuts_vs_beats,
            "timing_s": round(time.time() - t0, 2),
        }
        common.write_json(out_path, out)
        common.state_add_files(run_dir, "10-measure", [out_path, wavs["audio_wav"], wavs["audio_16k"]])
        log.info(f"audio-features.json written: {out['segmentation_summary']}, dead air {out['dead_air_total_s']}s, "
                 f"done in {out['timing_s']}s")
        return 0
    except Exception as e:
        import traceback
        log.error(f"audio failed: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
