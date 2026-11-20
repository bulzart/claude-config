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
    # The word budget comes from how many words a minute of the comparable narration really holds, pauses included
    # (overall_wpm), never from the speaking rate alone (active_wpm, which leaves every pause out: on 2026-11-19 that
    # overstated the budget by about 11%). An explicit --pace-wpm scales the references' overall rate by the same ratio.
    stats = {vid: ref_pace_stats(rd, vid, family[vid].get('duration_s')) for vid in refs}
    stats = {k: v for k, v in stats.items() if v}
    def mean_of(key):
        vals = [s[key] for s in stats.values() if s.get(key)]
        return round(statistics.mean(vals)) if vals else None
    active_refs, overall_refs = mean_of('active_wpm'), mean_of('overall_wpm')
    speech_only_words = round(target * pace_wpm / 60)
    if overall_refs and active_refs:
        target_words = round(target * overall_refs * (pace_wpm / active_refs) / 60)
    else:
        target_words = speech_only_words
    pace_profile = {'active_wpm': pace_wpm, 'overall_wpm': round(overall_refs * pace_wpm / active_refs)
                    if overall_refs and active_refs else None, 'runtime_wpm': mean_of('runtime_wpm'),
                    'references': stats, 'definitions': PACE_DEFINITIONS}
    lock = {'schema': SCHEMA, 'video': f'{int(args.video):02d}', 'mode': args.mode,
            'target_length_s': target, 'tolerance_audio_pct': 0.04, 'tolerance_export_pct': 0.025,
            'niche': effective_niche, 'story_form': effective_form, 'reference_ids': refs,
            'reference_durations_s': {i: family[i]['duration_s'] for i in refs},
            'language': args.language, 'pace_wpm': pace_wpm, 'pace_wpm_source': pace_wpm_source,
            'per_ref_wpm': per_ref_wpm, 'pace_profile': pace_profile,
            'target_words': target_words, 'target_words_speech_only': speech_only_words,
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
    words_note = (f'Write the script to about {target_words} words: the comparable narration holds '
                  f'{pace_profile["overall_wpm"]} words a minute with its own pauses ({pace_wpm} while speaking). '
                  if pace_profile['overall_wpm'] else
                  f'Write the script to under {speech_only_words} words (speech alone, no pauses counted: the '
                  'references have no word timings here). ')
    emit({'ok': True, 'lock_file': str(lockfile), 'locked_target_s': target, 'minutes': round(target/60, 2),
          'niche': effective_niche, 'story_form': effective_form, 'references': refs,
          'pace_wpm': pace_wpm, 'pace_wpm_source': pace_wpm_source, 'per_ref_wpm': per_ref_wpm,
          'pace_profile': pace_profile, 'target_words': target_words, 'target_words_speech_only': speech_only_words,
          'guidance': (f'Script, beat map, narration, timeline and export must respect this exact locked target. '
                       f'{wpm_note}. {words_note}plan-check forecasts the real length from the voice\'s own measured '
                       'pace and gaps once its first part is measured.')})


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
        # A silence the story wants says what it is for: what the viewer takes in, feels or sees while it lasts. A
        # held moment is a creative choice, never runtime; the cold reader sees every one (review-packet).
        if n_words(row.get('pause_purpose')) < MIN_NOTE_WORDS:
            issues.append(f'pause_{lid}_needs_its_story_purpose')
        plan.append({'line': lid, 'index': i + 1, 'pause_after_s': p, 'via': via,
                     'purpose': str(row.get('pause_purpose') or '').strip() or None})
    return plan, issues


def hold_snapshot(lines):
    """Every realised pause (longer than a natural line gap, by a pause tag or an edit hold) as the script's cold
    reader is shown it: {line: [seconds, via]}."""
    return {p['line']: [round(p['pause_after_s'], 2), p['via']] for p in script_pause_plan(lines)[0]}


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


# ---------------------------------------------------------------- what the voice is sent, and what it never is
# A script holds four different things, each in its own place:
#   1. the canonical narration: a line's `text`, exactly the words the viewer hears (captions come from it);
#   2. delivery tags: [bracketed] directions inline in `text`, sent to ElevenLabs, never spoken;
#   3. pronunciation: 40-plans/video-NN/pronunciation.json, applied only to what is sent, never to `text`;
#   4. editorial notes: a line's `note` field, never sent.
# Anything else that reaches the voice as markup (SSML, which Eleven v4 does not support; {braces}; *asterisks*; a stage
# direction in parentheses; a note in brackets) is read aloud or ignored, so plan-check refuses it.
SSML_RX = re.compile(r'<\s*/?\s*[A-Za-z][^<>]*>')
CURLY_RX = re.compile(r'\{[^{}]*\}')
ASTERISK_RX = re.compile(r'\*{1,2}[^*\s][^*]*\*{1,2}')
PAREN_RX = re.compile(r'\(([^()]{1,60})\)')
NOTE_TAG_RX = re.compile(r'^\s*(?:\d+|notes?|todo|tk|fixme|sources?|refs?|cite|citation|check|fact[- ]?check|'
                         r'placeholder|xx+|editor)\b', re.I)
IPA_SYMBOLS = set('ˈˌːəɪʊʃʒθðŋɑɔæɛʌɒɜɐɚɝɨʉɯɲɳɴɸβçʝɣχʁħʕɦɬɮɹɻʎʟɾɽʀʙʋɥʍʔ')
IPA_RX = re.compile(r'/[^/\s][^/]*/')
_CONTRAST = None


def contrast_axes():
    """The catalogue's opposite poles of delivery (volume, energy, tempo): asked for together on the same words, they
    contradict each other (ElevenLabs: contrasting tags on the same words blur the performance)."""
    global _CONTRAST
    if _CONTRAST is None:
        _CONTRAST = read_json(TAGS_FILE).get('contrast_axes') or {}
    return _CONTRAST


def tag_qualities(inner):
    """The qualities one tag asks for: '[tense, cautious]' -> ['tense', 'cautious']."""
    return [q.strip().lower() for q in str(inner).split(',') if q.strip()]


def contradictions(qualities):
    """The delivery axes on which these qualities ask for both poles at once ([whispering, shouting])."""
    text = ' ' + ' '.join(qualities) + ' '
    words = set(re.findall(r"[a-z']+", text))
    out = []
    for axis, poles in contrast_axes().items():
        hit = [pole for pole, terms in poles.items()
               if any((' ' + t + ' ' in text) if ' ' in t else (t in words) for t in terms)]
        if len(hit) > 1:
            out.append(axis)
    return out


def script_markup(lines):
    """Markup the voice can't take and delivery directions that fight each other (issues); tags stacked on the same
    words (a warning: several qualities go in one bracket, [a, b])."""
    issues, warnings = [], []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i+1:03d}')
        text = str(row.get('text') or '')
        if SSML_RX.search(text):
            issues.append(f'ssml_markup_not_supported_by_eleven_v4:{lid}')
        if CURLY_RX.search(text):
            issues.append(f'curly_brace_markup:{lid}')
        if ASTERISK_RX.search(text):
            issues.append(f'asterisk_markup:{lid}')
        for m in PAREN_RX.finditer(text):
            inner = ' '.join(m.group(1).lower().split())
            if '[' + inner + ']' in tag_catalogue() or is_pause_tag(inner) or inner in ('beat', 'silence', 'breath'):
                issues.append(f'stage_direction_in_parentheses:{lid}:({inner})')
        if any(set(x) & IPA_SYMBOLS for x in IPA_RX.findall(strip_tags(text))):
            issues.append(f'pronunciation_markup_in_script_text:{lid}')
        tags = list(TAG_RE.finditer(text))
        for m in tags:
            if NOTE_TAG_RX.match(m.group(1)):
                issues.append(f'editorial_note_in_spoken_text:{lid}:[{m.group(1).strip()}]')
        groups = []
        for k, m in enumerate(tags):
            if groups and not text[tags[k - 1].end():m.start()].strip():
                groups[-1].append(m)
            else:
                groups.append([m])
        for g in groups:
            shown = ''.join(m.group(0) for m in g)
            for axis in contradictions([q for m in g for q in tag_qualities(m.group(1))]):
                issues.append(f'contradictory_delivery:{lid}:{axis}:{shown}')
            if len(g) > 1:
                warnings.append(f'{lid}: tags stacked on the same words ({shown}); several qualities go in one bracket')
    return issues, warnings


def delivery_review_lines(review_text):
    """The line ids named under a "Delivery and tags" heading of editorial-review.md (where each kept tag says why)."""
    m = re.search(r'^#+[^\n]*delivery and tags[^\n]*\n(.*?)(?=^#|\Z)', review_text or '', flags=re.I | re.M | re.S)
    return set(re.findall(r'\bL\d{3,4}\b', m.group(1))) if m else set()


PRONUNCIATION_HOW = ('ipa', 'respell')
PRONUNCIATION_CONFIDENCE = ('confirmed', 'likely', 'uncertain')


def pronunciation_path(rd, video):
    return video_dir(rd, video) / 'pronunciation.json'


def term_rx(term):
    return re.compile(r'(?<![\w-])' + re.escape(term) + r'(?![\w-])')


def pronunciation_facts(rd, video, lines):
    """The episode's pronunciation list (40-plans/video-NN/pronunciation.json): the names and terms this voice may
    say wrong, each in a form Eleven v4 documents (IPA between slashes, or a respelling), where that pronunciation
    comes from and how sure it is. Only what is sent changes: the script and the captions keep the canonical
    spelling. An uncertain entry is flagged for listening, never treated as settled."""
    p = pronunciation_path(rd, video)
    out = {'file': str(p), 'issues': [], 'warnings': [], 'terms': [], 'uses': {}}
    if not p.is_file():
        return out
    d = read_json(p)
    if not d:
        out['issues'].append('pronunciation_file_unreadable')
        return out
    seen = set()
    for k, t in enumerate(d.get('terms') or [], 1):
        t = t if isinstance(t, dict) else {}
        term, say = str(t.get('term') or '').strip(), str(t.get('say') or '').strip()
        how, conf = str(t.get('how') or '').strip().lower(), str(t.get('confidence') or '').strip().lower()
        name = term or f'entry_{k}'
        if not term or not say:
            out['issues'].append(f'pronunciation_{name}_needs_term_and_say')
            continue
        if term in seen:
            out['issues'].append(f'pronunciation_{name}_listed_twice')
        seen.add(term)
        if how not in PRONUNCIATION_HOW:
            out['issues'].append(f'pronunciation_{name}_how_must_be:' + '/'.join(PRONUNCIATION_HOW))
        elif how == 'ipa' and not IPA_RX.fullmatch(say):
            out['issues'].append(f'pronunciation_{name}_ipa_goes_between_slashes')
        elif how == 'respell' and re.search(r'[/\[\]<>{}"]', say):
            out['issues'].append(f'pronunciation_{name}_respelling_is_plain_letters')
        if conf not in PRONUNCIATION_CONFIDENCE:
            out['issues'].append(f'pronunciation_{name}_confidence_must_be:' + '/'.join(PRONUNCIATION_CONFIDENCE))
        elif conf != 'uncertain' and n_words(t.get('source')) < 3:
            out['issues'].append(f'pronunciation_{name}_needs_its_source')
        elif conf == 'uncertain':
            out['warnings'].append(f'the pronunciation of "{term}" is uncertain ({say}): hear it on a short probe or '
                                   'trial before the parts that say it are recorded, and let the user listen')
        rx = term_rx(term)
        uses = [str(r.get('id') or f'L{i + 1:03d}') for i, r in enumerate(lines)
                if rx.search(strip_tags(r.get('text') or ''))]
        if not uses:
            out['warnings'].append(f'pronunciation entry "{term}" is not in the script')
        out['uses'][term] = uses
        out['terms'].append({'term': term, 'say': say, 'how': how, 'confidence': conf, 'rx': rx})
    return out


def tts_text(text, terms):
    """What ElevenLabs is sent for one line: its canonical text with its tags in place, every listed term in the
    form v4 pronounces: IPA between slashes inside double quotes (as ElevenLabs' own examples write it), or a
    respelling."""
    out = str(text).strip()
    for t in terms or []:
        if t.get('how') in PRONUNCIATION_HOW:
            form = f'"{t["say"]}"' if t['how'] == 'ipa' else t['say']
            out = t['rx'].sub(lambda m, f=form: f, out)
    return out


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
# The direction lock carries a production revision. A change that alters what production must do (another treatment
# chosen, the chosen treatment's narrator, visual language, sound..., the strategy's progression, another approach)
# raises the revision and marks the artifacts that field feeds (FIELD_EFFECTS). Each marked artifact must then be
# really updated (its content changes and its own checks apply: a script edit beyond a trim still gets a fresh read)
# or explicitly reapproved (`direction-reapprove`, with a reason, on record) before a stage that uses it continues.
# Evidence, alternatives, reasons and samples feed nothing: no new revision, nothing to redo, no new read.
TRACKED_FILES = ('beat-map', 'script', 'shot-plan', 'style-bible')
# 'voice' is the episode's narrator choice (60-voice/video-NN/voice-lock.json): a narrator change asks whether the
# chosen voice and its settings still fit, exactly as it asks of the recorded parts.
MEDIA_ARTIFACTS = ('voice', 'narration', 'stills', 'music', 'edit')
ALL_ARTIFACTS = TRACKED_FILES + MEDIA_ARTIFACTS
FIELD_EFFECTS = {
    'decision.treatment': ALL_ARTIFACTS,
    'chosen_approach.id': ('beat-map', 'script', 'shot-plan', 'edit'),
    'strategy.viewer_experience': ('beat-map', 'script'),
    'strategy.progression': ('beat-map', 'script', 'shot-plan', 'edit'),
    'strategy.facts_as_experience': ('beat-map', 'script'),
    'strategy.picture_contribution': ('shot-plan', 'style-bible', 'stills'),
    'strategy.sound_and_breath': ('beat-map', 'music', 'edit'),
    'treatment.narrator': ('beat-map', 'script', 'voice', 'narration'),
    'treatment.writing_voice': ('script',),
    'treatment.structure_and_pace': ('beat-map', 'script', 'shot-plan', 'edit'),
    'treatment.visual_language': ('shot-plan', 'style-bible', 'stills', 'edit'),
    'treatment.sound': ('beat-map', 'music', 'edit'),
    'treatment.audiovisual_relationship': ('beat-map', 'shot-plan', 'edit'),
    'treatment.emotional_course': ('beat-map', 'script'),
}
NO_EFFECT = ('evidence', 'approaches', 'other_treatments', 'decision.reasons', 'chosen_approach.why',
             'chosen_approach.runner_up', 'chosen_approach.why_not_runner_up', 'strategy.why_this_idea',
             'strategy.fits_and_forced', 'strategy.distinct_from_references', 'treatment.name',
             'treatment.evidence_used', 'treatment.departures', 'treatment.risks', 'treatment.samples')
TREATMENT_REREAD_BELOW = 0.7   # under this share of its blind read's vocabulary, the chosen treatment is a new one


def field_effects(key):
    """The artifacts a change to this part of direction.json must be followed by; a part this table doesn't know is
    assumed to matter for all of them."""
    if key in FIELD_EFFECTS:
        return FIELD_EFFECTS[key]
    if key in NO_EFFECT or key.startswith('other.'):
        return ()
    return ALL_ARTIFACTS


