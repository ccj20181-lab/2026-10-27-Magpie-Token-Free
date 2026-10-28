# -*- coding: utf-8 -*-
from faster_whisper import WhisperModel
from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
cache=Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots'
model=WhisperModel(str(next(x for x in cache.iterdir() if (x/'model.bin').exists())),device='cpu',compute_type='int8',cpu_threads=2)
a=json.loads((p/'audio_manifest.json').read_text());rows=[]
for sid in ['scene_03','scene_24','scene_28','scene_31','scene_33']:
 segments,info=model.transcribe(a['scenes'][sid]['path'],language='zh',initial_prompt='Magpie，WorkBuddy，Qoder，DeepSeek Harness，Codex，Token。',beam_size=5)
 text=''.join(s.text for s in segments)
 rows.append({'id':sid,'asr':text});print(sid,text,flush=True)
 (p/'work/asr-crosscheck.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
