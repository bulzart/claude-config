"""Test of cc_wordbox.py, the word-box caption look (the spoken word on a rounded colour box, one CapCut text per word): the planning only, no CapCut, no media.

    python tests/test_wordbox.py

Checks: the language rule, the lexicon on word sequences (a phrase keeps its place in time, punctuation survives), masking and case, the caption grouping, the frame-grid
moments and the hand-over of a too-short box, the centred line and the tracks (no two texts of a track overlap in time), the split of a line that is too wide, the
automatic size (the em at 4.6 % of the picture's smaller side, the same in any font and on a 16:9 and a 9:16 canvas), the removal of an earlier build's tracks,
and the no-box look (Montserrat Bold, yellow, one text per caption on the subtitle track, split when wider than CapCut's line).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_crypto_loader  # noqa: E402,F401
import cc_edit  # noqa: E402
import cc_wordbox as wb  # noqa: E402

FONT = Path("C:/Users/Bulzart/.claude/analyze-with-loupe/fonts/Montserrat-Bold.otf")
FONT2 = Path("C:/Users/Bulzart/.claude/analyze-with-loupe/fonts/LuckiestGuy-Regular.ttf")


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def W(w, s, e):
    return {"w": w, "s": s, "e": e}


def main():
    # the language rule
    check(wb.language_support("en")[0] and wb.language_support("pt-BR")[0] and wb.language_support(None)[0], "English, Portuguese and an unknown language can take the word box")
    ok, why = wb.language_support("ja")
    check(not ok and "without spaces" in why, "Japanese cannot (written without spaces): " + str(why))
    check(not wb.language_support("ar")[0] and "right to left" in wb.language_support("ar")[1], "Arabic cannot (written right to left)")

    # the lexicon works on word sequences and keeps punctuation and time
    words = [W("Kerrigan,", 1.0, 1.4), W("and", 1.5, 1.6), W("Tess", 1.7, 1.9), W("S", 1.9, 2.0), W("wins.", 2.1, 2.5)]
    caps = {"mask_terms": [], "replace": [["Kerrigan", "karrigan"], ["Tess S", "TeSeS"]], "case": "as-is"}
    toks = wb.tokens_from_words(words, caps, cc_edit._mask_word)
    check([t["w"] for t in toks] == ["karrigan,", "and", "TeSeS", "wins."], "lexicon: a name is spelled right, a two-word name becomes one token, the comma stays: " + str([t["w"] for t in toks]))
    check(abs(toks[2]["s"] - 1.7) < 1e-6 and abs(toks[2]["e"] - 2.0) < 1e-6, "the replaced token holds the span of the words it replaced (1.7 to 2.0)")
    words2 = [W("light", 0.0, 0.3), W("three", 1.0, 1.2), W("case", 1.2, 1.5), W("sequence", 1.5, 2.1)]
    toks2 = wb.tokens_from_words(words2, {"mask_terms": [], "replace": [["three case sequence", "3K sequence"]], "case": "as-is"}, cc_edit._mask_word)
    check([t["w"] for t in toks2] == ["light", "3K", "sequence"] and toks2[1]["s"] == 1.0 and abs(toks2[2]["e"] - 2.1) < 1e-6,
          "lexicon: a three-word phrase becomes two tokens that share its span: " + json.dumps([(t["w"], t["s"], t["e"]) for t in toks2]))
    toks3 = wb.tokens_from_words([W("what", 0, 0.2), W("the", 0.2, 0.3), W("shit", 0.3, 0.6)], {"mask_terms": [], "replace": [], "case": "upper"}, cc_edit._mask_word)
    check([t["w"] for t in toks3] == ["WHAT", "THE", "SH*T"], "masking (the default list, one asterisk) then the case rule: " + str([t["w"] for t in toks3]))
    toks3b = wb.tokens_from_words([W("oh", 0, 0.2), W("heck,", 0.2, 0.6)], {"mask_terms": ["heck"], "replace": [], "case": "upper"}, cc_edit._mask_word)
    check([t["w"] for t in toks3b] == ["OH", "H*CK,"], "a word the video's mask_terms adds is masked the same way and keeps its comma: " + str([t["w"] for t in toks3b]))
    toks4 = wb.tokens_from_words([W("Jaroskate", 0, 1), W("connects", 1, 2), W("the", 2, 2.2), W("headshot.", 2.2, 3)],
                                 {"mask_terms": [], "replace": [["Jaroskate connects the headshot", "Connects the headshot"]]}, cc_edit._mask_word)
    check([t["w"] for t in toks4] == ["Connects", "the", "headshot."], "a phrase that gets shorter keeps its words in order: " + str([t["w"] for t in toks4]))

    # grouping and caption times
    seq = [W(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(7)]
    groups = wb.group_words(seq, {"max_words": 3, "max_chars": 18, "gap_break_s": 0.5})
    check([len(g) for g in groups] == [3, 3, 1], "seven words, three per caption: 3 + 3 + 1")
    times = wb.cue_times(groups, 0.25)
    check(all(times[i][1] <= groups[i + 1][0]["s"] + 1e-9 for i in range(len(times) - 1)) and all(e > s for s, e in times), "caption times never overlap the next caption")
    check([len(g) for g in wb.group_words([W("Wait.", 0, 0.3), W("what", 0.35, 0.6), W("now", 0.6, 0.9)], {"max_words": 5, "max_chars": 40, "gap_break_s": 0.8})] == [1, 2],
          "a sentence end starts a new caption")

    # moments on the frame grid; a word that is spoken too quickly hands its box to the word before
    cue = {"start": 10.0, "end": 11.5, "words": [W("so", 10.0, 10.2), W("fast", 10.25, 10.3), W("here", 10.31, 11.4)]}
    rows = wb.plan_rows([cue], 60)
    r0 = rows[0]
    frame = 1 / 60
    check(all(abs(round(b / frame) * frame - b) < 1e-5 for b in r0["bounds"]) and r0["bounds"][0] == 10.0, "the moments sit on the frame grid and the first starts with the caption")
    check(1 not in r0["boxed"] and 0 in r0["boxed"] and 2 in r0["boxed"], "a 0.06 s word gets no box of its own (boxed words: %s)" % r0["boxed"])

    if not FONT.is_file():
        print("SKIP the line geometry: font not found: " + str(FONT))
    else:
        # automatic size: the em at 4.6 % of the smaller side, whatever the canvas and the font
        s169 = wb.auto_size(str(FONT), 1920, 1080)
        s916 = wb.auto_size(str(FONT), 1080, 1920)
        check(5.3 <= s169 <= 5.9 and 9.6 <= s916 <= 10.4, f"auto size: {s169} on 1920x1080 and {s916} on 1080x1920 (the Loupe videos use 5.5 and 10)")
        f1, f2 = wb.size_facts(str(FONT), s169, 1920, 1080), wb.size_facts(str(FONT), s916, 1080, 1920)
        check(abs(f1["em_pct_of_smaller_side"] - 4.6) < 0.25 and abs(f2["em_pct_of_smaller_side"] - 4.6) < 0.25 and f1["vs_guide"] == "inside",
              f"the em is {f1['em_pct_of_smaller_side']} % and {f2['em_pct_of_smaller_side']} % of the smaller side, inside the 4.0 to 5.0 guide")
        if FONT2.is_file():
            s_lg = wb.auto_size(str(FONT2), 1920, 1080)
            pct = wb.size_facts(str(FONT2), s_lg, 1920, 1080)["em_pct_of_smaller_side"]
            check(abs(pct - 4.6) < 0.25 and s_lg < s169, f"a font with a shorter line needs a smaller size for the same em: size {s_lg} gives {pct} %")
        check(wb.size_facts(str(FONT), 8, 1920, 1080)["vs_guide"] == "larger" and wb.size_facts(str(FONT), 3, 1920, 1080)["vs_guide"] == "smaller", "a size of 8 on 1080p is flagged larger and 3 smaller than the guide (facts, not a stop)")

        # the line, the texts and the tracks
        box = wb.box_params({"highlight_color": "#22AAFF", "box": {"round_radius": 0.4}})
        check(box["color"] == "#22AAFF" and box["round_radius"] == 0.4 and box["pad"] == 0.06 and box["gap_em"] == 0.55 and box["v_offset"] == 0.15,
              "box_params: the colour and the radius are the EDL's, the rest is the house preset (pad 0.06 since the user's 'a little bit smaller' of 2026-11-20, v_offset 0.15, words 0.55 em apart)")
        probe = wb.Probe(str(FONT), s169, 1920, box["gap_em"])
        c1 = {"start": 1.0, "end": 2.0, "words": [W("this", 1.0, 1.2), W("point", 1.3, 1.5), W("immovable.", 1.6, 2.0)]}
        c2 = {"start": 2.0, "end": 3.0, "words": [W("big", 2.0, 2.2), W("play", 2.4, 2.8)]}
        rows = wb.plan_rows([c1, c2], 60)
        groups, geo = wb.plan_texts(rows, probe, 1920)
        summ = wb.plan_summary(groups)
        # cue 1 (3 words): word 0: boxed + plain after = 2, word 1: plain before + boxed + plain after = 3, word 2: plain before + boxed = 2; cue 2 (2 words): 2 + 2
        check(summ["texts"] == 7 + 4 and summ["boxed_texts"] == 3 + 2, "the cues become 11 texts, 5 of them boxed: " + json.dumps(summ))
        for key, ents in groups.items():
            ents = sorted(ents, key=lambda e: e["start"])
            check(all(ents[i]["end"] <= ents[i + 1]["start"] + 1e-6 for i in range(len(ents) - 1)), f"track {wb.track_name(*key)}: no two texts overlap in time")
        xs1 = sorted({(e["x"], e["text"]) for k, v in groups.items() for e in v if e["cue"] == 1})
        wd = probe.widths([w["w"] for w in c1["words"]])
        total = sum(wd) + probe.gap * 2
        first_left = [e for k, v in groups.items() for e in v if e["cue"] == 1 and e["text"] == "this"][0]["x"] * 960 - wd[0] / 2
        last_right = [e for k, v in groups.items() for e in v if e["cue"] == 1 and e["text"] == "immovable."][0]["x"] * 960 + wd[2] / 2
        check(abs(first_left + total / 2) < 1.5 and abs(last_right - total / 2) < 1.5, "the line is centred: left edge %.1f, right edge %.1f, half the line %.1f px" % (first_left, last_right, total / 2))
        check(geo["widest_line_px"] == round(total, 1) or abs(geo["widest_line_px"] - total) < 1.0, "the geometry reports the widest line (%s px)" % geo["widest_line_px"])
        check({wb.track_name(*k) for k in groups} >= {"wordcap-1-box-in", "wordcap-1-word", "wordcap-2-word-in", "wordcap-2-box", "wordcap-3-word-in", "wordcap-3-box"},
              "the tracks are named wordcap-<n>-<box|word>[-in]: " + str(sorted(wb.track_name(*k) for k in groups)))

        # a line that is too wide is split in two, the words kept in order
        wide = {"start": 0.0, "end": 4.0, "words": [W(w, i * 0.4, i * 0.4 + 0.35) for i, w in enumerate("extraordinarily considerable accomplishments demonstrate tremendous perseverance".split())]}
        parts = wb.fit_cues([wide], probe, 700, 0.25)
        flat = [w["w"] for p in parts for w in p["words"]]
        check(len(parts) >= 2 and flat == [w["w"] for w in wide["words"]] and all(probe.line([w["w"] for w in p["words"]]) <= 700 or len(p["words"]) == 1 for p in parts)
              and all(parts[i]["end"] <= parts[i + 1]["start"] + 1e-6 for i in range(len(parts) - 1)), f"a too-wide caption is split ({len(parts)} parts), no word lost or reordered")
        one = wb.fit_cues([c1], probe, 5000, 0.25)
        check(len(one) == 1, "a caption that fits is left alone")

    # THE LOUPE VIDEO 04 LOOK is the default and the font is fixed (the user, 2026-11-13, after the screenshots of our box and of that video's: "always use the same font family")
    for k in ("short", "long"):
        d = cc_edit.DEFAULT_CAPTIONS[k]
        check(d["font_file"] == "LuckiestGuy-Regular.ttf" and d["font_file"] == wb.HOUSE_FONT_FILE and not d.get("font_family") and d["stroke_width"] == 0.18 and d["stroke_color"] == "#000000"
              and d["shadow"] is True and d["case"] == "upper" and d["color"] == "#FFFFFF" and d["box"]["gap_em"] == 0.55 and d["box"]["pad"] == 0.06 and d["box"]["v_offset"] == 0.15
              and d["box"]["round_radius"] == 0.3 and d["highlight_color"] == "#FF7A1A" and d["style"] == "word-box",
              f"the {k} default is Loupe video 04's look: Luckiest Guy, upper case, white with a 0.18 black outline and a shadow, the box 0.3 / 0.06 / 0.15 / 0.55 em")
        # THE NO-BOX LOOK (the user, 2026-11-20): Montserrat Bold, yellow #FFFF00, the black outline, nothing behind the text; the rest is the box look's for the same kind
        n = cc_edit.NO_BOX_CAPTIONS[k]
        check(n["style"] == "no-box" and n["font_file"] == "Montserrat-Bold.otf" == wb.NO_BOX_FONT_FILE and n["color"] == "#FFFF00" == wb.NO_BOX_COLOR and n["stroke_color"] == "#000000"
              and n["stroke_width"] == 0.18 and n["shadow"] is True and n["case"] == "upper" and n["highlight_words"] == [] and not n.get("font_family")
              and all(n[x] == d[x] for x in ("size", "size_em_pct", "y_rel", "max_words", "max_chars", "intro", "intro_s", "min_cue_s", "gap_break_s")),
              f"the {k} no-box default: Montserrat Bold, upper case, yellow #FFFF00 with the 0.18 black outline and the shadow, no key-word colour; size, place, words per caption and entrance as the box look's")
    if FONT2.is_file():
        m1 = wb.font_report(str(FONT2), "TEAM FALCONS WIN, ZERI CKA? Zëri çka? 3K 1v3 m0NESY")
        m2 = wb.font_report(str(FONT2), "Šnax Żyw Ğ")
        check(m1["font_covers"] and m1["font_missing_glyphs"] == [], "Luckiest Guy draws English, digits, punctuation and Albanian (ë ç): " + json.dumps(m1, ensure_ascii=False))
        check(not m2["font_covers"] and {"Š", "Ż", "Ğ"} <= set(m2["font_missing_glyphs"]), "it does not draw Š Ż Ğ: reported before the build as a fact: " + json.dumps(m2, ensure_ascii=False))
        # the box's relation to the font: the line is 1.0 em with the baseline low in it (what the tuned v_offset assumes), unlike a 1.2 em line (Barlow, Montserrat)
        from PIL import ImageFont
        asc, desc = ImageFont.truetype(str(FONT2), 1000).getmetrics()
        check(abs((asc + desc) / 1000 - 1.0) < 0.01, f"Luckiest Guy's line is 1.0 em (ascent {asc}, descent {desc}), the line the box numbers were tuned for")
        # the compose parts carry the outline AND the shadow, and the box with its padding and offset on the boxed texts only
        caps0 = {**cc_edit.DEFAULT_CAPTIONS["long"], "size": 4.5, "y_rel": 0.76}
        pl = wb.plan_word_box(caps0, [c1_ := {"start": 0.0, "end": 1.0, "words": [W("TEAM", 0.0, 0.4), W("WINS", 0.5, 0.9)]}], {"width": 1920, "height": 1080, "fps": 30}, str(FONT2))
        cp = wb.compose_parts(pl, caps0, 5.0)
        ops_box = [o for o in cp["operations"] if "bgColor" in o["style"]]
        ops_plain = [o for o in cp["operations"] if "bgColor" not in o["style"]]
        check(cp["texts"] == len(cp["operations"]) and ops_box and ops_plain and all(o["style"].get("shadow") is True and o["style"]["borderWidth"] == 0.18 and o["style"]["borderColor"] == "#000000" for o in cp["operations"]),
              "every composed text gets the 0.18 black outline and the shadow; " + str(len(ops_box)) + " boxed, " + str(len(ops_plain)) + " plain")
        check(all(o["style"]["bgRoundRadius"] == 0.3 and o["style"]["bgWidth"] == 0.06 and o["style"]["bgHeight"] == 0.06 and o["style"]["bgVOffset"] == 0.15 and o["style"]["bgHOffset"] == 0.0 for o in ops_box),
              "the boxed texts carry radius 0.3, padding 0.06 and the 0.15 vertical offset")
    # the no-box look's texts for the composition: ONE `subtitle` track, a text per caption in the centre on the captions' baseline, yellow, the outline and the shadow, no box
    if FONT.is_file():
        capsn = {**cc_edit.NO_BOX_CAPTIONS["short"], "size": wb.auto_size(str(FONT), 1080, 1920)}
        cues_n = [{"i": 1, "start": 0.0, "end": 0.8, "text": "TEAM WINS"}, {"i": 2, "start": 0.8, "end": 1.6, "text": "LET'S GO"}, {"i": 3, "start": 1.6, "end": 1.6, "text": "EMPTY"}]
        pln = wb.plan_lines(capsn, cues_n, {"width": 1080, "height": 1920, "fps": 30})
        check(pln["error"] is None and len(pln["tracks"]) == 1 and pln["tracks"][0]["track"] == "subtitle" and pln["tracks"][0]["entrance"] and not pln["tracks"][0]["boxed"]
              and [e["text"] for e in pln["tracks"][0]["entries"]] == ["TEAM WINS", "LET'S GO"] and all(e["x"] == 0.0 for e in pln["tracks"][0]["entries"]) and pln["y"] == round(1 - 2 * 0.66, 4),
              "plan_lines: one subtitle track, a text per caption centred on the baseline, a caption of no length left out: " + json.dumps(pln["tracks"])[:200])
        cpn = wb.compose_parts(pln, capsn, 5.0)
        check(cpn["texts"] == 2 and len(cpn["tracks"]) == 1 and all(i["color"] == "#FFFF00" and i["x"] == 0.0 for i in cpn["tracks"][0]["items"])
              and all("bgColor" not in o["style"] and o["style"]["borderWidth"] == 0.18 and o["style"]["borderColor"] == "#000000" and o["style"].get("shadow") is True for o in cpn["operations"]),
              "the no-box compose parts: yellow texts, each with the 0.18 black outline and the shadow, and no box: " + json.dumps(cpn["operations"][:1]))
        mn = wb.font_report(str(FONT), "ŠNAX ŽYW ĞÜL ZËRI ÇKA F*CK")
        check(mn["font_covers"] and not wb.font_report(str(FONT), "ПРИВЕТ")["font_covers"], "Montserrat Bold draws the Slavic and Turkish letters and the asterisk, not Cyrillic (a fact before the build)")
        probe_n = wb.Probe(str(FONT), capsn["size"], 1080, wb.space_em(str(FONT)))
        wide_n = [{"start": 0.0, "end": 3.0, "words": [W(w, i * 0.4, i * 0.4 + 0.35) for i, w in enumerate("UNBELIEVABLE CONGRATULATIONS EVERYBODY TONIGHT".split())]}]
        parts_n = wb.fit_cues(wide_n, probe_n, wb.LINE_FIT * 1080, 0.25)
        check(0.2 < wb.space_em(str(FONT)) < 0.35 and len(parts_n) >= 2 and all(probe_n.line([w["w"] for w in p_["words"]]) <= wb.LINE_FIT * 1080 or len(p_["words"]) == 1 for p_ in parts_n),
              f"a one-text caption wider than {wb.LINE_FIT:.0%} of a 1080 px frame is split ({len(parts_n)} parts), measured with the font's own space")

    # an earlier build's caption tracks are removed with their materials
    content = {"tracks": [{"type": "text", "name": "subtitle", "segments": [{"material_id": "a", "extra_material_refs": ["x"]}]},
                          {"type": "text", "name": "wordcap-1-box-in", "segments": [{"material_id": "b", "extra_material_refs": []}]},
                          {"type": "text", "name": "labels", "segments": [{"material_id": "c", "extra_material_refs": []}]},
                          {"type": "video", "name": "main", "segments": []}],
               "materials": {"texts": [{"id": "a"}, {"id": "b"}, {"id": "c"}], "material_animations": [{"id": "x"}]}}
    n = wb.drop_text_tracks(content)
    check(n == 2 and [t["name"] for t in content["tracks"]] == ["labels", "main"] and [m["id"] for m in content["materials"]["texts"]] == ["c"] and not content["materials"]["material_animations"],
          "drop_text_tracks removes the subtitle and wordcap tracks and their materials, keeps the others")
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
