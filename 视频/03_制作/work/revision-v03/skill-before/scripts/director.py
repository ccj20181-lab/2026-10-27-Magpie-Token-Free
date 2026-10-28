#!/usr/bin/env python3
"""35-scene real-media/Remotion director contract and deterministic assembly.
The agent writes semantic choices. This module validates them; it never invents a storyboard.
"""
from __future__ import annotations
import argparse, hashlib, json, math, shutil
from pathlib import Path
from brand_profiles import apply_brand_defaults
from caption_aliases import apply_caption_aliases, validate_caption_aliases
from source_highlights import validate_source_highlights, validate_source_camera

ROOT=Path(__file__).resolve().parent.parent
EFFECTS={'list','steps','comparison','relationship','timeline','highlight'}
TYPES={'real_screenshot','real_recording','motion_effect'}
DEFAULT_MIX={'real':22,'motion':13,'ai':0}

def read(p): return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok: raise ValueError(msg)
def ids(n=35): return [f'scene_{i:02d}' for i in range(1,n+1)]

def validate_narration(n,formal=False):
 require(n.get('schema_version')=='1.0','narration schema must be 1.0')
 require(n.get('brand')=='ai-coach','AI coach brand required')
 require(n.get('status') in {'draft','confirmed'},'invalid narration status')
 require(not formal or n['status']=='confirmed','formal assembly requires confirmed narration')
 require([s.get('id') for s in n.get('scenes',[])]==ids(),'new AI coach standard requires 35 ordered scenes')
 for s in n['scenes']:
  require(all(s.get(k) for k in ['narration','intent']),f"{s['id']}: missing narration/intent")
  require(isinstance(s.get('evidence_needed'),list),f"{s['id']}: evidence_needed must be a list")
  validate_caption_aliases(s.get('caption_aliases',[]),s['narration'])

def validate_effect(e):
 require(isinstance(e,dict) and isinstance(e.get('id'),str) and e['id'].strip(),'effect requires a nonempty id')
 require(isinstance(e.get('params'),dict),'effect params must be an object')
 require(e.get('renderer') in {None,'builtin','custom'},'invalid effect renderer')
 require(e.get('renderer')!='builtin' or e['id'] in EFFECTS,'unknown builtin effect; implement a custom component')
 if e.get('renderer')=='custom' or e['id'] not in EFFECTS:return
 p=e.get('params',{});items=p.get('items',[])
 require(isinstance(p.get('title'),str) and p['title'].strip() and isinstance(items,list),'builtin effect requires title and items')
 limits={'list':(3,6),'steps':(3,6),'comparison':(2,2),'relationship':(2,4),'timeline':(3,5),'highlight':(1,3)}
 lo,hi=limits[e['id']];require(lo<=len(items)<=hi,f"{e['id']} needs {lo}..{hi} items")
 require(all(isinstance(x,dict) and isinstance(x.get('label'),str) and x['label'].strip() and isinstance(x.get('detail',''),str) for x in items),'effect items require string label/detail')
 for x in items:
  require(len(x['label'])<=24 and len(x.get('detail',''))<=60,'effect text exceeds readable capacity; choose another visual instead of tiny type')

def material_mix_report(p):
 scenes=p['scenes']
 counts={'real':sum(s.get('visual_type','').startswith('real_') for s in scenes),
         'motion':sum(s.get('visual_type')=='motion_effect' for s in scenes),
         'ai':sum(s.get('visual_type')=='ai_image' for s in scenes)}
 notes=[]
 if counts!=DEFAULT_MIX:
  notes.append('Default is 22 real / 13 Remotion / 0 AI; review content-driven deviations.')
  if not p.get('material_mix_rationale'):notes.append('Record material_mix_rationale for the deviation.')
 return {'counts':counts,'default':dict(DEFAULT_MIX),'rationale':p.get('material_mix_rationale'),'notes':notes}

