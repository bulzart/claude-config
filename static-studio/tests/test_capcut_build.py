"""capcut-build (scripts/capcut_tools.py with scripts/capcut_build.mjs): the whole CapCut project of one video from the run's
decided files. The plan tests use a small fixture run made in a temp folder, never a real run. The build test writes into a
scratch copy of the CapCut template (copied read only, never the user's drafts folder) through the CapCut MCP's own library; it
is skipped when node, core.js, ffmpeg or the template is missing, or CapCut is open. No CapCut window, no network."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import types
import unittest
# the PC's shared lease folder (create-clips' CapCut store coordination) is never written by these tests
import os as _os, tempfile as _tempfile
_os.environ.setdefault("STATIC_GPU_LEASE_DIR", _tempfile.mkdtemp(prefix="capcut-test-leases-"))
import wave

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'scripts' / 'capcut_tools.py'
STATIC_CORE = ROOT / 'scripts' / 'static_core.py'
CFG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8')).get('capcut') or {}
CORE_JS = Path(str(CFG.get('mcp_core') or ''))
HAVE_FFPROBE, HAVE_FFMPEG, HAVE_NODE = (bool(shutil.which(x)) for x in ('ffprobe', 'ffmpeg', 'node'))


def cli(*args, tool=TOOL):
    r = subprocess.run([sys.executable, '-B', str(tool), *map(str, args)], capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env={**os.environ, 'STUDIO_HOME': str(ROOT)}, timeout=1800)
    last = None
    for line in reversed((r.stdout or '').strip().splitlines()):
        if line.strip().startswith('{'):
            try:
                last = json.loads(line)
            except ValueError:
                continue
            break
    if last is None:                     # static_core.py prints its answer indented, over several lines
        try:
            last = json.loads(r.stdout)
        except ValueError:
            pass
    return r.returncode, last, r


def load_module():
    os.environ['STUDIO_HOME'] = str(ROOT)
    spec = importlib.util.spec_from_file_location('capcut_tools_build_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pkey(p):
    return os.path.normcase(str(Path(p).resolve()))


def template_draft():
    """The empty template every project is cloned from, in the real drafts folder: only ever read (copied), never written."""
    t = Path(CFG.get('drafts_dir') or '') / (CFG.get('template_draft') or '')
    return t if (t / 'draft_content.json').is_file() else None


def write_wav(p, seconds, rate=16000):
    p.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(seconds * rate))
    with wave.open(str(p), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h', int(2000 * math.sin(2 * math.pi * 330 * i / rate))) for i in range(n)))


def write_png(p, rgb):
    from PIL import Image
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (64, 36), rgb).save(p)


def write_mov(p, seconds):
    """A transparent clip like draw_tool's (QuickTime Animation with alpha), made by ffmpeg."""
    p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                    f'color=c=black@0.0:s=64x36:r=30:d={seconds}', '-vf', 'format=argb', '-c:v', 'qtrle', str(p)],
                   check=True, capture_output=True)


