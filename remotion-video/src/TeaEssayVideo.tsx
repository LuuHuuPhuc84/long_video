import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  interpolate,
  Easing,
} from "remotion";

export interface EssaySceneItem {
  scene: number;
  chapter?: string;
  tag?: string;
  text: string;
  highlight: string;
  image?: string;
  video?: string;
  media_type?: "video" | "image";
  is_text_card?: boolean;
  is_end_screen?: boolean;
  startFrame: number;
  durationInFrames: number;
}

export interface TeaEssayVideoProps {
  id?: string;
  channel?: string;
  slogan?: string;
  title?: string;
  subtitle?: string;
  impactHook?: string;
  fps?: number;
  width?: number;
  height?: number;
  durationInFrames?: number;
  audioFile?: string;
  stylePreset?: "zen_amber" | "clean_natural" | "vintage_warm" | "film_contrast" | string;
  scenes?: EssaySceneItem[];
}

export interface StylePresetConfig {
  filter: string;
  washColor: string;
  vignette: string;
}

export const STYLE_PRESETS: Record<string, StylePresetConfig> = {
  zen_amber: {
    filter: "none",
    washColor: "transparent",
    vignette: "none",
  },
  clean_natural: {
    filter: "none",
    washColor: "transparent",
    vignette: "none",
  },
  vintage_warm: {
    filter: "contrast(1.04) saturate(0.88) sepia(0.12)",
    washColor: "rgba(224, 169, 109, 0.06)",
    vignette: "radial-gradient(circle at 50% 50%, transparent 64%, rgba(0, 0, 0, 0.28) 100%)",
  },
  film_contrast: {
    filter: "contrast(1.06) saturate(0.95)",
    washColor: "rgba(10, 15, 30, 0.03)",
    vignette: "radial-gradient(circle at 50% 50%, transparent 70%, rgba(0, 0, 0, 0.20) 100%)",
  },
};

