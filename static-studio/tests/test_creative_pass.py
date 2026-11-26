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
import test_audit_impl as audit                                    # noqa: E402
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
                          'A clerk dipped his pen', '"would_click"',
                          # the answer's example names every opening of this packet, and closes as JSON does
                          '"A": {"wants_to_know": "...", "slips_at": "... (or: nowhere)"',
                          '"C": {"wants_to_know": "...", "slips_at": "...", "thinks_it_is": "...", "like_every_other": "..."}},\n'
                          '  "keep_watching"'):
                self.assertIn(shown, text)
            self.assertNotIn('"D": {', text)
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

    def test_a_picture_only_our_titles_have_is_not_shown(self):
        # the reader must not be able to tell which titles are ours: a picture described for ours alone would say so
        vd = self.write_plan(review_script=False)
        save(vd / 'opening.json', dict(OPENINGS, shelf={'ours': OPENINGS['shelf']['ours'],
                                                        'others': ['The Battle, Hour by Hour', 'Why Armies Starve']}))
        made = self.packets('--readers', 1)
        text = Path(made['packets'][0]['packet']).read_text(encoding='utf-8')
        self.assertNotIn('(its picture:', text)
        self.assertIn('"The Order That Won the Battle"', text)
        self.assertTrue(any(w.startswith('the shelf shows titles only') for w in made['warnings']), made['warnings'])
        # with a picture beside them the thumbnail ideas are read as well, and nothing is said
        save(vd / 'opening.json', OPENINGS)
        made = self.packets('--readers', 1)
        self.assertIn('(its picture: a pen above a ledger of depots)',
                      Path(made['packets'][0]['packet']).read_text(encoding='utf-8'))
        self.assertEqual(made['warnings'], [])

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
        self.assertTrue(look[0].startswith('run sheet: the longest stretch with no key moment is 00:00-'), look)
        self.assertIn('B01 to B04). No beat in it carries a researched value: what keeps them watching', look[0])
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


# two measured models with known habits (the fixture's two references, their measurements replaced)
MODEL_A = {'picture': {'shots': 100, 'cuts_per_min': 10.0, 'shot_length_s': {'p10': 2.0, 'median': 5.0, 'p90': 9.0},
                       'longest_shot_s': 20.0, 'same_picture_again': 4, 'moving_time_share': 0.5},
           'narration': {'pauses_per_min': 12.0, 'pause_profile': {'pauses_0_8s_plus_per_min': 1.0, 'longest_pause_s': 1.2},
                         'gap_level_rel_speech_db': {'p10': -30.0, 'median': -20.0, 'p90': -10.0}}}
MODEL_B = {'picture': {'shots': 200, 'cuts_per_min': 16.0, 'shot_length_s': {'p10': 1.5, 'median': 3.0, 'p90': 6.0},
                       'longest_shot_s': 12.0, 'same_picture_again': 0, 'moving_time_share': 0.2},
           'narration': {'pauses_per_min': 18.0, 'pause_profile': {'pauses_0_8s_plus_per_min': 2.5, 'longest_pause_s': 3.0},
                         'gap_level_rel_speech_db': {'p10': -40.0, 'median': -25.0, 'p90': -12.0}}}
# a finished file that lies outside both on four habits
FILM = {'picture': {'shots': 60, 'cuts_per_min': 6.0, 'shot_length_s': {'median': 9.0}, 'longest_shot_s': 30.0,
                    'same_picture_again': 18, 'moving_time_share': 0.3},
        'narration': {'pauses_per_min': 14.0, 'gap_level_rel_speech_db': {'p10': -31.0, 'median': -30.0, 'p90': -25.0}}}
ASKED = ('pictures_per_min', 'seen_again_share', 'sound_under_voice_db', 'sound_moves_db')
WHY = ('each still is a painted map the viewer has to read, so it stands until the narration has walked the whole '
       'route across it')


def models(run):
    """The film's two models as measured films with known habits."""
    for v, s in (('V001', MODEL_A), ('V002', MODEL_B)):
        p = Path(run) / '20-analysis/av' / f'{v}.json'
        prof = read(p) if p.is_file() else {}
        prof['summary'] = {**(prof.get('summary') or {}), **s}
        save(p, prof)


