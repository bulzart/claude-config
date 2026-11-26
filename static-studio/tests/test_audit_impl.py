"""The audit implementation of 2026-11-26. No paid API calls.

Release state read from the real file (which file is the deliverable, how loud it plays, what a person did with it),
and a recurring major finding closed by a decision. The fixtures are test_static_core's; its own tests run there, once."""
from __future__ import annotations
import argparse
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
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

    def release(self, f, record=True, final=None):
        """release-check on a file, with the gates this fixture has no records for (plan, narration, shots, the final
        read) answered clean: what is tested is the binding to the file and what gets written."""
        c = self.core
        clean = {'ready': True, 'issues': [], 'warnings': []}
        args = argparse.Namespace(run=str(self.rd), video=1, file=str(f), thumbnail=None, record=record)
        with mock.patch.object(c, 'plan_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'audio_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'shot_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'timeline_facts', return_value=dict(clean)), \
                mock.patch.object(c, 'review_state',
                                  return_value=final or {'issues': [], 'warnings': [], 'rounds': 1}), \
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
        # the sound of this exact file is measured first (sound-review --file): a review of the raw export is not one
        # of its master, and the listening sheet it writes is the one handed to the user with the film
        self.assertEqual(self.release(out, record=False)['issues'],
                         ['sound:not_reviewed:run_sound-review_--file_on_this_file_(it_writes_the_listening_sheet_too)'])
        cli('sound-review', '--run', rd, '--video', 1, '--file', raw)
        self.assertEqual(self.release(out, record=False)['issues'],
                         ['sound:not_measured_in_this_file:run_sound-review_--file_on_it'])
        heard = cli('sound-review', '--run', rd, '--video', 1, '--file', out)
        self.assertEqual((heard['measured_in'], heard['sounds_placed'], heard['listening_items']), ('master.mp4', 0, 1))
        self.assertTrue(c.listening_sheet_path(rd, 1).is_file())
        # every gate passed: asked without --record it writes nothing, with it the release is on record for this file
        dry = self.release(out, record=False)
        self.assertTrue(dry['ready'], dry['issues'])
        self.assertTrue(str(dry['release_record']).startswith('not written'))
        self.assertFalse(c.release_path(rd, 1).exists())
        # an open answer of the final review is said with its reason, not only by its number
        self.assertNotIn('answers_needed', dry)
        why = {'r2:F1': 'a recurring major problem is closed by a decision'}
        held = self.release(out, final={'issues': ['final_review_r2_unanswered:F1'], 'warnings': [], 'rounds': 2,
                                        'answers_needed': why})
        self.assertEqual((held['ready'], held['answers_needed'], held['release_record']), (False, why, None))
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
        # the master is moved away afterwards: the record stands, and the report says the file is not where it was
        away = Path(out).with_name('moved-away.mp4')
        Path(out).rename(away)
        d = c.deliverable_facts(rd, 1)
        self.assertEqual(d['state'], 'released')
        self.assertTrue(any('no longer at its path: master.mp4' in s for s in d['stale']), d['stale'])
        away.rename(Path(out))
        self.assertFalse([s for s in c.deliverable_facts(rd, 1)['stale'] if 'no longer' in s])
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


class DefectTests(unittest.TestCase):
    """Defects the audit confirmed in the code, each held by a test."""

    @classmethod
    def setUpClass(cls):
        cls.core = load_core('static_studio_core_defects')

    def stops(self, fn, *a, **k):
        """What a command prints when it stops (exit 2)."""
        with mock.patch('sys.stdout', new_callable=io.StringIO) as so:
            with self.assertRaises(SystemExit) as ex:
                fn(*a, **k)
        self.assertEqual(ex.exception.code, 2)
        return json.loads(so.getvalue())

    def test_a_damaged_record_stops_the_command_and_is_named(self):
        # read as "nothing recorded yet", a damaged manifest would re-send (and bill) every narration part, and a
        # damaged lock or budget register would let a second paid job through
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            self.assertEqual(c.read_json(td / 'absent.json'), {})
            (td / 'list.json').write_text('[1, 2]', encoding='utf-8')
            self.assertEqual(c.read_json(td / 'list.json'), {})
            (td / 'bom.json').write_bytes(b'\xef\xbb\xbf{"a": 1}')
            self.assertEqual(c.read_json(td / 'bom.json'), {'a': 1})
            for name, raw in (('cut.json', b'{"status": "partial", "finished_parts": ['), ('empty.json', b''),
                              ('bytes.json', b'\xff\xfe\x00{')):
                (td / name).write_bytes(raw)
                out = self.stops(c.read_json, td / name)
                self.assertIn('is not valid JSON', out['error'])
                self.assertIn('Nothing was changed', out['error'])
                self.assertEqual(out['details']['file'], str(td / name))
            self.assertEqual(self.stops(c.read_json, td / 'absent.json', required=True)['error'], 'Cannot read JSON')
            # through a command: a run whose state is half-written is not taken for "no run here"
            save(td / 'run/state.json', {'schema': c.SCHEMA, 'run_id': 'r'})
            (td / 'run/state.json').write_text('{"schema": ', encoding='utf-8')
            self.assertIn('is not valid JSON', cli('status', '--run', td / 'run', '--look', expected=2)['error'])

    def test_an_unreadable_ledger_row_stops_before_money_is_counted(self):
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            c.ledger_add(rd, {'kind': 'tts', 'ok': True, 'budget': 'B1', 'phase': 'done', 'credits_billed': 100})
            with c.ledger_path(rd).open('a', encoding='utf-8') as f:
                f.write('\n')                                                 # a blank line is not a row
            self.assertEqual(len(c.ledger_rows(rd)), 1)
            self.assertEqual(c.budget_spent(rd, 'B1')[0], 100)
            with c.ledger_path(rd).open('a', encoding='utf-8') as f:
                f.write('{"kind": "tts", "budget": "B1", "phase": "pending", "max_cre\n')     # cut off while writing
            out = self.stops(c.ledger_rows, rd)
            self.assertIn('paid ledger has a row that cannot be read', out['error'])
            self.assertEqual((out['details']['line'], out['details']['text'][:14]), (3, '{"kind": "tts"'))
            self.stops(c.budget_spent, rd, 'B1')                              # never counted as unspent

    def test_a_reference_transcript_is_counted_and_the_narrators_norm_is_found(self):
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            save(rd / '10-media/V001/transcript.json', {'segments': [{'text': 'one two three'}, {'text': 'four five'}, 'x']})
            self.assertEqual(c.transcript_word_count(rd, 'V001'), 5)
            self.assertEqual(c.transcript_word_count(rd, 'V002'), 0)
            # the count is what the analysis sizing uses when the measurements are not there yet (it raised before)
            cfg = {'words_per_image': 500, 'inspect_candidate_weight': 1, 'per_reference_overhead': 2}
            self.assertEqual(c.ref_work(rd, 'V001', {'duration_s': 120, 'has_audio': True}, cfg)['transcript_words'], 5)
            self.assertTrue(callable(c.transcript_words))                     # the word list keeps its own name
            # the narrator's measured pace is read from the voice lock, where it is kept
            save(rd / '40-plans/video-01/length-lock.json', {'pace_wpm': 150, 'per_ref_wpm': {'V001': 148, 'V002': 0}})
            self.assertEqual(c.pace_context(rd, 1), {'target_wpm': 150, 'reference_wpm': [148], 'voice_wpm': None})
            voice = {'voice_id': 'TESTVOICE', 'model_id': 'eleven_v4', 'settings': {}}
            save(c.voice_lock_path(rd, 1), {**voice, 'measured': {**voice, 'wpm': 141.5, 'per_line_overhead_s': 0.42,
                                                                   'words': 420}})
            self.assertEqual(c.pace_context(rd, 1)['voice_wpm'], 141.5)


