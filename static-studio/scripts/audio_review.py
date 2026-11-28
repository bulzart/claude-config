"""Sound review: what a film's sound measurably does, from the files its run already has, and the few passages worth a
person's ears (the listening sheet).

Why this exists (2026-11-26): no agent can hear. A finished film had been checked by records and by one whole-film
figure; nobody had measured each piece of music against the voice where it plays, a sound cut off between two lines,
the air at the turns, or the names the transcript did not recognise, and nobody had been given a short list of what
to listen to. This module measures those things and builds that list.

What it is not: a judge. It uses no model and gives no verdict on how a voice sounds, whether music suits a story or
whether a pause works. A survey of speech-quality predictors and audio language models (same date) found none
installed here and none reliable enough on modern synthetic speech to stand in for a listener. Every figure here is a
level, a time or a count; every question on the sheet is for a person.

What its first run on a real film taught (same date; 51 sounds placed): sounds overlap, so a finished file is compared
with all the project's sounds playing in a passage together, never with one of them alone (a faint piece of music
over a room tone had read as five wrong levels, none of them real); a sound that plays to the film's last frame ends
with the film, not "between two lines"; and a room tone under everything is not music, so music and ambience are
counted apart (it had hidden six stretches of 45 seconds or more with no music).

Everything is decoded with ffmpeg to mono 16 kHz and read in 50 ms frames. Nothing is written by this module."""
from __future__ import annotations

import statistics
import subprocess
from pathlib import Path

SR = 16000
HOP_S = 0.05                 # one level frame
ACTIVE_UNDER_DB = 30.0       # the voice counts as speaking within this many dB of its own level
SOUNDING_UNDER_DB = 40.0     # a placed sound counts as sounding within this many dB of its own loudest frame
CLEAR_RUN_S = 0.4            # a stretch with no voice this long lets what is under it be heard alone
EARLY_STOP_S = 0.2           # a placement this much shorter than its file was cut before the file ended
TAIL_FADED_DB = 12.0         # a tail this far under the sound's own level has been faded out
NO_BED_S = 45.0              # a stretch this long with no music is listed (a fact, not a fault)
EXPORT_DIFFERS_DB = 6.0      # the finished file plays a passage this far from what the project's sounds ask: look there
FILM_END_S = 0.5             # a sound that plays to within this of the film's end ends with the film
WORDS_OVER_IT = 0.5          # the voice is over at least this share of a sound: one the words must be heard over
BETWEEN_WORDS_S = 0.4        # a pause of the voice this long is where the sound between the words is read (av_tools GAP_MIN_S)
BETWEEN_TRIM = 2             # level frames left out at each edge of it: the voice's tail and onset (av_tools GAP_TRIM_S)
LIFT_RAMP_S = 0.6            # how long a lifted bed takes to rise and to come back, unless its plan says
LIFT_GUARD_S = 0.15          # a rise starts this long after the voice stops and is over this long before it returns


def _np():
    import numpy as np
    return np


def load_mono(path):
    """A file's sound as mono 16 kHz samples (empty when it has none or cannot be read)."""
    np = _np()
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


SMALL_SPEAKER_HZ = 200.0     # a phone or a laptop speaker gives almost nothing under this
SMALL_SPEAKER_SHARE = 0.05   # a sound with less of its energy above it than this plays there as near silence


def small_speaker_share(path, hz=SMALL_SPEAKER_HZ, first_s=120.0):
    """Share (0..1) of a sound file's energy that lies above hz, read on its first two minutes; None when the file
    has no sound to read. A low tone or a rumble can measure loud and still be silence on the speaker most viewers
    hear a film on: a held tone built on 55 and 110 Hz carried the whole second half of a film and its held silences,
    and a bought 'steam hiss' was nine tenths rumble under 40 Hz (2026-11-28)."""
    np = _np()
    y = load_mono(path)[:int(SR * first_s)]
    if len(y) < SR // 10:
        return None
    spec = np.abs(np.fft.rfft(y)) ** 2
    total = float(spec.sum())
    if total <= 0:
        return None
    return round(float(spec[np.fft.rfftfreq(len(y), 1.0 / SR) >= hz].sum()) / total, 3)