export const TeaEssayVideo: React.FC<TeaEssayVideoProps> = (props) => {
  const channel = props.channel || "NỬA CHÉN TRÀ";
  const slogan = props.slogan || "Nhìn sâu để sống nhẹ";
  const title =
    props.title || "VÌ SAO CHÚNG TA DỄ NỔI NÓNG VỚI NGƯỜI THÂN NHẤT?";
  const subtitle =
    props.subtitle || "BÍ MẬT TÂM LÝ HỌC & NGHỆ THUẬT LÀM CHỦ CẢM XÚC GIA ĐÌNH";
  const audioFile = props.audioFile || "voiceover_essay_ep01.wav";
  const scenes = props.scenes || [];
  const durationInFrames = props.durationInFrames || 3600;
  const stylePresetKey = props.stylePreset || "zen_amber";
  const preset = STYLE_PRESETS[stylePresetKey] || STYLE_PRESETS.zen_amber;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#08090c",
        fontFamily:
          "'Montserrat', 'SF Pro Display', 'Segoe UI', -apple-system, sans-serif",
        color: "#ffffff",
        overflow: "hidden",
      }}
    >
      {/* 1. Cinematic B-Roll 16:9: Hòa tan mượt mà (Cross-fade), triệt tiêu hoàn toàn màn hình đen */}
      {scenes.map((scene: EssaySceneItem, index: number) => {
        const nextScene = scenes[index + 1];
        // Kéo dài ảnh phủ kín cả khoảng lặng âm thanh và gối đầu 15 frames vào cảnh sau
        const bgDuration = nextScene
          ? Math.max(scene.durationInFrames, nextScene.startFrame - scene.startFrame + 15)
          : scene.durationInFrames;

        return (
          <Sequence
            key={`bg-${scene.scene}`}
            from={scene.startFrame}
            durationInFrames={bgDuration}
          >
            <CinematicSceneBackground
              scene={scene}
              durationInFrames={bgDuration}
              index={index}
              filter={preset.filter}
            />
          </Sequence>
        );
      })}

      {/* 2. Lớp phủ mềm mại: Theo Preset Zen Amber / Clean Natural */}
      <SoftCinemaOverlay
        washColor={preset.washColor}
        vignette={preset.vignette}
      />

      {/* 3. Audio (Single Pre-mixed Voiceover + Ambient BGM) */}
      <Audio src={staticFile(audioFile)} volume={1.0} />

      {/* 4. Top-Left Branding Badge: NỬA CHÉN TRÀ */}
      <TopBrandBadge channel={channel} slogan={slogan} />

      {/* 5. Top-Right Dynamic Chapter Indicator */}
      {scenes.map((scene: EssaySceneItem) => (
        <Sequence
          key={`chap-${scene.scene}`}
          from={scene.startFrame}
          durationInFrames={scene.durationInFrames}
        >
          <ChapterIndicator
            chapter={scene.chapter || ""}
            sceneIndex={scene.scene}
            totalScenes={scenes.length}
          />
        </Sequence>
      ))}

      {/* 6. Floating Topic Header: Xuất hiện trang trọng ở 6s đầu mà không che B-roll */}
      <Sequence from={0} durationInFrames={180}>
        <FloatingTopicHeader title={title} subtitle={subtitle} />
      </Sequence>

      {/* 6b. Impact Center Typography (3 giây đầu tiên - Golden Retention Hook) */}
      <Sequence from={0} durationInFrames={90}>
        <ImpactCenterTypography text={props.impactHook || "AI ĐANG ĐIỀU KHIỂN TÂM TRÍ BẠN?"} />
      </Sequence>

      {/* 6c. Center Hero Text Card cho các cảnh THẺ CHỮ */}
      {scenes.map((scene: EssaySceneItem) => {
        if (!scene.is_text_card) return null;
        return (
          <Sequence
            key={`hero-card-${scene.scene}`}
            from={scene.startFrame}
            durationInFrames={scene.durationInFrames}
          >
            <CenterHeroTextCard
              highlight={scene.highlight}
              chapter={scene.chapter}
              tag={scene.tag}
              durationInFrames={scene.durationInFrames}
            />
          </Sequence>
        );
      })}

      {/* 7. Subtitle hiển thị cuốn chiếu từng câu ngắn, chữ to rõ (42px) */}
      {scenes.map((scene: EssaySceneItem) => (
        <Sequence
          key={`text-${scene.scene}`}
          from={scene.startFrame}
          durationInFrames={scene.durationInFrames}
        >
          <PacedSentenceCaption scene={scene} />
        </Sequence>
      ))}

      {/* 7b. Interactive End Screen 15s cho cảnh kết thúc có is_end_screen */}
      {scenes.map((scene: EssaySceneItem) => {
        if (!scene.is_end_screen) return null;
        return (
          <Sequence
            key={`endscreen-${scene.scene}`}
            from={scene.startFrame}
            durationInFrames={scene.durationInFrames}
          >
            <InteractiveEndScreen channel={channel} slogan={slogan} />
          </Sequence>
        );
      })}

      {/* 8. End Card (120 frames cuối ~ 4 giây nếu không có is_end_screen) */}
      {durationInFrames > 150 && !scenes.some((s) => s.is_end_screen) && (
        <Sequence from={durationInFrames - 120} durationInFrames={120}>
          <EndChannelCard channel={channel} slogan={slogan} />
        </Sequence>
      )}

      {/* 9. Minimalist Golden Progress Bar */}
      <ProgressBar totalFrames={durationInFrames} />
    </AbsoluteFill>
  );
};

