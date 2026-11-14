"""Test of the spoken-language handling (no real Whisper: a stand-in model names a language and says how sure it is).

    python tests/test_language.py

The config's language is 'auto': Whisper names the language of the chunk; a guess it is not sure of falls back to `fallback_language`; the first sure detection on real speech of a stream
chunk becomes the run's language (state.json settings.whisper.language_locked) and the chunks after it are told that language; an ad chunk never locks and never uses the lock; a language
the user set (the run's override) is never touched; the captions and stream.md read the language from the run.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failed += 1


class Info:
    def __init__(self, language, p):
        self.language, self.language_probability = language, p


class FakeModel:
    """transcribe(path, language=None, **kw): language None = Whisper names it itself (`guess`); a given language = that language, probability 1."""

    def __init__(self, guess=("de", 0.97), n_words=60):
        self.guess, self.n_words, self.calls = guess, n_words, []

    def transcribe(self, path, language=None, **kw):
        self.calls.append(language)
        info = Info(*self.guess) if language is None else Info(language, 1.0)
        words = [types.SimpleNamespace(word=f" w{i}", start=i * 0.4, end=i * 0.4 + 0.3, probability=0.9) for i in range(self.n_words)]
        seg = types.SimpleNamespace(start=0.0, end=max(0.5, self.n_words * 0.4), text=" test", avg_logprob=-0.2, no_speech_prob=0.01, compression_ratio=1.1, words=words)
        return iter([seg]), info


def transcriber(model, **cfg):
    import cc_audio
    t = cc_audio.Transcriber({"model": "tiny"})
    t.cfg.update({"language": "auto", "fallback_language": "en", "detect_min_probability": 0.85, **cfg})
    t.model, t._gate = model, threading.BoundedSemaphore(1)
    return t


def main():
    import cc_edit
    import cc_proc as P
    import cc_tables

    # 1. the transcriber: detection, the fallback for an unsure guess, a forced language
    m = FakeModel(("de", 0.97))
    r = transcriber(m).transcribe("x.wav", 0.0, 10.0)
    check(r["language"] == "de" and r["language_source"] == "detected" and m.calls == [None] and r["detected_language"] == "de", f"auto: a sure guess (de, 0.97) is used, decoded once: {m.calls}")
    m = FakeModel(("nn", 0.40))
    r = transcriber(m).transcribe("x.wav", 0.0, 10.0)
    check(r["language"] == "en" and r["language_source"] == "fallback" and m.calls == [None, "en"] and r["detected_language"] == "nn" and r["detected_probability"] == 0.4,
          f"auto: an unsure guess (nn, 0.40) is not trusted, the fallback language decodes the chunk and the guess is kept as a fact: {m.calls}")
    m = FakeModel(("nn", 0.40))
    r = transcriber(m, fallback_language="").transcribe("x.wav", 0.0, 10.0)
    check(r["language"] == "nn" and r["language_source"] == "detected" and m.calls == [None], "auto with no fallback language configured: the guess is kept as it is")
    m = FakeModel(("de", 0.97))
    r = transcriber(m).transcribe("x.wav", 0.0, 10.0, language="es")
    check(r["language"] == "es" and r["language_source"] == "forced" and m.calls == ["es"] and "detected_language" not in r, "a language given for the call (the run's locked one) is forced: no detection")
    m = FakeModel(("de", 0.97))
    r = transcriber(m, language="fr").transcribe("x.wav", 0.0, 10.0)
    check(r["language"] == "fr" and r["language_source"] == "forced" and m.calls == ["fr"], "a language in the config is forced too")

    with tempfile.TemporaryDirectory(prefix="cc-lang-test-") as tmp:
        tmp = Path(tmp)

        def make_run(name, language="auto"):
            run = tmp / name
            (run / "00-inventory").mkdir(parents=True)
            (run / "state.json").write_text(json.dumps({"schema": "cc/1", "channel": "x", "session": name, "settings": {"whisper": {"language": language}}}), encoding="utf-8")
            return run

        def state(run):
            return json.loads((run / "state.json").read_text(encoding="utf-8"))["settings"]["whisper"]

        sure = {"language": "de", "language_probability": 0.97, "language_source": "detected", "n_words": 120}
        auto = {"language": "auto"}

        # 2. the lock: the first sure detection on a stream chunk becomes the run's language
        run = make_run("20261114-000000-a")
        check(P.stream_language(run, {"id": "C0001"}, auto) is None, "an unlocked run: nothing is told to Whisper, it detects in the chunk")
        check(P.lock_language(run, "C0001", {"id": "C0001"}, auto, sure) is True and state(run)["language_locked"] == "de" and state(run)["language"] == "de"
              and "C0001" in state(run)["language_locked_from"], "a sure detection on real speech locks the run's language: " + json.dumps(state(run)))
        check(P.stream_language(run, {"id": "C0002"}, auto) == "de", "the chunks after it are told that language")
        check(P.lock_language(run, "C0002", {"id": "C0002"}, auto, {**sure, "language": "en"}) is False and state(run)["language_locked"] == "de", "a later detection never changes the lock")
        check(P.stream_language(run, {"id": "C0003", "kind": "ad"}, auto) is None, "an ad chunk does not use the lock (an advertisement is in its own language)")

        # 3. what does not lock
        for label, row, ov, tr in (("an ad chunk", {"id": "C0001", "kind": "ad"}, auto, sure),
                                   ("a fallback", {"id": "C0001"}, auto, {**sure, "language_source": "fallback"}),
                                   ("a forced language", {"id": "C0001"}, auto, {**sure, "language_source": "forced"}),
                                   ("little speech (10 words)", {"id": "C0001"}, auto, {**sure, "n_words": 10}),
                                   ("an unsure guess (0.5)", {"id": "C0001"}, auto, {**sure, "language_probability": 0.5}),
                                   ("the user's own language for the run", {"id": "C0001"}, {"language": "en"}, sure)):
            r2 = make_run("20261114-000000-" + label.split()[1].strip("()"))
            check(P.lock_language(r2, "C0001", row, ov, tr) is False and not state(r2).get("language_locked"), f"{label} never locks the run's language")
        r3 = make_run("20261114-000000-user")
        check(P.stream_language(r3, {"id": "C0001"}, {"language": "en"}) is None, "a language the user set for the run is left to the transcriber (forced), never replaced by a lock")

        # 4. the captions read the run's language: locked or chosen, else what Whisper reported most often for the stream chunks
        run4 = make_run("20261114-000000-cap")
        rows = [{"id": "C0001", "index": 1, "language": "en", "kind": "ad"}, {"id": "C0002", "index": 2, "language": "de"}, {"id": "C0003", "index": 3, "language": "de"},
                {"id": "C0004", "index": 4, "language": "en"}]
        (run4 / "00-inventory" / "chunks.json").write_text(json.dumps(rows), encoding="utf-8")
        check(cc_edit.whisper_language(run4) == "de", "no lock yet: the language of the captions is the one reported most often for the stream chunks (the ad chunk does not count)")
        P.lock_language(run4, "C0002", rows[1], auto, {**sure, "language": "es"})
        check(cc_edit.whisper_language(run4) == "es", "a locked language wins")
        run5 = make_run("20261114-000000-ja", "ja")
        check(cc_edit.whisper_language(run5) == "ja", "a language chosen for the run (settings.whisper.language) is what the captions use")

        # 5. stream.md says the language as a fact
        def full(i, lang, kind=None):
            r = {"id": f"C{i:04d}", "index": i, "file": f"10-media/C{i:04d}/chunk.mp4", "rec_start_s": (i - 1) * 180.0, "duration_s": 180.0, "t0_utc": f"2026-11-14T00:{i:02d}:00.000Z",
                 "t1_utc": f"2026-11-14T00:{i:02d}:50.000Z", "gap_before_s": 0, "ads_skipped_s": 0, "ended_by": "duration", "status": "done", "language": lang,
                 "stages": {s: True for s in ("move", "probe", "audio", "sheets", "transcript", "digest")}}
            if kind:
                r["kind"] = kind
            return r
        st5 = {"session": "x", "channel": "x", "settings": {"whisper": {"language_locked": "de", "language_locked_from": "C0002: de, probability 0.97, 120 words"}}}
        cc_tables.build_stream_md(run4, [full(1, "en", "ad"), full(2, "de"), full(3, "de")], st5)
        md = (run4 / "00-inventory" / "stream.md").read_text(encoding="utf-8")
        check("Spoken language (Whisper's detection, a fact): de in 2 chunks" in md and "the run's language is de" in md and "en in" not in md.split("\n")[4],
              "stream.md names the spoken language and the lock, and does not count the ad chunk: " + md.split("\n")[4][:160])
        cc_tables.build_stream_md(run4, [full(2, None), full(3, None)], {"session": "x", "channel": "x"})
        check("Spoken language" not in (run4 / "00-inventory" / "stream.md").read_text(encoding="utf-8"), "a run with no transcripts has no language line")

    print("ALL PASSED" if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
