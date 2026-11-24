"""Smoke tests for the isolated static-only command. No paid API calls."""
from __future__ import annotations
import argparse
import hashlib
import re
import json
import importlib.util
import io
import os
from unittest import mock
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT/'scripts'/'static_core.py'


def cli(*args, expected=0):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)],      # the tool always writes UTF-8
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


# What every planned pause has to say besides its length (03): what it is for, what is seen, what is heard.
TAG_EXCEPTION = {'reason': 'a test fixture of plain repeated sentences: no moment in it calls for a delivery or pause cue',
                 'approved_by_user': 'test fixture approval'}
HELD = {'pause_purpose': 'the viewer looks at the map for a while',
        'pause_picture': 'the map of the valley with the new road drawn in',
        'pause_sound': 'the low pulse of the bed goes on',
        'pause_landing': 'the line lands flat and final on its last word',
        'pause_resume': 'the next line starts again with a fresh lift'}


class StaticStudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        refs = self.home/'references'
        refs.mkdir()
        for idx in range(3):
            p = refs/f'video_{idx+1}.mp4'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                            '-i',f'color=c={"red" if idx==0 else "blue" if idx==1 else "green"}:s=64x36:r=5',
                            '-t','2.6','-pix_fmt','yuv420p',str(p)],check=True)
        self.run = Path(cli('init','--references',refs,'--workspace',self.home/'runs','--slug','test')['run'])
        self.assertTrue(cli('scan','--run',self.run)['ok'])
        invp = self.run/'00-inventory/references.json'
        inv = json.loads(invp.read_text())
        for i,row in enumerate(inv['items']):
            row['duration_s']=[540.,660.,60.][i]
        save(invp,inv)
        for i in range(1,4):
            card={'reference_id':f'V{i:03}', 'niches':['military history'] if i<=2 else ['how-to'],
                  'story_form':'historical narrative' if i<=2 else 'tutorial',
                  'viewer_experience':[{'start_s':0, 'end_s':50,'question':'why','evidence':'[O] source'}],
                  'moments_that_matter':[{'at':'00:10-00:30','observed':'the narrator names the cost before the decision',
                                          'interpretation':'the stakes come before the turn, so the turn lands'}]}
            save(self.run/f'20-analysis/cards/V{i:03}.json',card)
        src=self.run/'30-research/video-01'; src.mkdir(parents=True,exist_ok=True)
        (src/'sources.md').write_text('### S1. A primary record of the order\n- Access: read in full\n'
                                      '### S2. A later study of the campaign\n- Access: read: the chapter on supply\n',
                                      encoding='utf-8')
        save(src/'claims.json',{'claims':[
            {'id':'C01','claim':'The order moved the depots two weeks before the march.','sources':['S1'],
             'confidence':'confirmed','line_refs':['L041']},
            {'id':'C02','claim':'The survey sheet put the valley a mile too far north.','sources':['S2'],
             'confidence':'likely','line_refs':[]}]})

    def test_prepare_index_and_images_dry_run(self):
        self.assertTrue(cli('prepare','--run',self.run,'--ids','V001','--skip-whisper','--reason','the test references carry no narration worth transcribing')['ok'])
        index=self.run/'10-media/V001/frame-index.json'
        self.assertTrue(index.is_file())
        data=json.loads(index.read_text())
        self.assertEqual(data['mode'],'source_pts')
        self.assertGreaterEqual(len(data['frames']),2)
        self.assertEqual(data['frames'][0]['approx_s'],0.0)
        # two frames a second, each the first real frame of its half second, with its own time: a 5 fps clip has
        # frames every 0.2 s, so the samples are at 0, 0.6, 1.0, 1.6, 2.0 s (never the nominal 0.5, 1.5)
        self.assertEqual((data['fps'],data['interval_s'],data['sampler']),(2.0,0.5,'pts-v1'))
        self.assertEqual([f['t_s'] for f in data['frames']],[0.0,0.6,1.0,1.6,2.0])
        self.assertEqual([f['slot_s'] for f in data['frames']],[0.0,0.5,1.0,1.5,2.0])
        self.assertTrue((self.run/'10-media/V001/sampled-frames'/data['frames'][0]['file']).exists())
        job=self.home/'image-job.json'
        save(job,{'model':'gpt-image-2.5-flare','size':'1536x864','quality':'high',
                  'images':[{'id':'S1','prompt':'A carefully specified natural-lit tableau with historical uniforms and a precise map of terrain, no text','file':'S1.png'}]})
        result=subprocess.run([sys.executable,str(ROOT/'scripts/openai_images_worker.py'),
                               '--job',str(job)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'],'dry_run_no_charges')
        self.assertFalse((job.parent/'generated').exists())

    def test_subscription_character_preflight(self):
        spec=importlib.util.spec_from_file_location('static_studio_core', TOOL)
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        response={'character_count':900, 'character_limit':1000, 'status':'active'}
        with mock.patch.object(mod.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(response).encode())):
            self.assertEqual(mod.preflight_elevenlabs_balance('test-not-a-real-key',40)['available_character_allowance'],100)
        with mock.patch.object(mod.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(response).encode())):
            with self.assertRaises(SystemExit):
                mod.preflight_elevenlabs_balance('test-not-a-real-key',100)

    def test_niche_grouping_and_longform_lock(self):
        groups=cli('cohorts','--run',self.run)['groups']
        self.assertEqual(len(groups),2)
        self.assertEqual(next(x for x in groups if x['niche']=='military history')['median_s'],600)
        r=cli('length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
              '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145,'--pace-why','the test narrator reads at this pace')
        self.assertEqual(r['locked_target_s'],600)
        self.assertEqual(r['pace_wpm_source'],'explicit')
        cli('length','--run',self.run,'--video',1,'--mode','own','--niche','military history',
            '--story-form','historical narrative','--minutes',12,'--pace-wpm',145,'--pace-why','the test narrator reads at this pace',expected=2)
        cli('length','--run',self.run,'--video',2,'--mode','own','--niche','how-to',
            '--story-form','tutorial','--minutes',12,'--pace-wpm',145,'--pace-why','the test narrator reads at this pace',expected=2)

    # ---- the creative process, run through the real CLI the way an agent would (no media is generated)
    def measure_refs(self):
        cli('prepare','--run',self.run,'--ids','V001,V002','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        out=cli('av-profile','--run',self.run,'--refs','V001,V002','--no-sheets')
        self.assertTrue((self.run/'20-analysis/av/V001.json').is_file())
        for v in ('V001','V002'):
            self.content_review(v,[])
        return out

    def content_review(self, ref, segments, expected=0, **extra):
        doc={'looked_at':'every sampled frame and the whole soundtrack, start to end','segments':segments,
             'usable':'the pacing, the holds and the map transitions',**extra}
        rp=self.home/f'review-{ref}.json'; save(rp,doc)
        cli('content-review','--run',self.run,'--ref',ref,'--shot-sheets')      # every shot seen once
        return cli('content-review','--run',self.run,'--ref',ref,'--file',rp,expected=expected)

    def add_ref(self, vid, path, duration, audio, fps=30):
        invp=self.run/'00-inventory/references.json'; inv=json.loads(invp.read_text())
        inv['items'].append({'id':vid,'relative_path':Path(path).name,'kind':'video','source_path':str(path),
                             'fingerprint':vid+'-test','duration_s':duration,'has_video':True,'has_audio':audio,'fps':fps})
        save(invp,inv)

    @staticmethod
    def colour(path):
        from PIL import Image
        r,g,b=Image.open(path).convert('RGB').getpixel((32,18))
        return ('red' if r>150 and g<100 and b<100 else 'blue' if b>150 and r<100 and g<100 else
                'green' if g>90 and r<100 and b<100 else 'white' if min(r,g,b)>200 else '?')

    @staticmethod
    def direction_doc():
        def say(*parts):   # a sentence with enough words to count as written
            return ' '.join(parts)+' because the story itself asks for it here.'
        vocab={'T1':'wry curious amused quick bright friend jokes noticing oddly specific detail laughing',
               'T2':'hushed intimate patient quiet witness close breath dusk candle whisper still lingering'}
        def sample(tid, m):   # each treatment in its own words, as real treatments differ
            w=vocab[tid].split()
            return ' '.join(f'{m} {w[i%12]} {w[(i+3)%12]} {w[(i+5)%12]} moment {i} {w[(i+7)%12]}.' for i in range(9))
        treatments=[]
        for tid,tone in (('T1','wry curious friend'),('T2','hushed intimate witness')):
            treatments.append({'id':tid,'name':tone,
                **{k:say(tone,k.replace('_',' '),'for this video') for k in
                   ('narrator','writing_voice','structure_and_pace','visual_language','sound',
                    'audiovisual_relationship','emotional_course','evidence_used','departures','risks')},
                'samples':{m:{'narration':sample(tid,m),
                              'picture':f'{tid} picture for the {m}: a wide frame with one figure and the road ahead.'}
                           for m in ('opening','quiet_middle','turning_point')},
                'carries_values':[{'value':'R1','how':f'the {tone} narrator lets the battle show what the order made possible'}]})
        def cand(cid, subject, claim, what, why, reward, material, step):
            return {'id':cid,'subject':subject,'value_form':'a consequential decision','factual':True,
                    'what_happens':say(what),'why_it_matters':say(why),'reward':say(reward),
                    'strongest_material':[{'id':'M1','what':material,'certainty':'established','claims':[claim]}],
                    'runtime':{'progression':[{'adds':step,'material':['M1']}],'verdict':'sustains',
                               'why':say('each discovery opens the next, and the consequence fills the end')},
                    'feasibility':say('maps and period artifacts can show every step'),
                    'payoff':{'shape':'builds_to','rests_on':['M1'],'why_substantial':say('the viewer sees a quiet order decide a loud outcome'),
                              'needs_first':'what the army needed in order to move',
                              'worth_the_buildup':say('each step of the build-up is a discovery of its own')}}
        subject={'scope':{'kind':'niche','user_words':'military history','niche':'military history',
                          'understood_as':'wars, campaigns and the decisions and logistics that shaped them',
                          'boundary':'a story whose subject is not a war or a campaign, only told with its techniques'},
                 'audience_value':say('viewers of this niche come for decisions whose consequences they can follow'),
                 'from_references':[{'ref':'V001','at':'00:10-00:30','observed':'the narrator names the cost before the decision',
                                     'interpretation':'the stakes come before the turn, so the turn lands'}],
                 'candidates':[cand('T1','a supply decision before a battle','C01',
                                    'an order moves the depots before the march',
                                    'without the depots the army could not have moved at all',
                                    'the viewer sees how a quiet order decided a loud battle',
                                    'the order that moved the depots','the order, then what it made possible'),
                               cand('T2','a forgotten map error','C02',
                                    'a surveyor draws a valley a mile too far north',
                                    'every later plan inherits the error until someone walks it',
                                    'one wrong line explains a dozen failed marches',
                                    'the survey sheet with the misplaced valley','the error, then its long shadow')],
                 'selection':{'candidate':'T1','why':say('its consequence is clear and rests on a primary record'),
                              'decisive_material':['M1'],
                              'over_alternatives':[{'candidate':'T2','why_not':say('the map error rests on one later study only')}]},
                 'value_to_carry':[{'id':'R1','what':'the supply decision decided the battle',
                                    'why_it_matters':'without it the army could not have moved',
                                    'certainty':'established','rests_on':['M1'],'payoff':True}]}
        return {'video':1,
                'subject':subject,
                'evidence':{'references':['V001','V002'],
                            'observations':[{'ref':'V001','at':'00:00-00:30','what':'the narrator opens on a detail','label':'O'},
                                            {'ref':'V002','at':'02:10-02:40','what':'the picture holds while the voice slows','label':'O'},
                                            {'ref':'V001','at':'05:00-05:20','what':'cuts quicken at the turn','label':'O'}],
                            'unknowns':['audience retention is not available']},
                'approaches':[{'id':f'A{i}','changes':[axis],'pitch':say('pitch',axis),'strongest_case':say('case',axis),
                               'long_form_risk':say('risk',axis),'challenges_reference_formula':i==3}
                              for i,axis in enumerate(['perspective','scale','structure','voice','visualization'],1)],
                'chosen_approach':{'id':'A3','why':say('the structure approach wins'),'runner_up':'A1',
                                   'why_not_runner_up':say('the perspective approach repeats the references'),
                                   'exploration':say('perspective, scale, structure, voice and picture were each tried')},
                'strategy':{k:say('strategy',k.replace('_',' ')) for k in
                            ('why_this_idea','viewer_experience','progression','fits_and_forced','facts_as_experience',
                             'picture_contribution','sound_and_breath','distinct_from_references')},
                'treatments':treatments,
                'decision':{'treatment':'T1','why':say('the wry friend holds twenty minutes'),
                            'taken_from_others':say('the hushed close of the second treatment'),
                            'carries_payoff':say('the friend sets up what the army needs, then lets the battle answer it')}}

    def clear_development(self, kind):
        """A reader for whom the whole video is clear and pays: the three judgements given, nothing to find."""
        d={'what_happened':'the whole story is easy to follow','why_it_matters':'each turn changes what the people can do',
           'would_be_different':'without each turn the people would be stuck','learned_when':'before',
           'why_from':'the video','event':'clear','significance':'clear','reward':'landed'}
        if kind=='final':
            return [dict(d,at='00:00-59:59')]
        lines=json.loads((self.run/'40-plans/video-01/script.json').read_text(encoding='utf-8'))['lines']
        return [dict(d,lines=f"{lines[0]['id']}-{lines[-1]['id']}")]

    def review(self, kind, findings, answers=None, file=None, expected_record=0, developments=None):
        extra=['--file',file] if file else []
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind',kind,*extra)
        self.assertTrue(Path(packet['packet']).is_file())
        if kind in ('script','final'):
            findings=[dict(f,likely_cause=f.get('likely_cause') or 'what the reader thinks causes it')
                      if isinstance(f,dict) and 'likely_cause' not in f else f for f in findings]
        doc={'reviewer':'test reader','findings':findings}
        if kind in ('script','final'):
            doc['developments']=developments if developments is not None else self.clear_development(kind)
        if kind=='treatment':
            meta=json.loads(Path(packet['packet']).with_suffix('.json').read_text(encoding='utf-8')) \
                if Path(packet['packet']).with_suffix('.json').is_file() else {}
            pm=next(iter(sorted((self.run/'40-plans/video-01/reviews').glob('packet-treatment-r*.json'))),None)
            meta=json.loads(pm.read_text(encoding='utf-8')) if pm else meta
            if meta.get('scope_request'):
                doc['on_request']={lab:'yes: it stays within what was asked' for lab in meta.get('labels') or {}}
        save(Path(packet['findings_file']),doc)
        rec=cli('review-record','--run',self.run,'--video',1,'--kind',kind,expected=expected_record)
        if answers is not None:
            self.answer_file(rec['answers_file'],{'answers':answers})
        return packet,rec

    def answer_file(self, path, doc, reconcile='same'):
        """The director's answers written into the answers file review-record started (its reconciliation block kept);
        each key moment reconciled with the reader's account as `reconcile` says ('same' by default, None to leave it)."""
        path=Path(path)
        cur=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        cur.update(doc)
        if reconcile is not None:
            for bid,r in (cur.get('reconcile') or {}).items():
                if isinstance(reconcile,dict):
                    r.update(reconcile.get(bid) or {})
                elif not r.get('verdict'):
                    r.update(verdict=reconcile,note='the reader took the meaning the beat map plans for this moment')
        save(path,cur)

    def lock_direction(self, vd):
        save(vd/'direction.json',self.direction_doc())
        self.review('treatment',[{'id':'F1','severity':'minor','treatment':'A','problem':'the quiet middle may wear thin',
                                  'suggestion':'vary it'}],
                    {'F1':{'action':'kept','note':'the quiet middle is meant to rest the viewer'}})
        return cli('direction-lock','--run',self.run,'--video',1)

    def review_script(self):
        return self.review('script',[{'id':'F1','severity':'minor','lines':['L001-L002'],'problem':'the opening starts slowly'}],
                           {'F1':{'action':'kept','note':'the slow start is the treatment choice'}})

    def write_plan(self, lock=True, review_script=True):
        cli('length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
            '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145,'--pace-why','the test narrator reads at this pace')
        vd=self.run/'40-plans/video-01'
        save(vd/'blueprint.json',{'audience_promise':'Understood decision','central_question':'What happened?',
                                'narrative_approach':'Third-person procedural account of a single decision',
                                'why_this_length':'Five discoveries','original_angle':'Logistical stakes',
                                'human_lens':'People at crossroads','ending_payoff':'An earned conclusion',
                                'audience_knows':'that wars need supplies, but not how a single order moved them',
                                'visual_grammar':'Maps and restrained artifacts','factuality':'factual',
                                'research_sources':['S1','S2'],'title':'A test title'})
        self.measure_refs()
        if lock:
            self.lock_direction(vd)     # creative direction first: before any script exists
        words='careful planning and real consequences shaped every difficult choice and practical tradeoff through time and constrained people with different information under meaningful pressure at each stage'
        self.assertEqual(len(words.split()),26)
        lines=[{'id':f'L{i:03}','text':words+ ' changed.', 'pause_after_s':0} for i in range(1,53)]
        # Each line 27 spoken tokens x 52 = 1404: about 581 seconds at 145 wpm.
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines,'tags_exception':TAG_EXCEPTION})
        beats=[{'id':f'B{i:02}','start_s':(i-1)*120, 'end_s':i*120,
                'line_start':(i-1)*10+1 if i<5 else 41,
                'line_end':i*10 if i<5 else 52,
                'narrative_job':'genuinely deliver new evidence','visual_intent':'a purposeful comparison',
                'experience':'the viewer understands a new constraint','narration_direction':'curious, quickening',
                'sound_direction':'room tone, then a low pulse','pace':'brisk'} for i in range(1,6)]
        # the ending is where the researched value lands (topic discovery: a key moment carries it)
        beats[4].update({'key_moment':'the earned conclusion','carries':['R1'],
                         'significance':{'matters_because':'the conclusion shows what the quiet decision cost and saved',
                                         'reward':'an earned answer','certainty':'established',
                                         'self_contained':'everything it needs is given inside this beat'}})
        save(vd/'beat-map.json',{'target_length_s':600,'beats':beats})
        (vd/'editorial-review.md').write_text('## Self-audit\nNotes.\n',encoding='utf-8')
        if lock and review_script:
            self.review_script()
        return vd

    def test_plan_audio_partial_and_timeline(self):
        vd=self.write_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        dry=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4')
        self.assertEqual(dry['mode'],'dry_run_no_charges')
        self.assertGreater(dry['characters_total'],1000)
        # --max-parts: validated even in dry-run (no network/billing involved either way).
        cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4',
            '--max-parts','0',expected=2)
        self.assertEqual(cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID',
                             '--model-id','eleven_v4','--max-parts','1')['mode'],'dry_run_no_charges')
        self.assertEqual(cli('audio-check','--run',self.run,'--video',1,expected=2)['ready'],False)
        # An incomplete voice recording never makes the audio gate pass.
        d=self.run/'50-audio/video-01';d.mkdir(parents=True,exist_ok=True)
        specs=dry['candidate_manifest']
        save(d/'manifest.json',{**specs,'status':'partial','finished_parts':[]})
        self.assertIn('audio_is_partial_or_unverified',cli('audio-check','--run',self.run,'--video',1,expected=2)['issues'])
        # Simulate the exact planned speech coverage with a short surrogate audio part;
        # rejection occurs because the actual join is short, despite a complete flag.
        for chunk in specs['chunks']:
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                            '-i','anullsrc=r=8000:cl=mono','-t','2','-c:a','libmp3lame','-b:a','32k',str(d/chunk['file'])],check=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(d/specs['chunks'][0]['file']),
                        str(d/'narration.wav')],check=True)
        # Complete claims/line coverage, but duration still wildly below user's lock.
        save(d/'manifest.json',{**specs,'status':'complete','finished_parts':[c['id'] for c in specs['chunks']]})
        fail=cli('audio-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('narration_duration_outside_locked_tolerance',fail['issues'])
        # Even a visually complete timeline cannot pass without verified narration.
        tdir=self.run/'70-edit/video-01';tdir.mkdir(parents=True)
        save(tdir/'timeline.json',{'canvas':'1920x1080','visual_segments':[
            {'start_s':i*120,'end_s':(i+1)*120,'beat_id':f'B{i+1:02}',
             'purpose':'support the story with new visual information'} for i in range(5)]})
        self.assertIn('audio_gate_failed',cli('timeline-check','--run',self.run,'--video',1,expected=2)['issues'])
        # A cut that follows a beat the plan doesn't have is caught, not silently accepted.
        tl=json.loads((tdir/'timeline.json').read_text()); tl['visual_segments'][0]['beat_id']='B99'
        save(tdir/'timeline.json',tl)
        self.assertIn('visual_1_beat_not_in_beat_map',cli('timeline-check','--run',self.run,'--video',1,expected=2)['issues'])
        # A two-second export must not pass the 600s Standard.
        short=self.home/'references/video_1.mp4'
        res=cli('export-check','--run',self.run,'--video',1,'--file',short,expected=2)
        self.assertIn('export_duration_misses_user_locked_length',res['issues'])

    def load_core(self):
        spec=importlib.util.spec_from_file_location('static_studio_core', TOOL)
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_tags_pauses_and_content_flags(self):
        core=self.load_core()
        # Tags are sent but never spoken: not counted as words.
        self.assertEqual(core.count_words('[pause] And then [softly, slowly] the night comes.'),5)
        lines=[{'id':'L001','text':'There is one road.','pause_after_s':2,'pause_via':'tag'},
               {'id':'L002','text':'[pause] And then the night comes.'},
               {'id':'L003','text':'They look the same.','pause_after_s':4},
               {'id':'L004','text':'[gunshot] It is over.','pause_after_s':5,'pause_via':'edit'}]
        tags,issues=core.script_tags(lines)
        self.assertEqual([t['tag'] for t in tags],['[pause]','[gunshot]'])
        self.assertIn('audio_tag_not_for_narration:L004:[gunshot]',issues)
        plan,pissues=core.script_pause_plan(lines)
        self.assertIn('pause_L003_over_1s_needs_pause_via_tag_or_edit',pissues)
        self.assertEqual(core.edit_holds_s(lines),5.0)
        bad=[{'id':'L001','text':'A line.','pause_after_s':3,'pause_via':'tag'},{'id':'L002','text':'No tag here.'}]
        self.assertTrue(any('via_tag_but_no_pause_tag' in x for x in core.script_pause_plan(bad)[1]))
        self.assertIn('audio_tag_malformed_brackets:L001',core.script_tags([{'id':'L001','text':'[pause A line.'}])[1])
        # A flagged word needs an answer under a "Content flags" heading, not a mention anywhere.
        rows=[{'id':'L011','text':"You'd be home by Christmas."},{'id':'L020','text':'The wounded cross.'}]
        flags,fi=core.content_flags(rows,'# Review\nL011 is great.\n')
        self.assertEqual([f['line'] for f in flags],['L011'])
        self.assertIn('content_flag_unreviewed:L011:holiday_religion_superstition',fi)
        self.assertFalse(core.content_flags(rows,'## Content flags\n- L011: rewritten.\n')[1])

    def test_parts_keep_boundaries_and_alignment(self):
        core=self.load_core()
        lines=[{'text':f'Line number {i} is here.'} for i in range(1,9)]
        old=core.chunks_for_lines(lines,60)
        self.assertGreater(len(old),2)
        manifest=[{'id':i+1,'line_start':c['line_start'],'line_end':c['line_end']} for i,c in enumerate(old)]
        lines[1]['text']='Line two.'   # shorter: fresh greedy chunking could pull the next line into part 1
        kept=core.chunks_from_manifest(manifest,lines)
        self.assertEqual([(c['line_start'],c['line_end']) for c in kept],[(c['line_start'],c['line_end']) for c in old])
        self.assertIsNone(core.chunks_from_manifest(manifest,lines[:-1]))   # a removed line: boundaries no longer fit
        words=[{'start_s':i*0.5,'end_s':i*0.5+0.4,'text':w} for i,w in enumerate('you are twenty years old this is 1950'.split())]
        tok,ratio=core.align_lines(['You are twenty years old.','[pause] This is 1950.'],words)
        self.assertEqual(ratio,1.0)
        self.assertEqual(tok[1][0],(2.5,2.9))
        prof=core.pause_profile([{'start_s':0,'end_s':1},{'start_s':3,'end_s':4},{'start_s':4.1,'end_s':5}])
        self.assertEqual(prof['longest_pause_s'],2.0)

    def test_narration_must_leave_room_in_export_window(self):
        vd=self.write_plan()
        d=self.run/'50-audio/video-01';d.mkdir(parents=True,exist_ok=True)
        dry=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4')
        specs=dry['candidate_manifest']
        # one 615 s narration: inside audio's own 4% (600 +/- 24) but, with a planned 5 s closing hold,
        # outside the export window (600 +/- 15)
        for chunk in specs['chunks']:
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','anullsrc=r=8000:cl=mono',
                            '-t',str(615/len(specs['chunks'])),'-c:a','libmp3lame','-b:a','32k',str(d/chunk['file'])],check=True)
        (d/'parts.txt').write_text(''.join(f"file '{(d/c['file']).as_posix()}'\n" for c in specs['chunks']))
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(d/'parts.txt'),
                        str(d/'narration.wav')],check=True)
        save(d/'manifest.json',{**specs,'status':'complete','finished_parts':[c['id'] for c in specs['chunks']]})
        script=json.loads((vd/'script.json').read_text())
        script['lines'][-1].update({'pause_after_s':5,'pause_via':'edit',
                                    'pause_purpose':'the last picture stays while the ending settles',
                                    'pause_picture':'the empty road at dusk, the last light going',
                                    'pause_sound':'the bed resolves on its last chord'})
        save(vd/'script.json',script)
        res=cli('audio-check','--run',self.run,'--video',1,expected=2)
        self.assertNotIn('narration_duration_outside_locked_tolerance',res['issues'])
        self.assertIn('narration_plus_edit_holds_longer_than_export_window',res['issues'])
        self.assertEqual(res['edit_holds_s'],5.0)
        # A closing hold added after the script read is read again before anything is recorded.
        self.assertTrue(any('the ending' in x for x in cli('plan-check','--run',self.run,'--video',1,expected=2)['issues']))
        self.review_script()
        # Only the changed part would be re-recorded, never the whole narration.
        script['lines'][0]['text']='A changed first line.'
        save(vd/'script.json',script)
        again=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4')
        self.assertEqual(again['changed_recorded_parts'],[1])
        self.assertEqual(again['parts_to_record'],[1])
        refused=subprocess.run([sys.executable,str(TOOL),'tts','--run',str(self.run),'--video','1','--voice-id','TESTID',
                                '--model-id','eleven_multilingual_v2'],capture_output=True,text=True)
        self.assertEqual(refused.returncode,2)   # only eleven_v4 / eleven_v4_turbo are accepted
        self.assertIn('eleven_v4_turbo',refused.stderr)

    # ---------------------------------------------------------------- creative process
    def test_creative_planning_precedes_script(self):
        vd=self.write_plan(lock=False)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        for issue in ('direction_missing','direction_lock_missing','script_review_missing'):
            self.assertIn(issue,res['issues'])
        # Paid narration stays refused while the plan isn't ready (dry run: no network, no credits).
        tts=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4',expected=2)
        self.assertIn('direction_lock_missing',tts['details'])
        # The cold read of a script needs the locked direction it was written from.
        cli('review-packet','--run',self.run,'--video',1,'--kind','script',expected=2)
        # The script already exists: the direction can't be locked as if it had come first...
        save(vd/'direction.json',self.direction_doc())
        self.review('treatment',[],{})
        refused=cli('direction-lock','--run',self.run,'--video',1,expected=2)
        self.assertIn('BEFORE scriptwriting',refused['error'])
        # ...only as an explicit, recorded exception that every plan-check shows.
        late=cli('direction-lock','--run',self.run,'--video',1,'--late','script drafted before the direction step existed')
        self.assertTrue(late['late'])
        self.review_script()
        # What existed before the direction was made without it: each piece is revised for real or reapproved.
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertEqual(sorted(res['issues']),['beat_map_made_for_an_earlier_direction','script_made_for_an_earlier_direction'])
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','script','--reason','fine',expected=2)  # a real reason
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','script',
            '--reason','the script already speaks in the chosen wry voice')
        beats=json.loads((vd/'beat-map.json').read_text())
        beats['beats'][0]['narration_direction']='wry and quick, a friend setting up the puzzle'
        save(vd/'beat-map.json',beats)
        ok=cli('plan-check','--run',self.run,'--video',1)
        self.assertTrue(ok['ready'])
        self.assertTrue(any('locked after the script existed' in w for w in ok['warnings']))
        self.assertTrue(any(w.startswith('script reapproved') for w in ok['warnings']))
        self.assertTrue(ok['creative']['locked_late'])

    def test_direction_needs_real_alternatives_and_measured_evidence(self):
        core=self.load_core()
        self.measure_refs()
        vd=self.run/'40-plans/video-01'
        d=self.direction_doc()
        for a in d['approaches']:
            a['changes']=['structure']                 # five subjects told the same way are one approach
            a['challenges_reference_formula']=False
        d['treatments']=d['treatments'][:1]
        d['treatments'][0]['samples']['quiet_middle']['narration']='Too short to judge.'
        d['evidence']['references']=['V001','V003']    # V003 was never measured
        save(vd/'direction.json',d)
        issues=core.direction_facts(self.run,1)['issues']
        for issue in ('approaches_differ_on_fewer_than_3_axes','no_approach_challenges_the_reference_formula',
                      'direction_needs_2_to_4_distinct_treatments',
                      'treatment_T1_sample_quiet_middle_narration_under_50_words',
                      'direction_evidence_without_av_profile:V003'):
            self.assertIn(issue,issues)
        self.assertIn('direction_needs_2_to_4_distinct_treatments',cli('direction-lock','--run',self.run,'--video',1,expected=2)['details'])
        save(vd/'direction.json',self.direction_doc())
        self.assertEqual(core.direction_facts(self.run,1)['issues'],[])

    def test_reviews_cannot_be_bypassed(self):
        vd=self.write_plan(review_script=False)
        self.assertIn('script_review_missing',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        _,rec=self.review('script',[{'id':'F1','severity':'major','lines':['L003-L004'],
                                     'problem':'the recap stalls the opening badly'}])
        ans=Path(rec['answers_file'])
        self.assertIn('script_review_r1_unanswered:F1',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        cli('review-packet','--run',self.run,'--video',1,'--kind','script',expected=2)   # no new read before answering
        self.answer_file(ans,{'answers':{'F1':{'action':'kept','note':'we like the recap a lot here'}}})   # a major is never just kept
        self.assertIn('script_review_r1_unanswered:F1',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        self.answer_file(ans,{'answers':{'F1':{'action':'revised','lines':['L003'],'note':''}}})           # claimed, not done
        self.assertIn('script_review_r1_revised_but_unchanged:F1',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        script=json.loads((vd/'script.json').read_text())
        script['lines'][2]['text']='A shorter, sharper third line.'
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('script_review_round_2_required',res['issues'])   # a major finding asks for a fresh read
        self.assertFalse([x for x in res['issues'] if 'unchanged' in x])
        self.review('script',[{'id':'F1','severity':'minor','lines':['L010'],'problem':'one line still drags a bit'}],
                    {'F1':{'action':'kept','note':'that drag is a deliberate breath'}})
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # Sealed findings can't be softened afterwards.
        r1=vd/'reviews/script-r1.json'
        rec1=json.loads(r1.read_text()); rec1['findings'][0]['severity']='minor'; save(r1,rec1)
        self.assertIn('script_review_r1_findings_altered',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])

    def test_outdated_approvals_are_rejected(self):
        vd=self.write_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        original=json.loads((vd/'script.json').read_text())
        rewritten=json.loads(json.dumps(original))
        for row in rewritten['lines'][:20]:
            row['text']='A different sentence written after the read was approved, with new content.'
        save(vd/'script.json',rewritten)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('script_changed_after_review') for x in res['issues']))
        small=json.loads(json.dumps(original)); small['lines'][5]['text']='A trimmed line.'
        save(vd/'script.json',small)   # a length trim on one line: shown, not blocking
        ok=cli('plan-check','--run',self.run,'--video',1)
        self.assertTrue(ok['ready'])
        self.assertTrue(any('edited after its last read' in w for w in ok['warnings']))
        d=json.loads((vd/'direction.json').read_text())
        # A harmless change (the evidence, the alternatives, the reasons): no new revision, nothing to redo.
        d['evidence']['unknowns'].append('how the comments will react')
        save(vd/'direction.json',d)
        self.assertIn('direction_changed_since_lock',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        cli('direction-lock','--run',self.run,'--video',1,expected=2)          # any change needs --revise
        h=cli('direction-lock','--run',self.run,'--video',1,'--revise','noted one more unknown')
        self.assertEqual((h['production_rev'],h['affects'],h['outdated_now']),(1,[],[]))
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # A meaningful change (the strategy): a new revision, and what it touches must follow it.
        d['strategy']['progression']+=' And a new idea arrives late in the plan.'
        save(vd/'direction.json',d)
        m=cli('direction-lock','--run',self.run,'--video',1,'--revise','progression sharpened after the cold read')
        self.assertEqual((m['production_rev'],m['outdated_now']),(2,['beat-map','script']))
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('beat_map_made_for_an_earlier_direction',res['issues'])
        tts=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4',expected=2)
        self.assertIn('script_made_for_an_earlier_direction',tts['details'])   # no paid narration on an old script
        beats=json.loads((vd/'beat-map.json').read_text())
        beats['beats'][2]['experience']='the late idea lands as a real surprise'
        save(vd/'beat-map.json',beats)                                         # updated for real
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','script',
            '--reason','the new idea only changes the beat order, not a single line')
        ok=cli('plan-check','--run',self.run,'--video',1)
        self.assertTrue(ok['ready'])
        self.assertTrue(any('reapproved for direction revision 2' in w for w in ok['warnings']))
        # Refining the chosen treatment needs no new blind read; what that field feeds must follow it, nothing else.
        d['treatments'][0]['narrator']+=' Now noticeably warmer.'
        save(vd/'direction.json',d)
        r=cli('direction-lock','--run',self.run,'--video',1,'--revise','the narrator warmed up')
        self.assertEqual(r['production_rev'],3)
        self.assertEqual(r['affects'],['beat-map','script','voice','narration'])   # the voice choice is asked again too
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('script_made_for_an_earlier_direction',res['issues'])
        self.assertTrue(any('refined after its blind read' in w for w in res['warnings']))   # shown, never silent
        # A rewrite of the chosen treatment is a new treatment: it gets its own blind read first.
        rewrite=json.loads(json.dumps(d))
        for k in ('narrator','writing_voice','structure_and_pace','visual_language','sound','audiovisual_relationship',
                  'emotional_course','departures','risks','evidence_used'):
            rewrite['treatments'][0][k]='A gravel voiced coastguard reads old telegrams aloud beside a lighthouse lamp.'
        for m in ('opening','quiet_middle','turning_point'):
            rewrite['treatments'][0]['samples'][m]={'narration':' '.join(f'Telegram {i} crackles over static while the lighthouse beam sweeps the harbour wall.' for i in range(6)),
                                                    'picture':'a lighthouse lamp room at night, telegrams pinned to the wall'}
        save(vd/'direction.json',rewrite)
        r=cli('direction-lock','--run',self.run,'--video',1,'--revise','a whole new narrator and look',expected=2)
        self.assertIn('rewritten since its blind read',r['error'])
        # Only a treatment that never had a blind read can't be chosen.
        t3=json.loads(json.dumps(d['treatments'][1])); t3['id']='T3'
        d['treatments'].append(t3); d['decision']['treatment']='T3'
        save(vd/'direction.json',d)
        r=cli('direction-lock','--run',self.run,'--video',1,'--revise','switch to a brand-new treatment',expected=2)
        self.assertIn('never in a blind comparison',r['error'])

    def test_duration_rules_hold_with_the_creative_process(self):
        vd=self.write_plan()
        lock_before=(vd/'length-lock.json').read_bytes()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        script=json.loads((vd/'script.json').read_text())
        for row in script['lines']:
            row['text']='Short line here.'
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('script_forecast_misses_locked_length_by_over_8pct',res['issues'])
        self.assertEqual(lock_before,(vd/'length-lock.json').read_bytes())   # no creative step touches the lock
        cli('length','--run',self.run,'--video',1,'--mode','own','--niche','military history',
            '--story-form','historical narrative','--minutes',3,'--pace-wpm',145,'--pace-why','the test narrator reads at this pace',expected=2)

    def test_final_review_follows_the_exact_export(self):
        vd=self.write_plan()
        def export(path,colour):
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'color=c={colour}:s=320x180:r=30',
                            '-f','lavfi','-i','sine=frequency=220:sample_rate=16000','-t','4','-shortest',
                            '-pix_fmt','yuv420p','-c:a','aac',str(path)],check=True)
        exp=self.home/'export.mp4'; export(exp,'navy')
        tr=self.home/'export-transcript.json'
        save(tr,{'status':'transcribed','segments':[{'start_s':0.2,'end_s':3.6,'text':'words',
                 'words':[{'start_s':round(0.2+0.3*i,2),'end_s':round(0.45+0.3*i,2),'text':' word'} for i in range(11)]}]})
        prof=cli('av-profile','--run',self.run,'--video',1,'--file',exp,'--transcript',tr)
        self.assertGreaterEqual(prof['profiles']['video-01']['sheets'],1)
        self.assertGreaterEqual(prof['profiles']['video-01']['shot_sheets'],1)        # every shot once, for the reviewer
        self.assertIn('final_review_missing',cli('release-check','--run',self.run,'--video',1,'--file',exp,expected=2)['issues'])
        pk=cli('review-packet','--run',self.run,'--video',1,'--kind','final','--file',exp)
        worded=[{'id':'F1','severity':'minor','at':'Held silences 00:01-00:03, 00:05',
                 'problem':'the opening picture holds too long','likely_cause':'the hold outlasts the line'}]
        save(Path(pk['findings_file']),{'reviewer':'test reader','findings':worded,
                                        'developments':self.clear_development('final')})
        bad=cli('review-record','--run',self.run,'--video',1,'--kind','final',expected=2)
        self.assertIn('--normalize-at',' '.join(bad['details']))                # words around the times: refused...
        rec=cli('review-record','--run',self.run,'--video',1,'--kind','final','--normalize-at')
        sealed=json.loads(Path(rec['record']).read_text(encoding='utf-8'))      # ...or only the times are kept,
        self.assertEqual(sealed['at_normalized'],['F1'])                           # the reviewer's words beside them
        self.assertEqual(sealed['findings'][0]['at'],'00:01-00:03, 00:05')
        self.assertEqual(sealed['findings'][0]['at_original'],'Held silences 00:01-00:03, 00:05')
        self.assertEqual(sealed['findings'][0]['problem'],'the opening picture holds too long')   # its judgement untouched
        ptext=Path(pk['packet']).read_text(encoding='utf-8')
        self.assertIn('## Shot sheets: every shot once, in order',ptext)
        self.assertNotIn('meant to feel like',ptext)                              # the intent stays with the director
        self.assertIn('## The parts of this cut (by time only)',ptext)
        pmeta=json.loads((self.run/'40-plans/video-01/reviews/packet-final-r1.json').read_text(encoding='utf-8'))
        self.assertIn('key_moment_spans',pmeta)                                   # weighed as they stood at the read
        listed=[x[2:] for x in ptext.splitlines() if x.startswith('- ') and x.lower().endswith(('.jpg','.png'))]
        self.assertTrue(listed)                                                     # the sheets travel with the packet:
        for x in listed:                                                            # inside the reader's own folder
            self.assertTrue(Path(x).is_file() and Path(pk['packet']).parent in Path(x).parents, x)
        self.assertNotIn(str(self.run),ptext)
        self.assertIn('final_review_r1_unanswered:F1',cli('release-check','--run',self.run,'--video',1,'--file',exp,expected=2)['issues'])
        self.answer_file(Path(rec['answers_file']),{'answers':{'F1':{'action':'kept','note':'the hold is the planned breath'}}})
        rel=cli('release-check','--run',self.run,'--video',1,'--file',exp,expected=2)
        self.assertFalse([x for x in rel['issues'] if x.startswith('final_')])   # other gates (no audio here) still block
        self.assertEqual(rel['release_status'],'blocked')
        exp2=self.home/'export-2.mp4'; export(exp2,'maroon')                    # a different cut: not what was reviewed
        self.assertIn('final_review_outdated',cli('release-check','--run',self.run,'--video',1,'--file',exp2,expected=2)['issues'])

    def test_shot_plan_is_a_visual_argument(self):
        vd=self.write_plan()
        same='a wide valley at dawn with one narrow road and a column of small trucks far below'
        shots=[{'id':'S1','beat_id':'B01','line_start':'L001','line_end':'L010','composition':'wide',
                'new_thing':'the whole valley and the single road out','frame_prompt':same},
               {'id':'S2','beat_id':'B02','line_start':'L011','line_end':'L020','composition':'wide',
                'new_thing':'','frame_prompt':same+' again'},
               {'id':'S3','beat_id':'B03','line_start':'L021','line_end':'L030','composition':'wide',
                'new_thing':'how thin the column is against the ridge','frame_prompt':'a ridge line at night with fires along its length'},
               {'id':'S4','beat_id':'B04','line_start':'L031','line_end':'L052','composition':'wide',
                'new_thing':'the bridge gap in the pass that stops everything','frame_prompt':'a broken bridge over a gorge in snow with engineers looking down'}]
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        res=cli('shot-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('shot_S2_missing_new_thing',res['issues'])
        self.assertIn('beat_B05_has_no_shot',res['issues'])
        self.assertIn('shot_S4_lines_outside_beat_B04',res['issues'])   # S4 runs on into B05's lines
        self.assertTrue(any('nearly the same' in w for w in res['warnings']))
        self.assertTrue(any('in a row of the same composition' in w for w in res['warnings']))

    def test_a_shot_can_cut_in_on_a_word_inside_a_line(self):
        self.write_plan()
        base='a wide valley at dawn with one narrow road and a column of small trucks far below'
        props=['a ridge line at night with fires along its length', 'a broken bridge over a gorge in snow',
               'a radio operator bent over a set in a cellar', 'a harbour crowded with grey ships at noon',
               'a general reading a telegram beside a stove', 'a field hospital tent in heavy rain']
        def shot(i, b, a, z, **kw):
            return {'id': f'S{i}', 'beat_id': b, 'line_start': a, 'line_end': z, 'composition': f'c{i}',
                    'new_thing': 'something new the viewer sees here', 'frame_prompt': props[i - 1], **kw}
        shots=[shot(1,'B01','L001','L010'), shot(2,'B02','L011','L015'), shot(3,'B02','L015','L020',start_word=5),
               shot(4,'B03','L021','L030'), shot(5,'B04','L031','L040'), shot(6,'B05','L041','L052')]
        plan=self.run/'60-visuals/video-01/shot-plan.json'
        save(plan,{'video':1,'shots':shots})
        issues=cli('shot-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in issues if 'contiguous' in x or 'start_word' in x], issues)
        shots[2]['start_word']=40                                   # the line has 27 words
        save(plan,{'video':1,'shots':shots})
        self.assertIn('shot_S3_start_word_not_in_line',cli('shot-check','--run',self.run,'--video',1,expected=None)['issues'])
        shots[2]['start_word']=5; shots[2]['line_start']='L016'     # a cut word starts inside the line S2 ends on
        save(plan,{'video':1,'shots':shots})
        self.assertIn('shot_S3_lines_not_contiguous',cli('shot-check','--run',self.run,'--video',1,expected=None)['issues'])

    def test_every_narration_uses_expressive_cues_or_an_approved_exception(self):
        vd=self.write_plan()
        script=json.loads((vd/'script.json').read_text(encoding='utf-8'))
        script.pop('tags_exception')
        save(vd/'script.json',script)
        issues=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertTrue(any(x.startswith('no_expressive_tags') for x in issues))
        script['tags_exception']={'reason':'too short','approved_by_user':''}          # an exception needs a reason
        save(vd/'script.json',script)                                                  # and the user's own words
        issues=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertTrue(any(x.startswith('no_expressive_tags') for x in issues))
        script.pop('tags_exception')
        script['lines'][9]['text']='[thoughtful] '+script['lines'][9]['text']           # one purposeful cue, explained
        script['lines'][9]['cue_scope']='the whole line, then back to the level voice'
        save(vd/'script.json',script)
        (vd/'editorial-review.md').write_text('## Self-audit\nNotes.\n## Delivery and tags\nL010: the turn is a '
                                              'reflection, so the line settles thoughtfully.\n',encoding='utf-8')
        issues=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in issues if x.startswith('no_expressive_tags')])
        self.assertFalse([x for x in issues if x.startswith('tag_L010')])

    def test_the_cold_reader_is_isolated_and_its_findings_come_back_to_the_run(self):
        vd=self.write_plan(review_script=False)
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind','script')
        pk,fi=Path(packet['packet']),Path(packet['findings_file'])
        self.assertEqual(pk.parent,fi.parent)                                          # its own folder,
        self.assertNotIn(str(self.run.resolve()),str(pk.resolve()))                    # outside the run
        text=pk.read_text(encoding='utf-8')
        self.assertIn('likely_cause',text)
        self.assertIn('Following it by ear',text)
        self.assertIn('static-cold-reader',packet['next'])
        # a script-only read: no claim about the voice; no anchoring score, no cap on findings, real line ids
        self.assertIn('You are reading, not hearing',text)
        self.assertNotIn('"keep_watching_1_10": 7',text)
        self.assertNotIn('at most',text)
        head=text.split('## The narration')[0]
        ids={l['id'] for l in json.loads((vd/'script.json').read_text(encoding='utf-8'))['lines']}
        self.assertTrue(re.findall(r'L\d{3}',head))
        self.assertTrue(set(re.findall(r'L\d{3}',head)) <= ids, re.findall(r'L\d{3}',head))
        save(fi,{'reviewer':'test reader','developments':self.clear_development('script'),
                 'findings':[{'id':'F1','severity':'minor','lines':['L003'],
                 'problem':'a name arrives with no introduction','likely_cause':'a name nobody introduced'}]})
        cli('review-record','--run',self.run,'--video',1,'--kind','script')
        kept=json.loads((vd/'reviews/script-r1-findings.json').read_text(encoding='utf-8'))
        self.assertEqual(kept['findings'][0]['likely_cause'],'a name nobody introduced')

    def test_review_read_runs_the_reader_restricted_in_its_own_folder(self):
        vd=self.write_plan(review_script=False)
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind','script')
        stub=Path(self.tmp.name)/'stub_reader.py'
        stub.write_text('import json,os,sys\n'
                        'args=sys.argv[1:]\n'
                        'assert "--restricted" in args and args[args.index("--tools")+1]=="Read,Write", args\n'
                        'prompt=args[args.index("-p")+1]\n'
                        'assert prompt.startswith("Read only ") and os.path.samefile(os.path.dirname(prompt[10:].split(" and follow")[0]),os.getcwd()), (prompt,os.getcwd())\n'
                        'json.dump({"reviewer":"stub","developments":[{"lines":"L001-L052","what_happened":"a whole '
                        'story is told","why_it_matters":"each turn changes what they can do","why_from":"the video",'
                        '"would_be_different":"they would be stuck","learned_when":"before",'
                        '"event":"clear","significance":"clear","reward":"landed"}],'
                        '"findings":[{"id":"F1","severity":"minor","lines":["L002"],'
                        '"problem":"the second line repeats the first one","likely_cause":"the same point again"}]},'
                        'open("findings.json","w"))\n',encoding='utf-8')
        os.environ['STUDIO_CLAUDE_BIN']=json.dumps([sys.executable,str(stub)])
        try:
            res=cli('review-read','--run',self.run,'--video',1,'--kind','script')
        finally:
            os.environ.pop('STUDIO_CLAUDE_BIN',None)
        self.assertEqual(Path(res['findings_file']),Path(packet['findings_file']))
        cli('review-record','--run',self.run,'--video',1,'--kind','script')
        self.assertTrue((vd/'reviews/script-r1-findings.json').is_file())
        self.assertIn('review-read',packet['next'])

    def test_a_finding_about_a_silence_is_revised_by_changing_the_silence(self):
        vd=self.write_plan(review_script=False)
        script=json.loads((vd/'script.json').read_text(encoding='utf-8'))
        script['lines'][4].update({**HELD,'pause_total_s':2.4,'pause_via':'edit'})
        save(vd/'script.json',script)
        _,rec=self.review('script',[{'id':'F1','severity':'minor','lines':['L005'],
                                     'problem':'the silence after this line goes on too long'}])
        script['lines'][4].pop('pause_total_s',None)
        script['lines'][4].pop('pause_via',None)
        for k in list(HELD):
            script['lines'][4].pop(k,None)
        save(vd/'script.json',script)                                   # the text is the same, the silence is gone
        self.answer_file(Path(rec['answers_file']),{'answers':{'F1':{'action':'revised','lines':['L005'],
                                                         'note':'the planned silence after this line is removed'}}})
        issues=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in issues if 'revised_but_unchanged' in x])

    def test_writing_signals_count_what_a_listener_hears(self):
        core=self.load_core()
        lines=[{'id':'L001','text':'This is not a retreat. It is a plan.'},
               {'id':'L002','text':'This is not a defeat. It is a choice.'},
               {'id':'L003','text':'This is not a story. It is a warning.'},
               {'id':'L004','text':'Through mountains. In winter. While fighting.'},
               {'id':'L005','text':'They marched fourteen miles, then eleven, then ten, then twenty more.'},
               {'id':'L006','text':' '.join(['word']*40)+'.'},
               {'id':'L007','text':'The column is coming down the road tonight.'},
               {'id':'L008','text':'The column is coming down the road again.'},
               {'id':'L009','text':'The column is coming down the road at last.'}]
        s=core.writing_signals(lines,'en')
        self.assertTrue(any('column is coming down' in p['phrase'] for p in s['repeated_phrases']))
        self.assertTrue(any(x['shape']=='this is not _ | it is _' and x['times']==3 for x in s['repeated_sentence_shapes']))
        self.assertTrue(any(r['to']=='L004' for r in s['fragment_runs']))
        self.assertIn('L005',s['number_dense_lines'])
        self.assertEqual(s['long_sentences'][0]['line'],'L006')
        self.assertNotIn('repeated_sentence_shapes',core.writing_signals(lines,'de'))   # English heuristics stay English

    def narrated(self):
        """A locked direction, a 10-line script in two beats, and its recorded, measured narration (one part)."""
        vd=self.write_plan()
        lines=[{'id':f'L{i:03}','text':f'Line {i} tells the viewer something new about the road ahead tonight.'} for i in range(1,11)]
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        direction={'narrative_job':'deliver','visual_intent':'map','sound_direction':'bed','narration_direction':'curious'}
        save(vd/'beat-map.json',{'target_length_s':600,'beats':[
            {'id':'B01','start_s':0,'end_s':300,'line_start':1,'line_end':5,'experience':'oriented','pace':'brisk',**direction},
            {'id':'B02','start_s':300,'end_s':600,'line_start':6,'line_end':10,'experience':'uneasy','pace':'slow',**direction}]})
        d=self.run/'50-audio/video-01'; (d/'whisper').mkdir(parents=True)
        t,segs=0.3,[]
        for row in lines:          # what Whisper would have heard: the script's own words, in time
            s0,ws=t,[]
            for w in row['text'].split():
                ws.append({'start_s':round(t,3),'end_s':round(t+0.22,3),'text':' '+w}); t+=0.27
            segs.append({'start_s':round(s0,3),'end_s':round(t-0.05,3),'text':row['text'],'words':ws}); t+=0.4
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=150:sample_rate=16000',
                        '-t',f'{t+0.3:.2f}','-c:a','libmp3lame','-b:a','32k',str(d/'part-001.mp3')],check=True)
        save(d/'whisper/part-001.json',{'status':'transcribed','model':'medium','segments':segs})   # cached: no Whisper run
        (d/'whisper/part-001.txt').write_text('\n'.join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}" for s in segs),encoding='utf-8')
        text='\n'.join(r['text'] for r in lines)
        save(d/'manifest.json',{'model_id':'eleven_v4','voice_id':'TESTID','language':'en','status':'complete',
                                'finished_parts':[1],'voice_settings':{},
                                'chunks':[{'id':1,'line_start':1,'line_end':10,'file':'part-001.mp3','characters':len(text),
                                           'text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}]})
        return vd,d,cli('narration-measure','--run',self.run,'--video',1)

    def test_narration_measure_reports_delivery_per_beat(self):
        vd,d,out=self.narrated()
        self.assertEqual(out['alignment_match_ratio'],1.0)
        self.assertTrue(out['delivery'] and 'file' in out['delivery'],out.get('delivery'))
        dj=json.loads((d/'delivery.json').read_text())
        self.assertEqual(set(dj['spans']),{'B01','B02'})                    # the voice, beat by beat...
        self.assertEqual(dj['spans']['B02']['intended']['pace'],'slow')     # ...next to what each beat asked for
        self.assertEqual(set(dj['references']),{'V001','V002'})             # ...and to the locked references

    def shots_for_plan(self):
        """A shot plan for write_plan's five beats: one shot each, every one with its job and its own prompt."""
        ends={1:10,2:20,3:30,4:40,5:52}
        shots=[{'id':f'S{i}','beat_id':f'B0{i}','line_start':f'L{(i-1)*10+1:03}','line_end':f'L{ends[i]:03}',
                'composition':['wide','close','detail','wide','close'][i-1],
                'new_thing':f'what the viewer learns in beat {i} that the words leave out',
                'frame_prompt':f'a distinct picture {i} of the valley, {["dawn","noon","dusk","night","rain"][i-1]} light, one clear subject'}
               for i in range(1,6)]
        shots[4]['carries_significance']='the closing map shows the depots that made the march possible'
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        if (self.run/'40-plans/video-01/direction-lock.json').is_file() and \
                not (self.run/'60-visuals/video-01/style-lock.json').is_file():
            cli('style-lock','--run',self.run,'--video',1,'--style-prompt','painterly, soft edges','--departs-when','photorealistic, flat vector')
        return shots

    def test_generation_follows_the_approved_plan(self):
        vd=self.write_plan()
        shots=self.shots_for_plan()
        core=self.load_core()
        stills=self.home/'stills'
        job={'op':'generate','run':str(self.run),'video':1,
             'images':[{'shot_id':'S1','prompt':shots[0]['frame_prompt']+', painterly, soft edges','out':str(stills/'S1.png')}]}
        jobp=self.home/'stills-job.json'; save(jobp,job)
        ok=cli('media-check','--job',jobp,'--kind','stills')
        self.assertTrue(ok['ok'])
        self.assertEqual(ok['direction']['items'][0]['visual_intent'],'a purposeful comparison')   # what the picture must do
        self.assertTrue(ok['direction']['visual_language'])                                         # in the locked look
        # The thumbnail needs the locked direction, not a shot; an unknown purpose is refused.
        thumb={'run':str(self.run),'video':1,'purpose':'thumbnail',
               'images':[{'prompt':'a bold close portrait of a surveyor at dawn with a broken bridge behind, painterly, soft edges',
                          'out':str(stills/'thumb.png')}]}
        save(jobp,thumb); self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])
        thumb['purpose']='poster'; save(jobp,thumb)
        self.assertIn('job_purpose_must_be:shots/treatment_preview/thumbnail',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        # A deliberate callback shows an earlier shot's still again: nothing to generate for it.
        shots[4]['reuses']='S1'; shots[4].pop('frame_prompt')
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        save(jobp,{**job,'images':[{'shot_id':'S5','prompt':shots[0]['frame_prompt'],'out':str(stills/'S5.png')}]})
        self.assertIn('item_1_shot_S5_is_a_callback_of_S1_nothing_to_generate',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        save(jobp,job)
        self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])
        # A prompt that drifted from the approved shot, or a shot the plan doesn't have, is refused.
        drift=json.loads(json.dumps(job)); drift['images'][0]['prompt']='a rocket launch at noon, cinematic'
        save(jobp,drift)
        self.assertIn('item_1_prompt_does_not_carry_shot_S1_frame_prompt',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        drift['images'][0]['shot_id']='S99'; save(jobp,drift)
        self.assertIn('item_1_must_name_a_shot_of_the_shot_plan',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        # The workers refuse before anything loads (no run named: no ComfyUI, no model, no network).
        loose={'op':'generate','images':[{'prompt':'a carefully specified picture of the valley','out':str(stills/'x.png'),
                                          'file':'x.png'}],'tracks':[{'video':1,'caption':'a low warm drone','duration':10,'out':str(stills/'x.wav')}]}
        lp=self.home/'loose.json'; save(lp,loose)
        for worker,extra in (('image_worker.py',[]),('music_worker.py',[]),('openai_images_worker.py',['--execute'])):
            cmd=[sys.executable,str(ROOT/'scripts'/worker)]+(['--job',str(lp)] if worker.startswith('openai') else [str(lp)])+extra
            p=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,'OPENAI_API_KEY':''})
            self.assertEqual(p.returncode,2,worker+p.stdout+p.stderr)
            self.assertIn('job_must_name_its_run_and_video',p.stdout,worker)
        # Music names the beats it scores.
        music={'op':'generate','run':str(self.run),'video':1,
               'tracks':[{'video':1,'beats':['B02','B03'],'caption':'a low warm drone that thins out','duration':30,'out':str(self.home/'bed.wav'),
                          'serves':'the drone holds the waiting of B02 and thins as B03 opens up'}]}
        mp=self.home/'music-job.json'; save(mp,music)
        self.assertTrue(cli('media-check','--job',mp,'--kind','music')['ok'])
        music['tracks'][0]['beats']=['B99']; save(mp,music)
        self.assertIn('track_1_must_name_beats_of_the_beat_map',cli('media-check','--job',mp,'--kind','music',expected=2)['issues'])
        # What was made is recorded with its shot and the direction it was made under.
        gate=core.media_gate(job,'stills')
        stills.mkdir(); (stills/'S1.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*2048)
        core.record_media(gate['run'],1,'stills',[{'out':str(stills/'S1.png'),**gate['records'][0]}])
        self.assertEqual(core.stills_facts(self.run,1)['issues'],['stills_missing_or_untraced:S2,S3,S4'])   # S5 shows S1's
        # A meaningful change of the chosen treatment: its earlier picture and the shot plan no longer stand...
        d=json.loads((vd/'direction.json').read_text())
        d['treatments'][0]['visual_language']+=' Colder, sparser frames throughout.'
        save(vd/'direction.json',d)
        cli('direction-lock','--run',self.run,'--video',1,'--revise','a colder, sparser look')
        self.assertTrue(any(x.startswith('stills_made_for_an_earlier_direction:S1') for x in core.stills_facts(self.run,1)['issues']))
        save(jobp,job)
        self.assertIn('shot_plan_made_for_an_earlier_direction',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        # ...until the shot plan follows the new look for real, and the job carries its new prompt.
        shots[0]['frame_prompt']='a sparse cold picture 1 of the valley, dawn light, one clear subject'
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        self.assertNotIn('beat_map_made_for_an_earlier_direction',      # the look changed; the beats did not need to
                         cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        self.assertIn('item_1_prompt_does_not_carry_shot_S1_frame_prompt',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', painterly'; save(jobp,job)
        # the look changed: the style lock follows it, with its reason, as a new revision (never silently)
        self.assertIn('style_lock_outdated:the_chosen_treatments_visual_language_changed:relock_with_--why',
                      cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        cli('style-lock','--run',self.run,'--video',1,'--style-prompt','painterly','--departs-when','photorealistic, flat vector',
            '--why','the colder sparser look keeps only the painterly finish')
        self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])
        # Explicit reapproval accepts pictures as they are (user-supplied, say), on record.
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','stills','--reason','the user supplies painted stills for every shot')
        sf=core.stills_facts(self.run,1)
        self.assertEqual(sf['issues'],[])
        self.assertTrue(any('explicit reapproval' in w for w in sf['warnings']))
        # A later change that doesn't touch the pictures leaves that reapproval standing.
        d=json.loads((vd/'direction.json').read_text())
        d['treatments'][0]['narrator']+=' A touch drier.'
        save(vd/'direction.json',d)
        self.assertNotIn('stills',cli('direction-lock','--run',self.run,'--video',1,'--revise','a drier narrator')['affects'])
        self.assertEqual(core.stills_facts(self.run,1)['issues'],[])
        self.assertEqual(cli('direction-lock','--run',self.run,'--video',1)['unchanged'],True)   # nothing new: nothing to do
        # A still is never changed after the generator made it, and never carries a blur or an erase: no reapproval
        # accepts either (the user, 2026-11-23: never blur; manual 04). S5 shows S1's still.
        s1=stills/'S1.png'; raw=s1.read_bytes()
        s1.write_bytes(raw+b'blurred')
        self.assertIn('stills_changed_after_the_generator_made_them:S1,S5',core.stills_facts(self.run,1)['issues'])
        s1.write_bytes(raw)
        self.assertEqual(core.stills_facts(self.run,1)['issues'],[])
        log=self.run/'60-visuals/video-01/stills-postprocess.json'
        save(log,{'edits':[{'shot_id':'S1','regions':[{'mode':'soften','sigma':3,'poly':[[0,0],[9,0],[9,9]]}]}]})
        self.assertIn('stills_carry_a_blur_or_erase_touchup:S1,S5',core.stills_facts(self.run,1)['issues'])
        save(log,{'edits':[{'shot_id':'S1','superseded_at':'2026-11-23T00:00:00+00:00',
                            'regions':[{'mode':'soften','sigma':3,'poly':[[0,0],[9,0],[9,9]]}]}]})
        self.assertEqual(core.stills_facts(self.run,1)['issues'],[])        # made again: the old touch-up is history
        soft={'shot_id':'S1','regions':[{'mode':'soften','sigma':3,'poly':[[0,0],[9,0],[9,9]]}]}
        save(log,{'edits':[dict(soft,at='2000-01-01T00:00:00+00:00')]})     # before the still was generated again
        self.assertEqual(core.stills_facts(self.run,1)['issues'],[])
        save(log,{'edits':[dict(soft,at='2999-01-01T00:00:00+00:00')]})     # after it: still in the picture
        self.assertIn('stills_carry_a_blur_or_erase_touchup:S1,S5',core.stills_facts(self.run,1)['issues'])
        save(log,{'edits':[]})

    def test_a_reader_who_knew_why_only_from_outside_makes_a_major_finding(self):
        vd=self.write_plan(review_script=False)
        dev={'lines':'L010-L020','what_happened':'the plan is dropped at the last minute',
             'why_it_matters':'it was the only way to save the season','why_from':'my own knowledge',
             'would_be_different':'the season would have been lost','learned_when':'never',
             'event':'clear','significance':'clear','reward':'landed'}
        packet,rec=self.review('script',[],developments=[dev])
        sealed=json.loads(Path(rec['record']).read_text(encoding='utf-8'))
        # S1 for the reason known only from outside; K1 because the ending is a key moment this reader never named
        self.assertEqual(sealed['derived_findings'],['S1','K1'])
        self.assertEqual((sealed['findings'][0]['severity'],sealed['findings'][0]['lines']),('major','L010-L020'))
        self.assertEqual(rec['major'],['S1'])
        self.assertIn('S1',json.loads(Path(rec['answers_file']).read_text(encoding='utf-8'))['answers'])
        self.assertEqual(sealed['developments'][0]['why_from'],'my own knowledge')      # the reader's words kept

    def test_topic_discovery_gates_the_direction_and_the_blueprint(self):
        vd=self.write_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # a value only an ending can give is not forced on every format: reward_shape says how value builds up
        blue=json.loads((vd/'blueprint.json').read_text()); blue.pop('ending_payoff'); save(vd/'blueprint.json',blue)
        self.assertIn('blueprint_missing_ending_payoff_or_reward_shape',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        blue['reward_shape']='each step leaves the viewer able to do one more thing, in order'; save(vd/'blueprint.json',blue)
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # the lock refuses a chosen subject resting on sources the ledger does not hold
        d=json.loads((vd/'direction.json').read_text())
        d['subject']['candidates'][0]['strongest_material'][0]['sources']=['S9']
        save(vd/'direction.json',d)
        res=cli('direction-lock','--run',self.run,'--video',1,'--revise','a sensational source',expected=2)
        self.assertIn('cites_sources_not_in_the_ledger:S9',json.dumps(res))

    def test_a_changed_value_reaches_only_the_beats_that_carry_it(self):
        vd=self.write_plan()
        self.shots_for_plan()
        d=json.loads((vd/'direction.json').read_text())
        # another candidate's research refined: nothing in production follows
        d['subject']['candidates'][1]['feasibility']='period maps and one drawn reconstruction can show the error, for this audience and this length.'
        save(vd/'direction.json',d)
        res=cli('direction-lock','--run',self.run,'--video',1,'--revise','refined the alternative')
        self.assertEqual((res['affects'],res['production_rev']),([],1))
        # a researched value said more exactly: only B05 (which carries R1), its lines and its shot
        d['subject']['value_to_carry'][0]['what']='the supply decision, not the battle plan, decided the campaign'
        save(vd/'direction.json',d)
        res=cli('direction-lock','--run',self.run,'--video',1,'--revise','R1 said more exactly')
        self.assertEqual((res['affects'],res['production_rev']),(['beat-map','script','shot-plan'],2))
        lock=json.loads((vd/'direction-lock.json').read_text())
        self.assertEqual(sorted(lock['required']['beat-map']['parts']),['B05'])
        self.assertEqual(sorted(lock['required']['script']['parts']),[f'L{i:03}' for i in range(41,53)])
        self.assertEqual(sorted(lock['required']['shot-plan']['parts']),['S5'])
        pc=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('beat_map_made_for_an_earlier_direction:B05',pc['issues'])
        self.assertTrue(any(x.startswith('script_made_for_an_earlier_direction:L041') for x in pc['issues']))
        # B05 revisited, the other beats untouched: the beat map has followed
        bm=json.loads((vd/'beat-map.json').read_text())
        bm['beats'][4]['significance']['matters_because']='the conclusion shows that the quiet order, not the plan, decided it'
        save(vd/'beat-map.json',bm)
        pc=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertFalse([x for x in pc['issues'] if x.startswith('beat_map_made_for')])
        # its lines and its shot looked at and kept as they are: reapproved, on record
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','script','--reason','the B05 lines already say the decision decided it')
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','shot-plan','--reason','the closing map still shows the depots')
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # a new angle on the same subject is another story: the plan files, whole
        d['subject']['candidates'][0]['what_happens']='the film follows the clerk, not the general, through the two weeks before the march, for this audience and this length.'
        save(vd/'direction.json',d)
        res=cli('direction-lock','--run',self.run,'--video',1,'--revise','told from the clerk')
        self.assertEqual(res['affects'],['beat-map','script','shot-plan'])
        lock=json.loads((vd/'direction-lock.json').read_text())
        self.assertIn('baseline',lock['required']['beat-map'])
        self.assertNotIn('stills',lock['required'])

    def test_a_corrected_source_is_rechecked_not_rebuilt(self):
        vd=self.write_plan()
        src=self.run/'30-research/video-01/sources.md'
        src.write_text(src.read_text(encoding='utf-8').replace('A primary record of the order',
                                                               'A primary record of the order (catalogue number corrected)'),encoding='utf-8')
        pc=cli('plan-check','--run',self.run,'--video',1)
        note=[w for w in pc['warnings'] if w.startswith('research changed since the direction was locked')]
        self.assertTrue(note and 'C01' in note[0] and 'L041' in note[0] and 'R1' in note[0],note)
        self.assertEqual(pc['creative']['production_rev'],1)                  # nothing rebuilt for a correction
        res=cli('direction-lock','--run',self.run,'--video',1,'--research-rechecked','S1 catalogue number fixed; C01 and L041 still say the same')
        self.assertEqual(res['research_rechecked']['claims_to_recheck'],['C01'])
        pc=cli('plan-check','--run',self.run,'--video',1)
        self.assertFalse([w for w in pc['warnings'] if w.startswith('research changed')])
        # a claim found weaker after the lock: the value resting on it can no longer be said as established
        cp=self.run/'30-research/video-01/claims.json'
        cl=json.loads(cp.read_text()); cl['claims'][0]['confidence']='disputed'; save(cp,cl)
        pc=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any('said_as_established_but_claim_C01_is_disputed' in x for x in pc['issues']))

    def test_a_changed_beat_names_only_its_own_shots(self):
        vd=self.write_plan()
        self.shots_for_plan()
        self.assertTrue(cli('shot-check','--run',self.run,'--video',1)['ready'])
        bm=json.loads((vd/'beat-map.json').read_text())
        bm['beats'][2]['visual_intent']='the same valley, seen from the other army'
        save(vd/'beat-map.json',bm)
        sf=cli('shot-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('beat_B03_changed_since_its_shots_were_checked:S3:update_them_or_shot-check_--keep_why_they_still_fit',sf['issues'])
        # the other shots' stills can still be made; S3's waits for its beat
        job={'op':'generate','run':str(self.run),'video':1,
             'images':[{'shot_id':'S1','prompt':'a distinct picture 1 of the valley, dawn light, one clear subject, painterly, soft edges',
                        'out':str(self.home/'S1.png')}]}
        jobp=self.home/'job.json'; save(jobp,job)
        self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])
        job['images'][0].update(shot_id='S3',prompt='a distinct picture 3 of the valley, dusk light, one clear subject, '
                                                   'painterly, soft edges')
        save(jobp,job)
        self.assertIn('item_1_shot_S3_waits:its_beat_B03_changed_since_the_shot_plan_was_checked',
                      cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        res=cli('shot-check','--run',self.run,'--video',1,'--keep','the dusk valley reads the same from either side')
        self.assertTrue(res['ready'])
        self.assertTrue(cli('shot-check','--run',self.run,'--video',1)['ready'])
        self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])

    def test_an_exact_topic_asks_the_treatment_reader_whether_it_is_still_the_request(self):
        vd=self.write_plan(lock=False)
        d=self.direction_doc()
        d['subject']['scope'].update(kind='topic',user_words='the supply order before the battle',
                                     understood_as='a video about the order that moved the depots and what it decided',
                                     boundary='a video about the battle itself or about another order would be another topic')
        save(vd/'direction.json',d)
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind','treatment')
        text=Path(packet['packet']).read_text(encoding='utf-8')
        self.assertIn('What was asked for',text); self.assertIn('the supply order before the battle',text)
        save(Path(packet['findings_file']),{'reviewer':'test reader','findings':[]})
        res=cli('review-record','--run',self.run,'--video',1,'--kind','treatment',expected=2)   # the question unanswered
        self.assertIn('on_request: treatment A needs',json.dumps(res))
        doc={'reviewer':'test reader','findings':[],'on_request':{'A':'yes: it follows the order','B':'no: it is about the battle'}}
        save(Path(packet['findings_file']),doc)
        rec=cli('review-record','--run',self.run,'--video',1,'--kind','treatment')
        self.assertEqual(rec['major'],['Q1'])
        sealed=json.loads(Path(rec['record']).read_text(encoding='utf-8'))
        self.assertEqual(sealed['derived_findings'],['Q1'])
        self.assertEqual(sealed['findings'][0]['treatment'],'B')
        # the finding is answered before the treatments can be read again or locked
        self.assertIn('Q1',json.dumps(cli('review-packet','--run',self.run,'--video',1,'--kind','treatment',expected=2)))

    def test_an_interrupted_research_resumes_from_its_files(self):
        cli('length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
            '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145,'--pace-why','the test narrator reads at this pace')
        vd=self.run/'40-plans/video-01'
        save(vd/'blueprint.json',{'audience_promise':'Understood decision','title':'A test title'})
        self.measure_refs()
        d=self.direction_doc()
        sel,vals=d['subject'].pop('selection'),d['subject'].pop('value_to_carry')   # stopped mid-research
        save(vd/'direction.json',d)
        self.review('treatment',[],{})
        res=json.dumps(cli('direction-lock','--run',self.run,'--video',1,expected=2))
        self.assertIn('subject_selection_must_name_a_listed_candidate',res)
        self.assertIn('subject_needs_value_to_carry_with_distinct_ids',res)
        d['subject'].update(selection=sel,value_to_carry=vals)                        # resumed: the files hold everything
        save(vd/'direction.json',d)
        self.assertTrue(cli('direction-lock','--run',self.run,'--video',1)['ok'])

    def test_the_research_reaches_the_pictures_and_the_music(self):
        vd=self.write_plan()
        shots=self.shots_for_plan()
        jobp=self.home/'job.json'
        save(jobp,{'op':'generate','run':str(self.run),'video':1,
                   'images':[{'shot_id':'S5','prompt':shots[4]['frame_prompt']+', painterly, soft edges','out':str(self.home/'S5.png')}]})
        item=cli('media-check','--job',jobp,'--kind','stills')['direction']['items'][0]
        self.assertEqual(item['carries_values'][0]['id'],'R1')
        self.assertEqual(item['carries_values'][0]['certainty'],'established')
        self.assertTrue(item['matters_because'] and item['carries_significance'])
        save(jobp,{'run':str(self.run),'video':1,'tracks':[{'beats':['B05'],'caption':'a low pulse under the conclusion',
                                                             'serves':'a low pulse that lets the conclusion land without pushing it'}]})
        beat=cli('media-check','--job',jobp,'--kind','music')['direction']['items'][0]['beats']['B05']
        self.assertEqual(beat['key_moment'],'the earned conclusion')
        self.assertTrue(beat['matters_because'])

    def look_at_pictures(self, files, result='clean', expected=0, **extra):
        lp=self.home/'looks.json'
        save(lp,{'looks':[{'file':str(f),'result':result,'note':'a ridge road in snow at dawn, nobody hurt',**extra} for f in files]})
        return cli('content-review','--run',self.run,'--video',1,'--pictures','--file',lp,expected=expected)

    def test_edit_follows_the_retimed_shots_and_beats(self):
        vd,d,_=self.narrated()
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(d/'part-001.mp3'),str(d/'narration.wav')],check=True)
        shots=[{'id':'S1','beat_id':'B01','line_start':'L001','line_end':'L005','composition':'wide',
                'new_thing':'the road the narrator is talking about, from above','frame_prompt':'a long road through snow seen from a ridge at dawn'},
               {'id':'S2','beat_id':'B02','line_start':'L006','line_end':'L010','composition':'close',
                'new_thing':'the hands that will have to fix the bridge','frame_prompt':'cold hands holding a coil of rope beside a broken bridge'}]
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        self.assertEqual((plan['direction']['treatment'],plan['direction']['production_rev']),('T1',1))   # made under the locked direction
        self.assertTrue(plan['direction']['visual_language'] and plan['direction']['sound'])     # the editor gets the treatment's look and sound
        self.assertEqual(plan['shots'][1]['direction']['pace'],'slow')                           # each shot carries its beat's direction
        self.assertEqual([b['id'] for b in plan['beats']],['B01','B02'])
        # The stills are made through the gate and recorded with their shots.
        core=self.load_core()
        stills=self.home/'stills'; stills.mkdir()
        sl=self.run/'60-visuals/video-01/style-lock.json'
        if not sl.is_file():
            cli('style-lock','--run',self.run,'--video',1,'--style-prompt','ink wash','--departs-when','photorealistic, flat vector')
        style=json.loads(sl.read_text(encoding='utf-8'))['style_prompt']
        job={'run':str(self.run),'video':1,'images':[{'shot_id':s['id'],'prompt':s['frame_prompt']+', '+style,
                                                      'out':str(stills/f"{s['id']}.png")} for s in shots]}
        gate=core.media_gate(job,'stills'); self.assertTrue(gate['ok'],gate['issues'])
        for it in job['images']:
            Path(it['out']).write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*2048)
        core.record_media(gate['run'],1,'stills',[{'out':it['out'],**rec} for it,rec in zip(job['images'],gate['records'])])
        # timeline.json as read back from CapCut: each clip's own picture file (CapCut writes C:/ paths).
        tdir=self.run/'70-edit/video-01'
        seg=[{'start_s':s['start_s'],'end_s':s['end_s'],'beat_id':s['beat_id'],'shot_id':s['id'],'purpose':'the shot\'s job',
              'asset_path':str(stills/f"{s['id']}.png").replace('\\','/')} for s in plan['shots']]
        timeline={'canvas':'1920x1080','visual_segments':seg,
                  'audio_tracks':[{'kind':'narration','file':str(d/'narration.wav'),'start_s':0,'end_s':plan['edit_duration_s']},
                                  {'kind':'music','file':str(self.home/'bed.wav'),'start_s':0,'end_s':5,'beats':['B01']}]}
        save(tdir/'timeline.json',timeline)
        def trace():
            res=cli('timeline-check','--run',self.run,'--video',1,expected=2)
            return res,[x for x in res['issues'] if x.startswith(('visual_','shot_','edit_plan','audio_track','stills_'))]
        res,found=trace()
        self.assertEqual(found,['audio_track_2_music_without_provenance'])   # every cut traced; the bed is not
        # Every picture CapCut shows is looked at whole before the edit passes; a look holds for that exact file.
        self.assertIn('pictures_not_content_checked:2:S1.png,S2.png',res['issues'])
        bad=self.look_at_pictures([stills/'S1.png'],result='issue',expected=2)            # an issue names its category
        self.assertTrue(any('needs_its_category' in x for x in bad['details']))
        self.look_at_pictures([stills/'S1.png',stills/'S2.png'])
        self.assertFalse([x for x in trace()[0]['issues'] if x.startswith('pictures_')])
        self.look_at_pictures([stills/'S2.png'],result='issue',category='graphic_injury')
        self.assertIn('pictures_with_a_content_issue:1:S2.png',trace()[0]['issues'])
        (stills/'S2.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'1'*2048)                  # remade through the gate: looked at again
        core.record_media(gate['run'],1,'stills',[{'out':str(stills/'S2.png'),**gate['records'][1]}])
        self.assertIn('pictures_not_content_checked:1:S2.png',trace()[0]['issues'])
        self.look_at_pictures([stills/'S2.png'])
        # The bed made through the gate for the beat it scores; the gate hands the agent that beat's sound direction.
        mjob={'op':'generate','run':str(self.run),'video':1,'tracks':[{'video':1,'beats':['B01'],'duration':5,
                                                                      'serves':'a quiet bed under the opening that never leads it',
              'caption':'a low warm drone that thins out','out':str(self.home/'bed.wav')}]}
        mg=core.media_gate(mjob,'music'); self.assertTrue(mg['ok'],mg['issues'])
        self.assertEqual(mg['direction']['items'][0]['beats']['B01']['sound_direction'],'bed')
        core.record_media(mg['run'],1,'music',[{'out':mjob['tracks'][0]['out'],**mg['records'][0]}])
        res,found=trace()
        self.assertEqual(found,[])
        # Pictures swapped in CapCut, a clip relabelled to another beat, a bed moved outside its beats.
        a,b=timeline['visual_segments'][0]['asset_path'],timeline['visual_segments'][1]['asset_path']
        timeline['visual_segments'][0]['asset_path'],timeline['visual_segments'][1]['asset_path']=b,a
        timeline['visual_segments'][1]['beat_id']='B01'
        timeline['audio_tracks'][1].update({'beats':['B02'],'start_s':0,'end_s':1})
        save(tdir/'timeline.json',timeline)
        res,found=trace()
        for issue in ('visual_1_shows_the_still_of_shot_S2','visual_2_beat_differs_from_its_shot',
                      'audio_track_2_plays_outside_its_beats'):
            self.assertIn(issue,res['issues'])
        # The cut put back as it was.
        timeline['visual_segments'][0]['asset_path'],timeline['visual_segments'][1]['asset_path']=a,b
        timeline['visual_segments'][1]['beat_id']='B02'
        timeline['audio_tracks'][1].update({'beats':['B01'],'start_s':0,'end_s':5})
        save(tdir/'timeline.json',timeline)
        self.assertEqual(trace()[1],[])
        # The look changes: the stills and the edit plan no longer stand; the bed does (the sound didn't change).
        dd=json.loads((vd/'direction.json').read_text())
        dd['treatments'][0]['visual_language']+=' Colder light throughout.'
        save(vd/'direction.json',dd)
        cli('direction-lock','--run',self.run,'--video',1,'--revise','colder light')
        res,found=trace()
        self.assertIn('edit_plan_made_for_an_earlier_direction',found)
        self.assertTrue(any(x.startswith('stills_made_for_an_earlier_direction') for x in found))
        self.assertFalse([x for x in found if 'music' in x])
        # The shot plan changed its structure after the retime: the edit plan no longer describes it.
        shots[1]['line_start']='L007'; shots[0]['line_end']='L006'
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        self.assertIn('edit_plan_outdated_rerun_retime_shots',cli('timeline-check','--run',self.run,'--video',1,expected=2)['issues'])

    def test_recorded_narration_follows_the_narrator(self):
        vd=self.write_plan()
        core=self.load_core()
        script=json.loads((vd/'script.json').read_text())
        lang=json.loads((vd/'length-lock.json').read_text())['language']
        chunks=core.chunks_for_lines(script['lines'],min(core.model_limit('eleven_v4'),8000))
        d=self.run/'50-audio/video-01'
        save(d/'manifest.json',{'model_id':'eleven_v4','voice_id':'TESTID','language':lang,'status':'partial',
                                'finished_parts':[1],'part_revs':{'1':1},
                                'chunks':[{'id':i+1,'line_start':c['line_start'],'line_end':c['line_end'],'file':f'part-{i+1:03d}.mp3',
                                           'text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),'characters':len(c['text'])}
                                          for i,c in enumerate(chunks)]})
        (d/'part-001.mp3').write_bytes(b'0'*2048)          # part 1 recorded under revision 1 (dry runs only: no network)
        tts=['tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4']
        dry=cli(*tts)
        self.assertEqual(dry['parts_made_for_an_earlier_direction'],[])
        self.assertNotIn(1,dry['parts_to_record'])
        # The narrator changes in the chosen treatment: the recorded part no longer stands on its own.
        dd=json.loads((vd/'direction.json').read_text())
        dd['treatments'][0]['narrator']+=' Warmer, and a little amused.'
        save(vd/'direction.json',dd)
        r=cli('direction-lock','--run',self.run,'--video',1,'--revise','the narrator warmed up')
        self.assertEqual(r['affects'],['beat-map','script','voice','narration'])
        self.assertEqual(r['outdated_now'],['beat-map','script','narration'])   # no voice chosen yet in this fixture
        for a in ('beat-map','script'):
            cli('direction-reapprove','--run',self.run,'--video',1,'--artifact',a,'--reason','the words already carry the warmer narrator')
        dry=cli(*tts)
        self.assertEqual(dry['parts_made_for_an_earlier_direction'],[1])     # re-recorded with --rerecord-changed...
        self.assertIn(1,dry['parts_to_record'])
        self.assertIn('narration_parts_made_for_an_earlier_direction:1',cli('audio-check','--run',self.run,'--video',1,expected=2)['issues'])
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','narration',
            '--reason','the recorded voice already sounds warm enough here')   # ...or kept, on record
        dry=cli(*tts)
        self.assertEqual(dry['parts_made_for_an_earlier_direction'],[])
        self.assertNotIn(1,dry['parts_to_record'])
        self.assertFalse([x for x in cli('audio-check','--run',self.run,'--video',1,expected=2)['issues'] if 'earlier_direction' in x])

    def test_voice_candidates_measure_each_preview_without_listening(self):
        core=self.load_core()
        self.write_plan(lock=False)
        preview=self.home/'preview.mp3'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=140:sample_rate=16000',
                        '-t','3','-c:a','libmp3lame','-b:a','32k',str(preview)],check=True)

        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def fake_transcribe(path, outpath, *a):
            words=[{'start_s':round(0.1+0.33*i,2),'end_s':round(0.38+0.33*i,2),'text':f' w{i}'} for i in range(8)]
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[{'start_s':0.1,'end_s':2.8,'text':'w','words':words}]})
            Path(outpath).with_suffix('.txt').write_text('[0.1-2.8] w0 w1 w2 w3 w4 w5 w6 w7',encoding='utf-8')
            return 1
        args=argparse.Namespace(run=str(self.run),video=1,count=1,search='',design=0,design_description='',design_text='',
                                whisper_model='medium',device='cpu',compute_type='int8')
        voices={'voices':[{'voice_id':'voice123456789','name':'Test','labels':{'accent':'american'},
                           'preview_url':'https://example.invalid/preview.mp3'}]}
        with mock.patch.dict(os.environ,{'ELEVEN_API_KEY':'test-not-a-real-key','ELEVENLABS_API_KEY':''}), \
                mock.patch.object(core,'elevenlabs_request',return_value=voices), \
                mock.patch.object(core.urllib.request,'urlopen',side_effect=lambda *a,**k: Reply(preview.read_bytes())), \
                mock.patch.object(core,'transcribe',side_effect=fake_transcribe), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as printed:
            core.cmd_voice_candidates(args)
        res=json.loads(printed.getvalue())
        measured=res['candidates'][0]['measured_delivery']
        self.assertNotIn('error',measured)
        self.assertIn('pitch_range_st',measured)
        self.assertIn('cannot hear',res['guidance'])

    # ---------------------------------------------------------------- narration: voice lock, parts, cost, checks
    def fake_mp3(self, seconds=2):
        f=self.home/f'fake-{seconds}s.mp3'
        if not f.exists():
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=180:sample_rate=22050',
                            '-t',str(seconds),'-c:a','libmp3lame','-b:a','64k',str(f)],check=True)
        return f

    def core_call(self, core, *argv, fake=None):
        """One static_core command run in this process as the CLI runs it: ElevenLabs faked, any real request refused."""
        def no_network(*a, **k):
            raise AssertionError('a network request was made: ' + str(getattr(a[0], 'full_url', a[0]) if a else ''))
        code=0
        with mock.patch.dict(os.environ,{'ELEVENLABS_API_KEY':'test-not-a-real-key','ELEVEN_API_KEY':''}), \
                mock.patch.object(sys,'argv',['static_core.py',*map(str,argv)]), \
                mock.patch.object(core.urllib.request,'urlopen',side_effect=fake or no_network), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as out:
            try:
                core.main()
            except SystemExit as e:
                code=e.code if isinstance(e.code,int) else 0
            text=out.getvalue()
        return code,(json.loads(text) if text.strip() else {})

    def tagged_plan(self):
        """write_plan's ready plan with two delivery tags, a name on the pronunciation list and each tag's reason under
        "Delivery and tags", all written before the cold read, as a writer would."""
        vd=self.write_plan(review_script=False)
        script=json.loads((vd/'script.json').read_text())
        script['lines'][0]['text']='[curious] Somewhere near Hagaru the road narrows, '+script['lines'][0]['text']
        script['lines'][0]['cue_scope']='this first line only; the next line is plain again'
        script['lines'][12]['text']+=' [pause]'
        script['lines'][12].update({'pause_after_s':2,'pause_via':'tag','pause_purpose':'the cost of the choice lands first',
                                    'pause_picture':'the map stays on the crossing they chose',
                                    'pause_sound':'the low pulse goes on under it'})
        save(vd/'script.json',script)
        save(vd/'pronunciation.json',{'terms':[{'term':'Hagaru','say':'/həˈɡɑːruː/','how':'ipa','confidence':'likely',
                                                'source':'the standard Korean romanisation of the town name'}]})
        (vd/'editorial-review.md').write_text('## Self-audit\nNotes.\n\n## Delivery and tags\n- L001 [curious]: the narrator '
                                             'leans in on the first odd detail.\n- L013 [pause]: the cost lands.\n',encoding='utf-8')
        self.review_script()
        return vd

    def test_voice_lock_drives_every_recording(self):
        core=self.load_core()
        vd=self.tagged_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        pick=['voice-pick','--run',self.run,'--video',1,'--voice-id','VOICEA']
        reason='a warm curious friend at a table telling it plainly'
        self.assertIn('--reason',cli(*pick,'--settings','{"stability":0.6,"similarity_boost":0.8}',expected=2)['error'])
        cli(*pick,'--settings','{"stability":0.6}','--reason',reason,expected=2)                       # both settings chosen
        cli(*pick,'--settings','{"stability":0.6,"similarity_boost":0.8,"speed":1.1}','--reason',reason,expected=2)  # v4: no speed
        got=cli(*pick,'--settings','{"stability":0.6,"similarity_boost":0.8}','--reason',reason)
        vl=json.loads((self.run/'60-voice/video-01/voice-lock.json').read_text())
        self.assertEqual((vl['voice_id'],vl['treatment'],vl['production_rev'],vl['voice_rev']),('VOICEA','T1',1,1))
        self.assertEqual(got['settings'],{'stability':0.6,'similarity_boost':0.8})
        # The command line can't override the lock: another voice or other settings are refused, even in a dry run.
        tts=['tts','--run',self.run,'--video',1]
        self.assertIn('voice_id_differs_from_the_episode_voice_lock',cli(*tts,'--voice-id','OTHER',expected=2)['details']['conflicts'])
        cli(*tts,'--settings','{"stability":1.0,"similarity_boost":0.8}',expected=2)
        self.assertNotEqual(subprocess.run([sys.executable,str(TOOL),*map(str,tts),'--delivery','[excited]'],
                                           capture_output=True,text=True).returncode,0)          # --delivery no longer exists
        dry=cli(*tts)
        self.assertEqual((dry['voice']['voice_id'],dry['voice']['settings'],dry['execute_blockers']),
                         ('VOICEA',{'stability':0.6,'similarity_boost':0.8},[]))
        self.assertEqual([p['beats'] for p in dry['parts_view']][0][0]['id'],'B01')             # parts follow the beats
        # Recording, ElevenLabs faked: what goes out is the lock, the tags verbatim, the name in v4's IPA form.
        sent=[]; state={'used':0,'fail':None}
        mp3=self.fake_mp3().read_bytes()
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        def fake(req,timeout=None):
            url=req.full_url
            if url.endswith('/v1/user/subscription'):
                return Reply(json.dumps({'character_limit':100000,'character_count':state['used']}).encode())
            if url.endswith('/v1/models'):
                return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':1.0},
                                          'maximum_text_length_per_request':10000}]).encode())
            body=json.loads(req.data.decode())
            sent.append(body)
            if state['fail']==len(sent):
                raise core.urllib.error.HTTPError(url,422,'unprocessable',{},io.BytesIO(b'{}'))
            state['used']+=len(body['text'])
            return Reply(mp3)
        code,out=self.core_call(core,*tts,'--max-parts',1,'--execute',fake=fake)
        self.assertEqual(code,0,out)
        b=sent[0]
        self.assertEqual((b['model_id'],b['voice_settings']),('eleven_v4',{'stability':0.6,'similarity_boost':0.8}))
        self.assertTrue(b['text'].startswith('[curious] Somewhere near "/həˈɡɑːruː/" the road narrows'))
        self.assertIn('Hagaru',(vd/'script.json').read_text(encoding='utf-8'))             # the script keeps the spelling
        self.assertNotIn('previous_text',b); self.assertNotIn('[',b['next_text'])          # context: spoken words only
        man=json.loads((self.run/'50-audio/video-01/manifest.json').read_text())
        rec=man['part_records']['1']
        self.assertEqual((rec['voice_id'],rec['settings'],rec['treatment'],rec['production_rev']),
                         ('VOICEA',{'stability':0.6,'similarity_boost':0.8},'T1',1))
        self.assertEqual(rec['credits_billed'],len(b['text']))                              # measured, from the balance
        ledger=[json.loads(x) for x in (self.run/'logs/elevenlabs-ledger.jsonl').read_text().splitlines()]
        self.assertEqual(ledger[0]['phase'],'pending')                 # on record before it was sent
        ledger=[x for x in ledger if x['phase']=='done']
        self.assertEqual((ledger[0]['kind'],ledger[0]['delta']),('tts',len(b['text'])))
        # A refused request (4xx: answered before any work, never billed) blocks; the same command resumes and never
        # asks for a finished part again.
        state['fail']=2
        skip=['--skip-calibration','--reason','testing the resume path after a refused request']
        code,out=self.core_call(core,*tts,*skip,'--execute',fake=fake)
        self.assertEqual(code,2); self.assertIn('BLOCKED',out['error']); self.assertEqual(out['details']['outcome'],'failed')
        state['fail']=None
        before=len(sent)
        code,out=self.core_call(core,*tts,*skip,'--execute',fake=fake)
        parts=len(json.loads((self.run/'50-audio/video-01/manifest.json').read_text())['chunks'])
        self.assertEqual(len(sent)-before,parts-1)                                       # part 1 never again
        self.assertEqual(sent[1]['previous_text'].split('\n')[-1],
                         json.loads((vd/'script.json').read_text())['lines'][man['chunks'][0]['line_end']-1]['text'])
        # Changing the narrator's settings is a revision: the parts made with the old ones are re-recorded, never mixed.
        cli(*pick,'--settings','{"stability":0.9,"similarity_boost":0.8}','--reason',reason,expected=2)   # needs --replace
        cli(*pick,'--settings','{"stability":0.9,"similarity_boost":0.8}','--reason','steadier for the long middle stretch','--replace')
        dry=cli(*tts)
        self.assertEqual(dry['parts_recorded_with_another_voice_setup'],list(range(1,parts+1)))
        code,out=self.core_call(core,*tts,'--execute',fake=fake)
        self.assertEqual(code,2); self.assertIn('--rerecord-changed',out['error'])
        self.assertTrue(any(x.startswith('narration_parts_recorded_with_another_voice_setup')
                            for x in cli('audio-check','--run',self.run,'--video',1,expected=2)['issues']))
        # A narrator change in the direction asks again whether the chosen voice fits.
        dd=json.loads((vd/'direction.json').read_text()); dd['treatments'][0]['narrator']+=' Quieter now.'
        save(vd/'direction.json',dd)
        self.assertIn('voice',cli('direction-lock','--run',self.run,'--video',1,'--revise','a quieter narrator')['outdated_now'])
        for a in ('beat-map','script'):
            cli('direction-reapprove','--run',self.run,'--video',1,'--artifact',a,'--reason','the words already fit the quieter narrator')
        self.assertIn('voice_made_for_an_earlier_direction',cli(*tts)['execute_blockers'])
        cli('direction-reapprove','--run',self.run,'--video',1,'--artifact','voice','--reason','this voice already speaks quietly enough')
        self.assertEqual(cli(*tts)['execute_blockers'],[])

    # ---------------------------------------------------------------- remediation 2026-11-24: paid requests
    def paid_fake(self, core, state, sent):
        """ElevenLabs faked for a recording: the balance, the model rates, the account history and its audio, and TTS
        requests that work, or are cut off after ElevenLabs did (and billed) the work (state['mode'] 'timeout')."""
        mp3=self.fake_mp3().read_bytes()
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        def fake(req,timeout=None):
            url=req.full_url
            if url.endswith('/v1/user/subscription'):
                return Reply(json.dumps({'character_limit':100000,'character_count':state['used']}).encode())
            if url.endswith('/v1/models'):
                return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':1.0},
                                          'maximum_text_length_per_request':10000}]).encode())
            if '/v1/history/' in url and url.endswith('/audio'):
                return Reply(mp3)
            if '/v1/history' in url:
                return Reply(json.dumps({'history':state['history']}).encode())
            body=json.loads(req.data.decode())
            sent.append(body)
            state['used']+=len(body['text'])
            if state.get('mode')=='timeout':        # the work was done and billed; the answer never came back
                state['done_unseen'].append({'history_item_id':f'H{len(sent)}','text':body['text'],
                                             'model_id':body['model_id'],'date_unix':int(time.time())+5,
                                             'character_count_change_from':0,'character_count_change_to':len(body['text'])})
                raise TimeoutError('the read timed out')
            return Reply(mp3)
        return fake

    def picked_voice(self):
        vd=self.tagged_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        cli('voice-pick','--run',self.run,'--video',1,'--voice-id','VOICEA','--settings',
            '{"stability":0.6,"similarity_boost":0.8}','--reason','a warm curious friend at a table telling it plainly')
        return vd

    def ledger(self):
        return [json.loads(x) for x in (self.run/'logs/elevenlabs-ledger.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_an_unknown_paid_outcome_is_never_billed_twice(self):
        # A request cut off, timed out or answered by a server error may have been billed: it is never sent again on its
        # own. Its audio comes from the account history (free) when ElevenLabs finished it, else the job stops until the
        # user has checked the account (--retry-unreconciled ID --reason), on the ledger.
        core=self.load_core()
        self.picked_voice()
        tts=['tts','--run',self.run,'--video',1]
        skip=['--skip-calibration','--reason','testing what happens after a request is cut off']
        sent=[]; state={'used':0,'mode':None,'history':[],'done_unseen':[]}
        fake=self.paid_fake(core,state,sent)
        self.assertEqual(self.core_call(core,*tts,'--max-parts',1,'--execute',fake=fake)[0],0)        # part 1, fine
        state['mode']='timeout'
        code,out=self.core_call(core,*tts,*skip,'--max-parts',1,'--execute',fake=fake)                # part 2 cut off
        self.assertEqual((code,out['details']['outcome']),(2,'uncertain'))
        self.assertIn('sends nothing while its outcome is unknown',out['details']['resume'])
        self.assertEqual([x.get('outcome') for x in self.ledger() if x['phase']=='done'],['completed','uncertain'])
        # the account history does not show it yet: nothing is sent, the job stops for the user
        state['mode']=None
        before=len(sent)
        code,out=self.core_call(core,*tts,*skip,'--max-parts',1,'--execute',fake=fake)
        self.assertEqual((code,len(sent)),(2,before))
        self.assertIn('no known outcome',out['error'])
        # once the history holds it, the take comes from there: no second charge, recorded as recovered
        state['history']=list(state['done_unseen'])
        code,out=self.core_call(core,*tts,*skip,'--max-parts',1,'--execute',fake=fake)
        self.assertEqual((code,len(sent)),(0,before),out)
        man=json.loads((self.run/'50-audio/video-01/manifest.json').read_text())
        self.assertTrue(man['part_records']['2']['recovered_from_history'])
        self.assertIn('recovered',[x['phase'] for x in self.ledger()])
        # a request that never reached the history: sent again only on the user's word, which goes on the ledger
        state.update(mode='timeout',history=[],done_unseen=[])
        self.assertEqual(self.core_call(core,*tts,*skip,'--max-parts',1,'--execute',fake=fake)[0],2)  # part 3 cut off
        state['mode']=None
        code,out=self.core_call(core,*tts,*skip,'--max-parts',1,'--execute',fake=fake)
        self.assertEqual(code,2)
        a3=out['details']['unsettled'][0]['attempt_id']
        n=len(sent)
        code,out=self.core_call(core,*tts,'--skip-calibration','--retry-unreconciled',a3,'--reason',
                                'checked the account usage: part 3 was not billed','--max-parts',1,'--execute',fake=fake)
        self.assertEqual((code,len(sent)),(0,n+1),out)
        self.assertTrue(any(r['phase']=='reconciled' and r['attempt_id']==a3 for r in self.ledger()))
        # a refused request (4xx) was never billed: nothing to settle
        core.ledger_add(self.run,{'at':core.now(),'kind':'tts','attempt_id':'R1','pid':os.getpid(),'request_sha256':'r',
                                  'phase':'pending'})
        core.ledger_add(self.run,{'at':core.now(),'kind':'tts','attempt_id':'R1','phase':'done','ok':False,'outcome':'failed'})
        self.assertEqual(core.paid_unsettled(self.run,'r'),[])

    def test_an_unknown_design_or_probe_outcome_stops_with_nothing_sent(self):
        # The same rule for every billed request (Voice Design, probes, trials): a cut-off attempt whose process is gone
        # stops the next one until the user allows it; an attempt still being sent by a live process is never doubled.
        core=self.load_core()
        core.ledger_add(self.run,{'at':core.now(),'kind':'voice_design','attempt_id':'D1','pid':999999,'request_sha256':'d',
                                  'phase':'pending'})
        self.assertEqual([x['state'] for x in core.paid_unsettled(self.run,'d')],['cut_off'])
        with mock.patch('sys.stdout',new_callable=io.StringIO) as out, self.assertRaises(SystemExit):
            core.paid_reconcile(self.run,None,'d',{'text':'x'},None,from_history=False)
        self.assertIn('no known outcome',json.loads(out.getvalue())['error'])
        with mock.patch('sys.stdout',new_callable=io.StringIO), self.assertRaises(SystemExit):     # a reason is required
            core.paid_reconcile(self.run,None,'d',{'text':'x'},None,retry='D1',from_history=False)
        self.assertEqual(core.paid_reconcile(self.run,None,'d',{'text':'x'},None,retry='D1',
                                             reason='checked the usage page: the design call was not billed',
                                             from_history=False),(None,None))
        self.assertEqual(core.paid_unsettled(self.run,'d'),[])                       # settled once, on the ledger
        core.ledger_add(self.run,{'at':core.now(),'kind':'probe','attempt_id':'P1','pid':os.getpid()+0,'request_sha256':'p',
                                  'phase':'pending'})
        with mock.patch.object(core,'_pid_running',return_value=True), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as out, self.assertRaises(SystemExit):
            core.paid_reconcile(self.run,None,'p',{'text':'x'},None,from_history=False)
        self.assertIn('right now',json.loads(out.getvalue())['error'])

    def test_calibration_cannot_be_bypassed_one_part_at_a_time(self):
        # Before this voice setup has a real measured pace, only the parts it takes to reach a measurable sample are
        # recorded; asking for one part at a time does not get round it, and a skip needs its reason on record.
        core=self.load_core()
        vd=self.picked_voice()
        tts=['tts','--run',self.run,'--video',1]
        sent=[]; state={'used':0,'mode':None,'history':[],'done_unseen':[]}
        fake=self.paid_fake(core,state,sent)
        lines=json.loads((vd/'script.json').read_text())['lines']
        chunks=cli(*tts)['candidate_manifest']['chunks']
        words=[sum(core.count_words(lines[i-1]['text']) for i in range(c['line_start'],c['line_end']+1)) for c in chunks]
        recorded=0
        for k in range(len(chunks)):
            code,out=self.core_call(core,*tts,'--max-parts',1,'--execute',fake=fake)
            if code:
                break
            recorded+=1
        self.assertEqual(code,2,'every part was recorded before the voice was measured')
        self.assertIn('Calibrate first',out['error'])
        self.assertGreaterEqual(sum(words[:recorded]),core.CALIBRATION_MIN_WORDS)      # the sample is there
        self.assertLess(sum(words[:recorded-1]),core.CALIBRATION_MIN_WORDS)            # and nothing beyond it
        self.assertEqual(self.core_call(core,*tts,'--skip-calibration','--max-parts',1,'--execute',fake=fake)[0],2)
        code,out=self.core_call(core,*tts,'--skip-calibration','--reason','the user heard part one and approved the voice',
                                '--max-parts',1,'--execute',fake=fake)
        self.assertEqual(code,0,out)
        hist=json.loads((self.run/'50-audio/video-01/manifest.json').read_text())['history']
        self.assertTrue(any(h.get('skip_calibration') for h in hist))
        # the part records carry what was billed (the balance drop here: no cost header in the fake)
        man=json.loads((self.run/'50-audio/video-01/manifest.json').read_text())
        self.assertEqual(man['part_records']['1']['credits_billed'],chunks[0]['characters'])

    def test_openai_images_are_an_explicit_choice_and_never_billed_twice(self):
        # FLUX 3 Image Klein int8 is the run's engine; OpenAI Images only on the user's choice on record. Each request goes
        # on the images manifest before it is sent; an unknown outcome is not sent again until the user allows it.
        self.write_plan()
        shots=self.shots_for_plan()
        job={'run':str(self.run),'video':1,'model':'gpt-image-2.5-flare','size':'1536x864','quality':'high',
             'images':[{'id':'S1','shot_id':'S1','prompt':shots[0]['frame_prompt']+', painterly, soft edges','file':'S1.png'}]}
        jobp=self.home/'openai-job.json'; save(jobp,job)
        spec=importlib.util.spec_from_file_location('openai_images_worker_t', ROOT/'scripts/openai_images_worker.py')
        ow=importlib.util.module_from_spec(spec); spec.loader.exec_module(ow)
        png=b'\x89PNG\r\n\x1a\n'+b'2'*4096
        calls={'n':0,'mode':'ok'}
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        def fake(req,timeout=None):
            calls['n']+=1
            if calls['mode']=='timeout':
                raise TimeoutError('the read timed out')
            import base64 as b64
            return Reply(json.dumps({'data':[{'b64_json':b64.b64encode(png).decode()}]}).encode())
        def run(*extra):
            with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'test-not-a-real-key'}), \
                    mock.patch.object(ow.urllib.request,'urlopen',side_effect=fake), \
                    mock.patch.object(sys,'argv',['openai_images_worker.py','--job',str(jobp),'--execute',*map(str,extra)]), \
                    mock.patch('sys.stdout',new_callable=io.StringIO) as out:
                try:
                    ow.main(); code=0
                except SystemExit as e:
                    code=e.code
            return code,json.loads(out.getvalue())
        code,out=run()
        self.assertEqual((code,calls['n']),(2,0))
        self.assertTrue(any(x.startswith('image_engine_not_chosen_for_this_run:openai') for x in out['issues']))
        cli('image-engine','--run',self.run,'--engine','openai',expected=2)                 # the user's words needed
        cli('image-engine','--run',self.run,'--engine','openai','--why','the user: use OpenAI for this run')
        calls['mode']='timeout'
        code,out=run()
        self.assertEqual((code,out['outcome'],calls['n']),(2,'uncertain',1))
        stills=self.run/'60-visuals/video-01/stills'                                   # the run's own stills folder
        self.assertEqual(json.loads((stills/'images-manifest.json').read_text())['results'][0]['status'],'uncertain')
        calls['mode']='ok'
        code,out=run()
        self.assertEqual((code,calls['n']),(2,1))                                        # not sent again on its own
        self.assertIn('no known outcome',out['error'])
        code,out=run('--retry-unreconciled','S1.png','--reason','checked the usage page: nothing was billed')
        self.assertEqual((code,calls['n']),(0,2),out)
        rec=json.loads((self.run/'60-visuals/video-01/stills-provenance.json').read_text())['images']
        (k,v),=rec.items()
        self.assertEqual((v['engine'],v['submitted_prompt']),('openai:gpt-image-2.5-flare',job['images'][0]['prompt']))
        made=v['made_at']
        code,out=run()                                                                     # reused: its record stays
        self.assertEqual((code,calls['n']),(0,2))
        self.assertEqual(json.loads((self.run/'60-visuals/video-01/stills-provenance.json').read_text())['images'][k]['made_at'],made)

    # ---------------------------------------------------------------- remediation 2026-11-24: FLUX Klein's caption
    def test_the_upsampler_caption_is_checked_for_what_it_adds(self):
        core=self.load_core()
        req='A wooden desk by a window at dusk, an open notebook and a fountain pen, no people, painted in gouache.'
        good=req+' The light is low and warm; there are no other people, and no writing, lettering or labels anywhere.'
        self.assertEqual(core.caption_issues_with((),req,good),[])                     # negations are not additions
        self.assertTrue(any(x.startswith('caption_adds_a_child') for x in
                            core.caption_issues_with((),req,req+' A young boy sits at the desk.')))
        self.assertTrue(any(x.startswith('caption_adds_people_the_prompt_does_not_have:man') for x in
                            core.caption_issues_with((),req,req+' A man in a coat leans over the notebook.')))
        self.assertTrue(any(x.startswith('caption_adds_written_text') for x in
                            core.caption_issues_with((),req,req+' A sign with text reads OPEN.')))
        self.assertTrue(any(x.startswith('caption_keeps_') for x in
                            core.caption_issues_with((),req,'A busy harbour at noon with ships and gulls.')))
        theme=[{'theme':'V001/S2','label':'excluded_theme','avoid':['burning church']}]
        self.assertTrue(any('rules_out' in x for x in core.caption_issues_with(theme,req,req+' A burning church in the distance.')))
        self.assertTrue(any('content_flag_unanswered' in x for x in core.caption_issues_with((),req,req+' Blood on the floor.')))
        self.assertEqual(core.caption_issues_with((),req,req+' Blood-orange sky outside.',
                                                  'a blood-orange evening sky, no injury anywhere in the picture'),[])
        # Words that name a person in one sense only (a REAL FLUX upsampler caption, 2026-11-24, of a scene with no people:
        # "weathered plank faces", hills as "overlapping blue-green silhouettes"): drawn, with a note for the look.
        smoke=('a wide green valley at dawn, a narrow dirt road leading to a small supply depot of stacked wooden crates '
               'under a canvas awning, mist lying in the low fields, distant hills, no people, painterly, soft edges')
        real=("Painterly landscape illustration with soft edges, showing a wide green valley at dawn beneath a pale"
              " blue and peach sky. In the foreground, a narrow ochre dirt road begins near the lower center and wi"
              "nds into the valley, its uneven surface marked by shallow ruts, scattered stones, and tufts of grass"
              " along the margins. The road leads toward a small supply depot in the middle distance, right of cent"
              "er. A faded tan canvas awning stretches over a low wooden platform where several stacks of rough-hew"
              "n wooden crates sit in orderly rows, some stacked two high and others piled three high. The crates h"
              "ave dark iron corner fittings and weathered plank faces, with no lettering or labels. Low posts supp"
              "ort the sagging awning, whose front edge hangs above the crates and casts a muted shadow across them"
              ". Dew-darkened grass borders the depot, while patches of fog drift around its base. Across the left "
              "and center midground, broad fields lie in layers of white mist, with only irregular green slopes and"
              " darker hedgerows emerging through the haze. Distant rounded hills form overlapping blue-green silho"
              "uettes along the horizon, their upper ridges touched by the first warm light of sunrise. Thin clouds"
              " gather above the hills, shifting from cool grey-blue overhead to pale apricot near the horizon. The"
              " empty road, open fields, and unoccupied depot contain no figures, animals, carts, or workers; only "
              "grasses, mist, the winding road, and the crate-filled shelter remain clearly defined within the wide"
              " composition.")
        self.assertEqual(core.caption_review_with((),smoke,real),
                         {'issues':[],'notes':['caption_says_faces,silhouettes:words_that_may_name_people:'
                                               'look_for_people_in_the_still_when_it_lands'],
                          'people_hints':['faces','silhouettes']})
        # a word that clearly names a person stops the caption for a decision; one that only may goes to the look
        for extra,word in (('Her face is lit by the dawn.','face'),('Two workers unload the crates.','workers'),
                           ('A hooded figure walks along the ridge.','figure')):
            self.assertEqual(core.caption_issues_with((),smoke,smoke+'. '+extra),
                             [f'caption_adds_people_the_prompt_does_not_have:{word}'])
        for extra,word in (('A lone figure stands on the ridge.','figure'),('A figure in the doorway.','figure'),
                           ("The lighthouse's dark silhouette is standing on the far point.",'silhouette'),
                           ('A carved figure decorates the gate.','figure')):
            r=core.caption_review_with((),smoke,smoke+'. '+extra)
            self.assertEqual((r['issues'],r['people_hints']),([],[word]))          # drawn; its look answers it
            self.assertEqual(core.people_question(smoke,r),{'prompt_excludes_people':True,'hints':[word]})
        self.assertEqual(core.caption_review_with((),smoke,smoke+'. No figures or workers appear anywhere.'),
                         {'issues':[],'notes':[],'people_hints':[]})
        self.assertEqual(core.caption_review_with((),'a lone figure standing on a ridge at dawn',
                                                  'A lone figure stands on a ridge at dawn, his coat moving in the wind.'),
                         {'issues':[],'notes':[],'people_hints':[]})
        # a prompt that rules people out asks every still's look the question, whatever words the caption uses
        self.assertTrue(core.people_excluded('an empty quay at dusk, nobody in sight'))
        self.assertTrue(core.people_excluded('a ledger on a desk, no people'))
        self.assertFalse(core.people_excluded('a soldier reads the order by lamplight'))
        self.assertEqual(core.people_question('a ledger on a desk, no people',{'people_hints':[]}),
                         {'prompt_excludes_people':True,'hints':[]})
        self.assertIsNone(core.people_question('a ledger on a desk',{'people_hints':[]}))
        # words in quotation marks are what FLUX writes into the picture: ones the prompt does not give are stopped
        led='a cluttered desk with an open ledger of handwritten names, no people'
        self.assertEqual(core.caption_issues_with((),led,'A cluttered desk with an open ledger of handwritten names '
                                                   'in brown ink: "Arthur Bell", \u201cEleanor Finch\u201d; no people.'),
                         ['caption_adds_words_to_draw:Arthur Bell|Eleanor Finch'])
        self.assertEqual(core.caption_issues_with((),'a shop sign reading "OPEN" above the door',
                                                  'A wooden shop sign reading "OPEN" above a green door.'),[])
        # an edit caption from a reference image says what to take out: "remove all people" rules people out (a real
        # FLUX caption, 2026-11-24); "Crowd the pages" is a verb no word list can tell apart: that is a decision
        desk='the same desk seen closer, an open ledger of illegible entries, no people'
        self.assertEqual(core.caption_issues_with((),desk,'Keep the same desk seen closer with an open ledger of '
                                                  'illegible entries, but remove all people.'),[])
        self.assertEqual(core.caption_issues_with((),desk,'Keep the same desk seen closer, an open ledger of illegible '
                                                  'entries, no people. Crowd both pages with dense columns.'),
                         ['caption_adds_people_the_prompt_does_not_have:crowd'])
        # ...and a removal reaches only what closely follows it: a person revealed further on is still a person
        self.assertEqual(core.caption_issues_with((),desk,'Keep the same desk seen closer, an open ledger of illegible '
                                                  'entries; remove the fog to reveal two soldiers by the window.'),
                         ['caption_adds_people_the_prompt_does_not_have:soldiers'])
        # a stopped caption is drawn only when accepted for exactly that caption, with its reason; an added child never
        cap=smoke+". A soldier's helmet lies in the grass."
        iss=core.caption_issues_with((),smoke,cap)
        self.assertEqual(iss,['caption_adds_people_the_prompt_does_not_have:soldier'])
        sha=hashlib.sha256(cap.encode('utf-8')).hexdigest()
        self.assertEqual(core.caption_acceptance({'sha256':sha,'why':'only the helmet is there, nobody wears it'},cap,iss),
                         (True,None))
        self.assertFalse(core.caption_acceptance({'sha256':'0'*64,'why':'only the helmet is there, nobody wears it'},cap,iss)[0])
        self.assertFalse(core.caption_acceptance({'sha256':sha,'why':'fine'},cap,iss)[0])
        kid=smoke+'. A boy runs along the road.'
        kid_iss=core.caption_issues_with((),smoke,kid)
        self.assertIn('never accepted',core.caption_acceptance({'sha256':hashlib.sha256(kid.encode('utf-8')).hexdigest(),
                                                                'why':'he is only a small part of the wide scene'},
                                                               kid,kid_iss)[1])

    def flux_worker(self):
        spec=importlib.util.spec_from_file_location('flux_image_worker_t', ROOT/'scripts/image_worker.py')
        iw=importlib.util.module_from_spec(spec); spec.loader.exec_module(iw)
        return iw

    def run_flux(self, iw, job, captions, drawn):
        """image_worker.py's own generate path (FLUX 3 Image Klein int8), with only the ComfyUI process faked: the
        upsampler answers `captions` in turn, the image model writes a small PNG, and what it was given is kept."""
        root=self.home/'comfy'
        (root/'ComfyUI').mkdir(parents=True,exist_ok=True); (root/'ComfyUI'/'main.py').write_text('',encoding='utf-8')
        for sub,name in iw.MODELS.values():
            f=root/'ComfyUI'/'models'/sub/name; f.parent.mkdir(parents=True,exist_ok=True)
            if not f.exists():
                f.write_bytes(b'0'*64)
        work=self.home/'flux-work'
        caps=list(captions)
        def fake_run(proc,port,graph,timeout):
            kinds={str(n.get('class_type')) for n in graph.values() if isinstance(n,dict)}
            if 'TextGenerateV2' in kinds:
                return {'outputs':{'caption':{'text':[caps.pop(0)]}}},None
            drawn.append(graph['pos']['inputs']['text'])
            (work/'out').mkdir(parents=True,exist_ok=True)
            name=f'img{len(drawn)}.png'
            (work/'out'/name).write_bytes(b'\x89PNG\r\n\x1a\n'+bytes([len(drawn)])*2048)
            return {'outputs':{'save':{'images':[{'filename':name,'subfolder':''}]}}},None
        class Proc:
            returncode=None
            def poll(self): return None
        jobp=self.home/'flux-job.json'; save(jobp,{**job,'root':str(root)})
        code=0
        with mock.patch.object(iw,'start',return_value=(Proc(),None)), \
                mock.patch.object(iw,'wait_ready',return_value=({'system':{'comfyui_version':'0.41.0'}},None)), \
                mock.patch.object(iw,'run_prompt',side_effect=fake_run), mock.patch.object(iw,'free_models'), \
                mock.patch.object(iw,'stop'), mock.patch.object(iw,'stage_refs',return_value=[]), \
                mock.patch.object(iw.tempfile,'mkdtemp',side_effect=lambda **k: str(work)), \
                mock.patch.object(sys,'argv',['image_worker.py',str(jobp)]), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as out:
            try:
                iw.main()
            except SystemExit as e:
                code=e.code
        return code,json.loads(out.getvalue().strip().splitlines()[-1])

    def test_flux_klein_draws_only_an_approved_caption_and_records_what_it_drew(self):
        # The real FLUX 3 Image Klein int8 path (image_worker.py: the gate, the upsampler stage, the caption check, the
        # image stage, the provenance), ComfyUI faked: no model, no GPU.
        self.write_plan()
        shots=self.shots_for_plan()
        iw=self.flux_worker()
        stills=self.run/'60-visuals/video-01/stills'
        req=shots[0]['frame_prompt']+', painterly, soft edges'
        job={'op':'generate','run':str(self.run),'video':1,
             'images':[{'shot_id':'S1','prompt':req,'out':str(stills/'S1.png'),'seed':7,'width':1024,'height':576}]}
        good=req+' The valley opens under a pale dawn sky; no people and no lettering anywhere.'
        drawn=[]
        code,out=self.run_flux(iw,job,[good],drawn)
        self.assertEqual(code,0,out)
        self.assertEqual((out['engine'],out['precision']),('flux3-image-klein-int8','int8'))
        self.assertEqual(drawn,[good])                                                  # the model got the checked caption
        rec=json.loads((self.run/'60-visuals/video-01/stills-provenance.json').read_text())['images']
        (_k,v),=rec.items()
        self.assertEqual((v['engine'],v['precision'],v['submitted_prompt'],v['drew_from'],v['seed']),
                         ('flux3-image-klein-int8','int8',good,'caption',7))
        self.assertEqual(v['models']['unet'],'flux3-image-klein-int8-convrot.safetensors')
        self.assertEqual(v['caption_checks'],[])
        self.assertEqual(v['caption_notes'],[])
        # A caption that adds a child is never drawn; the item fails and says why.
        (stills/'S1.png').unlink()
        drawn.clear()
        code,out=self.run_flux(iw,job,[req+' A small boy waves from the ridge.'],drawn)
        self.assertEqual((code,drawn),(1,[]))
        self.assertIn('caption_adds_a_child',out['images'][0]['error'])
        self.assertFalse((stills/'S1.png').exists())
        # ...unless the item says to draw the approved prompt itself instead (recorded as such).
        job['images'][0]['on_caption_refused']='draw_request'
        code,out=self.run_flux(iw,job,[req+' A small boy waves from the ridge.'],drawn)
        self.assertEqual((code,drawn),(0,[req]))
        v=next(iter(json.loads((self.run/'60-visuals/video-01/stills-provenance.json').read_text())['images'].values()))
        self.assertEqual((v['submitted_prompt'],v['drew_from']),(req,'request (its caption was refused)'))
        # A caption stopped for a word that does not mean what it seems is drawn when the director accepts exactly
        # that caption, with the reason; the still then carries the people question its look must answer.
        job['images'][0].pop('on_caption_refused')
        helmet=req+" A soldier's helmet lies in the grass, no people anywhere."
        if (stills/'S1.png').exists():
            (stills/'S1.png').unlink()
        drawn.clear()
        code,out=self.run_flux(iw,job,[helmet],drawn)
        sha=hashlib.sha256(helmet.encode('utf-8')).hexdigest()
        self.assertEqual((code,drawn),(1,[]))
        self.assertIn(sha,out['images'][0]['error'])
        job['images'][0]['accept_caption']={'sha256':sha,'why':'only the helmet lies there, nobody wears it'}
        code,out=self.run_flux(iw,job,[helmet],drawn)
        self.assertEqual((code,drawn),(0,[helmet]))
        v=next(iter(json.loads((self.run/'60-visuals/video-01/stills-provenance.json').read_text())['images'].values()))
        self.assertEqual(v['caption_accepted']['issues'],['caption_adds_people_the_prompt_does_not_have:soldier'])
        self.assertEqual(v['people_question'],{'prompt_excludes_people':False,'hints':['soldier']})
        looks=self.home/'looks.json'
        save(looks,{'never_show_checked':True,'looks':[{'file':str(stills/'S1.png'),'result':'clean','note':'a helmet in the grass at dawn'}]})
        r=cli('content-review','--run',self.run,'--video',1,'--pictures','--file',looks,expected=2)
        self.assertIn('must_say_whether_anyone_appears',' '.join(r['details']))
        save(looks,{'never_show_checked':True,'looks':[{'file':str(stills/'S1.png'),'result':'clean','note':'a helmet in the grass at dawn',
                              'people':'a soldier stands behind the helmet'}]})
        r=cli('content-review','--run',self.run,'--video',1,'--pictures','--file',looks,expected=2)
        self.assertIn('someone_appears_that_its_prompt_does_not_ask_for',' '.join(r['details']))
        save(looks,{'never_show_checked':True,'looks':[{'file':str(stills/'S1.png'),'result':'clean','note':'a helmet in the grass at dawn',
                              'people':'none: only the helmet, nobody near it'}]})
        self.assertTrue(cli('content-review','--run',self.run,'--video',1,'--pictures','--file',looks)['ok'])
        job['images'][0].pop('accept_caption')
        # A job cannot swap the model or its precision.
        job['models']={'unet':'flux-dev-fp16.safetensors'}
        code,out=self.run_flux(iw,job,[good],drawn)
        self.assertEqual(code,1)
        self.assertIn('cannot swap',out['error'])


    # ---------------------------------------------------------------- remediation 2026-11-24: payoff and significance
    def test_a_candidate_payoff_is_assessed_before_the_choice(self):
        # Each niche's reward has its own shape: a history built to a decisive outcome, a tutorial delivering value
        # step by step, a comedy paying off several times. The chosen candidate's payoff must be assessed (an
        # alternative's gap is only a warning) and rest on its own material.
        core=self.load_core()
        d=self.direction_doc()
        s=d['subject']
        ok=lambda subj: core.subject_issues(subj,'',600,('V001','V002'))[0]
        base=[x for x in ok(s) if 'payoff' in x]
        self.assertEqual(base,[])
        for shape in ('builds_to','several','progressive'):
            s['candidates'][0]['payoff']['shape']=shape
            self.assertFalse([x for x in ok(s) if 'payoff' in x],shape)
        s['candidates'][0]['payoff']['shape']='climax'
        self.assertTrue(any('payoff_shape_must_be' in x for x in ok(s)))
        s['candidates'][0]['payoff']['shape']='builds_to'
        s['candidates'][0]['payoff']['rests_on']=['M9']
        self.assertTrue(any('payoff_rests_on_material_the_candidate_lacks:M9' in x for x in ok(s)))
        s['candidates'][0]['payoff'].update(rests_on=['M1'],worth_the_buildup='yes')
        self.assertTrue(any(x.endswith('payoff_needs_worth_the_buildup') for x in ok(s)))
        s['candidates'][0].pop('payoff')
        self.assertTrue(any(x.startswith('subject_candidate_T1_needs_its_payoff_assessed') for x in ok(s)))
        s=self.direction_doc()['subject']
        s['candidates'][1].pop('payoff')                            # an alternative: considered, so only a warning
        iss,warn=core.subject_issues(s,'',600,('V001','V002'))
        self.assertFalse([x for x in iss if 'T2' in x and 'payoff' in x])
        self.assertTrue([x for x in warn if 'T2' in x and 'payoff' in x])
        s['value_to_carry'][0].pop('payoff')                        # the chosen payoff becomes the value carried
        self.assertIn('subject_value_to_carry_names_no_payoff_value:mark_the_value_the_payoff_delivers_with_payoff_true',
                      core.subject_issues(s,'',600,('V001','V002'))[0])

    def test_the_payoff_value_reaches_the_film_in_its_own_shape(self):
        # A payoff the film builds to lands at a key moment that says what it means; a progressive one is delivered
        # along the way by more than one beat and needs no invented climax; it is never silently dropped.
        core=self.load_core()
        d=self.direction_doc()
        beats=[{'id':f'B0{i}','carries':[]} for i in range(1,6)]
        beats[4].update(carries=['R1'],key_moment='the earned conclusion',significance={'matters_because':'x'})
        self.assertEqual([x for x in core.subject_handoff_issues(d,beats) if 'payoff' in x],[])
        beats[4].pop('key_moment')
        self.assertTrue(any(x.startswith('payoff_value_R1_reaches_no_key_moment') for x in core.subject_handoff_issues(d,beats)))
        d['subject']['candidates'][0]['payoff']['shape']='progressive'       # a tutorial: value step by step
        self.assertTrue(any(x.startswith('progressive_payoff_value_R1_is_carried_by_one_beat')
                            for x in core.subject_handoff_issues(d,beats)))
        beats[1]['carries']=['R1']; beats[3]['carries']=['R1']
        self.assertEqual([x for x in core.subject_handoff_issues(d,beats) if 'payoff' in x],[])
        d['subject']['dropped']=[{'id':'R1','why':'it did not fit the treatment in the end'}]
        self.assertTrue(any(x.startswith('payoff_value_R1_is_dropped') for x in core.subject_handoff_issues(d,beats)))

    def test_treatments_say_how_they_deliver_the_payoff(self):
        self.write_plan(lock=False)
        vd=self.run/'40-plans/video-01'
        d=self.direction_doc()
        save(vd/'direction.json',d)
        core=self.load_core()
        self.assertFalse([x for x in core.direction_facts(self.run,1)['issues'] if 'payoff' in x])
        d['treatments'][1].pop('carries_values')
        d['decision'].pop('carries_payoff')
        save(vd/'direction.json',d)
        iss=core.direction_facts(self.run,1)['issues']
        self.assertIn('treatment_T2_does_not_say_how_it_delivers_the_payoff:R1:carries_values[{value,how}]',iss)
        self.assertIn('decision_missing_carries_payoff:how_the_chosen_treatment_makes_the_payoff_land',iss)
        # a direction whose research has no payoff value (locked before it existed) is not asked
        d['subject']['value_to_carry'][0].pop('payoff')
        save(vd/'direction.json',d)
        self.assertFalse([x for x in core.direction_facts(self.run,1)['issues'] if 'carries_payoff' in x or 'delivers_the_payoff' in x])
        self.assertEqual(core.field_effects('treatment.carries_values'),('beat-map','script'))

    def test_a_reader_whose_words_say_it_changes_little_is_a_finding(self):
        # The labels say it landed; the reader's own account says it changes little: the account is the evidence.
        core=self.load_core()
        order=[f'L{i:03}' for i in range(1,21)]
        km={'id':'B05','key_moment':'the reveal','significance':{'matters_because':'it decides the war'}}
        spans=[(km,15,20)]
        dev=lambda **k: dict({'lines':'L015-L018','what_happened':'the agent sends the last message','event':'clear',
                              'significance':'clear','reward':'landed','why_from':'the video','learned_when':'before',
                              'why_it_matters':'it makes the plan work','would_be_different':'the plan would fail'},**k)
        self.assertEqual(core.development_findings('script',[dev()],set(),spans,order),[])
        f,=core.development_findings('script',[dev(would_be_different='nothing much would be different, the war goes on')],
                                     set(),spans,order)
        self.assertEqual((f['severity'],f['derived_from']['reward']),('major','landed'))
        self.assertIn('changes little',f['likely_cause'])
        # weighed, not dismissed: no finding; off a key moment: minor
        self.assertEqual(core.development_findings('script',[dev(would_be_different='not much would change in the plot, '
                                                                 'but the agent would be unmasked')],set(),spans,order),[])
        f,=core.development_findings('script',[dev(lines='L002-L004',why_it_matters='it does not really matter')],set(),spans,order)
        self.assertEqual(f['severity'],'minor')
        # the reader's own note stays beside the computed cause, never in its place
        f,=core.development_findings('script',[dev(significance='unclear',note='too many names')],set(),spans,order)
        self.assertEqual((f['likely_cause'],f['reader_note']),('what it means was never established for the viewer','too many names'))

    def test_a_development_counts_for_a_key_moment_by_measured_overlap(self):
        core=self.load_core()
        km={'id':'B05'}
        span=[(km,316.4,330.0)]
        self.assertEqual(core._dev_overlaps('final',{'at':'05:10-05:15'},span,()),[])        # ends a second before
        self.assertEqual(core._dev_overlaps('final',{'at':'05:16'},span,()),[km])            # 316.4-317.0 shared
        self.assertEqual(core._dev_overlaps('final',{'at':'05:30'},span,()),[])              # 330 is its end: touch only
        self.assertEqual(core._dev_overlaps('final',{'at':'05:20-06:10'},span,()),[km])

    def test_key_moments_are_reconciled_with_the_readers_account(self):
        # After an independent read, the director sets each key moment's planned meaning beside the reader's account;
        # a gap is fixed like a major finding (its cause named, a fresh read follows), a different valid reading is kept.
        vd=self.write_plan(review_script=False)
        _,rec=self.review('script',[{'id':'F1','severity':'minor','lines':['L001-L002'],'problem':'the opening starts slowly'}])
        doc=json.loads(Path(rec['answers_file']).read_text(encoding='utf-8'))
        self.assertEqual(list(doc['reconcile']),['B05'])
        r=doc['reconcile']['B05']
        self.assertTrue(r['planned']['matters_because'])
        self.assertEqual(r['planned']['values'][0]['id'],'R1')
        self.assertTrue(r['planned']['values'][0]['payoff'])
        self.assertEqual(r['reader'][0]['why_it_matters'],'each turn changes what the people can do')
        ans={'F1':{'action':'kept','note':'the slow start is the treatment choice'}}
        self.answer_file(rec['answers_file'],{'answers':ans},reconcile=None)
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertIn('script_review_r1_key_moments_not_reconciled_with_the_readers_account:B05',iss)
        self.answer_file(rec['answers_file'],{'answers':ans},reconcile={'B05':{'verdict':'gap','note':'the reader never saw what the order cost'}})
        self.assertIn('script_review_r1_key_moments_not_reconciled_with_the_readers_account:B05',
                      cli('plan-check','--run',self.run,'--video',1,expected=None)['issues'])     # a gap needs its cause
        self.answer_file(rec['answers_file'],{'answers':ans},reconcile={'B05':{'cause':'setup','revision':'the order is set up in beat B02 now'}})
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in iss if 'not_reconciled' in x])
        self.assertIn('script_review_round_2_required',iss)                         # a gap counts as a major finding
        self.answer_file(rec['answers_file'],{'answers':ans},reconcile={'B05':{'verdict':'different_but_valid',
                         'note':'they read it as luck, which the film allows'}})
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in iss if 'not_reconciled' in x or 'round_2' in x])

    def test_a_revised_significance_finding_names_its_cause(self):
        core=self.load_core()
        f={'id':'S1','severity':'major','derived_from':{'development':1}}
        self.assertIn('needs the cause',core.answer_problem('script',f,{'action':'revised','lines':['L005']}))
        self.assertIsNone(core.answer_problem('script',f,{'action':'revised','lines':['L005'],'cause':'order'}))
        self.assertIn('which cause',core.answer_problem('script',f,{'action':'revised','lines':['L005'],'cause':'other'}))
        self.assertIsNone(core.answer_problem('script',f,{'action':'revised','lines':['L005'],
                                                          'cause':'other: the joke needs a beat of silence'}))
        self.assertIsNone(core.answer_problem('script',{'id':'F1','severity':'minor'},{'action':'revised','lines':['L1']}))


    # ---------------------------------------------------------------- remediation 2026-11-24: niche, readers, hand-offs
    def test_a_cohort_length_refuses_mixed_story_forms_unless_explained(self):
        for i,(form,cid) in enumerate((('tutorial','mine'),('historical narrative','mine')),1):
            cp=self.run/f'20-analysis/cards/V00{i}.json'
            card=json.loads(cp.read_text(encoding='utf-8')); card.update(story_form=form,cohort_id=cid); save(cp,card)
        out=cli('length','--run',self.run,'--video',1,'--mode','standard','--cohort-id','mine','--refs','V001,V002',
                '--pace-wpm',145,'--pace-why','the test narrator reads at this pace',expected=2)
        self.assertIn('mixes story forms',out['error'])
        out=cli('length','--run',self.run,'--video',1,'--mode','standard','--cohort-id','mine','--refs','V001,V002',
                '--pace-wpm',145,'--pace-why','the test narrator reads at this pace',
                '--forms-why','both are single-subject explainers of the same depth whatever their labels',expected=None)
        if out.get('ok'):
            lock=json.loads((self.run/'40-plans/video-01/length-lock.json').read_text(encoding='utf-8'))
            self.assertEqual(lock['story_forms'],['historical narrative','tutorial'])
            self.assertTrue(lock['forms_why'])
            core=self.load_core()
            self.assertEqual(core.locked_niche_names(self.run,lock),{'mine','military history'})

    def test_evidence_from_outside_the_niche_is_a_borrowed_technique(self):
        self.write_plan(lock=False)
        core=self.load_core()
        cp=self.run/'20-analysis/cards/V003.json'
        card=json.loads(cp.read_text(encoding='utf-8')); card.update(niches=['cooking']); save(cp,card)
        d=self.direction_doc()
        d['evidence']['references']=['V001','V002','V003']
        save(self.run/'40-plans/video-01/direction.json',d)
        iss=core.direction_facts(self.run,1)['issues']
        self.assertTrue(any(x.startswith('direction_evidence_V003_is_outside_the_locked_niche') for x in iss),iss)
        d['evidence']['borrowed']=[{'ref':'V003','technique':'the close slow build before each reveal',
                                    'not_taken':'its kitchen subject and its recipe structure'}]
        save(self.run/'40-plans/video-01/direction.json',d)
        self.assertFalse([x for x in core.direction_facts(self.run,1)['issues'] if 'outside_the_locked_niche' in x])
        d['subject']['scope'].pop('boundary')
        save(self.run/'40-plans/video-01/direction.json',d)
        self.assertIn('subject_niche_scope_needs_boundary',core.direction_facts(self.run,1)['issues'])

    def test_reader_packets_carry_no_pitch_and_no_excluded_scenes(self):
        self.write_plan(lock=False)
        vd=self.run/'40-plans/video-01'
        d=self.direction_doc()
        d['approaches'][2]['pitch']='THE DIRECTORS PITCH: this structure will make the battle unforgettable for everyone'
        save(vd/'direction.json',d)
        core=self.load_core()
        cut=[{'theme':'V001/S2','what':'a burning church at night','kind':'creative','label':'excluded_theme','avoid':[]}]
        with mock.patch.object(core,'excluded_themes',return_value=cut):
            code,pk=self.core_call(core,'review-packet','--run',self.run,'--video',1,'--kind','treatment')
            self.assertIn('burning church',core.house_rules(self.run,1))          # what the old packet would have said
        self.assertEqual(code,0,pk)
        text=Path(pk['packet']).read_text(encoding='utf-8')
        self.assertNotIn('burning church',text)
        self.assertNotIn('THE DIRECTORS PITCH',text)
        self.assertIn('House rules',text)
        self.assertNotIn('left out on purpose',text)
        meta=json.loads(next((vd/'reviews').glob('packet-treatment-r1.json')).read_text(encoding='utf-8'))
        self.assertIn('stops being one when',meta.get('scope_request') or '')         # the niche's line goes to the reader

    def test_a_read_records_how_its_reader_was_isolated(self):
        self.write_plan(review_script=False)
        _,rec=self.review('script',[{'id':'F1','severity':'minor','lines':['L001-L002'],'problem':'the opening starts slowly'}],
                          {'F1':{'action':'kept','note':'the slow start is the treatment choice'}})
        r=json.loads(Path(rec['record']).read_text(encoding='utf-8'))
        self.assertFalse(r['reader_confined'])
        self.assertIn('not confined',r['reader_route'])
        warn=cli('plan-check','--run',self.run,'--video',1,expected=None).get('warnings') or []
        self.assertTrue(any('review-read confines' in w for w in warn))

    def test_a_revision_gets_a_fresh_read_where_it_matters(self):
        # A fresh read follows a revision that touches what the reader's verdict rested on, however few its words; many
        # words reworded elsewhere do not force one (the user, 2026-11-24: no percentage decides it).
        core=self.load_core()
        old={f'L{i:03}':'the quiet order moved the depots before the march began at dawn' for i in range(1,21)}
        new=dict(old)
        self.assertEqual(core.script_revised_share(old,new),0.0)
        for i in range(1,11):
            new[f'L{i:03}']='an entirely different sentence about the river and the bridge and the town'
        self.assertGreater(core.script_revised_share(old,new),0.25)
        vd=self.write_plan(review_script=False)
        _,rec=self.review('script',[{'id':'F1','severity':'minor','lines':['L001-L030'],'problem':'the first half drags on'}])
        sc=json.loads((vd/'script.json').read_text(encoding='utf-8'))
        for l in sc['lines'][:30]:
            l['text']='a rewritten line that tells the depot story from the river crossing instead, plainly and briefly now.'
        save(vd/'script.json',sc)
        self.answer_file(rec['answers_file'],{'answers':{'F1':{'action':'revised','lines':['L001-L030'],'note':''}}})
        pc=cli('plan-check','--run',self.run,'--video',1,expected=None)
        self.assertFalse([x for x in pc['issues'] if x.startswith('script_revised_where_it_matters')],pc['issues'])
        self.assertTrue(any(w.startswith('script revised since its last read:') and 'none carries' in w
                            for w in pc['warnings']),pc['warnings'])
        deps=core.script_dependencies(vd)
        self.assertIn('key_moment:B05',deps['L045'])
        self.assertIn('payoff:R1',deps['L045'])
        self.assertNotIn('L001',deps)
        # one sentence of the key moment rewritten: its reader read another ending
        sc['lines'][44]['text']='and in the end the order saved nobody, because the depots burned before the march came.'
        save(vd/'script.json',sc)
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertTrue(any(x.startswith('script_revised_where_it_matters_since_its_last_read:L045(key_moment:B05)')
                            for x in iss),iss)
        # the director says on record that the change is wording only: no fresh read forced for it
        self.answer_file(rec['answers_file'],{'revision_notes':{'L045':'a clearer word order, the same ending and meaning'}})
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in iss if x.startswith('script_revised_where_it_matters')],iss)

    def test_uncertain_research_reaches_the_picture_and_the_music_its_direction(self):
        core=self.load_core()
        d=self.direction_doc()
        d['subject']['value_to_carry'].append({'id':'R2','what':'the route may have crossed the north ford',
                                               'why_it_matters':'it would explain the lost day','certainty':'speculative',
                                               'framed_as':'one reading of the dispatch, not a record'})
        beats=[{'id':'B01','carries':['R2']},{'id':'B02','carries':['R1']}]
        shots=[{'id':'S1','beat_id':'B01'},{'id':'S2','beat_id':'B02'},{'id':'S3','beat_id':'B01','reuses':'S1'}]
        self.assertEqual(core.uncertain_shot_issues(d,beats,shots),['shot_S1_of_beat_B01_needs_uncertainty_shown:R2_speculative'])
        shots[0]['uncertainty_shown']='the route is drawn dashed over the map as a reading, never a record'
        self.assertEqual(core.uncertain_shot_issues(d,beats,shots),[])
        beats[1].update(key_moment='the reveal',significance={'certainty':'contested'})
        self.assertEqual(core.uncertain_shot_issues(d,beats,shots),['shot_S2_of_beat_B02_needs_uncertainty_shown:significance_contested'])
        # a music track says how it serves its beats; the direction it answered goes on record
        self.write_plan()
        self.shots_for_plan()
        job={'op':'generate','run':str(self.run),'video':1,'tracks':[{'video':1,'beats':['B05'],'caption':'a low warm pulse','duration':20,
                                                                      'out':str(self.home/'bed.wav')}]}
        jp=self.home/'mjob.json'; save(jp,job)
        self.assertIn('track_1_needs_serves:how_its_caption_carries_out_the_sound_direction_of_its_beats',
                      cli('media-check','--job',jp,'--kind','music',expected=2)['issues'])
        job['tracks'][0]['serves']='a low pulse under the earned conclusion that never announces it'
        save(jp,job)
        with mock.patch('sys.stdout',new_callable=io.StringIO):
            g=core.media_gate(job,'music')
        self.assertTrue(g['ok'],g['issues'])
        self.assertEqual(g['records'][0]['serves'],job['tracks'][0]['serves'])
        self.assertEqual(g['records'][0]['direction']['beats']['B05']['key_moment'],'the earned conclusion')

    def test_a_music_bed_replaced_at_its_path_is_not_the_bed_that_was_made(self):
        core=self.load_core()
        with tempfile.TemporaryDirectory() as td:
            rd=Path(td)/'run'; (rd/'70-edit/video-01/music').mkdir(parents=True)
            bed=rd/'70-edit/video-01/music/M1.wav'; bed.write_bytes(b'RIFF-first')
            save(rd/'state.json',{'schema':core.SCHEMA,'run_id':'r'})
            core.record_media(rd,1,'music',[{'out':str(bed),'beats':['B01'],'production_rev':0}])
            rec=json.loads((rd/'70-edit/video-01/music-provenance.json').read_text(encoding='utf-8'))
            (k,v),=rec['tracks'].items()
            self.assertEqual(v['file_sha256'],core.file_sha256(bed))
            bed.write_bytes(b'RIFF-replaced')
            self.assertNotEqual(v['file_sha256'],core.file_sha256(bed))


    # ---------------------------------------------------------------- remediation 2026-11-24: style, pace, comprehension
    def test_stills_carry_exactly_the_locked_style(self):
        self.write_plan()
        shots=self.shots_for_plan()                                   # the direction is locked: the style is locked too
        core=self.load_core()
        stills=self.home/'stills'
        job={'op':'generate','run':str(self.run),'video':1,
             'images':[{'shot_id':'S1','prompt':shots[0]['frame_prompt']+', painterly, soft edges','out':str(stills/'S1.png')}]}
        jp=self.home/'style-job.json'; save(jp,job)
        ok=cli('media-check','--job',jp,'--kind','stills')
        self.assertEqual(ok['direction']['style_prompt'],'painterly, soft edges')
        # another look: the style is not carried and the added words reach for what the lock calls another look
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', photorealistic, harsh flash'
        save(jp,job)
        iss=cli('media-check','--job',jp,'--kind','stills',expected=2)['issues']
        self.assertTrue(any(x.startswith('item_1_does_not_carry_the_locked_style') for x in iss),iss)
        self.assertTrue(any(x.startswith('item_1_reaches_for_another_look:photorealistic') for x in iss),iss)
        # a shot's own light and framing are free with their reason: the look is an identity, not identical wording
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', painterly, soft edges, low warm rim light from the lamp'
        save(jp,job)
        self.assertTrue(any(x.startswith('item_1_adds_words_beyond_the_approved_prompt_and_the_style') for x in
                            cli('media-check','--job',jp,'--kind','stills',expected=2)['issues']))
        job['images'][0]['style_note']='the lamp is the only light in this shot, so its rim light belongs to the picture'
        save(jp,job)
        self.assertTrue(cli('media-check','--job',jp,'--kind','stills')['ok'])
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', a soft-edged painterly wash'
        job['images'][0]['style_note']='the same painterly soft look, worded for a wash of mist over the valley'
        save(jp,job)
        self.assertTrue(cli('media-check','--job',jp,'--kind','stills')['ok'])
        self.assertEqual(core.media_gate(job,'stills')['records'][0]['style_note'],job['images'][0]['style_note'])
        # a note never covers another look: that is a relock, or one picture's departure said on purpose
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', painterly, soft edges, photorealistic detail'
        save(jp,job)
        self.assertTrue(any(x.startswith('item_1_reaches_for_another_look:photorealistic') for x in
                            cli('media-check','--job',jp,'--kind','stills',expected=2)['issues']))
        job['images'][0]['style_departure']='an archival photograph insert, shown as a document inside the painted film'
        save(jp,job)
        self.assertTrue(cli('media-check','--job',jp,'--kind','stills')['ok'])
        for k in ('style_departure','style_note'):
            job['images'][0].pop(k)
        # a reference image steers the picture like words: the run's own material, or a locked style reference
        job['images'][0]['prompt']=shots[0]['frame_prompt']+', painterly, soft edges'
        outside=self.home/'elsewhere.png'; outside.write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*64)
        job['images'][0]['refs']=[str(outside)]
        save(jp,job)
        self.assertTrue(any(x.startswith('item_1_reference_outside_the_run:elsewhere.png') for x in
                            cli('media-check','--job',jp,'--kind','stills',expected=2)['issues']))
        inside=self.run/'60-visuals/video-01/stills/S0.png'; inside.parent.mkdir(parents=True,exist_ok=True)
        inside.write_bytes(outside.read_bytes())
        job['images'][0]['refs']=[str(inside)]
        save(jp,job)
        self.assertTrue(cli('media-check','--job',jp,'--kind','stills')['ok'])
        job['images'][0].pop('refs')
        # a lock without what would be another look is refused
        self.assertIn('--departs-when',cli('style-lock','--run',self.run,'--video',1,'--style-prompt','oil paint',
                                           '--why','trying another look entirely',expected=2)['error'])
        # a change of style is a new revision with its reason, kept in history
        cli('style-lock','--run',self.run,'--video',1,'--style-prompt','gouache, warm muted palette','--departs-when','photorealistic, flat vector',expected=2)
        r=cli('style-lock','--run',self.run,'--video',1,'--style-prompt','gouache, warm muted palette','--departs-when','photorealistic, flat vector',
              '--palette','#AA8844,#334455','--why','the treatment reader found the painterly look too soft')
        lock=json.loads((self.run/'60-visuals/video-01/style-lock.json').read_text(encoding='utf-8'))
        self.assertEqual((r['rev'],lock['history'][0]['style_prompt']),(2,'painterly, soft edges'))
        # a thumbnail carries the look, or says why it departs from it
        th={'run':str(self.run),'video':1,'purpose':'thumbnail',
            'images':[{'prompt':'a bold close portrait of a surveyor at dawn with a broken bridge behind','out':str(stills/'t.png')}]}
        save(jp,th)
        self.assertTrue(any('thumbnail_does_not_carry_the_locked_style' in x for x in cli('media-check','--job',jp,'--kind','stills',expected=2)['issues']))
        th['images'][0]['style_departure']='a thumbnail must read at a tiny size, so it is flatter and bolder than the film'
        save(jp,th)
        self.assertTrue(cli('media-check','--job',jp,'--kind','stills')['ok'])
        # the upsampler's caption keeps the locked look
        req='a wide valley at dawn, gouache, warm muted palette'
        self.assertIn('caption_drops_the_locked_style',' '.join(core.caption_review_with(
            (),req,'A photorealistic wide valley at dawn under a cold sky.',None,'gouache, warm muted palette')['issues']))
        self.assertEqual(core.caption_review_with((),req,'A gouache painting of a wide valley at dawn in a warm muted '
                                                  'palette.',None,'gouache, warm muted palette')['issues'],[])
        self.assertIn('caption_reaches_for_another_look:photorealistic',core.caption_review_with(
            (),req,'A gouache, warm muted palette view of a wide valley at dawn, photorealistic.',None,
            'gouache, warm muted palette',['photorealistic'])['issues'])
        # the lock goes stale when the treatment's visual language changes
        d=json.loads((self.run/'40-plans/video-01/direction.json').read_text(encoding='utf-8'))
        d['treatments'][0]['visual_language']='charcoal sketches on grey paper, high contrast, for this video'
        save(self.run/'40-plans/video-01/direction.json',d)
        self.assertTrue(any('visual_language_changed' in x for x in core.style_lock_state(self.run,1)[1]))

    def test_pace_needs_its_reason_and_is_never_a_blind_average(self):
        core=self.load_core()
        args=['length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
              '--story-form','historical narrative','--refs','V001,V002']
        code,out=self.core_call(core,*args,'--pace-wpm','145')
        self.assertEqual(code,2); self.assertIn('--pace-why',out['error'])
        with mock.patch.object(core,'compute_ref_wpm',return_value=(150,{'V001':118,'V002':182})):
            code,out=self.core_call(core,*args)
        self.assertEqual(code,2); self.assertIn('very different paces',out['error'])
        # intent against delivery, relative to this narration's own norm (never a universal range)
        beats=[{'id':'B1','pace':'slow and reflective'},{'id':'B2','pace_relative':'faster'},{'id':'B3','pace':'steady'},
               {'id':'B4','pace':'steady'},{'id':'B5','pace':'unhurried'}]
        beats+=[{'id':'B6','pace':'steady'},{'id':'B7','pace':'steady'}]
        rows=[{'id':'B1','wpm_inside_lines':180,'numbers_per_min':1},{'id':'B2','wpm_inside_lines':120,'numbers_per_min':0},
              {'id':'B3','wpm_inside_lines':150,'numbers_per_min':0},{'id':'B4','wpm_inside_lines':178,'numbers_per_min':9},
              {'id':'B5','wpm_inside_lines':125,'numbers_per_min':0},{'id':'B6','wpm_inside_lines':152,'numbers_per_min':0},
              {'id':'B7','wpm_inside_lines':148,'numbers_per_min':0}]
        sig=core.pace_signals(rows,beats)
        self.assertEqual({f['beat']:f['kind'] for f in sig},{'B1':'asked_slower_runs_faster_than_usual',
                                                             'B2':'asked_faster_runs_slower_than_usual',
                                                             'B4':'fast_where_densest'})
        self.assertEqual((sig[0]['narration_median_wpm'],sig[0]['variation_from']),(150,'beats'))
        # the same beats in a narration whose lines vary this much anyway: natural variation, nothing to examine
        lines=[{'words':12,'start_s':0,'end_s':12*60/v} for v in (90,110,135,150,165,190,210)]
        self.assertEqual(core.pace_signals(rows,beats,lines),[])
        # a whole narration outside the pace of every reference is examined once, for the whole
        whole=core.pace_signals(rows,beats,lines,{'reference_wpm':[120,140],'target_wpm':135})
        self.assertEqual([(f['beat'],f['kind'],f['references_wpm']) for f in whole],
                         [('overall','narration_outside_every_references_pace',[120,140])])
        self.assertEqual(core.pace_intent({'pace':'brisk but calm'}),None)            # mixed words: not inferred
        txt='## Self-audit\nok\n## Pace\n- B1: the quickening is the point here, the reveal rushes in\n## Next\n'
        self.assertIn('B1',core.editorial_section(txt,'pace'))
        self.assertNotIn('Next',core.editorial_section(txt,'pace'))

    def test_comprehension_signals_are_classified_in_context(self):
        vd=self.write_plan()
        sc=json.loads((vd/'script.json').read_text(encoding='utf-8'))
        sc['lines'][0]['text']='In Vienna, Anna met Boris, Carla and Dmitri at the station before the long march began there.'
        sc['lines'][1]['text']='Boris carried the money. Carla carried the papers. Dmitri carried nothing but the maps today.'
        sc['lines'][2]['text']='Dmitri watched Anna. Nobody in Vienna watched Dmitri, and Boris never asked Carla why at all.'
        save(vd/'script.json',sc)
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertTrue(any(x.startswith('comprehension_signals_not_classified_in_the_editorial_review:L001') for x in iss),iss)
        rv=(vd/'editorial-review.md').read_text(encoding='utf-8')
        (vd/'editorial-review.md').write_text(rv+'\n## Comprehension\n- L001: necessary_complexity: the four travellers are the '
                                              'story, each named by what they carry\n',encoding='utf-8')
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertFalse([x for x in iss if x.startswith('comprehension_signals_not_classified')])
        b=json.loads((vd/'blueprint.json').read_text(encoding='utf-8')); b.pop('audience_knows'); save(vd/'blueprint.json',b)
        self.assertTrue(any(x.startswith('blueprint_missing_audience_knows') for x in
                            cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']))
        # one line may answer signals that share a root (a name, a beat); never a blanket line over unrelated ones
        core=self.load_core()
        sig=['L001-L003: 4 names to hold arrive in about 30 s (Anna, Boris, Carla, Dmitri). Can a first-time viewer hold them?',
             'L020: "Boris" returns after about 4.0 min, heard only once or twice before. Does the viewer still know?',
             'L040: "Vienna" returns after about 5.0 min, heard only once or twice before. Does the viewer still know?']
        beat_of={'L001':'B01','L020':'B02','L040':'B04'}
        ok='- L001, L020: necessary_complexity: Boris is the thread the story follows, and his return pays it off\n'
        self.assertEqual(core.comprehension_unclassified(sig,ok,beat_of),(['L040'],[]))
        blanket='- L001, L020, L040: necessary_complexity: all of these are fine, the viewer will cope with them\n'
        self.assertEqual(core.comprehension_unclassified(sig,blanket,beat_of),([],['L040']))
        own=blanket+'- L040: missing_context: Vienna needs a reminder of the station where it all began\n'
        self.assertEqual(core.comprehension_unclassified(sig,own,beat_of),([],[]))
        self.assertEqual(core.comprehension_unclassified(sig,blanket,{'L001':'B01','L020':'B01','L040':'B01'}),([],[]))
        # a line the editorial review names as a comprehension gap is one a later revision must have read again
        self.assertNotIn('comprehension_gap',core.script_dependencies(vd).get('L001',[]))      # necessary_complexity
        rv=(vd/'editorial-review.md').read_text(encoding='utf-8')
        (vd/'editorial-review.md').write_text(rv+'- L002: accidental_confusion: the maps need a word of context before '
                                              'they matter\n',encoding='utf-8')
        self.assertIn('comprehension_gap',core.script_dependencies(vd).get('L002',[]))

    def test_an_older_direction_keeps_its_plan_and_hears_the_new_rules_as_advice(self):
        # A direction approved before the planning rules of 2026-11-24 (its lock has no planning_rules stamp) is never
        # sent back to re-plan: those checks become advisories. Its other checks stay as they are.
        vd=self.write_plan()
        lock=json.loads((vd/'direction-lock.json').read_text(encoding='utf-8'))
        self.assertEqual(lock['planning_rules'],2)                                   # a new lock is stamped
        b=json.loads((vd/'blueprint.json').read_text(encoding='utf-8')); b.pop('audience_knows'); save(vd/'blueprint.json',b)
        self.assertTrue(any(x.startswith('blueprint_missing_audience_knows') for x in
                            cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']))
        lock.pop('planning_rules'); save(vd/'direction-lock.json',lock)             # an older direction's lock
        pc=cli('plan-check','--run',self.run,'--video',1,expected=None)
        self.assertFalse([x for x in pc['issues'] if x.startswith('blueprint_missing_audience_knows')],pc['issues'])
        self.assertTrue(any(w.startswith('advisory') and 'blueprint_missing_audience_knows' in w for w in pc['warnings']))
        (vd/'editorial-review.md').unlink()                                         # not a planning rule: still an issue
        self.assertIn('editorial_review_missing',cli('plan-check','--run',self.run,'--video',1,expected=None)['issues'])
        core=self.load_core()
        iss=['style_lock_missing:x','item_1_prompt_does_not_carry_shot_S1_frame_prompt','caption_adds_a_child:boy',
             'track_1_needs_serves:y','content_flag_unanswered:z']
        warn=[]
        self.assertEqual(core.older_plan_advisory(self.run,1,iss,warn),['style_lock_missing:x','track_1_needs_serves:y'])
        self.assertEqual(iss,['item_1_prompt_does_not_carry_shot_S1_frame_prompt','caption_adds_a_child:boy',
                              'content_flag_unanswered:z'])
        self.assertEqual(len(warn),2)

    def test_a_changed_beat_flags_its_unchanged_lines(self):
        vd=self.write_plan()
        first=cli('plan-check','--run',self.run,'--video',1,expected=None)
        if not first['ready']:
            self.skipTest('the fixture plan does not pass plan-check here: '+','.join(first['issues'][:3]))
        bm=json.loads((vd/'beat-map.json').read_text(encoding='utf-8'))
        bm['beats'][1]['experience']='the viewer now feels the cost before the order, a different beat'
        save(vd/'beat-map.json',bm)
        iss=cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
        self.assertTrue(any(x.startswith('beat_B02_changed_since_its_lines_were_checked') for x in iss),iss)
        cli('plan-check','--run',self.run,'--video',1,'--keep','short',expected=2)            # a reason, not a word
        out=cli('plan-check','--run',self.run,'--video',1,'--keep','the lines already carry the cost before the order',expected=None)
        self.assertFalse([x for x in out['issues'] if 'changed_since_its_lines' in x])
        # status: the stage comes from the recorded gates, and the run's stored stage follows
        core=self.load_core()
        state=json.loads((self.run/'state.json').read_text(encoding='utf-8'))
        state['stage']='planning'; save(self.run/'state.json',state)            # a stale stored stage
        st=cli('status','--run',self.run)
        derived=st['videos']['1']['stage']
        self.assertIn(derived,core.STAGES)
        self.assertGreaterEqual(core.STAGES.index(derived),core.STAGES.index('direction_locked'))
        stored=json.loads((self.run/'state.json').read_text(encoding='utf-8'))['stage']
        self.assertEqual(stored,derived)                                          # corrected forward, from the gates

    def test_reference_evidence_is_measured_honestly(self):
        spec=importlib.util.spec_from_file_location('av_tools_t', ROOT/'scripts/av_tools.py')
        av=importlib.util.module_from_spec(spec); spec.loader.exec_module(av)
        w=lambda t,a,b: {'text':t,'start_s':a,'end_s':b}
        words=[w('one',13.0,13.4),w('two',13.5,14.2),w('three',16.0,16.4),w('four',16.5,16.9)]   # a 1.8 s pause at 15 s
        self.assertEqual(av.span_stats(words,None,0,15)['pauses']+av.span_stats(words,None,15,30)['pauses'],1)
        self.assertEqual(av.span_stats(words,None,0,15)['longest_pause_s'],1.8)
        feats=[{'t':i*0.5} for i in range(400)]
        kinds=['still']+['flash' if i%3==0 else 'still' for i in range(1,400)]
        self.assertGreater(len(av.inspect_candidates(feats,kinds,[])),60)                 # never a silent first 60
        out=cli('inspect-window','--run',self.run,'--ref','V001','--from','0','--to','2','--fps',2,expected=2)
        self.assertIn('samples faster',out['error'])

    def test_content_flags_cover_indecency_children_and_not_a_winding_road(self):
        core=self.load_core()
        self.assertEqual(core.prompt_flags('a dirt road wound through the green valley at dawn'),[])
        self.assertEqual(core.prompt_flags('a deep wound on the soldier arm'),['injury_gore_distress'])
        self.assertIn('indecency',core.prompt_flags('a naked swimmer at the lake'))
        self.assertIn('minor_in_the_picture',core.prompt_flags('a young boy waving from the ridge'))
        self.assertNotIn('minor_in_the_picture',core.prompt_flags('an empty schoolyard, no children anywhere'))
        self.assertEqual(core.prompt_flag_issues('item_1_prompt',['minor_in_the_picture'],'a long note that tries to answer it'),
                         ['item_1_prompt_shows_a_child:every_person_in_a_picture_is_an_adult_rewrite_it'])
        # treatments and beats that name what a cited reference's content review cut: rewritten, or a recorded context
        self.write_plan(lock=False)
        vd=self.run/'40-plans/video-01'
        d=self.direction_doc()
        d['treatments'][0]['sound']='a burning church bell tolls under the whole film, low and steady for this video'
        save(vd/'direction.json',d)
        cut=[{'theme':'V001/S2','what':'a burning church','kind':'creative','label':'excluded_theme','avoid':['burning church']}]
        with mock.patch.object(core,'excluded_themes',return_value=cut):
            iss=core.direction_facts(self.run,1)['issues']
            self.assertTrue(any(x.startswith('treatment_T1_names_what_a_content_review_rules_out') for x in iss),iss)
            d['content_context']=[{'where':'treatment T1','theme':'excluded_theme:V001/S2',
                                   'context':'the bell is a town bell heard far off, no church and no fire is shown'}]
            save(vd/'direction.json',d)
            self.assertFalse([x for x in core.direction_facts(self.run,1)['issues'] if 'rules_out' in x])


    def test_a_drawing_says_what_the_narration_says_in_the_locked_look(self):
        # An animated count lands on a figure its shot's lines say (or says why not); its words pass the picture rules;
        # its colours are read against the locked palette; a render no longer of its spec is stale.
        vd=self.write_plan()
        self.shots_for_plan()
        cli('style-lock','--run',self.run,'--video',1,'--style-prompt','painterly, soft edges','--departs-when','photorealistic, flat vector','--palette','#2B1D14,#B0302A',
            '--why','a palette for the drawings of this test')
        sc=json.loads((vd/'script.json').read_text(encoding='utf-8'))
        sc['lines'][0]['text']='Twenty-seven agents existed only on paper, and every one of them was believed for years.'
        save(vd/'script.json',sc)
        core=self.load_core()
        dd=self.run/'60-visuals/video-01/drawings'; dd.mkdir(parents=True)
        spec={'canvas':'1920x1080','fps':30,'dur_s':1,'shot':'S1','elements':[
              {'id':'num','type':'counter','at':[0.6,0.6],'from':0,'to':27,'suffix':' AGENTS','size':0.12,'fill':'#B0302A',
               'in':{'start_s':0.0,'dur_s':0.3,'ease':'linear'}},
              {'id':'lab','type':'text','at':[0.3,0.3],'text':'ON PAPER ONLY','size':0.1,'fill':'#2B1D14'}]}
        save(dd/'D01.json',spec)
        iss,warn=core.drawing_facts(self.run,1)
        self.assertEqual((iss,warn),([],[]))
        spec['elements'][0]['to']=30
        save(dd/'D01.json',spec)
        iss,_=core.drawing_facts(self.run,1)
        # the line says 27 (and 'every one of them': 1); the count lands on 30
        self.assertTrue(any(x.startswith('drawing_D01_counts_to_30_but_shot_S1_says:1,27') for x in iss),iss)
        spec['counter_note']='thirty is the total the next shot names, shown early on purpose'
        save(dd/'D01.json',spec)
        self.assertFalse([x for x in core.drawing_facts(self.run,1)[0] if 'counts_to' in x])
        spec['elements'][1]['text']='BLOOD ON THE MAP'
        spec['elements'][1]['fill']='#00FF00'
        save(dd/'D01.json',spec)
        iss,warn=core.drawing_facts(self.run,1)
        self.assertIn('drawing_D01_words_content_flag_unanswered:injury_gore_distress',iss)
        self.assertTrue(any('away from the locked palette' in w and '#00FF00' in w for w in warn),warn)


    def test_parts_follow_the_story(self):
        core=self.load_core()
        lines=[{'id':f'L{i:03}','text':('word '*30).strip()+'.'} for i in range(1,61)]   # 151 characters a line
        beats=[{'id':'B1','line_start':1,'line_end':8},{'id':'B2','line_start':9,'line_end':14},
               {'id':'B3','line_start':15,'line_end':54},{'id':'B4','line_start':55,'line_end':60}]
        lines[33]['pause_after_s']=2.0                     # inside the long beat, the story already breathes after L034
        parts=core.chunks_for_beats(lines,beats,3500,10000)
        ends=[p['line_end'] for p in parts]
        self.assertEqual(parts[0]['beats'],['B1','B2'])                       # short beats together
        self.assertIn(34,ends)                                                 # a long beat split where it breathes
        self.assertTrue(all(e in (8,14,54,60) or 15<=e<54 for e in ends))
        self.assertEqual(ends[-1],60)
        self.assertTrue(all(len(p['text'])<=10000 for p in parts))
        self.assertEqual(sum(p['line_end']-p['line_start']+1 for p in parts),60)  # every line once, none split
        self.assertEqual([p['line_start'] for p in parts][1:],[e+1 for e in ends[:-1]])
        joins_between_beats=[e for e in ends[:-1] if e in (8,14,54)]
        self.assertTrue(joins_between_beats)                                   # joins where the story turns
        fallback=core.chunks_for_beats(lines,[{'id':'B1','line_start':1,'line_end':30}],3500,10000)
        self.assertEqual(fallback[-1]['line_end'],60)                          # a beat map that misses lines: plain packing

    def test_markup_tags_and_pronunciation(self):
        core=self.load_core()
        rows=[{'id':'L001','text':'He waited. <break time="1.5s" />'},
              {'id':'L002','text':'{softly} Nobody moved.'},
              {'id':'L003','text':'(whispers) Nobody moved.'},
              {'id':'L004','text':'They *ran* for it.'},
              {'id':'L005','text':'[note: check this date] It was June.'},
              {'id':'L006','text':'[whispering, shouting] Get down.'},
              {'id':'L007','text':'[calm] [excited] Here it comes.'},
              {'id':'L008','text':'[softly] [slowly] Here it comes.'},
              {'id':'L009','text':'The town of /həˈɡɑːruː/ waited.'},
              {'id':'L010','text':'A plain line (with an aside) and [curious] a tag.'}]
        issues,warnings=core.script_markup(rows)
        for x in ('ssml_markup_not_supported_by_eleven_v4:L001','curly_brace_markup:L002',
                  'stage_direction_in_parentheses:L003:(whispers)','asterisk_markup:L004',
                  'editorial_note_in_spoken_text:L005:[note: check this date]','pronunciation_markup_in_script_text:L009'):
            self.assertIn(x,issues)
        self.assertTrue(any(x.startswith('contradictory_delivery:L006:volume') for x in issues))
        self.assertTrue(any(x.startswith('contradictory_delivery:L007:energy') for x in issues))
        self.assertFalse([x for x in issues if ':L008' in x or ':L010' in x])     # compatible, and a real aside
        self.assertTrue(any(w.startswith('L008') for w in warnings))              # stacked: one bracket is clearer
        # Pronunciation lives in its own file and changes only what is sent.
        self.write_plan()
        vd=self.run/'40-plans/video-01'
        lines=[{'id':'L001','text':'[curious] Near Hagaru, and Yudam-ni.'}]
        save(vd/'pronunciation.json',{'terms':[
            {'term':'Hagaru','say':'/həˈɡɑːruː/','how':'ipa','confidence':'confirmed','source':'an official romanisation table'},
            {'term':'Yudam-ni','say':'Yoo-dahm-nee','how':'respell','confidence':'uncertain'},
            {'term':'Koto-ri','say':'koto','how':'ipa','confidence':'likely'}]})
        pf=core.pronunciation_facts(self.run,1,lines)
        self.assertIn('pronunciation_Koto-ri_ipa_goes_between_slashes',pf['issues'])
        self.assertIn('pronunciation_Koto-ri_needs_its_source',pf['issues'])
        self.assertTrue(any('uncertain' in w and 'Yudam-ni' in w for w in pf['warnings']))
        self.assertTrue(any('Koto-ri' in w and 'not in the script' in w for w in pf['warnings']))
        sent=core.tts_text(lines[0]['text'],pf['terms'])
        self.assertEqual(sent,'[curious] Near "/həˈɡɑːruː/", and Yoo-dahm-nee.')
        # A kept tag says why under "Delivery and tags"; plan-check refuses one that doesn't.
        script=json.loads((vd/'script.json').read_text()); script['lines'][3]['text']='[thoughtful] '+script['lines'][3]['text']
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('tag_L004_not_explained_under_delivery_and_tags',res['issues'])
        self.assertTrue(any('pronunciation_Koto-ri' in x for x in res['issues']))

    def test_pace_model_counts_pauses_once(self):
        # Two reference narrators with known speech and pauses: 4 words in 1 s of speech, then 0.6 s of silence.
        for vid in ('V001','V002'):
            m=self.run/'10-media'/vid; m.mkdir(parents=True,exist_ok=True)
            segs,t=[],0.0
            for k in range(120):
                ws=[{'start_s':round(t+0.25*i,3),'end_s':round(t+0.25*i+0.22,3),'text':f' w{k}{i}'} for i in range(4)]
                segs.append({'start_s':round(t,3),'end_s':round(t+1.0,3),'text':' '.join(w['text'] for w in ws),'words':ws})
                t+=1.6
            save(m/'transcript.json',{'status':'transcribed','segments':segs})
            (m/'transcript.txt').write_text('\n'.join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}" for s in segs),encoding='utf-8')
        lock=cli('length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
                 '--story-form','historical narrative','--refs','V001,V002')
        pp=lock['pace_profile']
        self.assertEqual(pp['active_wpm'],240)                         # 4 words a second while speaking
        self.assertAlmostEqual(pp['overall_wpm'],150,delta=1)           # 4 words every 1.6 s, pauses included
        self.assertEqual(lock['target_words_speech_only'],round(600*240/60))
        self.assertAlmostEqual(lock['target_words'],600*pp['overall_wpm']/60,delta=2)   # the budget counts the pauses once
        self.assertLess(lock['target_words'],lock['target_words_speech_only'])

    def test_silence_cannot_pad_a_short_script(self):
        vd=self.write_plan()
        script=json.loads((vd/'script.json').read_text())
        script['pace_wpm']=200                                          # the same words now forecast far short of 600 s
        save(vd/'script.json',script)
        self.assertIn('script_forecast_misses_locked_length_by_over_8pct',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        for l in script['lines'][:-1]:
            l.update({'pause_after_s':3.2,'pause_via':'edit'})
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        for need in ('story_purpose','picture','sound'):                           # every hold says what it is for,
            self.assertIn(f'pause_L001_needs_its_{need}',res['issues'])            # what is seen and what is heard
        for l in script['lines'][:-1]:
            l.update(HELD)
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('holds_changed_after_the_script_read') for x in res['issues']))   # the reader never saw them
        self.assertGreater(res['holds']['runtime_carried_by_holds_s'],100)
        self.assertTrue(any(x.startswith('runtime_reached_with_held_silence') for x in res['issues']))
        # The packet puts each silence in front of the reader as a viewer would hear it: the whole of it, and no
        # other film's pause length to measure it against. The cold reader gets the words and the silences only:
        # no picture or sound plan, no house rules, in a folder outside the run.
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind','script')
        text=Path(packet['packet']).read_text(encoding='utf-8')
        self.assertIn('(silence after this line: about 3.8 s in all)',text)
        self.assertNotIn(HELD['pause_picture'],text)
        self.assertNotIn('House rules',text)
        self.assertNotIn(str(self.run),str(packet['packet']))
        # no priming (the user, 2026-11-22): no count or sum of the silences, no baseline gap, no picture assumed
        for primer in ('Silences in this script','own gap between two lines','picture stays','the voice stops'):
            self.assertNotIn(primer,text)
        self.assertNotIn('longest pause',text)
        # A reader who saw every hold does not make silence a way to reach the length: still blocked.
        self.review('script',[{'id':'F1','severity':'minor','lines':['L002'],'problem':'the holds feel long here'}],
                    {'F1':{'action':'kept','note':'the reader saw every hold and we keep them'}})
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('runtime_reached_with_held_silence') for x in res['issues']),res['issues'])
        self.assertFalse(any(x.startswith('holds_changed') for x in res['issues']))
        # The whole-silence form is no way round it.
        for l in script['lines'][:-1]:
            l.pop('pause_after_s'); l['pause_total_s']=3.8
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('runtime_reached_with_held_silence') for x in res['issues']))
        # The words reach the length again: the silences no longer carry it.
        script['pace_wpm']=145
        for l in script['lines'][:-1]:
            l.pop('pause_total_s'); [l.pop(k) for k in HELD]; l.pop('pause_via')
        save(vd/'script.json',script)
        self.assertFalse([x for x in cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
                          if x.startswith('runtime_reached')])

    def test_hold_changes_after_the_read_add_up(self):
        vd=self.write_plan(review_script=False)
        script=json.loads((vd/'script.json').read_text())
        for k in [1]+list(range(20,35))+[49]:                   # L002 (the opening), L021-L035, L050 (the ending)
            script['lines'][k].update({'pause_after_s':1.2,'pause_via':'edit',**HELD})
        save(vd/'script.json',script)
        self.review_script()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        # A small hold tweak after a read passes with a warning.
        script['lines'][24]['pause_after_s']=3.2                                    # L025: the middle of the film
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1)
        self.assertTrue(any('held silences changed after the last read' in w for w in res['warnings']))
        # The same 2 s in the opening (the hook), or a closing hold, is read again whatever its size.
        script['lines'][24]['pause_after_s']=1.2; script['lines'][1]['pause_after_s']=3.2
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('holds_changed_in_a_key_moment') and 'L002' in x and 'the opening' in x
                            for x in res['issues']))
        script['lines'][1]['pause_after_s']=1.2; script['lines'][49]['pause_after_s']=4.0
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any('L050' in x and 'the ending' in x for x in res['issues']))
        # A beat the map marks as a key moment (a reveal) counts like the hook and the ending.
        script['lines'][49]['pause_after_s']=1.2; script['lines'][24]['pause_after_s']=3.2
        save(vd/'script.json',script)
        bm=json.loads((vd/'beat-map.json').read_text()); bm['beats'][2]['key_moment']='the reveal'
        save(vd/'beat-map.json',bm)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any('L025' in x and 'the reveal' in x for x in res['issues']))
        bm['beats'][2].pop('key_moment'); save(vd/'beat-map.json',bm)
        # Small edits add up from the last read: fifteen 0.4 s nudges (none half a second) are 6 s of silence moved.
        script['lines'][24]['pause_after_s']=1.2
        for l in script['lines'][20:35]:
            l['pause_after_s']=1.6
        save(vd/'script.json',script)
        res=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertTrue(any(x.startswith('holds_changed_after_the_script_read:6s') for x in res['issues']))

    def test_every_line_heard_and_no_tag_read_aloud(self):
        core=self.load_core()
        vd=self.write_plan()
        lines=[{'id':'L001','text':'Twelve divisions came south that night.'},
               {'id':'L002','text':'[softly] Nobody in the valley knew yet.'},
               {'id':'L003','text':'The column is coming.'},
               {'id':'L004','text':'Two hundred and forty men held the hill.'},
               {'id':'L005','text':'By morning the road was quiet again.'}]
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        d=self.run/'50-audio/video-01'; (d/'whisper').mkdir(parents=True)
        heard=[['12','divisions','came','south','that','night.'],['Softly,','nobody','in','the','valley','knew','yet.'],
               [],['240','men','held','the','hill.'],['By','morning','the','road','was','quiet','again.']]
        t,segs=0.3,[]
        for ws_ in heard:          # what the long Whisper pass heard: digits, a tag read aloud, one line missing
            s0,ws=t,[]
            for w in ws_:
                ws.append({'start_s':round(t,3),'end_s':round(t+0.22,3),'text':' '+w}); t+=0.27
            if ws:
                segs.append({'start_s':round(s0,3),'end_s':round(t-0.05,3),'text':' '.join(ws_),'words':ws})
            t+=0.4 if ws_ else 1.2
        part=d/'part-001.mp3'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=150:sample_rate=16000',
                        '-t',f'{t+0.3:.2f}','-c:a','libmp3lame','-b:a','32k',str(part)],check=True)
        save(d/'whisper/part-001.json',{'status':'transcribed','model':'medium','segments':segs})
        (d/'whisper/part-001.txt').write_text('\n'.join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}" for s in segs),encoding='utf-8')
        text='\n'.join(r['text'] for r in lines)
        save(d/'manifest.json',{'model_id':'eleven_v4','voice_id':'TESTID','language':'en','status':'complete','finished_parts':[1],
                                'chunks':[{'id':1,'line_start':1,'line_end':5,'file':'part-001.mp3','characters':len(text),
                                           'text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}]})
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(part),str(d/'narration.wav')],check=True)
        found={'L003':False}
        def fake_transcribe(path,outpath,*a):          # the re-hearing of one short window
            lid=Path(outpath).stem.split('-')[-1]
            ws=[{'start_s':0.3+0.27*i,'end_s':0.52+0.27*i,'text':' '+w} for i,w in enumerate(
                'the column is coming'.split())] if found.get(lid) else []
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[{'start_s':0.3,'end_s':1.4,'text':'x','words':ws}] if ws else []})
            Path(outpath).with_suffix('.txt').write_text('',encoding='utf-8')
            return 1
        def measure(*extra):
            with mock.patch.object(core,'transcribe',side_effect=fake_transcribe):
                return self.core_call(core,'narration-measure','--run',self.run,'--video',1,'--no-delivery',*extra)
        code,out=measure()
        self.assertEqual(code,2)
        self.assertEqual(out['unheard_lines'],['L003'])                                  # digits and words: the same numbers
        self.assertEqual([t['line'] for t in out['tags_read_aloud']],['L002'])          # 'softly' said, not performed
        self.assertTrue(any(r['line']=='L003' and not r['found'] for r in out['rechecked_lines']))
        issues=cli('audio-check','--run',self.run,'--video',1,expected=2)['issues']
        self.assertIn('narration_line_not_heard:L003',issues)
        self.assertIn('narration_tag_read_aloud:L002:[softly]',issues)
        found['L003']=True                                                                # heard on its own window
        (d/'whisper/recheck-L003.json').unlink()          # (the fake transcript changes; real audio would not)
        code,out=measure()
        self.assertEqual(out['unheard_lines'],[])
        code,out=measure('--confirm','L002','--reason','fine')
        self.assertEqual(code,2)                                                          # a confirmation says who listened
        code,out=measure('--confirm','L002','--reason','the user listened at 00:02 and heard the tag performed')
        self.assertEqual((code,out['tags_read_aloud']),(0,[]))

    def test_words_stacked_at_one_instant_are_not_heard(self):
        # Whisper sometimes stacks a line's words at one instant somewhere else (no length each): that is no time, so
        # the line is listened to again on a window between real times, and found there (2026-11-23, part 4, L065/L066).
        core=self.load_core()
        vd=self.write_plan()
        lines=[{'id':'L001','text':'Twelve divisions came south that night.'},
               {'id':'L002','text':'What would a careful spy do then?'},
               {'id':'L003','text':'By morning the road was quiet again.'}]
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        d=self.run/'50-audio/video-01'; (d/'whisper').mkdir(parents=True)
        def run_of(words, t0, step=0.27, length=0.22):
            return [{'start_s':round(t0+step*i,3),'end_s':round(t0+step*i+length,3),'text':' '+w} for i,w in enumerate(words)]
        a=run_of('12 divisions came south that night.'.split(),0.3)
        b=[{'start_s':5.0,'end_s':5.0,'text':' '+w} for w in 'What would a careful'.split()]   # stacked, 3 s late
        c=run_of('By morning the road was quiet again.'.split(),5.1)
        segs=[{'start_s':x[0]['start_s'],'end_s':x[-1]['end_s'],'text':' '.join(w['text'] for w in x),'words':x} for x in (a,b,c)]
        part=d/'part-001.mp3'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=150:sample_rate=16000',
                        '-t','7.5','-c:a','libmp3lame','-b:a','32k',str(part)],check=True)
        save(d/'whisper/part-001.json',{'status':'transcribed','model':'medium','segments':segs})
        (d/'whisper/part-001.txt').write_text(chr(10).join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}" for s in segs),encoding='utf-8')
        text=chr(10).join(r['text'] for r in lines)
        save(d/'manifest.json',{'model_id':'eleven_v4','voice_id':'TESTID','language':'en','status':'complete','finished_parts':[1],
                                'chunks':[{'id':1,'line_start':1,'line_end':3,'file':'part-001.mp3','characters':len(text),
                                           'text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}]})
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(part),str(d/'narration.wav')],check=True)
        windows=[]
        def fake_transcribe(path,outpath,*a):           # the second listen hears the line where it really is
            windows.append(Path(outpath).stem)
            ws=[{'start_s':0.4+0.27*i,'end_s':0.62+0.27*i,'text':' '+w} for i,w in enumerate('What would a careful spy do then'.split())]
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[{'start_s':0.4,'end_s':2.3,'text':'x','words':ws}]})
            Path(outpath).with_suffix('.txt').write_text('',encoding='utf-8')
            return 1
        with mock.patch.object(core,'transcribe',side_effect=fake_transcribe):
            code,out=self.core_call(core,'narration-measure','--run',self.run,'--video',1,'--no-delivery')
        self.assertIn('recheck-L002',windows)                                   # stacked words were not taken as heard
        rec=next(r for r in out['rechecked_lines'] if r['line']=='L002')
        self.assertTrue(rec['found'])
        self.assertLess(rec['window_s'][0],2.2)                                 # from the end of L001's real words
        self.assertEqual(out['unheard_lines'],[])

    def test_capcut_narration_track_must_be_whole(self):
        core=self.load_core()
        f=self.home/'narration-edit.wav'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=200:sample_rate=16000',
                        '-t','10','-c:a','pcm_s16le',str(f)],check=True)
        expect={'file':str(f),'sha256':core.file_sha256(f),'duration_s':10.0}
        ok=[{'kind':'narration','file':str(f).replace('\\','/'),'start_s':0,'end_s':10,'source_start_s':0,'source_end_s':10,'speed':1}]
        self.assertEqual(core.narration_track_issues(self.run,ok,expect),[])
        fast=[dict(ok[0],end_s=9.709,speed=1.03)]
        self.assertTrue(any('speed_1.03_not_1' in x for x in core.narration_track_issues(self.run,fast,expect)))
        trimmed=[dict(ok[0],end_s=8,source_end_s=8)]
        self.assertIn('narration_trimmed_2.0s_missing_at_the_end',core.narration_track_issues(self.run,trimmed,expect))
        cut=[dict(ok[0],end_s=4,source_end_s=4),dict(ok[0],start_s=4,end_s=9,source_start_s=5,source_end_s=10)]
        self.assertTrue(any(x.startswith('narration_cut_1.0s_missing') for x in core.narration_track_issues(self.run,cut,expect)))
        self.assertIn('narration_track_missing',core.narration_track_issues(self.run,[],expect))
        self.assertIn('narration_track_1_speed_not_recorded',core.narration_track_issues(self.run,[{k:v for k,v in ok[0].items() if k!='speed'}],expect))
        # Read straight from a CapCut project: its own audio segment, its own speed.
        draft=self.home/'draft'; draft.mkdir()
        content={'tracks':[{'type':'audio','id':'t1','segments':[{'material_id':'m1','extra_material_refs':['s1'],
                  'source_timerange':{'start':0,'duration':10000000},'target_timerange':{'start':0,'duration':10000000},'speed':1}]}],
                 'materials':{'audios':[{'id':'m1','path':str(f).replace('\\','/')}],'speeds':[{'id':'s1','speed':1,'mode':0}]}}
        save(draft/'draft_content.json',content)
        segs=core.capcut_audio_segments(draft)
        self.assertEqual(core.narration_track_issues(self.run,segs,expect),[])
        content['tracks'][0]['segments'][0].update({'speed':1.05,'target_timerange':{'start':0,'duration':9523810}})
        save(draft/'draft_content.json',content)
        self.assertTrue(any('speed_1.05' in x for x in core.narration_track_issues(self.run,core.capcut_audio_segments(draft),expect)))
        raw=f.read_bytes(); f.write_bytes(raw[:150000]+b'\0'*2000+raw[152000:])   # the approved file changed after the retime
        self.assertIn('narration_file_changed_since_retime_shots',core.narration_track_issues(self.run,ok,expect))

    def test_export_must_carry_the_approved_narration(self):
        core=self.load_core()
        av=core._av()
        import numpy as np, soundfile as sf
        rng=np.random.default_rng(7); sr=16000; y=[]
        while len(y)<sr*48:              # speech-like: bursts of sound and short silences
            n=int(sr*rng.uniform(0.08,0.3)); g=int(sr*rng.uniform(0.04,0.45))
            y+=list(rng.normal(0,0.2,n)*np.hanning(n))+[0.0]*g
        nar=np.array(y[:sr*48],dtype='float32')
        bed=0.02*np.sin(2*np.pi*110*np.arange(len(nar))/sr).astype('float32')
        def wav(name,sig):
            p=self.home/name; sf.write(str(p),sig,sr); return p
        n_p=wav('narr.wav',nar)
        same=av.narration_in_mix(wav('mix.wav',nar+bed),n_p,windows=8,win_s=6,search_s=1.5)
        self.assertEqual(same['weak_windows'],[]); self.assertLess(abs(same['median_lag_s']),0.05)
        self.assertLess(same['lag_spread_s'],0.1); self.assertLess(same['bed_level_rel_speech_db'],-8)
        fast=np.interp(np.arange(0,len(nar),1.04),np.arange(len(nar)),nar).astype('float32')   # sped up 4%
        sped=av.narration_in_mix(wav('fast.wav',fast[:len(fast)]+bed[:len(fast)]),n_p,windows=8,win_s=6,search_s=1.5)
        self.assertTrue(sped['weak_windows'] or sped['lag_spread_s']>0.25)
        cut=np.concatenate([nar[:sr*20],nar[sr*24:]])                                          # four seconds missing
        gone=av.narration_in_mix(wav('cut.wav',cut+bed[:len(cut)]),n_p,windows=8,win_s=6,search_s=1.5)
        self.assertTrue(gone['weak_windows'] or gone['lag_spread_s']>0.25)
        # export-check: the export's own sound against the edit plan's narration.
        self.write_plan()
        save(self.run/'70-edit/video-01/edit-plan.json',{'narration_for_edit':{'file':str(n_p),'sha256':core.file_sha256(n_p),
                                                                              'duration_s':48.0}})
        def export(name,audio):
            p=self.home/name
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=black:s=320x180:r=10',
                            '-i',str(audio),'-shortest','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(p)],check=True)
            return p
        good=core.export_facts(self.run,1,export('good.mp4',self.home/'mix.wav'))
        self.assertFalse([x for x in good['issues'] if x.startswith('export_narration')],good.get('narration_in_export'))
        bad=core.export_facts(self.run,1,export('bad.mp4',self.home/'cut.wav'))
        self.assertTrue([x for x in bad['issues'] if x.startswith('export_narration')],bad.get('narration_in_export'))

    def test_cost_preflight_and_voice_design_check(self):
        core=self.load_core()
        self.write_plan()
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        calls=[]
        def fake(available,per_char):
            def f(req,timeout=None):
                calls.append(req.full_url)
                if req.full_url.endswith('/v1/user/subscription'):
                    return Reply(json.dumps({'character_limit':available,'character_count':0}).encode())
                if req.full_url.endswith('/v1/models'):
                    return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':per_char}},
                                             {'model_id':'eleven_v4_turbo','model_rates':{'character_cost_multiplier':0.5}}]).encode())
                raise AssertionError('a billed request was attempted: '+req.full_url)
            return f
        env={'ELEVENLABS_API_KEY':'test-not-a-real-key','ELEVEN_API_KEY':''}
        with mock.patch.dict(os.environ,env), mock.patch.object(core.urllib.request,'urlopen',side_effect=fake(4000,1.0)), \
                mock.patch('sys.stdout',new_callable=io.StringIO):
            with self.assertRaises(SystemExit):        # 4,000 characters at 1 credit, x1.15: more than 4,000 left
                core.credit_preflight(self.run,'k','eleven_v4',4000,1.15)
            ok=core.credit_preflight(self.run,'k','eleven_v4_turbo',4000,1.15)          # half price: fits
        self.assertEqual((ok['credits_per_character'],ok['expected_credits'],ok['required_available']),(0.5,2000,2300))
        self.assertFalse([c for c in calls if 'text-to-speech' in c])
        rates=json.loads((self.run/'logs/elevenlabs-models.json').read_text())
        self.assertIn('eleven_v4',rates['models'])
        # What the account was really billed, from the ledger: the measured ratio beside ElevenLabs' own figure.
        for d_,c in ((400,1000),(410,1000)):
            core.ledger_add(self.run,{'kind':'tts','model_id':'eleven_v4','ok':True,'delta':d_,'characters':c})
        self.assertEqual(core.measured_cost_ratio(self.run,'eleven_v4'),(0.405,2))
        # Voice Design is billed: without --execute it is only priced; with it, a short balance stops it before any call.
        calls.clear()
        args=argparse.Namespace(run=str(self.run),video=1,count=3,search='',design=3,design_description='a calm older narrator, warm and dry',
                                design_text='x'*400,execute=False,credit_safety_factor=1.15,keep_credits=0,
                                whisper_model='medium',device='cpu',compute_type='int8')
        with mock.patch.dict(os.environ,env), mock.patch.object(core.urllib.request,'urlopen',side_effect=fake(4000,1.0)), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as out:
            core.cmd_voice_candidates(args)
        priced=json.loads(out.getvalue())
        self.assertEqual((priced['mode'],priced['voice_design']['expected_credits'],priced['voice_design']['reserve_credits']),
                         ('dry_run_no_charges',400,1200))
        self.assertEqual(calls,[])
        args.execute=True
        with mock.patch.dict(os.environ,env), mock.patch.object(core.urllib.request,'urlopen',side_effect=fake(1000,1.0)), \
                mock.patch('sys.stdout',new_callable=io.StringIO) as out:
            with self.assertRaises(SystemExit):
                core.cmd_voice_candidates(args)
        self.assertIn('nothing was sent',json.loads(out.getvalue())['error'])
        self.assertFalse([c for c in calls if 'text-to-voice' in c])

    def test_narration_trial_plan_changes_one_thing_at_a_time(self):
        core=self.load_core()
        vd=self.write_plan()
        cli('voice-pick','--run',self.run,'--video',1,'--voice-id','VOICEA','--settings','{"stability":1.0,"similarity_boost":0.7}',
            '--reason','the measured, even narrator the treatment describes')
        plan={'id':'trial-01','passages':[{'id':'P1','moment':'opening','lines':'L001-L003'},
                                         {'id':'P2','moment':'turning point','lines':'L041-L042'}],
              'variants':[{'id':'A'},{'id':'B','stability':0.5},{'id':'C','stability':0.5,'tags':'none'}],
              'runs':[['P1','A'],['P1','B'],['P1','C'],['P2','A']],
              'questions':[{'id':'Q1','asks':'does lower stability widen the delivery here','compare':[['P1','A'],['P1','C']]}]}
        pf=self.home/'trial.json'; save(pf,plan)
        bad=cli('narration-trial','--run',self.run,'--video',1,'--plan',pf,expected=2)['details']
        self.assertIn('question_Q1_changes_2_things_at_once:stability,tags',bad)
        self.assertIn('run_P2_A_answers_no_question',bad)
        self.assertTrue(any(x.startswith('trial_needs_its_budget') for x in bad))          # the user's cap, named
        self.assertIn('passage_P1_says_its_intended_delivery',bad)
        plan['budget']={'id':'calibration-test','max_credits':5000}
        for p_ in plan['passages']:
            p_['intended_delivery']='curious and close, like telling a friend'
        plan['questions']=[{'id':'Q1','asks':'does lower stability widen the delivery here','compare':[['P1','A'],['P1','B']]},
                           {'id':'Q2','asks':'do the tags help or does the writing carry it','compare':[['P1','B'],['P1','C']]},
                           {'id':'Q3','asks':'does the voice stay the same narrator at the turn','compare':[['P1','A'],['P2','A']]}]
        save(pf,plan)
        dry=cli('narration-trial','--run',self.run,'--video',1,'--plan',pf)
        self.assertEqual((dry['mode'],dry['runs'],[q['varies'] for q in dry['questions']]),
                         ('dry_run_no_charges',4,[['stability'],['tags'],['passage']]))
        self.assertFalse((self.run/'60-voice/video-01/trials').exists())        # nothing recorded without --execute
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        mp3=self.fake_mp3().read_bytes(); used={'n':0}
        def fake(req,timeout=None):
            if req.full_url.endswith('/v1/user/subscription'):
                return Reply(json.dumps({'character_limit':20000,'character_count':used['n']}).encode())
            if req.full_url.endswith('/v1/models'):
                return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':1.0}}]).encode())
            used['n']+=len(json.loads(req.data.decode())['text'])
            return Reply(mp3)
        def fake_transcribe(path,outpath,*a):
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[]})
            Path(outpath).with_suffix('.txt').write_text('',encoding='utf-8')
            return 0
        with mock.patch.object(core,'transcribe',side_effect=fake_transcribe):
            code,out=self.core_call(core,'narration-trial','--run',self.run,'--video',1,'--plan',pf,'--execute',fake=fake)
        self.assertEqual(code,0,out)
        tdir=self.run/'60-voice/video-01/trials/trial-01'
        self.assertEqual(sorted(p.name for p in tdir.glob('*.mp3')),['P1-A.mp3','P1-B.mp3','P1-C.mp3','P2-A.mp3'])
        self.assertIn('Only stability changes',(tdir/'answer-key.md').read_text(encoding='utf-8'))
        rep=json.loads((tdir/'report.json').read_text())
        self.assertEqual(rep['runs']['P1|C']['variant']['tags'],'none')
        rows=[json.loads(x) for x in (self.run/'logs/elevenlabs-ledger.jsonl').read_text().splitlines()]
        self.assertEqual(sum(1 for x in rows if x['kind']=='trial' and x['phase']=='done'),4)
        self.assertEqual(sum(1 for x in rows if x['kind']=='trial' and x['phase']=='pending'),4)   # on record before sending
        # The blind set: neutral labels, a guide that names no setting, the key one folder up.
        guide=(tdir/'listening/listening-guide.md').read_text(encoding='utf-8')
        self.assertEqual(sorted(p.name for p in (tdir/'listening').glob('*.mp3')),
                         ['Q1-A.mp3','Q1-B.mp3','Q2-A.mp3','Q2-B.mp3','Q3-A.mp3','Q3-B.mp3'])
        for leak in ('stability','P1-A','P1-B','tags','0.5'):
            self.assertNotIn(leak,guide)
        key=json.loads((tdir/'answer-key.json').read_text())
        self.assertEqual({k['run'] for k in key['labels'] if k['question']=='Q1'},{'P1-A','P1-B'})
        self.assertTrue(key['same_recording'])                       # P1-A and P1-B are each used by two questions

    def test_trial_budget_holds_across_crashes_and_resumes(self):
        core=self.load_core()
        self.write_plan()
        cli('voice-pick','--run',self.run,'--video',1,'--voice-id','VOICEA','--settings','{"stability":1.0,"similarity_boost":0.7}',
            '--reason','the measured, even narrator the treatment describes')
        n=len('\n'.join(json.loads((self.run/'40-plans/video-01/script.json').read_text())['lines'][i]['text'] for i in (0,1)))
        plan={'id':'trial-02','budget':{'id':'cal-test','max_credits':3*n+1000},
              'passages':[{'id':'P1','moment':'opening','lines':'L001-L002','intended_delivery':'curious, close, unhurried'},
                          {'id':'P2','moment':'explaining','lines':'L021-L022','intended_delivery':'plain and clear, never read'}],
              'variants':[{'id':'A'},{'id':'B','stability':0.5},{'id':'C','context':'neighbours'}],
              'runs':[['P1','A'],['P1','B'],['P2','A'],['P2','C']],
              'questions':[{'id':'Q1','asks':'does lower stability widen the delivery here','compare':[['P1','A'],['P1','B']]},
                           {'id':'Q2','asks':'does the neighbouring context change how the part begins','compare':[['P2','A'],['P2','C']]}]}
        pf=self.home/'trial-02.json'; save(pf,plan)
        dry=cli('narration-trial','--run',self.run,'--video',1,'--plan',pf)
        self.assertGreater(dry['context_characters_to_record'],500)                   # the context fields are priced too
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        mp3=self.fake_mp3().read_bytes()
        st={'used':0,'posts':[],'history':[],'history_audio':0,'crash_next':False}
        def fake(req,timeout=None):
            url=req.full_url
            if url.endswith('/v1/user/subscription'):
                return Reply(json.dumps({'character_limit':20000,'character_count':st['used']}).encode())
            if url.endswith('/v1/models'):
                return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':1.0}}]).encode())
            if '/v1/history' in url:
                if url.endswith('/audio'):
                    st['history_audio']+=1; return Reply(mp3)
                return Reply(json.dumps({'history':st['history']}).encode())
            body=json.loads(req.data.decode()); st['posts'].append(body); st['used']+=len(body['text'])
            if st['crash_next']:                                       # the power goes while the request is out
                st['crash_next']=False
                st['history'].append({'history_item_id':'H1','text':body['text'],'model_id':body['model_id'],
                                      'date_unix':int(time.time()),'character_count_change_from':0,
                                      'character_count_change_to':len(body['text'])})
                raise KeyboardInterrupt
            r=Reply(mp3); r.headers={'character-cost':str(len(body['text'])),'request-id':f'req{len(st["posts"])}'}
            return r
        words=[{'start_s':round(0.1+0.3*i,2),'end_s':round(0.35+0.3*i,2),'text':' w'} for i in range(6)]
        def good_transcribe(path,outpath,*a):
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[{'start_s':0.1,'end_s':1.9,'text':'w','words':words}]})
            Path(outpath).with_suffix('.txt').write_text('[0.1-1.9] w w w w w w',encoding='utf-8')
            return 1
        ex=['narration-trial','--run',self.run,'--video',1,'--plan',pf,'--execute']
        tdir=self.run/'60-voice/video-01/trials/trial-02'
        # 1. The take arrives and is saved, then the session dies before it is measured.
        with mock.patch.object(core,'transcribe',side_effect=RuntimeError('the session stopped here')):
            code,out=self.core_call(core,*ex,fake=fake)
        self.assertEqual(code,2,out)
        rep=json.loads((tdir/'report.json').read_text())
        self.assertEqual((rep['runs']['P1|A']['measured'],len(st['posts'])),(False,1))
        self.assertEqual(rep['runs']['P1|A']['cost']['character_cost_header'],n)
        # 2. Next session: P1-A is measured without being sent again; then the power goes during P1-B's request,
        #    leaving its pending ledger row and a lock held by a process that no longer exists.
        st['crash_next']=True
        with mock.patch.object(core,'transcribe',side_effect=good_transcribe):
            with self.assertRaises(KeyboardInterrupt):
                self.core_call(core,*ex,fake=fake)
        self.assertEqual(len(st['posts']),2)
        save(tdir/'trial.lock',{'pid':999999,'at':'2026-11-20T00:00:00+00:00'})
        spent,open_=core.budget_spent(self.run,'cal-test')
        self.assertEqual((spent,len(open_)),(2*n,1))                   # the cut-off request counts at its largest charge
        # 3. Resume: P1-B comes from the account history (free, not paid twice), P2-A is recorded, and P2-C (with its
        #    context, at most n+context credits) would pass the cap: it is not sent.
        with mock.patch.object(core,'transcribe',side_effect=good_transcribe):
            code,out=self.core_call(core,*ex,fake=fake)
        self.assertEqual(code,2,out)
        self.assertEqual((out['stopped']['run'],out['stopped']['why']),('P2-C','budget'))
        self.assertEqual((len(st['posts']),st['history_audio']),(3,1))
        rep=json.loads((tdir/'report.json').read_text())
        self.assertTrue(rep['runs']['P1|B']['cost']['recovered_from_history'])
        self.assertTrue(all(rep['runs'][k]['measured'] for k in ('P1|A','P1|B','P2|A')))
        self.assertNotIn('P2|C',rep['runs'])
        self.assertEqual(core.budget_spent(self.run,'cal-test')[0],3*n)
        self.assertEqual(sorted(p.name for p in (tdir/'listening').glob('*.mp3')),['Q1-A.mp3','Q1-B.mp3'])   # Q2 waits
        # 4. Another plan can't raise the cap of a budget already in use.
        plan2={**plan,'id':'trial-03','budget':{'id':'cal-test','max_credits':9000}}; pf2=self.home/'trial-03.json'; save(pf2,plan2)
        self.assertTrue(any('is_registered_with' in x for x in
                            cli('narration-trial','--run',self.run,'--video',1,'--plan',pf2,expected=2)['details']))
        # 5. Nothing recorded drifts: changing a recorded take's request is refused (a new plan id instead).
        plan['variants'][1]['stability']=0.4; save(pf,plan)
        self.assertIn('P1-B',cli('narration-trial','--run',self.run,'--video',1,'--plan',pf,expected=2)['details'])

    def test_trial_repeats_and_a_join_between_parts(self):
        core=self.load_core()
        self.write_plan()
        cli('voice-pick','--run',self.run,'--video',1,'--voice-id','VOICEA','--settings','{"stability":1.0,"similarity_boost":0.7}',
            '--reason','the measured, even narrator the treatment describes')
        plan={'id':'trial-04','budget':{'id':'cal-test-2','max_credits':5000},
              'passages':[{'id':'J1','moment':'end of a part','lines':'L009-L010','intended_delivery':'a beat closing quietly'},
                          {'id':'J2','moment':'start of the next','lines':'L011-L012','intended_delivery':'a new beat, fresh energy'}],
              'variants':[{'id':'A'},{'id':'A2'},{'id':'C','context':'neighbours'}],
              'runs':[['J1','A'],['J2','A'],['J1','C'],['J2','C'],['J1','A2']],
              'questions':[{'id':'Q1','asks':'how much do two identical requests differ at the end of a part',
                            'compare':[['J1','A'],['J1','A2']],'repeat':True},
                           {'id':'Q9','asks':'a repeat that is not one is refused before anything is priced',
                            'compare':[['J1','A'],['J1','C']],'repeat':True}],
              'joins':[{'id':'Q2','parts':['J1','J2'],'compare':['A','C'],
                        'asks':'does the context make the join between two parts sound like one telling'}]}
        pf=self.home/'trial-04.json'; save(pf,plan)
        bad=cli('narration-trial','--run',self.run,'--video',1,'--plan',pf,expected=2)['details']
        self.assertIn('question_Q9_is_a_repeat_but_changes:context',bad)
        plan['questions'].pop(); save(pf,plan)
        dry=cli('narration-trial','--run',self.run,'--video',1,'--plan',pf)
        self.assertEqual((dry['questions'][0]['varies'],dry['joins'][0]['varies']),(['nothing: the same request twice'],['context']))
        class Reply(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*a): return False
        mp3=self.fake_mp3().read_bytes(); used={'n':0}
        def fake(req,timeout=None):
            if req.full_url.endswith('/v1/user/subscription'):
                return Reply(json.dumps({'character_limit':20000,'character_count':used['n']}).encode())
            if req.full_url.endswith('/v1/models'):
                return Reply(json.dumps([{'model_id':'eleven_v4','model_rates':{'character_cost_multiplier':1.0}}]).encode())
            n=len(json.loads(req.data.decode())['text']); used['n']+=n
            r=Reply(mp3); r.headers={'character-cost':str(round(n*0.4))}; return r
        words=[{'start_s':round(0.1+0.3*i,2),'end_s':round(0.35+0.3*i,2),'text':' w'} for i in range(6)]
        def good_transcribe(path,outpath,*a):
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[{'start_s':0.1,'end_s':1.9,'text':'w','words':words}]})
            Path(outpath).with_suffix('.txt').write_text('[0.1-1.9] w w w w w w',encoding='utf-8')
            return 1
        with mock.patch.object(core,'transcribe',side_effect=good_transcribe):
            code,out=self.core_call(core,'narration-trial','--run',self.run,'--video',1,'--plan',pf,'--execute',fake=fake)
        self.assertEqual(code,0,out)
        tdir=self.run/'60-voice/video-01/trials/trial-04'
        self.assertEqual(sorted(p.name for p in (tdir/'listening').glob('*.mp3')),['Q1-A.mp3','Q1-B.mp3','Q2-A.mp3','Q2-B.mp3'])
        joined=core.probe(tdir/'listening/Q2-A.mp3')['duration_s']
        self.assertGreater(joined,2*core.probe(tdir/'J1-A.mp3')['duration_s'])            # both parts and the pause between
        key=json.loads((tdir/'answer-key.json').read_text())
        self.assertEqual(sorted(r['variant'] for r in key['joins']),['A','C'])
        self.assertIn('Nothing changes: the same request sent twice',(tdir/'answer-key.md').read_text(encoding='utf-8'))
        # The cost header is the credits (the balance falls by it, later): 40 % here, and the budget counts exactly that.
        rep=json.loads((tdir/'report.json').read_text())
        self.assertEqual(out['credits_billed_this_trial'],sum(round(len(x['sent']['text'])*0.4) for x in rep['runs'].values()))
        self.assertEqual(out['budget_status']['spent'],out['credits_billed_this_trial'])

    def test_references_are_analysed_at_two_frames_per_second(self):
        core=self.load_core()
        st=json.loads((self.run/'state.json').read_text())
        self.assertEqual((st['analysis_fps'],st['analysis_sampler'],st['format']['fps']),(2.0,'pts-v1',30))  # the video stays 30
        # Red until 2.5 s, blue until 4.7 s, then green (30 fps): every sample shows exactly the picture of its own time.
        src=self.home/'sync.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=red:s=64x36:r=30:d=2.5',
                        '-f','lavfi','-i','color=c=blue:s=64x36:r=30:d=2.2','-f','lavfi','-i','color=c=green:s=64x36:r=30:d=1.3',
                        '-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0','-pix_fmt','yuv420p',str(src)],check=True)
        self.add_ref('V004',src,6.0,False)
        self.assertTrue(cli('prepare','--run',self.run,'--ids','V004','--skip-whisper','--reason','the test references carry no narration worth transcribing')['ok'])
        media=self.run/'10-media/V004'
        fi=json.loads((media/'frame-index.json').read_text())
        self.assertEqual([f['t_s'] for f in fi['frames']],[0.0,0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5])
        truth=lambda s:'red' if s<2.5-1e-6 else 'blue' if s<4.7-1e-6 else 'green'
        for f in fi['frames']:
            self.assertEqual(self.colour(media/'sampled-frames'/f['file']),truth(f['t_s']),f)
        # A variable frame rate (10, 24 then 7 fps) and a picture starting 0.37 s after the sound: each frame keeps
        # its own source time (nothing is inferred from frame numbers), and its time on the transcript's clock is
        # that time minus the audio's start, the clock every word time uses.
        vfr=self.home/'vfr.mp4'; mixed=self.home/'vfr-offset.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=red:s=64x36:r=10:d=1.3',
                        '-f','lavfi','-i','color=c=blue:s=64x36:r=24:d=1.1','-f','lavfi','-i','color=c=green:s=64x36:r=7:d=1.6',
                        '-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0','-fps_mode','vfr','-pix_fmt','yuv420p',str(vfr)],check=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=440:sample_rate=16000:d=4.5',
                        '-itsoffset','0.37','-i',str(vfr),'-map','1:v','-map','0:a','-c:v','copy','-c:a','aac',str(mixed)],check=True)
        starts=dict(x.split(',') for x in subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type,start_time',
                    '-of','csv=p=0',str(mixed)],capture_output=True,text=True).stdout.split())
        v0,a0=float(starts['video']),float(starts['audio'])
        self.assertAlmostEqual(v0-a0,0.37,places=2)
        self.add_ref('V005',mixed,4.5,True)
        self.assertTrue(cli('prepare','--run',self.run,'--ids','V005','--skip-whisper','--reason','the test references carry no narration worth transcribing')['ok'])
        fi=json.loads((self.run/'10-media/V005/frame-index.json').read_text())
        self.assertAlmostEqual(fi['clock_origin_s'],a0,places=3)
        blue0,green0=v0+1.3,v0+1.3+27/24          # the 24 fps part holds 27 frames (1.125 s)
        for f in fi['frames']:
            self.assertAlmostEqual(f['t_s'],f['pts_s']-a0,places=3)
            want='red' if f['pts_s']<blue0-1e-3 else 'blue' if f['pts_s']<green0-1e-3 else 'green'
            self.assertEqual(self.colour(self.run/'10-media/V005/sampled-frames'/f['file']),want,f)
            rate,start={'red':(10,v0),'blue':(24,blue0),'green':(7,green0)}[want]
            self.assertAlmostEqual((f['pts_s']-start)*rate,round((f['pts_s']-start)*rate),delta=0.02)   # a real frame's time
        self.assertAlmostEqual(fi['frames'][0]['t_s'],0.37,delta=0.01)
        # One rate per run: another rate is refused and nothing is re-sampled.
        before=sorted((media/'sampled-frames').glob('*.jpg'))
        self.assertIn('Clone the run',cli('prepare','--run',self.run,'--ids','V004','--fps',5,'--skip-whisper','--reason','the test references carry no narration worth transcribing',expected=2)['error'])
        self.assertEqual(sorted((media/'sampled-frames').glob('*.jpg')),before)
        # The frames and the transcript are cached apart: new frames never re-run Whisper. Frames made the older way
        # (one key for both, nominal slots) are not reused by a 2 fps run; the transcript still is.
        invp=self.run/'00-inventory/references.json'; inv=json.loads(invp.read_text())
        next(x for x in inv['items'] if x['id']=='V004')['has_audio']=True
        save(invp,inv)
        calls=[]
        def fake_transcribe(path,outpath,*a):
            calls.append(a)
            save(Path(outpath),{'status':'transcribed','model':'medium','segments':[]})
            Path(outpath).with_suffix('.txt').write_text('',encoding='utf-8')
            return 0
        stamp=lambda:[(f.name,f.stat().st_mtime_ns) for f in sorted((media/'sampled-frames').glob('*.jpg'))]
        with mock.patch.object(core,'transcribe',side_effect=fake_transcribe):
            self.assertEqual(self.core_call(core,'prepare','--run',self.run,'--ids','V004')[0],0)
            self.assertEqual(calls,[('medium','cuda','float16')])                       # Whisper medium, on the GPU
            self.assertEqual(self.core_call(core,'prepare','--run',self.run,'--ids','V004')[0],0)
            self.assertEqual(len(calls),1)                                             # resumed: nothing heard again
            code,out=self.core_call(core,'prepare','--run',self.run,'--ids','V004','--width',480)
            self.assertEqual((code,len(calls)),(0,1))                                 # frames re-made, Whisper not re-run
            man=json.loads((media/'preparation.json').read_text())
            self.assertEqual((man['frames_signature']['width'],man['frames_signature']['sampler']),(480,'pts-v1'))
            save(media/'preparation.json',{'id':'V004','signature':{'fingerprint':'V004-test','fps':2.0,'width':480,
                                                                     'whisper_model':'medium'}})   # an older manifest
            old=stamp()
            time.sleep(0.05)
            self.assertEqual(self.core_call(core,'prepare','--run',self.run,'--ids','V004','--width',480)[0],0)
            self.assertEqual(len(calls),1)
            self.assertNotEqual(stamp(),old)                                          # nominal frames: made again
        # av-profile records how its frames were taken, keys its cache by it, and its watch sheets show each frame
        # at its own time (the tile's frame is the last one before the middle of its five seconds).
        cli('av-profile','--run',self.run,'--refs','V004')
        prof=json.loads((self.run/'20-analysis/av/V004.json').read_text())
        self.assertEqual((prof['sampled_fps'],prof['sampler'],prof['signature']['fps'],prof['signature']['sampler'],
                          prof['thresholds']['transition_max_frame_pairs']),(2.0,'pts-v1',2.0,'pts-v1',3))
        self.assertTrue(any('2 fps' in u and 'exact timestamp' in u for u in prof['unknowns']))
        self.assertIn('inspect_candidates',prof)
        times=[f['t_s'] for f in json.loads((media/'frame-index.json').read_text())['frames']]
        self.assertEqual([x['step_s'] for x in prof['sheet_tiles']],[0.0,5.0])
        for x in prof['sheet_tiles']:
            self.assertIn(x['frame_s'],times)
            self.assertEqual(x['frame_s'],max(s for s in times if s<x['step_s']+2.5))
        # A run analysed before these settings keeps its 5 fps and its nominal slots (its frames, profiles and export
        # compare alike); its older manifests are honoured, nothing re-sampled.
        st=json.loads((self.run/'state.json').read_text())
        del st['analysis_fps'], st['analysis_sampler']; save(self.run/'state.json',st)
        dry=cli('prepare','--run',self.run,'--ids','V004','--dry-run')
        self.assertEqual((dry['fps'],dry['sampler']),(5.0,'nominal'))
        cli('prepare','--run',self.run,'--ids','V001','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        self.assertEqual(json.loads((self.run/'10-media/V001/frame-index.json').read_text())['mode'],'nominal_sample_time')
        frames_v1=lambda:[(f.name,f.stat().st_mtime_ns) for f in sorted((self.run/'10-media/V001/sampled-frames').glob('*.jpg'))]
        save(self.run/'10-media/V001/preparation.json',{'id':'V001','signature':{'fingerprint':json.loads(
            (self.run/'10-media/V001/preparation.json').read_text())['frames_signature']['fingerprint'],
            'fps':5.0,'width':960,'whisper_model':'medium'}})
        kept=frames_v1(); time.sleep(0.05)
        cli('prepare','--run',self.run,'--ids','V001','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        self.assertEqual(frames_v1(),kept)
        st['analysis_fps'],st['analysis_sampler']=2.0,'pts-v1'; save(self.run/'state.json',st)
        # A clone prepares its references again at the current rate, and keeps the content reviews (source times)
        # with the records of their closer looks, never a closer look's frames.
        self.content_review('V004',[])
        cli('inspect-window','--run',self.run,'--ref','V004','--from','2.3','--to','2.7','--why','the cut')
        clone=Path(cli('clone','--from-run',self.run,'--workspace',self.home/'runs')['run'])
        cst=json.loads((clone/'state.json').read_text())
        self.assertEqual((cst['analysis_fps'],cst['analysis_sampler']),(2.0,'pts-v1'))
        self.assertTrue((clone/'20-analysis/content/V004.json').is_file())
        self.assertEqual(len(list((clone/'20-analysis/inspect').rglob('index.json'))),1)
        self.assertEqual(list((clone/'20-analysis/inspect').rglob('*.jpg')),[])

    def test_a_closer_look_finds_what_the_samples_miss(self):
        # A white flash from 3.1 to 3.3 s in a red clip: the 2 fps samples (3.0, 3.5) never see it.
        src=self.home/'flash.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=red:s=64x36:r=30:d=3.1',
                        '-f','lavfi','-i','color=c=white:s=64x36:r=30:d=0.2','-f','lavfi','-i','color=c=red:s=64x36:r=30:d=2.7',
                        '-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0','-pix_fmt','yuv420p',str(src)],check=True)
        self.add_ref('V006',src,6.0,False)
        cli('prepare','--run',self.run,'--ids','V006','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        media=self.run/'10-media/V006'
        fi=json.loads((media/'frame-index.json').read_text())
        self.assertNotIn('white',[self.colour(media/'sampled-frames'/f['file']) for f in fi['frames']])
        # A closer look at that stretch only: 10 fps, each frame at its own time, with a contact sheet.
        out=cli('inspect-window','--run',self.run,'--ref','V006','--from','00:02.9','--to','00:03.5','--why','a flash between samples')
        idx=json.loads((Path(out['window'])/'index.json').read_text())
        seen=[(f['t_s'],self.colour(Path(out['window'])/'frames'/f['file'])) for f in idx['frames']]
        self.assertEqual([s for s,_ in seen],[2.9,3.0,3.1,3.2,3.3,3.4,3.5])
        self.assertEqual([s for s,c in seen if c=='white'],[3.1,3.2])
        self.assertTrue(Path(out['sheet']).is_file())
        self.assertEqual((idx['rate'],idx['why']),(10.0,'a flash between samples'))
        # Every frame of the stretch (--native): the flash is exactly 3.1 to 3.3 s.
        nat=cli('inspect-window','--run',self.run,'--ref','V006','--from','3.05','--to','3.35','--native')
        whites=[f['t_s'] for f in json.loads((Path(nat['window'])/'index.json').read_text())['frames']
                if self.colour(Path(nat['window'])/'frames'/f['file'])=='white']
        self.assertEqual((min(whites),len(whites)),(3.1,6))
        # A closer look is for a brief stretch, never a whole video at a higher rate.
        self.assertIn('brief stretch',cli('inspect-window','--run',self.run,'--ref','V006','--from','0','--to','60',
                                          '--fps',10,expected=2)['error'])
        # After a look at disturbing material, its frames go; the record that the look was taken stays.
        gone=cli('inspect-window','--run',self.run,'--ref','V006','--from','00:02.9','--to','00:03.5','--remove')
        self.assertEqual(list((Path(out['window'])/'frames').glob('*.jpg')),[])
        self.assertIn('frames_removed_at',json.loads(Path(gone['record_kept']).read_text()))

    def test_the_review_sees_every_shot_not_only_the_watch_sheets(self):
        # A 1.8 s blue shot at 8.0-9.8 s between red: the watch sheets' tiles (frames at 2, 7 and 12 s) never show it.
        src=self.home/'short-shot.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=red:s=64x36:r=30:d=8',
                        '-f','lavfi','-i','color=c=blue:s=64x36:r=30:d=1.8','-f','lavfi','-i','color=c=red:s=64x36:r=30:d=4.2',
                        '-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0','-pix_fmt','yuv420p',str(src)],check=True)
        self.add_ref('V007',src,14.0,False)
        cli('prepare','--run',self.run,'--ids','V007','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        cli('av-profile','--run',self.run,'--refs','V007')
        media=self.run/'10-media/V007/sampled-frames'
        times={f['t_s']:f['file'] for f in json.loads((self.run/'10-media/V007/frame-index.json').read_text())['frames']}
        tiles=json.loads((self.run/'20-analysis/av/V007.json').read_text())['sheet_tiles']
        self.assertEqual([self.colour(media/times[x['frame_s']]) for x in tiles],['red','red','red'])
        # The review is refused until every shot has been put in front of the reviewer...
        rp=self.home/'review-V007.json'
        save(rp,{'looked_at':'every sampled frame and the whole soundtrack, start to end','segments':[],'usable':'the colour cuts'})
        self.assertIn('shot_sheets_missing_run_content-review_--shot-sheets_and_open_every_one',
                      cli('content-review','--run',self.run,'--ref','V007','--file',rp,expected=2)['details'])
        made=cli('content-review','--run',self.run,'--ref','V007','--shot-sheets')
        self.assertEqual((made['shots'],len(made['sheets'])),(3,1))
        idx=json.loads((self.run/'20-analysis/content/V007-shots/index.json').read_text())
        # ...and there the short shot is seen, at its own time.
        self.assertEqual([self.colour(media/x['file']) for x in idx['shots']],['red','blue','red'])
        self.assertTrue(8.0<=idx['shots'][1]['frame_s']<=9.8)
        self.assertEqual(cli('content-review','--run',self.run,'--ref','V007','--file',rp)['segments'],0)
        self.assertEqual(json.loads((self.run/'20-analysis/content/V007.json').read_text())['shot_sheets'],1)

    def test_content_review_keeps_safety_and_creative_exclusions_apart(self):
        cli('prepare','--run',self.run,'--ids','V001','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        def seg(sid, kind, cat, action, **kw):
            return {'id':sid,'from':'00:01','to':'00:02','kind':kind,'category':cat,'action':action,
                    'what':'a short neutral description of the moment','role':'it sets up the next scene',
                    'evidence':'frame 00:01.5 and the words at 00:01-00:02','confidence':'sure',**kw}
        why='the fact is said plainly and nothing is shown'
        bad=lambda *s:self.content_review('V001',list(s),expected=2)['details']
        # Religious, superstitious or holiday material is the user's creative exclusion, never a safety matter.
        self.assertTrue(any('not_a_safety_category' in x for x in bad(seg('S1','safety','religious','exclude',severity='low',avoid=['the ritual']))))
        self.assertTrue(any('severity_is_for_safety_only' in x for x in bad(seg('S1','religion_superstition','superstition','exclude',severity='high',avoid=['the omen']))))
        self.assertTrue(any('action_must_be' in x for x in bad(seg('S1','holiday','holiday','restrict_visuals',why=why))))
        # The hard lines of safety: sexual content involving a minor is always excluded (and a child in an ordinary
        # scene is never filed under it); a high-severity segment is never kept as it is.
        self.assertTrue(any('sexual_content_minors_is_always_excluded' in x for x in bad(seg('S1','safety','sexual_content_minors','restrict_visuals',severity='high',why=why))))
        self.assertTrue(any('minors_is_not_a_category' in x for x in bad(seg('S1','safety','minors','exclude',severity='medium',why=why+' twice over',avoid=['x']))))
        self.assertTrue(any('high_severity_cannot_be_kept' in x for x in bad(seg('S1','safety','graphic_injury','keep',severity='high',why=why))))
        self.assertTrue(any('exclude_must_name_what_to_avoid' in x for x in bad(seg('S1','safety','graphic_injury','exclude',severity='high'))))
        # Proportionate, and grounded: an exclusion says why the lighter actions are not enough; what is low is never
        # excluded; evidence cites the times it was seen or heard; a doubt is looked at closer whatever is decided.
        self.assertTrue(any('exclude_must_say_why_restricting_what_is_shown_is_not_enough' in x for x in bad(
            seg('S1','safety','graphic_injury','exclude',severity='medium',avoid=['the wound']))))
        self.assertTrue(any('exclude_must_say_why_it_is_a_story_device_not_a_plain_fact' in x for x in bad(
            seg('S1','religion_superstition','religious','exclude',avoid=['the ritual']))))
        self.assertTrue(any('low_severity_is_restricted_or_kept_never_excluded' in x for x in bad(
            seg('S1','safety','distressing','exclude',severity='low',avoid=['the fall'],why='the fall is the whole point of this moment'))))
        self.assertTrue(any('evidence_must_cite_the_times' in x for x in bad(
            seg('S1','safety','distressing','keep',severity='low',why=why,evidence='seen in the frames and heard in the words'))))
        self.assertTrue(any('unsure_needs_a_closer_look' in x for x in bad(
            seg('S1','safety','graphic_injury','exclude',severity='medium',confidence='unsure',avoid=['the wound'],
                why='the moment is the injury itself, nothing else is told',**{'from':'00:02','to':'00:02.5'}))))
        # Not sure, and still to be used: a closer look first.
        unsure=seg('S1','safety','graphic_injury','restrict_visuals',severity='medium',confidence='unsure',why=why)
        self.assertTrue(any('needs_a_closer_look' in x for x in bad(unsure)))
        cli('inspect-window','--run',self.run,'--ref','V001','--from','00:01','--to','00:01.8','--why','is the injury shown?')
        # Legitimate storytelling stays usable: a battle told with its casualties, and a death explained, are kept as
        # they are (looked at, not graphic); fictional violence kept off screen keeps its subject with its visuals
        # restricted; a religious device and a holiday scene are excluded with what depends on them.
        good=[unsure,
              seg('S2','safety','distressing','keep',severity='low',why='casualty figures stated plainly over a map, nothing shown'),
              seg('S3','safety','graphic_injury','restrict_visuals',severity='high',why='the fight is told, the wound never shown'),
              seg('S4','religion_superstition','superstition','exclude',avoid=['omen','crows foretelling death'],
                  why='the omen carries the dread of the whole scene, a device and not a fact',
                  depends=[{'from':'00:05','to':'00:06','why':'the payoff recalls the omen'}]),
              seg('S5','holiday','holiday','exclude',avoid=['christmas truce'],
                  why='the truce is staged as a holiday scene that carries the episode')]
        out=self.content_review('V001',good,story_without_exclusions={'status':'bridged','note':'the dread comes from the weather and the silence instead'})
        self.assertEqual((out['excluded'],out['restricted'],out['kinds']),(2,2,{'safety':3,'religion_superstition':1,'holiday':1}))
        saved=json.loads((self.run/'20-analysis/content/V001.json').read_text())
        self.assertEqual((saved['frames_seen']['sampler'],len(saved['closer_looks'])),('pts-v1',1))
        # An excluded segment needs a word on whether the story still holds without it.
        self.assertIn('story_without_exclusions_needs_status_(coherent/bridged/too_dependent)_and_a_note',bad(*good))
        st=cli('content-review','--run',self.run,'--status')
        self.assertEqual(st['by_reference']['V001']['religion_superstition'],1)
        self.assertEqual(st['by_reference']['V002'],'not reviewed')
        # Where to look first: gathered pointers, never verdicts.
        sig=cli('content-review','--run',self.run,'--ref','V001','--signals')
        self.assertEqual((sig['frames']['sampler'],len(sig['closer_looks_taken'])),('pts-v1',1))
        self.assertIn('not verdicts',sig['note'])
        self.assertNotIn('why',sig['closer_looks_taken'][0])        # where the earlier looks were, never what they concluded
        # A blind second review: the earlier review and its closer looks leave every path the tools read; the
        # source evidence stays; the new review must take its own looks; the revision count goes on.
        arch=cli('content-review','--run',self.run,'--ref','V001','--archive')
        self.assertEqual((arch['moved'],arch['revision']),(['V001.json','inspect/'],1))
        self.assertFalse((self.run/'20-analysis/content/V001.json').exists())
        self.assertEqual(cli('content-review','--run',self.run,'--ref','V001','--signals')['closer_looks_taken'],[])
        self.assertTrue((self.run/'20-analysis/content/V001-shots/index.json').is_file())          # source evidence stays
        self.assertTrue(any('needs_a_closer_look' in x for x in bad(unsure)))                         # its own look first
        cli('inspect-window','--run',self.run,'--ref','V001','--from','00:01','--to','00:01.8','--why','is the injury shown?')
        again=self.content_review('V001',[unsure])
        self.assertEqual(json.loads((self.run/'20-analysis/content/V001.json').read_text())['revision'],2)
        self.assertTrue((self.run/'20-analysis/content-archive/V001-r1/V001.json').is_file())
        # The same window looked at again keeps the earlier look's reason on record.
        again=cli('inspect-window','--run',self.run,'--ref','V001','--from','00:01','--to','00:01.8','--why','a second opinion')
        idx=json.loads((Path(again['window'])/'index.json').read_text())
        self.assertEqual((idx['why'],idx['earlier'][0]['why']),('a second opinion','is the injury shown?'))

    def test_excluded_material_stays_out_of_what_is_made(self):
        vd=self.write_plan(lock=False)
        # V001: a superstitious device at 04:50-05:10 with its payoff at 06:10-06:30, excluded; V002: a graphic moment
        # at 02:00-02:20 whose subject may be told but never shown.
        cli('prepare','--run',self.run,'--ids','V001,V002','--skip-whisper','--reason','the test references carry no narration worth transcribing')
        def seg(sid, a, b_, kind, cat, action, **kw):
            return {'id':sid,'from':a,'to':b_,'kind':kind,'category':cat,'action':action,'confidence':'sure',
                    'what':'a soldier reads an omen in the crows' if kind!='safety' else 'a close view of a wound',
                    'role':'it builds dread before the attack','evidence':f'said and shown from {a} to {b_}',**kw}
        self.content_review('V001',[seg('S1','04:50','05:10','religion_superstition','superstition','exclude',avoid=['omen','crows foretelling death'],
                                        why='the omen is the device that carries the dread, not a plain fact',
                                        depends=[{'from':'06:10','to':'06:30','why':'the payoff recalls the omen'}])],
                            story_without_exclusions={'status':'bridged','note':'the dread comes from the weather and the silence instead'})
        self.content_review('V002',[seg('S1','02:00','02:20','safety','graphic_injury','restrict_visuals',severity='high',
                                        why='the cost is told by the count and the faces',avoid=['the open wound'])])
        doc=self.direction_doc()
        self.direction_doc=lambda:doc
        # The direction cannot cite the excluded device, nor what depended on it...
        lock=lambda expected=0:cli('direction-lock','--run',self.run,'--video',1,expected=expected)
        save(vd/'direction.json',doc)
        self.assertIn('direction_cites_excluded_material:V001@05:00-05:20:S1(religion_superstition)',lock(2)['details'])
        doc['evidence']['observations'][2]['at']='06:15-06:25'; save(vd/'direction.json',doc)
        self.assertIn('direction_cites_excluded_material:V001@06:15-06:25:S1(religion_superstition)',lock(2)['details'])
        # ...while the rest of that reference stays usable, and the restricted moment lends how it is told only.
        # A useful element inside the excluded moment may be cited, naming exactly what is taken (a warning, on record).
        doc['evidence']['observations'][2].update({'at':'04:55-05:00','borrows_only':'the long silent hold before the cut, not the omen'})
        save(vd/'direction.json',doc)
        df=self.load_core().direction_facts(self.run,1)
        self.assertFalse([x for x in df['issues'] if 'excluded' in x])
        self.assertTrue(any('inside excluded S1, cited only for: the long silent hold' in w for w in df['warnings']))
        doc['evidence']['observations'][2].pop('borrows_only')
        doc['evidence']['observations'][2]['at']='07:00-07:20'
        (vd/'script.json').rename(vd/'script-later.json')          # the direction is locked before the script
        self.lock_direction(vd)
        (vd/'script-later.json').rename(vd/'script.json')
        df=self.load_core().direction_facts(self.run,1)
        self.assertEqual(df['issues'],[])
        self.assertTrue(any('V002@02:10-02:40 is inside S1, whose visuals are restricted' in w for w in df['warnings']))
        # The script: the excluded device brought back in the words is a content flag to answer (rewrite, or why not).
        script=json.loads((vd/'script.json').read_text())
        script['lines'][2]['text']='At dawn the men saw it as an omen of what was coming changed.'
        save(vd/'script.json',script)
        self.review_script()
        pc=cli('plan-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('content_flag_unreviewed:L003:excluded_theme:V001/S1',pc['issues'])
        script['lines'][2]['text']='At dawn the men watched the ridge in silence and waited for the order changed.'
        save(vd/'script.json',script)
        packet,_=self.review_script()
        self.assertNotIn('content_flag_unreviewed:L003:excluded_theme:V001/S1',cli('plan-check','--run',self.run,'--video',1,expected=None)['issues'])
        # The cold reader gets the title, the words and the silences only (brief #4, 2026-11-22): no exclusion records.
        # The excluded device in disguise is plan-check's content flag above, answered by the editorial review.
        text=Path(packet['packet']).read_text(encoding='utf-8')
        self.assertNotIn('a soldier reads an omen in the crows',text)
        self.assertNotIn('saying plainly that people were hurt or died is fine',text)
        # Picture prompts: the excluded theme, or 02's subjects, are flags to answer before anything is generated.
        shots=self.shots_for_plan()
        shots[1]['frame_prompt']='black crows circling over the valley at noon as an omen, one clear subject'
        shots[2]['frame_prompt']='a severed rope hanging from the broken bridge at dusk, one clear subject'
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        sf=cli('shot-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('shot_S2_prompt_shows_what_a_content_review_rules_out_rewrite_it:excluded_theme:V001/S1',sf['issues'])
        self.assertIn('shot_S2_prompt_content_flag_unanswered:holiday_religion_superstition',sf['issues'])
        self.assertIn('shot_S3_prompt_content_flag_unanswered:injury_gore_distress',sf['issues'])
        shots[1]['content_note']='the birds are only weather here, not a sign of anything'      # a note cannot answer it
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        sf=cli('shot-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('shot_S2_prompt_shows_what_a_content_review_rules_out_rewrite_it:excluded_theme:V001/S1',sf['issues'])
        self.assertNotIn('shot_S2_prompt_content_flag_unanswered:holiday_religion_superstition',sf['issues'])
        shots[1].pop('content_note')
        shots[1]['frame_prompt']='black crows circling over the empty valley at noon, one clear subject'   # rewritten
        shots[2]['content_note']='a severed rope is a cut rope on a bridge; nobody is hurt or shown hurt'
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        self.assertFalse([x for x in cli('shot-check','--run',self.run,'--video',1,expected=None)['issues'] if 'content_flag' in x])
        # A restricted moment's subject can be told, but what its review says must never be shown is flagged in a
        # picture prompt, and the reviewers are told it.
        core=self.load_core()
        self.assertIn('restricted_theme:V002/S1',core.prompt_flags('a medic kneels by the open wound in the snow',core.excluded_themes(self.run,1)))
        self.assertIn('may be told, but never shown',core.house_rules(self.run,1))
        save(jobp_r:=self.home/'never.json',{'run':str(self.run),'video':1,'purpose':'thumbnail','images':[{'prompt':
             'a medic kneels by the open wound in the snow at dawn, painterly, soft edges','content_note':'the medic is the subject here, nothing else',
             'out':str(self.home/'never.png')}]})
        self.assertIn('item_1_prompt_shows_what_a_content_review_rules_out_rewrite_it:restricted_theme:V002/S1',
                      cli('media-check','--job',jobp_r,'--kind','stills',expected=2)['issues'])          # enforced, not a warning
        # Narration may still tell the restricted subject plainly: nothing flags it.
        self.assertEqual([f for f in core.content_flags([{'id':'L001','text':'The medic reached the wounded men and got them out before noon.'}],
                                                         '',core.excluded_themes(self.run,1))[0] if 'theme' in f['kind']],[])
        # Every picture's look is recorded against what the reviews rule out.
        (pic:=self.home/'still-a.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'2'*512)
        lp=self.home/'looks-never.json'
        save(lp,{'looks':[{'file':str(pic),'result':'clean','note':'a snowy ridge road at dawn, nobody hurt'}]})
        self.assertIn('never_show_checked',cli('content-review','--run',self.run,'--video',1,'--pictures','--file',lp,expected=2)['error'])
        save(lp,{'never_show_checked':True,'looks':[{'file':str(pic),'result':'clean','note':'a snowy ridge road at dawn, nobody hurt'}]})
        self.assertEqual(cli('content-review','--run',self.run,'--video',1,'--pictures','--file',lp)['recorded'],1)
        # Style words cannot bring in what the approved prompt doesn't; a thumbnail is held to the same.
        stills=self.home/'stills'
        jobp=self.home/'job.json'
        save(jobp,{'run':str(self.run),'video':1,'images':[{'shot_id':'S1','prompt':shots[0]['frame_prompt']+', candle-lit church glow','out':str(stills/'S1.png')}]})
        self.assertIn('item_1_style_words_content_flag_unanswered:holiday_religion_superstition',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        save(jobp,{'run':str(self.run),'video':1,'purpose':'thumbnail','images':[{'prompt':'blood on the snow beside a fallen soldier at the bridge','out':str(stills/'t.png')}]})
        self.assertIn('item_1_prompt_content_flag_unanswered:injury_gore_distress',cli('media-check','--job',jobp,'--kind','stills',expected=2)['issues'])
        # The safer picture that keeps the meaning: what is left behind, not the wound.
        save(jobp,{'run':str(self.run),'video':1,'purpose':'thumbnail','images':[{'prompt':'an empty helmet in the trampled snow at the bridge, dawn light behind, painterly, soft edges','out':str(stills/'t.png')}]})
        self.assertTrue(cli('media-check','--job',jobp,'--kind','stills')['ok'])
        # A story that depends on what was excluded: its craft may still be cited, never its story.
        self.content_review('V002',[seg('S1','02:00','02:20','safety','graphic_injury','exclude',severity='high',avoid=['the wound'],
                                        why='the moment is the wound itself, nothing else in it can be told')],
                            story_without_exclusions={'status':'too_dependent','note':'the whole story turns on the injury itself'})
        self.assertTrue(any('V002: its story depends on material excluded' in w for w in self.load_core().direction_facts(self.run,1)['warnings']))

    def test_legacy_not_imported_and_clone_keeps_only_analysis(self):
        clone=cli('clone','--from-run',self.run,'--workspace',self.home/'runs')['run']
        cp=Path(clone)
        self.assertTrue((cp/'20-analysis/cards/V001.json').exists())
        self.assertFalse((cp/'40-plans/video-01/length-lock.json').exists())
        self.assertEqual(json.loads((cp/'state.json').read_text())['selected_niche'],None)
        self.assertFalse(cli('status','--run',cp)['videos'])

    # ---------------------------------------------------------------- held silences: proposed, measured, decided
    def recorded_with_gaps(self, gaps, skew=0.15, split_after=None, edge=0.1, pauses=None, contours=None, room=0.0,
                           breaths=None, delivery=False):
        """A script of len(gaps) lines recorded with exactly known silences: a tone while each line is spoken, digital
        silence after it (gaps[i] s after line i+1). Whisper's end of each line is placed `skew` s late (it places line
        ends to within about 0.2 s). With split_after=k the narration is two parts (lines 1-k, then the rest), each
        with `edge` s of silence at the join's side, so the join's whole gap is 2*edge. pauses: {line index: fields}.
        contours: {line index: 'fall'|'rise'}: the line's last 0.6 s glides from 220 Hz to 140 Hz or 330 Hz. room: the
        level (amplitude) of a room tone in every silence instead of digital silence. breaths: {line index: seconds}:
        a soft breath (0.1 s of noise) that many seconds before the NEXT line starts. Measured by narration-measure
        (cached Whisper: nothing transcribed; with delivery=True its pitch and ending measurements run too)."""
        import numpy as np, soundfile as sf
        rng = np.random.default_rng(3)
        contours, breaths = contours or {}, breaths or {}
        def quiet(seconds):
            k = int(44100 * seconds)
            return (rng.normal(0, room, k) if room else np.zeros(k)).astype('float32')
        def tone(i, length):
            f = np.full(length, 220.0)
            glide = min(length, int(44100 * 0.6))
            if contours.get(i):
                f[-glide:] = np.linspace(220.0, 140.0 if contours[i] == 'fall' else 330.0, glide)
            return (0.3 * np.sin(2 * np.pi * np.cumsum(f) / 44100)).astype('float32')
        def silence_after(i, seconds):
            s = quiet(seconds)
            if i in breaths and seconds > breaths[i] + 0.1:
                k0 = len(s) - int(44100 * breaths[i])
                s[k0:k0 + 4410] += rng.normal(0, 0.011, 4410).astype('float32')     # about 30 dB under the voice
            return s
        vd=self.write_plan()
        n=len(gaps)
        lines=[{'id':f'L{i:03}','text':f'Line {i} tells the viewer something new about the road ahead tonight.'}
               for i in range(1,n+1)]
        for k,fields in (pauses or {}).items():
            lines[k-1].update(fields)
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        direction={'narrative_job':'deliver','visual_intent':'map','sound_direction':'bed','narration_direction':'curious'}
        half=n//2
        save(vd/'beat-map.json',{'target_length_s':600,'beats':[
            {'id':'B01','start_s':0,'end_s':300,'line_start':1,'line_end':half,'experience':'oriented','pace':'brisk',**direction},
            {'id':'B02','start_s':300,'end_s':600,'line_start':half+1,'line_end':n,'experience':'uneasy','pace':'slow',**direction}]})
        d=self.run/'50-audio/video-01'; (d/'whisper').mkdir(parents=True)
        sr=44100
        groups=[(1,n)] if not split_after else [(1,split_after),(split_after+1,n)]
        chunks,texts=[],[]
        for pid,(lo,hi) in enumerate(groups,1):
            audio=[quiet(0.3)]; pos=int(sr*0.3); segs=[]
            for i in range(lo,hi+1):
                row=lines[i-1]; spoken=' '.join(w for w in row['text'].split() if not w.startswith('[') and not w.endswith(']'))
                words=spoken.split()
                s0=pos/sr; ws=[]
                for j,w in enumerate(words):
                    ws.append({'start_s':round(s0+0.27*j,3),'end_s':round(s0+0.27*j+0.25,3),'text':' '+w})
                length=int(sr*0.27*len(words))
                audio.append(tone(i,length)); pos+=length
                end=pos/sr
                ws[-1]['end_s']=round(end+skew,3)
                segs.append({'start_s':round(s0,3),'end_s':round(end+skew,3),'text':spoken,'words':ws})
                g=edge if (split_after and i==hi and i<n) else gaps[i-1]
                audio.append(silence_after(i,g)); pos+=int(sr*g)
            name=f'part-{pid:03}.wav'
            sf.write(str(d/name),np.concatenate(audio),sr)
            if pid>1:          # the next part opens with `edge` of silence instead of 0.3 s
                y,_=sf.read(str(d/name),dtype='float32'); sf.write(str(d/name),y[int(sr*(0.3-edge)):],sr)
                for s in segs:
                    s['start_s']=round(s['start_s']-(0.3-edge),3); s['end_s']=round(s['end_s']-(0.3-edge),3)
                    for w in s['words']:
                        w['start_s']=round(w['start_s']-(0.3-edge),3); w['end_s']=round(w['end_s']-(0.3-edge),3)
            save(d/f'whisper/part-{pid:03}.json',{'status':'transcribed','model':'medium','segments':segs})
            (d/f'whisper/part-{pid:03}.txt').write_text('\n'.join(f"[{s['start_s']:.1f}-{s['end_s']:.1f}] {s['text']}"
                                                              for s in segs),encoding='utf-8')
            text='\n'.join(lines[i-1]['text'] for i in range(lo,hi+1))
            chunks.append({'id':pid,'line_start':lo,'line_end':hi,'file':name,'characters':len(text),
                           'text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()})
        save(d/'manifest.json',{'model_id':'eleven_v4','voice_id':'TESTID','language':'en','status':'complete',
                                'finished_parts':[c['id'] for c in chunks],'voice_settings':{},'chunks':chunks})
        (d/'parts.txt').write_text(''.join(f"file '{(d/c['file']).as_posix()}'\n" for c in chunks))
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(d/'parts.txt'),
                        '-ar','44100','-ac','2','-c:a','pcm_s16le',str(d/'narration.wav')],check=True)
        return vd,d,cli('narration-measure','--run',self.run,'--video',1,*([] if delivery else ['--no-delivery']))

    def two_shots(self, n):
        shots=[{'id':'S1','beat_id':'B01','line_start':'L001','line_end':f'L{n//2:03}','composition':'wide',
                'new_thing':'the road the narrator is talking about, from above','frame_prompt':'a long road through snow seen from a ridge at dawn'},
               {'id':'S2','beat_id':'B02','line_start':f'L{n//2+1:03}','line_end':f'L{n:03}','composition':'close',
                'new_thing':'the hands that will have to fix the bridge','frame_prompt':'cold hands holding a coil of rope beside a broken bridge'}]
        save(self.run/'60-visuals/video-01/shot-plan.json',{'video':1,'shots':shots})
        return shots

    def quiet_at(self, wav, t):
        av=self.load_core()._av()
        run=av.silence_at(wav,t,search_s=0.1)
        return round(run[1]-run[0],2) if run else None

    def test_a_held_silence_counts_the_voices_own_gap_once(self):
        core=self.load_core()
        gaps=[0.45,0.62,0.40,1.30,0.70,0.55,0.50,0.65,0.60,0.80]       # every line its own gap, one long by nature
        held=lambda total: {'pause_total_s':total,'pause_via':'edit',**HELD}
        vd,d,out=self.recorded_with_gaps(gaps,pauses={3:held(1.5),4:held(1.2),7:held(2.0)})
        # The gap after each line is read from the audio, not from Whisper's late line ends (0.15 s off here).
        lt=json.loads((d/'line-times.json').read_text())
        for r in lt['lines'][:-1]:
            self.assertEqual(r['gap_basis'],'audio')
            self.assertAlmostEqual(r['gap_after_s'],gaps[r['index']-1],delta=0.03)
        self.assertEqual(lt['lines'][-1].get('gap_is_tail'),True)
        # Before any decision: each pause is a proposal, its silence estimated against that line's own gap.
        holds_issues=lambda: [x for x in cli('plan-check','--run',self.run,'--video',1,expected=None)['issues']
                              if x.startswith('holds_changed')]
        before=holds_issues()
        h={x['line']:x for x in cli('holds','--run',self.run,'--video',1)['holds']}
        self.assertEqual({x['status'] for x in h.values()},{'provisional'})
        self.assertAlmostEqual(h['L003']['added_s'],1.1,delta=0.04)         # 1.5 wanted, 0.40 already there
        self.assertEqual(h['L004']['added_s'],0.0)                          # 1.2 wanted, the voice left 1.30
        self.assertAlmostEqual(h['L007']['added_s'],1.5,delta=0.04)
        # Nothing is inserted from a proposal: the edit waits for a decision on every planned pause.
        self.two_shots(10)
        res=cli('retime-shots','--run',self.run,'--video',1,expected=2)
        self.assertEqual(sorted(res['details']['undecided']),['L003','L004','L007'])
        # Decisions: L003 keeps its whole silence; L004's own gap already gives it; L007 (a reveal the next line
        # carries) needs no held silence at all.
        cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.5,
            '--reason','the cost lands before the next line, the map has time to settle')
        dec=cli('hold-decide','--run',self.run,'--video',1,'--line','L004','--stage','narration','--total',1.2,
                '--reason','the voice already breathes here long enough for the turn')['decision']
        self.assertEqual(dec['added_s'],0.0); self.assertIn('already gives it',dec['outcome'])
        cli('hold-decide','--run',self.run,'--video',1,'--line','L007','--stage','narration','--no-hold',
            '--reason','the reveal lands on the next line, a wait would only delay it')
        # A pause the script did not plan can be decided after listening too: no quota either way.
        cli('hold-decide','--run',self.run,'--video',1,'--line','L005','--stage','narration','--total',2,
            '--reason','heard aloud, the turn needs a breath the script did not give it')
        self.assertEqual(cli('plan-check','--run',self.run,'--video',1,expected=None)['holds']['undecided'],[])
        rt=cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        script_holds=[x for x in plan['holds'] if x['kind']=='script']
        self.assertEqual([x['after_line'] for x in script_holds],['L003','L005'])    # only where silence is added
        l3=script_holds[0]
        self.assertAlmostEqual(l3['hold_s'],1.1,delta=0.04)
        self.assertAlmostEqual(l3['resulting_gap_s'],1.5,delta=core.HOLD_VERIFY_TOL_S)
        self.assertEqual({p['after_line']:p['hold_s'] for p in plan['pauses']}['L004'],0.0)
        self.assertEqual({p['after_line']:p['hold_s'] for p in plan['pauses']}['L007'],0.0)
        # The edit's narration is the narration plus exactly the added silence: nothing cut, nothing doubled.
        nar_s=core.probe(d/'narration.wav')['duration_s']; edit_s=core.probe(d/'narration-edit.wav')['duration_s']
        added=sum(x['hold_s'] for x in plan['holds'])
        self.assertAlmostEqual(edit_s,nar_s+added,delta=0.03)
        self.assertEqual(rt['edit_duration_s'],plan['edit_duration_s'])
        import numpy as np, soundfile as sf
        loud=lambda p: float((np.abs(sf.read(str(p),dtype='float32')[0]).mean(axis=1)>0.05).sum())/44100
        self.assertAlmostEqual(loud(d/'narration.wav'),loud(d/'narration-edit.wav'),delta=0.01)   # every word kept
        lt_rows={r['id']:r for r in lt['lines']}
        shift=lambda t: t+sum(x['hold_s'] for x in plan['holds'] if x['at_audio_s']<=t)
        mid=lambda lid: shift((lt_rows[lid]['gap_span_s'][0]+lt_rows[lid]['gap_span_s'][1])/2)
        self.assertAlmostEqual(self.quiet_at(d/'narration-edit.wav',mid('L004')),1.30,delta=0.04)  # untouched
        self.assertAlmostEqual(self.quiet_at(d/'narration-edit.wav',mid('L007')),0.50,delta=0.04)  # untouched
        # The decisions never touched the reviewed script: they ask for no new read (what the fixture's own script
        # swap asks for is unchanged).
        self.assertEqual(holds_issues(),before)

    def test_a_hold_is_decided_again_with_its_picture_and_retimed(self):
        core=self.load_core()
        gaps=[0.5,0.6,0.4,0.6,0.5,0.6,0.5,0.6,0.5,0.7]
        vd,d,_=self.recorded_with_gaps(gaps,pauses={3:{'pause_total_s':1.4,'pause_via':'edit',**HELD},
                                                    10:{'pause_total_s':2.5,'pause_via':'edit',**HELD}})
        shots=self.two_shots(10)
        for lid,total in (('L003',1.4),('L010',2.5)):
            cli('hold-decide','--run',self.run,'--video',1,'--line',lid,'--stage','narration','--total',total,
                '--reason','held for the map to settle before the voice goes on')
        cli('retime-shots','--run',self.run,'--video',1)
        first=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        # The closing hold sits after the voice's own tail: the last picture holds, nothing is cut from the end.
        tail=[x for x in first['holds'] if x['after_line']=='L010'][0]
        self.assertAlmostEqual(tail['expected_gap_s'],2.5,delta=0.04)
        self.assertAlmostEqual(tail['resulting_gap_s'],2.5,delta=core.HOLD_VERIFY_TOL_S)
        # A changed decision is kept in the history, and the edit plan made from the old one is outdated.
        cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',0.9,
            '--reason','listening, the shorter beat keeps the joke dry and the pace up')
        hist=json.loads((vd/'holds.json').read_text())['history']
        self.assertEqual([x['total_s'] for x in hist],[1.4])
        tl=cli('timeline-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('edit_plan_outdated_holds_changed_rerun_retime_shots',tl['issues'])
        self.assertIn('holds_not_decided_with_their_picture:L003,L010',tl['issues'])
        cli('retime-shots','--run',self.run,'--video',1)
        second=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        self.assertNotEqual(first['narration_for_edit']['sha256'],second['narration_for_edit']['sha256'])
        l3=[x for x in second['holds'] if x['after_line']=='L003'][0]
        self.assertAlmostEqual(l3['resulting_gap_s'],0.9,delta=core.HOLD_VERIFY_TOL_S)
        self.assertAlmostEqual(second['edit_duration_s'],first['edit_duration_s']-0.5,delta=0.03)
        # With the stills: each held silence decided again with the shot on screen while it lasts.
        stills=self.home/'stills'; stills.mkdir()
        sl=self.run/'60-visuals/video-01/style-lock.json'
        if not sl.is_file():
            cli('style-lock','--run',self.run,'--video',1,'--style-prompt','ink wash','--departs-when','photorealistic, flat vector')
        style=json.loads(sl.read_text(encoding='utf-8'))['style_prompt']
        job={'run':str(self.run),'video':1,'images':[{'shot_id':s['id'],'prompt':s['frame_prompt']+', '+style,
                                                      'out':str(stills/f"{s['id']}.png")} for s in shots]}
        gate=core.media_gate(job,'stills'); self.assertTrue(gate['ok'],gate['issues'])
        for it in job['images']:
            Path(it['out']).write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*2048)
        core.record_media(gate['run'],1,'stills',[{'out':it['out'],**rec} for it,rec in zip(job['images'],gate['records'])])
        nobed=cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','picture','--total',0.9,
                  '--reason','with the still on screen the length still serves the moment',expected=2)
        self.assertIn('--bed',nobed['error'])                                 # with the picture, the sound too
        def confirm():
            for lid,total in (('L003',0.9),('L010',2.5)):
                dec=cli('hold-decide','--run',self.run,'--video',1,'--line',lid,'--stage','picture','--total',total,
                        '--bed','none','--reason','with the still on screen the length still serves the moment')['decision']
                self.assertTrue(dec['picture']['still'])
            return dec
        dec=confirm()
        self.assertEqual(dec['picture']['shot_id'],'S2')
        tl=cli('timeline-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('edit_plan_outdated_holds_changed_rerun_retime_shots',tl['issues'])   # the bed is now decided
        cli('retime-shots','--run',self.run,'--video',1)
        confirm()                                                             # the same again: nothing changes
        tl=cli('timeline-check','--run',self.run,'--video',1,expected=2)
        self.assertFalse([x for x in tl['issues'] if 'hold' in x])
        # The picture changes: the decision made with the old one no longer stands.
        (stills/'S1.png').write_bytes(b'\x89PNG\r\n\x1a\n'+b'1'*2048)
        tl=cli('timeline-check','--run',self.run,'--video',1,expected=2)
        self.assertIn('hold_L003_decided_with_another_picture',tl['issues'])
        # Re-recording the part a decision was made on leaves it stale: decided again before any retime.
        y=(d/'part-001.wav').read_bytes(); (d/'part-001.wav').write_bytes(y[:200000]+bytes([y[200000]^1])+y[200001:])
        for f in (d/'whisper').glob('*'):
            os.utime(f)                                          # the cached transcript still stands: no Whisper run
        cli('narration-measure','--run',self.run,'--video',1,'--no-delivery')
        self.assertEqual(sorted(cli('holds','--run',self.run,'--video',1)['undecided']),['L003','L010'])
        self.assertIn('undecided',cli('retime-shots','--run',self.run,'--video',1,expected=2)['details'])

    def test_a_join_and_a_performed_pause_are_not_stacked(self):
        gaps=[0.6,0.5,0.6,0.55,0.6,0.5,0.6,0.5,0.6,0.7]
        vd,d,out=self.recorded_with_gaps(gaps,split_after=5,edge=0.1)
        seam=out['seams'][0]
        self.assertAlmostEqual(seam['gap_s'],0.2,delta=0.03)                    # the join, read from the audio
        self.assertGreater(seam['seam_hold_s'],0.25)                            # continuity restored when nothing is held
        # A pause decided at the join is decided as a whole: the join's own 0.2 s counts, no seam hold on top.
        script=json.loads((vd/'script.json').read_text())
        script['lines'][4].update({'pause_total_s':1.6,'pause_via':'edit',**HELD})
        save(vd/'script.json',script)
        cli('narration-measure','--run',self.run,'--video',1,'--no-delivery')
        lt=json.loads((d/'line-times.json').read_text())
        self.assertEqual(lt['seams'][0]['seam_hold_s'],0.0)
        dec=cli('hold-decide','--run',self.run,'--video',1,'--line','L005','--stage','narration','--total',1.6,
                '--reason','the chapter turns here, a breath before the next part')['decision']
        self.assertAlmostEqual(dec['natural_gap_s'],0.2,delta=0.03)
        self.assertAlmostEqual(dec['added_s'],1.4,delta=0.03)
        self.two_shots(10)
        cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        self.assertEqual([x['kind'] for x in plan['holds']],['script'])
        self.assertAlmostEqual(plan['holds'][0]['resulting_gap_s'],1.6,delta=self.load_core().HOLD_VERIFY_TOL_S)
        # The hold belongs to the shot before the cut: the cut comes after the silence.
        s1=plan['shots'][0]
        self.assertAlmostEqual(s1['end_s'],plan['holds'][0]['at_audio_s']+plan['holds'][0]['hold_s'],delta=0.02)

    def test_pause_forms_double_application_and_signals(self):
        core=self.load_core()
        tagged=[{'id':'L001','text':'There is one road. [pause]','pause_total_s':2,'pause_via':'edit',**HELD},
                {'id':'L002','text':'And then the night comes.'}]
        # The whole silence decided once: the cue performs part of it, the edit tops up only what the measured cue
        # leaves (a residual). In the older added-on-top form the same pair would stack, and is refused.
        plan,issues=core.script_pause_plan(tagged)
        self.assertFalse([x for x in issues if 'is_an_edit_hold_and_a_pause_tag_at_once' in x])
        self.assertTrue(plan[0]['residual_of_tag'])
        older=[{'id':'L001','text':'There is one road. [pause]','pause_after_s':2,'pause_via':'edit',**HELD},
               {'id':'L002','text':'And then the night comes.'}]
        self.assertTrue(any('is_an_edit_hold_and_a_pause_tag_at_once' in x for x in core.script_pause_plan(older)[1]))
        both=[{'id':'L001','text':'A line.','pause_total_s':2,'pause_after_s':2,'pause_via':'edit',**HELD}]
        self.assertTrue(any('has_both' in x for x in core.script_pause_plan(both)[1]))
        bare=[{'id':'L001','text':'A line.','pause_total_s':0.8,**HELD}]
        self.assertIn('pause_L001_needs_pause_via_edit_or_tag',core.script_pause_plan(bare)[1])
        # No minimum, no maximum: a short beat and a long one are both expressible.
        ok=[{'id':'L001','text':'A line.','pause_total_s':0.9,'pause_via':'edit',**HELD},
            {'id':'L002','text':'Another.','pause_total_s':9.0,'pause_via':'edit',**HELD}]
        plan,issues=core.script_pause_plan(ok)
        self.assertEqual(issues,[])
        self.assertAlmostEqual(core.planned_added_s(plan[0],0.6),0.3)            # the whole 0.9, less the voice's 0.6
        self.assertEqual(core.planned_added_s(plan[0],1.1),0.0)                  # the voice already gives it
        self.assertAlmostEqual(core.planned_added_s(plan[1]),9.0-core.DEFAULT_NATURAL_GAP_S)
        # The older form reads as it was written and reviewed: added on top of the voice's gap.
        old=[{'id':'L001','text':'A line.','pause_after_s':2.5,'pause_via':'edit',**HELD},
             {'id':'L002','text':'Short.','pause_after_s':0.8}]
        plan,issues=core.script_pause_plan(old)
        self.assertEqual(([p['form'] for p in plan],issues),(['added'],[]))
        self.assertEqual(core.planned_added_s(plan[0],0.6),2.5)
        # Signals, never verdicts: lengths that step up through the film, or are all alike.
        rising=[{'seconds':s} for s in (2.5,3.0,3.5,4.0)]
        self.assertTrue(any('grow steadily' in w for w in core.hold_signals(rising)))
        self.assertEqual(core.hold_signals([{'seconds':s} for s in (1.2,3.0,0.8)]),[])
        self.assertTrue(any('every planned pause is 2' in w for w in core.hold_signals([{'seconds':2}]*3)))

    def test_previews_and_the_final_read_show_the_silences_as_they_are(self):
        gaps=[0.5,0.6,0.4,0.6,0.5,0.6,0.5,0.6,0.5,0.7]
        vd,d,_=self.recorded_with_gaps(gaps,pauses={3:{'pause_total_s':1.5,'pause_via':'edit',**HELD}})
        pv=cli('holds','--run',self.run,'--video',1,'--preview','L003','--totals','1.0,2.0')['preview']
        self.assertEqual([v['variant'] for v in pv['variants']],['voice-gap','total-1.00s','total-2.00s'])
        core=self.load_core()
        lens=[core.probe(Path(v['audio']))['duration_s'] for v in pv['variants']]     # the same moment, only the
        self.assertAlmostEqual(lens[1]-lens[0],1.0-pv['natural_gap_s'],delta=0.03)     # silence differs
        self.assertAlmostEqual(lens[2]-lens[0],2.0-pv['natural_gap_s'],delta=0.03)
        for v in pv['variants']:                     # each preview holds the whole silence it is named for
            self.assertAlmostEqual(self.quiet_at(Path(v['audio']),v['silence_centre_s']),v['whole_silence_s'],delta=0.04)
        self.assertTrue(Path(pv['guide']).is_file()); self.assertFalse(pv['picture'])        # no still yet: audio only
        dec=cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.5,
                '--reason','the user listened and the longer beat lets the map land','--listened','the 1.5 one feels right')['decision']
        self.assertEqual(len(dec['previews']),3); self.assertEqual(dec['listened'],'the 1.5 one feels right')
        self.two_shots(10)
        cli('retime-shots','--run',self.run,'--video',1)
        # The final reviewer is told where the held silences are and how long, not why the director wanted them.
        exp=self.home/'export.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=navy:s=320x180:r=30',
                        '-i',str(d/'narration-edit.wav'),'-shortest','-pix_fmt','yuv420p','-c:a','aac',str(exp)],check=True)
        tr=self.home/'export-transcript.json'
        save(tr,{'status':'transcribed','segments':[{'start_s':0.3,'end_s':3.0,'text':'words',
                 'words':[{'start_s':round(0.3+0.27*i,2),'end_s':round(0.55+0.27*i,2),'text':' word'} for i in range(10)]}]})
        cli('av-profile','--run',self.run,'--video',1,'--file',exp,'--transcript',tr)
        pk=cli('review-packet','--run',self.run,'--video',1,'--kind','final','--file',exp)
        text=Path(pk['packet']).read_text(encoding='utf-8')
        self.assertIn('## Held silences in this cut',text)
        self.assertIn('about 1.5 s with no voice, after "...',text)
        self.assertIn('road ahead tonight.", before "Line 4 tells',text)
        self.assertNotIn(HELD['pause_purpose'],text)

    # ---------------------------------------------------------------- transitions into and out of a held silence
    def test_how_a_line_lands_and_the_next_begins_is_measured(self):
        gaps=[0.6,0.7,0.6,0.7,0.6,0.7,0.6,0.7,0.6,0.8]
        vd,d,out=self.recorded_with_gaps(gaps,contours={2:'fall',4:'rise'},delivery=True,
                                         pauses={2:{'pause_total_s':1.4,'pause_via':'edit',**HELD},
                                                 4:{'pause_total_s':1.4,'pause_via':'edit',**HELD}})
        self.assertTrue(out['cadence_usual'])                                  # this voice's usual endings
        h={x['line']:x for x in cli('holds','--run',self.run,'--video',1)['holds']}
        fall,rise=h['L002']['ending'],h['L004']['ending']
        self.assertLess(fall['last_vowel_vs_line_st'],-3)                     # it lands: falls below the line
        self.assertGreater(rise['last_vowel_vs_line_st'],3)                   # it hangs: rises above the line
        self.assertGreater(rise['next_reset_st'],-12); self.assertLess(fall['next_reset_st'],12)
        self.assertEqual(fall['punctuation'],'.')
        self.assertLess(fall['soft_end_s'],0.1)                               # a clean stop, nothing after the vowel
        self.assertIn('inside_silence',h['L002'])

    def test_an_added_silence_keeps_a_breath_with_its_line(self):
        core=self.load_core()
        gaps=[0.6,0.6,1.0,0.6,0.6,1.0,0.6,0.6,1.0,0.7]
        # L003: a breath just before the next line. L006: a breath in the middle of the silence, where the middle of
        # the gap (the old place for an added silence) would have cut it in two. L009: a release just after the line,
        # which belongs to that line: the added silence goes after it.
        breaths={3:0.25,6:0.55,9:0.75}
        vd,d,_=self.recorded_with_gaps(gaps,breaths=breaths,pauses={k:{'pause_total_s':2.0,'pause_via':'edit',**HELD}
                                                                       for k in breaths})
        rows={x['id']:x for x in json.loads((d/'line-times.json').read_text())['lines']}
        for k,lead in breaths.items():
            r=rows[f'L{k:03}']
            self.assertAlmostEqual(r['gap_after_s'],1.0,delta=0.04)           # the breath is inside the silence...
            self.assertGreater(r['gap_other_material_s'],0.05)
            breath=(r['gap_span_s'][1]-lead, r['gap_span_s'][1]-lead+0.1)
            self.assertFalse(breath[0]-0.02<=r['gap_insert_at_s']<=breath[1]+0.02)   # ...never cut by the added one
            cli('hold-decide','--run',self.run,'--video',1,'--line',f'L{k:03}','--stage','narration','--total',2.0,
                '--reason','the turn lands, then the breath that opens the next line')
        self.two_shots(10)
        cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        import numpy as np, soundfile as sf
        y,sr=sf.read(str(d/'narration-edit.wav'),dtype='float32',always_2d=True); y=y[:,0]
        for p in plan['pauses']:
            self.assertAlmostEqual(p['resulting_gap_s'],2.0,delta=core.HOLD_VERIFY_TOL_S)
            # In the edit the breath is whole, and as far as recorded from the line it belongs to.
            lead=breaths[p['index']]
            t_from,t_next=p['times_in_edit']['silence_from_s'],p['times_in_edit']['next_line_s']
            win=y[int(t_from*sr):int(t_next*sr)]
            env=np.array([np.sqrt(np.mean(win[k:k+441]**2)) for k in range(0,len(win)-441,441)])
            on=env>env.max()/3
            start=int(np.argmax(on)); length=int(np.argmax(~on[start:])) if (~on[start:]).any() else len(on)-start
            at=t_from+0.01*start
            centre=(1.0-lead+0.05)/1.0                     # where the breath sits in its 1.0 s silence
            if centre>=0.45:  # an intake before the next line (or mid-silence): stays with the next line
                self.assertAlmostEqual(t_next-at,lead,delta=0.03)
            else:             # a release after the line: stays with that line
                self.assertAlmostEqual(at-t_from,1.0-lead,delta=0.04)
            self.assertAlmostEqual(0.01*length,0.1,delta=0.03)                # one breath, not two halves

    def test_a_fade_touches_only_audible_room_tone(self):
        import numpy as np, soundfile as sf
        core=self.load_core()
        gaps=[0.6,0.6,1.0,0.6,0.6,0.6,0.6,0.6,0.6,0.8]
        # A recording with audible room tone in its silences (about 45 dB under the voice).
        vd,d,_=self.recorded_with_gaps(gaps,room=0.0013,pauses={3:{'pause_total_s':1.8,'pause_via':'edit',**HELD}})
        r=[x for x in json.loads((d/'line-times.json').read_text())['lines'] if x['id']=='L003'][0]
        self.assertLess(r['gap_floor_under_speech_db'],core._av().AUDIBLE_FLOOR_UNDER_DB)
        refused=cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--no-hold',
                    '--into','fade','--reason','a fade with nothing added would only change the voice',expected=2)
        self.assertIn('nothing is added',json.dumps(refused))
        last=cli('hold-decide','--run',self.run,'--video',1,'--line','L010','--stage','narration','--total',2.0,
                 '--out-of','fade','--reason','the ending fades back in to nothing at all',expected=2)
        self.assertIn('nothing follows the last line',json.dumps(last))
        dec=cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.8,
                '--into','fade','--out-of','fade','--reason','the room tone eases into the held silence and back')['decision']
        f=dec['transition']['fades_on_narration_clock']
        self.assertTrue(f['into'] and f['out_of'])
        self.assertGreaterEqual(f['into'][0],r['gap_subrun_s'][0])            # inside the quiet stretch only
        self.assertLessEqual(f['out_of'][1],r['gap_subrun_s'][1])
        self.two_shots(10)
        cli('retime-shots','--run',self.run,'--video',1)                     # the voice-unchanged check passes
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        h=plan['holds'][0]
        self.assertEqual((h['transition']['into'],h['transition']['out_of']),('fade','fade'))
        self.assertAlmostEqual(h['resulting_gap_s'],1.8,delta=core.HOLD_VERIFY_TOL_S)
        # The room tone really fades to the splice: the last 50 ms before it are far quieter than in the recording.
        a,sr=sf.read(str(d/'narration.wav'),dtype='float32',always_2d=True); b,_=sf.read(str(d/'narration-edit.wav'),dtype='float32',always_2d=True)
        at=h['at_audio_s']; rms=lambda x: float(np.sqrt(np.mean(x**2))+1e-9)
        before_orig=rms(a[int((at-0.05)*sr):int(at*sr),0]); before_edit=rms(b[int((at-0.05)*sr):int(at*sr),0])
        self.assertLess(20*np.log10(before_edit/before_orig),-6)

    def test_a_fade_is_refused_where_the_silence_is_already_silent(self):
        gaps=[0.6,0.6,1.0,0.6,0.6,0.6,0.6,0.6,0.6,0.8]
        vd,d,_=self.recorded_with_gaps(gaps,pauses={3:{'pause_total_s':1.8,'pause_via':'edit',**HELD}})
        res=cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.8,
                '--into','fade','--reason','the room tone eases into the held silence',expected=2)
        self.assertIn('silence already',json.dumps(res))
        pv=cli('holds','--run',self.run,'--video',1,'--preview','L003','--totals','1.8','--into','clean,fade')['preview']
        self.assertEqual([v['variant'] for v in pv['variants']],['voice-gap','total-1.80s'])
        self.assertTrue(pv['refused'] and 'silence already' in json.dumps(pv['refused']))
        self.assertIn('Not rendered',Path(pv['guide']).read_text(encoding='utf-8'))

    def test_the_bed_around_a_silence_is_carried_and_checked(self):
        gaps=[0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.8]
        vd,d,_=self.recorded_with_gaps(gaps,pauses={3:{'pause_total_s':1.6,'pause_via':'edit',**HELD}})
        cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.6,'--bed','enters',
            '--reason','the music begins in the silence after the turn, under the picture')
        self.two_shots(10)
        cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        p=plan['pauses'][0]
        self.assertEqual(p['transition']['bed'],'enters')
        tm=p['times_in_edit']
        self.assertAlmostEqual(tm['next_line_s']-tm['silence_from_s'],1.6,delta=0.05)
        tdir=self.run/'70-edit/video-01'
        def check(music_start, music_end):
            save(tdir/'timeline.json',{'canvas':'1920x1080','visual_segments':[],
                 'audio_tracks':[{'kind':'narration','file':plan['narration_for_edit']['file'],'start_s':0,
                                  'end_s':plan['edit_duration_s']},
                                 {'kind':'music','file':str(self.home/'bed.wav'),'start_s':music_start,'end_s':music_end,
                                  'beats':['B01']}]})
            return [x for x in cli('timeline-check','--run',self.run,'--video',1,expected=2)['issues'] if '_bed_' in x]
        self.assertEqual(check(tm['silence_from_s']+0.2,plan['edit_duration_s']),[])      # it enters in the silence
        self.assertTrue(check(tm['silence_from_s']+6.0,plan['edit_duration_s']))          # six seconds late: caught
        cli('hold-decide','--run',self.run,'--video',1,'--line','L003','--stage','narration','--total',1.6,'--bed','none',
            '--reason','the silence stays bare, nothing under it at all')
        cli('retime-shots','--run',self.run,'--video',1)
        plan=json.loads((self.run/'70-edit/video-01/edit-plan.json').read_text())
        self.assertTrue(check(0.0,plan['edit_duration_s']))                 # a bed playing under a bare silence: caught

    def test_performance_plan_cues_and_bands(self):
        core=self.load_core()
        # A planned silence (whole-silence form) plans its performance: how the line lands, how the next starts.
        bare={k:v for k,v in HELD.items() if k not in ('pause_landing','pause_resume')}
        iss=core.script_pause_plan([{'id':'L001','text':'A line.','pause_total_s':2.0,'pause_via':'edit',**bare}])[1]
        self.assertIn('pause_L001_needs_how_the_line_lands',iss)
        self.assertIn('pause_L001_needs_how_the_next_line_starts',iss)
        self.assertEqual(core.script_pause_plan([{'id':'L001','text':'A line.','pause_total_s':2.0,'pause_via':'edit',
                                                   **HELD}])[1],[])
        # The older form keeps resuming as written (nothing new asked of it).
        self.assertEqual(core.script_pause_plan([{'id':'L001','text':'A line.','pause_after_s':2.0,'pause_via':'edit',
                                                   **bare}])[1],[])
        # A delivery cue and an edit hold serve different purposes; a pause cue and an edit hold in the whole-silence
        # form are one silence, the edit adding only what the measured cue leaves.
        soft=[{'id':'L001','text':'[softly] It went quiet.','pause_total_s':2.0,'pause_via':'edit',**HELD},
              {'id':'L002','text':'Then the phone rang.'}]
        self.assertEqual(core.script_pause_plan(soft)[1],[])
        short=[{'id':'L001','text':'It went quiet. [short pause]','pause_total_s':2.0,'pause_via':'edit',**HELD},
               {'id':'L002','text':'Then the phone rang.'}]
        self.assertFalse([x for x in core.script_pause_plan(short)[1] if 'is_an_edit_hold_and_a_pause_tag_at_once' in x])
        self.assertTrue(core.script_pause_plan(short)[0][0]['residual_of_tag'])
        # Cue estimates are bands from evidence: another voice's catalogue value, a labelled assumption, this voice.
        b=core.tag_estimate('[short pause]','pause',{})
        self.assertEqual((b['low_s'],b['high_s'],b['n']),(0.75,2.25,0))
        self.assertIn('another voice',b['basis'])
        d=core.tag_estimate('[softly]','delivery',{})
        self.assertEqual((d['low_s'],d['high_s']),core.TAG_BAND_DELIVERY_S)
        m=core.tag_estimate('[short pause]','pause',{'cue_observations':[{'tag':'[short pause]','excess_s':0.9},
                                                                         {'tag':'[short pause]','excess_s':1.4}]})
        self.assertEqual((m['low_s'],m['high_s'],m['n']),(0.9,1.4,2))
        md=core.tag_estimate('[softly]','delivery',{'cue_observations':[{'tag':'[softly]','line_extra_s':0.35}]})
        self.assertEqual((md['low_s'],md['high_s']),(0.35,0.35))
        # plan-check: a delivery cue names its scope, and the forecast carries the cues as a band.
        vd=self.tagged_plan()
        res=cli('plan-check','--run',self.run,'--video',1)
        low,high=res['tag_time_range_s']
        self.assertLessEqual(low,res['tag_time_s']); self.assertGreaterEqual(high,res['tag_time_s'])
        self.assertEqual({e['tag'] for e in res['tag_estimates']},{'[curious]','[pause]'})
        self.assertTrue(any(w.startswith('L013: a pause cue at the end of the line') for w in res['warnings']))
        self.assertFalse(any(w.startswith('L001: a pause cue') for w in res['warnings']))
        script=json.loads((vd/'script.json').read_text()); script['lines'][0].pop('cue_scope'); save(vd/'script.json',script)
        self.assertIn('tag_L001_needs_its_scope',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])

    def test_cue_measured_on_the_audio_silence(self):
        """A pause cue at a line's end is measured on the silence in the audio, the basis the holds and the edit use:
        Whisper placing that one line's end late must not make the cue look like it did nothing."""
        gaps=[0.6]*12; gaps[5]=1.4
        tagged={6:{'text':'Line 6 tells the viewer something new about the road ahead tonight. [pause]',
                   'pause_total_s':1.4,'pause_via':'tag',**HELD}}
        vd,d,_=self.recorded_with_gaps(gaps,pauses=tagged)
        w=json.loads((d/'whisper/part-001.json').read_text())
        seg=next(x for x in w['segments'] if x['text'].startswith('Line 6 '))
        seg['end_s']=round(seg['end_s']+0.5,3); seg['words'][-1]['end_s']=round(seg['words'][-1]['end_s']+0.5,3)
        save(d/'whisper/part-001.json',w)
        res=cli('narration-measure','--run',self.run,'--video',1,'--no-delivery')
        m=next(x for x in res['tags_measured'] if x['line']=='L006')
        self.assertEqual(m['basis'],'audio')
        self.assertAlmostEqual(m['gap_s'],1.4,delta=0.08)
        self.assertAlmostEqual(m['excess_s'],0.8,delta=0.1)
        self.assertLess(m['words_gap_s'],1.0)                     # what Whisper's late end alone suggested
        self.assertFalse(any('made no measurable pause' in x for x in res['warnings']))
        c=next(x for x in res['cue_outcomes'] if x['line']=='L006')
        self.assertEqual((c['outcome'],c['planned_s'],c['silence_after']),('achieved',1.4,'L006'))
        vl=json.loads((self.run/'60-voice/video-01/voice-lock.json').read_text()) if (self.run/'60-voice/video-01/voice-lock.json').exists() else {}
        obs=[o for o in ((vl.get('measured') or {}).get('cue_observations') or []) if o.get('line')=='L006']
        if obs:
            self.assertAlmostEqual(obs[-1]['excess_s'],0.8,delta=0.1)

    def test_cue_results_are_judged_with_a_tolerance(self):
        """A performed pause is judged on its length, never its clock time (the user's example: 0.8 s planned, 0.78 s
        that starts half a second later is a success); a delivery cue on whether its line moved the way it asked."""
        core=self.load_core()
        self.assertEqual(core.pause_cue_outcome(0.8,0.78)['outcome'],'achieved')
        self.assertEqual(core.pause_cue_outcome(1.6,0.82)['outcome'],'short')
        self.assertEqual(core.pause_cue_outcome(1.0,1.5)['outcome'],'long')
        self.assertEqual(core.pause_cue_outcome(2.0,2.45)['tolerance_s'],0.5)          # 25 % of a longer silence
        self.assertIsNone(core.pause_cue_outcome(None,0.8))
        self.assertEqual(core.cue_poles('quietly, slowly'),{'volume':'low','tempo':'slow'})
        self.assertEqual(core.cue_poles('curious'),{})
        usual={'speech_level_db':-20.0,'speech_rate_wpm':170.0,'pitch_range_st':9.0}
        q=lambda **kw: core.delivery_cue_outcome('quietly',{**usual,**kw},usual)['outcome']
        self.assertEqual(q(speech_level_db=-22.5),'as_asked')
        self.assertEqual(q(speech_level_db=-20.4),'no_clear_change')
        self.assertEqual(q(speech_level_db=-18.0),'opposite')
        self.assertEqual(core.delivery_cue_outcome('slowly',{**usual,'speech_rate_wpm':150.0},usual)['outcome'],'as_asked')
        self.assertEqual(core.delivery_cue_outcome('deadpan',{**usual,'pitch_range_st':6.5},usual)['outcome'],'as_asked')
        self.assertEqual(core.delivery_cue_outcome('curious',usual,usual)['outcome'],'not_measured')
        self.assertEqual(core.delivery_cue_outcome('quietly',{'speech_level_db':None},usual)['outcome'],'not_measured')

    def test_parts_break_only_at_chapter_turns(self):
        core=self.load_core()
        lines=[{'id':f'L{i:03d}','text':('word '*60).strip()+'.'} for i in range(1,13)]          # ~300 characters each
        beats=[{'id':f'B{k}','line_start':3*k-2,'line_end':3*k} for k in range(1,5)]
        plain=[(p['line_start'],p['line_end']) for p in core.chunks_for_beats(lines,beats,target=700,hard_max=10000)]
        beats[0]['chapter_start']=True; beats[2]['chapter_start']=True
        parts=core.chunks_for_beats(lines,beats,target=700,hard_max=10000)
        self.assertEqual([(p['line_start'],p['line_end']) for p in parts],[(1,6),(7,12)])
        self.assertTrue(all(p['chapter'] for p in parts))
        self.assertNotEqual(plain,[(1,6),(7,12)])                    # size alone would have cut inside a chapter
        # A chapter too long for one request is split between its beats, and says so.
        big=[{'id':f'L{i:03d}','text':('word '*400).strip()+'.'} for i in range(1,13)]          # ~2,000 characters each
        parts=core.chunks_for_beats(big,beats,target=3500,hard_max=10000)
        self.assertTrue(any(p.get('split_inside_chapter') for p in parts))
        self.assertTrue(all(len(p['text'])<=10000 for p in parts))
        self.assertEqual([parts[0]['line_start'],parts[-1]['line_end']],[1,12])

    def test_join_effects_are_listed_not_judged(self):
        core=self.load_core()
        usual={'last_vowel_fall_st':-6.3,'next_reset_st':7.7}
        self.assertEqual(core.seam_boundary_effects({'last_vowel_fall_st':-6.0,'next_reset_st':8.0},usual),[])
        fx=core.seam_boundary_effects({'last_vowel_fall_st':-10.1,'next_reset_st':16.0},usual)
        self.assertEqual(len(fx),2)
        self.assertIn('ending',fx[0]); self.assertIn('fresh beginning',fx[1])
        self.assertEqual(core.seam_boundary_effects({},usual),[])

    def test_dry_run_credits_use_verified_billing(self):
        import math
        self.write_plan()
        (self.run/'logs').mkdir(exist_ok=True)
        with open(self.run/'logs/elevenlabs-ledger.jsonl','a',encoding='utf-8') as f:
            f.write(json.dumps({'kind':'tts','model_id':'eleven_v4','ok':True,'phase':'done','characters':1000,
                                'character_cost_header':400})+'\n')
        save(self.run/'logs/elevenlabs-models.json',{'fetched_at':'2026-11-22T00:00:00+00:00',
                                                      'models':{'eleven_v4':{'model_rates':{'character_cost_multiplier':1.0}}}})
        dry=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4')
        ce=dry['credit_estimate']
        self.assertEqual((ce['verified_credits_per_character'],ce['verified_requests']),(0.4,1))
        self.assertEqual(ce['expected_credits'],math.ceil(dry['characters_to_record']*0.4))
        self.assertEqual(ce['upper_bound_at_documented_rate'],dry['characters_to_record'])


class AvToolsTests(unittest.TestCase):
    """The measurements on synthetic media whose answers are known in advance."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        if str(ROOT/'scripts') not in sys.path:
            sys.path.insert(0, str(ROOT/'scripts'))
        import av_tools
        self.av = av_tools

    def frames(self):
        import numpy as np, cv2
        h, w = 180, 320
        a = np.full((h, w, 3), (40, 40, 200), np.uint8); cv2.circle(a, (160, 90), 50, (200, 60, 30), -1)
        b = np.full((h, w, 3), (40, 170, 40), np.uint8); cv2.rectangle(b, (60, 40), (260, 140), (0, 230, 230), -1)
        grad = np.tile(np.linspace(30, 220, w, dtype=np.uint8), (h, 1))
        c = cv2.merge([grad, (grad * 0.6).astype(np.uint8), (255 - grad)]); cv2.circle(c, (160, 90), 45, (250, 250, 250), -1)

        def zoom(img, s):
            ch, cw = int(h / s), int(w / s)
            y0, x0 = (h - ch) // 2, (w - cw) // 2
            return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)
        seq = [a] * 10 + [b] * 10
        seq += [cv2.addWeighted(b, 1 - k / 5, c, k / 5, 0) for k in range(1, 6)]   # a dissolve into C
        seq += [c] * 10
        seq += [zoom(c, 1 + 0.03 * k) for k in range(1, 21)]                       # a slow push-in
        last = seq[-1]
        seq += [np.full((h, w, 3), 255, np.uint8), last] + [last] * 8               # a flash
        seq += [a] * 15                                                              # back to the first picture
        out = []
        for i, img in enumerate(seq):
            p = self.dir / f'{i:04d}.png'
            cv2.imwrite(str(p), img)
            out.append((round(i * 0.2, 3), p))
        return out

    def test_picture_cuts_transitions_motion_flash_and_returns(self):
        feats = self.av.frame_features(self.frames())
        shots, kinds, _ = self.av.segment_shots(feats)
        self.assertEqual([(s['start_s'], s['begins_with']) for s in shots],
                         [(0.0, 'start'), (2.0, 'cut'), (4.4, 'transition'), (13.0, 'cut')])
        self.assertEqual(shots[3].get('same_picture_as_shot'), 1)        # A came back after 11 s
        self.assertIn('flash', kinds)                                     # the white flash is not a cut
        self.assertGreater(shots[2]['motion_share'], 0.3)                 # the push-in is motion inside a shot
        self.assertEqual(shots[0]['motion_share'], 0.0)

    def one_fps_frames(self, zoom_per_s=0.08):
        import numpy as np, cv2
        h, w = 180, 320
        def pic(bg, shape):
            im = np.full((h, w, 3), bg, np.uint8); shape(im); return im
        a = pic((40, 40, 200), lambda im: cv2.circle(im, (160, 90), 50, (200, 60, 30), -1))
        b = pic((40, 170, 40), lambda im: cv2.rectangle(im, (60, 40), (260, 140), (0, 230, 230), -1))
        c = pic((200, 200, 40), lambda im: cv2.circle(im, (80, 60), 40, (20, 20, 20), -1))
        d = pic((120, 20, 120), lambda im: cv2.rectangle(im, (20, 100), (300, 170), (240, 240, 240), -1))
        e = pic((20, 90, 160), lambda im: cv2.circle(im, (240, 120), 45, (0, 255, 255), -1))
        grad = np.tile(np.linspace(30, 220, w, dtype=np.uint8), (h, 1))
        f = cv2.merge([grad, (grad * 0.6).astype(np.uint8), (255 - grad)]); cv2.circle(f, (160, 90), 45, (250, 250, 250), -1)
        def zoom(img, s):
            ch, cw = int(h / s), int(w / s); y0, x0 = (h - ch) // 2, (w - cw) // 2
            return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)
        seq = [a] * 4 + [b] * 3                      # a cut at 4 s
        seq += [c, d] + [e] * 3                       # two pictures of one second each: a quick series of cuts
        seq += [cv2.addWeighted(e, .5, f, .5, 0)] + [f] * 3      # a dissolve, caught in one sample
        seq += [zoom(f, 1 + zoom_per_s * k) for k in range(1, 7)]  # a push-in, six seconds
        seq += [a] * 3                                # back to the first picture
        out = []
        for i, img in enumerate(seq):
            p = self.dir / f'one-{i:04d}.png'; cv2.imwrite(str(p), img); out.append((float(i), p))
        return out

    def two_fps_frames(self, zoom_per_s=0.08):
        import numpy as np, cv2
        h, w = 180, 320
        def pic(bg, shape):
            im = np.full((h, w, 3), bg, np.uint8); shape(im); return im
        a = pic((40, 40, 200), lambda im: cv2.circle(im, (160, 90), 50, (200, 60, 30), -1))
        b = pic((40, 170, 40), lambda im: cv2.rectangle(im, (60, 40), (260, 140), (0, 230, 230), -1))
        c = pic((200, 200, 40), lambda im: cv2.circle(im, (80, 60), 40, (20, 20, 20), -1))
        d = pic((120, 20, 120), lambda im: cv2.rectangle(im, (20, 100), (300, 170), (240, 240, 240), -1))
        e = pic((20, 90, 160), lambda im: cv2.circle(im, (240, 120), 45, (0, 255, 255), -1))
        grad = np.tile(np.linspace(30, 220, w, dtype=np.uint8), (h, 1))
        f = cv2.merge([grad, (grad * 0.6).astype(np.uint8), (255 - grad)]); cv2.circle(f, (160, 90), 45, (250, 250, 250), -1)
        def zoom(img, s):
            ch, cw = int(h / s), int(w / s); y0, x0 = (h - ch) // 2, (w - cw) // 2
            return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)
        seq = [a] * 8 + [b] * 6                       # a cut at 4 s
        seq += [c, d] + [e] * 6                       # two pictures of half a second each: a quick series of cuts
        seq += [cv2.addWeighted(e, .5, f, .5, 0)] + [f] * 6       # a dissolve, caught in one sample
        seq += [zoom(f, 1 + zoom_per_s * 0.5 * k) for k in range(1, 13)]   # a push-in, six seconds
        seq += [a] * 6                                # back to the first picture
        out = []
        for i, img in enumerate(seq):
            p = self.dir / f'two-{i:04d}.png'; cv2.imwrite(str(p), img); out.append((i * 0.5, p))
        return out

    def test_two_frames_per_second_reads_the_same_edits(self):
        feats = self.av.frame_features(self.two_fps_frames())
        shots, kinds, _ = self.av.segment_shots(feats)
        self.assertEqual([(s['start_s'], s['begins_with']) for s in shots],
                         [(0.0, 'start'), (4.0, 'cut'), (7.0, 'cut'), (7.5, 'cut'), (8.0, 'cut'), (11.5, 'transition'),
                          (20.5, 'cut')])
        self.assertEqual(shots[-1].get('same_picture_as_shot'), 1)
        self.assertGreater(shots[5]['motion_share'], 0.5)                  # the push-in moves inside its shot
        self.assertEqual([self.av.transition_pairs(0.5)], [3])
        self.assertAlmostEqual(self.av.motion_diff(0.5), 1.19, delta=0.01)
        slow = self.av.segment_shots(self.av.frame_features(self.two_fps_frames(zoom_per_s=0.03)))[0]
        self.assertEqual(slow[5]['motion_share'], 0.0)                     # 3 % a second reads as still, as at 5 fps
        # what the samples cannot settle is listed for a closer look: the quick series and the dissolve
        cands = self.av.inspect_candidates(feats, kinds, shots)
        self.assertEqual([(c['from_s'], c['to_s']) for c in cands], [(6.5, 8.0), (10.5, 11.5)])
        self.assertIn('cut series', cands[0]['why'])
        self.assertEqual(cands[1]['why'], 'transition')
        prof = self.av.profile('two', 25.0, self.two_fps_frames(), None, [], sampler=self.av.SAMPLER)
        self.assertEqual((prof['sampled_fps'], prof['sampler'], len(prof['inspect_candidates'])), (2.0, 'pts-v1', 2))

    def test_one_frame_per_second_reads_the_same_edits(self):
        feats = self.av.frame_features(self.one_fps_frames())
        shots, kinds, _ = self.av.segment_shots(feats)
        self.assertEqual([(s['start_s'], s['begins_with']) for s in shots],
                         [(0.0, 'start'), (4.0, 'cut'), (7.0, 'cut'), (8.0, 'cut'), (9.0, 'cut'), (13.0, 'transition'),
                          (22.0, 'cut')])
        self.assertEqual(shots[-1].get('same_picture_as_shot'), 1)
        self.assertGreater(shots[5]['motion_share'], 0.5)                  # the push-in moves inside its shot
        # the same definitions at any rate: a transition lasts up to 1.6 s, a move is a speed of change
        self.assertEqual([self.av.transition_pairs(1 / r) for r in (5, 1)], [8, 2])
        self.assertEqual(self.av.motion_diff(0.2), 0.6)
        self.assertAlmostEqual(self.av.motion_diff(1.0), 2.0, delta=0.01)
        slow = self.av.segment_shots(self.av.frame_features(self.one_fps_frames(zoom_per_s=0.03)))[0]
        self.assertEqual(slow[5]['motion_share'], 0.0)                     # 3 % a second reads as still, as at 5 fps
        prof = self.av.profile('one', 25.0, self.one_fps_frames(), None, [])
        self.assertEqual((prof['sampled_fps'], prof['summary']['picture']['sampled_fps']), (1.0, 1.0))
        self.assertEqual(prof['thresholds']['transition_max_frame_pairs'], 2)

    def wav_and_words(self):
        import numpy as np, soundfile as sf
        sr = 16000
        y = np.zeros(int(18 * sr), np.float32)
        rng = np.random.default_rng(7)

        def tone(f0, dur, amp):
            t = np.arange(int(dur * sr)) / sr
            return (amp * (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(4 * np.pi * f0 * t) + .25 * np.sin(6 * np.pi * f0 * t)) / 1.75).astype(np.float32)
        words, t = [], 0.2
        for i in range(12):                                  # flat: one pitch, one level, short gaps
            seg = tone(120, 0.4, 0.5); y[int(t * sr):int(t * sr) + len(seg)] = seg
            words.append({'start_s': round(t, 3), 'end_s': round(t + 0.4, 3), 'text': f' flat{i}'}); t += 0.5
        t = 7.8                                              # 1.7 s of silence first
        f0s = [100, 170, 110, 190, 105, 180, 115, 200, 100, 175, 120, 185]
        for i in range(12):                                  # expressive: pitch and level move; a quiet bed in the gaps
            seg = tone(f0s[i], 0.35, [0.15, 0.8][i % 2]); y[int(t * sr):int(t * sr) + len(seg)] = seg
            words.append({'start_s': round(t, 3), 'end_s': round(t + 0.35, 3), 'text': f' move{i}'})
            g0, g1 = int((t + 0.35) * sr), int((t + 0.8) * sr)
            y[g0:g1] = (rng.uniform(-0.05, 0.05, g1 - g0)).astype(np.float32)
            t += 0.8
        wav = self.dir / 'voice.wav'
        sf.write(str(wav), y, sr)
        return wav, words

    def test_narration_delivery_and_the_level_under_the_voice(self):
        wav, words = self.wav_and_words()
        audio = self.av.audio_features(wav, words)
        flat = self.av.span_stats(words, audio, 0, 6.2)
        moving = self.av.span_stats(words, audio, 7.8, 18)
        self.assertLess(flat['pitch_range_st'], 1.0)
        self.assertGreater(moving['pitch_range_st'], 6.0)
        self.assertLess(flat['loudness_contrast_db'], 1.0)
        self.assertGreater(moving['loudness_contrast_db'], 3.0)
        silent = [g['rel_db'] for g in audio['gaps'] if g['start_s'] < 7]
        bed = [g['rel_db'] for g in audio['gaps'] if g['start_s'] > 7]
        self.assertTrue(silent and bed)
        self.assertLess(max(silent), -60)
        self.assertGreater(min(bed), -40)
        # One yardstick: the narration-only delivery and a full profile read the same numbers.
        prof = self.av.profile('x', audio['duration_s'], None, wav, words)
        self.assertEqual(prof['summary']['narration'], self.av.delivery('x', wav, words)['summary'])

    def test_watch_sheet_shows_frames_with_their_words(self):
        from PIL import Image
        frames = self.frames()
        words = [{'start_s': 0.5 + i, 'end_s': 0.9 + i, 'text': f' w{i}'} for i in range(15)]
        prof = self.av.profile('demo', 16.0, frames, None, words, sheets_dir=self.dir / 'sheets')
        self.assertEqual(len(prof['sheets']), 1)
        with Image.open(prof['sheets'][0]) as im:
            self.assertEqual(im.size, (4 * 320, 34 + 3 * (180 + 82)))
        self.assertIn('w0', prof['windows'][0]['said'])


class WhisperGpuTests(unittest.TestCase):
    """Whisper medium on the GPU through the pipeline's own code and interpreter, on real speech (Windows' built-in
    voice, offline, no credits). A PC without a working GPU fails these tests: the pipeline needs one."""
    SENTENCE = 'The river froze before the first patrol came back. Seven trucks waited at the bridge until morning.'

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.wav = cls.dir / 'speech.wav'
        ps = shutil.which('powershell.exe') or shutil.which('powershell')
        if not ps:
            raise unittest.SkipTest('no Windows speech voice to make the test sentence')
        cmd = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
               f"$s.SetOutputToWaveFile('{cls.wav}'); $s.Speak('{cls.SENTENCE}'); $s.Dispose()")
        subprocess.run([ps, '-NoProfile', '-Command', cmd], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def words_of(text):
        import re
        return re.findall(r"[a-z]+", text.lower())

    def test_the_production_interpreter_runs_whisper_medium_on_the_gpu(self):
        py = shutil.which('python')
        self.assertTrue(py and os.path.samefile(py, sys.executable), (py, sys.executable))   # the one create-video runs
        r = subprocess.run([py, str(TOOL), 'doctor', '--whisper', '--file', str(self.wav)], capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0, out)
        w, f = out['checks']['whisper'], out['checks']['whisper_file']
        self.assertEqual((w['model'], w['device'], w['compute_type'], f['device']), ('medium', 'cuda', 'float16', 'cuda'))
        self.assertTrue(w['gpu'])
        self.assertEqual(self.words_of(f['first_words']), self.words_of(self.SENTENCE))
        self.assertGreater(f['realtime_x'], 1.0)

    def test_word_times_from_the_gpu_are_in_order_and_inside_the_audio(self):
        spec = importlib.util.spec_from_file_location('static_core_gpu', TOOL)
        core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
        out = self.dir / 'transcript.json'
        core.transcribe(self.wav, out, 'medium', 'cuda', 'float16')
        tj = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual((tj['engine']['device'], tj['engine']['compute_type'], tj['model']), ('cuda', 'float16', 'medium'))
        words = [w for s in tj['segments'] for w in s['words']]
        self.assertEqual(self.words_of(' '.join(w['text'] for w in words)), self.words_of(self.SENTENCE))
        starts = [w['start_s'] for w in words]
        self.assertEqual(starts, sorted(starts))
        self.assertTrue(all(0 <= w['start_s'] <= w['end_s'] <= tj['duration_s'] + 0.05 for w in words))
        self.assertLess(starts[0], 1.0)
        for s in tj['segments']:
            self.assertLessEqual(s['start_s'], s['words'][0]['start_s'] + 0.05)
            self.assertGreaterEqual(s['end_s'] + 0.05, s['words'][-1]['end_s'])

    def test_no_gpu_stops_with_its_cause_and_never_uses_the_cpu(self):
        hidden = {**os.environ, 'CUDA_VISIBLE_DEVICES': '-1'}
        r = subprocess.run([sys.executable, str(TOOL), 'doctor', '--whisper'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=hidden)
        self.assertEqual(r.returncode, 2)
        err = json.loads(r.stdout)['error']
        self.assertIn('sees no CUDA device', err)
        self.assertIn('Nothing was transcribed', err)
        # The reference-processing stage: the same stop, and no transcript written.
        refs = self.dir / 'refs'; refs.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=64x36:r=10',
                        '-i', str(self.wav), '-t', '3', '-shortest', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                        str(refs / 'talk.mp4')], check=True)
        run = Path(cli('init', '--references', refs, '--workspace', self.dir / 'runs', '--slug', 'gpu')['run'])
        cli('scan', '--run', run)
        r = subprocess.run([sys.executable, str(TOOL), 'prepare', '--run', str(run), '--ids', 'V001'], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', env=hidden)
        self.assertEqual(r.returncode, 2)
        self.assertIn('sees no CUDA device', json.loads(r.stdout)['failed'][0]['error'])
        self.assertFalse((run / '10-media/V001/transcript.json').exists())
        self.assertTrue((run / '10-media/V001/frame-index.json').is_file())              # the frames were still made
        # The CPU only on the user's explicit word; another model never.
        r = subprocess.run([sys.executable, str(TOOL), 'prepare', '--run', str(run), '--ids', 'V001', '--device', 'cpu'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(r.returncode, 2)
        self.assertIn('explicitly says so', json.loads(r.stdout)['error'])
        r = subprocess.run([sys.executable, str(TOOL), 'prepare', '--run', str(run), '--whisper-model', 'small'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(r.returncode, 2)
        self.assertIn('invalid choice', r.stderr)
        spec = importlib.util.spec_from_file_location('static_core_cpu', TOOL)
        core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
        seen = []
        def fake(path, outpath, *a):
            seen.append(a)
            Path(outpath).write_text(json.dumps({'status': 'transcribed', 'segments': []}), encoding='utf-8')
            Path(outpath).with_suffix('.txt').write_text('', encoding='utf-8')
            return 0
        with mock.patch.object(core, 'transcribe', side_effect=fake), mock.patch.object(sys, 'argv', [
                'static_core.py', 'prepare', '--run', str(run), '--ids', 'V001', '--device', 'cpu',
                '--cpu-approved', 'the user said: use the CPU for this run']), \
                mock.patch('sys.stdout', new_callable=io.StringIO):
            try:
                core.main()
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertEqual(seen, [('medium', 'cpu', 'int8')])
        self.assertEqual(core._CPU_APPROVAL, 'the user said: use the CPU for this run')


class TimelineWriteTests(unittest.TestCase):
    """timeline-write: timeline.json from the saved CapCut project, each clip traced, nothing guessed (manual 05)."""

    def test_clips_traced_to_shots_stills_beds_and_named_sounds(self):
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)/'run'
            vis = rd/'60-visuals/video-01'
            (vis/'stills').mkdir(parents=True)
            for sid in ('S001', 'S002'):
                (vis/'stills'/f'{sid}.png').write_bytes(b'png')
            save(rd/'state.json', {'schema': 'static-youtube-longform-v1', 'run': 'r'})
            save(vis/'shot-plan.json', {'shots': [{'id': 'S001', 'beat_id': 'B01', 'new_thing': 'the house'},
                                                  {'id': 'S002', 'beat_id': 'B01', 'new_thing': 'the message'},
                                                  {'id': 'S003', 'beat_id': 'B02', 'reuses': 'S001', 'new_thing': 'the house again'}]})
            narr = rd/'50-audio/video-01/narration-edit.wav'; narr.parent.mkdir(parents=True); narr.write_bytes(b'wav')
            bed = rd/'70-edit/video-01/music/M1.wav'; bed.parent.mkdir(parents=True); bed.write_bytes(b'wav')
            tap = rd/'50-audio/sfx/tap.wav'; tap.parent.mkdir(parents=True); tap.write_bytes(b'wav')
            save(rd/'70-edit/video-01/edit-plan.json', {'narration_for_edit': {'file': str(narr)},
                 'shots': [{'id': 'S001', 'beat_id': 'B01', 'start_s': 0.0, 'end_s': 4.0},
                           {'id': 'S002', 'beat_id': 'B01', 'start_s': 4.0, 'end_s': 8.0},
                           {'id': 'S003', 'beat_id': 'B02', 'start_s': 8.0, 'end_s': 12.0}]})
            save(rd/'70-edit/video-01/music-provenance.json',
                 {'tracks': {os.path.normcase(str(bed.resolve())): {'beats': ['B01', 'B02']}}})
            us = lambda a, b: {'start': int(a * 1e6), 'duration': int((b - a) * 1e6)}
            draft = Path(td)/'draft'
            save(draft/'draft_content.json', {'canvas_config': {'width': 1920, 'height': 1080}, 'fps': 30,
                 'materials': {'videos': [{'id': 'v1', 'path': str(vis/'stills/S001.png').replace(chr(92), '/')},
                                          {'id': 'v2', 'path': str(vis/'stills/S002.png')},
                                          {'id': 'v3', 'path': str(vis/'stills/S002.png')}],
                               'audios': [{'id': 'a1', 'path': str(narr)}, {'id': 'a2', 'path': str(bed)},
                                          {'id': 'a3', 'path': str(tap)}, {'id': 'a4', 'path': str(Path(td)/'stray.wav')}]},
                 'tracks': [{'type': 'video', 'segments': [
                                {'id': 's1', 'material_id': 'v1', 'target_timerange': us(0, 4), 'source_timerange': us(0, 4)},
                                {'id': 's2', 'material_id': 'v2', 'target_timerange': us(4, 8), 'source_timerange': us(0, 4)},
                                {'id': 's3', 'material_id': 'v3', 'target_timerange': us(8, 12), 'source_timerange': us(0, 4)}]},
                            {'type': 'audio', 'segments': [
                                {'id': 'n', 'material_id': 'a1', 'target_timerange': us(0, 12), 'source_timerange': us(0, 12), 'speed': 1},
                                {'id': 'm', 'material_id': 'a2', 'target_timerange': us(1, 11), 'source_timerange': us(0, 10)},
                                {'id': 't', 'material_id': 'a3', 'target_timerange': us(2, 3), 'source_timerange': us(0, 1)},
                                {'id': 'x', 'material_id': 'a4', 'target_timerange': us(5, 6), 'source_timerange': us(0, 1)}]}]})
            sounds = Path(td)/'sounds.json'
            save(sounds, {'tap.wav': {'kind': 'sfx', 'beats': ['B01'], 'purpose': 'the key'}})
            out = cli('timeline-write', '--run', rd, '--video', 1, '--draft', draft, '--sounds', sounds, expected=2)
            tl = json.loads((rd/'70-edit/video-01/timeline.json').read_text(encoding='utf-8'))
            self.assertEqual([v['shot_id'] for v in tl['visual_segments']], ['S001', 'S002', 'S003'])
            kinds = [a['kind'] for a in tl['audio_tracks']]
            self.assertEqual(kinds, ['narration', 'music', 'sfx'])
            self.assertEqual(tl['audio_tracks'][1]['beats'], ['B01', 'B02'])
            self.assertEqual(tl['capcut_draft'], str(draft))
            # the callback S003 shows S002's still instead of S001's, and a sound nobody named: both reported, not guessed
            self.assertTrue(any(p.startswith('S003: the clip shows') for p in out['problems']), out['problems'])
            self.assertTrue(any('stray.wav' in p for p in out['problems']), out['problems'])


class ExportBindingTests(unittest.TestCase):
    """An export is held to the CapCut project it was made from (remediation 2026-11-24): timeline-check records what
    the saved project shows; export-check holds the export to it and records the file by its full sha256; release-check
    needs that record for the exact file, the master, and the project unchanged since."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('static_studio_core_eb', TOOL)
        cls.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.core)

    def ff(self, *args):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True)

    def still(self, path, seed):
        import numpy as np, cv2
        rng = np.random.default_rng(seed)
        img = np.full((1080, 1920, 3), 235, np.uint8)
        for _ in range(60):         # a picture with plenty of corners: keypoints to find it again
            x, y = int(rng.integers(0, 1800)), int(rng.integers(0, 980))
            col = tuple(int(c) for c in rng.integers(0, 200, 3))
            if rng.random() < 0.5:
                cv2.rectangle(img, (x, y), (x + int(rng.integers(30, 220)), y + int(rng.integers(30, 160))), col, -1)
            else:
                cv2.circle(img, (x, y), int(rng.integers(15, 90)), col, int(rng.integers(3, 12)))
        cv2.imencode('.png', img)[1].tofile(str(path))

    def export(self, out, order, size='1920x1080', black_at=None):
        """An mp4 of the stills in `order`, 4 s each, with the narration as its sound (and, optionally, 1.5 s of black)."""
        w, h = size.split('x')
        parts = []
        for i, f in enumerate(order):
            seg = self.td / f'seg{i}-{out.stem}.mp4'
            self.ff('-loop', 1, '-t', 4, '-i', f, '-vf', f'scale={w}:{h},fps=30,format=yuv420p', '-c:v', 'libx264',
                    '-preset', 'ultrafast', seg)
            parts.append(seg)
        lst = self.td / f'list-{out.stem}.txt'
        lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts), encoding='utf-8')
        vf = (f'drawbox=enable=between(t\\,{black_at}\\,{black_at + 1.5}):x=0:y=0:w=iw:h=ih:color=black:t=fill'
              if black_at is not None else 'null')
        self.ff('-f', 'concat', '-safe', 0, '-i', lst, '-i', self.narr, '-vf', vf, '-c:v', 'libx264', '-preset',
                'ultrafast', '-c:a', 'aac', '-shortest', out)
        return out

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.td = Path(self._t.name)
        rd = self.rd = self.td / 'run'
        vis = rd / '60-visuals/video-01'
        (vis / 'stills').mkdir(parents=True)
        self.stills = []
        for i, sid in enumerate(('S001', 'S002', 'S003')):
            p = vis / 'stills' / f'{sid}.png'
            self.still(p, 11 + i)
            self.stills.append(p)
        save(rd / 'state.json', {'schema': self.core.SCHEMA, 'run_id': 'r',
                                 'format': {'width': 1920, 'height': 1080, 'fps': 30}})
        save(vis / 'shot-plan.json', {'shots': [{'id': f'S00{i}', 'beat_id': 'B01', 'new_thing': 'a new thing here'}
                                                for i in (1, 2, 3)]})
        save(rd / '40-plans/video-01/length-lock.json', {'target_length_s': 12, 'tolerance_export_pct': 0.025})
        self.narr = rd / '50-audio/video-01/narration-edit.wav'
        self.narr.parent.mkdir(parents=True)
        # a voice-like sound: bursts of tone with short gaps, 12 s (the narration_in_mix envelope needs speech-like shape)
        self.ff('-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=44100:duration=12', '-af',
                "volume='if(lt(mod(t,1.2),0.9),1,0.02)':eval=frame", '-ac', 1, self.narr)
        self.plan = {'narration_for_edit': {'file': str(self.narr)}, 'pauses': [],
                     'shots': [{'id': f'S00{i}', 'beat_id': 'B01', 'start_s': (i - 1) * 4.0, 'end_s': i * 4.0}
                               for i in (1, 2, 3)]}
        save(rd / '70-edit/video-01/edit-plan.json', self.plan)
        us = lambda a, b: {'start': int(a * 1e6), 'duration': int((b - a) * 1e6)}
        self.draft = self.td / 'draft'
        self.content = {'canvas_config': {'width': 1920, 'height': 1080}, 'fps': 30,
            'materials': {'videos': [{'id': f'v{i}', 'path': str(p).replace(chr(92), '/')} for i, p in enumerate(self.stills, 1)],
                          'audios': [{'id': 'a1', 'path': str(self.narr)}],
                          'texts': [{'id': 't1', 'content': '{"text":"first words"}'}]},
            'tracks': [{'type': 'video', 'segments': [{'id': f's{i}', 'material_id': f'v{i}', 'target_timerange': us((i - 1) * 4, i * 4),
                                                       'source_timerange': us(0, 4)} for i in (1, 2, 3)]},
                       {'type': 'audio', 'segments': [{'id': 'n', 'material_id': 'a1', 'target_timerange': us(0, 12),
                                                       'source_timerange': us(0, 12), 'speed': 1}]},
                       {'type': 'text', 'segments': [{'id': 'tx', 'material_id': 't1', 'target_timerange': us(0.5, 2)}]}]}
        save(self.draft / 'draft_content.json', self.content)
        cli('timeline-write', '--run', rd, '--video', 1, '--draft', self.draft)
        # timeline-check's record of the checked project (here written as a passed check would write it)
        snap = self.core.project_snapshot(rd, 1, self.draft)
        save(self.core.timeline_check_path(rd, 1), {'checked_at': self.core.now(), 'draft': str(self.draft),
                                                    'snapshot_sha256': self.core.canonical_sha(snap), 'snapshot': snap})

    def tearDown(self):
        self._t.cleanup()

    def issues(self, f, deep=True):
        with mock.patch('sys.stdout', new_callable=io.StringIO):
            return self.core.export_facts(self.rd, 1, f, deep=deep)

    def test_a_snapshot_ignores_capcuts_frame_snapping_but_not_a_real_change(self):
        a = self.core.project_snapshot(self.rd, 1, self.draft)
        c = json.loads(json.dumps(self.content))
        c['tracks'][0]['segments'][1]['target_timerange']['start'] += 30000          # a CapCut re-save: 0.03 s
        save(self.draft / 'draft_content.json', c)
        self.assertEqual(self.core.project_changes(a, self.core.project_snapshot(self.rd, 1, self.draft)), [])
        # the real CapCut desktop re-saves a project it opened with its frame rate as 30.0 (2026-11-24): the same project
        c['fps'] = 30.0
        save(self.draft / 'draft_content.json', c)
        self.assertEqual(self.core.project_changes(a, self.core.project_snapshot(self.rd, 1, self.draft)), [])
        c['fps'] = 25
        save(self.draft / 'draft_content.json', c)
        self.assertEqual(self.core.project_changes(a, self.core.project_snapshot(self.rd, 1, self.draft)), ['fps 30 -> 25'])
        c['fps'] = 30
        c['tracks'][0]['segments'][0]['material_id'], c['tracks'][0]['segments'][1]['material_id'] = 'v2', 'v1'
        save(self.draft / 'draft_content.json', c)
        self.assertTrue(self.core.project_changes(a, self.core.project_snapshot(self.rd, 1, self.draft)))
        c = json.loads(json.dumps(self.content)); c['materials']['texts'][0]['content'] = '{"text":"other words"}'
        save(self.draft / 'draft_content.json', c)
        self.assertTrue(any(x.startswith('texts 1') for x in
                            self.core.project_changes(a, self.core.project_snapshot(self.rd, 1, self.draft))))

    def test_the_export_is_held_to_its_checked_project(self):
        good = self.export(self.td / 'good.mp4', self.stills)
        res = self.issues(good)
        mine = [x for x in res['issues'] if not x.startswith('audio_gate')]
        self.assertEqual(mine, [], res['issues'])
        self.assertEqual(res['pictures']['found'], 3)
        self.assertEqual(res['narration_in_export']['weak_windows'], [])
        # the project changed after its check: the export no longer answers for it
        c = json.loads(json.dumps(self.content))
        c['tracks'][0]['segments'][0]['material_id'], c['tracks'][0]['segments'][1]['material_id'] = 'v2', 'v1'
        save(self.draft / 'draft_content.json', c)
        self.assertTrue(any(x.startswith('project_changed_since_its_timeline_check') for x in self.issues(good, deep=False)['issues']))
        save(self.draft / 'draft_content.json', self.content)
        # an export whose pictures are in another order than the checked project
        wrong = self.export(self.td / 'wrong.mp4', [self.stills[1], self.stills[0], self.stills[2]])
        self.assertTrue(any(x.startswith('export_shows_another_picture_than_the_project_at') for x in self.issues(wrong)['issues']))
        # the run's size, exactly (a smaller review copy is not the master)
        small = self.export(self.td / 'small.mp4', self.stills, size='1280x720')
        self.assertIn('export_size_1280x720_is_not_the_runs_1920x1080', self.issues(small, deep=False)['issues'])

    def test_black_or_silence_blocks_unless_the_plan_holds_it(self):
        dark = self.export(self.td / 'dark.mp4', self.stills, black_at=5.0)
        self.assertTrue(any(x.startswith('export_black_') for x in self.issues(dark)['issues']))
        save(self.core.planned_blanks_path(self.rd, 1),
             {'blanks': [{'from_s': 4.9, 'to_s': 6.6, 'kind': 'black', 'why': 'a deliberate cut to black before the turn'}]})
        self.assertFalse(any(x.startswith('export_black_') for x in self.issues(dark)['issues']))
        rows = ['[silencedetect @ 0] silence_start: 3.0', '[silencedetect @ 0] silence_end: 6.0 | silence_duration: 3.0']
        self.assertEqual(self.core._blank_spans(rows, 'silence', 12), [(3.0, 6.0)])
        self.assertEqual(self.core._blank_spans(['[silencedetect] silence_start: 10.5'], 'silence', 12), [(10.5, 12.0)])

    def test_release_needs_this_exact_file_deep_checked_and_mastered(self):
        good = self.export(self.td / 'good.mp4', self.stills)
        rel = cli('release-check', '--run', self.rd, '--video', 1, '--file', good, expected=2)['issues']
        self.assertIn('export:not_checked_as_this_exact_file:run_export-check_--deep_on_it', rel)
        self.assertIn('export:not_mastered:run_master-sound_and_release_the_mastered_file', rel)
        cli('export-check', '--run', self.rd, '--video', 1, '--file', good, '--deep', expected=2)   # other gates fail here
        prov = json.loads(self.core.export_provenance_path(self.rd, 1).read_text(encoding='utf-8'))
        (sha, rec), = prov['exports'].items()
        self.assertEqual((rec['sha256'], rec['deep']), (self.core.file_sha256(good), True))
        self.assertEqual(rec['project']['draft'], str(self.draft))
        save(self.rd / '80-deliverables/video-01/master.json', {'export': {'sha256': 'x'}, 'mastered': {'sha256': sha}})
        rel = cli('release-check', '--run', self.rd, '--video', 1, '--file', good, expected=2)['issues']
        self.assertFalse(any(x.startswith(('export:not_checked_as_this_exact_file', 'export:not_mastered',
                                           'export:this_file_is_not_the_recorded_master')) for x in rel), rel)
        # a different file of the same project is not the one that was checked
        other = self.export(self.td / 'other.mp4', self.stills, black_at=1.0)
        rel = cli('release-check', '--run', self.rd, '--video', 1, '--file', other, expected=2)['issues']
        self.assertIn('export:not_checked_as_this_exact_file:run_export-check_--deep_on_it', rel)
        # the project changed after the export was checked
        c = json.loads(json.dumps(self.content)); c['materials']['texts'][0]['content'] = '{"text":"changed later"}'
        save(self.draft / 'draft_content.json', c)
        rel = cli('release-check', '--run', self.rd, '--video', 1, '--file', good, expected=2)['issues']
        self.assertTrue(any(x.startswith('export:the_project_changed_after_this_export_was_checked') for x in rel), rel)


class BedLevelsTests(unittest.TestCase):
    """bed-levels: "under_speech_db" N means N dB quieter than the narration, by the same loudness meter (2026-11-22)."""

    def test_a_bed_lands_the_asked_number_of_db_under_the_voice(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            for name, vol in (('voice.wav', 0.5), ('bed.wav', 0.5), ('soft.wav', 0.005)):
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                                f'sine=frequency=440:duration=4,volume={vol}', str(t/name)], check=True)
            save(t/'plan.json', {'narration': str(t/'voice.wav'),
                                 'tracks': [{'id': 'bed', 'file': str(t/'bed.wav'), 'under_speech_db': 20},
                                            {'id': 'soft', 'file': str(t/'soft.wav'), 'under_speech_db': 10}]})
            out = cli('bed-levels', '--plan', t/'plan.json', '--out', t/'levels.json')
            rows = {r['id']: r for r in out['tracks']}
            self.assertAlmostEqual(rows['bed']['gain_db'], -20.0, delta=0.3)     # as loud as the voice: 20 dB down
            self.assertAlmostEqual(rows['bed']['volume'], 0.1, delta=0.01)
            self.assertEqual(rows['soft']['volume'], 1.0)                       # 40 dB down already: needs gain, capped
            self.assertIn('note', rows['soft'])
            self.assertTrue((t/'levels.json').is_file())


class BedBakeTests(unittest.TestCase):
    """bed-levels --bake: the bed as it must play lives in its file (stretch, gain, fades), recorded against its source."""

    def test_baked_copy_lands_under_the_voice_and_keeps_the_beds_record(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            rd = t/'run'
            save(rd/'state.json', {'schema': 'static-youtube-longform-v1'})
            mus = rd/'70-edit/video-01/music'; mus.mkdir(parents=True)
            for name, vol, d in (('voice.wav', 0.5, 6), ('M1.wav', 0.5, 6)):
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                                f'sine=frequency=440:duration={d},volume={vol}', str((mus if name == 'M1.wav' else t)/name)], check=True)
            save(rd/'70-edit/video-01/music-provenance.json',
                 {'video': 1, 'tracks': {os.path.normcase(str((mus/'M1.wav').resolve())): {'beats': ['B01'], 'production_rev': 3}}})
            save(t/'plan.json', {'narration': str(t/'voice.wav'),
                                 'tracks': [{'id': 'M1', 'file': str(mus/'M1.wav'), 'under_speech_db': 20,
                                             'src_start': 1.0, 'dur': 4.0, 'fade_in': 0.2, 'fade_out': 0.5}]})
            out = cli('bed-levels', '--plan', t/'plan.json', '--bake', mus, '--run', rd, '--video', 1)
            row = out['tracks'][0]
            baked = Path(row['baked']['file'])
            self.assertTrue(baked.is_file())
            self.assertEqual(row['volume_in_project'], 1.0)
            r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(baked)],
                               capture_output=True, text=True)
            self.assertAlmostEqual(float(r.stdout), 4.0, delta=0.05)                     # its stretch only
            save(t/'check.json', {'narration': str(t/'voice.wav'), 'tracks': [{'id': 'b', 'file': str(baked), 'under_speech_db': 0}]})
            chk = cli('bed-levels', '--plan', t/'check.json')
            self.assertAlmostEqual(chk['tracks'][0]['file_lufs'] - chk['speech_lufs'], -20.0, delta=1.0)   # 20 dB under the voice
            prov = json.loads((rd/'70-edit/video-01/music-provenance.json').read_text(encoding='utf-8'))['tracks']
            rec = prov[os.path.normcase(str(baked.resolve()))]
            self.assertEqual(rec['beats'], ['B01'])
            self.assertEqual(rec['production_rev'], 3)
            self.assertEqual(rec['derivation']['src_start_s'], 1.0)


class RecheckWordsTests(unittest.TestCase):
    """A line heard whole on its second listen keeps that listen's word times (2026-11-22, L013)."""

    def test_second_listen_word_times_replace_a_sparse_long_pass(self):
        spec = importlib.util.spec_from_file_location('static_core_recheck', TOOL)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        row = {'_tok': [(66.2, 66.5), (66.5, 66.7), (66.7, 67.2), (71.8, 72.4), None, None, None], 'matched_words': 4}
        rec = {'tok_times': [[23.9, 24.1], [24.1, 24.4], [24.4, 24.9], [25.6, 25.8], [25.8, 26.1], [26.1, 26.5], [27.0, 27.4]]}
        self.assertEqual(core.merge_recheck_words(row, rec, 42.4), 7)
        self.assertAlmostEqual(row['_tok'][3][0], 68.0)
        self.assertTrue(row['words_from_recheck'])
        # a second listen that heard fewer words, or other words than the line has, changes nothing
        row2 = {'_tok': [(1.0, 1.2), (1.2, 1.4)], 'matched_words': 2}
        self.assertEqual(core.merge_recheck_words(row2, {'tok_times': [[0.1, 0.2], None]}, 0.0), 0)
        self.assertEqual(core.merge_recheck_words(row2, {'tok_times': [[0.1, 0.2]]}, 0.0), 0)
        self.assertEqual(row2['_tok'], [(1.0, 1.2), (1.2, 1.4)])


class SqueezedCaptionTests(unittest.TestCase):
    """captions-plan names runs of words that would flash by unread (2026-11-22, L013)."""

    def test_three_or_more_short_words_of_one_line_in_a_row_are_named(self):
        spec = importlib.util.spec_from_file_location('static_core_squeeze', TOOL)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        w = lambda t, s, e, line='L013': {'w': t, 's': s, 'e': e, 'line': line}
        words = [w('They', 67.98, 68.26), w('said', 68.26, 68.5), w('again.', 74.19, 74.25), w('No.', 74.25, 74.29),
                 w('He', 74.29, 74.31), w('tried', 74.31, 74.36), w('Next', 75.0, 75.3, 'L014')]
        runs = core.squeezed_runs(words)
        self.assertEqual([(r['line'], r['words'], r['from_s'], r['to_s']) for r in runs], [('L013', 4, 74.19, 74.36)])
        # two short words, or short words split across two lines, are not a run
        self.assertEqual(core.squeezed_runs(words[:4]), [])
        self.assertEqual(core.squeezed_runs([w('a', 1.0, 1.02), w('b', 1.02, 1.04), w('c', 1.04, 1.06, 'L014')]), [])


class StartWordTests(unittest.TestCase):
    """A cut on a word inside a line (shot-plan start_word), 2026-11-22: the final review asked five times for a cut on a
    word, which line-only cuts could not give."""

    def core(self):
        spec = importlib.util.spec_from_file_location('static_core_start_word', TOOL)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_the_cut_goes_in_the_pause_before_the_word_or_just_before_it(self):
        core = self.core()
        text = 'They said no. He tried again.'
        row = {'start_s': 0.0, 'end_s': 3.0,
               'word_times': [[0.0, 0.3], [0.3, 0.6], [0.6, 1.0], [1.6, 1.8], [1.8, 2.1], [2.1, 2.6]]}
        c = core.word_cut_s(row, text, 4)
        self.assertEqual((c['word'], c['cut_s'], c['pause_before_s']), ('He', 1.3, 0.6))
        self.assertEqual(core.word_cut_s(row, text, 2)['cut_s'], 0.3)       # no pause: just before the word
        self.assertIsNone(core.word_cut_s(row, text, 1))                     # the shot before needs a word of its own
        self.assertIsNone(core.word_cut_s(row, text, 7))

    def test_a_cut_word_changes_the_shot_structure_and_old_plans_keep_their_hash(self):
        core = self.core()
        a = [{'id': 'S1', 'beat_id': 'B1', 'line_start': 'L1', 'line_end': 'L2'}]
        self.assertEqual(core.shot_structure_sha(a), core.canonical_sha([['S1', 'B1', 'L1', 'L2']]))
        self.assertNotEqual(core.shot_structure_sha(a), core.shot_structure_sha([dict(a[0], start_word=3)]))


class MasterSoundTests(unittest.TestCase):
    """master-sound (2026-11-22): the export's mix brought to a measured loudness, the picture copied, the export kept."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.rd = Path(self.td.name)/'run'
        save(self.rd/'state.json', {'schema': 'static-youtube-longform-v1', 'run': 'r'})
        self.src = Path(self.td.name)/'export.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=30:d=6',
                        '-f', 'lavfi', '-i', 'aevalsrc=0.1*sin(2*PI*220*t)*(0.55+0.45*sin(2*PI*3*t)):s=44100:d=6',
                        '-shortest', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                        '-b:a', '192k', str(self.src)], check=True)
        save(self.rd/'00-inventory/references.json', {'items': [{'id': 'V001', 'source_path': str(self.src)}]})

    def probe(self, f):
        out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries',
                              'stream=codec_name,nb_read_frames', '-of', 'csv=p=0', str(f)], capture_output=True, text=True)
        return out.stdout.strip()

    def test_the_mix_reaches_the_target_under_the_ceiling_and_the_picture_is_copied(self):
        out = Path(self.td.name)/'final.mp4'
        res = cli('master-sound', '--run', self.rd, '--video', 1, '--file', self.src, '--out', out, '--target-lufs', -16,
                  '--refs', 'V001', '--why', 'the references are mastered louder than this export plays')
        self.assertLess(abs(res['result']['integrated_lufs'] + 16), 0.5, res)
        self.assertLessEqual(res['result']['true_peak_dbtp'], -1.5)
        self.assertEqual(self.probe(out), self.probe(self.src))          # the same picture, frame for frame
        self.assertTrue(self.src.is_file())                               # the export is kept
        rec = json.loads((self.rd/'80-deliverables/video-01/master.json').read_text(encoding='utf-8'))
        self.assertIn('integrated_lufs', rec['references']['V001'])
        self.assertIn('over_1db_share', rec['limiter_activity'])

    def test_refused_without_a_reason_or_onto_the_export_itself(self):
        cli('master-sound', '--run', self.rd, '--video', 1, '--file', self.src, '--out', Path(self.td.name)/'x.mp4',
            '--target-lufs', -14, '--why', 'louder', expected=2)
        cli('master-sound', '--run', self.rd, '--video', 1, '--file', self.src, '--out', self.src, '--target-lufs', -14,
            '--why', 'the references are mastered louder than this', expected=2)


class CaptionOnsetTests(unittest.TestCase):
    """A line's first caption word never lights before the voice (2026-11-22: "Just" lit inside a held breath)."""

    def test_the_first_word_starts_where_the_measured_silence_ends(self):
        spec = importlib.util.spec_from_file_location('static_core_onset', TOOL)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        ws = [{'w': 'Just', 's': 453.78, 'e': 454.76}, {'w': 'after', 's': 454.76, 'e': 455.14}]
        self.assertEqual(core.clamp_line_onset(ws, 454.465), 1)
        self.assertEqual((ws[0]['s'], ws[0]['e']), (454.465, 454.76))
        late = [{'w': 'So', 's': 10.0, 'e': 10.3}]
        self.assertEqual(core.clamp_line_onset(late, 10.01), 0)                 # within tolerance: untouched
        self.assertEqual(core.clamp_line_onset(late, None), 0)
        whole = [{'w': 'No.', 's': 5.0, 'e': 5.3}, {'w': 'Then', 's': 6.2, 'e': 6.5}]
        core.clamp_line_onset(whole, 5.6)                                       # the whole word was before the voice
        self.assertEqual((whole[0]['s'], whole[0]['e']), (5.6, 6.2))


class ComprehensionAndPauseTests(unittest.TestCase):
    """Brief #4 (2026-11-22): what a first-time viewer must hold, what a beat leans on, and a pause cue whose
    measured silence the edit tops up (a residual, never a second pause)."""

    def core(self):
        spec = importlib.util.spec_from_file_location('static_core_brief4', TOOL)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_many_names_to_hold_at_once_are_named_and_a_simple_story_is_left_alone(self):
        core = self.core()
        dense = [{'id': 'L001', 'text': 'In Vienna, Anna met Boris, Carla and Dmitri at the station.'},
                 {'id': 'L002', 'text': 'Boris carried the money. Carla carried the papers.'},
                 {'id': 'L003', 'text': 'Dmitri watched Anna. Nobody in Vienna watched Dmitri.'}]
        out = core.comprehension_signals(dense, [], 150, 'en')
        self.assertTrue(any('names to hold' in w and 'Dmitri' in w for w in out), out)
        simple = [{'id': 'L001', 'text': 'The cat sat on the warm mat.'},
                  {'id': 'L002', 'text': 'It slept all afternoon, and nothing else happened.'}]
        self.assertEqual(core.comprehension_signals(simple, [], 150, 'en'), [])
        passing = [{'id': 'L001', 'text': 'He read Proust, Joyce, Woolf and Mann that winter.'}]   # heard once: no load
        self.assertEqual(core.comprehension_signals(passing, [], 150, 'en'), [])
        self.assertEqual(core.comprehension_signals(dense, [], 150, 'de'), [])                    # every noun capitalised

    def test_a_name_returning_after_a_long_absence_is_named(self):
        core = self.core()
        filler = ' '.join(['the river kept on rising through the long wet spring'] * 50)
        lines = [{'id': 'L001', 'text': 'Eliza wrote the first letter.'}, {'id': 'L002', 'text': filler},
                 {'id': 'L003', 'text': 'Then Eliza wrote again.'}]
        out = core.comprehension_signals(lines, [], 150, 'en')
        self.assertTrue(any('"Eliza" returns' in w for w in out), out)

    def test_a_beat_leans_only_on_what_came_before_unless_it_is_held_back_on_purpose(self):
        core = self.core()
        lines = [{'id': f'L{i:03d}', 'text': 'words'} for i in range(1, 7)]
        beats = [{'id': 'B1', 'line_start': 1, 'line_end': 2},
                 {'id': 'B2', 'line_start': 3, 'line_end': 4, 'depends_on': [{'what': 'who the courier is', 'from': 'B1'}]},
                 {'id': 'B3', 'line_start': 5, 'line_end': 6}]
        self.assertEqual(core.beat_dependency_issues(beats, lines), [])
        beats[1]['depends_on'] = [{'what': 'the courier is the sister', 'from': 'B3'}]
        self.assertTrue(any('depends_on_later_B3' in x for x in core.beat_dependency_issues(beats, lines)))
        beats[1]['depends_on'] = [{'what': 'the courier is the sister', 'withheld': 'the reveal lands harder if the viewer '
                                   'meets her as a stranger first', 'revealed_in': 'L006'}]
        self.assertEqual(core.beat_dependency_issues(beats, lines), [])                # a mystery on purpose
        beats[1]['depends_on'] = [{'what': 'the courier is the sister', 'withheld': 'later', 'revealed_in': 'B1'}]
        out = core.beat_dependency_issues(beats, lines)
        self.assertTrue(any('withheld_needs_why' in x for x in out) and any('is_not_later' in x for x in out), out)

    def test_a_residual_pause_counts_its_cue_once_before_the_line_is_measured(self):
        core = self.core()
        why = {'pause_purpose': 'the reveal needs a moment to land with the viewer',
               'pause_picture': 'the empty chair stays on screen the whole time',
               'pause_sound': 'the bed carries on quietly under the silence',
               'pause_landing': 'the line falls and settles on its last word',
               'pause_resume': 'the next line starts again plainly and quietly'}
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)/'run'
            save(rd/'state.json', {'schema': 'static-youtube-longform-v1', 'run': 'r'})
            gap = core.DEFAULT_NATURAL_GAP_S
            cued = [{'id': 'L001', 'text': 'He asked them to stand by.', 'pause_total_s': 3.0, 'pause_via': 'edit', **why},
                    {'id': 'L002', 'text': '[short pause] Nobody answered.'}]
            row = [h for h in core.hold_facts(rd, 1, cued)['holds'] if h['line'] == 'L001'][0]
            cue = core.tag_cost_s('[short pause]')
            self.assertGreater(cue, 0)                                       # never assumed to take no time
            self.assertAlmostEqual(row['added_s'], round(max(0.0, 3.0 - gap - cue), 2))
            plain = [dict(cued[0]), {'id': 'L002', 'text': 'Nobody answered.'}]
            row = [h for h in core.hold_facts(rd, 1, plain)['holds'] if h['line'] == 'L001'][0]
            self.assertAlmostEqual(row['added_s'], round(3.0 - gap, 2))

    def test_a_pause_cue_topped_up_by_the_edit_is_a_residual_only_in_the_whole_silence_form(self):
        core = self.core()
        why = {'pause_purpose': 'the reveal needs a moment to land with the viewer',
               'pause_picture': 'the empty chair stays on screen the whole time',
               'pause_sound': 'the bed carries on quietly under the silence',
               'pause_landing': 'the line falls and settles on its last word',
               'pause_resume': 'the next line starts again plainly and quietly'}
        lines = [{'id': 'L001', 'text': 'He asked them to stand by.', 'pause_total_s': 1.6, 'pause_via': 'edit', **why},
                 {'id': 'L002', 'text': '[pause] Nobody answered.'}]
        plan, issues = core.script_pause_plan(lines)
        self.assertEqual(issues, [])
        self.assertTrue(plan[0]['residual_of_tag'])
        older = [dict(lines[0], pause_total_s=None, pause_after_s=1.5), lines[1]]
        older[0].pop('pause_total_s')
        plan, issues = core.script_pause_plan(older)
        self.assertTrue(any('edit_hold_and_a_pause_tag_at_once' in x for x in issues), issues)


class ReadabilityAndAnchorTests(unittest.TestCase):
    """Brief #4 (2026-11-22): drawn words a viewer can read, and sounds that move with the story when the narration is
    re-recorded or a hold changes."""

    def core(self):
        spec = importlib.util.spec_from_file_location('static_core_w67', TOOL)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_small_short_or_covered_words_are_named_and_a_clear_label_is_not(self):
        core = self.core()
        with tempfile.TemporaryDirectory() as td:
            mov = Path(td)/'D01.mov'
            save(mov.with_suffix('.json'), {'dur_s': 6.0, 'elements': [
                {'type': 'text', 'text': 'CALAIS', 'size': 0.018, 'at': [0.6, 0.3], 'in': {'start_s': 1.0}},
                {'type': 'text', 'text': 'TWO HUNDRED SHIPS', 'size': 0.04, 'at': [0.3, 0.84], 'in': {'start_s': 1.0}},
                {'type': 'text', 'text': 'GONE', 'size': 0.04, 'at': [0.3, 0.2], 'in': {'start_s': 1.0},
                 'out': {'start_s': 1.6}},
                {'type': 'text', 'text': 'LONDON', 'size': 0.035, 'at': [0.4, 0.3], 'in': {'start_s': 0.5}},
                {'type': 'line', 'points': [[0, 0], [1, 1]]}]})
            out = core.drawing_readability([{'file': str(mov)}], captions_on=True)
            self.assertTrue(any('"CALAIS"' in w and 'small' in w for w in out), out)
            self.assertTrue(any('"TWO HUNDRED SHIPS"' in w and 'caption band' in w for w in out), out)
            self.assertTrue(any('"GONE"' in w and 'on screen 0.6 s' in w for w in out), out)
            self.assertFalse([w for w in out if '"LONDON"' in w])
            self.assertFalse([w for w in core.drawing_readability([{'file': str(mov)}], captions_on=False)
                              if 'caption band' in w])

    def test_stamps_counters_and_cards_are_read_where_the_moving_still_puts_them(self):
        core = self.core()
        with tempfile.TemporaryDirectory() as td:
            mov = Path(td)/'D09.mov'
            save(mov.with_suffix('.json'), {'dur_s': 4.0, 'still_motion': {'scale': [1.0, 1.2], 'x': [0, 0], 'y': [0, 0]},
                                            'elements': [
                {'type': 'stamp', 'id': 's', 'text': 'INVENTED', 'size': 0.03, 'at': [0.5, 0.75], 'in': {'start_s': 0.5}},
                {'type': 'counter', 'id': 'n', 'from': 0, 'to': 1500, 'suffix': ' MEN', 'size': 0.018, 'at': [0.5, 0.3],
                 'in': {'start_s': 0.5, 'dur_s': 1.0}},
                {'type': 'card', 'id': 'c', 'center': [0.5, 0.45], 'lines': ['A NAME'], 'text_size': 0.03,
                 'in': {'kind': 'drop', 'start_s': 0.2}}]})
            out = core.drawing_readability([{'file': str(mov)}], captions_on=True)
            self.assertTrue(any('"INVENTED"' in w and 'caption band' in w for w in out), out)   # only at the end of the push
            self.assertTrue(any('"1,500 MEN"' in w and 'small' in w for w in out), out)
            self.assertFalse([w for w in out if '"A NAME"' in w])

    def test_a_sound_anchored_to_the_story_moves_when_the_narration_moves(self):
        core = self.core()
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)/'run'
            save(rd/'state.json', {'schema': 'static-youtube-longform-v1', 'run': 'r'})
            ep = rd/'70-edit/video-01/edit-plan.json'
            cap = rd/'70-edit/video-01/captions.json'
            lt = rd/'50-audio/video-01/line-times.json'
            save(ep, {'holds': [{'after_line': 'L001', 'at_audio_s': 2.5, 'hold_s': 1.0,
                                 'times_in_edit': {'silence_from_s': 2.2, 'silence_to_s': 3.8}}]})
            save(cap, {'words': [{'w': 'One', 'line': 'L001', 's': 0.2, 'e': 2.2},
                                 {'w': 'Two', 'line': 'L002', 's': 3.8, 'e': 6.0}]})
            save(lt, {'lines': [{'id': 'L001', 'start_s': 0.2, 'end_s': 2.2, 'gap_span_s': [2.2, 2.8]},
                                {'id': 'L002', 'start_s': 2.8, 'end_s': 5.0, 'gap_span_s': [5.0, 5.6]}]})
            beds = Path(td)/'beds.json'
            save(beds, {'beds': [{'id': 'M1', 'at': 2.6, 'end': 6.3}]})
            res = cli('sound-anchors', '--run', rd, '--video', 1, '--file', beds, '--to-anchors')
            b = json.loads(beds.read_text(encoding='utf-8'))['beds'][0]
            self.assertEqual(b['at_anchor'], {'line': 'L001', 'at': 'silence_start', 'offset_s': 0.4})
            self.assertEqual(b['end_anchor']['line'], 'L002')
            # a re-recording makes L001 1.5 s longer: the bed enters at the same moment of the story
            save(ep, {'holds': [{'after_line': 'L001', 'at_audio_s': 4.0, 'hold_s': 1.0,
                                 'times_in_edit': {'silence_from_s': 3.7, 'silence_to_s': 5.3}}]})
            save(cap, {'words': [{'w': 'One', 'line': 'L001', 's': 0.2, 'e': 3.7},
                                 {'w': 'Two', 'line': 'L002', 's': 5.3, 'e': 7.5}]})
            save(lt, {'lines': [{'id': 'L001', 'start_s': 0.2, 'end_s': 3.7, 'gap_span_s': [3.7, 4.3]},
                                {'id': 'L002', 'start_s': 4.3, 'end_s': 6.5, 'gap_span_s': [6.5, 7.1]}]})
            res = cli('sound-anchors', '--run', rd, '--video', 1, '--file', beds, '--resolve')
            b = json.loads(beds.read_text(encoding='utf-8'))['beds'][0]
            self.assertAlmostEqual(b['at'], 4.1)
            self.assertAlmostEqual(b['end'], 7.8)
            self.assertEqual(len(res['changed']), 2)
            # a sound that belongs to a word follows that word; a hand-written anchor survives --to-anchors
            sfx = Path(td)/'sfx.json'
            save(sfx, {'sfx': [{'id': 'key', 'at': 0.0, 'at_anchor': {'line': 'L002', 'at': 'word', 'word': 1,
                                                                       'offset_s': -0.1}}]})
            res = cli('sound-anchors', '--run', rd, '--video', 1, '--file', sfx, '--to-anchors')
            self.assertEqual(res['anchors_kept'], ['key.at'])
            cli('sound-anchors', '--run', rd, '--video', 1, '--file', sfx, '--resolve')
            self.assertAlmostEqual(json.loads(sfx.read_text(encoding='utf-8'))['sfx'][0]['at'], 5.2)


class SignificanceTests(unittest.TestCase):
    """What happened, why it matters, whether it paid (brief #5, 2026-11-23): planned for key moments, asked of both
    readers, turned into findings. The code enforces the process; weighing a reader's account is the director's."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('static_core_significance', TOOL)
        cls.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.core)

    def lines(self, n=12):
        return [{'id': f'L{i:03}', 'text': 'words'} for i in range(1, n + 1)]

    def dev(self, **kw):
        d = {'lines': 'L007-L012', 'what_happened': 'the bridge plan is abandoned', 'why_it_matters': 'the town stays cut off',
             'would_be_different': 'the town would have its bridge by winter', 'learned_when': 'before',
             'why_from': 'the video', 'event': 'clear', 'significance': 'clear', 'reward': 'landed'}
        d.update(kw)
        return d

    def test_a_key_moment_says_what_it_means_and_what_must_come_first(self):
        c, lines = self.core, self.lines()
        beats = [{'id': 'B01', 'line_start': 1, 'line_end': 6},
                 {'id': 'B02', 'line_start': 7, 'line_end': 12, 'key_moment': 'the reveal'}]
        self.assertIn('beat_B02_key_moment_needs_what_it_means:significance.matters_because',
                      c.beat_significance_issues(beats, lines))
        beats[1]['significance'] = {'matters_because': 'the plan the viewer trusted could never have worked',
                                    'reward': 'the oh of the hidden constraint'}
        self.assertTrue(any('must_know_first' in x for x in c.beat_significance_issues(beats, lines)))
        beats[1]['depends_on'] = [{'what': 'what the plan was meant to achieve', 'from': 'B01'}]
        self.assertEqual(c.beat_significance_issues(beats, lines), [])
        # Case D: a punchline's significance is its setup, not danger.
        joke = [{'id': 'B01', 'line_start': 1, 'line_end': 12, 'key_moment': 'the punchline',
                 'significance': {'matters_because': 'the absurd rule from the start finally bites its own maker',
                                  'reward': 'a laugh', 'self_contained': 'the setup sits in the same beat'}}]
        self.assertEqual(c.beat_significance_issues(joke, lines), [])
        # Case E: a contested consequence names the line that keeps it honest.
        beats[1]['significance']['certainty'] = 'contested'
        self.assertTrue(any('hedge' in x for x in c.beat_significance_issues(beats, lines)))
        beats[1]['significance']['hedge'] = 'L010'
        self.assertEqual(c.beat_significance_issues(beats, lines), [])
        beats[1]['significance']['hedge'] = 'L099'
        self.assertTrue(any('hedge' in x for x in c.beat_significance_issues(beats, lines)))
        self.assertEqual(c.beat_significance_issues([{'id': 'B03', 'line_start': 1, 'line_end': 2}], lines), [])

    def test_following_meaning_and_payoff_fail_separately(self):
        c = self.core
        f = lambda *ds: c.development_findings('script', list(ds), set())
        # Case A: the events are clear, why they matter is not, or the reader only knew it from elsewhere.
        a = f(self.dev(significance='unclear', why_it_matters='I could not tell'))
        self.assertEqual((a[0]['id'], a[0]['severity']), ('S1', 'major'))
        self.assertIn('the bridge plan is abandoned', a[0]['problem'])            # the reader's own words, quoted
        outside = f(self.dev(why_from='my own knowledge'))
        self.assertEqual(outside[0]['severity'], 'major')
        self.assertIn('own knowledge', outside[0]['problem'])
        # Case B: significance already established: nothing is added for its own sake.
        self.assertEqual(f(self.dev()), [])
        # Case C: a mystery held on purpose is not a gap.
        self.assertEqual(f(self.dev(significance='withheld', why_it_matters='not yet, and I want to know')), [])
        # Case D: an unconventional reward is the video's own; no stakes demanded.
        self.assertEqual(f(self.dev(reward='not the point here', what_happened='the cat finally learns the door')), [])
        # Partly clear, or a payoff that missed: minor, still answered.
        self.assertEqual([x['severity'] for x in f(self.dev(significance='partly'), self.dev(reward='missed'))],
                         ['minor', 'minor'])
        self.assertEqual(f(self.dev(event='unclear'))[0]['severity'], 'major')
        self.assertEqual(c.development_findings('script', [self.dev(significance='unclear')], {'S1'})[0]['id'], 'S2')

    def test_the_developments_follow_the_format(self):
        c = self.core
        order = [f'L{i:03}' for i in range(1, 13)]
        self.assertTrue(c.development_problems('script', [], order))
        self.assertEqual(c.development_problems('script', [self.dev()], order), [])
        bad = c.development_problems('script', [self.dev(lines='L099', significance='sort of')], order)
        self.assertTrue(any('"lines"' in x for x in bad) and any('"significance"' in x for x in bad))
        self.assertEqual(c.development_problems('final', [dict(self.dev(), at='05:16-06:07')], order), [])
        # The two answers added by brief 3 are owed only by readers who were asked them (round 8 was brief 2).
        old = {k: v for k, v in self.dev().items() if k not in ('would_be_different', 'learned_when')}
        self.assertEqual(c.development_problems('script', [old], order, 2), [])
        self.assertTrue(any('learned_when' in x for x in c.development_problems('script', [old], order, 3)))

    def test_a_reason_that_arrives_only_afterwards_is_major_on_a_key_moment(self):
        # The real case (2026-11-23): the trick's result was clear, why it mattered came 40 s later as a verdict.
        c = self.core
        order = [f'L{i:03}' for i in range(1, 13)]
        key = {'id': 'B02', 'key_moment': 'the turning point'}
        late = self.dev(learned_when='only afterwards', why_it_matters='the generals said it tipped the balance')
        on_key = c.development_findings('script', [late], set(), [(key, 7, 12)], order)
        self.assertEqual((on_key[0]['severity'], on_key[0]['lines']), ('major', 'L007-L012'))
        self.assertIn('B02', on_key[0]['problem'])
        # Elsewhere, a setup clear at the time that pays off later is ordinary craft (reader test D: a planted rule
        # called back in the last line); only partly clear at the time, it is a minor finding.
        self.assertEqual(c.development_findings('script', [late], set(), [(key, 1, 3)], order), [])
        partly = dict(late, significance='partly')
        self.assertEqual(c.development_findings('script', [partly], set(), [(key, 1, 3)], order)[0]['severity'], 'minor')
        # Case A on the real failure (reader test A): the turning point only partly carried its meaning -> major there.
        half = self.dev(significance='partly', learned_when='at the moment')
        self.assertEqual(c.development_findings('script', [half], set(), [(key, 7, 12)], order)[0]['severity'], 'major')
        self.assertEqual(c.development_findings('script', [self.dev(learned_when='never')], set())[0]['severity'],
                         'major')
        # Case C again: a mystery held on purpose is never a finding, whenever its reason comes.
        held = self.dev(significance='withheld', learned_when='only afterwards')
        self.assertEqual(c.development_findings('script', [held], set(), [(key, 7, 12)], order), [])
        # Case B: given before the moment, nothing is asked for.
        self.assertEqual(c.development_findings('script', [self.dev()], set(), [(key, 7, 12)], order), [])

    def test_a_key_moment_the_reader_never_named_is_checked(self):
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            vd = Path(td)
            save(vd / 'beat-map.json', {'beats': [{'id': 'B01', 'line_start': 1, 'line_end': 6},
                                                  {'id': 'B02', 'line_start': 7, 'line_end': 12, 'key_moment': 'the reveal',
                                                   'significance': {'matters_because': 'it changes what the plan meant'}}]})
            order = [f'L{i:03}' for i in range(1, 13)]
            miss = c.key_moment_findings(Path(td), vd, 1, 'script', [self.dev(lines='L001-L003')], order, set())
            self.assertEqual((miss[0]['id'], miss[0]['severity'], miss[0]['lines']), ('K1', 'minor', ['L007-L012']))
            self.assertIn('it changes what the plan meant', miss[0]['problem'])
            self.assertEqual(c.key_moment_findings(Path(td), vd, 1, 'script', [self.dev()], order, set()), [])

    def test_mixed_answers_missing_reasons_and_could_not_tell(self):
        # Audit 2026-11-23: a label alone is not an account, and an answer naming two choices is read by the worse one.
        c = self.core
        self.assertEqual(c._choice('the video, partly my own knowledge', c.DEV_FROM), 'my own knowledge')
        self.assertEqual(c._choice('clear, though only partly', c.DEV_SIGNIFICANCE), 'partly')
        self.assertEqual(c._choice('unclear', c.DEV_SIGNIFICANCE), 'unclear')        # "clear" inside "unclear" is not read
        self.assertEqual(c._choice('clear', c.DEV_SIGNIFICANCE), 'clear')
        self.assertIsNone(c._choice('mostly clear', c.DEV_SIGNIFICANCE))             # not a choice: the format is asked again
        order = [f'L{i:03}' for i in range(1, 13)]
        silent = self.dev()
        silent.pop('why_it_matters')
        self.assertTrue(any('why_it_matters' in p for p in c.development_problems('script', [silent], order, 4)))
        self.assertFalse(any('why_it_matters' in p for p in c.development_problems('script', [silent], order, 3)))
        key = {'id': 'B02', 'key_moment': 'the turning point'}
        blank = self.dev(would_be_different='I could not tell')                     # "clear", but no account behind it
        self.assertEqual(c.development_findings('script', [blank], set())[0]['severity'], 'minor')
        self.assertEqual(c.development_findings('script', [blank], set(), [(key, 7, 12)], order)[0]['severity'], 'major')
        mixed = self.dev(why_from='the video, partly my own knowledge')
        self.assertIn('own knowledge', c.development_findings('script', [mixed], set())[0]['problem'])

    def test_what_happened_and_the_payoff_count_on_a_key_moment(self):
        # Audit 2026-11-23: the three judgements each count; on a key moment, half-followed events and a missed payoff
        # are major, as half a meaning already was.
        c = self.core
        order = [f'L{i:03}' for i in range(1, 13)]
        key = {'id': 'B02', 'key_moment': 'the turning point'}
        on = lambda d: [x['severity'] for x in c.development_findings('script', [d], set(), [(key, 7, 12)], order)]
        off = lambda d: [x['severity'] for x in c.development_findings('script', [d], set())]
        self.assertEqual((on(self.dev(event='partly')), off(self.dev(event='partly'))), (['major'], ['minor']))
        self.assertEqual((on(self.dev(reward='missed')), off(self.dev(reward='missed'))), (['major'], ['minor']))
        self.assertEqual((on(self.dev(reward='partly')), off(self.dev(reward='partly'))), (['minor'], []))
        missed = c.development_findings('script', [self.dev(reward='missed')], set(), [(key, 7, 12)], order)[0]
        self.assertIn('did not land', missed['problem'])
        self.assertIn('B02', missed['problem'])
        self.assertIn('payoff', missed['suggestion'])                              # the advice follows the cause
        half = c.development_findings('script', [self.dev(event='partly')], set())[0]
        self.assertIn('easy to follow', half['suggestion'])
        # Case B still holds: a clear, landed development asks for nothing.
        self.assertEqual(on(self.dev()), [])

    def test_a_hedge_comes_at_or_after_the_claim_it_qualifies(self):
        c, lines = self.core, self.lines()
        sig = {'matters_because': 'the plan may have changed what the other side did next', 'reward': 'an honest answer',
               'self_contained': 'everything it needs is said inside the moment', 'certainty': 'contested'}
        beats = [{'id': 'B01', 'line_start': 1, 'line_end': 6},
                 {'id': 'B02', 'line_start': 7, 'line_end': 12, 'key_moment': 'the turning point',
                  'significance': dict(sig, hedge='L002')}]
        self.assertIn('beat_B02_hedge_comes_before_the_moment_it_qualifies:significance.hedge',
                      c.beat_significance_issues(beats, lines))
        beats[1]['significance']['hedge'] = 'L011'
        self.assertEqual(c.beat_significance_issues(beats, lines), [])

    def test_key_moments_are_weighed_as_sealed_with_the_packet(self):
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            vd = Path(td)
            save(vd / 'beat-map.json', {'beats': [{'id': 'B02', 'line_start': 7, 'line_end': 12}]})   # mark gone now
            order = [f'L{i:03}' for i in range(1, 13)]
            meta = {'key_moment_spans': [{'beat': 'B02', 'lo': 7, 'hi': 12, 'key_moment': 'the turning point',
                                          'matters_because': 'it changes what the plan meant'}]}
            spans = c.review_spans(meta, Path(td), vd, 1, 'script', order)
            self.assertEqual([(b['id'], lo, hi) for b, lo, hi in spans], [('B02', 7, 12)])
            half = self.dev(significance='partly')
            self.assertEqual(c.development_findings('script', [half], set(), spans, order)[0]['severity'], 'major')
            unnamed = c.key_moment_findings(Path(td), vd, 1, 'script', [self.dev(lines='L001-L003')], order, set(), spans)
            self.assertIn('it changes what the plan meant', unnamed[0]['problem'])
            self.assertEqual(c.review_spans({}, Path(td), vd, 1, 'script', order), [])   # an older packet: read now

    def test_a_new_export_always_gets_its_own_final_read(self):
        c = self.core
        with tempfile.TemporaryDirectory() as td:
            vd = Path(td)
            rv = vd / 'reviews'
            for r in (1, 2, 3):
                save(rv / f'final-r{r}.json', {'kind': 'final', 'round': r, 'findings': [],
                                               'findings_sha256': c.canonical_sha([]), 'subject_sha256': 'seen'})
                save(rv / f'final-r{r}-answers.json', {'answers': {}})
            self.assertNotIn('final_review_outdated', c.review_state(vd, 'final', 'seen')['issues'])
            self.assertIn('final_review_outdated', c.review_state(vd, 'final', 'never-read')['issues'])   # past round 2 too
            rec = json.loads((rv / 'final-r3.json').read_text(encoding='utf-8'))
            save(rv / 'final-r3.json', dict(rec, findings_outside_reader_folder=True, findings_from='C:/elsewhere/f.json'))
            self.assertTrue(any('outside the reader' in w for w in c.review_state(vd, 'final', 'seen')['warnings']))

    def test_both_readers_are_asked_the_three_things(self):
        for brief in (self.core.SCRIPT_BRIEF, self.core.FINAL_BRIEF):
            for want in ('why_from', 'my own knowledge', 'withheld', 'not the point here', 'ONLY what',
                         'would_be_different', 'learned_when', 'only afterwards', 'not their first'):
                self.assertIn(want, brief)
            for never in ('English', 'trick fooled'):                    # no one language, no one film's failure
                self.assertNotIn(never, brief)
        self.assertNotIn('meant to feel like', self.core.FINAL_BRIEF)    # the final reader is not told the intent
        self.assertIn('not told what any part is meant to do', self.core.FINAL_BRIEF)


class StillTouchupTests(unittest.TestCase):
    """still_touchup.py: never blurs or erases; a crisp mark keeps the original and records the edit (manual 04)."""

    def test_paint_puts_a_shape_where_the_model_drew_it_wrong(self):
        spec = importlib.util.spec_from_file_location('still_touchup_paint', TOOL.parent / 'still_touchup.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        from PIL import Image
        im = Image.new('RGB', (200, 100), (240, 235, 220))
        out = m.apply_regions(im, [{'mode': 'paint', 'fill': '#202020', 'soft': 0,
                                    'poly': [[100, 48], [170, 50], [100, 52]]}])
        self.assertLess(sum(out.getpixel((140, 50))), 200)            # the hand is there, pointing right
        self.assertEqual(out.getpixel((140, 20)), (240, 235, 220))    # nothing else changed
        with self.assertRaises(ValueError):
            m.apply_regions(im, [{'mode': 'paint', 'poly': [[0, 0], [1, 1]]}])

    def make_still(self, td):
        from PIL import Image
        run = Path(td)/'run'
        stills = run/'60-visuals/video-01/stills'
        stills.mkdir(parents=True)
        Image.new('RGB', (320, 180), (200, 190, 170)).save(stills/'S001.png')
        tool = ROOT/'scripts'/'still_touchup.py'
        spec = Path(td)/'spec.json'
        run_tool = lambda *a: subprocess.run([sys.executable, str(tool), '--run', str(run), '--video', '1', '--spec', str(spec), *a],
                                             capture_output=True, text=True, encoding='utf-8')
        return run, stills, spec, run_tool

    def test_blur_and_erase_are_refused_and_the_still_is_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            run, stills, spec, run_tool = self.make_still(td)
            before = (stills/'S001.png').read_bytes()
            for region in ({'mode': 'soften', 'sigma': 3, 'poly': [[200, 100], [300, 100], [300, 170]]},
                           {'mode': 'erase', 'size': 15, 'poly': [[30, 30], [160, 30], [160, 70]]}):
                save(spec, {'shot': 'S001', 'why': 'made-up print on the newspaper', 'regions': [region]})
                for extra in ((), ('--apply',)):
                    r = run_tool(*extra)
                    self.assertEqual(r.returncode, 2, r.stdout)
                    self.assertIn('refused', json.loads(r.stdout.strip().splitlines()[-1])['error'])
            self.assertEqual((stills/'S001.png').read_bytes(), before)            # nothing blurred or erased
            self.assertFalse((run/'60-visuals/video-01/stills-postprocess.json').exists())
            self.assertFalse((run/'60-visuals/video-01/stills-history').exists())

    def test_a_supplied_or_edited_picture_is_checked_kept_and_recorded(self):
        import hashlib
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            run, stills, spec, run_tool = self.make_still(td)
            f = stills/'S001.png'
            before = f.read_bytes()
            key = os.path.normcase(str(f.resolve()))
            save(run/'60-visuals/video-01/stills-provenance.json',
                 {'images': {key: {'shot_id': 'S001', 'file_sha256': hashlib.sha256(before).hexdigest()}}})
            tool = ROOT/'scripts'/'still_touchup.py'
            rp = lambda *a: subprocess.run([sys.executable, str(tool), '--run', str(run), '--video', '1', *a],
                                           capture_output=True, text=True, encoding='utf-8')
            square = Path(td)/'square.png'
            Image.new('RGB', (300, 300), (10, 20, 30)).save(square)
            r = rp('--replace', str(square), '--shot', 'S001', '--kind', 'edited', '--why',
                   'a colour corrected version of the still', '--apply')
            self.assertEqual(r.returncode, 2)                                  # another shape: it would be stretched
            self.assertEqual(f.read_bytes(), before)
            wide = Path(td)/'wide.png'
            Image.new('RGB', (640, 360), (10, 20, 30)).save(wide)
            self.assertEqual(rp('--replace', str(wide), '--shot', 'S001', '--kind', 'user_supplied', '--why',
                                'short').returncode, 2)                        # no real reason given
            save(run/'60-visuals/video-01/stills-postprocess.json',
                 {'edits': [{'shot_id': 'S001', 'at': '2026-11-22T10:00:00+00:00',
                             'regions': [{'mode': 'soften', 'sigma': 3, 'poly': [[0, 0], [9, 0], [9, 9]]}]}]})
            r = rp('--replace', str(wide), '--shot', 'S001', '--kind', 'user_supplied', '--why',
                   'the user painted this shot themselves', '--apply')
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(out['applied'], r.stdout + r.stderr)
            with Image.open(f) as im:
                self.assertEqual(im.size, (320, 180))                           # fitted to the still's size
            self.assertEqual((run/'60-visuals/video-01/stills-history/S001-before-replace-1.png').read_bytes(), before)
            edits = json.loads((run/'60-visuals/video-01/stills-postprocess.json').read_text(encoding='utf-8'))['edits']
            rec = edits[-1]
            self.assertEqual((rec['mode'], rec['kind']), ('replace', 'user_supplied'))
            self.assertTrue(edits[0].get('superseded_at'))                     # the old blur no longer stands
            self.assertIn('replaced by a checked user_supplied picture', edits[0]['superseded_by'])
            prov = json.loads((run/'60-visuals/video-01/stills-provenance.json').read_text(encoding='utf-8'))
            self.assertEqual(prov['images'][key]['file_sha256'], hashlib.sha256(f.read_bytes()).hexdigest())

    def test_a_crisp_mark_keeps_the_original_records_the_edit_and_moves_the_fingerprint(self):
        import hashlib
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            run, stills, spec, run_tool = self.make_still(td)
            f = stills/'S001.png'
            before = f.read_bytes()
            key = os.path.normcase(str(f.resolve()))
            save(run/'60-visuals/video-01/stills-provenance.json',
                 {'images': {key: {'shot_id': 'S001', 'file_sha256': hashlib.sha256(before).hexdigest()}}})
            save(spec, {'shot': 'S001', 'why': 'the clock needs its three o\'clock dot',
                        'regions': [{'mode': 'text', 'text': '9', 'at': [250, 50], 'size': 30},
                                    {'mode': 'paint', 'fill': '#202020', 'soft': 0, 'poly': [[100, 98], [170, 100], [100, 102]]}]})
            r = run_tool()
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(out['ok']); self.assertFalse(out['applied'])
            self.assertEqual(f.read_bytes(), before)                          # a preview changes nothing
            r = run_tool('--apply')
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(out['applied'])
            hist = run/'60-visuals/video-01/stills-history/S001-before-touchup-1.png'
            self.assertEqual(hist.read_bytes(), before)                        # the original is kept untouched
            fixed = Image.open(f).convert('L')
            self.assertLess(fixed.crop((238, 36, 262, 64)).getextrema()[0], 90)  # the painted numeral is there
            self.assertLess(fixed.getpixel((140, 100)), 90)                    # and the shape
            self.assertEqual(fixed.getpixel((40, 160)), Image.open(hist).convert('L').getpixel((40, 160)))   # nothing else
            rec = json.loads((run/'60-visuals/video-01/stills-postprocess.json').read_text(encoding='utf-8'))
            self.assertEqual(rec['edits'][0]['shot_id'], 'S001')
            self.assertIn('content-review', out['next'])
            prov = json.loads((run/'60-visuals/video-01/stills-provenance.json').read_text(encoding='utf-8'))
            self.assertEqual(prov['images'][key]['file_sha256'], hashlib.sha256(f.read_bytes()).hexdigest())
            run_tool('--apply')                                                # a second mark never overwrites the first original
            self.assertTrue((run/'60-visuals/video-01/stills-history/S001-before-touchup-2.png').is_file())
            save(spec, {'shot': 'S001', 'regions': []})
            r = run_tool('--apply')
            self.assertEqual(r.returncode, 2)                                  # no "why": refused, nothing written


class TopicDiscoveryTests(unittest.TestCase):
    """Topic discovery (2026-11-24, part 2): the subject is researched, compared and chosen within the user's scope; its
    evidence rests on claims whose sources were read; whether its material carries the locked length is the director's
    verdict with its reasons (never a percentage); the researched value reaches the beats in the order it needs, the
    script as surely as it is known, and the pictures. Each scenario is a different niche or scope; nothing asks for a
    conflict, a climax or a turning point."""

    LEDGER = ('### S1. A primary record\n- Access: read in full\n'
              '### S2. A field study\n- Access: read: abstract and results\n'
              '### S3. A textbook chapter\n- Access: read in full\n'
              '### S4. A news summary\n- Access: snippet (search result only)\n')
    CLAIMS = {'claims': [
        {'id': 'C01', 'claim': 'the core finding', 'sources': ['S1'], 'confidence': 'confirmed', 'line_refs': ['L003']},
        {'id': 'C02', 'claim': 'a supporting detail', 'sources': ['S2'], 'confidence': 'likely', 'line_refs': []},
        {'id': 'C03', 'claim': 'what the experts dispute', 'sources': ['S2', 'S3'], 'confidence': 'disputed', 'line_refs': []},
        {'id': 'C04', 'claim': 'a figure seen only in a search summary', 'sources': ['S4'], 'confidence': 'confirmed',
         'line_refs': []},
        {'id': 'C05', 'claim': 'a popular story', 'sources': ['S4'], 'confidence': 'legend', 'line_refs': []}]}
    WHY_NOT = ['its material is thinner and rests on one study', 'it is already the best known story of the field',
               'nothing in it can be shown without inventing pictures']

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('static_core_topics', TOOL)
        cls.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.core)

    def cand(self, cid, subject, form, what, why, reward, factual=True, material=None, runtime=None, **kw):
        mats = material if material is not None else [
            {'id': 'M1', 'what': f'the core finding of {subject}', 'certainty': 'established', 'claims': ['C01']},
            {'id': 'M2', 'what': f'the consequence of {subject}', 'certainty': 'established', 'claims': ['C01']}]
        c = {'id': cid, 'subject': subject, 'value_form': form, 'factual': factual,
             'what_happens': what, 'why_it_matters': why, 'reward': reward,
             'strongest_material': mats,
             'runtime': runtime if runtime is not None else {
                 'progression': [{'adds': f'what the viewer newly gets from {m["id"]}', 'material': [m['id']]}
                                 for m in mats if m.get('id')],
                 'verdict': 'sustains', 'why': 'the question, its evidence and its consequence fill it without repeats'},
             'feasibility': 'stills, maps and drawings can show every step of it'}
        first = next((str(m.get('id')) for m in mats if isinstance(m, dict) and m.get('id')), None)
        c['payoff'] = {'shape': 'builds_to', 'rests_on': [first] if first and factual is not False else [],
                       'why_substantial': f'the viewer finally sees what {subject} changes for people like them',
                       'needs_first': 'what the situation was before it',
                       'worth_the_buildup': 'every step on the way is a small discovery that the payoff then explains'}
        c.update(kw)
        return c

    def alt(self, cid='T2', n=0):
        texts = [('a forgotten survey error', 'a small mistake with large effects',
                  'a mapmaker draws a valley a mile too far north and nobody checks',
                  'every later plan inherits the error until a walker finds it',
                  'the pleasure of seeing one wrong line explain a dozen failures'),
                 ('a lighthouse keeper log', 'an ordinary record read closely',
                  'thirty years of weather notes kept by one keeper on one rock',
                  'they show a coast changing faster than anyone noticed at the time',
                  'the quiet shock of a slow change suddenly visible')][n]
        return self.cand(cid, *texts, material=[{'id': 'M1', 'what': f'the record behind {texts[0]}',
                                                 'certainty': 'established', 'sources': ['S2']}])

    def subj(self, cands, chosen='T1', kind='niche', user_words='geography', niche='geography', values=None,
             scope_extra=None, sel_extra=None, **kw):
        alts = [c['id'] for c in cands if c['id'] != chosen]
        s = {'scope': {'kind': kind, 'user_words': user_words, 'niche': niche,
                       **({'understood_as': f'{niche} as its viewers watch it: how places and their people work',
                           'boundary': f'a subject that is not {niche} itself, only told with a {niche} technique'}
                          if kind == 'niche' else {}),
                       **(scope_extra or {})},
             'audience_value': 'this audience comes to understand how the world works, not to collect facts',
             'from_references': [{'ref': 'V001', 'at': '01:10-01:40', 'observed': 'the map zooms out as the cause is named',
                                  'interpretation': 'the relation is shown before it is explained'}],
             'candidates': cands,
             'selection': {'candidate': chosen, 'why': 'its strongest material is surprising, read at the source, and builds',
                           'decisive_material': ['M1'],
                           'over_alternatives': [{'candidate': a, 'why_not': self.WHY_NOT[i % 3]} for i, a in enumerate(alts)],
                           **(sel_extra or {})},
             'value_to_carry': values if values is not None else [
                 {'id': 'R1', 'what': 'the core finding of the chosen subject', 'why_it_matters': 'it changes how the viewer sees it',
                  'certainty': 'established', 'rests_on': ['M1'], 'payoff': True}]}
        s.update(kw)
        return s

    def check(self, subject, locked_s=600, refs=('V001',), niche='geography', claims=None, ledger=None):
        return self.core.subject_issues(subject, self.LEDGER if ledger is None else ledger, locked_s, refs, niche,
                                        self.CLAIMS if claims is None else claims)

    # ---- different niches: different kinds of value, none of them asked for stakes, a conflict or a climax
    def test_each_niche_brings_its_own_kind_of_value(self):
        for niche, subject, form, what, why, reward in (
                ('history', 'the quiet supply order that decided a campaign', 'a consequential decision',
                 'a clerk moves the depots two weeks before the march', 'without the depots the army could not move',
                 'seeing how a quiet order decided a loud battle'),
                ('geography', 'why a lake turns animals to stone', 'a natural phenomenon explained',
                 'birds that land on the lake are preserved by its water', 'the chemistry turns a myth into a process',
                 'understanding a place that looks like a curse'),
                ('biology', 'how an octopus matches colours it cannot see', 'a surprising mechanism',
                 'its skin reacts to light the eyes cannot sort', 'a body solves what its eyes cannot',
                 'an answer and the honest edge of what is known'),
                ('science', 'the noise that was the oldest light', 'a surprising discovery',
                 'two engineers chase a hiss in their antenna for a year', 'the hiss is left over from the early universe',
                 'hearing the oldest signal there is'),
                ('how-to', 'fixing a squeaking door for good', 'a practical solution',
                 'find which hinge squeaks, then why, then fix the cause', 'most fixes treat the sound and it returns',
                 'a door that stays quiet and the reason it does')):
            iss, _ = self.check(self.subj([self.cand('T1', subject, form, what, why, reward), self.alt()], niche=niche,
                                          user_words=niche), niche=niche)
            self.assertEqual(iss, [], (niche, iss))

    def test_sufficiency_is_judged_from_the_material_never_counted(self):
        c = self.cand('T1', 'why dunes sing', 'a natural phenomenon explained', 'sand avalanches hum at one note',
                      'the note comes from the grains, not the wind', 'a sound that turns into a mechanism')
        c['runtime']['material_minutes'] = 4          # four minutes of notes for a ten-minute lock: no number decides
        self.assertEqual(self.check(self.subj([c, self.alt()]))[0], [])
        c['runtime'].update(verdict='short', shortfall='after the mechanism there is nothing new to show')
        c['runtime']['material_minutes'] = 15         # fifteen minutes of notes, judged short: the verdict decides
        short = 'subject_material_judged_short_for_the_locked_length:choose_another_candidate_or_angle_or_record_' \
                'the_users_decision_in_runtime_decision:never_pad'
        s = self.subj([c, self.alt()])
        self.assertIn(short, self.check(s)[0])
        s['runtime_decision'] = {'decided_by': 'director', 'user_words': 'fine', 'decision': 'we pad it a little'}
        self.assertIn(short, self.check(s)[0])        # only the user decides a shortfall; padding is never the answer
        s['runtime_decision'] = {'decided_by': 'user', 'user_words': 'make it six minutes then',
                                 'decision': 'the length lock is revised to six minutes'}
        self.assertNotIn(short, self.check(s)[0])
        c['runtime'] = {'material_minutes': 12, 'why': 'there is a lot of material on it'}
        iss = self.check(self.subj([c, self.alt()]))[0]
        self.assertIn('subject_candidate_T1_runtime_needs_its_progression:what_the_viewer_newly_gets_step_by_step', iss)
        self.assertIn('subject_candidate_T1_runtime_verdict_must_be:sustains/short/uncertain', iss)
        c['runtime'] = {'progression': [{'adds': 'the question the viewer starts from', 'material': ['M1']},
                                        {'adds': 'the question the viewer starts from', 'material': ['M2']},
                                        {'adds': 'a step with nothing under it at all', 'material': ['M7']},
                                        {'adds': 'the first finding seen again from above', 'material': ['M1']}],
                        'verdict': 'sustains', 'why': 'each step opens the next for this audience'}
        iss, warn = self.check(self.subj([c, self.alt()]))
        self.assertIn('subject_candidate_T1_runtime_step_2_repeats_an_earlier_step', iss)
        self.assertIn('subject_candidate_T1_runtime_step_3_names_material_this_candidate_lacks:M7', iss)
        self.assertIn('subject_candidate_T1_runtime_step_4_uses_only_material_earlier_steps_used:is_it_new_for_the_viewer',
                      warn)                       # a signal, not a refusal: a callback can be new for the viewer

    def test_a_recorded_link_is_not_evidence(self):
        def with_material(m):
            return self.subj([self.cand('T1', 'why a lake turns animals to stone', 'a phenomenon explained',
                                        'birds landing on it are preserved', 'the chemistry explains the myth',
                                        'a curse the viewer finally understands', material=[m]), self.alt()])
        m = {'id': 'M1', 'what': 'the water preserves what falls in', 'certainty': 'established', 'claims': ['C04']}
        self.assertIn('subject_candidate_T1_material_M1_claim_C04_rests_on_no_source_that_was_read:read_one_and_record_'
                      'its_Access', self.check(with_material(m))[0])
        read_now = self.LEDGER.replace('- Access: snippet (search result only)', '- Access: read in full')
        self.assertEqual(self.check(with_material(m), ledger=read_now)[0], [])
        m['claims'] = ['C03']
        self.assertTrue(any('said_as_established_but_claim_C03_is_disputed' in x for x in self.check(with_material(m))[0]))
        m['claims'] = ['C05']
        self.assertTrue(any('said_as_established_but_claim_C05_is_legend' in x for x in self.check(with_material(m))[0]))
        m.update(certainty='contested', claims=['C03'], hedge='said as what the experts still argue about')
        iss = self.check(with_material(m))[0]
        self.assertFalse([x for x in iss if 'material_M1' in x])          # contested, said as contested: fine
        m.update(certainty='established', claims=[], sources=['S1'])
        self.assertIn('subject_candidate_T1_material_M1_established_needs_its_claims:claims', self.check(with_material(m))[0])
        m.update(claims=['C09'])
        self.assertIn('subject_candidate_T1_material_M1_cites_claims_not_in_claims_json:C09', self.check(with_material(m))[0])

    def test_the_choice_rests_on_confirmed_evidence(self):
        c = self.cand('T1', 'the octopus that sees with its skin', 'a surprising mechanism',
                      'its skin reacts to light on its own', 'a body that solves what its eyes cannot',
                      'an answer and its honest edge',
                      material=[{'id': 'M1', 'what': 'the skin reacts to light alone', 'certainty': 'established',
                                 'claims': ['C02']}])
        c['runtime']['progression'] = [{'adds': 'a puzzle, then the skin experiment', 'material': ['M1']}]
        s = self.subj([c, self.alt()])
        self.assertIn('subject_choice_rests_on_M1_whose_claims_are_not_confirmed:C02:corroborate_them_or_rest_the_choice_'
                      'on_stronger_material', self.check(s)[0])
        c['strongest_material'][0]['claims'] = ['C01']
        self.assertEqual(self.check(s)[0], [])
        s['selection']['decisive_material'] = []
        self.assertIn('subject_selection_needs_decisive_material:the_chosen_subjects_material_the_choice_rests_on',
                      self.check(s)[0])
        s['selection']['decisive_material'] = ['M9']
        self.assertIn('subject_selection_decisive_material_not_in_the_chosen_subject:M9', self.check(s)[0])

    def test_a_sensational_candidate_with_weak_evidence_cannot_be_chosen(self):
        weak = self.cand('T2', 'the jellyfish that never dies', 'a shocking claim', 'it lives forever, the story goes',
                         'immortality would rewrite biology', 'a jaw-dropping fact',
                         material=[{'id': 'M1', 'what': 'the jellyfish cannot die', 'certainty': 'established',
                                    'claims': ['C05']}])
        solid = self.cand('T1', 'the jellyfish that runs its life backwards', 'a surprising mechanism told honestly',
                          'an adult turns back into a polyp under stress', 'one animal undoes its own ageing',
                          'wonder, with the honest limit that it still dies')
        iss, warn = self.check(self.subj([solid, weak, self.alt('T3')], niche='biology', user_words='biology'), niche='biology')
        self.assertEqual(iss, [])                       # considered and set aside: its gaps are only noted
        self.assertTrue(any('T2' in w and 'legend' in w for w in warn))
        iss = self.check(self.subj([solid, weak, self.alt('T3')], chosen='T2', niche='biology', user_words='biology'),
                         niche='biology')[0]
        self.assertTrue(any('said_as_established_but_claim_C05_is_legend' in x for x in iss))
        self.assertTrue(any(x.startswith('subject_choice_rests_on_M1_whose_claims_are_not_confirmed:C05') for x in iss))

    def test_a_hypothetical_keeps_premise_reasoning_and_speculation_apart(self):
        mats = [{'id': 'M1', 'what': 'the Moon raises most of our tides', 'certainty': 'established', 'claims': ['C01']},
                {'id': 'M2', 'what': 'the Moon is simply gone, all at once', 'certainty': 'assumed',
                 'framed_as': 'said as the premise of the thought experiment, never as possible'},
                {'id': 'M3', 'what': 'tides shrink to the Sun\'s share', 'certainty': 'reasoned', 'from': ['M1'],
                 'reasoning': 'the Sun alone raises tides a little under half as high'},
                {'id': 'M4', 'what': 'some coastal life would struggle', 'certainty': 'speculative',
                 'framed_as': 'a possibility the evidence does not settle'}]
        c = self.cand('T1', 'what if the Moon vanished', 'logically developed consequences',
                      'the tides, the nights and the tilt change one by one', 'each consequence follows from known physics',
                      'a world rebuilt step by step in the viewer\'s head', material=mats,
                      runtime={'progression': [{'adds': 'the premise and what is certain', 'material': ['M1', 'M2']},
                                               {'adds': 'the tides that follow from it', 'material': ['M3']},
                                               {'adds': 'what might follow, said as might', 'material': ['M4']}],
                               'verdict': 'sustains', 'why': 'three layers of consequence fill it for curious viewers'},
                      payoff={'shape': 'progressive', 'rests_on': ['M3'],
                              'why_substantial': 'the viewer rebuilds a familiar world one solid consequence at a time',
                              'needs_first': 'that the Moon raises most of the tides',
                              'worth_the_buildup': 'each layer of consequence is a reward of its own along the way'})
        vals = [{'id': 'R1', 'what': 'the tides would shrink by half', 'why_it_matters': 'coasts and life follow the tides',
                 'certainty': 'reasoned', 'rests_on': ['M3'], 'payoff': True},
                {'id': 'R2', 'what': 'coastal life might struggle', 'why_it_matters': 'it is the human stake of it',
                 'certainty': 'speculative', 'rests_on': ['M4'], 'framed_as': 'a possibility, said as one'}]
        scope = {'understood_as': 'the user wants the consequences of the Moon disappearing, as a thought experiment',
                 'boundary': 'a video about the Moon landing or the Moon\'s origin would be another video'}
        sel = {'keeps_user_scope': True, 'how_scope_kept': 'every step is a consequence of the user\'s premise itself'}
        s = self.subj([c], kind='story', user_words='What if the Moon disappeared?', niche='what if', values=vals,
                      scope_extra=scope, sel_extra=sel)
        self.assertEqual(self.check(s, niche='what if')[0], [])      # an exact concept: no alternative needed
        vals[0]['certainty'] = 'established'                          # a reasoned consequence said as a fact
        self.assertIn('subject_value_R1_said_as_established_but_rests_on_weaker_material:M3', self.check(s, niche='what if')[0])
        vals[0]['certainty'] = 'reasoned'
        mats[2]['from'] = ['M2']                                       # reasoning from an assumption is not established
        self.assertIn('subject_candidate_T1_material_M3_reasoned_from_items_not_established_here:M2',
                      self.check(s, niche='what if')[0])
        mats[2]['from'] = ['M1']
        mats[3].pop('framed_as')
        self.assertIn('subject_candidate_T1_material_M4_speculative_needs_how_it_is_framed:framed_as',
                      self.check(s, niche='what if')[0])

    def test_a_comedy_needs_no_stakes_and_may_invent(self):
        mats = [{'id': 'M1', 'what': 'a cat runs a tiny bakery badly', 'certainty': 'invented'},
                {'id': 'M2', 'what': 'it sells the last croissant to itself', 'certainty': 'invented'}]
        vals = [{'id': 'R1', 'what': 'the cat sells the last croissant to itself', 'why_it_matters': 'the setup pays as a joke',
                 'certainty': 'invented', 'payoff': True}]
        # a comedy pays several times: no climax to manufacture, no material to rest on (the premise is invented)
        c = self.cand('T1', 'a cat runs a bakery', 'a comic premise and its payoffs', 'a cat opens a bakery it cannot run',
                      'each customer makes the premise worse', 'a run of laughs and one last turn', factual=False, material=mats,
                      payoff={'shape': 'several', 'rests_on': [],
                              'why_substantial': 'each customer turns the same premise into a fresh, bigger laugh',
                              'needs_first': 'that the cat cannot bake at all',
                              'worth_the_buildup': 'the jokes escalate to the last croissant, which pays the whole setup'})
        s = self.subj([c, self.alt()], niche='comedy', user_words='comedy', values=vals)
        self.assertEqual(self.check(s, niche='comedy')[0], [])
        c['factual'] = True                                            # invention is not allowed in a factual subject
        self.assertTrue(any('invented_material_only' in x for x in self.check(s, niche='comedy')[0]))

    def test_an_ordinary_topic_with_a_real_angle_passes_on_its_substance(self):
        c = self.cand('T1', 'why toast lands butter side down', 'an everyday puzzle with a real mechanism',
                      'a slice falling from a table turns half a rotation', 'table height decides the outcome, not luck',
                      'the viewer can test it at breakfast')
        self.assertEqual(self.check(self.subj([c, self.alt()], niche='science', user_words='science'), niche='science')[0], [])

    def test_alternatives_are_answered_one_by_one(self):
        c = self.cand('T1', 'how rivers choose their path', 'a natural process', 'a river slowly bends itself into loops',
                      'the loops decide where towns could stand', 'a map that suddenly makes sense')
        self.assertIn('subject_niche_scope_needs_a_researched_alternative', self.check(self.subj([c]))[0])
        s = self.subj([c, self.alt('T2'), self.alt('T3', 1)])
        self.assertEqual(self.check(s)[0], [])
        s['selection']['over_alternatives'] = s['selection']['over_alternatives'][:1]
        self.assertIn('subject_selection_does_not_say_why_not_T3:over_alternatives', self.check(s)[0])
        s['selection']['over_alternatives'] = [{'candidate': 'T2', 'why_not': 'T2: it is weaker than the chosen one overall'},
                                               {'candidate': 'T3', 'why_not': 'T3: it is weaker than the chosen one overall'}]
        self.assertIn('subject_selection_gives_T2_and_T3_the_same_why_not:say_what_is_weaker_in_each', self.check(s)[0])
        s['selection']['over_alternatives'] = 'the others are weaker overall than this one'
        self.assertIn('subject_selection_over_alternatives_must_answer_each_alternative:[{candidate,why_not}]',
                      self.check(s)[0])
        self.assertFalse(any(k in json.dumps(s) for k in ('score', 'weight')))     # nothing numeric decides

    def test_a_reason_that_fits_any_candidate_explains_none(self):
        def templated(cid, subject):
            return self.cand(cid, subject, 'a natural phenomenon', f'the film follows {subject} from the question to the answer',
                             f'it changes how the viewer sees {subject}', f'the viewer leaves knowing {subject}')
        s = self.subj([templated('T1', 'singing dunes'), templated('T2', 'a lake of stone birds')])
        iss = self.check(s)[0]
        self.assertIn('subject_candidates_T1_and_T2_share_the_same_what_happens:a_reason_that_fits_any_candidate_explains_none',
                      iss)
        self.assertIn('subject_candidates_T1_and_T2_share_the_same_why_it_matters:a_reason_that_fits_any_candidate_explains_none',
                      iss)

    def test_an_exact_topic_is_developed_never_replaced(self):
        a1 = self.cand('T1', 'the history of salt', 'a surprising relationship', 'salt was paid, taxed and fought over',
                       'a kitchen staple ran economies for centuries', 'the viewer sees money in the salt cellar',
                       angle='salt as money, from Roman pay to colonial taxes')
        a2 = self.cand('T2', 'the history of salt', 'a long chain of causes', 'one trade route built a string of cities',
                       'whole regions grew rich on a mineral under their feet', 'a map of wealth that is really a map of salt',
                       angle='the salt roads and the cities they made')
        s = self.subj([a1, a2], kind='topic', user_words='the history of salt', niche='history')
        iss = self.check(s, niche='history')[0]
        for x in ('subject_topic_scope_needs_understood_as', 'subject_topic_scope_needs_boundary',
                  'subject_exact_topic_must_be_kept:selection.keeps_user_scope',
                  'subject_topic_scope_needs_how_scope_kept:selection.how_scope_kept'):
            self.assertIn(x, iss)
        s['scope'].update(understood_as='a video about salt across history: why it mattered and what it changed',
                          boundary='a video about cooking, chemistry or one salt mine alone would be another topic')
        s['selection'].update(keeps_user_scope=True, how_scope_kept='the angle is salt itself followed as money through history')
        iss, warn = self.check(s, niche='history')
        self.assertEqual(iss, [])
        a1['subject'] = 'how a white rock paid Roman soldiers'     # different words, same topic: no word test refuses it
        iss, warn = self.check(s, niche='history')
        self.assertEqual(iss, [])
        self.assertFalse([w for w in warn if 'shares no word' in w])
        self.assertIn('subject_topic_scope_needs_a_researched_alternative',
                      self.check(dict(s, candidates=[a1]), niche='history')[0])    # an exact topic compares its angles

    def test_a_broad_niche_stays_inside_the_locked_niche(self):
        s = self.subj([self.cand('T1', 'how rivers choose their path', 'a natural process', 'a river bends into loops',
                                 'the loops decide where towns stand', 'a map that makes sense'), self.alt()])
        self.assertEqual(self.check(s)[0], [])
        self.assertIn('subject_scope_niche_must_be_the_locked_niche:history', self.check(s, niche='history')[0])

    def test_references_inform_the_discovery_observed_apart_from_interpreted(self):
        s = self.subj([self.cand('T1', 'how fog forms in valleys', 'a natural phenomenon', 'cold air pools at night',
                                 'it explains why towns sit where they do', 'a morning view understood'), self.alt()])
        s['from_references'] = []
        self.assertIn('subject_needs_from_references:what_the_references_show_about_this_audiences_rewards', self.check(s)[0])
        s['from_references'] = [{'ref': 'V009', 'at': '00:20', 'observed': 'the narrator asks a question', 'interpretation': ''}]
        iss = self.check(s)[0]
        self.assertIn('subject_from_references_1_names_a_reference_not_in_the_evidence:V009', iss)
        self.assertIn('subject_from_references_1_needs_its_interpretation_apart', iss)
        c = self.core
        self.assertEqual(c.card_moment_issues({}, 'V001'), ['reference_V001_card_has_no_moments_that_matter'])
        good = {'moments_that_matter': [{'at': '01:00-01:20', 'observed': 'the reveal follows the question it answers',
                                         'interpretation': 'curiosity is set before it is paid'}]}
        self.assertEqual(c.card_moment_issues(good, 'V001'), [])

    # ---- the researched value reaches the film
    def test_researched_value_is_carried_in_the_order_it_needs(self):
        c = self.core
        vals = [{'id': 'R1', 'what': 'a', 'certainty': 'established'},
                {'id': 'R2', 'what': 'b', 'certainty': 'established', 'needs_first': ['R1']},
                {'id': 'R3', 'what': 'c', 'certainty': 'contested'}]
        direction = {'subject': {'value_to_carry': vals}}
        sig = {'matters_because': 'x y z w v', 'reward': 'an answer', 'self_contained': 'all of it inside'}
        beats = [{'id': 'B01', 'carries': ['R2']}, {'id': 'B02', 'carries': ['R1']},
                 {'id': 'B03', 'key_moment': 'the turn', 'significance': dict(sig), 'carries': ['R3']}]
        iss = c.subject_handoff_issues(direction, beats)
        self.assertIn('researched_value_R2_lands_before_R1_which_it_needs_first', iss)
        self.assertIn('beat_B03_carries_contested_R3_but_states_it_as_established', iss)
        beats[0]['carries'], beats[1]['carries'] = ['R1'], ['R2']
        beats[2]['significance']['certainty'] = 'contested'
        self.assertEqual(c.subject_handoff_issues(direction, beats), [])
        beats[2].pop('key_moment')                       # no key moment at all: nothing is asked to be invented
        self.assertEqual(c.subject_handoff_issues(direction, beats), [])
        beats[0]['carries'] = []
        self.assertIn('researched_value_R2_needs_R1_first_but_R1_reaches_no_beat', c.subject_handoff_issues(direction, beats))
        self.assertIn('researched_value_R1_reaches_no_beat:carry_it_or_drop_it_with_the_reason_in_subject.dropped',
                      c.subject_handoff_issues(direction, beats))
        beats[1]['carries'] = ['R9']
        self.assertTrue(any('carries_unknown_value:R9' in x for x in c.subject_handoff_issues(direction, beats)))
        self.assertEqual(c.subject_handoff_issues({}, beats), [])     # a direction made before topic discovery

    def test_a_speculative_value_is_not_given_a_settled_key_moment(self):
        c = self.core
        direction = {'subject': {'value_to_carry': [{'id': 'R1', 'what': 'what might follow', 'certainty': 'speculative'}]}}
        beats = [{'id': 'B01', 'key_moment': 'the last consequence', 'carries': ['R1'],
                  'significance': {'matters_because': 'it is where the thought experiment lands', 'reward': 'a vision',
                                   'self_contained': 'shown whole', 'certainty': 'established'}}]
        self.assertIn('beat_B01_carries_speculative_R1_but_states_it_as_established', c.subject_handoff_issues(direction, beats))
        beats[0]['significance']['certainty'] = 'speculative'
        self.assertEqual(c.subject_handoff_issues(direction, beats), [])

    def test_cumulative_value_needs_no_key_moment(self):
        # a tutorial whose value builds step by step: every step carried in order, none of them a "turn"
        c = self.core
        mats = [{'id': f'M{i}', 'what': f'step {i} works', 'certainty': 'established', 'claims': ['C01']} for i in (1, 2, 3)]
        vals = [{'id': f'R{i}', 'what': f'step {i} works', 'certainty': 'established', 'rests_on': [f'M{i}'],
                 **({'needs_first': [f'R{i - 1}']} if i > 1 else {})} for i in (1, 2, 3)]
        direction = {'subject': {'selection': {'candidate': 'T1'}, 'value_to_carry': vals,
                                 'candidates': [{'id': 'T1', 'factual': True, 'strongest_material': mats}]}}
        beats = [{'id': f'B0{i}', 'carries': [f'R{i}'], 'line_start': (i - 1) * 5 + 1, 'line_end': i * 5} for i in (1, 2, 3)]
        lines = [{'id': f'L{i:03}', 'text': 'a line'} for i in range(1, 16)]
        claims = {'claims': [{'id': 'C01', 'sources': ['S1'], 'confidence': 'confirmed', 'line_refs': ['L003', 'L008', 'L013']}]}
        self.assertEqual(c.subject_handoff_issues(direction, beats), [])
        self.assertEqual(c.value_script_issues(direction, beats, lines, claims), [])

    def test_the_script_says_the_research_as_surely_as_it_is_known(self):
        c = self.core
        mats = [{'id': 'M1', 'what': 'the finding', 'certainty': 'established', 'claims': ['C01']},
                {'id': 'M2', 'what': 'the open question', 'certainty': 'contested', 'claims': ['C03'], 'hedge': 'said as open'}]
        vals = [{'id': 'R1', 'what': 'the finding', 'certainty': 'established', 'rests_on': ['M1']},
                {'id': 'R2', 'what': 'what is still argued', 'certainty': 'contested', 'rests_on': ['M2'],
                 'hedge': 'said as what is argued'}]
        direction = {'subject': {'selection': {'candidate': 'T1'}, 'value_to_carry': vals,
                                 'candidates': [{'id': 'T1', 'factual': True, 'strongest_material': mats}]}}
        lines = [{'id': f'L{i:03}', 'text': 'a line'} for i in range(1, 11)]
        beats = [{'id': 'B01', 'carries': ['R1'], 'line_start': 1, 'line_end': 5},
                 {'id': 'B02', 'carries': ['R2'], 'line_start': 6, 'line_end': 10, 'hedges': {'R2': 'L008'}}]
        claims = {'claims': [{'id': 'C01', 'sources': ['S1'], 'confidence': 'confirmed', 'line_refs': ['L003']},
                             {'id': 'C03', 'sources': ['S2'], 'confidence': 'disputed', 'line_refs': ['L007']}]}
        self.assertEqual(c.value_script_issues(direction, beats, lines, claims), [])
        beats[0]['carries'], beats[1]['carries'] = [], ['R1', 'R2']    # R1 moved to a beat whose lines never say it
        self.assertIn('researched_value_R1_carried_by_B02_but_no_line_there_is_tied_to_its_claims:C01',
                      c.value_script_issues(direction, beats, lines, claims))
        beats[0]['carries'], beats[1]['carries'] = ['R1'], ['R2']
        beats[1]['hedges'] = {}
        self.assertIn('beat_B02_carries_contested_R2_without_the_line_that_says_so:hedges.R2',
                      c.value_script_issues(direction, beats, lines, claims))
        beats[1]['hedges'] = {'R2': 'L002'}
        self.assertIn('beat_B02_hedge_for_R2_comes_before_the_beat', c.value_script_issues(direction, beats, lines, claims))
        beats[1].update(key_moment='the open question', hedges={})    # a key moment keeps its own hedge (significance)
        self.assertEqual(c.value_script_issues(direction, beats, lines, claims), [])

    def test_a_key_moment_reaches_a_picture(self):
        c = self.core
        direction = {'subject': {}}
        beats = [{'id': 'B01'}, {'id': 'B02', 'key_moment': 'the turn'}]
        shots = [{'id': 'S1', 'beat_id': 'B01'}, {'id': 'S2', 'beat_id': 'B02'}]
        self.assertEqual(c.key_moment_shot_issues(direction, beats, shots),
                         ['key_moment_B02_no_shot_says_how_the_picture_carries_it:carries_significance'])
        shots[1]['carries_significance'] = 'the empty harbour holds while the words land'
        self.assertEqual(c.key_moment_shot_issues(direction, beats, shots), [])
        self.assertEqual(c.key_moment_shot_issues({}, beats, [{'id': 'S2', 'beat_id': 'B02'}]), [])   # older run

    def test_each_kind_of_change_reaches_only_what_it_changes(self):
        c = self.core
        self.assertEqual(c.field_effects('subject.selection.candidate'), c.ALL_ARTIFACTS)   # another subject
        self.assertEqual(c.field_effects('subject.chosen'), ('beat-map', 'script', 'shot-plan'))   # another angle
        self.assertEqual(c.field_effects('subject.value_to_carry.R2'), ('beat-map', 'script', 'shot-plan'))   # scoped
        for k in ('subject.other_candidates', 'subject.chosen.research', 'subject.scope', 'subject.selection.reasons',
                  'subject.from_references', 'subject.dropped'):
            self.assertEqual(c.field_effects(k), (), k)
        base = self.subj([self.cand('T1', 'how fog forms', 'a phenomenon', 'cold air pools at night',
                                    'it explains where towns sit', 'a morning view understood'), self.alt()])

        def changed(mutate):
            import copy
            d0 = {'subject': copy.deepcopy(base)}
            d1 = {'subject': copy.deepcopy(base)}
            mutate(d1['subject'])
            a, b = c.direction_sections(d0), c.direction_sections(d1)
            return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        self.assertEqual(changed(lambda s: s['candidates'][1].update(reward='a quieter reward')), ['subject.other_candidates'])
        self.assertEqual(changed(lambda s: s['value_to_carry'][0].update(what='the finding, said more exactly')),
                         ['subject.value_to_carry.R1'])
        self.assertEqual(changed(lambda s: s['candidates'][0].update(what_happens='told from the valley floor')),
                         ['subject.chosen'])
        self.assertEqual(changed(lambda s: s['candidates'][0]['strongest_material'][0].update(what='a corrected figure')),
                         ['subject.chosen.research'])
        self.assertIn('subject.selection.candidate', changed(lambda s: s['selection'].update(candidate='T2')))

    def test_the_ledger_records_what_was_read(self):
        led = self.core.ledger_entries('### S1. A study\n- Access: read in full.\n## S2. A page\n- **Access:** indirect\n'
                                       '#### **S3**. News\n- access: snippet\n### S4. Notes\n- Status: likely\n')
        self.assertEqual({k: v['access'] for k, v in led.items()},
                         {'S1': 'read', 'S2': 'indirect', 'S3': 'snippet', 'S4': 'unknown'})

    def test_an_alternative_ruled_out_unread_was_never_compared(self):
        unread = self.cand('T2', 'a forgotten survey error', 'a small mistake with large effects',
                           'a mapmaker draws a valley a mile too far north', 'every later plan inherits the error',
                           'one wrong line explains a dozen failures',
                           material=[{'id': 'M1', 'what': 'the error in the survey sheet', 'certainty': 'established',
                                      'sources': ['S4']}])                  # S4: a search summary, never read
        c = self.cand('T1', 'why dunes sing', 'a natural phenomenon explained', 'sand avalanches hum at one note',
                      'the note comes from the grains, not the wind', 'a sound that turns into a mechanism')
        iss, warn = self.check(self.subj([c, unread]))
        self.assertIn('subject_niche_scope_needs_an_alternative_whose_source_was_read:alternatives_seen_only_in_search_'
                      'summaries_were_never_compared', iss)
        iss, warn = self.check(self.subj([c, unread, self.alt('T3', 1)]))
        self.assertFalse([x for x in iss if 'whose_source_was_read' in x])   # one alternative really read: compared
        self.assertIn('subject_alternative_T2_ruled_out_on_search_summaries_alone:read_its_strongest_source_or_say_'
                      'plainly_the_comparison_was_uneven', warn)

    def test_a_key_moment_on_one_source_is_named(self):
        c = self.core
        mats = [{'id': 'M1', 'what': 'one experiment shifted the spawning', 'certainty': 'established', 'claims': ['C02']}]
        direction = {'subject': {'selection': {'candidate': 'T1'},
                                 'candidates': [{'id': 'T1', 'factual': True, 'strongest_material': mats}],
                                 'value_to_carry': [{'id': 'R1', 'what': 'x', 'certainty': 'established', 'rests_on': ['M1']}]}}
        beats = [{'id': 'B04', 'key_moment': 'the experiment', 'carries': ['R1']}]
        sig = c.key_moment_evidence_signals(direction, beats, self.CLAIMS)
        self.assertEqual(sig, ['key moment B04 carries R1 on single-source claims only (C02): corroborate them, or let '
                               'the script say whose finding it is'])
        mats[0]['claims'] = ['C01']                                               # confirmed: nothing to say
        self.assertEqual(c.key_moment_evidence_signals(direction, beats, self.CLAIMS), [])
        beats[0].pop('key_moment')                                                # an ordinary beat: not this signal
        mats[0]['claims'] = ['C02']
        self.assertEqual(c.key_moment_evidence_signals(direction, beats, self.CLAIMS), [])

    def test_a_treatment_sample_needs_no_turning_point(self):
        c = self.core
        samples = {'opening': {'narration': 'a'}, 'quiet_middle': {'narration': 'b'},
                   'strongest_moment': {'narration': 'the step that finally works', 'picture': 'the fixed hinge'}}
        self.assertEqual(c.sample_of(samples, 'turning_point')['picture'], 'the fixed hinge')
        self.assertEqual(c.sample_label(samples, 'turning_point'), 'strongest moment')
        self.assertEqual(c.sample_label({'turning_point': {}}, 'turning_point'), 'turning point')

class TopicPathTests(unittest.TestCase):
    """The whole path with real research (2026-11-24). Each recorded exercise in tests/fixtures/topic-research/<scope>
    is a fresh agent's topic discovery by the manual alone, with live web searches, for one user scope: its ledger,
    claims, subject block and a first sketch of beats and shots. The real commands carry it from the locked length and
    the references through the subject check and the direction lock, the beat map and script, the plan check, the shot
    plan and its check, to what the image and music workers would be given; then one researched value is revised and
    must reach only the beats that carry it. The references are the test run's own fixtures (none were processed for
    these niches), the script is placeholder lines carrying the sketch's own hedge sentences, the claims are tied to the
    lines of the beats that carry them as the writer would, and nothing is generated or paid for."""

    FIX = ROOT / 'tests' / 'fixtures' / 'topic-research'
    FORMS = {'history': 'historical narrative', 'geography': 'explainer', 'biology': 'explainer', 'how-to': 'tutorial',
             'what if': 'hypothetical'}
    WORDS = ('careful planning and real consequences shaped every difficult choice and practical tradeoff through time '
             'and constrained people with different information under meaningful pressure at each stage')
    report = {}

    @classmethod
    def tearDownClass(cls):
        out = os.environ.get('TOPIC_PATH_REPORT')
        if out and cls.report:
            Path(out).write_text(json.dumps(cls.report, indent=1, ensure_ascii=False), encoding='utf-8')

    @staticmethod
    def add_payoff(subject, sketch):
        """The recorded exercises predate the payoff assessment (2026-11-24): when the chosen candidate has none, the
        one its own sketch implies is added, never invented: the value a key-moment beat carries is a payoff the film
        builds to; otherwise the value most beats carry is delivered progressively."""
        cands = {str(c['id']): c for c in subject['candidates']}
        ch = cands[str(subject['selection']['candidate'])]
        if isinstance(ch.get('payoff'), dict):
            return
        keyed = [str(r) for b in sketch['beats'] if b.get('key_moment') for r in b.get('carries') or []]
        counts = {}
        for b in sketch['beats']:
            for r in b.get('carries') or []:
                counts[str(r)] = counts.get(str(r), 0) + 1
        vals = {str(v['id']): v for v in subject['value_to_carry']}
        pid = next((r for r in keyed if r in vals), None)
        shape = 'builds_to' if pid else 'progressive'
        if not pid:
            pid = max((r for r in counts if r in vals), key=lambda r: counts[r])
        mids = {str(m.get('id')) for m in ch.get('strongest_material') or [] if isinstance(m, dict)}
        rests = [m for m in vals[pid].get('rests_on') or [] if m in mids]
        ch['payoff'] = {'shape': shape, 'rests_on': rests or sorted(mids)[:1],
                        'why_substantial': str(ch.get('reward') or ch.get('why_it_matters')),
                        'needs_first': 'what the first beats establish about the subject',
                        'worth_the_buildup': str((ch.get('runtime') or {}).get('why') or ch.get('why_it_matters'))}
        vals[pid]['payoff'] = True

    def run_path(self, name):
        fx = self.FIX / name
        if not (fx / 'subject.json').is_file():
            self.skipTest(f'no recorded exercise {name}')
        subject = json.loads((fx / 'subject.json').read_text(encoding='utf-8'))
        subject = subject.get('subject', subject)
        sketch = json.loads((fx / 'plan-sketch.json').read_text(encoding='utf-8'))
        claims = json.loads((fx / 'claims.json').read_text(encoding='utf-8'))
        niche = subject['scope']['niche']
        form = self.FORMS.get(str(niche).lower(), 'explainer')
        h = StaticStudioTests('test_prepare_index_and_images_dry_run')
        h.setUp()
        self.addCleanup(h.doCleanups)
        run, rep = h.run, {'scope': subject['scope'], 'chosen': subject['selection']['candidate']}
        for i in (1, 2):      # the fixture references, labelled for this niche (none were processed for it)
            cp = run / f'20-analysis/cards/V{i:03}.json'
            card = json.loads(cp.read_text(encoding='utf-8'))
            card.update(niches=[niche], story_form=form)
            save(cp, card)
        rp = run / '30-research/video-01'
        shutil.copyfile(fx / 'sources.md', rp / 'sources.md')
        save(rp / 'claims.json', claims)
        cli('length', '--run', run, '--video', 1, '--mode', 'standard', '--niche', niche, '--story-form', form,
            '--refs', 'V001,V002', '--pace-wpm', 145, '--pace-why', 'the test narrator reads at this pace')
        vd = run / '40-plans/video-01'
        blue = {'audience_promise': subject.get('audience_value'), 'central_question': 'What does the research show?',
                'narrative_approach': 'one subject followed through its researched progression',
                'why_this_length': 'the progression of the chosen material', 'original_angle': 'the chosen angle',
                'human_lens': 'the people or the viewer inside it', 'visual_grammar': 'maps, drawings, illustrated stills',
                'factuality': 'factual', 'research_sources': ['S1'], 'title': 'A test title',
                'audience_knows': 'the everyday basics of the subject, none of its research'}
        blue.update(sketch.get('blueprint') or {})
        save(vd / 'blueprint.json', blue)
        h.measure_refs()
        if not subject.get('from_references'):
            # the fixture references' own moment (no real reference was processed for this niche)
            subject['from_references'] = [{'ref': 'V001', 'at': '00:10-00:30',
                                           'observed': 'the narrator names the cost before the decision',
                                           'interpretation': 'the stakes come before the turn, so the turn lands'}]
        self.add_payoff(subject, sketch)
        sc_ = subject['scope']
        if str(sc_.get('kind')).lower() == 'niche':
            # the recorded exercises predate the niche's line (2026-11-24): their own words stand in for it
            sc_.setdefault('understood_as', f'{sc_.get("niche")} as the user asked for it: {sc_.get("user_words")}')
            sc_.setdefault('boundary', f'a subject outside {sc_.get("niche")}, told only with its techniques')
        iss, warn = h.load_core().subject_issues(subject, (rp / 'sources.md').read_text(encoding='utf-8'), 600,
                                                 ('V001', 'V002'), niche, claims)
        rep['subject_issues'], rep['subject_warnings'] = iss, warn
        self.assertEqual(iss, [], (name, iss))
        d = h.direction_doc()
        d['subject'] = subject
        payv = [str(v['id']) for v in subject['value_to_carry'] if v.get('payoff') is True]
        for t in d['treatments']:
            t['carries_values'] = [{'value': p, 'how': f'treatment {t["id"]} lets the researched progression deliver it'}
                                   for p in payv]
        save(vd / 'direction.json', d)
        packet = cli('review-packet', '--run', run, '--video', 1, '--kind', 'treatment')
        meta = json.loads((vd / 'reviews' / 'packet-treatment-r1.json').read_text(encoding='utf-8'))
        doc = {'reviewer': 'test reader', 'findings': []}
        if meta.get('scope_request'):
            doc['on_request'] = {lab: 'yes: it stays on what was asked' for lab in meta['labels']}
            rep['treatment_reader_asked'] = meta['scope_request']
        save(Path(packet['findings_file']), doc)
        cli('review-record', '--run', run, '--video', 1, '--kind', 'treatment')
        lock = cli('direction-lock', '--run', run, '--video', 1, expected=None)
        self.assertTrue(lock.get('ok'), (name, lock))
        # the beat map and a placeholder script from the sketch; each hedge sentence becomes a line of its beat
        vals = {str(v['id']): v for v in subject['value_to_carry']}
        cands = {str(c['id']): c for c in subject['candidates']}
        mats = {str(m.get('id')): m for m in cands[str(subject['selection']['candidate'])].get('strongest_material') or []}
        sb = sketch['beats']
        per = [52 // len(sb) + (1 if i < 52 % len(sb) else 0) for i in range(len(sb))]
        lines, beats, k, t = [], [], 0, 0.0
        cl = {c['id']: c for c in claims['claims']}
        for b, cnt in zip(sb, per):
            first = k + 1
            for _ in range(cnt):
                k += 1
                lines.append({'id': f'L{k:03}', 'text': self.WORDS + ' changed.', 'pause_after_s': 0})
            carried = [str(r) for r in b.get('carries') or []]
            beat = {'id': b['id'], 'start_s': round(t, 1), 'end_s': round(t + 600 * cnt / 52, 1), 'line_start': first,
                    'line_end': k, 'carries': carried}
            t += 600 * cnt / 52
            for key, default in (('narrative_job', 'deliver what the research found here'),
                                 ('experience', 'the viewer understands something new'),
                                 ('narration_direction', 'plain and curious'), ('visual_intent', 'a purposeful picture'),
                                 ('sound_direction', 'room tone and a light bed'), ('pace', 'unhurried')):
                beat[key] = b.get(key) or default
            hedges, slot = {}, first
            for r, sentence in (b.get('hedges') or {}).items():
                if r not in carried or slot > k:
                    continue
                words = str(sentence).split()
                lines[slot - 1]['text'] = ' '.join(words + self.WORDS.split()[:max(0, 26 - len(words))]) + '.'
                hedges[r] = f'L{slot:03}'
                slot += 1
            if b.get('key_moment'):
                sig = dict(b.get('significance') or {})
                dep = sig.pop('depends_on', None) or b.get('depends_on')
                if isinstance(dep, list) and all(isinstance(x, dict) and x.get('from') for x in dep):
                    beat['depends_on'] = dep
                elif dep and beats:
                    beat['depends_on'] = [{'what': str(dep), 'from': beats[-1]['id']}]
                elif not sig.get('self_contained'):
                    sig['self_contained'] = 'everything it needs is given inside this beat'
                if str(sig.get('certainty') or '').lower() in ('contested', 'speculative'):
                    sig['hedge'] = next(iter(hedges.values()), f'L{first:03}')
                beat.update(key_moment=b['key_moment'], significance=sig)
            elif hedges:
                beat['hedges'] = hedges
            for r in carried:          # the writer ties each carried value's claims to a line of its beat
                ms = list(vals.get(r, {}).get('rests_on') or [])
                ms += [f for m in list(ms) for f in (mats.get(m) or {}).get('from') or []]
                for c in {c for m in ms for c in (mats.get(m) or {}).get('claims') or []}:
                    if c in cl and f'L{first:03}' not in cl[c].setdefault('line_refs', []):
                        cl[c]['line_refs'].append(f'L{first:03}')
            beats.append(beat)
        save(rp / 'claims.json', claims)
        save(vd / 'script.json', {'language': 'en', 'pace_wpm': 145, 'lines': lines, 'tags_exception': TAG_EXCEPTION})
        save(vd / 'beat-map.json', {'target_length_s': 600, 'beats': beats})
        # the placeholder script's comprehension signals (the exercise's own hedge sentences, placed one per line by this
        # harness) classified as the editorial stage would: kept, since the harness, not a writer, put them there
        sig = h.load_core().comprehension_signals(lines, beats, 145, 'en')
        comp = ''.join(f'- {x.split(":")[0].split("-")[0]}: necessary_complexity: the recorded sentences placed here by '
                       'the test harness, kept as written\n' for x in sig)
        (vd / 'editorial-review.md').write_text('## Self-audit\nNotes.\n' + ('## Comprehension\n' + comp if comp else ''),
                                                encoding='utf-8')
        h.review_script()
        pc = cli('plan-check', '--run', run, '--video', 1, expected=None)
        rep['plan_check_issues'] = pc['issues']
        self.assertTrue(pc['ready'], (name, pc['issues']))
        # the shot plan from the sketch: each beat's lines shared among its shots
        shots, comps, notes = [], ['wide', 'close', 'detail', 'medium'], {}
        for b in beats:
            mine = [s for s in sketch['shots'] if str(s.get('beat_id')) == b['id']] or [{}]
            span = list(range(b['line_start'], b['line_end'] + 1))
            cut = [span[i * len(span) // len(mine):(i + 1) * len(span) // len(mine)] for i in range(len(mine))]
            for s, part in zip(mine, cut):
                if not part:
                    continue
                sid = f'S{len(shots) + 1}'
                shots.append({'id': sid, 'beat_id': b['id'], 'line_start': f'L{part[0]:03}', 'line_end': f'L{part[-1]:03}',
                              'composition': comps[len(shots) % 4], 'new_thing': s.get('new_thing') or 'what this beat adds',
                              'frame_prompt': s.get('frame_prompt') or f'an illustrated still for {b["id"]}, one clear subject',
                              **({'carries_significance': s['carries_significance']} if s.get('carries_significance') else {})})
                notes[sid] = s.get('content_note')
        save(run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
        sc = cli('shot-check', '--run', run, '--video', 1, expected=None)
        flagged = sorted({x.split('_prompt_content_flag_unanswered')[0][len('shot_'):] for x in sc['issues']
                          if '_prompt_content_flag_unanswered:' in x})
        if flagged:
            # the house content gate fired on a picture prompt: it stays refused until the director answers it, and
            # the answer is recorded with the sketch (content_note), never invented here
            rep['content_gate_fired'] = {f: next(x for x in sc['issues'] if x.startswith(f'shot_{f}_')) for f in flagged}
            self.assertTrue(all(notes.get(f) for f in flagged), (name, 'unanswered content flags', flagged))
            for x in shots:
                if notes.get(x['id']):
                    x['content_note'] = notes[x['id']]
            save(run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
            sc = cli('shot-check', '--run', run, '--video', 1, expected=None)
        unsure = sorted({x.split('_of_beat_')[0][len('shot_'):] for x in sc['issues'] if '_needs_uncertainty_shown:' in x})
        if unsure:
            # the recorded exercises predate the rule (2026-11-24): the uncertainty gate fired on their contested and
            # speculative beats (the audit's gap, seen in real plans); the sketch's own words when it has them, else a
            # neutral statement the report marks as added here, so the rest of the path is exercised
            rep['uncertainty_gate_fired'] = unsure
            sk = {str(s.get('id') or ''): s for s in sketch.get('shots') or []}
            for x in shots:
                if x['id'] in unsure:
                    x['uncertainty_shown'] = (sk.get(x['id']) or {}).get('uncertainty_shown') or                         'the picture shows the setting only and asserts nothing the research leaves open'
            save(run / '60-visuals/video-01/shot-plan.json', {'video': 1, 'shots': shots})
            sc = cli('shot-check', '--run', run, '--video', 1, expected=None)
        rep['shot_check_issues'] = sc['issues']
        self.assertTrue(sc['ready'], (name, sc['issues']))
        # what the image and music workers would be given
        jobp = h.home / 'job.json'
        cli('style-lock', '--run', run, '--video', 1, '--style-prompt', 'illustrated, muted palette', '--departs-when', 'photorealistic, flat vector')   # the locked look
        save(jobp, {'op': 'generate', 'run': str(run), 'video': 1,
                    'images': [{'shot_id': s['id'], 'prompt': s['frame_prompt'] + ', illustrated, muted palette',
                                'out': str(h.home / f'{s["id"]}.png')} for s in shots]})
        mg = cli('media-check', '--job', jobp, '--kind', 'stills', expected=None)
        self.assertTrue(mg['ok'], (name, mg['issues']))
        by_beat = {b['id']: b for b in beats}
        for item in mg['direction']['items']:
            b = by_beat[item['beat_id']]
            self.assertEqual([v['id'] for v in item.get('carries_values') or []], b['carries'])
            for v in item.get('carries_values') or []:
                self.assertEqual(v['certainty'], vals[v['id']]['certainty'])
                if str(v['certainty']).lower() in ('contested', 'speculative', 'assumed'):
                    self.assertTrue(v.get('framing'), (name, v))      # how sure it is reaches the picture
            if b.get('key_moment'):
                self.assertTrue(item.get('matters_because'), (name, item))      # what the moment means, on every shot
        keys = [b['id'] for b in beats if b.get('key_moment')]
        for k in keys:                       # and at least one shot of each key moment says how its picture carries it
            self.assertTrue(any(i.get('carries_significance') for i in mg['direction']['items'] if i['beat_id'] == k),
                            (name, k))
        if keys:
            save(jobp, {'run': str(run), 'video': 1, 'tracks': [{'beats': keys, 'caption': 'a bed under these moments',
                                                                 'serves': 'a quiet bed that leaves these moments their weight'}]})
            mu = cli('media-check', '--job', jobp, '--kind', 'music', expected=None)
            self.assertTrue(mu['ok'] and all(mu['direction']['items'][0]['beats'][k].get('key_moment') for k in keys),
                            (name, mu))
        # one researched value revised: only the beats that carry it, their lines and their shots
        r = next(r for b in beats for r in b['carries'])
        d = json.loads((vd / 'direction.json').read_text(encoding='utf-8'))
        for v in d['subject']['value_to_carry']:
            if str(v['id']) == r:
                v['what'] = str(v['what']) + ' (said more exactly)'
        save(vd / 'direction.json', d)
        rev = cli('direction-lock', '--run', run, '--video', 1, '--revise', f'{r} said more exactly', expected=None)
        self.assertTrue(rev.get('ok'), (name, rev))
        req = json.loads((vd / 'direction-lock.json').read_text(encoding='utf-8'))['required']
        want = sorted(b['id'] for b in beats if r in b['carries'])
        self.assertEqual(sorted(req['beat-map']['parts']), want)
        self.assertEqual(sorted(req['shot-plan']['parts']), sorted(s['id'] for s in shots if s['beat_id'] in want))
        self.assertFalse({'stills', 'narration', 'music', 'edit', 'voice', 'style-bible'} & set(rev['affects']))
        rep.update(beats=len(beats), key_moments=keys, values=sorted(vals), shots=len(shots),
                   carried={b['id']: b['carries'] for b in beats if b['carries']},
                   hedged={b['id']: b.get('hedges') for b in beats if b.get('hedges')},
                   image_inputs_example=mg['direction']['items'][0],
                   revision_reached={'value': r, 'beats': want, 'affects': rev['affects']})
        type(self).report[name] = rep

    def test_history(self):
        self.run_path('history')

    def test_geography(self):
        self.run_path('geography')

    def test_human_body(self):
        self.run_path('human-body')

    def test_knife_sharpening(self):
        self.run_path('knife-sharpening')

    def test_moon_vanishes(self):
        self.run_path('moon-vanishes')

    def test_history_after_the_fixes(self):
        # the same history brief, run again once the manual asked for a wide survey first, read finalists, an ending
        # from the subject's own material and single-source key moments attributed or corroborated
        self.run_path('history-r2')

if __name__=='__main__':
    unittest.main()
