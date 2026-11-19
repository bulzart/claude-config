#!/usr/bin/env python3
"""Optional image generator for Static Studio using OpenAI's Images API.

CLI: openai_images_worker.py --job images.json [--execute]
Job: {"model":"gpt-image-2.5-flare", "size":"1536x864", "quality":"high",
      "images":[{"id":"S001", "prompt":"...", "file":"S001.png"}, ...]}

Dry run is free. --execute makes paid requests with OPENAI_API_KEY from environment.
No keys in job files or manifest. The agent must review actual images for accuracy.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


def output(data, error=False):
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if error:
        sys.exit(2)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--job', required=True)
    p.add_argument('--out-dir')
    p.add_argument('--execute', action='store_true', help='Paid API requests, explicitly opt in')
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
    dest=Path(a.out_dir).expanduser().resolve() if a.out_dir else jobpath.parent/'generated'
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
    if not a.execute:
        output({'ok':True,'mode':'dry_run_no_charges','model':model,'quality':quality,
                'size':size,'image_count':len(imgs),'output_dir':str(dest),
                'note':'Verify model access and pricing before rerunning with --execute; an API call is charged per generation.'})
        return
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
    status=[]
    for row in requested:
        name=row['file'];path=dest/name
        prev=prior.get(name) or {}
        if path.is_file() and path.stat().st_size>1024 and prev.get('hash') == row['hash'] and prev.get('status')=='ready':
            status.append({'file':name,'id':row['id'],'hash':row['hash'],'status':'ready','reused':True})
            continue
        if path.exists():
            output({'ok':False,'error':'Existing image not documented for this exact prompt; never overwrite silently: '+str(path)},True)
        req=urllib.request.Request('https://api.openai.com/v1/images/generations',
              data=json.dumps({'model':model,'prompt':row['prompt'],'size':size,'quality':quality,
                               'n':1,'output_format':'png'}).encode('utf-8'),method='POST',
              headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
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
            status.append({'file':name,'id':row['id'],'hash':row['hash'],'status':'ready','bytes':len(raw)})
        except (urllib.error.HTTPError,urllib.error.URLError,ValueError,RuntimeError,OSError) as exc:
            status.append({'file':name,'id':row['id'],'hash':row['hash'],'status':'blocked',
                           'error':type(exc).__name__+': '+str(exc)[:240]})
            combined=[x for k,x in prior.items() if k not in seen]+status
            mf.write_text(json.dumps({'model':model,'size':size,'quality':quality,'status':'partial','results':combined},indent=2),encoding='utf-8')
            output({'ok':False,'status':'partial','results':status,'note':'Do not pretend absent stills were generated.'},True)
    combined=[x for k,x in prior.items() if k not in seen]+status
    mf.write_text(json.dumps({'model':model,'size':size,'quality':quality,'status':'complete','results':combined},indent=2),encoding='utf-8')
    output({'ok':True,'status':'complete','images':len(status),'output_dir':str(dest),
            'note':'Inspect every result; API success cannot verify historical accuracy or shot continuity.'})

if __name__=='__main__':
    main()
