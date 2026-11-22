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
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

VIDEO_EXT = {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v', '.ts'}
DOC_EXT = {'.txt', '.md', '.pdf', '.docx', '.rtf', '.json'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 'static-youtube-longform-v1'
DEFAULT_MIN_LONGFORM = 480
# Reference analysis samples two frames per second (state.json analysis_fps, set when the run is made), each frame
# picked by and kept with its own source timestamp (analysis_sampler). A run keeps the rate and the sampler its
# references were analysed with, so its references and its own export are measured on one yardstick; a run whose
# state predates these settings was analysed at 5 fps with nominal slot times. The generated video's frame rate
# (format.fps), the CapCut timeline and the export are separate and unchanged.
ANALYSIS_FPS = 2.0
LEGACY_ANALYSIS_FPS = 5.0
ANALYSIS_SAMPLER = 'pts-v1'     # = av_tools.SAMPLER
LEGACY_SAMPLER = 'nominal'      # frames numbered at a fixed rate, their times read from the numbers


def run_analysis_fps(st):
    return float(st.get('analysis_fps') or LEGACY_ANALYSIS_FPS)


def run_analysis_sampler(st):
    return str(st.get('analysis_sampler') or LEGACY_SAMPLER)


def parse_clock(s):
    """Seconds from 75, '75.5', '01:15', '01:15.5' or '1:01:15'; None when it is none of these."""
    if s is None or isinstance(s, bool):
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    m = re.fullmatch(r'(?:(\d+):)?(\d{1,3}):(\d{1,2}(?:\.\d+)?)', s)
    if m:
        return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    try:
        return float(s)
    except ValueError:
        return None


def parse_span(s):
    """(start_s, end_s) of 'mm:ss-mm:ss', of {'from', 'to'}, or of one time (t, t); (None, None) when unreadable."""
    if isinstance(s, dict):
        a, b = parse_clock(s.get('from')), parse_clock(s.get('to'))
    else:
        parts = [x.strip() for x in str(s or '').split('-') if x.strip()]
        if len(parts) == 1:
            a = b = parse_clock(parts[0])
        elif len(parts) == 2:
            a, b = parse_clock(parts[0]), parse_clock(parts[1])
        else:
            a = b = None
    if a is None or b is None or b < a:
        return None, None
    return a, b


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


def file_sha256(path):
    """The whole file's content hash: what ties a cut to the exact approved narration (a quick fingerprint reads only
    the ends of a file)."""
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def cmd_doctor(args):
    checks = {'python': sys.version.split()[0], 'python_executable': sys.executable,
              'ffmpeg': shutil.which('ffmpeg') is not None,
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
    dirs = cuda_dll_dirs()
    checks['cuda_dll_dirs'] = dirs
    # a fresh terminal (opened after the user PATH got these folders) has them; an older process gets them in-process
    checks['cuda_dirs_on_this_process_path'] = len(_on_path(dirs)) == len(dirs) and bool(dirs)
    try:
        import ctranslate2
        checks['ctranslate2'] = ctranslate2.__version__
        checks['cuda_devices'] = ctranslate2.get_cuda_device_count()
    except ImportError:
        checks['ctranslate2'] = None
    ok = checks['ffmpeg'] and checks['ffprobe']
    if args.whisper:
        model, eng = whisper_model('medium', WHISPER_DEVICE, WHISPER_COMPUTE)   # a failure stops here, with its cause
        checks['whisper'] = {k: v for k, v in eng.items() if k != 'cuda_dll_dirs'}
        if args.file:
            import tempfile
            src = Path(args.file).expanduser().resolve()
            if not src.is_file():
                error('File not found', str(src))
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'probe.json'
                transcribe(src, out, 'medium', WHISPER_DEVICE, WHISPER_COMPUTE)
                tj = read_json(out)
            words = transcript_words(tj)
            checks['whisper_file'] = {'file': str(src), 'duration_s': tj.get('duration_s'), 'language': tj.get('language'),
                                      'segments': len(tj.get('segments') or []), 'words': len(words),
                                      'elapsed_s': tj.get('elapsed_s'), 'realtime_x': tj.get('realtime_x'),
                                      'device': (tj.get('engine') or {}).get('device'),
                                      'first_words': ' '.join(w['text'].strip() for w in words[:24])}
        ok = ok and checks['whisper']['device'] == 'cuda'
    emit({'ok': ok, 'checks': checks,
          'note': 'Whisper medium runs on the GPU for every transcription (doctor --whisper loads it and runs it once; '
                  '--file also transcribes that file). av-profile (watch sheets, delivery measurements) needs numpy, '
                  'opencv, librosa, soundfile and pillow; image/CapCut/TTS tools are checked separately.'})


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
          'analysis_fps': args.fps, 'analysis_sampler': ANALYSIS_SAMPLER, 'min_longform_s': args.min_longform,
          'notes': 'Static only. Agents invent new subjects within the chosen niche; references teach form, not copied content.'}
    write_json(rd / 'state.json', st)
    (rd / 'todo.md').write_text('# Static Studio run\n\n- [ ] Inventory and prepare references (av-profile: watch them as films)\n- [ ] Analyze evidence and choose niche\n- [ ] Lock comparable long-form length\n- [ ] Research the story; creative direction: approaches, treatments, blind read, direction-lock (before the script)\n- [ ] Beat directions and script; cold read with every finding answered; plan-check\n- [ ] Record complete narration (calibration part first: pace and delivery per beat)\n- [ ] Design and assemble image-led edit (shot-check, retime-shots)\n- [ ] Export; final watch review answered; release-check\n', encoding='utf-8')
    emit({'ok': True, 'run': str(rd), 'next': 'scan --run "' + str(rd) + '"'})


def cmd_clone(args):
    src, previous = run_folder(argparse.Namespace(run=args.from_run))
    import tempfile
    tmp = argparse.Namespace(references=previous['source_references'], workspace=args.workspace,
                            slug=args.slug, fps=ANALYSIS_FPS,
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
               'run_id': rd.name, 'created_at': now(), 'cloned_from': str(src),
               # frames are not cloned: the clone's references are prepared again, at the current analysis rate
               'analysis_fps': ANALYSIS_FPS, 'analysis_sampler': ANALYSIS_SAMPLER})
    write_json(rd/'state.json', st)
    for oldrel in ['00-inventory/references.json', '20-analysis/cohorts/index.json']:
        old = src/oldrel
        if old.is_file():
            target = rd/oldrel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(old, target)
    for card in (src/'20-analysis/cards').glob('V*.json'):
        shutil.copy2(card, rd/'20-analysis/cards'/card.name)
    # The content reviews are analysis too (their times are the source's, whatever the sampling rate), with the
    # records of their closer looks (index.json only: frames of a closer look are never copied).
    for review in (src/'20-analysis/content').glob('V*.json'):
        (rd/'20-analysis/content').mkdir(parents=True, exist_ok=True)
        shutil.copy2(review, rd/'20-analysis/content'/review.name)
    for idx in (src/'20-analysis/inspect').glob('*/*/index.json'):
        target = rd/idx.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(idx, target)
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


# Whisper is medium (the user's rule for all audio) and runs on the GPU: CTranslate2 (faster-whisper) with the CUDA 12
# runtime pip installed for this interpreter (nvidia-cublas-cu12, nvidia-cudnn-cu12, nvidia-cuda-nvrtc-cu12). The CPU
# is used only on the user's explicit yes (--device cpu --cpu-approved "..."), never as a silent fallback: a GPU that
# cannot run stops the command with what is missing. One model per process, loaded once for every file it hears.
WHISPER_MODELS = ('medium',)
WHISPER_DEVICE, WHISPER_COMPUTE = 'cuda', 'float16'
_WHISPER = {}
_DLL_DIRS = []
_CPU_APPROVAL = None


def cuda_dll_dirs():
    """The NVIDIA runtime folders pip installed for this interpreter (site-packages/nvidia/*/bin)."""
    roots = []
    try:
        import nvidia
        roots = [str(r) for r in getattr(nvidia, '__path__', [])]
    except ImportError:
        pass
    if not roots:
        import site
        roots = [str(Path(sp) / 'nvidia') for sp in site.getsitepackages() if (Path(sp) / 'nvidia').is_dir()]
    out = []
    for r in roots:
        out += [str(x) for x in sorted(Path(r).glob('*/bin')) if x.is_dir()]
    return list(dict.fromkeys(out))


def _on_path(dirs):
    have = {os.path.normcase(os.path.normpath(x)) for x in os.environ.get('PATH', '').split(os.pathsep) if x}
    return [d for d in dirs if os.path.normcase(os.path.normpath(d)) in have]


def cuda_runtime_setup():
    """Make those folders findable by CTranslate2 in THIS process (first on its PATH, and in its DLL search list).
    A terminal opened after they were added to the user's PATH has them already; a process started before (an agent
    session) does not. Nothing outside this process changes."""
    dirs = cuda_dll_dirs()
    if os.name == 'nt' and dirs:
        add = [d for d in dirs if d not in _on_path(dirs)]
        if add:
            os.environ['PATH'] = os.pathsep.join(add + [os.environ.get('PATH', '')])
        for d in dirs:
            if d not in _DLL_DIRS:
                try:
                    os.add_dll_directory(d)
                    _DLL_DIRS.append(d)
                except OSError:
                    pass
    return dirs


def _gpu_name():
    try:
        p = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
                           capture_output=True, text=True, timeout=15)
        return (p.stdout or '').strip().splitlines()[0] if p.returncode == 0 and p.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def whisper_model(model_name, device, compute_type):
    """(model, engine facts) loaded once per process. On the GPU it runs one second of silence through the encoder
    and decoder at once, so a missing CUDA library fails here, by name, before any real audio; the facts are what
    the inference engine itself reports (device, index, compute type), not the settings asked for."""
    key = (model_name, device, compute_type)
    if key in _WHISPER:
        return _WHISPER[key]
    if model_name not in WHISPER_MODELS:
        raise RuntimeError(f'Whisper {model_name} is not used here: every transcription is Whisper medium.')
    try:
        import ctranslate2
        import faster_whisper
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(f'faster-whisper is not importable in {sys.executable}: {exc}')
    facts = {'python': sys.executable, 'faster_whisper': getattr(faster_whisper, '__version__', None),
             'ctranslate2': getattr(ctranslate2, '__version__', None), 'model': model_name}
    if device == 'cuda':
        facts['cuda_dll_dirs'] = cuda_runtime_setup()
        facts['cuda_devices'] = ctranslate2.get_cuda_device_count()
        if facts['cuda_devices'] < 1:
            raise RuntimeError('Whisper runs on the GPU here, and CTranslate2 sees no CUDA device. Check the NVIDIA '
                               'driver (nvidia-smi), that CUDA_VISIBLE_DEVICES does not hide the card, and that '
                               f'{sys.executable} has the CUDA build of ctranslate2. Nothing was transcribed; the CPU is '
                               'used only on the user\'s explicit yes (--device cpu --cpu-approved "...").')
        facts['gpu'] = _gpu_name()
    elif device == 'cpu':
        facts['cpu_approved'] = _CPU_APPROVAL
    t0 = time.time()
    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        facts['load_s'] = round(time.time() - t0, 2)
        import numpy as np
        t1 = time.time()
        segs, _ = model.transcribe(np.zeros(16000, dtype=np.float32), beam_size=1, vad_filter=False,
                                   without_timestamps=True, language='en')
        list(segs)
        facts['warmup_s'] = round(time.time() - t1, 2)
    except Exception as exc:   # noqa: BLE001 - CTranslate2 raises plain RuntimeErrors and OSErrors for missing DLLs
        raise RuntimeError(f'Whisper {model_name} could not run on {device} ({compute_type}): {exc}. Python: '
                           f'{sys.executable}. NVIDIA runtime folders found for it: '
                           f'{facts.get("cuda_dll_dirs") or "none"} (cuBLAS 12, cuDNN 9, NVRTC from the nvidia-*-cu12 '
                           'packages; nvidia-smi shows the driver). Nothing was transcribed; no CPU fallback.')
    eng = model.model
    facts.update({'device': eng.device, 'device_index': eng.device_index, 'compute_type': eng.compute_type})
    if device == 'cuda' and eng.device != 'cuda':
        raise RuntimeError(f'Whisper was asked for the GPU but the engine reports {eng.device}; nothing transcribed.')
    _WHISPER[key] = (model, facts)
    return model, facts


def whisper_settings(args):
    """Checked once per command, before any work: Whisper medium on the GPU (cuda, float16). --device cpu needs
    --cpu-approved with the user's own words; nothing ever switches to the CPU by itself."""
    global _CPU_APPROVAL
    if getattr(args, 'whisper_model', 'medium') not in WHISPER_MODELS:
        error('Every transcription here is Whisper medium.', {'asked': args.whisper_model})
    dev = getattr(args, 'device', None) or WHISPER_DEVICE
    if dev == 'cpu':
        said = (getattr(args, 'cpu_approved', None) or '').strip()
        if n_words(said) < 3:
            error('Whisper runs on the GPU here. The CPU is used only when the user explicitly says so: pass '
                  '--cpu-approved "<what the user said>" with --device cpu. Nothing ran.')
        _CPU_APPROVAL = said
    args.device = dev
    if not getattr(args, 'compute_type', None):
        args.compute_type = WHISPER_COMPUTE if dev == 'cuda' else 'int8'


def add_whisper_args(p):
    p.add_argument('--whisper-model', default='medium', choices=list(WHISPER_MODELS))
    p.add_argument('--device', default=WHISPER_DEVICE, choices=['cuda', 'cpu'],
                   help='cuda: the GPU, always; cpu only with --cpu-approved')
    p.add_argument('--compute-type', default=None, help='float16 on the GPU (the default)')
    p.add_argument('--cpu-approved', help='the user\'s own words allowing Whisper on the CPU this time (--device cpu)')


def transcribe(path, outpath, model_name, device, compute_type):
    model, eng = whisper_model(model_name, device, compute_type)
    t0 = time.time()
    segs, info = model.transcribe(str(path), beam_size=5, word_timestamps=True, vad_filter=True,
                                  condition_on_previous_text=False)
    rows = []
    for s in segs:
        rows.append({'start_s': round(s.start, 3), 'end_s': round(s.end, 3), 'text': s.text.strip(),
                     'words': [{'start_s': round(w.start, 3), 'end_s': round(w.end, 3), 'text': w.word}
                               for w in s.words or []]})
    elapsed = time.time() - t0
    result = {'status': 'transcribed', 'source': str(path), 'model': model_name,
              'language': info.language, 'duration_s': round(info.duration, 2),
              'engine': {k: eng.get(k) for k in ('device', 'device_index', 'compute_type', 'gpu', 'faster_whisper',
                                                 'ctranslate2', 'python', 'cpu_approved') if eng.get(k) is not None},
              'elapsed_s': round(elapsed, 2), 'realtime_x': round(info.duration / elapsed, 1) if elapsed > 0 else None,
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
    fps = run_analysis_fps(st)
    sampler = run_analysis_sampler(st)
    if args.fps and abs(float(args.fps) - fps) > 1e-9:
        error(f'This run analyses its references at {fps:g} fps (state.json analysis_fps): every reference of a run is '
              'sampled at one rate, so they and the run\'s own export compare on one yardstick. Clone the run to '
              'analyse at another rate (a clone prepares its references again at the current rate).',
              {'run_fps': fps, 'requested_fps': args.fps})
    if not 0 < fps <= 60:
        error('FPS must be between 0 and 60')
    estimate = sum(v.get('duration_s') or 0 for v in chosen) * fps
    if args.dry_run:
        emit({'ok': True, 'videos': len(chosen), 'fps': fps, 'sampler': sampler,
              'estimated_sample_frames': int(estimate), 'per_video': {x['id']: x['duration_s'] for x in chosen},
              'note': f'{fps:g} fps is this run\'s analysis rate (a frame every {1 / fps:g} s'
                      + (', each at its own timestamp' if sampler == ANALYSIS_SAMPLER else ', nominal slot times')
                      + '); for a brief stretch the samples cannot settle, inspect-window looks closer.'})
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
        # The frames and the transcript are cached apart: a new sampling rate, sampler or width re-makes the
        # frames only, never the transcript (the audio did not change), and frames made another way are never
        # reused. An older manifest held one signature for both, for nominal-slot frames.
        pts_mode = bool(args.full_fps) or sampler == ANALYSIS_SAMPLER
        frames_sig = {'fingerprint': v['fingerprint'], 'fps': signature['fps'], 'width': args.width,
                      'sampler': ANALYSIS_SAMPLER if pts_mode else LEGACY_SAMPLER}
        words_sig = {k: signature[k] for k in ('fingerprint', 'whisper_model')}
        sig_key = 'full_frames_signature' if args.full_fps else 'frames_signature'
        old_sig = pold.get('signature') or {}
        old_frames = dict(pold.get(sig_key) or ({} if args.full_fps else
                                                {k: old_sig.get(k) for k in ('fingerprint', 'fps', 'width')}))
        old_frames.setdefault('sampler', LEGACY_SAMPLER)
        old_words = pold.get('transcript_signature') or {k: old_sig.get(k) for k in words_sig}
        index_path = dest / ('all-frames-index.json' if args.full_fps else 'frame-index.json')
        details = {k: x for k, x in pold.items() if k in ('frames_signature', 'full_frames_signature', 'frame_index',
                                                         'all_frames_index', 'sampler', 'sampled_frames', 'sample_fps')}
        details.update({'id': v['id'], 'source': str(src), 'signature': signature, sig_key: frames_sig,
                        'transcript_signature': words_sig, 'updated_at': now()})
        try:
            if not (old_frames == frames_sig and list(target.glob('*.jpg')) and (index_path.is_file() or not pts_mode)):
                if pts_mode:
                    frames, origin = _av().sample_frames(src, target, fps=fps, width=args.width, native=bool(args.full_fps))
                    gaps = [y['t_s'] - x['t_s'] for x, y in zip(frames, frames[1:])]
                    write_json(index_path, {
                        'source_id': v['id'], 'mode': 'source_pts', 'sampler': ANALYSIS_SAMPLER,
                        'fps': 'original' if args.full_fps else fps,
                        'interval_s': None if args.full_fps else round(1 / fps, 4),
                        'clock': 'transcript: each frame\'s source timestamp minus the audio stream\'s start, the '
                                 'clock of every word time and speech segment',
                        'clock_origin_s': round(origin, 4), 'max_gap_s': round(max(gaps), 4) if gaps else None,
                        'note': 'Each frame shows the picture at its t_s exactly; anything between two samples is '
                                'unseen (inspect-window looks closer at a brief stretch).',
                        'frames': [{**f, 'approx_s': f['t_s']} for f in frames]})
                else:   # a run made before: frames numbered at a fixed rate, as it was analysed
                    for existing in target.glob('*.jpg'):
                        existing.unlink()
                    run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src), '-vf',
                             f"fps={fps},scale={args.width}:-2", '-q:v', '5', str(target / '%07d.jpg')], timeout=None)
            if not args.full_fps:
                details['sampled_frames'] = len(list(target.glob('*.jpg')))
                details['sample_fps'] = fps
                details['sampler'] = frames_sig['sampler']
            else:
                details['all_frames'] = len(list(target.glob('*.jpg')))
            details['full_frame_extraction'] = bool(args.full_fps)
            details['all_frames_index' if args.full_fps else 'frame_index'] = str(index_path)
            # A run made before keeps its NOMINAL sample slots (re-derived from the file names), not exact PTS.
            sample_rate = fps
            if not args.full_fps and not pts_mode:
                frame_index_path = dest / 'frame-index.json'
                frame_names = sorted(x.name for x in target.glob('*.jpg'))
                frame_index = {'source_id': v['id'], 'mode': 'nominal_sample_time',
                               'warning': 'Approximate sample time from output slot; not source-native PTS.',
                               'fps': sample_rate, 'interval_s': round(1 / sample_rate, 4),
                               'tolerance_s': round(0.5 / sample_rate, 4),
                               'frames': [{'file': name, 'approx_s': round(i/sample_rate, 3)}
                                          for i, name in enumerate(frame_names)]}
                write_json(frame_index_path, frame_index)
                details['frame_index'] = str(frame_index_path)
            if not args.skip_whisper and v.get('has_audio'):
                tp = dest / 'transcript.json'
                if not (old_words == words_sig and read_json(tp).get('status') == 'transcribed'):
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
# The older pause form (`pause_after_s`): up to this long it was taken as the voice's own gap (nothing realised);
# longer, it was silence ADDED ON TOP of that gap. Kept so older scripts read as they were written and reviewed.
NATURAL_PAUSE_MAX_S = 1.0
# Natural gap per script line before this run's voice is measured (eleven_v4 here, 2026-11-19: 0.36-0.42 s).
DEFAULT_LINE_OVERHEAD_S = 0.4
# The silence after one line before this voice is measured, for a planned pause's estimate only (one eleven_v4
# narrator, 2026-11-21, from the audio: median 0.61 s, 0.19-0.79 s line to line). Once recorded, each line's own gap
# is used.
DEFAULT_NATURAL_GAP_S = 0.6
# What a planned pause has to say besides its length (03): what it is for, what the viewer sees while it lasts, what
# the sound does. Required of every planned pause, read by the cold reader, and carried into the edit.
PAUSE_TEXT_FIELDS = (('pause_purpose', 'needs_its_story_purpose'), ('pause_picture', 'needs_its_picture'),
                     ('pause_sound', 'needs_its_sound'))
# A planned silence is part of a performance (05 "Narration as a performance"): how the line before it should land and
# how the next line should start again are planned with it, before anything is recorded (pause_total_s form).
PAUSE_PERFORMANCE_FIELDS = (('pause_landing', 'needs_how_the_line_lands'),
                            ('pause_resume', 'needs_how_the_next_line_starts'))
# Seconds a cue may add, as a band, when this voice has not been measured with it (05): a catalogue value was measured
# on another voice (x0.5-1.5), a pause wording without one 1-3 s, a delivery cue may slow or quicken its own line a
# little. Assumptions, labelled as such, replaced by this voice's own observations once a take exists.
TAG_BAND_CATALOGUE = (0.5, 1.5)
TAG_BAND_PAUSE_UNKNOWN_S = (1.0, 3.0)
TAG_BAND_DELIVERY_S = (-0.3, 0.6)


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


SEAM_FALL_RATIO, SEAM_RESET_RATIO = 1.5, 1.6


def seam_boundary_effects(last_cad, usual):
    """How a join between two recorded parts may have changed the delivery (05): the last line of a part falling much
    harder than this voice usually lands a line (it can sound like an ending), and the next part starting much higher
    than its usual restart (a fresh beginning). Facts to listen for, never a verdict: at a chapter turn a fresh start
    belongs; inside a scene it is the recording boundary showing."""
    out = []
    if not last_cad or not usual:
        return out
    f, uf = last_cad.get('last_vowel_fall_st'), usual.get('last_vowel_fall_st')
    if isinstance(f, (int, float)) and isinstance(uf, (int, float)) and uf < 0 and f <= uf * SEAM_FALL_RATIO:
        out.append(f'the part ends with a harder fall than usual ({f:+.1f} st against {uf:+.1f}): it may sound like an ending')
    r, ur = last_cad.get('next_reset_st'), usual.get('next_reset_st')
    if isinstance(r, (int, float)) and isinstance(ur, (int, float)) and ur > 0 and r >= ur * SEAM_RESET_RATIO:
        out.append(f'the next part starts higher than usual ({r:+.1f} st against {ur:+.1f}): it may sound like a fresh '
                   'beginning')
    return out


def tag_estimate(tag, category, measured=None):
    """What one cue may add to the narration, as a band (05): this voice setup's own observations when a take has
    measured it (the silence a pause cue left beyond the usual gap; the time a delivery cue added to its line), else
    a labelled assumption. Never a universal number, and never assumed to add up exactly across a passage."""
    obs = [o for o in ((measured or {}).get('cue_observations') or []) if o.get('tag') == tag]
    key = 'excess_s' if category == 'pause' else 'line_extra_s'
    xs = [float(o[key]) for o in obs if isinstance(o.get(key), (int, float))]
    if xs:
        return {'tag': tag, 'low_s': round(min(xs), 2), 'high_s': round(max(xs), 2), 'n': len(xs),
                'basis': f'measured on this voice setup ({len(xs)} occurrence{"s" if len(xs) != 1 else ""})'}
    entry = tag_catalogue().get(tag) or {}
    if category == 'pause':
        if entry.get('approx_cost_s') is not None:
            a = float(entry['approx_cost_s'])
            return {'tag': tag, 'low_s': round(a * TAG_BAND_CATALOGUE[0], 2), 'high_s': round(a * TAG_BAND_CATALOGUE[1], 2),
                    'n': 0, 'basis': 'catalogue value measured on another voice: a band until this voice is measured'}
        return {'tag': tag, 'low_s': TAG_BAND_PAUSE_UNKNOWN_S[0], 'high_s': TAG_BAND_PAUSE_UNKNOWN_S[1], 'n': 0,
                'basis': 'pause wording not measured anywhere: an assumed band'}
    return {'tag': tag, 'low_s': TAG_BAND_DELIVERY_S[0], 'high_s': TAG_BAND_DELIVERY_S[1], 'n': 0,
            'basis': 'delivery cue not measured on this voice: may slow or quicken its line a little (assumed band)'}


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


def _pause_tags_around(lines, i):
    """The pause tags at line i's end and at the next line's start: where a performed pause sits."""
    here = str(lines[i].get('text') or '').rstrip()
    after = str(lines[i + 1].get('text') or '').lstrip() if i + 1 < len(lines) else ''
    ends = [m.group(1) for m in (re.search(r'\[([^\[\]]+)\]\s*$', here), re.match(r'\s*\[([^\[\]]+)\]', after)) if m]
    return [x for x in ends if is_pause_tag(x)]


def script_pause_plan(lines):
    """Each planned pause, how it is realised and what it is for. A pause is a proposal until the voice is measured
    (hold-decide), so the script says the experience it wants, never a length to insert mechanically:
    - `pause_total_s`: the WHOLE silence the viewer hears after the line, the voice's own gap included. The edit adds
      only the difference between it and the gap the voice really left there (measured), never the whole of it.
    - `pause_via`: 'edit' (a hold the edit adds: exact, free, adjustable) or 'tag' (a pause tag at this line's end or
      the next line's start, performed by the voice: costs its measured time inside the narration).
    - `pause_purpose`, `pause_picture`, `pause_sound`: what it is for, what the viewer sees while it lasts (what changes
      on screen, or why one frame holds), what the sound does (the bed goes on, drops out, one story-world sound).
    The older form, `pause_after_s`, is read as it was written and reviewed: over 1 s, silence ADDED ON TOP of the
    voice's own gap; up to 1 s, nothing to realise (`form` 'added')."""
    plan, issues = [], []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i+1:03d}')
        via = str(row.get('pause_via') or '').strip().lower()
        if via and via not in ('natural', 'tag', 'edit'):
            issues.append(f'pause_via_invalid:{lid}')
            continue
        has_total = row.get('pause_total_s') not in (None, '')
        try:
            total = float(row['pause_total_s']) if has_total else None
            after = float(row.get('pause_after_s') or 0)
        except (TypeError, ValueError):
            issues.append(f'pause_seconds_invalid:{lid}')
            continue
        if has_total and after:
            issues.append(f'pause_{lid}_has_both_pause_total_s_and_pause_after_s:write_only_pause_total_s')
            continue
        if has_total:
            if total <= 0:
                issues.append(f'pause_total_s_invalid:{lid}')
                continue
            if via not in ('tag', 'edit'):
                issues.append(f'pause_{lid}_needs_pause_via_edit_or_tag')
                continue
            form, seconds = 'total', total
        else:
            if after <= NATURAL_PAUSE_MAX_S and via in ('', 'natural'):
                continue
            if via in ('', 'natural'):
                issues.append(f'pause_{lid}_over_{NATURAL_PAUSE_MAX_S:g}s_needs_pause_via_tag_or_edit')
                continue
            form, seconds = 'added', after
        tags_here = _pause_tags_around(lines, i)
        if via == 'tag' and not tags_here:
            issues.append(f'pause_{lid}_via_tag_but_no_pause_tag_at_this_line_end_or_next_line_start')
        if via == 'edit' and tags_here:
            # One silence, realised once: a pause tag the voice performs and a hold the edit adds would stack.
            issues.append(f'pause_{lid}_is_an_edit_hold_and_a_pause_tag_at_once:choose_one')
        # A silence the story wants says what it is for, what is on screen while it lasts and what the sound does. A
        # written reason is not an approval: the length is decided against the recorded voice and the picture.
        for field, issue in PAUSE_TEXT_FIELDS:
            if n_words(row.get(field)) < MIN_NOTE_WORDS:
                issues.append(f'pause_{lid}_{issue}')
        if form == 'total':
            for field, issue in PAUSE_PERFORMANCE_FIELDS:
                if n_words(row.get(field)) < MIN_NOTE_WORDS:
                    issues.append(f'pause_{lid}_{issue}')
        plan.append({'line': lid, 'index': i + 1, 'via': via, 'form': form, 'seconds': seconds,
                     'total_s': seconds if form == 'total' else None,
                     'added_s': seconds if form == 'added' else None,
                     'purpose': str(row.get('pause_purpose') or '').strip() or None,
                     'picture': str(row.get('pause_picture') or '').strip() or None,
                     'sound': str(row.get('pause_sound') or '').strip() or None,
                     'landing': str(row.get('pause_landing') or '').strip() or None,
                     'resume': str(row.get('pause_resume') or '').strip() or None})
    return plan, issues


def hold_snapshot(lines):
    """Every planned pause as the script's cold reader is shown it: {line: [seconds, via]} (seconds as written:
    the whole silence for pause_total_s, the added silence for the older pause_after_s)."""
    return {p['line']: [round(p['seconds'], 2), p['via']] for p in script_pause_plan(lines)[0]}


