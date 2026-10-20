import { loadFont } from "@remotion/fonts";
import { Easing, staticFile } from "remotion";
import voiceover from "./voiceover.json";

// Fonts are bundled in public/fonts (variable woff2 files from Google Fonts) so
// rendering never depends on reaching fonts.gstatic.com.
const LATIN =
  "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD";
const LATIN_EXT =
  "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF";

export const fontFamily = "Inter Tight";
export const monoFamily = "JetBrains Mono";

loadFont({
  family: fontFamily,
  url: staticFile("fonts/inter-tight-latin.woff2"),
  weight: "400 800",
  unicodeRange: LATIN,
});
loadFont({
  family: fontFamily,
  url: staticFile("fonts/inter-tight-latin-ext.woff2"),
  weight: "400 800",
  unicodeRange: LATIN_EXT,
});
loadFont({
  family: monoFamily,
  url: staticFile("fonts/jetbrains-mono-latin.woff2"),
  weight: "500",
  unicodeRange: LATIN,
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
