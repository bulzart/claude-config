"""Smoke tests for the drawn-explanation renderer. Local work only, no API calls."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'scripts' / 'draw_tool.py'


def cli(*args, expected=0):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                            capture_output=True, text=True, check=False)
    try:
        output = json.loads(result.stdout)
    except ValueError:
        raise AssertionError(f'CLI not JSON: {result.stdout}\n{result.stderr}')
    if expected is not None:
        assert result.returncode == expected, f'Expected {expected} got {result.returncode}: {output}'
    return output


class DrawToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)

    def test_check_reports_dependencies(self):
        r = cli('check')
        self.assertTrue(r['ok'])
        self.assertTrue(r['pillow'])
        self.assertTrue(r['ffmpeg'])

    def test_render_produces_alpha_clip_with_correct_timing(self):
        spec = {
            'canvas': '640x360', 'fps': 10, 'dur_s': 1.0,
            'elements': [
                {'id': 'e1', 'type': 'ellipse', 'center': [0.5, 0.5], 'w': 0.1, 'h': 0.1,
                 'fill': '#ff8800', 'in': {'kind': 'grow', 'start_s': 0.0, 'dur_s': 0.3}},
                {'id': 'e2', 'type': 'text', 'at': [0.5, 0.8], 'text': 'HELLO', 'align': 'center',
                 'size': 0.05, 'fill': '#ffffff', 'in': {'kind': 'type', 'start_s': 0.1, 'dur_s': 0.4}},
            ],
        }
        spec_path = self.home / 'spec.json'
        spec_path.write_text(json.dumps(spec), encoding='utf-8')
        out = self.home / 'drawing.mov'
        r = cli('render', '--spec', spec_path, '--out', out)
        self.assertTrue(r['ok'])
        self.assertTrue(out.is_file())
        probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                '-show_entries', 'stream=codec_name,pix_fmt,duration,nb_frames',
                                '-of', 'json', str(out)], capture_output=True, text=True, check=True)
        info = json.loads(probe.stdout)['streams'][0]
        self.assertEqual(info['codec_name'], 'qtrle')
        self.assertIn('a', info['pix_fmt'])  # an alpha-carrying pixel format (e.g. argb)
        self.assertAlmostEqual(float(info['duration']), 1.0, delta=0.05)
        self.assertEqual(int(info['nb_frames']), 10)

    def test_empty_elements_refused(self):
        spec_path = self.home / 'spec.json'
        spec_path.write_text(json.dumps({'canvas': '640x360', 'fps': 10, 'dur_s': 1.0, 'elements': []}),
                             encoding='utf-8')
        r = cli('render', '--spec', spec_path, '--out', self.home / 'x.mov', expected=2)
        self.assertFalse(r['ok'])

    def test_unknown_element_type_refused(self):
        spec = {'canvas': '640x360', 'fps': 10, 'dur_s': 0.2,
                'elements': [{'id': 'bad', 'type': 'sparkle', 'in': {'kind': 'fade', 'start_s': 0, 'dur_s': 0.1}}]}
        spec_path = self.home / 'spec.json'
        spec_path.write_text(json.dumps(spec), encoding='utf-8')
        r = cli('render', '--spec', spec_path, '--out', self.home / 'x.mov', expected=2)
        self.assertFalse(r['ok'])



class DrawFramingTests(unittest.TestCase):
    """A drawing placed on its still follows the still's framing in the edit (2026-11-22)."""

    def test_positions_and_sizes_follow_the_still_scale_and_shift(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('draw_tool_under_test', Path(__file__).resolve().parents[1] / 'scripts' / 'draw_tool.py')
        dt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dt)
        els = [{'id': 'a', 'type': 'line', 'points': [[0.5, 0.5], [0.75, 0.25]]},
               {'id': 'b', 'type': 'rect', 'center': [0.25, 0.75], 'w': 0.1, 'h': 0.05},
               {'id': 'c', 'type': 'text', 'at': [0.6, 0.4], 'size': 0.03}]
        out = dt.apply_framing(els, {'scale': 1.1, 'x': 0.02, 'y': -0.04})
        self.assertEqual(out[0]['points'][0], [0.51, 0.52])                  # the centre moves only by the shift
        self.assertAlmostEqual(out[0]['points'][1][0], 0.5 + 0.01 + 0.25 * 1.1)
        self.assertAlmostEqual(out[1]['w'], 0.11)
        self.assertAlmostEqual(out[2]['size'], 0.033)
        self.assertEqual(els[0]['points'][0], [0.5, 0.5])                    # the spec itself is left as it was
        self.assertIs(dt.apply_framing(els, None), els)
        self.assertIs(dt.apply_framing(els, {'scale': 1.0}), els)

