import React from "react";
import { icons, Row, SceneShell, SkillHeader, Stat, useCue } from "../ui";

export const Reading: React.FC = () => {
  const cue = useCue("reading");
  return (
    <SceneShell id="reading" index={4}>
      <SkillHeader part={2} name="Reading" gloss="O‘qib tushunish" icon={icons.reading} />
      <div style={{ display: "flex", gap: 40, marginTop: 20 }}>
        <Stat delay={cue("besh qism")} value={5} label="qism" />
        <Stat delay={cue("o‘ttiz beshta")} value={35} label="savol" accent />
        <Stat delay={cue("bir soat")} value={60} label="daqiqa" />
      </div>
      <div style={{ marginTop: 20 }}>
        <Row
          delay={cue("Matnni")}
          index="↳"
          first
          title="Skimming & scanning"
          body="Matnni tez ko‘zdan kechirish va kerakli ma’lumotni topish"
        />
      </div>
    </SceneShell>
  );
};
