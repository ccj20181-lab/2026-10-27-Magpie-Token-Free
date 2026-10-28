from pathlib import Path
import json,hashlib,shutil,datetime
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v02';o=p/'work/candidate-v02';delivery=p.parent/'04_交付';current=delivery/'当前'
def h(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2))
qa=json.loads((o/'qa_report.json').read_text());assert qa['status']=='pass';assert qa['video_sha256']==h(o/'video_candidate.mp4')
baseline=json.loads((r/'baseline-v01/delivery-hashes.json').read_text())
for n,sha in baseline.items():assert h(current/n)==sha,(n,'prior delivery changed')
oldmanifest=json.loads((current/'delivery.json').read_text());assert oldmanifest['version']=='v01'
time=datetime.datetime.now().astimezone();history=delivery/'历史'/('v01-'+time.strftime('%Y%m%d-%H%M%S'));assert not history.exists()
prepared=r/'prepared-delivery-v02';prepared.mkdir(exist_ok=False)
shutil.copy2(o/'video_candidate.mp4',prepared/'video.mp4')
for n in ['封面.png','封面.jpg','字幕.srt','口播文案_成片版.txt']:shutil.copy2(current/n,prepared/n);assert h(prepared/n)==baseline[n]
new=dict(oldmanifest);new.update(version='v02',delivered_at=time.isoformat(),video_sha256=qa['video_sha256'],previous_version=str(history),source_snapshot=str(o/'source-snapshot'),revision_reason='全片真实界面先完整窗口，保留Logo/侧栏/空白；开场Magpie Agent/供应商/路由；Harness、WorkBuddy模型及每日100积分在同一源图上连续运镜。',audio_postprocessing={'revision_audio':'v01 mixed AAC copied byte-for-byte','aac_sha256':qa['audio_aac_sha256'],'prior_uniform_mix_gain_db':5,'integrated_loudness_lufs':-19.5,'true_peak_dbfs':-1.9},native_playback_check='candidate_pass_formal_path_pending',verification_scope=qa['scope'])
write(prepared/'delivery.json',new)
current.rename(history);prepared.rename(current)
evidence=history/'制作记录';evidence.mkdir()
for file in (r/'baseline-v01').iterdir():
 if file.is_file():shutil.copy2(file,evidence/file.name)
if (p/'archive_receipt.json').exists():shutil.copy2(p/'archive_receipt.json',evidence/'archive_receipt.json')
assert h(history/'video.mp4')==baseline['video.mp4'];assert h(current/'video.mp4')==qa['video_sha256']
for n in ['封面.png','封面.jpg','字幕.srt','口播文案_成片版.txt']:assert h(current/n)==h(history/n)
qa['previous_formal_video']=str(history/'video.mp4');qa['delivered_video']=str(current/'video.mp4');write(o/'qa_report.json',qa);write(p/'qa_report.json',qa)
rm=json.loads((r/'baseline-v01/render_manifest.json').read_text());rm.update(revision='v02',props=str(o/'remotion_props.json'),props_sha256=h(o/'remotion_props.json'),source_snapshot=str(o/'source-snapshot'),video_sha256=qa['video_sha256'],previous_delivery=str(history),postproduction={'visual_render':'Remotion H.264 CRF17, muted','mux':'original mixed AAC copied without reencoding','audio_source':str(history/'video.mp4'),'audio_aac_sha256':qa['audio_aac_sha256'],'prior_mix_gain_db':5},status='delivered_local_not_published');write(p/'render_manifest.json',rm)
write(r/'promotion_receipt.json',{'current':str(current),'history':str(history),'video_sha256':qa['video_sha256'],'unchanged_companion_files':['封面.png','封面.jpg','字幕.srt','口播文案_成片版.txt']})
print(json.dumps({'current':str(current),'history':str(history),'video_sha256':qa['video_sha256']},ensure_ascii=False))