@fixture_only
class ModelsBesideTests(base.StaticStudioTests):
    """The film beside its models (the audit of 2026-11-26: the finished film cut 7.5 times a minute where its five
    models cut 9.8 to 21.4 and showed a picture again in 30% of its shots where they do in 0 to 6%; every number was
    in the run, none was ever set beside the others, so none was a decision)."""

    def check(self, expected=0):
        return cli('shot-check', '--run', self.run, '--video', 1, expected=expected)

    def crafts(self, res):
        return [x for x in res['issues'] if x.startswith('craft_choice_')]

    def test_the_picture_plan_is_set_beside_the_models_before_a_still_is_made(self):
        vd = self.write_plan()
        shots = self.shots_for_plan()
        models(self.run)
        choices = vd / 'craft-choices.json'
        choices.unlink()                     # the fixture's own answer: this test gives the real ones
        core = self.load_core()
        f = core.models_beside_facts(self.run, 1)
        self.assertEqual(f['models'], ['V001', 'V002'])
        row = {r['measure']: r for r in f['rows']}
        cuts = row['pictures_per_min']
        self.assertEqual((cuts['models'], cuts['range'], cuts['outside'], cuts['read_on'], cuts['export']),
                         ({'V001': 10.0, 'V002': 16.0}, [10.0, 16.0], 'under', 'before', None))
        self.assertLess(cuts['before_export'], 1.0)
        self.assertTrue(cuts['before_basis'].startswith('planned: the shot plan on the planning pace (145 wpm)'))
        again = row['seen_again_share']
        self.assertEqual((again['range'], again['before_export'], again['outside']), ([0.0, 0.04], 0.0, None))
        self.assertEqual((row['sound_under_voice_db']['models'], row['sound_moves_db']['range']),
                         ({'V001': 20.0, 'V002': 25.0}, [20.0, 28.0]))
        self.assertIsNone(row['sound_moves_db']['before_export'])
        # asked only where a viewer feels it: how long a picture stands is said, never asked
        self.assertEqual([d['measure'] for d in f['departures'] if d['issue']], ['pictures_per_min'])
        self.assertIn('longest_picture_s', [d['measure'] for d in f['departures']])
        res = self.check(expected=2)
        self.assertEqual(res['issues'], self.crafts(res))
        self.assertRegex(res['issues'][0], r'^craft_choice_pictures_per_min:0\.\d_here_every_model_is_higher_'
                                           r'\(10_to_16\):change_it_or_say_why_in_craft-choices\.json$')
        self.assertEqual([r['measure'] for r in res['beside_the_models']['rows']], list(core.PICTURE_MEASURES))
        pic = res['pictures']
        self.assertEqual((pic['shots'], pic['stills'], pic['seen_again']['shots'], pic['most_shown']['times']), (5, 5, 0, 1))
        self.assertTrue(any(w.startswith('pictures: 5 still(s) in 5 shot(s) over ') and '; no picture returns; ' in w
                            for w in res['warnings']), res['warnings'])
        # a token is not a reason; a sentence is, and it stays in sight at every check
        save(choices, {'choices': [{'measure': 'pictures_per_min', 'why': 'slow on purpose'}]})
        self.assertEqual(len(self.crafts(self.check(expected=2))), 1)
        save(choices, {'choices': [{'measure': 'pictures_per_min', 'why': WHY}]})
        res = self.check()
        self.assertTrue(res['ready'])
        self.assertTrue(any(w.startswith('craft choice: cuts a minute (a new picture, or a return to one): 0.')
                            and w.endswith('The reason on record: ' + WHY) for w in res['warnings']), res['warnings'])
        # a picture that returns, a part that opens on one, two things side by side with nothing drawn on them
        shots[3]['reuses'] = 'S1'
        shots[2]['composition'] = 'split'
        save(self.run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
        res = self.check(expected=2)
        self.assertEqual(self.crafts(res), ['craft_choice_seen_again_share:0.2_here_every_model_is_lower_(0_to_0.04):'
                                            'change_it_or_say_why_in_craft-choices.json'])
        said = ' | '.join(res['warnings'])
        self.assertIn('1 shot(s) show a picture seen before (20% of the shots, ', said)
        self.assertIn('pictures: B04 open(s) on a picture the viewer has already seen', said)
        self.assertIn('pictures: S3 set(s) two things side by side with nothing drawn on them', said)
        self.assertEqual((res['pictures']['stills'], res['pictures']['most_shown']['still'],
                          res['pictures']['most_shown']['times']), (4, 'S1', 2))
        self.assertEqual((res['pictures']['seen_again']['as_ground_for_a_drawing'],
                          res['pictures']['most_shown']['under_a_drawing']), (0, 0))
        # A return that carries a drawing of its own shows something new on a ground the viewer knows: counted apart,
        # never as the same picture again (the real film used one sheet of paper under 22 different drawings).
        shots[3]['diagram_or_overlay'] = 'the map of the depots drawn on it, the second route in red'
        save(self.run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
        res = self.check(expected=None)
        self.assertEqual(self.crafts(res), [])
        pic = res['pictures']
        self.assertEqual((pic['seen_again']['shots'], pic['seen_again']['as_ground_for_a_drawing'],
                          pic['most_shown']['times'], pic['most_shown']['under_a_drawing'],
                          pic['beats_opening_on_a_seen_picture']), (0, 1, 2, 1, []))
        said = ' | '.join(res['warnings'])
        self.assertIn('; no picture returns with nothing new on it (1 return(s) to a still as the ground of a drawing '
                      'of its own); the still shown most is S1: 2 times, ', said)
        self.assertIn('), 1 of them under a drawing of its own; the longest a picture stands', said)
        self.assertNotIn('open(s) on a picture the viewer has already seen', said)
        row = {r['measure']: r for r in core.models_beside_facts(self.run, 1)['rows']}['seen_again_share']
        self.assertEqual(row['before_export'], 0.0)
        self.assertTrue(row['before_basis'].startswith('planned: returns with nothing new drawn on them'))
        shots[3].pop('diagram_or_overlay')
        save(self.run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
        # a direction approved before these rules hears it as advice
        lock = read(vd / 'direction-lock.json')
        save(vd / 'direction-lock.json', {**lock, 'planning_rules': 5})
        res = self.check(expected=None)
        self.assertFalse(self.crafts(res))
        self.assertTrue(any(w.startswith('advisory (this direction was approved before planning rules it need not '
                                         'follow): craft_choice_seen_again_share') for w in res['warnings']), res['warnings'])
        save(vd / 'direction-lock.json', lock)
        # the whole comparison as a page: read only, written where it is asked for
        before = {p: p.stat().st_mtime_ns for p in self.run.rglob('*') if p.is_file()}
        page = cli('beside-models', '--run', self.run, '--video', 1)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in self.run.rglob('*') if p.is_file()})
        self.assertIn("| measure | V001 | V002 | the models | this film before its export | this film's export |",
                      page['page_text'])
        self.assertIn('| 10 to 16 | 0.', page['page_text'])
        self.assertIn('**(outside)**', page['page_text'])
        self.assertIn('## Where this film lies outside every model', page['page_text'])
        out = self.home / 'pages' / 'beside.md'
        self.assertEqual(cli('beside-models', '--run', self.run, '--video', 1, '--out', out)['page'], str(out.resolve()))
        self.assertTrue(out.read_text(encoding='utf-8').startswith('# The film beside its models: A test title'))
        # a finished file is read on its own measurements, the way its models are
        film = self.home / 'film.mp4'
        film.write_bytes(b'not a film, only a file with a fingerprint' * 50)
        save(core.export_av_path(self.run, 1, core.quick_fingerprint(film)), {'summary': FILM})
        f = core.models_beside_facts(self.run, 1, film)
        row = {r['measure']: r for r in f['rows']}
        self.assertEqual((row['pictures_per_min']['export'], row['pictures_per_min']['read_on'],
                          row['pictures_per_min']['why']), (6.0, 'export', WHY))
        self.assertEqual((row['seen_again_share']['export'], row['seen_again_share']['outside']), (0.3, 'over'))
        self.assertEqual((row['sound_under_voice_db']['export'], row['sound_under_voice_db']['outside']), (30.0, 'over'))
        self.assertEqual((row['sound_moves_db']['export'], row['sound_moves_db']['outside']), (6.0, 'under'))
        self.assertEqual((row['pauses_per_min']['export'], row['pauses_per_min']['outside']), (14.0, None))
        self.assertEqual([d['measure'] for d in f['departures'] if d['issue']], list(ASKED[1:]))
        # the director may hold only some of the references as models; one model gives no range
        d = read(vd / 'direction.json')
        d['evidence']['models'] = ['V002', 'V099']
        save(vd / 'direction.json', d)
        f = core.models_beside_facts(self.run, 1)
        self.assertEqual((f['models'], f['departures']), (['V002'], []))
        self.assertTrue(any('V099 is named as a model but' in x for x in f['notes']), f['notes'])
        self.assertTrue(any('one measured model only' in x for x in f['notes']), f['notes'])


class BreathingSoundTests(unittest.TestCase):
    """Music that can rise where nobody speaks (the audit of 2026-11-26: every bed at one level for the whole film,
    20 to 25 LU under the voice, a closing theme at room-tone level; the level was picked with nothing to pick it
    against, and CapCut ignores a clip's volume, so a rise has to be in the file). The fixture is the sound review's:
    a tone for the voice that stops between six lines."""

    T, WORDS = audit.SoundReviewTests.T, audit.SoundReviewTests.WORDS
    ff, tone, setUp, tearDown = (audit.SoundReviewTests.ff, audit.SoundReviewTests.tone, audit.SoundReviewTests.setUp,
                                 audit.SoundReviewTests.tearDown)
    EVEN = {'id': 'even', 'under_speech_db': 22, 'why': 'a pulse under the whole film'}
    FOR = 'the theme comes up in the held breaths between the letters'

    @classmethod
    def setUpClass(cls):
        cls.core = audit.load_core('static_studio_core_breathing')

    def level(self, path, at_s):
        """A file's level around one moment (dB, over half a second)."""
        ar = self.core._audio_review()
        lv = ar.levels(ar.load_mono(path))
        i = int(round(at_s / ar.HOP_S))
        return float(lv[i - 5:i + 5].mean())

    def windows(self, got, want):
        """A lift's windows, each edge within one level frame of where the voice stops and starts, the rise exact."""
        self.assertEqual(len(got), len(want), got)
        for g, w in zip(got, want):
            self.assertLessEqual(max(abs(g[0] - w[0]), abs(g[1] - w[1])), 0.06, got)
            self.assertEqual(g[2], w[2], got)

    def bake(self, tracks, expected=0, bake=True):
        plan = self.td / 'beds.json'
        save(plan, {'narration': str(self.narr), 'tracks': tracks})
        return cli('bed-levels', '--plan', plan, *(('--bake', self.td / 'baked') if bake else ()), expected=expected)

    def review(self, bed):
        """The sound review of a cut whose only music is this bed, under the whole film."""
        save(self.rd / '70-edit/video-01/timeline.json', {'audio_tracks': [
            self.tracks[0], {'kind': 'music', 'file': str(bed), 'start_s': 0, 'end_s': 40, 'beats': ['B01'], 'volume': 1}]})
        return cli('sound-review', '--run', self.rd, '--video', 1)

    def test_a_bed_rises_where_nobody_speaks_and_is_back_before_the_next_word(self):
        rd = self.rd
        src = self.tone(self.td / 'theme.wav', 330, 40, '0.316')
        even = {**self.EVEN, 'file': str(src)}
        lift = {'by_db': 9, 'where_voice_is_silent_s': 1.5, 'ramp_s': 0.5, 'why': self.FOR}
        res = self.bake([even, {**even, 'id': 'breathing', 'at': 0.0, 'lift': lift}])
        flat, up = res['tracks']
        self.assertNotIn('lift', flat)
        # the three pauses of 1.5 s or more, a guard inside each edge; the half-second gaps are left alone
        self.windows(up['lift']['windows'], [[16.65, 19.35, 9.0], [24.65, 27.35, 9.0], [33.65, 35.35, 9.0]])
        self.assertEqual((up['lift']['by_db'], up['lift']['under_speech_db_at_its_peak'], up['lift']['ramp_s'],
                          up['lift']['why']), (9.0, 13.0, 0.5, self.FOR))
        self.assertLess(abs(up['lift']['lifted_s'] - 7.1), 0.3, up['lift'])
        a, b = Path(flat['baked']['file']), Path(up['baked']['file'])
        self.assertNotEqual(a.name, b.name)
        self.assertIn('.lift9dB', b.name)
        self.assertFalse(list((self.td / 'baked').glob('*.lifting')))
        # in the file itself: 9 dB up in the middle of a pause, at its own level under the words and as the voice returns
        own = self.level(a, 13.0)
        self.assertLess(abs(self.level(b, 13.0) - own), 0.3)
        self.assertLess(abs(self.level(b, 18.0) - own - 9.0), 0.5)
        self.assertLess(abs(self.level(b, 26.0) - own - 9.0), 0.5)
        self.assertLess(abs(self.level(b, 19.75) - own), 0.5)
        self.assertIn('Torcoli', res['context']['published'])
        # the sound review reads both mixes the way a finished film is read: what plays between the words, and
        # whether the music comes up where it is heard alone
        models(rd)
        save(rd / '40-plans/video-01/direction.json', {'evidence': {'references': ['V001', 'V002']}})
        res = self.review(a)
        gap = res['sound_between_the_words']['gap_level_rel_speech_db']
        self.assertGreaterEqual(res['sound_between_the_words']['pauses'], 3)
        self.assertLess(abs(gap['median'] + 22), 2.0, gap)
        self.assertLess(gap['p90'] - gap['p10'], 1.0, gap)
        self.assertLess(abs(res['music_heard_alone']['rises_when_alone_db']), 1.0, res['music_heard_alone'])
        self.assertTrue(any(x.startswith('music is heard with no voice over it for ') and 'never for longer than '
                            in x and 'does the voice leave it room?' in x for x in res['look_at']), res['look_at'])
        rows = {r['measure']: r for r in res['beside_the_models']['rows']}
        self.assertNotIn('pictures_per_min', rows)
        self.assertEqual((rows['sound_moves_db']['range'], rows['sound_moves_db']['outside'],
                          rows['sound_moves_db']['read_on'], rows['sound_under_voice_db']['outside']),
                         ([20.0, 28.0], 'under', 'before', None))
        self.assertEqual([x.split(':')[0] for x in res['craft_choices_asked']], ['craft_choice_sound_moves_db'])
        self.assertTrue(any(x.startswith('how far that sound moves through the film') and 'every model is higher' in x
                            for x in res['look_at']), res['look_at'])
        res = self.review(b)
        gap = res['sound_between_the_words']['gap_level_rel_speech_db']
        self.assertGreater(gap['p90'] - gap['p10'], 7.0, gap)
        self.assertGreater(res['music_heard_alone']['rises_when_alone_db'], 6.0, res['music_heard_alone'])
        # a reason on record is shown with the fact, and nothing more is asked
        save(rd / '40-plans/video-01/craft-choices.json', {'choices': [{'measure': m, 'why': WHY} for m in ASKED]})
        res = self.review(b)
        self.assertEqual(res['craft_choices_asked'], [])
        self.assertTrue(any(x.startswith('craft choice: how far that sound moves through the film') for x in res['look_at']),
                        res['look_at'])

    def test_a_lift_says_where_how_much_and_what_for(self):
        src = self.tone(self.td / 'theme.wav', 330, 40, '0.316')
        t = {**self.EVEN, 'file': str(src), 'at': 0.0}
        for lift, said in (({'by_db': 9, 'where_voice_is_silent_s': 1.5}, 'lift.why says what the rise is for'),
                           ({'by_db': 9, 'why': self.FOR}, 'lift says where the bed rises'),
                           ({'by_db': 0, 'where_voice_is_silent_s': 1.5, 'why': self.FOR}, 'lift.by_db says how many dB'),
                           ({'by_db': 9, 'moments': [[20, 18]], 'why': self.FOR}, 'each of lift.moments is [from_s, to_s]'),
                           ('up', 'lift is an object')):
            self.assertIn(said, self.bake([{**t, 'lift': lift}], expected=2)['error'])
        good = {'by_db': 9, 'where_voice_is_silent_s': 1.5, 'why': self.FOR}
        self.assertIn('where its baked copy starts',
                      self.bake([{**{k: v for k, v in t.items() if k != 'at'}, 'lift': good}], expected=2)['error'])
        self.assertIn('a lift lives in the baked file', self.bake([{**t, 'lift': good}], expected=2, bake=False)['error'])
        self.assertFalse((self.td / 'baked').exists())
        # a moment the director names is lifted whether or not the voice speaks there; a stretch that starts later in
        # the film is lifted on the film's clock
        row = self.bake([{**t, 'at': 10.0, 'dur': 20, 'lift': {'by_db': 6, 'moments': [[12.0, 14.0]], 'why': self.FOR,
                                                               'where_voice_is_silent_s': 2.5}}])['tracks'][0]
        self.windows(row['lift']['windows'], [[12.15, 13.85, 6.0], [16.65, 19.35, 6.0], [24.65, 27.35, 6.0]])
        f = Path(row['baked']['file'])
        self.assertLess(abs(self.level(f, 8.0) - self.level(f, 5.0) - 6.0), 0.5)     # film 18.0 against film 15.0
        # a rise the file cannot hold is refused, and nothing half-written is left behind
        row = self.bake([{**t, 'lift': {**good, 'by_db': 60}}])['tracks'][0]
        self.assertTrue(row['error'].startswith('lift: the rise would clip the file'), row)
        self.assertFalse(list((self.td / 'baked').glob('*.lifting')))
        # no pause that long inside the stretch: said, and the file is the even one
        row = self.bake([{**t, 'lift': {**good, 'where_voice_is_silent_s': 5}}])['tracks'][0]
        self.assertEqual((row['lift']['windows'], row['lift']['lifted_s'], row['lift']['full_rises']), ([], 0.0, 0))
        self.assertIn('nothing was lifted', row['lift']['note'])
        self.assertIn('More room is a planned silence the music carries', row['lift']['note'])
        # pauses too short for the whole rise: the bed comes up as far as each allows, and the answer says so
        row = self.bake([{**t, 'lift': {**good, 'ramp_s': 2.0}}])['tracks'][0]
        self.assertEqual((len(row['lift']['windows']), row['lift']['full_rises']), (3, 0))
        self.assertLess(max(w[2] for w in row['lift']['windows']), 9.0)
        self.assertIn('no silence in this stretch is long enough for the whole rise (9 dB up and back takes 4.3 s',
                      row['lift']['note'])
        # room enough: the count of whole rises, and no note
        row = self.bake([{**t, 'lift': good}])['tracks'][0]
        self.assertEqual(row['lift']['full_rises'], 3)
        self.assertNotIn('note', row['lift'])


@fixture_only
class ReleaseCraftTests(audit.ReleaseStateTests):
    """A finished file that lies outside every model on a habit a viewer feels has its reason on record before it is
    released; a direction approved before this rule hears it as advice."""

    def test_the_finished_file_is_read_beside_its_models_before_release(self):
        c, rd = self.core, self.rd
        raw = self.export(self.td / 'raw.mp4', self.stills)
        self.passed(raw)
        out = self.master(raw)
        self.passed(out)
        cli('sound-review', '--run', rd, '--video', 1, '--file', out)
        self.assertTrue(self.release(out, record=False)['ready'])        # no models named: nothing to stand beside
        models(rd)
        save(rd / '40-plans/video-01/direction.json', {'evidence': {'references': ['V001', 'V002']}})
        save(c.export_av_path(rd, 1, c.quick_fingerprint(Path(out))), {'summary': FILM})
        res = self.release(out, record=False)
        self.assertEqual([x.split(':')[:2] for x in res['issues']], [['craft', f'craft_choice_{m}'] for m in ASKED])
        self.assertIn('craft:craft_choice_sound_moves_db:6_here_every_model_is_higher_(20_to_28):change_it_or_say_why_'
                      'in_craft-choices.json', res['issues'])
        choices = rd / '40-plans/video-01/craft-choices.json'
        save(choices, {'choices': [{'measure': m, 'why': WHY} for m in ASKED]})
        self.assertTrue(self.release(out, record=False)['ready'])
        choices.unlink()
        save(rd / '40-plans/video-01/direction-lock.json', {'planning_rules': 5})
        res = self.release(out, record=False)
        self.assertTrue(res['ready'], res['issues'])
        self.assertEqual(len([w for w in res['warnings'] if w.startswith(
            'advisory (this direction was approved before planning rules it need not follow): craft_choice_')]), 4)


if __name__ == '__main__':
    unittest.main()
