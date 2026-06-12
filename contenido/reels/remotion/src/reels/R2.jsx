import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { fadeUp, fadeIn, lineGrow, GOLD, BG, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1.5, background: GOLD, opacity: 0.5, ...s, margin: '28px auto' }} />;
};

const BigQ = ({ frame, fps, delay, children }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 60,
      fontStyle: 'italic',
      color: WHITE,
      lineHeight: 1.25,
      textAlign: 'center',
      padding: '0 70px',
    }}>{children}</div>
  );
};

const Answer = ({ frame, fps, delay, children, gold = false }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: '"Playfair Display", serif',
      fontSize: 52,
      fontWeight: 700,
      color: gold ? GOLD : WHITE,
      textAlign: 'center',
      padding: '0 60px',
      lineHeight: 1.2,
    }}>{children}</div>
  );
};

const Body = ({ frame, fps, delay, children, style = {} }) => {
  const anim = fadeUp(frame, fps, delay);
  return (
    <div style={{
      ...anim,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 300,
      fontSize: 30,
      color: '#cccccc',
      lineHeight: 1.75,
      textAlign: 'center',
      padding: '0 80px',
      ...style,
    }}>{children}</div>
  );
};

export const R2 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = 25 * fps;
  const fadeOutStart = totalFrames - 25;
  const globalOpacity = frame > fadeOutStart ? 1 - (frame - fadeOutStart) / 25 : 1;

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity: globalOpacity }}>
      <style>{FONTS}</style>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(201,168,76,0.05) 0%, transparent 65%)', pointerEvents: 'none' }} />

      {/* HOOK (0-210) */}
      <Sequence from={0} durationInFrames={210}>
        <AbsoluteFill style={{ ...globalStyle, gap: 24, padding: '100px 0' }}>
          <BigQ frame={frame} fps={fps} delay={0}>
            "¿Alguna vez dijiste 'sí'
          </BigQ>
          <BigQ frame={frame} fps={fps} delay={20}>
            cuando querías decir 'no'?"
          </BigQ>
          <GoldLine frame={frame} fps={fps} delay={50} />
          <Answer frame={frame} fps={fps} delay={70} gold>
            Eso tiene un nombre.
          </Answer>
        </AbsoluteFill>
      </Sequence>

      {/* DESARROLLO (210-540) */}
      <Sequence from={210} durationInFrames={330}>
        <AbsoluteFill style={{ ...globalStyle, gap: 28, padding: '100px 0' }}>
          <Answer frame={frame - 210} fps={fps} delay={0} style={{ fontSize: 60 }}>
            La Máscara
          </Answer>
          <Answer frame={frame - 210} fps={fps} delay={15} gold style={{ fontSize: 52 }}>
            del Complaciente.
          </Answer>
          <GoldLine frame={frame - 210} fps={fps} delay={45} />
          <Body frame={frame - 210} fps={fps} delay={65}>
            No la elegiste conscientemente.
          </Body>
          <Body frame={frame - 210} fps={fps} delay={82}>
            La construiste para que alguien
          </Body>
          <Body frame={frame - 210} fps={fps} delay={96} style={{ color: WHITE, fontWeight: 500 }}>
            importante te amara.
          </Body>
          <Body frame={frame - 210} fps={fps} delay={120} style={{ color: MUTED, fontSize: 26 }}>
            Tal vez a los 6 años.
          </Body>
          <Body frame={frame - 210} fps={fps} delay={136} style={{ color: MUTED, fontSize: 26 }}>
            Tal vez a los 12.
          </Body>
        </AbsoluteFill>
      </Sequence>

      {/* CIERRE CTA (540-750) */}
      <Sequence from={540} durationInFrames={210}>
        <AbsoluteFill style={{ ...globalStyle, gap: 30, padding: '100px 0' }}>
          <Body frame={frame - 540} fps={fps} delay={0} style={{ color: MUTED }}>
            Tu sistema nervioso cree que
          </Body>
          <Body frame={frame - 540} fps={fps} delay={18} style={{ color: WHITE, fontWeight: 500 }}>
            decir "no" es peligroso.
          </Body>
          <GoldLine frame={frame - 540} fps={fps} delay={50} />
          <Answer frame={frame - 540} fps={fps} delay={70} style={{ fontSize: 44 }}>
            No eres demasiado bueno.
          </Answer>
          <Answer frame={frame - 540} fps={fps} delay={90} gold style={{ fontSize: 44 }}>
            Estás en piloto automático.
          </Answer>
          <Body frame={frame - 540} fps={fps} delay={130} style={{
            fontSize: 26, color: GOLD, marginTop: 24,
            border: `1px solid ${GOLD}`, padding: '14px 36px', borderRadius: 4
          }}>
            Comenta MASCARA → test gratuito
          </Body>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