def validate_plan(path,formal=False):
 p=read(path);npath=Path(p['narration_path']);n=read(npath);validate_narration(n,formal)
 require(p.get('schema_version')=='1.0','visual plan schema must be 1.0')
 require(p.get('project_id')==n.get('project_id'),'project mismatch')
 require(p.get('narration_sha256')==sha(npath),'narration changed; re-evaluate visual plan')
 require([s.get('id') for s in p.get('scenes',[])]==ids(),'visual plan needs 35 ordered scenes')
 for s,t in zip(p['scenes'],n['scenes']):
  sid=s['id'];require(s.get('narration')==t['narration'],f'{sid}: narration changed')
  require(s.get('caption_aliases',[])==t.get('caption_aliases',[]),f'{sid}: caption aliases changed')
  require(s.get('visual_type') in TYPES,f'{sid}: invalid visual type')
  for k in ['audience_takeaway','selection_reason','content_description','framing','timing']:
   require(bool(s.get(k)),f'{sid}: missing {k}')
  if s['visual_type'].startswith('real_'):
   require(s.get('media_surface','desktop') in {'desktop','phone'},f'{sid}: media_surface must be desktop or phone')
   require(s.get('capture_request_id'),f'{sid}: missing capture_request_id')
   r=s.get('capture_request',{});require(all(r.get(k) for k in ['purpose','required_events','framing','readability_requirements']),f'{sid}: incomplete capture request')
  else:validate_effect(s.get('effect'))
 mix=material_mix_report(p)['counts']
 require(mix['real']>=20,'real screenshots/recordings require at least 20 scenes')
 require(mix['motion']>0,'Remotion explanation scenes required')
 return p,n

def export_requests(path,out,reuse_manifest=None):
 p,n=validate_plan(path);requests={}
 reused=read(reuse_manifest) if reuse_manifest else None
 require(not reused or reused.get('project_id')==p['project_id'],'reuse manifest must be mapped to this video project')
 reused_assets={}
 for s in p['scenes']:
  if s['visual_type'].startswith('real_'):
   rid=s['capture_request_id'];kind='recording' if s['visual_type']=='real_recording' else 'screenshot'
   available=[a for a in (reused or {}).get('assets',[]) if a.get('request_id')==rid and a.get('type')==kind and s['id'] in a.get('scene_ids',[])]
   if available:
    asset=resolve_assets({'project_id':p['project_id'],'scenes':[s]},reused,None)[s['id']]
    key=asset.get('asset_id') or (rid,kind,asset['path'])
    reused_assets[key]=asset
    continue
   item=dict(s['capture_request']);item.update(id=rid,scene_ids=[s['id']],app=item.get('app','WorkBuddy'),deliverables=[kind])
   if rid in requests:
    previous=requests[rid]
    require(previous['purpose']==item['purpose'],f'{rid}: shared request has conflicting purpose')
    previous['scene_ids'].append(s['id']);previous['deliverables']=sorted(set(previous['deliverables']+[kind]));previous['required_events']=list(dict.fromkeys(previous['required_events']+item['required_events']))
   else:requests[rid]=item
 write(Path(out)/'capture_request.json',{'schema_version':'1.0','project_id':p['project_id'],'consumer':'video','requests':list(requests.values())})
 if reused is not None:
  write(Path(out)/'reused_capture_manifest.json',{'schema_version':'1.0','project_id':p['project_id'],'assets':list(reused_assets.values())})
 write(Path(out)/'material_mix_report.json',material_mix_report(p))
 lines=['# 35幕画面安排','|幕|口播|主视觉|具体画面|选择理由|取景与时间|','|---|---|---|---|---|---|']
 for s in p['scenes']:
  vals=[s['id'],s['narration'],s['visual_type'],s['content_description'],s['selection_reason'],str(s['framing'])+'；'+str(s['timing'])]
  lines.append('|'+ '|'.join(str(x).replace('|','／').replace('\n',' ') for x in vals)+'|')
 (Path(out)/'35幕画面安排.md').write_text('\n'.join(lines))
 return {'capture_requests':len(requests),'reused_assets':len(reused_assets),'image_requests':0,'material_mix':material_mix_report(p)}

