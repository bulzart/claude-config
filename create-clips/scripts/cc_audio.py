"""Audio of a chunk: 16 kHz extraction, loudness per window, the profile, and the Whisper transcript.

Gather-only: every number here is a measurement; nothing labels a moment as good or bad.
Whisper follows analyze-with-loupe's transcribe() (faster-whisper, local_files_only, word timestamps, VAD) with the settings of
config.json -> whisper. The model is loaded once per process (watch keeps it between chunks).
"""
from __future__ import annotations

import math
import os
import threading
import time
import wave
from pathlib import Path

import numpy as np

from cc_common import cfg_get, find_tool, load_config, read_json, run_cmd

DB_FLOOR = -90.0


# --------------------------------------------------------------------------- loudness

def extract_wav(chunk_mp4, wav_path, timeout: float = 900) -> dict:
    """The chunk's audio as 16 kHz mono 16-bit PCM. {ok, error}."""
    Path(wav_path).parent.mkdir(parents=True, exist_ok=True)
    cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", chunk_mp4, "-vn", "-sn", "-dn",
                  "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav_path], timeout=timeout)
    p = Path(wav_path)
    ok = cp.returncode == 0 and p.is_file() and p.stat().st_size > 44
    return {"ok": ok, "error": None if ok else (cp.stderr or "no audio decoded")[-300:].strip()}


def read_wav(path) -> tuple:
    """(float32 samples in -1..1, sample rate) of a 16-bit mono PCM wav."""
    with wave.open(str(path), "rb") as w:
        rate, n, ch, width = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError(f"expected 16-bit PCM, got {width * 8}-bit")
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a, rate


def _db(x) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return np.maximum(20.0 * np.log10(np.maximum(x, 1e-12)), DB_FLOOR)


def window_levels(samples: np.ndarray, rate: int, window_s: float = 0.5) -> tuple:
    """RMS and peak in dBFS per window ([rms...], [peak...]); the last window may be shorter; floor -90."""
    win = max(1, int(round(rate * window_s)))
    n = len(samples)
    if n == 0:
        return [], []
    full = n // win
    rms, peak = [], []
    if full:
        blk = samples[:full * win].reshape(full, win)
        rms.extend(np.sqrt((blk.astype(np.float64) ** 2).mean(axis=1)))
        peak.extend(np.abs(blk).max(axis=1))
    if n > full * win:
        tail = samples[full * win:].astype(np.float64)
        rms.append(float(np.sqrt((tail ** 2).mean())))
        peak.append(float(np.abs(tail).max()))
    return [round(float(v), 1) for v in _db(rms)], [round(float(v), 1) for v in _db(peak)]


def audio_json(rec_start_s: float, window_s: float, rms_db: list, peak_db: list, no_audio: bool = False) -> dict:
    clip = sum(1 for p in peak_db if p >= -0.5) * window_s
    return {"window_s": window_s, "rec_start_s": round(rec_start_s, 3), "rms_db": rms_db, "peak_db": peak_db,
            "clip_seconds": round(clip, 2), "no_audio": no_audio}


def audio_profile(rms_db: list, peak_db: list, window_s: float, rec_start_s: float) -> dict:
    """Summary numbers plus the loud-jump events: a window whose RMS is at least `loud_jump_db` above the median of the previous
    5 s (10 windows), taken only above `loud_jump_floor_db` so the step from digital silence to a quiet room is not one. Consecutive
    windows are one event, reported at the window with the largest jump."""
    thr = float(cfg_get("audio.loud_jump_db", 10))
    floor = float(cfg_get("audio.loud_jump_floor_db", -45))
    sil = float(cfg_get("audio.silence_db", -50))
    n = len(rms_db)
    if not n:
        return {"window_s": window_s, "windows": 0, "rms_mean_db": None, "rms_median_db": None, "rms_p90_db": None, "rms_max_db": None,
                "peak_max_db": None, "silence_share": None, "silence_db": sil, "loud_jump_db": thr, "loud_jump_floor_db": floor, "loud_jumps": []}
    a = np.asarray(rms_db, dtype=np.float64)
    prev_n = max(2, int(round(5.0 / window_s)))
    events, run = [], None
    for k in range(3, n):
        base = float(np.median(a[max(0, k - prev_n):k]))
        jump = float(a[k] - base)
        if jump >= thr and a[k] >= floor:
            if run is None:
                run = {"k": k, "jump": jump, "len": 1}
            else:
                run["len"] += 1
                if jump > run["jump"]:
                    run["k"], run["jump"] = k, jump
        elif run is not None:
            events.append(run)
            run = None
    if run is not None:
        events.append(run)
    jumps = [{"t": round(e["k"] * window_s, 2), "rec": round(rec_start_s + e["k"] * window_s, 2), "db": float(a[e["k"]]),
              "jump_db": round(e["jump"], 1), "run_s": round(e["len"] * window_s, 2)} for e in events]
    return {"window_s": window_s, "windows": n, "rms_mean_db": round(float(a.mean()), 1), "rms_median_db": round(float(np.median(a)), 1),
            "rms_p90_db": round(float(np.percentile(a, 90)), 1), "rms_max_db": round(float(a.max()), 1),
            "peak_max_db": round(float(max(peak_db)), 1) if peak_db else None,
            "silence_share": round(float((a < sil).mean()), 3), "silence_db": sil, "loud_jump_db": thr, "loud_jump_floor_db": floor,
            "loud_jumps": jumps}


