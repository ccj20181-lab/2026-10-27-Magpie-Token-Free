import React from 'react';
import {Audio, Loop, staticFile, useCurrentFrame} from 'remotion';
import type {AiCoachDemoData} from './types';

export const BgmTrack: React.FC<{data: AiCoachDemoData}> = ({data}) => {
  const frame = useCurrentFrame();
  const bgm = data.meta.bgm;
  if (!bgm?.path) {
    if (data.meta.workflowVersion === 2 && !data.meta.bgmOmissionReason?.trim()) {
      throw new Error('BGM is required: assemble music before rendering this video');
    }
    return null;
  }
  const gain = bgm.volume ?? 0.15;
  if (!Number.isFinite(gain) || gain <= 0 || gain > 1) {
    throw new Error('BGM volume must be > 0 and <= 1');
  }
  const total = data.scenes.reduce((sum, scene) => sum + scene.durationFrames, 0);
  const fadeIn = Math.round((bgm.fadeInSeconds ?? 0.8) * data.meta.fps);
  const fadeOut = Math.round((bgm.fadeOutSeconds ?? 1.6) * data.meta.fps);
  const envelope = Math.min(1, fadeIn ? frame / fadeIn : 1,
    fadeOut ? Math.max(0, total - 1 - frame) / fadeOut : 1);
  return <Loop durationInFrames={Math.max(1, Math.round((bgm.durationSeconds || 30) * data.meta.fps))}>
    <Audio src={staticFile(bgm.path)} volume={gain * envelope}/>
  </Loop>;
};