def levels(y):
    """Level in dB of every 50 ms."""
    np = _np()
    hop = int(SR * HOP_S)
    n = len(y) // hop
    if n == 0:
        return np.full(1, -140.0)
    return 10 * np.log10((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-14)


def clip_gain_db(volume):
    """A clip's volume in the project as dB (1 or nothing recorded: 0)."""
    import math
    try:
        v = float(volume)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if v <= 0 or abs(v - 1.0) < 1e-3 else 20 * math.log10(v)


def voice_profile(narration_file, volume=None):
    """The narration's level frames, where it is speaking, and the level it speaks at (the edit's narration plays from
    0, so its clock is the film's)."""
    np = _np()
    lv = levels(load_mono(narration_file)) + clip_gain_db(volume)
    ref = float(np.percentile(lv, 90))
    active = lv > ref - ACTIVE_UNDER_DB
    return {'levels': lv, 'active': active, 'speech_db': round(float(np.median(lv[active])) if active.any() else ref, 1),
            'duration_s': round(len(lv) * HOP_S, 2)}


def export_profile(export_file, voice):
    """A finished file (the export, or its master) on the same frames: its level through the film and the level it
    plays the voice at, read where the narration speaks. None when the file has no sound to read."""
    np = _np()
    lv = levels(load_mono(export_file))
    m = min(len(lv), len(voice['active']))
    if m < 20 or not voice['active'][:m].any():
        return None
    return {'levels': lv, 'speech_db': round(float(np.median(lv[:m][voice['active'][:m]])), 1),
            'duration_s': round(len(lv) * HOP_S, 2)}


def _runs(mask):
    """(start index, end index) of every run of True."""
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    return out


def _placed(track, voice):
    """One placed sound on the film's clock: (its facts, its first frame, its level frames, its runs with no voice
    over it). The frames are None when its file cannot be read."""
    np = _np()
    a, b = float(track['start_s']), float(track['end_s'])
    out = {'kind': track.get('kind'), 'file': Path(str(track.get('file'))).name, 'start_s': round(a, 2), 'end_s': round(b, 2)}
    y = load_mono(track['file'])
    src0 = max(0.0, float(track.get('source_start_s') or 0.0))
    if not len(y) or b <= a or src0 * SR >= len(y):
        return {**out, 'unreadable': True}, None, None, []
    file_s = len(y) / SR
    gain = clip_gain_db(track.get('volume'))
    lv = levels(y[int(src0 * SR):int((src0 + b - a) * SR)]) + gain
    sounding = lv > max(float(lv.max()) - SOUNDING_UNDER_DB, -90.0)
    level = float(np.median(lv[sounding])) if sounding.any() else float(lv.max())
    i0 = int(round(a / HOP_S))
    va = np.zeros(len(lv), dtype=bool)
    seg = voice['active'][i0:i0 + len(lv)]
    va[:len(seg)] = seg
    vl = voice['levels'][i0:i0 + len(lv)]
    voice_here = float(np.median(vl[seg])) if len(seg) and seg.any() else None
    clear = [(s, e) for s, e in _runs(sounding & ~va) if (e - s) * HOP_S >= CLEAR_RUN_S]
    longest = max(clear, key=lambda r: r[1] - r[0]) if clear else None
    early = file_s - src0 - (b - a)
    tail = float(np.median(lv[-2:]))
    alone = np.concatenate([lv[s:e] for s, e in clear]) if clear else None
    j0, j1 = int(round((b - 0.15) / HOP_S)), int(round((b + 0.4) / HOP_S))
    out.update({
        'level_db': round(level, 1), 'peak_db': round(float(lv.max()), 1),
        'under_voice_db': round((voice_here if voice_here is not None else voice['speech_db']) - level, 1),
        'voice_over_it_share': round(float((sounding & va).sum()) / max(1, int(sounding.sum())), 2),
        'in_the_clear_s': round(sum(e - s for s, e in clear) * HOP_S, 1),
        'longest_clear_s': [round(a + longest[0] * HOP_S, 2), round(a + longest[1] * HOP_S, 2)] if longest else None,
        # its level where it is heard alone, against the level the voice speaks at
        'alone_under_voice_db': round(voice['speech_db'] - float(np.median(alone)), 1) if alone is not None else None,
        'file_s': round(file_s, 2),
        'stops_early_s': round(early, 2) if early > EARLY_STOP_S else 0.0,
        'cut_while_sounding': bool(early > EARLY_STOP_S and level - tail < TAIL_FADED_DB),
        'end_between_lines': not bool(voice['active'][max(0, j0):j1].any())})
    if abs(gain) > 0.05:
        out['clip_volume'] = round(float(track['volume']), 3)        # a level set in the project, not in the file
    return out, i0, lv, clear


def placement_facts(track, voice):
    """One placed sound against the voice where it plays, by the project's own files: how far under the voice it sits,
    how long it is heard with no voice over it, and whether it was cut off before its file ended, still sounding.
    The level is the file's own with the clip's volume in the project (the house way bakes the level into the file and
    places it at volume 1)."""
    return _placed(track, voice)[0]


def project_mix(placed, voice):
    """The level of everything the project plays, frame by frame: the narration (its own floor in its pauses) and
    every placed sound, summed as power."""
    np = _np()
    live = [(i0, lv) for _, i0, lv, _ in placed if lv is not None]
    n = max([len(voice['levels'])] + [i0 + len(lv) for i0, lv in live])
    power = np.zeros(n)
    power[:len(voice['levels'])] += 10 ** (voice['levels'] / 10)
    for i0, lv in live:
        power[i0:i0 + len(lv)] += 10 ** (lv / 10)
    return 10 * np.log10(power + 1e-14)


def between_words(mix, voice):
    """What plays between the words, by the project's own files: in every pause of the voice of BETWEEN_WORDS_S or
    more (the silence before the first word and after the last left out), the level of everything the project plays
    there against the level the voice speaks at. The reading the reference measurements take from a finished film
    (av_tools gap_level_rel_speech_db: the same pause length and the same trim), so a mix can be set beside its models
    before it is exported. A forecast: the export is measured from its own sound, on Whisper's word times."""
    np = _np()
    m = len(voice['levels'])
    rel = []
    for s, e in _runs(~voice['active'][:m]):
        if s == 0 or e >= m or (e - s) * HOP_S < BETWEEN_WORDS_S:
            continue
        a, b = s + BETWEEN_TRIM, e - BETWEEN_TRIM
        if b > a:
            rel.append(float(np.median(mix[a:b])) - voice['speech_db'])
    if not rel:
        return {'pauses': 0, 'gap_level_rel_speech_db': None}
    return {'pauses': len(rel), 'gap_level_rel_speech_db': {
        k: round(float(np.percentile(rel, q)), 1) for k, q in (('p10', 10), ('median', 50), ('p90', 90))}}


def music_alone(placements):
    """Where music is heard with no voice over it: for how long in all, its longest such stretch, how far under the
    voice's level it plays there, and the most any piece comes up there above its own level through the film
    (rises_when_alone_db: near 0 when one level was set for the whole of it). None when the film has no music."""
    ps = [p for p in placements if p.get('kind') == 'music' and not p.get('unreadable')]
    if not ps:
        return None
    spans = [p['longest_clear_s'] for p in ps if p.get('longest_clear_s')]
    rows = [(p['under_voice_db'], p['alone_under_voice_db']) for p in ps if p.get('alone_under_voice_db') is not None]
    return {'seconds': round(sum(p.get('in_the_clear_s') or 0 for p in ps), 1),
            'longest': max(spans, key=lambda s: s[1] - s[0]) if spans else None,
            'under_voice_db_there': [min(a for _, a in rows), max(a for _, a in rows)] if rows else None,
            'rises_when_alone_db': round(max(u - a for u, a in rows), 1) if rows else None}


def voice_silences(voice, min_s, a=0.0, b=None):
    """Where the voice is silent for min_s or more on the film's clock, inside [a, b]; after the narration's last word
    the film has no voice, to b. [(from_s, to_s)]."""
    import math
    np = _np()
    m = len(voice['levels'])
    end = float(b) if b is not None else m * HOP_S
    quiet = np.ones(max(m, int(math.ceil(end / HOP_S))), dtype=bool)
    quiet[:m] = ~voice['active'][:m]
    out = []
    for s, e in _runs(quiet):
        x, y = max(float(a), s * HOP_S), min(end, e * HOP_S)
        if y - x >= float(min_s):
            out.append((round(x, 2), round(y, 2)))
    return out


def level_move(track, a, b, lead_s=3.0, q=90):
    """How far a placed sound's own level moves in [a, b] of the film against the lead_s before it, in dB (positive: it
    comes up there): its level there less its level before, each read at the q-th percentile of its 50 ms frames (90:
    its loud tenth, where a swell shows; 50: its middle, where a dip does). What a swell or a dip decided for a held
    silence looks like in the file itself. The music's own writing moves the level too, so this is a fact to listen
    beside. None when either stretch lies outside the file."""
    np = _np()
    y = load_mono(track['file'])
    off = max(0.0, float(track.get('source_start_s') or 0.0)) - float(track['start_s'])

    def level(x0, x1):
        i, j = int(round((x0 + off) * SR)), int(round((x1 + off) * SR))
        if i < 0 or j > len(y) or j - i < 2 * int(SR * HOP_S):
            return None
        return float(np.percentile(levels(y[i:j]), q))
    inside, before = level(float(a), float(b)), level(float(a) - float(lead_s), float(a) - 0.1)
    return None if inside is None or before is None else round(inside - before, 1)


def bake_lift(path, at_s, windows, by_db, ramp_s=LIFT_RAMP_S, guard_s=LIFT_GUARD_S):
    """Raise a baked bed where it is meant to be heard. Inside each window (the film's clock; the file starts at at_s)
    its level climbs by up to by_db over ramp_s, holds, and is back at its own level before the window ends, a guard
    inside each edge so a rise never sits on a word. A window too short for both ramps rises only as far as its length
    allows: the slope stays the same, so nothing pumps. Written over the file itself, in its own sample format; refused
    when the rise would clip. Returns the windows that changed the file, each with the rise it reached."""
    import os
    import soundfile as sf
    np = _np()
    by, ramp = float(by_db), max(0.05, float(ramp_s))
    wins = sorted((float(a) + guard_s, float(b) - guard_s) for a, b in windows if float(b) - float(a) > 2 * guard_s)
    used, peak, lifted = {}, 0.0, 0
    tmp = str(path) + '.lifting'
    with sf.SoundFile(str(path)) as src:
        sr = src.samplerate
        with sf.SoundFile(tmp, 'w', samplerate=sr, channels=src.channels, subtype=src.subtype, format=src.format) as dst:
            pos = 0
            while True:
                block = src.read(sr * 20, dtype='float32', always_2d=True)
                if not len(block):
                    break
                t0 = float(at_s) + pos / sr
                env = None
                for k, (a, b) in enumerate(wins):
                    if b <= t0 or a >= t0 + len(block) / sr:
                        continue
                    if env is None:
                        t = t0 + np.arange(len(block)) / sr
                        env = np.zeros(len(block))
                    e = by * np.clip(np.minimum(t - a, b - t) / ramp, 0.0, 1.0)
                    used[k] = max(used.get(k, 0.0), float(e.max()))
                    env = np.maximum(env, e)
                if env is not None and (env > 0).any():
                    block = block * (10 ** (env / 20)).astype('float32')[:, None]
                    lifted += int((env > 0.05).sum())
                    peak = max(peak, float(np.abs(block[env > 0]).max()))
                dst.write(block)
                pos += len(block)
    if peak > 1.0:
        os.remove(tmp)
        raise ValueError(f'the rise would clip the file (its peak would reach {peak:.2f} of full scale): lift it less, '
                         'or set the bed lower')
    os.replace(tmp, str(path))
    return {'windows': [[round(wins[k][0], 2), round(wins[k][1], 2), round(v, 1)] for k, v in sorted(used.items())
                        if v > 0.05],
            'lifted_s': round(lifted / sr, 1), 'ramp_s': ramp}


def placements_review(tracks, voice, export=None, total_s=None, between=None):
    """Every placed sound against the voice (placement_facts), which of them play to the film's last frame (total_s),
    and, with a finished file (export_profile), that file measured where no voice covers each sound, beside what all
    the project's sounds playing there ask for together. Together, because sounds overlap: a faint piece of music over
    a room tone is heard alone in no file, and comparing the file with that one piece reads the room tone as a wrong
    level. A dict given as `between` is filled with between_words (what the whole mix plays in the voice's pauses)."""
    np = _np()
    placed = [_placed(t, voice) for t in tracks]
    if total_s:
        for facts, *_ in placed:
            if not facts.get('unreadable') and facts['end_s'] >= float(total_s) - FILM_END_S:
                facts['ends_with_the_film'] = True
    mix = project_mix(placed, voice) if export or between is not None else None
    if between is not None:
        between.update(between_words(mix, voice))
    if export:
        m = min(len(mix), len(export['levels']))
        for facts, i0, lv, clear in placed:
            # Two frames in from each side of a run with no voice, so the voice's tail and onset are not read as music.
            idx = [k for s, e in clear if e - s > 6 for k in range(i0 + s + 2, min(i0 + e - 2, m))]
            if len(idx) >= 4:
                under = export['speech_db'] - float(np.median(export['levels'][idx]))
                asked = voice['speech_db'] - float(np.median(mix[idx]))
                facts['in_export'] = {'under_voice_db': round(under, 1), 'project_asks_db': round(asked, 1),
                                      'differs_db': round(under - asked, 1)}
    return [facts for facts, *_ in placed]


def is_cut_off(p):
    """A sound cut before its file ended, still sounding, where no line covers the cut and the film goes on: the stop
    a listener may hear as a mistake. (One that plays to the film's last frame ends with the film.)"""
    return bool(p.get('cut_while_sounding') and p.get('end_between_lines') and not p.get('ends_with_the_film'))


def short_name(file_name):
    """A sound's file as a person would name it: no baking suffix, no extension
    ('M2-letters.bed-m28.3dB.from68.2s-29.27s.wav' is 'M2-letters')."""
    s = str(file_name)
    return s.split('.bed-')[0] if '.bed-' in s else (s.rsplit('.', 1)[0] if '.' in s else s)


def bed_stretches(placements, total_s, kinds=('music', 'ambience')):
    """Where sounds of these kinds play at all, and the long stretches with none."""
    spans = sorted((p['start_s'], p['end_s']) for p in placements if p.get('kind') in kinds and not p.get('unreadable'))
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1] + 0.5:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    gaps, t = [], 0.0
    for s, e in merged + [[total_s, total_s]]:
        if s - t >= NO_BED_S:
            gaps.append([round(t, 1), round(s, 1)])
        t = max(t, e)
    covered = sum(e - s for s, e in merged)
    return {'plays': [[round(s, 1), round(e, 1)] for s, e in merged], 'none_for_long': gaps,
            'share_of_runtime': round(covered / total_s, 2) if total_s else None}


