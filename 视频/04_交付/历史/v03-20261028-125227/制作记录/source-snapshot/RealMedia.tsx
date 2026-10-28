import React from 'react';
import {Img,OffthreadVideo,Sequence,staticFile} from 'remotion';
import type {AiCoachScene,SourceCamera} from './types';
import {REAL_MEDIA_FRAMES,REAL_MEDIA_BACKGROUND} from './realMediaLayout';

/** A real source starts as the complete window. Only an explicit, narrated camera cue may move in. */
export function cameraGeometry(width:number,height:number,local:number,camera?:SourceCamera) {
 const frame=REAL_MEDIA_FRAMES.desktop;
 const innerWidth=frame.width-2*frame.padding,innerHeight=frame.height-2*frame.padding;
 const fullScale=Math.min(innerWidth/width,innerHeight/height);
 let progress=0,scale=fullScale;
 let left=(innerWidth-width*fullScale)/2,top=(innerHeight-height*fullScale)/2;
 if(camera){
  const t=Math.max(0,Math.min(1,(local-camera.fromFrame)/Math.max(1,camera.toFrame-camera.fromFrame)));
  progress=t*t*(3-2*t); // settled ends, no bounce, drift or scale discontinuity
  const [x,y,w,h]=camera.targetRect;
  if(x<0||y<0||w<=0||h<=0||x+w>width||y+h>height)throw new Error('Camera target must remain inside the original window');
  const endScale=Math.min(innerWidth/w,innerHeight/h);
  scale=fullScale+(endScale-fullScale)*progress;
  // Interpolate the affine transform directly: a corner focus stays inside
  // the viewport throughout the move instead of briefly slipping offscreen.
  const endLeft=innerWidth/2-(x+w/2)*endScale;
  const endTop=innerHeight/2-(y+h/2)*endScale;
  left+=(endLeft-left)*progress;top+=(endTop-top)*progress;
 }
 return {frame,innerWidth,innerHeight,scale,left,top,progress};
}

export const RealMedia:React.FC<{scene:AiCoachScene;local:number;sceneStart:number}>=({scene,local,sceneStart})=>{
 const sw=scene.sourceWidth??1024,sh=scene.sourceHeight??576;
 const g=cameraGeometry(sw,sh,local,scene.sourceCamera);
 const imageStyle:React.CSSProperties={position:'absolute',left:g.left,top:g.top,width:sw*g.scale,height:sh*g.scale,maxWidth:'none'};
 return <div style={{position:'absolute',left:g.frame.left,top:g.frame.top,width:g.frame.width,height:g.frame.height,overflow:'hidden',background:REAL_MEDIA_BACKGROUND,borderRadius:0}}>
  <div style={{position:'absolute',left:g.frame.padding,top:g.frame.padding,width:g.innerWidth,height:g.innerHeight,overflow:'hidden'}}>
   <Sequence from={sceneStart} durationInFrames={scene.durationFrames} layout="none">
    {scene.kind==='video'?<OffthreadVideo src={staticFile(scene.assetPath)} startFrom={scene.mediaStartFrame??0} muted style={imageStyle}/>:<Img src={staticFile(scene.assetPath)} style={imageStyle}/>}
   </Sequence>
   {scene.sourceRedactions?.map((r,i)=><div key={`privacy-${i}`} style={{position:'absolute',left:g.left+r.rect[0]*g.scale,top:g.top+r.rect[1]*g.scale,width:r.rect[2]*g.scale,height:r.rect[3]*g.scale,background:r.color??'#D8DFE6',pointerEvents:'none'}}/>)}
   {scene.sourceHighlights?.map((r,i)=><div key={`focus-${i}`} style={{position:'absolute',left:g.left+r.rect[0]*g.scale,top:g.top+r.rect[1]*g.scale,width:r.rect[2]*g.scale,height:r.rect[3]*g.scale,border:`${r.strokeWidth??5}px solid ${r.color??'#D93232'}`,boxSizing:'border-box',pointerEvents:'none'}}/>)}
  </div>
 </div>;
};
