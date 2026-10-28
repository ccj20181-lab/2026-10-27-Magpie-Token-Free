import {BgmTrack} from './BgmTrack';
import React from "react";
import {DirectorComposition} from "./DirectorComposition";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Loop,
  OffthreadVideo,
  Sequence,
  Series,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { AiCoachDemoData, AiCoachScene, CaptionSegment } from "./types";

const cdiDeepBlue = "#032442";
const yellow = "#FFD84D";
const contentSideSafe = 52;
const captionSideSafe = 76;
const illustrationStage = { top: 620, left: 52, right: 52, bottom: 610 } as const;
const recordingStage = { top: 390, left: 28, right: 28, bottom: 290 } as const;
const illustrationCaptionBottom = 300;
const recordingCaptionBottom = 130;

const NarrationTracks: React.FC<{ data: AiCoachDemoData }> = ({ data }) => (
  <>
    {(data.narrationTracks || []).map((track) => (
      <Sequence
        key={track.id}
        from={track.startFrame}
        durationInFrames={Math.max(1, track.durationFrames)}
      >
        <Audio src={staticFile(track.path)} />
      </Sequence>
    ))}
  </>
);

const SceneAudio: React.FC<{ scene: AiCoachScene }> = ({ scene }) =>
  scene.audioPath ? <Audio src={staticFile(scene.audioPath)} /> : null;

const PageShell: React.FC<{
  seriesTitle: string;
  episode: string;
  showEpisodeMarker?: boolean;
  backgroundPath?: string;
  cornerLogoPath?: string;
  cornerLogoWidth?: number;
  cornerLogoHeight?: number;
  cornerLogoBackground?: string;
  cornerLogoPaddingX?: number;
  cornerLogoPaddingY?: number;
  cornerLogoBorderRadius?: number;
  children: React.ReactNode;
}> = ({
  seriesTitle,
  episode,
  showEpisodeMarker = true,
  backgroundPath,
  cornerLogoPath,
  cornerLogoWidth = 136,
  cornerLogoHeight = 136,
  cornerLogoBackground,
  cornerLogoPaddingX = 0,
  cornerLogoPaddingY = 0,
  cornerLogoBorderRadius = 0,
  children,
}) => (
  <AbsoluteFill
    style={{
      background: cdiDeepBlue,
      color: "#F8FBFF",
      fontFamily: '"SF Pro Display","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif',
    }}
  >
    {backgroundPath ? (
      <Img
        src={staticFile(backgroundPath)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
    ) : null}
    <div
      style={{
        position: "absolute",
        top: 236,
        left: 64,
        right: 84,
        height: 136,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        zIndex: 20,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            padding: "16px 26px",
            borderRadius: 45,
            background: yellow,
            color: "#06172E",
            fontWeight: 900,
            fontSize: 34,
            boxShadow: "0 16px 36px rgba(255,216,77,0.25)",
          }}
        >
          {seriesTitle}
        </div>
        {showEpisodeMarker ? (
          <div
            style={{
              padding: "12px 17px",
              borderRadius: 60,
              background: "#F04B3E",
              color: "#FFFFFF",
              fontWeight: 800,
              fontSize: 26,
            }}
          >
            #{episode}
          </div>
        ) : null}
      </div>
      {cornerLogoPath ? (
        <div
          style={{
            boxSizing: "content-box",
            width: cornerLogoWidth,
            height: cornerLogoHeight,
            padding: `${cornerLogoPaddingY}px ${cornerLogoPaddingX}px`,
            borderRadius: 0,
            background: cornerLogoBackground || "transparent",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 21,
          }}
        >
          <Img
            src={staticFile(cornerLogoPath)}
            style={{
              width: cornerLogoWidth,
              height: cornerLogoHeight,
              objectFit: "contain",
            }}
          />
        </div>
      ) : null}
    </div>
    {children}
  </AbsoluteFill>
);

const activeCaptionText = (segments: CaptionSegment[] | undefined, fallback: string, frame: number) => {
  if (!segments?.length) return fallback;
  const active = segments.find((segment) => frame >= segment.startFrame && frame < segment.endFrame);
  return (active || segments[segments.length - 1]).text;
};

const CaptionBox: React.FC<{
  scene: AiCoachScene;
  compact?: boolean;
  cdiStyle?: boolean;
  lower?: boolean;
}> = ({
  scene,
  compact = false,
  cdiStyle = false,
  lower = false,
}) => {
  const frame = useCurrentFrame();
  const captionText = activeCaptionText(scene.captionSegments, scene.caption, frame);
  const captionLength = Array.from(captionText).length;
  const baseFontSize = 44;
  const fontSize =
    captionLength > 24 ? baseFontSize - 8 : captionLength > 20 ? baseFontSize - 5 : captionLength > 18 ? baseFontSize - 2 : baseFontSize;

  return (
  <div
    style={{
      position: "absolute",
      left: captionSideSafe,
      right: captionSideSafe,
      bottom: lower ? recordingCaptionBottom : illustrationCaptionBottom,
      padding: "18px 24px",
      borderRadius: 0,
      background: "rgba(9,24,52,0.86)",
      border: "1.5px solid rgba(255,255,255,0.14)",
      boxShadow: "0 18px 55px rgba(0,0,0,0.22)",
      zIndex: 20,
    }}
  >
    <div
      style={{
        fontSize,
        lineHeight: 1.42,
        fontWeight: 700,
        color: "#FFFFFF",
        textAlign: "center",
        textShadow: "none",
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "clip",
      }}
    >
      {captionText}
    </div>
  </div>
  );
};

const IntroScene: React.FC<{ scene: AiCoachScene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const assets = scene.assetPaths?.length ? scene.assetPaths : [scene.assetPath];
  const assetIndex = Math.min(
    assets.length - 1,
    Math.floor((frame / Math.max(1, scene.durationFrames)) * assets.length),
  );
  const enter = spring({ fps: 30, frame, config: { damping: 16, stiffness: 90 } });
  const zoom = interpolate(frame, [0, scene.durationFrames - 1], [1, 1.025], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.ease),
  });
  const recordingImage = scene.layout === "recording";
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          ...(recordingImage ? recordingStage : illustrationStage),
          overflow: "hidden",
          opacity: enter,
          transform: `translateY(${(1 - enter) * 18}px)`,
        }}
      >
        <Img
          src={staticFile(assets[assetIndex])}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            transform: `scale(${zoom})`,
          }}
        />
      </div>
      <CaptionBox scene={scene} cdiStyle lower={recordingImage} />
      <SceneAudio scene={scene} />
    </AbsoluteFill>
  );
};

