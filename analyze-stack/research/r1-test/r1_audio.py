import sys, json, subprocess, os, time
import r1_dllshim  # process-local msvcp140.dll workaround (soxr needs it); remove once VC++ redist is installed
import numpy as np, librosa
src, outdir = sys.argv[1], sys.argv[2]
wav = os.path.join(outdir, "audio22k.wav")
ff = os.environ.get("FFMPEG_EXE", r"C:\Users\Glaresquare1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")
subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", wav], check=True)
t0 = time.time()
y, sr = librosa.load(wav, sr=22050, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time", onset_envelope=onset_env)
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
rms_db = librosa.amplitude_to_db(rms, ref=np.max)
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
cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
res = {"duration": round(dur, 3), "sr": sr, "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 2),
       "n_beats": int(len(beats)), "beats": [round(float(b), 3) for b in beats],
       "n_onsets": int(len(onsets)), "onsets": [round(float(o), 3) for o in onsets],
       "silences_ge_0.5s_below_-40dBrel": sil, "rms_per_second": energy,
       "spectral_centroid_mean_hz": round(float(np.mean(cent)), 1), "elapsed_s": round(time.time() - t0, 2)}
json.dump(res, open(os.path.join(outdir, "audio-features.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("beats", "onsets", "rms_per_second")}, indent=1))
print("first beats", res["beats"][:12]); print("first onsets", res["onsets"][:12])
print("rms/sec", res["rms_per_second"])