def planned_added_s(p, gap_s=None):
    """The silence the edit adds for one planned pause before it is decided: the older form as written; the whole-
    silence form less the voice's gap there (measured, else the voice's usual gap, else DEFAULT_NATURAL_GAP_S). A
    performed pause (via tag) adds nothing in the edit."""
    if p['via'] != 'edit':
        return 0.0
    if p['form'] == 'added':
        return float(p['added_s'])
    return max(0.0, float(p['total_s']) - float(DEFAULT_NATURAL_GAP_S if gap_s is None else gap_s))


def edit_holds_s(lines, gaps=None):
    """The silence the planned edit holds add, before any is decided (gaps: {line index: the voice's gap there})."""
    plan, _ = script_pause_plan(lines)
    return round(sum(planned_added_s(p, (gaps or {}).get(p['index'])) for p in plan), 2)


# ---------------------------------------------------------------- held silences: proposed, measured, decided
# A planned pause is a proposal. Its length is decided twice, each time on evidence the script stage could not have:
# after the narration is recorded (`hold-decide --stage narration`: the gap the voice really left at that line, the
# voice's own rhythm around it, a listening preview) and once the pictures exist (`--stage picture`: the shot on screen
# while it lasts). Each decision names the whole silence wanted (or no hold) and why; the edit adds only the difference
# with the measured gap. Decisions live in 40-plans/video-NN/holds.json (every earlier one kept in its history), apart
# from the reviewed script, so a measured adjustment never re-opens the script read; the final watch review sees the
# silences as they are in the cut. Code gathers and checks the process; which length serves the moment is the
# director's call, never a formula's.
HOLD_STAGES = ('narration', 'picture')
HOLD_VERIFY_TOL_S = 0.06       # an inserted silence measured in the edit's narration lands this close to the decision
# The transition into and out of a held silence, decided with it, never applied by default. 'clean' keeps the voice
# exactly as recorded: its own ending, its own breath, an immediate stop (often the right one for a joke or a reveal).
# 'fade' works ONLY on the voice's own quiet inside the silence (its room tone), never on a syllable, a release or a
# breath, and only when that quiet is audible and long enough: it smooths room tone into and out of the added silence.
# The bed (music, ambience) is the bigger lever and is carried to the edit with exact times: it goes on, enters,
# stops, dips or swells around the silence, or there is none.
TRANSITION_INTO = ('clean', 'fade')
TRANSITION_OUT = ('clean', 'fade')
BED_MOVES = ('continues', 'enters', 'stops', 'dips', 'swells', 'none')
BED_KINDS = ('music', 'ambience', 'bed')        # timeline.json audio_tracks kinds that make the bed
FADE_MIN_S, FADE_MAX_S, FADE_MARGIN_S = 0.08, 0.3, 0.02


def fade_windows(gap, into='clean', out_of='clean', last_line=False):
    """Where a transition fade may act inside one silence (gap: measured_gap or line_gaps' facts, on the narration's
    clock): only on the quiet stretch the added silence goes into, from FADE_MARGIN_S inside its edges to the splice,
    at most FADE_MAX_S long. Returns ({'into': [a, b] | None, 'out_of': [a, b] | None}, problems): a problem means
    the fade cannot be done without touching the voice or without changing nothing at all."""
    res, problems = {'into': None, 'out_of': None}, []
    if into == 'clean' and out_of == 'clean':
        return res, problems
    sub, at = gap.get('subrun_s'), gap.get('insert_at_s')
    if gap.get('basis') != 'audio' or not sub or at is None:
        return res, ['no measured quiet stretch here to fade: the silence was not read from the audio']
    floor = gap.get('floor_under_speech_db')
    audible = float(_av().AUDIBLE_FLOOR_UNDER_DB)
    if floor is None or float(floor) > audible:
        problems.append(f'the voice\'s own silence here is {floor} dB under its speech (audible room tone starts within '
                        f'{audible:g} dB): it is silence already, a fade would change nothing anyone can hear')
    if into == 'fade':
        a, b = float(sub[0]) + FADE_MARGIN_S, float(at)
        if b - a < FADE_MIN_S:
            problems.append(f'only {max(0.0, b - a):.2f} s of quiet before the splice: too little to fade without '
                            'reaching the end of the line')
        else:
            res['into'] = [round(max(a, b - FADE_MAX_S), 3), round(b, 3)]
    if out_of == 'fade':
        if last_line:
            problems.append('nothing follows the last line: there is no way out of this silence to fade')
        else:
            a, b = float(at), float(sub[1]) - FADE_MARGIN_S
            if b - a < FADE_MIN_S:
                problems.append(f'only {max(0.0, b - a):.2f} s of quiet after the splice: too little to fade without '
                                'reaching the next line')
            else:
                res['out_of'] = [round(a, 3), round(min(b, a + FADE_MAX_S), 3)]
    return res, problems


def line_ending_mark(text):
    """The punctuation a line ends on (the writer's cadence the voice follows): '.', '?', '!', ',', ':', ';', '...',
    a dash, or '' when it ends on a word."""
    t = strip_tags(str(text or '')).rstrip().rstrip('"\'”’)')
    for mark in ('...', '…', '—', '--', '-', '.', '?', '!', ',', ':', ';'):
        if t.endswith(mark):
            return {'…': '...', '—': 'dash', '--': 'dash', '-': 'dash'}.get(mark, mark)
    return ''


def holds_path(rd, video):
    return video_dir(rd, video) / 'holds.json'


def hold_decisions(rd, video):
    d = read_json(holds_path(rd, video))
    return {'decisions': d.get('decisions') or {}, 'history': d.get('history') or []}


def line_times_state(rd, video):
    """line-times.json, whether it still describes the recorded parts, and each part's current fingerprint."""
    n = int(video)
    folder = rd / '50-audio' / f'video-{n:02d}'
    lt = read_json(folder / 'line-times.json')
    manifest = read_json(folder / 'manifest.json')
    prints = {int(c['id']): quick_fingerprint(folder / c['file']) for c in manifest.get('chunks') or []
              if c.get('id') is not None and (folder / c.get('file', '__missing__')).is_file()}
    current = bool(lt.get('parts')) and all(p.get('fingerprint') == prints.get(int(p.get('id'))) for p in lt['parts'])
    return lt, current, prints


def measured_gap(rows, index, nlines):
    """The silence the voice left after one line, as narration-measure read it from the audio (Whisper's gap on an
    older measurement). rows: {line index: line-times row}. None when the line is not recorded yet; natural_gap_s None
    when the next line is not (the silence after a line exists only once both sides are recorded)."""
    r = rows.get(index)
    if not r:
        return None
    nx = rows.get(index + 1)
    parts = {str(r.get('part')): None}
    if nx:
        parts[str(nx.get('part'))] = None
    if 'gap_after_s' in r:
        return {'natural_gap_s': r.get('gap_after_s'), 'basis': r.get('gap_basis') or 'audio',
                'span_s': r.get('gap_span_s'), 'parts': parts, 'subrun_s': r.get('gap_subrun_s'),
                'insert_at_s': r.get('gap_insert_at_s'), 'floor_under_speech_db': r.get('gap_floor_under_speech_db'),
                'other_material_s': r.get('gap_other_material_s'), 'cadence': r.get('cadence')}
    if nx and nx.get('start_s') is not None and r.get('end_s') is not None:
        return {'natural_gap_s': round(max(0.0, nx['start_s'] - r['end_s']), 3), 'basis': 'whisper',
                'span_s': [r['end_s'], nx['start_s']], 'parts': parts}
    return {'natural_gap_s': None, 'basis': 'unknown', 'span_s': None, 'parts': parts}


def voice_gap_profile(lt):
    """How long this voice pauses between lines, from the audio: the yardstick a held silence is set against."""
    gs = [float(r['gap_after_s']) for r in lt.get('lines') or []
          if r.get('gap_basis') == 'audio' and r.get('gap_after_s') is not None and not r.get('gap_is_tail')]
    if not gs:
        return {}
    q = sorted(gs)
    pick = lambda f: q[min(len(q) - 1, max(0, int(round(f * (len(q) - 1)))))]
    return {'lines': len(gs), 'median_s': round(statistics.median(gs), 2), 'p10_s': round(pick(.1), 2),
            'p90_s': round(pick(.9), 2), 'shortest_s': round(q[0], 2), 'longest_s': round(q[-1], 2)}


def _line_beats(vd):
    out = {}
    for b in read_json(vd / 'beat-map.json').get('beats') or []:
        try:
            for k in range(int(b['line_start']), int(b['line_end']) + 1):
                out[k] = str(b.get('id'))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def hold_shot(rd, video, index):
    """The shot on screen while the silence after line `index` lasts (a hold belongs to the shot before the cut), the
    shot after it when the cut falls there, and the still each one shows now (callbacks show the shot they reuse)."""
    n = int(video)
    shots = read_json(artifact_path(rd, n, 'shot-plan')).get('shots') or []
    lines = read_json(video_dir(rd, n) / 'script.json').get('lines') or []
    pos = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
    prov = read_json(artifact_path(rd, n, 'stills')).get('images') or {}
    latest = {}
    for path, rec in prov.items():
        sid = str(rec.get('shot_id'))
        if Path(path).is_file() and str(rec.get('made_at') or '') >= str((latest.get(sid) or ('', None))[0]):
            latest[sid] = (str(rec.get('made_at') or ''), path)
    by_id = {str(s.get('id')): s for s in shots}

    def still_of(s):
        src = str(s.get('reuses') or s.get('id'))
        hit = latest.get(src)
        return ({'still': hit[1], 'still_fingerprint': quick_fingerprint(Path(hit[1]))} if hit else
                {'still': None, 'still_fingerprint': None})
    for k, s in enumerate(shots):
        a, b = pos.get(str(s.get('line_start'))), pos.get(str(s.get('line_end')))
        if a is None or b is None or not a <= index <= b:
            continue
        out = {'shot_id': str(s.get('id')), 'new_thing': s.get('new_thing'), **still_of(s)}
        if index == b and k + 1 < len(shots):
            nxt = shots[k + 1]
            out['next_shot'] = {'shot_id': str(nxt.get('id')), **still_of(by_id.get(str(nxt.get('id'))) or nxt)}
        return out
    return None


def hold_facts(rd, video, lines=None):
    """Every planned pause (script.json) and every decided hold (holds.json): the proposal, the gap the voice really
    left there (once both sides are recorded), the decision in force and whether it still stands (the part it was
    decided on unchanged), and the silence the edit adds: decided, or estimated while provisional. Gathers and
    calculates; it never judges a hold."""
    n = int(video)
    vd = video_dir(rd, n)
    if lines is None:
        lines = read_json(vd / 'script.json').get('lines') or []
    plan, _ = script_pause_plan(lines)
    by_line = {p['line']: p for p in plan}
    index = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
    lt, current, prints = line_times_state(rd, n)
    rows = {int(r['index']): r for r in lt.get('lines') or []} if current else {}
    prof = voice_gap_profile(lt) if current else {}
    usual = prof.get('median_s') or (voice_measurement(rd, n) or {}).get('natural_gap_s')
    decs = hold_decisions(rd, n)['decisions']
    beats = _line_beats(vd)
    out = []
    for lid in sorted(set(by_line) | set(decs), key=lambda x: (index.get(x) or 10 ** 6, x)):
        i, p, d = index.get(lid), by_line.get(lid), decs.get(lid)
        if i is None:
            out.append({'line': lid, 'status': 'line_not_in_script', 'added_s': 0.0, 'decision': d})
            continue
        g = measured_gap(rows, i, len(lines))
        text = strip_tags(lines[i - 1].get('text') or '')
        after = strip_tags(lines[i].get('text') or '') if i < len(lines) else ''
        row = {'line': lid, 'index': i, 'beat': beats.get(i), 'words_before': text[-90:], 'words_after': after[:70],
               'proposal': ({k: p[k] for k in ('form', 'seconds', 'via', 'purpose', 'picture', 'sound')} if p else None),
               'natural_gap_s': g.get('natural_gap_s') if g else None, 'gap_basis': g.get('basis') if g else 'not_recorded',
               'status': 'provisional', 'decision': None,
               # How the line before it ends and the next begins (narration-measure, from the audio; the punctuation
               # from the script), and what the silence itself holds: what a transition is decided on.
               'ending': {'punctuation': line_ending_mark(lines[i - 1].get('text')), **((g or {}).get('cadence') or {})},
               'inside_silence': ({k: g.get(k) for k in ('insert_at_s', 'subrun_s', 'floor_under_speech_db',
                                                         'other_material_s')} if g else None)}
        # A silence planned through a pause cue: what the cue gave, judged with a tolerance (close is a success, the
        # model's timing can't be steered to the millisecond): achieved is kept as performed, nothing added.
        if p and p.get('via') == 'tag' and p.get('form') == 'total' and row['natural_gap_s'] is not None:
            row['cue_result'] = pause_cue_outcome(p.get('seconds'), row['natural_gap_s'])
        if d:
            fresh = bool(d.get('parts')) and all(prints.get(int(k)) == v for k, v in (d.get('parts') or {}).items())
            if fresh:
                row.update({'status': f'decided_{d.get("stage")}', 'decision': d, 'added_s': float(d.get('added_s') or 0),
                            'added_is_estimate': False, 'total_s': d.get('total_s'),
                            'natural_gap_s': d.get('natural_gap_s')})
            else:
                row.update({'status': 'stale', 'decision': d,
                            'why_stale': 'the part this line sits in was re-recorded after the decision'})
        if row['status'] in ('provisional', 'stale'):
            gap = row['natural_gap_s'] if row['natural_gap_s'] is not None else usual
            row['added_s'] = round(planned_added_s(p, gap), 2) if p else 0.0
            row['added_is_estimate'] = True
            row['estimate_from'] = ('this line\'s measured gap' if row['natural_gap_s'] is not None else
                                    'the voice\'s usual gap' if usual else f'{DEFAULT_NATURAL_GAP_S:g} s before any voice')
            if p and p['form'] == 'added':
                row['estimate_from'] = 'the older pause_after_s: added on top of the voice\'s gap, as written'
            if (row.get('cue_result') or {}).get('outcome') == 'achieved':
                row['added_s'] = 0.0
                row['estimate_from'] = ('the performed pause is within tolerance of the whole silence planned: kept as '
                                        'performed')
        out.append(row)
    return {'holds': out, 'voice_gaps': prof, 'line_times_current': current,
            'endings_usual': (lt.get('cadence_usual') or {}) if current else {},
            'added_s': round(sum(h.get('added_s') or 0 for h in out), 2),
            'undecided': [h['line'] for h in out if h['status'] in ('provisional', 'stale')],
            'decided_narration': [h['line'] for h in out if h['status'] == 'decided_narration'],
            'decided_picture': [h['line'] for h in out if h['status'] == 'decided_picture']}


def hold_decisions_sha(rd, video):
    """What the edit plan was timed from: the silence decided at every line (whole and added) and its transition (the
    fades the edit's narration carries, what the bed does). A confirmation with the picture that keeps all of these
    changes nothing in the edit, so it asks for no new retime."""
    decs = hold_decisions(rd, video)['decisions']
    def tr(v):
        t = v.get('transition') or {}
        return [t.get('into') or 'clean', t.get('out_of') or 'clean', t.get('bed')]
    return canonical_sha({k: [v.get('total_s'), v.get('added_s')] + (tr(v) if v.get('transition') else [])
                          for k, v in sorted(decs.items())})


def hold_signals(plan):
    """Facts about the planned pauses as a set, for the director to read (never a verdict): lengths that step up or
    down in film order, or are all alike, can mean the length came from a pattern or a position instead of the moment."""
    secs = [round(float(p['seconds']), 2) for p in plan]
    out = []
    if len(secs) >= 3:
        if all(b > a for a, b in zip(secs, secs[1:])) or all(b < a for a, b in zip(secs, secs[1:])):
            out.append('the planned pauses ' + ('grow' if secs[-1] > secs[0] else 'shrink') + ' steadily through the film ('
                       + ', '.join(f'{s:g}' for s in secs) + ' s): check that each length comes from its own moment, '
                       'not from its place in the film')
        elif len(set(secs)) == 1:
            out.append(f'every planned pause is {secs[0]:g} s: check that each length comes from its own moment')
    return out


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


def content_flags(lines, review_text, themes=()):
    m = re.search(r'^#+[^\n]*content flags?[^\n]*\n(.*?)(?=^#|\Z)', review_text or '', flags=re.I | re.M | re.S)
    section = m.group(1) if m else ''
    flags, issues = [], []
    for i, row in enumerate(lines):
        lid = str(row.get('id') or f'L{i+1:03d}')
        spoken = strip_tags(row.get('text') or '')
        found = [(kind, sorted({h.lower() for h in rx.findall(spoken)})) for kind, rx in CONTENT_FLAGS]
        # an excluded segment's theme (its review's "avoid") brought back in the words: rewritten, or why it isn't
        found += [(label, [ph]) for label, ph in theme_hits(spoken, themes)]
        for kind, hits in found:
            if hits:
                reviewed = bool(re.search(r'\b' + re.escape(lid) + r'\b', section))
                flags.append({'line': lid, 'kind': kind, 'terms': hits, 'reviewed': reviewed})
                if not reviewed:
                    issues.append(f'content_flag_unreviewed:{lid}:{kind}')
    return flags, issues


# ---------------------------------------------------------------- content: what a reference may lend, and to what
# Every reference gets a content review from the agent who watched it (01): its problem segments, each with its
# timestamps, what it is, what it does in the story, the evidence, how sure, and what is done with it. Two different
# things are recorded apart and never mixed: content safety (gore, distress, self-harm, ...: what must not be shown
# or reproduced) and the user's creative exclusions (religious or superstitious material, holidays: not harmful,
# just never used as a creative device here). Code checks the record's shape, that the closer looks it relies on
# were really taken, and that nothing excluded is cited or brought back downstream; the judgement is the agent's.
CONTENT_KINDS = ('safety', 'religion_superstition', 'holiday')
SAFETY_CATEGORIES = ('graphic_injury', 'distressing', 'self_harm', 'dangerous_acts', 'sexual_violence_exploitation',
                     'sexual_content_minors', 'hate_extremism', 'nudity_indecency', 'other')
CREATIVE_CATEGORIES = {'religion_superstition': ('religious', 'superstition'), 'holiday': ('holiday',)}
CONTENT_ACTIONS = {'safety': ('exclude', 'restrict_visuals', 'keep'),
                   'religion_superstition': ('exclude', 'keep'), 'holiday': ('exclude', 'keep')}
STORY_STATUS = ('coherent', 'bridged', 'too_dependent')
_THEME_STOP = {'the', 'and', 'with', 'from', 'that', 'this', 'into', 'onto', 'their', 'there', 'about', 'over',
               'under', 'his', 'her', 'its', 'for', 'was', 'were', 'are', 'any', 'all', 'one', 'who', 'what'}


def content_review_path(rd, ref):
    return rd / '20-analysis' / 'content' / f'{str(ref).strip().upper()}.json'


def shot_sheets_dir(rd, ref):
    return rd / '20-analysis' / 'content' / f'{str(ref).strip().upper()}-shots'


SHOTS_PER_SHEET = 36


def make_shot_sheets(rd, ref):
    """One frame of every shot (the sample nearest its middle), 36 to a sheet, each tile labelled with its frame's
    time: the content review's picture coverage. The watch sheets show a frame every 5 s, so a shot of a second or
    two between two tiles is seen only here. Shots come from the av-profile when it was made from these frames,
    else they are measured from the frames (no audio work)."""
    av = _av()
    fi = read_json(rd / '10-media' / ref / 'frame-index.json')
    rows = [(f['t_s'] if f.get('t_s') is not None else f['approx_s'], rd / '10-media' / ref / 'sampled-frames' / f['file'])
            for f in fi.get('frames') or []]
    if not rows:
        error('No sampled frames for this reference: run prepare first.', ref)
    prof = read_json(ref_av_path(rd, ref))
    sig = prof.get('signature') or {}
    if prof.get('shots') and sig.get('frames') == len(rows) and sig.get('sampler', LEGACY_SAMPLER) == (fi.get('sampler') or LEGACY_SAMPLER):
        shots = prof['shots']
    else:
        shots = av.segment_shots(av.frame_features(rows))[0]
    out = shot_sheets_dir(rd, ref)
    picked, sheets = render_shot_sheets(av, rows, shots, out, ref)
    write_json(out / 'index.json', {'reference_id': ref, 'shots': picked, 'sheets': sheets, 'frames': len(rows),
                                    'sampler': fi.get('sampler') or LEGACY_SAMPLER, 'made_at': now()})
    return {'shots': len(picked), 'sheets': sheets}


def render_shot_sheets(av, rows, shots, out, label):
    """rows [(t_s, frame path)], shots from segment_shots: the sample nearest each shot's middle, 36 to a sheet."""
    times = [t for t, _ in rows]
    picked = []
    for k, s in enumerate(shots, 1):
        mid = (float(s['start_s']) + float(s['end_s'])) / 2
        j = min(range(len(times)), key=lambda q: abs(times[q] - mid))
        picked.append({'n': k, 'start_s': s['start_s'], 'end_s': s['end_s'], 'frame_s': times[j], 'file': Path(rows[j][1]).name,
                       '_path': rows[j][1]})
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('sheet-*.jpg'):
        old.unlink()
    sheets = []
    for i in range(0, len(picked), SHOTS_PER_SHEET):
        part = picked[i:i + SHOTS_PER_SHEET]
        sheets.append(av.window_sheet([(x['frame_s'], x['_path']) for x in part],
                                      out / f'sheet-{i // SHOTS_PER_SHEET + 1:03d}.jpg',
                                      f'{label}  shots {part[0]["n"]}-{part[-1]["n"]} of {len(picked)}: one frame of every shot'))
    for x in picked:
        x.pop('_path')
    return picked, sheets


def picture_looks_path(rd, video):
    return rd / '60-visuals' / f'video-{int(video):02d}' / 'content-looks.json'


def closer_looks(rd, ref, a=None, b=None):
    """The closer looks (inspect-window) taken at a reference, overlapping [a, b] when given."""
    out = []
    for idx in sorted((rd / '20-analysis' / 'inspect' / str(ref).upper()).glob('*/index.json')):
        d = read_json(idx)
        lo, hi = d.get('from_s'), d.get('to_s')
        if lo is None or hi is None or not d.get('frames'):
            continue    # a look that took no frames (a window outside the video) was not a look
        if a is None or (lo <= b and hi >= a):
            out.append({'from_s': lo, 'to_s': hi, 'rate': d.get('rate'), 'frames': len(d.get('frames') or []),
                        'why': d.get('why'), 'frames_removed': bool(d.get('frames_removed_at'))})
    return out


def content_review_issues(rd, ref, doc, row):
    """Shape and process of one reference's content review: (issues, segments read as numbers)."""
    iss, segs = [], []
    if not isinstance(doc, dict):
        return ['content_review_must_be_a_json_object'], segs
    media = rd / '10-media' / ref
    if not (media / 'frame-index.json').is_file():
        iss.append('reference_not_prepared_run_prepare_first')
    elif read_json(shot_sheets_dir(rd, ref) / 'index.json').get('frames') != len(read_json(media / 'frame-index.json').get('frames') or []):
        # the review sees every shot: one frame of each (the watch sheets' frame every 5 s can step over a short shot)
        iss.append('shot_sheets_missing_run_content-review_--shot-sheets_and_open_every_one')
    if row.get('has_audio') and read_json(media / 'transcript.json').get('status') != 'transcribed':
        iss.append('reference_words_not_transcribed_run_prepare_with_whisper_first')
    if n_words(doc.get('looked_at')) < 4:
        iss.append('looked_at_must_say_what_was_watched_and_heard')
    dur = float(row.get('duration_s') or 0)
    raw = doc.get('segments')
    if not isinstance(raw, list):
        iss.append('segments_must_be_a_list_(empty_when_nothing_was_found)')
        raw = []
    ids = set()
    for k, s in enumerate(raw, 1):
        if not isinstance(s, dict):
            iss.append(f'segment_{k}_must_be_an_object')
            continue
        sid = str(s.get('id') or '').strip()
        if not re.fullmatch(r'[A-Za-z0-9_]+', sid) or sid in ids:
            iss.append(f'segment_{k}_needs_a_unique_id_(letters_digits)')
            sid = sid or f'#{k}'
        ids.add(sid)
        a, b_ = parse_clock(s.get('from')), parse_clock(s.get('to'))
        if a is None or b_ is None or b_ <= a or a < 0 or (dur and b_ > dur + 1):
            iss.append(f'segment_{sid}_from_to_must_be_times_inside_the_video')
            a = b_ = None
        kind = str(s.get('kind') or '')
        cat = str(s.get('category') or '')
        action = str(s.get('action') or '')
        if kind not in CONTENT_KINDS:
            iss.append(f'segment_{sid}_kind_must_be:' + '/'.join(CONTENT_KINDS))
        elif kind == 'safety':
            if cat in ('religious', 'superstition', 'holiday'):
                iss.append(f'segment_{sid}_religious_superstitious_or_holiday_material_is_not_a_safety_category:'
                           'record it as kind religion_superstition or holiday')
            elif cat == 'minors':
                iss.append(f'segment_{sid}_minors_is_not_a_category:sexual_content_involving_a_minor_is_'
                           'sexual_content_minors;_a_child_in_an_ordinary_scene_is_not_harm_by_itself_(our_own_pictures_'
                           'show_adults,_02)')
            elif cat not in SAFETY_CATEGORIES:
                iss.append(f'segment_{sid}_safety_category_must_be:' + '/'.join(SAFETY_CATEGORIES))
            sev = str(s.get('severity') or '')
            if sev not in ('low', 'medium', 'high'):
                iss.append(f'segment_{sid}_safety_needs_a_severity:low/medium/high')
            if cat == 'sexual_content_minors' and action != 'exclude':
                iss.append(f'segment_{sid}_sexual_content_minors_is_always_excluded')
            if sev == 'high' and action == 'keep':
                iss.append(f'segment_{sid}_high_severity_cannot_be_kept_as_it_is')
            # proportionate: what is low in severity is told within 02 (restricted) or kept, never cut out
            if sev == 'low' and action == 'exclude' and cat != 'sexual_content_minors':
                iss.append(f'segment_{sid}_low_severity_is_restricted_or_kept_never_excluded')
        else:
            if cat not in CREATIVE_CATEGORIES[kind]:
                iss.append(f'segment_{sid}_category_must_be:' + '/'.join(CREATIVE_CATEGORIES[kind]))
            if s.get('severity') not in (None, ''):
                iss.append(f'segment_{sid}_severity_is_for_safety_only:{kind}_is_a_creative_exclusion_not_harm')
        if kind in CONTENT_ACTIONS and action not in CONTENT_ACTIONS[kind]:
            iss.append(f'segment_{sid}_action_must_be:' + '/'.join(CONTENT_ACTIONS[kind]))
        if n_words(s.get('what')) < 4:
            iss.append(f'segment_{sid}_what_must_say_what_it_is_(neutrally,_no_graphic_detail)')
        if n_words(s.get('role')) < 3:
            iss.append(f'segment_{sid}_role_must_say_what_it_does_in_the_story')
        if n_words(s.get('evidence')) < 3:
            iss.append(f'segment_{sid}_evidence_must_say_what_shows_it')
        elif not re.search(r'\d{1,2}:\d{2}', str(s.get('evidence'))):
            iss.append(f'segment_{sid}_evidence_must_cite_the_times_it_was_seen_or_heard_(mm:ss)')
        if str(s.get('confidence') or '') not in ('sure', 'unsure'):
            iss.append(f'segment_{sid}_confidence_must_be_sure_or_unsure')
        if action == 'exclude' and n_words(s.get('why')) < 6:
            # the lighter actions were considered: why the moment cannot be told with what is shown restricted
            # (safety), or why it is a story device and not a plain fact (the creative exclusions)
            iss.append(f'segment_{sid}_exclude_must_say_why_' + ('restricting_what_is_shown_is_not_enough' if kind == 'safety'
                                                                 else 'it_is_a_story_device_not_a_plain_fact'))
        elif action in ('keep', 'restrict_visuals') and n_words(s.get('why')) < 4:
            iss.append(f'segment_{sid}_{action}_must_say_why')
        avoid = [str(x).strip() for x in s.get('avoid') or [] if str(x).strip()]
        if action == 'exclude' and not avoid:
            iss.append(f'segment_{sid}_exclude_must_name_what_to_avoid_bringing_back')
        deps = []
        for j, d in enumerate(s.get('depends') or [], 1):
            da, db = parse_clock((d or {}).get('from')), parse_clock((d or {}).get('to'))
            if da is None or db is None or db <= da or (dur and db > dur + 1):
                iss.append(f'segment_{sid}_depends_{j}_from_to_must_be_times_inside_the_video')
            elif n_words((d or {}).get('why')) < 3:
                iss.append(f'segment_{sid}_depends_{j}_must_say_what_it_depends_on')
            else:
                deps.append((da, db))
        looks = closer_looks(rd, ref, a, b_) if a is not None else []
        if str(s.get('confidence')) == 'unsure' and a is not None and not looks:
            # whatever is decided (cut, restricted or kept), a doubt is settled on what is there, not on a cue
            iss.append(f'segment_{sid}_unsure_needs_a_closer_look_first_(inspect-window)')
        segs.append({'id': sid, 'from_s': a, 'to_s': b_, 'kind': kind, 'category': cat, 'action': action,
                     'depends_s': deps, 'avoid': avoid, 'closer_looks': looks})
    if any(x['action'] == 'exclude' for x in segs):
        story = doc.get('story_without_exclusions') or {}
        if not isinstance(story, dict) or story.get('status') not in STORY_STATUS or n_words(story.get('note')) < 6:
            iss.append('story_without_exclusions_needs_status_(' + '/'.join(STORY_STATUS) + ')_and_a_note')
    if n_words(doc.get('usable')) < 3:
        iss.append('usable_must_say_what_stays_useful_(or_that_nothing_does)')
    return iss, segs


