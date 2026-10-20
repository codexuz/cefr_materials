import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import React from "react";
import { AbsoluteFill } from "remotion";
import { LOGO_REVEAL_FRAMES, LogoReveal } from "./brand/LogoReveal";
import { Hook } from "./scenes/Hook";
import { Levels } from "./scenes/Levels";
import { Listening } from "./scenes/Listening";
import { Marking } from "./scenes/Marking";
import { Outro } from "./scenes/Outro";
import { Overview } from "./scenes/Overview";
import { Reading } from "./scenes/Reading";
import { Speaking } from "./scenes/Speaking";
import { Writing } from "./scenes/Writing";
import { colors, sceneFrames, SceneId, TRANSITION_FRAMES } from "./theme";

export const scenes: { id: SceneId; name: string; component: React.FC }[] = [
  { id: "hook", name: "Hook", component: Hook },
  { id: "overview", name: "Overview", component: Overview },
  { id: "listening", name: "Listening", component: Listening },
  { id: "reading", name: "Reading", component: Reading },
  { id: "writing", name: "Writing", component: Writing },
  { id: "speaking", name: "Speaking", component: Speaking },
  { id: "marking", name: "Marking", component: Marking },
  { id: "levels", name: "Levels", component: Levels },
  { id: "outro", name: "Outro", component: Outro },
];

// Scenes plus the logo end card, minus one fade overlap per cut.
export const totalFrames =
  scenes.reduce((sum, s) => sum + sceneFrames(s.id), 0) +
  LOGO_REVEAL_FRAMES -
  TRANSITION_FRAMES * scenes.length;

const timing = linearTiming({ durationInFrames: TRANSITION_FRAMES });

export const MultilevelVideo: React.FC = () => (
  <AbsoluteFill style={{ background: colors.bg }}>
    <TransitionSeries>
      {scenes.map((s, i) => (
        <React.Fragment key={s.id}>
          {i > 0 ? <TransitionSeries.Transition presentation={fade()} timing={timing} /> : null}
          <TransitionSeries.Sequence name={s.name} durationInFrames={sceneFrames(s.id)}>
            <s.component />
          </TransitionSeries.Sequence>
        </React.Fragment>
      ))}
      <TransitionSeries.Transition presentation={fade()} timing={timing} />
      <TransitionSeries.Sequence name="Logo" durationInFrames={LOGO_REVEAL_FRAMES}>
        <LogoReveal />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  </AbsoluteFill>
);
