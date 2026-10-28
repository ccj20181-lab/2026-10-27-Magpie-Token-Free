# -*- coding: utf-8 -*-
from pathlib import Path
import json,time,os
os.environ['HF_HUB_OFFLINE']='1'
import mlx_whisper
p=Path(__file__).resolve().parents[1]
manifest=json.loads((p/'audio_manifest.json').read_text())
models=Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots'
model=next(x for x in models.iterdir() if (x/'config.json').exists())
out=p/'work/tts-asr-review.json'
rows=json.loads(out.read_text()) if out.exists() else []
done={x['id'] for x in rows}
for sid,a in manifest['scenes'].items():
 if sid in done:continue
 r=mlx_whisper.transcribe(a['path'],path_or_hf_repo=str(model),language='zh',word_timestamps=True,verbose=False,initial_prompt='简体中文。Magpie，WorkBuddy，Qoder，DeepSeek Harness，Codex，Step，GPT，Grok，Gemini，CC Switch，DeepSeek V4.1 Flash，Token，web，desktop，Profile。',condition_on_previous_text=False)
 rows.append({'id':sid,'source':a['text'],'asr':r['text'],'segments':r['segments']})
 out.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print(sid,r['text'],flush=True)
print('ASR_COMPLETE',len(rows),flush=True)
