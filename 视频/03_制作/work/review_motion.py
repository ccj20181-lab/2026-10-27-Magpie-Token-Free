#!/usr/bin/env python3
"""Sample the encoded Caishu motion scenes; produce review evidence, not an aesthetic pass."""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw

FRACTIONS=(.02,.20,.50,.85,.97,.995)
def review(video,props,out):
    video,props,out=Path(video).resolve(),Path(props).resolve(),Path(out).resolve()
    data=json.loads(props.read_text())['data'];fps=data['meta']['fps']
    if data['meta'].get('brandProfile')!='caishu_ai_lab':raise ValueError('This review layout is only for Caishu')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(video)]))
    stream=next(s for s in probe['streams'] if s['codec_type']=='video')
    if (stream['width'],stream['height'])!=(1080,1920):raise ValueError('Expected 1080x1920 encoded video')
    if int(stream['nb_frames'])!=sum(s['durationFrames'] for s in data['scenes']):raise ValueError('Encoded frame count differs from plan')
    out.mkdir(parents=True,exist_ok=True);tasks=[];cursor=0;motion=[]
    for scene in data['scenes']:
        if scene['kind']=='effect':
            motion.append(scene)
            for i,fraction in enumerate(FRACTIONS):
                local=min(scene['durationFrames']-1,int(scene['durationFrames']*fraction))
                tasks.append((scene['id'],i,(cursor+local)/fps))
        cursor+=scene['durationFrames']
    def capture(task):
        sid,i,time=task
        subprocess.run(['ffmpeg','-y','-v','error','-threads','1','-ss',str(time),'-i',str(video),'-vf',
                        'crop=1024:1100:28:470,scale=360:387','-frames:v','1',str(out/f'{sid}-{i}.png')],check=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:list(pool.map(capture,tasks))
    rows=[]
    for scene in motion:
        images=[Image.open(out/f'{scene["id"]}-{i}.png').convert('RGB') for i in range(len(FRACTIONS))]
        def delta(a,b):return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/(3*255)
        changes=[delta(a,b) for a,b in zip(images,images[1:])]
        rows.append({'scene_id':scene['id'],'phase_changes':changes,'final_hold_change':changes[-1],
                     'attention':['check reading hold or declare intentional continuing motion'] if changes[-1]>.006 else [],
                     'semantic_review':'required: compare object, action and landing with narration'})
    for batch in range(0,len(motion),4):
        group=motion[batch:batch+4];sheet=Image.new('RGB',(1080,len(group)*420),'#DDE3E3');draw=ImageDraw.Draw(sheet)
        for row,scene in enumerate(group):
            for col,i in enumerate((0,2,4)):
                sheet.paste(Image.open(out/f'{scene["id"]}-{i}.png'),(col*360,row*420+26))
                draw.text((col*360+8,row*420+7),f'{scene["id"]} / {FRACTIONS[i]:.0%}',fill='black')
        sheet.save(out/f'phone-contact-{batch//4}.jpg',quality=92)
    report={'status':'sampled_review_required','video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
            'fractions':FRACTIONS,'motion_scene_count':len(motion),'scenes':rows,
            'scope':'Encoded motion phase samples and phone contact sheets. Does not certify meaning, normal-speed rhythm, factual accuracy or sound.'}
    (out/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('video','props','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();r=review(a.video,a.props,a.out)
    print(json.dumps({'status':r['status'],'scenes':r['motion_scene_count'],'out':a.out},ensure_ascii=False))