def artifact_path(rd, video, name):
    n = int(video)
    vis, edit = rd / '60-visuals' / f'video-{n:02d}', rd / '70-edit' / f'video-{n:02d}'
    return {'beat-map': video_dir(rd, n) / 'beat-map.json', 'script': video_dir(rd, n) / 'script.json',
            'shot-plan': vis / 'shot-plan.json', 'style-bible': vis / 'style-bible.md',
            'voice': rd / '60-voice' / f'video-{n:02d}' / 'voice-lock.json',
            'narration': rd / '50-audio' / f'video-{n:02d}' / 'manifest.json',
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
    """One hash per part of direction.json (each field of the chosen approach, the strategy and the chosen
    treatment on its own), so a revision can tell exactly what changed."""
    trs = {str(t.get('id')): t for t in d.get('treatments') or [] if isinstance(t, dict)}
    dec = d.get('decision') if isinstance(d.get('decision'), dict) else {}
    chosen = str(dec.get('treatment'))
    out = {'evidence': canonical_sha(d.get('evidence')), 'approaches': canonical_sha(d.get('approaches')),
           'other_treatments': canonical_sha({k: v for k, v in trs.items() if k != chosen}),
           'decision.treatment': canonical_sha(chosen),
           'decision.reasons': canonical_sha({k: v for k, v in dec.items() if k != 'treatment'})}
    for group, part in (('chosen_approach', d.get('chosen_approach')), ('strategy', d.get('strategy')),
                        ('treatment', trs.get(chosen))):
        for k, v in (part if isinstance(part, dict) else {}).items():
            if not (group == 'treatment' and k == 'id'):
                out[f'{group}.{k}'] = canonical_sha(v)
    for k, v in d.items():
        if k not in ('evidence', 'approaches', 'treatments', 'decision', 'chosen_approach', 'strategy'):
            out['other.' + k] = canonical_sha(v)
    return out


def treatment_text(t):
    """A treatment's words, as a reader of it sees them: its fields and its sample moments."""
    t = t if isinstance(t, dict) else {}
    s = t.get('samples') if isinstance(t.get('samples'), dict) else {}
    return ' '.join([str(t.get(k) or '') for k in TREATMENT_KEYS] +
                    [str((s.get(m) or {}).get(x) or '') for m in SAMPLE_MOMENTS for x in ('narration', 'picture')])


def chosen_treatment_of(d):
    dec = d.get('decision') if isinstance(d.get('decision'), dict) else {}
    return next((t for t in d.get('treatments') or [] if isinstance(t, dict)
                 and str(t.get('id')) == str(dec.get('treatment'))), {})


def media_present(rd, video, name):
    p = artifact_path(rd, video, name)
    return p.is_file() and bool(read_json(p))


def _pkey(path):
    """One spelling per file, whichever tool wrote the path (CapCut writes C:/..., Python C:\\...)."""
    return os.path.normcase(str(Path(str(path)).expanduser().resolve()))


def required_rev(lock, artifact):
    """The production revision that last affected this artifact (None: no direction change has touched it)."""
    return ((lock.get('required') or {}).get(artifact) or {}).get('rev')


def reapproved_for(lock, artifact):
    """The explicit reapproval of this artifact that still applies: given for the revision that last touched it, or,
    for an artifact no change has touched (user-supplied stills, say), until one does."""
    ra = (lock.get('reapproved') or {}).get(artifact) or {}
    if not ra:
        return None
    req = required_rev(lock, artifact)
    return ra if req is None or ra.get('rev') == req else None


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


def narration_outdated_parts(lock, manifest):
    """Recorded parts made before the latest direction change that touched the narrator (a part recorded before
    parts carried their revision counts as made before any), unless the narration was reapproved for it."""
    req = required_rev(lock, 'narration')
    if not req or reapproved_for(lock, 'narration'):
        return []
    revs = manifest.get('part_revs') or {}
    out = []
    for x in manifest.get('finished_parts') or []:
        try:
            if int(revs.get(str(x)) or 0) < req:
                out.append(x)
        except (TypeError, ValueError):
            out.append(x)
    return out


def outdated_artifacts(rd, video):
    """Every artifact the latest meaningful direction change left behind (made for an earlier direction, neither
    updated since nor reapproved): the plan files and the media made from them."""
    n = int(video)
    lock = read_json(video_dir(rd, n) / 'direction-lock.json')
    names = set(stale_files(rd, n))
    vl = read_json(artifact_path(rd, n, 'voice'))
    if vl and not media_current(lock, 'voice', vl.get('production_rev')):
        names.add('voice')
    if narration_outdated_parts(lock, read_json(artifact_path(rd, n, 'narration'))):
        names.add('narration')
    for kind, key in (('stills', 'images'), ('music', 'tracks')):
        recs = (read_json(artifact_path(rd, n, kind)).get(key) or {}).values()
        if any(not media_current(lock, kind, r.get('production_rev')) for r in recs):
            names.add(kind)
    plan = read_json(artifact_path(rd, n, 'edit'))
    if plan and not media_current(lock, 'edit', (plan.get('direction') or {}).get('production_rev')):
        names.add('edit')
    return [a for a in ALL_ARTIFACTS if a in names]


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


STILL_PURPOSES = ('shots', 'treatment_preview', 'thumbnail')


def media_gate(job, kind):
    """What every generation worker runs before it makes anything (stills: image_worker.py, openai_images_worker.py;
    music: music_worker.py), and `media-check` runs by hand. A job names its run and video. Stills for the film
    (purpose "shots", the default) each name a shot of the checked shot plan, and the prompt carries that shot's
    approved frame_prompt word for word (style words may be added around it); a music track names the beats it
    scores. Refused while the direction, the beat map or the shot plan fails its check or was made for an earlier
    direction. Two other purposes for stills: "treatment_preview" (before the lock: each item names a treatment and
    a sample moment and carries that sample's picture) and "thumbnail" (the locked, current direction only).
    Returns the records to keep and, for the agent writing the prompts or captions, the direction each item
    carries out: the beat's intent and the locked treatment's visual language or sound."""
    out = {'ok': False, 'issues': [], 'warnings': [], 'records': [], 'run': None, 'video': None,
           'untracked': False, 'direction': {}}
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
    purpose = str(job.get('purpose') or 'shots') if kind == 'stills' else 'music'
    if kind == 'stills' and purpose not in STILL_PURPOSES:
        iss.append('job_purpose_must_be:' + '/'.join(STILL_PURPOSES))
        return out
    if purpose == 'treatment_preview':
        out['untracked'] = True
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
    rev, treatment = lock.get('production_rev', 1), lock.get('treatment')
    chosen = chosen_treatment_of(read_json(video_dir(rd, n) / 'direction.json'))
    if purpose == 'thumbnail':
        out['untracked'] = True
        for i, it in enumerate(items, 1):
            if n_words(it.get('prompt')) < 8:
                iss.append(f'item_{i}_missing_prompt')
        out['direction'] = {'treatment': treatment, 'visual_language': chosen.get('visual_language')}
        out['ok'] = not iss
        return out
    iss += beat_map_facts(rd, n)
    iss += list(stale_files(rd, n, ('beat-map',)).values())
    beats = {str(b.get('id')): b for b in read_json(video_dir(rd, n) / 'beat-map.json').get('beats') or []}
    if kind == 'stills':
        sf = shot_facts(rd, n)
        iss += sf['issues']
        out['warnings'] += sf['warnings']
        shots = {str(s.get('id')): s for s in read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []}
        out['direction'] = {'treatment': treatment, 'visual_language': chosen.get('visual_language'), 'items': []}
        for i, it in enumerate(items, 1):
            s = shots.get(str(it.get('shot_id') or it.get('id') or ''))
            if not s:
                iss.append(f'item_{i}_must_name_a_shot_of_the_shot_plan')
                continue
            if s.get('reuses'):
                iss.append(f'item_{i}_shot_{s.get("id")}_is_a_callback_of_{s.get("reuses")}_nothing_to_generate')
                continue
            fp = _norm(s.get('frame_prompt') or s.get('prompt'))
            if not fp or fp not in _norm(it.get('prompt')):
                iss.append(f'item_{i}_prompt_does_not_carry_shot_{s.get("id")}_frame_prompt')
            b = beats.get(str(s.get('beat_id'))) or {}
            out['direction']['items'].append({'shot_id': str(s.get('id')), 'beat_id': str(s.get('beat_id')),
                                              'new_thing': s.get('new_thing'), 'visual_intent': b.get('visual_intent'),
                                              'experience': b.get('experience')})
            out['records'].append({'shot_id': str(s.get('id')), 'beat_id': str(s.get('beat_id')),
                                   'frame_prompt_sha256': hashlib.sha256(fp.encode('utf-8')).hexdigest(),
                                   'production_rev': rev, 'treatment': treatment})
    else:
        out['direction'] = {'treatment': treatment, 'sound': chosen.get('sound'), 'items': []}
        for i, it in enumerate(items, 1):
            bs = [str(x) for x in it.get('beats') or []]
            if not bs or any(b not in beats for b in bs):
                iss.append(f'track_{i}_must_name_beats_of_the_beat_map')
            if str(it.get('video', n)) != str(n):
                iss.append(f'track_{i}_is_for_another_video')
            if n_words(it.get('caption')) < 3:
                iss.append(f'track_{i}_missing_caption')
            out['direction']['items'].append({'beats': {b: {k: (beats.get(b) or {}).get(k) for k in
                                                            ('sound_direction', 'experience', 'pace')} for b in bs}})
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
        data[key][_pkey(e['out'])] = {**{k: v for k, v in e.items() if k != 'out'}, 'made_at': now()}
    write_json(p, data)
    return str(p)


def stills_facts(rd, video):
    """Every shot has a still made through the gate, from its current approved prompt, under the current direction
    (or the director explicitly reapproved the stills for this revision, e.g. user-supplied or drawn pictures). A
    shot that `reuses` an earlier shot (a deliberate callback) shows that shot's still."""
    n = int(video)
    lock = read_json(video_dir(rd, n) / 'direction-lock.json')
    shots = read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []
    by_id = {str(s.get('id')): s for s in shots}
    prov = read_json(artifact_path(rd, n, 'stills')).get('images') or {}
    by_shot = {}
    for path, rec in prov.items():
        if Path(path).is_file():
            by_shot.setdefault(str(rec.get('shot_id')), []).append((str(rec.get('made_at') or ''), rec))
    missing, changed, older = [], [], []
    for s in shots:
        sid = str(s.get('id'))
        src = by_id.get(str(s.get('reuses') or sid)) or s
        recs = sorted(by_shot.get(str(src.get('id'))) or [], key=lambda x: x[0])
        if not recs:
            missing.append(sid)
            continue
        rec = recs[-1][1]
        fp = hashlib.sha256(_norm(src.get('frame_prompt') or src.get('prompt')).encode('utf-8')).hexdigest()
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


HOLDS_SMALL_CHANGE = (2, 5.0, 0.005)   # lines, seconds, share of the runtime: a hold tweak after a read, not a new film


def holds_changed(seen, now_holds):
    """Realised pauses added, removed or changed by half a second or more since a reader saw them: (lines, seconds)."""
    changed, moved = [], 0.0
    for lid in dict.fromkeys(list(seen) + list(now_holds)):
        a, b = seen.get(lid), now_holds.get(lid)
        sa, sb = (float(a[0]) if a else 0.0), (float(b[0]) if b else 0.0)
        if (a is None) != (b is None) or abs(sa - sb) >= 0.5 or (a and b and a[1] != b[1]):
            changed.append(lid)
            moved += abs(sa - sb)
    return changed, round(moved, 2)


def review_state(vd, kind, current_sha, snapshot=None, holds=None):
    """Where one review kind stands for the current version: every round's findings sealed and answered,
    'revised' answers backed by real changes, a fresh read after major findings (until the round cap), and the
    last read still describing what exists now (for a script, its held silences too). Issues block; warnings are
    shown and kept for the release sheet."""
    recs = review_records(vd, kind)
    st = {'kind': kind, 'rounds': len(recs), 'issues': [], 'warnings': [], 'majors_closed_by_decision': []}
    if not recs:
        st['issues'].append(f'{kind}_review_missing')
        return st
    if kind == 'script' and holds is not None:
        seen = recs[-1][0].get('holds_snapshot')
        if seen is None:
            if holds:
                st['warnings'].append('the last script read was made before holds were shown to readers: it did not '
                                      'see the held silences')
        else:
            ch, moved = holds_changed(seen, holds)
            if ch:
                lim_lines, lim_s, lim_share = HOLDS_SMALL_CHANGE
                target = read_json(vd / 'length-lock.json').get('target_length_s') or 0
                if len(ch) <= lim_lines and moved <= max(lim_s, lim_share * target):
                    st['warnings'].append(f'held silences changed after the last read on {len(ch)} line(s), '
                                          f'{moved:g} s in all (small enough to pass): ' + ','.join(ch))
                else:
                    st['issues'].append(f'holds_changed_after_the_script_read:{moved:g}s:' + ','.join(ch[:12])
                                        + ('...' if len(ch) > 12 else ''))
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
    # Delivery devices a listener counts without meaning to: questions in a row, exclamations, words in capitals
    # (read as emphasis), and how often the text directs the voice. Information only: the treatment decides.
    qruns, cur = [], []
    for lid, s, _ in sents:
        if s.endswith('?'):
            cur.append(lid)
        else:
            if len(cur) >= 2:
                qruns.append(cur)
            cur = []
    if len(cur) >= 2:
        qruns.append(cur)
    out['question_runs'] = [{'from': r[0], 'to': r[-1], 'questions': len(r)} for r in qruns][:12]
    out['exclamations'] = sum(1 for _, s, _ in sents if s.endswith('!'))
    caps = [(str(r.get('id') or f'L{i + 1:03d}'), w) for i, r in enumerate(lines)
            for w in re.findall(r'\b[A-Z]{4,}\b', strip_tags(r.get('text') or ''))]
    out['capitalised_words'] = {'count': len(caps), 'examples': [f'{a}:{b}' for a, b in caps[:8]]}
    tag_lines = [(str(r.get('id') or f'L{i + 1:03d}'), m.group(0)) for i, r in enumerate(lines)
                 for m in TAG_RE.finditer(str(r.get('text') or ''))]
    spoken = sum(len(t) for _, _, t in sents) or 1
    out['delivery_tags'] = {'count': len(tag_lines), 'per_1000_words': round(1000 * len(tag_lines) / spoken, 1),
                            'pause_tags': sum(1 for _, t in tag_lines if is_pause_tag(t[1:-1])),
                            'examples': [f'{a} {b}' for a, b in tag_lines[:10]]}
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
    used, cursor, earlier = set(), 0, set()
    for s in shots:
        sid = s.get('id')
        if str(s.get('beat_id')) not in beats:
            out['issues'].append(f'shot_{sid}_beat_not_in_beat_map')
        else:
            used.add(str(s.get('beat_id')))
        if n_words(s.get('new_thing')) < 4:
            out['issues'].append(f'shot_{sid}_missing_new_thing')
        if s.get('reuses') and str(s.get('reuses')) not in earlier:
            out['issues'].append(f'shot_{sid}_reuses_no_earlier_shot')   # a callback shows an earlier shot's still
        elif n_words(s.get('frame_prompt') or s.get('prompt')) < 8 and not s.get('reuses'):
            out['issues'].append(f'shot_{sid}_missing_frame_prompt')
        earlier.add(str(sid))
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


# ---------------------------------------------------------------- the episode's narrator (voice lock)
# Each video chooses its own narrator for its locked treatment (voice-pick writes 60-voice/video-NN/voice-lock.json);
# videos of a series may share one voice on purpose. Every recording of the video follows its lock: voice, model and
# settings. A video recorded before episodes had their own lock keeps the run's older one (60-voice/voice-lock.json).
VOICE_SETTING_KEYS = ('stability', 'similarity_boost')


def voice_lock_path(rd, video):
    return rd / '60-voice' / f'video-{int(video):02d}' / 'voice-lock.json'


def voice_lock(rd, video):
    """(lock, legacy): this video's own voice lock, or the run's older one for a video recorded before."""
    own = read_json(voice_lock_path(rd, video))
    if own:
        return own, False
    old = read_json(rd / '60-voice' / 'voice-lock.json')
    return old, bool(old)


def narrator_sha(direction):
    t = chosen_treatment_of(direction)
    return canonical_sha({k: t.get(k) for k in ('narrator', 'writing_voice')}) if t else None


def voice_settings_issues(settings):
    """Eleven v4 / v4 Turbo apply exactly two voice settings, stability and similarity (ElevenLabs' v4 docs: no style,
    no speed, no SSML); both are chosen, never left to the account default."""
    if not isinstance(settings, dict) or not settings:
        return ['voice_settings_missing']
    out = [f'voice_setting_not_applied_by_eleven_v4:{k}' for k in settings if k not in VOICE_SETTING_KEYS]
    for k in VOICE_SETTING_KEYS:
        v = settings.get(k)
        if v is None:
            out.append(f'voice_setting_missing:{k}')
        elif isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= float(v) <= 1:
            out.append(f'voice_setting_out_of_range:{k}')
    return out


def voice_facts(rd, video, voice_id=None, model_id=None, settings=None):
    """What this video's recording must use: its voice lock, current for the locked direction. A voice, model or
    settings given on a command line must be exactly the locked ones (conflicts); a change is a deliberate revision
    (voice-pick --replace with a reason), never an override."""
    vl, legacy = voice_lock(rd, video)
    out = {'issues': [], 'warnings': [], 'conflicts': [], 'legacy': legacy, 'lock': vl,
           'voice_id': vl.get('voice_id'), 'model_id': vl.get('model_id') or 'eleven_v4',
           'settings': vl.get('settings') or {}, 'voice_rev': vl.get('voice_rev', 1) if vl else None}
    if not vl:
        out['issues'].append('voice_lock_missing')
        return out
    if voice_id and voice_id != out['voice_id']:
        out['conflicts'].append('voice_id_differs_from_the_episode_voice_lock')
    if model_id and model_id != out['model_id']:
        out['conflicts'].append('model_differs_from_the_episode_voice_lock')
    if settings is not None and settings != out['settings']:
        out['conflicts'].append('voice_settings_differ_from_the_episode_voice_lock')
    out['issues'] += voice_settings_issues(out['settings'])
    if out['model_id'] not in TTS_MODELS:
        out['issues'].append('voice_lock_model_not_allowed')
    if legacy:
        out['warnings'].append('this video records with the run\'s older voice lock (made before each video chose its '
                               'own narrator); choosing a narrator for it now goes through voice-pick')
    else:
        dlock = read_json(video_dir(rd, video) / 'direction-lock.json')
        if dlock and not media_current(dlock, 'voice', vl.get('production_rev')):
            out['issues'].append('voice_made_for_an_earlier_direction')
        if n_words(vl.get('reason')) < MIN_NOTE_WORDS:
            out['issues'].append('voice_lock_without_its_reason')
    return out


def _measured_matches(m, voice_id, model_id, settings):
    return bool(m and m.get('wpm') and m.get('per_line_overhead_s') is not None and (m.get('words') or 0) >= 300
                and m.get('voice_id') == voice_id and (m.get('model_id') or 'eleven_v4') == (model_id or 'eleven_v4')
                and (m.get('settings') or {}) == (settings or {}))


def voice_measurement(rd, video=None):
    """The real measured pace and natural per-line gap of the voice this video records with (narration-measure writes
    it): from this video's voice lock, else from another episode of the run locked to the same voice, model and settings
    (a series voice keeps its calibration), else from the run's older lock. Empty until a real part of 300+ words of
    that exact voice setup has been measured."""
    if video is None:
        vl, legacy = read_json(rd / '60-voice' / 'voice-lock.json'), True
    else:
        vl, legacy = voice_lock(rd, video)
    want = (vl.get('voice_id'), vl.get('model_id') or 'eleven_v4', vl.get('settings') or {})
    m = vl.get('measured') or {}
    if _measured_matches(m, *want):
        return m
    if vl and not legacy:
        for other in sorted((rd / '60-voice').glob('video-*/voice-lock.json')):
            om = read_json(other).get('measured') or {}
            if other != voice_lock_path(rd, video) and _measured_matches(om, *want):
                return {**om, 'source': f'measured on {other.parent.name}: same voice, model and settings'}
        om = read_json(rd / '60-voice' / 'voice-lock.json').get('measured') or {}
        if _measured_matches(om, *want):
            return {**om, 'source': 'measured under the run\'s older voice lock: same voice, model and settings'}
    if legacy and vl.get('measured_wpm') and vl.get('measured_overhead_s') and vl.get('measured_overhead_lines'):
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


PACE_DEFINITIONS = {
    'active_wpm': 'words over the time Whisper marks as speech (pauses between its speech segments left out): how fast '
                  'the narrator talks while talking. The voice is measured the same way (narration-measure).',
    'overall_wpm': 'words over the time from the first word to the last, every pause included: how many words a '
                   'minute of the narration really holds. The script\'s word budget comes from this one.',
    'runtime_wpm': 'words over the whole video, intro and outro included.',
    'pause_share': 'the share of the speaking span that is silence between words.'}


def sentence_cadence(texts):
    """Words per sentence (median, 90th percentile) and sentences, from transcript or script text."""
    sents = [len(re.findall(r"[\w']+", s)) for t in texts for s in re.split(r'(?<=[.!?…])\s+', strip_tags(t))]
    sents = sorted(x for x in sents if x)
    if not sents:
        return {}
    return {'sentences': len(sents), 'sentence_words_median': sents[len(sents) // 2],
            'sentence_words_p90': sents[min(len(sents) - 1, int(0.9 * len(sents)))]}


def ref_pace_stats(rd, vid, duration_s=None):
    """One reference narrator on the pipeline's yardsticks (PACE_DEFINITIONS): the same transcribe() output the
    references and this run's narration are both measured from."""
    media = rd / '10-media' / vid
    tfile = media / 'transcript.txt'
    if not tfile.exists():
        return {}
    raw = tfile.read_text(encoding='utf-8', errors='replace')
    words, speech = transcript_speech(raw)
    tj = read_json(media / 'transcript.json')
    ws = transcript_words(tj)
    span = (ws[-1]['end_s'] - ws[0]['start_s']) if len(ws) > 1 else 0.0
    out = {'words': words, 'speech_s': round(speech, 1), 'span_s': round(span, 1),
           'active_wpm': round(words / (speech / 60)) if speech else None,
           'overall_wpm': round(words / (span / 60)) if span else None,
           'pause_share': round(max(0.0, 1 - speech / span), 3) if span and speech else None,
           **sentence_cadence([s.get('text') or '' for s in tj.get('segments') or []])}
    if duration_s:
        out['duration_s'] = round(float(duration_s), 1)
        out['runtime_wpm'] = round(words / (float(duration_s) / 60))
    return out


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
    # What reaches the voice: no markup it can't take, no directions that fight each other, and the pronunciation
    # list in the form v4 documents (it changes only what is sent; the canonical text stays for the captions).
    markup_issues, markup_warnings = script_markup(lines)
    issues += markup_issues
    pron = pronunciation_facts(rd, video, lines)
    issues += pron['issues']
    holds = round(sum(p['pause_after_s'] for p in pause_plan if p['via'] == 'edit'), 2)
    review = vd / 'editorial-review.md'
    review_text = review.read_text(encoding='utf-8', errors='replace') if review.exists() else ''
    flags, flag_issues = content_flags(lines, review_text)
    issues += flag_issues
    # Every kept tag says why this moment needs it, under "Delivery and tags" (03, 05): selective, not decorative.
    explained = delivery_review_lines(review_text)
    issues += [f'tag_{lid}_not_explained_under_delivery_and_tags'
               for lid in sorted({t['line'] for t in tags}) if lid not in explained]
    warnings = list(markup_warnings) + pron['warnings']
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
    seen = (dlock.get('reviewed_treatments') or {}).get(str(dfacts.get('chosen_treatment')))
    if seen is not None:
        now_text = treatment_text(chosen_treatment_of(read_json(vd / 'direction.json')))
        if now_text != seen:
            share = _jaccard(_content_tokens(seen), _content_tokens(now_text))
            warnings.append(f'the chosen treatment was refined after its blind read ({share:.0%} of its vocabulary is '
                            'still what the reader saw)')
    snapshot ={str(r.get('id') or f'L{i + 1:03d}'): str(r.get('text') or '') for i, r in enumerate(lines)}
    script_review = review_state(vd, 'script', script_hash(lines), snapshot, holds=hold_snapshot(lines)) if lines else \
        {'issues': ['script_review_missing'], 'warnings': [], 'rounds': 0}
    issues += script_review['issues']
    warnings += script_review['warnings']
    measured = voice_measurement(rd, video)
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
    # Held silence never stands in for story. The length check above counts the holds; this shows how much of the
    # locked runtime the words alone fill, next to how the comparable narrators pause. When holds carry runtime, the
    # cold reader has seen every one (review-packet shows them; a later change to them needs a new read).
    band = max(4, target * lock.get('tolerance_export_pct', .025)) if real is not None else max(10, .08 * target)
    content_s = real_narr if real_narr is not None else (round(early_narr, 2) if pace else None)
    carried = round(max(0.0, (target - band) - content_s), 1) if content_s is not None else None
    ref_pp = [p for p in (lock.get('reference_pause_profiles') or {}).values() if p]
    edit_holds = [p for p in pause_plan if p['via'] == 'edit']
    holds_info = {'edit_holds': len(edit_holds), 'edit_holds_s': holds,
                  'tag_pauses': sum(1 for p in pause_plan if p['via'] == 'tag'),
                  'share_of_runtime': round(holds / target, 3) if target else None,
                  'content_forecast_s': content_s, 'runtime_carried_by_holds_s': carried,
                  'longest_hold_s': max((p['pause_after_s'] for p in edit_holds), default=0),
                  'references_longest_pause_s': max((p.get('longest_pause_s') or 0 for p in ref_pp), default=None),
                  'references_pauses_1_5s_plus_per_min': round(statistics.mean(
                      [p['pauses_1_5s_plus_per_min'] for p in ref_pp if p.get('pauses_1_5s_plus_per_min') is not None]), 2)
                  if any(p.get('pauses_1_5s_plus_per_min') is not None for p in ref_pp) else None}
    if carried:
        warnings.append(f'{carried:.0f} s of the locked runtime is carried by held silence ({holds:.0f} s of edit holds '
                        f'in {len(edit_holds)} places): each one has to earn its moment, and the cold reader is shown them all')
    pp = lock.get('pace_profile') or {}
    density = {'script_words': words, 'words_per_runtime_minute': round(words / (target / 60)) if target else None,
               'references_overall_wpm': pp.get('overall_wpm'), 'references_runtime_wpm': pp.get('runtime_wpm'),
               'target_words': lock.get('target_words')}
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
            'pace_sources': {'references_wpm': lock.get('pace_wpm'), 'references_overall_wpm': pp.get('overall_wpm'),
                             'script_wpm': script.get('pace_wpm'), 'voice_measured_wpm': measured.get('wpm'),
                             'voice_overall_wpm': measured.get('overall_wpm'),
                             'voice_per_line_gap_s': round(measured['per_line_overhead_s'], 3) if measured else None},
            'audio_tags': tags, 'tag_time_s': tag_s, 'pause_plan': pause_plan, 'edit_holds_s': holds,
            'holds': holds_info, 'density': density,
            'pronunciation': {'file': pron['file'], 'terms': [{k: t[k] for k in ('term', 'say', 'how', 'confidence')}
                                                              | {'lines': len(pron['uses'].get(t['term']) or [])}
                                                              for t in pron['terms']]},
            'content_flags': flags, 'numbers_without_claim': numbers_without_claim,
            'creative': {'direction_locked': bool(dlock), 'locked_late': bool(dlock.get('late_reason')),
                         'treatment': dfacts.get('chosen_treatment'), 'production_rev': dlock.get('production_rev'),
                         'outdated': outdated_artifacts(rd, video), 'script_review_rounds': script_review['rounds'],
                         'majors_closed_by_decision': script_review.get('majors_closed_by_decision') or []},
            'writing_signals': writing_signals(lines, lock.get('language') or script.get('language') or 'en'),
            'forecast_s': forecast, 'real_narration_forecast_s': real_narr, 'real_forecast_s': real,
            'locked_target_s': target,
            'export_window_s': [round(target - max(4, target * lock.get('tolerance_export_pct', .025)), 2),
                                round(target + max(4, target * lock.get('tolerance_export_pct', .025)), 2)],
            'target_words_without_pauses': round(target * pace / 60) if pace else None,
            'target_words_with_reference_pauses': lock.get('target_words')}


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
    # GET /v1/models, 2026-11-19, and ElevenLabs' v4 migration guide: eleven_v4 and eleven_v4_turbo take 10,000
    # characters per request. model_rates() reads the live maximum_text_length_per_request before any paid request.
    known = {'eleven_v4': 10000, 'eleven_v4_turbo': 10000}
    return known.get(model, 3000)


# ---------------------------------------------------------------- parts that follow the story
PART_TARGET_CHARS = 3500     # an engineering guideline for one request, not a rule
PART_SOFT_MAX = 1.5          # a whole beat may run to this multiple of the target before it is split


def _split_long_beat(lines, sizes, lo, hi, target, hard_max):
    """One beat too long for one part, cut between lines into pieces of about `target` characters: at each even
    split, the nearby line end (within a quarter of the target) after which the story already breathes (a planned
    pause), else the nearest line end. Never inside a line, never above hard_max."""
    total = sum(sizes[lo - 1:hi])
    k = max(2, math.ceil(total / target))
    ends, acc = [], 0
    for j in range(lo, hi + 1):
        acc += sizes[j - 1]
        ends.append((j, acc))
    pieces, start = [], lo
    for q in range(1, k):
        goal = total * q / k
        options = [(j, c) for j, c in ends if start <= j < hi]
        if not options:
            break
        near = [x for x in options if abs(x[1] - goal) <= 0.25 * target] or \
            [min(options, key=lambda x: abs(x[1] - goal))]
        j = max(near, key=lambda x: (float(lines[x[0] - 1].get('pause_after_s') or 0) > NATURAL_PAUSE_MAX_S,
                                     float(lines[x[0] - 1].get('pause_after_s') or 0) > 0, -abs(x[1] - goal)))[0]
        pieces.append((start, j))
        start = j + 1
    pieces.append((start, hi))
    out = []
    for a, z in pieces:
        while z > a and sum(sizes[a - 1:z]) > hard_max:
            m, acc = a, sizes[a - 1]
            while m + 1 <= z and acc + sizes[m] <= hard_max:
                acc += sizes[m]
                m += 1
            out.append((a, m))
            a = m + 1
        if a <= z:
            out.append((a, z))
    return out


def chunks_for_beats(lines, beats, target=PART_TARGET_CHARS, hard_max=10000):
    """Parts that follow the story: whole beats, short neighbouring beats together up to about `target` characters, a
    beat longer than PART_SOFT_MAX x target split between lines where it already breathes. A join falls where the
    story turns, re-recording an edited line costs about one beat, and the calibration part is the opening. Never
    inside a line, never above hard_max; plain line packing when the beat map doesn't cover the script."""
    for i, row in enumerate(lines, 1):
        if len(str(row['text']).strip()) > hard_max:
            error('One script line exceeds safe TTS request size: split it into complete sentences.',
                  {'line': i, 'chars': len(str(row['text']).strip())})
    n = len(lines)
    sizes = [len(str(r['text']).strip()) + 1 for r in lines]
    spans, cursor = [], 0
    for b in beats or []:
        try:
            lo, hi = int(b['line_start']), int(b['line_end'])
        except (KeyError, TypeError, ValueError):
            spans = []
            break
        if lo != cursor + 1 or hi < lo or hi > n:
            spans = []
            break
        spans.append((lo, hi, str(b.get('id'))))
        cursor = hi
    if not spans or cursor != n:
        return [{**c, 'beats': []} for c in chunks_for_lines(lines, max([target] + sizes))]
    units = []
    for lo, hi, bid in spans:
        if sum(sizes[lo - 1:hi]) > target * PART_SOFT_MAX:
            units += [(a, z, bid) for a, z in _split_long_beat(lines, sizes, lo, hi, target, hard_max)]
        else:
            units.append((lo, hi, bid))
    parts = []
    for a, z, bid in units:
        c = sum(sizes[a - 1:z])
        if parts and parts[-1]['chars'] + c <= min(target * 1.1, hard_max):
            p = parts[-1]
            p['hi'], p['chars'] = z, p['chars'] + c
            if bid not in p['beats']:
                p['beats'].append(bid)
        else:
            parts.append({'lo': a, 'hi': z, 'chars': c, 'beats': [bid]})
    if len(parts) > 1 and parts[-1]['chars'] < 0.35 * target and \
            parts[-2]['chars'] + parts[-1]['chars'] <= min(target * PART_SOFT_MAX, hard_max):
        last = parts.pop()
        parts[-1]['hi'] = last['hi']
        parts[-1]['chars'] += last['chars']
        parts[-1]['beats'] += [b for b in last['beats'] if b not in parts[-1]['beats']]
    return [{'line_start': p['lo'], 'line_end': p['hi'], 'beats': p['beats'],
             'text': '\n'.join(str(r['text']).strip() for r in lines[p['lo'] - 1:p['hi']])} for p in parts]


def context_text(sent_lines, start, step, limit=500):
    """Whole neighbouring lines, spoken words only (their tags removed: those directed the other part), up to about
    `limit` characters, walking from line `start` (1-based) by `step`: -1 for what the previous part ended with, +1
    for what the next one starts with. Sent as previous_text / next_text, which ElevenLabs documents for continuity
    when generations are joined."""
    out, total, i = [], 0, start
    while 1 <= i <= len(sent_lines) and total < limit:
        t = strip_tags(sent_lines[i - 1])
        if t:
            out.append(t)
            total += len(t) + 1
        i += step
    if step < 0:
        out.reverse()
    return '\n'.join(out)


def language_code(language):
    """Eleven v4's language_code: ISO 639-1 for most languages, ISO 639-3 for the few without one ('fil', 'yue')."""
    code = re.split(r'[-_]', str(language or '').strip().lower())[0]
    return code if re.fullmatch(r'[a-z]{2,3}', code) else None


def voice_calibrated(rd, video, voice_id, model_id, settings):
    """True when this exact voice, model and settings has a real measured pace from a part of 300+ words."""
    m = voice_measurement(rd, video)
    if not m:
        return False
    if m.get('source') == 'hand-recorded (older run)':
        return m.get('voice_id') == voice_id and (m.get('settings') or {}) == (settings or {})
    return _measured_matches(m, voice_id, model_id, settings)


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


# ---------------------------------------------------------------- what ElevenLabs costs, and what it really billed
# ElevenLabs documents a per-model credit multiplier (GET /v1/models: model_rates.character_cost_multiplier, times
# cost_discount_multiplier) and the live allowance (GET /v1/user/subscription: character_limit - character_count, both
# free). It does not document whether tags, spaces, line breaks or previous_text/next_text are billed, so a request's
# characters are counted as its whole `text` (tags and line breaks included, context excluded), and every billed request
# is written to RUN/logs/elevenlabs-ledger.jsonl with the balance just before and just after it: the real cost, measured.
def ledger_path(rd):
    return rd / 'logs' / 'elevenlabs-ledger.jsonl'


def ledger_add(rd, entry):
    p = ledger_path(rd)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def ledger_rows(rd):
    p = ledger_path(rd)
    rows = []
    if p.is_file():
        for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def measured_cost_ratio(rd, model_id):
    """Credits this account was really billed per character sent on this model, from the ledger (other use of the
    account between the two balance reads can only push it up): (median, number of requests)."""
    ratios = [r['delta'] / r['characters'] for r in ledger_rows(rd)
              if r.get('model_id') == model_id and r.get('kind') in ('tts', 'probe', 'trial') and r.get('ok')
              and isinstance(r.get('delta'), (int, float)) and r['delta'] >= 0 and r.get('characters')]
    return (round(statistics.median(ratios), 3), len(ratios)) if ratios else (None, 0)


def subscription_balance(key):
    """The live allowance (GET /v1/user/subscription, free): credits left = character_limit - character_count. An
    overage the plan may allow is never counted as available."""
    try:
        data = elevenlabs_request('GET', '/v1/user/subscription', key, timeout=20)
        used, limit = int(data['character_count']), int(data['character_limit'])
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(f'cannot read the ElevenLabs balance (nothing was sent): {type(exc).__name__}: {str(exc)[:160]}')
    return {'available': limit - used, 'used': used, 'limit': limit, 'status': data.get('status'),
            'next_reset_unix': data.get('next_character_count_reset_unix'),
            'overage_possible': bool(data.get('can_extend_character_limit'))}


def model_rates(rd, key, model_id, max_age_h=24):
    """What ElevenLabs reports for this model (GET /v1/models, free): credits per character (character_cost_multiplier
    times cost_discount_multiplier), the longest text one request takes, its setting flags. Cached in RUN/logs for a
    day. A model the account doesn't list, or one without a reported cost, stops everything before a paid call."""
    cache = rd / 'logs' / 'elevenlabs-models.json'
    c = read_json(cache)
    try:
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(c['fetched_at'])).total_seconds()
    except (KeyError, TypeError, ValueError):
        age = None
    if age is None or age > max_age_h * 3600 or model_id not in (c.get('models') or {}):
        try:
            data = elevenlabs_request('GET', '/v1/models', key, timeout=30)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise RuntimeError(f'cannot read the model list (nothing was sent): {type(exc).__name__}: {str(exc)[:160]}')
        models = {m['model_id']: {k: m.get(k) for k in ('model_rates', 'maximum_text_length_per_request', 'can_use_style',
                                                         'can_use_speaker_boost', 'can_do_text_to_speech')}
                  for m in (data if isinstance(data, list) else []) if isinstance(m, dict) and m.get('model_id')}
        c = {'fetched_at': now(), 'models': models}
        write_json(cache, c)
    m = (c.get('models') or {}).get(model_id)
    if not m:
        raise RuntimeError(f'ElevenLabs does not list {model_id} for this account (nothing was sent)')
    rates = m.get('model_rates') or {}
    if rates.get('character_cost_multiplier') is None:
        raise RuntimeError(f'ElevenLabs reported no character_cost_multiplier for {model_id} (nothing was sent)')
    per_char = float(rates['character_cost_multiplier']) * float(rates.get('cost_discount_multiplier') or 1)
    return {'model_id': model_id, 'credits_per_character': round(per_char, 4),
            'character_cost_multiplier': rates.get('character_cost_multiplier'),
            'cost_discount_multiplier': rates.get('cost_discount_multiplier'),
            'maximum_text_length_per_request': m.get('maximum_text_length_per_request'),
            'can_use_style': m.get('can_use_style'), 'can_use_speaker_boost': m.get('can_use_speaker_boost'),
            'fetched_at': c.get('fetched_at')}


