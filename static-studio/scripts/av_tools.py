#!/usr/bin/env python3
"""Static Studio's audiovisual measurements: what the narration, the picture and the sound do over time.

Gather only. Every value here is a measurement or a mechanical extraction with its method named; nothing is
scored, ranked, called good or bad, or decided. The agents read the numbers and the watch sheets and judge what
they mean. The same functions measure the references, this run's narration and the finished export, so the three
compare on one yardstick (as pace already does).

What is measured, and how:
- Picture, from the sampled frames (the run's analysis rate: 2 fps for a new run, the rate a run was analysed at for
  an older one; the export's frames are taken at the same rate; each frame at its own source timestamp on the
  transcript's clock, see sample_frames): the change between consecutive frames (mean
  absolute grey difference at 64x36) and their colour histograms. A single big change is a cut; a few hard,
  recolouring changes in a row whose changes add up to much more than the run's own change are a quick series of
  cuts; any other short run of changes (up to TRANSITION_MAX_S) that ends on a different picture is a transition
  (dissolve, wipe, fast move); a long run is motion inside a shot (a camera move, animation); a change that returns
  to the same picture is a flash (at a low rate: anything seen in one sample only, a burst or a short cutaway).
  Stretches the samples cannot settle (a flash, a cut series, a transition, a shot shorter than two samples) are
  listed as inspect_candidates for a closer look at a higher rate (static_core.py inspect-window).
  Shots get their length, the share of time they move, brightness and saturation, and whether the same picture
  came back earlier (difference hash and histogram).
- Narration, from the audio and Whisper's word times: pitch (pYIN) and loudness per word, pitch range and pitch
  movement from word to word, loudness contrast between words, speaking rate per window, where the pauses fall
  (after a sentence, a clause, or inside a phrase), and the level in the gaps between words relative to speech
  (a music or ambience bed under the voice reads high, silence reads very low).
- Windows of WINDOW_S seconds hold all of it side by side, with the words spoken, so a moment can be read as a
  whole: what was said, what was shown, how fast it cut, how the voice moved.
- Watch sheets: one image per minute, a frame every SHEET_STEP_S seconds with the words spoken under it, so an
  agent can read a video the way an editor scrubs a timeline.

Not measured: on-screen text (no OCR here), what the music is, sound effects as such, exact frame times (the
sampled frames sit on nominal slots), voice and music separately (pitch and loudness come from the mixed track),
and anything a viewer feels.

Needs numpy, opencv-python (cv2), librosa, soundfile and Pillow, all local; ffmpeg extracts audio and frames.
"""
from __future__ import annotations

import bisect
import json
import math
import re
import statistics
import subprocess
from pathlib import Path

METHOD_VERSION = 'av-profile-3'          # 3: picture thresholds in seconds (any sampling rate), quick cut series
WINDOW_S = 15.0
SHEET_STEP_S = 5.0
SHEET_COLS, SHEET_ROWS = 4, 3            # 12 tiles: one sheet = 60 s
TILE_W, TILE_H, CAPTION_H = 320, 180, 82
GREY_W, GREY_H = 64, 36
CUT_DIFF = 8.0              # mean absolute grey difference (0-255) of two consecutive sampled frames: a hard change
MOTION_DIFF = 0.6           # above the still-frame noise floor (an unchanged still measures 0-0.1 on the references),
MOTION_STEP_S = 0.2         # between frames 0.2 s apart (tuned at 5 fps). Frames further apart change more for the
MOTION_SCALE_EXP = 0.75     # same motion, so the threshold grows with the interval: x (interval / 0.2 s) ** 0.75, 2.0
                            # at 1 fps. Calibrated 2026-11-20 on 3,770 one-second intervals of seven moving references:
                            # 2.0 agreed with their 5 fps reading 81 % of the time and gave the same moving share (58 %
                            # vs 56 %); 0.6 unchanged read 92 %, 3.0 (fully linear) 40 %. Half-second spacing (2 fps,
                            # bracketed by frames 0.4 and 0.6 s apart on the same references): the formula's 1.01 and
                            # 1.37 agreed 86 % and 86 % (best thresholds there: 1.2 at 87 %, 1.4 at 86 %); 1.19 at 0.5 s.
TRANSITION_MAX_S = 1.6      # a run of changes lasting up to this long that lands on another picture: a transition
                            # (8 frame pairs at 5 fps, 2 at 1 fps: the same 1.6 s at any sampling rate)
CUT_SERIES_PATH = 1.4       # a run whose every pair is a hard, recolouring change, and whose changes add up to this many
                            # times the run's own change, is a quick series of cuts (a dissolve's add up to about 1)
HIST_CUT = 0.3              # inside long motion, a big change counts as a cut only if the colours change this much too
DUP_BITS = 6                # difference-hash distance (of 64 bits) for "the same picture again"
DUP_HIST = 0.2
DUP_MIN_GAP_S = 10.0
F0_MIN, F0_MAX = 65.0, 500.0
SR = 16000
HOP = 512
FRAME = 2048
CHUNK_S = 60.0              # pYIN runs in chunks so memory stays small on a long video
GAP_MIN_S = 0.4             # gaps this long are where the level under the voice is read
GAP_TRIM_S = 0.1
PAUSE_MIN_S = 0.3           # the pipeline's pause threshold (pause_profile)


def transition_pairs(step_s):
    """TRANSITION_MAX_S as frame pairs at this sampling interval."""
    return max(1, int(round(TRANSITION_MAX_S / step_s))) if step_s and step_s > 0 else 8


def motion_diff(step_s):
    """MOTION_DIFF for frames this far apart (MOTION_SCALE_EXP), never below the 5 fps value."""
    return round(MOTION_DIFF * max(1.0, (step_s or MOTION_STEP_S) / MOTION_STEP_S) ** MOTION_SCALE_EXP, 3)


def thresholds(fps=None):
    out = {'window_s': WINDOW_S, 'cut_grey_diff': CUT_DIFF, 'motion_grey_diff_per_0_2s': MOTION_DIFF,
           'transition_max_s': TRANSITION_MAX_S, 'cut_series_path': CUT_SERIES_PATH, 'hist_cut_inside_motion': HIST_CUT,
           'same_picture_hash_bits': DUP_BITS, 'pitch_tracker': f'librosa.pyin {F0_MIN:g}-{F0_MAX:g} Hz',
           'pause_s': PAUSE_MIN_S, 'gap_level_min_gap_s': GAP_MIN_S}
    if fps:
        out.update({'sampled_fps': fps, 'transition_max_frame_pairs': transition_pairs(1.0 / fps),
                    'motion_grey_diff_per_frame_pair': motion_diff(1.0 / fps)})
    return out


def unknowns(fps=None, sampler=None):
    rate = f'{fps:g} fps' if fps else 'the analysis rate'
    tol = f'+-{0.5 / fps:g} s' if fps else 'half a sample interval'
    out = ['on-screen text (no OCR in this setup)',
           'voice and music are not separated: pitch and loudness come from the mixed track, so a loud bed can '
           'disturb them; compare loudness contrast only between tracks with a similar level under the voice '
           '(gap_level_rel_speech_db): a bed flattens it, a dry voice reads higher',
           (f'frames are samples ({rate}), each at its own exact timestamp on the transcript\'s clock; what happens '
            'between two samples is unseen, so a cut is known only to within one sample interval'
            if sampler == SAMPLER else
            f'frame times are nominal sample slots ({rate}: each frame shows the picture within {tol} of its slot), '
            'not exact cut frames'),
           'what a viewer feels, and whether the video kept its audience (no retention data)']
    if fps and fps < 10:
        out.append(f'at {rate} a shot shorter than about two samples ({2 / fps:g} s) can merge with its neighbours, a '
                   'flash shorter than a sample interval is rarely seen, and a "flash" is any picture seen in one '
                   'sample only; compare cut counts only with videos measured at the same rate; inspect_candidates '
                   'lists the stretches the samples cannot settle (inspect-window looks closer)')
    return out


def _np_cv():
    try:
        import numpy as np
        import cv2
    except ImportError as exc:
        raise RuntimeError(f'picture analysis needs numpy and opencv-python ({exc})') from exc
    return np, cv2


def _audio_deps():
    try:
        import numpy as np
        import librosa
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError(f'narration analysis needs numpy, librosa and soundfile ({exc})') from exc
    return np, librosa, sf


def _pct(vals, q):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    pos = (len(vals) - 1) * q
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def _r(x, nd=2):
    return None if x is None else round(float(x), nd)


