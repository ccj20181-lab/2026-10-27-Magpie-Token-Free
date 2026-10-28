from pathlib import Path
import json,hashlib,shutil,datetime,re
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v03';o=p/'work/candidate-v03';root=p.parents[4];current=p.parent/'04_交付/当前';delivery=current.parent

def h(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def read(f):return json.loads(Path(f).read_text())
def write(f,v):Path(f).write_text(json.dumps(v,ensure_ascii=False,indent=2))
qa=read(o/'qa_report.json');asr=read(r/'encoded-asr.json');assert '海外版' in asr[0]['asr'] and '就算搞定' in asr[1]['asr'];assert '省Token' not in asr[1]['asr'].replace(' ','')
qa.update(status='pass',encoded_targeted_asr=asr,agent_visual_review={'changed_caption_at_2m20':'WorkBuddy、WorkBuddy海外版; readable at360px','top_marker':'absent in all5132 encoded frames and reviewed samples','ending':'last frame and encoded ASR end at就算搞定; entire scene35 absent','previous_whole_window_camera_work':'preserved; 33 unchanged media ROI comparisons passed','human_full_listening_viewing':False},native_playback={'app':'QuickTime Player','candidate_path':str(o/'video_candidate.mp4'),'correct_path_opened':True,'duration_display':'02:51','playback_progress_seconds':[133.28,170.72],'ended_paused_at_seconds':0,'formal_path':'pending'},checked_at=datetime.datetime.now().astimezone().isoformat())
write(o/'qa_report.json',qa);assert h(o/'video_candidate.mp4')==qa['video_sha256']
baseline=read(r/'baseline-v02/delivery-hashes.json')
for name,sha in baseline.items():assert h(current/name)==sha,name
old=read(current/'delivery.json');assert old['version']=='v02';time=datetime.datetime.now().astimezone();history=delivery/'历史'/('v02-'+time.strftime('%Y%m%d-%H%M%S'));assert not history.exists()
prep=r/'prepared-delivery-v03';prep.mkdir(exist_ok=False)
shutil.copy2(o/'video_candidate.mp4',prep/'video.mp4');shutil.copy2(o/'字幕.srt',prep/'字幕.srt');script=p.parent/'01_口播/口播文案-v03.txt';shutil.copy2(script,prep/'口播文案_成片版.txt')
for name in ['封面.png','封面.jpg']:shutil.copy2(current/name,prep/name);assert h(prep/name)==baseline[name]
new=dict(old);new.update(version='v03',delivered_at=time.isoformat(),source_script=str(script),source_script_sha256=h(script),video_sha256=qa['video_sha256'],duration_seconds=qa['duration_seconds'],frames=5132,scene_count=34,episode_marker_visible=False,source_snapshot=str(o/'source-snapshot'),previous_version=str(history),revision_reason='scene28口播/配音/字幕WorkBuddy AI改WorkBuddy海外版；删除scene35整句收尾及对应画面时长；去掉顶部红色期数圆标。',audio_postprocessing={'uniform_mix_gain_db':5,'integrated_loudness_lufs':qa['integrated_loudness_lufs'],'true_peak_dbfs':qa['true_peak_dbfs'],'changed_voice_scenes':['scene_28'],'reused_original_voice_clip_count':33,'model':'speech-2.8-turbo','voice':'financevideo_v1_20260215','speed':1.13},verification_scope=qa['scope'],native_playback_check='candidate_pass_formal_path_pending')
write(prep/'delivery.json',new);current.rename(history);prep.rename(current);evidence=history/'制作记录';shutil.copytree(r/'baseline-v02',evidence)
assert h(history/'video.mp4')==baseline['video.mp4'];assert h(current/'video.mp4')==qa['video_sha256'];qa['previous_formal_video']=str(history/'video.mp4');qa['delivered_video']=str(current/'video.mp4');write(o/'qa_report.json',qa);write(p/'qa_report.json',qa)
plan=read(o/'visual_plan.lock.json');s=next(s for s in plan['scenes'] if s['id']=='scene_28');s['display_sequence']=read(o/'remotion_props.json')['data']['scenes'][27]['evidenceSequence']
if s.get('evidence_sequence'):
 for e,f in zip(s['evidence_sequence'],[0,177,207]):e['from_frame']=f
write(o/'visual_plan.lock.json',plan);write(p/'visual_plan.json',plan);shutil.copy2(o/'audio_manifest.lock.json',p/'audio_manifest.json');shutil.copy2(o/'narration.lock.json',p/'narration.confirmed.json')
rm=read(r/'baseline-v02/render_manifest.json');rm.update(revision='v03',material_mix={'real':22,'motion':12,'ai_generated':0},narration_source=str(script),narration_sha256=h(script),props=str(o/'remotion_props.json'),props_sha256=h(o/'remotion_props.json'),source_snapshot=str(o/'source-snapshot'),video_sha256=qa['video_sha256'],previous_delivery=str(history),postproduction=new['audio_postprocessing'],duration_seconds=qa['duration_seconds'],frames=5132,show_episode_marker=False,status='delivered_local_not_published');write(p/'render_manifest.json',rm)
write(p/'audio_qa.json',{'status':'pass','source_script':str(script),'provider':'minimax','model':'speech-2.8-turbo','voice':'financevideo_v1_20260215','speed':1.13,'scenes':34,'reused_original_voice_clips_hash_verified':33,'changed_voice_scene':'scene_28','targeted_asr_source':str(r/'scene_28_asr.json'),'encoded_asr':asr,'integrated_loudness_lufs':qa['integrated_loudness_lufs'],'true_peak_dbfs':qa['true_peak_dbfs'],'human_full_listening':False})
write(r/'promotion_receipt.json',{'current':str(current),'history':str(history),'video_sha256':qa['video_sha256'],'duration_seconds':qa['duration_seconds']});print(json.dumps({'version':'v03','history':str(history),'video_sha256':qa['video_sha256'],'duration_seconds':qa['duration_seconds']},ensure_ascii=False))
