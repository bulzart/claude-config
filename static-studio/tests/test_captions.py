"""The captions (scripts/captions.py): the two looks the user picks at the start, the word timing from the narration's
own Whisper times, the highlight's moments, real builds into a scratch copy of the CapCut template with capcut-cli
(never the user's CapCut store), and the read-back check. No network, no CapCut window."""
from __future__ import annotations
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
os.environ.setdefault('STUDIO_HOME', str(ROOT))
import captions as cap          # noqa: E402
import static_core as core      # noqa: E402
import capcut_tools as ct       # noqa: E402

AWL = Path.home() / '.claude' / 'analyze-with-loupe' / 'scripts' / 'awl.py'


def template_draft():
    """The empty template every project is cloned from, from the real store's config, read only (copied, never edited)."""
    cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8')).get('capcut') or {}
    t = Path(cfg.get('drafts_dir') or '') / (cfg.get('template_draft') or '')
    return t if (t / 'draft_content.json').is_file() else None


def W(w, s, e, line='L001'):
    return {'w': w, 's': s, 'e': e, 'line': line}


class CaptionTimingTests(unittest.TestCase):
    def test_the_copied_word_box_code_is_the_original(self):
        if not AWL.is_file():
            self.skipTest('the original word-box builder is not on this PC')

        def defs(p):
            text = Path(p).read_text(encoding='utf-8').replace('\r\n', '\n')
            lines = text.split('\n')
            return {n.name: '\n'.join(lines[n.lineno - 1:n.end_lineno]) for n in ast.parse(text).body
                    if isinstance(n, ast.FunctionDef)}
        o, c = defs(AWL), defs(ROOT / 'scripts' / 'captions.py')
        for name in ('_unspaced', 'chunk_words_fill', '_word_box_plan', '_word_box_segments', '_capcut_em_px', '_wb_norm',
                     '_upper_for', '_drop_text_tracks'):
            self.assertEqual(c.get(name), o.get(name), name)

    def test_the_looks_and_their_fonts(self):
        lg, mh = cap.look_of('luckiest-guy'), cap.look_of('montserrat-highlight')
        self.assertEqual((lg['font_name'], lg['upper'], lg['shadow'], lg['box']['pad']), (['Luckiest Guy', 'Regular'], True, True, 0.05))
        self.assertEqual((mh['font_name'], mh['fill'], mh['active'], mh['stroke_color'], mh['shadow']),
                         (['Montserrat', 'Bold'], '#FFFFFF', '#FFFF00', '#000000', False))
        self.assertNotIn('box', mh)
        # the size gives the same em on every canvas (4.6 % of the smaller side), the font's own line height counted
        self.assertEqual((cap.capcut_size(lg['font_path'], 1920, 1080), cap.capcut_size(mh['font_path'], 1920, 1080)), (4.5, 5.49))
        self.assertEqual(cap.capcut_size(mh['font_path'], 1080, 1920), 9.75)
        # a substituted font is refused, never reported as applied
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'Montserrat-Bold.otf'
            shutil.copyfile(cap.FONTS_DIR / 'LuckiestGuy-Regular.ttf', fake)
            old = cap.FONTS_DIR
            cap.FONTS_DIR = Path(tmp)
            try:
                with self.assertRaises(RuntimeError) as e:
                    cap.look_of('montserrat-highlight')
                self.assertIn('not Montserrat Bold', str(e.exception))
            finally:
                cap.FONTS_DIR = old

    def test_words_come_from_the_script_and_their_times_from_whisper(self):
        text = '[softly] Just \u2026 what you found there, twenty five men.'
        toks = core.tokens_of(text)
        self.assertEqual(toks, ['just', 'what', 'you', 'found', 'there', '25', 'men'])
        times = [[1.0, 1.3], [1.5, 1.7], [1.7, 1.8], [1.8, 2.1], [2.1, 2.4], [2.5, 3.1], [3.1, 3.4]]
        ws, prob = cap.line_words(text, times, (1.0, 3.4), core.tokens_of, core.strip_tags, 'en')
        self.assertIsNone(prob)
        self.assertEqual([w['w'] for w in ws], ['Just\u2026', 'what', 'you', 'found', 'there,', 'twenty', 'five', 'men.'])
        self.assertNotIn('[softly]', ' '.join(w['w'] for w in ws))                 # a tag is never captioned
        self.assertEqual((ws[0]['s'], ws[0]['e'], ws[0]['timing']), (1.0, 1.3, 'whisper'))
        tw, fv = ws[5], ws[6]                                                     # one token, '25', over two words
        self.assertEqual((tw['timing'], fv['timing'], tw['s'], fv['e']), ('shared', 'shared', 2.5, 3.1))
        self.assertAlmostEqual(tw['e'], fv['s'])
        # a word Whisper did not time sits between its timed neighbours by its length, and says so
        times[2] = None
        ws, _ = cap.line_words(text, times, (1.0, 3.4), core.tokens_of, core.strip_tags, 'en')
        self.assertEqual((ws[2]['timing'], ws[2]['s'], ws[2]['e']), ('between', 1.7, 1.8))
        # line times describing other words are refused
        self.assertIsNotNone(cap.line_words(text, times[:-1], (1.0, 3.4), core.tokens_of, core.strip_tags, 'en')[1])

    def test_holds_move_the_words_onto_the_edit_timeline(self):
        holds = [{'at_audio_s': 10.0, 'hold_s': 2.5}, {'at_audio_s': 20.0, 'hold_s': 0.3}]
        self.assertEqual([cap.edit_time(t, holds) for t in (9.9, 10.5, 19.9, 25.0)], [9.9, 13.0, 22.4, 27.8])

    def test_the_highlight_lights_only_the_word_being_spoken(self):
        look = cap.look_of('montserrat-highlight')
        words = [W('You', 0.0, 0.18), W('are', 0.2, 0.34), W('twenty', 0.36, 0.7), W('years', 0.72, 1.0), W('old.', 1.02, 1.4),
                 W('Nobody', 2.6, 3.0), W('told', 3.0, 3.0), W('you', 3.0, 3.05), W('why.', 3.6, 4.0)]
        groups = cap.highlight_groups(words, look, lambda s: len(s) * 20, 0.8 * 1920)
        self.assertEqual([[w['w'] for w in g] for g in groups], [['You', 'are', 'twenty', 'years', 'old.'],
                                                                 ['Nobody', 'told', 'you', 'why.']])   # a sentence end
        ms = cap.highlight_moments(groups, 30, look)
        frame = 1 / 30
        for a, b in zip(ms, ms[1:]):
            self.assertLessEqual(a['end'], b['start'] + 1e-9)                         # never two at once
        lit = [m for m in ms if m['active'] is not None]
        self.assertEqual([groups[m['group']][m['active']]['w'] for m in lit],
                         [w['w'] for w in words])                                     # every word, once, in order
        self.assertTrue(all(m['end'] - m['start'] >= 2 * frame - 1e-9 for m in lit))  # zero-length 'told' still lit
        # 'You' ends 0.02 s before 'are': no flash of white; after 'old.' the line stays white, then goes
        self.assertEqual(lit[0]['end'], lit[1]['start'])
        after_old = [m for m in ms if m['group'] == 0 and m['active'] is None]
        self.assertEqual(len(after_old), 1)
        self.assertLessEqual(after_old[0]['end'] - after_old[0]['start'], look['tail_s'] + 1e-6)
        # 'you' ends at 3.05 s, 'why.' starts at 3.6 s: a pause, so every word is white between them
        k = next(i for i, m in enumerate(ms) if m['active'] is not None and groups[m['group']][m['active']]['w'] == 'you')
        self.assertIsNone(ms[k + 1]['active'])
        self.assertAlmostEqual(ms[k + 1]['end'], 3.6, places=5)
        # never lit long after it is spoken
        self.assertLessEqual(lit[4]['end'], 1.4 + frame)
        # the ranges CapCut gets are UTF-16, so a word after an accented one still lands right
        self.assertEqual(cap.utf16_range(['Sí,', 'señor', '\U0001F600x'], 2), [10, 13])

    def test_a_long_stretch_is_cut_into_even_lines_that_fit(self):
        look = cap.look_of('montserrat-highlight')
        words = [W(f'w{i}', i * 0.3, i * 0.3 + 0.25) for i in range(13)]
        groups = cap.highlight_groups(words, look, lambda s: len(s) * 30, 0.8 * 1920)
        self.assertEqual([len(g) for g in groups], [5, 5, 3])                        # 13 words: ceil(13/6)=3 lines
        groups = cap.highlight_groups(words, look, lambda s: len(s) * 120, 0.8 * 1920)
        self.assertTrue(all(len(' '.join(w['w'] for w in g)) * 120 <= 0.8 * 1920 for g in groups))


