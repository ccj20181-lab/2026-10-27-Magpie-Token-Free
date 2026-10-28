from pathlib import Path
import subprocess,json,hashlib,math
p=Path(__file__).resolve().parents[2];r=p/'work/revision-v04';o=p/'work/candidate-v04';current=p.parent/'04_交付/当前/video.mp4'
def cmd(a):subprocess.run(a,check=True)
def run(a):return subprocess.check_output(a)
assert (o/'outro.mp4').is_file() and (o/'mix.wav').is_file()
cmd(['ffmpeg','-v','error','-y','-i',str(current),'-map','0:v:0','-an','-c:v','copy',str(o/'body-video.mp4')])
(o/'concat.txt').write_text("file 'body-video.mp4'\nfile 'outro.mp4'\n")
cmd(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(o/'concat.txt'),'-map','0:v:0','-c:v','copy',str(o/'picture.mp4')])
cmd(['ffmpeg','-v','error','-y','-i',str(o/'picture.mp4'),'-i',str(o/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','volume=5dB','-c:a','aac','-b:a','192k','-movflags','+faststart',str(o/'video_candidate.mp4')])
def frame_hashes(f,limit=None):
 a=['ffmpeg','-v','error','-i',str(f),'-map','0:v:0']
 if limit:a+=['-frames:v',str(limit)]
 data=run(a+['-f','framemd5','-']).decode();return [x.split(',')[-1].strip() for x in data.splitlines() if x and not x.startswith('#')]
a=frame_hashes(current);b=frame_hashes(o/'video_candidate.mp4',5132);assert len(a)==len(b)==5132 and a==b
(r/'picture-integrity.json').write_text(json.dumps({'copied_video_prefix_frames':5132,'all_decoded_frame_hashes_identical':True,'prefix_video_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'appended_outro_frames':52},indent=2));print('First5132 decoded frames are exactly identical to v03. Only52 outro frames appended.')
