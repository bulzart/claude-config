#!/usr/bin/env python3
"""Static Studio: deterministic intake + runtime/coverage gates for long-form YouTube.

No app/service daemon, GUI automation, generative model, or subscription required for
checks. Paid text-to-speech is opt-in with an explicit --execute flag. Input references
are always read-only. The Claude Code command directs the creative/CapCut work.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

VIDEO_EXT = {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v', '.ts'}
DOC_EXT = {'.txt', '.md', '.pdf', '.docx', '.rtf', '.json'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 'static-youtube-longform-v1'
DEFAULT_MIN_LONGFORM = 480


def emit(data, code=0):
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    if code:
        sys.exit(code)


def error(message, details=None):
    emit({'ok': False, 'error': message, 'details': details}, 2)


def read_json(path, required=False):
    try:
        obj = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(obj, dict):
            raise ValueError('expected JSON object')
        return obj
    except (OSError, ValueError) as exc:
        if required:
            error('Cannot read JSON', {'file': str(path), 'reason': str(exc)})
        return {}


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + '.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def elevenlabs_key():
    # PC adapter: this PC's pipelines keep the ElevenLabs key in ELEVEN_API_KEY; the package's own name is still read first.
    return os.environ.get('ELEVENLABS_API_KEY') or os.environ.get('ELEVEN_API_KEY') or ''


def run_cmd(cmd, timeout=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False,
                                encoding='utf-8', errors='replace')
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'{cmd[0]} execution failed: {exc}') from exc
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or f'{cmd[0]} error')[-1000:])
    return result.stdout


def probe(path):
    j = json.loads(run_cmd(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                            '-of', 'json', str(path)], timeout=35))
    streams = j.get('streams', [])
    v = next((s for s in streams if s.get('codec_type') == 'video'), None)
    a = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    fmt = j.get('format', {})
    dur = float(fmt.get('duration') or (v or a or {}).get('duration') or 0)
    fps = (v or {}).get('avg_frame_rate', '0/0')
    try:
        numer, denom = [int(x) for x in fps.split('/')]
        fps = round(numer / denom, 3) if denom else None
    except (ValueError, AttributeError):
        fps = None
    return {'duration_s': round(dur, 3), 'has_video': v is not None,
            'has_audio': a is not None, 'width': (v or {}).get('width'),
            'height': (v or {}).get('height'), 'fps': fps,
            'video_codec': (v or {}).get('codec_name'), 'audio_codec': (a or {}).get('codec_name')}


def run_folder(args):
    rd = Path(args.run).expanduser().resolve()
    st = read_json(rd / 'state.json', required=True)
    if st.get('schema') != SCHEMA:
        error('Not a Static Studio run; do not overwrite a legacy run', str(rd))
    return rd, st


def quick_fingerprint(path):
    h = hashlib.sha256()
    size = path.stat().st_size
    with path.open('rb') as f:
        h.update(f.read(256 * 1024))
        if size > 512 * 1024:
            f.seek(max(0, size - 256 * 1024))
            h.update(f.read(256 * 1024))
    return h.hexdigest()[:20] + ':' + str(size)


def cmd_doctor(args):
    checks = {'python': sys.version.split()[0], 'ffmpeg': shutil.which('ffmpeg') is not None,
              'ffprobe': shutil.which('ffprobe') is not None,
              'elevenlabs_api_key_set': bool(elevenlabs_key())}
    try:
        import faster_whisper  # noqa
        checks['faster_whisper'] = True
    except ImportError:
        checks['faster_whisper'] = False
    try:
        from PIL import Image  # noqa
        checks['pillow'] = True
    except ImportError:
        checks['pillow'] = False
    for mod, name in (('numpy', 'numpy'), ('cv2', 'opencv'), ('librosa', 'librosa'), ('soundfile', 'soundfile')):
        try:
            __import__(mod)
            checks[name] = True
        except ImportError:
            checks[name] = False
    checks['av_profile_ready'] = all(checks.get(k) for k in ('numpy', 'opencv', 'librosa', 'soundfile', 'pillow'))
    emit({'ok': checks['ffmpeg'] and checks['ffprobe'], 'checks': checks,
          'note': 'Whisper is required for reference audio analysis; av-profile (watch sheets, delivery measurements) '
                  'needs numpy, opencv, librosa, soundfile and pillow; image/CapCut/TTS tools are checked separately.'})


def cmd_init(args):
    ref = Path(args.references).expanduser().resolve()
    if not ref.is_dir():
        error('References directory missing', str(ref))
    root = Path(args.workspace).expanduser().resolve() if args.workspace else ROOT / 'runs'
    if ref == root or ref in root.parents or root in ref.parents:
        error('The run folder must be separate from source references; sources remain read-only.')
    slug = re.sub(r'[^a-z0-9-]+', '-', args.slug.lower()).strip('-')[:45] or 'narrative'
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
    rd = root / (stamp + '-' + slug)
    index = 2
    while rd.exists():
        rd = root / (stamp + '-' + slug + '-' + str(index))
        index += 1
    for d in ['00-inventory', '10-media', '20-analysis/cards', '20-analysis/cohorts',
              '30-research', '40-plans', '50-audio', '60-visuals', '70-edit', '80-deliverables', 'logs']:
        (rd / d).mkdir(parents=True, exist_ok=True)
    st = {'schema': SCHEMA, 'run_id': rd.name, 'created_at': now(), 'source_references': str(ref),
          'stage': 'intake', 'selected_niche': None, 'video_count': 0,
          'format': {'platform': 'YouTube long-form', 'aspect': '16:9', 'width': 1920, 'height': 1080, 'fps': 30},
          'analysis_fps': args.fps, 'min_longform_s': args.min_longform,
          'notes': 'Static only. Agents invent new subjects within the chosen niche; references teach form, not copied content.'}
    write_json(rd / 'state.json', st)
    (rd / 'todo.md').write_text('# Static Studio run\n\n- [ ] Inventory and prepare references (av-profile: watch them as films)\n- [ ] Analyze evidence and choose niche\n- [ ] Lock comparable long-form length\n- [ ] Research the story; creative direction: approaches, treatments, blind read, direction-lock (before the script)\n- [ ] Beat directions and script; cold read with every finding answered; plan-check\n- [ ] Record complete narration (calibration part first: pace and delivery per beat)\n- [ ] Design and assemble image-led edit (shot-check, retime-shots)\n- [ ] Export; final watch review answered; release-check\n', encoding='utf-8')
    emit({'ok': True, 'run': str(rd), 'next': 'scan --run "' + str(rd) + '"'})


def cmd_clone(args):
    src, previous = run_folder(argparse.Namespace(run=args.from_run))
    import tempfile
    tmp = argparse.Namespace(references=previous['source_references'], workspace=args.workspace,
                            slug=args.slug, fps=previous.get('analysis_fps', 5),
                            min_longform=previous.get('min_longform_s', DEFAULT_MIN_LONGFORM))
    # Make a new independent Static run; do not share mutable audio or output files.
    ref = Path(tmp.references)
    if not ref.is_dir():
        error('Source references no longer exist; cannot safely clone analysis.', str(ref))
    root = Path(tmp.workspace).expanduser().resolve() if tmp.workspace else ROOT / 'runs'
    slug = re.sub(r'[^a-z0-9-]+', '-', tmp.slug.lower()).strip('-')[:45] or 'clone'
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
    rd = root / (stamp + '-' + slug)
    idx = 2
    while rd.exists():
        rd = root / (stamp + '-' + slug + '-' + str(idx)); idx += 1
    for d in ['00-inventory', '10-media', '20-analysis/cards', '20-analysis/cohorts',
              '30-research', '40-plans', '50-audio', '60-visuals', '70-edit', '80-deliverables', 'logs']:
        (rd / d).mkdir(parents=True, exist_ok=True)
    st = {k:v for k,v in previous.items() if k not in ('selected_niche','video_count','stage','created_at','run_id')}
    st.update({'selected_niche': None, 'video_count': 0, 'stage': 'reference_analysis_complete',
               'run_id': rd.name, 'created_at': now(), 'cloned_from': str(src)})
    write_json(rd/'state.json', st)
    for oldrel in ['00-inventory/references.json', '20-analysis/cohorts/index.json']:
        old = src/oldrel
        if old.is_file():
            target = rd/oldrel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(old, target)
    for card in (src/'20-analysis/cards').glob('V*.json'):
        shutil.copy2(card, rd/'20-analysis/cards'/card.name)
    (rd/'todo.md').write_text('# Cloned Static analysis\n\n- [ ] prepare + av-profile the references again (frames and transcripts are not cloned)\n- [ ] Choose niche and lock a new video length\n- [ ] Creative direction and lock before the script; cold read; then produce (create-video.md D-G)\n', encoding='utf-8')
    emit({'ok': True, 'run': str(rd), 'source_run': str(src), 'note': 'Only analyses are reused. Source media is read-only; production assets remain independent.'})


def cmd_scan(args):
    rd, st = run_folder(args)
    ref = Path(st['source_references'])
    old = read_json(rd / '00-inventory/references.json')
    prev_by_path = {x['relative_path']: x for x in old.get('items', [])}
    items = []
    counters = {'video': max([int(x['id'][1:]) for x in old.get('items', []) if x['id'].startswith('V')] or [0]),
                'image': max([int(x['id'][1:]) for x in old.get('items', []) if x['id'].startswith('I')] or [0]),
                'document': max([int(x['id'][1:]) for x in old.get('items', []) if x['id'].startswith('D')] or [0])}
    seen = {}
    errors = []
    for path in sorted(ref.rglob('*')):
        if not path.is_file() or path.name.startswith('.'):
            continue
        suffix = path.suffix.lower()
        kind = ('video' if suffix in VIDEO_EXT else 'image' if suffix in IMAGE_EXT else
                'document' if suffix in DOC_EXT else None)
        if not kind:
            continue
        rel = path.relative_to(ref).as_posix()
        oldrow = prev_by_path.get(rel)
        if oldrow and oldrow.get('kind') == kind:
            ident = oldrow['id']
        else:
            counters[kind] += 1
            ident = {'video': 'V', 'image': 'I', 'document': 'D'}[kind] + f'{counters[kind]:03d}'
        row = {'id': ident, 'relative_path': rel, 'kind': kind, 'source_path': str(path),
               'size_bytes': path.stat().st_size, 'fingerprint': quick_fingerprint(path)}
        if kind == 'video':
            try:
                row.update(probe(path))
                if row['duration_s'] <= 0 or not row['has_video']:
                    errors.append({'id': ident, 'error': 'video has no valid duration/stream'})
            except (RuntimeError, ValueError) as exc:
                errors.append({'id': ident, 'error': str(exc)[:240]})
        dedup_key = (kind, row['fingerprint'])
        if dedup_key in seen:
            row['duplicate_of'] = seen[dedup_key]
        else:
            seen[dedup_key] = ident
        items.append(row)
    inv = {'schema': SCHEMA, 'references_dir': str(ref), 'scanned_at': now(), 'items': items, 'errors': errors}
    write_json(rd / '00-inventory/references.json', inv)
    emit({'ok': not errors, 'run': str(rd), 'counts': {k: sum(x['kind'] == k for x in items)
          for k in counters}, 'duplicates': sum('duplicate_of' in x for x in items), 'errors': errors,
          'source_read_only': True}, 2 if errors else 0)


def transcribe(path, outpath, model_name, device, compute_type):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError('faster-whisper unavailable: pip install faster-whisper')
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segs, info = model.transcribe(str(path), beam_size=5, word_timestamps=True, vad_filter=True,
                                  condition_on_previous_text=False)
    rows = []
    for s in segs:
        rows.append({'start_s': round(s.start, 3), 'end_s': round(s.end, 3), 'text': s.text.strip(),
                     'words': [{'start_s': round(w.start, 3), 'end_s': round(w.end, 3), 'text': w.word}
                               for w in s.words or []]})
    result = {'status': 'transcribed', 'source': str(path), 'model': model_name,
              'language': info.language, 'duration_s': round(info.duration, 2),
              'segments': rows, 'warning': 'Whisper is fallible: verify names, numbers and hard-to-hear claims by listening.'}
    write_json(outpath, result)
    outpath.with_suffix('.txt').write_text('\n'.join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}" for s in rows), encoding='utf-8')
    return len(rows)


def cmd_prepare(args):
    rd, st = run_folder(args)
    inv = read_json(rd / '00-inventory/references.json', required=True)
    ids = set(args.ids.split(',')) if args.ids else None
    chosen = [v for v in inv['items'] if v.get('kind') == 'video' and not v.get('duplicate_of')
              and (ids is None or v['id'] in ids)]
    if not chosen:
        error('No matching unique reference videos. Run scan first.')
    fps = args.fps or st.get('analysis_fps', 5)
    if not 0 < fps <= 60:
        error('FPS must be between 0 and 60')
    estimate = sum(v.get('duration_s') or 0 for v in chosen) * fps
    if args.dry_run:
        emit({'ok': True, 'videos': len(chosen), 'fps': fps, 'estimated_sample_frames': int(estimate),
              'per_video': {x['id']: x['duration_s'] for x in chosen},
              'note': '5 fps is the baseline; use --full-fps for a specific clip when true frame-by-frame detail is necessary.'})
        return
    results = []
    failures = []
    for v in chosen:
        dest = rd / '10-media' / v['id']
        dest.mkdir(parents=True, exist_ok=True)
        src = Path(v['source_path'])
        target = dest / ('all-frames' if args.full_fps else 'sampled-frames')
        target.mkdir(exist_ok=True)
        manifest = dest / 'preparation.json'
        pold = read_json(manifest)
        signature = {'fingerprint': v['fingerprint'], 'fps': 'original' if args.full_fps else fps,
                     'width': args.width, 'whisper_model': args.whisper_model}
        details = {'id': v['id'], 'source': str(src), 'signature': signature, 'updated_at': now()}
        try:
            if not (pold.get('signature') == signature and list(target.glob('*.jpg'))):
                for existing in target.glob('*.jpg'):
                    existing.unlink()
                vf = f"scale={args.width}:-2" if args.full_fps else f"fps={fps},scale={args.width}:-2"
                run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src), '-vf', vf,
                         '-q:v', '5', str(target / '%07d.jpg')], timeout=None)
            details['sampled_frames'] = len(list(target.glob('*.jpg')))
            details['sample_fps'] = v.get('fps') if args.full_fps else fps
            details['full_frame_extraction'] = bool(args.full_fps)
            # Non-native-FPS still indexes are NOMINAL sample slots, not exact PTS.
            # Require direct video inspection for precise scene-cut timing.
            sample_rate = details['sample_fps'] or fps
            if not args.full_fps and sample_rate:
                frame_index_path = dest / 'frame-index.json'
                frame_names = sorted(x.name for x in target.glob('*.jpg'))
                frame_index = {'source_id': v['id'], 'mode': 'nominal_sample_time',
                               'warning': 'Approximate sample time from output slot; not source-native PTS.',
                               'fps': sample_rate,
                               'frames': [{'file': name, 'approx_s': round(i/sample_rate, 3)}
                                          for i, name in enumerate(frame_names)]}
                write_json(frame_index_path, frame_index)
                details['frame_index'] = str(frame_index_path)
            if not args.skip_whisper and v.get('has_audio'):
                tp = dest / 'transcript.json'
                if not (pold.get('signature') == signature and read_json(tp).get('status') == 'transcribed'):
                    details['transcript_segments'] = transcribe(src, tp, args.whisper_model, args.device, args.compute_type)
                else:
                    details['transcript_segments'] = len(read_json(tp).get('segments', []))
            else:
                details['transcript_status'] = 'skipped_by_user' if args.skip_whisper else 'no_audio_stream'
            write_json(manifest, details)
            results.append(details)
        except (RuntimeError, ValueError, OSError) as exc:
            failures.append({'id': v['id'], 'error': str(exc)[:450]})
    emit({'ok': not failures, 'processed': results, 'failed': failures}, 2 if failures else 0)


def cards_inventory(rd):
    inv = read_json(rd / '00-inventory/references.json', required=True)
    vids = {x['id']: x for x in inv.get('items', []) if x.get('kind') == 'video' and not x.get('duplicate_of')}
    return vids


def card_set(rd):
    vids = cards_inventory(rd)
    cards = {}
    issues = []
    for ident, v in vids.items():
        path = rd / '20-analysis/cards' / f'{ident}.json'
        c = read_json(path)
        if not c:
            issues.append(ident + ': missing analytical card')
            continue
        if c.get('reference_id') != ident:
            issues.append(ident + ': card/reference ID mismatch')
        if not c.get('niches') or not isinstance(c.get('niches'), list):
            issues.append(ident + ': missing niches list')
        if not c.get('story_form'):
            issues.append(ident + ': missing story_form')
        if not c.get('viewer_experience') or not isinstance(c.get('viewer_experience'), list):
            issues.append(ident + ': missing timed viewer_experience moments')
        cards[ident] = c
    return vids, cards, issues


def cmd_cohorts(args):
    rd, st = run_folder(args)
    vids, cards, issues = card_set(rd)
    groups = {}
    for vid, card in cards.items():
        duration = vids[vid].get('duration_s')
        if not duration:
            continue
        cid = str(card.get('cohort_id') or '').strip().lower()
        if cid:
            groups.setdefault(('__cohort__:' + cid, ''), []).append((vid, duration))
        for niche in card.get('niches') or []:
            family = (str(niche).strip().lower(), str(card.get('story_form') or '').strip().lower())
            groups.setdefault(family, []).append((vid, duration))
    summaries = []
    for (key, form), members in sorted(groups.items()):
        vals = sorted(t for _, t in members)
        med = statistics.median(vals)
        entry = {'references': [ident for ident, _ in members],
                 'n': len(vals), 'min_s': round(vals[0], 1), 'median_s': round(med, 1),
                 'mean_s': round(statistics.mean(vals), 1), 'max_s': round(vals[-1], 1),
                 'spread_ratio': round(vals[-1] / vals[0], 2),
                 'longform_refs': [id for id, t in members if t >= st['min_longform_s']],
                 'warning': ('MIXED_RUNTIME_FAMILIES_SELECT_COMPARABLE_IDS' if vals[-1]/vals[0] > 1.8 else None)}
        if key.startswith('__cohort__:'):
            entry['cohort_id'] = key[len('__cohort__:'):]
        else:
            entry['niche'] = key
            entry['story_form'] = form
        summaries.append(entry)
    write_json(rd / '20-analysis/cohorts/index.json', {'groups': summaries, 'unresolved': issues, 'at': now()})
    emit({'ok': not issues, 'groups': summaries, 'missing_cards_or_fields': issues,
          'warning': 'Patterns and duration must be selected from comparable references, not averaged across unrelated niches.'}, 2 if issues else 0)


def video_dir(rd, video):
    n = int(video)
    if n < 1:
        error('video number must be >=1')
    return rd / '40-plans' / f'video-{n:02d}'


def normalize_refs(s):
    return [x.strip().upper() for x in (s or '').split(',') if x.strip()]


def cmd_length(args):
    rd, st = run_folder(args)
    outdir = video_dir(rd, args.video)
    lockfile = outdir / 'length-lock.json'
    if lockfile.exists():
        error('Length already locked. Do not silently revise runtime.', {'file': str(lockfile),
              'action': 'Use a new video ID or explicitly edit a documented revision with user approval.'})
    vids, cards, issues = card_set(rd)
    if issues:
        error('Analyze all reference videos before choosing length', issues)
    cohort_id = (getattr(args, 'cohort_id', None) or '').strip().lower()
    niche_arg = (args.niche or '').strip().lower()
    form_arg = (args.story_form or '').strip().lower()
    if not cohort_id and not (niche_arg and form_arg):
        error('Provide either --cohort-id or both --niche and --story-form')
    if cohort_id:
        family = {i: vids[i] for i, c in cards.items()
                  if str(c.get('cohort_id', '')).strip().lower() == cohort_id}
        if not family:
            error('No references with that cohort_id in their cards', {'cohort_id': cohort_id})
        effective_niche = '__cohort__:' + cohort_id
        effective_form = ''
    else:
        family = {i: vids[i] for i, c in cards.items()
                  if niche_arg in [str(x).lower() for x in c.get('niches') or []]
                  and str(c.get('story_form', '')).lower() == form_arg}
        if not family:
            error('No references in selected niche and story form', {'niche': niche_arg, 'form': form_arg})
        effective_niche = niche_arg
        effective_form = form_arg
    if st.get('selected_niche') and st['selected_niche'] != effective_niche:
        error('This run is one niche/channel only. Use clone for a different niche.',
              {'locked_niche': st['selected_niche'], 'requested': effective_niche})
    refs = normalize_refs(args.refs)
    if args.mode == 'standard':
        if len(refs) < 2:
            error('Standard requires >=2 explicitly selected comparable reference IDs (no mixed-folder averages).')
        if any(x not in family for x in refs):
            error('A selected reference is not in the selected group', refs)
        durations = [family[i]['duration_s'] for i in refs]
        if min(durations) < st['min_longform_s']:
            error('Standard cohort contains short-form; select long-form references only.', durations)
        if max(durations) / min(durations) > 1.8:
            error('Standard cohort spans incompatible runtime families; select a narrower group.', durations)
        target = round(statistics.median(durations)/5)*5
    else:
        if args.minutes is None or args.minutes <= 0:
            error('Own length requires --minutes N')
        target = round(args.minutes * 60)
        if not refs:
            refs = list(family)
        if any(x not in family for x in refs):
            error('An own-length reference must still match the selected group.', refs)
    if target < st['min_longform_s']:
        error('Target is shorter than long-form minimum configured for this run',
              {'target_s': target, 'minimum_s': st['min_longform_s']})
    computed_wpm, per_ref_wpm = compute_ref_wpm(rd, refs, family)
    if args.pace_wpm is not None:
        pace_wpm = args.pace_wpm
        pace_wpm_source = 'explicit'
    elif computed_wpm is not None:
        pace_wpm = computed_wpm
        pace_wpm_source = 'computed_from_refs'
    else:
        error('Cannot determine pace_wpm: no transcripts found in 10-media/ for the selected refs. '
              'Run prepare first, or pass --pace-wpm explicitly.')
    lock = {'schema': SCHEMA, 'video': f'{int(args.video):02d}', 'mode': args.mode,
            'target_length_s': target, 'tolerance_audio_pct': 0.04, 'tolerance_export_pct': 0.025,
            'niche': effective_niche, 'story_form': effective_form, 'reference_ids': refs,
            'reference_durations_s': {i: family[i]['duration_s'] for i in refs},
            'language': args.language, 'pace_wpm': pace_wpm, 'pace_wpm_source': pace_wpm_source,
            'per_ref_wpm': per_ref_wpm,
            # How the comparable narrators pause (same yardstick narration-measure uses on the generated voice):
            # the evidence the script stage reads before deciding any pause, hold or tag.
            'reference_pause_profiles': ref_pause_profiles(rd, refs),
            'locked_at': now(), 'rule': 'Immutable unless user explicitly approves a revised length.'}
    write_json(lockfile, lock)
    st['selected_niche'] = effective_niche
    st['video_count'] = max(st.get('video_count', 0), int(args.video))
    st['stage'] = 'planning'
    write_json(rd / 'state.json', st)
    wpm_note = (f'pace_wpm={pace_wpm} (computed from refs: {per_ref_wpm})'
                if pace_wpm_source == 'computed_from_refs'
                else f'pace_wpm={pace_wpm} (explicit override)')
    emit({'ok': True, 'lock_file': str(lockfile), 'locked_target_s': target, 'minutes': round(target/60, 2),
          'niche': effective_niche, 'story_form': effective_form, 'references': refs,
          'pace_wpm': pace_wpm, 'pace_wpm_source': pace_wpm_source, 'per_ref_wpm': per_ref_wpm,
          'target_words': round(target * pace_wpm / 60),
          'guidance': (f'Script, beat map, narration, timeline and export must respect this exact locked target. '
                       f'{wpm_note}. Write the script to ~{round(target * pace_wpm / 60)} words.')})


TAG_RE = re.compile(r'\[([^\[\]]{1,160})\]')
TAGS_FILE = ROOT / 'data' / 'elevenlabs-audio-tags.json'
TTS_MODELS = ('eleven_v4', 'eleven_v4_turbo')   # the user's standing rule: these two models only
# A planned pause up to this long is the voice's own gap between lines (already inside the measured per-line
# overhead): nothing to realise. Longer ones are realised by a pause tag or by a hold in the edit (pause_via).
NATURAL_PAUSE_MAX_S = 1.0
# Natural gap per script line before this run's voice is measured (eleven_v4 here, 2026-11-19: 0.36-0.42 s).
DEFAULT_LINE_OVERHEAD_S = 0.4


def strip_tags(text):
    """The spoken words of a line: inline [audio tags] are sent to ElevenLabs but never spoken."""
    return re.sub(r'[ \t]{2,}', ' ', TAG_RE.sub(' ', str(text))).strip()


def count_words(text):
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", strip_tags(text), flags=re.UNICODE))


_TAG_CATALOGUE = None


def tag_catalogue():
    global _TAG_CATALOGUE
    if _TAG_CATALOGUE is None:
        data = read_json(TAGS_FILE)
        _TAG_CATALOGUE = {' '.join(str(t['tag']).lower().split()): t for t in data.get('tags') or []}
    return _TAG_CATALOGUE


def classify_tag(inner):
    """The catalogue entry of one tag (its text inside the brackets). The vocabulary is open: a tag the
    catalogue doesn't list is 'custom', allowed, and judged on the calibration part (its measured delivery)."""
    key = '[' + ' '.join(str(inner).lower().split()) + ']'
    entry = tag_catalogue().get(key)
    if entry:
        return entry
    if 'accent' in key:
        return {'tag': key, 'category': 'accent_character', 'pipeline_status': 'not_for_narration'}
    return {'tag': key, 'category': 'pause' if 'pause' in key else 'custom', 'pipeline_status': 'custom'}


