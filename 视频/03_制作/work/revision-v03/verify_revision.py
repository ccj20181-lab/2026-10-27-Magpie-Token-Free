from pathlib import Path
import json,hashlib,re,subprocess,math
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageStat
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v03';o=p/'work/candidate-v03';v=o/'video_candidate.mp4';oldvideo=p.parent/'04_交付/当前/video.mp4';old=json.loads((p/'work/candidate-v02/remotion_props.json').read_text())['data'];new=json.loads((o/'remotion_props.json').read_text())['data']
def h(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args)
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(v)]));video=next(x for x in probe['streams'] if x['codec_type']=='video');audio=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (video['width'],video['height'],video['codec_name'],video['r_frame_rate'],int(video['nb_frames']))==(1080,1920,'h264','30/1',5132);assert audio['codec_name']=='aac';subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True)
levels=subprocess.run(['ffmpeg','-v','info','-i',str(v),'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True).stderr;(r/'loudness.log').write_text(levels);summary=levels[levels.rfind('Summary:'):];lufs=float(re.search(r'I:\s*(-?[\d.]+)',summary).group(1));peak=float(re.search(r'Peak:\s*(-?[\d.]+)',summary).group(1));assert peak<0,(peak,'audio clipping')
# Inspect every encoded frame in the old badge area (outside the yellow title).
def badge_pixels(f,one=False):
 args=['ffmpeg','-v','error','-i',str(f),'-vf','crop=130:150:370:235,scale=26:30']
 if one:args+=['-frames:v','1']
 a=np.frombuffer(run(args+['-pix_fmt','rgb24','-f','rawvideo','-']),dtype=np.uint8).reshape(-1,3);return int(((a[:,0]>170)&(a[:,1]<125)&(a[:,2]<125)).sum())
oldred=badge_pixels(oldvideo,True);newred=badge_pixels(v);assert oldred>10 and newred==0,(oldred,newred)
assert len(new['scenes'])==34 and all(s['id']!='scene_35' for s in new['scenes']);assert new['meta']['showEpisodeMarker'] is False
script=(p.parent/'01_口播/口播文案-v03.txt').read_text();spoken=re.findall(r'\d+\. \[scene_\d+[^\n]*\]\n([^\n]+)',script);assert spoken==[s['caption'] for s in new['scenes']];assert '类似这种真能省' not in script and 'WorkBuddy AI' not in script
sourceaudio=json.loads((o/'audio_manifest.lock.json').read_text())['scenes'];baseaudio=json.loads((r/'baseline-v02/audio_manifest.json').read_text())['scenes']
for s in new['scenes']:
 if s['id']=='scene_28':continue
 assert h(sourceaudio[s['id']]['path'])==h(baseaudio[s['id']]['path'])
 assert s==old['scenes'][int(s['id'][-2:])-1]
assert new['meta']['bgm']==old['meta']['bgm']
frames=r/'frames';frames.mkdir(exist_ok=True);named={};oldstarts={};newstarts={};cursor=0
for s in old['scenes']:oldstarts[s['id']]=cursor;cursor+=s['durationFrames']
cursor=0
for s in new['scenes']:newstarts[s['id']]=cursor;named[s['id']+'-mid']=cursor+s['durationFrames']//2;cursor+=s['durationFrames']
named.update({'overseas-caption':newstarts['scene_28']+190,'codex-caption':newstarts['scene_28']+219,'end-last':cursor-1,'opening-full':100,'harness-zoom':430,'wb-zoom':1311,'credits-zoom':3431})
def extract(src,f,dest):subprocess.run(['ffmpeg','-v','error','-y','-ss',str(f/30),'-i',str(src),'-frames:v','1','-vf','scale=360:640','-threads','1',str(dest)],check=True)
for name,f in named.items():extract(v,f,frames/(name+'.jpg'))
comparisons=[]
for s in new['scenes']:
 if s['id']=='scene_28':continue
 name=s['id'];dest=frames/(name+'-old.jpg');extract(oldvideo,oldstarts[name]+s['durationFrames']//2,dest)
 a=Image.open(dest).crop((9,170,351,530));b=Image.open(frames/(name+'-mid.jpg')).crop((9,170,351,530));error=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3;assert error<2,(name,error);comparisons.append({'scene':name,'media_roi_mean_pixel_error':error})
def sheet(items,dest,cols=5):
 im=Image.new('RGB',(cols*360,math.ceil(len(items)/cols)*668),'white');d=ImageDraw.Draw(im)
 for i,name in enumerate(items):
  x=i%cols*360;y=i//cols*668;im.paste(Image.open(frames/(name+'.jpg')),(x,y+28));d.text((x+8,y+7),name,fill='black')
 im.save(r/dest)
sheet([s['id']+'-mid' for s in new['scenes']],'all-scenes.jpg',6);sheet(['opening-full','harness-zoom','wb-zoom','credits-zoom','overseas-caption','codex-caption','end-last'],'changes.jpg',4)
for label,start,duration in [('scene_28',newstarts['scene_28']/30,new['scenes'][27]['durationFrames']/30),('ending',cursor/30-9,9)]:
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(v),'-t',str(duration),'-vn','-ar','16000','-ac','1',str(r/(label+'-encoded.wav'))],check=True)
report={'status':'technical_pass_final_asr_visual_pending','revision':'v03','video_sha256':h(v),'width':1080,'height':1920,'frames':5132,'fps':30,'duration_seconds':5132/30,'video_codec':video['codec_name'],'audio_codec':audio['codec_name'],'full_decode':'pass','integrated_loudness_lufs':lufs,'true_peak_dbfs':peak,'top_badge_red_pixels_all_frames':newred,'old_badge_detection_control':oldred,'new_script_matches_all_captions':True,'removed_scene':'scene_35','changed_voice_scene':'scene_28','unchanged_voice_scenes_hash_verified':33,'real_scenes':22,'motion_scenes':12,'visual_comparisons_excluding_changed_header_and_account_sequence':comparisons,'phone_review_frames':len(named),'bgm_same_source_and_configuration':True,'scope':'Targeted source/encoded ASR, full decode, all-frame badge check, per-scene media comparison, phone-scale visual samples and native playback; no human full listening/viewing, aesthetic approval or publication claim.'};(o/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:report[k] for k in ['status','frames','duration_seconds','integrated_loudness_lufs','true_peak_dbfs','top_badge_red_pixels_all_frames','phone_review_frames']})
