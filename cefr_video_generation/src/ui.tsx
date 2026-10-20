import { Audio } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  colors,
  easeInOut,
  easeOut,
  fontFamily,
  monoFamily,
  SceneId,
  TRANSITION_FRAMES,
  voice,
} from "./theme";

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

// Scene frame: off-white canvas, oversized ghost index, narration, exit drift.
export const SceneShell: React.FC<{
  id: SceneId;
  index: number;
  children: React.ReactNode;
}> = ({ id, index, children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exitStart = durationInFrames - TRANSITION_FRAMES - 4;
  const num = String(index).padStart(2, "0");

  return (
    <AbsoluteFill style={{ fontFamily, color: colors.ink, background: colors.bg }}>
      <Audio src={staticFile(voice(id).file)} />
      <div
        style={{
          position: "absolute",
          right: -40,
          bottom: 120,
          fontSize: 560,
          fontWeight: 800,
          letterSpacing: -30,
          lineHeight: 1,
          color: colors.ghost,
          translate: `0px ${interpolate(frame, [0, durationInFrames], [40, -40])}px`,
        }}
      >
        {num}
      </div>
      <AbsoluteFill
        style={{
          padding: "250px 90px 300px",
          justifyContent: "center",
          display: "flex",
          flexDirection: "column",
          gap: 44,
          opacity: interpolate(frame, [exitStart, durationInFrames], [1, 0], clamp),
          translate: `0px ${interpolate(frame, [exitStart, durationInFrames], [0, -40], { ...clamp, easing: easeInOut })}px`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Line-mask reveal: content slides up from behind its own baseline.
export const Mask: React.FC<{
  delay?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay = 0, children, style }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ overflow: "hidden", paddingBottom: "0.08em", marginBottom: "-0.08em", ...style }}>
      <div
        style={{
          translate: `0px ${interpolate(frame, [delay, delay + 26], [115, 0], { ...clamp, easing: easeOut })}%`,
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Subtle fade + short rise for supporting copy.
export const FadeUp: React.FC<{
  delay?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay = 0, children, style }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [delay, delay + 18], [0, 1], clamp),
        translate: `0px ${interpolate(frame, [delay, delay + 26], [28, 0], { ...clamp, easing: easeOut })}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// Hairline that draws from the left.
export const Rule: React.FC<{
  delay?: number;
  color?: string;
  thickness?: number;
  duration?: number;
}> = ({ delay = 0, color = colors.line, thickness = 2, duration = 30 }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        height: thickness,
        background: color,
        transformOrigin: "left center",
        scale: `${interpolate(frame, [delay, delay + duration], [0, 1], { ...clamp, easing: easeInOut })} 1`,
      }}
    />
  );
};

export const Headline: React.FC<{
  lines: React.ReactNode[];
  delay?: number;
  size?: number;
  stagger?: number;
}> = ({ lines, delay = 0, size = 96, stagger = 5 }) => (
  <div style={{ fontSize: size, fontWeight: 700, lineHeight: 1.04, letterSpacing: -0.028 * size }}>
    {lines.map((l, i) => (
      <Mask key={i} delay={delay + i * stagger}>
        {l}
      </Mask>
    ))}
  </div>
);

export const Icon: React.FC<{ d: string; size?: number; color?: string }> = ({
  d,
  size = 64,
  color = colors.ink,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

// Frame (relative to scene start) at which the narrator starts saying `phrase`.
// Uses ElevenLabs per-character timestamps; falls back to a character-position estimate.
export const useCue = (id: SceneId) => {
  const { fps } = useVideoConfig();
  const v = voice(id);
  const aligned = v.alignment?.characters === v.text;
  return (phrase: string) => {
    const idx = v.text.indexOf(phrase);
    if (idx < 0) throw new Error(`Cue "${phrase}" not in ${id}`);
    const seconds = aligned
      ? v.alignment.starts[idx]
      : (idx / v.text.length) * v.durationInSeconds;
    return Math.round(seconds * fps);
  };
};

export const icons = {
  listening: "M3 14v-2a9 9 0 0 1 18 0v2M3 14h3v6H4a1 1 0 0 1-1-1v-5zM21 14h-3v6h2a1 1 0 0 0 1-1v-5z",
  reading: "M2 5h7a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H2zM22 5h-7a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h8z",
  writing: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z",
  speaking: "M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3zM19 10v2a7 7 0 0 1-14 0v-2M12 19v3",
  bookmark: "M6 3h12v18l-6-4-6 4z",
  share: "M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M16 6l-4-4-4 4M12 2v13",
};

// "Bo'lim N / 4" eyebrow, oversized English skill name, Uzbek gloss and a line icon.
export const SkillHeader: React.FC<{
  part: number;
  name: string;
  gloss: string;
  icon: string;
}> = ({ part, name, gloss, icon }) => {
  const frame = useCurrentFrame();
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <FadeUp delay={2}>
            <div style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent, letterSpacing: 1 }}>
              BO‘LIM {part} / 4
            </div>
          </FadeUp>
          <Mask delay={6}>
            <div style={{ fontSize: 150, fontWeight: 700, letterSpacing: -6, lineHeight: 1 }}>{name}</div>
          </Mask>
        </div>
        <div
          style={{
            paddingBottom: 20,
            opacity: interpolate(frame, [14, 30], [0, 1], clamp),
            rotate: `${interpolate(frame, [14, 40], [-12, 0], { ...clamp, easing: easeOut })}deg`,
          }}
        >
          <Icon d={icon} size={110} color={colors.accent} />
        </div>
      </div>
      <FadeUp delay={14}>
        <div style={{ fontSize: 44, fontWeight: 500, color: colors.muted, marginTop: 10 }}>{gloss}</div>
      </FadeUp>
    </div>
  );
};

// Big counting number with a label, topped by a hairline.
export const Stat: React.FC<{
  delay: number;
  value: number;
  prefix?: string;
  label: string;
  accent?: boolean;
}> = ({ delay, value, prefix = "", label, accent }) => {
  const frame = useCurrentFrame();
  const n = Math.round(interpolate(frame, [delay, delay + 24], [0, value], { ...clamp, easing: easeOut }));
  return (
    <div style={{ flex: 1 }}>
      <Rule delay={delay - 4} color={colors.ink} />
      <FadeUp delay={delay}>
        <div
          style={{
            fontSize: 150,
            fontWeight: 700,
            letterSpacing: -6,
            lineHeight: 1,
            marginTop: 24,
            fontVariantNumeric: "tabular-nums",
            color: accent ? colors.accent : colors.ink,
          }}
        >
          {prefix}
          {n}
        </div>
        <div style={{ fontFamily: monoFamily, fontSize: 26, color: colors.muted, marginTop: 12, letterSpacing: 1 }}>
          {label.toUpperCase()}
        </div>
      </FadeUp>
    </div>
  );
};

// Numbered row separated by hairlines — used for notes, parts and tables.
export const Row: React.FC<{
  delay: number;
  index: string;
  title: React.ReactNode;
  meta?: React.ReactNode;
  body?: React.ReactNode;
  first?: boolean;
  padding?: number;
}> = ({ delay, index, title, meta, body, first, padding = 30 }) => (
  <div>
    <Rule delay={delay - 4} color={first ? colors.ink : colors.line} />
    <div style={{ display: "flex", gap: 30, padding: `${padding}px 0`, alignItems: "flex-start" }}>
      <FadeUp delay={delay} style={{ width: 70, flexShrink: 0, paddingTop: 10 }}>
        <span style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent }}>{index}</span>
      </FadeUp>
      <div style={{ flex: 1 }}>
        <Mask delay={delay}>
          <div style={{ fontSize: 50, fontWeight: 700, letterSpacing: -1.5, lineHeight: 1.12 }}>{title}</div>
        </Mask>
        {body ? (
          <FadeUp delay={delay + 6}>
            <div style={{ fontSize: 32, color: colors.muted, marginTop: 10, lineHeight: 1.35 }}>{body}</div>
          </FadeUp>
        ) : null}
      </div>
      {meta ? (
        <FadeUp delay={delay + 6} style={{ paddingTop: 12, textAlign: "right" }}>
          <span style={{ fontFamily: monoFamily, fontSize: 28, color: colors.ink }}>{meta}</span>
        </FadeUp>
      ) : null}
    </div>
  </div>
);
