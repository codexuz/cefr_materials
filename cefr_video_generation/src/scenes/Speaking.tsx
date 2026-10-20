import React from "react";
import { colors } from "../theme";
import { icons, Row, Rule, SceneShell, SkillHeader, useCue } from "../ui";

// New speaking format (Bilim va malakalarni baholash agentligi, 2026).
export const Speaking: React.FC = () => {
  const cue = useCue("speaking");
  const parts = [
    { index: "1.1", title: "O‘zingiz haqingizda", meta: "3 savol", at: cue("avval") },
    { index: "1.2", title: "Ikkita rasm asosida", meta: "3 savol", at: cue("keyin ikkita") },
    { index: "2", title: "Bitta mavzu", meta: "3 savol · 2 daq", at: cue("Ikkinchi qismda") },
    { index: "3", title: "Fikrning ikki tomoni", meta: "2 daq", at: cue("Uchinchi qismda") },
  ];
  const prepAt = cue("tayyorlanish");

  return (
    <SceneShell id="speaking" index={6}>
      <SkillHeader part={4} name="Speaking" gloss="Gapirish" icon={icons.speaking} />
      <div style={{ marginTop: 20 }}>
        {parts.map((p, i) => (
          <Row
            key={p.index}
            delay={p.at}
            index={p.index}
            first={i === 0}
            padding={26}
            title={p.title}
            meta={p.meta}
            body={i >= 2 ? <span style={{ color: colors.accent, opacity: 1 }}>+ 1 daqiqa tayyorgarlik</span> : undefined}
          />
        ))}
        <Rule delay={prepAt} color={colors.ink} />
      </div>
    </SceneShell>
  );
};
