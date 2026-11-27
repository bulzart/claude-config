"""The working set of references (2026-11-27, the owner: "only take 15 references do not lose all the resources on
analysing the whole 38 of them"). A run can work from some of its references folder: `reference-set` records which
ones are set aside and why, and every later step (prepare, the analysis plan, the niche evidence, the niche check,
the content record's state, a clone) sees the working set only. Nothing is deleted, and an unchanged run behaves as
before. No paid calls, no model."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT/'scripts'/'static_core.py'


def cli(*args, expected=0):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                            capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
    try:
        output = json.loads(result.stdout)
    except ValueError:
        raise AssertionError(f'CLI not JSON: {result.stdout}\n{result.stderr}')
    if expected is not None:
        assert result.returncode == expected, f'Expected {expected} got {result.returncode}: {output}'
    return output


def save(path, d):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d), encoding='utf-8')


class ReferenceSetTests(unittest.TestCase):
    # id: (duration_s, card niches, story form). Made-up subjects, unrelated to any run.
    REFS = {'V001': (700., ['lighthouses'], 'single-night investigation'),
            'V002': (650., ['lighthouses'], 'single-night investigation'),
            'V003': (620., ['sourdough'], 'recipe tutorial'),
            'V004': (600., ['sourdough'], 'recipe tutorial'),
            'V005': (720., ['tide pools'], 'nature documentary')}
    WHY = 'the owner asked for three references, and these three were analysed first'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        refs = self.home/'references'
        refs.mkdir()
        for i, colour in enumerate(('red', 'blue', 'green', 'yellow', 'cyan'), 1):
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                            f'color=c={colour}:s=64x36:r=5', '-t', '0.6', '-pix_fmt', 'yuv420p',
                            str(refs/f'clip_{i}.mp4')], check=True)
        self.run = Path(cli('init', '--references', refs, '--workspace', self.home/'runs', '--slug', 'refset')['run'])
        cli('scan', '--run', self.run)
        invp = self.run/'00-inventory/references.json'
        inv = json.loads(invp.read_text(encoding='utf-8'))
        for row in inv['items']:
            if row['id'] in self.REFS:
                row['duration_s'] = self.REFS[row['id']][0]
        save(invp, inv)
        for vid in ('V001', 'V002', 'V003'):
            self.analyse(vid)

    def analyse(self, vid):
        dur, nn, form = self.REFS[vid]
        av = self.run/'20-analysis/av'
        save(av/f'{vid}.json', {'sheets': [str(av/vid/f'sheet-{k:03d}.jpg') for k in range(1, 11)],
                                'shots': [{'start_s': k} for k in range(120)], 'inspect_candidates': [],
                                'summary': {'narration': {'words': 1700, 'speech_rate_wpm': 160,
                                                          'pitch_range_st': {'median': 9.0},
                                                          'pause_profile': {'longest_pause_s': 0.8}},
                                            'picture': {'cuts_per_min': 12.0}}})
        save(self.run/'20-analysis/content'/f'{vid}-shots'/'index.json', {'reference_id': vid, 'sheets': 4})
        save(self.run/'20-analysis/cards'/f'{vid}.json', {
            'reference_id': vid, 'niches': nn, 'story_form': form, 'language': 'en',
            'editorial_summary': 'a video about ' + ', '.join(nn), 'visual_medium': 'drawn stills',
            'narrator_character': 'a calm guide', 'delight': [{'what': 'a concrete surprise every minute'}],
            'viewer_experience': [{'start_s': 0, 'end_s': 30, 'question': 'what', 'evidence': '[O] 00:10'}]})
        (self.run/'20-analysis'/f'{vid}-notes.md').write_text('notes', encoding='utf-8')
        save(self.run/'20-analysis/content'/f'{vid}.json', {'reference_id': vid, 'segments': [],
                                                           'story_without_exclusions': {'status': 'coherent'}})

    @staticmethod
    def niche(nid, name, core):
        return {'id': nid, 'name': name, 'identity': f'videos about {name}: what it is and why people care about it',
                'boundary': f'stops being this niche when the video is no longer about {name} at all',
                'viewer_reward': f'the satisfaction of understanding {name} from the inside, step by step',
                'members': [{'ref': r, 'role': 'core', 'why': f'its card says it is about {name}'} for r in core],
                'formats': [{'form': 'how they tell it', 'refs': list(core)}], 'comparable_cohorts': [],
                'evidence': [{'ref': core[0], 'at': '00:10', 'observed': f'the opening shows {name} at work'}]}

    def keep(self, ids='V001,V002,V003', *extra, expected=0):
        return cli('reference-set', '--run', self.run, '--keep', ids, '--why', self.WHY, *extra, expected=expected)

    def three(self):
        return {'niches': [self.niche('N1', 'lighthouses', ['V001', 'V002']), self.niche('N2', 'sourdough', ['V003'])]}

    def test_a_run_without_a_choice_works_from_every_reference(self):
        out = cli('reference-set', '--run', self.run)
        self.assertEqual(out['working'], sorted(self.REFS))
        self.assertEqual(out['set_aside'], {})
        self.assertEqual(out['still_to_analyse'], ['V004', 'V005'])
        self.assertIsNone(out['file'])
        ev = cli('niche-evidence', '--run', self.run, expected=None)
        data = json.loads(Path(ev['evidence']).read_text(encoding='utf-8'))
        self.assertNotIn('set_aside', data)                       # an unchanged run keeps its evidence as it was
        self.assertNotIn('Set aside', Path(ev['markdown']).read_text(encoding='utf-8'))
        save(self.run/'20-analysis/niche-map.json', self.three())
        self.assertIn('references_not_in_any_niche_or_outliers:V004,V005',
                      cli('niche-check', '--run', self.run, expected=2)['issues'])
        self.assertNotIn('references_set_aside', cli('status', '--run', self.run))

    def test_the_working_set_is_what_every_later_step_sees(self):
        out = self.keep('V001,V002,V003', '--user-words', 'only take three references')
        self.assertEqual(out['working'], ['V001', 'V002', 'V003'])
        self.assertEqual(out['set_aside'], ['V004', 'V005'])
        self.assertEqual((out['analysed'], out['still_to_analyse']), (['V001', 'V002', 'V003'], []))
        rec = json.loads((self.run/'00-inventory/reference-set.json').read_text(encoding='utf-8'))
        self.assertEqual((rec['decided_by'], rec['user_words']), ('user', 'only take three references'))
        self.assertEqual(rec['set_aside']['V004'], {'file': 'clip_4.mp4', 'why': self.WHY})
        # prepare: no frames or transcript for a reference set aside, unless it is named
        self.assertEqual(sorted(cli('prepare', '--run', self.run, '--dry-run')['per_video']), ['V001', 'V002', 'V003'])
        self.assertEqual(sorted(cli('prepare', '--run', self.run, '--dry-run', '--ids', 'V004')['per_video']), ['V004'])
        # the analysis plan: nothing left to split; a reference set aside cannot be planned
        self.assertEqual(cli('analysis-plan', '--run', self.run, '--dry-run')['planned'], [])
        planned = cli('analysis-plan', '--run', self.run, '--all', '--dry-run', '--agents', 2)
        self.assertEqual(sorted(r for b in planned['batches'] for r in b['refs']), ['V001', 'V002', 'V003'])
        self.assertIn('not in the working set',
                      cli('analysis-plan', '--run', self.run, '--ids', 'V004', '--dry-run', expected=2)['error'])
        # the evidence, the niche check and the content record's state
        ev = cli('niche-evidence', '--run', self.run)
        data = json.loads(Path(ev['evidence']).read_text(encoding='utf-8'))
        self.assertEqual([r['ref'] for r in data['references']], ['V001', 'V002', 'V003'])
        self.assertEqual(data['set_aside'], ['V004', 'V005'])
        self.assertIn('Set aside for this run', Path(ev['markdown']).read_text(encoding='utf-8'))
        save(self.run/'20-analysis/niche-map.json', self.three())
        chk = cli('niche-check', '--run', self.run)
        self.assertEqual((chk['ok'], chk['facts']['references']), (True, 3))
        m = self.three()
        m['niches'][1]['members'].append({'ref': 'V004', 'role': 'core', 'why': 'its card says it is about sourdough'})
        m['niches'][1]['formats'][0]['refs'].append('V004')
        save(self.run/'20-analysis/niche-map.json', m)
        self.assertIn('niche_N2_member_is_set_aside_(reference-set):V004',
                      cli('niche-check', '--run', self.run, expected=2)['issues'])
        self.assertEqual(cli('content-review', '--run', self.run, '--status')['references'], 3)
        self.assertEqual(cli('status', '--run', self.run)['references_set_aside'], ['V004', 'V005'])

    def test_the_choice_is_kept_changed_and_undone(self):
        self.keep()
        cli('scan', '--run', self.run)                                  # a rescan keeps the choice
        self.assertEqual(cli('reference-set', '--run', self.run)['working'], ['V001', 'V002', 'V003'])
        out = cli('reference-set', '--run', self.run, '--aside', 'V005', '--why', 'the tide pool video is off the subject')
        self.assertEqual(out['working'], ['V001', 'V002', 'V003', 'V004'])
        self.assertEqual(out['still_to_analyse'], ['V004'])
        rec = json.loads((self.run/'00-inventory/reference-set.json').read_text(encoding='utf-8'))
        self.assertEqual(rec['decided_by'], 'director')
        self.assertEqual(rec['history'][0]['set_aside'], ['V004', 'V005'])
        out = cli('reference-set', '--run', self.run, '--all', '--why', 'the owner wants every reference after all')
        self.assertEqual((out['working'], out['set_aside']), (sorted(self.REFS), []))
        self.assertEqual(len(json.loads((self.run/'00-inventory/reference-set.json').read_text(encoding='utf-8'))['history']), 2)
        # nothing of a reference set aside was deleted
        self.keep('V001,V002')
        self.assertTrue((self.run/'20-analysis/cards/V003.json').is_file())
        self.assertTrue((self.run/'20-analysis/V003-notes.md').is_file())

    def test_what_it_refuses(self):
        self.assertIn('one of', cli('reference-set', '--run', self.run, '--keep', 'V001', '--aside', 'V002', '--why',
                                    self.WHY, expected=2)['error'])
        self.assertIn('--why', cli('reference-set', '--run', self.run, '--keep', 'V001', expected=2)['error'])
        self.assertIn('Unknown reference', self.keep('V001,V009', expected=2)['error'])
        self.assertIn('at least one reference', cli('reference-set', '--run', self.run, '--aside',
                                                    'V001,V002,V003,V004,V005', '--why', self.WHY, expected=2)['error'])
        self.assertFalse((self.run/'00-inventory/reference-set.json').exists())      # a refusal writes nothing
        # a locked niche keeps its members
        self.keep()
        cli('niche-evidence', '--run', self.run)
        save(self.run/'20-analysis/niche-map.json', self.three())
        cli('niche-check', '--run', self.run)
        cli('niche-lock', '--run', self.run, '--niche', 'N1', '--user-words', 'the lighthouse one')
        self.assertIn('locked niche', self.keep('V001,V003', expected=2)['error'])
        self.assertEqual(self.keep('V001,V002')['working'], ['V001', 'V002'])       # setting others aside is fine

    def test_a_clone_keeps_the_working_set(self):
        self.keep()
        cli('niche-evidence', '--run', self.run)
        save(self.run/'20-analysis/niche-map.json', self.three())
        cli('niche-check', '--run', self.run)
        clone = Path(cli('clone', '--from-run', self.run, '--workspace', self.home/'runs')['run'])
        self.assertEqual(cli('reference-set', '--run', clone)['working'], ['V001', 'V002', 'V003'])
        self.assertTrue(cli('niche-check', '--run', clone, expected=None)['facts']['references'] == 3)


if __name__ == '__main__':
    unittest.main()