def content_archive_dir(rd, ref, rev):
    return rd / '20-analysis' / 'content-archive' / f'{str(ref).upper()}-r{int(rev)}'


def archived_revision(rd, ref):
    revs = [int(m.group(1)) for p in (rd / '20-analysis' / 'content-archive').glob(f'{str(ref).upper()}-r*')
            if (m := re.fullmatch(rf'{str(ref).upper()}-r(\d+)', p.name))]
    return max(revs, default=0)


def archive_content_review(rd, ref):
    """Move a reference's review, its drafts in the content folder and its closer looks (frames and records) out of
    every path the tools and the next reviewer read, into 20-analysis/content-archive/V###-r<revision>/. The source
    evidence stays: frames, transcript, watch sheets, shot sheets, measurements. Nothing is deleted."""
    ref = str(ref).upper()
    cur = read_json(content_review_path(rd, ref))
    rev = int(cur.get('revision') or 0) or archived_revision(rd, ref) + 1
    dest = content_archive_dir(rd, ref, rev)
    while dest.exists():
        rev += 1
        dest = content_archive_dir(rd, ref, rev)
    moved = []
    for src in [content_review_path(rd, ref)] + sorted((rd / '20-analysis' / 'content').glob(f'{ref}-draft*')):
        if src.is_file():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest / src.name))
            moved.append(src.name)
    looks = rd / '20-analysis' / 'inspect' / ref
    if looks.is_dir() and any(looks.iterdir()):
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(looks), str(dest / 'inspect'))
        moved.append('inspect/')
    return {'archived_to': str(dest) if moved else None, 'moved': moved, 'revision': rev}


def content_exclusions(rd, ref):
    """[(from_s, to_s, segment id, kind, action)] of a reference's reviewed content: an excluded segment with the
    moments that depend on it, and a segment whose visuals are restricted."""
    doc = read_json(content_review_path(rd, ref))
    out = []
    for s in doc.get('segments') or []:
        if s.get('action') not in ('exclude', 'restrict_visuals'):
            continue
        a, b_ = parse_clock(s.get('from')), parse_clock(s.get('to'))
        if a is None or b_ is None:
            continue
        out.append((a, b_, str(s.get('id')), str(s.get('kind')), str(s.get('action'))))
        if s.get('action') == 'exclude':
            for d in s.get('depends') or []:
                da, db = parse_clock(d.get('from')), parse_clock(d.get('to'))
                if da is not None and db is not None:
                    out.append((da, db, str(s.get('id')), str(s.get('kind')), 'exclude'))
    return out


def excluded_themes(rd, video):
    """What a video must not bring back: the excluded segments of the references its direction cites, and what a
    restricted segment's `avoid` says must never be shown (its subject may still be told)."""
    d = read_json(video_dir(rd, video) / 'direction.json')
    ev = d.get('evidence') if isinstance(d.get('evidence'), dict) else {}
    out = []
    for ref in dict.fromkeys(str(x).strip().upper() for x in ev.get('references') or []):
        for s in read_json(content_review_path(rd, ref)).get('segments') or []:
            avoid = [str(x) for x in s.get('avoid') or [] if str(x).strip()]
            if s.get('action') == 'exclude' or (s.get('action') == 'restrict_visuals' and avoid):
                out.append({'theme': f'{ref}/{s.get("id")}', 'kind': s.get('kind'), 'what': s.get('what'),
                            'avoid': avoid, 'label': 'excluded_theme' if s.get('action') == 'exclude' else 'restricted_theme'})
    return out


def _theme_tokens(phrase):
    return [w for w in re.findall(r"[a-z0-9']+", str(phrase).lower()) if len(w) > 2 and w not in _THEME_STOP]


def theme_hits(text, themes):
    """[(theme, phrase)]: an avoid phrase whose every content word is in the text (any order, a plural too). A net
    for plain re-use only: a disguised version in other words is the reviewers' to catch (their packets list these)."""
    words = set(re.findall(r"[a-z0-9']+", strip_tags(str(text or '')).lower()))
    out = []
    for th in themes:
        for ph in th.get('avoid') or []:
            toks = _theme_tokens(ph)
            if toks and all(w in words or w + 's' in words or w + 'es' in words or
                            (w.endswith('s') and w[:-1] in words) for w in toks):
                out.append((f"{th.get('label') or 'excluded_theme'}:{th['theme']}", ph))
    return out


def prompt_flags(text, themes=()):
    """The content flags of a picture prompt: 02's words (swearing aside) and an excluded theme brought back."""
    plain = strip_tags(str(text or ''))
    kinds = [kind for kind, rx in CONTENT_FLAGS if kind != 'swearing' and rx.search(plain)]
    kinds += [label for label, _ in theme_hits(plain, themes)]
    return list(dict.fromkeys(kinds))


def prompt_flag_issues(prefix, kinds, note):
    """Issues for one picture prompt's flags. What a cited reference's content review rules out (excluded, or never
    shown) is rewritten out of the prompt: a note cannot answer it. 02's words can be plain (a blood-orange sky): a
    note of six words or more saying why it is not that content answers them, or the prompt is rewritten."""
    ruled_out = [k for k in kinds if k.startswith(('excluded_theme:', 'restricted_theme:'))]
    words = [k for k in kinds if k not in ruled_out]
    out = []
    if ruled_out:
        out.append(f'{prefix}_shows_what_a_content_review_rules_out_rewrite_it:' + '+'.join(ruled_out))
    if words and n_words(note) < 6:
        out.append(f'{prefix}_content_flag_unanswered:' + '+'.join(words))
    return out


def content_signals(rd, ref, row):
    """Where to look closer (gathered, never judged): stretches whose words touch 02's subjects, and the picture
    stretches the samples cannot settle (the av-profile's inspect_candidates)."""
    tj = read_json(rd / '10-media' / ref / 'transcript.json')
    hits = []
    for s in tj.get('segments') or []:
        for kind, rx in CONTENT_FLAGS:
            if kind == 'swearing':
                continue
            found = sorted({h.lower() for h in rx.findall(s.get('text') or '')})
            if found:
                hits.append({'from': _mmss(s.get('start_s')), 'to': _mmss(s.get('end_s')), 'kind': kind,
                             'words': found, 'said': str(s.get('text') or '')[:160]})
    prof = read_json(ref_av_path(rd, ref))
    fi = read_json(rd / '10-media' / ref / 'frame-index.json')
    return {'reference': ref, 'duration_s': row.get('duration_s'),
            'frames': {'count': len(fi.get('frames') or []), 'fps': fi.get('fps'), 'sampler': fi.get('sampler') or LEGACY_SAMPLER},
            'transcribed': tj.get('status') == 'transcribed', 'word_hits': hits[:120],
            'picture_candidates': prof.get('inspect_candidates') if prof else None,
            # which stretches were looked at closer, not why: a fresh or second review is not steered by the first
            'closer_looks_taken': [{k: x[k] for k in ('from_s', 'to_s', 'rate', 'frames')} for x in closer_looks(rd, ref)],
            'shot_sheets': (read_json(shot_sheets_dir(rd, ref) / 'index.json').get('sheets')
                            or 'not made yet: content-review --shot-sheets (one frame of every shot)'),
            'note': 'Places to look, not verdicts: a word can be plain fact, and something can be shown without a word '
                    'said. The review is your judgement of the whole video in context.'
                    + ('' if prof else ' Run av-profile for the picture candidates.')}


def cmd_content_review(args):
    """The content record: a reference's review (--ref with --file; --signals shows where to look first), the look at
    every picture a video's edit shows (--video with --pictures --file), or the run's state (--status)."""
    rd, st = run_folder(args)
    inv = read_json(rd / '00-inventory/references.json')
    rows = {x['id']: x for x in inv.get('items') or [] if x.get('kind') == 'video' and not x.get('duplicate_of')}
    if args.status:
        refs = {}
        for ref in rows:
            d = read_json(content_review_path(rd, ref))
            if not d:
                refs[ref] = 'not reviewed'
                continue
            segs = d.get('segments') or []
            refs[ref] = {'segments': len(segs),
                         **{k: sum(1 for s in segs if s.get('kind') == k) for k in CONTENT_KINDS},
                         'excluded': sum(1 for s in segs if s.get('action') == 'exclude'),
                         'restricted': sum(1 for s in segs if s.get('action') == 'restrict_visuals'),
                         'unsure': sum(1 for s in segs if s.get('confidence') == 'unsure'),
                         'story': (d.get('story_without_exclusions') or {}).get('status')}
        emit({'ok': True, 'reviewed': sum(1 for v in refs.values() if v != 'not reviewed'), 'references': len(rows),
              'by_reference': refs})
        return
    if args.video and args.pictures:
        if not args.file:
            error('Give the looks file: --file looks.json ({"looks": [{"file", "result": "clean"|"issue", "note"}]})')
        given = read_json(Path(args.file).expanduser().resolve(), required=True)
        looks = given.get('looks')
        if not isinstance(looks, list) or not looks:
            error('The looks file needs a "looks" list, one entry per picture looked at')
        ruled_out = excluded_themes(rd, args.video)
        if ruled_out and given.get('never_show_checked') is not True:
            error('Check every picture against what the cited references\' content reviews rule out, then confirm '
                  'with "never_show_checked": true in the looks file; a picture showing any of it is an issue.',
                  [f"{th['theme']}: {th['what']} (never: {', '.join(th['avoid'])})" for th in ruled_out])
        path = picture_looks_path(rd, args.video)
        data = read_json(path) or {'video': int(args.video), 'looks': {}}
        problems, saved = [], 0
        for k, lk in enumerate(looks, 1):
            f = _run_file(rd, (lk or {}).get('file'))
            if not f.is_file():
                problems.append(f'look_{k}_file_not_found:{f}')
                continue
            res = str(lk.get('result') or '')
            if res not in ('clean', 'issue'):
                problems.append(f'look_{k}_result_must_be_clean_or_issue')
            if n_words(lk.get('note')) < 3:
                problems.append(f'look_{k}_note_must_say_what_the_picture_shows')
            if res == 'issue' and str(lk.get('category') or '') not in SAFETY_CATEGORIES + CONTENT_KINDS[1:] + ('excluded_theme',):
                problems.append(f'look_{k}_an_issue_needs_its_category')
            if not problems:
                data['looks'][_pkey(f)] = {'file': str(f), 'sha256': file_sha256(f), 'result': res,
                                           'note': lk.get('note'), 'category': lk.get('category'), 'looked_at': now(),
                                           'never_show_checked': bool(ruled_out)}
                saved += 1
        if problems:
            error('The looks file does not follow the format; nothing was recorded.', problems)
        write_json(path, data)
        emit({'ok': True, 'recorded': saved, 'file': str(path),
              'issues_open': sum(1 for x in data['looks'].values() if x.get('result') == 'issue')})
        return
    if not args.ref:
        error('Name a reference (--ref V###), or --video N --pictures, or --status')
    ref = args.ref.strip().upper()
    row = rows.get(ref)
    if not row:
        error('No such reference video in this run', ref)
    if args.signals:
        emit({'ok': True, **content_signals(rd, ref, row)})
        return
    if args.archive:
        moved = archive_content_review(rd, ref)
        emit({'ok': True, 'reference': ref, **moved,
              'note': 'A blind review now starts from the source evidence only (frames, transcript, watch and shot '
                      'sheets, measurements). Its brief never names the archive.'})
        return
    if args.shot_sheets:
        made = make_shot_sheets(rd, ref)
        emit({'ok': True, 'reference': ref, **made,
              'note': 'Open every sheet: each shot of the video once, at its frame\'s time (the watch sheets show a '
                      'frame every 5 s and can step over a short shot).'})
        return
    if not args.file:
        error('Give the review: --file review.json (see 07 for its fields), or --signals for where to look first')
    doc = read_json(Path(args.file).expanduser().resolve(), required=True)
    issues, segs = content_review_issues(rd, ref, doc, row)
    if issues:
        error('The content review is not complete; nothing was saved.', issues)
    target = content_review_path(rd, ref)
    old = read_json(target)
    fi = read_json(rd / '10-media' / ref / 'frame-index.json')
    saved = {**doc, 'reference_id': ref, 'revision': max(int(old.get('revision') or 0), archived_revision(rd, ref)) + 1,
             'made_at': now(),
             'frames_seen': {'fps': fi.get('fps'), 'sampler': fi.get('sampler') or LEGACY_SAMPLER,
                             'count': len(fi.get('frames') or [])},
             'closer_looks': closer_looks(rd, ref),
             'shot_sheets': len(read_json(shot_sheets_dir(rd, ref) / 'index.json').get('sheets') or [])}
    saved['review_sha256'] = canonical_sha({k: v for k, v in saved.items() if k not in ('made_at', 'review_sha256')})
    write_json(target, saved)
    emit({'ok': True, 'file': str(target), 'revision': saved['revision'], 'segments': len(segs),
          'excluded': sum(1 for s in segs if s['action'] == 'exclude'),
          'restricted': sum(1 for s in segs if s['action'] == 'restrict_visuals'),
          'kinds': {k: sum(1 for s in segs if s['kind'] == k) for k in CONTENT_KINDS}})


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


CUE_PAUSE_TOLERANCE = (0.3, 0.25)
CUE_MOVES = {'volume': ('speech_level_db', 1.0, 'dB'), 'tempo': ('speech_rate_wpm', 0.05, 'share'),
             'energy': ('pitch_range_st', 1.0, 'st')}


def cue_poles(inner):
    """The delivery axes a cue asks to move, and which way: '[quietly, slowly]' -> {'volume': 'low', 'tempo': 'slow'}."""
    text = ' ' + ' '.join(tag_qualities(inner)) + ' '
    words = set(re.findall(r"[a-z']+", text))
    out = {}
    for axis, poles in contrast_axes().items():
        hit = [pole for pole, terms in poles.items()
               if any((' ' + t + ' ' in text) if ' ' in t else (t in words) for t in terms)]
        if len(hit) == 1:
            out[axis] = hit[0]
    return out


def pause_cue_outcome(planned_s, measured_s):
    """A performed pause is judged on its length, never on where it falls in time: achieved within max(0.3 s, 25 %) of
    the whole silence planned. The model's timing can't be steered to the millisecond; close is a success."""
    if planned_s is None or measured_s is None:
        return None
    tol = max(CUE_PAUSE_TOLERANCE[0], CUE_PAUSE_TOLERANCE[1] * float(planned_s))
    d = float(measured_s) - float(planned_s)
    return {'planned_s': round(float(planned_s), 2), 'measured_s': round(float(measured_s), 2),
            'tolerance_s': round(tol, 2), 'outcome': 'achieved' if abs(d) <= tol else 'short' if d < 0 else 'long'}


def delivery_cue_outcome(inner, line_stats, usual):
    """Whether a delivery cue moved its line the way it asked, against this take's usual line: volume by the speech
    level, tempo by the speaking rate, energy by the pitch range. Under the step it is no clear change, the wrong way it
    is opposite. A cue on none of these axes ([curious], [deadpan] aside) is listened to, not judged here."""
    poles = cue_poles(inner)
    if not poles:
        return {'outcome': 'not_measured', 'note': 'a cue on no measured axis (volume, energy, tempo): listen'}
    rows = []
    for axis, pole in poles.items():
        key, step, kind = CUE_MOVES[axis]
        v, u = (line_stats or {}).get(key), (usual or {}).get(key)
        if v is None or u is None:
            rows.append({'axis': axis, 'asked': pole, 'outcome': 'not_measured', 'note': 'too short to measure'})
            continue
        need = step * u if kind == 'share' else step
        moved = (u - v) if pole in ('low', 'slow') else (v - u)
        rows.append({'axis': axis, 'asked': pole, 'measure': key, 'line': v, 'usual': round(u, 2),
                     'change': round(v - u, 2), 'step': round(need, 2),
                     'outcome': 'as_asked' if moved >= need else 'opposite' if moved <= -need else 'no_clear_change'})
    outs = {r['outcome'] for r in rows}
    overall = ('as_asked' if outs == {'as_asked'} else 'opposite' if 'opposite' in outs else
               'not_measured' if outs == {'not_measured'} else 'no_clear_change' if 'no_clear_change' in outs
               else 'partly')
    return {'outcome': overall, 'axes': rows}


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


def pronunciation_facts(rd, video, lines, data=None):
    """The episode's pronunciation list (40-plans/video-NN/pronunciation.json, or `data` given directly, as a trial
    plan carries its own): the names and terms this voice may say wrong, each in a form Eleven v4 documents (IPA
    between slashes, or a respelling), where that pronunciation comes from and how sure it is. Only what is sent
    changes: the script and the captions keep the canonical spelling. An uncertain entry is flagged for listening,
    never treated as settled."""
    p = pronunciation_path(rd, video)
    out = {'file': str(p) if data is None else '(given)', 'issues': [], 'warnings': [], 'terms': [], 'uses': {}}
    if data is None:
        if not p.is_file():
            return out
        d = read_json(p)
        if not d:
            out['issues'].append('pronunciation_file_unreadable')
            return out
    else:
        d = data if isinstance(data, dict) else {}
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
        out['terms'].append({'term': term, 'say': say, 'how': how, 'confidence': conf, 'rx': rx,
                             'source': str(t.get('source') or '').strip() or None})
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
        cr = read_json(content_review_path(rd, v))
        if not cr:
            iss.append(f'direction_evidence_reference_without_content_review:{v}')
        elif (cr.get('story_without_exclusions') or {}).get('status') == 'too_dependent':
            warn.append(f'{v}: its story depends on material excluded from use (content review): cite how it is told '
                        '(pace, hooks, structure, picture), never its story')
    cut = {v: content_exclusions(rd, v) for v in refs}
    for o in ev.get('observations') or []:
        if not isinstance(o, dict):
            continue
        v = str(o.get('ref') or '').strip().upper()
        a, b_ = parse_span(o.get('at'))
        if a is None:
            continue
        for lo, hi, sid, kind, action in cut.get(v) or content_exclusions(rd, v):
            if a <= hi and b_ >= lo:
                if action == 'exclude' and n_words(o.get('borrows_only')) >= 6:
                    warn.append(f'{v}@{o.get("at")} is inside excluded {sid}, cited only for: {o.get("borrows_only")} '
                                '(never the excluded material itself)')
                elif action == 'exclude':
                    iss.append(f'direction_cites_excluded_material:{v}@{o.get("at")}:{sid}({kind})')
                else:
                    warn.append(f'{v}@{o.get("at")} is inside {sid}, whose visuals are restricted: borrow how it is '
                                'told, never what it shows')
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
            iss += prompt_flag_issues(f'item_{i}_prompt', prompt_flags(it.get('prompt'), excluded_themes(rd, n)),
                                      it.get('content_note'))
            out['records'].append({'purpose': 'treatment_preview', 'treatment': str(it.get('treatment')), 'moment': m})
        out['ok'] = not iss
        return out
    gate, lock, _ = direction_gate(rd, n)
    iss += gate
    rev, treatment = lock.get('production_rev', 1), lock.get('treatment')
    chosen = chosen_treatment_of(read_json(video_dir(rd, n) / 'direction.json'))
    if purpose == 'thumbnail':
        out['untracked'] = True
        themes = excluded_themes(rd, n)
        for i, it in enumerate(items, 1):
            if n_words(it.get('prompt')) < 8:
                iss.append(f'item_{i}_missing_prompt')
            iss += prompt_flag_issues(f'item_{i}_prompt', prompt_flags(it.get('prompt'), themes), it.get('content_note'))
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
        themes_now = excluded_themes(rd, n)
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
            # style words added around the approved frame prompt may not bring in what the prompt itself doesn't
            extra = [k for k in prompt_flags(it.get('prompt'), themes_now)
                     if k not in prompt_flags(s.get('frame_prompt') or s.get('prompt'), themes_now)]
            iss += prompt_flag_issues(f'item_{i}_style_words', extra, it.get('content_note'))
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
    """Realised pauses changed since the last script read, counted against what that reader was shown, so a run of
    small edits adds up instead of each passing on its own: (lines added, removed, realised another way or moved by
    half a second or more; seconds moved in all, every change counted however small)."""
    changed, moved = [], 0.0
    for lid in dict.fromkeys(list(seen) + list(now_holds)):
        a, b = seen.get(lid), now_holds.get(lid)
        sa, sb = (float(a[0]) if a else 0.0), (float(b[0]) if b else 0.0)
        moved += abs(sa - sb)
        if (a is None) != (b is None) or abs(sa - sb) >= 0.5 or (a and b and a[1] != b[1]):
            changed.append(lid)
    return changed, round(moved, 2)


