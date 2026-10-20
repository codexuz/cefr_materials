import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, easeOut, monoFamily } from "../theme";
import { FadeUp, Headline, Mask, Rule, SceneShell, useCue } from "../ui";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Approximate correct answers (out of 35) per level — Listening & Reading.
const answers = [
  { level: "C1", range: "28–35", color: colors.accent, cue: "yigirma sakkizta" },
  { level: "B2", range: "18–27", color: colors.accentMid, cue: "o‘n sakkiztadan" },
  { level: "B1", range: "10–17", color: colors.accentSoft, cue: "o‘ntadan" },
];

export const Marking: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCue("marking");
  const maxAt = cue("Har bir");
  const raschAt = cue("Listening va Reading");
  const expertAt = cue("Rayting va Speaking");
  const max = Math.round(interpolate(frame, [maxAt, maxAt + 30], [0, 75], { ...clamp, easing: easeOut }));

  return (
    <SceneShell id="marking" index={7}>
      <Headline size={104} delay={4} lines={["Baholash", "tizimi"]} />

      <FadeUp delay={maxAt}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 30 }}>
          <div style={{ fontSize: 210, fontWeight: 700, letterSpacing: -10, lineHeight: 0.85, color: colors.accent, fontVariantNumeric: "tabular-nums" }}>
            {max}
          </div>
          <div style={{ fontSize: 36, fontWeight: 600, lineHeight: 1.25, paddingBottom: 8 }}>
            har bir bo‘lim uchun
            <br />
            <span style={{ color: colors.muted, fontWeight: 500 }}>maksimal ball</span>
          </div>
        </div>
      </FadeUp>

      <div>
        <Rule delay={raschAt - 4} color={colors.ink} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "26px 0 8px" }}>
          <Mask delay={raschAt}>
            <span style={{ fontSize: 46, fontWeight: 700, letterSpacing: -1 }}>Listening & Reading</span>
          </Mask>
          <FadeUp delay={raschAt + 6}>
            <span style={{ fontFamily: monoFamily, fontSize: 26, color: colors.accent }}>RASCH METODI</span>
          </FadeUp>
        </div>
        <FadeUp delay={cue("Taxminan")}>
          <div style={{ fontFamily: monoFamily, fontSize: 24, color: colors.muted, padding: "10px 0 6px" }}>
            TO‘G‘RI JAVOBLAR (35 TADAN) · TAXMINAN
          </div>
        </FadeUp>
        <div style={{ display: "flex", gap: 16 }}>
          {answers.map((a) => (
            <FadeUp key={a.level} delay={cue(a.cue)} style={{ flex: 1 }}>
              <div style={{ borderTop: `6px solid ${a.color}`, paddingTop: 16 }}>
                <div style={{ fontSize: 52, fontWeight: 700, letterSpacing: -1.5, fontVariantNumeric: "tabular-nums" }}>{a.range}</div>
                <div style={{ fontSize: 32, fontWeight: 600, color: colors.muted, marginTop: 2 }}>{a.level}</div>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>

      <div>
        <Rule delay={expertAt - 4} color={colors.ink} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", paddingTop: 26 }}>
          <Mask delay={expertAt}>
            <span style={{ fontSize: 46, fontWeight: 700, letterSpacing: -1 }}>Writing & Speaking</span>
          </Mask>
          <FadeUp delay={expertAt + 6}>
            <span style={{ fontFamily: monoFamily, fontSize: 26, color: colors.accent }}>EKSPERTLAR</span>
          </FadeUp>
        </div>
        <FadeUp delay={expertAt + 10}>
          <div style={{ fontSize: 32, color: colors.muted, marginTop: 10 }}>Maxsus baholash mezonlari asosida</div>
        </FadeUp>
      </div>
    </SceneShell>
  );
};