def cached_model_rates(rd, model_id):
    """The last model rates read for this run (no network), for a dry run's estimate."""
    m = (read_json(rd / 'logs' / 'elevenlabs-models.json').get('models') or {}).get(model_id) or {}
    r = m.get('model_rates') or {}
    if r.get('character_cost_multiplier') is None:
        return None
    return round(float(r['character_cost_multiplier']) * float(r.get('cost_discount_multiplier') or 1), 4)


def credit_preflight(rd, key, model_id, characters, safety, assume_ratio=None, keep=0, label='this request'):
    """Before any billed request: what the model costs per character (ElevenLabs' own figure, or an explicit,
    recorded --assume-cost-ratio), what this account was really billed so far (the ledger) and the live balance.
    Refuses, with nothing sent, unless the balance covers the expected credits times the safety factor and still
    leaves --keep-credits."""
    rates = model_rates(rd, key, model_id)
    measured, samples = measured_cost_ratio(rd, model_id)
    ratio = float(assume_ratio) if assume_ratio is not None else rates['credits_per_character']
    expected = math.ceil(characters * ratio)
    bal = subscription_balance(key)
    required = math.ceil(expected * safety) + int(keep or 0)
    out = {'characters': characters, 'credits_per_character': ratio,
           'ratio_source': 'assumed (--assume-cost-ratio)' if assume_ratio is not None else 'ElevenLabs model rates',
           'documented_credits_per_character': rates['credits_per_character'],
           'measured_credits_per_character': measured, 'measured_requests': samples,
           'expected_credits': expected, 'safety_factor': safety, 'keep_credits': int(keep or 0),
           'required_available': required, 'available': bal['available'],
           'left_after_expected': bal['available'] - expected, 'next_reset_unix': bal['next_reset_unix'],
           'max_characters_per_request': rates['maximum_text_length_per_request']}
    if bal['available'] < required:
        error(f'Not enough ElevenLabs credits for {label}: nothing was sent.', out)
    return out


