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
        check(box["color"] == "#22AAFF" and box["round_radius"] == 0.4 and box["pad"] == 0.05 and box["gap_em"] == 0.55 and box["v_offset"] == 0.15,
              "box_params: the colour and the radius are the EDL's, the rest is the house preset (pad 0.05 since the user's second 'only a tiny bit' smaller of 2026-11-20, v_offset 0.15, words 0.55 em apart)")
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
              and d["shadow"] is True and d["case"] == "upper" and d["color"] == "#FFFFFF" and d["box"]["gap_em"] == 0.55 and d["box"]["pad"] == 0.05 and d["box"]["v_offset"] == 0.15
              and d["box"]["round_radius"] == 0.3 and d["highlight_color"] == "#FF7A1A" and d["style"] == "word-box",
              f"the {k} default is Loupe video 04's look: Luckiest Guy, upper case, white with a 0.18 black outline and a shadow, the box 0.3 / 0.05 / 0.15 / 0.55 em")
        # THE MONTSERRAT HIGHLIGHT LOOK (the user, 2026-11-20, a second style next to the box): Montserrat Bold, white, the 0.18 black outline and the shadow, the spoken word yellow,
        # no box; size, place, words per caption and entrance as the box look's for the same kind, so grouping and position are the ones that already work
        h = cc_edit.HIGHLIGHT_CAPTIONS[k]
        check(h["style"] == "word-highlight" and h["font_file"] == "Montserrat-Bold.otf" == wb.HIGHLIGHT_FONT_FILE and h["color"] == "#FFFFFF" and h["highlight_color"] == "#FFFF00"
              and h["stroke_color"] == "#000000" and h["stroke_width"] == 0.18 and h["shadow"] is True and h["case"] == "upper" and h["highlight_words"] == [] and "box" not in h
              and not h.get("font_family") and all(h[x] == d[x] for x in ("size", "size_em_pct", "y_rel", "max_words", "max_chars", "intro", "intro_s", "min_cue_s", "gap_break_s")),
              f"the {k} highlight default: Montserrat Bold, upper case, white with the 0.18 black outline and the shadow, the spoken word #FFFF00, no box; size, place, grouping, entrance as the box look's")
        check(d["font_file"] == "LuckiestGuy-Regular.ttf" and d["style"] == "word-box" and "box" in d, f"the {k} box default is untouched by the highlight look (still Luckiest Guy and its box)")
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
        check(all(o["style"]["bgRoundRadius"] == 0.3 and o["style"]["bgWidth"] == 0.05 and o["style"]["bgHeight"] == 0.05 and o["style"]["bgVOffset"] == 0.15 and o["style"]["bgHOffset"] == 0.0 for o in ops_box),
              "the boxed texts carry radius 0.3, padding 0.05 and the 0.15 vertical offset")
        check(not any(o["op"] == "text-ranges" for o in cp["operations"]), "the box look has no per-range colour (its highlight is the box): no text-ranges operation")
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

    # THE LEXICON'S RULES (the audit of 2026-11-20): punctuation written in a pattern must be there, a capitalised pattern word matches only that spelling, the pattern's
    # punctuation is replaced by the replacement's and never doubled, whole words, the longest pattern first, one pass, ambiguous entries and entries marked review are not applied
    def say(text, t0=0.0):
        out_, t = [], t0
        for x in text.split():
            out_.append(W(x, round(t, 3), round(t + 0.3, 3)))
            t += 0.35
        return out_

    def run_lex(text, pairs, case="upper"):
        toks, log = wb.tokens_with_log(say(text), {"mask_terms": [], "replace": pairs, "case": case}, cc_edit._mask_word)
        return " ".join(t["w"] for t in toks), log
    lex = [["Jack,", "Chat,"], ["Chad", "chat"], ["booby", "Boobie"], ["Oh my goodness, Jack.", "Oh my goodness, chat."]]
    got, log = run_lex("Yeah, that's the heart of Jack of Hearts.", lex)
    check(got == "YEAH, THAT'S THE HEART OF JACK OF HEARTS.", "audit case 1: 'Jack of Hearts' stays (the pattern 'Jack,' needs its comma): " + got)
    got, log = run_lex("Jack, why would they not count the money yet?", lex)
    check(got == "CHAT, WHY WOULD THEY NOT COUNT THE MONEY YET?" and len(log["applied"]) == 1 and log["applied"][0]["spoken"] == "Jack," and log["applied"][0]["shown"] == "Chat,",
          "audit case 2: 'Jack, why' becomes 'CHAT, WHY' with ONE comma, and the record says what changed: " + got + " " + json.dumps(log["applied"])[:160])
    got, _ = run_lex("Oh my goodness, Jack. This stuff's about to", lex)
    check(got == "OH MY GOODNESS, CHAT. THIS STUFF'S ABOUT TO", "a phrase pattern with its own punctuation: 'Jack.' becomes 'chat.', never 'CHAT,.': " + got)
    got, log = run_lex("Look at the boobies on that statue", [["boobies", "Boobie's"]])
    check(got == "LOOK AT THE BOOBIE'S ON THAT STATUE" and len(log["applied"]) == 1,
          "a plain pair is applied as written (the lexicon's author decides; the record shows it in context): " + got + " | " + log["applied"][0]["context"])
    got, log = run_lex("Look at the boobies on that statue", [{"from": "boobies", "to": "Boobie's", "review": True}])
    check(got == "LOOK AT THE BOOBIES ON THAT STATUE" and not log["applied"] and len(log["held"]) == 1 and "[boobies]" in log["held"][0]["context"],
          "audit case 3: an entry marked review is NOT applied; the place it would change is listed for the builder: " + got + " " + json.dumps(log["held"])[:160])
    got, log = run_lex("Jack of Hearts, and Jack, why", [{"from": "Jack", "to": "chat", "not_before": ["of hearts"]}])
    check(got == "JACK OF HEARTS, AND CHAT, WHY", "a context guard: 'Jack' becomes 'chat' except before 'of Hearts' (and keeps Whisper's comma): " + got)
    got, log = run_lex("Jack, Jack, Jack, no no no", [["Jack,", "Chat,"], ["no", "nah"], ["nah", "never"]])
    check(got == "CHAT, CHAT, CHAT, NAH NAH NAH", "repeated words are each replaced once, and a replacement is never replaced again (no 'never'): " + got)
    got, _ = run_lex("Chad Chad, chad CHAD", [["Chad", "chat"]], case="as-is")
    check(got == "chat chat, chat chat", "a pattern matches in any case, as the old matcher did (Chad, chad, CHAD); the comma stays: " + got)
    got, _ = run_lex("Chad Chad, chad CHAD", [{"from": "Chad", "to": "chat", "exact_case": True}], case="as-is")
    check(got == "chat chat, chad CHAD", "exact_case: the pattern matches only the spelling as written (Chad), not chad or CHAD: " + got)
    got, _ = run_lex("Just hurry free state stuff. Hurry free state?", [["Hurry free state", "Furry-Free State"]], case="as-is")
    check(got == "Just Furry-Free State stuff. Furry-Free State?", "the caseoh miss: a pattern written with a capital also fixes the lower-case words (hurry free state): " + got)
    got, log = run_lex("Chad chad", [["Chad", "chat"], ["chad", "Chad"]], case="as-is")
    check(got == "chat Chad" and not log["problems"], "two entries that differ only in case are not ambiguous: the one written in the word's own case wins: " + got)
    got, _ = run_lex("booby Booby. BOOBY?", [["booby", "Boobie"]], case="as-is")
    check(got == "Boobie Boobie. Boobie?", "a lower-case pattern word matches in any case, the punctuation Whisper wrote stays: " + got)
    got, _ = run_lex("I can't, I can do it", [["can", "could"]])
    check(got == "I CAN'T, I COULD DO IT", "whole words only: a contraction (can't) is not touched by a pair for 'can': " + got)
    got, _ = run_lex("he's the dispatcher's guy", [["dispatcher's", "dispatcher's"], ["he's", "he is"]])
    check(got == "HE IS THE DISPATCHER'S GUY", "a contraction in a pattern is matched with its apostrophe: " + got)
    got, log = run_lex("Jack of Hearts and jack", [{"from": "Jack", "to": "chat", "exact_case": True}, ["Jack of Hearts", "Jack of Hearts"]], case="as-is")
    check(got == "Jack of Hearts and jack", "the longest pattern wins (Jack of Hearts), and an exact_case 'Jack' does not reach the lower-case 'jack': " + got)
    got, log = run_lex("Jack of Hearts and jack", [["Jack", "chat"], ["Jack of Hearts", "Jack of Hearts"]], case="as-is")
    check(got == "Jack of Hearts and chat", "without exact_case the lower-case 'jack' is matched too (the longest pattern still keeps Jack of Hearts): " + got)
    got, log = run_lex("hey Kso what's up", [["Kso", "CaseOh"], ["Kso", "K-So"]])
    check(got == "HEY KSO WHAT'S UP" and log["problems"] and "ambiguous" in log["problems"][0]["problem"],
          "two entries with the same pattern and different replacements are ambiguous: neither is applied, the problem is reported: " + json.dumps(log["problems"])[:160])
    got, _ = run_lex("what the frick", [["frick", "fuck"]])
    check(got == "WHAT THE F*CK", "a word a replacement brings in is masked like any spoken word: " + got)
    got, log = run_lex("hello there", [["", "x"], "nonsense", ["...", "y"]])
    check(got == "HELLO THERE" and len(log["problems"]) == 3, "entries that cannot be used are listed as problems, never applied: " + json.dumps(log["problems"])[:200])

    # THE HIGHLIGHT LOOK'S MOMENTS: exactly one word yellow while it is spoken, the others white, every word white in a pause, on the frame grid
    c_hl = {"start": 0.0, "end": 1.40, "words": [W("THAT'S", 0.00, 0.30), W("ACTUALLY", 0.32, 0.80), W("CRAZY", 0.85, 1.30)]}
    st_ = wb.highlight_states(c_hl, 30)
    frame = 1 / 30
    check([s[2] for s in st_] == [0, 1, 2] and st_[0][0] == 0.0 and abs(st_[-1][1] - 1.4) < 1e-6 and all(abs(st_[i][1] - st_[i + 1][0]) < 1e-6 for i in range(len(st_) - 1))
          and all(abs(round(b / frame) * frame - b) < 1e-5 for s in st_ for b in s[:2]),
          "THAT'S ACTUALLY CRAZY: three moments, one word yellow in each, in order, back to back on the frame grid: " + json.dumps(st_))
    check(abs(st_[1][0] - round(0.32 / frame) * frame) < 1e-6 and abs(st_[2][0] - round(0.85 / frame) * frame) < 1e-6,
          "each word turns yellow on its own start (Whisper's word time, snapped to the frame)")
    st_p = wb.highlight_states({"start": 0.0, "end": 1.4, "words": [W("WAIT", 0.0, 0.3), W("WHAT", 1.0, 1.3)]}, 30)
    check([s[2] for s in st_p] == [0, None, 1] and abs(st_p[1][0] - 0.3) < 1e-6 and abs(st_p[1][1] - 1.0) < 1e-6,
          "a pause longer than hold_s inside a caption: every word white from the end of WAIT to the start of WHAT: " + json.dumps(st_p))
    st_h = wb.highlight_states({"start": 0.0, "end": 0.9, "words": [W("SO", 0.0, 0.3), W("FAST", 0.45, 0.9)]}, 30)
    check([s[2] for s in st_h] == [0, 1] and abs(st_h[0][1] - round(0.45 / frame) * frame) < 1e-5,
          "a short silence (0.15 s, under hold_s) keeps SO yellow until FAST starts: no white flicker: " + json.dumps(st_h))
    st_q = wb.highlight_states({"start": 0.0, "end": 0.8, "words": [W("A", 0.0, 0.3), W("B", 0.3, 0.32), W("C", 0.32, 0.8)]}, 30)
    check([s[2] for s in st_q] == [0, 2] and all(s[1] - s[0] >= 2 * frame - 1e-6 for s in st_q),
          "a word spoken for one frame (B) hands its moment to the word before: no one-frame yellow flicker: " + json.dumps(st_q))
    st_e = wb.highlight_states({"start": 0.0, "end": 2.0, "words": [W("END", 0.0, 0.4)]}, 30)
    check([s[2] for s in st_e] == [0, None] and abs(st_e[0][1] - 0.4) < 1e-6, "a caption held on screen after its last word: the word goes white when it is no longer spoken: " + json.dumps(st_e))
    check(wb.utf16_len("a\U0001F600b") == 4 and wb.utf16_len("ŽELJKO") == 6, "ranges are counted in UTF-16 units, as CapCut counts them (an emoji is two)")
    capsh = {**cc_edit.HIGHLIGHT_CAPTIONS["short"], "size": 9.8}
    cues_h = [{"i": 1, "start": 0.0, "end": 1.4, "text": "THAT'S ACTUALLY CRAZY", "words": c_hl["words"]},
              {"i": 2, "start": 1.4, "end": 2.5, "text": "WAIT. WHAT", "words": [W("WAIT.", 1.4, 1.7), W("WHAT", 2.2, 2.5)]}]
    ph = wb.plan_word_highlight(capsh, cues_h, {"width": 1080, "height": 1920, "fps": 30})
    ents = sorted((e for t in ph["tracks"] for e in t["entries"]), key=lambda e: e["start"])
    names = [t["track"] for t in ph["tracks"]]
    check(names == ["wordhl-in", "wordhl"] and [t["entrance"] for t in ph["tracks"]] == [True, False] and ph["error"] is None,
          "two tracks: wordhl-in (each caption's first moment, the only place an entrance goes) and wordhl (the rest): " + str(names))
    c1_ents = [e for e in ents if e["cue"] == 1]
    check([e["text"] for e in c1_ents] == ["THAT'S ACTUALLY CRAZY"] * 3 and [e["word"] for e in c1_ents] == ["THAT'S", "ACTUALLY", "CRAZY"]
          and [e["ranges"][0]["start"] for e in c1_ents] == [0, 7, 16] and [e["ranges"][0]["end"] for e in c1_ents] == [6, 15, 21]
          and all(e["ranges"][0]["font_color"] == "#FFFF00" and len(e["ranges"]) == 1 and e["x"] == 0.0 for e in c1_ents),
          "every moment holds the WHOLE line (same text, so nothing moves) and exactly the spoken word's range in yellow: " + json.dumps([(e["word"], e["ranges"]) for e in c1_ents]))
    c2_ents = [e for e in ents if e["cue"] == 2]
    check([e["word"] for e in c2_ents] == ["WAIT.", None, "WHAT"] and c2_ents[1]["ranges"] == [] and c2_ents[0]["ranges"][0]["end"] - c2_ents[0]["ranges"][0]["start"] == 5,
          "a pause in a caption is a moment with no yellow range; a word's own punctuation is lit with it (WAIT.): " + json.dumps([(e["word"], e["ranges"]) for e in c2_ents]))
    for t in ph["tracks"]:
        es = sorted(t["entries"], key=lambda e: e["start"])
        check(all(es[i]["end"] <= es[i + 1]["start"] + 1e-6 for i in range(len(es) - 1)), f"track {t['track']}: no two texts overlap in time")
    check(ph["states"]["texts"] == 6 and ph["states"]["pauses_all_white"] == 1 and ph["states"]["words_too_quick_to_light"] == 0, "the plan's facts: " + json.dumps(ph["states"]))
    cph = wb.compose_parts(ph, capsh, 10.0)
    rng_ops = [o for o in cph["operations"] if o["op"] == "text-ranges"]
    sty_ops = [o for o in cph["operations"] if o["op"] == "text-style"]
    check(cph["texts"] == 6 and len(rng_ops) == 5 and len(sty_ops) == 6 and all(i["color"] == "#FFFFFF" and i["x"] == 0.0 for t in cph["tracks"] for i in t["items"])
          and all(o["style"]["borderWidth"] == 0.18 and o["style"]["borderColor"] == "#000000" and o["style"].get("shadow") is True and "bgColor" not in o["style"] for o in sty_ops)
          and all(len(o["ranges"]) == 1 and o["ranges"][0]["font_color"] == "#FFFF00" for o in rng_ops),
          "the compose parts: white texts with the 0.18 black outline and the shadow, no box, and one text-ranges operation (the yellow word) on every moment but the pause")
    mat = {"content": json.dumps({"text": "THAT'S ACTUALLY CRAZY", "styles": [{"range": [0, 21], "size": 9.8, "bold": False, "fill": {"alpha": 1, "content": {"render_type": "solid", "solid": {"alpha": 1, "color": [1, 1, 1]}}},
                                                                             "font": {"id": "", "path": "x/Montserrat-Bold.otf"}, "strokes": [{"width": 0.18, "content": {"solid": {"color": [0, 0, 0]}}}]}]})}
    wb.set_text_ranges(mat, [{"start": 7, "end": 15, "font_color": "#FFFF00"}])
    sts = json.loads(mat["content"])["styles"]
    check([s["range"] for s in sts] == [[0, 7], [7, 15], [15, 21]] and [s["fill"]["content"]["solid"]["color"] for s in sts] == [[1, 1, 1], [1.0, 1.0, 0.0], [1, 1, 1]]
          and all(s["font"]["path"].endswith("Montserrat-Bold.otf") and s["strokes"] for s in sts) and wb._yellow_ranges(mat)[1] == [(7, 15)],
          "set_text_ranges (the route for a draft the composition did not caption): white, yellow, white, the font and the outline kept in every style")
    import tempfile
    dtmp = Path(tempfile.mkdtemp(prefix="wb-hl-"))
    try:
        good = dict(mat, id="m1", font_path="x/Montserrat-Bold.otf")
        bad_ = {"id": "m2", "font_path": "x/Montserrat-Bold.otf", "content": json.dumps({"text": "AB CD", "styles": [
            {"range": [0, 2], "bold": True, "fill": {"content": {"solid": {"color": [1, 1, 0]}}}, "font": {"path": "x/Montserrat-Bold.otf"}, "strokes": [{"width": 0.18, "content": {"solid": {"color": [0, 0, 0]}}}]},
            {"range": [2, 5], "fill": {"content": {"solid": {"color": [1, 1, 0]}}}, "font": {"path": "x/Montserrat-Bold.otf"}, "strokes": [{"width": 0.18, "content": {"solid": {"color": [0, 0, 0]}}}]}]})}
        (dtmp / "draft_content.json").write_text(json.dumps({"tracks": [{"type": "text", "name": "wordhl-in", "segments": [{"material_id": "m1", "target_timerange": {"start": 0, "duration": 1}},
                                                                                                                         {"material_id": "m2", "target_timerange": {"start": 1, "duration": 1}}]}],
                                                              "materials": {"texts": [good, bad_]}}), encoding="utf-8")
        hf = wb.highlight_facts(dtmp)
        check(hf["texts"] == 2 and hf["font_montserrat_bold"] == 2 and hf["outline_black"] == 2 and hf["one_yellow_word"] == 1 and hf["bold_flag_off"] == 1 and len(hf["bad"]) == 1,
              "highlight_facts reads a finished draft back: the good text passes, the one with two yellow styles and a faux bold is listed: " + json.dumps(hf)[:300])
    finally:
        import shutil
        shutil.rmtree(dtmp, ignore_errors=True)
    if FONT.is_file():
        from PIL import ImageFont
        fam, sty = ImageFont.truetype(str(FONT), 20).getname()
        check((fam, sty) == ("Montserrat", "Bold"), f"the highlight look's font file is Montserrat Bold by its own name table: {fam} {sty}")

    # an earlier build's caption tracks are removed with their materials
    content = {"tracks": [{"type": "text", "name": "subtitle", "segments": [{"material_id": "a", "extra_material_refs": ["x"]}]},
                          {"type": "text", "name": "wordcap-1-box-in", "segments": [{"material_id": "b", "extra_material_refs": []}]},
                          {"type": "text", "name": "wordhl-in", "segments": [{"material_id": "d", "extra_material_refs": []}]},
                          {"type": "text", "name": "labels", "segments": [{"material_id": "c", "extra_material_refs": []}]},
                          {"type": "video", "name": "main", "segments": []}],
               "materials": {"texts": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}], "material_animations": [{"id": "x"}]}}
    n = wb.drop_text_tracks(content)
    check(n == 3 and [t["name"] for t in content["tracks"]] == ["labels", "main"] and [m["id"] for m in content["materials"]["texts"]] == ["c"] and not content["materials"]["material_animations"],
          "drop_text_tracks removes the subtitle, wordcap and wordhl tracks and their materials, keeps the others")
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
