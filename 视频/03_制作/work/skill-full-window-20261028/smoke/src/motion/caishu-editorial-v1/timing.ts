export const clamp = (x:number) => Math.max(0,Math.min(1,x));
export const easeOut = (x:number) => 1-Math.pow(1-clamp(x),4);
export const easeInOut = (x:number) => {
  const p=clamp(x); return p<.5?8*p*p*p*p:1-Math.pow(-2*p+2,4)/2;
};
export const lerp = (a:number,b:number,p:number) => a+(b-a)*p;
export const seconds = (value:number,fps=30) => Math.round(value*fps);
export const tween = (local:number,startFrame:number,durationFrames=20) =>
  easeOut((local-startFrame)/Math.max(1,durationFrames));
type TimedScene = {durationFrames:number;captionSegments?:{text:string;startFrame:number;endFrame:number}[]};
/** The supplied caption segments are anchors, not a claim of word-level forced alignment. */
export const cueFrame = (scene:TimedScene,phrase:string,fallbackFraction:number) =>
  scene.captionSegments?.find(s=>s.text.includes(phrase))?.startFrame ??
  Math.round(clamp(fallbackFraction)*scene.durationFrames);

/** Marker and stroke share the same cumulative path length, including unequal segments. */
export function pointOnPolyline(points:readonly (readonly [number,number])[],progress:number):[number,number] {
  if(points.length<2) throw new Error('A flow path needs at least two points');
  const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1]));
  const total=lengths.reduce((a,b)=>a+b,0);
  if(total===0)return [points[0][0],points[0][1]];
  let distance=clamp(progress)*total,index=0;
  while(index<lengths.length-1&&distance>lengths[index])distance-=lengths[index++];
  const p=lengths[index]===0?0:distance/lengths[index];
  return [lerp(points[index][0],points[index+1][0],p),lerp(points[index][1],points[index+1][1],p)];
}
