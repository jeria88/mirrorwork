import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { fadeUp, fadeIn, lineGrow, GOLD, BG, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1, background: GOLD, opacity: 0.4, ...s, margin: '32px auto' }} />;
};

const Hook = ({ frame, fps, delay, children }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 52,
      fontStyle: 'italic',
      color: WHITE,
      lineHeight: 1.3,
      textAlign: 'center',
      padding: '0 70px',
    }}>{children}</div>
  );
};

const Narrate = ({ frame, fps, delay, children, style = {} }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 300,
      fontSize: 28,
      color: '#bbbbbb',
      lineHeight: 1.8,
      textAlign: 'center',
      padding: '0 90px',
      ...style,
    }}>{children}</div>
  );
};

const Reveal = ({ frame, fps, delay, children }) => {
  const anim = fadeUp(frame, fps, delay, { damping: 70, stiffness: 150 });
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 56,
      fontWeight: 700,
      color: GOLD,
      textAlign: 'center',
      padding: '0 70px',
      lineHeight: 1.2,
    }}>{children}</div>
  );
};

export const R3 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = 50 * fps;
  const fadeOutStart = totalFrames - 30;
  const opacity = frame > fadeOutStart ? 1 - (frame - fadeOutStart) / 30 : 1;

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity }}>
      <style>{FONTS}</style>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(201,168,76,0.03) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* HOOK (0-120) */}
      <Sequence from={0} durationInFrames={120}>
        <AbsoluteFill style={{ ...globalStyle, padding: '120px 0' }}>
          <Hook frame={frame} fps={fps} delay={10}>
            "Hay algo que nunca te he contado
          </Hook>
          <Hook frame={frame} fps={fps} delay={30}>
            sobre por qué escribí este libro."
          </Hook>
        </AbsoluteFill>
      </Sequence>

      {/* SETUP: Era terapeuta (120-390) */}
      <Sequence from={120} durationInFrames={270}>
        <AbsoluteFill style={{ ...globalStyle, gap: 20, padding: '100px 0' }}>
          <Narrate frame={frame - 120} fps={fps} delay={0}>Hubo un período de mi vida</Narrate>
          <Narrate frame={frame - 120} fps={fps} delay={18} style={{ color: GOLD, fontWeight: 400 }}>en que no me reconocía.</Narrate>
          <GoldLine frame={frame - 120} fps={fps} delay={50} />
          <Narrate frame={frame - 120} fps={fps} delay={70}>Era terapeuta.</Narrate>
          <Narrate frame={frame - 120} fps={fps} delay={85}>Acompañaba a otros a encontrarse.</Narrate>
          <GoldLine frame={frame - 120} fps={fps} delay={115} />
          <Narrate frame={frame - 120} fps={fps} delay={135} style={{ color: WHITE }}>Y yo mismo</Narrate>
          <Narrate frame={frame - 120} fps={fps} delay={150} style={{ color: WHITE, fontWeight: 500 }}>estaba completamente perdido.</Narrate>
        </AbsoluteFill>
      </Sequence>

      {/* EL DESCUBRIMIENTO (390-720) */}
      <Sequence from={390} durationInFrames={330}>
        <AbsoluteFill style={{ ...globalStyle, gap: 22, padding: '100px 0' }}>
          <Narrate frame={frame - 390} fps={fps} delay={0} style={{ color: MUTED }}>No era una crisis visible.</Narrate>
          <Narrate frame={frame - 390} fps={fps} delay={18} style={{ color: MUTED }}>Fue algo más silencioso.</Narrate>
          <GoldLine frame={frame - 390} fps={fps} delay={50} />
          <Narrate frame={frame - 390} fps={fps} delay={70}>Me di cuenta de que</Narrate>
          <Narrate frame={frame - 390} fps={fps} delay={85}>la persona que los demás veían...</Narrate>
          <Reveal frame={frame - 390} fps={fps} delay={110}>no era yo.</Reveal>
        </AbsoluteFill>
      </Sequence>

      {/* QUIEBRE Y SALVACIÓN (720-1050) */}
      <Sequence from={720} durationInFrames={330}>
        <AbsoluteFill style={{ ...globalStyle, gap: 28, padding: '100px 0' }}>
          <Narrate frame={frame - 720} fps={fps} delay={0}>Era una construcción.</Narrate>
          <Narrate frame={frame - 720} fps={fps} delay={18} style={{ color: MUTED }}>Brillante, funcional, efectiva.</Narrate>
          <GoldLine frame={frame - 720} fps={fps} delay={55} />
          <Narrate frame={frame - 720} fps={fps} delay={75} style={{ color: WHITE, fontWeight: 500 }}>Pero no era yo.</Narrate>
          <Narrate frame={frame - 720} fps={fps} delay={120} style={{ color: MUTED }}>Eso me rompió.</Narrate>
          <Reveal frame={frame - 720} fps={fps} delay={150}>Y luego me salvó.</Reveal>
        </AbsoluteFill>
      </Sequence>

      {/* CIERRE (1050-1500) */}
      <Sequence from={1050} durationInFrames={450}>
        <AbsoluteFill style={{ ...globalStyle, gap: 24, padding: '100px 0' }}>
          <Narrate frame={frame - 1050} fps={fps} delay={0} style={{ color: MUTED, fontSize: 24 }}>Endonautica nació de ese momento.</Narrate>
          <GoldLine frame={frame - 1050} fps={fps} delay={30} />
          <Narrate frame={frame - 1050} fps={fps} delay={55}>Porque supe que no era el único</Narrate>
          <Narrate frame={frame - 1050} fps={fps} delay={72}>que vivía dentro de un personaje</Narrate>
          <Narrate frame={frame - 1050} fps={fps} delay={88} style={{ color: GOLD, fontWeight: 400 }}>que nunca eligió.</Narrate>
          <GoldLine frame={frame - 1050} fps={fps} delay={130} />
          <Narrate frame={frame - 1050} fps={fps} delay={160} style={{ color: WHITE }}>Si algo de esto te suena...</Narrate>
          <Narrate frame={frame - 1050} fps={fps} delay={180} style={{ color: GOLD, fontWeight: 500 }}>este es tu lugar.</Narrate>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