def eleven_paid_post(rd, key, path, body, kind, meta, accept='audio/mpeg', timeout=180, require=0):
    """One billed ElevenLabs request, on record: the live balance just before and just after (free calls), the
    characters sent and what the account was billed, appended to the ledger whether it worked or not. When the
    balance just before is under `require`, nothing is sent. Returns (raw bytes or None, error or None, entry)."""
    before = subscription_balance(key)
    entry = {'at': now(), 'kind': kind, **meta, 'characters': len(str(body.get('text') or '')),
             'balance_before': before['available']}
    if before['available'] < require:
        return None, f'not sent: {before["available"]} credits left, this request needs {require}', None
    req = urllib.request.Request('https://api.elevenlabs.io' + path, data=json.dumps(body).encode('utf-8'),
                                 method='POST', headers={'xi-api-key': key, 'Content-Type': 'application/json',
                                                         'Accept': accept})
    raw, err, rid = None, None, None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            hdrs = getattr(resp, 'headers', None)
            rid = hdrs.get('request-id') if hdrs is not None else None
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        err = f'{type(exc).__name__}: {str(exc)[:240]}'
    try:
        after = subscription_balance(key)['available']
    except RuntimeError:
        after = None
    entry.update({'ok': err is None, 'error': err, 'request_id': rid, 'balance_after': after,
                  'delta': (before['available'] - after) if after is not None else None})
    ledger_add(rd, entry)
    return raw, err, entry


def tags_heard(sent_text, heard_text):
    """Delivery tags whose own words Whisper heard more often than the spoken text holds them: most likely read aloud
    ('[softly] Nobody moved.' heard as 'Softly, nobody moved.')."""
    heard, spoken = tokens_of(heard_text), tokens_of(strip_tags(sent_text))
    out = []
    for m in TAG_RE.finditer(sent_text):
        words = [w for w in tokens_of(m.group(1)) if len(w) > 2 and w not in EN_FUNCTION_WORDS]
        if words and sum(1 for w in words if heard.count(w) > spoken.count(w)) * 2 >= len(words):
            out.append(m.group(0))
    return out


def cmd_voice_candidates(args):
    """Suggest up to --count candidate voices (free, from the account's existing voices,
    and/or billed Voice Design previews), save each candidate's preview audio, transcribe
    it (Whisper) and record its preview_wpm with the references' yardstick. A preview is
    short: its pace does not predict the voice's real pace on a full chunk (measured on one
    run: preview 195 -> real 180; a 209 human sample -> 178). Each preview's delivery is
    measured too (pitch range and movement, loudness contrast), because the agents cannot
    listen: they choose for the treatment's narrator from descriptions, transcripts and these
    measurements; the user may listen and overrule. The real pace comes from the calibration part.
    Voice Design is billed (by the characters of its preview text, three voices a call): without --execute this
    only shows what the designs would cost; with --execute the live balance is checked first and every design call
    goes in the spend ledger. Writes a report; picks nothing itself.
    An earlier round's report is kept as candidates-<time>.json, never overwritten."""
    rd, st = run_folder(args)
    vd = video_dir(rd, args.video)
    outdir = rd / '60-voice' / f'video-{int(args.video):02d}' / 'candidates'
    design_n = max(0, args.design)
    free_n = max(0, args.count - design_n)
    text, plan = None, None
    if design_n:
        if not args.design_description:
            error('--design-description is required when --design > 0 '
                  '(the narrator the locked treatment describes: character, register, age, accent, delivery).')
        text = args.design_text
        if not text:
            script = read_json(vd / 'script.json')
            text = ' '.join(strip_tags(l['text']) for l in (script.get('lines') or [])[:8])[:1000]
        if not (100 <= len(text) <= 1000):
            error('Voice Design sample text must be 100-1000 characters.', {'characters': len(text)})
        calls = math.ceil(design_n / 3)
        plan = {'design_calls': calls, 'preview_characters': len(text), 'expected_credits': calls * len(text),
                'reserve_credits': calls * 3 * len(text),
                'how_billed': 'ElevenLabs: Voice Design is charged by the number of characters in its preview text; '
                              'each call makes three voices. Whether the three are billed once or three times is not '
                              'documented, so the reserve assumes three; the ledger records what was really billed.'}
        if not getattr(args, 'execute', False):
            emit({'ok': True, 'mode': 'dry_run_no_charges', 'voice_design': plan,
                  'design_description': args.design_description, 'preview_text': text,
                  'account_voices_requested': free_n,
                  'next': 'Review the cost, then re-run with --execute (the balance is checked before any design call).'})
            return
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    outdir.mkdir(parents=True, exist_ok=True)
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
        bal = subscription_balance(key)
        need = math.ceil(plan['reserve_credits'] * getattr(args, 'credit_safety_factor', 1.15)) + \
            int(getattr(args, 'keep_credits', 0) or 0)
        if bal['available'] < need:
            error('Not enough ElevenLabs credits for these Voice Design calls: nothing was sent.',
                  {**plan, 'available': bal['available'], 'required_available': need})
        made = 0
        while made < design_n:
            raw, err, entry = eleven_paid_post(rd, key, '/v1/text-to-voice/design',
                                               {'voice_description': args.design_description, 'text': text},
                                               'voice_design', {'video': int(args.video), 'model_id': 'voice_design'},
                                               accept='application/json', timeout=120)
            if err:
                error('Voice Design call failed (it may have been billed regardless; see the ledger). '
                      'Verify your ElevenLabs account before retrying.', {'error': err, 'ledger': entry})
            try:
                resp = json.loads(raw or b'{}')
            except ValueError:
                resp = {}
            previews = resp.get('previews') or []
            if not previews:
                error('Voice Design returned no previews.', {k: v for k, v in resp.items() if k != 'previews'})
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
          'voice_design': plan,
          'guidance': 'The agents cannot hear these files. Choose for the chosen treatment\'s narrator (direction.json): '
                      'compare each candidate\'s description and labels, what it said, and its measured delivery '
                      '(pitch range and movement, loudness contrast; a short sample, indicative only) with the '
                      'references\' (20-analysis/av). The files are listed for the user, who may listen and overrule. '
                      'preview_wpm does not predict real pace. Lock the pick with voice-pick; the real pace and '
                      'delivery are measured on the first real part (tts --max-parts 1, then narration-measure).'})


def cmd_voice_pick(args):
    """Choose this video's narrator: an editorial decision made for its locked treatment (the narrator it describes,
    the experience the audience should have, how the comparable narrators deliver), recorded with its reason in
    60-voice/video-NN/voice-lock.json. Every recording of the video then follows that lock: the voice, the model and the
    stability and similarity chosen for this narrator (stability trades consistency between generations against
    expressive range; it is never a pace control: Eleven v4 applies no speed setting, and the real pace is measured,
    not steered). Another video may share the voice for a series identity, or choose its own. Changing a video's
    voice or settings is a deliberate revision (--replace, with a reason); parts recorded with the old setup are then
    re-recorded (tts --rerecord-changed, or --archive-existing for another voice).
    A Voice Design candidate's generated_voice_id is saved to the account library first (POST /v1/text-to-voice)."""
    rd, st = run_folder(args)
    n = int(args.video)
    gate, dlock, dfacts = direction_gate(rd, n)
    if gate:
        error('The narrator is chosen for the locked treatment: lock the creative direction first (direction-lock).',
              gate)
    lockfile = voice_lock_path(rd, n)
    old = read_json(lockfile)
    if old and not args.replace:
        error('This video already has its narrator. A change is deliberate: --replace with a --reason.',
              {'file': str(lockfile)})
    if n_words(args.reason) < MIN_NOTE_WORDS:
        error('Say why this voice and these settings fit the treatment\'s narrator (--reason, a real sentence).')
    settings = parse_voice_settings(args.settings, args.model_id)
    bad = voice_settings_issues(settings)
    if bad:
        error('Choose both settings for this narrator: stability (consistency between generations against expressive '
              'range) and similarity_boost (closeness to the voice), each from 0 to 1.', bad)
    preview_wpm, source, design_description = None, None, None
    vdir = rd / '60-voice' / f'video-{n:02d}'
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
    direction = read_json(video_dir(rd, n) / 'direction.json')
    others = sorted(p.parent.name for p in (rd / '60-voice').glob('video-*/voice-lock.json')
                    if p != lockfile and read_json(p).get('voice_id') == final_voice_id)
    lock = {'video': n, 'voice_id': final_voice_id, 'generated_voice_id': saved_from,
            'name': args.name or old.get('name'), 'model_id': args.model_id, 'settings': settings,
            'reason': args.reason.strip(), 'treatment': dlock.get('treatment'),
            'production_rev': dlock.get('production_rev', 1), 'narrator_sha256': narrator_sha(direction),
            'voice_rev': int(old.get('voice_rev') or 0) + 1, 'same_voice_as': others,
            'preview_wpm': preview_wpm, 'design_description': design_description, 'locked_at': now(),
            'rule': 'Every recording of this video uses exactly this voice, model and settings; a change is '
                    'voice-pick --replace with a reason.',
            'pace_note': 'preview_wpm is a short-sample figure and is never used to size the script; the real '
                         'pace is measured (narration-measure) on the first real part.',
            'history': (old.get('history') or []) + ([{k: old.get(k) for k in (
                'voice_id', 'model_id', 'settings', 'reason', 'voice_rev', 'production_rev', 'locked_at')}] if old else [])}
    m = old.get('measured') or {}
    if _measured_matches(m, final_voice_id, args.model_id, settings):
        lock['measured'] = m   # same voice, model and settings: the real measurement still holds
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    write_json(lockfile, lock)
    recorded = read_json(rd / '50-audio' / f'video-{n:02d}' / 'manifest.json').get('finished_parts') or []
    emit({'ok': True, 'lock_file': str(lockfile), 'voice_id': final_voice_id, 'model_id': args.model_id,
          'settings': settings, 'voice_rev': lock['voice_rev'], 'saved_from_generated_voice_id': saved_from,
          'same_voice_as': others, 'calibrated': bool(voice_measurement(rd, n)),
          'guidance': ('Next: tts --run RUN --video N (a dry run: the parts, their beats, characters and credits), '
                       'then the calibration part (tts --max-parts 1 --execute) and narration-measure. Every '
                       'recording takes the voice, model and settings from this lock. '
                       + ('Parts already recorded with another voice setup are re-recorded before the narration is '
                          'complete (tts --rerecord-changed; another voice: --archive-existing).' if recorded and old else ''))})