# --------------------------------------------------------------------------- Whisper

_WORKERS = 1                    # how many chunks the watcher transcribes at the same time (cc_proc.cmd_watch sets it): faster-whisper's num_workers
_LOCK = threading.Lock()


def configure_workers(n: int) -> None:
    """The watcher runs `n` processors, each on its own chunk: the model must allow `n` transcriptions at once (num_workers), or a second one would wait for the first."""
    global _WORKERS
    _WORKERS = max(1, int(n))


class Transcriber:
    """faster-whisper behind one object. Loads on first use (once, whichever thread asks first), keeps the model, records what it really used.
    One model serves several threads: faster-whisper's num_workers (= the watcher's processors) lets their transcribe() calls run in parallel."""

    def __init__(self, wcfg: dict | None = None):
        base = dict(load_config().get("whisper") or {})
        base.update({k: v for k, v in (wcfg or {}).items() if v is not None})
        env_model = os.environ.get("CC_WHISPER_MODEL")
        if env_model:                       # tests and quick looks: the same code with another model
            base["model"] = env_model
        env_dev = os.environ.get("CC_WHISPER_DEVICE")
        if env_dev:
            base["device"] = env_dev
        self.cfg = base
        self.model = None
        self.used = {}
        self.load_seconds = None
        self._lock = threading.Lock()
        self._gate = None                   # at most `parallel` transcriptions at once: a further processor waits its turn (the cores are shared)

    # the device and compute type to try, in order
    def _attempts(self) -> list:
        dev = str(self.cfg.get("device") or "cpu").lower()
        ct = str(self.cfg.get("compute_type") or "int8")
        cuda_ct = str(self.cfg.get("cuda_compute_type") or "float16")
        if dev == "cuda":
            return [("cuda", cuda_ct), ("cpu", ct)]
        if dev == "auto":
            return [("cuda", cuda_ct), ("cpu", ct)]
        return [("cpu", ct)]

    def _prepare_cuda(self) -> None:
        d = self.cfg.get("cuda_dll_dir")
        if d and Path(d).is_dir():
            try:
                os.add_dll_directory(str(d))
            except (OSError, AttributeError):
                pass
            os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")

    def load(self) -> None:
        if self.model is not None:
            return
        with self._lock:                    # two processors asking at once: one loads, the other waits and uses the same model
            if self.model is not None:
                return
            self._load()

    def _load(self) -> None:
        t0 = time.time()
        attempts = self._attempts()
        if any(d == "cuda" for d, _ in attempts):
            self._prepare_cuda()
        from faster_whisper import WhisperModel  # type: ignore
        asked = str(self.cfg.get("model") or "medium")
        names = [asked]                     # ALWAYS the model asked for (medium), never a smaller one: no silent downgrade (the user, 2026-11-14)
        last_err = None
        threads = int(self.cfg.get("cpu_threads") or 0)
        workers = max(1, int(self.cfg.get("parallel") or _WORKERS))       # transcriptions that may run at the same time (default: as many as the watcher has processors)
        for dev, ct in attempts:
            for name in names:
                try:
                    kw = {"device": dev, "compute_type": ct, "local_files_only": bool(self.cfg.get("local_files_only", True)), "num_workers": workers}
                    if dev == "cpu" and threads:
                        kw["cpu_threads"] = threads
                    self.model = WhisperModel(name, **kw)
                    self._gate = threading.BoundedSemaphore(workers)
                    self.used = {"model": name, "device": dev, "compute_type": ct}
                    if workers > 1:
                        self.used["num_workers"] = workers
                    if name != asked:
                        self.used["model_fallback"] = {"asked": asked, "used": name}
                    if (dev, ct) != attempts[0]:
                        self.used["device_fallback"] = {"asked": attempts[0][0], "used": dev, "why": str(last_err)[:200] if last_err else None}
                    self.load_seconds = round(time.time() - t0, 1)
                    return
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    continue
        raise RuntimeError(f"the faster-whisper model {asked!r} could not be loaded ({str(last_err)[:300]}); there is no fallback to a smaller model: fix the cache or the memory and run the chunk again")

    def transcribe(self, wav_path, rec_start_s: float, duration_s: float | None, language: str | None = None) -> dict:
        self.load()
        model, gate = self.model, self._gate     # local names: an idle unload by the watcher cannot pull them away mid-call
        if model is None or gate is None:
            self.load()
            model, gate = self.model, self._gate
        # `language` = the run's locked language for this chunk (cc_proc.stream_language), else the config's; "auto" = Whisper names the language of this chunk itself
        lang = str(language or self.cfg.get("language") or "auto")
        auto = lang.lower() == "auto"
        prompt = str(self.cfg.get("initial_prompt") or "").strip() or None
        t_wait = time.time()
        with gate:                          # the generator is consumed inside the gate: the decoding happens here, not in model.transcribe()
            t0 = time.time()
            waited = t0 - t_wait
            tkw = dict(word_timestamps=True, vad_filter=bool(self.cfg.get("vad_filter", True)), beam_size=int(self.cfg.get("beam_size", 5)),
                       condition_on_previous_text=bool(self.cfg.get("condition_on_previous_text", False)), initial_prompt=prompt)
            segs, info = model.transcribe(str(wav_path), language=None if auto else lang, **tkw)
            source, detected = ("detected" if auto else "forced"), None
            if auto:
                # Whisper has named the language before it decodes anything (`info` is ready, the segments are not). A guess it is not sure of (music, one short word, noise) is not
                # trusted: the configured fallback language decodes the chunk instead, and the guess is kept as a fact (detected_language, detected_probability).
                detected = (str(info.language), round(float(info.language_probability), 3))
                fb = str(self.cfg.get("fallback_language") or "").strip()
                if detected[1] < float(self.cfg.get("detect_min_probability", 0.85)) and fb and fb.lower() != "auto":
                    segs, info = model.transcribe(str(wav_path), language=fb, **tkw)
                    source = "fallback"
            out_segs = []
            for s in segs:
                out_segs.append({
                    "start": round(float(s.start), 2), "end": round(float(s.end), 2), "text": str(s.text).strip(),
                    "avg_logprob": round(float(s.avg_logprob), 3), "no_speech_prob": round(float(s.no_speech_prob), 3),
                    "compression_ratio": round(float(s.compression_ratio), 2),
                    "words": [{"w": str(w.word).strip(), "s": round(float(w.start), 2), "e": round(float(w.end), 2),
                               "p": round(float(w.probability), 2)} for w in (s.words or []) if str(w.word).strip()]})
        n_words = sum(len(s["words"]) for s in out_segs)
        speech = sum(max(0.0, s["end"] - s["start"]) for s in out_segs)
        res = {"engine": "faster-whisper", **self.used, "language": info.language,
               "language_probability": round(float(info.language_probability), 3), "language_source": source, "vad_filter": bool(self.cfg.get("vad_filter", True)),
               "initial_prompt": prompt, "rec_start_s": round(rec_start_s, 3),
               "duration_s": round(float(duration_s), 3) if duration_s else None, "segments": out_segs, "n_words": n_words,
               "speech_seconds": round(speech, 2), "wpm_speech_only": round(n_words / (speech / 60), 1) if speech > 1 else None,
               "transcribe_seconds": round(time.time() - t0, 1), "model_load_seconds": self.load_seconds}
        if detected:
            res["detected_language"], res["detected_probability"] = detected
        if waited > 0.5:
            res["waited_for_turn_s"] = round(waited, 1)
        return res


_TRANSCRIBERS: dict = {}


def get_transcriber(wcfg: dict | None = None) -> Transcriber:
    """One Transcriber per process and per distinct run override (usually just one), so a long watch loads the model once and every processor shares it."""
    key = repr(sorted((wcfg or {}).items()))
    with _LOCK:
        t = _TRANSCRIBERS.get(key)
        if t is None:
            t = _TRANSCRIBERS[key] = Transcriber(wcfg)
            t._key = key
        return t


def unload_transcriber() -> bool:
    """Free the Whisper model's memory (a watcher that has been idle for a while drops it; the next chunk loads it again). True when a model was loaded.
    The watcher calls it only while no processor is working."""
    freed = False
    with _LOCK:
        for t in _TRANSCRIBERS.values():
            if t.model is not None:
                t.model = None
                freed = True
    if freed:
        import gc
        gc.collect()
    return freed


def empty_transcript(rec_start_s: float, duration_s: float | None, note: str) -> dict:
    return {"engine": None, "model": None, "device": None, "language": None, "language_probability": None, "rec_start_s": round(rec_start_s, 3),
            "duration_s": duration_s, "segments": [], "n_words": 0, "speech_seconds": 0.0, "wpm_speech_only": None, "note": note}
