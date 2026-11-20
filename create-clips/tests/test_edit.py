"""Regression test of cc_edit.py on a synthetic two-chunk run (no network, no CapCut store touched).

    python tests/test_edit.py            (Python312; ffmpeg on PATH; takes about a minute: the SFX scan is the slow part and is skipped here)

Builds two 12 s test chunks with ffmpeg, a transcript for each, then checks: layout maths, the EDL resolve across a chunk boundary, the censor split and file,
caption cues (masking, replacement), the cut facts, the MCP plan and finish plan, and capcut-finish against a draft in an isolated store (capcut-cli init --drafts);
the caption styles the user picks at the start: the Luckiest Guy box (the word on a rounded colour box) and the Montserrat highlight (white, only the spoken word
yellow), and the no-box look older runs may hold (Montserrat Bold, yellow, one text per caption); the caption_style setting and how legacy runs read.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent / "scripts" / "cc.py"
PY = sys.executable
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401  (the scripts may be encrypted at rest: the hook decrypts them with CC_SOURCE_KEY)
import cc_wordbox as wb  # noqa: E402


def cc(*args, env=None):
    cp = subprocess.run([PY, str(CC), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=900)
    last = [ln for ln in cp.stdout.strip().splitlines() if ln.startswith("{")]
    return json.loads(last[-1]) if last else {"ok": False, "stderr": cp.stderr[-400:]}


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def r_cues(out_dir) -> int:
    """The number of caption cues `captions` wrote for a video (captions.json next to its EDL)."""
    return len(json.loads((Path(out_dir) / "captions.json").read_text(encoding="utf-8"))["cues"])


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cc-edit-test-"))
    try:
        env = {**os.environ, "CC_RUNS_ROOT": str(tmp / "runs")}
        run = tmp / "runs" / "20261112-000000-testch"
        for n in (1, 2):
            d = run / "10-media" / f"C000{n}"
            d.mkdir(parents=True)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=60", "-f", "lavfi", "-i",
                            f"sine=frequency={440 * n}:sample_rate=48000", "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "120", "-c:a", "aac", str(d / "chunk.mp4")],
                           check=True)
        (run / "00-inventory").mkdir(parents=True)
        (run / "00-inventory" / "chunks.json").write_text(json.dumps([
            {"id": "C0001", "index": 1, "rec_start_s": 0.0, "duration_s": 12.0, "status": "done"},
            {"id": "C0002", "index": 2, "rec_start_s": 12.0, "duration_s": 12.0, "status": "done", "gap_before_s": 0}]), encoding="utf-8")
        (run / "state.json").write_text('{"schema":"cc/1","channel":"testch"}', encoding="utf-8")
        w = lambda s, e, t: {"w": t, "s": s, "e": e, "p": 1}  # noqa: E731
        (run / "10-media" / "C0001" / "transcript.json").write_text(json.dumps({"segments": [{"words": [
            w(1.0, 1.4, "Hello"), w(1.5, 1.9, "chat,"), w(2.0, 2.2, "this"), w(2.3, 2.4, "is"), w(2.5, 3.0, "wild."), w(3.4, 4.0, "Absolutely"), w(4.1, 4.6, "crazy")]}]}), encoding="utf-8")
        (run / "10-media" / "C0002" / "transcript.json").write_text(json.dumps({"segments": [{"words": [
            w(0.5, 0.9, "Damn"), w(1.0, 1.2, "Kai"), w(1.3, 1.6, "Sinat"), w(1.7, 2.1, "shit.")]}]}), encoding="utf-8")

        r = cc("layout-calc", "--src", "1280x720", "--canvas", "1080x1920", "--mode", "fill", "--focus", "0.3,0.5")
        check(abs(r["scale"] - 3.16049) < 1e-3 and abs(r["posX"] - 1.2642) < 1e-3 and not r["clamped"], "layout-calc fill focus 0.3")
        r = cc("layout-calc", "--src", "1280x720", "--canvas", "1080x1920", "--mode", "fill", "--focus", "0.0,0.5")
        check(r["clamped"], "layout-calc clamps a focus at the edge")

        edl = {"schema": "cc-edl/1", "video": "S01", "kind": "short", "layout": {"mode": "fill", "focus": [0.5, 0.5]},
               "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0, "zoom": [{"at": 1.0, "to": 1.2, "in": 0.2, "hold": 1.0, "out": 0.2}]},
                            {"id": "s2", "rec_from": 10.0, "rec_to": 15.0, "transition_in": {"slug": "flash", "dur": 0.2},
                             "censor": [{"rec_from": 11.0, "rec_to": 12.5, "region": [0.1, 0.1, 0.4, 0.4], "style": "blur", "why": "test"}],
                             "layout": {"mode": "fill", "focus": [0.3, 0.5]}}],
               "captions": {"mask_terms": ["damn"], "highlight_words": ["wild"], "replace": [["Kai Sinat", "Kai Cenat"]]}}
        out = run / "60-outputs" / "S01"
        out.mkdir(parents=True)
        sfx_file = Path("C:/Users/Bulzart/Documents/sound_effects/vine boom.mp3")
        if sfx_file.is_file():                                  # one sound effect on its own lane (skipped on a PC without the folder)
            edl["sfx"] = [{"file": str(sfx_file).replace("\\", "/"), "at": {"seg": "s1", "t": 1.2}, "volume": 0.7, "why": "test"}]
        (out / "edl.json").write_text(json.dumps(edl), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", out / "edl.json", "--make-censor", env=env)
        check(r.get("ok"), "edl-check ok: " + json.dumps(r.get("warnings")))
        check(r["totals"]["pieces"] == 5 and r["totals"]["chunks_used"] == ["C0001", "C0002"], "five pieces over two chunks (the censor span crosses the boundary)")
        check(abs(r["totals"]["duration_s"] - 9.1) < 0.01, "duration 9.1 s")
        res = json.loads((out / "resolved.json").read_text(encoding="utf-8"))
        check(len(list((run / "30-assets" / "censor").glob("C000*-*.mp4"))) == 2, "two blurred files made")
        check(all(abs(p["at"] - sum(q["dur_out"] for q in res["pieces"][:i])) < 1e-6 for i, p in enumerate(res["pieces"])), "pieces are contiguous on the output timeline")
        plan = json.loads((out / "mcp-plan.json").read_text(encoding="utf-8"))
        check(sum(1 for o in plan["ops"] if o["op"] == "add_video") == 5, "mcp plan has 5 add_video ops")
        fin = json.loads((out / "finish.json").read_text(encoding="utf-8"))
        check(len(fin["zoom"]) == 1 and fin["transitions"][0]["refused"] is None, "finish plan: one zoom, the flash transition accepted")
        r = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
        srt = (out / "captions.srt").read_text(encoding="utf-8")
        check(r.get("ok") and "SH*T" in srt and "D*MN" in srt and "KAI CENAT" in srt and "SHIT" not in srt and "DAMN" not in srt,
              "captions: the default list masks shit (SH*T), the EDL's mask_terms masks damn (D*MN), the lexicon replace applied: " + srt.replace("\n", " | ")[:200])
        check(r.get("masked_words") == 2 and r.get("masked", {}).get("sh*t") == 1 and r.get("masked", {}).get("d*mn") == 1,
              "captions: the answer tallies what was masked (as typed): " + json.dumps(r.get("masked")))
        res_on = json.loads((out / "resolved.json").read_text(encoding="utf-8"))
        check(res_on["captions"].get("enabled") is True and fin["captions"].get("enabled") is True,
              "captions are ON when the run has no `captions` key: resolved.json and finish.json say enabled")

        # the word-box look needs a text per word and state: too many spoken words, or a language it cannot take, fall back to the plain look with the reason written down
        e4 = {"schema": "cc-edl/1", "video": "S04", "kind": "short", "layout": {"mode": "fill", "focus": [0.5, 0.5]}, "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}],
              "captions": {"word_box_max_words": 3}}
        o4 = run / "60-outputs" / "S04"
        o4.mkdir(parents=True)
        (o4 / "edl.json").write_text(json.dumps(e4), encoding="utf-8")
        cc("edl-check", "--run", run, "--edl", o4 / "edl.json", env=env)
        res4 = json.loads((o4 / "resolved.json").read_text(encoding="utf-8"))
        check(res4["captions"]["style"] == "plain" and "spoken words" in res4["captions"].get("style_reason", ""),
              "more spoken words than captions.word_box_max_words: the plain look is used, with the reason: " + str(res4["captions"].get("style_reason"))[:120])
        e4["captions"] = {}
        (o4 / "edl.json").write_text(json.dumps(e4), encoding="utf-8")
        cc("state", "--run", run, "set", "settings.whisper.language=ja", env=env)
        cc("edl-check", "--run", run, "--edl", o4 / "edl.json", env=env)
        res4 = json.loads((o4 / "resolved.json").read_text(encoding="utf-8"))
        check(res4["captions"]["style"] == "plain" and "without spaces" in res4["captions"].get("style_reason", ""), "a language written without spaces (ja): the plain look, with the reason")
        cc("state", "--run", run, "set", "settings.whisper.language=en", env=env)
        cc("edl-check", "--run", run, "--edl", o4 / "edl.json", env=env)
        check(json.loads((o4 / "resolved.json").read_text(encoding="utf-8"))["captions"]["style"] == "word-box", "English: the word-box look is the default")

        # a short is ALWAYS 9:16 (the user, 2026-11-14): another canvas in a short's EDL is a warning (edl-check is then not ok); the default and an explicit 1080x1920 pass; a long video keeps 16:9
        e9 = {"schema": "cc-edl/1", "video": "S09", "kind": "short", "canvas": {"width": 1920, "height": 1080, "fps": 30}, "layout": {"mode": "fill", "focus": [0.5, 0.5]},
              "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}]}
        o9 = run / "60-outputs" / "S09"
        o9.mkdir(parents=True)
        (o9 / "edl.json").write_text(json.dumps(e9), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", o9 / "edl.json", env=env)
        check(r.get("ok") is False and any("9:16" in str(w.get("warning")) for w in r.get("warnings") or []),
              "a short with a 1920x1080 canvas: edl-check warns that a short is always 9:16 and is not ok: " + json.dumps(r.get("warnings"))[:160])
        e9["canvas"] = {"width": 1080, "height": 1920, "fps": 30}
        (o9 / "edl.json").write_text(json.dumps(e9), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", o9 / "edl.json", env=env)
        check(not any("9:16" in str(w.get("warning")) for w in r.get("warnings") or []), "a short with an explicit 1080x1920 canvas: no 9:16 warning")
        e9.pop("canvas")
        (o9 / "edl.json").write_text(json.dumps(e9), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", o9 / "edl.json", env=env)
        res9 = json.loads((o9 / "resolved.json").read_text(encoding="utf-8"))
        check(not any("9:16" in str(w.get("warning")) for w in r.get("warnings") or []) and (res9["canvas"]["width"], res9["canvas"]["height"]) == (1080, 1920),
              "a short with no canvas in its EDL gets 1080x1920 by default and no warning")
        l9 = {"schema": "cc-edl/1", "video": "L09", "kind": "long", "canvas": {"width": 1920, "height": 1080, "fps": 30}, "layout": {"mode": "native"},
              "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}]}
        ol9 = run / "60-outputs" / "L09"
        ol9.mkdir(parents=True)
        (ol9 / "edl.json").write_text(json.dumps(l9), encoding="utf-8")
        r = cc("edl-check", "--run", run, "--edl", ol9 / "edl.json", env=env)
        check(not any("9:16" in str(w.get("warning")) for w in r.get("warnings") or []), "a long video's 16:9 canvas is not touched by the 9:16 rule")

        # block sizing: a short recording still gets side-by-side agents
        r = cc("blocks", "--run", run, "--chunks", 10, env=env)
        check(r.get("ok") and len(r["blocks"]) == 1 and r["blocks"][0]["chunks"] == ["C0001", "C0002"], "blocks: two chunks are one block by default")
        r = cc("blocks", "--run", run, "--chunks", 10, "--min-blocks", 2, env=env)
        check(r.get("ok") and len(r["blocks"]) == 2 and r["block_size"] == 1 and r["min_blocks"] == 2, "blocks --min-blocks 2: two chunks make two blocks")
        r = cc("blocks", "--run", run, "--chunks", 1, "--min-blocks", 2, env=env)
        check(r.get("ok") and r["block_size"] == 1, "blocks --min-blocks never makes a block bigger than --chunks")

        # the user picked NO captions at the start (state.json captions=off): nothing is written, the finish plan says so
        (out / "captions.srt").unlink()
        (out / "captions.json").unlink()
        r = cc("state", "--run", run, "set", "captions=off", env=env)
        check(r.get("ok"), "state: captions=off recorded")
        r = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
        check(r.get("ok") and r.get("skipped") is True and not (out / "captions.srt").exists() and not (out / "captions.json").exists(),
              "captions OFF: `captions` answers skipped and writes no cue file")
        r = cc("edl-check", "--run", run, "--edl", out / "edl.json", env=env)
        fin_off = json.loads((out / "finish.json").read_text(encoding="utf-8"))
        check(r.get("ok") and fin_off["captions"].get("enabled") is False, "captions OFF: finish.json carries captions.enabled false")
        for word in ("false", "0", "no"):
            r = cc("state", "--run", run, "set", f"captions={word}", env=env)
            r2 = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
            check(r2.get("skipped") is True, f"captions={word} is read as off")
        cc("state", "--run", run, "set", "captions=on", env=env)
        r = cc("edl-check", "--run", run, "--edl", out / "edl.json", env=env)
        r = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
        check(r.get("ok") and not r.get("skipped") and (out / "captions.srt").is_file(), "captions back ON: the cues are written again")

        # THE NO-BOX LOOK (the user, 2026-11-20), picked at the start (state.json captions=no-box): Montserrat Bold, yellow #FFFF00, the black outline, nothing behind the
        # text, one text per caption; the run's look wins over an EDL that asks for another style or for key words in a colour; captions=box and the older 'on' are the box look
        e7 = {"schema": "cc-edl/1", "video": "S07", "kind": "short", "layout": {"mode": "fill", "focus": [0.5, 0.5]},
              "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}, {"id": "s2", "rec_from": 12.0, "rec_to": 14.5}],
              "captions": {"style": "word-box", "highlight_words": ["wild"], "mask_terms": ["damn"], "replace": [["Kai Sinat", "Kai Cenat"]]}}
        o7 = run / "60-outputs" / "S07"
        o7.mkdir(parents=True)
        (o7 / "edl.json").write_text(json.dumps(e7), encoding="utf-8")
        r = cc("state", "--run", run, "set", "captions=no-box", env=env)
        r = cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
        c7 = json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]
        check(r.get("ok") and c7["style"] == "no-box" and c7["look"] == "no-box" and c7["font_file"] == "Montserrat-Bold.otf" and c7["color"] == "#FFFF00" and c7["highlight_words"] == []
              and c7["enabled"] is True and "not used" in c7.get("style_reason", ""),
              "captions=no-box: the no-box look whatever the EDL asks (its style and key words are not used, with the reason): " + str(c7.get("style_reason"))[:160])
        r = cc("captions", "--run", run, "--resolved", o7 / "resolved.json", env=env)
        srt7 = (o7 / "captions.srt").read_text(encoding="utf-8")
        cj7 = json.loads((o7 / "captions.json").read_text(encoding="utf-8"))
        check(r.get("ok") and r.get("look") == "no-box" and r.get("style") == "no-box" and r.get("house_font") is True and str(r.get("font_file", "")).endswith("Montserrat-Bold.otf")
              and r.get("font_covers") is True and (r.get("lines") or {}).get("texts") == r.get("cues") > 0 and "word_box" not in r and cj7["style"] == "no-box" and cj7["look"] == "no-box"
              and "SH*T" in srt7 and "D*MN" in srt7 and "KAI CENAT" in srt7 and r["size"]["vs_guide"] == "inside",
              "captions (no-box): one text per caption in Montserrat Bold (the look's own font), masked, spelled, upper case, the auto size: " + json.dumps({k: r.get(k) for k in ("cues", "lines", "size")})[:300])
        cc("state", "--run", run, "set", "captions=box", env=env)
        cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
        c7b = json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]
        check(c7b["style"] == "word-box" and c7b["look"] == "box" and c7b["font_file"] == "LuckiestGuy-Regular.ttf" and c7b["box"]["pad"] == 0.05, "captions=box: the word-box look in Luckiest Guy, the box padding 0.05")
        e7b = {**e7, "captions": {"style": "no-box"}}
        (o7 / "edl.json").write_text(json.dumps(e7b), encoding="utf-8")
        cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
        c7c = json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]
        check(c7c["style"] == "word-box" and "not used" in c7c.get("style_reason", ""), "a box run whose EDL asks for the no-box style keeps the box look (the user's pick), with the reason")
        (o7 / "edl.json").write_text(json.dumps(e7), encoding="utf-8")
        cc("state", "--run", run, "set", "captions=on", env=env)
        cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
        check(json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]["look"] == "box", "captions=on (a run made before the look could be picked): the box look")

        # THE CAPTION STYLE (the user, 2026-11-20): the start asks captions on/off, then the style: caption_style=luckiest-guy (the box) or montserrat-highlight. A run without
        # the field keeps its historical look; a stored caption_style wins over the older captions value; a typo is refused, never read as another look
        def look_of(*pairs):
            for p in pairs:
                cc("state", "--run", run, "set", p, env=env)
            cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
            return json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]
        cc("state", "--run", run, "set", "caption_style=", env=env)
        check(look_of("captions=on")["look"] == "box", "legacy: captions=on and no caption_style is the Luckiest Guy box")
        check(look_of("captions=no-box")["look"] == "no-box", "legacy: captions=no-box and no caption_style stays the no-box look (its stored pick is kept)")
        r = cc("state", "--run", run, "set", "caption_style=montserrat-higlight", env=env)
        check(r.get("ok") is False and "not a caption style" in str(r.get("error", "")), "a caption_style typo is refused (nothing changed), never read as another look: " + str(r.get("error"))[:100])
        c_h = look_of("captions=on", "caption_style=montserrat-highlight")
        st_now = json.loads((run / "state.json").read_text(encoding="utf-8"))
        check(st_now.get("caption_style") == "montserrat-highlight" and c_h["look"] == "highlight" and c_h["style"] == "word-highlight" and c_h["font_file"] == "Montserrat-Bold.otf"
              and c_h["color"] == "#FFFFFF" and c_h["highlight_color"] == "#FFFF00" and c_h["stroke_width"] == 0.18 and c_h["stroke_color"] == "#000000" and "box" not in c_h
              and c_h["enabled"] is True and "not used" in c_h.get("style_reason", ""),
              "caption_style=montserrat-highlight: Montserrat Bold, white, the spoken word yellow, the outline, no box; the EDL's word-box style is not used: " + str(c_h.get("style_reason"))[:140])
        check(look_of("captions=no-box")["look"] == "highlight", "a stored caption_style wins over the older captions value (no-box)")
        check(look_of("caption_style=Luckiest Guy")["look"] == "box" and json.loads((run / "state.json").read_text(encoding="utf-8"))["caption_style"] == "luckiest-guy",
              "caption_style=Luckiest Guy is stored as luckiest-guy and gives the box look")
        cc("state", "--run", run, "set", "captions=on", "caption_style=montserrat-highlight", env=env)
        e7h = {**e7, "captions": {**e7["captions"], "style": "word-box", "font_family": "Luckiest Guy", "color": "#FF0000", "highlight_color": "#22AAFF"}}
        (o7 / "edl.json").write_text(json.dumps(e7h), encoding="utf-8")
        cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
        c_h2 = json.loads((o7 / "resolved.json").read_text(encoding="utf-8"))["captions"]
        check(c_h2["font_file"] == "Montserrat-Bold.otf" and not c_h2.get("font_family") and c_h2["color"] == "#FFFFFF" and c_h2["highlight_color"] == "#FFFF00"
              and "font_family" in c_h2.get("style_reason", "") and "highlight_color" in c_h2.get("style_reason", ""),
              "the highlight look never takes another font or colour from an EDL (said in style_reason): " + str(c_h2.get("style_reason"))[:200])
        r = cc("captions", "--run", run, "--resolved", o7 / "resolved.json", env=env)
        cj_h = json.loads((o7 / "captions.json").read_text(encoding="utf-8"))
        wh = r.get("word_highlight") or {}
        check(r.get("ok") and r.get("look") == "highlight" and r.get("style") == "word-highlight" and r.get("house_font") is True and r.get("font_names") == ["Montserrat", "Bold"]
              and wh.get("texts", 0) >= r.get("cues", 99) and wh.get("active_color") == "#FFFF00" and wh.get("color") == "#FFFFFF" and r["size"]["vs_guide"] == "inside"
              and "KAI CENAT" in (o7 / "captions.srt").read_text(encoding="utf-8") and (r.get("lexicon") or {}).get("applied") == 1 and cj_h["lexicon"]["applied"][0]["spoken"] == "Kai Sinat",
              "captions (highlight): Montserrat Bold by its own name, a text per moment, the lexicon applied with its record: " + json.dumps({k: r.get(k) for k in ("cues", "word_highlight", "lexicon")})[:400])
        (o7 / "edl.json").write_text(json.dumps(e7), encoding="utf-8")
        cc("state", "--run", run, "set", "captions=on", "caption_style=", env=env)
        cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)

        capcut = shutil.which("capcut")
        busy = "capcut.exe" in subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], capture_output=True, text=True).stdout.lower()
        if capcut and busy:
            print("SKIP capcut-compose/finish: CapCut is running on this PC (compose and finish refuse while it runs, and the app is the user's): close it and run this test again; those checks are NOT verified by this run")
        elif capcut:
            store = tmp / "drafts"
            store.mkdir()
            r = cc("capcut-compose", "--run", run, "--video", "S01", "--name", "cctest", "--store", store, env=env)
            check(r.get("ok") and r.get("video_segments_retargeted") == 5, "capcut-compose: one command, 5 video segments pointed at the real chunk files " + json.dumps(r)[:700])
            c = json.loads((store / "cctest" / "draft_content.json").read_text(encoding="utf-8"))
            vids = c["materials"].get("videos", [])
            check(vids and all(m["path"].endswith(("chunk.mp4", ".mp4")) and "placeholder" not in m["path"] for m in vids), "no video material points at the placeholder")
            check(not (store / "cctest" / "assets" / "video").exists(), "no media file was copied into the draft's assets/video")
            ver = subprocess.run([capcut, "version", str(store / "cctest")], capture_output=True, text=True).stdout
            check('"app_version":"9.7.0"' in ver.replace(" ", "") and '"os":"windows"' in ver.replace(" ", ""),
                  "the composed draft carries the CapCut 9.7 / windows version markers (the empty template), not capcut-cli's bundled 6.5.0 / mac skeleton")
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest", "--video", "S01", env=env)
            check(r.get("ok"), "capcut-finish ok on the composed draft")
            check(any(s.get("step") == "cleanup" for s in r.get("steps", [])) and not (store / "cctest" / ".capcut-cli-history").exists() and not list((store / "cctest").glob("*.bak")),
                  "after a good finish capcut-cli's undo snapshots and the *.bak copies are gone (the word-box look made them 100+ MB per project)")
            meta_p = store / "cctest" / "draft_meta_info.json"
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            pool = [e for g in meta.get("draft_materials", []) for e in g.get("value", [])]

            def pool_exists(e):
                fp = str(e.get("file_Path") or "")
                return (Path(fp) if re.match(r"^[A-Za-z]:[\\/]", fp) else (store / "cctest" / fp)).is_file()
            check(bool(pool) and all(pool_exists(e) for e in pool) and "placeholder" not in meta_p.read_text(encoding="utf-8"),
                  "every file in the draft's media pool exists and the placeholder is not listed (CapCut shows 'Media lost / Link media' for a missing one): " + str([e.get("extra_info") for e in pool]))
            cover = store / "cctest" / "draft_cover.jpg"
            pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "json", str(cover)], capture_output=True, text=True).stdout)["streams"][0]
            check(cover.stat().st_size != 42155 and abs(pr["width"] / pr["height"] - 1080 / 1920) < 0.02,
                  f"the project's cover is a frame of the first clip on the canvas's shape ({pr['width']}x{pr['height']}), not the template's 'Template text' tile")
            c = json.loads((store / "cctest" / "draft_content.json").read_text(encoding="utf-8"))
            texts = c["materials"].get("texts", [])
            cj = json.loads((out / "captions.json").read_text(encoding="utf-8"))
            check(cj.get("style") == "word-box" and len(texts) == cj["word_box"]["texts"] > len(cj["cues"]),
                  f"word-box captions (the default look): one CapCut text per word and state in the draft ({len(texts)} = the planned {cj['word_box']['texts']}, more than the {len(cj['cues'])} cues)")
            tnames = [t["name"] for t in c["tracks"] if t["type"] == "text"]
            check(tnames and all(n.startswith("wordcap-") for n in tnames) and "subtitle" not in tnames, "the caption tracks are the wordcap-* ones and there is no plain subtitle track: " + str(tnames))
            tm = {m["id"]: m for m in texts}
            boxed = [tm[s["material_id"]] for t in c["tracks"] if t["type"] == "text" and t["name"].endswith(("-box", "-box-in")) for s in t["segments"]]
            plain = [tm[s["material_id"]] for t in c["tracks"] if t["type"] == "text" and t["name"].endswith(("-word", "-word-in")) for s in t["segments"]]
            check(boxed and all(m.get("background_color", "").upper() == "#FF7A1A" and float(m.get("background_alpha") or 0) > 0 and abs(float(m.get("background_round_radius") or 0) - 0.3) < 1e-6
                                and float(m.get("background_width")) == 0.05 and float(m.get("background_height")) == 0.05 and float(m.get("background_vertical_offset")) == 0.15
                                and int(m.get("check_flag") or 0) & 16 for m in boxed),
                  f"the spoken word's text is on the preset box: orange #FF7A1A, rounded 0.3, padding 0.05 (a tiny bit smaller again, 2026-11-20), lifted 0.15, the box flag set ({len(boxed)} boxed texts)")
            check(plain and all(not float(m.get("background_alpha") or 0) and int(m.get("check_flag") or 0) & 8 and int(m.get("check_flag") or 0) & 32 and not int(m.get("check_flag") or 0) & 16 for m in plain)
                  and all(str(m.get("font_path", "")).endswith("LuckiestGuy-Regular.ttf") for m in boxed + plain),
                  f"the other words are plain with the thick outline and the shadow ({len(plain)} texts) and every text is in Luckiest Guy, the house font")
            check(all(abs(float(m["border_width"]) - 0.18) < 1e-6 and m.get("has_shadow") is True and json.loads(m["content"])["text"] == json.loads(m["content"])["text"].upper() for m in boxed + plain),
                  "every caption text has Loupe video 04's look: the 0.18 outline, the shadow, upper case")
            ys = {round(float(s["clip"]["transform"]["y"]), 4) for t in c["tracks"] if t["type"] == "text" for s in t["segments"]}
            xs = [float(s["clip"]["transform"]["x"]) for t in c["tracks"] if t["type"] == "text" for s in t["segments"]]
            check(len(ys) == 1 and ys == {round(1 - 2 * 0.66, 4)} and min(xs) < 0 < max(xs) and all(-1 < x < 1 for x in xs), f"every caption text is on one baseline (y {ys}) and the words sit left and right of the centre")
            seg0 = [t for t in c["tracks"] if t["type"] == "video"][0]["segments"][0]
            check(any(k["property_type"] == "KFTypeScaleX" for k in seg0.get("common_keyframes", [])), "the zoom keyframes are on the first clip")
            lint = subprocess.run([capcut, "lint", str(store / "cctest")], capture_output=True, text=True)
            check('"errors":0' in lint.stdout.replace(" ", ""), "capcut lint: 0 errors")
            if sfx_file.is_file():
                check(any(t["type"] == "audio" and t.get("segments") for t in c["tracks"]), "the sound effect is on an audio track")
            # THE SAME PROJECT BY TWO ROUTES (the user, 2026-11-13: the composition for everything): the older split (compose --bare, then finish with one `capcut transition` call and
            # one `import-srt` call per track) against the single composition above. The captions' texts, their styles and places, and the transition on the join must be the same.
            r = cc("capcut-compose", "--run", run, "--video", "S01", "--name", "cctest_bare", "--store", store, "--bare", env=env)
            ic = r.get("composed_in_the_same_call") or {}
            check(r.get("ok") and ic.get("caption_texts") == 0 and ic.get("transitions") == 0, "capcut-compose --bare: only the clips and the sound effects go into the composition " + str(ic))
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_bare", "--video", "S01", env=env)
            check(r.get("ok") and not any(s.get("composed") for s in r.get("steps", [])), "capcut-finish on a bare draft does the transitions and the captions the older way " + str([s.get("step") for s in r.get("steps", [])]))

            def text_rows(path):
                cc_ = json.loads((path / "draft_content.json").read_text(encoding="utf-8"))
                tmat = {m["id"]: m for m in cc_["materials"].get("texts", [])}
                fields = ("font_size", "text_color", "alignment", "has_border", "border_width", "border_color", "border_alpha", "background_color", "background_alpha", "background_style",
                          "background_round_radius", "background_width", "background_height", "background_horizontal_offset", "background_vertical_offset", "background_fill",
                          "check_flag", "font_path", "font_name", "line_max_width", "sub_type")
                rows = []
                for t in cc_["tracks"]:
                    if t["type"] != "text":
                        continue
                    for s in sorted(t["segments"], key=lambda s: int(s["target_timerange"]["start"])):
                        m = tmat[s["material_id"]]
                        rows.append({"track": t["name"], "start": int(s["target_timerange"]["start"]), "dur": int(s["target_timerange"]["duration"]),
                                     "x": round(float(s["clip"]["transform"]["x"]), 4), "y": round(float(s["clip"]["transform"]["y"]), 4), "text": json.loads(m["content"])["text"],
                                     "fields": {k: m.get(k) for k in fields}})
                joins = {}
                trm = {m["id"]: m for m in cc_["materials"].get("transitions", [])}
                for t in cc_["tracks"]:
                    if t["type"] == "video":
                        for s in t["segments"]:
                            for ref in s.get("extra_material_refs") or []:
                                if ref in trm:
                                    joins[int(s["target_timerange"]["start"])] = (trm[ref]["name"], trm[ref]["duration"], trm[ref]["effect_id"])
                return rows, joins
            rows_new, joins_new = text_rows(store / "cctest")
            rows_old, joins_old = text_rows(store / "cctest_bare")
            same_len = len(rows_new) == len(rows_old) > 0
            diffs = []
            for a_, b_ in zip(rows_new, rows_old):
                if a_["track"] != b_["track"] or a_["text"] != b_["text"] or a_["x"] != b_["x"] or a_["y"] != b_["y"] or a_["fields"] != b_["fields"]:
                    diffs.append((a_, b_))
                elif abs(a_["start"] - b_["start"]) > 1500 or abs(a_["dur"] - b_["dur"]) > 3000:     # the older route wrote whole milliseconds (an .srt), the composition microseconds
                    diffs.append((a_["start"], b_["start"], a_["dur"], b_["dur"]))
            check(same_len and not diffs, f"the single composition and the older two-step route make the same {len(rows_new)} caption texts (track, word, place, style, time within a millisecond) " + str(diffs[:1])[:500])
            check(joins_new and joins_new == joins_old, f"the transition on the join is the same by both routes {joins_new}")
            # ONE command for everything: compose + finish + the read-back, one answer
            r = cc("capcut-build", "--run", run, "--video", "S01", "--name", "cctest_build", "--store", store, env=env)
            rb = r.get("read_back") or {}
            check(r.get("ok") and not r.get("problems") and rb.get("main_clips") == 5 and rb.get("texts") == rb.get("composed_caption_texts") == cj["word_box"]["texts"]
                  and (rb.get("lint") or {}).get("errors") == 0 and rb.get("joins_not_contiguous") == 0 and not rb.get("media_missing"),
                  "capcut-build: one command makes the whole project and reads it back (clips, length, joins, texts, media on disk, lint): " + json.dumps({k: r.get(k) for k in ("ok", "problems", "seconds_by_part")}) + json.dumps(rb)[:300])
            check(any(s.get("step") == "captions-word-box" and s.get("composed") for s in (r.get("finish") or {}).get("steps", [])) and any(s.get("step") == "transitions" and s.get("composed") for s in (r.get("finish") or {}).get("steps", [])),
                  "capcut-build: finish did not write the transitions and the caption texts again (the composition had them)")
            # a transition compile refuses (an unknown name that the plan let through): the clips are composed alone, the half-made folder of this very call is removed,
            # and finish writes the rest the older way, with the failure reported
            fj = out / "finish.json"
            keep_finish = fj.read_text(encoding="utf-8")
            f_ = json.loads(keep_finish)
            f_["transitions"] = [{**t, "slug": "no-such-transition", "refused": None} for t in f_["transitions"]]
            fj.write_text(json.dumps(f_), encoding="utf-8")
            r = cc("capcut-compose", "--run", run, "--video", "S01", "--name", "cctest_fb", "--store", store, env=env)
            check(r.get("ok") and r.get("extras_error_then_composed_bare") and (r.get("composed_in_the_same_call") or {}).get("caption_texts") == 0 and (store / "cctest_fb" / "draft_content.json").is_file(),
                  "a transition compile refuses: the clips are composed alone and the answer says why " + str(r.get("extras_error_then_composed_bare"))[:160])
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_fb", "--video", "S01", env=env)
            cfb = json.loads((store / "cctest_fb" / "draft_content.json").read_text(encoding="utf-8"))
            check(r.get("ok") is False and any(s.get("step") == "transitions" and s.get("failed") for s in r.get("steps", [])) and [t["name"] for t in cfb["tracks"] if t["type"] == "text"],
                  "finish after that: the failed transition is reported, the captions are still written the older way")
            fj.write_text(keep_finish, encoding="utf-8")
            # captions.json older than the last edl-check no longer matches the cuts: the build refuses before it changes anything
            cc("edl-check", "--run", run, "--edl", out / "edl.json", env=env)
            r = cc("capcut-build", "--run", run, "--video", "S01", "--name", "cctest_stale", "--store", store, env=env)
            check(r.get("ok") is False and "older than the last edl-check" in str(r.get("error", "")) and not (store / "cctest_stale").exists(),
                  "capcut-build refuses captions that are older than the last edl-check, before it changes anything: " + str(r.get("error"))[:150])
            cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
            # four builds at once (production agents build side by side): each compile writes CapCut's shared project index under the store lock, and no project is lost from it
            import concurrent.futures as cf
            store2 = tmp / "drafts_par"
            store2.mkdir()
            with cf.ThreadPoolExecutor(max_workers=4) as ex:
                futs = [ex.submit(cc, "capcut-compose", "--run", run, "--video", "S01", "--name", f"par{i}", "--store", store2, env=env) for i in range(4)]
                res_par = [f.result() for f in futs]
            # the four calls build the SAME video, so they write the same compose-spec.json at the same moment, and on Windows one atomic replace of a file another process
            # just touched can die with "Access is denied" (seen about once in three runs when the PC was busy, with the real error captured). Real builds are different videos,
            # each in its own folder, so this is a collision of the test's setup, not of the index lock this step is about: a call that died exactly that way is run again, as an agent would.
            for i_, x_ in enumerate(res_par):
                if not x_.get("ok") and "compose-spec.json" in str(x_.get("stderr", "")) and "Access is denied" in str(x_.get("stderr", "")):
                    print(f"note: par{i_} died on the shared compose-spec.json (Windows replace race of this test's setup); run again")
                    res_par[i_] = cc("capcut-compose", "--run", run, "--video", "S01", "--name", f"par{i_}", "--store", store2, env=env)
            idx = json.loads((store2 / "root_meta_info.json").read_text(encoding="utf-8"))
            listed = sorted(Path(str(e.get("draft_fold_path", ""))).name for k, v in idx.items() if isinstance(v, list) for e in v if isinstance(e, dict))
            check(all(x.get("ok") for x in res_par) and listed == [f"par{i}" for i in range(4)],
                  f"four capcut-compose calls at once: all ok and all four projects are in the shared index {listed}")
            # the look is free: any font family and any highlight colour (the agent picks them to match the video), and the old plain look is still there
            def small_edl(video, caps):
                e = {"schema": "cc-edl/1", "video": video, "kind": "short", "layout": {"mode": "fill", "focus": [0.5, 0.5]},
                     "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}, {"id": "s2", "rec_from": 12.0, "rec_to": 14.5}], "captions": caps}
                o = run / "60-outputs" / video
                o.mkdir(parents=True, exist_ok=True)
                (o / "edl.json").write_text(json.dumps(e), encoding="utf-8")
                return o
            o2 = small_edl("S02", {"font_family": "Luckiest Guy", "highlight_color": "#22AAFF", "box": {"round_radius": 0.45}})
            r = cc("edl-check", "--run", run, "--edl", o2 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o2 / "resolved.json", env=env)
            check(r.get("ok") and str(r.get("font_file", "")).endswith("LuckiestGuy-Regular.ttf") and r["size"]["vs_guide"] == "inside" and r.get("highlight_color") == "#22AAFF" and r.get("house_font") is True,
                  "captions: the house font can also be named by its family (looked up on the PC), its size is automatic (the em inside the guide) and the highlight colour is the EDL's " + json.dumps({k: r.get(k) for k in ("font_file", "size")})[:300])
            r = cc("capcut-compose", "--run", run, "--video", "S02", "--name", "cctest5", "--store", store, env=env)
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest5", "--video", "S02", env=env)
            c5 = json.loads((store / "cctest5" / "draft_content.json").read_text(encoding="utf-8"))
            tm5 = {m["id"]: m for m in c5["materials"].get("texts", [])}
            boxed5 = [tm5[s["material_id"]] for t in c5["tracks"] if t["type"] == "text" and t["name"].endswith(("-box", "-box-in")) for s in t["segments"]]
            check(r.get("ok") and boxed5 and all(m["background_color"].upper() == "#22AAFF" and abs(float(m["background_round_radius"]) - 0.45) < 1e-6
                                                  and str(m["font_path"]).endswith("LuckiestGuy-Regular.ttf") for m in boxed5),
                  "a free highlight colour and box radius reach the draft: Luckiest Guy on a blue #22AAFF box with radius 0.45 " + str(r)[:200])
            o3 = small_edl("S03", {"style": "plain"})
            cc("edl-check", "--run", run, "--edl", o3 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o3 / "resolved.json", env=env)
            check(r.get("ok") and r.get("style") == "plain" and "word_box" not in r, "style plain: the old one-text-per-caption look is still available")
            cc("capcut-compose", "--run", run, "--video", "S03", "--name", "cctest6", "--store", store, env=env)
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest6", "--video", "S03", env=env)
            c6 = json.loads((store / "cctest6" / "draft_content.json").read_text(encoding="utf-8"))
            check(r.get("ok") and [t["name"] for t in c6["tracks"] if t["type"] == "text"] == ["subtitle"] and len(c6["materials"]["texts"]) == r_cues(o3), "style plain: one text per caption cue on the subtitle track")
            t6 = {m["id"]: m for m in c6["materials"]["texts"]}
            check(all(str(m.get("font_path", "")).endswith("LuckiestGuy-Regular.ttf") and abs(float(m["border_width"]) - 0.18) < 1e-6 and m.get("has_shadow") is True for m in t6.values()),
                  "the plain look is in the house font too, with the same 0.18 outline and shadow")
            # THE FONT IS FIXED (the user, 2026-11-13): a video that names another font is reported as a fact, and a character the house font cannot draw is known before the build
            o5 = small_edl("S05", {"font_family": "Barlow", "font_style": "Black"})
            cc("edl-check", "--run", run, "--edl", o5 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o5 / "resolved.json", env=env)
            check(r.get("ok") and r.get("house_font") is False and str(r.get("font_file", "")).endswith("Barlow-Black.ttf"), "a video that names another font is reported: house_font false " + json.dumps({k: r.get(k) for k in ("font_file", "house_font")}))
            r = cc("captions", "--run", run, "--resolved", out / "resolved.json", env=env)
            check(r.get("house_font") is True and str(r.get("font_file", "")).endswith("LuckiestGuy-Regular.ttf") and r.get("font_covers") is True, "the default is the house font, Luckiest Guy, and it draws every character of the captions")
            o6 = small_edl("S06", {"replace": [["Hello", "Šnax"]]})
            cc("edl-check", "--run", run, "--edl", o6 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o6 / "resolved.json", env=env)
            check(r.get("house_font") is True and "Š" in (r.get("font_missing_glyphs") or []) and r.get("font_covers") is False, "a character the house font cannot draw (Š) is listed by `captions` before the build " + json.dumps({k: r.get(k) for k in ("font_missing_glyphs", "font_covers")}, ensure_ascii=False))
            r = cc("capcut-build", "--run", run, "--video", "S06", "--name", "cctest_glyph", "--store", store, env=env)
            check(any("cannot draw" in p for p in r.get("problems", [])) and "Š" in ((r.get("caption_font") or {}).get("missing_glyphs") or []),
                  "capcut-build lists the missing character as a problem: " + str(r.get("problems"))[:200])
            # THE NO-BOX LOOK BUILT (the user, 2026-11-20): ONE composition with one `subtitle` track (a yellow text per caption), finish adds only the font and the entrance,
            # the read-back counts the texts; the older route (compose --bare, then one import of the cues) makes the same texts; a second finish never stacks a second track
            cc("state", "--run", run, "set", "captions=no-box", env=env)
            cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o7 / "resolved.json", env=env)
            n7 = r.get("cues")
            r = cc("capcut-build", "--run", run, "--video", "S07", "--name", "cctest_nobox", "--store", store, env=env)
            rb = r.get("read_back") or {}
            check(r.get("ok") and not r.get("problems") and rb.get("text_tracks") == 1 and rb.get("texts") == rb.get("composed_caption_texts") == n7 and (rb.get("lint") or {}).get("errors") == 0
                  and any(s.get("step") == "captions-no-box" and s.get("composed") for s in (r.get("finish") or {}).get("steps", [])),
                  "capcut-build (no-box): one composition with one text per caption, finish adds only the font and the entrance, the read-back agrees: "
                  + json.dumps({k: r.get(k) for k in ("ok", "problems")}) + json.dumps(rb)[:200])
            cn = json.loads((store / "cctest_nobox" / "draft_content.json").read_text(encoding="utf-8"))
            tmn = {m["id"]: m for m in cn["materials"].get("texts", [])}
            segs_n = [s for t in cn["tracks"] if t["type"] == "text" for s in t["segments"]]
            mats_n = [tmn[s["material_id"]] for s in segs_n]
            check([t["name"] for t in cn["tracks"] if t["type"] == "text"] == ["subtitle"] and len(mats_n) == n7
                  and all(str(m.get("text_color", "")).upper() == "#FFFF00" and str(m.get("font_path", "")).endswith("Montserrat-Bold.otf") and abs(float(m["border_width"]) - 0.18) < 1e-6
                          and str(m.get("border_color", "")).upper() == "#000000" and m.get("has_shadow") is True and not float(m.get("background_alpha") or 0)
                          and not int(m.get("check_flag") or 0) & 16 and json.loads(m["content"])["text"] == json.loads(m["content"])["text"].upper() for m in mats_n)
                  and all(abs(float(s["clip"]["transform"]["x"])) < 1e-6 and abs(float(s["clip"]["transform"]["y"]) - round(1 - 2 * 0.66, 4)) < 1e-4 for s in segs_n),
                  f"the no-box texts: one subtitle track, {len(mats_n)} yellow #FFFF00 texts in Montserrat Bold with the 0.18 black outline and the shadow, no box, upper case, centred on the baseline")
            cc("capcut-compose", "--run", run, "--video", "S07", "--name", "cctest_nobox_bare", "--store", store, "--bare", env=env)
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_nobox_bare", "--video", "S07", env=env)
            rows_n, _j = text_rows(store / "cctest_nobox")
            rows_b, _j = text_rows(store / "cctest_nobox_bare")
            diffs_n = [(a_, b_) for a_, b_ in zip(rows_n, rows_b) if a_["track"] != b_["track"] or a_["text"] != b_["text"] or a_["x"] != b_["x"] or a_["y"] != b_["y"]
                       or a_["fields"] != b_["fields"] or abs(a_["start"] - b_["start"]) > 1500 or abs(a_["dur"] - b_["dur"]) > 3000]
            check(r.get("ok") and len(rows_n) == len(rows_b) == n7 and not diffs_n,
                  f"the no-box look by the older route (one import of the cues) makes the same {len(rows_b)} texts as the composition " + str(diffs_n[:1])[:600])
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_nobox_bare", "--video", "S07", env=env)
            cb2 = json.loads((store / "cctest_nobox_bare" / "draft_content.json").read_text(encoding="utf-8"))
            check(r.get("ok") and [t["name"] for t in cb2["tracks"] if t["type"] == "text"] == ["subtitle"] and sum(len(t["segments"]) for t in cb2["tracks"] if t["type"] == "text") == n7,
                  "a second finish on the same draft replaces its caption track, it never stacks a second one " + str([s.get("step") for s in r.get("steps", [])]))
            # THE MONTSERRAT HIGHLIGHT LOOK BUILT (the user, 2026-11-20): ONE composition with the two wordhl tracks, a text per moment holding the whole line, the spoken word's
            # range yellow by capcut-cli's text-ranges; finish adds the font and the outline into every style; the read-back checks every text; the older route matches it
            cc("state", "--run", run, "set", "captions=on", "caption_style=montserrat-highlight", env=env)
            cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
            r = cc("captions", "--run", run, "--resolved", o7 / "resolved.json", env=env)
            n_hl = (r.get("word_highlight") or {}).get("texts")
            cj_hl = json.loads((o7 / "captions.json").read_text(encoding="utf-8"))
            r = cc("capcut-build", "--run", run, "--video", "S07", "--name", "cctest_hl", "--store", store, env=env)
            rb = r.get("read_back") or {}
            hl = rb.get("caption_highlight") or {}
            check(r.get("ok") and not r.get("problems") and rb.get("text_tracks") == 2 and rb.get("texts") == rb.get("composed_caption_texts") == n_hl and (rb.get("lint") or {}).get("errors") == 0
                  and hl.get("texts") == n_hl and hl.get("font_montserrat_bold") == hl.get("outline_black") == hl.get("bold_flag_off") == hl.get("ranges_cover_text") == hl.get("inactive_white") == n_hl
                  and hl.get("one_yellow_word", 0) + hl.get("all_white", 0) == n_hl and hl.get("one_yellow_word", 0) > 0
                  and any(s.get("step") == "captions-word-highlight" and s.get("composed") for s in (r.get("finish") or {}).get("steps", [])),
                  "capcut-build (highlight): one composition, the read-back of the finished draft: every text Montserrat Bold with the black outline, white, at most one yellow word: "
                  + json.dumps({k: r.get(k) for k in ("ok", "problems")}) + json.dumps(hl)[:300])
            ch = json.loads((store / "cctest_hl" / "draft_content.json").read_text(encoding="utf-8"))
            tmh = {m["id"]: m for m in ch["materials"].get("texts", [])}
            ents_h = sorted((e for t in wb.plan_word_highlight({**json.loads((o7 / "finish.json").read_text(encoding="utf-8"))["captions"], "size": 9.8},
                                                                                     cj_hl["cues"], {"width": 1080, "height": 1920, "fps": 30})["tracks"] for e in t["entries"]), key=lambda e: e["start"])
            segs_h = sorted(((t["name"], s) for t in ch["tracks"] if t["type"] == "text" for s in t["segments"]), key=lambda x: int(x[1]["target_timerange"]["start"]))
            bad_h = []
            for (tn, s), e in zip(segs_h, ents_h):
                cont = json.loads(tmh[s["material_id"]]["content"])
                yel = [st_["range"] for st_ in cont["styles"] if [round(v, 2) for v in st_["fill"]["content"]["solid"]["color"]] == [1.0, 1.0, 0.0]]
                want = [[x["start"], x["end"]] for x in e["ranges"]]
                if cont["text"] != e["text"] or yel != want or abs(int(s["target_timerange"]["start"]) / 1e6 - e["start"]) > 0.002 or abs(float(s["clip"]["transform"]["x"])) > 1e-6:
                    bad_h.append((tn, cont["text"], yel, want))
            check(len(segs_h) == len(ents_h) == n_hl and not bad_h and {tn for tn, _s in segs_h} == {"wordhl-in", "wordhl"},
                  f"in the draft: {len(segs_h)} texts on wordhl-in / wordhl, each the whole line centred, its yellow range exactly the word planned for that moment: " + str(bad_h[:2])[:300])
            fin_steps = [s.get("step") for s in (r.get("finish") or {}).get("steps", [])]
            anims_in = [t for t in ch["tracks"] if t["type"] == "text" and t["name"] == "wordhl-in"][0]["segments"]
            anims_on = [t for t in ch["tracks"] if t["type"] == "text" and t["name"] == "wordhl"][0]["segments"]
            amap = {a["id"]: a for a in ch["materials"].get("material_animations", [])}

            def has_in(seg):
                return any(an.get("type") == "in" for ref in seg.get("extra_material_refs") or [] for an in (amap.get(ref) or {}).get("animations", []))
            check(all(has_in(s) for s in anims_in) and not any(has_in(s) for s in anims_on),
                  "the short's 0.1 s fade-in is on each caption's first moment only (wordhl-in), never on a word change (wordhl): " + str(fin_steps))
            cc("capcut-compose", "--run", run, "--video", "S07", "--name", "cctest_hl_bare", "--store", store, "--bare", env=env)
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_hl_bare", "--video", "S07", env=env)
            chb = json.loads((store / "cctest_hl_bare" / "draft_content.json").read_text(encoding="utf-8"))
            tmb = {m["id"]: m for m in chb["materials"].get("texts", [])}
            rows_hc = sorted((int(s["target_timerange"]["start"]) // 1000, json.loads(tmh[s["material_id"]]["content"])["text"], str(wb._yellow_ranges(tmh[s["material_id"]])[1]))
                             for t in ch["tracks"] if t["type"] == "text" for s in t["segments"])
            rows_hb = sorted((int(s["target_timerange"]["start"]) // 1000, json.loads(tmb[s["material_id"]]["content"])["text"], str(wb._yellow_ranges(tmb[s["material_id"]])[1]))
                             for t in chb["tracks"] if t["type"] == "text" for s in t["segments"])
            hb = wb.highlight_facts(store / "cctest_hl_bare")
            check(r.get("ok") and len(rows_hb) == len(rows_hc) == n_hl and [(a_[1], a_[2]) for a_ in rows_hb] == [(a_[1], a_[2]) for a_ in rows_hc]
                  and all(abs(a_[0] - b_[0]) <= 2 for a_, b_ in zip(rows_hb, rows_hc)) and hb["one_yellow_word"] + hb["all_white"] == n_hl and hb["font_montserrat_bold"] == n_hl,
                  "the highlight look by the older route (import, then the ranges written into the draft) makes the same texts and yellow words as the composition: " + json.dumps(hb)[:200])
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest_hl_bare", "--video", "S07", env=env)
            chb2 = json.loads((store / "cctest_hl_bare" / "draft_content.json").read_text(encoding="utf-8"))
            check(r.get("ok") and sum(len(t["segments"]) for t in chb2["tracks"] if t["type"] == "text") == n_hl, "a second finish replaces the highlight tracks, never stacks them")
            # the same look on a LONG video (16:9, the long kind's place and grouping)
            eL = {"schema": "cc-edl/1", "video": "L07", "kind": "long", "layout": {"mode": "native"}, "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}, {"id": "s2", "rec_from": 12.0, "rec_to": 14.5}],
                  "captions": {"replace": [["Kai Sinat", "Kai Cenat"]], "mask_terms": ["damn"]}}
            oL = run / "60-outputs" / "L07"
            oL.mkdir(parents=True, exist_ok=True)
            (oL / "edl.json").write_text(json.dumps(eL), encoding="utf-8")
            cc("edl-check", "--run", run, "--edl", oL / "edl.json", env=env)
            cL = json.loads((oL / "resolved.json").read_text(encoding="utf-8"))["captions"]
            r = cc("captions", "--run", run, "--resolved", oL / "resolved.json", env=env)
            nL = (r.get("word_highlight") or {}).get("texts")
            r = cc("capcut-build", "--run", run, "--video", "L07", "--name", "cctest_hl_long", "--store", store, env=env)
            hlL = (r.get("read_back") or {}).get("caption_highlight") or {}
            cLd = json.loads((store / "cctest_hl_long" / "draft_content.json").read_text(encoding="utf-8"))
            ysL = {round(float(s["clip"]["transform"]["y"]), 4) for t in cLd["tracks"] if t["type"] == "text" for s in t["segments"]}
            check(cL["style"] == "word-highlight" and cL["y_rel"] == 0.88 and cL["max_words"] == 5 and r.get("ok") and not r.get("problems") and hlL.get("texts") == nL
                  and hlL.get("one_yellow_word", 0) + hlL.get("all_white", 0) == nL and ysL == {round(1 - 2 * 0.88, 4)} and cLd["canvas_config"]["width"] == 1920,
                  "the highlight look on a long video (1920x1080, the long kind's baseline 0.88 and 5 words per caption): built, every text read back good: " + json.dumps(hlL)[:200])
            cc("state", "--run", run, "set", "caption_style=", env=env)
            cc("state", "--run", run, "set", "captions=on", env=env)
            # a short that is not 9:16 is listed by capcut-build as a problem too (the user, 2026-11-14: shorts are ALWAYS 9:16), even when the edl-check warning was not heeded
            e7 = {"schema": "cc-edl/1", "video": "S08", "kind": "short", "canvas": {"width": 1920, "height": 1080, "fps": 30}, "layout": {"mode": "fill", "focus": [0.5, 0.5]},
                  "segments": [{"id": "s1", "rec_from": 0.9, "rec_to": 5.0}]}
            o7 = run / "60-outputs" / "S08"
            o7.mkdir(parents=True, exist_ok=True)
            (o7 / "edl.json").write_text(json.dumps(e7), encoding="utf-8")
            cc("edl-check", "--run", run, "--edl", o7 / "edl.json", env=env)
            cc("captions", "--run", run, "--resolved", o7 / "resolved.json", env=env)
            r = cc("capcut-build", "--run", run, "--video", "S08", "--name", "cctest_169", "--store", store, env=env)
            check(r.get("ok") is False and any("9:16" in p for p in r.get("problems", [])), "capcut-build lists a short that is not 9:16 as a problem: " + str(r.get("problems"))[:200])
            # an hour-long video has hundreds of pieces: 150 here; the facts of a chunk are read once, not once per piece (it took 24 s for 300 pieces before)
            big = {"schema": "cc-edl/1", "video": "L02", "kind": "long", "layout": {"mode": "native"},
                   "segments": [{"id": f"b{i}", "rec_from": round((i * 0.15) % 20 + 0.5, 2), "rec_to": round((i * 0.15) % 20 + 1.0, 2)} for i in range(150)]}
            out2 = run / "60-outputs" / "L02"
            out2.mkdir(parents=True)
            (out2 / "edl.json").write_text(json.dumps(big), encoding="utf-8")
            r = cc("edl-check", "--run", run, "--edl", out2 / "edl.json", env=env)
            n = r.get("totals", {}).get("pieces", 0)
            check(r.get("ok") and n >= 150, f"edl-check of a {n}-piece EDL ok")
            r = cc("capcut-compose", "--run", run, "--video", "L02", "--name", "cctest2", "--store", store, env=env)
            check(r.get("ok") and r.get("video_segments_retargeted") == n and r.get("seconds", 99) < 10, f"capcut-compose of {n} pieces: all retargeted, {r.get('seconds')} s (under 10) " + json.dumps(r)[:200])
            # captions OFF at the build: no caption track, no font, no entrance, and no srt is needed; captions ON without an srt is refused
            cc("state", "--run", run, "set", "captions=off", env=env)
            cc("edl-check", "--run", run, "--edl", out2 / "edl.json", env=env)
            r = cc("capcut-compose", "--run", run, "--video", "L02", "--name", "cctest3", "--store", store, env=env)
            check(r.get("ok"), "capcut-compose for the captions-off build ok " + json.dumps(r)[:160])
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest3", "--video", "L02", env=env)
            steps = [s.get("step") for s in r.get("steps", [])]
            c3 = json.loads((store / "cctest3" / "draft_content.json").read_text(encoding="utf-8"))
            check(r.get("ok") and "captions" in steps and not any(str(s).startswith("captions-") for s in steps) and not c3["materials"].get("texts"),
                  "capcut-finish with captions OFF: no srt needed, no caption import, font or entrance, no text in the draft " + str(steps))
            cc("state", "--run", run, "set", "captions=on", env=env)
            r = cc("capcut-compose", "--run", run, "--video", "L02", "--name", "cctest4", "--store", store, env=env)
            r = cc("capcut-finish", "--run", run, "--draft", store / "cctest4", "--video", "L02", env=env)
            check(r.get("ok") is False and "captions are on" in str(r.get("error", "")), "capcut-finish with captions ON and no captions.srt is refused: " + str(r.get("error"))[:120])
            # NOT tested here: opening the composed project in CapCut 9.7 itself (no tool here can); the first real build is that check
        else:
            print("skip capcut-compose/finish (capcut-cli not on PATH)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
