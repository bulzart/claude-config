"""Captions for a finished narration: the words the viewer hears, shown as they are spoken, in the look the user picks
at the start of the run (state.json: `captions` on|off and `caption_style`):

- `luckiest-guy` (Luckiest Guy word box): Luckiest Guy, capitals, white with a black outline and a shadow, three words a
  caption, the spoken word on a rounded colour box. CapCut draws a box behind a whole text only, so each word is its
  own text at its place on the centred line (tracks `caption-box-N-box` / `caption-box-N-word`).
- `montserrat-highlight` (Montserrat Bold word highlight): Montserrat Bold, white with a black outline, no box, no
  shadow: each caption line is one CapCut text per moment holding the whole line (track `caption-hl`), the word being
  spoken in yellow (#FFFF00) and every other word white; between words, in a pause, every word is white.

The words, their spelling and their order are the script's canonical text (tags removed; the pronunciation list never
reaches a caption). Their times are Whisper medium's word times of the recorded narration (narration-measure keeps
them in line-times.json), moved onto the edit's timeline by the holds retime-shots inserted. A word whose time Whisper
did not give (rare: a line found only on a second listen) is placed between its timed neighbours by its length, and
counted. Nothing here judges how a video should look: the look is the user's pick, its numbers are fixed; the box
colour of the word box is the agents' choice for each video, with its reason.

The word-box functions below marked "copied" are copied unchanged from the user's other toolkit's word-box builder
(awl.py: chunk_words_fill, _word_box_plan, _word_box_segments, _capcut_em_px, _wb_norm, _upper_for, _drop_text_tracks),
so the Luckiest Guy look and its timing behave exactly as there. One difference, on the Static Studio side only: the words
reach chunk_words_fill one sentence at a time (word_box_cues), so a caption never runs across a sentence end (the user,
2026-11-24: a real export showed "SPIES. NOT"); the copied function itself is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from pathlib import Path

CAPTION_STYLES = ('luckiest-guy', 'montserrat-highlight')
TRACK_PREFIX = 'caption-'
HIGHLIGHT_TRACK = 'caption-hl'
BOX_TRACK_PREFIX = 'caption-box-'
FONTS_DIR = Path(__file__).resolve().parent.parent / 'fonts'
CAPCUT_FONT_PER_SIZE = 0.00575     # CapCut's line height per size unit and canvas pixel (measured; capcut_tools.py has it too)
EM_SHARE = 0.046                   # a caption's em: 4.6 % of the frame's smaller side (small/normal on a phone)
Y_REL = {'landscape': 0.85, 'portrait': 0.75, 'square': 0.82}   # the caption line's centre, from the top
DEFAULT_FPS = 30
YELLOW = '#FFFF00'

LOOKS = {
    'luckiest-guy': {
        'label': 'Luckiest Guy word box', 'font_file': 'LuckiestGuy-Regular.ttf', 'font_name': ['Luckiest Guy', 'Regular'],
        'upper': True, 'fill': '#FFFFFF', 'stroke_color': '#000000', 'stroke_width': 0.18, 'shadow': True,
        'box': {'alpha': 1.0, 'round_radius': 0.3, 'style': 0, 'pad': 0.05, 'v_offset': 0.15},
        'gap_em': 0.55, 'words': 3, 'min_words': 3, 'break_gap_s': 0.8, 'max_line_width': 0.92},
    'montserrat-highlight': {
        'label': 'Montserrat Bold word highlight', 'font_file': 'Montserrat-Bold.otf', 'font_name': ['Montserrat', 'Bold'],
        'upper': False, 'fill': '#FFFFFF', 'active': YELLOW, 'stroke_color': '#000000', 'stroke_width': 0.18,
        'shadow': False, 'max_words': 6, 'break_gap_s': 0.6, 'max_line_width': 0.80,
        # a gap between two words shorter than bridge_s is not a pause the eye can see: the next word takes over at once
        # (no white flash); a longer one is a pause and every word turns white. Every word is lit for min_lit_frames.
        'bridge_s': 0.12, 'tail_s': 0.5, 'min_lit_frames': 2}}

SENTENCE_END = re.compile(r'[.!?…。！？]["”’\')\]]*$')
# a full stop that ends an abbreviation or an initial ends no sentence ("Mr. Pujol", "J. R. R. Tolkien")
NOT_SENTENCE_END = re.compile(r"(mr|mrs|ms|dr|prof|st|jr|sr|vs|gen|col|lt|sgt|capt|e\.g|i\.e|u\.s|u\.k|[a-z])\.",
                              re.I)


def ends_sentence(word) -> bool:
    """The word closes a sentence: it ends in . ! ? (or the full-width forms), and is not an abbreviation or an initial."""
    w = str(word or '')
    if not SENTENCE_END.search(w):
        return False
    core = w.rstrip('"”’\')]')
    return not NOT_SENTENCE_END.fullmatch(core)


def _cut_to_fit(cues: list, words: list, fits, info=None) -> list:
    """A cue wider than the frame allows is cut into nearly equal runs of its words that each fit (one word a run at
    the least): a sentence's tail joined to the cue before it must still be readable on one line."""
    sep = "" if _unspaced(info) else " "
    out, i = [], 0
    for c in cues:
        n = len(_tokens(c["text"], info))
        ws = words[i:i + n]
        i += n
        if n < 2 or fits(c["text"]) or sep.join(w["w"] for w in ws) != c["text"]:
            out.append(c)
            continue
        k = 2
        while True:
            size = math.ceil(n / k)
            runs = [ws[j:j + size] for j in range(0, n, size)]
            if size == 1 or all(fits(sep.join(w["w"] for w in r)) for r in runs):
                break
            k += 1
        for j, r in enumerate(runs):
            start = round(r[0]["s"], 2)
            end = c["end"] if j == len(runs) - 1 else min(round(r[-1]["e"] + 0.05, 2), round(runs[j + 1][0]["s"], 2))
            out.append({**c, "start": start, "end": round(max(end, start + 0.01), 2), "text": sep.join(w["w"] for w in r)})
    return out