def beds_by_kind(placements, total_s):
    """Music and ambience apart: a room tone under a whole film is not music, and counted with it would hide every
    stretch the film plays without any."""
    return {'music': bed_stretches(placements, total_s, ('music',)),
            'ambience': bed_stretches(placements, total_s, ('ambience',))}


def line_gaps(marks, order):
    """The silence after each line on the edit clock (holds included): [{line, next, at_s, gap_s}]."""
    out = []
    for cur, nxt in zip(order, order[1:]):
        if cur in marks and nxt in marks:
            out.append({'line': cur, 'next': nxt, 'at_s': round(float(marks[cur]['end']), 2),
                        'gap_s': round(float(marks[nxt]['start']) - float(marks[cur]['end']), 2)})
    return out


def turn_facts(gaps, first_lines):
    """The air before each part's first line, beside the film's ordinary gap between lines.
    first_lines: {line id: {'beat': id, 'why': 'chapter' | 'key moment'}}."""
    plain = [g['gap_s'] for g in gaps if g['next'] not in first_lines and g['gap_s'] >= 0]
    usual = round(statistics.median(plain), 2) if plain else None
    turns = [{**g, **first_lines[g['next']], 'ordinary_gap_s': usual} for g in gaps if g['next'] in first_lines]
    return {'ordinary_gap_s': usual, 'turns': turns}