@fixture_only
class PlanningRules5Tests(base.StaticStudioTests):
    """Planning rules 5 (2026-11-26): the subject is chosen with a look at what already exists and a working promise;
    a script that grew past its first whole draft says what the added lines carry; a key line resting on a claim the
    research did not confirm says how its words carry that; the opening is shown beside the references' hooks. Each
    asks for presence or an accountable answer. None scores anything."""

    NEED_COVERAGE = ('subject_selection_needs_coverage:what_already_exists_on_this_subject_where_you_looked_and_what_'
                     'this_film_adds')
    NEED_PROMISE = 'subject_selection_needs_its_promise:working_title_thumbnail_idea_and_what_the_viewer_expects'

    def test_the_subject_is_chosen_with_an_outward_look_and_a_working_promise(self):
        c = self.load_core()
        ok = {'looked': [{'where': 'YouTube search', 'for': 'the supply order'}],
              'exists': [{'what': 'a battle overview', 'by': 'a history channel', 'how_it_tells_it': 'hour by hour with maps'}],
              'this_film_adds': 'the order itself as the story, read from the ledgers'}
        self.assertEqual(c.coverage_issues(None), [self.NEED_COVERAGE])
        self.assertEqual(c.coverage_issues(ok), [])
        # nothing found is an answer, said in a sentence; a count of what exists decides nothing
        self.assertEqual(c.coverage_issues({**ok, 'exists': [], 'none_found':
                                            'two searches and one archive list show no film about this order'}), [])
        self.assertEqual(c.coverage_issues({**ok, 'exists': ok['exists'] * 40}), [])
        self.assertEqual(c.coverage_issues({**ok, 'exists': []}), [
            'subject_selection_coverage_needs_what_exists_or_why_nothing_was_found:exists[{what,by,how_it_tells_it}]_or_none_found'])
        self.assertEqual(c.coverage_issues({**ok, 'looked': [{'where': 'YouTube'}]}),
                         ['subject_selection_coverage_needs_where_it_looked:looked[{where,for}]'])
        self.assertEqual(c.coverage_issues({**ok, 'exists': [{'what': 'a film', 'how_it_tells_it': 'well'}]}),
                         ['subject_selection_coverage_entry_1_needs_what_it_is_and_how_it_tells_it'])
        self.assertEqual(c.coverage_issues({**ok, 'this_film_adds': 'more depth'}),
                         ['subject_selection_coverage_missing_what_this_film_adds'])
        self.assertEqual(c.selection_promise_issues(None), [self.NEED_PROMISE])
        self.assertEqual(c.selection_promise_issues({'working_title': 'Order', 'thumbnail_idea': 'a clerk',
                                                     'viewer_expects': 'a good story'}),
                         ['subject_selection_promise_missing_working_title', 'subject_selection_promise_missing_thumbnail_idea',
                          'subject_selection_promise_missing_what_the_viewer_expects'])
        # through the lock: a direction without them is not complete; with them it is locked under rules 5
        vd = self.write_plan(lock=False)
        doc = self.direction_doc()
        sel = doc['subject']['selection']
        cov, pr = sel.pop('coverage'), sel.pop('promise')
        save(vd / 'direction.json', doc)
        self.review('treatment', [{'id': 'F1', 'severity': 'minor', 'treatment': 'A', 'problem': 'the quiet middle may wear thin',
                                   'suggestion': 'vary it'}],
                    {'F1': {'action': 'kept', 'note': 'the quiet middle is meant to rest the viewer'}})
        res = cli('direction-lock', '--run', self.run, '--video', 1, expected=2)
        self.assertEqual([x for x in res['details'] if x.startswith('subject_selection_')], [self.NEED_COVERAGE, self.NEED_PROMISE])
        self.assertFalse((vd / 'direction-lock.json').exists())
        self.assertEqual(c.selection_promise(doc), {})
        self.assertEqual(c.selection_promise(self.direction_doc())['working_title'], pr['working_title'])
        # an older direction hears them as advice; one whose subject was chosen again after they existed follows them
        rd = self.home / 'older'
        od = rd / '40-plans/video-01'
        script_side = ['script_grew_17pct_since_its_first_complete_draft:say_what_the_added_lines_carry:plan-check_--grew-for',
                       'key_lines_on_unconfirmed_claims_need_their_wording_answered:L045:claim-wording.json']
        both = [self.NEED_COVERAGE, self.NEED_PROMISE] + script_side

        def left(lock):
            save(od / 'direction-lock.json', lock)
            save(od / 'direction.json', {'decision': {'treatment': 'T1'}, 'subject': {'selection': {'candidate': 'T1'}}})
            issues, warnings = list(both) + ['editorial_review_missing'], []
            c.older_plan_advisory(rd, 1, issues, warnings)
            self.assertEqual(len(issues) + len(warnings), 5)
            return issues
        self.assertEqual(left({'planning_rules': 4}), ['editorial_review_missing'])
        self.assertEqual(left({'planning_rules': 5}), both + ['editorial_review_missing'])
        self.assertEqual(left({'planning_rules': 4, 'planning_migration': {
            'to': 5, 'sections': ['subject.selection.candidate'], 'artifacts': []}}), both[:2] + ['editorial_review_missing'])
        self.assertEqual(left({'planning_rules': 4, 'planning_migration': {
            'to': 5, 'sections': [], 'artifacts': ['script']}}), script_side + ['editorial_review_missing'])
        self.assertEqual(left({'planning_rules': 4, 'planning_migration': {
            'to': 4, 'sections': ['subject.selection.candidate'], 'artifacts': ['script']}}), ['editorial_review_missing'])

    def test_a_script_is_held_to_its_own_first_whole_draft_not_to_the_length(self):
        vd = self.write_plan()
        res = cli('plan-check', '--run', self.run, '--video', 1)
        self.assertTrue(res['ready'], res['issues'])
        self.assertEqual(json.loads((vd / 'direction-lock.json').read_text(encoding='utf-8'))['planning_rules'], 6)
        size = json.loads((vd / 'script-size.json').read_text(encoding='utf-8'))
        self.assertEqual((size['first_complete_draft']['words'], size['first_complete_draft']['locked_s']), (1404, 600))
        self.assertEqual((res['script_size']['now_words'], res['script_size']['grew_pct']), (1404, 0.0))
        self.assertIsNone(res['length_conflict'])

        def resized(n_lines):
            """The script with n_lines lines (the last beat takes what is added or left)."""
            script = json.loads((vd / 'script.json').read_text(encoding='utf-8'))
            one = script['lines'][0]['text']
            script['lines'] = [{'id': f'L{i:03}', 'text': one, 'pause_after_s': 0} for i in range(1, n_lines + 1)]
            save(vd / 'script.json', script)
            bm = json.loads((vd / 'beat-map.json').read_text(encoding='utf-8'))
            bm['beats'][-1]['line_end'] = n_lines
            save(vd / 'beat-map.json', bm)
            return cli('plan-check', '--run', self.run, '--video', 1, expected=None)
        # 61 lines: 17 % over the first whole draft. What the added lines carry is asked; "to reach the length" is
        # refused as an answer before anything is read
        res = resized(61)
        grew = 'script_grew_17pct_since_its_first_complete_draft:say_what_the_added_lines_carry:plan-check_--grew-for'
        self.assertIn(grew, res['issues'])
        self.assertIn('user\'s length decision', cli('plan-check', '--run', self.run, '--video', 1, '--grew-for',
                                                     'to fill', expected=2)['error'])
        res = cli('plan-check', '--run', self.run, '--video', 1, '--grew-for',
                  'the second depot move could not be followed without the two steps added before it', expected=None)
        self.assertFalse([x for x in res['issues'] if x.startswith('script_grew_')], res['issues'])
        self.assertEqual(res['script_size']['growth_answered_up_to_words'], 61 * 27)
        # the first draft stays the measure, and growing well past the answered size asks again
        self.assertTrue(any(x.startswith('script_grew_25pct_') for x in resized(65)['issues']))
        self.assertEqual(json.loads((vd / 'script-size.json').read_text(encoding='utf-8'))['first_complete_draft']['words'], 1404)
        # a script far under the lock: its own size goes to the user before anything is added
        short = resized(40)
        self.assertIn('script_forecast_misses_locked_length_by_over_8pct', short['issues'])
        lc = short['length_conflict']
        self.assertEqual((lc['locked_s'], lc['difference_s'] < 0), (600, True))
        self.assertTrue(lc['what_to_do_first'].startswith('The script as written is the story\'s own size. Take that size '
                                                          'to the user before adding anything'), lc)
        self.assertIn('never to reach a length', lc['what_to_do_first'])
        long_ = resized(70)['length_conflict']
        self.assertTrue(long_['what_to_do_first'].startswith('The script runs longer than the lock. Cut what a listener '
                                                             'would drift through first'), long_)

    def test_a_key_line_on_an_unconfirmed_claim_says_how_its_words_carry_it(self):
        c = self.load_core()
        vd = self.write_plan()
        self.assertTrue(cli('plan-check', '--run', self.run, '--video', 1)['ready'])
        self.assertFalse((vd / 'claim-wording.json').exists())                 # nothing to answer: no file is made
        # the "likely" claim is tied to a line of the key moment (the last beat, L041-L052)
        cp = self.run / '30-research/video-01/claims.json'
        claims = json.loads(cp.read_text(encoding='utf-8'))
        claims['claims'][1]['line_refs'] = ['L045']
        save(cp, claims)
        res = cli('plan-check', '--run', self.run, '--video', 1, expected=2)
        need = 'key_lines_on_unconfirmed_claims_need_their_wording_answered:L045:claim-wording.json'
        self.assertIn(need, res['issues'])
        self.assertEqual(res['creative']['claim_wording']['why'], {'L045': 'not answered'})
        wp = vd / 'claim-wording.json'
        doc = json.loads(wp.read_text(encoding='utf-8'))
        entry = doc['answers']['L045']
        self.assertEqual((entry['beat'], entry['claims'], entry['how']),
                         ('B05', [{'id': 'C02', 'confidence': 'likely', 'note': ''}], ''))
        self.assertIn('key_moment:B05', entry['carries'])
        self.assertIn('ending', entry['carries'])

        def answered(**a):
            d = json.loads(wp.read_text(encoding='utf-8'))
            d['answers']['L045'].update({'how': '', 'words': '', 'in_line': '', 'why': ''}, **a)
            save(wp, d)
            return c.claim_wording_facts(self.run, 1)['why'].get('L045')
        self.assertEqual(answered(how='plain', why='it is fine'), '"plain" needs why it is safe to say without a qualifier')
        self.assertEqual(answered(how='softened'), '"how" must be hedged or plain')
        # a quoted hedge has to be in the line as written: no word list decides what counts as a hedge
        self.assertEqual(answered(how='hedged', words='the records suggest'), 'the words quoted are not in L045 as it is written')
        self.assertIsNone(answered(how='hedged', words='careful planning and real consequences'))
        self.assertIsNone(answered(how='hedged', words='Careful  planning', in_line='L044'))     # an earlier line of its beat
        self.assertEqual(answered(how='hedged', words='careful planning', in_line='L010'),
                         '"in_line" must be this line or an earlier line of its beat (L041-L045)')
        self.assertIsNone(answered(how='plain', why='the line states only the part the survey sheet itself shows'))
        self.assertNotIn(need, cli('plan-check', '--run', self.run, '--video', 1, expected=None)['issues'])
        # the line is reworded: the answer was for other words, so it is kept as superseded and asked again
        script = json.loads((vd / 'script.json').read_text(encoding='utf-8'))
        script['lines'][44]['text'] = 'The surviving sheet suggests the valley was drawn a mile too far north of the real one.'
        save(vd / 'script.json', script)
        self.assertEqual(c.claim_wording_facts(self.run, 1)['why'],
                         {'L045': 'the line was reworded since this answer: answer for the words it has now'})
        self.assertIn(need, cli('plan-check', '--run', self.run, '--video', 1, expected=2)['issues'])
        doc = json.loads(wp.read_text(encoding='utf-8'))
        self.assertEqual((doc['answers']['L045']['how'], doc['superseded'][0]['line'], doc['superseded'][0]['how']),
                         ('', 'L045', 'plain'))
        self.assertIsNone(answered(how='hedged', words='the surviving sheet suggests'))
        # a claim that gets its second source needs no answer at all
        claims['claims'][1]['confidence'] = 'confirmed'
        save(cp, claims)
        self.assertEqual(c.claim_wording_facts(self.run, 1)['lines'], 0)

    def test_the_opening_is_shown_beside_the_references_hooks(self):
        c = self.load_core()
        vd = self.write_plan(review_script=False)
        lines = json.loads((vd / 'script.json').read_text(encoding='utf-8'))['lines']
        clock = c.line_clock(lines, 145)
        self.assertEqual(clock['L001'], (0.0, 11.2))                           # 27 words at 145 wpm
        self.assertEqual(clock['L002'][0], 11.6)                               # and the voice's gap after the line
        self.assertEqual(c.opening_facts(self.run, 1, lines, 145), ({}, None))  # no reader yet: nothing is said

        def read_by_a_reader(promise, expected=0):
            packet = cli('review-packet', '--run', self.run, '--video', 1, '--kind', 'script')
            self.assertIn('"clear_at"', Path(packet['packet']).read_text(encoding='utf-8'))
            save(Path(packet['findings_file']), {'reviewer': 'test reader', 'findings': [], 'promise': promise,
                                                 'developments': self.clear_development('script')})
            return cli('review-record', '--run', self.run, '--video', 1, '--kind', 'script', expected=expected)
        told = {'promised': 'to understand the decision and what it cost', 'first_delivered': 'L006', 'waiting': []}
        bad = read_by_a_reader({**told, 'clear_at': 'near the start'}, expected=2)
        self.assertIn('promise: "clear_at" must be a line of the script (L005) or "never"', bad['details'])
        read_by_a_reader({**told, 'clear_at': 'L004'})
        facts, said = c.opening_facts(self.run, 1, lines, 145)
        self.assertEqual((facts['clear_at_line'], facts['clear_at_s'], facts['first_delivered_line'], facts['first_delivered_s']),
                         ('L004', 45.9, 'L006', 57.9))
        self.assertEqual((facts['working_title'], facts['reference_hooks_end_s'], said),
                         ('The Order That Won the Battle', {}, None))           # no hook measured: nothing to stand beside
        # the references this direction cites made their promise by 0:20 and 0:35: a look is asked, never a change
        for ref, end in (('V001', 20), ('V002', 35)):
            p = self.run / f'20-analysis/cards/{ref}.json'
            card = json.loads(p.read_text(encoding='utf-8'))
            card['hook'] = {'end_s': end}
            save(p, card)
        facts, said = c.opening_facts(self.run, 1, lines, 145)
        self.assertEqual(facts['reference_hooks_end_s'], {'V001': 20.0, 'V002': 35.0})
        self.assertTrue(said.startswith('opening: the latest reader knew what the video offers by L004, about 00:46 in'), said)
        self.assertIn('V001 00:20, V002 00:35', said)
        res = cli('plan-check', '--run', self.run, '--video', 1, expected=None)
        self.assertEqual(res['creative']['opening']['clear_at_line'], 'L004')
        self.assertTrue(any(w.startswith('opening: the latest reader knew') for w in res['warnings']), res['warnings'])
        self.assertFalse([x for x in res['issues'] if 'opening' in x], res['issues'])
        # a reader who was clear inside the references' range: the facts stay, nothing is said
        card['hook'] = {'end_s': 50}
        save(p, card)
        self.assertIsNone(c.opening_facts(self.run, 1, lines, 145)[1])