// Hiển thị B-roll: Hỗ trợ cả Video Footage (.mp4) chuyển động thực tế và Ảnh tĩnh Ken Burns
const CinematicSceneBackground: React.FC<{
  scene: EssaySceneItem;
  durationInFrames: number;
  index: number;
  filter?: string;
}> = ({ scene, durationInFrames, index, filter }) => {
  const frame = useCurrentFrame();
  const isEven = index % 2 === 0;

  // Hiệu ứng hòa tan mượt mà (Cross-fade / Dissolve) 15 frames đầu mỗi cảnh (trừ cảnh đầu tiên)
  const fadeIn =
    index === 0
      ? 1
      : interpolate(frame, [0, 15], [0, 1], {
          extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.quad),
        });

  if (scene.video) {
    return (
      <AbsoluteFill style={{ overflow: "hidden", opacity: fadeIn }}>
        <OffthreadVideo
          src={staticFile(scene.video)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: filter || "none",
          }}
          muted
        />
      </AbsoluteFill>
    );
  }

  const scale = interpolate(
    frame,
    [0, durationInFrames],
    isEven ? [1.02, 1.13] : [1.13, 1.03],
    { extrapolateRight: "clamp", easing: Easing.bezier(0.25, 0.1, 0.25, 1) }
  );

  const translateX = interpolate(
    frame,
    [0, durationInFrames],
    isEven ? [-10, 10] : [10, -10],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity: fadeIn }}>
      <Img
        src={staticFile(scene.image || "")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${translateX}px, 0px)`,
          filter: filter || "none",
        }}
      />
    </AbsoluteFill>
  );
};

// Impact Center Typography: Chữ điểm nhấn trung tâm ở 3s đầu tiên (Golden Retention Hook)
const ImpactCenterTypography: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12, 70, 85], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(frame, [0, 12, 85], [1.08, 1.0, 0.98], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 55,
        opacity,
        transform: `scale(${scale})`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          padding: "18px 42px",
          background: "rgba(10, 13, 20, 0.88)",
          borderRadius: 18,
          border: "1.5px solid rgba(224, 169, 109, 0.65)",
          boxShadow:
            "0 15px 45px rgba(0, 0, 0, 0.8), 0 0 30px rgba(224, 169, 109, 0.25)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
          backdropFilter: "blur(8px)",
        }}
      >
        <div
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: "#e0a96d",
            letterSpacing: 3.5,
            textTransform: "uppercase",
          }}
        >
          ✦ CÂU HỎI TỰ THẤU HIỂU ✦
        </div>
        <div
          style={{
            fontSize: 42,
            fontWeight: 800,
            color: "#ffffff",
            letterSpacing: 1.5,
            textAlign: "center",
            textShadow: "0 4px 20px rgba(0,0,0,0.9)",
          }}
        >
          {text}
        </div>
      </div>
    </div>
  );
};


// QUY CHUẨN TÔNG MÀU THEO PRESET (ZEN AMBER / CLEAN NATURAL / VINTAGE...):
const SoftCinemaOverlay: React.FC<{
  washColor?: string;
  vignette?: string;
}> = ({ washColor, vignette }) => {
  if (!washColor && !vignette) return null;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 4 }}>
      {washColor && washColor !== "transparent" && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: washColor,
            mixBlendMode: "color",
          }}
        />
      )}
      {vignette && vignette !== "none" && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: vignette,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

// Top-Left Branding Badge (Watermark đài truyền hình tinh giản, sắc nét)
const TopBrandBadge: React.FC<{ channel: string; slogan: string }> = ({
  channel,
}) => {
  return (
    <div
      style={{
        position: "absolute",
        top: 36,
        left: 48,
        display: "flex",
        alignItems: "center",
        gap: 14,
        background: "rgba(12, 14, 20, 0.82)",
        backdropFilter: "blur(14px)",
        padding: "10px 24px",
        borderRadius: 999,
        border: "1.5px solid rgba(224, 169, 109, 0.45)",
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        zIndex: 50,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          background: "linear-gradient(135deg, #e0a96d 0%, #b87b42 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 2px 10px rgba(224, 169, 109, 0.5)",
        }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#111"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
          <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
          <line x1="6" y1="2" x2="6" y2="4"></line>
          <line x1="10" y1="2" x2="10" y2="4"></line>
          <line x1="14" y1="2" x2="14" y2="4"></line>
        </svg>
      </div>
      <span
        style={{
          fontSize: 22,
          fontWeight: 800,
          letterSpacing: 2.5,
          color: "#ffffff",
          textTransform: "uppercase",
          textShadow: "0 2px 8px rgba(0,0,0,0.85)",
          WebkitFontSmoothing: "antialiased",
        }}
      >
        {channel}
      </span>
    </div>
  );
};

// Top-Right Chapter Indicator: Đã bỏ để tối ưu không gian điện ảnh thoáng đãng
const ChapterIndicator: React.FC<{
  chapter: string;
  sceneIndex: number;
  totalScenes: number;
}> = () => {
  return null;
};

// Floating Topic Header (Hiển thị trang trọng 6s đầu, không che khung hình)
const FloatingTopicHeader: React.FC<{ title: string; subtitle: string }> = ({
  title,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15, 155, 180], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, 15, 155, 180], [-12, 0, 0, -12], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 110,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        zIndex: 48,
        opacity,
        transform: `translateY(${translateY}px)`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: "rgba(10, 13, 20, 0.85)",
          backdropFilter: "blur(18px)",
          border: "1.5px solid rgba(224, 169, 109, 0.55)",
          boxShadow:
            "0 12px 35px rgba(0, 0, 0, 0.65), 0 0 25px rgba(224, 169, 109, 0.2)",
          borderRadius: 40,
          padding: "12px 36px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: "#e0a96d",
            boxShadow: "0 0 10px #e0a96d",
          }}
        />
        <span
          style={{
            color: "#ffffff",
            fontSize: 22,
            fontWeight: 800,
            letterSpacing: 1.5,
            textTransform: "uppercase",
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.8)",
          }}
        >
          {title}
        </span>
      </div>
    </div>
  );
};

// Component hiển thị chữ nhảy nảy theo từng từ cho Long Video (Video Essay 16:9)
// Tông màu vàng cát hổ phách cổ điển (#e0a96d) sang trọng, thanh lịch
const LongVideoKaraokeText: React.FC<{
  text: string;
  durationInFrames: number;
  localFrame: number;
}> = ({ text, durationInFrames, localFrame }) => {
  const words = useMemo(() => {
    // Triệt tiêu hoàn toàn dấu "/" và ký tự ngắt nhịp trong văn bản hiển thị
    const cleanStr = text.replace(/[\/]/g, " ").replace(/,,/g, ",").replace(/\s{2,}/g, " ").trim();
    const rawWords = cleanStr.split(/\s+/).filter((w) => w.length > 0 && w !== "/");
    if (rawWords.length === 0) return [];

    // Phân bổ trọng số theo độ dài từ và dấu câu
    const weights = rawWords.map((w) => {
      let weight = Math.max(w.length, 2);
      if (/[.,!?;:…]$/.test(w)) {
        weight += 3;
      }
      return weight;
    });

    const totalWeight = weights.reduce((acc, val) => acc + val, 0);

    let curr = 0;
    return rawWords.map((word, i) => {
      const dur = Math.max(
        3,
        Math.round((weights[i] / totalWeight) * durationInFrames)
      );
      const start = curr;
      const end = i === rawWords.length - 1 ? durationInFrames : curr + dur;
      curr = end;
      return { word, start, end };
    });
  }, [text, durationInFrames]);

  return (
    <div
      style={{
        fontSize: 42,
        lineHeight: 1.5,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        rowGap: 8,
        columnGap: 10,
        margin: 0,
      }}
    >
      {words.map((item, idx) => {
        const isCurrent = localFrame >= item.start && localFrame < item.end;
        const isPast = localFrame >= item.end;

        let scale = 1.0;
        let color = "rgba(255, 255, 255, 0.52)";
        let fontWeight = 600;
        let textShadow = "0 2px 8px rgba(0,0,0,0.85)";

        if (isCurrent) {
          const progress =
            (localFrame - item.start) / Math.max(item.end - item.start, 1);
          // Nảy nhẹ 1.15x sang trọng cho video dài 16:9
          scale = interpolate(progress, [0, 0.25, 1], [1.05, 1.16, 1.08], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          color = "#e0a96d"; // Vàng cát hổ phách Nửa Chén Trà
          fontWeight = 800;
          textShadow =
            "0 0 25px rgba(224, 169, 109, 0.85), 0 0 10px rgba(224, 169, 109, 0.6), 0 3px 10px rgba(0,0,0,0.95)";
        } else if (isPast) {
          color = "#ffffff";
          fontWeight = 600;
        }

        return (
          <span
            key={idx}
            style={{
              display: "inline-block",
              transform: `scale(${scale})`,
              transformOrigin: "center center",
              color,
              fontWeight,
              textShadow,
              transition: "color 0.1s ease",
            }}
          >
            {item.word}
          </span>
        );
      })}
    </div>
  );
};

// CƠ CHẾ PHỤ ĐỀ NHỊP ĐIỆU (Paced Sentence Captions) KẾT HỢP KARAOKE WORD BOUNCE:
// Tự động ngắt đoạn văn thành các câu ngắn và hiển thị theo nhịp đọc, chữ to (42px) cực kỳ dễ đọc
const PacedSentenceCaption: React.FC<{ scene: EssaySceneItem }> = ({
  scene,
}) => {
  const frame = useCurrentFrame();

  // Tách văn bản thành từng câu ngắn tự nhiên, triệt tiêu hoàn toàn dấu "/"
  const sentences = useMemo(() => {
    const raw = (scene.text || "").replace(/,,/g, ",").trim();
    // Tách theo dấu gạch chéo "/" (ngắt ý trong kịch bản)
    const chunks = raw.split(/\s*\/\s*/);
    const result: string[] = [];
    for (const chunk of chunks) {
      const matches = chunk.match(/[^.?!:]+[.?!:]?/g);
      if (matches && matches.length > 0) {
        for (const m of matches) {
          const cleaned = m.replace(/[\/]/g, "").replace(/,,/g, ",").trim();
          if (cleaned.length > 0) result.push(cleaned);
        }
      } else {
        const cleaned = chunk.replace(/[\/]/g, "").replace(/,,/g, ",").trim();
        if (cleaned.length > 0) result.push(cleaned);
      }
    }
    return result.length > 0 ? result : [raw.replace(/[\/]/g, "").replace(/,,/g, ",").trim()];
  }, [scene.text]);

  // Tính toán thời gian phân bổ cho từng câu dựa theo số lượng từ
  const sentenceRanges = useMemo(() => {
    const totalFrames = scene.durationInFrames;
    const wordCounts = sentences.map((s) => s.split(/\s+/).length);
    const totalWords = wordCounts.reduce((a, b) => a + b, 0) || 1;

    let currentStart = 0;
    return sentences.map((text, i) => {
      const share = wordCounts[i] / totalWords;
      // Dành tối thiểu 30 frames cho mỗi câu
      const duration = Math.max(30, Math.round(share * totalFrames));
      const end =
        i === sentences.length - 1 ? totalFrames : currentStart + duration;
      const range = { text, start: currentStart, end };
      currentStart = end;
      return range;
    });
  }, [sentences, scene.durationInFrames]);

  // Tìm câu đang được nói đến tại frame hiện tại
  const currentSentence =
    sentenceRanges.find((r) => frame >= r.start && frame < r.end)?.text ||
    sentenceRanges[sentenceRanges.length - 1]?.text ||
    scene.text;

  // Hiệu ứng chuyển động nhẹ khi đổi câu
  const activeRange = sentenceRanges.find(
    (r) => frame >= r.start && frame < r.end
  );
  const localFrame = activeRange ? frame - activeRange.start : 0;
  const sentenceFade = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const sentenceSlide = interpolate(localFrame, [0, 8], [8, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  const currentSentenceDuration = activeRange
    ? activeRange.end - activeRange.start
    : scene.durationInFrames;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 75,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "0 100px",
        zIndex: 45,
      }}
    >
      {/* 1. Thẻ Highlight đắt giá ở trên: Chữ 22px to rõ, tương phản đanh thép */}
      {scene.highlight && (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 32px",
            background:
              "linear-gradient(135deg, #fbbf24 0%, #e0a96d 100%)",
            borderRadius: 40,
            boxShadow:
              "0 8px 25px rgba(0, 0, 0, 0.65), 0 0 15px rgba(251, 191, 36, 0.45)",
            marginBottom: 16,
          }}
        >
          <span
            style={{
              fontSize: 22,
              fontWeight: 900,
              color: "#0c0e14",
              letterSpacing: 0.8,
              WebkitFontSmoothing: "antialiased",
            }}
          >
            ✦ {scene.highlight}
          </span>
        </div>
      )}

      {/* 2. Câu thoại hiện tại: Chữ to rõ (42px) kèm Karaoke Word Bounce */}
      <div
        style={{
          maxWidth: 1450,
          background: "rgba(10, 13, 20, 0.75)",
          backdropFilter: "blur(18px)",
          border: "1.5px solid rgba(255, 255, 255, 0.16)",
          borderRadius: 22,
          padding: "20px 45px",
          textAlign: "center",
          boxShadow: "0 18px 45px rgba(0, 0, 0, 0.65)",
          opacity: sentenceFade,
          transform: `translateY(${sentenceSlide}px)`,
        }}
      >
        <LongVideoKaraokeText
          text={currentSentence}
          durationInFrames={currentSentenceDuration}
          localFrame={localFrame}
        />
      </div>
    </div>
  );
};

// End Card tri ân & kêu gọi theo dõi
const EndChannelCard: React.FC<{ channel: string; slogan: string }> = ({
  channel,
  slogan,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(5, 6, 9, 0.88)",
        backdropFilter: "blur(20px)",
        opacity,
        zIndex: 60,
      }}
    >
      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: "50%",
          background: "linear-gradient(135deg, #e0a96d 0%, #b87b42 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 24,
          boxShadow: "0 8px 30px rgba(224, 169, 109, 0.5)",
        }}
      >
        <svg
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#111"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
          <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
          <line x1="6" y1="2" x2="6" y2="4"></line>
          <line x1="10" y1="2" x2="10" y2="4"></line>
          <line x1="14" y1="2" x2="14" y2="4"></line>
        </svg>
      </div>

      <h2
        style={{
          fontSize: 48,
          fontWeight: 900,
          color: "#ffffff",
          letterSpacing: 3,
          margin: "0 0 8px 0",
        }}
      >
        {channel}
      </h2>

      <p
        style={{
          fontSize: 22,
          color: "#e0a96d",
          fontWeight: 600,
          letterSpacing: 1.5,
          margin: "0 0 32px 0",
        }}
      >
        {slogan}
      </p>

      <div
        style={{
          padding: "12px 36px",
          borderRadius: 999,
          background: "rgba(255, 255, 255, 0.1)",
          border: "1px solid rgba(255, 255, 255, 0.25)",
          color: "#ffffff",
          fontSize: 18,
          fontWeight: 600,
          letterSpacing: 1,
        }}
      >
        Nhấn Đăng ký để cùng ngồi lại mỗi tuần
      </div>
    </AbsoluteFill>
  );
};

// Thanh tiến trình mỏng phía dưới
const ProgressBar: React.FC<{ totalFrames: number }> = ({ totalFrames }) => {
  const frame = useCurrentFrame();
  const progress = (frame / Math.max(1, totalFrames)) * 100;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: 6,
        backgroundColor: "rgba(255, 255, 255, 0.08)",
        zIndex: 55,
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${progress}%`,
          background: "linear-gradient(90deg, #b87b42 0%, #e0a96d 100%)",
          boxShadow: "0 0 8px rgba(224, 169, 109, 0.6)",
        }}
      />
    </div>
  );
};