def tag_cost_s(tag, measured_costs=None):
    """Seconds a tag adds: this voice's measured value (narration-measure) first, else the catalogue's
    approximate one, else 2 s for any pause wording and 0 for a delivery tag."""
    if measured_costs and tag in measured_costs:
        return float(measured_costs[tag])
    entry = tag_catalogue().get(tag) or {}
    if entry.get('approx_cost_s') is not None:
        return float(entry['approx_cost_s'])
    return 2.0 if 'pause' in tag else 0.0


def script_tags(lines):
    """Every inline tag in the script, with its catalogue status. Refuses only what a pipeline rule excludes
    (not_for_narration) and broken brackets; which tags fit the story is the agents' decision (05)."""
    found, issues = [], []
    for i, row in enumerate(lines):
        text = str(row.get('text') or '')
        lid = str(row.get('id') or f'L{i+1:03d}')
        if text.count('[') != text.count(']') or re.search(r'\[[^\]]*\[', text) or re.search(r'\][^\[]*\]', text):
            issues.append(f'audio_tag_malformed_brackets:{lid}')
        for m in TAG_RE.finditer(text):
            entry = classify_tag(m.group(1))
            found.append({'line': lid, 'index': i + 1, 'tag': entry['tag'], 'category': entry.get('category'),
                          'status': entry.get('pipeline_status'), 'at_line_start': not text[:m.start()].strip(),
                          'at_line_end': not text[m.end():].strip(), 'words_before': count_words(text[:m.start()])})
            if entry.get('pipeline_status') == 'not_for_narration':
                issues.append(f'audio_tag_not_for_narration:{lid}:{entry["tag"]}')
        if text.strip() and not strip_tags(text):
            issues.append(f'line_has_only_tags:{lid}')
    return found, issues


def is_pause_tag(inner):
    return classify_tag(inner).get('category') == 'pause'


def script_pause_plan(lines):
    """Each planned pause longer than a natural line gap and how it is realised: 'tag' (a pause tag at this
    line's end or the next line's start: costs the tag's measured time inside the narration) or 'edit' (a hold:
    the narration is split there and the picture held; adds pause_after_s to the edit, not to the narration)."""
    plan, issues = [], []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i+1:03d}')
        try:
            p = float(row.get('pause_after_s') or 0)
        except (TypeError, ValueError):
            issues.append(f'pause_after_s_invalid:{lid}')
            continue
        via = str(row.get('pause_via') or '').strip().lower()
        if via and via not in ('natural', 'tag', 'edit'):
            issues.append(f'pause_via_invalid:{lid}')
            continue
        if p <= NATURAL_PAUSE_MAX_S and via in ('', 'natural'):
            continue
        if via in ('', 'natural'):
            issues.append(f'pause_{lid}_over_{NATURAL_PAUSE_MAX_S:g}s_needs_pause_via_tag_or_edit')
            continue
        if via == 'tag':
            here = str(row.get('text') or '').rstrip()
            after = str(lines[i + 1].get('text') or '').lstrip() if i + 1 < len(lines) else ''
            ends = [m.group(1) for m in (re.search(r'\[([^\[\]]+)\]\s*$', here), re.match(r'\s*\[([^\[\]]+)\]', after)) if m]
            if not any(is_pause_tag(x) for x in ends):
                issues.append(f'pause_{lid}_via_tag_but_no_pause_tag_at_this_line_end_or_next_line_start')
        plan.append({'line': lid, 'index': i + 1, 'pause_after_s': p, 'via': via})
    return plan, issues


def edit_holds_s(lines):
    plan, _ = script_pause_plan(lines)
    return round(sum(p['pause_after_s'] for p in plan if p['via'] == 'edit'), 2)


# Words that may break 02's content rules. A hit is not a verdict (a word can be plain, unavoidable fact): it
# must be answered, line by line, under a "Content flags" heading in editorial-review.md (rewritten, or why kept).
CONTENT_FLAGS = [
    ('holiday_religion_superstition', re.compile(
        r"\b(christmas|xmas|thanksgiving|easter|hanukkah|ramadan|diwali|halloween|new year's|holiday|holidays|feast|"
        r"church|chapel|chaplain|pray|prayed|praying|prayer|prayers|god|gods|heaven|miracle|miraculous|blessed|"
        r"blessing|omen|omens|luck|lucky|luckily|curse|cursed|ghost|ghosts|haunted|astrology|superstition)\b", re.I)),
    ('injury_gore_distress', re.compile(
        r"\b(blood|bloody|bled|bleed|bleeding|wound|wounds|gore|gory|corpse|corpses|severed|amputated|amputation|"
        r"limb|limbs|agony|scream|screamed|screaming|sobbing|terror|terrified|panic|panicked|despair|suicide|"
        r"vomit|vomited|needle|syringe|inject|injected)\b", re.I)),
    ('swearing', re.compile(r"\b(hell|damn|damned|goddamn|bastard|crap|shit|fuck)\b", re.I)),
]


def content_flags(lines, review_text):
    m = re.search(r'^#+[^\n]*content flags?[^\n]*\n(.*?)(?=^#|\Z)', review_text or '', flags=re.I | re.M | re.S)
    section = m.group(1) if m else ''
    flags, issues = [], []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i+1:03d}')
        spoken = strip_tags(row.get('text') or '')
        for kind, rx in CONTENT_FLAGS:
            hits = sorted({h.lower() for h in rx.findall(spoken)})
            if hits:
                reviewed = bool(re.search(r'\b' + re.escape(lid) + r'\b', section))
                flags.append({'line': lid, 'kind': kind, 'terms': hits, 'reviewed': reviewed})
                if not reviewed:
                    issues.append(f'content_flag_unreviewed:{lid}:{kind}')
    return flags, issues


def script_hash(lines):
    return hashlib.sha256('\n'.join(str(r.get('text') or '').strip() for r in lines).encode('utf-8')).hexdigest()


# ---------------------------------------------------------------- creative direction, reviews, writing signals
# The code enforces the PROCESS: what has to exist, in what order, for which version, and that every reviewer
# finding is answered. It never judges the work: whether a treatment, a script or a cut is good is decided by the
# agents and the independent reviewers (10-creative-direction.md, 06). A passed gate means the process happened.
APPROACH_AXES = ('perspective', 'scale', 'structure', 'voice', 'visualization')
STRATEGY_KEYS = ('why_this_idea', 'viewer_experience', 'progression', 'fits_and_forced', 'facts_as_experience',
                 'picture_contribution', 'sound_and_breath', 'distinct_from_references')
TREATMENT_KEYS = ('narrator', 'writing_voice', 'structure_and_pace', 'visual_language', 'sound',
                  'audiovisual_relationship', 'emotional_course', 'evidence_used', 'departures', 'risks')
TREATMENT_SHOWN_TO_REVIEWER = ('narrator', 'writing_voice', 'structure_and_pace', 'visual_language', 'sound',
                               'audiovisual_relationship', 'emotional_course')
SAMPLE_MOMENTS = ('opening', 'quiet_middle', 'turning_point')
BEAT_DIRECTION_KEYS = ('experience', 'narration_direction', 'visual_intent', 'sound_direction', 'pace')
# A major finding asks for a fresh read of the revised version until this round; after it the director decides
# and records why (no endless loops). More rounds are always allowed, never required.
REVIEW_MAX_ROUNDS = {'treatment': 1, 'script': 2, 'final': 2}
REVIEW_ACTIONS = ('revised', 'kept', 'disputed')
MIN_FIELD_WORDS, MIN_SAMPLE_WORDS, MIN_PICTURE_WORDS, MIN_NOTE_WORDS = 6, 50, 10, 5
# Edits after the last read that no finding asked for: a few lines (a length trim) pass with a warning; more need
# a fresh read, because the approval no longer describes the script.
SMALL_EDIT_LINES, SMALL_EDIT_SHARE = 10, 0.03


def n_words(s):
    return len(re.findall(r'\w+', str(s or ''), flags=re.UNICODE))


def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def ref_av_path(rd, vid):
    return rd / '20-analysis' / 'av' / f'{vid}.json'


def _content_tokens(text):
    return {t for t in re.findall(r"[a-z0-9']+", strip_tags(text).lower()) if len(t) > 3}


def _jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def direction_facts(rd, video):
    """Structure of 40-plans/video-NN/direction.json (10-creative-direction.md): evidence read from measured
    references, five approaches that differ in how the story is told, the episode strategy, two or three
    audiovisual treatments with sample moments, and the decision. Presence and shape only."""
    vd = video_dir(rd, video)
    d = read_json(vd / 'direction.json')
    out = {'issues': [], 'warnings': [], 'direction_sha256': None, 'treatments_sha256': None,
           'chosen_treatment': None}
    iss, warn = out['issues'], out['warnings']
    if not d:
        iss.append('direction_missing')
        return out
    out['direction_sha256'] = canonical_sha(d)
    ev = d.get('evidence') if isinstance(d.get('evidence'), dict) else {}
    refs = [str(x).strip().upper() for x in ev.get('references') or []]
    if not refs:
        iss.append('direction_evidence_names_no_references')
    for v in refs:
        if not ref_av_path(rd, v).is_file():
            iss.append(f'direction_evidence_without_av_profile:{v}')
    obs = [o for o in ev.get('observations') or [] if isinstance(o, dict) and str(o.get('ref') or '').strip()
           and str(o.get('at') or '').strip() and n_words(o.get('what')) >= 4]
    if len(obs) < 3:
        iss.append('direction_evidence_needs_3_timed_observations')
    if not ev.get('unknowns'):
        iss.append('direction_evidence_lists_no_unknowns')
    apps = [a for a in d.get('approaches') or [] if isinstance(a, dict)]
    ids = [str(a.get('id') or '').strip() for a in apps]
    if len(apps) < 5 or len(set(ids)) != len(ids) or '' in ids:
        iss.append('direction_needs_5_distinct_approaches')
    axes = set()
    for a in apps:
        aid = a.get('id')
        changes = [str(x).strip().lower() for x in a.get('changes') or []]
        if not changes or any(x not in APPROACH_AXES for x in changes):
            iss.append(f'approach_{aid}_changes_must_name:' + '/'.join(APPROACH_AXES))
        axes |= set(changes) & set(APPROACH_AXES)
        for k in ('pitch', 'strongest_case', 'long_form_risk'):
            if n_words(a.get(k)) < MIN_FIELD_WORDS:
                iss.append(f'approach_{aid}_missing_{k}')
    if apps and len(axes) < 3:
        iss.append('approaches_differ_on_fewer_than_3_axes')
    if apps and not any(a.get('challenges_reference_formula') is True for a in apps):
        iss.append('no_approach_challenges_the_reference_formula')
    ca = d.get('chosen_approach') if isinstance(d.get('chosen_approach'), dict) else {}
    if ca.get('id') not in ids or ca.get('runner_up') not in ids or ca.get('runner_up') == ca.get('id'):
        iss.append('chosen_approach_and_runner_up_must_be_two_listed_approaches')
    for k in ('why', 'why_not_runner_up'):
        if n_words(ca.get(k)) < MIN_FIELD_WORDS:
            iss.append(f'chosen_approach_missing_{k}')
    strat = d.get('strategy') if isinstance(d.get('strategy'), dict) else {}
    for k in STRATEGY_KEYS:
        if n_words(strat.get(k)) < MIN_FIELD_WORDS:
            iss.append(f'strategy_missing_{k}')
    trs = [t for t in d.get('treatments') or [] if isinstance(t, dict)]
    tids = [str(t.get('id') or '').strip() for t in trs]
    out['treatments_sha256'] = canonical_sha(d.get('treatments') or [])
    if not 2 <= len(trs) <= 4 or len(set(tids)) != len(tids) or '' in tids:
        iss.append('direction_needs_2_to_3_distinct_treatments')
    for t in trs:
        tid = t.get('id')
        for k in TREATMENT_KEYS:
            if n_words(t.get(k)) < MIN_FIELD_WORDS:
                iss.append(f'treatment_{tid}_missing_{k}')
        samples = t.get('samples') if isinstance(t.get('samples'), dict) else {}
        for m in SAMPLE_MOMENTS:
            s = samples.get(m) if isinstance(samples.get(m), dict) else {}
            if n_words(strip_tags(s.get('narration') or '')) < MIN_SAMPLE_WORDS:
                iss.append(f'treatment_{tid}_sample_{m}_narration_under_{MIN_SAMPLE_WORDS}_words')
            if n_words(s.get('picture')) < MIN_PICTURE_WORDS:
                iss.append(f'treatment_{tid}_sample_{m}_picture_missing')
    for i in range(len(trs)):
        for j in range(i + 1, len(trs)):
            def toks(t):
                s = t.get('samples') if isinstance(t.get('samples'), dict) else {}
                return _content_tokens(' '.join(str((s.get(m) or {}).get('narration') or '') for m in SAMPLE_MOMENTS))
            sim = _jaccard(toks(trs[i]), toks(trs[j]))
            if sim >= 0.6:
                warn.append(f'treatments {tids[i]} and {tids[j]} share {sim:.0%} of their sample vocabulary: '
                            'are they really different treatments, or one treatment at two intensities?')
    dec = d.get('decision') if isinstance(d.get('decision'), dict) else {}
    out['chosen_treatment'] = dec.get('treatment')
    if dec.get('treatment') not in tids:
        iss.append('decision_must_name_a_listed_treatment')
    for k in ('why', 'taken_from_others'):
        if n_words(dec.get(k)) < MIN_FIELD_WORDS:
            iss.append(f'decision_missing_{k}')
    return out


# ---------------------------------------------------------------- what a direction change touches
# The direction lock carries a production revision. A change to the chosen treatment, the strategy or the chosen
# approach is meaningful: it raises the revision and marks the artifacts it affects. Each affected artifact must then
# be really updated (its content changes; its own checks apply) or explicitly reapproved (`direction-reapprove`, with
# a reason, on record) before a production stage that uses it continues. A change to the evidence, the alternatives
# or the reasons affects nothing: no new revision, no new work, no new read.
TRACKED_FILES = ('beat-map', 'script', 'shot-plan', 'style-bible')
MEDIA_ARTIFACTS = ('stills', 'music', 'edit')
ALL_ARTIFACTS = TRACKED_FILES + MEDIA_ARTIFACTS
SECTION_EFFECTS = {'chosen_treatment': ALL_ARTIFACTS,
                   'strategy': ('beat-map', 'script', 'shot-plan', 'edit'),
                   'chosen_approach': ('beat-map', 'script', 'shot-plan', 'edit')}


def artifact_path(rd, video, name):
    n = int(video)
    vis, edit = rd / '60-visuals' / f'video-{n:02d}', rd / '70-edit' / f'video-{n:02d}'
    return {'beat-map': video_dir(rd, n) / 'beat-map.json', 'script': video_dir(rd, n) / 'script.json',
            'shot-plan': vis / 'shot-plan.json', 'style-bible': vis / 'style-bible.md',
            'stills': vis / 'stills-provenance.json', 'music': edit / 'music-provenance.json',
            'edit': edit / 'edit-plan.json'}[name]


def artifact_sha(rd, video, name):
    """Content version of a tracked file: JSON by its canonical content, text by its words, so re-saving or
    reformatting without changing anything is not an update. None when the file doesn't exist."""
    p = artifact_path(rd, video, name)
    if not p.is_file():
        return None
    if p.suffix == '.json':
        d = read_json(p)
        return canonical_sha(d) if d else None
    return hashlib.sha256(' '.join(p.read_text(encoding='utf-8', errors='replace').split()).encode('utf-8')).hexdigest()


def direction_sections(d):
    """One hash per part of direction.json, so a revision can tell which part changed."""
    trs = {str(t.get('id')): t for t in d.get('treatments') or [] if isinstance(t, dict)}
    dec = d.get('decision') if isinstance(d.get('decision'), dict) else {}
    chosen = str(dec.get('treatment'))
    return {'evidence': canonical_sha(d.get('evidence')), 'approaches': canonical_sha(d.get('approaches')),
            'chosen_approach': canonical_sha(d.get('chosen_approach')), 'strategy': canonical_sha(d.get('strategy')),
            'chosen_treatment': canonical_sha([chosen, trs.get(chosen)]),
            'other_treatments': canonical_sha({k: v for k, v in trs.items() if k != chosen}),
            'decision_reasons': canonical_sha({k: v for k, v in dec.items() if k != 'treatment'})}


def media_present(rd, video, name):
    p = artifact_path(rd, video, name)
    return p.is_file() and bool(read_json(p))


def required_rev(lock, artifact):
    """The production revision that last affected this artifact (None: no direction change has touched it)."""
    return ((lock.get('required') or {}).get(artifact) or {}).get('rev')


def reapproved_for(lock, artifact):
    """The explicit reapproval of this artifact that still applies (given for the revision that last affected it)."""
    ra = (lock.get('reapproved') or {}).get(artifact) or {}
    want = required_rev(lock, artifact) or lock.get('production_rev', 1)
    return ra if ra and ra.get('rev') == want else None


def media_current(lock, artifact, made_rev):
    """Media made under production revision made_rev still stands: no direction change has touched this kind of
    artifact since, or it was explicitly reapproved for the revision that did."""
    req = required_rev(lock, artifact)
    if not req or reapproved_for(lock, artifact):
        return True
    try:
        return int(made_rev or 0) >= req
    except (TypeError, ValueError):
        return False


def stale_files(rd, video, names=TRACKED_FILES):
    """Tracked files a meaningful direction change affected that are still exactly as they were at that change, with
    no reapproval for it: {name: issue}."""
    lock = read_json(video_dir(rd, video) / 'direction-lock.json')
    out = {}
    for name in names:
        req = (lock.get('required') or {}).get(name)
        if not req:
            continue
        cur = artifact_sha(rd, video, name)
        if cur is None or cur != req.get('baseline'):
            continue                         # absent, or changed since the direction did: its own checks apply
        ra = reapproved_for(lock, name)
        if ra and ra.get('sha256') == cur:
            continue
        out[name] = f"{name.replace('-', '_')}_made_for_an_earlier_direction"
    return out


def direction_gate(rd, video):
    """The locked direction as production uses it: complete, locked, and unchanged since its lock."""
    df = direction_facts(rd, video)
    issues = list(df['issues'])
    lock = read_json(video_dir(rd, video) / 'direction-lock.json')
    if not lock:
        issues.append('direction_lock_missing')
    elif df.get('direction_sha256') and lock.get('direction_sha256') != df['direction_sha256']:
        issues.append('direction_changed_since_lock')
    return issues, lock, df


def beat_map_facts(rd, video, lines=None, target=None):
    """The beat map covers the locked length and every script line once, and every beat carries its direction:
    what the viewer should experience, and how narration, picture, sound and pace serve it (10-creative-direction.md).
    Presence only; the treatment evolves beat by beat."""
    vd = video_dir(rd, video)
    if lines is None:
        lines = read_json(vd / 'script.json').get('lines') or []
    if target is None:
        target = read_json(vd / 'length-lock.json').get('target_length_s')
    beats = read_json(vd / 'beat-map.json')
    issues = []
    if beats.get('target_length_s') != target:
        issues.append('beat_map_target_differs_from_locked_length')
    timing = beats.get('beats') or []
    if not timing:
        issues.append('beat_map_missing_beats')
    cursor_s, cursor_line = 0.0, 0
    for n, beat in enumerate(timing, 1):
        try:
            start, end = float(beat['start_s']), float(beat['end_s'])
            lstart, lend = int(beat['line_start']), int(beat['line_end'])
            if abs(start - cursor_s) > 0.5 or end <= start:
                issues.append(f'beat_{n}_time_gap_overlap_or_negative')
            if lstart != cursor_line + 1 or lend < lstart or lend > len(lines):
                issues.append(f'beat_{n}_line_coverage_gap_or_overlap')
            for key in ('narrative_job',) + BEAT_DIRECTION_KEYS:
                if not str(beat.get(key) or '').strip():
                    issues.append(f'beat_{n}_missing_{key}')
            cursor_s, cursor_line = end, lend
        except (TypeError, ValueError, KeyError):
            issues.append(f'beat_{n}_bad_structure')
    if timing and target is not None and (abs(cursor_s - target) > 1 or cursor_line != len(lines)):
        issues.append('beats_do_not_cover_all_time_and_lines')
    return issues


