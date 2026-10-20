import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, easeInOut, easeOut, fontFamily, monoFamily } from "../theme";
import { Logo } from "./Logo";

export const LOGO_REVEAL_FRAMES = 150;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const overshoot = Easing.bezier(0.34, 1.56, 0.64, 1);

// End card: circle pops, pages draw from the spine, bookmark wipes down, flame lights,
// then the mark slides aside (landscape) or up (portrait) to make room for the wordmark.
export const LogoReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const portrait = height > width;

  const p = (from: number, to: number, easing = easeOut) =>
    interpolate(frame, [from, to], [0, 1], { ...clamp, easing });

  const size = portrait ? 340 : 300;
  const settle = p(56, 84, easeInOut); // mark moves to make room for the wordmark
  const word = (delay: number) => ({
    translate: `0px ${interpolate(frame, [delay, delay + 26], [110, 0], { ...clamp, easing: easeOut })}%`,
  });

  const wordmark = (
    <div style={{ textAlign: portrait ? "center" : "left", color: colors.ink }}>
      <div style={{ overflow: "hidden", paddingBottom: "0.08em" }}>
        <div style={{ ...word(80), fontSize: portrait ? 120 : 112, fontWeight: 800, letterSpacing: -4, lineHeight: 1 }}>Impulse</div>
      </div>
      <div style={{ overflow: "hidden", paddingBottom: "0.08em" }}>
        <div style={{ ...word(86), fontSize: portrait ? 58 : 54, fontWeight: 500, letterSpacing: -1, lineHeight: 1.1, color: colors.muted }}>
          Learning Center
        </div>
      </div>
      <div style={{ overflow: "hidden", marginTop: 22 }}>
        <div style={{ ...word(96), fontFamily: monoFamily, fontSize: 26, letterSpacing: 2, color: colors.accent }}>
          MULTILEVEL · CEFR
        </div>
      </div>
    </div>
  );

  const mark = (
    <div style={{ scale: interpolate(frame, [0, 22], [0.6, 1], { ...clamp, easing: overshoot }), flexShrink: 0 }}>
      <Logo
        size={size}
        circle={p(0, 18, overshoot)}
        book={p(14, 50, easeInOut)}
        spine={p(40, 58)}
        flame={p(46, 72, easeInOut)}
      />
    </div>
  );

  return (
    <AbsoluteFill style={{ background: colors.bg, fontFamily }}>
      <Audio src={staticFile("sfx/logo.wav")} />
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        {portrait ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ translate: `0px ${interpolate(settle, [0, 1], [180, 0])}px` }}>{mark}</div>
            <div style={{ marginTop: 64 }}>{wordmark}</div>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 64 }}>
            <div style={{ translate: `${interpolate(settle, [0, 1], [232, 0])}px 0px` }}>{mark}</div>
            <div>{wordmark}</div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