@unittest.skipUnless(template_draft() and shutil.which('capcut'), 'needs capcut-cli and the CapCut template draft')
class CaptionBuildTests(unittest.TestCase):
    """Real capcut-cli writes into a scratch copy of the template (never the user's store), read back as CapCut opens it."""

    def setUp(self):
        if ct._capcut_running():
            self.skipTest('CapCut is open: capcut-cli refuses to write while it runs')
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name) / 'draft'
        shutil.copytree(template_draft(), self.d)
        words, t = [], 0.4
        script = ('You are twenty years old. You have been in Korea six weeks, and nobody has told you why. '
                  'This is 1950. The ratio is eight to one.')
        for i, w in enumerate(script.split()):
            d = 0.16 + 0.03 * (len(w) % 5)
            words.append(W(w, round(t, 3), round(t + d, 3), f'L{1 + i // 6:03d}'))
            t += d + (0.7 if w.endswith('.') else 0.03)
        self.words = words

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, style, **kw):
        return {'video': 1, 'captions': 'on', 'style': style, 'fps': 30, 'language': 'en', 'words': self.words, **kw}

    def canvas(self, w, h):
        for p in ct._draft_contents(self.d):
            c = json.loads(p.read_text(encoding='utf-8'))
            c.setdefault('canvas_config', {}).update({'width': w, 'height': h})
            p.write_text(json.dumps(c), encoding='utf-8')

    def test_montserrat_highlight_white_text_yellow_spoken_word(self):
        rec = cap.build_draft(self.d, self.plan('montserrat-highlight'), Path(self.tmp.name) / 'work')
        self.assertTrue(rec['ok'], rec)
        self.assertEqual(rec['check']['words_lit'], len(self.words))
        c = json.loads((self.d / 'draft_content.json').read_text(encoding='utf-8'))
        tr = [t for t in c['tracks'] if t.get('name') == cap.HIGHLIGHT_TRACK][0]
        mats = {m['id']: m for m in c['materials']['texts']}
        segs = sorted(tr['segments'], key=lambda s: s['target_timerange']['start'])
        first = mats[segs[0]['material_id']]
        content = json.loads(first['content'])
        self.assertEqual(content['text'], 'You are twenty years old.')                    # the whole line, one text
        fills = [tuple(s['fill']['content']['solid']['color']) for s in content['styles']]
        self.assertEqual(fills, [(1, 1, 0), (1, 1, 1)])                                   # 'You' yellow, the rest white
        self.assertEqual(content['styles'][0]['range'], [0, 3])
        self.assertTrue(first['font_path'].endswith('Montserrat-Bold.otf'))
        self.assertTrue(all(s['font']['path'].endswith('Montserrat-Bold.otf') and s['strokes'] for s in content['styles']))
        self.assertEqual((first['border_color'], first['border_width']), ('#000000', 0.18))
        self.assertFalse(first.get('background_color') and float(first.get('background_alpha') or 0) > 0)   # no box
        # the moments sit exactly on the frame grid the plan made, never overlapping
        starts = [s['target_timerange']['start'] for s in segs]
        self.assertTrue(all(abs(x / 1e6 * 30 - round(x / 1e6 * 30)) < 1e-3 for x in starts))
        for a, b in zip(segs, segs[1:]):
            self.assertLessEqual(a['target_timerange']['start'] + a['target_timerange']['duration'], b['target_timerange']['start'])
        # a pause between two sentences: an all-white moment, no word invented
        whites = [json.loads(mats[s['material_id']]['content']) for s in segs]
        self.assertTrue(any(all(tuple(st['fill']['content']['solid']['color']) == (1, 1, 1) for st in w['styles']) for w in whites))
        # the read-back catches a second yellow word or a wrong font
        st2 = json.loads(mats[segs[1]['material_id']]['content'])
        st2['styles'] = [{**st2['styles'][0], 'fill': {'alpha': 1, 'content': {'render_type': 'solid', 'solid': {'alpha': 1, 'color': [1, 1, 0]}}}}
                         for _ in range(2)]
        st2['styles'][0]['range'], st2['styles'][1]['range'] = [0, 3], [4, 7]
        mats[segs[1]['material_id']]['content'] = json.dumps(st2)
        mats[segs[2]['material_id']]['font_path'] = 'C:/Windows/Fonts/arial.ttf'
        (self.d / 'draft_content.json').write_text(json.dumps(c), encoding='utf-8')
        res = cap.check_draft(self.d, self.plan('montserrat-highlight'))
        self.assertFalse(res['ok'])
        self.assertTrue(any(x.startswith('more_than_one_yellow_word') for x in res['issues']))
        self.assertTrue(any(x.startswith('caption_font_is_not_Montserrat-Bold.otf') for x in res['issues']))

    def test_luckiest_guy_word_box_unchanged_look(self):
        with self.assertRaises(RuntimeError):
            cap.build_draft(self.d, self.plan('luckiest-guy'), Path(self.tmp.name) / 'work')   # no box colour chosen
        rec = cap.build_draft(self.d, self.plan('luckiest-guy', box_color='#E0457B'), Path(self.tmp.name) / 'work')
        self.assertTrue(rec['ok'], rec)
        c = json.loads((self.d / 'draft_content.json').read_text(encoding='utf-8'))
        mats = {m['id']: m for m in c['materials']['texts']}
        names = [t['name'] for t in cap.caption_tracks(c)]
        self.assertTrue(names and all(n.startswith(cap.BOX_TRACK_PREFIX) for n in names))
        self.assertNotIn(cap.HIGHLIGHT_TRACK, names)
        boxed = [mats[s['material_id']] for t in cap.caption_tracks(c) if t['name'].endswith('-box') for s in t['segments']]
        b = boxed[0]
        self.assertEqual((b['background_color'], b['background_round_radius'], b['background_width'], b['background_height'],
                          b['background_vertical_offset'], b['background_style']), ('#E0457B', 0.3, 0.05, 0.05, 0.15, 0))
        self.assertTrue(b['font_path'].endswith('LuckiestGuy-Regular.ttf'))
        self.assertTrue(b['has_shadow'])
        texts = [json.loads(mats[s['material_id']]['content'])['text'] for t in cap.caption_tracks(c) for s in t['segments']]
        self.assertTrue(all(x == x.upper() for x in texts))                               # capitals, one word per text
        self.assertTrue(all(' ' not in x for x in texts))
        self.assertEqual(rec['check']['words_boxed'], len(self.words))
        self.assertFalse(any(json.loads(m['content']).get('styles') and any(tuple(s['fill']['content']['solid']['color']) == (1, 1, 0)
                                                                            for s in json.loads(m['content'])['styles'])
                             for m in mats.values()))                                    # no yellow: not the other look
        # building again needs --replace and gives the same project
        with self.assertRaises(RuntimeError):
            cap.build_draft(self.d, self.plan('luckiest-guy', box_color='#E0457B'), Path(self.tmp.name) / 'work')
        again = cap.build_draft(self.d, self.plan('luckiest-guy', box_color='#E0457B'), Path(self.tmp.name) / 'work', replace=True)
        self.assertEqual((again['texts'], again['tracks']), (rec['texts'], rec['tracks']))

    def test_no_captions_leaves_no_caption_track(self):
        cap.build_draft(self.d, self.plan('montserrat-highlight'), Path(self.tmp.name) / 'work')
        off = {'video': 1, 'captions': 'off', 'style': None}
        self.assertFalse(cap.check_draft(self.d, off)['ok'])
        rec = cap.build_draft(self.d, off, Path(self.tmp.name) / 'work', replace=True)
        self.assertEqual(rec['captions'], 'off')
        self.assertTrue(cap.check_draft(self.d, off)['ok'])
        c = json.loads((self.d / 'draft_content.json').read_text(encoding='utf-8'))
        self.assertFalse(cap.caption_tracks(c))
        self.assertTrue([t for t in c['tracks'] if t.get('type') == 'text'])            # the template's own text stays

    def test_a_portrait_canvas_gets_its_own_size_and_place(self):
        self.canvas(1080, 1920)
        rec = cap.build_draft(self.d, self.plan('montserrat-highlight'), Path(self.tmp.name) / 'work')
        self.assertTrue(rec['ok'], rec)
        self.assertEqual((rec['canvas'], rec['size'], rec['y']), ([1080, 1920], 9.75, -0.5))
        self.assertLessEqual(rec['widest_line_px'], 0.8 * 1080)


