#!/usr/bin/env python3
"""Static Studio: render an animated drawing as a transparent overlay clip for CapCut.

CapCut has no freehand drawing primitive (only fixed mask shapes, keyframes on existing clips and library stickers),
so this tool is the drawing itself: it renders a spec frame by frame with Pillow and encodes it with an alpha channel
(QuickTime Animation, qtrle, in a .mov) so CapCut only plays it as an overlay clip above the still it explains.

What a spec can hold (manual 04, "Drawn animation"): strokes in several hands (plain, ink, brush, pencil, chalk,
marker) with draw-on, dashes that march and arrow heads that ride the pen; hand-drawn rings, ticks and crosses,
scribbles, highlights and redaction bars; words typed, typed with a caret, decoded, written, risen or popped, on a paper
plate if needed; counters; rubber stamps that slam; paper cards that drop, slide or flip; pins and sagging string;
icons that travel along a route with a trail (plane, ship, envelope, tank, dot); pulses and radio arcs; hatching;
Morse marks; groups; keyframed moves (offset, scale, rotation, opacity) on any element; soft shadows and glows.

Rendering: every frame is drawn at `supersample` times the canvas (default 3) and reduced, so strokes and letters are
smooth, and each element is composited on its own (a translucent stroke over a fill blends, never punches a hole).
A frame whose animation state equals the previous frame's is written once and reused.

Following the picture: a drawing is placed on its still. `still_motion` ({"scale": [s0, s1], "x": [x0, x1],
"y": [y0, y1]}: the values capcut-motion keys on the still, linear over the clip) moves and scales every element with
the picture frame by frame, so a still keeps its camera move under its drawing. `still_framing` (one framing for the
whole clip, `framing_applied` when the spec's positions already include it) is the static form.

Local work only: no model, no API, no credits.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SUPERSAMPLE = 3
FONT_DIRS = [Path(r'C:\Windows\Fonts'), Path.home() / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'Fonts',
             Path('/usr/share/fonts/truetype'), Path('/Library/Fonts'), Path('/System/Library/Fonts')]
FONT_NAMES = {'typed': 'courbd.ttf', 'typed-light': 'cour.ttf', 'hand': 'Inkfree.ttf', 'stencil': 'STENCIL.TTF',
              'serif': 'georgiab.ttf', 'script': 'BRUSHSCI.TTF', 'sans': 'bahnschrift.ttf'}
ELEMENT_TYPES = ('line', 'arrow', 'path', 'ellipse', 'rect', 'box', 'polygon', 'text', 'counter', 'stamp', 'card',
                 'ring', 'mark', 'scribble', 'highlight', 'redact', 'travel', 'pulse', 'hatch', 'string', 'pin',
                 'morse', 'group')
STROKE_STYLES = ('plain', 'ink', 'brush', 'pencil', 'chalk', 'marker')
ICONS = ('plane', 'ship', 'envelope', 'tank', 'dot', 'chevron')
POS_KEYS = ('at', 'center', 'a', 'b', 'pivot')
PTS_KEYS = ('points',)
SIZE_KEYS = ('w', 'h', 'size', 'r_max', 'icon_size', 'spacing', 'text_size')


def emit(data, code=0):
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


def error(msg, details=None):
    emit({'ok': False, 'error': msg, 'details': details}, 2)


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def ease(t, kind):
    t = clamp(t)
    if kind in (None, 'linear'):
        return t
    if kind == 'in':
        return t * t
    if kind == 'out':
        return 1 - (1 - t) * (1 - t)
    if kind == 'inout':
        return 3 * t * t - 2 * t * t * t
    if kind == 'out3':
        return 1 - (1 - t) ** 3
    if kind == 'expo':
        return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
    if kind == 'sine':
        return 0.5 - 0.5 * math.cos(math.pi * t)
    if kind == 'back':                  # runs a little past the end, then settles on it
        c1 = 1.70158
        return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2
    if kind == 'inback':
        c1 = 1.70158
        return (c1 + 1) * t ** 3 - c1 * t ** 2
    if kind == 'elastic':
        if t in (0.0, 1.0):
            return t
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
    if kind == 'bounce':
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        if t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        if t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        t -= 2.625 / d1
        return n1 * t * t + 0.984375
    raise ValueError(f'unknown ease: {kind}')


def window(a):
    """(start, dur) of an animation window {start_s, dur_s}."""
    return float(a.get('start_s', 0) or 0), max(1e-6, float(a.get('dur_s', 0.3) or 0.3))


def anim_p(a, t, default_ease='out'):
    """Eased progress of an animation window at t (clamped before and after; an overshooting ease may pass 1)."""
    if not a:
        return 1.0
    start, dur = window(a)
    return ease((t - start) / dur, a.get('ease', default_ease))


def progress(spec, t, key='in'):
    """Kept for older callers: 0..1 progress of the named animation (an exit counts down)."""
    a = spec.get(key)
    if not a:
        return 1.0 if key == 'in' else 0.0
    p = clamp(anim_p(a, t))
    return p if key == 'in' else 1 - p


QUICK_IN = ('pop', 'grow', 'slam', 'drop', 'slide', 'flip', 'rise')
# an entrance with no kind: a counter counts, a traveller travels, a pulse or Morse mark runs; anything else fades
DEFAULT_IN = {'counter': 'count', 'travel': 'draw', 'pulse': 'draw', 'morse': 'draw'}


def presence(el, t):
    """The element's opacity from its entrance and exit at t. A fade fades; a moving entrance (pop, slam, drop, ...)
    appears in the first third of its window; a drawn, typed or travelling entrance is fully there once it starts.
    Nothing shows before the entrance starts. An exit other than a fade does its own work and is gone at its end."""
    a = 1.0
    i = el.get('in')
    if i:
        start, dur = window(i)
        if t < start - 1e-9:
            return 0.0
        kind = i.get('kind') or DEFAULT_IN.get(el.get('type'), 'fade')
        if kind == 'fade':
            a = clamp(ease((t - start) / dur, i.get('ease', 'out')))
        elif kind in QUICK_IN:
            a = clamp((t - start) / (dur * 0.35))
    o = el.get('out')
    if o:
        start, dur = window(o)
        if t >= start:
            if o.get('kind', 'fade') == 'fade':
                a *= 1 - clamp(ease((t - start) / dur, o.get('ease', 'out')))
            elif t >= start + dur:
                a = 0.0
    return a


def visible_window(el, t, dur_s=None):
    return presence(el, t)


def hex_rgba(hexcolor, alpha=1.0):
    h = (hexcolor or '#ffffff').lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, max(0, min(255, round(alpha * 255))))


def _h(seed, i):
    """A repeatable pseudo-random number in [0, 1) for (seed, i)."""
    x = (seed * 0x9E3779B1 + i * 0x85EBCA77 + 0x165667B1) & 0xffffffff
    x ^= x >> 15
    x = (x * 0x2C1B3C6D) & 0xffffffff
    x ^= x >> 12
    x = (x * 0x297A2D39) & 0xffffffff
    x ^= x >> 15
    return x / 4294967296.0


def seed_of(el):
    return zlib.crc32(str(el.get('id', '')).encode('utf-8'))


# ------------------------------------------------------------------ the still under the drawing
def apply_framing(elements, framing):
    """A drawing placed on its still (positions in fractions of the still) follows the still as the edit frames it:
    framing = {"scale": s, "x": dx, "y": dy} is the still's scale (1 = it covers the canvas) and the shift of its centre
    in CapCut's half-canvas units (x to the right, y up), as the moves file holds it. Every position moves out from the
    centre by s and with the shift; every size (w, h, size, width of a stroke is kept) grows by s. Without a framing, or
    at scale 1 and no shift, the elements are returned unchanged."""
    if not framing:
        return elements
    s = float(framing.get('scale', 1.0))
    dx, dy = float(framing.get('x', 0.0)), float(framing.get('y', 0.0))
    if abs(s - 1.0) < 1e-9 and not dx and not dy:
        return elements
    return [transform_element(e, s, dx, dy, digits=5) for e in elements]


def transform_element(el, s, x, y, digits=None):
    """One element (and a group's children) moved with a still shown at scale s, its centre shifted by (x, y) in
    half-canvas units (x right, y up): positions go out from the centre by s and with the shift, sizes grow by s."""
    dx, dy = x / 2, -y / 2
    rnd = (lambda v: round(v, digits)) if digits else (lambda v: v)

    def tp(p):
        return [rnd(0.5 + dx + (float(p[0]) - 0.5) * s), rnd(0.5 + dy + (float(p[1]) - 0.5) * s)]
    e = dict(el)
    for k in PTS_KEYS:
        if k in e and isinstance(e[k], list):
            e[k] = [tp(p) for p in e[k]]
    for k in POS_KEYS:
        if k in e and isinstance(e[k], (list, tuple)) and len(e[k]) == 2:
            e[k] = tp(e[k])
    for k in SIZE_KEYS:
        if k in e and isinstance(e[k], (int, float)):
            e[k] = rnd(float(e[k]) * s)
    if isinstance(e.get('keys'), list):
        e['keys'] = [{**k, **{n: float(k[n]) * s for n in ('dx', 'dy') if n in k}} for k in e['keys']]
    if isinstance(e.get('children'), list):
        e['children'] = [transform_element(c, s, x, y, digits) for c in e['children']]
    return e


def still_state(spec, t):
    """(scale, x, y) of the still under the drawing at t, or None when the positions are already the frame's."""
    m = spec.get('still_motion')
    if isinstance(m, dict) and m.get('scale'):
        dur = float(m.get('dur_s') or spec.get('dur_s') or 1.0)
        f = clamp(t / max(1e-6, dur))
        lerp = lambda pair: float(pair[0]) + (float(pair[1]) - float(pair[0])) * f
        return lerp(m.get('scale', [1, 1])), lerp(m.get('x', [0, 0])), lerp(m.get('y', [0, 0]))
    fr = spec.get('still_framing')
    if isinstance(fr, dict) and spec.get('framing_applied') is not True:
        return float(fr.get('scale', 1.0)), float(fr.get('x', 0.0)), float(fr.get('y', 0.0))
    return None


def motion_varies(spec):
    m = spec.get('still_motion')
    if not isinstance(m, dict):
        return False
    return any(abs(float(v[0]) - float(v[1])) > 1e-9 for v in (m.get('scale', [1, 1]), m.get('x', [0, 0]),
                                                                  m.get('y', [0, 0])))


# ------------------------------------------------------------------ geometry
def catmull(pts, n=8, closed=False):
    """A smooth curve through the points (centripetal Catmull-Rom), n steps per span."""
    if len(pts) < 3:
        return list(pts)
    P = list(pts)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [(2 * P[0][0] - P[1][0], 2 * P[0][1] - P[1][1])] + P + [(2 * P[-1][0] - P[-2][0], 2 * P[-1][1] - P[-2][1])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]

        def tj(ti, a, b):
            return ti + max(1e-6, math.dist(a, b)) ** 0.5
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            a1 = [((t1 - t) * p0[j] + (t - t0) * p1[j]) / (t1 - t0) for j in (0, 1)]
            a2 = [((t2 - t) * p1[j] + (t - t1) * p2[j]) / (t2 - t1) for j in (0, 1)]
            a3 = [((t3 - t) * p2[j] + (t - t2) * p3[j]) / (t3 - t2) for j in (0, 1)]
            b1 = [((t2 - t) * a1[j] + (t - t0) * a2[j]) / (t2 - t0) for j in (0, 1)]
            b2 = [((t3 - t) * a2[j] + (t - t1) * a3[j]) / (t3 - t1) for j in (0, 1)]
            out.append(tuple(((t2 - t) * b1[j] + (t - t1) * b2[j]) / (t2 - t1) for j in (0, 1)))
    out.append(tuple(pts[0]) if closed else tuple(pts[-1]))
    return out


def densify(pts, step):
    """Points every `step` pixels along the path, with each one's distance from the start."""
    out, acc = [tuple(pts[0])], [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / max(0.5, step)))
        for k in range(1, n + 1):
            f = k / n
            out.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
            acc.append(acc[-1] + d / n)
    return out, acc


