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

    def write_plan(self):
        cli('length','--run',self.run,'--video',1,'--mode','standard','--niche','military history',
            '--story-form','historical narrative','--refs','V001,V002','--pace-wpm',145)
        vd=self.run/'40-plans/video-01'
        save(vd/'blueprint.json',{'audience_promise':'Understood decision','central_question':'What happened?',
                                'narrative_approach':'Third-person procedural account of a single decision',
                                'why_this_length':'Five discoveries','original_angle':'Logistical stakes',
                                'human_lens':'People at crossroads','ending_payoff':'An earned conclusion',
                                'visual_grammar':'Maps and restrained artifacts','factuality':'factual',
                                'research_sources':['S1','S2']})
        words='careful planning and real consequences shaped every difficult choice and practical tradeoff through time and constrained people with different information under meaningful pressure at each stage'
        self.assertEqual(len(words.split()),26)
        lines=[{'id':f'L{i:03}','text':words+ ' changed.', 'pause_after_s':0} for i in range(1,53)]
        # Each line 27 spoken tokens x 52 = 1404: about 581 seconds at 145 wpm.
        save(vd/'script.json',{'language':'en','pace_wpm':145,'lines':lines})
        beats=[{'id':f'B{i:02}','start_s':(i-1)*120, 'end_s':i*120,
                'line_start':(i-1)*10+1 if i<5 else 41,
                'line_end':i*10 if i<5 else 52,
                'narrative_job':'genuinely deliver new evidence','visual_intent':'a purposeful comparison'} for i in range(1,6)]
        save(vd/'beat-map.json',{'target_length_s':600,'beats':beats})
        (vd/'editorial-review.md').write_text('Evidence, exit risks, revisions made.',encoding='utf-8')
        return vd

    def test_plan_audio_partial_and_timeline(self):
        vd=self.write_plan()
        self.assertTrue(cli('plan-check','--run',self.run,'--video',1)['ready'])
        dry=cli('tts','--run',self.run,'--video',1,'--voice-id','TESTID','--model-id','eleven_v4')
        self.assertEqual(dry['mode'],'dry_run_no_charges')
        self.assertGreater(dry['characters_total'],1000)
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

    def test_legacy_not_imported_and_clone_keeps_only_analysis(self):
        clone=cli('clone','--from-run',self.run,'--workspace',self.home/'runs')['run']
        cp=Path(clone)
        self.assertTrue((cp/'20-analysis/cards/V001.json').exists())
        self.assertFalse((cp/'40-plans/video-01/length-lock.json').exists())
        self.assertEqual(json.loads((cp/'state.json').read_text())['selected_niche'],None)
        self.assertFalse(cli('status','--run',cp)['videos'])


if __name__=='__main__':
    unittest.main()
