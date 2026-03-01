import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "숏폼 자동 생성기",
  description: "영상 클립을 업로드하면 15초 숏폼 영상을 자동으로 만들어드립니다",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-gray-950 text-white min-h-screen">{children}</body>
    </html>
  );
}
