import { Composition, Folder } from "remotion";
import { LOGO_REVEAL_FRAMES, LogoReveal } from "./brand/LogoReveal";
import { MultilevelVideo, scenes, totalFrames } from "./MultilevelVideo";
import * as speaking from "./speaking/timeline";
import { SpeakingMock } from "./speaking/SpeakingMock";
import { FPS, HEIGHT, sceneFrames, WIDTH } from "./theme";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MultilevelVideo"
        component={MultilevelVideo}
        durationInFrames={totalFrames}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      {([1, 2] as const).map((id) => {
        const { totalFrames: frames } = speaking.buildTimeline(id);
        return (
          <Folder key={id} name={`Speaking-Mock-${id}`}>
            <Composition
              id={`SpeakingMock${id}`}
              component={SpeakingMock}
              defaultProps={{ mockId: id }}
              durationInFrames={frames}
              fps={speaking.FPS}
              width={speaking.WIDTH}
              height={speaking.HEIGHT}
            />
            <Composition
              id={`SpeakingMock${id}Reels`}
              component={SpeakingMock}
              defaultProps={{ mockId: id }}
              durationInFrames={frames}
              fps={speaking.FPS}
              width={speaking.HEIGHT}
              height={speaking.WIDTH}
            />
          </Folder>
        );
      })}
      <Folder name="Brand">
        <Composition id="LogoReveal" component={LogoReveal} durationInFrames={LOGO_REVEAL_FRAMES} fps={30} width={1920} height={1080} />
        <Composition id="LogoRevealReels" component={LogoReveal} durationInFrames={LOGO_REVEAL_FRAMES} fps={30} width={1080} height={1920} />
      </Folder>
      <Folder name="Scenes">
        {scenes.map((s) => (
          <Composition
            key={s.id}
            id={s.name}
            component={s.component}
            durationInFrames={sceneFrames(s.id)}
            fps={FPS}
            width={WIDTH}
            height={HEIGHT}
          />
        ))}
      </Folder>
    </>
  );
};
