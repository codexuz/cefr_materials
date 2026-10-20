import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, easeInOut, easeOut, monoFamily } from "../theme";
import { FadeUp, Icon, icons, Mask, SceneShell, useCue } from "../ui";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCue("outro");
  const boldAt = cue("dadil");
  const ctaAt = cue("Foydali");
  const saveAt = cue("Videoni");
  const shareAt = cue("ulashing");

  return (
    <SceneShell id="outro" index={9}>
      <div style={{ fontSize: 112, fontWeight: 700, lineHeight: 1.04, letterSpacing: -3.6 }}>
        <Mask delay={2}>Puxta</Mask>
        <Mask delay={7}>tayyorlaning,</Mask>
        <Mask delay={boldAt - 10}>maqsad sari</Mask>
        <Mask delay={boldAt - 5}>
          <span style={{ position: "relative", color: colors.accent }}>
            dadil
            <span
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: 6,
                height: 8,
                background: colors.accent,
                transformOrigin: "left center",
                scale: `${interpolate(frame, [boldAt + 8, boldAt + 32], [0, 1], { ...clamp, easing: easeInOut })} 1`,
              }}
            />
          </span>{" "}
          harakat
        </Mask>
        <Mask delay={boldAt}>qiling.</Mask>
      </div>

      <div
        style={{
          marginTop: 60,
          background: colors.ink,
          color: colors.white,
          borderRadius: 6,
          padding: "44px 44px",
          clipPath: `inset(0 ${interpolate(frame, [ctaAt, ctaAt + 26], [100, 0], { ...clamp, easing: easeOut })}% 0 0)`,
        }}
      >
        <FadeUp delay={ctaAt + 8}>
          <div style={{ fontFamily: monoFamily, fontSize: 24, opacity: 0.6, letterSpacing: 1 }}>
            FOYDALI MASLAHATLAR UCHUN KUZATIB BORING
          </div>
        </FadeUp>
        <Mask delay={ctaAt + 10}>
          <div style={{ fontSize: 68, fontWeight: 700, letterSpacing: -2.5, lineHeight: 1.08, marginTop: 14 }}>
            Impulse Learning Center
          </div>
        </Mask>
      </div>

      <div style={{ display: "flex", gap: 2, background: colors.line, border: `2px solid ${colors.line}` }}>
        {[
          { label: "Saqlab qo‘ying", at: saveAt, d: icons.bookmark },
          { label: "Do‘stlarga ulashing", at: shareAt, d: icons.share },
        ].map((b) => (
          <div key={b.label} style={{ flex: 1, background: colors.bg, padding: "30px 32px" }}>
            <FadeUp delay={b.at} style={{ display: "flex", alignItems: "center", gap: 22 }}>
              <Icon d={b.d} size={48} color={colors.accent} />
              <span style={{ fontSize: 36, fontWeight: 600 }}>{b.label}</span>
            </FadeUp>
          </div>
        ))}
      </div>
    </SceneShell>
  );
};
