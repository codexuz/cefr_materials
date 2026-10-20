import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { colors, easeInOut, easeOut, fontFamily, monoFamily } from "../theme";
import { FadeUp, Icon, icons, Mask, Rule } from "../ui";
import { usePortrait } from "./Question";
import { cueFrame, FPS, Part, PART_CHIME, partVoice, useMock, voice, VoiceId } from "./timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const partSummary: Record<Part, string> = {
  "1.1": "3 questions · 30 s each",
  "1.2": "2 pictures · 45 s + 30 s + 30 s",
  "2": "1 min preparation · 2 min speaking",
  "3": "1 min preparation · 2 min speaking",
};

const Canvas: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: colors.bg, color: colors.ink, fontFamily }}>{children}</AbsoluteFill>
);

// Portrait: one centred column inside the Reels safe area. Landscape: two absolute columns.
const Column: React.FC<{ children: React.ReactNode; gap?: number }> = ({ children, gap = 0 }) => (
  <div style={{ position: "absolute", left: 90, right: 90, top: 230, bottom: 360, display: "flex", flexDirection: "column", justifyContent: "center", gap }}>
    {children}
  </div>
);

// Each word darkens as the narrator says it (ElevenLabs character timestamps).
const SpokenText: React.FC<{ id: VoiceId; size: number }> = ({ id, size }) => {
  const frame = useCurrentFrame();
  const v = voice(id);
  const words: { w: string; at: number }[] = [];
  const re = /\S+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(v.text))) words.push({ w: m[0], at: Math.round(v.alignment.starts[m.index] * FPS) });
  return (
    <div style={{ fontSize: size, fontWeight: 600, lineHeight: 1.35, letterSpacing: -0.5 }}>
      {words.map((x, i) => (
        <span key={i} style={{ color: frame >= x.at ? colors.ink : "#C9C9C4" }}>
          {x.w}{" "}
        </span>
      ))}
    </div>
  );
};

const PartsList: React.FC<{ compact?: boolean }> = ({ compact }) => {
  const { partTopic } = useMock();
  const parts: Part[] = ["1.1", "1.2", "2", "3"];
  return (
    <div>
      {parts.map((p, i) => (
        <div key={p}>
          <Rule delay={14 + i * 6} color={i === 0 ? colors.ink : colors.line} />
          <div style={{ display: "flex", gap: 28, padding: compact ? "22px 0" : "28px 0" }}>
            <FadeUp delay={16 + i * 6} style={{ width: 90 }}>
              <span style={{ fontFamily: monoFamily, fontSize: 30, color: colors.accent }}>{p}</span>
            </FadeUp>
            <div>
              <Mask delay={16 + i * 6}>
                <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: -1 }}>{partTopic[p]}</div>
              </Mask>
              <FadeUp delay={20 + i * 6}>
                <div style={{ fontSize: 26, color: colors.muted, marginTop: 6 }}>{partSummary[p]}</div>
              </FadeUp>
            </div>
          </div>
        </div>
      ))}
      <Rule delay={40} color={colors.ink} />
    </div>
  );
};

const IntroTitle: React.FC<{ size: number }> = ({ size }) => {
  const { mock } = useMock();
  return (
  <>
    <FadeUp>
      <div style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent, letterSpacing: 2 }}>MULTILEVEL · CEFR</div>
    </FadeUp>
    <div style={{ fontSize: size, fontWeight: 700, letterSpacing: -0.045 * size, lineHeight: 0.95, marginTop: 24 }}>
      <Mask delay={4}>Speaking</Mask>
      <Mask delay={9}>
        <span style={{ color: colors.accent }}>Mock {String(mock.number).padStart(2, "0")}</span>
      </Mask>
    </div>
  </>
  );
};

const IntroNotes: React.FC = () => (
  <>
    <FadeUp delay={cueFrame("intro", "Har bir")} style={{ marginTop: 48 }}>
      <div style={{ fontSize: 38, fontWeight: 500, color: colors.muted, lineHeight: 1.4 }}>
        Har bir savoldan so‘ng tayyorlanish va gapirish vaqti beriladi.
      </div>
    </FadeUp>
    <FadeUp delay={cueFrame("intro", "Signal")} style={{ marginTop: 24, display: "flex", alignItems: "center", gap: 18 }}>
      <div style={{ width: 18, height: 18, borderRadius: 9, background: colors.accent, flexShrink: 0 }} />
      <div style={{ fontSize: 38, fontWeight: 700 }}>Signal eshitilganda gapirishni boshlang</div>
    </FadeUp>
  </>
);

