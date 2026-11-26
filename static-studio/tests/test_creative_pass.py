"""The creative pass of 2026-11-26. No paid API calls.

What a finished film is limited by is decided early and tested late. These tests cover the places where the pipeline
now makes a creative decision with evidence in hand, or tests it on fresh eyes before money is spent: the story sets
the length; the opening is chosen among several; the film is read on one page; the models' measured habits stand
beside the film's; the bed breathes; the pictures are counted. The code gathers facts and asks for an accountable
answer: nothing here scores or decides a creative question. The fixtures are test_static_core's."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_static_core as base                                    # noqa: E402
from test_static_core import cli, save                             # noqa: E402
from test_audit_impl import fixture_only                           # noqa: E402

PACE = ('--pace-wpm', 145, '--pace-why', 'the test narrator reads at this pace')
NEEDS_SIZE = ('subject_candidate_T1_runtime_needs_its_natural_size:natural_minutes_[low,high]_how_long_this_material_'
              'runs_when_told_well')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


@fixture_only
class StoryLengthTests(base.StaticStudioTests):
    """The story sets the length (the audit of 2026-11-26: a length was fixed with the subject, before any treatment;
    the research was sent back to fill it, and the filled stretch became the film's slow middle)."""

    MINOR = [{'id': 'F1', 'severity': 'minor', 'treatment': 'A', 'problem': 'the quiet middle may wear thin',
              'suggestion': 'vary it'}]
    KEPT = {'F1': {'action': 'kept', 'note': 'the quiet middle is meant to rest the viewer'}}

    def length(self, *more, expected=0):
        return cli('length', '--run', self.run, '--video', 1, '--mode', 'story', *more, expected=expected)

    def planned(self, natural=(8, 12)):
        """A run up to the treatment decision with no length locked: the niche, the user's choice that the story
        decides, the measured references and direction.json."""
        self.lock_niche()
        first = self.length()
        self.measure_refs()
        vd = self.run / '40-plans/video-01'
        doc = self.direction_doc()
        doc['subject']['candidates'][0]['runtime']['natural_minutes'] = list(natural)
        save(vd / 'direction.json', doc)
        return vd, doc, first

    def test_the_subject_states_its_own_size(self):
        c = self.load_core()
        self.assertEqual(c.natural_minutes({'natural_minutes': [9, 11.5]}), (9.0, 11.5))
        for bad in ([11, 9], [0, 5], [9], '12', 12, None, ['nine', 'ten'], [9, 10, 11]):
            self.assertIsNone(c.natural_minutes({'natural_minutes': bad}), bad)
        self.assertIsNone(c.natural_minutes(None))
        # a subject with no size of its own is not complete; an older direction hears that as advice
        vd = self.write_plan(lock=False)
        doc = self.direction_doc()
        doc['subject']['candidates'][0]['runtime'].pop('natural_minutes')
        save(vd / 'direction.json', doc)
        self.assertIn(NEEDS_SIZE, c.direction_facts(self.run, 1)['issues'])
        save(vd / 'direction-lock.json', {'planning_rules': 5})
        facts = c.direction_facts(self.run, 1)
        self.assertNotIn(NEEDS_SIZE, facts['issues'])
        self.assertTrue(any(w.startswith('advisory') and NEEDS_SIZE in w for w in facts['warnings']), facts['warnings'])

    def test_the_story_sets_the_length(self):
        vd, doc, first = self.planned()
        # the user's choice is on record before the subject is known, and nothing is locked yet
        self.assertEqual((first['locked'], first['mode']), (False, 'story'))
        self.assertFalse((vd / 'length-lock.json').exists())
        self.assertEqual(read(vd / 'length-intent.json')['mode'], 'story')
        self.assertEqual(cli('status', '--run', self.run, '--look')['videos']['1']['stage'], 'planning')
        # the treatments are compared with no length fixed: each shows its own size, and the reader is asked about it
        packet, _rec = self.review('treatment', self.MINOR, self.KEPT)
        text = Path(packet['packet']).read_text(encoding='utf-8')
        self.assertIn('Its length is not fixed yet', text)
        self.assertIn('### How it unfolds (about 10 min in all)', text)
        self.assertIn('"length_feels"', text)
        self.assertNotIn('About 10 minutes', text)
        self.assertNotIn('{', text.split('Write your answer as JSON')[0])      # every placeholder was filled
        self.assertTrue(read(vd / 'reviews/packet-treatment-r1.json')['length_open'])
        # a direction is locked with its length beside it
        res = cli('direction-lock', '--run', self.run, '--video', 1, expected=2)
        self.assertTrue(res['error'].startswith('Lock the length before the direction'), res)
        self.assertEqual(res['details']['story_size']['treatments_minutes'], {'T1': 10.0, 'T2': 10.0})
        # the same command now locks the chosen treatment's own movements, at the pace of the narrators the decision
        # calls relevant; minutes are not given on a first lock
        self.length('--minutes', 12, *PACE, expected=2)
        lock = self.length(*PACE)
        self.assertEqual((lock['locked_target_s'], lock['references']), (600, ['V001', 'V002']))
        self.assertEqual(lock['story_size'], {'treatment': 'T1', 'movements_minutes': 10.0, 'candidate': 'T1',
                                              'natural_minutes': [8, 12]})
        ll = read(vd / 'length-lock.json')
        self.assertEqual((ll['mode'], ll['rule']), ('story', self.load_core().STORY_LENGTH_RULE))
        self.assertTrue(cli('direction-lock', '--run', self.run, '--video', 1)['ok'])
        self.assertEqual(read(vd / 'direction-lock.json')['planning_rules'], 6)

    def test_a_story_length_follows_the_written_story_until_something_is_recorded(self):
        vd, _doc, _first = self.planned()
        self.review('treatment', self.MINOR, self.KEPT)
        self.length(*PACE)
        # never silently: a re-lock says why; then it is the director's to do, and the old lock stays on record
        res = self.length('--minutes', 9, *PACE, expected=2)
        self.assertIn('re-lock it to the story\'s real size', res['details']['action'])
        why = 'the first whole draft runs nine minutes with every beat delivered'
        again = self.length('--minutes', 9, '--revise', why, *PACE)
        self.assertEqual(again['locked_target_s'], 540)
        ll = read(vd / 'length-lock.json')
        self.assertEqual((len(ll['history']), ll['history'][0]['target_length_s'], ll['revised_because']), (1, 600, why))
        self.assertEqual((ll['approved_by_user'], ll['revised_by']),
                         ('', 'the director: the story sets this length and nothing was recorded yet'))
        # once narration is recorded, a new length is the user's decision again
        save(self.run / '50-audio/video-01/manifest.json', {'status': 'partial', 'finished_parts': []})
        trim = 'a slow part showed only in the recording and was cut'
        res = self.length('--minutes', 8.5, '--revise', trim, *PACE, expected=2)
        self.assertIn('user\'s own approval', res['error'])
        ok = self.length('--minutes', 8.5, '--revise', trim, '--user-approved', 'yes, eight and a half is fine', *PACE)
        self.assertEqual(ok['locked_target_s'], 510)
        self.assertNotIn('revised_by', read(vd / 'length-lock.json'))

    def test_a_length_outside_the_subjects_own_size_is_answered(self):
        vd, _doc, _first = self.planned(natural=(12, 14))
        self.review('treatment', self.MINOR, self.KEPT)
        # the chosen treatment runs ten minutes and the subject was judged twelve to fourteen: one of them is wrong
        facts = self.load_core().direction_facts(self.run, 1)
        self.assertTrue(any('one of the two is wrong' in w for w in facts['warnings']), facts['warnings'])
        self.assertEqual(facts['story_size']['natural_minutes'], [12, 14])
        res = self.length(*PACE, expected=2)
        self.assertEqual((res['details']['natural_minutes'], res['details']['length_minutes']), ([12, 14], 10.0))
        why = 'the treatment leaves out the second campaign, which the range still counted'
        self.assertEqual(self.length('--why', why, *PACE)['story_size']['why'], why)

    def test_a_length_the_user_asked_for_is_weighed_against_the_story(self):
        vd = self.write_plan(lock=False)                 # Standard: ten minutes, locked before the subject
        doc = self.direction_doc()
        doc['subject']['candidates'][0]['runtime']['natural_minutes'] = [12, 14]
        save(vd / 'direction.json', doc)
        c = self.load_core()
        need = ('subject_natural_size_12-14_min_is_not_the_locked_10_min:choose_another_candidate_or_angle_or_record_'
                'the_users_decision_in_runtime_decision:never_pad_never_squeeze')
        self.assertIn(need, c.direction_facts(self.run, 1)['issues'])
        doc['subject']['runtime_decision'] = {'decided_by': 'director', 'user_words': 'fine',
                                              'decision': 'we squeeze it into ten minutes'}
        save(vd / 'direction.json', doc)
        self.assertIn(need, c.direction_facts(self.run, 1)['issues'])          # only the user settles it
        doc['subject']['runtime_decision'] = {'decided_by': 'user', 'user_words': 'keep it at ten minutes',
                                              'decision': 'the film tells the first campaign only, at ten minutes'}
        save(vd / 'direction.json', doc)
        self.assertNotIn(need, c.direction_facts(self.run, 1)['issues'])
        # a length the user chose is never the director's to move, whatever the mode asked for now
        res = self.length('--revise', 'the story would rather run twelve minutes than ten', *PACE, expected=2)
        self.assertIn('user\'s own approval', res['error'])


def said(*parts):
    """A minute of narration in a test opening's own words (well past the fifty words an opening needs)."""
    return ' '.join(f'{p} and what it set in motion for the people who had to live with it afterwards.' for p in parts)


OPENINGS = {
    'candidates': [
        {'id': 'O1', 'way_in': 'the battle, because it is what viewers already know',
         'narration': said('The battle began at dawn', 'Thousands of men waited in the fog', 'Nobody had slept',
                           'The guns opened on the ridge'),
         'picture': 'a wide field in fog with two lines of soldiers and smoke rising on the far ridge'},
        {'id': 'O2', 'way_in': 'the clerk at his desk, two weeks before anyone knows the order matters',
         'narration': said('A clerk dipped his pen', 'The paper in front of him moved forty wagons', 'He signed it tired',
                           'He never saw what the signature bought'),
         'picture': 'a small candle-lit desk, one hand signing a sheet, a ledger of depots open beside it'},
        {'id': 'O3', 'way_in': 'the empty depot found afterwards, a puzzle the film then explains',
         'narration': said('The storehouse was already empty', 'Somebody had cleared it before the march', 'No officer remembered why',
                           'The answer was in a drawer'),
         'picture': 'an empty stone storehouse with open doors, cart ruts leading away across wet ground'}],
    'shelf': {'ours': [{'id': 'P1', 'title': 'The Order That Won the Battle',
                        'thumbnail': 'a clerk signing one order while an army waits'},
                       {'id': 'P2', 'title': 'One Signature, Forty Wagons', 'thumbnail': 'a pen above a ledger of depots'}],
              'others': ['The Battle, Hour by Hour', {'title': 'Why Armies Starve', 'thumbnail': 'an empty supply wagon'}]}}


@fixture_only
class OpeningContestTests(base.StaticStudioTests):
    """The opening is chosen among several, by fresh readers, before the whole script is read (the audit of
    2026-11-26: the film's opening was the first one written, and its promise came at 2:11)."""

    def packets(self, *more, expected=0):
        return cli('opening-packet', '--run', self.run, '--video', 1, *more, expected=expected)

    def answer(self, vd, p, keep, clicks=('P1',), stop=None):
        """A fresh reader's answer to one packet: keeps watching `keep`, clicks our `clicks` first."""
        meta = read(vd / 'reviews' / f'packet-opening-r{p["round"]}.json')
        lab = {v: k for k, v in meta['labels'].items()}
        num = {e['ours']: k for k, e in meta['shelf'].items() if e['ours']}
        doc = {'reviewer': 'test reader',
               'openings': {x: {'wants_to_know': 'what the order said', 'slips_at': 'nowhere',
                                'thinks_it_is': 'the story of one decision', 'like_every_other': 'no: it starts small'}
                            for x in meta['labels']},
               'keep_watching': f'Opening {lab[keep]}', 'why': 'it starts with a person I can follow at once',
               'keep_from_others': 'the empty storehouse',
               'shelf': {'expect': {k: 'a story about supply' for k in meta['shelf']},
                         'would_click': [int(num[c]) for c in clicks], 'why': 'it promises one clear thing'}}
        save(Path(p['findings_file']), doc)
        return meta

    def contest_issues(self):
        pc = cli('plan-check', '--run', self.run, '--video', 1, expected=None)
        return ([x.split(':')[0] for x in pc['issues'] if x.startswith('opening_contest')],
                [w for w in pc['warnings'] if 'opening' in w[:16]], pc)

    def test_the_opening_is_chosen_among_several_by_fresh_readers(self):
        vd = self.write_plan(review_script=False)
        (vd / 'opening.json').unlink()
        # no opening on record: plan-check says so, and the cold read of the whole script waits for it
        self.assertEqual(self.contest_issues()[0], ['opening_contest_missing'])
        res = cli('review-packet', '--run', self.run, '--video', 1, '--kind', 'script', expected=2)
        self.assertTrue(res['error'].startswith('The opening is chosen among several'), res)
        self.assertEqual(self.packets(expected=None)['details']['shape'], self.load_core().OPENING_SHAPE)
        save(vd / 'opening.json', dict(OPENINGS, candidates=OPENINGS['candidates'][:1]))
        self.assertEqual(self.contest_issues()[0], ['opening_contest_needs_2_to_4_openings_with_distinct_ids'])
        save(vd / 'opening.json', OPENINGS)
        self.assertEqual(self.contest_issues()[0], ['opening_contest_not_read'])
        # one packet per reader: the same openings, each reader's own order and stance, our titles unmarked on the shelf
        made = self.packets()
        self.assertEqual(([p['round'] for p in made['packets']], made['openings'], made['shelf_entries']), ([1, 2], 3, 4))
        texts = [Path(p['packet']).read_text(encoding='utf-8') for p in made['packets']]
        core = self.load_core()
        for k, text in enumerate(texts):
            self.assertIn(core.OPENING_STANCES[k], text)
            self.assertNotIn(core.OPENING_STANCES[1 - k], text)
            self.assertEqual(text.count('## Opening '), 3)
            for hidden in ('O1', 'O2', 'O3', 'P1', 'P2', 'way_in', 'the clerk at his desk, two weeks', '{SHELF}', '{{'):
                self.assertNotIn(hidden, text)
            for shown in ('"The Order That Won the Battle" (its picture: a clerk signing one order while an army waits)',
                          '"The Battle, Hour by Hour"', '"Why Armies Starve" (its picture: an empty supply wagon)',
                          'A clerk dipped his pen', '"would_click"'):
                self.assertIn(shown, text)
        metas = [read(vd / 'reviews' / f'packet-opening-r{k}.json') for k in (1, 2)]
        self.assertEqual(sorted(metas[0]['labels'].values()), ['O1', 'O2', 'O3'])
        self.assertTrue(metas[0]['labels'] != metas[1]['labels'] or metas[0]['shelf'] != metas[1]['shelf'])
        # nothing is recorded until a reader answers; a slip of format is the reader's to fix, never rewritten
        self.assertEqual(cli('opening-record', '--run', self.run, '--video', 1)['waiting_for_a_reader'], [1, 2])
        save(Path(made['packets'][0]['findings_file']), {'reviewer': 'test reader', 'keep_watching': 'the second one'})
        bad = cli('opening-record', '--run', self.run, '--video', 1, expected=2)
        self.assertEqual(bad['details']['round'], 1)
        self.assertTrue(any(x.startswith('"keep_watching" must be one of') for x in bad['details']['problems']))
        self.answer(vd, made['packets'][0], 'O2')
        self.answer(vd, made['packets'][1], 'O3', clicks=('P2', 'P1'))
        rec = cli('opening-record', '--run', self.run, '--video', 1)
        self.assertEqual((rec['recorded'], rec['summary']['kept_watching']), ([1, 2], {'O2': [1], 'O3': [2]}))
        self.assertEqual([r['clicked'] for r in rec['summary']['shelf']['P1']['readers']], [1, 2])
        self.assertEqual([r['clicked'] for r in rec['summary']['shelf']['P2']['readers']], [None, 1])
        self.assertEqual(rec['summary']['openings']['O1'][0]['wants_to_know'], 'what the order said')
        self.assertEqual(read(vd / 'reviews/opening-r1.json')['keep_watching_id'], 'O2')
        # the readers' accounts are evidence, the decision is the director's and says why
        self.assertEqual(self.contest_issues()[0], ['opening_contest_not_decided'])
        doc = dict(OPENINGS, decision={'opening': 'O1', 'why': 'short'})
        save(vd / 'opening.json', doc)
        self.assertEqual(self.contest_issues()[0], ['opening_contest_decision_missing_why',
                                                    'opening_contest_decision_missing_readers'])
        doc['decision'] = {'opening': 'O1', 'why': 'the battle is the picture every viewer of this niche already holds',
                           'readers': 'one kept the clerk and one the storehouse; the storehouse becomes the second beat'}
        save(vd / 'opening.json', doc)
        iss, warn, pc = self.contest_issues()
        self.assertEqual(iss, [])
        self.assertTrue(any('is not the one any reader would keep watching (they chose O2, O3)' in w for w in warn), warn)
        self.assertEqual(pc['creative']['opening_contest']['kept_watching'], {'O2': [1], 'O3': [2]})
        # the fixture's script does not open with the chosen opening's words: said, as a place to look
        self.assertTrue(any('were never in front of a reader' in w or 'was never in front of a reader' in w for w in warn), warn)
        script = read(vd / 'script.json')
        script['lines'][0]['text'] = OPENINGS['candidates'][0]['narration']
        save(vd / 'script.json', script)
        self.assertEqual(core.opening_state(self.run, 1, script['lines'])['facts']['script_keeps_chosen_opening'], 1.0)
        # the cold read may now be asked for; openings rewritten after the read were never read
        doc['candidates'] = [dict(c, narration=c['narration'] + ' And then the rain began to fall on all of them.')
                             for c in doc['candidates']]
        save(vd / 'opening.json', doc)
        self.assertEqual(self.contest_issues()[0], ['opening_contest_not_read'])
        self.assertEqual([p['round'] for p in self.packets('--readers', 1)['packets']], [3])

    def test_one_opening_only_is_said_and_shown(self):
        vd = self.write_plan(review_script=False)
        iss, warn, _pc = self.contest_issues()
        self.assertEqual(iss, [])
        self.assertTrue(warn[0].startswith('one opening only, no contest: a test fixture'), warn)
        save(vd / 'opening.json', {'single_opening_why': 'it is fine'})           # no reason is no way out
        self.assertEqual(self.contest_issues()[0], ['opening_contest_missing'])
        # an older direction hears the contest as advice
        (vd / 'opening.json').unlink()
        lock = read(vd / 'direction-lock.json')
        lock['planning_rules'] = 5
        save(vd / 'direction-lock.json', lock)
        iss, _warn, pc = self.contest_issues()
        self.assertEqual(iss, [])
        self.assertTrue(any(w.startswith('advisory') and 'opening_contest_missing' in w for w in pc['warnings']))
        self.assertTrue(cli('review-packet', '--run', self.run, '--video', 1, '--kind', 'script')['ok'])


@fixture_only
class RunSheetTests(base.StaticStudioTests):
    """The film on one page (the audit: a slow middle of three and a half minutes passed fourteen checks, each of
    which looked at one thing and none at the film's course)."""

    def test_the_film_on_one_page(self):
        vd = self.write_plan()
        core = self.load_core()
        facts = core.run_sheet_facts(self.run, 1)
        rows = facts['rows']
        self.assertEqual([r['beat'] for r in rows], ['B01', 'B02', 'B03', 'B04', 'B05'])
        self.assertTrue(facts['basis'].startswith('the planning pace (145 wpm)'), facts['basis'])
        self.assertEqual((rows[0]['lines'], rows[0]['from_s'], rows[0]['words']), ('L001-L010', 0.0, 270))
        self.assertEqual(rows[1]['from_s'], rows[0]['to_s'])
        self.assertEqual(rows[4]['gives'], 'KEY MOMENT: the earned conclusion; the supply decision decided the battle')
        self.assertEqual({k: facts['totals'][k] for k in ('beats', 'key_moments', 'values_carried', 'pictures_planned')},
                         {'beats': 5, 'key_moments': 1, 'values_carried': 1, 'pictures_planned': None})
        look = facts['look_at']
        self.assertEqual(len(look), 2, look)
        self.assertTrue(look[0].startswith('run sheet: the longest stretch with no key moment and no researched value '
                                           'carried is 00:00-'), look)
        self.assertIn('B01 to B04', look[0])
        self.assertTrue(look[1].startswith('run sheet: no beat says what the viewer is waiting for'), look)
        # what the viewer waits for, what the ear has to catch, and how many pictures carry each beat
        bm = read(vd / 'beat-map.json')
        for b in bm['beats'][:3]:
            b['viewer_question'] = 'How did the army move at all?'
        bm['beats'][3]['viewer_question'] = 'What did the order cost?'
        save(vd / 'beat-map.json', bm)
        script = read(vd / 'script.json')
        script['lines'][10]['text'] = ('In 1863 the clerk of General Harlan Voss moved 40 wagons from Fort Kessler to '
                                       'the river in 3 days, and nobody above him noticed.')
        save(vd / 'script.json', script)
        shots = self.shots_for_plan()
        shots[3]['reuses'] = 'S1'
        shots.append(dict(shots[2], id='S6', reuses='S1'))
        save(self.run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
        facts = core.run_sheet_facts(self.run, 1)
        by = {r['beat']: r for r in facts['rows']}
        self.assertEqual((by['B02']['numbers'], by['B02']['new_names']), (3, ['General Harlan Voss', 'Fort Kessler']))
        self.assertEqual((by['B03']['pictures'], by['B04']['pictures']),
                         ({'planned': 2, 'seen_before': 1}, {'planned': 1, 'seen_before': 1}))
        self.assertEqual(facts['totals']['pictures_planned'], 6)
        look = ' | '.join(facts['look_at'])
        self.assertIn('one question is kept for 00:00-', look)
        self.assertIn('B01 to B03) ("How did the army move at all?")', look)
        self.assertIn('no viewer question for B05:', look)
        self.assertIn('most for the ear to catch in B02 (3 number(s), 2 new name(s) in ', look)
        self.assertIn('the picture stands longest in B05: 1 picture(s) over ', look)
        self.assertIn('only pictures seen before in B04:', look)
        # the page: printed without touching the run, written only where it is asked for
        before = {p: p.stat().st_mtime_ns for p in self.run.rglob('*') if p.is_file()}
        res = cli('run-sheet', '--run', self.run, '--video', 1)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in self.run.rglob('*') if p.is_file()})
        self.assertIsNone(res['page'])
        self.assertIn('| B02 | ', res['page_text'])
        self.assertIn('General Harlan Voss, Fort Kessler', res['page_text'])
        self.assertIn('## Places to look (facts, never faults)', res['page_text'])
        self.assertEqual(res['look_at'], facts['look_at'])
        out = self.home / 'sheets' / 'run-sheet.md'
        self.assertEqual(cli('run-sheet', '--run', self.run, '--video', 1, '--out', out)['page'], str(out.resolve()))
        self.assertTrue(out.read_text(encoding='utf-8').startswith('# Run sheet: A test title'))
        # plan-check carries the places to look, as warnings and under run_sheet
        pc = cli('plan-check', '--run', self.run, '--video', 1, expected=None)
        self.assertEqual(pc['run_sheet']['look_at'], facts['look_at'])
        self.assertTrue(all(x in pc['warnings'] for x in facts['look_at']))


