import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, easeInOut, monoFamily } from "../theme";
import { FadeUp, Headline, Icon, icons, Mask, Rule, SceneShell, useCue } from "../ui";

const skills = [
  { name: "Listening", uz: "Tinglab tushunish", icon: icons.listening, cue: "Listening" },
  { name: "Reading", uz: "O‘qib tushunish", icon: icons.reading, cue: "Reading" },
  { name: "Writing", uz: "Yozish", icon: icons.writing, cue: "Rayting" },
  { name: "Speaking", uz: "Gapirish", icon: icons.speaking, cue: "Speaking" },
];

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Overview: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCue("overview");
  const gridAt = cue("U to‘rtta");
  const levelsAt = cue("Natijaga");
  const validAt = cue("ikki yil");

  return (
    <SceneShell id="overview" index={2}>
      <Headline size={104} delay={4} lines={["CEFR asosidagi", "milliy imtihon"]} />
      <FadeUp delay={14}>
        <div style={{ fontSize: 36, fontWeight: 500, color: colors.muted, lineHeight: 1.35 }}>
          Bilim va malakalarni baholash agentligi tomonidan o‘tkaziladi
        </div>
      </FadeUp>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 2,
          background: colors.line,
          border: `2px solid ${colors.line}`,
          opacity: interpolate(frame, [gridAt, gridAt + 12], [0, 1], clamp),
        }}
      >
        {skills.map((s) => {
          const at = cue(s.cue);
          return (
            <div
              key={s.name}
              style={{ position: "relative", background: colors.bg, padding: "32px 32px 36px", height: 230, display: "flex", flexDirection: "column", justifyContent: "space-between" }}
            >
              <FadeUp delay={at}>
                <Icon d={s.icon} size={56} />
              </FadeUp>
              <div>
                <Mask delay={at}>
                  <div style={{ fontSize: 50, fontWeight: 700, letterSpacing: -1.5 }}>{s.name}</div>
                </Mask>
                <FadeUp delay={at + 6}>
                  <div style={{ fontSize: 28, color: colors.muted, marginTop: 4 }}>{s.uz}</div>
                </FadeUp>
              </div>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: 6,
                  background: colors.accent,
                  transformOrigin: "left center",
                  scale: `${interpolate(frame, [at, at + 20], [0, 1], { ...clamp, easing: easeInOut })} 1`,
                }}
              />
            </div>
          );
        })}
      </div>

      <div>
        <Rule delay={levelsAt - 4} color={colors.ink} />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 30 }}>
          <div style={{ display: "flex", gap: 16 }}>
            {["B1", "B2", "C1"].map((l, i) => (
              <FadeUp key={l} delay={cue(["Bi bir", "Bi ikki", "Si bir"][i])}>
                <div style={{ fontSize: 48, fontWeight: 700, border: `2px solid ${colors.ink}`, borderRadius: 4, padding: "8px 22px" }}>{l}</div>
              </FadeUp>
            ))}
          </div>
          <FadeUp delay={validAt} style={{ textAlign: "right" }}>
            <div style={{ fontSize: 64, fontWeight: 700, letterSpacing: -2, lineHeight: 1 }}>2 yil</div>
            <div style={{ fontFamily: monoFamily, fontSize: 24, color: colors.muted, marginTop: 6 }}>AMAL QILADI</div>
          </FadeUp>
        </div>
      </div>
    </SceneShell>
  );
};