def word_box_fits(font_file, size, W, gap_em, max_px):
    """Whether a word-box line fits max_px: its words' advances at CapCut's measured em plus the gaps between them, as
    _word_box_segments lays the line out."""
    from PIL import ImageFont
    em = _capcut_em_px(font_file, size, W)
    f = ImageFont.truetype(font_file, max(1, int(round(em))))
    k_em = em / max(1, int(round(em)))
    gap = gap_em * em

    def fits(text):
        toks = _tokens(text)
        return sum(f.getlength(t) * k_em for t in toks) + gap * max(0, len(toks) - 1) <= max_px
    return fits


def word_box_cues(words: list, max_words: int = 3, min_words: int = 3, break_gap: float = 0.8, info=None,
                  fits=None) -> list:
    """The word box's cues: chunk_words_fill (the original, unchanged) on each sentence on its own, so a cue never runs
    across a sentence end; inside a sentence it fills as before (a short tail joins the cue before it, a pause of
    break_gap s or more still breaks). With fits (a line's text -> it fits the frame), a cue too wide is cut into
    nearly equal runs that fit. A cue's end never runs past the next cue's start."""
    parts, cur = [], []
    for w in words:
        cur.append(w)
        if ends_sentence(w.get('w')):
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    res = []
    for part in parts:
        cues = chunk_words_fill(part, max_words, min_words, break_gap, info)
        res += _cut_to_fit(cues, part, fits, info) if fits is not None else cues
    for i in range(len(res) - 1):
        if res[i]['end'] > res[i + 1]['start']:
            res[i]['end'] = round(max(res[i + 1]['start'], res[i]['start'] + 0.01), 2)
    return res


# ---------------------------------------------------------------- the choice and the look
def caption_choice(st):
    """(captions, style) of a run: ('on', style), ('off', None), or (None, None) while the user has not chosen."""
    cap = st.get('captions')
    if cap == 'off':
        return 'off', None
    if cap == 'on' and st.get('caption_style') in CAPTION_STYLES:
        return 'on', st['caption_style']
    return None, None


def look_of(style):
    """The look of a style, its font file checked: the file must be the font the look names (its own name table), so a
    missing or substituted font stops the build instead of being reported as applied."""
    if style not in LOOKS:
        raise RuntimeError(f'unknown caption style {style!r}: one of {", ".join(CAPTION_STYLES)}')
    look = json.loads(json.dumps(LOOKS[style]))
    f = FONTS_DIR / look['font_file']
    if not f.is_file():
        raise RuntimeError(f'the caption font is missing: {f} (the {look["label"]} look needs it; nothing was built)')
    from PIL import ImageFont
    name = list(ImageFont.truetype(str(f), 20).getname())
    if name != look['font_name']:
        raise RuntimeError(f'{f} is {" ".join(name)}, not {" ".join(look["font_name"])}: nothing was built')
    look['font_path'] = str(f).replace('\\', '/')
    look['font_sha256'] = hashlib.sha256(f.read_bytes()).hexdigest()
    return look


def orientation(W, H):
    return 'landscape' if W > H * 1.05 else 'portrait' if H > W * 1.05 else 'square'


def capcut_size(font_path, W, H):
    """The CapCut size that gives the caption em (EM_SHARE of the smaller side) for this font on this canvas: CapCut sets
    a text's line (the font's ascent + descent) at CAPCUT_FONT_PER_SIZE x size x canvas width."""
    from PIL import ImageFont
    asc, desc = ImageFont.truetype(font_path, 1000).getmetrics()
    em = EM_SHARE * min(W, H)
    return round(em * ((asc + desc) / 1000) / (CAPCUT_FONT_PER_SIZE * W), 2)


# ---------------------------------------------------------------- words and their times
def display_words(text, strip_tags):
    """The words a caption shows for one script line, in order: its canonical text with the tags removed, split at
    spaces. A piece with no letter or digit (a dash, an ellipsis) is joined to the word before it (or after it, at the
    start), so it never takes a moment of its own and no caption word holds a space."""
    out, pending = [], ''
    for piece in strip_tags(text).split():
        if not re.search(r'\w', piece, re.UNICODE):
            if out:
                out[-1] += piece
            else:
                pending += piece
            continue
        out.append(pending + piece)
        pending = ''
    if pending and out:
        out[-1] += pending
    return out


def _token_owners(words, tokens_of, language, token_map=None):
    """Which of the line's comparable tokens each display word holds, so a number written over several words ('twenty
    five' -> 25) is one token those words share. [(first, end, shared_with_the_word_before)].

    With token_map(text, language) -> (raw tokens, [(token, first_raw, last_raw)]) each word owns exactly the tokens whose
    raw words it holds (2026-11-22: counting tokens on the growing line goes wrong where a number merges backwards, 'a hundred
    and' -> '100', 'and' then 'a hundred and fifty' -> '150': the word after the number was marked as sharing it and 'and'
    took that word's time). Without it, the older count on the growing line."""
    if token_map is not None:
        _, merged = token_map(' '.join(words), language)
        spans, r0, last = [], 0, 0
        for k in range(len(words)):
            r1 = max(r0, len(token_map(' '.join(words[:k + 1]), language)[0]))
            ms = [m for m, (_t, f, l) in enumerate(merged) if f < r1 and l >= r0]
            if ms:
                spans.append((ms[0], ms[-1] + 1, merged[ms[0]][1] < r0))   # shared: its first token began in an earlier word
                last = ms[-1] + 1
            else:
                spans.append((last, last, False))                            # no token of its own (a lone dash): no time
            r0 = r1
        return spans, len(merged)
    spans, prev = [], 0
    for k in range(len(words)):
        n = len(tokens_of(' '.join(words[:k + 1]), language))
        if n > prev:
            spans.append((prev, n, False))
        else:
            spans.append((max(0, n - 1), max(n, 1), k > 0))
        prev = max(prev, n)
    return spans, prev


