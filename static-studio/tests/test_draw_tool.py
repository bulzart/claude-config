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


if __name__ == '__main__':
    unittest.main()
