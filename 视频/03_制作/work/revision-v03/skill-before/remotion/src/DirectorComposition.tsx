import React from 'react';
import {AbsoluteFill, Audio, Img, Loop, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {AiCoachDemoData, AiCoachScene, BuiltinEffectParams} from './types';
import {customEffects} from './CustomEffects';
import {BgmTrack} from './BgmTrack';
import {RealMedia} from './RealMedia';
const blue='#032442',yellow='#FFD84D';
const panel={left:28,top:762,width:1024,height:576};
export const transitionVector=(role:string,index:number):[number,number]=>['question','summary','advice','cta'].includes(role)?[0,1]:[index%2===0?1:-1,0];
const Media:React.FC<{scene:AiCoachScene;mediaWidth?:number}>=({scene,mediaWidth=1024})=>{
 const rect=scene.sourceRect;const style:React.CSSProperties=rect&&scene.sourceWidth&&scene.sourceHeight?{position:'absolute',width:mediaWidth*scene.sourceWidth/rect[2],height:mediaWidth*scene.sourceHeight/rect[2],maxWidth:'none',left:-mediaWidth*rect[0]/rect[2],top:-mediaWidth*rect[1]/rect[2]}:{width:'100%',height:'100%',objectFit:'contain'};
 return scene.kind==='video'?<OffthreadVideo src={staticFile(scene.assetPath)} startFrom={scene.mediaStartFrame||0} muted style={style}/>:<Img src={staticFile(scene.assetPath)} style={style}/>;
};
const Effect:React.FC<{scene:AiCoachScene;local:number}>=({scene,local})=>{
 const e=scene.effect!;
 const Custom=Object.prototype.hasOwnProperty.call(customEffects,e.id)?customEffects[e.id]:undefined;
 if(Custom&&e.renderer!=='builtin') return <Custom scene={scene} local={local}/>;
 if(e.renderer==='custom'||!['list','steps','comparison','relationship','timeline','highlight'].includes(e.id)) throw new Error(`Motion effect "${e.id}" has no registered component in CustomEffects.tsx`);
 const {title,items}=e.params as unknown as BuiltinEffectParams;
 if(typeof title!=='string'||!Array.isArray(items)||!items.length) throw new Error(`Builtin effect "${e.id}" requires title/items; use renderer: custom for a custom implementation`);
 const active=Math.min(items.length-1,Math.floor(local/Math.max(1,scene.durationFrames/items.length)));
 const card=(x:{label:string;detail?:string},i:number)=><div key={i} style={{background:'#fff',color:blue,borderLeft:`10px solid ${yellow}`,padding:'22px 28px',minHeight:106,outline:i===active?'4px solid #FFD84D':undefined}}><div style={{fontSize:40,fontWeight:850}}>{x.label}</div>{x.detail&&<div style={{fontSize:28,marginTop:8,lineHeight:1.35}}>{x.detail}</div>}</div>;
 return <div style={{position:'absolute',left:58,right:58,top:e.id==='list'?500:650}}><div style={{fontSize:56,fontWeight:850,marginBottom:38}}>{title}</div>
 {e.id==='comparison'?<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:30}}>{items.map(card)}</div>:
 e.id==='relationship'?<div style={{display:'flex',flexDirection:'column',gap:14}}>{items.map((x,i)=><React.Fragment key={i}>{card(x,i)}{i<items.length-1&&<div style={{textAlign:'center',fontSize:45,color:yellow}}>↓</div>}</React.Fragment>)}</div>:
 e.id==='timeline'?<div style={{borderLeft:`5px solid ${yellow}`,paddingLeft:32,display:'grid',gap:36}}>{items.map(card)}</div>:
 e.id==='highlight'?<div style={{display:'grid',gap:32}}>{items.map((x,i)=><div key={i} style={{opacity:local>=i*scene.durationFrames/items.length?1:0.25}}>{card(x,i)}</div>)}</div>:
 <div style={{display:'grid',gap:24}}>{items.map((x,i)=>card({...x,label:e.id==='steps'?`${i+1}  ${x.label}`:x.label},i))}</div>}
 </div>;
};
export const DirectorComposition:React.FC<{data:AiCoachDemoData}>=({data})=>{
 const frame=useCurrentFrame();let cursor=0;const starts=data.scenes.map(s=>{const t=cursor;cursor+=s.durationFrames;return t;});let index=starts.findIndex((x,i)=>frame>=x&&frame<x+data.scenes[i].durationFrames);index=Math.max(0,index);const s=data.scenes[index],local=frame-starts[index],prev=data.scenes[index-1];
 const ai=s.visualType==='ai_image';const canSlide=ai&&prev?.visualType==='ai_image'&&prev.assetPath!==s.assetPath;const win=Math.min(7,Math.floor(s.durationFrames/4));const moving=canSlide&&local<win;const progress=interpolate(local,[0,Math.max(1,win)],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});const [vx,vy]=transitionVector(s.semanticRole||'explain',index);
 const c=s.captionSegments?.find(c=>local>=c.startFrame&&local<c.endFrame);const text=c?.text||(!s.captionSegments?s.caption:'');
 return <AbsoluteFill style={{background:blue,color:'white',fontFamily:'PingFang SC, Arial'}}>
 <div style={{position:'absolute',top:252,left:64,display:'flex',alignItems:'center',gap:20}}><div style={{background:yellow,color:blue,borderRadius:45,padding:'22px 28px',fontSize:34,fontWeight:850}}>{data.meta.seriesTitle}</div>{data.meta.showEpisodeMarker!==false&&<div style={{background:'#FF4B3F',borderRadius:60,padding:17,fontSize:28,fontWeight:800}}>#{data.meta.episode}</div>}</div>
 {data.meta.cornerLogoPath&&<div style={{position:'absolute',right:84,top:236+(136-(data.meta.cornerLogoHeight??136)-2*(data.meta.cornerLogoPaddingY??0))/2,width:data.meta.cornerLogoWidth??136,height:data.meta.cornerLogoHeight??136,padding:`${data.meta.cornerLogoPaddingY??0}px ${data.meta.cornerLogoPaddingX??0}px`,background:data.meta.cornerLogoBackground,borderRadius:data.meta.cornerLogoBorderRadius??0,boxSizing:'content-box'}}><Img src={staticFile(data.meta.cornerLogoPath)} style={{width:'100%',height:'100%',objectFit:'contain'}}/></div>}
 {s.kind==='effect'?<Effect scene={s} local={local}/>:ai?<div style={{position:'absolute',...panel,overflow:'hidden',background:'#FFFFFF',borderRadius:0}}>
 {moving&&prev&&<div style={{position:'absolute',inset:0,transform:`translate(${-vx*progress*100}%,${-vy*progress*100}%)`}}><Media scene={prev}/></div>}
 <div style={{position:'absolute',inset:0,transform:moving?`translate(${vx*(1-progress)*100}%,${vy*(1-progress)*100}%)`:'none'}}><Sequence from={starts[index]} durationInFrames={s.durationFrames} layout="none"><Media scene={s}/></Sequence></div>
 </div>:<RealMedia scene={s} local={local} sceneStart={starts[index]}/>}
 {text&&<div style={{position:'absolute',left:48,right:48,bottom:126,minHeight:98,boxSizing:'border-box',padding:'12px 14px',background:'#091D36',border:'1px solid #31506A',display:'flex',alignItems:'center',justifyContent:'center',fontSize:text.length>22?36:42,fontWeight:800,lineHeight:1.25,textAlign:'center'}}>{text}</div>}
 <BgmTrack data={data}/>
 {data.scenes.map((a,i)=>a.audioPath?<Sequence key={a.id} from={starts[i]} durationInFrames={a.durationFrames}><Audio src={staticFile(a.audioPath)}/></Sequence>:null)}
 </AbsoluteFill>;
};
