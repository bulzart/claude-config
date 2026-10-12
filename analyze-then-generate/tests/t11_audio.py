import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *
import importlib.util as _iu

_spec = _iu.spec_from_file_location("atg_inproc", ATG)
atg = _iu.module_from_spec(_spec)
_spec.loader.exec_module(atg)
FF = atg.find_tool("ffmpeg")

ACR = Path(tempfile.mkdtemp(prefix="atg-audioctx-"))
GEN = Path(tempfile.mkdtemp(prefix="atg-audiogen-"))


def sh(*cmd):
    cp = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8")
    if cp.returncode != 0:
        print("ffmpeg failed:", cp.stderr[-400:])
        sys.exit(1)


# real audio: a steady 440 Hz tone and white noise, to see what the numbers say
sh(FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=6", "-ar", "22050", GEN / "tone.wav")
sh(FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=d=6:c=white:a=0.3", "-ar", "22050", GEN / "noise.wav")
pt, rc, _ = t("audio-profile", "--audio", GEN / "tone.wav", "--out", GEN / "tone.json")
pn, rc, _ = t("audio-profile", "--audio", GEN / "noise.wav", "--out", GEN / "noise.json")
check(not any(k in pt for k in ("music_bed", "energy_arc", "reusable_whole")), "the audio profile carries no music-bed, energy-arc or reusable verdict")
check(pt["format"] == 2 and abs(pt["peak_frequency_hz_median"] - 440) < 25 and pt["peak_frequency_steady_share"] >= 0.9 and pt["spectral_flatness_median"] < 0.05,
      "a steady 440 Hz tone: the strongest frequency is 440 Hz and steady, the spectrum is tonal: " + str((pt["peak_frequency_hz_median"], pt["peak_frequency_steady_share"], pt["spectral_flatness_median"])))
check(pn["spectral_flatness_median"] > 0.2 and pn["peak_frequency_steady_share"] < 0.5, "white noise: flat spectrum, no steady frequency: " + str((pn["spectral_flatness_median"], pn["peak_frequency_steady_share"])))
check(all(k in pt for k in ("energy_first_third_db", "energy_last_third_db", "energy_change_db", "harmonic_ratio_non_speech", "beat_strength", "non_speech_audible_share")), "the energy and harmonic numbers are there")


def ac_video(vid, name, dur, segs=None, engine="faster-whisper", language="en", prob=0.99, skipped=False, has_audio=True, speech_starts=None, profile=None, error=None, video_path=None):
    d = ACR / "10-media" / vid
    d.mkdir(parents=True, exist_ok=True)
    words_n = sum(len(s["text"].split()) for s in (segs or []))
    speech_s = round(sum(s["end"] - s["start"] for s in (segs or [])), 2)
    (d / "video.json").write_text(json.dumps({"id": vid, "video": video_path or f"C:/refs/{name}", "probe": {"duration_s": dur}, "audio": {"has_audio": has_audio},
                                              "hook": {"speech_starts_s": speech_starts}}), encoding="utf-8")
    tr = {"engine": engine, "has_speech": words_n > 0, "segments": segs or [], "skipped": skipped}
    if engine:
        tr.update({"model": "small", "language": language, "language_probability": prob, "n_words": words_n, "speech_seconds": speech_s, "wpm_speech_only": round(words_n / (speech_s / 60), 1) if speech_s > 1 else None})
    if error:
        tr["faster_whisper_error"] = error
    (d / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
    (d / "audio.json").write_text(json.dumps({"has_audio": has_audio, "integrated_lufs": -16.0, "lra_lu": 3.0, "silences": [{"start": 1, "end": 2}]}), encoding="utf-8")
    if profile:
        (d / "audio-profile.json").write_text(json.dumps(profile), encoding="utf-8")


def seg(t0, t1, text, p=0.95):
    ws = text.split()
    return {"start": t0, "end": t1, "text": text, "words": [{"w": w, "s": t0, "e": t1, "p": p} for w in ws]}


PROF = {"format": 2, "tempo_bpm": 100, "beat_strength": 0.1, "harmonic_ratio_non_speech": 0.7, "non_speech_audible_share": 0.5, "spectral_flatness_median": 0.01,
        "peak_frequency_hz_median": 440, "peak_frequency_steady_share": 0.9, "energy_change_db": 3.5}
ac_video("V01", "talk.mp4", 20.0, [seg(0.0, 5.0, "You're telling me this works in ten seconds? Stop scrolling."), seg(5.0, 12.0, "Hit the link below before they are gone.")], speech_starts=0.0, profile=PROF)
ac_video("V02", "song.mp4", 15.0, [seg(0.0, 4.0, "my money don't jiggle jiggle it follows"), seg(4.0, 8.0, "my money don't jiggle jiggle it follows"), seg(8.0, 12.0, "my money don't jiggle jiggle it follows")], language="en", prob=0.87, speech_starts=0.0, profile=PROF)
ac_video("V03", "music.mp4", 14.0, [], language="en", prob=0.33, profile=PROF)
ac_video("V04", "foreign.mp4", 18.0, [seg(0.0, 6.0, "ven la chao ven la chao", p=0.3)], language="es", prob=0.29)
ac_video("V05", "broken.mp4", 12.0, [], engine=None, error="no cached faster-whisper model")
ac_video("V06", "skipped.mp4", 12.0, [], engine=None, skipped=True)
ac_video("V07", "silent.mp4", 9.0, [], has_audio=False)
d_ = ACR / "10-media" / "V08"
d_.mkdir(parents=True, exist_ok=True)
(d_ / "video.json").write_text(json.dumps({"id": "V08", "video": "C:/refs/missing.mp4", "probe": {"duration_s": 5}, "audio": {"has_audio": True}}), encoding="utf-8")
(ACR / "10-media" / "docs").mkdir(exist_ok=True)


def acx(*args, ok=True):
    return t("audio-context", "--run", ACR, *args, ok=ok)


digest = ACR / "20-analysis" / "audio-context.md"
js, rc, _ = acx("--check", ok=False)
check(rc == 1 and not js["ok"] and js["without_a_transcript"] == ["V05", "V06", "V08"] and js["videos"] == 8, "a failed, a skipped and a missing transcript fail the check: " + str(js["without_a_transcript"]))
check(js["digest"] is None and not digest.exists(), "--check writes nothing (other agents may be reading the digest)")
check(js["status"] == {"ok": 3, "no-speech": 1, "failed": 1, "skipped": 1, "no-audio": 1, "missing": 1}, "every video gets one status, a fact about the transcription run: " + str(js["status"]))
js, rc, _ = acx("--check", "--out", ACR / "elsewhere.md", ok=False)
check((ACR / "elsewhere.md").exists() and (ACR / "elsewhere.json").exists(), "--check with --out writes to that path")
js, rc, _ = acx(ok=True)
check(digest.exists() and js["ok"], "without --check the digest is written")
data_ = json.loads((ACR / "20-analysis" / "audio-context.json").read_text(encoding="utf-8"))["videos"]
by_ = {r["id"]: r for r in data_}
check(all("kind" not in r and "flags" not in r for r in data_), "no video is labelled (no kind, no flags): " + str(sorted(by_["V02"].keys())[:6]))
check(by_["V01"]["hook_line"].startswith("You're telling me this works in ten seconds?") and by_["V01"]["words"] == 18 and by_["V01"]["first_word_s"] == 0.0 and by_["V01"]["first_word_p_at_least_half_s"] == 0.0,
      "a spoken video: the first sentence, the words, the first word, the first word of probability 0.5 or more")
check(by_["V02"]["repeats"][0]["times"] >= 2 and by_["V02"]["notes"] == [], "repeated three-word phrases are listed as an extraction; no 'lyrics' hint is given")
check(by_["V03"]["status"] == "no-speech" and by_["V03"]["notes"] == [], "no words found: a status, no 'music-or-ambient' label, no advice")
check(by_["V04"]["status"] == "ok" and by_["V04"]["notes"] == [] and by_["V04"]["low_confidence_share"] == 1.0 and by_["V04"]["words_below_half_probability"] == 6 and by_["V04"]["first_word_p_at_least_half_s"] is None and by_["V04"]["language_probability"] == 0.29,
      "an uncertain language and low-probability words are NUMBERS, not flags")
check(by_["V05"]["status"] == "failed" and "no cached faster-whisper model" in by_["V05"]["notes"][0], "a failed transcription says why")
check(by_["V07"]["status"] == "no-audio" and not by_["V07"]["notes"], "a video without an audio track is not an error")
md_ac = digest.read_text(encoding="utf-8")
check("[00:00.00-00:05.00] You're telling me this works in ten seconds? Stop scrolling." in md_ac and "no label such as music bed" in md_ac and "| V04 |" in md_ac and "languages heard: en x2, es x1" in md_ac
      and "flatness 0.01" in md_ac and "peak 440 Hz" in md_ac and "music bed likely" not in md_ac, "the digest carries every transcript line with its times and the sound NUMBERS, and no label")
for vid_ in ("V05", "V06", "V08"):
    (ACR / "10-media" / vid_ / "transcript.json").write_text(json.dumps({"engine": "faster-whisper", "has_speech": False, "segments": [], "skipped": False, "model": "small", "language": "en",
                                                                         "language_probability": 0.4, "n_words": 0, "speech_seconds": 0}), encoding="utf-8")
js, rc, _ = acx("--check")
check(rc == 0 and js["ok"] and js["without_a_transcript"] == [], "once every video has a transcript the check passes")
cards_ = ACR / "20-analysis" / "cards"
cards_.mkdir(parents=True, exist_ok=True)
(cards_ / "V01.md").write_text("# V01\nAudio context: language en (0.99) - voice on-camera - transcript ok\nSaid: \"You're telling me this works in ten seconds?\" a hard sell\n", encoding="utf-8")
(cards_ / "V02.md").write_text("# V02\nAudio context: language en - voice sung - transcript ok\n", encoding="utf-8")
js, rc, _ = acx("--check", ok=False)
check(rc == 1 and js["cards_missing_audio_context"] == {"V02": ["Said:"]}, "a card that lacks its 'Said:' line is listed: " + str(js["cards_missing_audio_context"]))
js, rc, _ = acx("--check", "--cards", ok=False)
check(rc == 1 and js["cards_missing_audio_context"]["V03"] == ["no card"], "--cards makes a missing card a failure")
js, rc, _ = acx("--set", "examples", ok=False)
check(rc == 2 and "no prepared examples" in js.get("error", ""), "a set that was not prepared is refused with the command to prepare it")

# the second pass: every video with no words found, kept between runs; the profile is measured again when its format is old
sh(FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=320x240:d=5:r=15", "-f", "lavfi", "-i", "sine=frequency=1000:duration=5", "-shortest", "-pix_fmt", "yuv420p", GEN / "beep.mp4")
sh(FF, "-y", "-loglevel", "error", "-i", GEN / "beep.mp4", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", ACR / "10-media" / "V03" / "audio-16k-test.wav")
(ACR / "10-media" / "V03" / "audio").mkdir(exist_ok=True)
shutil.copy2(ACR / "10-media" / "V03" / "audio-16k-test.wav", ACR / "10-media" / "V03" / "audio" / "audio-16k.wav")
vj = ACR / "10-media" / "V03" / "video.json"
vd = json.loads(vj.read_text(encoding="utf-8"))
vd["video"] = str(GEN / "beep.mp4")
vj.write_text(json.dumps(vd), encoding="utf-8")
(ACR / "10-media" / "V03" / "audio-profile.json").write_text(json.dumps({"music_bed": "likely", "energy_arc": "rising", "tempo_bpm": 120}), encoding="utf-8")   # an old-format profile
js, rc, _ = acx("--profile", "--second-pass")
prof3 = json.loads((ACR / "10-media" / "V03" / "audio-profile.json").read_text(encoding="utf-8"))
check(prof3["format"] == 2 and "music_bed" not in prof3 and abs(prof3["peak_frequency_hz_median"] - 1000) < 40, "an old-format profile is measured again with --profile: the strongest frequency of the 1 kHz beep is " + str(prof3["peak_frequency_hz_median"]))
by_ = {r["id"]: r for r in json.loads((ACR / "20-analysis" / "audio-context.json").read_text(encoding="utf-8"))["videos"]}
sp3 = by_["V03"].get("second_pass")
check(sp3 is not None and sp3["vad_filter"] is False and "words" in sp3, "--second-pass transcribes a video with no words found again without the voice filter: " + str(sp3 and (sp3["words"], sp3["text"][:40])))
check("second_pass" not in by_["V05"] and "second_pass" not in by_["V07"], "...only for videos in which no words were found")
js, rc, _ = acx()
by2_ = {r["id"]: r for r in json.loads((ACR / "20-analysis" / "audio-context.json").read_text(encoding="utf-8"))["videos"]}
check(by2_["V03"].get("second_pass") == sp3, "a second pass made earlier stays in the digest when it is written again")

finish()