def _norm(text):
    return ' '.join(strip_tags(str(text or '')).lower().split())


def media_gate(job, kind):
    """What every generation worker runs before it makes anything (stills: image_worker.py, openai_images_worker.py;
    music: music_worker.py), and `media-check` runs by hand. A job names its run and video; every still names a shot
    of the checked shot plan and its prompt carries that shot's approved frame prompt; every music track names the
    beats it scores. Refused while the direction, the beat map or the shot plan fails its check or was made for an
    earlier direction. Treatment previews (job purpose "treatment_preview") are the one exception: they come before
    the lock, name a treatment and a sample moment, and carry that sample's picture. Returns the records to keep."""
    out = {'ok': False, 'issues': [], 'warnings': [], 'records': [], 'run': None, 'video': None, 'preview': False}
    iss = out['issues']
    run, video = job.get('run'), job.get('video')
    if not run or not video:
        iss.append('job_must_name_its_run_and_video')
        return out
    rd = Path(str(run)).expanduser().resolve()
    if read_json(rd / 'state.json').get('schema') != SCHEMA:
        iss.append('job_run_is_not_a_static_studio_run')
        return out
    try:
        n = int(video)
        if n < 1:
            raise ValueError
    except (TypeError, ValueError):
        iss.append('job_video_must_be_a_positive_number')
        return out
    out.update(run=str(rd), video=n)
    items = job.get('images' if kind == 'stills' else 'tracks') or []
    if not items:
        iss.append('job_has_nothing_to_make')
    if kind == 'stills' and job.get('purpose') == 'treatment_preview':
        out['preview'] = True
        d = read_json(video_dir(rd, n) / 'direction.json')
        iss += [x for x in direction_facts(rd, n)['issues']
                if x.startswith(('treatment_', 'direction_needs_2', 'direction_missing'))]
        trs = {str(t.get('id')): t for t in d.get('treatments') or [] if isinstance(t, dict)}
        for i, it in enumerate(items, 1):
            t, m = trs.get(str(it.get('treatment'))), str(it.get('moment') or '')
            if not t or m not in SAMPLE_MOMENTS:
                iss.append(f'item_{i}_must_name_a_treatment_and_a_sample_moment')
                continue
            pic = ((t.get('samples') or {}).get(m) or {}).get('picture')
            if not _norm(pic) or _norm(pic) not in _norm(it.get('prompt')):
                iss.append(f'item_{i}_prompt_does_not_carry_its_sample_picture')
            out['records'].append({'purpose': 'treatment_preview', 'treatment': str(it.get('treatment')), 'moment': m})
        out['ok'] = not iss
        return out
    gate, lock, _ = direction_gate(rd, n)
    iss += gate
    iss += beat_map_facts(rd, n)
    iss += list(stale_files(rd, n, ('beat-map',)).values())
    rev, treatment = lock.get('production_rev', 1), lock.get('treatment')
    if kind == 'stills':
        sf = shot_facts(rd, n)
        iss += sf['issues']
        out['warnings'] += sf['warnings']
        shots = {str(s.get('id')): s for s in read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []}
        for i, it in enumerate(items, 1):
            s = shots.get(str(it.get('shot_id') or it.get('id') or ''))
            if not s:
                iss.append(f'item_{i}_must_name_a_shot_of_the_shot_plan')
                continue
            fp = _norm(s.get('frame_prompt') or s.get('prompt'))
            if not fp or fp not in _norm(it.get('prompt')):
                iss.append(f'item_{i}_prompt_does_not_carry_shot_{s.get("id")}_frame_prompt')
            out['records'].append({'shot_id': str(s.get('id')), 'beat_id': str(s.get('beat_id')),
                                   'frame_prompt_sha256': hashlib.sha256(fp.encode('utf-8')).hexdigest(),
                                   'production_rev': rev, 'treatment': treatment})
    else:
        beats = {str(b.get('id')) for b in read_json(video_dir(rd, n) / 'beat-map.json').get('beats') or []}
        for i, it in enumerate(items, 1):
            bs = [str(x) for x in it.get('beats') or []]
            if not bs or any(b not in beats for b in bs):
                iss.append(f'track_{i}_must_name_beats_of_the_beat_map')
            if n_words(it.get('caption')) < 3:
                iss.append(f'track_{i}_missing_caption')
            out['records'].append({'beats': bs, 'caption_sha256': hashlib.sha256(_norm(it.get('caption')).encode('utf-8')).hexdigest(),
                                   'production_rev': rev, 'treatment': treatment})
    out['ok'] = not iss
    return out


def record_media(run, video, kind, entries):
    """After a worker made its files: which shot (stills) or beats (music) each one belongs to, made under which
    direction revision. Read by timeline-check and release-check."""
    rd, n = Path(str(run)).expanduser().resolve(), int(video)
    p = artifact_path(rd, n, kind)
    key = 'images' if kind == 'stills' else 'tracks'
    data = read_json(p) or {'video': n}
    data.setdefault(key, {})
    for e in entries:
        data[key][str(Path(e['out']).expanduser().resolve())] = {**{k: v for k, v in e.items() if k != 'out'},
                                                                 'made_at': now()}
    write_json(p, data)
    return str(p)


def stills_facts(rd, video):
    """Every shot has a still made through the gate, from its current approved prompt, under the current direction
    (or the director explicitly reapproved the stills for this revision, e.g. user-supplied pictures)."""
    n = int(video)
    lock = read_json(video_dir(rd, n) / 'direction-lock.json')
    shots = read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []
    prov = read_json(artifact_path(rd, n, 'stills')).get('images') or {}
    by_shot = {}
    for path, rec in prov.items():
        if Path(path).is_file():
            by_shot.setdefault(str(rec.get('shot_id')), []).append((str(rec.get('made_at') or ''), rec))
    missing, changed, older = [], [], []
    for s in shots:
        sid = str(s.get('id'))
        recs = sorted(by_shot.get(sid) or [], key=lambda x: x[0])
        if not recs:
            missing.append(sid)
            continue
        rec = recs[-1][1]
        fp = hashlib.sha256(_norm(s.get('frame_prompt') or s.get('prompt')).encode('utf-8')).hexdigest()
        if rec.get('frame_prompt_sha256') != fp:
            changed.append(sid)
        if not media_current(lock, 'stills', rec.get('production_rev')):
            older.append(sid)
    ra = reapproved_for(lock, 'stills')
    out = {'issues': [], 'warnings': [], 'shots': len(shots), 'traced': len(shots) - len(missing)}
    found = [('stills_missing_or_untraced', missing), ('stills_show_an_older_shot_prompt', changed),
             ('stills_made_for_an_earlier_direction', older)]
    if ra:
        if missing or changed or older:
            out['warnings'].append('stills accepted as they are by explicit reapproval: ' + str(ra.get('reason')))
    else:
        out['issues'] += [f'{name}:' + ','.join(ids[:15]) + ('...' if len(ids) > 15 else '') for name, ids in found if ids]
    return out


def review_records(vd, kind):
    """Recorded rounds of one review kind, oldest first: (record, answers) with record['_round']."""
    out = []
    folder = vd / 'reviews'
    if not folder.is_dir():
        return out
    for p in folder.glob(f'{kind}-r*.json'):
        m = re.fullmatch(re.escape(kind) + r'-r(\d+)\.json', p.name)
        if not m:
            continue
        rec = read_json(p)
        if not rec:
            continue
        rec['_round'] = int(m.group(1))
        ans = read_json(p.with_name(f'{kind}-r{m.group(1)}-answers.json')).get('answers') or {}
        out.append((rec, ans if isinstance(ans, dict) else {}))
    return sorted(out, key=lambda x: x[0]['_round'])


def expand_lines(spec, order):
    """'L005', 'L005-L009' or a list of them -> line ids in script order; None when a line is unknown."""
    out = []
    for item in (spec if isinstance(spec, list) else [spec]):
        s = str(item).strip()
        m = re.fullmatch(r'(L\d+)\s*[-–]\s*(L\d+)', s)
        if m and m.group(1) in order and m.group(2) in order:
            i, j = order.index(m.group(1)), order.index(m.group(2))
            out += order[min(i, j):max(i, j) + 1]
        elif s in order:
            out.append(s)
        else:
            return None
    return out


def answer_problem(kind, finding, ans):
    """Why an answer to a finding is not yet an answer, or None."""
    ans = ans if isinstance(ans, dict) else {}
    act = str(ans.get('action') or '').strip().lower()
    if act not in REVIEW_ACTIONS:
        return 'no action (revised, kept or disputed)'
    if finding.get('severity') == 'major' and act == 'kept':
        return 'a major finding is revised or disputed, never simply kept'
    if act in ('kept', 'disputed') and n_words(ans.get('note')) < MIN_NOTE_WORDS:
        return 'needs a note saying why'
    if act == 'revised' and kind == 'script' and not ans.get('lines'):
        return 'revised needs the lines that changed'
    if act == 'revised' and kind != 'script' and n_words(ans.get('note')) < MIN_NOTE_WORDS:
        return 'revised needs a note saying what changed'
    return None


def review_state(vd, kind, current_sha, snapshot=None):
    """Where one review kind stands for the current version: every round's findings sealed and answered,
    'revised' answers backed by real changes, a fresh read after major findings (until the round cap), and the
    last read still describing what exists now. Issues block; warnings are shown and kept for the release sheet."""
    recs = review_records(vd, kind)
    st = {'kind': kind, 'rounds': len(recs), 'issues': [], 'warnings': [], 'majors_closed_by_decision': []}
    if not recs:
        st['issues'].append(f'{kind}_review_missing')
        return st
    max_r = REVIEW_MAX_ROUNDS[kind]
    for i, (rec, ans) in enumerate(recs):
        rnd, fs = rec['_round'], rec.get('findings') or []
        if canonical_sha(fs) != rec.get('findings_sha256'):
            st['issues'].append(f'{kind}_review_r{rnd}_findings_altered')
        later = recs[i + 1][0].get('subject_snapshot') if i + 1 < len(recs) else snapshot
        old = rec.get('subject_snapshot') or {}
        open_ids = []
        for f in fs:
            fid = str(f.get('id'))
            a = ans.get(fid) or {}
            if answer_problem(kind, f, a):
                open_ids.append(fid)
                continue
            if kind == 'script' and str(a.get('action')).strip().lower() == 'revised' and later is not None:
                ls = expand_lines(a.get('lines'), list(dict.fromkeys(list(old) + list(later))))
                if not ls:
                    open_ids.append(fid)
                elif all(old.get(x) == later.get(x) for x in ls):
                    st['issues'].append(f'{kind}_review_r{rnd}_revised_but_unchanged:{fid}')
        if open_ids:
            st['issues'].append(f'{kind}_review_r{rnd}_unanswered:' + ','.join(open_ids))
    rec, ans = recs[-1]
    rnd = rec['_round']
    majors = [str(f.get('id')) for f in rec.get('findings') or [] if f.get('severity') == 'major']
    if majors and rnd < max_r:
        st['issues'].append(f'{kind}_review_round_{rnd + 1}_required')
    elif majors:
        st['majors_closed_by_decision'] = majors
        st['warnings'].append(f'{kind} review: round {rnd} still found major problems ({", ".join(majors)}); '
                              'the director closed them with the reasons in the answers')
    if rec.get('subject_sha256') != current_sha:
        if kind == 'script' and snapshot is not None:
            old = rec.get('subject_snapshot') or {}
            changed = [k for k in dict.fromkeys(list(old) + list(snapshot)) if old.get(k) != snapshot.get(k)]
            asked = set()
            for a in ans.values():
                if isinstance(a, dict) and str(a.get('action')).strip().lower() == 'revised':
                    asked |= set(expand_lines(a.get('lines'), list(dict.fromkeys(list(old) + list(snapshot)))) or [])
            loose = [k for k in changed if k not in asked]
            if loose:
                total = sum(n_words(strip_tags(t)) for t in snapshot.values()) or 1
                moved = sum(n_words(strip_tags(snapshot.get(k) or old.get(k) or '')) for k in loose)
                if len(loose) <= SMALL_EDIT_LINES and moved <= SMALL_EDIT_SHARE * total:
                    st['warnings'].append(f'script edited after its last read on {len(loose)} line(s) no finding '
                                          'asked about (small enough to pass): ' + ','.join(loose))
                else:
                    st['issues'].append('script_changed_after_review:' + ','.join(loose[:15])
                                        + ('...' if len(loose) > 15 else ''))
        elif kind == 'final' and rnd >= max_r:
            st['warnings'].append('the export changed after the last final review round')
        else:
            st['issues'].append(f'{kind}_review_outdated')
    return st


EN_FUNCTION_WORDS = set((
    'a an the and but or so if then than that this these those it its is are was were be been being not no nor to '
    'of in on at by for with from as into onto over under about after before through you your yours we our they '
    'them their he him his she her i me my what which who whom whose when where why how there here do does did '
    'have has had will would can could may might must should just only also very all every each some any more '
    'most other such own same too now still even').split())
NUMBER_WORDS = re.compile(r"\d[\d,.]*|\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|"
                          r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)\b", re.I)


def writing_signals(lines, language='en'):
    """Counts the writer reads during revision (never a verdict, never shown to a cold reader): phrases repeated
    across lines, sentence shapes used again and again, runs of very short fragments, sentences too long to follow
    by ear, lines stacked with numbers, words echoing in neighbouring lines, and how sentence length varies."""
    sents = []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i + 1:03d}')
        for s in re.split(r'(?<=[.!?…])\s+', strip_tags(row.get('text') or '')):
            toks = re.findall(r"[\w']+", s.lower())
            if toks:
                sents.append((lid, s.strip(), toks))
    lengths = [len(t) for _, _, t in sents]
    out = {'sentences': len(sents),
           'sentence_words': {'mean': round(statistics.mean(lengths), 1) if lengths else None,
                              'spread': round(statistics.pstdev(lengths), 1) if lengths else None,
                              'share_under_5_words': round(sum(1 for x in lengths if x < 5) / len(lengths), 3)
                              if lengths else None},
           'questions': sum(1 for _, s, _ in sents if s.endswith('?'))}
    out['long_sentences'] = [{'line': lid, 'words': len(t)} for lid, _, t in sents if len(t) > 32][:20]
    runs, cur = [], []
    for lid, _, t in sents:
        if len(t) <= 4:
            cur.append(lid)
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    out['fragment_runs'] = [{'from': r[0], 'to': r[-1], 'fragments': len(r)} for r in runs][:20]
    english = str(language or '').lower().startswith('en')
    grams = {}
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i + 1:03d}')
        toks = re.findall(r"[\w']+", strip_tags(row.get('text') or '').lower())
        for n in (3, 4, 5):
            for k in range(len(toks) - n + 1):
                g = tuple(toks[k:k + n])
                if english and all(w in EN_FUNCTION_WORDS for w in g):
                    continue
                grams.setdefault(g, set()).add(lid)
    rep = sorted(((g, ls) for g, ls in grams.items() if len(ls) >= 3), key=lambda x: (-len(x[1]), -len(x[0])))
    kept = []
    for g, ls in rep:
        if any(len(k) > len(g) and ls <= kl and ' '.join(g) in ' '.join(k) for k, kl in kept):
            continue
        kept.append((g, ls))
        if len(kept) >= 15:
            break
    out['repeated_phrases'] = [{'phrase': ' '.join(g), 'lines': len(ls), 'examples': sorted(ls)[:6]} for g, ls in kept]
    if english:
        def skel(tokens):
            # Function words kept (articles aside), every run of content words one "_": the shape a listener hears.
            out_ = []
            for w in tokens:
                x = w if (w in EN_FUNCTION_WORDS and w not in ('a', 'an', 'the')) else '_'
                if not (x == '_' and out_ and out_[-1] == '_'):
                    out_.append(x)
            return ' '.join(out_)
        shapes = {}
        for lid, _, t in sents:
            if 2 <= len(t) <= 10:
                sk = skel(t)
                if sk.replace('_', '').strip():
                    shapes.setdefault(sk, []).append(lid)
        for (l1, _, t1), (l2, _, t2) in zip(sents, sents[1:]):   # two sentences used as one figure: their openings
            s1, s2 = skel(t1[:4]), skel(t2[:3])
            if s1.replace('_', '').strip() and s2.replace('_', '').strip():
                shapes.setdefault(s1 + ' | ' + s2, []).append(l1)
        out['repeated_sentence_shapes'] = [{'shape': k, 'times': len(v), 'examples': v[:6]} for k, v in
                                           sorted(shapes.items(), key=lambda x: -len(x[1])) if len(v) >= 3][:12]
        openings = {}
        for lid, _, t in sents:
            if len(t) >= 3:
                openings.setdefault(' '.join(t[:2]), []).append(lid)
        out['repeated_openings'] = [{'opening': k, 'times': len(v), 'examples': v[:6]} for k, v in
                                    sorted(openings.items(), key=lambda x: -len(x[1])) if len(v) >= 5][:12]
    out['number_dense_lines'] = [str(r.get('id') or f'L{i + 1:03d}') for i, r in enumerate(lines)
                                 if len(NUMBER_WORDS.findall(strip_tags(r.get('text') or ''))) >= 3][:30]
    echoes, ids = {}, [str(r.get('id') or f'L{i + 1:03d}') for i, r in enumerate(lines)]
    toks_by = [set(t for t in re.findall(r"[\w']+", strip_tags(r.get('text') or '').lower())
                   if len(t) >= 5 and (not english or t not in EN_FUNCTION_WORDS)) for r in lines]
    for i in range(len(lines)):
        window = toks_by[i:i + 4]
        for w in toks_by[i]:
            hits = [ids[i + k] for k, s in enumerate(window) if w in s]
            if len(hits) >= 3 and w not in echoes:
                echoes[w] = hits
    out['word_echoes'] = [{'word': w, 'lines': v} for w, v in list(echoes.items())[:15]]
    out['note'] = ('Signals for the writer, not verdicts: a repeated shape can be a deliberate refrain. Count what '
                   'the listener will hear: a device used once is style, used eight times it is a template.')
    return out


def shot_facts(rd, video):
    """The shot plan as a visual argument (04): every shot belongs to a beat and says what NEW thing its picture
    gives the viewer; every beat has a picture; lines run contiguously. Plus repetition signals: shots whose
    prompts are nearly the same, and long runs of one composition family."""
    n = int(video)
    plan = read_json(rd / '60-visuals' / f'video-{n:02d}' / 'shot-plan.json')
    out = {'ready': False, 'issues': [], 'warnings': [], 'shots': 0}
    if not plan:
        out['issues'].append('shot_plan_missing')
        return out
    beat_rows = read_json(video_dir(rd, n) / 'beat-map.json').get('beats') or []
    beats = [str(b.get('id')) for b in beat_rows]
    spans = {}
    for b in beat_rows:
        try:
            spans[str(b.get('id'))] = (int(b['line_start']), int(b['line_end']))
        except (KeyError, TypeError, ValueError):
            pass
    lines = read_json(video_dir(rd, n) / 'script.json').get('lines') or []
    order = [str(r.get('id') or f'L{i + 1:03d}') for i, r in enumerate(lines)]
    shots = plan.get('shots') or []
    out['shots'] = len(shots)
    used, cursor = set(), 0
    for s in shots:
        sid = s.get('id')
        if str(s.get('beat_id')) not in beats:
            out['issues'].append(f'shot_{sid}_beat_not_in_beat_map')
        else:
            used.add(str(s.get('beat_id')))
        if n_words(s.get('new_thing')) < 4:
            out['issues'].append(f'shot_{sid}_missing_new_thing')
        if n_words(s.get('frame_prompt') or s.get('prompt')) < 8:
            out['issues'].append(f'shot_{sid}_missing_frame_prompt')
        a = order.index(str(s.get('line_start'))) + 1 if str(s.get('line_start')) in order else None
        b = order.index(str(s.get('line_end'))) + 1 if str(s.get('line_end')) in order else None
        if a != cursor + 1 or b is None or b < a:
            out['issues'].append(f'shot_{sid}_lines_not_contiguous')
        span = spans.get(str(s.get('beat_id')))
        if span and a and b and (a < span[0] or b > span[1]):
            # The picture would play over another beat's words while following this beat's direction.
            out['issues'].append(f'shot_{sid}_lines_outside_beat_{s.get("beat_id")}')
        cursor = b or cursor
    # Made for an earlier direction (or before there was one): updated for real, or explicitly reapproved.
    out['issues'] += list(stale_files(rd, n, ('shot-plan', 'style-bible')).values())
    if order and cursor != len(order):
        out['issues'].append('shots_do_not_cover_every_line')
    for b in beats:
        if b not in used:
            out['issues'].append(f'beat_{b}_has_no_shot')
    toks = [(s.get('id'), _content_tokens(s.get('frame_prompt') or s.get('prompt') or '')) for s in shots]
    close = []
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            sim = _jaccard(toks[i][1], toks[j][1])
            if sim >= 0.7:
                close.append(f'{toks[i][0]}~{toks[j][0]} ({sim:.0%})')
    if close:
        out['warnings'].append('prompts nearly the same (a callback, or the same picture twice?): ' + ', '.join(close[:12]))
    run, prev = [], None
    for s in shots + [{}]:
        fam = str(s.get('composition') or '')
        if fam and fam == prev:
            run.append(s.get('id'))
        else:
            if len(run) >= 4:
                out['warnings'].append(f'{len(run)} shots in a row of the same composition "{prev}": {run[0]}-{run[-1]}')
            run = [s.get('id')] if fam else []
        prev = fam
    out['overlays'] = sum(1 for s in shots if str(s.get('diagram_or_overlay')).lower() not in ('', 'false', 'none', '0'))
    out['ready'] = not out['issues']
    return out


def voice_measurement(rd):
    """The locked voice's real measured pace and natural per-line gap (narration-measure writes it), or the
    older hand-recorded fields. Empty until a real chunk of at least 300 words has been measured."""
    vl = read_json(rd / '60-voice' / 'voice-lock.json')
    m = vl.get('measured') or {}
    if m.get('wpm') and m.get('per_line_overhead_s') is not None and (m.get('words') or 0) >= 300:
        return m
    if vl.get('measured_wpm') and vl.get('measured_overhead_s') and vl.get('measured_overhead_lines'):
        return {'wpm': vl['measured_wpm'], 'per_line_overhead_s': vl['measured_overhead_s'] / vl['measured_overhead_lines'],
                'voice_id': vl.get('voice_id'), 'settings': vl.get('settings') or {}, 'source': 'hand-recorded (older run)'}
    return {}


def strip_transcript_timestamps(raw):
    """Remove [start-end] timestamp prefixes (e.g. [0.0-2.4]) from transcript lines."""
    lines = []
    for line in raw.splitlines():
        cleaned = re.sub(r'^\s*\[[\d.]+\s*[-–]\s*[\d.]+\]\s*', '', line)
        if cleaned.strip():
            lines.append(cleaned)
    return ' '.join(lines)


def transcript_speech(raw):
    """(spoken words, speech seconds) of a [start-end] text transcript: the sum of the spoken segments'
    durations, so silence between segments is excluded. One yardstick for references and generated narration."""
    narr_s = sum(float(m.group(2)) - float(m.group(1))
                 for m in re.finditer(r'\[([\d.]+)-([\d.]+)\]', raw))
    return count_words(strip_transcript_timestamps(raw)), narr_s


