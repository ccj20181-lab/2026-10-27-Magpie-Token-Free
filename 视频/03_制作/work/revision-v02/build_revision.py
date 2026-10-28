# -*- coding: utf-8 -*-
from pathlib import Path
import json,copy,hashlib,shutil
p=Path(__file__).resolve().parents[2];out=p/'work/candidate-v02';out.mkdir(exist_ok=True)
base=p/'work/candidate-v01';props=json.loads((base/'remotion_props.json').read_text());data=props['data']
manifest=json.loads((p/'work/revision-v02/baseline-v01/capture_manifest.json').read_text())
assets={a['asset_id']:a for a in manifest['assets']}
public=p/'remotion/public';stage=public/'magpie-04-revision-v02';stage.mkdir(exist_ok=True)
for a in assets.values():
 assert hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256'],a['asset_id']
 a.pop('crop',None)
 a['display_policy']='complete_original_window; camera-only emphasis after an establishing hold'
 a['scene_ids']=[]
def visual(aid):
 a=assets[aid];src=Path(a['path']);dst=stage/(aid+src.suffix)
 if not dst.exists():shutil.copy2(src,dst)
 return {'assetPath':str(dst.relative_to(public)),'sourceWidth':a['width'],'sourceHeight':a['height'],'sourceHighlights':[],'sourceRedactions':[]}
def cam(rect,start,end):return {'targetRect':rect,'fromFrame':start,'toFrame':end}
def mark(rect):return [{'rect':rect,'color':'#D93232','strokeWidth':5}]
by_scene={s['id']:s for s in data['scenes']}
plan=json.loads((p/'work/revision-v02/baseline-v01/visual_plan.json').read_text())
planned={s['id']:s for s in plan['scenes']}
mapping={2:'native-agents-still',3:'article-providers',4:'article-models-a',5:'article-codex-config',7:'public-author',8:'public-readme',10:'native-wb-models',19:'public-ccswitch',20:'native-agents-video',21:'article-providers',22:'article-routing',24:'public-qoder',25:'article-plugins',26:'native-model-video',27:'native-tools-result',28:'article-accounts-wb',29:'article-accounts-wbai',30:'public-install',31:'native-prompt',32:'article-accounts-wbai',33:'native-profiles',34:'native-tools-start'}
for i,aid in mapping.items():
 sid=f'scene_{i:02d}';s=by_scene[sid];a=assets[aid]
 s.pop('sourceRect',None);s.pop('evidenceSequence',None);s.pop('sourceCamera',None)
 s.update(visual(aid));s['kind']='video' if a['type']=='recording' else 'image';s['visualType']='real_recording' if s['kind']=='video' else 'real_screenshot'
 if s['kind']=='image':s.pop('mediaStartFrame',None)
 if a.get('highlights'):s['sourceHighlights']=a['highlights']
 if a.get('redactions'):s['sourceRedactions']=a['redactions']
 a['scene_ids'].append(sid)
 q=planned[sid];q.update(visual_type=s['visualType'],capture_asset_id=aid,capture_request_id=a['request_id'],framing='完整原始应用窗口等比放入固定灰色媒体框；保留Logo、左侧导航、标题与空白。只在明确口播提示后连续运镜到局部，不用局部截图开场。')
 q['capture_request']['purpose']=a['semantic_support']

# 2.23–9.70 seconds: Agent → Providers → Routing, with whole-window continuity across scenes 2/3.
by_scene['scene_02']['evidenceSequence']=[{'fromFrame':0,**visual('native-agents-still')},{'fromFrame':66,**visual('article-providers')}]
by_scene['scene_03']['evidenceSequence']=[{'fromFrame':0,**visual('article-providers')},{'fromFrame':33,**visual('article-routing')},{'fromFrame':114,**visual('article-models-a'),'sourceHighlights':mark([1300,180,610,790])}]
for aid,sid in [('article-providers','scene_02'),('article-routing','scene_03'),('article-models-a','scene_03')]:assets[aid]['scene_ids'].append(sid)
by_scene['scene_04']['sourceHighlights']=mark([1300,180,610,790])
by_scene['scene_04']['sourceCamera']=cam([1240,135,760,940],33,78)
planned['scene_03']['content_description']='完整供应商页面接续开场，7秒切至完整路由页面，9.7秒切至完整Harness桌面并框出模型菜单；后续使用同一张截图推进。'
planned['scene_04']['content_description']='接续上一幕同一张完整Harness截图；先保留整体，再随“打开模型列表”连续运镜放大菜单，保持到“想用哪个就用哪个”。'

