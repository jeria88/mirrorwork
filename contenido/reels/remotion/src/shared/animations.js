import { spring, interpolate } from 'remotion';

export const GOLD = '#7ecfa8'; // Brand Jade (used as highlight color)
export const BG = '#040810';   // Deep cosmic dark background
export const WHITE = '#F0E8DC'; // Brand cream color for text
export const MUTED = 'rgba(240,232,220,0.52)'; // Muted text opacity

export function fadeUp(frame, fps, delay = 0, cfg = {}) {
  const f = Math.max(0, frame - delay);
  const p = spring({ frame: f, fps, config: { damping: 85, stiffness: 180, mass: 1, ...cfg } });
  return {
    opacity: interpolate(p, [0, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    transform: `translateY(${interpolate(p, [0, 1], [40, 0])}px)`,
  };
}

export function fadeIn(frame, fps, delay = 0) {
  const f = Math.max(0, frame - delay);
  const p = spring({ frame: f, fps, config: { damping: 100, stiffness: 120, mass: 1 } });
  return { opacity: interpolate(p, [0, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) };
}

export function scaleIn(frame, fps, delay = 0) {
  const f = Math.max(0, frame - delay);
  const p = spring({ frame: f, fps, config: { damping: 80, stiffness: 200, mass: 0.8 } });
  return {
    opacity: interpolate(p, [0, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    transform: `scale(${interpolate(p, [0, 1], [0.85, 1])})`,
  };
}

export function lineGrow(frame, fps, delay = 0) {
  const f = Math.max(0, frame - delay);
  const p = spring({ frame: f, fps, config: { damping: 100, stiffness: 200, mass: 1 } });
  return { width: `${interpolate(p, [0, 1], [0, 60])}px` };
}

export const FONTS = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:ital,wght@0,300;0,400;0,700;0,900;1,900&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');
`;

export const globalStyle = {
  fontFamily: "'Space Grotesk', sans-serif",
  background: BG,
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  overflow: 'hidden',
  position: 'relative',
};