def make_run(root: Path, drawings=True) -> Path:
    """A small run, decided through to the edit: three shots over 6 s (the third a callback showing the first one's still),
    two beats, one held silence the bed goes on under, a bed and a sound effect, a zoom, a pan and a join, and a drawing on
    the second shot."""
    rd = root / '20990101-000000-build'
    edit, vis = rd / '70-edit' / 'video-01', rd / '60-visuals' / 'video-01'
    edit.mkdir(parents=True)
    vis.mkdir(parents=True)
    (rd / 'state.json').write_text(json.dumps({'schema': 'static-youtube-longform-v1', 'captions': 'off',
                                               'capcut_plan': 'free'}), encoding='utf-8')
    narr = rd / '50-audio' / 'video-01' / 'narration-edit.wav'
    write_wav(narr, 6.0)
    shots = [('S001', 'B01', 0.0, 2.0), ('S002', 'B01', 2.0, 4.1), ('S003', 'B02', 4.1, 6.0)]
    plan = {'video': 1, 'edit_duration_s': 6.0, 'made_at': '2026-11-24T10:00:00+00:00',
            'narration_for_edit': {'file': str(narr), 'sha256': sha(narr), 'duration_s': 6.0},
            'beats': [{'id': 'B01', 'start_s': 0.0, 'end_s': 4.1}, {'id': 'B02', 'start_s': 4.1, 'end_s': 6.0}],
            'shots': [{'id': i, 'beat_id': b, 'start_s': s, 'end_s': e, 'duration_s': round(e - s, 3)} for i, b, s, e in shots],
            'pauses': [{'after_line': 'L002', 'transition': {'bed': 'continues'},
                        'times_in_edit': {'silence_from_s': 3.4, 'silence_to_s': 4.1, 'next_line_s': 4.1}}]}
    (edit / 'edit-plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
    (vis / 'shot-plan.json').write_text(json.dumps({'shots': [
        {'id': 'S001', 'beat_id': 'B01', 'new_thing': 'the house'}, {'id': 'S002', 'beat_id': 'B01', 'new_thing': 'the message'},
        {'id': 'S003', 'beat_id': 'B02', 'reuses': 'S001', 'new_thing': 'the house again'}]}), encoding='utf-8')
    prov = {}
    for sid, rgb in (('S001', (200, 30, 30)), ('S002', (30, 200, 30))):
        f = vis / 'stills' / f'{sid}.png'
        write_png(f, rgb)
        prov[pkey(f)] = {'shot_id': sid, 'beat_id': 'B01', 'file_sha256': sha(f), 'made_at': '2026-11-24T09:00:00+00:00'}
    (vis / 'stills-provenance.json').write_text(json.dumps({'video': 1, 'images': prov}), encoding='utf-8')
    (edit / 'capcut-images.json').write_text(json.dumps({'fps': 30, 'images': [
        {'image': 1, 'start': 0.0, 'shot_id': 'S001', 'motion': 'zoom-in', 'amount': 0.05},
        {'image': 2, 'start': 2.0, 'shot_id': 'S002', 'motion': 'none', 'transition': 'mix', 'trans_s': 0.5},
        {'image': 3, 'start': 4.1, 'shot_id': 'S003', 'motion': 'pan-right', 'amount': 0.04}]}), encoding='utf-8')
    bed = edit / 'music' / 'M1.wav'
    write_wav(bed, 3.0)
    (edit / 'music-provenance.json').write_text(json.dumps({'video': 1, 'tracks': {
        pkey(bed): {'beats': ['B01'], 'production_rev': 1, 'made_at': '2026-11-24T09:30:00+00:00'}}}), encoding='utf-8')
    tick = rd / '50-audio' / 'sfx' / 'video-01' / 'tick.wav'
    write_wav(tick, 0.5)
    (edit / 'sound-placements.json').write_text(json.dumps({
        'beds': [{'id': 'M1', 'file': '70-edit/video-01/music/M1.wav', 'at': 1.5, 'beats': ['B01'], 'why': 'under the build-up'}],
        'sfx': [{'id': 'tick', 'file': str(tick), 'at': 4.3, 'beats': ['B02'], 'purpose': 'a tick on the turn'}]}), encoding='utf-8')
    if drawings:
        dd = vis / 'drawings'
        dd.mkdir()
        (dd / 'D01.json').write_text(json.dumps({'canvas': '1920x1080', 'fps': 30, 'dur_s': 2.1, 'shot': 'S002', 'elements': [
            {'type': 'line', 'points': [[0.2, 0.2], [0.8, 0.8]], 'stroke': '#ffffff', 'width': 0.01,
             'in': {'kind': 'draw', 'start_s': 0.2, 'dur_s': 0.6}}]}), encoding='utf-8')
        write_mov(dd / 'D01.mov', 2.1)
        if HAVE_FFMPEG:
            draw_record(dd)
        (dd / 'placements.json').write_text('{"D01": {"note": "a working file, not a spec"}}', encoding='utf-8')
    return rd


def draw_record(dd, name='D01', seconds=2.1):
    """The render record draw_tool.py writes after a render, for a clip made here with ffmpeg (no renderer run)."""
    spec_ = importlib.util.spec_from_file_location('draw_tool_for_records', ROOT / 'scripts' / 'draw_tool.py')
    dt = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(dt)
    sp = Path(dd) / f'{name}.json'
    spec = json.loads(sp.read_text(encoding='utf-8'))
    still, how = dt.spec_still(spec, sp)
    dt.write_record(spec, sp, Path(dd) / f'{name}.mov', dt.spec_sha256(spec), dt.tool_sha256(), still, how,
                    dt._sha_or_none(still), (1920, 1080), 30.0, int(round(seconds * 30)), seconds, 1)


def edit_json(p, fn):
    data = json.loads(Path(p).read_text(encoding='utf-8'))
    fn(data)
    Path(p).write_text(json.dumps(data), encoding='utf-8')


def fake_draft(store: Path, name='24_Nov_2099_v01', content_name=None, **change):
    """A fresh, prepared clone as capcut-prep leaves it (enough for the draft checks; not a draft CapCut could open), with the
    template folder beside it."""
    (store / str(CFG.get('template_draft') or '_template')).mkdir(parents=True, exist_ok=True)
    (store / str(CFG.get('template_draft') or '_template') / 'draft_content.json').write_text('{}', encoding='utf-8')
    d = store / name
    d.mkdir(parents=True, exist_ok=True)
    content = {'id': 'T-1', 'name': content_name or name, 'tracks': [{'type': 'video', 'segments': []}, {'type': 'audio', 'segments': []}],
               'canvas_config': {'width': 1920, 'height': 1080}}
    content.update(change)
    (d / 'draft_content.json').write_text(json.dumps(content), encoding='utf-8')
    (d / 'timeline_layout.json').write_text(json.dumps({'dockItems': [{'timelineIds': ['T-1']}]}), encoding='utf-8')
    return d


@unittest.skipUnless(HAVE_FFPROBE, 'needs ffprobe')
class BuildPlanTests(unittest.TestCase):
    """The plan: every clip from the run's decided files, at its decided time, refused when an input is missing or changed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rd = make_run(self.root, drawings=HAVE_FFMPEG)
        self.edit = self.rd / '70-edit' / 'video-01'
        self.vis = self.rd / '60-visuals' / 'video-01'
        self.plan_file = self.edit / 'capcut' / 'build-plan.json'

    def tearDown(self):
        self.tmp.cleanup()

    def dry(self, *extra):
        return cli('capcut-build', '--run', self.rd, '--video', 1, '--dry-run', *extra)

    def refused(self, needle, *extra):
        code, res, r = self.dry(*extra)
        self.assertEqual(code, 2, (res, r.stderr[-400:]))
        self.assertIn(needle, ' | '.join(res.get('problems') or []))
        self.assertFalse(self.plan_file.exists(), 'a refused build writes nothing')
        self.assertFalse((self.edit / 'capcut' / 'build-log.json').exists())
        return res

    def test_the_plan_places_every_clip_from_the_decided_files(self):
        code, res, r = self.dry()
        self.assertEqual(code, 0, (res, r.stderr[-500:]))
        self.assertEqual(res['warnings'], [])
        plan = json.loads(self.plan_file.read_text(encoding='utf-8'))
        self.assertEqual([(i['shot_id'], Path(i['file']).name, i['at_us'], i['dur_us']) for i in plan['images']],
                         [('S001', 'S001.png', 0, 2000000), ('S002', 'S002.png', 2000000, 2100000),
                          ('S003', 'S001.png', 4100000, 1900000)])          # the callback shows the still it reuses
        n = plan['narration']
        self.assertEqual((n['at_us'], n['src_start_us'], n['speed'], n['volume']), (0, 0, 1.0, 1.0))
        self.assertAlmostEqual(n['dur_us'], 6000000, delta=1000)            # whole: the file's own length
        ep = json.loads((self.edit / 'edit-plan.json').read_text(encoding='utf-8'))
        self.assertEqual(n['sha256'], ep['narration_for_edit']['sha256'])
        self.assertEqual([(b['id'], b['track'], b['at_us'], b['dur_us'], b['recorded_music']) for b in plan['beds']],
                         [('M1', 'music', 1500000, 3000000, True)])
        self.assertEqual([(s['id'], s['track'], s['at_us'], s['dur_us']) for s in plan['sfx']], [('tick', 'sfx', 4300000, 500000)])
        if HAVE_FFMPEG:
            self.assertEqual([(o['id'], o['shot_id'], o['track'], o['at_us'], o['dur_us']) for o in plan['overlays']],
                             [('D01', 'S002', 'draw1', 2000000, 2100000)])
        self.assertEqual((plan['moves']['rows'], plan['moves']['moved']), (3, 2))
        self.assertEqual([(t['into_image'], t['into_shot'], t['transition']) for t in plan['moves']['transitions']], [(2, 'S002', 'mix')])
        self.assertEqual([h['as_decided'] for h in plan['held_silences']], [True])
        self.assertEqual(json.loads((self.edit / 'capcut' / 'sounds.json').read_text(encoding='utf-8')),
                         {'tick.wav': {'kind': 'sfx', 'beats': ['B02'], 'purpose': 'a tick on the turn'}})  # M1 is a recorded bed
        roles = {i['role'] for i in plan['inputs']}
        self.assertTrue({'edit_plan', 'narration', 'still', 'images_file', 'sound_placements', 'bed', 'sfx'} <= roles, roles)
        self.assertFalse((self.edit / 'capcut' / 'build-log.json').exists(), 'a dry run builds nothing')

    def test_explicit_opt_outs(self):
        code, res, r = self.dry('--no-moves', '--no-sounds', '--no-drawings')
        self.assertEqual(code, 0, (res, r.stderr[-400:]))
        plan = json.loads(self.plan_file.read_text(encoding='utf-8'))
        self.assertEqual((plan['moves'], plan['beds'], plan['sfx'], plan['overlays']), (None, [], [], []))
        joined = ' | '.join(plan['warnings'])
        for needle in ('--no-moves', '--no-sounds', 'music was made for this video'):
            self.assertIn(needle, joined)
        self.plan_file.unlink()
        self.refused('contradict', '--no-moves', '--images', self.edit / 'capcut-images.json')

    def test_an_input_missing_refuses(self):
        (self.edit / 'capcut-images.json').unlink()
        self.refused('no images file')

    def test_no_sound_placements_refuses(self):
        (self.edit / 'sound-placements.json').unlink()
        self.refused('no sound placements file')

    def test_no_edit_plan_refuses(self):
        (self.edit / 'edit-plan.json').unlink()
        self.refused('no readable edit plan')

    def test_a_changed_narration_refuses(self):
        p = self.rd / '50-audio' / 'video-01' / 'narration-edit.wav'
        p.write_bytes(p.read_bytes() + b'\x00\x00')
        self.refused('changed since retime-shots')

    def test_a_missing_still_refuses(self):
        (self.vis / 'stills' / 'S002.png').unlink()
        self.refused('S002: its still')

    def test_a_still_changed_after_it_was_made_refuses(self):
        write_png(self.vis / 'stills' / 'S002.png', (0, 0, 255))
        self.refused('changed after the generator made it')

    def test_a_still_recorded_for_another_shot_refuses(self):
        edit_json(self.vis / 'stills-provenance.json',
                  lambda d: d['images'][pkey(self.vis / 'stills' / 'S002.png')].update({'shot_id': 'S009'}))
        self.refused('was made for shot S009')

    def test_an_images_file_for_another_timing_refuses(self):
        edit_json(self.edit / 'capcut-images.json', lambda d: d['images'][1].update({'start': 2.5}))
        self.refused('written for another timing')

    def test_a_join_needs_the_row_before_it(self):
        edit_json(self.edit / 'capcut-images.json', lambda d: d['images'].pop(0))
        self.refused('needs the row of image 1')

    def test_a_join_outside_the_measured_catalogue_refuses(self):
        edit_json(self.edit / 'capcut-images.json', lambda d: d['images'][1].update({'transition': 'not-a-real-slug'}))
        self.refused('not in the measured catalogue')

    def test_a_partial_custom_move_refuses(self):
        edit_json(self.edit / 'capcut-images.json', lambda d: d['images'][0].update({'scale': [1.0, 1.1]}))
        self.refused('scale, x and y go together')

    def test_a_bed_without_beats_refuses(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['beds'][0].pop('beats'))
        self.refused('beats names the beats it serves')

    def test_a_beat_the_edit_plan_lacks_refuses(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['sfx'][0].update({'beats': ['B09']}))
        self.refused('does not have: B09')

    def test_a_bed_longer_than_its_file_refuses(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['beds'][0].update({'end': 6.0}))
        self.refused('which holds 3.000 s')

    def test_a_sound_after_the_last_picture_refuses(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['beds'][0].update({'at': 4.0}))
        self.refused('after the last picture')

    def test_two_sound_files_with_one_name_refuse(self):
        other = self.rd / '50-audio' / 'sfx' / 'other' / 'tick.wav'
        write_wav(other, 0.4)
        edit_json(self.edit / 'sound-placements.json',
                  lambda d: d['sfx'].append({'id': 'tick2', 'file': str(other), 'at': 5.0, 'beats': ['B02']}))
        self.refused('also named tick.wav')

    def test_a_changed_sound_file_refuses_when_its_hash_was_recorded(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['sfx'][0].update({'sha256': '0' * 64}))
        self.refused('changed since the placements recorded it')

    @unittest.skipUnless(HAVE_FFMPEG, 'needs ffmpeg for the drawing clip')
    def test_a_drawing_on_a_shot_the_edit_lacks_refuses(self):
        edit_json(self.vis / 'drawings' / 'D01.json', lambda d: d.update({'shot': 'S099'}))
        self.refused('which the edit plan does not have')

    @unittest.skipUnless(HAVE_FFMPEG, 'needs ffmpeg for the drawing clip')
    def test_a_drawing_clip_without_its_spec_refuses(self):
        (self.vis / 'drawings' / 'D01.json').unlink()
        self.refused('no drawing spec beside it')

    def test_facts_are_warnings_not_refusals(self):
        edit_json(self.edit / 'sound-placements.json', lambda d: d['beds'][0].update({'volume': 0.5}))
        edit_json(self.edit / 'edit-plan.json', lambda d: d['pauses'][0]['transition'].update({'bed': 'none'}))
        if HAVE_FFMPEG:
            write_mov(self.vis / 'drawings' / 'D01.mov', 1.5)
            edit_json(self.vis / 'drawings' / 'D01.json',
                      lambda d: d.update({'still_motion': {'scale': [1.0, 1.1], 'x': [0, 0], 'y': [0, 0]}}))
            draw_record(self.vis / 'drawings', seconds=1.5)       # rendered again, as a changed drawing must be
        code, res, r = self.dry()
        self.assertEqual(code, 0, (res, r.stderr[-400:]))
        joined = ' | '.join(json.loads(self.plan_file.read_text(encoding='utf-8'))['warnings'])
        self.assertIn('volume 0.5', joined)
        self.assertIn('decided with the bed "none"', joined)
        if HAVE_FFMPEG:
            self.assertIn('leaves the still', joined)
            self.assertIn("differs from the images file's move", joined)
        plan = json.loads(self.plan_file.read_text(encoding='utf-8'))
        self.assertEqual(plan['beds'][0]['volume'], 0.5)       # the decided level goes in as decided


@unittest.skipUnless(HAVE_FFPROBE, 'needs ffprobe')
class DraftCheckTests(unittest.TestCase):
    """Only a fresh, prepared clone is written: never the template, a project that holds clips, or one CapCut opened."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rd = make_run(self.root, drawings=False)
        self.store = self.root / 'drafts'

    def tearDown(self):
        self.tmp.cleanup()

    def dry(self, d):
        return cli('capcut-build', '--run', self.rd, '--video', 1, '--draft', d, '--dry-run')

    def test_a_fresh_prepared_clone_passes(self):
        code, res, r = self.dry(fake_draft(self.store))
        self.assertEqual(code, 0, (res, r.stderr[-400:]))
        plan = json.loads((self.rd / '70-edit' / 'video-01' / 'capcut' / 'build-plan.json').read_text(encoding='utf-8'))
        self.assertEqual((plan['draft_name'], plan['canvas'], plan['template_draft']),
                         ('24_Nov_2099_v01', '1920x1080', CFG.get('template_draft')))

    def test_every_other_draft_is_refused(self):
        cases = {
            'already holds 1 clip': lambda: fake_draft(self.store, tracks=[{'type': 'video', 'segments': [{'id': 'x'}]}]),
            'not this folder': lambda: fake_draft(self.store, name='a', content_name='b'),
            'is the template draft': lambda: fake_draft(self.store, name=str(CFG.get('template_draft'))),
            'the canvas is 1080x1920': lambda: fake_draft(self.store, canvas_config={'width': 1080, 'height': 1920}),
        }
        for needle, make in cases.items():
            with self.subTest(needle):
                d = make()
                code, res, _ = self.dry(d)
                self.assertEqual(code, 2, res)
                self.assertIn(needle, ' | '.join(res['problems']))
                shutil.rmtree(self.store)
        for needle, touch in (('draft_meta_info.json (the template', 'draft_meta_info.json'),
                              ('template-2.tmp is in the draft', 'template-2.tmp')):
            with self.subTest(needle):
                d = fake_draft(self.store)
                (d / touch).write_text('{}', encoding='utf-8')
                code, res, _ = self.dry(d)
                self.assertEqual(code, 2, res)
                self.assertIn(needle, ' | '.join(res['problems']))
                shutil.rmtree(self.store)
        with self.subTest('layout'):
            d = fake_draft(self.store)
            (d / 'timeline_layout.json').write_text('{"dockItems": [{"timelineIds": ["another"]}]}', encoding='utf-8')
            code, res, _ = self.dry(d)
            self.assertIn('timeline_layout.json does not point', ' | '.join(res['problems']))
            shutil.rmtree(self.store)
        with self.subTest('no template beside it'):
            d = fake_draft(self.store)
            shutil.rmtree(self.store / str(CFG.get('template_draft')))
            code, res, _ = self.dry(d)
            self.assertIn('is not beside this draft', ' | '.join(res['problems']))
            shutil.rmtree(self.store)
        with self.subTest('not a draft'):
            (self.root / 'empty').mkdir()
            code, res, _ = self.dry(self.root / 'empty')
            self.assertIn('not a CapCut draft', ' | '.join(res['problems']))

    def call(self, mod, d):
        a = types.SimpleNamespace(run=str(self.rd), video='1', draft=str(d), dry_run=False, images=None, no_moves=False,
                                  sound_placements=None, no_sounds=False, drawings=None, no_drawings=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                mod.cmd_capcut_build(a)
        return cm.exception.code, json.loads(buf.getvalue().strip().splitlines()[-1])

    def test_capcut_running_refuses_before_anything_is_read(self):
        mod = load_module()
        mod._capcut_running = lambda: True
        code, res = self.call(mod, fake_draft(self.store))
        self.assertEqual(code, 3, res)
        self.assertIn('CapCut is running', res['error'])
        self.assertFalse((self.rd / '70-edit' / 'video-01' / 'capcut').exists())

    def test_no_mcp_library_refuses(self):
        mod = load_module()
        mod._capcut_running = lambda: False
        real = mod.cfg_get
        mod.cfg_get = lambda path, default=None: str(self.root / 'nowhere' / 'core.js') if path == 'capcut.mcp_core' else real(path, default)
        code, res = self.call(mod, fake_draft(self.store))
        self.assertEqual(code, 2, res)
        self.assertIn('capcut.mcp_core', ' | '.join(res['problems']))
        self.assertFalse((self.rd / '70-edit' / 'video-01' / 'capcut').exists())


class CommandTests(unittest.TestCase):
    def test_help_and_config(self):
        r = subprocess.run([sys.executable, '-B', str(TOOL), 'capcut-build', '-h'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        for flag in ('--run', '--video', '--draft', '--images', '--no-moves', '--sound-placements', '--no-sounds', '--drawings',
                     '--dry-run'):
            self.assertIn(flag, r.stdout)
        self.assertEqual(CORE_JS.name, 'core.js', 'config.json -> capcut.mcp_core names the CapCut MCP library')
        self.assertTrue((ROOT / 'scripts' / 'capcut_build.mjs').is_file())

    def test_a_draft_or_a_dry_run(self):
        code, res, _ = cli('capcut-build', '--run', ROOT, '--video', 1)
        self.assertEqual(code, 2)
        self.assertIn('--draft', res['error'])


@unittest.skipUnless(HAVE_FFPROBE and HAVE_FFMPEG and HAVE_NODE and CORE_JS.is_file() and template_draft(),
                     'needs node, the CapCut MCP library, ffmpeg and the CapCut template draft')
class BuildIntoATemplateCopyTests(unittest.TestCase):
    """The real build, through the CapCut MCP's own library, into a clone of a scratch copy of the template."""

    @classmethod
    def setUpClass(cls):
        ct = load_module()
        if ct._capcut_running():
            raise unittest.SkipTest('CapCut is open: core.js refuses to save while it runs')
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.rd = make_run(root)
        cls.edit = cls.rd / '70-edit' / 'video-01'
        tpl = template_draft()
        cls.real_store, cls.real_tpl_sha = tpl.parent, sha(tpl / 'draft_content.json')
        cls.store = root / 'drafts'
        shutil.copytree(tpl, cls.store / tpl.name)                  # read only: the real template is copied, never written
        cls.tpl_copy_sha = sha(cls.store / tpl.name / 'draft_content.json')
        cls.name = '24_Nov_2099_v01'
        js = ("import { pathToFileURL } from 'url';"
              "const m = await import(pathToFileURL(process.env.CORE).href);"
              "console.log(JSON.stringify(m.cloneDraft(process.env.TPL, process.env.NAME, { empty: true })));")
        subprocess.run(['node', '--input-type=module', '-e', js], check=True, capture_output=True, text=True,
                       env={**os.environ, 'CORE': str(CORE_JS), 'TPL': tpl.name, 'NAME': cls.name,
                            'CAPCUT_DRAFTS_DIR': str(cls.store), 'CAPCUT_TEMPLATE_DRAFT': tpl.name})
        cls.draft = cls.store / cls.name
        code, res, r = cli('capcut-prep', '--draft', cls.draft, '--canvas', '1920x1080')
        assert code == 0, (res, r.stderr[-400:])
        extra = []
        cls.cli_ok = bool(ct._capcut_cli_path())
        if not cls.cli_ok:                                          # capcut-transitions needs capcut-cli: build without the join
            imgs = json.loads((cls.edit / 'capcut-images.json').read_text(encoding='utf-8'))
            imgs['images'][1].pop('transition')
            (cls.edit / 'no-join-images.json').write_text(json.dumps(imgs), encoding='utf-8')
            extra = ['--images', cls.edit / 'no-join-images.json']
        cls.code, cls.res, cls.r = cli('capcut-build', '--run', cls.rd, '--video', 1, '--draft', cls.draft, *extra)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def content(self, name='draft_content.json'):
        return json.loads((self.draft / name).read_text(encoding='utf-8'))

    def test_the_build_succeeds_and_logs_what_it_read(self):
        self.assertEqual(self.code, 0, (self.res, self.r.stderr[-600:]))
        log = json.loads((self.edit / 'capcut' / 'build-log.json').read_text(encoding='utf-8'))
        self.assertTrue(log['ok'])
        self.assertEqual(Path(log['draft']), self.draft)
        self.assertEqual({k: log['counts'][k] for k in ('pictures', 'overlays', 'narration', 'beds', 'sfx')},
                         {'pictures': 3, 'overlays': 1, 'narration': 1, 'beds': 1, 'sfx': 1})
        narr = next(i for i in log['inputs'] if i['role'] == 'narration')
        self.assertEqual(narr['sha256'], sha(self.rd / '50-audio' / 'video-01' / 'narration-edit.wav'))
        self.assertEqual(log['toolkit']['mcp_core_sha256'], sha(CORE_JS))
        self.assertEqual(sorted((t['name'], t['segments']) for t in log['tracks'] if t['segments']),
                         sorted([('video', 3), ('draw1', 1), ('audio', 1), ('music', 1), ('sfx', 1)]))
        self.assertIn('capcut-repair', ' '.join(self.res['next']))

    def test_the_pictures_are_the_shots_on_their_real_times(self):
        c = self.content()
        mats = {m['id']: m for m in c['materials']['videos']}
        main = next(t for t in c['tracks'] if t['type'] == 'video')
        segs = sorted(main['segments'], key=lambda s: s['target_timerange']['start'])
        self.assertEqual([(s['target_timerange']['start'], s['target_timerange']['duration'], Path(mats[s['material_id']]['path']).name)
                          for s in segs], [(0, 2000000, 'S001.png'), (2000000, 2100000, 'S002.png'), (4100000, 1900000, 'S001.png')])
        self.assertEqual({(mats[s['material_id']]['type'], mats[s['material_id']]['duration']) for s in segs}, {('photo', 10800000000)})
        kf = {k['property_type'] for k in segs[0].get('common_keyframes') or []}
        self.assertIn('KFTypeScaleX', kf)                            # capcut-motion keyed the zoom
        self.assertIn('KFTypePositionX', {k['property_type'] for k in segs[2].get('common_keyframes') or []})   # and the pan
        if self.cli_ok:                                              # the join into S002 sits on the clip before it
            joins = {m['id'] for m in c['materials'].get('transitions') or []}
            self.assertTrue(joins & set(segs[0].get('extra_material_refs') or []))
        draw = [t for t in c['tracks'] if t['type'] == 'video'][1]
        self.assertEqual([(s['target_timerange']['start'], s['target_timerange']['duration'], Path(mats[s['material_id']]['path']).name)
                          for s in draw['segments']], [(2000000, 2100000, 'D01.mov')])

    def test_the_narration_is_whole_at_0_speed_1_and_every_sound_in_capcuts_form(self):
        c = self.content()
        mats = {m['id']: m for m in c['materials']['audios']}
        got = {}
        for t in c['tracks']:
            for s in t['segments'] if t['type'] == 'audio' else []:
                m = mats[s['material_id']]
                got[Path(m['path']).name] = (t['name'], s['target_timerange'], s['source_timerange'], s.get('speed'), m['type'], m['name'])
        name, tg, src, speed, typ, mname = got['narration-edit.wav']
        self.assertEqual((tg['start'], src['start'], speed, typ, mname), (0, 0, 1, 'extract_music', 'narration-edit.wav'))
        self.assertEqual(tg['duration'], src['duration'])
        self.assertAlmostEqual(tg['duration'], 6000000, delta=1000)
        self.assertEqual((got['M1.wav'][0], got['M1.wav'][1]['start'], got['M1.wav'][4]), ('music', 1500000, 'extract_music'))
        self.assertEqual((got['tick.wav'][0], got['tick.wav'][1]['start'], got['tick.wav'][4]), ('sfx', 4300000, 'extract_music'))

    def test_the_mirror_holds_the_same_timeline(self):
        if (self.draft / 'draft_info.json').is_file():
            self.assertEqual(self.content('draft_info.json')['tracks'], self.content()['tracks'])

    def test_the_template_and_the_real_drafts_folder_are_untouched(self):
        self.assertEqual(sha(self.store / template_draft().name / 'draft_content.json'), self.tpl_copy_sha)
        self.assertEqual(sha(template_draft() / 'draft_content.json'), self.real_tpl_sha)
        self.assertFalse((self.real_store / self.name).exists())

    def test_a_second_build_on_the_same_project_is_refused(self):
        code, res, _ = cli('capcut-build', '--run', self.rd, '--video', 1, '--draft', self.draft, '--no-moves')
        self.assertEqual(code, 2, res)
        self.assertIn('already holds', ' | '.join(res['problems']))

    def test_timeline_write_traces_every_clip_the_build_placed(self):
        if self.code != 0:
            self.skipTest('the build failed (see test_the_build_succeeds_and_logs_what_it_read)')
        code, res, r = cli('timeline-write', '--run', self.rd, '--video', 1, '--draft', self.draft, '--sounds',
                           self.edit / 'capcut' / 'sounds.json', tool=STATIC_CORE)
        if res is None or code not in (0, 2):
            self.skipTest(f'static_core.py timeline-write did not run here: {r.stderr[-300:]}')
        self.assertEqual(res['problems'], [], res)
        self.assertEqual((res['visual_segments'], res['overlays'], res['audio_tracks']), (3, 1, 3))


if __name__ == '__main__':
    unittest.main()