def line_words(text, word_times, line_span, tokens_of, strip_tags, language, token_map=None):
    """One script line's display words with their narration times: [{'w', 's', 'e', 'timing'}] where timing is
    'whisper' (its own tokens' times), 'shared' (a number written over two words: its time split by length) or
    'between' (no time from Whisper: placed between its timed neighbours, or in the line's own span, by length).
    Returns (words, problem or None)."""
    words = display_words(text, strip_tags)
    if not words:
        return [], None
    spans, n_tok = _token_owners(words, tokens_of, language, token_map)
    if word_times is not None and len(word_times) != n_tok:
        return [], 'the line times hold other words than the script line has now'
    rows = []
    for w, (a, b, shared) in zip(words, spans):
        got = [word_times[i] for i in range(a, b) if word_times and i < len(word_times) and word_times[i]]
        rows.append({'w': w, 's': min(x[0] for x in got) if got else None, 'e': max(x[1] for x in got) if got else None,
                     'timing': 'whisper' if got else None, '_shared': shared})
    # a number written over two words: the token's time split between them by length
    k = 0
    while k < len(rows):
        j = k + 1
        while j < len(rows) and rows[j]['_shared']:
            j += 1
        if j - k > 1 and rows[k]['s'] is not None:
            s, e = rows[k]['s'], rows[k]['e']
            total = sum(len(r['w']) for r in rows[k:j]) or 1
            t = s
            for r in rows[k:j]:
                d = (e - s) * len(r['w']) / total
                r.update({'s': round(t, 3), 'e': round(t + d, 3), 'timing': 'shared'})
                t += d
        k = j
    # words Whisper gave no time: between their timed neighbours, by length
    lo, hi = (line_span or (None, None))
    k = 0
    while k < len(rows):
        if rows[k]['s'] is not None:
            k += 1
            continue
        j = k
        while j < len(rows) and rows[j]['s'] is None:
            j += 1
        a = rows[k - 1]['e'] if k > 0 else lo
        b = rows[j]['s'] if j < len(rows) else hi
        if a is None or b is None or b < a:
            return [], 'a word of this line has no time and no timed neighbour'
        total = sum(len(r['w']) for r in rows[k:j]) or 1
        t = a
        for r in rows[k:j]:
            d = (b - a) * len(r['w']) / total
            r.update({'s': round(t, 3), 'e': round(t + d, 3), 'timing': 'between'})
            t += d
        k = j
    for r in rows:
        r.pop('_shared', None)
    return rows, None


def edit_time(t, holds):
    """A narration time on the edit's timeline: plus every hold retime-shots inserted at or before it."""
    return round(t + sum(float(h['hold_s']) for h in holds if float(h['at_audio_s']) <= t + 1e-9), 3)


# ---------------------------------------------------------------- the word box (Luckiest Guy look)
# From _unspaced to _drop_text_tracks, except _tokens: copied unchanged from the other toolkit's word-box builder (awl.py),
# so the look and its timing are the same; tests/test_captions.py proves each copy equal to its original when awl.py is
# on this PC. _tokens is this pipeline's own (languages written with spaces only).
def _unspaced(info) -> bool:
    return bool(info) and info.get("spaced") is False


def _tokens(text, info=None) -> list:
    """The pieces a caption text is timed in: a language written with spaces, its words (text.split())."""
    return str(text or "").split()


def chunk_words_fill(words: list, max_words: int = 3, min_words: int = 3, break_gap: float = 0.8, info=None) -> list:
    """Timed words grouped into cues of max_words, filled across commas, sentence ends and short pauses (the word box shows which word is
    spoken, so the next words may show early; the user, 2026-11-09: "make it at least 3"); a cue never runs across a pause of break_gap s
    or more (a long pause, a chapter's dip). A stretch's last cue of fewer than min_words joins the cue before it in that stretch.
    info (_lang_info): for a language written without spaces the pieces are letters and a cue's text is joined with no space."""
    sep = "" if _unspaced(info) else " "
    stretches, cur = [], []
    for w in words:
        if cur and w["s"] - cur[-1]["e"] >= break_gap:
            stretches.append(cur)
            cur = []
        cur.append(w)
    if cur:
        stretches.append(cur)
    events = []
    for st in stretches:
        groups = [st[k:k + max_words] for k in range(0, len(st), max_words)]
        if len(groups) > 1 and len(groups[-1]) < min_words:
            last = groups.pop()
            groups[-1] = groups[-1] + last
        events += groups
    res = []
    starts = [round(ev[0]["s"], 2) for ev in events]
    for i, ev in enumerate(events):
        start = starts[i]
        end = max(ev[-1]["e"] + (0.05 if i + 1 < len(events) else 0.0), start + 0.25)
        if i + 1 < len(events):
            end = min(end, starts[i + 1])
        res.append({"start": start, "end": round(max(end, start + 0.01), 2), "text": sep.join(w["w"] for w in ev), "preset": "caption"})
    return res


def _word_box_plan(cues: list, words: list, offset: float, fps: int, min_frames: int = 1, info=None) -> tuple:
    """Each caption's moments: the cue's words in order, the box on the word being spoken, from the narration's word times (+ offset)
    on the frame grid. Returns (rows, problems): one row per cue {start, end, tokens, bounds[k] = the start of word k's box}. info
    (_lang_info) cuts a cue into the pieces its language is timed in (_tokens); the command itself takes only languages written with
    spaces, left to right."""
    rows, problems, wi = [], [], 0
    frame = 1.0 / max(1, int(fps))
    snap = lambda t: round(round(t / frame) * frame, 6)  # noqa: E731
    code = (info or {}).get("code")
    for ci, c in enumerate(cues):
        toks = _tokens(c["text"], info)
        times = []
        for t in toks:
            if wi >= len(words):
                problems.append({"cue": ci + 1, "text": c["text"], "error": "the narration's words ran out"})
                break
            w = words[wi]
            if _wb_norm(w.get("w"), code) != _wb_norm(t, code):
                problems.append({"cue": ci + 1, "text": c["text"], "token": t, "word": w.get("w"), "word_index": wi,
                                 "error": "the cue's word is not the narration's next word"})
            times.append(float(w["s"]) + offset)
            wi += 1
        cs, ce = snap(c["start"]), snap(c["end"])
        bounds = [cs]
        for k in range(1, len(toks)):
            t = snap(min(max(times[k] if k < len(times) else cs, bounds[-1]), ce))
            bounds.append(t)
        # a word whose box would show for under min_frames passes the box straight to the next word
        keep = [k for k in range(len(toks)) if (bounds[k + 1] if k + 1 < len(toks) else ce) - bounds[k] >= min_frames * frame - 1e-6]
        rows.append({"cue": ci + 1, "start": cs, "end": ce, "tokens": toks, "bounds": bounds, "boxed": keep})
    if wi != len(words):
        problems.append({"error": f"the cues hold {wi} words, the narration {len(words)}"})
    return rows, problems


