# -*- coding: utf-8 -*-
from pathlib import Path
import json,subprocess,math
import numpy as np
from scipy.signal import correlate,correlation_lags
p=Path(__file__).resolve().parents[1];c=p/'work/candidate-v01'
d=json.loads((c/'remotion_props.json').read_text())['data'];am=json.loads((p/'audio_manifest.json').read_text())
def dec(path):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1']),dtype=np.float32)
video=c/'video_delivery.mp4' if (c/'video_delivery.mp4').exists() else c/'video_candidate.mp4'
mixed=dec(video);voice=[]
for s in d['scenes']:
 x=dec(am['scenes'][s['id']]['path']);n=round(s['durationFrames']/30*16000);voice.append(np.pad(x[:n],(0,max(0,n-len(x)))))
voice=np.concatenate(voice)
bgm=dec(d['meta']['bgm']['sourcePath']);n=round(round(d['meta']['bgm']['durationSeconds']*30)/30*16000);bgm=np.pad(bgm[:n],(0,max(0,n-len(bgm))));bgm=np.tile(bgm,math.ceil(len(voice)/len(bgm)))[:len(voice)]
rows=[]
for start,end in [(0,2),(5,15),(65,75),(151,161)]:
 lo=int(start*16000);hi=int(end*16000);x=mixed[lo:hi];v=voice[lo:hi];b=bgm[lo:hi]
 for label,y in [('voice',v),('bgm',b)]:
  z=correlate(x,y,mode='full',method='fft');lags=correlation_lags(len(x),len(y),mode='full');valid=(lags>-16000)&(lags<16000);idx=np.argmax(np.abs(z[valid]));lag=int(lags[valid][idx]);val=float(z[valid][idx]/(np.linalg.norm(x)*np.linalg.norm(y)+1e-20));rows.append({'range':[start,end],'source':label,'lag_samples':lag,'correlation':val})
print(json.dumps(rows,indent=2));(p/'work/audio-alignment-audit.json').write_text(json.dumps({'video':str(video),'rows':rows},indent=2))
np.savez(p/'work/audio-audit-pcm.npz',mixed=mixed,voice=voice,bgm=bgm)
