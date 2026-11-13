"""create-clips word-box captions: the word being spoken sits on a coloured box with rounded corners that moves from word to word.

The look (the user, 2026-11-13): the same background-box preset and spoken-word highlight the Loupe toolkit's Static videos use (white words with a black
outline, the spoken word on a rounded colour box), with a free font family and a free highlight colour per video. CapCut draws a text's background box behind the
WHOLE text only, so the caption is built from one CapCut text per word: the line is centred, every word has its own place on it, the word being spoken is the
boxed text and the others are plain. The line's maths is the Loupe toolkit's: CapCut sets a text's LINE (the font's ascent + descent) at CAPCUT_FONT_PER_SIZE x
size x the canvas width (measured on CapCut's own renders), so each font's em is that over its line height in em.

This module holds the planning (pure functions: words -> tokens -> cues -> rows -> one text per word and state, no CapCut, no file) and `apply_word_box`,
which writes the tracks into a draft through capcut-cli and the draft's own JSON. Nothing here judges: the agent picks the font, the colour and the size.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CAPCUT_FONT_PER_SIZE = 0.00575
WORD_BOX_PREFIX = "wordcap"
# THE LOUPE LOOK, copied from video 04 of the run 20261106-063422-static-klein (the user, 2026-11-13: "always use the same font family as they used in that video"; his
# screenshots of our frame and of that video's showed our box far too big and off its word). The numbers below were settled with the user on the Loupe videos 03/04
# (2026-11-09/10) FOR THIS FONT: CapCut draws a box around the whole line of a text (ascent + descent), so how big the box looks and where it sits depends on the font's
# metrics. Luckiest Guy has a line of 1.0 em with its baseline at 0.70 of it and capitals as tall as its lowercase; a font like Barlow Black (line 1.2 em, baseline at
# 0.83, x-height 0.52 em) puts the same numbers' box far too high around the same word. So the font is fixed: never a font picked per video.
HOUSE_FONT_FILE = "LuckiestGuy-Regular.ttf"            # a name in the Loupe fonts folder (AWL fonts/)
HOUSE_FONT_FAMILY = "Luckiest Guy"
HOUSE_STROKE_WIDTH = 0.18                               # a thick black outline, and a shadow (has_shadow), as in the Loupe videos' caption look
# the box: a rounded box (radius 0.3), padding 0.08 (CapCut's own 0.14 reached 0.35 em past the word), sitting 0.15 lower so it centres on the word, words 0.55 em apart
# so neighbouring boxes never touch; the colour is the video's own (the agent's pick: DEFAULT_COLOR is only the fallback, the orange of Loupe video 04)
DEFAULT_BOX = {"alpha": 1.0, "round_radius": 0.3, "style": 0, "gap_em": 0.55, "pad": 0.08, "v_offset": 0.15}
DEFAULT_COLOR = "#FF7A1A"
# the box is one text per word placed left to right along a centred line: a language written without spaces or right to left cannot take it
NO_WORD_BOX = {"zh": "written without spaces between words", "ja": "written without spaces between words", "th": "written without spaces between words",
               "lo": "written without spaces between words", "km": "written without spaces between words", "my": "written without spaces between words",
               "bo": "written without spaces between words", "ar": "written right to left", "he": "written right to left", "fa": "written right to left",
               "ur": "written right to left", "yi": "written right to left", "ps": "written right to left", "sd": "written right to left",
               "ug": "written right to left", "dv": "written right to left"}
# a word-box text that shows for fewer frames than this hands its box to the word before (a box for one frame is a flicker)
MIN_BOX_S = 0.08
EDGE_EM = 0.35            # CapCut's box reaches about this far past its word on each side (measured by the Loupe toolkit)
FIT_FRACTION = 0.92       # a caption line may fill at most this much of the frame's width (box edges included)


def box_params(caps: dict) -> dict:
    """The box's numbers: the preset, overridden by the EDL's captions.box; the colour is captions.highlight_color."""
    b = {**DEFAULT_BOX, **(caps.get("box") or {})}
    b["color"] = str(caps.get("highlight_color") or DEFAULT_COLOR)
    return b


def language_support(code) -> tuple:
    """(True, None) when the captions' language can take the word box, else (False, why)."""
    base = str(code or "").lower().replace("_", "-").split("-")[0]
    why = NO_WORD_BOX.get(base)
    return (why is None), why


