export type AiCoachSceneKind = "image" | "title" | "video" | "cta" | "effect";

export interface CaptionSegment {
  text: string;
  startFrame: number;
  endFrame: number;
}

export interface MotionEffect {
  id: string;
  renderer?: "builtin" | "custom";
  params: Record<string, unknown>;
}

export interface BuiltinEffectParams {
  title: string;
  items: {label: string; detail?: string}[];
}

export interface MotionEffectProps {
  scene: AiCoachScene;
  local: number;
}

export interface SourceCamera {
  fromFrame:number;
  toFrame:number;
  targetRect:[number,number,number,number];
}

export interface AiCoachScene {
  id: string;
  kind: AiCoachSceneKind;
  layout?: "illustration" | "recording";
  visualType?: "real_screenshot" | "real_recording" | "ai_image" | "motion_effect";
  semanticRole?: string;
  sourceRect?: [number, number, number, number];
  sourceWidth?: number;
  sourceHeight?: number;
  sourceHighlights?: {rect:[number,number,number,number];color?:string;strokeWidth?:number}[];
  sourceRedactions?: {rect:[number,number,number,number];color?:string}[];
  sourceCamera?:SourceCamera;
  evidenceSequence?: {fromFrame:number;assetPath:string;sourceWidth:number;sourceHeight:number;sourceRect?:[number,number,number,number];sourceCamera?:SourceCamera;sourceRedactions?:{rect:[number,number,number,number];color?:string}[];sourceHighlights?:{rect:[number,number,number,number];color?:string;strokeWidth?:number}[]}[];
  mediaSurface?: "desktop" | "phone";
  mediaStartFrame?: number;
  effect?: MotionEffect;
  headline: string;
  caption: string;
  captionSegments?: CaptionSegment[];
  audioPath?: string;
  assetPath: string;
  assetPaths?: string[];
  durationFrames: number;
  videoDurationSeconds?: number;
}

export interface NarrationTrack {
  id: string;
  path: string;
  startFrame: number;
  durationFrames: number;
}

export interface AiCoachDemoData {
  meta: {
    motionStyle?: string;
    brandProfile?: "miaodong_finance" | "caishu_ai_lab";
    workflowVersion?: number;
    seriesTitle: string;
    episode: string;
    showEpisodeMarker?: boolean;
    demoTitle: string;
    fps: number;
    width: number;
    height: number;
    backgroundPath?: string;
    logoPath?: string;
    cornerLogoPath?: string;
    cornerLogoWidth?: number;
    cornerLogoHeight?: number;
    cornerLogoBackground?: string;
    cornerLogoPaddingX?: number;
    cornerLogoPaddingY?: number;
    cornerLogoBorderRadius?: number;
    bgmOmissionReason?: string;
    bgm?: {
      path: string;
      volume: number;
      durationSeconds: number;
      fadeInSeconds?: number;
      fadeOutSeconds?: number;
      sourcePath?: string;
      sha256?: string;
    };
  };
  scenes: AiCoachScene[];
  narrationTracks?: NarrationTrack[];
}
