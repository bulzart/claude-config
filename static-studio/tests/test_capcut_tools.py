"""Offline tests of the CapCut toolkit (scripts/capcut_tools.py): no CapCut, no MCP, no network. The writes into a real project were
checked separately in a scratch drafts store with the real MCP server and capcut-cli."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
# the PC's shared lease folder (create-clips' CapCut store coordination) is never written by these tests
import os as _os, tempfile as _tempfile
_os.environ.setdefault("STATIC_GPU_LEASE_DIR", _tempfile.mkdtemp(prefix="capcut-test-leases-"))

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'scripts' / 'capcut_tools.py'


def cli(*args, expected=None):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True, check=False,
                            env={**os.environ, 'STUDIO_HOME': str(ROOT)})
    last = None
    for line in reversed((result.stdout or '').strip().splitlines()):
        if line.strip().startswith('{'):
            last = json.loads(line)
            break
    if expected is not None:
        assert result.returncode == expected, f'expected {expected} got {result.returncode}: {last} {result.stderr[-300:]}'
    return result.returncode, last


def load_module():
    os.environ['STUDIO_HOME'] = str(ROOT)
    spec = importlib.util.spec_from_file_location('capcut_tools_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CapcutToolkitTests(unittest.TestCase):
    def test_help_lists_the_seven_commands(self):
        result = subprocess.run([sys.executable, str(TOOL), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        for name in ('capcut-name', 'capcut-prep', 'capcut-repair', 'capcut-motion', 'capcut-transitions', 'capcut-font', 'capcut-text-anim'):
            self.assertIn(name, result.stdout)

    def test_free_project_names(self):
        with tempfile.TemporaryDirectory() as store:
            _, first = cli('capcut-name', '--video', 3, '--date', '2026-11-19', '--store', store, expected=0)
            self.assertEqual(first['name'], '19_Nov_2026_v03')
            (Path(store) / first['name']).mkdir()
            _, second = cli('capcut-name', '--video', 3, '--date', '2026-11-19', '--store', store, expected=0)
            self.assertEqual(second['name'], '19_Nov_2026_v03-2')
            cli('capcut-name', '--video', 3, '--store', Path(store) / 'missing', expected=2)

    def test_refusals_change_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            not_a_draft = Path(tmp)
            for args in (('capcut-prep', '--draft', not_a_draft), ('capcut-repair', '--draft', not_a_draft)):
                self.assertEqual(cli(*args, expected=2 if args[0] == 'capcut-prep' else None)[0] in (1, 2), True)
            draft = Path(tmp) / 'draft'
            draft.mkdir()
            (draft / 'draft_content.json').write_text('{"id": "x", "name": "draft", "tracks": []}', encoding='utf-8')
            code, res = cli('capcut-motion', '--draft', draft, '--timeline', Path(tmp) / 'no-such-file.json')
            self.assertEqual(code, 2)
            self.assertIn('--timeline', res['error'])
            code, res = cli('capcut-transitions', '--draft', draft, '--timeline', Path(tmp) / 'no-such-file.json')
            self.assertEqual(code, 2)

    def test_catalogue_gate(self):
        mod = load_module()
        cat = json.loads((ROOT / 'data' / 'capcut-catalogue.json').read_text(encoding='utf-8'))
        free = next(x['slug'] for x in cat['transitions'] if x.get('visible_transition') and not x.get('pro'))
        hidden = next(x['slug'] for x in cat['transitions'] if not x.get('visible_transition'))
        pro_intro = next(x['slug'] for x in cat['text_intros'] if x.get('pro'))
        self.assertIsNone(mod._catalogue_refusal('transition', free, False))
        self.assertIn('drew nothing', mod._catalogue_refusal('transition', hidden, False))
        self.assertIn('not in the measured catalogue', mod._catalogue_refusal('transition', 'not-a-real-slug', False))
        self.assertIn('CapCut Pro', mod._catalogue_refusal('intro', pro_intro, False))
        self.assertIsNone(mod._catalogue_refusal('intro', pro_intro, True))
        self.assertFalse(mod._capcut_pro_ok(None), 'this PC has no CapCut Pro')

    def test_the_moves_the_images_file_asks_for(self):
        mod = load_module()
        zoom = mod._still_motion({'motion': 'zoom-in', 'amount': 0.06})
        self.assertEqual(zoom['scale'], [1.0, 1.06])
        pan = mod._still_motion({'motion': 'pan-right', 'amount': 0.05})
        self.assertEqual(pan['scale'], [1.05, 1.05])
        self.assertEqual(pan['x'], [0.049, -0.049])
        self.assertFalse(pan['edge_shows'])
        self.assertEqual(mod._still_motion({'motion': 'zoom-in'})['scale'], [1.0, 1.0], 'no stock amount')
        explicit = mod._still_motion({'scale': [1.0, 1.08], 'x': [0, 0.03], 'y': [0, 0]})
        self.assertEqual(explicit['scale'], [1.0, 1.08])
        self.assertEqual(explicit['x'], [0.0, 0.03])

    def test_the_store_lock_is_the_shared_one(self):
        mod = load_module()
        lock = Path(mod.cfg_get('capcut.store_lock'))
        self.assertEqual(lock.name, '.capcut-store.lock')
        self.assertTrue(lock.parent.is_dir(), 'the lock sits in a folder that exists')


class PhotoDurationTests(unittest.TestCase):
    """capcut-repair's photo-durations step: a still added without a duration gets CapCut's own still duration (2026-11-22)."""

    def test_missing_still_durations_get_capcuts_value_and_nothing_else_changes(self):
        ct = load_module()
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            content = {'materials': {'videos': [
                {'id': 'a', 'type': 'photo', 'duration': None, 'path': 'S001.png'},
                {'id': 'b', 'type': 'photo', 'duration': float('nan'), 'path': 'S002.png'},
                {'id': 'c', 'type': 'photo', 'duration': 10800000000, 'path': 'S003.png'},
                {'id': 'd', 'type': 'video', 'duration': 12533333, 'path': 'D01.mov'}]}, 'tracks': []}
            raw = json.dumps(content).replace('NaN', 'NaN')
            (d / 'draft_content.json').write_text(raw, encoding='utf-8')
            res = ct._photo_durations(d)
            self.assertEqual(res['fixed'], 2)
            back = json.loads((d / 'draft_content.json').read_text(encoding='utf-8'))
            durs = {m['id']: m['duration'] for m in back['materials']['videos']}
            self.assertEqual(durs, {'a': ct.PHOTO_DURATION_US, 'b': ct.PHOTO_DURATION_US, 'c': 10800000000, 'd': 12533333})
            self.assertTrue((d / 'draft_content.json.photo.bak').is_file())
            self.assertEqual(ct._photo_durations(d)['fixed'], 0)       # a second pass finds nothing to do



class AudioMaterialTests(unittest.TestCase):
    """capcut-repair's audio-materials step: an audio clip in CapCut's own form, or CapCut shows the track empty (2026-11-22)."""

    def test_an_unknown_audio_type_becomes_extract_music_named_after_its_file(self):
        ct = load_module()
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            content = {'materials': {'audios': [
                {'id': 'n', 'type': 'audio', 'path': 'C:/run/50-audio/narration-edit.wav', 'material_name': 'narration-edit.wav'},
                {'id': 'm', 'type': 'extract_music', 'path': 'C:/run/music/M1.wav', 'name': 'M1.wav', 'category_name': 'local'},
                {'id': 'u', 'type': 'audio', 'path': 'https://example.org/a.mp3'}]}, 'tracks': []}
            (d / 'draft_content.json').write_text(json.dumps(content), encoding='utf-8')
            res = ct._audio_materials(d)
            back = {m['id']: m for m in json.loads((d / 'draft_content.json').read_text(encoding='utf-8'))['materials']['audios']}
            self.assertEqual((back['n']['type'], back['n']['name'], back['n']['category_name']),
                             ('extract_music', 'narration-edit.wav', 'local'))
            self.assertEqual(back['m'], content['materials']['audios'][1])         # already CapCut's form: untouched
            self.assertEqual(back['u']['type'], 'audio')                            # not a local file: left alone
            self.assertGreater(res['fixed'], 0)
            self.assertEqual(ct._audio_materials(d)['fixed'], 0)                    # a second pass finds nothing to do

if __name__ == '__main__':
    unittest.main()
