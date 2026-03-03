"use client";

import { useState } from "react";

const EDGE_VOICES = [
  { id: "ko-KR-SunHiNeural", label: "선희", gender: "여", desc: "밝고 친근" },
  { id: "ko-KR-InJoonNeural", label: "인준", gender: "남", desc: "친근한" },
  { id: "ko-KR-HyunsuMultilingualNeural", label: "현수", gender: "남", desc: "자연스러운" },
];

const ELEVENLABS_VOICES = [
  // 여성 - premade (무료 API 사용 가능, 한국어 지원)
  { id: "cgSgspJ2msm6clMCkdW9", label: "Jessica", gender: "여", desc: "밝고 따뜻한 대화체", tag: "추천" },
  { id: "pFZP5JQG7iQjIQuC4Bku", label: "Lily", gender: "여", desc: "부드럽고 세련된", tag: "인기" },
  { id: "EXAVITQu4vr4xnSDxMaL", label: "Sarah", gender: "여", desc: "프로페셔널 나레이션", tag: "" },
  { id: "Xb7hH8MSUJpSbSDYk0k2", label: "Alice", gender: "여", desc: "또렷하고 교육적인", tag: "" },
  { id: "XrExE9yKIg1WjnnlVkGX", label: "Matilda", gender: "여", desc: "전문적이고 활기찬", tag: "" },
  { id: "FGY2WhTYpPnrIDTdsKH5", label: "Laura", gender: "여", desc: "트렌디한 소셜미디어", tag: "" },
  { id: "jsCqWAovK2LkecY7zXl4", label: "Freya", gender: "여", desc: "차분하고 깊은", tag: "" },
  { id: "hpp4J3VqNfWAUOO0d1Us", label: "Bella", gender: "여", desc: "밝고 프로페셔널", tag: "" },
  // 남성 - premade (무료 API 사용 가능, 한국어 지원)
  { id: "nPczCjzI2devNBz1zQrb", label: "Brian", gender: "남", desc: "깊고 편안한 나레이션", tag: "추천" },
  { id: "TX3LPaxmHKxFdv7VOQHJ", label: "Liam", gender: "남", desc: "에너지 넘치는 크리에이터", tag: "인기" },
  { id: "IKne3meq5aSn9XLyUdCD", label: "Charlie", gender: "남", desc: "깊고 자신감 넘치는", tag: "" },
  { id: "iP95p4xoKVk53GoZ742B", label: "Chris", gender: "남", desc: "친근하고 캐주얼한", tag: "" },
  { id: "cjVigY5qzO86Huf0OWal", label: "Eric", gender: "남", desc: "부드럽고 신뢰감", tag: "" },
  { id: "onwK4e9ZLuTAKqWW03F9", label: "Daniel", gender: "남", desc: "차분한 방송인 스타일", tag: "" },
  { id: "JBFqnCBsd6RMkjVDRZzb", label: "George", gender: "남", desc: "따뜻한 스토리텔러", tag: "" },
  { id: "bIHbv24MWmeRgasZH58o", label: "Will", gender: "남", desc: "편안하고 낙천적인", tag: "" },
];

interface Props {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  voiceId: string;
  onVoiceChange: (voiceId: string) => void;
  ttsEngine: string;
  onEngineChange: (engine: string) => void;
}

export default function VoiceSelector({ enabled, onToggle, voiceId, onVoiceChange, ttsEngine, onEngineChange }: Props) {
  const voices = ttsEngine === "elevenlabs" ? ELEVENLABS_VOICES : EDGE_VOICES;
  const [genderFilter, setGenderFilter] = useState<"all" | "여" | "남">("all");

  const filteredVoices = genderFilter === "all"
    ? voices
    : voices.filter(v => v.gender === genderFilter);

  const handleEngineChange = (engine: string) => {
    onEngineChange(engine);
    const newVoices = engine === "elevenlabs" ? ELEVENLABS_VOICES : EDGE_VOICES;
    onVoiceChange(newVoices[0].id);
  };

  return (
    <div className="space-y-3">
      <button
        onClick={() => onToggle(!enabled)}
        className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors
          ${enabled ? "bg-purple-600/20 border border-purple-500" : "bg-gray-800 border border-gray-700"}`}
      >
        <span className="text-sm font-medium">AI 음성 나레이션</span>
        <span className={`text-xs px-2 py-1 rounded-full ${enabled ? "bg-purple-600 text-white" : "bg-gray-700 text-gray-400"}`}>
          {enabled ? "ON" : "OFF"}
        </span>
      </button>

      {enabled && (
        <div className="space-y-3">
          {/* TTS 엔진 선택 */}
          <div className="flex gap-2">
            <button
              onClick={() => handleEngineChange("edge")}
              className={`flex-1 px-3 py-2 rounded-lg text-sm transition-colors
                ${ttsEngine === "edge"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              기본 (무료)
            </button>
            <button
              onClick={() => handleEngineChange("elevenlabs")}
              className={`flex-1 px-3 py-2 rounded-lg text-sm transition-colors
                ${ttsEngine === "elevenlabs"
                  ? "bg-amber-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              프리미엄 (ElevenLabs)
            </button>
          </div>

          {ttsEngine === "elevenlabs" && (
            <>
              <p className="text-xs text-amber-400/70 px-1">더 자연스럽고 사람 같은 AI 음성 (월 10,000자 무료)</p>
              {/* 성별 필터 */}
              <div className="flex gap-1">
                {(["all", "여", "남"] as const).map(g => (
                  <button
                    key={g}
                    onClick={() => setGenderFilter(g)}
                    className={`px-3 py-1 rounded-full text-xs transition-colors
                      ${genderFilter === g
                        ? "bg-purple-600 text-white"
                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
                  >
                    {g === "all" ? "전체" : g}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* 음성 선택 */}
          <div className={`grid gap-2 ${ttsEngine === "elevenlabs" ? "grid-cols-2 max-h-64 overflow-y-auto pr-1" : "grid-cols-2"}`}>
            {filteredVoices.map((v) => (
              <button
                key={v.id}
                onClick={() => onVoiceChange(v.id)}
                className={`px-3 py-2 rounded-lg text-left transition-colors relative
                  ${voiceId === v.id
                    ? "bg-purple-600 text-white ring-2 ring-purple-400"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
              >
                <div className="text-sm font-medium">
                  {v.label} ({v.gender})
                  {"tag" in v && (v as { tag?: string }).tag && (
                    <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/30 text-amber-300">
                      {(v as { tag?: string }).tag}
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400">{v.desc}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