def wpm_from_transcript_raw(raw):
    """Pure-narration WPM from a [start-end] text transcript: spoken words (timestamps
    stripped from the count) over the sum of spoken-chunk durations (silence excluded).
    This is the narrator's actual speaking rate, not a video-duration-diluted figure.
    Returns None if the transcript has no parseable [start-end] chunks."""
    wc, narr_s = transcript_speech(raw)
    if narr_s <= 0:
        return None
    return round(wc / (narr_s / 60))


def transcript_words(tjson):
    """Word timestamps of a transcript.json written by transcribe(), in time order."""
    out = []
    for seg in tjson.get('segments') or []:
        for w in seg.get('words') or []:
            if w.get('start_s') is not None and w.get('end_s') is not None and str(w.get('text') or '').strip():
                out.append({'start_s': float(w['start_s']), 'end_s': float(w['end_s']), 'text': str(w['text'])})
    return out


def pause_profile(words):
    """How a narrator pauses, from Whisper word timestamps: the silence between consecutive words. Computed the
    same way for the references and for this run's narration, so the two can be compared directly."""
    if len(words) < 2:
        return {}
    gaps = [max(0.0, b['start_s'] - a['end_s']) for a, b in zip(words, words[1:])]
    span = words[-1]['end_s'] - words[0]['start_s']
    mins = span / 60 if span > 0 else 0
    real = sorted(g for g in gaps if g >= 0.3)

    def per_min(th):
        return round(sum(1 for g in gaps if g >= th) / mins, 2) if mins else None

    def pct(q):
        return round(real[min(len(real) - 1, int(q * len(real)))], 2) if real else None
    return {'speech_span_s': round(span, 1), 'pauses_0_3s_plus_per_min': per_min(0.3),
            'pauses_0_8s_plus_per_min': per_min(0.8), 'pauses_1_5s_plus_per_min': per_min(1.5),
            'pauses_3s_plus_per_min': per_min(3.0), 'pause_median_s': pct(.5), 'pause_p90_s': pct(.9),
            'longest_pause_s': round(max(gaps), 2), 'silence_share': round(sum(gaps) / span, 3) if span > 0 else None}


def ref_pause_profiles(rd, refs):
    out = {}
    for vid in refs:
        t = read_json(rd / '10-media' / vid / 'transcript.json')
        if t:
            out[vid] = pause_profile(transcript_words(t))
    return out


def compute_ref_wpm(rd, refs, family):
    """Average WPM from the reference transcripts for the selected refs.
    Uses the sum of spoken-chunk durations (pure narration time) so the result
    matches the narrator's actual speaking rate — the pace ElevenLabs will generate at.
    Returns (rounded_wpm, per_ref_dict) or (None, {}) if no transcripts found."""
    per_ref = {}
    for vid in refs:
        tfile = rd / '10-media' / vid / 'transcript.txt'
        if not tfile.exists():
            continue
        wpm = wpm_from_transcript_raw(tfile.read_text(encoding='utf-8', errors='replace'))
        if wpm is not None:
            per_ref[vid] = wpm
    if not per_ref:
        return None, {}
    return round(statistics.mean(per_ref.values())), per_ref


def plan_facts(rd, video):
    vd = video_dir(rd, video)
    lock = read_json(vd / 'length-lock.json')
    blue = read_json(vd / 'blueprint.json')
    script = read_json(vd / 'script.json')
    beats = read_json(vd / 'beat-map.json')
    issues = []
    if not lock:
        issues.append('missing_locked_length')
        return {'ready': False, 'issues': issues}
    lines = script.get('lines') or []
    if not isinstance(lines, list) or not all(isinstance(x, dict) and str(x.get('text', '')).strip() for x in lines):
        issues.append('missing_or_invalid_script_lines')
        lines = []
    required_blue = ('audience_promise', 'narrative_approach', 'why_this_length', 'original_angle',
                     'ending_payoff', 'visual_grammar', 'factuality')
    for f in required_blue:
        if not str(blue.get(f, '')).strip():
            issues.append('blueprint_missing_' + f)
    if blue.get('factuality') == 'factual' and not blue.get('research_sources'):
        issues.append('factual_video_requires_independent_research_sources')
    if str(script.get('language') or '').lower() != str(lock.get('language') or '').lower():
        issues.append('script_language_differs_from_length_lock')
    issues += beat_map_facts(rd, video, lines, lock['target_length_s'])
    # Spoken words only: inline [audio tags] are sent to ElevenLabs but never spoken (count_words strips them).
    words = sum(count_words(x.get('text', '')) for x in lines)
    tags, tag_issues = script_tags(lines)
    pause_plan, pause_issues = script_pause_plan(lines)
    issues += tag_issues + pause_issues
    holds = round(sum(p['pause_after_s'] for p in pause_plan if p['via'] == 'edit'), 2)
    review = vd / 'editorial-review.md'
    review_text = review.read_text(encoding='utf-8', errors='replace') if review.exists() else ''
    flags, flag_issues = content_flags(lines, review_text)
    issues += flag_issues
    warnings = []
    # Creative direction first (10): the treatment is chosen and locked before the script is written, and it
    # stays the one that was locked. Then one fresh cold read of the script, every finding answered (06).
    gate, dlock, dfacts = direction_gate(rd, video)
    issues += gate
    warnings += dfacts['warnings']
    if dlock.get('late_reason'):
        warnings.append('creative direction was locked after the script existed: ' + str(dlock['late_reason']))
    # Made for an earlier direction (or before there was one): updated for real, or explicitly reapproved.
    issues += list(stale_files(rd, video, ('beat-map', 'script')).values())
    for name in (dlock.get('reapproved') or {}):
        ra = reapproved_for(dlock, name)
        if ra:
            warnings.append(f'{name} reapproved for direction revision {ra.get("rev")}: {ra.get("reason")}')
    snapshot = {str(r.get('id') or f'L{i + 1:03d}'): str(r.get('text') or '') for i, r in enumerate(lines)}
    script_review = review_state(vd, 'script', script_hash(lines), snapshot) if lines else \
        {'issues': ['script_review_missing'], 'warnings': [], 'rounds': 0}
    issues += script_review['issues']
    warnings += script_review['warnings']
    measured = voice_measurement(rd)
    tag_s = round(sum(tag_cost_s(t['tag'], measured.get('tag_costs_s')) for t in tags), 2)
    pace = float(script.get('pace_wpm') or lock.get('pace_wpm') or 0)
    if not pace:
        issues.append('script_missing_narration_pace')
    target = lock['target_length_s']
    # Narration = spoken words at a pace + the voice's natural gap after every line + what the tags add.
    # A pause the story wants longer than that gap exists only if it is realised (pause_via): a tag (inside
    # the narration) or an edit hold (added on top of it). Planned pauses are never sent to ElevenLabs.
    early_narr = (words * 60 / pace + DEFAULT_LINE_OVERHEAD_S * len(lines) + tag_s) if pace else 0
    forecast = round(early_narr + holds, 2) if pace else 0
    real_narr = real = None
    if measured.get('wpm') and lines:
        pace_real = float(measured.get('forecast_wpm') or measured['wpm'])
        real_narr = round(words * 60 / pace_real + measured['per_line_overhead_s'] * len(lines) + tag_s, 2)
        real = round(real_narr + holds, 2)
        # Once this voice is measured, the forecast has to land where export-check will look.
        if abs(real - target) > max(4, target * lock.get('tolerance_export_pct', .025)):
            issues.append('real_forecast_outside_export_tolerance')
    elif pace and abs(forecast - target) > max(10, .08 * target):
        issues.append('script_forecast_misses_locked_length_by_over_8pct')
    # Research <-> script: a line that states a number (a date, a count, a distance) and is tied to no claim.
    # Not blocking (a count of sides or the narrator's premise needs none); each consequential one gets a claim
    # before its part is recorded, because a wrong number found later costs a re-record.
    claims = read_json(rd / '30-research' / f'video-{int(video):02d}' / 'claims.json')
    covered = {r for c in (claims.get('claims') or []) for r in (c.get('line_refs') or [])}
    number_rx = re.compile(r"\d|\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
                           r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
                           r"eighty|ninety|hundred|thousand|million)\b", re.I)
    numbers_without_claim = [str(x.get('id')) for x in lines
                             if number_rx.search(strip_tags(x.get('text') or '')) and str(x.get('id')) not in covered]
    voice_pace = measured.get('forecast_wpm') or measured.get('wpm')
    if voice_pace and script.get('pace_wpm') and abs(float(script['pace_wpm']) - float(voice_pace)) > 3:
        warnings.append(f"script pace_wpm {script['pace_wpm']} differs from the voice's measured {voice_pace} "
                        "(script words per speech minute); the real forecast uses the measured one: set the script's "
                        "pace_wpm to it so one number is in use")
    if not review.exists():
        issues.append('editorial_review_missing')
    return {'ready': not issues, 'issues': issues, 'warnings': warnings, 'script_lines': len(lines),
            'words': words, 'narration_pace_wpm': pace,
            'pace_sources': {'references_wpm': lock.get('pace_wpm'), 'script_wpm': script.get('pace_wpm'),
                             'voice_measured_wpm': measured.get('wpm'),
                             'voice_per_line_gap_s': round(measured['per_line_overhead_s'], 3) if measured else None},
            'audio_tags': tags, 'tag_time_s': tag_s, 'pause_plan': pause_plan, 'edit_holds_s': holds,
            'content_flags': flags, 'numbers_without_claim': numbers_without_claim,
            'creative': {'direction_locked': bool(dlock), 'locked_late': bool(dlock.get('late_reason')),
                         'treatment': dfacts.get('chosen_treatment'), 'production_rev': dlock.get('production_rev'),
                         'outdated': sorted(stale_files(rd, video)), 'script_review_rounds': script_review['rounds'],
                         'majors_closed_by_decision': script_review.get('majors_closed_by_decision') or []},
            'writing_signals': writing_signals(lines, lock.get('language') or script.get('language') or 'en'),
            'forecast_s': forecast, 'real_narration_forecast_s': real_narr, 'real_forecast_s': real,
            'locked_target_s': target,
            'export_window_s': [round(target - max(4, target * lock.get('tolerance_export_pct', .025)), 2),
                                round(target + max(4, target * lock.get('tolerance_export_pct', .025)), 2)],
            'target_words_without_pauses': round(target * pace / 60) if pace else None}


def cmd_plan_check(args):
    rd, st = run_folder(args)
    result = plan_facts(rd, args.video)
    emit({'video': int(args.video), **result}, 0 if result['ready'] else 2)


def chunks_for_lines(lines, maximum):
    chunks = []
    cur, start = [], None
    for i, row in enumerate(lines, 1):
        text = str(row['text']).strip()
        if len(text) > maximum:
            error('One script line exceeds safe TTS request size: split it into complete sentences.', {'line': i, 'chars': len(text)})
        new = '\n'.join(cur + [text])
        if cur and len(new) > maximum:
            chunks.append({'line_start': start, 'line_end': i-1, 'text': '\n'.join(cur)})
            cur, start = [], None
        if start is None:
            start = i
        cur.append(text)
    if cur:
        chunks.append({'line_start': start, 'line_end': len(lines), 'text': '\n'.join(cur)})
    return chunks


def chunks_from_manifest(old_chunks, lines):
    """Keep the recorded parts' line boundaries, so editing one line changes only the part that holds it
    (fresh greedy chunking would shift every later boundary and force a full re-record). None when the
    boundaries no longer cover the script exactly (lines were added or removed)."""
    out, cursor = [], 0
    for c in old_chunks:
        try:
            lo, hi = int(c['line_start']), int(c['line_end'])
        except (KeyError, TypeError, ValueError):
            return None
        if lo != cursor + 1 or hi < lo or hi > len(lines):
            return None
        out.append({'line_start': lo, 'line_end': hi,
                    'text': '\n'.join(str(r['text']).strip() for r in lines[lo - 1:hi])})
        cursor = hi
    return out if cursor == len(lines) else None


def model_limit(model):
    # GET /v1/models, 2026-11-19: eleven_v4 and eleven_v4_turbo take 10,000 characters per request.
    known = {'eleven_v4': 10000, 'eleven_v4_turbo': 10000}
    return known.get(model, 3000)


def voice_calibrated(rd, voice_id, model_id, settings):
    """True when this exact voice/model/settings has a real measured pace from a chunk of 300+ words."""
    vl = read_json(rd / '60-voice' / 'voice-lock.json')
    m = vl.get('measured') or {}
    if m:
        return (m.get('voice_id') == voice_id and m.get('model_id') == model_id
                and (m.get('settings') or {}) == (settings or {}) and (m.get('words') or 0) >= 300)
    # older hand-recorded measurement (from a real chunk of the same voice and settings)
    return bool(vl.get('measured_wpm') and vl.get('measured_overhead_s') and vl.get('voice_id') == voice_id
                and (vl.get('settings') or {}) == (settings or {}))


def preflight_elevenlabs_balance(key, remaining_characters, safety_factor=1.15):
    """Check the subscription character allowance before ANY billable TTS call.

    Character allowance is not a guaranteed monetary-credit estimate for every
    model, tier or negotiated contract. Require human verification of the actual
    model's price, even when this preliminary guard passes.
    """
    req = urllib.request.Request('https://api.elevenlabs.io/v1/user/subscription',
                                 headers={'xi-api-key': key}, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        error('Cannot verify ElevenLabs subscription balance; no paid TTS requests were made.',
              f'{type(exc).__name__}: {str(exc)[:180]}')
    try:
        remaining = int(data['character_limit']) - int(data['character_count'])
    except (KeyError, TypeError, ValueError) as exc:
        error('Subscription API returned no usable character allowance; no paid TTS requests were made.', str(exc))
    needed = math.ceil(remaining_characters * safety_factor)
    if remaining < needed:
        error('Insufficient reported ElevenLabs character allowance for this entire remaining narration.',
              {'available_character_allowance': remaining, 'required_characters': remaining_characters,
               'reserve_adjusted_minimum': needed, 'note': 'Verify actual credit pricing for your model; overage was not assumed.'})
    return {'subscription_status': data.get('status'), 'available_character_allowance': remaining,
            'remaining_script_characters': remaining_characters, 'reserve_adjusted_minimum': needed,
            'warning': 'This check is based on character allowance, not model-specific credit cost; no guarantee against quota or billing limits.'}


def elevenlabs_request(method, path, key, body=None, params=None, timeout=60):
    url = 'https://api.elevenlabs.io' + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    headers = {'xi-api-key': key}
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def cmd_voice_candidates(args):
    """Suggest up to --count candidate voices (free, from the account's existing voices,
    and/or billed Voice Design previews), save each candidate's preview audio, transcribe
    it (Whisper) and record its preview_wpm with the references' yardstick. A preview is
    short: its pace does not predict the voice's real pace on a full chunk (measured on one
    run: preview 195 -> real 180; a 209 human sample -> 178). Each preview's delivery is
    measured too (pitch range and movement, loudness contrast), because the agents cannot
    listen: they choose for the treatment's narrator from descriptions, transcripts and these
    measurements; the user may listen and overrule. The real pace comes from the calibration part.
    Writes a report; picks nothing itself.
    An earlier round's report is kept as candidates-<time>.json, never overwritten."""
    rd, st = run_folder(args)
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    vd = video_dir(rd, args.video)
    outdir = rd / '60-voice' / f'video-{int(args.video):02d}' / 'candidates'
    outdir.mkdir(parents=True, exist_ok=True)
    design_n = max(0, args.design)
    free_n = max(0, args.count - design_n)
    candidates = []

    if free_n:
        try:
            data = elevenlabs_request('GET', '/v1/voices', key)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            error('Cannot list ElevenLabs account voices.', f'{type(exc).__name__}: {str(exc)[:200]}')
        pool = data.get('voices') or []
        needle = (args.search or '').strip().lower()
        if needle:
            def matches(v):
                hay = ' '.join([str(v.get('name') or '')] +
                               [str(x) for x in (v.get('labels') or {}).values()]).lower()
                return needle in hay
            pool = [v for v in pool if matches(v)]
        for v in pool[:free_n]:
            candidates.append({'source': 'account_voice', 'voice_id': v['voice_id'], 'name': v.get('name'),
                                'labels': v.get('labels') or {}, 'preview_url': v.get('preview_url')})
        if len(candidates) < free_n:
            error('Not enough existing account voices matched the search; broaden --search, lower --count, '
                  'or raise --design to fill the rest with newly designed voices.',
                  {'matched': len(candidates), 'requested': free_n})

    if design_n:
        if not args.design_description:
            error('--design-description is required when --design > 0 '
                  '(the narrator the locked treatment describes: character, register, age, accent, delivery).')
        text = args.design_text
        if not text:
            script = read_json(vd / 'script.json')
            lines = script.get('lines') or []
            text = ' '.join(l['text'] for l in lines[:8])[:1000]
        if not (100 <= len(text) <= 1000):
            error('Voice Design sample text must be 100-1000 characters.', {'characters': len(text)})
        made = 0
        while made < design_n:
            try:
                resp = elevenlabs_request('POST', '/v1/text-to-voice/design', key,
                                          body={'voice_description': args.design_description, 'text': text})
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                error('Voice Design call failed (this call may bill regardless of the error). '
                      'Verify your ElevenLabs account before retrying.', f'{type(exc).__name__}: {str(exc)[:200]}')
            previews = resp.get('previews') or []
            if not previews:
                error('Voice Design returned no previews.', resp)
            for prev in previews:
                if made >= design_n:
                    break
                candidates.append({'source': 'voice_design', 'voice_id': prev['generated_voice_id'],
                                    'name': f"design-{prev['generated_voice_id'][:8]}", 'labels': {},
                                    'audio_base_64': prev['audio_base_64']})
                made += 1

    results = []
    for i, c in enumerate(candidates, 1):
        stem = f'candidate-{i:02d}-{c["voice_id"][:10]}'
        fname = outdir / f'{stem}.mp3'
        if c['source'] == 'account_voice':
            if not c.get('preview_url'):
                results.append({**{k: c[k] for k in ('source', 'voice_id', 'name', 'labels')},
                                'file': None, 'preview_wpm': None, 'error': 'voice has no preview_url'})
                continue
            try:
                with urllib.request.urlopen(c['preview_url'], timeout=30) as resp:
                    fname.write_bytes(resp.read())
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
                results.append({**{k: c[k] for k in ('source', 'voice_id', 'name', 'labels')},
                                'file': None, 'preview_wpm': None,
                                'error': f'preview download failed: {type(exc).__name__}: {str(exc)[:160]}'})
                continue
        else:
            fname.write_bytes(base64.b64decode(c['audio_base_64']))
        tpath = outdir / f'{stem}.json'
        wpm, heard, voice_delivery = None, None, None
        try:
            transcribe(fname, tpath, args.whisper_model, args.device, args.compute_type)
            raw = tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace')
            wpm = wpm_from_transcript_raw(raw)
            heard = strip_transcript_timestamps(raw).strip() or None
        except (RuntimeError, ValueError, OSError) as exc:
            heard = f'transcription failed: {type(exc).__name__}: {str(exc)[:160]}'
        voice_delivery = measure_file_delivery(fname, tpath)
        results.append({'source': c['source'], 'voice_id': c['voice_id'], 'name': c.get('name'),
                        'labels': c.get('labels'), 'file': str(fname), 'preview_wpm': wpm, 'heard_text': heard,
                        'measured_delivery': voice_delivery})
    report = {'video': int(args.video), 'search': args.search, 'design_description': args.design_description,
              'made_at': now(), 'candidates': results}
    report_path = outdir.parent / 'candidates.json'
    if report_path.exists():   # keep every earlier round
        shutil.move(str(report_path), str(report_path.with_name(
            'candidates-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')))
    write_json(report_path, report)
    emit({'ok': True, 'candidates_file': str(report_path), 'count': len(results), 'candidates': results,
          'guidance': 'The agents cannot hear these files. Choose for the chosen treatment\'s narrator (direction.json): '
                      'compare each candidate\'s description and labels, what it said, and its measured delivery '
                      '(pitch range and movement, loudness contrast; a short sample, indicative only) with the '
                      'references\' (20-analysis/av). The files are listed for the user, who may listen and overrule. '
                      'preview_wpm does not predict real pace. Lock the pick with voice-pick; the real pace and '
                      'delivery are measured on the first real part (tts --max-parts 1, then narration-measure).'})


def cmd_voice_pick(args):
    """Lock the run's narrator voice. One voice for the whole run (every video, every
    language) unless --replace is explicitly passed to deliberately change it.
    A Voice Design candidate's generated_voice_id is not a usable voice until it is saved
    to the account library (POST /v1/text-to-voice) -- done here automatically, billed
    only in that it finalizes a design already generated, not a new design call."""
    rd, st = run_folder(args)
    lockfile = rd / '60-voice' / 'voice-lock.json'
    if lockfile.exists() and not args.replace:
        error('Voice already locked for this run. Pass --replace to deliberately change it.',
              {'file': str(lockfile)})
    try:
        settings = json.loads(args.settings) if args.settings else {}
    except ValueError as exc:
        error('--settings must be valid JSON.', str(exc))
    preview_wpm, source, design_description = None, None, None
    vdir = rd / '60-voice' / f'video-{int(args.video):02d}'
    for cfile in [vdir / 'candidates.json'] + sorted(vdir.glob('candidates-*.json'), reverse=True):
        cdata = read_json(cfile)
        hit = next((c for c in (cdata.get('candidates') or []) if c.get('voice_id') == args.voice_id), None)
        if hit:
            preview_wpm = hit.get('preview_wpm', hit.get('measured_wpm'))
            source, design_description = hit.get('source'), cdata.get('design_description')
            break
    final_voice_id = args.voice_id
    saved_from = None
    key = elevenlabs_key() if source == 'voice_design' else None
    if source == 'voice_design':
        if not key:
            error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
        try:   # already saved earlier (the save returns 400 the second time): use the library voice as it is
            elevenlabs_request('GET', '/v1/voices/' + urllib.parse.quote(args.voice_id, safe=''), key)
            source = 'account_voice'
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError):
            pass
    if source == 'voice_design':
        if not args.name:
            error('--name is required to save a Voice Design candidate as a permanent voice '
                  '(ElevenLabs requires voice_name).')
        try:
            resp = elevenlabs_request('POST', '/v1/text-to-voice', key,
                                      body={'voice_name': args.name,
                                            'voice_description': design_description or args.name,
                                            'generated_voice_id': args.voice_id})
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            error('Could not save the designed voice to your ElevenLabs library.',
                  f'{type(exc).__name__}: {str(exc)[:200]}')
        if not resp.get('voice_id'):
            error('Save call returned no voice_id.', resp)
        saved_from = args.voice_id
        final_voice_id = resp['voice_id']
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    old = read_json(lockfile)
    lock = {'voice_id': final_voice_id, 'generated_voice_id': saved_from, 'name': args.name or old.get('name'),
            'settings': settings, 'preview_wpm': preview_wpm, 'locked_at': now(),
            'rule': 'One voice per run across every video and language; '
                    '--replace required to deliberately change it.',
            'pace_note': 'preview_wpm is a short-sample figure and is never used to size the script; the real '
                         'pace is measured (narration-measure) on the first real chunk.'}
    m = old.get('measured') or {}
    if m.get('voice_id') == final_voice_id and (m.get('settings') or {}) == settings:
        lock['measured'] = m   # same voice and settings: the real measurement still holds
    write_json(lockfile, lock)
    emit({'ok': True, 'lock_file': str(lockfile), 'voice_id': final_voice_id,
          'saved_from_generated_voice_id': saved_from, 'preview_wpm': preview_wpm,
          'measured_kept': bool(lock.get('measured')),
          'guidance': f'Pass --voice-id {final_voice_id} to every "tts"/"voice-probe" call for this run. '
                      'Next: tts --max-parts 1 --execute (the calibration chunk), then narration-measure.'})