def _dist(vals, nd=2):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {'p10': _r(_pct(vals, .1), nd), 'median': _r(_pct(vals, .5), nd), 'p90': _r(_pct(vals, .9), nd)}


# ---------------------------------------------------------------- extraction

def extract_audio(src, out_wav):
    """Mono 16 kHz PCM of a video or audio file. Raises RuntimeError when the file has no audio stream."""
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(src), '-vn',
                        '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', str(out_wav)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode or not out_wav.is_file() or out_wav.stat().st_size < 1024:
        raise RuntimeError('no audio extracted: ' + (p.stderr or '')[-300:])
    return out_wav


def concat_audio(files, out_wav):
    """Several audio files joined into one mono 16 kHz PCM file (the parts of a narration)."""
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y']
    for f in files:
        cmd += ['-i', str(f)]
    cmd += ['-filter_complex', ''.join(f'[{i}:a]' for i in range(len(files))) + f'concat=n={len(files)}:v=0:a=1[a]',
            '-map', '[a]', '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', str(out_wav)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise RuntimeError('audio join failed: ' + (p.stderr or '')[-300:])
    return out_wav


SAMPLER = 'pts-v1'          # each frame picked by its real time and kept with its own timestamp (older: nominal slots)
_SHOWINFO = re.compile(r'\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:(-?[\d.]+)')


def clock_origin(src):
    """The source time a transcript of this file counts from: its audio stream's start (Whisper decodes the audio
    from its first sample), else its video stream's. A frame's source timestamp minus this is on the transcript's
    clock, the clock of every word time and speech segment."""
    try:
        p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,start_time', '-of', 'json',
                            str(src)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        streams = json.loads(p.stdout or '{}').get('streams') or []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 0.0

    def start(kind):
        for s in streams:
            if s.get('codec_type') == kind:
                try:
                    return float(s.get('start_time'))
                except (TypeError, ValueError):
                    return None
        return None
    a, v = start('audio'), start('video')
    return a if a is not None else (v if v is not None else 0.0)


def sample_frames(src, out_dir, fps=2.0, width=960, start_s=None, end_s=None, native=False):
    """Frames of a video by their real timestamps: the first frame of each 1/fps slot of source time (or, with
    native, every frame), optionally only from start_s to end_s (transcript clock). Nothing is inferred from frame
    numbers: each frame keeps its own timestamp, so a variable frame rate, a start offset or a dropped frame never
    shifts the frames after it. Returns (frames, origin): frames [{'file', 't_s' (transcript clock), 'pts_s'
    (source), 'slot_s'}], origin as clock_origin."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('*.jpg'):
        old.unlink()
    origin = clock_origin(src)
    conds = []
    if start_s is not None:
        conds.append(f'gte(t\\,{start_s + origin:.6f})')
    if end_s is not None:
        conds.append(f'lte(t\\,{end_s + origin:.6f})')
    if not native:
        conds.append(f'(isnan(prev_selected_t)+gt(floor(t*{fps:g})\\,floor(prev_selected_t*{fps:g})))')
    cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-nostats', '-y', '-loglevel', 'info', '-copyts']
    if start_s is not None:
        cmd += ['-ss', f'{max(0.0, start_s + origin - 2.0):.3f}']
    cmd += ['-i', str(src), '-vf', f"select='{'*'.join(conds) or '1'}',scale={width}:-2,showinfo", '-fps_mode', 'vfr',
            '-q:v', '5', str(out_dir / '%07d.jpg')]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise RuntimeError('frame extraction failed: ' + (p.stderr or '')[-300:])
    times = [float(m.group(1)) for m in _SHOWINFO.finditer(p.stderr or '')]
    files = sorted(out_dir.glob('*.jpg'))
    if len(times) != len(files):
        raise RuntimeError(f'frame timestamps not read ({len(files)} frames, {len(times)} times): nothing is guessed')
    frames = [{'file': f.name, 't_s': round(pts - origin, 4), 'pts_s': round(pts, 4),
               'slot_s': None if native else round(math.floor(pts * fps + 1e-6) / fps - origin, 4)}
              for f, pts in zip(files, times)]
    return frames, origin


def extract_frames(src, out_dir, fps=2.0, width=960):
    """Frames of a video at the analysis rate, each at its own time on the transcript's clock: (time, path) pairs."""
    frames, _ = sample_frames(src, out_dir, fps=fps, width=width)
    return [(f['t_s'], Path(out_dir) / f['file']) for f in frames]


# ---------------------------------------------------------------- picture

def frame_features(frames):
    """Per sampled frame: a small grey copy, colour histogram, difference hash, brightness and saturation."""
    np, cv2 = _np_cv()
    feats = []
    for t, path in frames:
        im = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_4)
        if im is None or im.size == 0:
            im = cv2.imread(str(path))
        if im is None or im.size == 0:
            continue
        small = cv2.resize(im, (GREY_W, GREY_H), interpolation=cv2.INTER_AREA)
        grey = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        d9 = cv2.resize(grey, (9, 8), interpolation=cv2.INTER_AREA).astype('int16')
        bits = (d9[:, 1:] > d9[:, :-1]).flatten()
        dhash = 0
        for b in bits:
            dhash = (dhash << 1) | int(bool(b))
        feats.append({'t': float(t), 'path': str(path), 'grey': grey, 'hist': hist, 'dhash': dhash,
                      'luma': float(grey.mean()), 'sat': float(hsv[..., 1].mean())})
    return feats


def _grey_diff(np, a, b):
    return float(np.mean(np.abs(a.astype('float32') - b.astype('float32'))))


