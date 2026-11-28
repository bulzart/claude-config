"""The director's kit (scripts/director_kit.py): word-anchored time, the drawn parts, still jobs, framing, sound plans.

A small made-up run in a temp folder; nothing is generated, bought or rendered."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import director_kit as dk  # noqa: E402


def put(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding='utf-8')


def make_run(root):
    run = Path(root) / 'run'
    put(run / '40-plans/video-01/script.json', {'lines': [
        {'id': 'L001', 'text': '[quietly] The ground is minus four degrees.'},
        {'id': 'L002', 'text': 'It read one hundred and nineteen of them that day.'}]})
    put(run / '50-audio/video-01/line-times.json', {'lines': [
        {'id': 'L001', 'word_times': [[0.0, 0.2], [0.2, 0.6], [0.6, 0.7], [0.7, 1.0], [1.0, 1.3], [1.3, 1.9]]},
        # the transcript writes "one hundred and nineteen" as one word: seven timed words for ten in the script
        {'id': 'L002', 'word_times': [[2.0, 2.2], [2.2, 2.5], [2.5, 3.3], [3.3, 3.4], [3.4, 3.7], [3.7, 3.9],
                                      [3.9, 4.3]]}]})
    stills = run / '60-visuals/video-01/stills'
    put(run / '60-visuals/video-01/shot-plan.json', {'shots': [
        {'id': 'S001', 'composition': 'place-wide', 'frame_prompt': 'A street.', 'content_note': 'nobody in sight'},
        {'id': 'S002', 'composition': 'section-master', 'frame_prompt': 'A cut.', 'refs': [str(stills / 'S001.png')]},
        {'id': 'S003', 'composition': 'place-wide', 'reuses': 'S001'}]})
    put(run / '60-visuals/video-01/style-lock.json', {'style_prompt': 'Flat ink.'})
    put(run / '70-edit/video-01/edit-plan.json', {
        'holds': [{'at_audio_s': 1.9, 'hold_s': 1.0}], 'edit_duration_s': 8.0,
        'narration_for_edit': {'file': 'narration.mp3'},
        'pauses': [{'after_line': 'L001', 'times_in_edit': {'silence_from_s': 1.9, 'silence_to_s': 2.9,
                                                              'next_line_s': 3.0}}],
        'beats': [{'id': 'B01', 'start_s': 0.0, 'end_s': 2.9}, {'id': 'B02', 'start_s': 2.9, 'end_s': 8.0}],
        'shots': [{'id': 'S001', 'start_s': 0.0, 'end_s': 2.9}, {'id': 'S002', 'start_s': 2.9, 'end_s': 6.0},
                  {'id': 'S003', 'start_s': 6.0, 'end_s': 8.0}]})
    return run


class KitCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.run = make_run(self.tmp)
        self.kit = dk.Kit(self.run, 1)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class WordTime(KitCase):
    def test_a_phrase_before_the_hold_keeps_its_time(self):
        self.assertAlmostEqual(self.kit.word_time(1, 'minus four'), 0.7)
        self.assertAlmostEqual(self.kit.word_time('L001', 'minus four', end=True), 1.3)

    def test_a_hold_moves_what_comes_after_it_on_the_edit_clock_only(self):
        self.assertAlmostEqual(self.kit.word_time(2), 3.0)
        self.assertAlmostEqual(self.kit.word_time(2, clock='narration'), 2.0)

    def test_a_phrase_after_a_spoken_figure_is_counted_from_the_end(self):
        # counted from the start, "that day" would fall on the last timed word; from the end it is found
        self.assertAlmostEqual(self.kit.word_time(2, 'that day', rev=True, clock='narration'), 3.7)
        self.assertAlmostEqual(self.kit.word_time(2, 'that day', rev=True), 4.7)

    def test_a_delivery_tag_is_not_a_word(self):
        self.assertEqual(self.kit.text['L001'][0], 'The')

    def test_a_phrase_the_line_does_not_hold_is_refused(self):
        with self.assertRaises(dk.KitError):
            self.kit.word_time(1, 'plus thirty-five')

    def test_the_pause_and_the_beats_of_a_stretch(self):
        self.assertEqual(self.kit.pause(1)['silence_to_s'], 2.9)
        self.assertEqual(self.kit.beats_of(2.0, 3.5), ['B01', 'B02'])
        with self.assertRaises(dk.KitError):
            self.kit.pause(2)

    def test_the_command_line_answers_with_the_time_inside_a_shot(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = dk.main(['word-time', '--run', str(self.run), '--line', 'L002', '--phrase', 'that day', '--rev',
                            '--shot', 'S002'])
        out = json.loads(buf.getvalue())
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out['edit_s'], 4.7)
        self.assertAlmostEqual(out['in_shot_s'], 1.8)


class OverlayParts(KitCase):
    def overlay(self, **kw):
        return dk.Overlay(self.kit, 'S002', **kw)

    def test_a_mark_is_timed_on_its_word_and_kept_inside_the_clip(self):
        d = self.overlay()
        self.assertAlmostEqual(d.at(2, 'that day', rev=True), 1.8)
        self.assertAlmostEqual(d.at(2, 'that day', rev=True, lead=9.0), 0.05)

    def test_a_value_that_stands_from_the_cut_has_no_entrance_and_no_hyphen(self):
        d = self.overlay(value_color=lambda v: '#1F5FA8' if v.startswith('-') else '#F08A1C')
        d.readout([0.7, 0.4], [(0, '-4 °C'), (1.2, '+35 °C')], pin=[0.5, 0.6])
        cards = [e for e in d.el if e['type'] == 'card']
        self.assertEqual(cards[0]['in'], {'kind': 'fade', 'start_s': 0, 'dur_s': 0.03})
        self.assertEqual(cards[0]['lines'], ['–4 °C'])
        self.assertEqual(cards[0]['text_color'], '#1F5FA8')
        self.assertEqual(cards[1]['in']['kind'], 'flip')
        self.assertEqual(cards[1]['text_color'], '#F08A1C')

    def test_a_counted_mark_is_bold_and_can_let_go(self):
        d = self.overlay()
        d.grip(0.5, 0.2, 0.8, 0.3, open_={4: 1.5}, color='#F2EDE2')
        marks = [e for e in d.el if e['id'].startswith('grip')]
        self.assertEqual(len(marks), 10)                       # five marks, each a dark edge under a colour
        self.assertGreaterEqual(min(e['width'] for e in marks), 17.0)
        self.assertEqual([e['out']['kind'] for e in marks if e['id'].startswith('grip4')], ['undraw', 'undraw'])

    def test_with_no_palette_every_mark_is_ink(self):
        d = self.overlay()
        d.cross([0.5, 0.5], 0.2)
        d.bar(0.5, 0.8, 0.05, 2, 0.2)
        self.assertEqual({e.get('stroke', e.get('fill')) for e in d.el if e['type'] == 'mark'}, {'#141414'})
        self.assertEqual({e['fill'] for e in d.el if e['type'] == 'rect'}, {'#141414'})

    def test_the_spec_carries_the_stills_own_move(self):
        put(self.run / '70-edit/video-01/capcut-images.json',
            {'images': [{'shot_id': 'S002', 'scale': [1.1, 1.12], 'x': [0.0, 0.0], 'y': [0.1, 0.1]}]})
        spec = self.overlay().spec()
        self.assertEqual(spec['still_motion'], {'scale': [1.1, 1.12], 'x': [0.0, 0.0], 'y': [0.1, 0.1]})
        self.assertEqual((spec['canvas'], spec['dur_s'], spec['shot']), ('1920x1080', 3.1, 'S002'))

    def test_every_part_is_a_spec_the_drawing_tool_accepts(self):
        d = self.overlay(palette={'main': '#1F5FA8', 'alert': '#F08A1C', 'light': '#A9C8E6'})
        d.tag([0.3, 0.2], 'January', 0.2)
        d.word([0.5, 0.3], 'DRY', 0.4)
        d.hand([0.6, 0.3], 'really?', 0.5)
        d.q([0.8, 0.3], 0.6)
        d.readout([0.7, 0.5], [(0, '-4 °C'), (1.0, '+35 °C')], pin=[0.5, 0.6])
        d.tick([0.2, 0.5], 0.7)
        d.cross([0.25, 0.5], 0.8)
        d.ring([0.4, 0.5], 0.1, 0.1, 0.9)
        d.arrow([[0.1, 0.1], [0.2, 0.2]], 1.0)
        d.line([[0.1, 0.7], [0.4, 0.7]], 1.1)
        d.bracket(0.9, 0.3, 0.6, 1.2, label='10 m')
        d.grip(0.5, 0.2, 0.8, 0.3, open_={4: 1.5})
        d.panel([0.5, 0.5], 0.3, 0.2, 0.1)
        d.bar(0.3, 0.8, 0.04, 3, 1.3, label='CAN HOLD', lose={2: 2.0})
        d.strip(0.1, 0.9, 0.9, 1.4, 2.4)
        d.scale(0.08, 0.3, 0.8, 0.2, marks=[(0.5, '10 m', 0.6)])
        d.wind(0.1, 0.9, 0.4, 0.45, 0.5)
        d.stamp([0.5, 0.6], 'NOT ASSURED', 2.0)
        d.dots([[0.1 + 0.01 * i, 0.9] for i in range(30)], 0.5, 1.0)
        spec = Path(self.tmp) / 'spec.json'
        put(spec, d.spec())
        sheet = Path(self.tmp) / 'sheet.jpg'
        for args in (['texts', '--spec', str(spec)],
                     ['preview', '--spec', str(spec), '--out', str(sheet), '--times', '1.0,2.9', '--width', '240',
                      '--grid']):                              # the renderer itself draws every part, twice
            r = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPTS / 'draw_tool.py'), *args],
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
            self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-800:])
        self.assertTrue(sheet.is_file())

    def test_a_shot_that_is_not_in_the_edit_is_refused(self):
        with self.assertRaises(dk.KitError):
            dk.Overlay(self.kit, 'S099')

    def test_drawings_are_named_in_shot_order(self):
        dr = dk.Drawings(self.kit)

        @dr.draw('S003')
        def _(d):
            d.tag([0.5, 0.2], 'later', 0.2)

        @dr.draw('S001')
        def _(d):
            d.tag([0.5, 0.2], 'first', 0.2)
        self.assertEqual([(n, s) for n, s, _d in dr.build()], [('D01', 'S001'), ('D02', 'S003')])
        self.assertEqual(dr.write(), 2)
        self.assertEqual(json.loads((self.kit.vis / 'drawings' / 'D02.json').read_text(encoding='utf-8'))['shot'],
                         'S003')


class StillJobs(KitCase):
    def test_one_job_per_still_with_the_look_and_a_diagram_drawn_direct(self):
        st = dk.Stills(self.kit, python_cmd='none.cmd', root='none')
        self.assertEqual(st.write_jobs(), 2)                   # S003 returns to S001: no still of its own
        a = json.loads((self.kit.vis / 'jobs' / 'still-S001.json').read_text(encoding='utf-8'))
        b = json.loads((self.kit.vis / 'jobs' / 'still-S002.json').read_text(encoding='utf-8'))
        self.assertEqual((a['op'], a['purpose'], len(a['images'])), ('generate', 'shots', 1))
        self.assertEqual(a['images'][0]['prompt'], 'A street. Flat ink.')
        self.assertEqual(a['images'][0]['content_note'], 'nobody in sight')
        self.assertTrue(a['images'][0]['upsample'])
        self.assertFalse(b['images'][0]['upsample'])           # a section is drawn straight from its prompt
        self.assertEqual(b['images'][0]['refs'], [str(self.kit.vis / 'stills' / 'S001.png')])
        self.assertNotEqual(a['images'][0]['seed'], b['images'][0]['seed'])

    def test_overrides_reach_one_still_or_every_job(self):
        put(self.kit.vis / 'jobs' / 'overrides.json', {'S002': {'seed': 11, 'upsample': True},
                                                       '_job': {'reserve_vram_gb': 8}})
        dk.Stills(self.kit, python_cmd='none.cmd', root='none').write_jobs()
        b = json.loads((self.kit.vis / 'jobs' / 'still-S002.json').read_text(encoding='utf-8'))
        self.assertEqual((b['images'][0]['seed'], b['images'][0]['upsample'], b['reserve_vram_gb']), (11, True, 8))

    def test_a_still_waits_for_the_still_it_is_made_from(self):
        st = dk.Stills(self.kit, python_cmd='none.cmd', root='none')
        self.assertEqual(st.todo(), ['S001', 'S002'])
        (self.kit.vis / 'stills').mkdir(parents=True, exist_ok=True)
        (self.kit.vis / 'stills' / 'S001.png').write_bytes(b'x')
        self.assertEqual(st.todo(), ['S002'])
        self.assertEqual(st.status(), (['S001'], ['S002']))

    def test_a_still_without_a_job_file_is_refused(self):
        with self.assertRaises(dk.KitError):
            dk.Stills(self.kit, python_cmd='none.cmd', root='none').run_one('S001')


class FramingRows(KitCase):
    def picture(self, border=0, line=False, pale_top=0):
        from PIL import Image, ImageDraw
        im = Image.new('RGB', (1920, 1088), (120, 130, 140))
        d = ImageDraw.Draw(im)
        if border:
            for box in ((0, 0, 1919, border - 1), (0, 1088 - border, 1919, 1087), (0, 0, border - 1, 1087),
                        (1920 - border, 0, 1919, 1087)):
                d.rectangle(box, fill=(242, 237, 226))
            if line:
                d.rectangle((border, border, 1919 - border, 1087 - border), outline=(20, 20, 20), width=2)
        if pale_top:
            d.rectangle((0, 0, 1919, pale_top - 1), fill=(240, 240, 240))
        return im

    def test_a_paper_border_and_its_frame_line_are_measured(self):
        self.assertEqual(dk.margin(self.picture(border=12), 'top'), 12)
        self.assertEqual(dk.margin(self.picture(border=12, line=True), 'left'), 16)
        self.assertEqual(dk.margin(self.picture(), 'bottom'), 0)

    def test_a_deep_pale_edge_is_the_picture_not_a_margin(self):
        self.assertEqual(dk.margin(self.picture(pale_top=140), 'top'), 0)       # snow, a pale sky

    def test_the_y_that_puts_a_band_under_the_frame(self):
        self.assertAlmostEqual(dk.hide_band_y(0.75, 1.36), -0.32)
        self.assertAlmostEqual(dk.hide_band_y(0.6, 1.1), -0.1)                  # never past the picture's own edge

    def test_a_family_shares_one_framing_a_variant_dissolves_and_a_hand_setting_wins(self):
        fr = dk.Framing(self.kit, overrides={'S003': {'scale': [1.2, 1.2], 'x': [0.0, 0.0], 'y': [-0.1, -0.1]}})
        crop = {'S001': {'min_scale': 1.06}, 'S002': {'min_scale': 1.02}}
        rows = fr.rows(crop, lambda i: dk.held(i) if i['has_drawing'] else dk.breathe(i, 0.02), drawn={'S002'})
        self.assertEqual(rows[0]['scale'], [1.06, 1.08])
        self.assertEqual((rows[1]['scale'], rows[1]['kind']), ([1.06, 1.06], 'held'))   # the family's largest need
        self.assertEqual((rows[1].get('transition'), rows[1].get('trans_s')), ('mix', 0.5))
        self.assertEqual((rows[2]['kind'], rows[2]['y']), ('set by hand', [-0.1, -0.1]))
        self.assertEqual([r['image'] for r in rows], [1, 2, 3])
        fr.write(crop, rows)
        self.assertEqual(self.kit.frame_of('S001'), {'scale': [1.06, 1.08], 'x': [0.0, 0.0], 'y': [0.0, 0.0]})


class SoundPlan(KitCase):
    def test_a_cue_is_placed_on_a_word_and_one_copy_is_baked_per_file_and_level(self):
        so = dk.Sound(self.kit)
        so.bed('wind', 'wind.wav', 0.0, so.S('S002'), 20, 'the open street', kind='ambience',
               lift={'by_db': 6, 'why': 'alone in the silence', 'moments': [[1.9, 2.9]]})
        so.fx('flip-1', 'flip.mp3', so.W(2, 'that day', rev=True), 11, 'the read-out flips')
        so.fx('flip-2', 'flip.mp3', 6.0, 11, 'it flips again')
        so.fx('flip-3', 'flip.mp3', 7.0, 6, 'and louder', dur=0.5, fade_out=0.1)
        beds, sfx = so.plan_docs()
        self.assertEqual(beds['narration'], 'narration.mp3')
        self.assertEqual((beds['tracks'][0]['dur'], beds['tracks'][0]['under_speech_db']), (2.9, 20))
        self.assertIn('lift', beds['tracks'][0])
        self.assertEqual([t['id'] for t in sfx['tracks']], ['flip-1', 'flip-3'])
        self.assertEqual([f['baked_as'] for f in so.sounds], ['flip-1', 'flip-1', 'flip-3'])
        self.assertEqual(so.sounds[0]['at'], 4.7)
        self.assertEqual(Path(so.sounds[0]['file']), self.kit.sfx / 'flip.mp3')
        so.plans()
        self.assertTrue((self.kit.edit / 'bed-plan.json').is_file() and (self.kit.edit / 'sfx-plan.json').is_file())


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg is not installed')
class HeldTone(unittest.TestCase):
    def test_the_synthesised_tone_can_be_played_by_a_small_speaker(self):
        import audio_review as ar
        tmp = tempfile.mkdtemp()
        try:
            f = Path(tmp) / 'tone.wav'
            self.assertAlmostEqual(dk.tone(f, 6), 6.0, places=1)
            self.assertGreater(ar.small_speaker_share(f), ar.SMALL_SPEAKER_SHARE)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