def cmd_voice_probe(args):
    """Hear a voice (and any inline tag written into --text) on a short real passage of this run's script,
    via one short billed call, before the paid narration: how the voice and the tags SOUND. Its WPM is
    reported but a sample under ~300 words does not predict real pace (measured here: short samples read up
    to 199 WPM, the same voice 175-188 on real chunks); the real pace comes from the calibration chunk.
    Separate from tts's chunk/resume state; does not touch script.json, length-lock.json or 50-audio/."""
    rd, st = run_folder(args)
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    vd = video_dir(rd, args.video)
    lock = read_json(vd / 'length-lock.json', required=True)
    text = args.text
    if not text:
        script = read_json(vd / 'script.json', required=True)
        buf, total = [], 0
        for l in script.get('lines') or []:
            buf.append(l['text'])
            total += len(l['text']) + 1
            if total >= 450:
                break
        text = ' '.join(buf)
    sent_text = (args.delivery + ' ' if args.delivery else '') + text
    limit = model_limit(args.model_id)
    if len(sent_text) > limit:
        error('Probe text exceeds the model request limit.', {'characters': len(sent_text), 'limit': limit})
    voice_settings = parse_voice_settings(args.settings, args.model_id)
    budget = preflight_elevenlabs_balance(key, len(sent_text), args.credit_safety_factor)
    body = {'text': sent_text, 'model_id': args.model_id}
    if voice_settings:
        body['voice_settings'] = voice_settings
    if lock.get('language') and args.model_id != 'eleven_multilingual_v2':
        body['language_code'] = lock['language'][:2]
    url = ('https://api.elevenlabs.io/v1/text-to-speech/' + urllib.parse.quote(args.voice_id, safe='')
           + '?output_format=mp3_44100_128')
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST',
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        error('Probe TTS call failed (may have been billed regardless of the error). '
              'Verify your ElevenLabs account before retrying.', f'{type(exc).__name__}: {str(exc)[:200]}')
    if len(raw) < 1024:
        error('Audio response too short.', {'bytes': len(raw)})
    outdir = rd / '60-voice' / f'video-{int(args.video):02d}' / 'probes'
    outdir.mkdir(parents=True, exist_ok=True)
    n = len(list(outdir.glob('probe-*.mp3'))) + 1
    stem = f'probe-{n:02d}-{args.voice_id[:10]}'
    fname = outdir / f'{stem}.mp3'
    fname.write_bytes(raw)
    tpath = outdir / f'{stem}.json'
    transcribe(fname, tpath, args.whisper_model, args.device, args.compute_type)
    rawtxt = tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace')
    wpm = wpm_from_transcript_raw(rawtxt)
    heard = strip_transcript_timestamps(rawtxt).strip()
    sent_tags = [classify_tag(m.group(1))['tag'] for m in TAG_RE.finditer(sent_text)]
    spoken_back = [t for t in sent_tags if t.strip('[]') and t.strip('[]').split()[0] in heard.lower()]
    emit({'ok': True, 'file': str(fname), 'voice_id': args.voice_id, 'model_id': args.model_id,
          'voice_settings': voice_settings or None, 'delivery': args.delivery or None,
          'sent_characters': len(sent_text), 'credit_preflight': budget, 'sample_words': count_words(text),
          'short_sample_wpm': wpm, 'references_pace_wpm': lock.get('pace_wpm'), 'tags_sent': sent_tags,
          'tags_maybe_read_aloud': spoken_back, 'heard_text': heard,
          'measured_delivery': measure_file_delivery(fname, tpath),
          'guidance': 'No agent here can hear this file. What stands in: the words heard back (a tag that shows up '
                      'in heard_text was read aloud) and measured_delivery (how the voice moves; a short sample, '
                      'indicative only), next to the treatment\'s narrator and the references. The user may listen '
                      'to the file. short_sample_wpm does not predict the real pace; do not size the script on it. '
                      'Real pace: tts --max-parts 1 --execute, then narration-measure.'})


def parse_voice_settings(raw, model_id):
    try:
        voice_settings = json.loads(raw) if raw else {}
    except ValueError as exc:
        error('--settings must be valid JSON (e.g. \'{"stability": 0.7, "similarity_boost": 0.8}\').', str(exc))
    if not isinstance(voice_settings, dict):
        error('--settings must be a JSON object.')
    # From each model's own capability flags (GET /v1/models, 2026-11-19): eleven_v4 and eleven_v4_turbo have
    # can_use_style=false and can_use_speaker_boost=false. Speed is not used: the user's standing decision.
    allowed = ('stability', 'similarity_boost')
    for k in voice_settings:
        if k not in allowed:
            error(f'Model {model_id!r} is used here with these voice settings only.', {'allowed': list(allowed), 'got': k})
    return voice_settings


def cmd_tts(args):
    rd, st = run_folder(args)
    chk = plan_facts(rd, args.video)
    if not chk['ready']:
        error('Plan must pass objective checks before billed audio generation', chk['issues'])
    vd = video_dir(rd, args.video)
    script = read_json(vd / 'script.json', required=True)
    lock = read_json(vd / 'length-lock.json', required=True)
    if not (1.0 <= args.credit_safety_factor <= 3.0):
        error('--credit-safety-factor must be from 1.0 to 3.0')
    if args.max_parts is not None and args.max_parts < 1:
        error('--max-parts must be at least 1.')
    voice_settings = parse_voice_settings(args.settings, args.model_id)
    limit = min(args.max_chars or model_limit(args.model_id), model_limit(args.model_id), 8000)
    narrdir = rd / '50-audio' / f'video-{int(args.video):02d}'
    manifest_path = narrdir / 'manifest.json'
    existing = read_json(manifest_path)
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    other_take = bool(existing) and any(existing.get(x) != y for x, y in
                                        (('model_id', args.model_id), ('voice_id', args.voice_id),
                                         ('language', lock['language'])))
    start_over = other_take or args.rechunk
    if start_over and not args.archive_existing and existing:
        error('The recorded audio uses another voice/model/language, or --rechunk asks for new part boundaries. '
              'Pass --archive-existing to move the whole folder aside (nothing is deleted; every part is re-billed).',
              {'folder': str(narrdir), 'recorded_with': {k: existing.get(k) for k in ('voice_id', 'model_id', 'language')}})
    chunks = None
    if existing.get('chunks') and not start_over:
        chunks = chunks_from_manifest(existing['chunks'], script['lines'])
        if chunks is None:
            error('Lines were added or removed since the parts were recorded, so their boundaries no longer fit. '
                  'Restore the line count, or re-record everything: --rechunk --archive-existing (every part re-billed).')
    if chunks is None:
        chunks = chunks_for_lines(script['lines'], limit)
    for i, c in enumerate(chunks, 1):
        if len(c['text']) > model_limit(args.model_id):
            error(f'Part {i} is now longer than the model accepts in one request.', {'characters': len(c['text'])})
    spec = {'model_id': args.model_id, 'voice_id': args.voice_id, 'language': lock['language'],
            'chunks': [{'id': i+1, 'line_start': c['line_start'], 'line_end': c['line_end'],
                        'text_sha256': hashlib.sha256(c['text'].encode()).hexdigest(),
                        'file': f'part-{i+1:03d}.mp3', 'characters': len(c['text'])}
                       for i, c in enumerate(chunks)]}
    old_chunks = {} if start_over else {c.get('id'): c for c in existing.get('chunks') or []}
    finished_before = [] if start_over else list(existing.get('finished_parts') or [])
    changed = [s['id'] for s in spec['chunks'] if s['id'] in finished_before
               and old_chunks.get(s['id'], {}).get('text_sha256') != s['text_sha256']]
    delivery_overhead = len(args.delivery) + 1 if args.delivery else 0
    if not args.execute:
        todo = [c for c, s in zip(chunks, spec['chunks']) if s['id'] not in finished_before or s['id'] in changed]
        emit({'ok': True, 'mode': 'dry_run_no_charges', 'video': args.video,
              'parts': len(chunks), 'characters_total': sum(len(x['text']) for x in chunks) + delivery_overhead * len(chunks),
              'parts_to_record': [s['id'] for s in spec['chunks'] if s['id'] not in finished_before or s['id'] in changed],
              'changed_recorded_parts': changed, 'starts_over': start_over,
              'characters_to_record': sum(len(x['text']) for x in todo) + delivery_overhead * len(todo),
              'calibrated': voice_calibrated(rd, args.voice_id, args.model_id, voice_settings),
              'model_limit_per_request': model_limit(args.model_id), 'delivery': args.delivery or None,
              'voice_settings': voice_settings or None,
              'target_length_s': lock['target_length_s'], 'candidate_manifest': spec,
              'next': 'Review credits, voice and preview. Re-run with --execute only after approving cost.'})
        return
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    if changed and not args.rerecord_changed:
        error('Script lines changed inside parts that are already recorded. Re-record only those parts with '
              '--rerecord-changed (their old takes move to superseded/, never deleted).',
              {'changed_parts': changed,
               'characters': sum(s['characters'] for s in spec['chunks'] if s['id'] in changed)})
    kept = [] if start_over else [x for x in finished_before if x not in changed
                                  and (narrdir / f'part-{x:03d}.mp3').is_file()
                                  and (narrdir / f'part-{x:03d}.mp3').stat().st_size > 1024]
    remaining_chunks = [c for i, c in enumerate(chunks) if (i + 1) not in kept]
    batch = remaining_chunks[:args.max_parts] if args.max_parts else remaining_chunks
    if len(batch) > 1 and not args.skip_calibration and not voice_calibrated(rd, args.voice_id, args.model_id, voice_settings):
        error('Calibrate first: this voice/model/settings has no real measured pace yet. Record one part '
              '(--max-parts 1 --execute), run narration-measure, check plan-check\'s real_forecast_s, then record '
              'the rest. --skip-calibration overrides this.')
    if not (0.1 <= args.assume_cost_ratio <= 1.0):
        error('--assume-cost-ratio must be from 0.1 to 1.0 (1.0 = trust the model\'s documented '
              'character_cost_multiplier; below 1.0 is an explicit, auditable override for a '
              'ratio you personally verified against real billing deltas this session).')
    raw_remaining_chars = sum(len(c['text']) for c in batch) + delivery_overhead * len(batch)
    # The balance is checked before anything on disk moves: a failed preflight leaves the folder as it was.
    budget = preflight_elevenlabs_balance(key, round(raw_remaining_chars * args.assume_cost_ratio),
                                         args.credit_safety_factor) if batch else {'remaining_script_characters': 0}
    if remaining_chunks:
        budget['raw_characters_before_ratio'] = raw_remaining_chars
        budget['assumed_cost_ratio'] = args.assume_cost_ratio
    history = list(existing.get('history') or [])
    if start_over and existing:
        archive = narrdir.with_name(f'{narrdir.name}-archive-{stamp}')
        shutil.move(str(narrdir), str(archive))
        history = [{'at': now(), 'archived_previous_take_to': str(archive)}]
        existing = {}
    narrdir.mkdir(parents=True, exist_ok=True)
    if changed:
        sup = narrdir / 'superseded'
        sup.mkdir(exist_ok=True)
        for pid in changed:
            part = narrdir / f'part-{pid:03d}.mp3'
            if part.exists():
                shutil.move(str(part), str(sup / f'part-{pid:03d}-{stamp}.mp3'))
        if (narrdir / 'narration.wav').exists():
            shutil.move(str(narrdir / 'narration.wav'), str(sup / f'narration-{stamp}.wav'))
        history.append({'at': now(), 'rerecorded_parts': changed, 'old_takes': str(sup)})
    manifest = {**spec, 'status': 'partial', 'created_at': existing.get('created_at', now()),
                'credit_preflight': budget, 'delivery': args.delivery or None, 'voice_settings': voice_settings or None,
                'finished_parts': kept, 'history': history}
    write_json(manifest_path, manifest)
    new_parts_done = 0
    for i, c in enumerate(chunks):
        fname = narrdir / f'part-{i+1:03d}.mp3'
        if (i+1) in manifest['finished_parts'] and fname.exists() and fname.stat().st_size > 1024:
            continue
        if args.max_parts and new_parts_done >= args.max_parts:
            break
        sent_text = (args.delivery + ' ' + c['text']) if args.delivery else c['text']
        body = {'text': sent_text, 'model_id': args.model_id}
        if voice_settings:
            body['voice_settings'] = voice_settings
        if lock['language'] and args.model_id != 'eleven_multilingual_v2':
            body['language_code'] = lock['language'][:2]
        if i:
            body['previous_text'] = chunks[i-1]['text'][-300:]
        if i < len(chunks)-1:
            body['next_text'] = chunks[i+1]['text'][:300]
        url = 'https://api.elevenlabs.io/v1/text-to-speech/' + urllib.parse.quote(args.voice_id, safe='')
        url += '?output_format=mp3_44100_128'
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST',
                                     headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            if len(raw) < 1024:
                raise RuntimeError('Audio response too short')
            temp = fname.with_suffix('.download')
            temp.write_bytes(raw)
            _ = probe(temp)  # ffprobe reads audio, even though temp suffix is generic
            temp.replace(fname)
            manifest['finished_parts'].append(i+1)
            write_json(manifest_path, manifest)
            new_parts_done += 1
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, RuntimeError) as exc:
            manifest['error'] = f'part {i+1}: {type(exc).__name__}: {str(exc)[:250]}'
            write_json(manifest_path, manifest)
            error('Partial ElevenLabs recording: BLOCKED (never shorten video to match credits).', manifest['error'])
    if len(manifest['finished_parts']) < len(chunks):
        emit({'ok': True, 'mode': 'partial_by_design_max_parts', 'new_parts_this_call': new_parts_done,
              'finished_parts': manifest['finished_parts'], 'total_parts': len(chunks),
              'parts_dir': str(narrdir),
              'next': 'Listen to the new part(s), then narration-measure (real pace, natural gap per line, what '
                      'each tag cost) and plan-check (real_forecast_s against the export window). Adjust the '
                      'lines of the parts not yet recorded if needed, then re-run the same tts command (no '
                      '--max-parts) for the rest -- finished parts are kept, never re-billed.'})
        return
    concat = narrdir / 'parts.txt'
    concat.write_text(''.join("file '" + str((narrdir / x['file']).resolve()).replace('\\', '/').replace("'", "'\\''") + "'\n"
                              for x in manifest['chunks']), encoding='utf-8')
    outpath = narrdir / 'narration.wav'
    run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-f', 'concat', '-safe', '0',
             '-i', str(concat), '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', str(outpath)])
    manifest['status'] = 'complete'
    manifest['duration_s'] = probe(outpath)['duration_s']
    manifest.pop('error', None)
    write_json(manifest_path, manifest)
    gate = audio_facts(rd, args.video)
    emit({'ok': gate['ready'], 'audio_file': str(outpath), 'duration_s': manifest['duration_s'],
          'audio_gate': gate}, 0 if gate['ready'] else 2)


def audio_facts(rd, video):
    vd = video_dir(rd, video)
    lock = read_json(vd / 'length-lock.json')
    script = read_json(vd / 'script.json')
    folder = rd / '50-audio' / f'video-{int(video):02d}'
    manifest = read_json(folder / 'manifest.json')
    issues = []
    if not lock:
        issues.append('missing_duration_lock')
    if not manifest:
        issues.append('narration_manifest_missing')
    if manifest.get('status') != 'complete':
        issues.append('audio_is_partial_or_unverified')
    if len(manifest.get('finished_parts', [])) != len(manifest.get('chunks', [])):
        issues.append('not_all_tts_parts_finished')
    cursor = 0
    part_durations = []
    script_lines = script.get('lines') or []
    for chunk in manifest.get('chunks') or []:
        if chunk.get('line_start') != cursor + 1 or chunk.get('line_end', 0) < chunk['line_start']:
            issues.append('audio_line_coverage_gap_overlap')
        cursor = chunk.get('line_end', cursor)
        part = folder / chunk.get('file', '__missing__')
        if not part.is_file():
            issues.append('audio_file_missing:' + chunk.get('file', '?'))
        else:
            try:
                part_durations.append(probe(part)['duration_s'])
            except (RuntimeError, ValueError):
                issues.append('audio_part_unreadable:' + chunk.get('file', '?'))
        lo = chunk.get('line_start', 0)
        hi = chunk.get('line_end', 0)
        text = '\n'.join(str(row.get('text') or '').strip() for row in script_lines[max(0, lo-1):hi])
        if text and hashlib.sha256(text.encode('utf-8')).hexdigest() != chunk.get('text_sha256'):
            issues.append('audio_part_text_hash_mismatch:' + chunk.get('file', '?'))
    if cursor != len(script.get('lines') or []):
        issues.append('some_script_lines_unrecorded')
    fname = folder / 'narration.wav'
    duration = None
    if not fname.is_file():
        issues.append('joined_narration_missing')
    else:
        try:
            duration = probe(fname)['duration_s']
        except (RuntimeError, ValueError) as exc:
            issues.append('narration_duration_unreadable:' + str(exc)[:160])
    target = lock.get('target_length_s')
    if target and duration and abs(target-duration) > max(8, target * lock.get('tolerance_audio_pct', 0.04)):
        issues.append('narration_duration_outside_locked_tolerance')
    if duration and part_durations and abs(sum(part_durations) - duration) > max(3, 0.01*duration):
        issues.append('joined_narration_differs_from_sum_of_parts')
    # The picture can't be shorter than the narration, and export-check holds the export to its own (tighter)
    # window: narration plus the planned edit holds must already fit it, or the export can never pass.
    holds = edit_holds_s(script_lines)
    window = None
    if target and duration:
        tol_e = max(4, target * lock.get('tolerance_export_pct', .025))
        window = [round(target - tol_e, 2), round(target + tol_e, 2)]
        if duration + holds > target + tol_e:
            issues.append('narration_plus_edit_holds_longer_than_export_window')
        elif duration + holds < target - tol_e:
            issues.append('narration_plus_edit_holds_shorter_than_export_window')
    return {'ready': not issues, 'issues': issues, 'duration_s': duration,
            'target_length_s': target, 'edit_holds_s': holds,
            'expected_edit_s': round(duration + holds, 2) if duration else None, 'export_window_s': window,
            'script_lines': len(script.get('lines') or []),
            'recorded_lines': cursor, 'manifest_status': manifest.get('status')}


def cmd_audio_check(args):
    rd, st = run_folder(args)
    result = audio_facts(rd, args.video)
    emit(result, 0 if result['ready'] else 2)


def shot_structure_sha(shots):
    """What the edit's timing depends on: which shots, for which beats, over which lines (prompts can change freely)."""
    return canonical_sha([[str(s.get(k)) for k in ('id', 'beat_id', 'line_start', 'line_end')] for s in shots or []])


def _run_file(rd, f):
    p = Path(str(f or '')).expanduser()
    return (p if p.is_absolute() else rd / p).resolve()


def timeline_facts(rd, video):
    """The CapCut project as recorded in timeline.json, against the plan it must follow: every visual segment is a
    retimed shot of the current edit plan (shot_id), for that shot's beat, starting where retime-shots put it; every
    shot is in the cut; every sound segment names the beats it serves and plays inside them; music comes from the
    gated worker under the current direction; the stills are current (stills_facts); the edit plan describes the
    current shots, script and direction. Plus the length and format checks the timeline always had."""
    n = int(video)
    vd = video_dir(rd, n)
    lock = read_json(vd / 'length-lock.json')
    dlock = read_json(vd / 'direction-lock.json')
    track = read_json(rd / '70-edit' / f'video-{n:02d}' / 'timeline.json')
    sound = audio_facts(rd, n)
    issues = ([] if sound['ready'] else ['audio_gate_failed'])
    warnings = []
    if not lock:
        issues.append('length_lock_missing')
    seq = track.get('visual_segments') or []
    if not seq:
        issues.append('timeline_visual_segments_missing')
    beat_ids = {str(b.get('id')) for b in read_json(vd / 'beat-map.json').get('beats') or []}
    plan = read_json(artifact_path(rd, n, 'edit'))
    plan_shots = {str(s.get('id')): s for s in plan.get('shots') or []}
    if not plan:
        issues.append('edit_plan_missing_run_retime_shots')
    else:
        lines = read_json(vd / 'script.json').get('lines') or []
        cur_shots = read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []
        if plan.get('shot_structure_sha256') != shot_structure_sha(cur_shots) or \
                plan.get('script_sha256') != script_hash(lines):
            issues.append('edit_plan_outdated_rerun_retime_shots')
        if not media_current(dlock, 'edit', (plan.get('direction') or {}).get('production_rev')):
            issues.append('edit_plan_made_for_an_earlier_direction')
    cursor, seen = 0.0, {}
    for i, clip in enumerate(seq, 1):
        try:
            a, b = float(clip['start_s']), float(clip['end_s'])
            if abs(a-cursor) > .16 or b <= a:
                issues.append(f'visual_gap_overlap_{i}')
            if not str(clip.get('beat_id') or '').strip():
                issues.append(f'visual_{i}_missing_beat_link')
            elif beat_ids and str(clip.get('beat_id')).strip() not in beat_ids:
                issues.append(f'visual_{i}_beat_not_in_beat_map')   # the cut would follow a beat that isn't planned
            if not str(clip.get('purpose') or '').strip():
                issues.append(f'visual_{i}_missing_story_purpose')
            sid = str(clip.get('shot_id') or '').strip()
            if not sid:
                issues.append(f'visual_{i}_missing_shot_id')
            elif plan_shots and sid not in plan_shots:
                issues.append(f'visual_{i}_shot_not_in_edit_plan')
            elif plan_shots:
                if str(plan_shots[sid].get('beat_id')) != str(clip.get('beat_id')):
                    issues.append(f'visual_{i}_beat_differs_from_its_shot')
                seen.setdefault(sid, []).append(a)
            cursor = b
        except (KeyError, TypeError, ValueError):
            issues.append(f'bad_visual_segment_{i}')
    if seq:
        for sid, s in plan_shots.items():
            if sid not in seen:
                issues.append(f'shot_{sid}_missing_from_timeline')
            elif abs(min(seen[sid]) - float(s.get('start_s') or 0)) > 0.5:
                issues.append(f'shot_{sid}_starts_off_its_retimed_time')
    if lock and abs(cursor - lock['target_length_s']) > max(4, lock['target_length_s'] * lock.get('tolerance_export_pct', .025)):
        issues.append('timeline_misses_locked_target')
    if plan.get('edit_duration_s') and seq and abs(cursor - plan['edit_duration_s']) > 0.5:
        issues.append('timeline_end_differs_from_edit_plan')   # the project drifted from the retimed shots
    spans = {str(b.get('id')): (float(b.get('start_s') or 0), float(b.get('end_s') or 0)) for b in plan.get('beats') or []}
    music = read_json(artifact_path(rd, n, 'music')).get('tracks') or {}
    music_used = False
    for j, seg in enumerate(track.get('audio_segments') or [], 1):
        kind = str(seg.get('kind') or '')
        if kind == 'narration':
            continue
        bs = [str(x) for x in seg.get('beats') or []]
        if not bs or any(x not in beat_ids for x in bs):
            issues.append(f'audio_{j}_must_name_beats_of_the_beat_map')
        else:
            try:
                a, b = float(seg['start_s']), float(seg['end_s'])
                if spans and not any(x in spans and a < spans[x][1] and b > spans[x][0] for x in bs):
                    issues.append(f'audio_{j}_plays_outside_its_beats')
            except (KeyError, TypeError, ValueError):
                issues.append(f'audio_{j}_needs_start_s_and_end_s')
        if kind == 'music':
            music_used = True
            rec = music.get(str(_run_file(rd, seg.get('file'))))
            if not rec and not reapproved_for(dlock, 'music'):
                issues.append(f'audio_{j}_music_without_provenance')
            elif rec and not media_current(dlock, 'music', rec.get('production_rev')):
                issues.append(f'audio_{j}_music_made_for_an_earlier_direction')
    if music and not music_used:
        warnings.append('music was made for this video but timeline.json lists no music segment: if the bed is in '
                        'the project, record it (audio_segments, kind "music", with its beats)')
    sf = stills_facts(rd, n)
    issues += sf['issues']
    warnings += sf['warnings']
    if track.get('canvas') not in ('1920x1080', '2560x1440', '3840x2160'):
        issues.append('canvas_not_youtube_16_9')
    return {'ready': not issues, 'issues': issues, 'warnings': warnings, 'last_visual_end_s': cursor,
            'target_length_s': lock.get('target_length_s'), 'audio_ready': sound['ready']}


