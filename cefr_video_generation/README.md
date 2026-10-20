# CEFR Video Generation

Remotion project that turns Multilevel (CEFR) exam material into finished videos for
Impulse Learning Center: an Uzbek explainer, and a full Speaking mock-exam simulation.
The visual style throughout is a white background with clean type, hairline rules and a
single blue accent.

## Videos

| Composition | Size | Length | What it is |
|---|---|---:|---|
| `MultilevelVideo` | 1080×1920 | ~3:25 | Uzbek explainer covering the four sections (Listening, Reading, Writing, Speaking), marking and levels; ends on the logo reveal |
| `SpeakingMock1` | 1920×1080 | ~12:32 | Speaking Mock 01 exam simulation for YouTube |
| `SpeakingMock1Reels` | 1080×1920 | ~12:32 | The same simulation laid out for Instagram Reels |
| `LogoReveal`, `LogoRevealReels` | both | 5 s | The Impulse logo end card on its own |

The Speaking mock follows the real exam flow for every question. The examiner audio
plays (**Listen**), a countdown runs for preparation (**Prepare**), a chime signals the
start, and the speaking countdown runs (**Speak**). The question layout depends on the
part:

- **1.1**: the question on its own.
- **1.2**: two photos.
- **2**: a picture with three questions.
- **3**: a statement with For and Against arguments.

English instructions introduce each part, and every word highlights as it is spoken. The
video ends with a subscribe/save screen and the logo reveal.

## Setup

Needs Node 20+, Python 3.13+ and FFmpeg (`ffmpeg`/`ffprobe` on PATH).

```bash
npm install
```

Voice generation uses ElevenLabs. Put the key in `.env`, either in this folder or in
its parent:

```
ELEVENLABS_API=sk_...
```

## Building

The narration is already committed (`public/voiceover/`, `public/speaking-mock1/vo/`),
so only the Speaking mock's question media has to be fetched:

```bash
python scripts/build_speaking_mock.py    # downloads question audio/images, writes src/speaking/questions.json and the sfx
npm run dev                              # Remotion Studio preview
npx remotion render SpeakingMock1 out/speaking-mock-01.mp4
npx remotion render SpeakingMock1Reels out/speaking-mock-01-reels.mp4
npx remotion render MultilevelVideo out/multilevel-video.mp4
```

The released files were loudness-normalised to the usual social-media level afterwards:

```bash
ffmpeg -i out/in.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k out/final.mp4
```

### Regenerating narration

```bash
python scripts/generate_voiceover.py                                  # explainer   (scripts/scenes.json)
python scripts/generate_voiceover.py scripts/speaking_mock1.voice.json  # speaking mock
```

A clip is re-synthesised only when its text, voice or settings change (`--force`
regenerates everything). ElevenLabs bills per character.

Each clip is requested from the `/with-timestamps` endpoint. The per-character timings
are stored in the manifests (`src/voiceover.json`, `src/speaking/voice.json`), and the
scenes use them to reveal each item exactly when its word is spoken.

| Clips | Voice | Model |
|---|---|---|
| Uzbek (explainer, mock intro/outro) | `xDwfBjUEPdIoQekNOXAX`, Jahongir | `eleven_v4`, the only family with Uzbek, alongside `eleven_v4_turbo` |
| English part instructions | `Xb7hH8MSUJpSbSDYk0k2`, Alice | `eleven_v4` |

In the Uzbek text, B1/B2/C1 are spelled "Bi bir / Bi ikki / Si bir" and Writing is spelled
"Rayting". Earlier voices mispronounced these terms. Only the spoken text uses these
spellings; the screen shows the normal forms.

## Layout

```
data/speaking_mock1.json        Mock Stream export (same shape as materials/<type>/*.json)
scripts/
  build_speaking_mock.py        fetch media + questions.json + generated sfx (chimes, click, logo bell)
  generate_voiceover.py         ElevenLabs narration with timestamps
  scenes.json                   explainer narration script
  speaking_mock1.voice.json     mock intro, part instructions and outro
src/
  scenes/                       explainer scenes
  speaking/                     mock simulation: timeline, timer, question layouts, cards
  brand/                        Impulse logo, redrawn as SVG, and the reveal end card
  theme.ts, ui.tsx              palette, fonts, shared motion components
```

`src/speaking/timeline.ts` computes the whole exam timeline from the measured audio
lengths and the prep/speak times in the JSON. To build another mock, add its JSON to
`data/`, point the build script and a new `*.voice.json` at it, and register another
composition.

## Sources

- The marking rules come from the Assessment Agency's criteria for the multi-level format
  (March 2023 revision). Listening and Reading are scored with the Rasch method. In
  Writing, Task 1 carries 33% of the marks and Task 2 carries 67%. Each section is scored
  out of 75.
- The Speaking structure and timings come from the agency's new Speaking format
  (September 2026): parts 1.1, 1.2, 2 and 3.
- Question audio and images belong to Mock Stream and are fetched from the URLs in the
  JSON. They are not stored in this repository.