def _dt():
    import importlib.util
    spec = importlib.util.spec_from_file_location('draw_tool_adv', Path(__file__).resolve().parents[1] / 'scripts' / 'draw_tool.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _alpha_box(img):
    return img.getchannel('A').getbbox()


class AdvancedDrawingTests(unittest.TestCase):
    """The advanced engine (user 2026-11-22: "push more advanced drawings and animations in the pipeline")."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.dt = _dt()

    def frame(self, spec, t, ss=1):
        cw, ch = (int(x) for x in spec['canvas'].split('x'))
        return self.dt.render_frame(spec, spec['elements'], t, int(t * spec.get('fps', 10)), cw, ch, ss, spec['dur_s'],
                                    spec.get('fps', 10))

    def test_every_element_type_renders_into_a_clip(self):
        INK = '#2b1d14'
        els = [
            {'id': 'l', 'type': 'arrow', 'points': [[0.1, 0.1], [0.3, 0.2], [0.4, 0.1]], 'smooth': True, 'style': 'ink',
             'stroke': INK, 'width': 4, 'tip': True, 'in': {'kind': 'draw', 'start_s': 0, 'dur_s': 0.5}},
            {'id': 'p', 'type': 'line', 'points': [[0.1, 0.3], [0.4, 0.3]], 'style': 'pencil', 'dash': True, 'march': 20},
            {'id': 'c', 'type': 'line', 'points': [[0.1, 0.35], [0.4, 0.35]], 'style': 'chalk', 'stroke': '#eeeeee'},
            {'id': 'd', 'type': 'line', 'points': [[0.1, 0.4], [0.4, 0.4]], 'dash': 'dot', 'stroke': INK},
            {'id': 'e', 'type': 'ellipse', 'center': [0.5, 0.1], 'w': 0.1, 'h': 0.06, 'stroke': INK, 'style': 'brush'},
            {'id': 'r', 'type': 'rect', 'center': [0.6, 0.1], 'w': 0.1, 'h': 0.06, 'fill': '#ccbb99', 'radius': 0.01},
            {'id': 'g', 'type': 'polygon', 'points': [[0.7, 0.05], [0.8, 0.05], [0.75, 0.15]], 'fill': '#ccbb99'},
            {'id': 't', 'type': 'text', 'at': [0.5, 0.25], 'text': 'TYPED', 'size': 0.05, 'fill': INK,
             'in': {'kind': 'typewriter', 'start_s': 0, 'dur_s': 0.4}, 'plate': {'fill': '#f3ecd9'}},
            {'id': 'h', 'type': 'text', 'at': [0.7, 0.25], 'text': 'here', 'font': 'hand', 'size': 0.06, 'fill': '#b0302a',
             'in': {'kind': 'write', 'start_s': 0, 'dur_s': 0.4}, 'underline': {'color': '#b0302a'}},
            {'id': 'x', 'type': 'text', 'at': [0.5, 0.35], 'text': 'DECODE', 'size': 0.05, 'fill': INK,
             'in': {'kind': 'decode', 'start_s': 0, 'dur_s': 0.6}},
            {'id': 'n', 'type': 'counter', 'at': [0.8, 0.35], 'from': 0, 'to': 315, 'size': 0.05, 'fill': INK,
             'in': {'start_s': 0, 'dur_s': 0.6}},
            {'id': 's', 'type': 'stamp', 'at': [0.5, 0.5], 'text': 'DECEASED', 'size': 0.06, 'rotate': -10,
             'in': {'kind': 'slam', 'start_s': 0.1, 'dur_s': 0.3}, 'shadow': {'alpha': 0.2}},
            {'id': 'k', 'type': 'card', 'center': [0.8, 0.5], 'w': 0.3, 'h': 0.1, 'lines': ['A NAME', 'a role'],
             'pin': True, 'tape': True, 'in': {'kind': 'drop', 'start_s': 0, 'dur_s': 0.4}, 'shadow': True},
            {'id': 'ri', 'type': 'ring', 'center': [0.2, 0.6], 'w': 0.15, 'h': 0.08, 'stroke': '#b0302a',
             'in': {'kind': 'draw', 'start_s': 0, 'dur_s': 0.5}},
            {'id': 'mk', 'type': 'mark', 'kind': 'cross', 'center': [0.35, 0.6], 'size': 0.06, 'stroke': '#b0302a',
             'in': {'kind': 'draw', 'start_s': 0, 'dur_s': 0.4}},
            {'id': 'tk', 'type': 'mark', 'kind': 'tick', 'center': [0.45, 0.6], 'size': 0.06, 'stroke': '#2e6b2e'},
            {'id': 'sc', 'type': 'scribble', 'center': [0.55, 0.6], 'w': 0.08, 'h': 0.05, 'stroke': '#b0302a'},
            {'id': 'hl', 'type': 'highlight', 'center': [0.7, 0.6], 'w': 0.15, 'h': 0.04},
            {'id': 'rd', 'type': 'redact', 'center': [0.85, 0.6], 'w': 0.12, 'h': 0.03,
             'in': {'kind': 'draw', 'start_s': 0, 'dur_s': 0.4}},
            {'id': 'tr', 'type': 'travel', 'points': [[0.1, 0.75], [0.3, 0.7], [0.45, 0.75]], 'icon': 'plane',
             'icon_size': 0.05, 'fill': INK, 'trail': {'dash': [1.5, 1.5]}, 'in': {'start_s': 0, 'dur_s': 0.6},
             'arrive_pulse': True},
            {'id': 'tr2', 'type': 'travel', 'points': [[0.9, 0.75], [0.6, 0.75]], 'icon': 'ship', 'icon_size': 0.05,
             'fill': INK},
            {'id': 'pu', 'type': 'pulse', 'center': [0.5, 0.9], 'r_max': 0.06, 'arc': [-90, 60],
             'in': {'start_s': 0, 'dur_s': 1.0}},
            {'id': 'ha', 'type': 'hatch', 'points': [[0.6, 0.82], [0.75, 0.82], [0.72, 0.95], [0.62, 0.95]],
             'in': {'kind': 'draw', 'start_s': 0, 'dur_s': 0.6}, 'cross': True},
            {'id': 'st', 'type': 'string', 'a': [0.8, 0.85], 'b': [0.95, 0.85], 'in': {'kind': 'draw', 'start_s': 0,
                                                                                         'dur_s': 0.3}},
            {'id': 'pi', 'type': 'pin', 'at': [0.8, 0.85], 'in': {'kind': 'drop', 'start_s': 0, 'dur_s': 0.3}},
            {'id': 'mo', 'type': 'morse', 'at': [0.1, 0.9], 'code': '.-. --', 'times': [0.1, 0.2, 0.3, 0.5, 0.6]},
            {'id': 'gr', 'type': 'group', 'pivot': [0.3, 0.9], 'glow': {'alpha': 0.4},
             'keys': [{'t': 0, 'rot': 0, 'scale': 0.5}, {'t': 0.5, 'rot': 15, 'scale': 1.0, 'ease': 'back'}],
             'children': [{'id': 'g1', 'type': 'rect', 'center': [0.3, 0.9], 'w': 0.05, 'h': 0.05, 'fill': INK}]},
        ]
        spec = {'canvas': '640x360', 'fps': 10, 'dur_s': 1.0, 'elements': els}
        p = self.home / 'all.json'
        p.write_text(json.dumps(spec), encoding='utf-8')
        r = cli('render', '--spec', p, '--out', self.home / 'all.mov', '--supersample', '2')
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['frames'], 10)
        kinds = set(cli('check')['element_types'])
        self.assertTrue({e['type'] for e in els} <= kinds)

    def test_a_drawing_follows_its_still_through_the_move(self):
        el = {'id': 'm', 'type': 'ellipse', 'center': [0.75, 0.25], 'w': 0.04, 'h': 0.04, 'fill': '#000000'}
        spec = {'canvas': '400x400', 'fps': 10, 'dur_s': 2.0, 'elements': [el],
                'still_motion': {'scale': [1.0, 1.2], 'x': [0.0, 0.1], 'y': [0.0, 0.0]}}
        for t, s, x in ((0.0, 1.0, 0.0), (2.0, 1.2, 0.1)):
            box = _alpha_box(self.frame(spec, t))
            cx = (box[0] + box[2]) / 2 / 400
            self.assertAlmostEqual(cx, 0.5 + x / 2 + 0.25 * s, delta=0.01)
        self.assertTrue(self.dt.motion_varies(spec))
        self.assertIsNone(self.dt.frame_state(spec['elements'], 1.0, 10, True))

    def test_words_are_listed_where_the_edit_shows_them(self):
        spec = {'dur_s': 4.0, 'still_motion': {'scale': [1.0, 1.2], 'x': [0, 0], 'y': [0, 0]}, 'elements': [
            {'id': 'n', 'type': 'counter', 'at': [0.5, 0.75], 'from': 0, 'to': 1500, 'suffix': ' MEN', 'size': 0.02,
             'in': {'start_s': 1.0, 'dur_s': 1.0}},
            {'id': 's', 'type': 'stamp', 'at': [0.5, 0.3], 'text': 'INVENTED', 'size': 0.04,
             'in': {'kind': 'slam', 'start_s': 3.5}},
            {'id': 'c', 'type': 'card', 'center': [0.5, 0.5], 'lines': ['A NAME', 'a role'], 'text_size': 0.03}]}
        texts = {w['text']: w for w in self.dt.readable_texts(spec)}
        self.assertEqual(set(texts), {'1,500 MEN', 'INVENTED', 'A NAME', 'a role'})
        self.assertAlmostEqual(texts['1,500 MEN']['size'], 0.024, places=4)
        self.assertEqual(texts['1,500 MEN']['y'], [0.75, 0.8])
        self.assertEqual(texts['INVENTED']['start_s'], 3.5)

    def test_a_still_tail_is_written_once_and_reused(self):
        spec = {'canvas': '320x180', 'fps': 10, 'dur_s': 2.0, 'elements': [
            {'id': 'a', 'type': 'text', 'at': [0.5, 0.5], 'text': 'ONE', 'size': 0.1, 'fill': '#000000',
             'in': {'kind': 'fade', 'start_s': 0.0, 'dur_s': 0.3}}]}
        p = self.home / 'tail.json'
        p.write_text(json.dumps(spec), encoding='utf-8')
        r = cli('render', '--spec', p, '--out', self.home / 'tail.mov', '--supersample', '1')
        self.assertTrue(r['ok'])
        self.assertGreaterEqual(r['frames_reused'], 14)

    def test_a_written_note_ends_fully_written_and_a_counter_counts(self):
        el = {'id': 'w', 'type': 'text', 'at': [0.5, 0.5], 'text': '?', 'font': 'hand', 'size': 0.3, 'fill': '#b0302a',
              'in': {'kind': 'write', 'start_s': 0.0, 'dur_s': 0.2}}
        spec = {'canvas': '300x300', 'fps': 10, 'dur_s': 1.0, 'elements': [el]}
        img = self.frame(spec, 0.5)
        a = img.getchannel('A')
        box = a.getbbox()
        right = a.crop((box[2] - (box[2] - box[0]) // 4, box[1], box[2], box[3]))
        self.assertGreater(right.getextrema()[1], 200)          # the last part of the mark is fully there
        c = {'type': 'counter', 'from': 0, 'to': 500, 'suffix': '+', 'in': {'start_s': 0.0, 'dur_s': 1.0, 'ease': 'linear'}}
        self.assertEqual(self.dt.counter_text(c, 0.5), '250+')
        self.assertEqual(self.dt.counter_text(c, 2.0), '500+')

    def test_a_traveller_arrives_and_morse_marks_light_in_time(self):
        spec = {'canvas': '400x200', 'fps': 10, 'dur_s': 2.0, 'elements': [
            {'id': 't', 'type': 'travel', 'points': [[0.1, 0.5], [0.9, 0.5]], 'icon': 'dot', 'icon_size': 0.1,
             'fill': '#000000', 'in': {'start_s': 0.0, 'dur_s': 0.5}}]}
        box = _alpha_box(self.frame(spec, 1.5))
        self.assertAlmostEqual((box[0] + box[2]) / 2 / 400, 0.9, delta=0.02)
        mo = {'canvas': '400x200', 'fps': 10, 'dur_s': 2.0, 'elements': [
            {'id': 'm', 'type': 'morse', 'at': [0.1, 0.5], 'code': '. .', 'size': 0.05, 'times': [0.2, 1.0]}]}
        one = _alpha_box(self.frame(mo, 0.5))
        two = _alpha_box(self.frame(mo, 1.5))
        self.assertIsNone(_alpha_box(self.frame(mo, 0.1)))
        self.assertLess(one[2], two[2])                          # the second mark only once its time has come

    def test_preview_puts_the_drawing_over_its_still(self):
        from PIL import Image
        still = self.home / 'still.png'
        Image.new('RGB', (640, 360), (200, 180, 140)).save(still)
        spec = {'canvas': '640x360', 'fps': 10, 'dur_s': 1.0, 'still_motion': {'scale': [1.1, 1.2], 'x': [0, 0], 'y': [0, 0]},
                'elements': [{'id': 'x', 'type': 'stamp', 'at': [0.5, 0.5], 'text': 'HELD', 'size': 0.1}]}
        p = self.home / 'p.json'
        p.write_text(json.dumps(spec), encoding='utf-8')
        out = self.home / 'sheet.jpg'
        r = cli('preview', '--spec', p, '--bg', still, '--times', '0.2,0.8', '--out', out, '--width', '320')
        self.assertTrue(r['ok'])
        self.assertTrue(out.is_file())
        self.assertEqual(r['tiles'], 2)

if __name__ == '__main__':
    unittest.main()