def cmd_timeline_check(args):
    rd, st = run_folder(args)
    res = timeline_facts(rd, args.video)
    emit(res, 0 if res['ready'] else 2)


def cmd_export_check(args):
    rd, st = run_folder(args)
    res = export_facts(rd, args.video, args.file, deep=args.deep)
    res['manual_review_required'] = ['watch opening/first minute', 'sample each major narrative chapter',
                                     'watch last minute', 'listen to all TTS joins',
                                     'check factual assertions/visual chronology', 'review title-thumbnail promise',
                                     'final watch review: av-profile --file, review-packet --kind final, release-check']
    emit(res, 0 if res['ready'] else 2)


def tokens_of(text):
    """Comparable word tokens: lower case, hyphens and apostrophes dropped ('Yudam-ni' matches 'Yudamni')."""
    out = []
    for w in re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", strip_tags(text), flags=re.UNICODE):
        t = re.sub(r"[-']", '', w.lower())
        if t:
            out.append(t)
    return out


def align_lines(line_texts, words):
    """Match script lines to Whisper words (difflib on word tokens). Returns, per line, a list of per-token
    (start, end) times (None where Whisper heard something else), and the share of script tokens matched."""
    s_tok, owner, pos = [], [], []
    tok_time = []
    for li, text in enumerate(line_texts):
        toks = tokens_of(text)
        tok_time.append([None] * len(toks))
        for k, t in enumerate(toks):
            s_tok.append(t)
            owner.append(li)
            pos.append(k)
    h_tok, h_time = [], []
    for w in words:
        for t in tokens_of(w['text']):
            h_tok.append(t)
            h_time.append((w['start_s'], w['end_s']))
    matched = 0
    for a, b, size in difflib.SequenceMatcher(a=s_tok, b=h_tok, autojunk=False).get_matching_blocks():
        for k in range(size):
            tok_time[owner[a + k]][pos[a + k]] = h_time[b + k]
            matched += 1
    return tok_time, (matched / len(s_tok)) if s_tok else 0.0


