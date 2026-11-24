#!/usr/bin/env python3
"""Optional image generator for Static Studio using OpenAI's Images API: an ALTERNATIVE to the run's default and primary
engine, FLUX 3 Image Klein int8 on this PC (image_worker.py). It is used only when the user explicitly chose it for the run
(static_core.py image-engine --engine openai --why "<their words>"), and never as a fallback when FLUX fails.

CLI: openai_images_worker.py --job images.json [--execute] [--out-dir DIR] [--retry-unreconciled FILE|all --reason "..."]
Job: {"run":"<RUN>", "video":1, "model":"gpt-image-2.5-flare", "size":"1536x864", "quality":"high",
      "images":[{"id":"S001", "prompt":"<the shot's frame_prompt, plus style words>", "file":"S001.png"}, ...]}

Dry run is free. --execute makes paid requests with OPENAI_API_KEY from environment, and only after Static Studio's
production gate (static_core.media_gate) passes: the run chose this engine, each image's id is a shot of the checked shot
plan, its prompt carries that shot's approved frame_prompt, and the direction, beat map and shot plan are current. The
pictures go to the run's stills folder (60-visuals/video-NN/stills) unless --out-dir says otherwise. Each request goes in the
folder's images-manifest.json BEFORE it is sent ("pending"), then "ready", "failed" (refused before any work: 4xx) or
"uncertain" (cut off, timed out, a server error or an unreadable answer: billed or not is unknown). An image whose earlier
request is pending or uncertain is not sent again until the user has checked the account and allows it
(--retry-unreconciled FILE --reason). Each picture made is recorded (60-visuals/video-NN/stills-provenance.json) with its
shot, beat, direction revision and the exact prompt sent; a reused picture keeps its first record.
No keys in job files or manifest. The agent must review actual images for accuracy.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


def output(data, error=False):
    s = json.dumps(data, indent=2, ensure_ascii=False)
    try:
        s.encode(sys.stdout.encoding or "utf-8")
    except (UnicodeEncodeError, LookupError):
        s = json.dumps(data, indent=2, ensure_ascii=True)   # a code-page pipe cannot hold every character: escaped
    print(s, flush=True)
    if error:
        sys.exit(2)


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--job', required=True)
    p.add_argument('--out-dir')
    p.add_argument('--execute', action='store_true', help='Paid API requests, explicitly opt in')
    p.add_argument('--retry-unreconciled', default='', help='Images (file names, or all) whose earlier paid request has no '
                   'known outcome: send them again after checking the account, with --reason')
    p.add_argument('--reason', default='', help='What you checked before --retry-unreconciled')
    a=p.parse_args()
    jobpath=Path(a.job).expanduser().resolve()
    try:
        job=json.loads(jobpath.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        output({'ok':False,'error':'bad image job: '+str(exc)},True)
    model=job.get('model','gpt-image-2.5-flare')
    size=job.get('size','1536x864')
    quality=job.get('quality','high')
    if not re.fullmatch(r'[0-9]{3,4}x[0-9]{3,4}',str(size)):
        output({'ok':False,'error':'size must be WIDTHxHEIGHT e.g. 1536x864'},True)
    w,h=map(int,size.split('x'))
    if w%16 or h%16 or max(w,h)>3840 or min(w,h)<256 or max(w/h,h/w)>3:
        output({'ok':False,'error':'unsupported candidate dimensions: use multiples of 16, practical 16:9 size and provider supported range'},True)
    imgs=job.get('images',[])
    if not isinstance(imgs,list) or not imgs:
        output({'ok':False,'error':'images must be a nonempty array'},True)
    seen=set()
    requested=[]
    for i,item in enumerate(imgs,1):
        if not isinstance(item,dict) or len(str(item.get('prompt') or '').strip())<20:
            output({'ok':False,'error':f'image {i} missing detailed prompt'},True)
        name=item.get('file') or f'S{i:03d}.png'
        if name in seen or Path(name).name != name or not str(name).lower().endswith('.png'):
            output({'ok':False,'error':f'invalid/duplicate output name: {name}'},True)
        seen.add(name)
        requested.append({'id':item.get('id',f'S{i:03d}'),'file':name,
                          'hash':hashlib.sha256(item['prompt'].encode('utf-8')).hexdigest(),
                          'prompt':item['prompt']})
    # Static Studio's production gate, before any paid call: the run chose this engine, the job names its run and video,
    # every image a shot of the checked shot plan with that shot's approved prompt, and the plan is current.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import static_core
        gate=static_core.media_gate(job,'stills',engine='openai:'+str(model))
    except Exception as exc:  # noqa: BLE001
        gate={'ok':False,'issues':['gate_unavailable: '+type(exc).__name__+': '+str(exc)[:200]]}
    if a.out_dir:
        dest=Path(a.out_dir).expanduser().resolve()
    elif gate.get('run') and gate.get('video') and not gate.get('untracked'):
        dest=Path(gate['run'])/'60-visuals'/f"video-{int(gate['video']):02d}"/'stills'
    else:
        dest=jobpath.parent/'generated'
    if not a.execute:   # free; says whether --execute would pass the gate
        output({'ok':True,'mode':'dry_run_no_charges','model':model,'quality':quality,
                'size':size,'image_count':len(imgs),'output_dir':str(dest),
                'production_gate':{'ok':gate['ok'],'issues':gate['issues']},
                'note':'An alternative to FLUX 3 Image Klein int8 (the default): only on the user\'s explicit choice '
                       '(image-engine). Verify model access and pricing before rerunning with --execute; an API call is '
                       'charged per generation.'})
        return
    if not gate['ok']:
        output({'ok':False,'error':'Static Studio: these stills cannot be generated yet (fix the plan, not the gate).',
                'issues':gate['issues']},True)
    key=os.environ.get('OPENAI_API_KEY')
    if not key:
        output({'ok':False,'error':'OPENAI_API_KEY missing in environment; never embed secrets in source files.'},True)
    dest.mkdir(parents=True, exist_ok=True)
    mf=dest/'images-manifest.json'
    old={}
    if mf.exists():
        try:
            old=json.loads(mf.read_text(encoding='utf-8'))
        except ValueError:
            output({'ok':False,'error':'existing images-manifest.json invalid; do not overwrite blindly'},True)
    if old and (old.get('model') != model or old.get('size') != size or old.get('quality') != quality):
        output({'ok':False,'error':'image model/size changed since generation began; create new folder to preserve provenance'},True)
    prior={x.get('file'):x for x in old.get('results',[])}
    allow={x.strip() for x in str(a.retry_unreconciled or '').split(',') if x.strip()}

    def save(state):
        mf.write_text(json.dumps({'model':model,'size':size,'quality':quality,'status':state,
                                  'results':list(prior.values())},indent=2),encoding='utf-8')
    status=[]
    for row in requested:
        name=row['file'];path=dest/name
        prev=prior.get(name) or {}
        if path.is_file() and path.stat().st_size>1024 and prev.get('hash') == row['hash'] and prev.get('status')=='ready':
            status.append({'file':name,'id':row['id'],'hash':row['hash'],'status':'ready','reused':True})
            continue
        earlier=[]
        if prev.get('hash') == row['hash'] and prev.get('status') in ('pending','uncertain') and not path.exists():
            # an earlier paid request for exactly this picture with no known outcome: never sent again on its own
            if 'all' not in allow and name not in allow:
                output({'ok':False,'error':'An earlier paid request for '+name+' has no known outcome (cut off, timed out '
                        'or unreadable): sending it again could bill it twice, so nothing was sent. Check the OpenAI usage '
                        'page; when it was not billed, or paying again is accepted, re-run with --retry-unreconciled '
                        +name+' --reason "what you checked".','earlier':prev},True)
            if len(str(a.reason or '').split())<4:
                output({'ok':False,'error':'--retry-unreconciled sends a request whose earlier outcome is unknown: say '
                        'what you checked (--reason).'},True)
            earlier=list(prev.get('earlier') or [])+[{**{k:prev.get(k) for k in ('status','at','error')},
                                                      'reconciled_at':now_iso(),'reason':a.reason.strip()}]
        if path.exists():
            output({'ok':False,'error':'Existing image not documented for this exact prompt; never overwrite silently: '+str(path)},True)
        prior[name]={'file':name,'id':row['id'],'hash':row['hash'],'status':'pending','at':now_iso(),'pid':os.getpid(),
                     **({'earlier':earlier} if earlier else {})}
        save('partial')     # on record before the request goes out: a crash or a power cut leaves it pending
        req=urllib.request.Request('https://api.openai.com/v1/images/generations',
              data=json.dumps({'model':model,'prompt':row['prompt'],'size':size,'quality':quality,
                               'n':1,'output_format':'png'}).encode('utf-8'),method='POST',
              headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        state,err=None,None
        try:
            with urllib.request.urlopen(req,timeout=240) as resp:
                content=json.loads(resp.read())
            data=(content.get('data') or [{}])[0].get('b64_json')
            if not data:
                raise RuntimeError('API returned no base64 image')
            raw=base64.b64decode(data,validate=True)
            if len(raw)<1024 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise RuntimeError('API result is not a valid PNG')
            temp=path.with_suffix('.part')
            temp.write_bytes(raw)
            temp.replace(path)
            prior[name]={'file':name,'id':row['id'],'hash':row['hash'],'status':'ready','bytes':len(raw),'at':now_iso(),
                         **({'earlier':earlier} if earlier else {})}
            status.append({'file':name,'id':row['id'],'hash':row['hash'],'status':'ready','bytes':len(raw)})
        except urllib.error.HTTPError as exc:
            # refused before any work (4xx) is not billed; after a server error (5xx) the outcome is unknown
            state='failed' if 400<=int(exc.code or 0)<500 else 'uncertain'
            err='HTTPError '+str(exc.code)+': '+str(exc)[:240]
        except Exception as exc:  # noqa: BLE001  cut off, timed out or unreadable: billed or not is unknown
            state='uncertain'
            err=type(exc).__name__+': '+str(exc)[:240]
        if err:
            prior[name]={'file':name,'id':row['id'],'hash':row['hash'],'status':state,'error':err,'at':now_iso(),
                         **({'earlier':earlier} if earlier else {})}
            status.append(prior[name])
            save('partial')
            output({'ok':False,'status':'partial','results':status,'outcome':state,
                    'note':'Do not pretend absent stills were generated.'+(' This request\'s outcome is unknown: it is '
                           'not sent again until the account was checked (--retry-unreconciled).' if state=='uncertain' else '')},True)
    save('complete')
    provenance=None
    if not gate.get('untracked'):   # which shot each picture shows, made under which direction revision, from what prompt
        made={x['file'] for x in status if x.get('status')=='ready' and not x.get('reused')}
        entries=[{'out':str(dest/row['file']),**rec,'engine':'openai:'+str(model),'submitted_prompt':row['prompt'],
                  'submitted_prompt_sha256':row['hash'],'drew_from':'request'}
                 for row,rec in zip(requested,gate['records']) if row['file'] in made]
        if entries:
            provenance=static_core.record_media(gate['run'],gate['video'],'stills',entries)
    output({'ok':True,'status':'complete','images':len(status),'output_dir':str(dest),'provenance':provenance,
            'note':'Inspect every result; API success cannot verify historical accuracy or shot continuity.'})

if __name__=='__main__':
    main()
