"""The render record of a drawing (2026-11-24): what a clip was rendered from (the spec's content, its still, the clip,
the renderer), the words and numbers it shows, and whether it is still the render of its spec and its still. Local work
only: tiny renders, no API calls."""
from __future__ import annotations

import collections
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'scripts' / 'draw_tool.py'
HAVE_FFMPEG = shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None


def load_tool():
    spec = importlib.util.spec_from_file_location('draw_tool_render_under_test', TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DT = load_tool()


def cli(*args, expected=0):
    r = subprocess.run([sys.executable, '-B', str(TOOL), *map(str, args)], capture_output=True, text=True, check=False)
    try:
        out = json.loads(r.stdout)
    except ValueError:
        raise AssertionError(f'the CLI reply is not JSON: {r.stdout}\n{r.stderr}')
    if expected is not None:
        assert r.returncode == expected, f'expected exit {expected}, got {r.returncode}: {out}'
    return out


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


LABEL = {'id': 'lab', 'type': 'text', 'at': [0.3, 0.3], 'text': 'MADRID', 'size': 0.12, 'fill': '#2b1d14',
         'in': {'kind': 'typewriter', 'start_s': 0.1, 'dur_s': 0.2},
         'out': {'kind': 'fade', 'start_s': 0.4, 'dur_s': 0.1}}
COUNTER = {'id': 'num', 'type': 'counter', 'at': [0.6, 0.6], 'from': 0, 'to': 315, 'suffix': ' MEN', 'size': 0.12,
           'fill': '#b0302a', 'in': {'start_s': 0.0, 'dur_s': 0.3, 'ease': 'linear'}}


def tiny_spec(**over):
    """A label and a counter on shot S001: five frames at 96x54."""
    spec = {'canvas': '96x54', 'fps': 10, 'dur_s': 0.5, 'shot': 'S001', 'beat': 'B01', 'elements': [LABEL, COUNTER]}
    spec.update(over)
    return json.loads(json.dumps(spec))


def painted(el, t, side=120):
    """The colour a lone element is painted in at t: the commonest colour of its most opaque pixels."""
    spec = {'canvas': f'{side}x{side}', 'fps': 10, 'dur_s': 1.0, 'elements': [el]}
    img = DT.render_frame(spec, spec['elements'], t, int(t * 10), side, side, 1, 1.0, 10)
    data = img.tobytes()
    px = [tuple(data[k:k + 4]) for k in range(0, len(data), 4)]
    top = max(p[3] for p in px)
    return '#%02x%02x%02x' % collections.Counter(p[:3] for p in px if p[3] == top).most_common(1)[0][0]


class SpecFactsTests(unittest.TestCase):
    """spec_facts: a spec's words, numbers and colours, read from the spec alone."""

    def test_the_label_and_the_counter(self):
        f = DT.spec_facts(tiny_spec())
        self.assertEqual([t['text'] for t in f['texts'] if t['type'] != 'counter'], ['MADRID'])
        lab = f['texts'][0]
        self.assertEqual((lab['start_s'], lab['full_s'], lab['out_s'], lab['end_s']), (0.1, 0.3, 0.4, 0.5))
        c, = f['counters']
        self.assertEqual((c['from'], c['to'], c['from_text'], c['to_text']), (0, 315, '0 MEN', '315 MEN'))
        self.assertEqual((c['count_start_s'], c['count_end_s'], c['lands_s'], c['lands_in_clip']),
                         (0.0, 0.3, 0.3, True))
        self.assertEqual(f['colors'], ['#2b1d14', '#b0302a'])
        self.assertEqual((f['shot'], f['beat'], f['problems']), ('S001', 'B01', []))

    def test_times_follow_groups_card_typing_morse_and_the_counter_landing(self):
        spec = {'canvas': '96x54', 'fps': 30, 'dur_s': 4.0, 'elements': [
            {'id': 'n', 'type': 'counter', 'at': [0.5, 0.5], 'from': 0, 'to': 1500, 'suffix': ' MEN',
             'in': {'start_s': 1.0, 'dur_s': 1.0}},
            {'id': 'g', 'type': 'group', 'in': {'kind': 'fade', 'start_s': 2.0, 'dur_s': 0.5},
             'out': {'start_s': 3.0, 'dur_s': 0.2}, 'children': [
                 {'id': 's', 'type': 'stamp', 'at': [0.5, 0.3], 'text': 'NO',
                  'in': {'kind': 'slam', 'start_s': 0.5, 'dur_s': 0.3}}]},
            {'id': 'k', 'type': 'card', 'center': [0.5, 0.5], 'lines': ['AB', 'CD'],
             'in': {'kind': 'drop', 'start_s': 1.0, 'dur_s': 0.4}},
            {'id': 'm', 'type': 'morse', 'at': [0.1, 0.9], 'code': '... --- ...'}]}
        f = DT.spec_facts(spec)
        n, = f['counters']
        self.assertEqual((n['to_text'], n['count_end_s']), ('1,500 MEN', 2.0))
        self.assertLess(n['lands_s'], 1.9)       # the default ease (out3) shows the number well before its window ends
        frame = round(n['lands_s'] * 30)
        self.assertEqual(DT.counter_text(spec['elements'][0], frame / 30), '1,500 MEN')
        self.assertNotEqual(DT.counter_text(spec['elements'][0], (frame - 1) / 30), '1,500 MEN')
        texts = {t['text']: t for t in f['texts']}
        self.assertEqual((texts['NO']['start_s'], texts['NO']['out_s'], texts['NO']['end_s']), (2.0, 3.0, 3.2))
        self.assertEqual((texts['AB']['start_s'], texts['AB']['full_s'], texts['CD']['full_s']), (1.25, 1.55, 1.85))
        self.assertEqual(texts['... --- ...']['decoded'], 'SOS')
        self.assertEqual(texts['1,500 MEN']['type'], 'counter')
        uses = {(u['id'], u['key']): u for u in f['color_uses']}
        self.assertEqual((uses[('s', 'color')]['color'], uses[('s', 'color')]['default']), ('#b0302a', True))
        self.assertEqual(f['problems'], [])

    def test_what_cannot_be_read_is_a_problem_not_an_error(self):
        f = DT.spec_facts({'dur_s': 1, 'elements': [
            {'id': 'n', 'type': 'counter', 'at': [0.5, 0.5], 'to': 'many', 'in': {'start_s': 0, 'dur_s': 0.5}},
            {'id': 'c', 'type': 'rect', 'center': [0.5, 0.5], 'fill': 'red'},
            'not an element']})
        self.assertEqual(f['counters'], [])
        self.assertEqual(len(f['problems']), 3, f['problems'])
        self.assertEqual(DT.spec_facts(['not', 'a', 'spec'])['problems'], ['the spec is not a JSON object'])

    def test_a_default_colour_is_the_colour_the_renderer_paints(self):
        for el, key, t in (({'id': 's', 'type': 'stamp', 'at': [0.5, 0.5], 'text': 'NO', 'size': 0.3, 'grunge': 0},
                            'color', 0.9),
                           ({'id': 'r', 'type': 'redact', 'center': [0.5, 0.5], 'w': 0.6, 'h': 0.2}, 'color', 0.9),
                           ({'id': 'h', 'type': 'highlight', 'center': [0.5, 0.5], 'w': 0.6, 'h': 0.2}, 'stroke', 0.9),
                           ({'id': 'k', 'type': 'card', 'center': [0.5, 0.5], 'w': 0.8, 'h': 0.6}, 'fill', 0.9),
                           ({'id': 'p', 'type': 'pulse', 'center': [0.5, 0.5], 'r_max': 0.3,
                             'in': {'start_s': 0, 'dur_s': 1}}, 'stroke', 0.5)):
            use, = [u for u in DT.spec_facts({'dur_s': 1.0, 'elements': [el]})['color_uses'] if u['key'] == key]
            self.assertTrue(use['default'])
            self.assertEqual(use['color'], painted(el, t), el['type'])

    def test_facts_and_status_import_no_pillow(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'spec.json'
            p.write_text(json.dumps(tiny_spec()), encoding='utf-8')
            code = ('import json, sys; sys.path.insert(0, sys.argv[1]); import draw_tool; '
                    'f = draw_tool.spec_facts(json.load(open(sys.argv[2], encoding="utf-8"))); '
                    's = draw_tool.render_status(sys.argv[2], "missing.mov"); '
                    'print(json.dumps({"pil": sorted(m for m in sys.modules if m.split(".")[0] == "PIL"), '
                    '"texts": [t["text"] for t in f["texts"]], "current": s["current"]}))')
            r = subprocess.run([sys.executable, '-B', '-c', code, str(TOOL.parent), str(p)], capture_output=True,
                               text=True, check=True, cwd=tmp)
        out = json.loads(r.stdout)
        self.assertEqual(out['pil'], [])
        self.assertEqual(out['texts'], ['MADRID', '315 MEN'])
        self.assertFalse(out['current'])


@unittest.skipUnless(HAVE_FFMPEG, 'needs ffmpeg and ffprobe to render')
class RenderRecordTests(unittest.TestCase):
    """A render's record, and render_status read from it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vis = Path(self.tmp.name) / '60-visuals' / 'video-01'
        self.dd = self.vis / 'drawings'
        self.dd.mkdir(parents=True)
        self.still = self.vis / 'stills' / 'S001.png'
        self.still.parent.mkdir()
        self.paint_still((200, 180, 140))
        self.spec_p, self.mov = self.dd / 'D01.json', self.dd / 'D01.mov'
        self.write_spec(tiny_spec())

    def paint_still(self, rgb):
        from PIL import Image
        Image.new('RGB', (96, 54), rgb).save(self.still)

    def write_spec(self, spec, **dump):
        self.spec_p.write_text(json.dumps(spec, **dump), encoding='utf-8')

    def render(self, *extra, expected=0):
        return cli('render', '--spec', self.spec_p, '--out', self.mov, '--supersample', '1', *extra, expected=expected)

    def record(self):
        return json.loads(DT.record_path(self.mov).read_text(encoding='utf-8'))

    def codes(self, still=None, spec=None):
        return [r['code'] for r in DT.render_status(spec or self.spec_p, self.mov, still)['reasons']]

    def test_a_render_writes_a_record_of_what_it_was_rendered_from(self):
        r = self.render()
        rec_p = DT.record_path(self.mov)
        self.assertEqual(rec_p.name, 'D01.render-record.json')
        self.assertEqual(Path(r['record']), rec_p.resolve())
        rec = self.record()
        self.assertEqual(rec['spec_sha256'], DT.spec_sha256(json.loads(self.spec_p.read_text(encoding='utf-8'))))
        self.assertEqual((rec['shot'], rec['beat']), ('S001', 'B01'))
        self.assertEqual((Path(rec['still']), rec['still_from']), (self.still.resolve(), 'shot'))  # as the build does
        self.assertEqual(rec['still_sha256'], sha(self.still))
        self.assertEqual(Path(rec['out']), self.mov.resolve())
        self.assertEqual((rec['out_sha256'], rec['out_bytes']), (sha(self.mov), self.mov.stat().st_size))
        self.assertEqual(rec['tool_sha256'], sha(TOOL))
        made = datetime.datetime.fromisoformat(rec['made_at'])
        self.assertEqual(made.utcoffset(), datetime.timedelta(0))
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc) - made).total_seconds()), 600)
        probe = json.loads(subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries',
             'stream=width,height,nb_read_frames,r_frame_rate:format=duration', '-of', 'json', str(self.mov)],
            capture_output=True, text=True, check=True).stdout)
        st = probe['streams'][0]
        num, den = (int(x) for x in st['r_frame_rate'].split('/'))
        self.assertEqual(rec['size'], [st['width'], st['height']])               # as rendered
        self.assertEqual(rec['frames'], int(st['nb_read_frames']))
        self.assertAlmostEqual(rec['fps'], num / den)
        self.assertAlmostEqual(rec['duration_s'], float(probe['format']['duration']), delta=0.02)
        texts = {t['text']: t for t in rec['texts']}
        self.assertEqual(set(texts), {'MADRID', '315 MEN'})
        lab = texts['MADRID']
        self.assertEqual((lab['start_s'], lab['full_s'], lab['out_s'], lab['end_s']), (0.1, 0.3, 0.4, 0.5))
        c, = rec['counters']
        self.assertEqual((c['from'], c['to'], c['to_text']), (0, 315, '315 MEN'))
        self.assertEqual((c['count_start_s'], c['count_end_s'], c['lands_s']), (0.0, 0.3, 0.3))

    def test_current_right_after_the_render(self):
        self.render()
        for still in (None, self.still):         # the still the record names, and the still the build places it over
            st = DT.render_status(self.spec_p, self.mov, still)
            self.assertTrue(st['current'], st)
            self.assertEqual(st['reasons'], [])

    def test_a_spec_written_again_unchanged_is_no_change_but_new_content_is(self):
        self.render()
        spec = json.loads(self.spec_p.read_text(encoding='utf-8'))
        before = self.spec_p.stat().st_mtime_ns
        self.write_spec(dict(reversed(list(spec.items()))), indent=3)          # other key order and spacing
        os.utime(self.spec_p, ns=(before + 7_000_000_000, before + 7_000_000_000))  # and a new time
        self.assertNotEqual(self.spec_p.stat().st_mtime_ns, before)
        self.assertEqual(self.codes(self.still), [])
        spec['elements'][0]['text'] = 'LISBON'
        self.write_spec(spec)
        st = DT.render_status(self.spec_p, self.mov, self.still)
        self.assertFalse(st['current'])
        self.assertEqual([r['code'] for r in st['reasons']], ['spec_changed'])

    def test_a_still_made_again_makes_the_render_stale(self):
        self.render()
        self.paint_still((10, 20, 30))
        for still in (None, self.still):
            self.assertEqual(self.codes(still), ['still_changed'])

    def test_a_changed_or_missing_clip_and_a_record_of_another_spec(self):
        self.render()
        twin = self.dd / 'D02.json'
        shutil.copyfile(self.spec_p, twin)                   # the same content, another drawing's spec
        self.assertEqual(self.codes(spec=twin), ['record_for_other_spec'])
        data = bytearray(self.mov.read_bytes())
        data[-1] ^= 0xFF                                     # the same size, another clip
        self.mov.write_bytes(bytes(data))
        self.assertEqual(self.codes(), ['mov_changed'])
        self.mov.unlink()
        self.assertEqual(self.codes(), ['mov_missing'])

    def test_a_moved_run_keeps_its_records(self):
        self.render()
        moved = Path(self.tmp.name) / 'clone' / 'video-01'
        shutil.copytree(self.vis, moved)
        st = DT.render_status(moved / 'drawings' / 'D01.json', moved / 'drawings' / 'D01.mov',
                              moved / 'stills' / 'S001.png')
        self.assertTrue(st['current'], st)

    def test_a_given_still_is_recorded_and_checked_by_its_content(self):
        other = self.vis / 'elsewhere.png'
        shutil.copyfile(self.still, other)
        self.render('--still', other)
        rec = self.record()
        self.assertEqual((rec['still_from'], Path(rec['still'])), ('given', other.resolve()))
        st = DT.render_status(self.spec_p, self.mov, self.still)    # placed over the shot's still: the same picture
        self.assertTrue(st['current'], st)
        self.assertTrue(any('the same picture' in n for n in st['notes']), st['notes'])

    def test_a_record_without_a_still_cannot_vouch_for_one(self):
        self.write_spec(tiny_spec(shot=None))
        self.render()
        self.assertIsNone(self.record()['still'])
        self.assertEqual(self.codes(), [])                   # nothing to check
        self.assertEqual(self.codes(self.still), ['still_not_recorded'])

    def test_a_failed_render_leaves_no_record(self):
        self.render()
        rec_p = DT.record_path(self.mov)
        self.assertTrue(rec_p.is_file())
        bad = tiny_spec()
        bad['elements'][1]['to'] = 'many'                    # refused while drawing
        self.write_spec(bad)
        self.assertFalse(self.render(expected=2)['ok'])
        self.assertFalse(rec_p.exists())
        self.assertEqual(self.codes()[0], 'no_record')
        self.write_spec(tiny_spec())
        self.render()
        self.assertTrue(rec_p.is_file())
        self.write_spec(tiny_spec(elements=[{'id': 'x', 'type': 'sparkle'}]))    # refused before drawing
        self.render(expected=2)
        self.assertFalse(rec_p.exists())
        self.assertEqual(list(self.dd.glob('*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