def resample_path(points, frac_len):
    """Return the prefix of `points` covering `frac_len` (0..1) of total arc length, with the cut point interpolated."""
    if frac_len >= 1.0 or len(points) < 2:
        return points
    seglens = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(seglens) or 1e-6
    target = total * max(0.0, frac_len)
    acc = 0.0
    out = [points[0]]
    for i, sl in enumerate(seglens):
        if acc + sl >= target:
            t = (target - acc) / sl if sl > 1e-9 else 0
            out.append((points[i][0] + (points[i + 1][0] - points[i][0]) * t,
                        points[i][1] + (points[i + 1][1] - points[i][1]) * t))
            return out
        acc += sl
        out.append(points[i + 1])
    return out


def point_at(dense, acc, u):
    """The point at arc-length fraction u and the path's direction there (radians)."""
    total = acc[-1] or 1e-6
    target = clamp(u) * total
    lo, hi = 0, len(acc) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if acc[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    i = max(1, lo)
    seg = acc[i] - acc[i - 1]
    f = (target - acc[i - 1]) / seg if seg > 1e-9 else 0.0
    x0, y0 = dense[i - 1]
    x1, y1 = dense[i]
    j0, j1 = max(0, i - 3), min(len(dense) - 1, i + 2)
    ang = math.atan2(dense[j1][1] - dense[j0][1], dense[j1][0] - dense[j0][0])
    return (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f), ang


def sub_path(dense, acc, u0, u1):
    """The part of a densified path between arc-length fractions u0 and u1, with each kept point's fraction."""
    total = acc[-1] or 1e-6
    if u1 <= u0:
        return [], []
    a, b = u0 * total, u1 * total
    pts, us = [], []
    p0, _ = point_at(dense, acc, u0)
    pts.append(p0)
    us.append(u0)
    for p, s in zip(dense, acc):
        if a < s < b:
            pts.append(p)
            us.append(s / total)
    p1, _ = point_at(dense, acc, u1)
    pts.append(p1)
    us.append(u1)
    return pts, us


# ------------------------------------------------------------------ fonts
_FONTS = {}


def font_path(el, default='typed'):
    if el.get('font_file'):
        return str(el['font_file'])
    name = FONT_NAMES.get(str(el.get('font') or default), FONT_NAMES[default])
    for d in FONT_DIRS:
        p = d / name
        if p.is_file():
            return str(p)
    return ''


def get_font(path, px):
    px = max(4, int(round(px)))
    key = (path, px)
    if key not in _FONTS:
        try:
            _FONTS[key] = ImageFont.truetype(path, px) if path else ImageFont.load_default(px)
        except OSError:
            _FONTS[key] = ImageFont.load_default(px)
    return _FONTS[key]


# ------------------------------------------------------------------ the frame being drawn
class Ctx:
    def __init__(self, W, H, ss, t, frame, dur_s, fps):
        self.W, self.H, self.ss, self.t, self.frame, self.dur_s, self.fps = W, H, ss, t, frame, dur_s, fps
        self.S = min(W, H)
        self.canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    def px(self, p):
        return (float(p[0]) * self.W, float(p[1]) * self.H)

    def wpx(self, w):
        """A stroke width in thousandths of the short side, in pixels of this canvas."""
        return max(1.0, float(w) * self.S / 1000.0)


class Layer:
    """A local RGBA image for one element, positioned at (ox, oy) on the canvas."""

    def __init__(self, x0, y0, x1, y1, pad=0.0):
        self.ox, self.oy = int(math.floor(x0 - pad)), int(math.floor(y0 - pad))
        w = max(1, int(math.ceil(x1 + pad)) - self.ox)
        h = max(1, int(math.ceil(y1 + pad)) - self.oy)
        if w * h > 60_000_000:
            raise ValueError('an element is far larger than the canvas')
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)

    def p(self, pt):
        return (pt[0] - self.ox, pt[1] - self.oy)

    def pts(self, pts):
        return [(x - self.ox, y - self.oy) for x, y in pts]


def bbox_of(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def with_alpha(img, alpha):
    if alpha >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel('A').point(lambda v, a=alpha: int(v * a + 0.5)))
    return img


def composite(ctx, img, ox, oy, alpha=1.0):
    if alpha <= 0.002 or img is None:
        return
    img = with_alpha(img, alpha)
    x0, y0 = int(round(ox)), int(round(oy))
    x1, y1 = x0 + img.width, y0 + img.height
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(ctx.W, x1), min(ctx.H, y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    if (cx0, cy0, cx1, cy1) != (x0, y0, x1, y1):
        img = img.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    ctx.canvas.alpha_composite(img, dest=(cx0, cy0))


# ------------------------------------------------------------------ strokes
def _dash_on(arc, on, off, offset):
    if on <= 0:
        return True
    return ((arc + offset) % (on + off)) < on


def stroke(draw, pts, us, total, base_w, rgba, style, seed, dash=None, offset=0.0):
    """Draw a densified path (points in the layer, each with its arc-length fraction of the WHOLE path) in a hand.
    The width profile is the whole path's, so a stroke being drawn on does not change shape as it grows."""
    if len(pts) < 2:
        return
    r, g, b, A = rgba
    style = style if style in STROKE_STYLES else 'plain'
    on = off = 0.0
    if dash:
        if dash is True:
            on, off = 3.0 * base_w + 4, 2.4 * base_w + 4
        elif dash == 'dot':
            on, off = 1.0, 0.0
        else:
            on, off = float(dash[0]) * base_w, float(dash[1]) * base_w
    if style == 'plain' and not dash:
        w = max(1, int(round(base_w)))
        draw.line(pts, fill=rgba, width=w, joint='curve')
        if w >= 3:
            for (x, y) in (pts[0], pts[-1]):
                draw.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=rgba)
        return
    n = len(pts)
    if dash == 'dot':                     # round dots along the path
        gap = 2.6 * base_w + 2
        rr = max(0.8, base_w * 0.55)
        nxt = (-offset) % gap
        for i in range(n - 1):
            a0, a1 = us[i] * total, us[i + 1] * total
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            while nxt <= a1 and a1 > a0:
                if nxt >= a0:
                    f = (nxt - a0) / (a1 - a0)
                    x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                    draw.ellipse([x - rr, y - rr, x + rr, y + rr], fill=rgba)
                nxt += gap
            if nxt < a0:
                nxt += gap * math.ceil((a0 - nxt) / gap)
        return
    ph1, ph2 = _h(seed, 1) * 6.28, _h(seed, 2) * 6.28
    for i in range(n - 1):
        u = us[i]
        arc = u * total
        if dash and not _dash_on(arc, on, off, offset):
            continue
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        a = 1.0
        w = base_w
        if style in ('ink', 'brush'):
            taper = (0.35 + 0.65 * ease(u / 0.12, 'sine')) * (0.45 + 0.55 * ease((1 - u) / 0.16, 'sine'))
            wav = 1 + 0.08 * math.sin(arc / (9.0 * base_w + 1) + ph1) + 0.05 * math.sin(arc / (3.7 * base_w + 1) + ph2)
            w = base_w * taper * wav
            if style == 'brush':
                ang = math.atan2(y1 - y0, x1 - x0)
                w *= 0.45 + 0.8 * abs(math.sin(ang - 0.6))
        elif style == 'pencil':
            w = base_w * 0.85
            a = 0.55 + 0.45 * _h(seed, i)
        elif style == 'chalk':
            if _h(seed, i * 3 + 7) < 0.13:
                continue
            a = 0.45 + 0.55 * _h(seed, i)
            w = base_w * (0.8 + 0.35 * _h(seed, i + 99))
        elif style == 'marker':
            w = base_w
        col = (r, g, b, int(A * a))
        draw.line([(x0, y0), (x1, y1)], fill=col, width=max(1, int(round(w))))
        if style in ('ink', 'brush', 'marker') and w >= 2.5:
            rr = w / 2
            draw.ellipse([x1 - rr, y1 - rr, x1 + rr, y1 + rr], fill=col)
    if style == 'pencil':                 # a second, lighter pass a hair to the side: a sketched line
        k = 0.45 * base_w
        for i in range(0, n - 1, 1):
            if dash and not _dash_on(us[i] * total, on, off, offset):
                continue
            if _h(seed, i + 500) < 0.35:
                continue
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
            ox, oy = math.cos(ang) * k, math.sin(ang) * k
            draw.line([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy)], fill=(r, g, b, int(A * 0.35)),
                      width=max(1, int(round(base_w * 0.5))))
    if style == 'chalk':                  # a little dust beside the stroke
        for i in range(0, n, 4):
            if _h(seed, i + 900) < 0.5:
                continue
            x, y = pts[i]
            d = (_h(seed, i + 901) - 0.5) * base_w * 2.4
            e = (_h(seed, i + 902) - 0.5) * base_w * 2.4
            rr = max(0.6, base_w * 0.12)
            draw.ellipse([x + d - rr, y + e - rr, x + d + rr, y + e + rr], fill=(r, g, b, int(A * 0.5)))


