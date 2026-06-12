import React from 'react';
import { Composition } from 'remotion';
import reelsData from './reels_data.json';
import { DynamicReel } from './reels/DynamicReel.jsx';

const W = 1080;
const H = 1920;
const FPS = 30;

export const RemotionRoot = () => (
  <>
    {reelsData.map(reel => (
      <Composition
        key={reel.id}
        id={reel.id}
        component={DynamicReel}
        width={W}
        height={H}
        fps={FPS}
        durationInFrames={reel.duration * FPS}
        defaultProps={{ reel }}
      />
    ))}
  </>
);
