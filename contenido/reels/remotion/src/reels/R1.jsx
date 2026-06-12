import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { fadeUp, fadeIn, lineGrow, GOLD, BG, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const Logo = ({ frame, fps, delay = 0 }) => {
  const style = fadeIn(frame, fps, delay);
  return (
    <div style={{ ...style, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <ellipse cx="24" cy="24" rx="20" ry="12" stroke={GOLD} strokeWidth="1.5" fill="none" opacity="0.8"/>
        <circle cx="24" cy="24" r="6" fill={GOLD} opacity="0.9"/>
        <circle cx="24" cy="24" r="2.5" fill={BG}/>
        <line x1="4" y1="24" x2="9" y2="24" stroke={GOLD} strokeWidth="1" opacity="0.5"/>
        <line x1="39" y1="24" x2="44" y2="24" stroke={GOLD} strokeWidth="1" opacity="0.5"/>
      </svg>
      <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 14, letterSpacing: '0.25em', textTransform: 'uppercase', color: GOLD, opacity: 0.7 }}>
        Endonautas
      </span>
    </div>
  );
};

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1.5, background: GOLD, opacity: 0.5, ...s, margin: '24px auto' }} />;
};

const BigText = ({ frame, fps, delay, children, style = {} }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 72,
      fontWeight: 700,
      color: WHITE,
      lineHeight: 1.15,
      textAlign: 'center',
      padding: '0 60px',
      ...style,
    }}>
      {children}
    </div>
  );
};

const Body = ({ frame, fps, delay, children, style = {} }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 300,
      fontSize: 32,
      color: '#cccccc',
      lineHeight: 1.7,
      textAlign: 'center',
      padding: '0 80px',
      ...style,
    }}>
      {children}
    </div>
  );
};

const GoldText = ({ frame, fps, delay, children }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontStyle: 'italic',
      fontSize: 64,
      color: GOLD,
      textAlign: 'center',
      padding: '0 60px',
      lineHeight: 1.2,
    }}>
      {children}
    </div>
  );
};

export const R1 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade out at end
  const totalFrames = 35 * fps;
  const fadeOutStart = totalFrames - 30;
  const globalOpacity = frame > fadeOutStart
    ? 1 - (frame - fadeOutStart) / 30
    : 1;

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity: globalOpacity }}>
      <style>{FONTS}</style>

      {/* Background radial glow */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 70% 50% at 50% 50%, rgba(201,168,76,0.04) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Grain texture overlay */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.03,
        backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noise)\'/%3E%3C/svg%3E")',
        pointerEvents: 'none',
      }} />

      {/* FASE 1: Logo (frames 0-60) */}
      <Sequence from={0} durationInFrames={90}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          <Logo frame={frame} fps={fps} delay={10} />
        </AbsoluteFill>
      </Sequence>

      {/* FASE 2: Hook contraintuitivo (frames 60-420) */}
      <Sequence from={60} durationInFrames={360}>
        <AbsoluteFill style={{ ...globalStyle, gap: 0, padding: '80px 0', justifyContent: 'center' }}>
          <BigText frame={frame - 60} fps={fps} delay={0}>
            El autoconocimiento
          </BigText>
          <BigText frame={frame - 60} fps={fps} delay={15}>
            te va a hacer
          </BigText>
          <BigText frame={frame - 60} fps={fps} delay={30} style={{ color: GOLD }}>
            más infeliz.
          </BigText>
          <GoldLine frame={frame - 60} fps={fps} delay={60} />
          <Body frame={frame - 60} fps={fps} delay={80} style={{ fontSize: 26, color: MUTED }}>
            Antes de que me mates:
          </Body>
          <Body frame={frame - 60} fps={fps} delay={95} style={{ fontSize: 36, color: WHITE }}>
            escúchame.
          </Body>
        </AbsoluteFill>
      </Sequence>

      {/* FASE 3: Desarrollo (frames 420-750) */}
      <Sequence from={420} durationInFrames={330}>
        <AbsoluteFill style={{ ...globalStyle, gap: 32, padding: '100px 0' }}>
          <Body frame={frame - 420} fps={fps} delay={0}>
            Cuando empiezas a conocerte de verdad,
          </Body>
          <Body frame={frame - 420} fps={fps} delay={20}>
            no encuentras paz inmediata.
          </Body>
          <GoldLine frame={frame - 420} fps={fps} delay={45} />
          <Body frame={frame - 420} fps={fps} delay={60}>
            Encuentras capas que nunca habías visto.
          </Body>
          <Body frame={frame - 420} fps={fps} delay={80}>
            Miedos detrás de tu personalidad.
          </Body>
          <Body frame={frame - 420} fps={fps} delay={100}>
            Patrones que llevan años corriendo
          </Body>
          <Body frame={frame - 420} fps={fps} delay={115} style={{ color: GOLD }}>
            sin permiso.
          </Body>
        </AbsoluteFill>
      </Sequence>

      {/* FASE 4: Cierre (frames 750-1050) */}
      <Sequence from={750} durationInFrames={300}>
        <AbsoluteFill style={{ ...globalStyle, gap: 24, padding: '80px 0' }}>
          <Body frame={frame - 750} fps={fps} delay={0} style={{ color: MUTED }}>
            Ese dolor no es señal de que algo está mal.
          </Body>
          <Body frame={frame - 750} fps={fps} delay={20} style={{ color: MUTED }}>
            Es señal de que por primera vez
          </Body>
          <Body frame={frame - 750} fps={fps} delay={35} style={{ color: WHITE, fontWeight: 500 }}>
            estás mirando de verdad.
          </Body>
          <GoldLine frame={frame - 750} fps={fps} delay={70} />
          <BigText frame={frame - 750} fps={fps} delay={90} style={{ fontSize: 56 }}>
            No te hace feliz.
          </BigText>
          <GoldText frame={frame - 750} fps={fps} delay={115}>
            Te hace libre.
          </GoldText>
          <Body frame={frame - 750} fps={fps} delay={145} style={{ fontSize: 24, color: MUTED }}>
            Hay una diferencia enorme.
          </Body>
          <Body frame={frame - 750} fps={fps} delay={170} style={{
            fontSize: 26, color: GOLD, marginTop: 16,
            border: `1px solid ${GOLD}`, padding: '12px 32px', borderRadius: 4
          }}>
            🔖 Guarda esto — lo vas a necesitar
          </Body>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
