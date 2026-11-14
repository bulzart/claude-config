"""Test of the caption masks: profanity and slurs are always typed with ONE asterisk (the user, 2026-11-14: "fuck, faggot, pedo, shit, gay and more ... f*ck, f*ggot or similarly").

    python tests/test_masks.py

Checks the data file (data/caption-masks.json: the user's list, the code holds no word), the style (the asterisk takes the first vowel after the first letter), the forms and compounds
that come with a stem, the words that must stay as they are (class, pass, therapist, torpedo, Scunthorpe, Dickens ...), punctuation and case, the per-video `mask_terms`, the tally
and that the house font can draw the asterisk. No CapCut, no media.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import cc_edit  # noqa: E402
import cc_wordbox as wb  # noqa: E402


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        check.failed += 1


check.failed = 0


def main():
    data = json.loads(cc_edit.MASKS_FILE.read_text(encoding="utf-8"))
    check(isinstance(data.get("anywhere"), list) and isinstance(data.get("whole_word"), list), "data/caption-masks.json holds the lists `anywhere` and `whole_word`")
    anywhere, whole = cc_edit.mask_lists()
    check(len(anywhere) >= 15 and len(whole) >= 30, f"the default list is real: {len(anywhere)} stems, {len(whole)} whole words")
    check(all(w in str(data["anywhere"]) for w in ("fuck", "shit", "faggot")) and all(w in whole for w in ("gay", "pedo")),
          "the user's own words are on the list: fuck, shit, faggot (anywhere), gay, pedo (whole word)")

    star = cc_edit._star
    cases = [("fuck", "f*ck"), ("shit", "sh*t"), ("faggot", "f*ggot"), ("pedo", "p*do"), ("gay", "g*y"), ("bitch", "b*tch"), ("ass", "a*s"), ("dyke", "d*ke"), ("tranny", "tr*nny"),
             ("Fuck", "F*ck"), ("GAY", "G*Y")]
    for src, want in cases:
        check(star(src) == want, f"style: {src} -> {star(src)} (want {want})")

    mw = lambda w, terms=frozenset(): cc_edit._mask_word(w, set(terms))   # noqa: E731
    masked = [("fuck", "f*ck"), ("fucking", "f*cking"), ("Fucking", "F*cking"), ("fuckin'", "f*ckin'"), ("motherfucker,", "motherf*cker,"), ("clusterfuck", "clusterf*ck"),
              ("shit.", "sh*t."), ("bullshit", "bullsh*t"), ("shitty", "sh*tty"), ("bitches", "b*tches"), ("faggot", "f*ggot"), ("faggots!", "f*ggots!"),
              ("nigga", "n*gga"), ("niggas", "n*ggas"), ("pussy", "p*ssy"), ("whore", "wh*re"), ("pedo", "p*do"), ("pedophile", "p*dophile"), ("Paedophiles", "P*edophiles"),
              ("gay", "g*y"), ("Gay,", "G*y,"), ("gays", "g*ys"), ("ass", "a*s"), ("ass?", "a*s?"), ("asshole", "a*shole"), ("badass", "bada*s"), ("dumbass", "dumba*s"),
              ("dick", "d*ck"), ("dickhead", "d*ckhead"), ("cocksucker", "c*cksucker"), ("cunt", "c*nt"), ("rape", "r*pe"), ("rapist", "r*pist"), ("retarded", "r*tarded"),
              ("(shit)", "(sh*t)"), ('"fuck"', '"f*ck"')]
    for src, want in masked:
        check(mw(src) == want, f"masked: {src} -> {mw(src)} (want {want})")
    kept = ["class", "pass", "assume", "assist", "bass", "glass", "passion", "assassin", "torpedo", "pedometer", "Dickens", "Dickinson", "Gayle", "gaylord", "cockpit", "peacock",
            "therapist", "Scunthorpe", "raccoon", "spicy", "hello", "Kai", "Cenat", "kill", "die", "hell", "damn", "crap", "the", "retardant", "grape", "drape", "shiitake", "a", "I"]
    for w in kept:
        check(mw(w) == w, f"kept as spoken: {w} -> {mw(w)}")
    check(mw("f**king") == "f**king" and mw("") == "" and mw("...") == "...", "an already masked word, an empty token and bare punctuation are left alone")

    check(mw("heck", {"heck"}) == "h*ck" and mw("Heck!", {"heck"}) == "H*ck!" and mw("heck") == "heck", "a word the video's mask_terms adds is masked the same way, only for that video")
    check(mw("x", {"x"}) == "x", "a one-letter term is never masked")

    words = [{"w": "What", "s": 0, "e": 1}, {"w": "the", "s": 1, "e": 2}, {"w": "fuck,", "s": 2, "e": 3}, {"w": "this", "s": 3, "e": 4}, {"w": "shit.", "s": 4, "e": 5},
             {"w": "Fucking", "s": 5, "e": 6}, {"w": "heck", "s": 6, "e": 7}]
    tally = cc_edit._masked_tally(words, {"mask_terms": ["heck"]})
    check(tally == {"f*ck": 1, "f*cking": 1, "h*ck": 1, "sh*t": 1}, "the tally says what was masked, as typed, with counts: " + json.dumps(tally))
    caps = {"mask_terms": [], "replace": [], "case": "upper"}
    toks = wb.tokens_from_words(words, caps, cc_edit._mask_word)
    check([t["w"] for t in toks] == ["WHAT", "THE", "F*CK,", "THIS", "SH*T.", "F*CKING", "HECK"], "the word-box tokens: masked, then upper case: " + str([t["w"] for t in toks]))

    ff = cc_edit.caption_font(dict(cc_edit._HOUSE))
    rep = wb.font_report(ff, "F*CK SH*T F*GGOT P*DO G*Y B*TCH A*S")
    check(rep.get("font_covers") is True and not rep.get("font_missing_glyphs"), "the house font (Luckiest Guy) can draw the asterisk: " + json.dumps(rep))

    # the list is loud when it is missing or broken (captions must never go out unmasked by accident)
    real = cc_edit.MASKS_FILE
    try:
        cc_edit.MASKS_FILE = real.with_name("no-such-mask-list.json")
        try:
            cc_edit.mask_lists()
            check(False, "a missing list raises")
        except ValueError as e:
            check("missing" in str(e), "a missing list raises a clear error: " + str(e)[:80])
    finally:
        cc_edit.MASKS_FILE = real
    print("FAILED: %d" % check.failed if check.failed else "ALL PASSED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
