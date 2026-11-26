"""The audit implementation of 2026-11-26. No paid API calls.

Release state read from the real file (which file is the deliverable, how loud it plays, what a person did with it),
and a recurring major finding closed by a decision. The fixtures are test_static_core's; its own tests run there, once."""
from __future__ import annotations
import argparse
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_static_core as base                                    # noqa: E402
from test_static_core import cli, save                             # noqa: E402


def fixture_only(cls):
    """A class here borrows a fixture from test_static_core, not its tests: those run once, in their own file."""
    for parent in cls.__mro__[1:]:
        for name in vars(parent):
            if name.startswith('test_') and name not in vars(cls):
                setattr(cls, name, None)
    return cls


def load_core(name):
    spec = importlib.util.spec_from_file_location(name, base.TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@fixture_only
class ReleaseStateTests(base.ExportBindingTests):
    """Built, exported, mastered, checked, heard by a person: five facts, none standing in for another (2026-11-26:
    a run read 'released' while the file in the user's hands was CapCut's own export, 7 dB under its master)."""

    WHY = 'the test references sit near this level and the voice carries it'

    def master(self, src, name='master.mp4', target=-16):
        out = self.td / name
        res = cli('master-sound', '--run', self.rd, '--video', 1, '--file', src, '--out', out, '--target-lufs', target,
                  '--why', self.WHY)
        self.assertLess(abs(res['result']['integrated_lufs'] - target), 0.5, res)
        return out

    def passed(self, f):
        """export-check --deep on a file. The fixture has no recorded narration gate, so that one issue is set aside
        by hand (as the binding tests do); every other finding has to be absent."""
        res = cli('export-check', '--run', self.rd, '--video', 1, '--file', f, '--deep', expected=None)
        self.assertEqual([x for x in res['issues'] if not x.startswith('audio_gate')], [], res['issues'])
        p = self.core.export_provenance_path(self.rd, 1)
        prov = json.loads(p.read_text(encoding='utf-8'))
        sha = self.core.file_sha256(f)
        prov['exports'][sha].update(ready=True, issues=[])
        save(p, prov)
        return sha

    def release(self, f, record=True):
        """release-check on a file, with the gates this fixture has no records for (plan, narration, shots, the final
        read) answered clean: what is tested is the binding to the file and what gets written."""
        c = self.core
        clean = {'ready': True, 'issues': [], 'warnings': []}
        args = argparse.Namespace(run=str(self.rd), video=1, file=str(f), thumbnail=None, record=record)
        with mock.patch.object(c, 'plan_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'audio_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'shot_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'timeline_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'review_state', return_value={'issues': [], 'warnings': [], 'rounds': 1}), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as so:
            try:
                c.cmd_release_check(args)
            except SystemExit:
                pass
        return json.loads(so.getvalue())

    def test_a_file_says_what_it_is_and_how_loud_it_plays(self):
        raw = self.export(self.td / 'raw.mp4', self.stills)
        res = self.issues(raw, deep=False)
        self.assertEqual(res['role'], 'not_on_record')
        self.assertIsInstance(res['loudness']['integrated_lufs'], float)
        self.assertTrue(any(w.startswith('not mastered yet') for w in res['warnings']), res['warnings'])
        out = self.master(raw)
        m = self.issues(out, deep=False)
        self.assertEqual(m['role'], 'master')
        self.assertFalse([x for x in m['issues'] if x.startswith('export_master_')], m['issues'])
        self.assertLess(abs(m['loudness']['integrated_lufs'] + 16), 0.5)
        r = self.issues(raw, deep=False)
        self.assertEqual(r['role'], 'unmastered_export')
        self.assertTrue(any('unmastered export' in w for w in r['warnings']), r['warnings'])
        # a third file of the same project is neither: a new export needs its own master
        other = self.export(self.td / 'other.mp4', self.stills, black_at=1.0)
        o = self.issues(other, deep=False)
        self.assertEqual(o['role'], 'not_on_record')
        self.assertTrue(any('not the recorded master' in w for w in o['warnings']), o['warnings'])
        # the record says one loudness and the file plays another: the file is believed
        mp = self.rd / '80-deliverables/video-01/master.json'
        rec = json.loads(mp.read_text(encoding='utf-8'))
        rec['target_lufs'] = -10.0
        save(mp, rec)
        bad = self.issues(out, deep=False)['issues']
        self.assertTrue(any(x.startswith('export_master_measures_') and x.endswith('_not_its_recorded_-10_LUFS')
                            for x in bad), bad)

    def test_the_deliverable_is_told_step_by_step(self):
        c, rd = self.core, self.rd
        d = c.deliverable_facts(rd, 1)
        self.assertEqual((d['state'], d['steps']['built'], d['steps']['exported']), ('built_not_exported', True, False))
        raw = self.export(self.td / 'raw.mp4', self.stills)
        # an export whose check found something counts for nothing, and the next step says why
        cli('export-check', '--run', rd, '--video', 1, '--file', raw, '--deep', expected=2)
        d = c.deliverable_facts(rd, 1)
        self.assertEqual(d['state'], 'built_not_exported')
        self.assertIn('does not count', d['next'])
        self.passed(raw)
        self.assertEqual(c.deliverable_facts(rd, 1)['state'], 'exported_not_mastered')
        out = self.master(raw)
        self.assertEqual(c.deliverable_facts(rd, 1)['state'], 'mastered_not_checked')
        msha = self.passed(out)
        d = c.deliverable_facts(rd, 1)
        self.assertEqual((d['state'], d['file']), ('mastered_not_released', str(out)))
        self.assertEqual(d['steps'], {'built': True, 'exported': True, 'mastered': True, 'verified': False,
                                      'human_review': 'none on record'})
        self.assertEqual(c.stage_after_stills(d['steps']), 'exported')
        # release-check through the command, with this fixture's other gates open: the file is named for what it is,
        # its loudness measured, the missing human review said first, and nothing is recorded while a gate is open
        rel = cli('release-check', '--run', rd, '--video', 1, '--file', out, '--record', expected=2)
        self.assertEqual(rel['file_is'], 'master')
        self.assertLess(abs(rel['loudness']['integrated_lufs'] + 16), 0.5)
        self.assertEqual(rel['human_review'], {'on_record': False, 'kinds': []})
        self.assertTrue(rel['warnings'][0].startswith('no person has listened'), rel['warnings'])
        self.assertIsNone(rel['release_record'])
        self.assertFalse(c.release_path(rd, 1).exists())
        # every gate passed: asked without --record it writes nothing, with it the release is on record for this file
        dry = self.release(out, record=False)
        self.assertTrue(dry['ready'], dry['issues'])
        self.assertTrue(str(dry['release_record']).startswith('not written'))
        self.assertFalse(c.release_path(rd, 1).exists())
        self.assertTrue(self.release(out)['ready'])
        rec = json.loads(c.release_path(rd, 1).read_text(encoding='utf-8'))
        self.assertEqual((rec['sha256'], rec['technical']['ready'], rec['human_review']['on_record']), (msha, True, False))
        d = c.deliverable_facts(rd, 1)
        self.assertEqual((d['state'], d['steps']['verified']), ('released', True))
        self.assertIn('no person has listened', d['next'])
        self.assertEqual(c.stage_after_stills(d['steps']), 'released')
        # the unmastered export never passes as the release, and leaves the record as it was
        notit = self.release(raw)
        self.assertIn('export:this_file_is_not_the_recorded_master:it_is_the_unmastered_export', notit['issues'])
        self.assertEqual(json.loads(c.release_path(rd, 1).read_text(encoding='utf-8'))['sha256'], msha)
        # which file is which, asked of the files themselves
        dv = cli('deliverable', '--run', rd, '--video', 1, '--file', raw)['this_file']
        self.assertEqual((dv['is'], dv['is_the_deliverable']), ('unmastered_export', False))
        dv = cli('deliverable', '--run', rd, '--video', 1, '--file', out)['this_file']
        self.assertEqual((dv['is'], dv['is_the_deliverable'], dv['of_the_project_as_it_stands']), ('master', True, True))
        # a person's listen is their own words, for that exact file; a word or two is not a record
        cli('human-review', '--run', rd, '--video', 1, '--file', out, '--kind', 'listened', '--user-words', 'fine',
            expected=2)
        self.assertFalse(c.human_review_path(rd, 1).exists())
        hr = cli('human-review', '--run', rd, '--video', 1, '--file', out, '--kind', 'listened_and_watched',
                 '--user-words', 'I heard and watched all of it on headphones')
        self.assertEqual(hr['deliverable']['steps']['human_review'], ['listened', 'watched'])
        self.assertEqual(c.deliverable_facts(rd, 1)['next'], '')
        self.assertFalse(c.human_review_state(rd, 1, c.file_sha256(raw))['on_record'])
        # the project is changed and not checked again: it is no longer the project that was built
        c2 = json.loads(json.dumps(self.content))
        c2['tracks'][0]['segments'][0]['material_id'], c2['tracks'][0]['segments'][1]['material_id'] = 'v2', 'v1'
        save(self.draft / 'draft_content.json', c2)
        d = c.deliverable_facts(rd, 1)
        self.assertEqual((d['state'], d['steps']['built']), ('project_changed_since_its_check', False))
        self.assertEqual(c.stage_after_stills(d['steps']), 'stills')
        # checked again as rebuilt: the earlier exports, their master and its release belong to an earlier build
        snap = c.project_snapshot(rd, 1, self.draft)
        save(c.timeline_check_path(rd, 1), {'checked_at': c.now(), 'draft': str(self.draft),
                                            'snapshot_sha256': c.canonical_sha(snap), 'snapshot': snap})
        d = c.deliverable_facts(rd, 1)
        self.assertEqual((d['state'], d['steps']['exported'], d['steps']['verified']), ('built_not_exported', False, False))
        said = ' | '.join(d['stale'])
        for part in ('2 export(s) on record belong to an earlier build', 'the master on record was made from an earlier build',
                     'a release is on record for a file that is not the current master'):
            self.assertIn(part, said)
        self.assertEqual(c.stage_after_stills(d['steps']), 'edit_checked')


@fixture_only
class StageFollowsRecordsTests(base.StaticStudioTests):
    """The stored stage never claims more than the records: status corrects it both ways, --look writes nothing."""

    def test_a_stored_released_is_corrected_and_look_leaves_the_file_alone(self):
        self.write_plan()
        sp = self.run / 'state.json'
        state = json.loads(sp.read_text(encoding='utf-8'))
        state['stage'] = 'released'
        save(sp, state)
        before = sp.read_bytes()
        seen = cli('status', '--run', self.run, '--look')
        self.assertEqual(seen['stage_was'], 'released')
        self.assertNotEqual(seen['stage'], 'released')
        self.assertIn('--look', seen['stage_note'])
        self.assertEqual(sp.read_bytes(), before)
        self.assertEqual(seen['videos']['1']['deliverable']['state'], 'not_built')
        done = cli('status', '--run', self.run)
        self.assertEqual((done['stage_was'], done['stage']), ('released', seen['stage']))
        self.assertEqual(json.loads(sp.read_text(encoding='utf-8'))['stage'], seen['stage'])
        self.assertNotIn('stage_was', cli('status', '--run', self.run))


class DecisionTests(unittest.TestCase):
    """A problem two readers found is closed by a decision, never by the word "disputed" (2026-11-26: a slow stretch
    was closed that way three times because its cure fell under the length window, and nobody was asked)."""

    F = {'id': 'F1', 'severity': 'major', 'needs_recurrence': True, 'problem': 'the middle leaves the brothers for too long'}
    OPTS = [{'cure': 'cut the two background beats to one', 'cost': 'forty seconds under the locked length'},
            {'cure': 'leave the passage as it is', 'cost': 'the slow stretch stays in the film'}]

    @classmethod
    def setUpClass(cls):
        cls.core = load_core('static_studio_core_decisions')

    def ans(self, **dec):
        a = {'action': 'disputed', 'note': 'the cut that cures it falls under the length window',
             'recurrence': {'recurs_of': 'r1:F1', 'root_cause': 'two background beats in a row leave the story',
                            'scope': 'dispute'}}
        return dict(a, decision=dec) if dec else a

    def why(self, **dec):
        return self.core.answer_problem('script', self.F, self.ans(**dec))

    def test_a_disputed_recurring_major_needs_the_cures_weighed_and_who_decided(self):
        c = self.core
        self.assertIsNone(c.answer_problem('script', self.F, self.ans(), 3))          # earlier rounds keep their rules
        self.assertIn('decision.options', self.why())
        ok = dict(options=self.OPTS, chosen='leave the passage as it is', blocked_by='nothing', decided_by='director')
        self.assertIn('decision.options', self.why(**dict(ok, options=self.OPTS[:1])))
        self.assertIn('decision.options', self.why(**dict(ok, options=[{'cure': 'cut', 'cost': 'time'}] * 2)))
        self.assertIn('decision.chosen', self.why(**dict(ok, chosen='')))
        self.assertIn('decision.blocked_by', self.why(**dict(ok, blocked_by='the weather')))
        self.assertIn('needs to say what', self.why(**dict(ok, blocked_by='other')))
        self.assertIsNone(self.why(**dict(ok, blocked_by='other: the archive holds no second letter')))
        self.assertIn('decided_by', self.why(**dict(ok, decided_by='nobody')))
        self.assertIsNone(self.why(**ok))
        self.assertIsNone(c.owner_lock_pending(self.ans(**ok)))

    def test_a_cure_blocked_by_the_users_lock_is_the_users_decision(self):
        c = self.core
        ok = dict(options=self.OPTS, chosen='leave the passage as it is', blocked_by='nothing', decided_by='director')
        for lock in ('length', 'recorded_narration', 'budget'):
            blocked = dict(ok, blocked_by=lock)
            self.assertIn('only the user can lift', self.why(**blocked))
            self.assertEqual(c.owner_lock_pending(self.ans(**blocked)), lock)
            self.assertIn('user_words', self.why(**dict(blocked, decided_by='user')))
            mine = dict(blocked, decided_by='user', user_words='keep the length and leave the middle')
            self.assertIsNone(self.why(**mine))
            self.assertIsNone(c.owner_lock_pending(self.ans(**mine)))
        # a re-plan is its own answer: a structural cause that is revised needs no decision
        revised = {'action': 'revised', 'lines': ['L001'], 'note': 'the order was changed for this finding',
                   'recurrence': {'recurs_of': 'r1:F1', 'root_cause': 'the treatment puts background first',
                                  'scope': 'structure'}}
        self.assertIsNone(c.answer_problem('script', self.F, revised))


@fixture_only
class DecisionFlowTests(base.StaticStudioTests):
    """The same, through review-record and plan-check: the open answer says why, and a cure the length blocks is
    reported as waiting for the user."""

    def test_a_cure_the_length_blocks_stops_for_the_user(self):
        vd = self.write_plan(review_script=False)
        major = {'id': 'F1', 'severity': 'major', 'lines': ['L001-L012'],
                 'problem': 'the decision the title promises arrives only after a long stretch of background',
                 'likely_cause': 'waiting too long for the payoff', 'suggestion': 'meet the decision sooner'}
        _, r1 = self.review('script', [major])
        script = json.loads((vd / 'script.json').read_text(encoding='utf-8'))
        script['lines'][0]['text'] = 'A shorter opening, with the same careful planning and real consequences, then on.'
        save(vd / 'script.json', script)
        self.answer_file(r1['answers_file'], {'answers': {'F1': {
            'action': 'revised', 'lines': ['L001'], 'note': 'the background before the decision was shortened'}}})
        _, r2 = self.review('script', [major])
        self.assertEqual(json.loads((vd / 'reviews/script-r2.json').read_text(encoding='utf-8'))['answer_rules'], 4)
        self.assertIn('decision', json.dumps(json.loads(Path(r2['answers_file']).read_text(encoding='utf-8'))))
        opts = [{'cure': 'cut the background beats to one', 'cost': 'forty seconds under the locked length'},
                {'cure': 'leave the passage as it is', 'cost': 'the slow stretch stays in the film'}]

        def answer(**dec):
            a = {'action': 'disputed', 'note': 'the cut that would cure it falls under the length window',
                 'recurrence': {'recurs_of': 'r1:F1', 'root_cause': 'the background still comes before the decision',
                                'scope': 'dispute'}}
            self.answer_file(r2['answers_file'], {'answers': {'F1': dict(a, decision=dec) if dec else a}})
            return cli('plan-check', '--run', self.run, '--video', 1, expected=None)
        res = answer()
        self.assertTrue(any(x.startswith('script_review_r2_unanswered') and 'F1' in x for x in res['issues']), res['issues'])
        self.assertIn('decision.options', res['creative']['answers_needed']['r2:F1'])
        res = answer(options=opts, chosen='leave the passage as it is', blocked_by='length', decided_by='director')
        self.assertIn('script_review_r2_F1_waits_for_the_users_decision:its_cure_is_blocked_by_length', res['issues'])
        res = answer(options=opts, chosen='leave the passage as it is', blocked_by='length', decided_by='user',
                     user_words='keep the length as it is')
        self.assertFalse([x for x in res['issues'] if x.startswith('script_review_r2') and 'F1' in x], res['issues'])
        self.assertEqual(res['creative']['answers_needed'], {})
        self.assertTrue(any('decided by the user: F1' in w for w in res['warnings']), res['warnings'])


if __name__ == '__main__':
    unittest.main()
