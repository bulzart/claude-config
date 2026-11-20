"""Tests for cc_voices (who speaks, as facts: the transcript's words that match the subtitle on screen) and what uses it: the [sub] marks in transcript.txt and
`window`, the `words` markers, the report signature that the marks never change, the processor's step, and captions.skip.

A real video is made with ffmpeg (subtitles burned in as white text with a black border, like a game's), next to a transcript whose words say the game's lines
(one spelled differently), the streamer's lines (no text on screen) and a line spoken over another subtitle. Run: python tests/test_voices.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "scripts" / "cc.py"
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_voices as V  # noqa: E402
import cc_tables  # noqa: E402
import cc_report  # noqa: E402
import cc_edit  # noqa: E402

PY = sys.executable


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    return (json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-600:]}), cp.stdout


SUBS = [(1.0, 3.5, "We sell that drive, we will have all the money we need."),
        (4.5, 6.5, "Nah, I would not make you come all the way out here."),
        (9.0, 11.0, "Search the safe for the diamond ring")]
W = lambda s, e, t: {"w": t, "s": s, "e": e, "p": 0.9}  # noqa: E731
TRANSCRIPT_WORDS = [
    # the game's first line, Whisper spelling one word differently ("their" for "that")
    W(1.10, 1.30, "We"), W(1.30, 1.50, "sell"), W(1.50, 1.70, "their"), W(1.70, 2.00, "drive,"), W(2.00, 2.20, "we"), W(2.20, 2.40, "will"), W(2.40, 2.60, "have"),
    W(2.60, 2.80, "all"), W(2.80, 2.95, "the"), W(2.95, 3.20, "money"), W(3.20, 3.30, "we"), W(3.30, 3.45, "need."),
    # the game's second line
    W(4.60, 4.80, "Nah,"), W(4.80, 4.90, "I"), W(4.90, 5.10, "would"), W(5.10, 5.25, "not"), W(5.25, 5.45, "make"), W(5.45, 5.55, "you"), W(5.55, 5.75, "come"),
    W(5.75, 5.90, "all"), W(5.90, 6.00, "the"), W(6.00, 6.15, "way"), W(6.15, 6.30, "out"), W(6.30, 6.45, "here."),
    # the streamer, nothing on screen
    W(7.00, 7.30, "Chat,"), W(7.30, 7.50, "look"), W(7.50, 7.70, "at"), W(7.70, 8.00, "this."),
    # the streamer over a mission prompt (other text on screen)
    W(9.20, 9.50, "Lord"), W(9.50, 9.70, "have"), W(9.70, 10.00, "mercy."),
]


def make_video(path: Path, tmp: Path):
    vf = []
    for k, (a, b, text) in enumerate(SUBS):
        tf = tmp / f"sub{k}.txt"
        tf.write_text(text, encoding="utf-8")
        tfe = str(tf).replace("\\", "/").replace(":", "\\:")
        vf.append(f"drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':textfile='{tfe}':fontcolor=white:fontsize=40:borderw=3:bordercolor=black:"
                  f"x=(w-tw)/2:y=h*0.86:enable='between(t,{a},{b})'")
    # a game's button prompt at the right edge, on the same rows as the second subtitle (it must not be read together with it)
    vf.append("drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='INTERRUPT':fontcolor=white:fontsize=34:borderw=3:bordercolor=black:"
              "x=w*0.86:y=h*0.865:enable='between(t,4.5,6.5)'")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30,colorlevels=romax=0.35:gomax=0.35:bomax=0.35", "-t", "12",
           "-vf", ",".join(vf), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "60", str(path)]
    subprocess.run(cmd, check=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-voices-test-"))
    try:
        run = tmp / "runs" / "20261120-000000-voicetest"
        cd = run / "10-media" / "C0001"
        cd.mkdir(parents=True)
        make_video(cd / "chunk.mp4", tmp)
        (cd / "probe.json").write_text(json.dumps({"duration_s": 12.0, "width": 1920, "height": 1080, "has_video": True, "has_audio": True}), encoding="utf-8")
        segs = [{"start": 1.10, "end": 3.45, "text": "We sell their drive, we will have all the money we need.", "words": TRANSCRIPT_WORDS[0:12]},
                {"start": 4.60, "end": 6.45, "text": "Nah, I would not make you come all the way out here.", "words": TRANSCRIPT_WORDS[12:24]},
                {"start": 7.00, "end": 8.00, "text": "Chat, look at this.", "words": TRANSCRIPT_WORDS[24:28]},
                {"start": 9.20, "end": 10.00, "text": "Lord have mercy.", "words": TRANSCRIPT_WORDS[28:31]}]
        tr = {"engine": "faster-whisper", "rec_start_s": 100.0, "duration_s": 12.0, "segments": segs, "n_words": 31}
        (cd / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
        (run / "00-inventory").mkdir(parents=True)
        (run / "00-inventory" / "chunks.json").write_text(json.dumps([{"id": "C0001", "index": 1, "rec_start_s": 100.0, "duration_s": 12.0, "status": "done",
                                                                        "stages": {"transcript": True, "move": True}}]), encoding="utf-8")
        (run / "state.json").write_text('{"schema":"cc/1","channel":"voicetest"}', encoding="utf-8")

        # the plain view is exactly what it always was when there are no labels
        old = "\n".join(f"[{cc_tables.fmt_hms(100.0 + s['start'])}-{cc_tables.fmt_hms(100.0 + s['end'])}] (C0001 +{s['start']:.2f}) {s['text']}" for s in segs) + "\n"
        check(cc_tables.render_transcript_txt("C0001", 100.0, tr) == old and cc_tables.render_transcript_txt("C0001", 100.0, tr, None) == old,
              "transcript.txt without voices labels is byte for byte the old view")
        (cd / "transcript.txt").write_bytes(old.replace("\n", "\r\n").encode("utf-8"))      # an old file with other line ends: its signature must still hold
        row = {"id": "C0001", "rec_start_s": 100.0, "duration_s": 12.0, "frames": None, "words": 31}
        sig_before = cc_report.source_sig(run, row)

        # the facts: one chunk read
        res = V.chunk_voices(run, "C0001")
        v = json.loads((cd / "voices.json").read_text(encoding="utf-8"))
        lab = v["labels"]
        check(res.get("ok") and v["schema"] == V.SCHEMA and v["version"] == V.VERSION and len(lab) == 31, "voices.json written: schema, version, one label per word: " + json.dumps(res)[:200])
        check(lab[0:12] == "S" * 12, "the game's first line is marked S, the word Whisper spelled differently ('their' for 'that') included: " + lab[0:12])
        check(lab[12:24] == "S" * 12, "the game's second line is marked S: " + lab[12:24])
        check(lab[24:28] == "....", "the streamer's line with nothing on screen is '.', not attributed: " + lab[24:28])
        check(lab[28:31] == "ooo", "words spoken over other on-screen text (a mission prompt) are 'o' (it says nothing about who): " + lab[28:31])
        texts = [x["text"] for x in v["lines"]]
        check(any("sell that drive" in t.lower() for t in texts) and any("diamond ring" in t.lower() for t in texts), "the subtitle lines are read as printed: " + json.dumps(texts)[:200])
        check(all(0.80 <= x["y"] <= 0.95 for x in v["lines"]) and v["summary"]["subtitle_y_median"] is not None, "each line's height on the picture is kept (subtitle_y_median for caption placement)")
        check(v["lines"][0]["rec_from"] >= 100.0 and v["lines"][0]["rec_from"] <= 101.6, "the lines carry rec times: " + str(v["lines"][0]["rec_from"]))
        res2 = V.chunk_voices(run, "C0001")
        check(res2.get("skipped") == "current", "a second read is skipped while voices.json is current (resume, no duplicate work)")

        # the marked view and its tools
        labels = V.labels_for(run, "C0001")
        txt = cc_tables.render_transcript_txt("C0001", 100.0, tr, labels)
        check(txt.startswith(cc_tables.SUB_HEADER) and "(C0001 +1.10) [sub] We sell their drive" in txt and "(C0001 +7.00) Chat, look at this." in txt
              and "[sub] Lord" not in txt, "transcript.txt marks the subtitled lines [sub], leaves the streamer's lines plain:\n" + txt[:400])
        check(V.render_chunk_transcript(run, "C0001") and (cd / "transcript.txt").read_text(encoding="utf-8") == txt, "render_chunk_transcript writes the marked view")
        check(cc_report.source_sig(run, row) == sig_before, "the [sub] marks and voices.json never make the chunk's report stale (same signature)")
        check(any(p.name == "voices.json" for p in cc_report.must_open(cc_report.inputs(run, "C0001"))),
              "the reporter is given voices.json to read")
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs"), "CC_NOTIFY": "0", "PYTHONIOENCODING": "utf-8"}
        r, stdout = cc("words", "--run", run, "--from", 100, "--to", 112, env=env)
        check(r.get("ok") and r.get("subtitled_words") == 24 and "[sub] We" in stdout and "here. [/sub]" in stdout and "[sub] Chat," not in stdout,
              "`words` shows [sub] ... [/sub] around the subtitled words: " + stdout.replace("\n", " | ")[:300])
        r, stdout = cc("window", "--run", run, "--from", 100, "--to", 112, "--what", "transcript", env=env)
        check(r.get("ok") and r.get("sub_marks") is True and "[sub] We sell their drive" in stdout, "`window` marks the subtitled lines too")
        r, _ = cc("voices", "--run", run, env=env)
        check(r.get("ok") and r.get("current") == 1 and r.get("made") == 0 and r["totals"]["subtitled"] == 24 and r.get("warning") is None,
              "`voices` on a run: the current chunk is not read again, the totals are reported: " + json.dumps(r)[:300])

        # a changed transcript makes the labels stale: they are not used until read again
        tr2 = json.loads(json.dumps(tr))
        tr2["segments"][2]["words"][0]["w"] = "Chad,"
        (cd / "transcript.json").write_text(json.dumps(tr2), encoding="utf-8")
        check(V.labels_for(run, "C0001") is None, "labels for an older transcript are not used (stale)")
        (cd / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")

        # the matcher on its own: a line matched once only, a short line ignored, a far substitution not taken
        words = [(0.5, 0.7, "Yeah,"), (0.7, 0.9, "for"), (0.9, 1.2, "now."), (5.0, 5.2, "Yeah,"), (5.2, 5.4, "for"), (5.4, 5.7, "now.")]
        ev = [{"t0": 0.4, "t1": 1.5, "text": "Yeah for now.", "tokens": V.norm_tokens("Yeah for now."), "conf": 0.99, "y": 0.86}]
        lab2, spans = V.match(ev, words)
        check(lab2 == "SSS...", "a subtitle line is matched once: the streamer repeating it later is not marked: " + lab2)
        lab3, _ = V.match([{"t0": 0.4, "t1": 1.5, "text": "Yeah.", "tokens": ["yeah"], "conf": 0.99, "y": 0.86}], words)
        check(lab3[:3] == "ooo", "a one-word subtitle is not used to attribute anything (too easy to match by chance): " + lab3)
        lab4, _ = V.match([{"t0": 0.4, "t1": 1.5, "text": "zebra yeah for now", "tokens": ["zebra", "yeah", "for", "now"], "conf": 0.99, "y": 0.86}],
                          [(0.1, 0.3, "Look"), (0.3, 0.45, "at"), (0.45, 0.6, "him"), (0.6, 0.8, "yeah"), (0.8, 1.0, "for"), (1.0, 1.2, "now")])
        check(lab4 == ".ooSSS", "words at the edge of a line that do not look like its words are never joined to it (the streamer over the game line): " + lab4)
        lab5, _ = V.match([{"t0": 0.4, "t1": 1.5, "text": "'Ey, you see the studio", "tokens": V.norm_tokens("'Ey, you see the studio"), "conf": 0.99, "y": 0.86}],
                          [(0.5, 0.7, "Hey,"), (0.7, 0.8, "you"), (0.8, 1.0, "see"), (1.0, 1.1, "the"), (1.1, 1.4, "studio")])
        check(lab5 == "SSSSS", "an edge word that looks like the subtitle's ('Hey' under ''Ey') joins the line: " + lab5)
        lab6, _ = V.match([{"t0": 0.4, "t1": 2.5, "text": "Mira, I sold three houses after listening", "tokens": V.norm_tokens("Mira, I sold three houses after listening"),
                            "conf": 0.99, "y": 0.86}],
                          [(0.5, 0.7, "He's"), (0.7, 0.9, "scamming"), (0.9, 1.1, "you!"), (1.2, 1.4, "Three"), (1.4, 1.6, "houses"), (1.6, 1.8, "after"), (1.8, 2.1, "listening")])
        check(lab6 == "oooSSSS", "the caseoh case: 'He's scamming you!' spoken over the start of the game's line stays unattributed: " + lab6)
        lab7, _ = V.match([{"t0": 0.4, "t1": 2.0, "text": "thelab okaygotta go", "tokens": ["thelab", "okaygotta", "go"], "conf": 0.9, "y": 0.86}],
                          [(0.5, 0.6, "the"), (0.6, 0.9, "lab."), (0.9, 1.2, "Okay,"), (1.2, 1.3, "I"), (1.3, 1.5, "gotta"), (1.5, 1.7, "go.")])
        check(lab7 == "SSSSSS", "words OCR ran together ('thelab', 'okaygotta') are read as the transcript's two words: " + lab7)
        check(V.split_joined(["knowwhat", "zzzz", "go"], {"know", "what", "go"}) == ["know", "what", "zzzz", "go"], "split_joined splits only a token that is two known words")
        check(not any("INTERRUPT" in x["text"] for x in v["lines"]), "a button prompt at the edge, on the subtitle's rows, is not read into the subtitle line")

        # captions.skip: words in a skipped rec span get no caption; nothing changes without it
        resolved = {"pieces": [{"kind": "clip", "chunk": "C0001", "src_from": 0.0, "src_to": 12.0, "at": 0.0, "speed": 1.0, "rec_from": 100.0}],
                    "captions": {}}
        all_words = cc_edit._resolved_words(run, resolved)
        resolved["captions"] = {"skip": [{"rec_from": 104.5, "rec_to": 106.6, "why": "test"}, {"bad": 1}]}
        skipped = []
        kept = cc_edit._resolved_words(run, resolved, skipped)
        check(len(all_words) == 31 and len(kept) == 19 and len(skipped) == 12 and all(not (104.5 <= w["rec"] < 106.6) for w in kept),
              f"captions.skip leaves out the words of its span (31 words, 12 skipped, a bad entry ignored): {len(all_words)} {len(kept)} {len(skipped)}")
        check(cc_edit._skip_spans({"captions": {"skip": [[1, 2], {"rec_from": 5, "rec_to": 4}, "x"]}}) == [[1.0, 2.0]], "only valid skip spans are used")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL PASSED" if not check.failed else f"FAILED: {check.failed}")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