def segment_shots(feats):
    """Shots from consecutive frame changes. Returns (shots, pair_kind, pair_diff): pair k is the change from frame
    k-1 to frame k, kind one of still / motion / cut / transition / flash."""
    np, cv2 = _np_cv()
    n = len(feats)
    if not n:
        return [], [], []
    d, h = [0.0] * n, [0.0] * n
    for k in range(1, n):
        d[k] = _grey_diff(np, feats[k]['grey'], feats[k - 1]['grey'])
        h[k] = float(cv2.compareHist(feats[k - 1]['hist'], feats[k]['hist'], cv2.HISTCMP_BHATTACHARYYA))
    kind = ['still'] * n
    kind[0] = 'start'
    starts = [(0, 'start')]
    gaps = sorted(feats[j]['t'] - feats[j - 1]['t'] for j in range(1, n))
    step = gaps[len(gaps) // 2] if gaps else 1.0
    max_pairs = transition_pairs(step)
    moving = motion_diff(step)

    def cut_series(lo, hi, net):
        # every pair a hard change that recolours, and the changes add up to far more than the net change: a quick
        # series of cuts (each sample a different picture), not one transition (a dissolve's pairs add up to its net)
        return (hi > lo and all(d[j] > CUT_DIFF and h[j] > HIST_CUT for j in range(lo, hi + 1))
                and sum(d[lo:hi + 1]) >= CUT_SERIES_PATH * net)
    k = 1
    while k < n:
        if d[k] <= moving:
            k += 1
            continue
        a = k
        while k < n and d[k] > moving:
            k += 1
        b = k - 1                      # pairs a..b change; frame a-1 is before the run, frame b after it
        length = b - a + 1
        total = _grey_diff(np, feats[b]['grey'], feats[a - 1]['grey'])
        if length <= max_pairs:
            if total > CUT_DIFF:
                if length == 1:
                    kind[a] = 'cut'
                    starts.append((a, 'cut'))
                elif cut_series(a, b, total):
                    for j in range(a, b + 1):
                        kind[j] = 'cut'
                        starts.append((j, 'cut'))
                else:
                    for j in range(a, b + 1):
                        kind[j] = 'transition'
                    starts.append((a + length // 2, 'transition'))
            else:
                flash = length <= 2 and max(d[a:b + 1]) > CUT_DIFF
                for j in range(a, b + 1):
                    kind[j] = 'flash' if flash else 'motion'
        else:
            # A long run is movement inside a shot (camera moves, animation). Big changes inside it are grouped and
            # read as a whole: one that comes back to the same picture is a flash (a muzzle burst, a dip to white);
            # one that lands on a new picture with new colours is a cut (one pair) or a transition (several); one
            # that keeps the colours is a fast move.
            j = a
            while j <= b:
                if d[j] <= CUT_DIFF:
                    kind[j] = 'motion'
                    j += 1
                    continue
                s0 = j
                while j <= b and d[j] > CUT_DIFF:
                    j += 1
                s1 = j - 1
                moved = _grey_diff(np, feats[s1]['grey'], feats[s0 - 1]['grey'])
                recoloured = float(cv2.compareHist(feats[s0 - 1]['hist'], feats[s1]['hist'],
                                                   cv2.HISTCMP_BHATTACHARYYA)) > HIST_CUT
                if moved <= CUT_DIFF:
                    label = 'flash'
                elif not recoloured:
                    label = 'motion'
                elif s1 == s0:
                    label = 'cut'
                    starts.append((s0, 'cut'))
                elif cut_series(s0, s1, moved):
                    label = 'cut'
                    starts += [(q, 'cut') for q in range(s0, s1 + 1)]
                else:
                    label = 'transition'
                    starts.append((s0 + (s1 - s0 + 1) // 2, 'transition'))
                for q in range(s0, s1 + 1):
                    kind[q] = label
    shots = []
    for i, (s0, how) in enumerate(starts):
        s1 = starts[i + 1][0] if i + 1 < len(starts) else n
        if s1 <= s0:
            continue
        t0 = feats[s0]['t']
        t1 = feats[s1]['t'] if s1 < n else feats[-1]['t'] + step
        inner = kind[s0 + 1:s1]
        key = feats[(s0 + s1 - 1) // 2]
        idx = range(s0, s1)
        shots.append({'start_s': _r(t0), 'end_s': _r(t1), 'length_s': _r(t1 - t0), 'begins_with': how,
                      'motion_share': _r(sum(1 for x in inner if x == 'motion') / len(inner) if inner else 0.0, 3),
                      'luma': _r(statistics.mean(feats[j]['luma'] for j in idx), 1),
                      'saturation': _r(statistics.mean(feats[j]['sat'] for j in idx), 1),
                      'keyframe': key['path'], '_dhash': key['dhash'], '_hist': key['hist']})
    for i, s in enumerate(shots):
        s['shot'] = i + 1
        for j in range(i - 1, -1, -1):
            o = shots[j]
            if s['start_s'] - o['end_s'] < DUP_MIN_GAP_S:
                continue
            if (bin(s['_dhash'] ^ o['_dhash']).count('1') <= DUP_BITS
                    and cv2.compareHist(o['_hist'], s['_hist'], cv2.HISTCMP_BHATTACHARYYA) <= DUP_HIST):
                s['same_picture_as_shot'] = o['shot']
                break
    for s in shots:
        s.pop('_dhash', None)
        s.pop('_hist', None)
    return shots, kind, d


def inspect_candidates(feats, kinds, shots, limit=60):
    """Stretches the samples cannot settle, for a closer look at a higher rate (inspect-window): a flash (a picture
    seen in one sample only), a transition or a cut series (what happened between the samples), and a shot shorter
    than two samples. [{'from_s', 'to_s', 'why'}], merged where they touch, in time order."""
    if len(feats) < 2:
        return []
    gaps = sorted(feats[j]['t'] - feats[j - 1]['t'] for j in range(1, len(feats)))
    step = gaps[len(gaps) // 2]
    out = []
    for k in range(1, len(feats)):
        if kinds[k] in ('flash', 'transition'):
            out.append([feats[k - 1]['t'], feats[k]['t'], kinds[k]])
        elif kinds[k] == 'cut' and k + 1 < len(feats) and kinds[k + 1] == 'cut':
            out.append([feats[k - 1]['t'], feats[k + 1]['t'], 'cut series'])
    for s in shots:
        if s['length_s'] < 2 * step - 1e-6 and s['begins_with'] != 'start':
            out.append([max(0.0, s['start_s'] - step), s['end_s'], 'short shot'])
    out.sort()
    merged = []
    for a, b, why in out:
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1][1] = max(merged[-1][1], b)
            if why not in merged[-1][2]:
                merged[-1][2].append(why)
        else:
            merged.append([a, b, [why]])
    return [{'from_s': _r(a, 3), 'to_s': _r(b, 3), 'why': ', '.join(w)} for a, b, w in merged[:limit]]


# ---------------------------------------------------------------- narration

def _clean(word):
    return str(word or '').strip()


def audio_features(wav, words):
    """Pitch and loudness of the narration around Whisper's word times. Returns per-word rows and the frame
    arrays the windows read. Pitch is in semitones from this narrator's own median, so voices compare by how
    much they move, not by how high they are."""
    np, librosa, sf = _audio_deps()
    y, sr = sf.read(str(wav), dtype='float32', always_2d=False)
    if getattr(y, 'ndim', 1) > 1:
        y = y.mean(axis=1)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
        sr = SR
    if len(y) < FRAME:
        y = np.pad(y, (0, FRAME - len(y)))
    chunk = max(HOP, int(CHUNK_S * sr) // HOP * HOP)
    f0_parts, v_parts = [], []
    for start in range(0, len(y), chunk):
        seg = y[start:start + chunk]
        nfr = int(math.ceil(len(seg) / HOP))
        if len(seg) < FRAME:
            seg = np.pad(seg, (0, FRAME - len(seg)))
        f0, vflag, _ = librosa.pyin(seg, fmin=F0_MIN, fmax=F0_MAX, sr=sr, frame_length=FRAME, hop_length=HOP)
        f0_parts.append(f0[:nfr])
        v_parts.append(vflag[:nfr])
    f0 = np.concatenate(f0_parts)
    voiced = np.concatenate(v_parts) & np.isfinite(f0)
    rms = librosa.feature.rms(y=y, frame_length=FRAME, hop_length=HOP)[0]
    nfr = min(len(f0), len(rms))
    f0, voiced, rms = f0[:nfr], voiced[:nfr], rms[:nfr]
    db = 20 * np.log10(np.maximum(rms, 1e-6))

    def span(a, b):
        i0 = max(0, int(a * sr / HOP))
        i1 = min(nfr, max(i0 + 1, int(math.ceil(b * sr / HOP))))
        return i0, i1

    in_word = np.zeros(nfr, dtype=bool)
    rows = []
    for w in words:
        i0, i1 = span(w['start_s'], w['end_s'])
        if i1 <= i0:
            rows.append({**w, 'db': None, 'f0': None})
            continue
        in_word[i0:i1] = True
        seg_f0 = f0[i0:i1][voiced[i0:i1]]
        rows.append({'start_s': float(w['start_s']), 'end_s': float(w['end_s']), 'text': w['text'],
                     'db': float(db[i0:i1].mean()),
                     'f0': float(np.median(seg_f0)) if len(seg_f0) else None})
    word_voiced = f0[voiced & in_word]
    ref_f0 = float(np.median(word_voiced)) if len(word_voiced) else None
    for r in rows:
        r['st'] = (12 * math.log2(r['f0'] / ref_f0)) if (r.get('f0') and ref_f0) else None
    speech_db = _pct([r['db'] for r in rows], .5)
    gaps = []
    for a, b in zip(rows, rows[1:]):
        g = b['start_s'] - a['end_s']
        if g >= GAP_MIN_S and speech_db is not None:
            i0, i1 = span(a['end_s'] + GAP_TRIM_S, b['start_s'] - GAP_TRIM_S)
            if i1 > i0:
                gaps.append({'start_s': a['end_s'], 'end_s': b['start_s'],
                             'rel_db': float(np.median(db[i0:i1]) - speech_db)})
    return {'ref_f0_hz': _r(ref_f0, 1), 'speech_db': _r(speech_db, 1), 'words': rows,
            'gaps': gaps, 'duration_s': nfr * HOP / sr}


# ---------------------------------------------------------------- windows and summary

def _speech_time(ws, segments=None, a=None, b=None):
    """Speaking time: Whisper's speech segments inside the stretch (the yardstick of the pipeline's WPM), or, with no
    segments, the words' own spans plus the short gaps between them (a pause of PAUSE_MIN_S or more is not speech)."""
    if segments:
        lo = float('-inf') if a is None else a
        hi = float('inf') if b is None else b
        return sum(max(0.0, min(e, hi) - max(s, lo)) for s, e in segments)
    if not ws:
        return 0.0
    t = sum(max(0.0, w['end_s'] - w['start_s']) for w in ws)
    t += sum(g for g in (y['start_s'] - x['end_s'] for x, y in zip(ws, ws[1:])) if 0 < g < PAUSE_MIN_S)
    return t


def span_stats(words, audio=None, a=None, b=None, segments=None):
    """Narration measurements over one stretch of time (a window, a beat, a whole film)."""
    ws = [w for w in words if (a is None or w['start_s'] >= a) and (b is None or w['start_s'] < b)]
    out = {'words': len(ws)}
    sp = _speech_time(ws, segments, a, b)
    out['speech_rate_wpm'] = _r(len(ws) / (sp / 60), 0) if sp >= 3 and len(ws) >= 6 else None
    gaps = [y['start_s'] - x['end_s'] for x, y in zip(ws, ws[1:])]
    pauses = [g for g in gaps if g >= PAUSE_MIN_S]
    out['pauses'] = len(pauses)
    out['longest_pause_s'] = _r(max(pauses, default=0.0))
    if audio:
        rows = [r for r in audio['words'] if (a is None or r['start_s'] >= a) and (b is None or r['start_s'] < b)]
        sts = [r['st'] for r in rows if r.get('st') is not None]
        # Per-word pitch (each word's median), so one octave slip in a frame doesn't widen the range.
        out['pitch_range_st'] = _r(_pct(sts, .9) - _pct(sts, .1)) if len(sts) >= 8 else None
        moves = [abs(y - x) for x, y in zip(sts, sts[1:])]
        out['pitch_movement_st'] = _r(statistics.mean(moves)) if len(moves) >= 4 else None
        dbs = [r['db'] for r in rows if r.get('db') is not None]
        out['loudness_contrast_db'] = _r(statistics.pstdev(dbs)) if len(dbs) >= 4 else None
        out['speech_level_db'] = _r(statistics.median(dbs), 1) if dbs else None
        lv = [g['rel_db'] for g in audio['gaps'] if (a is None or g['start_s'] >= a) and (b is None or g['start_s'] < b)]
        out['gap_level_rel_speech_db'] = _r(statistics.median(lv), 1) if lv else None
    return out


def windows(duration, words, audio, feats, shots, pair_kind, segments=None):
    out = []
    times = [f['t'] for f in feats]
    n = max(1, int(math.ceil(duration / WINDOW_S)))
    for k in range(n):
        a, b = k * WINDOW_S, min(duration, (k + 1) * WINDOW_S)
        row = {'start_s': _r(a), 'end_s': _r(b), **span_stats(words, audio, a, b, segments)}
        text = ' '.join(_clean(w['text']) for w in words if a <= w['start_s'] < b)
        row['said'] = (text[:420] + '...') if len(text) > 420 else text
        if feats:
            lo, hi = bisect.bisect_left(times, a), bisect.bisect_left(times, b)
            kinds = pair_kind[max(1, lo):hi]
            row['cuts'] = sum(1 for s in shots if a <= s['start_s'] < b and s['begins_with'] in ('cut', 'transition'))
            row['motion_share'] = _r(sum(1 for x in kinds if x == 'motion') / len(kinds), 3) if kinds else None
            fr = feats[lo:hi]
            row['luma'] = _r(statistics.mean(f['luma'] for f in fr), 1) if fr else None
            row['saturation'] = _r(statistics.mean(f['sat'] for f in fr), 1) if fr else None
            row['shots_seen'] = sum(1 for s in shots if s['start_s'] < b and s['end_s'] > a)
        out.append(row)
    return out


def _thirds(wins, key, duration):
    if not wins or not duration:
        return None
    res = []
    for i in range(3):
        a, b = duration * i / 3, duration * (i + 1) / 3
        vals = [w.get(key) for w in wins if a <= w['start_s'] < b and w.get(key) is not None]
        res.append(_r(statistics.median(vals)) if vals else None)
    return res


def summarize(duration, words, audio, shots, pair_kind, wins, segments=None):
    s = {'duration_s': _r(duration)}
    if words:
        whole = span_stats(words, audio, segments=segments)
        nar = {'words': len(words), 'speech_rate_wpm': whole.get('speech_rate_wpm'),
               'pauses_per_min': _r(whole['pauses'] / (duration / 60), 2) if duration else None,
               'rate_across_windows_wpm': _dist([w.get('speech_rate_wpm') for w in wins], 0),
               'by_third': {'speech_rate_wpm': _thirds(wins, 'speech_rate_wpm', duration)}}
        if audio:
            nar.update({'register_hz': audio.get('ref_f0_hz'),
                        'pitch_range_st': _dist([w.get('pitch_range_st') for w in wins]),
                        'pitch_movement_st': _dist([w.get('pitch_movement_st') for w in wins]),
                        'loudness_contrast_db': _dist([w.get('loudness_contrast_db') for w in wins]),
                        'gap_level_rel_speech_db': _dist([g['rel_db'] for g in audio['gaps']], 1)})
            nar['by_third'].update({k: _thirds(wins, k, duration) for k in
                                    ('pitch_range_st', 'pitch_movement_st', 'loudness_contrast_db')})
        s['narration'] = nar
    if shots:
        lengths = [x['length_s'] for x in shots]
        kinds = [k for k in pair_kind[1:]]
        s['picture'] = {
            'shots': len(shots),
            'cuts_per_min': _r((len(shots) - 1) / (duration / 60), 2) if duration else None,
            'shot_length_s': _dist(lengths, 1), 'longest_shot_s': _r(max(lengths), 1),
            'boundaries': {k: sum(1 for x in shots if x['begins_with'] == k) for k in ('cut', 'transition')},
            'moving_time_share': _r(sum(1 for k in kinds if k == 'motion') / len(kinds), 3) if kinds else None,
            'still_time_share': _r(sum(1 for k in kinds if k == 'still') / len(kinds), 3) if kinds else None,
            'flashes': sum(1 for k in kinds if k == 'flash'),
            'same_picture_again': sum(1 for x in shots if x.get('same_picture_as_shot')),
            'brightness_across_shots': _dist([x['luma'] for x in shots], 1),
            'saturation_across_shots': _dist([x['saturation'] for x in shots], 1),
            'by_third': {'cuts': [sum(w.get('cuts') or 0 for w in wins if duration * i / 3 <= w['start_s'] < duration * (i + 1) / 3)
                                  for i in range(3)],
                         'motion_share': _thirds(wins, 'motion_share', duration)}}
    return s


# ---------------------------------------------------------------- watch sheets

def _font(size):
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    for name in ('arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text, width, lines):
    words, rows, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width:
            rows.append(cur)
            cur = w
            if len(rows) == lines:
                break
        else:
            cur = (cur + ' ' + w).strip()
    if len(rows) < lines and cur:
        rows.append(cur)
    if len(rows) == lines and len(' '.join(rows)) < len(text):
        rows[-1] = rows[-1][:max(0, width - 3)] + '...'
    return rows


def _mmss(t):
    t = max(0, int(round(t)))
    return f'{t // 60:02d}:{t % 60:02d}'


def _mmss_tenths(t):
    t = max(0.0, float(t or 0))
    tenths = int(round(t * 10))
    return f'{tenths // 600:02d}:{(tenths // 10) % 60:02d}.{tenths % 10}'


def window_sheet(frames, out_path, title, words=()):
    """One contact sheet of a closer look (inspect-window): every frame of the window in order, each with its own
    time, and the words said during the window under the title. frames: [(t_s, path)]."""
    from PIL import Image, ImageDraw
    cols = 6
    tw, th = 240, 135
    rows = max(1, math.ceil(len(frames) / cols))
    head = 52
    sheet = Image.new('RGB', (cols * tw, head + rows * (th + 18)), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    f_small, f_head = _font(12), _font(15)
    draw.text((8, 6), title, fill=(235, 235, 235), font=f_head)
    said = ' '.join(_clean(w.get('text') or '') for w in words)
    if said:
        draw.text((8, 27), _wrap(said, 150, 1)[0], fill=(200, 200, 200), font=f_small)
    for j, (ts, fp) in enumerate(frames):
        x, y = (j % cols) * tw, head + (j // cols) * (th + 18)
        try:
            im = Image.open(fp).convert('RGB')
            im.thumbnail((tw - 4, th - 4))
            sheet.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        except OSError:
            pass
        draw.text((x + 4, y + th + 1), _mmss_tenths(ts), fill=(255, 210, 90), font=f_small)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=85)
    return str(out_path)


def render_sheets(feats, words, wins, out_dir, label, duration, tiles=None):
    """One JPEG per minute: a frame every SHEET_STEP_S seconds with the words spoken during those seconds. tiles, when
    a list, gets each tile's step start and the time of the frame it shows."""
    from PIL import Image, ImageDraw
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('sheet-*.jpg'):
        old.unlink()
    times = [f['t'] for f in feats]
    f_small, f_head = _font(13), _font(16)
    per = SHEET_COLS * SHEET_ROWS
    span = per * SHEET_STEP_S
    paths = []
    for m in range(int(math.ceil(duration / span))):
        t0 = m * span
        sheet = Image.new('RGB', (SHEET_COLS * TILE_W, 34 + SHEET_ROWS * (TILE_H + CAPTION_H)), (18, 18, 18))
        draw = ImageDraw.Draw(sheet)
        mw = [w for w in wins if t0 <= w['start_s'] < t0 + span]

        def agg(key, fn=sum):
            vals = [w.get(key) for w in mw if w.get(key) is not None]
            return fn(vals) if vals else None
        bits = [f'{label}  {_mmss(t0)}-{_mmss(min(duration, t0 + span))}']
        if agg('cuts') is not None:
            bits.append(f'cuts {agg("cuts")}')
        mo = agg('motion_share', lambda v: statistics.mean(v))
        if mo is not None:
            bits.append(f'moving {mo:.0%}')
        rate = agg('speech_rate_wpm', lambda v: statistics.median(v))
        if rate is not None:
            bits.append(f'{rate:.0f} wpm')
        pr = agg('pitch_range_st', lambda v: statistics.median(v))
        if pr is not None:
            bits.append(f'pitch range {pr:.1f} st')
        draw.text((8, 8), '   '.join(bits), fill=(235, 235, 235), font=f_head)
        for j in range(per):
            t = t0 + j * SHEET_STEP_S
            if t >= duration:
                break
            x, y = (j % SHEET_COLS) * TILE_W, 34 + (j // SHEET_COLS) * (TILE_H + CAPTION_H)
            shown = t
            if times:
                i = min(len(times) - 1, max(0, bisect.bisect_left(times, t + SHEET_STEP_S / 2) - 1))
                shown = times[i]
                if tiles is not None:
                    tiles.append({'step_s': _r(t, 3), 'frame_s': _r(shown, 4)})
                try:
                    im = Image.open(feats[i]['path']).convert('RGB')
                    im.thumbnail((TILE_W - 4, TILE_H - 4))
                    sheet.paste(im, (x + (TILE_W - im.width) // 2, y + (TILE_H - im.height) // 2))
                except OSError:
                    pass
            said = ' '.join(_clean(w['text']) for w in words if t <= w['start_s'] < t + SHEET_STEP_S)
            # the picture's own time; the words are those said from the step's start, five seconds of them
            draw.text((x + 6, y + TILE_H + 2), f'{_mmss_tenths(shown)}  words {_mmss(t)}-{_mmss(t + SHEET_STEP_S)}',
                      fill=(255, 210, 90), font=f_small)
            for li, row in enumerate(_wrap(said, 44, 4)):
                draw.text((x + 6, y + TILE_H + 17 + li * 15), row, fill=(225, 225, 225), font=f_small)
        p = out_dir / f'sheet-{m + 1:03d}.jpg'
        sheet.save(p, quality=82)
        paths.append(str(p))
    return paths


# ---------------------------------------------------------------- one call

READING = ('Measurements, not verdicts. Compare with the references measured the same way and decide what they mean '
           'for this story; a number that differs from the references is a question to look into, not a fault.')


def profile(label, duration, frames=None, wav=None, words=None, sheets_dir=None, segments=None, fps=None,
            sampler=None):
    """Everything above for one video (or one narration, with no frames): summary, windows, shots, sheets.
    segments: Whisper's speech segments as (start_s, end_s), the pipeline's WPM yardstick for speaking time. fps: the
    rate the frames were sampled at (read from their times when not given); it is written beside the measurements,
    since a cut count depends on it. sampler: how the frames were picked (SAMPLER: each at its own timestamp)."""
    words = words or []
    feats = frame_features(frames) if frames else []
    if feats and not fps and len(feats) > 1:
        gaps = sorted(feats[j]['t'] - feats[j - 1]['t'] for j in range(1, len(feats)))
        fps = round(1.0 / gaps[len(gaps) // 2], 3) if gaps[len(gaps) // 2] > 0 else None
    shots, kinds, _ = segment_shots(feats) if feats else ([], [], [])
    audio = audio_features(wav, words) if (wav and words) else None
    if not duration:
        duration = max([feats[-1]['t'] if feats else 0.0, words[-1]['end_s'] if words else 0.0])
    wins = windows(duration, words, audio, feats, shots, kinds, segments)
    summ = summarize(duration, words, audio, shots, kinds, wins, segments)
    if summ.get('picture') is not None:
        summ['picture']['sampled_fps'] = fps
    tiles = []
    sheets = render_sheets(feats, words, wins, sheets_dir, label, duration, tiles) if (sheets_dir and feats) else []
    return {'label': label, 'method': METHOD_VERSION, 'duration_s': _r(duration), 'sampled_fps': fps if feats else None,
            'summary': summ, 'windows': wins, 'shots': shots, 'sheets': sheets, 'sheet_tiles': tiles,
            'inspect_candidates': inspect_candidates(feats, kinds, shots) if feats else [],
            'sampler': sampler if feats else None,
            'thresholds': thresholds(fps if feats else None),
            'unknowns': unknowns(fps if feats else None, sampler if feats else None),
            'reading': READING}


ENV_HOP = 320                # 20 ms at 16 kHz: the loudness envelopes a narration is found by inside a mix


def _load_mono(path):
    np, librosa, sf = _audio_deps()
    y, sr = sf.read(str(path), dtype='float32', always_2d=False)
    if getattr(y, 'ndim', 1) > 1:
        y = y.mean(axis=1)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    return y


# ---------------------------------------------------------------- the silence between two lines, from the audio itself
# Whisper's word times place a line's end and the next line's start to within about 0.2 s (measured 2026-11-21 on a
# 35-line Eleven v4 part: the medians agree within 0.01 s, single lines differ by up to 0.2 s). A held silence is
# measured where it really is: frames more than QUIET_UNDER_DB under the narration's speech level (its 90th-percentile
# frame) are quiet, and the gap is the quiet run around Whisper's boundary. On that part, 35 dB matched Whisper's
# median gap within 0.01 s (30 dB: +0.01, 40 dB: -0.03, 45 dB: -0.05). A breath or a click inside a gap (a short stretch
# that stays well under speech) does not split it. The same measure reads the narration before and after a hold is
# inserted, so the edit's silences are verified with the yardstick that decided them.
GAP_HOP_S = 0.01
QUIET_UNDER_DB = 35.0
BRIDGE_MAX_S = 0.12         # a non-quiet stretch this short inside a gap ...
BRIDGE_UNDER_DB = 25.0      # ... that stays this far under the speech level is a breath or a click, not a word
GAP_SEARCH_S = 0.4          # how far from Whisper's boundary the silence may lie


def level_frames(y):
    """Loudness in dB of every 10 ms of a mono 16 kHz signal (20 ms windows)."""
    np, _, _ = _audio_deps()
    hop = int(SR * GAP_HOP_S)
    win = 2 * hop
    if len(y) < win:
        return np.full(1, -140.0)
    c = np.concatenate(([0.0], np.cumsum(np.asarray(y, dtype='float64') ** 2)))
    starts = np.arange(0, len(y) - win + 1, hop)
    power = (c[starts + win] - c[starts]) / win
    return 20 * np.log10(np.sqrt(np.maximum(power, 0)) + 1e-7)


def speech_level(levels):
    """The narration's speech level: its 90th-percentile 10 ms frame (the voice, not the silences)."""
    np, _, _ = _audio_deps()
    return float(np.percentile(levels, 90)) if len(levels) else 0.0


def quiet_run(levels, ref_db, t_s, duration_s=None, search_s=GAP_SEARCH_S):
    """The silence around time t_s: the run of quiet 10 ms frames nearest to it (within search_s), widened across
    breath- or click-short stretches that stay well under speech. (start_s, end_s), or None when nothing near t_s is
    quiet. A run that reaches the last frame ends at duration_s (the file's own end)."""
    n = len(levels)
    if not n:
        return None
    quiet = levels < ref_db - QUIET_UNDER_DB
    low = levels < ref_db - BRIDGE_UNDER_DB
    i = min(n - 1, max(0, int(round(t_s / GAP_HOP_S))))
    k = int(round(search_s / GAP_HOP_S))
    near = [j for j in range(max(0, i - k), min(n, i + k + 1)) if quiet[j]]
    if not near:
        return None
    j = min(near, key=lambda x: (abs(x - i), x))
    a = b = j
    bridge = int(round(BRIDGE_MAX_S / GAP_HOP_S))
    while True:
        while a > 0 and quiet[a - 1]:
            a -= 1
        m = a - 1          # a short low stretch, then quiet again: still the same silence
        while m >= 0 and not quiet[m] and low[m] and a - m <= bridge:
            m -= 1
        if m >= 0 and quiet[m] and a - m - 1 <= bridge and m < a - 1:
            a = m
            continue
        break
    while True:
        while b < n - 1 and quiet[b + 1]:
            b += 1
        m = b + 1
        while m < n and not quiet[m] and low[m] and m - b <= bridge:
            m += 1
        if m < n and quiet[m] and m - b - 1 <= bridge and m > b + 1:
            b = m
            continue
        break
    start = (a + 0.5) * GAP_HOP_S
    end = (b + 1.5) * GAP_HOP_S
    if b >= n - 1 and duration_s is not None:
        end = float(duration_s)
    if a == 0:
        start = 0.0
    return (round(start, 3), round(end, 3))


def line_gaps(wav, rows, last_index=None):
    """The silence after each line as the audio has it. rows: [{'index', 'start_s', 'end_s'}] in narration order, on
    the file's clock (Whisper's times); last_index: the script's last line. For each line: {'index', 'gap_s', 'span_s':
    [start, end], 'basis'}: 'audio' (the quiet run around Whisper's boundary, or the quiet tail after the script's last
    line) or 'whisper' (no quiet run near the boundary: Whisper's own gap is all there is). A line whose next line is not
    in this audio yet (its part not recorded) has gap_s None and basis 'unknown': the silence after it exists only once
    both sides are recorded."""
    y = _load_mono(wav)
    levels = level_frames(y)
    ref = speech_level(levels)
    dur = len(y) / SR
    out = []
    order = [r for r in rows if r.get('start_s') is not None and r.get('end_s') is not None]
    for r, nx in zip(order, order[1:] + [None]):
        if nx is not None and int(nx['index']) != int(r['index']) + 1:
            nx = 'gap'
        if nx == 'gap' or (nx is None and last_index is not None and int(r['index']) != int(last_index)):
            out.append({'index': r['index'], 'gap_s': None, 'span_s': None, 'basis': 'unknown'})
            continue
        if nx is None:      # after the script's last line: the quiet tail of the file, if it has one
            run = quiet_run(levels, ref, dur, duration_s=dur, search_s=0.05)
            run = run if run and run[1] >= dur - GAP_HOP_S else None
            span = [run[0], round(dur, 3)] if run else [round(min(float(r['end_s']), dur), 3), round(dur, 3)]
            out.append({'index': r['index'], 'gap_s': round(max(0.0, span[1] - span[0]), 3), 'span_s': span,
                        'basis': 'audio' if run else 'whisper', 'last_line': True})
            continue
        mid = (float(r['end_s']) + float(nx['start_s'])) / 2
        run = quiet_run(levels, ref, mid, duration_s=dur)
        if run:
            out.append({'index': r['index'], 'gap_s': round(run[1] - run[0], 3), 'span_s': list(run), 'basis': 'audio'})
        else:
            out.append({'index': r['index'], 'gap_s': round(max(0.0, float(nx['start_s']) - float(r['end_s'])), 3),
                        'span_s': [round(float(r['end_s']), 3), round(float(nx['start_s']), 3)], 'basis': 'whisper'})
    for g in out:
        if g['basis'] == 'audio' and g.get('span_s'):
            detail = gap_detail(levels, ref, g['span_s'], dur, last_line=bool(g.get('last_line')))
            if detail:
                g.update(detail)
    return {'speech_level_db': round(ref, 1), 'quiet_under_db': QUIET_UNDER_DB, 'duration_s': round(dur, 3),
            'gaps': out}


# Inside one silence. A gap can hold a breath or a click between stretches of true quiet (bridged above). An added
# silence goes in the middle of the LONGEST quiet stretch: an intake of breath just before the next line stays with
# that line, a release just after the last word stays with it, and the decaying end of the last word is never cut.
# How loud the voice's own silence is (its room tone, in dB under the speech level) decides whether there is any
# material a fade could work on: under AUDIBLE_FLOOR_UNDER_DB it is silence already (one eleven_v4 voice measured
# about 62 dB under its speech, 2026-11-21), and a fade would change nothing anyone can hear.
AUDIBLE_FLOOR_UNDER_DB = 55.0


def gap_detail(levels, ref, span, dur, last_line=False):
    """The quiet stretches inside one silence (span_s, on the file's clock): the longest one (`subrun_s`), where an added
    silence goes (`insert_at_s`: its middle; after the script's last line, the end of the file), the level of the
    voice's own silence there (`floor_under_speech_db`) and how much non-quiet material (a breath, a click) the
    silence holds (`other_material_s`). None when nothing in it is quiet."""
    np, _, _ = _audio_deps()
    a = max(0, min(int(round(span[0] / GAP_HOP_S)), len(levels) - 1))
    b = max(a + 1, min(int(round(span[1] / GAP_HOP_S)), len(levels)))
    seg = levels[a:b]
    quiet = seg < ref - QUIET_UNDER_DB
    runs, k = [], 0
    while k < len(seg):
        if quiet[k]:
            j = k
            while j + 1 < len(seg) and quiet[j + 1]:
                j += 1
            runs.append((k, j))
            k = j + 1
        else:
            k += 1
    if not runs:
        return None
    lo, hi = max(runs, key=lambda x: (x[1] - x[0], -x[0]))
    if len(runs) > 1:
        # Something sounds inside the silence (a breath, a release). An intake of breath leads into the next phrase,
        # a release ends the last one: one past the middle of the silence (or at it) stays with the next line, the
        # added silence goes before it; one in the first half stays with the line before, the silence goes after it.
        # A stretch too short to split (under 40 ms) falls back to the longest quiet stretch.
        sounds = [(runs[k][1] + 1, runs[k + 1][0] - 1) for k in range(len(runs) - 1)]
        s0, s1 = max(sounds, key=lambda x: x[1] - x[0])
        k = sounds.index((s0, s1))
        pick = runs[k] if (s0 + s1) / 2 >= 0.45 * len(seg) else runs[k + 1]
        if (pick[1] - pick[0] + 1) * GAP_HOP_S >= 0.04:
            lo, hi = pick
    sub = [round((a + lo + 0.5) * GAP_HOP_S, 3), round(min(dur, (a + hi + 1.5) * GAP_HOP_S), 3)]
    if hi >= len(seg) - 1 and b >= len(levels):
        sub[1] = round(dur, 3)
    floor = float(np.median(seg[quiet]))
    return {'subrun_s': sub, 'insert_at_s': round(dur, 3) if last_line else round((sub[0] + sub[1]) / 2, 3),
            'floor_under_speech_db': round(ref - floor, 1),
            'other_material_s': round(float((~quiet).sum()) * GAP_HOP_S, 3)}


# ---------------------------------------------------------------- how a line ends and the next begins
# The pitch and level of the last quarter-second of a line, next to the line's own and to the same voice's other
# endings, say whether the voice lands the sentence (falls, softens: a silence after it reads as meant) or leaves it
# hanging (stays level or rises: a long silence after it can sound like a dropout). The next line's first quarter-
# second says how it starts again (a pitch reset is a fresh start). Facts for the director, never a verdict: a
# suspended ending can be exactly the joke. Pitch: pYIN at CADENCE_HOP (16 ms). Its floor is 40 Hz and its frame
# 128 ms because narrators often land a sentence in creaky voice, far below their speaking pitch: one eleven_v4 voice
# ended a line at about 50 Hz (2026-11-21), which a 65 Hz floor clipped and a 500 Hz ceiling stopped calling voiced,
# reading a falling ending as a rising one. The 400 Hz ceiling covers narration; a shout above it reads unvoiced.
CADENCE_HOP = 256
CADENCE_FMIN, CADENCE_FMAX, CADENCE_FRAME = 40.0, 400.0, 2048
LOUD_VOWEL_UNDER_DB = 25.0      # a pitched frame within 25 dB of the speech level: a vowel, not a creak or a breath
END_WINDOW_S = 0.25
BEFORE_WINDOW_S = 0.5


def line_cadence(wav, rows):
    """For each pair of consecutive lines (rows: [{'index', 'start_s', 'end_s', 'gap_span_s'?}] in order, on the
    file's clock): how the first ends: `last_vowel_vs_line_st` (the pitch of its last clearly voiced, loud quarter-
    second against the line's, in semitones: below = falling), `last_vowel_fall_st` (against the half-second before),
    `soft_end_s` (sound after that vowel before the silence: a creaky or breathy landing, a release, final
    consonants; a creak lands a line but cannot be pitch-read, so read it with the next two), `end_level_db` (its last
    quarter-second of sound against the line's level); what the silence holds (`other_material_s`: a breath, a click);
    and how the next line begins: `next_reset_st` (its first vowels against this ending: a reset up is a fresh start),
    `next_lead_in_s` (sound before its first vowel: a breath, unvoiced consonants), `next_onset_level_db`. `usual`:
    this voice's median of each, the yardstick one ending is read against. Measurements, never a verdict."""
    np, librosa, _ = _audio_deps()
    y = _load_mono(wav)
    levels = level_frames(y)
    ref = speech_level(levels)
    f0, voiced, _ = librosa.pyin(y, fmin=CADENCE_FMIN, fmax=CADENCE_FMAX, sr=SR, frame_length=CADENCE_FRAME,
                                 hop_length=CADENCE_HOP)
    voiced = voiced & np.isfinite(f0)
    out = {}
    if not voiced.any():
        return {'boundaries': out, 'usual': {}, 'speech_level_dbfs': round(ref, 1)}
    st = np.full(len(f0), np.nan)
    st[voiced] = 12 * np.log2(f0[voiced] / float(np.median(f0[voiced])))
    hop_s = CADENCE_HOP / SR

    def vframes(a, b):
        i0, i1 = max(0, int(a / hop_s)), min(len(st), int(math.ceil(b / hop_s)))
        return [i for i in range(i0, i1) if voiced[i]]

    def med(ix):
        return float(np.median(st[ix])) if ix else None

    def level(a, b, speech_only=False):
        i0, i1 = max(0, int(a / GAP_HOP_S)), min(len(levels), max(int(a / GAP_HOP_S) + 1, int(math.ceil(b / GAP_HOP_S))))
        seg = levels[i0:i1]
        if speech_only:
            seg = seg[seg >= ref - QUIET_UNDER_DB]
        return float(np.median(seg)) if len(seg) else None
    # Pitch is read only on clearly voiced, LOUD frames (vowels): a creaky or breathy ending is too aperiodic for any
    # pitch tracker (its voicing confidence measured about 0.01, the same as ordinary vowels of a synthetic voice, so
    # the tracker's yes/no there depends on context). That soft end is measured by what can be measured: how long it
    # lasts after the last vowel and how far the level has dropped.
    lvl_at = lambda i: levels[min(len(levels) - 1, int(i * hop_s / GAP_HOP_S))]
    loud = [bool(voiced[i]) and lvl_at(i) >= ref - LOUD_VOWEL_UNDER_DB for i in range(len(st))]

    def vowels(a, b):
        i0, i1 = max(0, int(a / hop_s)), min(len(st), int(math.ceil(b / hop_s)))
        return [i for i in range(i0, i1) if loud[i]]
    order = [r for r in rows if r.get('start_s') is not None and r.get('end_s') is not None]
    for r, nx in zip(order, order[1:]):
        if int(nx['index']) != int(r['index']) + 1:
            continue
        span = r.get('gap_span_s') or [float(r['end_s']), float(nx['start_s'])]
        line_v = vowels(float(r['start_s']), float(span[0]))
        if len(line_v) < 8:
            continue
        t_last = line_v[-1] * hop_s
        last = [i for i in line_v if i * hop_s >= t_last - END_WINDOW_S]
        before = [i for i in line_v if t_last - END_WINDOW_S - BEFORE_WINDOW_S <= i * hop_s < t_last - END_WINDOW_S]
        line_level = level(float(r['start_s']), float(span[0]), speech_only=True)
        end_level = level(float(span[0]) - END_WINDOW_S, float(span[0]), speech_only=True)
        row = {'last_vowel_vs_line_st': _r(med(last) - med(line_v), 1),
               'last_vowel_fall_st': _r(med(last) - med(before), 1) if before else None,
               'end_level_db': _r(end_level - line_level, 1) if end_level is not None and line_level is not None else None,
               'soft_end_s': _r(max(0.0, float(span[0]) - (t_last + hop_s)), 2)}
        a, b = max(0, int(round(span[0] / GAP_HOP_S))), min(len(levels), int(round(span[1] / GAP_HOP_S)))
        row['other_material_s'] = _r(float((levels[a:b] >= ref - QUIET_UNDER_DB).sum()) * GAP_HOP_S, 2) if b > a else 0.0
        next_v = vowels(float(nx['start_s']), float(nx['end_s']))
        if next_v:
            t_first = next_v[0] * hop_s
            first = [i for i in next_v if i * hop_s <= t_first + END_WINDOW_S]
            nl = level(float(nx['start_s']), float(nx['end_s']), speech_only=True)
            ol = level(float(span[1]), float(span[1]) + END_WINDOW_S, speech_only=True)
            row.update({'next_reset_st': _r(med(first) - med(last), 1),
                        'next_lead_in_s': _r(max(0.0, t_first - float(span[1])), 2),
                        'next_onset_level_db': _r(ol - nl, 1) if ol is not None and nl is not None else None})
        out[int(r['index'])] = row
    usual = {}
    for k in ('last_vowel_vs_line_st', 'last_vowel_fall_st', 'end_level_db', 'soft_end_s', 'next_reset_st',
              'next_lead_in_s', 'next_onset_level_db'):
        vals = [v[k] for v in out.values() if v.get(k) is not None]
        if vals:
            usual[k] = _r(statistics.median(vals), 2)
    return {'boundaries': out, 'usual': usual, 'lines_read': len(out), 'speech_level_dbfs': round(ref, 1),
            'pitch_hop_s': round(hop_s, 3)}


def voice_unchanged(orig_wav, edit_wav, cuts, excluded=(), probe_s=0.02, max_lag=4, tol=3):
    """The edit's narration is the recording, sample for sample, outside its added silences and decided fades. cuts:
    [(at_s, added_s)] in order on the recording's clock; excluded: [[a, b]] stretches (fades) on the same clock. For
    each stretch between splices, probes at a quarter, half and three quarters of it (away from splices and fades) are
    looked up in the edit within a few samples of where they must be and compared on the first channel. Returns the
    probes that do not match (empty: the voice is untouched)."""
    np, _, sf = _audio_deps()
    a, sra = sf.read(str(orig_wav), dtype='int16', always_2d=True)
    b, srb = sf.read(str(edit_wav), dtype='int16', always_2d=True)
    if sra != srb:
        return [{'problem': f'sample rates differ ({sra} and {srb}): the edit was resampled'}]
    a, b = a[:, 0].astype('int32'), b[:, 0].astype('int32')
    n = int(round(probe_s * sra))
    edges = [0.0] + [float(c[0]) for c in cuts] + [len(a) / sra]
    shifts = [0.0]
    for c in cuts:
        shifts.append(shifts[-1] + float(c[1]))
    bad = []
    for k in range(len(edges) - 1):
        lo, hi = edges[k] + 0.03, edges[k + 1] - 0.03
        if hi - lo < 3 * probe_s:
            continue
        for frac in (0.25, 0.5, 0.75):
            t = lo + (hi - lo) * frac
            if any(float(x0) - probe_s <= t <= float(x1) for x0, x1 in excluded):
                continue
            i = int(round(t * sra))
            o = a[i:i + n]
            j = i + int(round(shifts[k] * sra))
            best = None
            for lag in range(-max_lag, max_lag + 1):
                if j + lag < 0:
                    continue
                e = b[j + lag:j + lag + n]
                if len(e) == len(o) and len(o):
                    d = int(np.max(np.abs(o - e)))
                    best = d if best is None else min(best, d)
            if best is None or best > tol:
                bad.append({'at_s': round(t, 3), 'max_difference': best})
    return bad


def silence_at(wav, t_s, search_s=GAP_SEARCH_S):
    """The quiet run around one moment of a file (the check that an inserted hold is where it was decided, as long as
    decided): (start_s, end_s) or None."""
    y = _load_mono(wav)
    levels = level_frames(y)
    return quiet_run(levels, speech_level(levels), t_s, duration_s=len(y) / SR, search_s=search_s)


def silences_at(wav, times, search_s=GAP_SEARCH_S):
    """silence_at for several moments of one file, loading it once."""
    y = _load_mono(wav)
    levels = level_frames(y)
    ref = speech_level(levels)
    return [quiet_run(levels, ref, t, duration_s=len(y) / SR, search_s=search_s) for t in times]


def _envelope(y):
    """Loudness per 20 ms (dB) of a pre-emphasised signal: speech stands out over a low music bed."""
    np, _, _ = _audio_deps()
    if len(y) < 2 * ENV_HOP:
        return np.zeros(1)
    y = np.append(y[0], y[1:] - 0.97 * y[:-1])
    n = len(y) // ENV_HOP
    frames = y[:n * ENV_HOP].reshape(n, ENV_HOP)
    return 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)


def narration_in_mix(mix_wav, narration_wav, windows=12, win_s=20.0, search_s=3.0):
    """Where an approved narration sits inside a mix (the export): their loudness envelopes compared window by window
    along the narration, each window searched within +-search_s. Per window: the lag and how closely the two match.
    Over the film: the spread and the slope of the lag (a speed change drifts, a cut or an insert jumps; a stretch
    the narration has and the mix lacks is not found), and the level of everything else under the voice: the mix
    where the narration is silent against the mix where it speaks. Measurement only: what it means is read by the
    checks and the agents."""
    np, _, _ = _audio_deps()
    nar, mix = _envelope(_load_mono(narration_wav)), _envelope(_load_mono(mix_wav))
    fps = SR / ENV_HOP
    W, S = int(win_s * fps), int(search_s * fps)
    if len(nar) <= W:
        W = max(10, len(nar) - 1)
    speaking = nar > (np.percentile(nar, 98) - 30)
    starts = sorted(set(int(x) for x in np.linspace(0, max(0, len(nar) - W), max(1, windows))))
    rows = []
    for p in starts:
        seg = nar[p:p + W]
        if len(seg) < 10 or speaking[p:p + W].mean() < 0.25:
            continue
        sz = (seg - seg.mean()) / (seg.std() + 1e-9)
        best_c, best_l = -2.0, None
        for lag in range(-S, S + 1):
            q = p + lag
            if q < 0 or q + W > len(mix):
                continue
            c = mix[q:q + W]
            cz = (c - c.mean()) / (c.std() + 1e-9)
            v = float(np.dot(sz, cz) / len(sz))
            if v > best_c:
                best_c, best_l = v, lag
        rows.append({'at_s': _r(p / fps, 1), 'lag_s': _r(best_l / fps, 3) if best_l is not None else None,
                     'match': _r(best_c, 3)})
    good = [r for r in rows if r['lag_s'] is not None and r['match'] >= 0.5]
    lags = [r['lag_s'] for r in good]
    slope = None
    if len(good) >= 3:
        xs = np.array([r['at_s'] for r in good]) / 60.0
        slope = _r(float(np.polyfit(xs, np.array(lags), 1)[0]), 3)
    n = min(len(nar), len(mix))
    quiet, loud = mix[:n][~speaking[:n]], mix[:n][speaking[:n]]
    bed = _r(float(np.median(quiet) - np.median(loud)), 1) if len(quiet) > 50 and len(loud) > 50 else None
    return {'windows': rows, 'weak_windows': [r['at_s'] for r in rows if r['lag_s'] is None or r['match'] < 0.5],
            'median_lag_s': _r(statistics.median(lags), 3) if lags else None,
            'lag_spread_s': _r(max(lags) - min(lags), 3) if lags else None, 'lag_slope_s_per_min': slope,
            'bed_level_rel_speech_db': bed, 'narration_s': _r(len(nar) / fps, 1), 'mix_s': _r(len(mix) / fps, 1),
            'method': 'pre-emphasised 20 ms loudness envelopes, z-normalised, best lag per window within '
                      f'+-{search_s:g} s'}


def _frame_at(video, t, width=320):
    """One frame of a video at t seconds (BGR array), through ffmpeg; None when there is none."""
    np, cv2 = _np_cv()
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-ss', f'{max(0.0, float(t)):.3f}', '-i', str(video),
           '-frames:v', '1', '-vf', f'scale={int(width)}:-2', '-f', 'image2pipe', '-vcodec', 'png', '-']
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0 or not p.stdout:
        return None
    return cv2.imdecode(np.frombuffer(p.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)


def _picture_features(img, cv2, width=640, n=1500):
    """ORB keypoints and descriptors of a picture at a working width: they survive a move, a zoom, a caption and an
    overlay over part of the frame, as a whole-picture comparison does not."""
    h, w = img.shape[:2]
    if w != width:
        img = cv2.resize(img, (int(width), max(2, int(h * width / w))), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    return cv2.ORB_create(nfeatures=n).detectAndCompute(g, None)


def _picture_inliers(fa, fb, np, cv2):
    """How many keypoints of two pictures agree on one geometric mapping (ratio-tested matches, RANSAC homography)."""
    (ka, da), (kb, db) = fa, fb
    if da is None or db is None or len(ka) < 8 or len(kb) < 8:
        return 0
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da, db, k=2)
    good = [q[0] for q in pairs if len(q) == 2 and q[0].distance < 0.75 * q[1].distance]
    if len(good) < 8:
        return 0
    src = np.float32([ka[g.queryIdx].pt for g in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[g.trainIdx].pt for g in good]).reshape(-1, 1, 2)
    _h, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    return int(mask.sum()) if mask is not None else 0


PICTURE_FOUND = 15          # inliers: the still is in the frame (measured on a real export: median 362 when it is)
PICTURE_OTHER = 30          # inliers another still needs to say the frame shows it instead


def picture_matches(video, samples, stills):
    """For each sample {'at_s', 'expect'} (a time in the export and the still file the project shows there): whether the
    export's frame there shows that still, by keypoints that agree on one geometric mapping (a camera move, a caption or
    an overlay over part of the frame leaves plenty). When the expected still is not found, every other still of the
    project is tried. verdict: 'found'; 'another' (another still clearly matches and the expected does not); 'unseen'
    (nothing matches well: a full-frame card, a dark frame). Measurement only: the checks say what a verdict means.
    Measured on one real export (2026-11-24): 85 of 92 shots found, 7 under full-frame overlays unseen, none 'another'."""
    np, cv2 = _np_cv()
    feats = {}
    for st in stills:
        try:
            img = cv2.imdecode(np.fromfile(str(st), dtype=np.uint8), cv2.IMREAD_COLOR)
        except (OSError, ValueError):
            img = None
        if img is not None:
            feats[str(st).lower().replace(chr(92), '/')] = (str(st), _picture_features(img, cv2))
    rows = []
    for smp in samples:
        exp = str(smp['expect']).lower().replace(chr(92), '/')
        row = {'at_s': smp['at_s'], 'expect': str(smp['expect']), 'shot': smp.get('shot')}
        frame = _frame_at(video, smp['at_s'], width=640)
        if frame is None or exp not in feats:
            rows.append({**row, 'verdict': 'unseen', 'error': 'no frame' if frame is None else 'still not readable'})
            continue
        ff = _picture_features(frame, cv2)
        e = _picture_inliers(ff, feats[exp][1], np, cv2)
        if e >= PICTURE_FOUND:
            rows.append({**row, 'verdict': 'found', 'inliers': e})
            continue
        best = max(((_picture_inliers(ff, v[1], np, cv2), v[0]) for k, v in feats.items() if k != exp),
                   default=(0, None))
        verdict = 'another' if best[0] >= PICTURE_OTHER and best[0] >= 2 * e + 10 else 'unseen'
        rows.append({**row, 'verdict': verdict, 'inliers': e, 'best': best[1], 'best_inliers': best[0]})
    return rows


def delivery(label, wav, words, spans=None, segments=None):
    """The narration alone (a recorded part, a whole narration, a voice preview): its delivery over the whole and,
    when spans are given ({name: (start_s, end_s)}), over each span (a beat)."""
    audio = audio_features(wav, words) if words else None
    duration = audio['duration_s'] if audio else (words[-1]['end_s'] if words else 0.0)
    wins = windows(duration, words, audio, [], [], [], segments)
    out = {'label': label, 'method': METHOD_VERSION, 'duration_s': _r(duration),
           'summary': summarize(duration, words, audio, [], [], wins, segments).get('narration'), 'windows': wins,
           'thresholds': thresholds(), 'unknowns': unknowns(), 'reading': READING}
    if spans:
        out['spans'] = {k: {'start_s': _r(a), 'end_s': _r(b), **span_stats(words, audio, a, b, segments)}
                        for k, (a, b) in spans.items()}
    return out