def _word_box_segments(rows: list, font_file: str, size: float, W: int, H: int, gap_em: float) -> tuple:
    """Every caption word as its own text: its place on the line (x in CapCut's half-canvas units, the line centred) from the font's
    advances at CapCut's measured em, and its stretches of time, boxed while it is spoken. Grouped by (slot, boxed, at the cue's start):
    no two texts of a group overlap in time, so each group is one track."""
    from PIL import ImageFont
    em = _capcut_em_px(font_file, size, W)
    f = ImageFont.truetype(font_file, max(1, int(round(em))))
    k_em = em / max(1, int(round(em)))
    gap = gap_em * em
    groups, widest = {}, 0.0
    for r in rows:
        toks, n = r["tokens"], len(r["tokens"])
        if not n:
            continue
        widths = [f.getlength(t) * k_em for t in toks]
        total = sum(widths) + gap * (n - 1)
        widest = max(widest, total)
        left, xs = -total / 2, []
        for wdt in widths:
            xs.append(round((left + wdt / 2) / (W / 2), 5))
            left += wdt + gap
        # the boxed word per moment: moment k runs from bounds[k]; a word not in `boxed` hands its box to the word before
        ends = r["bounds"][1:] + [r["end"]]
        owner = []
        for k in range(n):
            kk = k
            while kk not in r["boxed"] and kk > 0:
                kk -= 1
            owner.append(kk if kk in r["boxed"] else (r["boxed"][0] if r["boxed"] else None))
        for i in range(n):
            spans = []
            for k in range(n):
                if ends[k] - r["bounds"][k] <= 0:
                    continue
                state = owner[k] == i
                if spans and spans[-1]["boxed"] == state and abs(spans[-1]["end"] - r["bounds"][k]) < 1e-6:
                    spans[-1]["end"] = ends[k]
                else:
                    spans.append({"start": r["bounds"][k], "end": ends[k], "boxed": state})
            for sp in spans:
                key = (i, sp["boxed"], abs(sp["start"] - r["start"]) < 1e-6)
                groups.setdefault(key, []).append({"cue": r["cue"], "text": toks[i], "x": xs[i], **sp})
    return groups, {"em_px": round(em, 2), "gap_px": round(gap, 2), "widest_line_px": round(widest, 1), "canvas": [W, H]}


def _capcut_em_px(font_file: str, size: float, canvas_w: int) -> float:
    from PIL import ImageFont
    asc, desc = ImageFont.truetype(font_file, 1000).getmetrics()
    return CAPCUT_FONT_PER_SIZE * float(size) * float(canvas_w) / ((asc + desc) / 1000)


def _wb_norm(w: str, code=None) -> str:
    """A caption word and a narration word compared without case or marks: every letter and digit of any script (a caption in capitals
    against the word as spoken; \\W also drops a letter's combining marks and every punctuation mark). code: Turkish and Azeri keep
    their two i's apart (a capital I is the dotless one, İ the dotted one), so a caption in capitals matches the word as spoken."""
    s = str(w)
    if str(code or "").lower().split("-")[0] in ("tr", "az"):
        s = s.replace("İ", "i").replace("I", "ı")
    return re.sub(r"[\W_]+", "", s.casefold())


def _upper_for(text, code=None) -> str:
    """A caption text in capitals the way the language writes them: str.upper(), with the dotted capital I Turkish and Azeri write for
    'i' (Python gives 'I'), and Lithuanian's rule that a capital loses the dot above a soft-dotted letter."""
    t = str(text)
    c = str(code or "").lower().split("-")[0]
    if c in ("tr", "az"):
        t = t.replace("i", "İ")
    elif c == "lt":
        t = re.sub("(?<=[ijį])̇", "", t)
    return t.upper()


def _drop_text_tracks(content: dict, names: set) -> int:
    """Remove the named text tracks with their text materials and the animations only they used."""
    gone = [t for t in content.get("tracks", []) if t.get("type") == "text" and str(t.get("name") or "") in names]
    if not gone:
        return 0
    mids, refs = set(), set()
    for t in gone:
        for s in t.get("segments", []):
            mids.add(s.get("material_id"))
            refs.update(s.get("extra_material_refs") or [])
    content["tracks"] = [t for t in content.get("tracks", []) if t not in gone]
    still = {r for t in content.get("tracks", []) for s in t.get("segments", []) for r in (s.get("extra_material_refs") or [])}
    mats = content.get("materials", {})
    mats["texts"] = [m for m in mats.get("texts", []) if m.get("id") not in mids]
    for kind in ("material_animations",):
        if kind in mats:
            mats[kind] = [m for m in mats[kind] if m.get("id") not in refs or m.get("id") in still]
    return len(gone)


# ---------------------------------------------------------------- the highlight (Montserrat Bold look)
def highlight_groups(words, look, width_of, max_width_px):
    """The caption lines of the highlight look: a line never runs across a sentence end or a pause of break_gap_s or
    more; a longer stretch is cut into nearly equal lines of at most max_words that each fit max_width_px."""
    runs, cur = [], []
    for w in words:
        if cur and (w['s'] - cur[-1]['e'] >= look['break_gap_s'] or ends_sentence(cur[-1]['w'])):
            runs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        runs.append(cur)
    groups = []
    for run in runs:
        n = len(run)
        parts = max(1, math.ceil(n / look['max_words']))
        while True:
            size = math.ceil(n / parts)
            chunks = [run[i:i + size] for i in range(0, n, size)]
            if size == 1 or all(width_of(' '.join(x['w'] for x in c)) <= max_width_px for c in chunks):
                break
            parts += 1
        groups += chunks
    return groups


def highlight_moments(groups, fps, look):
    """Each caption line's moments on the frame grid: the word being spoken lit from its start to its end (a gap to the
    next word shorter than bridge_s is not a pause: the next word takes over at once), every word lit for at least
    min_lit_frames, all white in a pause between two words, and after the last word all white for tail_s or until the
    next line. Moments never overlap. [{'group', 'start', 'end', 'active' (word index in the line, or None)}]."""
    frame = 1.0 / fps
    snap = lambda x: round(round(x / frame) * frame, 6)  # noqa: E731
    min_lit = look['min_lit_frames'] * frame
    out, t = [], 0.0
    for gi, g in enumerate(groups):
        nxt_line = snap(groups[gi + 1][0]['s']) if gi + 1 < len(groups) else None
        t = max(t, snap(g[0]['s']))
        for k, w in enumerate(g):
            start = max(snap(w['s']), t)
            end = snap(w['e'])
            ns = snap(g[k + 1]['s']) if k + 1 < len(g) else None
            if ns is not None and ns - end < look['bridge_s'] - 1e-9:
                end = ns
            end = round(max(end, start + min_lit), 6)
            out.append({'group': gi, 'start': start, 'end': end, 'active': k})
            t = end
            if ns is not None and ns > t + 1e-9:
                out.append({'group': gi, 'start': t, 'end': ns, 'active': None})
                t = ns
        stay = snap(t + look['tail_s'])
        if nxt_line is not None:
            stay = min(stay, max(nxt_line, t))
        if stay > t + 1e-9:
            out.append({'group': gi, 'start': t, 'end': stay, 'active': None})
            t = stay
    return [m for m in out if m['end'] - m['start'] > 1e-9]


