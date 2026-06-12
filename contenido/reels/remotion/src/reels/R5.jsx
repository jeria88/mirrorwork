import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { fadeUp, fadeIn, lineGrow, GOLD, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1.5, background: GOLD, opacity: 0.5, ...s, margin: '28px auto' }} />;
};

const Big = ({ frame, fps, delay, children, gold = false }) => {
  const anim = fadeUp(frame, fps, delay, { damping: 80, stiffness: 160 });
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 60,
      fontWeight: 700,
      color: gold ? GOLD : WHITE,
      textAlign: 'center',
      padding: '0 70px',
      lineHeight: 1.2,
    }}>{children}</div>
  );
};

const Sub = ({ frame, fps, delay, children, style = {} }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 300,
      fontSize: 30,
      color: '#cccccc',
      textAlign: 'center',
      padding: '0 80px',
      lineHeight: 1.7,
      ...style,
    }}>{children}</div>
  );
};

export const R5 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = 25 * fps;
  const fadeOutStart = totalFrames - 25;
  const opacity = frame > fadeOutStart ? 1 - (frame - fadeOutStart) / 25 : 1;

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity }}>
      <style>{FONTS}</style>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 60% at 50% 50%, rgba(201,168,76,0.05) 0%, transparent 65%)', pointerEvents: 'none' }} />

      {/* HOOK (0-180) */}
      <Sequence from={0} durationInFrames={180}>
        <AbsoluteFill style={{ ...globalStyle, gap: 20, padding: '120px 0' }}>
          <Sub frame={frame} fps={fps} delay={0} style={{ fontSize: 28, color: MUTED }}>
            Si has llegado hasta aquí...
          </Sub>
          <Big frame={frame} fps={fps} delay={20}>
            hay algo en ti
          </Big>
          <Big frame={frame} fps={fps} delay={38} gold>
            que ya sabe que es hora.
          </Big>
        </AbsoluteFill>
      </Sequence>

      {/* PROPUESTA (180-480) */}
      <Sequence from={180} durationInFrames={300}>
        <AbsoluteFill style={{ ...globalStyle, gap: 24, padding: '100px 0' }}>
          <Sub frame={frame - 180} fps={fps} delay={0} style={{ color: MUTED }}>
            Tengo un test gratuito:
          </Sub>
          <Big frame={frame - 180} fps={fps} delay={20} style={{ fontSize: 56 }}>
            Descubre tu Máscara.
          </Big>
          <GoldLine frame={frame - 180} fps={fps} delay={55} />
          <Sub frame={frame - 180} fps={fps} delay={75}>
            Te toma 5 minutos.
          </Sub>
          <Sub frame={frame - 180} fps={fps} delay={90}>
            Te entrega un mapa
          </Sub>
          <Sub frame={frame - 180} fps={fps} delay={105} style={{ color: WHITE }}>
            de la identidad que construiste
          </Sub>
          <Sub frame={frame - 180} fps={fps} delay={120} style={{ color: GOLD, fontWeight: 400 }}>
            para sobrevivir.
          </Sub>
        </AbsoluteFill>
      </Sequence>

      {/* CTA FINAL (480-750) */}
      <Sequence from={480} durationInFrames={270}>
        <AbsoluteFill style={{ ...globalStyle, gap: 28, padding: '120px 0' }}>
          <Big frame={frame - 480} fps={fps} delay={0} style={{ fontSize: 52 }}>
            Solo comenta
          </Big>
          <Big frame={frame - 480} fps={fps} delay={18} gold style={{ fontSize: 72, letterSpacing: '0.05em' }}>
            MASCARA
          </Big>
          <Sub frame={frame - 480} fps={fps} delay={50} style={{ color: MUTED }}>en este video.</Sub>
          <GoldLine frame={frame - 480} fps={fps} delay={80} />
          <Sub frame={frame - 480} fps={fps} delay={100} style={{ color: MUTED, fontSize: 26 }}>Sin costo.</Sub>
          <Sub frame={frame - 480} fps={fps} delay={115} style={{ color: MUTED, fontSize: 26 }}>Sin trampa.</Sub>
          <Sub frame={frame - 480} fps={fps} delay={140} style={{ color: WHITE, fontWeight: 500 }}>Solo el mapa.</Sub>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