def pace_facts(marks, order, words):
    """Words per second of each line of eight words or more, with the film's median: the fastest and slowest lines."""
    rows = []
    for lid in order:
        m, w = marks.get(lid), words.get(lid) or 0
        if m and w >= 8 and float(m['end']) - float(m['start']) > 0.5:
            rows.append({'line': lid, 'at_s': round(float(m['start']), 2), 'end_s': round(float(m['end']), 2),
                         'words_per_s': round(w / (float(m['end']) - float(m['start'])), 2)})
    if len(rows) < 5:
        return {'median_words_per_s': None, 'fastest': [], 'slowest': []}
    med = statistics.median(r['words_per_s'] for r in rows)
    by = sorted(rows, key=lambda r: r['words_per_s'])
    rel = lambda r: {**r, 'against_median_pct': round(100 * (r['words_per_s'] / med - 1))}
    return {'median_words_per_s': round(med, 2), 'fastest': [rel(r) for r in by[-2:][::-1]],
            'slowest': [rel(r) for r in by[:2]]}


def mmss(t):
    t = max(0.0, float(t or 0))
    return f'{int(t // 60):02d}:{int(t % 60):02d}'


def export_gap_words(p):
    """How the finished file differs from the project at this sound, when it does by enough to look ('' otherwise)."""
    d = (p.get('in_export') or {}).get('differs_db')
    if d is None or abs(d) < EXPORT_DIFFERS_DB:
        return ''
    return f'the finished file plays this passage {abs(d):g} dB {"louder" if d < 0 else "quieter"} than the project asks'


