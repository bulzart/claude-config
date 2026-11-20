"""Smoke tests for the isolated static-only command. No paid API calls."""
from __future__ import annotations
import hashlib
import json
import importlib.util
import io
from unittest import mock
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT/'scripts'/'static_core.py'


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


def save(path, d):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d), encoding='utf-8')


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
                            '-t','0.6','-pix_fmt','yuv420p',str(p)],check=True)
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
                  'viewer_experience':[{'start_s':0, 'end_s':50,'question':'why','evidence':'[O] source'}]}
            save(self.run/f'20-analysis/cards/V{i:03}.json',card)

    def test_prepare_index_and_images_dry_run(self):
        self.assertTrue(cli('prepare','--run',self.run,'--ids','V001','--skip-whisper')['ok'])
        index=self.run/'10-media/V001/frame-index.json'
        self.assertTrue(index.is_file())
        data=json.loads(index.read_text())
        self.assertEqual(data['mode'],'nominal_sample_time')
        self.assertGreaterEqual(len(data['frames']),2)
        self.assertEqual(data['frames'][0]['approx_s'],0.0)
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
              '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145)
        self.assertEqual(r['locked_target_s'],600)
        self.assertEqual(r['pace_wpm_source'],'explicit')
        cli('length','--run',self.run,'--video',1,'--mode','own','--niche','military history',
            '--story-form','historical narrative','--minutes',12,'--pace-wpm',145,expected=2)
        cli('length','--run',self.run,'--video',2,'--mode','own','--niche','how-to',
            '--story-form','tutorial','--minutes',12,'--pace-wpm',145,expected=2)

    # ---- the creative process, run through the real CLI the way an agent would (no media is generated)
    def measure_refs(self):
        cli('prepare','--run',self.run,'--ids','V001,V002','--skip-whisper')
        out=cli('av-profile','--run',self.run,'--refs','V001,V002','--no-sheets')
        self.assertTrue((self.run/'20-analysis/av/V001.json').is_file())
        return out

    @staticmethod
    def direction_doc():
        def say(*parts):   # a sentence with enough words to count as written
            return ' '.join(parts)+' because the story itself asks for it here.'
        def sample(tag):
            return ' '.join([f'{tag} narration sentence number {i} that a viewer hears in this moment.' for i in range(6)])
        treatments=[]
        for tid,tone in (('T1','wry curious friend'),('T2','hushed intimate witness')):
            treatments.append({'id':tid,'name':tone,
                **{k:say(tone,k.replace('_',' '),'for this video') for k in
                   ('narrator','writing_voice','structure_and_pace','visual_language','sound',
                    'audiovisual_relationship','emotional_course','evidence_used','departures','risks')},
                'samples':{m:{'narration':sample(f'{tid} {m}'),
                              'picture':f'{tid} picture for the {m}: a wide frame with one figure and the road ahead.'}
                           for m in ('opening','quiet_middle','turning_point')}})
        return {'video':1,
                'evidence':{'references':['V001','V002'],
                            'observations':[{'ref':'V001','at':'00:00-00:30','what':'the narrator opens on a detail','label':'O'},
                                            {'ref':'V002','at':'02:10-02:40','what':'the picture holds while the voice slows','label':'O'},
                                            {'ref':'V001','at':'05:00-05:20','what':'cuts quicken at the turn','label':'O'}],
                            'unknowns':['audience retention is not available']},
                'approaches':[{'id':f'A{i}','changes':[axis],'pitch':say('pitch',axis),'strongest_case':say('case',axis),
                               'long_form_risk':say('risk',axis),'challenges_reference_formula':i==3}
                              for i,axis in enumerate(['perspective','scale','structure','voice','visualization'],1)],
                'chosen_approach':{'id':'A3','why':say('the structure approach wins'),'runner_up':'A1',
                                   'why_not_runner_up':say('the perspective approach repeats the references')},
                'strategy':{k:say('strategy',k.replace('_',' ')) for k in
                            ('why_this_idea','viewer_experience','progression','fits_and_forced','facts_as_experience',
                             'picture_contribution','sound_and_breath','distinct_from_references')},
                'treatments':treatments,
                'decision':{'treatment':'T1','why':say('the wry friend holds twenty minutes'),
                            'taken_from_others':say('the hushed close of the second treatment')}}

    def review(self, kind, findings, answers=None, file=None, expected_record=0):
        extra=['--file',file] if file else []
        packet=cli('review-packet','--run',self.run,'--video',1,'--kind',kind,*extra)
        self.assertTrue(Path(packet['packet']).is_file())
        save(Path(packet['findings_file']),{'reviewer':'test reader','findings':findings})
        rec=cli('review-record','--run',self.run,'--video',1,'--kind',kind,expected=expected_record)
        if answers is not None:
            save(Path(rec['answers_file']),{'answers':answers})
        return packet,rec

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
            '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145)
        vd=self.run/'40-plans/video-01'
        save(vd/'blueprint.json',{'audience_promise':'Understood decision','central_question':'What happened?',
                                'narrative_approach':'Third-person procedural account of a single decision',
                                'why_this_length':'Five discoveries','original_angle':'Logistical stakes',
                                'human_lens':'People at crossroads','ending_payoff':'An earned conclusion',
                                'visual_grammar':'Maps and restrained artifacts','factuality':'factual',
                                'research_sources':['S1','S2'],'title':'A test title'})
        self.measure_refs()
        if lock:
            self.lock_direction(vd)     # creative direction first: before any script exists
        words='careful planning and real consequences shaped every difficult choice and practical tradeoff through time and constrained people with different information under meaningful pressure at each stage'
        self.assertEqual(len(words.split()),26)
        lines=[{'id':f'L{i:03}','text':words+ ' changed.', 'pause_after_s':0} for i in range(1,53)]
        # Each line 27 spoken tokens x 52 = 1404: about 581 seconds at 145 wpm.
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        beats=[{'id':f'B{i:02}','start_s':(i-1)*120, 'end_s':i*120,
                'line_start':(i-1)*10+1 if i<5 else 41,
                'line_end':i*10 if i<5 else 52,
                'narrative_job':'genuinely deliver new evidence','visual_intent':'a purposeful comparison',
                'experience':'the viewer understands a new constraint','narration_direction':'curious, quickening',
                'sound_direction':'room tone, then a low pulse','pace':'brisk'} for i in range(1,6)]
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
        script['lines'][-1].update({'pause_after_s':5,'pause_via':'edit'})
        save(vd/'script.json',script)
        res=cli('audio-check','--run',self.run,'--video',1,expected=2)
        self.assertNotIn('narration_duration_outside_locked_tolerance',res['issues'])
        self.assertIn('narration_plus_edit_holds_longer_than_export_window',res['issues'])
        self.assertEqual(res['edit_holds_s'],5.0)
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
        ok=cli('plan-check','--run',self.run,'--video',1)
        self.assertTrue(ok['ready'])
        self.assertTrue(any('locked after the script existed' in w for w in ok['warnings']))
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
                      'direction_needs_2_to_3_distinct_treatments',
                      'treatment_T1_sample_quiet_middle_narration_under_50_words',
                      'direction_evidence_without_av_profile:V003'):
            self.assertIn(issue,issues)
        self.assertIn('direction_needs_2_to_3_distinct_treatments',cli('direction-lock','--run',self.run,'--video',1,expected=2)['details'])
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
        save(ans,{'answers':{'F1':{'action':'kept','note':'we like the recap a lot here'}}})   # a major is never just kept
        self.assertIn('script_review_r1_unanswered:F1',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        save(ans,{'answers':{'F1':{'action':'revised','lines':['L003'],'note':''}}})           # claimed, not done
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
        d['strategy']['progression']+=' And a new idea arrives late in the plan.'
        save(vd/'direction.json',d)
        self.assertIn('direction_changed_since_lock',cli('plan-check','--run',self.run,'--video',1,expected=2)['issues'])
        cli('direction-lock','--run',self.run,'--video',1,expected=2)          # a change needs --revise
        cli('direction-lock','--run',self.run,'--video',1,'--revise','progression sharpened after the cold read')
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        d['treatments'][0]['narrator']+=' Now much louder.'
        save(vd/'direction.json',d)                                            # treatments changed after their blind read
        r=cli('direction-lock','--run',self.run,'--video',1,'--revise','narrator changed',expected=2)
        self.assertIn('treatment_review_outdated',r['details'])

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
            '--story-form','historical narrative','--minutes',3,'--pace-wpm',145,expected=2)

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
        self.assertIn('final_review_missing',cli('release-check','--run',self.run,'--video',1,'--file',exp,expected=2)['issues'])
        _,rec=self.review('final',[{'id':'F1','severity':'minor','at':'00:01-00:03',
                                    'problem':'the opening picture holds too long'}],file=exp)
        self.assertIn('final_review_r1_unanswered:F1',cli('release-check','--run',self.run,'--video',1,'--file',exp,expected=2)['issues'])
        save(Path(rec['answers_file']),{'answers':{'F1':{'action':'kept','note':'the hold is the planned breath'}}})
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
        self.assertTrue(any('nearly the same' in w for w in res['warnings']))
        self.assertTrue(any('in a row of the same composition' in w for w in res['warnings']))

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

    def test_legacy_not_imported_and_clone_keeps_only_analysis(self):
        clone=cli('clone','--from-run',self.run,'--workspace',self.home/'runs')['run']
        cp=Path(clone)
        self.assertTrue((cp/'20-analysis/cards/V001.json').exists())
        self.assertFalse((cp/'40-plans/video-01/length-lock.json').exists())
        self.assertEqual(json.loads((cp/'state.json').read_text())['selected_niche'],None)
        self.assertFalse(cli('status','--run',cp)['videos'])


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


if __name__=='__main__':
    unittest.main()
