"use client";

const TYPES = [
  { id: "", label: "자동 감지", emoji: "🤖" },
  { id: "카페", label: "카페", emoji: "☕" },
  { id: "음식점", label: "음식점", emoji: "🍽️" },
  { id: "골프", label: "골프", emoji: "⛳" },
  { id: "태권도", label: "태권도", emoji: "🥋" },
  { id: "뷰티", label: "뷰티/에스테틱", emoji: "💆" },
  { id: "학원", label: "학원/교육", emoji: "📚" },
  { id: "헬스", label: "헬스/PT", emoji: "💪" },
  { id: "병원", label: "병원/클리닉", emoji: "🏥" },
  { id: "기타", label: "기타", emoji: "📌" },
];

interface Props {
  selected: string;
  onSelect: (type: string) => void;
}

export default function BusinessTypeSelector({ selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
      {TYPES.map((t) => (
        <button
          key={t.id}
          onClick={() => onSelect(t.id)}
          className={`px-3 py-2 rounded-lg text-sm transition-colors
            ${selected === t.id
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
        >
          {t.emoji} {t.label}
        </button>
      ))}
    </div>
  );
}
