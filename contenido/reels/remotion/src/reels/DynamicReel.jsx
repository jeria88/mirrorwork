import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, staticFile } from 'remotion';
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
      <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 14, letterSpacing: '0.25em', textTransform: 'uppercase', color: GOLD, opacity: 0.7 }}>
        Endonautas
      </span>
    </div>
  );
};

const GoldLine = ({ frame, fps, delay = 0 }) => {
  const s = lineGrow(frame, fps, delay);
  return <div style={{ height: 1.5, background: GOLD, opacity: 0.5, ...s, margin: '24px auto' }} />;
};

const DynamicElement = ({ element, frame, fps }) => {
  if (element.type === 'logo') {
    return <Logo frame={frame} fps={fps} delay={element.delay || 0} />;
  }
  if (element.type === 'line') {
    return <GoldLine frame={frame} fps={fps} delay={element.delay || 0} />;
  }

  // Text element
  const anim = fadeUp(frame, fps, element.delay || 0);
  
  // Resolve styles
  const fontStyle = element.font === 'playfair' ? "'Space Grotesk', sans-serif" : "'Plus Jakarta Sans', sans-serif";
  let color = element.color;
  if (color === 'gold') color = GOLD;
  else if (color === 'white') color = WHITE;
  else if (color === 'muted') color = MUTED;
  else if (!color) color = WHITE;
  
  const textStyle = {
    ...anim,
    fontFamily: fontStyle,
    fontSize: element.size || 32,
    fontWeight: element.weight || (element.bold ? 700 : 300),
    fontStyle: element.italic ? 'italic' : 'normal',
    color: color,
    lineHeight: element.lineHeight || (element.font === 'playfair' ? 1.25 : 1.7),
    textAlign: element.align || 'center',
    padding: element.padding || (element.font === 'playfair' ? '0 60px' : '0 80px'),
    ...((element.border) ? {
      border: `1px solid ${GOLD}`,
      padding: '12px 32px',
      borderRadius: 4,
      marginTop: 16,
      display: 'inline-block'
    } : {}),
    ...element.style
  };

  return (
    <div style={textStyle} dangerouslySetInnerHTML={{ __html: element.text || '' }} />
  );
};

export const DynamicReel = ({ reel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!reel || !reel.scenes) {
    return (
      <AbsoluteFill style={globalStyle}>
        <div style={{ color: GOLD }}>Error: No se cargaron los datos del Reel.</div>
      </AbsoluteFill>
    );
  }

  // Fade out at end
  const totalFrames = reel.duration * fps;
  const fadeOutStart = totalFrames - 30;
  const globalOpacity = frame > fadeOutStart
    ? 1 - (frame - fadeOutStart) / 30
    : 1;

  // Decide theme: Even IDs use Theme C (dark galaxy), odd IDs use Theme B (nebula)
  const isThemeC = reel.theme === 'C' || (reel.id && parseInt(reel.id.replace(/\D/g, '')) % 2 === 0);
  const bgImg = isThemeC ? staticFile('dark-galaxy-3-33931033.jpg') : staticFile('nebula-space-dark-3-33931036.jpg');
  const bgFilter = isThemeC 
    ? 'brightness(0.72) contrast(1.12) saturate(0.28)' 
    : 'brightness(0.58) contrast(1.18) saturate(0.48) hue-rotate(15deg)';

  return (
    <AbsoluteFill style={{ ...globalStyle, opacity: globalOpacity, background: '#040810' }}>
      <style>{`
        ${FONTS}
      `}</style>

      {/* Space Background Image */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `url(${bgImg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        filter: bgFilter,
        zIndex: 0
      }} />

      {/* Vignette bottom gradient overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        zIndex: 1,
        background: isThemeC
          ? 'linear-gradient(to top, rgba(3,6,12,0.96) 0%, rgba(3,6,12,0.75) 42%, rgba(3,6,12,0.30) 62%, rgba(3,6,12,0.0) 100%)'
          : 'linear-gradient(to top, rgba(4,6,14,0.96) 0%, rgba(4,6,14,0.75) 35%, rgba(4,6,14,0.30) 55%, rgba(4,6,14,0.0) 100%)'
      }} />

      {/* Bottom radial glow */}
      <div style={{
        position: 'absolute',
        inset: 0,
        zIndex: 2,
        background: isThemeC
          ? 'radial-gradient(ellipse 80% 60% at 50% 110%, rgba(6,48,36,0.48) 0%, transparent 58%)'
          : 'radial-gradient(ellipse 85% 60% at 50% 110%, rgba(8,55,42,0.48) 0%, transparent 58%)',
        pointerEvents: 'none'
      }} />

      {/* Noise texture overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        opacity: isThemeC ? 0.07 : 0.08,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
        zIndex: 3,
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        backgroundSize: '256px'
      }} />

      {/* Sidebar Jade (Theme B only) */}
      {!isThemeC && (
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: 8, // Doubled for vertical 1080x1920 layout
          zIndex: 4,
          background: 'linear-gradient(to bottom, transparent 8%, #7ecfa8 25%, #7ecfa8 75%, transparent 92%)',
          opacity: 0.65
        }} />
      )}

      {reel.scenes.map((scene, idx) => {
        const fromFrame = Math.round(scene.from * fps);
        const durationFrames = Math.round(scene.duration * fps);
        
        return (
          <Sequence key={idx} from={fromFrame} durationInFrames={durationFrames}>
            <AbsoluteFill style={{ 
              ...globalStyle, 
              background: 'transparent',
              gap: scene.gap !== undefined ? scene.gap : 24, 
              padding: scene.padding || '100px 0',
              justifyContent: scene.justifyContent || 'center',
              zIndex: 10
            }}>
              {scene.elements && scene.elements.map((el, elIdx) => (
                <DynamicElement 
                  key={elIdx} 
                  element={el} 
                  frame={frame - fromFrame} 
                  fps={fps} 
                />
              ))}
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
