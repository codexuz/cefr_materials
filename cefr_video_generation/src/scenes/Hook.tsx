import React from "react";
import { colors, monoFamily } from "../theme";
import { FadeUp, Headline, Icon, icons, Mask, Rule, SceneShell, useCue } from "../ui";

const skills = [
  { name: "Listening", icon: icons.listening },
  { name: "Reading", icon: icons.reading },
  { name: "Writing", icon: icons.writing },
  { name: "Speaking", icon: icons.speaking },
];

export const Hook: React.FC = () => {
  const cue = useCue("hook");
  const partsAt = cue("to‘rtta bo‘limi");
  const markAt = cue("baholash tizimi");

  return (
    <SceneShell id="hook" index={1}>
      <Headline
        size={128}
        delay={4}
        lines={[<span key="m" style={{ color: colors.accent }}>Multilevel</span>, "imtihoniga", "tayyormisiz?"]}
      />
      <FadeUp delay={cue("Unda")}>
        <div style={{ fontSize: 46, fontWeight: 500, color: colors.muted }}>Unda bu video aynan siz uchun.</div>
      </FadeUp>

      <div style={{ marginTop: 120 }}>
        <FadeUp delay={partsAt - 4}>
          <div style={{ fontFamily: monoFamily, fontSize: 26, color: colors.muted, letterSpacing: 1, marginBottom: 20 }}>
            4 BO‘LIM
          </div>
        </FadeUp>
        <Rule delay={partsAt - 4} color={colors.ink} />
        <div style={{ display: "flex" }}>
          {skills.map((s, i) => (
            <FadeUp
              key={s.name}
              delay={partsAt + i * 4}
              style={{ flex: 1, padding: "28px 0", borderRight: i < 3 ? `2px solid ${colors.line}` : undefined, textAlign: "center" }}
            >
              <Icon d={s.icon} size={52} />
              <div style={{ fontSize: 30, fontWeight: 600, marginTop: 12 }}>{s.name}</div>
            </FadeUp>
          ))}
        </div>
        <Rule delay={markAt - 6} color={colors.line} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 28 }}>
          <Mask delay={markAt}>
            <span style={{ fontSize: 52, fontWeight: 700, letterSpacing: -1.5 }}>+ Baholash tizimi</span>
          </Mask>
          <FadeUp delay={markAt + 6}>
            <span style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent }}>B1 · B2 · C1</span>
          </FadeUp>
        </div>
      </div>
    </SceneShell>
  );
};