# --------------------------------------------------------------------------- the words -> tokens -> cues

def _core(s: str) -> str:
    return re.sub(r"[^\w']+", "", str(s), flags=re.UNICODE).lower()


def _edges(w: str) -> tuple:
    """(leading punctuation, the word, trailing punctuation) of a token."""
    m = re.match(r"^([^\w']*)(.*?)([^\w']*)$", w, flags=re.UNICODE | re.DOTALL)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", w, "")


def tokens_from_words(words: list, caps: dict, mask_word) -> list:
    """The spoken words as they are captioned: the hardest words masked (`mask_terms`), the lexicon (`replace`: Whisper wrote -> right spelling) applied to
    WORD SEQUENCES, so a phrase that Whisper split across a caption's edge still matches and a replaced phrase keeps its place in time (its tokens share the
    span of the words they replace), the case rule last. Returns [{"w", "s", "e"}] in time order."""
    terms = {str(t).lower() for t in caps.get("mask_terms") or []}
    toks = [{"w": mask_word(x["w"], terms), "s": float(x["s"]), "e": float(x["e"])} for x in words]
    for pair in caps.get("replace") or []:
        try:
            src, dst = str(pair[0]).split(), str(pair[1]).split()
        except IndexError:
            continue
        if not src or not dst:
            continue
        srcn = [_core(x) for x in src]
        out, i = [], 0
        while i < len(toks):
            seg = toks[i:i + len(src)]
            if len(seg) == len(src) and [_core(t["w"]) for t in seg] == srcn:
                lead, trail = _edges(seg[0]["w"])[0], _edges(seg[-1]["w"])[2]
                s0, e0, n = seg[0]["s"], seg[-1]["e"], len(dst)
                for k, d in enumerate(dst):
                    text = (lead if k == 0 else "") + d + (trail if k == n - 1 else "")
                    out.append({"w": text, "s": round(s0 + (e0 - s0) * k / n, 3), "e": round(s0 + (e0 - s0) * (k + 1) / n, 3)})
                i += len(src)
            else:
                out.append(toks[i])
                i += 1
        toks = out
    case = caps.get("case")
    if case in ("upper", "lower"):
        for t in toks:
            t["w"] = t["w"].upper() if case == "upper" else t["w"].lower()
    return toks


def group_words(words: list, caps: dict) -> list:
    """Words -> caption lists: a new caption after `max_words` words, `max_chars` characters, a silence over `gap_break_s` or a sentence end."""
    mx_words, mx_chars, gap = int(caps["max_words"]), int(caps["max_chars"]), float(caps["gap_break_s"])
    cues, cur = [], []
    for w in words:
        if cur:
            text_len = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            if len(cur) >= mx_words or text_len > mx_chars or w["s"] - cur[-1]["e"] > gap or re.search(r"[.!?]$", cur[-1]["w"]):
                cues.append(list(cur))
                cur.clear()
        cur.append(w)
    if cur:
        cues.append(list(cur))
    return cues


def cue_times(groups: list, min_cue_s: float) -> list:
    """(start, end) of every caption: from its first word to its last, at least min_cue_s, never over the next caption's start."""
    times = []
    for i, ws in enumerate(groups):
        start, end = ws[0]["s"], ws[-1]["e"]
        nxt = groups[i + 1][0]["s"] if i + 1 < len(groups) else None
        end = max(end, start + float(min_cue_s))
        if nxt is not None:
            end = min(end, nxt)
        times.append((round(start, 3), round(end, 3)))
    return times


# --------------------------------------------------------------------------- the line's geometry

def capcut_em_px(font_file: str, size: float, canvas_w: int) -> float:
    from PIL import ImageFont
    asc, desc = ImageFont.truetype(font_file, 1000).getmetrics()
    return CAPCUT_FONT_PER_SIZE * float(size) * float(canvas_w) / ((asc + desc) / 1000)


