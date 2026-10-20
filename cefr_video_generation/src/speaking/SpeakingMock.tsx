import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { LogoReveal } from "../brand/LogoReveal";
import { colors } from "../theme";
import { IntroCard, OutroCard, PartCard } from "./Cards";
import { QuestionScene } from "./Question";
import { segments } from "./timeline";

// Hard cuts between segments, like the real computer-based exam; each card animates in on its own.
export const SpeakingMock: React.FC = () => (
  <AbsoluteFill style={{ background: colors.bg }}>
    <Series>
      {segments.map((s, i) => (
        <Series.Sequence
          key={i}
          durationInFrames={s.frames}
          name={s.kind === "question" ? `Q${s.q.number}` : s.kind === "part" ? `Part ${s.part}` : s.kind}
        >
          {s.kind === "intro" ? <IntroCard /> : null}
          {s.kind === "part" ? <PartCard part={s.part} /> : null}
          {s.kind === "question" ? <QuestionScene q={s.q} index={s.index} /> : null}
          {s.kind === "outro" ? <OutroCard /> : null}
          {s.kind === "logo" ? <LogoReveal /> : null}
        </Series.Sequence>
      ))}
    </Series>
  </AbsoluteFill>
);
