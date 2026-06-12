import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { fadeUp, fadeIn, lineGrow, GOLD, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1, background: GOLD, opacity: 0.4, ...s, margin: '32px auto' }} />;
};

const Manifesto = ({ frame, fps, delay, children, gold = false, size = 56 }) => {
  const anim = fadeUp(frame, fps, delay, { damping: 75, stiffness: 140, mass: 1.1 });
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: size,
      fontStyle: gold ? 'italic' : 'normal',
      fontWeight: gold ? 400 : 700,
      color: gold ? GOLD : WHITE,
      textAlign: 'center',
      padding: '0 70px',
      lineHeight: 1.2,
    }}>{children}</div>
  );
};

const Quiet = ({ frame, fps, delay, children }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 300,
      fontSize: 28,
      color: MUTED,
      textAlign: 'center',
      padding: '0 90px',
      lineHeight: 1.7,
    }}>{children}</div>
  );
};

const Logo = ({ frame, fps, delay }) => {
  const anim = fadeIn(frame, fps, delay);
  return (
    <div style={{ ...anim, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
        <ellipse cx="28" cy="28" rx="24" ry="14" stroke={GOLD} strokeWidth="1.5" fill="none" opacity="0.7"/>
        <circle cx="28" cy="28" r="7" fill={GOLD} opacity="0.85"/>
        <circle cx="28" cy="28" r="3" fill="#050505"/>
        <line x1="4" y1="28" x2="10" y2="28" stroke={GOLD} strokeWidth="1" opacity="0.4"/>
        <line x1="46" y1="28" x2="52" y2="28" stroke={GOLD} strokeWidth="1" opacity="0.4"/>
      </svg>
      <span style={{ fontFamily: 'Inter', fontSize: 13, letterSpacing: '0.28em', textTransform: 'uppercase', color: GOLD, opacity: 0.65 }}>
        Endonautas
      </span>
    </div>
  );
};

export const R6 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = 30 * fps;
  const fadeOutStart = totalFrames - 30;
  const opacity = frame > fadeOutStart ? 1 - (frame - fadeOutStart) / 30 : 1;

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity }}>
      <style>{FONTS}</style>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 65% 55% at 50% 50%, rgba(201,168,76,0.04) 0%, transparent 68%)', pointerEvents: 'none' }} />

      {/* APERTURA: Logo (0-90) */}
      <Sequence from={0} durationInFrames={90}>
        <AbsoluteFill style={{ ...globalStyle }}>
          <Logo frame={frame} fps={fps} delay={10} />
        </AbsoluteFill>
      </Sequence>

      {/* DECLARACIÓN (90-360) */}
      <Sequence from={90} durationInFrames={270}>
        <AbsoluteFill style={{ ...globalStyle, gap: 16, padding: '110px 0' }}>
          <Manifesto frame={frame - 90} fps={fps} delay={0} size={52}>
            Endonautas no es un método.
          </Manifesto>
          <GoldLine frame={frame - 90} fps={fps} delay={35} />
          <Manifesto frame={frame - 90} fps={fps} delay={55} gold size={60}>
            Es un mapa para encontrarte.
          </Manifesto>
        </AbsoluteFill>
      </Sequence>

      {/* LA PREGUNTA (360-600) */}
      <Sequence from={360} durationInFrames={240}>
        <AbsoluteFill style={{ ...globalStyle, gap: 20, padding: '110px 0' }}>
          <Quiet frame={frame - 360} fps={fps} delay={0}>
            En algún momento de tu vida
          </Quiet>
          <Quiet frame={frame - 360} fps={fps} delay={18}>
            vas a tener que hacerte la pregunta.
          </Quiet>
          <GoldLine frame={frame - 360} fps={fps} delay={55} />
          <Quiet frame={frame - 360} fps={fps} delay={80} style={{ color: '#777' }}>
            No "¿cómo puedo ser mejor?"
          </Quiet>
          <Quiet frame={frame - 360} fps={fps} delay={105} style={{ color: '#777' }}>
            Sino...
          </Quiet>
          <Manifesto frame={frame - 360} fps={fps} delay={135} gold size={50}>
            "¿Quién soy realmente?"
          </Manifesto>
        </AbsoluteFill>
      </Sequence>

      {/* CIERRE (600-900) */}
      <Sequence from={600} durationInFrames={300}>
        <AbsoluteFill style={{ ...globalStyle, gap: 28, padding: '100px 0' }}>
          <Quiet frame={frame - 600} fps={fps} delay={0} style={{ color: '#999' }}>
            Cuando llegues a esa pregunta,
          </Quiet>
          <Manifesto frame={frame - 600} fps={fps} delay={22} size={52}>
            aquí estamos.
          </Manifesto>
          <GoldLine frame={frame - 600} fps={fps} delay={60} />
          <Logo frame={frame - 600} fps={fps} delay={90} />
          <GoldLine frame={frame - 600} fps={fps} delay={140} />
          <Quiet frame={frame - 600} fps={fps} delay={165} style={{ color: WHITE }}>
            El viaje empieza con tu Máscara.
          </Quiet>
          <div style={{ ...fadeUp(frame - 600, fps, 190), fontFamily: 'Inter', fontSize: 26, color: GOLD, textAlign: 'center', border: `1px solid ${GOLD}`, padding: '14px 40px', borderRadius: 4 }}>
            Comenta MASCARA
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
