import { loadFont } from "@remotion/google-fonts/InterTight";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { Easing } from "remotion";
import voiceover from "./voiceover.json";

export const { fontFamily } = loadFont("normal", {
  weights: ["400", "500", "600", "700", "800"],
  subsets: ["latin", "latin-ext"],
});
export const { fontFamily: monoFamily } = loadMono("normal", {
  weights: ["500"],
  subsets: ["latin"],
});

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const TRANSITION_FRAMES = 12;
// Breathing room after each narration clip before the next scene starts.
const TAIL_FRAMES = 15;

export const colors = {
  bg: "#FAFAF7",
  ink: "#0D0D0F",
  muted: "#6E6E73",
  line: "#E3E3DE",
  ghost: "#F0F0EB",
  accent: "#2B50FF",
  accentSoft: "#A9B8FF",
  accentMid: "#6A84FF",
  white: "#FFFFFF",
};

export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

export type SceneId =
  | "hook"
  | "overview"
  | "listening"
  | "reading"
  | "writing"
  | "speaking"
  | "marking"
  | "levels"
  | "outro";

export const voice = (id: SceneId) => {
  const v = voiceover.find((s) => s.id === id);
  if (!v) throw new Error(`No voiceover for ${id}`);
  return v;
};

// Scene length = narration + tail + transition overlap (so the fade never cuts speech).
export const sceneFrames = (id: SceneId) =>
  Math.ceil(voice(id).durationInSeconds * FPS) + TAIL_FRAMES + TRANSITION_FRAMES;
