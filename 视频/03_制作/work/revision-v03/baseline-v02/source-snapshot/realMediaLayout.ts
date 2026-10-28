import type {AiCoachScene} from './types';

// Surface is explicit: a tall crop of a computer menu is not a phone screen.
// Fixed frames share a centre and backdrop; only source pixels are fitted inside.
export const REAL_MEDIA_FRAMES = {
  desktop: {left:28, top:510, width:1024, height:1080, padding:16},
  phone: {left:270, top:510, width:540, height:1080, padding:16},
} as const;
export const REAL_MEDIA_BACKGROUND = '#F4F7FA';

export const getRealMediaLayout = (scene:AiCoachScene) => {
  const surface=scene.mediaSurface ?? 'desktop';
  const frame=REAL_MEDIA_FRAMES[surface];
  const rect=scene.sourceRect ?? [0,0,scene.sourceWidth ?? 1024,scene.sourceHeight ?? 576];
  const scale=Math.min((frame.width-2*frame.padding)/rect[2],(frame.height-2*frame.padding)/rect[3]);
  const width=rect[2]*scale, height=rect[3]*scale;
  return {surface,frame,rect,scale,content:{left:(frame.width-width)/2,top:(frame.height-height)/2,width,height}};
};