// Center Hero Text Card cho các cảnh THẺ CHỮ
const CenterHeroTextCard: React.FC<{
  highlight: string;
  chapter?: string;
  tag?: string;
  durationInFrames: number;
}> = ({ highlight, chapter, tag, durationInFrames }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, 15, durationInFrames - 15, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp" }
  );
  const scale = interpolate(
    frame,
    [0, 20, durationInFrames],
    [0.96, 1.0, 1.02],
    { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 120,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 42,
        opacity,
        transform: `scale(${scale})`,
        pointerEvents: "none",
        padding: "0 60px",
      }}
    >
      <div
        style={{
          maxWidth: 1300,
          padding: "36px 64px",
          background: "rgba(12, 16, 26, 0.65)",
          borderRadius: 28,
          border: "2px solid rgba(224, 169, 109, 0.7)",
          boxShadow:
            "0 16px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(224, 169, 109, 0.25)",
          backdropFilter: "blur(18px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: 15,
            fontWeight: 800,
            color: "#e0a96d",
            letterSpacing: 4,
            textTransform: "uppercase",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span>✦</span>
          <span>{chapter || tag || "TRIẾT LÝ ỨNG DỤNG"}</span>
          <span>✦</span>
        </div>
        <div
          style={{
            fontSize: 52,
            fontWeight: 900,
            color: "#ffffff",
            lineHeight: 1.3,
            letterSpacing: 2,
            textShadow:
              "0 4px 25px rgba(0,0,0,0.9), 0 0 35px rgba(224, 169, 109, 0.5)",
          }}
        >
          {highlight}
        </div>
      </div>
    </div>
  );
};