const TitleScene: React.FC<{ scene: AiCoachScene; demoTitle: string }> = ({ scene, demoTitle }) => {
  const frame = useCurrentFrame();
  const titleEnter = spring({
    fps: 30,
    frame: Math.max(0, frame - 4),
    config: { damping: 14, stiffness: 110 },
  });
  return (
    <AbsoluteFill>
      <Img
        src={staticFile(scene.assetPath)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: "brightness(0.46)",
          transform: "scale(1.08)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(circle at top, rgba(255,216,77,0.18), rgba(4,18,43,0.86) 58%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 300,
          left: contentSideSafe,
          right: contentSideSafe,
          zIndex: 10,
          opacity: titleEnter,
          transform: `translateY(${(1 - titleEnter) * 24}px)`,
        }}
      >
        <div
          style={{
            fontSize: 86,
            lineHeight: 1.08,
            fontWeight: 900,
            color: "white",
            textShadow: "0 12px 32px rgba(0,0,0,0.34)",
          }}
        >
          {demoTitle}
        </div>
      </div>
      <CaptionBox scene={scene} />
      <SceneAudio scene={scene} />
    </AbsoluteFill>
  );
};

const VideoScene: React.FC<{ scene: AiCoachScene }> = ({ scene }) => {
  const loopFrames = Math.max(1, Math.round((scene.videoDurationSeconds || 1) * 30));
  return (
    <AbsoluteFill>
    <div
      style={{
        position: "absolute",
        ...recordingStage,
        borderRadius: 0,
        overflow: "hidden",
        clipPath: "inset(0 round 20px)",
        isolation: "isolate",
        contain: "paint",
        zIndex: 1,
        background: "transparent",
        boxShadow: "none",
        border: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Loop durationInFrames={loopFrames}>
        <OffthreadVideo
          src={staticFile(scene.assetPath)}
          muted
          style={{
            position: "absolute",
            left: "50%",
            top: 0,
            transform: "translateX(-50%)",
            width: "auto",
            height: "100%",
            maxWidth: "100%",
            objectFit: "contain",
            backgroundColor: "transparent",
            borderRadius: 0,
            clipPath: "inset(0 round 40px)",
          }}
        />
      </Loop>
    </div>
    <CaptionBox scene={scene} compact lower />
    <SceneAudio scene={scene} />
    </AbsoluteFill>
  );
};

const CtaScene: React.FC<{ scene: AiCoachScene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const fps = 30;
  const logoIn = spring({ frame, fps, config: { damping: 15, stiffness: 105 } });
  const textIn = spring({ frame: Math.max(0, frame - 10), fps, config: { damping: 18, stiffness: 100 } });
  const ring = interpolate(frame % 90, [0, 45, 90], [0.94, 1.04, 0.94], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(circle at 50% 32%, rgba(255,216,77,0.18), rgba(6,23,46,0) 35%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 292,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: logoIn,
          transform: `translateY(${(1 - logoIn) * 28}px) scale(${0.88 + logoIn * 0.12})`,
        }}
      >
        <div
          style={{
            width: 430,
            height: 430,
            borderRadius: 0,
            padding: 14,
            background: "rgba(255,255,255,0.96)",
            boxShadow: "0 28px 90px rgba(0,0,0,0.34)",
            transform: `scale(${ring})`,
          }}
        >
          <Img
            src={staticFile(scene.assetPath)}
            style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 0 }}
          />
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: contentSideSafe,
          right: contentSideSafe,
          top: 812,
          textAlign: "center",
          opacity: textIn,
          transform: `translateY(${(1 - textIn) * 20}px)`,
        }}
      >
        <div
          style={{
            fontSize: 76,
            lineHeight: 1.08,
            color: "#FFFFFF",
            fontWeight: 900,
            textShadow: "0 10px 34px rgba(0,0,0,0.28)",
          }}
        >
          {scene.headline}
        </div>
        <div
          style={{
            marginTop: 26,
            fontSize: 36,
            lineHeight: 1.36,
            color: "#EAF2FF",
            fontWeight: 700,
          }}
        >
          AI实战玩家，专注用AI解决真问题
        </div>
      </div>
      <CaptionBox scene={scene} />
      <SceneAudio scene={scene} />
    </AbsoluteFill>
  );
};