def draw_head(draw, tip, ang, kind, rgba, size, base_w):
    if not kind or size <= 0.5:
        return
    x, y = tip
    if kind in ('open', 'filled', 'barb'):
        a1, a2 = ang + math.radians(152), ang - math.radians(152)
        p1 = (x + size * math.cos(a1), y + size * math.sin(a1))
        p2 = (x + size * math.cos(a2), y + size * math.sin(a2))
        if kind == 'filled':
            draw.polygon([tip, p1, p2], fill=rgba)
        elif kind == 'barb':
            for p in (p1, p2):
                mid = ((x + p[0]) / 2 + (p[1] - y) * 0.12, (y + p[1]) / 2 - (p[0] - x) * 0.12)
                draw.line([tip, mid, p], fill=rgba, width=max(2, int(round(base_w))), joint='curve')
        else:
            w = max(2, int(round(base_w)))
            draw.line([p1, tip, p2], fill=rgba, width=w, joint='curve')
            for q in (p1, p2, tip):
                draw.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=rgba)
    elif kind == 'dot':
        draw.ellipse([x - size / 2, y - size / 2, x + size / 2, y + size / 2], fill=rgba)
    elif kind == 'bar':
        perp = ang + math.pi / 2
        p1 = (x + size * 0.6 * math.cos(perp), y + size * 0.6 * math.sin(perp))
        p2 = (x - size * 0.6 * math.cos(perp), y - size * 0.6 * math.sin(perp))
        draw.line([p1, p2], fill=rgba, width=max(2, int(round(base_w))))


def path_render(ctx, el, pts, closed=False):
    """A stroked path element with its entrance (draw), exit (undraw), dashes, head, tail and pen tip."""
    t = ctx.t
    if len(pts) < 2:
        return None
    if el.get('smooth') and len(pts) > 2:
        pts = catmull(pts, 10, closed)
    elif closed:
        pts = list(pts) + [pts[0]]
    base_w = ctx.wpx(el.get('width', 4))
    rgba = hex_rgba(el.get('stroke', '#ffffff'), float(el.get('alpha', 1.0)))
    style = el.get('style', 'plain')
    i = el.get('in') or {}
    p1 = clamp(anim_p(i, t, 'inout' if el.get('type') in ('ring', 'mark', 'scribble') else 'out')) \
        if i.get('kind') == 'draw' else 1.0
    o = el.get('out') or {}
    p0 = 0.0
    if o.get('kind') == 'undraw':
        p0 = clamp(anim_p(o, t, 'in'))
    if p1 <= p0:
        return None
    head = el.get('head') or ('open' if el.get('type') == 'arrow' else None)
    tail = el.get('tail') if el.get('tail') and el.get('tail') != head else None
    hs = float(el.get('head_size', 3.2)) * base_w + 2 * ctx.ss
    pad = base_w * 2 + hs + 6
    lay = Layer(*bbox_of(pts), pad=pad)
    dense, acc = densify(lay.pts(pts), max(1.0, min(base_w * 0.45, 4.0 * ctx.ss)))
    total = acc[-1] or 1e-6
    vis, us = sub_path(dense, acc, p0, p1)
    seed = seed_of(el)
    offset = 0.0
    if el.get('march'):
        offset = -float(el['march']) * t * ctx.S / 1000.0
    stroke(lay.draw, vis, us, total, base_w, rgba, style, seed, el.get('dash'), offset)
    if head and el.get('type') in ('arrow', 'line', 'path'):
        follow = el.get('head_follow', True)
        if p1 >= 0.999 or follow:
            tip, ang = point_at(dense, acc, p1)
            back, _ = point_at(dense, acc, max(0.0, p1 - min(0.5, hs * 1.2 / total)))
            ang = math.atan2(tip[1] - back[1], tip[0] - back[0]) if math.dist(tip, back) > 1 else ang
            grow = clamp(p1 / 0.15) if i.get('kind') == 'draw' else 1.0
            draw_head(lay.draw, tip, ang, head, rgba, hs * grow, base_w)
    if tail and p0 <= 0.001 and p1 > 0.02:
        tip, ang = point_at(dense, acc, 0.0)
        nxt, _ = point_at(dense, acc, min(1.0, hs * 1.2 / total))
        draw_head(lay.draw, tip, math.atan2(tip[1] - nxt[1], tip[0] - nxt[0]), tail, rgba, hs, base_w)
    if el.get('tip') and i.get('kind') == 'draw' and 0.0 < p1 < 0.999:
        tip, _ = point_at(dense, acc, p1)
        rr = base_w * 0.7
        lay.draw.ellipse([tip[0] - rr, tip[1] - rr, tip[0] + rr, tip[1] + rr], fill=rgba)
    return lay


# ------------------------------------------------------------------ element renderers (each returns a Layer or None)
def r_line(ctx, el):
    return path_render(ctx, el, [ctx.px(p) for p in el['points']])


def _shape_box(ctx, el):
    cx, cy = ctx.px(el['center'])
    w, h = float(el.get('w', 0.1)) * ctx.S, float(el.get('h', 0.1)) * ctx.S
    return cx, cy, w, h


def r_shape(ctx, el):
    kind = el.get('type')
    cx, cy, w, h = _shape_box(ctx, el)
    anim = (el.get('in') or {}).get('kind', 'fade')
    sw = ctx.wpx(el.get('width', 4))
    fill = hex_rgba(el['fill'], float(el.get('fill_alpha', 1.0))) if el.get('fill') else None
    stroke_c = hex_rgba(el['stroke'], float(el.get('alpha', 1.0))) if el.get('stroke') else None
    lay = Layer(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, pad=sw * 2 + 4)
    box = [cx - w / 2 - lay.ox, cy - h / 2 - lay.oy, cx + w / 2 - lay.ox, cy + h / 2 - lay.oy]
    style = el.get('style', 'plain')
    radius = float(el.get('radius', 0) or 0) * ctx.S
    if style != 'plain' and stroke_c:
        if fill:
            if kind == 'ellipse':
                lay.draw.ellipse(box, fill=fill)
            else:
                lay.draw.rounded_rectangle(box, radius=radius, fill=fill)
        pts = _outline_points(kind, box, radius)
        dense, acc = densify(pts, max(1.0, sw * 0.45))
        stroke(lay.draw, dense, [a / (acc[-1] or 1) for a in acc], acc[-1], sw, stroke_c, style, seed_of(el))
    elif kind == 'ellipse':
        lay.draw.ellipse(box, fill=fill, outline=stroke_c, width=max(1, int(round(sw))))
    elif radius > 0:
        lay.draw.rounded_rectangle(box, radius=radius, fill=fill, outline=stroke_c, width=max(1, int(round(sw))))
    else:
        lay.draw.rectangle(box, fill=fill, outline=stroke_c, width=max(1, int(round(sw))))
    if anim == 'wipe':
        p = clamp(anim_p(el.get('in'), ctx.t))
        frm = (el.get('in') or {}).get('from', 'left')
        mask = Image.new('L', lay.img.size, 0)
        x0, y0, x1, y1 = box
        x0, y0, x1, y1 = x0 - sw, y0 - sw, x1 + sw, y1 + sw
        clip = {'left': [x0, y0, x0 + (x1 - x0) * p, y1], 'right': [x1 - (x1 - x0) * p, y0, x1, y1],
                'top': [x0, y0, x1, y0 + (y1 - y0) * p]}.get(frm, [x0, y1 - (y1 - y0) * p, x1, y1])
        ImageDraw.Draw(mask).rectangle(clip, fill=255)
        lay.img.putalpha(ImageChops.multiply(lay.img.getchannel('A'), mask))
    return lay


def _outline_points(kind, box, radius=0.0, n=72):
    x0, y0, x1, y1 = box
    if kind == 'ellipse':
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def r_polygon(ctx, el):
    pts = [ctx.px(p) for p in el['points']]
    sw = ctx.wpx(el.get('width', 2))
    lay = Layer(*bbox_of(pts), pad=sw * 2 + 4)
    lp = lay.pts(pts)
    fill = hex_rgba(el['fill'], float(el.get('fill_alpha', 1.0))) if el.get('fill') else None
    stroke_c = hex_rgba(el['stroke'], float(el.get('alpha', 1.0))) if el.get('stroke') else None
    style = el.get('style', 'plain')
    if fill:
        lay.draw.polygon(lp, fill=fill)
    if stroke_c:
        if style == 'plain':
            lay.draw.line(lp + [lp[0]], fill=stroke_c, width=max(1, int(round(sw))), joint='curve')
        else:
            dense, acc = densify(lp + [lp[0]], max(1.0, sw * 0.45))
            stroke(lay.draw, dense, [a / (acc[-1] or 1) for a in acc], acc[-1], sw, stroke_c, style, seed_of(el))
    return lay


SCRAMBLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def _text_lines(el):
    return str(el.get('text', '')).split('\n')


