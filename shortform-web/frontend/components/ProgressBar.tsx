"use client";

const STEPS: Record<string, string> = {
  analyzing: "클립 분석 및 선별 중",
  combining: "영상 결합 중 (줌 + 전환 효과)",
  subtitles: "AI 자막 생성 중",
  tts: "AI 음성 생성 중",
  bgm: "BGM 선택 중",
  motion_frames: "모션 효과 적용 중",
  composing: "최종 합성 중",
  cleanup: "마무리 중",
};

interface Props {
  step: string;
  progress: number;
}

export default function ProgressBar({ step, progress }: Props) {
  const stepEntries = Object.entries(STEPS);

  return (
    <div className="space-y-3">
      {stepEntries.map(([key, label]) => {
        const stepIndex = stepEntries.findIndex(([k]) => k === key);
        const currentIndex = stepEntries.findIndex(([k]) => k === step);
        const isDone = stepIndex < currentIndex;
        const isCurrent = key === step;

        return (
          <div key={key} className="flex items-center gap-3">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0
                ${isDone ? "bg-green-600" : isCurrent ? "bg-blue-600 animate-pulse" : "bg-gray-700"}`}
            >
              {isDone ? "✓" : isCurrent ? "..." : ""}
            </div>
            <span className={`text-sm ${isCurrent ? "text-white" : isDone ? "text-green-400" : "text-gray-500"}`}>
              {label}
            </span>
          </div>
        );
      })}

      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>진행률</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
