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
    emit({'ok': checks['ffmpeg'] and checks['ffprobe'], 'checks': checks,
          'note': 'Whisper is required for reference audio analysis; image/CapCut/TTS tools are checked separately.'})


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
    (rd / 'todo.md').write_text('# Static Studio run\n\n- [ ] Inventory and prepare references\n- [ ] Analyze evidence and choose niche\n- [ ] Lock comparable long-form length\n- [ ] Research and plan original story\n- [ ] Record complete narration\n- [ ] Design and assemble image-led edit\n- [ ] Export and independently verify final video\n', encoding='utf-8')
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
    (rd/'todo.md').write_text('# Cloned Static analysis\n\n- [ ] Choose niche and lock a new video length\n- [ ] Plan and produce new long-form YouTube video\n', encoding='utf-8')
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


def count_words(text):
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text, flags=re.UNICODE))


def strip_transcript_timestamps(raw):
    """Remove [start-end] timestamp prefixes (e.g. [0.0-2.4]) from transcript lines."""
    lines = []
    for line in raw.splitlines():
        cleaned = re.sub(r'^\s*\[[\d.]+\s*[-–]\s*[\d.]+\]\s*', '', line)
        if cleaned.strip():
            lines.append(cleaned)
    return ' '.join(lines)


def wpm_from_transcript_raw(raw):
    """Pure-narration WPM from a [start-end] text transcript: spoken words (timestamps
    stripped from the count) over the sum of spoken-chunk durations (silence excluded).
    This is the narrator's actual speaking rate, not a video-duration-diluted figure.
    Returns None if the transcript has no parseable [start-end] chunks."""
    narr_s = sum(float(m.group(2)) - float(m.group(1))
                 for m in re.finditer(r'\[([\d.]+)-([\d.]+)\]', raw))
    if narr_s <= 0:
        return None
    wc = count_words(strip_transcript_timestamps(raw))
    return round(wc / (narr_s / 60))


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
    if beats.get('target_length_s') != lock['target_length_s']:
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
            for key in ('narrative_job', 'visual_intent'):
                if not str(beat.get(key) or '').strip():
                    issues.append(f'beat_{n}_missing_{key}')
            cursor_s, cursor_line = end, lend
        except (TypeError, ValueError, KeyError):
            issues.append(f'beat_{n}_bad_structure')
    if timing and (abs(cursor_s - lock['target_length_s']) > 1 or cursor_line != len(lines)):
        issues.append('beats_do_not_cover_all_time_and_lines')
    words = sum(count_words(x.get('text', '')) for x in lines)
    pause_s = sum(float(x.get('pause_after_s', 0)) for x in lines) if lines else 0
    pace = float(script.get('pace_wpm') or lock.get('pace_wpm') or 0)
    forecast = round(words * 60 / pace + pause_s, 2) if pace else 0
    if not pace:
        issues.append('script_missing_narration_pace')
    if abs(forecast - lock['target_length_s']) > max(10, .08 * lock['target_length_s']):
        issues.append('script_forecast_misses_locked_length_by_over_8pct')
    if not (vd / 'editorial-review.md').exists():
        issues.append('editorial_review_missing')
    return {'ready': not issues, 'issues': issues, 'script_lines': len(lines), 'words': words,
            'planned_pauses_s': round(pause_s, 2), 'narration_pace_wpm': pace,
            'forecast_s': forecast, 'locked_target_s': lock['target_length_s'],
            'target_words_without_pauses': round(lock['target_length_s'] * pace/60) if pace else None}


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


