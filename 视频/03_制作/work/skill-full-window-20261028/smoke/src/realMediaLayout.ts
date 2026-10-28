import type {AiCoachScene} from './types';

// Surface is explicit: a tall crop of a computer menu is not a phone screen.
// Fixed frames share a centre and backdrop; only source pixels are fitted inside.
export const REAL_MEDIA_FRAMES = {
  desktop: {left:28, top:510, width:1024, height:1080, padding:16},
  phone: {left:270, top:510, width:540, height:1080, padding:16},
} as const;
export const REAL_MEDIA_BACKGROUND = '#F4F7FA';

export const getRealMediaLayout = (scene:AiCoachScene, local=0) => {
  const surface=scene.mediaSurface ?? 'desktop';
  const frame=REAL_MEDIA_FRAMES[surface];
  const rect:[number,number,number,number]=[0,0,scene.sourceWidth ?? 1024,scene.sourceHeight ?? 576];
  const iw=frame.width-2*frame.padding,ih=frame.height-2*frame.padding;
  let scale=Math.min(iw/rect[2],ih/rect[3]);
  let left=(iw-rect[2]*scale)/2,top=(ih-rect[3]*scale)/2,progress=0;
  const c=scene.sourceCamera;
  if(c){
    const [x,y,w,h]=c.targetRect;
    if(![x,y,w,h,c.fromFrame,c.toFrame].every(Number.isFinite)||x<0||y<0||w<=0||h<=0||x+w>rect[2]||y+h>rect[3]||!Number.isInteger(c.fromFrame)||!Number.isInteger(c.toFrame)||c.fromFrame<=0||c.toFrame<=c.fromFrame||c.toFrame>=scene.durationFrames)throw new Error('Camera requires a full-window hold, in-source target, and landing hold within the scene');
    const t=Math.max(0,Math.min(1,(local-c.fromFrame)/(c.toFrame-c.fromFrame)));
    progress=t*t*(3-2*t);
    const endScale=Math.min(iw/w,ih/h);
    // Interpolate the affine transform, not centre * scale: corner targets must
    // stay in view during the entire move, including daily-credit cards.
    left+=(iw/2-(x+w/2)*endScale-left)*progress;
    top+=(ih/2-(y+h/2)*endScale-top)*progress;
    scale+=(endScale-scale)*progress;
  }
  return {surface,frame,rect,scale,progress,content:{left:frame.padding+left,top:frame.padding+top,width:rect[2]*scale,height:rect[3]*scale}};
};