// Interactive End Screen 15 giây theo quy chuẩn Shorts & Long Video
const InteractiveEndScreen: React.FC<{
  channel: string;
  slogan: string;
}> = ({ channel }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        zIndex: 58,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(8, 10, 16, 0.88)",
        backdropFilter: "blur(20px)",
        opacity,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 60,
          marginBottom: 30,
        }}
      >
        {/* Thẻ đề xuất 1: Video Shorts */}
        <div
          style={{
            width: 320,
            height: 480,
            borderRadius: 20,
            border: "2px solid rgba(224, 169, 109, 0.6)",
            background: "rgba(18, 22, 32, 0.9)",
            boxShadow: "0 15px 40px rgba(0,0,0,0.7)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            textAlign: "center",
          }}
        >
          <div
            style={{
              padding: "6px 16px",
              borderRadius: 20,
              background: "#e0a96d",
              color: "#111",
              fontSize: 13,
              fontWeight: 800,
              marginBottom: 20,
            }}
          >
            SHORTS ĐỀ XUẤT
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 800,
              color: "#fff",
              lineHeight: 1.4,
              marginBottom: 16,
            }}
          >
            ĐỪNG ĐÈ NÉN CƠN GIẬN
          </div>
          <div
            style={{
              fontSize: 13,
              color: "rgba(255,255,255,0.6)",
            }}
          >
            Bài học 60 giây chuyển hóa tức giận
          </div>
        </div>

        {/* Nút tròn Đăng ký ở giữa */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            style={{
              width: 110,
              height: 110,
              borderRadius: "50%",
              background: "linear-gradient(135deg, #e0a96d 0%, #b87b42 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 40px rgba(224, 169, 109, 0.6)",
            }}
          >
            <svg
              width="50"
              height="50"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#111"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
              <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
              <line x1="6" y1="2" x2="6" y2="4"></line>
              <line x1="10" y1="2" x2="10" y2="4"></line>
              <line x1="14" y1="2" x2="14" y2="4"></line>
            </svg>
          </div>
          <div
            style={{
              fontSize: 26,
              fontWeight: 900,
              color: "#ffffff",
              letterSpacing: 2,
            }}
          >
            {channel}
          </div>
          <div
            style={{
              padding: "10px 28px",
              borderRadius: 30,
              background: "#e0a96d",
              color: "#111",
              fontSize: 16,
              fontWeight: 800,
              boxShadow: "0 4px 15px rgba(224, 169, 109, 0.4)",
            }}
          >
            ĐĂNG KÝ KÊNH
          </div>
        </div>

        {/* Thẻ đề xuất 2: Video Dài tiếp theo */}
        <div
          style={{
            width: 480,
            height: 270,
            borderRadius: 20,
            border: "2px solid rgba(224, 169, 109, 0.6)",
            background: "rgba(18, 22, 32, 0.9)",
            boxShadow: "0 15px 40px rgba(0,0,0,0.7)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            textAlign: "center",
          }}
        >
          <div
            style={{
              padding: "6px 16px",
              borderRadius: 20,
              background: "rgba(255,255,255,0.15)",
              color: "#e0a96d",
              fontSize: 13,
              fontWeight: 800,
              marginBottom: 16,
            }}
          >
            VIDEO TIẾP THEO
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 800,
              color: "#fff",
              lineHeight: 1.4,
              marginBottom: 12,
            }}
          >
            TÂM THÁI BÌNH THƯỜNG LÀ ĐẠO
          </div>
          <div
            style={{
              fontSize: 14,
              color: "rgba(255,255,255,0.6)",
            }}
          >
            Bí quyết an yên giữa muôn ngàn biến đổi
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