def resolve_assets(p,capture,images):
 require(not capture or capture.get('project_id')==p['project_id'],'capture project mismatch')
 assets=(capture or {}).get('assets',[]);bound={}
 for s in p['scenes']:
  sid=s['id'];typ=s['visual_type']
  require(typ in TYPES,f'{sid}: invalid visual type; AI images are disabled')
  if typ.startswith('real_'):
   kind='recording' if typ=='real_recording' else 'screenshot'
   options=[a for a in assets if a.get('request_id')==s['capture_request_id'] and a.get('type')==kind and sid in a.get('scene_ids',[])]
   if s.get('capture_asset_id'):
    options=[a for a in options if a.get('asset_id')==s['capture_asset_id']]
   require(len(options)==1,f'{sid}: select exactly one requested real asset, found {len(options)}')
   a=options[0];require(a.get('qa',{}).get('status')=='accepted',f'{sid}: source has not passed QA')
   validate_source_highlights(a)
   require(a.get('semantic_support'),f'{sid}: missing semantic evidence')
  else:bound[sid]={'effect':s['effect']};continue
  path=Path(a.get('path',''));require(path.is_absolute() and path.is_file(),f'{sid}: missing absolute asset path')
  require(not a.get('sha256') or a['sha256']==sha(path),f'{sid}: asset changed after QA')
  if a.get('crop'):
   rect=a['crop'];require(len(rect)==4 and all(isinstance(v,(int,float)) for v in rect),f'{sid}: invalid crop')
   x,y,w,h=rect;require(x>=0 and y>=0 and w>0 and h>0 and x+w<=a.get('width',0) and y+h<=a.get('height',0),f'{sid}: crop outside source')
  bound[sid]=a
 return bound

def assemble(plan_path,capture_path,image_path,out,audio_manifest=None,formal=False):
 p,n=validate_plan(plan_path,formal);bound=resolve_assets(p,read(capture_path) if capture_path else None,read(image_path) if image_path else None)
 p=apply_brand_defaults(p,project_dir=Path(p['narration_path']).parent)
 from render_ai_coach_demo import load_env_file,synthesize_audio,copy_public,ffprobe_duration_seconds,caption_segments,probe_audio_duration_ms,ffprobe_dimensions
 from ai_coach_demo_builder import public_slug
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);slug=public_slug(n['project_id']+'-director-v2')
 meta=brand_metadata(p,slug,copy_public)
 if audio_manifest:
  amap=read(audio_manifest)['scenes'];audio={}
  for s in n['scenes']:
   a=amap[s['id']];require(a.get('text')==s['narration'],f"{s['id']}: audio text mismatch")
   ap=Path(a['path']);require(ap.is_file(),f'missing audio {ap}')
   require(not formal or a.get('provider')=='minimax','formal audio must retain approved MiniMax route')
   audio[s['id']]={'path':ap,'ms':probe_audio_duration_ms(ap)}
 else:
  load_env_file();made=synthesize_audio(out,{'scenes':n['scenes']},speed=1.13,force=False,preview=not formal)
  audio={k:{'path':v.path,'ms':v.duration_ms} for k,v in made.items()}
 payload=[];bindings=[]
 for s in p['scenes']:
  sid=s['id'];a=bound[sid];au=audio[sid];dur=max(1,math.ceil(au['ms']*30/1000))
  item={'id':sid,'kind':'effect' if s['visual_type']=='motion_effect' else 'video' if s['visual_type']=='real_recording' else 'image','visualType':s['visual_type'],'layout':'recording' if s['visual_type'].startswith('real_') else 'illustration','headline':s['audience_takeaway'],'caption':s['narration'],'durationFrames':dur,'audioPath':copy_public(au['path'],slug,f'audio/{sid}{au["path"].suffix}'),'assetPath':'','captionSegments':caption_segments(s['narration'],audio_duration_ms=au['ms'],duration_frames=dur),'semanticRole':s.get('semantic_role','explain')}
  item['captionSegments']=apply_caption_aliases(item['captionSegments'],s.get('caption_aliases',[]))
  if 'effect' in a:item['effect']=a['effect']
  else:
   src=Path(a['path']);actual_size=ffprobe_dimensions(src);require(actual_size==(a.get('width'),a.get('height')),f'{sid}: source dimensions changed or missing');item['assetPath']=copy_public(src,slug,f'visuals/{sid}{src.suffix}');item.update(sourceWidth=a.get('width'),sourceHeight=a.get('height'),mediaSurface=s.get('media_surface','desktop'))
   camera=validate_source_camera(s.get('source_camera'),a['width'],a['height'],dur)
   if camera:item['sourceCamera']=camera
   if a.get('highlights'):item['sourceHighlights']=a['highlights']
   if a.get('redactions'):
    validate_source_highlights(dict(a,highlights=a['redactions']))
    item['sourceRedactions']=a['redactions']
   if item['kind']=='video':
    start=float(s.get('source_start_seconds',0));length=ffprobe_duration_seconds(src)
    require(start>=0 and length-start>=dur/30+0.5,f'{sid}: source video does not cover narration + 0.5s margin')
    item['mediaStartFrame']=round(start*30)
  bindings.append({'scene_id':sid,'visual_type':s['visual_type'],'asset_path':a.get('path'),'asset_sha256':sha(a['path']) if a.get('path') else None,'audio_sha256':sha(au['path']),'duration_frames':dur,'effect':a.get('effect')})
  payload.append(item)
 meta.update(workflowVersion=2,episode=str(p.get('episode','测试')),demoTitle=n['title'],fps=30,width=1080,height=1920)
 data={'meta':meta,'scenes':payload}
 write(out/'remotion_props.json',{'data':data});write(out/'scene_bindings.json',{'schema_version':'1.0','formal':formal,'narration_sha256':sha(p['narration_path']),'scenes':bindings})
 write(out/'material_mix_report.json',material_mix_report(p))
 write(out/'visual_plan.lock.json',p);write(out/'narration.lock.json',n)
 return out/'remotion_props.json'

