"use client";

import { useState } from "react";

const EDGE_VOICES = [
  { id: "ko-KR-SunHiNeural", label: "선희", gender: "여", desc: "밝고 친근" },
  { id: "ko-KR-InJoonNeural", label: "인준", gender: "남", desc: "친근한" },
  { id: "ko-KR-HyunsuMultilingualNeural", label: "현수", gender: "남", desc: "자연스러운" },
];

const ELEVENLABS_VOICES = [
  // 여성 - 트렌디/소셜미디어
  { id: "zgDzx5jLLCqEp6Fl7Kl7", label: "한나", gender: "여", desc: "자연스럽고 트렌디한", tag: "인기" },
  { id: "9vTWeZwjAkqIiZJdCarV", label: "엠마", gender: "여", desc: "깔끔하고 프로페셔널", tag: "추천" },
  { id: "iWLjl1zCuqXRkW6494ve", label: "지수", gender: "여", desc: "활기찬 뉴스 스타일", tag: "" },
  { id: "Lb7qkOn5hF8p7qfCDH8q", label: "애니", gender: "여", desc: "부드럽고 사랑스러운", tag: "" },
  { id: "8jHHF8rMqMlg8if2mOUe", label: "한", gender: "여", desc: "캐주얼 팟캐스트 느낌", tag: "" },
  { id: "sf8Bpb1IU97NI9BHSMRf", label: "로사", gender: "여", desc: "차분하고 세련된", tag: "" },
  { id: "0oqpliV6dVSr9XomngOW", label: "지니", gender: "여", desc: "지적이고 따뜻한", tag: "" },
  { id: "AW5wrnG1jVizOYY7R1Oo", label: "지영", gender: "여", desc: "친근하고 자연스러운", tag: "" },
  // 남성 - 트렌디/소셜미디어
  { id: "m3gJBS8OofDJfycyA2Ip", label: "태형", gender: "남", desc: "친근한 소셜미디어", tag: "인기" },
  { id: "pb3lVZVjdFWbkhPKlelB", label: "해리", gender: "남", desc: "부드럽고 편안한", tag: "추천" },
  { id: "9rZOpKhfmFa6UIvpEi4C", label: "준혁", gender: "남", desc: "전문 성우 느낌", tag: "" },
  { id: "WqVy7827vjE2r3jWvbnP", label: "혁", gender: "남", desc: "감성적인 나레이션", tag: "" },
  { id: "nbrxrAz3eYm9NgojrmFK", label: "민준", gender: "남", desc: "차분하고 지적인", tag: "" },
  { id: "jB1Cifc2UQbq1gR3wnb0", label: "빈", gender: "남", desc: "따뜻하고 진중한", tag: "" },
  { id: "v1jVu1Ky28piIPEJqRrm", label: "데이빗", gender: "남", desc: "라디오 DJ 느낌", tag: "" },
  { id: "4JJwo477JUAx3HV0T7n7", label: "요한", gender: "남", desc: "자신감있고 믿음직한", tag: "" },
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
              <p className="text-xs text-amber-400/70 px-1">더 자연스럽고 사람 같은 음성</p>
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