def cmd_voice_probe(args):
    """Hear a short real passage, sent exactly as the script would send it (inline tags in place, the pronunciation
    list applied unless --no-pronunciation), via one short billed call: how the voice, the tags and the names SOUND,
    before the paid narration. Voice, model and settings default to this video's voice lock (another voice is probed
    while choosing: --voice-id with --settings). Its WPM is reported but a sample under ~300 words does not predict
    real pace (measured here: short samples read up to 199 WPM, the same voice 175-188 on real parts); the real pace
    comes from the calibration part. Separate from tts's parts; touches no script, lock or 50-audio file."""
    rd, st = run_folder(args)
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    n = int(args.video)
    vd = video_dir(rd, n)
    lock = read_json(vd / 'length-lock.json', required=True)
    vf = voice_facts(rd, n)
    voice_id = args.voice_id or vf['voice_id']
    if not voice_id:
        error('No voice lock for this video yet: give --voice-id and --settings to probe a candidate.')
    model_id = args.model_id or (vf['model_id'] if vf['lock'] else 'eleven_v4')
    settings = parse_voice_settings(args.settings, model_id) if args.settings else \
        (vf['settings'] if vf['lock'] and voice_id == vf['voice_id'] else {})
    bad = voice_settings_issues(settings)
    if bad:
        error('Probe with explicit settings for this narrator (stability and similarity_boost).', bad)
    script = read_json(vd / 'script.json')
    text = args.text
    if not text:
        buf, total = [], 0
        for l in script.get('lines') or []:
            buf.append(l['text'])
            total += len(l['text']) + 1
            if total >= 450:
                break
        text = ' '.join(buf)
    pron = pronunciation_facts(rd, n, script.get('lines') or [])
    sent_text = text if args.no_pronunciation else tts_text(text, pron['terms'])
    mk, _ = script_markup([{'id': 'probe', 'text': sent_text if args.no_pronunciation else text}])
    if mk:
        error('The probe text holds markup the voice can\'t take.', mk)
    limit = model_limit(model_id)
    if len(sent_text) > limit:
        error('Probe text exceeds the model request limit.', {'characters': len(sent_text), 'limit': limit})
    budget = credit_preflight(rd, key, model_id, len(sent_text), args.credit_safety_factor, None,
                              args.keep_credits, 'this probe')
    body = {'text': sent_text, 'model_id': model_id, 'voice_settings': settings}
    if language_code(lock.get('language')):
        body['language_code'] = language_code(lock.get('language'))
    path = '/v1/text-to-speech/' + urllib.parse.quote(voice_id, safe='') + '?output_format=mp3_44100_128'
    raw, err, entry = eleven_paid_post(rd, key, path, body, 'probe',
                                       {'video': n, 'model_id': model_id, 'voice_id': voice_id}, timeout=120)
    if err:
        error('Probe TTS call failed (it may have been billed regardless; see the ledger). '
              'Verify your ElevenLabs account before retrying.', {'error': err, 'ledger': entry})
    if not raw or len(raw) < 1024:
        error('Audio response too short.', {'bytes': len(raw or b'')})
    outdir = rd / '60-voice' / f'video-{n:02d}' / 'probes'
    outdir.mkdir(parents=True, exist_ok=True)
    k = len(list(outdir.glob('probe-*.mp3'))) + 1
    stem = f'probe-{k:02d}-{voice_id[:10]}'
    fname = outdir / f'{stem}.mp3'
    fname.write_bytes(raw)
    tpath = outdir / f'{stem}.json'
    transcribe(fname, tpath, args.whisper_model, args.device, args.compute_type)
    rawtxt = tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace')
    wpm = wpm_from_transcript_raw(rawtxt)
    heard = strip_transcript_timestamps(rawtxt).strip()
    emit({'ok': True, 'file': str(fname), 'voice_id': voice_id, 'model_id': model_id, 'voice_settings': settings,
          'sent_text': sent_text, 'sent_characters': len(sent_text), 'credit_preflight': budget,
          'credits_billed': entry.get('delta'), 'sample_words': count_words(text), 'short_sample_wpm': wpm,
          'references_pace_wpm': lock.get('pace_wpm'),
          'tags_sent': [m.group(0) for m in TAG_RE.finditer(sent_text)],
          'tags_maybe_read_aloud': tags_heard(sent_text, heard), 'heard_text': heard,
          'measured_delivery': measure_file_delivery(fname, tpath),
          'guidance': 'No agent here can hear this file. What stands in: the words heard back (a tag whose words show '
                      'up in heard_text was read aloud; a name heard differently may be mispronounced, or misheard by '
                      'Whisper) and measured_delivery (how the voice moves; a short sample, indicative only), next to '
                      'the treatment\'s narrator and the references. The user may listen to the file. '
                      'short_sample_wpm does not predict the real pace; do not size the script on it.'})


def parse_voice_settings(raw, model_id):
    try:
        voice_settings = json.loads(raw) if raw else {}
    except ValueError as exc:
        error('--settings must be valid JSON (e.g. \'{"stability": 0.7, "similarity_boost": 0.8}\').', str(exc))
    if not isinstance(voice_settings, dict):
        error('--settings must be a JSON object.')
    # ElevenLabs' v4 pages: "Both variants use two voice settings: Stability and Similarity"; "Style and Speed sliders
    # are not available in Eleven v4"; the migration guide: "Eleven v4 doesn't apply voice_settings.speed". The models'
    # own flags (GET /v1/models) agree: can_use_style=false, can_use_speaker_boost=false. Nothing else is sent.
    for k in voice_settings:
        if k not in VOICE_SETTING_KEYS:
            error(f'Model {model_id!r} applies these voice settings only (no speed, style or speaker boost on v4).',
                  {'allowed': list(VOICE_SETTING_KEYS), 'got': k})
    return voice_settings


def part_records_of(manifest):
    """What each finished part was recorded with. A manifest from before parts carried their own record gives its
    top-level voice, model and settings to every finished part, and its canonical text as what was sent."""
    recs = dict(manifest.get('part_records') or {})
    chunks = {str(c.get('id')): c for c in manifest.get('chunks') or []}
    for x in manifest.get('finished_parts') or []:
        k = str(x)
        if k not in recs:
            c = chunks.get(k) or {}
            recs[k] = {'voice_id': manifest.get('voice_id'), 'model_id': manifest.get('model_id'),
                       'settings': manifest.get('voice_settings') or {},
                       'sent_sha256': c.get('sent_sha256') or c.get('text_sha256'), 'legacy': True}
    return recs


def parts_list(raw):
    try:
        return sorted({int(x) for x in str(raw or '').split(',') if x.strip()})
    except ValueError:
        error('--rerecord-parts takes part numbers, e.g. 2 or 2,5.')