export const IntroCard: React.FC = () => {
  const portrait = usePortrait();
  return (
    <Canvas>
      <Audio src={staticFile(voice("intro").file)} />
      {portrait ? (
        <Column>
          <IntroTitle size={190} />
          <IntroNotes />
          <div style={{ marginTop: 70 }}>
            <PartsList compact />
          </div>
        </Column>
      ) : (
        <>
          <div style={{ position: "absolute", left: 120, top: 0, bottom: 0, width: 860, display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <IntroTitle size={200} />
            <IntroNotes />
          </div>
          <div style={{ position: "absolute", right: 120, top: 0, bottom: 0, width: 640, display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <PartsList />
          </div>
        </>
      )}
    </Canvas>
  );
};

export const PartCard: React.FC<{ part: Part }> = ({ part }) => {
  const frame = useCurrentFrame();
  const portrait = usePortrait();
  const { partTopic } = useMock();
  const id = partVoice[part];
  const chimeAt = Math.ceil(voice(id).durationInSeconds * FPS) + 4;
  const pulse = interpolate(frame, [chimeAt, chimeAt + 24], [0, 1], { ...clamp, easing: easeOut });

  const title = (
    <div>
      <FadeUp>
        <div style={{ fontFamily: monoFamily, fontSize: 30, color: colors.accent, letterSpacing: 2 }}>PART</div>
      </FadeUp>
      <Mask delay={3}>
        <div style={{ fontSize: 300, fontWeight: 700, letterSpacing: -14, lineHeight: 0.95 }}>{part}</div>
      </Mask>
      <FadeUp delay={10}>
        <div style={{ fontSize: 44, fontWeight: 700, letterSpacing: -1, marginTop: 20 }}>{partTopic[part]}</div>
        <div style={{ fontFamily: monoFamily, fontSize: 26, color: colors.muted, marginTop: 14 }}>{partSummary[part].toUpperCase()}</div>
      </FadeUp>
    </div>
  );

  const instructions = (
    <>
      <Rule delay={6} color={colors.ink} />
      <FadeUp delay={6}>
        <SpokenText id={id} size={portrait ? 44 : 46} />
      </FadeUp>
      {part === PART_CHIME ? (
        <div style={{ display: "flex", alignItems: "center", gap: 24, opacity: interpolate(frame, [chimeAt - 10, chimeAt], [0, 1], clamp) }}>
          <div style={{ position: "relative", width: 64, height: 64 }}>
            <div style={{ position: "absolute", inset: 0, borderRadius: 32, border: `3px solid ${colors.accent}`, scale: 1 + pulse * 0.8, opacity: 1 - pulse }} />
            <div style={{ position: "absolute", inset: 16, borderRadius: 16, background: colors.accent }} />
          </div>
          <span style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent, letterSpacing: 2 }}>START SIGNAL</span>
        </div>
      ) : null}
    </>
  );

  return (
    <Canvas>
      <Audio src={staticFile(voice(id).file)} />
      {part === PART_CHIME ? (
        <Sequence from={chimeAt} durationInFrames={30} layout="none">
          <Audio src={staticFile("sfx/start.wav")} />
        </Sequence>
      ) : null}

      {portrait ? (
        <Column gap={48}>
          {title}
          <div style={{ height: 20 }} />
          {instructions}
        </Column>
      ) : (
        <>
          <div style={{ position: "absolute", left: 120, top: 0, bottom: 0, width: 700, display: "flex", flexDirection: "column", justifyContent: "center" }}>
            {title}
          </div>
          <div style={{ position: "absolute", right: 120, top: 0, bottom: 0, width: 880, display: "flex", flexDirection: "column", justifyContent: "center", gap: 48 }}>
            {instructions}
          </div>
        </>
      )}
    </Canvas>
  );
};

const bell = "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0";
const check = "M20 6L9 17l-5-5";

// Button centres (px) — absolute so the cursor can be aimed at them exactly.
const BUTTONS = {
  landscape: { w: 540, sub: [665, 700], save: [1255, 700], cursorFrom: [1500, 1000] },
  portrait: { w: 720, sub: [540, 1080], save: [540, 1240], cursorFrom: [900, 1600] },
};

export const OutroCard: React.FC = () => {
  const frame = useCurrentFrame();
  const portrait = usePortrait();
  const { mock } = useMock();
  const L = portrait ? BUTTONS.portrait : BUTTONS.landscape;
  const subAt = cueFrame("outro", "obuna");
  const saveAt = cueFrame("outro", "saqlab");
  const byeAt = cueFrame("outro", "Keyingi");

  // Cursor path: off-screen → subscribe button → save button (tip lands just right of centre).
  const subClick = subAt + 14;
  const saveClick = saveAt + 14;
  const t = (x: number) => x + 90;
  const cx = interpolate(frame, [subAt - 16, subClick - 2, saveAt - 6, saveClick - 2], [L.cursorFrom[0], t(L.sub[0]), t(L.sub[0]), t(L.save[0])], { ...clamp, easing: easeInOut });
  const cy = interpolate(frame, [subAt - 16, subClick - 2, saveAt - 6, saveClick - 2], [L.cursorFrom[1], L.sub[1] + 10, L.sub[1] + 10, L.save[1] + 10], { ...clamp, easing: easeInOut });
  const press = (at: number) => interpolate(frame, [at, at + 3, at + 9], [1, 0.94, 1], clamp);
  const subscribed = frame >= subClick;
  const saved = frame >= saveClick;

  const button = (center: number[], children: React.ReactNode, style: React.CSSProperties, delay: number, at: number) => (
    <div style={{ position: "absolute", left: center[0] - L.w / 2, top: center[1] - 60, width: L.w, height: 120 }}>
      <FadeUp delay={delay} style={{ height: "100%" }}>
        <div
          style={{
            scale: press(at),
            height: "100%",
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 22,
            borderRadius: 999,
            fontSize: 44,
            fontWeight: 700,
            whiteSpace: "nowrap",
            ...style,
          }}
        >
          {children}
        </div>
      </FadeUp>
    </div>
  );

  return (
    <Canvas>
      <Audio src={staticFile(voice("outro").file)} />
      <Sequence from={subClick} durationInFrames={10} layout="none">
        <Audio src={staticFile("sfx/click.wav")} />
      </Sequence>
      <Sequence from={saveClick} durationInFrames={10} layout="none">
        <Audio src={staticFile("sfx/click.wav")} />
      </Sequence>

      <div style={{ position: "absolute", left: 90, right: 90, top: portrait ? 560 : 200, textAlign: "center" }}>
        <FadeUp>
          <div style={{ fontFamily: monoFamily, fontSize: 28, color: colors.accent, letterSpacing: 2 }}>
            {mock.title.toUpperCase()} · YAKUNLANDI
          </div>
        </FadeUp>
        <div style={{ fontSize: portrait ? 112 : 120, fontWeight: 700, letterSpacing: -5, lineHeight: 1.02, marginTop: 24 }}>
          <Mask delay={4}>Mashq foydali</Mask>
          <Mask delay={9}>bo‘ldimi?</Mask>
        </div>
      </div>

      {button(
        L.sub,
        <>
          <Icon d={subscribed ? check : bell} size={44} color={subscribed ? colors.accent : colors.white} />
          {subscribed ? "Obuna bo‘lindi" : "Obuna bo‘ling"}
        </>,
        { background: subscribed ? colors.ghost : colors.ink, color: subscribed ? colors.ink : colors.white },
        subAt - 20,
        subClick,
      )}
      {button(
        L.save,
        <>
          <svg width={44} height={44} viewBox="0 0 24 24" fill={saved ? colors.accent : "none"} stroke={saved ? colors.accent : colors.ink} strokeWidth={1.5} strokeLinejoin="round">
            <path d={icons.bookmark} />
          </svg>
          {saved ? "Saqlandi" : "Saqlab qo‘ying"}
        </>,
        { border: `3px solid ${saved ? colors.accent : colors.ink}`, color: saved ? colors.accent : colors.ink },
        saveAt - 20,
        saveClick,
      )}

      <div style={{ position: "absolute", left: 90, right: 90, top: portrait ? 1400 : 860, textAlign: "center" }}>
        <FadeUp delay={byeAt}>
          <div style={{ fontSize: 36, color: colors.muted, lineHeight: 1.5 }}>
            Keyingi mock testda ko‘rishguncha
            {portrait ? <br /> : " · "}
            <span style={{ color: colors.ink, fontWeight: 700 }}>Impulse Learning Center</span>
          </div>
        </FadeUp>
      </div>

      {/* Cursor */}
      <svg
        width={54}
        height={54}
        viewBox="0 0 24 24"
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          opacity: interpolate(frame, [subAt - 16, subAt - 8, byeAt, byeAt + 10], [0, 1, 1, 0], clamp),
          scale: (frame >= subClick && frame < subClick + 6) || (frame >= saveClick && frame < saveClick + 6) ? 0.9 : 1,
          filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.18))",
        }}
      >
        <path d="M4 2l16 9-7 2-3 7z" fill={colors.ink} stroke={colors.white} strokeWidth={1.4} strokeLinejoin="round" />
      </svg>
    </Canvas>
  );
};