def key_moment_lines(vd, line_ids):
    """The changed lines that sit in a beat where a held silence shapes the film whatever its size: the opening (the
    first beat: the hook), the ending (the last beat) and any beat the beat map marks `key_moment` (a reveal, the
    climax, an emotional turn: the agents' own mark). {line: why}."""
    lines = read_json(vd / 'script.json').get('lines') or []
    index = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
    beats = read_json(vd / 'beat-map.json').get('beats') or []
    out = {}
    for lid in line_ids:
        k = index.get(lid)
        for bi, b in enumerate(beats):
            try:
                lo, hi = int(b['line_start']), int(b['line_end'])
            except (KeyError, TypeError, ValueError):
                continue
            if k is None or not lo <= k <= hi:
                continue
            why = ('the opening' if bi == 0 else 'the ending' if bi == len(beats) - 1 else
                   f'a key moment ({str(b.get("key_moment")).strip()})' if str(b.get('key_moment') or '').strip()
                   and b.get('key_moment') is not False else None)
            if why:
                out[lid] = f'{b.get("id") or "beat " + str(bi + 1)}: {why}'
            break
    return out


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
            lim_lines, lim_s, lim_share = HOLDS_SMALL_CHANGE
            target = read_json(vd / 'length-lock.json').get('target_length_s') or 0
            keys = key_moment_lines(vd, ch)
            small = len(ch) <= lim_lines and moved <= max(lim_s, lim_share * target)
            if keys:
                # The hook, the ending and a marked key moment are read again after any real hold change there.
                st['issues'].append('holds_changed_in_a_key_moment_after_the_script_read:' + ','.join(
                    f'{lid} ({why})' for lid, why in list(keys.items())[:8]) + ('...' if len(keys) > 8 else ''))
            if (ch or moved > 0) and not small:
                st['issues'].append(f'holds_changed_after_the_script_read:{moved:g}s:' + ','.join(ch[:12])
                                    + ('...' if len(ch) > 12 else ''))
            elif moved > 0 and not keys:
                st['warnings'].append(f'held silences changed after the last read on {len(ch)} line(s), '
                                      f'{moved:g} s in all since that read (small enough to pass): '
                                      + (','.join(ch) or 'changes under half a second'))
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
    out = {'ready': False, 'issues': [], 'warnings': [], 'shots': 0, 'content_flags': []}
    if not plan:
        out['issues'].append('shot_plan_missing')
        return out
    themes = excluded_themes(rd, n)
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
        if not s.get('reuses'):
            kinds = prompt_flags(s.get('frame_prompt') or s.get('prompt'), themes)
            if kinds:
                found = prompt_flag_issues(f'shot_{sid}_prompt', kinds, s.get('content_note'))
                out['content_flags'].append({'shot': sid, 'kinds': kinds, 'open': found})
                out['issues'] += found
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
    # The silence the edit holds add: decided ones as decided (whole silence less the voice's measured gap there),
    # provisional ones estimated the same way. Never the proposal's whole length on top of the voice's own gap.
    hf = hold_facts(rd, video, lines) if lines else {'holds': [], 'added_s': 0.0, 'voice_gaps': {}, 'undecided': [],
                                                     'decided_narration': [], 'decided_picture': []}
    holds = hf['added_s']
    review = vd / 'editorial-review.md'
    review_text = review.read_text(encoding='utf-8', errors='replace') if review.exists() else ''
    flags, flag_issues = content_flags(lines, review_text, excluded_themes(rd, video))
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
    # Each cue as a band (its own evidence named): the forecast is a range wherever the evidence is limited, and
    # several cues in one passage are not assumed to add up exactly (05).
    tag_bands = [{**tag_estimate(t['tag'], t.get('category'), measured), 'line': t['line']} for t in tags]
    tag_low = round(sum(b['low_s'] for b in tag_bands), 2)
    tag_high = round(sum(b['high_s'] for b in tag_bands), 2)
    # A delivery cue colours the rest of its own line (every script line is sent on its own text line): the line
    # names the words it should colour and where the delivery returns (cue_scope), so a local change stays local.
    by_lid = {str(r.get('id') or f'L{i + 1:03d}'): r for i, r in enumerate(lines)}
    issues += [f'tag_{lid}_needs_its_scope' for lid in
               sorted({t['line'] for t in tags if t.get('category') != 'pause'})
               if n_words((by_lid.get(lid) or {}).get('cue_scope')) < 3]
    # A pause cue goes before the words that follow the silence: ElevenLabs "Place a tag before the words it affects",
    # and their examples put it before the next words or on its own line. At a line's end it is undocumented; one
    # measured there (eleven_v4, 2026-11-22) left about 0.2 s over the voice's usual gap.
    warnings += [f'{lid}: a pause cue at the end of the line; ElevenLabs places a tag before the words it affects: put it '
                 'at the start of the next line, before the words after the silence'
                 for lid in sorted({t['line'] for t in tags if t.get('category') == 'pause' and t.get('at_line_end')})]
    pace = float(script.get('pace_wpm') or lock.get('pace_wpm') or 0)
    if not pace:
        issues.append('script_missing_narration_pace')
    target = lock['target_length_s']
    # Narration = spoken words at a pace + the voice's natural gap after every line + what the tags add.
    # A pause the story wants longer than the voice's own gap there exists only if it is realised (pause_via): a tag
    # (inside the narration) or an edit hold, which adds only the difference between the whole silence wanted and the
    # gap the voice left (`holds`). Planned pauses are never sent to ElevenLabs.
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
    # Held silence never stands in for story, and never makes the length. The content is the narration with the voice's
    # own gaps and its delivery tags; the silence is what the edit holds add plus what pause tags perform. When the
    # content alone falls short of the window and the silence is what reaches it, the length is being padded: blocked.
    # The answer is the story (more substance, or an authorised length revision), never longer silences.
    band = max(4, target * lock.get('tolerance_export_pct', .025)) if real is not None else max(10, .08 * target)
    pause_tag_s = round(sum(tag_cost_s(t['tag'], measured.get('tag_costs_s')) for t in tags
                            if t.get('category') == 'pause'), 2)
    narr = real_narr if real_narr is not None else (round(early_narr, 2) if pace else None)
    content_s = round(narr - pause_tag_s, 2) if narr is not None else None
    carried = round(max(0.0, (target - band) - content_s), 1) if content_s is not None else None
    if carried and content_s + pause_tag_s + holds >= target - band:
        issues.append(f'runtime_reached_with_held_silence:{carried:g}s:the_words_alone_fall_short_of_the_length')
    ref_pp = [p for p in (lock.get('reference_pause_profiles') or {}).values() if p]
    edit_holds = [p for p in pause_plan if p['via'] == 'edit']
    holds_info = {'edit_holds': len(edit_holds), 'edit_holds_s': holds,
                  'tag_pauses': sum(1 for p in pause_plan if p['via'] == 'tag'), 'pause_tag_s': pause_tag_s,
                  'share_of_runtime': round(holds / target, 3) if target else None,
                  'content_forecast_s': content_s, 'runtime_carried_by_holds_s': carried,
                  'longest_added_s': max((h.get('added_s') or 0 for h in hf['holds']), default=0),
                  'undecided': hf['undecided'], 'decided_after_narration': hf['decided_narration'],
                  'decided_with_picture': hf['decided_picture'], 'voice_gaps': hf['voice_gaps'],
                  'each': [{k: h.get(k) for k in ('line', 'beat', 'status', 'natural_gap_s', 'added_s',
                                                   'added_is_estimate', 'total_s')} for h in hf['holds']],
                  'references_longest_pause_s': max((p.get('longest_pause_s') or 0 for p in ref_pp), default=None),
                  'references_pauses_1_5s_plus_per_min': round(statistics.mean(
                      [p['pauses_1_5s_plus_per_min'] for p in ref_pp if p.get('pauses_1_5s_plus_per_min') is not None]), 2)
                  if any(p.get('pauses_1_5s_plus_per_min') is not None for p in ref_pp) else None}
    older = [p['line'] for p in pause_plan if p['form'] == 'added']
    if older:
        warnings.append('pauses in the older form (pause_after_s: silence added on top of the voice\'s own gap): '
                        + ','.join(older) + '. Each is decided against the recorded voice (holds, hold-decide) before '
                        'the edit; a new script writes pause_total_s, the whole silence wanted')
    warnings += hold_signals(pause_plan)
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
            'audio_tags': tags, 'tag_time_s': tag_s, 'tag_time_range_s': [tag_low, tag_high], 'tag_estimates': tag_bands, 'pause_plan': pause_plan, 'edit_holds_s': holds,
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
            'real_forecast_range_s': ([round(real - (tag_s - tag_low), 2), round(real + (tag_high - tag_s), 2)]
                                      if real is not None else None),
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
# A part that follows the beat map's chapters (beats marked chapter_start) may hold a whole chapter up to this size:
# one request of ~7,000 characters took ~95 s here (measured ~75 characters a second), well inside the 180 s wait.
PART_CHAPTER_MAX = 7000


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
        pause_len = lambda row: float(row.get('pause_total_s') or row.get('pause_after_s') or 0)   # either form
        j = max(near, key=lambda x: (pause_len(lines[x[0] - 1]) > NATURAL_PAUSE_MAX_S,
                                     pause_len(lines[x[0] - 1]) > 0, -abs(x[1] - goal)))[0]
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
    # The story's own chapters, when the beat map marks them: a recording boundary sits only where the story itself
    # starts again, so the narrator's fresh start (and the previous part's last landing) falls where one belongs (05).
    starts = {str(b.get('id')) for b in beats or [] if b.get('chapter_start')}
    if starts:
        chapters = []
        for lo, hi, bid in spans:
            if not chapters or bid in starts:
                chapters.append([])
            chapters[-1].append((lo, hi, bid))
        out = []
        for ch in chapters:
            lo, hi = ch[0][0], ch[-1][1]
            size = sum(sizes[lo - 1:hi])
            if size <= min(PART_CHAPTER_MAX, hard_max):
                out.append({'line_start': lo, 'line_end': hi, 'beats': [b for _, _, b in ch], 'chapter': True,
                            'text': '\n'.join(str(r['text']).strip() for r in lines[lo - 1:hi])})
            else:          # a chapter too long for one request: split between its beats (flagged, listened to)
                sub = chunks_for_beats(lines[lo - 1:hi], [{'id': b, 'line_start': a - lo + 1, 'line_end': z - lo + 1}
                                                          for a, z, b in ch], target, hard_max)
                for c in sub:
                    out.append({**c, 'line_start': c['line_start'] + lo - 1, 'line_end': c['line_end'] + lo - 1,
                                'chapter': False, 'split_inside_chapter': True})
        return out
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
    """Credits this account was really billed per character sent on this model, from the ledger: ElevenLabs'
    character-cost header where the request has one (measured 2026-11-20: it equals the balance drop, which shows
    up only some seconds later), else the balance drop (other use of the account between the two balance reads can
    only push it up): (median, number of requests)."""
    ratios = []
    for r in ledger_rows(rd):
        if r.get('model_id') != model_id or r.get('kind') not in ('tts', 'probe', 'trial') or not r.get('ok') \
                or not r.get('characters') or r.get('phase') == 'pending':
            continue
        c = r.get('character_cost_header')
        if c is None and isinstance(r.get('delta'), (int, float)) and r['delta'] > 0:
            c = r['delta']
        if isinstance(c, (int, float)) and c >= 0:
            ratios.append(c / r['characters'])
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
    day (max_age_h=0 reads it again now: a trial checks the price before every request). A model the account doesn't
    list, or one without a reported cost, stops everything before a paid call."""
    cache = rd / 'logs' / 'elevenlabs-models.json'
    c = read_json(cache)
    try:
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(c['fetched_at'])).total_seconds()
    except (KeyError, TypeError, ValueError):
        age = None
    if age is None or age > max_age_h * 3600 or max_age_h <= 0 or model_id not in (c.get('models') or {}):
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
           'expected_credits': expected,
           'expected_credits_verified': math.ceil(characters * measured) if measured is not None else None, 'safety_factor': safety, 'keep_credits': int(keep or 0),
           'required_available': required, 'available': bal['available'],
           'left_after_expected': bal['available'] - expected, 'next_reset_unix': bal['next_reset_unix'],
           'max_characters_per_request': rates['maximum_text_length_per_request']}
    if bal['available'] < required:
        error(f'Not enough ElevenLabs credits for {label}: nothing was sent.', out)
    return out


def eleven_paid_post(rd, key, path, body, kind, meta, accept='audio/mpeg', timeout=180, require=0, max_credits=None):
    """One billed ElevenLabs request, on record: the live balance just before and just after (free calls), the
    characters sent (the text, and the context fields apart) and what the account was billed, appended to the ledger
    whether it worked or not. A 'pending' row goes in first, so a request cut off by a crash or a power cut is still
    on record (a trial budget counts it at its largest possible charge). The cost: ElevenLabs' `character-cost` reply
    header (documented under "Tracking generation costs"; measured 2026-11-20 on eleven_v4: it is the credits billed,
    the balance falling by exactly that some seconds later), and the balance drop read just after (often 0, since the
    balance lags). When `meta` names credits_per_character, `credits_billed` is the header, else a balance drop seen,
    else unknown (a trial budget then counts the request at its largest possible charge). When the balance just
    before is under `require`, nothing is sent. Returns (raw bytes or None, error or None, entry)."""
    before = subscription_balance(key)
    chars = len(str(body.get('text') or ''))
    ctx = len(str(body.get('previous_text') or '')) + len(str(body.get('next_text') or ''))
    attempt = hashlib.sha256(f'{now()}|{os.getpid()}|{path}|{chars}|{id(body)}'.encode('utf-8')).hexdigest()[:16]
    entry = {'at': now(), 'kind': kind, **meta, 'characters': chars, 'context_characters': ctx,
             'balance_before': before['available'], 'attempt_id': attempt}
    if max_credits is not None:
        entry['max_credits'] = int(max_credits)
    if before['available'] < require:
        return None, f'not sent: {before["available"]} credits left, this request needs {require}', None
    ledger_add(rd, {**entry, 'phase': 'pending'})
    req = urllib.request.Request('https://api.elevenlabs.io' + path, data=json.dumps(body).encode('utf-8'),
                                 method='POST', headers={'xi-api-key': key, 'Content-Type': 'application/json',
                                                         'Accept': accept})
    raw, err, rid, cost, trace, hist = None, None, None, None, None, None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            hdrs = getattr(resp, 'headers', None)
            if hdrs is not None:
                rid, trace, hist = hdrs.get('request-id'), hdrs.get('x-trace-id'), hdrs.get('history-item-id')
                cost = hdrs.get('character-cost')
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        err = f'{type(exc).__name__}: {str(exc)[:240]}'
    try:
        after = subscription_balance(key)['available']
    except RuntimeError:
        after = None
    try:
        cost = int(float(cost)) if cost not in (None, '') else None
    except (TypeError, ValueError):
        cost = None
    delta = (before['available'] - after) if after is not None else None
    entry.update({'phase': 'done', 'ok': err is None, 'error': err, 'request_id': rid, 'trace_id': trace,
                  'history_item_id': hist, 'character_cost_header': cost, 'balance_after': after, 'delta': delta})
    if meta.get('credits_per_character') is not None:
        entry['credits_billed'] = cost if cost is not None else (
            delta if isinstance(delta, (int, float)) and delta > 0 else None)
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


# ---------------------------------------------------------------- controlled calibration trials
TRIAL_VARIABLES = ('passage', 'voice_id', 'model_id', 'stability', 'similarity_boost', 'tags', 'pronunciation',
                   'context')
# What each take's numbers can and cannot carry: written into every take's record and into the answer key.
TRIAL_UNCERTAINTIES = [
    'one take per set-up: Eleven v4 varies from take to take, so a difference between two takes can be the setting or '
    'chance; only a repeat of the same request shows how much one set-up varies by itself',
    'Whisper medium word times are good to about a tenth of a second: so are the pauses and the pace',
    'pace on a passage of 30-70 words moves several words a minute with one pause more or less',
    'pitch is tracked per word (pyin) over a short sample: a range or movement is indicative, and a lower figure can be '
    'the right, quieter delivery for the moment',
    'loudness is each file\'s own (EBU R128); ElevenLabs levels each take by itself, so a level step between takes can '
    'come from that, not from the delivery',
    'none of these numbers says which take sounds better or more human: that is for the listener']
TRIAL_LISTEN_ITEMS = [
    ('natural', 'sounds like a person, not a reading'), ('flow', 'conversational flow'),
    ('charisma', 'vocal charisma: a voice you lean in to'), ('expressive', 'expressiveness'),
    ('fit', 'right for this moment of the story'), ('theatrical', 'too theatrical (which one is MORE)'),
    ('monotone', 'monotonous (which one is MORE)'), ('pauses', 'pauses where a person would pause'),
    ('pronunciation', 'names and words said right'), ('continuity', 'continuous with what comes before and after'),
    ('enjoyment', 'enjoyable to listen to'), ('keep', 'makes you want to keep listening for twenty minutes')]


def trial_plan_facts(plan, vf, lines, pron):
    """A trial plan, checked before anything is priced: passages (script lines of this video, or a short text), each
    with the delivery it is meant to have (`intended_delivery`), the variants (each variable set explicitly or taken
    from the voice lock), the runs pairing them, the questions, and the user's spending cap (`budget`: {id,
    max_credits}). Every run answers a question, and every question compares runs that differ in exactly one
    variable, so each answer can be read: two changes at once can't be told apart."""
    issues = []
    pid = str(plan.get('id') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,40}', pid):
        issues.append('trial_id_must_be_lowercase_letters_digits_and_dashes')
    budget = plan.get('budget') if isinstance(plan.get('budget'), dict) else {}
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,60}', str(budget.get('id') or '')) or not isinstance(
            budget.get('max_credits'), int) or isinstance(budget.get('max_credits'), bool) or budget['max_credits'] <= 0:
        issues.append('trial_needs_its_budget: {"id": "...", "max_credits": N}, the credits the user authorised for '
                      'these trials (every plan under the same id shares them)')
    index = {str(r.get('id') or f'L{i + 1:03d}'): i for i, r in enumerate(lines)}
    passages = {}
    for p in plan.get('passages') or []:
        k = str((p or {}).get('id') or '')
        if not k or k in passages or '-' in k:
            issues.append(f'passage_{k or "unnamed"}_needs_a_unique_id_without_dashes')
            continue
        text, rng, ids = None, None, None
        if p.get('lines'):
            m = re.fullmatch(r'\s*(L\d+)\s*(?:-\s*(L\d+))?\s*', str(p['lines']))
            if not m or m.group(1) not in index or (m.group(2) and m.group(2) not in index):
                issues.append(f'passage_{k}_names_lines_the_script_does_not_have')
            else:
                lo, hi = index[m.group(1)], index[m.group(2) or m.group(1)]
                if hi < lo:
                    issues.append(f'passage_{k}_lines_run_backwards')
                else:
                    rng = (lo + 1, hi + 1)
                    text = '\n'.join(str(r.get('text') or '').strip() for r in lines[lo:hi + 1])
                    ids = [str(r.get('id') or f'L{lo + j + 1:03d}') for j, r in enumerate(lines[lo:hi + 1])]
        elif p.get('text'):
            text = str(p['text']).strip()
        if not text or len(strip_tags(text)) < 20:
            issues.append(f'passage_{k}_needs_its_lines_or_a_text')
            text = text or ''
        if n_words(p.get('moment')) < 1:
            issues.append(f'passage_{k}_names_its_moment')
        if n_words(p.get('intended_delivery')) < 3:
            issues.append(f'passage_{k}_says_its_intended_delivery')
        issues += script_markup([{'id': f'passage_{k}', 'text': text}])[0]
        passages[k] = {'text': text, 'lines': rng, 'line_ids': ids, 'moment': p.get('moment'), 'why': p.get('why'),
                       'intended_delivery': p.get('intended_delivery'), 'lines_label': p.get('lines')}
    variants = {}
    for v in plan.get('variants') or []:
        k = str((v or {}).get('id') or '')
        if not k or k in variants or '-' in k:
            issues.append(f'variant_{k or "unnamed"}_needs_a_unique_id_without_dashes')
            continue
        voice = str(v.get('voice_id') or 'lock')
        voice_id = vf['voice_id'] if voice == 'lock' else voice
        if not voice_id:
            issues.append(f'variant_{k}_has_no_voice: there is no voice lock to stand for "lock"')
        model = v.get('model_id') or (vf['model_id'] if vf['lock'] else 'eleven_v4')
        if model not in TTS_MODELS:
            issues.append(f'variant_{k}_model_must_be:' + '/'.join(TTS_MODELS))
        settings = {x: v.get(x, (vf['settings'] or {}).get(x)) for x in VOICE_SETTING_KEYS}
        issues += [f'variant_{k}_{x}' for x in voice_settings_issues(settings)]
        tags = str(v.get('tags') or 'as_written')
        if tags not in ('as_written', 'none'):
            issues.append(f'variant_{k}_tags_must_be:as_written/none')
        ctx = str(v.get('context') or 'none')
        if ctx not in ('none', 'neighbours'):
            issues.append(f'variant_{k}_context_must_be:none/neighbours')
        variants[k] = {'voice_id': voice_id, 'model_id': model, **settings, 'tags': tags,
                       'pronunciation': bool(v.get('pronunciation', True)), 'context': ctx}
    runs = []
    for r in plan.get('runs') or []:
        pk, vk = (str(r[0]), str(r[1])) if isinstance(r, (list, tuple)) and len(r) == 2 else (None, None)
        if pk not in passages or vk not in variants:
            issues.append(f'run_{pk}_{vk}_names_an_unknown_passage_or_variant')
        elif (pk, vk) in runs:
            issues.append(f'run_{pk}_{vk}_listed_twice')
        else:
            runs.append((pk, vk))
    asked, questions = set(), []
    for q in plan.get('questions') or []:
        qid = str((q or {}).get('id') or '')
        cmp_ = [(str(x[0]), str(x[1])) for x in q.get('compare') or [] if isinstance(x, (list, tuple)) and len(x) == 2]
        if n_words(q.get('asks')) < MIN_NOTE_WORDS:
            issues.append(f'question_{qid}_must_say_what_it_asks')
        if len(cmp_) < 2 or any(x not in runs for x in cmp_):
            issues.append(f'question_{qid}_compares_runs_not_in_the_plan')
            continue
        def val(run, k):
            return run[0] if k == 'passage' else variants[run[1]][k]
        diffs = sorted({k for a in cmp_ for b in cmp_ for k in TRIAL_VARIABLES if val(a, k) != val(b, k)})
        if q.get('repeat'):
            # The same request twice: how much one set-up varies by itself, the yardstick for every other answer.
            if diffs:
                issues.append(f'question_{qid}_is_a_repeat_but_changes:' + ','.join(diffs))
        elif len(diffs) != 1:
            issues.append(f'question_{qid}_changes_{len(diffs)}_things_at_once:' + (','.join(diffs) or 'nothing'))
        questions.append({'id': qid, 'asks': q.get('asks'), 'compare': cmp_, 'varies': diffs,
                          'listen_for': q.get('listen_for'), 'repeat': bool(q.get('repeat'))})
        asked |= set(cmp_)
    joins = []
    for j in plan.get('joins') or []:
        jid = str((j or {}).get('id') or '')
        parts, cmpv = [str(x) for x in j.get('parts') or []], [str(x) for x in j.get('compare') or []]
        if len(parts) != 2 or len(cmpv) < 2 or any(x not in passages for x in parts) or any(x not in variants for x in cmpv):
            issues.append(f'join_{jid}_needs_two_passages_and_the_variants_it_compares')
            continue
        pa, pb = passages[parts[0]], passages[parts[1]]
        if not (pa['lines'] and pb['lines'] and pa['lines'][1] + 1 == pb['lines'][0]):
            issues.append(f'join_{jid}_passages_must_be_consecutive_script_lines')
        need = [(x, v) for v in cmpv for x in parts]
        missing = [f'{x}-{v}' for x, v in need if (x, v) not in runs]
        if missing:
            issues.append(f'join_{jid}_needs_runs:' + ','.join(missing))
        jd = sorted({k for x in cmpv for y in cmpv for k in TRIAL_VARIABLES if k != 'passage'
                     and variants[x][k] != variants[y][k]})
        if len(jd) != 1:
            issues.append(f'join_{jid}_changes_{len(jd)}_things_at_once:' + (','.join(jd) or 'nothing'))
        if n_words(j.get('asks')) < MIN_NOTE_WORDS:
            issues.append(f'join_{jid}_must_say_what_it_asks')
        joins.append({'id': jid, 'parts': parts, 'compare': cmpv, 'varies': jd, 'asks': j.get('asks'),
                      'listen_for': j.get('listen_for')})
        asked |= set(need)
    issues += [f'run_{a}_{b}_answers_no_question' for a, b in runs if (a, b) not in asked]
    if not runs:
        issues.append('trial_has_no_runs')
    return issues, passages, variants, runs, questions, joins


def trial_request(passages, variants, run, lines, pron):
    """What one trial run sends: the passage as the script would send it under that variant."""
    p, v = passages[run[0]], variants[run[1]]
    text = p['text'] if v['tags'] == 'as_written' else re.sub(r'[ \t]{2,}', ' ', TAG_RE.sub('', p['text'])).strip()
    terms = pron['terms'] if v['pronunciation'] else []
    sent = '\n'.join(tts_text(x, terms) for x in text.split('\n'))
    body = {'text': sent, 'model_id': v['model_id'],
            'voice_settings': {k: v[k] for k in VOICE_SETTING_KEYS}}
    if v['context'] == 'neighbours' and p['lines']:
        all_sent = [tts_text(r.get('text') or '', terms) for r in lines]
        prev, nxt = context_text(all_sent, p['lines'][0] - 1, -1), context_text(all_sent, p['lines'][1] + 1, 1)
        if prev:
            body['previous_text'] = prev
        if nxt:
            body['next_text'] = nxt
    return body


def trial_budgets_path(rd):
    return rd / '60-voice' / 'trial-budgets.json'


def trial_budget_check(rd, budget, plan_id, write=False):
    """The plan's cap against the run's register of trial budgets (RUN/60-voice/trial-budgets.json): the first plan
    naming an id registers it, and every later plan naming the same id must carry the same cap, so a new plan never
    raises it (only the user does, by hand). Returns issues."""
    reg = read_json(trial_budgets_path(rd))
    bid, cap = str(budget.get('id')), int(budget.get('max_credits'))
    have = (reg.get('budgets') or {}).get(bid)
    if have and int(have.get('max_credits') or -1) != cap:
        return [f'trial_budget_{bid}_is_registered_with_{have.get("max_credits")}_credits_not_{cap}']
    if write:
        b = reg.setdefault('budgets', {}).setdefault(bid, {'max_credits': cap, 'registered_at': now(),
                                                            'authorised': budget.get('authorised'), 'plans': []})
        if plan_id not in b.setdefault('plans', []):
            b['plans'].append(plan_id)
            write_json(trial_budgets_path(rd), reg)
    return []


def budget_spent(rd, budget_id):
    """What a trial budget has used so far, from the ledger: every request sent under it, failures, retries and resumed
    sessions included. A request counts its credits_billed (the larger of ElevenLabs' character-cost header and the
    balance drop); when neither is known, and for a request cut off before its outcome was written (a pending row
    with no outcome), its largest possible charge. Returns (credits, the cut-off requests)."""
    rows = [r for r in ledger_rows(rd) if r.get('budget') == budget_id]
    closed = {r.get('attempt_id') for r in rows if r.get('phase') in ('done', 'recovered')}
    spent, open_ = 0, []
    for r in rows:
        if r.get('phase') == 'pending':
            if r.get('attempt_id') not in closed:
                spent += int(r.get('max_credits') or 0)
                open_.append(r)
        elif r.get('phase') in ('done', 'recovered'):
            c = take_credits(r)
            spent += int(c) if c is not None else int(r.get('max_credits') or 0)
    return spent, open_


def take_credits(row):
    """What one request cost, best evidence first: ElevenLabs' character-cost header (exact), else the credits_billed
    on record (a balance drop seen), else None. A recovered request has no header: it counts as on record."""
    if row.get('character_cost_header') is not None and row.get('phase') != 'recovered':
        return row['character_cost_header']
    return row.get('credits_billed')


def _pid_running(pid):
    """True while a process with this id runs (a trial's lock is stale once its process is gone: after a crash or a
    power cut the next run takes over). Unknown counts as running."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid == os.getpid():
        return False
    try:
        if os.name == 'nt':
            out = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH', '/FO', 'CSV'], capture_output=True, text=True,
                                 timeout=20).stdout or ''
            return f'"{pid}"' in out
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (OSError, subprocess.SubprocessError):
        return True


def eleven_get_bytes(path, key, timeout=120):
    req = urllib.request.Request('https://api.elevenlabs.io' + path, headers={'xi-api-key': key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def recover_from_history(rd, key, pending, body, voice_id):
    """A request cut off before its answer was saved (a pending ledger row with no outcome): when ElevenLabs finished
    it anyway, its audio is in the account's history (GET /v1/history and an item's audio are free), so the take is
    taken from there instead of being paid for twice. The budget keeps counting that request at its largest possible
    charge (the history's character figures are recorded beside it; ElevenLabs does not document them as credits).
    Returns (audio, ledger row) or (None, None)."""
    try:
        since = int(dt.datetime.fromisoformat(str(pending['at'])).timestamp()) - 120
        data = elevenlabs_request('GET', '/v1/history', key, params={'page_size': 100, 'voice_id': voice_id}, timeout=30)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        return None, {'history_lookup_error': f'{type(exc).__name__}: {str(exc)[:160]}'}
    for it in (data.get('history') if isinstance(data, dict) else None) or []:
        if str(it.get('text')) != body['text'] or it.get('model_id') not in (None, body['model_id']):
            continue
        if int(it.get('date_unix') or 0) < since:
            continue
        try:
            audio = eleven_get_bytes('/v1/history/' + urllib.parse.quote(str(it['history_item_id']), safe='') + '/audio', key)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, KeyError):
            return None, None
        try:
            used = int(it['character_count_change_to']) - int(it['character_count_change_from'])
        except (KeyError, TypeError, ValueError):
            used = None
        row = {**{k: v for k, v in pending.items() if k not in ('phase', 'at')}, 'at': now(), 'phase': 'recovered',
               'ok': True, 'history_item_id': it.get('history_item_id'), 'request_id': it.get('request_id'),
               'history_character_count_change': used, 'credits_billed': pending.get('max_credits'),
               'note': 'audio taken from the account history after the request was cut off; counted at its largest '
                       'possible charge'}
        ledger_add(rd, row)
        return audio, row
    return None, None


def loudness_stats(path):
    """Integrated loudness (LUFS), loudness range (LU) and true peak (dBTP) of one file, by ffmpeg's EBU R128 meter
    (local, free). Never raises: {'error': ...} when it can't be read."""
    try:
        cp = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f',
                             'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'error': f'{type(exc).__name__}: {str(exc)[:120]}'}
    tail = (cp.stderr or '').rsplit('Summary:', 1)[-1]

    def num(rx):
        m = re.search(rx, tail)
        return float(m.group(1)) if m else None
    return {'integrated_lufs': num(r'I:\s*(-?[\d.]+|-inf)\s*LUFS'), 'loudness_range_lu': num(r'LRA:\s*(-?[\d.]+)\s*LU'),
            'true_peak_dbtp': num(r'Peak:\s*(-?[\d.]+|-inf)\s*dBFS')}


def trial_measure(rec, passage, pron_terms, language, args):
    """One take's measurements, from its own audio: Whisper medium (the words heard and their times), the pace while
    speaking and over the whole speaking span, the pauses and where they fall, pitch and loudness, every line heard,
    tags read aloud, names as heard, and what looks wrong. Evidence, never a verdict."""
    f = Path(rec['file'])
    tpath = f.with_suffix('.json')
    if not tpath.is_file():
        transcribe(f, tpath, args.whisper_model, args.device, args.compute_type)
    tj = read_json(tpath)
    words = transcript_words(tj)
    rawtxt = tpath.with_suffix('.txt').read_text(encoding='utf-8', errors='replace')
    plines = passage['text'].split('\n')
    d = align_detail(plines, words, language or 'en')
    dur = probe(f)['duration_s']
    heard = strip_transcript_timestamps(rawtxt).strip()
    spoken = sum(count_words(x) for x in plines)
    span = (words[-1]['end_s'] - words[0]['start_s']) if len(words) > 1 else 0.0
    pauses = [{'after_word': a['text'].strip(), 'at_s': round(a['end_s'], 2), 'pause_s': round(b['start_s'] - a['end_s'], 2)}
              for a, b in zip(words, words[1:]) if b['start_s'] - a['end_s'] >= 0.3]
    names = []
    for t in pron_terms:
        if t['rx'].search(strip_tags(passage['text'])):
            tt = tokens_of(t['term'])
            names.append({'term': t['term'], 'sent_as': t.get('sent_as') or t['term'],
                          'heard_as_written': all(x in d['heard'] for x in tt),
                          'nearest_heard': max(d['heard'], key=lambda h: difflib.SequenceMatcher(None, tt[0], h).ratio(),
                                               default=None)})
    delivery = measure_file_delivery(f, tpath)
    loud = loudness_stats(f)
    lead = round(words[0]['start_s'], 2) if words else None
    trail = round(dur - words[-1]['end_s'], 2) if words else None
    ids = passage.get('line_ids') or [f'line {i + 1}' for i in range(len(plines))]
    not_heard = [ids[i] for i, tt in enumerate(d['tok_time']) if tt and not any(tt)]
    read_aloud = tags_heard(rec['sent']['text'], heard)
    anomalies = []
    if not words:
        anomalies.append('Whisper heard no words')
    if not_heard:
        anomalies.append('lines not heard: ' + ', '.join(not_heard))
    if read_aloud:
        anomalies.append('a tag may have been read aloud: ' + ', '.join(read_aloud))
    if d['ratio'] < 0.9:
        anomalies.append(f'only {d["ratio"]:.0%} of the words matched what was sent (a word dropped, added or misheard)')
    for nm in names:
        if not nm['heard_as_written']:
            anomalies.append(f'{nm["term"]} was heard as "{nm["nearest_heard"]}" (Whisper\'s spelling, not proof of '
                             'how it was said: listen)')
    if lead is not None and lead > 1.0:
        anomalies.append(f'{lead} s of silence before the first word')
    if trail is not None and trail > 1.5:
        anomalies.append(f'{trail} s of silence after the last word')
    if isinstance(loud.get('true_peak_dbtp'), float) and loud['true_peak_dbtp'] > -0.3:
        anomalies.append(f'true peak {loud["true_peak_dbtp"]} dBTP: may clip')
    rec.update({
        'measured': True, 'measured_at': now(), 'duration_s': dur, 'words_spoken': spoken,
        'active_wpm': wpm_from_transcript_raw(rawtxt),
        'overall_wpm': round(spoken / (span / 60)) if span > 0 else None,
        'file_wpm': round(spoken / (dur / 60)) if dur else None,
        'speech_span_s': round(span, 2), 'lead_silence_s': lead, 'trail_silence_s': trail,
        'pause_profile': pause_profile(words), 'pauses': pauses,
        'delivery': delivery, 'loudness': loud,
        'alignment_match_ratio': round(d['ratio'], 3), 'lines_not_heard': not_heard,
        'tags_maybe_read_aloud': read_aloud, 'names': names, 'heard_text': heard[:900],
        'transcript': str(tpath), 'anomalies': anomalies, 'uncertainties': TRIAL_UNCERTAINTIES})
    return rec


def _blind_order(trial_id, qid, runs_):
    """The order a question's takes are labelled A, B, ... in: fixed by the trial and question (so a rebuilt set keeps
    its labels), unrelated to the variants' names."""
    return sorted(runs_, key=lambda r: hashlib.sha256(f'{trial_id}|{qid}|{r[0]}-{r[1]}'.encode('utf-8')).hexdigest())


def _join_audio(a, b, gap_s, out):
    """Two takes as the viewer hears two recorded parts: the first, a gap of the voice's own pause, the second."""
    run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(a), '-f', 'lavfi', '-t',
             f'{gap_s:.3f}', '-i', 'anullsrc=r=44100:cl=mono', '-i', str(b), '-filter_complex',
             '[0:a]aformat=sample_rates=44100:channel_layouts=mono[x];[1:a]aformat=sample_rates=44100:channel_layouts=mono[g];'
             '[2:a]aformat=sample_rates=44100:channel_layouts=mono[y];[x][g][y]concat=n=3:v=0:a=1[o]', '-map', '[o]',
             '-c:a', 'libmp3lame', '-b:a', '128k', str(out)])


