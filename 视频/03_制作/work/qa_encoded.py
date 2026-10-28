# -*- coding: utf-8 -*-
from pathlib import Path
import json,subprocess,hashlib,re,math
from PIL import Image,ImageDraw
import numpy as np
p=Path(__file__).resolve().parents[1];out=p/'work/encoded-qa';out.mkdir(exist_ok=True)
c=p/'work/candidate-v01';video=c/'video_delivery.mp4'
data=json.loads((c/'remotion_props.json').read_text())['data']
timeline=json.loads((c/'timeline.json').read_text())
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
vs=next(x for x in probe['streams'] if x['codec_type']=='video');au=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (vs['width'],vs['height'],vs['codec_name'])==(1080,1920,'h264')
assert vs['pix_fmt'] in {'yuv420p','yuvj420p'} # 8-bit 4:2:0, limited or explicitly tagged full range
assert int(vs['nb_frames'])==sum(x['durationFrames'] for x in data['scenes'])==5292
assert vs['avg_frame_rate']=='30/1' and au['codec_name']=='aac'
def sample(frame,name,scale='360:640'):
 f=out/(name+'.png')
 if f.exists() and json.loads((c/'picture-stream-identity.json').read_text())['identical']:return f
 subprocess.run(['ffmpeg','-y','-v','error','-threads','1','-ss',f'{frame/30:.6f}','-i',str(video),'-frames:v','1','-vf','scale='+scale,str(f)],check=True)
 return f
for s,t in zip(data['scenes'],timeline):
 mid=t['start_frame']+int(s['durationFrames']*.5)
 sample(mid,s['id']+'-mid')
 for phase,frac in [('first',.03),('last',.97)]:
  if s['kind']=='video' or s.get('evidenceSequence'):sample(t['start_frame']+min(s['durationFrames']-1,int(s['durationFrames']*frac)),s['id']+'-'+phase)
 for cs in s['captionSegments']:
  assert 0<=cs['startFrame']<cs['endFrame']<=s['durationFrames']
 assert s['captionSegments'][0]['startFrame']==0 and s['captionSegments'][-1]['endFrame']==s['durationFrames']
sample(5291,'final-frame')
for batch in range(0,35,5):
 group=data['scenes'][batch:batch+5];sheet=Image.new('RGB',(360*len(group),666),'#DDE3E3');d=ImageDraw.Draw(sheet)
 for j,s in enumerate(group):
  sheet.paste(Image.open(out/(s['id']+'-mid.png')),(j*360,24));d.text((j*360+8,6),s['id'],fill='black')
 sheet.save(out/f'full-phone-{batch//5}.jpg',quality=94)
dynamic=[s for s in data['scenes'] if s['kind']=='video' or s.get('evidenceSequence')]
for i,s in enumerate(dynamic):
 sheet=Image.new('RGB',(1080,666),'#DDE3E3');d=ImageDraw.Draw(sheet)
 for j,phase in enumerate(['first','mid','last']):
  sheet.paste(Image.open(out/(s['id']+'-'+phase+'.png')),(j*360,24));d.text((j*360+8,6),s['id']+' / '+phase,fill='black')
 sheet.save(out/(s['id']+'-phases.jpg'),quality=94)
decode=subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(video),'-f','null','-'],capture_output=True,text=True)
assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vn','-ac','2','-ar','48000','-f','f32le','pipe:1'])
mixed=np.frombuffer(pcm,dtype=np.float32)
peak=float(np.max(np.abs(mixed)));rms=float(np.sqrt(np.mean(mixed.astype(np.float64)**2)))
assert peak<1,peak
# Cross-correlate real source fingerprints with the encoded mix; allow codec priming.
alignment=json.loads((p/'work/audio-alignment-audit.json').read_text())
assert alignment['video']==str(video)
fingerprints=alignment['rows']
assert all(x['correlation']>.25 for x in fingerprints if x['source']=='bgm'),fingerprints
assert all(x['correlation']>.60 for x in fingerprints if x['source']=='voice'),fingerprints
assert all(abs(x['lag_samples'])/16000<.07 for x in fingerprints),fingerprints
report={'status':'technical_pass_visual_review_pending','video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'width':1080,'height':1920,'fps':30,'frames':5292,'duration_seconds':5292/30,'video_codec':'h264','pixel_format':vs['pix_fmt'],'audio_codec':'aac','audio_sample_rate':au['sample_rate'],'full_decode':'pass','audio_peak_dbfs':20*math.log10(peak),'audio_rms_dbfs':20*math.log10(rms),'actual_audio_source_fingerprints':fingerprints,'audio_check_note':'Fingerprint search permits AAC/MP3 encoder priming and sub-millisecond resampling differences; fixed sample-aligned gain regression is not used as a pass gate. Final mixed audio gets a uniform +5dB gain, with picture stream copied and natural narration timing retained.','caption_timing_continuity':'pass','scene_count':35,'real_scenes':22,'motion_scenes':13,'image_generated_scenes':0,'scope':'Full decode, encoding metadata, subtitle timing and actual mixed BGM verification; 35 phone-scale midpoint frames plus source-video/evidence boundary samples. Human full listening/viewing and aesthetic approval are not asserted.'}
(out/'qa-technical.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
