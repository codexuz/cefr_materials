import { createContext, useContext } from "react";
import { LOGO_REVEAL_FRAMES } from "../brand/LogoReveal";
import mock1 from "./mock1.json";
import mock2 from "./mock2.json";
import mock3 from "./mock3.json";
import mock4 from "./mock4.json";
import mock5 from "./mock5.json";
import voiceData from "./voice.json";

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

export type MockData = typeof mock1;
export type Question = MockData["questions"][number];
export type Part = "1.1" | "1.2" | "2" | "3";
// The narration is shared by every mock (it never names the mock or its topics).
export type VoiceId = "intro" | "p11" | "p12" | "p2" | "p3" | "outro";

export const mocks = { 1: mock1, 2: mock2, 3: mock3, 4: mock4, 5: mock5 } satisfies Record<number, MockData>;
export type MockId = keyof typeof mocks;

export const voice = (id: VoiceId) => {
  const v = voiceData.find((x) => x.id === id);
  if (!v) throw new Error(`No voice clip ${id}`);
  return v;
};

// Frame within a voice clip at which `phrase` starts being spoken (ElevenLabs alignment).
export const cueFrame = (id: VoiceId, phrase: string) => {
  const v = voice(id);
  const idx = v.text.indexOf(phrase);
  if (idx < 0) throw new Error(`Cue "${phrase}" not in ${id}`);
  return Math.round(v.alignment.starts[idx] * FPS);
};

const sec = (s: number) => Math.ceil(s * FPS);

export const partVoice: Record<Part, VoiceId> = {
  "1.1": "p11",
  "1.2": "p12",
  "2": "p2",
  "3": "p3",
};

// Frames per question phase. Listen = examiner audio + a short beat before the clock starts.
export const phaseFrames = (q: Question) => {
  const listen = sec(q.audioDuration + 0.6);
  const prep = q.prepTime * FPS;
  const speak = q.speakTime * FPS;
  const end = sec(1.6);
  return { listen, prep, speak, end, total: listen + prep + speak + end };
};

// Only Part 1.1's instructions say "when you hear this sound", so the chime is demoed there.
export const PART_CHIME: Part = "1.1";
const partFrames = (part: Part) =>
  sec(voice(partVoice[part]).durationInSeconds) +
  (part === PART_CHIME ? sec(1.2) : 0) +
  sec(0.8);

export type Segment =
  | { kind: "intro"; frames: number }
  | { kind: "part"; part: Part; frames: number }
  | { kind: "question"; q: Question; index: number; frames: number }
  | { kind: "outro"; frames: number }
  | { kind: "logo"; frames: number };

export const buildTimeline = (id: MockId) => {
  const data: MockData = mocks[id];
  const partTopic: Record<Part, string> = {
    "1.1": data.topics.p11Topic,
    "1.2": data.topics.p12Topic,
    "2": data.topics.p2Topic,
    "3": data.topics.p3Topic,
  };
  const segments: Segment[] = [
    { kind: "intro", frames: sec(voice("intro").durationInSeconds + 1) },
  ];
  let current: Part | null = null;
  data.questions.forEach((q, index) => {
    const part = q.part as Part;
    if (part !== current) {
      segments.push({ kind: "part", part, frames: partFrames(part) });
      current = part;
    }
    segments.push({ kind: "question", q, index, frames: phaseFrames(q).total });
  });
  segments.push({
    kind: "outro",
    frames: sec(voice("outro").durationInSeconds + 2),
  });
  segments.push({ kind: "logo", frames: LOGO_REVEAL_FRAMES });
  const totalFrames = segments.reduce((sum, s) => sum + s.frames, 0);
  return { mock: data, partTopic, segments, totalFrames };
};

export type Timeline = ReturnType<typeof buildTimeline>;

// The mock being rendered, provided by <SpeakingMock>.
export const MockContext = createContext<Timeline | null>(null);
export const useMock = () => {
  const t = useContext(MockContext);
  if (!t) throw new Error("useMock() outside <SpeakingMock>");
  return t;
};

export const formatClock = (seconds: number) => {
  const s = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};
