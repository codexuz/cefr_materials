import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { colors, fontFamily, monoFamily } from "../theme";
import { FPS, formatClock } from "./timeline";

export type Phase = "listen" | "prep" | "speak" | "end";

export const phaseColor: Record<Phase, string> = {
  listen: colors.ink,
  prep: "#E0912B",
  speak: colors.accent,
  end: colors.muted,
};

const phaseLabel: Record<Phase, string> = {
  listen: "LISTEN",
  prep: "PREPARATION",
  speak: "SPEAK NOW",
  end: "TIME IS UP",
};

// Countdown ring + clock. `elapsed`/`total` are frames within the current phase.
// `compact` = portrait layout: smaller ring with the label and steps beside it.
export const Timer: React.FC<{ phase: Phase; elapsed: number; total: number; compact?: boolean }> = ({
  phase,
  elapsed,
  total,
  compact,
}) => {
  const SIZE = compact ? 330 : 440;
  const STROKE = compact ? 12 : 14;
  const R = (SIZE - STROKE) / 2;
  const C = 2 * Math.PI * R;
  const frame = useCurrentFrame();
  const remaining = total > 0 ? 1 - elapsed / total : 0;
  const fill = phase === "prep" || phase === "speak" ? remaining : phase === "end" ? 0 : 1;
  const color = phaseColor[phase];
  const seconds = (total - elapsed) / FPS;

  return (
    <div style={{ display: "flex", flexDirection: compact ? "row" : "column", alignItems: "center", gap: compact ? 56 : 44, fontFamily }}>
      <div style={{ position: "relative", width: SIZE, height: SIZE, flexShrink: 0 }}>
        <svg width={SIZE} height={SIZE} style={{ rotate: "-90deg" }}>
          <circle cx={SIZE / 2} cy={SIZE / 2} r={R} fill="none" stroke={colors.line} strokeWidth={STROKE} />
          {phase !== "listen" ? (
            <circle
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={R}
              fill="none"
              stroke={color}
              strokeWidth={STROKE}
              strokeDasharray={C}
              strokeDashoffset={C * (1 - fill)}
            />
          ) : null}
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {phase === "listen" ? (
            <Equalizer scale={compact ? 0.8 : 1} />
          ) : (
            <div
              style={{
                fontSize: compact ? 100 : 128,
                fontWeight: 700,
                letterSpacing: -5,
                fontVariantNumeric: "tabular-nums",
                color: phase === "end" ? colors.muted : colors.ink,
              }}
            >
              {phase === "end" ? "0:00" : formatClock(seconds)}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", alignItems: compact ? "flex-start" : "center", gap: compact ? 30 : 44 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, height: 40 }}>
        {phase === "speak" ? (
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: 9,
              background: "#E5484D",
              opacity: interpolate(Math.sin(frame / 6), [-1, 1], [0.35, 1]),
            }}
          />
        ) : null}
        <span style={{ fontFamily: monoFamily, fontSize: 32, letterSpacing: 3, color }}>{phaseLabel[phase]}</span>
      </div>

      <Steps phase={phase} />
      </div>
    </div>
  );
};

// Five bars moving while the examiner speaks.
const Equalizer: React.FC<{ scale: number }> = ({ scale }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14, height: 140, scale }}>
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          style={{
            width: 18,
            borderRadius: 9,
            background: colors.ink,
            height: 30 + 100 * Math.abs(Math.sin(frame / (5 + i * 1.3) + i * 1.7)) * (i === 2 ? 1 : 0.75),
          }}
        />
      ))}
    </div>
  );
};

const steps: { id: Phase; label: string }[] = [
  { id: "listen", label: "Listen" },
  { id: "prep", label: "Prepare" },
  { id: "speak", label: "Speak" },
];

const Steps: React.FC<{ phase: Phase }> = ({ phase }) => {
  const order = ["listen", "prep", "speak", "end"];
  const current = order.indexOf(phase);
  return (
    <div style={{ display: "flex", gap: 10 }}>
      {steps.map((s, i) => {
        const active = s.id === phase;
        const done = i < current;
        return (
          <div
            key={s.id}
            style={{
              width: 140,
              paddingTop: 14,
              borderTop: `4px solid ${active ? phaseColor[s.id] : done ? colors.ink : colors.line}`,
              fontSize: 24,
              fontWeight: 600,
              color: active ? colors.ink : done ? colors.ink : colors.muted,
              opacity: active || done ? 1 : 0.7,
            }}
          >
            {s.label}
          </div>
        );
      })}
    </div>
  );
};

export const usePhase = (f: { listen: number; prep: number; speak: number }) => {
  const frame = useCurrentFrame();
  if (frame < f.listen) return { phase: "listen" as Phase, elapsed: frame, total: f.listen };
  if (frame < f.listen + f.prep) return { phase: "prep" as Phase, elapsed: frame - f.listen, total: f.prep };
  if (frame < f.listen + f.prep + f.speak)
    return { phase: "speak" as Phase, elapsed: frame - f.listen - f.prep, total: f.speak };
  return { phase: "end" as Phase, elapsed: 0, total: 0 };
};