def text_block(ctx, el, text_override=None, at=None, size=None, color=None):
    """A block of words (one or more lines) drawn into a layer, with its entrance: typed, typed with a caret,
    decoded, written (revealed left to right), or whole. Optional paper plate behind and a stroke under it."""
    t = ctx.t
    x, y = ctx.px(at or el['at'])
    px = float(size if size is not None else el.get('size', 0.04)) * ctx.S
    font = get_font(font_path(el), px)
    fill = hex_rgba(color or el.get('fill', '#ffffff'), float(el.get('alpha', 1.0)))
    lines = (text_override if text_override is not None else str(el.get('text', ''))).split('\n')
    align = el.get('align', 'left')
    anchor = {'left': 'lm', 'center': 'mm', 'right': 'rm'}.get(align, 'lm')
    lh = px * float(el.get('line_height', 1.22))
    y_first = y - lh * (len(lines) - 1) / 2
    boxes = []
    for k, line in enumerate(lines):
        bb = font.getbbox(line or ' ', anchor=anchor)
        boxes.append((x + bb[0], y_first + k * lh + bb[1], x + bb[2], y_first + k * lh + bb[3]))
    X0, Y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    X1, Y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    plate = el.get('plate')
    pp = float((plate or {}).get('pad', 0.006)) * ctx.S if plate else 0.0
    sw = ctx.wpx(el.get('stroke_width', 3)) if el.get('stroke_color') else 0
    lay = Layer(X0, Y0, X1, Y1, pad=pp + sw + px * 0.5 + 4)
    if plate:
        pf = hex_rgba(plate.get('fill', '#f3ecd9'), float(plate.get('alpha', 0.9)))
        ps = hex_rgba(plate['stroke'], float(plate.get('stroke_alpha', 0.9))) if plate.get('stroke') else None
        rr = float(plate.get('radius', 0.004)) * ctx.S
        lay.draw.rounded_rectangle([X0 - pp - lay.ox, Y0 - pp - lay.oy, X1 + pp - lay.ox, Y1 + pp - lay.oy], radius=rr,
                                   fill=pf, outline=ps, width=max(1, int(round(ctx.wpx(plate.get('width', 1.5))))))
    kind = (el.get('in') or {}).get('kind', 'fade')
    p = clamp(anim_p(el.get('in'), t, 'linear')) if kind in ('type', 'typewriter', 'decode', 'write', 'reveal') else 1.0
    full = '\n'.join(lines)
    n_chars = len(full.replace('\n', ''))
    shown = n_chars if kind not in ('type', 'typewriter', 'decode') else int(round(n_chars * p))
    seed = seed_of(el)
    count = 0
    caret_at = None
    for k, line in enumerate(lines):
        ly = y_first + k * lh - lay.oy
        lx = x - lay.ox
        visible = line
        rest = ''
        if kind in ('type', 'typewriter'):
            take = max(0, min(len(line), shown - count))
            visible = line[:take]
        elif kind == 'decode':
            take = max(0, min(len(line), shown - count))
            visible = line[:take]
            tick = ctx.frame // 2
            rest = ''.join(ch if ch == ' ' else SCRAMBLE[int(_h(seed, (count + j) * 31 + tick) * len(SCRAMBLE))]
                           for j, ch in enumerate(line[take:], start=take))
        count += len(line)
        # left edge of the whole line, so a partly typed line stays where the whole line will be
        full_w = font.getlength(line)
        left = lx - full_w / 2 if align == 'center' else lx - full_w if align == 'right' else lx
        kw = {'stroke_width': max(1, int(round(sw))), 'stroke_fill': hex_rgba(el['stroke_color'], 1.0)} \
            if el.get('stroke_color') else {}
        if visible:
            lay.draw.text((left, ly), visible, font=font, fill=fill, anchor='lm', **kw)
        if rest:
            dim = (fill[0], fill[1], fill[2], int(fill[3] * 0.55))
            lay.draw.text((left + font.getlength(visible), ly), rest, font=font, fill=dim, anchor='lm', **kw)
        if kind == 'typewriter' and (count >= shown) and caret_at is None:
            caret_at = (left + font.getlength(visible), ly)
    if kind == 'typewriter' and caret_at is not None:
        start, dur = window(el['in'])
        if t < start + dur + 0.7 and int((t - start) * 2.2) % 2 == 0 or (start <= t < start + dur):
            cx, cy = caret_at
            lay.draw.rectangle([cx + px * 0.04, cy - px * 0.42, cx + px * 0.12, cy + px * 0.42], fill=fill)
    if kind in ('write', 'reveal') and p < 0.999:
        mask = Image.new('L', lay.img.size, 0)
        soft = px * 0.6
        edge = (X0 - pp - lay.ox) + (X1 - X0 + 2 * pp + soft) * p   # the soft edge passes the last letter by the end
        md = ImageDraw.Draw(mask)
        md.rectangle([0, 0, max(0, edge - soft), mask.height], fill=255)
        steps = 8
        for s in range(steps):
            xa = edge - soft + soft * s / steps
            md.rectangle([xa, 0, xa + soft / steps + 1, mask.height], fill=int(255 * (1 - s / steps)))
        lay.img.putalpha(ImageChops.multiply(lay.img.getchannel('A'), mask))
    ul = el.get('underline')
    if ul:
        start, dur = window(el.get('in') or {'start_s': 0, 'dur_s': 0.01})
        d0 = start + dur + float(ul.get('delay', 0.1))
        q = clamp(ease((t - d0) / float(ul.get('dur_s', 0.35)), 'out'))
        if q > 0:
            uw = ctx.wpx(ul.get('width', 5))
            yy = Y1 + uw * 1.2 - lay.oy + px * 0.08
            pts = [(X0 - lay.ox - px * 0.1, yy + px * 0.02), ((X0 + X1) / 2 - lay.ox, yy - px * 0.03),
                   (X1 - lay.ox + px * 0.15, yy + px * 0.01)]
            pts = catmull(pts, 12)
            dense, acc = densify(pts, max(1.0, uw * 0.45))
            vis, us = sub_path(dense, acc, 0.0, q)
            stroke(lay.draw, vis, us, acc[-1], uw, hex_rgba(ul.get('color', '#b0302a'), float(ul.get('alpha', 0.9))),
                   ul.get('style', 'brush'), seed + 7)
    return lay


def r_text(ctx, el):
    return text_block(ctx, el)


def fmt_number(v, el):
    dec = int(el.get('decimals', 0) or 0)
    s = f'{v:,.{dec}f}' if el.get('sep', True) else f'{v:.{dec}f}'
    if el.get('sep') not in (None, True, False, ','):
        s = s.replace(',', str(el['sep']))
    return f"{el.get('prefix', '')}{s}{el.get('suffix', '')}"


def counter_text(el, t):
    """The counter's words at t: it lands exactly on `to` at the end of its window (never a frame of 149,999 for
    150,000), and a big count moves in round steps (`step`, by default a thousandth of the range rounded to a power of
    ten once the range is 10,000 or more)."""
    a = el.get('in') or {}
    p = clamp(anim_p(a, t, a.get('ease', 'out3'))) if a else 1.0
    v0, v1 = float(el.get('from', 0)), float(el.get('to', 0))
    if p >= 0.985:
        return fmt_number(v1, el)
    span = abs(v1 - v0)
    step = float(el.get('step') or (10 ** max(0, len(str(int(span))) - 3) if span >= 10000 else 1))
    v = v0 + (v1 - v0) * p
    if not int(el.get('decimals', 0) or 0):
        v = round(v / step) * step
    return fmt_number(v, el)


def r_counter(ctx, el):
    return text_block(ctx, {**el, 'in': None}, text_override=counter_text(el, ctx.t))


def r_stamp(ctx, el):
    """A rubber stamp: words in a border, in a slightly broken ink."""
    x, y = ctx.px(el['at'])
    px = float(el.get('size', 0.05)) * ctx.S
    font = get_font(font_path(el, 'stencil'), px)
    col = hex_rgba(el.get('color', '#b0302a'), float(el.get('alpha', 0.92)))
    lines = _text_lines(el)
    lh = px * 1.05
    widths = [font.getlength(l) for l in lines]
    tw, th = max(widths), lh * len(lines)
    padx, pady = px * float(el.get('pad_x', 0.45)), px * float(el.get('pad_y', 0.3))
    shape = el.get('shape', 'rect')
    bw = ctx.wpx(el.get('border', 7))
    if shape == 'circle':
        rr = max(tw, th) / 2 + padx
        x0, y0, x1, y1 = x - rr, y - rr, x + rr, y + rr
    else:
        x0, y0, x1, y1 = x - tw / 2 - padx, y - th / 2 - pady, x + tw / 2 + padx, y + th / 2 + pady
    lay = Layer(x0, y0, x1, y1, pad=bw * 3 + 6)
    box = [x0 - lay.ox, y0 - lay.oy, x1 - lay.ox, y1 - lay.oy]
    if shape == 'circle':
        lay.draw.ellipse(box, outline=col, width=max(1, int(round(bw))))
        if el.get('double', True):
            k = bw * 2.2
            lay.draw.ellipse([box[0] + k, box[1] + k, box[2] - k, box[3] - k], outline=col,
                             width=max(1, int(round(bw * 0.45))))
    else:
        lay.draw.rounded_rectangle(box, radius=px * 0.12, outline=col, width=max(1, int(round(bw))))
        if el.get('double', False):
            k = bw * 2.0
            lay.draw.rounded_rectangle([box[0] + k, box[1] + k, box[2] - k, box[3] - k], radius=px * 0.08, outline=col,
                                       width=max(1, int(round(bw * 0.45))))
    for k, line in enumerate(lines):
        ly = y - th / 2 + lh * (k + 0.5) - lay.oy
        lay.draw.text((x - lay.ox, ly), line, font=font, fill=col, anchor='mm')
    grunge = float(el.get('grunge', 0.22))
    if grunge > 0:
        lay.img.putalpha(ImageChops.multiply(lay.img.getchannel('A'), _grunge(lay.img.size, seed_of(el), grunge,
                                                                              ctx.ss)))
    return lay


_GRUNGE = {}


def _grunge(size, seed, amount, ss):
    """A worn-ink mask: specks and thin patches where the stamp did not take."""
    key = (size, seed, round(amount, 3), ss)
    if key not in _GRUNGE:
        w, h = size
        sw, sh = max(1, w // (2 * ss)), max(1, h // (2 * ss))
        rng = random.Random(seed)
        small = Image.frombytes('L', (sw, sh), rng.randbytes(sw * sh))
        small = small.filter(ImageFilter.GaussianBlur(0.6))
        cut = int(255 * amount * 0.55)
        small = small.point(lambda v: 0 if v < cut else 255 if v > cut + 40 else int((v - cut) * 255 / 40))
        _GRUNGE[key] = small.resize((w, h), Image.Resampling.BILINEAR)
    return _GRUNGE[key]


def r_card(ctx, el):
    """A paper card (an index card, a file tag) with typed lines, an optional pin or tape on top."""
    cx, cy = ctx.px(el['center'])
    w, h = float(el.get('w', 0.2)) * ctx.S, float(el.get('h', 0.08)) * ctx.S
    lay = Layer(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, pad=ctx.S * 0.03)
    box = [cx - w / 2 - lay.ox, cy - h / 2 - lay.oy, cx + w / 2 - lay.ox, cy + h / 2 - lay.oy]
    fill = hex_rgba(el.get('fill', '#f3ecd9'), float(el.get('fill_alpha', 1.0)))
    edge = hex_rgba(el.get('stroke', '#8b7b62'), float(el.get('alpha', 1.0)))
    lay.draw.rounded_rectangle(box, radius=float(el.get('radius', 0.004)) * ctx.S, fill=fill, outline=edge,
                               width=max(1, int(round(ctx.wpx(el.get('width', 1.5))))))
    if el.get('rule', False):                      # a red rule under the title, as on an index card
        yy = box[1] + h * 0.36
        lay.draw.line([(box[0] + w * 0.04, yy), (box[2] - w * 0.04, yy)], fill=hex_rgba('#c8615a', 0.7),
                      width=max(1, int(round(ctx.wpx(1.4)))))
    lines = el.get('lines') or ([el['text']] if el.get('text') else [])
    if lines:
        ts = float(el.get('text_size', 0.03)) * ctx.S
        t0 = float((el.get('in') or {}).get('start_s', 0)) + float(el.get('text_delay', 0.25))
        tdur = float(el.get('text_dur_s', 0.6))
        q = clamp((ctx.t - t0) / tdur) if el.get('type_text', True) else 1.0
        total = sum(len(str(l)) for l in lines)
        shown = int(round(total * q))
        lh = ts * 1.25
        y_first = cy - lh * (len(lines) - 1) / 2
        count = 0
        for k, line in enumerate(lines):
            line = str(line)
            take = max(0, min(len(line), shown - count))
            count += len(line)
            f = get_font(font_path(el), ts * (1.12 if k == 0 and len(lines) > 1 else 1.0))
            fc = hex_rgba(el.get('text_color', '#2b1d14'), 1.0)
            align = el.get('align', 'center')
            lx = cx if align == 'center' else box[0] + lay.ox + w * 0.06
            full_w = f.getlength(line)
            left = lx - full_w / 2 if align == 'center' else lx
            if take:
                lay.draw.text((left - lay.ox, y_first + k * lh - lay.oy), line[:take], font=f, fill=fc, anchor='lm')
    if el.get('pin'):
        _draw_pin(lay.draw, (cx - lay.ox, box[1] + h * 0.08), ctx.S * 0.008, hex_rgba(el.get('pin_color', '#b0302a')))
    if el.get('tape'):
        tw, th = w * 0.32, ctx.S * 0.018
        tx, ty = cx - lay.ox, box[1]
        lay.draw.polygon([(tx - tw / 2, ty - th / 2), (tx + tw / 2, ty - th / 2 + th * 0.12),
                          (tx + tw / 2, ty + th / 2), (tx - tw / 2, ty + th / 2 - th * 0.1)],
                         fill=hex_rgba('#e8dcb5', 0.75))
    return lay


def _draw_pin(draw, at, r, rgba):
    x, y = at
    draw.ellipse([x - r * 0.45 + r * 0.5, y - r * 0.45 + r * 0.9, x + r * 0.45 + r * 0.5, y + r * 0.45 + r * 0.9],
                 fill=(0, 0, 0, 60))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=rgba)
    draw.ellipse([x - r * 0.45, y - r * 0.55, x - r * 0.05, y - r * 0.15], fill=(255, 255, 255, 150))