class SoundReviewTests(unittest.TestCase):
    """The sound of a cut, measured: each piece of music against the voice where it plays, by the project's own files
    and in the finished file, a sound cut off between two lines, the air at a turn, a silence nobody listened to, a
    name heard differently; and the listening sheet for a person (2026-11-26: a finished film had been checked by
    records and one whole-film figure, and nobody had measured or been asked to listen to any of this)."""

    # six lines of "voice": a tone that stops between lines (seconds on the edit's clock)
    T = [(0.5, 5.5), (6.0, 11.0), (11.5, 16.5), (19.5, 24.5), (27.5, 33.5), (35.5, 39.5)]
    WORDS = [10, 10, 10, 10, 24, 9]

    @classmethod
    def setUpClass(cls):
        cls.core = load_core('static_studio_core_sound')

    def ff(self, *args):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True)

    def tone(self, out, hz, seconds, volume='1'):
        self.ff('-f', 'lavfi', '-i', f'sine=frequency={hz}:sample_rate=44100:duration={seconds}', '-af',
                f"volume='{volume}':eval=frame", '-ac', 1, out)
        return out

    def mixed(self, name, bed_b_gain=1.0):
        """What an export would play: the voice, both beds and the effect where the project places them."""
        out = self.td / name
        self.ff('-i', self.narr, '-i', self.bed_a, '-i', self.bed_b, '-i', self.hit, '-filter_complex',
                f'[2]atrim=0:12,volume={bed_b_gain},adelay=22000[b];[3]adelay=17000[h];'
                '[0][1][b][h]amix=inputs=4:normalize=0:duration=first', '-ac', 1, out)
        return out

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.td = Path(self._t.name)
        rd = self.rd = self.td / 'run'
        c = self.core
        ed, vd, au = rd / '70-edit/video-01', rd / '40-plans/video-01', rd / '50-audio/video-01'
        for d in (ed, vd, au):
            d.mkdir(parents=True)
        save(rd / 'state.json', {'schema': c.SCHEMA, 'run_id': 'r'})
        speaking = '+'.join(f'between(t,{a},{b})' for a, b in self.T)
        self.narr = self.tone(au / 'narration-edit.wav', 220, 40, f'if({speaking},1,0)')
        self.bed_a = self.tone(ed / 'bed-a.wav', 440, 12, '0.1')          # 20 dB under the voice, its whole file placed
        self.bed_b = self.tone(ed / 'bed-b.wav', 330, 30, '0.316')        # 10 dB under, cut off 18 s before its end
        self.hit = self.tone(ed / 'hit.wav', 900, 0.5, '0.5')
        self.tracks = [
            {'kind': 'narration', 'file': str(self.narr), 'start_s': 0, 'end_s': 40, 'source_start_s': 0,
             'source_end_s': 40, 'speed': 1, 'volume': 1},
            {'kind': 'music', 'file': str(self.bed_a), 'start_s': 0, 'end_s': 12, 'beats': ['B01'], 'volume': 1},
            {'kind': 'music', 'file': str(self.bed_b), 'start_s': 22, 'end_s': 34, 'beats': ['B03'], 'volume': 1},
            {'kind': 'sfx', 'file': str(self.hit), 'start_s': 17.0, 'end_s': 17.5, 'beats': ['B02'], 'volume': 1}]
        save(ed / 'timeline.json', {'audio_tracks': self.tracks})
        save(ed / 'edit-plan.json', {'narration_for_edit': {'file': str(self.narr)}, 'holds': []})
        save(vd / 'script.json', {'lines': [
            {'id': f'L00{i}', 'text': f'Line {i} of the film says something plain about Qin and the river.'}
            for i in range(1, 7)]})
        save(vd / 'beat-map.json', {'beats': [
            {'id': 'B01', 'line_start': 1, 'line_end': 2, 'chapter_start': True},
            {'id': 'B02', 'line_start': 3, 'line_end': 4, 'chapter_start': True},
            {'id': 'B03', 'line_start': 5, 'line_end': 6, 'key_moment': 'the letter is opened'}]})
        gaps = [(b, self.T[i + 1][0]) for i, (a, b) in enumerate(self.T[:-1])] + [(39.5, 40.0)]
        save(au / 'line-times.json', {
            'lines': [{'id': f'L00{i + 1}', 'start_s': a, 'end_s': b, 'words': self.WORDS[i], 'gap_span_s': list(gaps[i])}
                      for i, (a, b) in enumerate(self.T)],
            'pronunciation_heard': [{'term': 'Qin', 'line': 'L002', 'heard_as_written': False, 'nearest_heard': 'kin'},
                                    {'term': 'river', 'line': 'L002', 'heard_as_written': True},
                                    # a possessive, and a name heard as its planned respelling: the voice said both
                                    {'term': 'Jing', 'line': 'L003', 'heard_as_written': False, 'nearest_heard': 'jings'},
                                    {'term': 'Zhong', 'line': 'L004', 'heard_as_written': False, 'nearest_heard': 'jong'}]})
        save(vd / 'pronunciation.json', {'terms': [{'term': 'Qin', 'say': 'chin'}, {'term': 'Zhong', 'say': 'Jong'}]})
        save(vd / 'holds.json', {'decisions': {
            'L003': {'line': 'L003', 'total_s': 3.0, 'no_hold': False, 'listened': None},
            'L004': {'line': 'L004', 'total_s': 3.0, 'no_hold': False, 'listened': 'I heard it and it works'},
            'L005': {'line': 'L005', 'total_s': None, 'no_hold': True, 'listened': None}}})

    def tearDown(self):
        self._t.cleanup()

    def placed(self, res_or_rec, name):
        return next(p for p in res_or_rec['placements'] if p['file'] == name)

    def test_each_sound_is_measured_against_the_voice_where_it_plays(self):
        c, rd = self.core, self.rd
        res = cli('sound-review', '--run', rd, '--video', 1)
        rec = json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8'))
        a, b = self.placed(rec, 'bed-a.wav'), self.placed(rec, 'bed-b.wav')
        self.assertLess(abs(a['under_voice_db'] - 20), 1.0, a)
        self.assertLess(abs(b['under_voice_db'] - 10), 1.0, b)
        self.assertEqual((a['stops_early_s'], a['cut_while_sounding']), (0.0, False))
        self.assertEqual((b['stops_early_s'], b['cut_while_sounding'], b['end_between_lines']), (18.0, True, True))
        self.assertLess(abs(b['in_the_clear_s'] - 3.5), 0.3, b)                       # 24.5-27.5 and 33.5-34.0
        self.assertNotIn('in_export', b)
        self.assertLess(abs(res['music_under_voice_db']['quietest'] - 20), 1.0)
        self.assertLess(abs(res['music_under_voice_db']['least_quiet'] - 10), 1.0)
        self.assertTrue(any('bed-b.wav stops at 00:34' in x for x in res['look_at']), res['look_at'])
        self.assertTrue(res['measured_in'].startswith('the project\'s own files only'), res['measured_in'])
        # the turns: the chapter's first line beside the film's ordinary gap; the key moment is listed too
        turns = {t['next']: t for t in res['turns']}
        self.assertEqual((turns['L003']['why'], turns['L003']['gap_s']), ('chapter', 0.5))
        self.assertEqual((turns['L005']['why'], turns['L005']['gap_s']), ('key moment', 3.0))
        self.assertEqual(res['names_heard_differently'], ['Qin'])
        self.assertEqual([(d['uses'], d['recognised'], d['line']) for d in rec['names']], [(1, 0, 'L002')])
        self.assertEqual((res['music_share_of_runtime'], res['no_music_for_long'], res['ambience_share_of_runtime']),
                         (0.6, [], 0.0))
        self.assertIsNone(res['file_against_project'])
        self.assertEqual(res['holds_not_listened'], 1)
        self.assertEqual(rec['holds_not_listened'], [{'line': 'L003', 'from_s': 16.5, 'to_s': 19.5, 'total_s': 3.0}])
        self.assertEqual(rec['pace']['fastest'][0]['line'], 'L005')
        self.assertNotIn('line_marks', rec)
        # the listening sheet: a short list of places to listen, each with one question and an empty answer
        kinds = [i['kind'] for i in rec['listening_items']]
        for k in ('voice', 'key moment', 'name', 'music', 'sound stop', 'turn', 'silence', 'pace'):
            self.assertIn(k, kinds)
        self.assertEqual(kinds.count('music'), 2)
        self.assertEqual([i['id'] for i in rec['listening_items']], [f'H{k}' for k in range(1, len(kinds) + 1)])
        sheet = c.listening_sheet_path(rd, 1)
        text = sheet.read_text(encoding='utf-8')
        self.assertIn('| H1 | 00:00-00:25 | voice |', text)
        self.assertIn('Is "Qin" said the way you want?', text)
        self.assertIn('planned as "chin"; the transcript heard "kin"', text)
        filled = json.loads(sheet.with_suffix('.json').read_text(encoding='utf-8'))
        self.assertEqual({i['answer'] for i in filled['items']}, {''})
        # what a reviewer who cannot hear is given: times, kinds and levels, no file names, no purposes
        rows = '\n'.join(c.sound_rows(rec))
        self.assertRegex(rows, r'- 00:00-00:12: music, (19|20|21)(\.\d)? dB under the voice')
        self.assertIn('- sound effects at: 00:17', rows)
        self.assertIn('- a sound stops at 00:34, cut before its end, between two lines', rows)
        self.assertNotIn('bed-', rows)
        self.assertNotIn('.wav', rows)

    def test_the_finished_file_is_measured_and_a_review_answers_for_its_build_and_its_file(self):
        c, rd = self.core, self.rd
        ok = self.mixed('export.wav')
        self.assertEqual(c.sound_review_state(rd, 1)[:12], 'not_reviewed')
        res = cli('sound-review', '--run', rd, '--video', 1, '--file', ok)
        rec = json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8'))
        for name, want in (('bed-a.wav', 20), ('bed-b.wav', 10)):
            x = self.placed(rec, name)['in_export']
            self.assertLess(abs(x['under_voice_db'] - want), 1.5, x)
            self.assertLess(abs(x['differs_db']), 1.5, x)
        self.assertEqual(res['measured_in'], 'export.wav')
        self.assertFalse([x for x in res['look_at'] if 'export.wav plays' in x], res['look_at'])
        self.assertGreaterEqual(res['file_against_project']['passages_measured'], 2)
        self.assertLess(res['file_against_project']['largest_difference_db'], 1.5)
        self.assertIn('the finished file', '\n'.join(i['measured'] for i in rec['listening_items']))
        sha = c.file_sha256(ok)
        self.assertEqual(rec['export']['sha256'], sha)
        self.assertIsNone(c.sound_review_state(rd, 1))
        self.assertIsNone(c.sound_review_state(rd, 1, sha))
        # another file of the same build has not been measured
        loud = self.mixed('louder.wav', bed_b_gain=4.0)
        self.assertEqual(c.sound_review_state(rd, 1, c.file_sha256(loud)), 'not_measured_in_this_file:run_sound-review_--file_on_it')
        # a file that plays a bed 12 dB louder than the project's files ask: said as a place to look, with both figures
        res = cli('sound-review', '--run', rd, '--video', 1, '--file', loud)
        x = self.placed(json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8')), 'bed-b.wav')['in_export']
        self.assertLess(abs(x['differs_db'] + 12), 2.0, x)
        self.assertTrue(any('bed-b.wav' in s and 'louder.wav plays this passage 1' in s and 'louder' in s
                            for s in res['look_at']), res['look_at'])
        rows = '\n'.join(c.sound_rows(json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8'))))
        self.assertRegex(rows, r'- 00:22-00:34: music, \S+ dB under the voice \(the finished file plays this passage '
                               r'1\d(\.\d)? dB louder than the project asks\)')
        # a sound moved in the project: the review answers for an earlier build
        self.tracks[2]['start_s'], self.tracks[2]['end_s'] = 23, 35
        save(rd / '70-edit/video-01/timeline.json', {'audio_tracks': self.tracks})
        self.assertEqual(c.sound_review_state(rd, 1)[:36], 'reviewed_for_an_earlier_build_of_the')

    def test_a_finished_run_is_only_read_with_out(self):
        rd = self.rd
        before = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in rd.rglob('*') if p.is_file()}
        out = self.td / 'elsewhere'
        res = cli('sound-review', '--run', rd, '--video', 1, '--out', out)
        self.assertEqual({p: (p.stat().st_size, p.stat().st_mtime_ns) for p in rd.rglob('*') if p.is_file()}, before)
        self.assertTrue((out / 'sound-review.json').is_file())
        self.assertTrue((out / 'listening-sheet.md').is_file())
        self.assertTrue((out / 'listening-sheet.json').is_file())
        self.assertEqual(Path(res['listening_sheet']).parent, out.resolve())
        # no narration to measure against: said, nothing written
        (rd / '50-audio/video-01/narration-edit.wav').unlink()
        bad = cli('sound-review', '--run', rd, '--video', 1, '--out', self.td / 'none', expected=2)
        self.assertIn('No narration of the edit', bad['error'])
        self.assertFalse((self.td / 'none').exists())

    def test_long_stretches_without_music_and_a_clip_volume_are_facts(self):
        ar = self.core._audio_review()
        placed = [{'kind': 'music', 'start_s': 10, 'end_s': 40}, {'kind': 'ambience', 'start_s': 40.2, 'end_s': 60},
                  {'kind': 'sfx', 'start_s': 70, 'end_s': 71}, {'kind': 'music', 'start_s': 200, 'end_s': 230}]
        beds = ar.beds_by_kind(placed, 300)              # music and ambience apart: a room tone is not music
        self.assertEqual(beds['music']['plays'], [[10, 40], [200, 230]])
        self.assertEqual(beds['music']['none_for_long'], [[40, 200], [230, 300]])
        self.assertEqual(beds['music']['share_of_runtime'], 0.2)
        self.assertEqual((beds['ambience']['plays'], beds['ambience']['share_of_runtime']), ([[40.2, 60]], 0.07))
        # a level set in the project instead of the file is carried into the figure and named
        voice = ar.voice_profile(self.narr)
        half = ar.placement_facts({**self.tracks[1], 'volume': 0.5}, voice)
        self.assertEqual(half['clip_volume'], 0.5)
        self.assertLess(abs(half['under_voice_db'] - 26), 1.0, half)
        # a placement that starts inside its file is read from there
        late = ar.placement_facts({**self.tracks[2], 'source_start_s': 18.0}, voice)
        self.assertEqual(late['stops_early_s'], 0.0)

    def test_sounds_that_play_together_are_compared_together_and_a_room_tone_is_not_music(self):
        """Found on the first real film (2026-11-26, 51 sounds): a room tone under everything made each faint sound
        over it read as a wrong level in the finished file, read its own end at the film's last frame as a cut-off
        between two lines, and hid every stretch without music."""
        c, rd = self.core, self.rd
        ed = rd / '70-edit/video-01'
        floor = self.tone(ed / 'floor.wav', 150, 50, '0.0316')       # 30 dB under: a 50 s file under the whole 40 s film
        faint = self.tone(ed / 'faint.wav', 440, 12, '0.01')         # 40 dB under: heard alone in no file
        save(ed / 'timeline.json', {'audio_tracks': [
            self.tracks[0],
            {'kind': 'ambience', 'file': str(floor), 'start_s': 0, 'end_s': 40, 'volume': 1},
            {'kind': 'music', 'file': str(faint), 'start_s': 0, 'end_s': 12, 'volume': 1}]})
        export = self.td / 'export.wav'
        self.ff('-i', self.narr, '-i', floor, '-i', faint, '-filter_complex',
                '[1]atrim=0:40[f];[0][f][2]amix=inputs=3:normalize=0:duration=first', '-ac', 1, export)
        res = cli('sound-review', '--run', rd, '--video', 1, '--file', export)
        rec = json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8'))
        f, m = self.placed(rec, 'floor.wav'), self.placed(rec, 'faint.wav')
        # the faint music alone asks for 40 dB under the voice; with the room tone the two ask for about 29.6 together,
        # and that is what the file plays
        self.assertLess(abs(m['under_voice_db'] - 40), 1.0, m)
        self.assertLess(abs(m['in_export']['project_asks_db'] - 29.6), 1.0, m)
        self.assertLess(abs(m['in_export']['differs_db']), 1.5, m)
        self.assertFalse([x for x in res['look_at'] if 'plays this passage' in x], res['look_at'])
        # the room tone runs to the film's last frame: cut before its file ends, with the film, not between two lines
        self.assertEqual((f['stops_early_s'], f['cut_while_sounding'], f.get('ends_with_the_film')), (10.0, True, True))
        self.assertFalse([x for x in res['look_at'] if 'stop' in x], res['look_at'])
        kinds = [i['kind'] for i in rec['listening_items']]
        self.assertNotIn('sound stop', kinds)
        # music and ambience are counted apart, and the sheet asks about the words where the least quiet sound is
        self.assertEqual((res['music_share_of_runtime'], res['ambience_share_of_runtime']), (0.3, 1.0))
        self.assertIn('ambience', kinds)
        self.assertIn('Does the ambience get in the way of the words here?', c.listening_sheet_path(rd, 1).read_text(encoding='utf-8'))
        rows = '\n'.join(c.sound_rows(rec))
        self.assertRegex(rows, r'- 00:00-00:40: ambience, (29|30|31)(\.\d)? dB under the voice')
        self.assertNotIn('a sound stops', rows)
        self.assertNotIn('no music from', rows)                 # 28 s without music: under the 45 s that is listed
        # no music at all: said in one row, not as one long stretch
        save(ed / 'timeline.json', {'audio_tracks': [self.tracks[0], {'kind': 'ambience', 'file': str(floor),
                                                                    'start_s': 0, 'end_s': 40, 'volume': 1}]})
        cli('sound-review', '--run', rd, '--video', 1)
        rows = c.sound_rows(json.loads(c.sound_review_path(rd, 1).read_text(encoding='utf-8')))
        self.assertIn('- no music in this cut', rows)

    def test_a_name_said_as_planned_is_not_listed_as_heard_differently(self):
        c = self.core
        rows = ([{'term': 'Qin', 'line': 'L001', 'heard_as_written': True}] * 3
                + [{'term': 'Qin', 'line': 'L004', 'heard_as_written': False, 'nearest_heard': 'qins'},
                   {'term': 'Zhong', 'line': 'L005', 'heard_as_written': False, 'nearest_heard': 'jong'},
                   {'term': 'Chen Sheng', 'line': 'L006', 'heard_as_written': False, 'nearest_heard': 'chun'},
                   {'term': 'Hei Fu', 'line': 'L002', 'heard_as_written': True}]
                + [{'term': 'Hei Fu', 'line': f'L01{k}', 'heard_as_written': False, 'nearest_heard': 'hefu'} for k in range(3)]
                + [{'term': 'Yuan', 'line': 'L020', 'heard_as_written': False, 'nearest_heard': 'a'},
                   {'term': 'Yuan', 'line': 'L021', 'heard_as_written': False, 'nearest_heard': None}])
        pron = {'Qin': {'say': 'Chin'}, 'Zhong': {'say': 'Jong'}, 'Chen Sheng': {'say': 'Chun Shung'},
                'Hei Fu': {'say': 'Hay Foo'}, 'Yuan': {'say': 'Yoo-en'}}
        got = c.names_to_listen_for(rows, pron)
        # never recognised first, then the least recognised; a possessive and a planned respelling are not listed
        self.assertEqual([(d['term'], d['recognised'], d['uses'], d['line']) for d in got],
                         [('Yuan', 0, 2, 'L020'), ('Hei Fu', 1, 4, 'L010')])
        self.assertEqual((got[1]['heard'], got[1]['say'], got[1]['nearest_heard']), (['hefu'], 'Hay Foo', 'hefu'))
        # a nearest word that is nothing like the name is the transcript's noise: kept, not shown as what was heard
        self.assertEqual((got[0]['heard'], got[0]['nearest_heard']), (['a'], None))
        ar = c._audio_review()
        item = next(i for i in ar.listening_items({'duration_s': 30.0, 'names': got, 'line_marks': {
            'L020': {'start': 5.0, 'end': 8.0}, 'L010': {'start': 12.0, 'end': 15.0}}}) if 'Yuan' in i['question'])
        self.assertEqual(item['measured'],
                         'planned as "Yoo-en"; the transcript heard nothing near it (recognised in 0 of its 2 uses)')

    def test_the_sheet_asks_about_the_words_only_where_words_are(self):
        ar = self.core._audio_review()
        base = {'in_the_clear_s': 1.0, 'longest_clear_s': None}
        facts = {'duration_s': 100.0, 'placements': [
            {**base, 'kind': 'music', 'file': 'theme.bed-m20dB.from0s-10s.wav', 'start_s': 10.0, 'end_s': 20.0,
             'under_voice_db': 22.0, 'voice_over_it_share': 0.9},
            # a swell inside a silence: the loudest music of the film, with no words under it
            {**base, 'kind': 'music', 'file': 'swell.wav', 'start_s': 40.0, 'end_s': 44.0, 'under_voice_db': 8.0,
             'voice_over_it_share': 0.1},
            {**base, 'kind': 'music', 'file': 'far.wav', 'start_s': 60.0, 'end_s': 70.0, 'under_voice_db': 35.0,
             'voice_over_it_share': 1.0},
            {**base, 'kind': 'ambience', 'file': 'room.wav', 'start_s': 0.0, 'end_s': 100.0, 'under_voice_db': 31.0,
             'voice_over_it_share': 0.8, 'cut_while_sounding': True, 'end_between_lines': True,
             'ends_with_the_film': True, 'stops_early_s': 9.0}]}
        items = ar.listening_items(facts)
        said = '\n'.join(f'{i["kind"]}: {i["question"]} {i["measured"]}' for i in items)
        self.assertIn('music: Does the music get in the way of the words here? "theme": 22 dB under the voice', said)
        self.assertNotIn('swell', said)
        self.assertIn('"far": 35 dB under the voice', said)
        self.assertNotIn('finished file', said)                 # none was measured: nothing is said of one
        self.assertNotIn('sound stop', [i['kind'] for i in items])
        self.assertIn('ambience still sounding at the film\'s last frame', said)


if __name__ == '__main__':
    unittest.main()