# WorkBuddy model menu: complete client first, then a deliberate continuous push-in.
by_scene['scene_10']['sourceHighlights']=mark([1045,795,690,748])
by_scene['scene_10']['sourceCamera']=cam([1020,760,755,870],30,78)

# Free-credit explanation: full official page, then the full WorkBuddy client before entering the reward card.
daily=visual('native-wb-daily');daily['sourceHighlights']=mark([20,1360,488,235]);daily['sourceCamera']=cam([0,1280,540,330],180,218)
daily['sourceRedactions']=[{'rect':[22,1615,320,88],'color':'#EEF0F2'}]
by_scene['scene_24']['evidenceSequence']=[{'fromFrame':0,**visual('public-qoder'),'sourceHighlights':assets['public-qoder'].get('highlights',[])},{'fromFrame':156,**daily}]
assets['native-wb-daily']['scene_ids'].append('scene_24')

# Repeated Harness menu proof also establishes the whole application first.
by_scene['scene_26']['sourceCamera']=cam([1260,600,1050,1030],30,75)
by_scene['scene_26']['sourceHighlights']=mark([1320,775,740,725])

# All three account dialogs are shown together with the real Magpie window and sidebar, including blurred identities.
by_scene['scene_28']['evidenceSequence']=[{'fromFrame':0,**visual('article-accounts-wb')},{'fromFrame':102,**visual('article-accounts-wbai')},{'fromFrame':186,**visual('article-accounts-codex')}]
assets['article-accounts-wbai']['scene_ids'].append('scene_28');assets['article-accounts-codex']['scene_ids'].append('scene_28')

for s in data['scenes']:
 if s['kind']=='effect':continue
 assert 'sourceRect' not in s
 for e in s.get('evidenceSequence',[]):assert 'sourceRect' not in e
 planned[s['id']]['full_window_first']=True
 planned[s['id']]['display_sequence']=s.get('evidenceSequence')
 planned[s['id']]['source_camera']=s.get('sourceCamera')
manifest.update(revision='v02',revision_reason='2026-10-28用户要求所有真实界面完整窗口展示，明确重点后才连续运镜；开场加入Agent、供应商、路由三个完整页面。')
plan['revision']='v02';plan['revision_reason']=manifest['revision_reason']
(out/'remotion_props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2))
(out/'visual_plan.lock.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(out/'capture_manifest.lock.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(p/'visual_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(p/'capture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
for name in ['字幕.srt','narration.lock.json']:shutil.copy2(base/name,out/name)
timeline=json.loads((base/'timeline.json').read_text())
for item in timeline:item['visual_type']=by_scene[item['id']]['visualType']
(out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
snapshot=out/'source-snapshot';shutil.copytree(p/'remotion/src',snapshot/'src',dirs_exist_ok=True)
for name in ['package.json','package-lock.json','remotion.config.ts','motion-style.lock.json']:shutil.copy2(p/'remotion'/name,snapshot/name)

# Review frames include the new opening, cross-scene identity and every camera's establishing/moving/landing states.
cursor=0;starts={}
for s in data['scenes']:starts[s['id']]=cursor;cursor+=s['durationFrames']
frames={'agent-full':100,'providers-full':160,'routing-full':250,'harness-full':320,'harness-join-before':334,'harness-join-after':335,'harness-moving':390,'harness-close':430,'wb-full':starts['scene_10']+12,'wb-moving':starts['scene_10']+54,'wb-close':starts['scene_10']+100,'credits-full':starts['scene_24']+160,'credits-moving':starts['scene_24']+199,'credits-close':starts['scene_24']+235}
(p/'work/revision-v02/review-frames.json').write_text(json.dumps(frames,indent=2))
assert cursor==5292
print('v02:',len(mapping),'complete-window scenes; 4 deliberate camera moves; same 5292-frame timeline.')
