import React from "react";
import { Composition } from "remotion";
import { AiCoachDailyDemoComposition } from "./AiCoachDailyDemoComposition";
import { AiCoachDemoData } from "./types";
import {MagpieCover} from './MagpieCover';

const fallbackData: AiCoachDemoData = {
  meta: {
    seriesTitle: "每天一个AI理财小技巧",
    episode: "00",
    demoTitle: "AI Coach Daily Demo",
    fps: 30,
    width: 1080,
    height: 1920,
  },
  scenes: [
    {
      id: "scene_01",
      kind: "image",
      headline: "",
      caption: "",
      audioPath: "",
      assetPath: "",
      durationFrames: 30,
    },
  ],
};

export const RemotionRoot: React.FC = () => {
  return (
    <><Composition id="MagpieCover" component={MagpieCover} durationInFrames={1} fps={30} width={1080} height={1920} defaultProps={{data:fallbackData}}/><Composition
      id="AiCoachDailyDemo"
      component={AiCoachDailyDemoComposition as React.ComponentType<{ data: AiCoachDemoData }>}
      durationInFrames={30}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ data: fallbackData }}
      calculateMetadata={({ props }) => {
        const data = props.data as AiCoachDemoData;
        const totalFrames = data.scenes.reduce(
          (acc, scene) => acc + Math.max(1, scene.durationFrames || 0),
          0
        );
        return {
          durationInFrames: totalFrames || 30,
          fps: data.meta.fps || 30,
          width: data.meta.width || 1080,
          height: data.meta.height || 1920,
        };
      }}
    /></>
  );
};

export default RemotionRoot;