def r_pin(ctx, el):
    x, y = ctx.px(el['at'])
    r = float(el.get('size', 0.012)) * ctx.S / 2
    lay = Layer(x - r, y - r, x + r, y + r, pad=r * 2 + 4)
    _draw_pin(lay.draw, lay.p((x, y)), r, hex_rgba(el.get('color', '#b0302a'), float(el.get('alpha', 1.0))))
    return lay


def ring_points(ctx, el):
    cx, cy, w, h = _shape_box(ctx, el)
    turns = float(el.get('turns', 1.12))
    a0 = math.radians(float(el.get('start_deg', 200)))
    tilt = math.radians(float(el.get('tilt', -6)))
    wob = float(el.get('wobble', 0.05))
    seed = seed_of(el)
    n = max(24, int(64 * turns))
    pts = []
    for k in range(n + 1):
        f = k / n
        a = a0 + 2 * math.pi * turns * f
        grow = 1 + 0.05 * f
        wv = 1 + wob * (math.sin(a * 2 + _h(seed, 1) * 6) * 0.6 + math.sin(a * 3 + _h(seed, 2) * 6) * 0.4)
        rx, ry = w / 2 * grow * wv, h / 2 * grow * wv
        px_, py_ = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + px_ * math.cos(tilt) - py_ * math.sin(tilt), cy + px_ * math.sin(tilt) + py_ * math.cos(tilt)))
    return pts


def r_ring(ctx, el):
    el = {'style': 'brush', **el}
    return path_render(ctx, el, ring_points(ctx, el))


def r_mark(ctx, el):
    cx, cy = ctx.px(el['center'])
    s = float(el.get('size', 0.04)) * ctx.S
    kind = el.get('kind', 'tick')
    if kind == 'cross':
        a = [(cx - s / 2, cy - s / 2), (cx + s / 2, cy + s / 2)]
        b = [(cx + s / 2, cy - s / 2), (cx - s / 2, cy + s / 2)]
        e1 = {**el, 'type': 'line', 'id': f"{el.get('id')}-1", 'style': el.get('style', 'brush')}
        i = el.get('in') or {}
        if i.get('kind') == 'draw':
            st, du = window(i)
            e1['in'] = {**i, 'start_s': st, 'dur_s': du * 0.5}
            e2 = {**e1, 'id': f"{el.get('id')}-2", 'in': {**i, 'start_s': st + du * 0.5, 'dur_s': du * 0.5}}
        else:
            e2 = {**e1, 'id': f"{el.get('id')}-2"}
        l1 = path_render(ctx, e1, a)
        l2 = path_render(ctx, e2, b)
        return _merge_layers([l for l in (l1, l2) if l])
    pts = [(cx - s * 0.5, cy + s * 0.02), (cx - s * 0.12, cy + s * 0.42), (cx + s * 0.55, cy - s * 0.5)]
    return path_render(ctx, {**el, 'style': el.get('style', 'brush'), 'smooth': False}, pts)


def _merge_layers(layers):
    if not layers:
        return None
    x0 = min(l.ox for l in layers)
    y0 = min(l.oy for l in layers)
    x1 = max(l.ox + l.img.width for l in layers)
    y1 = max(l.oy + l.img.height for l in layers)
    out = Layer(x0, y0, x1, y1)
    for l in layers:
        out.img.alpha_composite(l.img, dest=(l.ox - out.ox, l.oy - out.oy))
    return out


def r_scribble(ctx, el):
    cx, cy, w, h = _shape_box(ctx, el)
    passes = int(el.get('passes', 7))
    seed = seed_of(el)
    pts = []
    for k in range(passes + 1):
        f = k / passes
        yy = cy - h / 2 + h * f + (_h(seed, k) - 0.5) * h * 0.08
        x_a = cx - w / 2 + (_h(seed, k + 50) - 0.5) * w * 0.08
        x_b = cx + w / 2 + (_h(seed, k + 90) - 0.5) * w * 0.08
        pts.append((x_a, yy) if k % 2 == 0 else (x_b, yy - h * 0.06))
    return path_render(ctx, {**el, 'style': el.get('style', 'ink'), 'smooth': True}, pts)


def r_highlight(ctx, el):
    cx, cy, w, h = _shape_box(ctx, el)
    seed = seed_of(el)
    pts = [(cx - w / 2, cy + (_h(seed, 1) - 0.5) * h * 0.12), (cx, cy + (_h(seed, 2) - 0.5) * h * 0.12),
           (cx + w / 2, cy + (_h(seed, 3) - 0.5) * h * 0.12)]
    e = {'stroke': '#f2d14a', 'alpha': 0.45, 'style': 'marker', **el, 'width': h * 1000 / ctx.S, 'smooth': True}
    if (e.get('in') or {}).get('kind') in (None, 'wipe'):
        e['in'] = {**(e.get('in') or {'start_s': 0, 'dur_s': 0.4}), 'kind': 'draw'}
    return path_render(ctx, e, pts)


def r_redact(ctx, el):
    cx, cy, w, h = _shape_box(ctx, el)
    i = el.get('in') or {}
    p = clamp(anim_p(i, ctx.t, 'out')) if i.get('kind') in ('draw', 'wipe') else 1.0
    lay = Layer(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, pad=h * 0.3 + 4)
    seed = seed_of(el)
    x0, x1 = cx - w / 2 - lay.ox, cx - w / 2 - lay.ox + w * p
    y0, y1 = cy - h / 2 - lay.oy, cy + h / 2 - lay.oy
    top = [(x0 + (x1 - x0) * k / 10, y0 + (_h(seed, k) - 0.5) * h * 0.1) for k in range(11)]
    bot = [(x0 + (x1 - x0) * k / 10, y1 + (_h(seed, k + 20) - 0.5) * h * 0.1) for k in range(11)]
    if x1 - x0 > 1:
        lay.draw.polygon(top + bot[::-1], fill=hex_rgba(el.get('color', '#151515'), float(el.get('alpha', 0.96))))
    return lay


ICON_SHAPES = {
    'plane': [[(0.5, 0.0), (0.36, 0.06), (0.08, 0.07), (-0.08, 0.46), (-0.2, 0.46), (-0.1, 0.07), (-0.34, 0.06),
               (-0.43, 0.2), (-0.5, 0.2), (-0.46, 0.0), (-0.5, -0.2), (-0.43, -0.2), (-0.34, -0.06), (-0.1, -0.07),
               (-0.2, -0.46), (-0.08, -0.46), (0.08, -0.07), (0.36, -0.06)]],
    'ship': [[(-0.5, -0.02), (0.5, -0.02), (0.38, 0.16), (-0.44, 0.16)],
             [(-0.2, -0.16), (0.14, -0.16), (0.14, -0.02), (-0.2, -0.02)],
             [(-0.08, -0.3), (0.0, -0.3), (0.0, -0.16), (-0.08, -0.16)]],
    'tank': [[(-0.5, 0.0), (0.42, 0.0), (0.5, 0.1), (0.42, 0.2), (-0.42, 0.2), (-0.5, 0.1)],
             [(-0.25, -0.16), (0.15, -0.16), (0.2, 0.0), (-0.3, 0.0)],
             [(0.12, -0.1), (0.58, -0.12), (0.58, -0.07), (0.12, -0.05)]],
    'envelope': [[(-0.5, -0.31), (0.5, -0.31), (0.5, 0.31), (-0.5, 0.31)]],
    'chevron': [[(0.5, 0.0), (-0.3, 0.38), (-0.12, 0.0), (-0.3, -0.38)]],
}


def _icon_polys(kind, at, ang, size, upright):
    flip = upright and math.cos(ang) < 0 and kind in ('ship', 'tank')
    if kind in ('envelope',):
        ang = 0.0
    if kind in ('ship', 'tank'):
        ang = math.pi if flip else 0.0 if upright else ang
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for poly in ICON_SHAPES.get(kind, []):
        pts = []
        for (u, v) in poly:
            if flip:
                v = -v                    # turned round, then mirrored so it stays the right way up
            pts.append((at[0] + (u * ca - v * sa) * size, at[1] + (u * sa + v * ca) * size))
        out.append(pts)
    return out


