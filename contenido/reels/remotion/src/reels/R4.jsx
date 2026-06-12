import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { fadeUp, lineGrow, GOLD, WHITE, MUTED, FONTS, globalStyle } from '../shared/animations.js';

const DimItem = ({ frame, fps, delay, num, name, desc }) => {
  const anim = fadeUp(frame, fps, delay, { damping: 90, stiffness: 220 });
  return (
    <div style={{ ...anim, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, padding: '0 80px' }}>
      <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, letterSpacing: '0.25em', color: GOLD, textTransform: 'uppercase', opacity: 0.6 }}>
        Dimensión {num}
      </div>
      <div style={{ fontFamily: '"Playfair Display", serif', fontSize: 52, fontWeight: 700, color: WHITE, textAlign: 'center', lineHeight: 1.1 }}>
        {name}
      </div>
      <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 24, fontWeight: 300, color: '#aaaaaa', textAlign: 'center', lineHeight: 1.6 }}>
        {desc}
      </div>
    </div>
  );
};

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1.5, background: GOLD, opacity: 0.4, ...s, margin: '20px auto' }} />;
};

const dims = [
  { num: 1, name: 'Cuerpo', desc: 'Tu historia emocional vive ahí,\nno en tu mente.' },
  { num: 2, name: 'Emoción', desc: 'La información más honesta\nque tienes.' },
  { num: 3, name: 'Identidad', desc: 'La brecha entre quién crees que eres\ny quién eres.' },
  { num: 4, name: 'Sombra', desc: 'Lo que niegas de ti\nte controla más.' },
  { num: 5, name: 'Propósito', desc: 'No se encuentra.\nSe construye.' },
  { num: 6, name: 'Relación', desc: 'Todo conflicto externo\ntiene raíz interna.' },
  { num: 7, name: 'Creencia', desc: 'Lo que crees determina\nlo que te permites vivir.' },
  { num: 8, name: 'Herida', desc: 'No una etiqueta.\nUna puerta de entrada.' },
  { num: 9, name: 'Tiempo', desc: '¿Cuánto tiempo vives\nfuera del presente?' },
  { num: 10, name: 'Máscara', desc: 'La construcción que hiciste\npara sobrevivir.' },
  { num: 11, name: 'Esencia', desc: 'Lo que quedas cuando\ndejas de ser el personaje.' },
  { num: 12, name: 'Trascendencia', desc: 'El sentido que da coherencia\nal viaje entero.' },
];

const FRAMES_PER_DIM = 90; // ~3 seg por dimensión
const INTRO_FRAMES = 90;

export const R4 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = 45 * fps;
  const fadeOutStart = totalFrames - 30;
  const opacity = frame > fadeOutStart ? 1 - (frame - fadeOutStart) / 30 : 1;

  const contentFrame = frame - INTRO_FRAMES;
  const currentDimIndex = contentFrame < 0 ? -1 : Math.floor(contentFrame / FRAMES_PER_DIM);
  const frameInDim = contentFrame < 0 ? 0 : contentFrame % FRAMES_PER_DIM;

  const showClose = frame > INTRO_FRAMES + dims.length * FRAMES_PER_DIM;
  const closeFrame = frame - (INTRO_FRAMES + dims.length * FRAMES_PER_DIM);

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity }}>
      <style>{FONTS}</style>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 70% 50% at 50% 50%, rgba(201,168,76,0.04) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* INTRO */}
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <AbsoluteFill style={{ ...globalStyle, gap: 20, padding: '120px 0' }}>
          <div style={{ ...fadeUp(frame, fps, 0), fontFamily: '"Playfair Display", serif', fontSize: 54, color: WHITE, textAlign: 'center', padding: '0 70px', lineHeight: 1.2 }}>
            ¿Cuántas dimensiones de ti mismo conoces?
          </div>
          <GoldLine frame={frame} fps={fps} delay={35} />
          <div style={{ ...fadeUp(frame, fps, 50), fontFamily: 'Inter, sans-serif', fontSize: 28, color: MUTED, textAlign: 'center' }}>
            La mayoría conoce 2 o 3.
          </div>
          <div style={{ ...fadeUp(frame, fps, 65), fontFamily: '"Playfair Display", serif', fontSize: 64, fontWeight: 700, color: GOLD, textAlign: 'center' }}>
            Hay 12.
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* DIMENSIONES */}
      {dims.map((dim, idx) => {
        const start = INTRO_FRAMES + idx * FRAMES_PER_DIM;
        return (
          <Sequence key={idx} from={start} durationInFrames={FRAMES_PER_DIM}>
            <AbsoluteFill style={{ ...globalStyle, padding: '80px 0', gap: 16 }}>
              <DimItem frame={frame - start} fps={fps} delay={0} {...dim} />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* CIERRE */}
      {showClose && (
        <Sequence from={INTRO_FRAMES + dims.length * FRAMES_PER_DIM} durationInFrames={300}>
          <AbsoluteFill style={{ ...globalStyle, gap: 24, padding: '100px 0' }}>
            <div style={{ ...fadeUp(closeFrame, fps, 0), fontFamily: '"Playfair Display", serif', fontSize: 48, color: WHITE, textAlign: 'center', padding: '0 70px', lineHeight: 1.25 }}>
              Cuando ves el mapa completo,
            </div>
            <div style={{ ...fadeUp(closeFrame, fps, 20), fontFamily: '"Playfair Display", serif', fontSize: 48, color: WHITE, textAlign: 'center', padding: '0 70px', lineHeight: 1.25 }}>
              dejas de luchar contra ti
            </div>
            <div style={{ ...fadeUp(closeFrame, fps, 40), fontFamily: '"Playfair Display", serif', fontStyle: 'italic', fontSize: 52, color: GOLD, textAlign: 'center' }}>
              y empiezas a integrarte.
            </div>
            <GoldLine frame={closeFrame} fps={fps} delay={80} />
            <div style={{ ...fadeUp(closeFrame, fps, 110), fontFamily: 'Inter, sans-serif', fontSize: 26, color: GOLD, textAlign: 'center', border: `1px solid ${GOLD}`, padding: '14px 36px', borderRadius: 4, marginTop: 16 }}>
              Comenta MASCARA → mapa gratis
            </div>
          </AbsoluteFill>
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
