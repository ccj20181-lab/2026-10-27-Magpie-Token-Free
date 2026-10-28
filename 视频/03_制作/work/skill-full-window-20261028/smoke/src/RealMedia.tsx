import React from 'react';
import {Img,OffthreadVideo,Sequence,staticFile} from 'remotion';
import type {AiCoachScene} from './types';
import {getRealMediaLayout,REAL_MEDIA_BACKGROUND} from './realMediaLayout';

/** Keep the full source; move one affine camera inside a fixed media viewport. */
export const RealMedia:React.FC<{scene:AiCoachScene;local:number;sceneStart:number}>=({scene,local,sceneStart})=>{
 const g=getRealMediaLayout(scene,local),p=g.frame.padding;
 const style:React.CSSProperties={position:'absolute',left:g.content.left-p,top:g.content.top-p,width:g.content.width,height:g.content.height,maxWidth:'none'};
 return <div style={{position:'absolute',left:g.frame.left,top:g.frame.top,width:g.frame.width,height:g.frame.height,overflow:'hidden',background:REAL_MEDIA_BACKGROUND,borderRadius:0}}>
  <div style={{position:'absolute',left:p,top:p,width:g.frame.width-2*p,height:g.frame.height-2*p,overflow:'hidden'}}>
   <Sequence from={sceneStart} durationInFrames={scene.durationFrames} layout="none">
    {scene.kind==='video'?<OffthreadVideo src={staticFile(scene.assetPath)} startFrom={scene.mediaStartFrame??0} muted style={style}/>:<Img src={staticFile(scene.assetPath)} style={style}/>}
   </Sequence>
   {scene.sourceRedactions?.map((r,i)=><div key={`privacy-${i}`} style={{position:'absolute',left:g.content.left-p+r.rect[0]*g.scale,top:g.content.top-p+r.rect[1]*g.scale,width:r.rect[2]*g.scale,height:r.rect[3]*g.scale,background:r.color??'#D8DFE6',pointerEvents:'none'}}/>)}
   {scene.sourceHighlights?.map((r,i)=><div key={`focus-${i}`} style={{position:'absolute',left:g.content.left-p+r.rect[0]*g.scale,top:g.content.top-p+r.rect[1]*g.scale,width:r.rect[2]*g.scale,height:r.rect[3]*g.scale,border:`${r.strokeWidth??5}px solid ${r.color??'#D93232'}`,boxSizing:'border-box',pointerEvents:'none'}}/>)}
  </div>
 </div>;
};
