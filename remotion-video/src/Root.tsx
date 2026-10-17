import { Composition } from "remotion";
import { TeaEssayVideo, TeaEssayVideoProps } from "./TeaEssayVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TeaEssayVideo"
        component={TeaEssayVideo}
        durationInFrames={3600}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
        calculateMetadata={({ props }) => {
          const p = props as unknown as TeaEssayVideoProps;
          return {
            durationInFrames: Number(p?.durationInFrames) || 3600,
            fps: Number(p?.fps) || 30,
            width: 1920,
            height: 1080,
          };
        }}
      />
    </>
  );
};
