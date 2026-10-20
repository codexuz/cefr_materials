import { Audio } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import { colors, fontFamily, monoFamily } from "../theme";
import { FadeUp, Mask, Rule } from "../ui";
import { phaseFrames, Question as Q, mock, partTopic, Part } from "./timeline";
import { Timer, usePhase } from "./Timer";

const CONTENT_WIDTH = 1060;

// Portrait (Reels) keeps content clear of Instagram's top bar and bottom caption/UI zone.
export const usePortrait = () => {
  const { width, height } = useVideoConfig();
  return height > width;
};

export const QuestionScene: React.FC<{ q: Q; index: number }> = ({
  q,
  index,
}) => {
  const f = phaseFrames(q);
  const { phase, elapsed, total } = usePhase(f);
  const part = q.part as Part;
  const speakAt = f.listen + f.prep;
  const portrait = usePortrait();

  return (
    <AbsoluteFill
      style={{ background: colors.bg, color: colors.ink, fontFamily }}
    >
      <Audio src={staticFile(q.audio)} />
      <Sequence from={speakAt} durationInFrames={30} layout="none">
        <Audio src={staticFile("sfx/start.wav")} />
      </Sequence>
      <Sequence from={speakAt + f.speak} durationInFrames={30} layout="none">
        <Audio src={staticFile("sfx/end.wav")} />
      </Sequence>

      <div
        style={{
          position: "absolute",
          display: "flex",
          flexDirection: "column",
          gap: 36,
          ...(portrait
            ? { left: 90, right: 90, top: 230, bottom: 760 }
            : { left: 120, top: 110, bottom: 110, width: CONTENT_WIDTH }),
        }}
      >
        <FadeUp>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              columnGap: 28,
              rowGap: 8,
              alignItems: "baseline",
              fontFamily: monoFamily,
              fontSize: 26,
              letterSpacing: 1,
            }}
          >
            <span style={{ color: colors.accent }}>PART {part}</span>
            <span style={{ color: colors.muted }}>
              QUESTION {index + 1} / {mock.questions.length}
            </span>
            <span style={{ color: colors.muted }}>
              · {partTopic[part].toUpperCase()}
            </span>
          </div>
        </FadeUp>
        {part === "1.1" ? <SimpleQuestion q={q} /> : null}
        {part === "1.2" ? <PictureQuestion q={q} /> : null}
        {part === "2" ? <LongTurn q={q} /> : null}
        {part === "3" ? <Debate q={q} /> : null}
      </div>

      {portrait ? (
        <div
          style={{
            position: "absolute",
            left: 90,
            right: 90,
            bottom: 360,
            height: 340,
            display: "flex",
            alignItems: "center",
          }}
        >
          <Timer phase={phase} elapsed={elapsed} total={total} compact />
        </div>
      ) : (
        <div
          style={{
            position: "absolute",
            right: 120,
            top: 0,
            bottom: 0,
            width: 520,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Timer phase={phase} elapsed={elapsed} total={total} />
        </div>
      )}
    </AbsoluteFill>
  );
};

const Prompt: React.FC<{ text: string; size: number }> = ({ text, size }) => (
  <Mask delay={4}>
    <div
      style={{
        fontSize: size,
        fontWeight: 700,
        letterSpacing: -0.028 * size,
        lineHeight: 1.1,
      }}
    >
      {text}
    </div>
  </Mask>
);

const SimpleQuestion: React.FC<{ q: Q }> = ({ q }) => (
  <div
    style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      gap: 40,
    }}
  >
    <Rule delay={2} color={colors.ink} />
    <Prompt text={q.prompt} size={usePortrait() ? 96 : 92} />
  </div>
);

const PictureQuestion: React.FC<{ q: Q }> = ({ q }) => {
  const portrait = usePortrait();
  return (
    <>
      <Prompt text={q.prompt} size={portrait ? 58 : 64} />
      <div
        style={{ flex: 1, display: "flex", gap: 24, alignItems: "flex-end" }}
      >
        {(q.images ?? []).map((src, i) => (
          <FadeUp key={src} delay={8 + i * 4} style={{ flex: 1 }}>
            <div style={{ position: "relative" }}>
              <Img
                src={staticFile(src)}
                style={{
                  width: "100%",
                  height: portrait ? 600 : 560,
                  objectFit: "cover",
                  borderRadius: 6,
                  display: "block",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  left: 16,
                  top: 16,
                  width: 52,
                  height: 52,
                  borderRadius: 4,
                  background: colors.ink,
                  color: colors.white,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 28,
                  fontWeight: 700,
                }}
              >
                {i + 1}
              </div>
            </div>
          </FadeUp>
        ))}
      </div>
    </>
  );
};

const LongTurn: React.FC<{ q: Q }> = ({ q }) => {
  const portrait = usePortrait();
  return (
    <>
      {q.contextImage ? (
        <FadeUp delay={4}>
          <Img
            src={staticFile(q.contextImage)}
            style={{
              width: "100%",
              height: portrait ? 300 : 380,
              objectFit: "cover",
              borderRadius: 6,
              display: "block",
            }}
          />
        </FadeUp>
      ) : null}
      <div>
        {(q.bulletPoints ?? []).map((b, i) => (
          <div key={b}>
            <Rule
              delay={10 + i * 5}
              color={i === 0 ? colors.ink : colors.line}
            />
            <div style={{ display: "flex", gap: 28, padding: "22px 0" }}>
              <span
                style={{
                  fontFamily: monoFamily,
                  fontSize: 26,
                  color: colors.accent,
                  paddingTop: 8,
                }}
              >
                0{i + 1}
              </span>
              <Mask delay={12 + i * 5}>
                <span
                  style={{
                    fontSize: portrait ? 36 : 40,
                    fontWeight: 600,
                    letterSpacing: -0.8,
                    lineHeight: 1.25,
                  }}
                >
                  {b}
                </span>
              </Mask>
            </div>
          </div>
        ))}
      </div>
    </>
  );
};

const Debate: React.FC<{ q: Q }> = ({ q }) => {
  const portrait = usePortrait();
  const sides = q.debatePoints
    ? [
        { title: "For", points: q.debatePoints.for, color: colors.accent },
        { title: "Against", points: q.debatePoints.against, color: "#E5484D" },
      ]
    : [];
  return (
    <>
      <Prompt text={`“${q.prompt}”`} size={portrait ? 54 : 64} />
      <div style={{ display: "flex", gap: portrait ? 30 : 40, marginTop: 10 }}>
        {sides.map((s, si) => (
          <div key={s.title} style={{ flex: 1 }}>
            <FadeUp delay={12 + si * 6}>
              <div
                style={{
                  fontFamily: monoFamily,
                  fontSize: 26,
                  letterSpacing: 2,
                  color: s.color,
                  marginBottom: 14,
                }}
              >
                {s.title.toUpperCase()}
              </div>
            </FadeUp>
            <Rule delay={12 + si * 6} color={s.color} thickness={4} />
            {s.points.map((p, i) => (
              <FadeUp key={p} delay={18 + si * 6 + i * 4}>
                <div
                  style={{
                    fontSize: portrait ? 27 : 30,
                    fontWeight: 500,
                    lineHeight: 1.35,
                    padding: portrait ? "16px 0" : "20px 0",
                    borderBottom: `2px solid ${colors.line}`,
                  }}
                >
                  {p}
                </div>
              </FadeUp>
            ))}
          </div>
        ))}
      </div>
    </>
  );
};
