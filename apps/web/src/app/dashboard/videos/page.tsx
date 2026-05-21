"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { videoApi, VideoListItem, ApiError } from "@/lib/api";
import VideoList from "@/components/VideoList";

const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID ?? "default-org-id";

const STATUS_OPTIONS = [
  { value: "", label: "전체" },
  { value: "draft", label: "초안" },
  { value: "uploaded", label: "업로드됨" },
  { value: "processing", label: "처리 중" },
  { value: "analyzed", label: "분석 완료" },
  { value: "failed", label: "실패" },
];

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (p: number, s: string, st: string) => {
      setLoading(true);
      setError(null);
      try {
        const res = await videoApi.list(ORG_ID, {
          page: p,
          pageSize,
          search: s || undefined,
          status: st || undefined,
        });
        setVideos(res.data);
        setTotal(res.meta.total);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "목록 조회 실패");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    load(page, search, status);
  }, [page, search, status, load]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load(1, search, status);
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">영상 관리</h1>
        <Link
          href="/dashboard/videos/upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
        >
          + 영상 등록
        </Link>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="제목 검색"
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          type="submit"
          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
        >
          검색
        </button>
      </form>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="py-16 text-center text-gray-400">불러오는 중...</div>
      ) : (
        <VideoList
          orgId={ORG_ID}
          videos={videos}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
