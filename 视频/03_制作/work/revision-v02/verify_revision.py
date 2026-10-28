from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageStat
p=Path(__file__).resolve().parents[2];o=p/'work/candidate-v02';r=p/'work/revision-v02';v=o/'video_candidate.mp4';old=p.parent/'04_交付/当前/video.mp4'
def hashfile(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args)
def audiohash(f,pcm=False):return hashlib.sha256(run(['ffmpeg','-v','error','-i',str(f),'-map','0:a:0','-c:a','pcm_s16le' if pcm else 'copy','-f','s16le' if pcm else 'adts','-'])).hexdigest()
subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True)
info=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(v)]));video=next(x for x in info['streams'] if x['codec_type']=='video');audio=next(x for x in info['streams'] if x['codec_type']=='audio')
assert (video['width'],video['height'],video['codec_name'],video['r_frame_rate'],int(video['nb_frames']))==(1080,1920,'h264','30/1',5292)
assert audio['codec_name']=='aac' and audio['sample_rate']=='48000'
assert audiohash(old)==audiohash(v) and audiohash(old,True)==audiohash(v,True)
a=json.loads((p/'work/candidate-v01/remotion_props.json').read_text())['data'];b=json.loads((o/'remotion_props.json').read_text())['data'];assert a['meta']==b['meta']
allowed={'sourceCamera','sourceRect','kind','assetPath','mediaStartFrame','visualType','sourceWidth','sourceHeight','evidenceSequence','sourceHighlights','sourceRedactions'}
for x,y in zip(a['scenes'],b['scenes']):
 assert len(a['scenes'])==len(b['scenes'])==35
 if x['kind']=='effect':assert x==y
 else:
  assert not(set(x)|set(y))-allowed-{k for k in set(x)|set(y) if x.get(k)==y.get(k)},x['id']
  for e in [y]+y.get('evidenceSequence',[]):assert 'sourceRect' not in e
assert (o/'字幕.srt').read_bytes()==(p/'work/candidate-v01/字幕.srt').read_bytes()
frames=r/'frames';frames.mkdir(exist_ok=True)
named=json.loads((r/'review-frames.json').read_text());cursor=0;effects=[]
for s in b['scenes']:
 named[s['id']+'-mid']=cursor+s['durationFrames']//2
 if s['kind']!='effect':
  named[s['id']+'-full']=cursor+3
  for e in s.get('evidenceSequence',[]):named[s['id']+'-evidence-'+str(e['fromFrame'])]=cursor+e['fromFrame']+2
 else:effects.append((s['id'],cursor+s['durationFrames']//2))
 cursor+=s['durationFrames']
def extract(src,frame,dest,size='360:640'):
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(frame/30),'-i',str(src),'-frames:v','1','-vf','scale='+size,'-threads','1',str(dest)],check=True)
for name,f in named.items():extract(v,f,frames/(name+'.jpg'))
def sheet(items,dest,cols=4):
 w,h=360,668;im=Image.new('RGB',(cols*w,((len(items)+cols-1)//cols)*h),'white');d=ImageDraw.Draw(im)
 for i,n in enumerate(items):
  x=i%cols*w;y=i//cols*h;im.paste(Image.open(frames/(n+'.jpg')),(x,y+28));d.text((x+8,y+7),n,fill='black')
 im.save(r/dest)
sheet(list(json.loads((r/'review-frames.json').read_text())),'camera-review.jpg')
sheet([s['id']+'-mid' for s in b['scenes']],'all-scenes.jpg',7)
sheet([n for n in named if '-full' in n or '-evidence-' in n],'full-window-review.jpg',6)
comparisons=[]
for name,f in effects:
 path=frames/(name+'-old.jpg');extract(old,f,path)
 diff=ImageStat.Stat(ImageChops.difference(Image.open(path),Image.open(frames/(name+'-mid.jpg')))).mean
 comparisons.append({'scene':name,'mean_pixel_error_0_255':sum(diff)/3});assert sum(diff)/3<1.5
j=[]
for f in [334,335]:
 path=frames/(str(f)+'-lossless.png');extract(v,f,path,'1080:1920');j.append(Image.open(path).crop((28,510,1052,1590)))
join_error=sum(ImageStat.Stat(ImageChops.difference(*j)).mean)/3;assert join_error<1.5
report={'status':'technical_pass_visual_review_pending','revision':'v02','video_sha256':hashfile(v),'width':1080,'height':1920,'fps':30,'frames':5292,'duration_seconds':176.4,'video_codec':video['codec_name'],'pixel_format':video['pix_fmt'],'audio_codec':'aac','audio_sample_rate':audio['sample_rate'],'full_decode':'pass','scene_count':35,'real_scenes':22,'motion_scenes':13,'image_generated_scenes':0,'audio_reused_byte_for_byte':True,'audio_aac_sha256':audiohash(v),'audio_decoded_pcm_sha256':audiohash(v,True),'brand_bgm_metadata_unchanged':True,'all_narration_subtitles_timing_unchanged':True,'all_real_scenes_no_precrop':True,'source_motion_scenes_unchanged':True,'encoded_motion_midpoint_comparisons':comparisons,'harness_join_media_mean_pixel_error':join_error,'camera_geometry_checks':json.loads((r/'geometry-checks.json').read_text()),'visual_review_frames':len(named),'scope':'Agent encoded-frame and camera-path review; native playback recorded separately. No claim of full human listening/viewing, user aesthetic acceptance or publication.'}
(o/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:report[k] for k in ['status','video_sha256','audio_reused_byte_for_byte','harness_join_media_mean_pixel_error','visual_review_frames']},ensure_ascii=False))