def trial_listening_set(outdir, plan, questions, report, passages, variants, joins=()):
    """The blind listening set for the user: listening/ holds each question's takes as <Q>-A.mp3, <Q>-B.mp3 ... (copies;
    the labels say nothing about the settings) and listening-guide.md (the lines, what each moment is meant to feel
    like, what to listen for, a sheet to fill in); answer-key.md / .json, one folder up, say which take is which, with
    every take's settings and measurements. A take used by two questions is copied under each question's own label. A
    join (two passages of consecutive lines, recorded as two requests the way two parts are) is heard as the viewer
    would: the first take, the voice's own pause, the second; the answer key shows the steps in level, pace and
    pitch across the join. Returns what was written."""
    lst = outdir / 'listening'
    lst.mkdir(parents=True, exist_ok=True)
    key, guide = [], [
        f'# Blind listening: {plan["id"]}', '',
        'Each question below has two (or more) takes. In each pair at most one thing differs (some questions send the very same request twice, to hear how much one set-up varies by itself). The file '
        'names say nothing about which is which; the answer key is one folder up (answer-key.md): open it only after '
        'you have written your notes.', '',
        'How to listen: headphones or good speakers, at the volume you would watch a video. Play A then B, then B then A. '
        'Judge the take, not the words (the words are the same).', '',
        'For each line of the sheet put A, B or "same", and a word or two when you can. What matters most: does it sound '
        'like a person telling you this story, and would you keep listening for twenty minutes?', '']
    done_q = []
    for q in questions:
        runs_ = q['compare']
        if not all((report['runs'].get(f'{a}|{b}') or {}).get('file') for a, b in runs_):
            continue
        p = passages[runs_[0][0]]
        same_p = all(r[0] == runs_[0][0] for r in runs_)
        guide += [f'## {q["id"]}: {p.get("moment") or ""}' + (f' ({p.get("lines_label")})' if p.get('lines_label') else ''),
                  '', f'Meant to feel: {p.get("intended_delivery")}', '']
        guide += [f'Listen for: {q.get("listen_for") or "which take sounds more like a person telling this story"}', '']
        if same_p:
            guide += ['The words: "' + ' '.join(strip_tags(x) for x in p['text'].split('\n')) + '"', '']
        labels = []
        for i, r in enumerate(_blind_order(plan['id'], q['id'], runs_)):
            lab = f'{q["id"]}-{chr(65 + i)}'
            src = Path(report['runs'][f'{r[0]}|{r[1]}']['file'])
            dst = lst / f'{lab}.mp3'
            shutil.copyfile(src, dst)
            labels.append(lab)
            key.append({'question': q['id'], 'label': lab, 'file': str(dst), 'run': f'{r[0]}-{r[1]}', 'source': str(src)})
        guide += ['Files: ' + ', '.join(f'{x}.mp3' for x in labels), '',
                  '| | ' + ' | '.join(x.split('-')[-1] for x in labels) + ' | same | note |',
                  '|---|' + '---|' * len(labels) + '---|---|']
        guide += [f'| {txt} |' + ' |' * len(labels) + ' | |' for _, txt in TRIAL_LISTEN_ITEMS]
        guide += ['', 'Which would you keep, and why (one line):', '', '']
        done_q.append(q['id'])
    join_rows = []
    for j in joins:
        takes = {(x, v): report['runs'].get(f'{x}|{v}') or {} for v in j['compare'] for x in j['parts']}
        if not all(tk.get('file') and tk.get('measured') for tk in takes.values()):
            continue
        pauses = sorted(pp['pause_s'] for tk in takes.values() for pp in tk.get('pauses') or [])
        gap = min(0.8, max(0.3, pauses[len(pauses) // 2] if pauses else 0.45))
        pa, pb = passages[j['parts'][0]], passages[j['parts'][1]]
        guide += [f'## {j["id"]}: the join between two recorded parts ({pa.get("lines_label")} | {pb.get("lines_label")})',
                  '', f'Meant to feel: {pa.get("intended_delivery")} | then: {pb.get("intended_delivery")}', '',
                  f'Listen for: {j.get("listen_for") or "which sounds like one person telling one story across the join"}',
                  '']
        labels = []
        for i, (_, v) in enumerate(_blind_order(plan['id'], j['id'], [(j['parts'][0], v) for v in j['compare']])):
            lab = f'{j["id"]}-{chr(65 + i)}'
            first, second = takes[(j['parts'][0], v)], takes[(j['parts'][1], v)]
            dst = lst / f'{lab}.mp3'
            _join_audio(first['file'], second['file'], gap, dst)
            labels.append(lab)
            lv = [(tk.get('loudness') or {}).get('integrated_lufs') for tk in (first, second)]
            pc = [tk.get('active_wpm') for tk in (first, second)]
            reg = [(tk.get('delivery') or {}).get('register_hz') for tk in (first, second)]
            join_rows.append({'question': j['id'], 'label': lab, 'variant': v, 'gap_s': round(gap, 2),
                              'level_step_lu': round(lv[1] - lv[0], 1) if None not in lv else None,
                              'pace_step_wpm': (pc[1] - pc[0]) if None not in pc else None,
                              'register_step_hz': round(reg[1] - reg[0], 1) if None not in reg else None,
                              'first_trail_silence_s': first.get('trail_silence_s'),
                              'second_lead_silence_s': second.get('lead_silence_s'), 'file': str(dst),
                              'takes': [first['file'], second['file']]})
            key.append({'question': j['id'], 'label': lab, 'file': str(dst),
                        'run': f'{j["parts"][0]}+{j["parts"][1]}-{v}',
                        'source': f'join of {first["file"]} and {second["file"]}'})
        guide += ['Files: ' + ', '.join(f'{x}.mp3' for x in labels), '',
                  '| | ' + ' | '.join(x.split('-')[-1] for x in labels) + ' | same | note |',
                  '|---|' + '---|' * len(labels) + '---|---|']
        guide += [f'| {txt} |' + ' |' * len(labels) + ' | |' for _, txt in TRIAL_LISTEN_ITEMS]
        guide += ['', 'Which would you keep, and why (one line):', '', '']
        done_q.append(j['id'])
    (lst / 'listening-guide.md').write_text('\n'.join(guide) + '\n', encoding='utf-8')
    by_source = {}
    for k in key:
        by_source.setdefault(k['source'], []).append(k['label'])
    md = [f'# Answer key: {plan["id"]}', '', 'Open after listening. Settings and measurements per take. The numbers are '
          'measurements, not verdicts: a narrower pitch range can be the right, quieter delivery, and a faster take is '
          'not a better one.', '']
    for q in questions:
        if q['id'] not in done_q:
            continue
        md += [f'## {q["id"]}: {q["asks"]}', ('Nothing changes: the same request sent twice (how much one set-up varies '
                                                'by itself).' if q.get('repeat') else
                                                f'Only {", ".join(q["varies"])} changes between these takes.'), '',
               '| label | take | stability | tags | pronunciation | context | active / overall wpm | duration s | '
               'longest pause s | pitch range st | loudness LUFS | credits | anomalies |',
               '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for k in [x for x in key if x['question'] == q['id']]:
            x = report['runs'][k['run'].replace('-', '|', 1)]
            v = variants[k['run'].split('-', 1)[1]]
            dl = x.get('delivery') or {}
            md.append(f'| {k["label"]} | {k["run"]} | {v["stability"]} | {v["tags"]} | {"on" if v["pronunciation"] else "off"}'
                      f' | {v["context"]} | {x.get("active_wpm")} / {x.get("overall_wpm")} | {x.get("duration_s")} | '
                      f'{(x.get("pause_profile") or {}).get("longest_pause_s")} | {dl.get("pitch_range_st")} | '
                      f'{(x.get("loudness") or {}).get("integrated_lufs")} | {take_credits(x.get("cost") or {})} | '
                      f'{"; ".join(x.get("anomalies") or []) or "none"} |')
        md.append('')
    for j in joins:
        rows_ = [r for r in join_rows if r['question'] == j['id']]
        if not rows_:
            continue
        md += [f'## {j["id"]}: {j["asks"]}', f'Two requests joined with a {rows_[0]["gap_s"]} s pause; only '
               f'{", ".join(j["varies"])} changes between the versions. A step is the second part minus the first.', '',
               '| label | variant | level step LU | pace step wpm (active) | register step Hz | silence at the end of the '
               'first s | silence before the second s |', '|---|---|---|---|---|---|---|']
        for r in rows_:
            setting = ', '.join(f'{k}={variants[r["variant"]][k]}' for k in j['varies'])
            md.append(f'| {r["label"]} | {r["variant"]} ({setting}) | {r["level_step_lu"]} | {r["pace_step_wpm"]} | '
                      f'{r["register_step_hz"]} | {r["first_trail_silence_s"]} | {r["second_lead_silence_s"]} |')
        md.append('')
    twins = [v for v in by_source.values() if len(v) > 1 and not str(v[0]).startswith('join')]
    if twins:
        md += ['Same recording under two labels (a baseline reused by two questions): ' +
               '; '.join(' = '.join(v) for v in twins), '']
    md += ['## What the numbers can and cannot say', ''] + [f'- {u}' for u in TRIAL_UNCERTAINTIES] + ['']
    (outdir / 'answer-key.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    write_json(outdir / 'answer-key.json', {'trial': plan['id'], 'labels': key, 'same_recording': twins,
                                            'joins': join_rows})
    return {'listening': str(lst), 'guide': str(lst / 'listening-guide.md'), 'answer_key': str(outdir / 'answer-key.md'),
            'questions_ready': done_q}


def cmd_narration_trial(args):
    """A controlled calibration trial before production: a few passages of this video (an opening, an explanation, a
    turn), each under a few voice set-ups, to learn what this voice does with this treatment: stability, tags or no
    tags, pronunciation, the context across a join, another narrator. The plan is checked (each question compares runs
    that differ in exactly one thing) and priced first; nothing is recorded without --execute. Then the takes are
    recorded one at a time, never two at once, each only after the price is read again, the live balance covers it
    and the plan's budget (the credits the user authorised, shared by every plan under its id, counted from the
    ledger with retries and interrupted requests) still covers its largest possible charge, context fields included.
    A take is saved and put on record the moment it arrives, then measured; re-running the same command continues:
    recorded takes are never sent again (each is matched by the fingerprint of its exact request), a take recorded but
    not measured is measured, and a request cut off by a crash is looked up in the account history before anything is
    paid again. listening/ is the blind set for the user's ears; answer-key.md says which take is which. The
    measurements are evidence, never a verdict on which take sounds better: no agent here can hear them."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    lock = read_json(vd / 'length-lock.json')
    script = read_json(vd / 'script.json')
    lines = script.get('lines') or []
    plan = read_json(args.plan, required=True)
    vf = voice_facts(rd, n)
    # A trial may carry its own pronunciation list, to hear a form before the episode adopts it (the episode's list,
    # and so what its recorded parts are compared against, stays as it is).
    pron = pronunciation_facts(rd, n, lines, plan.get('pronunciation')) if plan.get('pronunciation') is not None \
        else pronunciation_facts(rd, n, lines)
    issues, passages, variants, runs, questions, joins = trial_plan_facts(plan, vf, lines, pron)
    issues += pron['issues']
    budget = plan.get('budget') or {}
    if not issues:
        issues += trial_budget_check(rd, budget, plan['id'])
    if issues:
        error('The trial plan is not ready.', issues)
    lang = language_code((lock or {}).get('language'))

    def path_of(v):
        return '/v1/text-to-speech/' + urllib.parse.quote(v['voice_id'], safe='') + '?output_format=mp3_44100_128'
    bodies = {}
    for r in runs:
        b = trial_request(passages, variants, r, lines, pron)
        if lang:
            b['language_code'] = lang
        bodies[r] = b
    fps = {r: hashlib.sha256(json.dumps({'path': path_of(variants[r[1]]), 'body': bodies[r]}, sort_keys=True,
                                        ensure_ascii=False).encode('utf-8')).hexdigest() for r in runs}
    outdir = rd / '60-voice' / f'video-{n:02d}' / 'trials' / plan['id']
    report = read_json(outdir / 'report.json')
    recorded = report.get('runs') or {}

    def rkey(r):
        return f'{r[0]}|{r[1]}'

    def done(r):
        x = recorded.get(rkey(r)) or {}
        return bool(x.get('file')) and Path(x['file']).is_file() and x.get('request_sha256') == fps[r]
    drifted = [f'{a}-{b}' for a, b in runs if (recorded.get(rkey((a, b))) or {}).get('file') and not done((a, b))]
    if drifted:
        error('Recorded takes no longer match this plan (their exact request changed): a changed plan is a new trial '
              'id, so the recorded evidence stays what it was.', drifted)
    wanted = None
    if args.takes:
        names = {f'{a}-{b}': (a, b) for a, b in runs}
        asked = [x.strip() for x in args.takes.split(',') if x.strip()]
        unknown = [x for x in asked if x not in names]
        if unknown:
            error('--takes names runs this plan does not have.', {'unknown': unknown, 'runs': list(names)})
        wanted = [names[x] for x in asked]
    todo = [r for r in runs if not done(r) and (wanted is None or r in wanted)]
    chars = {r: len(bodies[r]['text']) for r in runs}
    ctx = {r: len(bodies[r].get('previous_text') or '') + len(bodies[r].get('next_text') or '') for r in runs}
    by_model = {}
    for r in todo:
        by_model.setdefault(variants[r[1]]['model_id'], [0, 0])
        by_model[variants[r[1]]['model_id']][0] += chars[r]
        by_model[variants[r[1]]['model_id']][1] += chars[r] + ctx[r]
    treatment = read_json(vd / 'direction-lock.json')
    treatment_info = ({'treatment': treatment.get('treatment'), 'production_rev': treatment.get('production_rev')}
                      if treatment else {'treatment': None, 'note': 'this video has no locked creative direction'})
    summary = {'trial': plan['id'], 'budget': {'id': budget['id'], 'max_credits': budget['max_credits']},
               'runs': len(runs), 'runs_to_record': len(todo),
               'characters_to_record': sum(chars[r] for r in todo),
               'context_characters_to_record': sum(ctx[r] for r in todo),
               'runs_detail': [{'run': f'{a}-{b}', 'moment': passages[a]['moment'], 'characters': chars[(a, b)],
                                'context_characters': ctx[(a, b)], 'voice_id': variants[b]['voice_id'],
                                'model_id': variants[b]['model_id'], 'stability': variants[b]['stability'],
                                'similarity_boost': variants[b]['similarity_boost'], 'tags': variants[b]['tags'],
                                'pronunciation': variants[b]['pronunciation'], 'context': variants[b]['context'],
                                'done': done((a, b)), 'this_time': (a, b) in todo} for a, b in runs],
               'questions': [{'id': q['id'], 'asks': q['asks'], 'compares': [f'{a}-{b}' for a, b in q['compare']],
                              'varies': q['varies'] or (['nothing: the same request twice'] if q.get('repeat') else [])}
                             for q in questions],
               'joins': [{'id': j['id'], 'asks': j['asks'], 'parts': j['parts'], 'compares': j['compare'],
                          'varies': j['varies']} for j in joins]}
    spent, open_ = budget_spent(rd, budget['id'])
    key = elevenlabs_key() if (args.execute or args.check_balance) else ''
    if (args.execute or args.check_balance) and not key:
        error('ELEVENLABS_API_KEY (or ELEVEN_API_KEY) is not set; do not store API keys in the command or ZIP.')
    if not args.execute:
        estimate = {}
        for model, (c, cmax) in by_model.items():
            per = model_rates(rd, key, model, max_age_h=0)['credits_per_character'] if args.check_balance else \
                cached_model_rates(rd, model)
            measured, samples = measured_cost_ratio(rd, model)
            estimate[model] = {'characters': c, 'characters_with_context': cmax, 'credits_per_character': per,
                               'expected_credits': math.ceil(c * per) if per is not None else None,
                               'max_credits': math.ceil(cmax * per) if per is not None else None,
                               'measured_credits_per_character': measured, 'measured_requests': samples}
        known = all(e['expected_credits'] is not None for e in estimate.values())
        total = sum(e['expected_credits'] or 0 for e in estimate.values()) if known else None
        total_max = sum(e['max_credits'] or 0 for e in estimate.values()) if known else None
        out = {'ok': True, 'mode': 'dry_run_no_charges', **summary, 'credit_estimate': estimate,
               'expected_credits_total': total, 'max_credits_total': total_max,
               'budget_status': {'spent': spent, 'left': budget['max_credits'] - spent,
                                 'interrupted_requests': len(open_),
                                 'fits': (spent + total_max <= budget['max_credits']) if total_max is not None else None}}
        if args.check_balance:
            bal = subscription_balance(key)
            out['balance'] = {'available': bal['available'], 'left_after_expected': bal['available'] - (total or 0),
                              'left_after_max': bal['available'] - (total_max or 0),
                              'next_reset_unix': bal['next_reset_unix']}
        out['next'] = ('Show the user this plan: each question, the runs it compares, the credits (expected and at most). '
                       'Record only after their approval: narration-trial ... --execute (one take at a time; --takes to '
                       'record some first).')
        emit(out)
        return
    outdir.mkdir(parents=True, exist_ok=True)
    lockf = outdir / 'trial.lock'
    held = read_json(lockf) if lockf.is_file() else {}
    if held and _pid_running(held.get('pid')):
        error('Another narration-trial is recording this trial (trial.lock): trials run one at a time.',
              {'lock': str(lockf), 'held_by': held})
    lockf.write_text(json.dumps({'pid': os.getpid(), 'at': now()}), encoding='utf-8')
    try:
        if not (outdir / 'plan.json').is_file() or read_json(outdir / 'plan.json') != plan:
            write_json(outdir / 'plan.json', plan)
        trial_budget_check(rd, budget, plan['id'], write=True)
        report = {'trial': plan['id'], 'video': n, 'treatment': treatment_info,
                  'voice_lock': {'file': str(rd / '60-voice' / 'voice-lock.json') if vf.get('legacy')
                                 else str(voice_lock_path(rd, n)), 'legacy': vf.get('legacy'),
                                 'voice_id': vf.get('voice_id'), 'model_id': vf.get('model_id'),
                                 'settings': vf.get('settings')},
                  'budget': summary['budget'], 'questions': summary['questions'], 'runs': recorded,
                  'started_at': report.get('started_at') or now(), 'sessions': (report.get('sessions') or []) + [now()]}
        write_json(outdir / 'report.json', report)
        language = lock.get('language') or 'en'
        # A take recorded but not yet measured (a session that stopped between the two) is measured, never re-sent.
        for r in runs:
            x = recorded.get(rkey(r)) or {}
            if done(r) and not x.get('measured'):
                trial_measure(x, passages[r[0]], [{**t, 'sent_as': t['say'] if variants[r[1]]['pronunciation'] else
                                                   t['term']} for t in pron['terms']], language, args)
                write_json(outdir / 'report.json', report)
        stop = None
        for r in todo:
            v = variants[r[1]]
            body = bodies[r]
            rates = model_rates(rd, key, v['model_id'], max_age_h=0)        # the price, read again before each request
            per = rates['credits_per_character']
            max_cr = math.ceil((chars[r] + ctx[r]) * per)
            spent, open_ = budget_spent(rd, budget['id'])
            audio, entry = None, None
            for o in [o for o in open_ if o.get('request_sha256') == fps[r]]:
                audio, entry = recover_from_history(rd, key, o, body, v['voice_id'])
                if audio:
                    break
            if audio is None:
                if spent + max_cr > budget['max_credits']:
                    stop = {'run': f'{r[0]}-{r[1]}', 'why': 'budget', 'spent': spent, 'this_request_at_most': max_cr,
                            'max_credits': budget['max_credits']}
                    break
                need = math.ceil(max_cr * args.credit_safety_factor) + int(args.keep_credits or 0)
                raw, err, entry = eleven_paid_post(
                    rd, key, path_of(v), body, 'trial',
                    {'video': n, 'trial': plan['id'], 'run': f'{r[0]}-{r[1]}', 'model_id': v['model_id'],
                     'voice_id': v['voice_id'], 'budget': budget['id'], 'request_sha256': fps[r],
                     'credits_per_character': per}, require=need, max_credits=max_cr)
                if entry is None:
                    stop = {'run': f'{r[0]}-{r[1]}', 'why': 'balance', 'error': err, 'needed': need}
                    break
                if err or not raw or len(raw) < 1024:
                    stop = {'run': f'{r[0]}-{r[1]}', 'why': 'request_failed', 'error': err or 'audio response too short',
                            'ledger': entry}
                    break
                audio = raw
            f = outdir / f'{r[0]}-{r[1]}.mp3'
            f.write_bytes(audio)
            terms = [{**t, 'sent_as': t['say'] if v['pronunciation'] else t['term']} for t in pron['terms']]
            applied = [{k: t.get(k) for k in ('term', 'say', 'how', 'confidence', 'source')} for t in pron['terms']
                       if v['pronunciation'] and t['rx'].search(strip_tags(passages[r[0]]['text']))]
            rec = {'run': f'{r[0]}-{r[1]}', 'file': str(f), 'request_sha256': fps[r],
                   'sent_text_sha256': hashlib.sha256(body['text'].encode('utf-8')).hexdigest(),
                   'sent': {'endpoint': path_of(v), **{k: body.get(k) for k in ('text', 'previous_text', 'next_text',
                                                                                 'model_id', 'voice_settings',
                                                                                 'language_code')}},
                   'tags': [m.group(0) for m in TAG_RE.finditer(body['text'])], 'pronunciation_applied': applied,
                   'variant': v, 'moment': passages[r[0]]['moment'], 'lines': passages[r[0]].get('lines_label'),
                   'intended_delivery': passages[r[0]]['intended_delivery'], 'treatment': treatment_info,
                   'cost': {'max_credits': max_cr, 'credits_per_character': per, 'characters_text': chars[r],
                            'characters_context': ctx[r],
                            'character_cost_header': (entry or {}).get('character_cost_header'),
                            'balance_drop': (entry or {}).get('delta'),
                            'credits_billed': (entry or {}).get('credits_billed'),
                            'recovered_from_history': (entry or {}).get('phase') == 'recovered'},
                   'ledger_attempt': (entry or {}).get('attempt_id'), 'recorded_at': now(), 'measured': False}
            recorded[rkey(r)] = rec
            write_json(outdir / 'report.json', report)
            trial_measure(rec, passages[r[0]], terms, language, args)
            write_json(outdir / 'report.json', report)
        all_done = all(done(r) for r in runs)
        if all_done:
            report['finished_at'] = now()
        write_json(outdir / 'report.json', report)
        listening = trial_listening_set(outdir, plan, questions, report, passages, variants, joins)
    finally:
        try:
            lockf.unlink()
        except OSError:
            pass
    spent, open_ = budget_spent(rd, budget['id'])
    res = {'ok': stop is None, 'mode': 'recorded', **summary, 'report': str(outdir / 'report.json'), **listening,
           'credits_billed_this_trial': sum((take_credits(x.get('cost') or {}) or 0) for x in report['runs'].values()),
           'budget_status': {'spent': spent, 'left': budget['max_credits'] - spent, 'interrupted_requests': len(open_)},
           'all_recorded': all_done, 'stopped': stop,
           'next': 'Give the user listening/ (blind) and, after their notes, answer-key.md; record their impressions '
                   'next to the measurements. Decide the voice lock (voice-pick) from both, never from the numbers alone.'}
    if stop:
        emit({**res, 'error': 'Stopped before ' + stop['run'] + ': ' + stop['why'] + '. Nothing more was sent; the takes '
                              'already recorded are kept (re-run the same command to continue).'}, 2)
    emit(res)


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
        verified, v_n = measured_cost_ratio(rd, model_id)
        emit({'ok': True, 'mode': 'dry_run_no_charges', 'video': n, 'parts': len(chunks),
              'characters_total': sum(s['characters'] for s in spec['chunks']),
              'parts_to_record': [s['id'] for s in todo], 'changed_recorded_parts': changed,
              'pronunciation_changed_parts': pron_changed, 'parts_recorded_with_another_voice_setup': other_setup,
              'parts_made_for_an_earlier_direction': outdated, 'parts_asked_to_rerecord': asked,
              'starts_over': start_over, 'characters_to_record': chars,
              'credit_estimate': {
                  'expected_credits': (math.ceil(chars * verified) if verified is not None else
                                       math.ceil(chars * per_char) if per_char is not None else None),
                  'basis': (f'verified billing on this account: {verified} credits per character sent, median of '
                            f'{v_n} billed request(s) in the ledger (the cost header)' if verified is not None else
                            'the model rates last read for this run (no billed request in the ledger yet)'
                            if per_char is not None else
                            'not read yet: --execute reads the credits per character and the live balance first'),
                  'verified_credits_per_character': verified, 'verified_requests': v_n,
                  'documented_credits_per_character': per_char,
                  'upper_bound_at_documented_rate': math.ceil(chars * per_char) if per_char is not None else None,
                  'note': 'characters = the exact text sent (tags and pronunciation forms included); --execute checks '
                          'the live balance against the documented rate times the safety factor'},
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
        history = [{'at': now(), 'archived_previous_take_to': str(archive),
                    'reason': (getattr(args, 'reason', None) or None)}]
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
    # window: narration plus the silence the edit holds add must already fit it, or the export can never pass. A hold
    # adds what was decided against the voice's measured gap there (estimated the same way while still provisional);
    # a join that already carries a hold gets no seam hold on top.
    hf = hold_facts(rd, video, script_lines)
    holds = hf['added_s']
    held_lines = {h['line'] for h in hf['holds']}
    if lt and seam_s:
        seam_s = sum(float(s.get('seam_hold_s') or 0) for s in lt.get('seams') or [] if s.get('after_line') not in held_lines)
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
        # The held silences: timed from the decisions in force, and each one decided again with its picture (the shot
        # on screen while it lasts, as that shot's still is now). A decision written down before the picture existed
        # is a proposal the picture can overturn.
        hf = hold_facts(rd, n, lines)
        if (plan.get('hold_decisions_sha256') is not None or hf['holds']) and \
                plan.get('hold_decisions_sha256') != hold_decisions_sha(rd, n):
            issues.append('edit_plan_outdated_holds_changed_rerun_retime_shots')
        not_with_picture = [h['line'] for h in hf['holds'] if h.get('index') and h['status'] != 'decided_picture']
        if not_with_picture:
            issues.append('holds_not_decided_with_their_picture:' + ','.join(not_with_picture))
        gone = [h['line'] for h in hf['holds'] if h['status'] == 'line_not_in_script']
        if gone:
            warnings.append('hold decisions for lines the script no longer has (ignored): ' + ','.join(gone))
        for h in hf['holds']:
            if h['status'] == 'decided_picture':
                seen_pic = (h.get('decision') or {}).get('picture') or {}
                now_pic = hold_shot(rd, n, h['index']) or {}
                if (seen_pic.get('shot_id'), seen_pic.get('still_fingerprint')) != \
                        (now_pic.get('shot_id'), now_pic.get('still_fingerprint')):
                    issues.append(f'hold_{h["line"]}_decided_with_another_picture')
        # What the bed does around each held silence, as decided, in the project: it enters, stops, goes on under it,
        # or there is none (from timeline.json's music and ambience tracks). A dip or a swell is a volume move the
        # project's read-back here does not carry: it is listed to listen to, never claimed.
        beds = [t for t in track.get('audio_tracks') or [] if isinstance(t, dict)
                and str(t.get('kind') or '').lower() in BED_KINDS and t.get('start_s') is not None
                and t.get('end_s') is not None]
        for p in plan.get('pauses') or []:
            bed, tm = (p.get('transition') or {}).get('bed'), p.get('times_in_edit') or {}
            if not bed or not tm:
                continue
            a, b = float(tm['silence_from_s']), float(tm['silence_to_s'])
            nxt = float(tm.get('next_line_s') or b)
            spans_ = [(float(t['start_s']), float(t['end_s'])) for t in beds]
            covers = any(s <= a + 0.05 and e >= b - 0.05 for s, e in spans_)
            under = any(s < b - 0.2 and e > a + 0.2 for s, e in spans_)
            ok = {'enters': any(a - 0.5 <= s <= nxt + 0.5 for s, _ in spans_),
                  'stops': any(a - 0.5 <= e <= nxt + 0.5 for _, e in spans_),
                  'continues': covers, 'none': not under, 'dips': covers, 'swells': covers}[bed]
            if not ok:
                issues.append(f'hold_{p["after_line"]}_bed_{bed}_not_in_the_project_at_{_mmss(a)}')
            elif bed in ('dips', 'swells'):
                warnings.append(f'{p["after_line"]}: the bed {bed} at {_mmss(a)}-{_mmss(nxt)}: a volume move the read-back '
                                'does not carry; listen there')
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
    looks = read_json(picture_looks_path(rd, n)).get('looks') or {}
    unlooked, flagged = [], []
    for f in dict.fromkeys(_run_file(rd, c.get('asset_path')) for c in seq
                           if isinstance(c, dict) and str(c.get('asset_path') or '').strip()):
        rec = looks.get(_pkey(f))
        if not rec or not f.is_file() or rec.get('sha256') != file_sha256(f):
            unlooked.append(f.name)
        elif rec.get('result') != 'clean':
            flagged.append(f.name)
    if unlooked:
        issues.append(f'pictures_not_content_checked:{len(unlooked)}:' + ','.join(unlooked[:10])
                      + ('...' if len(unlooked) > 10 else ''))
    if flagged:
        issues.append(f'pictures_with_a_content_issue:{len(flagged)}:' + ','.join(flagged[:10]))
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
    # The approved narration in the cut, whole: read from the CapCut project itself when timeline.json names it
    # (capcut_draft), else from timeline.json's narration entries.
    expect = plan.get('narration_for_edit') or {}
    nsegs = None
    if track.get('capcut_draft') and expect.get('file'):
        try:
            want = _pkey(_run_file(rd, expect['file']))
            nsegs = [s for s in capcut_audio_segments(track['capcut_draft']) if _pkey(s['file']) == want]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append('capcut_project_unreadable:' + str(exc)[:120])
    if nsegs is None:
        nsegs = [s for s in track.get('audio_tracks') or [] if str(s.get('kind')) == 'narration']
    issues += narration_track_issues(rd, nsegs, expect)
    # The captions, as the user chose them at the start: read back from the project itself.
    try:
        cissues, cchoice = captions_plan_facts(rd, n)
    except (RuntimeError, ImportError) as exc:
        cissues, cchoice = [f'captions_not_checked:{str(exc)[:120]}'], (None, None)
    if cchoice[0] is None:
        warnings.append('the user has not chosen the captions for this run (captions-choice): none are checked')
    elif cissues:
        issues += cissues
    elif track.get('capcut_draft'):
        try:
            cres = _captions().check_draft(track['capcut_draft'], read_json(captions_plan_path(rd, n)))
            issues += cres['issues']
            warnings += cres['warnings']
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append('captions_unreadable_in_the_project:' + str(exc)[:120])
    else:
        warnings.append('timeline.json names no capcut_draft: the captions were not read back from the project')
    sf = stills_facts(rd, n)
    issues += sf['issues']
    warnings += sf['warnings']
    if track.get('canvas') not in ('1920x1080', '2560x1440', '3840x2160'):
        issues.append('canvas_not_youtube_16_9')
    return {'ready': not issues, 'issues': issues, 'warnings': warnings, 'last_visual_end_s': cursor,
            'target_length_s': lock.get('target_length_s'), 'audio_ready': sound['ready']}


# ---------------------------------------------------------------- captions (the user's pick at the start)
def _captions():
    """The caption builder (captions.py, next to this file), loaded only when a caption command needs it."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import captions
    return captions


def captions_plan_path(rd, video):
    return rd / '70-edit' / f'video-{int(video):02d}' / 'captions.json'


def cmd_captions_choice(args):
    """The user's captions choice for this run, asked once at the start and kept in state.json: captions on with a
    style (luckiest-guy: Luckiest Guy word box; montserrat-highlight: Montserrat Bold, the spoken word yellow), or off.
    A typo is refused, and a choice already made changes only with --change and the user's reason."""
    rd, st = run_folder(args)
    cap = _captions()
    want = (args.captions, args.style or None)
    if want[0] == 'on' and want[1] not in cap.CAPTION_STYLES:
        error('With captions on, --style is one of: ' + ', '.join(cap.CAPTION_STYLES))
    if want[0] == 'off' and want[1]:
        error('Captions off take no style.')
    have = cap.caption_choice(st)
    if have[0] and have != want:
        if n_words(args.change) < 3:
            error('This run already has its captions choice; it changes only on the user\'s say (--change "why").',
                  {'captions': have[0], 'caption_style': have[1]})
        st.setdefault('captions_history', []).append({'captions': have[0], 'caption_style': have[1], 'until': now(),
                                                      'changed_because': args.change})
    st['captions'], st['caption_style'] = want
    st['captions_chosen_at'] = st.get('captions_chosen_at') if have == want else now()
    write_json(rd / 'state.json', st)
    emit({'ok': True, 'captions': want[0], 'caption_style': want[1],
          'look': cap.LOOKS[want[1]]['label'] if want[1] else 'no captions'})


def captions_plan_facts(rd, video, plan=None):
    """Whether the caption plan still describes this video: the run's choice, the script, the measured narration and
    the edit plan's holds it was made from."""
    n = int(video)
    cap = _captions()
    st = read_json(rd / 'state.json')
    choice = cap.caption_choice(st)
    plan = plan if plan is not None else read_json(captions_plan_path(rd, n))
    issues = []
    if not choice[0]:
        issues.append('captions_not_chosen: ask the user once (captions-choice)')
        return issues, choice
    if not plan:
        issues.append('captions_plan_missing: run captions-plan')
        return issues, choice
    if (plan.get('captions'), plan.get('style')) != choice:
        issues.append(f'captions_plan_is_for_another_choice:{plan.get("captions")}/{plan.get("style")}')
    if choice[0] == 'on':
        lines = read_json(video_dir(rd, n) / 'script.json').get('lines') or []
        ep = read_json(artifact_path(rd, n, 'edit'))
        if (plan.get('made_from') or {}).get('script_sha256') != script_hash(lines):
            issues.append('captions_plan_made_from_an_earlier_script')
        if (plan.get('made_from') or {}).get('narration_for_edit_sha256') != (ep.get('narration_for_edit') or {}).get('sha256'):
            issues.append('captions_plan_made_for_an_earlier_edit_narration')
    return issues, choice


def cmd_captions_plan(args):
    """The captions' words and times for this video, from the run's choice: the script's canonical words (tags removed;
    the pronunciation list never reaches a caption), each timed by Whisper medium on the recorded narration
    (line-times.json `word_times`, from narration-measure), moved onto the edit's timeline by every hold retime-shots
    inserted (edit-plan.json). Writes 70-edit/video-NN/captions.json. The word box needs its colour, chosen for this
    video's pictures, with the reason (--box-color, --box-color-why)."""
    rd, st = run_folder(args)
    n = int(args.video)
    cap = _captions()
    choice = cap.caption_choice(st)
    if not choice[0]:
        error('The user has not chosen the captions for this run: ask once (captions on or off and, when on, the style) '
              'and record it with captions-choice.')
    out = {'video': n, 'captions': choice[0], 'style': choice[1], 'made_at': now()}
    if choice[0] == 'off':
        write_json(captions_plan_path(rd, n), out)
        emit({'ok': True, 'captions': 'off', 'plan': str(captions_plan_path(rd, n)),
              'next': 'No caption is built; timeline-check confirms the project has no caption track.'})
        return
    vd = video_dir(rd, n)
    lock = read_json(vd / 'length-lock.json')
    lines = read_json(vd / 'script.json', required=True).get('lines') or []
    language = lock.get('language') or 'en'
    folder = rd / '50-audio' / f'video-{n:02d}'
    lt = read_json(folder / 'line-times.json', required=True)
    if not lt.get('complete') or lt.get('script_sha256') != script_hash(lines):
        error('line-times.json does not describe the whole current script: run narration-measure on the finished '
              'narration first.')
    rows = {r['index']: r for r in lt.get('lines') or []}
    if any('word_times' not in r for r in rows.values()):
        error('line-times.json has no word times (it was measured before captions needed them): run narration-measure '
              'again (free, local).')
    ep = read_json(artifact_path(rd, n, 'edit'), required=True)
    holds = sorted(ep.get('holds') or [], key=lambda h: float(h['at_audio_s']))
    if choice[1] == 'luckiest-guy':
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', args.box_color or '') or n_words(args.box_color_why) < MIN_NOTE_WORDS:
            error('The word box needs its colour for this video: --box-color #RRGGBB (a colour of the video\'s own '
                  'palette that stands out from the pictures behind the caption line) and --box-color-why "...".')
        out.update({'box_color': args.box_color.upper(), 'box_color_why': args.box_color_why})
    words, problems = [], []
    counts = {'whisper': 0, 'shared': 0, 'between': 0}
    for i, line in enumerate(lines, 1):
        r = rows.get(i) or {}
        ws, prob = cap.line_words(line.get('text') or '', r.get('word_times'), (r.get('start_s'), r.get('end_s')),
                                  tokens_of, strip_tags, language)
        if prob:
            problems.append({'line': line.get('id'), 'problem': prob})
            continue
        for w in ws:
            counts[w['timing']] += 1
            words.append({'w': w['w'], 's': cap.edit_time(w['s'], holds), 'e': cap.edit_time(w['e'], holds),
                          'line': line.get('id'), 'timing': w['timing']})
    if problems:
        error('Some lines cannot be captioned from the measured narration.', problems[:10])
    for a, b in zip(words, words[1:]):
        if b['s'] < a['s']:
            b['s'] = a['s']
        if b['e'] < b['s']:
            b['e'] = b['s']
    total = len(words) or 1
    out.update({'language': language, 'fps': int(args.fps), 'words': words,
                'timing_evidence': {**counts, 'words': len(words), 'whisper_share': round(counts['whisper'] / total, 3)},
                'holds_applied': len(holds),
                'made_from': {'line_times_measured_at': lt.get('measured_at'), 'script_sha256': script_hash(lines),
                              'narration_for_edit_sha256': (ep.get('narration_for_edit') or {}).get('sha256'),
                              'edit_plan_made_at': ep.get('made_at')}})
    write_json(captions_plan_path(rd, n), out)
    warn = []
    if counts['between']:
        warn.append(f'{counts["between"]} words had no time from Whisper (a line found on a second listen): each sits '
                    'between its timed neighbours by its length')
    emit({'ok': True, 'captions': 'on', 'style': choice[1], 'plan': str(captions_plan_path(rd, n)),
          'words': len(words), 'timing_evidence': out['timing_evidence'], 'warnings': warn,
          'next': 'With CapCut closed: captions-build --draft "<project folder>" (then capcut_tools.py capcut-repair '
                  '--keep-text), then timeline-check reads them back.'})


def cmd_captions_build(args):
    """Write the planned captions into the CapCut project (CapCut closed): the chosen look's tracks, each text at its
    planned time, then read back from the project and checked against the plan. Then capcut-repair --keep-text."""
    rd, st = run_folder(args)
    n = int(args.video)
    cap = _captions()
    plan = read_json(captions_plan_path(rd, n))
    issues, choice = captions_plan_facts(rd, n, plan)
    if issues:
        error('The captions plan is not ready.', issues)
    try:
        rec = cap.build_draft(args.draft, plan, rd / '70-edit' / f'video-{n:02d}' / 'captions-build', replace=args.replace)
    except RuntimeError as exc:
        error(str(exc))
    rec.update({'draft': str(Path(args.draft)), 'built_at': now()})
    write_json(rd / '70-edit' / f'video-{n:02d}' / 'captions-built.json', rec)
    emit({**rec, 'next': 'capcut_tools.py capcut-repair --draft "<project folder>" --keep-text; name the project in '
                         'timeline.json (capcut_draft): timeline-check reads the captions back from it.'},
         0 if rec.get('ok') else 2)


def cmd_captions_check(args):
    rd, st = run_folder(args)
    n = int(args.video)
    cap = _captions()
    plan = read_json(captions_plan_path(rd, n))
    issues, choice = captions_plan_facts(rd, n, plan)
    res = {'ok': False, 'issues': issues}
    if not issues:
        res = cap.check_draft(args.draft, plan)
    emit(res, 0 if res.get('ok') else 2)


def cmd_captions_preview(args):
    """A few frames of the planned captions as PNGs (PIL, not CapCut's renderer) to look at the look and the timing:
    which word is lit or boxed at each moment, over one of the video's stills when --background is given."""
    rd, st = run_folder(args)
    n = int(args.video)
    cap = _captions()
    plan = read_json(captions_plan_path(rd, n), required=True)
    if plan.get('captions') != 'on':
        error('Captions are off for this run: there is nothing to preview.')
    w, h = (int(x) for x in args.canvas.lower().split('x'))
    files = cap.preview(plan, Path(args.out), w, h, background=args.background, start_s=args.start, frames=args.frames)
    emit({'ok': True, 'files': files, 'note': 'PIL drawing of the layout, font, colours and timing; the outline thickness '
                                              'is approximate. CapCut draws the real captions.'})


def capcut_audio_segments(draft):
    """Every audio segment of a CapCut project, read from its own timeline document (the newest readable one of
    draft_content.json, template-2.tmp and the Timelines/ copies): the file it plays, where it sits (s), the stretch
    of the file it uses, and its speed (a curve speed is flagged)."""
    d = Path(str(draft)).expanduser()
    docs = [p for p in [d / 'draft_content.json', d / 'template-2.tmp'] if p.is_file()] + \
        sorted(d.glob('Timelines/*/draft_content.json'))
    content, doc = None, None
    for p in sorted(docs, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            c = json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(c, dict) and c.get('tracks') is not None:
            content, doc = c, p
            break
    if content is None:
        raise OSError(f'no readable timeline document in {d}')
    mats = {m.get('id'): m for m in (content.get('materials') or {}).get('audios') or []}
    speeds = {m.get('id'): m for m in (content.get('materials') or {}).get('speeds') or []}
    out = []
    for tr in content.get('tracks') or []:
        if tr.get('type') != 'audio':
            continue
        for s in tr.get('segments') or []:
            m = mats.get(s.get('material_id'))
            if not m:
                continue
            tg, src = s.get('target_timerange') or {}, s.get('source_timerange') or {}
            sp = next((speeds[r] for r in s.get('extra_material_refs') or [] if r in speeds), {})
            a, la = int(tg.get('start') or 0) / 1e6, int(tg.get('duration') or 0) / 1e6
            sa, ls = int(src.get('start') or 0) / 1e6, int(src.get('duration') or 0) / 1e6
            speed = s.get('speed') if s.get('speed') is not None else sp.get('speed', 1)
            out.append({'file': m.get('path'), 'start_s': round(a, 3), 'end_s': round(a + la, 3),
                        'source_start_s': round(sa, 3), 'source_end_s': round(sa + ls, 3), 'speed': float(speed or 1),
                        'curve_speed': bool(sp.get('curve_speed')) or bool(sp.get('mode')), 'volume': s.get('volume'),
                        'track': tr.get('name') or tr.get('id'), 'read_from': str(doc)})
    return out


def narration_track_issues(rd, segs, expect):
    """The approved narration in the cut, whole: every narration segment plays the edit plan's file (unchanged since
    retime-shots) at speed 1, each where it belongs, and together they cover the file from 0 to its end exactly once.
    A narration sped up, slowed, trimmed, cut or replaced is refused here, even when the export still has the right
    length."""
    if not expect:
        return []                    # no edit plan yet: edit_plan_missing_run_retime_shots says so
    out = []
    f = _run_file(rd, expect['file'])
    if not f.is_file():
        out.append('narration_file_missing')
    elif file_sha256(f) != expect.get('sha256'):
        out.append('narration_file_changed_since_retime_shots')
    if not segs:
        return out + ['narration_track_missing']
    want, dur = _pkey(f), float(expect.get('duration_s') or 0)
    rows = []
    for j, s in enumerate(segs, 1):
        if not s.get('file') or _pkey(_run_file(rd, s['file'])) != want:
            out.append(f'narration_track_{j}_plays_another_file')
            continue
        try:
            a, b = float(s['start_s']), float(s['end_s'])
            sa = float(s.get('source_start_s') or 0)
            sb = float(s['source_end_s']) if s.get('source_end_s') is not None else None
        except (KeyError, TypeError, ValueError):
            out.append(f'narration_track_{j}_needs_start_end_and_source_times')
            continue
        if sb is None:
            out.append(f'narration_track_{j}_source_range_not_recorded')
            sb = sa + (b - a)
        sp = s.get('speed')
        if sp is None:
            out.append(f'narration_track_{j}_speed_not_recorded')
        elif abs(float(sp) - 1.0) > 1e-3 or s.get('curve_speed'):
            out.append(f'narration_track_{j}_speed_{float(sp):g}_not_1')
        if abs((b - a) - (sb - sa)) > 0.05:
            out.append(f'narration_track_{j}_length_differs_from_its_source')
        if abs(a - sa) > 0.05:
            out.append(f'narration_track_{j}_moved_off_its_time')
        rows.append((sa, sb))
    rows.sort()
    if rows:
        cur = 0.0
        for sa, sb in rows:
            if sa - cur > 0.05:
                out.append(f'narration_cut_{round(sa - cur, 1)}s_missing_at_{_mmss(cur)}')
            elif cur - sa > 0.05:
                out.append(f'narration_plays_twice_near_{_mmss(sa)}')
            cur = max(cur, sb)
        if dur and dur - cur > 0.1:
            out.append(f'narration_trimmed_{round(dur - cur, 1)}s_missing_at_the_end')
    return out


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
    # The silence after each line, read from the audio itself (av_tools.line_gaps: the quiet run around Whisper's
    # boundary; Whisper alone places a line's ends to within about 0.2 s). It is what a held silence is decided
    # against (hold-decide) and what the edit adds to (retime-shots), never an average: lines differ.
    tmpdir, joined, gap_error, audio_gaps = tempfile.mkdtemp(prefix='narration-measure-'), None, None, {}
    files = [folder / c['file'] for c in sorted(chunks, key=lambda x: x['id'])
             if c['id'] <= max(x['id'] for x in use) and (folder / c['file']).is_file()]
    try:
        av = _av()
        joined = av.concat_audio(files, Path(tmpdir) / 'narration.wav')
        g = av.line_gaps(joined, [{'index': li, 'start_s': rows[li]['start_s'], 'end_s': rows[li]['end_s']}
                                  for li in order], last_index=len(lines))
        audio_gaps = {int(x['index']): x for x in g['gaps']}
    except (RuntimeError, ValueError, OSError, ImportError, KeyError) as exc:
        gap_error = f'{type(exc).__name__}: {str(exc)[:200]}'
    for li in order:
        x = audio_gaps.get(li)
        if x:
            rows[li].update({'gap_after_s': x['gap_s'], 'gap_span_s': x['span_s'], 'gap_basis': x['basis']})
            if x.get('last_line'):
                rows[li]['gap_is_tail'] = True
            # Inside the silence: where an added silence would go (the middle of its longest quiet stretch, so a breath
            # stays with its line), how loud the voice's own silence is, and what else it holds (a breath, a click).
            for k in ('subrun_s', 'insert_at_s', 'floor_under_speech_db', 'other_material_s'):
                if x.get(k) is not None:
                    rows[li]['gap_' + k] = x[k]
    # A cue at a line's end (or start) is measured on the audio's own silence there, the basis hold-decide and the edit
    # use: Whisper's word ends drift by up to ~0.4 s, enough to hide a short pause or invent one. The usual gap it is
    # compared with is read the same way (lines without a pause cue, inside one part). The word-based value stays.
    audio_usual = [rows[li]['gap_after_s'] for li in order
                   if rows[li].get('gap_after_s') is not None and not rows[li].get('gap_is_tail')
                   and li not in pause_tag_at and li + 1 in rows and rows[li + 1]['part'] == rows[li]['part']]
    if audio_usual:
        base_audio = statistics.median(audio_usual)
        for t in tag_rows:
            if not (t['at_end'] or t['at_start']):
                continue
            g = (rows.get(t['li'] if t['at_end'] else t['li'] - 1) or {}).get('gap_after_s')
            m = next((x for x in measured_tags if x['line'] == t['line'] and x['tag'] == t['tag']), None)
            if g is None or m is None or m.get('basis') == 'audio':
                continue
            m.update({'words_gap_s': m['gap_s'], 'gap_s': round(g, 2), 'excess_s': round(g - base_audio, 2),
                      'usual_gap_s': round(base_audio, 2), 'basis': 'audio'})
        costs = {}
        for m in measured_tags:
            costs.setdefault(m['tag'], []).append(m['excess_s'])
        costs = {k: round(statistics.median(v), 2) for k, v in costs.items()}
        tag_excess = sum(max(0.0, m['excess_s']) for m in measured_tags)
        per_line = round((tot_dur - tot_speech - tag_excess) / nlines, 3) if nlines else None
    part_ends = {int(c['line_end']) for c in chunks}
    between = [float(rows[li]['gap_after_s']) for li in order if rows[li].get('gap_basis') == 'audio'
               and rows[li].get('gap_after_s') is not None and not rows[li].get('gap_is_tail') and li not in part_ends]
    natural_audio = statistics.median(between) if between else None
    # The joins: the gap between the parts against the voice's own gap between lines, the pace on each side, and
    # any words said twice across it. A join shorter than the natural gap gets a seam hold in the edit (retime-shots),
    # unless the line before it carries a planned or decided hold (that silence is decided as a whole: never stacked).
    held = {p['line'] for p in script_pause_plan(lines)[0]} | set(hold_decisions(rd, n)['decisions'])
    seams, by_index = [], {r['index']: r for r in rows.values()}
    ordered_parts = sorted(use, key=lambda x: x['id'])
    for a_c, b_c in zip(ordered_parts, ordered_parts[1:]):
        if b_c['id'] != a_c['id'] + 1:
            continue
        last, first = by_index.get(int(a_c['line_end'])), by_index.get(int(b_c['line_start']))
        if not last or not first or last['end_s'] is None or first['start_s'] is None:
            continue
        if last.get('gap_basis') == 'audio' and last.get('gap_after_s') is not None and natural_audio is not None:
            gap, natural_here = round(float(last['gap_after_s']), 3), natural_audio
        else:
            gap, natural_here = round(first['start_s'] - last['end_s'], 3), natural_gap
        planned = str(last['id']) in held
        hold = round(natural_here - gap, 2) if (not planned and natural_here - gap >= 0.08) else 0.0
        def side(lo_i, hi_i):
            rs = [by_index[x] for x in range(lo_i, hi_i + 1) if x in by_index and by_index[x]['start_s'] is not None]
            w = sum(count_words(lines[r['index'] - 1].get('text') or '') for r in rs)
            span = (rs[-1]['end_s'] - rs[0]['start_s']) if len(rs) > 1 else 0
            return round(w / (span / 60)) if span > 3 else None
        t = (last['end_s'] + first['start_s']) / 2
        before_tok = [h for h, a, b, u in heard_tokens if b <= t][-3:]
        after_tok = [h for h, a, b, u in heard_tokens if a >= t][:3]
        seams.append({'after_part': a_c['id'], 'after_line': last['id'], 'at_s': round(t, 3), 'gap_s': gap,
                      'natural_gap_s': round(natural_here, 3), 'seam_hold_s': hold,
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
    delivery, delivery_error, cadence_usual, line_stats = None, None, {}, {}
    if not args.no_delivery:
        try:
            av = _av()
            spans = {}
            for b in beat_rows:
                spans[str(b['id'])] = (b['start_s'], b['end_s'])
            for li in order:        # every line, so a cue's line can be compared with this take's usual line
                if rows[li].get('start_s') is not None and rows[li].get('end_s') is not None:
                    spans[f'line_{li}'] = (rows[li]['start_s'], rows[li]['end_s'])
            for s in seams:
                spans[f'seam_{s["after_part"]}_before'] = (max(0.0, s['at_s'] - 20), s['at_s'])
                spans[f'seam_{s["after_part"]}_after'] = (s['at_s'], s['at_s'] + 20)
            wav = joined if joined is not None else av.concat_audio(files, Path(tmpdir) / 'narration.wav')
            delivery = av.delivery(f'video-{n:02d} narration', wav, all_words, spans=spans, segments=all_segments)
            line_stats = {int(k[5:]): v for k, v in (delivery.get('spans') or {}).items() if k.startswith('line_')}
            delivery['spans'] = {k: v for k, v in (delivery.get('spans') or {}).items() if not k.startswith('line_')}
            # How each line ends and the next begins (the facts a held silence's transition is decided on), next to
            # this voice's usual endings.
            cad = av.line_cadence(wav, [{'index': li, 'start_s': rows[li]['start_s'], 'end_s': rows[li]['end_s'],
                                         'gap_span_s': rows[li].get('gap_span_s')} for li in order])
            for li, c in (cad.get('boundaries') or {}).items():
                if int(li) in rows:
                    rows[int(li)]['cadence'] = c
            cadence_usual = cad.get('usual') or {}
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
    shutil.rmtree(tmpdir, ignore_errors=True)
    # Each cue as it came out on this take (05): the silence a pause cue left beyond the voice's usual gap, the time a
    # delivery cue added to its own line against this voice's pace, how that line ended, and whether the next line
    # carried the change on (spill). Kept with the voice setup and the take, so takes can be compared.
    setup = {'voice_id': manifest.get('voice_id'), 'model_id': manifest.get('model_id'),
             'settings': manifest.get('voice_settings') or {}}
    def _extra(li):
        r = rows.get(li)
        if not r or r.get('start_s') is None or r.get('end_s') is None or not forecast_wpm:
            return None
        w = count_words(lines[li - 1].get('text') or '')
        return round((r['end_s'] - r['start_s']) - w * 60 / forecast_wpm, 2) if w else None
    tagged_lines = {t['li'] for t in tag_rows}
    usual_line = {}
    for key in ('speech_level_db', 'speech_rate_wpm', 'pitch_range_st'):
        vals = [v.get(key) for k, v in line_stats.items() if k not in tagged_lines and v.get(key) is not None]
        if vals:
            usual_line[key] = statistics.median(vals)
    cue_obs, cue_outcomes = [], []
    for t in tag_rows:
        li, r = t['li'], rows.get(t['li']) or {}
        m = next((x for x in measured_tags if x['line'] == t['line'] and x['tag'] == t['tag']), None)
        nxt = rows.get(li + 1) or {}
        if t.get('category') == 'pause':
            gli = li if t['at_end'] else li - 1 if t['at_start'] else None
            held = lines[gli - 1] if gli and 0 < gli <= len(lines) else {}
            planned = held.get('pause_total_s') if held.get('pause_via') == 'tag' else None
            outcome = pause_cue_outcome(planned, m['gap_s'] if m else None) or \
                {'outcome': 'performed', 'measured_s': m['gap_s'] if m else None,
                 'note': 'no whole silence planned through this cue: what it gave is decided at the holds'}
            outcome['silence_after'] = str(rows[gli]['id']) if gli in rows else None
        else:
            outcome = delivery_cue_outcome(t['inner'], line_stats.get(li), usual_line) if line_stats else \
                {'outcome': 'not_measured', 'note': 'delivery not measured (--no-delivery)'}
        cue_outcomes.append({'line': t['line'], 'tag': t['tag'], **outcome})
        cue_obs.append({'tag': t['tag'], 'category': t.get('category'), 'line': t['line'],
                        'at': 'start' if t['at_start'] else 'end' if t['at_end'] else 'inside',
                        'excess_s': m['excess_s'] if m else None, 'gap_s': m['gap_s'] if m else None,
                        'line_extra_s': _extra(li), 'end_level_db': (r.get('cadence') or {}).get('end_level_db'),
                        'next_line_extra_s': _extra(li + 1),
                        'next_end_level_db': (nxt.get('cadence') or {}).get('end_level_db'),
                        'usual_end_level_db': cadence_usual.get('end_level_db') if cadence_usual else None,
                        'outcome': cue_outcomes[-1].get('outcome'),
                        'take': prints.get(r.get('part')), **setup, 'measured_at': now()})
    # The joins: did the recording boundary change the delivery where the story goes on (not at a chapter turn)?
    chapter_first = set()
    for b in read_json(vd / 'beat-map.json').get('beats') or []:
        try:
            if b.get('chapter_start'):
                chapter_first.add(int(b['line_start']))
        except (KeyError, TypeError, ValueError):
            pass
    by_id = {str(rows[li]['id']): li for li in order}
    for sm in seams:
        li_last = by_id.get(str(sm['after_line']))
        sm['chapter_break'] = (li_last + 1) in chapter_first if li_last else False
        sm['boundary_effects'] = seam_boundary_effects((rows.get(li_last) or {}).get('cadence') or {}, cadence_usual)
    for r in rows.values():
        # each comparable token's [start, end] on the narration (None where Whisper did not hear it): the captions'
        # word times
        r['word_times'] = [None if x is None else [round(x[0], 3), round(x[1], 3)] for x in (r.pop('_tok', None) or [])]
    gaps_now = voice_gap_profile({'lines': list(rows.values())})
    out = {'video': n, 'complete': complete, 'script_sha256': script_hash(lines) if complete else None,
           'narration_file': str(folder / 'narration.wav') if complete else None, 'parts': per_part,
           'duration_s': round(tot_dur, 2), 'words': int(tot_words), 'speech_s': round(tot_speech, 2), 'wpm': wpm,
           'script_words': script_words, 'forecast_wpm': forecast_wpm, 'overall_wpm': overall_wpm,
           'natural_line_gap_median_s': round(natural_gap, 3), 'per_line_overhead_s': per_line,
           'line_gaps_from_audio': gaps_now, 'line_gaps_error': gap_error, 'cadence_usual': cadence_usual,
           'alignment_match_ratio': round(ratio_all, 3), 'tags_measured': measured_tags,
           'cue_observations': cue_obs, 'cue_outcomes': cue_outcomes, 'unheard_lines': unheard, 'rechecked_lines': rechecks,
           'tags_read_aloud': read_aloud,
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
        keep = {(o.get('tag'), o.get('line'), o.get('take')) for o in cue_obs}
        observations = ([o for o in prev.get('cue_observations') or []
                         if (o.get('tag'), o.get('line'), o.get('take')) not in keep] if same else []) + cue_obs
        vl['measured'] = {'voice_id': manifest['voice_id'], 'model_id': manifest['model_id'], 'settings': settings,
                          'wpm': wpm, 'words': int(tot_words), 'script_words': script_words,
                          'forecast_wpm': forecast_wpm, 'overall_wpm': overall_wpm, 'speech_s': round(tot_speech, 2),
                          'duration_s': round(tot_dur, 2), 'lines': nlines, 'per_line_overhead_s': per_line,
                          'natural_gap_s': gaps_now.get('median_s') or round(natural_gap, 3),
                          'tag_costs_s': tag_costs, 'cue_observations': observations[-120:],
                          'parts': [p['id'] for p in per_part], 'measured_at': now(),
                          'method': out['method']}
        for k in ('measured_wpm', 'measured_overhead_s', 'measured_overhead_lines', 'measured_wpm_source'):
            vl.pop(k, None)
        write_json(vl_path, vl)
        wrote = True
    warnings = []
    for sm in seams:
        if sm.get('boundary_effects') and not sm.get('chapter_break'):
            warnings.append(f"part join after {sm['after_line']} at {_mmss(sm['at_s'])} (not a chapter turn): "
                            + '; '.join(sm['boundary_effects'])
                            + '. Listen there; if the narrator concludes or restarts mid-scene, re-record with the '
                              'parts split at chapter turns (beat-map chapter_start).')
    if ratio_all < 0.9:
        warnings.append('Under 90% of the script words were matched: listen for missing or extra words, or a script edit.')
    for m in measured_tags:
        if classify_tag(m['tag'][1:-1]).get('category') == 'pause' and m['excess_s'] < 0.2:
            warnings.append(f"{m['line']} {m['tag']} made no measurable pause ({m['gap_s']} s against the usual "
                            f"{m.get('usual_gap_s', round(natural_gap, 2))} s, {m.get('basis', 'word times')}): listen "
                            "(was it read aloud?)")
    for c in cue_outcomes:
        if c.get('outcome') in ('short', 'long'):
            warnings.append(f"{c['line']} {c['tag']}: the pause came out {c['outcome']} ({c['measured_s']} s against "
                            f"{c['planned_s']} s planned, tolerance {c['tolerance_s']} s): decide it at the holds")
        elif c.get('outcome') in ('opposite', 'no_clear_change'):
            warnings.append(f"{c['line']} {c['tag']}: the line did not move as the cue asked ({c['outcome']}): listen")
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
          'natural_line_gap_median_s': round(natural_gap, 3), 'tags_measured': measured_tags, 'cue_outcomes': cue_outcomes,
          'line_gaps_from_audio': gaps_now, 'line_gaps_error': gap_error, 'cadence_usual': cadence_usual,
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
                  'plan-check (real_forecast_s against the export window); holds (each planned pause next to the gap '
                  'the voice really left there) and hold-decide for every pause whose lines are recorded; when '
                  'complete: retime-shots.'},
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
    inv = cards_inventory(rd)
    for vid in refs:
        tfile = rd / '10-media' / vid / 'transcript.txt'
        wpm = wpm_from_transcript_raw(tfile.read_text(encoding='utf-8', errors='replace')) if tfile.exists() else None
        out[vid] = {'wpm': wpm, **ref_pace_stats(rd, vid, (inv.get(vid) or {}).get('duration_s')),
                    **(ref_pause_profiles(rd, [vid]).get(vid) or {})}
    narr = None
    if args.video:
        lt = read_json(rd / '50-audio' / f'video-{int(args.video):02d}' / 'line-times.json')
        if lt:
            sc = read_json(video_dir(rd, args.video) / 'script.json').get('lines') or []
            narr = {'wpm': lt.get('wpm'), 'overall_wpm': lt.get('overall_wpm'), 'complete': lt.get('complete'),
                    **sentence_cadence([r.get('text') or '' for r in sc]), **(lt.get('pause_profile') or {}),
                    'beats': lt.get('beats')}
    emit({'ok': True, 'references': out, 'narration': narr, 'definitions': PACE_DEFINITIONS,
          'note': 'wpm / active_wpm = words over Whisper\'s speech time; overall_wpm = words over the whole span, '
                  'pauses included; pauses = silence between consecutive words (Whisper word timestamps). The same '
                  'functions for references and narration. A different pace is a fact to read, never a fault: a '
                  'slower narrator is not a duller one.'})


def _narration_source(rd, video, tmpdir):
    """The recorded narration as one file on line-times' clock: narration.wav once it is complete, else the recorded
    parts joined in order (as narration-measure joins them)."""
    n = int(video)
    folder = rd / '50-audio' / f'video-{n:02d}'
    if (folder / 'narration.wav').is_file() and read_json(folder / 'line-times.json').get('complete'):
        return folder / 'narration.wav'
    chunks = read_json(folder / 'manifest.json').get('chunks') or []
    files = [folder / c['file'] for c in sorted(chunks, key=lambda x: x['id']) if (folder / c['file']).is_file()]
    if not files:
        error('No recorded narration to preview.')
    return _av().concat_audio(files, Path(tmpdir) / 'narration.wav')


def hold_previews(rd, video, lines, lid, totals, intos='clean', outs='clean'):
    """Short local previews of one held silence at several whole lengths (the voice's own gap among them) and, when
    asked, several transitions (intos/outs: 'clean,fade'): the words around it, the silence, and, once the stills
    exist, the shot(s) on screen as the edit would cut them. A transition that cannot be done here is listed with why,
    not rendered. For the user's ears and the director's comparison; a preview shows a still without CapCut's moves,
    captions or music."""
    n = int(video)
    index = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
    if lid not in index:
        error('--preview names a line the script does not have.', lid)
    i = index[lid]
    lt, current, _ = line_times_state(rd, n)
    if not current:
        error('line-times.json does not describe the recorded parts: run narration-measure first.')
    rows = {int(r['index']): r for r in lt.get('lines') or []}
    g = measured_gap(rows, i, len(lines))
    if not g or g['natural_gap_s'] is None:
        error('A preview needs this line and the next recorded and measured.', lid)
    natural = float(g['natural_gap_s'])
    r = rows[i]
    span = g.get('span_s') if g.get('basis') == 'audio' else None
    at = (g.get('insert_at_s') if g.get('insert_at_s') is not None else (span[0] + span[1]) / 2) if span else \
        (r['end_s'] + (rows[i + 1]['start_s'] if i + 1 in rows else r['end_s'])) / 2
    last = i == len(lines)
    prev_r, next_r = rows.get(i - 1) or r, rows.get(i + 1)
    start = max(0.0, max(prev_r['start_s'], r['end_s'] - 15.0) - 0.3)
    end = (min(next_r['end_s'], (next_r['start_s'] or 0) + 10.0) + 0.4) if next_r else None
    wanted = sorted({round(float(x), 2) for x in str(totals or '').replace(';', ',').split(',') if x.strip()})
    if any(x <= 0 for x in wanted):
        error('--totals are whole silences in seconds, each above 0.')
    pick = lambda s, allowed: [x for x in dict.fromkeys(y.strip() for y in str(s or 'clean').split(',') if y.strip())
                               if x in allowed] or ['clean']
    intos, outs = pick(intos, TRANSITION_INTO), pick(outs, TRANSITION_OUT)
    variants, refused = [('voice-gap', natural, 0.0, 'clean', 'clean')], []
    for x in wanted:
        add = round(max(0.0, x - natural), 3)
        for ti in intos:
            for to in outs:
                if (ti, to) != ('clean', 'clean'):
                    _, problems = fade_windows(g, ti, to, last_line=last)
                    if add <= 0:
                        problems = ['nothing is added at this length: a fade would change the voice\'s own gap'] + problems
                    if problems:
                        refused.append({'variant': f'total-{x:.2f}s into-{ti} out-of-{to}', 'why': problems})
                        continue
                name = f'total-{x:.2f}s' + ('' if (ti, to) == ('clean', 'clean') else f'-into-{ti}-out-of-{to}')
                variants.append((name, x, add, ti, to))
    out_dir = rd / '70-edit' / f'video-{n:02d}' / 'hold-previews' / lid
    out_dir.mkdir(parents=True, exist_ok=True)
    shot = hold_shot(rd, n, i)
    made = []
    with tempfile.TemporaryDirectory() as tmp:
        src = _narration_source(rd, n, tmp)
        dur = probe(src)['duration_s']
        end = dur if end is None or last else min(end, dur)
        at = dur if last else at
        for label, total, add, ti, to in variants:
            wav = out_dir / f'{label}.wav'
            fades, _ = fade_windows(g, ti, to, last_line=last)
            fa = (f",afade=t=out:st={fades['into'][0] - start:.3f}:d={fades['into'][1] - fades['into'][0]:.3f}"
                  if fades.get('into') else '')
            fb = f",afade=t=in:st=0:d={fades['out_of'][1] - fades['out_of'][0]:.3f}" if fades.get('out_of') else ''
            filt = [f'[0:a]atrim=start={start:.3f}:end={at:.3f},asetpts=PTS-STARTPTS{fa}[a]',
                    f'anullsrc=r=44100:cl=stereo,atrim=duration={max(add, 0.001):.3f}[s]']
            labels = '[a][s]'
            if at < end - 0.01:
                filt.append(f'[0:a]atrim=start={at:.3f}:end={end:.3f},asetpts=PTS-STARTPTS{fb}[b]')
                labels += '[b]'
            filt.append(f'{labels}concat=n={len(labels) // 3}:v=0:a=1,aresample=44100[out]')
            run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src), '-filter_complex',
                     ';'.join(filt), '-map', '[out]', '-ac', '2', '-c:a', 'pcm_s16le', str(wav)])
            item = {'variant': label, 'whole_silence_s': round(natural + add, 2), 'added_s': add, 'audio': str(wav),
                    'silence_centre_s': round((at - start) + add / 2, 3), 'into': ti, 'out_of': to}
            stills = []
            if shot and shot.get('still'):
                cut = (at - start) + add                  # the hold stays on the shot before the cut
                if shot.get('next_shot', {}).get('still'):
                    stills = [(shot['still'], cut), (shot['next_shot']['still'], max(0.1, (end - start) + add - cut))]
                else:
                    stills = [(shot['still'], (end - start) + add)]
            if stills:
                mp4 = out_dir / f'{label}.mp4'
                cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y']
                for path, d in stills:
                    cmd += ['-loop', '1', '-t', f'{d:.3f}', '-i', str(path)]
                cmd += ['-i', str(wav), '-filter_complex',
                        ''.join(f'[{k}:v]scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2,'
                                f'setsar=1,fps=30[v{k}];' for k in range(len(stills))) +
                        ''.join(f'[v{k}]' for k in range(len(stills))) + f'concat=n={len(stills)}:v=1:a=0[v]',
                        '-map', '[v]', '-map', f'{len(stills)}:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', str(mp4)]
                run_cmd(cmd)
                item['video'] = str(mp4)
            made.append(item)
    words_before = strip_tags(lines[i - 1].get('text') or '')
    words_after = strip_tags(lines[i].get('text') or '') if i < len(lines) else '(the end of the narration)'
    guide = [f'# Held silence after {lid}: listening previews', '',
             f'Before: "{words_before}"', f'After: "{words_after}"', '',
             f'The voice\'s own gap here: {natural:.2f} s ({g.get("basis")}). Each file is the same moment with a '
             'different whole silence after the line (and, where named, a different transition); nothing else differs.',
             '']
    guide += [f'- {m["variant"]}: about {m["whole_silence_s"]:.2f} s of silence'
              + ('' if (m['into'], m['out_of']) == ('clean', 'clean') else f', into {m["into"]}, out of {m["out_of"]}')
              + f' -> {m.get("video") or m["audio"]}' for m in made]
    if refused:
        guide += ['', 'Not rendered (they could not be done here without touching the voice, or would change nothing):']
        guide += [f'- {x["variant"]}: ' + '; '.join(x['why']) for x in refused]
    guide += ['', 'Listen for: does the line land, or does the silence wait for nothing? Does the voice stop the way '
              'the moment wants (a clean stop can be the point)? Does the next line come back in naturally, or too '
              'late? Would you want the voice to go on sooner?',
              'Previews show the still only: no camera moves, captions, transitions or music.' if shot and shot.get('still')
              else 'Audio only: the picture and the music for this moment do not exist yet.']
    (out_dir / 'index.md').write_text('\n'.join(guide) + '\n', encoding='utf-8')
    return {'line': lid, 'natural_gap_s': natural, 'gap_basis': g.get('basis'), 'folder': str(out_dir),
            'guide': str(out_dir / 'index.md'), 'variants': made, 'refused': refused,
            'inside_silence': {k: g.get(k) for k in ('insert_at_s', 'subrun_s', 'floor_under_speech_db', 'other_material_s')},
            'picture': bool(shot and shot.get('still')),
            'limits': 'A preview is the recorded voice with the silence set as named, over the shot\'s still when it '
                      'exists: no camera moves, captions, transitions or music. No agent here can hear it; the '
                      'user\'s ears decide what it sounds like.'}


def cmd_holds(args):
    """Every planned pause next to what the recorded voice really did there (gathers; free): the proposal, the gap the
    voice left after that line (from the audio), this voice's own range of gaps, the words around it, the shot on
    screen and its still once they exist, and the decision in force. With --preview LINE --totals a,b: short local
    previews of that moment at each whole silence, the voice's own gap among them. Nothing is decided here."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    lines = read_json(vd / 'script.json', required=True).get('lines') or []
    hf = hold_facts(rd, n, lines)
    for h in hf['holds']:
        if h.get('index'):
            sh = hold_shot(rd, n, h['index'])
            if sh:
                h['on_screen'] = sh
    plan = read_json(artifact_path(rd, n, 'edit'))
    out = {'ok': True, 'video': n, 'holds': hf['holds'], 'voice_gaps': hf['voice_gaps'],
           'endings_usual': hf['endings_usual'],
           'line_times_current': hf['line_times_current'], 'added_s': hf['added_s'],
           'undecided': hf['undecided'], 'decided_after_narration': hf['decided_narration'],
           'decided_with_picture': hf['decided_picture'],
           'edit_plan_timed_from_these_decisions': (plan.get('hold_decisions_sha256') == hold_decisions_sha(rd, n))
           if plan else None,
           'reading': 'A planned pause is a proposal. For each: does the voice\'s own gap here already give the moment '
                      'what it needs? What does the viewer see and hear while it lasts, and would they wait, or want '
                      'the voice to go on? Decide the WHOLE silence (or no hold) with hold-decide; the edit adds only '
                      'the difference with the measured gap. No quota, no formula, no length copied from a reference. '
                      'The transition: `ending` says how the line lands (the pitch of its last clear vowel against the '
                      'line, falling below zero; how long and how soft its end is after that vowel, where a creaky '
                      'landing shows; its punctuation) and how the next line starts again (its reset and lead-in), '
                      'next to this voice\'s usual (`endings_usual`). A landed line takes a silence as meant; one left '
                      'hanging (level or rising, little softening) can make a long silence sound like a dropout or a '
                      'wait for a laugh. Clean is the default; a fade is possible only on audible room tone '
                      '(`inside_silence`); the bed is often the better lever. Numbers, never a verdict: listen.',
           'next': 'hold-decide --line Lnnn --stage narration (--total S | --no-hold) [--into clean|fade] '
                   '[--out-of clean|fade] [--bed continues|enters|stops|dips|swells|none] --reason "..." for every pause '
                   'whose line and the next are recorded; after the stills exist, again with --stage picture (--bed '
                   'required).'}
    if args.preview:
        out['preview'] = hold_previews(rd, n, lines, args.preview.strip(), args.totals, args.into, args.out_of)
    emit(out)


def cmd_hold_decide(args):
    """Decide one held silence on evidence: the WHOLE silence wanted after the line (--total, the voice's own gap
    included) or none (--no-hold), at a stage: 'narration' (the voice is recorded and measured there) or 'picture'
    (the shot on screen has its still). The edit adds only the difference with the gap the voice really left; a
    decision does not touch the reviewed script, and every earlier decision is kept in the file's history."""
    rd, st = run_folder(args)
    n = int(args.video)
    vd = video_dir(rd, n)
    lines = read_json(vd / 'script.json', required=True).get('lines') or []
    index = {str(r.get('id') or f'L{i + 1:03d}'): i + 1 for i, r in enumerate(lines)}
    lid = args.line.strip()
    if lid not in index:
        error('--line names a line the script does not have.', lid)
    if (args.total is None) == (not args.no_hold):
        error('Give the whole silence wanted after the line (--total S: the voice\'s own gap included) or --no-hold.')
    if args.total is not None and args.total <= 0:
        error('--total is the whole silence in seconds, above 0 (--no-hold for none).')
    if n_words(args.reason) < MIN_NOTE_WORDS:
        error('Say why this length serves this moment (--reason): what the viewer takes in, what the picture and the '
              'sound do, why not shorter or longer.')
    i = index[lid]
    lt, current, prints = line_times_state(rd, n)
    if not current:
        error('line-times.json does not describe the recorded parts: run narration-measure on them first.')
    rows = {int(r['index']): r for r in lt.get('lines') or []}
    g = measured_gap(rows, i, len(lines))
    if not g or g['natural_gap_s'] is None:
        error('The silence after this line exists only once this line and the next are recorded and measured '
              '(narration-measure): decide it then.', lid)
    natural = float(g['natural_gap_s'])
    total = None if args.no_hold else round(float(args.total), 3)
    added = 0.0 if total is None else round(max(0.0, total - natural), 3)
    # The transition: kept clean unless this moment asks otherwise, and a fade only where it can work on the voice's
    # own quiet without touching the voice (fade_windows), and only into or out of silence that is really added.
    into, out_of, bed = args.into, args.out_of, (args.bed or None)
    if args.stage == 'picture' and not bed:
        error('With the picture, say what the bed does around this silence (--bed continues|enters|stops|dips|swells|'
              'none): the transition is the picture, the voice and the sound together.')
    fades, problems = fade_windows(g, into, out_of, last_line=(i == len(lines)))
    if (into == 'fade' or out_of == 'fade') and added <= 0:
        problems.insert(0, 'nothing is added here: a fade would change the voice\'s own natural gap, not a held silence')
    if problems:
        error('That transition cannot be done here without touching the voice or without changing nothing at all.',
              {'line': lid, 'into': into, 'out_of': out_of, 'problems': problems,
               'measured': {k: g.get(k) for k in ('natural_gap_s', 'subrun_s', 'insert_at_s', 'floor_under_speech_db')}})
    p = {x['line']: x for x in script_pause_plan(lines)[0]}.get(lid)
    rec = {'line': lid, 'index': i, 'beat': _line_beats(vd).get(i), 'stage': args.stage, 'total_s': total,
           'no_hold': total is None, 'natural_gap_s': natural, 'gap_basis': g.get('basis'),
           'gap_span_s': g.get('span_s'), 'added_s': added, 'resulting_gap_s': round(natural + added, 3),
           'outcome': ('no added silence: the voice\'s own gap' if total is None else
                       'the voice\'s own gap already gives it: nothing added' if added == 0 else
                       f'adds {added:g} s to the voice\'s {natural:g} s'),
           'reason': args.reason.strip(), 'listened': (args.listened or '').strip() or None, 'decided_at': now(),
           'parts': {k: prints.get(int(k)) for k in (g.get('parts') or {}) if k.isdigit()},
           'proposal': ({k: p[k] for k in ('form', 'seconds', 'via', 'purpose', 'picture', 'sound')} if p else None),
           'voice_gaps': voice_gap_profile(lt),
           'transition': {'into': into, 'out_of': out_of, 'bed': bed, 'fades_on_narration_clock': fades},
           'ending': {'punctuation': line_ending_mark(lines[i - 1].get('text')), **(g.get('cadence') or {})},
           'endings_usual': lt.get('cadence_usual') or {},
           'inside_silence': {k: g.get(k) for k in ('insert_at_s', 'subrun_s', 'floor_under_speech_db',
                                                    'other_material_s')}}
    if args.stage == 'picture':
        sh = hold_shot(rd, n, i)
        if not sh or not sh.get('still'):
            error('The picture stage decides with the picture: the shot on screen during this silence has no still yet.',
                  {'line': lid, 'shot': sh})
        rec['picture'] = sh
    pv = rd / '70-edit' / f'video-{n:02d}' / 'hold-previews' / lid
    if pv.is_dir():
        rec['previews'] = sorted(str(x) for x in pv.iterdir() if x.suffix in ('.wav', '.mp4'))
    data = read_json(holds_path(rd, n))
    decisions, history = data.get('decisions') or {}, data.get('history') or []
    before = decisions.get(lid)
    if before:
        history.append({**before, 'superseded_at': now()})
    decisions[lid] = rec
    write_json(holds_path(rd, n), {'video': n, 'decisions': decisions, 'history': history,
                                   'how': 'hold-decide: the whole silence after a line (the voice\'s own gap included) '
                                          'or none, decided after the narration and again with the picture; the edit '
                                          'adds only the difference with the measured gap (retime-shots).'})
    plan = read_json(artifact_path(rd, n, 'edit'))
    emit({'ok': True, 'decision': rec, 'replaced': before,
          'next': ('retime-shots: the edit plan was timed from other decisions. ' if plan and
                   plan.get('hold_decisions_sha256') != hold_decisions_sha(rd, n) else '') +
                  ('The picture stage confirms it with the shot on screen once the stills exist (--stage picture).'
                   if args.stage == 'narration' else 'Rebuild the CapCut project from the new edit plan if it changed.')})


def cmd_retime_shots(args):
    """Time every shot to the real narration: each cut falls in the silence between the last line of one shot
    and the first line of the next. Only DECIDED holds are inserted (hold-decide: a planned pause is a proposal until
    the voice is measured): each adds the difference between the whole silence decided and the gap the voice really
    left there (measured in narration.wav itself), placed in the middle of that silence so no word is touched, and
    belongs to the shot before it. The result is verified in narration-edit.wav with the same measure, and refused when
    the silence is what brings the edit up to the length. Rewrites shot-plan.json's start_s/end_s (the planned values
    kept once as planned_*), writes 70-edit/video-NN/edit-plan.json and, whenever there are holds, the narration with its
    holds (50-audio/video-NN/narration-edit.wav) -- the audio file the CapCut project uses."""
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
    # Every planned pause is decided against the recorded voice before the edit is timed: its length was a proposal
    # written before any voice existed. Nothing is inserted from a pre-recording estimate.
    hf = hold_facts(rd, n, lines)
    if hf['undecided']:
        error('Every planned pause is decided against the recorded voice before the edit is timed (its length was a '
              'proposal): read `holds`, preview where it helps, then hold-decide each one (--stage narration).',
              {'undecided': hf['undecided'], 'stale': [h['line'] for h in hf['holds'] if h['status'] == 'stale']})
    decided = [h for h in hf['holds'] if h['status'].startswith('decided_')]
    nar = folder / 'narration.wav'
    gmap, av = {}, None
    if decided:
        av = _av()
        gmap = {int(x['index']): x for x in av.line_gaps(nar, [{'index': r['index'], 'start_s': r['start_s'],
                                                                'end_s': r['end_s']} for r in lt['lines']],
                                                       last_index=len(lines))['gaps']}
    holds, pauses, notes = [], [], []
    for h in decided:
        i, d = h['index'], h['decision']
        g = gmap.get(i) or {}
        natural = float(g['gap_s']) if g.get('gap_s') is not None else float(d.get('natural_gap_s') or 0)
        total_s = d.get('total_s')
        added = 0.0 if total_s is None else round(max(0.0, float(total_s) - natural), 3)
        if g.get('basis') == 'audio' and g.get('span_s'):
            # Inside the voice's own silence, in the middle of its longest quiet stretch: the end of the line (its
            # decay, a release) stays with that line, a breath before the next line stays with the next line.
            at = dur if i == len(lines) else (g['insert_at_s'] if g.get('insert_at_s') is not None else
                                              (g['span_s'][0] + g['span_s'][1]) / 2)
        else:
            at = (times[i]['end_s'] + times[i + 1]['start_s']) / 2 if i < len(lines) else dur
            notes.append(f'{h["line"]}: no clear silence found in the audio after it; the hold sits at Whisper\'s '
                         'boundary: listen there')
        if d.get('natural_gap_s') is not None and abs(float(d['natural_gap_s']) - natural) > 0.1:
            notes.append(f'{h["line"]}: the gap measured in narration.wav ({natural:.2f} s) differs from the one the '
                         f'decision read ({float(d["natural_gap_s"]):.2f} s); the decided whole silence is kept')
        tr = d.get('transition') or {}
        into, out_of = tr.get('into') or 'clean', tr.get('out_of') or 'clean'
        fades, problems = fade_windows({**g, 'insert_at_s': at}, into, out_of, last_line=(i == len(lines)))
        if problems or ((into == 'fade' or out_of == 'fade') and added <= 0):
            error(f'{h["line"]}: the decided transition no longer fits the narration as measured now: decide it again '
                  '(hold-decide).', {'into': into, 'out_of': out_of, 'problems': problems or ['nothing is added here']})
        span = g.get('span_s') or [times[i]['end_s'], times[i + 1]['start_s'] if i < len(lines) else dur]
        rec = {'after_line': h['line'], 'index': i, 'at_audio_s': round(at, 3), 'hold_s': added, 'kind': 'script',
               'purpose': (h.get('proposal') or {}).get('purpose') or d.get('reason'), 'total_s': total_s,
               'natural_gap_s': round(natural, 3), 'gap_basis': g.get('basis') or d.get('gap_basis'),
               'stage': d.get('stage'), 'decided_at': d.get('decided_at'),
               'expected_gap_s': round(natural + added, 3),
               'transition': {'into': into, 'out_of': out_of, 'bed': tr.get('bed'), 'fades': fades},
               '_span': [float(span[0]), float(span[1])],
               '_next_start': float(times[i + 1]['start_s']) if i < len(lines) else None}
        pauses.append(rec)
        if added > 0:
            holds.append(rec)
    # A join between recorded parts that came out shorter than the voice's own gap between lines (narration-measure)
    # gets back exactly the missing fraction of a second: continuity, never padding (capped at the natural gap). A join
    # whose line carries a decided pause gets none: that silence was decided as a whole.
    held_lines = {h['line'] for h in hf['holds']}
    seam_s = 0.0
    if not args.no_seam_holds:
        for s in lt.get('seams') or []:
            if float(s.get('seam_hold_s') or 0) > 0 and s.get('after_line') not in held_lines:
                holds.append({'after_line': s.get('after_line'), 'at_audio_s': round(float(s['at_s']), 3),
                              'hold_s': round(float(s['seam_hold_s']), 2), 'kind': 'seam',
                              'purpose': 'restores the voice\'s natural gap at the join between two recorded parts'})
                seam_s += round(float(s['seam_hold_s']), 2)
    holds.sort(key=lambda h: h['at_audio_s'])
    total = round(dur + sum(h['hold_s'] for h in holds), 3)
    # Where each decided pause sits on the edit's own clock: the silence from the end of the line to the next line
    # (the voice's gap plus what was added), so the bed's move (enters, stops, dips...) is placed on it exactly.
    for p in pauses:
        before = sum(h['hold_s'] for h in holds if h['at_audio_s'] < p['at_audio_s'] - 1e-6)
        own = p['hold_s']
        sp, ns = p.pop('_span'), p.pop('_next_start')
        p['times_in_edit'] = {'silence_from_s': round(sp[0] + before, 3), 'silence_to_s': round(sp[1] + before + own, 3),
                              'next_line_s': round(ns + before + own, 3) if ns is not None else None}
    # The length is reached by the narration, never by the silence added to it.
    tol0 = max(4, lock['target_length_s'] * lock.get('tolerance_export_pct', .025))
    win_lo = lock['target_length_s'] - tol0
    held_s = round(sum(h['hold_s'] for h in holds if h['kind'] == 'script'), 3)
    if dur + seam_s < win_lo <= total:
        error('The edit reaches the locked length only with the held silence: the narration ends '
              f'{win_lo - dur - seam_s:.1f} s short of the export window. The answer is the story (more substance in '
              'the parts to re-record, or an authorised length revision), never longer silences.',
              {'narration_s': dur, 'held_silence_s': held_s, 'export_window_from_s': round(win_lo, 2)})
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
    out_shots, start = [], 0.0
    hold_at = {int(h['index']): h['at_audio_s'] for h in pauses}
    for k, (s, (a, b)) in enumerate(zip(shots, ranges)):
        if k + 1 < len(shots):
            # The cut sits in the silence after the shot's last line: where its hold is, when it has one (the hold stays
            # on the shot before), else in the middle of the measured silence, else at Whisper's boundary.
            g = gmap.get(b) or {}
            split = (hold_at[b] if b in hold_at else
                     (g['span_s'][0] + g['span_s'][1]) / 2 if g.get('basis') == 'audio' and g.get('span_s') else
                     (times[b]['end_s'] + times[b + 1]['start_s']) / 2)
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
    tol = max(4, lock['target_length_s'] * lock.get('tolerance_export_pct', .025))
    edit_audio = None
    if holds:      # the CapCut project uses the narration with its holds: always written when there are any
        src, outp = folder / 'narration.wav', folder / 'narration-edit.wav'
        filt, labels, prev = [], [], 0.0
        # A decided fade works on the stretch of the voice's own quiet next to its splice: out at the end of the
        # stretch before it, in at the start of the stretch after it. Nothing else in the narration is touched.
        seg_fx = [[] for _ in range(len(holds) + 1)]
        bounds = [0.0] + [h['at_audio_s'] for h in holds]
        for j, h in enumerate(holds):
            fz = (h.get('transition') or {}).get('fades') or {}
            if fz.get('into'):
                seg_fx[j].append(f"afade=t=out:st={fz['into'][0] - bounds[j]:.3f}:d={fz['into'][1] - fz['into'][0]:.3f}")
            if fz.get('out_of'):
                seg_fx[j + 1].append(f"afade=t=in:st=0:d={fz['out_of'][1] - fz['out_of'][0]:.3f}")
        fx = lambda k: ''.join(',' + x for x in seg_fx[k])
        for j, h in enumerate(holds):
            filt.append(f"[0:a]atrim=start={prev:.3f}:end={h['at_audio_s']:.3f},asetpts=PTS-STARTPTS{fx(j)}[a{j}]")
            filt.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={h['hold_s']:.3f}[s{j}]")
            labels += [f'[a{j}]', f'[s{j}]']
            prev = h['at_audio_s']
        if prev < dur - 0.01:
            filt.append(f'[0:a]atrim=start={prev:.3f},asetpts=PTS-STARTPTS{fx(len(holds))}[tail]')
            labels.append('[tail]')
        filt.append(''.join(labels) + f'concat=n={len(labels)}:v=0:a=1[out]')
        run_cmd(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src),
                 '-filter_complex', ';'.join(filt), '-map', '[out]', '-ar', '44100', '-ac', '2',
                 '-c:a', 'pcm_s16le', str(outp)])
        edit_audio = {'file': str(outp), 'duration_s': probe(outp)['duration_s']}
        # The silences as they really are in the file the project will carry, read with the yardstick that decided
        # them: the voice's own gap plus what was added, at the place decided, and nothing added anywhere else.
        if abs(edit_audio['duration_s'] - total) > 0.05:
            error('narration-edit.wav is not the narration plus the decided holds: its length differs.',
                  {'expected_s': total, 'got_s': edit_audio['duration_s']})
        script_holds = [h for h in holds if h['kind'] == 'script']
        if script_holds:
            av = av or _av()
            centres, shift = {}, 0.0
            for h in holds:
                if h['kind'] == 'script':
                    centres[h['after_line']] = h['at_audio_s'] + shift + h['hold_s'] / 2
                shift += h['hold_s']
            runs = av.silences_at(outp, [centres[h['after_line']] for h in script_holds], search_s=0.1)
            wrong = []
            for h, run in zip(script_holds, runs):
                got = round(run[1] - run[0], 3) if run else None
                expect = h['expected_gap_s'] if h.get('gap_basis') == 'audio' else h['hold_s']
                h['resulting_gap_s'] = got
                if got is None or abs(got - expect) > HOLD_VERIFY_TOL_S:
                    wrong.append({'line': h['after_line'], 'expected_s': expect, 'measured_s': got})
            if wrong:
                error('The edit\'s narration does not carry the silences that were decided (measured in '
                      'narration-edit.wav): nothing was written to the shot plan or the edit plan.', wrong)
        # The voice itself is the recording, sample for sample, everywhere outside the added silences and the decided
        # fades: no word, release or breath was moved, cut, faded or resampled.
        av = av or _av()
        excluded = [w for h in holds for w in ((h.get('transition') or {}).get('fades') or {}).values() if w]
        changed = av.voice_unchanged(src, outp, [(h['at_audio_s'], h['hold_s']) for h in holds], excluded)
        if changed:
            error('narration-edit.wav differs from the recorded narration outside its added silences and decided '
                  'fades: nothing was written to the shot plan or the edit plan.', changed)
    plan['timed_to'] = {'narration': str(folder / 'narration.wav'), 'edit_duration_s': total, 'retimed_at': now()}
    write_json(plan_path, plan)
    # The one audio file the CapCut project must carry, at 0 s, at speed 1, untrimmed (timeline-check), and that the
    # export must contain (export-check): its fingerprint ties the cut to this exact approved narration.
    nf = Path(edit_audio['file']) if edit_audio else folder / 'narration.wav'
    narration_for_edit = {'file': str(nf), 'sha256': file_sha256(nf), 'duration_s': probe(nf)['duration_s'],
                          'parts': [p.get('id') for p in lt.get('parts') or []],
                          'part_fingerprints': {str(p.get('id')): p.get('fingerprint') for p in lt.get('parts') or []}}
    edit_plan = {'video': n, 'narration_file': str(folder / 'narration.wav'), 'narration_duration_s': dur,
                 'holds': holds, 'edit_duration_s': total, 'edit_narration': edit_audio,
                 'narration_for_edit': narration_for_edit,
                 'export_window_s': [round(lock['target_length_s'] - tol, 2), round(lock['target_length_s'] + tol, 2)],
                 'within_export_window': abs(total - lock['target_length_s']) <= tol,
                 # What the editor carries out (09): the locked treatment's picture, sound and pace, and each shot's
                 # beat direction below; the revision stamps which direction this edit plan follows.
                 'direction': {'treatment': dlock.get('treatment'), 'production_rev': dlock.get('production_rev', 1),
                               **{k: chosen_treatment_of(read_json(vd / 'direction.json')).get(k) for k in
                                  ('visual_language', 'sound', 'audiovisual_relationship', 'structure_and_pace')}},
                 'shot_structure_sha256': shot_structure_sha(shots), 'script_sha256': script_hash(lines),
                 # Every decided pause and what it became (added, or nothing: the voice's own gap), and the decisions
                 # this plan was timed from (timeline-check: a later decision means a new retime).
                 'pauses': pauses, 'hold_decisions_sha256': hold_decisions_sha(rd, n), 'voice_gaps': hf['voice_gaps'],
                 'beats': [{'id': b, 'start_s': round(a, 2), 'end_s': round(z, 2), **beat_dir.get(b, {})}
                           for b, (a, z) in beat_spans.items()],
                 'shots': out_shots, 'notes': notes, 'made_at': now()}
    write_json(rd / '70-edit' / f'video-{n:02d}' / 'edit-plan.json', edit_plan)
    emit({'ok': True, 'edit_plan': str(rd / '70-edit' / f'video-{n:02d}' / 'edit-plan.json'),
          'shot_plan': str(plan_path), 'shots': len(out_shots), 'edit_duration_s': total, 'holds': holds,
          'pauses': pauses, 'within_export_window': edit_plan['within_export_window'], 'edit_narration': edit_audio,
          'narration_for_edit': narration_for_edit, 'notes': notes,
          'next': 'Put narration_for_edit.file in the CapCut project at 0 s, speed 1, untrimmed; name the project in '
                  'timeline.json (capcut_draft) so timeline-check reads the narration from CapCut itself. With the '
                  'stills made, look at each held silence with its shot (holds --preview) and confirm or change it '
                  '(hold-decide --stage picture); a changed decision is retimed before the project is rebuilt.'})


def _av():
    """The audiovisual measurements (av_tools.py, next to this file): loaded only when a command needs them, so the
    rest of the pipeline never waits on numpy/OpenCV/librosa."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import av_tools
    return av_tools


INSPECT_MAX_FRAMES = 400


def inspect_dir(rd, label, a, b, rate):
    tag = 'native' if rate == 'native' else f'{float(rate):g}fps'
    return rd / '20-analysis' / 'inspect' / label / f'{a:.2f}-{b:.2f}@{tag}'


def cmd_inspect_window(args):
    """A closer look at one brief stretch of a reference (--ref) or of any video (--file, e.g. an export): every
    frame (--native) or a higher rate, each at its own timestamp on the transcript's clock, with the words said
    there and one contact sheet. For what the run's samples cannot settle (an inspect_candidate, a fast cut, a
    possibly graphic moment, an uncertain continuity), never a whole video. --remove deletes that look's frames
    afterwards (disturbing material); its index.json stays as the record that the look was taken."""
    rd, st = run_folder(args)
    a, b = parse_clock(args.start), parse_clock(args.end)
    if a is None or b is None or b <= a:
        error('--from and --to must be times (mm:ss, h:mm:ss or seconds), --to after --from')
    row, tj = None, {}
    if args.ref:
        inv = read_json(rd / '00-inventory/references.json', required=True)
        row = next((x for x in inv.get('items') or [] if x.get('id') == args.ref.strip().upper()
                    and x.get('kind') == 'video'), None)
        if not row:
            error('No such reference video in this run', args.ref)
        src, label = Path(row['source_path']), row['id']
        tj = read_json(rd / '10-media' / label / 'transcript.json')
    elif args.file:
        src = Path(args.file).expanduser().resolve()
        if not src.is_file():
            error('File not found', str(src))
        row = probe(src)
        label = 'file-' + quick_fingerprint(src)[:12]
    else:
        error('Name a reference (--ref V###) or a video file (--file)')
    rate = 'native' if args.native else float(args.fps)
    out = inspect_dir(rd, label, a, b, rate)
    if args.remove:
        idx = read_json(out / 'index.json')
        if not idx:
            error('No such closer look to remove', str(out))
        gone = 0
        for f in list((out / 'frames').glob('*.jpg')) + ([out / 'sheet.jpg'] if (out / 'sheet.jpg').is_file() else []):
            f.unlink()
            gone += 1
        idx['frames_removed_at'] = now()
        write_json(out / 'index.json', idx)
        emit({'ok': True, 'removed_files': gone, 'record_kept': str(out / 'index.json')})
        return
    duration = row.get('duration_s')
    if duration and a >= float(duration):
        error('The window starts after the video ends', {'duration_s': duration})
    if rate != 'native' and not 0 < rate <= 60:
        error('--fps must be between 0 and 60')
    per_s = float(row.get('fps') or 30) if rate == 'native' else rate
    if (b - a) * per_s > INSPECT_MAX_FRAMES:
        error(f'A closer look is for a brief stretch: this one would be about {int((b - a) * per_s)} frames (at most '
              f'{INSPECT_MAX_FRAMES}). Narrow it or lower --fps; the video as a whole stays at the run\'s rate.')
    av = _av()
    frames, origin = av.sample_frames(src, out / 'frames', fps=1.0 if rate == 'native' else rate, width=args.width,
                                      start_s=a, end_s=b, native=rate == 'native')
    words = [w for w in transcript_words(tj) if a <= w['start_s'] <= b] if tj else []
    shown = 'every frame' if rate == 'native' else f'{rate:g} fps'
    sheet = av.window_sheet([(f['t_s'], out / 'frames' / f['file']) for f in frames], out / 'sheet.jpg',
                            f'{label}  {_mmss(a)}-{_mmss(b)}  {shown}: {len(frames)} frames', words)
    before = read_json(out / 'index.json')
    earlier = (before.get('earlier') or []) + ([{'why': before.get('why'), 'made_at': before.get('made_at')}]
                                               if before.get('made_at') else [])
    write_json(out / 'index.json', {'label': label, 'source': str(src), 'from_s': a, 'to_s': b, 'rate': rate,
                                    'width': args.width, 'why': args.why, 'earlier': earlier,
                                    'clock_origin_s': origin, 'frames': frames,
                                    'words': ' '.join(str(w.get('text') or '').strip() for w in words),
                                    'sheet': sheet, 'made_at': now()})
    emit({'ok': True, 'window': str(out), 'frames': len(frames), 'sheet': sheet,
          'first_s': frames[0]['t_s'] if frames else None, 'last_s': frames[-1]['t_s'] if frames else None,
          'note': 'Look at the sheet (and the frames themselves where a detail matters). After a look at disturbing '
                  'material, remove the frames (--remove): the record stays.'})


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
            frames = [(f['t_s'] if f.get('t_s') is not None else f['approx_s'], media / 'sampled-frames' / f['file'])
                      for f in fi.get('frames') or []]
            if not frames:
                error('No sampled frames for this reference: run prepare first.', vid)
            tj = read_json(media / 'transcript.json')
            words = transcript_words(tj)
            target = ref_av_path(rd, vid)
            ffps = float(fi.get('fps') or run_analysis_fps(st))
            fsampler = str(fi.get('sampler') or LEGACY_SAMPLER)
            if abs(ffps - run_analysis_fps(st)) > 1e-9:
                results.setdefault('_notes', []).append(f'{vid}: its frames were sampled at {ffps:g} fps, the run '
                                                        f'analyses at {run_analysis_fps(st):g} fps: compare its cut '
                                                        'counts only with videos sampled at the same rate')
            sig = {'fingerprint': row.get('fingerprint'), 'frames': len(frames), 'fps': ffps, 'sampler': fsampler,
                   'words': len(words), 'method': av.METHOD_VERSION, 'sheets': not args.no_sheets}
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
                                  segments=_segments_of(tj), fps=ffps, sampler=fsampler)
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
            frames = av.extract_frames(f, Path(tmp) / 'frames', fps=run_analysis_fps(st))
            wav = None
            if meta.get('has_audio'):
                try:
                    wav = av.extract_audio(f, Path(tmp) / 'audio.wav')
                except RuntimeError:
                    wav = None
            prof = av.profile(f'video-{n:02d}', meta['duration_s'], frames, wav, words,
                              sheets_dir=None if args.no_sheets else target.with_suffix(''),
                              segments=_segments_of(tj), fps=run_analysis_fps(st), sampler=av.SAMPLER)
            # every shot of our own export once, for the final reviewer: a short shot between two watch-sheet frames
            # is seen there (made now, while the export's frames exist)
            prof['shot_sheets'] = ([] if args.no_sheets or not prof.get('shots') else
                                   render_shot_sheets(av, frames, prof['shots'], target.with_suffix('') / 'shots',
                                                      f'video-{n:02d}')[1])
        for s in prof['shots']:
            s.pop('keyframe', None)            # the export's frames were temporary; the sheets keep the pictures
        lock = read_json(video_dir(rd, n) / 'length-lock.json')
        prof['references'] = {v: read_json(ref_av_path(rd, v)).get('summary') for v in lock.get('reference_ids') or []
                              if ref_av_path(rd, v).is_file()}
        prof.update({'source': {'file': str(f), 'fingerprint': fp}, 'made_at': now()})
        write_json(target, prof)
        results[f'video-{n:02d}'] = {'file': str(target), 'sheets': len(prof['sheets']),
                                     'shot_sheets': len(prof.get('shot_sheets') or []), 'summary': prof['summary'],
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
               'wounds, bodies or injuries shown, or described in their physical detail; saying plainly that people '
               'were hurt or died is fine); no extreme distress; no swearing; nothing indecent; every person an adult.')


def house_rules(rd, video):
    """HOUSE_RULES, plus the themes this video's reference material was cut for (its content reviews)."""
    themes = excluded_themes(rd, video)
    out = HOUSE_RULES
    gone = [th for th in themes if th.get('label') != 'restricted_theme']
    shown = [th for th in themes if th.get('label') == 'restricted_theme']
    if gone:
        out += (' Parts of the reference material were left out on purpose; nothing in this video may bring them back, '
                'in other words or other pictures either: ' +
                '; '.join(f'{th["what"]} ({"a content-safety exclusion" if th["kind"] == "safety" else "a creative exclusion"})'
                          for th in gone) + '.')
    if shown:
        out += (' These may be told, but never shown or described in their graphic form: ' +
                '; '.join(f'{th["what"]} (never shown: {", ".join(th["avoid"])})' for th in shown) + '.')
    return out

