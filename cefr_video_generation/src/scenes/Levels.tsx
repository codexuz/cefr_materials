import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, easeOut, monoFamily } from "../theme";
import { FadeUp, Headline, Mask, Rule, SceneShell, useCue } from "../ui";

const MAX = 75;
const levels = [
  { level: "B1", from: 38, to: 50, color: colors.accentSoft, cue: "O‘ttiz sakkizdan", spoken: "Bi bir" },
  { level: "B2", from: 51, to: 64, color: colors.accentMid, cue: "ellik birdan", spoken: "Bi ikki" },
  { level: "C1", from: 65, to: 75, color: colors.accent, cue: "oltmish beshdan", spoken: "Si bir" },
];

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Levels: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCue("levels");
  const scaleAt = cue("O‘ttiz sakkizdan");
  const failAt = cue("O‘ttiz sakkiz balldan past");

  return (
    <SceneShell id="levels" index={8}>
      <Headline size={104} delay={4} lines={["Yakuniy natija", "— o‘rtacha ball"]} />
      <FadeUp delay={16}>
        <div style={{ fontFamily: monoFamily, fontSize: 28, color: colors.muted, whiteSpace: "nowrap" }}>
          (Listening + Reading + Writing + Speaking) ÷ 4
        </div>
      </FadeUp>

      {/* 0–75 score scale */}
      <FadeUp delay={scaleAt} style={{ marginTop: 20 }}>
        <div style={{ position: "relative", height: 90, marginBottom: 14 }}>
          {levels.map((l) => (
            <div
              key={l.level}
              style={{
                position: "absolute",
                left: `${(l.from / MAX) * 100}%`,
                width: `${((l.to - l.from) / MAX) * 100}%`,
                bottom: 0,
                textAlign: "center",
              }}
            >
              <Mask delay={cue(l.spoken)}>
                <span style={{ fontSize: 64, fontWeight: 800, letterSpacing: -2 }}>{l.level}</span>
              </Mask>
            </div>
          ))}
        </div>
        <div style={{ position: "relative", height: 72, background: colors.ghost }}>
          {levels.map((l) => {
            const at = cue(l.cue);
            return (
              <div
                key={l.level}
                style={{
                  position: "absolute",
                  top: 0,
                  bottom: 0,
                  left: `calc(${(l.from / MAX) * 100}% + 2px)`,
                  width: `calc(${((l.to - l.from) / MAX) * 100}% - 4px)`,
                  background: l.color,
                  transformOrigin: "left center",
                  scale: `${interpolate(frame, [at, at + 24], [0, 1], { ...clamp, easing: easeOut })} 1`,
                }}
              />
            );
          })}
        </div>
        <div style={{ position: "relative", height: 50, fontFamily: monoFamily, fontSize: 24, color: colors.muted }}>
          {[0, 38, 75].map((n) => (
            <span key={n} style={{ position: "absolute", top: 14, left: `${(n / MAX) * 100}%`, translate: n === 0 ? "0" : n === MAX ? "-100%" : "-50%" }}>
              {n}
            </span>
          ))}
        </div>
      </FadeUp>

      {/* Score table */}
      <div style={{ marginTop: 10 }}>
        {levels.map((l, i) => {
          const at = cue(l.cue);
          return (
            <div key={l.level}>
              <Rule delay={at - 4} color={i === 0 ? colors.ink : colors.line} />
              <div style={{ display: "flex", alignItems: "center", padding: "28px 0" }}>
                <div style={{ width: 28, height: 28, background: l.color, marginRight: 28, scale: interpolate(frame, [at, at + 10], [0, 1], clamp) }} />
                <Mask delay={at} style={{ flex: 1 }}>
                  <span style={{ fontSize: 56, fontWeight: 700 }}>{l.level}</span>
                </Mask>
                <Mask delay={at + 4}>
                  <span style={{ fontSize: 56, fontWeight: 600, fontVariantNumeric: "tabular-nums", letterSpacing: -1 }}>
                    {l.from}–{l.to}
                    <span style={{ fontSize: 30, color: colors.muted, fontWeight: 500 }}> ball</span>
                  </span>
                </Mask>
              </div>
            </div>
          );
        })}
        <Rule delay={failAt - 4} color={colors.ink} />
        <div style={{ display: "flex", alignItems: "center", padding: "28px 0" }}>
          <div style={{ width: 28, height: 28, border: `2px solid ${colors.muted}`, marginRight: 28, opacity: interpolate(frame, [failAt, failAt + 10], [0, 1], clamp) }} />
          <Mask delay={failAt} style={{ flex: 1 }}>
            <span style={{ fontSize: 40, fontWeight: 600, color: colors.muted }}>38 dan past — sertifikat berilmaydi</span>
          </Mask>
        </div>
      </div>
    </SceneShell>
  );
};