def cmd_narration_measure(args):
    """Measure the real narration with the references' own yardstick (the same transcribe() and
    wpm_from_transcript_raw): real pace, the natural gap after each line, what every inline tag actually cost,
    how the narration pauses next to the references, and when each script line is spoken. Writes
    50-audio/video-NN/line-times.json and, from 300+ words of the locked voice, voice-lock.json -> measured
    (what plan-check's real_forecast_s and the tts calibration gate read)."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    script = read_json(vd / 'script.json', required=True)
    lock = read_json(vd / 'length-lock.json', required=True)
    lines = script.get('lines') or []
    folder = rd / '50-audio' / f'video-{n:02d}'
    manifest = read_json(folder / 'manifest.json', required=True)
    chunks = manifest.get('chunks') or []
    finished = set(manifest.get('finished_parts') or [])
    use = [c for c in chunks if c['id'] in finished and (folder / c['file']).is_file()]
    if args.parts:
        want = {int(x) for x in args.parts.split(',') if x.strip()}
        use = [c for c in use if c['id'] in want]
    if not use:
        error('No finished narration parts to measure.')
    durations = {c['id']: probe(folder / c['file'])['duration_s'] for c in chunks if (folder / c['file']).is_file()}
    wdir = folder / 'whisper'
    wdir.mkdir(exist_ok=True)
    tags, _ = script_tags(lines)
    rows, all_words, per_part, all_segments = {}, [], [], []
    tot_words = tot_speech = tot_dur = 0.0
    for c in use:
        lo, hi = int(c['line_start']), int(c['line_end'])
        text = '\n'.join(str(r.get('text') or '').strip() for r in lines[lo - 1:hi])
        if hashlib.sha256(text.encode('utf-8')).hexdigest() != c.get('text_sha256'):
            error(f'Part {c["id"]} (lines {lo}-{hi}) was recorded from other text than the script has now. '
                  'Measure only the parts that match (--parts), or re-record this one.')
        part = folder / c['file']
        tpath = wdir / (Path(c['file']).stem + '.json')
        cached = read_json(tpath)
        if not (cached and tpath.stat().st_mtime >= part.stat().st_mtime and cached.get('model') == args.whisper_model):
            transcribe(part, tpath, args.whisper_model, args.device, args.compute_type)
        tj = read_json(tpath)
        wc, speech = transcript_speech(tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace'))
        offset = sum(durations.get(x['id'], 0) for x in chunks if x['id'] < c['id'])
        words = transcript_words(tj)
        tok_time, ratio = align_lines([str(r.get('text') or '') for r in lines[lo - 1:hi]], words)
        for j, tt in enumerate(tok_time):
            got = [x for x in tt if x]
            rows[lo + j] = {'id': lines[lo + j - 1].get('id'), 'index': lo + j,
                            'start_s': round(offset + got[0][0], 3) if got else None,
                            'end_s': round(offset + max(x[1] for x in got), 3) if got else None,
                            'matched_words': len(got), 'words': len(tt),
                            '_tok': [None if x is None else (offset + x[0], offset + x[1]) for x in tt]}
        all_words += [{'start_s': w['start_s'] + offset, 'end_s': w['end_s'] + offset, 'text': w['text']} for w in words]
        all_segments += _segments_of(tj, offset)
        per_part.append({'id': c['id'], 'lines': [lo, hi], 'offset_s': round(offset, 3),
                         'duration_s': durations[c['id']], 'words': wc, 'speech_s': round(speech, 2),
                         'wpm': round(wc / (speech / 60)) if speech else None, 'alignment_match_ratio': round(ratio, 3)})
        tot_words += wc
        tot_speech += speech
        tot_dur += durations[c['id']]
    order = sorted(rows)
    for k, li in enumerate(order):     # a line Whisper missed entirely sits between its neighbours
        r = rows[li]
        if r['start_s'] is None:
            prev_end = next((rows[x]['end_s'] for x in reversed(order[:k]) if rows[x]['end_s'] is not None), None)
            next_start = next((rows[x]['start_s'] for x in order[k + 1:] if rows[x]['start_s'] is not None), None)
            r['start_s'] = prev_end if prev_end is not None else next_start
            r['end_s'] = next_start if next_start is not None else prev_end
            r['interpolated'] = True
    pause_tag_at = set()
    for t in tags:
        if t['category'] == 'pause':
            pause_tag_at.add(t['index'] if t['at_line_end'] else t['index'] - 1 if t['at_line_start'] else -1)
    gaps = [rows[li + 1]['start_s'] - rows[li]['end_s'] for li in order
            if li + 1 in rows and li not in pause_tag_at and rows[li]['end_s'] is not None
            and rows[li + 1]['start_s'] is not None]
    natural_gap = statistics.median(gaps) if gaps else 0.0
    measured_tags = []
    for t in tags:
        li = t['index']
        if li not in rows:
            continue
        tok, k = rows[li]['_tok'], t['words_before']
        before = next((x[1] for x in reversed(tok[:k]) if x), None)
        if before is None and li - 1 in rows:
            before = rows[li - 1]['end_s']
        after = next((x[0] for x in tok[k:] if x), None)
        if after is None and li + 1 in rows:
            after = rows[li + 1]['start_s']
        if before is None or after is None:
            continue
        base = natural_gap if (t['at_line_start'] or t['at_line_end']) else 0.15
        measured_tags.append({'line': t['line'], 'tag': t['tag'], 'gap_s': round(after - before, 2),
                              'excess_s': round(after - before - base, 2)})
    costs = {}
    for m in measured_tags:
        costs.setdefault(m['tag'], []).append(m['excess_s'])
    costs = {k: round(statistics.median(v), 2) for k, v in costs.items()}
    tag_excess = sum(max(0.0, m['excess_s']) for m in measured_tags)
    nlines = len(rows)
    wpm = round(tot_words / (tot_speech / 60)) if tot_speech else None
    # Whisper's long pass drops a phrase now and then (measured here: ~1% of words, heard in the audio when a
    # short window is re-transcribed), so its word count runs a little low. wpm stays the references' yardstick
    # (they are measured the same way); the length forecast uses the script's own words over the same speech
    # time, which reproduces the measured take exactly.
    script_words = sum(count_words(lines[li - 1].get('text') or '') for li in rows)
    forecast_wpm = round(script_words / (tot_speech / 60), 1) if tot_speech else None
    per_line = round((tot_dur - tot_speech - tag_excess) / nlines, 3) if nlines else None
    complete = sorted(rows) == list(range(1, len(lines) + 1))
    ratio_all = (sum(p['alignment_match_ratio'] * (p['lines'][1] - p['lines'][0] + 1) for p in per_part) / nlines) if nlines else 0
    profile = pause_profile(all_words)
    # How the voice moves, beat by beat, next to what each beat asked for and to the references measured the same
    # way (av_tools): the writing of the parts not yet recorded is where a flat stretch gets fixed.
    delivery, delivery_error = None, None
    if not args.no_delivery:
        try:
            av = _av()
            import tempfile
            top = max(c['id'] for c in use)
            files = [folder / c['file'] for c in sorted(chunks, key=lambda x: x['id'])
                     if c['id'] <= top and (folder / c['file']).is_file()]
            beats = read_json(vd / 'beat-map.json').get('beats') or []
            spans = {}
            for b in beats:
                try:
                    b0, b1 = int(b['line_start']), int(b['line_end'])
                except (KeyError, TypeError, ValueError):
                    continue
                if b0 in rows and b1 in rows and rows[b0]['start_s'] is not None and rows[b1]['end_s'] is not None:
                    spans[str(b.get('id'))] = (rows[b0]['start_s'], rows[b1]['end_s'])
            with tempfile.TemporaryDirectory() as tmp:
                wav = av.concat_audio(files, Path(tmp) / 'narration.wav')
                delivery = av.delivery(f'video-{n:02d} narration', wav, all_words, spans=spans, segments=all_segments)
            for b in beats:
                k = str(b.get('id'))
                if k in (delivery.get('spans') or {}):
                    delivery['spans'][k]['intended'] = {x: b.get(x) for x in ('experience', 'narration_direction', 'pace')}
            delivery['references'] = {v: (read_json(ref_av_path(rd, v)).get('summary') or {}).get('narration')
                                      for v in lock.get('reference_ids') or [] if ref_av_path(rd, v).is_file()}
            delivery['parts'] = [p['id'] for p in per_part]
            delivery['measured_at'] = now()
            write_json(folder / 'delivery.json', delivery)
        except (RuntimeError, ValueError, OSError, ImportError, KeyError) as exc:
            delivery_error = f'{type(exc).__name__}: {str(exc)[:200]}'
    for r in rows.values():
        r.pop('_tok', None)
    out = {'video': n, 'complete': complete, 'script_sha256': script_hash(lines) if complete else None,
           'narration_file': str(folder / 'narration.wav') if complete else None, 'parts': per_part,
           'duration_s': round(tot_dur, 2), 'words': int(tot_words), 'speech_s': round(tot_speech, 2), 'wpm': wpm,
           'script_words': script_words, 'forecast_wpm': forecast_wpm,
           'natural_line_gap_median_s': round(natural_gap, 3), 'per_line_overhead_s': per_line,
           'alignment_match_ratio': round(ratio_all, 3), 'tags_measured': measured_tags,
           'pause_profile': profile, 'lines': [rows[li] for li in order], 'measured_at': now(),
           'method': 'transcribe() + wpm_from_transcript_raw on each part, exactly as on the references'}
    write_json(folder / 'line-times.json', out)
    vl_path = rd / '60-voice' / 'voice-lock.json'
    vl = read_json(vl_path)
    settings = manifest.get('voice_settings') or {}
    wrote = False
    note = None
    if tot_words < 300:
        note = 'Under 300 words measured: too short to calibrate (short samples read fast and scatter).'
    elif vl.get('voice_id') != manifest.get('voice_id') or (vl.get('settings') or {}) != settings:
        note = 'The narration was recorded with another voice or settings than voice-lock.json: not written there.'
    else:
        prev = vl.get('measured') or {}
        same = (prev.get('voice_id') == manifest['voice_id'] and prev.get('model_id') == manifest['model_id']
                and (prev.get('settings') or {}) == settings)
        tag_costs = dict(prev.get('tag_costs_s') or {}) if same else {}
        tag_costs.update(costs)
        vl['measured'] = {'voice_id': manifest['voice_id'], 'model_id': manifest['model_id'], 'settings': settings,
                          'wpm': wpm, 'words': int(tot_words), 'script_words': script_words,
                          'forecast_wpm': forecast_wpm, 'speech_s': round(tot_speech, 2),
                          'duration_s': round(tot_dur, 2), 'lines': nlines, 'per_line_overhead_s': per_line,
                          'tag_costs_s': tag_costs, 'parts': [p['id'] for p in per_part], 'measured_at': now(),
                          'method': out['method']}
        for k in ('measured_wpm', 'measured_overhead_s', 'measured_overhead_lines', 'measured_wpm_source'):
            vl.pop(k, None)
        write_json(vl_path, vl)
        wrote = True
    warnings = []
    if ratio_all < 0.9:
        warnings.append('Under 90% of the script words were matched: listen for missing or extra words, or a script edit.')
    for m in measured_tags:
        if m['tag'] in ('[pause]', '[long pause]', '[short pause]', '[slightly pause]') and m['excess_s'] < 0.2:
            warnings.append(f"{m['line']} {m['tag']} made no measurable pause: listen (was it read aloud?)")
    emit({'ok': True, 'line_times': str(folder / 'line-times.json'), 'complete': complete, 'wpm': wpm,
          'forecast_wpm': forecast_wpm, 'words': int(tot_words), 'script_words': script_words,
          'duration_s': round(tot_dur, 2), 'per_line_overhead_s': per_line,
          'natural_line_gap_median_s': round(natural_gap, 3), 'tags_measured': measured_tags,
          'pause_profile': profile,
          'references': {v: {'wpm': (lock.get('per_ref_wpm') or {}).get(v), **p}
                         for v, p in ref_pause_profiles(rd, lock.get('reference_ids') or []).items()},
          'alignment_match_ratio': round(ratio_all, 3), 'voice_lock_updated': wrote, 'note': note,
          'warnings': warnings,
          'delivery': ({'file': str(folder / 'delivery.json'), 'summary': delivery.get('summary'),
                        'references': delivery.get('references'),
                        'reading': 'Pitch range and movement, loudness contrast and rate across the narration, per '
                                   'beat in the file: a beat asked to lift that measures flat is rewritten in the '
                                   'parts not yet recorded (10-creative-direction.md), never fixed in the audio.'}
                       if delivery else {'error': delivery_error} if delivery_error else None),
          'next': 'plan-check (real_forecast_s against the export window); when complete: retime-shots.'})


def cmd_pace_profile(args):
    """Pace and pauses of the references (and, when measured, this video's narration) with one yardstick."""
    rd, st = run_folder(args)
    refs = normalize_refs(args.refs)
    lock = read_json(video_dir(rd, args.video) / 'length-lock.json') if args.video else {}
    if not refs:
        refs = lock.get('reference_ids') or []
    if not refs:
        error('Give --refs V001,V002, or --video NN to use that video\'s locked references.')
    out = {}
    for vid in refs:
        tfile = rd / '10-media' / vid / 'transcript.txt'
        wpm = wpm_from_transcript_raw(tfile.read_text(encoding='utf-8', errors='replace')) if tfile.exists() else None
        out[vid] = {'wpm': wpm, **(ref_pause_profiles(rd, [vid]).get(vid) or {})}
    narr = None
    if args.video:
        lt = read_json(rd / '50-audio' / f'video-{int(args.video):02d}' / 'line-times.json')
        if lt:
            narr = {'wpm': lt.get('wpm'), 'complete': lt.get('complete'), **(lt.get('pause_profile') or {})}
    emit({'ok': True, 'references': out, 'narration': narr,
          'note': 'WPM = words over pure speech time; pauses = silence between consecutive words (Whisper word '
                  'timestamps). Same functions for references and narration.'})


def cmd_retime_shots(args):
    """Time every shot to the real narration: each cut falls in the silence between the last line of one shot
    and the first line of the next; an edit hold (pause_via "edit") is inserted at its line and belongs to the
    shot before it. Rewrites shot-plan.json's start_s/end_s (the planned values kept once as planned_*), writes
    70-edit/video-NN/edit-plan.json, and with --render-narration the narration with its holds
    (50-audio/video-NN/narration-edit.wav) -- the audio file the CapCut project uses."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    lock = read_json(vd / 'length-lock.json', required=True)
    script = read_json(vd / 'script.json', required=True)
    lines = script.get('lines') or []
    folder = rd / '50-audio' / f'video-{n:02d}'
    lt = read_json(folder / 'line-times.json', required=True)
    if not lt.get('complete') or lt.get('script_sha256') != script_hash(lines):
        error('line-times.json does not describe the whole current script: run narration-measure on the finished narration.')
    gate = audio_facts(rd, n)
    blocking = [x for x in gate['issues'] if not x.startswith('narration_plus_edit_holds')
                and x != 'narration_duration_outside_locked_tolerance']
    if blocking:
        error('The narration is not complete and matching the script yet.', blocking)
    shots_gate = shot_facts(rd, n)
    if shots_gate['issues']:
        error('The shot plan is not a complete visual argument yet (shot-check): every shot needs its beat and what '
              'NEW thing its picture gives the viewer, and every beat a picture.', shots_gate['issues'])
    dgate, dlock, _ = direction_gate(rd, n)
    dgate += list(stale_files(rd, n, ('beat-map',)).values())
    if dgate:
        error('The edit is timed and directed from the locked creative direction and its current beat map.', dgate)
    beat_dir = {str(b.get('id')): {k: b.get(k) for k in ('experience', 'visual_intent', 'sound_direction', 'pace')}
                for b in read_json(vd / 'beat-map.json').get('beats') or []}
    plan_path = rd / '60-visuals' / f'video-{n:02d}' / 'shot-plan.json'
    plan = read_json(plan_path, required=True)
    shots = plan.get('shots') or []
    index = {str(r.get('id')): i + 1 for i, r in enumerate(lines)}
    times = {r['index']: r for r in lt['lines']}
    dur = gate['duration_s']
    holds = []
    for p in script_pause_plan(lines)[0]:
        if p['via'] == 'edit':
            i = p['index']
            at = (times[i]['end_s'] + times[i + 1]['start_s']) / 2 if i < len(lines) else dur
            holds.append({'after_line': p['line'], 'at_audio_s': round(at, 3), 'hold_s': p['pause_after_s']})
    holds.sort(key=lambda h: h['at_audio_s'])
    total = round(dur + sum(h['hold_s'] for h in holds), 3)
    ranges, cursor = [], 0
    for s in shots:
        a, b = index.get(str(s.get('line_start'))), index.get(str(s.get('line_end')))
        if a is None or b is None or a != cursor + 1 or b < a:
            error(f'Shot {s.get("id")} does not start on the line after the previous shot ends.',
                  {'line_start': s.get('line_start'), 'line_end': s.get('line_end'), 'previous_end': cursor})
        ranges.append((a, b))
        cursor = b
    if cursor != len(lines):
        error('The shots do not cover every script line.', {'last_line_covered': cursor, 'lines': len(lines)})
    out_shots, start, notes = [], 0.0, []
    for k, (s, (a, b)) in enumerate(zip(shots, ranges)):
        if k + 1 < len(shots):
            split = (times[b]['end_s'] + times[b + 1]['start_s']) / 2
            end = split + sum(h['hold_s'] for h in holds if h['at_audio_s'] <= split + 1e-6)
        else:
            end = total
        s.setdefault('planned_start_s', s.get('start_s'))
        s.setdefault('planned_end_s', s.get('end_s'))
        s['start_s'], s['end_s'] = round(start, 2), round(end, 2)
        length = end - start
        if length < 2.0 or length > 45.0:
            notes.append(f"{s.get('id')} now lasts {length:.1f}s (planned "
                         f"{(s['planned_end_s'] or 0) - (s['planned_start_s'] or 0):.1f}s): check it still works")
        # Each shot carries its beat's direction: what the editor's move, transition and sound serve here (09, 05).
        out_shots.append({'id': s.get('id'), 'beat_id': s.get('beat_id'), 'start_s': s['start_s'],
                          'end_s': s['end_s'], 'duration_s': round(length, 2),
                          'direction': beat_dir.get(str(s.get('beat_id'))) or {}})
        start = end
    beat_spans = {}
    for s in out_shots:
        b = str(s['beat_id'])
        lo, hi = beat_spans.get(b, (s['start_s'], s['end_s']))
        beat_spans[b] = (min(lo, s['start_s']), max(hi, s['end_s']))
    plan['timed_to'] = {'narration': str(folder / 'narration.wav'), 'edit_duration_s': total, 'retimed_at': now()}
    write_json(plan_path, plan)
    tol = max(4, lock['target_length_s'] * lock.get('tolerance_export_pct', .025))
    edit_audio = None
    if args.render_narration:
        src, outp = folder / 'narration.wav', folder / 'narration-edit.wav'
        filt, labels, prev = [], [], 0.0
        for j, h in enumerate(holds):
            filt.append(f"[0:a]atrim=start={prev:.3f}:end={h['at_audio_s']:.3f},asetpts=PTS-STARTPTS[a{j}]")
            filt.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={h['hold_s']:.3f}[s{j}]")
            labels += [f'[a{j}]', f'[s{j}]']
            prev = h['at_audio_s']
        if prev < dur - 0.01:
            filt.append(f'[0:a]atrim=start={prev:.3f},asetpts=PTS-STARTPTS[tail]')
            labels.append('[tail]')
        filt.append(''.join(labels) + f'concat=n={len(labels)}:v=0:a=1[out]')
        run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src),
                 '-filter_complex', ';'.join(filt), '-map', '[out]', '-ar', '44100', '-ac', '2',
                 '-c:a', 'pcm_s16le', str(outp)])
        edit_audio = {'file': str(outp), 'duration_s': probe(outp)['duration_s']}
    edit_plan = {'video': n, 'narration_file': str(folder / 'narration.wav'), 'narration_duration_s': dur,
                 'holds': holds, 'edit_duration_s': total, 'edit_narration': edit_audio,
                 'export_window_s': [round(lock['target_length_s'] - tol, 2), round(lock['target_length_s'] + tol, 2)],
                 'within_export_window': abs(total - lock['target_length_s']) <= tol,
                 'direction': {'treatment': dlock.get('treatment'), 'production_rev': dlock.get('production_rev', 1)},
                 'shot_structure_sha256': shot_structure_sha(shots), 'script_sha256': script_hash(lines),
                 'beats': [{'id': b, 'start_s': round(a, 2), 'end_s': round(z, 2), **beat_dir.get(b, {})}
                           for b, (a, z) in beat_spans.items()],
                 'shots': out_shots, 'notes': notes, 'made_at': now()}
    write_json(rd / '70-edit' / f'video-{n:02d}' / 'edit-plan.json', edit_plan)
    emit({'ok': True, 'edit_plan': str(rd / '70-edit' / f'video-{n:02d}' / 'edit-plan.json'),
          'shot_plan': str(plan_path), 'shots': len(out_shots), 'edit_duration_s': total, 'holds': holds,
          'within_export_window': edit_plan['within_export_window'], 'edit_narration': edit_audio, 'notes': notes})


def _av():
    """The audiovisual measurements (av_tools.py, next to this file): loaded only when a command needs them, so the
    rest of the pipeline never waits on numpy/OpenCV/librosa."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import av_tools
    return av_tools


def _segments_of(tjson, offset=0.0):
    return [(float(s['start_s']) + offset, float(s['end_s']) + offset) for s in tjson.get('segments') or []
            if s.get('start_s') is not None and s.get('end_s') is not None]


def measure_file_delivery(audio_path, transcript_path):
    """How the voice in one short file moves (a voice preview, a probe): pitch range and word-to-word movement,
    loudness contrast and register, on the references' yardstick. A short sample is indicative only. Never raises:
    a measurement that can't be made comes back as {'error': ...}."""
    try:
        av = _av()
        import tempfile
        tj = read_json(transcript_path)
        with tempfile.TemporaryDirectory() as tmp:
            wav = av.extract_audio(audio_path, Path(tmp) / 'sample.wav')
            dv = av.delivery(Path(audio_path).stem, wav, transcript_words(tj), spans={'whole': (0.0, 1e9)},
                             segments=_segments_of(tj))
        whole = (dv.get('spans') or {}).get('whole') or {}
        out = {k: whole.get(k) for k in ('pitch_range_st', 'pitch_movement_st', 'loudness_contrast_db',
                                         'speech_rate_wpm')}
        out['register_hz'] = (dv.get('summary') or {}).get('register_hz')
        return out
    except (RuntimeError, ValueError, OSError, ImportError, KeyError, TypeError) as exc:
        return {'error': f'{type(exc).__name__}: {str(exc)[:120]}'}


def export_av_path(rd, video, fingerprint):
    return rd / '70-edit' / f'video-{int(video):02d}' / 'av' / f"export-{fingerprint.split(':')[0][:10]}.json"


def cmd_av_profile(args):
    """Measured evidence of how a video works over time (av_tools.py): the references (--refs), or this video's
    export (--video NN --file). Writes the measurements and one watch sheet per minute (frames every 5 s with the
    words spoken under them) for the agents to read like an editor scrubbing a timeline."""
    rd, st = run_folder(args)
    av = _av()
    import tempfile
    results = {}
    if args.refs:
        vids = cards_inventory(rd)
        for vid in normalize_refs(args.refs):
            row = vids.get(vid)
            if not row:
                error('Unknown reference ID (or a duplicate).', vid)
            media = rd / '10-media' / vid
            fi = read_json(media / 'frame-index.json')
            frames = [(f['approx_s'], media / 'sampled-frames' / f['file']) for f in fi.get('frames') or []]
            if not frames:
                error('No sampled frames for this reference: run prepare first.', vid)
            tj = read_json(media / 'transcript.json')
            words = transcript_words(tj)
            target = ref_av_path(rd, vid)
            sig = {'fingerprint': row.get('fingerprint'), 'frames': len(frames), 'words': len(words),
                   'method': av.METHOD_VERSION, 'sheets': not args.no_sheets}
            old = read_json(target)
            if old.get('signature') == sig and not args.force:
                results[vid] = {'file': str(target), 'cached': True, 'summary': old.get('summary')}
                continue
            with tempfile.TemporaryDirectory() as tmp:
                wav = None
                if row.get('has_audio') and words:
                    try:
                        wav = av.extract_audio(row['source_path'], Path(tmp) / 'audio.wav')
                    except RuntimeError as exc:
                        results.setdefault('_notes', []).append(f'{vid}: audio not measured ({str(exc)[:120]})')
                prof = av.profile(vid, row.get('duration_s') or frames[-1][0], frames, wav, words,
                                  sheets_dir=None if args.no_sheets else target.with_suffix(''),
                                  segments=_segments_of(tj))
            tfile = media / 'transcript.txt'
            if prof['summary'].get('narration') is not None:
                prof['summary']['narration']['wpm_pipeline'] = (wpm_from_transcript_raw(
                    tfile.read_text(encoding='utf-8', errors='replace')) if tfile.exists() else None)
                prof['summary']['narration']['pause_profile'] = pause_profile(words)
            prof.update({'signature': sig, 'source': {'id': vid, 'fingerprint': row.get('fingerprint')},
                         'made_at': now()})
            write_json(target, prof)
            results[vid] = {'file': str(target), 'sheets': len(prof['sheets']), 'summary': prof['summary']}
    elif args.video and args.file:
        n = int(args.video)
        f = Path(args.file).expanduser().resolve()
        if not f.is_file():
            error('Export file not found', str(f))
        fp = quick_fingerprint(f)
        target = export_av_path(rd, n, fp)
        target.parent.mkdir(parents=True, exist_ok=True)
        meta = probe(f)
        if args.transcript:
            tj = read_json(args.transcript, required=True)
        else:
            tpath = target.with_name(target.stem + '-whisper.json')
            if not (read_json(tpath).get('status') == 'transcribed'):
                transcribe(f, tpath, args.whisper_model, args.device, args.compute_type)
            tj = read_json(tpath)
        words = transcript_words(tj)
        with tempfile.TemporaryDirectory(dir=str(target.parent)) as tmp:
            frames = av.extract_frames(f, Path(tmp) / 'frames', fps=st.get('analysis_fps', 5))
            wav = None
            if meta.get('has_audio'):
                try:
                    wav = av.extract_audio(f, Path(tmp) / 'audio.wav')
                except RuntimeError:
                    wav = None
            prof = av.profile(f'video-{n:02d}', meta['duration_s'], frames, wav, words,
                              sheets_dir=None if args.no_sheets else target.with_suffix(''),
                              segments=_segments_of(tj))
        for s in prof['shots']:
            s.pop('keyframe', None)            # the export's frames were temporary; the sheets keep the pictures
        lock = read_json(video_dir(rd, n) / 'length-lock.json')
        prof['references'] = {v: read_json(ref_av_path(rd, v)).get('summary') for v in lock.get('reference_ids') or []
                              if ref_av_path(rd, v).is_file()}
        prof.update({'source': {'file': str(f), 'fingerprint': fp}, 'made_at': now()})
        write_json(target, prof)
        results[f'video-{n:02d}'] = {'file': str(target), 'sheets': len(prof['sheets']), 'summary': prof['summary'],
                                     'references': prof['references']}
    else:
        error('Give --refs V001,V002 (references), or --video NN --file export.mp4 (this video\'s export).')
    emit({'ok': True, 'profiles': results,
          'reading': 'Measurements, not verdicts: what the voice, the picture and the cut do over time. Open the '
                     'sheets in order to watch the video as a storyboard with its words; compare numbers only with '
                     'videos measured the same way (10-creative-direction.md).'})


def cmd_direction_lock(args):
    """Lock the creative direction (direction.json) before the script is written: it must be complete, and its
    treatments must have had their blind comparison read with every finding answered. A video whose script came
    first can be locked only with --late "reason" (recorded and shown at every plan-check). A later change needs
    --revise "what changed and why" (kept in the lock's history).

    Every lock knows which parts changed. A change to the chosen treatment, the strategy or the chosen approach is
    meaningful: the production revision goes up and the artifacts it affects (SECTION_EFFECTS) must be updated or
    explicitly reapproved before the stages that use them continue. Anything that already existed before the first
    lock was made without a direction and is affected the same way. A change to the evidence, the alternatives or the
    reasons is harmless: same revision, nothing to redo. Refining the chosen treatment needs no new blind read; only a
    treatment that was never in one does."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    df = direction_facts(rd, n)
    if df['issues']:
        error('The creative direction is not complete yet.', df['issues'])
    lockp = vd / 'direction-lock.json'
    prev = read_json(lockp)
    if not prev:
        tr = review_state(vd, 'treatment', df['treatments_sha256'])
        if tr['issues']:
            error('The treatments need their blind comparison read (review-packet --kind treatment), recorded, and '
                  'every finding answered before the direction is locked.', tr['issues'])
    else:
        recs = review_records(vd, 'treatment')
        compared = set(((recs[-1][0].get('labels') or {}).values()) if recs else [])
        if str(df['chosen_treatment']) not in compared:
            error('The chosen treatment was never in a blind comparison read: run review-packet --kind treatment for '
                  'the current treatments first.', {'chosen': df['chosen_treatment'], 'compared': sorted(compared)})
    d = read_json(vd / 'direction.json')
    sections = direction_sections(d)
    script_exists = (vd / 'script.json').is_file()
    entry = {'locked_at': now(), 'direction_sha256': df['direction_sha256'],
             'treatments_sha256': df['treatments_sha256'], 'treatment': df['chosen_treatment'],
             'script_existed': script_exists, 'sections': sections}
    if not prev:
        if script_exists and not args.late:
            error('A script already exists: the creative direction is decided and locked BEFORE scriptwriting. For a '
                  'video whose script really came first, --late "reason" records that exception (shown at every '
                  'plan-check and in the release sheet).')
        # Whatever already exists was made without a direction: it is affected by this first one.
        required = {a: {'rev': 1, 'baseline': artifact_sha(rd, n, a)} for a in TRACKED_FILES if artifact_sha(rd, n, a)}
        required.update({m: {'rev': 1} for m in MEDIA_ARTIFACTS if media_present(rd, n, m)})
        hit = list(required)
        lock = {**entry, 'late_reason': args.late or None, 'history': [], 'production_rev': 1, 'required': required,
                'reapproved': {}, 'changed_sections': [], 'affects': hit}
    else:
        if prev.get('direction_sha256') == df['direction_sha256']:
            emit({'ok': True, 'unchanged': True, 'lock': str(lockp), 'treatment': prev.get('treatment'),
                  'production_rev': prev.get('production_rev')})
            return
        if not args.revise:
            error('The direction changed since it was locked. Re-lock with --revise "what changed and why".')
        old = prev.get('sections') or {}
        changed = [k for k, h in sections.items() if old.get(k) != h]
        hit = [a for a in ALL_ARTIFACTS if any(a in SECTION_EFFECTS.get(k, ()) for k in changed)]
        rev = prev.get('production_rev', 1)
        history = (prev.get('history') or []) + [{k: prev.get(k) for k in ('locked_at', 'direction_sha256', 'treatment',
                                                                          'production_rev')}
                                                 | {'revised_because': args.revise, 'changed_sections': changed}]
        lock = {**prev, **entry, 'history': history, 'changed_sections': changed, 'affects': hit}
        if hit:   # meaningful: a new revision, and each artifact it touches must follow it
            required = dict(prev.get('required') or {})
            for a in hit:
                required[a] = {'rev': rev + 1, **({'baseline': artifact_sha(rd, n, a)} if a in TRACKED_FILES else {})}
            lock.update({'production_rev': rev + 1, 'required': required,
                         'reapproved': {k: v for k, v in (prev.get('reapproved') or {}).items() if k not in hit}})
    write_json(lockp, lock)
    outdated = sorted(stale_files(rd, n))
    emit({'ok': True, 'lock': str(lockp), 'treatment': lock['treatment'], 'late': bool(lock.get('late_reason')),
          'production_rev': lock['production_rev'], 'changed_sections': lock.get('changed_sections'),
          'affects': hit, 'outdated_now': outdated,
          'next': ('Update or explicitly reapprove (direction-reapprove --artifact NAME --reason "...") each outdated '
                   'artifact before the stage that uses it continues.' if outdated else
                   'Beat directions and the script are written from this treatment (03, 10).')})


def cmd_direction_reapprove(args):
    """Explicit reapproval after a meaningful direction change: the director has looked and this artifact, as it is,
    still serves the locked treatment. Recorded with its reason, for this revision only, and shown at every check and
    in the release sheet. A file artifact is approved in its current content (changing it later is an update);
    stills, music or the edit plan are approved as a set for this revision (also how pictures made outside the gated
    workers, e.g. supplied by the user, are accepted)."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    lockp = vd / 'direction-lock.json'
    lock = read_json(lockp)
    if not lock:
        error('No direction lock yet: there is nothing to reapprove against.')
    if n_words(args.reason) < MIN_NOTE_WORDS:
        error('Say why this artifact still serves the locked treatment (a real reason, a few words at least).')
    rev = required_rev(lock, args.artifact) or lock.get('production_rev', 1)
    entry = {'rev': rev, 'at': now(), 'reason': args.reason}
    if args.artifact in TRACKED_FILES:
        if args.artifact not in stale_files(rd, n, (args.artifact,)):
            emit({'ok': True, 'unchanged': True, 'note': f'{args.artifact} is not outdated: nothing to reapprove.'})
            return
        entry['sha256'] = artifact_sha(rd, n, args.artifact)
    lock.setdefault('reapproved', {})[args.artifact] = entry
    write_json(lockp, lock)
    emit({'ok': True, 'artifact': args.artifact, 'for_revision': rev, 'still_outdated': sorted(stale_files(rd, n))})


def cmd_media_check(args):
    """The same check the generation workers run before they make anything (media_gate), on a job file by hand."""
    job = read_json(args.job, required=True)
    res = media_gate(job, args.kind)
    emit({k: v for k, v in res.items() if k != 'records'} | {'items': len(res['records'])}, 0 if res['ok'] else 2)


HOUSE_RULES = ('House rules the video must keep (never suggest breaking them; flag any line or picture that comes '
               'close): no holiday, religious or superstitious scene used as a story device; nothing gory (no blood, '
               'wounds, bodies or injuries shown or described); no extreme distress; no swearing; nothing indecent; '
               'every person an adult.')

SCRIPT_BRIEF = """# Cold read: {TITLE}

You are a first-time viewer, not an editor. Below is the complete narration of a long-form YouTube video
(about {MINUTES} minutes, narrated over illustrated stills). You get only the title and the words, on purpose:
no plan, no rationale. Read nothing else and do not change any file except the one you are asked to write.

Read it all the way through as someone who clicked the title and is listening. Be honest, specific and fair:
say what works as plainly as what does not. Refer to line ids.

Think about:
1. What the video promised, and whether it delivered.
2. Your gut, 1-10: would you keep watching? (a viewer's gut, not a quality score)
3. Where your attention dropped, and why: facts with no consequence for anyone, the same point made again, a list
   read aloud, a sentence pattern repeating, textbook register, explaining what you had already felt, exposition
   before you cared. Roughly how long each stretch felt.
4. What feels formulaic: devices used so often they stop working (count them).
5. The strongest passages, and why they work.
6. Whether the narrator sounds like a person you would enjoy listening to: personality, warmth, wit or emotion
   where the material invites it; or a reader of facts; or someone straining for drama.
7. Lines hard to follow by ear: number pile-ups, very long sentences, tangled grammar, jargon.
8. The ending: does it land; is anything after the payoff too long or too short.

Then list findings (at most 12), each concrete enough to act on. Severity "major": a viewer would likely stop
watching, lose the thread or stop trusting the video there (a long sag, a confusing stretch, a contradiction, a
broken or unearned ending, a line breaking the house rules). "minor": polish.

{HOUSE_RULES}
Do not invent facts. If a fix needs a new fact, write "needs a sourced detail".

Write your answer as JSON, and nothing else, to: {OUT}
{{
  "reviewer": "fresh cold reader",
  "verdict": {{"promise": "...", "delivered": "...", "keep_watching_1_10": 7, "why": "..."}},
  "strongest": [{{"lines": "L052-L058", "why": "..."}}],
  "findings": [{{"id": "F1", "severity": "major", "lines": ["L112-L135"], "problem": "...",
                 "viewer_impact": "...", "suggestion": "..."}}]
}}

## The narration
"""

TREATMENT_BRIEF = """# Treatment comparison (blind)

Below are {K} different ways to make the same long-form YouTube video: how it sounds (the narrator and the
writing) and how it looks (pictures, motion, sound), each shown through three short sample moments. The labels are
random. You get nothing else, on purpose: read nothing else and change no file except the one you are asked to write.

The video: {PREMISE}
About {MINUTES} minutes, narrated over illustrated stills.

Judge them as a viewer choosing what to watch for {MINUTES} minutes, not by the best first 30 seconds:
1. Which would you most want to watch to the end, and why?
2. For each: where it would wear thin over a long video; what feels fresh; what feels like a template, or like
   any other video in this genre; whether the voice and the pictures feel like one idea.
3. Which narrator would you enjoy for {MINUTES} minutes, and which would tire you (too flat, too theatrical,
   too cute, too much like a lecture)?
4. Anything in a sample that breaks the house rules.

Findings (at most 8): each names the treatment label, severity "major" (this treatment would not hold a long watch,
or has a serious flaw) or "minor", the problem, why it matters to a viewer, and a suggestion.

{HOUSE_RULES}

Write your answer as JSON, and nothing else, to: {OUT}
{{
  "reviewer": "fresh reader",
  "would_watch": "B",
  "why": "...",
  "per_treatment": {{"A": "...", "B": "..."}},
  "findings": [{{"id": "F1", "severity": "minor", "treatment": "A", "problem": "...",
                 "viewer_impact": "...", "suggestion": "..."}}]
}}
"""

FINAL_BRIEF = """# Final watch review: {TITLE}

You review the finished video as a viewer would experience it. You cannot play it; you have its watch sheets: one
image per minute, a frame every 5 seconds with the words spoken under it. Open every sheet in order and read them
like a film. Below them are a few measurements per minute (facts, not verdicts). Read nothing else and change no file
except the one you are asked to write.

Judge it against what each part was meant to feel like (listed below), not against a generic checklist:
1. Did each part deliver what it set out to do?
2. Where does it get visually repetitive, or the pictures stop adding anything to the words (a slideshow)?
3. Where do picture and words not connect, or contradict each other?
4. Where does it feel like a lecture or a dry documentary instead of a story? Where does it drag or rush?
5. Continuity breaks: a person, place, object, light or time of day that jumps without reason.
6. The first minute and the ending.
7. Anything on screen or in the words that breaks the house rules.

Findings (at most 12), each with "at" as "mm:ss-mm:ss", severity "major" (a viewer would likely leave, get lost
or stop trusting it there) or "minor", the problem, why it matters to a viewer, and a suggestion.

{HOUSE_RULES}

Write your answer as JSON, and nothing else, to: {OUT}
{{
  "reviewer": "fresh final reviewer",
  "verdict": {{"delivered": "...", "keep_watching_1_10": 7, "why": "..."}},
  "findings": [{{"id": "F1", "severity": "major", "at": "03:10-04:05", "problem": "...",
                 "viewer_impact": "...", "suggestion": "..."}}]
}}
"""


def _fill(template, **kw):
    out = template
    for k, v in kw.items():
        out = out.replace('{' + k + '}', str(v))
    return out.replace('{{', '{').replace('}}', '}')


def _mmss(t):
    t = max(0, int(round(float(t or 0))))
    return f'{t // 60:02d}:{t % 60:02d}'


def cmd_review_packet(args):
    """The bare material for ONE fresh reviewer (an agent spawned with nothing but this file): the script for a
    cold read, the treatments' samples for a blind comparison, or the export's watch sheets for the final review.
    Refuses while the previous round still has unanswered findings."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    kind = args.kind
    recs = review_records(vd, kind)
    if recs:
        last, ans = recs[-1]
        open_ids = [str(f.get('id')) for f in last.get('findings') or [] if answer_problem(kind, f, ans.get(str(f.get('id'))))]
        if open_ids:
            error('Answer every finding of the previous round first (revised with its lines, kept or disputed with a '
                  'reason), then ask for a fresh read.', {'round': last['_round'], 'open': open_ids})
    rnd = recs[-1][0]['_round'] + 1 if recs else 1
    lock = read_json(vd / 'length-lock.json', required=True)
    minutes = round(lock['target_length_s'] / 60)
    blue = read_json(vd / 'blueprint.json')
    title = blue.get('title') or (blue.get('title_options') or ['(untitled)'])[0]
    if isinstance(title, dict):
        title = title.get('title') or json.dumps(title, ensure_ascii=False)
    folder = vd / 'reviews'          # created only when a packet is actually written: a refusal leaves no trace
    out_path = folder / f'{kind}-r{rnd}-findings.json'
    meta = {'kind': kind, 'round': rnd, 'video': n, 'created_at': now(), 'findings_file': str(out_path)}
    if kind == 'script':
        if not read_json(vd / 'direction-lock.json'):
            error('Lock the creative direction first (direction-lock): the script is written from it, and read after it.')
        script = read_json(vd / 'script.json', required=True)
        lines = script.get('lines') or []
        snapshot = {str(r.get('id') or f'L{i + 1:03d}'): str(r.get('text') or '') for i, r in enumerate(lines)}
        text = _fill(SCRIPT_BRIEF, TITLE=title, MINUTES=minutes, HOUSE_RULES=HOUSE_RULES, OUT=out_path)
        text += '\n'.join(f'{lid} {strip_tags(t)}' for lid, t in snapshot.items()) + '\n'
        meta.update({'subject_sha256': script_hash(lines), 'subject_snapshot': snapshot})
    elif kind == 'treatment':
        df = direction_facts(rd, n)
        blocking = [x for x in df['issues'] if x.startswith(('treatment_', 'direction_needs_2', 'direction_missing'))]
        if blocking:
            error('The treatments are not complete enough to compare.', blocking)
        d = read_json(vd / 'direction.json')
        trs = {str(t['id']): t for t in d.get('treatments') or []}
        subject = df['treatments_sha256']
        order = sorted(trs, key=lambda x: hashlib.sha256((subject + x).encode('utf-8')).hexdigest())
        labels = {chr(65 + i): tid for i, tid in enumerate(order)}
        apps = {str(a.get('id')): a for a in d.get('approaches') or [] if isinstance(a, dict)}
        chosen = apps.get(str((d.get('chosen_approach') or {}).get('id'))) or {}
        premise = ' '.join(x for x in (str(blue.get('audience_promise') or ''), str(chosen.get('pitch') or '')) if x)
        text = _fill(TREATMENT_BRIEF, K=len(trs), PREMISE=premise or '(see the samples)', MINUTES=minutes,
                     HOUSE_RULES=HOUSE_RULES, OUT=out_path)
        for lab, tid in labels.items():
            t = trs[tid]
            text += f'\n## Treatment {lab}\n'
            for k in TREATMENT_SHOWN_TO_REVIEWER:
                text += f'- {k.replace("_", " ")}: {t.get(k)}\n'
            for m in SAMPLE_MOMENTS:
                s = (t.get('samples') or {}).get(m) or {}
                text += (f'\n### {m.replace("_", " ")}\nWhat you see: {s.get("picture")}\n'
                         f'What you hear: {strip_tags(s.get("narration") or "")}\n')
        meta.update({'subject_sha256': subject, 'labels': labels})
    else:
        if not args.file:
            error('The final review reads a real export: give --file export.mp4.')
        f = Path(args.file).expanduser().resolve()
        if not f.is_file():
            error('Export file not found', str(f))
        fp = quick_fingerprint(f)
        prof = read_json(export_av_path(rd, n, fp))
        if not prof:
            error('Run av-profile --video NN --file on this export first: it makes the watch sheets the reviewer reads.')
        beats = read_json(vd / 'beat-map.json').get('beats') or []
        plan = read_json(rd / '70-edit' / f'video-{n:02d}' / 'edit-plan.json')
        spans = {}
        for s in plan.get('shots') or []:
            b = str(s.get('beat_id'))
            lo, hi = spans.get(b, (s['start_s'], s['end_s']))
            spans[b] = (min(lo, s['start_s']), max(hi, s['end_s']))
        text = _fill(FINAL_BRIEF, TITLE=title, HOUSE_RULES=HOUSE_RULES, OUT=out_path)
        text += '\n## What each part was meant to feel like\n'
        for b in beats:
            a_s, b_s = spans.get(str(b.get('id')), (b.get('start_s'), b.get('end_s')))
            text += f'- {_mmss(a_s)}-{_mmss(b_s)}: {b.get("experience") or b.get("narrative_job")} (pace: {b.get("pace") or "-"})\n'
        text += '\n## Watch sheets, in order\n' + '\n'.join(f'- {p}' for p in prof.get('sheets') or []) + '\n'
        text += '\n## Measurements per minute (facts, not verdicts)\n| minute | cuts | moving | wpm | pitch range st |\n|---|---|---|---|---|\n'
        wins = prof.get('windows') or []
        for m0 in range(0, int(prof.get('duration_s') or 0) + 1, 60):
            mw = [w for w in wins if m0 <= (w.get('start_s') or 0) < m0 + 60]
            if not mw:
                continue
            cuts = sum(w.get('cuts') or 0 for w in mw)
            mo = [w['motion_share'] for w in mw if w.get('motion_share') is not None]
            wp = [w['speech_rate_wpm'] for w in mw if w.get('speech_rate_wpm')]
            pr = [w['pitch_range_st'] for w in mw if w.get('pitch_range_st') is not None]
            text += (f'| {_mmss(m0)} | {cuts} | {round(100 * statistics.mean(mo)) if mo else "-"}% | '
                     f'{round(statistics.median(wp)) if wp else "-"} | {round(statistics.median(pr), 1) if pr else "-"} |\n')
        meta.update({'subject_sha256': fp, 'file': str(f)})
    packet = folder / f'packet-{kind}-r{rnd}.md'
    folder.mkdir(parents=True, exist_ok=True)
    packet.write_text(text, encoding='utf-8')
    write_json(folder / f'packet-{kind}-r{rnd}.json', meta)
    emit({'ok': True, 'kind': kind, 'round': rnd, 'packet': str(packet), 'findings_file': str(out_path),
          'next': ('Spawn ONE fresh agent with no other context. Its whole prompt: "Read only ' + str(packet) +
                   ' and follow it exactly." Do not add your rationale, the plan, or what you hope it finds. Then '
                   'review-record --kind ' + kind + '. Never edit the reviewer\'s findings.')})


def cmd_review_record(args):
    """Seal a reviewer's findings for the current round (they can no longer change without plan-check noticing) and
    start the answers file: every finding gets revised (with its lines), kept or disputed (with a reason)."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    kind = args.kind
    recs = review_records(vd, kind)
    rnd = recs[-1][0]['_round'] + 1 if recs else 1
    folder = vd / 'reviews'
    meta = read_json(folder / f'packet-{kind}-r{rnd}.json')
    if not meta:
        error(f'No packet for round {rnd}: run review-packet --kind {kind} first and give it to a fresh reviewer.')
    fpath = Path(args.findings).expanduser() if args.findings else Path(meta['findings_file'])
    raw = read_json(fpath, required=True)
    findings = raw.get('findings')
    if not isinstance(findings, list):
        error('The findings file has no "findings" list.', str(fpath))
    problems, seen = [], set()
    order = list((meta.get('subject_snapshot') or {}).keys())
    for f in findings:
        fid = str(f.get('id') or '').strip() if isinstance(f, dict) else ''
        if not fid or fid in seen:
            problems.append(f'finding without a unique id: {f}')
            continue
        seen.add(fid)
        if f.get('severity') not in ('major', 'minor'):
            problems.append(f'{fid}: severity must be "major" or "minor"')
        if n_words(f.get('problem')) < 4:
            problems.append(f'{fid}: the problem is not described')
        if kind == 'script':
            if not f.get('lines') or expand_lines(f.get('lines'), order) is None:
                problems.append(f'{fid}: "lines" must name lines of the reviewed script (L005 or L005-L009)')
        elif kind == 'treatment':
            if str(f.get('treatment') or '').strip().upper() not in (meta.get('labels') or {}):
                problems.append(f'{fid}: "treatment" must be one of the packet\'s labels')
            else:
                f['treatment_id'] = meta['labels'][str(f['treatment']).strip().upper()]
        elif not re.fullmatch(r'\d{1,3}:\d{2}(\s*-\s*\d{1,3}:\d{2})?', str(f.get('at') or '').strip()):
            problems.append(f'{fid}: "at" must be mm:ss or mm:ss-mm:ss')
    if problems:
        error('The findings file does not follow the packet\'s format. Ask the reviewer to fix the format; never '
              'rewrite its judgement.', problems)
    rec = {'kind': kind, 'round': rnd, 'video': n, 'packet': str(folder / f'packet-{kind}-r{rnd}.md'),
           'subject_sha256': meta['subject_sha256'], 'subject_snapshot': meta.get('subject_snapshot'),
           'labels': meta.get('labels'), 'file': meta.get('file'), 'reviewer': raw.get('reviewer') or 'unstated',
           'verdict': raw.get('verdict') or {k: raw.get(k) for k in ('would_watch', 'why', 'per_treatment') if k in raw},
           'strongest': raw.get('strongest'), 'findings': findings, 'findings_sha256': canonical_sha(findings),
           'recorded_at': now()}
    write_json(folder / f'{kind}-r{rnd}.json', rec)
    ans_path = folder / f'{kind}-r{rnd}-answers.json'
    if not ans_path.exists():
        write_json(ans_path, {'answers': {str(f['id']): {'action': '', 'lines': [], 'note': ''} for f in findings},
                              'how': 'action: revised (script: list the lines changed) | kept (minor only) | disputed; '
                                     'kept and disputed need a reason in note. A major finding is revised or disputed.'})
    majors = [str(f['id']) for f in findings if f.get('severity') == 'major']
    need_more = bool(majors) and rnd < REVIEW_MAX_ROUNDS[kind]
    emit({'ok': True, 'record': str(folder / f'{kind}-r{rnd}.json'), 'answers_file': str(ans_path),
          'findings': len(findings), 'major': majors,
          'next': ('Answer every finding in the answers file and make the revisions. ' +
                   (f'Major findings: after revising, a fresh round-{rnd + 1} read of the new version is required '
                    '(review-packet again, a NEW agent).' if need_more else
                    'No further read is required by the process; another one is always allowed.'))})


def cmd_shot_check(args):
    rd, st = run_folder(args)
    res = shot_facts(rd, args.video)
    emit(res, 0 if res['ready'] else 2)


def export_facts(rd, video, file, deep=False):
    lock = read_json(video_dir(rd, video) / 'length-lock.json')
    if not lock:
        error('Length lock not found for video')
    issues = []
    if not audio_facts(rd, video)['ready']:
        issues.append('audio_gate_failed')
    video_file = Path(file).expanduser().resolve()
    if not video_file.is_file():
        error('Export file not found', str(video_file))
    meta = probe(video_file)
    target = lock['target_length_s']
    if not meta['has_video'] or not meta['has_audio']:
        issues.append('export_missing_picture_or_sound')
    if not meta['width'] or not meta['height'] or abs(meta['width'] / meta['height'] - 16 / 9) > 0.025:
        issues.append('export_aspect_not_16_9')
    if meta['width'] and meta['width'] < 1280:
        issues.append('export_low_resolution')
    if abs(meta['duration_s'] - target) > max(4, target * lock.get('tolerance_export_pct', .025)):
        issues.append('export_duration_misses_user_locked_length')
    diag = {}
    if deep:
        for name, filters in [('black_frames', ['-vf', 'blackdetect=d=0.6:pix_th=0.10']),
                              ('audio_silence', ['-af', 'silencedetect=noise=-48dB:d=2'])]:
            cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-i', str(video_file)] + filters + ['-f', 'null', '-']
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=None)
                rows = [x.strip() for x in p.stderr.splitlines() if
                        ('black_start:' in x if name == 'black_frames' else 'silence_start:' in x)]
                diag[name] = rows[:200]
            except OSError as exc:
                diag[name] = ['scan_unavailable:' + str(exc)]
    return {'ready': not issues, 'issues': issues, 'file': str(video_file), 'metadata': meta, 'target_s': target,
            'difference_s': round(meta['duration_s'] - target, 2), 'diagnostic_flags': diag}