def utf16_range(words, k):
    """The [start, end) of word k inside the line ' '.join(words), in UTF-16 code units (CapCut's text ranges)."""
    before = ' '.join(words[:k]) + (' ' if k else '')
    a = len(before.encode('utf-16-le')) // 2
    return [a, a + len(words[k].encode('utf-16-le')) // 2]


def _ass_time(t):
    cs = int(round(t * 100))
    return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'


def _ass_text(s):
    return str(s).replace('\\', '/').replace('{', '(').replace('}', ')')


def highlight_ass(groups, moments, W, H):
    """The highlight moments as ASS events: capcut-cli's import-ass turns each inline colour override into a CapCut
    text range, so the active word is its own yellow range and the rest of the line white."""
    lines = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', '', '[V4+ Styles]',
             'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
             'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, '
             'MarginR, MarginV, Encoding',
             'Style: Default,Montserrat,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1',
             '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    for m in moments:
        ws = [_ass_text(w['w']) for w in groups[m['group']]]
        if m['active'] is None:
            text = ' '.join(ws)
        else:
            k = m['active']
            text = ' '.join(ws[:k] + ['{\\c&H00FFFF&}' + ws[k] + '{\\c&HFFFFFF&}'] + ws[k + 1:])
        lines.append(f'Dialogue: 0,{_ass_time(m["start"])},{_ass_time(m["end"])},Default,,0,0,0,,{text}')
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------- CapCut: write and read back
def _srt_time(t):
    ms = int(round(t * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def _ct():
    import capcut_tools
    return capcut_tools


def caption_tracks(content):
    return [t for t in content.get('tracks', []) if t.get('type') == 'text' and str(t.get('name') or '').startswith(TRACK_PREFIX)]


def _set_font(m, c, font_path, ct):
    """What capcut-font writes for one text: the font file on the material and on every style (the ranges kept), and the
    outline where CapCut 9.x draws it from (each style's strokes)."""
    m.update({'font_name': '', 'font_title': 'none', 'font_id': '', 'font_resource_id': '', 'font_category_id': '',
              'font_category_name': '', 'font_source_platform': 0, 'font_team_id': '', 'font_url': '', 'fonts': [],
              'font_path': font_path})
    ct._text_outline_into_styles(m, c)
    for s in c.get('styles') or []:
        s['font'] = {'id': '', 'path': font_path}


def _patch_segments(d, ct, track_entries, font_path, y, box=None, box_color=None):
    """After capcut-cli wrote the tracks: in every root copy of the timeline, each text at its exact planned time (the
    frame grid, in microseconds), its place on the line, its font, and for a boxed word the box's size and offset
    (capcut-cli leaves those unset). Returns (texts patched, problems)."""
    placed, problems = 0, []
    for p in ct._draft_contents(d):
        c2 = json.loads(p.read_text(encoding='utf-8'))
        byname = {str(t.get('name') or ''): t for t in c2.get('tracks', []) if t.get('type') == 'text'}
        tmats = {m.get('id'): m for m in c2.get('materials', {}).get('texts', [])}
        here = 0
        for name, entries in track_entries.items():
            segs = sorted((byname.get(name) or {}).get('segments') or [], key=lambda s: int(s['target_timerange']['start']))
            if len(segs) != len(entries):
                problems.append({'file': p.name, 'track': name, 'texts': len(segs), 'planned': len(entries)})
                continue
            for s, e in zip(segs, entries):
                if abs(int(s['target_timerange']['start']) / 1e6 - e['start']) > 0.006:
                    problems.append({'file': p.name, 'track': name, 'at': e['start'],
                                     'segment_start': int(s['target_timerange']['start']) / 1e6})
                    break
                a, b = int(round(e['start'] * 1e6)), int(round(e['end'] * 1e6))
                s['target_timerange'] = {'start': a, 'duration': b - a}
                if isinstance(s.get('source_timerange'), dict):
                    s['source_timerange'] = {'start': 0, 'duration': b - a}
                s.setdefault('clip', {}).setdefault('transform', {})['x'] = e.get('x', 0.0)
                s['clip']['transform']['y'] = y
                m = tmats.get(s.get('material_id'))
                if m is None:
                    continue
                try:
                    c = json.loads(m.get('content') or '{}')
                except ValueError:
                    c = {}
                _set_font(m, c, font_path, ct)
                if box and e.get('boxed'):
                    m.update({'background_color': box_color, 'background_alpha': float(box['alpha']),
                              'background_style': int(box['style']), 'background_round_radius': float(box['round_radius']),
                              'background_width': float(box['pad']), 'background_height': float(box['pad']),
                              'background_horizontal_offset': 0.0, 'background_vertical_offset': float(box['v_offset']),
                              'background_fill': ''})
                    ct._text_outline_into_styles(m, c)
                if c:
                    m['content'] = json.dumps(c, ensure_ascii=False, separators=(',', ':'))
                here += 1
        p.write_text(json.dumps(c2, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        placed = max(placed, here)
    return placed, problems


def build_draft(d, plan, work, replace=False):
    """Write the plan's captions into a CapCut draft (closed CapCut only): the tracks of the chosen look, each text at its
    planned time, then the read-back check. Returns the build record."""
    ct = _ct()
    d = Path(d)
    if not (d / 'draft_content.json').is_file():
        raise RuntimeError(f'not a CapCut draft (no draft_content.json): {d}')
    if (d / '.locked').exists() or ct._capcut_running():
        raise RuntimeError('CapCut is running: close it, then build the captions again (nothing was changed)')
    content = json.loads((d / 'draft_content.json').read_text(encoding='utf-8'))
    cc = content.get('canvas_config') or {}
    W, H = int(cc.get('width') or 0), int(cc.get('height') or 0)
    if not W or not H:
        raise RuntimeError('the draft has no canvas size (canvas_config)')
    have = caption_tracks(content)
    if plan['captions'] == 'off':
        if have and not replace:
            raise RuntimeError('this run has captions off but the draft has caption tracks: pass --replace to remove them')
        if have:
            for p in ct._draft_contents(d):
                c2 = json.loads(p.read_text(encoding='utf-8'))
                _drop_text_tracks(c2, {str(t.get('name')) for t in caption_tracks(c2)})
                p.write_text(json.dumps(c2, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        return {'ok': True, 'captions': 'off', 'tracks': [], 'removed': len(have)}
    if have and not replace:
        raise RuntimeError('the draft already has caption tracks: pass --replace to build them again')
    if have:
        for p in ct._draft_contents(d):
            c2 = json.loads(p.read_text(encoding='utf-8'))
            _drop_text_tracks(c2, {str(t.get('name')) for t in caption_tracks(c2)})
            p.write_text(json.dumps(c2, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    style = plan['style']
    look = look_of(style)
    fps = int(plan.get('fps') or DEFAULT_FPS)
    size = capcut_size(look['font_path'], W, H)
    y = round(1 - 2 * Y_REL[orientation(W, H)], 4)
    cli = ct._capcut_cli()
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    words = plan['words']
    base = ['--font-size', str(size), '--color', look['fill'], '--align', '1', '--x', '0', '--y', str(y),
            '--border-width', str(look['stroke_width']), '--border-color', look['stroke_color']]
    if look['shadow']:
        base.append('--shadow')
    record = {'style': style, 'canvas': [W, H], 'size': size, 'y': y, 'fps': fps, 'font': look['font_path'],
              'font_sha256': look['font_sha256']}
    if style == 'montserrat-highlight':
        from PIL import ImageFont
        em = EM_SHARE * min(W, H)
        f = ImageFont.truetype(look['font_path'], max(1, int(round(em))))
        k_em = em / max(1, int(round(em)))
        groups = highlight_groups(words, look, lambda s: f.getlength(s) * k_em, look['max_line_width'] * W)
        moments = highlight_moments(groups, fps, look)
        ass = work / 'captions-highlight.ass'
        ass.write_text(highlight_ass(groups, moments, W, H), encoding='utf-8')
        cp = ct.run([cli, 'import-ass', str(d), str(ass), '--track-name', HIGHLIGHT_TRACK, *base], timeout=1800)
        if cp.returncode != 0:
            raise RuntimeError('capcut-cli import-ass failed: ' + str((ct._last_json(cp.stdout) or {}).get('error')
                                                                       or cp.stderr or cp.stdout)[-400:])
        entries = {HIGHLIGHT_TRACK: [{'start': m['start'], 'end': m['end'], 'x': 0.0} for m in moments]}
        placed, problems = _patch_segments(d, ct, entries, look['font_path'], y)
        widest = max((f.getlength(' '.join(w['w'] for w in g)) * k_em for g in groups), default=0.0)
        record.update({'lines': len(groups), 'texts': len(moments), 'lit': sum(1 for m in moments if m['active'] is not None),
                       'tracks': [HIGHLIGHT_TRACK], 'widest_line_px': round(widest, 1), 'placed': placed,
                       'problems': problems[:5], 'ass': str(ass)})
    else:
        box_color = plan.get('box_color')
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', str(box_color or '')):
            raise RuntimeError('the word box needs its colour (captions-plan --box-color #RRGGBB)')
        lw = [{'w': _upper_for(w['w'], plan.get('language')), 's': w['s'], 'e': w['e']} for w in words]
        cues = word_box_cues(lw, look['words'], look['min_words'], look['break_gap_s'],
                             fits=word_box_fits(look['font_path'], size, W, float(look['gap_em']),
                                                look['max_line_width'] * W))
        rows, problems = _word_box_plan(cues, lw, 0.0, fps)
        if problems:
            raise RuntimeError('the captions and the narration words do not line up: ' + json.dumps(problems[:3]))
        groups, geo = _word_box_segments(rows, look['font_path'], size, W, H, float(look['gap_em']))
        if geo['widest_line_px'] > look['max_line_width'] * W:
            raise RuntimeError(f'a caption line is wider than {look["max_line_width"]:.0%} of the frame at this size: {geo}')
        merged = {}
        for (i, boxed, _first), ents in groups.items():
            merged.setdefault((i, boxed), []).extend(ents)
        entries = {}
        for (i, boxed) in sorted(merged, key=lambda k: (not k[1], k[0])):     # boxed tracks first: plain words draw above
            name = f'{BOX_TRACK_PREFIX}{i + 1}-{"box" if boxed else "word"}'
            ents = sorted(merged[(i, boxed)], key=lambda e: e['start'])
            sp = work / f'{name}.srt'
            sp.write_text('\n'.join(f'{n + 1}\n{_srt_time(e["start"])} --> {_srt_time(e["end"])}\n{e["text"]}\n'
                                    for n, e in enumerate(ents)), encoding='utf-8')
            args = [cli, 'import-srt', str(d), str(sp), '--track-name', name, *base]
            if boxed:
                bx = look['box']
                args += ['--bg-color', box_color, '--bg-alpha', str(bx['alpha']), '--bg-style', str(bx['style']),
                         '--bg-round-radius', str(bx['round_radius'])]
            cp = ct.run(args, timeout=1800)
            if cp.returncode != 0:
                raise RuntimeError(f'capcut-cli import-srt failed on {name}: ' + str(
                    (ct._last_json(cp.stdout) or {}).get('error') or cp.stderr or cp.stdout)[-400:])
            entries[name] = [{**e, 'boxed': boxed} for e in ents]
        placed, problems = _patch_segments(d, ct, entries, look['font_path'], y, box=look['box'], box_color=box_color)
        record.update({'cues': len(cues), 'texts': sum(len(v) for v in entries.values()),
                       'boxed_texts': sum(len(v) for k, v in entries.items() if k.endswith('-box')),
                       'tracks': list(entries), 'geometry': geo, 'box_color': box_color, 'placed': placed,
                       'problems': problems[:5]})
    record['check'] = check_draft(d, plan)
    record['ok'] = not record.get('problems') and record['check']['ok']
    return record


def newest_content(d):
    """The project's timeline as CapCut will open it: the newest readable one of draft_content.json, template-2.tmp
    (written when the user opens the project) and the Timelines/ copies."""
    d = Path(d)
    docs = [p for p in (d / 'draft_content.json', d / 'template-2.tmp') if p.is_file()] + \
        sorted(d.glob('Timelines/*/draft_content.json'))
    for p in sorted(docs, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            c = json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(c, dict) and c.get('tracks') is not None:
            return c
    return None


def _style_fill(s):
    col = (((s.get('fill') or {}).get('content') or {}).get('solid') or {}).get('color')
    return tuple(round(float(x), 3) for x in col) if col else None


def _hex3(h):
    h = h.lstrip('#')
    return tuple(round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4))


def check_draft(d, plan, fps=None):
    """Read the captions back from the CapCut project itself and hold them against the plan: the chosen look (font file,
    colours, box or none), and the timing word by word: every word of the narration shown, lit (highlight) or boxed (word
    box) while it is spoken; in the highlight, never more than one yellow word, the yellow word is the word being
    spoken, and no word is yellow through a pause. With captions off, no caption track at all."""
    d = Path(d)
    content = newest_content(d)
    if content is None:
        return {'ok': False, 'issues': [f'not a CapCut draft (no readable timeline document): {d}']}
    tracks = caption_tracks(content)
    issues, warnings = [], []
    if plan['captions'] == 'off':
        if tracks:
            issues.append('captions_off_but_the_project_has_caption_tracks:' + ','.join(str(t.get('name')) for t in tracks))
        return {'ok': not issues, 'issues': issues, 'warnings': warnings, 'style': 'off'}
    style = plan['style']
    look = LOOKS[style]
    fps = int(fps or plan.get('fps') or DEFAULT_FPS)
    frame = 1.0 / fps
    mats = {m.get('id'): m for m in content.get('materials', {}).get('texts', [])}
    texts = []
    for t in tracks:
        for s in t.get('segments') or []:
            m = mats.get(s.get('material_id')) or {}
            try:
                c = json.loads(m.get('content') or '{}')
            except ValueError:
                c = {}
            texts.append({'track': str(t.get('name')), 'start': int(s['target_timerange']['start']) / 1e6,
                          'end': (int(s['target_timerange']['start']) + int(s['target_timerange']['duration'])) / 1e6,
                          'text': str(c.get('text') or ''), 'styles': c.get('styles') or [], 'm': m})
    if not texts:
        return {'ok': False, 'issues': ['captions_on_but_the_project_has_no_caption_text'], 'warnings': warnings,
                'style': style}
    wrong_font = sorted({Path(str(x['m'].get('font_path') or '')).name for x in texts} - {look['font_file']})
    if wrong_font:
        issues.append(f'caption_font_is_not_{look["font_file"]}:' + ','.join(wrong_font))
    if any(not all((s.get('font') or {}).get('path') for s in x['styles']) for x in texts):
        issues.append('a_caption_range_has_no_font_file')
    if any(not all(s.get('strokes') for s in x['styles']) for x in texts):
        issues.append('a_caption_range_has_no_outline')
    words = plan['words']
    if style == 'montserrat-highlight':
        if any(t.get('name') != HIGHLIGHT_TRACK for t in tracks):
            issues.append('word_box_tracks_in_a_highlight_project')
        if any(float(x['m'].get('background_alpha') or 0) > 0 and x['m'].get('background_color') for x in texts):
            issues.append('a_highlight_caption_has_a_box')
        white, yellow = _hex3(look['fill']), _hex3(look['active'])
        lit = []                      # (start, end, lit word text)
        for x in sorted(texts, key=lambda r: r['start']):
            ys = [s for s in x['styles'] if _style_fill(s) == yellow]
            others = [s for s in x['styles'] if _style_fill(s) not in (yellow, white)]
            if others:
                issues.append(f'a_caption_colour_other_than_white_or_yellow_at_{x["start"]:.2f}s')
            if len(ys) > 1:
                issues.append(f'more_than_one_yellow_word_at_{x["start"]:.2f}s')
            if ys:
                a, b = ys[0]['range']
                u = x['text'].encode('utf-16-le')
                lit.append((x['start'], x['end'], u[2 * a:2 * b].decode('utf-16-le')))
        # every word lit, in order, near its own start; never lit far past its end
        j, missed, late, overlong = 0, [], [], []
        for wi, w in enumerate(words):
            while j < len(lit) and lit[j][0] < w['s'] - 0.5:
                j += 1
            if j < len(lit) and _wb_norm(lit[j][2]) == _wb_norm(w['w']):
                if lit[j][0] - w['s'] > 0.25:
                    late.append(w['w'])
                allowed = max(w['e'], lit[j][0] + look['min_lit_frames'] * frame)
                # the bridge decided as the builder decides it: on the frame grid (2026-11-22: a gap of exactly 0.12 s is
                # 0.10 s once both ends are snapped, so the builder bridged it and the check, in raw seconds, did not)
                snap = lambda x: round(round(x / frame) * frame, 6)  # noqa: E731
                if wi + 1 < len(words) and snap(words[wi + 1]['s']) - snap(w['e']) < look['bridge_s'] - 1e-9:
                    allowed = max(allowed, snap(words[wi + 1]['s']))
                if lit[j][1] > allowed + 2 * frame:
                    overlong.append(w['w'])
                j += 1
            else:
                missed.append(w['w'])
        if missed:
            issues.append(f'{len(missed)}_words_never_lit:' + ','.join(missed[:8]))
        if overlong:
            issues.append(f'{len(overlong)}_words_stay_lit_after_they_are_spoken:' + ','.join(overlong[:8]))
        if late:
            warnings.append(f'{len(late)} words lit more than 0.25 s after Whisper heard them start: ' + ','.join(late[:8]))
        stats = {'texts': len(texts), 'lit_moments': len(lit), 'words': len(words), 'words_lit': len(words) - len(missed)}
    else:
        if any(not str(t.get('name')).startswith(BOX_TRACK_PREFIX) for t in tracks):
            issues.append('highlight_tracks_in_a_word_box_project')
        boxed = [x for x in texts if x['track'].endswith('-box')]
        if not boxed:
            issues.append('no_word_is_ever_boxed')
        cols = {str(x['m'].get('background_color') or '').upper() for x in boxed}
        if plan.get('box_color') and cols != {str(plan['box_color']).upper()}:
            issues.append('the_box_colour_is_not_the_planned_one:' + ','.join(sorted(cols)))
        if any(x['m'].get('background_color') and float(x['m'].get('background_alpha') or 0) > 0 for x in texts
               if x['track'].endswith('-word')):
            issues.append('a_plain_word_has_a_box')
        if any(x['text'] != x['text'].upper() for x in texts):
            issues.append('a_word_box_caption_is_not_in_capitals')
        order = sorted(boxed, key=lambda r: r['start'])
        j, missed, passed = 0, [], []
        for wi, w in enumerate(words):
            while j < len(order) and order[j]['start'] < w['s'] - 0.5:
                j += 1
            if j < len(order) and _wb_norm(order[j]['text']) == _wb_norm(w['w']):
                j += 1
            elif wi + 1 < len(words) and words[wi + 1]['s'] - w['s'] < 1.5 * frame:
                # the word box's own rule: a word that starts within a frame of the next hands its box straight on
                passed.append(w['w'])
            else:
                missed.append(w['w'])
        if missed:
            issues.append(f'{len(missed)}_words_never_boxed:' + ','.join(missed[:8]))
        if passed:
            warnings.append(f'{len(passed)} words start within a frame of the next and passed their box on (the word '
                            'box\'s own rule): ' + ','.join(passed[:8]))
        stats = {'texts': len(texts), 'boxed_texts': len(boxed), 'words': len(words),
                 'words_boxed': len(words) - len(missed) - len(passed), 'words_passed_on': len(passed)}
    overlaps = 0
    for t in tracks:
        segs = sorted(t.get('segments') or [], key=lambda s: int(s['target_timerange']['start']))
        for a, b in zip(segs, segs[1:]):
            if int(a['target_timerange']['start']) + int(a['target_timerange']['duration']) > int(b['target_timerange']['start']):
                overlaps += 1
    if overlaps:
        issues.append(f'{overlaps}_caption_texts_overlap_on_their_track')
    return {'ok': not issues, 'issues': issues, 'warnings': warnings, 'style': style, **stats}


# ---------------------------------------------------------------- a synthetic preview (PIL), for a look at the look
def preview(plan, out_dir, W=1920, H=1080, background=None, start_s=None, frames=8):
    """A few frames of the captions as PNGs (PIL, not CapCut's renderer): the layout, the font, the colours and which
    word is lit or boxed at each moment, over a still of the video when one is given. The outline is drawn at an
    approximate thickness; CapCut's own drawing is the export."""
    from PIL import Image, ImageDraw, ImageFont
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    look = look_of(plan['style'])
    em = EM_SHARE * min(W, H)
    font = ImageFont.truetype(look['font_path'], max(1, int(round(em))))
    cy = Y_REL[orientation(W, H)] * H
    words = plan['words']
    if start_s is None:
        start_s = words[0]['s'] if words else 0.0
    if background and Path(background).is_file():
        bg = Image.open(background).convert('RGB').resize((W, H))
    else:
        bg = Image.new('RGB', (W, H), (60, 66, 72))
    stroke = max(2, int(round(em * 0.08)))
    files = []
    if plan['style'] == 'montserrat-highlight':
        groups = highlight_groups(words, look, lambda s: font.getlength(s), look['max_line_width'] * W)
        moments = [m for m in highlight_moments(groups, int(plan.get('fps') or DEFAULT_FPS), look) if m['end'] > start_s][:frames]
        for i, m in enumerate(moments):
            img = bg.copy()
            dr = ImageDraw.Draw(img)
            ws = [w['w'] for w in groups[m['group']]]
            line = ' '.join(ws)
            x = (W - font.getlength(line)) / 2
            for k, w in enumerate(ws):
                col = look['active'] if m['active'] == k else look['fill']
                dr.text((x, cy), w, font=font, fill=col, anchor='lm', stroke_width=stroke, stroke_fill=look['stroke_color'])
                x += font.getlength(w + ' ')
            dr.text((20, 20), f'{m["start"]:.2f}-{m["end"]:.2f}s  lit: {ws[m["active"]] if m["active"] is not None else "(pause: all white)"}',
                    font=ImageFont.truetype(look['font_path'], 24), fill='#FFFFFF')
            f = out_dir / f'highlight-{i + 1:02d}.png'
            img.save(f)
            files.append(str(f))
    else:
        box_color = plan.get('box_color') or '#7A3CFF'
        lw = [{'w': _upper_for(w['w'], plan.get('language')), 's': w['s'], 'e': w['e']} for w in words]
        gap_px = float(look['gap_em']) * em

        def fits(s):
            return sum(font.getlength(t) for t in s.split()) + gap_px * (len(s.split()) - 1) <= look['max_line_width'] * W
        cues = [c for c in word_box_cues(lw, look['words'], look['min_words'], look['break_gap_s'], fits=fits)
                if c['end'] > start_s]
        shots = []
        for c in cues:
            toks = c['text'].split()
            for k in range(len(toks)):
                shots.append((c, toks, k))
                if len(shots) >= frames:
                    break
            if len(shots) >= frames:
                break
        gap = look['gap_em'] * em
        pad = look['box']['pad'] * em * 5
        for i, (c, toks, k) in enumerate(shots):
            img = bg.copy()
            dr = ImageDraw.Draw(img)
            widths = [font.getlength(t) for t in toks]
            x = (W - (sum(widths) + gap * (len(toks) - 1))) / 2
            for j, (t, wdt) in enumerate(zip(toks, widths)):
                if j == k:
                    box_h = em * 1.25
                    dr.rounded_rectangle([x - pad, cy - box_h / 2 - em * 0.15 * 0.5, x + wdt + pad, cy + box_h / 2 - em * 0.15 * 0.5],
                                         radius=int(em * look['box']['round_radius']), fill=box_color)
                dr.text((x, cy), t, font=font, fill=look['fill'], anchor='lm', stroke_width=stroke,
                        stroke_fill=look['stroke_color'])
                x += wdt + gap
            f = out_dir / f'wordbox-{i + 1:02d}.png'
            img.save(f)
            files.append(str(f))
    return files