const LegacyComposition: React.FC<{ data: AiCoachDemoData }> = ({ data }) => (
  <PageShell
    seriesTitle={data.meta.seriesTitle}
    episode={data.meta.episode}
    showEpisodeMarker={data.meta.showEpisodeMarker}
    backgroundPath={data.meta.backgroundPath}
    cornerLogoPath={data.meta.cornerLogoPath}
    cornerLogoWidth={data.meta.cornerLogoWidth}
    cornerLogoHeight={data.meta.cornerLogoHeight}
    cornerLogoBackground={data.meta.cornerLogoBackground}
    cornerLogoPaddingX={data.meta.cornerLogoPaddingX}
    cornerLogoPaddingY={data.meta.cornerLogoPaddingY}
    cornerLogoBorderRadius={data.meta.cornerLogoBorderRadius}
  >
    <BgmTrack data={data} />
    <NarrationTracks data={data} />
    <Series>
      {data.scenes.map((scene) => (
        <Series.Sequence key={scene.id} durationInFrames={scene.durationFrames}>
          {scene.kind === "image" ? (
            <IntroScene scene={scene} />
          ) : scene.kind === "title" ? (
            <TitleScene scene={scene} demoTitle={data.meta.demoTitle} />
          ) : scene.kind === "cta" ? (
            <CtaScene scene={scene} />
          ) : (
            <VideoScene scene={scene} />
          )}
        </Series.Sequence>
      ))}
    </Series>
  </PageShell>
);

export const AiCoachDailyDemoComposition: React.FC<{data:AiCoachDemoData}>=({data})=>data.meta.workflowVersion===2?<DirectorComposition data={data}/>:<LegacyComposition data={data}/>;
export default AiCoachDailyDemoComposition;