# The caption size (the user, 2026-11-13: "neither too small nor too large ... most viewers may be watching from the phone or tablets ... go to the most optimal in the
# small/normal side"): the em of the caption is a fixed share of the picture's SMALLER side, so it looks the same on a 16:9 video (its height) and on a vertical
# one (its width), in any font. 4.6 % keeps to the small/normal side the user asked for and sits close to broadcast subtitle practice; the guide for the agent is 4.0 to
# 5.0 %, never above. For the house font (line 1.0 em) 4.6 % is CapCut size 4.5 on a 16:9 canvas and 8.0 on a 9:16 one. The Loupe videos themselves use size 5.5 / 10 in
# that font, which is an em of about 5.6 % of the smaller side, some 20 % larger: the user has not asked for that size here, so it is a number to change, not the default.
DEFAULT_EM_PCT = 4.6
EM_PCT_GUIDE = (4.0, 5.0)


def auto_size(font_file: str, canvas_w: int, canvas_h: int, em_pct: float = DEFAULT_EM_PCT) -> float:
    """The CapCut `size` that makes the font's em `em_pct` percent of the canvas's smaller side (CapCut sets the LINE, ascent + descent, at
    CAPCUT_FONT_PER_SIZE x size x width, so a font with a taller line needs a smaller size for the same em). One decimal, as CapCut takes it."""
    from PIL import ImageFont
    asc, desc = ImageFont.truetype(font_file, 1000).getmetrics()
    line_em = (asc + desc) / 1000
    em_px = float(em_pct) / 100.0 * min(int(canvas_w), int(canvas_h))
    return round(em_px * line_em / (CAPCUT_FONT_PER_SIZE * int(canvas_w)), 1)


def size_facts(font_file: str, size: float, canvas_w: int, canvas_h: int) -> dict:
    """Facts about a caption size: the em in pixels and as a percent of the canvas's smaller side, against the guide (a fact, not a verdict)."""
    em = capcut_em_px(font_file, size, canvas_w)
    pct = round(100.0 * em / min(int(canvas_w), int(canvas_h)), 2)
    return {"size": size, "em_px": round(em, 1), "em_pct_of_smaller_side": pct, "guide_pct": list(EM_PCT_GUIDE),
            "vs_guide": "inside" if EM_PCT_GUIDE[0] <= pct <= EM_PCT_GUIDE[1] else ("larger" if pct > EM_PCT_GUIDE[1] else "smaller")}


_GLYPHS = {}