def brand_metadata(plan,slug,copy_public):
 from render_ai_coach_demo import prepare_bgm
 p=apply_brand_defaults(plan,project_dir=Path(plan['narration_path']).parent if plan.get('narration_path') else None)
 corner=p.get('corner_logo') or {}
 meta={'brandProfile':p['brand_profile'],'seriesTitle':p['series_title'],'showEpisodeMarker':bool(p.get('show_episode_marker',True)),
       'motionStyle':p.get('motion_style') or ('caishu-editorial-v1' if p['brand_profile']=='caishu_ai_lab' else 'white-line-v1')}
 logo=p.get('corner_logo_path') or corner.get('path') or p.get('corner_logo_image')
 if logo:
  lp=Path(logo).expanduser().resolve();require(lp.is_file(),f'brand logo missing: {lp}')
  meta['cornerLogoPath']=copy_public(lp,slug,f'brand/{lp.name}')
 for src,dst,default in [('width','cornerLogoWidth',136),('height','cornerLogoHeight',136),('padding_x','cornerLogoPaddingX',0),('padding_y','cornerLogoPaddingY',0),('border_radius','cornerLogoBorderRadius',0)]:
  meta[dst]=corner.get(src,default)
 meta['cornerLogoBackground']=corner.get('background')
 meta['bgm']=prepare_bgm(p,slug,copy_public)
 if meta['bgm'] is None:meta['bgmOmissionReason']=p['bgm']['omission_reason']
 return meta

def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
 for name in ['validate','requests','assemble']:
  sp=sub.add_parser(name);sp.add_argument('--plan',required=True)
  if name!='validate':sp.add_argument('--out',required=True)
  if name=='assemble':
   sp.add_argument('--capture');sp.add_argument('--images');sp.add_argument('--audio-manifest');sp.add_argument('--formal',action='store_true')
  if name=='requests':sp.add_argument('--reuse-manifest',help='Accepted article assets already mapped to this video project')
 a=ap.parse_args()
 if a.cmd=='validate':
  p,_=validate_plan(a.plan);print(json.dumps(material_mix_report(p),ensure_ascii=False,indent=2));print('35-scene semantic plan structure passed; custom implementation and visual judgment remain required')
 elif a.cmd=='requests':print(export_requests(a.plan,a.out,a.reuse_manifest))
 else:print(assemble(a.plan,a.capture,a.images,a.out,a.audio_manifest,a.formal))
if __name__=='__main__':main()
