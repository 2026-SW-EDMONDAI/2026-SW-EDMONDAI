import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SegmentFlow",
  description: "교육영상 세그먼트 분석 및 광고 위치 추천 운영 도구",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
