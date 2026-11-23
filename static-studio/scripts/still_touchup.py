#!/usr/bin/env python3
"""still_touchup.py - a small crisp mark painted onto a generated still, with its original kept (manual 04).

Nothing in a still is ever blurred, erased or covered (the user, 2026-11-23: "never blur anything, if there's
something to be blurred then instruct in the image generation so that it avoids that thing"). Made-up lettering, a
place name on a map, a badge or a seal emblem is kept out by the frame prompt and the still is generated again; the
`erase` and `soften` modes this tool had (a median filter and a Gaussian blur) are refused. What is left paints
something the picture needs, on top, in its own crisp stroke, never over a fault (a wrong numeral, hand or word is
remade with the still):
  text    a character or word (`text`, `at` [x, y] centre, `size` px, `fill`, optional `font` file).
  paint   a filled shape in one colour (`poly`, `fill`, its edge softened by `soft` px like a drawn stroke).

  python still_touchup.py --run RUN --video N --spec SPEC.json            preview only (jobs/SHOT-touchup-preview.png)
  python still_touchup.py --run RUN --video N --spec SPEC.json --apply    write the still
  python still_touchup.py --run RUN --video N --replace FILE --shot S014 --kind user_supplied|edited --why "..." [--apply]
          a picture the user supplies, or a legitimate edit made elsewhere (a crop, a colour correction):
          checked (it opens, the still's shape, enough pixels), kept beside the original, recorded, looked at
          again. Legitimate editing comes in this way; hiding something never does.

SPEC: {"shot": "S059", "why": "...", "regions": [{"mode": "text", "text": "3", "at": [x, y], "size": 50}, ...]}
--apply keeps the original in 60-visuals/video-NN/stills-history/ (never overwritten), records the edit in
60-visuals/video-NN/stills-postprocess.json and moves the still's provenance fingerprint to the touched file, so the
change is known as this recorded one (any other change to a still is refused by timeline-check); the still keeps its
shot, and its look must be recorded again (content-review --pictures), because a look holds for an exact file.
Prints one JSON object on its last line. Exit 0 = done, 2 = refused (nothing written).
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_FONT = r'C:\Windows\Fonts\times.ttf'


def emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


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
        if mode in ('erase', 'soften'):
            raise ValueError(f'{mode!r} is refused: nothing in a still is blurred, erased or covered (the user, '
                             f'2026-11-23). Write the frame prompt so the thing is not made, and generate the '
                             f'still again (manual 04)')
        raise ValueError(f'unknown mode {mode!r} (text or paint)')
    return out


def keep_original(vis, src, shot, tag):
    hist_dir = vis / 'stills-history'
    hist_dir.mkdir(parents=True, exist_ok=True)
    k = 1
    while (hist_dir / f'{shot}-before-{tag}-{k}.png').exists():
        k += 1
    hist = hist_dir / f'{shot}-before-{tag}-{k}.png'
    shutil.copy2(src, hist)
    return hist


def move_fingerprint(vis, src):
    """The still's provenance fingerprint follows a recorded change, so timeline-check knows it (anything else that
    changes a still after the generator made it is refused there: manual 04)."""
    prov_p = vis / 'stills-provenance.json'
    if not prov_p.is_file():
        return False
    prov = json.loads(prov_p.read_text(encoding='utf-8'))
    me, hit = os.path.normcase(str(src.resolve())), False
    for k, v in (prov.get('images') or {}).items():
        if os.path.normcase(str(Path(k).resolve())) == me and isinstance(v, dict) and v.get('file_sha256'):
            v['file_sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
            v['changed_after_generation_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
            hit = True
    if hit:
        prov_p.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding='utf-8')
    return hit


def record_edit(vis, entry):
    rec = vis / 'stills-postprocess.json'
    d = json.loads(rec.read_text(encoding='utf-8')) if rec.is_file() else {
        'note': 'Changes made to stills after generation (still_touchup.py): crisp marks and recorded replacements; '
                'each keeps its original in stills-history/.', 'edits': []}
    d['edits'].append({**entry, 'at': datetime.now(timezone.utc).isoformat(timespec='seconds')})
    rec.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')


def supersede_touchups(vis, shot, why):
    """Earlier blur or erase touch-ups of a still stop applying once a checked replacement stands in their place."""
    rec = vis / 'stills-postprocess.json'
    if not rec.is_file():
        return []
    d = json.loads(rec.read_text(encoding='utf-8'))
    done = []
    for e in d.get('edits') or []:
        if (isinstance(e, dict) and str(e.get('shot_id')) == shot and not e.get('superseded_at')
                and any((r or {}).get('mode') in ('erase', 'soften') for r in e.get('regions') or [])):
            e['superseded_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
            e['superseded_by'] = why
            done.append(e.get('at'))
    if done:
        rec.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    return done


def replace_still(a, vis):
    """A replacement picture for a still: one the user supplies, or a legitimate edit made elsewhere (a crop, a colour
    or contrast correction, a retouch that makes the picture right). Checked (it opens, it has the still's shape and
    enough pixels), kept beside the original, recorded with what it is and why, and looked at again before use. Never
    a way to blur or cover something the picture should not show: that is generated again (manual 04)."""
    shot, why = str(a.shot or '').strip(), str(a.why or '').strip()
    if not shot or not a.kind or len(why.split()) < 4:
        emit({'ok': False, 'error': '--replace needs --shot, --kind (user_supplied or edited) and --why (what the new '
                                    'picture is and why it replaces the still)'}, 2)
    src = vis / 'stills' / f'{shot}.png'
    if not src.is_file():
        emit({'ok': False, 'error': f'no still {src}'}, 2)
    new_path = Path(a.replace).expanduser()
    try:
        new = Image.open(new_path)
        new.load()
        new = new.convert('RGB')
    except (OSError, ValueError) as e:
        emit({'ok': False, 'error': f'the replacement does not open as a picture: {e}'}, 2)
    cur = Image.open(src)
    want, got = cur.width / cur.height, new.width / new.height
    if abs(got - want) > 0.02 * want:
        emit({'ok': False, 'error': f'the replacement is {new.width}x{new.height}, the still {cur.width}x{cur.height}: '
                                    'crop it to the still\'s shape first (it would be stretched)'}, 2)
    if new.width < 0.75 * cur.width:
        emit({'ok': False, 'error': f'the replacement is {new.width} px wide, the still {cur.width}: too small for the '
                                    'frame it fills'}, 2)
    if new.size != cur.size:
        new = new.resize(cur.size, Image.Resampling.LANCZOS)
    if not a.apply:
        p = vis / 'jobs' / f'{shot}-replace-preview.png'
        p.parent.mkdir(parents=True, exist_ok=True)
        new.save(p)
        emit({'ok': True, 'applied': False, 'preview': str(p), 'next': 'look at it at full size, then --apply'})
    hist = keep_original(vis, src, shot, 'replace')
    new.save(src)
    move_fingerprint(vis, src)
    gone = supersede_touchups(vis, shot, f'replaced by a checked {a.kind} picture: {why}')
    record_edit(vis, {'shot_id': shot, 'touchups_retired': len(gone), 'file': str(src.relative_to(Path(a.run))).replace('\\', '/'),
                      'original': str(hist.relative_to(Path(a.run))).replace('\\', '/'), 'why': why,
                      'mode': 'replace', 'kind': a.kind, 'from': str(new_path.resolve())})
    emit({'ok': True, 'applied': True, 'file': str(src), 'original': str(hist),
          'next': 'record the still\'s look again (content-review --pictures): the earlier look was for the old file'})


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--run', required=True)
    ap.add_argument('--video', required=True, type=int)
    ap.add_argument('--spec', help='crisp marks: {"shot", "why", "regions": [...]}')
    ap.add_argument('--replace', help='a replacement picture for the still: user-supplied, or an edit made elsewhere')
    ap.add_argument('--shot', help='with --replace: the still it replaces (S014)')
    ap.add_argument('--kind', choices=('user_supplied', 'edited'), help='with --replace: where the picture comes from')
    ap.add_argument('--why', help='with --replace: what the new picture is and why it replaces the still')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    vis = Path(a.run) / '60-visuals' / f'video-{a.video:02d}'
    if a.replace:
        replace_still(a, vis)
    if not a.spec:
        emit({'ok': False, 'error': 'give --spec (crisp marks) or --replace (a recorded replacement)'}, 2)
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
    hist = keep_original(vis, src, shot, 'touchup')
    out.save(src)
    move_fingerprint(vis, src)
    record_edit(vis, {'shot_id': shot, 'file': str(src.relative_to(Path(a.run))).replace('\\', '/'),
                      'original': str(hist.relative_to(Path(a.run))).replace('\\', '/'), 'why': spec['why'],
                      'regions': regions})
    emit({'ok': True, 'applied': True, 'file': str(src), 'original': str(hist),
          'next': 'record the still\'s look again (content-review --pictures): the earlier look was for the old file'})


if __name__ == '__main__':
    main()
