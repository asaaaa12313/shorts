"use client";

const EDGE_VOICES = [
  { id: "ko-KR-SunHiNeural", label: "선희", gender: "여", desc: "밝고 친근" },
  { id: "ko-KR-InJoonNeural", label: "인준", gender: "남", desc: "친근한" },
  { id: "ko-KR-HyunsuMultilingualNeural", label: "현수", gender: "남", desc: "자연스러운" },
];

const ELEVENLABS_VOICES = [
  { id: "21m00Tcm4TlvDq8ikWAM", label: "Rachel", gender: "여", desc: "차분하고 자연스러운" },
  { id: "EXAVITQu4vr4xnSDxMaL", label: "Bella", gender: "여", desc: "부드럽고 따뜻한" },
  { id: "ErXwobaYiN019PkySvjV", label: "Antoni", gender: "남", desc: "깔끔하고 명확한" },
  { id: "VR6AewLTigWG4xSOukaG", label: "Arnold", gender: "남", desc: "힘있고 안정적인" },
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

  const handleEngineChange = (engine: string) => {
    onEngineChange(engine);
    // 엔진 변경 시 해당 엔진의 첫 번째 음성으로 자동 선택
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
            <p className="text-xs text-amber-400/70 px-1">API 키 필요 · 더 자연스러운 음성</p>
          )}

          {/* 음성 선택 */}
          <div className="grid grid-cols-2 gap-2">
            {voices.map((v) => (
              <button
                key={v.id}
                onClick={() => onVoiceChange(v.id)}
                className={`px-3 py-2 rounded-lg text-left transition-colors
                  ${voiceId === v.id
                    ? "bg-purple-600 text-white ring-2 ring-purple-400"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
              >
                <div className="text-sm font-medium">{v.label} ({v.gender})</div>
                <div className="text-xs text-gray-400">{v.desc}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