def under_voice_words(p, file_measured=False):
    """How far under the voice a sound plays, by the project's own files, and what the finished file does there when
    one was measured (file_measured) and has a stretch of this sound with no voice over it."""
    d = (p.get('in_export') or {}).get('differs_db')
    said = f'{p["under_voice_db"]:g} dB under the voice by the project\'s files'
    if d is None:
        return said + ('; the voice is over all of it, so the finished file could not be read here' if file_measured
                       else '')
    return said + ('; the finished file plays the same there' if abs(d) < 0.05 else
                   f'; the finished file is {abs(d):g} dB {"louder" if d < 0 else "quieter"} there')


def _item(kind, a, b, total, question, measured, hear=''):
    a, b = max(0.0, a), min(total, b) if total else b
    return {'kind': kind, 'from_s': round(a, 1), 'to_s': round(b, 1), 'where': f'{mmss(a)}-{mmss(b)}',
            'hear': hear, 'question': question, 'measured': measured, 'answer': ''}


def listening_items(facts, texts=None, key_lines=None, limit_names=5):
    """The passages worth a person's ears, with one question each. Chosen from the measurements as places to listen,
    never as faults: the quietest music, the least quiet sound the words must be heard over, a sound cut off between
    lines, the turn with the least air, silences nobody has listened to, the names the transcript recognised least,
    the fastest line, the opening, each key moment's landing, the ending. A short list on purpose: a person's
    attention is the scarce thing here."""
    texts, total = texts or {}, float(facts.get('duration_s') or 0)
    marks = facts.get('line_marks') or {}
    items = [_item('voice', 0, min(25.0, total), total,
                   'Is this the narrator and the tone you want for this film? Does the first line make you want the next?',
                   'the opening, as it plays')]

    def line_window(lid, lead=6.0, tail=3.0):
        m = marks.get(lid)
        return (float(m['start']) - lead, float(m.get('silence_end') or m['end']) + tail) if m else None
    for lid, beat in list((key_lines or {}).items())[:3]:
        w = line_window(lid)
        if w:
            items.append(_item('key moment', w[0], w[1], total,
                               'Does this moment land: the way the line is said, the pause after it, what plays under it?',
                               f'the last line of key moment {beat}', hear=str(texts.get(lid, ''))[:110]))
    for n in (facts.get('names') or [])[:limit_names]:
        m = marks.get(n['line'])
        if m:
            seen = f' (recognised in {n.get("recognised") or 0} of its {n["uses"]} uses)' if (n.get('uses') or 0) > 1 else ''
            heard = f'heard "{n["nearest_heard"]}"' if n.get('nearest_heard') else 'heard nothing near it'
            items.append(_item('name', float(m['start']) - 1, min(float(m['end']) + 1, float(m['start']) + 14), total,
                               f'Is "{n["term"]}" said the way you want?',
                               f'planned as "{n.get("say") or n["term"]}"; the transcript {heard}{seen}',
                               hear=str(texts.get(n['line'], ''))[:110]))
    placed = [p for p in facts.get('placements') or [] if not p.get('unreadable')]
    in_file = 'speech_db' in (facts.get('export') or {})          # a finished file was measured too
    music = [p for p in placed if p.get('kind') == 'music']
    quiet = max(music, key=lambda p: p['under_voice_db']) if music else None
    if quiet:
        c = quiet.get('longest_clear_s') or [quiet['start_s'], min(quiet['end_s'], quiet['start_s'] + 10)]
        items.append(_item('music', c[0] - 4, c[1] + 4, total,
                           'Can you hear the music here? Is it as present as you want it?',
                           f'"{short_name(quiet["file"])}": {under_voice_words(quiet, in_file)}; '
                           f'{quiet["in_the_clear_s"]:g} s of it with no voice over it (the quietest music in the film)'))
    over = [p for p in placed if p.get('kind') in ('music', 'ambience')
            and (p.get('voice_over_it_share') or 0) >= WORDS_OVER_IT]
    loud = min(over, key=lambda p: p['under_voice_db']) if over else None
    if loud and loud is not quiet and (not quiet or quiet['under_voice_db'] - loud['under_voice_db'] >= 3):
        mid = (loud['start_s'] + loud['end_s']) / 2
        items.append(_item(str(loud.get('kind')), max(loud['start_s'] - 2, mid - 7), min(loud['end_s'] + 2, mid + 7), total,
                           f'Does the {loud.get("kind")} get in the way of the words here?',
                           f'"{short_name(loud["file"])}": {under_voice_words(loud, in_file)} '
                           '(the least quiet sound under the voice in the film)'))
    for p in [p for p in placed if is_cut_off(p)][:3]:
        items.append(_item('sound stop', p['end_s'] - 5, p['end_s'] + 3, total,
                           f'Do you hear a sound cut off at {mmss(p["end_s"])}?',
                           f'"{short_name(p["file"])}" stops {p["stops_early_s"]:g} s before its file ends, still '
                           'sounding, between two lines'))
    turns = (facts.get('turns') or {}).get('turns') or []
    usual = (facts.get('turns') or {}).get('ordinary_gap_s')
    tight = sorted((t for t in turns if t.get('why') == 'chapter' and usual and t['gap_s'] <= usual * 1.3),
                   key=lambda t: t['gap_s'])[:2]
    for t in tight:
        items.append(_item('turn', t['at_s'] - 8, t['at_s'] + t['gap_s'] + 6, total,
                           'A new part begins here. Does the turn have room, or does the film run straight on?',
                           f'{t["gap_s"]:g} s of air before {t["next"]} ({t["beat"]}); between ordinary lines it is {usual:g} s'))
    for h in sorted(facts.get('holds_not_listened') or [], key=lambda h: -float(h.get('total_s') or 0))[:3]:
        items.append(_item('silence', h['from_s'] - 8, h['to_s'] + 4, total,
                           'Does this silence work, or does it stall?',
                           f'{h.get("total_s")} s held after {h["line"]}; nobody is on record as having listened to it'))
    fast = ((facts.get('pace') or {}).get('fastest') or [None])[0]
    if fast and fast['against_median_pct'] >= 25:
        items.append(_item('pace', fast['at_s'] - 2, fast['end_s'] + 2, total, 'Is this line rushed?',
                           f'{fast["line"]}: {fast["against_median_pct"]} % faster than the film\'s median line',
                           hear=str(texts.get(fast['line'], ''))[:110]))
    if total > 60:
        on = sorted({str(p.get('kind')) for p in placed if p.get('ends_with_the_film') and p.get('cut_while_sounding')})
        items.append(_item('ending', total - 25, total, total,
                           'Does the ending land, and does the sound close cleanly?',
                           'the last 25 seconds' + (f'; {" and ".join(on)} still sounding at the film\'s last frame, '
                                                    'with no fade of its own' if on else '')))
    items.sort(key=lambda i: i['from_s'])
    for k, it in enumerate(items, 1):
        it['id'] = f'H{k}'
    return items


