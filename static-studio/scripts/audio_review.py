"""Sound review: what a film's sound measurably does, from the files its run already has, and the few passages worth a
person's ears (the listening sheet).

Why this exists (2026-11-26): no agent can hear. A finished film had been checked by records and by one whole-film
figure; nobody had measured each piece of music against the voice where it plays, a sound cut off between two lines,
the air at the turns, or the names the transcript heard differently, and nobody had been given a short list of what
to listen to. This module measures those things and builds that list.

What it is not: a judge. It uses no model and gives no verdict on how a voice sounds, whether music suits a story or
whether a pause works. A survey of speech-quality predictors and audio language models (same date) found none
installed here and none reliable enough on modern synthetic speech to stand in for a listener. Every figure here is a
level, a time or a count; every question on the sheet is for a person.

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
NO_BED_S = 45.0              # a stretch this long with no music or ambience is listed (a fact, not a fault)


def _np():
    import numpy as np
    return np


def load_mono(path):
    """A file's sound as mono 16 kHz samples (empty when it has none or cannot be read)."""
    np = _np()
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def levels(y):
    """Level in dB of every 50 ms."""
    np = _np()
    hop = int(SR * HOP_S)
    n = len(y) // hop
    if n == 0:
        return np.full(1, -140.0)
    return 10 * np.log10((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-14)


def voice_profile(narration_file):
    """The narration's level frames, where it is speaking, and the level it speaks at."""
    np = _np()
    lv = levels(load_mono(narration_file))
    ref = float(np.percentile(lv, 90))
    active = lv > ref - ACTIVE_UNDER_DB
    return {'levels': lv, 'active': active, 'speech_db': round(float(np.median(lv[active])) if active.any() else ref, 1),
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


def placement_facts(track, voice):
    """One placed sound against the voice where it plays: how far under the voice it sits, how long it is heard with
    no voice over it, and whether it was cut off before its file ended, still sounding, where nothing covers the cut."""
    np = _np()
    a, b = float(track['start_s']), float(track['end_s'])
    out = {'kind': track.get('kind'), 'file': Path(str(track.get('file'))).name, 'start_s': round(a, 2), 'end_s': round(b, 2)}
    y = load_mono(track['file'])
    if not len(y) or b <= a:
        return {**out, 'unreadable': True}
    file_s = len(y) / SR
    lv = levels(y[:int((b - a) * SR)])
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
    early = file_s - (b - a)
    tail = float(np.median(lv[-2:]))
    j0, j1 = int(round((b - 0.15) / HOP_S)), int(round((b + 0.4) / HOP_S))
    out.update({
        'level_db': round(level, 1), 'peak_db': round(float(lv.max()), 1),
        'under_voice_db': round((voice_here if voice_here is not None else voice['speech_db']) - level, 1),
        'voice_over_it_share': round(float((sounding & va).sum()) / max(1, int(sounding.sum())), 2),
        'in_the_clear_s': round(sum(e - s for s, e in clear) * HOP_S, 1),
        'longest_clear_s': [round(a + longest[0] * HOP_S, 2), round(a + longest[1] * HOP_S, 2)] if longest else None,
        'file_s': round(file_s, 2),
        'stops_early_s': round(early, 2) if early > EARLY_STOP_S else 0.0,
        'cut_while_sounding': bool(early > EARLY_STOP_S and level - tail < TAIL_FADED_DB),
        'end_between_lines': not bool(voice['active'][max(0, j0):j1].any())})
    return out


def bed_stretches(placements, total_s):
    """Where music or ambience plays at all, and the long stretches with none."""
    spans = sorted((p['start_s'], p['end_s']) for p in placements if p.get('kind') in ('music', 'ambience')
                   and not p.get('unreadable'))
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


def _item(kind, a, b, total, question, measured, hear=''):
    a, b = max(0.0, a), min(total, b) if total else b
    return {'kind': kind, 'from_s': round(a, 1), 'to_s': round(b, 1), 'where': f'{mmss(a)}-{mmss(b)}',
            'hear': hear, 'question': question, 'measured': measured, 'answer': ''}


def listening_items(facts, texts=None, key_lines=None, limit_names=5):
    """The passages worth a person's ears, with one question each. Chosen from the measurements as places to listen,
    never as faults: the quietest and the least quiet music, a sound cut off between lines, the turn with the least
    air, silences nobody has listened to, names the transcript heard differently, the fastest line, the opening, each
    key moment's landing, the ending. A short list on purpose: a person's attention is the scarce thing here."""
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
            items.append(_item('name', float(m['start']) - 1, min(float(m['end']) + 1, float(m['start']) + 14), total,
                               f'Is "{n["term"]}" said the way you want?',
                               f'planned as "{n.get("say") or n["term"]}"; the transcript heard "{n.get("nearest_heard")}"',
                               hear=str(texts.get(n['line'], ''))[:110]))
    beds = [p for p in facts.get('placements') or [] if p.get('kind') in ('music', 'ambience') and not p.get('unreadable')]
    if beds:
        quiet = max(beds, key=lambda p: p['under_voice_db'])
        loud = min(beds, key=lambda p: p['under_voice_db'])
        c = quiet.get('longest_clear_s') or [quiet['start_s'], min(quiet['end_s'], quiet['start_s'] + 10)]
        items.append(_item('music', c[0] - 4, c[1] + 4, total,
                           'Can you hear the music here? Is it as present as you want it?',
                           f'{quiet["file"]}: {quiet["under_voice_db"]:g} dB under the voice, '
                           f'{quiet["in_the_clear_s"]:g} s with no voice over it (the quietest in the film)'))
        if loud is not quiet and quiet['under_voice_db'] - loud['under_voice_db'] >= 3:
            mid = (loud['start_s'] + loud['end_s']) / 2
            items.append(_item('music', mid - 7, mid + 7, total,
                               'Does the music get in the way of the words here?',
                               f'{loud["file"]}: {loud["under_voice_db"]:g} dB under the voice (the least quiet in the film)'))
    for p in [p for p in facts.get('placements') or [] if p.get('cut_while_sounding') and p.get('end_between_lines')][:3]:
        items.append(_item('sound stop', p['end_s'] - 5, p['end_s'] + 3, total,
                           f'Do you hear a sound cut off at {mmss(p["end_s"])}?',
                           f'{p["file"]} stops {p["stops_early_s"]:g} s before its file ends, still sounding, between two lines'))
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
        items.append(_item('ending', total - 25, total, total,
                           'Does the ending land, and does the sound close cleanly?', 'the last 25 seconds'))
    items.sort(key=lambda i: i['from_s'])
    for k, it in enumerate(items, 1):
        it['id'] = f'H{k}'
    return items


def sheet_markdown(items, title, file_name, facts):
    """The listening sheet as a page a person can follow with the film open."""
    secs = sum(i['to_s'] - i['from_s'] for i in items)
    beds = facts.get('beds') or {}
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
             f'- Music or ambience plays for {int(round(100 * (beds.get("share_of_runtime") or 0)))} % of the film.'
             + (' Long stretches with none: ' + ', '.join(f'{mmss(a)}-{mmss(b)}' for a, b in beds.get('none_for_long') or [])
                + '.' if beds.get('none_for_long') else ''),
             '- These figures say where sound is and how loud. They do not say how it sounds.', '']
    return '\n'.join(rows)