def model_limit(model):
    known = {'eleven_v4': 10000, 'eleven_v3': 3000, 'eleven_multilingual_v2': 10000,
             'eleven_flash_v2_5': 40000, 'eleven_turbo_v2_5': 40000}
    return known.get(model, 3000)


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
    it (Whisper), and measure its pace with the same pure-narration-time method used for
    reference transcripts, so candidates are comparable to the locked script's pace_wpm.
    Writes a report for the user to listen to and pick from; picks nothing itself."""
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
                  '(e.g. "calm, grave, measured male documentary narrator, American accent").')
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
                                'file': None, 'measured_wpm': None, 'error': 'voice has no preview_url'})
                continue
            try:
                with urllib.request.urlopen(c['preview_url'], timeout=30) as resp:
                    fname.write_bytes(resp.read())
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
                results.append({**{k: c[k] for k in ('source', 'voice_id', 'name', 'labels')},
                                'file': None, 'measured_wpm': None,
                                'error': f'preview download failed: {type(exc).__name__}: {str(exc)[:160]}'})
                continue
        else:
            fname.write_bytes(base64.b64decode(c['audio_base_64']))
        tpath = outdir / f'{stem}.json'
        wpm, heard = None, None
        try:
            transcribe(fname, tpath, args.whisper_model, args.device, args.compute_type)
            raw = tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace')
            wpm = wpm_from_transcript_raw(raw)
            heard = strip_transcript_timestamps(raw).strip() or None
        except (RuntimeError, ValueError, OSError) as exc:
            heard = f'transcription failed: {type(exc).__name__}: {str(exc)[:160]}'
        results.append({'source': c['source'], 'voice_id': c['voice_id'], 'name': c.get('name'),
                        'labels': c.get('labels'), 'file': str(fname), 'measured_wpm': wpm, 'heard_text': heard})
    report = {'video': int(args.video), 'search': args.search, 'design_description': args.design_description,
              'candidates': results}
    report_path = outdir.parent / 'candidates.json'
    write_json(report_path, report)
    emit({'ok': True, 'candidates_file': str(report_path), 'count': len(results), 'candidates': results,
          'guidance': 'Listen to each file. Compare measured_wpm across candidates (and, once known, against '
                      'the locked pace_wpm). Then lock the pick: voice-pick --run RUN --video NN --voice-id ID.'})


def cmd_voice_pick(args):
    """Lock the run's narrator voice. One voice for the whole run (every video, every
    language) unless --replace is explicitly passed to deliberately change it."""
    rd, st = run_folder(args)
    lockfile = rd / '60-voice' / 'voice-lock.json'
    if lockfile.exists() and not args.replace:
        error('Voice already locked for this run. Pass --replace to deliberately change it.',
              {'file': str(lockfile)})
    try:
        settings = json.loads(args.settings) if args.settings else {}
    except ValueError as exc:
        error('--settings must be valid JSON.', str(exc))
    measured_wpm = None
    cfile = rd / '60-voice' / f'video-{int(args.video):02d}' / 'candidates.json'
    for c in (read_json(cfile).get('candidates') or []):
        if c.get('voice_id') == args.voice_id:
            measured_wpm = c.get('measured_wpm')
            break
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    lock = {'voice_id': args.voice_id, 'name': args.name, 'settings': settings, 'measured_wpm': measured_wpm,
            'locked_at': now(), 'rule': 'One voice per run across every video and language; '
                                        '--replace required to deliberately change it.'}
    write_json(lockfile, lock)
    emit({'ok': True, 'lock_file': str(lockfile), 'voice_id': args.voice_id, 'measured_wpm': measured_wpm,
          'guidance': f'Pass --voice-id {args.voice_id} to every "tts" call for this run.'})


def cmd_tts(args):
    rd, st = run_folder(args)
    chk = plan_facts(rd, args.video)
    if not chk['ready']:
        error('Plan must pass objective checks before billed audio generation', chk['issues'])
    vd = video_dir(rd, args.video)
    script = read_json(vd / 'script.json', required=True)
    lock = read_json(vd / 'length-lock.json', required=True)
    limit = min(args.max_chars or model_limit(args.model_id), model_limit(args.model_id))
    limit = min(limit, 3000) if args.model_id == 'eleven_v3' else min(limit, 8000)
    chunks = chunks_for_lines(script['lines'], limit)
    narrdir = rd / '50-audio' / f'video-{int(args.video):02d}'
    narrdir.mkdir(parents=True, exist_ok=True)
    manifest_path = narrdir / 'manifest.json'
    existing = read_json(manifest_path)
    spec = {'model_id': args.model_id, 'voice_id': args.voice_id, 'language': lock['language'],
            'chunks': [{'id': i+1, 'line_start': c['line_start'], 'line_end': c['line_end'],
                        'text_sha256': hashlib.sha256(c['text'].encode()).hexdigest(),
                        'file': f'part-{i+1:03d}.mp3', 'characters': len(c['text'])}
                       for i, c in enumerate(chunks)]}
    if not (1.0 <= args.credit_safety_factor <= 3.0):
        error('--credit-safety-factor must be from 1.0 to 3.0')
    if not args.execute:
        emit({'ok': True, 'mode': 'dry_run_no_charges', 'video': args.video,
              'parts': len(chunks), 'characters_total': sum(len(x['text']) for x in chunks),
              'model_limit_per_request': model_limit(args.model_id),
              'target_length_s': lock['target_length_s'], 'candidate_manifest': spec,
              'next': 'Review credits, voice and preview. Re-run with --execute only after approving cost.'})
        return
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    if existing and any(existing.get(x) != spec[x] for x in ('model_id', 'voice_id', 'language')):
        error('Existing partial audio uses another voice/model/language; choose a new video or manually archive the old manifest.')
    if existing.get('chunks') and [{k: x[k] for k in ('id', 'line_start', 'line_end', 'text_sha256', 'file', 'characters')}
                                  for x in existing['chunks']] != spec['chunks']:
        error('Script changed since audio generation began. Reconcile/re-record affected chunks explicitly.')
    remaining_chunks = [c for i, c in enumerate(chunks)
                        if not ((i + 1) in existing.get('finished_parts', [])
                        and (narrdir / f'part-{i+1:03d}.mp3').is_file()
                        and (narrdir / f'part-{i+1:03d}.mp3').stat().st_size > 1024)]
    budget = preflight_elevenlabs_balance(key, sum(len(c['text']) for c in remaining_chunks),
                                         args.credit_safety_factor) if remaining_chunks else {'remaining_script_characters': 0}
    manifest = {**spec, 'status': 'partial', 'created_at': existing.get('created_at', now()),
                'credit_preflight': budget,
                'finished_parts': existing.get('finished_parts', [])}
    write_json(manifest_path, manifest)
    for i, c in enumerate(chunks):
        fname = narrdir / f'part-{i+1:03d}.mp3'
        if (i+1) in manifest['finished_parts'] and fname.exists() and fname.stat().st_size > 1024:
            continue
        body = {'text': c['text'], 'model_id': args.model_id}
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
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, RuntimeError) as exc:
            manifest['error'] = f'part {i+1}: {type(exc).__name__}: {str(exc)[:250]}'
            write_json(manifest_path, manifest)
            error('Partial ElevenLabs recording: BLOCKED (never shorten video to match credits).', manifest['error'])
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
    return {'ready': not issues, 'issues': issues, 'duration_s': duration,
            'target_length_s': target, 'script_lines': len(script.get('lines') or []),
            'recorded_lines': cursor, 'manifest_status': manifest.get('status')}


def cmd_audio_check(args):
    rd, st = run_folder(args)
    result = audio_facts(rd, args.video)
    emit(result, 0 if result['ready'] else 2)


def cmd_timeline_check(args):
    rd, st = run_folder(args)
    lock = read_json(video_dir(rd, args.video) / 'length-lock.json')
    track = read_json(rd / '70-edit' / f'video-{int(args.video):02d}' / 'timeline.json')
    sound = audio_facts(rd, args.video)
    issues = ([] if sound['ready'] else ['audio_gate_failed'])
    if not lock:
        issues.append('length_lock_missing')
    seq = track.get('visual_segments') or []
    if not seq:
        issues.append('timeline_visual_segments_missing')
    cursor = 0.0
    for i, clip in enumerate(seq, 1):
        try:
            a, b = float(clip['start_s']), float(clip['end_s'])
            if abs(a-cursor) > .16 or b <= a:
                issues.append(f'visual_gap_overlap_{i}')
            if not str(clip.get('beat_id') or '').strip():
                issues.append(f'visual_{i}_missing_beat_link')
            if not str(clip.get('purpose') or '').strip():
                issues.append(f'visual_{i}_missing_story_purpose')
            cursor = b
        except (KeyError, TypeError, ValueError):
            issues.append(f'bad_visual_segment_{i}')
    if lock and abs(cursor - lock['target_length_s']) > max(4, lock['target_length_s'] * .025):
        issues.append('timeline_misses_locked_target')
    if track.get('canvas') not in ('1920x1080', '2560x1440', '3840x2160'):
        issues.append('canvas_not_youtube_16_9')
    emit({'ready': not issues, 'issues': issues, 'last_visual_end_s': cursor,
          'target_length_s': lock.get('target_length_s'), 'audio_ready': sound['ready']}, 0 if not issues else 2)


def cmd_export_check(args):
    rd, st = run_folder(args)
    lock = read_json(video_dir(rd, args.video) / 'length-lock.json')
    issues = []
    if not lock:
        error('Length lock not found for video')
    if not audio_facts(rd, args.video)['ready']:
        issues.append('audio_gate_failed')
    video = Path(args.file).expanduser().resolve()
    if not video.is_file():
        error('Export file not found', str(video))
    meta = probe(video)
    target = lock['target_length_s']
    if not meta['has_video'] or not meta['has_audio']:
        issues.append('export_missing_picture_or_sound')
    if not meta['width'] or not meta['height'] or abs(meta['width']/meta['height'] - 16/9) > 0.025:
        issues.append('export_aspect_not_16_9')
    if meta['width'] and meta['width'] < 1280:
        issues.append('export_low_resolution')
    if abs(meta['duration_s']-target) > max(4, target*lock.get('tolerance_export_pct', .025)):
        issues.append('export_duration_misses_user_locked_length')
    deep = {}
    if args.deep:
        for name, filters in [('black_frames', ['-vf', 'blackdetect=d=0.6:pix_th=0.10']),
                              ('audio_silence', ['-af', 'silencedetect=noise=-48dB:d=2'])]:
            cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-i', str(video)] + filters + ['-f', 'null', '-']
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=None)
                lines = [x.strip() for x in p.stderr.splitlines() if
                         ('black_start:' in x if name == 'black_frames' else 'silence_start:' in x)]
                deep[name] = lines[:200]
            except OSError as exc:
                deep[name] = ['scan_unavailable:' + str(exc)]
    emit({'ready': not issues, 'issues': issues, 'file': str(video), 'metadata': meta,
          'target_s': target, 'difference_s': round(meta['duration_s']-target, 2), 'diagnostic_flags': deep,
          'manual_review_required': ['watch opening/first minute', 'sample each major narrative chapter',
                                     'watch last minute', 'listen to all TTS joins',
                                     'check factual assertions/visual chronology', 'review title-thumbnail promise']},
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
                          'issues': list(dict.fromkeys(plan['issues'] + audio['issues']))}
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
    p.add_argument('--design', type=int, default=0); p.add_argument('--design-description', default='')
    p.add_argument('--design-text', default='')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_voice_candidates)
    p = sub.add_parser('voice-pick'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--name', default='')
    p.add_argument('--settings', default=''); p.add_argument('--replace', action='store_true')
    p.set_defaults(func=cmd_voice_pick)
    p = sub.add_parser('tts'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--model-id', default='eleven_v4')
    p.add_argument('--max-chars', type=int); p.add_argument('--execute', action='store_true')
    p.add_argument('--credit-safety-factor', type=float, default=1.15,
                   help='Character-allowance reserve, not a promise of credit price (default 1.15)')
    p.set_defaults(func=cmd_tts)
    p = sub.add_parser('audio-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_audio_check)
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