def r_travel(ctx, el):
    """An icon moving along a route (eased over its entrance window), turning with the route, with a trail behind."""
    pts = [ctx.px(p) for p in el['points']]
    if el.get('smooth', True) and len(pts) > 2:
        pts = catmull(pts, 10)
    size = float(el.get('icon_size', 0.03)) * ctx.S
    tw = ctx.wpx((el.get('trail') or {}).get('width', 2.4))
    lay = Layer(*bbox_of(pts), pad=size + tw * 3 + 8)
    dense, acc = densify(lay.pts(pts), max(1.0, 2.0 * ctx.ss))
    i = el.get('in') or {}
    p = clamp(anim_p(i, ctx.t, i.get('ease', 'inout'))) if i else 1.0
    o = el.get('out') or {}
    trail = el.get('trail')
    if trail and p > 0:
        vis, us = sub_path(dense, acc, 0.0, p)
        stroke(lay.draw, vis, us, acc[-1], tw, hex_rgba(trail.get('stroke', el.get('stroke', '#2b1d14')),
                                                         float(trail.get('alpha', 0.85))),
               trail.get('style', 'plain'), seed_of(el), trail.get('dash', [1.6, 1.8]))
    if o.get('kind') == 'arrive' and ctx.t >= window(o)[0]:
        return lay
    tip, ang = point_at(dense, acc, p)
    kind = el.get('icon', 'dot')
    fill = hex_rgba(el.get('fill', el.get('stroke', '#2b1d14')), float(el.get('alpha', 1.0)))
    edge = hex_rgba(el['stroke'], 1.0) if el.get('stroke') and el.get('fill') else None
    orient = el.get('orient', True)
    a = ang if orient else 0.0
    if kind == 'dot':
        lay.draw.ellipse([tip[0] - size / 2, tip[1] - size / 2, tip[0] + size / 2, tip[1] + size / 2], fill=fill,
                         outline=edge)
    else:
        polys = _icon_polys(kind, tip, a, size, el.get('upright', True))
        for k, poly in enumerate(polys):
            lay.draw.polygon(poly, fill=fill, outline=edge)
        if kind == 'envelope' and polys:
            (x0, y0), (x1, _), (_, y1) = polys[0][0], polys[0][1], polys[0][2]
            flap = hex_rgba(el.get('flap', '#8b7b62'), 1.0)
            lw = max(1, int(round(size * 0.05)))
            lay.draw.line([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + size * 0.04), (x1, y0)], fill=flap, width=lw)
            lay.draw.polygon(polys[0], outline=flap)
    if el.get('arrive_pulse') and p >= 0.999:
        st, du = window(i)
        q = clamp((ctx.t - st - du) / 0.6)
        if q < 1:
            rr = size * (0.6 + 1.6 * q)
            col = fill[:3] + (int(fill[3] * (1 - q)),)
            lay.draw.ellipse([tip[0] - rr, tip[1] - rr, tip[0] + rr, tip[1] + rr], outline=col,
                             width=max(1, int(round(tw))))
    return lay


def r_pulse(ctx, el):
    """Rings (or arcs: a radio signal) spreading from a point while the entrance window lasts."""
    cx, cy = ctx.px(el['center'])
    rmax = float(el.get('r_max', 0.08)) * ctx.S
    sw = ctx.wpx(el.get('width', 3))
    lay = Layer(cx - rmax, cy - rmax, cx + rmax, cy + rmax, pad=sw * 2 + 4)
    st, du = window(el.get('in') or {'start_s': 0, 'dur_s': ctx.dur_s})
    period = float(el.get('period_s', 1.2))
    rings = max(1, int(el.get('rings', 3)))
    col = hex_rgba(el.get('stroke', '#2b1d14'), float(el.get('alpha', 0.9)))
    arc = el.get('arc')
    c = lay.p((cx, cy))
    t = ctx.t
    for k in range(int(du / period * rings) + rings + 1):
        born = st + k * period / rings
        if born > st + du or born > t:
            continue
        q = (t - born) / period
        if q < 0 or q >= 1:
            continue
        r = rmax * (0.08 + 0.92 * ease(q, 'out'))
        a = (1 - q) ** 1.4
        w = max(1, int(round(sw * (1.0 - 0.5 * q))))
        cc = col[:3] + (int(col[3] * a),)
        box = [c[0] - r, c[1] - r, c[0] + r, c[1] + r]
        if arc:
            d, spread = float(arc[0]), float(arc[1])
            lay.draw.arc(box, d - spread / 2, d + spread / 2, fill=cc, width=w)
        else:
            lay.draw.ellipse(box, outline=cc, width=w)
    return lay


def r_hatch(ctx, el):
    """Hatching inside a shape (a region on a map), drawn line by line in a pencil hand."""
    pts = [ctx.px(p) for p in el['points']]
    x0, y0, x1, y1 = bbox_of(pts)
    sw = ctx.wpx(el.get('width', 1.6))
    lay = Layer(x0, y0, x1, y1, pad=sw * 2 + 4)
    poly = lay.pts(pts)
    mask = Image.new('L', lay.img.size, 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    hatch = Image.new('RGBA', lay.img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hatch)
    spacing = max(2.0, float(el.get('spacing', 0.012)) * ctx.S)
    col = hex_rgba(el.get('stroke', '#6f6f6c'), float(el.get('alpha', 0.6)))
    i = el.get('in') or {}
    p = clamp(anim_p(i, ctx.t, 'inout')) if i.get('kind') == 'draw' else 1.0
    seed = seed_of(el)
    W, H = lay.img.size
    diag = math.hypot(W, H)
    for a_deg in [float(el.get('angle', 35))] + ([float(el.get('angle', 35)) + 90] if el.get('cross') else []):
        a = math.radians(a_deg)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        n = int(diag / spacing) + 2
        shown = p * n
        for k in range(n):
            if k >= shown:
                break
            frac = clamp(shown - k)
            off = (k - n / 2) * spacing
            mx, my = W / 2 + nx * off, H / 2 + ny * off
            jit = (_h(seed, k) - 0.5) * spacing * 0.25
            a0 = (mx - dx * diag / 2 + nx * jit, my - dy * diag / 2 + ny * jit)
            a1 = (mx + dx * diag / 2 + nx * jit, my + dy * diag / 2 + ny * jit)
            a1 = (a0[0] + (a1[0] - a0[0]) * frac, a0[1] + (a1[1] - a0[1]) * frac)
            dense, acc = densify([a0, a1], max(1.0, sw * 1.6))
            stroke(hd, dense, [s / (acc[-1] or 1) for s in acc], acc[-1], sw, col, el.get('style', 'pencil'), seed + k)
    hatch.putalpha(ImageChops.multiply(hatch.getchannel('A'), mask))
    lay.img.alpha_composite(hatch)
    if el.get('outline'):
        stroke_c = hex_rgba(el.get('outline_color', el.get('stroke', '#6f6f6c')), float(el.get('alpha', 0.6)))
        lay.draw.line(poly + [poly[0]], fill=stroke_c, width=max(1, int(round(sw))))
    return lay


def r_string(ctx, el):
    """A string pinned from a to b, sagging, drawn out from a; it settles with a small swing once it reaches b."""
    a, b = ctx.px(el['a']), ctx.px(el['b'])
    sag = float(el.get('sag', 0.08))
    i = el.get('in') or {}
    st, du = window(i) if i else (0.0, 0.01)
    swing = 0.0
    if el.get('wobble', True) and ctx.t > st + du:
        q = ctx.t - st - du
        swing = 0.35 * math.exp(-q * 3.5) * math.sin(q * 14)
    L = math.dist(a, b)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + L * sag * (1 + swing))
    pts = [((1 - f) ** 2 * a[0] + 2 * (1 - f) * f * mid[0] + f * f * b[0],
            (1 - f) ** 2 * a[1] + 2 * (1 - f) * f * mid[1] + f * f * b[1]) for f in [k / 24 for k in range(25)]]
    return path_render(ctx, {'stroke': '#9a2a22', 'width': 1.8, **el, 'type': 'string'}, pts)


MORSE = {'.': 1, '-': 3}


def r_morse(ctx, el):
    """Morse marks (dots and dashes) appearing one by one, each lit for a moment as it is sent."""
    x, y = ctx.px(el['at'])
    d = float(el.get('size', 0.012)) * ctx.S
    code = str(el.get('code', ''))
    syms = [c for c in code if c in '.- /']
    xs, cur = [], 0.0
    for c in syms:
        if c in MORSE:
            xs.append((c, cur))
            cur += (MORSE[c] + 1) * d
        else:
            cur += 2 * d if c == ' ' else 4 * d
    if not xs:
        return None
    lay = Layer(x, y - d, x + cur, y + d, pad=d * 2 + 4)
    st, du = window(el.get('in') or {'start_s': 0, 'dur_s': 1})
    times = el.get('times')
    col = hex_rgba(el.get('color', '#2b1d14'), float(el.get('alpha', 1.0)))
    lit = hex_rgba(el.get('lit', '#d4a017'), 1.0)
    for k, (c, off) in enumerate(xs):
        born = float(times[k]) if times and k < len(times) else st + du * k / max(1, len(xs))
        if ctx.t < born:
            break
        glow = clamp(1 - (ctx.t - born) / 0.18)
        cc = tuple(int(col[j] + (lit[j] - col[j]) * glow) for j in range(4))
        x0 = x + off - lay.ox
        if c == '.':
            lay.draw.ellipse([x0, y - d / 2 - lay.oy, x0 + d, y + d / 2 - lay.oy], fill=cc)
        else:
            lay.draw.rounded_rectangle([x0, y - d * 0.4 - lay.oy, x0 + 3 * d, y + d * 0.4 - lay.oy], radius=d * 0.4,
                                       fill=cc)
    return lay


def r_group(ctx, el):
    layers = []
    for ch in sorted(el.get('children') or [], key=lambda e: e.get('z', 0)):
        got = render_element_layer(ctx, ch)
        if got:
            layers.append(got)
    return _merge_layers(layers)


RENDERERS = {'line': r_line, 'arrow': r_line, 'path': r_line, 'ellipse': r_shape, 'rect': r_shape, 'box': r_shape,
             'polygon': r_polygon, 'text': r_text, 'counter': r_counter, 'stamp': r_stamp, 'card': r_card,
             'ring': r_ring, 'mark': r_mark, 'scribble': r_scribble, 'highlight': r_highlight, 'redact': r_redact,
             'travel': r_travel, 'pulse': r_pulse, 'hatch': r_hatch, 'string': r_string, 'pin': r_pin,
             'morse': r_morse, 'group': r_group}


# ------------------------------------------------------------------ moves, effects and compositing
def key_values(el, t):
    """dx, dy (frame fractions), scale, rot (degrees, clockwise) and alpha from the element's keyframes at t; each
    property is interpolated between the keys that set it, the later key's ease shaping the way to it."""
    keys = el.get('keys')
    out = {'dx': 0.0, 'dy': 0.0, 'scale': 1.0, 'rot': 0.0, 'alpha': 1.0}
    if not keys:
        return out
    ks = sorted(keys, key=lambda k: float(k.get('t', 0)))
    for name in out:
        pts = [(float(k.get('t', 0)), float(k[name]), k.get('ease', 'inout')) for k in ks if name in k]
        if not pts:
            continue
        if t <= pts[0][0]:
            out[name] = pts[0][1]
        elif t >= pts[-1][0]:
            out[name] = pts[-1][1]
        else:
            for (t0, v0, _), (t1, v1, e1) in zip(pts, pts[1:]):
                if t0 <= t <= t1:
                    out[name] = v0 + (v1 - v0) * ease((t - t0) / max(1e-6, t1 - t0), e1)
                    break
    return out