def font_glyphs(font_file) -> set:
    """The code points a TrueType or OpenType font file has a glyph for (its cmap's Unicode subtables, formats 4 and 12), read with no library: the same reading the
    Loupe toolkit's capcut-font does, so a missing character is known when the captions are planned, not when the project is open. Raises ValueError for a file
    that is not a plain TrueType/OpenType font."""
    import struct
    p = Path(font_file)
    st = p.stat()
    key = (str(p.resolve()), st.st_mtime_ns, st.st_size)
    if key in _GLYPHS:
        return _GLYPHS[key]
    d = p.read_bytes()
    base = struct.unpack(">I", d[12:16])[0] if d[:4] == b"ttcf" else 0
    if d[base:base + 4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
        raise ValueError("not a TrueType or OpenType font file")
    cmap = None
    for k in range(struct.unpack(">H", d[base + 4:base + 6])[0]):
        tag, _cs, off, _ln = struct.unpack(">4sIII", d[base + 12 + 16 * k:base + 28 + 16 * k])
        if tag == b"cmap":
            cmap = off
            break
    if cmap is None:
        raise ValueError("the font file has no cmap table")
    got = set()
    for k in range(struct.unpack(">H", d[cmap + 2:cmap + 4])[0]):
        plat, enc, off = struct.unpack(">HHI", d[cmap + 4 + 8 * k:cmap + 12 + 8 * k])
        if not (plat == 0 or (plat == 3 and enc in (1, 10))):
            continue
        sub = cmap + off
        fmt = struct.unpack(">H", d[sub:sub + 2])[0]
        if fmt == 4:
            seg = struct.unpack(">H", d[sub + 6:sub + 8])[0] // 2
            o = sub + 14
            ends = struct.unpack(f">{seg}H", d[o:o + 2 * seg])
            starts = struct.unpack(f">{seg}H", d[o + 2 * seg + 2:o + 4 * seg + 2])
            deltas = struct.unpack(f">{seg}h", d[o + 4 * seg + 2:o + 6 * seg + 2])
            ro_at = o + 6 * seg + 2
            offs = struct.unpack(f">{seg}H", d[ro_at:ro_at + 2 * seg])
            for i in range(seg):
                if starts[i] == 0xFFFF:
                    continue
                for c in range(starts[i], min(ends[i], 0xFFFE) + 1):
                    if offs[i] == 0:
                        g = (c + deltas[i]) & 0xFFFF
                    else:
                        at = ro_at + 2 * i + offs[i] + 2 * (c - starts[i])
                        g = struct.unpack(">H", d[at:at + 2])[0] if at + 2 <= len(d) else 0
                        g = (g + deltas[i]) & 0xFFFF if g else 0
                    if g:
                        got.add(c)
        elif fmt == 12:
            for j in range(struct.unpack(">I", d[sub + 12:sub + 16])[0]):
                s0, e0, g0 = struct.unpack(">III", d[sub + 16 + 12 * j:sub + 28 + 12 * j])
                if e0 - s0 <= 0x110000:
                    got.update(c for c in range(s0, e0 + 1) if g0 + (c - s0))
    _GLYPHS[key] = got
    return got


def font_report(font_file, text: str) -> dict:
    """Whether the font has a glyph for every character of the captions: {"font_missing_glyphs": [...], "font_covers": bool}. A fact: a font that lacks a character draws a box
    or another font's letter. The house font (Luckiest Guy) draws English, Albanian (ë, ç), French, Spanish and German; it has no Slavic or Turkish letters (š ž č ć đ ğ ş)."""
    import struct
    import unicodedata
    try:
        have = font_glyphs(font_file)
    except (OSError, ValueError, struct.error) as e:
        return {"font_missing_glyphs": None, "font_covers": None, "font_glyphs_error": f"{type(e).__name__}: {e}"[:200]}
    miss = sorted({c for c in str(text or "") if not c.isspace() and unicodedata.category(c) not in ("Cc", "Cf", "Cs") and ord(c) not in have})
    return {"font_missing_glyphs": miss, "font_covers": not miss}


class Probe:
    """A font at CapCut's em on a canvas: word widths and the gap between words, in canvas pixels."""

    def __init__(self, font_file: str, size: float, canvas_w: int, gap_em: float):
        from PIL import ImageFont
        self.em = capcut_em_px(font_file, size, canvas_w)
        n = max(1, int(round(self.em)))
        self.font = ImageFont.truetype(font_file, n)
        self.k = self.em / n
        self.gap = gap_em * self.em

    def widths(self, tokens: list) -> list:
        return [self.font.getlength(t) * self.k for t in tokens]

    def line(self, tokens: list) -> float:
        return sum(self.widths(tokens)) + self.gap * max(0, len(tokens) - 1)


def fit_cues(cues: list, probe: Probe, limit_px: float, min_cue_s: float) -> list:
    """Captions as {start, end, words}; a caption whose line is wider than limit_px is split into two at the middle word (again until each fits), the first
    one ending where the second starts. Pure geometry: no word is changed or dropped."""
    out, todo = [], list(cues)
    while todo:
        c = todo.pop(0)
        ws = c["words"]
        if len(ws) < 2 or probe.line([w["w"] for w in ws]) <= limit_px:
            out.append(c)
            continue
        m = max(1, len(ws) // 2)
        a, b = ws[:m], ws[m:]
        a_end = max(a[-1]["e"], a[0]["s"] + min_cue_s)
        a_end = min(a_end, b[0]["s"])
        todo[0:0] = [{"start": c["start"], "end": round(a_end, 3), "words": a}, {"start": round(b[0]["s"], 3), "end": c["end"], "words": b}]
    return out


# --------------------------------------------------------------------------- rows and texts

def plan_rows(cues: list, fps: int, min_box_s: float = MIN_BOX_S) -> list:
    """Each caption's moments on the frame grid: its words in order and `bounds[k]`, the start of word k's moment (the first at the caption's start);
    `boxed` lists the words whose box would show for at least min_box_s (the box of a quicker word goes to the word before)."""
    frame = 1.0 / max(1, int(fps))
    min_frames = max(1, int(round(min_box_s / frame)))

    def snap(t):
        return round(round(t / frame) * frame, 6)
    rows = []
    for ci, c in enumerate(cues):
        toks = [w["w"] for w in c["words"]]
        times = [float(w["s"]) for w in c["words"]]
        cs = snap(c["start"])
        ce = max(snap(c["end"]), cs + frame)
        bounds = [cs]
        for k in range(1, len(toks)):
            bounds.append(snap(min(max(times[k], bounds[-1]), ce)))
        keep = [k for k in range(len(toks)) if (bounds[k + 1] if k + 1 < len(toks) else ce) - bounds[k] >= min_frames * frame - 1e-6]
        rows.append({"cue": ci + 1, "start": cs, "end": ce, "tokens": toks, "bounds": bounds, "boxed": keep})
    return rows


def plan_texts(rows: list, probe: Probe, canvas_w: int) -> tuple:
    """Every caption word as its own text: its x on the centred line (CapCut's half-canvas units) and its stretches of time, boxed while it is spoken.
    Grouped by (word index, boxed, starts at the caption's start): no two texts of a group overlap in time, so each group is one CapCut track.
    Returns (groups, geometry)."""
    groups, widest = {}, 0.0
    for r in rows:
        toks, n = r["tokens"], len(r["tokens"])
        if not n:
            continue
        widths = probe.widths(toks)
        total = sum(widths) + probe.gap * (n - 1)
        widest = max(widest, total)
        left, xs = -total / 2, []
        for wdt in widths:
            xs.append(round((left + wdt / 2) / (canvas_w / 2), 5))
            left += wdt + probe.gap
        ends = r["bounds"][1:] + [r["end"]]
        owner = []                                    # who holds the box in moment k: the word, or the word before when its own box would be too short
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
    return groups, {"em_px": round(probe.em, 2), "gap_px": round(probe.gap, 2), "widest_line_px": round(widest, 1), "canvas_w": canvas_w}


def track_name(i: int, boxed: bool, first: bool) -> str:
    return f"{WORD_BOX_PREFIX}-{i + 1}-{'box' if boxed else 'word'}{'-in' if first else ''}"


def plan_summary(groups: dict) -> dict:
    return {"tracks": len(groups), "texts": sum(len(v) for v in groups.values()), "boxed_texts": sum(len(v) for k, v in groups.items() if k[1])}


# --------------------------------------------------------------------------- the draft

def srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def drop_text_tracks(content: dict, keep_prefix_of=(WORD_BOX_PREFIX, "subtitle")) -> int:
    """Remove the caption text tracks of an earlier build (word-box tracks and the plain 'subtitle' track) with their text materials, so a second finish
    does not stack a second set of captions on the first."""
    def hit(t):
        nm = str(t.get("name") or "")
        return t.get("type") == "text" and any(nm == p or nm.startswith(p + "-") for p in keep_prefix_of)
    gone = [t for t in content.get("tracks", []) if hit(t)]
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
    if "material_animations" in mats:
        mats["material_animations"] = [m for m in mats["material_animations"] if m.get("id") not in refs or m.get("id") in still]
    return len(gone)


def plan_word_box(caps: dict, cues: list, canvas: dict, font_file: str) -> dict:
    """The word-box captions as a plan (no draft, no file): the box's numbers, the baseline `y` (CapCut's -1..1 units), the tracks (the boxed ones first, so the plain
    words draw above a box's edge) each with its texts, and the line's geometry. `error` is set when a caption line would be wider than the frame."""
    W, fps = int(canvas["width"]), int(canvas.get("fps") or 30)
    box = box_params(caps)
    probe = Probe(font_file, float(caps["size"]), W, float(box["gap_em"]))
    rows = plan_rows(cues, fps)
    groups, geo = plan_texts(rows, probe, W)
    plan = {"box": box, "y": round(1 - 2 * float(caps["y_rel"]), 4), "geometry": geo, "captions": len(rows), "tracks": [], "error": None}
    if geo["widest_line_px"] > FIT_FRACTION * W:
        plan["error"] = (f"a caption line is {geo['widest_line_px']:.0f} px wide, over {FIT_FRACTION:.0%} of the {W} px frame: run `captions` again "
                         f"(it splits long lines) or lower captions.size")
        return plan
    for key in sorted(groups, key=lambda k: (not k[1], k[0], not k[2])):
        i, boxed, first = key
        plan["tracks"].append({"track": track_name(i, boxed, first), "boxed": boxed, "entrance": first, "entries": sorted(groups[key], key=lambda e: e["start"])})
    return plan


def compose_parts(plan: dict, caps: dict, total_s: float) -> dict:
    """The planned captions as the captions' part of a `capcut compile` spec, so the whole project is one composition: one text track per planned track, every text
    already on its place on the line (`x` per word, the shared baseline `y`, the size and the colour), and one `text-style` operation per text: the outline, and on the
    boxed ones the box with the padding and offsets that capcut-cli's import-srt leaves unset. These are the same capcut-cli functions import-srt calls (addText and
    setTextStyle), so the texts are the ones the older route made, without a process and a draft write per track. A text is cut at the video's end (the project must
    not grow past its last clip); one that would then be shorter than a millisecond is dropped. Times are whole microseconds, so a text ends exactly where the next
    one of its track starts."""
    box, y = plan["box"], plan["y"]
    outline = {}
    if caps.get("stroke_color") and float(caps.get("stroke_width") or 0) > 0:
        outline = {"borderWidth": float(caps["stroke_width"]), "borderColor": str(caps["stroke_color"])}
    if caps.get("shadow"):                                  # the Loupe look's shadow: capcut-cli's `--shadow` (has_shadow on, CapCut's own shadow numbers)
        outline["shadow"] = True
    end_us = int(round(float(total_s) * 1e6))
    tracks, ops, kept, n, clipped, dropped = [], [], [], 0, 0, 0
    for tr in plan["tracks"]:
        items, entries = [], []
        for e in tr["entries"]:
            s_us, e_full = int(round(e["start"] * 1e6)), int(round(e["end"] * 1e6))
            e_us = min(e_full, end_us)
            if e_us - s_us < 1000:
                dropped += 1
                continue
            clipped += 1 if e_us < e_full else 0
            n += 1
            ref = f"cap{n}"
            items.append({"ref": ref, "text": e["text"], "start": s_us / 1e6, "duration": (e_us - s_us) / 1e6, "fontSize": float(caps["size"]),
                          "color": str(caps["color"]), "x": e["x"], "y": y})
            entries.append({**e, "start": s_us / 1e6, "end": e_us / 1e6})
            style = dict(outline)
            if tr["boxed"]:
                style.update({"bgColor": box["color"], "bgAlpha": float(box["alpha"]), "bgStyle": int(box["style"]), "bgRoundRadius": float(box["round_radius"]),
                              "bgWidth": float(box["pad"]), "bgHeight": float(box["pad"]), "bgHOffset": 0.0, "bgVOffset": float(box["v_offset"])})
            if style:
                ops.append({"op": "text-style", "target": ref, "style": style})
        if items:
            tracks.append({"type": "text", "name": tr["track"], "items": items})
            kept.append({**tr, "entries": entries})
    return {"tracks": tracks, "operations": ops, "plan_tracks": kept, "texts": n, "clipped_at_end": clipped, "dropped": dropped}


def check_composed(d: Path, plan_tracks: list, boxed_fill: bool, draft_files) -> dict:
    """After `capcut compile` wrote the captions into the draft: every planned track is there with its texts in the planned order and at the planned time (2 ms), and the
    boxed texts get the one box field the compile route cannot set (`background_fill`, empty: CapCut's own value for a plain colour box). Written into every copy of
    the timeline. Returns facts: {"ok", "tracks", "texts", "boxed_texts", "unmatched": [...]}."""
    texts, boxed_texts, unmatched = 0, 0, []
    for p in draft_files(d):
        c = json.loads(p.read_text(encoding="utf-8"))
        byname = {str(t.get("name") or ""): t for t in c.get("tracks", []) if t.get("type") == "text"}
        mats = {m.get("id"): m for m in c.get("materials", {}).get("texts", [])}
        n_here, b_here, changed = 0, 0, False
        for tr in plan_tracks:
            t = byname.get(tr["track"])
            segs = sorted((t or {}).get("segments") or [], key=lambda s: int(s["target_timerange"]["start"]))
            if len(segs) != len(tr["entries"]):
                unmatched.append({"file": p.name, "track": tr["track"], "texts": len(segs), "planned": len(tr["entries"])})
                continue
            for s, e in zip(segs, tr["entries"]):
                if abs(int(s["target_timerange"]["start"]) / 1e6 - e["start"]) > 0.002:
                    unmatched.append({"file": p.name, "track": tr["track"], "at": e["start"], "segment_start": int(s["target_timerange"]["start"]) / 1e6})
                    break
                n_here += 1
                if tr["boxed"]:
                    b_here += 1
                    m = mats.get(s.get("material_id"))
                    if m is not None and boxed_fill and m.get("background_fill") != "":
                        m["background_fill"] = ""
                        changed = True
        if changed:
            p.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        if p.name == "draft_content.json":
            texts, boxed_texts = n_here, b_here
    return {"ok": not unmatched, "tracks": len(plan_tracks), "texts": texts, "boxed_texts": boxed_texts, "unmatched": unmatched[:5]}


def apply_word_box(d: Path, vdir: Path, caps: dict, cues: list, canvas: dict, font_file: str, cli: str, awl: list, run, sh, draft_files, after_write=None) -> dict:
    """Write the word-box captions into an existing draft (the route for a draft that capcut-compose did not put them in): one track per (word index, boxed, entrance)
    with capcut-cli's import-srt (the box flags on the boxed ones), each text moved to its place on the line and the box's padding written into the draft's own JSON
    (capcut-cli leaves them unset), then the font on every text and the entrance on the tracks that start a caption. Returns {"ok", "steps", ...}; the caller runs
    capcut-repair afterwards. A draft made by `capcut-compose` already holds these texts (compose_parts) and only needs `font_and_entrance`."""
    plan = plan_word_box(caps, cues, canvas, font_file)
    box, geo, rows_n, y = plan["box"], plan["geometry"], plan["captions"], plan["y"]
    steps = []
    if plan["error"]:
        return {"ok": False, "error": plan["error"], "geometry": geo, "steps": steps}
    dropped = 0
    for p in draft_files(d):
        c = json.loads(p.read_text(encoding="utf-8"))
        dropped = max(dropped, drop_text_tracks(c))
        p.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    work = vdir / "word-box"
    work.mkdir(parents=True, exist_ok=True)
    tracks, failed = [], []
    for tr0 in plan["tracks"]:
        name, boxed, first, ents = tr0["track"], tr0["boxed"], tr0["entrance"], tr0["entries"]
        sp = work / f"{name}.srt"
        sp.write_text("\n".join(f"{n + 1}\n{srt_time(e['start'])} --> {srt_time(e['end'])}\n{e['text']}\n" for n, e in enumerate(ents)), encoding="utf-8")
        args = [cli, "import-srt", str(d), str(sp), "--track-name", name, "--font-size", str(caps["size"]), "--color", str(caps["color"]),
                "--align", "1", "--x", "0", "--y", str(y)]
        if caps.get("stroke_color") and float(caps.get("stroke_width") or 0) > 0:
            args += ["--border-width", str(caps["stroke_width"]), "--border-color", str(caps["stroke_color"])]
        if caps.get("shadow"):
            args.append("--shadow")
        if boxed:
            args += ["--bg-color", box["color"], "--bg-alpha", str(box["alpha"]), "--bg-style", str(box["style"]), "--bg-round-radius", str(box["round_radius"])]
        r = sh(args, 600)
        if after_write:                                # capcut-cli keeps an undo snapshot of the whole draft after every write: the caller drops it (hundreds of MB over 15 tracks)
            after_write()
        if r["exit"] != 0:
            failed.append({"track": name, "error": str((r.get("result") if isinstance(r.get("result"), dict) else {}).get("error") or r.get("stderr") or r.get("result"))[-300:]})
            continue
        tracks.append({"track": name, "texts": len(ents), "boxed": boxed, "entrance": first, "entries": ents})
    placed, unmatched = 0, []
    for p in draft_files(d):                      # every copy of the timeline: capcut-cli wrote the root's documents, repair copies them into the nested ones
        c2 = json.loads(p.read_text(encoding="utf-8"))
        byname = {str(t.get("name") or ""): t for t in c2.get("tracks", []) if t.get("type") == "text"}
        tmats = {m.get("id"): m for m in c2.get("materials", {}).get("texts", [])}
        n_here = 0
        for tr in tracks:
            t = byname.get(tr["track"])
            segs = sorted((t or {}).get("segments") or [], key=lambda s: int(s["target_timerange"]["start"]))
            if len(segs) != len(tr["entries"]):
                unmatched.append({"file": p.name, "track": tr["track"], "texts": len(segs), "planned": len(tr["entries"])})
                continue
            for s, e in zip(segs, tr["entries"]):
                if abs(int(s["target_timerange"]["start"]) / 1e6 - e["start"]) > 0.002:
                    unmatched.append({"file": p.name, "track": tr["track"], "at": e["start"], "segment_start": int(s["target_timerange"]["start"]) / 1e6})
                    break
                s.setdefault("clip", {}).setdefault("transform", {})["x"] = e["x"]
                s["clip"]["transform"]["y"] = y
                m = tmats.get(s.get("material_id"))
                if m is not None and tr["boxed"]:
                    # capcut-cli's import-srt leaves the box's size and offsets unset: CapCut's own values for a box (0.14 around the text, centred, is CapCut's
                    # own; the Loupe videos use the smaller pad 0.08 and a vertical offset that lets the box sit a little low)
                    m.update({"background_width": float(box["pad"]), "background_height": float(box["pad"]), "background_horizontal_offset": 0.0,
                              "background_vertical_offset": float(box["v_offset"]), "background_fill": ""})
                n_here += 1
        p.write_text(json.dumps(c2, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        placed = max(placed, n_here)
    steps.append({"step": "captions-word-box", "captions": rows_n, "tracks": len(tracks), "texts": sum(t["texts"] for t in tracks),
                  "boxed_texts": sum(t["texts"] for t in tracks if t["boxed"]), "placed": placed, "failed": failed[:5], "unmatched": unmatched[:5],
                  "dropped_old_caption_tracks": dropped, "geometry": geo, "box": box, "exit": 0 if not failed and not unmatched else 1})
    steps.extend(font_and_entrance(d, caps, [t for t in tracks if t["entrance"]], font_file, awl, run, sh))
    return {"ok": not failed and not unmatched, "steps": steps, "geometry": geo, "texts": sum(t["texts"] for t in tracks)}


def font_and_entrance(d: Path, caps: dict, entrance_tracks: list, font_file: str, awl: list, run, sh) -> list:
    """What no capcut-cli composition can write: the caption font on every text (awl's `capcut-font` also sets the outline and the box flags CapCut 9.7 needs) and, when the
    EDL asks for an entrance, the animation on the tracks that start a caption (one call per track). Runs on a draft whatever route wrote its texts."""
    steps = [{"step": "captions-font", **sh([*awl, "capcut-font", "--draft", str(d), "--font-file", str(font_file)], 600)}]
    if caps.get("intro"):
        for tr in entrance_tracks:
            steps.append({"step": "captions-intro:" + tr["track"], **sh([*awl, "capcut-text-anim", "--draft", str(d), "--track", tr["track"], "--intro", caps["intro"],
                                                                           "--intro-duration", str(caps.get("intro_s") or 0.1), "--run", str(run)], 300)})
    return steps
