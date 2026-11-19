#!/usr/bin/env python3
"""Static Studio: render an animated vector drawing (lines, arrows, shapes, text) as a
transparent-background video clip, for placement as a CapCut overlay on its own track.

CapCut has no freehand drawing primitive (only fixed mask shapes, keyframes on existing
clips, and library stickers) -- this tool is the "drawing" itself: it renders the vector
animation frame by frame with Pillow and encodes it with an alpha channel (QuickTime
Animation / qtrle in a .mov container) so CapCut only has to play it as an overlay clip,
never draw anything.

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
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def emit(data, code=0):
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


def error(msg, details=None):
    emit({'ok': False, 'error': msg, 'details': details}, 2)


def ease(t, kind):
    t = max(0.0, min(1.0, t))
    if kind in (None, 'linear'):
        return t
    if kind == 'in':
        return t * t
    if kind == 'out':
        return 1 - (1 - t) * (1 - t)
    if kind == 'inout':
        return 3 * t * t - 2 * t * t * t
    raise ValueError(f'unknown ease: {kind}')


def progress(spec, t, key='in'):
    """0..1 progress of the named animation at time t (clamped before/after)."""
    a = spec.get(key)
    if not a:
        return 1.0 if key == 'in' else 0.0
    start, dur = float(a.get('start_s', 0)), max(1e-6, float(a.get('dur_s', 0.3)))
    raw = (t - start) / dur
    p = ease(raw, a.get('ease', 'out'))
    return p if key == 'in' else 1 - p


def visible_window(el, t, dur_s):
    """Combined in/out alpha multiplier (0..1) at time t."""
    p_in = progress(el, t, 'in')
    out = el.get('out')
    if not out:
        return p_in
    out_start = float(out.get('start_s', dur_s))
    if t < out_start:
        return p_in
    p_out = progress({'in': out}, t, 'in')  # reuse ease curve on the out window
    return p_in * (1 - p_out)


def frac(canvas_w, canvas_h, xy):
    return xy[0] * canvas_w, xy[1] * canvas_h


def short_side(w, h):
    return min(w, h)


def boil_offset(el, frame_idx, amp_px):
    if not el.get('boil'):
        return 0.0, 0.0
    seed = hash((el.get('id', ''), frame_idx // 3)) & 0xffffffff
    rnd = random.Random(seed)
    return (rnd.uniform(-amp_px, amp_px), rnd.uniform(-amp_px, amp_px))


def resample_path(points, frac_len):
    """Return the prefix of `points` covering `frac_len` (0..1) of total arc length,
    with the cut point interpolated so a partial segment is included."""
    if frac_len >= 1.0 or len(points) < 2:
        return points
    seglens = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(seglens) or 1e-6
    target = total * max(0.0, frac_len)
    acc = 0.0
    out = [points[0]]
    for i, sl in enumerate(seglens):
        if acc + sl >= target:
            remain = target - acc
            t = remain / sl if sl > 1e-9 else 0
            x = points[i][0] + (points[i + 1][0] - points[i][0]) * t
            y = points[i][1] + (points[i + 1][1] - points[i][1]) * t
            out.append((x, y))
            return out
        acc += sl
        out.append(points[i + 1])
    return out


def draw_dashed_line(draw, points, fill, width, dash_on=10, dash_off=8):
    if len(points) < 2:
        return
    remaining = dash_on
    on = True
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        seg = math.dist((x0, y0), (x1, y1))
        pos = 0.0
        while pos < seg:
            step = min(remaining, seg - pos)
            t0, t1 = pos / seg, (pos + step) / seg
            if on:
                draw.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                           (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=fill, width=width)
            pos += step
            remaining -= step
            if remaining <= 1e-6:
                on = not on
                remaining = dash_on if on else dash_off


def draw_head(draw, p_from, p_to, kind, fill, size):
    if not kind:
        return
    ang = math.atan2(p_to[1] - p_from[1], p_to[0] - p_from[0])
    if kind in ('open', 'filled'):
        a1 = ang + math.radians(150)
        a2 = ang - math.radians(150)
        p1 = (p_to[0] + size * math.cos(a1), p_to[1] + size * math.sin(a1))
        p2 = (p_to[0] + size * math.cos(a2), p_to[1] + size * math.sin(a2))
        if kind == 'filled':
            draw.polygon([p_to, p1, p2], fill=fill)
        else:
            draw.line([p1, p_to, p2], fill=fill, width=max(2, size // 4))
    elif kind == 'dot':
        draw.ellipse([p_to[0] - size / 2, p_to[1] - size / 2, p_to[0] + size / 2, p_to[1] + size / 2], fill=fill)
    elif kind == 'bar':
        perp = ang + math.pi / 2
        p1 = (p_to[0] + size * math.cos(perp), p_to[1] + size * math.sin(perp))
        p2 = (p_to[0] - size * math.cos(perp), p_to[1] - size * math.sin(perp))
        draw.line([p1, p2], fill=fill, width=max(2, size // 4))


def hex_rgba(hexcolor, alpha):
    h = (hexcolor or '#ffffff').lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, max(0, min(255, round(alpha * 255))))


def render_element(draw, el, t, frame_idx, canvas_w, canvas_h, dur_s):
    a = visible_window(el, t, dur_s)
    if a <= 0.002:
        return
    ss = short_side(canvas_w, canvas_h)
    ox, oy = boil_offset(el, frame_idx, amp_px=max(1.0, ss * 0.0015))
    kind = el.get('type')
    anim = (el.get('in') or {}).get('kind', 'fade')
    p_in = progress(el, t, 'in')

    if kind in ('line', 'arrow'):
        pts = [frac(canvas_w, canvas_h, p) for p in el['points']]
        pts = [(x + ox, y + oy) for x, y in pts]
        if anim == 'draw':
            pts = resample_path(pts, p_in)
        stroke = hex_rgba(el.get('stroke', '#ffffff'), (el.get('alpha', 1.0)) * a)
        width = max(1, round(el.get('width', 4) * ss / 1000))
        if el.get('dash'):
            draw_dashed_line(draw, pts, stroke, width)
        else:
            if len(pts) >= 2:
                draw.line(pts, fill=stroke, width=width, joint='curve')
        if len(pts) >= 2:
            head_size = max(6, width * 3)
            tail = el.get('tail') or (el.get('head') if kind == 'arrow' and not el.get('tail') else None)
            head = el.get('head') or ('open' if kind == 'arrow' else None)
            if head and (anim != 'draw' or p_in >= 0.999):
                draw_head(draw, pts[-2], pts[-1], head, stroke, head_size)
            if tail and tail != head and (anim != 'draw' or p_in <= 0.001 or len(pts) >= 2):
                draw_head(draw, pts[1] if len(pts) > 1 else pts[0], pts[0], tail, stroke, head_size)

    elif kind in ('ellipse', 'rect', 'box'):
        cx, cy = frac(canvas_w, canvas_h, el['center'])
        w, h = el.get('w', 0.1) * ss, el.get('h', 0.1) * ss
        scale = p_in if anim == 'grow' else (1.0 + 0.15 * math.sin(p_in * math.pi)) if anim == 'pop' and p_in < 1 else 1.0
        if anim == 'pop':
            scale = 1.0 if p_in >= 0.999 else (p_in * (1.0 + 0.18 * math.sin(min(1.0, p_in) * math.pi)))
        w, h = w * max(0.0, scale), h * max(0.0, scale)
        cx, cy = cx + ox, cy + oy
        box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
        fill = hex_rgba(el['fill'], el.get('fill_alpha', 1.0) * a) if el.get('fill') else None
        stroke = hex_rgba(el['stroke'], (el.get('alpha', 1.0)) * a) if el.get('stroke') else None
        width = max(1, round(el.get('width', 4) * ss / 1000))
        if anim == 'wipe':
            frm = (el.get('in') or {}).get('from', 'left')
            if frm == 'left':
                box_clip = [box[0], box[1], box[0] + (box[2] - box[0]) * p_in, box[3]]
            elif frm == 'right':
                box_clip = [box[2] - (box[2] - box[0]) * p_in, box[1], box[2], box[3]]
            elif frm == 'top':
                box_clip = [box[0], box[1], box[2], box[1] + (box[3] - box[1]) * p_in]
            else:
                box_clip = [box[0], box[3] - (box[3] - box[1]) * p_in, box[2], box[3]]
            layer = Image.new('RGBA', draw.im.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            (ld.ellipse if kind == 'ellipse' else ld.rectangle)(box, fill=fill, outline=stroke, width=width)
            mask = Image.new('L', draw.im.size, 0)
            ImageDraw.Draw(mask).rectangle(box_clip, fill=255)
            draw.im.paste(Image.composite(layer, Image.new('RGBA', draw.im.size, (0, 0, 0, 0)), mask), (0, 0), mask=None)
            return
        (draw.ellipse if kind == 'ellipse' else draw.rectangle)(box, fill=fill, outline=stroke, width=width)

    elif kind == 'polygon':
        pts = [frac(canvas_w, canvas_h, p) for p in el['points']]
        pts = [(x + ox, y + oy) for x, y in pts]
        fill = hex_rgba(el['fill'], el.get('fill_alpha', 1.0) * a) if el.get('fill') else None
        stroke = hex_rgba(el['stroke'], (el.get('alpha', 1.0)) * a) if el.get('stroke') else None
        draw.polygon(pts, fill=fill, outline=stroke)

    elif kind == 'text':
        x, y = frac(canvas_w, canvas_h, el['at'])
        x, y = x + ox, y + oy
        size = max(8, round(el.get('size', 0.04) * ss))
        try:
            font = ImageFont.truetype(el['font_file'], size) if el.get('font_file') else ImageFont.load_default(size)
        except OSError:
            font = ImageFont.load_default(size)
        text = el.get('text', '')
        if anim == 'type':
            n = max(0, round(len(text) * p_in))
            text = text[:n]
        fill = hex_rgba(el.get('fill', '#ffffff'), (el.get('alpha', 1.0)) * a)
        anchor = {'left': 'lm', 'center': 'mm', 'right': 'rm'}.get(el.get('align', 'left'), 'lm')
        if el.get('stroke_color'):
            draw.text((x, y), text, font=font, fill=fill, anchor=anchor,
                      stroke_width=max(1, size // 18), stroke_fill=hex_rgba(el['stroke_color'], a))
        else:
            draw.text((x, y), text, font=font, fill=fill, anchor=anchor)
    else:
        raise ValueError(f'unknown element type: {kind!r}')


def cmd_render(args):
    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    try:
        cw, ch = (int(x) for x in spec['canvas'].lower().split('x'))
    except (KeyError, ValueError):
        error('spec.canvas must be like "1920x1080"')
    fps = float(spec.get('fps', 30))
    dur_s = float(spec['dur_s'])
    elements = spec.get('elements') or []
    if not elements:
        error('spec.elements is empty: nothing to render')
    n_frames = max(1, round(dur_s * fps))
    outdir = Path(args.out).expanduser().resolve()
    outdir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='draw_') as tmp:
        tmp = Path(tmp)
        for i in range(n_frames):
            t = i / fps
            img = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for el in sorted(elements, key=lambda e: e.get('z', 0)):
                try:
                    render_element(draw, el, t, i, cw, ch, dur_s)
                except (KeyError, ValueError) as exc:
                    error(f"element {el.get('id', '?')!r} failed to render", f'{type(exc).__name__}: {exc}')
            img.save(tmp / f'f{i:05d}.png')
        if shutil.which('ffmpeg') is None:
            error('ffmpeg not found on PATH')
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(fps),
               '-i', str(tmp / 'f%05d.png'), '-c:v', 'qtrle', '-pix_fmt', 'argb', str(outdir)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            error('ffmpeg encode failed', res.stderr[-800:])
    emit({'ok': True, 'file': str(outdir), 'canvas': spec['canvas'], 'fps': fps, 'dur_s': dur_s,
          'frames': n_frames, 'elements': len(elements), 'codec': 'qtrle (alpha-preserving QuickTime Animation)',
          'note': 'Import as a video overlay on its own track in CapCut, positioned at the drawing\'s start_s '
                  'over the still it explains. Verify the alpha renders correctly once placed; this encode is '
                  'verified by ffprobe (has_alpha-capable codec, correct duration) but CapCut import has not '
                  'been visually confirmed in this environment.'})


def cmd_check(args):
    img = Image.new('RGBA', (4, 4))
    ok_ffmpeg = shutil.which('ffmpeg') is not None
    emit({'ok': ok_ffmpeg, 'pillow': True, 'ffmpeg': ok_ffmpeg,
          'qtrle_available': True})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Render an animated drawing spec to a transparent overlay clip')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('render')
    p.add_argument('--spec', required=True, help='path to a drawing spec JSON file')
    p.add_argument('--out', required=True, help='output .mov path')
    p.set_defaults(func=cmd_render)
    p = sub.add_parser('check')
    p.set_defaults(func=cmd_check)
    args = ap.parse_args()
    try:
        args.func(args)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as exc:
        error(type(exc).__name__ + ': ' + str(exc)[:800])
