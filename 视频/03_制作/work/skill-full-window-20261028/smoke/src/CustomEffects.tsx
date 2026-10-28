import type {ComponentType} from 'react';
import type {MotionEffectProps} from './types';

// Register each project's narration-driven components in its own source copy.
// Keys and params are open; this registry intentionally contains no topic templates.
export const customEffects: Record<string, ComponentType<MotionEffectProps>> = {};
