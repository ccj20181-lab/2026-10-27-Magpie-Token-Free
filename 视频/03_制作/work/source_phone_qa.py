# -*- coding: utf-8 -*-
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1];out=p/'work/source-phone-qa';out.mkdir(exist_ok=True)
data=json.loads((p/'work/candidate-v01/remotion_props.json').read_text())['data']
public=p/'remotion/public';sources=[]
for s in data['scenes']:
 if s['kind']=='effect':continue
 choices=s.get('evidenceSequence') or [s]
 for j,visual in enumerate(choices):
  sid=s['id']+('-'+str(j) if s.get('evidenceSequence') else '')
  src=public/visual['assetPath']
  if s['kind']=='video':
   frame=out/(sid+'-raw.png');t=(s.get('mediaStartFrame',0)+s['durationFrames']*.5)/30
   subprocess.run(['ffmpeg','-y','-v','error','-threads','1','-ss',str(t),'-i',str(src),'-frames:v','1',str(frame)],check=True)
   im=Image.open(frame).convert('RGB')
  else:im=Image.open(src).convert('RGB')
  d=ImageDraw.Draw(im)
  for h in visual.get('sourceHighlights',[]):
   x,y,w,hg=h['rect'];d.rectangle((x,y,x+w,y+hg),outline='#D93232',width=5)
  if visual.get('sourceRect'):
   x,y,w,h=visual['sourceRect'];im=im.crop((x,y,x+w,y+h))
  im.thumbnail((330,349))
  card=Image.new('RGB',(360,400),'#DDE3E3');d=ImageDraw.Draw(card);d.text((9,5),sid,fill='black');d.rectangle((9,28,350,388),fill='#F4F7FA');card.paste(im,(180-im.width//2,208-im.height//2));card.save(out/(sid+'.jpg'),quality=94);sources.append(sid)
for batch in range(0,len(sources),8):
 group=sources[batch:batch+8];sheet=Image.new('RGB',(1440,math.ceil(len(group)/4)*400),'#DDE3E3')
 for i,sid in enumerate(group):sheet.paste(Image.open(out/(sid+'.jpg')),(i%4*360,i//4*400))
 sheet.save(out/f'phone-sheet-{batch//8}.jpg',quality=94)
print('Source phone review frames',len(sources))
