"""transcribe.py - Stage 1: speech transcription with word timestamps -> 10-measure\\transcript.json / .srt / .txt

Usage: python transcribe.py --run-dir <run> [--model small] [--language auto] [--engine faster-whisper|ffmpeg]
                            [--beam-size 5] [--no-vad] [--quiet]

Engines:
  faster-whisper (default): CPU int8, VAD filter, word timestamps + probabilities. Models `small`, `small.en`, `base`
                            are cached in the default HF cache (C:\\Users\\Glaresquare1\\.cache\\huggingface\\hub).
  ffmpeg:                   ffmpeg's built-in whisper.cpp filter with the ggml models in C:\\Users\\Glaresquare1\\.cache\\whisper-cpp\\
                            (tiny.en, base.en). Segment timestamps only (no words). Python-free fallback.

transcript.json: {engine, model, language, language_probability, has_speech, segments:[{id,start,end,text,words:[{word,start,end,probability}],
                  avg_logprob, no_speech_prob}], n_segments, n_words, speech_s, wpm_speech_only, wpm_whole_video, ...}
transcript.srt:  SIDECAR for the owner's external caption tool and for analysis ONLY - never rendered into an edit.
transcript.txt:  plain text, one segment per line ("No speech detected." when empty).
No speech: has_speech=false, empty srt, exit 0. ASR failure: transcript.error.txt written, exit 1.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools\ free of __pycache__ (only the run dir and model caches are written)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

GGML = {"tiny": "ggml-tiny.en.bin", "tiny.en": "ggml-tiny.en.bin", "base": "ggml-base.en.bin", "base.en": "ggml-base.en.bin",
        "small": "ggml-small.en.bin", "small.en": "ggml-small.en.bin"}


def write_srt(path: Path, segments: list[dict]) -> None:
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{common.fmt_srt(s['start'])} --> {common.fmt_srt(s['end'])}")
        lines.append(s["text"].strip())
        lines.append("")
    common.write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def run_faster_whisper(audio: Path, model: str, language: str | None, beam: int, vad: bool, log) -> dict:
    from faster_whisper import WhisperModel
    t = time.time()
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    load_s = round(time.time() - t, 2)
    log.info(f"faster-whisper model '{model}' loaded (cpu/int8) in {load_s}s")
    kw = dict(language=language, word_timestamps=True, beam_size=beam, vad_filter=vad)
    if vad:
        kw["vad_parameters"] = {"min_silence_duration_ms": 500}
    segs_iter, info = wm.transcribe(str(audio), **kw)
    segments = []
    for s in segs_iter:
        words = [{"word": w.word.strip(), "start": round(float(w.start), 3), "end": round(float(w.end), 3),
                  "probability": round(float(w.probability), 3)} for w in (s.words or [])]
        segments.append({"id": len(segments) + 1, "start": round(float(s.start), 3), "end": round(float(s.end), 3),
                         "text": s.text.strip(), "words": words,
                         "avg_logprob": round(float(s.avg_logprob), 3) if s.avg_logprob is not None else None,
                         "no_speech_prob": round(float(s.no_speech_prob), 3) if s.no_speech_prob is not None else None})
        if not log.quiet:
            log.info(f"[{common.fmt_mmss(s.start)} - {common.fmt_mmss(s.end)}] {s.text.strip()}")
    return {"engine": "faster-whisper", "model": model, "compute": "cpu/int8", "vad_filter": vad, "beam_size": beam,
            "language": info.language, "language_probability": round(float(info.language_probability), 3),
            "audio_duration_s": round(float(info.duration), 3), "model_load_s": load_s, "segments": segments}


def parse_srt(text: str) -> list[dict]:
    segs = []
    blocks = re.split(r"\r?\n\r?\n", text.strip())
    for b in blocks:
        lines = [ln for ln in b.strip().splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1] if "-->" in lines[1] else lines[0])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        txt = " ".join(lines[2:] if "-->" in lines[1] else lines[1:]).strip()
        segs.append({"id": len(segs) + 1, "start": round(start, 3), "end": round(end, 3), "text": txt, "words": [],
                     "avg_logprob": None, "no_speech_prob": None})
    return segs


def run_ffmpeg_whisper(audio: Path, model: str, language: str | None, mdir: Path, log) -> dict:
    name = GGML.get(model, GGML["base"])
    mpath = common.WHISPER_CPP_DIR / name
    if not mpath.exists():
        alt = common.WHISPER_CPP_DIR / "ggml-base.en.bin"
        log.warn(f"{name} not in {common.WHISPER_CPP_DIR}; using {alt.name}")
        mpath = alt
    if not mpath.exists():
        raise RuntimeError(f"no ggml model in {common.WHISPER_CPP_DIR} (download ggml-base.en.bin from huggingface ggerganov/whisper.cpp)")
    esc = str(mpath).replace("\\", "/").replace(":", "\\:")
    dest = "transcript-ffmpeg.srt"
    (mdir / dest).unlink(missing_ok=True)
    lang = language or "en"
    af = f"whisper=model='{esc}':language={lang}:queue=10:use_gpu=false:format=srt:destination={dest}"
    res = common.run_cmd([common.ffmpeg(), "-hide_banner", "-loglevel", "warning", "-y", "-i", str(audio), "-af", af,
                          "-f", "null", "-"], log=log, cwd=mdir, timeout=3600)
    if not res.ok:
        raise RuntimeError(f"ffmpeg whisper filter failed rc={res.returncode}: {res.tail(10)}")
    txt = (mdir / dest).read_text(encoding="utf-8", errors="replace") if (mdir / dest).exists() else ""
    segments = parse_srt(txt)
    return {"engine": "ffmpeg-whisper", "model": mpath.name, "compute": "cpu", "vad_filter": False, "beam_size": None,
            "language": lang, "language_probability": None, "audio_duration_s": None, "model_load_s": None,
            "segments": segments, "raw_srt": common.rel(mdir.parent, mdir / dest)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="speech transcription with word timestamps")
    common.add_std_args(ap)
    ap.add_argument("--model", default="small", help="faster-whisper model (small | small.en | base | tiny); ffmpeg engine: tiny | base")
    ap.add_argument("--language", default="auto", help="ISO code (en) or auto")
    ap.add_argument("--engine", default="faster-whisper", choices=["faster-whisper", "ffmpeg"])
    ap.add_argument("--beam-size", type=int, default=5)
    ap.add_argument("--no-vad", action="store_true", help="disable the VAD filter (faster-whisper)")
    ap.add_argument("--audio", default=None, help="override the audio file (default 10-measure/audio-16k.wav, else source.mp4)")
    a = ap.parse_args(argv)
    t0 = time.time()
    run_dir = common.resolve_run_dir(a.run_dir)
    log = common.measure_log(run_dir, "transcribe", a.quiet)
    mdir = common.measure_dir(run_dir)
    err_path = mdir / "transcript.error.txt"
    try:
        err_path.unlink(missing_ok=True)
        probe = common.read_json(mdir / "probe.json") or {}
        duration = float(probe.get("duration_s") or 0.0)
        if a.audio:
            audio = Path(a.audio).resolve()
        elif (mdir / "audio-16k.wav").exists():
            audio = mdir / "audio-16k.wav"
        else:
            audio = common.source_mp4(run_dir)
        if probe and probe.get("has_audio") is False:
            res = {"engine": a.engine, "model": a.model, "language": None, "language_probability": None, "segments": []}
            note = "no audio stream in the source"
        else:
            language = None if a.language.lower() in ("auto", "", "none") else a.language
            log.info(f"transcribing {audio.name} with {a.engine} ({a.model}, language={a.language})")
            if a.engine == "ffmpeg":
                res = run_ffmpeg_whisper(audio, a.model, language, mdir, log)
            else:
                res = run_faster_whisper(audio, a.model, language, a.beam_size, not a.no_vad, log)
            note = None
        segments = res["segments"]
        n_words = sum(len(s["words"]) for s in segments) if any(s["words"] for s in segments) else \
            sum(len(s["text"].split()) for s in segments)
        lang_p = res.get("language_probability")
        has_speech = n_words > 0 and not (lang_p is not None and lang_p < 0.5 and n_words < 5)
        speech_s = round(sum(s["end"] - s["start"] for s in segments), 2)
        if not duration:
            duration = float(res.get("audio_duration_s") or 0.0)
        out = {
            **{k: v for k, v in res.items() if k != "segments"},
            "source_audio": common.rel(run_dir, audio), "has_speech": has_speech,
            "language_uncertain": bool(lang_p is not None and lang_p < 0.5),
            "n_segments": len(segments), "n_words": n_words, "speech_s": speech_s,
            "wpm_speech_only": round(n_words / speech_s * 60, 1) if speech_s > 0 else None,
            "wpm_whole_video": round(n_words / duration * 60, 1) if duration > 0 else None,
            "wpm_note": "WPM denominators stated: speech-only = sum of segment durations; whole-video = source duration",
            "segments": segments,
            "sidecar_rule": "transcript.srt is a sidecar for the external caption tool and for analysis only; it is never rendered into an edit",
            "note": note if note else ("no speech detected" if not has_speech else None),
            "timing_s": round(time.time() - t0, 2),
        }
        common.write_json(mdir / "transcript.json", out)
        write_srt(mdir / "transcript.srt", segments if has_speech else [])
        txt = "\n".join(s["text"] for s in segments) if has_speech else "No speech detected."
        common.write_text(mdir / "transcript.txt", txt + "\n")
        common.state_add_files(run_dir, "10-measure", [mdir / "transcript.json", mdir / "transcript.srt", mdir / "transcript.txt"])
        if has_speech:
            log.info(f"{len(segments)} segments, {n_words} words, language {out['language']} (p={lang_p}), "
                     f"{out['wpm_speech_only']} wpm speech-only; done in {out['timing_s']}s")
        else:
            log.info(f"no speech detected (language guess {out['language']} p={lang_p}); empty srt written; done in {out['timing_s']}s")
        return 0
    except Exception as e:
        import traceback
        msg = f"transcription failed ({a.engine} {a.model}): {e}\n{traceback.format_exc()}"
        common.write_text(err_path, msg)
        log.error(msg)
        return 1


if __name__ == "__main__":
    sys.exit(main())