def cmd_release_check(args):
    """Every recorded gate for one export: plan (direction, reviews, length), narration, shot plan, the export
    itself, and the final watch review of THIS file with every finding answered. 'ready' means the process was
    followed through; it does not measure whether the video is good."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    plan = plan_facts(rd, n)
    audio = audio_facts(rd, n)
    shots = shot_facts(rd, n)
    edit = timeline_facts(rd, n)
    exp = export_facts(rd, n, args.file, deep=False)
    fin = review_state(vd, 'final', quick_fingerprint(Path(args.file).expanduser().resolve()))
    issues = ([f'plan:{x}' for x in plan['issues']] + [f'audio:{x}' for x in audio['issues']] +
              [f'shots:{x}' for x in shots['issues']] + [f'edit:{x}' for x in edit['issues']] +
              [f'export:{x}' for x in exp['issues']] + fin['issues'])
    issues = list(dict.fromkeys(issues))
    warnings = list(dict.fromkeys(plan.get('warnings', []) + shots.get('warnings', []) + edit.get('warnings', []) +
                                  fin['warnings']))
    emit({'ready': not issues, 'release_status': 'ready' if not issues else 'blocked', 'issues': issues,
          'warnings': warnings, 'export': {k: exp[k] for k in ('file', 'metadata', 'target_s', 'difference_s')},
          'final_review_rounds': fin['rounds'],
          'note': 'Ready means every recorded gate passed for this exact file. It does not say the video is good: '
                  'that is the director\'s and the reviewers\' judgement, recorded in their files.'},
         0 if not issues else 2)


def cmd_status(args):
    rd, st = run_folder(args)
    inv = read_json(rd / '00-inventory/references.json')
    n = st.get('video_count', 0)
    videos = {}
    for i in range(1, n+1):
        vd = video_dir(rd, i)
        if not (vd / 'length-lock.json').exists():
            videos[str(i)] = {'stage': 'not_locked'}
            continue
        plan = plan_facts(rd, i)
        audio = audio_facts(rd, i)
        videos[str(i)] = {'target_s': read_json(vd/'length-lock.json').get('target_length_s'),
                          'plan_ready': plan['ready'], 'audio_ready': audio['ready'],
                          'creative': {**(plan.get('creative') or {}),
                                       'reviews': {k: len(review_records(vd, k)) for k in REVIEW_MAX_ROUNDS}},
                          'issues': list(dict.fromkeys(plan['issues'] + audio['issues'])),
                          'warnings': plan.get('warnings', [])}
    emit({'ok': True, 'run': str(rd), 'stage': st.get('stage'), 'selected_niche': st.get('selected_niche'),
          'reference_videos': len([x for x in inv.get('items', []) if x.get('kind') == 'video']),
          'videos': videos})


def main():
    # PC adapter: Windows pipes default to cp1252, so a reference name with a character outside it (s-cedilla, an emoji) made the
    # JSON output fail after the work was done; Claude Code sets PYTHONIOENCODING, a plain terminal does not.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(description='Static-only long-form YouTube reference-to-video integrity toolkit')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('doctor'); p.set_defaults(func=cmd_doctor)
    p = sub.add_parser('init'); p.add_argument('--references', required=True); p.add_argument('--workspace')
    p.add_argument('--slug', default='story'); p.add_argument('--fps', type=float, default=5.0)
    p.add_argument('--min-longform', type=int, default=DEFAULT_MIN_LONGFORM); p.set_defaults(func=cmd_init)
    p = sub.add_parser('clone'); p.add_argument('--from-run', required=True); p.add_argument('--workspace'); p.add_argument('--slug', default='clone'); p.set_defaults(func=cmd_clone)
    p = sub.add_parser('scan'); p.add_argument('--run', required=True); p.set_defaults(func=cmd_scan)
    p = sub.add_parser('prepare'); p.add_argument('--run', required=True); p.add_argument('--ids')
    p.add_argument('--fps', type=float); p.add_argument('--width', type=int, default=960)
    # PC adapter: ctranslate2 sees the GPU here but its CUDA runtime (cublas64_12.dll) is missing, so 'auto' picked the GPU and failed
    # on the first encode. CPU/int8 is what the user's other pipelines run on this PC (pass --device cuda --compute-type float16 to override).
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.add_argument('--full-fps', action='store_true')
    p.add_argument('--skip-whisper', action='store_true'); p.add_argument('--dry-run', action='store_true')
    p.set_defaults(func=cmd_prepare)
    p = sub.add_parser('cohorts'); p.add_argument('--run', required=True); p.set_defaults(func=cmd_cohorts)
    p = sub.add_parser('length'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--mode', choices=['standard','own'], required=True); p.add_argument('--niche', default='')
    p.add_argument('--story-form', default=''); p.add_argument('--cohort-id', default='')
    p.add_argument('--refs', default='')
    p.add_argument('--minutes', type=float); p.add_argument('--language', default='en');
    p.add_argument('--pace-wpm', type=float, default=None); p.set_defaults(func=cmd_length)
    p = sub.add_parser('plan-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_plan_check)
    p = sub.add_parser('voice-candidates'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--count', type=int, default=5); p.add_argument('--search', default='')
    p.add_argument('--design', type=int, default=0)
    p.add_argument('--design-description', default='', help='The narrator this story needs: character, register, '
                   'age, accent, delivery (from the creative strategy and the references\' narrators). Pace words '
                   'here do not set the real pace (measured: no steady effect, preview pace not kept on real '
                   'chunks); the real pace is measured on the calibration chunk.')
    p.add_argument('--design-text', default='')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_voice_candidates)
    p = sub.add_parser('voice-pick'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--name', default='')
    p.add_argument('--settings', default=''); p.add_argument('--replace', action='store_true')
    p.set_defaults(func=cmd_voice_pick)
    p = sub.add_parser('voice-probe'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--model-id', default='eleven_v4', choices=TTS_MODELS)
    p.add_argument('--settings', default='', help='JSON voice_settings (stability, similarity_boost), as tts.')
    p.add_argument('--delivery', default=''); p.add_argument('--text', default='', help='The passage to hear, '
                   'inline [tags] included exactly as the script will carry them.')
    p.add_argument('--credit-safety-factor', type=float, default=1.15)
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_voice_probe)
    p = sub.add_parser('tts'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--model-id', default='eleven_v4', choices=TTS_MODELS)
    p.add_argument('--max-chars', type=int); p.add_argument('--execute', action='store_true')
    p.add_argument('--delivery', default='', help='A tag prepended to every part sent. Measured: a pace tag here '
                   'had no lasting effect over a real part. Delivery belongs inline in the script\'s lines, '
                   'decided at the script stage (05 -> Inline audio tags). Not hashed into the integrity check.')
    p.add_argument('--settings', default='', help='JSON voice_settings (stability, similarity_boost) sent with '
                   'every part. Empty uses ElevenLabs\' bare default stability 0.5, which widens variability.')
    p.add_argument('--rerecord-changed', action='store_true', help='Re-record only the recorded parts whose '
                   'lines changed (old takes move to superseded/); the other parts are kept as they are.')
    p.add_argument('--rechunk', action='store_true', help='Start over with fresh part boundaries (every part '
                   're-billed); needs --archive-existing when audio exists.')
    p.add_argument('--archive-existing', action='store_true', help='Move the existing audio folder aside (to '
                   'video-NN-archive-<time>) before starting over with another voice/model/language or --rechunk.')
    p.add_argument('--skip-calibration', action='store_true', help='Allow recording several parts before this '
                   'voice/model/settings has a real measured pace (normally: --max-parts 1, then narration-measure).')
    p.add_argument('--credit-safety-factor', type=float, default=1.15,
                   help='Character-allowance reserve, not a promise of credit price (default 1.15)')
    p.add_argument('--assume-cost-ratio', type=float, default=1.0,
                   help='0.1-1.0, default 1.0 (trust the model\'s documented character_cost_multiplier). '
                   'Below 1.0 is an explicit override of the preflight\'s required balance for a ratio '
                   'of real-billed-to-raw-characters you personally verified this session (e.g. from a '
                   'probe\'s own before/after subscription delta) -- never guessed, always auditable in '
                   'the manifest\'s credit_preflight.assumed_cost_ratio.')
    p.add_argument('--max-parts', type=int, default=None,
                   help='Generate at most N new parts this call, then stop (status stays partial, no '
                   'narration.wav yet, nothing re-billed next time). Use --max-parts 1 to generate only '
                   'the first real chunk, measure/listen to it, and confirm the voice/settings/pace before '
                   'paying for the rest -- the AWL Static pattern: the first chunk IS the calibration '
                   'check, paid once, kept if good, never a separate throwaway sample.')
    p.set_defaults(func=cmd_tts)
    p = sub.add_parser('audio-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_audio_check)
    p = sub.add_parser('narration-measure', help='Real pace, line gap, tag costs, pauses and line times of the narration')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--parts', default='', help='Only these finished parts, e.g. 1 (the calibration part)')
    p.add_argument('--no-delivery', action='store_true', help='Skip the delivery measurement (pitch, loudness, '
                   'rate per beat next to the references)')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_narration_measure)
    p = sub.add_parser('av-profile', help='Measured audiovisual evidence and watch sheets: references or this export')
    p.add_argument('--run', required=True); p.add_argument('--refs', default='')
    p.add_argument('--video', type=int); p.add_argument('--file', default='')
    p.add_argument('--transcript', default='', help='An existing Whisper transcript.json of the export (else Whisper '
                   'medium transcribes it, cached)')
    p.add_argument('--no-sheets', action='store_true'); p.add_argument('--force', action='store_true')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_av_profile)
    p = sub.add_parser('direction-lock', help='Lock the creative direction before the script is written')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--late', default='', help='Only for a video whose script existed first: why (recorded, shown)')
    p.add_argument('--revise', default='', help='Re-lock a changed direction: what changed and why (kept in history)')
    p.set_defaults(func=cmd_direction_lock)
    p = sub.add_parser('review-packet', help='The bare material for ONE fresh reviewer agent')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--kind', required=True, choices=list(REVIEW_MAX_ROUNDS))
    p.add_argument('--file', default='', help='The export (final review)'); p.set_defaults(func=cmd_review_packet)
    p = sub.add_parser('review-record', help='Seal a reviewer\'s findings and start the answers file')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--kind', required=True, choices=list(REVIEW_MAX_ROUNDS))
    p.add_argument('--findings', default='', help='Default: the findings file the packet named')
    p.set_defaults(func=cmd_review_record)
    p = sub.add_parser('shot-check', help='The shot plan as a visual argument, plus repetition signals')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_shot_check)
    p = sub.add_parser('release-check', help='Every recorded gate for one export, final watch review included')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--file', required=True); p.set_defaults(func=cmd_release_check)
    p = sub.add_parser('direction-reapprove', help='After a meaningful direction change: this artifact, as it is, '
                       'still serves the locked treatment (recorded with its reason, for this revision)')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--artifact', required=True, choices=list(ALL_ARTIFACTS)); p.add_argument('--reason', required=True)
    p.set_defaults(func=cmd_direction_reapprove)
    p = sub.add_parser('media-check', help='The check the image and music workers run before generating, on a job file')
    p.add_argument('--job', required=True); p.add_argument('--kind', required=True, choices=['stills', 'music'])
    p.set_defaults(func=cmd_media_check)
    p = sub.add_parser('pace-profile', help='Pace and pauses of the references (and the measured narration)')
    p.add_argument('--run', required=True); p.add_argument('--refs', default=''); p.add_argument('--video', type=int)
    p.set_defaults(func=cmd_pace_profile)
    p = sub.add_parser('retime-shots', help='Time the shot plan to the real narration and its edit holds')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--render-narration', action='store_true', help='Also write narration-edit.wav with the holds')
    p.set_defaults(func=cmd_retime_shots)
    p = sub.add_parser('timeline-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_timeline_check)
    p = sub.add_parser('export-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--file', required=True); p.add_argument('--deep', action='store_true'); p.set_defaults(func=cmd_export_check)
    p = sub.add_parser('status'); p.add_argument('--run', required=True); p.set_defaults(func=cmd_status)
    args = ap.parse_args()
    try:
        args.func(args)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as exc:
        error(type(exc).__name__ + ': ' + str(exc)[:800])


if __name__ == '__main__':
    main()