def cmd_tts(args):
    """Record this video's narration in parts, following its plan and its voice lock exactly: voice, model and
    settings come from the lock (a different value on the command line is refused; a change is a voice revision).
    Parts follow the beats (about PART_TARGET_CHARS characters, joins where the story already turns). Each part sends
    its lines' canonical text with their tags and the pronunciation list applied, its neighbours' spoken words as
    context. Every finished part records the voice, model, settings, direction revision and the fingerprint of the
    exact text sent; every billed request goes in the spend ledger with the balance before and after. Finished parts
    are never billed again; a part recorded from other text, another pronunciation, another voice setup or an earlier
    direction is re-recorded only with --rerecord-changed, and a part that must be redone after listening only with
    --rerecord-parts N --reason (old takes always kept in superseded/)."""
    rd, st = run_folder(args)
    n = int(args.video)
    chk = plan_facts(rd, n)
    if not chk['ready']:
        error('Plan must pass objective checks before billed audio generation', chk['issues'])
    vd = video_dir(rd, n)
    script = read_json(vd / 'script.json', required=True)
    lines = script['lines']
    lock = read_json(vd / 'length-lock.json', required=True)
    if not (1.0 <= args.credit_safety_factor <= 3.0):
        error('--credit-safety-factor must be from 1.0 to 3.0')
    if args.max_parts is not None and args.max_parts < 1:
        error('--max-parts must be at least 1.')
    if args.assume_cost_ratio is not None and not (0.1 <= args.assume_cost_ratio <= 1.0):
        error('--assume-cost-ratio must be from 0.1 to 1.0: an explicit, recorded override of the credits per '
              'character ElevenLabs reports for the model, for a ratio measured on this account (the ledger).')
    given = parse_voice_settings(args.settings, args.model_id or 'eleven_v4') if args.settings else None
    vf = voice_facts(rd, n, args.voice_id or None, args.model_id or None, given)
    if vf['conflicts']:
        error('The recording follows this video\'s voice lock; another voice, model or settings on the command line is '
              'refused. A deliberate change is a voice revision: voice-pick --replace --reason "...".',
              {'conflicts': vf['conflicts'], 'voice_lock': {k: vf[k] for k in ('voice_id', 'model_id', 'settings')}})
    voice_id = vf['voice_id'] or args.voice_id
    model_id = vf['model_id'] if vf['lock'] else (args.model_id or 'eleven_v4')
    settings = vf['settings'] if vf['lock'] else (given or {})
    pron = pronunciation_facts(rd, n, lines)
    sent_lines = [tts_text(r['text'], pron['terms']) for r in lines]
    hard_max = model_limit(model_id)
    target = args.max_chars or PART_TARGET_CHARS
    narrdir = rd / '50-audio' / f'video-{n:02d}'
    manifest_path = narrdir / 'manifest.json'
    existing = read_json(manifest_path)
    dlock = read_json(vd / 'direction-lock.json')
    beats = read_json(vd / 'beat-map.json').get('beats') or []
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    other_take = bool(existing) and any(existing.get(x) != y for x, y in
                                        (('model_id', model_id), ('voice_id', voice_id), ('language', lock['language'])))
    start_over = other_take or args.rechunk
    if start_over and not args.archive_existing and existing:
        error('The recorded audio uses another voice/model/language, or --rechunk asks for new part boundaries. '
              'Pass --archive-existing to move the whole folder aside (nothing is deleted; every part is re-billed).',
              {'folder': str(narrdir), 'recorded_with': {k: existing.get(k) for k in ('voice_id', 'model_id', 'language')}})
    chunks = None
    if existing.get('chunks') and not start_over:
        chunks = chunks_from_manifest(existing['chunks'], lines)
        if chunks is None:
            error('Lines were added or removed since the parts were recorded, so their boundaries no longer fit. '
                  'Restore the line count, or re-record everything: --rechunk --archive-existing (every part re-billed).')
        for c, old in zip(chunks, existing['chunks']):
            c['beats'] = old.get('beats') or []
    if chunks is None:
        chunks = chunks_for_beats(lines, beats, target, hard_max)
    for c in chunks:
        c['sent'] = '\n'.join(sent_lines[c['line_start'] - 1:c['line_end']])
    for i, c in enumerate(chunks, 1):
        if len(c['sent']) > hard_max:
            error(f'Part {i} is now longer than the model accepts in one request.', {'characters': len(c['sent'])})
    sha = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()
    spec = {'model_id': model_id, 'voice_id': voice_id, 'language': lock['language'],
            'chunks': [{'id': i + 1, 'line_start': c['line_start'], 'line_end': c['line_end'],
                        'beats': c.get('beats') or [], 'text_sha256': sha(c['text']), 'sent_sha256': sha(c['sent']),
                        'file': f'part-{i + 1:03d}.mp3', 'characters': len(c['sent'])}
                       for i, c in enumerate(chunks)]}
    old_chunks = {} if start_over else {c.get('id'): c for c in existing.get('chunks') or []}
    finished_before = [] if start_over else list(existing.get('finished_parts') or [])
    records = {} if start_over else part_records_of(existing)
    changed = [s['id'] for s in spec['chunks'] if s['id'] in finished_before
               and old_chunks.get(s['id'], {}).get('text_sha256') != s['text_sha256']]
    pron_changed = [s['id'] for s in spec['chunks'] if s['id'] in finished_before and s['id'] not in changed
                    and (records.get(str(s['id'])) or {}).get('sent_sha256') != s['sent_sha256']]
    setup = (voice_id, model_id, settings)
    other_setup = [x for x in finished_before if x not in changed and
                   tuple((records.get(str(x)) or {}).get(k) or ({} if k == 'settings' else None)
                         for k in ('voice_id', 'model_id', 'settings')) != setup]
    # Parts recorded before the latest direction change that touched the narrator, unless the narration was
    # reapproved for it (direction-reapprove --artifact narration): re-recorded like changed lines.
    outdated = [] if start_over else [x for x in narration_outdated_parts(dlock, existing) if x in finished_before]
    asked = parts_list(args.rerecord_parts)
    if any(x not in finished_before for x in asked):
        error('--rerecord-parts names parts that are not recorded yet.', {'asked': asked, 'recorded': finished_before})
    redo = sorted(set(changed) | set(pron_changed) | set(other_setup) | set(outdated) | set(asked))
    by_beat = {str(b.get('id')): b for b in beats}
    parts_view = [{'part': s['id'], 'lines': [s['line_start'], s['line_end']], 'characters': s['characters'],
                   'beats': [{'id': b, **{k: (by_beat.get(b) or {}).get(k) for k in ('narration_direction', 'pace')}}
                             for b in s['beats']]} for s in spec['chunks']]
    todo = [s for s in spec['chunks'] if s['id'] not in finished_before or s['id'] in redo]
    if not args.execute:
        per_char = cached_model_rates(rd, model_id)
        chars = sum(s['characters'] for s in todo)
        emit({'ok': True, 'mode': 'dry_run_no_charges', 'video': n, 'parts': len(chunks),
              'characters_total': sum(s['characters'] for s in spec['chunks']),
              'parts_to_record': [s['id'] for s in todo], 'changed_recorded_parts': changed,
              'pronunciation_changed_parts': pron_changed, 'parts_recorded_with_another_voice_setup': other_setup,
              'parts_made_for_an_earlier_direction': outdated, 'parts_asked_to_rerecord': asked,
              'starts_over': start_over, 'characters_to_record': chars,
              'credit_estimate': ({'credits_per_character': per_char, 'expected_credits': math.ceil(chars * per_char),
                                   'basis': 'the model rates last read for this run; --execute reads them again with '
                                            'the live balance'} if per_char is not None else
                                  {'expected_credits': None, 'basis': 'not read yet: --execute reads the model\'s '
                                                                      'credits per character and the live balance first'}),
              'calibrated': voice_calibrated(rd, n, voice_id, model_id, settings),
              'voice': {'voice_id': voice_id, 'model_id': model_id, 'settings': settings,
                        'voice_rev': vf['voice_rev'], 'older_run_level_lock': vf['legacy']},
              'execute_blockers': vf['issues'], 'voice_warnings': vf['warnings'],
              'pronunciation_terms': [t['term'] for t in pron['terms']],
              'model_limit_per_request': hard_max, 'part_target_chars': target, 'parts_view': parts_view,
              'target_length_s': lock['target_length_s'], 'candidate_manifest': spec,
              'next': 'Review the parts, the voice lock and the credits. Re-run with --execute only after approving cost.'})
        return
    if vf['issues']:
        error('This video has no usable voice lock for recording.', {
            'issues': vf['issues'], 'how': 'voice-pick --run RUN --video N --voice-id ID --settings \'{...}\' --reason '
                                           '"..." (after a direction change: --replace, or direction-reapprove '
                                           '--artifact voice)'})
    key = elevenlabs_key()
    if not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    flagged = [x for x in redo if x not in asked]
    if flagged and not args.rerecord_changed:
        error('Recorded parts no longer match what this video would record now: their lines changed, the '
              'pronunciation list changed what they send, they were recorded with another voice setup, or before the '
              'latest direction change to the narrator. Re-record only those parts with --rerecord-changed (their old '
              'takes move to superseded/, never deleted), or, when the recorded voice still serves the locked '
              'treatment after a direction change, keep them with direction-reapprove --artifact narration --reason.',
              {'changed_parts': changed, 'pronunciation_changed_parts': pron_changed,
               'parts_recorded_with_another_voice_setup': other_setup, 'parts_made_for_an_earlier_direction': outdated,
               'characters': sum(s['characters'] for s in spec['chunks'] if s['id'] in flagged)})
    if asked and n_words(args.reason) < MIN_NOTE_WORDS:
        error('Say why these parts are recorded again (--reason): what was heard, or what the checks found.')
    kept = [] if start_over else [x for x in finished_before if x not in redo
                                  and (narrdir / f'part-{x:03d}.mp3').is_file()
                                  and (narrdir / f'part-{x:03d}.mp3').stat().st_size > 1024]
    remaining = [s for s in spec['chunks'] if s['id'] not in kept]
    batch = remaining[:args.max_parts] if args.max_parts else remaining
    if len(batch) > 1 and not args.skip_calibration and not voice_calibrated(rd, n, voice_id, model_id, settings):
        error('Calibrate first: this voice/model/settings has no real measured pace yet. Record one part '
              '(--max-parts 1 --execute), run narration-measure, check plan-check\'s real_forecast_s, then record '
              'the rest. --skip-calibration overrides this.')
    rates = model_rates(rd, key, model_id)
    req_max = rates.get('maximum_text_length_per_request')
    if req_max and any(s['characters'] > int(req_max) for s in batch):
        error('A part is longer than ElevenLabs now accepts for this model in one request.',
              {'max_characters': req_max, 'parts': [s['id'] for s in batch if s['characters'] > int(req_max)]})
    # The balance is checked before anything on disk moves: a failed preflight leaves the folder as it was.
    budget = credit_preflight(rd, key, model_id, sum(s['characters'] for s in batch), args.credit_safety_factor,
                              args.assume_cost_ratio, args.keep_credits, 'this recording') if batch else {}
    history = list(existing.get('history') or [])
    if start_over and existing:
        archive = narrdir.with_name(f'{narrdir.name}-archive-{stamp}')
        shutil.move(str(narrdir), str(archive))
        history = [{'at': now(), 'archived_previous_take_to': str(archive)}]
        existing = {}
    narrdir.mkdir(parents=True, exist_ok=True)
    if redo:
        sup = narrdir / 'superseded'
        sup.mkdir(exist_ok=True)
        for pid in redo:
            part = narrdir / f'part-{pid:03d}.mp3'
            if part.exists():
                shutil.move(str(part), str(sup / f'part-{pid:03d}-{stamp}.mp3'))
        if (narrdir / 'narration.wav').exists():
            shutil.move(str(narrdir / 'narration.wav'), str(sup / f'narration-{stamp}.wav'))
        history.append({'at': now(), 'rerecorded_parts': redo, 'text_changed': changed,
                        'pronunciation_changed': pron_changed, 'other_voice_setup': other_setup,
                        'earlier_direction': outdated, 'asked': asked, 'reason': args.reason or None,
                        'old_takes': str(sup)})
    part_revs = {k: v for k, v in (existing.get('part_revs') or {}).items() if str(k).isdigit() and int(k) in kept}
    part_records = {k: v for k, v in records.items() if str(k).isdigit() and int(k) in kept}
    base = {'voice_id': voice_id, 'model_id': model_id, 'settings': settings, 'voice_rev': vf['voice_rev'],
            'older_run_level_lock': vf['legacy'], 'treatment': dlock.get('treatment'),
            'production_rev': dlock.get('production_rev', 1)}
    manifest = {**spec, 'status': 'partial', 'created_at': existing.get('created_at', now()),
                'credit_preflight': budget, 'voice_settings': settings, 'voice_lock': base,
                'pronunciation_terms': [t['term'] for t in pron['terms']],
                'finished_parts': kept, 'part_revs': part_revs, 'part_records': part_records, 'history': history}
    write_json(manifest_path, manifest)
    per_char = budget.get('credits_per_character') or rates['credits_per_character']
    keep = int(args.keep_credits or 0)
    code = language_code(lock['language'])
    new_parts_done = 0
    for i, (c, s) in enumerate(zip(chunks, spec['chunks'])):
        fname = narrdir / s['file']
        if s['id'] in manifest['finished_parts'] and fname.exists() and fname.stat().st_size > 1024:
            continue
        if args.max_parts and new_parts_done >= args.max_parts:
            break
        body = {'text': c['sent'], 'model_id': model_id, 'voice_settings': settings}
        if code:
            body['language_code'] = code
        prev = context_text(sent_lines, c['line_start'] - 1, -1) if i else ''
        nxt = context_text(sent_lines, c['line_end'] + 1, 1) if i < len(chunks) - 1 else ''
        if prev:
            body['previous_text'] = prev
        if nxt:
            body['next_text'] = nxt
        path = '/v1/text-to-speech/' + urllib.parse.quote(voice_id, safe='') + '?output_format=mp3_44100_128'
        need = math.ceil(s['characters'] * per_char * args.credit_safety_factor) + keep
        try:
            raw, err, entry = eleven_paid_post(rd, key, path, body, 'tts',
                                               {'video': n, 'part': s['id'], 'model_id': model_id, 'voice_id': voice_id},
                                               require=need)
        except RuntimeError as exc:
            raw, err, entry = None, str(exc), None
        if not err and (not raw or len(raw) < 1024):
            err = 'audio response too short'
        if not err:
            temp = fname.with_suffix('.download')
            temp.write_bytes(raw)
            try:
                probe(temp)  # ffprobe reads audio, even though temp suffix is generic
                temp.replace(fname)
            except (RuntimeError, ValueError, OSError) as exc:
                err = f'unreadable audio: {str(exc)[:200]}'
        if err:
            manifest['error'] = f'part {s["id"]}: {err}'
            write_json(manifest_path, manifest)
            error('Partial ElevenLabs recording: BLOCKED (never shorten video to match credits).',
                  {'error': manifest['error'], 'ledger_entry': entry, 'resume': 'the same command again: finished '
                                                                                'parts are kept and never billed again'})
        manifest['finished_parts'].append(s['id'])
        manifest['part_revs'][str(s['id'])] = dlock.get('production_rev', 1)
        manifest['part_records'][str(s['id'])] = {
            **base, 'text_sha256': s['text_sha256'], 'sent_sha256': s['sent_sha256'], 'characters_sent': s['characters'],
            'previous_text_sha256': sha(prev) if prev else None, 'next_text_sha256': sha(nxt) if nxt else None,
            'request_id': (entry or {}).get('request_id'), 'credits_billed': (entry or {}).get('delta'),
            'recorded_at': now()}
        manifest.pop('error', None)
        write_json(manifest_path, manifest)
        new_parts_done += 1
    if len(manifest['finished_parts']) < len(chunks):
        emit({'ok': True, 'mode': 'partial_by_design_max_parts', 'new_parts_this_call': new_parts_done,
              'finished_parts': manifest['finished_parts'], 'total_parts': len(chunks),
              'parts_dir': str(narrdir),
              'next': 'Listen to the new part(s), then narration-measure (real pace, natural gap per line, what '
                      'each tag cost, every line heard) and plan-check (real_forecast_s against the export window). '
                      'Adjust the lines of the parts not yet recorded if needed, then re-run the same tts command (no '
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
    gate = audio_facts(rd, n)
    emit({'ok': gate['ready'], 'audio_file': str(outpath), 'duration_s': manifest['duration_s'],
          'audio_gate': gate, 'next': 'narration-measure: every line heard, tags not read aloud, the joins, the real pace.'},
         0 if gate['ready'] else 2)


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
    # Recorded before the latest direction change to the narrator: re-recorded or explicitly reapproved first.
    old_parts = narration_outdated_parts(read_json(vd / 'direction-lock.json'), manifest) if manifest else []
    if old_parts:
        issues.append('narration_parts_made_for_an_earlier_direction:' + ','.join(str(x) for x in old_parts))
    # One narrator throughout: every part recorded with the voice, model and settings of the video's voice lock.
    warnings = []
    vf = voice_facts(rd, video)
    if manifest and vf['lock']:
        recs = part_records_of(manifest)
        setup = (vf['voice_id'], vf['model_id'], vf['settings'])
        other = [x for x in manifest.get('finished_parts') or []
                 if tuple((recs.get(str(x)) or {}).get(k) or ({} if k == 'settings' else None)
                          for k in ('voice_id', 'model_id', 'settings')) != setup]
        if other:
            issues.append('narration_parts_recorded_with_another_voice_setup:' + ','.join(str(x) for x in other))
    # Every line heard, no tag read aloud (narration-measure, on these exact parts).
    lt = read_json(folder / 'line-times.json')
    seam_s = 0.0
    if lt:
        now_prints = {c.get('id'): quick_fingerprint(folder / c['file']) for c in manifest.get('chunks') or []
                      if (folder / c.get('file', '__missing__')).is_file()}
        current = bool(lt.get('parts')) and all(p.get('fingerprint') == now_prints.get(p.get('id'))
                                                for p in lt['parts'])
        if current:
            issues += [f'narration_line_not_heard:{x}' for x in lt.get('unheard_lines') or []]
            issues += [f'narration_tag_read_aloud:{t["line"]}:{t["tag"]}' for t in lt.get('tags_read_aloud') or []]
            seam_s = sum(float(s.get('seam_hold_s') or 0) for s in lt.get('seams') or [])
        else:
            warnings.append('line-times.json describes an earlier recording: run narration-measure on these parts')
    # The picture can't be shorter than the narration, and export-check holds the export to its own (tighter)
    # window: narration plus the planned edit holds must already fit it, or the export can never pass.
    holds = edit_holds_s(script_lines)
    window = None
    if target and duration:
        tol_e = max(4, target * lock.get('tolerance_export_pct', .025))
        window = [round(target - tol_e, 2), round(target + tol_e, 2)]
        if duration + holds + seam_s > target + tol_e:
            issues.append('narration_plus_edit_holds_longer_than_export_window')
        elif duration + holds + seam_s < target - tol_e:
            issues.append('narration_plus_edit_holds_shorter_than_export_window')
    return {'ready': not issues, 'issues': issues, 'warnings': warnings, 'duration_s': duration,
            'target_length_s': target, 'edit_holds_s': holds, 'seam_holds_s': round(seam_s, 2),
            'expected_edit_s': round(duration + holds + seam_s, 2) if duration else None, 'export_window_s': window,
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
    """The CapCut project as recorded in timeline.json (written from CapCut's own read-back), against the plan it
    must follow: every visual segment is a retimed shot of the current edit plan (shot_id), for that shot's beat,
    starting where retime-shots put it, and shows that shot's own still (asset_path traced through the stills record;
    a callback shot may show the shot it reuses); every shot is in the cut; every audio track other than the
    narration names the beats it serves and plays inside them; music comes from the gated worker under the current
    direction; the stills are current (stills_facts); the edit plan describes the current shots, script and
    direction. Plus the length and format checks the timeline always had."""
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
    cur_shots = read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []
    reuse_of = {str(s.get('id')): str(s.get('reuses')) for s in cur_shots if s.get('reuses')}
    stills = read_json(artifact_path(rd, n, 'stills')).get('images') or {}
    stills_reapproved = bool(reapproved_for(dlock, 'stills'))
    if not plan:
        issues.append('edit_plan_missing_run_retime_shots')
    else:
        lines = read_json(vd / 'script.json').get('lines') or []
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
            if not str(clip.get('asset_path') or '').strip():
                issues.append(f'visual_{i}_missing_asset_path')
            elif sid:   # the picture CapCut really shows, traced to the shot (and beat) it was made for
                rec = stills.get(_pkey(_run_file(rd, clip['asset_path'])))
                if rec and str(rec.get('shot_id')) not in (sid, reuse_of.get(sid)):
                    issues.append(f'visual_{i}_shows_the_still_of_shot_{rec.get("shot_id")}')
                elif not rec and not stills_reapproved:
                    issues.append(f'visual_{i}_still_without_provenance')
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
    for j, seg in enumerate(track.get('audio_tracks') or [], 1):
        kind = str(seg.get('kind') or '')
        if kind == 'narration':
            continue
        bs = [str(x) for x in seg.get('beats') or []]
        if not bs or any(x not in beat_ids for x in bs):
            issues.append(f'audio_track_{j}_must_name_beats_of_the_beat_map')
        else:
            try:
                a, b = float(seg['start_s']), float(seg['end_s'])
                if spans and not any(x in spans and a < spans[x][1] and b > spans[x][0] for x in bs):
                    issues.append(f'audio_track_{j}_plays_outside_its_beats')
            except (KeyError, TypeError, ValueError):
                issues.append(f'audio_track_{j}_needs_start_s_and_end_s')
        if kind == 'music':
            music_used = True
            rec = music.get(_pkey(_run_file(rd, seg.get('file')))) if seg.get('file') else None
            if not rec and not reapproved_for(dlock, 'music'):
                issues.append(f'audio_track_{j}_music_without_provenance')
            elif rec and not media_current(dlock, 'music', rec.get('production_rev')):
                issues.append(f'audio_track_{j}_music_made_for_an_earlier_direction')
    if music and not music_used:
        warnings.append('music was made for this video but timeline.json lists no music track: if the bed is in '
                        'the project, record it (audio_tracks: kind "music", its file, start_s, end_s and beats)')
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


NUM_ONES = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
            'nine': 9}
NUM_TEENS = {'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
             'seventeen': 17, 'eighteen': 18, 'nineteen': 19}
NUM_TENS = {'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80,
            'ninety': 90}
NUM_SCALES = {'thousand': 1000, 'million': 10 ** 6, 'billion': 10 ** 9}
NUM_WORDS = set(NUM_ONES) | set(NUM_TEENS) | set(NUM_TENS) | set(NUM_SCALES) | {'hundred'}


def _num_kind(w):
    if w in NUM_ONES:
        return 'ones', NUM_ONES[w]
    if w in NUM_TEENS:
        return 'teen', NUM_TEENS[w]
    if w in NUM_TENS:
        return 'tens', NUM_TENS[w]
    if w == 'hundred':
        return 'hundred', 100
    if w in NUM_SCALES:
        return 'scale', NUM_SCALES[w]
    return None, None


def _merge_numbers(toks):
    """English number words as digits, so a spoken number and Whisper's digits are one token: 'twelve' -> '12',
    'two hundred and forty' -> '240', 'twenty-six' -> '26', 'nineteen fifty' -> '1950' (a year said in pairs).
    Returns [(token, first_index, last_index)] over the input tokens."""
    out, i, n = [], 0, len(toks)
    while i < n:
        kind, val = _num_kind(toks[i])
        if kind is None or kind in ('hundred', 'scale'):
            if toks[i] == 'a' and i + 1 < n and _num_kind(toks[i + 1])[0] in ('hundred', 'scale'):
                kind, val = 'ones', 1
            else:
                out.append((toks[i], i, i))
                i += 1
                continue
        chunks, total, cur, last, j, start = [], 0, val, kind, i + 1, i
        while j < n:
            k2, v2 = _num_kind(toks[j])
            if toks[j] == 'and' and j + 1 < n and last in ('hundred', 'scale') and _num_kind(toks[j + 1])[0] in ('ones', 'teen', 'tens'):
                j += 1
                continue
            if k2 is None:
                break
            ok = (last == 'tens' and k2 == 'ones') or (k2 == 'hundred' and last in ('ones', 'teen', 'tens')) or \
                 (last in ('hundred', 'scale') and k2 in ('ones', 'teen', 'tens')) or k2 == 'scale'
            if not ok:
                chunks.append((total + cur, start, j - 1))
                total, cur, last, start = 0, v2, k2, j
                j += 1
                continue
            if k2 == 'hundred':
                cur *= 100
            elif k2 == 'scale':
                total += cur * v2
                cur = 0
            else:
                cur += v2
            last = k2
            j += 1
        chunks.append((total + cur, start, j - 1))
        if len(chunks) == 2 and 10 <= chunks[0][0] <= 99 and 10 <= chunks[1][0] <= 99:
            out.append((str(chunks[0][0] * 100 + chunks[1][0]), chunks[0][1], chunks[1][2]))   # 'nineteen fifty'
        else:
            out += [(str(v), a, b) for v, a, b in chunks]
        i = j
    return out


def raw_tokens(text, english=True):
    s = strip_tags(text)
    if english:
        s = re.sub(r'(\d)\s*%', r'\1 percent', s)
        s = re.sub(r'\$\s?(\d[\d,.]*)', r'\1 dollars', s)
    s = re.sub(r'(?<=\d),(?=\d{3}\b)', '', s)
    out = []
    for w in re.findall(r"\b[\w]+(?:[-'.][\w]+)*\b", s, flags=re.UNICODE):
        w = w.lower()
        if english and '-' in w and all(p in NUM_WORDS for p in w.split('-')):
            out += w.split('-')
            continue
        t = re.sub(r"[-']", '', w)
        if not re.fullmatch(r'\d+\.\d+', t):
            t = t.replace('.', '')
        if t:
            out.append(t)
    return out


def tokens_of(text, language='en'):
    """Comparable word tokens: lower case, hyphens and apostrophes dropped ('Yudam-ni' matches 'Yudamni'), and, in
    English, numbers as digits on both sides ('Twelve divisions' matches Whisper's '12 divisions')."""
    english = str(language or 'en').lower().startswith('en')
    toks = raw_tokens(text, english)
    return [t for t, _, _ in _merge_numbers(toks)] if english else toks


def align_detail(line_texts, words, language='en'):
    """Script lines against Whisper's words: difflib on comparable tokens, then, inside each stretch where the two
    disagree, a word Whisper spelt differently (a name: 'Chosin' heard as 'Choson') paired by its letters. Returns
    per-line token times, the share matched, and Whisper's tokens with their times and which were matched."""
    english = str(language or 'en').lower().startswith('en')
    s_tok, owner, pos, tok_time = [], [], [], []
    for li, text in enumerate(line_texts):
        toks = tokens_of(text, language)
        tok_time.append([None] * len(toks))
        for k, t in enumerate(toks):
            s_tok.append(t)
            owner.append(li)
            pos.append(k)
    raw, times = [], []
    for w in words:
        for t in raw_tokens(w['text'], english):
            raw.append(t)
            times.append((w['start_s'], w['end_s']))
    merged = _merge_numbers(raw) if english else [(t, i, i) for i, t in enumerate(raw)]
    h_tok = [t for t, _, _ in merged]
    h_time = [(times[a][0], times[b][1]) for _, a, b in merged]
    used, matched = set(), 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=s_tok, b=h_tok, autojunk=False).get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                tok_time[owner[i1 + k]][pos[i1 + k]] = h_time[j1 + k]
                used.add(j1 + k)
                matched += 1
        elif op == 'replace':
            jj = j1
            for ii in range(i1, i2):
                if len(s_tok[ii]) < 4:
                    continue
                for jx in range(jj, j2):
                    if difflib.SequenceMatcher(None, s_tok[ii], h_tok[jx]).ratio() >= 0.75:
                        tok_time[owner[ii]][pos[ii]] = h_time[jx]
                        used.add(jx)
                        matched += 1
                        jj = jx + 1
                        break
    return {'tok_time': tok_time, 'ratio': (matched / len(s_tok)) if s_tok else 0.0,
            'heard': h_tok, 'heard_times': h_time, 'heard_used': used}


def align_lines(line_texts, words, language='en'):
    """Match script lines to Whisper words. Returns, per line, a list of per-token (start, end) times (None where
    Whisper heard something else), and the share of script tokens matched."""
    d = align_detail(line_texts, words, language)
    return d['tok_time'], d['ratio']


def confirmations_path(folder):
    return folder / 'listening-confirmations.json'


def recheck_line(part_file, a, b, line_text, wdir, lid, args, language):
    """A line the long Whisper pass did not hear, listened to again on its own: Whisper medium on a short window
    of the part around where the line should be. Found, it was a transcription miss; still missing, the line may
    really be absent from the audio."""
    clip, tj_path = wdir / f'recheck-{lid}.wav', wdir / f'recheck-{lid}.json'
    window = [round(a, 2), round(b, 2)]
    cached = read_json(tj_path)
    if not (cached.get('window') == window and tj_path.stat().st_mtime >= Path(part_file).stat().st_mtime
            and cached.get('model') == args.whisper_model):
        run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-ss', f'{a:.3f}', '-t',
                 f'{max(0.5, b - a):.3f}', '-i', str(part_file), '-ac', '1', '-ar', '16000', str(clip)])
        transcribe(clip, tj_path, args.whisper_model, args.device, args.compute_type)
        cached = read_json(tj_path)
        cached['window'] = window
        write_json(tj_path, cached)
    words = transcript_words(cached)
    d = align_detail([line_text], words, language)
    got = [x for x in d['tok_time'][0] if x]
    return {'line': lid, 'window_s': window, 'matched': round(d['ratio'], 2), 'found': d['ratio'] >= 0.6,
            'heard': ' '.join(str(w['text']).strip() for w in words)[:300],
            'times': [a + got[0][0], a + max(x[1] for x in got)] if got else None}


