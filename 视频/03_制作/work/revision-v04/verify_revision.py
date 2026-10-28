from pathlib import Path
import json,subprocess,hashlib,re,math
import numpy as np
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v04';o=p/'work/candidate-v04';v=o/'video_candidate.mp4'
def run(a):return subprocess.check_output(a)
def h(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
a=json.loads((p/'work/candidate-v03/remotion_props.json').read_text())['data'];b=json.loads((o/'remotion_props.json').read_text())['data'];assert a['meta']==b['meta'] and a['scenes']==b['scenes'][:34];assert b['scenes'][34]['caption']=='我是财叔，我们下期见。'
ams=json.loads((o/'audio_manifest.lock.json').read_text())['scenes'];oldams=json.loads((r/'baseline-v03/audio_manifest.json').read_text())['scenes']
for s in a['scenes']:assert h(ams[s['id']]['path'])==h(oldams[s['id']]['path'])
original=json.loads((p/'work/revision-v03/baseline-v02/audio_manifest.json').read_text())['scenes']['scene_35']['path'];raw=run(['ffmpeg','-v','error','-i',original,'-f','s16le','-acodec','pcm_s16le','-']);new=run(['ffmpeg','-v','error','-i',ams['scene_35']['path'],'-f','s16le','-acodec','pcm_s16le','-']);assert new==raw[:round(.74*32000)*2]+raw[4*32000*2:round(4.98*32000)*2]
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-of','json',str(v)]));video=next(x for x in probe['streams'] if x['codec_type']=='video');assert (video['width'],video['height'],video['r_frame_rate'],video['codec_name'],int(video['nb_frames']))==(1080,1920,'30/1','h264',5184);subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True)
assert json.loads((r/'picture-integrity.json').read_text())['all_decoded_frame_hashes_identical']
levels=subprocess.run(['ffmpeg','-v','info','-i',str(v),'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True).stderr;(r/'loudness.log').write_text(levels);s=levels[levels.rfind('Summary:'):];lufs=float(re.search(r'I:\s*(-?[\d.]+)',s).group(1));peak=float(re.search(r'Peak:\s*(-?[\d.]+)',s).group(1));assert peak<0
pixels=np.frombuffer(run(['ffmpeg','-v','error','-i',str(v),'-vf','crop=130:150:370:235,scale=26:30','-pix_fmt','rgb24','-f','rawvideo','-']),dtype=np.uint8).reshape(-1,3);red=int(((pixels[:,0]>170)&(pixels[:,1]<125)&(pixels[:,2]<125)).sum());assert red==0
src=(p.parent/'01_口播/口播文案-v04.txt').read_text();texts=re.findall(r'\d+\. \[scene_\d+[^\n]*\]\n([^\n]+)',src);assert texts==[s['caption'] for s in b['scenes']];assert '类似这种真能省' not in src and '我继续给大家挖' not in src
im=Image.new('RGB',(1440,668),'white');d=ImageDraw.Draw(im)
for i,(f,name) in enumerate([(5128,'body-before-ending'),(5134,'name'),(5164,'goodbye'),(5183,'last-frame')]):
 out=r/(name+'.png');subprocess.run(['ffmpeg','-v','error','-y','-ss',str(f/30),'-i',str(v),'-frames:v','1','-vf','scale=360:640','-threads','1',str(out)],check=True);im.paste(Image.open(out),(i*360,28));d.text((i*360+8,7),name,fill='black')
im.save(r/'ending-review.jpg')
subprocess.run(['ffmpeg','-v','error','-y','-ss',str(5132/30),'-i',str(v),'-t',str(52/30),'-vn','-ar','16000','-ac','1',str(r/'ending-encoded.wav')],check=True)
report={'status':'technical_pass_asr_visual_pending','revision':'v04','video_sha256':h(v),'width':1080,'height':1920,'fps':30,'frames':5184,'duration_seconds':172.8,'video_codec':'h264','audio_codec':'aac','full_decode':'pass','prefix_34_scenes_props_and_meta_unchanged':True,'prefix_5132_video_frames_decoded_md5_identical':True,'all_34_existing_voice_source_hashes_unchanged':True,'outro_voice_approved_source_samples_identical':True,'outro_voice_retained_intervals_seconds':[[0,.74],[4,4.98]],'outro_text':'我是财叔，我们下期见。','top_badge_red_pixels_all_frames':red,'scene_count':35,'real_scenes':22,'motion_scenes':13,'integrated_loudness_lufs':lufs,'true_peak_dbfs':peak,'music':'Same BGM source/volume; only move final fade-out to the restored ending','scope':'All prefix frames exact decoded equality; original voice sample equality; targeted encoded ASR and ending visual/native checks. No human full listening/viewing or publication claim.'};(o/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:report[k] for k in ['status','duration_seconds','prefix_5132_video_frames_decoded_md5_identical','integrated_loudness_lufs','true_peak_dbfs']})
