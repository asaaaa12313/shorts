"use client";

const EFFECTS = [
  { id: "", label: "자동 순환", emoji: "🔄" },
  { id: "pop_in", label: "팝인", emoji: "💥" },
  { id: "slide_up", label: "슬라이드 업", emoji: "⬆️" },
  { id: "slide_down", label: "슬라이드 다운", emoji: "⬇️" },
  { id: "bounce", label: "바운스", emoji: "🏀" },
  { id: "scale_pulse", label: "펄스", emoji: "💫" },
  { id: "zoom_in", label: "줌인", emoji: "🔍" },
  { id: "zoom_out", label: "줌아웃", emoji: "🔎" },
  { id: "rotate_in", label: "회전", emoji: "🌀" },
  { id: "slide_right", label: "슬라이드 옆", emoji: "➡️" },
  { id: "typewriter", label: "타이핑", emoji: "⌨️" },
];

interface Props {
  selected: string;
  onSelect: (effect: string) => void;
}

export default function SubtitleEffectSelector({ selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
      {EFFECTS.map((e) => (
        <button
          key={e.id}
          onClick={() => onSelect(e.id)}
          className={`px-3 py-2 rounded-lg text-sm transition-colors
            ${selected === e.id
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
        >
          {e.emoji} {e.label}
        </button>
      ))}
    </div>
  );
}