def entrance_move(el, t, ctx):
    """The built-in moves of an entrance: (dx px, dy px, scale, rot deg)."""
    i = el.get('in') or {}
    kind = i.get('kind')
    if not kind:
        return 0.0, 0.0, 1.0, 0.0
    st, du = window(i)
    q = clamp((t - st) / du)
    if kind == 'grow':
        return 0.0, 0.0, max(0.0, ease(q, i.get('ease', 'out'))), 0.0
    if kind == 'pop':
        if q >= 1:
            return 0.0, 0.0, 1.0, 0.0
        return 0.0, 0.0, max(0.0, ease(q, 'back')), 0.0
    if kind == 'slam':
        s0 = float(i.get('from_scale', 2.2))
        if q < 0.7:
            s = s0 + (0.94 - s0) * (q / 0.7) ** 2
        else:
            s = 0.94 + 0.06 * ease((q - 0.7) / 0.3, 'out')
        return 0.0, 0.0, s, float(i.get('spin', 7.0)) * (1 - ease(q, 'out'))
    if kind == 'drop':
        e = ease(q, 'back')
        return 0.0, -(1 - e) * ctx.S * float(i.get('distance', 0.08)), 1.0, float(i.get('spin', 9.0)) * (1 - e)
    if kind == 'slide':
        e = ease(q, i.get('ease', 'out3'))
        d = (1 - e) * float(i.get('distance', 0.12))
        frm = i.get('from', 'left')
        dx = -d * ctx.W if frm == 'left' else d * ctx.W if frm == 'right' else 0.0
        dy = -d * ctx.H if frm == 'top' else d * ctx.H if frm == 'bottom' else 0.0
        return dx, dy, 1.0, 0.0
    if kind == 'rise':
        e = ease(q, 'out3')
        return 0.0, (1 - e) * ctx.S * float(i.get('distance', 0.02)), 1.0, 0.0
    if kind == 'flip':
        return 0.0, 0.0, max(0.02, ease(q, 'out')), 0.0
    return 0.0, 0.0, 1.0, 0.0


def exit_move(el, t, ctx):
    o = el.get('out') or {}
    if o.get('kind') != 'shrink':
        return 1.0
    st, du = window(o)
    return 1 - clamp(ease((t - st) / du, 'in'))


def affine(img, ox, oy, pivot, dx, dy, s, rot_deg, sx=1.0):
    """Move, scale (sx extra on x, for a flip) and rotate a layer about a pivot (canvas pixels)."""
    if abs(s - 1) < 1e-4 and abs(rot_deg) < 1e-3 and abs(sx - 1) < 1e-4:
        return img, ox + dx, oy + dy
    th = math.radians(rot_deg)
    c, sn = math.cos(th), math.sin(th)
    Px, Py = pivot
    corners = [(ox, oy), (ox + img.width, oy), (ox, oy + img.height), (ox + img.width, oy + img.height)]
    fw = []
    for (x, y) in corners:
        u, v = (x - Px) * s * sx, (y - Py) * s
        fw.append((Px + dx + u * c - v * sn, Py + dy + u * sn + v * c))
    X0, Y0, X1, Y1 = bbox_of(fw)
    X0, Y0 = math.floor(X0), math.floor(Y0)
    W, H = max(1, math.ceil(X1) - X0), max(1, math.ceil(Y1) - Y0)
    if W * H > 60_000_000:
        return img, ox + dx, oy + dy
    k = 1.0 / max(1e-6, s)
    kx = k / max(1e-6, sx)
    # output (u, v) -> canvas Q = (u + X0, v + Y0); w = Q - P - D; p = P + R(-th) w / s (x also / sx); local = p - o
    wx0, wy0 = X0 - Px - dx, Y0 - Py - dy
    a, b = c * kx, sn * kx
    d_, e = -sn * k, c * k
    cc = Px - ox + (c * wx0 + sn * wy0) * kx
    ff = Py - oy + (-sn * wx0 + c * wy0) * k
    pm = img.convert('RGBa').transform((W, H), Image.Transform.AFFINE, (a, b, cc, d_, e, ff),
                                       resample=Image.Resampling.BICUBIC)
    return pm.convert('RGBA'), X0, Y0


def effects(ctx, img, ox, oy, el):
    sh, gl = el.get('shadow'), el.get('glow')
    if not sh and not gl:
        return img, ox, oy
    S = ctx.S
    if sh is True:
        sh = {}
    if gl is True:
        gl = {}
    pad = 4
    if sh:
        pad = max(pad, int(float(sh.get('blur', 0.004)) * S * 3 + max(abs(float(sh.get('dx', 0.002))),
                                                                        abs(float(sh.get('dy', 0.004)))) * S) + 4)
    if gl:
        pad = max(pad, int(float(gl.get('blur', 0.006)) * S * 3) + 4)
    size = (img.width + 2 * pad, img.height + 2 * pad)
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    alpha = img.getchannel('A')
    if gl:
        g = Image.new('L', size, 0)
        g.paste(alpha, (pad, pad))
        g = g.filter(ImageFilter.GaussianBlur(float(gl.get('blur', 0.006)) * S))
        ga = float(gl.get('alpha', 0.6))
        g = g.point(lambda v: int(min(255, v * ga * 1.8)))
        col = Image.new('RGBA', size, hex_rgba(gl.get('color', '#fff2c0')))
        col.putalpha(g)
        out.alpha_composite(col)
    if sh:
        dxp, dyp = int(round(float(sh.get('dx', 0.002)) * S)), int(round(float(sh.get('dy', 0.004)) * S))
        g = Image.new('L', size, 0)
        g.paste(alpha, (pad + dxp, pad + dyp))
        g = g.filter(ImageFilter.GaussianBlur(float(sh.get('blur', 0.004)) * S))
        sa = float(sh.get('alpha', 0.35))
        g = g.point(lambda v: int(v * sa))
        col = Image.new('RGBA', size, hex_rgba(sh.get('color', '#000000')))
        col.putalpha(g)
        out.alpha_composite(col)
    out.alpha_composite(img, dest=(pad, pad))
    return out, ox - pad, oy - pad


