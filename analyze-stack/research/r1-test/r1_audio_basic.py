"""librosa-free audio features (soundfile + numpy + scipy only): RMS energy, dead air, spectral-flux
onsets and an autocorrelation tempo estimate. Fallback for machines where librosa/soxr cannot load."""
import sys, json, os, subprocess, time
import numpy as np, soundfile as sf
from scipy.signal import find_peaks
src, outdir = sys.argv[1], sys.argv[2]
wav = os.path.join(outdir, "audio22k.wav")
ff = os.environ.get("FFMPEG_EXE", r"C:\Users\Glaresquare1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", wav], check=True)
t0 = time.time()
y, sr = sf.read(wav, dtype="float32")
if y.ndim > 1: y = y.mean(axis=1)
dur = len(y) / sr
win, hop = 2048, 512
n = max(0, (len(y) - win) // hop + 1)
idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
frames = y[idx] * np.hanning(win)[None, :]
rms = np.sqrt(np.mean(frames ** 2, axis=1))
times = hop * np.arange(n) / sr
rms_db = 20 * np.log10(np.maximum(rms, 1e-9) / max(float(rms.max()), 1e-9))
thr = -40.0; sil = []; start = None
for t, d in zip(times, rms_db):
    if d < thr and start is None: start = t
    elif d >= thr and start is not None:
        if t - start >= 0.5: sil.append([round(float(start), 2), round(float(t), 2)])
        start = None
if start is not None and dur - start >= 0.5: sil.append([round(float(start), 2), round(dur, 2)])
energy = []
for s in range(int(np.ceil(dur))):
    m = (times >= s) & (times < s + 1)
    energy.append(round(float(np.mean(rms[m])), 5) if np.any(m) else 0.0)
# spectral flux -> onsets
S = np.abs(np.fft.rfft(frames, axis=1))
S = np.log1p(S)
flux = np.sum(np.maximum(0.0, np.diff(S, axis=0)), axis=1)
flux = np.concatenate([[0.0], flux])
flux_n = (flux - flux.mean()) / (flux.std() + 1e-9)
peaks, _ = find_peaks(flux_n, height=1.0, distance=int(0.1 * sr / hop))
onsets = [round(float(times[p]), 3) for p in peaks]
# tempo by autocorrelation of flux (30-200 BPM)
fr = sr / hop
ac = np.correlate(flux_n, flux_n, mode="full")[len(flux_n) - 1:]
lag_min, lag_max = int(fr * 60 / 200), int(fr * 60 / 30)
lag = lag_min + int(np.argmax(ac[lag_min:lag_max])) if lag_max < len(ac) else 0
bpm = round(60.0 * fr / lag, 1) if lag else None
cent = (np.sum(S * np.fft.rfftfreq(win, 1 / sr)[None, :], axis=1) / (np.sum(S, axis=1) + 1e-9))
res = {"method": "soundfile+numpy fallback (no librosa)", "duration": round(dur, 3), "sr": sr,
       "tempo_bpm_autocorr": bpm, "n_onsets": len(onsets), "onsets": onsets,
       "silences_ge_0.5s_below_-40dBrel": sil, "rms_per_second": energy,
       "spectral_centroid_mean_hz": round(float(np.mean(cent)), 1), "elapsed_s": round(time.time() - t0, 2)}
json.dump(res, open(os.path.join(outdir, "audio-features-basic.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("onsets", "rms_per_second")}, indent=1))
print("first onsets", onsets[:12]); print("rms/sec", energy)