def sheet_markdown(items, title, file_name, facts):
    """The listening sheet as a page a person can follow with the film open."""
    secs = sum(i['to_s'] - i['from_s'] for i in items)
    beds = facts.get('beds') or {}
    music, amb = beds.get('music') or {}, beds.get('ambience') or {}
    pct = lambda d: int(round(100 * (d.get('share_of_runtime') or 0)))
    rows = [f'# Listening sheet: {title}', '',
            f'File: `{file_name}`. {len(items)} passages, about {int(round(secs / 60)) or 1} min of listening.',
            '', 'No check in this system can hear. Everything else was measured; these are the places where only your '
            'ears can decide. Use headphones first; play the music passages once more on a phone speaker.',
            'For each one, answer in a few words. "Fine" is an answer. Then tell the director, who records it '
            '(`human-review --answers`).', '',
            '| # | When | What | Listen for | Measured | Your answer |', '|---|---|---|---|---|---|']
    for i in items:
        hear = f' "{i["hear"]}"' if i.get('hear') else ''
        rows.append(f'| {i["id"]} | {i["where"]} | {i["kind"]}{hear} | {i["question"]} | {i["measured"]} |  |'
                    .replace('\n', ' '))
    rows += ['', '## What was measured, for reference', '',
             f'- The voice speaks at about {facts.get("speech_db")} dB (file level); ordinary gap between lines '
             f'{(facts.get("turns") or {}).get("ordinary_gap_s")} s.',
             f'- Music plays for {pct(music)} % of the film.'
             + (' Long stretches with none: ' + ', '.join(f'{mmss(a)}-{mmss(b)}' for a, b in music.get('none_for_long') or [])
                + '.' if music.get('plays') and music.get('none_for_long') else ''),
             *([f'- Ambience (background sound that is not music) plays for {pct(amb)} % of the film.']
               if amb.get('plays') else []),
             '- These figures say where sound is and how loud. They do not say how it sounds.', '']
    return '\n'.join(rows)