class CaptionChoiceAndPlanTests(unittest.TestCase):
    """captions-choice and captions-plan through the command line, on a hand-made run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / 'run'
        (self.run / '40-plans' / 'video-01').mkdir(parents=True)
        (self.run / '50-audio' / 'video-01').mkdir(parents=True)
        (self.run / '70-edit' / 'video-01').mkdir(parents=True)
        core.write_json(self.run / 'state.json', {'schema': core.SCHEMA})
        lines = [{'id': 'L001', 'text': 'You are twenty years old.'},
                 {'id': 'L002', 'text': '[softly] The mountains are still there.', 'pause_after_s': 3, 'pause_via': 'edit',
                  'pause_purpose': 'the last picture stays while the ending settles'}]
        core.write_json(self.run / '40-plans/video-01/script.json', {'language': 'en', 'lines': lines})
        core.write_json(self.run / '40-plans/video-01/length-lock.json', {'language': 'en', 'target_length_s': 10})
        wt1 = [[0.1, 0.25], [0.27, 0.4], [0.42, 0.8], [0.82, 1.1], [1.12, 1.5]]
        wt2 = [[2.2, 2.35], [2.37, 2.9], [2.92, 3.1], [3.12, 3.5], [3.52, 4.0]]
        core.write_json(self.run / '50-audio/video-01/line-times.json',
                        {'complete': True, 'script_sha256': core.script_hash(lines), 'measured_at': 'now',
                         'lines': [{'index': 1, 'id': 'L001', 'start_s': 0.1, 'end_s': 1.5, 'word_times': wt1},
                                   {'index': 2, 'id': 'L002', 'start_s': 2.2, 'end_s': 4.0, 'word_times': wt2}]})
        core.write_json(self.run / '70-edit/video-01/edit-plan.json',
                        {'holds': [{'after_line': 'L001', 'at_audio_s': 1.85, 'hold_s': 3.0}],
                         'narration_for_edit': {'sha256': 'abc'}, 'made_at': 'now'})

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *a, expected=0):
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'static_core.py'), *map(str, a)], capture_output=True,
                           text=True, encoding='utf-8')
        self.assertEqual(r.returncode, expected, r.stdout + r.stderr)
        return json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}

    def test_the_choice_is_asked_once_and_kept(self):
        self.cli('captions-plan', '--run', self.run, '--video', 1, expected=2)              # not chosen: nothing planned
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'montserat', expected=2)   # a typo
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', expected=2)       # on needs its style
        self.cli('captions-choice', '--run', self.run, '--captions', 'off', '--style', 'luckiest-guy', expected=2)
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'montserrat-highlight')
        st = json.loads((self.run / 'state.json').read_text(encoding='utf-8'))
        self.assertEqual((st['captions'], st['caption_style']), ('on', 'montserrat-highlight'))
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'luckiest-guy', expected=2)
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'luckiest-guy',
                 '--change', 'the user asked for the box look after all')
        st = json.loads((self.run / 'state.json').read_text(encoding='utf-8'))
        self.assertEqual((st['caption_style'], st['captions_history'][0]['caption_style']), ('luckiest-guy', 'montserrat-highlight'))

    def test_the_plan_is_the_script_timed_on_the_edit(self):
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'montserrat-highlight')
        out = self.cli('captions-plan', '--run', self.run, '--video', 1)
        plan = json.loads(Path(out['plan']).read_text(encoding='utf-8'))
        self.assertEqual([w['w'] for w in plan['words']], 'You are twenty years old. The mountains are still there.'.split())
        self.assertEqual(plan['words'][0]['s'], 0.1)
        self.assertEqual(plan['words'][5]['s'], 5.2)                  # after the 3 s hold retime-shots put at 1.85 s
        self.assertEqual(plan['timing_evidence']['whisper_share'], 1.0)
        # a later script or a re-cut narration makes the plan stale for the build and the check
        issues, _ = core.captions_plan_facts(self.run, 1)
        self.assertEqual(issues, [])
        ep = json.loads((self.run / '70-edit/video-01/edit-plan.json').read_text(encoding='utf-8'))
        ep['narration_for_edit']['sha256'] = 'other'
        core.write_json(self.run / '70-edit/video-01/edit-plan.json', ep)
        self.assertIn('captions_plan_made_for_an_earlier_edit_narration', core.captions_plan_facts(self.run, 1)[0])
        # the word box needs its colour and why
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'luckiest-guy', '--change',
                 'the user picked the box look')
        self.cli('captions-plan', '--run', self.run, '--video', 1, expected=2)
        self.cli('captions-plan', '--run', self.run, '--video', 1, '--box-color', '#E0457B', '--box-color-why',
                 'the warm red of the flares in the stills, clear against the night blue')
        # captions off: a plan that says so, and nothing to build
        self.cli('captions-choice', '--run', self.run, '--captions', 'off', '--change', 'the user turned captions off')
        out = self.cli('captions-plan', '--run', self.run, '--video', 1)
        self.assertEqual(out['captions'], 'off')

    def test_a_spanish_line_keeps_its_letters(self):
        lines = [{'id': 'L001', 'text': '¿Qué pasó en el embalse? Nadie lo sabía.'}]
        core.write_json(self.run / '40-plans/video-01/script.json', {'language': 'es', 'lines': lines})
        core.write_json(self.run / '40-plans/video-01/length-lock.json', {'language': 'es', 'target_length_s': 10})
        toks = core.tokens_of(lines[0]['text'], 'es')
        wt = [[0.1 + 0.3 * i, 0.35 + 0.3 * i] for i in range(len(toks))]
        core.write_json(self.run / '50-audio/video-01/line-times.json',
                        {'complete': True, 'script_sha256': core.script_hash(lines), 'measured_at': 'now',
                         'lines': [{'index': 1, 'id': 'L001', 'start_s': 0.1, 'end_s': wt[-1][1], 'word_times': wt}]})
        self.cli('captions-choice', '--run', self.run, '--captions', 'on', '--style', 'luckiest-guy')
        out = self.cli('captions-plan', '--run', self.run, '--video', 1, '--box-color', '#3366FF', '--box-color-why',
                       'the cold blue of the reservoir in every still')
        plan = json.loads(Path(out['plan']).read_text(encoding='utf-8'))
        self.assertEqual([w['w'] for w in plan['words']], ['¿Qué', 'pasó', 'en', 'el', 'embalse?', 'Nadie', 'lo', 'sabía.'])
        self.assertEqual(cap._upper_for('pasó'), 'PASÓ')


if __name__ == '__main__':
    unittest.main()