def boil_px(el, ctx):
    if not el.get('boil'):
        return 0.0, 0.0
    amp = max(1.0, ctx.S * 0.0015)
    rnd = random.Random(seed_of(el) * 1000003 + ctx.frame // 3)
    return rnd.uniform(-amp, amp), rnd.uniform(-amp, amp)


def element_pivot(ctx, el, lay):
    if el.get('pivot'):
        return ctx.px(el['pivot'])
    for k in ('center', 'at'):
        if el.get(k):
            return ctx.px(el[k])
    return lay.ox + lay.img.width / 2, lay.oy + lay.img.height / 2


def render_element_layer(ctx, el):
    """One element at this frame as (Layer) with its moves, effects and opacity applied, or None."""
    a = presence(el, ctx.t)
    if a <= 0.002:
        return None
    kind = el.get('type')
    if kind not in RENDERERS:
        raise ValueError(f'unknown element type: {kind!r}')
    lay = RENDERERS[kind](ctx, el)
    if lay is None:
        return None
    kv = key_values(el, ctx.t)
    edx, edy, es, erot = entrance_move(el, ctx.t, ctx)
    bx, by = boil_px(el, ctx)
    s = kv['scale'] * es * exit_move(el, ctx.t, ctx)
    rot = float(el.get('rotate', 0.0)) + kv['rot'] + erot
    sx = 1.0
    if (el.get('in') or {}).get('kind') == 'flip':
        sx, s = s, kv['scale'] * exit_move(el, ctx.t, ctx)
    if s <= 0.002 or sx <= 0.002:
        return None
    dx = kv['dx'] * ctx.W + edx + bx
    dy = kv['dy'] * ctx.H + edy + by
    img, ox, oy = affine(lay.img, lay.ox, lay.oy, element_pivot(ctx, el, lay), dx, dy, s, rot, sx)
    img, ox, oy = effects(ctx, img, ox, oy, el)
    alpha = a * clamp(kv['alpha'])
    if alpha < 0.999:
        img = with_alpha(img, alpha)
    out = Layer.__new__(Layer)
    out.img, out.ox, out.oy = img, int(round(ox)), int(round(oy))
    out.draw = None
    return out


def render_element(draw, el, t, frame_idx, canvas_w, canvas_h, dur_s):
    """Kept for older callers: draw one element onto the image behind `draw` (no supersampling)."""
    ctx = Ctx(canvas_w, canvas_h, 1, t, frame_idx, dur_s, 30)
    ctx.canvas = getattr(draw, '_image', None) or ctx.canvas
    got = render_element_layer(ctx, el)
    if got:
        composite(ctx, got.img, got.ox, got.oy)


# ------------------------------------------------------------------ frames
def element_busy(el, t, fps):
    """Is this element changing around t (so the frame cannot be the previous one again)?"""
    if el.get('march'):
        return True
    h = 1.0 / fps
    wins = []
    i = el.get('in')
    if i:
        st, du = window(i)
        extra = 0.0
        kind = i.get('kind')
        if kind == 'typewriter':
            extra = 0.9
        if el.get('type') == 'card':
            extra = float(el.get('text_delay', 0.25)) + float(el.get('text_dur_s', 0.6)) + 0.1
        if el.get('type') == 'string':
            extra = 1.6
        if el.get('type') == 'travel' and el.get('arrive_pulse'):
            extra = 0.7
        if el.get('underline'):
            extra = max(extra, float(el['underline'].get('delay', 0.1)) + float(el['underline'].get('dur_s', 0.35)) + 0.1)
        if el.get('type') == 'pulse':
            extra = float(el.get('period_s', 1.2)) + 0.1
        if el.get('type') == 'morse' and el.get('times'):
            ts = [float(x) for x in el['times']]
            wins.append((min(ts) - h, max(ts) + 0.3))
        if el.get('type') == 'morse':
            extra = 0.3
        wins.append((st - h, st + du + extra + h))
    o = el.get('out')
    if o:
        st, du = window(o)
        wins.append((st - h, st + du + h))
    if el.get('keys'):
        ts = [float(k.get('t', 0)) for k in el['keys']]
        wins.append((min(ts) - h, max(ts) + h))
    if el.get('type') == 'group':
        return any(element_busy(c, t, fps) for c in el.get('children') or []) or any(a <= t <= b for a, b in wins)
    return any(a <= t <= b for a, b in wins)


def _boils(el):
    return bool(el.get('boil')) or any(_boils(c) for c in el.get('children') or [])


def frame_state(elements, t, fps, moving, frame=0):
    """A key for what this frame shows when nothing is moving: two frames with the same key are the same picture.
    None when something is animating (or the still moves under the drawing)."""
    if moving:
        return None
    if any(element_busy(e, t, fps) for e in elements):
        return None
    key = tuple(round(presence(e, t), 3) for e in elements)
    return key + ((frame // 3,) if any(_boils(e) for e in elements) else ())


def render_frame(spec, elements, t, frame_idx, cw, ch, ss, dur_s, fps):
    st = still_state(spec, t)
    els = [transform_element(e, *st) for e in elements] if st else elements
    ctx = Ctx(cw * ss, ch * ss, ss, t, frame_idx, dur_s, fps)
    for el in sorted(els, key=lambda e: e.get('z', 0)):
        try:
            got = render_element_layer(ctx, el)
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            raise ValueError(f"element {el.get('id', '?')!r} failed to render: {type(exc).__name__}: {exc}")
        if got:
            composite(ctx, got.img, got.ox, got.oy)
    img = ctx.canvas.reduce(ss) if ss > 1 else ctx.canvas
    soften = float(spec.get('soften', 0) or 0)
    if soften > 0:
        img = img.filter(ImageFilter.GaussianBlur(soften))
    grain = float(spec.get('grain', 0) or 0)
    if grain > 0:
        img.putalpha(ImageChops.multiply(img.getchannel('A'), _grain_tex(img.size, grain)))
    return img


_GRAIN = {}


def _grain_tex(size, amount):
    key = (size, round(amount, 3))
    if key not in _GRAIN:
        w, h = size
        rng = random.Random(1944)
        tex = Image.frombytes('L', (w // 2, h // 2), rng.randbytes((w // 2) * (h // 2)))
        lo = int(255 * (1 - amount))
        tex = tex.point(lambda v: lo + (255 - lo) * v // 255).resize(size, Image.Resampling.BILINEAR)
        _GRAIN[key] = tex
    return _GRAIN[key]


def load_spec(path):
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    try:
        cw, ch = (int(x) for x in spec['canvas'].lower().split('x'))
    except (KeyError, ValueError, AttributeError):
        error('spec.canvas must be like "1920x1080"')
    if not spec.get('elements'):
        error('spec.elements is empty: nothing to render')
    for el in _walk(spec['elements']):
        if el.get('type') not in RENDERERS:
            error(f"element {el.get('id', '?')!r} has an unknown type {el.get('type')!r}",
                  {'known': sorted(RENDERERS)})
    return spec, cw, ch


def _walk(elements):
    for e in elements or []:
        yield e
        if e.get('type') == 'group':
            yield from _walk(e.get('children'))


def cmd_render(args):
    spec, cw, ch = load_spec(args.spec)
    fps = float(spec.get('fps', 30))
    dur_s = float(spec['dur_s'])
    ss = int(args.supersample or spec.get('supersample') or SUPERSAMPLE)
    elements = spec['elements']
    n_frames = max(1, round(dur_s * fps))
    moving = motion_varies(spec)
    outp = Path(args.out).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    reused = 0
    with tempfile.TemporaryDirectory(prefix='draw_') as tmp:
        tmp = Path(tmp)
        last_state, last_file = None, None
        for i in range(n_frames):
            t = i / fps
            state = frame_state(elements, t, fps, moving, i)
            f = tmp / f'f{i:05d}.png'
            if state is not None and state == last_state and last_file is not None:
                shutil.copyfile(last_file, f)
                reused += 1
                continue
            try:
                img = render_frame(spec, elements, t, i, cw, ch, ss, dur_s, fps)
            except ValueError as exc:
                error(str(exc))
            img.save(f, compress_level=1)
            last_state, last_file = state, f
        if shutil.which('ffmpeg') is None:
            error('ffmpeg not found on PATH')
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(fps),
               '-i', str(tmp / 'f%05d.png'), '-c:v', 'qtrle', '-pix_fmt', 'argb', str(outp)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            error('ffmpeg encode failed', res.stderr[-800:])
    emit({'ok': True, 'file': str(outp), 'canvas': spec['canvas'], 'fps': fps, 'dur_s': dur_s, 'frames': n_frames,
          'frames_reused': reused, 'supersample': ss, 'elements': len(elements), 'follows_still_motion': moving,
          'codec': 'qtrle (alpha-preserving QuickTime Animation)',
          'note': 'Import as a video overlay on its own track in CapCut, at the drawing\'s shot start, for the shot\'s '
                  'length, over the still it explains. Look at it placed: `preview` composites frames over the still.'})


def still_frame(bg_path, cw, ch, state):
    """The still as the edit shows it at one moment: covering the canvas, scaled by s about the centre and shifted."""
    im = Image.open(bg_path).convert('RGB')
    s, x, y = state if state else (1.0, 0.0, 0.0)
    cover = max(cw / im.width, ch / im.height) * s
    w, h = max(1, round(im.width * cover)), max(1, round(im.height * cover))
    im = im.resize((w, h), Image.Resampling.LANCZOS)
    cx, cy = cw / 2 + x * cw / 2, ch / 2 - y * ch / 2
    canvas = Image.new('RGB', (cw, ch), (0, 0, 0))
    canvas.paste(im, (round(cx - w / 2), round(cy - h / 2)))
    return canvas


def cmd_preview(args):
    """Frames of the drawing over its still (as the edit frames the still at each moment), as one contact sheet."""
    spec, cw, ch = load_spec(args.spec)
    fps = float(spec.get('fps', 30))
    dur_s = float(spec['dur_s'])
    times = [float(x) for x in str(args.times).split(',') if x.strip()] if args.times else \
        [round(dur_s * k / 5, 2) for k in range(1, 6)]
    ss = int(args.supersample or 2)
    tiles = []
    for t in times:
        t = clamp(t, 0.0, max(0.0, dur_s - 1.0 / fps))
        frame = render_frame(spec, spec['elements'], t, int(t * fps), cw, ch, ss, dur_s, fps)
        if args.bg:
            base = still_frame(args.bg, cw, ch, still_state({**spec, 'framing_applied': False}, t) if
                               spec.get('still_motion') or spec.get('still_framing') else None).convert('RGBA')
        else:
            base = Image.new('RGBA', (cw, ch), (128, 128, 128, 255))
        base.alpha_composite(frame)
        tw = int(args.width)
        tile = base.convert('RGB').resize((tw, round(tw * ch / cw)), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(tile)
        lab = f't={t:.2f}s'
        d.rectangle([0, 0, 8 + 9 * len(lab), 20], fill=(0, 0, 0))
        d.text((4, 4), lab, fill=(255, 255, 0))
        tiles.append(tile)
    cols = max(1, min(int(args.cols), len(tiles)))
    rows = math.ceil(len(tiles) / cols)
    tw, th = tiles[0].size
    sheet = Image.new('RGB', (cols * tw + (cols - 1) * 6, rows * th + (rows - 1) * 6), (20, 20, 20))
    for k, tile in enumerate(tiles):
        sheet.paste(tile, ((k % cols) * (tw + 6), (k // cols) * (th + 6)))
    outp = Path(args.out).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(outp, quality=88)
    emit({'ok': True, 'file': str(outp), 'times': times, 'tiles': len(tiles), 'over_still': bool(args.bg)})


def readable_texts(spec):
    """The words a drawing shows for a viewer to read (labels, numbers, names, stamps, card lines): each with its size
    (a share of the frame's height), where its middle sits (y, a share of the frame's height, at the clip's start and
    end when the drawing follows a moving still), when it is on screen, and its element. Facts for the readability
    check (static_core timeline-check); nothing is judged here."""
    dur = float(spec.get('dur_s') or 0)
    out = []
    states = [still_state(spec, 0.0), still_state(spec, dur)]

    def ys_and_size(pt, size):
        ys, sz = [], size
        for st in states:
            if st:
                s, x, y = st
                ys.append(0.5 - y / 2 + (float(pt[1]) - 0.5) * s)
                sz = size * s
            else:
                ys.append(float(pt[1]))
        return ys, sz

    def add(el, text, at, size, extra_end=None):
        if not str(text).strip() or not at:
            return
        ys, sz = ys_and_size(at, float(size))
        i, o = el.get('in') or {}, el.get('out') or {}
        start = float(i.get('start_s', 0) or 0)
        end = float(o.get('start_s')) if o.get('start_s') is not None else dur
        out.append({'id': el.get('id'), 'type': el.get('type'), 'text': str(text), 'size': round(sz, 4),
                    'y': [round(v, 4) for v in ys], 'start_s': round(start, 3), 'end_s': round(end, 3)})
    for el in _walk(spec.get('elements')):
        k = el.get('type')
        if k == 'text':
            add(el, el.get('text', ''), el.get('at'), el.get('size', 0.04))
        elif k == 'counter':
            add(el, fmt_number(float(el.get('to', 0)), el), el.get('at'), el.get('size', 0.04))
        elif k == 'stamp':
            add(el, el.get('text', ''), el.get('at'), el.get('size', 0.05))
        elif k == 'card':
            lines = el.get('lines') or ([el['text']] if el.get('text') else [])
            for line in lines:
                add(el, line, el.get('center'), el.get('text_size', 0.03))
    return out


def cmd_texts(args):
    spec, _, _ = load_spec(args.spec)
    emit({'ok': True, 'texts': readable_texts(spec)})


def cmd_check(args):
    ok_ffmpeg = shutil.which('ffmpeg') is not None
    fonts = {k: bool(font_path({'font': k})) for k in FONT_NAMES}
    emit({'ok': ok_ffmpeg, 'pillow': True, 'ffmpeg': ok_ffmpeg, 'qtrle_available': True, 'supersample': SUPERSAMPLE,
          'element_types': list(ELEMENT_TYPES), 'stroke_styles': list(STROKE_STYLES), 'icons': list(ICONS),
          'fonts': fonts})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Render an animated drawing spec to a transparent overlay clip')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('render')
    p.add_argument('--spec', required=True, help='path to a drawing spec JSON file')
    p.add_argument('--out', required=True, help='output .mov path')
    p.add_argument('--supersample', type=int, default=None, help=f'draw at N times the canvas (default {SUPERSAMPLE})')
    p.set_defaults(func=cmd_render)
    p = sub.add_parser('preview', help='frames of the drawing over its still, as one contact sheet (JPG)')
    p.add_argument('--spec', required=True)
    p.add_argument('--out', required=True, help='the sheet (.jpg)')
    p.add_argument('--bg', default=None, help='the still under the drawing (framed as the spec says)')
    p.add_argument('--times', default=None, help='seconds into the clip, comma separated (default: five spread)')
    p.add_argument('--width', type=int, default=640, help='width of each tile')
    p.add_argument('--cols', type=int, default=3)
    p.add_argument('--supersample', type=int, default=None)
    p.set_defaults(func=cmd_preview)
    p = sub.add_parser('texts', help='the words the drawing shows, with their sizes, places and times')
    p.add_argument('--spec', required=True)
    p.set_defaults(func=cmd_texts)
    p = sub.add_parser('check')
    p.set_defaults(func=cmd_check)
    args = ap.parse_args()
    try:
        args.func(args)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as exc:
        error(type(exc).__name__ + ': ' + str(exc)[:800])
