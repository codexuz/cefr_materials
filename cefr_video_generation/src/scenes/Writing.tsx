import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, easeOut, monoFamily } from "../theme";
import { FadeUp, icons, Mask, Rule, SceneShell, SkillHeader, Stat, useCue } from "../ui";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Writing: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCue("writing");
  const t1 = cue("Birinchi topshiriq");
  const t2 = cue("Ikkinchi topshiriq");
  const tipAt = cue("Shuning");

  const grow = (at: number) =>
    interpolate(frame, [at, at + 26], [0, 1], { ...clamp, easing: easeOut });

  return (
    <SceneShell id="writing" index={5}>
      <SkillHeader part={3} name="Writing" gloss="Yozish" icon={icons.writing} />
      <div style={{ display: "flex", gap: 40, marginTop: 10 }}>
        <Stat delay={cue("ikkita")} value={2} label="topshiriq" />
        <Stat delay={cue("Oltmish")} value={60} label="daqiqa" />
      </div>

      {/* Weight split: Task 1 = 33%, Task 2 = 67% */}
      <div style={{ marginTop: 10 }}>
        <div style={{ display: "flex", gap: 6, height: 96 }}>
          <div style={{ width: "33%", background: colors.accentSoft, transformOrigin: "left center", scale: `${grow(t1)} 1`, display: "flex", alignItems: "center", paddingLeft: 24 }}>
            <span style={{ fontSize: 44, fontWeight: 700, opacity: grow(t1 + 10) }}>33%</span>
          </div>
          <div style={{ width: "67%", background: colors.accent, color: colors.white, transformOrigin: "left center", scale: `${grow(t2)} 1`, display: "flex", alignItems: "center", paddingLeft: 24 }}>
            <span style={{ fontSize: 44, fontWeight: 700, opacity: grow(t2 + 10) }}>67%</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, marginTop: 22 }}>
          <FadeUp delay={t1 + 6} style={{ width: "33%" }}>
            <div style={{ fontFamily: monoFamily, fontSize: 24, color: colors.muted }}>TASK 1</div>
            <div style={{ fontSize: 36, fontWeight: 700, marginTop: 6, lineHeight: 1.15 }}>Xat</div>
            <div style={{ fontSize: 26, color: colors.muted, marginTop: 4 }}>vaziyat asosida</div>
          </FadeUp>
          <FadeUp delay={t2 + 6} style={{ width: "67%", paddingLeft: 24 }}>
            <div style={{ fontFamily: monoFamily, fontSize: 24, color: colors.muted }}>TASK 2</div>
            <div style={{ fontSize: 36, fontWeight: 700, marginTop: 6 }}>Esse</div>
            <div style={{ fontSize: 26, color: colors.muted, marginTop: 4 }}>umumiy ballning katta qismi</div>
          </FadeUp>
        </div>
      </div>

      <div style={{ marginTop: 10 }}>
        <Rule delay={tipAt - 4} color={colors.ink} />
        <div style={{ display: "flex", alignItems: "center", gap: 28, paddingTop: 30 }}>
          <FadeUp delay={tipAt}>
            <span style={{ fontFamily: monoFamily, fontSize: 26, color: colors.accent }}>MASLAHAT</span>
          </FadeUp>
          <Mask delay={tipAt}>
            <span style={{ fontSize: 46, fontWeight: 700, letterSpacing: -1 }}>Essega ko‘proq vaqt ajrating</span>
          </Mask>
        </div>
      </div>
    </SceneShell>
  );
};
