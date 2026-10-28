from pathlib import Path
import json,copy,math,hashlib,shutil,re
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v03';o=p/'work/candidate-v03';o.mkdir(exist_ok=True);base=p/'work/candidate-v02';props=json.loads((base/'remotion_props.json').read_text());data=props['data'];data['meta']['showEpisodeMarker']=False
old=copy.deepcopy(data['scenes']);data['scenes']=[s for s in data['scenes'] if s['id']!='scene_35'];n=json.loads((r/'narration-v03.confirmed.json').read_text());nmap={s['id']:s for s in n['scenes']};audio=json.loads((r/'baseline-v02/audio_manifest.json').read_text());audio['revision']='v03';audio['scenes'].pop('scene_35');a=json.loads((r/'scene_28_audio.json').read_text());audio['scenes']['scene_28']=a
s=next(s for s in data['scenes'] if s['id']=='scene_28');s['caption']=nmap['scene_28']['narration'];s['durationFrames']=math.ceil(a['duration_ms']*.03);dest=p/'remotion/public/magpie-04-revision-v03';dest.mkdir(exist_ok=True);shutil.copy2(a['path'],dest/'scene_28.mp3');s['audioPath']='magpie-04-revision-v03/scene_28.mp3'
# New audio ASR provides the exact phrase starts; preserve all other captions.
s['captionSegments']=[{'text':'最最关键的是','startFrame':0,'endFrame':30},{'text':'Magpie 还支持你同时接多个账号','startFrame':30,'endFrame':108},{'text':'我现在就同时挂了多个','startFrame':108,'endFrame':150},{'text':'WorkBuddy、WorkBuddy 海外版','startFrame':150,'endFrame':207},{'text':'Codex 账号','startFrame':207,'endFrame':s['durationFrames']}]
# Retain all three complete Magpie account windows; align the overseas/Codex
# changes to the newly spoken brand names rather than shortening a source crop.
s['evidenceSequence'][1]['fromFrame']=177;s['evidenceSequence'][2]['fromFrame']=207
for previous,current in zip(old,data['scenes']):
 if current['id']!='scene_28':assert current==previous,current['id']
 assert current['caption']==nmap[current['id']]['narration']
 if current['id']!='scene_28':
  ap=p/'remotion/public'/current['audioPath'];orig=Path(audio['scenes'][current['id']]['path']);assert hashlib.sha256(ap.read_bytes()).hexdigest()==hashlib.sha256(orig.read_bytes()).hexdigest()
(o/'remotion_props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2));(o/'audio_manifest.lock.json').write_text(json.dumps(audio,ensure_ascii=False,indent=2));(o/'narration.lock.json').write_text(json.dumps(n,ensure_ascii=False,indent=2))
plan=json.loads((r/'baseline-v02/visual_plan.json').read_text());plan['revision']='v03';plan['narration_path']=str(p.parent/'01_口播/narration-v03.json');plan['narration_sha256']=hashlib.sha256(Path(plan['narration_path']).read_bytes()).hexdigest();plan['show_episode_marker']=False;plan['scenes']=[s for s in plan['scenes'] if s['id']!='scene_35'];plan['scene_count_exception']=n['scene_count_exception'];next(s for s in plan['scenes'] if s['id']=='scene_28')['narration']=a['text'];(o/'visual_plan.lock.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(o/'capture_manifest.lock.json').write_bytes((r/'baseline-v02/capture_manifest.json').read_bytes())
cursor=0;timeline=[];subs=[];idx=0
def stamp(f):
 ms=round(f*1000/30);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{sec:02},{ms:03}'
for scene in data['scenes']:
 timeline.append({'id':scene['id'],'start_frame':cursor,'duration_frames':scene['durationFrames'],'visual_type':scene['visualType']})
 for c in scene['captionSegments']:
  idx+=1;subs.append(f'{idx}\n{stamp(cursor+c["startFrame"])} --> {stamp(cursor+c["endFrame"])}\n{c["text"]}\n')
 cursor+=scene['durationFrames']
(o/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2));(o/'字幕.srt').write_text('\n'.join(subs));shutil.copytree(p/'remotion/src',o/'source-snapshot/src',dirs_exist_ok=True)
for name in ['package.json','package-lock.json','remotion.config.ts','motion-style.lock.json']:shutil.copy2(p/'remotion'/name,o/'source-snapshot'/name)
(r/'build_check.json').write_text(json.dumps({'scene_count':len(data['scenes']),'frames':cursor,'duration':cursor/30,'unchanged_voice_scenes':33,'changed_voice':['scene_28'],'removed':['scene_35'],'red_episode_marker':False},indent=2));print('v03',len(data['scenes']),cursor,'frames',cursor/30,'seconds; 33 original voice clips reused')
