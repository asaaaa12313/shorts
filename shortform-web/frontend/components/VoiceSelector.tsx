"use client";

const VOICES = [
  { id: "ko-KR-SunHiNeural", label: "선희", gender: "여", desc: "밝고 친근" },
  { id: "ko-KR-InJoonNeural", label: "인준", gender: "남", desc: "친근한" },
  { id: "ko-KR-HyunsuMultilingualNeural", label: "현수", gender: "남", desc: "자연스러운" },
];

interface Props {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  voiceId: string;
  onVoiceChange: (voiceId: string) => void;
}

export default function VoiceSelector({ enabled, onToggle, voiceId, onVoiceChange }: Props) {
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
        <div className="grid grid-cols-2 gap-2">
          {VOICES.map((v) => (
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
      )}
    </div>
  );
}