@fixture_only
class ReaderTests(base.StaticStudioTests):
    """Readers say what they would do, never a score (the audit: reader scores sat at 7 to 8 for thirteen rounds and
    told nobody anything)."""

    def read_script(self, verdict, findings):
        packet = cli('review-packet', '--run', self.run, '--video', 1, '--kind', 'script')
        first = read(self.run / '40-plans/video-01/script.json')['lines'][0]['id']
        save(Path(packet['findings_file']), {
            'reviewer': 'test reader', 'verdict': verdict, 'findings': findings,
            'developments': self.clear_development('script'),
            'promise': {'promised': 'to understand the decision and what it cost', 'first_delivered': first, 'waiting': []}})
        return packet, cli('review-record', '--run', self.run, '--video', 1, '--kind', 'script')

    def test_a_reader_says_where_they_would_stop_never_a_score(self):
        vd = self.write_plan(review_script=False)
        minor = {'id': 'F1', 'severity': 'minor', 'lines': ['L001-L002'], 'problem': 'the opening starts slowly',
                 'likely_cause': 'a general statement before any person'}
        stop = {'promise': 'one decision', 'delivered': 'partly', 'watched_to_end': 'no', 'would_stop_at': 'L020',
                'why': 'four facts in a row with nobody in them'}
        packet, rec = self.read_script(stop, [minor])
        text = Path(packet['packet']).read_text(encoding='utf-8')
        self.assertNotIn('1 to 10', text)
        self.assertNotIn('keep_watching_1_10', text)
        self.assertIn('"watched_to_end": "yes | no"', text)
        self.assertIn('the line where you would have stopped, and what would have kept you', text)
        # a reader who would have left, with no major of their own at that place: the statement is a major finding
        self.assertEqual(rec['major'], ['X1'])
        x = [f for f in read(vd / 'reviews/script-r1.json')['findings'] if f['id'] == 'X1'][0]
        self.assertEqual((x['lines'], x['derived_from']['verdict']['would_stop_at']), (['L020'], 'L020'))
        self.assertIn('four facts in a row with nobody in them', x['problem'])
        core = self.load_core()
        order = [f'L{i:03}' for i in range(1, 53)]
        major = dict(minor, id='F2', severity='major', lines=['L018-L022'])
        self.assertEqual(core.stop_findings('script', stop, [major], order, set()), [])     # already their own finding
        self.assertEqual(core.stop_findings('script', dict(stop, watched_to_end='yes'), [], order, set()), [])
        self.assertEqual(core.stop_findings('script', dict(stop, would_stop_at='somewhere'), [], order, {'X1'})[0]['id'], 'X2')
        late = core.stop_findings('final', dict(stop, would_stop_at='about 08:59'), [], order, set())[0]
        self.assertEqual((late['id'], late['at'], late['severity']), ('X1', '08:59', 'major'))
        covered = [{'id': 'F1', 'severity': 'major', 'at': '02:00, 08:40-09:30'}]
        self.assertEqual(core.stop_findings('final', dict(stop, would_stop_at='08:59'), covered, order, set()), [])
        self.assertEqual(core.BRIEF_VERSION, 7)
        self.assertIn('"would_stop_at": "<mm:ss where you would have left, or none>"', core.FINAL_BRIEF)
        self.assertNotIn('1_10', core.FINAL_BRIEF + core.SCRIPT_BRIEF + core.TREATMENT_BRIEF)


if __name__ == '__main__':
    unittest.main()