def cmd_narration_measure(args):
    """Measure the real narration with the references' own yardstick (the same transcribe() and
    wpm_from_transcript_raw): real pace (while speaking, and overall with every pause), the natural gap after each
    line, what every inline tag actually cost, how the narration pauses next to the references, when each script line
    is spoken, and the joins between parts. Every line must be heard: a line Whisper's long pass missed is listened to
    again on its own (a short Whisper medium window); one still missing blocks the edit until it is re-recorded or the
    user confirms by listening (--confirm L105 --reason "..."). A tag whose words were heard was read aloud: the same.
    Writes 50-audio/video-NN/line-times.json and, from 300+ words of the locked voice, the voice lock's `measured`
    (what plan-check's real_forecast_s and the tts calibration gate read)."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    script = read_json(vd / 'script.json', required=True)
    lock = read_json(vd / 'length-lock.json', required=True)
    language = lock.get('language') or script.get('language') or 'en'
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
    prints = {c['id']: quick_fingerprint(folder / c['file']) for c in chunks if (folder / c['file']).is_file()}
    wdir = folder / 'whisper'
    wdir.mkdir(exist_ok=True)
    conf_path = confirmations_path(folder)
    conf = read_json(conf_path)
    if args.confirm:
        if n_words(args.reason) < MIN_NOTE_WORDS:
            error('A listening confirmation says who listened and what they heard (--reason).')
        line_part = {li: c for c in chunks for li in range(int(c['line_start']), int(c['line_end']) + 1)}
        ids = [x.strip() for x in args.confirm.split(',') if x.strip()]
        index = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
        for lid in ids:
            if lid not in index:
                error('--confirm names a line the script does not have.', lid)
            c = line_part.get(index[lid])
            conf.setdefault('lines', {})[lid] = {'reason': args.reason, 'at': now(),
                                                 'part_fingerprint': prints.get(c['id']) if c else None}
        write_json(conf_path, conf)
    rows, all_words, per_part, all_segments = {}, [], [], []
    heard_tokens = []          # (token, start, end, used) over the whole narration
    rechecks, tot_words, tot_speech, tot_dur = [], 0.0, 0.0, 0.0
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
        d = align_detail([str(r.get('text') or '') for r in lines[lo - 1:hi]], words, language)
        for j, tt in enumerate(d['tok_time']):
            got = [x for x in tt if x]
            rows[lo + j] = {'id': lines[lo + j - 1].get('id'), 'index': lo + j, 'part': c['id'],
                            'start_s': round(offset + got[0][0], 3) if got else None,
                            'end_s': round(offset + max(x[1] for x in got), 3) if got else None,
                            'matched_words': len(got), 'words': len(tt),
                            '_tok': [None if x is None else (offset + x[0], offset + x[1]) for x in tt]}
        heard_tokens += [(t, offset + a, offset + b, k in d['heard_used'])
                         for k, (t, (a, b)) in enumerate(zip(d['heard'], d['heard_times']))]
        # A line the long pass did not hear (or barely): listened to again, on its own.
        order_here = list(range(lo, hi + 1))
        for li in order_here:
            r = rows[li]
            short = r['words'] <= 1
            if not r['words'] or (r['matched_words'] if short else r['matched_words'] / r['words'] >= 0.5):
                continue
            prev_end = next((rows[x]['end_s'] for x in reversed(range(lo, li)) if rows[x]['end_s'] is not None
                             and rows[x]['matched_words']), None)
            next_start = next((rows[x]['start_s'] for x in range(li + 1, hi + 1) if rows[x]['start_s'] is not None
                               and rows[x]['matched_words']), None)
            a = max(0.0, (prev_end - offset - 0.6) if prev_end is not None else 0.0)
            b = min(durations[c['id']], (next_start - offset + 0.6) if next_start is not None else durations[c['id']])
            if b - a > 60:
                b = a + 60
            if args.no_recheck:
                rec = {'line': r['id'], 'window_s': [round(a, 2), round(b, 2)], 'found': False, 'skipped': True}
            else:
                rec = recheck_line(part, a, b, str(lines[li - 1].get('text') or ''), wdir, str(r['id']), args, language)
                if rec['found'] and rec.get('times'):
                    r['start_s'], r['end_s'] = round(offset + rec['times'][0], 3), round(offset + rec['times'][1], 3)
                    r['heard_on_recheck'] = True
            rec['part'] = c['id']
            rechecks.append(rec)
        all_words += [{'start_s': w['start_s'] + offset, 'end_s': w['end_s'] + offset, 'text': w['text']} for w in words]
        all_segments += _segments_of(tj, offset)
        per_part.append({'id': c['id'], 'lines': [lo, hi], 'offset_s': round(offset, 3), 'fingerprint': prints[c['id']],
                         'duration_s': durations[c['id']], 'words': wc, 'speech_s': round(speech, 2),
                         'wpm': round(wc / (speech / 60)) if speech else None, 'alignment_match_ratio': round(d['ratio'], 3)})
        tot_words += wc
        tot_speech += speech
        tot_dur += durations[c['id']]
    order = sorted(rows)
    for k, li in enumerate(order):     # a line still without times sits between its neighbours
        r = rows[li]
        if r['start_s'] is None:
            prev_end = next((rows[x]['end_s'] for x in reversed(order[:k]) if rows[x]['end_s'] is not None), None)
            next_start = next((rows[x]['start_s'] for x in order[k + 1:] if rows[x]['start_s'] is not None), None)
            r['start_s'] = prev_end if prev_end is not None else next_start
            r['end_s'] = next_start if next_start is not None else prev_end
            r['interpolated'] = True
    confirmed = conf.get('lines') or {}
    def confirmed_for(lid):
        c = confirmed.get(str(lid))
        li = next((x for x in order if str(rows[x]['id']) == str(lid)), None)
        return bool(c and li is not None and c.get('part_fingerprint') == prints.get(rows[li]['part']))
    unheard = [str(rc['line']) for rc in rechecks if not rc.get('found') and not confirmed_for(rc['line'])]
    # Every tag: what it cost, and whether its own words were heard (read aloud instead of performed).
    pause_tag_at, tag_rows = set(), []
    for li in order:
        text = str(lines[li - 1].get('text') or '')
        for m in TAG_RE.finditer(text):
            entry = classify_tag(m.group(1))
            at_start, at_end = not text[:m.start()].strip(), not text[m.end():].strip()
            tag_rows.append({'li': li, 'line': rows[li]['id'], 'tag': entry['tag'], 'category': entry.get('category'),
                             'k': len(tokens_of(text[:m.start()], language)), 'at_start': at_start, 'at_end': at_end,
                             'inner': m.group(1)})
            if entry.get('category') == 'pause':
                pause_tag_at.add(li if at_end else li - 1 if at_start else -1)
    gaps = [rows[li + 1]['start_s'] - rows[li]['end_s'] for li in order
            if li + 1 in rows and li not in pause_tag_at and rows[li]['end_s'] is not None
            and rows[li + 1]['start_s'] is not None and rows[li + 1]['part'] == rows[li]['part']]
    natural_gap = statistics.median(gaps) if gaps else 0.0
    measured_tags, read_aloud = [], []
    for t in tag_rows:
        li = t['li']
        tok, k = rows[li]['_tok'], t['k']
        before = next((x[1] for x in reversed(tok[:k]) if x), None)
        if before is None and li - 1 in rows:
            before = rows[li - 1]['end_s']
        after = next((x[0] for x in tok[k:] if x), None)
        if after is None and li + 1 in rows:
            after = rows[li + 1]['start_s']
        if before is None or after is None:
            continue
        base = natural_gap if (t['at_start'] or t['at_end']) else 0.15
        measured_tags.append({'line': t['line'], 'tag': t['tag'], 'gap_s': round(after - before, 2),
                              'excess_s': round(after - before - base, 2)})
        words_of_tag = [w for w in tokens_of(t['inner'], language) if len(w) > 2 and w not in EN_FUNCTION_WORDS]
        stray = [h for h, a, b, used in heard_tokens if not used and a >= before - 0.1 and b <= after + 0.1]
        if words_of_tag and sum(1 for w in words_of_tag if w in stray) * 2 >= len(words_of_tag):
            if not confirmed_for(t['line']):
                read_aloud.append({'line': t['line'], 'tag': t['tag'], 'heard': stray[:8]})
    costs = {}
    for m in measured_tags:
        costs.setdefault(m['tag'], []).append(m['excess_s'])
    costs = {k: round(statistics.median(v), 2) for k, v in costs.items()}
    tag_excess = sum(max(0.0, m['excess_s']) for m in measured_tags)
    nlines = len(rows)
    wpm = round(tot_words / (tot_speech / 60)) if tot_speech else None
    # Whisper's long pass drops a phrase now and then (measured here: ~1% of words, heard in the audio when a short
    # window is re-transcribed), so its word count runs a little low. wpm stays the references' yardstick (they are
    # measured the same way); the length forecast uses the script's own words over the same speech time.
    script_words = sum(count_words(lines[li - 1].get('text') or '') for li in rows)
    forecast_wpm = round(script_words / (tot_speech / 60), 1) if tot_speech else None
    overall_wpm = round(script_words / (tot_dur / 60), 1) if tot_dur else None
    per_line = round((tot_dur - tot_speech - tag_excess) / nlines, 3) if nlines else None
    complete = sorted(rows) == list(range(1, len(lines) + 1))
    ratio_all = (sum(p['alignment_match_ratio'] * (p['lines'][1] - p['lines'][0] + 1) for p in per_part) / nlines) if nlines else 0
    profile = pause_profile(all_words)
    # Possible repeats: three or more heard tokens matched to no script word, that repeat the words around them.
    repeats = []
    run = []
    for idx, (h, a, b, used) in enumerate(heard_tokens + [('', 0, 0, True)]):
        if not used and h:
            run.append(idx)
            continue
        if len(run) >= 3:
            seq = [heard_tokens[x][0] for x in run]
            around = [heard_tokens[x][0] for x in range(max(0, run[0] - 12), min(len(heard_tokens), run[-1] + 13))
                      if x not in run]
            if any(seq == around[x:x + len(seq)] for x in range(len(around) - len(seq) + 1)):
                repeats.append({'at_s': round(heard_tokens[run[0]][1], 2), 'heard': ' '.join(seq)})
        run = []
    # The joins: the gap between the parts against the voice's own gap between lines, the pace on each side, and
    # any words said twice across it. A join shorter than the natural gap gets a seam hold in the edit (retime-shots).
    seams, by_index = [], {r['index']: r for r in rows.values()}
    ordered_parts = sorted(use, key=lambda x: x['id'])
    for a_c, b_c in zip(ordered_parts, ordered_parts[1:]):
        if b_c['id'] != a_c['id'] + 1:
            continue
        last, first = by_index.get(int(a_c['line_end'])), by_index.get(int(b_c['line_start']))
        if not last or not first or last['end_s'] is None or first['start_s'] is None:
            continue
        gap = round(first['start_s'] - last['end_s'], 3)
        planned = str(lines[int(a_c['line_end']) - 1].get('pause_via') or '').lower() in ('tag', 'edit')
        hold = round(natural_gap - gap, 2) if (not planned and natural_gap - gap >= 0.08) else 0.0
        def side(lo_i, hi_i):
            rs = [by_index[x] for x in range(lo_i, hi_i + 1) if x in by_index and by_index[x]['start_s'] is not None]
            w = sum(count_words(lines[r['index'] - 1].get('text') or '') for r in rs)
            span = (rs[-1]['end_s'] - rs[0]['start_s']) if len(rs) > 1 else 0
            return round(w / (span / 60)) if span > 3 else None
        t = (last['end_s'] + first['start_s']) / 2
        before_tok = [h for h, a, b, u in heard_tokens if b <= t][-3:]
        after_tok = [h for h, a, b, u in heard_tokens if a >= t][:3]
        seams.append({'after_part': a_c['id'], 'after_line': last['id'], 'at_s': round(t, 3), 'gap_s': gap,
                      'natural_gap_s': round(natural_gap, 3), 'seam_hold_s': hold,
                      'wpm_before': side(int(a_c['line_end']) - 7, int(a_c['line_end'])),
                      'wpm_after': side(int(b_c['line_start']), int(b_c['line_start']) + 7),
                      'repeated_words': before_tok if before_tok and before_tok == after_tok else None})
    # Each beat as heard: its pace while speaking and with its pauses, how dense with numbers, next to what it asked.
    beat_rows = []
    for b in read_json(vd / 'beat-map.json').get('beats') or []:
        try:
            b0, b1 = int(b['line_start']), int(b['line_end'])
        except (KeyError, TypeError, ValueError):
            continue
        rs = [by_index[x] for x in range(b0, b1 + 1) if x in by_index and by_index[x]['start_s'] is not None]
        if len(rs) < 2:
            continue
        w = sum(count_words(lines[r['index'] - 1].get('text') or '') for r in rs)
        span = rs[-1]['end_s'] - rs[0]['start_s']
        inside = sum(max(0.0, r['end_s'] - r['start_s']) for r in rs)
        between = [y['start_s'] - x['end_s'] for x, y in zip(rs, rs[1:])]
        nums = sum(len(NUMBER_WORDS.findall(strip_tags(lines[r['index'] - 1].get('text') or ''))) for r in rs)
        beat_rows.append({'id': b.get('id'), 'start_s': round(rs[0]['start_s'], 2), 'end_s': round(rs[-1]['end_s'], 2),
                          'words': w, 'wpm_overall': round(w / (span / 60)) if span > 0 else None,
                          'wpm_inside_lines': round(w / (inside / 60)) if inside > 0 else None,
                          'longest_gap_s': round(max(between), 2) if between else None,
                          'gaps_over_0_8s': sum(1 for g in between if g >= 0.8),
                          'numbers_per_min': round(nums / (span / 60), 1) if span > 0 else None,
                          'tags': sum(1 for t in tag_rows if b0 <= t['li'] <= b1),
                          'intended': {x: b.get(x) for x in ('experience', 'narration_direction', 'pace')}})
    # Names on the pronunciation list, as Whisper heard them where they are said (a listening list, never a verdict:
    # Whisper itself mishears names).
    pron = pronunciation_facts(rd, n, lines)
    pron_heard = []
    for t in pron['terms']:
        tt = tokens_of(t['term'], language)
        for lid in pron['uses'].get(t['term']) or []:
            li = next((x for x in order if str(rows[x]['id']) == lid), None)
            if li is None or rows[li]['start_s'] is None:
                continue
            here = [h for h, a, b, u in heard_tokens if a >= rows[li]['start_s'] - 0.2 and b <= rows[li]['end_s'] + 0.2]
            hit = all(x in here for x in tt)
            close = None if hit else max(here, key=lambda h: difflib.SequenceMatcher(None, tt[0], h).ratio(), default=None)
            pron_heard.append({'term': t['term'], 'line': lid, 'at_s': rows[li]['start_s'], 'heard_as_written': hit,
                               'nearest_heard': close})
    # How the voice moves, beat by beat and on each side of every join, next to what each beat asked for and to the
    # references measured the same way (av_tools): the writing of the parts not yet recorded is where a flat stretch
    # gets fixed.
    delivery, delivery_error = None, None
    if not args.no_delivery:
        try:
            av = _av()
            import tempfile
            top = max(c['id'] for c in use)
            files = [folder / c['file'] for c in sorted(chunks, key=lambda x: x['id'])
                     if c['id'] <= top and (folder / c['file']).is_file()]
            spans = {}
            for b in beat_rows:
                spans[str(b['id'])] = (b['start_s'], b['end_s'])
            for s in seams:
                spans[f'seam_{s["after_part"]}_before'] = (max(0.0, s['at_s'] - 20), s['at_s'])
                spans[f'seam_{s["after_part"]}_after'] = (s['at_s'], s['at_s'] + 20)
            with tempfile.TemporaryDirectory() as tmp:
                wav = av.concat_audio(files, Path(tmp) / 'narration.wav')
                delivery = av.delivery(f'video-{n:02d} narration', wav, all_words, spans=spans, segments=all_segments)
            for b in read_json(vd / 'beat-map.json').get('beats') or []:
                k = str(b.get('id'))
                if k in (delivery.get('spans') or {}):
                    delivery['spans'][k]['intended'] = {x: b.get(x) for x in ('experience', 'narration_direction', 'pace')}
            for s in seams:
                bf = (delivery.get('spans') or {}).get(f'seam_{s["after_part"]}_before') or {}
                af = (delivery.get('spans') or {}).get(f'seam_{s["after_part"]}_after') or {}
                s['level_db_before'], s['level_db_after'] = bf.get('speech_level_db'), af.get('speech_level_db')
                s['pitch_range_before'], s['pitch_range_after'] = bf.get('pitch_range_st'), af.get('pitch_range_st')
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
           'script_words': script_words, 'forecast_wpm': forecast_wpm, 'overall_wpm': overall_wpm,
           'natural_line_gap_median_s': round(natural_gap, 3), 'per_line_overhead_s': per_line,
           'alignment_match_ratio': round(ratio_all, 3), 'tags_measured': measured_tags,
           'unheard_lines': unheard, 'rechecked_lines': rechecks, 'tags_read_aloud': read_aloud,
           'possible_repeats': repeats, 'seams': seams, 'beats': beat_rows, 'pronunciation_heard': pron_heard,
           'pause_profile': profile, 'lines': [rows[li] for li in order], 'measured_at': now(),
           'method': 'transcribe() + wpm_from_transcript_raw on each part, exactly as on the references; lines '
                     'aligned on comparable tokens (numbers as digits), a missed line re-heard on its own window'}
    write_json(folder / 'line-times.json', out)
    own, legacy = voice_lock(rd, n)
    vl_path = voice_lock_path(rd, n) if (own and not legacy) else rd / '60-voice' / 'voice-lock.json'
    vl = read_json(vl_path)
    settings = manifest.get('voice_settings') or {}
    recs = part_records_of(manifest)
    setups = {json.dumps([(recs.get(str(c['id'])) or {}).get(k) for k in ('voice_id', 'model_id', 'settings')],
                         sort_keys=True) for c in use}
    wrote, note = False, None
    if tot_words < 300:
        note = 'Under 300 words measured: too short to calibrate (short samples read fast and scatter).'
    elif len(setups) > 1:
        note = 'The measured parts were recorded with different voice setups: nothing written to the voice lock.'
    elif vl.get('voice_id') != manifest.get('voice_id') or (vl.get('settings') or {}) != settings or \
            (vl.get('model_id') or 'eleven_v4') != manifest.get('model_id'):
        note = 'The narration was recorded with another voice, model or settings than the voice lock: not written there.'
    else:
        prev = vl.get('measured') or {}
        same = (prev.get('voice_id') == manifest['voice_id'] and prev.get('model_id') == manifest['model_id']
                and (prev.get('settings') or {}) == settings)
        tag_costs = dict(prev.get('tag_costs_s') or {}) if same else {}
        tag_costs.update(costs)
        vl['measured'] = {'voice_id': manifest['voice_id'], 'model_id': manifest['model_id'], 'settings': settings,
                          'wpm': wpm, 'words': int(tot_words), 'script_words': script_words,
                          'forecast_wpm': forecast_wpm, 'overall_wpm': overall_wpm, 'speech_s': round(tot_speech, 2),
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
        if classify_tag(m['tag'][1:-1]).get('category') == 'pause' and m['excess_s'] < 0.2:
            warnings.append(f"{m['line']} {m['tag']} made no measurable pause: listen (was it read aloud?)")
    for r in repeats:
        warnings.append(f'possible repeated words at {_mmss(r["at_s"])}: "{r["heard"]}" (listen)')
    for s in seams:
        if s.get('repeated_words'):
            warnings.append(f'words heard on both sides of the join after part {s["after_part"]}: listen at {_mmss(s["at_s"])}')
    issues = [f'narration_line_not_heard:{x}' for x in unheard] + \
             [f'narration_tag_read_aloud:{t["line"]}:{t["tag"]}' for t in read_aloud]
    emit({'ok': not issues, 'issues': issues, 'line_times': str(folder / 'line-times.json'), 'complete': complete,
          'wpm': wpm, 'forecast_wpm': forecast_wpm, 'overall_wpm': overall_wpm, 'words': int(tot_words),
          'script_words': script_words, 'duration_s': round(tot_dur, 2), 'per_line_overhead_s': per_line,
          'natural_line_gap_median_s': round(natural_gap, 3), 'tags_measured': measured_tags,
          'unheard_lines': unheard, 'rechecked_lines': rechecks, 'tags_read_aloud': read_aloud, 'seams': seams,
          'beats': beat_rows, 'pronunciation_heard': pron_heard, 'pause_profile': profile,
          'references': {v: {'wpm': (lock.get('per_ref_wpm') or {}).get(v), **p}
                         for v, p in ref_pause_profiles(rd, lock.get('reference_ids') or []).items()},
          'alignment_match_ratio': round(ratio_all, 3), 'voice_lock_updated': wrote, 'note': note,
          'warnings': warnings,
          'delivery': ({'file': str(folder / 'delivery.json'), 'summary': delivery.get('summary'),
                        'references': delivery.get('references'),
                        'reading': 'Pitch range and movement, loudness contrast and rate across the narration, per '
                                   'beat and on each side of every join: a beat asked to lift that measures flat is '
                                   'rewritten in the parts not yet recorded (10-creative-direction.md), never fixed in '
                                   'the audio. A calm, intimate narrator measures narrower than an energetic one: '
                                   'compare with what each beat asked for, not with a target.'}
                       if delivery else {'error': delivery_error} if delivery_error else None),
          'next': ('Listen where flagged; a line still not heard is re-recorded (tts --rerecord-parts N --reason) or '
                   'confirmed by the user (--confirm Lnnn --reason). ' if issues else '') +
                  'plan-check (real_forecast_s against the export window); when complete: retime-shots.'},
         0 if not issues else 2)


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
                 # What the editor carries out (09): the locked treatment's picture, sound and pace, and each shot's
                 # beat direction below; the revision stamps which direction this edit plan follows.
                 'direction': {'treatment': dlock.get('treatment'), 'production_rev': dlock.get('production_rev', 1),
                               **{k: chosen_treatment_of(read_json(vd / 'direction.json')).get(k) for k in
                                  ('visual_language', 'sound', 'audiovisual_relationship', 'structure_and_pace')}},
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

    Every lock knows which fields changed (direction_sections). A change that alters what production must do raises
    the production revision, and the artifacts that field feeds (FIELD_EFFECTS) must be updated or explicitly
    reapproved before the stages that use them continue. Anything that already existed before the first lock was made
    without a direction and is affected the same way. Evidence, alternatives, reasons and samples are harmless: same
    revision, nothing to redo. Refining the chosen treatment needs no new blind read (it is shown at every plan-check);
    a treatment that was never in one, or one rewritten past TREATMENT_REREAD_BELOW of the vocabulary its reader saw,
    gets its own blind read first."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    df = direction_facts(rd, n)
    if df['issues']:
        error('The creative direction is not complete yet.', df['issues'])
    lockp = vd / 'direction-lock.json'
    prev = read_json(lockp)
    if prev and prev.get('direction_sha256') == df['direction_sha256']:
        emit({'ok': True, 'unchanged': True, 'lock': str(lockp), 'treatment': prev.get('treatment'),
              'production_rev': prev.get('production_rev')})
        return
    d = read_json(vd / 'direction.json')
    trs = {str(t.get('id')): t for t in d.get('treatments') or [] if isinstance(t, dict)}
    chosen = str(df['chosen_treatment'])
    tr = review_state(vd, 'treatment', df['treatments_sha256'])
    if not tr['issues']:      # the latest blind read saw exactly these treatments
        reviewed = {k: treatment_text(v) for k, v in trs.items()}
    elif not prev:
        error('The treatments need their blind comparison read (review-packet --kind treatment), recorded, and '
              'every finding answered before the direction is locked.', tr['issues'])
    else:
        unsettled = [x for x in tr['issues'] if x != 'treatment_review_outdated']
        if unsettled:
            error('The latest blind read of the treatments is not settled yet: answer every finding first.', unsettled)
        reviewed = dict(prev.get('reviewed_treatments') or {})
        seen = reviewed.get(chosen)
        if seen is None:
            error('The chosen treatment was never in a blind comparison read: run review-packet --kind treatment for '
                  'the current treatments first.', {'chosen': chosen, 'compared': sorted(reviewed)})
        share = _jaccard(_content_tokens(seen), _content_tokens(treatment_text(trs.get(chosen))))
        if share < TREATMENT_REREAD_BELOW:
            error(f'The chosen treatment has been rewritten since its blind read: {share:.0%} of its vocabulary is '
                  'still what the reader saw. A rewrite this large is a new treatment: give the current treatments '
                  'their own blind read (review-packet --kind treatment), answer it, then lock again.',
                  {'treatment': chosen, 'still_the_same': round(share, 2), 'needs_at_least': TREATMENT_REREAD_BELOW})
    sections = direction_sections(d)
    script_exists = (vd / 'script.json').is_file()
    entry = {'locked_at': now(), 'direction_sha256': df['direction_sha256'],
             'treatments_sha256': df['treatments_sha256'], 'treatment': df['chosen_treatment'],
             'script_existed': script_exists, 'sections': sections, 'reviewed_treatments': reviewed}
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
        if not args.revise:
            error('The direction changed since it was locked. Re-lock with --revise "what changed and why".')
        old = prev.get('sections') or {}
        changed = sorted(k for k in set(old) | set(sections) if old.get(k) != sections.get(k))
        hit = [a for a in ALL_ARTIFACTS if any(a in field_effects(k) for k in changed)]
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
    outdated = outdated_artifacts(rd, n)
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
    emit({'ok': True, 'artifact': args.artifact, 'for_revision': rev, 'still_outdated': outdated_artifacts(rd, n)})


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

Words in [square brackets] are delivery directions the voice receives but never says. A line followed by
"(the picture holds N s in silence)" is followed by that silence while the picture stays on screen. Judge both as
part of what you would hear: does each direction help, or push the narration into theatre; does each silence earn
its moment, or pad the runtime?

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
9. The delivery directions and the silences: where they help, where they are theatre or filler, where a silence
   holds a moment the story has not earned.

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
        holds = hold_snapshot(lines)
        text = _fill(SCRIPT_BRIEF, TITLE=title, MINUTES=minutes, HOUSE_RULES=HOUSE_RULES, OUT=out_path)
        held = sum(v[0] for v in holds.values() if v[1] == 'edit')
        refs_pp = [p for p in (lock.get('reference_pause_profiles') or {}).values() if p]
        longest = max((p.get('longest_pause_s') or 0 for p in refs_pp), default=0)
        text += (f'Held silences in this script: {len(holds)} ({held:g} s where the picture holds with no voice, '
                 f'{round(100 * held / lock["target_length_s"], 1)}% of the runtime).'
                 + (f' The comparable narrators\' longest pause is about {longest:g} s.' if longest else '') + '\n\n')
        for lid, t in snapshot.items():
            text += f'{lid} {t}\n'
            if lid in holds:
                s, via = holds[lid]
                text += (f'      (the picture holds {s:g} s in silence)\n' if via == 'edit'
                         else f'      (the voice pauses here, about {s:g} s)\n')
        meta.update({'subject_sha256': script_hash(lines), 'subject_snapshot': snapshot, 'holds_snapshot': holds})
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
           'holds_snapshot': meta.get('holds_snapshot'),
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
    p.add_argument('--execute', action='store_true', help='Voice Design is billed: without this flag the designs are '
                   'only priced; with it the balance is checked first and each call goes in the spend ledger.')
    p.add_argument('--credit-safety-factor', type=float, default=1.15)
    p.add_argument('--keep-credits', type=int, default=0, help='Credits that must still be left afterwards')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_voice_candidates)
    p = sub.add_parser('voice-pick', help='Choose this video\'s narrator for its locked treatment (voice, model, '
                       'settings, the reason): every recording of the video follows it')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', required=True); p.add_argument('--name', default='')
    p.add_argument('--model-id', default='eleven_v4', choices=TTS_MODELS)
    p.add_argument('--settings', default='', help='JSON: {"stability": S, "similarity_boost": M}, both chosen for '
                   'this narrator (stability: consistency between generations against expressive range)')
    p.add_argument('--reason', default='', help='Why this voice and these settings fit the treatment\'s narrator')
    p.add_argument('--replace', action='store_true', help='Change this video\'s narrator deliberately (a revision)')
    p.set_defaults(func=cmd_voice_pick)
    p = sub.add_parser('voice-probe'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', default='', help='Default: this video\'s voice lock')
    p.add_argument('--model-id', default='', choices=('',) + TTS_MODELS, help='Default: the voice lock\'s')
    p.add_argument('--settings', default='', help='JSON voice_settings (stability, similarity_boost); default the lock\'s.')
    p.add_argument('--text', default='', help='The passage to hear, inline [tags] included exactly as the script '
                   'will carry them; the pronunciation list is applied as tts applies it.')
    p.add_argument('--no-pronunciation', action='store_true', help='Send the plain spelling (to hear the difference)')
    p.add_argument('--credit-safety-factor', type=float, default=1.15)
    p.add_argument('--keep-credits', type=int, default=0, help='Credits that must still be left afterwards')
    p.add_argument('--whisper-model', default='medium'); p.add_argument('--device', default='cpu')
    p.add_argument('--compute-type', default='int8'); p.set_defaults(func=cmd_voice_probe)
    p = sub.add_parser('tts'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--voice-id', default='', help='Optional: must be the video\'s voice lock (a check, never an override)')
    p.add_argument('--model-id', default='', choices=('',) + TTS_MODELS, help='Optional: must be the voice lock\'s')
    p.add_argument('--settings', default='', help='Optional JSON: must be the voice lock\'s settings (a check)')
    p.add_argument('--max-chars', type=int, help=f'Target part size in characters for new parts (default '
                   f'{PART_TARGET_CHARS}: a guideline; parts follow the beats)')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--rerecord-changed', action='store_true', help='Re-record only the recorded parts that no longer '
                   'match (lines, pronunciation, voice setup or direction changed; old takes move to superseded/).')
    p.add_argument('--rerecord-parts', default='', help='Re-record these finished parts after listening or a check '
                   '(e.g. a line not heard, a tag read aloud): 2 or 2,5, with --reason')
    p.add_argument('--reason', default='', help='Why --rerecord-parts re-records them (kept in the history)')
    p.add_argument('--rechunk', action='store_true', help='Start over with fresh part boundaries (every part '
                   're-billed); needs --archive-existing when audio exists.')
    p.add_argument('--archive-existing', action='store_true', help='Move the existing audio folder aside (to '
                   'video-NN-archive-<time>) before starting over with another voice/model/language or --rechunk.')
    p.add_argument('--skip-calibration', action='store_true', help='Allow recording several parts before this '
                   'voice/model/settings has a real measured pace (normally: --max-parts 1, then narration-measure).')
    p.add_argument('--credit-safety-factor', type=float, default=1.15,
                   help='Reserve over the expected credits (default 1.15)')
    p.add_argument('--assume-cost-ratio', type=float, default=None,
                   help='0.1-1.0: credits per character to assume instead of the rate ElevenLabs reports for the model '
                   '(GET /v1/models). Only for a ratio measured on this account (the spend ledger): never guessed, '
                   'always recorded in the manifest\'s credit_preflight.')
    p.add_argument('--keep-credits', type=int, default=0, help='Credits that must still be left after this recording')
    p.add_argument('--max-parts', type=int, default=None,
                   help='Generate at most N new parts this call, then stop (status stays partial, no '
                   'narration.wav yet, nothing re-billed next time). Use --max-parts 1 to generate only '
                   'the first real part, measure it, and confirm the voice, settings and pace before '
                   'paying for the rest: the first part IS the calibration, paid once, kept if good, '
                   'never a separate throwaway sample.')
    p.set_defaults(func=cmd_tts)
    p = sub.add_parser('audio-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_audio_check)
    p = sub.add_parser('narration-measure', help='Real pace, line gap, tag costs, pauses and line times of the narration')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--parts', default='', help='Only these finished parts, e.g. 1 (the calibration part)')
    p.add_argument('--no-delivery', action='store_true', help='Skip the delivery measurement (pitch, loudness, '
                   'rate per beat next to the references)')
    p.add_argument('--no-recheck', action='store_true', help='Do not re-hear missed lines on their own (they stay '
                   'unresolved and block the edit)')
    p.add_argument('--confirm', default='', help='Lines the user listened to and confirms (heard, tag performed): '
                   'L105 or L105,L319, with --reason; kept until that part is re-recorded')
    p.add_argument('--reason', default='', help='Who listened and what they heard (for --confirm)')
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
    p.add_argument('--render-narration', action='store_true', help='Kept for older notes: narration-edit.wav is '
                   'always written when the edit has holds (it is the audio the CapCut project uses)')
    p.add_argument('--no-seam-holds', action='store_true', help='Do not restore the voice\'s natural gap at the '
                   'joins between recorded parts')
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