SCRIPT_BRIEF = """# Cold read: {TITLE}

You are a first-time viewer, not an editor. Below is the complete narration of a long-form YouTube video
(about {MINUTES} minutes, narrated over illustrated stills). You get only the title and the words, on purpose:
no plan, no rationale. Read nothing else and do not change any file except the one you are asked to write.

Read it all the way through as someone who clicked the title and is listening. Be honest, specific and fair:
say what works as plainly as what does not. Refer to line ids.

Words in [square brackets] are delivery directions the voice receives but never says. A line followed by
"(silence: ...)" is followed by about that much silence in all, the voice's own short gap included, with what you
would see and hear while it lasts. The lengths are proposals, not yet fitted to the recorded voice. Judge both as
part of what you would hear: does each direction help, or push the narration into theatre; would you want each
silence, or would you be waiting for the voice to go on?

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
9. The delivery directions and the silences: where they help, where they are theatre or filler. For each silence:
   does it feel needed, or does it delay the next thing you want to know? Would you become impatient? Does it help
   the joke, the reveal or the feeling, or would the line land as well with the voice going straight on? Does it make
   the narrator sound unnaturally slow? Would a first-time viewer understand why it is there? A silence you would
   cut or shorten is a finding.

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
like a film. Then open its shot sheets: one frame of every shot in order, so a short shot that falls between two
watch-sheet frames is seen too. Below them are a few measurements per minute (facts, not verdicts). Read nothing else and change no file
except the one you are asked to write.

Judge it against what each part was meant to feel like (listed below), not against a generic checklist:
1. Did each part deliver what it set out to do?
2. Where does it get visually repetitive, or the pictures stop adding anything to the words (a slideshow)?
3. Where do picture and words not connect, or contradict each other?
4. Where does it feel like a lecture or a dry documentary instead of a story? Where does it drag or rush?
5. Continuity breaks: a person, place, object, light or time of day that jumps without reason.
6. The first minute and the ending.
7. Anything on screen or in the words that breaks the house rules, however it is carried: said outright,
   paraphrased or implied, or only shown in a picture.
8. The held silences listed below (the voice stops; the picture stays). For each, from the words around it, the
   shot on screen and its length: would it feel like a moment worth the wait, or dead air? Would you become
   impatient there? Does it help the line before it land, or delay what comes next? You cannot hear it or see motion
   inside a shot, so say what you can judge and what you cannot. A silence you would cut or shorten is a finding.

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
        text = _fill(SCRIPT_BRIEF, TITLE=title, MINUTES=minutes, HOUSE_RULES=house_rules(rd, n), OUT=out_path)
        # What the reader is shown is the silence a viewer would hear: the whole of it, the voice's own gap included
        # (an older added-on-top value is shown with that gap added), with what is on screen and in the sound. No
        # reference pause length is shown: a length is set by its own moment, not matched to another film's.
        pp = {p['line']: p for p in script_pause_plan(lines)[0]}
        gap = (voice_measurement(rd, n) or {}).get('natural_gap_s') or DEFAULT_NATURAL_GAP_S
        whole = {lid: (p['seconds'] if p['form'] == 'total' or p['via'] == 'tag' else p['seconds'] + gap)
                 for lid, p in pp.items()}
        text += (f'Silences in this script: {len(pp)}, about {sum(whole.values()):.0f} s in all. A narrator\'s own '
                 f'gap between two lines is about {gap:.1f} s; a silence longer than that is a held moment.\n\n')
        for lid, t in snapshot.items():
            text += f'{lid} {t}\n'
            if lid in pp:
                p = pp[lid]
                how = 'the voice pauses' if p['via'] == 'tag' else 'the voice stops, the picture stays'
                text += (f'      (silence: about {whole[lid]:.1f} s in all, {how}. On screen: '
                         f'{p.get("picture") or "not described"}. Sound: {p.get("sound") or "not described"}.)\n')
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
                     HOUSE_RULES=house_rules(rd, n), OUT=out_path)
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
        text = _fill(FINAL_BRIEF, TITLE=title, HOUSE_RULES=house_rules(rd, n), OUT=out_path)
        text += '\n## What each part was meant to feel like\n'
        for b in beats:
            a_s, b_s = spans.get(str(b.get('id')), (b.get('start_s'), b.get('end_s')))
            text += f'- {_mmss(a_s)}-{_mmss(b_s)}: {b.get("experience") or b.get("narrative_job")} (pace: {b.get("pace") or "-"})\n'
        # The silences as they are in this cut (the edit plan the project was built from): where, how long in all,
        # and the words on each side. Not the director's reasons: the reviewer judges them fresh.
        script_lines = read_json(vd / 'script.json').get('lines') or []
        line_text = {str(r.get('id') or f'L{i + 1:03d}'): strip_tags(r.get('text') or '') for i, r in enumerate(script_lines)}
        order_ids = list(line_text)
        shift, held_rows = 0.0, []
        for h in sorted(plan.get('holds') or [], key=lambda x: x['at_audio_s']):
            if h.get('kind') == 'script':
                lid = str(h.get('after_line'))
                k = order_ids.index(lid) if lid in order_ids else -1
                after = line_text[order_ids[k + 1]] if 0 <= k < len(order_ids) - 1 else '(the end)'
                bed = (h.get('transition') or {}).get('bed')
                held_rows.append(f'- {_mmss(h["at_audio_s"] + shift)}: about '
                                 f'{h.get("resulting_gap_s") or h.get("expected_gap_s") or h["hold_s"]:.1f} s with no '
                                 f'voice, after "...{line_text.get(lid, "")[-70:]}", before "{after[:60]}..."'
                                 + (f' (the music {bed})' if bed and bed != 'none' else ' (no music)' if bed else ''))
            shift += float(h.get('hold_s') or 0)
        text += ('\n## Held silences in this cut\n' + ('\n'.join(held_rows) if held_rows else
                 '- none: every pause is the voice\'s own') + '\n')
        text += '\n## Watch sheets, in order\n' + '\n'.join(f'- {p}' for p in prof.get('sheets') or []) + '\n'
        if prof.get('shot_sheets'):
            text += ('\n## Shot sheets: every shot once, in order\n' +
                     '\n'.join(f'- {p}' for p in prof['shot_sheets']) + '\n')
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
    # The export carries the approved narration, whole, at its own speed: the edit plan's narration file found in the
    # export's sound, window by window along the film (a speed change drifts, a cut or an insert jumps, a missing
    # stretch is not found), and the level of everything else under the voice.
    warnings, narration_match = [], None
    plan = read_json(rd / '70-edit' / f'video-{int(video):02d}' / 'edit-plan.json')
    nfe = plan.get('narration_for_edit') or {}
    nf = _run_file(rd, nfe['file']) if nfe.get('file') else None
    if nf and meta['has_audio']:
        if not nf.is_file():
            issues.append('export_narration_file_missing')
        else:
            try:
                av = _av()
                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    m = av.narration_in_mix(av.extract_audio(video_file, Path(tmp) / 'mix.wav'),
                                            av.extract_audio(nf, Path(tmp) / 'narration.wav'))
                narration_match = m
                for w in m['weak_windows']:
                    issues.append(f'export_narration_not_found_near_{_mmss(w)}')
                if m['lag_spread_s'] is not None and m['lag_spread_s'] > 0.25:
                    issues.append(f'export_narration_timing_drifts_{m["lag_spread_s"]:g}s')
                if m['median_lag_s'] is not None and abs(m['median_lag_s']) > 0.25:
                    issues.append(f'export_narration_offset_{m["median_lag_s"]:g}s')
                if m.get('bed_level_rel_speech_db') is not None and m['bed_level_rel_speech_db'] > -8:
                    warnings.append(f'the sound under the voice sits {m["bed_level_rel_speech_db"]:g} dB below the speech: '
                                    'music may mask words; listen on small speakers')
            except (RuntimeError, ValueError, OSError, ImportError) as exc:
                issues.append('export_narration_not_checked:' + f'{type(exc).__name__}: {str(exc)[:120]}')
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
    return {'ready': not issues, 'issues': issues, 'warnings': warnings, 'file': str(video_file), 'metadata': meta,
            'target_s': target, 'difference_s': round(meta['duration_s'] - target, 2), 'diagnostic_flags': diag,
            'narration_in_export': {k: v for k, v in (narration_match or {}).items() if k != 'windows'} or None}


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
    looks = read_json(picture_looks_path(rd, n)).get('looks') or {}
    shown = {_pkey(_run_file(rd, c.get('asset_path'))) for c in
             read_json(rd / '70-edit' / f'video-{n:02d}' / 'timeline.json').get('visual_segments') or []
             if isinstance(c, dict) and c.get('asset_path')}
    content = {'pictures_shown': len(shown), 'pictures_looked_at_clean': sum(1 for k in shown if (looks.get(k) or {}).get('result') == 'clean'),
               'excluded_reference_themes_in_force': len(excluded_themes(rd, n)),
               'what_was_seen': 'every picture the timeline shows was looked at whole (content-looks); the export '
                                'itself only through its watch sheets (a frame every 5 s) by the final reviewer, so '
                                'drawn overlays and captions are checked by the timeline and caption checks, not '
                                'frame by frame'}
    emit({'ready': not issues, 'release_status': 'ready' if not issues else 'blocked', 'issues': issues,
          'warnings': warnings, 'export': {k: exp[k] for k in ('file', 'metadata', 'target_s', 'difference_s')},
          'final_review_rounds': fin['rounds'], 'content': content,
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
        hf = hold_facts(rd, i)
        videos[str(i)] = {'target_s': read_json(vd/'length-lock.json').get('target_length_s'),
                          'plan_ready': plan['ready'], 'audio_ready': audio['ready'],
                          'holds': {'planned_or_decided': len(hf['holds']), 'provisional': hf['undecided'],
                                    'decided_after_narration': hf['decided_narration'],
                                    'decided_with_picture': hf['decided_picture'], 'added_s': hf['added_s']},
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
    p = sub.add_parser('doctor'); p.add_argument('--whisper', action='store_true',
                                                 help='load Whisper medium on the GPU and run it once')
    p.add_argument('--file', help='with --whisper: also transcribe this file (nothing is written to a run)')
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser('init'); p.add_argument('--references', required=True); p.add_argument('--workspace')
    p.add_argument('--slug', default='story')
    p.add_argument('--fps', type=float, default=ANALYSIS_FPS, help='Reference analysis frames per second (2 by default; '
                   'kept by the run)')
    p.add_argument('--min-longform', type=int, default=DEFAULT_MIN_LONGFORM); p.set_defaults(func=cmd_init)
    p = sub.add_parser('clone'); p.add_argument('--from-run', required=True); p.add_argument('--workspace'); p.add_argument('--slug', default='clone'); p.set_defaults(func=cmd_clone)
    p = sub.add_parser('scan'); p.add_argument('--run', required=True); p.set_defaults(func=cmd_scan)
    p = sub.add_parser('prepare'); p.add_argument('--run', required=True); p.add_argument('--ids')
    p.add_argument('--fps', type=float); p.add_argument('--width', type=int, default=960)
    # Whisper medium on the GPU: the CUDA 12 runtime is installed for this interpreter (cuda_runtime_setup finds it).
    add_whisper_args(p); p.add_argument('--full-fps', action='store_true')
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
    add_whisper_args(p); p.set_defaults(func=cmd_voice_candidates)
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
    add_whisper_args(p); p.set_defaults(func=cmd_voice_probe)
    p = sub.add_parser('narration-trial', help='A controlled calibration trial: a few passages under a few voice '
                       'set-ups, each question changing one thing; priced first, recorded only with --execute')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--plan', required=True, help='The trial plan JSON: passages, variants, runs, questions, budget')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--takes', default='', help="Record only these runs this time (e.g. P2-A), in the plan's order; "
                   'the rest wait for a later call')
    p.add_argument('--check-balance', action='store_true', help='Dry run with the live balance and the model\'s '
                   'credits per character (free calls)')
    p.add_argument('--credit-safety-factor', type=float, default=1.15)
    p.add_argument('--assume-cost-ratio', type=float, default=None)
    p.add_argument('--keep-credits', type=int, default=0, help='Credits that must still be left afterwards')
    add_whisper_args(p); p.set_defaults(func=cmd_narration_trial)
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
    add_whisper_args(p); p.set_defaults(func=cmd_narration_measure)
    p = sub.add_parser('av-profile', help='Measured audiovisual evidence and watch sheets: references or this export')
    p.add_argument('--run', required=True); p.add_argument('--refs', default='')
    p.add_argument('--video', type=int); p.add_argument('--file', default='')
    p.add_argument('--transcript', default='', help='An existing Whisper transcript.json of the export (else Whisper '
                   'medium transcribes it, cached)')
    p.add_argument('--no-sheets', action='store_true'); p.add_argument('--force', action='store_true')
    add_whisper_args(p); p.set_defaults(func=cmd_av_profile)
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
    p = sub.add_parser('holds', help='Every planned pause next to the gap the recorded voice really left there; '
                       '--preview Lnnn --totals a,b renders listening (and, with stills, watching) previews')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--preview', default='', help='A line whose held silence to preview (Lnnn)')
    p.add_argument('--totals', default='', help='Whole silences to preview, in seconds (the voice\'s own gap is always '
                   'one of the previews): 1.2,2.0')
    p.add_argument('--into', default='clean', help='Transitions into the silence to compare: clean,fade')
    p.add_argument('--out-of', dest='out_of', default='clean', help='Transitions out of the silence to compare: clean,fade')
    p.set_defaults(func=cmd_holds)
    p = sub.add_parser('hold-decide', help='Decide one held silence on evidence: the whole silence after a line, or none')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--line', required=True); p.add_argument('--stage', required=True, choices=HOLD_STAGES)
    p.add_argument('--total', type=float, default=None, help='The WHOLE silence after the line, in seconds, the '
                   'voice\'s own gap included (the edit adds only the difference)')
    p.add_argument('--no-hold', action='store_true', help='No added silence: the voice\'s own gap stays as recorded')
    p.add_argument('--reason', required=True, help='Why this length serves this moment')
    p.add_argument('--listened', default='', help='The user\'s own words, when they listened to the previews')
    p.add_argument('--into', default='clean', choices=TRANSITION_INTO, help='Into the silence: clean (the voice as '
                   'recorded, the default) or fade (the voice\'s own room tone fades into the added silence; refused '
                   'where it would touch the voice or where that quiet is inaudible)')
    p.add_argument('--out-of', dest='out_of', default='clean', choices=TRANSITION_OUT, help='Out of the silence: clean '
                   '(the default) or fade (the room tone fades back in before the next line; same limits)')
    p.add_argument('--bed', default='', choices=('',) + BED_MOVES, help='What the music or ambience does around the '
                   'silence (required with --stage picture)')
    p.set_defaults(func=cmd_hold_decide)
    p = sub.add_parser('retime-shots', help='Time the shot plan to the real narration and its decided holds')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--render-narration', action='store_true', help='Kept for older notes: narration-edit.wav is '
                   'always written when the edit has holds (it is the audio the CapCut project uses)')
    p.add_argument('--no-seam-holds', action='store_true', help='Do not restore the voice\'s natural gap at the '
                   'joins between recorded parts')
    p.set_defaults(func=cmd_retime_shots)
    p = sub.add_parser('captions-choice', help='The user\'s captions choice, asked once at the start: on with a style, or off')
    p.add_argument('--run', required=True); p.add_argument('--captions', required=True, choices=('on', 'off'))
    p.add_argument('--style', default='', choices=('', 'luckiest-guy', 'montserrat-highlight'))
    p.add_argument('--change', default='', help='Why a choice already made changes (the user\'s say)')
    p.set_defaults(func=cmd_captions_choice)
    p = sub.add_parser('captions-plan', help='The captions\' words and times on the edit\'s timeline (70-edit/video-NN/captions.json)')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--box-color', default='', help='The word box\'s colour for this video (#RRGGBB)')
    p.add_argument('--box-color-why', default='', help='Why that colour (the video\'s palette, the pictures behind the line)')
    p.add_argument('--fps', type=int, default=30); p.set_defaults(func=cmd_captions_plan)
    p = sub.add_parser('captions-build', help='Write the planned captions into the CapCut project (CapCut closed) and read them back')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--draft', required=True); p.add_argument('--replace', action='store_true')
    p.set_defaults(func=cmd_captions_build)
    p = sub.add_parser('captions-check', help='Read the captions back from the CapCut project and check them against the plan')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--draft', required=True); p.set_defaults(func=cmd_captions_check)
    p = sub.add_parser('captions-preview', help='A few PNG frames of the planned captions (PIL, not CapCut\'s renderer)')
    p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--out', required=True); p.add_argument('--canvas', default='1920x1080')
    p.add_argument('--background', default=''); p.add_argument('--start', type=float, default=None)
    p.add_argument('--frames', type=int, default=8); p.set_defaults(func=cmd_captions_preview)
    p = sub.add_parser('timeline-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.set_defaults(func=cmd_timeline_check)
    p = sub.add_parser('export-check'); p.add_argument('--run', required=True); p.add_argument('--video', type=int, required=True)
    p.add_argument('--file', required=True); p.add_argument('--deep', action='store_true'); p.set_defaults(func=cmd_export_check)
    p = sub.add_parser('status'); p.add_argument('--run', required=True); p.set_defaults(func=cmd_status)
    p = sub.add_parser('content-review', help='The content record: a reference\'s review (--ref --file; --signals '
                       'for where to look), the look at every picture of an edit (--video --pictures --file), --status')
    p.add_argument('--run', required=True); p.add_argument('--ref'); p.add_argument('--file')
    p.add_argument('--signals', action='store_true'); p.add_argument('--status', action='store_true')
    p.add_argument('--shot-sheets', action='store_true', help='one frame of every shot, 36 to a sheet, for the review')
    p.add_argument('--archive', action='store_true', help='before a blind second review: move the current review and '
                   'its closer looks to content-archive (the source evidence stays)')
    p.add_argument('--video', type=int); p.add_argument('--pictures', action='store_true')
    p.set_defaults(func=cmd_content_review)
    p = sub.add_parser('inspect-window', help='A closer look at a brief stretch of a reference or video: a higher rate '
                       'or every frame, each at its own time, with the words and one contact sheet')
    p.add_argument('--run', required=True); p.add_argument('--ref'); p.add_argument('--file')
    p.add_argument('--from', dest='start', required=True); p.add_argument('--to', dest='end', required=True)
    p.add_argument('--fps', type=float, default=10.0); p.add_argument('--native', action='store_true')
    p.add_argument('--width', type=int, default=640); p.add_argument('--why', default='')
    p.add_argument('--remove', action='store_true', help='delete this look\'s frames after it was taken (the record stays)')
    p.set_defaults(func=cmd_inspect_window)
    args = ap.parse_args()
    if hasattr(args, 'device'):
        whisper_settings(args)
    try:
        args.func(args)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as exc:
        error(type(exc).__name__ + ': ' + str(exc)[:800])


if __name__ == '__main__':
    main()
