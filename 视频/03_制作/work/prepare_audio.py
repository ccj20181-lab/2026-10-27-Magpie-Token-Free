from pathlib import Path
import sys,json,re,hashlib,time
root=Path('/Users/henry/Desktop/财叔 AI Lab')
skill=root/'.agents/skills/ai-coach-daily-demo'
sys.path.insert(0,str(skill/'scripts'))
from render_ai_coach_demo import load_env_file,synthesize_audio,tts_settings
project=Path(__file__).resolve().parents[1]
source=project.parent/'01_口播/narration-v02.json'
n=json.loads(source.read_text())
txt=(source.parent/'口播文案-v02.txt').read_text()
spoken=re.findall(r'\d+\. \[scene_\d+[^\n]*\]\n([^\n]+)',txt)
assert spoken==[s['narration'] for s in n['scenes']], 'source text mismatch'
n['status']='confirmed'
n['confirmation']={'basis':'用户明确要求根据口播文案-v02生成完整视频','date':'2026-10-27','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(project/'narration.confirmed.json').write_text(json.dumps(n,ensure_ascii=False,indent=2))
load_env_file()
print('TTS route:',tts_settings(1.13,'minimax'),flush=True)
audio=synthesize_audio(project,n,speed=1.13,force=False,preview=False)
out={'schema_version':'1.0','scenes':{s['id']:{'text':s['narration'],'path':str(audio[s['id']].path),'provider':'minimax','duration_ms':audio[s['id']].duration_ms,'model':audio[s['id']].model,'voice':audio[s['id']].voice,'speed':audio[s['id']].speed} for s in n['scenes']}}
(project/'audio_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('COMPLETE',len(audio),'scenes',round(sum(a.duration_ms for a in audio.values())/1000,2),'seconds',flush=True)
