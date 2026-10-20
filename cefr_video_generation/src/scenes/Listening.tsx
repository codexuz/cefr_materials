import React from "react";
import { icons, Row, SceneShell, SkillHeader, Stat, useCue } from "../ui";

export const Listening: React.FC = () => {
  const cue = useCue("listening");
  return (
    <SceneShell id="listening" index={3}>
      <SkillHeader part={1} name="Listening" gloss="Tinglab tushunish" icon={icons.listening} />
      <div style={{ display: "flex", gap: 40, marginTop: 20 }}>
        <Stat delay={cue("olti qism")} value={6} label="qism" />
        <Stat delay={cue("o‘ttiz beshta")} value={35} label="savol" accent />
        <Stat delay={cue("taxminan")} value={35} prefix="~" label="daqiqa" />
      </div>
      <div style={{ marginTop: 20 }}>
        <Row delay={cue("Audiolar")} index="01" first title="Audio 2 marta eshittiriladi" />
        <Row delay={cue("javoblarni")} index="02" title="+10 daqiqa" body="Javoblarni varaqaga ko‘chirish uchun" />
      </div>
    </SceneShell>
  );
};
