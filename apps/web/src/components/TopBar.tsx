"use client";

import { useRouter } from "next/navigation";

export default function TopBar() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
      <h2 className="text-sm font-medium text-gray-500">운영자 대시보드</h2>
      <button
        onClick={handleLogout}
        className="rounded px-3 py-1 text-sm text-gray-600 hover:bg-gray-100"
      >
        로그아웃
      </button>
    </header>
  );
}
