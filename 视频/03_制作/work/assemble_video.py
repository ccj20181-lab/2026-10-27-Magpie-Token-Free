# -*- coding: utf-8 -*-
from pathlib import Path
import sys,json,hashlib,math,shutil
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,'/Users/henry/Desktop/财叔 AI Lab/.agents/skills/ai-coach-daily-demo/scripts')
import director
import render_ai_coach_demo as renderer
renderer.PUBLIC_ROOT=p/'remotion/public/ai-coach-daily-demo'
out=p/'work/candidate-v01'
director.assemble(p/'visual_plan.json',p/'capture_manifest.json',None,out,p/'audio_manifest.json',True)
props=out/'remotion_props.json';data=json.loads(props.read_text())
captions=json.loads((p/'work/caption-overrides.json').read_text())
manifest=json.loads((p/'capture_manifest.json').read_text())
assets={a['asset_id']:a for a in manifest['assets']}
plan=json.loads((p/'visual_plan.json').read_text())
mapped={s['id']:s for s in plan['scenes']}
def stage_asset(a,relative):
 path=Path(a['path']);result={'assetPath':renderer.copy_public(path,'magpie-04-evidence',relative+path.suffix),'sourceWidth':a['width'],'sourceHeight':a['height']}
 for src,dst in [('crop','sourceRect'),('redactions','sourceRedactions'),('highlights','sourceHighlights')]:
  if a.get(src):result[dst]=a[src]
 return result
for s in data['data']['scenes']:
 s['captionSegments']=captions[s['id']]
 req=mapped[s['id']]
 if req.get('capture_asset_id'):
  a=assets[req['capture_asset_id']]
  if a.get('redactions'):s['sourceRedactions']=a['redactions']
  if req.get('evidence_sequence'):
   seq=[]
   for i,e in enumerate(req['evidence_sequence']):
    asset=assets[e['asset_id']]
    assert asset['qa']['status']=='accepted'
    assert director.sha(asset['path'])==asset['sha256']
    seq.append({'fromFrame':e['from_frame'],**stage_asset(asset,s['id']+'-'+str(i))})
   s['evidenceSequence']=seq
props.write_text(json.dumps(data,ensure_ascii=False,indent=2))
timeline=[];cursor=0;subtitle=[];counter=0
def stamp(frame):
 ms=round(frame*1000/30);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02},{ms:03}'
for s in data['data']['scenes']:
 timeline.append({'id':s['id'],'start_frame':cursor,'duration_frames':s['durationFrames'],'visual_type':s['visualType']})
 for c in s['captionSegments']:
  counter+=1;subtitle.append(f'{counter}\n{stamp(cursor+c["startFrame"])} --> {stamp(cursor+c["endFrame"])}\n{c["text"]}\n')
 cursor+=s['durationFrames']
(out/'字幕.srt').write_text('\n'.join(subtitle))
(out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
snapshot=out/'source-snapshot';snapshot.mkdir(exist_ok=True)
shutil.copytree(p/'remotion/src',snapshot/'src',dirs_exist_ok=True)
for name in ['package.json','package-lock.json','remotion.config.ts','motion-style.lock.json']:
 shutil.copy2(p/'remotion'/name,snapshot/name)
print('ASSEMBLED',len(timeline),'scenes',cursor,'frames',round(cursor/30,2),'s')
