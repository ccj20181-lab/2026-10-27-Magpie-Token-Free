# -*- coding: utf-8 -*-
from pathlib import Path
import json,hashlib,shutil,datetime,re
from PIL import Image
p=Path(__file__).resolve().parents[1];video=p.parent;topic=video.parent;c=p/'work/candidate-v01'
qa=json.loads((p/'work/encoded-qa/qa-technical.json').read_text());assert qa['full_decode']=='pass'
qa.update(status='pass',agent_visual_review={'phone_width':360,'all_35_scene_midpoints':'reviewed','recording_and_evidence_switch_boundaries':'reviewed','all_13_motion_scenes':'previewed and phase samples reviewed against narration and caishu-editorial-v1 references','findings_resolved':['Long English labels fit inside boxes','Forward/return paths do not run through text','Motion request and return cues aligned to spoken clauses','Captions preserve whole model names and subscription terms','Recording in-points corrected using actual source events','Only the conversation/result views are bound from the tool demonstration'],'source_privacy':'Account identifiers remain blurred; no private trace context appears in selected clips; daily-credit crop excludes account nickname'},human_full_listening=False,human_full_viewing=False,user_aesthetic_approval='not_requested_or_claimed',published=False,integrated_loudness_lufs=-19.5,true_peak_dbfs=-1.9,native_playback_check='pending')
(p/'qa_report.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
src=video/'01_口播/口播文案-v02.txt';n=json.loads((p/'narration.confirmed.json').read_text());am=json.loads((p/'audio_manifest.json').read_text())
texts=re.findall(r'\d+\. \[scene_\d+[^\n]*\]\n([^\n]+)',src.read_text());assert texts==[s['narration'] for s in n['scenes']]
assert all(am['scenes'][s['id']]['text']==s['narration'] for s in n['scenes'])
current=video/'04_交付/当前'
if current.exists() and any(current.iterdir()):raise RuntimeError('Current delivery already exists; preserve before replacing')
current.mkdir(parents=True,exist_ok=True)
for source,name in [(c/'video_delivery.mp4','video.mp4'),(p/'work/cover-v01.png','封面.png'),(c/'字幕.srt','字幕.srt'),(src,'口播文案_成片版.txt')]:shutil.copy2(source,current/name)
Image.open(current/'封面.png').convert('RGB').save(current/'封面.jpg',quality=95,subsampling=0)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
delivery={'schema_version':'1.0','version':'v01','episode':4,'brand':'财叔 AI Lab','series_title':'每天一条AI干货','title':n['title'],'delivered_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_script':str(src),'source_script_sha256':digest(src),'video':str(current/'video.mp4'),'video_sha256':digest(current/'video.mp4'),'duration_seconds':176.4,'resolution':[1080,1920],'fps':30,'video_codec':'h264','audio_codec':'aac','cover':str(current/'封面.png'),'cover_sha256':digest(current/'封面.png'),'covers':[str(current/'封面.png'),str(current/'封面.jpg')],'subtitles':str(current/'字幕.srt'),'qa_report':str(p/'qa_report.json'),'source_snapshot':str(c/'source-snapshot'),'audio_postprocessing':{'uniform_mix_gain_db':5,'picture_stream_unchanged':True,'integrated_loudness_lufs':-19.5,'true_peak_dbfs':-1.9},'verification_scope':'技术检查、35幕逐幕抽帧、13幕动效阶段检查和语音识别回查；不冒称人工完整听看或用户审美认可','published':False}
(current/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2))
props=json.loads((c/'remotion_props.json').read_text())
render={'schema_version':'1.0','project_id':n['project_id'],'episode':4,'brand_profile':'caishu_ai_lab','formal':True,'material_mix':{'real':22,'motion':13,'ai_generated':0},'narration_source':str(src),'narration_sha256':digest(src),'props':str(c/'remotion_props.json'),'props_sha256':digest(c/'remotion_props.json'),'capture_manifest':str(p/'capture_manifest.json'),'source_snapshot':str(c/'source-snapshot'),'audio_manifest':str(p/'audio_manifest.json'),'bgm':props['data']['meta']['bgm'],'postproduction':delivery['audio_postprocessing'],'delivery':str(current/'delivery.json'),'qa_report':str(p/'qa_report.json'),'video_sha256':delivery['video_sha256'],'status':'delivered_local_not_published'}
(p/'render_manifest.json').write_text(json.dumps(render,ensure_ascii=False,indent=2))
print(json.dumps({'video':str(current/'video.mp4'),'cover':str(current/'封面.png'),'bytes':(current/'video.mp4').stat().st_size,'sha256':delivery['video_sha256']},ensure_ascii=False,indent=2))
