#!/usr/bin/env python3
"""still_touchup.py - a local fix to a generated still, region by region, with its original kept (manual 04).

Image models write legible nonsense into titles, mastheads, plates and print, and an edit made with the still itself as the
reference keeps that lettering. When the still is otherwise right, the fix is local: each region is a pixel polygon with a
mode.
  erase   a median filter of `size` px over the region: thin strokes (letters) go, the ground's own colour stays. For a
          title or a plate on a fairly plain ground; on busy texture it leaves a smudge (look at the preview).
  soften  a Gaussian blur of `sigma` px with fresh paper grain (`grain`, std in 8-bit levels, default 2): print stays
          print, too small to read.
  text    paint a corrected character or word (`text`, `at` [x, y] centre, `size` px, `fill`, optional `font` file),
          for example a clock numeral the model doubled. Erase the wrong one first with an `erase` region.
  paint   a filled shape in one colour (`poly`, `fill`, softened by `soft` px like a drawn stroke): a pointer or a clock
          hand the model put in the wrong place, after an `erase` of the wrong one.
Masks are feathered (`feather` px) and can be shrunk (`shrink` px) so the region's own edges stay sharp.

  python still_touchup.py --run RUN --video N --spec SPEC.json            preview only (jobs/SHOT-touchup-preview.png)
  python still_touchup.py --run RUN --video N --spec SPEC.json --apply    write the still

SPEC: {"shot": "S014", "why": "...", "regions": [{"mode": "soften", "sigma": 4.5, "poly": [[x, y], ...]}, ...]}
--apply keeps the original in 60-visuals/video-NN/stills-history/ (never overwritten), records the edit in
60-visuals/video-NN/stills-postprocess.json and changes nothing else: the still keeps its provenance record (the shot it
was made for), and its look must be recorded again (content-review --pictures), because a look holds for an exact file.
Prints one JSON object on its last line. Exit 0 = done, 2 = refused (nothing written).
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_FONT = r'C:\Windows\Fonts\times.ttf'


def emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def _grain(shape, std, seed=7):
    """Paper grain for a softened area: fresh luminance noise. (Grain taken from the area itself would carry the very strokes
    the soften is meant to hide back into it.)"""
    n = np.random.default_rng(seed).normal(0.0, std, shape[:2])
    return np.repeat(n[:, :, None], shape[2], axis=2)


def apply_regions(im, regions):
    """The still with every region fixed, in order (a later region works on the earlier ones' result)."""
    out = im.convert('RGB').copy()
    for r in regions:
        mode = r.get('mode')
        if mode == 'text':
            layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
            font = ImageFont.truetype(r.get('font') or DEFAULT_FONT, int(r['size']))
            ImageDraw.Draw(layer).text(tuple(r['at']), str(r['text']), font=font, fill=r.get('fill', '#2b2b2b'), anchor='mm')
            layer = layer.filter(ImageFilter.GaussianBlur(float(r.get('soft', 0.6))))
            base = out.convert('RGBA')
            base.alpha_composite(layer)
            out = base.convert('RGB')
            continue
        if mode == 'paint':
            shape = [tuple(int(v) for v in p) for p in r['poly']]
            if len(shape) < 3:
                raise ValueError('a painted shape needs a polygon of at least three points')
            layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(shape, fill=r.get('fill', '#2b2b2b'))
            layer = layer.filter(ImageFilter.GaussianBlur(float(r.get('soft', 0.6))))
            base = out.convert('RGBA')
            base.alpha_composite(layer)
            out = base.convert('RGB')
            continue
        if mode not in ('erase', 'soften'):
            raise ValueError(f'unknown mode {mode!r} (erase, soften, text or paint)')
        poly = [tuple(int(v) for v in p) for p in r['poly']]
        if len(poly) < 3:
            raise ValueError('a region needs a polygon of at least three points')
        mask = Image.new('L', out.size, 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        if r.get('shrink'):
            mask = mask.filter(ImageFilter.MinFilter(2 * int(r['shrink']) + 1))
        mask = mask.filter(ImageFilter.GaussianBlur(float(r.get('feather', 4))))
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        pad = 40
        box = (max(0, min(xs) - pad), max(0, min(ys) - pad), min(out.width, max(xs) + pad), min(out.height, max(ys) + pad))
        part = out.crop(box)
        if mode == 'erase':
            size = int(r.get('size', 19)) | 1
            fixed = part.filter(ImageFilter.MedianFilter(size)).filter(ImageFilter.GaussianBlur(1.0))
        else:
            b = np.asarray(part.filter(ImageFilter.GaussianBlur(float(r.get('sigma', 4.0)))), dtype=float)
            fixed = Image.fromarray(np.clip(b + _grain(b.shape, float(r.get('grain', 2.0))), 0, 255).astype(np.uint8))
        full = out.copy()
        full.paste(fixed, box[:2])
        out = Image.composite(full, out, mask)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--run', required=True)
    ap.add_argument('--video', required=True, type=int)
    ap.add_argument('--spec', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    vis = Path(a.run) / '60-visuals' / f'video-{a.video:02d}'
    try:
        spec = json.loads(Path(a.spec).read_text(encoding='utf-8'))
        shot = str(spec['shot'])
        regions = spec['regions']
    except (OSError, ValueError, KeyError) as e:
        emit({'ok': False, 'error': f'spec: {e}'}, 2)
    if not str(spec.get('why') or '').strip():
        emit({'ok': False, 'error': 'the spec needs a "why": what was wrong in the still and what the fix does'}, 2)
    src = vis / 'stills' / f'{shot}.png'
    if not src.is_file():
        emit({'ok': False, 'error': f'no still {src}'}, 2)
    try:
        out = apply_regions(Image.open(src), regions)
    except (ValueError, KeyError, OSError) as e:
        emit({'ok': False, 'error': f'region: {e}'}, 2)
    if not a.apply:
        p = vis / 'jobs' / f'{shot}-touchup-preview.png'
        p.parent.mkdir(parents=True, exist_ok=True)
        out.save(p)
        emit({'ok': True, 'applied': False, 'preview': str(p), 'next': 'look at the preview at full size, then --apply'})
    hist_dir = vis / 'stills-history'
    hist_dir.mkdir(parents=True, exist_ok=True)
    k = 1
    while (hist_dir / f'{shot}-before-touchup-{k}.png').exists():
        k += 1
    hist = hist_dir / f'{shot}-before-touchup-{k}.png'
    shutil.copy2(src, hist)
    out.save(src)
    rec = vis / 'stills-postprocess.json'
    d = json.loads(rec.read_text(encoding='utf-8')) if rec.is_file() else {
        'note': 'Local fixes made to generated stills after generation (still_touchup.py); each keeps its original in '
                'stills-history/.', 'edits': []}
    d['edits'].append({'shot_id': shot, 'file': str(src.relative_to(Path(a.run))).replace('\\', '/'),
                       'original': str(hist.relative_to(Path(a.run))).replace('\\', '/'), 'why': spec['why'],
                       'regions': regions, 'at': datetime.now(timezone.utc).isoformat(timespec='seconds')})
    rec.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    emit({'ok': True, 'applied': True, 'file': str(src), 'original': str(hist),
          'next': 'record the still\'s look again (content-review --pictures): the earlier look was for the old file'})


if __name__ == '__main__':
    main()
